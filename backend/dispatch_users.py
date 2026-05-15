"""
dispatch_users.py — DB-backed Dispatch Portal user roster.

Mirrors `hr_users.py` exactly so admins can add/remove Safety personnel
(Dispatcher, Dispatcher, Dispatcher) and issue per-person
passwords without redeploying. Reuses bcrypt + token primitives from
`pm_auth.py` for consistency across all 5 portals.

Schema (db.dispatch_users):
  id                   str (uuid)
  name                 str
  email                str (lowercase canonical key)
  phone                str (optional)
  role                 str  e.g. "Dispatcher", "Dispatcher"
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
import time as _time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pm_auth import (
    hash_password,
    verify_password,
    generate_temp_password,
    _pm_hmac_secret,
)

logger = logging.getLogger(__name__)


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
        "role": (doc.get("role") or "Dispatcher").strip(),
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


# Initial roster — seeded once on first boot if empty.
INITIAL_DISPATCH_USERS: List[Dict[str, str]] = [
    {"name": "Dispatcher", "email": "dispatch@mascigc.com", "role": "Dispatcher"},
]


async def seed_dispatch_users(db) -> None:
    """Idempotent seed: index on email + insert initial users if empty."""
    try:
        await db.dispatch_users.create_index("email", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"dispatch_users index: {e}")
    if await db.dispatch_users.count_documents({}) > 0:
        return
    docs = [_normalize(r) for r in INITIAL_DISPATCH_USERS]
    if docs:
        await db.dispatch_users.insert_many(docs)
        logger.info(f"dispatch_users seeded {len(docs)} initial users")


# ----- token helpers (per-user, bcrypt-bound) --------------------------

def _dispatch_session_epoch() -> str:
    return os.environ.get("ADMIN_SESSION_EPOCH", "1").strip() or "1"


def make_dispatch_user_token(user_id: str, password_hash: str) -> str:
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    msg = f"epoch={_dispatch_session_epoch()}|dispatch_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def parse_dispatch_user_token(token: str) -> Optional[Tuple[str, str]]:
    if not token or "." not in token:
        return None
    uid, _, sig = token.partition(".")
    if not uid or not sig or len(sig) != 64:
        return None
    return uid, sig


async def is_valid_dispatch_user_token_async(db, token: str) -> Optional[dict]:
    parsed = parse_dispatch_user_token(token)
    if not parsed:
        return None
    user_id, _ = parsed
    user = await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("disabled"):
        return None
    pwh = user.get("password_hash") or ""
    if not pwh:
        return None
    expected = make_dispatch_user_token(user_id, pwh)
    if not hmac.compare_digest(token, expected):
        return None
    return user


# ----- DB ops ----------------------------------------------------------

async def list_dispatch_users(db, only_active: bool = False) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"is_active": True} if only_active else {}
    cursor = db.dispatch_users.find(q, {"_id": 0}).sort("name", 1)
    return await cursor.to_list(500)


async def add_dispatch_user(db, body: Dict[str, Any]) -> Dict[str, Any]:
    doc = _normalize(body)
    if not doc["name"]:
        raise ValueError("name is required")
    if not doc["email"] or "@" not in doc["email"]:
        raise ValueError("a valid email is required")
    if await db.dispatch_users.find_one({"email": doc["email"]}, {"_id": 0}):
        raise ValueError(f"A Dispatch user with email {doc['email']} already exists")
    await db.dispatch_users.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_dispatch_user(db, user_id: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    update_fields: Dict[str, Any] = {"updated_at": _now()}
    if "name" in body:
        update_fields["name"] = (body.get("name") or "").strip()
    if "email" in body:
        new_email = (body.get("email") or "").strip().lower()
        if not new_email or "@" not in new_email:
            raise ValueError("a valid email is required")
        clash = await db.dispatch_users.find_one(
            {"email": new_email, "id": {"$ne": user_id}}, {"_id": 0}
        )
        if clash:
            raise ValueError(f"Another Dispatch user already uses {new_email}")
        update_fields["email"] = new_email
    if "phone" in body:
        update_fields["phone"] = (body.get("phone") or "").strip()
    if "role" in body:
        update_fields["role"] = (body.get("role") or "Dispatcher").strip()
    if "is_active" in body:
        update_fields["is_active"] = bool(body["is_active"])
    if "disabled" in body:
        update_fields["disabled"] = bool(body["disabled"])
    res = await db.dispatch_users.update_one({"id": user_id}, {"$set": update_fields})
    if res.matched_count == 0:
        return None
    return await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})


async def delete_dispatch_user(db, user_id: str) -> bool:
    res = await db.dispatch_users.delete_one({"id": user_id})
    return res.deleted_count > 0


async def find_dispatch_user_by_email(db, email: str) -> Optional[dict]:
    if not email:
        return None
    return await db.dispatch_users.find_one({"email": email.strip().lower()}, {"_id": 0})


async def set_dispatch_user_password(db, user_id: str, plain_password: str, *, must_change: bool) -> Optional[dict]:
    user = await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return None
    pwh = hash_password(plain_password)
    await db.dispatch_users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": pwh,
            "must_change_password": bool(must_change),
            "password_set_at": _now(),
            "updated_at": _now(),
        }},
    )
    return await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})


async def stamp_dispatch_login(db, user_id: str, ip: Optional[str] = None) -> None:
    fields: dict = {"last_login_at": _now()}
    if ip:
        fields["last_login_ip"] = ip
    await db.dispatch_users.update_one({"id": user_id}, {"$set": fields})


# ----- Self-service password reset ------------------------------------
_DISPATCH_RESET_TOKEN_TTL_SECONDS = 30 * 60


def make_dispatch_reset_token(user_id: str, password_hash: str) -> str:
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    exp = int(_time.time()) + _DISPATCH_RESET_TOKEN_TTL_SECONDS
    msg = f"reset|exp={exp}|dispatch_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{user_id}.{sig}"


async def consume_dispatch_reset_token(db, token: str) -> Optional[dict]:
    if not token or token.count(".") != 2:
        return None
    exp_str, user_id, sig = token.split(".", 2)
    try:
        exp = int(exp_str)
    except ValueError:
        return None
    if exp < int(_time.time()):
        return None
    user = await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("disabled"):
        return None
    pwh = user.get("password_hash") or ""
    if not pwh:
        return None
    msg = f"reset|exp={exp}|dispatch_user:{user_id}:{pwh[:16]}".encode()
    expected_sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return user


def public_dispatch_user_view(user: dict) -> dict:
    if not user:
        return {}
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    safe["has_password"] = bool(user.get("password_hash"))
    return safe


__all__ = [
    "seed_dispatch_users",
    "list_dispatch_users",
    "add_dispatch_user",
    "update_dispatch_user",
    "delete_dispatch_user",
    "find_dispatch_user_by_email",
    "set_dispatch_user_password",
    "stamp_dispatch_login",
    "make_dispatch_user_token",
    "is_valid_dispatch_user_token_async",
    "make_dispatch_reset_token",
    "consume_dispatch_reset_token",
    "public_dispatch_user_view",
    "verify_password",
    "generate_temp_password",
]
