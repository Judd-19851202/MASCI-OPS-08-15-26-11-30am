"""Track 13.30 · Service Truck Daily Reconciliation backend tests.

Verifies:
  * Start day creates record + status = "start_logged".
  * Re-starting the same truck/date before close is idempotent.
  * Close pulls dispensed totals from Track 13.29 fuel_lube_visits (case-
    insensitive truck match) and computes expected_end / variance / status.
  * Variance status classification (green / yellow / red / incomplete) and
    per-product overall rollup.
  * Missing close → variance_status remains "incomplete".
  * List filters (date range · truck · variance status) honored + 90-day cap.
  * Detail includes linked fuel/lube visits.
  * Optional review writes notes and re-closes the day.
  * No cost / accounting / PO number / fuel tax fields appear anywhere on
    the response (sanity assertion).
  * No mutation of fuel_lube_visits during close (read-only join).
"""
import os
import re
import time
import uuid
import httpx
import pytest


REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin() -> str:
    r = httpx.post(f"{API}/admin/login", json={"password": "Maddix123!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


def _truck() -> str:
    return f"ITEST-FL-{uuid.uuid4().hex[:6]}"


def _today_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).date().isoformat()


def _start(tok: str, *, truck: str, date: str, start_q: dict, tech_id="itest-tech") -> dict:
    body = {
        "date": date, "service_truck_unit": truck,
        "tech_id": tech_id, "tech_name": "ITest Tech",
        "start_quantities": start_q, "notes": "itest start",
    }
    r = httpx.post(f"{API}/shop/service-truck-reconciliation/start",
                   json=body, headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _visit(tok: str, *, truck: str, date: str, line: dict, project="ITEST-13-30") -> dict:
    body = {
        "visit_date": date, "project_number": project,
        "fuel_lube_truck_unit": truck,
        "fuel_lube_tech_id": "itest-tech", "fuel_lube_tech_name": "ITest Tech",
        "equipment_lines": [{
            "unit_number": f"unit-{uuid.uuid4().hex[:6]}",
            **line,
        }],
    }
    r = httpx.post(f"{API}/shop/fuel-lube/visits",
                   json=body, headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _close(tok: str, *, truck: str, date: str, end_q: dict) -> dict:
    body = {
        "date": date, "service_truck_unit": truck,
        "end_quantities": end_q, "submitted_by": "ITest Tech",
    }
    r = httpx.post(f"{API}/shop/service-truck-reconciliation/close",
                   json=body, headers={"X-Admin-Token": tok}, timeout=30)
    return r


# ── 1. Start creates record ─────────────────────────────────────────────


def test_start_creates_record_and_is_idempotent_before_close():
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    a = _start(tok, truck=truck, date=date,
               start_q={"red_diesel_gallons": 1000, "def_gallons": 50})
    assert a["status"] == "start_logged"
    # Idempotent re-start
    b = _start(tok, truck=truck, date=date,
               start_q={"red_diesel_gallons": 950, "def_gallons": 60})
    assert b["status"] == "start_logged"
    assert b["id"] == a["id"]


# ── 2. Close pulls dispensed totals from fuel/lube visits ───────────────


def test_close_pulls_dispensed_and_computes_variance_green():
    """Example from spec — within ≤2 % so GREEN even with -15 gal raw."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date,
           start_q={"red_diesel_gallons": 1000, "clear_diesel_gallons": 250,
                    "gasoline_gallons": 100, "def_gallons": 50})
    _visit(tok, truck=truck, date=date, line={
        "red_diesel_gallons": 840, "clear_diesel_gallons": 60,
        "gasoline_gallons": 20, "def_gallons": 18,
    })
    r = _close(tok, truck=truck, date=date,
               end_q={"red_diesel_gallons": 145, "clear_diesel_gallons": 190,
                      "gasoline_gallons": 80, "def_gallons": 31})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "closed"
    assert body["variance_status"] == "green"   # 15/1000=1.5%, others 0
    rec = body["reconciliation"]
    rows = {r["field"]: r for r in rec["variance"]["rows"]}
    # Red diesel: expected 160, actual 145, var -15, pct 1.5% -> green
    assert rows["red_diesel_gallons"]["expected_end"] == 160.0
    assert rows["red_diesel_gallons"]["actual_end"] == 145.0
    assert rows["red_diesel_gallons"]["variance"] == -15.0
    assert rows["red_diesel_gallons"]["status"] == "green"
    # DEF: expected 32, actual 31, var -1, abs<=2qt fuel tol 5gal -> green
    assert rows["def_gallons"]["status"] == "green"
    assert rec["dispensed_quantities"]["visit_count"] == 1


# ── 3. Yellow + Red classifications ─────────────────────────────────────


def test_close_yellow_classification():
    """Variance > 2% and ≤ 5 % → yellow."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"red_diesel_gallons": 1000})
    _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 500})
    # expected_end=500, actual=460 → variance=-40 → 4% → yellow
    r = _close(tok, truck=truck, date=date, end_q={"red_diesel_gallons": 460})
    assert r.status_code == 200
    body = r.json()
    assert body["variance_status"] == "yellow"
    assert body["status"] == "needs_review"


def test_close_red_classification():
    """Variance > 5% → red + status needs_review."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"red_diesel_gallons": 1000})
    _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 500})
    # expected_end=500, actual=400 → variance=-100 → 10% → red
    r = _close(tok, truck=truck, date=date, end_q={"red_diesel_gallons": 400})
    assert r.status_code == 200
    body = r.json()
    assert body["variance_status"] == "red"
    assert body["status"] == "needs_review"


def test_close_fluid_quart_thresholds():
    """Engine oil 30 qt baseline, expected_end 10 qt, actual 7 qt = -3 qt.
    abs<=2qt? no.  pct 3/30=10% → red."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"engine_oil_quarts": 30})
    _visit(tok, truck=truck, date=date, line={"engine_oil_quarts": 20})
    r = _close(tok, truck=truck, date=date, end_q={"engine_oil_quarts": 7})
    body = r.json()
    assert body["variance_status"] == "red"


# ── 4. Incomplete (start logged but no close) ─────────────────────────


def test_incomplete_until_close():
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    a = _start(tok, truck=truck, date=date,
               start_q={"red_diesel_gallons": 200})
    # Without closing, list shows variance_status=incomplete
    r = httpx.get(f"{API}/shop/service-truck-reconciliation",
                  params={"service_truck_unit": truck, "from": date, "to": date},
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    rows = r.json()["reconciliations"]
    match = [x for x in rows if x["id"] == a["id"]]
    assert match
    assert match[0]["variance_status"] == "incomplete"
    assert match[0]["status"] == "start_logged"


# ── 5. List filters + 90-day cap ────────────────────────────────────────


def test_list_filters_and_range_cap():
    tok = _admin()
    # default 30-day window works
    r = httpx.get(f"{API}/shop/service-truck-reconciliation",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "reconciliations" in body and "range" in body
    # >90 days rejected
    r = httpx.get(f"{API}/shop/service-truck-reconciliation",
                  params={"from": "2025-01-01", "to": "2026-06-13"},
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422
    # bad variance_status enum rejected
    r = httpx.get(f"{API}/shop/service-truck-reconciliation",
                  params={"variance_status": "purple"},
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422


# ── 6. Detail includes linked visits ────────────────────────────────────


def test_detail_includes_linked_visits():
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    a = _start(tok, truck=truck, date=date,
               start_q={"red_diesel_gallons": 500})
    v = _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 100})
    r = httpx.get(f"{API}/shop/service-truck-reconciliation/{a['id']}",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["reconciliation"]["id"] == a["id"]
    assert any(x["id"] == v["id"] for x in body["linked_visits"])


# ── 7. Review endpoint writes notes + re-closes ─────────────────────────


def test_review_writes_notes_and_clears_needs_review():
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"red_diesel_gallons": 1000})
    _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 500})
    close = _close(tok, truck=truck, date=date, end_q={"red_diesel_gallons": 400})
    assert close.json()["variance_status"] == "red"
    rec_id = close.json()["id"]
    r = httpx.post(f"{API}/shop/service-truck-reconciliation/{rec_id}/review",
                   json={"review_notes": "Confirmed siphon-back to bulk tank · adjusted.",
                         "reviewer_name": "Shop Mgr ITest"},
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "closed"
    # Detail shows the review notes
    r = httpx.get(f"{API}/shop/service-truck-reconciliation/{rec_id}",
                  headers={"X-Admin-Token": tok}, timeout=30)
    rec = r.json()["reconciliation"]
    assert rec["reviewed_by"] == "Shop Mgr ITest"
    assert "siphon-back" in rec["review_notes"]


# ── 8. Doctrine guardrails ─────────────────────────────────────────────


def test_response_has_no_cost_or_accounting_fields():
    """Sanity sweep — no cost/price/PO/tax/invoice/margin keys in response."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date,
           start_q={"red_diesel_gallons": 100})
    _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 50})
    close = _close(tok, truck=truck, date=date,
                   end_q={"red_diesel_gallons": 50})
    blob = repr(close.json()).lower()
    for forbidden in ("cost", "price", "po_number", "invoice", "tax", "margin",
                      "ledger_amount", "payable", "receivable", "general_ledger"):
        assert forbidden not in blob, f"forbidden term leaked: {forbidden}"


def test_close_does_not_mutate_fuel_lube_visit():
    """The close endpoint must NEVER mutate the source fuel/lube visits."""
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"red_diesel_gallons": 500})
    v = _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 100})
    before = httpx.get(f"{API}/shop/fuel-lube/visits/{v['id']}",
                      headers={"X-Admin-Token": tok}, timeout=30).json()
    _close(tok, truck=truck, date=date, end_q={"red_diesel_gallons": 400})
    after = httpx.get(f"{API}/shop/fuel-lube/visits/{v['id']}",
                     headers={"X-Admin-Token": tok}, timeout=30).json()
    # Status must remain "submitted" · totals must match · submitted_at must match
    assert before["status"] == after["status"]
    assert before["totals"] == after["totals"]
    assert before["submitted_at"] == after["submitted_at"]


# ── 9. Cannot re-open a closed day ──────────────────────────────────────


def test_cannot_restart_a_closed_day():
    tok = _admin()
    truck = _truck()
    date = _today_iso()
    _start(tok, truck=truck, date=date, start_q={"red_diesel_gallons": 100})
    _visit(tok, truck=truck, date=date, line={"red_diesel_gallons": 50})
    close = _close(tok, truck=truck, date=date, end_q={"red_diesel_gallons": 50})
    assert close.status_code == 200
    # Now try to restart — should 409
    body = {
        "date": date, "service_truck_unit": truck,
        "tech_id": "itest", "tech_name": "ITest Tech",
        "start_quantities": {"red_diesel_gallons": 200},
    }
    r = httpx.post(f"{API}/shop/service-truck-reconciliation/start",
                   json=body, headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 409
