#!/usr/bin/env python3
"""Compare immutable national ÄFO snapshots at ÄJO-row level.

Missing rows are reported as unconfirmed absences, never as deletion events.
The input snapshots are read-only; only the requested report file is written.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PORTAL_ID_RE = re.compile(r"drillDownToAjoReport\(\s*\d+\s*,\s*['\"]([^'\"]+)['\"]\s*\)")


def row_fields(raw_row: Any) -> dict[str, str]:
    if not isinstance(raw_row, list):
        raise ValueError("ÄJO row must be a list of field cells")
    fields: dict[str, str] = {}
    for cell in raw_row:
        if not isinstance(cell, dict) or not isinstance(cell.get("Name"), str):
            raise ValueError("ÄJO row contains malformed field cell")
        name = cell["Name"]
        if name in fields:
            raise ValueError(f"Duplicate field {name!r} in ÄJO row")
        fields[name] = str(cell.get("Text", "") if cell.get("Text") is not None else "")
    return fields


def stable_ajo_id(fields: dict[str, str]) -> str:
    value = fields.get("AfoName", "")
    match = PORTAL_ID_RE.search(value)
    if not match:
        raise ValueError(f"Missing drillDownToAjoReport ID in AfoName: {value!r}")
    return match.group(1)


def load_snapshot(path: Path, expected_date: str, expected_afo_id: str) -> dict[str, Any]:
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read snapshot {path}: {exc}") from exc
    if snapshot.get("snapshot_date") != expected_date:
        raise ValueError(f"{path}: snapshot_date is not {expected_date}")
    if snapshot.get("afo_id") != expected_afo_id:
        raise ValueError(f"{path}: afo_id does not match directory {expected_afo_id}")
    if snapshot.get("hunting_season") != "2026/2027":
        raise ValueError(f"{path}: unexpected hunting season")
    if snapshot.get("boundary_mode") != "current":
        raise ValueError(f"{path}: boundary_mode is not current")
    rows = snapshot.get("raw_area_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: raw_area_rows missing or empty")
    if snapshot.get("source_row_count") != len(rows):
        raise ValueError(f"{path}: source_row_count does not match raw_area_rows")
    indexed: dict[str, dict[str, str]] = {}
    for index, raw in enumerate(rows):
        fields = row_fields(raw)
        key = stable_ajo_id(fields)
        if key in indexed:
            raise ValueError(f"{path}: duplicate stable ÄJO ID {key}")
        indexed[key] = fields
    return {"metadata": snapshot, "rows": indexed}


def compare_afo(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_rows, new_rows = old["rows"], new["rows"]
    old_ids, new_ids = set(old_rows), set(new_rows)
    added = [
        {"ajo_id": key, "new": new_rows[key]}
        for key in sorted(new_ids - old_ids)
    ]
    missing = [
        {
            "ajo_id": key,
            "old": old_rows[key],
            "classification": "missing_in_later_snapshot_unconfirmed",
            "deletion_event": False,
        }
        for key in sorted(old_ids - new_ids)
    ]
    changed = []
    status_changes = []
    field_change_counts = Counter()
    status_transition_counts = Counter()
    for key in sorted(old_ids & new_ids):
        before, after = old_rows[key], new_rows[key]
        fields = sorted(set(before) | set(after))
        differences = {
            name: {"old": before.get(name), "new": after.get(name)}
            for name in fields if before.get(name) != after.get(name)
        }
        if differences:
            item = {"ajo_id": key, "changes": differences}
            changed.append(item)
            field_change_counts.update(differences.keys())
            if "FinishedReporting" in differences:
                transition = f"{differences['FinishedReporting']['old']} -> {differences['FinishedReporting']['new']}"
                status_transition_counts[transition] += 1
                status_changes.append({
                    "ajo_id": key,
                    **differences["FinishedReporting"],
                })
    return {
        "old_row_count": len(old_rows),
        "new_row_count": len(new_rows),
        "added_rows": added,
        "missing_rows_unconfirmed": missing,
        "changed_rows": changed,
        "finished_reporting_changes": status_changes,
        "field_change_counts": dict(field_change_counts),
        "status_transition_counts": dict(status_transition_counts),
        "unchanged_row_count": len(old_ids & new_ids) - len(changed),
    }


def compare_snapshot_sets(root: Path, old_date: str, new_date: str, expected_afo_count: int = 129) -> dict[str, Any]:
    base = root / "data" / "national_afo_snapshots"
    if not base.is_dir():
        raise ValueError(f"Snapshot directory not found: {base}")
    afo_dirs = sorted(p.name for p in base.iterdir() if p.is_dir())
    if len(afo_dirs) != expected_afo_count:
        raise ValueError(f"Expected {expected_afo_count} ÄFO directories, found {len(afo_dirs)}")
    results = {}
    old_total = new_total = 0
    totals = Counter()
    field_totals = Counter()
    status_transitions = Counter()
    for afo_id in afo_dirs:
        old_path = base / afo_id / f"{old_date}.json"
        new_path = base / afo_id / f"{new_date}.json"
        if not old_path.is_file() or not new_path.is_file():
            raise ValueError(f"Incomplete snapshot pair for {afo_id}: {old_path.name}, {new_path.name}")
        old = load_snapshot(old_path, old_date, afo_id)
        new = load_snapshot(new_path, new_date, afo_id)
        if old["metadata"].get("hunting_season") != new["metadata"].get("hunting_season"):
            raise ValueError(f"Season mismatch for {afo_id}")
        result = compare_afo(old, new)
        results[afo_id] = result
        old_total += result["old_row_count"]
        new_total += result["new_row_count"]
        totals["added"] += len(result["added_rows"])
        totals["missing_unconfirmed"] += len(result["missing_rows_unconfirmed"])
        totals["changed"] += len(result["changed_rows"])
        totals["status_changed"] += len(result["finished_reporting_changes"])
        totals["unchanged"] += result["unchanged_row_count"]
        field_totals.update(result["field_change_counts"])
        status_transitions.update(result["status_transition_counts"])
    return {
        "report_type": "national_afo_ajo_row_diff",
        "old_snapshot_date": old_date,
        "new_snapshot_date": new_date,
        "hunting_season": "2026/2027",
        "boundary_mode": "current",
        "afo_count": len(afo_dirs),
        "old_raw_ajo_row_count": old_total,
        "new_raw_ajo_row_count": new_total,
        "summary": dict(totals),
        "field_change_counts": dict(field_totals),
        "finished_reporting_transition_counts": dict(status_transitions),
        "absence_policy": "Rows missing from the later snapshot are unconfirmed absences, not deletion events.",
        "source_snapshots_modified": False,
        "areas": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--old-date", default="2026-11-21")
    parser.add_argument("--new-date", default="2026-11-23")
    parser.add_argument("--expected-afo-count", type=int, default=129)
    parser.add_argument("--out", type=Path, default=Path("out/national-ajo-row-diff.json"))
    args = parser.parse_args()
    report = compare_snapshot_sets(args.root, args.old_date, args.new_date, args.expected_afo_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(args.out),
        "afo_count": report["afo_count"],
        "old_rows": report["old_raw_ajo_row_count"],
        "new_rows": report["new_raw_ajo_row_count"],
        "summary": report["summary"],
        "field_change_counts": report["field_change_counts"],
        "finished_reporting_transition_counts": report["finished_reporting_transition_counts"],
        "source_snapshots_modified": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
