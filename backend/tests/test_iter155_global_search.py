"""Iter155 · Phase G · GLOBAL SEARCH — backend tests.

Tests:
  * Auth gate — no portal token => 401
  * Empty / too-short q => 422
  * Safety role — sees safety-visible kinds; cannot see hr/leadership-only kinds
  * HR role — sees employees/training/docs; CANNOT see incidents/CAs/fire_ext
  * Kinds filter — narrows scope, never expands it
  * Lightweight payload — rows have id/title/url; NO raw bodies/PII
  * Permission-safe explicit request: HR requesting fire_extinguishers => empty
"""
import os
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PW = "SafetyTest2026!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRTesting2026!"

# Override conftest's auto-injected X-Admin-Token so we can exercise
# the real portal-token resolution paths. setdefault won't clobber an
# explicit empty string.
NO_ADMIN = {"X-Admin-Token": ""}

TAG = f"TEST_iter155_{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PW},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def hr_token():
    r = requests.post(
        f"{BASE_URL}/api/hr/login",
        json={"email": HR_EMAIL, "password": HR_PW},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"HR login failed: {r.status_code} {r.text}")
    return r.json()["token"]


def test_anon_returns_401():
    r = requests.get(
        f"{BASE_URL}/api/search?q=test",
        headers=NO_ADMIN, timeout=20,
    )
    assert r.status_code == 401


def test_empty_q_rejected(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 422


def test_short_q_rejected(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=a",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 422


def test_safety_scope_has_safety_kinds(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=3",
        headers={"X-Safety-Token": safety_token, **NO_ADMIN}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["role"] == "safety"
    scope = set(d["scope"])
    # Safety MUST see these kinds
    for k in ("tasks", "notifications", "incidents", "corrective_actions",
              "fire_extinguishers", "safety_documents", "safety_training",
              "document_expirations", "employees", "equipment"):
        assert k in scope, f"safety scope missing {k}"
    # Safety MUST NOT see leadership-only kinds
    for k in ("field_leadership", "po_requests", "projects",
              "operations_events"):
        assert k not in scope, f"safety scope unexpectedly includes {k}"


def test_hr_scope_excludes_safety_only_kinds(hr_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=3",
        headers={"X-HR-Token": hr_token, **NO_ADMIN}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["role"] == "hr"
    scope = set(d["scope"])
    for k in ("employees", "safety_training", "document_expirations",
              "field_leadership", "po_requests", "tasks", "notifications"):
        assert k in scope, f"hr scope missing {k}"
    # HR MUST NOT see incidents / CAs / fire_extinguishers / safety_documents
    for k in ("incidents", "corrective_actions", "fire_extinguishers",
              "safety_documents", "equipment", "projects", "operations_events"):
        assert k not in scope, f"hr scope leak: {k}"


def test_hr_cannot_force_safety_only_kinds(hr_token):
    """HR explicitly requesting fire_extinguishers => empty scope, total 0."""
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&kinds=fire_extinguishers,incidents",
        headers={"X-HR-Token": hr_token, **NO_ADMIN}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["scope"] == []
    assert d["total"] == 0
    assert d["groups"] == []


def test_kinds_filter_narrows_only(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&kinds=tasks,corrective_actions",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    assert set(d["scope"]) <= {"tasks", "corrective_actions"}
    for g in d["groups"]:
        assert g["kind"] in ("tasks", "corrective_actions")


def test_payload_lightweight(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=2",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    # Every row must be: id, title, url, kind. No raw body/description/image.
    for g in d["groups"]:
        for row in g["rows"]:
            assert "id" in row and row["id"]
            assert "title" in row and row["title"]
            assert "kind" in row
            # FORBIDDEN keys — these would be PII / heavy payload
            for forbidden in ("body", "description", "signature_image",
                              "file_data", "image_data", "raw"):
                assert forbidden not in row, (
                    f"row leaked '{forbidden}' for kind={row['kind']}"
                )


def test_limit_respected(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=2",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    for g in d["groups"]:
        assert len(g["rows"]) <= 2, f"limit violated for {g['kind']}"


def test_limit_bounds(safety_token):
    # limit > 15 must 422
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=100",
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 422


def test_q_max_length(safety_token):
    too_long = "x" * 81
    r = requests.get(
        f"{BASE_URL}/api/search",
        params={"q": too_long},
        headers={"X-Safety-Token": safety_token}, timeout=20,
    )
    assert r.status_code == 422


def test_response_carries_role_and_scope(safety_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test",
        headers={"X-Safety-Token": safety_token, **NO_ADMIN}, timeout=20,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["q"] == "test"
    assert d["role"] == "safety"
    assert isinstance(d["scope"], list)
    assert isinstance(d["total"], int)
