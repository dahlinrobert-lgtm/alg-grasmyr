#!/usr/bin/env python3
"""Extract raw worksheet rows for target VVO/ÄSO registrations from official Älgdata workbooks.

The output preserves raw cell positions and source headers rather than assuming a stable
column schema across years. It is an audit extract, not yet website-ready statistics.
"""
from __future__ import annotations
import csv, re
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out" / "target-area-workbook-audit"
FILE_RE = re.compile(r"Avskjutning med mål - Förvaltningsområde - (Historiska|Nuvarande) gränser - .*? - (\d{4})--(\d{4})", re.I)
TARGETS = {
    "24-01-02-342-Ä": "Hörneåns ÄSO",
    "24-01-02-017-A": "Gräsmyrs VVO",
    "24-01-02-006-A": "Mullsjö VVO",
    "24-01-02-008-A": "Tallbergslidens VVO",
    "24-01-02-028-A": "Hörnsjö VVO",
    "24-01-02-045-A": "Hummelholms VVO",
    "24-01-02-100-A": "Torrböle VVO",
}
def cell(v):
    return "" if v is None else str(v).strip()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    output = []
    schema = []
    for path in sorted(DATA.glob("*.xlsx")):
        match = FILE_RE.search(path.name)
        if not match:
            continue
        mode = "historical" if match.group(1).lower().startswith("histor") else "current"
        season = f"{match.group(2)}/{match.group(3)}"
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if not rows:
            continue
        # Preserve the raw header rows so schema changes and merged/blank headers remain visible.
        for row_idx, row in enumerate(rows[:3], start=1):
            schema.append({"file": path.name, "season": season, "boundary_mode": mode,
                           "row_number": row_idx, "cells_json": repr([cell(v) for v in row])})
        for row_idx, row in enumerate(rows, start=1):
            values = [cell(v) for v in row]
            joined = " | ".join(values)
            # Registration IDs may be stored as a cell or embedded in a text cell.
            for registration, label in TARGETS.items():
                if registration in joined:
                    output.append({
                        "season": season, "boundary_mode": mode, "registration": registration,
                        "target_label": label, "source_file": path.name, "worksheet": ws.title,
                        "row_number": row_idx, "raw_cells_json": repr(values),
                    })
                    break
    fields = ["season","boundary_mode","registration","target_label","source_file","worksheet","row_number","raw_cells_json"]
    with (OUT / "target_area_raw_rows.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";"); w.writeheader(); w.writerows(output)
    with (OUT / "worksheet_schema_samples.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields2 = ["file","season","boundary_mode","row_number","cells_json"]
        w = csv.DictWriter(f, fieldnames=fields2, delimiter=";"); w.writeheader(); w.writerows(schema)
    seasons = sorted({r["season"] for r in output})
    print(f"workbooks parsed: {len({r['source_file'] for r in output})}")
    print(f"target rows extracted: {len(output)}")
    print(f"seasons with target rows: {', '.join(seasons)}")
    print(f"outputs: {OUT}")
    # Emit a compact, inspectable sample for the 2005/2006 season into the workflow log.
    for row in output:
        if row["season"] == "2005/2006":
            print("SAMPLE_2005_2006 " + row["registration"] + " " + row["boundary_mode"] + " " + row["raw_cells_json"])
    for row in schema:
        if row["season"] == "2005/2006" and row["row_number"] <= 3:
            print("SCHEMA_2005_2006 " + row["boundary_mode"] + " row=" + str(row["row_number"]) + " " + row["cells_json"])
if __name__ == "__main__":
    main()
