"""Iter B · Phase 1 · PM scope filter for /api/search + audit helper smoke.

Verifies:
  * PM users searching tasks ONLY see tasks linked to projects in their
    PM scope (linked_project_number ∈ pm_proj). A task whose linked
    project is OUT of scope must NOT appear in their /api/search result.
  * lib/audit.append_audit() importable, runs without crash on a
    non-existent record (best-effort fire-and-forget).
"""
import os
import uuid
import asyncio
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

PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"

NO_ADMIN = {"X-Admin-Token": ""}

TAG = f"TEST_iterB_{uuid.uuid4().hex[:6]}"


# ────────────────────────────────────────────────────────────────────
# PM /api/search scope test
# ────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PW},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token", "")


def test_pm_search_role_is_pm(pm_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=3",
        headers={"X-PM-Token": pm_token, **NO_ADMIN},
        timeout=20,
    )
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert d["role"] == "pm"
    # PM should at least include tasks
    scope = set(d["scope"])
    assert "tasks" in scope


def test_pm_tasks_search_respects_pm_proj(pm_token):
    """Plant 2 tasks via admin: one linked to a project number guaranteed
    OUT of any PM's scope (uuid-named), and confirm the PM cannot retrieve
    it via /api/search?kinds=tasks. We rely on the conftest auto-injecting
    X-Admin-Token for the seeding requests.

    Note: we can't easily plant a task that IS in PM scope because we don't
    know that PM's projects from the API; but the test still proves
    OUT-OF-SCOPE tasks are filtered (the critical security property).
    """
    out_of_scope_proj = f"{TAG}_NO_PM"  # almost certainly not in any PM scope
    seed_payload = {
        "title": f"{TAG}_out_of_scope_task",
        "priority": "High",
        "status": "Open",
        "source_module": "test",
        "linked_project_number": out_of_scope_proj,
        "assignee_role": "pm",
    }
    seed = requests.post(
        f"{BASE_URL}/api/tasks", json=seed_payload, timeout=20,
    )
    # If tasks API isn't open for direct create, skip rather than fail.
    if seed.status_code not in (200, 201):
        pytest.skip(f"Cannot seed task for PM scope test: {seed.status_code}")
    seeded = seed.json()
    seeded_id = seeded.get("id") or seeded.get("task", {}).get("id")
    assert seeded_id, f"no id in seed response: {seeded}"

    try:
        # PM searches for the unique tag — should NOT find the out-of-scope task
        r = requests.get(
            f"{BASE_URL}/api/search",
            params={"q": TAG, "kinds": "tasks", "limit": 15},
            headers={"X-PM-Token": pm_token, **NO_ADMIN},
            timeout=20,
        )
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        # Walk every tasks-group row and ensure our seeded id is absent
        found_ids = set()
        for g in d.get("groups", []):
            if g.get("kind") == "tasks":
                for row in g.get("rows", []):
                    found_ids.add(row.get("id"))
        assert seeded_id not in found_ids, (
            f"PM scope leak — out-of-scope task {seeded_id} visible via "
            f"search. Groups={d.get('groups')}"
        )
    finally:
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/tasks/{seeded_id}", timeout=10)
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────────
# lib/audit.append_audit smoke test
# ────────────────────────────────────────────────────────────────────
def test_append_audit_smoke():
    """Importable; runs without crash on a non-existent record."""
    import sys
    sys.path.insert(0, "/app/backend")
    from lib.audit import append_audit  # noqa: PLC0415

    class _FakeColl:
        async def update_one(self, *a, **kw):
            class R:  # noqa
                matched_count = 0
                modified_count = 0
            return R()

    class _FakeDB:
        def __getitem__(self, name):
            return _FakeColl()

    async def _run():
        return await append_audit(
            _FakeDB(),
            collection="po_requests",
            record_id="nonexistent",
            action="test",
            actor={"role": "test", "name": "Smoke"},
            details={"k": "v"},
        )

    entry = asyncio.get_event_loop().run_until_complete(_run()) \
        if not asyncio.get_event_loop().is_closed() \
        else asyncio.run(_run())
    assert entry["action"] == "test"
    assert entry["actor"]["role"] == "test"
    assert "id" in entry and entry["id"]
    assert "at" in entry


def test_append_audit_swallows_db_error():
    """If the DB update raises, append_audit must not propagate."""
    import sys
    sys.path.insert(0, "/app/backend")
    from lib.audit import append_audit  # noqa: PLC0415

    class _BoomColl:
        async def update_one(self, *a, **kw):
            raise RuntimeError("simulated db down")

    class _BoomDB:
        def __getitem__(self, name):
            return _BoomColl()

    async def _run():
        return await append_audit(
            _BoomDB(),
            collection="po_requests",
            record_id="x",
            action="boom",
        )

    entry = asyncio.run(_run())
    # Still returns an entry — best effort, never raises.
    assert entry["action"] == "boom"
