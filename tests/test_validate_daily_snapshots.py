import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_daily_snapshots import validate_area


class DailySnapshotValidationTests(unittest.TestCase):
    def write_snapshot(self, folder: Path, date: str, total: str, previous: str | None,
                       previous_rows: dict | None = None) -> dict:
        csv_path = folder / f"{date}.csv"
        metadata_path = folder / f"{date}.json"
        columns = [
            "registreringsnummer", "jaktomradesnamn", "jaktsasong",
            "fallda_totalt", "avskjutningsmal_totalt",
        ]
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, delimiter=";")
            writer.writeheader()
            writer.writerow({
                "registreringsnummer": "24-01-02-342-Ä",
                "jaktomradesnamn": "Hörneåns älgskötselområde",
                "jaktsasong": "2026/2027",
                "fallda_totalt": total,
                "avskjutningsmal_totalt": "140",
            })
        row = {
            "registreringsnummer": "24-01-02-342-Ä",
            "jaktomradesnamn": "Hörneåns älgskötselområde",
            "jaktsasong": "2026/2027",
            "fallda_totalt": total,
            "avskjutningsmal_totalt": "140",
        }
        changes = []
        if previous_rows is None:
            changes = [{
                "season": "2026/2027", "change": "new_season", "current": row
            }]
        elif previous_rows["2026/2027"]["fallda_totalt"] != total:
            changes = [{
                "season": "2026/2027",
                "change": "values_changed",
                "fields": {
                    "fallda_totalt": {
                        "previous": previous_rows["2026/2027"]["fallda_totalt"],
                        "current": total,
                    }
                },
            }]
        metadata = {
            "snapshot_date_utc": date,
            "captured_at_utc": f"{date}T06:35:00+00:00",
            "area_key": "hornean",
            "area_id": "724577",
            "report_id": "4",
            "boundary_mode": "current",
            "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "season_count": 1,
            "download_report": {"data_csv_rows": 1},
            "warnings": [],
            "previous_snapshot": previous,
            "changes_since_previous_snapshot": changes,
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        return {"2026/2027": row}

    def test_valid_two_day_history_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = self.write_snapshot(folder, "2026-11-01", "10", None)
            self.write_snapshot(folder, "2026-11-02", "12", "2026-11-01.csv", first)
            self.assertEqual(validate_area(folder), [])

    def test_legacy_slutrapporterat_column_is_accepted_as_season_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = self.write_snapshot(folder, "2026-11-01", "10", None)
            second_path = folder / "2026-11-02.csv"
            legacy_columns = [
                "registreringsnummer", "jaktomradesnamn", "slutrapporterat",
                "fallda_totalt", "avskjutningsmal_totalt",
            ]
            with second_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=legacy_columns, delimiter=";")
                writer.writeheader()
                writer.writerow({
                    "registreringsnummer": "24-01-02-342-Ä",
                    "jaktomradesnamn": "Hörneåns älgskötselområde",
                    "slutrapporterat": "2026/2027",
                    "fallda_totalt": "12",
                    "avskjutningsmal_totalt": "140",
                })
            metadata_path = folder / "2026-11-02.json"
            metadata = {
                "snapshot_date_utc": "2026-11-02",
                "captured_at_utc": "2026-11-02T06:35:00+00:00",
                "area_key": "hornean",
                "area_id": "724577",
                "report_id": "4",
                "boundary_mode": "current",
                "sha256": hashlib.sha256(second_path.read_bytes()).hexdigest(),
                "season_count": 1,
                "download_report": {"data_csv_rows": 1},
                "warnings": [],
                "previous_snapshot": "2026-11-01.csv",
                "changes_since_previous_snapshot": [{
                    "season": "2026/2027",
                    "change": "values_changed",
                    "fields": {
                        "fallda_totalt": {"previous": "10", "current": "12"}
                    }
                }],
            }
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            self.assertEqual(validate_area(folder), [])

    def test_invalid_legacy_season_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_snapshot(folder, "2026-11-01", "10", None)
            path = folder / "2026-11-01.csv"
            content = path.read_text(encoding="utf-8-sig").replace(
                "2026/2027", "Nej"
            ).replace("jaktsasong", "slutrapporterat")
            path.write_text(content, encoding="utf-8-sig")
            metadata_path = folder / "2026-11-01.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            errors = validate_area(folder)
            self.assertTrue(any("invalid hunting season" in error for error in errors))

    def test_hash_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_snapshot(folder, "2026-11-01", "10", None)
            (folder / "2026-11-01.csv").write_text("tampered", encoding="utf-8")
            errors = validate_area(folder)
            self.assertTrue(any("SHA-256" in error for error in errors))

    def test_incorrect_change_log_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = self.write_snapshot(folder, "2026-11-01", "10", None)
            self.write_snapshot(folder, "2026-11-02", "12", "2026-11-01.csv", first)
            metadata_path = folder / "2026-11-02.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["changes_since_previous_snapshot"] = []
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            errors = validate_area(folder)
            self.assertTrue(any("change log does not match" in error for error in errors))

    def test_duplicate_hunting_season_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_snapshot(folder, "2026-11-01", "10", None)
            path = folder / "2026-11-01.csv"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("24-01-02-342-Ä;Hörneåns älgskötselområde;2026/2027;10;140\n")
            metadata_path = folder / "2026-11-01.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            errors = validate_area(folder)
            self.assertTrue(any("duplicate hunting season" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
