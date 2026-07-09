# Corpus Manifests

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
