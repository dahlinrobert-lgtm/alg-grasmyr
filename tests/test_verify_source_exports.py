import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_source_exports import audit, check_entry


class SourceExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "data/raw/test.csv"
        self.path.parent.mkdir(parents=True)
        self.path.write_text("jaktsasong;fallda_totalt\n2026/2027;78\n", encoding="utf-8")
        self.entry = {
            "source_id": "test-export-1",
            "relative_path": "data/raw/test.csv",
            "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "area_key": "hornean",
            "area_id": "724577",
            "hunting_seasons": ["2026/2027"],
            "report_id": "4",
            "boundary_mode": "current",
            "exported_at_utc": "2026-11-05T10:00:00Z",
        }

    def test_valid_file_integrity_only(self):
        self.assertEqual(check_entry(self.root, self.entry)["status"], "integrity_verified")

    def test_hash_mismatch(self):
        self.entry["sha256"] = "0" * 64
        self.assertEqual(check_entry(self.root, self.entry)["status"], "hash_mismatch")

    def test_missing_export(self):
        self.path.unlink()
        self.assertEqual(check_entry(self.root, self.entry)["status"], "missing_file")

    def test_reject_path_traversal(self):
        self.entry["relative_path"] = "data/raw/../../../secret.csv"
        self.assertEqual(check_entry(self.root, self.entry)["status"], "invalid")

    def test_empty_manifest_is_not_source_verified(self):
        manifest = self.root / "manifest.json"
        manifest.write_text('{"schema_version":1,"exports":[]}', encoding="utf-8")
        report = audit(self.root, manifest)
        self.assertEqual(report["manifest_entry_count"], 0)
        self.assertEqual(report["snapshot_value_verification_status"], "not_implemented")

    def test_duplicate_ids_invalid(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"exports": [self.entry, self.entry]}), encoding="utf-8")
        report = audit(self.root, manifest)
        self.assertEqual(report["counts"]["invalid"], 1)


if __name__ == "__main__":
    unittest.main()
