"""Compare-and-swap pointer to the latest immutable national Älgdata snapshot.

Snapshot objects remain immutable. This module only changes a small JSON pointer,
using Azure Blob ETags to prevent stale or concurrent writers from silently
replacing a newer checkpoint.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from typing import Any

from scripts.azure_checkpoint_store import (
    CONTAINER,
    PREFIX_ROOT,
    _clients,
)


def _validate_collection_id(collection_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", collection_id):
        raise ValueError("collection_id contains unsupported characters")


def latest_pointer_blob_name(collection_id: str) -> str:
    _validate_collection_id(collection_id)
    return f"{PREFIX_ROOT}/collections/{collection_id}/latest.json"


def read_latest(collection_id: str) -> dict[str, Any] | None:
    """Return the current pointer and ETag, or None when no pointer exists."""
    from azure.core.exceptions import ResourceNotFoundError

    credential, service = _clients()
    try:
        container = service.get_container_client(CONTAINER)
        blob = container.get_blob_client(latest_pointer_blob_name(collection_id))
        try:
            props = blob.get_blob_properties()
        except ResourceNotFoundError:
            return None
        payload = json.loads(blob.download_blob().readall())
        _validate_pointer(payload, collection_id)
        return {"pointer": payload, "etag": props.etag}
    finally:
        service.close()
        credential.close()


def _validate_pointer(payload: dict[str, Any], collection_id: str) -> None:
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("kind") != "national_algdata_latest_checkpoint"
        or payload.get("collection_id") != collection_id
        or payload.get("production_write") is not False
        or not isinstance(payload.get("snapshot_id"), str)
        or not payload["snapshot_id"]
        or not isinstance(payload.get("generation"), int)
        or payload["generation"] < 1
    ):
        raise ValueError("Latest checkpoint pointer failed schema/provenance validation")


def compare_and_swap_latest(
    collection_id: str,
    snapshot_id: str,
    expected_etag: str | None,
) -> dict[str, Any]:
    """Move latest pointer only if its ETag still equals the caller's observation.

    expected_etag=None means create-only: it succeeds only if the pointer is absent.
    A stale ETag raises Azure's ResourceModifiedError/ResourceExistsError.
    """
    from azure.core import MatchConditions
    from azure.core.exceptions import ResourceNotFoundError

    _validate_collection_id(collection_id)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", snapshot_id):
        raise ValueError("snapshot_id contains unsupported characters")

    credential, service = _clients()
    try:
        container = service.get_container_client(CONTAINER)
        snapshot_manifest_name = (
            f"{PREFIX_ROOT}/snapshots/{collection_id}/{snapshot_id}/checkpoint-manifest.json"
        )
        snapshot_manifest = json.loads(
            container.get_blob_client(snapshot_manifest_name).download_blob().readall()
        )
        if (
            snapshot_manifest.get("schema_version") != 1
            or snapshot_manifest.get("kind") != "national_algdata_checkpoint_snapshot"
            or snapshot_manifest.get("collection_id") != collection_id
            or snapshot_manifest.get("snapshot_id") != snapshot_id
            or snapshot_manifest.get("production_write") is not False
        ):
            raise ValueError("Target snapshot manifest failed provenance validation")

        blob = container.get_blob_client(latest_pointer_blob_name(collection_id))
        current = None
        try:
            props = blob.get_blob_properties()
            current = json.loads(blob.download_blob().readall())
            _validate_pointer(current, collection_id)
        except ResourceNotFoundError:
            props = None

        if expected_etag is None:
            if props is not None:
                raise RuntimeError("Latest pointer already exists; create-only update refused")
            generation = 1
            previous_snapshot_id = None
            blob.upload_blob(
                json.dumps({
                    "schema_version": 1,
                    "kind": "national_algdata_latest_checkpoint",
                    "collection_id": collection_id,
                    "snapshot_id": snapshot_id,
                    "previous_snapshot_id": previous_snapshot_id,
                    "generation": generation,
                    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "production_write": False,
                }, sort_keys=True).encode("utf-8"),
                overwrite=False,
                content_type="application/json",
            )
        else:
            if props is None or props.etag != expected_etag:
                raise RuntimeError("Latest pointer ETag changed; refusing stale checkpoint update")
            generation = current["generation"] + 1
            payload = {
                "schema_version": 1,
                "kind": "national_algdata_latest_checkpoint",
                "collection_id": collection_id,
                "snapshot_id": snapshot_id,
                "previous_snapshot_id": current["snapshot_id"],
                "generation": generation,
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "production_write": False,
            }
            blob.upload_blob(
                json.dumps(payload, sort_keys=True).encode("utf-8"),
                overwrite=True,
                etag=expected_etag,
                match_condition=MatchConditions.IfNotModified,
                content_type="application/json",
            )

        new_props = blob.get_blob_properties()
        return {
            "status": "updated",
            "collection_id": collection_id,
            "snapshot_id": snapshot_id,
            "previous_snapshot_id": previous_snapshot_id if expected_etag is None else current["snapshot_id"],
            "generation": generation,
            "etag": new_props.etag,
            "production_write": False,
        }
    finally:
        service.close()
        credential.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    read = sub.add_parser("read-latest")
    read.add_argument("--collection-id", required=True)
    update = sub.add_parser("compare-and-swap-latest")
    update.add_argument("--collection-id", required=True)
    update.add_argument("--snapshot-id", required=True)
    update.add_argument("--expected-etag", default=None)
    args = parser.parse_args()

    if args.command == "read-latest":
        result = read_latest(args.collection_id)
    else:
        result = compare_and_swap_latest(
            args.collection_id, args.snapshot_id, args.expected_etag
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
