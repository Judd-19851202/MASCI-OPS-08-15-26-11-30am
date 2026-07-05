#!/usr/bin/env python3
"""
DR-CUTOVER-001 · V1 daily_reports → ODS backfill

Idempotent, resumable, batched, dry-run-first.

Usage:
    python3 -m scripts.backfill_dr_v1_to_ods --dry-run
    python3 -m scripts.backfill_dr_v1_to_ods --live --batch-size 100
    python3 -m scripts.backfill_dr_v1_to_ods --live --resume-from <report_id>

Rules:
  1. Never mutates the source `daily_reports` documents.
  2. Uses the existing `ingest_dr_v1_report` (same code as the live
     submit hook) so backfill and live emission produce identical
     facts.
  3. Idempotent: re-running supersedes any previous facts for the
     same source_id — no duplicate `is_current=true` facts.
  4. Records every batch in `operational_ingestion_runs` with
     `trigger="backfill"`.
  5. Prints a summary at the end with totals + per-project counts.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from typing import Optional

# Ensure /app/backend is on sys.path when invoked as a script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:  # noqa: BLE001
    pass
from services.ods_spine import ingest_dr_v1_report  # type: ignore
from services.ods_spine.flags import ods_enabled, dr_v2_spine_emission_enabled  # type: ignore


def _load_env() -> tuple[str, str]:
    url = ""
    db_name = ""
    with open(os.path.join(os.path.dirname(__file__), "..", ".env")) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("MONGO_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("DB_NAME="):
                db_name = line.split("=", 1)[1].strip().strip('"')
    if not url or not db_name:
        raise RuntimeError("MONGO_URL / DB_NAME missing from backend/.env")
    return url, db_name


async def run_backfill(
    *,
    dry_run: bool,
    batch_size: int,
    resume_from: Optional[str],
    limit: Optional[int],
) -> None:
    url, db_name = _load_env()
    client = AsyncIOMotorClient(url)
    db = client[db_name]

    query = {}
    if resume_from:
        query["id"] = {"$gt": resume_from}

    total = await db.daily_reports.count_documents(query)
    print(f"[backfill] docs to process: {total}")
    print(f"[backfill] mode: {'DRY-RUN' if dry_run else 'LIVE'}  batch_size={batch_size}")
    print(f"[backfill] flags: ODS_ENABLED={ods_enabled()}  DR_V2_SPINE_EMISSION_ENABLED={dr_v2_spine_emission_enabled()}")
    if not dry_run and (not ods_enabled() or not dr_v2_spine_emission_enabled()):
        print("[backfill] ABORT: live mode requires both flags to be truthy in the environment.")
        return
    if not total:
        print("[backfill] nothing to do")
        return

    per_project: dict[str, int] = {}
    inserted_total = 0
    superseded_total = 0
    processed = 0
    skipped_no_anchor = 0
    empty_facts = 0
    started = time.time()

    cursor = db.daily_reports.find(query).sort("id", 1)
    async for rec in cursor:
        processed += 1
        rid = rec.get("id") or rec.get("doc_id") or rec.get("report_number") or ""
        if dry_run:
            # In dry-run mode, just simulate the builder and print
            # per-record counts without writing.
            from services.ods_spine.ingest import _build_facts_from_dr_v1_report  # type: ignore
            facts = _build_facts_from_dr_v1_report(rec)
            if not facts:
                empty_facts += 1
            per_project.setdefault(rec.get("project_number") or "?", 0)
            per_project[rec.get("project_number") or "?"] += len(facts)
            inserted_total += len(facts)
        else:
            out = await ingest_dr_v1_report(
                db, rec, actor="backfill", trigger="backfill",
            )
            if out.get("skipped"):
                if out.get("reason") == "no_report_id":
                    skipped_no_anchor += 1
                continue
            if out.get("facts_inserted", 0) == 0:
                empty_facts += 1
            inserted_total += out.get("facts_inserted", 0)
            superseded_total += out.get("facts_superseded", 0)
            per_project.setdefault(rec.get("project_number") or "?", 0)
            per_project[rec.get("project_number") or "?"] += out.get("facts_inserted", 0)

        if limit and processed >= limit:
            break
        if processed % batch_size == 0:
            elapsed = time.time() - started
            rate = processed / elapsed if elapsed else 0
            print(f"[backfill] processed={processed}/{total} · inserted={inserted_total} · superseded={superseded_total} · empty={empty_facts} · rate={rate:.1f}/s")

    elapsed = time.time() - started
    print()
    print("=" * 60)
    print(f"[backfill] DONE · {'DRY-RUN' if dry_run else 'LIVE'}")
    print(f"  processed:         {processed}")
    print(f"  facts inserted:    {inserted_total}")
    print(f"  facts superseded:  {superseded_total}")
    print(f"  no facts (empty):  {empty_facts}")
    print(f"  skipped (no id):   {skipped_no_anchor}")
    print(f"  elapsed:           {elapsed:.1f}s")
    print()

    # ── KPI snapshot recompute for touched (project, date) pairs ─────
    if not dry_run:
        print("[backfill] Recomputing KPI snapshots for touched (project, date) pairs...")
        from services.ods_spine.kpi import compute_kpi_snapshot  # type: ignore
        pairs = set()
        async for f in db["operational_facts"].find(
            {"source_type": "daily_report_v1", "is_current": True},
            {"_id": 0, "tenant_id": 1, "project_id": 1, "date": 1},
        ):
            pairs.add((f.get("tenant_id") or "masci", f.get("project_id"), f.get("date")))
        n_snaps = 0
        for tid, pid, date in pairs:
            if not pid or not date:
                continue
            try:
                await compute_kpi_snapshot(db, tenant_id=tid, project_id=pid, date=date)
                n_snaps += 1
            except Exception as e:  # noqa: BLE001
                print(f"  snapshot error for {pid}@{date}: {e}")
        print(f"[backfill] snapshots recomputed: {n_snaps}")
        print()

    print("  top 10 projects by facts:")
    for proj, cnt in sorted(per_project.items(), key=lambda kv: kv[1], reverse=True)[:10]:
        print(f"    {proj}: {cnt} facts")

    client.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="DR-CUTOVER-001 · V1 → ODS backfill")
    ap.add_argument("--dry-run", action="store_true", help="Compute counts only; do NOT write ODS facts")
    ap.add_argument("--live", action="store_true", help="Actually write facts (opposite of --dry-run)")
    ap.add_argument("--batch-size", type=int, default=100, help="Log progress every N docs")
    ap.add_argument("--resume-from", type=str, default=None, help="Resume after a given report id (sorted ascending)")
    ap.add_argument("--limit", type=int, default=None, help="Cap total docs processed (test/soak)")
    args = ap.parse_args()

    if not args.dry_run and not args.live:
        ap.error("Specify either --dry-run or --live (safety guard)")
    if args.dry_run and args.live:
        ap.error("Cannot use --dry-run and --live together")

    asyncio.run(run_backfill(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        resume_from=args.resume_from,
        limit=args.limit,
    ))


if __name__ == "__main__":
    main()
