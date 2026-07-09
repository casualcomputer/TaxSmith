# Corpus Exports

These files are generated from `corpus/` for tools that do not handle nested folders well.

- `flat-md/`: one Markdown file per document, with stable path-derived filenames.
- `flat-txt/`: one plain-text-compatible file per document, preserving title and source headers.
- `documents.jsonl`: one JSON object per document with metadata plus full Markdown text.
- `documents.csv`: metadata-only inventory for review, filtering, and upload tracking.

Prefer `corpus/cra/` when your RAG tool supports recursive folder ingestion.
Use `flat-md/` or `flat-txt/` when a web UI drops folder structure.
Use `documents.jsonl` for API ingestion or custom loaders.

## Export Choice

| Export | Provides | Why it is useful | Tradeoff |
| --- | --- | --- | --- |
| `flat-md/` | Markdown body plus source headers in one file per document. | Keeps headings and tables more visible to Markdown-aware chunkers. | Some upload tools reject `.md` or strip Markdown. |
| `flat-txt/` | Plain text body in one file per document. | Highest compatibility with basic RAG products. | Less structural signal than Markdown. |
| `documents.jsonl` | Metadata plus full Markdown text per row. | Best for production ETL, reproducible ingestion, content analysis, and metadata-preserving chunking. | Requires a script or API ingestion loop. |
| `documents.csv` | Metadata only. | Best for auditing coverage, filtering subsets, and tracking upload status. | No full text. |

## JSONL Field Guide

Important fields in `documents.jsonl`:

- `id`: stable path-derived document ID.
- `title`: document title for display and citation snippets.
- `text`: full converted Markdown text.
- `source`: original Canada.ca URL for answer-level citations.
- `corpus_path`: nested path in `corpus/`.
- `source_family`: source/crawl family for dataset splitting.
- `document_type`: `publication`, `technical_publication`, `manual`, or
  `video_transcript`.
- `archived`: archive flag to expose in retrieval filters and citations.
- `last_modified`: source-page modified date captured during conversion.
- `bytes`: approximate size signal for chunking and batching.

For content analysis, use JSONL when you want to count documents by family,
compare archived versus current material, sample long documents, score source
authority, or trace generated answers back to the exact Canada.ca source.
