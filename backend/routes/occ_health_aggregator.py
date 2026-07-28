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

from lib.canonical_truth import canonical_truth_surface, derived_truth_payload
from lib.runtime_identity import runtime_identity_public_payload

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

Status = str


def _mk(status: Status, summary: str, evidence: Optional[Dict[str, Any]] = None,
        action: Optional[str] = None, checked_at: Optional[str] = None,
        *, canonical_status: Optional[str] = None,
        root_cause_id: Optional[str] = None,
        applicable: bool = True, enabled: bool = True,
        reason_code: Optional[str] = None) -> Dict[str, Any]:
    # TRACK 28.11 · Every card carries a canonical status field so
    # Diagnostics + OCC + system-health speak the same vocabulary.
    from lib.canonical_status import to_canonical  # local import for cycles
    return {
        "status": status,
        "canonical_status": canonical_status or to_canonical(
            status, applicable=applicable, enabled=enabled),
        "summary": summary,
        "evidence": evidence or {},
        "recommended_action": action or "",
        "reason_code": reason_code or "",
        "root_cause_id": root_cause_id,
        "applicable": applicable,
        "enabled": enabled,
        "checked_at": checked_at,  # ISO UTC — frontend formats to local time.
    }


# ── Evaluators ────────────────────────────────────────────────────
# Each evaluator takes (body, err) and returns a normalized card
# result. ``body`` is None if the probe failed → treat as UNKNOWN
# rather than inventing GREEN.


def _eval_api_health(body, err, checked_at):
    if err or not body:
        return _mk("MISMATCH", "API not reachable.", {"error": str(err or "no response")},
                   "Check backend supervisor status.", checked_at)
    ok = bool(body.get("ok"))
    return _mk("VERIFIED" if ok else "MISMATCH",
               f"API service {'reporting OK' if ok else 'FAILING'}",
               {"service": body.get("service"), "raw_ts": body.get("ts")},
               "" if ok else "Investigate backend logs immediately.",
               body.get("ts") or checked_at)


def _eval_version(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Version endpoint not reachable.",
                   {"error": str(err or "no response")},
                   "Restart backend supervisor if persistent.", checked_at)
    uptime_s = int(body.get("uptime_s") or 0)
    h, m = uptime_s // 3600, (uptime_s % 3600) // 60
    return _mk("VERIFIED",
               f"{body.get('service', 'service')} · uptime {h}h {m}m",
               {"commit": body.get("commit"), "release": body.get("release"),
                "started_at": body.get("started_at"), "session_timeouts": body.get("session_timeouts")},
               "",
               body.get("started_at") or checked_at)


def _eval_operations_overview(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "OCC operations registry unreachable.",
                   {"error": str(err or "no response")}, "Check admin auth.", checked_at)
    ops = body.get("operations", []) or []
    critical = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "critical")
    warning = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "warning")
    unavail = sum(1 for o in ops if (o.get("status_snapshot") or {}).get("status") == "unavailable")
    total = len(ops)
    status = "MISMATCH" if critical else ("DEGRADED" if warning or unavail else "VERIFIED")
    summary = f"{total} registered ops · {critical} critical · {warning} attention · {unavail} unavailable"
    action = "Open Maintenance Operations console below and inspect the red items." if critical or warning else ""
    return _mk(status, summary,
               {"total": total, "critical": critical, "warning": warning, "unavailable": unavail},
               action, checked_at)


def _eval_recovery_snapshot(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Recovery snapshot unreachable.",
                   {"error": str(err or "no response")},
                   "Verify /api/admin/recovery/snapshot returns 200.", checked_at)

    # TRACK 28.09D · Backup Health Severity Aggregator Repair.
    # Previous bug 1: `pill_map` was missing "amber" (recovery_dashboard
    # emits AMBER/GREEN/RED uppercase, not YELLOW). This silently
    # downgraded AMBER pills to "unknown" and mis-triggered CRITICAL.
    # Previous bug 2: a single hardcoded action ("Investigate scheduler
    # + R2 sync now.") was shown for every RED, even when scheduler and
    # R2 were both healthy and the real cause was a null restore drill,
    # bucket capacity, integrity failure, etc.
    # Fix: (a) accept every real pill vocabulary the endpoint emits,
    # (b) derive a reason_code from the actual evidence, (c) route the
    # recommended action off that reason_code so the card, evidence,
    # and action always tell the same story.
    pill_raw = str(body.get("pill", ""))
    pill = pill_raw.lower()
    status = {
        "green": "VERIFIED",
        "yellow": "DEGRADED",
        "amber": "DEGRADED",
        "red": "MISMATCH",
        "critical": "MISMATCH",
    }.get(pill, "UNVERIFIABLE")

    last_backup = (body.get("last_backup") or {})
    age = body.get("backup_age_minutes")
    target = body.get("backup_age_target_minutes")
    archive_count = (body.get("archive_count") or {})
    rpo = body.get("rpo") or {}
    rto = body.get("rto") or {}
    bucket_usage = body.get("bucket_usage") or {}
    scheduler = body.get("scheduler") or {}
    warnings = body.get("warnings") or []
    last_drill = body.get("last_drill")
    last_backup_ok = last_backup.get("ok")
    hourly_activation = body.get("hourly_activation") or {}
    failures_7d = body.get("failures_7d") or 0
    if isinstance(failures_7d, list):
        failures_7d = len(failures_7d)
    elif isinstance(failures_7d, dict):
        total_failures = 0
        for value in failures_7d.values():
            try:
                total_failures += int(value or 0)
            except Exception:  # noqa: BLE001
                continue
        failures_7d = total_failures
    else:
        try:
            failures_7d = int(failures_7d or 0)
        except Exception:  # noqa: BLE001
            failures_7d = 0

    # Derive the primary reason for the observed status. Order matters —
    # highest-severity, most-specific cause wins.
    reason_code = "healthy"
    reason_text = "Backups & R2 healthy."
    if last_backup_ok is False:
        reason_code, reason_text = "backup_failed", "Last backup attempt failed."
    elif age is None:
        reason_code, reason_text = "no_backup_evidence", "No recent backup evidence available."
    elif str(bucket_usage.get("status", "")).upper() == "RED":
        reason_code = "bucket_over_alert"
        reason_text = (
            f"R2 bucket usage {bucket_usage.get('gb', 0)} GB above alert "
            f"threshold {bucket_usage.get('alert_gb', 0)} GB."
        )
    elif target is not None and age > 2 * target:
        reason_code = "backup_stale_critical"
        reason_text = f"Backup age {age:.1f}m exceeds 2× target ({target}m)."
    elif target is not None and age > target:
        reason_code = "backup_stale"
        reason_text = f"Backup age {age:.1f}m exceeds target ({target}m)."
    elif str(hourly_activation.get("activation_status", "")).upper() == "BLOCKED BY SAFETY GUARD":
        reason_code = "hourly_blocked_by_safety_guard"
        reason_text = "Hourly complete R2 is blocked by a safety guard."
    elif failures_7d > 0:
        reason_code = "recent_failures"
        reason_text = f"{failures_7d} backup failure(s) in last 7 days."
    elif str(bucket_usage.get("status", "")).upper() == "AMBER":
        reason_code = "bucket_over_warn"
        reason_text = (
            f"R2 bucket usage {bucket_usage.get('gb', 0)} GB above warn "
            f"threshold {bucket_usage.get('warn_gb', 0)} GB."
        )
    elif not scheduler.get("is_healthy", scheduler.get("alive", True)):
        # Scheduler-quiet does not by itself drive the pill (recovery_dashboard
        # only adds it as a warning), but if the pill IS yellow/red and no
        # other cause fits, surface scheduler explicitly rather than mixing
        # it into the freshness message.
        reason_code = "scheduler_quiet"
        reason_text = "Backup scheduler heartbeat is quiet."

    # Recommended action — reason-specific, not a one-size-fits-all message.
    action_by_reason = {
        "healthy": "",
        "backup_failed": "Open Storage & Recovery → run backup verification, then re-trigger backup.",
        "no_backup_evidence": "Open Storage & Recovery to trigger a fresh backup and confirm evidence.",
        "bucket_over_alert": "Open Storage & Recovery → R2 Lifecycle to review capacity and rotate old archives.",
        "backup_stale_critical": "Trigger a fresh backup immediately and confirm a new recoverable archive lands.",
        "backup_stale": "Verify the next backup completes on schedule.",
        "hourly_blocked_by_safety_guard": "Open Storage & Recovery → Backup Scheduler and clear the active/stale blocker before trusting hourly cadence.",
        "recent_failures": "Open Storage & Recovery → Backup History to inspect recent failures.",
        "bucket_over_warn": "Plan R2 capacity review; usage approaching alert threshold.",
        "scheduler_quiet": "Check /admin/scheduler-runs; scheduler heartbeat is quiet.",
    }
    action = action_by_reason.get(reason_code, "")

    # Truthful headline: separate backup freshness from restore readiness.
    rpo_status = str(rpo.get("status", "")).upper()
    rto_status = str(rto.get("status", "")).upper()
    rto_drill_min = rto.get("last_drill_min")
    freshness_summary = (
        f"Backup {age:.1f}m old · target ≤ {target}m · "
        f"{archive_count.get('r2_total', 0)} archives in R2"
    ) if age is not None else "No backup age available."
    if rto_drill_min is None:
        restore_summary = "Restore drill: not yet run."
    else:
        restore_summary = f"Restore drill: last completed in {rto_drill_min}m."
    summary = f"{freshness_summary}  {restore_summary}"

    return _mk(status, summary,
               {
                   "pill": pill_raw.upper() or "UNKNOWN",
                   "reason_code": reason_code,
                   "reason": reason_text,
                   "backup_age_minutes": age,
                   "target_minutes": target,
                   "archive_count": archive_count,
                   "rpo": rpo,
                   "rto": rto,
                   "bucket_usage": bucket_usage,
                   "scheduler": {
                       "alive": scheduler.get("alive"),
                       "is_healthy": scheduler.get("is_healthy"),
                   },
                   "last_backup": last_backup,
                   "last_drill": last_drill,
                   "warnings": warnings,
                   "hourly_cadence_enabled": body.get("hourly_cadence_enabled"),
                   "hourly_activation": hourly_activation,
               },
               action,
               last_backup.get("ts") or body.get("computed_at") or checked_at,
               # TRACK 28.11 · Tag cards whose criticality is driven by
               # the same shared root cause (R2 bucket over threshold)
               # so Diagnostics can display them under a single "why"
               # explanation instead of two independent disasters.
               root_cause_id=(
                   "r2_bucket_capacity"
                   if reason_code in ("bucket_over_alert", "bucket_over_warn")
                   else None
               ),
               reason_code=reason_code)

def _eval_storage_health(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Storage lifecycle unreachable.",
                   {"error": str(err or "no response")},
                   "Trigger a lifecycle scan from Storage & Recovery.", checked_at)
    band = str(body.get("band", "unknown")).lower()
    status = {"green": "VERIFIED", "amber": "DEGRADED", "red": "MISMATCH"}.get(band, "UNVERIFIABLE")
    score = body.get("overall_score", 0)
    capacity = body.get("capacity") or {}
    objects = body.get("objects") or {}
    orphan_pct = objects.get("orphan_pct")
    summary = (
        f"Score {score}/100 · {capacity.get('gb', 0):.1f} GB · "
        f"{objects.get('total', 0)} objects · "
        f"{objects.get('verified_orphan', 0)} orphan candidates"
        f"{' (' + str(orphan_pct) + '%)' if orphan_pct is not None else ''}"
    )
    action = (
        "Open Storage & Recovery → R2 Lifecycle to review the dry-run."
        if status in ("MISMATCH", "DEGRADED") else ""
    )
    return _mk(status, summary,
               {"overall_score": score, "band": band.upper(),
                "sub_scores": body.get("sub_scores"),
                "capacity": capacity, "objects": objects,
                "freshness": body.get("freshness")},
               action, body.get("generated_at") or checked_at,
               # TRACK 28.11 · When lifecycle status is driven by
               # capacity being over threshold, share the same
               # root_cause_id as the recovery_snapshot card so a
               # single R2-bucket-over-threshold issue is not
               # counted as two independent disasters.
               root_cause_id=(
                   "r2_bucket_capacity"
                   if capacity.get("over_alert") or (band in ("amber", "red")
                                                     and capacity.get("gb", 0)
                                                     >= capacity.get("warn_gb", 1e9))
                   else None
               ),
               reason_code=(
                   "storage_lifecycle_healthy" if status == "green"
                   else "storage_lifecycle_needs_review"
               ))




def _eval_backups_scheduler(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Scheduler state unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    sch = body.get("scheduler") or {}
    alive = bool(sch.get("alive"))
    resurrects = int(sch.get("resurrect_count") or 0)
    in_progress = bool(sch.get("in_progress"))
    if not alive and resurrects > 3:
        status, summary = "MISMATCH", f"Scheduler not alive · {resurrects} resurrects."
        action = "Investigate backup scheduler loop crash (see /admin/scheduler-runs)."
    elif not alive:
        status, summary = "DEGRADED", "Scheduler dormant (may auto-resurrect on next tick)."
        action = "Watch for auto-resurrect within the next hour."
    else:
        status, summary = "VERIFIED", f"Scheduler alive{' · run in progress' if in_progress else ''}."
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
        return _mk("UNVERIFIABLE", "Integration probes unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    probes = body.get("probes") or []
    # TRACK 28.11: A probe whose status is "disabled" AND explicitly
    # `mocked=True` is an intentional stub — the integration is
    # NOT_APPLICABLE to this tenant (e.g. MASCI does not use
    # MaintainX). Such probes must NOT be counted as degraded and
    # must NOT escalate the parent card. Annotate each probe with a
    # canonical status so the UI can render the neutral badge.
    from lib.canonical_status import (  # noqa: PLC0415
        to_canonical, NOT_APPLICABLE, DISABLED,
    )
    def _is_intentional_stub(p):
        st = str(p.get("status") or "").lower()
        return st == "disabled" and bool(p.get("mocked"))

    for p in probes:
        if _is_intentional_stub(p):
            p["canonical_status"] = NOT_APPLICABLE
            p["applicable"] = False
            if not p.get("message"):
                p["message"] = "Not applicable — this tenant does not use this integration."
        else:
            p["canonical_status"] = to_canonical(p.get("status"))
            p["applicable"] = True

    live_probes = [p for p in probes if p.get("applicable")]
    stubbed = [p for p in probes if not p.get("applicable")]
    degraded = [p for p in live_probes if p.get("canonical_status") != "VERIFIED"]
    overall = str(body.get("overall_status") or "").lower()
    if overall == "critical" or degraded:
        status = "MISMATCH"
    elif overall == "warning":
        status = "DEGRADED"
    elif any(p.get("canonical_status") in {"DEGRADED", "UNVERIFIABLE"} for p in degraded):
        status = "DEGRADED"
    else:
        status = "VERIFIED"
    healthy_live = len(live_probes) - len(degraded)
    total_live = len(live_probes)
    stub_note = f" · {len(stubbed)} not applicable" if stubbed else ""
    summary = f"{healthy_live}/{total_live} live integration probes healthy{stub_note}"
    action = ("Open Platform Configuration → Integrations to inspect degraded probes."
              if degraded else "")
    return _mk(status, summary,
               {"probes": probes, "overall_status": body.get("overall_status"),
                "not_applicable_probe_ids": [p.get("id") for p in stubbed]},
               action, body.get("checked_at") or checked_at,
               reason_code=("integrations_healthy" if status == "VERIFIED"
                            else "integrations_degraded"))


def _eval_email_v2(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Email routing status unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    empty = list(body.get("critical_empty_route_keys") or [])
    band = str(body.get("band") or "").lower()
    mode = body.get("mode") or "—"
    if empty or band == "red":
        status = "MISMATCH"
    elif band in ("yellow", "amber"):
        status = "DEGRADED"
    else:
        status = "VERIFIED"
    counts = body.get("route_counts") or {}
    summary = f"Mode {mode} · {counts.get('total', 0)} routes · {len(empty)} critical route(s) empty"
    if empty:
        action = "Fill or reroute the missing critical route keys."
    elif status == "DEGRADED":
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
        return _mk("UNVERIFIABLE", "AI gateway status unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    enabled = bool(body.get("gateway_enabled"))
    tenant_default = bool(body.get("tenant_ai_default_enabled"))
    resolved_ok = bool(body.get("resolved_provider_available"))
    provider = body.get("resolved_selected_provider") or body.get("default_provider") or "—"
    if not enabled:
        status, summary = "DEGRADED", f"Gateway OFF · tenant default {'ON' if tenant_default else 'OFF'}."
        action = "Enable in AI configuration only if platform requires AI."
    elif not resolved_ok:
        status, summary = "MISMATCH", f"Gateway ON · resolved provider {provider} UNAVAILABLE."
        action = "Rotate provider key or switch failover provider."
    else:
        status, summary = "VERIFIED", f"Gateway ON · provider {provider} available."
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
        return _mk("UNVERIFIABLE", "Draft health endpoint unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    buckets = body.get("buckets") or {}
    abandoned = int(buckets.get("abandoned_gt_24h", 0) or 0)
    failed = int(buckets.get("failed_last_24h", 0) or 0)
    stale = int(buckets.get("stale_1h_to_24h", 0) or 0)
    if failed > 0 or abandoned > 5:
        status = "MISMATCH"
    elif abandoned > 0 or stale > 0:
        status = "DEGRADED"
    else:
        status = "VERIFIED"
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
        return _mk("UNVERIFIABLE", "Session inventory unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    count = int(body.get("count") or 0)
    timeouts_on = bool(body.get("timeouts_enabled"))
    summary = f"{count} active session(s) · timeouts {'on' if timeouts_on else 'OFF'}"
    status = "VERIFIED" if timeouts_on else "DEGRADED"
    action = "Enable session timeouts before production." if not timeouts_on else ""
    return _mk(status, summary,
               {"count": count, "timeouts_enabled": timeouts_on,
                "tiers": body.get("tiers")},
               action, body.get("server_now") or checked_at)


def _eval_governance(body, err, checked_at):
    if err or not body:
        return _mk("UNVERIFIABLE", "Governance summary unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    sev = body.get("severity_counts") or {}
    highs = int(sev.get("high", 0) or 0) + int(sev.get("critical", 0) or 0)
    health = str(body.get("health_label") or "").lower()
    if health == "critical" or highs > 20:
        status = "MISMATCH"
    elif health == "warning" or highs > 0:
        status = "DEGRADED"
    else:
        status = "VERIFIED"
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
        return _mk("UNVERIFIABLE", "Production certification endpoint unreachable.",
                   {"error": str(err or "no response")}, "", checked_at)
    band = str(body.get("platform_band") or "").lower()
    if band in ("green", "healthy"):
        status = "VERIFIED"
    elif band in ("yellow", "amber", "warning"):
        status = "DEGRADED"
    elif band in ("red", "critical"):
        status = "MISMATCH"
    else:
        status = "UNVERIFIABLE"
    counters = body.get("counters") or {}
    workflows = body.get("workflows") or body.get("workflows_summary") or []
    if isinstance(workflows, list):
        workflows_len = len(workflows)
    else:
        try:
            workflows_len = int(workflows or 0)
        except Exception:  # noqa: BLE001
            workflows_len = 0
    summary = f"Platform band: {band or 'unknown'} · {counters.get('workflows_certified', 0)} workflows certified"
    return _mk(status, summary,
               {"platform_band": band, "counters": counters,
                "workflows_summary_len": workflows_len},
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
    dict(id="storage_health", section="storage_recovery",
         title="R2 Storage Lifecycle Health",
         endpoint="/api/admin/r2/lifecycle/health",
         drilldown="/admin/storage-recovery", requires_auth=True,
         evaluator=_eval_storage_health),
    # 3 · Queues & Workers -----------------------------------------
    dict(id="backup_scheduler", section="queues_workers",
         title="Backup Scheduler Loop",
         endpoint="/api/admin/backups-scheduler-state",
         drilldown="/admin/scheduler-runs", requires_auth=True,
         evaluator=_eval_backups_scheduler),
    # 4 · Communications -------------------------------------------
    dict(id="email_v2", section="communications", title="Email Routing",
         endpoint="/api/admin/email-routing/v2/status",
         drilldown="/admin/communications", requires_auth=True, evaluator=_eval_email_v2),
    # 5 · AI Operations --------------------------------------------
    dict(id="ai_gateway", section="ai_operations", title="AI Gateway",
         endpoint="/api/ai/gateway/status",
         drilldown="/admin/ai-operations", requires_auth=True,
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
         drilldown="/admin/identity-security", requires_auth=True,
         evaluator=_eval_sessions),
    dict(id="governance", section="identity_security",
         title="Governance & Trust",
         endpoint="/api/admin/governance/summary",
         drilldown="/admin/governance-trust", requires_auth=True,
         evaluator=_eval_governance),
    dict(id="production_certification", section="identity_security",
         title="Production Certification",
         endpoint="/api/admin/production-certification",
         drilldown="/admin/governance-trust", requires_auth=True,
         evaluator=_eval_production_cert),
    # 8 · Integrations ---------------------------------------------
    dict(id="integrations", section="integrations",
         title="Integration Probes",
         endpoint="/api/admin/integrations/health",
         drilldown="/admin/platform-configuration", requires_auth=True,
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
        "source_probe_state": "probe_failure" if isinstance(evaluated.get("evidence"), dict) and evaluated.get("evidence", {}).get("error") else "source_success",
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
        for h in ("x-admin-token", "x-directory-token", "authorization"):
            v = request.headers.get(h)
            if v:
                headers[h.replace("x-", "X-").title().replace("Token", "Token")] = v

        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            probes: List[Awaitable] = [
                _probe_one(client, card, headers, now_iso) for card in CARDS
            ]
            results = await asyncio.gather(*probes, return_exceptions=False)

        bundle = getattr(getattr(request, "app", None).state, "runtime_identity_bundle", None)
        runtime_identity = runtime_identity_public_payload(bundle) if bundle else None
        runtime_identity_card = {
            "id": "runtime_identity",
            "section": "platform_runtime",
            "title": "Runtime Identity Authority",
            "endpoint": "internal:runtime_identity_bundle",
            "drilldown": "/admin/system-health",
            "status": (runtime_identity or {}).get("status", "UNVERIFIABLE"),
            "canonical_status": (runtime_identity or {}).get("status", "UNVERIFIABLE"),
            "summary": ((runtime_identity or {}).get("validation") or {}).get("detail") or "Runtime identity unavailable.",
            "evidence": runtime_identity or {},
            "recommended_action": "" if (runtime_identity or {}).get("valid") else "Resolve runtime identity authority before trusting downstream surfaces.",
            "reason_code": (runtime_identity or {}).get("mismatch_category") or "runtime_identity",
            "root_cause_id": "runtime_identity_authority",
            "applicable": True,
            "enabled": True,
            "checked_at": now_iso,
        }
        results = [runtime_identity_card, *results]

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

        # Overall posture should reflect actionable verified child truth.
        # A single UNVERIFIABLE card must not outrank fresh VERIFIED/DEGRADED
        # child surfaces and collapse the whole OCC snapshot to UNKNOWN.
        canonical_overall = _worst_status(results)
        if any(r.get("status") == "MISMATCH" for r in results):
            overall = "MISMATCH"
        elif any(r.get("status") == "DEGRADED" for r in results):
            overall = "DEGRADED"
        elif any(r.get("status") == "VERIFIED" for r in results):
            overall = "VERIFIED"
        else:
            overall = canonical_overall
        counts = {"VERIFIED": 0, "DEGRADED": 0, "MISMATCH": 0, "UNVERIFIABLE": 0, "NOT_APPLICABLE": 0}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1

        # TRACK 28.11 · Canonical counts + shared-root-cause grouping.
        # Diagnostics and OCC must speak one vocabulary and never
        # double-count a single root cause. We keep the legacy counts
        # dict for backward compatibility and add canonical_counts +
        # root_cause_groups alongside it.
        from lib.canonical_status import summarize as _canon_summarize  # noqa: PLC0415
        canonical_summary = _canon_summarize(results)
        # Collect unique root_cause_id references so Diagnostics can
        # display the shared "why" (e.g. two RED cards both driven by
        # r2_bucket_capacity → one root cause, not two disasters).
        root_cause_groups: Dict[str, List[str]] = {}
        for r in results:
            rcid = r.get("root_cause_id")
            if rcid:
                root_cause_groups.setdefault(rcid, []).append(r["id"])

        truth_surface = canonical_truth_surface("occ_health_aggregator")
        canonical_owner_surface = canonical_truth_surface(
            truth_surface.get("canonical_owner_id")
        ) if truth_surface.get("canonical_owner_id") else None

        return {
            "generated_at": now_iso,
            "overall_status": overall,
            "overall_canonical": canonical_summary["highest"],
            "truth_surface": truth_surface,
            "truth_relationship": derived_truth_payload(
                "occ_health_aggregator",
                canonical_owner_route=(
                    (canonical_owner_surface or {}).get("owner_endpoint")
                    or truth_surface.get("owner_endpoint")
                ),
                derivation_explanation="OCC health is a derived aggregator over fresh child probes; upstream canonical owners remain authoritative for their own subjects.",
                canonical_status=canonical_summary["highest"],
                derived_status=overall,
                conflicts=[] if overall == canonical_overall else ["Aggregate status differs from canonical severity ordering because OCC prefers actionable verified child truth over standalone unknown cards."],
                evidence_age_source="generated_at",
                stale_evidence=False,
            )["relationship"],
            "runtime_identity": runtime_identity,
            "counts": counts,
            "canonical_counts": {
                "verified": canonical_summary["verified"],
                "degraded": canonical_summary["degraded"],
                "mismatch": canonical_summary["mismatch"],
                "unverifiable": canonical_summary["unverifiable"],
                "not_applicable": canonical_summary["not_applicable"],
                "total_applicable": canonical_summary["total_applicable"],
            },
            "root_cause_groups": root_cause_groups,
            "unique_critical_root_causes": len({
                r.get("root_cause_id") for r in results
                if r["status"] == "MISMATCH" and r.get("root_cause_id")
            }) + sum(1 for r in results
                     if r["status"] == "MISMATCH" and not r.get("root_cause_id")),
            "total_cards": len(results),
            "sections": sections,
        }

    return api_router


def _worst_status(cards: List[Dict[str, Any]]) -> Status:
    from lib.canonical_status import to_canonical

    order = {"MISMATCH": 4, "UNVERIFIABLE": 3, "DEGRADED": 2, "VERIFIED": 1, "NOT_APPLICABLE": 0}
    worst = "NOT_APPLICABLE"
    for c in cards:
        s = to_canonical(c.get("status", "NOT_APPLICABLE"))
        if order.get(s, 0) > order.get(worst, 0):
            worst = s
    return worst
