import unittest

from scripts.discover_national_areas import latest_year_window
from scripts.download_statistics import classify_data_status


class CurrentSeasonTests(unittest.TestCase):
    def test_catalogue_uses_latest_available_hunting_season(self):
        starts = [
            {"label": "1990/1991", "value": "1990"},
            {"label": "2025/2026", "value": "2025"},
            {"label": "2026/2027", "value": "2026"},
        ]
        ends = [
            {"label": "2026/2027", "value": "2026"},
        ]
        start, end = latest_year_window(starts, ends)
        self.assertEqual(start["label"], "2026/2027")
        self.assertEqual(end["label"], "2026/2027")

    def test_empty_current_season_is_not_parser_failure(self):
        self.assertEqual(classify_data_status(0, {"tables": [{"rows": []}]}), "no_rendered_rows")

    def test_unrecognized_table_is_distinguished(self):
        self.assertEqual(classify_data_status(0, {"tables": [{"rows": [["Other", "Header"]]}]}),
                         "unrecognized_table_structure")

    def test_data_rows_are_detected(self):
        self.assertEqual(classify_data_status(3, {"tables": [{"rows": []}]}), "data_rows")


if __name__ == "__main__":
    unittest.main()
