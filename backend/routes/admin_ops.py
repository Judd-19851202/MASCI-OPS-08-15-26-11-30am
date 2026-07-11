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
    # TRUST-TIME-1 · always emit tz-aware ISO so the browser localizes.
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
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
        # Also check for recent degraded-mode fallbacks (R2 misconfigured
        # mid-deploy means files are silently going to Mongo as base64
        # blobs — that's the failure mode P3 wants us to alert on).
        try:
            from photo_storage import is_configured as r2_configured  # noqa: PLC0415
            ok = r2_configured()
            # Count degraded events in last 24h — accept both BSON datetime
            # and legacy ISO string entries so historical records still match.
            since_dt = now - timedelta(hours=24)
            since_iso = since_dt.isoformat()
            degraded = 0
            try:
                degraded = await db.r2_degraded_events.count_documents({
                    "$or": [
                        {"at": {"$gte": since_dt}},
                        {"at": {"$gte": since_iso}},
                    ],
                })
            except Exception:  # noqa: BLE001
                pass
            if not ok:
                cards.append({"key": "r2", "label": "Cloudflare R2",
                              "status": "yellow",
                              "detail": "Not configured (inline-only — large files going to MongoDB)"})
            elif degraded > 0:
                cards.append({"key": "r2", "label": "Cloudflare R2",
                              "status": "red",
                              "detail": f"DEGRADED — {degraded} uploads fell back to Mongo in last 24h. Check R2 credentials."})
            else:
                cards.append({"key": "r2", "label": "Cloudflare R2",
                              "status": "green",
                              "detail": "Configured · ready · no degraded events"})
        except Exception as e:  # noqa: BLE001
            cards.append({"key": "r2", "label": "Cloudflare R2", "status": "yellow",
                          "detail": f"Probe error: {e!s}"[:120]})

        # 3. Last successful backup (any kind)
        # iter440 · Phase 31.2 health-lock · real scheduler writes to
        # `backup_health` with `ok=true` + `ts` (NOT
        # `backup_runs.status=success/started_at`). Filter to rows that
        # actually produced a backup file (filename != null) so the
        # banner never reports a quota-probe row as a backup.
        #
        # Track 15.73D · primary signal is the R2 bucket newest-object
        # age (same source of truth as `/api/health/full`). The audit
        # row is consulted only when R2 listing is unavailable. This
        # prevents the alert from firing when R2 has fresh backups but
        # the `backup_health` write-path is briefly broken — a real
        # source of post-restart alert spam.
        try:
            from server import _r2_backup_age_seconds_cached  # noqa: PLC0415
            r2_age_s = await _r2_backup_age_seconds_cached()
        except Exception:
            r2_age_s = None
        try:
            if r2_age_s is not None:
                hrs = r2_age_s / 3600.0
                status = "green" if hrs < 24 else "yellow" if hrs < 72 else "red"
                cards.append({"key": "backup", "label": "Last backup",
                              "status": status,
                              "detail": f"R2 newest object {hrs:.1f}h ago"})
            else:
                last = await db.backup_health.find_one(
                    {"ok": True, "filename": {"$nin": [None, ""]}},
                    {"_id": 0}, sort=[("ts", -1)],
                )
                if last:
                    started_at = last.get("ts")
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

        # 5. Integration health (Motive + MaintainX) — DB-backed truth
        # via shared helper. No more hard-coded yellow; surfaces last
        # successful sync + webhook status so the admin can verify
        # at-a-glance that an integration is actually live.
        # TRACK 28.11: MaintainX is NOT_APPLICABLE for MASCI — its
        # `disabled + mocked=True` state does not contribute to the
        # parent integrations card severity or overall rollup.
        try:
            from routes.integrations._storage import compute_provider_status  # noqa: PLC0415
            integrations: List[Dict[str, Any]] = []
            env_var_map = {"motive": "MOTIVE_API_KEY", "maintainx": "MAINTAINX_API_KEY"}
            colour_map = {"ok": "green", "degraded": "yellow", "disabled": "not_applicable"}
            child_statuses: List[str] = []
            for prov in ("motive", "maintainx"):
                snap = await compute_provider_status(
                    db, prov, env_api_key_var=env_var_map.get(prov),
                )
                snap_status = snap["status"]
                # TRACK 28.11 · NOT_APPLICABLE for MASCI-unused integrations.
                if snap_status == "disabled" and snap.get("mocked"):
                    colour = "not_applicable"
                else:
                    colour = colour_map.get(snap_status, "yellow")
                detail_bits: List[str] = []
                if snap_status == "ok":
                    detail_bits.append("Live")
                    if snap.get("last_successful_sync_at"):
                        detail_bits.append(f"synced {snap['last_successful_sync_at']}")
                    detail_bits.append(
                        "webhook armed" if snap["webhook_secret_present"] else "webhook secret missing"
                    )
                elif snap_status == "degraded":
                    detail_bits.append(snap["message"])
                elif colour == "not_applicable":
                    detail_bits.append("Not applicable — MASCI does not use this integration.")
                else:
                    detail_bits.append("Stubbed" if snap["mocked"] else snap["message"])
                integrations.append({
                    "provider":               prov,
                    "status":                 colour,
                    "detail":                 " · ".join(detail_bits),
                    "enabled":                snap["enabled"],
                    "applicable":             colour != "not_applicable",
                    "api_key_present":        snap["api_key_present"],
                    "webhook_secret_present": snap["webhook_secret_present"],
                    "last_successful_sync_at": snap["last_successful_sync_at"],
                    "last_failed_sync_at":    snap["last_failed_sync_at"],
                })
                child_statuses.append(colour)
            # Outer card colour reflects the worst APPLICABLE child.
            # not_applicable children never escalate the parent.
            applicable_statuses = [s for s in child_statuses if s != "not_applicable"]
            if "red" in applicable_statuses:
                outer = "red"
            elif "yellow" in applicable_statuses:
                outer = "yellow"
            elif applicable_statuses:
                outer = "green"
            else:
                outer = "not_applicable"
            outer_detail_parts: List[str] = []
            for child in integrations:
                outer_detail_parts.append(f"{child['provider'].title()}: {child['status']}")
            cards.append({
                "key":      "integrations",
                "label":    "Integrations",
                "status":   outer,
                "detail":   " · ".join(outer_detail_parts) if outer_detail_parts else "No integrations configured",
                "children": integrations,
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[system-health:integrations] {e}")
            cards.append({"key": "integrations", "label": "Integrations",
                          "status": "yellow", "detail": "Status query failed"})

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

        # 8. Build version — pull from live server module if the deploy
        # env vars weren't stamped (Emergent deploys don't set them,
        # so we fall back to the runtime source_hash + startup timestamp).
        # ATT-28.11C-1 fix: the previous fallback imported a symbol
        # (`_STARTED_AT`) that never existed on server.py, so the except
        # branch was always taken and the card rendered `built —`.
        # The real module variable is `_STARTUP_TS` (a tz-aware datetime).
        version = os.environ.get("MASCI_BUILD_VERSION") or ""
        built_at = os.environ.get("MASCI_BUILD_AT") or ""
        if not version:
            try:
                from server import _SOURCE_HASH as src_hash  # noqa: PLC0415
                version = str(src_hash or "unknown")[:12]
            except Exception:
                version = "unknown"
        if not built_at:
            try:
                from server import _STARTUP_TS as started  # noqa: PLC0415
                built_at = started.isoformat() if started else "—"
            except Exception:
                built_at = "—"
        cards.append({"key": "version", "label": "Build version",
                      "status": "green",
                      "detail": f"{version} · built {built_at}"})

        # Roll-up overall status — TRACK 28.11: canonical vocabulary,
        # not-applicable and disabled cards do NOT escalate severity.
        from lib.canonical_status import to_canonical, summarize, highest  # noqa: PLC0415
        for c in cards:
            c["canonical_status"] = to_canonical(
                c.get("status"),
                applicable=c.get("applicable", True),
                enabled=c.get("enabled", True),
            )
        canonical_summary = summarize(cards)
        overall = "green"
        if canonical_summary["critical"] > 0:
            overall = "red"
        elif canonical_summary["attention"] > 0:
            overall = "yellow"
        elif canonical_summary["unknown"] > 0:
            overall = "yellow"

        return {
            "overall": overall,
            "overall_canonical": canonical_summary["highest"],
            "cards": cards,
            "counts": {
                "healthy": canonical_summary["healthy"],
                "attention": canonical_summary["attention"],
                "critical": canonical_summary["critical"],
                "unknown": canonical_summary["unknown"],
                "stale": canonical_summary["stale"],
                "disabled": canonical_summary["disabled"],
                "not_applicable": canonical_summary["not_applicable"],
                "total_applicable": canonical_summary["total_applicable"],
                "total_cards": canonical_summary["total_cards"],
            },
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

        # Sort by timestamp desc · normalize datetime → ISO string so mixed
        # rows (older entries with `at` stored as datetime, newer ones as
        # ISO string) don't crash the comparator with a TypeError.
        def _ts(r):
            at = r.get("at")
            if not at:
                return ""
            if hasattr(at, "isoformat"):
                return at.isoformat()
            return str(at)
        rows.sort(key=_ts, reverse=True)
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
                        # iter140 — carry master IDs so we can enrich with
                        # canonical labels after all probes resolve.
                        "_equipment_master_id": r.get("equipment_master_id"),
                        "_employee_master_id": r.get("employee_master_id"),
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

        # ── iter140 — Master Label Enrichment ─────────────────────
        # Collect every equipment_master_id / employee_master_id surfaced
        # across all result groups, then do ONE bulk lookup per master
        # collection and stamp canonical labels back onto each row.
        eq_ids = {row["_equipment_master_id"] for g in groups for row in g["rows"]
                  if row.get("_equipment_master_id")}
        emp_ids = {row["_employee_master_id"] for g in groups for row in g["rows"]
                   if row.get("_employee_master_id")}

        eq_map: Dict[str, str] = {}
        emp_map: Dict[str, str] = {}
        try:
            if eq_ids:
                async for d in db.equipment_master.find(
                    {"id": {"$in": list(eq_ids)}},
                    {"_id": 0, "id": 1, "unit_number": 1, "make_model": 1},
                ):
                    parts = [d.get("unit_number"), d.get("make_model")]
                    eq_map[d["id"]] = " · ".join(p for p in parts if p) or d["id"]
            if emp_ids:
                async for d in db.employees.find(
                    {"id": {"$in": list(emp_ids)}},
                    {"_id": 0, "id": 1, "name": 1, "first_name": 1,
                     "last_name": 1, "employee_id": 1},
                ):
                    full = d.get("name") or " ".join(
                        p for p in [d.get("first_name"), d.get("last_name")] if p
                    )
                    emp_map[d["id"]] = full or d.get("employee_id") or d["id"]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[search] master-label enrichment failed: {e}")

        for g in groups:
            for row in g["rows"]:
                eq_label = eq_map.get(row.pop("_equipment_master_id", None) or "")
                emp_label = emp_map.get(row.pop("_employee_master_id", None) or "")
                if eq_label:
                    row["linked_equipment_label"] = eq_label
                if emp_label:
                    row["linked_employee_label"] = emp_label

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
        # iter440 · Phase 31.2 health-lock · same collection-name fix +
        # filename filter so quota-probe rows don't masquerade as
        # backups in the deploy-recovery view.
        recent_backups: List[Dict[str, Any]] = []
        try:
            async for r in db.backup_health.find(
                {"ok": True, "filename": {"$nin": [None, ""]}}, {"_id": 0},
            ).sort("ts", -1).limit(5):
                recent_backups.append({
                    "started_at": r.get("ts"),
                    "kind": r.get("mode") or "unknown",
                    "destination": "r2" if "r2" in (r.get("mode") or "") else "—",
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

    # ════════════════════════════════════════════════════════════════
    # iter338 · Admin Reference Lookup
    # ────────────────────────────────────────────────────────────────
    # Resolve a canonical reference (the same one shown on the iter335
    # /thank-you page, iter336 review headers, and iter337 PDFs) into
    # the matching record so leadership can drop on the right detail
    # page in one step. ADMIN-ONLY. No public lookup. No QR. No fuzzy
    # search. Exact-match across the canonical number fields for the 9
    # supported record kinds, then UUID fallback.
    LOOKUP_MAP = [
        # (collection, number_field, kind, frontend_path_template)
        ("incidents",                  "incident_number",   "incident",          "/admin/incidents/{id}"),
        ("daily_reports",              "report_number",     "daily-report",      "/admin/daily/{id}"),
        ("inspections",                "inspection_number", "inspection",        "/admin/inspections/{id}"),
        ("meetings",                   "meeting_number",    "meeting",           "/admin/meetings/{id}"),
        ("equipment_inspections",      "inspection_number", "equipment-inspection","/admin/equipment/{id}"),
        ("jhas",                       "jha_number",        "jha",               "/admin/jha-plans"),
        ("safety_equipment_issuances", "issuance_number",   "issuance",          "/safety/forms/equipment-issuance/{id}"),
        ("safety_training_records",    "training_number",   "training",          "/safety/forms/equipment-training/{id}"),
        ("field_leadership_records",   "record_number",     "field-leadership",  "/admin/field-leadership/{id}"),
    ]

    @router.get("/lookup", dependencies=[Depends(require_admin)])
    async def admin_lookup_ref(ref: str = Query(..., min_length=3, max_length=80)):
        # Normalize — operators may paste with surrounding whitespace or
        # lower-case the prefix when typing on mobile.
        needle = (ref or "").strip().upper()
        if not needle:
            raise HTTPException(400, "ref required")

        # 1. Exact match across canonical number fields. We also check
        #    `doc_id` per-collection for legacy records that still carry
        #    the older identifier.
        for coll_name, num_field, kind, path_tmpl in LOOKUP_MAP:
            coll = getattr(db, coll_name)
            doc = await coll.find_one(
                {"$or": [{num_field: needle}, {"doc_id": needle}]},
                {"_id": 0, "id": 1, num_field: 1, "doc_id": 1},
            )
            if doc:
                record_id = doc.get("id") or ""
                return {
                    "found": True,
                    "kind": kind,
                    "id": record_id,
                    "ref": needle,
                    "path": path_tmpl.format(id=record_id) if record_id else path_tmpl,
                }

        # 2. UUID fallback — operator pasted the record's raw `id`.
        for coll_name, _, kind, path_tmpl in LOOKUP_MAP:
            coll = getattr(db, coll_name)
            doc = await coll.find_one({"id": ref.strip()}, {"_id": 0, "id": 1})
            if doc:
                return {
                    "found": True,
                    "kind": kind,
                    "id": doc.get("id") or "",
                    "ref": ref.strip(),
                    "path": path_tmpl.format(id=doc.get("id") or ""),
                }

        return {"found": False, "ref": needle}

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
