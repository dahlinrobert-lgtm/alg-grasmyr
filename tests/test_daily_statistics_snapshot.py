import tempfile
import unittest
from pathlib import Path

from scripts.daily_statistics_snapshot import read_rows, compare


class DailyStatisticsSnapshotTests(unittest.TestCase):
    def test_legacy_slutrapporterat_is_used_as_season_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.csv"
            path.write_text(
                "registreringsnummer;jaktomradesnamn;slutrapporterat;fallda_totalt\n"
                "24-01-02-342-Ä;Hörneåns älgskötselområde;2026/2027;80\n",
                encoding="utf-8-sig",
            )
            rows = read_rows(path)
            self.assertEqual(list(rows), ["2026/2027"])
            self.assertEqual(rows["2026/2027"]["jaktsasong"], "2026/2027")
            self.assertNotIn("slutrapporterat", rows["2026/2027"])

    def test_missing_season_column_does_not_fall_back_to_row_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                "registreringsnummer;jaktomradesnamn;fallda_totalt\n"
                "24-01-02-342-Ä;Hörneåns älgskötselområde;80\n",
                encoding="utf-8-sig",
            )
            with self.assertRaisesRegex(ValueError, "missing hunting-season value"):
                read_rows(path)

    def test_comparison_uses_stable_season_key(self):
        previous = {"2026/2027": {"jaktsasong": "2026/2027", "fallda_totalt": "78"}}
        current = {"2026/2027": {"jaktsasong": "2026/2027", "fallda_totalt": "80"}}
        changes = compare(previous, current)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["season"], "2026/2027")
        self.assertEqual(changes[0]["change"], "values_changed")


if __name__ == "__main__":
    unittest.main()
