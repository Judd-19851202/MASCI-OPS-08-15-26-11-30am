"""Daily Job Report endpoint tests for /api/daily-reports CRUD + validation + regression."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fall back to frontend/.env REACT_APP_BACKEND_URL
    from pathlib import Path
    env_path = Path("/app/frontend/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


def _full_payload(prefix="TEST_DR"):
    return {
        "project_name": f"{prefix}_Project A1A",
        "project_number": "TEST-25-23",
        "location": "Port Orange, FL",
        "report_date": "2026-01-15",
        "report_number": "DR-001",
        "prepared_by": "Test Foreman",
        "superintendent": "Test Super",
        "weather_summary": "75°F / Sunny",
        "weather_snapshots": [
            {"time": "06:00", "condition": "Clear", "temp_f": 65, "precip_in": 0, "humidity_pct": 70, "wind_mph": 4},
            {"time": "12:00", "condition": "Sunny", "temp_f": 80, "precip_in": 0, "humidity_pct": 55, "wind_mph": 8},
            {"time": "18:00", "condition": "Sunny", "temp_f": 78, "precip_in": 0, "humidity_pct": 60, "wind_mph": 6},
        ],
        "schedule_delays": "No",
        "weather_impact": "No",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "incident_notes": "",
        "general_notes": "Smooth day.",
        "masci_crews": [
            {"trade": "Earthwork", "foreman": "Joe", "count": "5", "hours": "8", "work_performed": "Grading"},
            {"trade": "Concrete", "foreman": "Mike", "count": "3", "hours": "8", "work_performed": "Pour curb"},
        ],
        "subcontractors": [
            {"company": "ABC Striping", "trade": "Striping", "foreman": "L. Lopez", "count": "2", "hours": "6", "work_performed": "Lane lines"},
        ],
        "visitors": [
            {"name": "Bob Inspector", "company": "FDOT", "time_in": "10:00", "time_out": "11:30", "purpose": "QA visit"},
        ],
        "equipment": [
            {"description": "CAT 320 Excavator", "hours_used": "6", "time_delivered": "07:00", "time_removed": "", "notes": ""},
        ],
        "materials": [
            {"description": "Crushed Aggregate", "quantity": "40", "unit": "ton", "supplier": "Vulcan", "ticket_number": "T-9911", "notes": ""},
        ],
        "activities": [
            {"activity": "Curb pour", "percent_complete": "60", "station_from": "10+00", "station_to": "12+00", "notes": ""},
        ],
        "photos": [f"data:image/png;base64,FAKE{i}" for i in range(6)],
        "prepared_by_signature": "data:image/png;base64,SIGFAKE",
        "superintendent_signature": "",
    }


@pytest.fixture(scope="module")
def created_id():
    payload = _full_payload()
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    rid = body["id"]
    yield rid, body
    # cleanup
    requests.delete(f"{API}/daily-reports/{rid}", timeout=30)


# --- CRUD ---
class TestDailyReportCRUD:
    def test_create_returns_full_doc_and_no_id_leak(self, created_id):
        rid, body = created_id
        assert isinstance(body["id"], str) and len(body["id"]) > 0
        assert "_id" not in body
        assert body["project_name"].startswith("TEST_DR")
        assert body["report_date"] == "2026-01-15"
        assert body["prepared_by"] == "Test Foreman"
        assert len(body["masci_crews"]) == 2
        assert len(body["subcontractors"]) == 1
        assert len(body["visitors"]) == 1
        assert len(body["equipment"]) == 1
        assert len(body["materials"]) == 1
        assert len(body["activities"]) == 1
        assert len(body["photos"]) == 6
        assert len(body["weather_snapshots"]) == 3
        assert "created_at" in body

    def test_list_summary_no_id_and_counts(self, created_id):
        rid, _ = created_id
        r = requests.get(f"{API}/daily-reports", timeout=30)
        assert r.status_code == 200
        items = r.json()
        match = [x for x in items if x["id"] == rid]
        assert len(match) == 1, "Created report should appear in list"
        item = match[0]
        assert "_id" not in item
        assert item["photo_count"] == 6
        assert item["crew_count"] == 2
        assert item["sub_count"] == 1
        assert item["visitor_count"] == 1
        assert item["weather_summary"] == "75°F / Sunny"
        assert item["project_number"] == "TEST-25-23"
        assert item["prepared_by"] == "Test Foreman"

    def test_get_full_doc_preserves_nested_arrays(self, created_id):
        rid, _ = created_id
        r = requests.get(f"{API}/daily-reports/{rid}", timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert "_id" not in body
        assert body["id"] == rid
        assert body["masci_crews"][0]["trade"] == "Earthwork"
        assert body["masci_crews"][1]["foreman"] == "Mike"
        assert body["subcontractors"][0]["company"] == "ABC Striping"
        assert body["visitors"][0]["name"] == "Bob Inspector"
        assert body["equipment"][0]["description"] == "CAT 320 Excavator"
        assert body["materials"][0]["ticket_number"] == "T-9911"
        assert body["activities"][0]["activity"] == "Curb pour"
        assert body["weather_snapshots"][1]["temp_f"] == 80
        assert body["prepared_by_signature"].startswith("data:image/png")

    def test_get_404_for_unknown(self):
        r = requests.get(f"{API}/daily-reports/does-not-exist", timeout=30)
        assert r.status_code == 404

    def test_delete_and_verify_removed(self):
        # DEPLOY-FIX-001 · Workstream C3 — DR delete is permanently frozen
        # at HTTP 410 Gone. Daily Reports are historical-immutable records
        # (see /app/backend/routes/daily_reports.py:580). Hard delete is
        # no longer permitted; records remain accessible via GET. The test
        # name "delete_and_verify_removed" is retained for backwards-grep,
        # but the contract it locks in is now "delete-is-gone, record-stays."
        payload = _full_payload(prefix="TEST_DR_DEL")
        r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
        assert r.status_code == 200
        rid = r.json()["id"]
        d = requests.delete(f"{API}/daily-reports/{rid}", timeout=30)
        assert d.status_code == 410, (
            f"DR delete must return 410 Gone (historical-immutable doctrine); got {d.status_code}"
        )
        # Record must STILL be present — deletion is forbidden.
        g = requests.get(f"{API}/daily-reports/{rid}", timeout=30)
        assert g.status_code == 200, (
            f"DR record must persist after DELETE attempt; got {g.status_code}"
        )

    def test_delete_404_for_unknown(self):
        # DEPLOY-FIX-001 · Workstream C3 — even for unknown ids the
        # endpoint returns 410 (the operation itself is gone, not the
        # record). 404 is no longer reachable.
        r = requests.delete(f"{API}/daily-reports/nope-{os.urandom(4).hex()}", timeout=30)
        assert r.status_code == 410, (
            f"DR delete must return 410 Gone for any id; got {r.status_code}"
        )


# --- Validation ---
class TestDailyReportValidation:
    @pytest.mark.parametrize("missing", ["project_name", "location", "prepared_by", "report_date"])
    def test_missing_required_returns_422(self, missing):
        payload = _full_payload(prefix="TEST_DR_VAL")
        payload.pop(missing, None)
        r = requests.post(f"{API}/daily-reports", json=payload, timeout=30)
        assert r.status_code == 422, f"Expected 422 when {missing} missing, got {r.status_code}: {r.text}"


# --- Regression on other modules ---
class TestRegressionOtherModules:
    def test_inspections_get_works(self):
        r = requests.get(f"{API}/inspections", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_meetings_get_works(self):
        r = requests.get(f"{API}/meetings", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_jhas_get_works(self):
        r = requests.get(f"{API}/jhas", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_incidents_get_works(self):
        r = requests.get(f"{API}/incidents", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_inspection_post_minimal(self):
        # existing regression; quick smoke
        payload = {
            "project_name": "TEST_DR_REG_INSP",
            "location": "Port Orange",
            "inspection_date": "2026-01-15",
            "inspection_time": "10:00",
            "inspector_name": "Insp",
            "foreman_name": "Fore",
            "work_activity": "General",
        }
        r = requests.post(f"{API}/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        # cleanup
        requests.delete(f"{API}/inspections/{rid}", timeout=30)
