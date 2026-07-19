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
import argparse
import json
from datetime import datetime, timezone

from dotenv import dotenv_values
from pymongo import MongoClient
from lib.operator_safety import (
    redact_target_identity,
    require_cli_backup_ack,
    require_cli_confirmation,
    require_cli_execute,
    require_cli_runtime_guard,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-production", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--backup-ack", action="store_true")
    args = ap.parse_args()

    env = dotenv_values("/app/backend/.env")
    mongo_url = env.get("MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = env.get("DB_NAME") or os.environ.get("DB_NAME")
    app_env = env.get("APP_ENV") or os.environ.get("APP_ENV") or ""
    if not (mongo_url and db_name):
        print("ERROR: MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2

    target = redact_target_identity(mongo_url, db_name)
    print(json.dumps({"target": target, "mode": "execute" if args.execute else "dry-run"}, indent=2))

    if args.execute:
        try:
            require_cli_execute(args.execute)
            require_cli_confirmation(args.confirm, expected="SEED_PROJECT_MEMBERSHIPS")
            require_cli_backup_ack(args.backup_ack)
            require_cli_runtime_guard(
                app_env=app_env,
                db_name=db_name,
                allow_production=args.allow_production,
                expected_db_name="masci_safety",
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 3

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

    planned = len(privileged) * len(projects)
    if not args.execute:
        print(json.dumps({
            "mode": "dry-run",
            "target": target,
            "project_count": len(projects),
            "privileged_user_count": len(privileged),
            "planned_membership_pairs": planned,
        }, indent=2))
        return 0

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
