"""TRACK 23.10-D · Safety Portal Trench KPI Lift.

Consumer wrapper only. Ships ZERO new KPI logic — every count comes
from Track 23.10-C physical facts (`services/trench_safety`) and the
Track 23.10-B qualifications registry.

Endpoint shape (single spine per audit doc):

    GET /api/safety/company/trench-safety-kpis           ?window=30d
    GET /api/safety/projects/{project_number}/trench-safety-kpis
    GET /api/safety/company/trench-safety-cleanup        (missing/ambiguous list)

Rules
-----
* No double-counting — every count is a distinct current fact.
* B-04 preserved — `safe_to_use_verified_count` derives from the fact
  payload flag, never from `status="completed"` alone.
* Source classification is honest: LIVE requires project linkage,
  PARTIAL for asset-only / ambiguous, MISSING for no linkage at all.
* Zero cost/money fields.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from services.ods_spine.store import COLL_FACTS
from services.trench_safety.facts_emitter import SOURCE_TYPE_TRENCH
from services.certifications.qualification_registry import (
    list_active_qualifications, qualification_summary,
)


BANNED_COST_KEYS = frozenset({
    "cost", "rate", "budget", "payroll", "wage", "wages",
    "dollars", "amount", "price", "spend", "spent", "revenue",
    "invoice", "billing", "charge",
})

TENANT_DEFAULT = "masci"


def _assert_no_cost(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Runtime guard — strip any cost-adjacent key before responding.

    Belt-and-suspenders on top of the read-only spine. Never mutates
    the source facts.
    """
    def scrub(obj):
        if isinstance(obj, dict):
            return {k: scrub(v) for k, v in obj.items()
                    if k not in BANNED_COST_KEYS}
        if isinstance(obj, list):
            return [scrub(x) for x in obj]
        return obj
    return scrub(payload)


def _window_start(window: str) -> Optional[str]:
    now = datetime.now(timezone.utc).date()
    if window == "7d":
        return (now - timedelta(days=7)).isoformat()
    if window == "30d":
        return (now - timedelta(days=30)).isoformat()
    if window == "mtd":
        return now.replace(day=1).isoformat()
    if window == "ptd":                                          # project-to-date
        return None
    return (now - timedelta(days=30)).isoformat()                 # default 30d


def _classify_source(linked: int, partial: int, missing: int) -> str:
    """Honest source classification. LIVE requires >0 linked facts.
    PARTIAL for asset-only/ambiguous. MISSING for nothing at all."""
    if linked > 0 and missing + partial == 0:
        return "LIVE"
    if linked > 0:
        return "LIVE"                                            # some linked = LIVE overall (linked > 0)
    if partial > 0 or missing > 0:
        return "PARTIAL"
    return "MISSING"


def _fact_query(fact_type: str, window_start: Optional[str] = None,
                project_id: Optional[str] = None) -> Dict[str, Any]:
    q: Dict[str, Any] = {
        "tenant_id": TENANT_DEFAULT,
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "fact_type": fact_type,
        "is_current": True,
    }
    if window_start:
        q["date"] = {"$gte": window_start}
    if project_id:
        q["project_id"] = str(project_id)
    return q


async def _count(db, q: Dict[str, Any]) -> int:
    return await db[COLL_FACTS].count_documents(q)


async def _fact_link_breakdown(
    db, fact_type: str, window_start: Optional[str] = None,
) -> Dict[str, int]:
    """Return {linked_live, partial, missing, ambiguous} counts across
    all current facts of a given type. Uses `payload.linkage`."""
    q = _fact_query(fact_type, window_start=window_start)
    out = {"live": 0, "partial": 0, "missing": 0, "ambiguous": 0}
    cursor = db[COLL_FACTS].find(q, {"_id": 0, "payload.linkage": 1,
                                     "project_id": 1})
    async for f in cursor:
        link = (f.get("payload") or {}).get("linkage") or {}
        status = link.get("project_link_status") or "missing"
        # Never over-classify. The linker's own status is canonical.
        if status in {"explicit", "inherited_from_daily_report",
                      "inherited_from_parent_record",
                      "inferred_from_assignment"}:
            out["live"] += 1
        elif status == "ambiguous":
            out["ambiguous"] += 1
        elif status == "inferred_from_current_asset":
            out["partial"] += 1
        else:
            out["missing"] += 1
    return out


async def company_trench_safety_kpis(
    db, window: str = "30d",
) -> Dict[str, Any]:
    """Company-wide trench KPI lift. Never invents joins."""
    win = _window_start(window)

    excavation_days     = await _count(db, _fact_query("excavation_day_fact", win))
    inspections         = await _count(db, _fact_query("trench_inspection_fact", win))
    all_holds           = await _count(db, _fact_query("trench_hold_fact", win))
    open_holds          = await db[COLL_FACTS].count_documents(
        {**_fact_query("trench_hold_fact", win), "payload.is_active": True})
    closed_holds        = all_holds - open_holds
    all_repairs         = await _count(db, _fact_query("trench_repair_fact", win))
    completed_repairs   = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_repair_fact", win),
        "payload.status": "completed",
    })
    safe_verifications  = await _count(db, _fact_query("trench_verification_fact", win))
    cp_assignments      = await _count(db, _fact_query("competent_person_assignment_fact", win))
    # Historical (no window) missing-link count — cleanup surface.
    hist_missing_holds  = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_hold_fact"),
        "payload.linkage.project_link_status": "missing",
    })
    hist_missing_excavs = await db[COLL_FACTS].count_documents({
        **_fact_query("excavation_day_fact"),
        "payload.linkage.project_link_status": "missing",
    })
    hist_missing_insps  = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_inspection_fact"),
        "payload.linkage.project_link_status": "missing",
    })
    hist_missing_reps   = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_repair_fact"),
        "payload.linkage.project_link_status": "missing",
    })
    hist_missing_total  = hist_missing_holds + hist_missing_excavs + hist_missing_insps + hist_missing_reps

    # Linkage confidence breakdown (across every trench fact type in-window).
    linkage_breakdown = {"live": 0, "partial": 0, "missing": 0, "ambiguous": 0}
    for ft in (
        "excavation_day_fact", "trench_inspection_fact",
        "trench_hold_fact", "trench_repair_fact",
    ):
        b = await _fact_link_breakdown(db, ft, window_start=win)
        for k in linkage_breakdown:
            linkage_breakdown[k] += b[k]

    # Active competent persons (Track 23.10-B).
    cp_registry = await list_active_qualifications(
        db, qualification_type="COMPETENT_PERSON", warning_days=30,
    )
    cp_summary = await qualification_summary(
        db, qualification_type="COMPETENT_PERSON", warning_days=30,
    )

    # Top projects by attention.
    top_projects = await _top_projects_by_attention(db, window_start=win, limit=8)

    # Max depth observed.
    max_depth = 0.0
    cursor = db[COLL_FACTS].find(
        _fact_query("excavation_day_fact", win),
        {"_id": 0, "payload.max_depth_ft": 1},
    )
    async for f in cursor:
        try:
            v = float((f.get("payload") or {}).get("max_depth_ft") or 0)
            if v > max_depth:
                max_depth = v
        except (TypeError, ValueError):
            pass

    # Source classification per audit doc §4.
    trench_source = _classify_source(
        linkage_breakdown["live"],
        linkage_breakdown["partial"] + linkage_breakdown["ambiguous"],
        linkage_breakdown["missing"],
    )
    # Qualifications engine is LIVE (23.10-B shipped).
    cert_source = "LIVE" if cp_summary["active_count"] > 0 else "PARTIAL"

    result = {
        "window": window,
        "window_start": win,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trench": {
            "excavation_days": excavation_days,
            "trench_inspections": inspections,
            "open_holds": open_holds,
            "closed_holds": closed_holds,
            "total_holds": all_holds,
            "repairs_total": all_repairs,
            "repairs_completed": completed_repairs,
            # B-04 lock — never inferred from status alone.
            "safe_to_use_verified": safe_verifications,
            "competent_person_assignments": cp_assignments,
            "max_depth_observed_ft": max_depth,
            "linkage_breakdown": linkage_breakdown,
            "historical_missing_link_count": hist_missing_total,
            "historical_missing_by_type": {
                "excavation_day_fact": hist_missing_excavs,
                "trench_hold_fact": hist_missing_holds,
                "trench_inspection_fact": hist_missing_insps,
                "trench_repair_fact": hist_missing_reps,
            },
        },
        "certifications": {
            "active_competent_persons": cp_summary["active_count"],
            "expiring_within_days": cp_summary["expiring_within_days"],
            "expiring_soon": cp_summary["expiring_within_count"],
            "expired": cp_summary["expired_count"],
            "suspended": cp_summary["suspended_count"],
            "revoked": cp_summary["revoked_count"],
            "pending": cp_summary["pending_count"],
            "cp_registry_sample": cp_registry[:5],
        },
        "top_projects": top_projects,
        "source_classification": {
            "trench": trench_source,
            "certifications": cert_source,
        },
    }
    return _assert_no_cost(result)


async def _top_projects_by_attention(
    db, *, window_start: Optional[str], limit: int = 8,
) -> List[Dict[str, Any]]:
    """Aggregate the in-window facts by project_id then score."""
    q_base = {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
        "project_id": {"$nin": ["unknown"]},
    }
    if window_start:
        q_base["date"] = {"$gte": window_start}

    projects: Dict[str, Dict[str, Any]] = {}
    cursor = db[COLL_FACTS].find(q_base, {"_id": 0, "project_id": 1,
                                          "fact_type": 1, "payload": 1})
    async for f in cursor:
        pn = f.get("project_id")
        if not pn or pn == "unknown":
            continue
        p = projects.setdefault(pn, {
            "project_number": pn, "excavation_days": 0,
            "open_holds": 0, "repairs": 0, "verifications": 0,
            "inspections": 0, "cp_assignments": 0,
            "attention_score": 0,
        })
        ft = f.get("fact_type")
        pl = f.get("payload") or {}
        if ft == "excavation_day_fact":
            p["excavation_days"] += 1
        elif ft == "trench_hold_fact":
            if pl.get("is_active"):
                p["open_holds"] += 1
        elif ft == "trench_repair_fact":
            p["repairs"] += 1
        elif ft == "trench_verification_fact":
            p["verifications"] += 1
        elif ft == "trench_inspection_fact":
            p["inspections"] += 1
        elif ft == "competent_person_assignment_fact":
            p["cp_assignments"] += 1

    # Attention score = 5*open_holds + 3*(repairs-verifications) + 1*excavation_days
    for p in projects.values():
        pending = max(0, p["repairs"] - p["verifications"])
        p["attention_score"] = (
            5 * p["open_holds"] + 3 * pending + 1 * p["excavation_days"]
        )
        p["cp_coverage"] = "assigned" if p["cp_assignments"] > 0 else \
            ("needed" if p["excavation_days"] > 0 else "not_required")
        p["link_status"] = "LIVE"                                 # by construction (linked project_id)
    ranked = sorted(projects.values(),
                    key=lambda x: x["attention_score"], reverse=True)
    return ranked[:limit]


async def project_trench_safety_kpis(
    db, project_number: str,
) -> Dict[str, Any]:
    """Per-project block for the Safety Portal drilldown."""
    q_proj = {"project_id": str(project_number)}
    counts = {}
    for ft in (
        "excavation_day_fact", "trench_inspection_fact",
        "trench_hold_fact", "trench_repair_fact",
        "trench_verification_fact",
        "competent_person_assignment_fact",
    ):
        counts[ft] = await db[COLL_FACTS].count_documents(
            {**_fact_query(ft), **q_proj},
        )
    open_holds = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_hold_fact"), **q_proj,
        "payload.is_active": True,
    })
    safe_verified = await db[COLL_FACTS].count_documents({
        **_fact_query("trench_repair_fact"), **q_proj,
        "payload.safe_to_use_verified": True,
    })
    # Latest excavation-day signal.
    latest_ex = await db[COLL_FACTS].find(
        _fact_query("excavation_day_fact", project_id=str(project_number)),
        {"_id": 0},
    ).sort("date", -1).to_list(1)
    latest_ex = latest_ex[0] if latest_ex else None

    # CP snapshot: latest CP assignment on this project.
    latest_cp_assignments = await db[COLL_FACTS].find(
        _fact_query("competent_person_assignment_fact", project_id=str(project_number)),
        {"_id": 0},
    ).sort("created_at", -1).to_list(5)

    unresolved_utility = await db[COLL_FACTS].count_documents({
        **_fact_query("excavation_day_fact"), **q_proj,
        "payload.utilities_status": "damage_strike",
    })
    linkage = await _fact_link_breakdown_for_project(db, project_number)
    trench_source = _classify_source(
        linkage["live"],
        linkage["partial"] + linkage["ambiguous"],
        linkage["missing"],
    )

    result = {
        "project_number": project_number,
        "excavation_days": counts["excavation_day_fact"],
        "inspections": counts["trench_inspection_fact"],
        "holds_total": counts["trench_hold_fact"],
        "open_holds": open_holds,
        "closed_holds": counts["trench_hold_fact"] - open_holds,
        "repairs": counts["trench_repair_fact"],
        "verifications": counts["trench_verification_fact"],
        "safe_to_use_verified": safe_verified,
        "cp_assignments": counts["competent_person_assignment_fact"],
        "unresolved_utility_conflict_count": unresolved_utility,
        "latest_excavation_day": (latest_ex or {}).get("payload"),
        "cp_snapshot": (latest_cp_assignments[0].get("payload")
                        if latest_cp_assignments else None),
        "recent_cp_assignments": [f.get("payload") for f in latest_cp_assignments],
        "linkage_breakdown": linkage,
        "source_classification": {
            "trench": trench_source,
            "certifications": "LIVE",
        },
    }
    return _assert_no_cost(result)


async def _fact_link_breakdown_for_project(
    db, project_number: str,
) -> Dict[str, int]:
    out = {"live": 0, "partial": 0, "missing": 0, "ambiguous": 0}
    for ft in (
        "excavation_day_fact", "trench_inspection_fact",
        "trench_hold_fact", "trench_repair_fact",
    ):
        q = {**_fact_query(ft), "project_id": str(project_number)}
        cursor = db[COLL_FACTS].find(q, {"_id": 0, "payload.linkage": 1})
        async for f in cursor:
            link = (f.get("payload") or {}).get("linkage") or {}
            st = link.get("project_link_status") or "missing"
            if st in {"explicit", "inherited_from_daily_report",
                      "inherited_from_parent_record",
                      "inferred_from_assignment"}:
                out["live"] += 1
            elif st == "ambiguous":
                out["ambiguous"] += 1
            elif st == "inferred_from_current_asset":
                out["partial"] += 1
            else:
                out["missing"] += 1
    return out


async def cleanup_missing_ambiguous(
    db, limit: int = 100,
) -> Dict[str, Any]:
    """Read-only cleanup list. NEVER invents joins. Safety/Admin only."""
    q_base = {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
        "$or": [
            {"payload.linkage.project_link_status": "missing"},
            {"payload.linkage.project_link_status": "ambiguous"},
            {"payload.linkage.project_link_status": "inferred_from_current_asset"},
        ],
    }
    cursor = db[COLL_FACTS].find(q_base, {"_id": 0}).sort("created_at", -1)
    docs = await cursor.to_list(limit * 2)
    items: List[Dict[str, Any]] = []
    counters = {"missing": 0, "ambiguous": 0, "asset_only": 0}
    oldest = None
    newest = None
    for f in docs[:limit]:
        pl = f.get("payload") or {}
        link = pl.get("linkage") or {}
        st = link.get("project_link_status") or "missing"
        if st == "missing":
            counters["missing"] += 1
            reason = "no explicit project, no daily report, no active deployment window"
        elif st == "ambiguous":
            counters["ambiguous"] += 1
            reason = "multiple overlapping deployments — needs manual review"
        elif st == "inferred_from_current_asset":
            counters["asset_only"] += 1
            reason = "asset current_project fallback — low confidence, not accepted as LIVE"
        else:
            continue
        items.append({
            "fact_id": f.get("fact_id"),
            "fact_type": f.get("fact_type"),
            "record_type": (f.get("fact_type") or "").replace("_fact", ""),
            "record_id": f.get("source_item_id"),
            "asset_id": pl.get("asset_id"),
            "date": f.get("date"),
            "current_status": (
                "active" if pl.get("is_active")
                else pl.get("status") or "closed"
            ),
            "confidence": link.get("confidence") or "none",
            "reason": reason,
            "possible_project": link.get("project_number"),
            "possible_project_note":
                "candidate only — NOT applied. Manual audit required." if link.get("project_number") else "",
        })
        d = f.get("date") or f.get("created_at") or ""
        if not oldest or (d and d < oldest):
            oldest = d
        if not newest or (d and d > newest):
            newest = d
    total_missing = await db[COLL_FACTS].count_documents({
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
        "payload.linkage.project_link_status": "missing",
    })
    total_ambiguous = await db[COLL_FACTS].count_documents({
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
        "payload.linkage.project_link_status": "ambiguous",
    })
    total_asset_only = await db[COLL_FACTS].count_documents({
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "is_current": True,
        "payload.linkage.project_link_status": "inferred_from_current_asset",
    })
    result = {
        "totals": {
            "missing": total_missing,
            "ambiguous": total_ambiguous,
            "asset_only": total_asset_only,
        },
        "counts_returned": counters,
        "oldest_unlinked_at": oldest,
        "newest_unlinked_at": newest,
        "items": items,
        "read_only": True,
        "note": "This list is a Safety/Admin cleanup surface. No auto-fix. "
                "No fake joins. Ambiguous / asset-only linkages remain "
                "unaccepted until manually verified.",
    }
    return _assert_no_cost(result)


__all__ = [
    "company_trench_safety_kpis",
    "project_trench_safety_kpis",
    "cleanup_missing_ambiguous",
    "BANNED_COST_KEYS",
]
