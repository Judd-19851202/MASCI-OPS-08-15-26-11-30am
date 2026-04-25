"""Backend tests for Accident / Incident Reports endpoints."""
import os
import pytest
import requests


def _base_url():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


BASE_URL = _base_url()
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _payload(name="TEST_INC_Lift_NearMiss", severity="medical"):
    return {
        "project_name": name,
        "project_number": "TEST-INC-01",
        "location": "TEST Lay-down Yard",
        "incident_date": "2026-01-22",
        "incident_time": "14:30",
        "reported_date": "2026-01-22",
        "reported_by": "TEST Foreman Jones",
        "supervisor_name": "TEST Supt Smith",
        "incident_type": "Injury / Illness",
        "severity": severity,
        "osha_recordable": "Yes",
        "work_stopped": "Yes",
        "person_name": "TEST Worker A",
        "person_role": "Laborer",
        "person_employer": "MASCI",
        "person_years_experience": "3",
        "body_part": "Hand - Left",
        "injury_nature": "Laceration",
        "treatment_provided": "Stitches at urgent care",
        "medical_facility": "TEST Urgent Care",
        "sent_home": "Yes",
        "description": "While moving a panel, hand was pinched between panel and rebar.",
        "immediate_cause": "Inadequate hand placement",
        "contributing_factors": "Rushed schedule, gloves not cut-rated",
        "root_causes": {"training": True, "ppe": True, "supervision": False},
        "root_cause_notes": "Cut-rated gloves not provided to crew",
        "witnesses": [
            {"name": "TEST Witness A", "statement": "Saw it happen at 2:30pm"},
            {"name": "TEST Witness B", "statement": "Was helping with the lift"},
        ],
        "immediate_actions_taken": "First aid, transported to clinic",
        "corrective_actions": "Issue cut-rated gloves to all laborers",
        "responsible_party": "Safety Manager",
        "target_completion_date": "2026-01-29",
        "notified_safety_manager": "Yes",
        "notified_pm": "Yes",
        "notified_gc": "Yes",
        "notified_owner": "No",
        "notified_osha": "No",
        "notified_other": "Insurance carrier",
        "photos": [
            "data:image/png;base64,iVBORw0KGgo=",
            "data:image/png;base64,iVBORw0KGgo=",
        ],
        "reporter_signature": "data:image/png;base64,iVBORw0KGgo=",
        "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
    }


class TestIncidents:
    def test_create_incident(self, session):
        r = session.post(f"{API}/incidents", json=_payload())
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d and isinstance(d["id"], str)
        assert "_id" not in d
        assert d["severity"] == "medical"
        assert d["incident_type"] == "Injury / Illness"
        assert len(d["witnesses"]) == 2
        assert len(d["photos"]) == 2
        assert d["root_causes"]["training"] is True
        assert d["reporter_signature"].startswith("data:image/png;base64")
        assert "created_at" in d
        pytest.incident_id = d["id"]

    def test_create_near_miss(self, session):
        r = session.post(
            f"{API}/incidents",
            json=_payload(name="TEST_INC_NearMiss", severity="near_miss"),
        )
        assert r.status_code == 200
        d = r.json()
        assert d["severity"] == "near_miss"
        pytest.incident_nm_id = d["id"]

    def test_create_missing_required_returns_422(self, session):
        r = session.post(f"{API}/incidents", json={"project_name": "TEST_only"})
        assert r.status_code == 422

    def test_list_incidents_summaries(self, session):
        r = session.get(f"{API}/incidents")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 2
        first = items[0]
        for k in [
            "id", "project_name", "location", "incident_date", "incident_type",
            "severity", "person_name", "reported_by", "osha_recordable",
            "photo_count", "created_at",
        ]:
            assert k in first, f"missing {k} in incident summary"
        assert "_id" not in first
        # sorted desc by created_at
        cas = [x["created_at"] for x in items if x.get("created_at")]
        assert cas == sorted(cas, reverse=True)
        match = [x for x in items if x["id"] == pytest.incident_id]
        assert match
        assert match[0]["photo_count"] == 2
        assert match[0]["severity"] == "medical"
        assert match[0]["osha_recordable"] == "Yes"

    def test_get_incident_full(self, session):
        r = session.get(f"{API}/incidents/{pytest.incident_id}")
        assert r.status_code == 200
        d = r.json()
        assert "_id" not in d
        assert d["id"] == pytest.incident_id
        assert d["root_causes"]["training"] is True
        assert d["root_causes"]["ppe"] is True
        assert len(d["witnesses"]) == 2
        assert d["witnesses"][0]["name"] == "TEST Witness A"
        assert len(d["photos"]) == 2
        assert d["reporter_signature"].startswith("data:image/png;base64")

    def test_get_nonexistent_incident_404(self, session):
        r = session.get(f"{API}/incidents/does-not-exist-xyz")
        assert r.status_code == 404

    def test_delete_incident_then_404(self, session):
        r = session.delete(f"{API}/incidents/{pytest.incident_id}")
        assert r.status_code == 200
        assert r.json().get("deleted") is True
        r2 = session.get(f"{API}/incidents/{pytest.incident_id}")
        assert r2.status_code == 404
        # double delete -> 404
        r3 = session.delete(f"{API}/incidents/{pytest.incident_id}")
        assert r3.status_code == 404

    def test_delete_nonexistent_incident_404(self, session):
        r = session.delete(f"{API}/incidents/does-not-exist-xyz")
        assert r.status_code == 404

    def test_cleanup_near_miss(self, session):
        nm = getattr(pytest, "incident_nm_id", None)
        if nm:
            session.delete(f"{API}/incidents/{nm}")


# ---- Regression: existing modules still work ----
class TestRegression:
    def test_inspections_list_ok(self, session):
        r = session.get(f"{API}/inspections")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_meetings_list_ok(self, session):
        r = session.get(f"{API}/meetings")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_jhas_list_ok(self, session):
        r = session.get(f"{API}/jhas")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
