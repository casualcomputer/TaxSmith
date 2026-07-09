# TCC Official Decisia Validation Samples

This folder contains local Markdown conversions from official Tax Court of
Canada Lexum/Decisia pages. They are validation samples, not the main TCC upload
corpus.

- Current validation files: 10
- Court: Tax Court of Canada
- Source index: https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do
- Harvester: `scripts/court_decisions_to_markdown.py --court tcc`

The upload-ready TCC corpus is generated separately from the A2AJ Canadian Case
Law parquet pull under `data/a2aj_case_law/TCC/`. These official-page-derived
files are useful for checking source fidelity, metadata extraction, and
deduplication logic. They are not copied into `corpus/` by
`scripts/build_corpus_layout.py`.

Before relying on a case in legal work, verify the text, citation, date, and
procedural status against the official TCC/Lexum/Decisia page.
