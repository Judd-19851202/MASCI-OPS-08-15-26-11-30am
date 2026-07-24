from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path("/app/backend")
sys.path.insert(0, str(ROOT))

from pm_auth import compute_pm_scope  # noqa: E402


class _AsyncCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._index = 0

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._index]
        self._index += 1
        return row


class _Collection:
    def __init__(self, rows):
        self.rows = list(rows)

    async def find_one(self, query, projection=None):  # noqa: ARG002
        query = query or {}
        for row in self.rows:
            matched = True
            for key, value in query.items():
                if row.get(key) != value:
                    matched = False
                    break
            if matched:
                return row
        return None

    def find(self, query, projection=None):  # noqa: ARG002
        query = query or {}
        out = []
        for row in self.rows:
            if query.get("deleted_at") == {"$in": [None, ""]} and row.get("deleted_at") not in (None, ""):
                continue
            ors = query.get("$or") or []
            if ors:
                matched = False
                for clause in ors:
                    if all(row.get(k) == v for k, v in clause.items()):
                        matched = True
                        break
                if not matched:
                    continue
            if query.get("active") is True and row.get("active") is not True:
                continue
            out.append(row)
        return _AsyncCursor(out)


class _DB:
    def __init__(self):
        self.project_managers = _Collection(
            [
                {
                    "id": "pm-1",
                    "email": "pm@example.com",
                    "password_hash": "pm-hash",
                    "linked_to_directory": False,
                },
                {
                    "id": "admin-pm-1",
                    "email": "super@example.com",
                    "password_hash": "admin-pm-hash",
                    "linked_to_directory": True,
                    "source": "directory-shadow",
                },
                {
                    "id": "pm-shadow-1",
                    "email": "pm.shadow@example.com",
                    "password_hash": "pm-shadow-hash",
                    "linked_to_directory": True,
                    "source": "directory-shadow",
                },
            ]
        )
        self.user_directory = _Collection(
            [
                {
                    "id": "admin-pm-1",
                    "email": "super@example.com",
                    "portals": ["admin", "pm"],
                    "is_super_admin": True,
                },
                {
                    "id": "pm-shadow-1",
                    "email": "pm.shadow@example.com",
                    "portals": ["pm"],
                    "is_super_admin": False,
                },
            ]
        )
        self.jobs_master = _Collection(
            [
                {"project_number": "26-05", "pm_email": "pm@example.com", "deleted_at": ""},
                {"project_number": "26-06", "co_pm_emails": "pm@example.com", "deleted_at": None},
                {"project_number": "OLD-01", "pm_email": "pm@example.com", "deleted_at": "2026-01-01"},
                {"project_number": "99-01", "pm_email": "pm.shadow@example.com", "deleted_at": None},
            ]
        )
        self.project_team_assignments = _Collection(
            [
                {"project_number": "26-07", "email": "pm@example.com", "active": True},
                {"project_number": "26-08", "user_id": "pm-1", "active": True},
                {"project_number": "26-09", "email": "pm@example.com", "active": False},
                {"project_number": "99-02", "user_id": "pm-shadow-1", "active": True},
            ]
        )


def _run(coro):
    return asyncio.run(coro)


def test_directory_admin_actor_gets_unrestricted_scope():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {
                "_actor": "admin",
                "email": "jaymn.judd@mascigc.com",
                "name": "Super Admin",
                "portals": ["admin", "pm", "shop"],
                "is_super_admin": True,
            },
        )
    )
    assert scope.is_admin is True
    assert scope.project_numbers is None
    assert scope.filter({"status": "open"}) == {"status": "open"}


def test_legacy_true_admin_stays_unrestricted():
    scope = _run(compute_pm_scope(_DB(), True))
    assert scope.is_admin is True
    assert scope.project_numbers is None


def test_pm_actor_collects_jobs_and_team_assignments():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {"_actor": "pm", "id": "pm-1", "email": "pm@example.com"},
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == {"26-05", "26-06", "26-07", "26-08"}
    assert set(scope.filter({})["project_number"]["$in"]) == {"26-05", "26-06", "26-07", "26-08"}


def test_raw_pm_actor_shape_collects_assigned_projects():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {
                "id": "pm-1",
                "email": "pm@example.com",
                "password_hash": "pm-hash",
                "linked_to_directory": False,
            },
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == {"26-05", "26-06", "26-07", "26-08"}


def test_raw_pm_actor_does_not_gain_unrestricted_scope():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {
                "id": "pm-shadow-1",
                "email": "pm.shadow@example.com",
                "password_hash": "pm-shadow-hash",
                "linked_to_directory": True,
                "source": "directory-shadow",
            },
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == {"99-01", "99-02"}


def test_super_admin_retains_unrestricted_scope_in_pm_token_context():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {
                "id": "admin-pm-1",
                "email": "super@example.com",
                "password_hash": "admin-pm-hash",
                "linked_to_directory": True,
                "source": "directory-shadow",
            },
        )
    )
    assert scope.is_admin is True
    assert scope.project_numbers is None


def test_password_hash_mismatch_does_not_recover_super_admin_or_broaden_scope():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {
                "id": "admin-pm-1",
                "email": "super@example.com",
                "password_hash": "WRONG-HASH",
                "linked_to_directory": True,
                "source": "directory-shadow",
            },
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == set()
    assert scope.filter({"status": "open"}) == {"status": "open", "__pm_empty_scope__": True}
    assert scope.allows("99-01") is False


def test_directory_id_email_mismatch_does_not_elevate_or_grant_cross_project_access():
    db = _DB()
    db.project_managers.rows.append(
        {
            "id": "collision-pm-1",
            "email": "collision.pm@example.com",
            "password_hash": "collision-hash",
            "linked_to_directory": True,
            "source": "directory-shadow",
        }
    )
    db.user_directory.rows.append(
        {
            "id": "collision-pm-1",
            "email": "different-admin@example.com",
            "portals": ["admin", "pm"],
            "is_super_admin": True,
        }
    )
    db.jobs_master.rows.append(
        {
            "project_number": "77-01",
            "pm_email": "collision.pm@example.com",
            "deleted_at": None,
        }
    )
    db.project_team_assignments.rows.append(
        {
            "project_number": "77-02",
            "user_id": "collision-pm-1",
            "active": True,
        }
    )

    scope = _run(
        compute_pm_scope(
            db,
            {
                "id": "collision-pm-1",
                "email": "collision.pm@example.com",
                "password_hash": "collision-hash",
                "linked_to_directory": True,
                "source": "directory-shadow",
            },
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == {"77-01", "77-02"}
    assert set(scope.filter({})["project_number"]["$in"]) == {"77-01", "77-02"}
    assert scope.allows("77-01") is True
    assert scope.allows("26-05") is False


def test_co_pm_actor_collects_assigned_projects():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {"_actor": "pm", "role": "co_pm", "id": "pm-1", "email": "pm@example.com"},
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == {"26-05", "26-06", "26-07", "26-08"}


def test_unassigned_pm_gets_empty_scope():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {"_actor": "pm", "id": "pm-404", "email": "noprojects@example.com"},
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == set()
    assert scope.filter({}) == {"__pm_empty_scope__": True}


def test_non_admin_without_email_fails_closed():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {"_actor": "leadership", "name": "Field Leadership"},
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == set()
    assert scope.filter({}) == {"__pm_empty_scope__": True}


def test_email_only_actor_does_not_gain_pm_or_admin_scope():
    scope = _run(
        compute_pm_scope(
            _DB(),
            {"email": "pm@example.com", "name": "Ambiguous Actor"},
        )
    )
    assert scope.is_admin is False
    assert scope.project_numbers == set()
    assert scope.filter({}) == {"__pm_empty_scope__": True}