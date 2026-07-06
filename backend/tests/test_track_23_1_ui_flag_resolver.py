"""TRACK 23.1 · V3 UI feature flag resolver lock envelope.

Locks:
- Admin override (force_v3) beats every other scope.
- Pilot user allow-list beats project override.
- Denied user beats tenant default.
- Tenant default falls back to env when the flag doc is missing.
- Missing/unavailable flag doc still returns a clean False by default.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from routes.ui_flags import COLL_UI_FLAGS, FLAG_KEY, resolve_dr_v3_flag


class _Coll:
    def __init__(self, rows=None):
        self.rows = rows or []

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items()):
                return dict(r)
        return None


class _DB:
    def __init__(self, flag_doc: Optional[Dict[str, Any]] = None):
        self._c = _Coll([{**(flag_doc or {}), "_id": FLAG_KEY}] if flag_doc else [])

    def __getitem__(self, name):
        assert name == COLL_UI_FLAGS
        return self._c


@pytest.mark.asyncio
async def test_admin_override_wins():
    db = _DB({"tenant_default": False, "denied_users": ["alice@masci.com"]})
    out = await resolve_dr_v3_flag(
        db, user_email="alice@masci.com", admin_override=True,
    )
    assert out["enabled"] is True
    assert out["source"] == "admin_override"


@pytest.mark.asyncio
async def test_pilot_user_beats_denied_and_default():
    db = _DB({
        "pilot_users": ["chris@masci.com"],
        "denied_users": ["chris@masci.com"],
        "tenant_default": False,
    })
    out = await resolve_dr_v3_flag(db, user_email="chris@masci.com")
    assert out["enabled"] is True
    assert out["source"] == "pilot_user"


@pytest.mark.asyncio
async def test_project_pilot_enables_v3():
    db = _DB({"pilot_projects": ["25-21"], "tenant_default": False})
    out = await resolve_dr_v3_flag(db, project_number="25-21")
    assert out["enabled"] is True
    assert out["source"] == "pilot_project"


@pytest.mark.asyncio
async def test_denied_user_blocks_when_no_higher_scope():
    db = _DB({"denied_users": ["skeptic@masci.com"], "tenant_default": True})
    out = await resolve_dr_v3_flag(db, user_email="skeptic@masci.com")
    assert out["enabled"] is False
    assert out["source"] == "denied_user"


@pytest.mark.asyncio
async def test_tenant_default_is_final_hop():
    db = _DB({"tenant_default": True})
    out = await resolve_dr_v3_flag(db, user_email="anyone@masci.com")
    assert out["enabled"] is True
    assert out["source"] == "tenant_default"


@pytest.mark.asyncio
async def test_missing_flag_doc_returns_false_by_default(monkeypatch):
    monkeypatch.delenv("DR_V3_TENANT_DEFAULT", raising=False)
    db = _DB(None)
    out = await resolve_dr_v3_flag(db, user_email="anyone@masci.com")
    assert out["enabled"] is False
    assert out["source"] == "tenant_default"


@pytest.mark.asyncio
async def test_env_default_promotes_when_no_flag_doc(monkeypatch):
    monkeypatch.setenv("DR_V3_TENANT_DEFAULT", "true")
    db = _DB(None)
    out = await resolve_dr_v3_flag(db, user_email="anyone@masci.com")
    assert out["enabled"] is True
    assert out["source"] == "tenant_default"


@pytest.mark.asyncio
async def test_case_insensitive_user_match():
    db = _DB({"pilot_users": ["Chris@masci.com"]})
    out = await resolve_dr_v3_flag(db, user_email="chris@MASCI.com")
    assert out["enabled"] is True
    assert out["source"] == "pilot_user"


@pytest.mark.asyncio
async def test_empty_context_falls_through_to_tenant_default():
    db = _DB({"tenant_default": False})
    out = await resolve_dr_v3_flag(db)
    assert out["enabled"] is False
