"""
shop_users.py — DB-backed Shop user roster with per-user passwords.

Mirrors `project_managers.py` so admins can add/remove shop personnel
(mechanics, shop manager, parts coordinator) and issue per-person
passwords without redeploying. Reuses the bcrypt + token primitives
already in `pm_auth.py` for consistency.

Schema (db.shop_users):
  id                   str (uuid)
  name                 str
  email                str (lowercase canonical key)
  phone                str (optional)
  role                 str  e.g. "Shop Manager", "Mechanic", "Parts"
  is_active            bool
  disabled             bool
  password_hash        str | None
  must_change_password bool
  password_set_at      iso-utc | None
  last_login_at        iso-utc | None
  created_at, updated_at  iso-utc
"""
from __future__ import annotations

import hmac
import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pm_auth import (
    hash_password,
    verify_password,
    generate_temp_password,
    _pm_hmac_secret,
)
from session_timeout import has_active_session_activity

logger = logging.getLogger(__name__)


# ----- helpers ---------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in doc:
        doc.pop("_id")
    email = (doc.get("email") or "").strip().lower()
    return {
        "id": doc.get("id") or str(uuid.uuid4()),
        "name": (doc.get("name") or "").strip(),
        "email": email,
        "phone": (doc.get("phone") or "").strip(),
        "role": (doc.get("role") or "Mechanic").strip(),
        "is_active": bool(doc.get("is_active", True)),
        "disabled": bool(doc.get("disabled", False)),
        "password_hash": doc.get("password_hash"),
        "must_change_password": bool(doc.get("must_change_password", False)),
        "password_set_at": doc.get("password_set_at"),
        "last_login_at": doc.get("last_login_at"),
        "last_login_ip": doc.get("last_login_ip"),
        "created_at": doc.get("created_at") or _now(),
        "updated_at": doc.get("updated_at") or _now(),
    }


# Track 15.67 Phase 3 · Tenant-safe seed resolver
# Resolved from `SHOP_SEED_USERS` env var. Format identical to safety.
def _resolve_initial_shop_users() -> List[Dict[str, str]]:
    raw = (os.environ.get("SHOP_SEED_USERS") or "").strip()
    if raw:
        out: List[Dict[str, str]] = []
        for entry in raw.split(","):
            parts = [p.strip() for p in entry.split("|")]
            if not parts or not parts[0] or "@" not in parts[0]:
                continue
            email = parts[0].lower()
            name = parts[1] if len(parts) > 1 and parts[1] else "Shop User"
            role = parts[2] if len(parts) > 2 and parts[2] else "Mechanic"
            out.append({"name": name, "email": email, "role": role})
        return out
    try:
        from tenant_context import is_masci as _is_masci
        masci_tenant = _is_masci()
    except Exception:
        masci_tenant = True
    if masci_tenant:
        return [
            {"name": "Shop Manager", "email": "shopmanager@mascigc.com", "role": "Shop Manager"},
        ]
    logger.warning(
        "shop_users seed: SHOP_SEED_USERS unset and tenant is not MASCI — "
        "refusing to seed MASCI personnel into a non-MASCI tenant."
    )
    return []


INITIAL_SHOP_USERS: List[Dict[str, str]] = _resolve_initial_shop_users()


async def seed_shop_users(db) -> None:
    """Idempotent seed: index on email + insert initial users if empty."""
    try:
        await db.shop_users.create_index("email", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"shop_users index: {e}")
    if await db.shop_users.count_documents({}) > 0:
        return
    docs = [_normalize(r) for r in INITIAL_SHOP_USERS]
    if docs:
        await db.shop_users.insert_many(docs)
        logger.info(f"shop_users seeded {len(docs)} initial users")
    else:
        logger.info("shop_users seed skipped — no initial users resolved (tenant-safe).")


# ----- token helpers (per-user, bcrypt-bound) --------------------------

def _shop_session_epoch() -> str:
    return os.environ.get("ADMIN_SESSION_EPOCH", "1").strip() or "1"


def make_shop_user_token(user_id: str, password_hash: str) -> str:
    """`<user_id>.<hmac>` — same scheme as PM tokens."""
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    msg = f"epoch={_shop_session_epoch()}|shop_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def parse_shop_user_token(token: str) -> Optional[Tuple[str, str]]:
    if not token or "." not in token:
        return None
    uid, _, sig = token.partition(".")
    if not uid or not sig or len(sig) != 64:
        return None
    return uid, sig


async def is_valid_shop_user_token_async(
    db,
    token: str,
    *,
    allow_unbound_directory_session: bool = False,
) -> Optional[dict]:
    parsed = parse_shop_user_token(token)
    if not parsed:
        return None
    user_id, _ = parsed
    user = await db.shop_users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("disabled"):
        return None
    pwh = user.get("password_hash") or ""
    if not pwh:
        return None
    expected = make_shop_user_token(user_id, pwh)
    if not hmac.compare_digest(token, expected):
        return None
    if not await has_active_session_activity(
        db,
        token,
        allow_unbound_directory_session=allow_unbound_directory_session,
    ):
        return None
    return user


# ----- DB ops ----------------------------------------------------------

async def list_shop_users(db, only_active: bool = False) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"is_active": True} if only_active else {}
    cursor = db.shop_users.find(q, {"_id": 0}).sort("name", 1)
    return await cursor.to_list(500)


async def add_shop_user(db, body: Dict[str, Any]) -> Dict[str, Any]:
    doc = _normalize(body)
    if not doc["name"]:
        raise ValueError("name is required")
    if not doc["email"] or "@" not in doc["email"]:
        raise ValueError("a valid email is required")
    if await db.shop_users.find_one({"email": doc["email"]}, {"_id": 0}):
        raise ValueError(f"A shop user with email {doc['email']} already exists")
    await db.shop_users.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_shop_user(db, user_id: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    update_fields: Dict[str, Any] = {"updated_at": _now()}
    if "name" in body:
        update_fields["name"] = (body.get("name") or "").strip()
    if "email" in body:
        new_email = (body.get("email") or "").strip().lower()
        if not new_email or "@" not in new_email:
            raise ValueError("a valid email is required")
        clash = await db.shop_users.find_one(
            {"email": new_email, "id": {"$ne": user_id}}, {"_id": 0}
        )
        if clash:
            raise ValueError(f"Another shop user already uses {new_email}")
        update_fields["email"] = new_email
    if "phone" in body:
        update_fields["phone"] = (body.get("phone") or "").strip()
    if "role" in body:
        update_fields["role"] = (body.get("role") or "Mechanic").strip()
    if "is_active" in body:
        update_fields["is_active"] = bool(body["is_active"])
    if "disabled" in body:
        update_fields["disabled"] = bool(body["disabled"])
    res = await db.shop_users.update_one({"id": user_id}, {"$set": update_fields})
    if res.matched_count == 0:
        return None
    return await db.shop_users.find_one({"id": user_id}, {"_id": 0})


async def delete_shop_user(db, user_id: str) -> bool:
    res = await db.shop_users.delete_one({"id": user_id})
    return res.deleted_count > 0


async def find_shop_user_by_email(db, email: str) -> Optional[dict]:
    if not email:
        return None
    return await db.shop_users.find_one(
        {"email": email.strip().lower()}, {"_id": 0}
    )


async def set_shop_user_password(
    db, user_id: str, plain_password: str, *, must_change: bool
) -> Optional[dict]:
    user = await db.shop_users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return None
    pwh = hash_password(plain_password)
    await db.shop_users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": pwh,
            "must_change_password": bool(must_change),
            "password_set_at": _now(),
            "updated_at": _now(),
        }},
    )
    return await db.shop_users.find_one({"id": user_id}, {"_id": 0})


async def stamp_shop_login(db, user_id: str, ip: Optional[str] = None) -> None:
    fields: dict = {"last_login_at": _now()}
    if ip:
        fields["last_login_ip"] = ip
    await db.shop_users.update_one({"id": user_id}, {"$set": fields})


# ----- Self-service password reset ------------------------------------
# Mirrors pm_auth.make_reset_token / consume_reset_token. The token is
# self-revoking: once the user resets, password_hash[:16] changes →
# the token's HMAC no longer matches.

import time as _time

_SHOP_RESET_TOKEN_TTL_SECONDS = 30 * 60  # 30 minutes


def make_shop_reset_token(user_id: str, password_hash: str) -> str:
    """``<exp_unix>.<user_id>.<hmac>`` — single-use, 30-min TTL.

    Bound to the first 16 chars of the current password_hash so any
    successful reset invalidates the token immediately.
    """
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    exp = int(_time.time()) + _SHOP_RESET_TOKEN_TTL_SECONDS
    msg = f"reset|exp={exp}|shop_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{user_id}.{sig}"


async def consume_shop_reset_token(db, token: str) -> Optional[dict]:
    """Validate a forgot-password token. Returns the shop user doc if
    valid AND not expired AND the password_hash hasn't been rotated.
    Returns None on any failure (no leakage of which step failed)."""
    if not token or token.count(".") != 2:
        return None
    exp_str, user_id, sig = token.split(".", 2)
    try:
        exp = int(exp_str)
    except ValueError:
        return None
    if exp < int(_time.time()):
        return None
    user = await db.shop_users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("disabled"):
        return None
    pwh = user.get("password_hash") or ""
    if not pwh:
        return None
    msg = f"reset|exp={exp}|shop_user:{user_id}:{pwh[:16]}".encode()
    expected_sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return user


def public_shop_user_view(user: dict) -> dict:
    if not user:
        return {}
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    safe["has_password"] = bool(user.get("password_hash"))
    return safe


# Re-export bcrypt verify so the login endpoint can use a single import
__all__ = [
    "seed_shop_users",
    "list_shop_users",
    "add_shop_user",
    "update_shop_user",
    "delete_shop_user",
    "find_shop_user_by_email",
    "set_shop_user_password",
    "stamp_shop_login",
    "make_shop_user_token",
    "is_valid_shop_user_token_async",
    "make_shop_reset_token",
    "consume_shop_reset_token",
    "public_shop_user_view",
    "verify_password",
    "generate_temp_password",
]
