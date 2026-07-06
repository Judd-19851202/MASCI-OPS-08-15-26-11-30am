"""
scripts/seed_track_23_5_cert_employees.py — TRACK 23.5 cert fixture.

Populates trade / crew / supervisor on the 5 employees named in the
TRACK 23.5 mandate:

    Alec Perkins       · General Laborer · Shop        · David Puma
    Alejandro Escobedo · General Laborer · Concrete    · David Hinson
    Allen Smathers     · Supervisor      · Utility     · Leo
    Alvaro Cia         · 1st Mill Operator · Paving    · Jason
    Amanda Kapp        · Accounting Clerk  · Accounting · Sandy Lohrey

These are the exact values the operator quoted from the Employee
Lifecycle UI. Refuses to run against APP_ENV=production or
DB_NAME=masci_safety (matches the safety pattern from Track 15.13F).

Writes only canonical Employee Lifecycle keys (trade, crew, supervisor)
via `db.employees.update_one` — same keys the HR create/patch endpoint
persists. NO duplicate schema. NO new collection.

Idempotent — running twice produces the same state.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

CERT_EMPLOYEES = [
    ("Alec Perkins",       "General Laborer",   "Shop",       "David Puma"),
    ("Alejandro Escobedo", "General Laborer",   "Concrete",   "David Hinson"),
    ("Allen Smathers",     "Supervisor",        "Utility",    "Leo"),
    ("Alvaro Cia",         "1st Mill Operator", "Paving",     "Jason"),
    ("Amanda Kapp",        "Accounting Clerk",  "Accounting", "Sandy Lohrey"),
]


async def main() -> int:
    load_dotenv()
    app_env = os.environ.get("APP_ENV", "").lower()
    db_name = os.environ.get("DB_NAME", "")
    if app_env == "production" or db_name == "masci_safety":
        print(f"REFUSING: APP_ENV={app_env!r} DB_NAME={db_name!r} — cert fixture is preview-only.")
        return 2

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[db_name]
    now = datetime.now(timezone.utc).isoformat()

    updated = 0
    skipped = 0
    for name, trade, crew, supervisor in CERT_EMPLOYEES:
        result = await db.employees.update_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}},
            {"$set": {
                "trade": trade,
                "crew": crew,
                "supervisor": supervisor,
                "updated_at": now,
                "track_23_5_cert_seed": True,
            }},
        )
        if result.matched_count == 0:
            print(f"  SKIP  {name}: not found in db.employees")
            skipped += 1
        else:
            updated += 1
            doc = await db.employees.find_one(
                {"name": {"$regex": f"^{name}$", "$options": "i"}},
                {"_id": 0, "name": 1, "trade": 1, "crew": 1, "supervisor": 1},
            )
            print(f"  OK    {doc}")

    print(f"\nUpdated: {updated}  Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
