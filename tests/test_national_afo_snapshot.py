import tempfile
import unittest
from pathlib import Path

from scripts.snapshot_national_afo import (
    archive_complete_batch,
    load_active_afo_catalog,
    parse_afo_summary,
    parse_current_number,
)


class NationalAfoSnapshotTests(unittest.TestCase):
    def test_parse_current_number_preserves_zero_and_null(self):
        self.assertEqual(parse_current_number("1 234 (2 408)"), 1234)
        self.assertEqual(parse_current_number("12,5 (14,2)"), 12.5)
        self.assertEqual(parse_current_number("0 (783)"), 0)
        self.assertIsNone(parse_current_number("-"))

    def test_parse_summa_row_uses_total_cells(self):
        rows = [
            {"rows": [
                ["Registreringsnummer", "Jaktområdets namn", "Slut- rapporterat", "Registrerad areal ha", "Fällda älgar"],
                ["Vuxen", "Handjur", "Hondjur", "Kalv", "Totalt", "Avskjutningsmål"],
                ["Summa:", "", "", "14 773,37 (780 017,77)", "25 (1 550)", "13 (843)", "12 (707)",
                 "17 (858)", "9 (428)", "8 (430)", "42 (2 408)", "1 (4)", "1 (1)", "", "", "",
                 "35 (2 000)", "0 (783)", "0 (883)", "31 (1 394)", "66 (3 394)", "", "", "", ""],
            ]}
        ]
        parsed = parse_afo_summary(rows)
        self.assertEqual(parsed["fallda_totalt"], 42)
        self.assertEqual(parsed["avskjutningsmal_totalt"], 66)
        self.assertEqual(parsed["fallda_totalt_raw"], "42 (2 408)")

    def test_summary_row_is_required(self):
        with self.assertRaises(ValueError):
            parse_afo_summary([{"rows": [["Registreringsnummer"], ["No rows"]]}])

    def test_catalog_filters_to_current_season_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.csv"
            path.write_text(
                "county;county_portal_value;afo_name;afo_portal_value;boundary_mode;from_year;to_year\n"
                "Västerbottens län;24;Sydöstra;5;current;2026/2027;2026/2027\n"
                "Västerbottens län;24;Sydöstra;5;historical;2026/2027;2026/2027\n"
                "Gävleborgs län;21;Furuvik;14;current;2024/2025;2024/2025\n",
                encoding="utf-8-sig",
            )
            rows = load_active_afo_catalog(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["afo_id"], "24-005")

    def test_incomplete_batch_does_not_write_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "snapshots"
            with self.assertRaises(ValueError):
                archive_complete_batch([], root, "2026/2027", {"24-005"})
            self.assertFalse((Path(tmp) / "national_afo_dashboard.json").exists())


if __name__ == "__main__":
    unittest.main()
