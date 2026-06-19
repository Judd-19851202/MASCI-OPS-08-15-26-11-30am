"""
tests/test_track_13_6h_sla_chip.py

Track 13.6H · Phase 1 — SLA / Age chip (operational truth only).

Verifies:
  • _sla_label_hold derives "Held N Days" / "Held Today" / "Held 1 Day"
    purely from opened_at (no risk score, no AI rank).
  • _sla_label_due derives "Due Today" / "Due Tomorrow" /
    "Due In N Days" / "Overdue N Days" purely from due_date.
  • Every PM-2 row carries sla_label; every PM-3 row carries sla_label.
  • Empty inputs → honest empty string (no fabricated label).

Run:
    cd /app/backend && python -m pytest tests/test_track_13_6h_sla_chip.py -v
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_PW = "Maddix123!"
HOLDS = "/api/pm/command-center/holds"
DUE = "/api/pm/command-center/due-today"


def _run(coro): return asyncio.run(coro)


async def _admin_token():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/admin/login", json={"password": ADMIN_PW})
        r.raise_for_status()
        return r.json()["token"]


# ─── 1 · _sla_label_hold pure-helper unit tests ─────────────────────
def test_sla_label_hold_empty_input():
    from routes.pm_command_center import _sla_label_hold
    assert _sla_label_hold(None) == ""
    assert _sla_label_hold("") == ""


def test_sla_label_hold_today_one_day_n_days():
    from routes.pm_command_center import _sla_label_hold
    now = datetime.now(timezone.utc)
    assert _sla_label_hold(now.isoformat(), now) == "Held Today"
    assert _sla_label_hold((now - timedelta(days=1)).isoformat(), now) == "Held 1 Day"
    assert _sla_label_hold((now - timedelta(days=5)).isoformat(), now) == "Held 5 Days"
    assert _sla_label_hold((now - timedelta(days=42)).isoformat(), now) == "Held 42 Days"


def test_sla_label_hold_handles_z_suffix():
    from routes.pm_command_center import _sla_label_hold
    now = datetime.now(timezone.utc)
    iso_z = (now - timedelta(days=3)).isoformat().replace("+00:00", "Z")
    assert _sla_label_hold(iso_z, now) == "Held 3 Days"


# ─── 2 · _sla_label_due pure-helper unit tests ──────────────────────
def test_sla_label_due_empty_input():
    from routes.pm_command_center import _sla_label_due
    assert _sla_label_due(None) == ""
    assert _sla_label_due("") == ""
    assert _sla_label_due("not-a-date") == ""


def test_sla_label_due_today_tomorrow_future_overdue():
    from routes.pm_command_center import _sla_label_due
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    tomorrow = (now + timedelta(days=1)).date().isoformat()
    in_4 = (now + timedelta(days=4)).date().isoformat()
    overdue_1 = (now - timedelta(days=1)).date().isoformat()
    overdue_2 = (now - timedelta(days=2)).date().isoformat()
    assert _sla_label_due(today, now) == "Due Today"
    assert _sla_label_due(tomorrow, now) == "Due Tomorrow"
    assert _sla_label_due(in_4, now) == "Due In 4 Days"
    assert _sla_label_due(overdue_1, now) == "Overdue 1 Day"
    assert _sla_label_due(overdue_2, now) == "Overdue 2 Days"


# ─── 3 · No forbidden vocabulary anywhere in helpers ────────────────
def test_sla_label_vocabulary_is_operational_truth_only():
    """Doctrine: no risk scores · no AI priority · no red/yellow/green."""
    from routes.pm_command_center import _sla_label_hold, _sla_label_due
    now = datetime.now(timezone.utc)
    samples = [
        _sla_label_hold(now.isoformat(), now),
        _sla_label_hold((now - timedelta(days=12)).isoformat(), now),
        _sla_label_due(now.date().isoformat(), now),
        _sla_label_due((now - timedelta(days=5)).date().isoformat(), now),
    ]
    forbidden = ("score", "risk", "ai", "priority", "red", "yellow", "green",
                 "high-risk", "critical-priority")
    for s in samples:
        low = s.lower()
        for word in forbidden:
            assert word not in low, f"forbidden vocab {word!r} in sla_label {s!r}"


# ─── 4 · Every PM-2 row carries sla_label ───────────────────────────
def test_holds_rows_carry_sla_label():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{HOLDS}",
                            headers={"X-Admin-Token": tok})
            j = r.json()
            assert j["counts"]["total"] > 0, "no holds in preview to verify"
            seen_held = False
            for row in j["rows"]:
                # sla_label key must exist on every row (string, possibly empty).
                assert "sla_label" in row, f"row missing sla_label: {row}"
                if row["sla_label"]:
                    assert row["sla_label"].startswith("Held "), (
                        f"hold row sla_label must start with 'Held ': {row['sla_label']!r}")
                    seen_held = True
            assert seen_held, "no hold sla_label produced from real timestamps"
    _run(go())


# ─── 5 · Every PM-3 row carries sla_label ──────────────────────────
def test_due_today_rows_carry_sla_label_due_today():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{DUE}",
                            headers={"X-Admin-Token": tok})
            j = r.json()
            for row in j["rows"]:
                assert "sla_label" in row
                # Engine only returns today-dated items → label is "Due Today".
                if row["sla_label"]:
                    assert row["sla_label"] == "Due Today", (
                        f"PM-3 row sla_label expected 'Due Today': {row['sla_label']!r}")
    _run(go())
