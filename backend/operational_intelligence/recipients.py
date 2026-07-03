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


__all__ = [
    "COLLECTION_RECIPIENTS", "COLLECTION_GROUPS",
    "list_recipients_for", "list_groups",
    "add_group", "add_group_member",
]
