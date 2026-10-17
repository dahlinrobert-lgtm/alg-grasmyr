#!/usr/bin/env python3
"""Create loss-minimizing CSV copies and a manifest from an Älgdata XLSX export.

This utility intentionally does not assign semantic meaning to fields. Each
worksheet is copied row-by-row, including leading title/header rows, so a
real export can be examined before implementing a source-specific normalizer.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "sheet"


def value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Downloaded .xlsx or .xlsm export")
    parser.add_argument("--out", type=Path, default=Path("data/processed"),
                        help="Output directory (default: data/processed)")
    args = parser.parse_args()
    source = args.file.resolve()
    if not source.exists() or not source.is_file():
        parser.error(f"File does not exist: {source}")
    if source.suffix.lower() not in {".xlsx", ".xlsm"}:
        parser.error("Only .xlsx and .xlsm are supported. Export legacy .xls as .xlsx.")

    output_dir = args.out.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # data_only=True reads displayed/cached values rather than formula strings.
    workbook = load_workbook(source, read_only=True, data_only=True)
    manifest: dict[str, Any] = {
        "source_file": source.name,
        "source_path": str(source),
        "sha256": sha256_file(source),
        "format": source.suffix.lower(),
        "created_utc": datetime.now().astimezone().isoformat(),
        "conversion_note": (
            "Worksheet values are copied row-by-row; no statistical field mapping "
            "or filtering is applied. CSV is a convenience copy, not the source of record."
        ),
        "sheets": [],
    }

    source_stem = safe_name(source.stem)
    used_output_names: set[str] = set()
    for sheet_index, sheet in enumerate(workbook.worksheets, start=1):
        base = f"{source_stem}__{sheet_index:02d}_{safe_name(sheet.title)}.csv"
        filename = base
        suffix = 2
        while filename.lower() in used_output_names:
            filename = f"{source_stem}__{sheet_index:02d}_{safe_name(sheet.title)}_{suffix}.csv"
            suffix += 1
        used_output_names.add(filename.lower())
        output_path = output_dir / filename
        row_count = 0
        max_columns = 0
        with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            for row in sheet.iter_rows(values_only=True):
                values = [value_to_text(value) for value in row]
                # Keep row positions, but trim blank cells only from the end.
                while values and values[-1] == "":
                    values.pop()
                if not values:
                    writer.writerow([])
                    row_count += 1
                    continue
                writer.writerow(values)
                max_columns = max(max_columns, len(values))
                row_count += 1
        manifest["sheets"].append({
            "sheet_name": sheet.title,
            "output_csv": filename,
            "rows_written": row_count,
            "max_columns_written": max_columns,
            "csv_delimiter": ";",
            "encoding": "utf-8-sig",
        })

    manifest_path = output_dir / f"{source_stem}__manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(manifest['sheets'])} worksheet(s) from {source.name}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
