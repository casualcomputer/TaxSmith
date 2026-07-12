# Case-Law Data Notes

This folder preserves derived case-law material and source-validation samples.
For normal browsing or RAG ingestion, use `corpus/cases/` instead.

## Available Coverage

| Folder | Court | Current role | Official index |
| --- | --- | --- | --- |
| `tcc/` | Tax Court of Canada | A2AJ-derived Markdown compatibility layer | https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do |
| `validation/tcc-official-decisia/` | Tax Court of Canada | Ten official-page-derived QA samples | https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do |

The repository currently does not contain broad FCA, SCC, or Federal Court
coverage. Those courts remain important dataset gaps, especially for appellate
history, binding precedent, and judicial review of CRA decisions.

## TCC Representations

| Path | Role |
| --- | --- |
| `data/a2aj_case_law/TCC/train.parquet` | Canonical local A2AJ parquet pull |
| `data/a2aj_case_law/TCC/raw.jsonl` | Field-preserving JSONL representation |
| `data/a2aj_case_law/TCC/schema.json` | Column schema, counts, sizes, and provenance |
| `docs/cases/tcc/` | Derived Markdown kept for inspection |
| `corpus/cases/tcc/` | User-facing Markdown for browsing and retrieval |
| `docs/cases/validation/tcc-official-decisia/` | Official-page-derived validation samples |

Do not ingest all representations together. The A2AJ text is an unofficial
reproduction, and official validation samples may overlap with cases in the
upload corpus. Verify any case used for legal work against the official court
page and check subsequent history at higher courts.
