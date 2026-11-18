"""Azure-backed synthetic compare-and-swap test for latest checkpoint pointers."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from azure.core.exceptions import ResourceModifiedError

# The workflow executes this file directly (python scripts/...). In that mode
# the scripts directory, rather than the repository root package, is on sys.path.
from azure_checkpoint_pointer import compare_and_swap_latest, read_latest
from azure_checkpoint_store import create_synthetic_fixture, publish_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-id", required=True)
    args = parser.parse_args()
    collection_id = args.collection_id

    with tempfile.TemporaryDirectory(prefix="algdata-pointer-smoke-") as temp:
        root = Path(temp)
        fixture1 = root / "snapshot-1"
        fixture2 = root / "snapshot-2"
        create_synthetic_fixture(fixture1)
        create_synthetic_fixture(fixture2)
        (fixture2 / "checkpoint.json").write_text(
            '{"schema_version":1,"kind":"synthetic_national_algdata_checkpoint",'
            '"production_write":false,"revision":2}\n',
            encoding="utf-8",
        )
        publish_snapshot(fixture1, collection_id, "snapshot-1")
        publish_snapshot(fixture2, collection_id, "snapshot-2")

    initial = read_latest(collection_id)
    if initial is not None:
        raise RuntimeError("Synthetic collection unexpectedly already has a latest pointer")

    first = compare_and_swap_latest(collection_id, "snapshot-1", None)
    observed = read_latest(collection_id)
    if observed is None or observed["pointer"]["generation"] != 1:
        raise RuntimeError("Initial pointer creation did not produce generation 1")

    second = compare_and_swap_latest(
        collection_id, "snapshot-2", observed["etag"]
    )
    if second["generation"] != 2:
        raise RuntimeError("Conditional pointer advance did not produce generation 2")

    stale_rejected = False
    try:
        # Deliberately reuse the ETag observed before the successful advance.
        compare_and_swap_latest(collection_id, "snapshot-1", observed["etag"])
    except ResourceModifiedError:
        stale_rejected = True

    final = read_latest(collection_id)
    if not stale_rejected:
        raise RuntimeError("Azure did not reject the stale ETag with HTTP 412")
    if (
        final is None
        or final["pointer"]["generation"] != 2
        or final["pointer"]["snapshot_id"] != "snapshot-2"
    ):
        raise RuntimeError("Stale update changed the latest pointer")

    print(json.dumps({
        "status": "passed",
        "collection_id": collection_id,
        "initial_generation": first["generation"],
        "advanced_generation": second["generation"],
        "stale_etag_rejected_by_azure": stale_rejected,
        "final_snapshot_id": final["pointer"]["snapshot_id"],
        "final_generation": final["pointer"]["generation"],
        "production_write": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
