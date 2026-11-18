import tempfile
import unittest
from contextlib import ExitStack
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
        area_dir.mkdir(parents=True, exist_ok=True)
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
            with ExitStack() as stack:
                stack.enter_context(patch("scripts.run_national_batches.run_area", side_effect=self.fake_success))
                stack.enter_context(patch("scripts.azure_checkpoint_pointer.read_latest", return_value=None))
                cas = stack.enter_context(patch(
                    "scripts.azure_checkpoint_pointer.compare_and_swap_latest",
                    side_effect=[
                        {"etag": "etag-1", "generation": 1},
                        {"etag": "etag-2", "generation": 2},
                        {"etag": "etag-3", "generation": 3},
                    ],
                ))
                publish = stack.enter_context(patch("scripts.azure_checkpoint_store.publish_snapshot"))
                validate = stack.enter_context(patch("scripts.azure_batch_checkpoint.validate_batch_package"))
                manifest = run_collection(
                    candidates, output, batch_size=2, azure_collection_id="test-collection"
                )

            self.assertEqual(manifest["completed_count"], 2)
            self.assertEqual(publish.call_count, 3)  # initial manifest + each area
            self.assertEqual(validate.call_count, 3)
            self.assertIsNone(cas.call_args_list[0].args[2])
            self.assertEqual(cas.call_args_list[1].args[2], "etag-1")
            self.assertEqual(cas.call_args_list[2].args[2], "etag-2")
            self.assertTrue((package / "selected_candidates.json").is_file())
            self.assertTrue((package / "checkpoint_provenance.json").is_file())


if __name__ == "__main__":
    unittest.main()
