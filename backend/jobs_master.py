"""
jobs_master.py — DB-backed MASCI active-jobs registry.

Replaces the static /app/frontend/src/lib/jobLibrary.js. Admin can add /
edit / delete / activate-deactivate jobs via the AdminJobMasterPanel.
JobPicker pulls live from /api/jobs.

Schema (db.jobs_master):
  id              str (uuid)
  project_number  str (unique key for upsert, e.g. "25-21" or "26-08 - CP")
  project_name    str
  location        str
  client          str
  project_manager str
  active          bool      (false = hidden from JobPicker)
  created_at      iso-utc
  updated_at      iso-utc
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent / "data" / "jobs_master.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip _id, ensure id, fill defaults."""
    if "_id" in doc:
        doc.pop("_id")
    out = {
        "id": doc.get("id") or str(uuid.uuid4()),
        "project_number": (doc.get("project_number") or "").strip(),
        "project_name": (doc.get("project_name") or "").strip(),
        "location": (doc.get("location") or "").strip(),
        "client": (doc.get("client") or "").strip(),
        "project_manager": (doc.get("project_manager") or "").strip(),
        "active": bool(doc.get("active", True)),
        "created_at": doc.get("created_at") or _now(),
        "updated_at": doc.get("updated_at") or _now(),
    }
    return out


async def seed_jobs_master(db) -> None:
    """Idempotent: if collection is empty, load from JSON seed."""
    try:
        await db.jobs_master.create_index("project_number", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"jobs_master index: {e}")

    if await db.jobs_master.count_documents({}) > 0:
        logger.info("jobs_master already populated — skipping seed")
        return

    if not DATA_FILE.exists():
        logger.info("jobs_master.json not found — skipping seed")
        return

    try:
        rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"jobs_master.json parse error: {e}")
        return

    if not isinstance(rows, list) or not rows:
        return

    docs = [_normalize(r) for r in rows]
    await db.jobs_master.insert_many(docs)
    logger.info(f"jobs_master seeded {len(docs)} jobs")


async def list_jobs(db, only_active: bool = True) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"active": True} if only_active else {}
    cursor = db.jobs_master.find(q, {"_id": 0}).sort("project_number", 1)
    return await cursor.to_list(2000)


async def upsert_job(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert by project_number. Returns the saved doc.

    `id` and `created_at` are insert-only: on update we never overwrite the
    existing primary key, otherwise PATCH/DELETE by id would 404 right after
    an Add/Update click.
    """
    doc = _normalize(body)
    if not doc["project_number"]:
        raise ValueError("project_number is required")
    if not doc["project_name"]:
        raise ValueError("project_name is required")
    now = _now()
    insert_only = {
        "id": doc["id"],
        "created_at": doc.get("created_at") or now,
    }
    update_fields = {
        "project_number": doc["project_number"],
        "project_name": doc["project_name"],
        "location": doc["location"],
        "client": doc["client"],
        "project_manager": doc["project_manager"],
        "active": doc["active"],
        "updated_at": now,
    }
    await db.jobs_master.update_one(
        {"project_number": doc["project_number"]},
        {"$set": update_fields, "$setOnInsert": insert_only},
        upsert=True,
    )
    saved = await db.jobs_master.find_one(
        {"project_number": doc["project_number"]}, {"_id": 0}
    )
    return saved


async def delete_job(db, job_id: str) -> bool:
    res = await db.jobs_master.delete_one({"id": job_id})
    return res.deleted_count > 0


async def set_active(db, job_id: str, active: bool) -> Optional[Dict[str, Any]]:
    await db.jobs_master.update_one(
        {"id": job_id}, {"$set": {"active": bool(active), "updated_at": _now()}}
    )
    return await db.jobs_master.find_one({"id": job_id}, {"_id": 0})


async def bulk_replace(db, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Replace the whole collection with a new list (used by admin upload)."""
    docs = [_normalize(r) for r in rows]
    # Validate before wiping
    for d in docs:
        if not d["project_number"] or not d["project_name"]:
            raise ValueError(
                f"Every row must have project_number + project_name (offender: {d})"
            )
    await db.jobs_master.delete_many({})
    if docs:
        await db.jobs_master.insert_many(docs)
    return {"replaced": len(docs)}
