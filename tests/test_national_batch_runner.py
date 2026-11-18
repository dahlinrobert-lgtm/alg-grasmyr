import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_national_batches import run_collection


def candidate(area_id):
    return {
        "area_portal_id": str(area_id),
        "county": "Norrbottens län",
        "afo_name": "Test-ÄFO",
        "from_year": "2026/2027",
        "to_year": "2026/2027",
    }


class NationalBatchRunnerTests(unittest.TestCase):
    def fake_success(self, candidate_row, area_dir, report_id, area_timeout):
        return {
            "area_id": str(candidate_row["area_portal_id"]),
            "county": candidate_row["county"],
            "afo_name": candidate_row["afo_name"],
            "portal_selection_success": True,
            "data_available": True,
            "data_status": "data_rows",
            "data_csv_rows": 2,
            "errors": [],
        }

    def test_limit_then_resume_skips_completed_areas(self):
        candidates = [candidate(i) for i in range(1, 6)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch("scripts.run_national_batches.run_area", side_effect=self.fake_success) as mocked:
                first = run_collection(candidates, output, batch_size=2, limit=2)
                self.assertEqual(first["completed_count"], 2)
                self.assertEqual(mocked.call_count, 2)

                second = run_collection(candidates, output, batch_size=2)
                self.assertEqual(second["completed_count"], 5)
                self.assertEqual(mocked.call_count, 5)
                self.assertEqual(second["status"], "completed")

    def test_candidate_set_mismatch_refuses_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            first = [candidate(1), candidate(2)]
            with patch("scripts.run_national_batches.run_area", side_effect=self.fake_success):
                run_collection(first, output, limit=1)
                with self.assertRaisesRegex(ValueError, "candidate list differs"):
                    run_collection([candidate(1), candidate(3)], output)

    def test_valid_empty_report_is_not_a_failure(self):
        candidates = [candidate(1)]
        def no_data(candidate_row, area_dir, report_id, area_timeout):
            return {
                "area_id": "1", "portal_selection_success": True,
                "data_available": False, "data_status": "no_rendered_rows",
                "errors": [],
            }
        with tempfile.TemporaryDirectory() as directory:
            with patch("scripts.run_national_batches.run_area", side_effect=no_data):
                manifest = run_collection(candidates, Path(directory) / "run")
            self.assertEqual(manifest["no_data_count"], 1)
            self.assertEqual(manifest["failure_count"], 0)
            self.assertEqual(manifest["results"]["1"]["status"], "no_data")


if __name__ == "__main__":
    unittest.main()
