"""Package and validate a national Älgdata batch checkpoint for Azure snapshots.

This is opt-in tooling. It does not run portal downloads or publish website data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.azure_checkpoint_store import publish_snapshot, restore_snapshot
except ModuleNotFoundError:  # direct script execution from scripts/
    from azure_checkpoint_store import publish_snapshot, restore_snapshot


def validate_batch_package(root: Path) -> dict[str, Any]:
    root = root.resolve()
    selected_path = root / "selected_candidates.json"
    manifest_path = root / "run" / "manifest.json"
    provenance_path = root / "checkpoint_provenance.json"
    for path in (selected_path, manifest_path):
        if not path.is_file():
            raise ValueError(f"Required batch checkpoint file is missing: {path.relative_to(root)}")

    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = selected.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("selected_candidates.json must contain a non-empty candidates list")
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported batch manifest schema_version")
    if manifest.get("production_write") is not False:
        raise ValueError("Refusing batch package unless production_write is false")
    if manifest.get("candidates") != candidates:
        raise ValueError("Frozen candidate list differs from the batch manifest")
    if manifest.get("candidate_count") != len(candidates):
        raise ValueError("candidate_count does not match frozen candidates")
    results = manifest.get("results")
    if not isinstance(results, dict):
        raise ValueError("Batch manifest results must be an object")
    known_ids = {str(row.get("area_portal_id", "")) for row in candidates}
    if not set(results).issubset(known_ids):
        raise ValueError("Batch manifest contains results outside the frozen candidate set")
    if manifest.get("completed_count") != len(results):
        raise ValueError("completed_count does not match the result map")
    for area_id, result in results.items():
        if result.get("status") not in {"success", "no_data", "failed"}:
            raise ValueError(f"Unsupported result status for area {area_id}")
        area_dir = root / "run" / "areas" / area_id
        if not area_dir.is_dir():
            raise ValueError(f"Result directory missing for area {area_id}")
    if provenance_path.is_file():
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance.get("production_write") is not False:
            raise ValueError("Checkpoint provenance must keep production_write=false")
    return {
        "run_id": manifest.get("run_id"),
        "status": manifest.get("status"),
        "candidate_count": len(candidates),
        "completed_count": len(results),
        "success_count": manifest.get("success_count", 0),
        "no_data_count": manifest.get("no_data_count", 0),
        "failure_count": manifest.get("failure_count", 0),
        "production_write": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    upload = sub.add_parser("upload")
    upload.add_argument("--package-dir", type=Path, required=True)
    upload.add_argument("--collection-id", required=True)
    upload.add_argument("--snapshot-id", required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("--collection-id", required=True)
    restore.add_argument("--snapshot-id", required=True)
    restore.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "upload":
        summary = validate_batch_package(args.package_dir)
        stored = publish_snapshot(args.package_dir, args.collection_id, args.snapshot_id)
        result = {"package": summary, "azure": stored}
    else:
        stored = restore_snapshot(args.collection_id, args.snapshot_id, args.output_dir)
        summary = validate_batch_package(args.output_dir)
        result = {"package": summary, "azure": stored}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
