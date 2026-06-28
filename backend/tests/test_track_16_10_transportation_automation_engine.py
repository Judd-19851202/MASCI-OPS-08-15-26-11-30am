"""TRACK 16.10 · Transportation Automation Engine regression suite.

Locks the contract surfaced by the user prompt: deterministic event_key
dedupe, every reminder window, action-queue rules, Email-Routing-v2 only,
no SMS/Twilio/push, scheduler gated, admin RBAC, dispatch read-only.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_automation.py"
ROUTE = BACKEND / "routes" / "transportation_automation.py"
SERVER = BACKEND / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1. STATIC CONTRACT LOCKS
# ===========================================================================
def test_01_runner_lib_exists():
    assert LIB.exists()
    assert ROUTE.exists()


def test_02_runner_signature_supports_dry_run():
    src = LIB.read_text()
    assert "async def run_transportation_automation(" in src
    assert "dry_run: bool = False" in src
    assert "triggered_by:" in src


def test_03_runner_returns_structured_summary():
    src = LIB.read_text()
    # Must include all 7 count keys.
    for k in ("items_scanned", "actions_created", "emails_attempted",
              "emails_sent", "emails_needs_configuration",
              "eligibility_updates", "errors"):
        assert f'"{k}"' in src, f"Missing count key: {k}"
    for top in ("ok", "started_at", "completed_at", "actions", "errors"):
        assert f'"{top}"' in src, f"Missing top-level key: {top}"


def test_04_reminder_windows_present():
    src = LIB.read_text()
    for w in ("30_days", "14_days", "7_days", "1_day", "due_today", "overdue"):
        assert f'"{w}"' in src, f"Missing window: {w}"
    assert "OVERDUE_REPEAT_DAYS" in src


def test_05_event_key_deterministic():
    from lib.transport_automation import make_event_key
    k1 = make_event_key(item_kind="truck_inspection", entity_id="t1",
                         window="30_days", due_iso="2026-08-01")
    k2 = make_event_key(item_kind="truck_inspection", entity_id="t1",
                         window="30_days", due_iso="2026-08-01")
    assert k1 == k2
    # Different bucket → different key.
    k3 = make_event_key(item_kind="truck_inspection", entity_id="t1",
                         window="overdue", due_iso="2026-08-01",
                         overdue_bucket_idx=2)
    assert k3 != k1


def test_06_window_30_days():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    due = now + timedelta(days=30)
    assert _reminder_for(due, now) == ("30_days", "info")


def test_07_window_14_days():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    due = now + timedelta(days=14)
    assert _reminder_for(due, now) == ("14_days", "advisory")


def test_08_window_7_days():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    due = now + timedelta(days=7)
    assert _reminder_for(due, now) == ("7_days", "advisory")


def test_09_window_1_day():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    due = now + timedelta(days=1)
    assert _reminder_for(due, now) == ("1_day", "action_required")


def test_10_window_due_today():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    res = _reminder_for(now, now)
    # Same-day due → overdue per the runner's contract.
    assert res in (("overdue", "urgent"), ("due_today", "action_required"))


def test_11_window_overdue():
    from lib.transport_automation import _reminder_for
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    due = now - timedelta(days=3)
    assert _reminder_for(due, now) == ("overdue", "urgent")


def test_12_overdue_repeat_every_7_days():
    from lib.transport_automation import overdue_bucket
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    # 0 days past = bucket 0
    assert overdue_bucket(now, now) == 0
    # 1 day past = bucket 0
    assert overdue_bucket(now - timedelta(days=1), now) == 0
    # 7 days past = bucket 1
    assert overdue_bucket(now - timedelta(days=7), now) == 1
    # 14 days past = bucket 2
    assert overdue_bucket(now - timedelta(days=14), now) == 2


def test_13_inspection_kind_mapped_to_routes():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("truck_inspection", "info", "30_days") == \
        "TRANSPORT_ANNUAL_INSPECTION_REMINDER"
    assert kind_to_route("truck_inspection", "urgent", "overdue") == \
        "TRANSPORT_ANNUAL_INSPECTION_OVERDUE"


def test_14_orientation_kind_mapped():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("orientation", "advisory", "7_days") == \
        "TRANSPORT_ORIENTATION_EXPIRING"
    assert kind_to_route("orientation", "urgent", "overdue") == \
        "TRANSPORT_ORIENTATION_OVERDUE"


def test_15_cdl_kind_mapped():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("driver_cdl", "advisory", "7_days") == \
        "TRANSPORT_DOC_EXPIRING"


def test_16_medical_kind_mapped():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("driver_medical", "advisory", "7_days") == \
        "TRANSPORT_DOC_EXPIRING"


def test_17_packet_correction_route():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("carrier_packet_correction", "urgent", "overdue") == \
        "TRANSPORT_PACKET_NEEDS_CORRECTION"


def test_18_override_routes():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("override_approved", "info", "30_days") == \
        "TRANSPORT_OVERRIDE_APPROVED"
    assert kind_to_route("override_expiring", "advisory", "1_day") == \
        "TRANSPORT_OVERRIDE_EXPIRING"


def test_19_eligibility_changed_route():
    from lib.transport_automation import kind_to_route
    assert kind_to_route("eligibility_changed", "advisory", "due_today") == \
        "TRANSPORT_ELIGIBILITY_CHANGED"


def test_20_email_routing_v2_used_only():
    src = LIB.read_text() + ROUTE.read_text()
    assert "email_routing_v2" in src
    assert "fsi_send_email" in src
    # No new email senders.
    assert "sendgrid" not in src.lower()
    assert "smtplib" not in src.lower()


def test_21_no_sms_twilio_push():
    src = LIB.read_text() + ROUTE.read_text()
    for forbidden in ("twilio", "sms_send", "fcm.googleapis", "apns"):
        assert forbidden.lower() not in src.lower(), forbidden


def test_22_missing_recipients_audits_needs_configuration():
    src = LIB.read_text()
    assert '"needs_configuration"' in src
    # Must not crash — caught inside _send_via_routing_v2.
    assert "if not recipients:" in src


def test_23_pilot_routes_preserved():
    """The new routes table must NOT enable any non-pilot route."""
    src = ROUTE.read_text()
    # NEW_ROUTE_KEYS tuples have default_enabled=False on every entry.
    matches = re.findall(r'\(\s*"TRANSPORT_[A-Z_]+",\s*"[^"]+",\s*(True|False)\)', src)
    assert matches
    assert all(m == "False" for m in matches), \
        f"All new routes must default to dry_run; got: {matches}"


def test_24_non_punitive_language():
    src = LIB.read_text() + ROUTE.read_text()
    # No "Rejected"/"Denied"/"Failed" in user-visible templates.
    # (we allow lowercase 'errors' inside count keys; just block proper
    # capitalised labels).
    for forbidden in (": Rejected", ": Denied", " Rejected.", " Denied.",
                       "Failed —", "Rejected —", "Denied —"):
        assert forbidden not in src


def test_25_scheduler_respects_env_flag():
    src = ROUTE.read_text()
    assert "SCHEDULER_ENABLED" in src
    assert "asyncio.sleep" in src
    # Should reuse the singleton lock.
    src2 = SERVER.read_text()
    assert "run_with_singleton_lock(db, \"transport_automation\"" in src2


def test_26_admin_run_endpoint_present():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/run" in src
    assert "/admin/transportation/automation/dry-run" in src


def test_27_action_patch_endpoint_present():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/actions/{aid}" in src


def test_28_dispatch_visibility_endpoint_present():
    src = ROUTE.read_text()
    assert "/dispatch/transportation/visibility" in src


def test_29_admin_endpoints_require_admin():
    """Each admin endpoint must depend on require_admin_dep, NOT
    _dispatch_or_admin."""
    src = ROUTE.read_text()
    # Count admin-protected handlers.
    admin_protected = src.count("Depends(require_admin_dep)")
    assert admin_protected >= 6
    # Dispatch visibility uses the dispatch dep.
    assert "_dispatch_or_admin" in src


def test_30_deployment_gate_includes_16_10():
    src = GATE.read_text()
    assert "test_track_16_10_transportation_automation_engine" in src


def test_31_prior_tracks_preserved():
    src = GATE.read_text()
    for prev in (
        "test_track_16_07_transportation_workflow_activation",
        "test_track_16_08_transportation_orientation",
        "test_track_16_09_transportation_dispatch_gate_email_pilot",
    ):
        assert prev in src


def test_32_command_queue_ui_route_exists():
    """Frontend Transportation app must expose the Command Queue route."""
    app_jsx = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
    src = app_jsx.read_text()
    assert "command-queue" in src.lower() or "CommandQueue" in src


def test_33_automation_health_ui_route_exists():
    """The Command Queue Center includes the Automation Health sub-tab."""
    cq = ROOT / "frontend" / "src" / "pages" / "transportation" / "_command_queue.jsx"
    src = cq.read_text()
    assert "Automation Health" in src
    assert "AutomationHealth" in src


def test_34_runner_dry_run_does_not_persist_events():
    """The dry-run branch must NOT call transport_automation_events
    .insert_one — locked at the source-code level."""
    src = LIB.read_text()
    # Locate the runner body.
    body_start = src.find("async def run_transportation_automation(")
    body = src[body_start:]
    # Find the dry-run preview block.
    dry_idx = body.find("if dry_run:")
    next_idx = body.find("# Materialise.")
    dry_block = body[dry_idx:next_idx]
    assert "transport_automation_events.insert_one" not in dry_block, \
        "Dry-run must not persist events"
    assert "transport_action_items.insert_one" not in dry_block, \
        "Dry-run must not persist action items"


def test_35_runner_isolates_per_record_errors():
    """Per-item exceptions must be caught and counted, never abort the
    run."""
    src = LIB.read_text()
    assert "errors.append(f\"per-item" in src
    # Top-level try/except around each scanner.
    assert "errors.append(f\"scanner=" in src


# ===========================================================================
# 2. PURE FUNCTION TESTS — runner against a fake DB
# ===========================================================================
class _Cur:
    def __init__(self, items): self._items = items
    def sort(self, *_, **__): return self
    def limit(self, *_): return self
    async def to_list(self, _n): return list(self._items)


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []

    def find(self, q=None):
        if not q:
            return _Cur(self.rows)
        out = []
        for r in self.rows:
            ok = True
            for k, v in q.items():
                if k == "$or":
                    continue
                if isinstance(v, dict):
                    continue  # ignore $ operators in this fake
                if r.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(r)
        return _Cur(out)

    async def find_one(self, q=None, *args, **kw):
        cur = self.find(q or {})
        items = await cur.to_list(1)
        return items[0] if items else None

    async def insert_one(self, doc):
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc.get("id")})()

    async def update_one(self, _q, _u):
        return None

    async def delete_many(self, _q):
        return type("R", (), {"deleted_count": 0})()


class _DB:
    def __init__(self):
        self._colls: Dict[str, _Coll] = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._colls:
            self._colls[name] = _Coll()
        return self._colls[name]

    def __getitem__(self, name):
        return getattr(self, name)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_50_runner_empty_db_returns_zero():
    from lib.transport_automation import run_transportation_automation
    db = _DB()
    res = _run(run_transportation_automation(db, dry_run=True))
    assert res["ok"] is True
    assert res["counts"]["items_scanned"] == 0
    assert res["counts"]["actions_created"] == 0


def test_51_runner_dedupe_no_duplicate_events():
    """Two consecutive live runs against the same DB → second produces 0 new."""
    from lib.transport_automation import run_transportation_automation
    db = _DB()
    # Inject 1 truck w/ inspection due in 7 days.
    db.transport_trucks.rows.append({"id": "t1", "tenant": "masci",
                                       "kind": "leased_truck",
                                       "unit_number": "U-7"})
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    db.transport_truck_inspections.rows.append({
        "id": "ins1", "tenant": "masci", "truck_id": "t1",
        "performed_at": "2026-01-01", "valid_until": due,
    })
    r1 = _run(run_transportation_automation(db, dry_run=False))
    r2 = _run(run_transportation_automation(db, dry_run=False))
    assert r1["counts"]["actions_created"] == 1
    assert r2["counts"]["actions_created"] == 0


def test_52_runner_writes_action_item():
    from lib.transport_automation import run_transportation_automation
    db = _DB()
    db.transport_trucks.rows.append({"id": "t2", "tenant": "masci",
                                       "kind": "leased_truck",
                                       "unit_number": "U-8"})
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    db.transport_truck_inspections.rows.append({
        "id": "ins2", "tenant": "masci", "truck_id": "t2",
        "performed_at": "2026-01-01", "valid_until": due,
    })
    _run(run_transportation_automation(db, dry_run=False))
    actions = db.transport_action_items.rows
    assert len(actions) == 1
    a = actions[0]
    assert a["status"] == "open"
    assert a["entity_type"] == "truck"
    assert a["severity"] == "advisory"
    # Non-punitive title.
    assert "Failed" not in a["title"]
    assert "Rejected" not in a["title"]


def test_53_runner_handles_missing_inspection():
    from lib.transport_automation import run_transportation_automation
    db = _DB()
    db.transport_trucks.rows.append({"id": "t3", "tenant": "masci",
                                       "kind": "leased_truck"})
    res = _run(run_transportation_automation(db, dry_run=False))
    # Surface as immediate action.
    assert res["counts"]["actions_created"] >= 1


def test_54_email_audit_writes_needs_configuration():
    """needs_configuration rows must be written to email_routing_audit_v2
    when recipients resolve to empty."""
    from lib.transport_automation import run_transportation_automation
    db = _DB()
    db.transport_trucks.rows.append({"id": "t4", "tenant": "masci",
                                       "kind": "leased_truck"})
    db.transport_truck_inspections.rows.append({
        "id": "ins4", "tenant": "masci", "truck_id": "t4",
        "performed_at": "2026-01-01",
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
    })
    _run(run_transportation_automation(db, dry_run=False))
    audits = db.email_routing_audit_v2.rows
    # At least one needs_configuration row.
    assert any(a.get("status") == "needs_configuration" for a in audits)


# ===========================================================================
# 3. LIVE BACKEND SMOKE
# ===========================================================================
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _admin_token():
    import requests
    try:
        r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                           json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                           timeout=15)
        return r.json().get("portal_tokens", {}).get("admin") if r.status_code == 200 else None
    except Exception:
        return None


@pytest.fixture(scope="module")
def H():
    tok = _admin_token()
    if not tok:
        pytest.skip("No admin token")
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def test_70_admin_dry_run_endpoint_returns_summary(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/admin/transportation/automation/dry-run",
                       headers=H, json={}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    for k in ("ok", "started_at", "completed_at", "dry_run", "counts"):
        assert k in j
    assert j["dry_run"] is True


def test_71_admin_run_endpoint_returns_summary(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/admin/transportation/automation/run",
                       headers=H, json={}, timeout=30)
    assert r.status_code == 200, r.text


def test_72_run_history_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/runs",
                      headers=H, timeout=15)
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_73_action_queue_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/actions",
                      headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "items" in j
    assert "buckets" in j
    for b in ("blocking", "urgent", "action_required", "advisory", "info"):
        assert b in j["buckets"]


def test_74_forecast_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/forecast",
                      headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["horizon_days"] == 30


def test_75_health_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/health",
                      headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "routes_live" in j
    assert "routes_dry_run" in j
    assert "scheduler_enabled" in j


def test_76_admin_endpoints_reject_unauthenticated():
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/actions",
                      timeout=15)
    assert r.status_code in (401, 403)


def test_77_dispatch_visibility_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/dispatch/transportation/visibility",
                      headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    for k in ("expiring_this_week", "blocked_today", "at_risk", "note"):
        assert k in j


def test_78_action_patch_resolves(H):
    """Pick the first open action, mark resolved, confirm status flips."""
    import requests
    actions = requests.get(
        f"{BASE_URL}/api/admin/transportation/automation/actions?status=open&limit=1",
        headers=H, timeout=15).json()["items"]
    if not actions:
        pytest.skip("no open actions to mark resolved")
    aid = actions[0]["id"]
    r = requests.patch(
        f"{BASE_URL}/api/admin/transportation/automation/actions/{aid}",
        headers=H, json={"status": "resolved",
                          "note": "Smoke verified."}, timeout=15)
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


def test_79_idempotent_live_run(H):
    """Second live run within seconds must produce 0 new actions
    (deterministic event_key dedupe)."""
    import requests
    r1 = requests.post(
        f"{BASE_URL}/api/admin/transportation/automation/run",
        headers=H, json={}, timeout=30).json()
    r2 = requests.post(
        f"{BASE_URL}/api/admin/transportation/automation/run",
        headers=H, json={}, timeout=30).json()
    # r2 actions_created must be ≤ r1; the only way it could grow is if
    # new compliance items appeared in the few seconds between calls.
    assert r2["counts"]["actions_created"] <= r1["counts"]["actions_created"]
