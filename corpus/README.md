# Corpus

This is the canonical, user-facing raw corpus. Files are converted to Markdown
and arranged by source domain, not by scraper implementation. For RAG ingestion
or human review, start here when your tool supports recursive folders.

## Layout

```text
corpus/
  cra/
    forms-publications/
    tax/
      technical-information/
        income-tax/
          current-publications/
        compliance-manuals-policies/
    multimedia/
  manifests/
```

## Counts

| Corpus | Documents |
| --- | ---: |
| `cra/forms-publications` | 1,146 |
| `cra/multimedia` | 125 |
| `cra/tax/technical-information/compliance-manuals-policies` | 2 |
| `cra/tax/technical-information/income-tax` | 149 |

## What Each Area Is For

| Area | Main content | Best uses | Lower-value or caution areas |
| --- | --- | --- | --- |
| `cra/forms-publications` | Forms/publications, guides, GST/HST memoranda, notices, payroll tables, and broad CRA publication pages. | Broad-domain retrieval, taxpayer-facing Q&A, payroll/GST/HST lookup, program and form discovery. | Some pages are index/catalogue wrappers or table-heavy references. They can be useful for routing but may not be final answer sources. |
| `cra/tax/technical-information/income-tax/current-publications` | Folios, information circulars, interpretation bulletins, and technical news. | Technical income-tax research, authority ranking, citation-rich answer generation, professional workflows. | Archived bulletins and older technical news need archive-aware filtering and explicit citation warnings. |
| `cra/tax/technical-information/compliance-manuals-policies` | Audit and compliance manuals. | Questions about audit workflow, documentation expectations, risk review, and CRA administrative practice. | Not legislation and not a substitute for current law or policy updates. |
| `cra/multimedia` | Video/webinar transcripts for individuals, businesses, and charities. | Plain-language explanations, examples, outreach content, and user-friendly summaries. | Usually not the best source for technical legal conclusions. |

## Markdown File Shape

The Markdown files are raw converted documents. Most include a YAML-style
metadata block or source header followed by the converted body. Useful signals
for retrieval and analysis include:

- Titles and heading structure.
- Source URL and last-modified date.
- Tables, examples, thresholds, dates, form names, and program names.
- Archive labels or titles that indicate older guidance.
- Transcript text for natural-language examples and user phrasing.

Less useful text can include repeated Canada.ca navigation fragments, generic
service notices, contact blocks, catalogue wrapper content, and duplicated
headers. Keep it available for provenance, but consider downweighting or
filtering it during chunking and reranking.

## Manifests

- `corpus/manifests/documents.jsonl` is the primary machine-readable manifest.
- `corpus/manifests/documents.csv` is the same inventory for spreadsheet review.
- `corpus/manifests/sources.jsonl` summarizes source-family coverage.

Each manifest row keeps `corpus_path`, `source_path`, `source`,
`last_modified`, `source_family`, `document_type`, and `archived` status where
inferable. Use these fields to split datasets, filter archived material, attach
citations, and audit coverage before indexing.
