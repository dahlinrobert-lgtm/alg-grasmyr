#!/usr/bin/env python3
"""Compare Älgdata XLSX exports by registration number, not worksheet row position."""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out" / "boundary-workbook-audit"
PATTERN = re.compile(r"Avskjutning med mål - Förvaltningsområde - (Historiska|Nuvarande) gränser - .*? - (\d{4})--(\d{4})", re.I)
COLS = ["Registreringsnummer","Jaktområdets namn","Säsong","Slut-rapporterat","Registrerad areal ha","Vuxen","Handjur","Hondjur","Kalv","Handjur kalv","Hondjur kalv","Totalt","Varav otjänliga","Varav oregistrerad mark","Älgar/1000 ha","Tjur %","Kalv %","Vuxen historik","Handjur historik","Hondjur historik","Kalv historik","Totalt historik","Älgar/1000 ha historik","Vuxen per 1000 ha","Kalv per 1000 ha","Totalt per 1000 ha"]

def txt(v):
    return "" if v is None else str(v).strip()

def workbook_rows(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if len(rows) < 3:
        return {}
    headers = [txt(v) for v in rows[1]]
    output = {}
    for row in rows[2:]:
        vals = [txt(v) for v in row]
        if not vals or not vals[0]:
            continue
        reg = vals[0]
        # Exports may repeat the same key; preserve duplicates so they can be diagnosed.
        output.setdefault(reg, []).append({headers[i] if i < len(headers) and headers[i] else f"column_{i+1}": vals[i] for i in range(len(vals))})
    return output

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records=[]
    by_key={}
    seen_hashes={}
    for p in sorted(DATA.glob("*.xlsx")):
        m=PATTERN.search(p.name)
        if not m: continue
        mode="historical" if m.group(1).lower().startswith("histor") else "current"
        season=f"{m.group(2)}/{m.group(3)}"
        digest=sha(p)
        duplicate_of=seen_hashes.get(digest, "")
        seen_hashes.setdefault(digest,p.name)
        rec={"file":p.name,"mode":mode,"season":season,"size_bytes":p.stat().st_size,"sha256":digest,"duplicate_of":duplicate_of}
        records.append(rec)
        if not duplicate_of:
            by_key.setdefault(season,{}).setdefault(mode,[]).append(p)
    with (OUT/"workbook_inventory.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["file","mode","season","size_bytes","sha256","duplicate_of"],delimiter=";")
        w.writeheader(); w.writerows(records)
    comparisons=[]
    # Detailed inventory keyed by official registration number and actual reported area/harvest columns.
    missing_registration_details = []
    for season, modes in sorted(by_key.items()):
        old_files = modes.get("historical", [])
        new_files = modes.get("current", [])
        if not old_files or not new_files:
            continue
        for oldp in old_files:
            oldrows = workbook_rows(oldp)
            for newp in new_files:
                newrows = workbook_rows(newp)
                for reg in sorted(set(newrows) - set(oldrows)):
                    for row in newrows[reg]:
                        missing_registration_details.append({
                            "season": season, "registration": reg,
                            "name": row.get("Jaktområdets namn", ""),
                            "area_ha": row.get("Registrerad areal ha", ""),
                            "total_harvest": row.get("Totalt", ""),
                            "source_file": newp.name
                        })

    for season,modes in sorted(by_key.items()):
        olds=modes.get("historical",[]); news=modes.get("current",[])
        if not olds or not news:
            comparisons.append({"season":season,"status":"missing one boundary mode","historical_registrations":"","current_registrations":"","only_historical_count":"","only_current_count":"","field_difference_count":"","old_files":len(olds),"new_files":len(news)})
            continue
        for oldp in olds:
            oldrows=workbook_rows(oldp)
            for newp in news:
                newrows=workbook_rows(newp)
                oldkeys=set(oldrows); newkeys=set(newrows)
                missing_new=sorted(oldkeys-newkeys)
                missing_old=sorted(newkeys-oldkeys)
                field_diffs=[]
                duplicates=[]
                for reg in sorted(oldkeys & newkeys):
                    if len(oldrows[reg]) != 1 or len(newrows[reg]) != 1:
                        duplicates.append({"registration":reg,"historical_rows":len(oldrows[reg]),"current_rows":len(newrows[reg])})
                        continue
                    a,b=oldrows[reg][0],newrows[reg][0]
                    for col in sorted(set(a)|set(b)):
                        av,bv=a.get(col,""),b.get(col,"")
                        # Skip metadata and derived ratios where small denominator/rounding may differ.
                        if av != bv and col not in ("Säsong",):
                            field_diffs.append({"registration":reg,"name":a.get("Jaktområdets namn",b.get("Jaktområdets namn","")),"field":col,"historical":av,"current":bv})
                # Only report non-title differences using identity keys.
                status="compared by registration number"
                comparisons.append({
                    "season":season,"status":status,"historical_file":oldp.name,"current_file":newp.name,
                    "historical_registrations":len(oldkeys),"current_registrations":len(newkeys),
                    "old_files":1,"new_files":1,
                    "only_historical_count":len(missing_new),"only_current_count":len(missing_old),
                    "only_historical":missing_new,"only_current":missing_old,
                    "duplicate_keys":duplicates,"field_difference_count":len(field_diffs),
                    "field_differences":field_diffs,
                    "area_differences":[d for d in field_diffs if "areal" in d["field"].lower()],
                    "harvest_differences":[d for d in field_diffs if any(k in d["field"].lower() for k in ("vuxen","handjur","hondjur","kalv","totalt","otjänliga","oregistrerad"))]
                })
    # Track target ÄSO and historical component registrations in each original export.
    tracked = {
        "24-01-02-342-Ä": "Hörneåns ÄSO",
        "24-01-02-017-A": "Gräsmyrs VVO",
        "24-01-02-006-A": "Mullsjö VVO",
        "24-01-02-008-A": "Tallbergslidens VVO",
        "24-01-02-028-A": "Hörnsjö VVO",
        "24-01-02-045-A": "Hummelholms VVO",
        "24-01-02-052-A": "Nyåkers VVO",
        "24-01-02-093-A": "Djupsjö VVO",
        "24-01-02-100-A": "Torrböle VVO",
        "24-01-02-098-A": "Höglågdal",
        "24-01-02-183-A": "Namnlös registrering 183",
        "24-01-02-049-A": "Öre-Brattfors VVO",
        "24-01-02-067-A": "Hallens VVO",
    }
    tracked_rows = []
    for rec in records:
        p = DATA / rec["file"]
        rows = workbook_rows(p)
        for reg, display in tracked.items():
            for row in rows.get(reg, []):
                tracked_rows.append({
                    "season": rec["season"], "boundary_mode": rec["mode"],
                    "file": rec["file"], "registration": reg,
                    "tracked_label": display, "reported_name": row.get("Jaktområdets namn", ""),
                    "reported_area_ha": row.get("Registrerad areal ha", ""),
                    "harvest_total": row.get("Totalt", ""),
                    "reported_status": row.get("Slut-rapporterat", "")
                })
    tracked_fields=["season","boundary_mode","registration","tracked_label","reported_name","reported_area_ha","harvest_total","reported_status","file"]
    for outpath in [OUT/"tracked_registration_history.csv", DATA/"processed"/"area-registration-boundary-audit.csv"]:
        with outpath.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=tracked_fields,delimiter=";"); w.writeheader(); w.writerows(tracked_rows)
    # Direct comparison of the target ÄSO's reported area with the site's published series.
    target_rows = [r for r in tracked_rows if r["registration"] == "24-01-02-342-Ä"]
    annual_path = DATA / "area_annual.csv"
    annual = {}
    if annual_path.exists():
        with annual_path.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f,delimiter=";"):
                if row.get("series") == "hornean_current":
                    annual[row.get("season","")] = row.get("reported_area_ha","")
    area_check = []
    seen_pairs = set()
    for r in target_rows:
        pair=(r["season"],r["boundary_mode"],r["reported_area_ha"],r["file"])
        if pair in seen_pairs: continue
        seen_pairs.add(pair)
        site_area=annual.get(r["season"],"")
        area_check.append({
            "season":r["season"],"boundary_mode":r["boundary_mode"],"file":r["file"],
            "registration":r["registration"],"excel_reported_area_ha":r["reported_area_ha"],
            "site_series_area_ha":site_area,
            "matches_site_series": str(r["reported_area_ha"]) == str(site_area) if site_area else ""
        })
    area_fields=["season","boundary_mode","registration","excel_reported_area_ha","site_series_area_ha","matches_site_series","file"]
    for outpath in [OUT/"hornean_area_source_check.csv", DATA/"processed"/"hornean-area-source-check.csv"]:
        with outpath.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=area_fields,delimiter=";"); w.writeheader(); w.writerows(area_check)
    (OUT/"boundary_comparison.json").write_text(json.dumps(comparisons,ensure_ascii=False,indent=2),encoding="utf-8")
    with (OUT/"boundary_comparison_summary.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=["season","status","historical_file","current_file","historical_registrations","current_registrations","only_historical_count","only_current_count","field_difference_count"]
        w=csv.DictWriter(f,fieldnames=fields,delimiter=";"); w.writeheader()
        for x in comparisons: w.writerow({k:x.get(k,"") for k in fields})
    report=["# Jämförelse av originalfiler: historiska och nuvarande gränser","",
      f"Antal Excel-filer inventerade: **{len(records)}**. Identiska filer med samma SHA-256 har identifierats som dubbletter.",
      "",
      "Jämförelsen matchar rader på **registreringsnummer**, inte Excel-radnummer. Därför ska sorteringsskillnader inte räknas som dataskillnader. Gränslägen kan påverka registrerad areal och förvaltningsstatistik; rapporten visar skillnaderna men avgör inte vilken geometri som juridiskt gäller.",
      "",
      "| Säsong | Status | Historiska registreringar | Nuvarande registreringar | Endast historiska | Endast nuvarande | Fält som skiljer |",
      "|---|---|---:|---:|---:|---:|---:|"]
    for x in comparisons:
        label = x.get("status","")
        if x.get("season") == "2019/2020" and x.get("current_file","").endswith("2019--2020.xlsx"):
            label = "compared by registration number (duplicate export)"
        report.append("| "+" | ".join(str(v) for v in [x.get("season",""),label,x.get("historical_registrations",""),x.get("current_registrations",""),x.get("only_historical_count",""),x.get("only_current_count",""),x.get("field_difference_count","")])+" |")
    report.extend(["","## Säsongsvisa skillnader",""])
    for x in comparisons:
        if x["status"]!="compared by registration number": continue
        report.extend([f"### {x['season']}","",f"Historisk fil: `{x['historical_file']}`  ",f"Nuvarande fil: `{x['current_file']}`",""])
        if x["only_historical"]:
            report.append("Registreringar endast i historisk fil: "+", ".join(x["only_historical"]))
        if x["only_current"]:
            report.append("Registreringar endast i nuvarande fil:")
            details = [d for d in missing_registration_details if d["season"] == x["season"]]
            for d in details:
                report.append(f"- \`{d['registration']}\` — {d['name']}; areal {d['area_ha']} ha; totalt fällda {d['total_harvest']}. Källa: \`{d['source_file']}\`")
        if x["duplicate_keys"]: report.append("Dubbletter av registreringsnummer: "+json.dumps(x["duplicate_keys"],ensure_ascii=False))
        report.extend(["","| Registreringsnummer | Jaktområde | Fält | Historiskt | Nuvarande |","|---|---|---|---|---|"])
        for d in x["field_differences"][:250]:
            vals=[d["registration"],d["name"],d["field"],d["historical"],d["current"]]
            vals=[str(v).replace("|","\\|").replace("\n"," ") for v in vals]
            report.append("| "+" | ".join(vals)+" |")
        if len(x["field_differences"])>250: report.append(f"| … | … | … | Första 250 av {len(x['field_differences'])} fältskillnader visas | |")
        if not x["field_differences"] and not x["only_historical"] and not x["only_current"]:
            report.append("| — | — | — | Inga värdeskillnader identifierade | — |")
        report.append("")
    report.extend(["## Kontroll av arealen för Hörneåns ÄSO (24-01-02-342-Ä)","",
        "| Säsong | Gränsvariant | Excel: registrerad areal (ha) | Webbseriens areal (ha) | Matchar | Fil |",
        "|---|---|---:|---:|---|---|"])
    if area_check:
        for r in area_check:
            report.append("| "+" | ".join(str(r.get(k,"")) for k in ["season","boundary_mode","excel_reported_area_ha","site_series_area_ha","matches_site_series","file"])+" |")
    else:
        report.append("| — | — | — | — | Ingen rad med det exakta registreringsnumret hittades i Excel-exporterna | — |")
    report.extend(["",
        "## Historiska jaktområden och kandidater",
        "",
        "Fulla radvärden för de kända äldre områdeskoderna finns i \`out/boundary-workbook-audit/tracked_registration_history.csv\` i körningens artefakt. De är avsiktligt inte automatiskt summerade till Hörneåns ÄSO: medlemskap och geometri kräver separat belägg.",
        "",
        "## Viktiga reservationer","","- Perioder utan båda filtyperna kan inte jämföras direkt.","- Identiska dubblettfiler ska inte räknas som oberoende belägg.","- Registreringsnummer som saknas i en export kan bero på exporturval eller gränsdefinition; det är inte automatiskt ett bevis på att jaktområdet upphört eller tillkommit.","- Denna rapport verifierar Excel-innehåll och skillnader mellan exporterna, inte formella beslut eller polygonernas juridiska status.",""])
    (DATA/"processed"/"boundary-comparison-summary.md").write_text("\n".join(report),encoding="utf-8")
    print(f"Compared {len(records)} XLSX files using registration keys; report written to data/processed/boundary-comparison-summary.md")

if __name__=="__main__": main()
