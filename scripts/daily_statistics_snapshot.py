#!/usr/bin/env python3
"""Create a dated, immutable snapshot of current Älgdata harvest statistics.

The existing portal downloader remains the source adapter. This wrapper stores
its raw rendered CSV and metadata under a date/area path, and compares the new
observation with the previous stored snapshot. It deliberately describes
changes as changes in the portal's registered statistics, not as exact kill
dates: reporting can be delayed and the portal report is cumulative by season.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADER = ROOT / "scripts" / "download_statistics.py"


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        rows = {}
        for row in reader:
            key = row.get("jaktsasong") or row.get("Jaktsäsong") or str(len(rows))
            rows[key] = {str(k): str(v or "") for k, v in row.items() if k is not None}
        return rows


def compare(previous: dict[str, dict[str, str]], current: dict[str, dict[str, str]]) -> list[dict]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area-id", default="724577")
    parser.add_argument("--area-key", default="hornean")
    parser.add_argument("--afo-name", default="Sydöstra älgförvaltningsområdet")
    parser.add_argument("--from-year", default="2020/2021")
    parser.add_argument("--to-year", default="2026/2027")
    parser.add_argument("--boundary-mode", choices=("current", "historical"), default="current")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "daily_snapshots")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    snapshot_date = now.date().isoformat()
    out_dir = args.output_root / args.area_key
    out_dir.mkdir(parents=True, exist_ok=True)
    dated_csv = out_dir / f"{snapshot_date}.csv"
    dated_json = out_dir / f"{snapshot_date}.json"

    import tempfile
    with tempfile.TemporaryDirectory(prefix="algdata-snapshot-") as tmp:
        tmp_dir = Path(tmp)
        command = [
            sys.executable, str(DOWNLOADER),
            "--out", str(tmp_dir),
            "--area-id", args.area_id,
            "--afo-name", args.afo_name,
            "--from-year", args.from_year,
            "--to-year", args.to_year,
            "--boundary-mode", args.boundary_mode,
            "--report-id", "4",
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if completed.returncode != 0:
            raise RuntimeError(
                f"Älgdata downloader failed (exit {completed.returncode}). "
                f"stdout={completed.stdout[-2000:]} stderr={completed.stderr[-4000:]}"
            )
        reports = list(tmp_dir.glob("download-report.json"))
        csv_files = list(tmp_dir.glob("*.csv"))
        if not reports or not csv_files:
            raise RuntimeError("Downloader completed without both report metadata and CSV data")
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        source_csv = csv_files[0]
        warnings = [message for message in report.get("errors", []) if message.startswith("Requested end year ")]
        fatal_errors = [message for message in report.get("errors", []) if message not in warnings]
        if fatal_errors:
            raise RuntimeError("Älgdata report contains errors: " + "; ".join(fatal_errors))
        if not report.get("data_csv_rows"):
            raise RuntimeError("Älgdata report returned no data rows")
        raw_bytes = source_csv.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        dated_csv.write_bytes(raw_bytes)

    previous_files = sorted(
        p for p in out_dir.glob("*.csv") if p.name != dated_csv.name
    )
    previous_rows = read_rows(previous_files[-1]) if previous_files else {}
    current_rows = read_rows(dated_csv)
    changes = compare(previous_rows, current_rows)

    metadata = {
        "snapshot_date_utc": snapshot_date,
        "captured_at_utc": now.isoformat(),
        "source": "Länsstyrelsernas Älgdata statistikportal",
        "source_url": "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/",
        "area_key": args.area_key,
        "area_id": args.area_id,
        "afo": args.afo_name,
        "boundary_mode": args.boundary_mode,
        "report_id": "4",
        "report_name": "Avskjutning med mål — ÄJO",
        "requested_season_range": [args.from_year, args.to_year],
        "selected_season_end": report.get("hunting_year_to_selected"),
        "download_report": report,
        "warnings": warnings,
        "csv_file": dated_csv.name,
        "sha256": digest,
        "season_count": len(current_rows),
        "previous_snapshot": previous_files[-1].name if previous_files else None,
        "changes_since_previous_snapshot": changes,
        "interpretation": (
            "Changes are changes in the cumulative values registered in the portal. "
            "They are not exact individual kill dates and may reflect delayed reporting."
        ),
    }
    dated_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "snapshot_csv": str(dated_csv.relative_to(ROOT)),
        "snapshot_metadata": str(dated_json.relative_to(ROOT)),
        "sha256": digest,
        "season_count": len(current_rows),
        "changes_since_previous_snapshot": len(changes),
        "previous_snapshot": metadata["previous_snapshot"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
