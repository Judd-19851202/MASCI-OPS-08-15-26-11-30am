"""
iter357 · Operational Intelligence Notifications (Phase 2 P1).

Tests the role-scoped digest engine:
- GET /api/admin/notifications/digest     (admin-strict)
- GET /api/safety/notifications/digest    (safety or admin)

Invariants:
1. RBAC — anon = 401 on both endpoints.
2. Admin token works on /admin/notifications/digest and on
   /safety/notifications/digest (safety-or-admin gate).
3. Payload shape: {ok, role, generated_at, summary, sections}.
4. Admin digest always includes a governance_score section and a
   numeric convergence score.
5. Safety digest reports counts that match the live detector findings
   for the respective rules (deterministic — same rule_ids must produce
   the same counts).
6. Sections that have a `rule_ids` list correctly point at findings
   that actually exist.
"""
from __future__ import annotations

import os

import requests


# ---------------- bootstrap ----------------
_FRONT_ENV = "/app/frontend/.env"
_BACK_ENV = "/app/backend/.env"
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

try:
    with open(_BACK_ENV) as fh:
        for ln in fh:
            if ln.startswith("ADMIN_PASSWORD="):
                ADMIN_PASSWORD = ln.split("=", 1)[1].strip().strip('"')
                break
        else:
            ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
except FileNotFoundError:
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

ADMIN_TOKEN = ""
if URL and ADMIN_PASSWORD:
    try:
        r = requests.post(f"{URL}/api/admin/login",
                          json={"password": ADMIN_PASSWORD}, timeout=10)
        if r.status_code == 200:
            ADMIN_TOKEN = r.json().get("token", "")
    except Exception:
        ADMIN_TOKEN = ""

import requests.api  # noqa: E402, F401
import requests.sessions  # noqa: E402

_orig_request = requests.api.request
_orig_session_request = requests.sessions.Session.request


def _patched(method, url, **kwargs):
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    return _orig_request(method, url, **kwargs)


def _patched_session(self, method, url, **kwargs):
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    return _orig_session_request(self, method, url, **kwargs)


requests.api.request = _patched
requests.sessions.Session.request = _patched_session


ADMIN_URL = f"{URL}/api/admin/notifications/digest"
SAFETY_URL = f"{URL}/api/safety/notifications/digest"
SCAN_URL = f"{URL}/api/admin/compliance/scan"
LIST_URL = f"{URL}/api/admin/compliance/findings"


# ---------------- RBAC ----------------

def test_admin_digest_rejects_anon():
    r = requests.get(ADMIN_URL, timeout=10,
                     headers={"X-Admin-Token": "", "X-Safety-Token": ""})
    assert r.status_code == 401, r.text


def test_safety_digest_rejects_anon():
    r = requests.get(SAFETY_URL, timeout=10,
                     headers={"X-Admin-Token": "", "X-Safety-Token": ""})
    assert r.status_code == 401, r.text


# ---------------- Shape ----------------

def test_admin_digest_shape():
    requests.post(SCAN_URL, timeout=60)
    r = requests.get(ADMIN_URL, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["role"] == "admin"
    assert body["generated_at"]
    summary = body["summary"]
    for k in ("critical", "high", "medium", "low", "info", "total_open"):
        assert k in summary
    assert isinstance(summary["score"], int)
    assert summary["score_label"] in ("healthy", "fair", "degraded", "critical")
    sections = body["sections"]
    keys = [s["key"] for s in sections]
    assert "governance_score" in keys


def test_safety_digest_shape():
    requests.post(SCAN_URL, timeout=60)
    r = requests.get(SAFETY_URL, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["role"] == "safety"
    summary = body["summary"]
    for k in ("total_open", "overdue_capas", "incidents_needing_capa",
              "capas_awaiting_verification", "capas_without_owner",
              "incidents_closed_capa_open", "trainings_expired"):
        assert k in summary, k


# ---------------- Determinism / signal correctness ----------------

def test_safety_digest_counts_match_findings():
    """Safety digest counts must equal live open-finding counts for the
    rules they aggregate."""
    requests.post(SCAN_URL, timeout=60)
    r = requests.get(SAFETY_URL, timeout=15)
    assert r.status_code == 200
    body = r.json()
    summary = body["summary"]

    expected = {
        "overdue_capas":                "CAPA_OVERDUE",
        "incidents_needing_capa":       "INC_NEEDS_CAPA",
        "capas_awaiting_verification":  "CAPA_AWAITING_VERIFICATION",
        "capas_without_owner":          "CAPA_NO_OWNER",
        "incidents_closed_capa_open":   "INC_CLOSED_CAPA_OPEN",
        "trainings_expired":            "TRN_EXPIRED",
    }
    for summary_key, rule_id in expected.items():
        r2 = requests.get(
            f"{LIST_URL}?rule_id={rule_id}&limit=1000", timeout=15,
        )
        live_count = r2.json().get("count", 0)
        digest_count = summary.get(summary_key, 0)
        assert digest_count == live_count, (
            f"{summary_key} mismatch — digest reports {digest_count}, "
            f"live findings report {live_count}"
        )


def test_admin_digest_includes_critical_section_when_present():
    """If governance summary reports >0 critical, the admin digest must
    include a 'critical_findings' section."""
    requests.post(SCAN_URL, timeout=60)
    r = requests.get(ADMIN_URL, timeout=15)
    body = r.json()
    summary = body["summary"]
    keys = [s["key"] for s in body["sections"]]
    if summary["critical"] > 0:
        assert "critical_findings" in keys, (
            f"summary has {summary['critical']} critical findings but "
            f"sections = {keys}"
        )


def test_section_items_have_minimum_shape():
    """Every section with items must include the keys we render in UI."""
    requests.post(SCAN_URL, timeout=60)
    for url in (ADMIN_URL, SAFETY_URL):
        r = requests.get(url, timeout=15)
        body = r.json()
        for s in body["sections"]:
            for it in s.get("items") or []:
                for k in ("id", "rule_id", "severity", "entity_name"):
                    assert k in it, (url, s["key"], k, it)
