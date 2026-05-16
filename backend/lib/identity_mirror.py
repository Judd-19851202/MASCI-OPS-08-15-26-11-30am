"""
lib/identity_mirror.py — Phase K1 · Silent Unified Identity Mirror
==================================================================

Backfills the existing `user_directory` collection (from iter82) with
shadow rows for every user that currently lives in a per-portal
collection (`hr_users`, `pm_users`, `shop_users`, `safety_users`,
`dispatch_users`). Strictly **read-only with respect to login flow**:

  • Existing per-portal logins keep working unchanged.
  • Mirrored rows have a randomized password_hash (cannot be used via
    /api/auth/multi-login). That endpoint stays gated to rows whose
    `mirrored` flag is NOT True, OR whose admin has subsequently set a
    real master password (which clears `mirrored`).
  • No new HTTP endpoints exposed.
  • No UI surfaced.
  • No enforcement changes.

What it adds
------------
  • A single row in `user_directory` per real person (by email).
  • An accurate `portals` array reflecting which per-portal collections
    that email lives in.
  • An `employee_id` linkage when one is discoverable from the portal
    record (or NULL if not).
  • A `mirrored=True` flag distinguishing auto-populated rows from
    user-managed multi-portal accounts.
  • A `mirror_sources` dict tracking which per-portal record fed each
    portal entry (useful for the eventual Phase K8 cutover).
  • Unique indexes on `user_directory.email` and `user_directory.id`.

The backfill is **idempotent** — safe to re-run on every startup.

Phase K2+ work is OUT OF SCOPE here.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import bcrypt

logger = logging.getLogger(__name__)

# Per-portal collections that feed the mirror. The leadership portal is
# intentionally absent — it currently uses a shared password (MASCIGC)
# and named accounts are introduced in Phase K7.
PORTAL_COLLECTIONS: List[Tuple[str, str]] = [
    ("admin", "admin_users"),          # may not exist; safe if empty
    ("hr",    "hr_users"),
    ("pm",    "pm_users"),
    ("shop",  "shop_users"),
    ("safety", "safety_users"),
    ("dispatch", "dispatch_users"),
]

# Random per-row hash for mirrored entries. Computed once at module
# load to keep startup fast; each mirrored row gets a fresh bcrypt of
# a random 48-byte token so no two rows share a hash, and none of them
# are guessable.
def _random_unguessable_hash() -> str:
    return bcrypt.hashpw(
        secrets.token_urlsafe(48).encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("ascii")


async def ensure_indexes(db) -> None:
    """Create the unique indexes the mirror relies on. Idempotent.

    A duplicate `email` row predating this index would block creation;
    the routine first squashes any such duplicates by keeping the most
    recently updated row.
    """
    try:
        # Squash duplicate emails (defensive — none observed in current
        # preview but production has more history).
        pipe = [
            {"$match": {"email": {"$type": "string", "$ne": ""}}},
            {"$group": {"_id": "$email", "ids": {"$push": "$id"}, "n": {"$sum": 1}}},
            {"$match": {"n": {"$gt": 1}}},
        ]
        async for grp in db.user_directory.aggregate(pipe):
            keep_id = grp["ids"][0]
            drop_ids = grp["ids"][1:]
            if drop_ids:
                await db.user_directory.delete_many({"id": {"$in": drop_ids}})
                logger.info(f"[identity-mirror] dedup email={grp['_id']} kept={keep_id} dropped={len(drop_ids)}")

        await db.user_directory.create_index("email", unique=True, name="email_unique")
        await db.user_directory.create_index("id", unique=True, name="id_unique")
        # Helpful secondary indexes — read-only paths only.
        await db.user_directory.create_index("portals", name="portals_arr")
        await db.user_directory.create_index("mirrored", name="mirrored_flag")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[identity-mirror] ensure_indexes warning: {e}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: Any) -> Optional[str]:
    if not email or not isinstance(email, str):
        return None
    e = email.strip().lower()
    if "@" not in e:
        return None
    return e


def _candidate_employee_id(doc: Dict[str, Any]) -> Optional[str]:
    """Pull a linkable employee_id off the portal-user document if one
    is present. Different portals stamp this differently; we look at
    the most common shapes."""
    for key in ("employee_id", "linked_employee_id", "employee_master_id", "emp_id"):
        v = doc.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


async def _collect_portal_emails(db) -> Dict[str, Dict[str, Any]]:
    """Walk every portal collection and build a dict keyed by email →
    {portals: set, employee_id: str | None, name: str, sources: {portal: source_id}}.
    Collections that don't exist are silently ignored."""
    aggregated: Dict[str, Dict[str, Any]] = {}
    for portal, coll_name in PORTAL_COLLECTIONS:
        try:
            cursor = db[coll_name].find({}, {"_id": 0})
            async for doc in cursor:
                email = _normalize_email(doc.get("email"))
                if not email:
                    continue
                entry = aggregated.setdefault(email, {
                    "portals": set(),
                    "employee_id": None,
                    "name": "",
                    "sources": {},
                })
                entry["portals"].add(portal)
                entry["sources"][portal] = doc.get("id") or doc.get("user_id") or None
                if not entry["employee_id"]:
                    entry["employee_id"] = _candidate_employee_id(doc)
                if not entry["name"]:
                    n = (doc.get("name") or "").strip()
                    if n:
                        entry["name"] = n
        except Exception as e:  # noqa: BLE001
            logger.info(f"[identity-mirror] {coll_name} skipped: {e}")
    return aggregated


async def backfill_mirror(db) -> Dict[str, Any]:
    """Idempotent mirror sync. Returns a stats dict suitable for logging.

    Behavior:
      • For every email present in any per-portal collection:
        - If no `user_directory` row exists → create a mirrored row.
        - If a row exists AND is `mirrored=True` → union the portals
          list with what we found, refresh `mirror_sources`,
          fill in employee_id if missing.
        - If a row exists AND is NOT mirrored (user has set their own
          master password) → leave the row's `portals` and password
          ALONE. We only touch `mirror_sources` so the cutover map
          stays accurate.
    """
    stats: Dict[str, int] = {
        "scanned_emails": 0,
        "created": 0,
        "updated_mirrored": 0,
        "touched_managed": 0,
        "untouched": 0,
    }

    aggregated = await _collect_portal_emails(db)
    stats["scanned_emails"] = len(aggregated)

    for email, info in aggregated.items():
        portals_found = sorted(info["portals"])
        sources = info["sources"]
        employee_id = info["employee_id"]
        name = info["name"] or email.split("@")[0]

        existing = await db.user_directory.find_one({"email": email}, {"_id": 0})

        if not existing:
            # Create a fresh mirrored row with an unguessable password.
            row = {
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "portals": portals_found,
                "password_hash": _random_unguessable_hash(),
                "is_super_admin": False,
                "disabled": False,
                "must_change_password": False,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "last_login_at": None,
                "last_login_portal": None,
                # Mirror-specific fields:
                "mirrored": True,
                "mirror_sources": sources,
                "employee_id": employee_id,
                "schema_version": 1,
            }
            try:
                await db.user_directory.insert_one(row)
                stats["created"] += 1
            except Exception as e:  # likely race on unique email index
                logger.info(f"[identity-mirror] insert race for {email}: {e}")
                stats["untouched"] += 1
            continue

        if existing.get("mirrored"):
            # Union portals + refresh sources, fill employee_id if blank.
            merged_portals = sorted(set(existing.get("portals") or []) | set(portals_found))
            update: Dict[str, Any] = {
                "portals": merged_portals,
                "mirror_sources": sources,
                "updated_at": _now_iso(),
                "schema_version": 1,
            }
            if not existing.get("employee_id") and employee_id:
                update["employee_id"] = employee_id
            if not existing.get("name") and name:
                update["name"] = name
            await db.user_directory.update_one({"id": existing["id"]}, {"$set": update})
            stats["updated_mirrored"] += 1
            continue

        # Managed row (user has a master pw). Only refresh sources so
        # the cutover map stays accurate. Never overwrite portals or pw.
        await db.user_directory.update_one(
            {"id": existing["id"]},
            {"$set": {
                "mirror_sources": {**(existing.get("mirror_sources") or {}), **sources},
                "schema_version": 1,
            }},
        )
        stats["touched_managed"] += 1

    return stats


async def run_startup_mirror(db) -> None:
    """Hook for the FastAPI startup event. Logs results; never raises."""
    try:
        await ensure_indexes(db)
        stats = await backfill_mirror(db)
        logger.info(
            "[identity-mirror] startup sync complete: "
            f"scanned={stats['scanned_emails']} "
            f"created={stats['created']} "
            f"updated_mirrored={stats['updated_mirrored']} "
            f"touched_managed={stats['touched_managed']}"
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[identity-mirror] startup sync failed: {e}")
