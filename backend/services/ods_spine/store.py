"""ODS-001 · Spine store — the ONLY module allowed to write to spine collections.

Write primitives:
    write_facts()          — idempotent supersede-then-insert
    supersede_facts()      — mark superseded without re-insert
    record_ingestion_run() — audit trail entry

Read primitives live in services/ods_spine/query.py.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional

from .model import validate_fact_envelope, now_iso


COLL_FACTS = "operational_facts"
COLL_RUNS = "operational_ingestion_runs"
COLL_SNAPSHOTS = "operational_kpi_snapshots"
COLL_PROJECT_CFG = "project_operational_config"
COLL_LINKS = "operational_fact_links"


async def ensure_indexes(db) -> None:
    """Idempotent index creation. Called from route registration."""
    try:
        await db[COLL_FACTS].create_index(
            [("tenant_id", 1), ("project_id", 1), ("date", 1), ("fact_type", 1), ("is_current", 1)],
            name="ods_facts_hot_query",
        )
        await db[COLL_FACTS].create_index(
            [("tenant_id", 1), ("source_type", 1), ("source_id", 1), ("fact_type", 1), ("is_current", 1), ("date", 1)],
            name="ods_facts_source_window",
        )
        await db[COLL_FACTS].create_index(
            [("source_type", 1), ("source_id", 1), ("source_item_id", 1), ("fact_type", 1)],
            name="ods_facts_dedupe_key",
        )
        await db[COLL_FACTS].create_index("ingestion_run_id", name="ods_facts_run")
        await db[COLL_FACTS].create_index("fact_id", unique=True, name="ods_facts_id_unique")
        await db[COLL_RUNS].create_index("run_id", unique=True, name="ods_runs_id_unique")
        await db[COLL_RUNS].create_index(
            [("source_type", 1), ("source_id", 1), ("started_at", -1)],
            name="ods_runs_by_source",
        )
        await db[COLL_SNAPSHOTS].create_index(
            [("tenant_id", 1), ("project_id", 1), ("date", 1), ("window", 1)],
            unique=True, name="ods_snapshots_key",
        )
        await db[COLL_PROJECT_CFG].create_index("project_id", unique=True, name="ods_project_cfg_id")
        await db[COLL_LINKS].create_index(
            [("from_fact_id", 1), ("link_type", 1)],
            name="ods_links_from",
        )
        await db[COLL_LINKS].create_index(
            [("to_fact_id", 1), ("link_type", 1)],
            name="ods_links_to",
        )
    except Exception:  # noqa: BLE001 — index creation is best-effort at boot
        pass


async def record_ingestion_run(
    db,
    *,
    source_type: str,
    source_id: str,
    source_version: int,
    actor: str,
    trigger: str,
    ok: bool = True,
    error: Optional[str] = None,
    facts_inserted: int = 0,
    facts_superseded: int = 0,
    facts_unchanged: int = 0,
    started_at: Optional[str] = None,
) -> str:
    run_id = uuid.uuid4().hex
    finished = now_iso()
    doc = {
        "run_id": run_id,
        "source_type": source_type,
        "source_id": source_id,
        "source_version": int(source_version or 0),
        "started_at": started_at or finished,
        "finished_at": finished,
        "facts_inserted": facts_inserted,
        "facts_superseded": facts_superseded,
        "facts_unchanged": facts_unchanged,
        "ok": bool(ok),
        "error": error,
        "actor": actor,
        "trigger": trigger,
    }
    await db[COLL_RUNS].insert_one(doc)
    return run_id


async def supersede_facts(
    db,
    *,
    source_type: str,
    source_id: str,
    source_item_ids: Optional[Iterable[str]] = None,
) -> int:
    """Mark existing facts for this source as superseded. Returns count."""
    q: Dict[str, Any] = {
        "source_type": source_type,
        "source_id": source_id,
        "is_current": True,
    }
    if source_item_ids is not None:
        q["source_item_id"] = {"$in": list(source_item_ids)}
    res = await db[COLL_FACTS].update_many(
        q,
        {"$set": {
            "is_current": False,
            "source_status": "superseded",
            "updated_at": now_iso(),
        }},
    )
    return res.modified_count or 0


async def write_facts(
    db,
    facts: List[Dict[str, Any]],
    *,
    ingestion_run_id: str,
) -> Dict[str, int]:
    """Insert a batch of validated facts. Returns counters.

    Caller is responsible for having already called `supersede_facts` for
    the same `(source_type, source_id)` so `is_current=True` remains
    monotonically owned by the newest run.
    """
    counters = {"inserted": 0, "rejected": 0}
    if not facts:
        return counters

    stamped: List[Dict[str, Any]] = []
    now = now_iso()
    for f in facts:
        if not f.get("fact_id"):
            f["fact_id"] = uuid.uuid4().hex
        f.setdefault("ingestion_run_id", ingestion_run_id)
        f.setdefault("is_current", True)
        f.setdefault("source_status", "full")
        f.setdefault("confidence", 1.0)
        f.setdefault("created_at", now)
        f["updated_at"] = now
        err = validate_fact_envelope(f)
        if err:
            counters["rejected"] += 1
            continue
        stamped.append(f)

    if stamped:
        await db[COLL_FACTS].insert_many(stamped, ordered=False)
        counters["inserted"] = len(stamped)
    return counters
