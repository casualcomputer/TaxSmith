#!/usr/bin/env python3
"""Export A2AJ Canadian Case Law parquet rows to field-preserving raw JSONL."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = ROOT / "data/a2aj_case_law/TCC/train.parquet"
DEFAULT_OUTPUT = ROOT / "data/a2aj_case_law/TCC/raw.jsonl"
DEFAULT_SCHEMA = ROOT / "data/a2aj_case_law/TCC/schema.json"
A2AJ_DATASET = "a2aj/canadian-case-law"
A2AJ_DATASET_URL = "https://huggingface.co/datasets/a2aj/canadian-case-law"
A2AJ_LAST_UPDATED = "2026-07-05"


def import_pyarrow_parquet() -> Any:
    try:
        import pyarrow.parquet as pq
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pyarrow is required to read A2AJ parquet files. Install it into a "
            "temporary target, for example:\n"
            "  python3 -m pip install --target /private/tmp/taxsmith_pydeps pyarrow\n"
            "Then rerun with PYTHONPATH=/private/tmp/taxsmith_pydeps."
        ) from exc
    return pq


def relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def json_ready(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    return value


def write_schema_manifest(
    *,
    schema_path: Path,
    parquet_path: Path,
    output_path: Path,
    parquet: Any,
    exported_rows: int,
    limit: int | None,
) -> None:
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_schema = parquet.schema_arrow
    manifest = {
        "data_source": "A2AJ Canadian Case Law",
        "data_source_dataset": A2AJ_DATASET,
        "data_source_url": A2AJ_DATASET_URL,
        "data_source_last_updated": A2AJ_LAST_UPDATED,
        "source_parquet": relative_to_root(parquet_path),
        "raw_jsonl": relative_to_root(output_path),
        "parquet_size_bytes": parquet_path.stat().st_size,
        "parquet_row_count": parquet.metadata.num_rows,
        "exported_row_count": exported_rows,
        "export_limit": limit,
        "export_generated_at": datetime.now(timezone.utc).isoformat(),
        "raw_jsonl_policy": (
            "Each JSONL record preserves the A2AJ parquet column names exactly. "
            "Datetime/date values are serialized to ISO strings for JSON compatibility."
        ),
        "columns": [
            {"name": field.name, "type": str(field.type)}
            for field in parquet_schema
        ],
    }
    schema_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def export(args: argparse.Namespace) -> int:
    pq = import_pyarrow_parquet()
    parquet = pq.ParquetFile(args.parquet)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    exported_rows = 0
    with args.output.open("w", encoding="utf-8") as handle:
        for batch in parquet.iter_batches(batch_size=args.batch_size):
            for row in batch.to_pylist():
                handle.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")
                exported_rows += 1
                if args.limit and exported_rows >= args.limit:
                    write_schema_manifest(
                        schema_path=args.schema,
                        parquet_path=args.parquet,
                        output_path=args.output,
                        parquet=parquet,
                        exported_rows=exported_rows,
                        limit=args.limit,
                    )
                    print(
                        f"Exported {exported_rows:,} raw A2AJ row(s) to "
                        f"{relative_to_root(args.output)}."
                    )
                    return 0

    write_schema_manifest(
        schema_path=args.schema,
        parquet_path=args.parquet,
        output_path=args.output,
        parquet=parquet,
        exported_rows=exported_rows,
        limit=args.limit,
    )
    print(f"Exported {exported_rows:,} raw A2AJ row(s) to {relative_to_root(args.output)}.")
    print(f"Wrote schema manifest {relative_to_root(args.schema)}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    return export(args)


if __name__ == "__main__":
    raise SystemExit(main())
