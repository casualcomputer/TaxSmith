# Corpus Analysis

This note summarizes the current local corpus distribution and whether it is
enough for Taxsmith's intended authority-aware Canadian tax research and risk
detection workflows.

The numbers below come from `corpus/manifests/documents.jsonl`. Token counts are
planning estimates using `ceil(character_count / 4)`, not exact tokenizer counts.

## Summary

The corpus is strong enough for a CRA-guidance-centered prototype, especially
for:

- filing-position workflows based on CRA guides, forms/publications, and folios
- risk identification based on CRA audit manuals and common-review materials
- evidence and documentation checklists
- form and guide retrieval for T1, T2, T3, payroll, GST/HST, SR&ED, and selected
  other programs

It is not yet enough for a complete authority-aware Canadian tax platform. The
main missing layers are binding law, regulations, treaties, Finance proposal
tracking, provincial tax sources, and richer form/PDF extraction. The Tax Court
layer is now much stronger: the upload-ready corpus includes 15,704 TCC
language-version Markdown documents converted from the A2AJ Canadian Case Law
TCC parquet dataset. Ten direct official Decisia conversions are kept separately
under `docs/cases/validation/tcc-official-decisia/` for source QA and are not
copied into `corpus/`.

For TCC extraction agents, the raw A2AJ pull should be treated as canonical:
`data/a2aj_case_law/TCC/train.parquet` is the local A2AJ source dataset,
`data/a2aj_case_law/TCC/raw.jsonl` is a field-preserving JSONL view, and
`docs/cases/tcc/` plus `corpus/cases/tcc/` are Markdown compatibility layers.
The A2AJ parquet contains structured columns and plain-text
`unofficial_text_en/fr`; it does not contain raw official HTML.

In short:

| Use case | Current readiness | Notes |
| --- | --- | --- |
| CRA guide retrieval | Strong | Broad forms/publications corpus. |
| CRA interpretation retrieval | Good | Current income tax publications and folios are present. |
| Audit-risk workflow design | Good | Income Tax Audit Manual and Large Business Audit Manual are present, but must be split by section. |
| Deterministic return checks | Partial | Needs form/line maps and extracted PDF table/form content. |
| Final legal authority answers | Partial | TCC coverage is now broad, but still needs Justice Laws, regulations, treaties, and tax-relevant FCA/SCC/FC coverage. |
| Proposed-law/currentness tracking | Not enough | Needs Finance budgets, draft legislation, NWMMs, explanatory notes. |
| Provincial tax workflows | Not enough | Needs provincial/territorial source families and at least province-trigger flags. |

## Top-Level Distribution

| Corpus folder | Documents | Archived | Estimated tokens | Min | P50 | P90 | P95 | P99 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `cases/tcc` | 15,704 | 0 | 113,029,456 | 536 | 5,182 | 13,570 | 18,616 | 35,346 | 299,878 |
| `cra/forms-publications` | 1,146 | 404 | 8,005,760 | 56 | 3,110 | 15,480 | 23,815 | 53,150 | 134,199 |
| `cra/tax/technical-information/income-tax` | 149 | 49 | 1,287,050 | 56 | 5,381 | 20,693 | 25,887 | 34,284 | 52,447 |
| `cra/multimedia` | 125 | 0 | 329,877 | 83 | 984 | 6,550 | 7,696 | 12,071 | 12,887 |
| `cra/tax/technical-information/compliance-manuals-policies` | 2 | 0 | 550,047 | 27,428 | 522,619 | 522,619 | 522,619 | 522,619 | 522,619 |

Observations:

- Most of the corpus is CRA forms/publications. That is useful for practitioner
  workflow and filing support, but it should not be treated as binding law.
- The income tax technical folder has a better authority profile than general
  publications, but still contains archived material.
- Multimedia is useful for explanations and common-review context, not for high
  authority conclusions.
- The Tax Court corpus is now the largest source family by both document count
  and tokens. It should be indexed separately from CRA guidance so case-law
  retrieval can use court/citation/date filters.
- Case-law issue-mining should start from the A2AJ parquet or raw JSONL when
  citation networks, bilingual fields, row provenance, or source fidelity matter.
  The Markdown layer is useful for RAG loaders but should not be treated as the
  only representation of the case data.
- Official-page-derived TCC validation files are intentionally outside
  `corpus/` to prevent duplicate retrieval when users bulk upload the corpus.
  Keep `docs/cases/validation/` as a QA/comparison dataset.
- The compliance manual folder has only two documents, but one is very large:
  the merged Income Tax Audit Manual is about 522k estimated tokens. It must be
  split into chapter/section spans before retrieval.

## Folder-Level Distribution

| Folder | Documents | Archived | Estimated tokens | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| `corpus/cases/tcc` | 15,704 | 0 | 113,029,456 | 536 | 299,878 |
| `corpus/cra/forms-publications/publications` | 1,082 | 404 | 7,726,625 | 56 | 134,199 |
| `corpus/cra/forms-publications/payroll` | 57 | 0 | 201,746 | 610 | 27,530 |
| `corpus/cra/multimedia/businesses-video-gallery` | 55 | 0 | 162,445 | 302 | 12,071 |
| `corpus/cra/multimedia/individuals-video-gallery` | 52 | 0 | 103,271 | 83 | 9,552 |
| `corpus/cra/tax/technical-information/income-tax/current-publications/folios` | 51 | 0 | 670,886 | 212 | 34,284 |
| `corpus/cra/tax/technical-information/income-tax/current-publications/information-circulars` | 50 | 1 | 365,575 | 56 | 28,820 |
| `corpus/cra/tax/technical-information/income-tax/current-publications/technical-news` | 47 | 47 | 198,142 | 505 | 25,964 |
| `corpus/cra/multimedia/charities-video-gallery` | 18 | 0 | 64,161 | 91 | 12,887 |
| `corpus/cra/forms-publications/tax-packages-years` | 7 | 0 | 77,389 | 1,444 | 21,301 |
| `corpus/cra/tax/technical-information/compliance-manuals-policies` | 2 | 0 | 550,047 | 27,428 | 522,619 |
| `corpus/cra/tax/technical-information/income-tax/current-publications/interpretation-bulletins` | 1 | 1 | 52,447 | 52,447 | 52,447 |

Observations:

- The forms/publications `publications` folder is broad and noisy. It includes
  high-value GST/HST memoranda and guides, but also old, archived, cancelled, or
  plain-language materials. It needs role classification.
- Current income tax folios are a good base for eligibility and interpretive
  guidance.
- Technical news and interpretation bulletins are mostly or entirely archived in
  this snapshot. They should be retrievable for history, but answers must expose
  the archived status.
- Payroll is well represented as CRA publications, but many table pages link to
  PDFs. If payroll calculations matter, extract the PDFs or rely on official
  calculators/rate tables separately.

## Document Type Distribution

| Document type | Documents | Archived | Estimated tokens | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `case_law` | 15,704 | 0 | 113,029,456 | 5,182 | 18,616 | 299,878 |
| `publication` | 1,146 | 404 | 8,005,760 | 3,110 | 23,815 | 134,199 |
| `technical_publication` | 149 | 49 | 1,287,050 | 5,381 | 25,887 | 52,447 |
| `video_transcript` | 125 | 0 | 329,877 | 984 | 7,696 | 12,887 |
| `manual` | 2 | 0 | 550,047 | 522,619 | 522,619 | 522,619 |

## Long-Document Outliers

| Estimated tokens | Title | Type |
| ---: | --- | --- |
| 522,619 | Income Tax Audit Manual | manual |
| 299,878 | Kang v. M.N.R. | case_law |
| 211,150 | Gill c. M.R.N. | case_law |
| 198,604 | Cameco Corporation c. La Reine | case_law |
| 176,457 | Gill v. M.N.R. | case_law |
| 172,608 | Cameco Corporation v. The Queen | case_law |
| 134,199 | Guide for the Partnership Information Return (T5013 Forms) | publication |
| 121,018 | Exempt U.S. Organizations - Under Article XXI of the Canada - United States Tax Convention | publication |
| 114,846 | ExxonMobil Canada Resources Company v. The King | case_law |
| 113,198 | T3 Trust Guide - 2025 | publication |

Implication:

- Do not set a model context window based on the largest file.
- Use heading-aware chunking and retain `heading_path`, `source`, `document_type`,
  `archived`, and `estimated_token_count` on every chunk.
- Very large manuals and guides should be split into logical source spans before
  embedding or model ingestion.

## Current Dataset Strengths

The existing corpus is enough to build the first risk-detection spine around
CRA-facing workflows:

- credit/deduction/election discovery from CRA forms and publications
- eligibility checklists from folios and guides
- evidence requirements from guides, GST/HST memoranda, audit manuals, and
  common-review transcripts
- form and schedule discovery from T2, T3, T5013, GST/HST, payroll, and SR&ED
  materials
- audit procedure retrieval from the Income Tax Audit Manual and Large Business
  Audit Manual
- common mistake and limited-review patterns from CRA webinars and publications

This is especially useful for the product frame:

```text
tax position
-> eligibility facts
-> required evidence
-> forms and fields
-> reconciliation checks
-> risk indicators
-> audit procedures
```

## Current Dataset Gaps

The corpus is not yet authority complete. The most important missing datasets
are:

| Missing source family | Why it matters | Priority |
| --- | --- | --- |
| Justice Laws statutes | Binding Income Tax Act, Excise Tax Act, UHT Act, luxury tax, CPP/EI law. | Highest |
| Justice Laws regulations | CCA classes, prescribed rates, payroll/source deduction rules, GST/HST regulations. | Highest |
| Treaties and protocols | Non-resident withholding, taxable Canadian property, PE, capital gains, pensions. | High |
| SCC/FCA/FC tax cases | Court hierarchy, binding appellate law, later treatment, and judicial review of CRA administrative decisions. TCC coverage is now broad; appellate and FC layers are still missing. | High |
| Department of Finance proposals | Budgets, draft legislation, explanatory notes, NWMMs, proposed vs enacted status. | High |
| CRA forms as forms | Current forms, schedules, slips, line numbers, PDF fields, annual form versions. | High |
| PDF table extraction | Payroll tables, schedules, detailed rate tables, form attachments. | High for deterministic checks |
| Provincial/territorial sources | Quebec, Alberta corporate tax, QST/PST/RST, provincial credits and payroll taxes. | Medium to high |
| CRA rulings and technical interpretations | Narrow CRA administrative views and transaction-specific reasoning. | Medium |
| Commercial/secondary commentary | Practitioner issue spotting and citators, only if licensed. | Later |

## Case-Law Harvest Plan

Use `scripts/court_decisions_to_markdown.py` for official court decision
ingestion. The intended Taxsmith scope is:

| Court | Folder | Scope | Why |
| --- | --- | --- | --- |
| Tax Court of Canada | `docs/cases/tcc` -> `corpus/cases/tcc` | A2AJ-derived upload layer | Specialized federal tax appeal forum; useful for issues, evidence, pleadings, and common failure mechanisms. |
| Tax Court validation | `docs/cases/validation/tcc-official-decisia` | Official-page-derived QA samples | Source-fidelity checks against official Decisia pages; keep outside production upload indexes unless deduped and tagged. |
| Federal Court of Appeal | `docs/cases/fca` -> `corpus/cases/fca` | Tax-relevant decisions | Binding appellate treatment of TCC decisions and federal tax law. |
| Supreme Court of Canada | `docs/cases/scc` -> `corpus/cases/scc` | Tax-relevant decisions | Highest authority for major interpretive principles and leading tax cases. |
| Federal Court | `docs/cases/fc` -> `corpus/cases/fc` | Tax-relevant judicial review and related matters | Taxpayer relief, CRA administrative decisions, collections, remission, access, mandamus, and procedural fairness. |

The harvester prefers HTML decision text and can mirror PDFs with `--pdf`.
Lexum/Decisia may require human validation during bulk access; when that
happens, the harvester stops and should be resumed later rather than bypassed.

For the A2AJ TCC bulk source, use
`scripts/a2aj_case_law_parquet_to_raw_jsonl.py` to refresh the raw JSONL view
and `scripts/a2aj_tcc_parquet_to_markdown.py --force` to regenerate the derived
Markdown layer. The Markdown converter does not infer docket numbers, judges, or
subjects by default; use `--infer-text-metadata` only for clearly labelled
`inferred_*` metadata.

For official TCC page checks, use `scripts/court_decisions_to_markdown.py
--court tcc`. Its default output is `docs/cases/validation/tcc-official-decisia/`
so official-page conversions do not overlap with the upload-ready A2AJ TCC
corpus.

## Recommendation

You have enough data to build a useful MVP for CRA-informed risk identification,
but not enough to let the system present itself as a full Canadian tax authority
engine.

The next ingestion priorities should be:

1. Add Justice Laws versions of the Income Tax Act, Income Tax Regulations, and
   Excise Tax Act.
2. Add a form/line extraction layer for T2, T1, T3, T5013, GST/HST, T4/T5,
   SR&ED/T661, and major elections/certificates.
3. Split the Income Tax Audit Manual and long CRA guides by heading into
   source spans.
4. Expand case law: all TCC decisions, then tax-relevant FCA and SCC decisions,
   then tax-relevant Federal Court judicial review decisions.
5. Add Finance budgets, draft legislation, NWMMs, and explanatory notes as a
   separate proposed-law corpus.
6. Add province-trigger metadata before adding full provincial corpora. At
   minimum, detect Quebec, Alberta, QST/PST/RST, payroll/health taxes, and
   provincial credits.
7. Add GST/HST legal materials and regulations if ITC/GST/HST risk detection is
   core to the MVP.

## Suggested Dataset Split

Avoid one undifferentiated dataset. A better default split is:

| Dataset | Include | Purpose |
| --- | --- | --- |
| `cra-income-tax-technical-current` | Current folios and current ICs | Eligibility, interpretation, technical CRA position. |
| `cra-income-tax-historical` | Archived technical news, archived ITs, cancelled/replaced docs | Historical context only. |
| `cra-forms-guides` | Forms/publications and guides | Filing workflows, form discovery, practical instructions. |
| `cra-gst-hst-guidance` | GST/HST memoranda, notices, info sheets, guides | ITC and indirect tax risk. |
| `cra-compliance-audit` | Audit manuals and compliance materials | Audit procedures, evidence, risk logic. |
| `cra-multimedia-explainers` | Video transcripts/webinars | Plain-language explanations and common mistakes. |
| `law-federal-tax` | Justice Laws statutes/regulations | Binding law once added. |
| `cases-tax` | Upload-ready TCC cases, then tax-relevant SCC/FCA/FC cases | Judicial authority and evidentiary/risk pattern mining. |
| `cases-validation` | Official-page-derived validation samples | QA, source-fidelity checks, and deduplication tests; keep separate from production retrieval. |
| `finance-proposals` | Budgets, draft legislation, NWMMs, explanatory notes | Proposed-law tracking once added. |

Retrieval should prefer higher-authority datasets for legal conclusions and
prefer audit/forms datasets for risk packets and evidence workflows.
