import json
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
        html_tables = [{"rows": [["Registreringsnummer"], ["Summa:", "", "42 (2 408)"]]}]
        parsed = parse_afo_api_data(data, html_tables)
        self.assertEqual(parsed["fallda_totalt"], 11)
        self.assertEqual(parsed["avskjutningsmal_totalt"], 15)
        self.assertEqual(parsed["source_row_count"], 2)
        self.assertEqual(parsed["finished_reporting_area_count"], 1)
        self.assertEqual(parsed["areas_with_kills_count"], 2)
        self.assertEqual(parsed["areas_with_targets_count"], 2)
        self.assertEqual(len(parsed["raw_area_rows"]), 2)
        self.assertEqual(parsed["raw_html_summa_row"][2], "42 (2 408)")

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

    @staticmethod
    def _record(afo_id="24-005", shot=11, target=15):
        return {
            "afo_id": afo_id,
            "county": "Västerbottens län",
            "afo_name": "Sydöstra",
            "fallda_totalt": shot,
            "fallda_totalt_raw": str(shot),
            "avskjutningsmal_totalt": target,
            "avskjutningsmal_totalt_raw": str(target),
            "data_status": "area_rows_available",
            "source_row_count": 2,
            "finished_reporting_area_count": 1,
            "areas_with_kills_count": 2 if shot else 0,
            "areas_with_targets_count": 2 if target else 0,
        }

    def test_dashboard_advances_to_newer_complete_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            expected = {"24-005"}
            first_path, first = archive_complete_batch(
                [self._record(shot=11)], root, "2026/2027", expected,
                snapshot_date="2026-11-22",
            )
            first_snapshot = root / "24-005" / "2026-11-22.json"
            second_path, second = archive_complete_batch(
                [self._record(shot=12)], root, "2026/2027", expected,
                snapshot_date="2026-11-23",
            )
            self.assertEqual(first_path, second_path)
            self.assertEqual(second["snapshot_date"], "2026-11-23")
            self.assertEqual(json.loads(second_path.read_text(encoding="utf-8"))["areas"][0]["fallda_totalt"], 12)
            self.assertEqual(json.loads(first_snapshot.read_text(encoding="utf-8"))["fallda_totalt"], 11)

    def test_same_day_identical_dashboard_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            expected = {"24-005"}
            path, dashboard = archive_complete_batch(
                [self._record()], root, "2026/2027", expected,
                snapshot_date="2026-11-23",
            )
            before = path.read_bytes()
            archive_complete_batch(
                [self._record()], root, "2026/2027", expected,
                snapshot_date="2026-11-23",
            )
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(dashboard["snapshot_date"], "2026-11-23")

    def test_same_day_changed_dashboard_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            expected = {"24-005"}
            path, _ = archive_complete_batch(
                [self._record(shot=11)], root, "2026/2027", expected,
                snapshot_date="2026-11-23",
            )
            before = path.read_bytes()
            with self.assertRaisesRegex(FileExistsError, "same-day dashboard"):
                archive_complete_batch(
                    [self._record(shot=11)], root, "2027/2028", expected,
                    snapshot_date="2026-11-23",
                )
            self.assertEqual(path.read_bytes(), before)

    def test_older_batch_cannot_regress_dashboard_or_write_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            expected = {"24-005"}
            path, _ = archive_complete_batch(
                [self._record(shot=12)], root, "2026/2027", expected,
                snapshot_date="2026-11-23",
            )
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "Refusing to replace newer dashboard"):
                archive_complete_batch(
                    [self._record(shot=11)], root, "2026/2027", expected,
                    snapshot_date="2026-11-22",
                )
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((root / "24-005" / "2026-11-22.json").exists())

    def test_incomplete_batch_does_not_write_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            with self.assertRaises(ValueError):
                archive_complete_batch([], root, "2026/2027", {"24-005"})
            self.assertFalse((Path(tmp) / "national_afo_dashboard.json").exists())


if __name__ == "__main__":
    unittest.main()
