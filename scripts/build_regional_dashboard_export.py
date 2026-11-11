#!/usr/bin/env python3
"""Build a compact public dashboard export from immutable regional Älgdata snapshots."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

TOTAL_FIELD = "fallda_totalt"


def read_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    if len(rows) != 1:
        raise ValueError(f"{path}: expected exactly one row, got {len(rows)}")
    return {str(k): str(v or "").strip() for k, v in rows[0].items() if k}


def number(value: str) -> int | float | None:
    value = value.strip().replace(",", ".")
    if not value or value == "-":
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return int(result) if result.is_integer() else result


def build_area(folder: Path) -> dict:
    csv_files = sorted(folder.glob("*.csv"))
    snapshots = []
    first_positive = None
    latest_increase = None
    previous_total = None
    latest_meta = {}

    for csv_path in csv_files:
        meta_path = csv_path.with_suffix(".json")
        if not meta_path.is_file():
            raise ValueError(f"{folder.name}/{csv_path.stem}: missing metadata")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        row = read_row(csv_path)
        total = number(row.get(TOTAL_FIELD, ""))
        delta = None if previous_total is None or total is None else total - previous_total
        if total is not None and total > 0 and first_positive is None:
            first_positive = csv_path.stem
        if delta is not None and delta > 0:
            latest_increase = csv_path.stem

        snapshots.append({
            "date": csv_path.stem,
            "total": total,
            "delta": delta,
            "adult_total": number(row.get("fallda_vuxna_totalt", "")),
            "calf_total": number(row.get("fallda_kalvar_totalt", "")),
            "reported_area_ha": number(row.get("registrerad_areal_ha", "")),
            "slutrapporterat": row.get("slutrapporterat") or None,
        })
        previous_total = total
        latest_meta = meta

    latest = snapshots[-1] if snapshots else None
    return {
        "area_key": folder.name,
        "area_id": latest_meta.get("area_id"),
        "area_display_id": latest_meta.get("area_display_id"),
        # Some portal catalogue labels contain only the trailing area type
        # ("A" or "Ä") when the actual hunting-area name is missing. Never
        # present that type marker as the area's name; use its stable ID instead.
        "area_name": latest_meta.get("area_name") or latest_meta.get("area_display_id") or folder.name,
        "area_name_missing": not bool(latest_meta.get("area_name")),
        "catalogue_area_name": latest_meta.get("catalogue_area_name"),
        "quality_flags": latest_meta.get("quality_flags") or [],
        "county": latest_meta.get("county"),
        "afo": latest_meta.get("afo"),
        "hunting_season": latest_meta.get("hunting_season", "2026/2027"),
        "snapshot_count": len(snapshots),
        "first_snapshot_date": snapshots[0]["date"] if snapshots else None,
        "latest_snapshot_date": latest["date"] if latest else None,
        "first_observed_positive_date": first_positive,
        "latest_observed_increase_date": latest_increase,
        "latest_total": latest["total"] if latest else None,
        "latest_delta": latest["delta"] if latest else None,
        "slutrapporterat": latest["slutrapporterat"] if latest else None,
        "snapshots": snapshots,
    }


def build_export(root: Path, status_root: Path | None = None) -> dict:
    areas_by_key = {area["area_key"]: area for area in
                    (build_area(folder) for folder in sorted(root.iterdir()) if folder.is_dir())}
    status_root = status_root or root.parent / "regional_pilot_status"
    if status_root.exists():
        for folder in sorted(p for p in status_root.iterdir() if p.is_dir()):
            statuses = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]
            if not statuses:
                continue
            latest_status = statuses[-1]
            area = areas_by_key.get(folder.name)
            if area is None:
                area = {
                    "area_key": folder.name, "area_id": latest_status.get("area_id"),
                    "area_display_id": latest_status.get("area_display_id"),
                    "area_name": latest_status.get("area_name") or latest_status.get("area_display_id") or folder.name,
                    "area_name_missing": not bool(latest_status.get("area_name")),
                    "county": latest_status.get("county"), "afo": latest_status.get("afo"),
                    "hunting_season": latest_status.get("hunting_season"), "snapshot_count": 0,
                    "first_snapshot_date": None, "latest_snapshot_date": None,
                    "first_observed_positive_date": None, "latest_observed_increase_date": None,
                    "latest_total": None, "latest_delta": None, "slutrapporterat": None, "snapshots": []
                }
                areas_by_key[folder.name] = area
            area["latest_observation_status"] = latest_status.get("observation_status")
            area["latest_observation_date"] = latest_status.get("snapshot_date_utc")
            area["latest_data_status"] = latest_status.get("data_status")
            area["no_data_observation_count"] = len(statuses)
            area["no_data_observations"] = [
                {"date": item.get("snapshot_date_utc"), "status": item.get("data_status")}
                for item in statuses
            ]
    areas = list(areas_by_key.values())
    areas.sort(key=lambda x: (x.get("county") or "", x.get("area_name") or ""))
    dates = sorted({s["date"] for a in areas for s in a["snapshots"]})
    latest_date = max(dates) if dates else None
    latest_areas = sum(1 for a in areas if a["latest_snapshot_date"] == latest_date)
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Länsstyrelsernas Älgdata statistikportal",
        "source_url": "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/",
        "report": "Avskjutning med mål — ÄJO",
        "hunting_season": "2026/2027",
        "latest_snapshot_date": latest_date,
        "area_count": len(areas),
        "areas_with_latest_snapshot": latest_areas,
        "snapshot_date_count": len(dates),
        "interpretation": (
            "Dates are observation dates in daily cumulative portal snapshots. "
            "First observed positive is not the exact kill date. Latest observed increase "
            "is the snapshot date when a cumulative increase was first visible; reporting "
            "delays and corrections may affect it."
        ),
        "areas": areas,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/regional_pilot_snapshots"))
    parser.add_argument("--output", type=Path, default=Path("data/regional_pilot_dashboard.json"))
    parser.add_argument("--status-root", type=Path, default=Path("data/regional_pilot_status"))
    args = parser.parse_args()
    payload = build_export(args.root, args.status_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "area_count": payload["area_count"],
        "latest_snapshot_date": payload["latest_snapshot_date"],
        "areas_with_latest_snapshot": payload["areas_with_latest_snapshot"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
