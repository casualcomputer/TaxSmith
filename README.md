# Taxsmith

Authority-aware Canadian tax corpus and retrieval workflow prototype.

Taxsmith is being shaped as an open corpus repo for public Canadian tax source
materials. The goal is simple: keep the raw converted documents easy to inspect,
easy to upload into RAG tools, and easy to reuse in agent or evaluation
workflows without first reverse-engineering Canada.ca.

## What To Use

Start with `corpus/` for normalized Markdown browsing and RAG ingestion. For
A2AJ case-law extraction agents, treat the raw pull in `data/a2aj_case_law/` as
the canonical local A2AJ input: the parquet file is the source of truth for this
repo's A2AJ pipeline, and `raw.jsonl` is a field-preserving JSONL export for
tools that cannot read parquet. This does not make the A2AJ pull an official
Tax Court source.

```text
corpus/
  cases/
    fca/
    fc/
    scc/
    tcc/
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
| `corpus/cases/tcc/` | 15,704 | Tax Court of Canada decisions derived from the A2AJ Canadian Case Law TCC parquet pull. The repository is not the official court source. |
| `corpus/cra/forms-publications/` | 1,146 | CRA forms/publications crawl. Mostly HTML-derived, with PDF fallback where HTML was unavailable. |
| `corpus/cra/tax/technical-information/income-tax/current-publications/` | 149 | Income tax folios, information circulars, interpretation bulletins, and technical news. |
| `corpus/cra/tax/technical-information/compliance-manuals-policies/` | 2 | Income Tax Audit Manual and Large Business Audit Manual. |
| `corpus/cra/multimedia/` | 125 | CRA video transcripts from business, individual, and charity galleries. |

Raw case-law pull:

| Path | Role |
| --- | --- |
| `data/a2aj_case_law/TCC/train.parquet` | Canonical local A2AJ TCC parquet pull for this repo's A2AJ pipeline. Contains structured A2AJ columns and plain-text `unofficial_text_en/fr`, not raw official HTML. |
| `data/a2aj_case_law/TCC/raw.jsonl` | Field-preserving JSONL serialization of the parquet rows for agent/ETL code that does not read parquet. |
| `data/a2aj_case_law/TCC/schema.json` | Column schema, row counts, file sizes, and export provenance. |
| `docs/cases/tcc/` and `corpus/cases/tcc/` | Upload-ready Markdown compatibility layer derived from the A2AJ raw pull. |
| `docs/cases/validation/tcc-official-decisia/` | Official-page-derived TCC validation samples kept outside the upload corpus to avoid duplicate retrieval. |

## Tax Court Case-Law Data Limitation

The TCC corpus in this repository is a local research and RAG dataset, not an
official Tax Court of Canada publication and not an authoritative legal record.

The upload-ready TCC corpus comes from the third-party A2AJ Canadian Case Law
dataset: 15,704 language-version Markdown documents are derived from
`data/a2aj_case_law/TCC/train.parquet`. A2AJ provides plain-text
`unofficial_text_en/fr` fields and upstream license notes. The parquet does not
contain raw official Decisia HTML, and the derived Markdown should be treated as
an unofficial reproduction.

The repo also preserves 10 direct TCC Decisia page conversions from a small live
crawl under `docs/cases/validation/tcc-official-decisia/`. Those records include
official-page metadata such as an HTML hash where captured, and they are useful
as validation samples or an official-source-derived comparison set. They are not
copied into `corpus/` or `exports/`, because mixing them with A2AJ-derived files
can create duplicate retrieval for the same court item. Users should verify
citations, text, dates, and procedural status against the official
TCC/Lexum/Decisia page before relying on a case.

## RAG Usage

Recommended starting points:

- Folder-native loaders: point them at `corpus/` recursively.
- Web upload UIs that flatten or dislike folders: use `exports/flat-md/` or `exports/flat-txt/`.
- API ingestion or custom loaders: use `exports/documents.jsonl` for full text plus metadata, or `corpus/manifests/documents.jsonl` for metadata only.
- Do not assume a RAG product can ingest this repository as one `.zip`. Use ZIP
  only when the target product explicitly documents archive unpacking for
  knowledge ingestion.
- Do not upload `docs/cases/validation/` into a production retrieval index
  unless you are deliberately building a QA/comparison dataset.

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
| RAGFlow | High for batched files/API, not ZIP | `exports/flat-md/` or scripted uploads from `corpus/` | Confirmed nested folder objects and multi-file upload APIs. Do not assume one ZIP or one local folder upload. Create folders/upload files in batches, link/convert files to datasets, then attach manifest metadata. |
| Dify | High for API-per-document, limited UI upload | `exports/documents.jsonl` | Confirmed default UI upload limit of 5 files and 15 MB per file; create-by-file accepts one file per request. For the full corpus, loop over JSONL rows and use create-by-text or one file request per document. |
| AnythingLLM | Medium from checked docs | `exports/flat-txt/` first | Confirmed high-level document ingestion and examples like PDF/TXT/DOCX. ZIP and Markdown support were not verified here, so use flat TXT unless your installed version documents more. |
| LlamaIndex | High for local loaders | `corpus/` | Confirmed local recursive Markdown loading. Join with `corpus/manifests/documents.jsonl` when you want source metadata on every document. |
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
- `cases-tax`: upload-ready TCC decisions plus tax-relevant FCA, SCC, and Federal Court decisions.
- `cases-validation`: optional QA/comparison dataset from `docs/cases/validation/`; keep it separate from production retrieval unless deduped and tagged.

## Repository Structure

```text
.
|-- corpus/                 # Canonical raw Markdown corpus and manifests
|-- exports/                # Flat and JSONL ingestion-friendly exports
|-- data/                   # Original manual conversions used as staging inputs
|-- docs/
|   |-- RAG_USAGE.md
|   |-- cases/              # Court decision staging outputs and validation samples
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

For the A2AJ Tax Court pull, keep the raw export and Markdown compatibility
layer separate:

```bash
python3 scripts/a2aj_case_law_parquet_to_raw_jsonl.py
python3 scripts/a2aj_tcc_parquet_to_markdown.py --force
python3 scripts/build_corpus_layout.py
```

The Markdown converter does not infer docket numbers, judges, or subjects by
default. Use `--infer-text-metadata` only when you deliberately want clearly
labelled `inferred_*` metadata from the text labels.

The builder creates:

- `corpus/**/*.md`
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
