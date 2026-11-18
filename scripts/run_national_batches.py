"""Sequential, resumable runner for national Älgdata portal downloads.

The runner writes only to its selected output directory. It never updates production
snapshots or the website. Checkpoints are saved after every completed attempt.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    # Support both module execution and direct script execution from scripts/.
    from scripts.national_batching import (
        create_manifest,
        load_manifest,
        record_result,
        save_manifest_atomic,
    )
except ModuleNotFoundError:
    from national_batching import (
        create_manifest,
        load_manifest,
        record_result,
        save_manifest_atomic,
    )


def load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate file must contain a non-empty candidates array")
    return candidates


def run_area(
    candidate: dict[str, Any],
    area_dir: Path,
    report_id: str,
    area_timeout: int,
) -> dict[str, Any]:
    area_id = str(candidate["area_portal_id"])
    area_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, "scripts/download_statistics.py",
        "--out", str(area_dir),
        "--area-id", area_id,
        "--county", str(candidate["county"]),
        "--afo-name", str(candidate["afo_name"]),
        "--from-year", str(candidate["from_year"]),
        "--to-year", str(candidate["to_year"]),
        "--boundary-mode", "current",
        "--report-id", report_id,
    ]
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(
            command, text=True, capture_output=True, timeout=area_timeout, check=False
        )
        (area_dir / "runner-stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
        (area_dir / "runner-stderr.txt").write_text(completed.stderr or "", encoding="utf-8")
        report_path = area_dir / "download-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
        selected = report.get("selected_area") or {}
        portal_ok = (
            completed.returncode == 0
            and str(selected.get("area_id", "")) == area_id
            and report.get("hunting_year_from") == str(candidate["from_year"])
            and report.get("hunting_year_to_selected") == str(candidate["to_year"])
            and report.get("boundary_mode") == "current"
            and not report.get("errors")
        )
        rows = int(report.get("data_csv_rows", 0) or 0)
        return {
            "area_id": area_id,
            "county": candidate["county"],
            "afo_name": candidate["afo_name"],
            "attempt_started_at_utc": started,
            "attempt_finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "return_code": completed.returncode,
            "portal_selection_success": portal_ok,
            "data_available": rows > 0,
            "data_status": report.get("data_status", "missing_report"),
            "data_csv": report.get("data_csv"),
            "data_csv_rows": rows,
            "report_present": report_path.is_file(),
            "errors": report.get("errors", []) if report else ["download-report.json missing or invalid"],
        }
    except subprocess.TimeoutExpired as exc:
        (area_dir / "runner-timeout.txt").write_text(
            f"Timed out after {area_timeout} seconds\n", encoding="utf-8"
        )
        return {
            "area_id": area_id,
            "county": candidate["county"],
            "afo_name": candidate["afo_name"],
            "attempt_started_at_utc": started,
            "attempt_finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "return_code": None,
            "portal_selection_success": False,
            "data_available": False,
            "data_status": "timeout",
            "report_present": (area_dir / "download-report.json").is_file(),
            "errors": [f"download timed out after {area_timeout} seconds"],
        }


def run_collection(
    candidates: list[dict[str, Any]],
    output_dir: Path,
    batch_size: int = 100,
    report_id: str = "4",
    area_timeout: int = 240,
    limit: int | None = None,
    stop_after_area: int | None = None,
    retry_failed: bool = False,
    azure_collection_id: str | None = None,
) -> dict[str, Any]:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    azure_state: dict[str, Any] | None = None
    package_root = output_dir.parent
    if azure_collection_id:
        try:
            from scripts.azure_checkpoint_store import publish_snapshot, restore_snapshot
            from scripts.azure_checkpoint_pointer import read_latest, compare_and_swap_latest
            from scripts.azure_batch_checkpoint import validate_batch_package
        except ModuleNotFoundError:
            from azure_checkpoint_store import publish_snapshot, restore_snapshot
            from azure_checkpoint_pointer import read_latest, compare_and_swap_latest
            from azure_batch_checkpoint import validate_batch_package

        selected_path = package_root / "selected_candidates.json"
        if selected_path.exists():
            selected_payload = json.loads(selected_path.read_text(encoding="utf-8"))
            if selected_payload.get("candidates") != candidates:
                raise ValueError("Azure frozen candidate list differs from requested candidates")
        else:
            selected_path.write_text(
                json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        latest = read_latest(azure_collection_id)
        if latest is not None:
            # Azure is the authoritative resume source; refuse to overlay local state.
            with tempfile.TemporaryDirectory(prefix="algdata-azure-resume-") as temp:
                restored_root = Path(temp) / "package"
                restore_snapshot(
                    azure_collection_id,
                    latest["pointer"]["snapshot_id"],
                    restored_root,
                )
                validate_batch_package(restored_root)
                restored_selected = json.loads(
                    (restored_root / "selected_candidates.json").read_text(encoding="utf-8")
                )
                if restored_selected.get("candidates") != candidates:
                    raise ValueError("Azure checkpoint candidate identity differs; refusing resume")
                if output_dir.exists() and any(output_dir.iterdir()):
                    raise ValueError("Local run directory is not empty; refusing to overlay Azure checkpoint")
                if output_dir.exists():
                    output_dir.rmdir()
                shutil.copytree(restored_root / "run", output_dir)
            manifest = load_manifest(manifest_path)
            if manifest.get("candidates") != candidates:
                raise ValueError("Azure checkpoint manifest candidate identity differs")
            azure_state = {"etag": latest["etag"], "generation": latest["pointer"]["generation"]}
        else:
            azure_state = {"etag": None, "generation": 0}

    output_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
        if manifest.get("candidates") != candidates:
            raise ValueError("candidate list differs from checkpoint; use a new output directory")
    else:
        manifest = create_manifest(
            candidates, batch_size=batch_size,
            run_id=output_dir.name,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        save_manifest_atomic(manifest_path, manifest)

    if azure_collection_id and azure_state and azure_state["generation"] == 0:
        provenance_path = package_root / "checkpoint_provenance.json"
        provenance_path.write_text(json.dumps({
            "collection_id": azure_collection_id,
            "checkpoint_backend": "azure_blob",
            "production_write": False,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        validate_batch_package(package_root)
        snapshot_id = "checkpoint-" + uuid.uuid4().hex
        publish_snapshot(package_root, azure_collection_id, snapshot_id)
        pointer = compare_and_swap_latest(azure_collection_id, snapshot_id, None)
        azure_state = {"etag": pointer["etag"], "generation": pointer["generation"]}

    processed_this_run = 0
    for candidate in candidates:
        area_id = str(candidate["area_portal_id"])
        existing = manifest.get("results", {}).get(area_id)
        if existing and existing.get("status") in {"success", "no_data"}:
            continue
        if existing and existing.get("status") == "failed" and not retry_failed:
            continue
        if limit is not None and processed_this_run >= limit:
            break

        history = existing.get("attempt_history", []) if existing else []
        attempt_number = len(history) + 1
        area_dir = output_dir / "areas" / area_id / f"attempt-{attempt_number:04d}"
        result = run_area(candidate, area_dir, report_id, area_timeout)
        result["attempt_number"] = attempt_number
        record_result(manifest, result)
        manifest["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        save_manifest_atomic(manifest_path, manifest)
        if azure_collection_id and azure_state is not None:
            provenance_path = package_root / "checkpoint_provenance.json"
            provenance_path.write_text(json.dumps({
                "collection_id": azure_collection_id,
                "checkpoint_backend": "azure_blob",
                "production_write": False,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validate_batch_package(package_root)
            snapshot_id = "checkpoint-" + uuid.uuid4().hex
            publish_snapshot(package_root, azure_collection_id, snapshot_id)
            pointer = compare_and_swap_latest(
                azure_collection_id, snapshot_id, azure_state["etag"]
            )
            azure_state = {"etag": pointer["etag"], "generation": pointer["generation"]}
        processed_this_run += 1
        print(json.dumps({
            "area_id": area_id,
            "status": manifest["results"][area_id]["status"],
            "completed_count": manifest["completed_count"],
            "candidate_count": manifest["candidate_count"],
        }, ensure_ascii=False), flush=True)
        if stop_after_area is not None and processed_this_run >= stop_after_area:
            break

    manifest["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_manifest_atomic(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--report-id", default="4")
    parser.add_argument("--area-timeout", type=int, default=240)
    parser.add_argument(
        "--azure-collection-id",
        help="Enable durable Azure checkpoint/resume for this frozen collection ID",
    )
    parser.add_argument("--limit", type=int, help="Maximum new area attempts in this invocation")
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Retry areas whose latest checkpoint status is failed; success and no_data remain final",
    )
    args = parser.parse_args()
    if args.area_timeout < 1:
        parser.error("--area-timeout must be positive")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    manifest = run_collection(
        load_candidates(args.candidates), args.out, args.batch_size,
        args.report_id, args.area_timeout, args.limit,
        retry_failed=args.retry_failed,
        azure_collection_id=args.azure_collection_id,
    )
    print(json.dumps({
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "candidate_count": manifest["candidate_count"],
        "completed_count": manifest["completed_count"],
        "success_count": manifest["success_count"],
        "no_data_count": manifest["no_data_count"],
        "failure_count": manifest["failure_count"],
        "production_write": False,
    }, ensure_ascii=False, indent=2))
    return 0 if manifest["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
