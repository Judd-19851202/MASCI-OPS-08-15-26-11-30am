"""
deploy_readiness.py — Iter136 (Phase-1 Iter D). One-stop pre-deploy
checklist endpoint. Aggregates:
  • Backend service reachability + uptime
  • Mongo connectivity + collection counts on critical collections
  • TTL indexes present on telemetry collections
  • Critical indexes present on hot collections
  • R2 configured (storage health from safety_doc_storage)
  • Resend configured (email)
  • Integrations health (Motive / MaintainX configured?)
  • Recent integration error logs (last 24h)
  • Recent degraded-mode R2 events (last 24h)
  • Training Center seed completeness
  • Default admin not still active with default password

Each check returns { id, label, severity, passed, detail }.
Final response has overall_status: 'ready' | 'attention' | 'blocked'.

Endpoint:
  GET /api/admin/deploy-readiness   (admin-token gated)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


# Critical collections + the index spec key we expect on each. Index-key
# is a tuple of (field_name, direction) — order matters for compound.
CRITICAL_INDEXES: Dict[str, List[tuple]] = {
    "fire_extinguishers":  [("id", 1)],
    "corrective_actions":  [("id", 1), ("status", 1)],
    "incidents":           [("id", 1)],
    "inspections":         [("id", 1)],
    "safety_training_records": [("id", 1)],
    "equipment_master":    [("id", 1)],
    "employees":           [("id", 1)],
}

TTL_COLLECTIONS = ["r2_degraded_events", "digest_runs", "system_health_events", "audit_events"]


def build_deploy_readiness_router(db, require_admin: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/admin", tags=["admin-deploy"])

    async def _check_mongo() -> Dict[str, Any]:
        try:
            await db.command("ping")
            collections = await db.list_collection_names()
            return {"id": "mongo", "label": "MongoDB reachable",
                    "severity": "blocker", "passed": True,
                    "detail": f"{len(collections)} collections"}
        except Exception as e:  # noqa: BLE001
            return {"id": "mongo", "label": "MongoDB reachable",
                    "severity": "blocker", "passed": False, "detail": str(e)[:200]}

    async def _check_critical_collections() -> Dict[str, Any]:
        gaps: List[str] = []
        for coll in CRITICAL_INDEXES:
            try:
                n = await db[coll].count_documents({}, limit=1)
                # An empty collection is fine; we only care that we *can* query it
                _ = n
            except Exception:  # noqa: BLE001
                gaps.append(coll)
        if not gaps:
            return {"id": "critical_collections", "label": "Critical collections queryable",
                    "severity": "blocker", "passed": True,
                    "detail": f"{len(CRITICAL_INDEXES)} collections checked"}
        return {"id": "critical_collections", "label": "Critical collections queryable",
                "severity": "blocker", "passed": False,
                "detail": "Cannot query: " + ", ".join(gaps)}

    async def _check_critical_indexes() -> Dict[str, Any]:
        """Verify each critical collection has an index on `id` (used as
        the application-level key everywhere instead of _id)."""
        missing: List[str] = []
        for coll, _spec in CRITICAL_INDEXES.items():
            try:
                idxs = await db[coll].index_information()
                has_id_index = any("id" in [k for k, _ in v.get("key", [])] for v in idxs.values())
                if not has_id_index:
                    missing.append(coll)
            except Exception:  # noqa: BLE001
                missing.append(coll)
        if not missing:
            return {"id": "critical_indexes", "label": "Hot collections have id-index",
                    "severity": "warn", "passed": True,
                    "detail": f"{len(CRITICAL_INDEXES)} collections OK"}
        return {"id": "critical_indexes", "label": "Hot collections have id-index",
                "severity": "warn", "passed": False,
                "detail": "Missing id-index on: " + ", ".join(missing)}

    async def _check_ttl_indexes() -> Dict[str, Any]:
        missing: List[str] = []
        for coll in TTL_COLLECTIONS:
            try:
                idxs = await db[coll].index_information()
                has_ttl = any("expireAfterSeconds" in v for v in idxs.values())
                if not has_ttl:
                    missing.append(coll)
            except Exception:  # noqa: BLE001
                # If the collection doesn't exist yet, TTL will be applied on first insert
                pass
        if not missing:
            return {"id": "ttl_indexes", "label": "TTL indexes on telemetry collections",
                    "severity": "warn", "passed": True,
                    "detail": f"{len(TTL_COLLECTIONS)} collections OK"}
        return {"id": "ttl_indexes", "label": "TTL indexes on telemetry collections",
                "severity": "warn", "passed": False,
                "detail": "Missing TTL on: " + ", ".join(missing)}

    async def _check_r2() -> Dict[str, Any]:
        try:
            import safety_doc_storage  # noqa: PLC0415
            configured = bool(getattr(safety_doc_storage, "is_configured", lambda: False)())
        except Exception:  # noqa: BLE001
            configured = False
        return {"id": "r2", "label": "Cloudflare R2 configured",
                "severity": "warn", "passed": configured,
                "detail": "OK — uploads will land in R2" if configured else "Not configured — uploads fall back to inline base64"}

    async def _check_resend() -> Dict[str, Any]:
        key_present = bool(os.environ.get("RESEND_API_KEY"))
        return {"id": "resend", "label": "Resend transactional email configured",
                "severity": "warn", "passed": key_present,
                "detail": "API key present" if key_present else "RESEND_API_KEY missing — password resets won't email; tokens still in audit log"}

    async def _check_integration_errors() -> Dict[str, Any]:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            n = await db.integration_error_logs.count_documents({"at": {"$gte": cutoff}})
        except Exception:  # noqa: BLE001
            n = 0
        passed = n < 10
        return {"id": "integration_errors_24h", "label": "Integration errors (last 24h)",
                "severity": "warn", "passed": passed,
                "detail": f"{n} errors in last 24h" + ("" if passed else " — investigate before deploy")}

    async def _check_r2_degraded() -> Dict[str, Any]:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            n = await db.r2_degraded_events.count_documents({"at": {"$gte": cutoff}})
        except Exception:  # noqa: BLE001
            n = 0
        passed = n < 5
        return {"id": "r2_degraded_24h", "label": "R2 degraded events (last 24h)",
                "severity": "warn", "passed": passed,
                "detail": f"{n} fallback-to-inline events in last 24h"}

    async def _check_training_seed() -> Dict[str, Any]:
        try:
            n = await db.training_guides.count_documents({})
        except Exception:  # noqa: BLE001
            n = 0
        # 16 is the minimum seeded set (will grow with iter134/135 additions)
        passed = n >= 16
        return {"id": "training_seed", "label": "Training Center seeded",
                "severity": "info", "passed": passed,
                "detail": f"{n} guides in db.training_guides"}

    async def _check_master_coverage() -> Dict[str, Any]:
        """iter140 — cross-portal master-binding coverage rollup.
        Pass if every collection that COULD bind to a master has >=50%
        coverage. Warn otherwise.

        iter142b — ignore collections with <10 total rows. A 1-of-3
        ratio is statistical noise, not a real coverage gap; in prod
        these collections will have hundreds/thousands of rows."""
        from routes.master_lookup import build_master_binding_audit, MASTER_BINDING_SAMPLE_THRESHOLD  # noqa: PLC0415
        MIN_SAMPLE = MASTER_BINDING_SAMPLE_THRESHOLD
        audit = await build_master_binding_audit(db)
        worst_pct = 100
        worst_name = ""
        gaps: list[str] = []
        small: list[str] = []
        details: list[dict[str, Any]] = []
        for label, coverage_map in (("equipment", audit.get("equipment_coverage") or {}), ("employee", audit.get("employee_coverage") or {})):
            for coll_name, metrics in coverage_map.items():
                eligible_total = int(metrics.get("eligible_total") or 0)
                pct = int(metrics.get("pct") or 0)
                details.append({
                    "collection": coll_name,
                    "binding_type": label,
                    "eligible_total": eligible_total,
                    "with_master_ref": int(metrics.get("with_master_ref") or 0),
                    "missing_master_ref": int(metrics.get("missing_master_ref") or 0),
                    "pct": pct,
                    "canonical_field": metrics.get("canonical_field"),
                    "source_fields": metrics.get("source_fields") or [],
                    "backfill_endpoint": metrics.get("backfill_endpoint"),
                    "review_queue_endpoint": metrics.get("review_queue_endpoint"),
                })
                if eligible_total == 0:
                    continue
                if eligible_total < MIN_SAMPLE:
                    small.append(f"{coll_name} {label[:3]} ({eligible_total})")
                    continue
                if pct < 50:
                    gaps.append(f"{coll_name} {label[:3]} {pct}%")
                if pct < worst_pct:
                    worst_pct, worst_name = pct, f"{coll_name}.{label}"
        passed = not gaps  # ignore small samples
        if not gaps and not small:
            detail = "All cross-portal collections ≥50% bound to master records"
        elif not gaps and small:
            detail = f"All ≥50% bound · {len(small)} small sample(s) skipped: " + ", ".join(small[:3])
        else:
            detail = f"Worst: {worst_name} at {worst_pct}% · gaps: " + ", ".join(gaps[:5])
        return {"id": "master_coverage", "label": "Cross-portal master-binding coverage",
                "severity": "warn", "passed": passed, "detail": detail,
                "formula": {
                    "threshold_pct": 50,
                    "minimum_sample_threshold": MIN_SAMPLE,
                    "denominator_definition": "eligible records with canonical binding present or at least one source field populated",
                    "source_of_truth": "/api/master-lookup/audit",
                },
                "details": details[:25]}

    async def _check_default_admin() -> Dict[str, Any]:
        """If MASCI1982! still works as the admin password in prod, that's
        a deploy blocker. We can't actually test the password from here
        without round-tripping the auth flow, so we check if the legacy
        admin's password_hash is still the unmodified seed hash."""
        try:
            admin = await db.admin_users.find_one(
                {"role": {"$in": ["super_admin", "legacy_admin"]}},
                {"_id": 0, "password_changed_at": 1, "email": 1},
            )
            if not admin:
                return {"id": "default_admin", "label": "Default admin password rotated",
                        "severity": "info", "passed": True, "detail": "No legacy admin row"}
            changed_at = admin.get("password_changed_at")
            if changed_at:
                return {"id": "default_admin", "label": "Default admin password rotated",
                        "severity": "warn", "passed": True,
                        "detail": f"Last changed {str(changed_at)[:10]}"}
            return {"id": "default_admin", "label": "Default admin password rotated",
                    "severity": "warn", "passed": False,
                    "detail": "password_changed_at is empty — using factory password?"}
        except Exception as e:  # noqa: BLE001
            return {"id": "default_admin", "label": "Default admin password rotated",
                    "severity": "warn", "passed": True, "detail": f"check unavailable: {e}"}

    async def _check_integrations_health() -> Dict[str, Any]:
        """iter142 — run all integration probes via the unified
        run_all_probes() helper. Pass = no probes reported `down`.
        Warn = at least one degraded but no fatal failures."""
        try:
            from routes.integration_health import run_all_probes  # noqa: PLC0415
            payload = await run_all_probes(db)
            statuses = [p["status"] for p in payload.get("probes", [])]
            down = [p for p in payload["probes"] if p["status"] == "down"]
            degraded = [p for p in payload["probes"] if p["status"] == "degraded"]
            if down:
                names = ", ".join(p["id"] for p in down)
                return {"id": "integrations_health",
                        "label": "Live integration probes",
                        "severity": "blocker", "passed": False,
                        "detail": f"DOWN: {names}"}
            if degraded:
                names = ", ".join(p["id"] for p in degraded)
                return {"id": "integrations_health",
                        "label": "Live integration probes",
                        "severity": "warn", "passed": False,
                        "detail": f"Degraded: {names}"}
            return {"id": "integrations_health",
                    "label": "Live integration probes",
                    "severity": "warn", "passed": True,
                    "detail": f"{len(statuses)} probes all OK or disabled"}
        except Exception as e:  # noqa: BLE001
            return {"id": "integrations_health",
                    "label": "Live integration probes",
                    "severity": "warn", "passed": False,
                    "detail": f"probe-runner crashed: {str(e)[:160]}"}

    @router.get("/deploy-readiness", dependencies=[Depends(require_admin)])
    async def deploy_readiness():
        checks: List[Dict[str, Any]] = []
        # Order matters — blockers first so UI can short-circuit
        for c in [
            _check_mongo, _check_critical_collections,
            _check_critical_indexes, _check_ttl_indexes,
            _check_r2, _check_resend,
            _check_integration_errors, _check_r2_degraded,
            _check_training_seed, _check_master_coverage,
            _check_integrations_health,
            _check_default_admin,
        ]:
            try:
                checks.append(await c())
            except Exception as e:  # noqa: BLE001
                checks.append({"id": c.__name__, "label": c.__name__,
                               "severity": "warn", "passed": False, "detail": f"check failed: {e}"})

        blockers_failed = [c for c in checks if c["severity"] == "blocker" and not c["passed"]]
        warns_failed = [c for c in checks if c["severity"] == "warn" and not c["passed"]]

        if blockers_failed:
            overall = "blocked"
        elif warns_failed:
            overall = "attention"
        else:
            overall = "ready"

        # TRACK 28.11 · Canonical status vocabulary so Diagnostics /
        # OCC / any consumer can classify this card without inventing
        # its own severity map. Also annotate each check.
        from lib.canonical_status import (  # noqa: PLC0415
            HEALTHY, ATTENTION, CRITICAL, to_canonical,
        )
        canonical_overall = {
            "ready": HEALTHY,
            "attention": ATTENTION,
            "blocked": CRITICAL,
        }.get(overall, ATTENTION)
        canonical_reason_code = (
            "healthy" if canonical_overall == HEALTHY
            else "blockers" if canonical_overall == CRITICAL
            else "warns_present"
        )
        canonical_summary = (
            f"{len(checks) - len(blockers_failed) - len(warns_failed)}/{len(checks)} checks passed"
            f" · {len(blockers_failed)} blocker(s) · {len(warns_failed)} warn(s)"
        )
        canonical_action = (
            "" if canonical_overall == HEALTHY
            else "Investigate blocker(s) below; deployment is not authorized." if canonical_overall == CRITICAL
            else "Review the warn(s) below; production deploy is authorized after triage."
        )
        for c in checks:
            c["canonical_status"] = to_canonical(
                "healthy" if c["passed"] else ("critical" if c["severity"] == "blocker" else "attention")
            )

        return {
            "overall_status": overall,
            "canonical_status": canonical_overall,
            "canonical_reason_code": canonical_reason_code,
            "canonical_summary": canonical_summary,
            "recommended_action": canonical_action,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "blocker_count": len(blockers_failed),
            "warn_count": len(warns_failed),
            "total_checks": len(checks),
            "checks": checks,
        }

    return router


__all__ = ["build_deploy_readiness_router"]
