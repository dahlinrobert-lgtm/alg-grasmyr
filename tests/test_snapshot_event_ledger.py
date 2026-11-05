import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_snapshot_event_ledger import build_area, classify, event_id


class SnapshotEventLedgerTests(unittest.TestCase):
    def write_snapshot(self, folder, date, total, season="2026/2027", extra=None):
        row = {
            "registreringsnummer": "24-01-02-342-Ä",
            "jaktomradesnamn": "Hörneåns älgskötselområde",
            "jaktsasong": season,
            "fallda_totalt": total,
            "avskjutningsmal_totalt": "140",
        }
        if extra:
            row.update(extra)
        path = folder / f"{date}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row), delimiter=";")
            writer.writeheader()
            writer.writerow(row)
        metadata = {
            "snapshot_date_utc": date,
            "captured_at_utc": f"{date}T06:35:00+00:00",
            "area_key": "hornean",
            "area_id": "724577",
            "download_report": {"selected_area": {"display_label": "Hörneåns älgskötselområde"}},
        }
        path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")

    def test_cumulative_increase_is_reported_not_exact_kill_date(self):
        self.assertEqual(classify("fallda_totalt", "71", "78")[0], "reported_value_increase")
        self.assertIn("inte exakt", classify("fallda_totalt", "71", "78")[1])

    def test_decrease_is_correction(self):
        self.assertEqual(classify("fallda_totalt", "78", "75")[0], "correction")

    def test_blank_transitions_are_explicit(self):
        self.assertEqual(classify("fallda_totalt", "", "2")[0], "new_value")
        self.assertEqual(classify("fallda_totalt", "2", "")[0], "value_removed")

    def test_events_are_deterministic_and_only_for_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_snapshot(folder, "2026-11-01", "71")
            self.write_snapshot(folder, "2026-11-02", "78")
            first, summary = build_area(folder)
            second, _ = build_area(folder)
            self.assertEqual(first, second)
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(first[0]["event_type"], "reported_value_increase")
            self.assertEqual(first[0]["event_id"], event_id(first[0]))

    def test_missing_season_is_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_snapshot(folder, "2026-11-01", "71")
            self.write_snapshot(folder, "2026-11-02", "0", season="2025/2026")
            events, _ = build_area(folder)
            missing = [event for event in events if event["event_type"] == "season_missing"]
            self.assertEqual(len(missing), 1)
            self.assertIn("inte bevis", missing[0]["classification_reason"])


if __name__ == "__main__":
    unittest.main()
