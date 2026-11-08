#!/usr/bin/env python3
"""Archive a validated regional pilot as immutable per-area daily snapshots."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_one_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"{path}: expected exactly one area row, got {len(rows)}")
    return {str(k): str(v or "") for k, v in rows[0].items() if k is not None}


def compare_rows(previous: dict[str, str], current: dict[str, str]) -> list[dict]:
    changes = []
    for field in sorted(set(previous) | set(current)):
        old, new = previous.get(field, ""), current.get(field, "")
        if old != new:
            changes.append({"field": field, "previous": old, "current": new})
    return changes


def area_key(candidate: dict) -> str:
    county = re.sub(r"[^a-z0-9]+", "-", candidate["county"].casefold()).strip("-")
    display_id = candidate.get("area_display_id") or candidate["area_portal_id"]
    stable = re.sub(r"[^a-zA-Z0-9-]+", "-", display_id).strip("-").lower()
    return f"{county}-{stable}"


def archive_pilot(pilot_dir: Path, output_root: Path, captured_at: datetime | None = None) -> dict:
    captured_at = captured_at or datetime.now(timezone.utc)
    date = captured_at.date().isoformat()
    summary = json.loads((pilot_dir / "pilot_summary.json").read_text(encoding="utf-8"))
    selected = json.loads((pilot_dir / "selected_candidates.json").read_text(encoding="utf-8"))
    candidates = selected.get("candidates", [])
    results = summary.get("results", [])
    if not candidates or len(candidates) != summary.get("candidate_count"):
        raise ValueError("Pilot candidate count is empty or inconsistent")
    if (len(results) != len(candidates)
            or summary.get("portal_selection_success_count") != len(candidates)
            or summary.get("data_available_count") != len(candidates)
            or summary.get("data_row_count") != len(candidates)):
        raise ValueError("Pilot must return exactly one data row for every selected area")
    if summary.get("failure_count") != 0 or summary.get("identity_collisions"):
        raise ValueError("Refusing to archive pilot with failures or identity collisions")
    by_id = {str(x["area_portal_id"]): x for x in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("Duplicate portal IDs in candidate set")
    if summary.get("min_end_year") != 2026:
        raise ValueError("This daily baseline workflow is pinned to 2026/2027")
    archived, unchanged = [], []
    for result in results:
        portal_id = str(result["area_id"])
        candidate = by_id.get(portal_id)
        if candidate is None or not result.get("portal_selection_success"):
            raise ValueError(f"Unexpected or unsuccessful area result: {portal_id}")
        if result.get("selected_to_year") != "2026/2027":
            raise ValueError(f"{portal_id}: selected season is not 2026/2027")
        if result.get("boundary_mode") != "current":
            raise ValueError(f"{portal_id}: non-current boundary mode")
        folder = next((p for p in pilot_dir.iterdir() if p.is_dir() and p.name.endswith(f"-{portal_id}")), None)
        if folder is None:
            raise ValueError(f"{portal_id}: missing pilot output folder")
        report_path = folder / "download-report.json"
        if not report_path.is_file():
            raise ValueError(f"{portal_id}: missing download-report.json")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        selected_area = report.get("selected_area") or {}
        if str(selected_area.get("area_id", "")) != portal_id:
            raise ValueError(f"{portal_id}: portal selected a different area")
        if report.get("hunting_year_to_selected") != "2026/2027":
            raise ValueError(f"{portal_id}: report season mismatch")
        csv_name = report.get("data_csv")
        source_csv = folder / csv_name if csv_name else None
        if source_csv is None or not source_csv.is_file():
            raise ValueError(f"{portal_id}: missing source CSV")
        if report.get("errors"):
            raise ValueError(f"{portal_id}: portal report contains errors: {report.get('errors')}")
        row = read_one_row(source_csv)
        if row.get("registreringsnummer") != str(selected_area.get("display_label", "")).split(" - ")[0]:
            raise ValueError(f"{portal_id}: CSV registration number does not match portal selection")
        if row.get("slutrapporterat") not in {"Ja", "Nej"}:
            raise ValueError(f"{portal_id}: invalid slutrapporterat flag")
        key = area_key(candidate)
        target = output_root / key
        target.mkdir(parents=True, exist_ok=True)
        csv_path = target / f"{date}.csv"
        json_path = target / f"{date}.json"
        digest = sha256(source_csv)
        if csv_path.exists() or json_path.exists():
            if csv_path.is_file() and json_path.is_file():
                old_meta = json.loads(json_path.read_text(encoding="utf-8"))
                if old_meta.get("sha256") == digest:
                    unchanged.append(key)
                    continue
            raise FileExistsError(f"{key}: refusing to overwrite an existing dated snapshot")
        previous_files = sorted(target.glob("*.csv"))
        previous_row, previous_name, previous_meta = {}, None, {}
        if previous_files:
            previous_csv = previous_files[-1]
            previous_meta_path = previous_csv.with_suffix(".json")
            if not previous_meta_path.is_file():
                raise ValueError(f"{key}: previous snapshot metadata missing")
            previous_meta = json.loads(previous_meta_path.read_text(encoding="utf-8"))
            previous_row = read_one_row(previous_csv)
            previous_name = previous_csv.name
        shutil.copyfile(source_csv, csv_path)
        source_name = (row.get("jaktomradesnamn") or "").strip()
        catalogue_name = (candidate.get("area_name") or "").strip()
        generic_labels = {"A", "Ä", "B", "E", "LICENSOMRÅDE", "ÄLGSKÖTSELOMRÅDE"}
        has_catalogue_name = bool(catalogue_name and catalogue_name.upper() not in generic_labels)
        quality_flags = []
        if not source_name:
            quality_flags.append("missing_jaktomradesnamn")
        if not source_name and not has_catalogue_name:
            quality_flags.append("missing_descriptive_area_name")
        metadata = {
            "snapshot_date_utc": date,
            "captured_at_utc": captured_at.isoformat(),
            "source": "Länsstyrelsernas Älgdata statistikportal",
            "source_url": "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/",
            "area_key": key,
            "area_id": portal_id,
            "area_display_id": candidate.get("area_display_id", ""),
            "area_name": source_name,
            "catalogue_area_name": catalogue_name,
            "area_label_raw": candidate.get("area_label_raw", ""),
            "display_name": source_name or (catalogue_name if has_catalogue_name else f"Jaktområde {candidate.get('area_display_id') or candidate.get('area_portal_id')}"),
            "display_name_source": "portal_report" if source_name else ("selector_catalogue" if has_catalogue_name else "registration_id_fallback"),
            "quality_flags": quality_flags,
            "county": candidate["county"],
            "afo": candidate["afo_name"],
            "boundary_mode": "current",
            "report_id": "4",
            "report_name": "Avskjutning med mål — ÄJO",
            "hunting_season": "2026/2027",
            "slutrapporterat": row["slutrapporterat"],
            "csv_file": csv_path.name,
            "sha256": digest,
            "row_count": 1,
            "previous_snapshot": previous_name,
            "previous_area_id": previous_meta.get("area_id"),
            "changes_since_previous_snapshot": compare_rows(previous_row, row) if previous_row else [],
            "download_report": report,
            "interpretation": "Cumulative portal report values observed at capture time; changes are not exact kill dates and may reflect delayed reporting or corrections."
        }
        json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        archived.append(key)
    result = {
        "snapshot_date_utc": date, "candidate_count": len(candidates),
        "archived_count": len(archived), "unchanged_count": len(unchanged),
        "area_keys_archived": archived, "area_keys_unchanged": unchanged,
        "output_root": str(output_root)
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, default=Path("out/geographic-pilot"))
    parser.add_argument("--output-root", type=Path, default=Path("data/regional_pilot_snapshots"))
    args = parser.parse_args()
    archive_pilot(args.pilot_dir, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
