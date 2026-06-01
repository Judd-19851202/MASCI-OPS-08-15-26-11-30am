"""routes/scheduler_runs_admin.py — iter445 · Sprint · Scheduler Hardening.

Admin-only read endpoints over the ``scheduler_runs`` audit collection.

Operator value
--------------
Answers the questions the OMEGA Batch demands:
  1. Why did this digest send?
  2. Which pod sent it?
  3. When did it send?
  4. Who received it?
  5. Was a duplicate prevented?

All answers are queryable here without admin DB access.
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from lib.scheduler_runs import SCHEDULER_RUNS_COLLECTION


def build_scheduler_runs_admin_router(db, require_admin) -> APIRouter:
    router = APIRouter(prefix="/api/admin/scheduler-runs", tags=["admin · scheduler runs"])

    @router.get("")
    async def list_scheduler_runs(
        scheduler: Optional[str] = Query(
            default=None,
            description="Filter to one scheduler (po_digest · safety_digest · operator_digest)",
        ),
        limit: int = Query(default=50, ge=1, le=500),
        _admin=Depends(require_admin),
    ):
        """Return recent scheduler runs, newest first."""
        q: dict = {}
        if scheduler:
            q["scheduler"] = scheduler
        cursor = (
            db[SCHEDULER_RUNS_COLLECTION]
            .find(q, {"_id": 0})
            .sort("started_at", -1)
            .limit(int(limit))
        )
        items: List[dict] = []
        async for doc in cursor:
            # Normalize datetimes for JSON serialization
            for k in ("started_at", "finished_at", "last_dedup_at", "ttl_at"):
                v = doc.get(k)
                if v is not None and hasattr(v, "isoformat"):
                    doc[k] = v.isoformat()
            # Same for dedup_attempt_log entries
            for ev in doc.get("dedup_attempt_log") or []:
                ts = ev.get("ts")
                if ts is not None and hasattr(ts, "isoformat"):
                    ev["ts"] = ts.isoformat()
            items.append(doc)
        # Headline counts for the UI summary card
        total = await db[SCHEDULER_RUNS_COLLECTION].count_documents(q)
        dedup_total = await db[SCHEDULER_RUNS_COLLECTION].count_documents(
            {**q, "dedup_attempts": {"$gt": 0}}
        )
        failed_total = await db[SCHEDULER_RUNS_COLLECTION].count_documents(
            {**q, "status": "failed"}
        )
        return {
            "items": items,
            "total": total,
            "dedup_total": dedup_total,
            "failed_total": failed_total,
        }

    @router.get("/{scheduler}/{slot_key:path}")
    async def get_scheduler_run(
        scheduler: str,
        slot_key: str,
        _admin=Depends(require_admin),
    ):
        """Detail for one specific (scheduler, slot_key) execution."""
        doc = await db[SCHEDULER_RUNS_COLLECTION].find_one(
            {"scheduler": scheduler, "slot_key": slot_key},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="scheduler run not found")
        for k in ("started_at", "finished_at", "last_dedup_at", "ttl_at"):
            v = doc.get(k)
            if v is not None and hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        for ev in doc.get("dedup_attempt_log") or []:
            ts = ev.get("ts")
            if ts is not None and hasattr(ts, "isoformat"):
                ev["ts"] = ts.isoformat()
        return doc

    return router


__all__ = ["build_scheduler_runs_admin_router"]
