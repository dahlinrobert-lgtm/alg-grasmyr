import unittest

from scripts.azure_checkpoint_pointer import (
    _validate_collection_id,
    _validate_pointer,
    latest_pointer_blob_name,
)


class AzureCheckpointPointerTests(unittest.TestCase):
    def valid_pointer(self):
        return {
            "schema_version": 1,
            "kind": "national_algdata_latest_checkpoint",
            "collection_id": "national-smoke",
            "snapshot_id": "snapshot-0001",
            "generation": 1,
            "production_write": False,
        }

    def test_pointer_path_is_scoped_to_collection(self):
        self.assertEqual(
            latest_pointer_blob_name("national-smoke"),
            "national-algdata/collections/national-smoke/latest.json",
        )

    def test_valid_pointer_is_accepted(self):
        _validate_pointer(self.valid_pointer(), "national-smoke")

    def test_pointer_for_different_collection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            _validate_pointer(self.valid_pointer(), "other-collection")

    def test_production_write_pointer_is_rejected(self):
        payload = self.valid_pointer()
        payload["production_write"] = True
        with self.assertRaisesRegex(ValueError, "provenance"):
            _validate_pointer(payload, "national-smoke")

    def test_invalid_collection_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            _validate_collection_id("../unsafe")


if __name__ == "__main__":
    unittest.main()
