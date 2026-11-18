#!/usr/bin/env python3
"""Validate national Älgdata preflight candidate coverage and portal identities."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(directory: Path) -> list[str]:
    errors = []
    candidates_path = directory / "selected_candidates.json"
    summary_path = directory / "national_preflight_summary.json"
    if not candidates_path.is_file() or not summary_path.is_file():
        return ["missing selected_candidates.json or national_preflight_summary.json"]
    selected = json.loads(candidates_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    candidates = selected.get("candidates", [])
    results = summary.get("results", [])
    candidate_ids = [str(x.get("area_portal_id", "")) for x in candidates]
    result_ids = [str(x.get("area_id", "")) for x in results]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate list contains duplicate portal IDs")
    if len(result_ids) != len(set(result_ids)):
        errors.append("result list contains duplicate portal IDs")
    if set(candidate_ids) != set(result_ids):
        errors.append("result IDs do not match candidate IDs")
    if len(candidates) != summary.get("candidate_count"):
        errors.append("candidate_count does not match candidate list")
    if summary.get("production_write") is not False:
        errors.append("preflight must explicitly declare production_write=false")

    by_id = {str(x.get("area_portal_id")): x for x in candidates}
    for result in results:
        area_id = str(result.get("area_id", ""))
        candidate = by_id.get(area_id)
        if not candidate:
            continue
        if result.get("county") != candidate.get("county"):
            errors.append(f"{area_id}: county mismatch")
        if result.get("afo_name") != candidate.get("afo_name"):
            errors.append(f"{area_id}: AFO mismatch")
        if result.get("requested_from_year") != candidate.get("from_year"):
            errors.append(f"{area_id}: requested start season mismatch")
        if result.get("requested_to_year") != candidate.get("to_year"):
            errors.append(f"{area_id}: requested end season mismatch")
        if result.get("portal_selection_success"):
            selected_area = result.get("selected_area") or {}
            if str(selected_area.get("area_id", "")) != area_id:
                errors.append(f"{area_id}: successful portal result has wrong selected ID")
            if result.get("selected_to_year") != candidate.get("to_year"):
                errors.append(f"{area_id}: selected end season mismatch")
            if result.get("errors"):
                errors.append(f"{area_id}: successful result contains errors")
        elif not result.get("errors"):
            errors.append(f"{area_id}: failed result has no diagnostic error")

    success_count = sum(bool(x.get("portal_selection_success")) for x in results)
    failure_count = len(results) - success_count
    if summary.get("portal_selection_success_count") != success_count:
        errors.append("portal_selection_success_count is inconsistent")
    if summary.get("failure_count") != failure_count:
        errors.append("failure_count is inconsistent")
    if summary.get("failure_count") == 0 and not candidates:
        errors.append("empty national candidate set cannot be considered successful")
    expected_data_count = sum(bool(x.get("data_available")) for x in results)
    if summary.get("data_available_count") != expected_data_count:
        errors.append("data_available_count is inconsistent")
    if summary.get("failure_count", 0) > 0:
        errors.append(f"national preflight recorded {summary['failure_count']} failed area probes; inspect diagnostics")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("out/national-preflight"))
    args = parser.parse_args()
    errors = validate(args.directory)
    print(json.dumps({"valid": not errors, "error_count": len(errors), "errors": errors},
                     ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
