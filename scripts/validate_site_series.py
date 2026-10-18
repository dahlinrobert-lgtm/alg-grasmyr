#!/usr/bin/env python3
"""Validate the reconstructed elk harvest series against source CSVs."""
from __future__ import annotations
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
METHOD_HTML = (ROOT / "metod-data.html").read_text(encoding="utf-8")
SPECS = [
    ("elkHarvest", "data/processed/avskjutning_mal_ajo_hornean_2013-2026.csv",
     {"total": "fallda_totalt", "adult": "fallda_vuxna_totalt",
      "calves": "fallda_kalvar_totalt", "target": "avskjutningsmal_totalt"}),
    ("elkObs", "data/processed/algobs_hornean_2013-2026.csv",
     {"obs": "algobs_per_mantimme", "hours": "mantimmar",
      "calves": "antal_kalvar_per_hondjur"}),
    ("elkAge", "data/processed/medelalder_vuxna_hornean_2013-2026.csv",
     {"male": "handjur_medelalder_ar", "nMale": "handjur_antal",
      "female": "hondjur_medelalder_ar", "nFemale": "hondjur_antal"}),
    ("elkWeight", "data/processed/slaktvikt_hornean_2013-2026.csv",
     {"male": "handjur_vikt_kg", "nMale": "handjur_antal",
      "female": "hondjur_vikt_kg", "nFemale": "hondjur_antal",
      "calves": "kalvar_totalt_vikt_kg", "nCalves": "kalvar_totalt_antal",
      "maleCalf": "han_kalv_vikt_kg", "nMaleCalf": "han_kalv_antal",
      "femaleCalf": "hon_kalv_vikt_kg", "nFemaleCalf": "hon_kalv_antal",
      "calvesSep": "kalvar_sep_vikt_kg", "nCalvesSep": "kalvar_sep_antal",
      "maleCalfSep": "han_kalv_sep_vikt_kg", "nMaleCalfSep": "han_kalv_sep_antal",
      "femaleCalfSep": "hon_kalv_sep_vikt_kg", "nFemaleCalfSep": "hon_kalv_sep_antal",
      "calvesOct": "kalvar_okt_vikt_kg", "nCalvesOct": "kalvar_okt_antal",
      "maleCalfOct": "han_kalv_okt_vikt_kg", "nMaleCalfOct": "han_kalv_okt_antal",
      "femaleCalfOct": "hon_kalv_okt_vikt_kg", "nFemaleCalfOct": "hon_kalv_okt_antal"}),
]
HISTORICAL_CSV = "data/official_historical_area_summary_2009_2013.csv"
HISTORICAL_OBS_CSV = "data/processed/algobs_hornean_historical_boundaries_2010-2013.csv"
RECONSTRUCTED_AREAS = {
    "GRÄSMYRS VILTVÅRDSOMRÅDE",
    "MULLSJÖ VILTVÅRDSOMRÅDE",
    "TALLBERGSLIDENS VILTVÅRDSOMRÅDE",
    "HUMMELHOLMS VILTVÅRDSOMRÅDE",
    "HÖRNSJÖ VILTVÅRDSOMRÅDE",
    "TORRBÖLE VILTVÅRDSOMRÅDE",
}
HISTORICAL_SEASONS = ["2009/2010", "2010/2011", "2011/2012", "2012/2013"]

def number(value: str):
    value = value.strip().replace("%", "").replace(",", ".")
    if value in ("", "-", "null", "None"):
        return None
    try:
        return float(value)
    except ValueError:
        return value

def site_rows(array_name: str):
    match = re.search(rf"const\s+{re.escape(array_name)}\s*=\s*\[(.*?)\];", HTML, re.S)
    if not match:
        raise ValueError(f"Could not find JavaScript array {array_name}")
    rows = []
    for obj in re.finditer(r"\{([^{}]+)\}", match.group(1)):
        row = {}
        for pair in obj.group(1).split(","):
            if ":" not in pair:
                continue
            key, value = pair.split(":", 1)
            key, value = key.strip(), value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            row[key] = value
        if "season" in row:
            rows.append(row)
    return rows

def csv_rows(path: str):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))

def main():
    errors = []
    totals = []

    # Keep the landing page focused on charts, while ensuring the moved source
    # notes remain available on the dedicated methodology page.
    for label, needle in [
        ("method page link", 'href="metod-data.html"'),
        ("chart section", 'id="alg"'),
        ("historic VVO section", 'id="historiska-vvo"'),
        ("area chart", 'id="areaHistoryChart"'),
    ]:
        if needle not in HTML:
            errors.append(f"index.html: missing {label} ({needle})")
    for label, needle in [
        ("page title", "<title>Metod & data"),
        ("historical boundaries section", 'id="granser"'),
        ("area data section", 'id="arealdata"'),
        ("sources section", 'id="kallor"'),
        ("link back to charts", 'href="index.html"'),
        ("official statistics portal", "algdata-apps-stat"),
    ]:
        if needle not in METHOD_HTML:
            errors.append(f"metod-data.html: missing {label} ({needle})")
    if "<script>" in METHOD_HTML:
        errors.append("metod-data.html: should be a content-only page, not a duplicate dashboard")
    if "Arbetshypotes – inte verifierad gränshistorik" in HTML:
        errors.append("index.html: long area-history hypothesis should live on metod-data.html")
    totals.append(("page structure and methodology links", 1 if not errors else 0, 1))

    # The visible harvest series has a 2000s VVO proxy segment, four historical-boundary
    # VVO seasons, and then the official 13-season Hörneåns ÄSO series. Validate the
    # 2000s sums against transcribed official current-boundary workbook rows and the
    # 2009/2010–2012/2013 segment against the historical-boundary summary CSV.
    harvest = site_rows("elkHarvest")
    historical = csv_rows(HISTORICAL_CSV)
    historical_by_season: dict[str, dict[str, float]] = {}
    for season in HISTORICAL_SEASONS:
        source_rows = [
            row for row in historical
            if row["hunting_year"] == season
            and row["area_name"].strip().upper() in RECONSTRUCTED_AREAS
        ]
        if {r["area_name"].strip().upper() for r in source_rows} != RECONSTRUCTED_AREAS:
            errors.append(f"{HISTORICAL_CSV} {season}: expected exactly the six reconstructed VVOs")
        historical_by_season[season] = {
            "total": sum(int(r["harvest_total"]) for r in source_rows),
            "target": sum(int(r["quota_total"]) for r in source_rows),
        }
    current_boundary_expected = {
        "2000/2001": (126, 72), "2001/2002": (129, 72),
        "2002/2003": (133, 97), "2003/2004": (117, 106),
        "2004/2005": (112, 78), "2005/2006": (100, 64),
        "2006/2007": (81, 53), "2007/2008": (95, 60),
        "2008/2009": (89, 58),
    }
    for season, (expected_total, expected_target) in current_boundary_expected.items():
        rows = [r for r in harvest if r.get("season") == season]
        if len(rows) != 1:
            errors.append(f"elkHarvest {season}: expected one six-VVO proxy row, found {len(rows)}")
            continue
        if number(rows[0].get("total", "")) != expected_total:
            errors.append(f"elkHarvest {season} total: site={rows[0].get('total')}, workbook sum={expected_total}")
        if number(rows[0].get("target", "")) != expected_target:
            errors.append(f"elkHarvest {season} target: site={rows[0].get('target')}, workbook sum={expected_target}")
    totals.append(("elkHarvest current-boundary VVO sums 2000/2001–2008/2009", 9, 9))

    for season in HISTORICAL_SEASONS:
        rows = [r for r in harvest if r.get("season") == season]
        if len(rows) != 1:
            errors.append(f"elkHarvest {season}: expected exactly one reconstructed site row, found {len(rows)}")
            continue
        row = rows[0]
        for field in ("total", "target"):
            actual, expected = number(row.get(field, "")), historical_by_season[season][field]
            if actual != expected:
                errors.append(f"elkHarvest {season} {field}: site={actual!r}, sum of six VVOs={expected!r}")
        # These historic registrations expose total harvest and quota only in
        # the processed summary; do not assert anything about adult/calf fields.
    totals.append(("elkHarvest historical VVO sums", len(HISTORICAL_SEASONS), len(HISTORICAL_SEASONS)))

    # Historical Älgobs exists as a direct ÄSO report with historical boundaries
    # for 2010/2011–2012/2013. It is not a sum of the six VVO harvest records.
    obs = site_rows("elkObs")
    historical_obs = csv_rows(HISTORICAL_OBS_CSV)
    obs_by_season = {row["jaktsasong"]: row for row in historical_obs}
    obs_fields = {"obs": "algobs_per_mantimme", "hours": "mantimmar",
                  "calves": "antal_kalvar_per_hondjur"}
    for season in HISTORICAL_SEASONS:
        rows = [row for row in obs if row.get("season") == season]
        if len(rows) != 1:
            errors.append(f"elkObs {season}: expected exactly one historical row, found {len(rows)}")
            continue
        row = rows[0]
        if season == "2009/2010":
            if any(number(row.get(field, "")) is not None for field in obs_fields):
                errors.append("elkObs 2009/2010: values should remain missing; no source record is available")
            continue
        source_row = obs_by_season.get(season)
        if source_row is None:
            errors.append(f"{HISTORICAL_OBS_CSV}: missing season {season}")
            continue
        for site_field, csv_field in obs_fields.items():
            actual, expected = number(row.get(site_field, "")), number(source_row.get(csv_field, ""))
            if actual != expected:
                errors.append(f"elkObs {season} {site_field}: site={actual!r}, historical CSV {csv_field}={expected!r}")
    totals.append(("elkObs historical-boundary extension", 3, 3))

    # Older mean-age values cannot be reconstructed from available source files.
    # Keep explicit null rows for timeline alignment and ensure they stay null.
    age = site_rows("elkAge")
    for season in HISTORICAL_SEASONS:
        rows = [row for row in age if row.get("season") == season]
        if len(rows) != 1:
            errors.append(f"elkAge {season}: expected one explicit missing-value row, found {len(rows)}")
            continue
        if any(number(rows[0].get(field, "")) is not None for field in ("male", "nMale", "female", "nFemale")):
            errors.append(f"elkAge {season}: unsupported historical age values must remain missing")
    totals.append(("elkAge historical missing-value rows", 4, 4))

    # The post-reconstruction segment remains checked against the processed ÄSO
    # series exactly, with the original 13 seasonal records.
    for array_name, csv_path, field_map in SPECS:
        web = site_rows(array_name)
        source = csv_rows(csv_path)
        if array_name in ("elkHarvest", "elkObs", "elkAge", "elkWeight"):
            web = [row for row in web if int(row.get("season", "0").split("/")[0]) >= 2013]
        by_season = {row["jaktsasong"]: row for row in source}
        if len(web) != len(source):
            errors.append(f"{array_name}: expected {len(source)} rows in both sources, site={len(web)}, CSV={len(source)}")
        if len(by_season) != len(source):
            errors.append(f"{csv_path}: duplicate season keys")
        for row in web:
            season = row["season"]
            source_row = by_season.get(season)
            if source_row is None:
                errors.append(f"{array_name} {season}: season missing from CSV")
                continue
            for site_field, csv_field in field_map.items():
                actual, expected = number(row.get(site_field, "")), number(source_row.get(csv_field, ""))
                if actual != expected:
                    errors.append(f"{array_name} {season} {site_field}: site={actual!r}, CSV {csv_field}={expected!r}")
        totals.append((array_name, len(web), len(source)))

    for name, web_count, source_count in totals:
        print(f"PASS {name}: {web_count} site rows, {source_count} source rows")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f" - {error}")
        raise SystemExit(1)
    print("PASS: 2000s VVO proxy sums, 2009/2010–2012/2013 historical VVO sums, historical-boundary Älgobs, explicit age gaps, and current ÄSO series match their validation sources.")

if __name__ == "__main__":
    main()
