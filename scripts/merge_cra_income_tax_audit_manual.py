#!/usr/bin/env python3
"""Merge Canada.ca Income Tax Audit Manual chapters into one Markdown file."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_TOC_URL = (
    "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/"
    "income-tax-audit-manual-domestic-compliance-programs-branch-dcpb-5.html"
)
DEFAULT_OUTPUT = Path("data/cra_income_tax_audit_manual.md")
USER_AGENT = "Taxsmith CRA manual merger/0.1 (+https://www.canada.ca/)"


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)


@dataclass(frozen=True)
class ChapterLink:
    title: str
    url: str


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {name.lower(): value or "" for name, value in attrs})
        self.stack[-1].children.append(node)
        if tag.lower() not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].children.append(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.stack[-1].children.append(unescape(f"&#{name};"))


def parse_html(html: str) -> Node:
    parser = TreeBuilder()
    parser.feed(html)
    parser.close()
    return parser.root


def walk(node: Node | str) -> Iterable[Node]:
    if isinstance(node, str):
        return
    yield node
    for child in node.children:
        yield from walk(child)


def text_content(node: Node | str) -> str:
    if isinstance(node, str):
        return node
    if node.tag in {"script", "style"}:
        return ""
    if node.tag == "br":
        return "\n"
    return "".join(text_content(child) for child in node.children)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def find_first(node: Node, tag: str, **attrs: str) -> Node | None:
    for candidate in walk(node):
        if candidate.tag != tag:
            continue
        if all(candidate.attrs.get(key) == value for key, value in attrs.items()):
            return candidate
    return None


def has_class(node: Node, class_name: str) -> bool:
    return class_name in node.attrs.get("class", "").split()


def remove_nodes(node: Node, predicate) -> None:
    kept: list[Node | str] = []
    for child in node.children:
        if isinstance(child, Node):
            if predicate(child):
                continue
            remove_nodes(child, predicate)
        kept.append(child)
    node.children = kept


def fetch(url: str, timeout: int) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def discover_chapters(toc_html: str, toc_url: str) -> list[ChapterLink]:
    root = parse_html(toc_html)
    main = find_first(root, "main") or root
    chapters: list[ChapterLink] = []
    seen_titles: set[str] = set()
    for link in walk(main):
        if link.tag != "a":
            continue
        title = normalize_space(text_content(link))
        href = link.attrs.get("href", "")
        if not title.startswith("Chapter ") or not href:
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        chapters.append(ChapterLink(title=title, url=urljoin(toc_url, href)))
    if not chapters:
        raise RuntimeError("No chapter links found in the table of contents.")
    return chapters


def markdown_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def inline_markdown(node: Node | str, base_url: str) -> str:
    if isinstance(node, str):
        return normalize_inline(node)
    if node.tag in {"script", "style", "meta", "link"}:
        return ""
    if node.tag == "br":
        return "\n"
    content = "".join(inline_markdown(child, base_url) for child in node.children)
    content = re.sub(r"[ \t]+", " ", content)
    if node.tag in {"strong", "b"}:
        return f"**{content.strip()}**" if content.strip() else ""
    if node.tag in {"em", "i"}:
        return f"*{content.strip()}*" if content.strip() else ""
    if node.tag == "code":
        return f"`{content.strip()}`" if content.strip() else ""
    if node.tag == "a":
        href = node.attrs.get("href", "")
        label = content.strip() or href
        if not href:
            return label
        return f"[{label}]({urljoin(base_url, href)})"
    if node.tag == "img":
        alt = node.attrs.get("alt", "")
        src = node.attrs.get("src", "")
        return f"![{markdown_escape(alt)}]({urljoin(base_url, src)})" if src else ""
    return content


def normalize_inline(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\n]+", " ", text)
    return text


def children_to_markdown(
    children: list[Node | str],
    base_url: str,
    heading_offset: int,
    list_depth: int = 0,
) -> list[str]:
    blocks: list[str] = []
    for child in children:
        blocks.extend(node_to_markdown(child, base_url, heading_offset, list_depth))
    return blocks


def node_to_markdown(
    node: Node | str,
    base_url: str,
    heading_offset: int,
    list_depth: int = 0,
) -> list[str]:
    if isinstance(node, str):
        text = normalize_space(node)
        return [text] if text else []
    if node.tag in {"script", "style", "meta", "link", "noscript"}:
        return []
    if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        text = normalize_space(inline_markdown(node, base_url))
        if not text:
            return []
        level = min(6, int(node.tag[1]) + heading_offset)
        return [f"{'#' * level} {text}"]
    if node.tag == "p":
        text = normalize_space(inline_markdown(node, base_url))
        return [text] if text else []
    if node.tag in {"ul", "ol"}:
        ordered = node.tag == "ol"
        lines: list[str] = []
        item_number = 1
        for child in node.children:
            if isinstance(child, Node) and child.tag == "li":
                lines.extend(list_item_markdown(child, base_url, heading_offset, list_depth, ordered, item_number))
                item_number += 1
        return ["\n".join(lines)] if lines else []
    if node.tag == "blockquote":
        blocks = children_to_markdown(node.children, base_url, heading_offset, list_depth)
        quoted = "\n\n".join(blocks)
        return ["\n".join(f"> {line}" if line else ">" for line in quoted.splitlines())] if quoted else []
    if node.tag == "table":
        return [table_to_markdown(node, base_url)] if table_to_markdown(node, base_url) else []
    if node.tag == "hr":
        return ["---"]
    return children_to_markdown(node.children, base_url, heading_offset, list_depth)


def list_item_markdown(
    node: Node,
    base_url: str,
    heading_offset: int,
    depth: int,
    ordered: bool,
    number: int,
) -> list[str]:
    inline_parts: list[str] = []
    nested_blocks: list[str] = []
    for child in node.children:
        if isinstance(child, Node) and child.tag in {"ul", "ol"}:
            nested_blocks.extend(node_to_markdown(child, base_url, heading_offset, depth + 1))
        elif isinstance(child, Node) and child.tag in {"p", "div"}:
            inline_parts.append(inline_markdown(child, base_url))
        else:
            inline_parts.append(inline_markdown(child, base_url))
    text = normalize_space("".join(inline_parts))
    marker = f"{number}." if ordered else "-"
    indent = "  " * depth
    lines = [f"{indent}{marker} {text}".rstrip()]
    for block in nested_blocks:
        lines.extend(f"{indent}  {line}" if line else "" for line in block.splitlines())
    return lines


def table_to_markdown(table: Node, base_url: str) -> str:
    rows: list[list[str]] = []
    for row in walk(table):
        if row.tag != "tr":
            continue
        cells = [
            normalize_space(inline_markdown(cell, base_url)).replace("|", "\\|")
            for cell in row.children
            if isinstance(cell, Node) and cell.tag in {"th", "td"}
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    separator = ["---"] * width
    body = rows[1:]
    return "\n".join(
        ["| " + " | ".join(header) + " |", "| " + " | ".join(separator) + " |"]
        + ["| " + " | ".join(row) + " |" for row in body]
    )


def extract_main_markdown(html: str, url: str) -> tuple[str, str | None]:
    root = parse_html(html)
    main = find_first(root, "main") or root
    modified = None
    date_node = find_first(main, "gcds-date-modified")
    if date_node is not None:
        modified = normalize_space(text_content(date_node))
    remove_nodes(
        main,
        lambda node: has_class(node, "pagedetails")
        or node.tag in {"script", "style"}
        or node.attrs.get("id") in {"wb-cont"},
    )
    blocks = node_to_markdown(main, url, heading_offset=1)
    markdown = "\n\n".join(block for block in blocks if block.strip())
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown, modified


def build_markdown(toc_url: str, timeout: int, delay: float) -> str:
    fetched: dict[str, str] = {}
    toc_html = fetch(toc_url, timeout)
    fetched[toc_url] = toc_html
    chapters = discover_chapters(toc_html, toc_url)
    _, toc_modified = extract_main_markdown(toc_html, toc_url)

    lines = [
        "# Income Tax Audit Manual",
        "",
        f"Source table of contents: {toc_url}",
        f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
    ]
    if toc_modified:
        lines.append(f"TOC date modified: {toc_modified}")
    lines.extend(["", "## Merged Chapters", ""])
    lines.extend(f"- [{chapter.title}](#{slugify(chapter.title)})" for chapter in chapters)

    for index, chapter in enumerate(chapters, start=1):
        if chapter.url not in fetched:
            if delay and index > 1:
                time.sleep(delay)
            fetched[chapter.url] = fetch(chapter.url, timeout)
        body, modified = extract_main_markdown(fetched[chapter.url], chapter.url)
        lines.extend(["", "---", "", f"## {chapter.title}", "", f"Source: {chapter.url}"])
        if modified:
            lines.append(f"Date modified: {modified}")
        if body:
            body = remove_redundant_top_headings(body)
            lines.extend(["", body])

    return "\n".join(lines).rstrip() + "\n"


def remove_redundant_top_headings(markdown: str) -> str:
    lines = markdown.splitlines()
    while lines and (
        lines[0].startswith("## Income Tax Audit Manual")
        or lines[0].startswith("### Compliance Programs Branch")
    ):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    lines = [
        line
        for line in lines
        if not re.match(r"^### \**Chapter \d+\.\d+\b", line)
    ]
    return "\n".join(lines).strip()


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge CRA Income Tax Audit Manual chapters from Canada.ca into Markdown."
    )
    parser.add_argument("--toc-url", default=DEFAULT_TOC_URL, help="Canada.ca table-of-contents URL.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Markdown output path. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument("--timeout", type=int, default=30, help="Per-request timeout in seconds.")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between chapter requests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    markdown = build_markdown(args.toc_url, args.timeout, args.delay)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output} ({markdown.count(chr(10)):,} lines).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
