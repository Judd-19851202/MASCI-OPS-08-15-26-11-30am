"""TRACK 16.14 · Dispatcher Learning Loop regression."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_dispatch_learning.py"
ROUTE = BACKEND / "routes" / "transportation_intelligence.py"
FE_INTEL = ROOT / "frontend" / "src" / "pages" / "transportation" / "_intelligence.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---- fake DB --------------------------------------------------------------
def _matches(row: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in (q or {}).items():
        if isinstance(v, dict) and "$gte" in v:
            if (row.get(k) or "") < v["$gte"]:
                return False
            if "$lte" in v and (row.get(k) or "") > v["$lte"]:
                return False
            continue
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
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


def _ts(days_ago=0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _seed_audit(db, kind: str, days_ago: int = 0, **payload):
    db.transport_dispatch_recommendation_audit.rows.append({
        "tenant": "masci", "kind": kind, "ts": _ts(days_ago),
        "payload": payload,
    })


# ===========================================================================
# 1 — Lib exists
# ===========================================================================
def test_01_lib_exists():
    assert LIB.exists()


# ===========================================================================
# 2 — Public functions present
# ===========================================================================
def test_02_function_surface():
    src = LIB.read_text()
    for fn in (
        "build_dispatch_learning_summary",
        "build_recommendation_adoption_trends",
        "build_common_alternative_reasons",
        "build_common_watch_items",
        "build_excluded_reason_patterns",
        "build_engine_tuning_signals",
    ):
        assert f"async def {fn}" in src


# ===========================================================================
# 3 — Summary uses the recommendation audit collection
# ===========================================================================
def test_03_summary_uses_audit_collection():
    src = LIB.read_text()
    assert "transport_dispatch_recommendation_audit" in src


# ===========================================================================
# 4 — Library is read-only against business collections
# ===========================================================================
def test_04_read_only_no_writes_to_business():
    src = LIB.read_text()
    # Never write to recommendation audit / employees / drivers / etc.
    for forbidden in (
        "db.transport_dispatch_recommendation_audit.update_one",
        "db.transport_dispatch_recommendation_audit.delete_many",
        "db.transport_dispatch_recommendation_audit.insert_one",
        "db.employees.",
        "db.transport_persons.update_one",
        "db.transport_persons.insert_one",
    ):
        assert forbidden not in src


# ===========================================================================
# 5 — API endpoint exists
# ===========================================================================
def test_05_api_endpoint_present():
    src = ROUTE.read_text()
    assert "/dispatch-learning" in src


# ===========================================================================
# 6 — Endpoint is GET-only
# ===========================================================================
def test_06_endpoint_get_only():
    src = ROUTE.read_text()
    # The dispatch-learning handler is a @router.get.
    idx = src.find("/dispatch-learning")
    prefix = src[max(0, idx - 200):idx]
    assert "@router.get(" in prefix


# ===========================================================================
# 7 — Endpoint is admin-gated
# ===========================================================================
def test_07_endpoint_admin_gated():
    src = ROUTE.read_text()
    idx = src.find('"/dispatch-learning"')
    # Find handler and ensure require_admin_dep is Depended in its signature.
    handler = src[idx:idx + 600]
    assert "Depends(require_admin_dep)" in handler


# ===========================================================================
# 8 — Default days = 30
# ===========================================================================
def test_08_default_days_thirty():
    src = ROUTE.read_text()
    assert "days: int = Query(30" in src


# ===========================================================================
# 9 — Max days capped at 365
# ===========================================================================
def test_09_max_days_capped():
    src = ROUTE.read_text()
    assert "le=365" in src


# ===========================================================================
# 10 — Schema version 16.14.0
# ===========================================================================
def test_10_schema_version():
    from lib.transport_dispatch_learning import SCHEMA_VERSION
    assert SCHEMA_VERSION == "16.14.0"


# ===========================================================================
# 11 — Summary counts the right kinds
# ===========================================================================
def test_11_summary_counts():
    from lib.transport_dispatch_learning import build_dispatch_learning_summary
    db = _DB()
    for k in (
        "transport_dispatch_recommendation_generated",
        "transport_dispatch_recommendation_viewed",
        "transport_dispatch_recommendation_selected",
        "transport_dispatch_non_recommended_selected",
        "transport_dispatch_recommendation_ignored",
        "transport_dispatch_recommendation_failed",
    ):
        _seed_audit(db, k, days_ago=1)
    out = _run(build_dispatch_learning_summary(db))
    s = out["summary"]
    assert s["recommendations_generated"] == 1
    assert s["recommendations_viewed"] == 1
    assert s["recommended_selected"] == 1
    assert s["eligible_alternative_selected"] == 1
    assert s["ignored"] == 1
    assert s["recommendation_unavailable"] == 1


# ===========================================================================
# 12 — Adoption trend points
# ===========================================================================
def test_12_adoption_trend():
    from lib.transport_dispatch_learning import build_recommendation_adoption_trends
    db = _DB()
    _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=1)
    _seed_audit(db, "transport_dispatch_recommendation_selected", days_ago=1)
    _seed_audit(db, "transport_dispatch_non_recommended_selected", days_ago=1)
    out = _run(build_recommendation_adoption_trends(db, days=7))
    assert out["points"]
    p = out["points"][-1]
    assert p["generated"] == 1
    assert p["selected"] == 1
    assert p["non_recommended_selected"] == 1
    # Adoption pct = selected / (selected + alt) = 50.0
    assert p["adoption_pct"] == 50.0


# ===========================================================================
# 13 — Alternative reasons
# ===========================================================================
def test_13_alternative_reasons():
    from lib.transport_dispatch_learning import build_common_alternative_reasons
    db = _DB()
    _seed_audit(db, "transport_dispatch_non_recommended_selected", days_ago=2,
                note="operator preference")
    _seed_audit(db, "transport_dispatch_non_recommended_selected", days_ago=2,
                note="operator preference")
    _seed_audit(db, "transport_dispatch_non_recommended_selected", days_ago=2,
                note="closer truck")
    out = _run(build_common_alternative_reasons(db, days=7))
    labels = [p["label"] for p in out["patterns"]]
    assert "operator preference" in labels
    assert out["total_non_recommended_selections"] == 3


# ===========================================================================
# 14 — Watch item patterns
# ===========================================================================
def test_14_watch_items():
    from lib.transport_dispatch_learning import build_common_watch_items
    db = _DB()
    _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=2,
                recommendation_id="r1", watch=["Insurance expires in 14 days"])
    _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=2,
                recommendation_id="r2", watch=["Insurance expires in 14 days"])
    out = _run(build_common_watch_items(db, days=7))
    labels = [p["label"] for p in out["patterns"]]
    assert "Insurance expires in 14 days" in labels


# ===========================================================================
# 15 — Excluded reason patterns sourced from eligibility state
# ===========================================================================
def test_15_excluded_patterns():
    from lib.transport_dispatch_learning import build_excluded_reason_patterns
    db = _DB()
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "person", "target_id": "p1",
        "state": "not_dispatchable",
        "reasons": [{"code": "hr_status_terminated",
                      "label": "Employee is terminated in HR"}],
    })
    out = _run(build_excluded_reason_patterns(db, days=30))
    labels = [p["label"] for p in out["patterns"]]
    assert "Employee is terminated in HR" in labels


# ===========================================================================
# 16 — Engine tuning signals (frequent unavailable)
# ===========================================================================
def test_16_tuning_signal_unavailable():
    from lib.transport_dispatch_learning import build_engine_tuning_signals
    db = _DB()
    for _ in range(20):
        _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=1)
    for _ in range(3):
        _seed_audit(db, "transport_dispatch_recommendation_failed", days_ago=1)
    out = _run(build_engine_tuning_signals(db, days=7))
    codes = [s["code"] for s in out["signals"]]
    assert "frequent_recommendation_unavailable" in codes


# ===========================================================================
# 17 — Tuning signal: many ignored without view
# ===========================================================================
def test_17_tuning_signal_ignored():
    from lib.transport_dispatch_learning import build_engine_tuning_signals
    db = _DB()
    for _ in range(20):
        _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=1)
    for _ in range(7):
        _seed_audit(db, "transport_dispatch_recommendation_ignored", days_ago=1)
    out = _run(build_engine_tuning_signals(db, days=7))
    codes = [s["code"] for s in out["signals"]]
    assert "many_ignored_without_view" in codes


# ===========================================================================
# 18 — Tuning signal: frequent alternative selection
# ===========================================================================
def test_18_tuning_signal_alt():
    from lib.transport_dispatch_learning import build_engine_tuning_signals
    db = _DB()
    for _ in range(10):
        _seed_audit(db, "transport_dispatch_recommendation_selected", days_ago=1)
    for _ in range(10):
        _seed_audit(db, "transport_dispatch_non_recommended_selected", days_ago=1)
    out = _run(build_engine_tuning_signals(db, days=7))
    codes = [s["code"] for s in out["signals"]]
    assert "frequent_alternative_selection" in codes


# ===========================================================================
# 19 — Tuning signal: healthy explainability usage
# ===========================================================================
def test_19_tuning_signal_explainability():
    from lib.transport_dispatch_learning import build_engine_tuning_signals
    db = _DB()
    for _ in range(20):
        _seed_audit(db, "transport_dispatch_recommendation_generated", days_ago=1)
    for _ in range(15):
        _seed_audit(db, "transport_dispatch_recommendation_viewed", days_ago=1)
    out = _run(build_engine_tuning_signals(db, days=7))
    codes = [s["code"] for s in out["signals"]]
    assert "healthy_explainability_usage" in codes


# ===========================================================================
# 20 — Empty state handled
# ===========================================================================
def test_20_empty_state():
    from lib.transport_dispatch_learning import (
        build_dispatch_learning_summary, build_engine_tuning_signals,
    )
    db = _DB()
    out = _run(build_dispatch_learning_summary(db))
    assert out["summary"]["recommendations_generated"] == 0
    out2 = _run(build_engine_tuning_signals(db))
    assert out2["signals"] == []


# ===========================================================================
# 21 — Audit event recorded on view
# ===========================================================================
def test_21_view_audit_event():
    from lib.transport_dispatch_learning import record_learning_view
    db = _DB()
    _run(record_learning_view(
        db, viewer_role="admin", viewer_id="u1",
        range_info={"days": 30}, summary_counts={"generated": 0}))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "transport_dispatch_learning_viewed" in kinds


# ===========================================================================
# 22 — No per-dispatcher ranking anywhere in the lib
# ===========================================================================
def test_22_no_per_dispatcher_ranking():
    src = LIB.read_text()
    for forbidden in (
        "dispatcher_rank", "per_dispatcher", "dispatcher_score",
        "dispatcher_ranking", "individual_score", "leaderboard",
    ):
        assert forbidden not in src, f"per-dispatcher token leaked: {forbidden}"


# ===========================================================================
# 23 — No individual-performance vocabulary in user-facing strings
# ===========================================================================
def test_23_no_performance_vocab():
    for p in (LIB, FE_INTEL):
        src = p.read_text()
        for forbidden in (
            "performance review", "Performance Review",
            "poor performance", "bad dispatcher",
            "noncompliant dispatcher",
        ):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 24 — No emails added in this track
# ===========================================================================
def test_24_no_emails_added():
    src = LIB.read_text()
    for forbidden in ("smtp", "sendgrid", "send_email", "send_mail",
                       "MIMEMultipart"):
        assert forbidden not in src.lower() if forbidden.islower() else \
            forbidden not in src


# ===========================================================================
# 25 — No SMS / Twilio / push references
# ===========================================================================
def test_25_no_sms_or_push():
    for p in (LIB, FE_INTEL):
        src = p.read_text()
        for forbidden in ("twilio", "TWILIO", "sendSms",
                           "push_notification", "fcm.googleapis"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 26 — No recommendation scoring duplication
# ===========================================================================
def test_26_no_scoring_duplication():
    src = LIB.read_text()
    for forbidden in (
        "compute_driver_intelligence",
        "compute_carrier_intelligence",
        "compute_truck_intelligence",
        "recommend_drivers",
        "recommend_carriers",
        "recommend_trucks",
        "def composite",
        "def grade",
    ):
        assert forbidden not in src


# ===========================================================================
# 27 — No assignment gate changes (no dispatch lifecycle imports)
# ===========================================================================
def test_27_no_assignment_gate_changes():
    src = LIB.read_text()
    for forbidden in ("dispatch_lifecycle", "transport_dispatch_gate",
                       "block_envelope", "HTTPException(403"):
        assert forbidden not in src


# ===========================================================================
# 28 — No HR changes (no employees collection writes)
# ===========================================================================
def test_28_no_hr_changes():
    src = LIB.read_text()
    for forbidden in ("db.employees.update_one", "db.employees.insert_one",
                       "db.employees.delete_many"):
        assert forbidden not in src


# ===========================================================================
# 29 — UI Learning Loop tab exists
# ===========================================================================
def test_29_ui_learning_tab_exists():
    src = FE_INTEL.read_text()
    assert "tx-intel-tab-learning" in src
    assert "Learning Loop" in src
    assert "LearningLoopPanel" in src


# ===========================================================================
# 30 — UI Executive summary cards exist
# ===========================================================================
def test_30_ui_summary_cards():
    src = FE_INTEL.read_text()
    for tid in (
        "tx-intel-learning-summary",
        "tx-intel-learning-generated",
        "tx-intel-learning-viewed",
        "tx-intel-learning-selected",
        "tx-intel-learning-alt",
        "tx-intel-learning-ignored",
        "tx-intel-learning-unavailable",
    ):
        assert tid in src


# ===========================================================================
# 31 — UI Adoption trend section
# ===========================================================================
def test_31_ui_adoption_section():
    src = FE_INTEL.read_text()
    assert "tx-intel-learning-adoption" in src


# ===========================================================================
# 32 — UI Watch items section
# ===========================================================================
def test_32_ui_watch_section():
    src = FE_INTEL.read_text()
    assert "tx-intel-learning-watch" in src


# ===========================================================================
# 33 — UI Excluded patterns section
# ===========================================================================
def test_33_ui_excluded_section():
    src = FE_INTEL.read_text()
    assert "tx-intel-learning-excluded" in src


# ===========================================================================
# 34 — UI Tuning signals section
# ===========================================================================
def test_34_ui_tuning_section():
    src = FE_INTEL.read_text()
    assert "tx-intel-learning-tuning" in src


# ===========================================================================
# 35 — UI carries team-level disclaimer
# ===========================================================================
def test_35_ui_team_level_disclaimer():
    src = FE_INTEL.read_text()
    assert "tx-intel-learning-disclaimer" in src
    assert "no individual scorekeeping" in src.lower()


# ===========================================================================
# 36 — Forbidden punitive vocabulary not introduced
# ===========================================================================
def test_36_no_punitive_vocab():
    for p in (LIB, FE_INTEL):
        src = p.read_text()
        for forbidden in ("Rejected", "Denied", "Failed —",
                           "rejected!", "denied!", "bad dispatcher"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 37 — Track 16.13 tests still wired
# ===========================================================================
def test_37_track_16_13_preserved():
    src = GATE.read_text()
    assert "test_track_16_13_dispatch_decision_surface" in src


# ===========================================================================
# 38 — Deployment gate includes Track 16.14 tests
# ===========================================================================
def test_38_gate_includes_track_16_14():
    src = GATE.read_text()
    assert "test_track_16_14_dispatcher_learning_loop" in src


# ===========================================================================
# 39 — Range cap behaves: requesting 9999 days caps at 365
# ===========================================================================
def test_39_range_cap():
    from lib.transport_dispatch_learning import build_dispatch_learning_summary
    db = _DB()
    out = _run(build_dispatch_learning_summary(db, days=9999))
    assert out["range"]["days"] == 365


# ===========================================================================
# 40 — Range floor: requesting -5 days clamps to 1
# ===========================================================================
def test_40_range_floor():
    from lib.transport_dispatch_learning import build_dispatch_learning_summary
    db = _DB()
    out = _run(build_dispatch_learning_summary(db, days=-5))
    assert out["range"]["days"] == 1
