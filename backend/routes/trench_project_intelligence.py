"""TRACK 23.10-C · Trench Project Intelligence read APIs.

Consumers of the 7 canonical trench facts + 4 derived views. Read-only.

Scope
-----
* PM tokens: only projects they are assigned to (via `pm_auth.compute_pm_scope`).
* Safety / Admin tokens: company-wide + any project.
* Field / Trench / Shop / Dispatch tokens: rejected at 403 (this is
  operational-intelligence surface, not field surface).

Endpoints
---------
GET /api/trench-intelligence/projects/{project_number}/summary
GET /api/trench-intelligence/projects/{project_number}/excavations
GET /api/trench-intelligence/projects/{project_number}/inspections
GET /api/trench-intelligence/projects/{project_number}/holds
GET /api/trench-intelligence/projects/{project_number}/repairs
GET /api/trench-intelligence/projects/{project_number}/competent-persons
GET /api/trench-intelligence/projects/{project_number}/deployments
GET /api/trench-intelligence/projects/{project_number}/asset-utilization
GET /api/trench-intelligence/projects/{project_number}/releases
GET /api/trench-intelligence/projects/{project_number}/activity
GET /api/trench-intelligence/projects/{project_number}/readiness
GET /api/trench-intelligence/company/summary                              (Safety/Admin only)
POST /api/trench-intelligence/backfill                                    (Admin only)
POST /api/trench-intelligence/projects/{project_number}/recompute-summary (Safety/Admin only)
GET  /api/trench-intelligence/link-resolve/{collection}/{record_id}       (Safety/Admin — diagnostic)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from services.certifications.qualification_registry import (
    list_active_qualifications,
)
from services.ods_spine.store import COLL_FACTS
from services.trench_safety.facts_emitter import (
    SOURCE_TYPE_TRENCH,
    recompute_project_excavation_summary,
)
from services.trench_safety.derived_views import (
    deployment_view,
    excavation_activity_view,
    trench_asset_utilization,
    trench_release_view,
)
from services.trench_safety.project_linker import resolve_project


PM_ROLES = {"pm"}
SAFETY_ADMIN_ROLES = {"safety", "admin"}
ALLOWED_ROLES = PM_ROLES | SAFETY_ADMIN_ROLES


def _role(actor: Dict[str, Any]) -> str:
    return (actor.get("_actor") or actor.get("role") or "").lower()


async def _pm_project_numbers(db, actor: Dict[str, Any]) -> Optional[List[str]]:
    """None = unrestricted (admin/safety). List = PM's assigned projects."""
    if _role(actor) in SAFETY_ADMIN_ROLES:
        return None
    try:
        from pm_auth import compute_pm_scope                        # noqa: PLC0415
        scope = await compute_pm_scope(db, actor)
        if getattr(scope, "is_admin", False):
            return None
        return list(scope.project_numbers or [])
    except Exception:                                              # noqa: BLE001
        return []


def _facts_query(project_number: str, fact_type: str) -> Dict[str, Any]:
    return {
        "source_type": SOURCE_TYPE_TRENCH,
        "source_id": "trench_safety",
        "project_id": str(project_number),
        "fact_type": fact_type,
        "is_current": True,
    }


async def _load_facts(
    db, project_number: str, fact_type: str, limit: int = 2000,
) -> List[Dict[str, Any]]:
    return await db[COLL_FACTS].find(
        _facts_query(project_number, fact_type), {"_id": 0},
    ).to_list(limit)


def build_trench_project_intelligence_router(
    db,
    *,
    require_read_dep,
    require_admin_dep,
) -> APIRouter:
    """`require_read_dep`  — any authenticated portal token (multi-portal).
    Additional scope + role checks are applied per-endpoint."""

    r = APIRouter(prefix="/api", tags=["trench-project-intelligence"])

    async def _authorize_project(
        actor: Dict[str, Any], project_number: str,
    ) -> None:
        role = _role(actor)
        if role not in ALLOWED_ROLES:
            raise HTTPException(
                403,
                "Trench intelligence: PM · Safety · Admin only",
            )
        if role in PM_ROLES:
            allowed = await _pm_project_numbers(db, actor)
            if allowed is not None and str(project_number) not in allowed:
                raise HTTPException(
                    403,
                    "PM: not assigned to this project",
                )

    async def _authorize_company(actor: Dict[str, Any]) -> None:
        if _role(actor) not in SAFETY_ADMIN_ROLES:
            raise HTTPException(
                403, "Company-wide view: Safety · Admin only",
            )

    # ─── Project summary ──────────────────────────────────────────
    @r.get("/trench-intelligence/projects/{project_number}/summary")
    async def project_summary(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        rows = await db[COLL_FACTS].find(
            _facts_query(project_number, "project_excavation_summary_fact"),
            {"_id": 0},
        ).sort("created_at", -1).to_list(1)
        if not rows:
            # Compute on-demand — never fake, always honest.
            await recompute_project_excavation_summary(
                db, project_number, actor="on_demand",
                trigger="api.summary",
            )
            rows = await db[COLL_FACTS].find(
                _facts_query(project_number, "project_excavation_summary_fact"),
                {"_id": 0},
            ).sort("created_at", -1).to_list(1)
        return {
            "project_number": project_number,
            "summary": (rows[0] or {}).get("payload") if rows else {},
            "fact_id": (rows[0] or {}).get("fact_id") if rows else None,
        }

    # ─── Excavations / inspections / holds / repairs (fact lists) ─
    @r.get("/trench-intelligence/projects/{project_number}/excavations")
    async def project_excavations(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        rows = await _load_facts(db, project_number, "excavation_day_fact")
        return {"project_number": project_number, "count": len(rows), "items": rows}

    @r.get("/trench-intelligence/projects/{project_number}/inspections")
    async def project_inspections(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        rows = await _load_facts(db, project_number, "trench_inspection_fact")
        return {"project_number": project_number, "count": len(rows), "items": rows}

    @r.get("/trench-intelligence/projects/{project_number}/holds")
    async def project_holds(
        project_number: str,
        active_only: bool = Query(default=False),
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        rows = await _load_facts(db, project_number, "trench_hold_fact")
        if active_only:
            rows = [r for r in rows if (r.get("payload") or {}).get("is_active")]
        return {"project_number": project_number, "count": len(rows), "items": rows}

    @r.get("/trench-intelligence/projects/{project_number}/repairs")
    async def project_repairs(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        rows = await _load_facts(db, project_number, "trench_repair_fact")
        return {"project_number": project_number, "count": len(rows), "items": rows}

    # ─── Competent Persons (consume 23.10-B engine — DO NOT duplicate)
    @r.get("/trench-intelligence/projects/{project_number}/competent-persons")
    async def project_competent_persons(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        # 1) Currently active CPs (org-wide registry).
        registry = await list_active_qualifications(
            db, qualification_type="COMPETENT_PERSON", warning_days=30,
        )
        # 2) Historical CP assignments already made against this project.
        assignments = await _load_facts(
            db, project_number, "competent_person_assignment_fact",
        )
        return {
            "project_number": project_number,
            "registry": registry,
            "historical_assignments": assignments,
        }

    # ─── Deployments / utilisation / releases / activity (derived) ─
    @r.get("/trench-intelligence/projects/{project_number}/deployments")
    async def project_deployments(
        project_number: str,
        asset_id: Optional[str] = None,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        items = await deployment_view(
            db, project_number=project_number, asset_id=asset_id,
        )
        return {"project_number": project_number, "count": len(items), "items": items}

    @r.get("/trench-intelligence/projects/{project_number}/asset-utilization")
    async def project_asset_utilization(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        items = await trench_asset_utilization(db, project_number)
        return {"project_number": project_number, "count": len(items), "items": items}

    @r.get("/trench-intelligence/projects/{project_number}/releases")
    async def project_releases(
        project_number: str,
        limit: int = Query(default=200, ge=1, le=1000),
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        items = await trench_release_view(
            db, project_number=project_number, limit=limit,
        )
        return {"project_number": project_number, "count": len(items), "items": items}

    @r.get("/trench-intelligence/projects/{project_number}/activity")
    async def project_activity(
        project_number: str,
        since: Optional[str] = None, until: Optional[str] = None,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        view = await excavation_activity_view(
            db, project_number, since_date=since, until_date=until,
        )
        return view

    # ─── Scheduling readiness (consumer surface — never owned here) ─
    @r.get("/trench-intelligence/projects/{project_number}/readiness")
    async def project_readiness(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        """Scheduling-consumable readiness object. Booleans only. Never
        overrides Scheduling's own guardrails — this is a read model."""
        await _authorize_project(actor, project_number)
        # Data we need.
        holds = await _load_facts(db, project_number, "trench_hold_fact")
        open_holds = [h for h in holds
                      if (h.get("payload") or {}).get("is_active")]
        repairs = await _load_facts(db, project_number, "trench_repair_fact")
        open_repairs_unsafe = [
            r for r in repairs
            if (r.get("payload") or {}).get("status") not in ("completed",)
            or not (r.get("payload") or {}).get("safe_to_use_verified")
        ]
        excavations = await _load_facts(db, project_number, "excavation_day_fact")
        # Take latest excavation-day fact as the current planning signal.
        excavations.sort(key=lambda f: f.get("date") or "", reverse=True)
        latest_exc = excavations[0] if excavations else None
        latest_pl = (latest_exc or {}).get("payload") or {}

        cp_registry = await list_active_qualifications(
            db, qualification_type="COMPETENT_PERSON",
        )
        cp_assignments = await _load_facts(
            db, project_number, "competent_person_assignment_fact",
        )
        cp_assigned = bool(cp_assignments)
        cp_valid = (cp_assignments
                    and (cp_assignments[0].get("payload") or {}).get("cert_valid_at_report"))

        unresolved = [
            e for e in excavations
            if (e.get("payload") or {}).get("utilities_status") == "damage_strike"
        ]

        blockers = {
            "open_hold_blocks_work": bool(open_holds),
            "open_repair_blocks_work": bool(open_repairs_unsafe),
            "utility_conflict_blocks_work": bool(unresolved),
            "competent_person_cert_expired": cp_assigned and not bool(cp_valid),
        }
        safety_clear = not any(blockers.values()) and cp_assigned

        return {
            "project_number": project_number,
            "excavation_work_today": bool(latest_pl.get("inspection_completed") is not None),
            "excavation_planned_tomorrow": bool(latest_pl.get("tomorrow_planned")),
            "competent_person_assigned": cp_assigned,
            "competent_person_cert_valid": bool(cp_valid),
            "competent_person_org_registry_count": len(cp_registry),
            "open_hold_count": len(open_holds),
            "open_repair_unsafe_count": len(open_repairs_unsafe),
            "utility_conflict_count": len(unresolved),
            "safety_clear_to_schedule": safety_clear,
            "blockers": blockers,
        }

    # ─── Company-wide (Safety + Admin only) ───────────────────────
    @r.get("/trench-intelligence/company/summary")
    async def company_summary(
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_company(actor)
        pipeline = [
            {"$match": {
                "source_type": SOURCE_TYPE_TRENCH,
                "source_id": "trench_safety",
                "fact_type": "project_excavation_summary_fact",
                "is_current": True,
            }},
            {"$sort": {"created_at": -1}},
        ]
        rows = await db[COLL_FACTS].aggregate(pipeline).to_list(5000)
        total_projects = len(rows)
        agg = {
            "excavation_day_count": 0, "trench_inspection_count": 0,
            "trench_hold_count": 0, "open_trench_holds": 0,
            "trench_repair_open_count": 0,
            "trench_safe_to_use_verified_count": 0,
            "competent_person_assignments": 0,
            "max_depth_observed_ft": 0.0,
        }
        for row in rows:
            pl = row.get("payload") or {}
            for k in list(agg.keys()):
                if k == "max_depth_observed_ft":
                    v = float(pl.get(k) or 0)
                    if v > agg[k]:
                        agg[k] = v
                else:
                    agg[k] += int(pl.get(k) or 0)
        return {
            "projects_with_summary": total_projects,
            "aggregates": agg,
            "note": "Values here are LIVE-per-project sums · "
                    "MISSING / PARTIAL projects excluded",
        }

    # ─── Diagnostics: resolve a single record's linkage ───────────
    @r.get("/trench-intelligence/link-resolve/{collection}/{record_id}")
    async def link_resolve(
        collection: str, record_id: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        if _role(actor) not in SAFETY_ADMIN_ROLES:
            raise HTTPException(
                403, "Safety / Admin only")
        allowed_cols = {
            "trench_excavations", "trench_safety_inspections",
            "trench_safety_holds", "trench_safety_repairs",
            "trench_safety_deployments",
        }
        if collection not in allowed_cols:
            raise HTTPException(
                400, f"collection must be one of {sorted(allowed_cols)}",
            )
        row = await db[collection].find_one({"id": record_id}, {"_id": 0})
        if not row:
            raise HTTPException(404, "record not found")
        linkage = await resolve_project(db, row)
        return {
            "collection": collection,
            "record_id": record_id,
            "linkage": linkage.as_dict(),
        }

    # ─── Admin ops ────────────────────────────────────────────────
    @r.post("/trench-intelligence/backfill")
    async def trigger_backfill(
        boot_mode: bool = Query(default=True),
        _admin: Any = Depends(require_admin_dep),
    ):
        """Admin-only manual backfill trigger. Fire-and-forget so it
        never times out preview ingress on large data sets.

        * `boot_mode=true` (default) — capped batch of
          `TRACK_23_10_C_BOOT_LIMIT` rows per collection. Returns
          immediately with a run marker.
        * `boot_mode=false` — full replay. Also fire-and-forget; poll
          `/api/trench-intelligence/company/summary` for progress.
        """
        import asyncio                                          # noqa: PLC0415
        from scripts.backfill_track_23_10_c_trench_facts import (  # noqa: PLC0415
            run_backfill,
        )
        started_at = datetime.now(timezone.utc).isoformat()

        async def _bg():
            try:
                await run_backfill(db, boot_mode=boot_mode)
            except Exception as exc:                              # noqa: BLE001
                # Non-fatal — the boot hook re-runs on next restart.
                print(f"[api.backfill] {exc}")

        asyncio.create_task(_bg())
        return {
            "track": "23.10-C",
            "kicked_off": True,
            "boot_mode": boot_mode,
            "started_at": started_at,
            "note": "Fire-and-forget. Poll /api/trench-intelligence/company/summary for progress.",
        }

    @r.post("/trench-intelligence/projects/{project_number}/recompute-summary")
    async def trigger_recompute(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        if _role(actor) not in SAFETY_ADMIN_ROLES:
            raise HTTPException(403, "Safety / Admin only")
        fid = await recompute_project_excavation_summary(
            db, project_number, actor="api.recompute",
            trigger="api.recompute_summary",
        )
        return {"project_number": project_number, "fact_id": fid,
                "at": datetime.now(timezone.utc).isoformat()}

    return r


__all__ = ["build_trench_project_intelligence_router"]
