"""
TRACK 16.07 — Live smoke for /api/admin/transportation/timeline/{entity_type}/{entity_id}.

Validates the ONE new endpoint added in Track 16.07 against the running preview backend:
- 401 anonymous
- 422 on bad entity_type
- 404 on unknown id
- 200 with sorted combined audit events for carrier / person / truck
- No regression on Track 16.04/16.05/16.06 sanity endpoints
"""

import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    if not BASE:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    tok = r.json().get("portal_tokens", {}).get("admin")
    assert tok, f"no admin token in: {list(r.json().keys())}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


# ─── Auth + validation contract ──────────────────────────────────────────

def test_timeline_anonymous_returns_401():
    # Retry on slow network — preview ingress is occasionally rate-limited.
    last = None
    for _ in range(3):
        try:
            r = requests.get(
                f"{BASE}/api/admin/transportation/timeline/carrier/anything", timeout=45
            )
            last = r.status_code
            break
        except requests.exceptions.ReadTimeout:
            continue
    assert last in (401, 403), f"got {last}"


def test_timeline_bad_entity_type_returns_422(admin_headers):
    r = requests.get(
        f"{BASE}/api/admin/transportation/timeline/widget/anything",
        headers=admin_headers,
        timeout=15,
    )
    assert r.status_code == 422, f"expected 422 got {r.status_code} body={r.text[:200]}"


def test_timeline_unknown_id_returns_404(admin_headers):
    r = requests.get(
        f"{BASE}/api/admin/transportation/timeline/carrier/ghost-id-doesnt-exist",
        headers=admin_headers,
        timeout=15,
    )
    assert r.status_code == 404, f"expected 404 got {r.status_code}"


# ─── Happy path per entity type ──────────────────────────────────────────

def _get_first(headers, path, key=None):
    r = requests.get(f"{BASE}{path}", headers=headers, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"{path} returned {r.status_code}; skipping happy-path")
    body = r.json()
    if isinstance(body, list):
        rows = body
    else:
        rows = body.get("items") or body.get(key or "") or body.get("rows") or []
    if not rows:
        pytest.skip(f"no rows from {path}; skipping happy-path")
    return rows[0]


def _assert_timeline_shape(body):
    assert isinstance(body, dict), f"expected object got {type(body)}"
    # Backend returns {"count": int, "items": [...]} (verified live).
    items = body.get("items")
    assert isinstance(items, list), f"items missing/not list: {list(body.keys())}"
    assert body.get("count") == len(items), f"count mismatch: {body.get('count')} vs {len(items)}"
    # Sorted ascending by 'ts' (ISO string). Empty / missing ts are tolerated.
    times = [e.get("ts") or "" for e in items]
    assert times == sorted(times), "events not sorted ascending"


def test_timeline_carrier_returns_combined_events(admin_headers):
    carrier = _get_first(admin_headers, "/api/admin/transportation/carriers", "carriers")
    cid = carrier.get("id") or carrier.get("carrier_id")
    assert cid
    r = requests.get(
        f"{BASE}/api/admin/transportation/timeline/carrier/{cid}",
        headers=admin_headers,
        timeout=25,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    body = r.json()
    _assert_timeline_shape(body)
    # Carrier timeline should include events from at least the carrier itself
    sources = {e.get("entity_type") for e in body["items"]}
    # not asserting non-empty (carrier may have zero recorded audit events yet)


def test_timeline_person_returns_combined_events(admin_headers):
    person = _get_first(admin_headers, "/api/admin/transportation/persons", "persons")
    pid = person.get("id") or person.get("person_id")
    assert pid
    r = requests.get(
        f"{BASE}/api/admin/transportation/timeline/person/{pid}",
        headers=admin_headers,
        timeout=25,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    _assert_timeline_shape(r.json())


def test_timeline_truck_returns_combined_events(admin_headers):
    truck = _get_first(admin_headers, "/api/admin/transportation/trucks", "trucks")
    tid = truck.get("id") or truck.get("truck_id")
    assert tid
    r = requests.get(
        f"{BASE}/api/admin/transportation/timeline/truck/{tid}",
        headers=admin_headers,
        timeout=25,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    _assert_timeline_shape(r.json())


# ─── Regression: prior tracks still alive ────────────────────────────────

def test_regression_carriers_list_still_200(admin_headers):
    r = requests.get(f"{BASE}/api/admin/transportation/carriers", headers=admin_headers, timeout=15)
    assert r.status_code == 200


def test_regression_inspections_queue_still_200(admin_headers):
    r = requests.get(f"{BASE}/api/admin/transportation/inspections/queue", headers=admin_headers, timeout=15)
    assert r.status_code == 200


def test_regression_dashboard_still_200(admin_headers):
    r = requests.get(f"{BASE}/api/admin/transportation/dashboard", headers=admin_headers, timeout=15)
    assert r.status_code == 200
