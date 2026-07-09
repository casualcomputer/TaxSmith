# Taxsmith

Authority-aware Canadian tax corpus for RAG, agents, and content analysis.

Taxsmith is being shaped as an open corpus repo for public Canadian tax source
materials. The goal is simple: keep the raw converted documents easy to inspect,
easy to upload into RAG tools, and easy to reuse in agent or evaluation
workflows without first reverse-engineering Canada.ca.

## What To Use

Start with `corpus/`. It is the normalized raw Markdown layout, arranged by
public source family so humans and recursive loaders can browse it naturally.
Use `exports/` when a RAG product or ingestion script needs flat files, plain
text, JSONL, or CSV.

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
exports/
  flat-md/
  flat-txt/
  documents.jsonl
  documents.csv
```

Current generated corpus:

| Corpus | Markdown docs | Notes |
| --- | ---: | --- |
| `corpus/cra/forms-publications/` | 1,146 | CRA forms/publications crawl. Mostly HTML-derived, with PDF fallback where HTML was unavailable. |
| `corpus/cra/tax/technical-information/income-tax/current-publications/` | 149 | Income tax folios, information circulars, interpretation bulletins, and technical news. |
| `corpus/cra/tax/technical-information/compliance-manuals-policies/` | 2 | Income Tax Audit Manual and Large Business Audit Manual. |
| `corpus/cra/multimedia/` | 125 | CRA video transcripts from business, individual, and charity galleries. |

## Folder Guide

| Folder or file | What it contains | Why it matters | Watch-outs |
| --- | --- | --- | --- |
| `corpus/cra/forms-publications/` | General CRA forms/publications pages, guides, notices, memoranda, GST/HST memoranda, payroll tables, and related publication pages. | Broad coverage and good recall for common taxpayer, payroll, GST/HST, benefit, and compliance topics. | Some files are catalogue-like or table-heavy. Treat them as retrieval material, not as a curated legal hierarchy. |
| `corpus/cra/tax/technical-information/income-tax/current-publications/` | Income tax folios, information circulars, interpretation bulletins, and income tax technical news. | Higher-authority technical guidance for income tax interpretation and professional research workflows. | Many interpretation bulletins and technical news items are archived. Keep `archived` visible in citations and filters. |
| `corpus/cra/tax/technical-information/compliance-manuals-policies/` | CRA audit and compliance manuals. | Useful for audit-process, risk, documentation, and procedural questions. | Manuals describe CRA administrative practice; they are not a substitute for the statute, regulations, or current CRA positions. |
| `corpus/cra/multimedia/` | Video and webinar transcripts from CRA business, individual, and charity galleries. | Plain-language explanations, examples, and outreach content that can improve answer accessibility. | Lower authority for technical answers. Prefer it for explainers, not as the final authority on complex tax interpretation. |
| `corpus/manifests/` | Metadata inventories for the canonical Markdown corpus. | Lets you filter by source family, document type, archive status, source URL, and path before ingestion. | Manifest rows are only as complete as the public page metadata captured during conversion. |
| `exports/flat-md/` | One Markdown file per document with path-derived filenames. | Best for upload UIs that accept many files but do not preserve nested folders. | Filenames are long because they preserve provenance. Use the manifest to map them back to source paths. |
| `exports/flat-txt/` | Plain-text versions of the same documents. | Useful when a product rejects Markdown or handles `.txt` more reliably. | Loses some Markdown structure compared with `flat-md/`. |
| `exports/documents.jsonl` | One JSON object per document with metadata and full Markdown text. | Best input for production ingestion scripts, batch ETL, content analysis, and reproducible indexing. | Large enough that some no-code tools will not ingest it directly; stream it row by row. |
| `exports/documents.csv` | Metadata-only inventory. | Spreadsheet-friendly audit, filtering, sampling, and ingestion tracking. | Does not include full document text. |

## What The Files Tell You

Most Markdown files start with front matter and source headers. The manifest
normalizes the same ideas into fields:

- `source`: original Canada.ca page to cite in generated answers.
- `corpus_path`: canonical nested Markdown path inside this repo.
- `source_family`: crawl family such as `cra_income_tax_current_publications`
  or `cra_forms_publications`.
- `document_type`: broad type: `publication`, `technical_publication`,
  `manual`, or `video_transcript`.
- `archived`: inferred archive status. Use this for filtering and warnings.
- `last_modified`: source-page modified date when captured.
- `title`, `language`, `bytes`, and `text`: display, filtering, sizing, and
  ingestion fields.

Useful information in this corpus includes headings, definitions, examples,
rates, administrative procedures, eligibility rules, filing/remittance steps,
CRA explanatory language, source URLs, and archive/current signals. Less useful
information includes navigation residue, page chrome, repeated boilerplate,
catalogue wrapper pages, and generic contact/service text. Those pieces can
still help provenance, but they should usually receive lower retrieval weight
than substantive publication sections.

## Content Analysis Uses

The corpus is useful beyond direct RAG ingestion:

- Coverage analysis: count documents by `source_family`, `document_type`, or
  `archived` to see which tax areas are represented.
- Authority analysis: compare answers retrieved from manuals, technical
  publications, general publications, and transcripts.
- Change monitoring: use `source`, `last_modified`, and stable paths to refresh
  or diff specific public documents over time.
- Chunk-quality evaluation: sample long guides, tables, archived bulletins, and
  transcripts separately because they behave differently in retrieval.
- Domain vocabulary mining: extract recurring headings, defined terms, forms,
  program names, and tax concepts for query expansion or ontology work.
- Citation QA: verify every answer can trace back to Canada.ca through
  `source`, not merely to this converted repository.

For technical tax answering, a useful default ranking is: current technical
publications and manuals first, broad forms/publications next, multimedia
transcripts last unless the user asks for a plain-language explanation.

## RAG Usage

Recommended starting points:

- Folder-native loaders: point them at `corpus/cra/` recursively.
- Web upload UIs that flatten or dislike folders: use `exports/flat-md/` or `exports/flat-txt/`.
- API ingestion or custom loaders: use `exports/documents.jsonl` for full text plus metadata, or `corpus/manifests/documents.jsonl` for metadata only.
- Do not assume a RAG product can ingest this repository as one `.zip`. Use ZIP
  only when the target product explicitly documents archive unpacking for
  knowledge ingestion.

Each document keeps source metadata such as `source`, `last_modified`,
`corpus_path`, `source_family`, `document_type`, and inferred `archived`
status. More framework-specific notes are in [docs/RAG_USAGE.md](docs/RAG_USAGE.md).

## Production RAG Loading

This repo is intended to be loaded into production RAG systems as documents plus
metadata, not as one giant archive. If a framework has file-count, file-size, or
supported-extension limits, prefer scripted ingestion from `exports/documents.jsonl`
or batched flat-file upload from `exports/flat-md/` or `exports/flat-txt/`.

| Product / framework | Confidence | Best repo input | Production loading approach |
| --- | --- | --- | --- |
| RAGFlow | High for batched files/API, not ZIP | `exports/flat-md/` or scripted uploads from `corpus/cra/` | Confirmed nested folder objects and multi-file upload APIs. Do not assume one ZIP or one local folder upload. Create folders/upload files in batches, link/convert files to datasets, then attach manifest metadata. |
| Dify | High for API-per-document, limited UI upload | `exports/documents.jsonl` | Confirmed default UI upload limit of 5 files and 15 MB per file; create-by-file accepts one file per request. For the full corpus, loop over JSONL rows and use create-by-text or one file request per document. |
| AnythingLLM | Medium from checked docs | `exports/flat-txt/` first | Confirmed high-level document ingestion and examples like PDF/TXT/DOCX. ZIP and Markdown support were not verified here, so use flat TXT unless your installed version documents more. |
| LlamaIndex | High for local loaders | `corpus/cra/` | Confirmed local recursive Markdown loading. Join with `corpus/manifests/documents.jsonl` when you want source metadata on every document. |
| LangChain / LangGraph apps | General ETL pattern | `exports/documents.jsonl` | Build `Document` objects from JSONL text and metadata, then chunk by Markdown headings before embedding. Verify your chosen loader/vector store limits separately. |
| Haystack or custom ETL | General ETL pattern | `exports/documents.jsonl` | Treat each row as one source document and preserve manifest metadata through conversion, chunking, indexing, and citation display. Verify converter and document-store limits separately. |

Other production RAG UIs can still use this corpus, but they should not be listed
as directly supported until their current docs confirm file types, file counts,
file sizes, folder behavior, and archive behavior.

Recommended dataset split for production indexes:

- `cra-income-tax-technical`: folios, information circulars, interpretation bulletins, and technical news.
- `cra-compliance-manuals`: audit manuals and compliance policy material.
- `cra-forms-publications`: broad CRA guides, notices, memoranda, forms publications, and payroll tables.
- `cra-multimedia-transcripts`: plain-language video and webinar transcript content.

## Repository Structure

```text
.
|-- corpus/                 # Canonical raw Markdown corpus and manifests
|-- exports/                # Flat and JSONL ingestion-friendly exports
|-- docs/
|   `-- RAG_USAGE.md        # RAG loading, chunking, and citation notes
|-- CITATION.cff            # Machine-readable citation metadata
`-- README.md
```

## Source And Reuse Notes

This repository contains converted copies of public Government of Canada web
content. Keep the original source URL with every derived document and chunk.
Before redistribution, review the Canada.ca terms and conditions:

https://www.canada.ca/en/transparency/terms.html

Canada.ca distinguishes non-commercial reproduction from commercial
redistribution and may exclude third-party copyrighted content.

## Citation And Attribution

If you use this corpus, manifests, exports, or derived chunks in
academic work, benchmarks, model training, model evaluation, internal tools,
commercial RAG systems, or customer-facing products, cite this repository and
preserve the original Canada.ca source URLs in downstream citations.

Minimum attribution:

- Cite this repository or released dataset in papers, model cards, data cards,
  product documentation, and commercial attribution notices.
- Keep `source`, `last_modified`, `corpus_path`, `document_type`, and `archived`
  metadata attached to documents/chunks where your system supports metadata.
- In generated answers, cite the original Canada.ca `source` URL, not only this
  repository.
- Do not present this project as an official Canada Revenue Agency service.

Suggested BibTeX:

```bibtex
@misc{taxsmith_cra_corpus_2026,
  title        = {Taxsmith Canadian Tax Corpus: CRA Public Tax Publications in Markdown},
  author       = {Luan, Henry},
  year         = {2026},
  howpublished = {\url{https://github.com/casualcomputer/TaxSmith}},
  note         = {Converted corpus generated from public Canada Revenue Agency and Canada.ca source materials}
}
```

The machine-readable citation metadata is in `CITATION.cff`. Citation does not
replace your responsibility to review Canada.ca terms, source-page notices, and
any downstream commercial-use requirements.

## Known Gaps

- The broad forms/publications corpus still needs a QA pass to replace
  catalogue wrapper records with their ultimate HTML or PDF publication where
  possible.
- Technical-information topic pages beyond income tax and compliance manuals
  are not fully crawled yet.
- French-language equivalents are out of scope for the current English corpus.
