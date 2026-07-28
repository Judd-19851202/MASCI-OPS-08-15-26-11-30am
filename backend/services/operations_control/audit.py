"""TRACK 24.17 · OCC append-only audit log.

Every OCC action — dry-run or apply — writes a row to
``db.operations_audit`` so a super-admin can prove exactly what
happened, who did it, and what changed.

Rows are immutable by convention (no update/delete endpoint is
exposed). If the platform ever needs a retention policy, a future
track can add a maintenance job — but the OCC never rewrites
history.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

COLLECTION = "operations_audit"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_indexes(db) -> None:
    coll = db[COLLECTION]
    await coll.create_index([("ts", -1)])
    await coll.create_index([("operation_id", 1), ("ts", -1)])
    await coll.create_index([("actor_id", 1), ("ts", -1)])
    await coll.create_index([("mode", 1), ("ts", -1)])
    await coll.create_index([("dry_run_id", 1), ("ts", -1)])
    await coll.create_index("action_id", unique=True)


async def write(db, *, operation_id: str, mode: str, actor: Dict[str, Any],
                risk: str, result: Dict[str, Any],
                before: Optional[Dict[str, Any]] = None,
                after: Optional[Dict[str, Any]] = None,
                confirmation_phrase: Optional[str] = None,
                dry_run_id: Optional[str] = None,
                reason: Optional[str] = None,
                error: Optional[str] = None) -> str:
    """Write one audit row. Returns the assigned ``action_id``."""
    action_id = str(uuid.uuid4())
    row = {
        "action_id": action_id,
        "operation_id": operation_id,
        "mode": mode,          # "dry_run" | "apply" | "status"
        "risk": risk,
        "actor_id": actor.get("id") or actor.get("email") or "unknown",
        "actor_email": actor.get("email") or "",
        "actor_role": actor.get("role") or "admin",
        "ts": _now_iso(),
        "confirmation_phrase_used": bool(confirmation_phrase),
        "dry_run_id": dry_run_id,
        "reason": (reason or "")[:500],
        "before": before or {},
        "after": after or {},
        "result": result or {},
        "error": (error or "")[:2000],
    }
    await db[COLLECTION].insert_one(row)
    return action_id


async def list_recent(db, *, limit: int = 100,
                      operation_id: Optional[str] = None,
                      actor_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if operation_id:
        q["operation_id"] = operation_id
    if actor_id:
        q["actor_id"] = actor_id
    cursor = db[COLLECTION].find(q, {"_id": 0}).sort("ts", -1).limit(limit)
    return [row async for row in cursor]


async def get(db, action_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION].find_one(
        {"action_id": action_id}, {"_id": 0},
    )


async def latest_for_operation(
    db,
    *,
    operation_id: str,
    mode: Optional[str] = None,
    dry_run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    q: Dict[str, Any] = {"operation_id": operation_id}
    if mode:
        q["mode"] = mode
    if dry_run_id:
        q["dry_run_id"] = dry_run_id
    return await db[COLLECTION].find_one(q, {"_id": 0}, sort=[("ts", -1)])
