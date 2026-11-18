import json
import tempfile
import unittest
from pathlib import Path

from scripts.azure_batch_checkpoint import validate_batch_package


class AzureBatchCheckpointTests(unittest.TestCase):
    def make_package(self, root: Path):
        candidates = [{"area_portal_id": "123", "county": "Test", "afo_name": "Test-AFO"}]
        (root / "selected_candidates.json").write_text(
            json.dumps({"candidates": candidates}), encoding="utf-8"
        )
        area = root / "run" / "areas" / "123" / "attempt-0001"
        area.mkdir(parents=True)
        (area / "download-report.json").write_text("{}", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "run_id": "synthetic-run",
            "production_write": False,
            "candidate_count": 1,
            "completed_count": 1,
            "success_count": 1,
            "no_data_count": 0,
            "failure_count": 0,
            "candidates": candidates,
            "results": {"123": {"status": "success"}},
        }
        (root / "run" / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_valid_package_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_package(root)
            summary = validate_batch_package(root)
            self.assertEqual(summary["completed_count"], 1)
            self.assertIs(summary["production_write"], False)

    def test_production_write_true_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_package(root)
            path = root / "run" / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["production_write"] = True
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "production_write"):
                validate_batch_package(root)

    def test_candidate_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_package(root)
            path = root / "run" / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["candidates"] = []
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidate list differs"):
                validate_batch_package(root)


if __name__ == "__main__":
    unittest.main()
