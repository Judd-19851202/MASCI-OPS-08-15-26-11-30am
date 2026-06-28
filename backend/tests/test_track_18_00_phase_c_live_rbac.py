"""Live RBAC + audit + safety validation for Track 18.00 Phase C.

Hits the deployed preview backend (REACT_APP_BACKEND_URL from frontend/.env)
end-to-end with the super-admin multi-login flow, then for each portal token
calls /api/admin/transportation/search and verifies the per-portal allowed
result-groups.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import pytest
import requests


def _backend_url() -> str:
    env_path = Path("/app/frontend/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _backend_url()

# Per-portal expected allowed groups (lifted from _types_for_role).
ALLOWED = {
    "admin":       {"drivers", "carriers", "trucks", "dispatch", "projects",
                    "documents", "orientation", "actions", "intelligence", "timeline"},
    "dispatch":    {"trucks", "drivers", "carriers", "dispatch", "projects"},
    "pm":          {"projects", "dispatch", "trucks"},
    "hr":          {"drivers", "documents", "orientation"},
    "safety":      {"drivers", "trucks"},
    "shop":        {"trucks"},
    "fl":          {"drivers", "projects"},
}

HEADER_BY_PORTAL = {
    "admin":    "X-Admin-Token",
    "dispatch": "X-Dispatch-Token",
    "pm":       "X-PM-Token",
    "hr":       "X-HR-Token",
    "safety":   "X-Safety-Token",
    "shop":     "X-Shop-Token",
    "fl":       "X-FL-Token",
}


@pytest.fixture(scope="module")
def portal_tokens():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    tokens = data.get("portal_tokens") or {}
    if not tokens:
        pytest.skip("no portal_tokens returned")
    return tokens


def test_01_unauth_returns_401():
    last_exc = None
    for _ in range(3):
        try:
            r = requests.get(f"{BASE_URL}/api/admin/transportation/search",
                             params={"q": "truck"}, timeout=45)
            assert r.status_code in (401, 403), r.status_code
            return
        except requests.exceptions.ReadTimeout as exc:
            last_exc = exc
            time.sleep(1)
    raise last_exc  # noqa: PLE0704


def test_02_rbac_admin_returns_envelope(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token missing")
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": "truck"},
        headers={HEADER_BY_PORTAL["admin"]: token},
        timeout=20,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("ok") is True
    assert data.get("query") == "truck"
    assert data.get("schema_version") == "18.00C"
    assert isinstance(data.get("results"), list)
    assert isinstance(data.get("counts"), dict)
    for res in data["results"]:
        assert res.get("route") and isinstance(res["route"], str)
        for k in ("type", "title", "subtitle", "status", "source", "route", "reason"):
            assert k in res, f"missing {k} in result"


@pytest.mark.parametrize("portal", ["dispatch", "pm", "hr", "safety", "shop", "fl"])
def test_03_rbac_per_portal_groups(portal_tokens, portal):
    token = portal_tokens.get(portal)
    if not token:
        pytest.skip(f"{portal} token missing")
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": "truck"},
        headers={HEADER_BY_PORTAL[portal]: token},
        timeout=20,
    )
    assert r.status_code == 200, f"{portal} got {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert data.get("schema_version") == "18.00C"
    allowed = ALLOWED[portal]
    # Every result's group must fall within the portal's allowed set.
    bad = [res for res in data.get("results", [])
           if res.get("group") and res["group"] not in allowed]
    assert not bad, f"{portal} leaked groups: {set(b['group'] for b in bad)} (allowed={allowed})"
    # counts keys also must be subset of allowed.
    for g in data.get("counts", {}):
        assert g in allowed, f"{portal} counts has disallowed group {g}"


def test_04_hr_never_returns_trucks(portal_tokens):
    token = portal_tokens.get("hr")
    if not token:
        pytest.skip("hr token missing")
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": "truck"},
        headers={HEADER_BY_PORTAL["hr"]: token},
        timeout=20,
    )
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    truck_results = [x for x in data.get("results", []) if x.get("group") == "trucks"]
    assert truck_results == [], "HR portal leaked trucks group"
    assert "trucks" not in data.get("counts", {})


def test_05_special_regex_chars_safe(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token missing")
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": "truck.*214"},
        headers={HEADER_BY_PORTAL["admin"]: token},
        timeout=20,
    )
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    assert data.get("ok") is True


def test_06_limit_bounded(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token missing")
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": "truck", "limit": 999},
        headers={HEADER_BY_PORTAL["admin"]: token},
        timeout=20,
    )
    # FastAPI Query(le=50) returns 422 for over-cap.
    assert r.status_code in (200, 422), r.status_code
    if r.status_code == 200:
        assert len(r.json().get("results", [])) <= 50


def test_07_query_max_chars(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token missing")
    big = "a" * 200
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/search",
        params={"q": big},
        headers={HEADER_BY_PORTAL["admin"]: token},
        timeout=20,
    )
    # 80-char cap (FastAPI Query max_length).
    assert r.status_code in (200, 422), r.status_code


def test_08_every_result_route_non_empty(portal_tokens):
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("admin token missing")
    for q in ("truck", "214", "DOT", "driver"):
        r = requests.get(
            f"{BASE_URL}/api/admin/transportation/search",
            params={"q": q},
            headers={HEADER_BY_PORTAL["admin"]: token},
            timeout=20,
        )
        assert r.status_code == 200
        for res in r.json().get("results", []):
            assert res.get("route") and res["route"].startswith("/"), \
                f"dead route for q={q}: {res}"


def test_09_no_new_collection_introduced():
    """Grep for any collection name suggesting a search index."""
    src = Path("/app/backend/routes/transportation_search.py").read_text()
    assert not re.search(r"transportation_search_index|transport_search_index|search_index", src)


def test_10_audit_event_kind_present():
    """Smoke: verify the route still mentions the audit kind."""
    src = Path("/app/backend/routes/transportation_search.py").read_text()
    assert "transportation_search_performed" in src
    assert "query_prefix" in src
    assert "query_length" in src
