"""TRACK 25.01 · Deploy readiness + recovery playbook probes for the OCC.

Phase C of the Admin Operating System (AOS) consolidation: absorb the
scattered ``/admin/deploy-readiness`` and ``/admin/deploy-recovery``
pages into the Operations Control Center as first-class read-only
operations. Legacy pages continue to render (Phase B banner strategy)
but the canonical home for these checks is now OCC.

Both operations delegate to the same production code paths the legacy
pages call so the numbers stay identical.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── deploy.readiness_check ──────────────────────────────────────────

async def _deploy_readiness_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cheap read-only probe. Delegates to the same helpers used by
    ``/api/admin/deploy-readiness`` so the OCC card matches the legacy
    surface exactly. Falls back gracefully if the helpers are unavailable
    (e.g. in unit-test contexts where ``db`` is None).
    """
    db = payload.get("_db")
    if db is None:
        return {
            "status": "unavailable",
            "summary": "Deploy readiness requires an active database "
                       "session — probe not run in this context.",
            "generated_at": _now_iso(),
        }
    try:
        # Import lazily so the OCC registry loads without side effects.
        from routes import deploy_readiness as dr_module  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {
            "status": "unavailable",
            "summary": "Deploy readiness helpers not importable.",
            "error": str(e)[:200],
            "generated_at": _now_iso(),
        }

    # Rebuild a router just to reach the closure-bound checks. This is
    # the safest way to reuse the checks without duplicating logic: the
    # legacy endpoint composes them the same way. We use a stub
    # `require_admin` because the OCC layer already gated us.
    async def _stub_admin():  # pragma: no cover — never awaited
        return {"email": "occ", "role": "admin"}

    try:
        router = dr_module.build_deploy_readiness_router(db, _stub_admin)
    except Exception as e:  # noqa: BLE001
        return {
            "status": "unavailable",
            "summary": "Could not build deploy-readiness router.",
            "error": str(e)[:200],
            "generated_at": _now_iso(),
        }

    # Find the endpoint function and invoke it directly. FastAPI stores
    # the full path (with the router prefix) on each route.
    endpoint_fn = None
    for route in router.routes:
        path = getattr(route, "path", "")
        if path.endswith("/deploy-readiness"):
            endpoint_fn = route.endpoint
            break
    if not endpoint_fn:
        return {
            "status": "unavailable",
            "summary": "Deploy-readiness endpoint not found on router.",
            "generated_at": _now_iso(),
        }
    try:
        result = await endpoint_fn()
    except Exception as e:  # noqa: BLE001
        return {
            "status": "critical",
            "summary": f"Deploy-readiness check crashed: {str(e)[:160]}",
            "generated_at": _now_iso(),
        }

    overall = result.get("overall_status") or "unknown"
    status_map = {"ready": "healthy", "attention": "warning",
                  "blocked": "critical"}
    checks = result.get("checks") or []
    failed = [c for c in checks if not c.get("passed")]
    warnings: List[str] = [c.get("label", c.get("id", "")) for c in failed]
    return {
        "status": status_map.get(overall, "warning"),
        "summary": (
            f"{result.get('total_checks', 0)} pre-deploy checks · "
            f"{result.get('blocker_count', 0)} blockers · "
            f"{result.get('warn_count', 0)} warnings · overall {overall.upper()}"
        ),
        "overall_status": overall,
        "checks": checks,
        "blocker_count": result.get("blocker_count", 0),
        "warn_count": result.get("warn_count", 0),
        "total_checks": result.get("total_checks", 0),
        "warnings": warnings[:20],
        "canonical_source": "routes.deploy_readiness",
        "legacy_route": "/admin/deploy-readiness",
        "generated_at": _now_iso(),
    }


# ── deploy.recovery_playbook ────────────────────────────────────────

_RECOVERY_STEPS = [
    {
        "step": "1",
        "title": "Confirm the incident window",
        "detail": (
            "Run OCC → Health Overview to establish baseline. Note the "
            "affected time range, symptoms, and which portals reported "
            "issues. Freeze this in the audit log."
        ),
    },
    {
        "step": "2",
        "title": "Verify backup posture",
        "detail": (
            "OCC → Backup Health Check. Confirm the latest backup file "
            "and total size. If backups are stale, stop and escalate — "
            "recovery without a recent backup can lose data."
        ),
    },
    {
        "step": "3",
        "title": "Isolate the failing subsystem",
        "detail": (
            "Use OCC → System Health, R2 Health, AI Health, and Email "
            "Delivery Health to identify which component is degraded. "
            "Do NOT redeploy until root cause is confirmed."
        ),
    },
    {
        "step": "4",
        "title": "Choose the recovery path",
        "detail": (
            "Config drift → fix .env and restart. Data drift → restore "
            "the affected collection from backup. Provider outage → "
            "wait for the provider AND flip the app into safe mode "
            "(EMAIL_SAFETY_MODE=strict)."
        ),
    },
    {
        "step": "5",
        "title": "Restore then verify",
        "detail": (
            "After restore: run OCC → Deploy Readiness. Every blocker "
            "must be green before re-opening the portals. Failure to "
            "verify has caused every past re-incident."
        ),
    },
    {
        "step": "6",
        "title": "Post-mortem",
        "detail": (
            "Every recovery must record a `recovery_incident` audit row "
            "in `operations_audit` with root cause + prevention item. "
            "This locks the learning into the platform."
        ),
    },
]


async def _deploy_recovery_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only playbook + posture snapshot for platform recovery.

    We surface the canonical 6-step playbook the on-call operator
    should follow, plus a snapshot of the local backup posture so the
    playbook is not aspirational — step 2 (verify backups) can be
    performed in the same click.
    """
    backup_dir = Path(os.environ.get("BACKUP_DIR") or "/app/backend/backups")
    has_backups = backup_dir.exists() and any(backup_dir.rglob("*"))
    latest_iso = None
    if has_backups:
        latest = max(
            (p for p in backup_dir.rglob("*") if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            default=None,
        )
        if latest:
            latest_iso = datetime.fromtimestamp(
                latest.stat().st_mtime, tz=timezone.utc,
            ).isoformat()

    warnings: List[str] = []
    state = "healthy"
    if not has_backups:
        state = "warning"
        warnings.append(
            "No local backup files found. Recovery step 2 requires a "
            "recent backup — verify offsite backup posture before "
            "proceeding with any recovery playbook."
        )

    return {
        "status": state,
        "summary": (
            "Recovery playbook available · "
            + (f"latest local backup {latest_iso[:16]}"
               if latest_iso else "NO local backups found")
        ),
        "playbook": _RECOVERY_STEPS,
        "backup_dir": str(backup_dir),
        "latest_local_backup_at": latest_iso,
        "warnings": warnings,
        "legacy_route": "/admin/deploy-recovery",
        "canonical_source": "services.operations_control.deploy",
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="deploy.readiness_check",
            title="Deploy Readiness",
            description=(
                "Runs the full pre-deploy checklist: Mongo · critical "
                "indexes · R2 · Resend · integration probes · master "
                "coverage · default-admin rotation. Green means safe "
                "to deploy. Blocker means DO NOT deploy."
            ),
            category=OperationCategory.HEALTH,
            risk=RiskLevel.INFO,
            status_fn=_deploy_readiness_status,
            dry_run_fn=_deploy_readiness_status,
            reads=[
                "Mongo ping + collection reachability",
                "critical index presence on hot collections",
                "TTL indexes on telemetry collections",
                "R2 and Resend env posture",
                "live integration probes (Motive · MaintainX)",
                "master-binding coverage across employees + equipment",
                "default admin password-rotation timestamp",
            ],
            writes=[],
            never_touches=["provider keys", "user data", "audit rows"],
        ),
        Operation(
            id="deploy.recovery_playbook",
            title="Deploy Recovery Playbook",
            description=(
                "Canonical 6-step on-call playbook for platform "
                "recovery. Surfaces the latest local backup timestamp "
                "so step 2 (verify backups) can be executed in one "
                "click. Read-only reference — apply is per-step manual."
            ),
            category=OperationCategory.HEALTH,
            risk=RiskLevel.INFO,
            status_fn=_deploy_recovery_status,
            dry_run_fn=_deploy_recovery_status,
            reads=[
                "local backup directory (mtime of latest file)",
                "static recovery playbook",
            ],
            writes=[],
            never_touches=["backup files", "Mongo", "R2"],
        ),
    ]
