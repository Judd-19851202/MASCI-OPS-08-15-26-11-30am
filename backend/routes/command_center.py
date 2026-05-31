"""Executive Operations Command Center — Phase A backend.

Single read-only synthesis surface for Operations Leadership. Returns a
RAG-scored snapshot composed entirely from EXISTING collections — no
schema changes, no new workflows, no notifications, no fan-out.

Card surface (Phase A · slim per FINAL_PHASE_A_RECOMMENDATION.md):
    1. Jobs Today
    2. Safety Today
    3. Equipment Today
    4. Accountability Overdue
    5. Approvals Aging

Endpoints (all admin-strict):
    GET  /admin/command-center/snapshot          read snapshot
    GET  /admin/command-center/thresholds        read scoring config
    PATCH/admin/command-center/thresholds        update scoring config (audit-logged)
    GET  /admin/command-center/calendar          read working calendar config
    PATCH/admin/command-center/calendar          update calendar (audit-logged)
    GET  /admin/command-center/drilldown/{card}/{item_id}   per-item detail

Frozen-surface guarantee:
    - Imports nothing from singleton_scheduler / recovery_dashboard.
    - Emits zero notifications, zero emails, zero tasks.
    - Touches only two NEW collections (command_center_thresholds,
      command_center_calendar) plus reads of existing collections.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException


# ─── In-memory cache (15 sec like recovery_dashboard) ────────────────
_CACHE: Dict[str, Any] = {"computed_at": 0.0, "snapshot": None}
_CACHE_TTL_SECONDS = 15.0


# ─── Default scoring config (operator-tunable via /thresholds) ───────
DEFAULT_THRESHOLDS: Dict[str, Any] = {
    "_id": "command_center_thresholds",
    "version": 1,
    "rules": {
        # ── JOBS ──
        "JOBS-DR-MISSING": {
            "amber": 2, "red": 5,
            "lookback_hours": 36,
            "predicate": "Active jobs without a daily report filed in the last 36 working hours",
            "operational_risk": "Field activity invisible to leadership · accountability gap",
            "leadership_action": "PM contacts foreman · confirm work happened · refile DR if missed",
            "owner_role": "pm",
            "expected_resolution": "Same day (refile DR) or next business day",
        },
        "JOBS-ISSUE-NO-OWNER": {
            "amber": 1, "red": 1,
            "predicate": "Open incident OR open corrective action with no assigned owner",
            "operational_risk": "Active issue has no responsible party — silent escalation risk",
            "leadership_action": "Operations Director assigns owner immediately",
            "owner_role": "operations_leadership",
            "expected_resolution": "Within 24 hours of detection",
        },
        "JOBS-ISSUE-NO-PATH": {
            "amber": 1, "red": 3, "stale_days": 7,
            "predicate": "Open incident older than 7 days with no linked corrective action",
            "operational_risk": "Issue acknowledged but no resolution path documented",
            "leadership_action": "Safety + PM document corrective action or close incident",
            "owner_role": "safety",
            "expected_resolution": "Within 5 business days",
        },

        # ── SAFETY ──
        "SAF-CRITICAL-UNRESOLVED": {
            "amber_hours": 24, "red_hours": 48,
            "severities_critical": ["critical", "high", "serious"],
            "predicate": "High/Critical/Serious incident unresolved beyond age threshold",
            "operational_risk": "Personnel safety exposure · regulatory exposure",
            "leadership_action": "Safety lead briefs Operations Director · site visit if warranted",
            "owner_role": "safety",
            "expected_resolution": "Critical: 24h · High: 48h",
        },
        "SAF-OSHA-OPEN": {
            "red_hours": 24,
            "predicate": "OSHA-recordable incident open beyond 24 hours",
            "operational_risk": "OSHA reporting clock is running · noncompliance penalty risk",
            "leadership_action": "Confirm OSHA notification submitted · close internal record",
            "owner_role": "safety",
            "expected_resolution": "Within OSHA reporting window (8h fatality / 24h hospitalization)",
        },
        "SAF-CA-OVERDUE": {
            "amber": 1, "red": 3,
            "predicate": "Corrective actions past due_date",
            "operational_risk": "Documented hazards remain mitigated only on paper",
            "leadership_action": "Safety lead reassigns or closes overdue CAs",
            "owner_role": "safety",
            "expected_resolution": "Within 5 business days of detection",
        },
        "SAF-CA-CHRONIC": {
            "amber_days": 60,
            "predicate": "Corrective action open for more than 60 days regardless of due date",
            "operational_risk": "Long-running open finding signals broken closure workflow",
            "leadership_action": "Safety reviews CA · closes, extends, or escalates",
            "owner_role": "safety",
            "expected_resolution": "Within 10 business days of detection",
        },

        # ── EQUIPMENT ──
        "EQP-OOS-OLD": {
            "amber_hours": 24, "red_hours": 72,
            "predicate": "Out-of-service fleet defect open beyond age threshold",
            "operational_risk": "Equipment unavailable → crew idle / project delay / rental cost",
            "leadership_action": "Shop manager confirms parts/labor plan · Operations approves rental if needed",
            "owner_role": "shop",
            "expected_resolution": "OOS: 72h max · sooner if production-critical",
        },
        "EQP-OOS-NEW": {
            "red": 1,
            "predicate": "Newly out-of-service fleet defect with no shop acknowledgement in 24h",
            "operational_risk": "Defect reported but Shop has not engaged",
            "leadership_action": "Operations escalates directly to Shop Manager",
            "owner_role": "shop",
            "expected_resolution": "Acknowledgement within 24 hours of report",
        },
        "EQP-BACKLOG": {
            "amber": 10, "red": 20,
            "predicate": "Total open fleet defects (any severity)",
            "operational_risk": "Aggregate maintenance debt impacts fleet availability",
            "leadership_action": "Operations + Shop review weekly · staffing or vendor escalation",
            "owner_role": "shop",
            "expected_resolution": "Trend reduction over 30 days",
        },

        # ── ACCOUNTABILITY ──
        "ACC-HIGH-OVERDUE": {
            "amber": 3, "red": 8,
            "priorities_action_required": ["High", "Critical"],
            "predicate": "High or Critical priority tasks past their due_at",
            "operational_risk": "Action items the platform tracked but no one closed",
            "leadership_action": "Assignee or Admin triages queue · reassign or close",
            "owner_role": "varies_by_task",
            "expected_resolution": "Within 2 business days",
        },
        "ACC-STALE": {
            "red_days": 14,
            "priorities_action_required": ["High", "Critical"],
            "predicate": "High/Critical task overdue by more than 14 days",
            "operational_risk": "Long-stale critical task — workflow has broken down",
            "leadership_action": "Operations Director reviews individually · forces closure or escalation",
            "owner_role": "operations_leadership",
            "expected_resolution": "Within 5 business days of detection",
        },

        # ── APPROVALS ──
        "APP-AMBER": {
            "amber_days_min": 3, "amber_days_max": 4,
            "predicate": "PO request pending approval 3-4 days",
            "operational_risk": "Approaching the operationally-late threshold",
            "leadership_action": "Named approver decides or escalates within 24h",
            "owner_role": "approver_per_routing",
            "expected_resolution": "Within MASCI PO SLA (operator-tunable)",
        },
        "APP-RED": {
            "red_days_min": 5,
            "predicate": "PO request pending approval 5+ days",
            "operational_risk": "Operationally late · materials/work blocked",
            "leadership_action": "Operations Director forces decision or reassigns approver",
            "owner_role": "approver_per_routing",
            "expected_resolution": "Within 1 business day of detection",
        },
        "APP-WEEK": {
            "red_days_min": 7,
            "predicate": "PO request pending approval 7+ days",
            "operational_risk": "Severe approval breakdown · project impact likely",
            "leadership_action": "Executive intervention · approver reassignment",
            "owner_role": "operations_leadership",
            "expected_resolution": "Same day",
        },
    },
}

DEFAULT_CALENDAR: Dict[str, Any] = {
    "_id": "command_center_calendar",
    "version": 1,
    "timezone_offset_hours": -5,        # Eastern Standard default; operator-tunable
    "working_weekdays": [0, 1, 2, 3, 4], # Mon-Fri (Python weekday: Mon=0, Sun=6)
    "working_hour_start": 6,             # 06:00 local
    "working_hour_end": 18,              # 18:00 local
    "holidays": [],                      # ["YYYY-MM-DD", ...]
}


# ─── Helpers ─────────────────────────────────────────────────────────
def _parse_ts(v: Any) -> Optional[datetime]:
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str) and v:
        try:
            s = v.replace("Z", "+00:00") if v.endswith("Z") else v
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return None


def _hours_since(ts: Optional[datetime]) -> Optional[float]:
    if not ts:
        return None
    delta = datetime.now(timezone.utc) - ts
    return round(delta.total_seconds() / 3600.0, 2)


def _days_since(ts: Optional[datetime]) -> Optional[float]:
    h = _hours_since(ts)
    return None if h is None else round(h / 24.0, 2)


def _worst_pill(*pills: str) -> str:
    """Return the worst pill among inputs. RED > AMBER > GREEN."""
    if "RED" in pills:
        return "RED"
    if "AMBER" in pills:
        return "AMBER"
    return "GREEN"


def _fmt_age_hours(h: Optional[float]) -> str:
    if h is None:
        return "—"
    if h < 1:
        return "< 1h"
    if h < 48:
        return f"{int(round(h))}h"
    return f"{int(round(h / 24))}d"


# ─── Per-card builders ───────────────────────────────────────────────
async def _build_jobs_card(db: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Card 1: Jobs Today — missing deliverables · unowned issues · no resolution path."""
    warnings: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    # JOBS-DR-MISSING — active jobs without DR in last 36h
    r_dr = rules.get("JOBS-DR-MISSING", DEFAULT_THRESHOLDS["rules"]["JOBS-DR-MISSING"])
    lookback_hours = int(r_dr.get("lookback_hours", 36))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()
    active_jobs_cursor = db.jobs_master.find(
        {"$and": [
            {"$or": [{"status": {"$in": ["Active", "active", "Open", "open"]}},
                     {"status": {"$exists": False}},
                     {"status": None}]},
            {"project_number": {"$ne": None}},
        ]},
        {"_id": 0, "project_number": 1, "project_name": 1, "primary_pm_email": 1,
         "primary_pm_name": 1, "id": 1},
    )
    active_jobs = await active_jobs_cursor.to_list(length=500)

    dr_missing_count = 0
    dr_missing_examples: List[Dict[str, Any]] = []
    for job in active_jobs:
        pn = job.get("project_number")
        if not pn:
            continue
        recent_dr = await db.daily_reports.find_one(
            {"project_number": pn, "created_at": {"$gte": cutoff}},
            {"_id": 0, "id": 1},
        )
        if not recent_dr:
            dr_missing_count += 1
            if len(dr_missing_examples) < 5:
                dr_missing_examples.append({
                    "what_wrong": f"No daily report filed for {pn} in last {lookback_hours}h",
                    "why_red": f"Rule JOBS-DR-MISSING · threshold AMBER {r_dr['amber']} / RED {r_dr['red']}",
                    "owner": job.get("primary_pm_name") or job.get("primary_pm_email") or "Unassigned PM",
                    "current_status": "DR missing",
                    "eta": "Same day",
                    "drill_to": f"/admin/jobs?project_number={pn}",
                    "rule_id": "JOBS-DR-MISSING",
                    "severity": "amber" if dr_missing_count < r_dr["red"] else "red",
                })

    if dr_missing_count >= r_dr["red"]:
        warnings.append({"kind": "JOBS-DR-MISSING", "severity": "red",
                         "message": f"{dr_missing_count} active jobs without recent DR (RED ≥ {r_dr['red']})",
                         "item_count": dr_missing_count, "rule_id": "JOBS-DR-MISSING",
                         "owner": "pm", "drill_to": "/admin/jobs"})
    elif dr_missing_count >= r_dr["amber"]:
        warnings.append({"kind": "JOBS-DR-MISSING", "severity": "amber",
                         "message": f"{dr_missing_count} active jobs without recent DR (AMBER ≥ {r_dr['amber']})",
                         "item_count": dr_missing_count, "rule_id": "JOBS-DR-MISSING",
                         "owner": "pm", "drill_to": "/admin/jobs"})
    items.extend(dr_missing_examples)

    # JOBS-ISSUE-NO-OWNER — open incident or CA with no owner
    r_no_owner = rules.get("JOBS-ISSUE-NO-OWNER", DEFAULT_THRESHOLDS["rules"]["JOBS-ISSUE-NO-OWNER"])
    unowned_cas = await db.corrective_actions.find(
        {"status": {"$in": ["Open", "In Progress", "Pending Review"]},
         "$or": [{"assigned_to_name": None}, {"assigned_to_name": ""},
                 {"assigned_to_name": {"$exists": False}}]},
        {"_id": 0, "id": 1, "title": 1, "project_number": 1, "due_date": 1, "created_at": 1},
    ).limit(20).to_list(length=20)
    unowned_count = await db.corrective_actions.count_documents(
        {"status": {"$in": ["Open", "In Progress", "Pending Review"]},
         "$or": [{"assigned_to_name": None}, {"assigned_to_name": ""},
                 {"assigned_to_name": {"$exists": False}}]},
    )

    if unowned_count >= r_no_owner["red"]:
        warnings.append({"kind": "JOBS-ISSUE-NO-OWNER", "severity": "red",
                         "message": f"{unowned_count} open issue(s) without an assigned owner",
                         "item_count": unowned_count, "rule_id": "JOBS-ISSUE-NO-OWNER",
                         "owner": "operations_leadership", "drill_to": "/safety-portal/corrective-actions"})
        for ca in unowned_cas[:3]:
            items.append({
                "what_wrong": ca.get("title") or "Untitled corrective action",
                "why_red": "Rule JOBS-ISSUE-NO-OWNER · no assigned owner",
                "owner": "UNASSIGNED",
                "current_status": "Open · awaiting assignment",
                "eta": "Within 24 hours",
                "drill_to": f"/safety-portal/corrective-actions/{ca.get('id', '')}",
                "rule_id": "JOBS-ISSUE-NO-OWNER",
                "severity": "red",
            })

    # JOBS-ISSUE-NO-PATH — old incident with no CA linked
    r_no_path = rules.get("JOBS-ISSUE-NO-PATH", DEFAULT_THRESHOLDS["rules"]["JOBS-ISSUE-NO-PATH"])
    stale_days = int(r_no_path.get("stale_days", 7))
    cutoff_stale = (datetime.now(timezone.utc) - timedelta(days=stale_days)).isoformat()
    stale_incidents = await db.incidents.find(
        {"created_at": {"$lt": cutoff_stale}},
        {"_id": 0, "id": 1, "severity": 1, "created_at": 1, "project_number": 1,
         "doc_id": 1, "type_of_incident": 1},
        sort=[("created_at", -1)],
    ).limit(30).to_list(length=30)

    no_path_count = 0
    for inc in stale_incidents:
        inc_id = inc.get("id")
        if not inc_id:
            continue
        linked = await db.corrective_actions.find_one(
            {"$or": [{"source_id": inc_id}, {"incident_id": inc_id}]},
            {"_id": 0, "id": 1},
        )
        if not linked:
            no_path_count += 1
            if len(items) < 8 and no_path_count <= 3:
                age_d = _days_since(_parse_ts(inc.get("created_at")))
                items.append({
                    "what_wrong": f"Incident {inc.get('doc_id') or inc_id[:8]} open {int(age_d or 0)}d · no corrective action",
                    "why_red": f"Rule JOBS-ISSUE-NO-PATH · open > {stale_days}d without CA",
                    "owner": "Safety",
                    "current_status": "Open · no resolution path",
                    "eta": "Within 5 business days",
                    "drill_to": f"/admin/incidents/{inc_id}",
                    "rule_id": "JOBS-ISSUE-NO-PATH",
                    "severity": "amber" if no_path_count < r_no_path["red"] else "red",
                })

    if no_path_count >= r_no_path["red"]:
        warnings.append({"kind": "JOBS-ISSUE-NO-PATH", "severity": "red",
                         "message": f"{no_path_count} stale incidents without a documented resolution path",
                         "item_count": no_path_count, "rule_id": "JOBS-ISSUE-NO-PATH",
                         "owner": "safety", "drill_to": "/admin/incidents"})
    elif no_path_count >= r_no_path["amber"]:
        warnings.append({"kind": "JOBS-ISSUE-NO-PATH", "severity": "amber",
                         "message": f"{no_path_count} stale incidents without a documented resolution path",
                         "item_count": no_path_count, "rule_id": "JOBS-ISSUE-NO-PATH",
                         "owner": "safety", "drill_to": "/admin/incidents"})

    pill = _worst_pill(*(w["severity"].upper() for w in warnings)) if warnings else "GREEN"
    return {
        "card_id": "jobs",
        "title": "Jobs Today",
        "pill": pill,
        "headline_counts": {
            "dr_missing": dr_missing_count,
            "unowned_issues": unowned_count,
            "stale_incidents_no_path": no_path_count,
            "active_jobs_total": len(active_jobs),
        },
        "warnings": warnings,
        "items": items[:10],
    }


async def _build_safety_card(db: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Card 2: Safety Today — critical unresolved · OSHA open · CAs overdue · chronic."""
    warnings: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    # SAF-CRITICAL-UNRESOLVED
    r_crit = rules.get("SAF-CRITICAL-UNRESOLVED", DEFAULT_THRESHOLDS["rules"]["SAF-CRITICAL-UNRESOLVED"])
    crit_severities = [s.lower() for s in r_crit.get("severities_critical",
                                                      ["critical", "high", "serious"])]
    red_hours = int(r_crit.get("red_hours", 48))
    amber_hours = int(r_crit.get("amber_hours", 24))

    crit_incidents = await db.incidents.find(
        {"$expr": {"$in": [{"$toLower": {"$ifNull": ["$severity", ""]}}, crit_severities]}},
        {"_id": 0, "id": 1, "severity": 1, "created_at": 1, "doc_id": 1,
         "project_number": 1, "osha_recordable": 1, "type_of_incident": 1},
        sort=[("created_at", 1)],
    ).limit(50).to_list(length=50)

    crit_red_count = 0
    crit_amber_count = 0
    for inc in crit_incidents:
        ts = _parse_ts(inc.get("created_at"))
        if not ts:
            continue
        age_h = _hours_since(ts) or 0
        if age_h >= red_hours:
            crit_red_count += 1
            if len(items) < 8:
                items.append({
                    "what_wrong": f"{(inc.get('severity') or 'Unspecified').title()} incident {inc.get('doc_id') or 'unspecified'} open {_fmt_age_hours(age_h)}",
                    "why_red": f"Rule SAF-CRITICAL-UNRESOLVED · age ≥ {red_hours}h",
                    "owner": "Safety",
                    "current_status": "Open · unresolved",
                    "eta": "Critical: 24h · High: 48h",
                    "drill_to": f"/admin/incidents/{inc.get('id')}",
                    "rule_id": "SAF-CRITICAL-UNRESOLVED",
                    "severity": "red",
                })
        elif age_h >= amber_hours:
            crit_amber_count += 1

    if crit_red_count > 0:
        warnings.append({"kind": "SAF-CRITICAL-UNRESOLVED", "severity": "red",
                         "message": f"{crit_red_count} high/critical incident(s) unresolved past {red_hours}h",
                         "item_count": crit_red_count, "rule_id": "SAF-CRITICAL-UNRESOLVED",
                         "owner": "safety", "drill_to": "/admin/incidents"})
    elif crit_amber_count > 0:
        warnings.append({"kind": "SAF-CRITICAL-UNRESOLVED", "severity": "amber",
                         "message": f"{crit_amber_count} high/critical incident(s) approaching age threshold",
                         "item_count": crit_amber_count, "rule_id": "SAF-CRITICAL-UNRESOLVED",
                         "owner": "safety", "drill_to": "/admin/incidents"})

    # SAF-OSHA-OPEN
    r_osha = rules.get("SAF-OSHA-OPEN", DEFAULT_THRESHOLDS["rules"]["SAF-OSHA-OPEN"])
    osha_hours = int(r_osha.get("red_hours", 24))
    cutoff_osha = (datetime.now(timezone.utc) - timedelta(hours=osha_hours)).isoformat()
    osha_open = await db.incidents.count_documents({
        "osha_recordable": {"$regex": "^Yes$", "$options": "i"},
        "created_at": {"$lt": cutoff_osha},
    })
    if osha_open > 0:
        warnings.append({"kind": "SAF-OSHA-OPEN", "severity": "red",
                         "message": f"{osha_open} OSHA-recordable incident(s) open beyond {osha_hours}h",
                         "item_count": osha_open, "rule_id": "SAF-OSHA-OPEN",
                         "owner": "safety", "drill_to": "/admin/incidents?osha=yes"})
        osha_docs = await db.incidents.find(
            {"osha_recordable": {"$regex": "^Yes$", "$options": "i"},
             "created_at": {"$lt": cutoff_osha}},
            {"_id": 0, "id": 1, "doc_id": 1, "severity": 1, "created_at": 1},
            sort=[("created_at", 1)],
        ).limit(3).to_list(length=3)
        for o in osha_docs:
            items.append({
                "what_wrong": f"OSHA-recordable incident {o.get('doc_id') or 'unspecified'} open past 24h",
                "why_red": "Rule SAF-OSHA-OPEN · regulatory clock running",
                "owner": "Safety",
                "current_status": "Open · OSHA notification clock active",
                "eta": "Within OSHA reporting window",
                "drill_to": f"/admin/incidents/{o.get('id')}",
                "rule_id": "SAF-OSHA-OPEN",
                "severity": "red",
            })

    # SAF-CA-OVERDUE
    r_ca = rules.get("SAF-CA-OVERDUE", DEFAULT_THRESHOLDS["rules"]["SAF-CA-OVERDUE"])
    today = datetime.now(timezone.utc).isoformat()[:10]
    ca_overdue_count = await db.corrective_actions.count_documents({
        "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        "due_date": {"$ne": None, "$lt": today},
    })
    if ca_overdue_count >= r_ca["red"]:
        warnings.append({"kind": "SAF-CA-OVERDUE", "severity": "red",
                         "message": f"{ca_overdue_count} corrective action(s) past due date",
                         "item_count": ca_overdue_count, "rule_id": "SAF-CA-OVERDUE",
                         "owner": "safety", "drill_to": "/safety-portal/corrective-actions?status=overdue"})
    elif ca_overdue_count >= r_ca["amber"]:
        warnings.append({"kind": "SAF-CA-OVERDUE", "severity": "amber",
                         "message": f"{ca_overdue_count} corrective action(s) past due date",
                         "item_count": ca_overdue_count, "rule_id": "SAF-CA-OVERDUE",
                         "owner": "safety", "drill_to": "/safety-portal/corrective-actions?status=overdue"})
    if ca_overdue_count > 0:
        ca_docs = await db.corrective_actions.find(
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]},
             "due_date": {"$ne": None, "$lt": today}},
            {"_id": 0, "id": 1, "title": 1, "due_date": 1, "assigned_to_name": 1,
             "priority": 1, "status": 1},
            sort=[("due_date", 1)],
        ).limit(3).to_list(length=3)
        for ca in ca_docs:
            items.append({
                "what_wrong": ca.get("title") or "Untitled CA",
                "why_red": f"Rule SAF-CA-OVERDUE · due {ca.get('due_date')} · status {ca.get('status')}",
                "owner": ca.get("assigned_to_name") or "Unassigned",
                "current_status": ca.get("status") or "Open",
                "eta": "Within 5 business days",
                "drill_to": f"/safety-portal/corrective-actions/{ca.get('id')}",
                "rule_id": "SAF-CA-OVERDUE",
                "severity": "amber" if ca_overdue_count < r_ca["red"] else "red",
            })

    # SAF-CA-CHRONIC
    r_chronic = rules.get("SAF-CA-CHRONIC", DEFAULT_THRESHOLDS["rules"]["SAF-CA-CHRONIC"])
    chronic_days = int(r_chronic.get("amber_days", 60))
    cutoff_chronic = (datetime.now(timezone.utc) - timedelta(days=chronic_days)).isoformat()
    chronic_count = await db.corrective_actions.count_documents({
        "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        "created_at": {"$lt": cutoff_chronic},
    })
    if chronic_count >= r_chronic.get("amber", 1):
        warnings.append({"kind": "SAF-CA-CHRONIC", "severity": "amber",
                         "message": f"{chronic_count} corrective action(s) open more than {chronic_days} days",
                         "item_count": chronic_count, "rule_id": "SAF-CA-CHRONIC",
                         "owner": "safety", "drill_to": "/safety-portal/corrective-actions"})

    pill = _worst_pill(*(w["severity"].upper() for w in warnings)) if warnings else "GREEN"
    return {
        "card_id": "safety",
        "title": "Safety Today",
        "pill": pill,
        "headline_counts": {
            "critical_unresolved_red": crit_red_count,
            "critical_unresolved_amber": crit_amber_count,
            "osha_open": osha_open,
            "ca_overdue": ca_overdue_count,
            "ca_chronic": chronic_count,
        },
        "warnings": warnings,
        "items": items[:10],
    }


async def _build_equipment_card(db: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Card 3: Equipment Today — OOS old · OOS unacknowledged · backlog."""
    warnings: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    SEV_OOS = "oos"
    OPEN_STATES = ["open", "acknowledged"]

    # EQP-OOS-OLD
    r_old = rules.get("EQP-OOS-OLD", DEFAULT_THRESHOLDS["rules"]["EQP-OOS-OLD"])
    red_h = int(r_old.get("red_hours", 72))
    amber_h = int(r_old.get("amber_hours", 24))
    cutoff_red = (datetime.now(timezone.utc) - timedelta(hours=red_h)).isoformat()
    cutoff_amber = (datetime.now(timezone.utc) - timedelta(hours=amber_h)).isoformat()

    oos_red_count = await db.fleet_defects.count_documents(
        {"severity": SEV_OOS, "status": {"$in": OPEN_STATES},
         "created_at": {"$lt": cutoff_red}})
    oos_amber_count = await db.fleet_defects.count_documents(
        {"severity": SEV_OOS, "status": {"$in": OPEN_STATES},
         "created_at": {"$lt": cutoff_amber, "$gte": cutoff_red}})

    if oos_red_count > 0:
        warnings.append({"kind": "EQP-OOS-OLD", "severity": "red",
                         "message": f"{oos_red_count} unit(s) out-of-service for more than {red_h}h",
                         "item_count": oos_red_count, "rule_id": "EQP-OOS-OLD",
                         "owner": "shop", "drill_to": "/admin/equipment-inspections?status=oos"})
    elif oos_amber_count > 0:
        warnings.append({"kind": "EQP-OOS-OLD", "severity": "amber",
                         "message": f"{oos_amber_count} unit(s) OOS approaching {red_h}h threshold",
                         "item_count": oos_amber_count, "rule_id": "EQP-OOS-OLD",
                         "owner": "shop", "drill_to": "/admin/equipment-inspections?status=oos"})

    if oos_red_count + oos_amber_count > 0:
        oos_docs = await db.fleet_defects.find(
            {"severity": SEV_OOS, "status": {"$in": OPEN_STATES}},
            {"_id": 0, "id": 1, "truck_unit_number": 1, "trailer_unit_number": 1,
             "created_at": 1, "status": 1, "defect_text": 1, "defect_summary": 1},
            sort=[("created_at", 1)],
        ).limit(5).to_list(length=5)
        for d in oos_docs:
            age_h = _hours_since(_parse_ts(d.get("created_at")))
            unit = d.get("truck_unit_number") or d.get("trailer_unit_number") or "unspecified"
            sev_pill = "red" if (age_h or 0) >= red_h else "amber"
            items.append({
                "what_wrong": f"Unit {unit} OOS · {d.get('defect_summary') or d.get('defect_text') or 'see defect'}",
                "why_red": f"Rule EQP-OOS-OLD · OOS {_fmt_age_hours(age_h)}",
                "owner": "Shop",
                "current_status": d.get("status") or "open",
                "eta": "≤72h · sooner if production-critical",
                "drill_to": f"/admin/equipment?defect_id={d.get('id', '')}",
                "rule_id": "EQP-OOS-OLD",
                "severity": sev_pill,
            })

    # EQP-OOS-NEW (any OOS defect created in last 24h with status=open, no shop ack)
    new_oos_unack = await db.fleet_defects.count_documents({
        "severity": SEV_OOS,
        "status": "open",
        "created_at": {"$gte": cutoff_amber},
    })
    if new_oos_unack > 0:
        warnings.append({"kind": "EQP-OOS-NEW", "severity": "red",
                         "message": f"{new_oos_unack} newly OOS defect(s) without Shop acknowledgement",
                         "item_count": new_oos_unack, "rule_id": "EQP-OOS-NEW",
                         "owner": "shop", "drill_to": "/admin/equipment-inspections?status=oos&unack=true"})

    # EQP-BACKLOG
    r_bk = rules.get("EQP-BACKLOG", DEFAULT_THRESHOLDS["rules"]["EQP-BACKLOG"])
    backlog_total = await db.fleet_defects.count_documents({"status": {"$in": OPEN_STATES}})
    if backlog_total >= r_bk["red"]:
        warnings.append({"kind": "EQP-BACKLOG", "severity": "red",
                         "message": f"Open defect backlog: {backlog_total} units (RED ≥ {r_bk['red']})",
                         "item_count": backlog_total, "rule_id": "EQP-BACKLOG",
                         "owner": "shop", "drill_to": "/admin/equipment-inspections"})
    elif backlog_total >= r_bk["amber"]:
        warnings.append({"kind": "EQP-BACKLOG", "severity": "amber",
                         "message": f"Open defect backlog: {backlog_total} units (AMBER ≥ {r_bk['amber']})",
                         "item_count": backlog_total, "rule_id": "EQP-BACKLOG",
                         "owner": "shop", "drill_to": "/admin/equipment-inspections"})

    pill = _worst_pill(*(w["severity"].upper() for w in warnings)) if warnings else "GREEN"
    return {
        "card_id": "equipment",
        "title": "Equipment Today",
        "pill": pill,
        "headline_counts": {
            "oos_red": oos_red_count,
            "oos_amber": oos_amber_count,
            "new_oos_unack": new_oos_unack,
            "backlog_total": backlog_total,
        },
        "warnings": warnings,
        "items": items[:10],
    }


async def _build_accountability_card(db: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Card 4: Accountability Overdue — high/critical tasks past due."""
    warnings: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    r_h = rules.get("ACC-HIGH-OVERDUE", DEFAULT_THRESHOLDS["rules"]["ACC-HIGH-OVERDUE"])
    r_s = rules.get("ACC-STALE", DEFAULT_THRESHOLDS["rules"]["ACC-STALE"])
    action_priorities = r_h.get("priorities_action_required", ["High", "Critical"])

    now_iso = datetime.now(timezone.utc).isoformat()
    overdue_count = await db.tasks.count_documents({
        "priority": {"$in": action_priorities},
        "status": {"$in": ["Open", "In Progress"]},
        "due_at": {"$ne": None, "$lt": now_iso},
    })

    stale_days = int(r_s.get("red_days", 14))
    cutoff_stale = (datetime.now(timezone.utc) - timedelta(days=stale_days)).isoformat()
    stale_count = await db.tasks.count_documents({
        "priority": {"$in": action_priorities},
        "status": {"$in": ["Open", "In Progress"]},
        "due_at": {"$ne": None, "$lt": cutoff_stale},
    })

    if overdue_count >= r_h["red"]:
        warnings.append({"kind": "ACC-HIGH-OVERDUE", "severity": "red",
                         "message": f"{overdue_count} high/critical tasks overdue (RED ≥ {r_h['red']})",
                         "item_count": overdue_count, "rule_id": "ACC-HIGH-OVERDUE",
                         "owner": "varies", "drill_to": "/tasks?priority=High,Critical&status=Open"})
    elif overdue_count >= r_h["amber"]:
        warnings.append({"kind": "ACC-HIGH-OVERDUE", "severity": "amber",
                         "message": f"{overdue_count} high/critical tasks overdue (AMBER ≥ {r_h['amber']})",
                         "item_count": overdue_count, "rule_id": "ACC-HIGH-OVERDUE",
                         "owner": "varies", "drill_to": "/tasks?priority=High,Critical&status=Open"})

    if stale_count > 0:
        warnings.append({"kind": "ACC-STALE", "severity": "red",
                         "message": f"{stale_count} high/critical task(s) overdue more than {stale_days}d",
                         "item_count": stale_count, "rule_id": "ACC-STALE",
                         "owner": "operations_leadership", "drill_to": "/tasks?stale=true"})

    if overdue_count > 0:
        task_docs = await db.tasks.find(
            {"priority": {"$in": action_priorities},
             "status": {"$in": ["Open", "In Progress"]},
             "due_at": {"$ne": None, "$lt": now_iso}},
            {"_id": 0, "id": 1, "title": 1, "priority": 1, "status": 1,
             "due_at": 1, "assignee_role": 1, "assignee_user_id": 1, "kind": 1},
            sort=[("due_at", 1)],
        ).limit(5).to_list(length=5)
        for t in task_docs:
            age_h = _hours_since(_parse_ts(t.get("due_at")))
            owner_disp = (t.get("assignee_role") or "unassigned").capitalize()
            sev = "red" if (age_h or 0) >= stale_days * 24 else (
                "red" if overdue_count >= r_h["red"] else "amber")
            items.append({
                "what_wrong": t.get("title") or f"Task {t.get('id', '')[:8]}",
                "why_red": f"Rule ACC-HIGH-OVERDUE · overdue {_fmt_age_hours(age_h)}",
                "owner": owner_disp,
                "current_status": t.get("status") or "Open",
                "eta": "Within 2 business days",
                "drill_to": f"/tasks/{t.get('id', '')}",
                "rule_id": "ACC-STALE" if (age_h or 0) >= stale_days * 24 else "ACC-HIGH-OVERDUE",
                "severity": sev,
            })

    pill = _worst_pill(*(w["severity"].upper() for w in warnings)) if warnings else "GREEN"
    return {
        "card_id": "accountability",
        "title": "Accountability Overdue",
        "pill": pill,
        "headline_counts": {
            "high_priority_overdue": overdue_count,
            "stale_over_threshold": stale_count,
        },
        "warnings": warnings,
        "items": items[:10],
    }


async def _build_approvals_card(db: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
    """Card 5: Approvals Aging — POs pending approval."""
    warnings: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    r_amber = rules.get("APP-AMBER", DEFAULT_THRESHOLDS["rules"]["APP-AMBER"])
    r_red = rules.get("APP-RED", DEFAULT_THRESHOLDS["rules"]["APP-RED"])
    r_week = rules.get("APP-WEEK", DEFAULT_THRESHOLDS["rules"]["APP-WEEK"])

    amber_min = int(r_amber.get("amber_days_min", 3))
    amber_max = int(r_amber.get("amber_days_max", 4))
    red_min = int(r_red.get("red_days_min", 5))
    week_min = int(r_week.get("red_days_min", 7))

    cutoff_amber_start = (datetime.now(timezone.utc) - timedelta(days=amber_max + 1)).isoformat()
    cutoff_amber_end = (datetime.now(timezone.utc) - timedelta(days=amber_min)).isoformat()
    cutoff_red = (datetime.now(timezone.utc) - timedelta(days=red_min)).isoformat()
    cutoff_week = (datetime.now(timezone.utc) - timedelta(days=week_min)).isoformat()

    pending_statuses = ["Pending Approval", "Submitted", "Clarification Needed"]

    amber_count = await db.po_requests.count_documents({
        "status": {"$in": pending_statuses},
        "created_at": {"$lte": cutoff_amber_end, "$gt": cutoff_amber_start},
    })
    red_count = await db.po_requests.count_documents({
        "status": {"$in": pending_statuses},
        "created_at": {"$lte": cutoff_red},
    })
    week_count = await db.po_requests.count_documents({
        "status": {"$in": pending_statuses},
        "created_at": {"$lte": cutoff_week},
    })

    if week_count > 0:
        warnings.append({"kind": "APP-WEEK", "severity": "red",
                         "message": f"{week_count} PO(s) pending approval 7+ days · executive intervention",
                         "item_count": week_count, "rule_id": "APP-WEEK",
                         "owner": "operations_leadership", "drill_to": "/po-requests?status=pending&age=7"})
    if red_count > 0:
        warnings.append({"kind": "APP-RED", "severity": "red",
                         "message": f"{red_count} PO(s) pending approval 5+ days (operationally late)",
                         "item_count": red_count, "rule_id": "APP-RED",
                         "owner": "approver", "drill_to": "/po-requests?status=pending&age=5"})
    elif amber_count > 0:
        warnings.append({"kind": "APP-AMBER", "severity": "amber",
                         "message": f"{amber_count} PO(s) pending approval {amber_min}-{amber_max} days",
                         "item_count": amber_count, "rule_id": "APP-AMBER",
                         "owner": "approver", "drill_to": "/po-requests?status=pending&age=3"})

    # Surface the 5 oldest pending POs for the drill list
    po_docs = await db.po_requests.find(
        {"status": {"$in": pending_statuses}},
        {"_id": 0, "id": 1, "vendor": 1, "description": 1, "estimated_amount": 1,
         "status": 1, "created_at": 1, "requested_by_name": 1, "urgency": 1,
         "project_number": 1, "doc_id": 1},
        sort=[("created_at", 1)],
    ).limit(5).to_list(length=5)
    for p in po_docs:
        age_h = _hours_since(_parse_ts(p.get("created_at")))
        age_d = (age_h or 0) / 24.0
        if age_d >= week_min:
            sev = "red"
            rule = "APP-WEEK"
        elif age_d >= red_min:
            sev = "red"
            rule = "APP-RED"
        elif age_d >= amber_min:
            sev = "amber"
            rule = "APP-AMBER"
        else:
            continue
        items.append({
            "what_wrong": f"PO {p.get('doc_id') or p.get('id', '')[:8]} · {p.get('vendor', '—')} · ${p.get('estimated_amount', 0):,.0f}",
            "why_red": f"Rule {rule} · pending {int(age_d)}d · status {p.get('status')}",
            "owner": p.get("requested_by_name") or "Requester",
            "current_status": p.get("status") or "Pending",
            "eta": "Within MASCI PO SLA",
            "drill_to": f"/po-requests/{p.get('id', '')}",
            "rule_id": rule,
            "severity": sev,
        })

    pill = _worst_pill(*(w["severity"].upper() for w in warnings)) if warnings else "GREEN"
    return {
        "card_id": "approvals",
        "title": "Approvals Aging",
        "pill": pill,
        "headline_counts": {
            "pending_amber": amber_count,
            "pending_red": red_count,
            "pending_week_plus": week_count,
        },
        "warnings": warnings,
        "items": items[:10],
    }


# ─── Snapshot composer ───────────────────────────────────────────────
async def _load_thresholds(db: Any) -> Dict[str, Any]:
    doc = await db.command_center_thresholds.find_one({"_id": "command_center_thresholds"})
    if not doc:
        return DEFAULT_THRESHOLDS["rules"]
    return doc.get("rules") or DEFAULT_THRESHOLDS["rules"]


async def _load_calendar(db: Any) -> Dict[str, Any]:
    doc = await db.command_center_calendar.find_one({"_id": "command_center_calendar"})
    if not doc:
        return {k: v for k, v in DEFAULT_CALENDAR.items() if k != "_id"}
    doc.pop("_id", None)
    return doc


async def _seed_defaults(db: Any) -> None:
    """Idempotent seed of the threshold + calendar config docs."""
    existing = await db.command_center_thresholds.find_one({"_id": "command_center_thresholds"})
    if not existing:
        await db.command_center_thresholds.insert_one(dict(DEFAULT_THRESHOLDS))
    existing_cal = await db.command_center_calendar.find_one({"_id": "command_center_calendar"})
    if not existing_cal:
        await db.command_center_calendar.insert_one(dict(DEFAULT_CALENDAR))


def build_command_center_router(
    db: Any,
    require_admin_strict_dep: Any,
) -> APIRouter:
    """Factory mirroring recovery_dashboard pattern. Caller passes the live
    `db` handle and the admin-strict auth dep."""
    router = APIRouter()

    @router.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - exercised at app boot
        try:
            await _seed_defaults(db)
        except Exception:
            pass  # silent: not blocking app boot if seeding fails

    @router.get("/admin/command-center/snapshot")
    async def snapshot(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        now_wall = time.time()
        if _CACHE["snapshot"] is not None and (now_wall - _CACHE["computed_at"]) < _CACHE_TTL_SECONDS:
            cached = dict(_CACHE["snapshot"])
            cached["cached"] = True
            return cached

        # Seed defaults on first call too (covers fresh DBs).
        await _seed_defaults(db)
        rules = await _load_thresholds(db)
        calendar = await _load_calendar(db)

        jobs_card = await _build_jobs_card(db, rules)
        safety_card = await _build_safety_card(db, rules)
        equipment_card = await _build_equipment_card(db, rules)
        accountability_card = await _build_accountability_card(db, rules)
        approvals_card = await _build_approvals_card(db, rules)

        cards = [jobs_card, safety_card, equipment_card, accountability_card, approvals_card]
        overall_pill = _worst_pill(*(c["pill"] for c in cards))

        # Headline aggregate
        red_warn_total = sum(1 for c in cards for w in c["warnings"] if w["severity"] == "red")
        amber_warn_total = sum(1 for c in cards for w in c["warnings"] if w["severity"] == "amber")
        red_item_total = sum(1 for c in cards for it in c["items"] if it.get("severity") == "red")
        amber_item_total = sum(1 for c in cards for it in c["items"] if it.get("severity") == "amber")

        snapshot_doc = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "pill": overall_pill,
            "pulse": {
                "pill": overall_pill,
                "red_warnings": red_warn_total,
                "amber_warnings": amber_warn_total,
                "red_items": red_item_total,
                "amber_items": amber_item_total,
                "headline": (
                    f"{red_warn_total} RED · {amber_warn_total} AMBER warnings"
                    if (red_warn_total + amber_warn_total) > 0
                    else "All five operational signals GREEN"
                ),
            },
            "cards": cards,
            "calendar": calendar,
            "cached": False,
        }

        _CACHE["snapshot"] = snapshot_doc
        _CACHE["computed_at"] = now_wall
        return snapshot_doc

    @router.get("/admin/command-center/thresholds")
    async def get_thresholds(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        await _seed_defaults(db)
        doc = await db.command_center_thresholds.find_one(
            {"_id": "command_center_thresholds"}, {"_id": 0})
        return doc or {k: v for k, v in DEFAULT_THRESHOLDS.items() if k != "_id"}

    @router.patch("/admin/command-center/thresholds")
    async def patch_thresholds(
        payload: Dict[str, Any] = Body(...),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        new_rules = payload.get("rules")
        if not isinstance(new_rules, dict) or not new_rules:
            raise HTTPException(status_code=400, detail="payload.rules must be a non-empty dict")
        await _seed_defaults(db)
        existing = await db.command_center_thresholds.find_one(
            {"_id": "command_center_thresholds"}) or {}
        merged = dict(existing.get("rules") or {})
        for k, v in new_rules.items():
            if isinstance(v, dict):
                merged[k] = {**(merged.get(k) or {}), **v}
        new_version = int(existing.get("version", 0)) + 1
        await db.command_center_thresholds.update_one(
            {"_id": "command_center_thresholds"},
            {"$set": {"rules": merged, "version": new_version,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        # audit
        try:
            await db.admin_audit.insert_one({
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "command_center.thresholds.update",
                "version": new_version,
                "changed_keys": list(new_rules.keys()),
            })
        except Exception:
            pass
        # invalidate cache
        _CACHE["snapshot"] = None
        return {"ok": True, "version": new_version, "rules_count": len(merged)}

    @router.get("/admin/command-center/calendar")
    async def get_calendar(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        await _seed_defaults(db)
        doc = await db.command_center_calendar.find_one(
            {"_id": "command_center_calendar"}, {"_id": 0})
        return doc or {k: v for k, v in DEFAULT_CALENDAR.items() if k != "_id"}

    @router.patch("/admin/command-center/calendar")
    async def patch_calendar(
        payload: Dict[str, Any] = Body(...),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        allowed = {"timezone_offset_hours", "working_weekdays", "working_hour_start",
                   "working_hour_end", "holidays"}
        update = {k: v for k, v in payload.items() if k in allowed}
        if not update:
            raise HTTPException(status_code=400, detail="no allowed calendar fields in payload")
        await _seed_defaults(db)
        existing = await db.command_center_calendar.find_one(
            {"_id": "command_center_calendar"}) or {}
        new_version = int(existing.get("version", 0)) + 1
        update["version"] = new_version
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.command_center_calendar.update_one(
            {"_id": "command_center_calendar"}, {"$set": update})
        try:
            await db.admin_audit.insert_one({
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "command_center.calendar.update",
                "version": new_version,
                "changed_keys": list(update.keys()),
            })
        except Exception:
            pass
        _CACHE["snapshot"] = None
        return {"ok": True, "version": new_version}

    @router.get("/admin/command-center/drilldown/{card_id}/{item_id}")
    async def drilldown(
        card_id: str,
        item_id: str,
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        """Return the 5-question payload (what · why · who · status · eta) for an item.

        Sources from existing collections by card_id. Does not invent data.
        """
        if card_id == "jobs":
            doc = await db.jobs_master.find_one({"id": item_id}, {"_id": 0}) or \
                  await db.incidents.find_one({"id": item_id}, {"_id": 0}) or \
                  await db.corrective_actions.find_one({"id": item_id}, {"_id": 0})
        elif card_id == "safety":
            doc = await db.incidents.find_one({"id": item_id}, {"_id": 0}) or \
                  await db.corrective_actions.find_one({"id": item_id}, {"_id": 0})
        elif card_id == "equipment":
            doc = await db.fleet_defects.find_one({"id": item_id}, {"_id": 0})
        elif card_id == "accountability":
            doc = await db.tasks.find_one({"id": item_id}, {"_id": 0})
        elif card_id == "approvals":
            doc = await db.po_requests.find_one({"id": item_id}, {"_id": 0})
        else:
            raise HTTPException(status_code=400, detail=f"unknown card_id {card_id}")

        if not doc:
            raise HTTPException(status_code=404, detail=f"{card_id}/{item_id} not found")

        return {
            "card_id": card_id,
            "item_id": item_id,
            "source_doc": doc,
            "actions_underway": doc.get("status") or doc.get("state") or "see source",
            "owner": (
                doc.get("assigned_to_name") or doc.get("assignee_user_id") or
                doc.get("requested_by_name") or doc.get("primary_pm_name") or
                doc.get("assignee_role") or "Unassigned"
            ),
            "expected_resolution": doc.get("due_date") or doc.get("due_at") or "Not set",
        }

    return router
