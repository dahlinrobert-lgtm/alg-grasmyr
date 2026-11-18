import unittest

from scripts.run_national_preflight import select_national_candidates
from scripts.discover_national_areas import county_discovery_audit


class NationalPreflightSelectionTests(unittest.TestCase):
    def test_selects_one_area_per_current_afo_and_excludes_known_pilot_ids(self):
        rows = [
            {"county": "Norrbottens län", "afo_name": "AFO A", "boundary_mode": "current",
             "area_portal_id": "101", "area_name": "Area B", "from_year": "2026/2027", "to_year": "2026/2027"},
            {"county": "Norrbottens län", "afo_name": "AFO A", "boundary_mode": "current",
             "area_portal_id": "102", "area_name": "Area A", "from_year": "2026/2027", "to_year": "2026/2027"},
            {"county": "Norrbottens län", "afo_name": "AFO B", "boundary_mode": "current",
             "area_portal_id": "724577", "area_name": "Existing pilot", "from_year": "2026/2027", "to_year": "2026/2027"},
            {"county": "Skåne län", "afo_name": "AFO S", "boundary_mode": "historical",
             "area_portal_id": "201", "area_name": "Historical", "from_year": "2026/2027", "to_year": "2026/2027"},
            {"county": "Skåne län", "afo_name": "AFO S", "boundary_mode": "current",
             "area_portal_id": "202", "area_name": "Too old", "from_year": "2025/2026", "to_year": "2025/2026"},
        ]
        selected, coverage = select_national_candidates(rows, min_end_year=2026)
        self.assertEqual([x["area_portal_id"] for x in selected], ["102"])
        self.assertEqual(coverage["afo_count"], 1)
        self.assertEqual(coverage["counties"], ["Norrbottens län"])

    def test_can_select_more_than_one_area_per_afo(self):
        rows = [
            {"county": "Västerbottens län", "afo_name": "AFO", "boundary_mode": "current",
             "area_portal_id": str(i), "area_name": f"Area {i}", "from_year": "2026/2027", "to_year": "2026/2027"}
            for i in range(1, 4)
        ]
        selected, coverage = select_national_candidates(rows, areas_per_afo=2)
        self.assertEqual(len(selected), 2)
        self.assertEqual(coverage["afo_coverage"][0]["selected_count"], 2)
        self.assertEqual([x["area_portal_id"] for x in selected], ["1", "3"])

    def test_gotland_is_explicitly_non_applicable_not_a_missing_county(self):
        from scripts.discover_national_areas import EXPECTED_SWEDISH_COUNTIES

        audit = county_discovery_audit(EXPECTED_SWEDISH_COUNTIES)
        self.assertNotIn("Gotlands län", audit["missing_expected_counties"])
        self.assertEqual(audit["non_applicable_counties"][0]["county"], "Gotlands län")
        self.assertEqual(audit["administrative_county_count"], 21)
        self.assertEqual(audit["expected_county_count"], 20)
        self.assertTrue(audit["complete"])

    def test_a_real_missing_eligible_county_is_still_reported(self):
        audit = county_discovery_audit(["Västerbottens län", "Norrbottens län"])
        self.assertIn("Skåne län", audit["missing_expected_counties"])
        self.assertNotIn("Gotlands län", audit["missing_expected_counties"])
        self.assertFalse(audit["complete"])


if __name__ == "__main__":
    unittest.main()
