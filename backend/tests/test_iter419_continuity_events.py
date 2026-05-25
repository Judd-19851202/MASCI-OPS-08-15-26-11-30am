"""iter419 · Phase 21.0 · Operational Exception Continuity tests.

Walking-skeleton verification:
1. Canonical kinds list returns the 5 locked continuity-event kinds.
2. Anonymous list/create blocked.
3. Dispatch/admin can create a continuity event tied to an assignment.
4. Public shape excludes Mongo _id (sanitization).
5. Unknown kind → 400.
6. Missing assignment → 404.
7. by-assignment listing returns events in creation order.
8. Narrative truncated at 500 chars.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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


CANONICAL_KINDS = {
    "TRAILER_SWAP",
    "REASSIGNED_DURING_WAITING",
    "STALE_ASSIGNMENT_RECOVERED",
    "DELAYED_LIFECYCLE_UPDATE",
    "ASSIGNMENT_REASSIGNED",
}


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter419-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


@pytest.fixture(scope="module")
def assignment(hdrs) -> dict:
    r = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-iter419",
            "driver_name": "iter419 Driver",
            "haul_type": "Material",
            "project_number": "9999",
            "material": "Asphalt",
        },
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["assignment"]


def _anon_status(method: str, path: str, body: dict | None = None) -> int:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"User-Agent": "Mozilla/5.0 (iter419 anon test)"}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


# ──────────────────────────────────────────────────────────────
# 1. Kinds list (any portal token)
# ──────────────────────────────────────────────────────────────
def test_iter419_kinds_list_admin_ok():
    r = requests.get(f"{API}/dispatch/continuity-events/kinds", timeout=10)
    assert r.status_code == 200, r.text
    kinds = set(r.json().get("kinds") or [])
    assert kinds == CANONICAL_KINDS


def test_iter419_kinds_list_anon_blocked():
    assert _anon_status("GET", "/dispatch/continuity-events/kinds") == 401


# ──────────────────────────────────────────────────────────────
# 2. Create happy path
# ──────────────────────────────────────────────────────────────
def test_iter419_create_event_happy_path(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={
            "kind": "TRAILER_SWAP",
            "assignment_id": assignment["id"],
            "narrative": "Trailer T-12 swapped to T-09 at Plant A",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    assert body["kind"] == "TRAILER_SWAP"
    assert body["assignment_id"] == assignment["id"]
    assert body["narrative"].startswith("Trailer T-12")
    assert body["captured_role"]
    assert body["created_at"]
    # NO Mongo _id leakage
    assert "_id" not in body


# ──────────────────────────────────────────────────────────────
# 3. Unknown kind rejected
# ──────────────────────────────────────────────────────────────
def test_iter419_unknown_kind_rejected(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={"kind": "INVENTED_KIND", "assignment_id": assignment["id"]},
        timeout=10,
    )
    assert r.status_code == 400, r.text


# ──────────────────────────────────────────────────────────────
# 4. Unknown assignment → 404
# ──────────────────────────────────────────────────────────────
def test_iter419_unknown_assignment_404(hdrs):
    r = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={
            "kind": "TRAILER_SWAP",
            "assignment_id": "does-not-exist-" + uuid.uuid4().hex[:8],
        },
        timeout=10,
    )
    assert r.status_code == 404, r.text


# ──────────────────────────────────────────────────────────────
# 5. Anon create blocked
# ──────────────────────────────────────────────────────────────
def test_iter419_anon_create_blocked(assignment):
    code = _anon_status(
        "POST", "/dispatch/continuity-events",
        body={"kind": "TRAILER_SWAP", "assignment_id": assignment["id"]},
    )
    assert code == 401


# ──────────────────────────────────────────────────────────────
# 6. by-assignment list returns events oldest→newest
# ──────────────────────────────────────────────────────────────
def test_iter419_list_by_assignment(assignment, hdrs):
    # Add a second event so we exercise ordering
    r1 = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={
            "kind": "DELAYED_LIFECYCLE_UPDATE",
            "assignment_id": assignment["id"],
            "narrative": "State arrived late · weak signal at pit",
        },
        timeout=15,
    )
    assert r1.status_code == 200, r1.text

    r = requests.get(
        f"{API}/dispatch/continuity-events/by-assignment/{assignment['id']}",
        headers=hdrs,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] >= 2
    events = body["events"]
    kinds = [e["kind"] for e in events]
    assert "TRAILER_SWAP" in kinds
    assert "DELAYED_LIFECYCLE_UPDATE" in kinds
    # Oldest first (creation order)
    times = [e["created_at"] for e in events]
    assert times == sorted(times)
    # No _id leakage
    for e in events:
        assert "_id" not in e


# ──────────────────────────────────────────────────────────────
# 7. Narrative truncated to 500 chars
# ──────────────────────────────────────────────────────────────
def test_iter419_narrative_max_length(assignment, hdrs):
    long_text = "x" * 1200
    r = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={
            "kind": "ASSIGNMENT_REASSIGNED",
            "assignment_id": assignment["id"],
            "narrative": long_text,
        },
        timeout=15,
    )
    # Pydantic may either reject (422) or accept-and-truncate; both are
    # operationally safe. Verify one of those happens, never an open
    # 500-char-bypass.
    if r.status_code == 200:
        body = r.json()
        assert len(body["narrative"]) <= 500
    else:
        assert r.status_code in (400, 422), r.text


# ──────────────────────────────────────────────────────────────
# 8. Missing assignment_id rejected
# ──────────────────────────────────────────────────────────────
def test_iter419_missing_assignment_id(hdrs):
    r = requests.post(
        f"{API}/dispatch/continuity-events",
        headers=hdrs,
        json={"kind": "TRAILER_SWAP", "assignment_id": ""},
        timeout=10,
    )
    assert r.status_code in (400, 422), r.text
