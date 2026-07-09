# Case-Law Validation Files

This folder is for source QA, regression tests, and spot-checking unofficial or
third-party case-law data against official court pages.

Files here are intentionally outside the upload-ready `docs/cases/tcc`,
`docs/cases/fca`, `docs/cases/fc`, and `docs/cases/scc` staging folders. Do not
bulk upload this folder into production RAG indexes unless you are deliberately
building a validation or comparison dataset.

Production upload rule:

- Upload `corpus/` or `exports/` for normal retrieval.
- Keep `docs/cases/validation/` separate for QA checks.
- If a validation file and corpus file represent the same court item, dedupe by
  `court_key + item_id + language` or by canonical `source` URL before indexing.
