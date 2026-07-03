"""Recipients + Groups — the ONE recipient engine.

Zero-drift: reuses the Track 19.39 ``morning_digest_recipients``
collection (which already carries a ``digest_type`` column). Adds a
new additive ``operational_recipient_groups`` collection for group
support without touching the individual-recipient collection.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


COLLECTION_RECIPIENTS = "morning_digest_recipients"      # existing · zero drift
COLLECTION_GROUPS = "operational_recipient_groups"       # additive


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def list_recipients_for(
    db, *, product_id: str, active_only: bool = True,
) -> List[Dict[str, Any]]:
    """Return the resolved recipient list for a product. Union of
    directly-subscribed individuals + members of groups that subscribe
    to the product."""
    # Direct individuals — collection stores per-row `digest_type`.
    q: Dict[str, Any] = {"digest_type": product_id}
    if active_only:
        q["active"] = True
    direct = [
        d async for d in db[COLLECTION_RECIPIENTS].find(q, {"_id": 0})
    ]

    # Group expansion.
    groups = [
        g async for g in db[COLLECTION_GROUPS].find(
            {"products": product_id}, {"_id": 0},
        )
    ]
    group_emails: Dict[str, Dict[str, Any]] = {}
    for g in groups:
        for m in (g.get("members") or []):
            if active_only and not m.get("active", True):
                continue
            e = (m.get("email") or "").lower()
            if not e:
                continue
            group_emails[e] = {
                "email": e,
                "display_name": m.get("display_name") or "",
                "role_label": m.get("role_label") or g.get("group_name") or "",
                "active": True,
                "source": f"group:{g.get('group_id')}",
            }

    # Merge direct + groups, dedupe by email (direct takes precedence).
    merged: Dict[str, Dict[str, Any]] = {}
    for m in list(group_emails.values()):
        merged[m["email"].lower()] = m
    for r in direct:
        merged[(r.get("email") or "").lower()] = r
    return list(merged.values())


async def list_groups(db) -> List[Dict[str, Any]]:
    return [g async for g in db[COLLECTION_GROUPS].find({}, {"_id": 0})]


async def add_group(db, *, group_id: str, group_name: str,
                    products: Optional[List[str]] = None,
                    created_by: str = "admin") -> Dict[str, Any]:
    doc = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "group_name": group_name,
        "products": list(products or []),
        "members": [],
        "created_at": _now_iso(),
        "created_by": created_by,
    }
    await db[COLLECTION_GROUPS].insert_one(doc)
    doc.pop("_id", None)  # strip Mongo ObjectId — not JSON serializable
    return doc


async def add_group_member(db, *, group_id: str, email: str,
                           display_name: str = "", role_label: str = "",
                           active: bool = True) -> Optional[Dict[str, Any]]:
    email = (email or "").strip().lower()
    if "@" not in email:
        raise ValueError(f"invalid email: {email!r}")
    member = {"email": email, "display_name": display_name,
              "role_label": role_label, "active": active}
    await db[COLLECTION_GROUPS].update_one(
        {"group_id": group_id},
        {"$push": {"members": member}},
    )
    return await db[COLLECTION_GROUPS].find_one({"group_id": group_id}, {"_id": 0})


# ---------------------------------------------------------------------------
# TRACK 19.45A · Universal recipient management (individuals · additive)
# ---------------------------------------------------------------------------
async def list_recipients(db, *, product_id: Optional[str] = None,
                          active_only: bool = False,
                          search: Optional[str] = None,
                          limit: int = 500) -> List[Dict[str, Any]]:
    """Admin-facing list. When product_id is None, returns every row
    across every product. Search matches email/display_name/role_label
    case-insensitively."""
    q: Dict[str, Any] = {}
    if product_id:
        q["digest_type"] = product_id
    if active_only:
        q["active"] = True
    if search:
        s = str(search).strip().lower()
        q["$or"] = [
            {"email": {"$regex": s, "$options": "i"}},
            {"display_name": {"$regex": s, "$options": "i"}},
            {"role_label": {"$regex": s, "$options": "i"}},
        ]
    return [r async for r in db[COLLECTION_RECIPIENTS].find(q, {"_id": 0}).limit(limit)]


async def add_recipient(db, *, email: str, product_id: str,
                        display_name: str = "", role_label: str = "",
                        department: str = "",
                        notes: str = "", added_by: str = "admin",
                        active: bool = True) -> Dict[str, Any]:
    email = (email or "").strip().lower()
    if "@" not in email:
        raise ValueError(f"invalid email: {email!r}")
    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "display_name": display_name,
        "role_label": role_label,
        "department": department,
        "notes": notes,
        "digest_type": product_id,
        "active": bool(active),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "added_by": added_by,
        "updated_by": added_by,
    }
    await db[COLLECTION_RECIPIENTS].insert_one(doc)
    doc.pop("_id", None)  # strip Mongo ObjectId — not JSON serializable
    return doc


async def update_recipient(db, *, recipient_id: str,
                           updated_by: str = "admin",
                           **fields) -> Optional[Dict[str, Any]]:
    """Additive · never overwrites created_* fields · always stamps updated_*."""
    allowed = {"email", "display_name", "role_label", "department",
               "notes", "active", "digest_type"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await db[COLLECTION_RECIPIENTS].find_one(
            {"id": recipient_id}, {"_id": 0})
    if "email" in updates:
        updates["email"] = str(updates["email"]).strip().lower()
        if "@" not in updates["email"]:
            raise ValueError(f"invalid email: {updates['email']!r}")
    updates["updated_at"] = _now_iso()
    updates["updated_by"] = updated_by
    await db[COLLECTION_RECIPIENTS].update_one(
        {"id": recipient_id}, {"$set": updates})
    return await db[COLLECTION_RECIPIENTS].find_one(
        {"id": recipient_id}, {"_id": 0})


async def deactivate_recipient(db, *, recipient_id: str,
                               updated_by: str = "admin") -> Optional[Dict[str, Any]]:
    """Deactivation is preferred over deletion — regulatory replay."""
    return await update_recipient(
        db, recipient_id=recipient_id, updated_by=updated_by, active=False)


async def bulk_import_recipients(db, *, rows: List[Dict[str, Any]],
                                 default_product_id: Optional[str] = None,
                                 added_by: str = "admin") -> Dict[str, Any]:
    """Bulk import. Skips rows with invalid emails; dedupes by
    (email, digest_type). Returns per-row status."""
    result: Dict[str, Any] = {"inserted": 0, "skipped": 0,
                              "duplicate": 0, "errors": []}
    for row in rows or []:
        try:
            email = (row.get("email") or "").strip().lower()
            product = row.get("digest_type") or row.get("product_id") \
                or default_product_id
            if "@" not in email or not product:
                result["skipped"] += 1
                result["errors"].append({"row": row, "reason": "invalid email or product"})
                continue
            existing = await db[COLLECTION_RECIPIENTS].find_one(
                {"email": email, "digest_type": product}, {"_id": 0})
            if existing:
                result["duplicate"] += 1
                continue
            await add_recipient(
                db, email=email, product_id=product,
                display_name=row.get("display_name") or "",
                role_label=row.get("role_label") or "",
                department=row.get("department") or "",
                notes=row.get("notes") or "",
                added_by=added_by,
                active=bool(row.get("active", True)),
            )
            result["inserted"] += 1
        except Exception as e:  # noqa: BLE001
            result["errors"].append({"row": row, "reason": str(e)})
            result["skipped"] += 1
    return result


__all__ = [
    "COLLECTION_RECIPIENTS", "COLLECTION_GROUPS",
    "list_recipients_for", "list_groups", "list_recipients",
    "add_group", "add_group_member",
    "add_recipient", "update_recipient", "deactivate_recipient",
    "bulk_import_recipients",
]
