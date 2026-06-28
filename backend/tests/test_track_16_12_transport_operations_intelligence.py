"""TRACK 16.12 · Transportation Operations Intelligence regression."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

CORE = BACKEND / "lib" / "transport_intelligence_core.py"
DRV = BACKEND / "lib" / "transport_driver_intelligence.py"
CAR = BACKEND / "lib" / "transport_carrier_intelligence.py"
TRK = BACKEND / "lib" / "transport_truck_intelligence.py"
PRED = BACKEND / "lib" / "transport_prediction_engine.py"
REC = BACKEND / "lib" / "transport_recommendation_engine.py"
ORCH = BACKEND / "lib" / "transport_operations_intelligence.py"
ROUTE = BACKEND / "routes" / "transportation_intelligence.py"
FE_INTEL = ROOT / "frontend" / "src" / "pages" / "transportation" / "_intelligence.jsx"
FE_LISTS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_lists.jsx"
FE_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
FE_SHARED = ROOT / "frontend" / "src" / "pages" / "transportation" / "_shared.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---- minimal fake DB ------------------------------------------------------
def _matches(row: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in (q or {}).items():
        if k == "$or":
            if not any(_matches(row, sub) for sub in v):
                return False
            continue
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
    def sort(self, *args, **__):
        if args and isinstance(args[0], list) and args[0]:
            key, direction = args[0][0]
            self._items.sort(key=lambda r: r.get(key) or "",
                              reverse=direction == -1)
        elif args and isinstance(args[0], str):
            direction = args[1] if len(args) > 1 else 1
            self._items.sort(key=lambda r: r.get(args[0]) or "",
                              reverse=direction == -1)
        return self
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
            rows.sort(key=lambda r: r.get(key) or "",
                       reverse=direction == -1)
        return rows[0] if rows else None
    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"_id_{len(self.rows)}"
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()
    async def update_one(self, q, update, upsert=False):
        for r in self.rows:
            if _matches(r, q or {}):
                if "$set" in update:
                    r.update(update["$set"])
                return type("R", (), {"matched_count": 1})()
        if upsert:
            doc = dict((update or {}).get("$set", {}))
            doc.update((update or {}).get("$setOnInsert", {}))
            doc.update(q or {})
            await self.insert_one(doc)
        return type("R", (), {"matched_count": 0})()


class _DB:
    def __init__(self):
        self._c: Dict[str, _Coll] = {}
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


def _seed_driver(db, *, driver_id="tp-1", elig_state="eligible",
                  kind="masci_employee", carrier_id=None,
                  with_cert=True):
    db.transport_persons.rows.append({
        "_id": f"_id_{driver_id}", "id": driver_id, "tenant": "masci",
        "kind": kind, "employee_id": "E1",
        "carrier_id": carrier_id,
        "first_name": "Jane", "last_name": "Driver",
        "status": "active", "safety_hold": False,
    })
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "person",
        "target_id": driver_id, "state": elig_state, "reasons": [],
        "computed_at": "2026-02-09T12:00:00+00:00",
    })
    if with_cert:
        future = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()
        db.transport_certificates.rows.append({
            "id": f"cert-{driver_id}", "tenant": "masci",
            "transport_person_id": driver_id,
            "issued_at": "2026-01-01T00:00:00+00:00",
            "expires_at": future,
        })


def _seed_carrier(db, *, carrier_id="c-1", safety_hold=False,
                   packet_status="approved", rate_ack=True):
    db.carriers.rows.append({
        "_id": f"_id_{carrier_id}", "id": carrier_id, "tenant": "masci",
        "legal_name": "Big Hauler LLC", "carrier_type": "leased_hauler",
        "status": "active", "safety_hold": safety_hold,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
    })
    db.transport_carrier_packets.rows.append({
        "tenant": "masci", "carrier_id": carrier_id,
        "status": packet_status, "rate_acknowledged": rate_ack,
    })


def _seed_truck(db, *, truck_id="t-1", elig_state="eligible",
                 inspection_result="ready", safety_hold=False):
    db.transport_trucks.rows.append({
        "_id": f"_id_{truck_id}", "id": truck_id, "tenant": "masci",
        "truck_number": "T-100", "ownership": "leased_carrier",
        "truck_type": "dump_truck", "status": "active",
        "safety_hold": safety_hold,
    })
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "truck",
        "target_id": truck_id, "state": elig_state, "reasons": [],
        "computed_at": "2026-02-09T12:00:00+00:00",
    })
    if inspection_result:
        db.transport_truck_inspections.rows.append({
            "id": f"insp-{truck_id}", "tenant": "masci",
            "transport_truck_id": truck_id,
            "inspected_at": "2026-02-01T00:00:00+00:00",
            "result": inspection_result,
        })


# ===========================================================================
# 1 — Static contract locks
# ===========================================================================
def test_01_core_exists():
    assert CORE.exists()


def test_02_engine_files_present():
    for p in (DRV, CAR, TRK, PRED, REC, ORCH, ROUTE):
        assert p.exists(), p


def test_03_core_pure_helpers():
    from lib.transport_intelligence_core import (
        clamp, grade, composite, derive_band, parse_iso, days_until,
    )
    assert clamp(150) == 100 and clamp(-1) == 0
    assert grade(95) == "excellent" and grade(10) == "critical"
    assert composite([{"score": 80, "weight": 1},
                       {"score": 100, "weight": 1}]) == 90.0
    assert derive_band(85)["grade"] == "strong"
    assert parse_iso("not-a-date") is None
    assert days_until(None) is None


def test_04_make_explanation_shape():
    from lib.transport_intelligence_core import make_explanation
    e = make_explanation(code="x", label="L", impact="positive",
                         weight=1, delta=5)
    for key in ("code", "label", "impact", "weight", "delta", "at"):
        assert key in e


def test_05_audit_helper_never_raises():
    from lib.transport_intelligence_core import write_intelligence_audit
    db = _DB()
    _run(write_intelligence_audit(db, kind="x", subject_type="s",
                                    subject_id="z", snapshot={"a": 1}))
    assert len(db.transport_intelligence_audit.rows) == 1


# ===========================================================================
# 6–15 — Driver intelligence
# ===========================================================================
def test_06_driver_intelligence_basic():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    out = _run(compute_driver_intelligence(db, "tp-1"))
    assert out["driver_id"] == "tp-1"
    assert out["overall"]["score"] > 0
    assert out["indices"]["compliance"]["score"] > 0


def test_07_driver_not_found():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    out = _run(compute_driver_intelligence(_DB(), "missing"))
    assert out.get("ok") is False


def test_08_driver_eligibility_flows_into_compliance():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db, elig_state="not_dispatchable")
    out = _run(compute_driver_intelligence(db, "tp-1"))
    assert out["indices"]["compliance"]["score"] < 60


def test_09_driver_safety_hold_penalty():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    db.transport_persons.rows[0]["safety_hold"] = True
    out = _run(compute_driver_intelligence(db, "tp-1"))
    assert any("safety_hold" in e["code"] for e in out["explanations"])
    assert out["indices"]["safety"]["score"] < 100


def test_10_driver_explanations_always_present():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    out = _run(compute_driver_intelligence(db, "tp-1"))
    assert len(out["explanations"]) > 0


def test_11_driver_audit_written():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    _run(compute_driver_intelligence(db, "tp-1"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "driver_intelligence_refresh" in kinds


def test_12_driver_no_audit_when_disabled():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    _run(compute_driver_intelligence(db, "tp-1", persist_audit=False))
    assert db.transport_intelligence_audit.rows == []


def test_13_driver_deterministic_repeat():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    a = _run(compute_driver_intelligence(db, "tp-1", persist_audit=False))
    b = _run(compute_driver_intelligence(db, "tp-1", persist_audit=False))
    assert a["overall"] == b["overall"]
    assert a["indices"] == b["indices"]


def test_14_driver_list_filter():
    from lib.transport_driver_intelligence import list_driver_intelligence
    db = _DB()
    _seed_driver(db, driver_id="tp-1", elig_state="eligible")
    _seed_driver(db, driver_id="tp-2", elig_state="not_dispatchable")
    out = _run(list_driver_intelligence(db, state="eligible"))
    assert {x["driver_id"] for x in out} == {"tp-1"}


def test_15_driver_does_not_mutate_records():
    from lib.transport_driver_intelligence import compute_driver_intelligence
    db = _DB()
    _seed_driver(db)
    snap_before = {k: v for k, v in db.transport_persons.rows[0].items()
                    if k != "_id"}
    _run(compute_driver_intelligence(db, "tp-1"))
    snap_after = {k: v for k, v in db.transport_persons.rows[0].items()
                   if k != "_id"}
    assert snap_before == snap_after


# ===========================================================================
# 16–25 — Carrier intelligence
# ===========================================================================
def test_16_carrier_basic():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    out = _run(compute_carrier_intelligence(db, "c-1"))
    assert out["carrier_id"] == "c-1"
    assert out["overall"]["score"] > 0


def test_17_carrier_not_found():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    out = _run(compute_carrier_intelligence(_DB(), "missing"))
    assert out.get("ok") is False


def test_18_carrier_safety_hold_penalty():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db, safety_hold=True)
    out = _run(compute_carrier_intelligence(db, "c-1"))
    assert out["indices"]["safety"]["score"] < 100


def test_19_carrier_packet_missing():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db, packet_status="pending_review", rate_ack=False)
    out = _run(compute_carrier_intelligence(db, "c-1"))
    assert out["indices"]["compliance"]["score"] < 100


def test_20_carrier_preferred_status_high():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    _seed_driver(db, carrier_id="c-1", driver_id="tp-c1")
    _seed_truck(db, truck_id="t-c1")
    db.transport_trucks.rows[0]["carrier_id"] = "c-1"
    out = _run(compute_carrier_intelligence(db, "c-1"))
    # 5 sub-scores: high compliance + safety + reliability + experience
    assert out["overall"]["score"] >= 70


def test_21_carrier_audit_written():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    _run(compute_carrier_intelligence(db, "c-1"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "carrier_intelligence_refresh" in kinds


def test_22_carrier_list_returns_all():
    from lib.transport_carrier_intelligence import list_carrier_intelligence
    db = _DB()
    _seed_carrier(db, carrier_id="c-1")
    _seed_carrier(db, carrier_id="c-2")
    out = _run(list_carrier_intelligence(db))
    assert {c["carrier_id"] for c in out} == {"c-1", "c-2"}


def test_23_carrier_does_not_mutate_records():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    snap = {k: v for k, v in db.carriers.rows[0].items() if k != "_id"}
    _run(compute_carrier_intelligence(db, "c-1"))
    after = {k: v for k, v in db.carriers.rows[0].items() if k != "_id"}
    assert snap == after


def test_24_carrier_indices_named_correctly():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    out = _run(compute_carrier_intelligence(db, "c-1"))
    for k in ("compliance", "safety", "reliability", "experience"):
        assert k in out["indices"]


def test_25_carrier_fleet_signals():
    from lib.transport_carrier_intelligence import compute_carrier_intelligence
    db = _DB()
    _seed_carrier(db)
    _seed_driver(db, carrier_id="c-1", driver_id="tp-c1")
    out = _run(compute_carrier_intelligence(db, "c-1"))
    assert out["fleet"]["total_drivers"] == 1


# ===========================================================================
# 26–32 — Truck intelligence
# ===========================================================================
def test_26_truck_basic():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db)
    out = _run(compute_truck_intelligence(db, "t-1"))
    assert out["truck_id"] == "t-1"
    assert out["overall"]["score"] > 0


def test_27_truck_not_found():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    out = _run(compute_truck_intelligence(_DB(), "missing"))
    assert out.get("ok") is False


def test_28_truck_safety_hold_penalty():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db, safety_hold=True)
    out = _run(compute_truck_intelligence(db, "t-1"))
    assert out["indices"]["mechanical_readiness"]["score"] < 100


def test_29_truck_inspection_missing():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db, inspection_result=None)
    out = _run(compute_truck_intelligence(db, "t-1"))
    assert any(e["code"] == "inspection_missing"
               for e in out["explanations"])


def test_30_truck_inspection_not_ready():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db, inspection_result="not_ready")
    out = _run(compute_truck_intelligence(db, "t-1"))
    assert out["indices"]["mechanical_readiness"]["score"] < 70


def test_31_truck_audit_written():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db)
    _run(compute_truck_intelligence(db, "t-1"))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "truck_intelligence_refresh" in kinds


def test_32_truck_does_not_mutate_records():
    from lib.transport_truck_intelligence import compute_truck_intelligence
    db = _DB()
    _seed_truck(db)
    snap = {k: v for k, v in db.transport_trucks.rows[0].items() if k != "_id"}
    _run(compute_truck_intelligence(db, "t-1"))
    after = {k: v for k, v in db.transport_trucks.rows[0].items() if k != "_id"}
    assert snap == after


# ===========================================================================
# 33–40 — Recommendation engine
# ===========================================================================
def test_33_recommend_drivers_eligible_only():
    from lib.transport_recommendation_engine import recommend_drivers
    db = _DB()
    _seed_driver(db, driver_id="tp-1", elig_state="eligible")
    _seed_driver(db, driver_id="tp-2", elig_state="not_dispatchable")
    out = _run(recommend_drivers(db))
    ids = {x["driver_id"] for x in out["items"]}
    assert "tp-1" in ids and "tp-2" not in ids


def test_34_recommend_drivers_carries_why():
    from lib.transport_recommendation_engine import recommend_drivers
    db = _DB()
    _seed_driver(db)
    out = _run(recommend_drivers(db))
    assert out["items"][0]["why"]


def test_35_recommend_carriers_basic():
    from lib.transport_recommendation_engine import recommend_carriers
    db = _DB()
    _seed_carrier(db)
    out = _run(recommend_carriers(db))
    assert out["items"][0]["carrier_id"] == "c-1"


def test_36_recommend_trucks_filter_by_carrier():
    from lib.transport_recommendation_engine import recommend_trucks
    db = _DB()
    _seed_truck(db, truck_id="t-1")
    db.transport_trucks.rows[0]["carrier_id"] = "c-1"
    out = _run(recommend_trucks(db, carrier_id="c-1"))
    assert {x["truck_id"] for x in out["items"]} == {"t-1"}


def test_37_recommend_trucks_filter_by_type():
    from lib.transport_recommendation_engine import recommend_trucks
    db = _DB()
    _seed_truck(db, truck_id="t-1")
    db.transport_trucks.rows[0]["truck_type"] = "dump_truck"
    out = _run(recommend_trucks(db, truck_type="lowboy"))
    assert out["items"] == []


def test_38_recommend_triple():
    from lib.transport_recommendation_engine import recommend_dispatch_triple
    db = _DB()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    out = _run(recommend_dispatch_triple(db))
    assert out["driver"] and out["truck"] and out["carrier"]


def test_39_recommend_audit_written():
    from lib.transport_recommendation_engine import recommend_drivers
    db = _DB()
    _seed_driver(db)
    _run(recommend_drivers(db))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "driver_recommendations_generated" in kinds


def test_40_recommend_deterministic():
    from lib.transport_recommendation_engine import recommend_drivers
    db = _DB()
    _seed_driver(db)
    a = _run(recommend_drivers(db))
    b = _run(recommend_drivers(db))
    assert [x["driver_id"] for x in a["items"]] == [x["driver_id"] for x in b["items"]]


# ===========================================================================
# 41–46 — Prediction engine
# ===========================================================================
def test_41_predictions_shape():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    out = _run(compute_predictions(db))
    for k in ("documentation_expirations", "inspection_expirations",
               "orientation_renewals", "carrier_risk", "by_bucket"):
        assert k in out


def test_42_predictions_doc_expiring_soon_bucketed():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    soon = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    db.driver_documents.rows.append({
        "id": "d1", "tenant": "masci", "transport_person_id": "tp-1",
        "document_type": "cdl", "expires_at": soon,
    })
    out = _run(compute_predictions(db))
    assert out["by_bucket"].get("due_this_week") == 1


def test_43_predictions_overdue_bucket():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    db.driver_documents.rows.append({
        "id": "d1", "tenant": "masci", "transport_person_id": "tp-1",
        "document_type": "cdl", "expires_at": past,
    })
    out = _run(compute_predictions(db))
    assert out["by_bucket"].get("overdue") == 1


def test_44_predictions_carrier_risk_classified():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    _seed_carrier(db)
    db.transport_action_items.rows.append({
        "tenant": "masci", "status": "open", "severity": "critical",
        "entity_id": "c-1", "entity_type": "carrier",
    })
    out = _run(compute_predictions(db))
    risks = {r["subject_id"]: r["risk"] for r in out["carrier_risk"]}
    assert risks["c-1"] == "high"


def test_45_predictions_audit_written():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    _run(compute_predictions(db))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "predictions_refresh" in kinds


def test_46_predictions_deterministic():
    from lib.transport_prediction_engine import compute_predictions
    db = _DB()
    a = _run(compute_predictions(db))
    b = _run(compute_predictions(db))
    assert a["summary"] == b["summary"]


# ===========================================================================
# 47–52 — Executive orchestrator
# ===========================================================================
def test_47_dashboard_shape():
    from lib.transport_operations_intelligence import build_executive_dashboard
    db = _DB()
    out = _run(build_executive_dashboard(db))
    for k in ("transportation_health", "driver_health", "carrier_health",
               "truck_health", "dispatch_readiness", "capacity",
               "top_performers", "attention_required", "trends"):
        assert k in out


def test_48_dashboard_capacity():
    from lib.transport_operations_intelligence import build_executive_dashboard
    db = _DB()
    _seed_driver(db)
    _seed_truck(db)
    out = _run(build_executive_dashboard(db))
    assert out["capacity"]["drivers"]["total"] == 1
    assert out["capacity"]["trucks"]["total"] == 1


def test_49_dashboard_audit_written():
    from lib.transport_operations_intelligence import build_executive_dashboard
    db = _DB()
    _run(build_executive_dashboard(db))
    kinds = [r.get("kind") for r in db.transport_intelligence_audit.rows]
    assert "executive_dashboard_generated" in kinds


def test_50_operational_health_thin():
    from lib.transport_operations_intelligence import build_operational_health
    out = _run(build_operational_health(_DB()))
    assert "transportation_health" in out
    assert "schema_version" in out


def test_51_dashboard_top_attention_lists():
    from lib.transport_operations_intelligence import build_executive_dashboard
    db = _DB()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    out = _run(build_executive_dashboard(db))
    assert "drivers" in out["top_performers"]
    assert "drivers" in out["attention_required"]


def test_52_dashboard_trends_buckets():
    from lib.transport_operations_intelligence import build_executive_dashboard
    db = _DB()
    out = _run(build_executive_dashboard(db))
    for k in ("30d", "90d", "365d"):
        assert k in out["trends"]


# ===========================================================================
# 53–60 — API + UI + gate locks
# ===========================================================================
def test_53_api_route_paths_present():
    src = ROUTE.read_text()
    for p in (
        "/drivers/{driver_id}",
        "/carriers/{carrier_id}",
        "/trucks/{truck_id}",
        "/dashboard",
        "/operational-health",
        "/recommendations",
        "/predictions",
        "/audit",
    ):
        assert p in src


def test_54_api_routes_admin_gated():
    src = ROUTE.read_text()
    # Every endpoint uses require_admin_dep — confirm import + reference count.
    assert "require_admin_dep" in src
    assert src.count("Depends(require_admin_dep)") >= 8


def test_55_api_routes_read_only():
    src = ROUTE.read_text()
    # No router.patch / delete / put on the intelligence router.
    # Track 16.15 introduces ONE narrow POST that only writes to
    # ``transport_action_items`` (materialize cleanup actions); it is
    # allowed because it does not mutate any source intelligence
    # record. Every other route must remain a GET.
    for verb in ("@router.patch", "@router.delete", "@router.put"):
        assert verb not in src
    # Allowed POST is the materialize endpoint only.
    post_count = src.count("@router.post(")
    assert post_count <= 1
    if post_count:
        assert "materialize-actions" in src


def test_56_router_registered_in_server():
    src = (BACKEND / "server.py").read_text()
    assert "register_track_16_12_routes" in src


def test_57_ui_intelligence_center_present():
    src = FE_INTEL.read_text()
    assert "tx-intel-center" in src
    assert "ExecutiveDashboard" in src
    assert "RecommendationsPanel" in src
    assert "PredictionsPanel" in src


def test_58_ui_driver_intelligence_card_present():
    src = FE_LISTS.read_text()
    assert "DriverIntelligenceCard" in src
    assert "driver-ws-intelligence-overall-chip" in src


def test_59_ui_subnav_intelligence():
    src = FE_SHARED.read_text()
    assert '"intelligence"' in src
    assert "Intelligence" in src


def test_60_app_route_wired():
    src = FE_APP.read_text()
    assert "intelligence/*" in src
    assert "IntelligenceCenter" in src


def test_61_deployment_gate_includes_track_16_12():
    src = GATE.read_text()
    assert "test_track_16_12_transport_operations_intelligence" in src


def test_62_prior_tracks_preserved_in_gate():
    src = GATE.read_text()
    for f in (
        "test_track_16_04_transportation_foundation",
        "test_track_16_05_transportation_onboarding_compliance_center",
        "test_track_16_06_transportation_experience_layer",
        "test_track_16_07_transportation_workflow_activation",
        "test_track_16_08_transportation_orientation",
        "test_track_16_09_transportation_dispatch_gate_email_pilot",
        "test_track_16_10_transportation_automation_engine",
        "test_track_16_10a_transport_command_digest",
        "test_track_16_11_transport_hr_lifecycle_integration",
        "test_track_16_11A_transport_sync_monitor",
    ):
        assert f in src


def test_63_no_punitive_vocabulary_in_libs():
    for p in (CORE, DRV, CAR, TRK, PRED, REC, ORCH):
        src = p.read_text()
        for forbidden in ("Rejected", "Denied", "Failed —", "rejected!",
                           "denied!"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


def test_64_no_sms_push_in_libs():
    for p in (CORE, DRV, CAR, TRK, PRED, REC, ORCH):
        src = p.read_text()
        for forbidden in ("twilio", "TWILIO", "sendSms",
                           "push_notification", "fcm.googleapis"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


def test_65_no_destructive_mongo_ops_in_libs():
    for p in (CORE, DRV, CAR, TRK, PRED, REC, ORCH):
        src = p.read_text()
        for forbidden in ("drop_collection", "delete_many",
                           "drop_indexes", "db.employees.update_one",
                           "db.transport_persons.update_one",
                           "db.carriers.update_one",
                           "db.transport_trucks.update_one"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


def test_66_audit_writes_use_intelligence_collection():
    src = CORE.read_text()
    assert "transport_intelligence_audit" in src


def test_67_schema_version_propagates():
    from lib.transport_intelligence_core import SCHEMA_VERSION
    from lib.transport_driver_intelligence import (
        compute_driver_intelligence,
    )
    db = _DB()
    _seed_driver(db)
    out = _run(compute_driver_intelligence(db, "tp-1"))
    assert out["schema_version"] == SCHEMA_VERSION
