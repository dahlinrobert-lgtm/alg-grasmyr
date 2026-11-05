#!/usr/bin/env python3
"""Run a bounded, read-only regional pilot against the public Älgdata selector."""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_COUNTIES = [
    "Norrbottens län",
    "Västerbottens län",
    "Jämtlands län",
    "Dalarnas län",
    "Gävleborgs län",
    "Skåne län",
]
EXCLUDED_AREA_IDS = {"724577", "718148"}  # Keep Hörneån ÄSO and historic Gräsmyr VVO distinct.


def year_number(season: str) -> int:
    match = re.match(r"^(\d{4})/\d{4}$", (season or "").strip())
    return int(match.group(1)) if match else -1


def select_candidates(catalog_path: Path, counties: list[str], min_end_year: int = 2024) -> tuple[list[dict], list[str]]:
    with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    selected, missing = [], []
    for county in counties:
        candidates = [
            row for row in rows
            if row.get("county") == county
            and row.get("boundary_mode") == "current"
            and row.get("area_portal_id")
            and row.get("area_portal_id") not in EXCLUDED_AREA_IDS
            and year_number(row.get("from_year", "")) >= 1990
            and year_number(row.get("to_year", "")) >= min_end_year
            and row.get("afo_name")
        ]
        if not candidates:
            missing.append(county)
            continue
        # Prefer the broadest recent coverage, then stable lexical ordering.
        candidates.sort(key=lambda r: (
            -year_number(r.get("to_year", "")),
            year_number(r.get("from_year", "")),
            r.get("area_name", "").casefold(),
            r.get("area_portal_id", ""),
        ))
        selected.append(candidates[0])
    return selected, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/national_area_catalog/national_area_catalog.csv"))
    parser.add_argument("--out", type=Path, default=Path("out/geographic-pilot"))
    parser.add_argument("--counties", nargs="*", default=DEFAULT_COUNTIES)
    parser.add_argument("--min-end-year", type=int, default=2024)
    parser.add_argument("--report-id", default="4")
    args = parser.parse_args()

    candidates, missing = select_candidates(args.catalog, args.counties, args.min_end_year)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "selected_candidates.json").write_text(
        json.dumps({"counties_requested": args.counties, "missing_counties": missing,
                    "candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    results = []
    for index, candidate in enumerate(candidates, start=1):
        area_id = candidate["area_portal_id"]
        county_slug = re.sub(r"[^a-z0-9]+", "-", candidate["county"].casefold()).strip("-")
        target = args.out / f"{index:02d}-{county_slug}-{area_id}"
        start = candidate["from_year"]
        if year_number(start) < 2020:
            start = "2020/2021"
        command = [
            sys.executable, "scripts/download_statistics.py",
            "--out", str(target),
            "--area-id", area_id,
            "--county", candidate["county"],
            "--afo-name", candidate["afo_name"],
            "--from-year", start,
            "--to-year", candidate["to_year"],
            "--boundary-mode", "current",
            "--report-id", args.report_id,
        ]
        completed = subprocess.run(command, text=True, capture_output=True)
        report_path = target / "download-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        selected = report.get("selected_area") or {}
        errors = report.get("errors") or ([completed.stderr[-2000:]] if completed.returncode else [])
        success = completed.returncode == 0 and bool(report.get("data_csv_rows")) and selected.get("area_id") == area_id
        results.append({
            "county": candidate["county"],
            "afo_name": candidate["afo_name"],
            "area_id": area_id,
            "area_label_catalogue": candidate.get("area_label_raw", ""),
            "boundary_mode": "current",
            "requested_from_year": start,
            "requested_to_year": candidate["to_year"],
            "selected_area": selected,
            "selected_to_year": report.get("hunting_year_to_selected"),
            "data_csv_rows": report.get("data_csv_rows", 0),
            "success": success,
            "errors": errors,
        })
        print(json.dumps(results[-1], ensure_ascii=False))
    summary = {
        "report_id": args.report_id,
        "pilot_counties": args.counties,
        "candidate_count": len(candidates),
        "missing_counties": missing,
        "success_count": sum(x["success"] for x in results),
        "failure_count": sum(not x["success"] for x in results),
        "results": results,
        "interpretation": (
            "A successful run proves that this area could be selected and a report table was returned "
            "for this run. It does not establish a stable geographic identity, source-Excel equivalence, "
            "or sustained daily reliability. No pilot output is committed to production snapshots."
        ),
    }
    (args.out / "pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in ("candidate_count", "missing_counties", "success_count", "failure_count")}, ensure_ascii=False))
    return 0 if summary["success_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
