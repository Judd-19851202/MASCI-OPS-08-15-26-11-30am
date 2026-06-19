"""TRACK 15.40 · Directory Resolution Regression Test.

Asserts `_enrich_row_with_directory` falls back to the `employees`
collection when `user_directory` does not contain the user, and
resolves `display_name` from the canonical employee record.

Run:
    cd /app/backend && python3 -m pytest tests/test_track_15_40_directory_resolution.py -v
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from routes.project_team_assignments import (  # noqa: E402
    _enrich_row_with_directory,
    _resolve_display_name,
)


def _get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    assert mongo_url and db_name, "MONGO_URL and DB_NAME must be set"
    assert "preview" in db_name.lower() or os.environ.get("APP_ENV") != "production", (
        "Refusing to run regression test against production DB"
    )
    return AsyncIOMotorClient(mongo_url)[db_name]


async def _seed_employee():
    db = _get_db()
    emp_id = f"track1540-{uuid.uuid4()}"
    await db.employees.insert_one({
        "id": emp_id,
        "employee_id": "TRK1540",
        "name": "Track 15.40 TestEmployee",
        "first_name": "Track",
        "last_name": "TestEmployee",
        "email": "track1540@mascicert.local",
        "preferred_name": "T",
    })
    return emp_id


async def _cleanup_employee(emp_id):
    db = _get_db()
    await db.employees.delete_one({"id": emp_id})


def _run(coro):
    """Run an async coroutine in a fresh event loop per test (Motor
    refuses to be shared across event loops in pytest-asyncio default
    mode)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_employee_fallback_by_user_id():
    """When a row's user_id matches employees.id and ud_row is absent,
    resolver must populate display_name from the employee record."""

    async def _t():
        emp_id = await _seed_employee()
        try:
            db = _get_db()
            row = {
                "user_id": emp_id,
                "employee_id": None,
                "email": None,
                "display_name": None,
            }
            await _enrich_row_with_directory(db, row)
            assert row["display_name"] == "Track 15.40 TestEmployee", row["display_name"]
            assert row.get("name") == "Track 15.40 TestEmployee"
            assert row.get("preferred_name") == "T"
            # email mirrored from employees
            assert row.get("email") == "track1540@mascicert.local"
        finally:
            await _cleanup_employee(emp_id)

    _run(_t())


def test_employee_fallback_by_email():
    """When a row carries only an email (no user_id), resolver must
    find employees by email and resolve display_name from `name`."""

    async def _t():
        emp_id = await _seed_employee()
        try:
            db = _get_db()
            row = {
                "user_id": None,
                "employee_id": None,
                "email": "track1540@mascicert.local",
                "display_name": None,
            }
            await _enrich_row_with_directory(db, row)
            # emp_row.name wins over row.email since ud/emp sources are
            # iterated before row in _resolve_display_name.
            assert row["display_name"] == "Track 15.40 TestEmployee", row["display_name"]
        finally:
            await _cleanup_employee(emp_id)

    _run(_t())


def test_unknown_user_falls_back_to_sentinel():
    """When nothing resolves, the resolver returns the operator-visible
    "Unknown person — Admin review required" sentinel."""

    async def _t():
        db = _get_db()
        row = {
            "user_id": None,
            "employee_id": None,
            "email": None,
            "display_name": None,
        }
        await _enrich_row_with_directory(db, row)
        assert row["display_name"] == "Unknown person — Admin review required"

    _run(_t())


def test_alec_perkins_resolves():
    """Production fixture sanity: Alec Perkins MUST resolve to
    'Alec Perkins' on preview DB."""

    async def _t():
        db = _get_db()
        uid = "c9d7ebc3-a292-4d7a-8765-0ce2739c6029"
        emp = await db.employees.find_one({"id": uid})
        if not emp:
            pytest.skip("Alec Perkins fixture not present in this DB")
        row = {
            "user_id": uid,
            "email": None,
            "employee_id": None,
            "display_name": None,
        }
        await _enrich_row_with_directory(db, row)
        assert row["display_name"] == "Alec Perkins", row["display_name"]

    _run(_t())


def test_resolve_display_name_sources_order():
    """Pure-function smoke: resolver walks full_name → display_name →
    name → first+last → email → employee_id → sentinel WITHIN each
    source, then advances to the next source."""
    assert _resolve_display_name({"full_name": "FN", "name": "N"}) == "FN"
    assert _resolve_display_name({"display_name": "DN", "name": "N"}) == "DN"
    assert _resolve_display_name({"name": "N", "first_name": "F"}) == "N"
    assert _resolve_display_name(
        {"first_name": "F", "last_name": "L", "email": "e@e"}
    ) == "F L"
    assert _resolve_display_name({"email": "e@e", "employee_id": "X"}) == "e@e"
    assert _resolve_display_name({"employee_id": "X"}) == "Employee #X"
    assert _resolve_display_name({}) == "Unknown person — Admin review required"
    # First populated source wins (left-to-right precedence):
    assert _resolve_display_name(
        {"name": "First"}, {"name": "Second"}
    ) == "First"
