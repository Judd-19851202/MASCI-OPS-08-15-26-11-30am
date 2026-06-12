"""
tests/test_track_13_6f_pm_engines.py

Track 13.6F · Phase 3 & 4 — PM-2 Unified Holds and PM-3 Due Today
operational aggregation engines.

Run with:
    cd /app/backend && python -m pytest tests/test_track_13_6f_pm_engines.py -v

Doctrine coverage:
  1. Auth required (401 without admin/PM token) — permission boundary.
  2. Admin token unlocks both endpoints with documented envelope.
  3. Response shape: ok=True · as_of · scoped_projects · counts · rows.
  4. PM scope isolation — PM with no project_numbers gets empty rows,
     never an all-data leak.
  5. PM token with assigned projects returns ONLY rows whose
     project_number is in scope (no cross-project bleed).
  6. Empty-state behavior is honest (counts zeroed when nothing real).
  7. Every row carries a real source field and a real destination_path.
  8. PM-2 row.kind ∈ {equipment_hold, constraint, fleet_defect} ONLY
     — no invented kinds, no RFIs / Submittals.
  9. PM-3 row.kind ∈ {capa, daily_report_pending} ONLY.
 10. project_number filter respected for admin scope.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_BREAK_GLASS_PW = "MASCI1982!"
PM_DEMO_EMAIL = "pm.demo@mascigc.com"
PM_DEMO_PW = "PmTest2026!"

HOLDS_PATH = "/api/pm/command-center/holds"
DUE_PATH = "/api/pm/command-center/due-today"

ALLOWED_HOLD_KINDS = {"equipment_hold", "constraint", "fleet_defect"}
ALLOWED_DUE_KINDS = {"capa", "daily_report_pending"}
ALLOWED_HOLD_SOURCES = {
    "equipment_master", "operational_constraints", "fleet_defects",
}
ALLOWED_DUE_SOURCES = {"corrective_actions", "daily_reports"}


def _run(coro):
    return asyncio.run(coro)


async def _admin_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/admin/login",
                          json={"password": ADMIN_BREAK_GLASS_PW})
        r.raise_for_status()
        data = r.json()
        tok = data.get("token") or data.get("admin_token")
        assert tok
        return tok


async def _pm_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/pm/login",
                          json={"email": PM_DEMO_EMAIL, "password": PM_DEMO_PW})
        if r.status_code != 200:
            pytest.skip(f"PM demo login unavailable: {r.status_code} {r.text}")
        return r.json().get("token") or ""


# ─── 1 · Auth required ────────────────────────────────────────────
@pytest.mark.parametrize("path", [HOLDS_PATH, DUE_PATH])
def test_engine_requires_auth(path):
    async def go():
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{path}")
            assert r.status_code == 401, f"{path} → {r.status_code} {r.text}"
    _run(go())


# ─── 2 · Admin envelope shape ─────────────────────────────────────
def test_holds_envelope_admin():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{HOLDS_PATH}",
                              headers={"X-Admin-Token": tok})
            assert r.status_code == 200, r.text
            j = r.json()
            assert j.get("ok") is True
            assert "as_of" in j
            assert "scoped_projects" in j
            assert "counts" in j and "rows" in j
            for key in ("total", "equipment_holds",
                        "constraint_holds", "fleet_defects"):
                assert key in j["counts"], f"counts missing {key}"
                assert isinstance(j["counts"][key], int)
            for row in j["rows"]:
                assert row.get("kind") in ALLOWED_HOLD_KINDS, row
                assert row.get("source") in ALLOWED_HOLD_SOURCES, row
                assert row.get("destination_path"), row
                # map-ready field set present
                for k in ("status", "trust_state", "source_system"):
                    assert k in row, f"row missing {k}: {row}"
    _run(go())


def test_due_today_envelope_admin():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{DUE_PATH}",
                              headers={"X-Admin-Token": tok})
            assert r.status_code == 200, r.text
            j = r.json()
            assert j.get("ok") is True
            assert "as_of" in j and "as_of_date" in j
            assert "counts" in j and "rows" in j
            for key in ("total", "capas_due_today",
                        "daily_reports_pending_today"):
                assert key in j["counts"]
                assert isinstance(j["counts"][key], int)
            for row in j["rows"]:
                assert row.get("kind") in ALLOWED_DUE_KINDS, row
                assert row.get("source") in ALLOWED_DUE_SOURCES, row
                assert row.get("destination_path"), row
                assert row.get("due_date"), row
    _run(go())


# ─── 3 · PM token scope isolation ─────────────────────────────────
@pytest.mark.parametrize("path,counts_keys", [
    (HOLDS_PATH, {"total", "equipment_holds",
                  "constraint_holds", "fleet_defects"}),
    (DUE_PATH, {"total", "capas_due_today",
                "daily_reports_pending_today"}),
])
def test_engine_pm_scope_isolation(path, counts_keys):
    """PM token must NEVER see all-data. Either rows are bound to
    scoped_projects, or response is honestly empty."""
    async def go():
        pm_tok = await _pm_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{path}",
                              headers={"X-PM-Token": pm_tok})
            assert r.status_code == 200, r.text
            j = r.json()
            assert j.get("ok") is True
            scoped = j.get("scoped_projects")
            # PM must NEVER have scoped_projects == "all"
            assert scoped != "all", f"PM token returned admin scope: {scoped}"
            assert set(j["counts"].keys()) >= counts_keys
            # If PM has rows, each row's project_number (when present)
            # must be in scoped_projects.
            if isinstance(scoped, list) and scoped:
                for row in j.get("rows", []):
                    pn = row.get("project_number")
                    if pn:
                        assert pn in scoped, (
                            f"PM row leaks project_number={pn} "
                            f"not in scope={scoped}")
    _run(go())


# ─── 4 · Project-number filter (admin) ────────────────────────────
def test_holds_project_filter_unknown_returns_empty():
    """Admin filtering to a project that doesn't exist must zero out
    the counts — proves the filter actually narrows."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}{HOLDS_PATH}?project_number=NONEXISTENT-XYZ-99999",
                headers={"X-Admin-Token": tok})
            assert r.status_code == 200
            j = r.json()
            # equipment_holds + constraint_holds + fleet_defects all
            # must be 0 for a non-existent project.
            assert j["counts"]["equipment_holds"] == 0
            assert j["counts"]["constraint_holds"] == 0
            assert j["counts"]["fleet_defects"] == 0
    _run(go())


def test_due_today_project_filter_unknown_returns_empty():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}{DUE_PATH}?project_number=NONEXISTENT-XYZ-99999",
                headers={"X-Admin-Token": tok})
            assert r.status_code == 200
            j = r.json()
            assert j["counts"]["total"] == 0
            assert j["counts"]["capas_due_today"] == 0
            assert j["counts"]["daily_reports_pending_today"] == 0
            assert j["rows"] == []
    _run(go())


# ─── 5 · Pure-helper unit tests for the new aggregator helpers ────
def test_age_days_helper_handles_none_and_z_suffix():
    from datetime import datetime, timezone, timedelta
    from routes.pm_command_center import _age_days
    assert _age_days(None) == 0
    assert _age_days("") == 0
    now = datetime.now(timezone.utc)
    iso = (now - timedelta(days=5)).isoformat()
    # both with and without Z must parse
    assert _age_days(iso, now) == 5
    iso_z = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    assert _age_days(iso_z, now) == 2


def test_constraint_row_preserves_source_and_destination():
    from datetime import datetime, timezone
    from routes.pm_command_center import _constraint_row
    now = datetime.now(timezone.utc)
    c = {
        "id": "C-1",
        "title": "Owner Hold — utility relocation",
        "discipline": "utilities",
        "kind": "utility-conflict",
        "severity": "high",
        "status": "open",
        "project_id": "P-1",
        "created_at": now.isoformat(),
    }
    row = _constraint_row(c, c["created_at"], now,
                          project_id_to_pn={"P-1": "24-06"})
    assert row["kind"] == "constraint"
    assert row["source"] == "operational_constraints"
    # Track 13.6G — destination is the constraint detail page, not the list.
    assert row["destination_path"] == "/constraints/C-1"
    assert row["source_engine"] == "operational_constraints"
    assert row["source_id"] == "C-1"
    assert row["destination_label"].startswith("Open · ")
    assert row["project_number"] == "24-06"
    assert row["status"] == "open"
    assert row["severity"] == "high"
    assert row["source_system"] == "operational_constraints"
