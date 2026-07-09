"""TRACK 27.00 · Phase A · Lifecycle status backfill.

Purpose
-------
235 legacy employee documents in the live DB have no `lifecycle_status`
field set. The HR page's "Actively Employed" KPI card interprets those
as active by falling back to `is_active`, but the status dropdown filter
does a strict `lifecycle_status == "Active"` match, so those 235 rows
disappear when HR picks "Active" from the dropdown. That is the exact
mechanism that produces the 230-vs-18 mismatch HR reported.

This script closes the ambiguity source by writing `lifecycle_status`
on those 235 rows based on their `is_active` flag. After the backfill:

    is_active != False  →  lifecycle_status = "Active"
    is_active === False →  lifecycle_status = "Inactive"

Existing rows that already carry a `lifecycle_status` value are NEVER
overwritten. The backfill is idempotent (re-running is a noop) and
reversible (every write emits a `kind=backfill_lifecycle_status` event
in `employee_lifecycle_events` with old_value=None and new_value=X, so
a reverse script can undo it by scanning that kind).

Usage
-----
    # 1) Dry-run (default) — prints exactly which rows would change.
    python -m scripts.track_27_backfill_lifecycle_status

    # 2) Real run — writes to Mongo and emits audit events.
    python -m scripts.track_27_backfill_lifecycle_status --commit

    # 3) Reverse (undo the backfill).
    python -m scripts.track_27_backfill_lifecycle_status --reverse
    python -m scripts.track_27_backfill_lifecycle_status --reverse --commit

Safety
------
- Never touches `deleted_at IS NOT None` rows.
- Never overwrites an existing `lifecycle_status` value.
- Dry-run is the default so nobody can accidentally mutate prod.
- Every write is audit-logged with an `actor="backfill:track_27"` tag.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

# Allow running as a script from /app/backend or via `python -m`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _connect():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    return client, client[db_name]


async def dry_run(db) -> Dict[str, Any]:
    """Report which rows would be touched without writing anything."""
    to_active = []
    to_inactive = []
    already_set_but_null = []
    async for doc in db.employees.find(
        {"deleted_at": None,
         "$or": [{"lifecycle_status": {"$exists": False}},
                 {"lifecycle_status": None}]},
        {"_id": 0, "id": 1, "employee_id": 1, "name": 1,
         "lifecycle_status": 1, "is_active": 1},
    ):
        row = {
            "id": doc.get("id"),
            "employee_id": doc.get("employee_id") or "",
            "name": doc.get("name") or "",
            "current_lifecycle_status": doc.get("lifecycle_status"),
            "is_active": doc.get("is_active"),
        }
        if doc.get("is_active") is False:
            row["target_status"] = "Inactive"
            to_inactive.append(row)
        else:
            # is_active == True OR is_active is None → default to Active
            # (a row with neither field is a very-old legacy record that
            # has always displayed as active in the UI; preserve that).
            row["target_status"] = "Active"
            to_active.append(row)
        if doc.get("lifecycle_status") is None and "lifecycle_status" in doc:
            already_set_but_null.append(row["id"])
    return {
        "would_set_active": len(to_active),
        "would_set_inactive": len(to_inactive),
        "explicit_null_field_present": len(already_set_but_null),
        "sample_active": to_active[:5],
        "sample_inactive": to_inactive[:5],
    }


async def apply(db, *, actor: str = "backfill:track_27") -> Dict[str, Any]:
    """Perform the backfill. Idempotent: skips rows that already have a value."""
    now = _now_iso()
    active_hits = 0
    inactive_hits = 0
    events: List[Dict[str, Any]] = []
    async for doc in db.employees.find(
        {"deleted_at": None,
         "$or": [{"lifecycle_status": {"$exists": False}},
                 {"lifecycle_status": None}]},
        {"_id": 0, "id": 1, "employee_id": 1,
         "lifecycle_status": 1, "is_active": 1},
    ):
        if doc.get("is_active") is False:
            new_status = "Inactive"
            inactive_hits += 1
        else:
            new_status = "Active"
            active_hits += 1
        r = await db.employees.update_one(
            {"id": doc["id"],
             "$or": [{"lifecycle_status": {"$exists": False}},
                     {"lifecycle_status": None}]},
            {"$set": {"lifecycle_status": new_status,
                      "lifecycle_status_backfilled_at": now}},
        )
        if r.modified_count:
            events.append({
                "employee_id": doc["id"],
                "kind": "backfill_lifecycle_status",
                "old_value": None,
                "new_value": new_status,
                "reason": ("Track 27.00 Phase A · legacy row had no "
                           "lifecycle_status; derived from is_active"),
                "actor": actor,
                "at": now,
            })
    if events:
        await db.employee_lifecycle_events.insert_many(events)
    return {
        "set_to_active": active_hits,
        "set_to_inactive": inactive_hits,
        "events_written": len(events),
    }


async def reverse(db, *, dry: bool = True) -> Dict[str, Any]:
    """Undo the backfill by removing lifecycle_status from every row that
    still carries the `lifecycle_status_backfilled_at` marker."""
    query = {"lifecycle_status_backfilled_at": {"$exists": True}}
    if dry:
        n = await db.employees.count_documents(query)
        return {"would_unset": n}
    r = await db.employees.update_many(
        query,
        {"$unset": {"lifecycle_status": "",
                    "lifecycle_status_backfilled_at": ""}},
    )
    now = _now_iso()
    await db.employee_lifecycle_events.insert_one({
        "employee_id": "*",
        "kind": "backfill_lifecycle_status_reversed",
        "old_value": None, "new_value": None,
        "reason": "Track 27.00 Phase A reverse",
        "actor": "backfill:track_27",
        "at": now,
        "affected_count": r.modified_count,
    })
    return {"unset": r.modified_count}


def _print_report(label: str, report: Dict[str, Any]) -> None:
    print(f"\n=== {label} ===")
    for k, v in report.items():
        if k.startswith("sample_"):
            print(f"{k}:")
            for row in v:
                print(f"  · id={row.get('id','')[:8]}…  "
                      f"employee_id={row.get('employee_id','')}  "
                      f"name={row.get('name','')[:32]!r}  "
                      f"is_active={row.get('is_active')}  "
                      f"→ {row.get('target_status')}")
        else:
            print(f"{k}: {v}")


async def main_async(args: argparse.Namespace) -> int:
    client, db = await _connect()
    try:
        if args.reverse:
            print("Mode: REVERSE" + (" · dry-run" if not args.commit else " · WRITE"))
            report = await reverse(db, dry=not args.commit)
            _print_report("REVERSE report", report)
            return 0

        print("Mode: BACKFILL" + (" · dry-run" if not args.commit else " · WRITE"))
        dry = await dry_run(db)
        _print_report("DRY-RUN report", dry)
        if not args.commit:
            print("\nNo changes made (dry-run). Re-run with --commit to apply.")
            return 0

        print("\nApplying…")
        applied = await apply(db)
        _print_report("WRITE report", applied)
        return 0
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true",
                        help="Actually write to Mongo (default is dry-run).")
    parser.add_argument("--reverse", action="store_true",
                        help="Undo the backfill instead of applying it.")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
