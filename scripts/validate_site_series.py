#!/usr/bin/env python3
"""Validate the reconstructed elk harvest series against source CSVs."""
from __future__ import annotations
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
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
]
HISTORICAL_CSV = "data/official_historical_area_summary_2009_2013.csv"
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
    if value in ("", "-"):
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

    # The visible harvest series has four additional reconstructed years, before
    # the official 13-season Hörneåns ÄSO series. Validate those against the six
    # named historical VVO registrations, not against the newer ÄSO CSV.
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

    # The post-reconstruction segment remains checked against the processed ÄSO
    # series exactly, with the original 13 seasonal records.
    for array_name, csv_path, field_map in SPECS:
        web = site_rows(array_name)
        source = csv_rows(csv_path)
        if array_name == "elkHarvest":
            web = [row for row in web if row.get("season") not in HISTORICAL_SEASONS]
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
    print("PASS: reconstructed historical sums and all current ÄSO series match their source CSVs.")

if __name__ == "__main__":
    main()
