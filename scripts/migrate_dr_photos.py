#!/usr/bin/env python3
"""Batch G · GAP-1 — Daily Report photo bloat remediation.

Walks `daily_reports` in a target DB. For each DR, finds inline base64
`data:image/...` photos at three nested paths:

    1. doc.photos[]
    2. doc.subcontractors[*].photos[]
    3. doc.materials[*].ticket_photos[]

Each inline data-URL is uploaded to R2 via `photo_storage.upload_data_url`
and replaced with the returned `photo://` reference. The replacement is
idempotent: anything that is already a `photo://` reference (or is empty)
is skipped.

SAFETY:
 - --dry-run is the default. NOTHING is written to Mongo or R2 until
   --apply is passed explicitly.
 - Refuses to operate on the live `masci_safety` database unless
   --i-know-this-is-prod is passed.
 - Per-DR transaction: each DR is either fully migrated and saved, or
   skipped entirely on first error. Originals are preserved on disk
   if --backup-dir is given (writes the pre-migration JSON to that dir).

USAGE:
    # Test against drill DB (safe):
    python3 scripts/migrate_dr_photos.py \\
        --target-db masci_restore_drill_2026_05_30 --apply

    # Production (requires explicit acknowledgement):
    python3 scripts/migrate_dr_photos.py \\
        --target-db masci_safety --i-know-this-is-prod --apply
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Resolve backend imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# Load backend/.env so photo_storage helpers can find their R2 credentials
_env_file = ROOT / "backend" / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _v = _v.strip().strip('"').strip("'")
        os.environ.setdefault(_k.strip(), _v)

from pymongo import MongoClient  # noqa: E402

# photo_storage helper (already-built infrastructure, see backend/photo_storage.py)
import photo_storage as _ps  # noqa: E402


def _is_data_url(s) -> bool:
    return isinstance(s, str) and s.startswith("data:image/")


def _walk_photo_list(lst, source_id: str, stats: dict, dry_run: bool = False):
    """Walk a list of photo strings, replacing data:URLs with photo:// refs.
    Mutates `lst` in place. `stats` is updated with bytes_in / bytes_out / count_migrated.
    In dry_run mode, NO upload is performed and the entry is left unchanged
    (size savings estimated using a stand-in photo:// reference length)."""
    if not isinstance(lst, list):
        return
    for i, item in enumerate(lst):
        if _is_data_url(item):
            stats["count_migrated"] += 1
            stats["bytes_in"] += len(item)
            if dry_run:
                # Estimate the size of a photo:// reference without uploading.
                # Typical reference: photo://<bucket>/photos/<yyyy>/<mm>/<source>/<n>
                # Conservative upper bound ~ 100 chars.
                stats["bytes_out"] += 100
            else:
                ref = asyncio.run(_ps.upload_data_url(item, source_id=source_id))
                lst[i] = ref
                stats["bytes_out"] += len(ref)
        # if already photo:// or empty, skip


def migrate_dr(doc: dict, stats: dict, dry_run: bool = False) -> bool:
    """Mutate doc in-place. Returns True if any change was made (or would be made in dry_run)."""
    dr_id = doc.get("id", "unknown")[:32]
    source_id = f"dr_{dr_id}"
    initial_count = stats["count_migrated"]

    # Path 1: doc.photos[]
    _walk_photo_list(doc.get("photos"), source_id, stats, dry_run=dry_run)

    # Path 2: doc.subcontractors[*].photos[]
    for sub in (doc.get("subcontractors") or []):
        if isinstance(sub, dict):
            _walk_photo_list(sub.get("photos"), f"{source_id}_sub", stats, dry_run=dry_run)

    # Path 3: doc.materials[*].ticket_photos[]
    for mat in (doc.get("materials") or []):
        if isinstance(mat, dict):
            _walk_photo_list(mat.get("ticket_photos"), f"{source_id}_mat", stats, dry_run=dry_run)

    return stats["count_migrated"] > initial_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate inline base64 photos out of daily_reports.")
    parser.add_argument("--target-db", required=True, help="Target Mongo database name")
    parser.add_argument("--apply", action="store_true", help="Actually write to Mongo/R2 (default is dry-run)")
    parser.add_argument("--i-know-this-is-prod", action="store_true", help="Required to operate on live masci_safety")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N DRs (for staged rollout)")
    parser.add_argument("--backup-dir", default=None, help="If set, write original JSON of each migrated DR here before save")
    parser.add_argument("--mongo-url", default=None, help="Override MONGO_URL")
    args = parser.parse_args()

    if args.target_db == "masci_safety" and not args.i_know_this_is_prod:
        print("REFUSING: --target-db=masci_safety requires --i-know-this-is-prod")
        return 2

    mongo_url = args.mongo_url or os.environ.get("MONGO_URL")
    if not mongo_url:
        env_file = ROOT / "backend" / ".env"
        for line in env_file.read_text().splitlines():
            if line.startswith("MONGO_URL="):
                mongo_url = line.split("=", 1)[1].strip().strip('"')
                break
    if not mongo_url:
        print("REFUSING: MONGO_URL not configured")
        return 2

    if not _ps.is_configured():
        print("REFUSING: photo_storage is not configured (R2 credentials missing). Aborting.")
        return 3

    print(f"{'=' * 60}")
    print("  GAP-1 DR PHOTO BLOAT MIGRATION")
    print(f"  Target DB     : {args.target_db}")
    print(f"  Mode          : {'APPLY (live)' if args.apply else 'DRY-RUN (no writes)'}")
    print(f"  Photo storage : {'configured' if _ps.is_configured() else 'NOT CONFIGURED'}")
    print(f"  Backup dir    : {args.backup_dir or '(none)'}")
    print(f"{'=' * 60}")

    if args.backup_dir:
        Path(args.backup_dir).mkdir(parents=True, exist_ok=True)

    mc = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
    db = mc[args.target_db]
    coll = db.daily_reports
    total = coll.count_documents({})
    if args.limit:
        total = min(total, args.limit)
    print(f"  DRs to scan   : {total}")
    print()

    started = time.time()
    summary = {
        "drs_scanned": 0,
        "drs_changed": 0,
        "drs_skipped_clean": 0,
        "drs_failed": 0,
        "count_migrated": 0,
        "bytes_in": 0,
        "bytes_out": 0,
        "errors": [],
    }
    cursor = coll.find({}, {"_id": 0})
    if args.limit:
        cursor = cursor.limit(args.limit)

    for i, doc in enumerate(cursor, 1):
        summary["drs_scanned"] += 1
        stats = {"count_migrated": 0, "bytes_in": 0, "bytes_out": 0}
        dr_id = (doc.get("id") or "?")[:8]
        try:
            changed = migrate_dr(doc, stats, dry_run=not args.apply)
            summary["count_migrated"] += stats["count_migrated"]
            summary["bytes_in"] += stats["bytes_in"]
            summary["bytes_out"] += stats["bytes_out"]
            if not changed:
                summary["drs_skipped_clean"] += 1
                continue
            summary["drs_changed"] += 1
            saved_kb = (stats["bytes_in"] - stats["bytes_out"]) / 1024
            print(f"  [{i:>3}/{total}] {dr_id}: migrated {stats['count_migrated']:>2} photos · saved {saved_kb:.1f} KB")

            if args.apply:
                if args.backup_dir:
                    orig = coll.find_one({"id": doc["id"]}, {"_id": 0})
                    (Path(args.backup_dir) / f"{dr_id}.json").write_text(json.dumps(orig, default=str))
                coll.replace_one({"id": doc["id"]}, doc)
        except Exception as e:
            summary["drs_failed"] += 1
            summary["errors"].append({"id": dr_id, "err": str(e)[:200]})
            print(f"  [{i:>3}/{total}] {dr_id}: FAIL · {type(e).__name__}: {str(e)[:120]}")

    elapsed = time.time() - started
    print()
    print("=" * 60)
    print(f"  SUMMARY ({'DRY-RUN' if not args.apply else 'APPLIED'})")
    print(f"  DRs scanned         : {summary['drs_scanned']}")
    print(f"  DRs that would change: {summary['drs_changed']}")
    print(f"  DRs already clean    : {summary['drs_skipped_clean']}")
    print(f"  DRs failed           : {summary['drs_failed']}")
    print(f"  Photos to migrate    : {summary['count_migrated']}")
    print(f"  Bytes in (base64)    : {summary['bytes_in']:>14,} ({summary['bytes_in']/1024/1024:.1f} MB)")
    print(f"  Bytes out (refs)     : {summary['bytes_out']:>14,} ({summary['bytes_out']/1024/1024:.4f} MB)")
    savings_mb = (summary['bytes_in'] - summary['bytes_out']) / 1024 / 1024
    pct = (savings_mb / (summary['bytes_in']/1024/1024) * 100) if summary['bytes_in'] else 0
    print(f"  Net savings          : {savings_mb:.1f} MB ({pct:.1f}%)")
    print(f"  Elapsed              : {elapsed:.1f} s")
    print(f"{'=' * 60}")
    if summary["errors"]:
        print()
        print("ERRORS (first 5):")
        for e in summary["errors"][:5]:
            print(f"  {e}")
    return 0 if summary["drs_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
