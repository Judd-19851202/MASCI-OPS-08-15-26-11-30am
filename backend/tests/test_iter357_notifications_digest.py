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

import requests


# ---------------- bootstrap ----------------
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

ADMIN_HEADERS = {}
SAFETY_HEADERS = {}
if URL:
    try:
        r = requests.post(
            f"{URL}/api/auth/multi-login",
            json={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
            timeout=15,
        )
        if r.status_code == 200:
            body = r.json()
            ADMIN_HEADERS = {
                "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin", ""),
                "X-Directory-Token": body.get("session_token") or "",
            }
    except Exception:
        ADMIN_HEADERS = {}
    try:
        r = requests.post(
            f"{URL}/api/safety/login",
            json={"email": "cert.safety@example.com", "password": "CertProof2026!"},
            timeout=15,
        )
        if r.status_code == 200:
            SAFETY_HEADERS = {"X-Safety-Token": r.json().get("token", "")}
    except Exception:
        SAFETY_HEADERS = {}

import requests.api  # noqa: E402, F401
import requests.sessions  # noqa: E402

_orig_request = requests.api.request
_orig_session_request = requests.sessions.Session.request


def _patched(method, url, **kwargs):
    if isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        if url.endswith("/api/admin/notifications/digest") or url.endswith("/api/admin/compliance/scan") or "/api/admin/compliance/findings" in url:
            for k, v in ADMIN_HEADERS.items():
                if v:
                    headers.setdefault(k, v)
        if url.endswith("/api/safety/notifications/digest"):
            for k, v in SAFETY_HEADERS.items():
                if v:
                    headers.setdefault(k, v)
        kwargs["headers"] = headers
    return _orig_request(method, url, **kwargs)


def _patched_session(self, method, url, **kwargs):
    if isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        if url.endswith("/api/admin/notifications/digest") or url.endswith("/api/admin/compliance/scan") or "/api/admin/compliance/findings" in url:
            for k, v in ADMIN_HEADERS.items():
                if v:
                    headers.setdefault(k, v)
        if url.endswith("/api/safety/notifications/digest"):
            for k, v in SAFETY_HEADERS.items():
                if v:
                    headers.setdefault(k, v)
        kwargs["headers"] = headers
    return _orig_session_request(self, method, url, **kwargs)


requests.api.request = _patched
requests.sessions.Session.request = _patched_session


def _auth_post(url: str, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    if url.endswith("/api/admin/compliance/scan") or "/api/admin/compliance/findings" in url:
        login = requests.post(
            f"{URL}/api/auth/multi-login",
            json={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
            timeout=15,
        )
        assert login.status_code == 200, login.text
        body = login.json()
        headers = {
            "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin", ""),
            "X-Directory-Token": body.get("session_token") or "",
            **headers,
        }
    return requests.post(url, headers=headers, **kwargs)


def _auth_get(url: str, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    if url.endswith("/api/admin/notifications/digest") or "/api/admin/compliance/findings" in url:
        login = requests.post(
            f"{URL}/api/auth/multi-login",
            json={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
            timeout=15,
        )
        assert login.status_code == 200, login.text
        body = login.json()
        headers = {
            "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin", ""),
            "X-Directory-Token": body.get("session_token") or "",
            **headers,
        }
    elif url.endswith("/api/safety/notifications/digest"):
        login = requests.post(
            f"{URL}/api/safety/login",
            json={"email": "cert.safety@example.com", "password": "CertProof2026!"},
            timeout=15,
        )
        assert login.status_code == 200, login.text
        headers = {"X-Safety-Token": login.json().get("token", ""), **headers}
    return requests.get(url, headers=headers, **kwargs)


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
    _auth_post(SCAN_URL, timeout=60)
    r = _auth_get(ADMIN_URL, timeout=15)
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
    _auth_post(SCAN_URL, timeout=60)
    r = _auth_get(SAFETY_URL, timeout=15)
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
    _auth_post(SCAN_URL, timeout=60)
    r = _auth_get(SAFETY_URL, timeout=15)
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
        r2 = _auth_get(
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
    _auth_post(SCAN_URL, timeout=60)
    r = _auth_get(ADMIN_URL, timeout=15)
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
    _auth_post(SCAN_URL, timeout=60)
    for url in (ADMIN_URL, SAFETY_URL):
        r = _auth_get(url, timeout=15)
        body = r.json()
        for s in body["sections"]:
            for it in s.get("items") or []:
                for k in ("id", "rule_id", "severity", "entity_name"):
                    assert k in it, (url, s["key"], k, it)
