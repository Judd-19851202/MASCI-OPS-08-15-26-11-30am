"""TRACK 15.79 · Deployment ledger persistence.

Append-only Mongo collection (``deployment_decisions``) that records
every Trust Gate invocation. Designed so the operator can audit
*"on date X, was the platform deploy-ready? what blocked it?"*
without parsing CI logs.

Documents are **immutable** — there is no UPDATE/DELETE surface
exposed. The endpoint only writes via ``insert_one`` and a
``$setOnInsert``-only TTL index housekeeping path (year-old
records expire automatically).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request


COLLECTION = "deployment_decisions"


async def ensure_indexes(db) -> None:
    try:
        await db[COLLECTION].create_index([("ts", -1)])
        await db[COLLECTION].create_index([("commit", 1), ("ts", -1)])
        await db[COLLECTION].create_index([("decision", 1), ("ts", -1)])
        # 365-day TTL on the ts_dt field (immutable for the operator's
        # forensic window; older entries auto-expire to keep the
        # collection small).
        await db[COLLECTION].create_index(
            "ts_dt", expireAfterSeconds=365 * 24 * 3600
        )
    except Exception:
        pass


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.post("/api/admin/deployment-readiness/snapshot")
    async def append_snapshot(
        request: Request,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Append one deployment decision to the immutable ledger.

        Body (all fields optional except ``decision``)::

            {
              "decision":  "pass" | "fail",
              "exit_code": int,
              "commit":    "abc1234",
              "branch":    "main",
              "environment": "preview" | "production",
              "operator":  "jaymn.judd@mascigc.com",
              "duration_ms": 38234,
              "trust_score": 40,
              "trust_band":  "red",
              "blocking_count": 0,
              "advisory_count": 3,
              "regression_count": 99,
              "blocking_ids": ["..."]
            }
        """
        await ensure_indexes(db)
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "invalid JSON body")
        decision = (body.get("decision") or "").lower()
        if decision not in {"pass", "fail"}:
            raise HTTPException(
                400, "decision must be exactly 'pass' or 'fail'"
            )
        now = datetime.now(timezone.utc)
        doc: Dict[str, Any] = {
            "ts": now.isoformat(),
            "ts_dt": now,
            "decision": decision,
            "exit_code": int(body.get("exit_code") or 0),
            "commit": str(body.get("commit") or "")[:40],
            "branch": str(body.get("branch") or "")[:64],
            "environment": str(body.get("environment") or "")[:32],
            "operator": str(body.get("operator") or "")[:128],
            "duration_ms": int(body.get("duration_ms") or 0),
            "trust_score": int(body.get("trust_score") or 0),
            "trust_band": str(body.get("trust_band") or "")[:16],
            "blocking_count": int(body.get("blocking_count") or 0),
            "advisory_count": int(body.get("advisory_count") or 0),
            "regression_count": int(body.get("regression_count") or 0),
            "blocking_ids": (body.get("blocking_ids") or [])[:32],
        }
        await db[COLLECTION].insert_one(doc)
        return {"ok": True, "ts": doc["ts"]}

    @router.get("/api/admin/deployment-readiness/history")
    async def history(
        limit: int = 50,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Read-only view of the deployment ledger (newest first)."""
        limit = max(1, min(int(limit or 50), 500))
        rows = []
        cursor = db[COLLECTION].find(
            {}, {"_id": 0, "ts_dt": 0}, sort=[("ts", -1)], limit=limit,
        )
        async for r in cursor:
            rows.append(r)
        total = await db[COLLECTION].count_documents({})
        pass_count = await db[COLLECTION].count_documents({"decision": "pass"})
        fail_count = await db[COLLECTION].count_documents({"decision": "fail"})
        return {
            "count": len(rows),
            "total_ever": total,
            "pass_total": pass_count,
            "fail_total": fail_count,
            "events": rows,
        }

    return router
