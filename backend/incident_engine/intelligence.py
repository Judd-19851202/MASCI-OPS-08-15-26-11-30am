"""Track 19.16 · Phase D · Executive Intelligence Center — aggregations.

Read-only intelligence over the incident engine. Every function is a
PURE aggregation over the existing collections — no writes, no new
storage. Executive Intelligence CONSUMES data; it never owns data.

Zero-Drift preserved.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .constants import COLLECTION_CASES, COLLECTION_CORRECTIVE_ACTIONS
from .workspace import (
    COLLECTION_TASKS, list_tasks,
    compute_case_health,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(dt: Optional[str]) -> Optional[datetime]:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def _sla_status(case: Dict[str, Any]) -> str:
    """Compute SLA bucket for a case: ON_PACE | WATCH | BEHIND | MISSED | NONE.

    Target date lives at ``safety_block.target_ready_at`` (extra field —
    ``SafetyBlock`` has ``extra='allow'``). Closed cases return NONE.
    """
    if (case.get("state") or "") in ("CLOSED",):
        return "NONE"
    sb = case.get("safety_block") or {}
    target = _parse(sb.get("target_ready_at"))
    if not target:
        return "NONE"
    now = _now()
    if now > target:
        return "MISSED"
    delta = target - now
    if delta < timedelta(days=2):
        return "BEHIND"
    if delta < timedelta(days=5):
        return "WATCH"
    return "ON_PACE"


async def _all_cases(db) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_CASES].find({}, {"_id": 0}).sort("created_at", -1)
    return [d async for d in cur]


# ── HOME · Company Health + Action Queue ─────────────────────────────
async def compute_company_health(db) -> Dict[str, Any]:
    cases = await _all_cases(db)
    open_cases = [c for c in cases if c.get("state") != "CLOSED"]
    critical_types = {"employee_injury", "utility_strike", "workplace_violence"}
    critical = [c for c in open_cases
                if (c.get("field_block") or {}).get("incident_type") in critical_types]

    sla_counts = Counter(_sla_status(c) for c in open_cases)
    ca_open = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {"consumer_kind": "incident_case", "state": {"$in": ["OPEN", "ASSIGNED", "IN_PROGRESS"]}}
    )
    ca_total = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {"consumer_kind": "incident_case"}
    )

    # Average readiness of open cases (computed live).
    total_completeness = 0
    n = 0
    for c in open_cases:
        try:
            h = await compute_case_health(db, case_id=c["id"], case_doc=c)
            total_completeness += h.get("completeness_pct", 0)
            n += 1
        except Exception:
            continue
    avg_readiness = round(total_completeness / n) if n else 0

    # Trend: cases in past 30 days vs previous 30 days.
    now = _now()
    recent = sum(1 for c in cases
                 if (dt := _parse(c.get("created_at"))) and dt > now - timedelta(days=30))
    prev = sum(1 for c in cases
               if (dt := _parse(c.get("created_at")))
               and now - timedelta(days=60) < dt <= now - timedelta(days=30))
    trend = "flat"
    if recent > prev * 1.15:
        trend = "worsening"
    elif recent < prev * 0.85:
        trend = "improving"

    return {
        "open_cases": len(open_cases),
        "total_cases": len(cases),
        "critical_cases": len(critical),
        "avg_readiness_pct": avg_readiness,
        "corrective_actions_open": ca_open,
        "corrective_actions_total": ca_total,
        "sla": {
            "on_pace": sla_counts.get("ON_PACE", 0),
            "watch":   sla_counts.get("WATCH", 0),
            "behind":  sla_counts.get("BEHIND", 0),
            "missed":  sla_counts.get("MISSED", 0),
            "unset":   sla_counts.get("NONE", 0),
        },
        "trend_30d": trend,
        "trend_counts": {"recent_30d": recent, "prior_30d": prev},
    }


async def compute_action_queue(db, limit: int = 20) -> List[Dict[str, Any]]:
    """Cases requiring executive attention, ranked by urgency."""
    cases = await _all_cases(db)
    critical_types = {"employee_injury", "utility_strike", "workplace_violence"}
    now = _now()
    queue: List[Dict[str, Any]] = []
    for c in cases:
        if c.get("state") == "CLOSED":
            continue
        fb = c.get("field_block") or {}
        sb = c.get("safety_block") or {}
        inc_type = fb.get("incident_type") or ""
        reasons: List[str] = []
        urgency = 0

        if inc_type in critical_types:
            reasons.append("critical_incident_type")
            urgency += 30
        if sb.get("osha_recordable") is True:
            reasons.append("osha_recordable")
            urgency += 20
        sla = _sla_status(c)
        if sla in ("MISSED", "BEHIND"):
            reasons.append(f"sla_{sla.lower()}")
            urgency += 25 if sla == "MISSED" else 15
        # Cases open > 14 days without root cause.
        created = _parse(c.get("submitted_at") or c.get("created_at"))
        age_days = max(0, (now - created).days) if created else 0
        if age_days > 14 and not (sb.get("root_cause_summary") or "").strip():
            reasons.append("stale_investigation")
            urgency += 10

        if not reasons:
            continue

        queue.append({
            "case_id": c["id"],
            "case_number": c.get("case_number") or "",
            "incident_type": inc_type,
            "state": c.get("state"),
            "location_label": fb.get("location_label") or "",
            "job_number": fb.get("job_number") or "",
            "age_days": age_days,
            "sla": sla,
            "urgency": urgency,
            "reasons": reasons,
            "recommended_action": _recommended_action(reasons, sb),
        })

    queue.sort(key=lambda x: x["urgency"], reverse=True)
    return queue[:limit]


def _recommended_action(reasons: List[str], safety_block: Dict[str, Any]) -> str:
    if "sla_missed" in reasons:
        return "review_immediately"
    if "critical_incident_type" in reasons and not safety_block.get("root_cause_summary"):
        return "assign_root_cause_owner"
    if "sla_behind" in reasons:
        return "reallocate_investigator"
    if "stale_investigation" in reasons:
        return "escalate_to_safety_lead"
    if "osha_recordable" in reasons:
        return "verify_osha_paperwork"
    return "review"


# ── Root Cause Intelligence ─────────────────────────────────────────
async def compute_root_cause_intelligence(db) -> Dict[str, Any]:
    cases = await _all_cases(db)
    freq: Counter = Counter()
    severity: Dict[str, int] = defaultdict(int)   # heuristic — count of injury cases per cause
    recurrence: Dict[str, int] = defaultdict(int)
    for c in cases:
        sb = c.get("safety_block") or {}
        cats = list(sb.get("root_cause_categories") or [])
        for cat in cats:
            key = str(cat).strip().lower()
            if not key:
                continue
            freq[key] += 1
            if (c.get("field_block") or {}).get("incident_type") in (
                "employee_injury", "utility_strike"):
                severity[key] += 1
        # Recurrence: appears in more than one case's contributing factors
        for cf in list(sb.get("contributing_factors") or []):
            key = str(cf).strip().lower()
            if key:
                recurrence[key] += 1

    return {
        "categories": [
            {"code": k, "count": n, "severity_weighted": severity.get(k, 0)}
            for k, n in freq.most_common(20)
        ],
        "recurring_factors": [
            {"code": k, "occurrences": n}
            for k, n in Counter(recurrence).most_common(10) if n > 1
        ],
    }


# ── Corrective Action Intelligence ──────────────────────────────────
async def compute_capa_intelligence(db) -> Dict[str, Any]:
    q_base = {"consumer_kind": "incident_case"}
    total = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(q_base)
    open_ = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {**q_base, "state": {"$in": ["OPEN", "ASSIGNED", "IN_PROGRESS"]}}
    )
    verified = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {**q_base, "state": "VERIFIED"}
    )
    canceled = await db[COLLECTION_CORRECTIVE_ACTIONS].count_documents(
        {**q_base, "state": "CANCELED"}
    )

    # Overdue: due_at in the past and not verified/canceled.
    now_iso = _now().isoformat()
    cur = db[COLLECTION_CORRECTIVE_ACTIONS].find(
        {**q_base, "state": {"$in": ["OPEN", "ASSIGNED", "IN_PROGRESS"]}},
        {"_id": 0},
    )
    all_open = [d async for d in cur]
    overdue = [a for a in all_open if a.get("due_at") and a["due_at"] < now_iso]

    # Class breakdown.
    class_counts: Counter = Counter()
    for a in all_open:
        class_counts[a.get("action_class", "")] += 1

    # Average completion time (verified actions).
    cur_v = db[COLLECTION_CORRECTIVE_ACTIONS].find(
        {**q_base, "state": "VERIFIED"}, {"_id": 0},
    )
    completion_days: List[float] = []
    async for a in cur_v:
        c0 = _parse(a.get("created_at"))
        v0 = _parse(a.get("verified_at"))
        if c0 and v0 and v0 > c0:
            completion_days.append((v0 - c0).total_seconds() / 86400.0)
    avg_completion = round(sum(completion_days) / len(completion_days), 1) if completion_days else 0.0

    return {
        "total": total,
        "open": open_,
        "verified": verified,
        "canceled": canceled,
        "overdue": len(overdue),
        "avg_completion_days": avg_completion,
        "by_class": [{"class": k, "count": v} for k, v in class_counts.most_common(10)],
    }


# ── Project Intelligence ────────────────────────────────────────────
async def compute_project_intelligence(db) -> List[Dict[str, Any]]:
    cases = await _all_cases(db)
    by_job: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "job_number": "", "cases": 0, "open": 0, "critical": 0,
    })
    critical_types = {"employee_injury", "utility_strike", "workplace_violence"}
    for c in cases:
        fb = c.get("field_block") or {}
        job = (fb.get("job_number") or "").strip() or "UNKNOWN"
        rec = by_job[job]
        rec["job_number"] = job
        rec["cases"] += 1
        if c.get("state") != "CLOSED":
            rec["open"] += 1
        if fb.get("incident_type") in critical_types:
            rec["critical"] += 1
    ranked = sorted(by_job.values(), key=lambda r: (r["critical"], r["open"], r["cases"]), reverse=True)
    return ranked[:25]


# ── Fleet Intelligence ──────────────────────────────────────────────
async def compute_fleet_intelligence(db) -> Dict[str, Any]:
    cases = await _all_cases(db)
    vehicles = [c for c in cases
                if (c.get("field_block") or {}).get("incident_type") == "vehicle_accident"]
    equipment = [c for c in cases
                 if (c.get("field_block") or {}).get("incident_type") == "equipment_accident"]

    def _by_id(rows, key):
        counter: Counter = Counter()
        for r in rows:
            fb = r.get("field_block") or {}
            val = str(fb.get(key) or "").strip()
            if val:
                counter[val] += 1
        return counter

    veh_ids = _by_id(vehicles, "vehicle_ids")
    eq_ids = _by_id(equipment, "equipment_id")
    return {
        "vehicle_incidents_total": len(vehicles),
        "equipment_incidents_total": len(equipment),
        "repeat_vehicles": [{"id": k, "count": v} for k, v in veh_ids.most_common() if v > 1],
        "repeat_equipment": [{"id": k, "count": v} for k, v in eq_ids.most_common() if v > 1],
    }


# ── Learning Intelligence ───────────────────────────────────────────
async def compute_learning_intelligence(db) -> Dict[str, Any]:
    cases = await _all_cases(db)
    near_miss = [c for c in cases
                 if (c.get("field_block") or {}).get("incident_type") == "near_miss"]

    hour_counter: Counter = Counter()
    weekday_counter: Counter = Counter()
    month_counter: Counter = Counter()
    for c in cases:
        occ = _parse((c.get("field_block") or {}).get("occurred_at"))
        if occ:
            hour_counter[occ.hour] += 1
            weekday_counter[occ.weekday()] += 1
            month_counter[occ.month] += 1

    # Top RCA categories = same as root_cause_intelligence but pared.
    rca = await compute_root_cause_intelligence(db)

    # Verified corrective actions grouped by class (proxy for "most effective").
    cur = db[COLLECTION_CORRECTIVE_ACTIONS].find(
        {"consumer_kind": "incident_case", "state": "VERIFIED"}, {"_id": 0},
    )
    effective: Counter = Counter()
    async for a in cur:
        effective[a.get("action_class", "")] += 1

    return {
        "near_miss_count": len(near_miss),
        "peak_hours": [{"hour": h, "count": n} for h, n in hour_counter.most_common(6)],
        "peak_weekdays": [{"weekday": d, "count": n} for d, n in weekday_counter.most_common()],
        "peak_months": [{"month": m, "count": n} for m, n in month_counter.most_common()],
        "top_root_causes": rca["categories"][:5],
        "most_verified_action_classes": [
            {"class": k, "count": v} for k, v in effective.most_common(5)
        ],
    }


# ── Risk Heatmap (incident_type × project) ──────────────────────────
async def compute_risk_heatmap(db) -> Dict[str, Any]:
    cases = await _all_cases(db)
    matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    types: set = set()
    jobs: set = set()
    for c in cases:
        fb = c.get("field_block") or {}
        t = fb.get("incident_type") or "unknown"
        j = (fb.get("job_number") or "").strip() or "UNKNOWN"
        matrix[j][t] += 1
        types.add(t)
        jobs.add(j)

    return {
        "incident_types": sorted(types),
        "jobs": sorted(jobs),
        "cells": [
            {"job": j, "type": t, "count": matrix[j].get(t, 0)}
            for j in sorted(jobs) for t in sorted(types)
            if matrix[j].get(t, 0) > 0
        ],
    }


# ── Executive Brief ─────────────────────────────────────────────────
async def compute_executive_brief(db) -> Dict[str, Any]:
    """Structured brief. Not prose — sections that render as intelligence."""
    health = await compute_company_health(db)
    queue = await compute_action_queue(db, limit=5)
    capa = await compute_capa_intelligence(db)
    proj = await compute_project_intelligence(db)
    fleet = await compute_fleet_intelligence(db)
    learn = await compute_learning_intelligence(db)
    return {
        "organization_health": health,
        "highest_risks": queue,
        "positive_trends": {
            "avg_readiness_pct": health["avg_readiness_pct"],
            "verified_corrective_actions": capa["verified"],
            "improving": health["trend_30d"] == "improving",
        },
        "negative_trends": {
            "overdue_corrective_actions": capa["overdue"],
            "sla_missed_or_behind":
                health["sla"]["missed"] + health["sla"]["behind"],
            "worsening": health["trend_30d"] == "worsening",
        },
        "top_projects_by_risk": proj[:5],
        "fleet": fleet,
        "learning": learn,
    }


__all__ = [
    "compute_company_health",
    "compute_action_queue",
    "compute_root_cause_intelligence",
    "compute_capa_intelligence",
    "compute_project_intelligence",
    "compute_fleet_intelligence",
    "compute_learning_intelligence",
    "compute_risk_heatmap",
    "compute_executive_brief",
    "_sla_status",
]
