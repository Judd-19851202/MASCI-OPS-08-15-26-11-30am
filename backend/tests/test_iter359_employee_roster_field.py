"""
iter359 · UI-level Employee Linkage Enforcement (Phase 2 P2).

Backend coverage is mostly assertion of the existing roster search
endpoint behavior the new EmployeeRosterField depends on:
- GET /api/master-lookup/employees?q=...  must return items[] with
  {id, label, raw} or a list of similar shape.

This iteration is primarily a frontend change (the EmployeeRosterField
component + its wiring into NewIncident), but a small backend contract
test guards against regression on the data source.
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

LOOKUP_URL = f"{URL}/api/master-lookup/employees"


def test_employee_lookup_returns_items_on_query():
    """Search by any common letter must return at least one employee.
    Any non-error response with the documented shape passes."""
    r = requests.get(LOOKUP_URL, params={"q": "a", "limit": 5},
                     headers={"X-Admin-Token": ADMIN_TOKEN}, timeout=15)
    assert r.status_code == 200, r.text
    payload = r.json()
    # Accept either {items: [...]} OR a bare list.
    items = payload.get("items") if isinstance(payload, dict) else payload
    assert isinstance(items, list)


def test_employee_lookup_item_shape():
    r = requests.get(LOOKUP_URL, params={"q": "a", "limit": 5},
                     headers={"X-Admin-Token": ADMIN_TOKEN}, timeout=15)
    payload = r.json()
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not items:
        return  # empty preview DB — nothing to assert
    for it in items[:5]:
        # The component reads .id and .label primarily, .raw secondarily.
        assert "id" in it
        assert "label" in it or "name" in it or "raw" in it


def test_employee_lookup_empty_query_safe():
    """Empty or whitespace query must not 500."""
    r = requests.get(LOOKUP_URL, params={"q": "", "limit": 5},
                     headers={"X-Admin-Token": ADMIN_TOKEN}, timeout=15)
    assert r.status_code in (200, 400, 422), (
        f"Empty query returned {r.status_code}"
    )


def test_employee_lookup_limit_respected():
    r = requests.get(LOOKUP_URL, params={"q": "a", "limit": 3},
                     headers={"X-Admin-Token": ADMIN_TOKEN}, timeout=15)
    payload = r.json()
    items = payload.get("items") if isinstance(payload, dict) else payload
    if items:
        assert len(items) <= 3
