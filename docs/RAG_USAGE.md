# RAG Usage Notes

This repo is meant to work in two modes:

- Human/source mode: browse `corpus/cra/` by the same families used on Canada.ca.
- Ingestion mode: use `exports/` when a RAG tool wants flat files or API-ready JSONL.

## Which Folder To Use

| Situation | Use | Why |
| --- | --- | --- |
| Loader supports recursive directories | `corpus/cra/` | Preserves source structure and readable paths. |
| Upload UI loses nested folders | `exports/flat-md/` | Stable path-derived filenames keep provenance in the filename. |
| Upload UI rejects Markdown | `exports/flat-txt/` | Same content with plain `.txt` extension and source headers. |
| API ingestion or custom ETL | `exports/documents.jsonl` | One row per document with full Markdown text plus metadata. |
| Metadata review/filtering | `corpus/manifests/documents.csv` | Easy to inspect in a spreadsheet before ingestion. |

Do not assume a framework can ingest this repo as a single `.zip`. The checked
docs for the tools below do not prove generic ZIP ingestion for knowledge-base
loading. Use ZIP only when the target deployment explicitly documents archive
unpacking for ingestion.

The key manifest fields are:

- `id`: stable document identifier derived from corpus path.
- `corpus_path`: canonical Markdown path in this repo.
- `source`: original Canada.ca URL.
- `last_modified`: Canada.ca modified date when captured.
- `source_family`: scrape/source family, for example `cra_income_tax_current_publications`.
- `document_type`: `publication`, `technical_publication`, `manual`, or `video_transcript`.
- `archived`: inferred from title/path when Canada.ca labels the page as archived.

## Framework Notes

These notes distinguish production RAG products from library loaders. Product UIs
often have file-count, file-size, supported-extension, and folder/ZIP behavior
that changes by deployment. When in doubt, use `exports/documents.jsonl` and
write a small ingestion loop so every document keeps its manifest metadata.

### Production RAG Products

| Product | Confidence from checked docs | Use first | Do not assume |
| --- | --- | --- | --- |
| RAGFlow | Folder objects and multi-file upload APIs are documented. | `exports/flat-md/`, or scripted API uploads from `corpus/cra/`. | One local folder upload preserving the tree; one ZIP upload unpacked into a corpus. |
| Dify | UI file limits and one-file API upload are documented; create-by-text is documented. | `exports/documents.jsonl` with create-by-text in a loop. | Whole-repo upload, ZIP ingestion, or large UI batch upload. |
| AnythingLLM | Document ingestion, drag-and-drop upload, source citations, and examples like PDF/TXT/DOCX are documented. | `exports/flat-txt/`. | ZIP ingestion or Markdown support unless your installed version documents it. |

### LlamaIndex

LlamaIndex `SimpleDirectoryReader` supports Markdown and local directory loading.
Its docs note that subdirectories require `recursive=True`, which makes
`corpus/cra/` the natural input.

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    input_dir="corpus/cra",
    recursive=True,
    required_exts=[".md"],
).load_data()
```

For stronger metadata, read `corpus/manifests/documents.jsonl` and attach the
manifest row matching each file path before chunking.

Source: [LlamaIndex SimpleDirectoryReader](https://developers.llamaindex.ai/python/framework/module_guides/loading/simpledirectoryreader/)

### RAGFlow

RAGFlow's file management docs say it supports nested folder structures and
individual or bulk file uploads. Its API docs also document dataset document
uploads at `POST /api/v1/datasets/{dataset_id}/documents`, with one or more
local files via multipart form data.

What is confirmed:

- Folder objects can exist in RAGFlow file management.
- Multiple files can be uploaded in one request.
- Files can be linked/converted to datasets.

What is not confirmed from the checked docs:

- Uploading one local directory and preserving its tree automatically.
- Uploading one `.zip` and having RAGFlow unpack it as a knowledge corpus.

Practical path:

1. Create datasets by authority family, for example `CRA income tax technical`,
   `CRA compliance manuals`, `CRA forms/publications`, and `CRA multimedia`.
2. Use `exports/flat-md/` for UI/bulk file upload, or script folder creation and
   file upload from `corpus/cra/` through the API.
3. Set document metadata from `corpus/manifests/documents.jsonl`, especially
   `source`, `corpus_path`, `document_type`, and `archived`.

Important caveat: RAGFlow's file-management search filters only the current
directory, and its docs note there is no bulk/whole-folder download as of
v0.26.4. Keep this repo as the source of truth.

Sources: [RAGFlow file management](https://github.com/infiniflow/ragflow/blob/main/docs/guides/manage_files.md), [RAGFlow HTTP API reference](https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md)

### Dify

Dify's UI documentation says local file import is supported, but the default
self-host limits are small for this corpus: 5 files per upload and 15 MB per
file. Its document upload API creates one document by file at a time and returns
a batch ID for asynchronous indexing. Its text API can create one document from
raw text, which pairs well with iterating `exports/documents.jsonl`.

ZIP ingestion was not confirmed from the checked Dify docs.

Practical path:

1. For a tiny subset, upload files manually from `exports/flat-md/` or
   `exports/flat-txt/`.
2. For the full corpus, iterate `exports/documents.jsonl` and call the Dify
   create-by-text endpoint once per row.
3. Use Dify document metadata for `source`, `corpus_path`, `source_family`,
   `document_type`, and `archived` so retrieval can filter high-authority
   materials.

Sources: [Dify import text data](https://docs.dify.ai/en/self-host/use-dify/knowledge/create-knowledge/import-text-data/readme), [Dify create document by file](https://docs.dify.ai/api-reference/documents/create-document-by-file), [Dify create document by text](https://docs.dify.ai/api-reference/documents/create-document-by-text)

### AnythingLLM

AnythingLLM's official README describes document chat, source citations,
drag-and-drop uploads, and multiple document type support such as PDF, TXT, and
DOCX. The checked docs did not confirm ZIP ingestion, and they did not give a
precise Markdown support guarantee. For this repo, start with `exports/flat-txt/`.
Use `exports/flat-md/` only if your installed version accepts Markdown.

Recommended split:

- One workspace for technical tax materials: income tax publications plus manuals.
- One workspace for broad forms/publications.
- One workspace for multimedia transcripts if you want conversational CRA
  explainer content.

Source: [AnythingLLM README](https://github.com/Mintplex-Labs/anything-llm/blob/master/README.md)

## Dataset Design

Avoid putting every document into one undifferentiated vector index unless the
framework has strong metadata filtering and reranking. A useful default split is:

| Dataset | Include | Typical use |
| --- | --- | --- |
| `cra-income-tax-technical` | `corpus/cra/tax/technical-information/income-tax/` | Folios, ICs, bulletins, technical news. |
| `cra-compliance-manuals` | `corpus/cra/tax/technical-information/compliance-manuals-policies/` | Audit procedure and compliance workflow questions. |
| `cra-forms-publications` | `corpus/cra/forms-publications/` | General CRA guides, notices, memoranda, payroll tables. |
| `cra-multimedia-transcripts` | `corpus/cra/multimedia/` | Plain-language videos and webinar transcript retrieval. |

For tax work, set retrieval preferences so manuals and technical publications
rank above video transcripts and general explainer pages when the query is
technical or procedural.

## Chunking Guidance

Good defaults:

- Split Markdown on headings first.
- Attach the heading trail, `source`, `corpus_path`, and `last_modified` to every chunk.
- Keep tables intact where possible; CRA pages often encode thresholds, dates,
  rates, and examples in tables.
- Use smaller chunks for transcripts and long guides.
- Keep `archived=true` chunks searchable, but expose the archived status in
  citations so answers do not treat old guidance as current.
- When displaying final answers, cite the original Canada.ca URL from `source`;
  cite this repository in product/docs/model cards as the corpus conversion and
  packaging source.

Suggested metadata per chunk:

```json
{
  "source": "https://www.canada.ca/...",
  "corpus_path": "corpus/cra/...",
  "title": "Income Tax Folio S1-F1-C1, Medical Expense Tax Credit",
  "heading_path": ["Summary", "Discussion and interpretation"],
  "source_family": "cra_income_tax_current_publications",
  "document_type": "technical_publication",
  "archived": false,
  "last_modified": "2025-08-15"
}
```

## Why Both Nested And Flat Exports Exist

Nested folders are best for source review and recursive loaders. Flat exports
are better for upload interfaces that do not recurse, do not preserve paths, or
only show filenames after ingestion. The manifest bridges the two: every flat
filename maps back to the canonical `corpus_path` and Canada.ca `source`.

The repo should be treated as the source of truth; RAG tools should be treated as
indexes built from it.

## Citation Requirements

If this corpus is used in academic work, benchmark construction, model training,
model evaluation, commercial RAG deployments, internal tools, or public products:

- Cite this repository or its released dataset artifact.
- Preserve the original Canada.ca `source` URL for answer-level citations.
- Keep `corpus_path`, `document_type`, `source_family`, `last_modified`, and
  `archived` metadata through ingestion where possible.
- Mention in model cards, data cards, product docs, or papers that the corpus is
  a converted/packaged copy of public CRA and Canada.ca source materials.
- Do not imply the project is an official CRA or Government of Canada service.

See `CITATION.cff` and the README citation section for a suggested citation.
