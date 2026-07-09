#!/usr/bin/env python3
"""Convert one Canada.ca HTML page into a single Markdown document."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from merge_cra_income_tax_audit_manual import (
    extract_main_markdown,
    fetch,
    find_first,
    normalize_space,
    parse_html,
    text_content,
)


def page_title(html: str) -> str:
    root = parse_html(html)
    h1 = find_first(root, "h1")
    if h1 is not None:
        title = normalize_space(text_content(h1))
        if title:
            return title
    title = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if title:
        return normalize_space(re.sub(r"\s+-\s+Canada\.ca$", "", title.group(1)))
    return "Canada.ca page"


def build_markdown(url: str, html: str) -> str:
    title = page_title(html)
    body, modified = extract_main_markdown(html, url)
    lines = [
        f"# {title}",
        "",
        f"Source: {url}",
        f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
    ]
    if modified:
        lines.append(f"Date modified: {modified}")
    if body:
        lines.extend(["", body])
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Source Canada.ca page URL.")
    parser.add_argument("--input-html", type=Path, help="Optional cached HTML file to convert.")
    parser.add_argument("--output", type=Path, required=True, help="Markdown output path.")
    parser.add_argument("--timeout", type=int, default=30, help="Per-request timeout in seconds.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.input_html:
        html = args.input_html.read_text(encoding="utf-8", errors="replace")
    else:
        html = fetch(args.url, args.timeout)
    markdown = build_markdown(args.url, html)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output} ({markdown.count(chr(10)):,} lines).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
