"""TRACK 23.1 · Cost Code Provider abstraction lock envelope.

Locks:
- Provider abstraction contract (base class + `list_for_project` async).
- ``JobsMasterCostCodeProvider`` filters inactive codes, dedupes, and
  sorts.
- Empty / missing project ⇒ empty list (UI hides selector).
- Registry can accept new adapters without touching the DR UI.
- ``get_provider`` respects the ``COST_CODE_PROVIDER`` env var and
  returns a singleton.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest


from services.cost_codes.provider import (  # noqa: E402
    CostCodeProvider,
    JobsMasterCostCodeProvider,
    _reset_singleton_for_tests,
    get_provider,
    register_provider,
)


# ── In-memory jobs_master stub ─────────────────────────────────

class _FakeColl:
    def __init__(self, rows=None):
        self.rows = rows or []

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items()):
                return dict(r)
        return None


class _FakeDB:
    def __init__(self, jobs_master_rows=None):
        self.jobs_master = _FakeColl(jobs_master_rows)


# ── Contract ───────────────────────────────────────────────────

def test_provider_base_is_abstract():
    with pytest.raises(TypeError):
        CostCodeProvider()  # abstract; cannot instantiate


def test_jobs_master_provider_is_default():
    _reset_singleton_for_tests()
    db = _FakeDB([])
    provider = get_provider(db)
    assert isinstance(provider, JobsMasterCostCodeProvider)
    assert provider.name == "jobs_master"


def test_get_provider_returns_singleton():
    _reset_singleton_for_tests()
    db = _FakeDB([])
    a = get_provider(db)
    b = get_provider(db)
    assert a is b


# ── Behaviors ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_project_returns_empty():
    _reset_singleton_for_tests()
    db = _FakeDB([])
    provider = get_provider(db)
    assert await provider.list_for_project("") == []
    assert await provider.list_for_project("25-99") == []


@pytest.mark.asyncio
async def test_active_codes_returned_sorted():
    rows = [
        {
            "project_number": "25-21",
            "cost_codes": [
                {"code": "300-CURB", "description": "Curb", "active": True},
                {"code": "100-CLEAR", "description": "Clearing", "active": True},
                {"code": "200-EARTH", "description": "Earthwork", "active": True},
            ],
        }
    ]
    _reset_singleton_for_tests()
    db = _FakeDB(rows)
    provider = get_provider(db)
    out = await provider.list_for_project("25-21")
    assert [c["code"] for c in out] == ["100-CLEAR", "200-EARTH", "300-CURB"]


@pytest.mark.asyncio
async def test_inactive_codes_filtered_and_dedup():
    rows = [
        {
            "project_number": "25-21",
            "cost_codes": [
                {"code": "100-CLEAR", "description": "Clearing", "active": True},
                {"code": "100-CLEAR", "description": "dup", "active": True},
                {"code": "999-DEAD", "description": "Retired", "active": False},
                {"code": "", "description": "malformed", "active": True},
            ],
        }
    ]
    _reset_singleton_for_tests()
    db = _FakeDB(rows)
    provider = get_provider(db)
    out = await provider.list_for_project("25-21")
    assert [c["code"] for c in out] == ["100-CLEAR"]
    assert all(c["active"] is True for c in out)


@pytest.mark.asyncio
async def test_project_without_cost_codes_returns_empty():
    """UI must hide selector cleanly when the job has no codes at all."""
    rows = [{"project_number": "25-22", "project_name": "No codes here"}]
    _reset_singleton_for_tests()
    db = _FakeDB(rows)
    provider = get_provider(db)
    out = await provider.list_for_project("25-22")
    assert out == []


@pytest.mark.asyncio
async def test_get_uses_default_filter():
    rows = [
        {
            "project_number": "25-21",
            "cost_codes": [{"code": "100-CLEAR", "description": "Clearing", "active": True}],
        }
    ]
    _reset_singleton_for_tests()
    db = _FakeDB(rows)
    provider = get_provider(db)
    hit = await provider.get("25-21", "100-clear")  # case-insensitive
    assert hit and hit["code"] == "100-CLEAR"
    miss = await provider.get("25-21", "999-X")
    assert miss is None


# ── Registry ───────────────────────────────────────────────────

class _StubProvider(CostCodeProvider):
    name = "stub"
    def __init__(self, db):
        self._db = db
    async def list_for_project(self, project_number):
        return [{"code": "STUB-001", "description": "stub", "active": True}]


def test_register_provider_accepts_new_adapters(monkeypatch):
    register_provider("stub", _StubProvider)
    monkeypatch.setenv("COST_CODE_PROVIDER", "stub")
    _reset_singleton_for_tests()
    provider = get_provider(_FakeDB([]))
    assert isinstance(provider, _StubProvider)
    assert provider.name == "stub"


def test_unknown_provider_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("COST_CODE_PROVIDER", "vaporware_erp_9000")
    _reset_singleton_for_tests()
    provider = get_provider(_FakeDB([]))
    assert isinstance(provider, JobsMasterCostCodeProvider)


def test_register_provider_rejects_non_subclass():
    class NotAProvider:
        pass
    with pytest.raises(TypeError):
        register_provider("bad", NotAProvider)
