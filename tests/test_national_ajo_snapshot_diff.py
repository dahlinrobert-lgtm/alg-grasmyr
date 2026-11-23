import json
import tempfile
import unittest
from pathlib import Path

from scripts.compare_national_ajo_snapshots import (
    compare_afo,
    compare_snapshot_sets,
    load_snapshot,
    stable_ajo_id,
)


def cell(name, text):
    return {"Name": name, "Text": text}


def raw_row(portal_id="715897", name="Jaktlag A", shot="2", target="4", finished="Nej"):
    return [
        cell("AfoName", f"<a onclick=\"drillDownToAjoReport(4,'{portal_id}');\">01-00-01-A</a>"),
        cell("AjoName", name),
        cell("Season", "2026/2027"),
        cell("FinishedReporting", finished),
        cell("ShotTotal", shot),
        cell("AssignedTotal", target),
    ]


def snapshot(afo_id, date, rows):
    return {
        "afo_id": afo_id,
        "snapshot_date": date,
        "hunting_season": "2026/2027",
        "boundary_mode": "current",
        "source_row_count": len(rows),
        "raw_area_rows": rows,
    }


class NationalAjoDiffTests(unittest.TestCase):
    def test_extracts_stable_portal_id(self):
        self.assertEqual(stable_ajo_id({"AfoName": "drillDownToAjoReport(4,'715897')"}), "715897")

    def test_detects_changes_status_and_addition_without_false_deletion(self):
        old = {"rows": {"1": {"ShotTotal": "2", "FinishedReporting": "Nej"}}}
        new = {"rows": {
            "1": {"ShotTotal": "5", "FinishedReporting": "Ja"},
            "2": {"ShotTotal": "0"},
        }}
        result = compare_afo(old, new)
        self.assertEqual([x["ajo_id"] for x in result["added_rows"]], ["2"])
        self.assertEqual(len(result["changed_rows"]), 1)
        self.assertEqual(len(result["finished_reporting_changes"]), 1)
        self.assertEqual(result["missing_rows_unconfirmed"], [])
        self.assertEqual(result["summary"] if "summary" in result else result["unchanged_row_count"], 0)

    def test_missing_later_row_is_unconfirmed_not_deletion(self):
        result = compare_afo(
            {"rows": {"old-id": {"ShotTotal": "1"}}},
            {"rows": {}},
        )
        missing = result["missing_rows_unconfirmed"][0]
        self.assertEqual(missing["classification"], "missing_in_later_snapshot_unconfirmed")
        self.assertFalse(missing["deletion_event"])

    def test_rejects_duplicate_stable_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "01-001" / "2026-11-21.json"
            path.parent.mkdir()
            path.write_text(json.dumps(snapshot("01-001", "2026-11-21", [
                raw_row(), raw_row()
            ])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate stable"):
                load_snapshot(path, "2026-11-21", "01-001")

    def test_rejects_incomplete_snapshot_pair_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "data" / "national_afo_snapshots" / "01-001"
            base.mkdir(parents=True)
            old = base / "2026-11-21.json"
            old.write_text(json.dumps(snapshot("01-001", "2026-11-21", [raw_row()])), encoding="utf-8")
            before = old.read_bytes()
            with self.assertRaisesRegex(ValueError, "Incomplete snapshot pair"):
                compare_snapshot_sets(Path(tmp), "2026-11-21", "2026-11-23", 1)
            self.assertEqual(old.read_bytes(), before)

    def test_complete_pair_report_counts_rows_and_does_not_modify_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "data" / "national_afo_snapshots" / "01-001"
            base.mkdir(parents=True)
            old = base / "2026-11-21.json"
            new = base / "2026-11-23.json"
            old.write_text(json.dumps(snapshot("01-001", "2026-11-21", [raw_row()])), encoding="utf-8")
            new.write_text(json.dumps(snapshot("01-001", "2026-11-23", [raw_row(shot="3", finished="Ja")])), encoding="utf-8")
            before = (old.read_bytes(), new.read_bytes())
            report = compare_snapshot_sets(Path(tmp), "2026-11-21", "2026-11-23", 1)
            self.assertEqual(report["afo_count"], 1)
            self.assertEqual(report["old_raw_ajo_row_count"], 1)
            self.assertEqual(report["summary"]["changed"], 1)
            self.assertEqual(report["summary"]["status_changed"], 1)
            self.assertEqual((old.read_bytes(), new.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
