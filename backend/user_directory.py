"""
user_directory.py — Multi-portal "Access Control Center" (iter82)
==================================================================
A lookup layer that links a single email + master password to one OR more
of the platform's four portal namespaces (admin · pm · shop · hr).

Why this exists
---------------
Today, an org owner who needs Admin + PM + HR access has three separate
accounts with three separate passwords and three separate sign-in flows.
This module gives them ONE master account that issues all three portal
tokens at once.

Design principles
-----------------
1. **Additive, not destructive.** Existing per-portal login endpoints
   (/api/pm/login, /api/hr/login, etc.) keep working unchanged. This is
   a NEW endpoint that sits alongside them. Rollback = delete the
   `user_directory` collection. Existing users see zero change.

2. **Super-admins can never lock themselves out.** A row with
   `is_super_admin=true` cannot be deleted or disabled by the admin
   panel — guards against accidental self-lockout.

3. **One password to rule them all.** Master password is bcrypt-hashed,
   stored on the directory row, and validated by this module. Per-portal
   passwords (PM/Shop/HR) keep their own independent hashes — useful for
   employees who only have a single portal.

4. **Audit everything privileged.** Every login, every portal switch,
   every directory mutation lands in `admin_audit` so you can answer
   "who-changed-what-when" without grep'ing logs.

Schema — `user_directory` collection
------------------------------------
{
  id: uuid,
  email: lowercased,
  name: str,
  portals: ["admin"|"pm"|"shop"|"hr", ...],   # which portals this user gets
  password_hash: bcrypt str,                  # master password
  is_super_admin: bool,                       # cannot be deleted/disabled
  disabled: bool,
  must_change_password: bool,
  created_at, updated_at, last_login_at, last_login_portal,
}

Schema — `admin_audit` collection
---------------------------------
{
  id: uuid, ts: iso, actor_email: str, action: str,
  target_email: optional, diff: dict, ip: optional, user_agent: optional,
}
"""
from __future__ import annotations

import logging
import os
import uuid
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
from session_timeout import (
    clear_session_activity_for_user,
    has_active_session_activity,
)

logger = logging.getLogger(__name__)

ALLOWED_PORTALS = ("admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership")


# ─────────────────────────────────────────────────────────────────────
# Password hashing — bcrypt 12 rounds (matches PM/HR auth playbook spec)
# ─────────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ─────────────────────────────────────────────────────────────────────
# Public views (NEVER include _id or password_hash)
# ─────────────────────────────────────────────────────────────────────
def public_view(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "name": row.get("name") or "",
        "portals": sorted(set(row.get("portals") or [])),
        "is_super_admin": bool(row.get("is_super_admin")),
        "disabled": bool(row.get("disabled")),
        "must_change_password": bool(row.get("must_change_password")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "last_login_at": row.get("last_login_at"),
        "last_login_portal": row.get("last_login_portal"),
    }


# ─────────────────────────────────────────────────────────────────────
# Core lookups
# ─────────────────────────────────────────────────────────────────────
async def find_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    return await db.user_directory.find_one(
        {"email": email.strip().lower()}, {"_id": 0}
    )


async def find_by_id(db, user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    return await db.user_directory.find_one({"id": user_id}, {"_id": 0})


# ─────────────────────────────────────────────────────────────────────
# Creation + mutation
# ─────────────────────────────────────────────────────────────────────
async def create_directory_user(
    db,
    *,
    email: str,
    name: str,
    portals: List[str],
    password: str,
    is_super_admin: bool = False,
    must_change_password: bool = False,
) -> Dict[str, Any]:
    """Create a new directory user. Caller is responsible for auth
    (admin-strict only). Raises ValueError on bad input."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError("Valid email required.")
    if await find_by_email(db, email):
        raise ValueError("A directory user with that email already exists.")
    cleaned_portals = sorted({p for p in (portals or []) if p in ALLOWED_PORTALS})
    if not cleaned_portals:
        raise ValueError(
            "Must grant at least one portal (admin / pm / shop / hr)."
        )
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": (name or "").strip() or email.split("@")[0],
        "portals": cleaned_portals,
        "password_hash": hash_password(password),
        "is_super_admin": bool(is_super_admin),
        "disabled": False,
        "must_change_password": bool(must_change_password),
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "last_login_portal": None,
    }
    await db.user_directory.insert_one(row)
    return public_view(row)


async def update_directory_user(
    db,
    *,
    user_id: str,
    name: Optional[str] = None,
    portals: Optional[List[str]] = None,
    disabled: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """Mutate directory user. Super-admin rows are protected: their
    `is_super_admin` flag and `admin` portal cannot be removed, and they
    cannot be disabled. Returns updated public view or None."""
    row = await find_by_id(db, user_id)
    if not row:
        return None
    update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if name is not None:
        update["name"] = (name or "").strip() or row["email"].split("@")[0]
    if portals is not None:
        cleaned = sorted({p for p in portals if p in ALLOWED_PORTALS})
        if not cleaned:
            raise ValueError("Must grant at least one portal.")
        if row.get("is_super_admin") and "admin" not in cleaned:
            cleaned = sorted(set(cleaned + ["admin"]))
        update["portals"] = cleaned
    if disabled is not None:
        if row.get("is_super_admin") and disabled:
            raise ValueError("Cannot disable a super-admin account.")
        update["disabled"] = bool(disabled)
    await db.user_directory.update_one({"id": user_id}, {"$set": update})
    refreshed = await find_by_id(db, user_id)
    return public_view(refreshed)


async def delete_directory_user(db, *, user_id: str) -> bool:
    row = await find_by_id(db, user_id)
    if not row:
        return False
    if row.get("is_super_admin"):
        raise ValueError("Cannot delete a super-admin account.")
    await db.user_directory.delete_one({"id": user_id})
    return True


async def rotate_master_password(
    db, *, user_id: str, new_password: str, must_change: bool = False
) -> Optional[Dict[str, Any]]:
    """Force-reset master password (admin tool). Returns new public view."""
    if not new_password or len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    row = await find_by_id(db, user_id)
    if not row:
        return None
    await db.user_directory.update_one(
        {"id": user_id},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "must_change_password": bool(must_change),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return public_view(await find_by_id(db, user_id))


async def self_change_password(
    db, *, user_id: str, current_password: str, new_password: str
) -> bool:
    """User-initiated rotation. Verifies current pw, sets new, clears
    `must_change_password` flag. Returns True on success."""
    if not new_password or len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    row = await find_by_id(db, user_id)
    if not row:
        return False
    if not verify_password(current_password, row.get("password_hash") or ""):
        return False
    await db.user_directory.update_one(
        {"id": user_id},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "must_change_password": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return True


# ─────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────
async def authenticate(
    db, *, email: str, password: str
) -> Optional[Dict[str, Any]]:
    """Verify email+password against the directory. Returns the raw row
    (NOT public view — caller may need password_hash for token signing).
    Returns None when no match / disabled / wrong pw."""
    row = await find_by_email(db, email)
    if not row:
        return None
    if row.get("disabled"):
        return None
    if not verify_password(password, row.get("password_hash") or ""):
        return None
    return row


async def stamp_last_login(db, *, user_id: str, portal: str) -> None:
    """Record last-login timestamp + portal. Best-effort; failures
    are logged but don't block the login response."""
    try:
        await db.user_directory.update_one(
            {"id": user_id},
            {
                "$set": {
                    "last_login_at": datetime.now(timezone.utc).isoformat(),
                    "last_login_portal": portal,
                }
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[directory] stamp_last_login failed: {e}")


# ─────────────────────────────────────────────────────────────────────
# Admin audit log
# ─────────────────────────────────────────────────────────────────────
async def write_audit(
    db,
    *,
    actor_email: str,
    action: str,
    target_email: Optional[str] = None,
    diff: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Append-only audit log. Never raises — audit must not break flows."""
    try:
        await db.admin_audit.insert_one(
            {
                "id": str(uuid.uuid4()),
                "ts": datetime.now(timezone.utc).isoformat(),
                "actor_email": (actor_email or "").lower(),
                "action": action,
                "target_email": (target_email or "").lower() or None,
                "diff": diff or {},
                "ip": ip,
                "user_agent": (user_agent or "")[:200] or None,
            }
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[audit] write failed: action={action} err={e}")


async def list_audit(
    db,
    *,
    limit: int = 100,
    skip: int = 0,
    actor: Optional[str] = None,
    action: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if actor:
        q["actor_email"] = actor.lower()
    if action:
        q["action"] = action
    cursor = db.admin_audit.find(q, {"_id": 0}).sort("ts", -1).skip(skip).limit(limit)
    return [r async for r in cursor]


# ─────────────────────────────────────────────────────────────────────
# Bootstrap super-admin (runs once at startup)
# ─────────────────────────────────────────────────────────────────────
async def bootstrap_super_admin(db) -> None:
    """Idempotent. Reads SUPER_ADMIN_EMAIL + SUPER_ADMIN_BOOTSTRAP_PASSWORD
    from env. If the email already exists in the directory, do nothing.
    If not, create the account with all four portals + is_super_admin=true.
    After first successful bootstrap, the env vars are effectively
    ignored — the account becomes a normal (super-admin) row that can be
    rotated from the admin panel."""
    email = (os.environ.get("SUPER_ADMIN_EMAIL") or "").strip().lower()
    plain = (os.environ.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD") or "").strip()
    if not email or not plain:
        logger.info(
            "[directory] bootstrap skipped (SUPER_ADMIN_EMAIL / "
            "SUPER_ADMIN_BOOTSTRAP_PASSWORD not configured)"
        )
        return
    existing = await find_by_email(db, email)
    if existing:
        # Already seeded. Top up the portals list if any are missing
        # (covers the case where we add a new portal type later) but do
        # NOT touch the password — that's been chosen by the user.
        missing = [p for p in ALLOWED_PORTALS if p not in (existing.get("portals") or [])]
        if missing:
            await db.user_directory.update_one(
                {"id": existing["id"]},
                {"$set": {"portals": list(ALLOWED_PORTALS),
                          "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
            logger.info(f"[directory] topped up super-admin portals: added {missing}")
        return
    try:
        await create_directory_user(
            db,
            email=email,
            name="Super Admin",
            portals=list(ALLOWED_PORTALS),
            password=plain,
            is_super_admin=True,
            must_change_password=False,
        )
        await write_audit(
            db,
            actor_email="system",
            action="bootstrap_super_admin",
            target_email=email,
            diff={"portals": list(ALLOWED_PORTALS), "is_super_admin": True},
        )
        logger.info(f"[directory] super-admin bootstrapped: {email}")
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[directory] bootstrap failed: {e}")


# ─────────────────────────────────────────────────────────────────────
# Cross-portal token bundling
# ─────────────────────────────────────────────────────────────────────
def make_directory_token() -> str:
    """Opaque session token written into a server-side session store
    (`directory_sessions` collection). Used to identify the multi-portal
    user; per-portal tokens (admin/pm/shop/hr) are minted separately."""
    return secrets.token_urlsafe(32)


async def persist_session(db, *, token: str, user_id: str, ttl_seconds: int = 60 * 60 * 12) -> None:
    """Store a server-side session for the directory token. Default TTL
    is 12 hours. Index `expires_at` for TTL eviction (best-effort)."""
    now = datetime.now(timezone.utc)
    try:
        await db.directory_sessions.delete_many({"user_id": user_id})
    except Exception as e:  # noqa: BLE001
        logger.warning("[directory] prior session cleanup failed: %s", e)
    await db.directory_sessions.insert_one(
        {
            "id": str(uuid.uuid4()),
            "token": token,
            "user_id": user_id,
            "created_at": now.isoformat(),
            "expires_at_ts": int(now.timestamp()) + ttl_seconds,
        }
    )


async def session_user(db, *, token: str) -> Optional[Dict[str, Any]]:
    """Resolve a directory session token → public view of its user.
    Returns None if expired, missing, or user disabled."""
    if not token:
        return None
    sess = await db.directory_sessions.find_one({"token": token}, {"_id": 0})
    if not sess:
        return None
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if sess.get("expires_at_ts", 0) < now_ts:
        return None
    row = await find_by_id(db, sess["user_id"])
    if not row or row.get("disabled"):
        return None
    return row


async def kill_session(db, *, token: str) -> None:
    if token:
        await db.directory_sessions.delete_one({"token": token})



# ─────────────────────────────────────────────────────────────────────
# TRACK 15.32 (2026-02) — per-user admin token
# ─────────────────────────────────────────────────────────────────────
# The shared ADMIN_PASSWORD HMAC was retired with this track. Per-user
# admin tokens follow the same `<user_id>.<HMAC>` shape used by
# `pm_auth.make_pm_token` and `shop_users.make_shop_user_token`. The
# HMAC binds to ADMIN_HMAC_SECRET + ADMIN_SESSION_EPOCH + user_id +
# password_hash[:16] so:
#   • A directory password rotation instantly invalidates extant tokens.
#   • A bumped ADMIN_SESSION_EPOCH wipes every per-user admin token.
#   • Tokens carry the user identity; session_activity attribution is
#     restored on every privileged action.
import hashlib as _h  # noqa: E402
import hmac as _hmac  # noqa: E402


def _admin_hmac_secret() -> bytes:
    """Same secret/epoch envelope used by the shop/pm minters."""
    s = os.environ.get("ADMIN_HMAC_SECRET") or ""
    if not s:
        # Hard error — admin tokens MUST be deterministic across restarts
        # for session_activity to survive logouts.
        raise RuntimeError(
            "ADMIN_HMAC_SECRET must be set to mint directory admin tokens."
        )
    return s.encode("utf-8")


def _admin_session_epoch() -> str:
    return (os.environ.get("ADMIN_SESSION_EPOCH") or "1").strip()


def make_directory_admin_token(user_id: str, password_hash: str) -> str:
    """Mint `<user_id>.<HMAC>` for an admin-authorized directory user.
    Mirrors `pm_auth.make_pm_token` / `shop_users.make_shop_user_token`.
    """
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash are required")
    msg = (
        f"epoch={_admin_session_epoch()}|admin:{user_id}:{password_hash[:16]}"
    ).encode()
    sig = _hmac.new(_admin_hmac_secret(), msg, _h.sha256).hexdigest()
    return f"{user_id}.{sig}"


def _make_directory_admin_session_token_from_nonce(user_id: str, password_hash: str, nonce: str) -> str:
    if not user_id or not password_hash or not nonce:
        raise ValueError("user_id, password_hash, and nonce are required")
    msg = (
        f"epoch={_admin_session_epoch()}|admin-session:{user_id}:{nonce}:{password_hash[:16]}"
    ).encode()
    sig = _hmac.new(_admin_hmac_secret(), msg, _h.sha256).hexdigest()
    return f"{user_id}.{nonce}.{sig}"


def make_directory_admin_session_token(user_id: str, password_hash: str, session_token: str) -> str:
    """Mint a session-scoped admin token for shared preview/runtime use.

    Shape: ``<user_id>.<nonce>.<HMAC>`` where the nonce is derived from the
    directory session token. This prevents concurrent shared-account logins
    from stamping over the same deterministic admin token row.
    """
    if not user_id or not password_hash or not session_token:
        raise ValueError("user_id, password_hash, and session_token are required")
    nonce = _h.sha256(session_token.encode("utf-8")).hexdigest()[:16]
    return _make_directory_admin_session_token_from_nonce(user_id, password_hash, nonce)


def _parse_directory_admin_token(token: str) -> Optional[Tuple[str, Optional[str], str]]:
    if not token or "." not in token:
        return None
    parts = token.split(".")
    if len(parts) == 2:
        uid, sig = parts
        if not uid or not sig or len(sig) != 64:
            return None
        return uid, None, sig
    if len(parts) == 3:
        uid, nonce, sig = parts
        if not uid or not nonce or not sig or len(sig) != 64:
            return None
        return uid, nonce, sig
    return None


async def is_valid_directory_admin_token_async(
    db, token: str,
    *,
    allow_unbound_directory_session: bool = True,
) -> Optional[Dict[str, Any]]:
    """Validate a per-user admin token. Returns the directory row on
    success, None on failure. Disabled users + users without the
    `admin` portal are rejected even with a valid signature."""
    parsed = _parse_directory_admin_token(token)
    if not parsed:
        return None
    uid, nonce, _sig = parsed
    row = await find_by_id(db, uid)
    if not row or row.get("disabled"):
        return None
    if "admin" not in (row.get("portals") or []):
        return None
    pwh = row.get("password_hash") or ""
    if not pwh:
        return None
    expected = (
        _make_directory_admin_session_token_from_nonce(uid, pwh, nonce)
        if nonce
        else make_directory_admin_token(uid, pwh)
    )
    if not _hmac.compare_digest(token, expected):
        return None
    if not await has_active_session_activity(
        db,
        token,
        allow_unbound_directory_session=allow_unbound_directory_session,
    ):
        return None
    return row
