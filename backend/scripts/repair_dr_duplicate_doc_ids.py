"""TRACK 22.4b-followup-DR · duplicate doc_id repair + counter fence.

Additional defect surfaced during B-03 audit: **85 distinct doc_ids
appear on more than one Daily Report row** (170 rows total in the
dupe groups). Root cause: the atomic `doc_id_counters.DR-YYYY.seq`
counter was reset below values that already existed (most likely a
preview cert seed / restore drill that lowered the counter). Every
subsequent atomic mint then produced a value that collided with a
previously-persisted row.

Repair rules
------------
For each duplicate doc_id group:
  * Keep the chronologically-first row's doc_id (based on `created_at`,
    falling back to `report_date`).
  * For every subsequent row in the group, mint a **fresh** doc_id via
    `mint_doc_id` (atomic — cannot collide) and rewrite `doc_id` +
    `report_number` on that row.
  * Log every reassignment to `dr_doc_id_dedup_audit`.

Fence
-----
Post-repair, seed every `doc_id_counters.DR-YYYY.seq` to
`max(seq, max_doc_id_seq_in_daily_reports_for_that_year)` so a future
restore/reset never lowers the counter below live rows.

Doctrine
--------
- **Idempotent.** After a successful pass, re-running is zero-diff.
- **Non-destructive.** Never deletes rows. Reassignment preserves
  `id` (UUID), `project_number`, `report_date`, and every payload
  field — only `doc_id` + `report_number` change on the *later*
  duplicates.
- **Preview-safe.** Refuses APP_ENV=production without explicit
  --allow-production.
- **Adds unique index.** Creates a UNIQUE index on `doc_id` after
  the repair so future collisions fail loud at insert time (never
  silently reuse a doc_id again).
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

AUDIT_COLL = "dr_doc_id_dedup_audit"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seq_from_doc_id(doc_id: str) -> int:
    if not doc_id:
        return 0
    parts = doc_id.split("-")
    if len(parts) != 3:
        return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0


def _year_from_doc_id(doc_id: str) -> str:
    if not doc_id:
        return ""
    parts = doc_id.split("-")
    if len(parts) != 3:
        return ""
    return parts[1]


async def _sort_key(row: dict) -> tuple:
    return (row.get("created_at") or row.get("report_date") or "", row.get("id") or "")


async def run(*, dry_run: bool, allow_production: bool) -> int:
    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if app_env == "production" and not allow_production:
        print(f"REFUSING to run: APP_ENV={app_env!r}. Use --allow-production to override.")
        return 2

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    sys.path.insert(0, "/app/backend")
    from doc_ids import mint_doc_id  # noqa: PLC0415

    counts = {
        "duplicate_groups_found": 0,
        "rows_reassigned": 0,
        "counter_advances": 0,
        "would_write_updates": 0,
    }

    # Step 1 — find every duplicate doc_id group.
    dupe_groups: list[dict] = []
    async for pat in db.daily_reports.aggregate([
        {"$group": {"_id": "$doc_id", "count": {"$sum": 1}, "ids": {"$push": "$id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]):
        dupe_groups.append(pat)

    counts["duplicate_groups_found"] = len(dupe_groups)

    for pat in dupe_groups:
        doc_id = pat["_id"]
        # Fetch every row in the group with full context.
        rows = []
        async for r in db.daily_reports.find(
            {"doc_id": doc_id},
            {"_id": 1, "id": 1, "doc_id": 1, "report_number": 1,
             "created_at": 1, "report_date": 1, "project_number": 1},
        ):
            rows.append(r)
        # Sort chronologically; keep the first, reassign the rest.
        rows.sort(key=lambda r: (r.get("created_at") or r.get("report_date") or "", r.get("id") or ""))
        keeper = rows[0]
        for later in rows[1:]:
            when = later.get("report_date") or later.get("created_at")
            if dry_run:
                new_doc_id = f"[would mint from DR-{_year_from_doc_id(doc_id)}]"
            else:
                new_doc_id = await mint_doc_id(db, "DR", when=when)
                await db.daily_reports.update_one(
                    {"_id": later["_id"]},
                    {"$set": {
                        "doc_id": new_doc_id,
                        "report_number": new_doc_id,
                        "b03_dedup_at": _now_iso(),
                        "b03_previous_doc_id": doc_id,
                    }},
                )
                await db[AUDIT_COLL].insert_one({
                    "at": _now_iso(),
                    "id": later.get("id"),
                    "action": "reassign_duplicate_doc_id",
                    "kept_row_id": keeper.get("id"),
                    "old_doc_id": doc_id,
                    "new_doc_id": new_doc_id,
                })
            counts["rows_reassigned"] += 1
            counts["would_write_updates"] += 1

    # Step 2 — Counter fence. For every year present in daily_reports,
    # advance the counter to at least the max observed seq.
    year_max_seq: dict[str, int] = {}
    async for r in db.daily_reports.find({}, {"_id": 0, "doc_id": 1}):
        did = r.get("doc_id") or ""
        y = _year_from_doc_id(did)
        s = _seq_from_doc_id(did)
        if y and s:
            year_max_seq[y] = max(year_max_seq.get(y, 0), s)

    for year, max_seq in year_max_seq.items():
        counter_key = f"DR-{year}"
        row = await db.doc_id_counters.find_one({"_id": counter_key}, {"_id": 0, "seq": 1})
        cur = int((row or {}).get("seq") or 0)
        if cur < max_seq:
            counts["counter_advances"] += 1
            counts["would_write_updates"] += 1
            if not dry_run:
                await db.doc_id_counters.update_one(
                    {"_id": counter_key},
                    {"$set": {"seq": max_seq}, "$setOnInsert": {"prefix": "DR", "year": int(year)}},
                    upsert=True,
                )
                await db[AUDIT_COLL].insert_one({
                    "at": _now_iso(),
                    "action": "counter_fence_advance",
                    "counter_key": counter_key,
                    "old_seq": cur,
                    "new_seq": max_seq,
                })

    # Step 3 — Add unique index on doc_id. Skip if dry-run or if the
    # collection still has known duplicates (defensive).
    if not dry_run and counts["duplicate_groups_found"] == 0 or (not dry_run and counts["rows_reassigned"] > 0):
        # Re-verify dupe-free before index creation.
        dupe_after = 0
        async for _p in db.daily_reports.aggregate([
            {"$group": {"_id": "$doc_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]):
            dupe_after += 1
        if dupe_after > 0:
            print(f"⚠ still {dupe_after} dupe groups after repair; NOT creating unique index")
        else:
            try:
                await db.daily_reports.create_index(
                    "doc_id", unique=True, sparse=True, name="daily_reports_doc_id_uniq",
                )
                print("✓ created UNIQUE index daily_reports_doc_id_uniq")
            except Exception as exc:
                print(f"index create noted: {exc}")

    print("── TRACK 22.4b-followup-DR duplicate doc_id repair summary ──")
    for k, v in counts.items():
        print(f"  {k:32s} {v}")
    if dry_run:
        print("\nDRY RUN — no writes performed.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-production", action="store_true")
    args = ap.parse_args()
    sys.exit(asyncio.run(run(dry_run=args.dry_run, allow_production=args.allow_production)))


if __name__ == "__main__":
    main()
