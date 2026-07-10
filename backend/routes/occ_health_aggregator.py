"""TRACK 25 · SPRINT 2 · Operations Control Center — Trust Layer aggregator.

Endpoint
--------
* ``GET /api/admin/occ/health``  — one canonical trust snapshot for OCC.

Design principles
-----------------
* **Zero new truth sources.** The aggregator fans out over the same
  child endpoints operators already use elsewhere. Every card can be
  drilled into its source URL for verification.
* **No hidden cache.** Each request re-probes fresh (client controls
  when to refresh via the OCC "Refresh" button). If a child endpoint
  is slow or fails, that specific card degrades to ``UNKNOWN`` with a
  reason — the rest of the snapshot still returns.
* **Honest UNKNOWN over fake GREEN.** Missing / unreachable data is
  labeled ``UNKNOWN`` with the exact reason (endpoint 4xx / 5xx /
  timeout / unavailable). Never invent a healthy value.
* **Per-request auth passthrough.** The caller's ``X-Admin-Token`` is
  forwarded to every child endpoint so RBAC is enforced exactly as if
  the operator hit each child endpoint directly.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Request

# Backend listens on 0.0.0.0:8001 (supervisor-managed). We fan out over
# localhost so we do not depend on the ingress being reachable from
# inside the pod (some environments block that).
_BACKEND_INTERNAL_BASE = os.environ.get(
    "OCC_HEALTH_INTERNAL_BASE",
    "http://127.0.0.1:8001",
).rstrip("/")

# Per-probe timeout. Kept small so a single stuck upstream never blocks
# the whole snapshot. Individual cards degrade to UNKNOWN on timeout.
_PROBE_TIMEOUT_S = 6.0


# ── Section + Card metadata ──────────────────────────────────────
# Each card declares:
#   id            : stable dom / test id
#   section       : one of the eight required Sprint 2 sections
#   title         : human label
#   summary_key   : plain-English description (source of truth for UI)
#   endpoint      : the source endpoint that will be probed
#   drilldown     : admin route to open for deeper investigation
#   evaluator     : callable(payload | None, err | None) → dict{
#                       status, summary, evidence, action, checked_at
#                   }
#   requires_auth : whether X-Admin-Token needs to be forwarded

SECTIONS = [
    ("platform_runtime",     "Platform Runtime"),
    ("storage_recovery",     "Storage & Recovery"),
    ("queues_workers",       "Queues & Workers"),
    ("communications",       "Communications"),
    ("ai_operations",        "AI Operations"),
    ("daily_reports",        "Daily Report Operations"),
    ("identity_security",    "HR / Identity / Security"),
    ("integrations",         "Integrations"),
]

Status = str  # "green" | "yellow" | "red" | "unknown"


def _mk(status: Status, summary: str, evidence: Optional[Dict[str, Any]] = None,
        action: Optional[str] = None, checked_at: Optional[str] = None) -> Dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "evidence": evidence or {},
        "recommended_action": action or "",
        "checked_at": checked_at,  # ISO UTC — frontend formats to local time.
    }


# ── Evaluators ────────────────────────────────────────────────────
# Each evaluator takes (body, err) and returns a normalized card
# result. ``body`` is None if the probe failed → treat as UNKNOWN
# rather than inventing GREEN.


def _eval_api_health(body, err, checked_at):
    if err or not body:
        return _mk("red", "API not reachable.", {"error": str(err or "no response")},
                   "Check backend supervisor status.", checked_at)
    ok = bool(body.get("ok"))
    return _mk("green" if ok else "red",
               f"API service {'reporting OK' if ok else 'FAILING'}",
               {"service": body.get("service"), "raw_ts": body.get("ts")},
               "" if ok else "Investigate backend logs immediately.",
               body.get("ts") or checked_at)


def _eval_version(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Version endpoint not reachable.",
                   {"error": str(err or "no response")},
                   "Restart backend supervisor if persistent.", checked_at)
    uptime_s = int(body.get("uptime_s") or 0)
    h, m = uptime_s // 3600, (uptime_s % 3600) // 60
    return _mk("green",
               f"{body.get('service', 'service')} · uptime {h}h {m}m",
               {"commit": body.get("commit"), "release": body.get("release"),
                "started_at": body.get("started_at"), "session_timeouts": body.get("session_timeouts")},
               "",
               body.get("started_at") or checked_at)


def _eval_operations_overview(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "OCC operations registry unreachable.",
                   {"error": str(err or "no response")}, "Check admin auth.", checked_at)
    ops = body.get("operations", []) or []
    critical = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "critical")
    warning = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "warning")
    unavail = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "unavailable")
    total = len(ops)
    status = "red" if critical else ("yellow" if warning or unavail else "green")
    summary = f"{total} registered ops · {critical} critical · {warning} attention · {unavail} unavailable"
    action = "Open Maintenance Operations console below and inspect the red items." if critical or warning else ""
    return _mk(status, summary,
               {"total": total, "critical": critical, "warning": warning, "unavailable": unavail},
               action, checked_at)


def _eval_recovery_snapshot(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Recovery snapshot unreachable.",
                   {"error": str(err or "no response")},
                   "Verify /api/admin/recovery/snapshot returns 200.", checked_at)
    pill = str(body.get("pill", "")).lower()
    status = {"green": "green", "yellow": "yellow", "red": "red"}.get(pill, "unknown")
    last_backup = (body.get("last_backup") or {})
    age = body.get("backup_age_minutes")
    target = body.get("backup_age_target_minutes")
    archive_count = (body.get("archive_count") or {})
    summary = (
        f"Backup age {age}m · target ≤ {target}m · "
        f"{archive_count.get('r2_total', 0)} archives in R2"
    ) if age is not None else "No backup age available."
    action = ("Investigate scheduler + R2 sync now."
              if status == "red"
              else ("Verify next backup completes on schedule." if status == "yellow" else ""))
    return _mk(status, summary,
               {"pill": pill.upper(), "backup_age_minutes": age,
                "target_minutes": target, "archive_count": archive_count,
                "rpo": body.get("rpo"), "rto": body.get("rto"),
                "last_backup": last_backup, "warnings": body.get("warnings"),
                "hourly_cadence_enabled": body.get("hourly_cadence_enabled")},
               action, last_backup.get("ts") or body.get("computed_at") or checked_at)


def _eval_backups_scheduler(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Scheduler state unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    sch = body.get("scheduler") or {}
    alive = bool(sch.get("alive"))
    resurrects = int(sch.get("resurrect_count") or 0)
    in_progress = bool(sch.get("in_progress"))
    if not alive and resurrects > 3:
        status, summary = "red", f"Scheduler not alive · {resurrects} resurrects."
        action = "Investigate backup scheduler loop crash (see /admin/scheduler-runs)."
    elif not alive:
        status, summary = "yellow", "Scheduler dormant (may auto-resurrect on next tick)."
        action = "Watch for auto-resurrect within the next hour."
    else:
        status, summary = "green", f"Scheduler alive{' · run in progress' if in_progress else ''}."
        action = ""
    return _mk(status, summary,
               {"alive": alive, "resurrect_count": resurrects, "in_progress": in_progress,
                "last_tick_ts": sch.get("last_tick_ts"),
                "last_attempt_outcome": sch.get("last_attempt_outcome"),
                "boot_step": sch.get("boot_step"),
                "boot_exception": sch.get("boot_exception")},
               action, sch.get("last_tick_ts") or sch.get("last_resurrect_ts") or checked_at)


def _eval_integrations(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Integration probes unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    probes = body.get("probes") or []
    degraded = [p for p in probes if p.get("status") not in ("ok", "healthy")]
    overall = str(body.get("overall_status") or "").lower()
    if overall == "critical" or degraded:
        status = "red"
    elif overall == "warning":
        status = "yellow"
    else:
        status = "green"
    summary = f"{len(probes) - len(degraded)}/{len(probes)} probes healthy"
    action = ("Open Platform Configuration → Integrations to inspect degraded probes."
              if degraded else "")
    return _mk(status, summary,
               {"probes": probes, "overall_status": body.get("overall_status")},
               action, body.get("checked_at") or checked_at)


def _eval_email_v2(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Email routing status unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    empty = list(body.get("critical_empty_route_keys") or [])
    band = str(body.get("band") or "").lower()
    mode = body.get("mode") or "—"
    if empty or band == "red":
        status = "red"
    elif band in ("yellow", "amber"):
        status = "yellow"
    else:
        status = "green"
    counts = body.get("route_counts") or {}
    summary = f"Mode {mode} · {counts.get('total', 0)} routes · {len(empty)} critical route(s) empty"
    if empty:
        action = "Fill or reroute the missing critical route keys."
    elif status == "yellow":
        action = body.get("band_reason") or "Investigate email routing degradation."
    else:
        action = ""
    return _mk(status, summary,
               {"mode": mode, "band": band, "route_counts": counts,
                "critical_empty_route_keys": empty,
                "audit_counters": body.get("audit_counters"),
                "last_v2_audit_age_minutes": body.get("last_v2_audit_age_minutes"),
                "band_reason": body.get("band_reason")},
               action, body.get("ts") or checked_at)


def _eval_ai_gateway(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "AI gateway status unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    enabled = bool(body.get("gateway_enabled"))
    tenant_default = bool(body.get("tenant_ai_default_enabled"))
    resolved_ok = bool(body.get("resolved_provider_available"))
    provider = body.get("resolved_selected_provider") or body.get("default_provider") or "—"
    if not enabled:
        status, summary = "yellow", f"Gateway OFF · tenant default {'ON' if tenant_default else 'OFF'}."
        action = "Enable in AI configuration only if platform requires AI."
    elif not resolved_ok:
        status, summary = "red", f"Gateway ON · resolved provider {provider} UNAVAILABLE."
        action = "Rotate provider key or switch failover provider."
    else:
        status, summary = "green", f"Gateway ON · provider {provider} available."
        action = ""
    return _mk(status, summary,
               {"gateway_enabled": enabled, "tenant_ai_default_enabled": tenant_default,
                "resolved_provider": provider,
                "resolved_provider_available": resolved_ok,
                "modules": body.get("modules"),
                "transport": body.get("transport")},
               action, checked_at)


def _eval_draft_health(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Draft health endpoint unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    buckets = body.get("buckets") or {}
    abandoned = int(buckets.get("abandoned_gt_24h", 0) or 0)
    failed = int(buckets.get("failed_last_24h", 0) or 0)
    stale = int(buckets.get("stale_1h_to_24h", 0) or 0)
    if failed > 0 or abandoned > 5:
        status = "red"
    elif abandoned > 0 or stale > 0:
        status = "yellow"
    else:
        status = "green"
    summary = (
        f"{failed} failed / {abandoned} abandoned / {stale} stale drafts (24h window)"
    )
    action = ("Investigate failed drafts in daily reports admin queue." if failed
              else "Encourage abandoned drafts to be completed or discarded." if abandoned
              else "")
    return _mk(status, summary,
               {"buckets": buckets, "sources": body.get("sources")},
               action, body.get("generated_at") or checked_at)


def _eval_sessions(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Session inventory unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    count = int(body.get("count") or 0)
    timeouts_on = bool(body.get("timeouts_enabled"))
    summary = f"{count} active session(s) · timeouts {'on' if timeouts_on else 'OFF'}"
    status = "green" if timeouts_on else "yellow"
    action = "Enable session timeouts before production." if not timeouts_on else ""
    return _mk(status, summary,
               {"count": count, "timeouts_enabled": timeouts_on,
                "tiers": body.get("tiers")},
               action, body.get("server_now") or checked_at)


def _eval_governance(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Governance summary unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    sev = body.get("severity_counts") or {}
    highs = int(sev.get("high", 0) or 0) + int(sev.get("critical", 0) or 0)
    health = str(body.get("health_label") or "").lower()
    if health == "critical" or highs > 20:
        status = "red"
    elif health == "warning" or highs > 0:
        status = "yellow"
    else:
        status = "green"
    summary = f"{highs} high/critical rules · health label: {body.get('health_label', 'unknown')}"
    action = ("Open Governance & Trust to triage high-severity rules."
              if highs else "")
    # `last_scan` from the governance endpoint is an object, not an ISO
    # string. Only forward it into `checked_at` if it is a string.
    last_scan = body.get("last_scan")
    stamp = last_scan if isinstance(last_scan, str) else checked_at
    return _mk(status, summary,
               {"severity_counts": sev, "status_counts": body.get("status_counts"),
                "health_label": body.get("health_label"),
                "convergence_score": body.get("convergence_score"),
                "rule_counts": body.get("rule_counts"),
                "last_scan": last_scan},
               action, stamp)


def _eval_production_cert(body, err, checked_at):
    if err or not body:
        return _mk("unknown", "Production certification endpoint unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    band = str(body.get("platform_band") or "").lower()
    if band in ("green", "healthy"):
        status = "green"
    elif band in ("yellow", "warning"):
        status = "yellow"
    elif band in ("red", "critical"):
        status = "red"
    else:
        status = "unknown"
    counters = body.get("counters") or {}
    summary = f"Platform band: {band or 'unknown'} · {counters.get('workflows_certified', 0)} workflows certified"
    return _mk(status, summary,
               {"platform_band": band, "counters": counters,
                "workflows_summary_len": len(body.get("workflows") or [])},
               "", body.get("generated_at") or checked_at)


# ── Card manifest ─────────────────────────────────────────────────
CARDS: List[Dict[str, Any]] = [
    # 1 · Platform Runtime -----------------------------------------
    dict(id="api_health", section="platform_runtime", title="API Health",
         endpoint="/api/health", drilldown="/admin/system-health",
         requires_auth=False, evaluator=_eval_api_health),
    dict(id="version", section="platform_runtime", title="Build & Uptime",
         endpoint="/api/version", drilldown="/admin/system-health",
         requires_auth=False, evaluator=_eval_version),
    dict(id="operations_registry", section="platform_runtime",
         title="Registered Maintenance Ops",
         endpoint="/api/admin/operations-control/overview",
         drilldown="/admin/operations-control", requires_auth=True,
         evaluator=_eval_operations_overview),
    # 2 · Storage & Recovery ---------------------------------------
    dict(id="recovery_snapshot", section="storage_recovery",
         title="Backups & R2 Recovery",
         endpoint="/api/admin/recovery/snapshot",
         drilldown="/admin/storage-recovery", requires_auth=True,
         evaluator=_eval_recovery_snapshot),
    # 3 · Queues & Workers -----------------------------------------
    dict(id="backup_scheduler", section="queues_workers",
         title="Backup Scheduler Loop",
         endpoint="/api/admin/backups-scheduler-state",
         drilldown="/admin/scheduler-runs", requires_auth=True,
         evaluator=_eval_backups_scheduler),
    # 4 · Communications -------------------------------------------
    dict(id="email_v2", section="communications", title="Email Routing (v2)",
         endpoint="/api/admin/email-routing/v2/status",
         drilldown="/admin/email", requires_auth=True, evaluator=_eval_email_v2),
    # 5 · AI Operations --------------------------------------------
    dict(id="ai_gateway", section="ai_operations", title="AI Gateway",
         endpoint="/api/ai/gateway/status",
         drilldown="/admin/ai-configuration", requires_auth=True,
         evaluator=_eval_ai_gateway),
    # 6 · Daily Report Operations ----------------------------------
    dict(id="daily_report_drafts", section="daily_reports",
         title="Daily Report Drafts Health",
         endpoint="/api/admin/draft-health",
         drilldown="/admin/daily", requires_auth=True,
         evaluator=_eval_draft_health),
    # 7 · HR / Identity / Security ---------------------------------
    dict(id="sessions", section="identity_security",
         title="Active Sessions",
         endpoint="/api/admin/sessions/recent",
         drilldown="/admin/sessions", requires_auth=True,
         evaluator=_eval_sessions),
    dict(id="governance", section="identity_security",
         title="Governance & Trust",
         endpoint="/api/admin/governance/summary",
         drilldown="/admin/governance", requires_auth=True,
         evaluator=_eval_governance),
    dict(id="production_certification", section="identity_security",
         title="Production Certification",
         endpoint="/api/admin/production-certification",
         drilldown="/admin/governance", requires_auth=True,
         evaluator=_eval_production_cert),
    # 8 · Integrations ---------------------------------------------
    dict(id="integrations", section="integrations",
         title="Integration Probes",
         endpoint="/api/admin/integrations/health",
         drilldown="/admin/integrations", requires_auth=True,
         evaluator=_eval_integrations),
]


# ── Fan-out probe ─────────────────────────────────────────────────
async def _probe_one(client: httpx.AsyncClient, card_meta: Dict[str, Any],
                     headers: Dict[str, str], now_iso: str) -> Dict[str, Any]:
    url = _BACKEND_INTERNAL_BASE + card_meta["endpoint"]
    hdrs = headers if card_meta.get("requires_auth") else {}
    try:
        r = await client.get(url, headers=hdrs)
        if r.status_code >= 400:
            evaluated = card_meta["evaluator"](None, f"HTTP {r.status_code}", now_iso)
        else:
            evaluated = card_meta["evaluator"](r.json(), None, now_iso)
    except Exception as e:  # noqa: BLE001
        evaluated = card_meta["evaluator"](None, f"{type(e).__name__}: {e}", now_iso)
    return {
        "id": card_meta["id"],
        "section": card_meta["section"],
        "title": card_meta["title"],
        "endpoint": card_meta["endpoint"],
        "drilldown": card_meta["drilldown"],
        **evaluated,
    }


# ── FastAPI route registration ────────────────────────────────────
def register_occ_health_routes(api_router: APIRouter, require_admin: Callable):
    """Attach ``GET /api/admin/occ/health`` to the platform api_router.

    The endpoint has no server-side cache — every call re-probes fresh.
    The client (OCC frontend) controls when refresh happens via its
    Refresh button and shows the last-checked local time to operators.
    """

    @api_router.get("/admin/occ/health")
    async def occ_health(
        request: Request,
        actor: Any = Depends(require_admin),  # noqa: ARG001 · gate only
    ) -> Dict[str, Any]:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        # Forward the caller's admin token so RBAC on child endpoints
        # sees the same identity. We accept either the canonical
        # X-Admin-Token or the legacy Authorization: Bearer <token>
        # header (both are already used elsewhere).
        headers: Dict[str, str] = {}
        for h in ("x-admin-token", "authorization"):
            v = request.headers.get(h)
            if v:
                headers[h.replace("x-", "X-").title().replace("Token", "Token")] = v

        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            probes: List[Awaitable] = [
                _probe_one(client, card, headers, now_iso) for card in CARDS
            ]
            results = await asyncio.gather(*probes, return_exceptions=False)

        # Group results by section, preserving the declared section order.
        sections: List[Dict[str, Any]] = []
        by_section: Dict[str, List[Dict[str, Any]]] = {sid: [] for sid, _ in SECTIONS}
        for r in results:
            by_section.setdefault(r["section"], []).append(r)
        for section_id, section_label in SECTIONS:
            cards = by_section.get(section_id, [])
            worst = _worst_status(cards)
            sections.append({
                "id": section_id,
                "label": section_label,
                "status": worst,
                "cards": cards,
            })

        # Overall posture = worst status across all cards.
        overall = _worst_status(results)
        counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1

        return {
            "generated_at": now_iso,
            "overall_status": overall,
            "counts": counts,
            "total_cards": len(results),
            "sections": sections,
        }

    return api_router


def _worst_status(cards: List[Dict[str, Any]]) -> Status:
    order = {"red": 3, "yellow": 2, "unknown": 1, "green": 0}
    worst = "green"
    for c in cards:
        s = c.get("status", "green")
        if order.get(s, 0) > order.get(worst, 0):
            worst = s
    return worst
