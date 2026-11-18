"""End-to-end synthetic Azure checkpoint/resume test for the national batch runner."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from run_national_batches import run_collection
from azure_checkpoint_pointer import read_latest
from azure_batch_checkpoint import validate_batch_package


def fake_area(candidate, area_dir, report_id, area_timeout):
    area_dir.mkdir(parents=True, exist_ok=True)
    return {
        "area_id": str(candidate["area_portal_id"]),
        "county": candidate["county"],
        "afo_name": candidate["afo_name"],
        "portal_selection_success": True,
        "data_available": True,
        "data_status": "synthetic_rows",
        "data_csv_rows": 1,
        "errors": [],
    }


def main() -> int:
    candidates = [
        {
            "area_portal_id": "SYNTHETIC-001",
            "county": "Synthetic county",
            "afo_name": "Synthetic AFO",
            "from_year": "2025/2026",
            "to_year": "2025/2026",
        },
        {
            "area_portal_id": "SYNTHETIC-002",
            "county": "Synthetic county",
            "afo_name": "Synthetic AFO",
            "from_year": "2025/2026",
            "to_year": "2025/2026",
        },
    ]
    collection_id = __import__("os").environ["COLLECTION_ID"]

    with tempfile.TemporaryDirectory(prefix="algdata-azure-runner-test-") as temp:
        root = Path(temp)
        first_package = root / "first"
        with patch("run_national_batches.run_area", side_effect=fake_area) as first_call:
            first = run_collection(
                candidates,
                first_package / "run",
                batch_size=2,
                limit=1,
                azure_collection_id=collection_id,
            )
        if first_call.call_count != 1 or first["completed_count"] != 1:
            raise RuntimeError("First synthetic invocation did not process exactly one area")

        second_package = root / "second"
        with patch("run_national_batches.run_area", side_effect=fake_area) as second_call:
            second = run_collection(
                candidates,
                second_package / "run",
                batch_size=2,
                limit=1,
                azure_collection_id=collection_id,
            )
        if second_call.call_count != 1:
            raise RuntimeError("Resume did not process exactly one remaining area")
        if second_call.call_args.args[0]["area_portal_id"] != "SYNTHETIC-002":
            raise RuntimeError("Resume did not skip the area already stored in Azure")
        if second["completed_count"] != 2 or second["status"] != "completed":
            raise RuntimeError("Resumed synthetic collection did not complete")

        latest = read_latest(collection_id)
        if latest is None or latest["pointer"]["generation"] != 3:
            raise RuntimeError("Expected initial checkpoint plus two per-area checkpoint generations")

        with tempfile.TemporaryDirectory(prefix="algdata-azure-runner-restore-") as restore_temp:
            restored = Path(restore_temp) / "package"
            from azure_checkpoint_store import restore_snapshot
            restore_snapshot(collection_id, latest["pointer"]["snapshot_id"], restored)
            summary = validate_batch_package(restored)
            if summary["completed_count"] != 2:
                raise RuntimeError("Final Azure snapshot did not restore both area results")

        print(json.dumps({
            "status": "passed",
            "collection_id": collection_id,
            "first_invocation_completed": first["completed_count"],
            "resumed_invocation_completed": second["completed_count"],
            "final_generation": latest["pointer"]["generation"],
            "final_completed_count": summary["completed_count"],
            "production_write": False,
            "portal_requests": 0,
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
