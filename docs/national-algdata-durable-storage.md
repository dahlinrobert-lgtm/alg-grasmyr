# National Älgdata – durable checkpoint storage design

## Decision

Use Azure Blob Storage as the durable object store for national Älgdata collection checkpoints and raw portal outputs. GitHub Actions artifacts remain short-lived diagnostics and convenient hand-off packages; they are not the authoritative archive.

The Azure identity, dedicated container, and synthetic upload/restore path have now been configured and tested. The national batch runner itself still uses GitHub Actions artifacts; Azure is not yet its authoritative checkpoint backend.

## Storage layout

Use a private Blob container dedicated to this collection, for example `national-algdata`.

Recommended object layout:

```text
national-algdata/
  runs/
    <collection_id>/
      candidate-set/
        candidates.json
        candidate-set-manifest.json
      areas/
        <area_portal_id>/
          <attempt_id>/
            download-report.json
            export.csv
            runner-stdout.txt
            runner-stderr.txt
            checksums.json
      checkpoints/
        manifest.json
        checkpoint.json
      run-manifest.json
```

- `collection_id` is a stable identifier for one frozen candidate set and collection period, not a GitHub Actions run ID.
- Candidate-set files are written once and treated as immutable. A continuation must verify their SHA-256 digest before processing.
- Each area attempt gets a unique `attempt_id`; never overwrite an earlier raw attempt.
- The checkpoint manifest references the accepted attempt for each area and records status, timestamps, source report metadata and hashes.
- Upload raw files first. Publish the new checkpoint manifest last, using an ETag/conditional write so readers never see a manifest that points to incomplete files.
- A technical failure remains `failed`; a valid empty portal report remains `no_data`. Neither is converted into zero harvest.

## Authentication

Prefer GitHub Actions OpenID Connect (OIDC) over a storage account key or connection string.

Required Azure setup:
1. Create or select an Azure Storage account with Blob Storage enabled.
2. Create a private container named `national-algdata`.
3. Register an Entra ID application or use an existing workload identity.
4. Add a federated credential for this repository and the protected GitHub branch/environment used by the collection workflow.
5. Assign the identity the least-privilege `Storage Blob Data Contributor` role scoped to the dedicated container (or storage account if container scope is not available in the chosen setup).
6. Enable Blob versioning and soft delete for blobs; configure an appropriate retention policy and review storage lifecycle rules before enabling automatic deletion.

GitHub repository configuration (prefer Actions variables for non-secret identifiers):
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_STORAGE_ACCOUNT`
- `AZURE_STORAGE_CONTAINER` (default `national-algdata`)

The workflow needs `permissions: id-token: write` and `contents: read`, followed by `azure/login@v2`. Do not add client secrets, account keys, SAS tokens, or connection strings to workflow files, commits, logs, or artifacts.

## Workflow behavior

1. A new collection discovers the catalogue once, selects the complete candidate set, and freezes it with a SHA-256 digest.
2. Before any portal request, the runner downloads the candidate set and checkpoint from Blob Storage and validates their schema, digest, collection ID and `production_write=false`.
3. It processes areas sequentially and writes each attempt to a unique object prefix.
4. It verifies uploaded object hashes and sizes.
5. It updates the checkpoint manifest conditionally after each area. A concurrent or stale writer must fail rather than overwrite newer state.
6. A resumed run reads the latest checkpoint from Blob Storage; it does not depend on a previous GitHub Actions run ID or an unexpired Actions artifact.
7. At the end, it writes a run summary and optionally uploads a small diagnostic artifact to GitHub Actions.

## Integrity and recovery

- SHA-256 for every raw output and frozen candidate file.
- ETag conditional writes for checkpoint updates.
- Blob versioning and soft delete enabled.
- Periodic inventory/export of blob names, sizes, hashes and versions.
- A documented restore test that reconstructs a checkpoint in a clean runner and validates every referenced object.
- No automatic deletion of source exports until a tested retention policy and backup procedure are approved.
- Keep portal error details and original response/report files for auditability, subject to source terms and data-retention requirements.

## Rollout gates

Do not switch the national collector to Azure until all gates pass:

1. Azure identity and private container are configured by the repository owner.
2. A manual test uploads a synthetic checkpoint and small synthetic files, then downloads them in a separate Actions run.
3. Hashes, ETags, conditional updates, version restore and soft-delete recovery are tested.
4. A small real-data smoke run writes only to the isolated Azure prefix and can resume in another run.
5. The storage inventory and operating instructions are updated.
6. Only then consider a full national collection. Website publishing and existing regional daily workflows remain out of scope.

## Current status

The GitHub-artifact resume mechanism was proven by smoke runs #5 and #6. It remains the interim checkpoint transport, with 30-day artifact retention.

A first isolated Azure implementation is merged on `main`:
- `scripts/azure_checkpoint_store.py` publishes immutable snapshot files and uploads the checkpoint manifest last.
- Every file is accompanied by SHA-256 and byte-count metadata; an existing object is accepted only when its metadata matches.
- Restore validates manifest provenance, safe relative paths, SHA-256 and byte counts.
- `.github/workflows/national-algdata-azure-smoke.yml` is manual and synthetic-only. It supports upload and restore in separate workflow runs.
- The workflow targets the existing `stskogkolldata` account and a dedicated `national-algdata` container.

The separate-run synthetic upload and restore tests have both passed in GitHub Actions (upload run `44402880891`, restore run `44403461037`). OIDC and Blob access to `stskogkolldata/national-algdata` are verified. The national runner still uses GitHub Actions artifacts; do not treat Azure as authoritative until batch-package validation, conditional checkpoint updates, recovery/versioning, and a bounded real-data resume test have passed.

A follow-on opt-in batch-package layer is being developed on branch `feature/azure-batch-checkpoint-package`. It validates the frozen candidate set, manifest, result IDs/statuses, and `production_write=false` before upload and after restore. It does not change the portal runner or website publishing.


## Azure batch-runner integration (opt-in)

The national runner now has an opt-in Azure backend through
`scripts/run_national_batches.py --azure-collection-id <stable-id>`.

When enabled, the runner:
- freezes the candidate list in the checkpoint package and refuses a different candidate set on resume;
- restores and validates the latest Azure snapshot before processing;
- creates an initial checkpoint before the first area request;
- publishes a new immutable package snapshot after every processed area;
- advances the latest pointer with the ETag observed for the prior generation;
- fails closed on stale/concurrent pointer updates;
- keeps `production_write=false` and does not publish website data.

Without `--azure-collection-id`, the existing local/GitHub-artifact behavior is unchanged.

A separate manual workflow, `National Älgdata Azure batch runner synthetic integration`,
runs two synthetic invocations against Azure and verifies resume and final restore. It
does not call the Älgdata portal. Do not enable Azure for a real national portal run
until this synthetic workflow passes and a bounded real-data pilot has been reviewed.
