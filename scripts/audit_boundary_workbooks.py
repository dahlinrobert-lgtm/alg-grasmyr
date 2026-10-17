#!/usr/bin/env python3
"""Audit original Älgdata XLSX exports grouped by boundary mode and season.

The script preserves workbook cell positions and reports sheet dimensions,
non-empty cell samples, and cell-by-cell differences for matching seasons
where both historical and current boundary exports exist. It does not infer
that either boundary mode represents the true area of a VVO.
"""
from __future__ import annotations
import csv, json, re
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out" / "boundary-workbook-audit"
PATTERN = re.compile(r"Avskjutning med mål - Förvaltningsområde - (Historiska|Nuvarande) gränser - .*? - (\d{4})--(\d{4})", re.I)

def val(v):
    if v is None: return ""
    return str(v)

def inspect(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    sheets = []
    for ws in wb.worksheets:
        rows = []
        for row in ws.iter_rows():
            cells = [{"cell": c.coordinate, "value": val(c.value)} for c in row if c.value is not None]
            if cells:
                rows.append(cells)
            if len(rows) >= 35:
                break
        sheets.append({"name": ws.title, "max_row": ws.max_row, "max_column": ws.max_column, "rows": rows})
    wb.close()
    return sheets

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA.glob("*.xlsx"))
    records = []
    by_key = {}
    for p in files:
        m = PATTERN.search(p.name)
        if not m:
            continue
        mode = "historical" if m.group(1).lower().startswith("histor") else "current"
        season = f"{m.group(2)}/{m.group(3)}"
        sheets = inspect(p)
        payload = {"file": p.name, "boundary_mode": mode, "season": season, "size_bytes": p.stat().st_size, "sheets": sheets}
        (OUT / (p.stem.replace("/", "_") + ".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append({"file": p.name, "boundary_mode": mode, "season": season, "size_bytes": p.stat().st_size, "sheet_count": len(sheets), "sheet_names": " | ".join(s["name"] for s in sheets)})
        by_key.setdefault(season, {}).setdefault(mode, []).append((p, sheets))
    with (OUT / "workbook_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f, fieldnames=["file","boundary_mode","season","size_bytes","sheet_count","sheet_names"], delimiter=";")
        w.writeheader(); w.writerows(records)
    comparisons = []
    for season, modes in sorted(by_key.items()):
        if "historical" not in modes or "current" not in modes:
            comparisons.append({"season":season,"status":"missing one boundary mode","historical_files":len(modes.get("historical",[])),"current_files":len(modes.get("current",[])),"cell_differences":""})
            continue
        for old_path, old_sheets in modes["historical"]:
            for new_path, new_sheets in modes["current"]:
                old_map = {(si, r, c): val(cell.value) for si, ws in enumerate(load_workbook(old_path, read_only=True, data_only=True).worksheets) for r, row in enumerate(ws.iter_rows(),1) for c,cell in enumerate(row,1) if cell.value is not None}
                wb2=load_workbook(new_path, read_only=True, data_only=True)
                new_map = {(si, r, c): val(cell.value) for si, ws in enumerate(wb2.worksheets) for r, row in enumerate(ws.iter_rows(),1) for c,cell in enumerate(row,1) if cell.value is not None}
                wb2.close()
                keys=sorted(set(old_map)|set(new_map))
                diffs=[{"sheet_index":k[0],"row":k[1],"column":k[2],"historical":old_map.get(k,""),"current":new_map.get(k,"")} for k in keys if old_map.get(k,"") != new_map.get(k,"")]
                comparisons.append({"season":season,"status":"compared","historical_file":old_path.name,"current_file":new_path.name,"cell_differences":len(diffs),"differences":diffs})
    (OUT/"boundary_comparison.json").write_text(json.dumps(comparisons, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT/"boundary_comparison_summary.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=["season","status","historical_files","current_files","historical_file","current_file","cell_differences"]
        w=csv.DictWriter(f,fieldnames=fields,delimiter=";");w.writeheader()
        for x in comparisons:
            w.writerow({k:x.get(k,"") for k in fields})
    report = ["# Original Excel-export audit: historical vs current boundaries", "", f"Workbook files inspected: **{len(records)}**.", "", "Cell values are compared at matching sheet/row/column positions. This shows export differences, not which boundary is geographically correct.", "", "| Season | Status | Historical files | Current files | Different cells |", "|---|---|---:|---:|---:|"]
    for x in comparisons:
        report.append("| " + " | ".join(str(x.get(k, "")) for k in ["season", "status", "historical_files", "current_files", "cell_differences"]) + " |")
    report.extend(["", "## Cell-level differences", ""])
    found = False
    for x in comparisons:
        diffs = x.get("differences", [])
        if not diffs:
            continue
        found = True
        report.extend(["### " + x["season"], "", "Historical: " + x["historical_file"], "", "Current: " + x["current_file"], "", "| Sheet index | Row | Column | Historical value | Current value |", "|---:|---:|---:|---|---|"])
        for d in diffs[:200]:
            oldv = str(d["historical"]).replace("|", "\\|").replace("\n", " ")
            newv = str(d["current"]).replace("|", "\\|").replace("\n", " ")
            report.append(f"| {d['sheet_index']} | {d['row']} | {d['column']} | {oldv} | {newv} |")
        if len(diffs) > 200:
            report.append(f"| … | … | … | First 200 of {len(diffs)} differences shown | |")
        report.append("")
    if not found:
        report.append("No cell-level differences detected in seasons where both boundary modes were available.")
    report.extend(["", "## Interpretation cautions", "", "- A missing workbook is not evidence of zero area or zero observations.", "- Differences may reflect export layout or boundary-mode semantics; inspect actual values before interpreting them.", "- The 2017/18 and 2018/19 gaps remain gaps unless source workbooks are added.", "- This comparison does not prove VVO membership or that a registration joined an ÄSO.", ""])
    (DATA / "processed" / "boundary-comparison-summary.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Audited {len(records)} original XLSX workbooks; readable report generated.")
if __name__ == "__main__": main()
