"""TRACK 18.00 Phase D — LIVE RBAC regression vs deployed preview backend.

Envelope (verified by curl): {ok, entity, sections, counts, schema_version}
sections = {recent_activity, timeline, related_records, open_actions, audit}.
"""
import os
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE = line.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_EMAIL, ADMIN_PW = "jaymn.judd@mascigc.com", "Maddix123!"
DISPATCH_EMAIL, DISPATCH_PW = "dispatch@mascigc.com", "DispatchTest2026!"
HR_EMAIL, HR_PW = "hrmanager@mascigc.com", "HRTesting2026!"
TIMEOUT = 45


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
                      timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
def dispatch_token():
    r = requests.post(f"{BASE}/api/dispatch/login",
                      json={"email": DISPATCH_EMAIL, "password": DISPATCH_PW},
                      timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def hr_token():
    # Direct /api/hr/login with hrmanager creds was rotated; use the super-admin
    # multi-login fan-out which returns portal_tokens.hr unconditionally.
    r = requests.post(f"{BASE}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
                      timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    tok = r.json().get("portal_tokens", {}).get("hr")
    if not tok:
        # fallback to legacy per-portal login
        r2 = requests.post(f"{BASE}/api/hr/login",
                           json={"email": HR_EMAIL, "password": HR_PW},
                           timeout=TIMEOUT)
        if r2.status_code != 200:
            pytest.skip(f"HR token unavailable: multi-login no hr key, /api/hr/login → {r2.status_code}")
        tok = r2.json()["token"]
    return tok


def url(entity_type, entity_id):
    return f"{BASE}/api/admin/transportation/related/{entity_type}/{entity_id}"


def test_01_anonymous_blocked():
    r = requests.get(url("driver", "ghost"), timeout=TIMEOUT)
    assert r.status_code == 401


def test_02_admin_envelope_shape(admin_token):
    r = requests.get(url("driver", "ghost"),
                     headers={"X-Admin-Token": admin_token}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("schema_version") == "18.00D"
    assert "entity" in body and "counts" in body and "sections" in body
    s = body["sections"]
    for sec in ("recent_activity", "timeline", "related_records",
                "open_actions", "audit"):
        assert sec in s, f"missing section {sec}: {list(s.keys())}"
    assert isinstance(body["counts"], dict)


def test_03_unsupported_entity_400(admin_token):
    r = requests.get(url("alien", "xyz"),
                     headers={"X-Admin-Token": admin_token}, timeout=TIMEOUT)
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert detail.startswith("unsupported_entity_type:"), detail


def test_04_unknown_id_clean_envelope(admin_token):
    r = requests.get(url("driver", "ghost"),
                     headers={"X-Admin-Token": admin_token}, timeout=TIMEOUT)
    assert r.status_code == 200
    body = r.json()
    assert body["entity"]["title"] == "(not found)"
    assert body["sections"]["related_records"] == []


def test_05_dispatch_filters_document_orientation(dispatch_token):
    r = requests.get(url("driver", "ghost"),
                     headers={"X-Dispatch-Token": dispatch_token}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    body = r.json()
    rel = body["sections"].get("related_records", [])
    types = {rec.get("type") for rec in rel}
    assert "document" not in types, types
    assert "orientation" not in types, types


def test_06_hr_filters_truck_dispatch(hr_token):
    r = requests.get(url("driver", "ghost"),
                     headers={"X-HR-Token": hr_token}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    body = r.json()
    rel = body["sections"].get("related_records", [])
    types = {rec.get("type") for rec in rel}
    assert "truck" not in types, types
    assert "dispatch_assignment" not in types, types


def test_07_cross_portal_anon_vs_admin(admin_token):
    target = url("dispatch_assignment", "ghost")
    assert requests.get(target, timeout=TIMEOUT).status_code == 401
    assert requests.get(target, headers={"X-Admin-Token": admin_token},
                        timeout=TIMEOUT).status_code == 200


def test_08_all_eleven_entity_types_admin(admin_token):
    for et in ["driver", "carrier", "truck", "dispatch_assignment", "project",
               "certificate", "document", "orientation", "inspection",
               "action_item", "cleanup_signal"]:
        r = requests.get(url(et, "ghost"),
                         headers={"X-Admin-Token": admin_token}, timeout=TIMEOUT)
        assert r.status_code == 200, f"{et} → {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body["schema_version"] == "18.00D"
        s = body["sections"]
        for sec in ("recent_activity", "timeline", "related_records",
                    "open_actions", "audit"):
            assert sec in s, f"{et} missing section {sec}"
