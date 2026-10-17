#!/usr/bin/env python3
"""Inspect the public Älgdata statistics portal and capture network metadata.

No cookies, credentials, request bodies or response bodies are collected. The
report is intended to reveal the portal's public data endpoints and form
structure before source-specific automation is written.
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


async def inspect_dom(page) -> dict[str, Any]:
    return await page.evaluate("""() => {
      const labelFor = (el) => {
        const labels = el.labels ? Array.from(el.labels).map(x => x.innerText.trim()).filter(Boolean) : [];
        const parent = el.parentElement ? (el.parentElement.innerText || '').trim().slice(0, 180) : '';
        return labels.join(' / ') || el.getAttribute('aria-label') || el.getAttribute('title') || parent;
      };
      const controls = Array.from(document.querySelectorAll('select, input, button, [role="combobox"], [role="listbox"], [role="option"]'))
        .filter(el => {
          const type = (el.getAttribute('type') || '').toLowerCase();
          const name = (el.getAttribute('name') || '').toLowerCase();
          return !(el.tagName === 'INPUT' && (
            type === 'hidden' || /(token|password|secret|cookie|authorization)/.test(name)
          ));
        })
        .slice(0, 250).map(el => ({
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role') || '',
          type: el.getAttribute('type') || '',
          name: el.getAttribute('name') || '',
          label: labelFor(el),
          value: 'value' in el ? String(el.value || '') : '',
          text: (el.innerText || el.value || '').trim().slice(0, 180),
          placeholder: el.getAttribute('placeholder') || '',
          options: el.tagName === 'SELECT' ? Array.from(el.options).slice(0, 250).map(o => ({
            group: o.parentElement && o.parentElement.tagName === 'OPTGROUP' ? o.parentElement.label : '',
            label: o.text.trim(), value: o.value, selected: o.selected
          })) : []
        }));
      return {
        title: document.title,
        url: location.href,
        text: (document.body ? document.body.innerText : '').slice(0, 12000),
        controls,
        scripts: Array.from(document.scripts).map(s => s.src).filter(Boolean),
        links: Array.from(document.querySelectorAll('a[href]')).slice(0, 150).map(a => ({
          text: (a.innerText || '').trim().slice(0, 100), href: a.href
        }))
      };
    }""")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("portal-inspection.json"))
    parser.add_argument("--seconds", type=int, default=8, help="Seconds to let the SPA load (default: 8)")
    args = parser.parse_args()

    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    json_payloads: list[dict[str, Any]] = []
    response_tasks: set[asyncio.Task] = set()
    page_errors: list[str] = []
    console_errors: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("request", lambda req: requests.append({
            "url": req.url, "method": req.method, "resource_type": req.resource_type
        }))
        page.on("response", lambda res: responses.append({
            "url": res.url, "status": res.status,
            "content_type": res.headers.get("content-type", ""),
            "resource_type": res.request.resource_type
        }))

        async def capture_public_json(res) -> None:
            try:
                content_type = res.headers.get("content-type", "").lower()
                if res.request.resource_type not in ("xhr", "fetch"):
                    return
                if "application/json" not in content_type or "/Home/" not in res.url:
                    return
                body = await res.text()
                if len(body.encode("utf-8", errors="replace")) > 250_000:
                    json_payloads.append({
                        "url": res.url, "status": res.status,
                        "truncated": True, "body_chars": len(body)
                    })
                    return
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = body
                json_payloads.append({
                    "url": res.url, "status": res.status,
                    "truncated": False, "json": parsed
                })
            except Exception:
                # Some responses are not readable after navigation or cancellation.
                return

        def schedule_response_body(res) -> None:
            task = asyncio.create_task(capture_public_json(res))
            response_tasks.add(task)
            task.add_done_callback(response_tasks.discard)

        page.on("response", schedule_response_body)
        page.on("pageerror", lambda err: page_errors.append(str(err)[:500]))
        page.on("console", lambda msg: console_errors.append(msg.text[:500]) if msg.type == "error" else None)

        navigation_error = None
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as exc:
            navigation_error = str(exc)[:1000]
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await page.wait_for_timeout(max(0, min(args.seconds, 20)) * 1000)
        dom = await inspect_dom(page)

        # Select Västerbottens län, then visit its AFOs so the portal populates
        # the dependent hunting-area list. These are read-only public lookups.
        exploratory_actions: list[dict[str, str]] = []
        # The form's native selects are ordered: report, county, AFO, start year, end year, hunting area.
        selects = page.locator("select")
        county_select = selects.nth(1)
        try:
            county_value = await county_select.locator("option").filter(has_text="Västerbottens län").first.get_attribute("value")
            if county_value:
                await county_select.select_option(value=county_value)
                await page.wait_for_timeout(900)
                exploratory_actions.append({"target": "Västerbottens län", "action": "selected native option"})
        except Exception as exc:
            exploratory_actions.append({"target": "Västerbottens län", "action": "select failed: " + str(exc)[:120]})

        area_discovery: list[dict[str, Any]] = []
        afo_select = page.locator("select").nth(2)
        area_select = page.locator("select").nth(5)
        try:
            afo_options = await afo_select.locator("option").evaluate_all(
                "(els) => els.map(o => ({label: o.text.trim(), value: o.value}))"
            )
        except Exception:
            afo_options = []

        target_terms = (
            "Högland", "Hogland", "01-02-183", "01-02-098",
            "Hörneåns älgskötselområde", "Hörneåns ÄSO",
            "Gräsmyrs viltvårdsområde", "Gräsmyr",
            "Djupsjö", "Nyåker", "Tallbergslidens",
        )
        for afo in afo_options:
            if afo["value"] == "-1" or not afo["label"]:
                continue
            try:
                await afo_select.select_option(value=afo["value"])
                await page.wait_for_timeout(1000)
                opts = await area_select.locator("option").evaluate_all(
                    "(els) => els.map(o => ({label: o.text.trim(), value: o.value}))"
                )
                discovered = [o for o in opts if o["value"] != "-1" and o["label"]]
                matches = [
                    {"term": term, "options": [o for o in discovered if term.casefold() in o["label"].casefold()]}
                    for term in target_terms
                ]
                matches = [m for m in matches if m["options"]]
                area_discovery.append({
                    "afo_name": afo["label"],
                    "afo_id": afo["value"],
                    "areas_loaded": len(discovered),
                    "area_options": discovered,
                    "target_matches": matches,
                })
                # Intentionally inspect every AFO. Do not stop when Hörneåns or
                # Gräsmyr is found, since that previously prevented a full search.
            except Exception as exc:
                area_discovery.append({
                    "afo_name": afo["label"], "afo_id": afo["value"],
                    "error": str(exc)[:180],
                })
        final_dom = await inspect_dom(page)
        if response_tasks:
            await asyncio.gather(*list(response_tasks), return_exceptions=True)

        # Only public JSON payloads from the portal's own Home endpoints are retained.
        report = {
            "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_url": URL,
            "navigation_error": navigation_error,
            "initial_dom": dom,
            "exploratory_actions": exploratory_actions,
            "area_discovery": area_discovery,
            "final_dom": final_dom,
            "requests": requests,
            "responses": responses,
            "public_json_payloads": json_payloads,
            "page_errors": page_errors,
            "console_errors": console_errors[:100],
            "limitations": [
                "Only public page structure, request metadata and small JSON responses from public Home endpoints are recorded.",
                "Hidden inputs and fields with token/password/secret/cookie/authorization names are excluded.",
                "No cookies, request bodies, authentication data, or form submissions are collected.",
                "The portal may load statistics only after selecting a statistics type or filters."
            ]
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({
            "output": str(args.output),
            "title": final_dom.get("title"),
            "controls": len(final_dom.get("controls", [])),
            "requests": len(requests),
            "responses": len(responses),
            "exploratory_actions": exploratory_actions,
            "area_discovery": [
                {"afo_name": x.get("afo_name"), "afo_id": x.get("afo_id"),
                 "areas_loaded": x.get("areas_loaded"), "target_matches": x.get("target_matches", []),
                 "error": x.get("error")}
                for x in area_discovery
            ],
            "likely_data_requests": [
                x for x in responses
                if x.get("resource_type") in ("xhr", "fetch")
                or any(k in x.get("url", "").lower() for k in ("api", "query", "export", "statistik", "jaktomrade", "jaktområde"))
            ][:120],
            "navigation_error": navigation_error,
            "page_errors": page_errors[:15],
        }, ensure_ascii=False, indent=2))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
