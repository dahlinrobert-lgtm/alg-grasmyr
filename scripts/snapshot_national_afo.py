#!/usr/bin/env python3
"""Collect immutable current-season ÄFO totals from the public Älgdata portal."""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

PORTAL_URL = "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/"
BOUNDARY_URL = (
    "https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/"
    "Jaktadm/lst_jaktadm_visning/MapServer/1/query"
)
SEASON = "2026/2027"
REPORT_ID = "3"  # Avskjutning med mål — ÄFO
SOURCE = "Länsstyrelsernas Älgdata statistikportal"
EXPECTED_BOUNDARY_FEATURES = 129


def parse_current_number(raw: str) -> int | float | None:
    """Read the leading value in the portal's 'current (comparison)' cell."""
    value = (raw or "").strip()
    if not value or value == "-":
        return None
    value = value.split("(", 1)[0].strip().replace("\u00a0", "").replace(" ", "")
    value = value.replace(",", ".")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        raise ValueError(f"Unrecognized numeric cell: {raw!r}")
    number = float(value)
    return int(number) if number.is_integer() else number


def parse_portal_count(raw: Any) -> int:
    """Parse a non-negative count from one Älgdata area row; missing values are not zero."""
    value = str(raw if raw is not None else "").strip().replace("\u00a0", "").replace(" ", "")
    if not value or value == "-":
        raise ValueError(f"Missing count in source row: {raw!r}")
    value = value.replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.0+)?", value):
        raise ValueError(f"Unrecognized count in source row: {raw!r}")
    return int(float(value))


def parse_afo_api_data(data: dict[str, Any], html_tables: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum ShotTotal and AssignedTotal across every ÄJO row in the ÄFO report."""
    rows = data.get("TableDataFormatted")
    if not isinstance(rows, list) or not rows:
        raise ValueError("ÄFO report did not return TableDataFormatted area rows")

    def values(field: str) -> list[int]:
        parsed = []
        for index, row in enumerate(rows):
            cell = next((item for item in row if item.get("Name") == field), None)
            if cell is None:
                raise ValueError(f"Source row {index} is missing field {field}")
            parsed.append(parse_portal_count(cell.get("Text")))
        return parsed

    shot_values = values("ShotTotal")
    target_values = values("AssignedTotal")
    finished = sum(1 for row in rows if next((item.get("Text") for item in row if item.get("Name") == "FinishedReporting"), "") == "Ja")
    areas_with_kills = sum(1 for value in shot_values if value > 0)
    areas_with_targets = sum(1 for value in target_values if value > 0)

    candidates = [
        table.get("rows", [])
        for table in html_tables
        if table.get("rows") and any("Registreringsnummer" in str(cell) for cell in table["rows"][0])
    ]
    html_summary = None
    if candidates:
        html_rows = max(candidates, key=len)
        html_summary = next((row for row in html_rows if row and str(row[0]).strip().casefold().startswith("summa")), None)

    return {
        "source_row_count": len(rows),
        "finished_reporting_area_count": finished,
        "areas_with_kills_count": areas_with_kills,
        "areas_with_targets_count": areas_with_targets,
        "fallda_totalt": sum(shot_values),
        "fallda_totalt_raw": str(sum(shot_values)),
        "avskjutningsmal_totalt": sum(target_values),
        "avskjutningsmal_totalt_raw": str(sum(target_values)),
        "raw_header_one": data.get("HeaderOne", []),
        "raw_header_two": data.get("HeaderTwo", []),
        "raw_area_rows": rows,
        "raw_html_summa_row": html_summary,
    }

def load_active_afo_catalog(path: Path, season: str = SEASON) -> list[dict[str, str]]:
    """Keep only current-boundary AFOs with a selector valid for the requested season."""
    records: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            if row.get("boundary_mode") != "current":
                continue
            if row.get("from_year") != season or row.get("to_year") != season:
                continue
            county_code = f"{int(row['county_portal_value']):02d}"
            afo_number = f"{int(row['afo_portal_value']):03d}"
            afo_id = f"{county_code}-{afo_number}"
            record = {
                "afo_id": afo_id,
                "county": row["county"],
                "county_portal_value": row["county_portal_value"],
                "afo_name": row["afo_name"],
                "afo_portal_value": row["afo_portal_value"],
                "hunting_season": season,
            }
            previous = records.get(afo_id)
            if previous and previous != record:
                raise ValueError(f"Conflicting current AFO catalogue entries for {afo_id}")
            records[afo_id] = record
    if not records:
        raise ValueError(f"No current AFO catalogue entries for {season}")
    return [records[key] for key in sorted(records)]


async def selector_options(locator) -> list[dict[str, Any]]:
    return await locator.locator("option").evaluate_all(
        "(els) => els.map(o => ({label:(o.text||'').trim(),value:o.value,disabled:!!o.disabled}))"
    )


async def choose_report(select, report_id: str) -> dict[str, Any]:
    for option in await selector_options(select):
        try:
            config = json.loads(option["value"])
        except Exception:
            continue
        if str(config.get("Id")) == report_id:
            await select.select_option(value=option["value"])
            return config
    raise RuntimeError(f"Report ID {report_id} is not available")


async def select_exact(select, label: str) -> str:
    options = await selector_options(select)
    match = next((item for item in options if item["label"].casefold() == label.casefold()), None)
    if not match:
        raise RuntimeError(f"Portal option not found: {label}")
    await select.select_option(value=match["value"])
    return match["value"]


async def select_season(select, season: str) -> str:
    options = await selector_options(select)
    match = next((item for item in options if item["label"] == season and not item["disabled"]), None)
    if not match:
        raise RuntimeError(f"Season {season} is not enabled in the portal")
    await select.select_option(value=match["value"])
    return match["value"]


async def fetch_boundary_ids(request) -> set[str]:
    response = await request.get(
        BOUNDARY_URL,
        params={
            "where": "1=1",
            "outFields": "afo_id",
            "returnGeometry": "false",
            "f": "json",
        },
        timeout=45000,
    )
    if not response.ok:
        raise RuntimeError(f"ÄFO boundary query returned HTTP {response.status}")
    payload = await response.json()
    if "error" in payload:
        raise RuntimeError(f"ÄFO boundary query error: {payload['error']}")
    return {str(item["attributes"]["afo_id"]) for item in payload.get("features", [])}


async def prepare_portal_page(browser):
    """Create a clean portal page; used again after transient response/navigation failures."""
    page = await browser.new_page(viewport={"width": 1440, "height": 1000})
    page.set_default_timeout(20000)
    await page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=60000)
    selects = page.locator("select")
    await selects.nth(5).wait_for(state="attached", timeout=30000)
    config = await choose_report(selects.nth(0), REPORT_ID)
    if config.get("Name") != "ÄFO" or config.get("HuntingArea") != "0":
        await page.close()
        raise RuntimeError(f"Unexpected report configuration for ID 3: {config}")
    return page


async def collect_with_recovery(browser, page, item: dict[str, str], season: str, attempts: int = 3):
    """Retry one AFO on a fresh page after transient portal/browser response failures."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return await collect_one(page, item, season), page
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                break
            print(
                f"Retrying AFO {item['afo_id']} on a fresh browser page "
                f"after attempt {attempt}/{attempts}: {type(exc).__name__}: {exc}",
                flush=True,
            )
            try:
                await page.close()
            except Exception:
                pass
            page = await prepare_portal_page(browser)
    raise RuntimeError(
        f"AFO {item['afo_id']} failed after {attempts} attempts: "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error


async def collect_one(page, item: dict[str, str], season: str) -> dict[str, Any]:
    selects = page.locator("select")
    await select_exact(selects.nth(1), item["county"])
    await page.wait_for_timeout(300)
    await select_exact(selects.nth(2), item["afo_name"])
    await page.wait_for_timeout(450)

    current_boundary = page.locator('input[name="optTypeAFO"][value="G"]')
    if await current_boundary.count():
        await current_boundary.check()
        await page.wait_for_timeout(250)

    await select_season(selects.nth(3), season)
    await page.wait_for_timeout(200)
    await select_season(selects.nth(4), season)

    response_waiter = page.expect_response(
        lambda response: "/LoadData/GetData" in response.url
        and response.request.method == "POST",
        timeout=30000,
    )
    button = page.locator('input[type="button"][value="Visa statistik"]')
    if not await button.count():
        raise RuntimeError("Visa statistik button not found")
    async with response_waiter as response_info:
        await button.click()
    response = await response_info.value
    if not response.ok:
        raise RuntimeError(f"ÄFO report returned HTTP {response.status}")
    api_payload = await response.json()
    if api_payload.get("Error") or api_payload.get("Errors"):
        raise RuntimeError(f"Portal returned a report error: {api_payload.get('Error') or api_payload.get('Errors')}")
    await page.wait_for_timeout(350)
    tables = await page.evaluate("""() => Array.from(document.querySelectorAll('table')).map(t => ({
      rows:Array.from(t.querySelectorAll('tr')).slice(0,200).map(tr =>
        Array.from(tr.querySelectorAll('th,td')).map(c => (c.innerText||'').replace(/\\s+/g,' ').trim())
      )
    }))""")
    parsed = parse_afo_api_data(api_payload.get("Data") or {}, tables)
    return {
        **item,
        "snapshot_date": datetime.now(timezone.utc).date().isoformat(),
        "source": SOURCE,
        "source_url": PORTAL_URL,
        "report_id": REPORT_ID,
        "report_name": "ÄFO",
        "boundary_mode": "current",
        "hunting_season": season,
        "aggregation_level": "sum of ShotTotal and AssignedTotal across all registered ÄJO rows within the AFO",
        "data_status": "area_rows_available",
        "report_name_from_api": (api_payload.get("Data") or {}).get("ReportName"),
        **parsed,
    }


def archive_complete_batch(
    records: list[dict[str, Any]],
    output_root: Path,
    season: str,
    expected_ids: set[str],
    snapshot_date: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    observed_ids = {item["afo_id"] for item in records}
    if observed_ids != expected_ids:
        raise ValueError(
            f"Incomplete AFO batch: expected {len(expected_ids)}, got {len(observed_ids)}; "
            f"missing={sorted(expected_ids-observed_ids)[:10]}, extra={sorted(observed_ids-expected_ids)[:10]}"
        )

    snapshot_date = snapshot_date or datetime.now(timezone.utc).date().isoformat()
    try:
        datetime.strptime(snapshot_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid snapshot date: {snapshot_date!r}") from exc

    staged: list[tuple[Path, str]] = []
    for item in records:
        path = output_root / item["afo_id"] / f"{snapshot_date}.json"
        content = json.dumps(item, ensure_ascii=False, indent=2) + "\n"
        staged.append((path, content))

    dashboard_path = output_root.parent / "national_afo_dashboard.json"
    # A dashboard is a replaceable current view, unlike the immutable dated
    # snapshots. It may advance to a newer complete batch, but never regress.
    existing_dashboard = None
    if dashboard_path.exists():
        existing_dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
        existing_date = existing_dashboard.get("snapshot_date")
        if not isinstance(existing_date, str):
            raise ValueError("Existing national AFO dashboard has no valid snapshot_date")
        try:
            datetime.strptime(existing_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Existing dashboard has invalid snapshot_date: {existing_date!r}") from exc
        if snapshot_date < existing_date:
            raise ValueError(
                f"Refusing to replace newer dashboard dated {existing_date} with older batch {snapshot_date}"
            )

    # Validate every immutable snapshot and same-day dashboard before writing
    # any destination. A same-day retry is allowed only when byte-identical.
    for path, content in staged:
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"Refusing to overwrite changed same-day snapshot: {path}")

    dashboard = {
        "schema_version": 1,
        "snapshot_date": snapshot_date,
        "source": SOURCE,
        "source_url": PORTAL_URL,
        "report_id": REPORT_ID,
        "report_name": "ÄFO",
        "boundary_mode": "current",
        "hunting_season": season,
        "afo_count": len(records),
        "areas_with_data": sum(1 for item in records if item["fallda_totalt"] is not None),
        "interpretation": (
            "Fällda totals are calculated by summing ShotTotal across all TableDataFormatted ÄJO rows within each AFO; avskjutningsmål is the sum of AssignedTotal. "
            "The portal's visible Summa row uses a two-part display; its leading value is not the animal total. "
            "Full raw area rows and the HTML Summa row are preserved in each immutable AFO snapshot. "
            "Totals are cumulative reported values for the selected hunting season, not exact daily kill events."
        ),
        "areas": sorted(
            [
                {
                    "afo_id": item["afo_id"],
                    "county": item["county"],
                    "afo_name": item["afo_name"],
                    "hunting_season": season,
                    "fallda_totalt": item["fallda_totalt"],
                    "fallda_totalt_raw": item["fallda_totalt_raw"],
                    "avskjutningsmal_totalt": item["avskjutningsmal_totalt"],
                    "avskjutningsmal_totalt_raw": item["avskjutningsmal_totalt_raw"],
                    "data_status": item["data_status"],
                    "source_row_count": item["source_row_count"],
                    "finished_reporting_area_count": item["finished_reporting_area_count"],
                    "areas_with_kills_count": item["areas_with_kills_count"],
                    "areas_with_targets_count": item["areas_with_targets_count"],
                }
                for item in records
            ],
            key=lambda item: item["afo_id"],
        ),
    }
    dashboard_content = json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n"
    if existing_dashboard is not None and snapshot_date == existing_dashboard["snapshot_date"]:
        existing_content = json.dumps(existing_dashboard, ensure_ascii=False, indent=2) + "\n"
        if existing_content != dashboard_content:
            raise FileExistsError(
                f"Refusing to overwrite changed same-day dashboard: {dashboard_path}"
            )

    # All validation has passed. Preserve immutable snapshots and advance the
    # derived dashboard only when this complete batch is newer.
    for path, content in staged:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    if existing_dashboard is None or snapshot_date > existing_dashboard["snapshot_date"]:
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        dashboard_path.write_text(dashboard_content, encoding="utf-8")
    return dashboard_path, dashboard


async def run(args) -> dict[str, Any]:
    catalog = load_active_afo_catalog(args.catalog, args.season)
    if args.county:
        catalog = [item for item in catalog if item["county"].casefold() == args.county.casefold()]
    if args.afo_name:
        catalog = [item for item in catalog if item["afo_name"].casefold() == args.afo_name.casefold()]
    if args.limit:
        catalog = catalog[: args.limit]
    if not catalog:
        raise ValueError("No AFOs match the requested national catalogue selection")

    async with async_playwright() as playwright:
        request = await playwright.request.new_context(timeout=45000)
        boundary_ids = await fetch_boundary_ids(request)
        browser = await playwright.chromium.launch(headless=True)
        page = None
        try:
            page = await prepare_portal_page(browser)
            records = []
            errors = []
            for item in catalog:
                try:
                    record, page = await collect_with_recovery(
                        browser, page, item, args.season, attempts=3
                    )
                    records.append(record)
                except Exception as exc:
                    errors.append(
                        {"afo_id": item["afo_id"], "county": item["county"], "afo_name": item["afo_name"],
                         "error": type(exc).__name__ + ": " + str(exc)[:1000]}
                    )
            if errors:
                raise RuntimeError(
                    f"National AFO batch incomplete: {len(errors)} failures out of {len(catalog)}; "
                    + json.dumps(errors[:10], ensure_ascii=False)
                )
            expected_ids = {item["afo_id"] for item in catalog}
            # For a full national run, boundary IDs must match the current AFO catalogue.
            if not args.county and not args.afo_name and not args.limit and boundary_ids != expected_ids:
                raise RuntimeError(
                    f"Boundary/catalogue mismatch: boundary={len(boundary_ids)}, "
                    f"catalogue={len(expected_ids)}, missing={sorted(expected_ids-boundary_ids)}, "
                    f"extra={sorted(boundary_ids-expected_ids)}"
                )
            if args.county or args.afo_name or args.limit:
                return {"probe_count": len(records), "records": records, "boundary_count": len(boundary_ids)}
            dashboard_path, dashboard = archive_complete_batch(
                records, args.output_root, args.season, expected_ids
            )
            return {"dashboard_path": str(dashboard_path), "dashboard": dashboard}
        finally:
            if page is not None:
                try:
                    await page.close()
                except Exception:
                    pass
            await browser.close()
            await request.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/national_area_catalog/national_area_catalog.csv"))
    parser.add_argument("--output-root", type=Path, default=Path("data/national_afo_snapshots"))
    parser.add_argument("--season", default=SEASON)
    parser.add_argument("--county")
    parser.add_argument("--afo-name")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    result = asyncio.run(run(args))
    print(json.dumps(result, ensure_ascii=False, indent=2)[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
