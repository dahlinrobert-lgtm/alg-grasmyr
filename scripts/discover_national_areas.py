#!/usr/bin/env python3
"""Discover the public Älgdata area selector nationally.

This is a read-only catalogue crawl. It enumerates county, AFO and area
selector options for both current and historical boundary modes. It does not
assume that a portal area ID is a permanent geographic identity.
"""
from __future__ import annotations
import argparse, asyncio, csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/"

async def options(select):
    return await select.locator("option").evaluate_all(
        "(els) => els.map(o => ({label:o.text.trim(), value:o.value, disabled:o.disabled}))"
    )

async def choose_report(select, report_id):
    for o in await options(select):
        try:
            cfg = json.loads(o["value"])
        except Exception:
            continue
        if str(cfg.get("Id")) == str(report_id):
            await select.select_option(value=o["value"])
            return
    raise RuntimeError(f"Report Id={report_id} unavailable")

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/national_area_catalog"))
    ap.add_argument("--report-id", default="4")
    ap.add_argument("--county", action="append", help="Optional county label filter; repeatable")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows, errors, coverage = [], [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(20000)
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        selects = page.locator("select")
        await selects.nth(5).wait_for(state="attached", timeout=30000)
        await choose_report(selects.nth(0), args.report_id)
        counties = await options(selects.nth(1))
        counties = [c for c in counties if c["value"] not in ("", "-1") and c["label"]]
        if args.county:
            wanted = {x.casefold() for x in args.county}
            counties = [c for c in counties if c["label"].casefold() in wanted]
        for county in counties:
            try:
                await selects.nth(1).select_option(value=county["value"])
                await page.wait_for_timeout(500)
                for mode, radio_value in (("current", "G"), ("historical", "F")):
                    try:
                        radio = page.locator(f'input[name="optTypeAFO"][value="{radio_value}"]')
                        if await radio.count():
                            await radio.check()
                            await page.wait_for_timeout(300)
                        afos = [x for x in await options(selects.nth(2)) if x["value"] not in ("", "-1") and x["label"]]
                        for afo in afos:
                            try:
                                await selects.nth(2).select_option(value=afo["value"])
                                await page.wait_for_timeout(350)
                                starts = [x for x in await options(selects.nth(3)) if not x["disabled"] and x["value"]]
                                if not starts:
                                    raise RuntimeError("No enabled start-year options")
                                # Select earliest supported season to maximize catalogue coverage.
                                await selects.nth(3).select_option(value=starts[0]["value"])
                                await page.wait_for_timeout(250)
                                ends = [x for x in await options(selects.nth(4)) if not x["disabled"] and x["value"]]
                                if not ends:
                                    raise RuntimeError("No enabled end-year options")
                                await selects.nth(4).select_option(value=ends[-1]["value"])
                                await page.wait_for_timeout(450)
                                areas = [x for x in await options(selects.nth(5)) if x["value"] not in ("", "-1") and x["label"]]
                                coverage.append({"county":county["label"],"afo":afo["label"],"afo_id":afo["value"],"boundary_mode":mode,
                                                 "from_year":starts[0]["label"],"to_year":ends[-1]["label"],"area_count":len(areas)})
                                for area in areas:
                                    label = area["label"]
                                    match = re.match(r"^\s*([^\s]+)\s*[-–]\s*(.*?)\s*$", label)
                                    rows.append({
                                        "county":county["label"], "county_portal_value":county["value"],
                                        "afo_name":afo["label"], "afo_portal_value":afo["value"],
                                        "boundary_mode":mode, "from_year":starts[0]["label"], "to_year":ends[-1]["label"],
                                        "area_portal_id":area["value"], "area_display_id":match.group(1) if match else "",
                                        "area_name":match.group(2) if match else label,
                                        "area_label_raw":label, "catalogued_at_utc":datetime.now(timezone.utc).isoformat(),
                                    })
                            except Exception as exc:
                                errors.append({"county":county["label"],"afo":afo["label"],"mode":mode,"error":str(exc)[:500]})
                    except Exception as exc:
                        errors.append({"county":county["label"],"mode":mode,"error":str(exc)[:500]})
            except Exception as exc:
                errors.append({"county":county["label"],"error":str(exc)[:500]})
        await browser.close()
    # Keep duplicate area IDs across modes: they represent separate source observations.
    csv_path = args.out / "national_area_catalog.csv"
    fields = list(rows[0]) if rows else ["county","afo_name","boundary_mode","area_portal_id","area_name"]
    with csv_path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter=";"); w.writeheader(); w.writerows(rows)
    report = {"catalogued_at_utc":datetime.now(timezone.utc).isoformat(),"source_url":URL,
              "report_id":args.report_id,"area_observations":len(rows),"unique_portal_area_ids":len({r["area_portal_id"] for r in rows}),
              "counties_seen":len(counties),"county_afo_coverage":coverage,"errors":errors,
              "interpretation":"Selector catalogue only. IDs and labels are observations, not verified stable geographic identities; current/historical modes and year coverage must be retained."}
    (args.out/"national_area_catalog.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"csv":str(csv_path),"area_observations":len(rows),"unique_portal_area_ids":report["unique_portal_area_ids"],
                      "counties":len(counties),"afo_combinations":len(coverage),"errors":len(errors)},ensure_ascii=False,indent=2))
    if not rows: raise SystemExit("No area options discovered")

if __name__ == "__main__":
    asyncio.run(main())
