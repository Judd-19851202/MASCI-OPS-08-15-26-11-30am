"""iter437 Phase Sigma-III · P0 · Magic-link driver_id validation tests.

Combines:
  - Unit tests for `_validate_driver_eligibility` (Mongo-backed).
  - Integration smoke tests via live API.

Run with: cd /app/backend && python3 -m pytest tests/test_iter437_magic_link_hardening.py -v
"""
from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

import pytest
import requests


def _arun(coro):
    """Run a coroutine to completion on a module-shared event loop.

    iter437 Phase Sigma-III · safer than ``asyncio.get_event_loop()``
    because pytest-playwright's anyio fixture may already be using the
    default loop. We maintain ONE persistent loop for this module so
    Motor's client (bound at first use) survives across tests instead
    of breaking on "Event loop is closed".
    """
    global _MODULE_LOOP
    try:
        loop = _MODULE_LOOP
    except NameError:
        loop = None
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        globals()["_MODULE_LOOP"] = loop
    return loop.run_until_complete(coro)

# Bootstrap env
for line in Path("/app/backend/.env").read_text().splitlines():
    if "=" not in line or line.strip().startswith("#"):
        continue
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

BASE = next(
    line.split("=", 1)[1].strip().strip('"')
    for line in Path("/app/frontend/.env").read_text().splitlines()
    if line.startswith("REACT_APP_BACKEND_URL")
)


import driver_sessions as DS  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def dispatch_token():
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={
            "email": os.environ["SUPER_ADMIN_EMAIL"],
            "password": os.environ["SUPER_ADMIN_BOOTSTRAP_PASSWORD"],
        },
        timeout=15,
    )
    return r.json()["portal_tokens"]["dispatch"]


@pytest.fixture()
def disabled_employee(db):
    """Seed a disabled employee row for this test, clean up after."""
    eid = f"sigma3-disabled-{uuid.uuid4().hex[:8]}"

    async def setup():
        await db.employees.insert_one({
            "id": eid, "name": "Sigma3 Disabled Test", "disabled": True,
        })

    async def teardown():
        await db.employees.delete_one({"id": eid})

    _arun(setup())
    yield eid
    _arun(teardown())


# ---------------------------------------------------------------------------
# Unit tests — direct helper call
# ---------------------------------------------------------------------------
def test_validate_rejects_missing_driver_id(db):
    async def go():
        with pytest.raises(DS.DriverIneligibleError) as exc:
            await DS._validate_driver_eligibility(db, "")
        assert exc.value.code == "missing_driver_id"

    _arun(go())


def test_validate_rejects_unknown_driver(db):
    async def go():
        with pytest.raises(DS.DriverIneligibleError) as exc:
            await DS._validate_driver_eligibility(db, f"nope-{uuid.uuid4().hex}")
        assert exc.value.code == "driver_not_found"

    _arun(go())


def test_validate_rejects_disabled_employee(db, disabled_employee):
    async def go():
        with pytest.raises(DS.DriverIneligibleError) as exc:
            await DS._validate_driver_eligibility(db, disabled_employee)
        assert exc.value.code == "driver_disabled"

    _arun(go())


def test_validate_accepts_real_employee(db):
    """Find a real, non-disabled employee and accept it."""
    async def go():
        emp = await db.employees.find_one(
            {"disabled": {"$ne": True}, "active": {"$ne": False}}, {"id": 1},
        )
        assert emp, "no usable employee in db for this test"
        result = await DS._validate_driver_eligibility(db, emp["id"])
        assert result["id"] == emp["id"]

    _arun(go())


# ---------------------------------------------------------------------------
# HTTP integration tests — live route
# ---------------------------------------------------------------------------
def test_magic_link_route_rejects_unknown_driver(dispatch_token):
    r = requests.post(
        f"{BASE}/api/dispatch/driver/magic-link",
        headers={"X-Dispatch-Token": dispatch_token, "Content-Type": "application/json"},
        json={"driver_id": f"unknown-{uuid.uuid4().hex}"},
        timeout=10,
    )
    assert r.status_code == 404, r.text[:200]
    body = r.json()
    detail = body.get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("code") == "driver_not_found"


def test_magic_link_route_rejects_empty_driver_id(dispatch_token):
    """Pydantic min_length=1 → 422. Either 400 or 422 is acceptable."""
    r = requests.post(
        f"{BASE}/api/dispatch/driver/magic-link",
        headers={"X-Dispatch-Token": dispatch_token, "Content-Type": "application/json"},
        json={"driver_id": ""},
        timeout=10,
    )
    assert r.status_code in (400, 422)


def test_magic_link_route_accepts_real_employee(dispatch_token):
    employees = requests.get(f"{BASE}/api/employees", timeout=10).json()
    arr = employees if isinstance(employees, list) else (employees.get("employees") or employees.get("items") or [])
    assert arr, "no employees available"
    real_id = arr[0]["id"]
    r = requests.post(
        f"{BASE}/api/dispatch/driver/magic-link",
        headers={"X-Dispatch-Token": dispatch_token, "Content-Type": "application/json"},
        json={"driver_id": real_id},
        timeout=10,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("ok") is True
    assert body.get("magic_token")
    assert body.get("expires_at")
