"""
P0-A/P0-B read-first MaintainX integration tests.

Coverage (no live MaintainX calls — all responses are stubbed via
httpx MockTransport):

  1. Missing API key returns structured config error.
  2. Invalid API key surfaces a 401 → `unauthorized` code.
  3. Successful test_connection() with a valid stub returns ok=True.
  4. Asset list pagination stops once the upstream signals no_next.
  5. Asset list aborts cleanly at max_pages cap.
  6. 429 rate-limit response surfaces retry_after.
  7. Duplicate detection — unit_number collision flagged.
  8. Dry-run pipeline performs NO writes when save_report=False.
  9. WRITE methods on the client raise MaintainxWriteDisabled.
 10. MASCI equipment is not mutated by the dry-run.
 11. MaintainX is not called for any write during the dry-run.

Run:
   cd /app/backend && python -m pytest tests/test_maintainx_p0_read_first.py -v
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import httpx
import pytest

# Make sure backend/ is importable when running from anywhere
import sys
sys.path.insert(0, "/app/backend")

from services.maintainx_client import (  # noqa: E402
    MaintainxClient,
    MaintainxConfig,
    MaintainxConfigError,
    MaintainxClientError,
    MaintainxWriteDisabled,
)
from services import maintainx_asset_sync as asset_sync  # noqa: E402


# ──────────────────────────────────────────────────────────────────
# In-memory db stub — minimal Mongo-shaped surface for the pipeline
# ──────────────────────────────────────────────────────────────────
class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)
    def sort(self, *a, **kw):
        return self
    async def to_list(self, _n):
        return self._rows
    def __aiter__(self):
        async def _gen():
            for r in self._rows:
                yield r
        return _gen()


class _Coll:
    def __init__(self, rows=None):
        self._rows = list(rows or [])
        self.insert_calls = 0
        self.update_calls = 0
        self.delete_calls = 0
    def find(self, q=None, proj=None):
        return _Cursor(self._rows)
    async def find_one(self, q, proj=None):
        for r in self._rows:
            ok = all(r.get(k) == v for k, v in (q or {}).items() if not isinstance(v, dict))
            if ok:
                return r
        return None
    async def insert_one(self, doc):
        self.insert_calls += 1
        self._rows.append(doc)
        return type("R", (), {"inserted_id": "x"})()
    async def update_one(self, *a, **kw):
        self.update_calls += 1
        return type("R", (), {"matched_count": 1})()
    async def delete_one(self, *a, **kw):
        self.delete_calls += 1
        return type("R", (), {"deleted_count": 1})()


class _DB:
    def __init__(self, equipment, mappings=None):
        self.equipment_master = _Coll(equipment)
        self.asset_mappings = _Coll(mappings or [])
        self.maintainx_dryrun_reports = _Coll()


# ──────────────────────────────────────────────────────────────────
# httpx MockTransport helpers
# ──────────────────────────────────────────────────────────────────
def _make_client(handler) -> MaintainxClient:
    """Patch httpx.AsyncClient inside MaintainxClient so every test
    uses a deterministic transport."""
    transport = httpx.MockTransport(handler)

    class _PatchedClient(MaintainxClient):
        def __init__(self, cfg=None):
            super().__init__(cfg or MaintainxConfig(
                api_key="test_key_abcd1234",
                base_url="https://mx.test/v1",
                sync_enabled=False, write_enabled=False,
            ))
        async def _get(self, path, *, params=None, client=None):
            async with httpx.AsyncClient(timeout=self._timeout, transport=transport) as c:
                resp = await c.get(
                    path if path.startswith("http") else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}",
                    headers=self._headers(),
                    params=params or {},
                )
            return self._handle_response(resp)

    return _PatchedClient()


# ══════════════════════════════════════════════════════════════════
# 1. Missing API key
# ══════════════════════════════════════════════════════════════════
def test_missing_api_key_test_connection(monkeypatch):
    monkeypatch.delenv("MAINTAINX_API_KEY", raising=False)
    client = MaintainxClient(MaintainxConfig.from_env())
    result = asyncio.run(client.test_connection())
    assert result["ok"] is False
    assert result["status"] == "missing_api_key"


def test_missing_api_key_assert_raises(monkeypatch):
    monkeypatch.delenv("MAINTAINX_API_KEY", raising=False)
    client = MaintainxClient(MaintainxConfig.from_env())
    with pytest.raises(MaintainxConfigError):
        client._assert_configured()


# ══════════════════════════════════════════════════════════════════
# 2. Invalid API key → 401
# ══════════════════════════════════════════════════════════════════
def test_invalid_key_returns_401_classified():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})
    client = _make_client(handler)
    result = asyncio.run(client.test_connection())
    assert result["ok"] is False
    assert result["code"] == "unauthorized"
    # `status` is overwritten by the HTTP code via to_dict() spread
    assert result["status"] == 401


# ══════════════════════════════════════════════════════════════════
# 3. Successful connection
# ══════════════════════════════════════════════════════════════════
def test_successful_connection_mock():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"id": 1}]})
    client = _make_client(handler)
    result = asyncio.run(client.test_connection())
    assert result["ok"] is True
    assert result["status"] == "connected"


# ══════════════════════════════════════════════════════════════════
# 4. Asset pagination
# ══════════════════════════════════════════════════════════════════
def test_asset_list_pagination_mock():
    page_responses = {
        "1": [{"id": "a-1", "name": "Asset 1"}, {"id": "a-2", "name": "Asset 2"}],
        "2": [{"id": "a-3", "name": "Asset 3"}],
        "3": [],
    }
    def handler(req: httpx.Request) -> httpx.Response:
        page = req.url.params.get("page", "1")
        results = page_responses.get(page, [])
        has_more = page == "1"  # page 2 must drain via empty results
        return httpx.Response(200, json={"results": results, "hasMore": has_more})
    client = _make_client(handler)
    rows = asyncio.run(client.list_assets(page_size=2, max_pages=5))
    assert len(rows) == 3
    assert rows[0]["id"] == "a-1"


def test_asset_list_max_pages_cap():
    def handler(req: httpx.Request) -> httpx.Response:
        # Always returns a full page with hasMore=True (would loop forever)
        return httpx.Response(200, json={
            "results": [{"id": f"a-{req.url.params.get('page','1')}"}],
            "hasMore": True,
        })
    client = _make_client(handler)
    rows = asyncio.run(client.list_assets(page_size=1, max_pages=3))
    assert len(rows) == 3


# ══════════════════════════════════════════════════════════════════
# 5. Rate limit
# ══════════════════════════════════════════════════════════════════
def test_rate_limit_surfaces_retry_after():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "12"}, json={"error": "rate_limited"})
    client = _make_client(handler)
    with pytest.raises(MaintainxClientError) as ei:
        asyncio.run(client._get("/assets"))
    assert ei.value.code == "rate_limited"
    assert ei.value.retry_after == 12.0


# ══════════════════════════════════════════════════════════════════
# 6. Duplicate detection
# ══════════════════════════════════════════════════════════════════
def test_duplicate_unit_number_flagged():
    masci = [
        {"id": "m-1", "unit_number": "TRK-100", "make": "Mack", "model": "Granite"},
        {"id": "m-2", "unit_number": "TRK-100", "make": "Mack", "model": "Granite"},  # dup
    ]
    masci_norm = [asset_sync.normalize_masci_equipment(m) for m in masci]
    idx: Dict = {}
    for m in masci_norm:
        u = asset_sync._norm_unit(m["unit_number"])
        idx.setdefault(("unit", u), []).append(m)
    cls = asset_sync._match_asset(
        mx={"maintainx_asset_id": "mx-1", "unit_number": "trk-100"},
        masci=masci_norm,
        existing_by_external_id={},
        masci_index=idx,
    )
    assert cls["classification"] == "possible_duplicate"
    assert "m-1" in cls["candidate_masci_ids"]
    assert "m-2" in cls["candidate_masci_ids"]


def test_duplicate_risk_blocks_same_unit():
    masci = [{"id": "m-1", "unit_number": "TRK-50"}]
    masci_norm = [asset_sync.normalize_masci_equipment(m) for m in masci]
    idx: Dict = {("unit", "TRK50"): masci_norm}
    risk = asset_sync._duplicate_risk_for_new_asset(
        mx={"unit_number": "TRK-50"}, masci_index=idx,
    )
    assert risk["has_risk"] is True
    assert risk["verdict"] == "blocked_by_collision"


# ══════════════════════════════════════════════════════════════════
# 7. Dry-run produces no writes (save_report=False)
# ══════════════════════════════════════════════════════════════════
def test_dryrun_no_writes_when_save_false(monkeypatch):
    """save_report=False → nothing is inserted, nothing is updated."""
    db = _DB(
        equipment=[
            {"id": "m-1", "unit_number": "EX-1", "make": "Cat", "model": "320"},
        ],
        mappings=[],
    )
    # Stub the asset pull to return one known asset
    async def fake_iter(*a, **kw):
        for x in [{"id": "mx-1", "name": "Excavator 1", "unitNumber": "EX-1"}]:
            yield asset_sync.normalize_maintainx_asset(x).get("maintainx_asset_id") and x
    # Force normalised pipeline via direct injection: monkey-patch run_asset_dryrun's client
    async def fake_test_connection(self):
        return {"ok": True, "status": "connected", "config": self.config.public_view()}

    async def fake_iter_assets(self, *, page_size=100, max_pages=50):
        for x in [{"id": "mx-1", "name": "Excavator 1", "unitNumber": "EX-1"}]:
            yield x

    monkeypatch.setattr(MaintainxClient, "test_connection", fake_test_connection)
    monkeypatch.setattr(MaintainxClient, "iter_assets", fake_iter_assets)
    monkeypatch.setattr(MaintainxClient, "is_configured", lambda self: True)

    report = asyncio.run(asset_sync.run_asset_dryrun(db, save_report=False))

    # Counters reflect a match …
    assert report["totals"]["maintainx_assets_pulled"] == 1
    assert report["totals"]["masci_equipment_count"] == 1
    # … and NO writes to any collection were performed.
    assert db.equipment_master.insert_calls == 0
    assert db.equipment_master.update_calls == 0
    assert db.asset_mappings.insert_calls == 0
    assert db.asset_mappings.update_calls == 0
    assert db.maintainx_dryrun_reports.insert_calls == 0
    assert report["saved"] is False


def test_dryrun_only_writes_to_dryrun_reports_when_save_true(monkeypatch):
    db = _DB(equipment=[{"id": "m-1", "unit_number": "EX-1"}], mappings=[])

    async def fake_test_connection(self):
        return {"ok": True, "status": "connected", "config": self.config.public_view()}

    async def fake_iter_assets(self, *, page_size=100, max_pages=50):
        for x in [{"id": "mx-1", "name": "Excavator 1", "unitNumber": "EX-1"}]:
            yield x

    monkeypatch.setattr(MaintainxClient, "test_connection", fake_test_connection)
    monkeypatch.setattr(MaintainxClient, "iter_assets", fake_iter_assets)
    monkeypatch.setattr(MaintainxClient, "is_configured", lambda self: True)

    report = asyncio.run(asset_sync.run_asset_dryrun(db, save_report=True))

    # ONLY the dry-run report collection should have been touched.
    assert db.equipment_master.insert_calls == 0
    assert db.equipment_master.update_calls == 0
    assert db.asset_mappings.insert_calls == 0
    assert db.asset_mappings.update_calls == 0
    assert db.maintainx_dryrun_reports.insert_calls == 1
    assert report["saved"] is True


# ══════════════════════════════════════════════════════════════════
# 8. Write disabled prevents mutation on the client itself
# ══════════════════════════════════════════════════════════════════
def test_client_write_methods_raise(monkeypatch):
    monkeypatch.setenv("MAINTAINX_WRITE_ENABLED", "true")  # Even when "enabled"
    monkeypatch.setenv("MAINTAINX_API_KEY", "abc")
    client = MaintainxClient(MaintainxConfig.from_env())
    with pytest.raises(MaintainxWriteDisabled):
        asyncio.run(client.create_asset())
    with pytest.raises(MaintainxWriteDisabled):
        asyncio.run(client.update_asset())
    with pytest.raises(MaintainxWriteDisabled):
        asyncio.run(client.delete_asset())


# ══════════════════════════════════════════════════════════════════
# 9. Mask the API key
# ══════════════════════════════════════════════════════════════════
def test_api_key_masked_everywhere():
    cfg = MaintainxConfig(api_key="sk-mx-supersecret-token-1234",
                          base_url="https://x", sync_enabled=False, write_enabled=False)
    view = cfg.public_view()
    assert view["api_key_present"] is True
    assert "supersecret" not in str(view)
    assert view["api_key_masked"].endswith("1234")
    assert view["api_key_last4"] == "1234"
