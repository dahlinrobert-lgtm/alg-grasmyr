import csv, json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.archive_geographic_pilot import archive_pilot

def read_csv_total(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.DictReader(handle, delimiter=";"))["fallda_totalt"]
from scripts.validate_regional_pilot_snapshots import validate_root


class RegionalPilotSnapshotTests(unittest.TestCase):
    def make_pilot(self, root: Path, total="3"):
        folder = root / "01-test-lan-123456"
        folder.mkdir(parents=True, exist_ok=True)
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

    def test_preserves_changed_same_day_snapshot_as_intraday_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir(); out=root/"history"
            self.make_pilot(pilot)
            archive_pilot(pilot,out,datetime(2026,11,6,6,0,tzinfo=timezone.utc))
            self.make_pilot(pilot,"4")
            intraday = root / "intraday"
            result = archive_pilot(pilot,out,datetime(2026,11,6,7,0,tzinfo=timezone.utc),intraday_root=intraday)
            self.assertEqual(result["intraday_archived_count"],1)
            daily = next(out.rglob("2026-11-06.csv"))
            self.assertEqual(read_csv_total(daily),"3")
            observation = next(intraday.rglob("*.csv"))
            self.assertEqual(read_csv_total(observation),"4")
            self.assertEqual(len(list(intraday.rglob("*.json"))),1)


    def test_records_explicit_no_data_without_creating_zero_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pilot=root/"pilot"; pilot.mkdir(); out=root/"history"
            self.make_pilot(pilot)
            folder=pilot/"01-test-lan-123456"
            (folder/"report.csv").unlink()
            report={"selected_area":{"area_id":"123456","display_label":"12-34-56-A - Testområde"},
                    "hunting_year_to_selected":"2026/2027","data_csv":None,
                    "data_csv_rows":0,"data_status":"no_rendered_rows","errors":[]}
            (folder/"download-report.json").write_text(json.dumps(report),encoding="utf-8")
            summary=json.loads((pilot/"pilot_summary.json").read_text())
            summary["data_available_count"]=0
            summary["no_data_count"]=1
            summary["data_row_count"]=0
            summary["results"][0]["data_available"]=False
            summary["results"][0]["data_csv_rows"]=0
            summary["results"][0]["data_status"]="no_rendered_rows"
            (pilot/"pilot_summary.json").write_text(json.dumps(summary),encoding="utf-8")
            status_root=root/"status"
            result=archive_pilot(pilot,out,datetime(2026,11,11,10,0,tzinfo=timezone.utc),status_root=status_root)
            self.assertEqual(result["no_data_count"],1)
            self.assertEqual(list(out.rglob("*.csv")),[])
            status=json.loads(next(status_root.rglob("*.json")).read_text())
            self.assertEqual(status["observation_status"],"no_reported_data")
            self.assertEqual(status["row_count"],0)

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
