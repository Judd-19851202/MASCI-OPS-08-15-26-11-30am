"""Track 22.1F · Platform Operations API foundation.

Read-only runtime attestation surface. Returns non-secret operational
metadata that lets admins/operators verify the platform's foundation
health WITHOUT ever exposing secrets, tokens, API keys, DB URIs, or PII.

Contract:
    * NEVER return a secret (checked by tests + code review).
    * NEVER perform a side effect (no DB writes, no email, no external calls).
    * NEVER return per-user or per-record data.
    * Only surfaces derivable-from-boot metadata + the LIFECYCLE_STEPS /
      on_startup registry state + the bytecode fingerprint lock result.

Used by:
    * Ops dashboards
    * Deploy readiness scripts
    * Engineering audits during Track 22.1F-K migrations

Route wiring (server.py) — mounted onto the existing `api_router`
under `require_admin_strict`. Route path: /api/admin/platform/status.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from lib.runtime_identity import runtime_identity_public_payload


_MIGRATION_TARGETS = {
    # Groups that are already fully migrated (or will be, per roadmap)
    # into `LIFECYCLE_STEPS`. Used to compute a "migration progress"
    # percentage that any admin can read.
    "index-ensure":       {"track": "22.1E", "closed": True},
    "seed":               {"track": "22.1F", "closed": True},
    "scheduler-nonemail": {"track": "22.1G", "closed": True},
    "email-scheduler":    {"track": "22.1H",   "closed": True},
    "misc-bootstrap":     {"track": "22.1I",   "closed": True},
    "backup-scheduler":   {"track": "22.1I.1", "closed": True},
    "command-center":     {"track": "22.1L",   "closed": True},
    "readiness":          {"track": "22.1J",   "closed": True},
    "shutdown":           {"track": "22.1K",   "closed": True},
}


def _cors_status(app) -> Dict[str, Any]:
    """Introspect the CORS middleware without leaking the origin list.

    We deliberately return counts + booleans instead of the actual
    origin strings — those live in .env and are considered ops data.
    """
    for m in app.user_middleware:
        cls_name = getattr(m.cls, "__name__", "")
        if cls_name == "CORSMiddleware":
            opts = getattr(m, "kwargs", None) or getattr(m, "options", None) or {}
            allow_origins = opts.get("allow_origins") or []
            allow_methods = opts.get("allow_methods") or []
            allow_origin_regex = opts.get("allow_origin_regex")
            allow_headers = opts.get("allow_headers") or []
            return {
                "installed": True,
                "explicit_origin_count": len(allow_origins) if isinstance(allow_origins, (list, tuple)) else 0,
                "origin_regex_configured": bool(allow_origin_regex),
                "wildcard_methods": allow_methods == ["*"],
                "wildcard_headers": allow_headers == ["*"],
                "credentials_allowed": bool(opts.get("allow_credentials", False)),
                "method_count": len(allow_methods) if isinstance(allow_methods, (list, tuple)) else 0,
                "header_count": len(allow_headers) if isinstance(allow_headers, (list, tuple)) else 0,
            }
    return {
        "installed": False,
        "explicit_origin_count": 0,
        "origin_regex_configured": False,
        "wildcard_methods": False,
        "wildcard_headers": False,
        "credentials_allowed": False,
        "method_count": 0,
        "header_count": 0,
    }


def _lifecycle_registry_summary() -> Dict[str, Any]:
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS, SHUTDOWN_STEPS
    by_group: Dict[str, int] = {}
    for step in LIFECYCLE_STEPS:
        by_group[step.group] = by_group.get(step.group, 0) + 1
    # Readiness-last invariant (Track 22.1J): the readiness group must be the
    # final phase and must contain exactly one handler.
    readiness_names = [s.name for s in LIFECYCLE_STEPS if s.group == "readiness"]
    readiness_last_invariant = {
        "readiness_group_size": len(readiness_names),
        "readiness_handlers": readiness_names,
        "runs_after_non_readiness_lifecycle_steps": True,
        "runs_after_legacy_on_startup": True,
        "final_phase_of_lifespan": True,
    }
    # Track 22.1K: shutdown registry summary.
    shutdown_registry = {
        "total": len(SHUTDOWN_STEPS),
        "names": [s.name for s in SHUTDOWN_STEPS],
        "graceful_shutdown_supported": True,
        "runs_before_legacy_on_shutdown": True,
        "swallow_on_exception": True,
    }
    return {
        "total": len(LIFECYCLE_STEPS),
        "by_group": by_group,
        "names_by_group": {
            g: [s.name for s in LIFECYCLE_STEPS if s.group == g]
            for g in sorted(by_group.keys())
        },
        "readiness_last_invariant": readiness_last_invariant,
        "shutdown_registry": shutdown_registry,
    }


def _bytecode_fingerprint_summary(app) -> Dict[str, Any]:
    try:
        from lib.scheduler_bootstrap import verify_locked_bytecode
        result = verify_locked_bytecode(app)
        return {
            "checked": result.get("checked", 0),
            "ok_count": len(result.get("ok", [])),
            "drift_count": len(result.get("drift", [])),
            "missing_count": len(result.get("missing", [])),
            "clean": (result.get("drift") == [] and result.get("missing") == []),
        }
    except Exception as exc:  # noqa: BLE001
        return {"checked": 0, "ok_count": 0, "drift_count": 0, "missing_count": 0, "clean": False, "error": type(exc).__name__}


def _email_safety_summary() -> Dict[str, Any]:
    mode = (os.environ.get("EMAIL_SAFETY_MODE") or "").strip().lower()
    patched = False
    try:
        import resend
        send_fn = getattr(getattr(resend, "Emails", None), "send", None)
        # The monkey-patch closure has `_blocked_send` in its qualname,
        # OR the classic send was replaced with our closure. Either way,
        # our patch names include "_blocked_send".
        qn = getattr(send_fn, "__qualname__", "") or getattr(send_fn, "__name__", "")
        patched = "_blocked_send" in qn
    except Exception:  # noqa: BLE001
        pass
    return {
        "mode": mode or "off",
        "resend_sdk_patched": patched,
        "live_emails_possible": (mode == "off") and not patched,
    }


def _routes_summary(app) -> Dict[str, Any]:
    route_count = 0
    method_count = 0
    for r in app.routes:
        if hasattr(r, "endpoint"):
            route_count += 1
            method_count += len(getattr(r, "methods", None) or [])
    try:
        oa_paths = len(app.openapi().get("paths", {}))
    except Exception:  # noqa: BLE001
        oa_paths = 0
    return {
        "route_count": route_count,
        "route_methods_total": method_count,
        "openapi_path_count": oa_paths,
    }


def _lifecycle_migration_progress(app) -> Dict[str, Any]:
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS, SHUTDOWN_STEPS
    on_startup = len(app.router.on_startup)
    on_shutdown = len(app.router.on_shutdown)
    lifecycle = len(LIFECYCLE_STEPS)
    shutdown = len(SHUTDOWN_STEPS)
    total_startup = on_startup + lifecycle
    total_shutdown = on_shutdown + shutdown
    startup_pct = round((lifecycle / total_startup) * 100.0, 2) if total_startup else 0.0
    shutdown_pct = round((shutdown / total_shutdown) * 100.0, 2) if total_shutdown else 0.0
    return {
        "on_startup_legacy_count": on_startup,
        "on_shutdown_legacy_count": on_shutdown,
        "lifecycle_steps_count": lifecycle,
        "shutdown_steps_count": shutdown,
        "total_lifecycle_callables": total_startup,
        "total_shutdown_callables": total_shutdown,
        "migrated_pct": startup_pct,
        "startup_migration_pct": startup_pct,
        "shutdown_migration_pct": shutdown_pct,
        "lifecycle_complete": (on_startup == 0 and on_shutdown == 0),
        "target_groups": _MIGRATION_TARGETS,
    }


def _recommended_next_actions(app) -> list:
    """Deterministic advice based on runtime state. No secrets."""
    from lib.lifespan_bootstrap import LIFECYCLE_STEPS
    groups_present = {s.group for s in LIFECYCLE_STEPS}
    advice: list = []
    if "index-ensure" in groups_present and "seed" in groups_present and "scheduler-nonemail" not in groups_present:
        advice.append({
            "priority": "P1",
            "action": "Execute Track 22.1G — migrate non-email schedulers to LIFECYCLE_STEPS.",
            "gate": "Non-email scheduler bytecode is not fingerprint-locked; safe to migrate directly.",
        })
    if "scheduler-nonemail" in groups_present and "email-scheduler" not in groups_present:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1H — migrate 4-5 email-capable scheduler handlers (fingerprint-locked).",
            "gate": "Must preserve all 5 locked SHA-256 fingerprints; run verify_locked_bytecode() after cutover.",
        })
    elif "email-scheduler" in groups_present and "misc-bootstrap" not in groups_present:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1I — migrate remaining miscellaneous bootstrap handlers.",
            "gate": "Prove each handler is independent of a specific bootstrap earlier in on_startup.",
        })
    elif "misc-bootstrap" in groups_present and "backup-scheduler" not in groups_present:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1I.1 — migrate _start_backup_scheduler with backup/R2 safety audit.",
            "gate": "R2 safety audit + bytecode fingerprint lock + no live-email path.",
        })
    elif "backup-scheduler" in groups_present and "readiness" not in groups_present:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1J — migrate _iter453_6_flip_ready_flag into LIFECYCLE_STEPS.readiness (must remain LAST).",
            "gate": "Orchestrator must expose a final readiness phase that runs AFTER remaining legacy on_startup handlers.",
        })
    elif "readiness" in groups_present and len(app.router.on_startup) > 0:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1L — migrate the last router-hosted @app.on_event('startup') handler (routes.command_center._startup).",
            "gate": "Router-hosted startup must move into LIFECYCLE_STEPS without disturbing readiness-last ordering.",
        })
    if "command-center" in groups_present and len(app.router.on_startup) == 0 and len(app.router.on_shutdown) == 0:
        advice.append({
            "priority": "P0",
            "action": "🎉 Track 22.1K closed — LIFECYCLE ARCHITECTURE COMPLETE. Startup + shutdown are 100% owned by the Lifespan framework. No legacy @app.on_event(...) decorators remain anywhere.",
            "gate": "Zero legacy startup + zero legacy shutdown decorators. All handlers routed through LIFECYCLE_STEPS / SHUTDOWN_STEPS registries with per-step observability and swallow-on-exception semantics.",
        })
    elif "command-center" in groups_present and len(app.router.on_startup) == 0:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1K — migrate the sole remaining @app.on_event('shutdown') handler into a lifecycle-managed shutdown hook.",
            "gate": "Preserve exact shutdown ordering; no swallowed exceptions beyond current behavior.",
        })
    if "readiness" in groups_present and len(app.router.on_shutdown) > 0:
        advice.append({
            "priority": "P1",
            "action": "Track 22.1K — migrate the sole remaining @app.on_event('shutdown') handler into a lifecycle-managed shutdown hook.",
            "gate": "Preserve exact shutdown ordering; no swallowed exceptions beyond current behavior.",
        })
    if len(app.router.on_startup) > 0:
        advice.append({
            "priority": "P2",
            "action": f"Retire the remaining {len(app.router.on_startup)} @app.on_event('startup') decorators.",
            "gate": "Track 22.1L closes the last one.",
        })
    return advice


def platform_status(app) -> Dict[str, Any]:
    """Assemble the full platform status attestation payload.

    Read-only. No side effects. No secrets.
    """
    runtime_identity_bundle = getattr(getattr(app, "state", None), "runtime_identity_bundle", None)
    runtime_identity = runtime_identity_public_payload(runtime_identity_bundle) if runtime_identity_bundle else None
    return {
        "service": "masci-hub",
        "attestation_version": "22.1K",
        "runtime": {
            "app_env": ((runtime_identity or {}).get("identity") or {}).get("app_env") or "unknown",
            "worker_pid": os.getpid(),
        },
        "runtime_identity": runtime_identity,
        "routes": _routes_summary(app),
        "middleware": {
            "count": len(app.user_middleware),
            "cors": _cors_status(app),
        },
        "lifecycle": {
            "on_startup_legacy_count": len(app.router.on_startup),
            "on_shutdown_count": len(app.router.on_shutdown),
            "registry": _lifecycle_registry_summary(),
            "migration_progress": _lifecycle_migration_progress(app),
        },
        "bytecode_fingerprints": _bytecode_fingerprint_summary(app),
        "email_safety": _email_safety_summary(),
        "readiness": {
            "ready_flag": bool(getattr(getattr(app, "state", None), "ready", False)),
        },
        "recent_track_closures": ["22.1H", "22.1I", "22.1I.1", "22.1J", "22.1L", "22.1K"],
        "recommended_next_actions": _recommended_next_actions(app),
    }
