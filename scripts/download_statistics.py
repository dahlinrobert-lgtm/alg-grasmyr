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
        buttons: Array.from(document.querySelectorAll('button,input[type=button],input[type=submit]'))
          .map(b => ({tag:b.tagName.toLowerCase(), value:b.value || '', text:(b.innerText || '').trim(), disabled:!!b.disabled})),
      };
    }""")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("out/hornean-avskjutning"))
    parser.add_argument("--from-year", default="2010/2011")
    parser.add_argument("--to-year", default="2025/2026")
    parser.add_argument("--area-id", default=AREA_ID)
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
            await choose_by_label(page.locator("select").nth(2), AFO_NAME)
            await page.wait_for_timeout(900)

            # Set current boundaries unless the user changes this script/config.
            current_radio = page.locator('input[name="optTypeAFO"][value="G"]')
            if await current_radio.count():
                await current_radio.check()
                await page.wait_for_timeout(250)

            # Select the required hunting area by internal official ID after AFO load.
            area_select = page.locator("select").nth(5)
            area_options = await area_select.locator("option").evaluate_all(
                "(els) => els.map(o => ({label:o.text.trim(),value:o.value}))"
            )
            area_option = next((o for o in area_options if o["value"] == args.area_id), None)
            if area_option is None:
                raise RuntimeError(
                    f"Area ID {args.area_id} unavailable under {AFO_NAME}; "
                    f"loaded {len(area_options)} options"
                )
            await area_select.select_option(value=args.area_id)
            selected_area = {"area_id": args.area_id, "display_label": area_option["label"]}

            # Year selectors are the 4th and 5th native select controls.
            from_select = page.locator("select").nth(3)
            to_select = page.locator("select").nth(4)
            await choose_by_label(from_select, args.from_year)
            await choose_by_label(to_select, args.to_year)

            await page.wait_for_timeout(400)
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

            excel = page.locator('input[type="button"][value="Excel"]')
            if await excel.count() and not await excel.is_disabled():
                try:
                    async with page.expect_download(timeout=15000) as download_info:
                        await excel.click()
                    download = await download_info.value
                    suggested = download.suggested_filename or (
                        f"hornean_avskjutning_{args.from_year.replace('/', '-')}_"
                        f"{args.to_year.replace('/', '-')}.xlsx"
                    )
                    if not Path(suggested).suffix:
                        suggested += ".xlsx"
                    export_path = output_dir / suggested
                    await download.save_as(export_path)
                except Exception as exc:
                    errors.append("Excel export unavailable: " + str(exc)[:500])
            else:
                errors.append("Excel export button was missing or disabled")
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
        "afo": AFO_NAME,
        "selected_area": selected_area,
        "report_config": report_config,
        "hunting_year_from": args.from_year,
        "hunting_year_to": args.to_year,
        "boundary_mode": "current",
        "navigation_error": navigation_error,
        "errors": errors,
        "export_file": str(export_path.name) if export_path and export_path.exists() else None,
        "export_size_bytes": export_path.stat().st_size if export_path and export_path.exists() else None,
        "before_stats": before_stats,
        "after_stats": after_stats,
        "request_metadata": request_meta,
        "response_metadata": responses,
        "public_json_responses": public_json,
        "note": (
            "One official portal report configuration; raw workbook has not been normalized. "
            "The historical Gräsmyrs VVO is a separate identity and is not treated as the same area."
        )
    }
    report_path = output_dir / "download-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "export_file": report["export_file"],
        "export_size_bytes": report["export_size_bytes"],
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
