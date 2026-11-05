import csv
import tempfile
import unittest
from pathlib import Path

from scripts.run_geographic_pilot import select_candidates


class GeographicPilotTests(unittest.TestCase):
    def test_selects_one_recent_current_area_per_county(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            fields = ["county", "boundary_mode", "area_portal_id", "from_year", "to_year",
                      "afo_name", "area_name", "area_label_raw"]
            rows = [
                ["Norrbottens län", "current", "100", "2018/2019", "2025/2026", "AFO N", "Zeta", "Zeta"],
                ["Norrbottens län", "current", "101", "2018/2019", "2026/2027", "AFO N", "Beta", "Beta"],
                ["Norrbottens län", "historical", "102", "2018/2019", "2026/2027", "AFO N", "Old", "Old"],
                ["Västerbottens län", "current", "724577", "2018/2019", "2026/2027", "AFO V", "Hörneån", "Hörneån"],
                ["Västerbottens län", "current", "718148", "2018/2019", "2026/2027", "AFO V", "Gräsmyr", "Gräsmyr"],
                ["Västerbottens län", "current", "200", "2018/2019", "2025/2026", "AFO V", "Delta", "Delta"],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerow(fields)
                writer.writerows(rows)
            selected, missing, collisions = select_candidates(path, ["Norrbottens län", "Västerbottens län", "Skåne län"])
            self.assertEqual([r["area_portal_id"] for r in selected], ["101", "200"])
            self.assertEqual(missing, ["Skåne län"])
            self.assertEqual(collisions, [])

    def test_excludes_stale_catalog_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            fields = ["county", "boundary_mode", "area_portal_id", "from_year", "to_year", "afo_name"]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
                writer.writeheader()
                writer.writerow({"county":"Skåne län","boundary_mode":"current","area_portal_id":"300",
                                 "from_year":"2010/2011","to_year":"2022/2023","afo_name":"AFO"})
            selected, missing, collisions = select_candidates(path, ["Skåne län"], min_end_year=2024)
            self.assertEqual(selected, [])
            self.assertEqual(missing, ["Skåne län"])

    def test_selects_latest_available_even_when_catalog_is_historical(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            fields = ["county", "boundary_mode", "area_portal_id", "from_year", "to_year", "afo_name", "area_name"]
            rows = [
                ["Norrbottens län", "current", "300", "1998/1999", "2007/2008", "AFO N", "Old"],
                ["Norrbottens län", "current", "301", "2008/2009", "2017/2018", "AFO N", "Newer"],
                ["Norrbottens län", "historical", "302", "2018/2019", "2025/2026", "AFO N", "Historical"],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerow(fields)
                writer.writerows(rows)
            selected, missing, collisions = select_candidates(path, ["Norrbottens län"])
            self.assertEqual([r["area_portal_id"] for r in selected], ["301"])
            self.assertEqual(missing, [])

    def test_duplicate_portal_id_is_not_assigned_to_two_counties(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            fields = ["county", "boundary_mode", "area_portal_id", "from_year", "to_year", "afo_name", "area_name"]
            rows = [
                ["Jämtlands län", "current", "722495", "2026/2027", "2026/2027", "AFO J", "Area J"],
                ["Gävleborgs län", "current", "722495", "2026/2027", "2026/2027", "AFO G", "Area G"],
                ["Gävleborgs län", "current", "722496", "2026/2027", "2026/2027", "AFO G", "Area G2"],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerow(fields)
                writer.writerows(rows)
            selected, missing, collisions = select_candidates(path, ["Jämtlands län", "Gävleborgs län"])
            self.assertEqual([r["area_portal_id"] for r in selected], ["722495", "722496"])
            self.assertEqual(missing, [])
            self.assertEqual(len(collisions), 1)
            self.assertEqual(collisions[0]["already_assigned_county"], "Jämtlands län")


if __name__ == "__main__":
    unittest.main()
