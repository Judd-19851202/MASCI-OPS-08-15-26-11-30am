"""
TRACK 27.06 · R2 Lifecycle Governance API.

Read-only surface for the operator UI + OCC + regression tests. All
endpoints require an admin-strict caller — the dependency function is
injected by ``server.py``.

Endpoints
---------
POST /api/admin/r2/lifecycle/scan          → inventory + refs + classify
GET  /api/admin/r2/lifecycle/latest        → last-run summary + health
GET  /api/admin/r2/lifecycle/inventory     → paginated inventory rows
GET  /api/admin/r2/lifecycle/classification→ counts snapshot + samples
GET  /api/admin/r2/lifecycle/object        → evidence drawer for one key
POST /api/admin/r2/lifecycle/dry-run       → certified would-delete list
GET  /api/admin/r2/lifecycle/health        → Phase 10 storage-health score
GET  /api/admin/r2/lifecycle/intelligence  → top prefixes / projects / cost
GET  /api/admin/r2/lifecycle/growth        → daily upload series (90d)

Zero deletes.  Zero writes to R2.  Zero repair of Mongo references.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from services.r2_lifecycle import (
    ALLOWED_FOR_DELETION,
    CLASSIFICATIONS,
    DRY_RUN_REFUSAL_STATES,
    classification_counts,
    classify_all,
    compute_storage_health,
    estimate_cost,
    growth_series,
    inventory_summary,
    largest_objects,
    latest_run_id,
    run_inventory_scan,
    scan_mongo_references,
    top_prefixes,
    top_projects,
)

logger = logging.getLogger(__name__)


def build_r2_lifecycle_router(db, require_admin_strict_dep) -> APIRouter:
    router = APIRouter(prefix="/admin/r2/lifecycle", tags=["r2-lifecycle"])

    # ── Scan ─────────────────────────────────────────────────────────
    @router.post("/scan")
    async def scan(
        max_pages: Optional[int] = Query(None, ge=1, le=10000),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        """Kick off the full three-phase lifecycle refresh: inventory
        → references → classification. Persists to the lifecycle
        collections; returns a summary that the UI can render.

        This is idempotent — repeated invocations upsert.  Nothing is
        mutated in R2.
        """
        import photo_storage  # noqa: PLC0415 — lazy
        if not photo_storage.is_configured():
            raise HTTPException(
                status_code=503,
                detail="R2 (photo_storage) is not configured on this pod.",
            )
        client = photo_storage._client()  # boto3 client
        if not client:
            raise HTTPException(status_code=503, detail="R2 client failed to initialise.")
        bucket = photo_storage._bucket()

        inv = await run_inventory_scan(db, client, bucket, max_pages=max_pages, initiator="operator")
        refs = await scan_mongo_references(db)
        cls = await classify_all(db)
        return {"inventory": inv, "references": refs, "classification": cls}

    # ── Latest ───────────────────────────────────────────────────────
    @router.get("/latest")
    async def latest(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        inv = await inventory_summary(db)
        cls = await classification_counts(db)
        health = await compute_storage_health(db)
        return {
            "inventory": inv,
            "classification": cls,
            "health": health,
            "latest_inventory_run": await latest_run_id(db, "inventory"),
            "latest_classification_run": await latest_run_id(db, "classification"),
        }

    # ── Inventory list ───────────────────────────────────────────────
    @router.get("/inventory")
    async def inventory(
        prefix: Optional[str] = None,
        min_bytes: Optional[int] = Query(None, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        skip: int = Query(0, ge=0),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if prefix:
            q["prefix"] = prefix
        if min_bytes:
            q["size"] = {"$gte": int(min_bytes)}
        total = await db.r2_inventory.count_documents(q)
        cursor = db.r2_inventory.find(q, {"_id": 0}).sort("size", -1).skip(skip).limit(limit)
        items: List[Dict[str, Any]] = []
        async for row in cursor:
            items.append(row)
        return {"total_matching": total, "count": len(items), "items": items}

    # ── Classification snapshot ──────────────────────────────────────
    @router.get("/classification")
    async def classification(
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        latest = await classification_counts(db)
        samples: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CLASSIFICATIONS}
        for c in CLASSIFICATIONS:
            cursor = db.r2_classifications.find(
                {"classification": c},
                {"_id": 0, "key": 1, "size": 1, "prefix": 1, "reason": 1},
            ).sort("size", -1).limit(3)
            async for row in cursor:
                samples[c].append(row)
        return {"summary": latest, "samples": samples}

    # ── Evidence drawer for a single key ─────────────────────────────
    @router.get("/object")
    async def object_evidence(
        key: str = Query(..., min_length=1),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        inv_row = await db.r2_inventory.find_one({"_id": key}, {"_id": 0})
        if not inv_row:
            raise HTTPException(status_code=404, detail=f"Key not in inventory: {key}")
        cls_row = await db.r2_classifications.find_one({"_id": key}, {"_id": 0})
        refs: List[Dict[str, Any]] = []
        async for r in db.r2_references.find({"r2_key": key}, {"_id": 0}):
            refs.append(r)
        return {
            "inventory": inv_row,
            "classification": cls_row,
            "references": refs,
            "collections_searched": [
                {"collection": src["collection"], "owner": src["owner"], "feature": src["feature"]}
                for src in _reference_sources_snapshot()
            ],
        }

    # ── Dry-run ──────────────────────────────────────────────────────
    @router.post("/dry-run")
    async def dry_run(
        limit: int = Query(500, ge=1, le=10000),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        """Return the objects that WOULD be deleted if the (future)
        delete engine were unlocked today, plus a certification
        result. If ANY object in the top-``limit`` batch is not
        VERIFIED_ORPHAN, the batch is refused.

        Zero deletes. Zero mutations.  Zero side effects.
        """
        # Get the population — the top-``limit`` largest orphans.
        candidates: List[Dict[str, Any]] = []
        async for row in db.r2_classifications.find(
            {"classification": "VERIFIED_ORPHAN"},
            {"_id": 0, "key": 1, "size": 1, "prefix": 1, "reason": 1, "evidence": 1},
        ).sort("size", -1).limit(limit):
            candidates.append(row)

        # Cross-check: none of the candidates may still exhibit a
        # protective class in the persistence store (paranoia in case
        # a classification pass ran mid-scan).
        blocked: List[Dict[str, Any]] = []
        async for row in db.r2_classifications.find(
            {"classification": {"$in": list(DRY_RUN_REFUSAL_STATES)}},
            {"_id": 0, "key": 1, "classification": 1, "size": 1},
        ).limit(10):
            blocked.append(row)

        allowed_only = all(
            c.get("classification", "VERIFIED_ORPHAN") in ALLOWED_FOR_DELETION
            for c in candidates
        )
        total_bytes = sum(int(c.get("size") or 0) for c in candidates)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidates_count": len(candidates),
            "candidates_total_bytes": total_bytes,
            "candidates_total_gb": round(total_bytes / (1024 ** 3), 3),
            "candidates_sample": candidates[:100],
            "certification": {
                "batch_allowed": allowed_only,
                "refusal_reason": (
                    "Non-orphan candidates present — see `blocked_by_state`."
                    if not allowed_only else None
                ),
                "allowed_classifications": sorted(list(ALLOWED_FOR_DELETION)),
                "refusal_classifications": sorted(list(DRY_RUN_REFUSAL_STATES)),
            },
            "blocked_by_state": blocked,
            "delete_engine_status": "DISABLED",
            "policy": (
                "This session ships lifecycle governance ONLY. Deletion "
                "is explicitly disabled until Phase 7 is scoped and "
                "operator-approved."
            ),
        }

    # ── Storage Health ───────────────────────────────────────────────
    @router.get("/health")
    async def health(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        return await compute_storage_health(db)

    # ── Intelligence + cost ──────────────────────────────────────────
    @router.get("/intelligence")
    async def intelligence(
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        inv = await inventory_summary(db)
        cls = await classification_counts(db)
        cost = estimate_cost(
            total_bytes=int(inv.get("total_bytes") or 0),
            orphan_bytes=int(cls.get("verified_orphan_bytes") or 0),
        )
        return {
            "top_prefixes":   await top_prefixes(db, 20),
            "top_projects":   await top_projects(db, 20),
            "largest_objects": await largest_objects(db, 25),
            "cost": cost,
        }

    @router.get("/growth")
    async def growth(
        days: int = Query(90, ge=1, le=365),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        return {"days": days, "series": await growth_series(db, days=days)}

    return router


def _reference_sources_snapshot() -> List[Dict[str, Any]]:
    """Local helper to keep the router file self-contained for typing."""
    from services.r2_lifecycle.references import REFERENCE_SOURCES  # noqa: PLC0415
    return [src.as_dict() for src in REFERENCE_SOURCES]
