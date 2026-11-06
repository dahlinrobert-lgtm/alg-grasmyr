#!/usr/bin/env python3
"""Validate immutable per-area regional pilot snapshots and adjacent changes."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_one(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"expected exactly one row, got {len(rows)}")
    return {str(k): str(v or "") for k, v in rows[0].items() if k is not None}


def compare_rows(previous: dict[str, str], current: dict[str, str]) -> list[dict]:
    return [
        {"field": field, "previous": previous.get(field, ""), "current": current.get(field, "")}
        for field in sorted(set(previous) | set(current))
        if previous.get(field, "") != current.get(field, "")
    ]


def validate_area(folder: Path) -> list[str]:
    errors = []
    csvs = {p.stem: p for p in folder.glob("*.csv")}
    jsons = {p.stem: p for p in folder.glob("*.json")}
    if set(csvs) != set(jsons):
        errors.append(f"{folder.name}: CSV/JSON date pairs do not match")
    previous_row, previous_name, previous_area_id = {}, None, None
    for date in sorted(set(csvs) & set(jsons)):
        cp, jp = csvs[date], jsons[date]
        if not DATE_RE.fullmatch(date):
            errors.append(f"{folder.name}: invalid snapshot date {date}")
            continue
        try:
            datetime.strptime(date, "%Y-%m-%d")
            meta = json.loads(jp.read_text(encoding="utf-8"))
            row = read_one(cp)
        except Exception as exc:
            errors.append(f"{folder.name}/{date}: cannot read snapshot: {exc}")
            continue
        if meta.get("snapshot_date_utc") != date:
            errors.append(f"{folder.name}/{date}: metadata date mismatch")
        try:
            captured = datetime.fromisoformat(str(meta.get("captured_at_utc", "")).replace("Z", "+00:00"))
            if captured.tzinfo is None:
                raise ValueError("timezone missing")
        except ValueError:
            errors.append(f"{folder.name}/{date}: invalid capture timestamp")
        if meta.get("area_key") != folder.name:
            errors.append(f"{folder.name}/{date}: area_key differs from directory")
        if not meta.get("area_id") or not meta.get("area_display_id"):
            errors.append(f"{folder.name}/{date}: missing portal or display identity")
        if meta.get("hunting_season") != "2026/2027":
            errors.append(f"{folder.name}/{date}: unexpected hunting season")
        if meta.get("boundary_mode") != "current" or meta.get("report_id") != "4":
            errors.append(f"{folder.name}/{date}: unexpected report or boundary mode")
        if meta.get("row_count") != 1:
            errors.append(f"{folder.name}/{date}: row_count is not 1")
        if hashlib.sha256(cp.read_bytes()).hexdigest() != meta.get("sha256"):
            errors.append(f"{folder.name}/{date}: SHA-256 mismatch")
        if row.get("slutrapporterat") not in {"Ja", "Nej"}:
            errors.append(f"{folder.name}/{date}: invalid slutrapporterat flag")
        if not row.get("registreringsnummer"):
            errors.append(f"{folder.name}/{date}: missing registration number")
        expected_flags = ["missing_jaktomradesnamn"] if not row.get("jaktomradesnamn") else []
        if meta.get("quality_flags", []) != expected_flags:
            errors.append(f"{folder.name}/{date}: area-name quality flags mismatch")
        if meta.get("previous_snapshot") != previous_name:
            errors.append(f"{folder.name}/{date}: previous_snapshot pointer mismatch")
        expected_changes = compare_rows(previous_row, row) if previous_name else []
        if meta.get("changes_since_previous_snapshot") != expected_changes:
            errors.append(f"{folder.name}/{date}: change log mismatch")
        if previous_area_id and meta.get("previous_area_id") != previous_area_id:
            errors.append(f"{folder.name}/{date}: previous portal ID lineage mismatch")
        previous_row, previous_name, previous_area_id = row, cp.name, meta.get("area_id")
    return errors


def validate_root(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"snapshot root does not exist: {root}"]
    folders = sorted(p for p in root.iterdir() if p.is_dir())
    if not folders:
        return [f"no area snapshot directories under {root}"]
    errors = []
    for folder in folders:
        errors.extend(validate_area(folder))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/regional_pilot_snapshots"))
    args = parser.parse_args()
    errors = validate_root(args.root)
    print(json.dumps({"valid": not errors, "error_count": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
