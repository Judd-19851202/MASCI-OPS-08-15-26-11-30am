"""
seed_project_memberships.py

Adds every owner/admin user to every active project as a member,
populating the `project_members` collection (the one the /api/projects
route actually queries via projects.py:_is_member / list_members).

Idempotent — uses upsert.

Run:
  python3 /app/backend/scripts/seed_project_memberships.py
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import dotenv_values
from pymongo import MongoClient


def main() -> int:
    env = dotenv_values("/app/backend/.env")
    mongo_url = env.get("MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = env.get("DB_NAME") or os.environ.get("DB_NAME")
    if not (mongo_url and db_name):
        print("ERROR: MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2

    db = MongoClient(mongo_url)[db_name]
    now = datetime.now(timezone.utc).isoformat()

    # Owners and admins → all projects (HQ is implicit).
    privileged = list(
        db.users.find(
            {"role": {"$in": ["owner", "admin"]}, "is_active": True},
            {"_id": 0, "id": 1, "email": 1, "role": 1},
        )
    )
    if not privileged:
        print("No owner/admin users found — aborting.")
        return 1
    print(f"[users] {len(privileged)} privileged users")

    projects = list(
        db.projects.find(
            {"archived": {"$ne": True}, "is_hq": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1},
        )
    )
    print(f"[projects] {len(projects)} non-HQ active projects")

    created = 0
    for u in privileged:
        for p in projects:
            res = db.project_members.update_one(
                {"project_id": p["id"], "user_id": u["id"]},
                {
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "project_id": p["id"],
                        "user_id": u["id"],
                        "added_at": now,
                        "added_by": "seed_script",
                    }
                },
                upsert=True,
            )
            if res.upserted_id is not None:
                created += 1

    total = db.project_members.count_documents({})
    print(f"[seed] inserted {created} new project_members rows; collection now has {total} total")

    # Per-user membership summary
    print("[summary]")
    for u in privileged:
        cnt = db.project_members.count_documents({"user_id": u["id"]})
        print(f"  - {u['email']:40s} role={u['role']:7s} memberships={cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
