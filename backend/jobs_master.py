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
import re
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
    co = doc.get("co_pm_emails") or []
    if not isinstance(co, list):
        co = []
    cleaned_co = []
    seen = set()
    for e in co:
        if not isinstance(e, str):
            continue
        em = e.strip().lower()
        if em and em not in seen:
            seen.add(em)
            cleaned_co.append(em)
        if len(cleaned_co) >= 4:
            break
    out = {
        "id": doc.get("id") or str(uuid.uuid4()),
        "project_number": (doc.get("project_number") or "").strip(),
        "project_name": (doc.get("project_name") or "").strip(),
        "location": (doc.get("location") or "").strip(),
        "client": (doc.get("client") or "").strip(),
        "project_manager": (doc.get("project_manager") or "").strip(),
        "pm_email": (doc.get("pm_email") or "").strip().lower(),
        "co_pm_emails": cleaned_co,
        "active": bool(doc.get("active", True)),
        "created_at": doc.get("created_at") or _now(),
        "updated_at": doc.get("updated_at") or _now(),
    }
    return out


async def seed_jobs_master(db) -> None:
    """Idempotent: if collection is empty, load from JSON seed.
    Always runs the pm_email backfill — rolls existing jobs that have only
    a project_manager name forward to also have pm_email set, so the new
    DB-backed routing knows where to send each job's emails. Safe to run
    on every boot (only updates docs whose pm_email is still empty)."""
    try:
        await db.jobs_master.create_index("project_number", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"jobs_master index: {e}")

    if await db.jobs_master.count_documents({}) == 0:
        if DATA_FILE.exists():
            try:
                rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(rows, list) and rows:
                    docs = [_normalize(r) for r in rows]
                    await db.jobs_master.insert_many(docs)
                    logger.info(f"jobs_master seeded {len(docs)} jobs")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"jobs_master.json parse error: {e}")
        else:
            logger.info("jobs_master.json not found — skipping seed")
    else:
        logger.info("jobs_master already populated — skipping seed")

    # ----- pm_email backfill -----
    # Any job that has a project_manager name but no pm_email gets linked
    # to the matching PM in project_managers. Idempotent.
    backfilled = 0
    cursor = db.jobs_master.find(
        {
            "$or": [
                {"pm_email": {"$exists": False}},
                {"pm_email": ""},
                {"pm_email": None},
            ],
            "project_manager": {"$nin": ["", None]},
        },
        {"_id": 0},
    )
    async for j in cursor:
        nm = (j.get("project_manager") or "").strip()
        if not nm:
            continue
        pm = await db.project_managers.find_one({"name": nm}, {"_id": 0})
        if pm and pm.get("email"):
            await db.jobs_master.update_one(
                {"id": j["id"]},
                {"$set": {
                    "pm_email": pm["email"].lower(),
                    "updated_at": _now(),
                }},
            )
            backfilled += 1
    if backfilled:
        logger.info(f"jobs_master backfill linked pm_email on {backfilled} jobs")


async def list_jobs(db, only_active: bool = True, search: str = None) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"deleted_at": {"$in": [None, ""]}}
    if only_active:
        q["active"] = True
    # Population-independent server-side search across the FULL canonical
    # project master, so any job is discoverable regardless of master size.
    if search and str(search).strip():
        sre = {"$regex": re.escape(str(search).strip()), "$options": "i"}
        q["$or"] = [{"project_number": sre}, {"name": sre}, {"project_name": sre}, {"client": sre}]
    cursor = db.jobs_master.find(q, {"_id": 0}).sort("project_number", 1)
    return await cursor.to_list(200 if (search and str(search).strip()) else 5000)


async def list_archived_jobs(db) -> List[Dict[str, Any]]:
    """Soft-deleted jobs, newest deletion first."""
    cursor = db.jobs_master.find(
        {"deleted_at": {"$ne": None, "$exists": True}}, {"_id": 0}
    ).sort("deleted_at", -1)
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        if d.get("deleted_at"):
            out.append(d)
    return out


async def upsert_job(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert by project_number. Returns the saved doc.

    `id` and `created_at` are insert-only: on update we never overwrite the
    existing primary key, otherwise PATCH/DELETE by id would 404 right after
    an Add/Update click.

    ``co_pm_emails`` is only written when the caller explicitly passes a
    list — passing ``None`` (the default) preserves the existing co-PMs
    so the primary-PM reassign UI doesn't accidentally wipe them.
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
        "pm_email": doc["pm_email"],
        "active": doc["active"],
        "updated_at": now,
    }
    # Only write co_pm_emails when the caller explicitly passed a list.
    if body.get("co_pm_emails") is not None:
        update_fields["co_pm_emails"] = doc["co_pm_emails"]
    else:
        # On insert, co_pm_emails defaults to [] (handled by setOnInsert).
        insert_only["co_pm_emails"] = []
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
    """Soft-delete: mark deleted_at instead of removing the row, so a
    mis-click is recoverable from the Archive tab for 14 days."""
    res = await db.jobs_master.update_one(
        {"$and": [{"id": job_id}, {"deleted_at": {"$in": [None, ""]}}]},
        {"$set": {"deleted_at": _now()}},
    )
    return res.matched_count > 0


async def restore_job(db, job_id: str) -> bool:
    res = await db.jobs_master.update_one(
        {"$and": [{"id": job_id}, {"deleted_at": {"$ne": None}}]},
        {"$unset": {"deleted_at": ""}, "$set": {"updated_at": _now()}},
    )
    return res.matched_count > 0


async def set_active(db, job_id: str, active: bool) -> Optional[Dict[str, Any]]:
    await db.jobs_master.update_one(
        {"id": job_id}, {"$set": {"active": bool(active), "updated_at": _now()}}
    )
    return await db.jobs_master.find_one({"id": job_id}, {"_id": 0})


async def bulk_replace(db, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Replace the whole collection with a new list (used by admin upload)."""
    docs = [_normalize(r) for r in rows]
    if not docs:
        raise ValueError("bulk replace refused: rows must be non-empty for full replacement")
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
