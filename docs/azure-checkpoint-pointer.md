# Azure latest checkpoint pointer

## Purpose

Immutable snapshots are stored below:

`national-algdata/snapshots/<collection_id>/<snapshot_id>/`

This design adds a small mutable pointer at:

`national-algdata/collections/<collection_id>/latest.json`

The pointer identifies the latest accepted immutable snapshot. It is not itself a checkpoint and must never point to a snapshot until that snapshot's manifest and files have been uploaded and verified.

## Compare-and-swap protocol

1. Read `latest.json` and retain its Azure ETag. If it does not exist, retain the absent state (`expected_etag = null`).
2. Upload a new immutable snapshot using a unique snapshot ID.
3. Validate the target snapshot manifest's schema, collection ID, snapshot ID and `production_write=false`.
4. Attempt to update `latest.json`:
   - For an absent pointer, create with `overwrite=false`.
   - For an existing pointer, write with `IfNotModified` and the observed ETag.
5. If the ETag has changed, fail closed. The caller must read the new pointer, reconcile the newer checkpoint and retry deliberately. Never blindly retry with the stale manifest.
6. The pointer records a monotonically increasing generation and the previous snapshot ID for audit and recovery.

## Current implementation scope

`scripts/azure_checkpoint_pointer.py` provides:
- collection-scoped pointer naming and schema validation;
- reading the current pointer together with its ETag;
- create-only initialization;
- ETag-conditional pointer replacement;
- validation that the referenced immutable snapshot manifest exists and has matching provenance.

The Azure synthetic workflow runs the pointer schema unit tests without Azure access. The pointer update itself still requires an authenticated integration test.

## Safety boundaries / not yet enabled

- The national batch runner does not yet read or write this pointer.
- No automatic resume from Azure is enabled.
- No real portal data is uploaded by this feature branch.
- GitHub Actions artifact resume remains unchanged.
- Concurrent updates are rejected rather than merged automatically.
- Blob versioning and soft-delete recovery still require separate configuration verification and restore tests.

## Next integration gate

Before connecting the runner, add mocked tests for ETag conflict behavior and an Azure-backed synthetic test that creates an initial pointer, advances it conditionally, and proves that a stale ETag cannot replace the newer generation. Then integrate one checkpoint publication after each completed area, with immutable snapshot IDs and the frozen candidate-set identity preserved.
