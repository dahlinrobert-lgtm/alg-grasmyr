# National ÄFO avskjutning snapshots

## Scope

Collect cumulative current-season ÄFO totals from Länsstyrelsernas Älgdata report ID 3 (ÄFO, current boundaries) for hunting season 2026/2027. The national selector catalogue is filtered to current-boundary entries active for the requested season. The full national run must match the current JaktAdm boundary IDs exactly.

## Aggregation rule

The portal's visible HTML `Summa` row uses a two-part display, for example `42 (2 408)`. The leading number is not the animal total. The authoritative aggregate is calculated by summing `ShotTotal` and `AssignedTotal` across every `TableDataFormatted` ÄJO row within the AFO. Preserve all raw ÄJO rows and the raw HTML Summa row in each immutable snapshot for auditability.

Missing values are errors, not zero. Explicit source zero values remain zero. A full national batch fails closed if any AFO fails, if the selector catalogue and current boundary IDs differ, or if any required source count cannot be parsed.

## Historical storage

Each snapshot is stored under `data/national_afo_snapshots/{afo_id}/{snapshot_date}.json`. Existing same-day snapshots are immutable: identical retries are idempotent; changed content for an existing date is refused. The dashboard is a derived current view at `data/national_afo_dashboard.json`. The workflow runs daily at 04:35 UTC and can also be started manually. The scheduled workflow commits only after the complete batch and all tests succeed.

## Verified baseline evidence

The corrected full batch from 2026-11-16 (workflow run 43952789564) returned 129/129 active AFOs and 129 snapshot files. Independent validation of its artifact confirmed:
- 3,237 raw ÄJO rows across the 129 AFOs.
- For every AFO, `fallda_totalt` equals the sum of raw `ShotTotal` values.
- For every AFO, `avskjutningsmal_totalt` equals the sum of raw `AssignedTotal` values.
- Both aggregates also match the parenthetical totals in the preserved HTML `Summa` row.
- Zero aggregate mismatches across all 129 AFOs.
- Explicit zeros are retained as zero; all 129 AFOs have `area_rows_available`.

The earlier 129/129 batch that parsed the leading Summa values is invalid and must not be used. The corrected artifact is evidence for the parser and baseline, but a fresh current-date snapshot should be run from `main` after this PR is merged.

## Publication and interpretation

These are cumulative reported totals for a selected hunting season, not individual kill events, exact kill dates, or kill locations. Do not conflate national ÄFO totals with regional ÄJO change snapshots. Never convert missing or unavailable data to zero.


## Transient portal response recovery — 2026-11-21

The first fresh run from current `main` (workflow run #9) passed all four parser/archive regression tests and retrieved 128 of 129 AFOs. A single AFO (25-004, ÄFO 4, Norrbottens län) failed because Playwright could not retrieve a response body after the page navigated away. The batch failed closed: no dashboard or snapshot archive was written.

The collector is being updated to retry each failed AFO up to three times, recreating and reinitializing a clean portal page between attempts. The complete national batch still must succeed before any snapshot or dashboard is written. This recovery does not turn missing values into zero and does not weaken exact 129-AFO validation.
