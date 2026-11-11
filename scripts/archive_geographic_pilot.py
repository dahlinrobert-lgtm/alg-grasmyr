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


def archive_pilot(pilot_dir: Path, output_root: Path, captured_at: datetime | None = None,
                  intraday_root: Path | None = None, status_root: Path | None = None) -> dict:
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
            or summary.get("data_available_count", 0) + summary.get("no_data_count", 0) != len(candidates)):
        raise ValueError("Pilot must return one successful data or explicit no-data result for every selected area")
    if summary.get("failure_count") != 0 or summary.get("identity_collisions"):
        raise ValueError("Refusing to archive pilot with failures or identity collisions")
    by_id = {str(x["area_portal_id"]): x for x in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("Duplicate portal IDs in candidate set")
    if summary.get("min_end_year") != 2026:
        raise ValueError("This daily baseline workflow is pinned to 2026/2027")
    archived, unchanged, intraday_archived, no_data_recorded = [], [], [], []
    status_root = status_root or output_root.parent / "regional_pilot_status"
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
        if report.get("errors"):
            raise ValueError(f"{portal_id}: portal report contains errors: {report.get('errors')}")
        key = area_key(candidate)
        if not result.get("data_available"):
            if (result.get("data_status") not in {"no_rendered_table", "no_rendered_rows", "unrecognized_table_structure"}
                    or int(result.get("data_csv_rows", -1)) != 0
                    or int(report.get("data_csv_rows", -1)) != 0
                    or report.get("data_status") != result.get("data_status")):
                raise ValueError(f"{portal_id}: no-data result is not explicitly attested by the portal report")
            status_dir = status_root / key
            status_dir.mkdir(parents=True, exist_ok=True)
            status_path = status_dir / f"{date}.json"
            status = {
                "snapshot_date_utc": date, "captured_at_utc": captured_at.isoformat(),
                "observation_status": "no_reported_data", "data_status": result["data_status"],
                "source": "Länsstyrelsernas Älgdata statistikportal", "area_key": key,
                "area_id": portal_id, "area_display_id": candidate.get("area_display_id", ""),
                "area_name": candidate.get("area_name", ""), "county": candidate["county"],
                "afo": candidate["afo_name"], "hunting_season": "2026/2027", "row_count": 0,
                "download_report": report,
                "interpretation": "Area selection succeeded, but the portal returned no report rows at capture time. This is not equivalent to zero harvested animals."
            }
            if status_path.exists():
                if json.loads(status_path.read_text(encoding="utf-8")) != status:
                    raise FileExistsError(f"{key}: refusing to overwrite existing no-data status for {date}")
            else:
                status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
            no_data_recorded.append(key)
            continue
        csv_name = report.get("data_csv")
        source_csv = folder / csv_name if csv_name else None
        if source_csv is None or not source_csv.is_file():
            raise ValueError(f"{portal_id}: missing source CSV")
        row = read_one_row(source_csv)
        if row.get("registreringsnummer") != str(selected_area.get("display_label", "")).split(" - ")[0]:
            raise ValueError(f"{portal_id}: CSV registration number does not match portal selection")
        if row.get("slutrapporterat") not in {"Ja", "Nej"}:
            raise ValueError(f"{portal_id}: invalid slutrapporterat flag")
        target = output_root / key
        target.mkdir(parents=True, exist_ok=True)
        csv_path = target / f"{date}.csv"
        json_path = target / f"{date}.json"
        digest = sha256(source_csv)
        if csv_path.exists() or json_path.exists():
            if not (csv_path.is_file() and json_path.is_file()):
                raise FileExistsError(f"{key}: incomplete existing daily snapshot pair")
            old_meta = json.loads(json_path.read_text(encoding="utf-8"))
            if old_meta.get("sha256") == digest:
                unchanged.append(key)
                continue

            # Keep the first daily observation immutable. A changed re-run is
            # retained separately as an intraday observation rather than
            # overwriting the canonical daily snapshot or failing the whole run.
            observation_root = intraday_root or output_root.parent / "regional_pilot_intraday"
            observation_dir = observation_root / key / date
            observation_dir.mkdir(parents=True, exist_ok=True)
            stamp = captured_at.strftime("%Y%m%dT%H%M%S%fZ")
            observation_csv = observation_dir / f"{stamp}.csv"
            observation_json = observation_dir / f"{stamp}.json"
            if observation_csv.exists() or observation_json.exists():
                raise FileExistsError(f"{key}: intraday observation timestamp collision")
            shutil.copyfile(source_csv, observation_csv)
            observation_meta = {
                "snapshot_date_utc": date,
                "captured_at_utc": captured_at.isoformat(),
                "observation_type": "same_day_change",
                "source": "Länsstyrelsernas Älgdata statistikportal",
                "area_key": key,
                "area_id": portal_id,
                "area_display_id": candidate.get("area_display_id", ""),
                "county": candidate["county"],
                "afo": candidate["afo_name"],
                "hunting_season": "2026/2027",
                "slutrapporterat": row["slutrapporterat"],
                "csv_file": observation_csv.name,
                "sha256": digest,
                "row_count": 1,
                "daily_snapshot": str(csv_path),
                "daily_snapshot_sha256": old_meta.get("sha256"),
                "changes_vs_daily_snapshot": compare_rows(read_one_row(csv_path), row),
                "interpretation": "Same-day cumulative portal observation; not a separate kill-date record."
            }
            observation_json.write_text(json.dumps(observation_meta, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
            intraday_archived.append(f"{key}/{date}/{stamp}")
            continue
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
        metadata = {
            "snapshot_date_utc": date,
            "captured_at_utc": captured_at.isoformat(),
            "source": "Länsstyrelsernas Älgdata statistikportal",
            "source_url": "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/",
            "area_key": key,
            "area_id": portal_id,
            "area_display_id": candidate.get("area_display_id", ""),
            "area_name": row.get("jaktomradesnamn", ""),
            "catalogue_area_name": candidate.get("area_name", ""),
            "quality_flags": ["missing_jaktomradesnamn"] if not row.get("jaktomradesnamn") else [],
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
        "intraday_archived_count": len(intraday_archived), "intraday_observations": intraday_archived,
        "no_data_count": len(no_data_recorded), "area_keys_no_data": no_data_recorded,
        "area_keys_archived": archived, "area_keys_unchanged": unchanged,
        "output_root": str(output_root)
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, default=Path("out/geographic-pilot"))
    parser.add_argument("--output-root", type=Path, default=Path("data/regional_pilot_snapshots"))
    parser.add_argument("--intraday-root", type=Path, default=Path("data/regional_pilot_intraday"))
    parser.add_argument("--status-root", type=Path, default=Path("data/regional_pilot_status"))
    args = parser.parse_args()
    archive_pilot(args.pilot_dir, args.output_root, intraday_root=args.intraday_root,
                  status_root=args.status_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
