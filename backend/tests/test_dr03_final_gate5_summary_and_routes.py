from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from routes.daily_summary import register_daily_summary_routes
from routes.operational_records import _project_legacy
from lib.synthetic_dr_filter import is_synthetic_dr, apply_synthetic_dr_exclusion


class _FakeCollection:
    def __init__(self):
        self.docs = []

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    async def update_one(self, q, update, upsert=False):
        return type("R", (), {"matched_count": 1})()

    async def update_many(self, q, update):
        return type("R", (), {"matched_count": 0})()

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("R", (), {"inserted_id": "x"})()


class _FakeDB:
    def __init__(self):
        self.daily_reports = _FakeCollection()
        self.tenant_ai_capabilities = _FakeCollection()
        self.operational_facts = _FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


def _build_client() -> TestClient:
    db = _FakeDB()
    router = APIRouter(prefix="/api")
    register_daily_summary_routes(router, db=db, rate_limit_public_post=lambda: True)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_summary_draft_returns_live_fixture_totals_even_when_ai_disabled() -> None:
    client = _build_client()
    payload = {
        "project_name": "D Curb Test",
        "project_number": "27-DR03",
        "report_date": "2026-07-15",
        "prepared_by": "Jaymn Judd",
        "location": "North lot",
        "weather_summary": "Sunny",
        "masci_crews": [{
            "employee_id": "E-1",
            "name": "Crew One",
            "trade": "Concrete",
            "start_time": "06:00",
            "stop_time": "17:45",
            "lunch_minutes": 30,
        }],
        "subcontractors": [{"company": "Acme Concrete", "count": 1, "hours": 11}],
        "equipment": [{"description": "Skid Steer", "hours_used": 4, "idle_hours": 6}],
        "production": [{"description": "D curb", "quantity": 875, "unit": "LF", "percent_complete": 65}],
        "photos": ["a", "b", "c", "d", "e", "f"],
    }
    response = client.post("/api/daily-reports/summary/draft", json={"payload": payload})
    assert response.status_code == 200, response.text
    body = response.json()
    summary_input = body["summary_input"]
    assert summary_input["labor"]["employee_count"] == 1
    assert summary_input["labor"]["total_employee_hours"] == 11.25
    assert summary_input["subcontractors"]["subcontractor_count"] == 1
    assert summary_input["subcontractors"]["total_hours"] == 11.0
    assert summary_input["equipment"]["equipment_count"] == 1
    assert summary_input["equipment"]["total_run_hours"] == 4.0
    assert summary_input["equipment"]["total_idle_hours"] == 6.0
    assert summary_input["photos"]["photo_count"] == 6
    assert isinstance(body["summary_text"], str) and body["summary_text"].strip()
    assert body["enabled"] is False
    assert body["reason_disabled"]
    assert body["mode"] == "deterministic_fallback"
    assert "debug_payloads" not in body


def test_operational_record_viewer_uses_governed_daily_report_alias() -> None:
    projected = _project_legacy({"id": "dr-123"})
    assert projected["viewer_route"] == "/daily-reports/dr-123"


def test_certification_records_are_classified_as_hidden_everywhere() -> None:
    doc = {"certification_record": True, "synthetic_record": True, "hidden_from_operations": True}
    assert is_synthetic_dr(doc) is True
    query = apply_synthetic_dr_exclusion({})
    clauses = query["$and"]
    assert {"certification_record": {"$ne": True}} in clauses
    assert {"synthetic_record": {"$ne": True}} in clauses
    assert {"hidden_from_operations": {"$ne": True}} in clauses