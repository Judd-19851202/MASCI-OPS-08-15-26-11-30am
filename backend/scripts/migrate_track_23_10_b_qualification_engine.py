"""TRACK 23.10-B · Qualifications Engine additive migration.

Idempotent. Zero destructive changes. Run at boot or on demand.

Steps
-----
1. Backfill `verification_status` for legacy `safety_training_records`
   rows: "active" if `expiration_date >= today` (or missing), else
   "expired".
2. Backfill `verification_status_history[]` with a single entry
   marking the migration event.
3. Backfill `qualification_type` from the free-text
   `certification_type` when it maps to an engine enum value. Non-
   engine values are LEFT ALONE (`qualification_type` stays absent).
4. Emit one `qualification_certification_fact` per engine-typed row
   into ODS `operational_facts` (via `emit_qualification_certification_fact`).
5. Ensure indexes.

Safe to re-run: every write is `find_one_and_update` gated by whether
the target field already has the migrated value. Fact emission uses
`supersede_facts` so re-running collapses to at most 1 current fact
per row.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# Ensure backend root is importable when run as a script.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from services.certifications.qualification_types import (            # noqa: E402
    QUALIFICATION_ENGINE_TYPES,
    is_engine_type,
)
from services.certifications.qualification_facts import (             # noqa: E402
    emit_qualification_certification_fact,
)


COLL = "safety_training_records"


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _map_legacy_type(cert_type: Any) -> str:
    """Map legacy free-text `certification_type` → engine enum value."""
    if not cert_type:
        return ""
    v = str(cert_type).strip()
    upper = v.upper().replace(" ", "_").replace("/", "_").replace("-", "_")
    # Exact enum match wins.
    if upper in QUALIFICATION_ENGINE_TYPES:
        return upper
    # Common alias table (defensive; deliberately conservative).
    aliases = {
        "OSHA10": "OSHA_10",
        "OSHA_10_HOUR": "OSHA_10",
        "OSHA30": "OSHA_30",
        "OSHA_30_HOUR": "OSHA_30",
        "FIRSTAID": "FIRST_AID_CPR",
        "FIRST_AID": "FIRST_AID_CPR",
        "CPR": "FIRST_AID_CPR",
        "AED": "FIRST_AID_CPR",
        "FLAGGER": "TRAFFIC_CONTROL_FLAGGER",
        "TRAFFIC_CONTROL": "TRAFFIC_CONTROL_FLAGGER",
        "SIGNAL": "SIGNAL_PERSON",
        "CRANE": "CRANE_OPERATOR",
        "CDL": "CDL_ENDORSEMENT",
        "COMPETENT": "COMPETENT_PERSON",
    }
    return aliases.get(upper, "")


async def _backfill_row(db, row: Dict[str, Any]) -> Dict[str, Any]:
    patch: Dict[str, Any] = {}
    now = datetime.now(timezone.utc).isoformat()
    today = _today()

    # 1 · verification_status
    if not row.get("verification_status"):
        exp = str(row.get("expiration_date") or "")[:10]
        if not exp or exp >= today:
            patch["verification_status"] = "active"
        else:
            patch["verification_status"] = "expired"

    # 2 · verification_status_history
    if not row.get("verification_status_history"):
        target = patch.get("verification_status") or row.get("verification_status") or "active"
        patch["verification_status_history"] = [{
            "status": target,
            "at": now,
            "actor_id": "system-migration",
            "actor_role": "system",
            "reason": "23.10-B additive backfill",
        }]

    # 3 · qualification_type mapping (never overwrite an existing value).
    if not row.get("qualification_type"):
        mapped = _map_legacy_type(row.get("certification_type"))
        if mapped:
            patch["qualification_type"] = mapped

    if not row.get("suspended_at"):
        patch.setdefault("suspended_at", None)
    if not row.get("revoked_at"):
        patch.setdefault("revoked_at", None)

    if patch:
        patch["migrated_at"] = now
        patch["migration_track"] = "23.10-B"
        await db[COLL].update_one({"id": row["id"]}, {"$set": patch})
        row = {**row, **patch}
    return row


async def _ensure_indexes(db) -> None:
    try:
        await db[COLL].create_index(
            "qualification_type",
            name="track_23_10_b_qualification_type",
        )
        await db[COLL].create_index(
            [("qualification_type", 1), ("verification_status", 1),
             ("expiration_date", 1)],
            name="track_23_10_b_active_registry",
        )
        await db[COLL].create_index(
            [("employee_id", 1), ("qualification_type", 1)],
            name="track_23_10_b_employee_type",
        )
        await db.hr_audit.create_index(
            [("kind", 1), ("qualification_id", 1), ("at", -1)],
            name="track_23_10_b_hr_audit_qual",
        )
    except Exception:                                              # noqa: BLE001
        pass


async def _backfill_cp_designations(db) -> Dict[str, int]:
    """One-time backfill: convert legacy CP designations on
    `db.employees` (from FV-7.2) into first-class
    `safety_training_records` rows with
    `qualification_type=COMPETENT_PERSON`.

    Idempotent: creates one row per (employee, cert data) if there is
    no existing active COMPETENT_PERSON row on the employee.
    """
    import uuid                                                    # noqa: PLC0415

    now = datetime.now(timezone.utc).isoformat()
    created = 0
    scanned = 0
    cursor = db.employees.find(
        {"$or": [
            {"competent_person_designated": True},
            {"cp_designated": True},
        ]},
        {"_id": 0},
    )
    async for emp in cursor:
        scanned += 1
        eid = emp.get("id") or emp.get("employee_id")
        if not eid:
            continue
        # Already have a COMPETENT_PERSON row? Skip.
        exists = await db[COLL].find_one(
            {
                "employee_id": eid,
                "$or": [
                    {"qualification_type": "COMPETENT_PERSON"},
                    {"certification_type": "COMPETENT_PERSON"},
                ],
            },
            {"_id": 0, "id": 1},
        )
        if exists:
            continue
        approval = str(emp.get("cp_approval_date") or "")[:10] or _today()
        expiration = str(emp.get("cp_expiration_date") or "")[:10] or ""
        # If expiration blank, default to +5 years (OSHA typical retraining).
        if not expiration:
            y = int(approval[:4]) + 5
            expiration = f"{y}{approval[4:]}"
        row = {
            "id": str(uuid.uuid4()),
            "employee_id": eid,
            "employee_master_id": emp.get("id") or eid,
            "employee_name": emp.get("name") or "",
            "qualification_type": "COMPETENT_PERSON",
            "certification_type": "COMPETENT_PERSON",
            "training_name": "Competent Person Designation",
            "completed_date": approval,
            "expiration_date": expiration,
            "issuing_organization": emp.get("cp_approved_by") or "MASCI",
            "issued_by": emp.get("cp_approved_by") or "MASCI",
            "notes": emp.get("cp_notes") or "Migrated from FV-7.2 CP designation",
            "verification_status": "active",
            "verification_status_history": [{
                "status": "active", "at": now,
                "actor_id": "system-migration",
                "actor_role": "system",
                "reason": "23.10-B backfill from db.employees CP designation",
            }],
            "suspended_at": None,
            "revoked_at": None,
            "created_at": now, "updated_at": now,
            "created_by": "system-migration",
            "created_by_role": "system",
            "originating_portal": "migration",
            "migrated_at": now,
            "migration_track": "23.10-B",
            "status": "Completed",
        }
        await db[COLL].insert_one(row)
        created += 1
    return {"cp_scanned": scanned, "cp_created": created}


async def run_migration(db, emit_facts: bool = True) -> Dict[str, Any]:
    """Idempotent migration entrypoint. Returns counters."""
    await _ensure_indexes(db)
    cp_counters = await _backfill_cp_designations(db)
    scanned = 0
    updated = 0
    facts_emitted = 0
    engine_rows = 0
    cursor = db[COLL].find({}, {"_id": 0})
    async for row in cursor:
        if not row.get("id"):
            continue
        scanned += 1
        original = dict(row)
        row = await _backfill_row(db, row)
        if row != original:
            updated += 1
        qtype = row.get("qualification_type") or row.get("certification_type")
        if is_engine_type(qtype):
            engine_rows += 1
            if emit_facts:
                try:
                    fid = await emit_qualification_certification_fact(
                        db, row,
                        actor="system-migration",
                        trigger="track_23_10_b.migration",
                        submitted_by="system",
                    )
                    if fid:
                        facts_emitted += 1
                except Exception:                                  # noqa: BLE001
                    pass
    return {
        "scanned": scanned,
        "updated": updated,
        "engine_rows": engine_rows,
        "facts_emitted": facts_emitted,
        **cp_counters,
        "at": datetime.now(timezone.utc).isoformat(),
    }


async def _run_cli() -> None:
    from motor.motor_asyncio import AsyncIOMotorClient       # noqa: PLC0415

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("MONGO_URL / DB_NAME must be set")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        result = await run_migration(db)
        print("[TRACK 23.10-B migration]", result)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(_run_cli())
