"""Backend tests for Site Safety Meetings (toolbox talks) and JHA endpoints."""
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


# ============================================================
# Meetings
# ============================================================
def _meeting_payload(name="TEST_TBT_Daily Huddle"):
    return {
        "project_name": name,
        "project_number": "TEST-M-01",
        "location": "TEST Lot A, MM 50",
        "meeting_date": "2026-01-20",
        "meeting_time": "07:00",
        "conducted_by": "TEST Foreman Jones",
        "topic": "Heat Illness Prevention",
        "topic_category": "Health",
        "hazards_reviewed": "Heat, dehydration, sun exposure",
        "discussion_notes": "Drink water every 15 min, take shade breaks.",
        "references_cited": "OSHA 1926.95",
        "action_items": "Refill water cooler.",
        "attendees": [
            {"name": "TEST Worker A", "signature": "data:image/png;base64,iVBORw0KGgo="},
            {"name": "TEST Worker B", "signature": "data:image/png;base64,iVBORw0KGgo="},
            {"name": "TEST Worker C", "signature": "data:image/png;base64,iVBORw0KGgo="},
        ],
        "photos": ["data:image/png;base64,iVBORw0KGgo="],
        "conductor_signature": "data:image/png;base64,iVBORw0KGgo=",
    }


class TestMeetings:
    def test_create_meeting(self, session):
        r = session.post(f"{API}/meetings", json=_meeting_payload())
        assert r.status_code == 200, r.text
        data = r.json()
        assert "id" in data and isinstance(data["id"], str)
        assert "_id" not in data
        assert data["project_name"].startswith("TEST_TBT_")
        assert data["topic"] == "Heat Illness Prevention"
        assert len(data["attendees"]) == 3
        assert "created_at" in data
        pytest.meeting_id = data["id"]

    def test_create_meeting_missing_required_returns_422(self, session):
        r = session.post(f"{API}/meetings", json={"project_name": "TEST_only"})
        assert r.status_code == 422

    def test_list_meetings_summaries(self, session):
        r = session.get(f"{API}/meetings")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        first = items[0]
        for k in [
            "id", "project_name", "location", "meeting_date", "conducted_by",
            "topic", "topic_category", "attendee_count", "created_at",
        ]:
            assert k in first, f"missing {k} in summary"
        assert "_id" not in first
        # sorted desc by created_at
        cas = [x["created_at"] for x in items if x.get("created_at")]
        assert cas == sorted(cas, reverse=True)
        match = [x for x in items if x["id"] == pytest.meeting_id]
        assert match and match[0]["attendee_count"] == 3

    def test_get_meeting_full(self, session):
        r = session.get(f"{API}/meetings/{pytest.meeting_id}")
        assert r.status_code == 200
        d = r.json()
        assert "_id" not in d
        assert d["id"] == pytest.meeting_id
        assert len(d["attendees"]) == 3
        assert d["attendees"][0]["signature"].startswith("data:image/png;base64")
        assert d["conductor_signature"].startswith("data:image/png;base64")
        assert len(d["photos"]) == 1

    def test_get_nonexistent_meeting_404(self, session):
        r = session.get(f"{API}/meetings/does-not-exist-xyz")
        assert r.status_code == 404

    def test_delete_meeting_then_404(self, session):
        r = session.delete(f"{API}/meetings/{pytest.meeting_id}")
        assert r.status_code == 200
        assert r.json().get("deleted") is True
        r2 = session.get(f"{API}/meetings/{pytest.meeting_id}")
        assert r2.status_code == 404

    def test_delete_nonexistent_meeting_404(self, session):
        r = session.delete(f"{API}/meetings/does-not-exist-xyz")
        assert r.status_code == 404


# ============================================================
# JHAs
# ============================================================
def _jha_payload(name="TEST_JHA_Trench Excavation"):
    return {
        "project_name": name,
        "project_number": "TEST-J-01",
        "location": "TEST Trench B, MM 51",
        "jha_date": "2026-01-21",
        "job_title": "Trench excavation 6ft",
        "job_description": "Excavate 6ft trench for storm drain",
        "crew_lead": "TEST Crew Lead Smith",
        "crew_members": "5 laborers + 1 operator",
        "ppe_required": {"hard_hat": True, "high_vis": True, "boots": True, "gloves": True},
        "permits_required": {"excavation": True, "confined_space": False},
        "tools_equipment": "Mini-ex, shoring, ladder",
        "task_steps": [
            {"description": "Set up MOT", "hazards": "Traffic", "controls": "Cones, flagger"},
            {"description": "Excavate", "hazards": "Cave-in", "controls": "Bench/slope, daily inspection"},
            {"description": "Place pipe", "hazards": "Crush", "controls": "Tagline, hand signals"},
        ],
        "stop_work_acknowledged": "Yes",
        "nearest_hospital": "TEST Hospital, 3 mi",
        "emergency_contact": "911 / Foreman x123",
        "crew_signoffs": [
            {"name": "TEST Sign A", "signature": "data:image/png;base64,iVBORw0KGgo="},
            {"name": "TEST Sign B", "signature": "data:image/png;base64,iVBORw0KGgo="},
        ],
        "foreman_signature": "data:image/png;base64,iVBORw0KGgo=",
        "photos": ["data:image/png;base64,iVBORw0KGgo="],
    }


class TestJhas:
    def test_create_jha(self, session):
        r = session.post(f"{API}/jhas", json=_jha_payload())
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d and isinstance(d["id"], str)
        assert "_id" not in d
        assert d["job_title"] == "Trench excavation 6ft"
        assert len(d["task_steps"]) == 3
        assert len(d["crew_signoffs"]) == 2
        assert d["ppe_required"]["hard_hat"] is True
        assert "created_at" in d
        pytest.jha_id = d["id"]

    def test_create_jha_missing_required_returns_422(self, session):
        r = session.post(f"{API}/jhas", json={"project_name": "TEST_only"})
        assert r.status_code == 422

    def test_list_jhas_summaries(self, session):
        r = session.get(f"{API}/jhas")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        first = items[0]
        for k in [
            "id", "project_name", "location", "jha_date", "crew_lead",
            "job_title", "step_count", "signoff_count", "created_at",
        ]:
            assert k in first, f"missing {k} in JHA summary"
        assert "_id" not in first
        match = [x for x in items if x["id"] == pytest.jha_id]
        assert match
        assert match[0]["step_count"] == 3
        assert match[0]["signoff_count"] == 2

    def test_get_jha_full(self, session):
        r = session.get(f"{API}/jhas/{pytest.jha_id}")
        assert r.status_code == 200
        d = r.json()
        assert "_id" not in d
        assert d["id"] == pytest.jha_id
        assert d["task_steps"][1]["hazards"] == "Cave-in"
        assert d["crew_signoffs"][0]["signature"].startswith("data:image/png;base64")
        assert d["foreman_signature"].startswith("data:image/png;base64")

    def test_get_nonexistent_jha_404(self, session):
        r = session.get(f"{API}/jhas/does-not-exist-xyz")
        assert r.status_code == 404

    def test_delete_jha_then_404(self, session):
        r = session.delete(f"{API}/jhas/{pytest.jha_id}")
        assert r.status_code == 200
        assert r.json().get("deleted") is True
        r2 = session.get(f"{API}/jhas/{pytest.jha_id}")
        assert r2.status_code == 404

    def test_delete_nonexistent_jha_404(self, session):
        r = session.delete(f"{API}/jhas/does-not-exist-xyz")
        assert r.status_code == 404
