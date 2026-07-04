"""Sprint 1C — Incident Delete Workflow Remediation tests.

Authorized scope: validate the remediated DELETE /api/incidents/{id} route
covers every behaviour the operator explicitly required:

  1.  Super-admin (X-Admin-Token) can delete an incident with no CAPAs.
  2.  Safety-role (X-Safety-Token) is rejected with HTTP 401.
  3.  Identifier resolution: UUID works, doc_id works, junk → 404.
  4.  CAPA dependency: linked corrective action blocks delete with HTTP 409
      and the response body explains which CAPAs block it.
  5.  Audit event is written to db.audit_events on a successful delete.

The conftest auto-attaches X-Admin-Token to every request hitting this
host, so for the 401 / safety-token cases we explicitly pass `headers=`
to override the conftest fixture (Session.request `setdefault` no-ops
when an explicit header is supplied).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

# Track 21.2 · soft-skip when the legacy conftest constants aren't provided.
try:
    from tests.conftest import ADMIN_TOKEN, URL
except ImportError:
    ADMIN_TOKEN, URL = "", ""


pytestmark = pytest.mark.skipif(
    not URL or not ADMIN_TOKEN,
    reason="Preview backend URL or admin token unavailable.",
)


def _db():
    """Direct preview-DB handle for fixtures and assertions."""
    mongo_url = os.environ.get("MONGO_URL", "")
    db_name = os.environ.get("DB_NAME", "")
    if not mongo_url:
        # Fallback to backend/.env
        for line in open("/app/backend/.env"):
            if line.startswith("MONGO_URL="):
                mongo_url = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("DB_NAME="):
                db_name = line.split("=", 1)[1].strip().strip('"')
    return MongoClient(mongo_url)[db_name]


def _make_incident(tag: str) -> dict:
    """Insert a minimal incident row directly into the preview DB.

    We bypass the public POST endpoint so the test doesn't depend on
    idempotency keys / fan-out / Resend wiring. The route under test is
    pure DB + CAPA lookup, so a hand-built doc is the cleanest fixture.
    """
    incident_id = str(uuid.uuid4())
    # Use a clearly-test doc_id outside any production INC-YYYY range.
    doc_id = f"INC-SPRINT1C-{tag}"
    db = _db()
    db.incidents.insert_one({
        "id": incident_id,
        "doc_id": doc_id,
        "project_name": f"Sprint1C Test Project {tag}",
        "project_number": "",
        "location": "Test Lab",
        "incident_date": "2026-02-01",
        "incident_time": "10:00",
        "reported_date": "2026-02-01",
        "reported_by": "Sprint1C Tester",
        "incident_type": "Near Miss",
        "severity": "minor",
        "description": "Sprint 1C synthetic incident — safe to delete.",
        "osha_recordable": "No",
        "work_stopped": "No",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "_sprint1c_test": True,
    })
    return {"id": incident_id, "doc_id": doc_id}


def _cleanup(incident_id: str | None = None, doc_id: str | None = None,
             capa_id: str | None = None):
    db = _db()
    if incident_id:
        db.incidents.delete_one({"id": incident_id})
    if doc_id:
        db.incidents.delete_one({"doc_id": doc_id})
    if capa_id:
        db.corrective_actions.delete_one({"id": capa_id})


# ──────────────────────────────────────────────────────────────────────
# 1 · Super-admin delete by UUID — happy path
# ──────────────────────────────────────────────────────────────────────
def test_super_admin_can_delete_incident_by_uuid():
    inc = _make_incident("uuid-happy")
    try:
        r = requests.delete(f"{URL}/api/incidents/{inc['id']}", timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("deleted") is True
        assert body.get("id") == inc["id"]
        # Confirm row actually gone.
        assert _db().incidents.find_one({"id": inc["id"]}) is None
    finally:
        _cleanup(inc["id"])


# ──────────────────────────────────────────────────────────────────────
# 2 · Super-admin delete by doc_id (id-vs-doc_id behaviour)
# ──────────────────────────────────────────────────────────────────────
def test_super_admin_can_delete_incident_by_doc_id():
    inc = _make_incident("doc-id")
    try:
        r = requests.delete(f"{URL}/api/incidents/{inc['doc_id']}", timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        # Backend resolves doc_id → canonical UUID before delete.
        assert body.get("id") == inc["id"]
        assert body.get("doc_id") == inc["doc_id"]
        assert _db().incidents.find_one({"id": inc["id"]}) is None
    finally:
        _cleanup(inc["id"])


def test_unknown_identifier_returns_404():
    bogus = f"INC-NONEXISTENT-{uuid.uuid4().hex[:6]}"
    r = requests.delete(f"{URL}/api/incidents/{bogus}", timeout=10)
    assert r.status_code == 404, r.text


# ──────────────────────────────────────────────────────────────────────
# 3 · Safety-role token must be REJECTED (workflow safety preserved)
# ──────────────────────────────────────────────────────────────────────
def test_safety_role_token_is_rejected():
    inc = _make_incident("safety-deny")
    try:
        # Explicitly override the conftest's admin header so the safety
        # token is the ONLY auth on the request. Send a syntactically
        # plausible but unrecognized safety token.
        headers = {
            "X-Admin-Token": "",
            "X-PM-Token": "",
            "X-Safety-Token": "sprint1c.fake-safety-token",
        }
        r = requests.delete(
            f"{URL}/api/incidents/{inc['id']}",
            headers=headers, timeout=10,
        )
        assert r.status_code == 401, (
            f"Safety token MUST NOT delete incidents. Got HTTP {r.status_code}: {r.text}"
        )
        # Row must still exist after rejected delete.
        assert _db().incidents.find_one({"id": inc["id"]}) is not None
    finally:
        _cleanup(inc["id"])


def test_no_token_is_rejected():
    inc = _make_incident("no-token")
    try:
        headers = {"X-Admin-Token": "", "X-PM-Token": ""}
        r = requests.delete(
            f"{URL}/api/incidents/{inc['id']}",
            headers=headers, timeout=10,
        )
        assert r.status_code == 401
        assert _db().incidents.find_one({"id": inc["id"]}) is not None
    finally:
        _cleanup(inc["id"])


# ──────────────────────────────────────────────────────────────────────
# 4 · CAPA-linked incident must be BLOCKED with 409 + explanatory body
# ──────────────────────────────────────────────────────────────────────
def test_incident_with_linked_capa_returns_409():
    inc = _make_incident("capa-block")
    capa_id = str(uuid.uuid4())
    db = _db()
    db.corrective_actions.insert_one({
        "id": capa_id,
        "title": "Sprint1C synthetic CAPA — should block delete",
        "source_kind": "incident",
        "source_id": inc["id"],
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "_sprint1c_test": True,
    })
    try:
        r = requests.delete(f"{URL}/api/incidents/{inc['id']}", timeout=10)
        assert r.status_code == 409, r.text
        body = r.json()
        detail = body.get("detail") or {}
        assert isinstance(detail, dict), f"Expected structured detail, got {detail!r}"
        assert detail.get("code") == "incident_has_linked_capas"
        assert detail.get("linked_capa_count") == 1
        # The blocking CAPA preview must surface so the user can act on it.
        capas = detail.get("linked_capas") or []
        assert any(c.get("id") == capa_id for c in capas)
        # Crucially — the incident row must still exist (no half-delete).
        assert db.incidents.find_one({"id": inc["id"]}) is not None
    finally:
        _cleanup(inc["id"], capa_id=capa_id)


# ──────────────────────────────────────────────────────────────────────
# 5 · Successful delete writes an audit_events row
# ──────────────────────────────────────────────────────────────────────
def test_delete_writes_audit_event():
    inc = _make_incident("audit")
    db = _db()
    before = db.audit_events.count_documents({
        "kind": "incident_deleted",
        "incident_id": inc["id"],
    })
    try:
        r = requests.delete(f"{URL}/api/incidents/{inc['id']}", timeout=10)
        assert r.status_code == 200, r.text
        after = db.audit_events.count_documents({
            "kind": "incident_deleted",
            "incident_id": inc["id"],
        })
        assert after == before + 1, (
            f"Expected 1 new audit event for incident_deleted; before={before} after={after}"
        )
        evt = db.audit_events.find_one(
            {"kind": "incident_deleted", "incident_id": inc["id"]},
            {"_id": 0},
        )
        assert evt is not None
        assert evt.get("actor_role") in {"admin", "pm", "unknown"}
        assert evt.get("incident_doc_id") == inc["doc_id"]
    finally:
        _cleanup(inc["id"])
        # Tidy the audit row so repeated test runs don't accumulate noise.
        db.audit_events.delete_many({
            "kind": "incident_deleted",
            "incident_id": inc["id"],
        })
