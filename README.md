# Taxsmith

Authority-aware Canadian tax corpus and retrieval workflow prototype.

Taxsmith is being shaped as an open corpus repo for public Canadian tax source
materials. The goal is simple: keep the raw converted documents easy to inspect,
easy to upload into RAG tools, and easy to reuse in agent or evaluation
workflows without first reverse-engineering Canada.ca.

## What To Use

Start with `corpus/`. The older `docs/` and `data/` folders are scrape outputs
and staging material; `corpus/` is the normalized raw data layout.

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
|-- data/                   # Original manual conversions used as staging inputs
|-- docs/
|   |-- RAG_USAGE.md
|   `-- cra/                # Scrape outputs and crawl notes
|-- scripts/                # Scrapers and corpus/export builder
|-- src/taxsmith/           # Retrieval/workflow prototype
|-- tests/
`-- README.md
```

## Refreshing The Corpus

After rerunning any scraper, regenerate the user-facing layout:

```bash
python3 scripts/build_corpus_layout.py
```

The builder creates:

- `corpus/cra/**/*.md`
- `corpus/manifests/documents.jsonl`
- `corpus/manifests/documents.csv`
- `exports/flat-md/*.md`
- `exports/flat-txt/*.txt`
- `exports/documents.jsonl`

It refuses to overwrite an existing `corpus/` or `exports/` directory unless
that directory has the generator marker, so accidental hand-edited corpus data is
not silently replaced.

## Retrieval Prototype

The core engine is deliberately separated from any agent framework:

- `taxsmith.schemas`: canonical source, citation, query, and retrieval data structures.
- `taxsmith.workflow_contracts`: deterministic practitioner workflows that require specific source checks.
- `taxsmith.retrieval`: retrieval interfaces and authority ranking helpers.
- `taxsmith.orchestrator`: orchestration boundary where LangGraph can later coordinate the workflow.

LangGraph is planned for orchestration, not for search itself. The search layer
should remain independently testable.

## Source And Reuse Notes

This repository contains converted copies of public Government of Canada web
content. Keep the original source URL with every derived document and chunk.
Before redistribution, review the Canada.ca terms and conditions:

https://www.canada.ca/en/transparency/terms.html

Canada.ca distinguishes non-commercial reproduction from commercial
redistribution and may exclude third-party copyrighted content.

## Citation And Attribution

If you use this corpus, manifests, exports, scraper output, or derived chunks in
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

Suggested BibTeX, replacing `<REPO_URL>` with the canonical published URL:

```bibtex
@misc{taxsmith_cra_corpus_2026,
  title        = {Taxsmith Canadian Tax Corpus: CRA Public Tax Publications in Markdown},
  author       = {Luan, Henry},
  year         = {2026},
  howpublished = {\url{<REPO_URL>}},
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
