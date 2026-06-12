"""
Track 13.4A · Step 2 — PM Preview Fixture
==========================================

Idempotent seed for `pm.demo@mascigc.com` — a PREVIEW-ONLY Project Manager
fixture scoped to exactly TWO real jobs via `co_pm_emails[]` so we do not
override the primary `pm_email` of any production-relevant job.

Rules honoured:
  • Preview env only — refuses to run unless APP_ENV != "production"
    AND DB_NAME ends with "_preview" (defence in depth).
  • Re-runnable: rewrites the password hash + must_change_password flag
    every time so the test credentials stay valid even after rotation.
  • Picks the FIRST TWO ACTIVE jobs (by project_number) and grants
    co-PM status; never demotes/replaces a primary PM.
  • No admin role / no portal_tokens / no super-admin powers.

Reusable for future PM regression smoke tests.
"""
from __future__ import annotations
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
# Allow `import pm_auth` (it lives at /app/backend/pm_auth.py)
sys.path.insert(0, "/app/backend")
from pm_auth import set_pm_password  # noqa: E402

PM_EMAIL = "pm.demo@mascigc.com"
PM_NAME = "PM Demo (Preview Fixture)"
PM_PASSWORD = "PmTest2026!"


async def main():
    app_env = (os.environ.get("APP_ENV") or "production").lower()
    db_name = os.environ["DB_NAME"]
    if app_env == "production" or not db_name.endswith("_preview"):
        raise RuntimeError(
            f"REFUSING TO RUN — PM Demo fixture is preview-only. "
            f"APP_ENV={app_env!r} DB_NAME={db_name!r}"
        )

    client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[db_name]

    now = datetime.now(timezone.utc).isoformat()

    # Upsert the PM doc.
    existing = await db.project_managers.find_one({"email": PM_EMAIL})
    if existing:
        pm_id = existing["id"]
        await db.project_managers.update_one(
            {"id": pm_id},
            {"$set": {
                "name": PM_NAME,
                "phone": "",
                "is_active": True,
                "updated_at": now,
            }},
        )
        print(f"[fixture] reused existing PM row id={pm_id}")
    else:
        pm_id = str(uuid.uuid4())
        await db.project_managers.insert_one({
            "id": pm_id,
            "name": PM_NAME,
            "email": PM_EMAIL,
            "phone": "",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        print(f"[fixture] inserted PM row id={pm_id}")

    # Set a known password (must_change=false → ready for automation/tests).
    updated = await set_pm_password(db, pm_id, PM_PASSWORD, must_change=False)
    if not updated:
        raise RuntimeError("set_pm_password returned None")
    print(f"[fixture] password set; has_hash={bool(updated.get('password_hash'))}")

    # Pick 2 active jobs (by project_number ascending) to scope to.
    target_project_numbers = []
    cursor = db.jobs_master.find(
        {"deleted_at": {"$in": [None, ""]}, "is_active": {"$ne": False}},
        {"_id": 0, "project_number": 1, "project_name": 1, "project_manager": 1},
    ).sort("project_number", 1).limit(2)
    async for job in cursor:
        target_project_numbers.append(job["project_number"])
        print(f"[fixture] target job: {job.get('project_number')} :: {job.get('project_name')} "
              f"(primary PM: {job.get('project_manager')})")

    if len(target_project_numbers) < 2:
        raise RuntimeError(f"Could not find 2 active jobs; found {len(target_project_numbers)}")

    # First, clear pm.demo@ from any jobs that aren't in the target list
    # so the fixture stays scoped to exactly 2 projects on re-runs.
    await db.jobs_master.update_many(
        {"project_number": {"$nin": target_project_numbers},
         "co_pm_emails": PM_EMAIL},
        {"$pull": {"co_pm_emails": PM_EMAIL},
         "$set": {"updated_at": now}},
    )

    # Then add pm.demo@ to co_pm_emails on each target job (addToSet = idempotent).
    for pn in target_project_numbers:
        await db.jobs_master.update_one(
            {"project_number": pn},
            {"$addToSet": {"co_pm_emails": PM_EMAIL},
             "$set": {"updated_at": now}},
        )

    # Verify scope from the DB's perspective.
    scope_count = await db.jobs_master.count_documents({
        "$or": [{"pm_email": PM_EMAIL}, {"co_pm_emails": PM_EMAIL}],
        "deleted_at": {"$in": [None, ""]},
    })
    print(f"[fixture] verified pm_scope job count: {scope_count}")
    print()
    print(f"  Email:    {PM_EMAIL}")
    print(f"  Password: {PM_PASSWORD}")
    print(f"  Projects: {target_project_numbers}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
