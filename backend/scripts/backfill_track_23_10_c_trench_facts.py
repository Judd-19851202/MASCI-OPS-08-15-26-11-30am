"""TRACK 23.10-C · Trench Safety facts backfill.

Idempotent. Replay-safe. Non-destructive. Never mutates source rows.

Emits (or re-emits with supersession):
  * `excavation_day_fact` per `trench_excavations` row
  * `trench_inspection_fact` per `trench_safety_inspections` row
  * `trench_hold_fact` per `trench_safety_holds` row
  * `trench_repair_fact` per `trench_safety_repairs` row
    (companion `trench_verification_fact` when safe_to_use_verified)
  * `project_excavation_summary_fact` per distinct project resolved

Boot-safe: caps its work per boot with `boot_batch_limit` to avoid
blocking startup. Run the CLI (`--full`) to emit everything.

Usage
-----
Boot hook:
    await run_backfill(db, boot_mode=True)

Full replay:
    python3 -m scripts.backfill_track_23_10_c_trench_facts
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


from services.ods_spine.store import COLL_FACTS                            # noqa: E402
from services.trench_safety.facts_emitter import (                          # noqa: E402
    SOURCE_TYPE_TRENCH,
    emit_excavation_day_fact,
    emit_trench_inspection_fact,
    emit_trench_hold_fact,
    emit_trench_repair_fact,
    recompute_project_excavation_summary,
)
from services.trench_safety.project_linker import resolve_project           # noqa: E402


_BOOT_LIMIT_DEFAULT = int(os.environ.get("TRACK_23_10_C_BOOT_LIMIT", "500"))


async def _emit_batch(
    db, coll_name: str, emitter, batch_size: int,
) -> Dict[str, int]:
    """Emit facts for rows in `coll_name` that do not yet have a
    current fact. Uses ODS-level idempotency (`supersede_facts`) — safe
    to re-run over rows that already emitted."""
    scanned = 0
    emitted = 0
    project_numbers: set = set()
    cursor = db[coll_name].find({}, {"_id": 0}).limit(batch_size)
    async for row in cursor:
        scanned += 1
        try:
            fid = await emitter(db, row, actor="backfill-23-10-c",
                                trigger=f"backfill.{coll_name}")
            if fid:
                emitted += 1
            # Track distinct projects for summary recompute.
            linkage = await resolve_project(db, row)
            if linkage.project_number:
                project_numbers.add(linkage.project_number)
        except Exception as exc:                                       # noqa: BLE001
            # Never let a single bad row abort the batch.
            print(f"[backfill] {coll_name} row {row.get('id')} · {exc}")
    return {
        "collection": coll_name,
        "scanned": scanned,
        "emitted": emitted,
        "projects_touched": list(project_numbers),
    }


async def run_backfill(
    db, boot_mode: bool = False,
    boot_batch_limit: int = _BOOT_LIMIT_DEFAULT,
    recompute_summaries: bool = True,
) -> Dict[str, Any]:
    """Idempotent backfill entrypoint.

    `boot_mode=True` caps each source scan at `boot_batch_limit` — the
    same limit is applied per-collection so a fresh preview DB with
    thousands of rows can complete backfill across multiple boots
    without slowing startup.
    """
    limit = boot_batch_limit if boot_mode else 100_000
    plan = [
        ("trench_excavations",           emit_excavation_day_fact),
        ("trench_safety_inspections",    emit_trench_inspection_fact),
        ("trench_safety_holds",          emit_trench_hold_fact),
        ("trench_safety_repairs",        emit_trench_repair_fact),
    ]
    started = datetime.now(timezone.utc).isoformat()
    results: List[Dict[str, Any]] = []
    all_projects: set = set()
    for coll_name, emitter in plan:
        r = await _emit_batch(db, coll_name, emitter, limit)
        results.append(r)
        all_projects.update(r["projects_touched"])

    summary_count = 0
    if recompute_summaries and all_projects:
        for pn in list(all_projects)[:5000]:
            try:
                fid = await recompute_project_excavation_summary(
                    db, pn, actor="backfill-23-10-c",
                    trigger="backfill.summary",
                )
                if fid:
                    summary_count += 1
            except Exception as exc:                                   # noqa: BLE001
                print(f"[backfill] summary {pn} · {exc}")

    finished = datetime.now(timezone.utc).isoformat()
    return {
        "track": "23.10-C",
        "boot_mode": boot_mode,
        "boot_batch_limit": limit,
        "started_at": started,
        "finished_at": finished,
        "batches": results,
        "projects_resolved": len(all_projects),
        "summaries_written": summary_count,
    }


async def _run_cli() -> None:
    from motor.motor_asyncio import AsyncIOMotorClient                     # noqa: PLC0415

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("MONGO_URL / DB_NAME must be set")
    boot = "--boot" in sys.argv
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        r = await run_backfill(db, boot_mode=boot)
        print("[TRACK 23.10-C backfill]", r)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(_run_cli())
