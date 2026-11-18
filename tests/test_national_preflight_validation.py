import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_national_preflight import validate


class NationalPreflightValidationTests(unittest.TestCase):
    def test_valid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = {"county": "Test län", "afo_name": "AFO", "area_portal_id": "123",
                         "from_year": "2026/2027", "to_year": "2026/2027"}
            result = {"county": "Test län", "afo_name": "AFO", "area_id": "123",
                      "requested_from_year": "2026/2027", "requested_to_year": "2026/2027",
                      "selected_area": {"area_id": "123"}, "selected_to_year": "2026/2027",
                      "portal_selection_success": True, "errors": []}
            (root / "selected_candidates.json").write_text(json.dumps({"candidates": [candidate]}))
            (root / "national_preflight_summary.json").write_text(json.dumps({
                "candidate_count": 1, "results": [result], "portal_selection_success_count": 1,
                "failure_count": 0, "data_available_count": 0, "production_write": False,
            }))
            self.assertEqual(validate(root), [])

    def test_rejects_wrong_identity_and_production_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = {"county": "Test län", "afo_name": "AFO", "area_portal_id": "123",
                         "from_year": "2026/2027", "to_year": "2026/2027"}
            result = {"county": "Test län", "afo_name": "AFO", "area_id": "123",
                      "requested_from_year": "2026/2027", "requested_to_year": "2026/2027",
                      "selected_area": {"area_id": "999"}, "selected_to_year": "2025/2026",
                      "portal_selection_success": True, "errors": []}
            (root / "selected_candidates.json").write_text(json.dumps({"candidates": [candidate]}))
            (root / "national_preflight_summary.json").write_text(json.dumps({
                "candidate_count": 1, "results": [result], "portal_selection_success_count": 1,
                "failure_count": 0, "data_available_count": 0, "production_write": True,
            }))
            self.assertTrue(validate(root))


if __name__ == "__main__":
    unittest.main()
