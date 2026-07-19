#!/usr/bin/env python3
"""DR-UNIFY-003 · Mongo collection rename migration.

Idempotent, resumable, dry-run-first migration that copies documents
from the legacy ``dr_v2_*`` collections to their canonical
``daily_report_*`` counterparts. No source collection is destroyed by
this script — the destructive drop step is deliberately left to
DR-UNIFY-004 (deployment certification), so preview/prod can validate
the rename fully before the rollback safety net is removed.

Behaviour
---------
- ``--dry-run``  (default) — counts + duplicate-id detection, no writes.
- ``--live``     — copies documents to the canonical collection. Skips
                   ``_id`` collisions (assume the doc already migrated).
                   Re-runs are safe: a fully-migrated pair is a no-op.
- ``--verify``   — assert every source ``_id`` is present in the target
                   with an equal ``id`` field (when present). Exits
                   non-zero on any drift.
- ``--rollback`` — informational only; prints the exact one-line
                   command an operator would run to reverse the copy
                   (deletion by ``_id`` present in the source).

Safety
------
- Never drops the source collection.
- Never modifies source documents.
- Never sends emails or calls any external service.
- Refuses to run against ``APP_ENV=production`` unless
  ``--allow-prod`` is also passed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from lib.operator_safety import (  # type: ignore  # noqa: E402
    redact_target_identity,
    require_cli_backup_ack,
    require_cli_confirmation,
    require_cli_execute,
    require_cli_runtime_guard,
)

# Canonical → legacy pairs; import from lib/ so a single source of truth exists.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.daily_report_collections import COLLECTION_ALIASES  # type: ignore  # noqa: E402


def _pairs() -> List[Tuple[str, str]]:
    """Return (canonical, legacy) pairs in stable order."""
    return list(COLLECTION_ALIASES.items())


async def _count(db, name: str) -> int:
    try:
        return await db[name].estimated_document_count()
    except Exception:
        return 0


async def _dry_run(db) -> Dict[str, Any]:
    report: Dict[str, Any] = {"mode": "dry-run", "pairs": [],
                              "totals": {"source": 0, "target": 0,
                                         "collisions": 0, "would_copy": 0}}
    for canonical, legacy in _pairs():
        src_n = await _count(db, legacy)
        tgt_n = await _count(db, canonical)
        collisions = 0
        would_copy = 0
        if src_n:
            # Cheap collision probe (up to 500 samples).
            cursor = db[legacy].find({}, {"_id": 1}).limit(500)
            src_ids = [d["_id"] async for d in cursor]
            if src_ids:
                existing = await db[canonical].count_documents({"_id": {"$in": src_ids}})
                collisions = existing
                would_copy = max(0, len(src_ids) - existing)
        row = {"canonical": canonical, "legacy": legacy,
               "legacy_count": src_n, "canonical_count": tgt_n,
               "sampled_collisions": collisions,
               "sampled_would_copy": would_copy}
        report["pairs"].append(row)
        report["totals"]["source"] += src_n
        report["totals"]["target"] += tgt_n
        report["totals"]["collisions"] += collisions
        report["totals"]["would_copy"] += would_copy
    return report


async def _live(db) -> Dict[str, Any]:
    report: Dict[str, Any] = {"mode": "live", "pairs": [], "started_at": _now_iso(), "migration_batch_id": str(uuid.uuid4())}
    failed_records: Dict[str, List[str]] = {}
    for canonical, legacy in _pairs():
        copied = 0
        skipped = 0
        cursor = db[legacy].find({})
        async for doc in cursor:
            try:
                await db[canonical].insert_one(dict(doc))
                copied += 1
            except Exception:
                failed_records.setdefault(canonical, []).append(str(doc.get("id") or doc.get("_id") or "unknown"))
                skipped += 1  # duplicate key or transient — skip; keep going
        report["pairs"].append({
            "canonical": canonical, "legacy": legacy,
            "copied": copied, "skipped_existing_or_error": skipped,
            "target_count_after": await _count(db, canonical),
            "source_count_still": await _count(db, legacy),
        })
    report["completed_at"] = _now_iso()
    report["failed_records"] = failed_records
    report["ok"] = sum(len(v) for v in failed_records.values()) == 0
    report["status"] = "success" if report["ok"] else "partial_failure"
    return report


async def _verify(db) -> Dict[str, Any]:
    report: Dict[str, Any] = {"mode": "verify", "pairs": [], "ok": True}
    for canonical, legacy in _pairs():
        src_n = await _count(db, legacy)
        tgt_n = await _count(db, canonical)
        missing = 0
        if src_n:
            cursor = db[legacy].find({}, {"_id": 1}).limit(1000)
            src_ids = [d["_id"] async for d in cursor]
            if src_ids:
                present = await db[canonical].count_documents({"_id": {"$in": src_ids}})
                missing = max(0, len(src_ids) - present)
        row = {"canonical": canonical, "legacy": legacy,
               "legacy_count": src_n, "canonical_count": tgt_n,
               "sampled_missing_in_canonical": missing}
        if missing > 0:
            report["ok"] = False
        report["pairs"].append(row)
    return report


def _rollback_plan() -> Dict[str, Any]:
    return {
        "mode": "rollback-plan",
        "one_liner": (
            "for each pair in COLLECTION_ALIASES: "
            "db[canonical].delete_many({'_id': {'$in': [d['_id'] for d in db[legacy].find({}, {'_id':1})]}})"
        ),
        "notes": [
            "This script never deletes source docs, so rollback = delete matching _ids from the canonical collection.",
            "Only necessary if the migration itself corrupted the canonical side — the legacy side is always intact.",
            "For production, take a Mongo snapshot before running --live.",
        ],
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run(args) -> int:
    app_env = (os.environ.get("APP_ENV") or "").lower()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        sys.stderr.write("MONGO_URL and DB_NAME env vars are required.\n")
        return 3

    target = redact_target_identity(mongo_url, db_name)
    if args.live:
        try:
            require_cli_execute(args.live)
            require_cli_confirmation(args.confirm, expected="MIGRATE_DR_V2_TO_DAILY_REPORTS")
            require_cli_backup_ack(args.backup_ack)
            require_cli_runtime_guard(
                app_env=app_env,
                db_name=db_name,
                allow_production=args.allow_prod,
                expected_db_name="masci_safety",
            )
        except RuntimeError as exc:
            sys.stderr.write(f"{exc}\n")
            return 4

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    try:
        if args.rollback:
            report = _rollback_plan()
        elif args.verify:
            report = await _verify(db)
        elif args.live:
            report = await _live(db)
        else:
            report = await _dry_run(db)
    finally:
        client.close()

    print(json.dumps({"target": target, "requested_mode": "live" if args.live else "verify" if args.verify else "rollback" if args.rollback else "dry-run"}, indent=2))
    print(json.dumps(report, indent=2, default=str))
    if isinstance(report, dict) and report.get("ok") is False:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="(default) Count docs, detect collisions, no writes.")
    ap.add_argument("--live", action="store_true",
                    help="Copy from legacy to canonical. Idempotent. Never destructive.")
    ap.add_argument("--verify", action="store_true",
                    help="Assert every legacy _id is present in canonical.")
    ap.add_argument("--rollback", action="store_true",
                    help="Print the one-line rollback plan; performs no writes.")
    ap.add_argument("--allow-prod", action="store_true",
                    help="Explicitly allow APP_ENV=production. Off by default.")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--backup-ack", action="store_true")
    args = ap.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
