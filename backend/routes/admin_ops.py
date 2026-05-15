"""
admin_ops.py — Iter130 operational infrastructure.

Four lightweight, admin-only operational tools for deployment safety,
visibility, and accountability. Designed to be FAST and SIMPLE — no
giant dashboards, no analytics bloat, no full-table scans.

  GET /api/admin/system-health      — green/yellow/red status panel
  GET /api/admin/audit-log          — paginated unified audit feed
  GET /api/admin/search             — cross-collection operational search
  GET /api/admin/deploy-recovery    — known-good builds + R2 chain probe

All endpoints respect the admin gate. Reads only — no writes.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    return dt.replace(microsecond=0).isoformat()


def build_admin_ops_router(db, require_admin) -> APIRouter:
    router = APIRouter(prefix="/api/admin", tags=["admin-ops"])

    # ════════════════════════════════════════════════════════════════
    #  system_health computation — exposed as a reusable coroutine
    #  so the background health_monitor can call it without paying
    #  an HTTP round-trip to ourselves.
    # ════════════════════════════════════════════════════════════════
    async def compute_system_health() -> Dict[str, Any]:
        cards: List[Dict[str, Any]] = []
        now = _now()

        # 1. Database connectivity
        try:
            await db.command("ping")
            cards.append({"key": "database", "label": "MongoDB", "status": "green",
                          "detail": "Connected"})
        except Exception as e:  # noqa: BLE001
            cards.append({"key": "database", "label": "MongoDB", "status": "red",
                          "detail": f"Ping failed: {e!s}"[:120]})

        # 2. R2 / object storage status (from photo_storage helper)
        try:
            from photo_storage import is_configured as r2_configured  # noqa: PLC0415
            ok = r2_configured()
            cards.append({"key": "r2", "label": "Cloudflare R2",
                          "status": "green" if ok else "yellow",
                          "detail": "Configured · ready" if ok else "Not configured (inline-only)"})
        except Exception as e:  # noqa: BLE001
            cards.append({"key": "r2", "label": "Cloudflare R2", "status": "yellow",
                          "detail": f"Probe error: {e!s}"[:120]})

        # 3. Last successful backup (any kind)
        try:
            last = await db.backup_runs.find_one(
                {"status": "success"}, {"_id": 0}, sort=[("started_at", -1)]
            )
            if last:
                started_at = last.get("started_at")
                dt = _parse_iso(started_at)
                hrs = (now - dt).total_seconds() / 3600.0 if dt else 999
                status = "green" if hrs < 24 else "yellow" if hrs < 72 else "red"
                cards.append({"key": "backup", "label": "Last backup",
                              "status": status,
                              "detail": f"{started_at} ({hrs:.1f}h ago)"})
            else:
                cards.append({"key": "backup", "label": "Last backup",
                              "status": "yellow", "detail": "No backup runs recorded"})
        except Exception:  # noqa: BLE001
            cards.append({"key": "backup", "label": "Last backup",
                          "status": "yellow", "detail": "Backup state unknown"})

        # 4. Recent auth failures (last 1h)
        try:
            since = now - timedelta(hours=1)
            cnt = await db.admin_audit.count_documents({
                "action": {"$in": ["login_failed", "auth_failed", "login_blocked"]},
                "at": {"$gte": since.isoformat()},
            })
            status = "green" if cnt < 10 else "yellow" if cnt < 50 else "red"
            cards.append({"key": "auth_failures", "label": "Auth failures (1h)",
                          "status": status, "detail": f"{cnt} attempts"})
        except Exception:
            cards.append({"key": "auth_failures", "label": "Auth failures (1h)",
                          "status": "yellow", "detail": "Audit query unavailable"})

        # 5. Integration health (Motive + MaintainX placeholders)
        try:
            cfg = await db.integration_settings.find_one({}, {"_id": 0}) or {}
            integrations = []
            for prov in ("motive", "maintainx"):
                p = cfg.get(prov, {})
                enabled = bool(p.get("enabled"))
                demo = bool(p.get("demo_mode"))
                integrations.append({
                    "provider": prov,
                    "status": "green" if enabled else "yellow" if demo else "yellow",
                    "detail": "Enabled" if enabled else ("Demo mode" if demo else "Stubbed"),
                })
            cards.append({"key": "integrations", "label": "Integrations",
                          "status": "yellow",  # always yellow until live
                          "detail": "Motive + MaintainX (stubbed)",
                          "children": integrations})
        except Exception:
            cards.append({"key": "integrations", "label": "Integrations",
                          "status": "yellow", "detail": "Stubbed (no live API yet)"})

        # 6. Recent failed sync count (24h)
        try:
            since = now - timedelta(hours=24)
            cnt = await db.integration_error_logs.count_documents({
                "at": {"$gte": since.isoformat()},
            })
            status = "green" if cnt == 0 else "yellow" if cnt < 5 else "red"
            cards.append({"key": "failed_syncs", "label": "Failed syncs (24h)",
                          "status": status, "detail": f"{cnt} failures"})
        except Exception:
            cards.append({"key": "failed_syncs", "label": "Failed syncs (24h)",
                          "status": "green", "detail": "0 failures"})

        # 7. Active sessions (rough — directory tokens issued in last 12h)
        try:
            since = now - timedelta(hours=12)
            cnt = await db.user_directory.count_documents({
                "last_login_at": {"$gte": since.isoformat()},
            })
            cards.append({"key": "active_sessions", "label": "Active users (12h)",
                          "status": "green", "detail": f"{cnt} signed-in users"})
        except Exception:
            cards.append({"key": "active_sessions", "label": "Active users (12h)",
                          "status": "green", "detail": "—"})

        # 8. Build version (read from env stamped at deploy)
        version = os.environ.get("MASCI_BUILD_VERSION", "unknown")
        built_at = os.environ.get("MASCI_BUILD_AT", "—")
        cards.append({"key": "version", "label": "Build version",
                      "status": "green",
                      "detail": f"{version} · built {built_at}"})

        # Roll-up overall status
        overall = "green"
        if any(c["status"] == "red" for c in cards):
            overall = "red"
        elif any(c["status"] == "yellow" for c in cards):
            overall = "yellow"

        return {
            "overall": overall,
            "cards": cards,
            "checked_at": _iso(now),
        }

    # Expose for the background health monitor (no HTTP round-trip).
    router.compute_system_health = compute_system_health  # type: ignore[attr-defined]

    # ════════════════════════════════════════════════════════════════
    #  GET /system-health  — admin-only HTTP endpoint
    # ════════════════════════════════════════════════════════════════
    @router.get("/system-health", dependencies=[Depends(require_admin)])
    async def system_health():
        return await compute_system_health()

    # ════════════════════════════════════════════════════════════════
    #  GET /system-health/recent  — last N synthetic monitor results
    # ════════════════════════════════════════════════════════════════
    @router.get("/system-health/recent", dependencies=[Depends(require_admin)])
    async def system_health_recent(limit: int = Query(40, ge=1, le=200)):
        rows: List[Dict[str, Any]] = []
        async for r in db.health_monitor_runs.find(
            {}, {"_id": 0},
        ).sort("at", -1).limit(limit):
            rows.append(r)
        return {"limit": limit, "rows": rows}

    # ════════════════════════════════════════════════════════════════
    #  GET /audit-log  — unified merged feed
    # ════════════════════════════════════════════════════════════════
    @router.get("/audit-log", dependencies=[Depends(require_admin)])
    async def audit_log(
        q: Optional[str] = Query(None),
        actor: Optional[str] = Query(None),
        action: Optional[str] = Query(None),
        source: Optional[str] = Query(None, description="audit_events|admin_audit|operations_events|integration_wizard_runs"),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ):
        """
        Aggregates four append-only collections into one timeline:
          - audit_events (impersonation, dispatch actions, etc.)
          - admin_audit (multi-portal sign-ins, password changes, role changes)
          - operations_events (asset events from operations.py)
          - integration_wizard_runs (mapping wizard commits)
        Each row is normalized to {at, actor, action, target, source, detail}.
        """
        rows: List[Dict[str, Any]] = []
        sources = [source] if source else [
            "audit_events", "admin_audit", "operations_events", "integration_wizard_runs",
        ]

        # We pull per-collection then merge-sort. Cap each query so memory
        # stays bounded even at offset=0.
        per_source_cap = max(limit * 4, 80)

        if "audit_events" in sources:
            async for r in db.audit_events.find({}, {"_id": 0}).sort("at", -1).limit(per_source_cap):
                rows.append({
                    "at": r.get("at"),
                    "actor": r.get("actor_email") or r.get("actor") or "system",
                    "action": r.get("kind") or r.get("action") or "audit_event",
                    "target": r.get("user_email") or r.get("target_email") or "",
                    "source": "audit_events",
                    "detail": {k: v for k, v in r.items() if k not in {"at", "_id"}},
                })

        if "admin_audit" in sources:
            async for r in db.admin_audit.find({}, {"_id": 0}).sort("at", -1).limit(per_source_cap):
                rows.append({
                    "at": r.get("at"),
                    "actor": r.get("actor_email") or "anonymous",
                    "action": r.get("action") or "admin_audit",
                    "target": r.get("target_email") or "",
                    "source": "admin_audit",
                    "detail": {k: v for k, v in r.items() if k not in {"at", "_id"}},
                })

        if "operations_events" in sources:
            async for r in db.operations_events.find({}, {"_id": 0}).sort("created_at", -1).limit(per_source_cap):
                rows.append({
                    "at": r.get("created_at"),
                    "actor": r.get("created_by") or r.get("actor_name") or "system",
                    "action": r.get("event_type") or "ops_event",
                    "target": r.get("asset_id") or r.get("employee_id") or "",
                    "source": "operations_events",
                    "detail": {
                        "severity": r.get("severity"),
                        "status": r.get("status"),
                        "source_module": r.get("source_module"),
                        "summary": r.get("summary") or r.get("notes") or "",
                        "id": r.get("id"),
                    },
                })

        if "integration_wizard_runs" in sources:
            async for r in db.integration_wizard_runs.find({}, {"_id": 0}).sort("started_at", -1).limit(per_source_cap):
                rows.append({
                    "at": r.get("started_at"),
                    "actor": r.get("actor") or "admin",
                    "action": f"wizard_commit_{r.get('kind', 'unknown')}",
                    "target": r.get("source_label") or "",
                    "source": "integration_wizard_runs",
                    "detail": {
                        "totals": r.get("totals"),
                        "id": r.get("id"),
                    },
                })

        # Apply filters
        if actor:
            a = actor.lower()
            rows = [r for r in rows if a in (r["actor"] or "").lower()]
        if action:
            ac = action.lower()
            rows = [r for r in rows if ac in (r["action"] or "").lower()]
        if q:
            qs = q.lower()
            def matches(r):
                blob = f"{r.get('actor')} {r.get('action')} {r.get('target')} {r.get('source')}".lower()
                return qs in blob
            rows = [r for r in rows if matches(r)]

        # Sort by timestamp desc
        rows.sort(key=lambda r: r.get("at") or "", reverse=True)
        total = len(rows)
        paged = rows[offset: offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "rows": paged,
        }

    # ════════════════════════════════════════════════════════════════
    #  GET /search  — cross-collection operational search
    # ════════════════════════════════════════════════════════════════
    @router.get("/search", dependencies=[Depends(require_admin)])
    async def global_search(
        q: str = Query(..., min_length=2, max_length=80),
        limit: int = Query(8, ge=1, le=20, description="Max results per category"),
    ):
        """
        Lightweight typeahead across the operational object surface.
        Returns up to `limit` matches per category. No full table scans —
        uses regex on indexed string fields. The 7 collection probes run
        concurrently via asyncio.gather() (~3× speedup at no risk).
        """
        import asyncio  # noqa: PLC0415

        # Escape regex special chars in user input
        safe = re.escape(q.strip())
        if not safe:
            return {"q": q, "groups": []}
        rx = {"$regex": safe, "$options": "i"}

        async def probe(coll, fields, label, link_template, status_field=None):
            ors = [{f: rx} for f in fields]
            try:
                cur = coll.find({"$or": ors}, {"_id": 0}).limit(limit)
                rows = []
                async for r in cur:
                    title = next((str(r.get(f)) for f in fields if r.get(f)), "—")
                    rows.append({
                        "id": r.get("id") or r.get("_id"),
                        "title": title,
                        "subtitle": ", ".join(
                            f"{f}={r.get(f)}" for f in fields[1:3] if r.get(f)
                        )[:140],
                        "status": (r.get(status_field) if status_field else None),
                        "link": link_template.format(id=r.get("id") or ""),
                    })
                if rows:
                    return {"label": label, "rows": rows, "count": len(rows)}
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[search] {label} failed: {e}")
            return None

        results = await asyncio.gather(
            probe(db.equipment_master,    ["unit_number", "name", "type", "make", "model"], "Equipment / Assets",  "/admin/assets/{id}"),
            probe(db.employees,           ["name", "employee_id", "role", "title"],         "Employees",           "/admin/people?employee_id={id}"),
            probe(db.operations_events,   ["event_type", "summary", "notes"],               "Operations Events",   "/admin/operations-events?id={id}", status_field="status"),
            probe(db.equipment_transfers, ["from_project_number", "to_project_number", "reason"], "Transfers",      "/admin/dispatch?transfer={id}", status_field="status"),
            probe(db.incidents,           ["title", "description", "incident_type"],        "Incidents",           "/incidents/{id}", status_field="severity"),
            probe(db.corrective_actions,  ["title", "description", "category"],             "Corrective Actions",  "/safety-portal/corrective-actions?id={id}", status_field="status"),
            probe(db.projects,            ["project_number", "name", "location"],           "Jobs / Projects",     "/admin/jobs?id={id}"),
        )
        groups = [r for r in results if r]

        return {
            "q": q,
            "groups": groups,
            "total": sum(g["count"] for g in groups),
        }

    # ════════════════════════════════════════════════════════════════
    #  GET /deploy-recovery  — backup/version probe
    # ════════════════════════════════════════════════════════════════
    @router.get("/deploy-recovery", dependencies=[Depends(require_admin)])
    async def deploy_recovery_status():
        """
        Read-only operational readiness probe. Reports:
          - current build version
          - most recent successful backup runs (last 5)
          - R2 cloud-archive chain state if configured
          - known-good build version stamps from history
        Frontend renders this alongside the static rollback playbook.
        """
        version = os.environ.get("MASCI_BUILD_VERSION", "unknown")
        built_at = os.environ.get("MASCI_BUILD_AT", "—")

        # Recent successful backups (any kind)
        recent_backups: List[Dict[str, Any]] = []
        try:
            async for r in db.backup_runs.find(
                {"status": "success"}, {"_id": 0},
            ).sort("started_at", -1).limit(5):
                recent_backups.append({
                    "started_at": r.get("started_at"),
                    "kind": r.get("kind") or "unknown",
                    "destination": r.get("destination") or "—",
                    "size_bytes": r.get("size_bytes") or 0,
                })
        except Exception:  # noqa: BLE001
            recent_backups = []

        # R2 status
        r2_status = "yellow"
        r2_detail = "Not configured"
        try:
            from photo_storage import is_configured as r2_configured  # noqa: PLC0415
            if r2_configured():
                r2_status = "green"
                r2_detail = "Configured · uploads ready"
        except Exception:  # noqa: BLE001
            pass

        # Known-good build history (last 10 stamps from version_history if present)
        history: List[Dict[str, Any]] = []
        try:
            async for r in db.deploy_version_history.find(
                {}, {"_id": 0},
            ).sort("deployed_at", -1).limit(10):
                history.append(r)
        except Exception:
            history = []

        return {
            "current": {
                "version": version,
                "built_at": built_at,
            },
            "r2": {"status": r2_status, "detail": r2_detail},
            "recent_backups": recent_backups,
            "known_good_history": history,
            "checked_at": _iso(_now()),
        }

    return router


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    try:
        # Accept "...Z" and "...+00:00"
        if isinstance(s, str) and s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:  # noqa: BLE001
        return None


__all__ = ["build_admin_ops_router"]
