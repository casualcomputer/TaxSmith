#!/usr/bin/env python3
"""Convert A2AJ Tax Court parquet rows into Taxsmith Markdown case files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import html
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = ROOT / "data/a2aj_case_law/TCC/train.parquet"
DEFAULT_OUTPUT_DIR = ROOT / "docs/cases/tcc"
DEFAULT_MANIFEST = ROOT / "data/a2aj_case_law/TCC/manifest.jsonl"
A2AJ_DATASET = "a2aj/canadian-case-law"
A2AJ_DATASET_URL = "https://huggingface.co/datasets/a2aj/canadian-case-law"
A2AJ_LAST_UPDATED = "2026-07-05"


@dataclass(frozen=True)
class ConvertedCase:
    title: str
    citation: str
    citation2: str
    decision_date: str
    language: str
    source: str
    item_id: str
    raw_format: str
    raw_source_path: str
    raw_row_index: int
    raw_text_field: str
    raw_url_field: str
    scraped_timestamp: str
    cases_cited_count: int
    cases_citing_count: int
    upstream_license: str
    text_sha256: str
    markdown_path: str
    conversion_status: str = ""
    inferred_file_numbers: str = ""
    inferred_judges: str = ""
    inferred_subjects: str = ""
    inferred_metadata_method: str = ""


def import_pyarrow_parquet() -> Any:
    try:
        import pyarrow.parquet as pq
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pyarrow is required to read A2AJ parquet files. Install it into a "
            "temporary target, for example:\n"
            "  python3 -m pip install --target /private/tmp/taxsmith_pydeps pyarrow\n"
            "Then rerun with PYTHONPATH=/private/tmp/taxsmith_pydeps."
        ) from exc
    return pq


def yaml_quote(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def slugify(value: str) -> str:
    value = html.unescape(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def iso_date(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value)
    return text[:10] if re.match(r"\d{4}-\d{2}-\d{2}", text) else text


def iso_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def item_id_from_url(url: str) -> str:
    match = re.search(r"/item/(\d+)/index\.do", url or "")
    if match:
        return match.group(1)
    digest = hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:10]
    return digest


def relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def first_following_line(lines: list[str], labels: tuple[str, ...]) -> str:
    normalized_labels = {label.lower() for label in labels}
    for index, line in enumerate(lines):
        if line.strip().lower() in normalized_labels:
            for candidate in lines[index + 1 : index + 4]:
                candidate = candidate.strip()
                if candidate:
                    return candidate
    return ""


def text_metadata(text: str) -> dict[str, str]:
    lines = [line.strip() for line in text.splitlines()]
    return {
        "court_database": first_following_line(lines, ("Court (s) Database", "Court Database")),
        "file_numbers": first_following_line(lines, ("File numbers", "Docket", "Dockets")),
        "judges": first_following_line(lines, ("Judges and Taxing Officers", "Judge", "Before")),
        "subjects": first_following_line(lines, ("Subjects", "Subject")),
    }


def parse_front_matter_fragment(text: str) -> dict[str, str]:
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


def existing_metadata(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as handle:
        fragment = handle.read(16_384)
    return parse_front_matter_fragment(fragment)


def should_write_existing(path: Path, args: argparse.Namespace) -> bool:
    if not path.exists():
        return True
    if not args.force:
        return False
    if args.overwrite_non_a2aj:
        return True
    return existing_metadata(path).get("data_source") == "A2AJ Canadian Case Law"


def output_path(output_dir: Path, case: ConvertedCase, bilingual: bool) -> Path:
    citation_slug = slugify(case.citation)
    title_slug = slugify(case.title)[:80]
    language_suffix = f"-{case.language}" if bilingual else ""
    filename = f"{citation_slug}-{case.item_id}-{title_slug}{language_suffix}.md"
    year = case.decision_date[:4] if re.match(r"\d{4}", case.decision_date) else "unknown-year"
    return output_dir / year / filename


def build_case(
    row: dict[str, Any],
    language: str,
    *,
    row_index: int,
    parquet_path: Path,
    infer_text_metadata: bool,
) -> ConvertedCase | None:
    suffix = f"_{language}"
    text_field = f"unofficial_text{suffix}"
    url_field = f"url{suffix}"
    text = str(row.get(text_field) or "").strip()
    if not text:
        return None

    source = str(row.get(url_field) or "")
    decision_date = iso_date(row.get(f"document_date{suffix}"))
    inferred = text_metadata(text) if infer_text_metadata else {}
    cases_citing = row.get(f"cases_citing{suffix}") or []
    cases_citing_count = len(cases_citing) if cases_citing else int(row.get("citing_cases_count") or 0)
    return ConvertedCase(
        title=str(row.get(f"name{suffix}") or "").strip() or "Untitled Tax Court decision",
        citation=str(row.get(f"citation{suffix}") or "").strip(),
        citation2=str(row.get(f"citation2{suffix}") or "").strip(),
        decision_date=decision_date,
        language=language,
        source=source,
        item_id=item_id_from_url(source),
        raw_format="parquet",
        raw_source_path=relative_to_root(parquet_path),
        raw_row_index=row_index,
        raw_text_field=text_field,
        raw_url_field=url_field,
        scraped_timestamp=iso_datetime(row.get(f"scraped_timestamp{suffix}")),
        cases_cited_count=len(row.get(f"cases_cited{suffix}") or []),
        cases_citing_count=cases_citing_count,
        upstream_license=str(row.get("upstream_license") or ""),
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        markdown_path="",
        inferred_file_numbers=inferred.get("file_numbers", ""),
        inferred_judges=inferred.get("judges", ""),
        inferred_subjects=inferred.get("subjects", ""),
        inferred_metadata_method=(
            "label_following_line_from_unofficial_text" if infer_text_metadata else ""
        ),
    )


def write_markdown(path: Path, case: ConvertedCase, text: str) -> None:
    front_matter = [
        "---",
        f"title: {yaml_quote(case.title)}",
        f"source: {yaml_quote(case.source)}",
        f"last_modified: {yaml_quote(case.decision_date)}",
        'court: "Tax Court of Canada"',
        'court_key: "tcc"',
        'court_database: "Tax Court of Canada Judgments"',
        f"citation: {yaml_quote(case.citation)}",
        f"citation2: {yaml_quote(case.citation2)}",
        f"neutral_citation: {yaml_quote(case.citation)}",
        f"decision_date: {yaml_quote(case.decision_date)}",
        f"language: {yaml_quote(case.language)}",
        f"item_id: {yaml_quote(case.item_id)}",
        'case_scope: "all"',
        'data_source: "A2AJ Canadian Case Law"',
        f"data_source_dataset: {yaml_quote(A2AJ_DATASET)}",
        f"data_source_url: {yaml_quote(A2AJ_DATASET_URL)}",
        f"data_source_last_updated: {yaml_quote(A2AJ_LAST_UPDATED)}",
        f"raw_format: {yaml_quote(case.raw_format)}",
        f"raw_source_path: {yaml_quote(case.raw_source_path)}",
        f"raw_row_index: {case.raw_row_index}",
        f"raw_text_field: {yaml_quote(case.raw_text_field)}",
        f"raw_url_field: {yaml_quote(case.raw_url_field)}",
        'markdown_conversion: "decision text copied from A2AJ unofficial_text field; no structural parsing by default"',
        f"scraped_timestamp: {yaml_quote(case.scraped_timestamp)}",
        f"cases_cited_count: {case.cases_cited_count}",
        f"cases_citing_count: {case.cases_citing_count}",
        f"upstream_license: {yaml_quote(case.upstream_license)}",
        f"text_sha256: {yaml_quote(case.text_sha256)}",
        f"downloaded_at: {yaml_quote(date.today().isoformat())}",
        "authority_type: tcc_case",
        "document_type: case_law",
        "source_family: case_law_tcc",
    ]
    if case.inferred_metadata_method:
        front_matter.extend(
            [
                f"inferred_file_numbers: {yaml_quote(case.inferred_file_numbers)}",
                f"inferred_judges: {yaml_quote(case.inferred_judges)}",
                f"inferred_subjects: {yaml_quote(case.inferred_subjects)}",
                f"inferred_metadata_method: {yaml_quote(case.inferred_metadata_method)}",
            ]
        )
    front_matter.extend(["---", ""])
    body = [
        f"# {case.title}",
        "",
        f"- Citation: {case.citation}",
        f"- Decision date: {case.decision_date}",
        "- Court: Tax Court of Canada",
        f"- Language: {case.language}",
        "- Data source: A2AJ Canadian Case Law",
        f"- Raw source: `{case.raw_source_path}` row {case.raw_row_index}, field `{case.raw_text_field}`",
        "- Conversion note: decision text is copied from the A2AJ source field without structural parsing.",
    ]
    if case.inferred_subjects:
        body.append(f"- Inferred subjects: {case.inferred_subjects}")
    if case.inferred_file_numbers:
        body.append(f"- Inferred file numbers: {case.inferred_file_numbers}")
    if case.inferred_judges:
        body.append(f"- Inferred judges: {case.inferred_judges}")
    body.extend(["", "## Decision Text", "", text.strip(), ""])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front_matter + body), encoding="utf-8")


def write_manifest(path: Path, rows: list[ConvertedCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")


def convert(args: argparse.Namespace) -> int:
    pq = import_pyarrow_parquet()
    parquet = pq.ParquetFile(args.parquet)
    converted: list[ConvertedCase] = []
    written = 0
    skipped_existing = 0
    skipped_protected = 0
    skipped_empty = 0
    row_index = 0

    for batch in parquet.iter_batches(batch_size=args.batch_size):
        for row in batch.to_pylist():
            language_cases = [
                case
                for language in ("en", "fr")
                if (
                    case := build_case(
                        row,
                        language,
                        row_index=row_index,
                        parquet_path=args.parquet,
                        infer_text_metadata=args.infer_text_metadata,
                    )
                )
            ]
            row_index += 1
            if not language_cases:
                skipped_empty += 1
                continue
            bilingual = len(language_cases) > 1
            for case in language_cases:
                text = str(row.get(f"unofficial_text_{case.language}") or "").strip()
                path = output_path(args.output_dir, case, bilingual)
                case = ConvertedCase(**{**asdict(case), "markdown_path": path.relative_to(ROOT).as_posix()})
                if should_write_existing(path, args):
                    write_markdown(path, case, text)
                    written += 1
                    conversion_status = "written"
                elif args.force and path.exists():
                    skipped_protected += 1
                    conversion_status = "protected_existing_non_a2aj"
                else:
                    skipped_existing += 1
                    conversion_status = "existing"
                case = ConvertedCase(
                    **{**asdict(case), "conversion_status": conversion_status}
                )
                converted.append(case)
                if args.limit and len(converted) >= args.limit:
                    write_manifest(args.manifest, converted)
                    print(
                        f"Converted limit reached: {written:,} written, "
                        f"{skipped_existing:,} existing, "
                        f"{skipped_protected:,} protected, {skipped_empty:,} empty."
                    )
                    return 0

    write_manifest(args.manifest, converted)
    print(
        f"Converted {len(converted):,} Tax Court language-version row(s): "
        f"{written:,} written, {skipped_existing:,} existing, "
        f"{skipped_protected:,} protected, {skipped_empty:,} empty."
    )
    print(f"Wrote manifest {args.manifest.relative_to(ROOT)}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing A2AJ-derived Markdown files; official Decisia files stay protected",
    )
    parser.add_argument(
        "--overwrite-non-a2aj",
        action="store_true",
        help="with --force, also overwrite existing non-A2AJ Markdown files",
    )
    parser.add_argument(
        "--infer-text-metadata",
        action="store_true",
        help="add clearly labelled inferred_* metadata extracted from labels in unofficial_text",
    )
    args = parser.parse_args()
    return convert(args)


if __name__ == "__main__":
    raise SystemExit(main())
