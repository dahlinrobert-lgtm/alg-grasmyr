# National Älgdata – checkpoint continuation

The manual workflow `National Älgdata batch runner smoke test` supports continuing a smoke collection across separate GitHub Actions runs.

## Starting a collection

1. Open the [workflow](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/workflows/national-algdata-batch-smoke.yml).
2. Run it with `resume_run_id` empty.
3. Set `limit` to the number of new area attempts for this invocation (maximum 20).
4. The workflow freezes a geographically balanced sample of up to 20 areas and stores the exact candidate list with the checkpoint.

## Continuing a collection

1. Open the previous successful workflow run and copy its numeric run ID.
2. Start the workflow again and enter that value in `resume_run_id`.
3. The workflow downloads the artifact from that exact run, verifies its provenance, frozen candidate list, manifest identity and `production_write=false`, then resumes the existing output directory.
4. The `limit` input controls the maximum number of additional area attempts in this invocation. Completed `success`, `no_data` and `failed` results are not attempted again.

Each run uploads a new artifact with the updated checkpoint. Use the latest successful run ID for the next continuation.

## Boundaries and retention

- This mechanism is an interim cross-run checkpoint for the bounded smoke workflow, not yet the full national production collector.
- GitHub Actions artifacts are retained for 30 days by this workflow. Continue before the source artifact expires.
- The workflow still does not write production data or publish website data.
- The candidate list is frozen on the first run; continuation never silently refreshes or replaces it.
- A failed or incomplete source run may still have an artifact, but continuation is accepted only if the checkpoint and provenance validations pass.
- Artifacts are not a permanent archive. A later production design should use durable storage with explicit retention, integrity checks, and backup/restore procedures.

## Expected manifest states

Each area remains classified as `success`, `no_data` or `failed`. A missing report or technical failure must never be interpreted as zero harvest. The manifest remains the authoritative checkpoint for this smoke collection.
