"""TRACK 25 · SPRINT 7/8 · Trust Events aggregator.

Endpoint
--------
* ``GET /api/admin/occ/trust-events``  — one bounded read-only feed
  of recent platform trust events. Composes:

    - admin audit entries (`admin_audit` collection)
    - scheduler run outcomes (`admin/scheduler-runs`)
    - canonical deployment-readiness findings (`admin/deployment-readiness`)
    - OCC operations audit (`admin/operations-control/audit`)
    - Trust Spine authority verification

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
    when a child probe fails · caller's X-Admin-Token is forwarded ·
    Trust Spine remains canonical event architecture.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Request

from lib.canonical_status import DEGRADED, MISMATCH, UNVERIFIABLE, VERIFIED
from lib.canonical_truth import canonical_truth_surface
from lib.ots_truth import (
    OBSERVED,
    canonical_truth_card,
    compatibility_projection,
    projected_truth_relationship,
    public_ots_projection,
)

_BACKEND_INTERNAL_BASE = os.environ.get(
    "OCC_HEALTH_INTERNAL_BASE",
    "http://127.0.0.1:8001",
).rstrip("/")
_PROBE_TIMEOUT_S = 6.0
_TRUST_SPINE_PATH = "/api/admin/trust-spine"
_CANONICAL_DEPLOYMENT_READINESS_PATH = "/api/admin/deployment-readiness"

# Actions in `admin_audit` we classify as auth-related events.
_AUTH_ACTIONS = {
    "multi_login", "login", "logout", "login_failure", "login_locked",
    "password_reset", "password_change", "mfa_enroll", "mfa_verify",
    "session_revoked", "session_terminated",
}
_DEPLOY_ACTIONS = {
    "deployment_verification",
    "deployment_verification_pass",
    "deployment_verification_fail",
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
    if action in _DEPLOY_ACTIONS or action.startswith("deployment_verification"):
        # TD-0005 (historical-as-current): deployment_verification audit rows are
        # HISTORICAL point-in-time records of the automatic startup check, and one
        # is written on every backend start (so a single condition produces many
        # near-identical rows). Current deploy readiness is canonically owned by
        # /api/admin/deployment-readiness and is surfaced in this feed as
        # `deploy_blocker` CRITICAL events. A past (often repeated) NO-GO/fail
        # startup-verification row must therefore NOT be counted as a current
        # critical platform event — doing so inflates the "critical" count and
        # contradicts the canonical deploy-readiness pass. Preserve the row as
        # historical evidence at `info`; genuine current blockers flow via
        # deploy_blocker from the canonical owner.
        kind = "deploy"
        severity = "info"
    summary = f"{row.get('actor_email') or row.get('actor_id') or 'system'} · {action or 'admin action'}"
    return _mk(
        ts=row.get("ts") or row.get("at"),
        kind=kind, severity=severity, summary=summary,
        source_endpoint="/api/admin/audit",
        evidence={k: v for k, v in row.items() if k in (
            "action", "actor_id", "actor_email", "outcome", "target",
            "target_id", "ip", "ua_hash", "diff",
        )},
    )


def _from_scheduler(item: Dict[str, Any]) -> Dict[str, Any]:
    status = str(item.get("status") or item.get("outcome") or "").lower()
    severity = "warning" if status in ("fail", "failed", "error") else "info"
    return _mk(
        ts=item.get("ts") or item.get("started_at") or item.get("last_tick_ts"),
        kind="scheduler", severity=severity,
        summary=f"scheduler · {item.get('scheduler') or item.get('name', 'run')} · {status or 'ran'}",
        source_endpoint="/api/admin/scheduler-runs",
        evidence={k: v for k, v in item.items() if k in (
            "name", "scheduler", "slot_key", "status", "outcome", "duration_ms", "duration_s",
            "attempt", "error", "reason", "dedup_attempts",
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


def _from_deploy_blocker(check: Dict[str, Any], generated_at: Optional[str], *, source_endpoint: str) -> Dict[str, Any]:
    status = str(check.get("status") or check.get("decision") or "").lower()
    severity = "critical" if status in ("blocked", "fail", "failed") else "warning"
    return _mk(
        ts=check.get("ts") or generated_at,
        kind="deploy_blocker", severity=severity,
        summary=f"deploy · {check.get('id', 'check')} · {status}",
        source_endpoint=source_endpoint,
        evidence={k: v for k, v in check.items() if k in (
            "id", "status", "decision", "summary", "message", "detail", "owner", "category", "evidence", "remediation",
        )},
    )


def _event_identity(event: Dict[str, Any]) -> str:
    evidence = event.get("evidence") or {}
    kind = str(event.get("kind") or "")
    if kind == "ops_audit":
        source_id = evidence.get("action_id") or f"{evidence.get('operation_id')}::{evidence.get('mode')}"
    elif kind == "scheduler":
        source_id = evidence.get("slot_key") or f"{evidence.get('scheduler') or evidence.get('name')}::{evidence.get('status') or evidence.get('outcome')}"
    elif kind == "deploy_blocker":
        source_id = f"{evidence.get('id')}::{evidence.get('status') or evidence.get('decision')}"
    else:
        source_id = "::".join(
            str(evidence.get(k) or "")
            for k in ("action", "actor_email", "actor_id", "outcome", "target_id", "target")
        )
    return f"{event.get('source_endpoint')}::{kind}::{source_id}::{event.get('ts') or ''}::{event.get('summary') or ''}"


def _collapse_duplicate_events(events: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
    seen: Dict[str, Dict[str, Any]] = {}
    duplicate_count = 0
    for event in events:
      key = _event_identity(event)
      if key in seen:
          duplicate_count += 1
          continue
      seen[key] = event
    return list(seen.values()), duplicate_count


def _latest_event_timestamp(events: List[Dict[str, Any]], fallback: str) -> str:
    stamped = [str(event.get("ts") or "") for event in events if event.get("ts")]
    return max(stamped) if stamped else fallback


def _tally_window(events: List[Dict[str, Any]], limit: int) -> tuple[List[Dict[str, Any]], Dict[str, int], Dict[str, int], int]:
    """TD-0005: per-severity counts MUST describe exactly the events returned.

    The feed is bounded to ``limit`` for presentation. Previously ``counts`` was
    tallied over the full pre-truncation merged population while ``events`` was
    returned as ``events[:limit]`` — so the card could claim "8 critical" while
    only 6 were enumerable in the list. Counts are now computed over the SAME
    window that is returned, keeping the headline number reconcilable with the
    visible events.
    """
    window = events[: max(1, int(limit or 1))]
    counts = {"info": 0, "warning": 0, "critical": 0}
    by_kind: Dict[str, int] = {}
    auth_failures = 0
    for e in window:
        sev = e.get("severity") or "info"
        counts[sev] = counts.get(sev, 0) + 1
        kind = e.get("kind") or "audit"
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind == "auth" and sev in ("warning", "critical"):
            auth_failures += 1
    return window, counts, by_kind, auth_failures


def _build_truth_binding(
    *,
    now_iso: str,
    events: List[Dict[str, Any]],
    errors: Dict[str, str],
    duplicate_suppression_count: int,
    trust_spine_body: Dict[str, Any],
    deploy_body: Dict[str, Any],
) -> Dict[str, Any]:
    contradictions: List[str] = []
    unknowns: List[str] = []
    degradation_reasons: List[str] = []

    if errors:
        degradation_reasons.append(f"{len(errors)} child probe(s) were unavailable during this aggregate read.")
        unknowns.extend([f"probe_unavailable:{key}" for key in sorted(errors.keys())])

    if duplicate_suppression_count > 0:
        degradation_reasons.append(
            f"{duplicate_suppression_count} exact duplicate aggregate event(s) were suppressed before presentation."
        )

    trust_relationship = (trust_spine_body or {}).get("truth_relationship") or {}
    if not errors.get("trust_spine"):
        if trust_relationship.get("role") != "CANONICAL_OWNER" or trust_relationship.get("canonical_owner_id") != "trust_spine":
            contradictions.append(
                "Trust Spine authority verification failed: upstream route did not confirm trust_spine as canonical event owner."
            )
    else:
        unknowns.append("Trust Spine authority could not be verified in this request.")

    deploy_relationship = (deploy_body or {}).get("truth_relationship") or {}
    if not errors.get("deployment_readiness"):
        if deploy_relationship.get("canonical_owner_route") != _CANONICAL_DEPLOYMENT_READINESS_PATH:
            contradictions.append(
                "Canonical deployment-readiness owner route was not preserved in the child evidence."
            )
        if deploy_body.get("decision") == "pass" and (deploy_body.get("blocking_gates") or []):
            contradictions.append(
                "Canonical deployment readiness reported pass while blocking gates were still present."
            )
    else:
        unknowns.append("Canonical deployment readiness could not be verified in this request.")

    if not events:
        unknowns.append("No trust events were available in the requested window.")

    if contradictions:
        evidence_state = "contradicted"
        evidence_quality = "CORRELATED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = MISMATCH
    elif errors and not events:
        evidence_state = "unavailable"
        evidence_quality = "UNAVAILABLE"
        evidence_confidence = "UNKNOWN"
        truth_evaluation = UNVERIFIABLE
    elif errors or duplicate_suppression_count > 0:
        evidence_state = "partial"
        evidence_quality = "OBSERVED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = DEGRADED
    else:
        evidence_state = "observed"
        evidence_quality = "OBSERVED"
        evidence_confidence = "MEDIUM"
        truth_evaluation = VERIFIED

    event_ts = _latest_event_timestamp(events, now_iso)
    truth_card = canonical_truth_card(
        truth_subject="shared_operational_trust_event_feed",
        canonical_owner="trust_spine",
        truth_surface_id="occ_trust_events",
        evidence_state=evidence_state,
        evidence_quality=evidence_quality,
        evidence_confidence=evidence_confidence,
        truth_evaluation=truth_evaluation,
        permitted_claim=OBSERVED,
        claim_ceiling=OBSERVED,
        claim_basis=[
            _TRUST_SPINE_PATH,
            "/api/admin/audit",
            "/api/admin/scheduler-runs",
            "/api/admin/operations-control/audit",
            _CANONICAL_DEPLOYMENT_READINESS_PATH,
        ],
        prohibited_claims=[
            "canonical event ownership",
            "event engine authority",
            "deployment certification authority",
            "platform attestation authority",
            "trust spine replacement",
        ],
        degradation_reasons=degradation_reasons,
        unknowns=unknowns,
        contradictory_evidence=contradictions,
        evidence_timestamp=event_ts,
        evaluation_timestamp=now_iso,
        audit_reference="C2-R2-OCC-TRUST-EVENTS",
        evidence_required_to_raise_claim=[
            "direct canonical event ownership evidence",
            "registered event identity contract for the aggregate feed",
            "independent event replay and persistence evidence if the family were ever asked to claim engine authority",
        ],
        notes=[
            "OCC Trust Events is a read-only aggregator only.",
            "Trust Spine remains the canonical lifecycle event architecture.",
            "Aggregate counts do not assign or override child truth.",
        ],
    )
    return {
        "truth_surface": canonical_truth_surface("occ_trust_events"),
        "truth_relationship": projected_truth_relationship(
            surface_id="occ_trust_events",
            card=truth_card,
            canonical_owner_route=_TRUST_SPINE_PATH,
            derivation_explanation=(
                "OCC Trust Events is a read-only aggregator over existing audit and event evidence. "
                "It references Trust Spine as canonical event architecture and preserves child-source authority."
            ),
            derived_status=truth_card["truth_evaluation"],
        ),
        "ots_truth": public_ots_projection(truth_card),
        "compatibility": compatibility_projection(
            preserved_fields=7,
            deprecated_fields=0,
            new_fields=5,
            alias_fields=[],
            breaking_changes=0,
        ),
    }


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
        for h in ("x-admin-token", "x-directory-token", "authorization"):
            v = request.headers.get(h)
            if v:
                headers[h.replace("x-", "X-").title().replace("Token", "Token")] = v

        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            audit_body, sched_body, ops_body, deploy_body, trust_spine_body = await asyncio.gather(
                _get(client, f"/api/admin/audit?limit={limit}", headers),
                _get(client, f"/api/admin/scheduler-runs?limit={limit}", headers),
                _get(client, f"/api/admin/operations-control/audit?limit={limit}", headers),
                _get(client, _CANONICAL_DEPLOYMENT_READINESS_PATH, headers),
                _get(client, _TRUST_SPINE_PATH, headers),
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
            generated_at = deploy_body.get("generated_at")
            for chk in deploy_body.get("blocking_gates") or []:
                ev = _from_deploy_blocker(
                    {**chk, "status": "blocked"},
                    generated_at,
                    source_endpoint=_CANONICAL_DEPLOYMENT_READINESS_PATH,
                )
                events.append(ev)
                blockers.append(ev)
            for chk in deploy_body.get("advisory_findings") or []:
                events.append(
                    _from_deploy_blocker(
                        {**chk, "status": "warning"},
                        generated_at,
                        source_endpoint=_CANONICAL_DEPLOYMENT_READINESS_PATH,
                    )
                )
        elif isinstance(deploy_body, dict):
            errors["deployment_readiness"] = deploy_body.get("__error__", "")

        if isinstance(trust_spine_body, dict) and "__error__" in trust_spine_body:
            errors["trust_spine"] = trust_spine_body.get("__error__", "")

        events, duplicate_suppression_count = _collapse_duplicate_events(events)

        # Sort newest-first; put items without ts at the end.
        def _key(e):
            return e.get("ts") or ""
        events.sort(key=_key, reverse=True)

        # Aggregates per kind — cheap surface for domain landing cards.
        # TD-0005: counts are tallied over the RETURNED window so "N critical"
        # is always enumerable in `events` below.
        window, counts, by_kind, auth_failures = _tally_window(events, limit)

        truth_binding = _build_truth_binding(
            now_iso=now_iso,
            events=events,
            errors=errors,
            duplicate_suppression_count=duplicate_suppression_count,
            trust_spine_body=trust_spine_body if isinstance(trust_spine_body, dict) else {},
            deploy_body=deploy_body if isinstance(deploy_body, dict) else {},
        )

        return {
            "generated_at": now_iso,
            "counts": counts,
            "by_kind": by_kind,
            "auth_failures_in_window": auth_failures,
            "unresolved_blockers": blockers,
            "events": window,
            "window_event_count": len(window),
            "total_events_in_feed": len(events),
            "probe_errors": errors,
            "duplicate_suppression_count": duplicate_suppression_count,
            **truth_binding,
        }

    return api_router
