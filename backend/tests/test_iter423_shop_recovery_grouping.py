"""iter423 · Phase 25 · Shop Operational Cognition Convergence tests.

Backend additive walking-skeleton verification:
  1. /api/dispatch/recovery/by-shop is RBAC-gated (anon 401).
  2. /by-shop returns the stable bucket scaffold even when empty.
  3. /by-shop groups active recoveries by canonical sub-state.
  4. waiting_on_parts is reported separately in summary.
  5. returned_to_service appears in restored_recent (7-day window).
  6. summary.returned_today only counts today's transitions.
  7. /api/dispatch/continuity-events/recent returns newest-first, capped.
  8. /by-shop sanitises every row (no Mongo _id leakage).
  9. Four new guidance articles are registered.
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter423-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


def _create_assignment(hdrs, suffix: str) -> dict:
    body = {
        "truck_id": f"T-iter423{suffix}",
        "driver_name": f"iter423 Driver {suffix}",
        "haul_type": "Material",
        "project_number": "9999",
        "material": "Asphalt",
    }
    r = requests.post(f"{API}/dispatch/assignments", headers=hdrs, json=body, timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["assignment"]


def _transition_recovery(hdrs, aid: str, to_state: str, note: str = "") -> dict:
    r = requests.post(
        f"{API}/dispatch/recovery/{aid}/transition",
        headers=hdrs,
        json={"to_state": to_state, "note": note},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()


# ──────────────────────────────────────────────────────────────
# 1. /by-shop RBAC
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_anon_blocked():
    import urllib.error
    import urllib.request
    req = urllib.request.Request(
        f"{API}/dispatch/recovery/by-shop",
        headers={"User-Agent": "Mozilla/5.0 (iter423 anon)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert False, f"Expected 401 · got {r.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 401, e.code


# ──────────────────────────────────────────────────────────────
# 2. Stable empty-tenant scaffold
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_empty_tenant_scaffold(hdrs):
    r = requests.get(f"{API}/dispatch/recovery/by-shop", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    buckets = body["buckets"]
    # All six canonical active-recovery buckets present and empty
    for k in ("reported", "acknowledged", "diagnosing",
              "waiting_on_parts", "repair_active", "operational_test"):
        assert k in buckets
        assert buckets[k] == [], k
    assert body["restored_recent"] == []
    assert body["summary"]["total_active"] == 0
    assert body["summary"]["waiting_on_parts"] == 0
    assert body["summary"]["returned_today"] == 0


# ──────────────────────────────────────────────────────────────
# 3. Active recovery grouping
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_groups_active_recoveries(hdrs):
    a1 = _create_assignment(hdrs, "-A")
    a2 = _create_assignment(hdrs, "-B")
    a3 = _create_assignment(hdrs, "-C")
    _transition_recovery(hdrs, a1["id"], "acknowledged", "Truck A acknowledged")
    _transition_recovery(hdrs, a1["id"], "diagnosing", "Truck A diagnosing")
    _transition_recovery(hdrs, a2["id"], "acknowledged")
    _transition_recovery(hdrs, a3["id"], "acknowledged")
    _transition_recovery(hdrs, a3["id"], "diagnosing")
    _transition_recovery(hdrs, a3["id"], "repair_active", "parts on hand")

    r = requests.get(f"{API}/dispatch/recovery/by-shop", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    buckets = body["buckets"]
    # a1 → diagnosing · a2 → acknowledged · a3 → repair_active
    assert any(row["assignment_id"] == a1["id"] for row in buckets["diagnosing"])
    assert any(row["assignment_id"] == a2["id"] for row in buckets["acknowledged"])
    assert any(row["assignment_id"] == a3["id"] for row in buckets["repair_active"])
    assert body["summary"]["total_active"] >= 3
    # No _id leakage anywhere
    for k, rows in buckets.items():
        for row in rows:
            assert "_id" not in row, f"_id leaked in bucket {k}"
    # truck_id + driver_name surface for downstream impact line
    diag_a1 = next(r for r in buckets["diagnosing"] if r["assignment_id"] == a1["id"])
    assert diag_a1["truck_id"] == "T-iter423-A"
    assert diag_a1["driver_name"]
    assert diag_a1["last_recovery_at"]


# ──────────────────────────────────────────────────────────────
# 4. waiting_on_parts surfaces in summary
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_waiting_on_parts_summary(hdrs):
    a = _create_assignment(hdrs, "-WAIT")
    _transition_recovery(hdrs, a["id"], "acknowledged")
    _transition_recovery(hdrs, a["id"], "diagnosing")
    _transition_recovery(hdrs, a["id"], "waiting_on_parts", "sensor ordered, ETA Thursday")

    r = requests.get(f"{API}/dispatch/recovery/by-shop", headers=hdrs, timeout=10)
    body = r.json()
    waiting = body["buckets"]["waiting_on_parts"]
    assert any(row["assignment_id"] == a["id"] for row in waiting)
    assert body["summary"]["waiting_on_parts"] >= 1
    row = next(r for r in waiting if r["assignment_id"] == a["id"])
    assert row["last_recovery_note"] == "sensor ordered, ETA Thursday"


# ──────────────────────────────────────────────────────────────
# 5. returned_to_service appears in restored_recent
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_returned_to_service_in_restored(hdrs):
    a = _create_assignment(hdrs, "-RET")
    _transition_recovery(hdrs, a["id"], "acknowledged")
    _transition_recovery(hdrs, a["id"], "diagnosing")
    _transition_recovery(hdrs, a["id"], "repair_active")
    _transition_recovery(hdrs, a["id"], "operational_test")
    _transition_recovery(hdrs, a["id"], "returned_to_service", "Back in line")

    r = requests.get(f"{API}/dispatch/recovery/by-shop", headers=hdrs, timeout=10)
    body = r.json()
    restored = body["restored_recent"]
    assert any(row["assignment_id"] == a["id"] for row in restored)
    row = next(r for r in restored if r["assignment_id"] == a["id"])
    assert row["truck_id"] == "T-iter423-RET"
    assert row["returned_at"]
    assert row["note"] == "Back in line"
    # Should NOT also appear in any active bucket
    for k, rows in body["buckets"].items():
        assert not any(rr["assignment_id"] == a["id"] for rr in rows), f"leaked into {k}"


# ──────────────────────────────────────────────────────────────
# 6. summary.returned_today reflects today's transitions only
# ──────────────────────────────────────────────────────────────
def test_iter423_by_shop_returned_today_count(hdrs):
    a = _create_assignment(hdrs, "-TODAY")
    _transition_recovery(hdrs, a["id"], "acknowledged")
    _transition_recovery(hdrs, a["id"], "returned_to_service")
    r = requests.get(f"{API}/dispatch/recovery/by-shop", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["summary"]["returned_today"] >= 1


# ──────────────────────────────────────────────────────────────
# 7. /continuity-events/recent newest-first capped
# ──────────────────────────────────────────────────────────────
def test_iter423_continuity_events_recent_ordering(hdrs):
    a = _create_assignment(hdrs, "-EVT")
    # Create three events
    for kind, narrative in (
        ("TRAILER_SWAP", "First event"),
        ("DELAYED_LIFECYCLE_UPDATE", "Second event"),
        ("STALE_ASSIGNMENT_RECOVERED", "Third event"),
    ):
        r = requests.post(
            f"{API}/dispatch/continuity-events",
            headers=hdrs,
            json={"kind": kind, "assignment_id": a["id"], "narrative": narrative},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        time.sleep(0.01)  # ensure distinct created_at ordering

    r = requests.get(
        f"{API}/dispatch/continuity-events/recent",
        headers=hdrs, params={"limit": 25}, timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    events = body["events"]
    assert len(events) >= 3
    # Filter to this tenant's events with our narratives
    ours = [e for e in events if e.get("assignment_id") == a["id"]]
    assert len(ours) == 3
    # Newest first
    times = [e["created_at"] for e in ours]
    assert times == sorted(times, reverse=True)
    # No _id leakage
    for e in events:
        assert "_id" not in e


def test_iter423_continuity_events_recent_limit_clamped(hdrs):
    r = requests.get(
        f"{API}/dispatch/continuity-events/recent",
        headers=hdrs, params={"limit": 999}, timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["events"]) <= 50


def test_iter423_continuity_events_recent_anon_blocked():
    import urllib.error
    import urllib.request
    req = urllib.request.Request(
        f"{API}/dispatch/continuity-events/recent",
        headers={"User-Agent": "Mozilla/5.0 (iter423 anon)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            assert False, f"Expected 401 · got {r.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 401, e.code


# ──────────────────────────────────────────────────────────────
# 8. Guidance articles registered + indexed by tags
# ──────────────────────────────────────────────────────────────
def test_iter423_guidance_articles_registered(hdrs):
    # Help-search endpoint should find each new article
    for article_id, query in (
        ("dls-equipment-needing-attention", "equipment needing attention"),
        ("dls-active-recovery-work", "active recovery work"),
        ("dls-waiting-on-parts", "waiting on parts"),
        ("dls-returned-to-service", "returned to service"),
    ):
        # Try the article fetch endpoint (lightweight check)
        r = requests.get(
            f"{API}/guidance/articles/{article_id}",
            headers=hdrs, timeout=10,
        )
        assert r.status_code == 200, f"{article_id} → {r.status_code}: {r.text[:120]}"
        body = r.json()
        assert body.get("id") == article_id
        assert body.get("title")
        assert isinstance(body.get("body"), list) and len(body["body"]) >= 1
