"""
test_iter161_ops_center_signal_cards.py — Iter161.

Verifies the two signal-derived Operations Center cards added on top of
Iter160 telemetry:

  * po_approval_p90 (admin + pm)
  * repeat_equipment_failures (admin + shop + dispatch)

Discipline guard:
  - Empty state returns severity='Info' with display='No signal yet'
  - Threshold ladders are exactly as approved by the user
  - severity is on the CARD, not nested inside value
  - PM gets po_approval_p90, NOT repeat_equipment_failures
  - Shop+Dispatch get repeat_equipment_failures, NOT po_approval_p90
  - Existing cards (tasks_overdue etc.) still render — no regression
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

import sys
sys.path.insert(0, "/app/backend")


def _kv(p, k):
    try:
        with open(p) as f:
            for line in f:
                if line.startswith(f"{k}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
       or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
MONGO_URL = _kv(Path("/app/backend/.env"), "MONGO_URL")
DB_NAME = _kv(Path("/app/backend/.env"), "DB_NAME")


def _get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


def _arun(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _get_admin_token():
    r = requests.post(f"{URL}/api/admin/login",
                      json={"password": "MASCI1982!"},
                      headers={"X-Admin-Token": ""}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


# ──────────────────────────────────────────────────────────────────
# Admin ops-center contract — both new cards present
# ──────────────────────────────────────────────────────────────────
def test_admin_ops_center_has_signal_cards():
    r = requests.get(f"{URL}/api/operations-center", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    keys = {c["key"] for c in data["cards"]}
    assert "po_approval_p90" in keys
    assert "repeat_equipment_failures" in keys


def test_pm_gets_po_approval_p90_not_repeat_equipment():
    """PM role visibility: po_approval_p90 yes · repeat_equipment_failures no."""
    tok = _get_admin_token()
    r = requests.get(
        f"{URL}/api/operations-center?role_override=pm",
        headers={"X-Admin-Token": tok}, timeout=15,
    )
    assert r.status_code == 200
    keys = {c["key"] for c in r.json()["cards"]}
    assert "po_approval_p90" in keys
    assert "repeat_equipment_failures" not in keys


def test_shop_gets_repeat_equipment_not_po_approval():
    """Shop role: repeat_equipment_failures yes · po_approval_p90 no."""
    tok = _get_admin_token()
    r = requests.get(
        f"{URL}/api/operations-center?role_override=shop",
        headers={"X-Admin-Token": tok}, timeout=15,
    )
    assert r.status_code == 200
    keys = {c["key"] for c in r.json()["cards"]}
    assert "repeat_equipment_failures" in keys
    assert "po_approval_p90" not in keys


def test_dispatch_gets_repeat_equipment_not_po_approval():
    tok = _get_admin_token()
    r = requests.get(
        f"{URL}/api/operations-center?role_override=dispatch",
        headers={"X-Admin-Token": tok}, timeout=15,
    )
    assert r.status_code == 200
    keys = {c["key"] for c in r.json()["cards"]}
    assert "repeat_equipment_failures" in keys
    assert "po_approval_p90" not in keys


# ──────────────────────────────────────────────────────────────────
# Card shape contract — severity is on the CARD, not nested in value
# ──────────────────────────────────────────────────────────────────
def test_signal_card_shape_severity_on_card():
    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    for key in ("po_approval_p90", "repeat_equipment_failures"):
        card = next(c for c in r["cards"] if c["key"] == key)
        assert "severity" in card and card["severity"] in ("Info", "Warning", "Critical")
        assert "value" in card
        # severity must have been stripped from the value payload (it
        # always lives on the card to keep the frontend contract clean).
        assert "severity" not in card["value"]
        assert "display" in card["value"]
        assert "count" in card["value"]


# ──────────────────────────────────────────────────────────────────
# Empty-state behaviour — neutral, plain wording, no alarm
# ──────────────────────────────────────────────────────────────────
def test_po_approval_p90_empty_state_neutral():
    """Clear all po.approve signals in the last 30d; expect Info severity
    + 'No signal yet' display."""
    async def clear():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal",
            "signal": "po.approve",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
    _arun(clear())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"] if c["key"] == "po_approval_p90")
    assert card["severity"] == "Info"
    assert card["value"]["display"] == "No signal yet"
    assert card["value"]["count"] == 0


def test_repeat_equipment_failures_empty_state_neutral():
    async def clear():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal",
            "signal": "equipment.fail",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
    _arun(clear())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"]
                if c["key"] == "repeat_equipment_failures")
    assert card["severity"] == "Info"
    assert card["value"]["display"] == "No signal yet"
    assert card["value"]["count"] == 0


# ──────────────────────────────────────────────────────────────────
# Threshold ladders — exactly as approved by the user
# ──────────────────────────────────────────────────────────────────
def test_po_approval_threshold_amber_warning_at_72h():
    """Seed po.approve signals at 72h elapsed → p90 ≈ 72h → severity Warning."""
    from lib.operational_signals import record_signal
    marker = f"po_amber_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        # Clear other recent po.approve to isolate
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "po.approve",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        # 10 events all at 72h = warning band (>48h, ≤120h)
        for _ in range(10):
            await record_signal(
                db, signal="po.approve", module="po.requests",
                elapsed_ms=72 * 3600 * 1000,
                dims={"_m": marker},
            )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"] if c["key"] == "po_approval_p90")
    assert card["severity"] == "Warning"
    assert "h" in card["value"]["display"] or "d" in card["value"]["display"]

    # Cleanup
    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_po_approval_threshold_red_critical_above_120h():
    """Seed po.approve at 240h elapsed → severity Critical."""
    from lib.operational_signals import record_signal
    marker = f"po_red_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "po.approve",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        for _ in range(10):
            await record_signal(
                db, signal="po.approve", module="po.requests",
                elapsed_ms=240 * 3600 * 1000,
                dims={"_m": marker},
            )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"] if c["key"] == "po_approval_p90")
    assert card["severity"] == "Critical"

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_po_approval_threshold_info_under_48h():
    """Seed po.approve at 1h elapsed → severity Info (neutral)."""
    from lib.operational_signals import record_signal
    marker = f"po_info_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "po.approve",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        for _ in range(10):
            await record_signal(
                db, signal="po.approve", module="po.requests",
                elapsed_ms=3600 * 1000,  # 1 hour
                dims={"_m": marker},
            )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"] if c["key"] == "po_approval_p90")
    assert card["severity"] == "Info"

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_repeat_equipment_threshold_amber_at_1_offender():
    """Seed 3 fails for one equipment → 1 repeat offender → Warning."""
    from lib.operational_signals import record_signal
    marker = f"eq_amber_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "equipment.fail",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        eq = f"EQ-{marker}"
        for _ in range(3):
            await record_signal(
                db, signal="equipment.fail", module="test",
                dims={"equipment_id": eq, "_m": marker},
            )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"]
                if c["key"] == "repeat_equipment_failures")
    assert card["severity"] == "Warning"
    assert card["value"]["count"] == 1

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_repeat_equipment_threshold_red_at_3_offenders():
    """Seed 3 fails each for 3 different equipment → Critical."""
    from lib.operational_signals import record_signal
    marker = f"eq_red_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "equipment.fail",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        for eq_suffix in ("A", "B", "C"):
            for _ in range(3):
                await record_signal(
                    db, signal="equipment.fail", module="test",
                    dims={"equipment_id": f"EQ-{eq_suffix}-{marker}",
                          "_m": marker},
                )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"]
                if c["key"] == "repeat_equipment_failures")
    assert card["severity"] == "Critical"
    assert card["value"]["count"] == 3
    assert len(card["value"]["top"]) == 3

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_repeat_equipment_below_threshold_stays_info():
    """Seed 2 fails for one equipment (below 3-threshold) → 0 repeat
    offenders → Info severity (no false positive)."""
    from lib.operational_signals import record_signal
    marker = f"eq_below_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        await db.usage_events.delete_many({
            "kind": "operational_signal", "signal": "equipment.fail",
            "at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
        })
        eq = f"EQ-{marker}"
        for _ in range(2):  # Only 2 fails — below 3-threshold
            await record_signal(
                db, signal="equipment.fail", module="test",
                dims={"equipment_id": eq, "_m": marker},
            )
    _arun(seed())

    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    card = next(c for c in r["cards"]
                if c["key"] == "repeat_equipment_failures")
    assert card["severity"] == "Info"  # No repeat offender at <3 fails
    assert card["value"]["count"] == 0

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


# ──────────────────────────────────────────────────────────────────
# Regression — existing cards untouched
# ──────────────────────────────────────────────────────────────────
def test_existing_cards_still_render():
    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    keys = {c["key"] for c in r["cards"]}
    # Sanity check: the legacy cards are still there.
    for legacy in ("tasks_overdue", "po_pending_approval", "doc_exp_expiring",
                   "incidents_open", "ca_overdue", "equipment_down",
                   "audit_coverage"):
        assert legacy in keys


def test_signal_cards_carry_url_for_deep_link():
    r = requests.get(f"{URL}/api/operations-center", timeout=15).json()
    for key in ("po_approval_p90", "repeat_equipment_failures"):
        card = next(c for c in r["cards"] if c["key"] == key)
        assert card.get("url"), f"{key} must carry a deep-link url"
        assert card["url"].startswith("/")
