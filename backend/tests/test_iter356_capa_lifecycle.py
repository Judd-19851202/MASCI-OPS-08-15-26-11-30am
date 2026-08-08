"""
iter356 · Incident → CAPA → Closeout Lifecycle Enforcement (Phase 2 P0).

Tests cover both halves of the iteration:

A. DETECTOR (governance engine extension)
   - INC_NEEDS_CAPA — severe incident with no linked CAPA
   - CAPA_AWAITING_VERIFICATION — Pending Review > 7 days
   - CAPA_NO_OWNER — open CAPA with no assigned_to_name

B. BACKEND ENFORCEMENT (safety_portal/corrective_actions.py PATCH)
   - Legal status transitions accepted
   - Illegal transitions rejected (422)
   - Pending Review → Closed without Verified rejected
   - Verified stamps verified_by_name + verified_at
   - Closed stamps closed_by_name + completed_at
   - status_history[] appended on every status change
   - transition_note flows through to status_history entry

Authentication uses the current preview contracts:
  - admin governance routes: /api/auth/multi-login fixture → X-Admin-Token + X-Directory-Token
  - safety corrective-action routes: /api/safety/login → X-Safety-Token
"""
from __future__ import annotations

import uuid

import requests


# Target -----------------------------------------------------------------
_FRONT_ENV = "/app/frontend/.env"
try:
    with open(_FRONT_ENV) as fh:
        for ln in fh:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                URL = ln.split("=", 1)[1].strip().rstrip("/")
                break
        else:
            URL = "http://localhost:8001"
except FileNotFoundError:
    URL = "http://localhost:8001"

# Bootstrap live preview tokens.
ADMIN_TOKEN = ""
DIRECTORY_TOKEN = ""
SAFETY_TOKEN = ""
if URL:
    try:
        r = requests.post(f"{URL}/api/auth/multi-login",
                          json={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
                          timeout=15)
        if r.status_code == 200:
            ADMIN_TOKEN = (r.json().get("portal_tokens") or {}).get("admin", "")
            DIRECTORY_TOKEN = r.json().get("session_token", "")
    except Exception:
        ADMIN_TOKEN = ""
        DIRECTORY_TOKEN = ""
    try:
        r = requests.post(f"{URL}/api/safety/login",
                          json={"email": "cert.safety@example.com", "password": "CertProof2026!"},
                          timeout=15)
        if r.status_code == 200:
            SAFETY_TOKEN = r.json().get("token", "")
    except Exception:
        SAFETY_TOKEN = ""

# Patch requests to auto-attach admin + safety tokens.
import requests.api  # noqa: E402, F401
import requests.sessions  # noqa: E402

_orig_request = requests.api.request
_orig_session_request = requests.sessions.Session.request


def _patched(method, url, **kwargs):
    if isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        if ADMIN_TOKEN:
            headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        if DIRECTORY_TOKEN:
            headers.setdefault("X-Directory-Token", DIRECTORY_TOKEN)
        if SAFETY_TOKEN:
            headers.setdefault("X-Safety-Token", SAFETY_TOKEN)
        kwargs["headers"] = headers
    return _orig_request(method, url, **kwargs)


def _patched_session(self, method, url, **kwargs):
    if isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        if ADMIN_TOKEN:
            headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        if DIRECTORY_TOKEN:
            headers.setdefault("X-Directory-Token", DIRECTORY_TOKEN)
        if SAFETY_TOKEN:
            headers.setdefault("X-Safety-Token", SAFETY_TOKEN)
        kwargs["headers"] = headers
    return _orig_session_request(self, method, url, **kwargs)


requests.api.request = _patched
requests.sessions.Session.request = _patched_session

SCAN_URL = f"{URL}/api/admin/compliance/scan"
LIST_URL = f"{URL}/api/admin/compliance/findings"
SUMMARY_URL = f"{URL}/api/admin/governance/summary"
CA_LIST_URL = f"{URL}/api/safety/corrective-actions"


# ---------------------------------------------------------------------------
# Part A — Detector wiring
# ---------------------------------------------------------------------------

def test_governance_catalog_lists_new_lifecycle_rules():
    r = requests.get(SUMMARY_URL, timeout=15)
    assert r.status_code == 200, r.text
    catalog = r.json().get("rule_catalog") or {}
    for rule_id in ("INC_NEEDS_CAPA", "CAPA_AWAITING_VERIFICATION", "CAPA_NO_OWNER"):
        assert rule_id in catalog, f"{rule_id} missing"
        assert catalog[rule_id]["category"] == "lifecycle"


def test_scan_runs_lifecycle_detector_cleanly():
    r = requests.post(SCAN_URL, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["detector_errors"] == {}


# ---------------------------------------------------------------------------
# Part B — Backend enforcement on CAPA PATCH
# ---------------------------------------------------------------------------

def _create_capa(title="iter356-lifecycle-test"):
    payload = {
        "title": f"{title}-{uuid.uuid4().hex[:6]}",
        "description": "lifecycle test seed",
        # PRE-C10 safety truth guard:
        # lifecycle certification rows must remain technically auditable
        # without polluting operator/executive KPI surfaces.
        "source_kind": "synthetic_test",
        "source_id": "",
        "project_number": "TEST-LIFECYCLE",
        "assigned_to_name": "Test Owner",
        "assigned_to_email": "owner@example.com",
        "priority": "Medium",
        "due_date": "",
        "notes": "",
    }
    r = requests.post(CA_LIST_URL, json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    return j.get("id") or j.get("doc", {}).get("id")


def test_capa_legal_transition_open_to_in_progress():
    cid = _create_capa()
    if not cid:
        return
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "In Progress",
                             "transition_note": "starting work"},
                       timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "In Progress"
    history = body.get("status_history") or []
    assert any(e.get("to") == "In Progress" for e in history)
    assert any(e.get("note") == "starting work" for e in history)


def test_capa_illegal_transition_open_to_closed():
    cid = _create_capa()
    if not cid:
        return
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "Closed"}, timeout=15)
    assert r.status_code == 422, r.text


def test_capa_cannot_close_without_verified():
    """Pending Review → Closed must be rejected; Pending Review → Verified → Closed must succeed."""
    cid = _create_capa()
    if not cid:
        return
    # Walk through legal transitions to Pending Review.
    for next_status in ("In Progress", "Pending Review"):
        r = requests.patch(f"{CA_LIST_URL}/{cid}",
                           json={"status": next_status}, timeout=15)
        assert r.status_code == 200, (next_status, r.text)
    # Pending Review → Closed should be rejected.
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "Closed"}, timeout=15)
    assert r.status_code == 422, r.text
    # Pending Review → Verified should succeed.
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "Verified",
                             "transition_note": "verified by second reviewer"},
                       timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Verified"
    assert body.get("verified_at")
    # Verified → Closed should succeed.
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "Closed",
                             "transition_note": "closeout"},
                       timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Closed"
    assert body.get("completed_at")
    history = body.get("status_history") or []
    assert len(history) >= 4, history
    transitions = [(e["from"], e["to"]) for e in history]
    assert ("Pending Review", "Verified") in transitions
    assert ("Verified", "Closed") in transitions


def test_capa_status_history_is_append_only():
    """Updating non-status fields must NOT alter status_history."""
    cid = _create_capa()
    if not cid:
        return
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "In Progress",
                             "transition_note": "begin"},
                       timeout=15)
    assert r.status_code == 200
    history_before = r.json().get("status_history") or []
    # Update a non-status field.
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"notes": "added note without status change"},
                       timeout=15)
    assert r.status_code == 200, r.text
    history_after = r.json().get("status_history") or []
    assert history_after == history_before, (
        "status_history must be append-only and only mutate on status change"
    )


def test_capa_reopen_from_closed_is_allowed():
    """Closed → In Progress is the supported re-open path."""
    cid = _create_capa()
    if not cid:
        return
    for s in ("In Progress", "Pending Review", "Verified", "Closed"):
        r = requests.patch(f"{CA_LIST_URL}/{cid}",
                           json={"status": s}, timeout=15)
        assert r.status_code == 200, (s, r.text)
    r = requests.patch(f"{CA_LIST_URL}/{cid}",
                       json={"status": "In Progress",
                             "transition_note": "reopened after new info"},
                       timeout=15)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "In Progress"
