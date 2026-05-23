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

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends


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
# Router factory
# ---------------------------------------------------------------------------

def build_notifications_router(
    db,
    require_admin_strict,
    require_safety_or_admin,
):
    router = APIRouter(tags=["notifications"])

    @router.get("/api/admin/notifications/digest",
                dependencies=[Depends(require_admin_strict)])
    async def admin_digest():
        return await _build_admin_digest(db)

    @router.get("/api/safety/notifications/digest")
    async def safety_digest(_: dict = Depends(require_safety_or_admin)):
        return await _build_safety_digest(db)

    return router


__all__ = [
    "build_notifications_router",
    "_build_admin_digest",
    "_build_safety_digest",
]
