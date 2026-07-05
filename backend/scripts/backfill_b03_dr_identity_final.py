"""TRACK 22.4b-followup-DR · B-03 FINAL ELIMINATION backfill.

Historical repair for Daily Report identity skew.

Root cause
----------
Two identity fields ended up on `daily_reports`:
  * `doc_id`         — atomic, canonical, `DR-YYYY-NNNNN` from mint_doc_id.
  * `report_number`  — legacy, freely written by the client, historically
                       pre-filled from `/daily-reports/next-number` in
                       the `DR-YYYYMMDD-NNN` shape.

Live audit surfaced **271 rows** where `report_number != doc_id`, and
older bug reports flagged empty `report_number` on newer inserts (now
also closed by the write-path unconditional-mirror fix).

Repair rules
------------
For every row:
  1. If `doc_id` is empty/missing → mint one atomically via `mint_doc_id`
     (idempotent, uses the same counter as production).
  2. Set `report_number = doc_id` unconditionally. This is the doctrine:
     `doc_id` is the canonical identity, `report_number` mirrors it.

Doctrine
--------
- **Idempotent.** Zero updates on the second run.
- **Non-destructive.** Only rewrites `report_number` (the drifted field);
  never touches `doc_id` unless one is missing.
- **Preview-safe.** Refuses to run when APP_ENV=production unless
  `--allow-production` is explicitly passed.
- **Audit trail.** Every touched row logged to
  `dr_report_number_backfill_audit` (existing collection).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

AUDIT_COLL = "dr_report_number_backfill_audit"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(*, dry_run: bool, allow_production: bool) -> int:
    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if app_env == "production" and not allow_production:
        print(f"REFUSING to run: APP_ENV={app_env!r}. Use --allow-production to override.")
        return 2

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("MONGO_URL / DB_NAME are missing.")
        return 3

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Late-imported so the CLI works even before backend startup.
    sys.path.insert(0, "/app/backend")
    from doc_ids import mint_doc_id  # noqa: PLC0415

    counts = {
        "scanned": 0,
        "already_aligned": 0,
        "report_number_updated": 0,
        "doc_id_minted": 0,
        "would_write_updates": 0,
    }

    async for row in db.daily_reports.find(
        {},
        {"_id": 1, "id": 1, "doc_id": 1, "report_number": 1, "report_date": 1, "created_at": 1},
    ):
        counts["scanned"] += 1
        doc_id = (row.get("doc_id") or "").strip()
        rn = (row.get("report_number") or "").strip()

        # (1) mint a canonical doc_id if missing (rare — the counter is atomic
        #     and mint has been in place for many revs, but be defensive).
        if not doc_id:
            when = row.get("report_date") or row.get("created_at")
            new_doc_id = await mint_doc_id(db, "DR", when=when)
            counts["doc_id_minted"] += 1
            counts["would_write_updates"] += 1
            if not dry_run:
                await db.daily_reports.update_one(
                    {"_id": row["_id"]},
                    {"$set": {
                        "doc_id": new_doc_id,
                        "report_number": new_doc_id,
                        "b03_backfill_at": _now_iso(),
                    }},
                )
                await db[AUDIT_COLL].insert_one({
                    "at": _now_iso(),
                    "id": row.get("id"),
                    "action": "mint_doc_id_and_mirror_report_number",
                    "old_doc_id": doc_id,
                    "old_report_number": rn,
                    "new_doc_id": new_doc_id,
                })
            continue

        # (2) mirror doc_id onto report_number when they diverge.
        if rn == doc_id:
            counts["already_aligned"] += 1
            continue

        counts["report_number_updated"] += 1
        counts["would_write_updates"] += 1
        if not dry_run:
            await db.daily_reports.update_one(
                {"_id": row["_id"]},
                {"$set": {
                    "report_number": doc_id,
                    "b03_backfill_at": _now_iso(),
                    "b03_previous_report_number": rn,
                }},
            )
            await db[AUDIT_COLL].insert_one({
                "at": _now_iso(),
                "id": row.get("id"),
                "action": "mirror_report_number_to_doc_id",
                "old_report_number": rn,
                "new_report_number": doc_id,
                "doc_id": doc_id,
            })

    print("── TRACK 22.4b-followup-DR B-03 backfill summary ──")
    for k, v in counts.items():
        print(f"  {k:32s} {v}")
    if dry_run:
        print("\nDRY RUN — no writes performed. Re-run without --dry-run to apply.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="scan only, no writes")
    ap.add_argument("--allow-production", action="store_true", help="explicit override")
    args = ap.parse_args()
    sys.exit(asyncio.run(run(dry_run=args.dry_run, allow_production=args.allow_production)))


if __name__ == "__main__":
    main()
