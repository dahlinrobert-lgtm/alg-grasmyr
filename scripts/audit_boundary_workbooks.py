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
    for season,modes in sorted(by_key.items()):
        olds=modes.get("historical",[]); news=modes.get("current",[])
        if not olds or not news:
            comparisons.append({"season":season,"status":"missing one boundary mode","old_files":len(olds),"new_files":len(news)})
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
                    "only_historical_count":len(missing_new),"only_current_count":len(missing_old),
                    "only_historical":missing_new,"only_current":missing_old,
                    "duplicate_keys":duplicates,"field_difference_count":len(field_diffs),
                    "field_differences":field_diffs,
                    "area_differences":[d for d in field_diffs if "areal" in d["field"].lower()],
                    "harvest_differences":[d for d in field_diffs if any(k in d["field"].lower() for k in ("vuxen","handjur","hondjur","kalv","totalt","otjänliga","oregistrerad"))]
                })
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
        report.append("| "+" | ".join(str(x.get(k,"")) for k in ["season","status","historical_registrations","current_registrations","only_historical_count","only_current_count","field_difference_count"])+" |")
    report.extend(["","## Säsongsvisa skillnader",""])
    for x in comparisons:
        if x["status"]!="compared by registration number": continue
        report.extend([f"### {x['season']}","",f"Historisk fil: `{x['historical_file']}`  ",f"Nuvarande fil: `{x['current_file']}`",""])
        if x["only_historical"]:
            report.append("Registreringar endast i historisk fil: "+", ".join(x["only_historical"]))
        if x["only_current"]:
            report.append("Registreringar endast i nuvarande fil: "+", ".join(x["only_current"]))
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
    report.extend(["## Viktiga reservationer","","- Perioder utan båda filtyperna kan inte jämföras direkt.","- Identiska dubblettfiler ska inte räknas som oberoende belägg.","- Registreringsnummer som saknas i en export kan bero på exporturval eller gränsdefinition; det är inte automatiskt ett bevis på att jaktområdet upphört eller tillkommit.","- Denna rapport verifierar Excel-innehåll och skillnader mellan exporterna, inte formella beslut eller polygonernas juridiska status.",""])
    (DATA/"processed"/"boundary-comparison-summary.md").write_text("\n".join(report),encoding="utf-8")
    print(f"Compared {len(records)} XLSX files using registration keys; report written to data/processed/boundary-comparison-summary.md")

if __name__=="__main__": main()
