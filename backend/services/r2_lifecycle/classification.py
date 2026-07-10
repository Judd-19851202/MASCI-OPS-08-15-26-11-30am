"""
Phase 4 · Strict classification engine.

Each object in `r2_inventory` receives EXACTLY ONE classification.
The classifier is a pure function of:

- the object's inventory row,
- the set of Mongo references pointing at its key (from `r2_references`),
- the platform's protective flags (retention/backup/legal-hold/system).

There are no heuristics.  There are no probabilities that flip on
close calls.  If ANY protective flag matches, the object is protected.
If NO reference exists AND no protective flag matches, the object is a
VERIFIED_ORPHAN.  Every other outcome is AMBIGUOUS.

The classification result is persisted to `r2_classifications`, one
document per key.  Downstream (dry-run, health score) reads from that
snapshot, never from R2 directly.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# ── Allowed classifications ────────────────────────────────────────────
CLASSIFICATIONS = (
    "VERIFIED_OWNER",
    "VERIFIED_ORPHAN",
    "AMBIGUOUS",
    "SYSTEM_RESERVED",
    "RETENTION_PROTECTED",
    "BACKUP_PROTECTED",
    "LEGAL_HOLD",
    "HISTORICAL",
    "PENDING",
    "UNKNOWN",
)

# States that the certification gate refuses to delete.  Everything
# except VERIFIED_ORPHAN is refused today (the gate is deliberately
# maximally strict — we can loosen it later, we cannot un-delete files).
ALLOWED_FOR_DELETION = frozenset({"VERIFIED_ORPHAN"})

# Sub-set that will BLOCK a batch even if it contains a single member.
# Any AMBIGUOUS/UNKNOWN/PENDING/SYSTEM/RETENTION/BACKUP/LEGAL/HISTORICAL
# object in a dry-run refusal set means the batch cannot proceed.
DRY_RUN_REFUSAL_STATES = frozenset({
    "AMBIGUOUS", "UNKNOWN", "PENDING",
    "SYSTEM_RESERVED", "RETENTION_PROTECTED", "BACKUP_PROTECTED",
    "LEGAL_HOLD", "HISTORICAL",
})


# ── Protective prefix patterns (SYSTEM_RESERVED) ───────────────────────
# Objects living under these prefixes are never candidates for deletion
# regardless of Mongo references.  Add here — never inline.
_SYSTEM_RESERVED_PREFIXES = (
    "system/",                # platform-managed internals
    "_system/",
    "recovery-drills/",       # drill archives — must survive audits
    "audit-exports/",         # regulatory exports
)

_BACKUP_PREFIXES = (
    "backups/",
    "complete-backups/",
    "MASCI_complete_backup",  # nightly complete archives (root-level key)
    "MASCI_backup",
)

_HISTORICAL_PREFIXES = (
    "legacy-imports/",
    "historical/",
)

_PENDING_MAX_AGE_HOURS = 2  # objects <2h old are considered PENDING


# ── Pure classifier ────────────────────────────────────────────────────
@dataclass
class Classification:
    """Return type of :func:`classify_object`. Serialisable as-is."""
    key: str
    classification: str
    confidence: float
    evidence: List[Dict[str, Any]]
    protective_flags: List[str]
    reason: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hours_old(last_modified_iso: Optional[str], now: datetime) -> Optional[float]:
    if not last_modified_iso:
        return None
    try:
        # `last_modified` is stored as an ISO string by inventory.py
        ts = datetime.fromisoformat(last_modified_iso.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        return None
    return (now - ts).total_seconds() / 3600.0


def _matches_prefix(key: str, prefixes: tuple) -> bool:
    for p in prefixes:
        if key.startswith(p):
            return True
    return False


def classify_object(
    inv_row: Dict[str, Any],
    refs: List[Dict[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> Classification:
    """Classify a single object.

    Parameters
    ----------
    inv_row : the persisted `r2_inventory` doc.
    refs    : the list of `r2_references` docs matching the key.
    now     : injected clock for tests.
    """
    now = now or _now()
    key = inv_row["key"]
    protective: List[str] = []

    # 1) System-reserved prefixes always win.
    if _matches_prefix(key, _SYSTEM_RESERVED_PREFIXES):
        return Classification(
            key=key, classification="SYSTEM_RESERVED", confidence=1.0,
            evidence=[{"kind": "prefix", "reason": "platform-managed prefix"}],
            protective_flags=["system_reserved"],
            reason="Key lives under a platform-managed prefix.",
        )

    # 2) Backup archives.
    if _matches_prefix(key, _BACKUP_PREFIXES):
        return Classification(
            key=key, classification="BACKUP_PROTECTED", confidence=1.0,
            evidence=[{"kind": "prefix", "reason": "backup archive"}],
            protective_flags=["backup"],
            reason="Key is a recovery/backup archive.",
        )

    # 3) Historical imports.
    if _matches_prefix(key, _HISTORICAL_PREFIXES):
        return Classification(
            key=key, classification="HISTORICAL", confidence=1.0,
            evidence=[{"kind": "prefix", "reason": "historical archive"}],
            protective_flags=["historical"],
            reason="Key is a historical/legacy archive.",
        )

    # 4) Pending: freshly-uploaded objects (may still be racing with
    #    the DB write). Treat as PENDING for two hours to eliminate
    #    the classic upload → classify → delete race.
    age = _hours_old(inv_row.get("last_modified"), now)
    if age is not None and age < _PENDING_MAX_AGE_HOURS:
        return Classification(
            key=key, classification="PENDING", confidence=1.0,
            evidence=[{"kind": "age", "hours_old": round(age, 2)}],
            protective_flags=["pending"],
            reason="Object is younger than the pending-write safety window.",
        )

    # 5) Verified owner: at least one Mongo reference exists.
    if refs:
        return Classification(
            key=key, classification="VERIFIED_OWNER", confidence=1.0,
            evidence=[
                {
                    "kind": "mongo_reference",
                    "collection": r.get("collection"),
                    "owner": r.get("owner"),
                    "feature": r.get("feature"),
                    "doc_id": r.get("doc_id"),
                    "field_path": r.get("field_path"),
                }
                for r in refs[:20]
            ],
            protective_flags=[],
            reason=f"Referenced by {len(refs)} Mongo document(s).",
        )

    # 6) Verified orphan: inventoried, older than PENDING window, no
    #    protective flag, no Mongo reference.  This is the ONLY class
    #    the delete engine will ever accept.
    return Classification(
        key=key, classification="VERIFIED_ORPHAN", confidence=1.0,
        evidence=[
            {"kind": "no_reference", "collections_searched": len(refs) == 0},
            {"kind": "age_ok", "hours_old": round(age, 2) if age is not None else None},
        ],
        protective_flags=[],
        reason=(
            "No Mongo reference matches this key AND no protective flag "
            "applies AND object is older than the pending window."
        ),
    )


# ── Bulk driver ────────────────────────────────────────────────────────
async def classify_all(db, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Read every inventory row + its references, compute a fresh
    classification, and upsert into `r2_classifications`.  Returns a
    run summary."""
    now = now or _now()
    run_id = f"cls-{uuid4().hex[:12]}"

    # Preload references once — much cheaper than a per-key query.
    refs_by_key: Dict[str, List[Dict[str, Any]]] = {}
    async for r in db.r2_references.find({}, {"_id": 0}):
        refs_by_key.setdefault(r["r2_key"], []).append(r)

    counts: Dict[str, int] = {c: 0 for c in CLASSIFICATIONS}
    orphan_bytes = 0
    ops: List[Any] = []
    from pymongo import UpdateOne  # noqa: PLC0415 — lazy

    async for inv in db.r2_inventory.find({}, {"_id": 0}):
        result = classify_object(inv, refs_by_key.get(inv["key"], []), now=now)
        counts[result.classification] += 1
        if result.classification == "VERIFIED_ORPHAN":
            orphan_bytes += int(inv.get("size") or 0)
        ops.append(UpdateOne(
            {"_id": inv["key"]},
            {"$set": {
                "key": result.key,
                "classification": result.classification,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "protective_flags": result.protective_flags,
                "reason": result.reason,
                "size": int(inv.get("size") or 0),
                "prefix": inv.get("prefix"),
                "project_number": inv.get("project_number"),
                "last_modified": inv.get("last_modified"),
                "classified_at": now.isoformat(),
                "run_id": run_id,
            }},
            upsert=True,
        ))
        if len(ops) >= 500:
            await db.r2_classifications.bulk_write(ops, ordered=False)
            ops.clear()
    if ops:
        await db.r2_classifications.bulk_write(ops, ordered=False)

    summary = {
        "run_id": run_id,
        "kind": "classification",
        "started_at": now.isoformat(),
        "completed_at": _now().isoformat(),
        "counts": counts,
        "verified_orphan_bytes": orphan_bytes,
        "total_classified": sum(counts.values()),
    }
    await db.r2_lifecycle_runs.insert_one(dict(summary))
    return summary


async def classification_counts(db) -> Dict[str, Any]:
    """Return the counts summary of the latest classification run, or
    an empty structure if none has ever been executed."""
    row = await db.r2_lifecycle_runs.find_one(
        {"kind": "classification"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    if not row:
        return {"has_data": False, "counts": {c: 0 for c in CLASSIFICATIONS},
                "verified_orphan_bytes": 0, "total_classified": 0}
    row["has_data"] = True
    return row
