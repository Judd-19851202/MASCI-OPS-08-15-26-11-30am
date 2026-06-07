"""
routes/notifications.py — Phase 2 P1 · Operational Intelligence Notifications.

Role-scoped digest engine. Generates a per-role "today's intelligence"
payload from the existing detector findings + lifecycle state. No new
source-of-truth collections — purely an aggregation + presentation layer
over what iter354-356 already detects.

Endpoints (in this iteration — Admin + Safety roles):
- GET /api/admin/notifications/digest      (admin-strict)
- GET /api/safety/notifications/digest     (safety or admin token)

Pattern is intentionally extensible — adding HR, PM, Dispatch, FL digests
is mechanical: write a `_build_<role>_digest(db, scope_user=None)` function
that returns the same payload shape and wire it onto the existing portal
token gate.

Payload shape (every role returns the same envelope):
{
  ok: true,
  role: "admin",
  generated_at: ISO timestamp,
  summary: { critical: int, high: int, medium: int, low: int,
             total_open: int, score: int|null, score_label: str|null },
  sections: [
    {
      key: "governance_score",
      severity: "info" | "high" | "critical",
      title: "Governance score dropped by 12 points overnight",
      body: "...",
      count: 1,
      action_url: "/admin/governance",
      rule_ids: ["..."] (optional),
      items: [ ... up to 5 sample finding rows ... ]
    },
    ...
  ],
}
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).isoformat()[:10]


async def _count_open_findings(db, rule_id: str) -> int:
    return await db["compliance_findings"].count_documents({
        "rule_id": rule_id,
        "status": {"$in": ["open", "acknowledged"]},
    })


async def _sample_open_findings(
    db, rule_ids: List[str], limit: int = 5,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not rule_ids:
        return rows
    cursor = db["compliance_findings"].find(
        {"rule_id": {"$in": rule_ids},
         "status": {"$in": ["open", "acknowledged"]}},
        {"_id": 0, "id": 1, "rule_id": 1, "severity": 1, "title": 1,
         "entity_name": 1, "description": 1, "last_detected_at": 1},
    ).sort("last_detected_at", -1).limit(limit)
    async for row in cursor:
        rows.append(row)
    return rows


def _severity_total(severity_counts: Dict[str, int]) -> int:
    return sum(int(v or 0) for v in severity_counts.values())


# ---------------------------------------------------------------------------
# ADMIN DIGEST
# ---------------------------------------------------------------------------

async def _build_admin_digest(db) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    # Latest scan + previous scan for governance-score delta.
    scans_cursor = db["compliance_scans"].find(
        {}, {"_id": 0}
    ).sort("started_at", -1).limit(2)
    scans = [row async for row in scans_cursor]
    latest = scans[0] if scans else None
    previous = scans[1] if len(scans) > 1 else None

    # Governance summary (mirror logic from /admin/governance/summary).
    sev_counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    async for row in db["compliance_findings"].aggregate([
        {"$match": {"status": {"$in": ["open", "acknowledged"]}}},
        {"$group": {"_id": "$severity", "n": {"$sum": 1}}},
    ]):
        sev_counts[row["_id"] or "info"] = row["n"]
    score = 100
    score -= 20 * sev_counts["critical"]
    score -= 8 * sev_counts["high"]
    score -= 3 * sev_counts["medium"]
    score -= 1 * sev_counts["low"]
    score = max(0, min(100, score))
    if score >= 90:
        label = "healthy"
    elif score >= 70:
        label = "fair"
    elif score >= 40:
        label = "degraded"
    else:
        label = "critical"

    # Section 1 · Score banner (always present).
    score_body = (
        f"Convergence score is {score}/100 ({label}). "
        f"{sev_counts['critical']} critical · {sev_counts['high']} high · "
        f"{sev_counts['medium']} medium · {sev_counts['low']} low open findings."
    )
    if previous and latest:
        # Re-derive previous open-counts implicitly via the previous scan's
        # severity_counts.
        prev_sev = previous.get("severity_counts") or {}
        prev_open = _severity_total(prev_sev)
        cur_open = sev_counts["critical"] + sev_counts["high"] + sev_counts["medium"] + sev_counts["low"]
        delta = cur_open - prev_open
        if abs(delta) >= 1:
            score_body += (
                f" Δ vs previous scan ({previous.get('finished_at', '')[:16].replace('T', ' ')}): "
                f"{'+' if delta > 0 else ''}{delta} open finding(s)."
            )

    sections.append({
        "key": "governance_score",
        "severity": ("critical" if label == "critical" else
                     "high" if label == "degraded" else
                     "medium" if label == "fair" else "info"),
        "title": f"Governance score · {score}/100 · {label}",
        "body": score_body,
        "count": 1,
        "action_url": "/admin/governance",
    })

    # Section 2 · Critical findings (top 5).
    if sev_counts["critical"] > 0:
        crit_items = []
        cursor = db["compliance_findings"].find(
            {"status": {"$in": ["open", "acknowledged"]}, "severity": "critical"},
            {"_id": 0, "id": 1, "rule_id": 1, "severity": 1, "title": 1,
             "entity_name": 1, "description": 1, "last_detected_at": 1},
        ).sort("last_detected_at", -1).limit(5)
        async for row in cursor:
            crit_items.append(row)
        sections.append({
            "key": "critical_findings",
            "severity": "critical",
            "title": f"{sev_counts['critical']} critical finding(s) open",
            "body": "Highest-priority compliance contradictions awaiting acknowledgment or resolution.",
            "count": sev_counts["critical"],
            "action_url": "/admin/compliance-findings?severity=critical",
            "items": crit_items,
        })

    # Section 3 · Linkage failures (high severity — identity drift).
    linkage_open = (
        await _count_open_findings(db, "EMP_LINK_UNRESOLVABLE")
        + await _count_open_findings(db, "EMP_LINK_AMBIGUOUS")
    )
    if linkage_open > 0:
        sections.append({
            "key": "linkage_failures",
            "severity": "high",
            "title": f"{linkage_open} employee-linkage failure(s)",
            "body": "Operational records reference employee names that don't match the master, or match more than one active employee. Use the Backfill panel for the easy ones; the rest need manual disambiguation.",
            "count": linkage_open,
            "action_url": "/admin/compliance-findings?category=linkage",
            "rule_ids": ["EMP_LINK_UNRESOLVABLE", "EMP_LINK_AMBIGUOUS"],
            "items": await _sample_open_findings(
                db, ["EMP_LINK_UNRESOLVABLE", "EMP_LINK_AMBIGUOUS"], 5,
            ),
        })

    # Section 4 · Lifecycle continuity (severe incidents without CAPAs).
    needs_capa = await _count_open_findings(db, "INC_NEEDS_CAPA")
    if needs_capa > 0:
        sections.append({
            "key": "incident_lifecycle",
            "severity": "critical",
            "title": f"{needs_capa} severe incident(s) with no CAPA",
            "body": "High / Critical / OSHA-recordable incidents that have not yet spawned a corrective action. Safety must open a CAPA before these incidents can be closed.",
            "count": needs_capa,
            "action_url": "/admin/compliance-findings?rule_id=INC_NEEDS_CAPA",
            "rule_ids": ["INC_NEEDS_CAPA"],
            "items": await _sample_open_findings(db, ["INC_NEEDS_CAPA"], 5),
        })

    # Section 5 · Last scan freshness.
    if latest:
        finished = latest.get("finished_at") or ""
        try:
            ts = datetime.fromisoformat(finished.replace("Z", "+00:00"))
            stale = datetime.now(timezone.utc) - ts > timedelta(hours=36)
        except Exception:
            stale = True
        if stale:
            sections.append({
                "key": "scan_freshness",
                "severity": "medium",
                "title": "Compliance scan is stale",
                "body": f"Last successful scan finished {finished[:19].replace('T',' ')}. Trigger a fresh scan from /admin/governance to refresh signal.",
                "count": 1,
                "action_url": "/admin/governance",
            })

    return {
        "ok": True,
        "role": "admin",
        "generated_at": _now_iso(),
        "summary": {
            **sev_counts,
            "total_open": (sev_counts["critical"] + sev_counts["high"]
                           + sev_counts["medium"] + sev_counts["low"]),
            "score": score,
            "score_label": label,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# SAFETY DIGEST
# ---------------------------------------------------------------------------

async def _build_safety_digest(db) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    # 1 · Overdue CAPAs
    overdue = await _count_open_findings(db, "CAPA_OVERDUE")
    if overdue > 0:
        sections.append({
            "key": "capa_overdue",
            "severity": "high",
            "title": f"{overdue} CAPA(s) past due date",
            "body": "Corrective actions whose due_date has elapsed but status is still open. Owner must move them forward to Pending Review, Verified, or Closed.",
            "count": overdue,
            "action_url": "/safety-portal/corrective-actions?tab=Overdue",
            "rule_ids": ["CAPA_OVERDUE"],
            "items": await _sample_open_findings(db, ["CAPA_OVERDUE"], 5),
        })

    # 2 · Severe incidents needing CAPAs
    needs_capa = await _count_open_findings(db, "INC_NEEDS_CAPA")
    if needs_capa > 0:
        sections.append({
            "key": "incidents_needing_capa",
            "severity": "critical",
            "title": f"{needs_capa} severe incident(s) need a CAPA",
            "body": "High / Critical / OSHA-recordable incidents do not have a corrective action linked. Open one before the incident is closed (the lifecycle gate now blocks closeout without a verified CAPA).",
            "count": needs_capa,
            "action_url": "/safety-portal/incidents",
            "rule_ids": ["INC_NEEDS_CAPA"],
            "items": await _sample_open_findings(db, ["INC_NEEDS_CAPA"], 5),
        })

    # 3 · CAPAs stuck in Pending Review
    pending_stuck = await _count_open_findings(db, "CAPA_AWAITING_VERIFICATION")
    if pending_stuck > 0:
        sections.append({
            "key": "capa_awaiting_verification",
            "severity": "medium",
            "title": f"{pending_stuck} CAPA(s) waiting for verification",
            "body": "A second reviewer needs to inspect the corrective work and advance the CAPA from Pending Review to Verified. After verification, the original owner can close it.",
            "count": pending_stuck,
            "action_url": "/safety-portal/corrective-actions?tab=Pending+Review",
            "rule_ids": ["CAPA_AWAITING_VERIFICATION"],
            "items": await _sample_open_findings(db, ["CAPA_AWAITING_VERIFICATION"], 5),
        })

    # 4 · CAPAs with no owner
    no_owner = await _count_open_findings(db, "CAPA_NO_OWNER")
    if no_owner > 0:
        sections.append({
            "key": "capa_no_owner",
            "severity": "medium",
            "title": f"{no_owner} CAPA(s) have no owner",
            "body": "Active CAPAs must have a named owner before moving to Pending Review. Assign one or close as no-action-required with a transition note.",
            "count": no_owner,
            "action_url": "/safety-portal/corrective-actions",
            "rule_ids": ["CAPA_NO_OWNER"],
            "items": await _sample_open_findings(db, ["CAPA_NO_OWNER"], 5),
        })

    # 5 · Incident closed but CAPA still open
    closed_open = await _count_open_findings(db, "INC_CLOSED_CAPA_OPEN")
    if closed_open > 0:
        sections.append({
            "key": "incident_closed_capa_open",
            "severity": "high",
            "title": f"{closed_open} incident(s) closed with CAPA still open",
            "body": "These incidents were closed but their corrective action chain is still unresolved. Re-open the CAPA workflow or document why the loose end is acceptable.",
            "count": closed_open,
            "action_url": "/admin/compliance-findings?rule_id=INC_CLOSED_CAPA_OPEN",
            "rule_ids": ["INC_CLOSED_CAPA_OPEN"],
            "items": await _sample_open_findings(db, ["INC_CLOSED_CAPA_OPEN"], 5),
        })

    # 6 · Training expirations
    trn_expired = await _count_open_findings(db, "TRN_EXPIRED")
    if trn_expired > 0:
        sections.append({
            "key": "training_expired",
            "severity": "high",
            "title": f"{trn_expired} employee(s) have expired training records",
            "body": "Active employees whose required training certifications have lapsed. Each one is a potential OSHA / DOT exposure.",
            "count": trn_expired,
            "action_url": "/admin/compliance-findings?rule_id=TRN_EXPIRED",
            "rule_ids": ["TRN_EXPIRED"],
            "items": await _sample_open_findings(db, ["TRN_EXPIRED"], 5),
        })

    # 7 · Trench Safety section (Phase 7.5C)
    try:
        from routes.trench_safety.notifications import build_trench_digest_section  # noqa: PLC0415
        ts = await build_trench_digest_section(db)
        ts_total = sum(
            int(ts.get(k) or 0) for k in (
                "open_safety_holds", "open_certification_holds",
                "repairs_awaiting_verification", "new_damage_reports_7d",
                "failed_inspections_7d", "expiring_certifications_30d",
            )
        )
        # Always emit the section so Trench Safety is visible in the digest,
        # even when counts are all zero (per directive — digest integration
        # must be present).
        sections.append({
            "key": "trench_safety",
            "severity": "high" if ts.get("open_safety_holds", 0) > 0 else "medium",
            "title": f"Trench Safety — {ts_total} item(s) requiring attention",
            "body": (
                f"Open Safety Holds: {ts['open_safety_holds']} · "
                f"Cert Holds: {ts['open_certification_holds']} · "
                f"Inspection Holds: {ts['open_inspection_holds']} · "
                f"Repairs awaiting verification: {ts['repairs_awaiting_verification']} · "
                f"Expiring certs (30d): {ts['expiring_certifications_30d']} · "
                f"New damage reports (7d): {ts['new_damage_reports_7d']} · "
                f"Failed inspections (7d): {ts['failed_inspections_7d']}"
            ),
            "count": ts_total,
            "action_url": "/safety/trench-safety",
            "rule_ids": ["TRENCH_SAFETY_OPEN_WORK"],
            "items": [],
            "trench_safety": ts,
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[notifications-digest] trench section failed: {e}")

    total = sum(s["count"] for s in sections)

    return {
        "ok": True,
        "role": "safety",
        "generated_at": _now_iso(),
        "summary": {
            "total_open": total,
            "overdue_capas": overdue,
            "incidents_needing_capa": needs_capa,
            "capas_awaiting_verification": pending_stuck,
            "capas_without_owner": no_owner,
            "incidents_closed_capa_open": closed_open,
            "trainings_expired": trn_expired,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# HR DIGEST
# ---------------------------------------------------------------------------

async def _build_hr_digest(db) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    # 1 · Linkage failures (HR can resolve identity drift via the master).
    unresolvable = await _count_open_findings(db, "EMP_LINK_UNRESOLVABLE")
    ambiguous = await _count_open_findings(db, "EMP_LINK_AMBIGUOUS")
    if (unresolvable + ambiguous) > 0:
        sections.append({
            "key": "linkage_failures",
            "severity": "high",
            "title": f"{unresolvable + ambiguous} employee-linkage failure(s)",
            "body": "Operational records reference employee names HR's master cannot resolve. Resolving each one closes operational records back into the canonical identity timeline.",
            "count": unresolvable + ambiguous,
            "action_url": "/admin/compliance-findings?category=linkage",
            "rule_ids": ["EMP_LINK_UNRESOLVABLE", "EMP_LINK_AMBIGUOUS"],
            "items": await _sample_open_findings(
                db, ["EMP_LINK_UNRESOLVABLE", "EMP_LINK_AMBIGUOUS"], 5,
            ),
        })

    # 2 · Driver qualification (HR-owned source-of-truth).
    drv_med_exp = await _count_open_findings(db, "DRV_MED_EXPIRED")
    drv_cdl_exp = await _count_open_findings(db, "DRV_CDL_EXPIRED")
    if (drv_med_exp + drv_cdl_exp) > 0:
        sections.append({
            "key": "driver_qualification_expired",
            "severity": "critical",
            "title": f"{drv_med_exp + drv_cdl_exp} driver qualification(s) expired",
            "body": "Active approved drivers with an expired medical card or CDL. DOT exposure — HR must update the employee master before they can return to driving status.",
            "count": drv_med_exp + drv_cdl_exp,
            "action_url": "/hr/driver-qualification",
            "rule_ids": ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"],
            "items": await _sample_open_findings(
                db, ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"], 5,
            ),
        })

    drv_med_30 = await _count_open_findings(db, "DRV_MED_EXPIRING")
    drv_cdl_30 = await _count_open_findings(db, "DRV_CDL_EXPIRING")
    if (drv_med_30 + drv_cdl_30) > 0:
        sections.append({
            "key": "driver_qualification_expiring",
            "severity": "high",
            "title": f"{drv_med_30 + drv_cdl_30} driver qualification(s) expiring ≤30d",
            "body": "Heads-up so HR can chase renewals before the records lapse.",
            "count": drv_med_30 + drv_cdl_30,
            "action_url": "/hr/driver-qualification",
            "rule_ids": ["DRV_MED_EXPIRING", "DRV_CDL_EXPIRING"],
            "items": await _sample_open_findings(
                db, ["DRV_MED_EXPIRING", "DRV_CDL_EXPIRING"], 5,
            ),
        })

    # 3 · Archived but still active flag.
    archived_active = await _count_open_findings(db, "EMP_ARCHIVED_ACTIVE")
    if archived_active > 0:
        sections.append({
            "key": "archived_active",
            "severity": "medium",
            "title": f"{archived_active} archived employee(s) still flagged active",
            "body": "Soft-deleted employee records that still report is_active=true. HR should restore or finalize archival to keep the timeline consistent.",
            "count": archived_active,
            "action_url": "/admin/compliance-findings?rule_id=EMP_ARCHIVED_ACTIVE",
            "rule_ids": ["EMP_ARCHIVED_ACTIVE"],
            "items": await _sample_open_findings(db, ["EMP_ARCHIVED_ACTIVE"], 5),
        })

    # 4 · Expired training (HR adjacent — labor/compliance exposure).
    trn_expired = await _count_open_findings(db, "TRN_EXPIRED")
    if trn_expired > 0:
        sections.append({
            "key": "training_expired",
            "severity": "high",
            "title": f"{trn_expired} employee(s) with expired training",
            "body": "Active employees whose required training certifications have lapsed. Coordinate with Safety to re-deliver and re-certify.",
            "count": trn_expired,
            "action_url": "/admin/compliance-findings?rule_id=TRN_EXPIRED",
            "rule_ids": ["TRN_EXPIRED"],
            "items": await _sample_open_findings(db, ["TRN_EXPIRED"], 5),
        })

    return {
        "ok": True, "role": "hr", "generated_at": _now_iso(),
        "summary": {
            "total_open": sum(s["count"] for s in sections),
            "linkage_failures": unresolvable + ambiguous,
            "driver_qualification_expired": drv_med_exp + drv_cdl_exp,
            "driver_qualification_expiring_30d": drv_med_30 + drv_cdl_30,
            "archived_active": archived_active,
            "trainings_expired": trn_expired,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# PM DIGEST (project-scoped — but at the digest layer we surface
# unscoped counts; the PM Crew Compliance page already has the
# project-scoped breakdown).
# ---------------------------------------------------------------------------

async def _build_pm_digest(db, scope_user: Dict[str, Any]) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    capa_overdue = await _count_open_findings(db, "CAPA_OVERDUE")
    if capa_overdue > 0:
        sections.append({
            "key": "capa_overdue",
            "severity": "high",
            "title": f"{capa_overdue} CAPA(s) past due",
            "body": "Open corrective actions across projects that have passed their due date. Open the list to see which affect your crew.",
            "count": capa_overdue,
            "action_url": "/pm/crew-compliance",
            "rule_ids": ["CAPA_OVERDUE"],
            "items": await _sample_open_findings(db, ["CAPA_OVERDUE"], 5),
        })

    trn_expired = await _count_open_findings(db, "TRN_EXPIRED")
    if trn_expired > 0:
        sections.append({
            "key": "training_expired",
            "severity": "high",
            "title": f"{trn_expired} crew member(s) with expired training",
            "body": "Visit Crew Compliance to see which of these are on your projects — read-only governance, but you can escalate to Safety/HR.",
            "count": trn_expired,
            "action_url": "/pm/crew-compliance",
            "rule_ids": ["TRN_EXPIRED"],
            "items": await _sample_open_findings(db, ["TRN_EXPIRED"], 5),
        })

    ppe_missing = await _count_open_findings(db, "PPE_MISSING")
    if ppe_missing > 0:
        sections.append({
            "key": "ppe_missing",
            "severity": "medium",
            "title": f"{ppe_missing} active employee(s) with no PPE accountability",
            "body": "Crew members who have zero PPE issuance records on file. Flag to Safety for issuance + acknowledgement.",
            "count": ppe_missing,
            "action_url": "/pm/crew-compliance",
            "rule_ids": ["PPE_MISSING"],
            "items": await _sample_open_findings(db, ["PPE_MISSING"], 5),
        })

    drv_med_exp = await _count_open_findings(db, "DRV_MED_EXPIRED")
    drv_cdl_exp = await _count_open_findings(db, "DRV_CDL_EXPIRED")
    if (drv_med_exp + drv_cdl_exp) > 0:
        sections.append({
            "key": "driver_unavailable",
            "severity": "high",
            "title": f"{drv_med_exp + drv_cdl_exp} qualified driver(s) currently unavailable",
            "body": "Approved drivers with expired credentials cannot operate company vehicles until HR updates the master. Affects project staffing.",
            "count": drv_med_exp + drv_cdl_exp,
            "action_url": "/pm/crew-compliance",
            "rule_ids": ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"],
            "items": await _sample_open_findings(
                db, ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"], 5,
            ),
        })

    return {
        "ok": True, "role": "pm", "generated_at": _now_iso(),
        "scope_user": {"id": scope_user.get("id"),
                        "name": scope_user.get("name") or scope_user.get("email")},
        "summary": {
            "total_open": sum(s["count"] for s in sections),
            "capa_overdue": capa_overdue,
            "trainings_expired": trn_expired,
            "ppe_missing": ppe_missing,
            "driver_unavailable": drv_med_exp + drv_cdl_exp,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# DISPATCH DIGEST
# ---------------------------------------------------------------------------

async def _build_dispatch_digest(db) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    med_exp = await _count_open_findings(db, "DRV_MED_EXPIRED")
    cdl_exp = await _count_open_findings(db, "DRV_CDL_EXPIRED")
    if med_exp > 0:
        sections.append({
            "key": "med_card_expired",
            "severity": "critical",
            "title": f"{med_exp} driver(s) with expired medical card",
            "body": "Cannot dispatch — DOT violation. Notify HR to chase renewal. Re-check before assigning to today's runs.",
            "count": med_exp,
            "action_url": "/dispatch-portal/driver-qualification",
            "rule_ids": ["DRV_MED_EXPIRED"],
            "items": await _sample_open_findings(db, ["DRV_MED_EXPIRED"], 5),
        })
    if cdl_exp > 0:
        sections.append({
            "key": "cdl_expired",
            "severity": "critical",
            "title": f"{cdl_exp} driver(s) with expired CDL",
            "body": "CDL holders are not legally permitted to operate commercial vehicles until renewed. Pull them from dispatch immediately.",
            "count": cdl_exp,
            "action_url": "/dispatch-portal/driver-qualification",
            "rule_ids": ["DRV_CDL_EXPIRED"],
            "items": await _sample_open_findings(db, ["DRV_CDL_EXPIRED"], 5),
        })

    med_30 = await _count_open_findings(db, "DRV_MED_EXPIRING")
    cdl_30 = await _count_open_findings(db, "DRV_CDL_EXPIRING")
    if (med_30 + cdl_30) > 0:
        sections.append({
            "key": "expiring_30d",
            "severity": "high",
            "title": f"{med_30 + cdl_30} driver credential(s) expiring ≤30d",
            "body": "Heads-up so you can rebalance assignments before these drivers lose eligibility.",
            "count": med_30 + cdl_30,
            "action_url": "/dispatch-portal/driver-qualification",
            "rule_ids": ["DRV_MED_EXPIRING", "DRV_CDL_EXPIRING"],
            "items": await _sample_open_findings(
                db, ["DRV_MED_EXPIRING", "DRV_CDL_EXPIRING"], 5,
            ),
        })

    return {
        "ok": True, "role": "dispatch", "generated_at": _now_iso(),
        "summary": {
            "total_open": sum(s["count"] for s in sections),
            "med_card_expired": med_exp,
            "cdl_expired": cdl_exp,
            "expiring_30d": med_30 + cdl_30,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# FL (Field Leadership) DIGEST
# ---------------------------------------------------------------------------

async def _build_fl_digest(db, scope_user: Dict[str, Any]) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []

    trn_expired = await _count_open_findings(db, "TRN_EXPIRED")
    if trn_expired > 0:
        sections.append({
            "key": "training_expired",
            "severity": "high",
            "title": f"{trn_expired} field employee(s) with expired training",
            "body": "Operational readiness risk on jobs. Coordinate with Safety to re-deliver before assignment.",
            "count": trn_expired,
            "action_url": "/fl/dq",
            "rule_ids": ["TRN_EXPIRED"],
            "items": await _sample_open_findings(db, ["TRN_EXPIRED"], 5),
        })

    ppe_missing = await _count_open_findings(db, "PPE_MISSING")
    if ppe_missing > 0:
        sections.append({
            "key": "ppe_missing",
            "severity": "medium",
            "title": f"{ppe_missing} field employee(s) with no PPE accountability",
            "body": "Operational readiness gap. Notify Safety to issue and acknowledge PPE before next shift.",
            "count": ppe_missing,
            "action_url": "/fl/dq",
            "rule_ids": ["PPE_MISSING"],
            "items": await _sample_open_findings(db, ["PPE_MISSING"], 5),
        })

    med_exp = await _count_open_findings(db, "DRV_MED_EXPIRED")
    cdl_exp = await _count_open_findings(db, "DRV_CDL_EXPIRED")
    if (med_exp + cdl_exp) > 0:
        sections.append({
            "key": "driver_unavailable",
            "severity": "high",
            "title": f"{med_exp + cdl_exp} driver(s) currently unavailable",
            "body": "Field operations affected — these drivers cannot drive until HR updates the master.",
            "count": med_exp + cdl_exp,
            "action_url": "/fl/dq",
            "rule_ids": ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"],
            "items": await _sample_open_findings(
                db, ["DRV_MED_EXPIRED", "DRV_CDL_EXPIRED"], 5,
            ),
        })

    inc_needs_capa = await _count_open_findings(db, "INC_NEEDS_CAPA")
    if inc_needs_capa > 0:
        sections.append({
            "key": "incidents_needing_capa",
            "severity": "high",
            "title": f"{inc_needs_capa} severe incident(s) without a CAPA",
            "body": "Safety governance issue — surfaces here so FL knows incident exposure on the field side.",
            "count": inc_needs_capa,
            "action_url": "/fl/accountability",
            "rule_ids": ["INC_NEEDS_CAPA"],
            "items": await _sample_open_findings(db, ["INC_NEEDS_CAPA"], 5),
        })

    return {
        "ok": True, "role": "fl", "generated_at": _now_iso(),
        "scope_user": {"id": scope_user.get("id"),
                        "name": scope_user.get("name") or scope_user.get("email")},
        "summary": {
            "total_open": sum(s["count"] for s in sections),
            "trainings_expired": trn_expired,
            "ppe_missing": ppe_missing,
            "driver_unavailable": med_exp + cdl_exp,
            "incidents_needing_capa": inc_needs_capa,
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_notifications_router(
    db,
    require_admin_strict,
    require_safety_or_admin,
):
    router = APIRouter(tags=["notifications"])

    # Local token validators imported lazily to avoid circular imports
    # at server startup.
    async def _resolve_hr_user(x_hr_token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not x_hr_token:
            return None
        from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
        return await is_valid_hr_user_token_async(db, x_hr_token)

    async def _resolve_pm_user(x_pm_token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not x_pm_token:
            return None
        from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
        return await is_valid_pm_user_token_async(db, x_pm_token)

    async def _resolve_dispatch_user(x_dispatch_token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not x_dispatch_token:
            return None
        from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415
        return await is_valid_dispatch_user_token_async(db, x_dispatch_token)

    async def _resolve_fl_user(x_fl_token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not x_fl_token:
            return None
        from field_leadership_users import is_valid_fl_user_token_async  # noqa: PLC0415
        return await is_valid_fl_user_token_async(db, x_fl_token)

    @router.get("/api/admin/notifications/digest",
                dependencies=[Depends(require_admin_strict)])
    async def admin_digest():
        return await _build_admin_digest(db)

    @router.get("/api/safety/notifications/digest")
    async def safety_digest(_: dict = Depends(require_safety_or_admin)):
        return await _build_safety_digest(db)

    @router.get("/api/hr/notifications/digest")
    async def hr_digest(
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ):
        user = await _resolve_hr_user(x_hr_token)
        if user:
            return await _build_hr_digest(db)
        # Admin can preview the HR digest for operational oversight.
        from server import _is_valid_admin_token  # noqa: PLC0415
        if x_admin_token and _is_valid_admin_token(x_admin_token):
            return await _build_hr_digest(db)
        raise HTTPException(401, "HR or Admin auth required")

    @router.get("/api/pm/notifications/digest")
    async def pm_digest(
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ):
        user = await _resolve_pm_user(x_pm_token)
        if user:
            return await _build_pm_digest(db, user)
        from server import _is_valid_admin_token  # noqa: PLC0415
        if x_admin_token and _is_valid_admin_token(x_admin_token):
            return await _build_pm_digest(db, {"id": "admin", "name": "Admin"})
        raise HTTPException(401, "PM or Admin auth required")

    @router.get("/api/dispatch/notifications/digest")
    async def dispatch_digest(
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ):
        user = await _resolve_dispatch_user(x_dispatch_token)
        if user:
            return await _build_dispatch_digest(db)
        from server import _is_valid_admin_token  # noqa: PLC0415
        if x_admin_token and _is_valid_admin_token(x_admin_token):
            return await _build_dispatch_digest(db)
        raise HTTPException(401, "Dispatch or Admin auth required")

    @router.get("/api/fl/notifications/digest")
    async def fl_digest(
        x_fl_token: Optional[str] = Header(default=None, alias="X-FL-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ):
        user = await _resolve_fl_user(x_fl_token)
        if user:
            return await _build_fl_digest(db, user)
        from server import _is_valid_admin_token  # noqa: PLC0415
        if x_admin_token and _is_valid_admin_token(x_admin_token):
            return await _build_fl_digest(db, {"id": "admin", "name": "Admin"})
        raise HTTPException(401, "FL or Admin auth required")

    return router


__all__ = [
    "build_notifications_router",
    "_build_admin_digest",
    "_build_safety_digest",
    "_build_hr_digest",
    "_build_pm_digest",
    "_build_dispatch_digest",
    "_build_fl_digest",
]
