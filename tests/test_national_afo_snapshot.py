import tempfile
import unittest
from pathlib import Path

from scripts.snapshot_national_afo import (
    archive_complete_batch,
    load_active_afo_catalog,
    parse_afo_api_data,
)


class NationalAfoSnapshotTests(unittest.TestCase):
    def test_parse_afo_totals_sum_underlying_area_rows(self):
        data = {
            "TableDataFormatted": [
                [
                    {"Name": "ShotTotal", "Text": "5"},
                    {"Name": "AssignedTotal", "Text": "7"},
                    {"Name": "FinishedReporting", "Text": "Ja"},
                ],
                [
                    {"Name": "ShotTotal", "Text": "6"},
                    {"Name": "AssignedTotal", "Text": "8"},
                    {"Name": "FinishedReporting", "Text": "Nej"},
                ],
            ],
            "HeaderOne": [{"Name": "Fällda älgar"}],
            "HeaderTwo": [{"Name": "Totalt"}],
        }
        parsed = parse_afo_api_data(data, [])
        self.assertEqual(parsed["fallda_totalt"], 11)
        self.assertEqual(parsed["avskjutningsmal_totalt"], 15)
        self.assertEqual(parsed["source_row_count"], 2)
        self.assertEqual(parsed["finished_reporting_area_count"], 1)
        self.assertEqual(parsed["areas_with_kills_count"], 2)
        self.assertEqual(parsed["areas_with_targets_count"], 2)
        self.assertEqual(len(parsed["raw_area_rows"]), 2)

    def test_missing_area_count_is_not_silently_zero(self):
        data = {"TableDataFormatted": [[
            {"Name": "ShotTotal", "Text": "-"},
            {"Name": "AssignedTotal", "Text": "8"},
        ]]}
        with self.assertRaises(ValueError):
            parse_afo_api_data(data, [])

    def test_catalog_filters_to_current_season_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            path.write_text(
                "county;county_portal_value;afo_name;afo_portal_value;boundary_mode;from_year;to_year\n"
                "Västerbottens län;24;Sydöstra;5;current;2026/2027;2026/2027\n"
                "Västerbottens län;24;Sydöstra;5;historical;2026/2027;2026/2027\n"
                "Gävleborgs län;21;Furuvik;14;current;2024/2025;2024/2025\n",
                encoding="utf-8-sig",
            )
            rows = load_active_afo_catalog(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["afo_id"], "24-005")

    def test_incomplete_batch_does_not_write_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            with self.assertRaises(ValueError):
                archive_complete_batch([], root, "2026/2027", {"24-005"})
            self.assertFalse((Path(tmp) / "national_afo_dashboard.json").exists())


if __name__ == "__main__":
    unittest.main()
