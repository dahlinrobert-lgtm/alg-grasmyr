import tempfile
import unittest
from pathlib import Path

from scripts.azure_checkpoint_store import (
    _safe_relative_path,
    create_synthetic_fixture,
    sha256_file,
)


class AzureCheckpointStoreTests(unittest.TestCase):
    def test_safe_relative_path_rejects_traversal_and_absolute_paths(self):
        self.assertEqual(_safe_relative_path("areas/123/export.csv"), "areas/123/export.csv")
        for value in ("../secret", "areas/../../secret", "/absolute/file", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _safe_relative_path(value)

    def test_synthetic_fixture_is_explicitly_non_production(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "fixture"
            create_synthetic_fixture(root)
            checkpoint = (root / "checkpoint.json").read_text(encoding="utf-8")
            export = root / "areas" / "SYNTHETIC-001" / "export.csv"
            self.assertIn('"production_write": false', checkpoint)
            self.assertIn("SYNTHETIC-001", checkpoint)
            self.assertTrue(export.is_file())
            digest, size = sha256_file(export)
            self.assertEqual(len(digest), 64)
            self.assertEqual(size, export.stat().st_size)


if __name__ == "__main__":
    unittest.main()
