# CRA Corpus

This folder contains scraper outputs and crawl notes for Canada Revenue Agency
public web content. For RAG ingestion, use the normalized `corpus/` layout at
the repository root; this folder is kept for auditability and scraper refreshes.

## Structure

```text
docs/cra/
|-- forms-publications/
|   `-- rag-publications/
|-- income-tax/
|   |-- current-publications/
|   `-- rag-publications/
|-- multimedia/
|   |-- businesses-video-transcripts/
|   |-- charities-video-transcripts/
|   `-- individuals-video-transcripts/
`-- README.md
```

Canonical ingest paths are generated under:

```text
corpus/cra/
exports/
```

## Inventory

| Path | Files | Purpose |
| --- | ---: | --- |
| `forms-publications/rag-publications/` | 1,146 | Broad CRA forms/publications corpus. Useful for retrieval, but still needs wrapper-page normalization QA. |
| `income-tax/current-publications/` | 333 | Full structural mirror from the current income tax publications page. Useful for auditing the crawl. |
| `income-tax/rag-publications/` | 149 | Cleanest current income-tax technical publication set for RAG. |
| `multimedia/businesses-video-transcripts/` | 55 | CRA business video transcript corpus. |
| `multimedia/individuals-video-transcripts/` | 52 | CRA individuals video transcript corpus. |
| `multimedia/charities-video-transcripts/` | 18 | CRA charities video transcript corpus. |

## Technical Information Roadmap

Source landing page:

https://www.canada.ca/en/revenue-agency/services/tax/technical-information.html

The landing page lists these technical-information branches:

- Excise duties technical information
- Excise taxes and other levies technical information
- Fuel charge technical information
- GST/HST technical information
- Underused housing tax technical information
- Luxury tax technical information
- Income tax
- Delegation of powers, duties, and functions
- Provincial income allocation newsletters
- Compliance Manuals and Policies
- Indexation adjustment for personal income tax and benefit amounts

Current coverage:

- Income tax current publications are covered under `income-tax/rag-publications/`.
- Compliance manuals are covered in `data/`:
  - `data/cra_income_tax_audit_manual.md`
  - `data/cra_large_business_audit_manual.md`
- Some GST/HST, excise, notices, info sheets, and circulars are present through
  the broad forms/publications crawl, but they have not yet been audited against
  each technical-information topic page.

Next crawl phases:

1. Create a source map for each technical-information branch and save it as a manifest.
2. Crawl GST/HST technical publication families by type:
   GST memoranda, GST/HST memoranda, technical information bulletins, policy statements, notices, info sheets, and Excise/GST/HST News.
3. Crawl excise duties, excise taxes and other levies, fuel charge, luxury tax, and underused housing tax technical pages.
4. Crawl compliance policies and committees after manuals:
   policies, referral procedures, privilege claims, signature guidance, and review committees.
5. De-duplicate against `forms-publications/rag-publications/` by canonical source URL.
6. Emit a JSONL manifest with `path`, `title`, `source`, `last_modified`,
   `corpus`, and `source_family`.

## Quality Notes

- Prefer `income-tax/rag-publications/` over `income-tax/current-publications/`
  when building a RAG index. The current-publications folder intentionally keeps
  intermediate pages for auditability.
- Treat `forms-publications/rag-publications/` as high-value but not final.
  Some pages are Canada.ca publication landing pages that point to the actual
  online/PDF format. The next QA pass should follow those "Online format" links.
- Every generated Markdown file should retain a source URL. Do not ingest a
  chunk without source metadata.
