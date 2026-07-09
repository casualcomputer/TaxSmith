#!/usr/bin/env python3
"""Build the user-facing corpus and export layouts from scraped CRA Markdown."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = ROOT / "corpus"
EXPORTS_ROOT = ROOT / "exports"
GENERATOR_MARKER = ".generated-by-build-corpus-layout"
TOKEN_ESTIMATOR = "ceil_character_count_div_4"


@dataclass(frozen=True)
class SourceRule:
    source: Path
    destination: Path
    corpus: str
    source_family: str
    source_url: str
    document_type: str
    audience: str = ""


SOURCE_RULES = [
    SourceRule(
        source=ROOT / "docs/cra/forms-publications/rag-publications",
        destination=CORPUS_ROOT / "cra/forms-publications",
        corpus="cra/forms-publications",
        source_family="cra_forms_publications",
        source_url="https://www.canada.ca/en/revenue-agency/services/forms-publications/publications.html",
        document_type="publication",
    ),
    SourceRule(
        source=ROOT / "docs/cra/income-tax/rag-publications",
        destination=CORPUS_ROOT / "cra/tax/technical-information/income-tax/current-publications",
        corpus="cra/tax/technical-information/income-tax",
        source_family="cra_income_tax_current_publications",
        source_url="https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/current-publications.html",
        document_type="technical_publication",
    ),
    SourceRule(
        source=ROOT / "docs/cases/tcc",
        destination=CORPUS_ROOT / "cases/tcc",
        corpus="cases/tcc",
        source_family="case_law_tcc",
        source_url="https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do",
        document_type="case_law",
    ),
    SourceRule(
        source=ROOT / "docs/cases/fca",
        destination=CORPUS_ROOT / "cases/fca",
        corpus="cases/fca",
        source_family="case_law_fca",
        source_url="https://decisions.fca-caf.gc.ca/fca-caf/decisions/en/nav_date.do",
        document_type="case_law",
    ),
    SourceRule(
        source=ROOT / "docs/cases/scc",
        destination=CORPUS_ROOT / "cases/scc",
        corpus="cases/scc",
        source_family="case_law_scc",
        source_url="https://decisions.scc-csc.ca/scc-csc/scc-csc/en/nav_date.do",
        document_type="case_law",
    ),
    SourceRule(
        source=ROOT / "docs/cases/fc",
        destination=CORPUS_ROOT / "cases/fc",
        corpus="cases/fc",
        source_family="case_law_fc",
        source_url="https://decisions.fct-cf.gc.ca/fc-cf/decisions/en/nav_date.do",
        document_type="case_law",
    ),
]

MANUALS = [
    (
        ROOT / "data/cra_income_tax_audit_manual.md",
        CORPUS_ROOT
        / "cra/tax/technical-information/compliance-manuals-policies/income-tax-audit-manual.md",
        "Income Tax Audit Manual",
        "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax-audit-manual-domestic-compliance-programs-branch-dcpb-5.html",
    ),
    (
        ROOT / "data/cra_large_business_audit_manual.md",
        CORPUS_ROOT
        / "cra/tax/technical-information/compliance-manuals-policies/large-business-audit-manual.md",
        "Large Business Audit Manual",
        "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/compliance-manuals-policies/large-business-audit-manual-international-large-business-investigations-branch-ilbib.html",
    ),
]

MULTIMEDIA_SOURCES = [
    (
        ROOT / "docs/cra/multimedia/businesses-video-transcripts",
        CORPUS_ROOT / "cra/multimedia/businesses-video-gallery",
        "businesses-video-gallery",
        "cra_business_video_gallery",
        "https://www.canada.ca/en/revenue-agency/news/cra-multimedia-library/businesses-video-gallery.html",
        "businesses",
    ),
    (
        ROOT / "docs/cra/multimedia/individuals-video-transcripts",
        CORPUS_ROOT / "cra/multimedia/individuals-video-gallery",
        "individuals-video-gallery",
        "cra_individuals_video_gallery",
        "https://www.canada.ca/en/revenue-agency/news/cra-multimedia-library/individuals-video-gallery.html",
        "individuals",
    ),
    (
        ROOT / "docs/cra/multimedia/charities-video-transcripts",
        CORPUS_ROOT / "cra/multimedia/charities-video-gallery",
        "charities-video-gallery",
        "cra_charities_video_gallery",
        "https://www.canada.ca/en/revenue-agency/news/cra-multimedia-library/charities-video-gallery.html",
        "charities",
    ),
]


def reset_generated_dir(path: Path) -> None:
    if path.exists():
        marker = path / GENERATOR_MARKER
        if not marker.exists():
            raise SystemExit(
                f"Refusing to overwrite {path}; missing {GENERATOR_MARKER} marker."
            )
        shutil.rmtree(path)
    path.mkdir(parents=True)
    (path / GENERATOR_MARKER).write_text(
        "Generated by scripts/build_corpus_layout.py. Do not edit generated copies in place.\n",
        encoding="utf-8",
    )


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
        value = value.strip().strip('"').strip("'")
        metadata[key.strip()] = value
    return metadata


def strip_front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 5 :].lstrip()


def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def stable_id(corpus_path: Path, used_ids: set[str]) -> str:
    base = slugify(corpus_path.with_suffix("").as_posix())
    if len(base) > 180:
        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
        base = f"{base[:169].rstrip('-')}-{digest}"
    candidate = base
    counter = 2
    while candidate in used_ids:
        candidate = f"{base}-{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate


def infer_archived(corpus_path: Path, title: str) -> bool:
    haystack = f"{corpus_path.as_posix()} {title}".lower()
    return "archived" in haystack or "/archived-" in haystack


def estimate_token_count(text: str) -> int:
    """Estimate model tokens for planning when no tokenizer dependency is installed."""
    if not text:
        return 0
    return (len(text) + 3) // 4


def document_size_metadata(text: str) -> dict[str, object]:
    return {
        "bytes": len(text.encode("utf-8")),
        "character_count": len(text),
        "line_count": len(text.splitlines()),
        "word_count": len(re.findall(r"\S+", text)),
        "estimated_token_count": estimate_token_count(text),
        "token_estimator": TOKEN_ESTIMATOR,
    }


def copy_markdown(
    source_path: Path,
    destination_path: Path,
    *,
    corpus: str,
    source_family: str,
    source_url: str,
    document_type: str,
    audience: str = "",
) -> dict[str, object]:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    text = source_path.read_text(encoding="utf-8")
    destination_path.write_text(text, encoding="utf-8")

    metadata = parse_front_matter(text)
    title = metadata.get("title") or first_heading(text) or destination_path.stem
    corpus_path = destination_path.relative_to(ROOT)
    optional_metadata_fields = [
        "authority_type",
        "case_scope",
        "cases_cited_count",
        "cases_citing_count",
        "citation",
        "citation2",
        "court",
        "court_key",
        "court_database",
        "data_source",
        "data_source_dataset",
        "data_source_last_updated",
        "data_source_url",
        "decision_date",
        "downloaded_at",
        "file_numbers",
        "inferred_file_numbers",
        "inferred_judges",
        "inferred_metadata_method",
        "inferred_subjects",
        "item_id",
        "judges",
        "markdown_conversion",
        "neutral_citation",
        "pdf_path",
        "pdf_sha256",
        "pdf_url",
        "raw_format",
        "raw_row_index",
        "raw_source_path",
        "raw_text_field",
        "raw_url_field",
        "scraped_timestamp",
        "source_html_sha256",
        "subjects",
        "tax_relevance",
        "text_sha256",
        "upstream_license",
    ]

    document = {
        "title": title,
        "source": metadata.get("source") or source_url,
        "video_source": metadata.get("video_source", ""),
        "last_modified": metadata.get("last_modified", ""),
        "corpus_path": corpus_path.as_posix(),
        "source_path": source_path.relative_to(ROOT).as_posix(),
        "corpus": corpus,
        "source_family": source_family,
        "source_url": source_url,
        "document_type": document_type,
        "audience": audience,
        "format": "markdown",
        "language": metadata.get("language", "en"),
        "archived": infer_archived(corpus_path, title),
        **document_size_metadata(text),
    }
    for field in optional_metadata_fields:
        if field in metadata:
            document[field] = metadata[field]
    return document


def copy_tree(rule: SourceRule) -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    if not rule.source.exists():
        return documents
    for source_path in sorted(rule.source.rglob("*.md")):
        if source_path.name.lower() == "readme.md":
            continue
        destination_path = rule.destination / source_path.relative_to(rule.source)
        documents.append(
            copy_markdown(
                source_path,
                destination_path,
                corpus=rule.corpus,
                source_family=rule.source_family,
                source_url=rule.source_url,
                document_type=rule.document_type,
                audience=rule.audience,
            )
        )
    return documents


def copy_multimedia() -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    for source_root, destination_root, gallery_slug, source_family, source_url, audience in MULTIMEDIA_SOURCES:
        for source_path in sorted(source_root.rglob("*.md")):
            rel_path = source_path.relative_to(source_root)
            parts = rel_path.parts
            if parts and parts[0] == gallery_slug:
                rel_path = Path(*parts[1:]) if len(parts) > 1 else Path(source_path.name)
            destination_path = destination_root / rel_path
            documents.append(
                copy_markdown(
                    source_path,
                    destination_path,
                    corpus="cra/multimedia",
                    source_family=source_family,
                    source_url=source_url,
                    document_type="video_transcript",
                    audience=audience,
                )
            )
    return documents


def copy_manuals() -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    source_url = "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/compliance-manuals-policies.html"
    for source_path, destination_path, _title, page_url in MANUALS:
        documents.append(
            copy_markdown(
                source_path,
                destination_path,
                corpus="cra/tax/technical-information/compliance-manuals-policies",
                source_family="cra_compliance_manuals_policies",
                source_url=source_url,
                document_type="manual",
            )
        )
        documents[-1]["source"] = page_url
    return documents


def add_ids(documents: list[dict[str, object]]) -> None:
    used_ids: set[str] = set()
    for doc in sorted(documents, key=lambda item: str(item["corpus_path"])):
        doc["id"] = stable_id(Path(str(doc["corpus_path"])), used_ids)


def write_manifests(documents: list[dict[str, object]]) -> None:
    manifests_dir = CORPUS_ROOT / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(documents, key=lambda item: str(item["corpus_path"]))
    jsonl_path = manifests_dir / "documents.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for doc in ordered:
            handle.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")

    csv_path = manifests_dir / "documents.csv"
    fieldnames = [
        "id",
        "title",
        "source",
        "last_modified",
        "corpus_path",
        "source_path",
        "corpus",
        "source_family",
        "document_type",
        "audience",
        "archived",
        "bytes",
        "character_count",
        "line_count",
        "word_count",
        "estimated_token_count",
        "token_estimator",
        "video_source",
        "language",
        "authority_type",
        "case_scope",
        "data_source",
        "citation",
        "citation2",
        "neutral_citation",
        "decision_date",
        "court",
        "court_key",
        "court_database",
        "subjects",
        "inferred_subjects",
        "tax_relevance",
        "file_numbers",
        "inferred_file_numbers",
        "judges",
        "inferred_judges",
        "inferred_metadata_method",
        "item_id",
        "raw_format",
        "raw_source_path",
        "raw_row_index",
        "raw_text_field",
        "raw_url_field",
        "markdown_conversion",
        "scraped_timestamp",
        "cases_cited_count",
        "cases_citing_count",
        "pdf_url",
        "pdf_path",
        "pdf_sha256",
        "source_html_sha256",
        "text_sha256",
        "data_source_dataset",
        "data_source_url",
        "data_source_last_updated",
        "upstream_license",
        "downloaded_at",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for doc in ordered:
            writer.writerow({field: doc.get(field, "") for field in fieldnames})

    sources: dict[tuple[str, str, str], dict[str, object]] = {}
    for doc in ordered:
        key = (
            str(doc["source_family"]),
            str(doc["corpus"]),
            str(doc["source_url"]),
        )
        source = sources.setdefault(
            key,
            {
                "source_family": key[0],
                "corpus": key[1],
                "source_url": key[2],
                "document_count": 0,
                "archived_count": 0,
                "bytes": 0,
                "character_count": 0,
                "line_count": 0,
                "word_count": 0,
                "estimated_token_count": 0,
                "token_estimator": TOKEN_ESTIMATOR,
            },
        )
        source["document_count"] = int(source["document_count"]) + 1
        source["archived_count"] = int(source["archived_count"]) + int(bool(doc["archived"]))
        source["bytes"] = int(source["bytes"]) + int(doc["bytes"])
        source["character_count"] = int(source["character_count"]) + int(doc["character_count"])
        source["line_count"] = int(source["line_count"]) + int(doc["line_count"])
        source["word_count"] = int(source["word_count"]) + int(doc["word_count"])
        source["estimated_token_count"] = int(source["estimated_token_count"]) + int(
            doc["estimated_token_count"]
        )

    with (manifests_dir / "sources.jsonl").open("w", encoding="utf-8") as handle:
        for source in sorted(sources.values(), key=lambda item: str(item["source_family"])):
            handle.write(json.dumps(source, ensure_ascii=False, sort_keys=True) + "\n")

    (manifests_dir / "README.md").write_text(
        """# Corpus Manifests

`documents.jsonl` and `documents.csv` describe every Markdown document in `corpus/`.

Use `documents.jsonl` when your ingestion code can attach metadata per document.
Use `documents.csv` for spreadsheet QA, filtering, and upload checklists.
Use `sources.jsonl` for source-family counts and high-level coverage checks.

Size metadata includes bytes, characters, lines, words, and estimated token
counts. `estimated_token_count` uses `ceil(character_count / 4)` as a planning
estimate, not an exact model tokenizer count.

Case-law rows may include raw-source provenance such as `raw_format`,
`raw_source_path`, `raw_row_index`, and `raw_text_field`. A2AJ-derived Tax Court
Markdown uses these fields to point back to the canonical parquet row. Any
`inferred_*` fields are opt-in conversion metadata and should not be treated as
source-provided court metadata.
""",
        encoding="utf-8",
    )


def write_exports(documents: list[dict[str, object]]) -> None:
    flat_md = EXPORTS_ROOT / "flat-md"
    flat_txt = EXPORTS_ROOT / "flat-txt"
    flat_md.mkdir(parents=True, exist_ok=True)
    flat_txt.mkdir(parents=True, exist_ok=True)

    full_jsonl = EXPORTS_ROOT / "documents.jsonl"
    with full_jsonl.open("w", encoding="utf-8") as jsonl_handle:
        for doc in sorted(documents, key=lambda item: str(item["id"])):
            source_text = (ROOT / str(doc["corpus_path"])).read_text(encoding="utf-8")
            flat_name = f"{doc['id']}.md"
            md_target = flat_md / flat_name
            md_target.write_text(source_text, encoding="utf-8")

            txt_target = flat_txt / f"{doc['id']}.txt"
            body = strip_front_matter(source_text)
            txt_target.write_text(
                "\n".join(
                    [
                        f"Title: {doc['title']}",
                        f"Source: {doc['source']}",
                        f"Corpus path: {doc['corpus_path']}",
                        f"Document type: {doc['document_type']}",
                        f"Last modified: {doc['last_modified']}",
                        "",
                        body,
                    ]
                ),
                encoding="utf-8",
            )

            json_doc = dict(doc)
            json_doc["text"] = source_text
            jsonl_handle.write(json.dumps(json_doc, ensure_ascii=False, sort_keys=True) + "\n")

    shutil.copy2(CORPUS_ROOT / "manifests/documents.csv", EXPORTS_ROOT / "documents.csv")

    (EXPORTS_ROOT / "README.md").write_text(
        """# Corpus Exports

These files are generated from `corpus/` for tools that do not handle nested folders well.

- `flat-md/`: one Markdown file per document, with stable path-derived filenames.
- `flat-txt/`: one plain-text-compatible file per document, preserving title and source headers.
- `documents.jsonl`: one JSON object per document with metadata plus full Markdown text.
- `documents.csv`: metadata-only inventory for review, filtering, and upload tracking.

Prefer `corpus/` when your RAG tool supports recursive folder ingestion.
Use `flat-md/` or `flat-txt/` when a web UI drops folder structure.
Use `documents.jsonl` for API ingestion or custom loaders.

Metadata includes bytes, characters, lines, words, and estimated token counts.
`estimated_token_count` uses `ceil(character_count / 4)` as a planning estimate,
not an exact model tokenizer count.
""",
        encoding="utf-8",
    )


def write_corpus_readme(documents: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for doc in documents:
        counts[str(doc["corpus"])] = counts.get(str(doc["corpus"]), 0) + 1

    lines = [
        "# Corpus",
        "",
        "This is the canonical, user-facing raw corpus. Files are converted to Markdown and arranged by source domain, not by scraper implementation.",
        "",
        "The older `docs/` and `data/` folders are scrape outputs and staging material. For RAG ingestion, start here.",
        "",
        "## Layout",
        "",
        "```text",
        "corpus/",
        "  cases/",
        "    fca/",
        "    fc/",
        "    scc/",
        "    tcc/",
        "  cra/",
        "    forms-publications/",
        "    tax/",
        "      technical-information/",
        "        income-tax/",
        "          current-publications/",
        "        compliance-manuals-policies/",
        "    multimedia/",
        "  manifests/",
        "```",
        "",
        "## Counts",
        "",
        "| Corpus | Documents |",
        "| --- | ---: |",
    ]
    for corpus, count in sorted(counts.items()):
        lines.append(f"| `{corpus}` | {count:,} |")
    lines.extend(
        [
            "",
            "## Manifests",
            "",
            "- `corpus/manifests/documents.jsonl` is the primary machine-readable manifest.",
            "- `corpus/manifests/documents.csv` is the same inventory for spreadsheet review.",
            "- `corpus/manifests/sources.jsonl` summarizes source-family coverage.",
            "",
            "Each manifest row keeps `corpus_path`, `source_path`, `source`, `last_modified`, `source_family`, `document_type`, and `archived` status where inferable.",
            "",
            "Each manifest row also includes `bytes`, `character_count`, `line_count`, `word_count`, `estimated_token_count`, and `token_estimator`. The token estimate uses `ceil(character_count / 4)` for context-window planning and is not an exact model tokenizer count.",
            "",
            "Case-law rows may include raw-source provenance fields such as `raw_format`, `raw_source_path`, `raw_row_index`, and `raw_text_field`. Treat `inferred_*` fields, when present, as conversion hints rather than source-provided court metadata.",
            "",
            "For distribution analysis and dataset gap assessment, see `docs/CORPUS_ANALYSIS.md`.",
        ]
    )
    (CORPUS_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    reset_generated_dir(CORPUS_ROOT)
    reset_generated_dir(EXPORTS_ROOT)

    documents: list[dict[str, object]] = []
    for rule in SOURCE_RULES:
        documents.extend(copy_tree(rule))
    documents.extend(copy_multimedia())
    documents.extend(copy_manuals())

    add_ids(documents)
    write_manifests(documents)
    write_exports(documents)
    write_corpus_readme(documents)

    print(f"Built {len(documents):,} corpus documents")
    print(f"Wrote {CORPUS_ROOT.relative_to(ROOT)} and {EXPORTS_ROOT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
