"""TRACK 16.10A · Monday-morning Transportation Command Digest regression.

Static contract locks + pure builder tests + live e2e against the
preview backend.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_command_digest.py"
ROUTE = BACKEND / "routes" / "transportation_automation.py"
SERVER = BACKEND / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ===========================================================================
# 1. STATIC CONTRACT LOCKS
# ===========================================================================
def test_01_digest_lib_exists():
    assert LIB.exists()


def test_02_builder_and_sender_present():
    src = LIB.read_text()
    assert "async def build_transport_command_digest" in src
    assert "async def send_transport_command_digest" in src


def test_03_weekly_route_key_seeded():
    src = ROUTE.read_text()
    assert "TRANSPORT_COMMAND_DIGEST_WEEKLY" in src


def test_04_route_is_internal_only():
    src = ROUTE.read_text()
    assert 'internal_only": route_key == "TRANSPORT_COMMAND_DIGEST_WEEKLY"' in src


def test_05_route_defaults_dry_run_disabled():
    """Locked: every NEW_ROUTE_KEYS entry, including the digest, ships
    enabled=False."""
    src = ROUTE.read_text()
    m = re.search(r"NEW_ROUTE_KEYS\s*=\s*\((.*?)\)\s*\n\n", src, re.DOTALL)
    assert m
    # Every tuple's 3rd entry must be False.
    bools = re.findall(r"\(\s*\"TRANSPORT_[A-Z_]+\",\s*\"[^\"]+\",\s*(True|False)\s*\)", m.group(1))
    assert bools, "Expected route tuples"
    assert all(b == "False" for b in bools), \
        f"All routes (including digest) must default to dry-run: {bools}"


def test_06_builder_reads_action_queue():
    src = LIB.read_text()
    assert "transport_action_items" in src


def test_07_builder_summarises_blocking():
    src = LIB.read_text()
    assert "blocking_items" in src
    assert '"blocking"' in src


def test_08_builder_summarises_urgent():
    src = LIB.read_text()
    assert "urgent_items" in src


def test_09_builder_summarises_due_soon():
    src = LIB.read_text()
    assert "expiring_soon_items" in src
    assert "due_this_week" in src


def test_10_builder_summarises_overdue():
    src = LIB.read_text()
    assert "overdue_items" in src
    assert "Overdue" in src


def test_11_builder_summarises_email_route_health():
    src = LIB.read_text()
    assert "routes_active" in src
    assert "routes_audit_only" in src
    assert "routes_needs_configuration" in src


def test_12_digest_includes_command_queue_links():
    src = LIB.read_text()
    assert "Transportation Command Queue" in src
    assert "/admin/transportation/command-queue" in src


def test_13_digest_has_plain_text_body():
    src = LIB.read_text()
    assert "_render_text" in src
    assert '"body_text"' in src


def test_14_digest_has_html_body():
    src = LIB.read_text()
    assert "_render_html" in src
    assert '"body_html"' in src


def test_15_sender_uses_email_routing_v2():
    src = LIB.read_text()
    assert "email_routing_v2" in src
    assert "resolve_and_audit" in src


def test_16_no_duplicate_sender_logic():
    src = LIB.read_text()
    # Re-uses the existing fsi primitive.
    assert "fsi_send_email" in src
    # No alternate sender libs.
    assert "smtplib" not in src
    assert "sendgrid" not in src.lower()


def test_17_no_sms_twilio_push():
    src = LIB.read_text() + ROUTE.read_text()
    for forbidden in ("twilio", "sms_send", "apns", "fcm.googleapis"):
        assert forbidden.lower() not in src.lower(), forbidden


def test_18_missing_recipients_audits_needs_configuration():
    src = LIB.read_text()
    assert "needs_configuration" in src
    assert "if not recipients:" in src


def test_19_weekly_dedupe_via_iso_week_key():
    src = LIB.read_text()
    assert "_week_key" in src
    assert "isocalendar" in src
    assert 'transport_command_digest:' in src
    # Dedupe filter present.
    assert "already_sent_this_week" in src


def test_20_dry_run_repeatable():
    """Live runs guarded by dedupe; dry-run is NOT — same dry-run can be
    re-fired indefinitely."""
    src = LIB.read_text()
    # Dedupe filter explicitly checks `not dry_run and not force`.
    assert "if not dry_run and not force:" in src


def test_21_scheduler_respects_env_flag():
    src = ROUTE.read_text()
    assert "transport_command_digest_scheduler_loop" in src
    assert "SCHEDULER_ENABLED" in src
    # Monday detection.
    assert "weekday() == 0" in src


def test_22_admin_dry_run_endpoint():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/digest/dry-run" in src


def test_23_admin_send_now_endpoint():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/digest/send-now" in src


def test_24_admin_preview_endpoint():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/digest/preview" in src


def test_25_admin_run_history_endpoint():
    src = ROUTE.read_text()
    assert "/admin/transportation/automation/digest/runs" in src


def test_26_ui_status_card_exists():
    fe = ROOT / "frontend" / "src" / "pages" / "transportation" / "_command_queue.jsx"
    src = fe.read_text()
    assert "digest" in src.lower()
    assert "DigestCard" in src or "digest" in src.lower()


def test_27_no_external_carrier_recipients():
    """The digest module must NOT reference carrier_documents / carrier
    contact-email resolution paths. Recipients come solely from the
    TRANSPORT_COMMAND_DIGEST_WEEKLY route configuration (internal)."""
    src = LIB.read_text()
    # Sender resolves recipients through resolve_and_audit only.
    assert "carrier_contact_email" not in src
    assert "external_carrier" not in src
    # Route is explicitly marked internal_only at bootstrap (see test_04).


def test_28_no_punitive_language():
    src = LIB.read_text()
    for forbidden in (": Rejected", ": Denied", " Failed —",
                       "Rejected —", "Denied —", "Failed.\n"):
        assert forbidden not in src


def test_29_track_16_10_tests_preserved():
    src = GATE.read_text()
    assert "test_track_16_10_transportation_automation_engine" in src


def test_30_deployment_gate_includes_track_16_10A():
    src = GATE.read_text()
    assert "test_track_16_10a_transport_command_digest" in src


def test_31_scheduler_armed_in_server():
    src = SERVER.read_text()
    assert "transport_command_digest_scheduler_loop" in src
    assert 'run_with_singleton_lock(db, "transport_command_digest"' in src


def test_32_subject_line_format():
    src = LIB.read_text()
    assert "MASCI Transportation Command Digest" in src
    assert "Week of " in src


# ===========================================================================
# 2. PURE BUILDER TESTS
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
                if k == "$regex" or isinstance(v, dict):
                    continue
                if r.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(r)
        return _Cur(out)

    async def find_one(self, q=None, *_, **__):
        cur = self.find(q or {})
        items = await cur.to_list(1)
        return items[0] if items else None

    async def insert_one(self, doc):
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc.get("id")})()


class _DB:
    def __init__(self):
        self._c: Dict[str, _Coll] = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._c:
            self._c[name] = _Coll()
        return self._c[name]

    def __getitem__(self, k):
        return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_50_builder_empty_db_returns_zero_summary():
    from lib.transport_command_digest import build_transport_command_digest
    out = _run(build_transport_command_digest(_DB()))
    assert out["summary"]["open_total"] == 0
    assert out["summary"]["blocking"] == 0
    assert out["internal_only"] is True
    assert "MASCI Transportation Command Digest" in out["subject"]
    assert "MASCI Transportation Command Digest" in out["body_text"]
    assert "<h2" in out["body_html"]


def test_51_builder_buckets_by_severity():
    from lib.transport_command_digest import build_transport_command_digest
    db = _DB()
    db.transport_action_items.rows.append({
        "id": "a1", "tenant": "masci", "status": "open",
        "severity": "blocking", "title": "Driver blocked",
        "due_date": "2026-06-25",
    })
    db.transport_action_items.rows.append({
        "id": "a2", "tenant": "masci", "status": "open",
        "severity": "urgent", "title": "Inspection expired",
        "due_date": "2026-06-25",
    })
    out = _run(build_transport_command_digest(db))
    assert out["summary"]["blocking"] == 1
    assert out["summary"]["urgent"] == 1


def test_52_builder_route_health_classification():
    from lib.transport_command_digest import build_transport_command_digest
    db = _DB()
    db.email_routes.rows.append({
        "tenant_key": "masci", "route_key": "TRANSPORT_CARRIER_INVITE",
        "enabled": True, "to": ["dispatch@masci.com"],
    })
    db.email_routes.rows.append({
        "tenant_key": "masci", "route_key": "TRANSPORT_DOC_EXPIRING",
        "enabled": False, "to": [],
    })
    db.email_routes.rows.append({
        "tenant_key": "masci", "route_key": "TRANSPORT_COMMAND_DIGEST_WEEKLY",
        "enabled": True, "to": [],
    })
    out = _run(build_transport_command_digest(db))
    assert "TRANSPORT_CARRIER_INVITE" in out["routes_active"]
    assert "TRANSPORT_DOC_EXPIRING" in out["routes_audit_only"]
    assert "TRANSPORT_COMMAND_DIGEST_WEEKLY" in out["routes_needs_configuration"]


def test_53_sender_dedupe_for_live():
    from lib.transport_command_digest import send_transport_command_digest
    db = _DB()
    # Seed a prior sent run for the current week.
    from lib.transport_command_digest import _week_key  # noqa: WPS437
    wk = _week_key()
    db.transport_command_digest_runs.rows.append({
        "tenant": "masci", "week_key": wk, "dry_run": False,
        "status": "sent",
    })
    out = _run(send_transport_command_digest(db, dry_run=False))
    assert out.get("skipped") is True
    assert out["status"] == "already_sent_this_week"


def test_54_sender_dry_run_not_blocked_by_dedupe():
    from lib.transport_command_digest import send_transport_command_digest
    db = _DB()
    from lib.transport_command_digest import _week_key
    wk = _week_key()
    db.transport_command_digest_runs.rows.append({
        "tenant": "masci", "week_key": wk, "dry_run": False,
        "status": "sent",
    })
    out = _run(send_transport_command_digest(db, dry_run=True))
    # Dry-run NEVER short-circuits.
    assert out.get("skipped") is not True


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


def test_70_preview_endpoint(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/digest/preview",
                      headers=H, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "subject" in j
    assert "body_html" in j
    assert "body_text" in j
    assert j["internal_only"] is True


def test_71_dry_run_endpoint(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/admin/transportation/automation/digest/dry-run",
                       headers=H, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["dry_run"] is True


def test_72_send_now_handles_needs_configuration(H):
    import requests
    r = requests.post(f"{BASE_URL}/api/admin/transportation/automation/digest/send-now",
                       headers=H, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    # Recipients empty → needs_configuration is the canonical answer.
    assert j["status"] in ("needs_configuration", "sent",
                           "already_sent_this_week")


def test_73_runs_history(H):
    import requests
    r = requests.get(f"{BASE_URL}/api/admin/transportation/automation/digest/runs",
                      headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "items" in j


def test_74_preview_endpoint_admin_only():
    import requests
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/automation/digest/preview",
        timeout=10)
    assert r.status_code in (401, 403)
