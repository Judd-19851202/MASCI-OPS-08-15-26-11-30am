"""
routes/dispatch_governance.py · iter395 · Phase 11.4 · DLS Governance.

Read-only, on-demand operational signal computation. NO new collection,
NO write side, NO scheduler — the lifecycle truth already lives in
`dispatch_assignments` and `dispatch_state_events`; this module simply
reads it and projects the four canonical findings the operator
sanctioned for iter395:

  • ASSIGNMENT_STUCK            — non-terminal assignment, no transition ≥ N min
  • WAIT_THRESHOLD_EXCEEDED     — currently WAITING for ≥ N min
  • BREAKDOWN_ACTIVE            — currently in BREAKDOWN
  • NON_STANDARD_TRANSITION_PATTERN — ≥ N non-standard transitions in window
                                       on a single truck

Doctrine (per the iter395 directive):
  • Findings are OPERATIONAL SIGNALS, not punishment.
  • Disciplined — exactly four detectors, nothing else.
  • Disciplined — never store these; they expire when the underlying
    lifecycle truth changes. Stale alerts are worse than no alerts.
  • Tenant-scoped (X-Tenant-Id), and read-gated by `any portal token`
    so PM/Shop/Safety/FL hubs can light their own tiles in iter396+
    WITHOUT a new endpoint.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Query

import dispatch_lifecycle as DLS
from routes.dispatch_lifecycle import DEFAULT_TENANT_ID

logger = logging.getLogger("dispatch_governance_routes")

# ── Thresholds (env-overridable later if needed; sane defaults today)
STUCK_THRESHOLD_MINUTES = 30
WAIT_THRESHOLD_MINUTES = 20
NON_STANDARD_WINDOW_MINUTES = 120
NON_STANDARD_COUNT_THRESHOLD = 3
MAX_FINDINGS_PER_KIND = 50


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _minutes_since(iso: Optional[str], reference: Optional[datetime] = None) -> Optional[int]:
    ref = reference or _now()
    parsed = _parse_iso(iso)
    if parsed is None:
        return None
    return max(0, int((ref - parsed).total_seconds() / 60))


def _human_minutes(minutes: Optional[int]) -> str:
    """Readability guard — render an elapsed magnitude as d/h/m instead
    of a raw minute count ('113996 min' → '79d 3h'). Value unchanged;
    the numeric field (minutes_in_state/…) still carries the raw truth."""
    if minutes is None:
        return "unknown"
    m = max(0, int(minutes))
    if m < 60:
        return f"{m}m"
    h = m // 60
    if h < 24:
        r = m % 60
        return f"{h}h {r}m" if r else f"{h}h"
    d = h // 24
    rh = h % 24
    return f"{d}d {rh}h" if rh else f"{d}d"


# ════════════════════════════════════════════════════════════════════
# Detectors
# ════════════════════════════════════════════════════════════════════
async def _detect_assignment_stuck(
    db, *, tenant_id: str, threshold_minutes: int, now: datetime,
) -> List[Dict[str, Any]]:
    """Active assignment that has not transitioned for ≥ threshold."""
    cursor = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
            "cancelled_at": None,
        },
        {"_id": 0},
    )
    rows = await cursor.to_list(length=500)
    findings: List[Dict[str, Any]] = []
    for a in rows:
        mins = _minutes_since(a.get("last_transition_at"), now)
        if mins is None or mins < threshold_minutes:
            continue
        # Skip rows where the WAITING detector will fire — wait gets
        # its own finding category so we don't double-count.
        if a.get("current_state") == DLS.WAITING:
            continue
        findings.append({
            "kind": "ASSIGNMENT_STUCK",
            "severity": "high" if mins >= threshold_minutes * 2 else "medium",
            "assignment_id": a["id"],
            "truck_id": a.get("truck_id"),
            "driver_id": a.get("driver_id"),
            "driver_name": a.get("driver_name") or "",
            "project_number": a.get("project_number") or "",
            "current_state": a.get("current_state"),
            "minutes_in_state": mins,
            "threshold_minutes": threshold_minutes,
            "last_transition_at": a.get("last_transition_at"),
            "headline": (
                f"{a.get('truck_id') or 'Truck'} stuck in {a.get('current_state')} "
                f"for {_human_minutes(mins)} · {str(a['id'])[-6:]}"
            ),
        })
    findings.sort(key=lambda f: f.get("minutes_in_state") or 0, reverse=True)
    return findings[:MAX_FINDINGS_PER_KIND]


async def _detect_wait_threshold(
    db, *, tenant_id: str, threshold_minutes: int, now: datetime,
) -> List[Dict[str, Any]]:
    """Assignment currently in WAITING for ≥ threshold."""
    cursor = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": DLS.WAITING,
            "cancelled_at": None,
        },
        {"_id": 0},
    )
    rows = await cursor.to_list(length=200)
    findings: List[Dict[str, Any]] = []
    for a in rows:
        mins = _minutes_since(a.get("last_transition_at"), now)
        if mins is None or mins < threshold_minutes:
            continue
        reason = a.get("current_wait_reason") or "UNCATEGORIZED_WAIT"
        findings.append({
            "kind": "WAIT_THRESHOLD_EXCEEDED",
            "severity": "high" if mins >= threshold_minutes * 2 else "medium",
            "assignment_id": a["id"],
            "truck_id": a.get("truck_id"),
            "driver_id": a.get("driver_id"),
            "driver_name": a.get("driver_name") or "",
            "project_number": a.get("project_number") or "",
            "wait_reason": reason,
            "minutes_waiting": mins,
            "threshold_minutes": threshold_minutes,
            "last_transition_at": a.get("last_transition_at"),
            "headline": (
                f"{a.get('truck_id') or 'Truck'} waiting on "
                f"{reason.replace('_', ' ')} for {_human_minutes(mins)}"
            ),
        })
    findings.sort(key=lambda f: f.get("minutes_waiting") or 0, reverse=True)
    return findings[:MAX_FINDINGS_PER_KIND]


async def _detect_breakdown_active(
    db, *, tenant_id: str, now: datetime,
) -> List[Dict[str, Any]]:
    """Any active assignment in BREAKDOWN."""
    cursor = db.dispatch_assignments.find(
        {
            "tenant_id": tenant_id,
            "current_state": DLS.BREAKDOWN,
            "cancelled_at": None,
        },
        {"_id": 0},
    )
    rows = await cursor.to_list(length=200)
    findings: List[Dict[str, Any]] = []
    for a in rows:
        mins = _minutes_since(a.get("last_transition_at"), now) or 0
        findings.append({
            "kind": "BREAKDOWN_ACTIVE",
            "severity": "critical",
            "assignment_id": a["id"],
            "truck_id": a.get("truck_id"),
            "driver_id": a.get("driver_id"),
            "driver_name": a.get("driver_name") or "",
            "project_number": a.get("project_number") or "",
            "minutes_down": mins,
            "last_transition_at": a.get("last_transition_at"),
            "headline": (
                f"{a.get('truck_id') or 'Truck'} in BREAKDOWN "
                f"({_human_minutes(mins)})"
            ),
        })
    findings.sort(key=lambda f: f.get("minutes_down") or 0, reverse=True)
    return findings[:MAX_FINDINGS_PER_KIND]


async def _detect_non_standard_pattern(
    db, *, tenant_id: str, window_minutes: int, count_threshold: int,
    now: datetime,
) -> List[Dict[str, Any]]:
    """Truck with ≥ count_threshold non-standard transitions in window."""
    since = (now - timedelta(minutes=window_minutes)).isoformat()
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "standard": False,
            "at": {"$gte": since},
            "truck_id": {"$ne": None},
        }},
        {"$group": {
            "_id": "$truck_id",
            "count": {"$sum": 1},
            "latest_at": {"$max": "$at"},
            "samples": {"$push": {
                "from_state": "$from_state",
                "to_state": "$to_state",
                "at": "$at",
                "warning_tag": "$warning_tag",
                "correction_reason": "$correction_reason",
            }},
        }},
        {"$match": {"count": {"$gte": count_threshold}}},
        {"$sort": {"count": -1}},
        {"$limit": MAX_FINDINGS_PER_KIND},
    ]
    rows = await db.dispatch_state_events.aggregate(pipeline).to_list(
        length=MAX_FINDINGS_PER_KIND,
    )
    findings: List[Dict[str, Any]] = []
    for row in rows:
        truck = row["_id"]
        samples = sorted(row.get("samples") or [], key=lambda s: s["at"])[-5:]
        findings.append({
            "kind": "NON_STANDARD_TRANSITION_PATTERN",
            "severity": "medium",
            "truck_id": truck,
            "count_in_window": int(row["count"]),
            "window_minutes": window_minutes,
            "threshold": count_threshold,
            "latest_at": row.get("latest_at"),
            "samples": samples,
            "headline": (
                f"{truck} · {row['count']} non-standard transitions in "
                f"last {window_minutes} min"
            ),
        })
    return findings


# ════════════════════════════════════════════════════════════════════
# Router
# ════════════════════════════════════════════════════════════════════
def build_dispatch_governance_router(
    db,
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Build the DLS governance findings router. Read-gated by the
    cross-portal aggregator so PM/Safety/Shop/FL/dispatch/admin can
    poll it for their own role-aware tiles (iter396+) without a new
    auth surface."""
    router = APIRouter(
        prefix="/api/dispatch/governance",
        tags=["dispatch-governance"],
    )

    @router.get("/findings")
    async def get_findings(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        stuck_threshold: int = Query(
            STUCK_THRESHOLD_MINUTES, ge=0, le=720,
            description="Minutes a non-terminal assignment may remain "
                        "without a transition before being flagged. "
                        "Set to 0 to surface every active assignment.",
        ),
        wait_threshold: int = Query(
            WAIT_THRESHOLD_MINUTES, ge=0, le=720,
            description="Minutes in WAITING before being flagged. "
                        "Set to 0 to surface every WAITING row.",
        ),
        non_standard_window: int = Query(
            NON_STANDARD_WINDOW_MINUTES, ge=15, le=1440,
            description="Window for non-standard pattern detection.",
        ),
        non_standard_min: int = Query(
            NON_STANDARD_COUNT_THRESHOLD, ge=2, le=20,
            description="Min non-standard transitions in window to flag.",
        ),
        project_numbers: Optional[str] = Query(
            None,
            description="Optional comma-separated list of project_numbers. "
                        "When provided, findings are filtered to assignments "
                        "tied to those projects (PM-scope tile use case).",
        ),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        now = _now()
        project_filter: Optional[set] = None
        if project_numbers:
            project_filter = {
                p.strip() for p in project_numbers.split(",") if p.strip()
            } or None
        stuck = await _detect_assignment_stuck(
            db, tenant_id=tenant_id, threshold_minutes=stuck_threshold, now=now,
        )
        wait = await _detect_wait_threshold(
            db, tenant_id=tenant_id, threshold_minutes=wait_threshold, now=now,
        )
        bdn = await _detect_breakdown_active(db, tenant_id=tenant_id, now=now)
        pattern = await _detect_non_standard_pattern(
            db,
            tenant_id=tenant_id,
            window_minutes=non_standard_window,
            count_threshold=non_standard_min,
            now=now,
        )
        all_findings = bdn + stuck + wait + pattern   # severity-ordered roughly
        if project_filter:
            # Filter to PM-scope projects. NON_STANDARD_TRANSITION_PATTERN
            # has no project_number (it's truck-level) — drop it from the
            # filtered view since a PM scope doesn't apply.
            all_findings = [
                f for f in all_findings
                if (f.get("project_number") or "") in project_filter
            ]
        counts = {
            "BREAKDOWN_ACTIVE": sum(1 for f in all_findings if f["kind"] == "BREAKDOWN_ACTIVE"),
            "ASSIGNMENT_STUCK": sum(1 for f in all_findings if f["kind"] == "ASSIGNMENT_STUCK"),
            "WAIT_THRESHOLD_EXCEEDED": sum(1 for f in all_findings if f["kind"] == "WAIT_THRESHOLD_EXCEEDED"),
            "NON_STANDARD_TRANSITION_PATTERN": sum(1 for f in all_findings if f["kind"] == "NON_STANDARD_TRANSITION_PATTERN"),
            "total": len(all_findings),
        }
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "generated_at": now.isoformat(),
            "thresholds": {
                "stuck_threshold_minutes": stuck_threshold,
                "wait_threshold_minutes": wait_threshold,
                "non_standard_window_minutes": non_standard_window,
                "non_standard_min_count": non_standard_min,
            },
            "counts": counts,
            "findings": all_findings,
        }

    return router


__all__ = [
    "build_dispatch_governance_router",
    "STUCK_THRESHOLD_MINUTES",
    "WAIT_THRESHOLD_MINUTES",
    "NON_STANDARD_WINDOW_MINUTES",
    "NON_STANDARD_COUNT_THRESHOLD",
]
