#!/usr/bin/env python3
"""Download CRA video gallery pages and convert transcripts to Markdown."""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

from lxml import etree, html


BASE = "https://www.canada.ca"
DEFAULT_GALLERY_URL = "https://www.canada.ca/en/revenue-agency/news/cra-multimedia-library/businesses-video-gallery.html"


@dataclass(frozen=True)
class VideoRow:
    title: str
    url: str
    description: str
    series: str


def clean_url(url: str, base: str = BASE) -> str | None:
    if not url or url.startswith(("mailto:", "tel:", "javascript:")):
        return None
    joined = urljoin(base, url)
    joined, _fragment = urldefrag(joined)
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "www.canada.ca":
        return None
    if parsed.path.startswith("/content/canadasite/"):
        parsed = parsed._replace(path=parsed.path.removeprefix("/content/canadasite"))
    if not parsed.path.endswith(".html"):
        return None
    return parsed._replace(scheme="https", query="", fragment="").geturl()


def cache_path(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    stem = Path(urlparse(url).path).stem
    return cache_dir / f"{digest}-{stem}.html"


def parse_doc(path: Path) -> html.HtmlElement:
    return html.fromstring(path.read_bytes())


def cached_paths_by_url(cache_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in cache_dir.glob("*.html"):
        try:
            doc = parse_doc(path)
        except (OSError, etree.ParserError):
            continue
        canonical = doc.xpath("//link[@rel='canonical']/@href")
        if canonical:
            url = clean_url(canonical[0])
            if url:
                paths[url] = path
    return paths


def find_gallery(cache_dir: Path, gallery_url: str) -> Path | None:
    return cached_paths_by_url(cache_dir).get(gallery_url)


def text_content(node: html.HtmlElement) -> str:
    return " ".join(node.text_content().split())


def header_map(table: html.HtmlElement) -> dict[str, int]:
    headers = [text_content(th).lower() for th in table.xpath(".//thead//th")]
    return {header: index for index, header in enumerate(headers)}


def header_index(headers: dict[str, int], *needles: str) -> int | None:
    for header, index in headers.items():
        if all(needle in header for needle in needles):
            return index
    return None


def clean_gallery_title(value: str) -> str:
    return re.sub(r"^(Video|Infographic)\s+", "", value).strip()


def gallery_rows(cache_dir: Path, gallery_url: str = DEFAULT_GALLERY_URL) -> list[VideoRow]:
    gallery = find_gallery(cache_dir, gallery_url)
    if not gallery:
        return []
    doc = parse_doc(gallery)
    rows: list[VideoRow] = []
    seen_urls: set[str] = set()
    for table in doc.xpath("//main//table"):
        headers = header_map(table)
        title_index = header_index(headers, "title")
        if title_index is None:
            title_index = 0
        description_index = header_index(headers, "description")
        series_index = header_index(headers, "series")
        media_type_index = header_index(headers, "media", "type")
        for tr in table.xpath(".//tbody/tr"):
            cells = tr.xpath("./td")
            if len(cells) <= title_index:
                continue
            media_type = ""
            if media_type_index is not None and len(cells) > media_type_index:
                media_type = text_content(cells[media_type_index]).lower()
            title_cell = cells[title_index]
            title_text = text_content(title_cell)
            if media_type and media_type != "video":
                continue
            if not media_type and title_text.lower().startswith("infographic "):
                continue
            link = title_cell.xpath(".//h2//a[@href]") or title_cell.xpath(".//a[@href]")
            if not link:
                continue
            url = clean_url(link[0].get("href"), gallery_url)
            if not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            if description_index is not None and len(cells) > description_index:
                description = text_content(cells[description_index])
            else:
                description = " ".join(text_content(p) for p in title_cell.xpath(".//p"))
            series = ""
            if series_index is not None and len(cells) > series_index:
                series = text_content(cells[series_index])
            rows.append(
                VideoRow(
                    title=clean_gallery_title(text_content(link[0]) or title_text),
                    url=url,
                    description=description,
                    series=series,
                )
            )
    return rows


def write_curl_config(rows: list[VideoRow], cache_dir: Path, config_path: Path) -> int:
    cached = cached_paths_by_url(cache_dir)
    missing = [row.url for row in rows if row.url not in cached]
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


def relative_markdown_path(url: str) -> Path:
    path = urlparse(url).path
    prefix = "/en/revenue-agency/news/cra-multimedia-library/"
    if path.startswith(prefix):
        rel = path.split(prefix, 1)[1]
    else:
        rel = Path(path).name
    return Path(rel).with_suffix(".md")


def inline_md(node) -> str:
    tag = node.tag.lower() if isinstance(node.tag, str) else ""
    if tag == "br":
        return "\n"
    parts = [node.text or ""]
    for child in node:
        parts.append(inline_md(child))
        parts.append(child.tail or "")
    text = re.sub(r"\s+", " ", "".join(parts)).strip()
    if not text:
        return ""
    if tag == "a":
        href = clean_url(node.get("href", ""), BASE) or node.get("href", "")
        return f"[{text}]({href})"
    if tag in {"strong", "b"}:
        return f"**{text}**"
    if tag in {"em", "i"}:
        return f"*{text}*"
    return text


def table_to_md(table: html.HtmlElement) -> list[str]:
    rows = []
    for tr in table.xpath(".//tr"):
        cells = tr.xpath("./th|./td")
        if cells:
            rows.append([inline_md(cell).replace("\n", " ").strip() for cell in cells])
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def block_md(node: html.HtmlElement, depth: int = 0) -> list[str]:
    tag = node.tag.lower() if isinstance(node.tag, str) else ""
    if tag in {"script", "style", "figure"}:
        return []
    if tag in {"h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        return [f"{'#' * level} {text_content(node)}"]
    if tag == "p":
        value = inline_md(node)
        return [value] if value else []
    if tag in {"ul", "ol"}:
        lines: list[str] = []
        ordered = tag == "ol"
        for index, li in enumerate(node.xpath("./li"), 1):
            marker = f"{index}." if ordered else "-"
            first = inline_md(li).strip()
            if first:
                lines.append(f"{'  ' * depth}{marker} {first}")
        return lines
    if tag == "table":
        return table_to_md(node)
    if tag in {"div", "section", "article", "details"}:
        lines: list[str] = []
        for child in node:
            lines.extend(block_md(child, depth))
        return lines
    return []


def modified_date(doc: html.HtmlElement) -> str | None:
    dates = [text_content(node) for node in doc.xpath("//gcds-date-modified")]
    return dates[0] if dates else None


def page_title(doc: html.HtmlElement) -> str:
    h1 = doc.xpath("//main//h1")
    if h1:
        return text_content(h1[0])
    title = doc.xpath("//title/text()")
    return title[0].replace(" - Canada.ca", "").strip() if title else "Untitled"


def video_source(doc: html.HtmlElement) -> str | None:
    source = doc.xpath("//main//figure[contains(@class, 'wb-mltmd')]//source/@src")
    return source[0] if source else None


def transcript_blocks(doc: html.HtmlElement) -> list[str]:
    headings = [
        h
        for h in doc.xpath("//main//*[self::h2 or self::h3]")
        if "transcript" in text_content(h).lower()
    ]
    if not headings:
        headings = [
            h
            for h in doc.xpath("//main//*[self::h2 or self::h3]")
            if "speaking notes" in text_content(h).lower()
        ]
    if not headings:
        headings = [
            h
            for h in doc.xpath("//main//h1")
            if text_content(h).lower().startswith("transcript")
        ]
    if not headings:
        return []
    heading = headings[0]
    lines = ["## Transcript"]
    parent = heading.getparent()
    if parent is None:
        return lines
    siblings = list(parent)
    start = siblings.index(heading) + 1
    for node in siblings[start:]:
        tag = node.tag.lower() if isinstance(node.tag, str) else ""
        if tag == "section" and "pagedetails" in (node.get("class") or "").split():
            break
        if tag in {"h1", "h2"}:
            break
        lines.extend(block_md(node))
    return [line for line in lines if line]


def write_transcripts(cache_dir: Path, output_dir: Path, gallery_url: str) -> tuple[int, list[str]]:
    if output_dir.exists():
        for path in sorted(output_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    output_dir.mkdir(parents=True, exist_ok=True)
    cached = cached_paths_by_url(cache_dir)
    written = 0
    issues: list[str] = []
    for row in gallery_rows(cache_dir, gallery_url):
        path = cached.get(row.url)
        if not path:
            issues.append(f"missing: {row.title} - {row.url}")
            continue
        doc = parse_doc(path)
        transcript = transcript_blocks(doc)
        if not transcript:
            issues.append(f"no transcript found: {row.title} - {row.url}")
            continue
        title = page_title(doc) or row.title
        front_matter = [
            "---",
            f'title: "{title.replace(chr(34), chr(39))}"',
            f'gallery_title: "{row.title.replace(chr(34), chr(39))}"',
            f"source: {row.url}",
        ]
        if row.series and row.series != "|none|":
            front_matter.append(f'series: "{row.series.replace(chr(34), chr(39))}"')
        video = video_source(doc)
        if video:
            front_matter.append(f"video_source: {video}")
        date = modified_date(doc)
        if date:
            front_matter.append(f"last_modified: {date}")
        front_matter.extend(["---", "", f"# {title}", ""])
        out = output_dir / relative_markdown_path(row.url)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(front_matter + transcript) + "\n", encoding="utf-8")
        written += 1
    return written, issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices={"discover", "convert"})
    parser.add_argument("--gallery-url", default=DEFAULT_GALLERY_URL)
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/taxsmith_cra_videos"))
    parser.add_argument("--curl-config", type=Path, default=Path("/private/tmp/taxsmith_cra_videos/curl.config"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/cra/multimedia/businesses-video-transcripts"))
    args = parser.parse_args()

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    gallery_url = clean_url(args.gallery_url) or args.gallery_url
    rows = gallery_rows(args.cache_dir, gallery_url)
    if args.mode == "discover":
        if not rows:
            print(f"gallery_missing={gallery_url}")
            return
        missing = write_curl_config(rows, args.cache_dir, args.curl_config)
        print(f"videos={len(rows)} missing={missing} config={args.curl_config}")
    else:
        written, issues = write_transcripts(args.cache_dir, args.output_dir, gallery_url)
        print(f"transcripts={written} issues={len(issues)} output={args.output_dir}")
        for issue in issues:
            print(issue)


if __name__ == "__main__":
    main()
