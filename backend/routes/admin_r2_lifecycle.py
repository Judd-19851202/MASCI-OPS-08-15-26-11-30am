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
import re
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
from lib.r2_retention_authority import latest_retention_snapshot, retention_policy_payload

logger = logging.getLogger(__name__)


def _inventory_prefix_filter(prefix: Optional[str]) -> Dict[str, Any]:
    """Normalize the operator-supplied prefix filter.

    `r2_inventory.prefix` stores only the TOP-LEVEL segment (e.g. `backups`),
    so queries like `backups/` must normalize to the same truthful population
    as `backups`.

    For deeper paths (e.g. `backups/auto-90d/`), match on the full object key
    instead of the top-level prefix field.
    """
    if not prefix:
        return {}
    normalized = str(prefix).strip().lstrip("/").rstrip("/")
    if not normalized:
        return {}
    if "/" in normalized:
        return {"key": {"$regex": f"^{re.escape(normalized)}(?:/|$)"}}
    return {"prefix": normalized}


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
        retention = await latest_retention_snapshot(db)
        return {
            "inventory": inv,
            "classification": cls,
            "health": health,
            "retention": retention,
            "latest_inventory_run": await latest_run_id(db, "inventory"),
            "latest_classification_run": await latest_run_id(db, "classification"),
        }

    @router.get("/retention")
    async def retention(
        limit: int = Query(250, ge=1, le=2000),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        snapshot = await latest_retention_snapshot(db, limit=limit)
        return {
            **snapshot,
            "policy": retention_policy_payload(),
            "decisions": list(snapshot.get("decisions") or [])[:limit],
        }

    @router.get("/retention/policy")
    async def retention_policy(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        snapshot = await latest_retention_snapshot(db)
        return {
            "policy": retention_policy_payload(),
            "latest_generated_at": snapshot.get("generated_at"),
            "archive_count": snapshot.get("archive_count"),
            "survivors_by_tier": snapshot.get("survivors_by_tier"),
            "deleted_by_tier": snapshot.get("deleted_by_tier"),
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
        q: Dict[str, Any] = _inventory_prefix_filter(prefix)
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

    # ── Track 27.07 Phase 3 · Break-the-classifier sampling harness ──
    # Read-only. Never mutates R2 or Mongo. Returns adversarial samples
    # (100 largest orphan candidates + 500 random + per-prefix + all
    # zero-byte + all duplicate-ETag) so the operator can spot false
    # orphans BEFORE any manifest is approved.
    @router.get("/sample")
    async def classifier_sample(
        largest: int = Query(100, ge=0, le=1000),
        random_n: int = Query(500, ge=0, le=5000),
        per_prefix: int = Query(25, ge=0, le=200),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        from services.r2_lifecycle.classification import ALLOWED_FOR_DELETION  # noqa: PLC0415
        coll = db["r2_inventory"]
        orphan_filter = {"classification": {"$in": list(ALLOWED_FOR_DELETION)}}
        # 100 largest orphan candidates
        cursor_largest = coll.find(orphan_filter).sort("size_bytes", -1).limit(largest)
        largest_docs = await cursor_largest.to_list(largest) if largest else []
        # Random 500 orphan candidates via $sample
        random_docs: List[Dict[str, Any]] = []
        if random_n:
            random_docs = await coll.aggregate([
                {"$match": orphan_filter},
                {"$sample": {"size": random_n}},
            ]).to_list(random_n)
        # Per-prefix sample: top prefixes with N each
        top = await top_prefixes(db, 40)
        per_prefix_docs: List[Dict[str, Any]] = []
        if per_prefix:
            for p in top:
                px = p.get("prefix") or ""
                if not px:
                    continue
                docs = await coll.find({
                    **orphan_filter, "key": {"$regex": f"^{px}"},
                }).limit(per_prefix).to_list(per_prefix)
                per_prefix_docs.extend(docs)
        # All zero-byte orphans
        zero = await coll.find({**orphan_filter, "size_bytes": 0}).to_list(2000)
        # Duplicate-ETag candidates (best-effort — group by etag with >1 count)
        dup_agg = await coll.aggregate([
            {"$match": orphan_filter},
            {"$group": {"_id": "$etag", "n": {"$sum": 1}, "keys": {"$push": "$key"}}},
            {"$match": {"n": {"$gt": 1}}},
            {"$limit": 500},
        ]).to_list(500)

        def _slim(d: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "key": d.get("key"),
                "size_bytes": d.get("size_bytes"),
                "size_mb": round((d.get("size_bytes") or 0) / (1024 * 1024), 3),
                "etag": d.get("etag"),
                "last_modified": (d.get("last_modified").isoformat()
                                  if hasattr(d.get("last_modified"), "isoformat")
                                  else d.get("last_modified")),
                "classification": d.get("classification"),
                "reason_code": d.get("reason_code"),
                "reference_count": d.get("reference_count", 0),
                "project_number": d.get("project_number"),
            }
        return {
            "harness_version": "27.07.phase3.v1",
            "counts": {
                "largest": len(largest_docs),
                "random": len(random_docs),
                "per_prefix": len(per_prefix_docs),
                "zero_byte": len(zero),
                "duplicate_etag_groups": len(dup_agg),
            },
            "largest": [_slim(d) for d in largest_docs],
            "random_sample": [_slim(d) for d in random_docs][:random_n],
            "per_prefix_sample": [_slim(d) for d in per_prefix_docs],
            "zero_byte_all": [_slim(d) for d in zero],
            "duplicate_etag_groups": [
                {"etag": g["_id"], "count": g["n"], "keys_sample": g["keys"][:5]}
                for g in dup_agg
            ],
            "invariant": (
                "Every sampled row must be VERIFIED_ORPHAN. Any operator "
                "spot-check that finds a live reference invalidates the "
                "entire candidate set — re-register the reference source, "
                "rerun scan/references/classify, then re-sample."
            ),
        }

    # ── Track 27.07 Phase 6 · Logical (non-destructive) quarantine ──
    # This endpoint marks approved orphan keys in the canonical
    # `r2_inventory` collection with a `quarantine` sub-document.
    # It does NOT copy, move, or delete anything in R2. The physical
    # R2 objects remain untouched. This is the "logical quarantine
    # only" option from the Track 27.07 Phase 6 spec. A separate,
    # explicitly-approved future track authorizes any physical move.
    @router.post("/quarantine")
    async def quarantine_mark(
        manifest_id: str = Query(..., description="Dry-run manifest ID (audit reference)."),
        holding_hours: int = Query(168, ge=24, le=720, description="Holding window (24-720h, default 168h=7d)."),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        from services.r2_lifecycle.classification import ALLOWED_FOR_DELETION  # noqa: PLC0415
        from datetime import datetime, timezone, timedelta  # noqa: PLC0415
        coll = db["r2_inventory"]
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=holding_hours)
        # Only VERIFIED_ORPHAN, only objects not already quarantined.
        query = {
            "classification": {"$in": list(ALLOWED_FOR_DELETION)},
            "quarantine": {"$exists": False},
        }
        candidates = await coll.find(query).to_list(200000)
        if not candidates:
            return {
                "ok": True, "manifest_id": manifest_id,
                "quarantined": 0, "reason": "No eligible VERIFIED_ORPHAN candidates.",
                "hard_delete_status": "DISABLED",
            }
        result = await coll.update_many(query, {"$set": {"quarantine": {
            "manifest_id": manifest_id,
            "state": "HOLDING",
            "quarantined_at": now,
            "holding_until": deadline,
            "release_authorized": False,
        }}})
        return {
            "ok": True, "manifest_id": manifest_id,
            "quarantined": result.modified_count,
            "eligible_candidates": len(candidates),
            "holding_hours": holding_hours,
            "holding_until": deadline.isoformat(),
            "physical_r2_state": "UNTOUCHED — this is a logical mark only.",
            "hard_delete_status": "DISABLED",
        }

    @router.get("/quarantine")
    async def quarantine_list(
        _: bool = Depends(require_admin_strict_dep),
        limit: int = Query(500, ge=1, le=5000),
    ) -> Dict[str, Any]:
        coll = db["r2_inventory"]
        rows = await coll.find({"quarantine.state": "HOLDING"}).limit(limit).to_list(limit)
        total_bytes = sum(int(r.get("size_bytes") or 0) for r in rows)
        return {
            "count": len(rows),
            "total_bytes": total_bytes,
            "total_gb": round(total_bytes / (1024 ** 3), 3),
            "hard_delete_status": "DISABLED",
            "rows": [{
                "key": r.get("key"),
                "size_bytes": r.get("size_bytes"),
                "classification": r.get("classification"),
                "quarantine": r.get("quarantine"),
            } for r in rows],
        }

    @router.post("/quarantine/cancel")
    async def quarantine_cancel(
        manifest_id: str = Query(..., description="Cancel all quarantine marks for this manifest."),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        coll = db["r2_inventory"]
        result = await coll.update_many(
            {"quarantine.manifest_id": manifest_id},
            {"$unset": {"quarantine": ""}},
        )
        return {"ok": True, "manifest_id": manifest_id, "released": result.modified_count}

    return router


def _reference_sources_snapshot() -> List[Dict[str, Any]]:
    """Local helper to keep the router file self-contained for typing."""
    from services.r2_lifecycle.references import REFERENCE_SOURCES  # noqa: PLC0415
    return [src.as_dict() for src in REFERENCE_SOURCES]
