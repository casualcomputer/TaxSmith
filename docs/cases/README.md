# Case-Law Corpus Staging

Court decisions are staged here before `scripts/build_corpus_layout.py` copies
them into `corpus/cases/`.

Validation and comparison files live under `docs/cases/validation/` and are not
copied into `corpus/`. Keep them separate from production uploads unless you are
building a QA dataset.

## Court Sources

| Folder | Court | Default scope | Source |
| --- | --- | --- | --- |
| `tcc/` | Tax Court of Canada | A2AJ-derived upload layer | https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do |
| `fca/` | Federal Court of Appeal | Tax-relevant decisions | https://decisions.fca-caf.gc.ca/fca-caf/decisions/en/nav_date.do |
| `scc/` | Supreme Court of Canada | Tax-relevant decisions | https://decisions.scc-csc.ca/scc-csc/scc-csc/en/nav_date.do |
| `fc/` | Federal Court | Tax-relevant judicial review and related decisions | https://decisions.fct-cf.gc.ca/fc-cf/decisions/en/nav_date.do |
| `validation/tcc-official-decisia/` | Tax Court of Canada | Official-page-derived validation samples | https://decision.tcc-cci.gc.ca/tcc-cci/decisions/en/nav_date.do |

The generic harvester is `scripts/court_decisions_to_markdown.py`. It prefers
HTML decision text and can mirror PDFs with `--pdf`.

```bash
python3 scripts/court_decisions_to_markdown.py --court tcc --delay 5
python3 scripts/court_decisions_to_markdown.py --court fca --scope tax --delay 5
python3 scripts/court_decisions_to_markdown.py --court scc --scope tax --delay 5
python3 scripts/court_decisions_to_markdown.py --court fc --scope tax --delay 5
```

Use `--all-courts` for the default Taxsmith harvest plan: all TCC decisions,
plus tax-relevant FCA, SCC, and FC decisions. Use `--scope all` only when you
intentionally want to mirror a whole non-TCC court database.

Lexum/Decisia may require human validation during bulk access. The harvester
stops on validation or rate limiting and can be resumed later.

For TCC, the direct official harvester now writes to
`docs/cases/validation/tcc-official-decisia/` by default. This avoids mixing
official-page-derived validation samples into the A2AJ-derived upload corpus.

For bulk Tax Court coverage, keep the A2AJ raw pull as the source of truth:

- `data/a2aj_case_law/TCC/train.parquet`: canonical A2AJ parquet pull
- `data/a2aj_case_law/TCC/raw.jsonl`: field-preserving JSONL export
- `data/a2aj_case_law/TCC/schema.json`: column schema, counts, and provenance
- `docs/cases/tcc/`: derived Markdown compatibility layer for upload/RAG
- `docs/cases/validation/tcc-official-decisia/`: official-page-derived validation samples, not copied into `corpus/`

`scripts/a2aj_case_law_parquet_to_raw_jsonl.py` refreshes the raw JSONL view.
`scripts/a2aj_tcc_parquet_to_markdown.py --force` regenerates the Markdown
layer. A2AJ text is an unofficial reproduction; preserve the upstream license
note and the official source URL.
