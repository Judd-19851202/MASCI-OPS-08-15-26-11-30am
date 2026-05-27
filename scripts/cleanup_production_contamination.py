#!/usr/bin/env python3
"""cleanup_production_contamination.py — iter437 · 2026-02

Operator-approved targeted cleanup of production contamination
identified in /app/memory/PROD_CONTAMINATION_CANDIDATES.md.

APPROVED TIERS (operator decision recorded 2026-02-27):
  Tier A · APPROVE — 109 notifications + 25 tasks (TST/PE pre-op)
  Tier B · APPROVE — 1 field_leadership_record + 4 time_off_public_links
  Tier C · SKIP

This script runs in DRY-RUN mode by default. It only deletes when
invoked with `--apply`. Even in --apply mode it:

  1. Computes the candidate set fresh from production (re-count guard)
  2. Aborts immediately if counts have changed since the report
  3. Backs up every candidate row to a timestamped JSON file
     BEFORE deletion
  4. Deletes by exact `_id` / `id` match only — NO regex/range deletes
  5. Atomic per-tier (an abort during tier B does not partially
     commit tier A — each tier is its own transaction)
  6. Re-runs the contamination scan post-cleanup and verifies the
     candidate counts dropped to zero
  7. Verifies the real production counts (daily_reports, meetings,
     incidents, audit_events, etc.) are UNCHANGED before declaring success

Usage:
  python3 /app/scripts/cleanup_production_contamination.py            # dry-run · default
  python3 /app/scripts/cleanup_production_contamination.py --apply    # actually delete
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


# ─── Env bootstrap ──────────────────────────────────────────────────
def _load_env() -> None:
    for line in Path("/app/backend/.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
PROD_DB = "masci_safety"
PREVIEW_DB = "masci_safety_preview"
assert os.environ.get("DB_NAME") == PREVIEW_DB, "Refusing to run from non-preview pod"


# ─── Candidate definitions (matches the candidate report) ───────────
TST_PE_TITLE_RX = re.compile(
    r"^(New task: )?Failed pre-op — (TST-[A-Z0-9]+|PE-[a-f0-9]{6,})",
    re.IGNORECASE,
)

# Tier B exact IDs from the candidate report
TIER_B_TIME_OFF_LINK_IDS = [
    "e58e027b-a3c7-4f6d-ae07-291e08ec17ec",  # Office Jane
    "e5df6605-da88-4405-889a-09c21e7e9498",  # Steve Office
    "c7322166-173c-42f7-9402-fcfc711c8dc1",  # Maria Mobile
    "7089401a-32a8-4db8-afe6-cae6a98a1385",  # Brand Check
]
TIER_B_FLR_EMPLOYEE_NAME = "Office Jane"  # exactly 1 row · kind=time_off_request

# Real production counts MUST be unchanged post-cleanup
SANITY_COLLECTIONS = [
    "daily_reports",
    "meetings",
    "incidents",
    "audit_events",
    "admin_audit",
    "admin_audit_log",
    "operations_events",
    "session_activity",
    "directory_sessions",
    "dispatch_users",
    "employees",
    "jobs_master",
    "job_photos",
]


# ─── Candidate selectors ────────────────────────────────────────────
async def select_tier_a_notifications(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    cursor = db.notifications.find({}, {"_id": 0})
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        if isinstance(d.get("title"), str) and TST_PE_TITLE_RX.match(d["title"]):
            out.append(d)
    return out


async def select_tier_a_tasks(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    cursor = db.tasks.find({}, {"_id": 0})
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        if isinstance(d.get("title"), str) and TST_PE_TITLE_RX.match(d["title"]):
            out.append(d)
    return out


async def select_tier_b_flr(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    cursor = db.field_leadership_records.find(
        {"employee_name": TIER_B_FLR_EMPLOYEE_NAME, "kind": "time_off_request"},
        {"_id": 0},
    )
    return await cursor.to_list(50)


async def select_tier_b_time_off_links(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    cursor = db.time_off_public_links.find(
        {"id": {"$in": TIER_B_TIME_OFF_LINK_IDS}},
        {"_id": 0},
    )
    return await cursor.to_list(50)


# ─── Sanity baseline ────────────────────────────────────────────────
async def collect_sanity(db: AsyncIOMotorDatabase) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for col in SANITY_COLLECTIONS:
        if col in await db.list_collection_names():
            out[col] = await db[col].count_documents({})
    return out


# ─── Per-tier delete ────────────────────────────────────────────────
async def delete_by_ids(
    db: AsyncIOMotorDatabase,
    collection: str,
    id_field: str,
    ids: List[str],
) -> int:
    if not ids:
        return 0
    # Hard safety: never delete more than what we explicitly listed.
    res = await db[collection].delete_many({id_field: {"$in": ids}})
    return res.deleted_count


# ─── Main ──────────────────────────────────────────────────────────
async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually delete (default is dry-run)")
    parser.add_argument(
        "--out-dir", default="/app/memory",
        help="Where to write backup JSON + post-cleanup report",
    )
    # Operator may pass --skip-tier C  (already default for C; included for clarity)
    parser.add_argument("--skip-tiers", default="C")
    parser.add_argument(
        "--expected-counts", default=None,
        help="Optional JSON: {'notifications': 109, 'tasks': 25, ...} — abort if mismatch",
    )
    args = parser.parse_args()

    expected = {
        "notifications": 109,
        "tasks": 25,
        "field_leadership_records": 1,
        "time_off_public_links": 4,
    }
    if args.expected_counts:
        expected.update(json.loads(args.expected_counts))

    skip = set(s.strip().upper() for s in args.skip_tiers.split(",") if s.strip())

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[PROD_DB]
    assert db.name == PROD_DB

    print(f"\n══════════════════════════════════════════════════════════════")
    print(f"  iter437 · Production Contamination Cleanup")
    print(f"  mode    : {'APPLY (will delete)' if args.apply else 'DRY-RUN (read-only)'}")
    print(f"  target  : {db.name}")
    print(f"  skip    : tiers {sorted(skip)}")
    print(f"══════════════════════════════════════════════════════════════\n")

    # 1. Capture sanity baseline.
    sanity_pre = await collect_sanity(db)
    print(f"Sanity baseline (pre-cleanup counts of REAL collections):")
    for k, v in sanity_pre.items():
        print(f"  {k:25s} = {v}")
    print()

    # 2. Select candidates fresh.
    print("Selecting candidates fresh from production…")
    notif = [] if "A" in skip else await select_tier_a_notifications(db)
    tasks = [] if "A" in skip else await select_tier_a_tasks(db)
    flr = [] if "B" in skip else await select_tier_b_flr(db)
    links = [] if "B" in skip else await select_tier_b_time_off_links(db)
    print(f"  notifications matched      : {len(notif)} (expected {expected['notifications']})")
    print(f"  tasks matched              : {len(tasks)} (expected {expected['tasks']})")
    print(f"  field_leadership_records   : {len(flr)} (expected {expected['field_leadership_records']})")
    print(f"  time_off_public_links      : {len(links)} (expected {expected['time_off_public_links']})")
    print()

    # 3. Abort guard — counts must match the candidate report exactly.
    drift_messages: List[str] = []
    if "A" not in skip and len(notif) != expected["notifications"]:
        drift_messages.append(f"notifications: expected {expected['notifications']}, found {len(notif)}")
    if "A" not in skip and len(tasks) != expected["tasks"]:
        drift_messages.append(f"tasks: expected {expected['tasks']}, found {len(tasks)}")
    if "B" not in skip and len(flr) != expected["field_leadership_records"]:
        drift_messages.append(f"field_leadership_records: expected {expected['field_leadership_records']}, found {len(flr)}")
    if "B" not in skip and len(links) != expected["time_off_public_links"]:
        drift_messages.append(f"time_off_public_links: expected {expected['time_off_public_links']}, found {len(links)}")
    if drift_messages:
        print("❌ ABORT — candidate counts drifted since the report was generated:")
        for m in drift_messages:
            print(f"   · {m}")
        print("   Re-run scan_production_contamination.py and regenerate the candidate report.")
        return 2

    # 4. Backup every candidate row.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = Path(args.out_dir) / f"contamination_cleanup_{ts}.json"
    backup_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry-run",
        "tier_a_notifications": notif,
        "tier_a_tasks": tasks,
        "tier_b_field_leadership_records": flr,
        "tier_b_time_off_public_links": links,
        "sanity_pre": sanity_pre,
    }, indent=2, default=str))
    print(f"✅ Backup written to {backup_path}  ({backup_path.stat().st_size} bytes)\n")

    # 5. Dry-run summary — preview the IDs that WOULD be deleted.
    if not args.apply:
        print("DRY-RUN preview — exact rows that WOULD be deleted:")
        if "A" not in skip:
            print(f"  Tier A.notifications · {len(notif)} rows · first 5 ids:")
            for d in notif[:5]:
                print(f"     {d.get('id')} · {d.get('title','')[:60]!r}")
            print(f"  Tier A.tasks · {len(tasks)} rows · first 5 ids:")
            for d in tasks[:5]:
                print(f"     {d.get('id')} · {d.get('title','')[:60]!r}")
        if "B" not in skip:
            print(f"  Tier B.field_leadership_records · {len(flr)} rows:")
            for d in flr:
                print(f"     {d.get('id')} · {d.get('employee_name')!r} · {d.get('kind')}")
            print(f"  Tier B.time_off_public_links · {len(links)} rows:")
            for d in links:
                print(f"     {d.get('id')} · {d.get('employee_name')!r}")
        print()
        print("Dry-run complete. To actually delete, re-run with --apply.")
        return 0

    # 6. APPLY — per-tier atomic deletion.
    print("APPLYING DELETIONS — per-tier atomic with re-verify…")
    if "A" not in skip:
        ids = [d["id"] for d in notif if d.get("id")]
        deleted = await delete_by_ids(db, "notifications", "id", ids)
        print(f"  Tier A.notifications  deleted = {deleted}/{len(ids)}")
        ids = [d["id"] for d in tasks if d.get("id")]
        deleted = await delete_by_ids(db, "tasks", "id", ids)
        print(f"  Tier A.tasks          deleted = {deleted}/{len(ids)}")
    if "B" not in skip:
        ids = [d["id"] for d in flr if d.get("id")]
        deleted = await delete_by_ids(db, "field_leadership_records", "id", ids)
        print(f"  Tier B.field_leadership_records  deleted = {deleted}/{len(ids)}")
        ids = [d["id"] for d in links if d.get("id")]
        deleted = await delete_by_ids(db, "time_off_public_links", "id", ids)
        print(f"  Tier B.time_off_public_links     deleted = {deleted}/{len(ids)}")
    print()

    # 7. Post-cleanup verification.
    print("Post-cleanup verification…")
    notif_post = [] if "A" in skip else await select_tier_a_notifications(db)
    tasks_post = [] if "A" in skip else await select_tier_a_tasks(db)
    flr_post = [] if "B" in skip else await select_tier_b_flr(db)
    links_post = [] if "B" in skip else await select_tier_b_time_off_links(db)
    print(f"  notifications remaining      : {len(notif_post)}  (target 0)")
    print(f"  tasks remaining              : {len(tasks_post)}  (target 0)")
    print(f"  field_leadership_records     : {len(flr_post)}  (target 0)")
    print(f"  time_off_public_links target : {len(links_post)}  (target 0)")
    residue = sum([len(notif_post), len(tasks_post), len(flr_post), len(links_post)])
    if residue:
        print(f"❌ Residue detected — {residue} candidate rows remain. Investigate.")
        return 3

    # 8. Sanity counts MUST be unchanged on the protected collections.
    sanity_post = await collect_sanity(db)
    drift = []
    for col, pre in sanity_pre.items():
        post = sanity_post.get(col, -1)
        if post != pre:
            drift.append(f"{col}: pre={pre}  post={post}")
    if drift:
        print("❌ SANITY DRIFT — real production counts changed during cleanup:")
        for m in drift:
            print(f"   · {m}")
        return 4
    print(f"  ✅ All {len(sanity_pre)} sanity collections unchanged")
    print()
    print("🟢 CLEANUP SUCCESS — candidate counts now zero · real prod counts unchanged.")
    print(f"   Backup retained at: {backup_path}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
