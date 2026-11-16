#!/usr/bin/env python3
"""Read-only probe of ÄFO-level harvest statistics and national ÄFO boundary services."""
from __future__ import annotations
import argparse, asyncio, csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

PORTAL = "https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/"
LST_WMS = "https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/services/Jaktadm/lst_jaktadm_visning/MapServer/WMSServer?service=WMS&request=GetCapabilities"
SKS_LAYER = "https://geodpags.skogsstyrelsen.se/arcgis/rest/services/Geodataportal/GeodataportalVisaAbinrapport/MapServer/4"
SKS_COUNT = SKS_LAYER + "/query?where=1%3D1&returnCountOnly=true&f=json"

async def options(select):
    return await select.locator("option").evaluate_all(
        "(els) => els.map(o => ({label:(o.text||'').trim(), value:o.value, disabled:!!o.disabled}))"
    )

async def choose_report(select, report_id):
    for item in await options(select):
        try:
            cfg=json.loads(item["value"])
        except Exception:
            continue
        if str(cfg.get("Id")) == report_id:
            await select.select_option(value=item["value"])
            return {"id":report_id,"label":item["label"],"config":cfg}
    raise RuntimeError("Report Id not found: "+report_id)

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--county",default="Västerbottens län")
    ap.add_argument("--afo",default="Sydöstra älgförvaltningsområdet")
    ap.add_argument("--from-year",default="2026/2027")
    ap.add_argument("--to-year",default="2026/2027")
    ap.add_argument("--report-id",default="22")
    ap.add_argument("--out",type=Path,default=Path("out/afo-source-probe"))
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    result={"probed_at_utc":datetime.now(timezone.utc).isoformat(),"inputs":{k:str(v) for k,v in vars(args).items()},"sources":{}}

    async with async_playwright() as p:
        request=await p.request.new_context(timeout=45000)
        for key,url in (
            ("lansstyrelsen_wms",LST_WMS),
            ("lansstyrelsen_rest_service_root","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer?f=pjson"),
            ("lansstyrelsen_rest_layer_0","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/0?f=pjson"),
            ("lansstyrelsen_rest_layer_1","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/1?f=pjson"),
            ("lansstyrelsen_rest_layer_2","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/2?f=pjson"),
            ("lansstyrelsen_rest_query_2","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/2/query?where=1%3D1&returnCountOnly=true&f=json"),
            ("lansstyrelsen_afo_count","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/1/query?where=1%3D1&returnCountOnly=true&f=json"),
            ("lansstyrelsen_afo_features","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/1/query?where=1%3D1&outFields=OBJECTID,afo_id,namn_afo,forvaltare&returnGeometry=true&outSR=4326&f=geojson"),
            ("lansstyrelsen_metadata","https://ext-geodatakatalog.lansstyrelsen.se/GeodataKatalogen/GetMetaDataById?id=6d4c42de-2b43-4b72-98ec-856d8adfaf29"),
            ("skogsstyrelsen_layer_count",SKS_COUNT),
            ("skogsstyrelsen_layer_attributes",SKS_LAYER+"/query?where=1%3D1&outFields=AFONr_SKS,AFONamn_SKS,LanNamn,AFONr,AFONamn,InvAr&returnGeometry=false&f=json")
        ):
            try:
                response=await request.get(url)
                body=await response.text()
                if key=="lansstyrelsen_wms":
                    (args.out/"lansstyrelsen-wms-capabilities.xml").write_text(body,encoding="utf-8")
                entry={"status":response.status,"content_type":response.headers.get("content-type",""),"body_chars":len(body)}
                if key=="lansstyrelsen_wms":
                    entry["is_wms_capabilities"]="WMS_Capabilities" in body or "WMT_MS_Capabilities" in body
                    entry["layer_names"]=re.findall(r"<(?:\w+:)?Name>([^<]+)</(?:\w+:)?Name>",body)[:100]
                    entry["service_title"]=re.findall(r"<(?:\w+:)?Title>([^<]+)</(?:\w+:)?Title>",body)[:5]
                else:
                    try: entry["json"]=json.loads(body)
                    except Exception: entry["body_excerpt"]=body[:1200]
                result["sources"][key]=entry
            except Exception as exc:
                result["sources"][key]={"error":type(exc).__name__+": "+str(exc)[:1000]}

        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page(viewport={"width":1440,"height":1000})
        try:
            await page.goto("https://dahlinrobert-lgtm.github.io/Skog/",wait_until="domcontentloaded",timeout=60000)
            cors_result=await page.evaluate("""async (url) => {
              try { const r=await fetch(url); const j=await r.json(); return {ok:r.ok,status:r.status,type:j.type,features:j.features?.length}; }
              catch(e) { return {ok:false,error:String(e)}; }
            }""","https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer/1/query?where=1%3D1&outFields=OBJECTID,afo_id,namn_afo,forvaltare&returnGeometry=true&outSR=4326&f=geojson")
            result["sources"]["browser_cors_from_github_pages"]=cors_result
        except Exception as exc:
            result["sources"]["browser_cors_from_github_pages"]={"ok":False,"error":type(exc).__name__+": "+str(exc)[:1000]}
        page.set_default_timeout(20000)
        captured=[]
        captured_requests=[]
        page.on("request",lambda req: captured_requests.append({"url":req.url,"method":req.method,"post_data":req.post_data}) if "LoadData/GetData" in req.url else None)
        async def capture_response(response):
            try:
                if response.request.resource_type not in ("xhr","fetch"):
                    return
                entry={"url":response.url,"status":response.status,"content_type":response.headers.get("content-type","")}
                if "json" in entry["content_type"].lower():
                    body=await response.text()
                    entry["body_chars"]=len(body)
                    entry["body"]=body[:500000]
                captured.append(entry)
            except Exception:
                pass
        page.on("response",capture_response)
        try:
            await page.goto(PORTAL,wait_until="domcontentloaded",timeout=60000)
            selects=page.locator("select")
            await selects.nth(5).wait_for(state="attached",timeout=30000)
            report_options=await options(selects.nth(0))
            report_catalog=[]
            for opt in report_options:
                try:
                    cfg=json.loads(opt["value"])
                    report_catalog.append({"label":opt["label"],"id":str(cfg.get("Id")),"name":cfg.get("Name"),"report_level":cfg.get("ReportLevel"),"county":cfg.get("County"),"elk_management":cfg.get("ElkManagement"),"hunting_area":cfg.get("HuntingArea")})
                except Exception:
                    continue
            report=await choose_report(selects.nth(0),args.report_id)
            if report["config"].get("County") == "1":
                await selects.nth(1).select_option(label=args.county)
                await page.wait_for_timeout(600)
            if report["config"].get("ElkManagement") == "1":
                await selects.nth(2).select_option(label=args.afo)
                await page.wait_for_timeout(800)
            radio=page.locator('input[name="optTypeAFO"][value="G"]')
            if await radio.count() and report["config"].get("ElkManagement") == "1":
                await radio.check()
                await page.wait_for_timeout(400)
            await selects.nth(3).select_option(label=args.from_year)
            await page.wait_for_timeout(400)
            end_options=await options(selects.nth(4))
            end=next((x for x in end_options if x["label"]==args.to_year and not x["disabled"]),None)
            if not end:
                raise RuntimeError("Requested end year is not enabled: "+args.to_year)
            await selects.nth(4).select_option(value=end["value"])
            await page.wait_for_timeout(500)
            area_options=await options(selects.nth(5))
            selected_area=next((x for x in area_options if x["value"] in ("","-1")),None)
            if report["config"].get("HuntingArea") == "1":
                if selected_area:
                    await selects.nth(5).select_option(value=selected_area["value"])
                else:
                    raise RuntimeError("No blank/all-area option found in hunting-area selector")
            else:
                selected_area={"label":"not required by report config","value":None}
            before=await page.evaluate("""() => ({
              controls:Array.from(document.querySelectorAll('select')).map(s=>({
                value:s.value,selected:s.selectedIndex>=0?s.options[s.selectedIndex].text.trim():'',
                options:s.options.length
              })),
              text:(document.body?.innerText||'').slice(0,12000)
            })""")
            button=page.locator('input[type="button"][value="Visa statistik"]')
            if not await button.count():
                raise RuntimeError("Visa statistik button not found")
            await button.click()
            try: await page.wait_for_load_state("networkidle",timeout=15000)
            except Exception: pass
            await page.wait_for_timeout(5000)
            after=await page.evaluate("""() => ({
              title:document.title,
              text:(document.body?.innerText||'').slice(-16000),
              tables:Array.from(document.querySelectorAll('table')).slice(0,15).map(t=>({
                rows:Array.from(t.querySelectorAll('tr')).slice(0,80).map(tr=>
                  Array.from(tr.querySelectorAll('th,td')).map(c=>(c.innerText||'').trim())
                )
              }))
            })""")
            result["sources"]["afo_level_report"]={"status":"completed","report":report,"report_catalog":report_catalog,"selected_without_hunting_area":selected_area,"before":before,"after":after,"network_responses":captured,"network_requests":captured_requests}
        except Exception as exc:
            result["sources"]["afo_level_report"]={"status":"error","error":type(exc).__name__+": "+str(exc)[:1500]}
        finally:
            await browser.close()
        await request.dispose()

    try:
        expected=set()
        with Path("data/national_area_catalog/national_area_catalog.csv").open("r",encoding="utf-8-sig",newline="") as handle:
            for row in csv.DictReader(handle,delimiter=";"):
                if row.get("boundary_mode")=="current":
                    expected.add(f"{int(row['county_portal_value']):02d}-{int(row['afo_portal_value']):03d}")
        features=(result["sources"].get("lansstyrelsen_afo_features",{}).get("json") or {}).get("features",[])
        actual={str((f.get("properties") or {}).get("afo_id") or (f.get("attributes") or {}).get("afo_id")) for f in features}
        result["sources"]["afo_catalog_crosswalk"]={"catalog_current_count":len(expected),"boundary_feature_count":len(actual),"missing_boundary_ids":sorted(expected-actual),"extra_boundary_ids":sorted(actual-expected)}
    except Exception as exc:
        result["sources"]["afo_catalog_crosswalk"]={"error":type(exc).__name__+": "+str(exc)[:1000]}

    path=args.out/"afo_source_probe.json"
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(path),"sources":{k:{"status":v.get("status"),"error":v.get("error"),"count":(v.get("json") or {}).get("count"),"wms":v.get("is_wms_capabilities")} for k,v in result["sources"].items()}},ensure_ascii=False,indent=2))

if __name__=="__main__":
    asyncio.run(main())
