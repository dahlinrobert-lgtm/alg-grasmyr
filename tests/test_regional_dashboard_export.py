import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_regional_dashboard_export import build_area, build_export


class RegionalDashboardExportTests(unittest.TestCase):
    def write_snapshot(self, folder: Path, date: str, total: str, previous: str | None = None):
        with (folder / f"{date}.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["registreringsnummer", "jaktomradesnamn", "slutrapporterat",
                            "fallda_totalt", "fallda_vuxna_totalt", "fallda_kalvar_totalt"],
                delimiter=";",
            )
            writer.writeheader()
            writer.writerow({
                "registreringsnummer": "20-21-03-030-A",
                "jaktomradesnamn": "Testområdet",
                "slutrapporterat": "Nej",
                "fallda_totalt": total,
                "fallda_vuxna_totalt": total,
                "fallda_kalvar_totalt": "0",
            })
        (folder / f"{date}.json").write_text(json.dumps({
            "area_key": folder.name,
            "area_id": "123",
            "area_display_id": "20-21-03-030-A",
            "area_name": "Testområdet",
            "county": "Dalarnas län",
            "afo": "Test-ÄFO",
            "hunting_season": "2026/2027",
        }), encoding="utf-8")

    def test_first_observation_and_latest_increase_are_snapshot_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "test-area"
            folder.mkdir()
            self.write_snapshot(folder, "2026-11-06", "0")
            self.write_snapshot(folder, "2026-11-07", "3")
            area = build_area(folder)
            self.assertEqual(area["first_observed_positive_date"], "2026-11-07")
            self.assertEqual(area["latest_observed_increase_date"], "2026-11-07")
            self.assertEqual(area["latest_total"], 3)
            self.assertEqual(area["latest_delta"], 3)

    def test_no_increase_does_not_invent_an_increase_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "test-area"
            folder.mkdir()
            self.write_snapshot(folder, "2026-11-06", "2")
            self.write_snapshot(folder, "2026-11-07", "2")
            area = build_area(folder)
            self.assertEqual(area["first_observed_positive_date"], "2026-11-06")
            self.assertIsNone(area["latest_observed_increase_date"])
            self.assertEqual(area["latest_delta"], 0)

    def test_generic_catalogue_suffix_is_not_used_as_area_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "skane-area"
            folder.mkdir()
            self.write_snapshot(folder, "2026-11-08", "0")
            meta_path = folder / "2026-11-08.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["area_name"] = ""
            meta["catalogue_area_name"] = "A"
            meta["area_display_id"] = "12-02-07-001"
            meta["quality_flags"] = ["missing_jaktomradesnamn"]
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            area = build_area(folder)
            self.assertEqual(area["area_name"], "")
            self.assertEqual(area["catalogue_area_name"], "A")
            self.assertEqual(area["display_name"], "Jaktområde 12-02-07-001")
            self.assertEqual(area["display_name_source"], "registration_id_fallback")
            self.assertIn("missing_descriptive_area_name", area["quality_flags"])

    def test_real_portal_name_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "named-area"
            folder.mkdir()
            self.write_snapshot(folder, "2026-11-08", "0")
            area = build_area(folder)
            self.assertEqual(area["display_name"], "Testområdet")
            self.assertEqual(area["display_name_source"], "portal_report")

    def test_export_reports_latest_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "test-area"
            folder.mkdir()
            self.write_snapshot(folder, "2026-11-06", "0")
            self.write_snapshot(folder, "2026-11-07", "1")
            payload = build_export(root)
            self.assertEqual(payload["area_count"], 1)
            self.assertEqual(payload["areas_with_latest_snapshot"], 1)
            self.assertEqual(payload["latest_snapshot_date"], "2026-11-07")


if __name__ == "__main__":
    unittest.main()
