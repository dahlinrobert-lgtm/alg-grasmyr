#!/usr/bin/env python3
"""Audit provenance of official Älgdata exports using an explicit source manifest.

A passing checksum establishes file integrity and declared identity, not equality
between a workbook's cells and daily portal snapshot values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SEASON = re.compile(r"^\d{4}/\d{4}$")
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def check_entry(root: Path, entry: dict) -> dict:
    result = {"source_id": str(entry.get("source_id", "")), "status": "invalid", "errors": []}
    required = ("source_id", "relative_path", "sha256", "area_key", "area_id",
                "hunting_seasons", "report_id", "boundary_mode", "exported_at_utc")
    for key in required:
        if not entry.get(key):
            result["errors"].append(f"missing {key}")
    if result["errors"]:
        return result
    rel = str(entry["relative_path"])
    posix = PurePosixPath(rel)
    if (posix.is_absolute() or ".." in posix.parts or "\\" in rel or
            posix.suffix.lower() not in ALLOWED_EXTENSIONS or
            posix.parts[:2] != ("data", "raw")):
        result["errors"].append("relative_path must be a file under data/raw with an allowed extension")
        return result
    if not isinstance(entry["hunting_seasons"], list) or not all(
            isinstance(s, str) and SEASON.fullmatch(s) for s in entry["hunting_seasons"]):
        result["errors"].append("hunting_seasons must contain YYYY/YYYY strings")
    if not isinstance(entry["sha256"], str) or not SHA256.fullmatch(entry["sha256"]):
        result["errors"].append("sha256 must be a lowercase 64-character digest")
    if not str(entry["area_id"]).isdigit():
        result["errors"].append("area_id must be a numeric portal identifier")
    if result["errors"]:
        return result
    file_path = root / rel
    if not file_path.is_file():
        result["status"] = "missing_file"
        result["errors"].append("declared export file is not present")
        return result
    actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if actual != entry["sha256"]:
        result["status"] = "hash_mismatch"
        result["errors"].append("file sha256 does not match declared digest")
        return result
    result["status"] = "integrity_verified"
    return result


def audit(root: Path, manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("exports")
    if not isinstance(entries, list):
        raise ValueError("manifest.exports must be an array")
    results = [check_entry(root, e) for e in entries]
    seen = set()
    for result in results:
        if result["source_id"] in seen:
            result["status"] = "invalid"
            result["errors"].append("duplicate source_id")
        seen.add(result["source_id"])
    snapshots = sorted((root / "data" / "daily_snapshots").glob("*/*.json"))
    declared = {(str(e.get("area_key")), str(e.get("area_id")), str(e.get("report_id")), s)
                for e in entries for s in e.get("hunting_seasons", []) if isinstance(s, str)}
    coverage = []
    for meta_path in snapshots:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        key = (str(meta.get("area_key", meta_path.parent.name)), str(meta.get("area_id", "")),
               str(meta.get("report_id", "")), "")
        # A declaration of the same area/report is a *candidate*, not verified
        # snapshot-cell equivalence. Snapshot metadata can omit season lists.
        candidates = [r["source_id"] for e, r in zip(entries, results)
                      if str(e.get("area_key")) == key[0] and
                      str(e.get("area_id")) == key[1] and
                      str(e.get("report_id")) == key[2] and
                      r["status"] == "integrity_verified"]
        coverage.append({"snapshot": meta_path.relative_to(root).as_posix(),
                         "integrity_verified_source_candidates": candidates,
                         "snapshot_values_verified": False})
    counts = {status: sum(r["status"] == status for r in results)
              for status in ("integrity_verified", "missing_file", "hash_mismatch", "invalid")}
    return {
        "manifest_entry_count": len(entries),
        "counts": counts,
        "sources": results,
        "snapshots": coverage,
        "snapshot_value_verification_status": "not_implemented",
        "note": "Matching area/report and SHA-256 does not verify workbook cells against snapshot values. Cell-level comparison requires an explicit field mapping and parser.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=Path("data/source_exports/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("data/quality/source_export_audit.json"))
    args = parser.parse_args()
    report = audit(args.root, args.root / args.manifest)
    dest = args.root / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Source export audit: {report['manifest_entry_count']} entries; {report['counts']}")
    return 1 if any(s["status"] != "integrity_verified" for s in report["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
