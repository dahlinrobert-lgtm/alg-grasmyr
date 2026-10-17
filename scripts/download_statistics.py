#!/usr/bin/env python3
"""Download an official Älgdata Excel report through the public portal UI.

This initial, conservative downloader handles one verified area and one report
configuration per run. It uses the same public selectors as the site, does not
bypass authentication, and stores a metadata report even when the Excel export
is unavailable. It does not normalize the returned data.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

URL = "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/"
COUNTY_NAME = "Västerbottens län"
AFO_NAME = "Sydöstra älgförvaltningsområdet"
AREA_ID = "724577"
AREA_DISPLAY_ID = "24-01-02-342-Ä"
AREA_NAME = "Hörneåns älgskötselområde"
REPORT_ID = "4"  # Avskjutning med mål — ÄJO


async def native_select_options(locator) -> list[dict[str, str]]:
    return await locator.locator("option").evaluate_all(
        "(els) => els.map(o => ({label: o.text.trim(), value: o.value}))"
    )


async def choose_by_label(select, label: str) -> str:
    options = await native_select_options(select)
    found = next((o for o in options if o["label"].casefold() == label.casefold()), None)
    if not found:
        raise RuntimeError(f"Option not found: {label}; first options={options[:12]}")
    await select.select_option(value=found["value"])
    return found["value"]


async def choose_report(select, report_id: str) -> dict[str, Any]:
    options = await native_select_options(select)
    for opt in options:
        try:
            config = json.loads(opt["value"])
        except (json.JSONDecodeError, TypeError):
            continue
        if str(config.get("Id")) == report_id:
            await select.select_option(value=opt["value"])
            config["option_label"] = opt["label"]
            return config
    raise RuntimeError(f"Report option Id={report_id} was not found")


async def choose_available_end_year(select, requested: str, start_year: str) -> str:
    options = await select.locator("option").evaluate_all(
        "(els) => els.map(o => ({label:o.text.trim(), value:o.value, disabled:o.disabled}))"
    )
    eligible = [o for o in options if o["value"] >= start_year and not o["disabled"]]
    if not eligible:
        raise RuntimeError(f"No enabled end-year options on or after {start_year}")
    target = next((o for o in eligible if o["value"] == requested), None)
    if target is None:
        # The portal disables future or unsupported seasons for some report types.
        # Use the latest enabled season not later than the requested year.
        earlier = [o for o in eligible if o["value"] <= requested]
        target = earlier[-1] if earlier else eligible[0]
    await select.select_option(value=target["value"])
    return target["value"]


async def capture_visible_state(page) -> dict[str, Any]:
    return await page.evaluate("""() => {
      const texts = (els) => Array.from(els).slice(0, 100).map(el =>
        (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 500)
      );
      const tables = Array.from(document.querySelectorAll('table')).slice(0, 20).map(t => ({
        caption: t.caption ? t.caption.innerText.trim() : '',
        rows: Array.from(t.querySelectorAll('tr')).slice(0, 60).map(tr =>
          Array.from(tr.querySelectorAll('th,td')).map(c =>
            (c.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 200)
          )
        )
      }));
      return {
        title: document.title,
        url: location.href,
        visible_text: (document.body ? document.body.innerText : '').slice(0, 20000),
        headings: texts(document.querySelectorAll('h1,h2,h3,h4')),
        tables,
        table_count: document.querySelectorAll('table').length,
        form_controls: Array.from(document.querySelectorAll('select')).map(s => ({
          id: s.id,
          label: s.getAttribute('aria-label') || s.getAttribute('aria-labelledby') || '',
          value: s.value,
          selected_text: s.selectedIndex >= 0 ? (s.options[s.selectedIndex].text || '').trim() : '',
          options_count: s.options.length
        })),
        radios: Array.from(document.querySelectorAll('input[type=radio]')).map(r => ({
          name:r.name, value:r.value, checked:!!r.checked, label:r.labels && r.labels.length ? r.labels[0].innerText.trim() : ''
        })),
        buttons: Array.from(document.querySelectorAll('button,input[type=button],input[type=submit]'))
          .map(b => ({tag:b.tagName.toLowerCase(), value:b.value || '', text:(b.innerText || '').trim(), disabled:!!b.disabled, visible:!!(b.offsetWidth || b.offsetHeight || b.getClientRects().length)})),
      };
    }""")



CSV_FIELDS = [
    "registreringsnummer", "jaktomradesnamn", "jaktsasong", "registrerad_areal_ha",
    "fallda_vuxna_totalt", "fallda_vuxna_handjur", "fallda_vuxna_hondjur",
    "fallda_kalvar_totalt", "fallda_kalvar_handjur", "fallda_kalvar_hondjur",
    "fallda_totalt", "fallda_otjanliga", "fallda_oregistrerad_mark",
    "fallda_per_1000_ha", "tjur_andel_pct", "kalv_andel_pct",
    "avskjutningsmal_vuxna", "avskjutningsmal_handjur", "avskjutningsmal_hondjur",
    "avskjutningsmal_kalv", "avskjutningsmal_totalt", "avskjutningsmal_per_1000_ha",
    "nyttjandegrad_vuxna_pct", "nyttjandegrad_kalv_pct", "nyttjandegrad_totalt_pct",
]


def save_statistics_table(state: dict[str, Any] | None, output_path: Path) -> int:
    """Save the rendered Älgdata 'Avskjutning med mål — ÄJO' table as CSV."""
    if not state:
        return 0
    candidates = []
    for table in state.get("tables", []):
        rows = table.get("rows", [])
        if rows and any("Registreringsnummer" in cell for cell in rows[0]):
            candidates.append(rows)
    # The UI may render a header-only clone before the actual sortable data table.
    target_table = max(candidates, key=len) if candidates else None
    if not target_table:
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_FIELDS)
        # The rendered DataTable has a two-row grouped header followed by a
        # summary row. The rest are one row per hunting season. Preserve source
        # display values, including percent signs and decimal commas.
        for row in target_table[2:]:
            if not row or not row[0] or row[0].strip().casefold().startswith("summa"):
                continue
            if len(row) < len(CSV_FIELDS):
                continue
            writer.writerow(row[:len(CSV_FIELDS)])
            written += 1
    return written

async def save_rendered_table(state: dict[str, Any] | None, output_path: Path) -> int:
    """Write the longest rendered result table verbatim as a semicolon CSV.

    This is a raw capture for report types whose columns have not yet been
    normalized. Grouped header rows and summary rows are deliberately retained.
    """
    if not state:
        return 0
    candidates = [
        table.get("rows", [])
        for table in state.get("tables", [])
        if table.get("rows")
    ]
    if not candidates:
        return 0
    rows = max(candidates, key=len)
    if len(rows) < 2:
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("out/hornean-avskjutning"))
    parser.add_argument("--from-year", default="2010/2011")
    parser.add_argument("--to-year", default="2025/2026")
    parser.add_argument("--area-id", default=AREA_ID)
    parser.add_argument("--afo-name", default=AFO_NAME)
    parser.add_argument("--boundary-mode", choices=("current", "historical"), default="current")
    parser.add_argument("--report-id", default=REPORT_ID)
    args = parser.parse_args()

    output_dir = args.out.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    responses: list[dict[str, Any]] = []
    request_meta: list[dict[str, Any]] = []
    public_json: list[dict[str, Any]] = []
    response_tasks: set[asyncio.Task] = set()
    navigation_error: str | None = None
    errors: list[str] = []
    report_config: dict[str, Any] | None = None
    selected_area: dict[str, Any] | None = None
    export_path: Path | None = None
    before_stats: dict[str, Any] | None = None
    after_stats: dict[str, Any] | None = None
    selected_year_to: str | None = None
    data_csv_path: Path | None = None
    data_csv_rows = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page.set_default_timeout(15000)
        page.on("request", lambda req: request_meta.append({
            "url": req.url, "method": req.method, "resource_type": req.resource_type
        }))
        page.on("response", lambda res: responses.append({
            "url": res.url, "status": res.status,
            "content_type": res.headers.get("content-type", ""),
            "resource_type": res.request.resource_type
        }))

        async def capture_json(res) -> None:
            try:
                if res.request.resource_type not in ("xhr", "fetch"):
                    return
                if "/Home/" not in res.url or "json" not in res.headers.get("content-type", "").lower():
                    return
                body = await res.text()
                if len(body.encode("utf-8", errors="replace")) > 500_000:
                    public_json.append({"url": res.url, "status": res.status, "truncated": True,
                                        "body_chars": len(body)})
                    return
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = body[:1000]
                public_json.append({"url": res.url, "status": res.status, "truncated": False, "json": parsed})
            except Exception:
                return

        def schedule_capture(res) -> None:
            task = asyncio.create_task(capture_json(res))
            response_tasks.add(task)
            task.add_done_callback(response_tasks.discard)

        page.on("response", schedule_capture)

        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            await page.locator("select").nth(5).wait_for(state="attached", timeout=30000)

            # Report configuration from the app's own report menu.
            report_config = await choose_report(page.locator("select").nth(0), args.report_id)

            # County and AFO trigger official dependent JSON lookups.
            await choose_by_label(page.locator("select").nth(1), COUNTY_NAME)
            await page.wait_for_timeout(500)
            await choose_by_label(page.locator("select").nth(2), args.afo_name)
            await page.wait_for_timeout(900)

            # Choose historical/current boundary interpretation before the dependent filters.
            boundary_value = "F" if args.boundary_mode == "historical" else "G"
            boundary_radio = page.locator(f'input[name="optTypeAFO"][value="{boundary_value}"]')
            if await boundary_radio.count():
                await boundary_radio.check()
                await page.wait_for_timeout(350)

            # Year selectors are the 4th and 5th native select controls. Choose them
            # before the hunting area because the portal refreshes dependent filters.

            from_select = page.locator("select").nth(3)
            to_select = page.locator("select").nth(4)
            await choose_by_label(from_select, args.from_year)
            selected_year_to = await choose_available_end_year(
                to_select, args.to_year, args.from_year
            )
            if selected_year_to != args.to_year:
                errors.append(
                    f"Requested end year {args.to_year} was disabled by the portal; "
                    f"using latest permitted year {selected_year_to}"
                )

            # Select area last: changing years can refresh the form and clear this field.
            await page.wait_for_timeout(350)
            area_select = page.locator("select").nth(5)
            area_options = await area_select.locator("option").evaluate_all(
                "(els) => els.map(o => ({label:o.text.trim(),value:o.value}))"
            )
            area_option = next((o for o in area_options if o["value"] == args.area_id), None)
            if area_option is None:
                raise RuntimeError(
                    f"Area ID {args.area_id} unavailable under {args.afo_name}; "
                    f"loaded {len(area_options)} options"
                )
            await area_select.select_option(value=args.area_id)
            selected_area = {"area_id": args.area_id, "display_label": area_option["label"]}
            await page.wait_for_timeout(500)

            before_stats = await capture_visible_state(page)
            show_button = page.locator('input[type="button"][value="Visa statistik"]')
            if not await show_button.count():
                raise RuntimeError('Could not find "Visa statistik" button')
            await show_button.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(1500)
            after_stats = await capture_visible_state(page)

            # The portal's export buttons remain hidden in some UI states. The
            # rendered result table is public, visible in the page and gives a
            # reproducible CSV copy without depending on the hidden Excel control.
            safe_from = args.from_year.replace("/", "-")
            safe_to = selected_year_to.replace("/", "-")
            report_slug = "avskjutning_mal_ajo" if args.report_id == "4" else f"report_{args.report_id}"
            data_csv_path = output_dir / (
                f"{report_slug}_{args.area_id}_{safe_from}_{safe_to}.csv"
            )
            if args.report_id == "4":
                data_csv_rows = save_statistics_table(after_stats, data_csv_path)
            else:
                data_csv_rows = save_rendered_table(after_stats, data_csv_path)
            if data_csv_rows == 0:
                errors.append("Could not locate data rows in the rendered statistics table")
        except Exception as exc:
            errors.append(type(exc).__name__ + ": " + str(exc)[:1000])
        finally:
            if response_tasks:
                await asyncio.gather(*list(response_tasks), return_exceptions=True)
            await browser.close()

    report = {
        "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": URL,
        "county": COUNTY_NAME,
        "afo": args.afo_name,
        "selected_area": selected_area,
        "report_config": report_config,
        "hunting_year_from": args.from_year,
        "hunting_year_to_requested": args.to_year,
        "hunting_year_to_selected": selected_year_to,
        "boundary_mode": args.boundary_mode,
        "navigation_error": navigation_error,
        "errors": errors,
        "data_csv": str(data_csv_path.name) if data_csv_path and data_csv_path.exists() else None,
        "data_csv_rows": data_csv_rows,
        "data_csv_size_bytes": data_csv_path.stat().st_size if data_csv_path and data_csv_path.exists() else None,
        "before_stats": before_stats,
        "after_stats": after_stats,
        "request_metadata": request_meta,
        "response_metadata": responses,
        "public_json_responses": public_json,
        "note": (
            "One official portal report configuration; CSV fields map the rendered grouped table, values preserved as displayed. "
            "The historical Gräsmyrs VVO is a separate identity and is not treated as the same area."
        )
    }
    report_path = output_dir / "download-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "data_csv": report["data_csv"],
        "data_csv_rows": report["data_csv_rows"],
        "data_csv_size_bytes": report["data_csv_size_bytes"],
        "selected_area": selected_area,
        "report_config": report_config,
        "errors": errors,
        "tables_after_stats": after_stats.get("table_count") if after_stats else None,
        "response_endpoints": [
            {"url": r["url"], "status": r["status"], "content_type": r["content_type"]}
            for r in responses if "/Home/" in r["url"]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
