"""MASCI Inspection backend API tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")


def _read_frontend_url():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return None


_fe_url = _read_frontend_url()
if _fe_url:
    BASE_URL = _fe_url
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
    # GET /api/health returns {ok: true, service: "masci-hub", ts: ...}
    r = session.get(f"{API}/health")
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


# ---- Grading: new fields persisted + surfaced in list summaries ----
class TestGrading:
    def _grade_payload(self, project_name, score=85, status="PASS", auto_fail=0, yes=10, no=2, total=12):
        return {
            "project_name": project_name,
            "project_number": "TEST-G",
            "location": "TEST Grade Lane",
            "inspection_date": "2026-01-16",
            "inspection_time": "10:00",
            "operation": "Day",
            "inspector_name": "TEST Grade Inspector",
            "foreman_name": "TEST Grade Foreman",
            "work_activity": "Grading verify",
            "ppe_compliance": {"hard_hats": "Yes"},
            "site_hazards": {"housekeeping": "Yes"},
            "hazards_observed": "No",
            "stop_work_issued": "No",
            "corrected_on_site": "N/A",
            "photos": [],
            "inspector_signature": "data:image/png;base64,iVBORw0KGgo=",
            "foreman_signature": "data:image/png;base64,iVBORw0KGgo=",
            "score": score,
            "status": status,
            "auto_fail_count": auto_fail,
            "graded_yes": yes,
            "graded_no": no,
            "graded_total": total,
        }

    def test_create_persists_grade_fields(self, session):
        payload = self._grade_payload("TEST_GRADE_PASS_85", score=85, status="PASS", auto_fail=0, yes=10, no=2, total=12)
        r = session.post(f"{API}/inspections", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["score"] == 85
        assert data["status"] == "PASS"
        assert data["auto_fail_count"] == 0
        assert data["graded_yes"] == 10
        assert data["graded_no"] == 2
        assert data["graded_total"] == 12
        pytest.grade_pass_id = data["id"]

        # GET by id confirms persistence
        g = session.get(f"{API}/inspections/{data['id']}")
        assert g.status_code == 200
        gd = g.json()
        assert gd["score"] == 85 and gd["status"] == "PASS" and gd["graded_total"] == 12

    def test_create_fail_with_auto_fail(self, session):
        payload = self._grade_payload("TEST_GRADE_FAIL_AF", score=80, status="FAIL", auto_fail=1, yes=8, no=2, total=10)
        r = session.post(f"{API}/inspections", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "FAIL"
        assert data["auto_fail_count"] == 1
        pytest.grade_fail_id = data["id"]

    def test_list_includes_grade_fields(self, session):
        r = session.get(f"{API}/inspections")
        assert r.status_code == 200
        items = r.json()
        for needed in ("score", "status", "auto_fail_count", "graded_yes", "graded_no", "graded_total"):
            assert needed in items[0], f"missing {needed} in summary"
        # find our created PASS one
        pass_match = [x for x in items if x["id"] == pytest.grade_pass_id]
        assert pass_match
        assert pass_match[0]["score"] == 85
        assert pass_match[0]["status"] == "PASS"
        assert pass_match[0]["graded_total"] == 12
        # FAIL one
        fail_match = [x for x in items if x["id"] == pytest.grade_fail_id]
        assert fail_match and fail_match[0]["status"] == "FAIL" and fail_match[0]["auto_fail_count"] == 1

    def test_create_without_grade_returns_defaults(self, session):
        # backward-compat: payload missing score fields -> server should accept and default
        payload = self._grade_payload("TEST_GRADE_NONE")
        for k in ("score", "status", "auto_fail_count", "graded_yes", "graded_no", "graded_total"):
            payload.pop(k, None)
        r = session.post(f"{API}/inspections", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data.get("score") is None
        assert data.get("auto_fail_count") in (0, None)
        pytest.grade_none_id = data["id"]

    def test_cleanup_grade_inspections(self, session):
        for attr in ("grade_pass_id", "grade_fail_id", "grade_none_id"):
            iid = getattr(pytest, attr, None)
            if iid:
                session.delete(f"{API}/inspections/{iid}")
