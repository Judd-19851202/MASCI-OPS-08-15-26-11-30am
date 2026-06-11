"""
Tests for MASCI Live Map Command Surface Alignment Sprint.
Validates /api/operations-map/snapshot vocabulary, auth gate, and regression endpoints.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASS = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("portal_tokens", {}).get("admin")
    assert tok, "admin portal token missing"
    return tok


@pytest.fixture(scope="module")
def snapshot(admin_token):
    r = requests.get(f"{BASE_URL}/api/operations-map/snapshot",
                     headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200, f"snapshot failed: {r.status_code} {r.text[:300]}"
    return r.json()


# --- Auth gate ---
def test_snapshot_requires_admin_token():
    r = requests.get(f"{BASE_URL}/api/operations-map/snapshot", timeout=20)
    assert r.status_code == 401, f"expected 401 without token, got {r.status_code}"


def test_snapshot_invalid_token_rejected():
    r = requests.get(f"{BASE_URL}/api/operations-map/snapshot",
                     headers={"X-Admin-Token": "bogus-token-xyz"}, timeout=20)
    assert r.status_code == 401


# --- Top-level keys ---
def test_snapshot_top_level_keys(snapshot):
    expected = {"ok", "as_of", "operational_summary", "feed_status", "counts",
                "assets", "geofences", "geofence_count", "project_rollups",
                "project_rollups_overflow", "project_rollups_total"}
    missing = expected - set(snapshot.keys())
    assert not missing, f"missing keys: {missing} | actual: {list(snapshot.keys())}"
    assert snapshot["ok"] is True


# --- operational_summary shape & MASCI labels ---
def test_operational_summary_structure(snapshot):
    summary = snapshot["operational_summary"]
    assert isinstance(summary, list), f"expected list, got {type(summary)}"
    assert len(summary) == 6, f"expected 6 tiles, got {len(summary)}"
    by_id = {t["id"]: t for t in summary}
    expected_ids = {"total", "connected", "working", "idle", "attention", "offline"}
    assert set(by_id.keys()) == expected_ids, f"ids mismatch: {set(by_id.keys())}"

    expected_labels = {
        "total":     "Total Assets",
        "connected": "Connected Assets",
        "working":   "Working",
        "idle":      "Idle",
        "attention": "Attention Required",
        "offline":   "Offline",
    }
    for tile_id, label in expected_labels.items():
        assert by_id[tile_id]["label"] == label, \
            f"tile {tile_id}: expected label '{label}', got '{by_id[tile_id]['label']}'"
        assert "value" in by_id[tile_id], \
            f"tile {tile_id} missing value: {by_id[tile_id]}"


def test_feed_status_present(snapshot):
    fs = snapshot["feed_status"]
    assert fs["status"] in ("live", "delayed", "offline")
    assert fs["label"] in ("Live Data", "Delayed Data", "No Recent Updates")


# --- project_rollups shape ---
def test_project_rollups_shape(snapshot):
    rollups = snapshot["project_rollups"]
    assert isinstance(rollups, list), f"expected list, got {type(rollups)}"
    assert len(rollups) <= 5, "snapshot must cap top buckets to 5"
    if len(rollups) > 0:
        required = {"name", "display_name", "bucket_type", "total",
                    "connected_count", "attention_required_count",
                    "offline_count", "last_activity_at",
                    "assignment_source", "assignment_confidence"}
        first = rollups[0]
        missing = required - set(first.keys())
        assert not missing, f"project_rollups[0] missing: {missing} | keys={list(first.keys())}"


def test_project_rollups_ranked_by_attention(snapshot):
    """rollups must be sorted by attention_required_count desc (tie-broken by offline desc, total desc)."""
    rollups = snapshot["project_rollups"]
    if len(rollups) < 2:
        pytest.skip("need >=2 rollups to verify ranking")
    for i in range(len(rollups) - 1):
        a, b = rollups[i], rollups[i + 1]
        ka = (a["attention_required_count"], a["offline_count"], a["total"])
        kb = (b["attention_required_count"], b["offline_count"], b["total"])
        assert ka >= kb, f"rollups not ranked at index {i}: {a['name']}={ka} vs {b['name']}={kb}"


def test_project_rollups_location_fallback(snapshot):
    """When no geofences exist (preview), location buckets must materialize
    instead of collapsing into a single Unassigned/Unknown card."""
    if snapshot.get("geofence_count", 0) > 0:
        pytest.skip("environment has geofences; location fallback test only runs in geofence-free env")
    rollups = snapshot["project_rollups"]
    if not rollups:
        pytest.skip("no rollups to verify")
    sources = {r.get("assignment_source") for r in rollups}
    # When preview lacks geofences but has GPS, expect gps_location buckets.
    if any(a.get("lat") is not None for a in snapshot.get("assets", [])):
        assert "gps_location" in sources or "explicit_project" in sources, \
            f"expected gps_location/explicit_project bucket, got sources={sources}"


def test_project_rollups_no_raw_family_strings(snapshot):
    """rollups must not surface raw event_family strings"""
    import json as _json
    blob = _json.dumps(snapshot["project_rollups"])
    forbidden = ["vehicle_gps", "geofence_enter", "geofence_exit"]
    for f in forbidden:
        assert f not in blob, f"project_rollups contains forbidden raw token '{f}'"


# --- Regression: other operations-map endpoints ---
def test_search_endpoint_responds(admin_token):
    r = requests.get(f"{BASE_URL}/api/operations-map/search",
                     params={"q": "a"},
                     headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code in (200, 400), f"search returned {r.status_code}"


def test_timeline_endpoint_responds(admin_token):
    r = requests.get(f"{BASE_URL}/api/operations-map/timeline",
                     headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code == 200, f"timeline failed: {r.status_code} {r.text[:200]}"


def test_asset_detail_endpoint(admin_token, snapshot):
    assets = snapshot.get("assets") or []
    if not assets:
        pytest.skip("no assets in snapshot to test asset detail")
    key = assets[0].get("unit_number") or assets[0].get("asset_key") or assets[0].get("id")
    if not key:
        pytest.skip("no usable key on first asset")
    r = requests.get(f"{BASE_URL}/api/operations-map/asset/{key}",
                     headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code in (200, 404), f"asset detail returned {r.status_code}"


def test_geofence_endpoint(admin_token, snapshot):
    gfs = snapshot.get("geofences") or []
    if not gfs:
        pytest.skip("no geofences in preview snapshot")
    gid = gfs[0].get("id") or gfs[0].get("geofence_id")
    r = requests.get(f"{BASE_URL}/api/operations-map/geofence/{gid}",
                     headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code in (200, 404)
