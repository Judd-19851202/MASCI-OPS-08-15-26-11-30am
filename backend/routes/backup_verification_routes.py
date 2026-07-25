"""
backup_verification_routes.py — admin endpoints for the weekly verification cron.

Exposes three admin-strict endpoints:
  GET  /api/admin/backup-verification/preview   — build report without emailing
  POST /api/admin/backup-verification/run-now   — build + email immediately
  GET  /api/admin/backup-verification/state     — last-run + next-fire metadata
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from backup_verification import (
    _env_int,
    _enabled,
    _verification_recipients,
    _next_scheduled_dt,
    build_verification_report,
    send_verification_email,
    DEFAULT_DAY_OF_WEEK,
    DEFAULT_HOUR_UTC,
)
from lib.ots_truth import OBSERVED, canonical_truth_card, compatibility_projection, projected_truth_relationship, public_ots_projection


def build_backup_verification_router(db, require_admin_strict_dep: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/admin/backup-verification", tags=["backup-verification"])

    @router.get("/preview", dependencies=[Depends(require_admin_strict_dep)])
    async def preview_report() -> Dict[str, Any]:
        """Build the verification report WITHOUT emailing. Useful for the
        admin panel preview button."""
        report = await build_verification_report(db)
        return {"ok": True, "report": report}

    @router.post("/run-now", dependencies=[Depends(require_admin_strict_dep)])
    async def run_now(body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
        """Build the report and email it to the configured recipients
        immediately. Body can override `{recipients: ["a@b.com", ...]}`
        for one-off sends."""
        force_recipients: Optional[List[str]] = None
        raw = body.get("recipients") if isinstance(body, dict) else None
        if isinstance(raw, list) and raw:
            force_recipients = [str(r).strip() for r in raw if str(r).strip()]
        result = await send_verification_email(db, force_recipients=force_recipients, manual=True)
        # Stamp the manual-run marker as well so the weekly cron doesn't
        # double-send right after a manual one.
        try:
            await db.backup_health.update_one(
                {"id": "_verification_last_run"},
                {"$set": {"id": "_verification_last_run", "ts": datetime.now(timezone.utc).isoformat(),
                          "manual": True}},
                upsert=True,
            )
        except Exception:
            pass
        if not result.get("sent") and result.get("error"):
            # Surface config errors to the admin panel with a 4xx so the
            # UI shows the reason inline rather than a generic 500.
            err = result.get("error") or ""
            if "RESEND_API_KEY" in err or "recipient" in err.lower():
                raise HTTPException(status_code=400, detail=err)
        return {"ok": bool(result.get("sent") or result.get("report")), **result}

    @router.get("/state", dependencies=[Depends(require_admin_strict_dep)])
    async def cron_state() -> Dict[str, Any]:
        """Read-only snapshot of the cron's configuration and last/next run."""
        day = _env_int("BACKUP_VERIFICATION_DAY", DEFAULT_DAY_OF_WEEK) % 7
        hour = _env_int("BACKUP_VERIFICATION_HOUR_UTC", DEFAULT_HOUR_UTC) % 24
        now = datetime.now(timezone.utc)
        next_fire = _next_scheduled_dt(now, day, hour)

        marker = await db.backup_health.find_one(
            {"id": "_verification_last_run"}, {"_id": 0}
        )
        last_run_iso = (marker or {}).get("ts")
        last_was_manual = bool((marker or {}).get("manual"))

        truth_card = canonical_truth_card(
            truth_subject="bcss_backup_archive_lineage",
            canonical_owner="bcss_backup_archive_lineage",
            truth_surface_id="bcss_backup_archive_lineage",
            evidence_state="historical" if marker and marker.get("ts") else "declared",
            evidence_quality="HISTORICAL" if marker and marker.get("ts") else "DECLARED",
            evidence_confidence="MEDIUM" if marker and marker.get("ts") else "LOW",
            truth_evaluation="UNVERIFIABLE",
            permitted_claim=OBSERVED,
            claim_ceiling=OBSERVED,
            claim_basis=["verification scheduler config", "backup_health marker", "recipient configuration"],
            prohibited_claims=["CORRELATED", "VERIFIED", "VALIDATED", "CERTIFIED"],
            degradation_reasons=[],
            unknowns=[] if _enabled() else ["Verification schedule is disabled or absent."],
            contradictory_evidence=[],
            evidence_timestamp=last_run_iso or next_fire.isoformat(),
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
            audit_reference="OTS-C5-BACKUP-VERIFICATION-STATE",
            evidence_required_to_raise_claim=["executed preview/report validation evidence"],
            notes=["State route exposes scheduler/config state only."],
        )
        compatibility = compatibility_projection(
            preserved_fields=8,
            deprecated_fields=0,
            new_fields=3,
            alias_fields=[],
            breaking_changes=0,
        )
        return {
            "ok": True,
            "enabled": _enabled(),
            "schedule": {
                "day_of_week": day,
                "day_label": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day],
                "hour_utc": hour,
            },
            "next_fire_iso": next_fire.isoformat(),
            "last_run_iso": last_run_iso,
            "last_was_manual": last_was_manual,
            "recipients": _verification_recipients(),
            "max_age_threshold_hrs": _env_int("BACKUP_VERIFICATION_MAX_AGE_HOURS", 36),
            "ots_truth": public_ots_projection(truth_card),
            "truth_relationship": projected_truth_relationship(
                surface_id="bcss_backup_archive_lineage",
                card=truth_card,
                canonical_owner_route="/api/admin/backup-verification/state",
                derivation_explanation="Backup Verification state is a scheduler/config projection only. It is not the validation report truth itself.",
                derived_status="UNVERIFIABLE",
            ),
            "compatibility": compatibility,
        }

    return router
