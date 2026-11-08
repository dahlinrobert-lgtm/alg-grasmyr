#!/usr/bin/env python3
"""Validate integrity and day-to-day change detection in Älgdata snapshots."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_COLUMNS = {
    "registreringsnummer",
    "jaktomradesnamn",
    "fallda_totalt",
    "avskjutningsmal_totalt",
}
SEASON_COLUMNS = ("jaktsasong", "slutrapporterat")
SEASON_RE = re.compile(r"^\\d{4}/\\d{4}$")


class ValidationError(Exception):
    pass


def load_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValidationError(f"{path}: missing required columns: {', '.join(sorted(missing))}")
        season_column = next((name for name in SEASON_COLUMNS if name in columns), None)
        if season_column is None:
            raise ValidationError(
                f"{path}: missing hunting-season column; expected one of: {', '.join(SEASON_COLUMNS)}"
            )
        rows: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            season = (row.get(season_column) or "").strip()
            if not season:
                raise ValidationError(f"{path}:{line_number}: empty {season_column}")
            if not SEASON_RE.fullmatch(season):
                raise ValidationError(
                    f"{path}:{line_number}: invalid hunting season {season!r} in {season_column}"
                )
            if season in rows:
                raise ValidationError(f"{path}:{line_number}: duplicate hunting season {season!r}")
            normalized = {str(k): str(v or "") for k, v in row.items() if k is not None}
            normalized["jaktsasong"] = season
            rows[season] = normalized
    if not rows:
        raise ValidationError(f"{path}: CSV contains no data rows")
    return rows


def compare_rows(previous: dict[str, dict[str, str]], current: dict[str, dict[str, str]]) -> list[dict]:
    changes = []
    for season in sorted(set(previous) | set(current)):
        old = previous.get(season)
        new = current.get(season)
        if old is None:
            changes.append({"season": season, "change": "new_season", "current": new})
        elif new is None:
            changes.append({"season": season, "change": "season_missing", "previous": old})
        else:
            fields = {
                field: {"previous": old.get(field, ""), "current": new.get(field, "")}
                for field in sorted(set(old) | set(new))
                if old.get(field, "") != new.get(field, "")
            }
            if fields:
                changes.append({"season": season, "change": "values_changed", "fields": fields})
    return changes


def validate_area(area_dir: Path) -> list[str]:
    errors: list[str] = []
    csv_by_date = {p.stem: p for p in area_dir.glob("*.csv")}
    json_by_date = {p.stem: p for p in area_dir.glob("*.json")}
    dates = sorted(set(csv_by_date) | set(json_by_date))

    for date in dates:
        if not DATE_RE.fullmatch(date):
            errors.append(f"{area_dir}: unexpected snapshot filename date {date!r}")
            continue
        if date not in csv_by_date:
            errors.append(f"{area_dir}/{date}: metadata exists without CSV")
        if date not in json_by_date:
            errors.append(f"{area_dir}/{date}: CSV exists without metadata")

    valid_dates = sorted(set(csv_by_date) & set(json_by_date))
    previous_rows: dict[str, dict[str, str]] = {}
    previous_date: str | None = None

    for date in valid_dates:
        csv_path = csv_by_date[date]
        json_path = json_by_date[date]
        try:
            metadata = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{json_path}: cannot read valid JSON metadata: {exc}")
            continue

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"{csv_path}: invalid calendar date {date!r}")
            continue

        if metadata.get("snapshot_date_utc") != date:
            errors.append(f"{json_path}: snapshot_date_utc does not match filename")
        captured = metadata.get("captured_at_utc")
        try:
            captured_dt = datetime.fromisoformat(str(captured).replace("Z", "+00:00"))
            if captured_dt.tzinfo is None:
                raise ValueError("timestamp has no timezone")
        except ValueError:
            errors.append(f"{json_path}: captured_at_utc is missing or not timezone-aware")

        if not metadata.get("area_id") or not metadata.get("area_key"):
            errors.append(f"{json_path}: area_id or area_key is missing")
        if metadata.get("report_id") != "4":
            errors.append(f"{json_path}: unexpected report_id {metadata.get('report_id')!r}")
        if metadata.get("boundary_mode") not in {"current", "historical"}:
            errors.append(f"{json_path}: invalid boundary_mode")

        digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        if metadata.get("sha256") != digest:
            errors.append(f"{csv_path}: SHA-256 does not match metadata")

        try:
            rows = load_csv(csv_path)
        except (OSError, UnicodeError, csv.Error, ValidationError) as exc:
            errors.append(str(exc))
            continue

        if metadata.get("season_count") != len(rows):
            errors.append(f"{json_path}: season_count does not match CSV ({len(rows)})")
        report_rows = (metadata.get("download_report") or {}).get("data_csv_rows")
        if report_rows != len(rows):
            errors.append(f"{json_path}: download_report.data_csv_rows does not match CSV ({len(rows)})")
        if metadata.get("warnings") is None:
            errors.append(f"{json_path}: warnings field is missing")

        expected_previous = f"{previous_date}.csv" if previous_date else None
        if metadata.get("previous_snapshot") != expected_previous:
            errors.append(
                f"{json_path}: previous_snapshot should be {expected_previous!r}, "
                f"got {metadata.get('previous_snapshot')!r}"
            )

        expected_changes = compare_rows(previous_rows, rows)
        actual_changes = metadata.get("changes_since_previous_snapshot")
        if actual_changes != expected_changes:
            errors.append(f"{json_path}: change log does not match the two CSV snapshots")

        previous_rows = rows
        previous_date = date

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/daily_snapshots"))
    args = parser.parse_args()

    if not args.root.exists():
        print(f"ERROR: snapshot directory does not exist: {args.root}", file=sys.stderr)
        return 1

    area_dirs = sorted(path for path in args.root.iterdir() if path.is_dir())
    if not area_dirs:
        print(f"ERROR: no area snapshot directories found under {args.root}", file=sys.stderr)
        return 1

    errors = []
    snapshot_count = 0
    for area_dir in area_dirs:
        area_errors = validate_area(area_dir)
        errors.extend(area_errors)
        snapshot_count += len(list(area_dir.glob("*.csv")))

    if errors:
        print(f"FAILED: {len(errors)} validation error(s) across {snapshot_count} CSV snapshot(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: validated {snapshot_count} dated CSV snapshot(s) across {len(area_dirs)} area(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
