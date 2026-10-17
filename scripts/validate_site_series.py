#!/usr/bin/env python3
"""Validate the three 13-season elk series embedded in index.html against processed CSVs."""
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
    for array_name, csv_path, field_map in SPECS:
        web = site_rows(array_name)
        source = csv_rows(csv_path)
        by_season = {row["jaktsasong"]: row for row in source}
        if len(web) != 13 or len(source) != 13:
            errors.append(f"{array_name}: expected 13 seasons in both sources, site={len(web)}, CSV={len(source)}")
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
    for name, web_count, csv_count in totals:
        print(f"PASS {name}: {web_count} site rows, {csv_count} CSV rows")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f" - {error}")
        raise SystemExit(1)
    print("PASS: all selected website values match processed CSV values.")

if __name__ == "__main__":
    main()
