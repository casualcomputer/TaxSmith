#!/usr/bin/env python3
"""Mirror official Canadian court decisions into Markdown.

The supported court sites are powered by Lexum/Decisia. The harvester reads
their public date navigation pages, prefers the HTML decision text, and can also
mirror source PDFs. It stops when Lexum asks for validation or rate-limits the
session so a bulk harvest can be resumed later instead of hammering the site.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "Taxsmith corpus builder (research; contact: local repository user)"


class SiteAccessInterrupted(RuntimeError):
    """Raised when the source site asks us to pause the harvest."""


class CaptchaRequired(SiteAccessInterrupted):
    """Raised when Lexum/Decisia asks for human validation."""


@dataclass(frozen=True)
class CourtConfig:
    key: str
    court: str
    court_database: str
    authority_type: str
    source_family: str
    base_url: str
    date_nav_path: str
    path_prefix: str
    output_dir: Path
    data_dir: Path
    full_corpus_by_default: bool = False

    @property
    def source_url(self) -> str:
        return urljoin(self.base_url, self.date_nav_path)


COURTS: dict[str, CourtConfig] = {
    "tcc": CourtConfig(
        key="tcc",
        court="Tax Court of Canada",
        court_database="Tax Court of Canada Judgments",
        authority_type="tcc_case",
        source_family="case_law_tcc",
        base_url="https://decision.tcc-cci.gc.ca",
        date_nav_path="/tcc-cci/decisions/en/nav_date.do",
        path_prefix="/tcc-cci/decisions",
        output_dir=ROOT / "docs/cases/validation/tcc-official-decisia",
        data_dir=ROOT / "data/tcc_decisions",
        full_corpus_by_default=True,
    ),
    "fca": CourtConfig(
        key="fca",
        court="Federal Court of Appeal",
        court_database="Federal Court of Appeal Decisions",
        authority_type="fca_case",
        source_family="case_law_fca",
        base_url="https://decisions.fca-caf.gc.ca",
        date_nav_path="/fca-caf/decisions/en/nav_date.do",
        path_prefix="/fca-caf/decisions",
        output_dir=ROOT / "docs/cases/fca",
        data_dir=ROOT / "data/fca_decisions",
    ),
    "fc": CourtConfig(
        key="fc",
        court="Federal Court",
        court_database="Federal Court Decisions",
        authority_type="fc_case",
        source_family="case_law_fc",
        base_url="https://decisions.fct-cf.gc.ca",
        date_nav_path="/fc-cf/decisions/en/nav_date.do",
        path_prefix="/fc-cf/decisions",
        output_dir=ROOT / "docs/cases/fc",
        data_dir=ROOT / "data/fc_decisions",
    ),
    "scc": CourtConfig(
        key="scc",
        court="Supreme Court of Canada",
        court_database="Supreme Court of Canada Judgments",
        authority_type="scc_case",
        source_family="case_law_scc",
        base_url="https://decisions.scc-csc.ca",
        date_nav_path="/scc-csc/scc-csc/en/nav_date.do",
        path_prefix="/scc-csc/scc-csc",
        output_dir=ROOT / "docs/cases/scc",
        data_dir=ROOT / "data/scc_decisions",
    ),
}


TAX_STRONG_PATTERNS = [
    r"\bincome tax\b",
    r"\bincome tax act\b",
    r"\bexcise tax\b",
    r"\bexcise tax act\b",
    r"\bgoods and services tax\b",
    r"\bharmonized sales tax\b",
    r"\bgst\b",
    r"\bhst\b",
    r"\btax court\b",
    r"\btaxpayer\b",
    r"\btaxable\b",
    r"\breassessment\b",
    r"\btax assessment\b",
    r"\bminister of national revenue\b",
    r"\bnational revenue\b",
    r"\bm\.?n\.?r\.?\b",
    r"\bcanada revenue agency\b",
    r"\brevenue canada\b",
    r"\bcra\b",
    r"\bcanada pension plan\b",
    r"\bemployment insurance act\b",
    r"\bsource deduction",
    r"\bwithholding tax\b",
    r"\bpart xiii\b",
    r"\bgaar\b",
    r"\bgeneral anti-avoidance\b",
    r"\bsection 160\b",
    r"\bsubsection 160\b",
    r"\bcapital cost allowance\b",
    r"\bsr&ed\b",
    r"\bsred\b",
    r"\bscientific research and experimental development\b",
    r"\btax credit\b",
    r"\btax shelter\b",
    r"\btransfer pricing\b",
    r"\btaxable canadian property\b",
    r"\bcharitable donation\b",
    r"\bregistered charity\b",
    r"\brrsp\b",
    r"\brrif\b",
    r"\btfsa\b",
]


@dataclass(frozen=True)
class CaseSummary:
    item_id: str
    title: str
    citation: str
    decision_date: str
    language: str
    subjects: tuple[str, ...]
    item_url: str
    pdf_url: str
    year: int


@dataclass(frozen=True)
class CaseDocument:
    summary: CaseSummary
    court_database: str = ""
    file_numbers: str = ""
    judges: str = ""
    source_html_sha256: str = ""
    pdf_sha256: str = ""
    pdf_path: str = ""
    text: str = ""
    case_scope: str = ""
    tax_relevance: str = ""


def fetch_url(url: str, timeout: int, retries: int = 2) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=timeout) as response:
                content = response.read()
                if b"/robocop/captcha/" in content or b"Decisia software calls upon users" in content:
                    raise CaptchaRequired(
                        "Lexum/Decisia returned a validation page. Stop the harvest, "
                        "complete validation or wait, then resume with a larger --delay."
                    )
                return content
        except SiteAccessInterrupted:
            raise
        except HTTPError as exc:
            last_error = exc
            if exc.code in {403, 429}:
                raise SiteAccessInterrupted(
                    f"Could not fetch {url}: HTTP {exc.code}. The decision site may be "
                    "rate-limiting or requiring Lexum validation; resume later with a larger --delay."
                ) from exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
        except (URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not fetch {url}: {last_error}") from last_error


def decode_html(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def strip_tags(fragment: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", fragment)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def slugify(value: str) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def relative_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def with_iframe(url: str) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}iframe=true"


def year_index_url(config: CourtConfig, year: int, current_year: int) -> str:
    if year == current_year:
        return config.source_url
    prefix = config.date_nav_path.rsplit("/nav_date.do", 1)[0]
    return urljoin(config.base_url, f"{prefix}/{year}/nav_date.do")


def page_url(index_url: str, page: int) -> str:
    if page <= 1:
        return index_url
    separator = "&" if "?" in index_url else "?"
    return f"{index_url}{separator}page={page}"


def discover_years(config: CourtConfig, timeout: int) -> list[int]:
    content = decode_html(fetch_url(with_iframe(config.source_url), timeout))
    prefix = re.escape(config.path_prefix)
    years = {
        int(year)
        for year in re.findall(rf"{prefix}/(?:en|fr)/(\d{{4}})/nav_date\.do", content)
    }
    title_match = re.search(r"Navigation by Date:\s*(\d{4})", content)
    if title_match:
        years.add(int(title_match.group(1)))
    if not years:
        raise RuntimeError(f"Could not discover {config.court} decision years from date navigation page.")
    return sorted(years, reverse=True)


def parse_total_results(content: str) -> int:
    match = re.search(r"<h2>\s*([\d,\u00a0 ]+)&nbsp;result\(s\)</h2>", content)
    if not match:
        match = re.search(r"<h2>\s*([\d,\u00a0 ]+)\s*result\(s\)</h2>", content)
    if not match:
        return 0
    digits = re.sub(r"\D", "", html.unescape(match.group(1)))
    return int(digits) if digits else 0


def parse_page_numbers(content: str) -> set[int]:
    pages = {1}
    for page in re.findall(r"[?&]page=(\d+)", content):
        pages.add(int(page))
    return pages


def parse_case_summaries(config: CourtConfig, content: str, fallback_year: int) -> list[CaseSummary]:
    summaries: list[CaseSummary] = []
    blocks = re.findall(r'(?is)<li class="[^"]*list-item-expanded[^"]*">(.*?)</li>', content)
    prefix = re.escape(config.path_prefix)
    for block in blocks:
        item_match = re.search(
            rf'href="([^"]*{prefix}/(en|fr)/item/(\d+)/index\.do)"',
            block,
        )
        title_match = re.search(r'(?is)<span class="title">\s*<a[^>]*>(.*?)</a>\s*</span>', block)
        citation_match = re.search(r'(?is)<span class="citation">(.*?)</span>', block)
        date_match = re.search(r'(?is)<span class="publicationDate">(.*?)</span>', block)
        if not (item_match and title_match and citation_match and date_match):
            continue

        pdf_match = re.search(
            rf'href="([^"]*{prefix}/(?:en|fr)/\d+/1/document\.do)"',
            block,
        )
        subject_match = re.search(r'(?is)<div class="subject">\s*<span>(.*?)</span>\s*</div>', block)
        subjects = (
            tuple(
                part.strip()
                for part in strip_tags(subject_match.group(1)).splitlines()
                if part.strip()
            )
            if subject_match
            else ()
        )
        decision_date = strip_tags(date_match.group(1))
        year = int(decision_date[:4]) if re.match(r"\d{4}", decision_date) else fallback_year
        summaries.append(
            CaseSummary(
                item_id=item_match.group(3),
                title=strip_tags(title_match.group(1)),
                citation=strip_tags(citation_match.group(1)),
                decision_date=decision_date,
                language=item_match.group(2),
                subjects=subjects,
                item_url=urljoin(config.base_url, item_match.group(1)),
                pdf_url=urljoin(config.base_url, pdf_match.group(1)) if pdf_match else "",
                year=year,
            )
        )
    return summaries


def filter_years(years: list[int], start_year: int | None, end_year: int | None) -> list[int]:
    if start_year is not None:
        years = [year for year in years if year >= start_year]
    if end_year is not None:
        years = [year for year in years if year <= end_year]
    return years


def discover_cases_for_year(
    config: CourtConfig,
    year: int,
    current_year: int,
    timeout: int,
    delay: float,
) -> list[CaseSummary]:
    index_url = year_index_url(config, year, current_year)
    first_page = decode_html(fetch_url(with_iframe(index_url), timeout))
    pages = parse_page_numbers(first_page)
    total = parse_total_results(first_page)
    if total:
        pages.update(range(1, (total + 24) // 25 + 1))

    by_item_id: dict[str, CaseSummary] = {}
    for page in sorted(pages):
        content = (
            first_page
            if page == 1
            else decode_html(fetch_url(with_iframe(page_url(index_url, page)), timeout))
        )
        for summary in parse_case_summaries(config, content, year):
            by_item_id[summary.item_id] = summary
        if delay:
            time.sleep(delay)
    return sorted(
        by_item_id.values(),
        key=lambda item: (item.decision_date, item.citation, item.item_id),
        reverse=True,
    )


def discover_cases(
    config: CourtConfig,
    start_year: int | None,
    end_year: int | None,
    timeout: int,
    delay: float,
) -> list[CaseSummary]:
    all_years = discover_years(config, timeout)
    years = filter_years(all_years, start_year, end_year)
    if not years:
        return []

    current_year = max(all_years)
    by_item_id: dict[str, CaseSummary] = {}
    for year in years:
        for summary in discover_cases_for_year(config, year, current_year, timeout, delay):
            by_item_id[summary.item_id] = summary
    return sorted(
        by_item_id.values(),
        key=lambda item: (item.decision_date, item.citation, item.item_id),
        reverse=True,
    )


class TextExtractor(HTMLParser):
    block_tags = {
        "address",
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = re.sub(r"\s+", " ", data)
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        raw = html.unescape(raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r" *\n *", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def extract_element_by_id(content: str, element_id: str) -> str:
    start_match = re.search(rf'(?is)<div[^>]+id="{re.escape(element_id)}"[^>]*>', content)
    if not start_match:
        return ""
    pos = start_match.end()
    depth = 1
    tag_pattern = re.compile(r"(?is)<(/?)div\b[^>]*>")
    for match in tag_pattern.finditer(content, pos):
        depth += -1 if match.group(1) else 1
        if depth == 0:
            return content[start_match.end() : match.start()]
    return content[start_match.end() :]


def normalize_metadata_key(value: str) -> str:
    value = value.lower().replace("(s)", "s")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def extract_metadata(content: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    table_match = re.search(r'(?is)<div class="metadata">(.*?)</table>', content)
    if not table_match:
        return metadata
    for row in re.findall(r"(?is)<tr>(.*?)</tr>", table_match.group(1)):
        label_match = re.search(r'(?is)<td class="label">(.*?)</td>', row)
        value_match = re.search(r'(?is)<td class="metadata">(.*)', row)
        if not (label_match and value_match):
            continue
        key = normalize_metadata_key(strip_tags(label_match.group(1)))
        metadata[key] = strip_tags(value_match.group(1))
    return metadata


def first_metadata_value(metadata: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = metadata.get(key, "")
        if value:
            return value
    return ""


def html_to_text(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    return parser.text()


def parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def markdown_path(output_dir: Path, summary: CaseSummary) -> Path:
    citation_slug = slugify(summary.citation)
    title_slug = slugify(summary.title)[:80]
    return output_dir / str(summary.year) / f"{citation_slug}-{summary.item_id}-{title_slug}.md"


def pdf_path(data_dir: Path, summary: CaseSummary) -> Path:
    citation_slug = slugify(summary.citation)
    title_slug = slugify(summary.title)[:80]
    return data_dir / "pdf" / str(summary.year) / f"{citation_slug}-{summary.item_id}-{title_slug}.pdf"


def raw_html_path(data_dir: Path, summary: CaseSummary) -> Path:
    return data_dir / "html" / str(summary.year) / f"{summary.item_id}.html"


def tax_relevance_reason(summary: CaseSummary, text: str = "", custom_terms: tuple[str, ...] = ()) -> str:
    haystack = " ".join(
        [
            summary.title,
            summary.citation,
            " ".join(summary.subjects),
            summary.item_url,
            text[:200_000],
        ]
    ).lower()
    for term in custom_terms:
        if term.lower() in haystack:
            return f"custom:{term}"
    for pattern in TAX_STRONG_PATTERNS:
        match = re.search(pattern, haystack, flags=re.IGNORECASE)
        if match:
            return match.group(0).lower()
    return ""


def filter_by_scope(
    config: CourtConfig,
    summaries: list[CaseSummary],
    scope: str,
    custom_terms: tuple[str, ...],
) -> list[CaseSummary]:
    if scope == "all":
        return summaries
    if scope == "auto" and config.full_corpus_by_default:
        return summaries
    return [summary for summary in summaries if tax_relevance_reason(summary, custom_terms=custom_terms)]


def load_existing_document(config: CourtConfig, summary: CaseSummary, out_path: Path) -> CaseDocument:
    existing = out_path.read_text(encoding="utf-8", errors="replace")
    metadata = parse_front_matter(existing)
    return CaseDocument(
        summary=summary,
        court_database=metadata.get("court_database", config.court_database),
        file_numbers=metadata.get("file_numbers", ""),
        judges=metadata.get("judges", ""),
        source_html_sha256=metadata.get("source_html_sha256", ""),
        pdf_sha256=metadata.get("pdf_sha256", ""),
        pdf_path=metadata.get("pdf_path", ""),
        text=existing,
        case_scope=metadata.get("case_scope", ""),
        tax_relevance=metadata.get("tax_relevance", ""),
    )


def write_markdown(path: Path, config: CourtConfig, document: CaseDocument) -> None:
    summary = document.summary
    front_matter = [
        "---",
        f"title: {yaml_quote(summary.title)}",
        f"source: {yaml_quote(summary.item_url)}",
        f"last_modified: {yaml_quote(summary.decision_date)}",
        f"court: {yaml_quote(config.court)}",
        f"court_key: {yaml_quote(config.key)}",
        f"court_database: {yaml_quote(document.court_database)}",
        f"citation: {yaml_quote(summary.citation)}",
        f"neutral_citation: {yaml_quote(summary.citation)}",
        f"decision_date: {yaml_quote(summary.decision_date)}",
        f"language: {yaml_quote(summary.language)}",
        f"item_id: {yaml_quote(summary.item_id)}",
        f"file_numbers: {yaml_quote(document.file_numbers)}",
        f"judges: {yaml_quote(document.judges)}",
        f"subjects: {yaml_quote('; '.join(summary.subjects))}",
        f"case_scope: {yaml_quote(document.case_scope)}",
        f"tax_relevance: {yaml_quote(document.tax_relevance)}",
        f"pdf_url: {yaml_quote(summary.pdf_url)}",
        f"pdf_path: {yaml_quote(document.pdf_path)}",
        f"pdf_sha256: {yaml_quote(document.pdf_sha256)}",
        f"source_html_sha256: {yaml_quote(document.source_html_sha256)}",
        f"downloaded_at: {yaml_quote(date.today().isoformat())}",
        f"authority_type: {config.authority_type}",
        "document_type: case_law",
        f"source_family: {config.source_family}",
        "---",
        "",
    ]
    body = [
        f"# {summary.title}",
        "",
        f"- Citation: {summary.citation}",
        f"- Decision date: {summary.decision_date}",
        f"- Court: {config.court}",
    ]
    if summary.subjects:
        body.append(f"- Subjects: {'; '.join(summary.subjects)}")
    if document.file_numbers:
        body.append(f"- File numbers: {document.file_numbers}")
    if document.judges:
        body.append(f"- Judges: {document.judges}")
    if document.tax_relevance:
        body.append(f"- Tax relevance: {document.tax_relevance}")
    if document.pdf_path and not document.text.strip():
        body.append(f"- PDF mirror: {document.pdf_path}")
    body.extend(["", "## Decision Text", "", document.text.strip(), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front_matter + body), encoding="utf-8")


def download_case(
    config: CourtConfig,
    summary: CaseSummary,
    output_dir: Path,
    data_dir: Path,
    *,
    timeout: int,
    delay: float,
    force: bool,
    download_pdf: bool,
    scope: str,
    custom_terms: tuple[str, ...],
) -> CaseDocument | None:
    out_path = markdown_path(output_dir, summary)
    raw_path = raw_html_path(data_dir, summary)
    if out_path.exists() and raw_path.exists() and not force:
        return load_existing_document(config, summary, out_path)

    content = decode_html(fetch_url(with_iframe(summary.item_url), timeout))
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(content, encoding="utf-8")
    html_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    metadata = extract_metadata(content)
    document_fragment = extract_element_by_id(content, "document-content")
    text = html_to_text(document_fragment) if document_fragment else html_to_text(content)
    relevance = tax_relevance_reason(summary, text, custom_terms)
    if scope == "tax" and not relevance:
        return None

    saved_pdf_path = ""
    pdf_sha = ""
    if download_pdf and summary.pdf_url:
        target_pdf_path = pdf_path(data_dir, summary)
        if force or not target_pdf_path.exists():
            pdf_content = fetch_url(summary.pdf_url, timeout)
            target_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            target_pdf_path.write_bytes(pdf_content)
            if delay:
                time.sleep(delay)
        else:
            pdf_content = target_pdf_path.read_bytes()
        saved_pdf_path = relative_to_root(target_pdf_path)
        pdf_sha = hashlib.sha256(pdf_content).hexdigest()

    document = CaseDocument(
        summary=summary,
        court_database=first_metadata_value(metadata, ("court_database",)) or config.court_database,
        file_numbers=first_metadata_value(
            metadata,
            (
                "file_numbers",
                "file_number",
                "docket",
                "docket_number",
                "dockets",
                "court_file_number",
                "court_file_numbers",
            ),
        ),
        judges=first_metadata_value(
            metadata,
            (
                "judges_and_taxing_officers",
                "judges",
                "judge",
                "coram",
                "present",
                "panel",
            ),
        ),
        source_html_sha256=html_sha,
        pdf_sha256=pdf_sha,
        pdf_path=saved_pdf_path,
        text=text,
        case_scope=scope,
        tax_relevance=relevance,
    )
    write_markdown(out_path, config, document)
    if delay:
        time.sleep(delay)
    return document


def write_manifest(path: Path, output_dir: Path, config: CourtConfig, documents: list[CaseDocument]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for document in documents:
            summary = asdict(document.summary)
            summary["subjects"] = list(document.summary.subjects)
            row = {
                **summary,
                "court": config.court,
                "court_key": config.key,
                "court_database": document.court_database,
                "authority_type": config.authority_type,
                "source_family": config.source_family,
                "file_numbers": document.file_numbers,
                "judges": document.judges,
                "case_scope": document.case_scope,
                "tax_relevance": document.tax_relevance,
                "source_html_sha256": document.source_html_sha256,
                "pdf_sha256": document.pdf_sha256,
                "pdf_path": document.pdf_path,
                "markdown_path": relative_to_root(markdown_path(output_dir, document.summary)),
            }
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_readme(
    output_dir: Path,
    manifest_path: Path,
    config: CourtConfig,
    case_count: int,
    pdf_enabled: bool,
    scope: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scope_note = "all decisions" if scope == "all" or config.full_corpus_by_default else "tax-relevant decisions"
    validation_note = []
    if "validation" in output_dir.parts:
        validation_note = [
            "This folder is for validation and source QA. It is intentionally outside the upload-ready `docs/cases/tcc` staging folder so production RAG uploads do not mix official-page conversions with the A2AJ-derived TCC layer.",
            "",
        ]
    lines = [
        f"# {config.court} Decisions",
        "",
        f"Official {config.court} decision corpus mirrored from the public Lexum/Decisia date index.",
        "",
        *validation_note,
        f"- Scope: {scope_note}",
        f"- Markdown decisions: {case_count:,}",
        f"- PDF mirror enabled: {'yes' if pdf_enabled else 'no'}",
        f"- Harvester manifest: `{relative_to_root(manifest_path)}`",
        f"- Source index: {config.source_url}",
        "",
        "The Markdown files include front matter for citation, decision date, language, subjects, docket/file numbers, judge, official source URL, and PDF URL.",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def resolve_scope(config: CourtConfig, requested_scope: str) -> str:
    if requested_scope != "auto":
        return requested_scope
    return "all" if config.full_corpus_by_default else "tax"


def run_court(
    config: CourtConfig,
    *,
    output_dir: Path,
    data_dir: Path,
    start_year: int | None,
    end_year: int | None,
    max_cases: int | None,
    delay: float,
    timeout: int,
    download_pdf: bool,
    force: bool,
    dry_run: bool,
    scope: str,
    custom_terms: tuple[str, ...],
) -> int:
    resolved_scope = resolve_scope(config, scope)
    all_years = discover_years(config, timeout)
    years = filter_years(all_years, start_year, end_year)
    current_year = max(all_years)
    if not years:
        print(f"No {config.court} years matched the requested range.")
        return 0

    print(
        f"Harvesting {config.court}: {len(years):,} year(s), "
        f"scope={resolved_scope}, pdf={'yes' if download_pdf else 'no'}."
    )
    documents: list[CaseDocument] = []
    errors: list[str] = []
    interrupted = False
    printed_dry_run_rows = 0
    total_discovered = 0
    total_selected = 0
    remaining = max_cases
    manifest_path = data_dir / "manifest.jsonl"

    for year in years:
        try:
            year_cases = discover_cases_for_year(config, year, current_year, timeout, delay)
        except SiteAccessInterrupted as exc:
            message = f"{config.source_url} year {year}: {exc}"
            errors.append(message)
            interrupted = True
            print(f"STOP {message}", file=sys.stderr)
            break
        except Exception as exc:  # noqa: BLE001 - keep long harvests moving and record failures.
            message = f"{config.source_url} year {year}: {exc}"
            errors.append(message)
            print(f"ERROR {message}", file=sys.stderr)
            continue

        total_discovered += len(year_cases)
        year_cases = filter_by_scope(config, year_cases, resolved_scope, custom_terms)
        if remaining is not None:
            year_cases = year_cases[:remaining]
        total_selected += len(year_cases)
        print(f"Year {year}: discovered {len(year_cases):,} selected decision(s).")

        if dry_run:
            for summary in year_cases:
                if printed_dry_run_rows >= 20:
                    break
                reason = tax_relevance_reason(summary, custom_terms=custom_terms)
                suffix = f" [{reason}]" if reason else ""
                print(f"{summary.decision_date} {summary.citation} {summary.title}{suffix}")
                printed_dry_run_rows += 1
        else:
            for index, summary in enumerate(year_cases, start=1):
                try:
                    document = download_case(
                        config,
                        summary,
                        output_dir,
                        data_dir,
                        timeout=timeout,
                        delay=delay,
                        force=force,
                        download_pdf=download_pdf,
                        scope=resolved_scope,
                        custom_terms=custom_terms,
                    )
                    if document is None:
                        print(f"[{year} {index}/{len(year_cases)}] skipped after detail filter: {summary.citation} {summary.title}")
                        continue
                    documents.append(document)
                    print(f"[{year} {index}/{len(year_cases)}] {summary.citation} {summary.title}")
                except SiteAccessInterrupted as exc:
                    message = f"{summary.item_url}: {exc}"
                    errors.append(message)
                    interrupted = True
                    print(f"STOP {message}", file=sys.stderr)
                    break
                except Exception as exc:  # noqa: BLE001 - keep long harvests moving and record failures.
                    message = f"{summary.item_url}: {exc}"
                    errors.append(message)
                    print(f"ERROR {message}", file=sys.stderr)

            write_manifest(manifest_path, output_dir, config, documents)
            write_readme(output_dir, manifest_path, config, len(documents), download_pdf, resolved_scope)

        if interrupted:
            break
        if remaining is not None:
            remaining -= len(year_cases)
            if remaining <= 0:
                break

    if dry_run:
        print(
            f"Discovered {total_discovered:,} {config.court} decision(s); "
            f"{total_selected:,} selected for scope={resolved_scope}."
        )
        return 2 if interrupted else 0

    write_manifest(manifest_path, output_dir, config, documents)
    write_readme(output_dir, manifest_path, config, len(documents), download_pdf, resolved_scope)
    if errors:
        error_path = data_dir / "errors.log"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text("\n".join(errors) + "\n", encoding="utf-8")
        print(f"Completed with {len(errors):,} error(s). See {relative_to_root(error_path)}.", file=sys.stderr)
        return 2 if interrupted else 1
    print(f"Wrote {len(documents):,} Markdown decision(s) and {relative_to_root(manifest_path)}.")
    return 0


def selected_courts(args: argparse.Namespace) -> list[str]:
    if args.all_courts:
        return ["tcc", "fca", "scc", "fc"]
    return args.court or ["tcc"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--court", action="append", choices=sorted(COURTS), help="Court to harvest. Repeatable.")
    parser.add_argument("--all-courts", action="store_true", help="Harvest TCC, FCA, SCC, and FC.")
    parser.add_argument("--output-dir", type=Path, help="Override output directory for a single selected court.")
    parser.add_argument("--data-dir", type=Path, help="Override raw-data directory for a single selected court.")
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--max-cases", type=int, help="Limit downloads for smoke tests.")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between requests in seconds.")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--pdf", action="store_true", help="Also mirror the source PDFs.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing downloaded files.")
    parser.add_argument("--dry-run", action="store_true", help="Discover and report cases without downloading.")
    parser.add_argument(
        "--scope",
        choices=("auto", "tax", "all"),
        default="auto",
        help="auto means all TCC decisions and tax-relevant FCA/SCC/FC decisions.",
    )
    parser.add_argument(
        "--include-term",
        action="append",
        default=[],
        help="Additional case-insensitive term that marks a non-TCC case as tax-relevant.",
    )
    args = parser.parse_args(argv)

    court_keys = selected_courts(args)
    if len(court_keys) > 1 and (args.output_dir or args.data_dir):
        parser.error("--output-dir and --data-dir can only be used with one --court")

    status = 0
    for key in court_keys:
        config = COURTS[key]
        output_dir = args.output_dir or config.output_dir
        data_dir = args.data_dir or config.data_dir
        try:
            court_status = run_court(
                config,
                output_dir=output_dir,
                data_dir=data_dir,
                start_year=args.start_year,
                end_year=args.end_year,
                max_cases=args.max_cases,
                delay=args.delay,
                timeout=args.timeout,
                download_pdf=args.pdf,
                force=args.force,
                dry_run=args.dry_run,
                scope=args.scope,
                custom_terms=tuple(args.include_term),
            )
        except SiteAccessInterrupted as exc:
            print(f"STOP {config.court}: {exc}", file=sys.stderr)
            court_status = 2
        status = max(status, court_status)
        if court_status == 2:
            break
    return status


if __name__ == "__main__":
    raise SystemExit(main())
