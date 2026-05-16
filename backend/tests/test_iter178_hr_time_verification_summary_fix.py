"""
test_iter178_hr_time_verification_summary_fix.py — Iter178 bug fix.

HR reported: Time Verification top summary cards showed
  Regular: 0.00
  Overtime: 0.00
while the table rows displayed correct Reg/OT values. Root cause: the
summary block summed `regular_hours` / `overtime_hours` off the per-day
rows, which are intentionally always 0 because the FLSA Reg/OT split
happens at the weekly rollup stage (per MASCI payroll policy).

This test exercises the endpoint end-to-end and asserts:

  1. summary.total_regular  == sum of weekly[*].regular_hours
  2. summary.total_overtime == sum of weekly[*].overtime_hours
  3. summary.total_lunch    == sum of weekly[*].lunch_hours (new field)
  4. summary.total_hours    == sum of weekly[*].total_hours
  5. INVARIANT: total_hours == total_regular + total_overtime
  6. When weekly rollup contains overtime, summary.total_overtime > 0
  7. CSV export contains a "WEEKLY ROLLUP" section + TOTALS footer

Uses a fresh DB and seeds three days of daily-report crew rows for one
employee totaling 50 hours so the FLSA split produces 40 regular +
10 overtime.
"""
from __future__ import annotations

import asyncio
import csv as _csv
import io as _io
import os
import sys
import uuid
from pathlib import Path

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")

BACKEND_URL = "http://localhost:8001"


async def _db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ.get("DB_NAME", "test_database")]


async def _hr_token() -> str:
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
        r = await c.post(
            "/api/hr/login",
            json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        )
        assert r.status_code == 200, f"hr login failed: {r.status_code} {r.text}"
        return r.json()["token"]


# Inject 3 daily-report rows so the test employee tots 50 hrs in one week
async def _seed_daily_reports(week_ending: str, marker: str):
    """Seed daily reports for the Mon-Sat days in the same week as
    `week_ending`. Returns the inserted ids for cleanup."""
    from datetime import date, datetime, timedelta, timezone

    db = await _db()
    end = date.fromisoformat(week_ending)
    days = [end - timedelta(days=n) for n in (5, 4, 3)]  # 3 work days in this week
    # 18 + 18 + 14 = 50 hrs → 40 reg + 10 OT after FLSA split
    hour_specs = [18.0, 18.0, 14.0]
    inserted = []
    for d, hrs in zip(days, hour_specs):
        doc = {
            "id": f"itest-dr-{uuid.uuid4().hex[:8]}",
            "report_date": d.isoformat(),
            "project_number": "ITEST-001",
            "project_name": "Iter178 Test Project",
            "prepared_by": f"ITEST Foreman {marker}",
            "masci_crews": [
                {
                    "name": f"ITEST Mechanic {marker}",
                    "trade": "Operator",
                    "start_time": "06:00",
                    "stop_time": "23:00",
                    "lunch_minutes": 30,
                    "hours": hrs,
                }
            ],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.daily_reports.insert_one(doc)
        inserted.append(doc["id"])
    return inserted


async def _cleanup(ids):
    db = await _db()
    if ids:
        await db.daily_reports.delete_many({"id": {"$in": ids}})


def _run(coro):
    return asyncio.run(coro)


def test_summary_uses_weekly_rollup_not_per_day_rows():
    """Bug repro + fix verification."""

    async def body():
        from datetime import date, timedelta

        marker = uuid.uuid4().hex[:6]
        # Pick a date far enough in past to avoid colliding with real prod data
        we = (date.today() - timedelta(days=42)).isoformat()
        ids = await _seed_daily_reports(we, marker)
        try:
            tok = await _hr_token()
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=15) as c:
                # Scope the query to the marker employee so we read only our seed
                r = await c.get(
                    "/api/hr/time-verification",
                    params={"week_ending": we, "employee": marker},
                    headers={"X-HR-Token": tok},
                )
                assert r.status_code == 200, r.text
                j = r.json()
                s = j["summary"]
                weekly = j["weekly"]
                # Sanity: one employee in scope
                assert s["total_employees"] == 1, j
                assert len(weekly) == 1
                wk = weekly[0]
                # FLSA split must apply: 50 hrs → 40 reg + 10 OT
                assert wk["total_hours"] == 50.0, wk
                assert wk["regular_hours"] == 40.0, wk
                assert wk["overtime_hours"] == 10.0, wk
                # The fix: summary must equal the weekly rollup
                assert s["total_regular"] == 40.0, s
                assert s["total_overtime"] == 10.0, s
                assert s["total_hours"] == 50.0, s
                assert s["total_overtime"] > 0, "OT summary still zero — fix did not land"
                # Invariant must hold
                assert round(s["total_regular"] + s["total_overtime"], 2) == s["total_hours"], s
                # Lunch hours field exists (additive new card)
                assert "total_lunch" in s
                assert s["total_lunch"] == wk["lunch_hours"]
        finally:
            await _cleanup(ids)

    _run(body())


def test_summary_zero_when_no_data():
    """Empty window must not crash + must keep new total_lunch key."""

    async def body():
        from datetime import date, timedelta

        we = (date.today() - timedelta(days=900)).isoformat()  # ancient, no data
        tok = await _hr_token()
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
            r = await c.get(
                "/api/hr/time-verification",
                params={"week_ending": we, "employee": "no-such-name-zzz"},
                headers={"X-HR-Token": tok},
            )
        assert r.status_code == 200, r.text
        s = r.json()["summary"]
        assert s["total_employees"] == 0
        assert s["total_hours"] == 0
        assert s["total_regular"] == 0
        assert s["total_overtime"] == 0
        assert s["total_lunch"] == 0

    _run(body())


def test_filter_narrows_summary():
    """Summary must respect filters (the user explicitly required this)."""

    async def body():
        from datetime import date, timedelta

        marker = uuid.uuid4().hex[:6]
        we = (date.today() - timedelta(days=42)).isoformat()
        ids = await _seed_daily_reports(we, marker)
        try:
            tok = await _hr_token()
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                # Match the seed
                r_match = await c.get(
                    "/api/hr/time-verification",
                    params={"week_ending": we, "employee": marker},
                    headers={"X-HR-Token": tok},
                )
                # Exclude the seed
                r_exclude = await c.get(
                    "/api/hr/time-verification",
                    params={
                        "week_ending": we,
                        "employee": f"definitely-not-{marker}",
                    },
                    headers={"X-HR-Token": tok},
                )
            sm = r_match.json()["summary"]
            sx = r_exclude.json()["summary"]
            assert sm["total_overtime"] == 10.0
            assert sx["total_overtime"] == 0.0
            assert sm["total_employees"] >= 1
            assert sx["total_employees"] == 0
        finally:
            await _cleanup(ids)

    _run(body())


def test_csv_export_contains_weekly_rollup_and_totals_footer():
    """CSV had the same zeros-in-Reg/OT bug — assert the new sections."""

    async def body():
        from datetime import date, timedelta

        marker = uuid.uuid4().hex[:6]
        we = (date.today() - timedelta(days=42)).isoformat()
        ids = await _seed_daily_reports(we, marker)
        try:
            tok = await _hr_token()
            async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=10) as c:
                r = await c.get(
                    "/api/hr/time-verification.csv",
                    params={"week_ending": we, "employee": marker},
                    headers={"X-HR-Token": tok},
                )
            assert r.status_code == 200
            text = r.content.decode("utf-8")
            # Parse all rows to inspect structure
            rows = list(_csv.reader(_io.StringIO(text)))
            # First row is the per-day header
            assert rows[0][0] == "Date"
            # Must contain the new weekly rollup section
            joined = "\n".join(",".join(r) for r in rows)
            assert "WEEKLY ROLLUP" in joined, "CSV missing WEEKLY ROLLUP section"
            assert "TOTALS" in joined, "CSV missing TOTALS footer"
            # The TOTALS row must show 40 / 10 / total 50 for our seed
            totals_row = next(r for r in rows if r and r[0] == "TOTALS")
            # Layout: ["TOTALS", "", "", reg, ot, lunch, total]
            assert float(totals_row[3]) == 40.0, totals_row
            assert float(totals_row[4]) == 10.0, totals_row
            assert float(totals_row[6]) == 50.0, totals_row
        finally:
            await _cleanup(ids)

    _run(body())
