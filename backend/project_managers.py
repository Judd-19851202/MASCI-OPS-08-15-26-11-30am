"""
project_managers.py — DB-backed PM roster.

Replaces the hardcoded PM_TABLE in pm_routing.py. Admins can add new PMs
as MASCI hires them, deactivate ones who leave, edit phone/email at any
time. Jobs (jobs_master) reference a PM by email (canonical key), so
reassigning a job is a 1-field edit on the job, not a code change.

Schema (db.project_managers):
  id          str (uuid)
  name        str
  email       str (lowercase canonical key)
  phone       str (optional)
  is_active   bool (false = hidden from job dropdown)
  created_at  iso-utc
  updated_at  iso-utc
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Initial roster — seeded on first boot if collection is empty. Sourced from
# the historical pm_routing.py PM_TABLE (Feb 2026 PM Job List PDF). Once
# seeded, the DB is the source of truth — edits here are NOT replayed.
INITIAL_PMS: List[Dict[str, str]] = [
    {"name": "David Jewett",     "email": "davidjewett@mascigc.com"},
    {"name": "Chris Wright",     "email": "chriswright@mascigc.com"},
    {"name": "Ramon Rodriguez",  "email": "RamonRodriguez@mascigc.com"},
    {"name": "Jaymn Judd",       "email": "jaymn.judd@mascigc.com"},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in doc:
        doc.pop("_id")
    email = (doc.get("email") or "").strip().lower()
    return {
        "id": doc.get("id") or str(uuid.uuid4()),
        "name": (doc.get("name") or "").strip(),
        "email": email,
        "phone": (doc.get("phone") or "").strip(),
        "is_active": bool(doc.get("is_active", True)),
        "created_at": doc.get("created_at") or _now(),
        "updated_at": doc.get("updated_at") or _now(),
    }


async def seed_project_managers(db) -> None:
    """Idempotent: index on email + seed initial roster if empty."""
    try:
        await db.project_managers.create_index("email", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"project_managers index: {e}")

    if await db.project_managers.count_documents({}) > 0:
        return

    docs = [_normalize(r) for r in INITIAL_PMS]
    if docs:
        await db.project_managers.insert_many(docs)
        logger.info(f"project_managers seeded {len(docs)} initial PMs")


async def list_pms(db, only_active: bool = False) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"is_active": True} if only_active else {}
    cursor = db.project_managers.find(q, {"_id": 0}).sort("name", 1)
    return await cursor.to_list(500)


async def add_pm(db, body: Dict[str, Any]) -> Dict[str, Any]:
    doc = _normalize(body)
    if not doc["name"]:
        raise ValueError("name is required")
    if not doc["email"] or "@" not in doc["email"]:
        raise ValueError("a valid email is required")
    # Uniqueness — case-insensitive on email
    existing = await db.project_managers.find_one(
        {"email": doc["email"]}, {"_id": 0}
    )
    if existing:
        raise ValueError(f"A PM with email {doc['email']} already exists")
    await db.project_managers.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_pm(db, pm_id: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    update_fields: Dict[str, Any] = {"updated_at": _now()}
    if "name" in body:
        update_fields["name"] = (body.get("name") or "").strip()
    if "email" in body:
        new_email = (body.get("email") or "").strip().lower()
        if not new_email or "@" not in new_email:
            raise ValueError("a valid email is required")
        # Don't allow stomping another PM's email
        clash = await db.project_managers.find_one(
            {"email": new_email, "id": {"$ne": pm_id}}, {"_id": 0}
        )
        if clash:
            raise ValueError(f"Another PM already uses {new_email}")
        update_fields["email"] = new_email
    if "phone" in body:
        update_fields["phone"] = (body.get("phone") or "").strip()
    if "is_active" in body:
        update_fields["is_active"] = bool(body["is_active"])

    res = await db.project_managers.update_one(
        {"id": pm_id}, {"$set": update_fields}
    )
    if res.matched_count == 0:
        return None
    return await db.project_managers.find_one({"id": pm_id}, {"_id": 0})


async def delete_pm(db, pm_id: str) -> bool:
    """Hard-delete. Use update_pm(is_active=False) for soft-deactivate."""
    res = await db.project_managers.delete_one({"id": pm_id})
    return res.deleted_count > 0


async def find_pm_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    return await db.project_managers.find_one(
        {"email": email.strip().lower()}, {"_id": 0}
    )
