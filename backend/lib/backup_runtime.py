from __future__ import annotations

import os
import socket
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pymongo.errors import DuplicateKeyError

BACKUP_JOBS_COLLECTION = "backup_jobs"
BACKUP_JOB_TTL_DAYS = 120
BACKUP_JOB_KIND_COMPLETE_R2 = "complete-r2"
BACKUP_JOB_KIND_RESTORE_DRILL = "restore-drill"
BACKUP_JOB_KIND_RESTORE_IMPORT = "restore-import"
RESTORE_CERT_OPERATION_CLASS = "restore-certification"
RESTORE_CERT_DEFAULT_LEASE_MINUTES = 45


class BackupJobOwnershipLost(RuntimeError):
    pass


@dataclass
class BackupJobLease:
    job_id: str
    owner_id: str
    owner_token: str


def backup_now() -> datetime:
    return datetime.now(timezone.utc)


def backup_owner_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def backup_run_id() -> str:
    return f"brun-{uuid.uuid4().hex}"


def backup_slot_key_for_hour(moment: datetime) -> str:
    dt = moment.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return dt.isoformat()


def backup_slot_key_for_day(moment: datetime) -> str:
    dt = moment.astimezone(timezone.utc)
    return dt.date().isoformat()


def restore_certification_guard_slot(environment: str) -> str:
    return f"{RESTORE_CERT_OPERATION_CLASS}::{str(environment or 'unknown').strip().lower()}"


def restore_certification_terminal_slot(environment: str, job_id: str, state: str) -> str:
    return f"{restore_certification_guard_slot(environment)}::{state}::{job_id}"


def restore_certification_lease_minutes(env: Optional[Dict[str, Any]] = None) -> int:
    raw = None
    if env:
        raw = env.get("RESTORE_CERT_LEASE_MINUTES")
    try:
        val = int(str(raw or RESTORE_CERT_DEFAULT_LEASE_MINUTES))
    except Exception:
        val = RESTORE_CERT_DEFAULT_LEASE_MINUTES
    return max(15, min(val, 180))


def restore_certification_lease_expires_at(*, now: Optional[datetime] = None, lease_minutes: int = RESTORE_CERT_DEFAULT_LEASE_MINUTES) -> str:
    moment = now or backup_now()
    return (moment + timedelta(minutes=int(lease_minutes))).isoformat()


def is_restore_certification_stale(row: Optional[Dict[str, Any]], *, now: Optional[datetime] = None, lease_minutes: int = RESTORE_CERT_DEFAULT_LEASE_MINUTES) -> bool:
    if not row:
        return False
    if str(row.get("state") or "").lower() not in {"queued", "running", "downloading"}:
        return False
    current = now or backup_now()
    lease_exp = row.get("lease_expires_at")
    heartbeat = row.get("heartbeat_at")
    try:
        lease_dt = datetime.fromisoformat(str(lease_exp).replace("Z", "+00:00")) if lease_exp else None
    except Exception:
        lease_dt = None
    try:
        heartbeat_dt = datetime.fromisoformat(str(heartbeat).replace("Z", "+00:00")) if heartbeat else None
    except Exception:
        heartbeat_dt = None
    if lease_dt and current <= lease_dt:
        return False
    if not heartbeat_dt:
        return True
    return current - heartbeat_dt > timedelta(minutes=max(int(lease_minutes), 15))


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
        "backup_run_id": backup_run_id(),
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
    owner_token = uuid.uuid4().hex
    await db[BACKUP_JOBS_COLLECTION].update_one(
        {"job_id": job_id},
        {
            "$set": {
                "state": "running",
                "started_at": now,
                "updated_at": now,
                "heartbeat_at": now,
                "owner_token": owner_token,
                "ownership_revoked": False,
                "heartbeat_failure": None,
            },
            "$inc": {"attempt_count": 1, "lease_epoch": 1},
        },
    )
    row = await db[BACKUP_JOBS_COLLECTION].find_one({"job_id": job_id}, {"_id": 0, "owner_id": 1}) or {}
    return BackupJobLease(job_id=job_id, owner_id=str(row.get("owner_id") or ""), owner_token=owner_token)


async def heartbeat_backup_job(db: Any, job_id: str, *, owner_token: str, extra: Optional[Dict[str, Any]] = None) -> None:
    payload: Dict[str, Any] = {
        "updated_at": backup_now().isoformat(),
        "heartbeat_at": backup_now().isoformat(),
    }
    if extra:
        payload.update(extra)
    result = await db[BACKUP_JOBS_COLLECTION].update_one(
        {
            "job_id": job_id,
            "state": "running",
            "owner_token": owner_token,
            "ownership_revoked": {"$ne": True},
        },
        {"$set": payload},
    )
    if int(getattr(result, "modified_count", 0) or 0) == 0:
        raise BackupJobOwnershipLost(f"backup job ownership lost: {job_id}")


async def record_backup_job_heartbeat_failure(db: Any, job_id: str, *, owner_token: str, error: str) -> None:
    await db[BACKUP_JOBS_COLLECTION].update_one(
        {"job_id": job_id, "owner_token": owner_token},
        {
            "$set": {
                "updated_at": backup_now().isoformat(),
                "heartbeat_failure": error[:500],
                "heartbeat_failure_at": backup_now().isoformat(),
            },
            "$inc": {"heartbeat_failure_count": 1},
        },
    )


async def assert_backup_job_ownership(db: Any, job_id: str, *, owner_token: str) -> None:
    row = await db[BACKUP_JOBS_COLLECTION].find_one(
        {
            "job_id": job_id,
            "state": "running",
            "owner_token": owner_token,
            "ownership_revoked": {"$ne": True},
        },
        {"_id": 0, "job_id": 1},
    )
    if not row:
        raise BackupJobOwnershipLost(f"backup job ownership lost: {job_id}")


async def complete_backup_job(db: Any, job_id: str, *, outcome: str, result: Optional[Dict[str, Any]] = None, state: str = "completed", owner_token: Optional[str] = None) -> None:
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
    query: Dict[str, Any] = {"job_id": job_id}
    if owner_token is not None:
        query.update({"owner_token": owner_token, "ownership_revoked": {"$ne": True}})
    result_doc = await db[BACKUP_JOBS_COLLECTION].update_one(query, {"$set": payload})
    if owner_token is not None and int(getattr(result_doc, "modified_count", 0) or 0) == 0:
        raise BackupJobOwnershipLost(f"backup job ownership lost: {job_id}")


async def fail_backup_job(db: Any, job_id: str, *, error: str, result: Optional[Dict[str, Any]] = None, state: str = "failed", owner_token: Optional[str] = None) -> None:
    payload = dict(result or {})
    payload.setdefault("error", error[:1500])
    await complete_backup_job(db, job_id, outcome="failed", result=payload, state=state, owner_token=owner_token)


async def list_backup_jobs(db: Any, *, kind: Optional[str] = None, limit: int = 20) -> list[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if kind:
        q["kind"] = kind
    cursor = db[BACKUP_JOBS_COLLECTION].find(q, {"_id": 0}).sort("created_at", -1).limit(int(limit))
    return [row async for row in cursor]


async def get_active_backup_jobs(db: Any) -> list[Dict[str, Any]]:
    cursor = db[BACKUP_JOBS_COLLECTION].find({"state": {"$in": ["queued", "running"]}}, {"_id": 0}).sort("created_at", -1)
    return [row async for row in cursor]


async def list_stale_backup_jobs(db: Any, *, limit: int = 20) -> list[Dict[str, Any]]:
    cursor = db[BACKUP_JOBS_COLLECTION].find({"state": "stale"}, {"_id": 0}).sort("updated_at", -1).limit(int(limit))
    return [row async for row in cursor]


async def mark_stale_backup_jobs(db: Any, *, stale_before_iso: str) -> int:
    result = await db[BACKUP_JOBS_COLLECTION].update_many(
        {
            "state": {"$in": ["queued", "running"]},
            "heartbeat_at": {"$lt": stale_before_iso},
        },
        {
            "$set": {
                "state": "stale",
                "updated_at": backup_now().isoformat(),
                "failure_reason": "stale_job_recovered",
                "ownership_revoked": True,
                "ownership_revoked_at": backup_now().isoformat(),
                "owner_token": None,
            }
        },
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
    "RESTORE_CERT_OPERATION_CLASS",
    "RESTORE_CERT_DEFAULT_LEASE_MINUTES",
    "backup_owner_id",
    "backup_run_id",
    "backup_slot_key_for_hour",
    "backup_slot_key_for_day",
    "restore_certification_guard_slot",
    "restore_certification_terminal_slot",
    "restore_certification_lease_minutes",
    "restore_certification_lease_expires_at",
    "is_restore_certification_stale",
    "ensure_backup_runtime_indexes",
    "claim_backup_job",
    "start_backup_job",
    "heartbeat_backup_job",
    "complete_backup_job",
    "fail_backup_job",
    "list_backup_jobs",
    "list_stale_backup_jobs",
    "get_active_backup_jobs",
    "mark_stale_backup_jobs",
    "BackupJobLease",
    "BackupJobOwnershipLost",
    "record_backup_job_heartbeat_failure",
    "assert_backup_job_ownership",
    "classify_backup_overlap",
]