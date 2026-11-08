import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_geographic_pilot import validate_pilot


class GeographicPilotArtifactValidationTests(unittest.TestCase):
    def make_fixture(self, root: Path):
        area_id = "123456"
        folder = root / f"01-test-lan-{area_id}"
        folder.mkdir()
        candidate = {
            "county": "Test län", "afo_name": "ÄFO 1", "boundary_mode": "current",
            "from_year": "2026/2027", "to_year": "2026/2027",
            "area_portal_id": area_id,
        }
        (root / "selected_candidates.json").write_text(json.dumps({
            "candidates": [candidate]
        }), encoding="utf-8")
        row = {
            "registreringsnummer": "12-34-56-A",
            "jaktomradesnamn": "Test jaktlag",
            "slutrapporterat": "Nej",
            "fallda_totalt": "3",
        }
        csv_path = folder / "report.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row), delimiter=";")
            writer.writeheader()
            writer.writerow(row)
        report = {
            "selected_area": {"area_id": area_id, "display_label": "12-34-56-A - Test jaktlag"},
            "hunting_year_from": "2026/2027",
            "hunting_year_to_selected": "2026/2027",
            "boundary_mode": "current",
            "data_csv": "report.csv",
            "data_csv_rows": 1,
            "errors": [],
        }
        (folder / "download-report.json").write_text(json.dumps(report), encoding="utf-8")
        result = {
            "county": "Test län", "afo_name": "ÄFO 1", "area_id": area_id,
            "boundary_mode": "current", "requested_from_year": "2026/2027",
            "requested_to_year": "2026/2027", "data_csv_rows": 1,
            "data_status": "data_rows", "portal_selection_success": True,
            "data_available": True,
        }
        summary = {
            "candidate_count": 1, "results": [result], "data_row_count": 1,
            "portal_selection_success_count": 1, "data_available_count": 1,
            "failure_count": 0,
        }
        (root / "pilot_summary.json").write_text(json.dumps(summary), encoding="utf-8")
        return report, result

    def test_validates_matching_candidate_portal_report_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_fixture(Path(tmp))
            self.assertEqual(validate_pilot(Path(tmp)), [])

    def test_detects_portal_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report, _ = self.make_fixture(root)
            report["selected_area"]["area_id"] = "999999"
            report_path = next(root.glob("*/download-report.json"))
            report_path.write_text(json.dumps(report), encoding="utf-8")
            errors = validate_pilot(root)
            self.assertTrue(any("portal-selected ID" in error for error in errors))

    def test_accepts_explicit_no_rendered_rows_without_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report, result = self.make_fixture(root)
            report["data_status"] = "no_rendered_rows"
            report["data_csv"] = None
            report["data_csv_rows"] = 0
            result["data_status"] = "no_rendered_rows"
            result["data_csv_rows"] = 0
            summary = json.loads((root / "pilot_summary.json").read_text(encoding="utf-8"))
            summary["data_row_count"] = 0
            summary["data_available_count"] = 0
            (root / "pilot_summary.json").write_text(json.dumps(summary), encoding="utf-8")
            (root / "01-test-lan-123456" / "report.csv").unlink()
            report_path = root / "01-test-lan-123456" / "download-report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(validate_pilot(root), [])

    def test_rejects_missing_csv_without_explicit_no_rows_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report, _ = self.make_fixture(root)
            report["data_csv"] = None
            report["data_csv_rows"] = 0
            report["data_status"] = "data_rows"
            report_path = root / "01-test-lan-123456" / "download-report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            (root / "01-test-lan-123456" / "report.csv").unlink()
            errors = validate_pilot(root)
            self.assertTrue(any("missing report CSV" in error for error in errors))

    def test_detects_wrong_hunting_season(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report, result = self.make_fixture(root)
            report["hunting_year_to_selected"] = "2025/2026"
            report_path = next(root.glob("*/download-report.json"))
            report_path.write_text(json.dumps(report), encoding="utf-8")
            errors = validate_pilot(root)
            self.assertTrue(any("portal-selected end season" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
