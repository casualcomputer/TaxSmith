# Taxsmith

An authority-aware Canadian tax corpus for research, retrieval, and risk-analysis
experiments.

This repository is primarily a **dataset**. You do not need to run code to use
it.

## Start Here

Choose one representation based on how you plan to use the material:

| Need | Use | What it contains |
| --- | --- | --- |
| Browse documents or load folders recursively | `corpus/` | Canonical Markdown organized by source family |
| Upload files to a tool that flattens folders | `exports/flat-md/` or `exports/flat-txt/` | The same documents with path-safe filenames |
| Build a custom ingestion pipeline | `exports/documents.jsonl` | One document per row with text and metadata |
| Review coverage, sizes, and token estimates | `corpus/manifests/documents.csv` | Spreadsheet-friendly document inventory |
| Inspect original dataset representations and provenance | `data/` | Raw or source-preserving inputs, including TCC parquet/JSONL |

Most users should start with `corpus/`. Do not upload `corpus/`, `exports/`, and
`data/` together; they contain overlapping representations of the same material.

## What Is Included

| Corpus | Documents | Role |
| --- | ---: | --- |
| Tax Court of Canada cases | 15,704 | Unofficial A2AJ-derived language-version decisions |
| CRA forms and publications | 1,146 | Filing guidance, forms, guides, notices, and payroll material |
| CRA income tax technical publications | 149 | Folios, information circulars, technical news, and archived bulletins |
| CRA multimedia transcripts | 125 | Plain-language webinars and video transcripts |
| CRA compliance manuals | 2 | Income Tax Audit Manual and Large Business Audit Manual |

Detailed distributions, long-document outliers, token estimates, strengths, and
dataset gaps are documented in [docs/CORPUS_ANALYSIS.md](docs/CORPUS_ANALYSIS.md).

## Folder Map

```text
corpus/                         canonical user-facing Markdown
  cases/tcc/                    A2AJ-derived TCC decisions
  cra/                          CRA publications, technical material, and transcripts
  manifests/                    document inventories and metadata
exports/                        ingestion-friendly copies of the corpus
data/                           raw/source-preserving dataset representations
docs/                           dataset notes, provenance, and validation material
```

The same source document may appear in more than one representation. Pick one
user-facing representation for ingestion and retain the manifests for metadata.

## Metadata And Context Size

The corpus manifest includes `source`, `last_modified`, `corpus_path`,
`source_family`, `document_type`, `archived`, file size, character count, word
count, and `estimated_token_count`.

Token estimates use `ceil(character_count / 4)`. They are useful for studying
the distribution and planning chunk sizes, but they are not exact counts for a
specific tokenizer. The largest file is the merged Income Tax Audit Manual at
about 522,000 estimated tokens; this is a source document size, not a suggested
model context window. Large documents should be split by headings before model
input or embedding.

See [docs/RAG_USAGE.md](docs/RAG_USAGE.md) for ingestion choices and metadata
handling.

## Tax Court Data Limitation

The TCC corpus is a research dataset, not an official Tax Court of Canada
publication or an authoritative legal record.

The 15,704 upload-ready Markdown files are derived from the third-party A2AJ
Canadian Case Law TCC dataset. The source-preserving local copies are:

| Path | Role |
| --- | --- |
| `data/a2aj_case_law/TCC/train.parquet` | Canonical local A2AJ pull with structured fields and `unofficial_text_en/fr` |
| `data/a2aj_case_law/TCC/raw.jsonl` | Field-preserving JSONL representation of the parquet rows |
| `data/a2aj_case_law/TCC/schema.json` | Schema, counts, sizes, and provenance |
| `corpus/cases/tcc/` | Markdown compatibility layer for browsing and retrieval |

The parquet contains plain-text unofficial reproductions, not raw official
Decisia HTML. Ten direct official-page-derived samples are kept separately in
`docs/cases/validation/tcc-official-decisia/` for source-fidelity checks. They
are excluded from the upload corpus to reduce duplicate retrieval.

Before relying on a case, verify its text, citation, date, and procedural status
against the official TCC/Lexum/Decisia source.

## Authority-Aware Use

Different folders serve different roles. CRA guidance can explain filing,
eligibility, evidence, and audit practice, but it is not binding legislation.
Archived publications should be used as historical context. TCC decisions are
judicial sources, but this repository's copies are unofficial and may have been
appealed or subsequently considered by higher courts.

A production system should retain source authority, date, archived status, and
provenance on every chunk. It should also keep official validation records
separate from production retrieval unless records are deliberately deduplicated
and tagged.

## Known Coverage Gaps

This is enough for a CRA-guidance-centered prototype, but not for a complete
Canadian tax authority system. Important additions still include consolidated
federal statutes and regulations, treaties, Department of Finance proposals,
current form/line extraction, tax-relevant FCA/SCC/FC decisions, provincial and
territorial sources, and broader official-source case validation.

## Source And Attribution

This repository contains converted copies of public Government of Canada web
content and third-party case-law dataset material. Preserve original source URLs
and review the applicable source terms before redistribution. Do not present
Taxsmith as an official Canada Revenue Agency or Tax Court service.

If you use this corpus in research, benchmarks, model development, evaluation,
or a product, cite this repository and retain document-level provenance. See
[CITATION.cff](CITATION.cff) for citation metadata.
