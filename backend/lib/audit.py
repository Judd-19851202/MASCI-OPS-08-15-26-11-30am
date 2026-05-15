"""
lib/audit.py — Iter B unification.

Single audit-log helper. Replaces fragmented `_audit_push` patterns
scattered across po_requests / employee_lifecycle / admin_ops /
hub_banners. Each module previously rolled its own — the function
signatures were close enough that they should be unified but distinct
enough that some had subtle bugs around UTC time and missing actor info.

The new pattern:

    from lib.audit import append_audit

    await append_audit(
        db, collection="po_requests",
        record_id=po_id,
        action="approve",
        actor={"role": "hr", "name": "Jane Doe", "id": "u_123"},
        details={"approved_amount": 120.0, "notes": "..."},
    )

Semantics:
  * `collection` — the parent collection (`po_requests`, `employees`, …).
  * `record_id` — the parent record's `id` field (not Mongo `_id`).
  * The function appends to `record.audit` (preserving existing entries
    via $push). NO replacement. NO race. NO ObjectId leakage.
  * Always uses UTC timezone-aware datetime.
  * Returns the inserted audit entry dict (handy for tests).

Backwards compat: po_requests' existing `_audit_push` will continue
to work; this helper is the canonical entry point for ALL new modules
and existing modules will be migrated incrementally.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def append_audit(
    db,
    *,
    collection: str,
    record_id: str,
    action: str,
    actor: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append one entry to the `audit` array of a parent record.

    Returns the entry (timestamped, with a fresh id) so callers can
    surface it directly in their response if needed."""
    entry = {
        "id": uuid.uuid4().hex,
        "action": action,
        "actor": actor or {},
        "details": details or {},
        "at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db[collection].update_one(
            {"id": record_id},
            {"$push": {"audit": entry},
             "$set": {"updated_at": datetime.now(timezone.utc)}},
        )
    except Exception as e:  # noqa: BLE001
        # Audit is best-effort. Never break the parent write.
        logger.warning("[append_audit] %s/%s/%s failed: %s",
                       collection, record_id, action, e)
    return entry


__all__ = ["append_audit"]
