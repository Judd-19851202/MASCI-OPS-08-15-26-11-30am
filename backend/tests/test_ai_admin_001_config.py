"""
AI-ADMIN-001 · Admin AI Configuration Center — lock envelope.

Proves the eight-pillar contract:

1. No secret values ever leave the backend.
2. Admin-only enforcement (strict, PM rejected).
3. Tenant isolation on updates.
4. Allow-list on writes (extra fields silently dropped).
5. Update is idempotent + version-stamped.
6. Audit entry written on every mutation.
7. Provider connection-test endpoint returns booleans only, never keys.
8. AI OFF invariants still hold — Daily Report submit does not depend
   on any new admin route.

All tests use an in-memory fake Mongo — no real DB required.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Header
from fastapi.testclient import TestClient


# ─────────────────────── fake Mongo ────────────────────────────────

class _FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                out = {k: v for k, v in d.items() if k != "_id"}
                return out
        return None

    def find(self, q=None, projection=None):
        q = q or {}
        matched = [
            {k: v for k, v in d.items() if k != "_id"}
            for d in self.docs
            if all(d.get(k) == v for k, v in q.items())
        ]
        return _FakeCursor(matched)

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("R", (), {"inserted_id": "x"})()

    async def update_one(self, q, update, upsert=False):
        set_body = update.get("$set", {})
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in q.items()):
                self.docs[i] = {**d, **set_body}
                return type("R", (), {"matched_count": 1, "modified_count": 1})()
        if upsert:
            self.docs.append({**q, **set_body})
            return type("R", (), {"matched_count": 0, "upserted_id": "x"})()
        return type("R", (), {"matched_count": 0, "modified_count": 0})()


class _FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)
        self._sort = None
        self._limit = None

    def sort(self, key, direction=1):
        rev = direction < 0
        self.docs.sort(key=lambda d: d.get(key) or "", reverse=rev)
        return self

    def limit(self, n):
        self._limit = int(n)
        return self

    async def to_list(self, length=None):
        n = self._limit or length or len(self.docs)
        return self.docs[:n]


class _FakeDB:
    def __init__(self):
        self.tenant_ai_capabilities = _FakeCollection()
        self.tenant_ai_capability_audit = _FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


# ─────────────────────── env sandbox ──────────────────────────────

_AI_KEYS = [
    "AI_GATEWAY_ENABLED",
    "AI_PROVIDER_ANTHROPIC_ENABLED", "AI_PROVIDER_OPENAI_ENABLED",
    "AI_PROVIDER_GOOGLE_ENABLED",
    "AI_DEFAULT_PROVIDER",
    "AI_DAILY_REPORT_SUMMARY_ENABLED", "AI_PHOTO_VISION_ENABLED",
    "AI_PM_INTELLIGENCE_ENABLED", "AI_ADMIN_INTELLIGENCE_ENABLED",
    "AI_SAFETY_INTELLIGENCE_ENABLED", "AI_TRANSLATION_ENABLED",
    "TENANT_AI_ENABLED",
    "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED",
    "TENANT_AI_PHOTO_INTELLIGENCE_ENABLED",
    "TENANT_AI_PM_INTELLIGENCE_ENABLED",
    "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED",
    "TENANT_AI_SAFETY_INTELLIGENCE_ENABLED",
    "TENANT_AI_TRANSLATION_ENABLED",
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


# ─────────────────────── test app factory ─────────────────────────

def _build_app(db, *, admin_ok: bool = True, pm_actor: bool = False) -> FastAPI:
    """Build a FastAPI app wired to the AI-ADMIN-001 router with a
    dummy admin gate. `admin_ok=False` → the gate always 401s.
    `pm_actor=True` → the gate 401s to simulate PM token being rejected."""
    from routes.ai_admin_config import register_ai_admin_config_routes

    async def require_admin_strict_stub(
        x_admin_token: Optional[str] = Header(default=None),
    ):
        if not admin_ok:
            raise HTTPException(status_code=401, detail="Admin login required")
        if pm_actor:
            # simulate the real gate which rejects PM tokens
            raise HTTPException(status_code=401, detail="PM token rejected")
        if not x_admin_token:
            raise HTTPException(status_code=401, detail="Admin login required")
        return True

    router = APIRouter(prefix="/api")
    register_ai_admin_config_routes(
        router, db=db, require_admin_strict=require_admin_strict_stub,
    )
    app = FastAPI()
    app.include_router(router)
    return app


# ─────────────────────── invariants ───────────────────────────────

def test_status_endpoint_returns_no_raw_key_values():
    os.environ["ANTHROPIC_API_KEY"] = "sk-should-NEVER-leak-xyz"
    os.environ["OPENAI_API_KEY"] = "sk-openai-secret-abc"
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.get("/api/admin/ai/config/status", headers={"X-Admin-Token": "t"})
    assert r.status_code == 200
    body = r.text
    assert "sk-should-NEVER-leak-xyz" not in body
    assert "sk-openai-secret-abc" not in body
    j = r.json()
    assert j["providers"]["anthropic"]["key_present"] is True
    assert j["providers"]["openai"]["key_present"] is True
    assert j["providers"]["google"]["key_present"] is False


def test_status_endpoint_requires_admin_token():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.get("/api/admin/ai/config/status")  # no X-Admin-Token
    assert r.status_code == 401


def test_pm_token_is_rejected_by_strict_admin_gate():
    db = _FakeDB()
    client = TestClient(_build_app(db, pm_actor=True))
    r = client.get(
        "/api/admin/ai/config/status", headers={"X-Admin-Token": "pm-ish"}
    )
    assert r.status_code == 401


def test_tenants_list_always_includes_default_masci():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.get("/api/admin/ai/tenants", headers={"X-Admin-Token": "t"})
    assert r.status_code == 200
    tids = [t["tenant_id"] for t in r.json()["tenants"]]
    assert "masci" in tids


def test_tenants_list_reflects_saved_overrides():
    db = _FakeDB()
    db.tenant_ai_capabilities.docs.append({
        "tenant_id": "acme", "tenant_name": "Acme Corp",
        "tenant_ai_enabled": True,
    })
    client = TestClient(_build_app(db))
    r = client.get("/api/admin/ai/tenants", headers={"X-Admin-Token": "t"})
    tenants = r.json()["tenants"]
    acme = next(t for t in tenants if t["tenant_id"] == "acme")
    assert acme["has_override_doc"] is True
    assert acme["tenant_ai_enabled"] is True
    assert acme["tenant_name"] == "Acme Corp"


def test_tenant_capabilities_get_returns_modules_and_overrides():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.get(
        "/api/admin/ai/tenants/masci/capabilities",
        headers={"X-Admin-Token": "t"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["tenant_id"] == "masci"
    assert j["has_override_doc"] is False
    for module in (
        "daily_report_summary", "photo_intelligence", "pm_intelligence",
        "admin_intelligence", "safety_intelligence", "translation",
    ):
        assert module in j["modules"]
        assert j["modules"][module]["enabled"] is False


def test_update_tenant_capabilities_writes_only_allowlisted_fields():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    payload = {
        "tenant_ai_enabled": True,
        "daily_report_summary_enabled": True,
        "photo_intelligence_enabled": True,
        # Malicious extras — must be dropped by the pydantic + allow-list gate.
        "ANTHROPIC_API_KEY": "sk-attack",
        "tenant_id": "another-tenant",
    }
    r = client.put(
        "/api/admin/ai/tenants/masci/capabilities",
        json=payload,
        headers={"X-Admin-Token": "t", "X-Admin-Actor": "root@mascigc.com"},
    )
    assert r.status_code == 200, r.text
    stored = db.tenant_ai_capabilities.docs[0]
    assert stored["tenant_id"] == "masci"  # never overridden
    assert "ANTHROPIC_API_KEY" not in stored
    assert stored["tenant_ai_enabled"] is True
    assert stored["updated_by"] == "root@mascigc.com"
    assert stored["version"] == 1


def test_update_rejects_empty_patch():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.put(
        "/api/admin/ai/tenants/masci/capabilities",
        json={"note": "just a comment"},
        headers={"X-Admin-Token": "t"},
    )
    assert r.status_code == 400
    assert "no updatable fields" in r.json()["detail"]


def test_update_is_tenant_isolated():
    db = _FakeDB()
    db.tenant_ai_capabilities.docs.append({
        "tenant_id": "acme", "tenant_ai_enabled": True, "version": 3,
    })
    client = TestClient(_build_app(db))
    r = client.put(
        "/api/admin/ai/tenants/widgets/capabilities",
        json={"tenant_ai_enabled": True},
        headers={"X-Admin-Token": "t"},
    )
    assert r.status_code == 200
    acme = next(d for d in db.tenant_ai_capabilities.docs if d["tenant_id"] == "acme")
    widgets = next(d for d in db.tenant_ai_capabilities.docs if d["tenant_id"] == "widgets")
    assert acme["version"] == 3  # untouched
    assert widgets["tenant_ai_enabled"] is True
    assert widgets["version"] == 1


def test_update_writes_audit_entry_with_before_after_and_actor():
    db = _FakeDB()
    db.tenant_ai_capabilities.docs.append({
        "tenant_id": "masci", "tenant_ai_enabled": False,
        "version": 2,
    })
    client = TestClient(_build_app(db))
    r = client.put(
        "/api/admin/ai/tenants/masci/capabilities",
        json={"tenant_ai_enabled": True, "note": "Enabling for pilot."},
        headers={"X-Admin-Token": "t", "X-Admin-Actor": "jaymn@mascigc.com"},
    )
    assert r.status_code == 200
    assert len(db.tenant_ai_capability_audit.docs) == 1
    audit = db.tenant_ai_capability_audit.docs[0]
    assert audit["tenant_id"] == "masci"
    assert audit["actor"] == "jaymn@mascigc.com"
    assert audit["before"]["tenant_ai_enabled"] is False
    assert audit["after"]["tenant_ai_enabled"] is True
    assert "tenant_ai_enabled" in audit["changed_fields"]
    assert audit["note"] == "Enabling for pilot."
    # No secrets in audit — sanity scan.
    import json as _j
    assert "API_KEY" not in _j.dumps(audit)


def test_update_response_recomputes_modules():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-test",
    })
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.put(
        "/api/admin/ai/tenants/masci/capabilities",
        json={
            "tenant_ai_enabled": True,
            "daily_report_summary_enabled": True,
        },
        headers={"X-Admin-Token": "t"},
    )
    j = r.json()
    assert j["modules"]["daily_report_summary"]["enabled"] is True
    assert j["modules"]["photo_intelligence"]["enabled"] is False


def test_audit_endpoint_returns_recent_entries_newest_first():
    db = _FakeDB()
    db.tenant_ai_capability_audit.docs.extend([
        {"tenant_id": "masci", "actor": "a", "timestamp": "2026-02-01T00:00:00Z",
         "before": {}, "after": {"tenant_ai_enabled": True},
         "changed_fields": ["tenant_ai_enabled"], "note": None},
        {"tenant_id": "masci", "actor": "b", "timestamp": "2026-02-14T00:00:00Z",
         "before": {"tenant_ai_enabled": True},
         "after": {"tenant_ai_enabled": False},
         "changed_fields": ["tenant_ai_enabled"], "note": None},
    ])
    client = TestClient(_build_app(db))
    r = client.get(
        "/api/admin/ai/tenants/masci/audit",
        headers={"X-Admin-Token": "t"},
    )
    entries = r.json()["entries"]
    assert entries[0]["actor"] == "b"
    assert entries[1]["actor"] == "a"


def test_provider_test_endpoint_returns_booleans_only():
    os.environ["AI_PROVIDER_ANTHROPIC_ENABLED"] = "true"
    os.environ["ANTHROPIC_API_KEY"] = "sk-should-NEVER-leak-yyy"
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/admin/ai/providers/anthropic/test",
        headers={"X-Admin-Token": "t"},
    )
    assert r.status_code == 200
    body = r.text
    assert "sk-should-NEVER-leak-yyy" not in body
    j = r.json()
    assert j["provider"] == "anthropic"
    assert j["flag_enabled"] is True
    assert j["key_present"] is True
    assert j["status"] == "ready"


def test_provider_test_unknown_provider_returns_404():
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/admin/ai/providers/bogus/test",
        headers={"X-Admin-Token": "t"},
    )
    assert r.status_code == 404


def test_provider_test_reports_status_missing_key():
    os.environ["AI_PROVIDER_OPENAI_ENABLED"] = "true"
    # OPENAI_API_KEY intentionally unset
    db = _FakeDB()
    client = TestClient(_build_app(db))
    r = client.post(
        "/api/admin/ai/providers/openai/test",
        headers={"X-Admin-Token": "t"},
    )
    assert r.json()["status"] == "missing_key"


def test_daily_report_submit_route_does_not_import_ai_admin_config():
    """The admin AI config surface must not couple to the field
    submit path. Regression guard so nobody accidentally adds an import
    of the admin module at the top of routes/daily_reports.py."""
    from pathlib import Path
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    top = "\n".join(src.splitlines()[:80])
    assert "ai_admin_config" not in top


def test_ai_off_still_lets_ods_ingestion_run():
    """AI OFF invariant regression — the admin module doesn't leak into
    ODS. Trivially exercised by importing the ingest builder with no
    AI env vars set (they were popped by the autouse fixture)."""
    from services.ods_spine.ingest import _build_facts_from_dr_v1_report
    facts = _build_facts_from_dr_v1_report({
        "id": "ai-admin-off-lock",
        "project_number": "AI-ADMIN-OFF",
        "report_date": "2026-02-15",
        "masci_crews": [{"trade": "Concrete", "count": 3, "hours": 8}],
        "photos": ["p1", "p2"],
    })
    assert len(facts) >= 3
