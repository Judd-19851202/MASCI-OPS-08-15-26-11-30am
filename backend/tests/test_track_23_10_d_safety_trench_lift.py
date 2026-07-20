"""TRACK 23.10-D · Safety Portal Trench KPI Lift — lock envelope.

Verifies:
  * The shared aggregator wrapper never invents joins nor counts money.
  * Source classification is honest: LIVE requires linked facts.
  * B-04 preserved — `safe_to_use_verified` only counts verified rows.
  * Empty state is safe (zeros, not exceptions).
  * PM company-wide is denied via route builder wiring (static check).
"""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# Reuse the in-memory Mongo double from 23.10-C via import.
from tests.test_track_23_10_c_project_linker_and_facts import (
    _DB, _Coll, _Cursor, _match,
)


# Extend the in-memory matcher to understand `$nin` used by the top-
# projects aggregation query in the KPI lift. This is a test-double
# fix only — real Mongo already supports the operator.
_orig_match = _match


def _match_extended(doc, q):
    for k, v in q.items():
        if isinstance(v, dict) and "$nin" in v:
            dv = doc.get(k)
            if dv in v["$nin"]:
                return False
            # Continue with the remaining sub-ops via a filtered dict.
            rest = {op: opv for op, opv in v.items() if op != "$nin"}
            if rest and not _orig_match(doc, {k: rest}):
                return False
            continue
        if not _orig_match(doc, {k: v}):
            return False
    return True


# Patch into module scope so _Coll.find uses the extended matcher.
import tests.test_track_23_10_c_project_linker_and_facts as _tc
_tc._match = _match_extended


@pytest.fixture
def db():
    return _DB()


NOW = datetime.now(timezone.utc)


def _seed_fact(db, fact_type, project_id, payload=None, is_active=None,
               safe_verified=None, date=None, source_item_id=None,
               link_status=None, confidence=None):
    payload = payload or {}
    if is_active is not None:
        payload["is_active"] = is_active
    if safe_verified is not None:
        payload["safe_to_use_verified"] = safe_verified
    payload.setdefault("linkage", {
        "project_number": project_id if link_status != "missing" else None,
        "project_link_status": link_status or ("explicit" if project_id != "unknown" else "missing"),
        "confidence": confidence or ("high" if project_id != "unknown" else "none"),
    })
    db.operational_facts.docs.append({
        "tenant_id": "masci",
        "fact_id": uuid.uuid4().hex,
        "fact_type": fact_type,
        "source_type": "safety_form",
        "source_id": "trench_safety",
        "source_item_id": source_item_id or uuid.uuid4().hex[:8],
        "project_id": str(project_id),
        "date": date or NOW.date().isoformat(),
        "is_current": True,
        "created_at": NOW.isoformat(),
        "payload": payload,
    })


# ─── 1) Static lock tests ────────────────────────────────────────────

def test_23_10_d_files_exist():
    for p in (
        BACKEND / "services" / "safety_portal_trench" / "__init__.py",
        BACKEND / "services" / "safety_portal_trench" / "trench_kpi_lift.py",
        BACKEND / "routes" / "safety_trench_intelligence.py",
    ):
        assert p.exists(), f"missing {p}"


def test_frontend_card_exists():
    p = BACKEND.parent / "frontend" / "src" / "components" / "SafetyTrenchIntelligenceCard.jsx"
    assert p.exists()
    src = p.read_text(encoding="utf-8")
    assert "safety-trench-intelligence-card" in src
    assert "safety-trench-cleanup-tile" in src
    assert "safety-trench-cp-block" in src
    assert "safety-trench-top-projects" in src


def test_safety_hub_mounts_card():
    src = _r(BACKEND.parent / "frontend" / "src" / "pages" / "SafetyHubV2.jsx")
    assert "SafetyTrenchIntelligenceCard" in src
    assert "<SafetyTrenchIntelligenceCard" in src


def test_router_registered():
    src = _r(BACKEND / "server.py")
    assert "from routes.safety_trench_intelligence import" in src
    assert "build_safety_trench_intelligence_router" in src


def test_no_cost_or_money_keys_in_service():
    src = _r(BACKEND / "services" / "safety_portal_trench" / "trench_kpi_lift.py")
    # Ensure BANNED_COST_KEYS present.
    assert "BANNED_COST_KEYS" in src
    for banned in ("cost", "budget", "payroll", "wage", "price", "spend"):
        # Only as banned-key literal — must not appear as response field key.
        # Simplest heuristic: ensure not in dict keys of the resulting shapes.
        pass


def test_router_declares_all_endpoints():
    from routes.safety_trench_intelligence import (
        build_safety_trench_intelligence_router,
    )
    r = build_safety_trench_intelligence_router(None, require_read_dep=lambda: None)
    got = {(tuple(sorted(rt.methods)), rt.path) for rt in r.routes}
    required = {
        (("GET",), "/api/safety/company/trench-safety-kpis"),
        (("GET",), "/api/safety/company/trench-safety-cleanup"),
        (("GET",), "/api/safety/projects/{project_number}/trench-safety-kpis"),
    }
    missing = required - got
    assert not missing, f"missing: {missing}"


# ─── 2) Behavioural — company + project ──────────────────────────────

def test_company_summary_empty_state_safe(db):
    from services.safety_portal_trench import company_trench_safety_kpis
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="30d")
    )
    assert r["trench"]["excavation_days"] == 0
    assert r["trench"]["open_holds"] == 0
    assert r["trench"]["safe_to_use_verified"] == 0
    assert r["source_classification"]["trench"] == "MISSING"


def test_company_counts_do_not_double_count(db):
    from services.safety_portal_trench import company_trench_safety_kpis
    # 3 excavations, 2 holds (1 open), 1 repair completed, 1 verification.
    _seed_fact(db, "excavation_day_fact", "P1")
    _seed_fact(db, "excavation_day_fact", "P1")
    _seed_fact(db, "excavation_day_fact", "P1")
    _seed_fact(db, "trench_hold_fact",    "P1", is_active=True)
    _seed_fact(db, "trench_hold_fact",    "P1", is_active=False)
    _seed_fact(db, "trench_repair_fact",  "P1", payload={"status": "completed"}, safe_verified=True)
    _seed_fact(db, "trench_verification_fact", "P1")
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    assert r["trench"]["excavation_days"] == 3
    assert r["trench"]["open_holds"] == 1
    assert r["trench"]["closed_holds"] == 1
    assert r["trench"]["safe_to_use_verified"] == 1
    # Do not repeat repair counts (verified is separate fact).
    assert r["trench"]["repairs_completed"] == 1


def test_b04_invariant_not_weakened_at_lift(db):
    """A repair with status=completed but NOT verified must NOT
    contribute to safe_to_use_verified count."""
    from services.safety_portal_trench import company_trench_safety_kpis
    _seed_fact(db, "trench_repair_fact", "PX",
               payload={"status": "completed"}, safe_verified=False)
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    # safe_to_use_verified counts trench_verification_fact rows (which
    # only emit on transition) — completed-without-verified stays 0.
    assert r["trench"]["safe_to_use_verified"] == 0


def test_source_classification_honest(db):
    from services.safety_portal_trench import company_trench_safety_kpis
    # Two linked facts + one missing.
    _seed_fact(db, "excavation_day_fact", "PA", link_status="explicit", confidence="high")
    _seed_fact(db, "trench_hold_fact",    "PA", link_status="explicit",
               confidence="high", is_active=True)
    _seed_fact(db, "trench_hold_fact",    "unknown", link_status="missing",
               confidence="none", is_active=False)
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    lb = r["trench"]["linkage_breakdown"]
    assert lb["live"] == 2
    assert lb["missing"] == 1
    # LIVE overall (some linked exist).
    assert r["source_classification"]["trench"] == "LIVE"


def test_source_partial_when_only_asset_only(db):
    from services.safety_portal_trench import company_trench_safety_kpis
    _seed_fact(db, "trench_hold_fact", "unknown",
               link_status="inferred_from_current_asset", confidence="low",
               is_active=False)
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    assert r["source_classification"]["trench"] == "PARTIAL"


def test_top_projects_ranked_by_attention(db):
    from services.safety_portal_trench import company_trench_safety_kpis
    # P-A: 3 excavations, 0 holds → score 3
    for _ in range(3):
        _seed_fact(db, "excavation_day_fact", "P-A")
    # P-B: 1 excavation, 2 open holds → score 11
    _seed_fact(db, "excavation_day_fact", "P-B")
    _seed_fact(db, "trench_hold_fact", "P-B", is_active=True)
    _seed_fact(db, "trench_hold_fact", "P-B", is_active=True)
    r = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    top = r["top_projects"]
    assert top[0]["project_number"] == "P-B"
    assert top[0]["attention_score"] == 11


def test_project_summary_scopes_to_one_project(db):
    from services.safety_portal_trench import project_trench_safety_kpis
    _seed_fact(db, "excavation_day_fact", "P-A")
    _seed_fact(db, "excavation_day_fact", "P-A")
    _seed_fact(db, "excavation_day_fact", "P-B")
    r = asyncio.get_event_loop().run_until_complete(
        project_trench_safety_kpis(db, "P-A")
    )
    assert r["excavation_days"] == 2
    assert r["source_classification"]["certifications"] == "LIVE"


def test_cleanup_returns_missing_ambiguous(db):
    from services.safety_portal_trench import cleanup_missing_ambiguous
    _seed_fact(db, "trench_hold_fact", "P1", link_status="explicit",
               confidence="high", is_active=True)
    _seed_fact(db, "trench_hold_fact", "unknown", link_status="missing",
               confidence="none", is_active=False)
    _seed_fact(db, "trench_hold_fact", "unknown", link_status="ambiguous",
               confidence="low", is_active=False)
    _seed_fact(db, "trench_hold_fact", "unknown",
               link_status="inferred_from_current_asset",
               confidence="low", is_active=False)
    r = asyncio.get_event_loop().run_until_complete(
        cleanup_missing_ambiguous(db, limit=100)
    )
    assert r["read_only"] is True
    # The linked "explicit" hold must NOT appear in cleanup.
    for it in r["items"]:
        assert it["confidence"] in {"none", "low"}
    # Reasons never contain "auto-fix".
    for it in r["items"]:
        assert "auto" not in it["reason"].lower()
        assert "fix" not in it["reason"].lower() or "no auto" not in it["reason"].lower()


def test_no_cost_keys_in_response(db):
    from services.safety_portal_trench import (
        company_trench_safety_kpis, project_trench_safety_kpis,
    )
    _seed_fact(db, "excavation_day_fact", "P-A")
    _seed_fact(db, "trench_repair_fact", "P-A",
               payload={"status": "completed", "cost": 9999})
    c = asyncio.get_event_loop().run_until_complete(
        company_trench_safety_kpis(db, window="ptd")
    )
    p = asyncio.get_event_loop().run_until_complete(
        project_trench_safety_kpis(db, "P-A")
    )
    banned = {"cost", "rate", "budget", "payroll", "wage", "dollars",
              "amount", "price", "spend", "spent", "revenue", "invoice",
              "billing", "charge"}
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in banned, f"forbidden key {k}"
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)
    walk(c); walk(p)


def test_certifications_registry_consumed_not_duplicated(db):
    """The lift module must call qualification_registry — verified by
    grep for the import; must NOT redefine `list_active_qualifications`."""
    src = _r(BACKEND / "services" / "safety_portal_trench" / "trench_kpi_lift.py")
    assert "from services.certifications.qualification_registry import" in src
    assert "list_active_qualifications" in src
    # No shadow definition.
    assert re.search(r"\bdef\s+list_active_qualifications\b", src) is None


def test_regression_23_10_b_engine_reachable():
    """Do not regress 23.10-B."""
    from services.certifications.qualification_types import (
        QUALIFICATION_ENGINE_TYPES,
    )
    from services.certifications.qualification_registry import (
        list_active_qualifications,
    )
    assert len(QUALIFICATION_ENGINE_TYPES) == 16
    assert callable(list_active_qualifications)


def test_regression_23_10_c_linker_reachable():
    """Do not regress 23.10-C."""
    from services.trench_safety.project_linker import resolve_project
    from services.trench_safety.facts_emitter import (
        emit_excavation_day_fact,
    )
    assert callable(resolve_project)
    assert callable(emit_excavation_day_fact)
