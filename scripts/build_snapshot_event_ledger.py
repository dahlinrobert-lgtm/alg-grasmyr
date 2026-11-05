#!/usr/bin/env python3
"""Build a deterministic event ledger and quality report from daily Älgdata snapshots."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

EVENT_FIELDS = [
    "event_id", "observed_at_utc", "snapshot_date_utc", "area_key", "area_id",
    "area_name", "hunting_season", "field_name", "previous_value",
    "current_value", "event_type", "classification_reason", "source_csv",
    "previous_csv",
]
CUMULATIVE_FIELDS = {
    "fallda_totalt", "fallda_vuxna_totalt", "fallda_vuxna_handjur",
    "fallda_vuxna_hondjur", "fallda_kalvar_totalt", "fallda_kalvar_handjur",
    "fallda_kalvar_hondjur", "fallda_otjanliga", "fallda_oregistrerad_mark",
}
NUMERIC_RE = re.compile(r"^-?\d+(?:[,.]\d+)?%?$")


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        rows = {}
        for row in reader:
            season = (row.get("jaktsasong") or "").strip()
            if season:
                rows[season] = {str(k): str(v or "").strip() for k, v in row.items() if k}
        return rows


def numeric(value: str) -> float | None:
    cleaned = value.strip().replace("%", "").replace(",", ".")
    if not cleaned or not NUMERIC_RE.fullmatch(value.strip()):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def classify(field: str, old: str, new: str) -> tuple[str, str]:
    if not old and new:
        return "new_value", "Fältet saknade tidigare värde och har nu ett rapporterat värde."
    if old and not new:
        return "value_removed", "Ett tidigare rapporterat värde saknas i det senaste uttaget; detta är inte bevis för noll."
    before, after = numeric(old), numeric(new)
    if field in CUMULATIVE_FIELDS and before is not None and after is not None and after > before:
        return "reported_value_increase", "Kumulativt portalvärde har ökat; ändringen visar nyregistrerad rapportering, inte exakt händelsedatum."
    if before is not None and after is not None and after < before:
        return "correction", "Rapporterat numeriskt värde har minskat och klassas som möjlig rättelse."
    return "correction", "Ett tidigare rapporterat fältvärde har ändrats; orsaken kan inte avgöras enbart från snapshots."


def event_id(payload: dict) -> str:
    stable = {key: payload.get(key) for key in (
        "area_id", "snapshot_date_utc", "hunting_season", "field_name",
        "event_type", "previous_value", "current_value",
    )}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_area(area_dir: Path) -> tuple[list[dict], dict]:
    csv_files = sorted(area_dir.glob("*.csv"))
    events: list[dict] = []
    previous_rows = None
    previous_path = None
    area_info = {}
    season_counts = []
    for current_path in csv_files:
        current_rows = read_rows(current_path)
        metadata_path = current_path.with_suffix(".json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        area_info = metadata or area_info
        season_counts.append({"date": current_path.stem, "season_count": len(current_rows)})
        if previous_rows is not None:
            common = sorted(set(previous_rows) & set(current_rows))
            for season in common:
                old_row, new_row = previous_rows[season], current_rows[season]
                for field in sorted(set(old_row) | set(new_row)):
                    old, new = old_row.get(field, ""), new_row.get(field, "")
                    if old == new:
                        continue
                    event_type, reason = classify(field, old, new)
                    item = {
                        "observed_at_utc": metadata.get("captured_at_utc", ""),
                        "snapshot_date_utc": current_path.stem,
                        "area_key": metadata.get("area_key", area_dir.name),
                        "area_id": metadata.get("area_id", ""),
                        "area_name": new_row.get("jaktomradesnamn") or old_row.get("jaktomradesnamn", ""),
                        "hunting_season": season,
                        "field_name": field,
                        "previous_value": old,
                        "current_value": new,
                        "event_type": event_type,
                        "classification_reason": reason,
                        "source_csv": current_path.as_posix(),
                        "previous_csv": previous_path.as_posix() if previous_path else "",
                    }
                    item["event_id"] = event_id(item)
                    events.append(item)
            for season in sorted(set(current_rows) - set(previous_rows)):
                row = current_rows[season]
                item = {
                    "observed_at_utc": metadata.get("captured_at_utc", ""),
                    "snapshot_date_utc": current_path.stem,
                    "area_key": metadata.get("area_key", area_dir.name),
                    "area_id": metadata.get("area_id", ""),
                    "area_name": row.get("jaktomradesnamn", ""),
                    "hunting_season": season,
                    "field_name": "__season__",
                    "previous_value": "",
                    "current_value": "present",
                    "event_type": "new_season",
                    "classification_reason": "Jaktåret förekom inte i föregående snapshot men finns i det senaste uttaget.",
                    "source_csv": current_path.as_posix(),
                    "previous_csv": previous_path.as_posix() if previous_path else "",
                }
                item["event_id"] = event_id(item)
                events.append(item)
            for season in sorted(set(previous_rows) - set(current_rows)):
                row = previous_rows[season]
                item = {
                    "observed_at_utc": metadata.get("captured_at_utc", ""),
                    "snapshot_date_utc": current_path.stem,
                    "area_key": metadata.get("area_key", area_dir.name),
                    "area_id": metadata.get("area_id", ""),
                    "area_name": row.get("jaktomradesnamn", ""),
                    "hunting_season": season,
                    "field_name": "__season__",
                    "previous_value": "present",
                    "current_value": "",
                    "event_type": "season_missing",
                    "classification_reason": "Jaktåret saknas i senaste portaluttaget; möjlig uttags-/rapporteringslucka, inte bevis för raderad statistik.",
                    "source_csv": current_path.as_posix(),
                    "previous_csv": previous_path.as_posix() if previous_path else "",
                }
                item["event_id"] = event_id(item)
                events.append(item)
        previous_rows, previous_path = current_rows, current_path
    summary = {
        "area_key": area_info.get("area_key", area_dir.name),
        "area_id": area_info.get("area_id", ""),
        "area_name": area_info.get("download_report", {}).get("selected_area", {}).get("display_label", ""),
        "snapshot_count": len(csv_files),
        "first_snapshot": csv_files[0].stem if csv_files else None,
        "latest_snapshot": csv_files[-1].stem if csv_files else None,
        "season_counts": season_counts,
        "event_count": len(events),
    }
    return events, summary


def excel_inventory(root: Path) -> dict:
    candidates = sorted(
        p.relative_to(root).as_posix()
        for p in (root / "data" / "raw").rglob("*")
        if p.is_file() and p.suffix.lower() in {".xlsx", ".xls"}
    ) if (root / "data" / "raw").exists() else []
    return {
        "candidate_file_count": len(candidates),
        "candidate_files": candidates,
        "automatic_snapshot_matches": [],
        "verification_status": "not_verified",
        "note": "Filnamnsinventeringen fastställer inte att en Excel-export motsvarar ett visst snapshot. Matchning kräver verifierat manifest med område, jaktår och exportidentitet.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    snapshot_root = args.root / "data" / "daily_snapshots"
    all_events, areas = [], []
    for area_dir in sorted(p for p in snapshot_root.iterdir() if p.is_dir()):
        events, summary = build_area(area_dir)
        all_events.extend(events)
        areas.append(summary)
    all_events.sort(key=lambda x: (x["area_key"], x["snapshot_date_utc"], x["hunting_season"], x["field_name"], x["event_id"]))

    events_dir = args.root / "data" / "events"
    quality_dir = args.root / "data" / "quality"
    events_dir.mkdir(parents=True, exist_ok=True)
    quality_dir.mkdir(parents=True, exist_ok=True)
    area_keys = sorted({e["area_key"] for e in all_events} | {a["area_key"] for a in areas})
    for key in area_keys:
        subset = [e for e in all_events if e["area_key"] == key]
        jsonl_path = events_dir / f"{key}_events.jsonl"
        with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in subset:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        csv_path = events_dir / f"{key}_events.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDS, delimiter=";")
            writer.writeheader()
            writer.writerows(subset)

    counts = {}
    for event in all_events:
        counts[event["event_type"]] = counts.get(event["event_type"], 0) + 1
    quality = {
        "generated_at_utc": (max((a["latest_snapshot"] for a in areas if a["latest_snapshot"]), default="") + "T00:00:00Z") if areas else "",
        "scope": "daily portal snapshots; report 4 (Avskjutning med mål — ÄJO)",
        "area_count": len(areas),
        "snapshot_count": sum(a["snapshot_count"] for a in areas),
        "event_count": len(all_events),
        "event_counts_by_type": dict(sorted(counts.items())),
        "areas": areas,
        "source_export_inventory": excel_inventory(args.root),
        "interpretation_limits": [
            "Events compare adjacent available snapshots; they do not identify exact dates when an animal was harvested.",
            "A missing season is a portal-output absence, not proof that source statistics were deleted or equal to zero.",
            "The Excel inventory is a filename inventory only; no primary-source match is claimed without a verified manifest.",
            "Only fields that changed are emitted; unchanged daily observations are not duplicated as events.",
        ],
    }
    (quality_dir / "snapshot_quality_report.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"OK: wrote {len(all_events)} events from {quality['snapshot_count']} snapshots across {len(areas)} area(s)")
    print(f"Event types: {json.dumps(counts, ensure_ascii=False, sort_keys=True)}")
    print(f"Primary Excel candidates inventoried: {quality['source_export_inventory']['candidate_file_count']} (not automatically source-verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
