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
            selected, missing = select_candidates(path, ["Norrbottens län", "Västerbottens län", "Skåne län"])
            self.assertEqual([r["area_portal_id"] for r in selected], ["101", "200"])
            self.assertEqual(missing, ["Skåne län"])

    def test_excludes_stale_catalog_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            fields = ["county", "boundary_mode", "area_portal_id", "from_year", "to_year", "afo_name"]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
                writer.writeheader()
                writer.writerow({"county":"Skåne län","boundary_mode":"current","area_portal_id":"300",
                                 "from_year":"2010/2011","to_year":"2022/2023","afo_name":"AFO"})
            selected, missing = select_candidates(path, ["Skåne län"])
            self.assertEqual(selected, [])
            self.assertEqual(missing, ["Skåne län"])


if __name__ == "__main__":
    unittest.main()
