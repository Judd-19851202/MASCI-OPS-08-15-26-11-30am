"""
tests/test_track_13_6g_deep_link_triage.py

Track 13.6G — Deep-Link Operational Triage.

Validates that every aggregated row from PM-2 (Unified Holds) and PM-3
(Due Today) carries the canonical drill quartet:
  - source_engine
  - source_id
  - destination_path
  - destination_label
…and that every destination_path:
  • starts with a real, known PM-facing path,
  • encodes a target id in the URL (deep-link, not list-page reconstruction),
  • respects PM scope (no privilege escalation, no project bleed).

Run:
    cd /app/backend && python -m pytest tests/test_track_13_6g_deep_link_triage.py -v
"""
from __future__ import annotations

import asyncio
import os
import sys
from urllib.parse import urlparse, parse_qs

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_PW = "MASCI1982!"
PM_EMAIL = "pm.demo@mascigc.com"
PM_PW = "PmTest2026!"

HOLDS = "/api/pm/command-center/holds"
DUE = "/api/pm/command-center/due-today"

CANONICAL_DRILL_FIELDS = (
    "source_engine", "source_id", "destination_path", "destination_label",
)

# Real, currently-mounted PM-facing destination roots (App.js verified).
ALLOWED_DEST_ROOTS = (
    "/pm/fleet", "/pm/daily", "/pm/incidents", "/constraints",
)


def _run(coro): return asyncio.run(coro)


async def _admin_token():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/admin/login", json={"password": ADMIN_PW})
        r.raise_for_status()
        return r.json()["token"]


async def _pm_token():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/pm/login",
                         json={"email": PM_EMAIL, "password": PM_PW})
        if r.status_code != 200:
            pytest.skip(f"PM demo login unavailable: {r.status_code}")
        return r.json().get("token") or ""


def _assert_drill_fields_present(row):
    for f in CANONICAL_DRILL_FIELDS:
        assert f in row, f"row missing canonical drill field {f}: {row}"
        assert row[f] not in (None, ""), f"row.{f} empty: {row}"


def _assert_destination_path_real(path: str):
    assert path.startswith("/"), f"destination_path must be absolute: {path}"
    assert any(path.startswith(root) for root in ALLOWED_DEST_ROOTS), (
        f"destination_path {path!r} does not start with a real "
        f"PM-facing route root {ALLOWED_DEST_ROOTS}")


def _assert_destination_encodes_source_id(path: str, source_id: str, kind: str):
    """Every deep link must carry the source_id either in the URL path
    segment (true detail route, e.g. /constraints/<id>) or in a focus
    query param. Backend owns routing truth — browser must not
    reconstruct paths."""
    parsed = urlparse(path)
    qs = parse_qs(parsed.query)
    if kind == "constraint":
        # /constraints/<id>
        assert parsed.path.rstrip("/").endswith(source_id), (
            f"constraint deep-link must end with id: {path}")
    elif kind == "daily_report_pending":
        # /pm/daily/<id>
        assert parsed.path.rstrip("/").endswith(source_id), (
            f"daily_report_pending deep-link must end with id: {path}")
    elif kind == "equipment_hold":
        # /pm/fleet?focus_asset_id=<id>&focus_unit=…
        assert qs.get("focus_asset_id", [""])[0] == source_id, (
            f"equipment_hold deep-link missing focus_asset_id={source_id}: {path}")
    elif kind == "fleet_defect":
        assert qs.get("focus_defect_id", [""])[0] == source_id, (
            f"fleet_defect deep-link missing focus_defect_id={source_id}: {path}")
    elif kind == "capa":
        assert qs.get("focus_capa", [""])[0] == source_id, (
            f"capa deep-link missing focus_capa={source_id}: {path}")
    else:
        pytest.fail(f"Unknown kind {kind!r} — drill encoding undefined.")


# ─── 1 · Holds rows: canonical drill quartet + real destination roots ──
def test_holds_rows_carry_canonical_drill_quartet():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{HOLDS}",
                            headers={"X-Admin-Token": tok})
            assert r.status_code == 200, r.text
            j = r.json()
            assert j["counts"]["total"] > 0, (
                "preview DB has zero holds — cannot validate drill quartet")
            for row in j["rows"]:
                _assert_drill_fields_present(row)
                _assert_destination_path_real(row["destination_path"])
                _assert_destination_encodes_source_id(
                    row["destination_path"], row["source_id"], row["kind"])
                # source_engine matches row.source — single source of truth.
                assert row["source_engine"] == row["source"]
    _run(go())


# ─── 2 · Due Today rows: canonical drill quartet + real destination roots ──
def test_due_today_rows_carry_canonical_drill_quartet():
    """Run the same shape check on Due Today. Even when counts are 0,
    the empty array structurally satisfies the contract — this test is
    a smoke check that the endpoint stays correct when populated."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{DUE}",
                            headers={"X-Admin-Token": tok})
            assert r.status_code == 200
            j = r.json()
            for row in j["rows"]:
                _assert_drill_fields_present(row)
                _assert_destination_path_real(row["destination_path"])
                _assert_destination_encodes_source_id(
                    row["destination_path"], row["source_id"], row["kind"])
                assert row["source_engine"] == row["source"]
    _run(go())


# ─── 3 · destination_label is human-readable (≥3 chars, ≤80 chars) ──
def test_destination_labels_human_readable():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            for path in (HOLDS, DUE):
                r = await c.get(f"{BASE}{path}",
                                headers={"X-Admin-Token": tok})
                j = r.json()
                for row in j["rows"]:
                    label = row["destination_label"]
                    assert isinstance(label, str)
                    assert 3 <= len(label) <= 80, (
                        f"destination_label out of range: {label!r}")
    _run(go())


# ─── 4 · PM scope isolation on drill destinations ──
def test_pm_scope_destination_isolation():
    """PM token must never emit a row whose project_number leaks
    outside the PM's scoped_projects list."""
    async def go():
        pm_tok = await _pm_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{HOLDS}",
                            headers={"X-PM-Token": pm_tok})
            j = r.json()
            assert j["scoped_projects"] != "all"
            scoped = j["scoped_projects"]
            if isinstance(scoped, list):
                for row in j["rows"]:
                    pn = row.get("project_number")
                    if pn:
                        assert pn in scoped, (
                            f"PM holds drill row leaks pn={pn} "
                            f"not in scope={scoped}")
            # Same for Due Today.
            r2 = await c.get(f"{BASE}{DUE}",
                             headers={"X-PM-Token": pm_tok})
            j2 = r2.json()
            assert j2["scoped_projects"] != "all"
    _run(go())


# ─── 5 · destination_path is URL-safe (no raw spaces / control chars) ──
def test_destination_paths_url_safe():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{HOLDS}",
                            headers={"X-Admin-Token": tok})
            j = r.json()
            for row in j["rows"]:
                path = row["destination_path"]
                assert " " not in path, (
                    f"destination_path contains unencoded space: {path}")
                # url-parse must not blow up
                parsed = urlparse(path)
                assert parsed.path.startswith("/")
    _run(go())


# ─── 6 · _urlq pure-helper unit test ──
def test_urlq_pure_helper_encodes_special_chars():
    from routes.pm_command_center import _urlq
    assert _urlq(None) == ""
    assert _urlq("") == ""
    assert _urlq("abc") == "abc"
    assert _urlq("a/b c") == "a%2Fb%20c"
    assert _urlq("CAPA #42") == "CAPA%20%2342"
