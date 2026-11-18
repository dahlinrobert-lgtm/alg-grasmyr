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


    def test_failed_attempt_is_preserved_and_retried_only_when_opted_in(self):
        candidates = [candidate(1)]
        calls = []
        def fail_then_succeed(candidate_row, area_dir, report_id, area_timeout):
            calls.append(area_dir)
            if len(calls) == 1:
                return {
                    "area_id": "1", "portal_selection_success": False,
                    "data_available": False, "data_status": "timeout",
                    "errors": ["temporary timeout"],
                }
            return self.fake_success(candidate_row, area_dir, report_id, area_timeout)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch("scripts.run_national_batches.run_area", side_effect=fail_then_succeed):
                first = run_collection(candidates, output)
                self.assertEqual(first["failure_count"], 1)
                skipped = run_collection(candidates, output)
                self.assertEqual(len(calls), 1)
                self.assertEqual(skipped["failure_count"], 1)
                final = run_collection(candidates, output, retry_failed=True)

            result = final["results"]["1"]
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["attempt_number"], 2)
            self.assertEqual(len(result["attempt_history"]), 2)
            self.assertEqual(result["attempt_history"][0]["status"], "failed")
            self.assertEqual(result["attempt_history"][1]["status"], "success")
            self.assertNotEqual(calls[0], calls[1])
            self.assertTrue(str(calls[0]).endswith("attempt-0001"))
            self.assertTrue(str(calls[1]).endswith("attempt-0002"))

    def test_no_data_is_final_and_not_retried(self):
        candidates = [candidate(1)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch("scripts.run_national_batches.run_area", side_effect=lambda *args: {
                "area_id": "1", "portal_selection_success": True,
                "data_available": False, "data_status": "no_rendered_rows",
                "errors": [],
            }) as mocked:
                first = run_collection(candidates, output)
                second = run_collection(candidates, output, retry_failed=True)
                self.assertEqual(mocked.call_count, 1)
            self.assertEqual(first["no_data_count"], 1)
            self.assertEqual(second["results"]["1"]["status"], "no_data")
            self.assertEqual(len(second["results"]["1"]["attempt_history"]), 1)


if __name__ == "__main__":
    unittest.main()
