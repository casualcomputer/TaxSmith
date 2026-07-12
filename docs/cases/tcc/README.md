# Tax Court of Canada Decisions

Tax Court of Canada decision corpus staged from the A2AJ Canadian Case Law bulk
parquet (`a2aj/canadian-case-law`, TCC split).

Direct official Lexum/Decisia crawl outputs are kept separately under
`docs/cases/validation/tcc-official-decisia/` for source QA and are not copied
into the production upload corpus.

This folder is not an official Tax Court of Canada publication and is not an
authoritative legal record. Files here are unofficial A2AJ reproductions. Users
should verify the case against the official TCC/Lexum/Decisia page.

- Current Markdown decisions: 15,704
- Unique TCC item IDs: 8,083
- Languages: English and French, one Markdown file per available language version
- PDF mirror enabled: no
- A2AJ conversion manifest: `data/a2aj_case_law/TCC/manifest.jsonl`
- A2AJ raw parquet: `data/a2aj_case_law/TCC/train.parquet`
- A2AJ raw JSONL: `data/a2aj_case_law/TCC/raw.jsonl`
- A2AJ schema manifest: `data/a2aj_case_law/TCC/schema.json`
- Official validation samples: `docs/cases/validation/tcc-official-decisia/`
- Source index: https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do

For A2AJ-derived decisions, the raw parquet is canonical for this repo's A2AJ
pipeline. It contains structured A2AJ columns and plain-text
`unofficial_text_en/fr` fields, not raw official HTML. `raw.jsonl` preserves
those parquet column names for tools that prefer JSONL. The Markdown files are a
compatibility layer for browsing, recursive Markdown loaders, and flat exports.

A2AJ-derived Markdown includes citation, decision date, language, official
source URL, row-level raw-source metadata, and source provenance. It does not
infer subjects, docket/file numbers, or judges by default. Any `inferred_*`
fields should be treated as conversion hints rather than source-provided court
metadata.
