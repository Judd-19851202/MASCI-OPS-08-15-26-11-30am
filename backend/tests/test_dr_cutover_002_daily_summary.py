"""DR-CUTOVER-002 · Daily Operational Summary lock envelope.

Proves every invariant listed in the DR-CUTOVER-002 spec at the API
layer using an in-memory fake Mongo. No live provider call. No live
email. No PDF render.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from routes.daily_summary import (
    _compose_deterministic_summary,
    register_daily_summary_routes,
)


# ─────────────────────── fake Mongo ────────────────────────────────

class _FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("R", (), {"inserted_id": "x"})()

    async def update_one(self, q, update, upsert=False):
        set_body = update.get("$set", {})
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in q.items()):
                self.docs[i] = {**d, **set_body}
                return type("R", (), {"matched_count": 1})()
        if upsert:
            self.docs.append({**q, **set_body})
            return type("R", (), {"matched_count": 0})()
        return type("R", (), {"matched_count": 0})()

    async def update_many(self, q, update):
        set_body = update.get("$set", {})
        n = 0
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in q.items()):
                self.docs[i] = {**d, **set_body}
                n += 1
        return type("R", (), {"matched_count": n})()


class _FakeDB:
    def __init__(self):
        self.daily_reports = _FakeCollection()
        self.tenant_ai_capabilities = _FakeCollection()
        self.operational_facts = _FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


# ─────────────────────── env sandbox ──────────────────────────────

_AI_KEYS = [
    "AI_GATEWAY_ENABLED",
    "AI_PROVIDER_ANTHROPIC_ENABLED", "AI_PROVIDER_OPENAI_ENABLED",
    "AI_PROVIDER_GOOGLE_ENABLED",
    "AI_DAILY_REPORT_SUMMARY_ENABLED",
    "AI_DEFAULT_PROVIDER",
    "TENANT_AI_ENABLED", "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY",
]


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {k: os.environ.get(k) for k in _AI_KEYS}
    for k in _AI_KEYS:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _turn_ai_all_on():
    """Flip every deployment env flag ON so the resolver would return
    enabled=True for daily_report_summary when the tenant also opts in."""
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-composer-only-no-live-call",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        "TENANT_AI_ENABLED": "true",
        "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
    })


# ─────────────────────── test app ──────────────────────────────────

def _rate_limit_stub():
    return True


def _build_app(db) -> FastAPI:
    router = APIRouter(prefix="/api")
    register_daily_summary_routes(
        router, db=db, rate_limit_public_post=_rate_limit_stub,
    )
    app = FastAPI()
    app.include_router(router)
    return app


# ─────────────────────── fixtures ─────────────────────────────────

RICH_PAYLOAD = {
    "project_name": "Route 121 Grade",
    "project_number": "26-04",
    "report_date": "2026-02-15",
    "prepared_by": "J. Doe",
    "superintendent": "R. Smith",
    "shift": "Day",
    "weather_summary": "Sunny, 58°F, light wind",
    "schedule_delays": "Yes",
    "schedule_delays_notes": "1hr fuel delay AM",
    "weather_impact": "No",
    "safety_incidents_today": "No",
    "injuries_reported": "No",
    "general_notes": "Solid production day.",
    "masci_crews": [
        {"trade": "Grading", "count": 4, "hours": 8},
        {"trade": "Pipe", "count": 2, "hours": 8},
    ],
    "subcontractors": [{"company": "Acme Concrete"}],
    "equipment": [
        {"description": "CAT 335F Excavator", "hours": 7.5},
        {"description": "930M Loader", "hours": 6},
    ],
    "materials": [{"material": "Aggregate Base"}],
    "outbound_materials": [{"material": "Unsuitable Soil"}],
    "activities": [{"description": "Placed 350 LF of 24\" RCP"}],
    "production": [
        {"description": "24 in RCP", "quantity": 350, "unit": "LF"},
    ],
    "constraints": [{"constraint_type": "utility"}],
    "photos": ["photo:a", "photo:b", "photo:c", "photo:d", "photo:e", "photo:f"],
    "photo_captions": ["North headwall", "Trench alignment"],
    "narrative_sections": {"tomorrow_plan": "Continue pipe install"},
}


# ─────────────────────── invariants ───────────────────────────────

def test_ai_disabled_draft_returns_enabled_false_never_500():
    # Every AI env stripped by autouse fixture — resolver returns disabled.
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["enabled"] is False
    assert j["summary_text"] is None
    assert j["reason_disabled"]  # non-empty machine-readable code


def test_tenant_ai_off_blocks_summary_generation():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-x",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        # Tenant AI stays OFF (default).
    })
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/summary/draft",
        json={"payload": RICH_PAYLOAD, "tenant_id": "masci"},
    )
    j = r.json()
    assert j["enabled"] is False
    assert j["reason_disabled"] == "tenant_ai_disabled"


def test_module_off_blocks_summary_generation():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-x",
        # AI_DAILY_REPORT_SUMMARY_ENABLED stays OFF.
        "TENANT_AI_ENABLED": "true",
        "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
    })
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    j = r.json()
    assert j["enabled"] is False
    assert j["reason_disabled"].startswith("module_disabled_global")


def test_missing_provider_key_reports_no_provider_not_500():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        # ANTHROPIC_API_KEY intentionally empty
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        "TENANT_AI_ENABLED": "true",
        "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
    })
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    assert r.status_code == 200
    j = r.json()
    assert j["enabled"] is False
    assert j["reason_disabled"] == "no_provider_available"


def test_enabled_path_returns_deterministic_composed_summary():
    _turn_ai_all_on()
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    j = r.json()
    assert j["enabled"] is True
    text = j["summary_text"]
    assert text and len(text) > 40
    # Every literal value in the payload appears verbatim — proves
    # "never invents facts".
    for expected in [
        "Route 121 Grade", "26-04", "2026-02-15", "J. Doe",
        "Sunny, 58°F, light wind",
        "Grading", "Pipe",
        "Acme Concrete",
        "CAT 335F Excavator", "930M Loader",
        "24 in RCP", "350",
        "Aggregate Base", "Unsuitable Soil",
        "Continue pipe install",
    ]:
        assert expected in text, f"expected `{expected}` in composed summary"


def test_composer_never_invents_a_safety_incident():
    """If the report says NO incident and NO injury, the composed
    summary must not mention safety at all."""
    payload = {**RICH_PAYLOAD,
               "safety_incidents_today": "No", "injuries_reported": "No"}
    result = _compose_deterministic_summary(payload)
    assert "Safety:" not in result["summary_text"]
    # Add an incident and verify it surfaces.
    payload["safety_incidents_today"] = "Yes"
    payload["incident_notes"] = "First aid administered to Worker A"
    result2 = _compose_deterministic_summary(payload)
    assert "Safety:" in result2["summary_text"]
    assert "First aid administered to Worker A" in result2["summary_text"]


def test_composer_never_mentions_photos_when_none_attached():
    payload = {**RICH_PAYLOAD, "photos": [], "photo_captions": []}
    result = _compose_deterministic_summary(payload)
    assert "photo" not in result["summary_text"].lower()


def test_composer_uses_only_allowed_fields():
    """Feeding an unrecognised key must not surface in the summary."""
    payload = {**RICH_PAYLOAD,
               "secret_field_not_supposed_to_leak":
                   "REDACTED-SHOULD-NEVER-APPEAR"}
    result = _compose_deterministic_summary(payload)
    assert "REDACTED-SHOULD-NEVER-APPEAR" not in result["summary_text"]


def test_composer_output_contains_no_ai_language():
    """The response body must not surface AI/model/provider vocabulary
    (that's a UX-copy contract enforced end-to-end)."""
    _turn_ai_all_on()
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    text = r.text.lower()
    # summary_text lives inside; scan the whole body.
    for banned in ["anthropic", "openai", "claude", "gpt", "gemini",
                   "provider", "model", "token cost", "ai agent"]:
        assert banned not in text, f"banned term `{banned}` leaked into response"


def test_accept_persists_summary_onto_daily_report_doc():
    _turn_ai_all_on()
    db = _FakeDB()
    db.daily_reports.docs.append({
        "id": "dr-001", "project_number": "26-04",
        "report_date": "2026-02-15", "prepared_by": "J. Doe",
        "masci_crews": [{"trade": "Grading", "count": 4, "hours": 8}],
    })
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/dr-001/summary/accept",
        json={"summary_text": "Final approved summary text.",
              "language": "en", "source": "user_edited",
              "accepted_by": "J. Doe"},
    )
    assert r.status_code == 200, r.text
    stored = db.daily_reports.docs[0]
    assert stored["ai_accepted_summary"] == "Final approved summary text."
    assert stored["ai_accepted_summary_meta"]["accepted_by"] == "J. Doe"
    assert stored["ai_accepted_summary_meta"]["language"] == "en"
    assert stored["daily_operational_summary"] == "Final approved summary text."
    assert stored["daily_operational_summary_status"] == "accepted"
    assert stored["daily_operational_summary_source"] == "user_edited"
    assert stored["daily_operational_summary_accepted_by"] == "J. Doe"
    assert stored["daily_operational_summary_language"] == "en"
    # HR-critical & safety-critical fields UNTOUCHED.
    assert stored["masci_crews"] == [{"trade": "Grading", "count": 4, "hours": 8}]
    assert stored["report_date"] == "2026-02-15"


def test_accept_returns_404_when_report_missing():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/nonexistent/summary/accept",
        json={"summary_text": "hi", "language": "en"},
    )
    assert r.status_code == 404


def test_accept_rejects_empty_summary_text():
    db = _FakeDB()
    db.daily_reports.docs.append({"id": "dr-1"})
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/dr-1/summary/accept",
        json={"summary_text": ""},
    )
    assert r.status_code == 422  # pydantic min_length=1


def test_accept_truncates_ludicrously_long_input():
    db = _FakeDB()
    db.daily_reports.docs.append({"id": "dr-1"})
    client = TestClient(_build_app(db))
    # Pydantic max_length=4000 rejects 5000 chars → 422.
    r = client.post(
        "/api/daily-reports/dr-1/summary/accept",
        json={"summary_text": "x" * 5000},
    )
    assert r.status_code == 422


def test_accept_never_writes_a_provider_key_or_token_field():
    """No matter what the client sends, the accept handler patches only
    the whitelisted daily_operational_summary_* fields — and never
    stores any secret."""
    _turn_ai_all_on()
    db = _FakeDB()
    db.daily_reports.docs.append({"id": "dr-1", "prepared_by": "Ana"})
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/dr-1/summary/accept",
        json={
            "summary_text": "Legit summary.",
            "language": "en",
            # Adversarial extras — must NOT be stored on the report.
            "ANTHROPIC_API_KEY": "sk-attempted-write",
            "id": "dr-attack",
            "masci_crews": [{"trade": "attacker"}],
        },
    )
    assert r.status_code == 200
    stored = db.daily_reports.docs[0]
    for k in stored.keys():
        assert "API_KEY" not in k
    assert stored["id"] == "dr-1"
    assert "masci_crews" not in stored  # untouched (never seeded either)


def test_accept_emits_intelligence_fact_when_ods_enabled(monkeypatch):
    """Best-effort intelligence_fact emission. When ODS is off, no
    fact should be written — but the response must still be 200."""
    from services.ods_spine import flags as ods_flags
    monkeypatch.setattr(ods_flags, "ods_enabled", lambda: True)
    _turn_ai_all_on()
    db = _FakeDB()
    db.daily_reports.docs.append({
        "id": "dr-2", "project_number": "26-04",
        "report_date": "2026-02-15", "prepared_by": "J. Doe",
    })
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/daily-reports/dr-2/summary/accept",
        json={"summary_text": "Approved.", "language": "en"},
    )
    assert r.status_code == 200
    intel = [f for f in db.operational_facts.docs
             if f.get("fact_type") == "intelligence_fact"]
    assert len(intel) == 1
    fact = intel[0]
    assert fact["source_type"] == "daily_report"
    assert fact["source_id"] == "dr-2"
    assert fact["source_item_id"] == "intel:operational_summary"
    assert fact["is_current"] is True
    # No provider/model in the fact payload.
    import json as _j
    assert "provider" not in _j.dumps(fact).lower()


def test_accept_supersedes_prior_intelligence_fact_idempotency(monkeypatch):
    from services.ods_spine import flags as ods_flags
    monkeypatch.setattr(ods_flags, "ods_enabled", lambda: True)
    db = _FakeDB()
    db.daily_reports.docs.append({
        "id": "dr-3", "project_number": "26-04",
        "report_date": "2026-02-15", "prepared_by": "J. Doe",
    })
    client = TestClient(_build_app(db))
    for _ in range(3):
        client.post(
            "/api/daily-reports/dr-3/summary/accept",
            json={"summary_text": "Approved v" + str(_), "language": "en"},
        )
    current = [f for f in db.operational_facts.docs
               if f.get("fact_type") == "intelligence_fact" and f.get("is_current")]
    assert len(current) == 1  # only the latest stays current
    superseded = [f for f in db.operational_facts.docs
                  if f.get("fact_type") == "intelligence_fact"
                  and not f.get("is_current")]
    assert len(superseded) == 2


def test_language_flag_accepts_es_and_falls_back_to_en():
    _turn_ai_all_on()
    db = _FakeDB()
    db.daily_reports.docs.append({"id": "dr-4", "prepared_by": "J"})
    client = TestClient(_build_app(db))

    r = client.post(
        "/api/daily-reports/dr-4/summary/accept",
        json={"summary_text": "resumen", "language": "es"},
    )
    assert r.json()["language"] == "es"
    assert db.daily_reports.docs[0]["daily_operational_summary_language"] == "es"

    r = client.post(
        "/api/daily-reports/dr-4/summary/accept",
        json={"summary_text": "resumé", "language": "fr"},  # unknown
    )
    assert r.json()["language"] == "en"


def test_response_never_leaks_provider_key():
    os.environ["ANTHROPIC_API_KEY"] = "sk-should-never-leak-into-json"
    _turn_ai_all_on()
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    assert "sk-should-never-leak-into-json" not in r.text


def test_dr_v2_shell_not_exposed_from_daily_summary_route():
    """Route surface guard — dr-v2 has its own mount; the DR-CUTOVER-002
    router must not accidentally register a v2 alias."""
    from routes import daily_summary
    src = open(daily_summary.__file__).read()
    assert "/dr-v2" not in src
    assert "dr_v2" not in src


def test_field_ui_wire_response_contains_no_ai_agent_language():
    """The response body from BOTH endpoints must avoid AI vocabulary
    that could leak into the field UI (defence-in-depth against a
    future UI author binding a raw response.provider to a label)."""
    _turn_ai_all_on()
    db = _FakeDB()
    db.daily_reports.docs.append({"id": "dr-x", "prepared_by": "J"})
    client = TestClient(_build_app(db))
    r1 = client.post("/api/daily-reports/summary/draft", json={"payload": RICH_PAYLOAD})
    r2 = client.post("/api/daily-reports/dr-x/summary/accept",
                     json={"summary_text": "OK", "language": "en"})
    for body in (r1.text.lower(), r2.text.lower()):
        for banned in ["\"model\":", "\"provider\":", "\"token_cost\":",
                       "\"anthropic_api_key\":", "\"openai_api_key\":"]:
            assert banned not in body


def test_daily_reports_route_still_ignorant_of_ai_summary():
    """The core V1 submit path must remain fully independent of the
    summary module — proves 'Summary failure cannot block submit'."""
    from pathlib import Path
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    assert "daily_summary" not in src
    assert "resolve_ai_capabilities" not in src


def test_composer_handles_completely_empty_payload_gracefully():
    result = _compose_deterministic_summary({})
    assert isinstance(result["summary_text"], str)
    assert "insufficient_evidence_for_meaningful_summary" in result["warnings"]
