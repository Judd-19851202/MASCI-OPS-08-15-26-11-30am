from __future__ import annotations

import os
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pymongo.errors import DuplicateKeyError

BACKUP_JOBS_COLLECTION = "backup_jobs"
BACKUP_JOB_TTL_DAYS = 120
BACKUP_JOB_KIND_COMPLETE_R2 = "complete-r2"
BACKUP_JOB_KIND_RESTORE_DRILL = "restore-drill"
BACKUP_JOB_KIND_RESTORE_IMPORT = "restore-import"


def backup_now() -> datetime:
    return datetime.now(timezone.utc)


def backup_owner_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def backup_slot_key_for_hour(moment: datetime) -> str:
    dt = moment.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return dt.isoformat()


def backup_slot_key_for_day(moment: datetime) -> str:
    dt = moment.astimezone(timezone.utc)
    return dt.date().isoformat()


async def ensure_backup_runtime_indexes(db: Any) -> None:
    coll = db[BACKUP_JOBS_COLLECTION]
    await coll.create_index([("kind", 1), ("slot_key", 1)], unique=True, name="ix_backup_jobs_kind_slot")
    await coll.create_index([("job_type", 1), ("state", 1)], name="ix_backup_jobs_type_state")
    await coll.create_index("ttl_at", expireAfterSeconds=0, name="ix_backup_jobs_ttl")
    await coll.create_index("updated_at", name="ix_backup_jobs_updated")


async def claim_backup_job(
    db: Any,
    *,
    job_type: str,
    kind: str,
    slot_key: str,
    trigger: str,
    owner_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    now = backup_now()
    doc = {
        "job_id": f"bjob-{uuid.uuid4().hex}",
        "job_type": job_type,
        "kind": kind,
        "slot_key": slot_key,
        "trigger": trigger,
        "owner_id": owner_id or backup_owner_id(),
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "state": "queued",
        "attempt_count": 0,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "heartbeat_at": now.isoformat(),
        "metadata": metadata or {},
        "ttl_at": now + timedelta(days=BACKUP_JOB_TTL_DAYS),
    }
    try:
        await db[BACKUP_JOBS_COLLECTION].insert_one(dict(doc))
        return doc
    except DuplicateKeyError:
        return None


async def start_backup_job(db: Any, job_id: str) -> None:
    now = backup_now().isoformat()
    await db[BACKUP_JOBS_COLLECTION].update_one(
        {"job_id": job_id},
        {"$set": {"state": "running", "started_at": now, "updated_at": now, "heartbeat_at": now}, "$inc": {"attempt_count": 1}},
    )


async def heartbeat_backup_job(db: Any, job_id: str, *, extra: Optional[Dict[str, Any]] = None) -> None:
    payload: Dict[str, Any] = {
        "updated_at": backup_now().isoformat(),
        "heartbeat_at": backup_now().isoformat(),
    }
    if extra:
        payload.update(extra)
    await db[BACKUP_JOBS_COLLECTION].update_one({"job_id": job_id}, {"$set": payload})


async def complete_backup_job(db: Any, job_id: str, *, outcome: str, result: Optional[Dict[str, Any]] = None, state: str = "completed") -> None:
    now = backup_now()
    payload: Dict[str, Any] = {
        "state": state,
        "outcome": outcome,
        "updated_at": now.isoformat(),
        "heartbeat_at": now.isoformat(),
        "completed_at": now.isoformat(),
        "ttl_at": now + timedelta(days=BACKUP_JOB_TTL_DAYS),
    }
    if result is not None:
        payload["result"] = result
    await db[BACKUP_JOBS_COLLECTION].update_one({"job_id": job_id}, {"$set": payload})


async def fail_backup_job(db: Any, job_id: str, *, error: str, result: Optional[Dict[str, Any]] = None, state: str = "failed") -> None:
    payload = dict(result or {})
    payload.setdefault("error", error[:1500])
    await complete_backup_job(db, job_id, outcome="failed", result=payload, state=state)


async def list_backup_jobs(db: Any, *, kind: Optional[str] = None, limit: int = 20) -> list[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if kind:
        q["kind"] = kind
    cursor = db[BACKUP_JOBS_COLLECTION].find(q, {"_id": 0}).sort("created_at", -1).limit(int(limit))
    return [row async for row in cursor]


async def get_active_backup_jobs(db: Any) -> list[Dict[str, Any]]:
    cursor = db[BACKUP_JOBS_COLLECTION].find({"state": {"$in": ["queued", "running"]}}, {"_id": 0}).sort("created_at", -1)
    return [row async for row in cursor]


async def mark_stale_backup_jobs(db: Any, *, stale_before_iso: str) -> int:
    result = await db[BACKUP_JOBS_COLLECTION].update_many(
        {
            "state": {"$in": ["queued", "running"]},
            "heartbeat_at": {"$lt": stale_before_iso},
        },
        {"$set": {"state": "stale", "updated_at": backup_now().isoformat(), "failure_reason": "stale_job_recovered"}},
    )
    return int(getattr(result, "modified_count", 0) or 0)


def classify_backup_overlap(active_jobs: list[Dict[str, Any]]) -> Dict[str, Any]:
    backups = [j for j in active_jobs if j.get("kind") == BACKUP_JOB_KIND_COMPLETE_R2]
    restores = [j for j in active_jobs if j.get("kind") in {BACKUP_JOB_KIND_RESTORE_DRILL, BACKUP_JOB_KIND_RESTORE_IMPORT}]
    return {
        "backup_active": bool(backups),
        "restore_active": bool(restores),
        "active_backups": backups,
        "active_restores": restores,
        "overlap_blocked": bool(backups and restores),
    }


__all__ = [
    "BACKUP_JOB_KIND_COMPLETE_R2",
    "BACKUP_JOB_KIND_RESTORE_DRILL",
    "BACKUP_JOB_KIND_RESTORE_IMPORT",
    "backup_owner_id",
    "backup_slot_key_for_hour",
    "backup_slot_key_for_day",
    "ensure_backup_runtime_indexes",
    "claim_backup_job",
    "start_backup_job",
    "heartbeat_backup_job",
    "complete_backup_job",
    "fail_backup_job",
    "list_backup_jobs",
    "get_active_backup_jobs",
    "mark_stale_backup_jobs",
    "classify_backup_overlap",
]