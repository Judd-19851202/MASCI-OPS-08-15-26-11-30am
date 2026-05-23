"""
iter358 · Operational Intelligence digest expansion to HR / PM / Dispatch / FL.

Tests RBAC + envelope shape on each new endpoint:
- GET /api/hr/notifications/digest        (HR or Admin token)
- GET /api/pm/notifications/digest        (PM or Admin token)
- GET /api/dispatch/notifications/digest  (Dispatch or Admin token)
- GET /api/fl/notifications/digest        (FL or Admin token)

The four new endpoints share the same envelope as the iter357 admin/safety
digests — these tests reinforce that contract and confirm RBAC rejects
anonymous callers.
"""
from __future__ import annotations

import os

import requests


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

ROLES = ["hr", "pm", "dispatch", "fl"]
URLS = {r: f"{URL}/api/{r}/notifications/digest" for r in ROLES}


# ---------------- RBAC ----------------

def test_all_role_digests_reject_anonymous():
    for role, url in URLS.items():
        r = requests.get(url, timeout=10, headers={
            "X-Admin-Token": "", "X-HR-Token": "", "X-PM-Token": "",
            "X-Dispatch-Token": "", "X-FL-Token": "",
        })
        assert r.status_code == 401, f"{role} should be 401 but got {r.status_code}: {r.text}"


def test_all_role_digests_accept_admin_preview():
    """Admins can preview each role's digest for operational oversight."""
    for role, url in URLS.items():
        r = requests.get(url, timeout=15,
                         headers={"X-Admin-Token": ADMIN_TOKEN})
        assert r.status_code == 200, f"{role} admin-preview should be 200: {r.text}"
        body = r.json()
        assert body["ok"] is True
        assert body["role"] == role
        assert body["generated_at"]
        assert "summary" in body
        assert "sections" in body
        assert "total_open" in body["summary"]
        # PM and FL digests include a scope_user echo.
        if role in ("pm", "fl"):
            assert "scope_user" in body


# ---------------- Role-specific summary keys ----------------

def test_hr_digest_summary_shape():
    r = requests.get(URLS["hr"], timeout=15,
                     headers={"X-Admin-Token": ADMIN_TOKEN})
    body = r.json()
    for k in ("linkage_failures", "driver_qualification_expired",
              "driver_qualification_expiring_30d", "archived_active",
              "trainings_expired"):
        assert k in body["summary"], k


def test_pm_digest_summary_shape():
    r = requests.get(URLS["pm"], timeout=15,
                     headers={"X-Admin-Token": ADMIN_TOKEN})
    body = r.json()
    for k in ("capa_overdue", "trainings_expired", "ppe_missing",
              "driver_unavailable"):
        assert k in body["summary"], k


def test_dispatch_digest_summary_shape():
    r = requests.get(URLS["dispatch"], timeout=15,
                     headers={"X-Admin-Token": ADMIN_TOKEN})
    body = r.json()
    for k in ("med_card_expired", "cdl_expired", "expiring_30d"):
        assert k in body["summary"], k


def test_fl_digest_summary_shape():
    r = requests.get(URLS["fl"], timeout=15,
                     headers={"X-Admin-Token": ADMIN_TOKEN})
    body = r.json()
    for k in ("trainings_expired", "ppe_missing", "driver_unavailable",
              "incidents_needing_capa"):
        assert k in body["summary"], k


def test_section_items_carry_minimum_keys():
    """Every section's items[] must include the keys the UI renders."""
    for role, url in URLS.items():
        r = requests.get(url, timeout=15,
                         headers={"X-Admin-Token": ADMIN_TOKEN})
        body = r.json()
        for s in body["sections"]:
            for it in s.get("items") or []:
                for k in ("id", "rule_id", "severity", "entity_name"):
                    assert k in it, (role, s["key"], k, it)
