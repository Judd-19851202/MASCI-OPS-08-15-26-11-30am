"""iter245 — Vendors / Subcontractors master list.

Operator directive (2026-05-19):
  - Field Leadership submits PO requests using a searchable vendor
    dropdown to eliminate inconsistent spelling variants.
  - Centralized vendors collection, append-only from Field Leadership.
  - Normalization: trim whitespace, case-insensitive dedupe, basic
    sanitation.
  - Audit fields: created_by, created_at, source.
  - No approval gate. No procurement system. No vendor-management
    expansion beyond what this single PO-request workflow needs.

Endpoints (registered from server.py):
  GET    /api/vendors          (any signed-in portal user; FL allowed)
  POST   /api/vendors          (any signed-in portal user; FL allowed)
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


VENDORS_COLLECTION = "vendors"


# ── Models ──────────────────────────────────────────────────────────────
class VendorIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    category: Optional[str] = "General"   # General | Subcontractor | Materials | Equipment | Rental
    notes: Optional[str] = ""


class VendorOut(BaseModel):
    id: str
    name: str
    name_key: str                # case-insensitive dedupe key
    category: Optional[str] = "General"
    notes: Optional[str] = ""
    created_by: Optional[Dict[str, Any]] = None  # {role, name, user_id}
    created_at: str
    source: Optional[str] = "field_leadership_po_request"
    is_active: bool = True


# ── Normalization ───────────────────────────────────────────────────────
def _normalize_name(raw: str) -> str:
    """Trim · collapse internal whitespace · strip control chars."""
    s = (raw or "").strip()
    s = re.sub(r"\s+", " ", s)
    # strip non-printable chars but keep accented/utf-8 (vendor names like "García & Sons")
    s = "".join(c for c in s if c.isprintable())
    return s


def _name_key(name: str) -> str:
    """Case-insensitive duplicate-detection key.

    Lowercases, removes punctuation/quotes, collapses whitespace.
    This is the field we index on for dedupe — two vendors that differ
    only by case, trailing space, or punctuation collide here.
    """
    s = (name or "").lower().strip()
    s = re.sub(r"[\.,\'\"\(\)&]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


# ── Storage helpers ─────────────────────────────────────────────────────
async def list_vendors(db, *, only_active: bool = True) -> List[Dict[str, Any]]:
    """Sorted alphabetically by name, _id stripped."""
    q = {"is_active": True} if only_active else {}
    cursor = db[VENDORS_COLLECTION].find(q, {"_id": 0}).sort("name", 1)
    return [v async for v in cursor]


async def find_vendor_by_key(db, name_key: str) -> Optional[Dict[str, Any]]:
    return await db[VENDORS_COLLECTION].find_one({"name_key": name_key}, {"_id": 0})


async def create_vendor(
    db,
    body: VendorIn,
    *,
    actor: Optional[Dict[str, Any]] = None,
    source: str = "field_leadership_po_request",
) -> Dict[str, Any]:
    """Append-only create with normalization + dedupe.

    Returns the existing vendor if one already exists under the same
    `name_key` (idempotent for callers who fire-and-forget). The caller
    can detect this by comparing `created_at` — re-used vendors carry
    their original timestamp.
    """
    name = _normalize_name(body.name)
    if len(name) < 2:
        raise ValueError("Vendor name must be at least 2 characters after trim")
    key = _name_key(name)
    if not key:
        raise ValueError("Vendor name normalizes to empty — invalid input")

    # Idempotent dedupe — if the key already exists, return that record.
    existing = await find_vendor_by_key(db, key)
    if existing:
        return existing

    rec = {
        "id": str(uuid.uuid4()),
        "name": name,
        "name_key": key,
        "category": (body.category or "General").strip() or "General",
        "notes": (body.notes or "").strip(),
        "created_by": actor or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "is_active": True,
    }
    await db[VENDORS_COLLECTION].insert_one(dict(rec))
    return rec


async def ensure_unique_index(db) -> None:
    """Idempotent index creation. Called once at server startup."""
    try:
        await db[VENDORS_COLLECTION].create_index("name_key", unique=True, name="vendors_namekey_uniq")
    except Exception:
        # Index already exists — fine
        pass
