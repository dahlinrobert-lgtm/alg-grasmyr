#!/usr/bin/env python3
"""Validate identity, season, CSV structure and summary consistency of a pilot artifact."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def validate_pilot(output_dir: Path, min_end_year: int = 2026) -> list[str]:
    errors: list[str] = []
    summary_path = output_dir / "pilot_summary.json"
    candidates_path = output_dir / "selected_candidates.json"
    if not summary_path.is_file():
        return ["missing pilot_summary.json"]
    if not candidates_path.is_file():
        return ["missing selected_candidates.json"]

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    selected_doc = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates = selected_doc.get("candidates", [])
    results = summary.get("results", [])
    expected_season = f"{min_end_year}/{min_end_year + 1}" if min_end_year > 0 else None

    if summary.get("candidate_count") != len(candidates):
        errors.append("summary candidate_count does not match selected_candidates.json")
    if len(results) != len(candidates):
        errors.append("number of result records does not match candidate count")

    candidate_by_id = {str(x.get("area_portal_id")): x for x in candidates}
    if len(candidate_by_id) != len(candidates):
        errors.append("selected candidate list contains duplicate portal IDs")

    result_ids = [str(x.get("area_id")) for x in results]
    if len(set(result_ids)) != len(result_ids):
        errors.append("pilot results contain duplicate portal IDs")
    if set(result_ids) != set(candidate_by_id):
        errors.append("result portal IDs do not match selected candidate portal IDs")

    checked_csv_rows = 0
    schema: tuple[str, ...] | None = None
    for result in results:
        area_id = str(result.get("area_id", ""))
        candidate = candidate_by_id.get(area_id)
        if not candidate:
            continue
        if result.get("county") != candidate.get("county"):
            errors.append(f"{area_id}: county differs between candidate and result")
        if result.get("afo_name") != candidate.get("afo_name"):
            errors.append(f"{area_id}: AFO differs between candidate and result")
        if result.get("requested_from_year") != candidate.get("from_year"):
            errors.append(f"{area_id}: requested start year differs from catalogue")
        if result.get("requested_to_year") != candidate.get("to_year"):
            errors.append(f"{area_id}: requested end year differs from catalogue")
        if result.get("boundary_mode") != "current":
            errors.append(f"{area_id}: result is not current-boundary mode")
        if expected_season and candidate.get("to_year") != expected_season:
            errors.append(f"{area_id}: candidate end season {candidate.get('to_year')} != {expected_season}")

        report_dir = output_dir / next(
            (p.name for p in output_dir.iterdir()
             if p.is_dir() and p.name.endswith(f"-{area_id}")),
            f"missing-{area_id}",
        )
        report_path = report_dir / "download-report.json"
        if not report_path.is_file():
            errors.append(f"{area_id}: missing download-report.json")
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        selected = report.get("selected_area") or {}
        if str(selected.get("area_id", "")) != area_id:
            errors.append(f"{area_id}: portal-selected ID does not match requested ID")
        if report.get("hunting_year_from") != candidate.get("from_year"):
            errors.append(f"{area_id}: report start season differs from candidate")
        if report.get("hunting_year_to_selected") != candidate.get("to_year"):
            errors.append(f"{area_id}: portal-selected end season differs from candidate")
        if report.get("boundary_mode") != "current":
            errors.append(f"{area_id}: report is not current-boundary mode")

        csv_name = report.get("data_csv")
        csv_path = report_dir / csv_name if csv_name else None
        if not csv_path or not csv_path.is_file():
            if (
                report.get("data_status") in {
                    "no_rendered_table",
                    "no_rendered_rows",
                    "unrecognized_table_structure",
                }
                and result.get("data_status") == report.get("data_status")
                and int(report.get("data_csv_rows", 0) or 0) == 0
                and int(result.get("data_csv_rows", 0) or 0) == 0
            ):
                # Some valid area selections return no rendered table/rows for
                # the current season. A missing CSV is expected only when both
                # the download report and pilot summary explicitly say so.
                continue
            errors.append(f"{area_id}: missing report CSV")
            continue
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            rows = list(reader)
            current_schema = tuple(reader.fieldnames or ())
        if schema is None:
            schema = current_schema
        elif current_schema != schema:
            errors.append(f"{area_id}: CSV column schema differs from other pilot areas")
        if not rows:
            if result.get("data_status") != "no_rendered_rows":
                errors.append(f"{area_id}: empty CSV does not match data_status")
        else:
            if result.get("data_status") != "data_rows":
                errors.append(f"{area_id}: non-empty CSV does not match data_status")
            for row in rows:
                if row.get("registreringsnummer") != str(selected.get("display_label", "")).split(" - ")[0]:
                    errors.append(f"{area_id}: CSV registration number differs from portal-selected area")
                if row.get("slutrapporterat") not in {"Ja", "Nej"}:
                    errors.append(f"{area_id}: invalid slutrapporterat value")
        checked_csv_rows += len(rows)
        if len(rows) != int(report.get("data_csv_rows", -1)):
            errors.append(f"{area_id}: CSV row count differs from download report")
        if len(rows) != int(result.get("data_csv_rows", -1)):
            errors.append(f"{area_id}: CSV row count differs from pilot summary")
        if result.get("portal_selection_success") and report.get("errors"):
            errors.append(f"{area_id}: portal success is true but download report contains errors")

    if checked_csv_rows != int(summary.get("data_row_count", -1)):
        errors.append("summary data_row_count does not match validated CSV rows")
    if summary.get("portal_selection_success_count") != sum(bool(x.get("portal_selection_success")) for x in results):
        errors.append("summary portal_selection_success_count is inconsistent")
    if summary.get("data_available_count") != sum(bool(x.get("data_available")) for x in results):
        errors.append("summary data_available_count is inconsistent")
    if summary.get("failure_count") != sum(not bool(x.get("portal_selection_success")) for x in results):
        errors.append("summary failure_count is inconsistent")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("out/geographic-pilot"))
    parser.add_argument("--min-end-year", type=int, default=2026)
    args = parser.parse_args()
    errors = validate_pilot(args.directory, args.min_end_year)
    print(json.dumps({"valid": not errors, "error_count": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
