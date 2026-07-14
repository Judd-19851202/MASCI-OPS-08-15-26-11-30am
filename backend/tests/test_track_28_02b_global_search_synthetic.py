"""TRACK 28.02B · Global Search must not surface synthetic Daily Reports.

Discovered during the fix-as-you-certify audit that followed the CSV
export leak: `routes/global_search.py::run_daily_reports` matched
against `daily_reports` with a scope filter but WITHOUT the
`apply_synthetic_dr_exclusion` guard. Consequence — any user hitting
Cmd+K (every portal) whose query text hit a synthetic project_name /
prepared_by / weather_summary would receive the hidden certification
rows in their search results.

Fix: threaded `apply_synthetic_dr_exclusion` around the composed query
inside `run_daily_reports`.

Blast radius pre-fix:
  • Every portal that mounts the Cmd+K global search bar (admin, pm,
    hr, safety, dispatch, shop, field-leadership).
  • Every synthetic DR whose fields matched a user query.

Regression contract (this test):
  1. Seed a synthetic/certification Daily Report fixture directly into
     Mongo (submit route is now constitutionally gated by approved
     summary requirements).
  2. Hit /api/global-search?q=TEST_28_02_ with an admin token.
  3. Assert the seeded DR id is NOT in the `daily_reports`
     result kind.
  4. Cleanup via direct Mongo purge (DR delete is archive-locked 410).
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
    return {"X-Admin-Token": r.json()["portal_tokens"]["admin"]}


def test_global_search_excludes_synthetic_daily_reports(admin_headers: dict) -> None:
    pname = f"TEST_28_02_gsearch_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    dr_id = f"dr-test-28-02b-{uuid.uuid4().hex[:10]}"
    payload = {
        "id": dr_id,
        "doc_id": f"DR-TEST-{uuid.uuid4().hex[:8]}",
        "report_number": f"DR-TEST-{uuid.uuid4().hex[:8]}",
        "project_name": pname,
        "project_number": "TEST28",
        "location": "TEST · Cert",
        "report_date": date.today().isoformat(),
        "prepared_by": "TEST_28_02_GSearch_Foreman",
        "synthetic_record": True,
        "hidden_from_operations": True,
        "certification_record": True,
        "ai_accepted_summary": "Approved summary: synthetic global-search exclusion fixture.",
        "ai_accepted_summary_meta": {"source": "manual", "accepted": True},
    }
    _mongo().daily_reports.insert_one(dict(payload))

    try:
        # Query text should trivially match the synthetic project_name.
        r = httpx.get(
            f"{BACKEND}/api/search",
            headers=admin_headers,
            params={"q": "TEST_28_02_gsearch", "limit": 15},
            timeout=30,
        )
        # 200 required; if search endpoint is protected we accept 401
        # only as a hard failure (fix the auth path, don't skip).
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        # Extract daily_report rows regardless of grouping shape.
        rows = []
        if isinstance(body, dict):
            for k in ("results", "groups", "kinds"):
                v = body.get(k)
                if isinstance(v, dict):
                    rows.extend(v.get("daily_reports") or [])
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict) and it.get("kind") == "daily_reports":
                            rows.extend(it.get("results") or it.get("rows") or [])
        ids = {row.get("id") for row in rows if isinstance(row, dict)}
        assert dr_id not in ids, (
            "TRACK 28.02B regression: synthetic DR leaked to /api/global-search"
        )
    finally:
        _mongo().daily_reports.delete_one({"id": dr_id})
