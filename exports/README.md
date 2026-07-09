# Corpus Exports

These files are generated from `corpus/` for tools that do not handle nested folders well.

- `flat-md/`: one Markdown file per document, with stable path-derived filenames.
- `flat-txt/`: one plain-text-compatible file per document, preserving title and source headers.
- `documents.jsonl`: one JSON object per document with metadata plus full Markdown text.
- `documents.csv`: metadata-only inventory for review, filtering, and upload tracking.

Prefer `corpus/cra/` when your RAG tool supports recursive folder ingestion.
Use `flat-md/` or `flat-txt/` when a web UI drops folder structure.
Use `documents.jsonl` for API ingestion or custom loaders.
