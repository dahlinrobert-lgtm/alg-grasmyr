import tempfile
import unittest
from pathlib import Path

from scripts.national_batching import (
    create_manifest,
    load_manifest,
    next_pending_batch,
    public_status,
    record_result,
    save_manifest_atomic,
)


def candidate(area_id):
    return {
        "area_portal_id": str(area_id),
        "county": "Norrbottens län",
        "afo_name": "Test-ÄFO",
        "from_year": "2026/2027",
        "to_year": "2026/2027",
    }


class NationalBatchingTests(unittest.TestCase):
    def test_batches_are_deterministic_and_cover_every_candidate_once(self):
        candidates = [candidate(i) for i in range(1, 8)]
        manifest = create_manifest(candidates, batch_size=3, run_id="test")
        self.assertEqual([len(x["candidate_ids"]) for x in manifest["batches"]], [3, 3, 1])
        flattened = [area_id for batch in manifest["batches"] for area_id in batch["candidate_ids"]]
        self.assertEqual(flattened, [str(i) for i in range(1, 8)])
        self.assertEqual(next_pending_batch(manifest)["batch_id"], "batch-0001")

    def test_duplicate_or_missing_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            create_manifest([candidate(1), candidate(1)], batch_size=1)
        invalid = candidate(2)
        invalid["area_portal_id"] = ""
        with self.assertRaises(ValueError):
            create_manifest([invalid])

    def test_checkpoint_resume_and_status_distinguish_no_data_from_failure(self):
        manifest = create_manifest([candidate(1), candidate(2), candidate(3)], batch_size=2)
        record_result(manifest, {"area_id": "1", "portal_selection_success": True, "data_available": True})
        record_result(manifest, {"area_id": "2", "portal_selection_success": True, "data_available": False})
        self.assertEqual(manifest["results"]["1"]["status"], "success")
        self.assertEqual(manifest["results"]["2"]["status"], "no_data")
        self.assertEqual(next_pending_batch(manifest)["batch_id"], "batch-0002")
        record_result(manifest, {"area_id": "3", "portal_selection_success": False, "data_available": False})
        self.assertEqual(manifest["status"], "completed_with_errors")
        self.assertEqual(manifest["failure_count"], 1)
        self.assertEqual(manifest["no_data_count"], 1)
        self.assertIsNone(next_pending_batch(manifest))
        self.assertFalse(public_status(manifest)["production_write"])

    def test_unknown_area_is_rejected(self):
        manifest = create_manifest([candidate(1)])
        with self.assertRaises(ValueError):
            record_result(manifest, {"area_id": "999", "portal_selection_success": True})

    def test_atomic_manifest_roundtrip(self):
        manifest = create_manifest([candidate(1)], batch_size=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            save_manifest_atomic(path, manifest)
            loaded = load_manifest(path)
            self.assertEqual(loaded["candidate_count"], 1)
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
