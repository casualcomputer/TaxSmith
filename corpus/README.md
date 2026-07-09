# Corpus

This is the canonical, user-facing raw corpus. Files are converted to Markdown and arranged by source domain, not by scraper implementation.

The older `docs/` and `data/` folders are scrape outputs and staging material. For RAG ingestion, start here.

## Layout

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
```

## Counts

| Corpus | Documents |
| --- | ---: |
| `cases/tcc` | 15,704 |
| `cra/forms-publications` | 1,146 |
| `cra/multimedia` | 125 |
| `cra/tax/technical-information/compliance-manuals-policies` | 2 |
| `cra/tax/technical-information/income-tax` | 149 |

## Manifests

- `corpus/manifests/documents.jsonl` is the primary machine-readable manifest.
- `corpus/manifests/documents.csv` is the same inventory for spreadsheet review.
- `corpus/manifests/sources.jsonl` summarizes source-family coverage.

Each manifest row keeps `corpus_path`, `source_path`, `source`, `last_modified`, `source_family`, `document_type`, and `archived` status where inferable.

Each manifest row also includes `bytes`, `character_count`, `line_count`, `word_count`, `estimated_token_count`, and `token_estimator`. The token estimate uses `ceil(character_count / 4)` for context-window planning and is not an exact model tokenizer count.

Case-law rows may include raw-source provenance fields such as `raw_format`, `raw_source_path`, `raw_row_index`, and `raw_text_field`. Treat `inferred_*` fields, when present, as conversion hints rather than source-provided court metadata.

For distribution analysis and dataset gap assessment, see `docs/CORPUS_ANALYSIS.md`.
