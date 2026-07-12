# Data Staging

This folder contains staging inputs and raw pulls that feed the generated
`corpus/` and `exports/` layouts.

## A2AJ Case Law

Tax Court bulk case-law data lives under `data/a2aj_case_law/TCC/`.

| File | Role |
| --- | --- |
| `train.parquet` | Canonical A2AJ Canadian Case Law TCC parquet pull. |
| `raw.jsonl` | Field-preserving JSONL serialization for tools that do not read parquet. |
| `schema.json` | Column schema, row counts, file sizes, and export provenance. |
| `manifest.jsonl` | Taxsmith Markdown conversion manifest. |

The parquet contains structured A2AJ columns and plain-text
`unofficial_text_en/fr`; it is not raw official HTML. The JSONL preserves the
same source fields for systems that do not read parquet. The Markdown files in
`corpus/cases/tcc/` are a derived compatibility representation.

Official-page-derived TCC validation samples are staged under
`docs/cases/validation/tcc-official-decisia/`, not in `data/` and not in the
production upload corpus.

## Merged CRA Manuals

This folder also contains long-form CRA manual documents that are more useful as
merged Markdown files than as deeply nested page mirrors.

For RAG ingestion, use the generated copies under
`corpus/cra/tax/technical-information/compliance-manuals-policies/`. This
folder is the staging source for those generated corpus documents.

| File | Source | Notes |
| --- | --- | --- |
| `cra_income_tax_audit_manual.md` | https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax-audit-manual-domestic-compliance-programs-branch-dcpb-5.html | Multi-page Income Tax Audit Manual merged from chapter links. |
| `cra_large_business_audit_manual.md` | https://www.canada.ca/en/revenue-agency/services/tax/technical-information/compliance-manuals-policies/large-business-audit-manual-international-large-business-investigations-branch-ilbib.html | Single-page Large Business Audit Manual converted to Markdown. |

## Ingestion Notes

- These files are large. Split by headings before embedding.
- Keep the `Source:` line and chapter heading trail on every chunk.
- The manuals include references to internal CRA InfoZone materials that are not
  publicly accessible. Keep those references as caveats, not as retrievable
  source claims.
