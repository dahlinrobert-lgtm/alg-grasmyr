#!/usr/bin/env python3
"""Run a bounded national Älgdata preflight: one current area per AFO.

This is a read-only technical probe. Outputs are workflow artifacts only and
must not be copied into the production or daily snapshot history.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.run_geographic_pilot import EXCLUDED_AREA_IDS, year_number


def load_catalog(path: Path) -> tuple[list[dict], dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    metadata_path = path.with_suffix(".json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    return rows, metadata


def select_national_candidates(
    rows: list[dict], min_end_year: int = 2026, areas_per_afo: int = 1
) -> tuple[list[dict], dict]:
    if areas_per_afo < 1:
        raise ValueError("areas_per_afo must be at least 1")

    grouped: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    excluded_only: list[dict] = []
    for row in rows:
        if row.get("boundary_mode") != "current":
            continue
        if year_number(row.get("to_year", "")) < min_end_year:
            continue
        area_id = str(row.get("area_portal_id", "")).strip()
        county = row.get("county", "").strip()
        afo = row.get("afo_name", "").strip()
        if not area_id or not county or not afo:
            continue
        if area_id in EXCLUDED_AREA_IDS:
            excluded_only.append({"county": county, "afo_name": afo, "area_id": area_id})
            continue
        grouped[(county, afo)].setdefault(area_id, row)

    selected: list[dict] = []
    coverage = []
    for (county, afo), by_id in sorted(grouped.items(), key=lambda item: (item[0][0].casefold(), item[0][1].casefold())):
        candidates = sorted(
            by_id.values(),
            key=lambda r: (r.get("area_name", "").casefold(), r.get("area_portal_id", "")),
        )
        chosen = candidates[:areas_per_afo]
        selected.extend(chosen)
        coverage.append({
            "county": county,
            "afo_name": afo,
            "catalogue_area_count": len(by_id),
            "selected_count": len(chosen),
            "selected_area_ids": [str(x["area_portal_id"]) for x in chosen],
        })

    counties = sorted({x["county"] for x in coverage}, key=str.casefold)
    summary = {
        "county_count": len(counties),
        "counties": counties,
        "afo_count": len(coverage),
        "afo_coverage": coverage,
        "excluded_area_observations": excluded_only,
        "candidate_count": len(selected),
    }
    return selected, summary


def run_preflight(
    candidates: list[dict], output_dir: Path, report_id: str = "4"
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, candidate in enumerate(candidates, start=1):
        area_id = str(candidate["area_portal_id"])
        county_slug = re.sub(r"[^a-z0-9]+", "-", candidate["county"].casefold()).strip("-")
        target = output_dir / f"{index:04d}-{county_slug}-{area_id}"
        command = [
            sys.executable, "scripts/download_statistics.py",
            "--out", str(target),
            "--area-id", area_id,
            "--county", candidate["county"],
            "--afo-name", candidate["afo_name"],
            "--from-year", candidate["from_year"],
            "--to-year", candidate["to_year"],
            "--boundary-mode", "current",
            "--report-id", report_id,
        ]
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=180)
            report_path = target / "download-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
            selected = report.get("selected_area") or {}
            portal_success = (
                completed.returncode == 0
                and str(selected.get("area_id", "")) == area_id
                and report.get("hunting_year_from") == candidate["from_year"]
                and report.get("hunting_year_to_selected") == candidate["to_year"]
                and report.get("boundary_mode") == "current"
                and not report.get("errors")
            )
            results.append({
                "county": candidate["county"],
                "afo_name": candidate["afo_name"],
                "area_id": area_id,
                "requested_from_year": candidate["from_year"],
                "requested_to_year": candidate["to_year"],
                "selected_area": selected,
                "selected_to_year": report.get("hunting_year_to_selected"),
                "data_csv_rows": int(report.get("data_csv_rows", 0) or 0),
                "data_status": report.get("data_status", "missing_report"),
                "portal_selection_success": portal_success,
                "data_available": int(report.get("data_csv_rows", 0) or 0) > 0,
                "return_code": completed.returncode,
                "errors": report.get("errors") or ([completed.stderr[-2000:]] if completed.returncode else []),
                "report_present": report_path.is_file(),
            })
        except subprocess.TimeoutExpired:
            results.append({
                "county": candidate["county"], "afo_name": candidate["afo_name"],
                "area_id": area_id, "requested_from_year": candidate["from_year"],
                "requested_to_year": candidate["to_year"], "selected_area": {},
                "selected_to_year": None, "data_csv_rows": 0, "data_status": "timeout",
                "portal_selection_success": False, "data_available": False,
                "return_code": None, "errors": ["download timed out after 180 seconds"],
                "report_present": False,
            })
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/national_area_catalog/national_area_catalog.csv"))
    parser.add_argument("--out", type=Path, default=Path("out/national-preflight"))
    parser.add_argument("--min-end-year", type=int, default=2026)
    parser.add_argument("--areas-per-afo", type=int, default=1)
    parser.add_argument("--max-catalog-age-days", type=int, default=14)
    parser.add_argument("--report-id", default="4")
    args = parser.parse_args()

    rows, catalog_meta = load_catalog(args.catalog)
    captured = catalog_meta.get("catalogued_at_utc")
    if not captured:
        raise SystemExit("National catalogue metadata is missing catalogued_at_utc")
    catalog_time = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    age_days = (datetime.now(timezone.utc) - catalog_time).total_seconds() / 86400
    if age_days < -1 or age_days > args.max_catalog_age_days:
        raise SystemExit(f"National catalogue is stale or future-dated: age_days={age_days:.2f}")

    candidates, coverage = select_national_candidates(rows, args.min_end_year, args.areas_per_afo)
    if not candidates:
        raise SystemExit("No current-boundary national candidates matched the requested season")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "selected_candidates.json").write_text(
        json.dumps({"catalogue_metadata": catalog_meta, "coverage": coverage,
                    "min_end_year": args.min_end_year, "areas_per_afo": args.areas_per_afo,
                    "candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    results = run_preflight(candidates, args.out, args.report_id)
    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_id": args.report_id,
        "min_end_year": args.min_end_year,
        "areas_per_afo": args.areas_per_afo,
        "catalogue_age_days": round(age_days, 2),
        "coverage": coverage,
        "candidate_count": len(candidates),
        "portal_selection_success_count": sum(bool(x["portal_selection_success"]) for x in results),
        "data_available_count": sum(bool(x["data_available"]) for x in results),
        "no_data_count": sum(x["data_status"] in {"no_rendered_table", "no_rendered_rows"} for x in results),
        "failure_count": sum(not x["portal_selection_success"] for x in results),
        "results": results,
        "production_write": False,
        "interpretation": (
            "Technical sample only: one or more areas per current AFO. Empty report tables are not zero harvest. "
            "Results are workflow artifacts and are not written to production snapshots."
        ),
    }
    (args.out / "national_preflight_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in (
        "candidate_count", "portal_selection_success_count", "data_available_count",
        "no_data_count", "failure_count", "production_write"
    )}, ensure_ascii=False, indent=2))
    return 0 if summary["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
