"""TRACK 22.4b-follow-up · B-03 · Daily Report identifier alignment.

Backfill script that idempotently copies ``doc_id`` into ``report_number``
for every daily report where ``report_number`` is empty. Non-destructive:
never overwrites an existing non-empty ``report_number``, never modifies
``doc_id``, and never touches records without a canonical ``doc_id``.

Design guarantees
-----------------
- **Idempotent**: running multiple times produces the same result.
- **Non-destructive**: only sets ``report_number`` when it is empty
  (``""``, ``None``, or absent) AND ``doc_id`` is populated.
- **Dry-run capable**: pass ``--dry-run`` to see counts without writing.
- **Auditable**: logs found/fixed/skipped counts; writes a summary row
  to ``dr_report_number_backfill_audit``.

Usage
-----
    python -m scripts.backfill_dr_report_number [--dry-run]

Also importable::

    from scripts.backfill_dr_report_number import backfill_dr_report_number

Rationale
---------
Track 22.4b defect B-03 discovered that 80 % of preview daily reports
had empty ``report_number`` because the field is model-optional and
most submissions never sent one. Trust Spine uses ``doc_id`` and joins
correctly, but legacy code paths and the admin search bar sometimes
read ``report_number`` — so aligning the two fields eliminates a whole
class of silent lookup misses.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    print("motor / python-dotenv required")
    sys.exit(1)


COLLECTION = "daily_reports"
AUDIT_COLL = "dr_report_number_backfill_audit"


async def backfill_dr_report_number(db, *, dry_run: bool = False) -> dict:
    """Run the backfill. Returns a counts dict.

    Parameters
    ----------
    db:
        Motor database handle.
    dry_run:
        When ``True`` no writes occur; only counts are computed.
    """
    empty_query = {
        "$and": [
            {"$or": [
                {"report_number": ""},
                {"report_number": None},
                {"report_number": {"$exists": False}},
            ]},
            {"doc_id": {"$nin": ["", None], "$exists": True, "$type": "string"}},
        ]
    }
    total = await db[COLLECTION].count_documents({})
    candidates = await db[COLLECTION].count_documents(empty_query)
    populated_already = await db[COLLECTION].count_documents({
        "report_number": {"$nin": ["", None], "$exists": True, "$type": "string"}
    })

    if dry_run:
        return {
            "dry_run": True,
            "total": total,
            "populated_already": populated_already,
            "candidates": candidates,
            "would_update": candidates,
        }

    # Batched aggregation-style update — copies doc_id into report_number
    # only when the candidate query matches. Motor lacks $set-from-field
    # pre-4.2 syntax, so use an aggregation pipeline update.
    result = await db[COLLECTION].update_many(
        empty_query,
        [{"$set": {"report_number": "$doc_id"}}],
    )
    updated = result.modified_count

    audit_row = {
        "track": "TRACK_22_4B_FOLLOWUP_B03",
        "run_at": datetime.now(timezone.utc),
        "environment": os.environ.get("APP_ENV") or "unknown",
        "total_daily_reports": total,
        "candidates_before": candidates,
        "already_populated_before": populated_already,
        "updated": updated,
        "safe_to_delete": True,
        "no_real_operational_effect": True,
    }
    await db[AUDIT_COLL].insert_one(audit_row)

    return {
        "dry_run": False,
        "total": total,
        "populated_already": populated_already,
        "candidates": candidates,
        "updated": updated,
    }


async def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute counts without writing.")
    args = parser.parse_args()

    load_dotenv("/app/backend/.env")
    mongo_url = os.environ["MONGO_URL"].strip('"')
    db_name = os.environ["DB_NAME"].strip('"')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    result = await backfill_dr_report_number(db, dry_run=args.dry_run)
    print(f"[TRACK 22.4b-follow-up · B-03] {result}")


if __name__ == "__main__":
    asyncio.run(_main())
