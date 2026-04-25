"""MASCI Inspection backend API tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def sample_payload():
    return {
        "project_name": "TEST_I-95 Resurfacing",
        "project_number": "TEST-001",
        "location": "TEST Mile Marker 50",
        "inspection_date": "2026-01-15",
        "inspection_time": "09:30",
        "operation": "Day",
        "inspector_name": "TEST Inspector Smith",
        "foreman_name": "TEST Foreman Jones",
        "crew_personnel": "Crew of 5",
        "subcontractors": "ABC Paving",
        "weather_conditions": "Sunny 75F",
        "work_activity": "Asphalt paving phase 2",
        "ppe_compliance": {"hard_hats": "Yes", "high_vis": "Yes", "boots": "Yes"},
        "equipment": {"applies": "Yes", "notes": "ok", "items": {"seat_belts": "Yes"}},
        "traffic_control": {"applies": "No", "notes": "", "items": {}},
        "mot_moving_trucks": {"applies": "No", "notes": "", "items": {}},
        "fall_protection": {"applies": "No", "notes": "", "items": {}},
        "excavation": {"applies": "No", "notes": "", "items": {}},
        "electrical": {"applies": "No", "notes": "", "items": {}},
        "concrete_paving": {"applies": "Yes", "notes": "hot work", "items": {"burn_protection": "Yes"}},
        "site_hazards": {"housekeeping": "Yes", "walking_surfaces": "Yes"},
        "hazards_observed": "Yes",
        "stop_work_issued": "No",
        "corrected_on_site": "Yes",
        "responsible_party": "Foreman Jones",
        "corrective_action_notes": "Cleaned up debris near MOT taper",
        "photos": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgAAIAAAUAAeImBZsAAAAASUVORK5CYII=",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=",
        ],
        "inspector_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgAAIAAAUAAeImBZsAAAAASUVORK5CYII=",
        "foreman_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgAAIAAAUAAeImBZsAAAAASUVORK5CYII=",
    }


# Health
def test_root_health(session):
    r = session.get(f"{API}/")
    assert r.status_code == 200
    assert r.json().get("ok") is True


# Create
class TestCreate:
    def test_create_full_payload(self, session, sample_payload):
        r = session.post(f"{API}/inspections", json=sample_payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "id" in data and isinstance(data["id"], str)
        assert "_id" not in data
        assert data["project_name"] == sample_payload["project_name"]
        assert data["photos"] == sample_payload["photos"]
        assert data["inspector_signature"] == sample_payload["inspector_signature"]
        assert data["equipment"]["applies"] == "Yes"
        assert "created_at" in data
        pytest.created_id = data["id"]

    def test_create_missing_required_returns_422(self, session):
        r = session.post(f"{API}/inspections", json={"project_name": "TEST_only"})
        assert r.status_code == 422


# List
class TestList:
    def test_list_returns_summaries(self, session):
        r = session.get(f"{API}/inspections")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 1
        first = items[0]
        for k in [
            "id", "project_name", "location", "inspection_date", "inspector_name",
            "foreman_name", "hazards_observed", "stop_work_issued", "photo_count", "created_at"
        ]:
            assert k in first, f"missing {k}"
        # sorted desc by created_at
        created_ats = [x["created_at"] for x in items if x.get("created_at")]
        assert created_ats == sorted(created_ats, reverse=True)
        # the just-created one should appear and have photo_count == 2
        match = [x for x in items if x["id"] == pytest.created_id]
        assert match, "created inspection not in list"
        assert match[0]["photo_count"] == 2
        assert "_id" not in match[0]


# Get by id
class TestGet:
    def test_get_by_id(self, session, sample_payload):
        r = session.get(f"{API}/inspections/{pytest.created_id}")
        assert r.status_code == 200
        data = r.json()
        assert "_id" not in data
        assert data["id"] == pytest.created_id
        assert data["work_activity"] == sample_payload["work_activity"]
        assert data["site_hazards"]["housekeeping"] == "Yes"
        assert len(data["photos"]) == 2

    def test_get_nonexistent_returns_404(self, session):
        r = session.get(f"{API}/inspections/does-not-exist-xyz")
        assert r.status_code == 404


# Delete
class TestDelete:
    def test_delete_then_404(self, session):
        r = session.delete(f"{API}/inspections/{pytest.created_id}")
        assert r.status_code == 200
        assert r.json().get("deleted") is True
        # verify gone
        r2 = session.get(f"{API}/inspections/{pytest.created_id}")
        assert r2.status_code == 404

    def test_delete_nonexistent_returns_404(self, session):
        r = session.delete(f"{API}/inspections/does-not-exist-xyz")
        assert r.status_code == 404
