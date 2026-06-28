"""TRACK 16.15 · Operational Cleanup Companion regression."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_cleanup_companion.py"
ROUTE = BACKEND / "routes" / "transportation_intelligence.py"
FE_INTEL = ROOT / "frontend" / "src" / "pages" / "transportation" / "_intelligence.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---- fake DB (same pattern as Track 16.14) -------------------------------
def _matches(row, q):
    for k, v in (q or {}).items():
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if isinstance(v, dict) and "$gte" in v:
            if (row.get(k) or "") < v["$gte"]:
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Cur:
    def __init__(self, items): self._items = list(items)
    def sort(self, *_, **__): return self
    def limit(self, _): return self
    async def to_list(self, _=None): return list(self._items)


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []
    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])
    async def find_one(self, q=None, *_, **kwargs):
        rows = [r for r in self.rows if _matches(r, q or {})]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            rows.sort(key=lambda r: r.get(key) or "", reverse=direction == -1)
        return rows[0] if rows else None
    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"_id_{len(self.rows)}"
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()


class _DB:
    def __init__(self): self._c: Dict[str, _Coll] = {}
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._c:
            self._c[name] = _Coll()
        return self._c[name]
    def __getitem__(self, k): return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _seed_insurance_doc(db, days_until_expiry=10, person="tp-1"):
    exp = (datetime.now(timezone.utc) + timedelta(days=days_until_expiry)).isoformat()
    db.driver_documents.rows.append({
        "id": f"doc-{len(db.driver_documents.rows)}",
        "tenant": "masci",
        "transport_person_id": person,
        "document_type": "Insurance Certificate",
        "expires_at": exp,
    })


def _seed_truck_overdue(db, tid="t-1"):
    db.transport_trucks.rows.append({
        "id": tid, "tenant": "masci", "truck_number": "T-100",
        "status": "active",
    })
    past = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    db.transport_truck_inspections.rows.append({
        "id": f"i-{tid}", "tenant": "masci",
        "transport_truck_id": tid, "result": "ready",
        "inspected_at": past,
    })


# ===========================================================================
# 1 — Lib exists
# ===========================================================================
def test_01_lib_exists():
    assert LIB.exists()


# ===========================================================================
# 2 / 3 / 4 — Public functions present
# ===========================================================================
def test_02_build_signals_exists():
    src = LIB.read_text()
    assert "async def build_cleanup_signals" in src


def test_03_build_signal_detail_exists():
    src = LIB.read_text()
    assert "async def build_cleanup_signal_detail" in src


def test_04_materialize_exists():
    src = LIB.read_text()
    assert "async def materialize_cleanup_actions" in src


# ===========================================================================
# 5 — No new scoring functions introduced
# ===========================================================================
def test_05_no_new_scoring():
    src = LIB.read_text()
    for forbidden in (
        "def compute_driver_intelligence",
        "def compute_carrier_intelligence",
        "def compute_truck_intelligence",
        "def composite(",
        "def grade(",
        "compute_score",
    ):
        assert forbidden not in src


# ===========================================================================
# 6 — Uses existing intelligence/learning/automation collections
# ===========================================================================
def test_06_reads_existing_collections():
    src = LIB.read_text()
    # Reads existing collections.
    for coll in (
        "transport_persons", "transport_trucks", "carriers",
        "transport_certificates", "transport_truck_inspections",
        "transport_eligibility_state", "transport_carrier_packets",
        "driver_documents",
    ):
        assert coll in src
    # And delegates to existing learning builders.
    assert "build_common_watch_items" in src
    assert "build_excluded_reason_patterns" in src


# ===========================================================================
# 7 — Schema version is 16.15.0
# ===========================================================================
def test_07_schema_version():
    from lib.transport_cleanup_companion import SCHEMA_VERSION
    assert SCHEMA_VERSION == "16.15.0"


# ===========================================================================
# 8 — Signal output includes source_count
# ===========================================================================
def test_08_signal_includes_source_count():
    from lib.transport_cleanup_companion import build_cleanup_signals
    db = _DB()
    _seed_insurance_doc(db)
    out = _run(build_cleanup_signals(db))
    assert out["signals"]
    s = out["signals"][0]
    assert "source_count" in s
    assert s["source_count"] >= 1


# ===========================================================================
# 9 — Signal output includes recommended_action
# ===========================================================================
def test_09_signal_recommended_action():
    from lib.transport_cleanup_companion import build_cleanup_signals
    db = _DB()
    _seed_insurance_doc(db)
    out = _run(build_cleanup_signals(db))
    assert out["signals"][0]["recommended_action"]


# ===========================================================================
# 10 — Detail records include direct_link
# ===========================================================================
def test_10_detail_includes_direct_link():
    from lib.transport_cleanup_companion import build_cleanup_signal_detail
    db = _DB()
    _seed_insurance_doc(db)
    out = _run(build_cleanup_signal_detail(db, "insurance_expiring_soon"))
    assert out["ok"]
    assert out["affected"]
    assert out["affected"][0]["direct_link"]


# ===========================================================================
# 11 — Materialize creates action items
# ===========================================================================
def test_11_materialize_creates_actions():
    from lib.transport_cleanup_companion import materialize_cleanup_actions
    db = _DB()
    _seed_insurance_doc(db)
    out = _run(materialize_cleanup_actions(db, "insurance_expiring_soon"))
    assert out["created"] >= 1
    assert len(db.transport_action_items.rows) >= 1


# ===========================================================================
# 12 — Materialize dedupes by event_key
# ===========================================================================
def test_12_materialize_dedupes():
    from lib.transport_cleanup_companion import materialize_cleanup_actions
    db = _DB()
    _seed_insurance_doc(db)
    _run(materialize_cleanup_actions(db, "insurance_expiring_soon"))
    out2 = _run(materialize_cleanup_actions(db, "insurance_expiring_soon"))
    assert out2["created"] == 0
    assert out2["skipped_duplicates"] >= 1


# ===========================================================================
# 13 — Materialize does not mutate source records
# ===========================================================================
def test_13_no_source_mutation():
    from lib.transport_cleanup_companion import materialize_cleanup_actions
    db = _DB()
    _seed_insurance_doc(db)
    snapshot = {k: v for k, v in db.driver_documents.rows[0].items()
                 if k != "_id"}
    _run(materialize_cleanup_actions(db, "insurance_expiring_soon"))
    after = {k: v for k, v in db.driver_documents.rows[0].items()
              if k != "_id"}
    assert snapshot == after


# ===========================================================================
# 14 — Created actions carry source=intelligence_cleanup
# ===========================================================================
def test_14_source_is_intelligence_cleanup():
    from lib.transport_cleanup_companion import materialize_cleanup_actions
    db = _DB()
    _seed_insurance_doc(db)
    _run(materialize_cleanup_actions(db, "insurance_expiring_soon"))
    row = db.transport_action_items.rows[0]
    assert row["source"] == "intelligence_cleanup"
    assert row["related_event_key"].startswith("cleanup::")
    assert row["related_signal_key"] == "insurance_expiring_soon"


# ===========================================================================
# 15 — Audit on materialize
# ===========================================================================
def test_15_audit_on_materialize():
    from lib.transport_cleanup_companion import materialize_cleanup_actions
    db = _DB()
    _seed_insurance_doc(db)
    _run(materialize_cleanup_actions(db, "insurance_expiring_soon",
                                       actor="admin@masci"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "transport_cleanup_actions_materialized" in kinds


# ===========================================================================
# 16 — Audit on view (signal list)
# ===========================================================================
def test_16_audit_on_signal_view():
    from lib.transport_cleanup_companion import record_cleanup_view
    db = _DB()
    _run(record_cleanup_view(
        db, kind="transport_cleanup_signal_viewed",
        viewer_role="admin"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "transport_cleanup_signal_viewed" in kinds


# ===========================================================================
# 17 — Audit on detail view
# ===========================================================================
def test_17_audit_on_detail_view():
    from lib.transport_cleanup_companion import record_cleanup_view
    db = _DB()
    _run(record_cleanup_view(
        db, kind="transport_cleanup_detail_viewed",
        signal_key="insurance_expiring_soon", viewer_role="admin"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "transport_cleanup_detail_viewed" in kinds


# ===========================================================================
# 18 / 19 / 20 — API endpoints exist
# ===========================================================================
def test_18_api_signals_endpoint():
    src = ROUTE.read_text()
    assert '"/cleanup-signals"' in src


def test_19_api_detail_endpoint():
    src = ROUTE.read_text()
    assert '"/cleanup-signals/{signal_key}"' in src


def test_20_api_materialize_endpoint():
    src = ROUTE.read_text()
    assert '/cleanup-signals/{signal_key}/materialize-actions' in src


# ===========================================================================
# 21 — Endpoints are admin-gated
# ===========================================================================
def test_21_endpoints_admin_gated():
    """Cleanup endpoints must be auth-gated.

    TRACK 18.12C reclassified the read endpoints
    (`/cleanup-signals` and `/cleanup-signals/{key}`) as Class B
    (dispatcher-read-only summary) so the Mission Control Cleanup card
    can load for dispatchers. Both now route through the `ops_guard`
    alias (`require_dispatch_or_admin_dep or require_admin_dep`). The
    materialize POST stays strict-admin via `require_admin_dep`. This
    regression accepts either dep on the read endpoints; the write
    endpoint must remain admin-strict.
    """
    src = ROUTE.read_text()
    idx_block = src.find("# TRACK 16.15")
    block = src[idx_block:idx_block + 3500] if idx_block > 0 else ""
    # Read endpoints accept ops_guard (which falls back to admin-strict)
    # OR direct admin gate.
    total = (
        block.count("Depends(require_admin_dep)")
        + block.count("Depends(ops_guard)")
    )
    assert total >= 3, (
        f"cleanup endpoints must be auth-gated; found {total} guards "
        f"(expected 3: 2 GETs + 1 POST)")
    # The materialize POST must remain admin-strict.
    mat_idx = block.find("/cleanup-signals/{signal_key}/materialize-actions")
    assert mat_idx >= 0
    mat_window = block[mat_idx:mat_idx + 500]
    assert "Depends(require_admin_dep)" in mat_window, (
        "cleanup materialize POST must remain admin-strict")


# ===========================================================================
# 22 — Anonymous blocked / 23 — Dispatch token blocked from materialize
# ===========================================================================
def test_22_anonymous_blocked():
    """Both gating paths rely on the shared admin dep — same gate as
    Track 16.14 (proven there). We assert the contract here."""
    src = ROUTE.read_text()
    # No dispatch_or_admin reference inside the cleanup block.
    idx = src.find("# TRACK 16.15")
    block = src[idx:idx + 3500]
    assert "require_dispatch_or_admin" not in block


def test_23_dispatch_blocked_from_materialize():
    src = ROUTE.read_text()
    idx = src.find("materialize-actions")
    handler = src[max(0, idx - 100): idx + 600]
    assert "Depends(require_admin_dep)" in handler


# ===========================================================================
# 24 — UI Cleanup Companion tab exists
# ===========================================================================
def test_24_ui_cleanup_tab():
    src = FE_INTEL.read_text()
    assert "tx-intel-tab-cleanup" in src
    assert "Cleanup Companion" in src
    assert "CleanupCompanionPanel" in src


# ===========================================================================
# 25 — Top Cleanup Signal Card exists
# ===========================================================================
def test_25_ui_top_card():
    src = FE_INTEL.read_text()
    assert "tx-intel-cleanup-top-card" in src
    assert "tx-intel-cleanup-top-title" in src


# ===========================================================================
# 26 — Affected Records Drawer exists
# ===========================================================================
def test_26_ui_affected_drawer():
    src = FE_INTEL.read_text()
    assert "tx-intel-cleanup-affected-drawer" in src
    assert "tx-intel-cleanup-detail-title" in src


# ===========================================================================
# 27 — Create cleanup actions button exists
# ===========================================================================
def test_27_ui_materialize_button():
    src = FE_INTEL.read_text()
    assert "tx-intel-cleanup-materialize-btn" in src
    assert "Create cleanup actions" in src


# ===========================================================================
# 28 — Empty state handled
# ===========================================================================
def test_28_empty_state():
    src = FE_INTEL.read_text()
    assert "tx-intel-cleanup-empty" in src
    from lib.transport_cleanup_companion import build_cleanup_signals
    db = _DB()
    out = _run(build_cleanup_signals(db))
    assert out["signals"] == []


# ===========================================================================
# 29 — Command Queue integration uses transport_action_items
# ===========================================================================
def test_29_uses_transport_action_items():
    src = LIB.read_text()
    assert "db.transport_action_items.insert_one" in src
    # Action rows use the existing schema fields the Command Queue
    # already understands.
    assert '"action_type"' in src
    assert '"severity"' in src
    assert '"status": "open"' in src


# ===========================================================================
# 30 — No emails added in this track
# ===========================================================================
def test_30_no_emails():
    src = LIB.read_text()
    for forbidden in ("smtp", "sendgrid", "send_email", "send_mail",
                       "MIMEMultipart"):
        assert forbidden.lower() not in src.lower()


# ===========================================================================
# 31 — No SMS / Twilio / push
# ===========================================================================
def test_31_no_sms_or_push():
    for p in (LIB, FE_INTEL):
        src = p.read_text()
        for forbidden in ("twilio", "TWILIO", "sendSms",
                           "push_notification", "fcm.googleapis"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 32 — No punitive labels
# ===========================================================================
def test_32_no_punitive_labels():
    for p in (LIB, FE_INTEL):
        src = p.read_text()
        for forbidden in ("Rejected", "Denied", "Failed —",
                           "rejected!", "denied!", "bad dispatcher"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 33 — No dispatch assignment behavior changes
# ===========================================================================
def test_33_no_dispatch_assignment_changes():
    src = LIB.read_text()
    for forbidden in ("dispatch_lifecycle", "transport_dispatch_gate",
                       "block_envelope"):
        assert forbidden not in src


# ===========================================================================
# 34 — No HR behavior changes
# ===========================================================================
def test_34_no_hr_changes():
    src = LIB.read_text()
    for forbidden in ("db.employees.update_one", "db.employees.insert_one",
                       "db.employees.delete_many"):
        assert forbidden not in src


# ===========================================================================
# 35 — Track 16.14 tests still wired
# ===========================================================================
def test_35_track_16_14_preserved():
    src = GATE.read_text()
    assert "test_track_16_14_dispatcher_learning_loop" in src


# ===========================================================================
# 36 — Deployment gate includes Track 16.15 tests
# ===========================================================================
def test_36_gate_includes_track_16_15():
    src = GATE.read_text()
    assert "test_track_16_15_operational_cleanup_companion" in src


# ===========================================================================
# 37 — Multiple signals surfaced from different sources
# ===========================================================================
def test_37_multiple_signals_surfaced():
    from lib.transport_cleanup_companion import build_cleanup_signals
    db = _DB()
    _seed_insurance_doc(db)
    _seed_truck_overdue(db)
    out = _run(build_cleanup_signals(db))
    keys = {s["signal_key"] for s in out["signals"]}
    assert "insurance_expiring_soon" in keys
    assert "inspection_overdue" in keys


# ===========================================================================
# 38 — Unknown signal returns ok=false
# ===========================================================================
def test_38_unknown_signal_returns_error():
    from lib.transport_cleanup_companion import (
        build_cleanup_signal_detail, materialize_cleanup_actions,
    )
    db = _DB()
    a = _run(build_cleanup_signal_detail(db, "does_not_exist"))
    assert a["ok"] is False
    b = _run(materialize_cleanup_actions(db, "does_not_exist"))
    assert b["ok"] is False


# ===========================================================================
# 39 — Range cap honoured by builders
# ===========================================================================
def test_39_range_cap_honoured():
    from lib.transport_cleanup_companion import build_cleanup_signals
    db = _DB()
    out = _run(build_cleanup_signals(db, days=99999))
    assert out["range"]["days"] == 365


# ===========================================================================
# 40 — Hr_sync_mismatch picks up needs_correction projections
# ===========================================================================
def test_40_hr_sync_mismatch_signal():
    from lib.transport_cleanup_companion import build_cleanup_signal_detail
    db = _DB()
    db.transport_persons.rows.append({
        "id": "tp-1", "tenant": "masci", "kind": "masci_employee",
        "employee_id": "E1", "first_name": "Jane", "last_name": "Driver",
        "status": "active",
        "hr_projection": {"transport_state": "needs_correction",
                            "reason_labels": ["HR linkage missing"]},
    })
    out = _run(build_cleanup_signal_detail(db, "hr_sync_mismatch"))
    assert out["ok"]
    assert any(it["entity_id"] == "tp-1" for it in out["affected"])
