"""
tests/test_dispatch_command_center_phase_1.py

FORGEDOPS Dispatch Command Center V1 · Phase 1 contract tests.

Run with:
    cd /app/backend && python -m pytest tests/test_dispatch_command_center_phase_1.py -v

Doctrine coverage (per Phase 1 authorization):
  1. Auth required (401 without admin token)
  2. Any-portal reads work with admin token
  3. Admin/Dispatch required for broadcast SMS
  4. Empty-data safe rendering (counts default to zero)
  5. Motive missing-values handled (motive.connected == False)
  6. FleetWatcher returns not_connected
  7. MaintainX returns not_connected
  8. Asset Spine linkage uses canonical AssetSpine service
  9. Driver linkage shape
  10. Job linkage shape
  11. Shop feed linkage shape
  12. Broadcast SMS stubs cleanly when provider absent; unique broadcast_id
  13. No mutation on GET endpoints
"""
from __future__ import annotations

import asyncio
import os

import httpx

from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_BREAK_GLASS_PW = "MASCI1982!"


def _run(coro):
    return asyncio.run(coro)


async def _admin_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{BASE}/api/admin/login",
            json={"password": ADMIN_BREAK_GLASS_PW},
        )
        r.raise_for_status()
        data = r.json()
        tok = data.get("token") or data.get("admin_token")
        assert tok, f"no admin token in response: {data}"
        return tok


# ─── 1 · Auth required on every GET ────────────────────────────────
def test_summary_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/dispatch/command/summary")
            assert r.status_code == 401, r.text
    _run(go())


def test_fleet_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/dispatch/command/fleet")
            assert r.status_code == 401
    _run(go())


def test_drivers_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/dispatch/command/drivers")
            assert r.status_code == 401
    _run(go())


def test_jobs_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/dispatch/command/jobs")
            assert r.status_code == 401
    _run(go())


def test_haul_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/dispatch/command/haul")
            assert r.status_code == 401
    _run(go())


def test_shop_feed_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}/api/shop/command-feed")
            assert r.status_code == 401
    _run(go())


# ─── 2 · Admin reads return canonical envelopes ────────────────────
def test_summary_envelope_with_admin():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/summary",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["ok"] is True
            assert d["tenant_id"] == "masci"
            for key in ("fleet", "drivers", "jobs", "haul", "shop",
                        "safety", "asset_health", "communication",
                        "integration_readiness"):
                assert key in d, f"missing key: {key}"
            ir = d["integration_readiness"]
            assert ir["fleetwatcher"] == "not_connected"
            assert ir["maintainx"] == "not_connected"
            assert ir["sms_provider"] in ("active", "provider_not_configured")
    _run(go())


# ─── 3 · Broadcast requires dispatch/admin ─────────────────────────
def test_broadcast_requires_dispatch_or_admin():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{BASE}/api/dispatch/command/broadcast-sms",
                json={"audience": "all_active", "message": "x"},
            )
            assert r.status_code == 401, r.text
    _run(go())


# ─── 4 · Empty data safety ─────────────────────────────────────────
def test_drivers_empty_tenant_zero_counts():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/drivers",
                headers={"X-Admin-Token": tok,
                         "X-Tenant-Id": "no_such_tenant_zzz"},
            )
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["counts"]["shifted"] == 0
            assert d["counts"]["un_acked"] == 0
            assert d["rows"] == []
    _run(go())


# ─── 5-7 · Integration null-safety on every row ────────────────────
def test_fleet_rows_carry_integration_templates():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/fleet?limit=5",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            d = r.json()
            for row in d["rows"]:
                assert "motive" in row
                assert "fleetwatcher" in row
                assert "maintainx" in row
                assert row["fleetwatcher"]["status"] == "not_connected"
                assert row["maintainx"]["status"] == "not_connected"
                if not row["motive"]["mapped"]:
                    assert row["motive"]["last_event_at"] is None
    _run(go())


def test_haul_rows_carry_fleetwatcher_template():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/haul?limit=3",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            d = r.json()
            assert d["integration_readiness"]["fleetwatcher"] == "not_connected"
            for row in d["rows"]:
                assert row["fleetwatcher"]["status"] == "not_connected"
                assert row["fleetwatcher"]["tons"] is None
                assert row["fleetwatcher"]["ticket_number"] is None
    _run(go())


# ─── 8 · Asset Spine linkage ───────────────────────────────────────
def test_summary_asset_health_uses_canonical_spine():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/summary",
                headers={"X-Admin-Token": tok},
            )
            d = r.json()
            ah = d["asset_health"]
            assert ah.get("total_assets") is not None, \
                "asset_health did not bind to AssetSpine canonical service"
    _run(go())


# ─── 9 · Driver shape ──────────────────────────────────────────────
def test_drivers_envelope_shape():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/drivers",
                headers={"X-Admin-Token": tok},
            )
            d = r.json()
            for k in ("shifted", "un_acked", "in_breakdown",
                      "waiting", "off_shift_today"):
                assert k in d["counts"]
    _run(go())


# ─── 10 · Job shape ────────────────────────────────────────────────
def test_jobs_envelope_shape():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/dispatch/command/jobs",
                headers={"X-Admin-Token": tok},
            )
            d = r.json()
            assert "rows" in d and "counts" in d
            assert "projects_active" in d["counts"]
            for row in d["rows"]:
                for k in ("project_number", "trucks_today",
                          "drivers_today", "loads_today",
                          "materials_in_count", "materials_out_count",
                          "fleetwatcher"):
                    assert k in row, f"row missing {k}"
    _run(go())


# ─── 11 · Shop feed shape ──────────────────────────────────────────
def test_shop_feed_shape():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/shop/command-feed?limit=2",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200, r.text
            d = r.json()
            for k in ("needs_attention", "active_recovery",
                      "waiting_on_parts", "returned_today", "counts",
                      "integration_readiness"):
                assert k in d, f"missing key {k}"
            assert d["integration_readiness"]["maintainx"] == "not_connected"
    _run(go())


# ─── 12 · Broadcast stubs cleanly + unique id ──────────────────────
def test_broadcast_stubs_when_provider_missing():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r1 = await c.post(
                f"{BASE}/api/dispatch/command/broadcast-sms",
                headers={"X-Admin-Token": tok},
                json={"audience": "all_active",
                      "message": "phase1 test 1",
                      "kind": "general"},
            )
            assert r1.status_code == 200, r1.text
            d1 = r1.json()
            assert d1["ok"] is True
            if d1["provider_status"] == "provider_not_configured":
                assert d1["sent"] == 0
                assert d1["failed"] == 0
                for row in d1["results"]:
                    assert row["sms_result"]["status"] == "skipped"
            r2 = await c.post(
                f"{BASE}/api/dispatch/command/broadcast-sms",
                headers={"X-Admin-Token": tok},
                json={"audience": "all_active",
                      "message": "phase1 test 2",
                      "kind": "general"},
            )
            assert r2.status_code == 200
            d2 = r2.json()
            assert d1["broadcast_id"] != d2["broadcast_id"]
    _run(go())


# ─── 13 · GET endpoints are read-only / idempotent ─────────────────
def test_get_endpoints_are_idempotent():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r1 = await c.get(
                f"{BASE}/api/dispatch/command/fleet?limit=3",
                headers={"X-Admin-Token": tok},
            )
            r2 = await c.get(
                f"{BASE}/api/dispatch/command/fleet?limit=3",
                headers={"X-Admin-Token": tok},
            )
            assert r1.status_code == 200 and r2.status_code == 200
            d1, d2 = r1.json(), r2.json()
            assert d1["counts"]["total"] == d2["counts"]["total"]
            assert {r["unit_number"] for r in d1["rows"]} == \
                   {r["unit_number"] for r in d2["rows"]}
    _run(go())


# ─── Bad input on broadcast ────────────────────────────────────────
def test_broadcast_bad_audience_returns_400():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{BASE}/api/dispatch/command/broadcast-sms",
                headers={"X-Admin-Token": tok},
                json={"audience": "", "message": "x"},
            )
            assert r.status_code in (400, 422)
    _run(go())
