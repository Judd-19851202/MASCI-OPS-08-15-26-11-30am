"""
test_iter407_assignment_lookups.py · Phase 14 · Dispatch Assignment Issuance.

Backend regression for the dispatcher-gated assignment-lookups endpoint
that powers the iter407 Create Assignment drawer.

Covers:
  • GET /api/dispatch/driver/assignment-lookups requires dispatch+admin
  • Empty tenant returns empty memory lists (no leakage from defaults)
  • Recent project + material + source + destination distinct values
    are surfaced from existing dispatch_assignments (operational memory)
  • Multi-row continuity: 3 inserts → 3 distinct labels per category
"""
from __future__ import annotations

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


def _anon_status(path: str) -> int:
    """Bypass conftest's requests auto-injection by using urllib directly."""
    req = urllib.request.Request(
        f"{API}{path}", method="GET",
        headers={"User-Agent": "Mozilla/5.0 (iter407 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _dispatch_token():
    """Admin path is simpler for fork tests — admin satisfies the gate."""
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "MASCI1982!"},
        timeout=15,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token available in this env.")


# ════════════════════════════════════════════════════════════════════
# 1. Auth gate
# ════════════════════════════════════════════════════════════════════
def test_assignment_lookups_requires_auth():
    assert _anon_status("/dispatch/driver/assignment-lookups") == 401


def test_assignment_lookups_authorized_returns_shape():
    hdrs = _dispatch_token()
    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    for k in ("recent_projects", "recent_materials", "recent_sources", "recent_destinations"):
        assert k in j and isinstance(j[k], list), f"{k} missing or wrong type"


# ════════════════════════════════════════════════════════════════════
# 2. Empty tenant returns empty recent_* lists (materials/sources/dest
#    stay tenant-scoped; projects are platform-level per iter408).
# ════════════════════════════════════════════════════════════════════
def test_empty_tenant_returns_empty_recents():
    hdrs = _dispatch_token()
    hdrs["X-Tenant-Id"] = f"iter407-empty-{uuid.uuid4().hex[:8]}"
    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200
    j = r.json()
    # iter408: recent_materials/sources/destinations remain tenant-scoped
    # (they're truly operational memory of this tenant's hauls).
    assert j["recent_materials"] == []
    assert j["recent_sources"] == []
    assert j["recent_destinations"] == []
    # recent_projects is platform-wide (daily_reports + assignments)
    # so we only check shape, not emptiness.
    assert isinstance(j["recent_projects"], list)


# ════════════════════════════════════════════════════════════════════
# 3. Operational memory feeds itself — create assignments, see recents
# ════════════════════════════════════════════════════════════════════
def test_recents_surface_from_existing_assignments():
    hdrs = _dispatch_token()
    tenant = f"iter407-mem-{uuid.uuid4().hex[:8]}"
    hdrs["X-Tenant-Id"] = tenant

    # Seed 3 distinct assignments via the existing iter392 endpoint.
    for i in range(3):
        payload = {
            "truck_id": f"T-IT407-{i}",
            "project_number": f"PRJ-{i}",
            "project_name": f"Project {i}",
            "material": f"Material {i}",
            "source_location": f"Plant {i}",
            "destination": f"Dest {i}",
        }
        rc = requests.post(
            f"{API}/dispatch/assignments",
            headers=hdrs, json=payload, timeout=15,
        )
        assert rc.status_code == 200, rc.text

    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    assert r.status_code == 200
    j = r.json()

    proj_numbers = {p["project_number"] for p in j["recent_projects"]}
    assert {"PRJ-0", "PRJ-1", "PRJ-2"}.issubset(proj_numbers)
    # project_name carried through
    by_num = {p["project_number"]: p for p in j["recent_projects"]}
    assert by_num["PRJ-1"]["project_name"] == "Project 1"

    materials = {m["label"] for m in j["recent_materials"]}
    assert {"Material 0", "Material 1", "Material 2"}.issubset(materials)

    sources = {s["label"] for s in j["recent_sources"]}
    assert {"Plant 0", "Plant 1", "Plant 2"}.issubset(sources)

    destinations = {d["label"] for d in j["recent_destinations"]}
    assert {"Dest 0", "Dest 1", "Dest 2"}.issubset(destinations)


def test_recents_dedupe_same_value():
    """Memory lists return DISTINCT values — same project twice = one entry."""
    hdrs = _dispatch_token()
    tenant = f"iter407-dedupe-{uuid.uuid4().hex[:8]}"
    hdrs["X-Tenant-Id"] = tenant

    payload = {
        "truck_id": "T-DUP-A",
        "project_number": "DUP-PRJ",
        "project_name": "Duplicate Project",
        "material": "DUP-MAT",
        "source_location": "DUP-SRC",
        "destination": "DUP-DST",
    }
    for _ in range(3):
        payload["truck_id"] = f"T-DUP-{uuid.uuid4().hex[:4]}"
        rc = requests.post(
            f"{API}/dispatch/assignments",
            headers=hdrs, json=payload, timeout=15,
        )
        assert rc.status_code == 200

    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert sum(1 for p in j["recent_projects"] if p["project_number"] == "DUP-PRJ") == 1
    assert sum(1 for m in j["recent_materials"] if m["label"] == "DUP-MAT") == 1
    assert sum(1 for s in j["recent_sources"] if s["label"] == "DUP-SRC") == 1
    assert sum(1 for d in j["recent_destinations"] if d["label"] == "DUP-DST") == 1


# ════════════════════════════════════════════════════════════════════
# 4. Tenant isolation
# ════════════════════════════════════════════════════════════════════
def test_tenant_isolation_in_recents():
    hdrs_a = _dispatch_token()
    hdrs_b = dict(hdrs_a)
    tenant_a = f"iter407-iso-A-{uuid.uuid4().hex[:6]}"
    tenant_b = f"iter407-iso-B-{uuid.uuid4().hex[:6]}"
    hdrs_a["X-Tenant-Id"] = tenant_a
    hdrs_b["X-Tenant-Id"] = tenant_b

    # Seed assignment only in tenant A
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs_a,
        json={
            "truck_id": "T-ISO-A",
            "project_number": "ISO-A-PRJ",
            "material": "ISO-A-MAT",
            "source_location": "ISO-A-SRC",
            "destination": "ISO-A-DST",
        },
        timeout=15,
    )
    assert rc.status_code == 200

    # Tenant B should see NONE of it.
    rb = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs_b, timeout=15,
    )
    jb = rb.json()
    assert all(p["project_number"] != "ISO-A-PRJ" for p in jb["recent_projects"])
    assert all(m["label"] != "ISO-A-MAT" for m in jb["recent_materials"])
    assert all(s["label"] != "ISO-A-SRC" for s in jb["recent_sources"])
    assert all(d["label"] != "ISO-A-DST" for d in jb["recent_destinations"])


# ════════════════════════════════════════════════════════════════════
# 5. No new collections — implicit via response shape
# ════════════════════════════════════════════════════════════════════
def test_response_does_not_leak_underscored_or_mongo_fields():
    hdrs = _dispatch_token()
    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    for cat in ("recent_projects", "recent_materials", "recent_sources", "recent_destinations"):
        for row in j[cat]:
            assert "_id" not in row
            for k in row.keys():
                assert not k.startswith("_"), f"Internal field leaked: {k}"
