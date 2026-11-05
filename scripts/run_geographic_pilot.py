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


def select_candidates(
    catalog_path: Path,
    counties: list[str],
    min_end_year: int = 0,
    areas_per_county: int = 5,
) -> tuple[list[dict], list[str], list[dict]]:
    """Select a bounded current-boundary sample, spread across AFOs first."""
    if areas_per_county < 1:
        raise ValueError("areas_per_county must be at least 1")
    with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    selected: list[dict] = []
    missing: list[str] = []
    collisions: list[dict] = []
    used_ids: dict[str, str] = {}

    for county in counties:
        candidates = [
            row for row in rows
            if row.get("county") == county
            and row.get("boundary_mode") == "current"
            and row.get("area_portal_id")
            and row.get("area_portal_id") not in EXCLUDED_AREA_IDS
            and year_number(row.get("to_year", "")) >= min_end_year
            and row.get("afo_name")
        ]
        candidates.sort(key=lambda r: (
            -year_number(r.get("to_year", "")),
            r.get("afo_name", "").casefold(),
            r.get("area_name", "").casefold(),
            r.get("area_portal_id", ""),
        ))

        # Deduplicate repeated catalogue observations for the same portal ID.
        by_id: dict[str, dict] = {}
        for candidate in candidates:
            by_id.setdefault(candidate["area_portal_id"], candidate)

        # Round-robin across AFOs: first choose one area per AFO, then a
        # second area per AFO, etc. This avoids a sample dominated by one AFO.
        by_afo: dict[str, list[dict]] = {}
        for candidate in by_id.values():
            by_afo.setdefault(candidate["afo_name"], []).append(candidate)
        afo_names = sorted(by_afo, key=str.casefold)
        county_selected: list[dict] = []
        for round_index in range(max((len(v) for v in by_afo.values()), default=0)):
            for afo_name in afo_names:
                options = by_afo[afo_name]
                if round_index >= len(options):
                    continue
                candidate = options[round_index]
                area_id = candidate["area_portal_id"]
                if area_id in used_ids:
                    collisions.append({
                        "area_id": area_id,
                        "county": county,
                        "already_assigned_county": used_ids[area_id],
                        "afo_name": candidate.get("afo_name", ""),
                    })
                    continue
                used_ids[area_id] = county
                county_selected.append(candidate)
                if len(county_selected) >= areas_per_county:
                    break
            if len(county_selected) >= areas_per_county:
                break

        if not county_selected:
            missing.append(county)
        selected.extend(county_selected)

    return selected, missing, collisions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/national_area_catalog/national_area_catalog.csv"))
    parser.add_argument("--out", type=Path, default=Path("out/geographic-pilot"))
    parser.add_argument("--counties", nargs="*", default=DEFAULT_COUNTIES)
    parser.add_argument("--min-end-year", type=int, default=2026, help="Minimum end-season start year; defaults to the 2026/2027 season")
    parser.add_argument("--areas-per-county", type=int, default=5, help="Maximum areas sampled per county, spread across AFOs first")
    parser.add_argument("--report-id", default="4")
    args = parser.parse_args()

    candidates, missing, collisions = select_candidates(args.catalog, args.counties, args.min_end_year, args.areas_per_county)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "selected_candidates.json").write_text(
        json.dumps({"counties_requested": args.counties, "missing_counties": missing,
                    "min_end_year": args.min_end_year, "areas_per_county": args.areas_per_county,
                    "candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    results = []
    for index, candidate in enumerate(candidates, start=1):
        area_id = candidate["area_portal_id"]
        county_slug = re.sub(r"[^a-z0-9]+", "-", candidate["county"].casefold()).strip("-")
        target = args.out / f"{index:02d}-{county_slug}-{area_id}"
        # Use the exact catalogue-supported period; do not force a newer start year.
        start = candidate["from_year"]
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
        portal_success = completed.returncode == 0 and selected.get("area_id") == area_id
        data_rows = int(report.get("data_csv_rows", 0) or 0)
        data_status = report.get("data_status", "unknown")
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
            "data_csv_rows": data_rows,
            "data_status": data_status,
            "portal_selection_success": portal_success,
            "data_available": data_rows > 0,
            "errors": errors,
        })
        print(json.dumps(results[-1], ensure_ascii=False))
    summary = {
        "report_id": args.report_id,
        "pilot_counties": args.counties,
        "min_end_year": args.min_end_year,
        "areas_per_county_target": args.areas_per_county,
        "candidate_count": len(candidates),
        "county_coverage": {
            county: {
                "selected_count": sum(x["county"] == county for x in candidates),
                "afo_count": len({x["afo_name"] for x in candidates if x["county"] == county}),
                "area_ids": [x["area_portal_id"] for x in candidates if x["county"] == county],
            }
            for county in args.counties
        },
        "missing_counties": missing,
        "identity_collisions": collisions,
        "portal_selection_success_count": sum(x["portal_selection_success"] for x in results),
        "data_available_count": sum(x["data_available"] for x in results),
        "no_data_count": sum(x["data_status"] == "no_rendered_rows" for x in results),
        "failure_count": sum(not x["portal_selection_success"] for x in results),
        "data_row_count": sum(x["data_csv_rows"] for x in results),
        "nonempty_report_count": sum(x["data_status"] == "data_rows" for x in results),
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
    print(json.dumps({k: summary[k] for k in ("candidate_count", "missing_counties", "identity_collisions",
                                                  "portal_selection_success_count", "data_available_count",
                                                  "no_data_count", "failure_count")}, ensure_ascii=False))
    # Empty current-season statistics are a valid observation, not a failed portal run.
    return 0 if summary["portal_selection_success_count"] == len(candidates) and candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
