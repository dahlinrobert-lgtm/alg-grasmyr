# National ÄJO row-level snapshot comparison

## Purpose and boundaries

This audit compares the immutable national ÄFO snapshots at the underlying ÄJO-row level. It does not collect new source data, modify snapshots, update the dashboard, or create deletion/event records. The existing national collector remains the sole owner of source acquisition and snapshot storage.

Stable row identity is the numeric/string portal ID passed to `drillDownToAjoReport` in each row's `AfoName` field. The key is scoped by `afo_id` so IDs are never compared across different ÄFOs. Duplicate or missing IDs fail the audit rather than being guessed from names.

## Run

The manual GitHub Actions workflow **National ÄJO row-level snapshot comparison** defaults to:

- Earlier snapshot: `2026-11-21`
- Later snapshot: `2026-11-23`
- Expected current ÄFO coverage: 129

It runs regression tests, validates that both dates exist for every ÄFO, that season is 2026/2027, `boundary_mode=current`, and that `source_row_count` matches the preserved `raw_area_rows`. It then uploads a JSON report as an artifact. The workflow has read-only repository permissions.

Local invocation:

```bash
python -m unittest tests.test_national_ajo_snapshot_diff -v
python scripts/compare_national_ajo_snapshots.py --old-date 2026-11-21 --new-date 2026-11-23 --expected-afo-count 129 --out out/national-ajo-row-diff.json
```

## Classification rules

- New portal IDs in the later snapshot are reported as added rows.
- Portal IDs absent from the later snapshot are reported as `missing_in_later_snapshot_unconfirmed`, with `deletion_event=false`. They are not classified as deleted, cancelled, or completed.
- Shared IDs are compared field by field. This includes `ShotTotal`, `AssignedTotal`, `FinishedReporting`, names, area and other source attributes.
- `FinishedReporting` changes are separately indexed; reporting status is mutable and is not an event history.
- Missing files, partial coverage, wrong season/boundary mode, row-count mismatch, duplicate IDs or malformed rows fail the entire audit. No partial report is produced.

## Architecture fit

Reuse/extend the existing national snapshot architecture: `scripts/snapshot_national_afo.py`, `data/national_afo_snapshots/{afo_id}/{date}.json`, and the existing GitHub Actions test conventions. The new script is a read-only derived audit, not a second collector or a new source-of-truth store. The report is an ephemeral workflow artifact; the immutable source snapshots remain authoritative.

## Evidence status

The implementation and regression tests are introduced by PR. The actual 129-ÄFO row-level comparison is **not verified until the manual workflow completes successfully and its artifact has been inspected**. No customer feed, worker integration or alerts are enabled. Source rights for historical retention, processing, commercial use and customer display remain separate assessments.


## First verified national comparison: 2026-11-21 to 2026-11-23

The PR validation workflow executed the full comparison against all archived snapshot pairs on the branch. Run [45283539790](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/45283539790) completed successfully. Artifact `national-ajo-row-diff` (ID `14870128151`, SHA-256 `efa92935eecc4a3434ec5c8c63cdb179caeed755bf39b918534ea9ad98abdb35`) contains the complete row-level JSON report.

Verified results:

- 129/129 ÄFOs validated; both dates contain exactly 3,237 raw ÄJO rows.
- 2,841 rows are unchanged and 396 shared-ID rows have one or more changed source attributes.
- No new portal IDs and no IDs missing from the later snapshot.
- `ShotTotal` changed on 378 ÄJO rows. The national aggregate increased by 972 (56,715 to 57,687), consistent with the independently verified dashboard comparison.
- `FinishedReporting` changed on 42 rows: 41 transitions from `Nej` to `Ja`, and one from `Ja` to `Nej`.
- Other changed attributes include shot breakdowns, utilization percentages and `ShotAreal`; the artifact lists every changed field and old/new value per stable portal ID.
- The report explicitly confirms `source_snapshots_modified=false`.

The 42 status changes are row-level transitions; they are not equivalent to the earlier dashboard count of 10 ÄFOs with a changed number of finished-reporting areas. The two measures have different aggregation levels.

Interpretation: these are changes between cumulative season reports, not dated individual harvest events. No rows were added or missing in this pair, and no deletion inference is justified. The audit does not establish permission for commercial use, customer display or redistribution.
