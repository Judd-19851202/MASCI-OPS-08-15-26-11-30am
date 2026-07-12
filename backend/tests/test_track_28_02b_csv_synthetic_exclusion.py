"""TRACK 28.02B · Regression lock — synthetic Daily Reports must be
excluded from the /api/daily-reports.csv admin export.

Root cause of the P1 leak (discovered during Track 28.02B E2E cert):
the JSON list at ``GET /api/daily-reports`` correctly ran through
``apply_synthetic_dr_exclusion`` (TRACK 24.9 doctrine), but the sibling
CSV export at ``GET /api/daily-reports.csv`` was ONLY applying the PM
scope filter — so every synthetic/certification/smoke row that the
operational list correctly hides was silently included in the CSV
download.

Blast radius before fix:
  • Any admin exporting Daily Reports to CSV received a polluted file.
  • Downstream analytics/audits ingesting the CSV saw synthetic rows.
  • Doctrine violation of TRACK 24.9 ("synthetic rows must never appear
    on user-facing operational screens" — CSV export is user-facing).

Fix: `routes/daily_reports.py::list_daily_reports_csv` now applies
``apply_synthetic_dr_exclusion(scope.filter({}))`` before the
aggregation pipeline, matching the JSON list contract exactly.

This test locks the invariant: for a fresh TEST_28_02_ prefixed
Daily Report, the CSV response must NOT contain its project_name.
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import date
import httpx
import pytest
from pymongo import MongoClient


def _backend() -> str:
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:  # noqa: BLE001
        pass
    with open("/app/frontend/.env", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("no backend url")


def _mongo():
    url = os.environ.get("MONGO_URL")
    dbn = os.environ.get("DB_NAME") or "masci_safety_preview"
    if not url:
        with open("/app/backend/.env", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MONGO_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("DB_NAME="):
                    dbn = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(url)[dbn]


BACKEND = _backend()


@pytest.fixture(scope="module")
def admin_headers() -> dict:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()["portal_tokens"]["admin"]
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def test_csv_export_excludes_synthetic_daily_report(admin_headers: dict) -> None:
    """The CSV export must inherit the same synthetic-DR exclusion as
    the JSON list, per TRACK 24.9 doctrine."""
    pname = f"TEST_28_02_csv_filter_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    payload = {
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert",
        "report_date": date.today().isoformat(),
        "prepared_by": "TEST_28_02_Foreman",
        "ai_accepted_summary": "Approved summary: synthetic CSV exclusion certification record.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "TEST_28_02_Foreman",
            "accepted_at": f"{date.today().isoformat()}T19:00:00Z",
        },
    }
    # POST
    r = httpx.post(f"{BACKEND}/api/daily-reports", headers=admin_headers, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    dr_id = r.json()["id"]

    try:
        # JSON list must hide it (baseline confidence in TRACK 24.9).
        r = httpx.get(f"{BACKEND}/api/daily-reports", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert dr_id not in [x.get("id") for x in r.json()], (
            "TRACK 24.9 JSON exclusion broke — synthetic DR leaked to /api/daily-reports"
        )

        # CSV export — the actual TRACK 28.02B fix.
        r = httpx.get(f"{BACKEND}/api/daily-reports.csv", headers=admin_headers, timeout=60)
        assert r.status_code == 200
        assert pname not in r.text, (
            "TRACK 28.02B regression: synthetic DR leaked to /api/daily-reports.csv"
        )
    finally:
        # Cleanup: the API DELETE is intentionally 410; purge via Mongo.
        _mongo().daily_reports.delete_one({"id": dr_id})
