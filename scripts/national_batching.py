"""Deterministic, resumable batch state for national Älgdata collection.

This module deliberately contains no portal calls and no production writes.
It provides the durable manifest primitives used by the later batch runner.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

AREA_STATES = {"success", "no_data", "failed"}
BATCH_STATES = {"pending", "running", "completed", "completed_with_errors"}


def plan_batches(candidates: list[dict[str, Any]], batch_size: int = 100) -> list[dict[str, Any]]:
    """Split candidates into deterministic, ordered batches without dropping IDs."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    ids = [str(row.get("area_portal_id", "")).strip() for row in candidates]
    if any(not area_id for area_id in ids):
        raise ValueError("every candidate must have an area_portal_id")
    if len(ids) != len(set(ids)):
        raise ValueError("candidate portal IDs must be unique")

    batches = []
    for offset in range(0, len(candidates), batch_size):
        number = len(batches) + 1
        chunk = candidates[offset : offset + batch_size]
        batches.append({
            "batch_id": f"batch-{number:04d}",
            "ordinal": number,
            "status": "pending",
            "candidate_ids": [str(row["area_portal_id"]) for row in chunk],
            "result_count": 0,
            "success_count": 0,
            "no_data_count": 0,
            "failure_count": 0,
        })
    return batches


def create_manifest(
    candidates: list[dict[str, Any]],
    batch_size: int = 100,
    run_id: str = "national",
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Create a versioned manifest retaining the exact candidate identity."""
    batches = plan_batches(candidates, batch_size)
    return {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": created_at_utc,
        "status": "pending",
        "production_write": False,
        "batch_size": batch_size,
        "candidate_count": len(candidates),
        "completed_count": 0,
        "success_count": 0,
        "no_data_count": 0,
        "failure_count": 0,
        "candidates": candidates,
        "batches": batches,
        "results": {},
    }


def classify_result(result: dict[str, Any]) -> str:
    """Keep a valid empty report distinct from a technical failure."""
    if not result.get("portal_selection_success"):
        return "failed"
    if result.get("data_available"):
        return "success"
    return "no_data"


def record_result(manifest: dict[str, Any], result: dict[str, Any]) -> None:
    """Record one result idempotently and refresh aggregate batch/run states."""
    area_id = str(result.get("area_id", "")).strip()
    if not area_id:
        raise ValueError("result must contain area_id")
    known_ids = {
        str(candidate.get("area_portal_id", ""))
        for candidate in manifest.get("candidates", [])
    }
    if area_id not in known_ids:
        raise ValueError(f"result area_id {area_id} is not in this run's candidate set")

    normalized = dict(result)
    normalized["status"] = classify_result(normalized)
    manifest.setdefault("results", {})[area_id] = normalized

    for batch in manifest.get("batches", []):
        ids = batch["candidate_ids"]
        batch_results = [manifest["results"][key] for key in ids if key in manifest["results"]]
        batch["result_count"] = len(batch_results)
        batch["success_count"] = sum(x["status"] == "success" for x in batch_results)
        batch["no_data_count"] = sum(x["status"] == "no_data" for x in batch_results)
        batch["failure_count"] = sum(x["status"] == "failed" for x in batch_results)
        if len(batch_results) == len(ids):
            batch["status"] = "completed_with_errors" if batch["failure_count"] else "completed"
        elif batch_results:
            batch["status"] = "running"
        else:
            batch["status"] = "pending"

    results = list(manifest["results"].values())
    manifest["completed_count"] = len(results)
    manifest["success_count"] = sum(x["status"] == "success" for x in results)
    manifest["no_data_count"] = sum(x["status"] == "no_data" for x in results)
    manifest["failure_count"] = sum(x["status"] == "failed" for x in results)
    if len(results) == manifest["candidate_count"]:
        manifest["status"] = "completed_with_errors" if manifest["failure_count"] else "completed"
    elif results:
        manifest["status"] = "running"
    else:
        manifest["status"] = "pending"


def next_pending_batch(manifest: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first batch not yet fully accounted for, preserving source order."""
    for batch in manifest.get("batches", []):
        if batch["status"] not in {"completed", "completed_with_errors"}:
            return batch
    return None


def public_status(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, safe status payload suitable for a website status panel."""
    return {
        "schema_version": manifest.get("schema_version", 1),
        "run_id": manifest.get("run_id"),
        "status": manifest.get("status", "pending"),
        "production_write": False,
        "candidate_count": manifest.get("candidate_count", 0),
        "completed_count": manifest.get("completed_count", 0),
        "success_count": manifest.get("success_count", 0),
        "no_data_count": manifest.get("no_data_count", 0),
        "failure_count": manifest.get("failure_count", 0),
        "batch_count": len(manifest.get("batches", [])),
        "completed_batch_count": sum(
            batch.get("status") in {"completed", "completed_with_errors"}
            for batch in manifest.get("batches", [])
        ),
        "updated_at_utc": manifest.get("updated_at_utc"),
    }


def save_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    """Write a complete JSON manifest atomically to avoid half-written checkpoints."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported national batch manifest schema_version")
    if manifest.get("production_write") is not False:
        raise ValueError("national batch manifest must keep production_write=false")
    return manifest
