import csv, json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.archive_geographic_pilot import archive_pilot
from scripts.validate_regional_pilot_snapshots import validate_root


class RegionalPilotSnapshotTests(unittest.TestCase):
    def make_pilot(self, root: Path, total="3"):
        folder = root / "01-test-lan-123456"
        folder.mkdir(parents=True)
        candidate = {
            "county": "Test län", "afo_name": "Test ÄFO",
            "area_portal_id": "123456", "area_display_id": "12-34-56-A",
            "area_name": "Testområde", "area_label_raw": "12-34-56-A - Testområde",
            "from_year": "2026/2027", "to_year": "2026/2027",
        }
        (root / "selected_candidates.json").write_text(json.dumps({"candidates":[candidate]}), encoding="utf-8")
        row = {"registreringsnummer":"12-34-56-A","jaktomradesnamn":"Testområde",
               "slutrapporterat":"Nej","fallda_totalt":total,"avskjutningsmal_totalt":"10"}
        csv_path = folder / "report.csv"
        with csv_path.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=list(row),delimiter=";");w.writeheader();w.writerow(row)
        report = {"selected_area":{"area_id":"123456","display_label":"12-34-56-A - Testområde"},
                  "hunting_year_to_selected":"2026/2027","data_csv":"report.csv","errors":[]}
        (folder/"download-report.json").write_text(json.dumps(report),encoding="utf-8")
        result = {"area_id":"123456","county":"Test län","afo_name":"Test ÄFO",
                  "portal_selection_success":True,"selected_to_year":"2026/2027",
                  "boundary_mode":"current"}
        summary={"candidate_count":1,"min_end_year":2026,"results":[result],
                 "portal_selection_success_count":1,"data_available_count":1,"data_row_count":1,
                 "failure_count":0,"identity_collisions":[]}
        (root/"pilot_summary.json").write_text(json.dumps(summary),encoding="utf-8")

    def test_archives_immutable_snapshot_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir(); out=root/"history"
            self.make_pilot(pilot)
            first=archive_pilot(pilot,out,datetime(2026,11,6,6,0,tzinfo=timezone.utc))
            self.assertEqual(first["archived_count"],1)
            self.assertEqual(validate_root(out),[])
            second=archive_pilot(pilot,out,datetime(2026,11,6,7,0,tzinfo=timezone.utc))
            self.assertEqual(second["unchanged_count"],1)
            self.assertEqual(validate_root(out),[])

    def test_refuses_to_overwrite_changed_same_day_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir(); out=root/"history"
            self.make_pilot(pilot)
            archive_pilot(pilot,out,datetime(2026,11,6,6,0,tzinfo=timezone.utc))
            self.make_pilot(pilot,"4")
            with self.assertRaises(FileExistsError):
                archive_pilot(pilot,out,datetime(2026,11,6,7,0,tzinfo=timezone.utc))

    def test_detects_tampered_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir(); out=root/"history"
            self.make_pilot(pilot)
            archive_pilot(pilot,out,datetime(2026,11,6,6,0,tzinfo=timezone.utc))
            path=next(out.rglob("*.csv")); path.write_text("tampered",encoding="utf-8")
            self.assertTrue(any("SHA-256" in e for e in validate_root(out)))

    def test_refuses_incomplete_pilot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir()
            self.make_pilot(pilot)
            summary=json.loads((pilot/"pilot_summary.json").read_text())
            summary["failure_count"]=1
            (pilot/"pilot_summary.json").write_text(json.dumps(summary))
            with self.assertRaises(ValueError):
                archive_pilot(pilot,root/"history",datetime(2026,11,6,6,0,tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
