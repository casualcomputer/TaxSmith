#!/usr/bin/env python3
"""Mirror CRA income tax current publications into Markdown.

The script has two modes:

1. discover: read cached HTML pages and emit a curl config for missing pages.
2. convert: convert all cached in-scope pages to Markdown.

Network fetching is intentionally left to curl so the fetch step is auditable and
can be retried independently.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urldefrag

from lxml import etree, html


BASE = "https://www.canada.ca"
START_URL = (
    "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/"
    "income-tax/current-publications.html"
)
PUBLICATIONS_INDEX_URL = "https://www.canada.ca/en/revenue-agency/services/forms-publications/publications.html"
BROKEN_PUBLICATION_PDF_RECOVERIES = {
    "https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4215.html": (
        "https://www.canada.ca/content/dam/cra-arc/formspubs/pub/rc4215/rc4215-23e.pdf"
    ),
}
SEED_URLS = [
    START_URL,
    "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html",
    "https://www.canada.ca/en/revenue-agency/services/forms-publications/current-income-tax-information-circulars-6.html",
    "https://www.canada.ca/en/revenue-agency/services/forms-publications/current-income-tax-interpretation-bulletins-9.html",
    "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/current-income-tax-technical-news-ittn.html",
]

SUPPORTING_INCOME_TAX_SLUGS = {
    "introducing-income-tax-folios",
    "table-concordance-bulletin-folio",
    "whats-new-income-tax-folios",
    "list-cancelled-interpretation-bulletins",
    "what-archived-content-notice-means-interpretation-bulletins",
    "cancellation-income-tax-technical-publications",
    "table-concordance-ittn-folio",
}


def clean_url(url: str, base: str = BASE) -> str | None:
    if not url or url.startswith(("mailto:", "tel:", "javascript:")):
        return None
    joined = urljoin(base, url)
    joined, _fragment = urldefrag(joined)
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "www.canada.ca":
        return None
    if "%20" in parsed.path:
        return None
    if ".html/" in parsed.path:
        return None
    if not parsed.path.endswith(".html"):
        return None
    return parsed._replace(scheme="https", query="", fragment="").geturl()


def slugify(value: str) -> str:
    value = html_lib.unescape(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def cache_path(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return cache_dir / f"{digest}.html"


def relative_markdown_path(url: str) -> Path | None:
    path = urlparse(url).path
    name = Path(path).stem

    if url == START_URL:
        return Path("index.md")
    if path.endswith("/income-tax-folios-index.html"):
        return Path("folios/index.md")
    if "/income-tax-folios-index/" in path:
        rel = path.split("/income-tax-folios-index/", 1)[1]
        parts = rel.split("/")
        if len(parts) == 1:
            return Path("folios") / f"{Path(parts[0]).stem}.md"
        if parts[-1].startswith("folio-") or parts[-1].startswith("series-"):
            return Path("folios", *parts[:-1], Path(parts[-1]).stem, "index.md")
        return Path("folios", *parts[:-1], f"{Path(parts[-1]).stem}.md")

    ic_indexes = {
        "current-income-tax-information-circulars-6": "index.md",
        "current-income-tax-information-circulars": "ic00-ic09/index.md",
        "current-income-tax-information-circulars-1": "ic10-ic19/index.md",
        "current-income-tax-information-circulars-2": "ic70-ic79/index.md",
        "current-income-tax-information-circulars-3": "ic80-ic89/index.md",
        "current-income-tax-information-circulars-4": "ic90-ic99/index.md",
    }
    if name in ic_indexes:
        return Path("information-circulars") / ic_indexes[name]

    it_indexes = {
        "current-income-tax-interpretation-bulletins-9": "index.md",
        "current-income-tax-interpretation-bulletins-8": "it050-it099/index.md",
        "current-income-tax-interpretation-bulletins-10": "it100-it149/index.md",
        "current-income-tax-interpretation-bulletins-1": "it150-it199/index.md",
        "current-income-tax-interpretation-bulletins-2": "it200-it249/index.md",
        "current-income-tax-interpretation-bulletins-3": "it250-it299/index.md",
        "current-income-tax-interpretation-bulletins-4": "it300-it349/index.md",
        "current-income-tax-interpretation-bulletins-5": "it350-it399/index.md",
        "current-income-tax-interpretation-bulletins-6": "it400-it449/index.md",
        "current-income-tax-interpretation-bulletins-7": "it450-it499/index.md",
        "current-income-tax-interpretation-bulletins": "it500-it549/index.md",
    }
    if name in it_indexes:
        return Path("interpretation-bulletins") / it_indexes[name]

    if name == "current-income-tax-technical-news-ittn":
        return Path("technical-news/index.md")

    if name in SUPPORTING_INCOME_TAX_SLUGS:
        return Path("supporting") / f"{name}.md"

    if "/services/forms-publications/publications/" in path:
        publication_rel = path.split("/services/forms-publications/publications/", 1)[1]
        publication_parts = publication_rel.split("/")
        publication_root = Path(publication_parts[0]).stem
        publication_tail = [Path(part).stem if part.endswith(".html") else part for part in publication_parts]
        if publication_root.startswith("ic"):
            return Path("information-circulars/publications", *publication_tail).with_suffix(".md")
        if publication_root.startswith("itnews") or publication_root.startswith("archived-technical-tax-topics"):
            return Path("technical-news/publications", *publication_tail).with_suffix(".md")
        if publication_root.startswith("it-") or publication_root in {"it-index"}:
            return Path("interpretation-bulletins/publications", *publication_tail).with_suffix(".md")
        if "archived-income-tax-act-workgroup-cross-reference-chart" in name:
            return Path("technical-news/publications") / f"{name}.md"

    return None


def forms_publications_markdown_path(url: str) -> Path | None:
    path = urlparse(url).path
    prefix = "/en/revenue-agency/services/forms-publications/"
    if not path.startswith(prefix) or not path.endswith(".html"):
        return None
    rel = path.split(prefix, 1)[1]
    return Path(rel).with_suffix(".md")


def forms_publications_pdf_path(url: str, pdf_cache_dir: Path) -> Path:
    parsed = urlparse(url)
    name = Path(parsed.path).name or "publication.pdf"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return pdf_cache_dir / f"{digest}-{name}"


def parse_doc(path: Path) -> html.HtmlElement:
    return html.fromstring(path.read_bytes())


def cache_paths_by_url(cache_dir: Path) -> dict[str, Path]:
    paths = {}
    for path in cache_dir.glob("*.html"):
        try:
            doc = parse_doc(path)
        except (etree.ParserError, OSError):
            continue
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        if canonical:
            url = clean_url(canonical[0])
            if url:
                paths[url] = path
    return paths


def cached_urls(cache_dir: Path) -> set[str]:
    return set(cache_paths_by_url(cache_dir))


def discover_links(cache_dir: Path) -> set[str]:
    urls = set(SEED_URLS)
    for path in cache_dir.glob("*.html"):
        try:
            doc = parse_doc(path)
        except (etree.ParserError, OSError):
            continue
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        base = clean_url(canonical[0]) if canonical else BASE
        main = doc.xpath("//main")
        root = main[0] if main else doc
        for href in root.xpath(".//a[@href]/@href"):
            url = clean_url(href, base or BASE)
            if url and relative_markdown_path(url):
                urls.add(url)
    return urls


def publications_index_urls(cache_dir: Path) -> set[str]:
    urls = {PUBLICATIONS_INDEX_URL}
    for path in cache_dir.glob("*.html"):
        try:
            doc = parse_doc(path)
        except (etree.ParserError, OSError):
            continue
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        canonical_url = clean_url(canonical[0]) if canonical else None
        if canonical_url != PUBLICATIONS_INDEX_URL:
            continue
        for href in doc.xpath("//main//table//tbody/tr/td[1]//a[@href]/@href"):
            url = clean_url(href, canonical_url)
            if url and forms_publications_markdown_path(url):
                urls.add(url)
    return urls


def is_publications_descendant(url: str, root_urls: set[str]) -> bool:
    path = urlparse(url).path
    root_paths = {urlparse(root).path for root in root_urls}
    if path in root_paths:
        return True
    descendant_prefixes = {
        root_path[:-5] + "/"
        for root_path in root_paths
        if root_path.endswith(".html")
    }
    return any(path.startswith(prefix) for prefix in descendant_prefixes)


def discover_publications_links(cache_dir: Path) -> set[str]:
    roots = publications_index_urls(cache_dir)
    urls = set(roots)
    for path in cache_dir.glob("*.html"):
        try:
            doc = parse_doc(path)
        except (etree.ParserError, OSError):
            continue
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        base = clean_url(canonical[0]) if canonical else BASE
        if not base or not is_publications_descendant(base, roots):
            continue
        main = doc.xpath("//main")
        root = main[0] if main else doc
        for href in root.xpath(".//a[@href]/@href"):
            url = clean_url(href, base)
            if url and forms_publications_markdown_path(url) and is_publications_descendant(url, roots):
                urls.add(url)
    return urls


def write_curl_config(urls: Iterable[str], cache_dir: Path, config_path: Path) -> int:
    cached = cached_urls(cache_dir)
    missing = [url for url in sorted(urls) if url not in cached]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        for url in missing:
            handle.write(f"url = {url}\n")
            handle.write(f"output = {cache_path(cache_dir, url)}\n")
            handle.write("location\n")
            handle.write("fail\n")
            handle.write("silent\n")
            handle.write("show-error\n\n")
    return len(missing)


def write_pdf_curl_config(urls: Iterable[str], pdf_cache_dir: Path, config_path: Path) -> int:
    pdf_cache_dir.mkdir(parents=True, exist_ok=True)
    missing = [url for url in sorted(urls) if not forms_publications_pdf_path(url, pdf_cache_dir).exists()]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        for url in missing:
            handle.write(f"url = {url}\n")
            handle.write(f"output = {forms_publications_pdf_path(url, pdf_cache_dir)}\n")
            handle.write("location\n")
            handle.write("fail\n")
            handle.write("silent\n")
            handle.write("show-error\n\n")
    return len(missing)


def text_content(node: html.HtmlElement) -> str:
    return " ".join(node.text_content().split())


def inline_md(node) -> str:
    if isinstance(node, str):
        return node
    tag = node.tag.lower() if isinstance(node.tag, str) else ""
    parts = [node.text or ""]
    for child in node:
        parts.append(inline_md(child))
        parts.append(child.tail or "")
    text = "".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if tag == "a":
        href = clean_url(node.get("href", ""), BASE)
        return f"[{text}]({href or node.get('href')})"
    if tag in {"em", "i"}:
        return f"*{text}*"
    if tag in {"strong", "b"}:
        return f"**{text}**"
    if tag == "code":
        return f"`{text}`"
    if tag == "br":
        return "\n"
    return text


def inline_md_without_nested_blocks(node: html.HtmlElement) -> str:
    parts = [node.text or ""]
    for child in node:
        child_tag = child.tag.lower() if isinstance(child.tag, str) else ""
        if child_tag in {"ul", "ol", "table"}:
            parts.append(child.tail or "")
            continue
        parts.append(inline_md(child))
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def table_to_md(table: html.HtmlElement) -> list[str]:
    rows = []
    for tr in table.xpath(".//tr"):
        cells = tr.xpath("./th|./td")
        if not cells:
            continue
        rows.append([inline_md(cell).replace("\n", " ").strip() for cell in cells])
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    output = ["| " + " | ".join(rows[0]) + " |"]
    output.append("| " + " | ".join(["---"] * width) + " |")
    for row in rows[1:]:
        output.append("| " + " | ".join(row) + " |")
    return output


def block_md(node: html.HtmlElement, depth: int = 0) -> list[str]:
    tag = node.tag.lower() if isinstance(node.tag, str) else ""
    if tag in {"script", "style", "nav", "aside", "button", "gcds-date-modified"}:
        return []
    if "pagedetails" in (node.get("class") or "").split():
        return []
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        return [f"{'#' * level} {text_content(node)}"]
    if tag == "p":
        value = inline_md(node)
        return [value] if value else []
    if tag in {"ul", "ol"}:
        lines = []
        ordered = tag == "ol"
        for index, li in enumerate(node.xpath("./li"), 1):
            marker = f"{index}." if ordered else "-"
            first = inline_md_without_nested_blocks(li)
            child_blocks = []
            for child in li:
                if isinstance(child.tag, str) and child.tag.lower() in {"ul", "ol", "table"}:
                    child_blocks.extend(block_md(child, depth + 1))
            if first:
                lines.append(f"{'  ' * depth}{marker} {first}")
            for child_line in child_blocks:
                lines.append(f"{'  ' * (depth + 1)}{child_line}")
        return lines
    if tag == "table":
        return table_to_md(node)
    if tag == "dl":
        lines = []
        for child in node:
            child_tag = child.tag.lower() if isinstance(child.tag, str) else ""
            if child_tag == "dt":
                lines.append(f"**{inline_md(child)}**")
            elif child_tag == "dd":
                value = inline_md(child)
                if value:
                    lines.append(value)
        return lines
    if tag in {"div", "section", "main", "article"}:
        lines = []
        for child in node:
            lines.extend(block_md(child, depth))
        return lines
    return []


def page_title(doc: html.HtmlElement) -> str:
    h1 = doc.xpath("//main//h1")
    if h1:
        return text_content(h1[0])
    title = doc.xpath("//title/text()")
    return title[0].replace(" - Canada.ca", "").strip() if title else "Untitled"


def modified_date(doc: html.HtmlElement) -> str | None:
    dates = [text_content(node) for node in doc.xpath("//gcds-date-modified")]
    return dates[0] if dates else None


def convert_page(url: str, html_path: Path, output_path: Path) -> None:
    doc = parse_doc(html_path)
    main = doc.xpath("//main")
    if not main:
        return
    title = page_title(doc)
    date = modified_date(doc)
    front_matter = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"source: {url}",
    ]
    if date:
        front_matter.append(f"last_modified: {date}")
    front_matter.extend(["---", ""])

    body = block_md(main[0])
    if body and body[0].startswith("# "):
        body_lines = body
    else:
        body_lines = [f"# {title}", *body]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = "\n".join(front_matter) + "\n\n".join(body_lines) + "\n"
    output_path.write_text(output, encoding="utf-8")


def pdf_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = result.stdout.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_pdf_page(
    title: str,
    source_url: str,
    pdf_url: str,
    html_path: Path | None,
    pdf_path: Path,
    output_path: Path,
    last_modified: str | None = None,
) -> None:
    date = last_modified
    if html_path:
        doc = parse_doc(html_path)
        date = modified_date(doc) or date
    front_matter = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"source: {source_url}",
        f"pdf_source: {pdf_url}",
        "extracted_from_pdf: true",
    ]
    if date:
        front_matter.append(f"last_modified: {date}")
    front_matter.extend(["---", ""])
    body = pdf_text(pdf_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(front_matter) + f"# {title}\n\n" + body + "\n", encoding="utf-8")


def page_kind(rel: Path, doc: html.HtmlElement) -> str:
    body_text = "\n".join(block_md(doc.xpath("//main")[0])) if doc.xpath("//main") else ""
    rel_text = rel.as_posix()
    if rel.name == "index.md":
        return "navigation"
    if "The chapters currently available in this folio are" in body_text:
        return "navigation"
    if rel_text.startswith("supporting/") or "chapter-history" in rel_text:
        return "supporting"
    if "You can **view** this publication in:" in body_text:
        return "wrapper"
    return "ultimate"


def publication_title_from_index(cache_dir: Path, url: str) -> str:
    index_path = cache_paths_by_url(cache_dir).get(PUBLICATIONS_INDEX_URL)
    if not index_path:
        return Path(urlparse(url).path).stem
    doc = parse_doc(index_path)
    for tr in doc.xpath("//main//table//tbody/tr"):
        hrefs = tr.xpath("./td[1]//a[@href]/@href")
        if not hrefs:
            continue
        row_url = clean_url(hrefs[0], PUBLICATIONS_INDEX_URL)
        if row_url == url:
            cells = [" ".join(td.text_content().split()) for td in tr.xpath("./td")]
            if len(cells) >= 2:
                return f"{cells[0]} - {cells[1]}".strip(" -")
    return Path(urlparse(url).path).stem


def publication_metadata_from_index(cache_dir: Path, url: str) -> tuple[str, str | None]:
    index_path = cache_paths_by_url(cache_dir).get(PUBLICATIONS_INDEX_URL)
    if not index_path:
        return Path(urlparse(url).path).stem, None
    doc = parse_doc(index_path)
    for tr in doc.xpath("//main//table//tbody/tr"):
        hrefs = tr.xpath("./td[1]//a[@href]/@href")
        if not hrefs:
            continue
        row_url = clean_url(hrefs[0], PUBLICATIONS_INDEX_URL)
        if row_url == url:
            cells = [" ".join(td.text_content().split()) for td in tr.xpath("./td")]
            title = f"{cells[0]} - {cells[1]}".strip(" -") if len(cells) >= 2 else Path(urlparse(url).path).stem
            last_update = cells[2] if len(cells) >= 3 else None
            return title, last_update
    return Path(urlparse(url).path).stem, None


def pdf_only_publications(cache_dir: Path) -> dict[str, tuple[str, str]]:
    roots = publications_index_urls(cache_dir)
    paths = cache_paths_by_url(cache_dir)
    pdfs = {}
    for url in sorted(roots):
        if url == PUBLICATIONS_INDEX_URL:
            continue
        html_path = paths.get(url)
        if not html_path:
            continue
        doc = parse_doc(html_path)
        main = doc.xpath("//main")
        root = main[0] if main else doc
        body_text = " ".join(root.text_content().split())
        pdf_links = [
            urljoin(url, href)
            for href in root.xpath(".//a[@href]/@href")
            if ".pdf" in href.lower()
        ]
        html_links = [
            clean_url(href, url)
            for href in root.xpath(".//a[@href]/@href")
            if clean_url(href, url) and is_publications_descendant(clean_url(href, url), roots)
        ]
        if pdf_links and not html_links and "You can" in body_text and "publication" in body_text.lower():
            pdfs[url] = (publication_title_from_index(cache_dir, url), pdf_links[0])
    for url, pdf_url in BROKEN_PUBLICATION_PDF_RECOVERIES.items():
        title, _last_update = publication_metadata_from_index(cache_dir, url)
        pdfs[url] = (title, pdf_url)
    return pdfs


def convert_all(cache_dir: Path, output_dir: Path) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    count = 0
    manifest: dict[str, list[tuple[str, str]]] = {
        "ultimate": [],
        "navigation": [],
        "wrapper": [],
        "supporting": [],
    }
    paths = cache_paths_by_url(cache_dir)
    for url in sorted(paths):
        rel = relative_markdown_path(url)
        if not rel:
            continue
        path = paths[url]
        doc = parse_doc(path)
        convert_page(url, path, output_dir / rel)
        manifest[page_kind(rel, doc)].append((str(rel), url))
        count += 1
    manifest_lines = [
        "# CRA Income Tax Current Publications",
        "",
        f"Source index: {START_URL}",
        "",
        "## Counts",
        "",
        f"- Ultimate publication text pages: {len(manifest['ultimate'])}",
        f"- Navigation/index pages: {len(manifest['navigation'])}",
        f"- Publication wrapper pages: {len(manifest['wrapper'])}",
        f"- Supporting/history pages: {len(manifest['supporting'])}",
        "",
        "## All Mirrored Pages",
        "",
    ]
    for kind, title in [
        ("ultimate", "Ultimate Publication Text Pages"),
        ("navigation", "Navigation/Index Pages"),
        ("wrapper", "Publication Wrapper Pages"),
        ("supporting", "Supporting/History Pages"),
    ]:
        manifest_lines.extend([f"### {title}", ""])
        for rel, url in manifest[kind]:
            manifest_lines.append(f"- [{rel}]({rel}) - {url}")
        manifest_lines.append("")
    (output_dir / "MANIFEST.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    ultimate_lines = [
        "# Ultimate CRA Income Tax Publication Text Pages",
        "",
        "This list excludes navigation `index.md` files, wrapper pages that only link to HTML/PDF versions, chapter-history pages, and supporting concordance/admin pages.",
        "",
    ]
    for rel, url in manifest["ultimate"]:
        ultimate_lines.append(f"- [{rel}]({rel}) - {url}")
    (output_dir / "ULTIMATE_PUBLICATIONS.md").write_text("\n".join(ultimate_lines) + "\n", encoding="utf-8")
    return count


def convert_rag_corpus(cache_dir: Path, output_dir: Path) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    count = 0
    paths = cache_paths_by_url(cache_dir)
    for url in sorted(paths):
        rel = relative_markdown_path(url)
        if not rel:
            continue
        path = paths[url]
        doc = parse_doc(path)
        if page_kind(rel, doc) != "ultimate":
            continue
        convert_page(url, path, output_dir / rel)
        count += 1
    return count


def convert_publications_rag_corpus(cache_dir: Path, output_dir: Path, pdf_cache_dir: Path) -> int:
    roots = publications_index_urls(cache_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    count = 0
    paths = cache_paths_by_url(cache_dir)
    for url in sorted(paths):
        if url == PUBLICATIONS_INDEX_URL:
            continue
        if not is_publications_descendant(url, roots):
            continue
        rel = forms_publications_markdown_path(url)
        if not rel:
            continue
        path = paths[url]
        doc = parse_doc(path)
        if page_kind(rel, doc) != "ultimate":
            continue
        convert_page(url, path, output_dir / rel)
        count += 1
    for url, (title, pdf_url) in pdf_only_publications(cache_dir).items():
        rel = forms_publications_markdown_path(url)
        html_path = paths.get(url)
        pdf_path = forms_publications_pdf_path(pdf_url, pdf_cache_dir)
        _title, last_update = publication_metadata_from_index(cache_dir, url)
        if not rel or not pdf_path.exists():
            continue
        convert_pdf_page(title, url, pdf_url, html_path, pdf_path, output_dir / rel, last_update)
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices={
            "discover",
            "convert",
            "rag",
            "discover-publications",
            "discover-publication-pdfs",
            "publications-rag",
        },
    )
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/taxsmith_cra_cache"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/cra/income-tax/current-publications"))
    parser.add_argument("--curl-config", type=Path, default=Path("/private/tmp/taxsmith_cra_cache/curl.config"))
    parser.add_argument("--pdf-cache-dir", type=Path, default=Path("/private/tmp/taxsmith_cra_pdf_cache"))
    args = parser.parse_args()

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "discover":
        urls = discover_links(args.cache_dir)
        missing = write_curl_config(urls, args.cache_dir, args.curl_config)
        print(f"discovered={len(urls)} missing={missing} config={args.curl_config}")
    elif args.mode == "discover-publications":
        urls = discover_publications_links(args.cache_dir)
        missing = write_curl_config(urls, args.cache_dir, args.curl_config)
        print(f"discovered={len(urls)} missing={missing} config={args.curl_config}")
    elif args.mode == "discover-publication-pdfs":
        pdfs = {pdf_url for _url, (_title, pdf_url) in pdf_only_publications(args.cache_dir).items()}
        missing = write_pdf_curl_config(pdfs, args.pdf_cache_dir, args.curl_config)
        print(f"pdfs={len(pdfs)} missing={missing} config={args.curl_config}")
    elif args.mode == "convert":
        count = convert_all(args.cache_dir, args.output_dir)
        print(f"converted={count} output={args.output_dir}")
    elif args.mode == "rag":
        count = convert_rag_corpus(args.cache_dir, args.output_dir)
        print(f"rag_documents={count} output={args.output_dir}")
    else:
        count = convert_publications_rag_corpus(args.cache_dir, args.output_dir, args.pdf_cache_dir)
        print(f"publications_rag_documents={count} output={args.output_dir}")


if __name__ == "__main__":
    main()
