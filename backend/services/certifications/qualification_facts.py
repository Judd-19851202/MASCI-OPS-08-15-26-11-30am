"""TRACK 23.10-B · ODS fact emitters for the qualifications engine.

Emits into `db.operational_facts` (the shared ODS spine collection).

Fact types
----------
* `qualification_certification_fact` — one per `safety_training_records`
  write (create · update · suspend · revoke · reinstate · renew) where
  `qualification_type` belongs to the engine enum.
* `qualification_expiration_fact` — daily digest of rows expiring in
  [0, `warn_days`] days. De-duped per (row, date).
* `qualification_assignment_fact` — emitted by CONSUMERS (Daily Report,
  trench inspection, scheduling) — not by this module. We only ship
  the schema constant here for downstream reuse.

Envelope
--------
Every fact is idempotent under a natural key
`(source_type, source_id, source_item_id, fact_type, is_current=True)`
via the existing `supersede_facts` primitive.

The engine registers three new `fact_type` values with the ODS model
via `model.EXTRA_FACT_TYPES` (see `model.py`).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Optional

from services.ods_spine.store import (
    COLL_FACTS, record_ingestion_run, supersede_facts, write_facts,
)
from services.ods_spine.model import now_iso

from .qualification_types import QUALIFICATION_ENGINE_TYPES, is_engine_type


TENANT_DEFAULT = "masci"
SOURCE_TYPE = "safety_form"            # existing enum in ods_spine.model
SOURCE_TYPE_ID = "safety_training_records"

FACT_TYPE_CERT = "qualification_certification_fact"
FACT_TYPE_EXPIRATION = "qualification_expiration_fact"
FACT_TYPE_ASSIGNMENT = "qualification_assignment_fact"


def _row_project_id(row: Mapping[str, Any]) -> str:
    """Qualification certs are org-scoped, not project-scoped. Store an
    empty project id (ODS envelope requires a truthy string; use a
    sentinel that filters cleanly downstream)."""
    return str(row.get("project_number") or "org")


def _row_date(row: Mapping[str, Any]) -> str:
    """Use `completed_date` if present, else today. Coerce to YYYY-MM-DD."""
    v = row.get("completed_date") or row.get("created_at") or now_iso()
    s = str(v)
    return s[:10] if len(s) >= 10 else datetime.now(timezone.utc).date().isoformat()


def _build_cert_fact(
    row: Mapping[str, Any],
    submitted_by: str,
    ingestion_run_id: str,
) -> Dict[str, Any]:
    return {
        "fact_id": uuid.uuid4().hex,
        "fact_type": FACT_TYPE_CERT,
        "tenant_id": TENANT_DEFAULT,
        "project_id": _row_project_id(row),
        "date": _row_date(row),
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_TYPE_ID,
        "source_item_id": row.get("id") or "",
        "source_version": int(row.get("source_version") or 0),
        "source_status": "full",
        "is_current": True,
        "submitted_by": submitted_by or "",
        "verified_identity": True,
        "confidence": 1.0,
        "trace_id": row.get("id") or "",
        "ingestion_run_id": ingestion_run_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "payload": {
            "qualification_id": row.get("id") or "",
            "qualification_type": row.get("qualification_type")
                or row.get("certification_type") or "",
            "qualification_sub_code":
                (row.get("type_metadata") or {}).get("sub_code") or "",
            "employee_id": row.get("employee_id") or "",
            "employee_master_id": row.get("employee_master_id") or "",
            "verification_status": row.get("verification_status") or "active",
            "issued_at": (str(row.get("completed_date") or ""))[:10],
            "expires_at": (str(row.get("expiration_date") or ""))[:10],
            "issuing_organization": row.get("issuing_organization")
                or row.get("issued_by") or "",
            "training_standard": row.get("training_standard") or "",
            "jurisdiction": row.get("jurisdiction") or "",
            "certificate_number": row.get("certificate_number") or "",
        },
    }


async def emit_qualification_certification_fact(
    db,
    row: Mapping[str, Any],
    *,
    actor: str = "system",
    trigger: str = "safety_training_records.write",
    submitted_by: str = "",
) -> Optional[str]:
    """Emit a single `qualification_certification_fact` for the given
    safety_training_records row. No-op for non-engine types."""
    qtype = row.get("qualification_type") or row.get("certification_type")
    if not is_engine_type(qtype):
        return None
    started = now_iso()
    run_id = await record_ingestion_run(
        db,
        source_type=SOURCE_TYPE,
        source_id=SOURCE_TYPE_ID,
        source_version=int(row.get("source_version") or 0),
        actor=actor,
        trigger=trigger,
        started_at=started,
    )
    fact = _build_cert_fact(row, submitted_by, run_id)
    # Supersede any prior current fact for the same qualification_id.
    await supersede_facts(
        db,
        source_type=SOURCE_TYPE, source_id=SOURCE_TYPE_ID,
        source_item_ids=[row.get("id") or ""],
    )
    await write_facts(db, [fact], ingestion_run_id=run_id)
    return fact["fact_id"]


async def emit_qualification_expiration_facts_daily(
    db,
    *,
    warn_days: int = 30,
    actor: str = "system",
    trigger: str = "qualification_expiration.daily",
) -> Dict[str, int]:
    """Daily emitter: one `qualification_expiration_fact` per active
    qualification expiring within `warn_days`. De-duped per (row, date)."""
    from .qualification_registry import COLL as REG_COLL

    today = datetime.now(timezone.utc).date().isoformat()
    warn_cutoff = (
        datetime.now(timezone.utc).date() + timedelta(days=warn_days)
    ).isoformat()

    q = {
        "$or": [
            {"verification_status": "active"},
            {"verification_status": {"$exists": False}},
        ],
        "expiration_date": {"$gte": today, "$lte": warn_cutoff},
    }
    rows = await db[REG_COLL].find(q, {"_id": 0}).to_list(20_000)
    rows = [r for r in rows if is_engine_type(
        r.get("qualification_type") or r.get("certification_type")
    )]

    if not rows:
        await record_ingestion_run(
            db,
            source_type=SOURCE_TYPE, source_id=SOURCE_TYPE_ID,
            source_version=0, actor=actor, trigger=trigger,
            facts_inserted=0,
        )
        return {"inserted": 0, "scanned": 0}

    run_id = await record_ingestion_run(
        db,
        source_type=SOURCE_TYPE, source_id=SOURCE_TYPE_ID,
        source_version=0, actor=actor, trigger=trigger,
    )
    # Idempotency: supersede any prior expiration facts emitted today
    # for the same rows.
    ids = [r.get("id") for r in rows if r.get("id")]
    # Only supersede our own subset — use `source_item_id` filter.
    await db[COLL_FACTS].update_many(
        {
            "source_type": SOURCE_TYPE,
            "source_id": SOURCE_TYPE_ID,
            "source_item_id": {"$in": ids},
            "fact_type": FACT_TYPE_EXPIRATION,
            "date": today,
            "is_current": True,
        },
        {"$set": {
            "is_current": False,
            "source_status": "superseded",
            "updated_at": now_iso(),
        }},
    )

    facts: List[Dict[str, Any]] = []
    for r in rows:
        exp = str(r.get("expiration_date") or "")[:10]
        days_left = (
            datetime.fromisoformat(exp).date()
            - datetime.now(timezone.utc).date()
        ).days if exp else -1
        facts.append({
            "fact_id": uuid.uuid4().hex,
            "fact_type": FACT_TYPE_EXPIRATION,
            "tenant_id": TENANT_DEFAULT,
            "project_id": "org",
            "date": today,
            "source_type": SOURCE_TYPE,
            "source_id": SOURCE_TYPE_ID,
            "source_item_id": r.get("id") or "",
            "source_version": 0,
            "source_status": "full",
            "is_current": True,
            "submitted_by": "system",
            "verified_identity": True,
            "confidence": 1.0,
            "trace_id": r.get("id") or "",
            "ingestion_run_id": run_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "payload": {
                "qualification_id": r.get("id") or "",
                "qualification_type": r.get("qualification_type")
                    or r.get("certification_type") or "",
                "employee_id": r.get("employee_id") or "",
                "expires_at": exp,
                "days_left": days_left,
                "warn_days": warn_days,
            },
        })
    result = await write_facts(db, facts, ingestion_run_id=run_id)
    return {"inserted": result.get("inserted", 0), "scanned": len(rows)}


__all__ = [
    "FACT_TYPE_CERT",
    "FACT_TYPE_EXPIRATION",
    "FACT_TYPE_ASSIGNMENT",
    "SOURCE_TYPE",
    "SOURCE_TYPE_ID",
    "emit_qualification_certification_fact",
    "emit_qualification_expiration_facts_daily",
]
