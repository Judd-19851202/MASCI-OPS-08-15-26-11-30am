"""
data_fixes.py — async-safe production data healers.

Two idempotent fixes used by:
  - POST /api/admin/data-fixes/run   (manual one-click admin button)
  - Backend startup self-heal       (auto-run if equipment is missing make/model)

Both fixes are SAFE to run any number of times. They only update docs that
need updating; they never delete or wipe data.
"""
from __future__ import annotations

import logging
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Reuse the manufacturer dictionary + splitter from the seed script
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from seed_equipment_make_model import split_make_model  # noqa: E402

logger = logging.getLogger(__name__)


async def fix_equipment_make_model(db) -> dict:
    """Populate `make` + `model` on every equipment_master doc that's missing
    them, by splitting `make_model` (or the year-stripped `display_label`).

    Returns a summary dict.
    """
    coll = db.equipment_master
    total = await coll.count_documents({})
    needing = await coll.count_documents(
        {"$or": [{"make": {"$exists": False}}, {"make": ""}, {"make": None}]}
    )
    fixed = 0
    cursor = coll.find(
        {"$or": [{"make": {"$exists": False}}, {"make": ""}, {"make": None}]},
        {"_id": 0, "id": 1, "make_model": 1, "display_label": 1},
    )
    async for d in cursor:
        mm = (d.get("make_model") or d.get("display_label") or "").strip()
        if not mm:
            continue
        # Strip a leading 4-digit year if present (display_label fallback)
        mm2 = re.sub(r"^\d{4}\s+", "", mm).strip()
        make, model = split_make_model(mm2)
        if make:
            await coll.update_one(
                {"id": d["id"]}, {"$set": {"make": make, "model": model}}
            )
            fixed += 1

    after_missing = await coll.count_documents(
        {"$or": [{"make": {"$exists": False}}, {"make": ""}, {"make": None}]}
    )
    summary = {
        "total": total,
        "before_missing": needing,
        "fixed": fixed,
        "still_missing": after_missing,
    }
    logger.info(f"[data-fix] equipment_master: {summary}")
    return summary


async def fix_project_memberships(db) -> dict:
    """Ensure every owner/admin user is a member of every non-HQ active project.
    Uses the `project_members` collection (matches the route in projects.py).
    """
    now = datetime.now(timezone.utc).isoformat()

    privileged = [
        u
        async for u in db.users.find(
            {"role": {"$in": ["owner", "admin"]}, "is_active": True},
            {"_id": 0, "id": 1, "email": 1, "role": 1},
        )
    ]
    projects = [
        p
        async for p in db.projects.find(
            {"archived": {"$ne": True}, "is_hq": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1},
        )
    ]
    created = 0
    for u in privileged:
        for p in projects:
            res = await db.project_members.update_one(
                {"project_id": p["id"], "user_id": u["id"]},
                {
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "project_id": p["id"],
                        "user_id": u["id"],
                        "added_at": now,
                        "added_by": "data-fix",
                    }
                },
                upsert=True,
            )
            if res.upserted_id is not None:
                created += 1

    total_members = await db.project_members.count_documents({})
    summary = {
        "privileged_users": len(privileged),
        "projects": len(projects),
        "created": created,
        "total_after": total_members,
    }
    logger.info(f"[data-fix] project_members: {summary}")
    return summary


async def run_all_fixes(db) -> dict:
    """Run all production data fixes — used by the admin endpoint."""
    eq = await fix_equipment_make_model(db)
    pm = await fix_project_memberships(db)
    return {
        "ok": True,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "equipment_master": eq,
        "project_members": pm,
    }


async def boot_self_heal(db) -> None:
    """Called once on backend startup. Auto-fixes:
      1. equipment_master make/model split (if any unit is missing make)
      2. project_members seed (if any owner/admin has 0 memberships)

    Never raises — failure is logged and ignored so a bad fix can't keep the
    backend from booting.
    """
    try:
        missing_eq = await db.equipment_master.count_documents(
            {"$or": [{"make": {"$exists": False}}, {"make": ""}, {"make": None}]}
        )
        if missing_eq > 0:
            logger.info(
                f"[boot-self-heal] {missing_eq} equipment units missing make — auto-fixing"
            )
            await fix_equipment_make_model(db)
        else:
            logger.info("[boot-self-heal] equipment_master clean — no fix needed")
    except Exception as e:  # pragma: no cover
        logger.warning(f"[boot-self-heal] equipment skipped: {e}")

    try:
        # If any owner/admin has zero project_members rows, run the seed.
        privileged_ids = [
            u["id"]
            async for u in db.users.find(
                {"role": {"$in": ["owner", "admin"]}, "is_active": True},
                {"_id": 0, "id": 1},
            )
        ]
        non_hq_count = await db.projects.count_documents(
            {"archived": {"$ne": True}, "is_hq": {"$ne": True}}
        )
        needs_seed = False
        if privileged_ids and non_hq_count > 0:
            for uid in privileged_ids:
                cnt = await db.project_members.count_documents({"user_id": uid})
                if cnt < non_hq_count:
                    needs_seed = True
                    break
        if needs_seed:
            logger.info(
                "[boot-self-heal] privileged user(s) missing project_members — auto-seeding"
            )
            await fix_project_memberships(db)
        else:
            logger.info("[boot-self-heal] project_members clean — no fix needed")
    except Exception as e:  # pragma: no cover
        logger.warning(f"[boot-self-heal] memberships skipped: {e}")
