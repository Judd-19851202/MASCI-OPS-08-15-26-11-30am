"""
doc_ids.py — Human-readable document numbering for every submission.

Why this exists
----------------
Every form / report / inspection that flows through MASCI Hub gets a
machine UUID (the ``id`` field) but those are useless to humans on the
phone with payroll, the field, or insurance.

This module mints **human-readable doc IDs** of the form
``<PREFIX>-<YEAR>-<5-digit-seq>`` (e.g. ``PRE-2026-00042``) on every
new submission, atomically, with no race conditions, and stores them on
the record alongside the UUID. The PDF generator stamps the doc_id in
the top-right header; the admin global search bar resolves a doc ID
straight to the record's detail page.

Sequence resets each calendar year so 2026's first Pre-Op is
``PRE-2026-00001``, regardless of how many were submitted in 2025.

Design choices
--------------
* **Atomic counter** via Mongo ``find_one_and_update($inc, upsert=True)``.
  Two concurrent submissions never collide.
* **Per-(prefix, year) bucket** — counter ``_id`` is the literal
  ``"PRE-2026"``. New year = new counter row, no special migration.
* **Idempotent**: ``ensure_doc_id`` skips minting if the record already
  has a ``doc_id`` field. Safe to call from re-saved drafts.
* **Backfillable**: ``backfill_collection`` walks an existing collection
  in chronological order and stamps every record that's missing a
  doc_id, so old records pulled up after the migration still display
  one. Backfilled IDs are the same format as fresh ones — they just
  reflect the chronological order of submission.

Public surface
--------------
- ``mint_doc_id(db, prefix, when=None)`` → str
- ``ensure_doc_id(db, doc, prefix, when=None)`` → str
- ``backfill_collection(db, collection, prefix_resolver)`` → int
- ``REGISTRY``: tuple of (collection_name, prefix or callable) — single
  source of truth used by both ingestion and the admin search index.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Prefix resolution. Most collections have a single prefix; field_leadership
# branches on the record's ``kind``.
PrefixResolver = Union[str, Callable[[Dict[str, Any]], str]]


def _field_leadership_prefix(rec: Dict[str, Any]) -> str:
    """field_leadership_records hold many shapes — give each a distinct
    prefix so the doc ID itself communicates what kind of form it is.

    Keys MUST stay in sync with FIELD_LEADERSHIP_KINDS in
    routes/field_leadership.py — the resolver ran against an older
    taxonomy in iter54 and silently bucketed everything that didn't
    match into the catch-all "FL", producing PRD drift. Now reconciled.
    """
    kind = (rec.get("kind") or "").lower()
    return {
        # Equipment lifecycle
        "equipment_checkout":         "EQC",
        "equipment_return":           "EQR",
        # People-management touchpoints
        "write_up":                   "FLW",  # write-up / discipline
        "verbal_coaching":            "FLC",  # coaching
        "attendance":                 "FLA",  # attendance log
        "recognition":                "FLR",  # recognition / kudos
        "new_employee_eval":          "FLE",  # evaluation
        "crew_eval":                  "FLG",  # crew evaluation (group)
        "promotion_recommendation":   "FLP",  # promotion
        "training_deficiency":        "FLT",  # training gap
        "supervisor_notes":           "FLN",  # supervisor notes
    }.get(kind, "FL")


# (collection, prefix-or-resolver, sort-key-for-backfill)
# sort_key tells the backfill which timestamp to walk in — submissions
# are stamped in the order they happened.
REGISTRY: List[Tuple[str, PrefixResolver, str]] = [
    ("equipment_inspections",       "PRE", "created_at"),
    ("daily_reports",               "DR",  "report_date"),
    ("inspections",                 "INSP","created_at"),
    ("meetings",                    "MTG", "created_at"),
    ("jhas",                        "JHA", "created_at"),
    ("incidents",                   "INC", "created_at"),
    ("qaqc_inspections",            "QC",  "created_at"),
    ("field_leadership_records",    _field_leadership_prefix, "occurred_at"),
    ("safety_equipment_issuances",  "SEI", "created_at"),
    ("safety_equipment_trainings",  "SET", "created_at"),
]


def _resolve_prefix(prefix: PrefixResolver, doc: Dict[str, Any]) -> str:
    return prefix(doc) if callable(prefix) else str(prefix)


def _year_for(when: Optional[Any]) -> int:
    """Year of the supplied timestamp (ISO string, datetime, or None=now).

    We use UTC consistently so a submission at 11pm EST on Dec 31 doesn't
    accidentally land in next year's counter.
    """
    if isinstance(when, datetime):
        dt = when.astimezone(timezone.utc) if when.tzinfo else when.replace(tzinfo=timezone.utc)
    elif isinstance(when, str) and when:
        try:
            # Common shapes: "2026-05-08T10:31:00+00:00", "2026-05-08T10:31:00Z", "2026-05-08"
            s = when.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return dt.year


async def mint_doc_id(db, prefix: str, when: Optional[Any] = None) -> str:
    """Atomically mint the next ``<PREFIX>-<YEAR>-<NNNNN>`` doc ID.

    Uses Mongo's ``$inc`` with upsert on ``doc_id_counters`` keyed by
    ``"<PREFIX>-<YEAR>"``. Concurrent calls are safe — every caller
    gets a distinct seq number.
    """
    year = _year_for(when)
    counter_key = f"{prefix}-{year}"
    res = await db.doc_id_counters.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"seq": 1}, "$setOnInsert": {"prefix": prefix, "year": year}},
        upsert=True,
        return_document=True,  # ReturnDocument.AFTER on motor>=3 returns the updated doc
    )
    seq = (res or {}).get("seq", 1)
    return f"{prefix}-{year}-{seq:05d}"


async def ensure_doc_id(
    db,
    doc: Dict[str, Any],
    prefix: PrefixResolver,
    when: Optional[Any] = None,
) -> str:
    """Stamp a doc with a fresh doc_id if it doesn't have one already.

    Mutates ``doc`` in place AND returns the value so callers can use
    either pattern. Idempotent — re-saving an already-stamped record
    keeps the original doc_id.
    """
    if isinstance(doc.get("doc_id"), str) and doc["doc_id"].strip():
        return doc["doc_id"]
    pre = _resolve_prefix(prefix, doc)
    new_id = await mint_doc_id(db, pre, when=when)
    doc["doc_id"] = new_id
    return new_id


async def backfill_collection(
    db,
    collection: str,
    prefix: PrefixResolver,
    sort_key: str = "created_at",
) -> int:
    """One-shot backfill: walks every record in chronological order and
    stamps any that are missing ``doc_id``.

    Returns the number of records stamped. Calling twice is safe — the
    second pass finds zero records to stamp because the first pass
    already filled them in.
    """
    cursor = db[collection].find(
        {"$or": [{"doc_id": {"$exists": False}}, {"doc_id": ""}, {"doc_id": None}]},
        {"_id": 0, "id": 1, "kind": 1, sort_key: 1, "created_at": 1, "occurred_at": 1, "report_date": 1},
    ).sort([(sort_key, 1), ("created_at", 1)])
    rows = await cursor.to_list(length=None)
    count = 0
    for row in rows:
        if not row.get("id"):
            continue
        when = (
            row.get(sort_key)
            or row.get("created_at")
            or row.get("occurred_at")
            or row.get("report_date")
        )
        pre = _resolve_prefix(prefix, row)
        new_id = await mint_doc_id(db, pre, when=when)
        await db[collection].update_one({"id": row["id"]}, {"$set": {"doc_id": new_id}})
        count += 1
    if count:
        logger.info(f"[doc_ids] backfilled {count} records in {collection}")
    return count


async def backfill_all(db) -> Dict[str, int]:
    """Run backfill_collection across every registered collection.

    Idempotent on subsequent boots. Logs a per-collection summary.
    """
    summary: Dict[str, int] = {}
    for collection, prefix, sort_key in REGISTRY:
        try:
            n = await backfill_collection(db, collection, prefix, sort_key)
            if n:
                summary[collection] = n
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[doc_ids] backfill failed for {collection}: {e}")
    return summary


async def find_record_by_doc_id(db, doc_id: str) -> Optional[Dict[str, Any]]:
    """Cross-collection doc-id lookup powering the admin search bar.

    Returns ``{collection, kind, id, doc_id, project_number, ...}`` so
    the frontend can route to the correct detail page. Doc IDs are
    case-insensitive (we normalize uppercase before query).
    """
    if not doc_id:
        return None
    needle = doc_id.strip().upper()
    if not needle:
        return None
    for collection, _prefix, _sort in REGISTRY:
        rec = await db[collection].find_one(
            {"doc_id": needle},
            {"_id": 0, "id": 1, "doc_id": 1, "kind": 1,
             "project_number": 1, "project_name": 1,
             "created_at": 1, "occurred_at": 1, "report_date": 1,
             "employee_name": 1, "supervisor_name": 1,
             "submitted_by": 1, "title": 1, "form_id": 1, "type": 1},
        )
        if rec:
            return {**rec, "collection": collection}
    return None


__all__ = [
    "REGISTRY",
    "mint_doc_id",
    "ensure_doc_id",
    "backfill_collection",
    "backfill_all",
    "find_record_by_doc_id",
]
