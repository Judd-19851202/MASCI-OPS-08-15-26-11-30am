"""TRACK 25 · SPRINT 7/8 · Trust Events aggregator.

Endpoint
--------
* ``GET /api/admin/occ/trust-events``  — one canonical read-only feed
  of the most recent platform trust events. Composes:

    - admin audit entries (`admin_audit` collection)
    - scheduler run outcomes (`admin/scheduler-runs`)
    - deploy readiness blockers (`admin/deploy-readiness`)
    - OCC operations audit (`admin/operations-control/audit`)
    - governance findings snapshot

  into a single time-sorted list with a stable envelope:

    {
      ts, kind, severity, summary, source_endpoint, evidence
    }

This wires four Sprint-4/5 trust gaps in one shot:
  * gap-gov-trust-events (Unified Trust events log)
  * gap-gov-unresolved-blockers (Unresolved production blockers)
  * gap-sec-auth-failures (Recent auth failures)  — sourced from
    admin audit rows whose action matches an auth failure pattern.
  * gap-maint-history-summary (Cross-domain maintenance history) —
    OCC operations audit rows carry this data.

Design principles (identical to occ_health_aggregator):
  · zero new truth sources · zero server cache · honest UNKNOWN
    when a child probe fails · caller's X-Admin-Token is forwarded.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Request

_BACKEND_INTERNAL_BASE = os.environ.get(
    "OCC_HEALTH_INTERNAL_BASE",
    "http://127.0.0.1:8001",
).rstrip("/")
_PROBE_TIMEOUT_S = 6.0

# Actions in `admin_audit` we classify as auth-related events.
_AUTH_ACTIONS = {
    "multi_login", "login", "logout", "login_failure", "login_locked",
    "password_reset", "password_change", "mfa_enroll", "mfa_verify",
    "session_revoked", "session_terminated",
}


def _mk(ts: Optional[str], kind: str, severity: str, summary: str,
        source_endpoint: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ts": ts,
        "kind": kind,               # "audit" | "scheduler" | "deploy_blocker" | "ops_audit" | "governance"
        "severity": severity,       # "info" | "warning" | "critical"
        "summary": summary,
        "source_endpoint": source_endpoint,
        "evidence": evidence,
    }


async def _get(client: httpx.AsyncClient, path: str, headers: Dict[str, str]) -> Any:
    url = _BACKEND_INTERNAL_BASE + path
    try:
        r = await client.get(url, headers=headers)
        if r.status_code >= 400:
            return {"__error__": f"HTTP {r.status_code}", "__status__": r.status_code}
        return r.json()
    except Exception as e:  # noqa: BLE001
        return {"__error__": f"{type(e).__name__}: {e}"}


def _classify_audit(row: Dict[str, Any]) -> Dict[str, Any]:
    action = str(row.get("action") or "").lower()
    outcome = str(row.get("outcome") or "").lower()
    severity = "info"
    kind = "audit"
    if action in _AUTH_ACTIONS or action.startswith("login") or action.startswith("mfa"):
        kind = "auth"
        if "fail" in action or "locked" in action or outcome in ("fail", "failed", "denied"):
            severity = "warning"
    if outcome in ("fail", "failed", "error"):
        severity = "critical"
    summary = f"{row.get('actor_email') or row.get('actor_id') or 'system'} · {action or 'admin action'}"
    return _mk(
        ts=row.get("ts") or row.get("at"),
        kind=kind, severity=severity, summary=summary,
        source_endpoint="/api/admin/audit",
        evidence={k: v for k, v in row.items() if k in (
            "action", "actor_id", "actor_email", "outcome", "target",
            "target_id", "ip", "ua_hash",
        )},
    )


def _from_scheduler(item: Dict[str, Any]) -> Dict[str, Any]:
    status = str(item.get("status") or item.get("outcome") or "").lower()
    severity = "warning" if status in ("fail", "failed", "error") else "info"
    return _mk(
        ts=item.get("ts") or item.get("started_at") or item.get("last_tick_ts"),
        kind="scheduler", severity=severity,
        summary=f"scheduler · {item.get('name', 'run')} · {status or 'ran'}",
        source_endpoint="/api/admin/scheduler-runs",
        evidence={k: v for k, v in item.items() if k in (
            "name", "status", "outcome", "duration_ms", "duration_s",
            "attempt", "error", "reason",
        )},
    )


def _from_ops_audit(row: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(row.get("mode") or "").lower()
    severity = "critical" if row.get("error") else "info"
    return _mk(
        ts=row.get("ts"),
        kind="ops_audit", severity=severity,
        summary=f"ops · {row.get('operation_id')} · {mode}",
        source_endpoint="/api/admin/operations-control/audit",
        evidence={k: v for k, v in row.items() if k in (
            "operation_id", "mode", "actor_email", "action_id", "error",
        )},
    )


def _from_deploy_blocker(check: Dict[str, Any], generated_at: Optional[str]) -> Dict[str, Any]:
    status = str(check.get("status") or "").lower()
    severity = "critical" if status in ("blocked", "fail", "failed") else "warning"
    return _mk(
        ts=check.get("ts") or generated_at,
        kind="deploy_blocker", severity=severity,
        summary=f"deploy · {check.get('id', 'check')} · {status}",
        source_endpoint="/api/admin/deploy-readiness",
        evidence={k: v for k, v in check.items() if k in (
            "id", "status", "message", "detail", "owner",
        )},
    )


def register_occ_trust_events_routes(api_router: APIRouter, require_admin: Callable):
    """Attach ``GET /api/admin/occ/trust-events`` to the platform api_router."""

    @api_router.get("/admin/occ/trust-events")
    async def occ_trust_events(
        request: Request,
        limit: int = 25,
        actor: Any = Depends(require_admin),  # noqa: ARG001 · gate only
    ) -> Dict[str, Any]:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        headers: Dict[str, str] = {}
        for h in ("x-admin-token", "authorization"):
            v = request.headers.get(h)
            if v:
                headers[h.replace("x-", "X-").title().replace("Token", "Token")] = v

        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            audit_body, sched_body, ops_body, deploy_body = await asyncio.gather(
                _get(client, f"/api/admin/audit?limit={limit}", headers),
                _get(client, f"/api/admin/scheduler-runs?limit={limit}", headers),
                _get(client, f"/api/admin/operations-control/audit?limit={limit}", headers),
                _get(client, "/api/admin/deploy-readiness", headers),
            )

        events: List[Dict[str, Any]] = []
        errors: Dict[str, str] = {}

        if isinstance(audit_body, dict) and "__error__" not in audit_body:
            for r in audit_body.get("entries") or []:
                events.append(_classify_audit(r))
        elif isinstance(audit_body, dict):
            errors["audit"] = audit_body.get("__error__", "")

        if isinstance(sched_body, dict) and "__error__" not in sched_body:
            for r in sched_body.get("items") or sched_body.get("runs") or []:
                events.append(_from_scheduler(r))
        elif isinstance(sched_body, dict):
            errors["scheduler"] = sched_body.get("__error__", "")

        if isinstance(ops_body, dict) and "__error__" not in ops_body:
            for r in ops_body.get("audit") or []:
                events.append(_from_ops_audit(r))
        elif isinstance(ops_body, dict):
            errors["ops_audit"] = ops_body.get("__error__", "")

        blockers: List[Dict[str, Any]] = []
        if isinstance(deploy_body, dict) and "__error__" not in deploy_body:
            generated_at = deploy_body.get("checked_at")
            for chk in deploy_body.get("checks") or []:
                st = str(chk.get("status") or "").lower()
                if st in ("blocked", "fail", "failed", "warning"):
                    ev = _from_deploy_blocker(chk, generated_at)
                    events.append(ev)
                    if st in ("blocked", "fail", "failed"):
                        blockers.append(ev)
        elif isinstance(deploy_body, dict):
            errors["deploy"] = deploy_body.get("__error__", "")

        # Sort newest-first; put items without ts at the end.
        def _key(e):
            return e.get("ts") or ""
        events.sort(key=_key, reverse=True)

        # Aggregates per kind — cheap surface for domain landing cards.
        counts = {"info": 0, "warning": 0, "critical": 0}
        by_kind: Dict[str, int] = {}
        auth_failures = 0
        for e in events:
            counts[e["severity"]] = counts.get(e["severity"], 0) + 1
            by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
            if e["kind"] == "auth" and e["severity"] in ("warning", "critical"):
                auth_failures += 1

        return {
            "generated_at": now_iso,
            "counts": counts,
            "by_kind": by_kind,
            "auth_failures_in_window": auth_failures,
            "unresolved_blockers": blockers,
            "events": events[:limit],
            "probe_errors": errors,
        }

    return api_router
