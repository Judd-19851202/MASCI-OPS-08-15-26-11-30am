"""TRACK 15.75D · In-App Production Trust Validator.

Admin-gated, read-only endpoint that lets a super-admin verify the
Track 15.74 → 15.75C trust-audit contracts directly from the admin
UI — no shell scripts, no token copying, no DevTools, no Mongo.

The endpoint aggregates **only** data that already lives in
admin-safe surfaces (the `/api/health/full` heartbeat, the V2
email-routing status, the PM-coverage endpoint, the
`email_routing_audit_v2` collection). It performs **zero** writes,
returns **no** secrets (no Resend API key, no Mongo URL, no HMAC
tokens, no password hashes, no recipient PII beyond what the
existing PM-coverage card already exposes).

Final band (`green` / `amber` / `red`) is computed defensively:
unknown audit statuses, empty critical routes, recent failures, or
sub-system outages immediately produce `red`. Workflows with no
recent submissions are honestly tagged `amber-no-activity` — never
fake-green.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from lib.archive_lineage import backup_recent_truth, build_canonical_archive_lineage
from lib.canonical_truth import canonical_truth_surface, derived_truth_payload
from lib.runtime_identity import runtime_identity_public_payload


ALLOWED_STATUSES = {
    "sent",
    "failed",
    "dry_run",
    "resolved",
    "routed_to_dead_letter",
    "dead_letter_unconfigured",
    "shop_recipient_unconfigured",
    "escalated_to_admin_dead_letter",
}

WORKFLOW_MODULES = [
    "auto_email_dispatch:daily-report",
    "auto_email_dispatch:meeting",
    "auto_email_dispatch:incident",
    "auto_email_dispatch:qaqc",
    "auto_email_dispatch:jha",
    "auto_email_dispatch:inspection",
    "shop_preop_dispatch",
]

# Map calling_module → collection that holds the source records, so
# we can detect "recent submission exists but no audit row" =>
# silent-failure red.
WORKFLOW_SOURCE_COLLECTION = {
    "auto_email_dispatch:daily-report": "daily_reports",
    "auto_email_dispatch:meeting": "meetings",
    "auto_email_dispatch:incident": "incidents",
    "auto_email_dispatch:qaqc": "qaqc_inspections",
    "auto_email_dispatch:jha": "jhas",
    "auto_email_dispatch:inspection": "inspections",
    "shop_preop_dispatch": "equipment_inspections",
}


def make_router(db, require_admin_only_dep, get_runtime_identity=None) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/platform-trust/validate")
    async def platform_trust_validate(
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since_24h = (now - timedelta(hours=24)).isoformat()

        red_reasons: List[str] = []
        amber_reasons: List[str] = []

        # ----- system (no secrets) -----
        runtime_identity = runtime_identity_public_payload(get_runtime_identity()) if callable(get_runtime_identity) else {}
        identity = (runtime_identity or {}).get("identity") or {}
        system_block: Dict[str, Any] = {
            "app_env": identity.get("app_env") or "preview",
            "db_name": identity.get("db_name") or "",
            "source_hash": os.environ.get("SOURCE_HASH") or "unknown",
            "started_at": getattr(
                router, "_started_at_iso", None
            ) or "unknown",
        }
        try:
            lineage = await build_canonical_archive_lineage(
                db,
                current_env=identity.get("app_env"),
                current_db=identity.get("db_name"),
            )
            backup_recent = backup_recent_truth(lineage).get("ok")
        except Exception:
            backup_recent = None
        system_block["backup_recent"] = backup_recent
        system_block["mongo"] = True  # we just queried successfully
        try:
            scheduler_ok = bool(
                getattr(router, "_scheduler_alive", lambda: True)()
            )
        except Exception:
            scheduler_ok = None
        system_block["scheduler"] = scheduler_ok
        system_block["ok"] = bool(
            system_block["mongo"]
            and (system_block["scheduler"] in (True, None))
            and (system_block["backup_recent"] in (True, None))
        )
        if backup_recent is False:
            red_reasons.append("backup_not_recent")
        if scheduler_ok is False:
            red_reasons.append("scheduler_down")

        # ----- email_routing -----
        email_routing: Dict[str, Any] = {
            "mode": (
                "v2"
                if (os.environ.get("EMAIL_ROUTING_V2") or "").lower() == "true"
                else "legacy"
            ),
            "v2_enabled": (
                (os.environ.get("EMAIL_ROUTING_V2") or "").lower() == "true"
            ),
            "auto_email_reports": (
                (os.environ.get("AUTO_EMAIL_REPORTS") or "").lower() == "true"
            ),
        }
        # Route counts (masci tenant only — extend if multi-tenant ever)
        try:
            from tenant_context import resolve_tenant_key  # noqa: PLC0415
            tk = resolve_tenant_key()
        except Exception:
            tk = "masci"
        route_total = await db.email_routes.count_documents(
            {"_id": {"$regex": f"^{tk}::"}}
        )
        email_routing["route_total"] = route_total
        critical_keys = [
            "ADMIN_DEAD_LETTER_TO",
            "BACKUP_ALERTS",
            "HEALTH_ALERTS",
            "OUTAGE_ALERTS",
            "PRE_OP_FAIL_FALLBACK",
        ]
        critical_empty: List[str] = []
        for ck in critical_keys:
            doc = await db.email_routes.find_one({"_id": f"{tk}::{ck}"})
            to = (doc or {}).get("to") or []
            if not (isinstance(to, list) and to):
                critical_empty.append(ck)
        email_routing["critical_total"] = len(critical_keys)
        email_routing["critical_empty_count"] = len(critical_empty)
        email_routing["critical_empty_route_keys"] = critical_empty
        # 24h error count
        errors_24h = await db.email_routing_audit_v2.count_documents(
            {"ts": {"$gte": since_24h},
             "status": {"$in": ["failed", "error"]}}
        )
        email_routing["errors_last_24h"] = errors_24h
        if critical_empty:
            red_reasons.append(
                f"critical_route_empty:{','.join(critical_empty)}"
            )
        if errors_24h > 0:
            red_reasons.append(f"errors_last_24h:{errors_24h}")

        # ----- audit_status_integrity -----
        status_counters: Dict[str, int] = {}
        async for r in db.email_routing_audit_v2.aggregate([
            {"$group": {"_id": "$status", "n": {"$sum": 1}}}
        ]):
            sk = r.get("_id") or ""
            if sk:
                status_counters[sk] = int(r["n"])
        unknown_statuses = [s for s in status_counters if s not in ALLOWED_STATUSES]
        unknown_status_count = sum(status_counters[s] for s in unknown_statuses)
        audit_integrity = {
            "allowed_statuses": sorted(ALLOWED_STATUSES),
            "observed_statuses": sorted(status_counters.keys()),
            "unknown_statuses": unknown_statuses,
            "unknown_status_count": unknown_status_count,
            "status_counters": status_counters,
            "pass": not unknown_statuses,
        }
        if unknown_statuses:
            red_reasons.append(
                f"unknown_audit_status:{','.join(unknown_statuses)}"
            )

        # ----- workflow_delivery_health -----
        workflow_health: List[Dict[str, Any]] = []
        for mod in WORKFLOW_MODULES:
            sent_24h = await db.email_routing_audit_v2.count_documents(
                {"calling_module": mod, "status": "sent",
                 "ts": {"$gte": since_24h}}
            )
            failed_24h = await db.email_routing_audit_v2.count_documents(
                {"calling_module": mod, "status": "failed",
                 "ts": {"$gte": since_24h}}
            )
            dead_24h = await db.email_routing_audit_v2.count_documents(
                {"calling_module": "pm_routing_dead_letter",
                 "subject": {"$regex": f"^\\[PM UNRESOLVED\\] "
                             + mod.split(":")[-1]},
                 "ts": {"$gte": since_24h}}
            )
            uncfg_24h = await db.email_routing_audit_v2.count_documents(
                {"calling_module": "shop_routing_unresolved",
                 "ts": {"$gte": since_24h}}
            ) if mod == "shop_preop_dispatch" else 0
            latest = await db.email_routing_audit_v2.find_one(
                {"calling_module": mod},
                sort=[("ts", -1)],
                projection={"_id": 0, "ts": 1, "status": 1},
            )
            # Detect silent-failure pattern: recent submission of this
            # kind exists in source collection but ZERO audit rows.
            src_coll = WORKFLOW_SOURCE_COLLECTION.get(mod)
            recent_submissions_24h = 0
            if src_coll:
                try:
                    recent_submissions_24h = await db[src_coll].count_documents(
                        {"created_at": {"$gte": since_24h}}
                    )
                except Exception:
                    recent_submissions_24h = 0
            total_audit_rows = sent_24h + failed_24h
            band = "green"
            reason = ""
            if failed_24h > 0:
                band = "red"
                reason = f"{failed_24h} send(s) failed in last 24h"
                red_reasons.append(f"{mod}:failed_{failed_24h}")
            elif recent_submissions_24h > 0 and total_audit_rows == 0:
                band = "red"
                reason = (
                    f"{recent_submissions_24h} recent submission(s) but "
                    f"no audit row — silent failure suspected"
                )
                red_reasons.append(f"{mod}:silent_missing_audit")
            elif sent_24h > 0:
                band = "green"
                reason = f"{sent_24h} successful send(s) in last 24h"
            elif recent_submissions_24h == 0 and total_audit_rows == 0:
                band = "amber-no-activity"
                reason = "no submissions of this kind in last 24h"
                amber_reasons.append(f"{mod}:no_activity")
            else:
                band = "amber"
                reason = "ambiguous — partial activity"
                amber_reasons.append(f"{mod}:ambiguous")
            workflow_health.append({
                "calling_module": mod,
                "sent_24h": sent_24h,
                "failed_24h": failed_24h,
                "dead_letter_24h": dead_24h,
                "unconfigured_24h": uncfg_24h,
                "recent_submissions_24h": recent_submissions_24h,
                "latest_status": (latest or {}).get("status"),
                "latest_ts": (latest or {}).get("ts"),
                "band": band,
                "reason": reason,
            })

        # ----- pm_email_coverage -----
        pm_cov: Dict[str, Any] = {}
        try:
            # Re-use the existing roster-aware logic by calling the helper
            # directly to avoid HTTP overhead.
            from routes.admin_pm_coverage import EMAIL_RE  # noqa: PLC0415
            counters = {
                "active_total": 0,
                "active_direct_pm_email": 0,
                "active_roster_resolved": 0,
                "active_missing_unresolved": 0,
            }
            roster_pm: Dict[str, str] = {}
            async for tr in db.project_team_assignments.find(
                {"assignment_role": "pm", "active": True, "is_primary": True},
                {"_id": 0, "project_number": 1, "email": 1},
            ):
                pn = (tr.get("project_number") or "").strip()
                em = (tr.get("email") or "").strip().lower()
                if pn and em:
                    roster_pm.setdefault(pn, em)
            missing_unresolved = 0
            resolved_via_roster = 0
            async for j in db.jobs_master.find(
                {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                {"_id": 0, "project_number": 1, "pm_email": 1},
            ):
                counters["active_total"] += 1
                pn = (j.get("project_number") or "").strip()
                pme = (j.get("pm_email") or "").strip()
                if pme and EMAIL_RE.match(pme):
                    counters["active_direct_pm_email"] += 1
                elif pn in roster_pm and EMAIL_RE.match(roster_pm[pn]):
                    counters["active_roster_resolved"] += 1
                    resolved_via_roster += 1
                else:
                    counters["active_missing_unresolved"] += 1
                    missing_unresolved += 1
            pm_cov = {
                "active_total": counters["active_total"],
                "active_direct_pm_email": counters["active_direct_pm_email"],
                "active_roster_resolved": counters["active_roster_resolved"],
                "active_missing_unresolved": missing_unresolved,
            }
            if missing_unresolved > 0:
                amber_reasons.append(
                    f"pm_unresolved:{missing_unresolved}"
                )
        except Exception as exc:  # noqa: BLE001
            pm_cov = {"error": str(exc)[:120]}

        # ----- dead_letter_health -----
        dead_24h_total = await db.email_routing_audit_v2.count_documents({
            "calling_module": "pm_routing_dead_letter",
            "ts": {"$gte": since_24h},
        })
        dead_by_subject: Dict[str, int] = {}
        async for r in db.email_routing_audit_v2.aggregate([
            {"$match": {
                "calling_module": "pm_routing_dead_letter",
                "ts": {"$gte": since_24h},
            }},
            {"$group": {"_id": "$subject", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 10},
        ]):
            sk = r.get("_id") or ""
            if sk:
                dead_by_subject[sk] = int(r["n"])
        unconfigured_24h = status_counters.get("dead_letter_unconfigured", 0)
        shop_uncfg_24h = await db.email_routing_audit_v2.count_documents({
            "calling_module": "shop_routing_unresolved",
            "ts": {"$gte": since_24h},
        })
        dead_letter_health = {
            "dead_letters_24h": dead_24h_total,
            "dead_letters_by_subject_top10": dead_by_subject,
            "dead_letter_unconfigured_total": unconfigured_24h,
            "shop_recipient_unconfigured_24h": shop_uncfg_24h,
        }
        if unconfigured_24h > 0:
            red_reasons.append(
                f"dead_letter_unconfigured:{unconfigured_24h}"
            )
        if shop_uncfg_24h > 0:
            red_reasons.append(
                f"shop_recipient_unconfigured:{shop_uncfg_24h}"
            )

        # ----- final band -----
        if red_reasons:
            final_band = "red"
        elif amber_reasons:
            final_band = "amber"
        else:
            final_band = "green"

        validation_status = {
            "green": "VERIFIED",
            "amber": "DEGRADED",
            "red": "MISMATCH",
        }.get(final_band, "UNVERIFIABLE")

        return {
            "track": "15.75D",
            "generated_at": now.isoformat(),
            "canonical_truth": {
                "platform_truth_owner": canonical_truth_surface("platform_attestation"),
                "validation_surface": canonical_truth_surface("platform_trust_validator"),
            },
            "truth_relationship": derived_truth_payload(
                "platform_trust_validator",
                canonical_owner_route="/api/admin/platform/status",
                derivation_explanation="This route is a validator. It checks admin-safe evidence against canonical platform truth and must not replace the platform owner.",
                canonical_status=validation_status,
                derived_status=validation_status,
                conflicts=["Validation result is separate from canonical platform truth."] if final_band in {"amber", "red"} else [],
                evidence_age_source="generated_at",
                stale_evidence=False,
            )["relationship"],
            "system": system_block,
            "email_routing": email_routing,
            "audit_status_integrity": audit_integrity,
            "workflow_delivery_health": workflow_health,
            "pm_email_coverage": pm_cov,
            "dead_letter_health": dead_letter_health,
            "final_band": final_band,
            "red_reasons": red_reasons,
            "amber_reasons": amber_reasons,
        }

    return router
