"""
field_leadership_users.py — DB-backed Field Leadership user roster.

iter314 · Operational identity expansion. Mirrors `hr_users.py` /
`shop_users.py` EXACTLY — same bcrypt primitives, same token scheme,
same HMAC binding, same reset-token TTL. The only differences are:

  - Collection name: `field_leadership_users`
  - Token short-name in HMAC payload: `fl_user`
  - Default role: "Superintendent" (vs HR's "HR Coordinator")
  - Initial seed: a single test/seed user per operator approval

Field Leadership means: Superintendents · Foremen · Truck Bosses ·
Working Supervisors · approved operational field leaders. NOT general
employees, laborers, or crew. This role is operationally bounded.

Schema (db.field_leadership_users):
  id                   str (uuid)
  name                 str
  email                str (lowercase canonical key)
  phone                str (optional)
  role                 str  e.g. "Superintendent", "Foreman",
                            "Truck Boss", "Working Supervisor"
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
from session_timeout import has_active_session_activity

logger = logging.getLogger(__name__)


# Allowed roles for Field Leadership users — operationally bounded.
ALLOWED_FL_ROLES = {
    "Superintendent",
    "Foreman",
    "Truck Boss",
    "Working Supervisor",
    "Field Supervisor",
}


# ─────────────────────────────────────────────────────────────────
# Phase V.2 · FL Role Standardization (2026-05-29)
# ─────────────────────────────────────────────────────────────────
# Canonical Field-Leadership role ladder.  Permissions use the
# canonical value; UI displays the label.  Aliases map legacy
# free-form roles into the canonical ladder safely.  UNCERTAIN
# mappings (`General Foreman`, `Field Supervisor`, `Truck Boss`,
# `Working Supervisor`) are surfaced as `_uncertain_role_value` on
# the public roster so the operator can review and confirm in a
# follow-up directive.  Doctrine:
#   - FL_ROLE_ENUM_CERTIFICATION.md
#   - LEGACY_ROLE_MAPPING_REVIEW.md
FL_CANONICAL_ROLES = {
    "sr_superintendent": "Sr. Superintendent",
    "superintendent":    "Superintendent",
    "foreman":           "Foreman",
    "leadman":           "Leadman",
}

# Hard aliases — confidently mapped.  Compared case-insensitively.
FL_ROLE_ALIASES_HARD = {
    "sr. superintendent":      "sr_superintendent",
    "sr superintendent":       "sr_superintendent",
    "senior superintendent":   "sr_superintendent",
    "superintendent":          "superintendent",
    "foreman":                 "foreman",
    "leadman":                 "leadman",
    "crew lead":               "leadman",
    "crewlead":                "leadman",
}

# Uncertain aliases — proposed canonical default, but flagged on the
# public roster so the operator can review/override.  Each entry is
# (proposed_canonical, note).
FL_ROLE_ALIASES_UNCERTAIN = {
    "general foreman":    ("foreman",        "operator review · could be Foreman or Leadman"),
    "field supervisor":   ("superintendent", "operator review · could be Superintendent or Foreman"),
    "truck boss":         ("leadman",        "operator review · trucking lead role · likely Leadman"),
    "working supervisor": ("foreman",        "operator review · field-working lead · likely Foreman"),
}

# Back-compat: the legacy enum is still consumed by older create /
# patch payload validation.  Expanded so old free-form role strings
# still validate during the transition window.  New canonical writes
# go through `_canonical_role()`.
ALLOWED_FL_ROLES = {
    # canonical labels
    "Sr. Superintendent",
    "Superintendent",
    "Foreman",
    "Leadman",
    # legacy labels still in the wild
    "Truck Boss",
    "Working Supervisor",
    "Field Supervisor",
    "General Foreman",
}


def _canonical_role(raw_role: str) -> Dict[str, Any]:
    """
    Resolve an arbitrary `role` string to:
      {
        "value": <canonical key | "unknown">,
        "label": <display label>,
        "uncertain": <True iff alias is in FL_ROLE_ALIASES_UNCERTAIN>,
        "uncertain_note": <reviewer note or None>,
      }
    Never raises.  Unknown legacy strings echo back as `value=unknown`,
    `label=<raw>` so the UI can still render them and they do not
    silently get auto-mapped to a different role.
    """
    key = (raw_role or "").strip().lower()
    if key in FL_ROLE_ALIASES_HARD:
        canon = FL_ROLE_ALIASES_HARD[key]
        return {
            "value": canon,
            "label": FL_CANONICAL_ROLES[canon],
            "uncertain": False,
            "uncertain_note": None,
        }
    if key in FL_ROLE_ALIASES_UNCERTAIN:
        canon, note = FL_ROLE_ALIASES_UNCERTAIN[key]
        return {
            "value": canon,
            "label": FL_CANONICAL_ROLES[canon],
            "uncertain": True,
            "uncertain_note": note,
        }
    # Unknown — preserve raw, never guess.
    return {
        "value": "unknown",
        "label": (raw_role or "").strip() or "Unknown",
        "uncertain": True,
        "uncertain_note": "unrecognized legacy role · operator review required",
    }


# ----- helpers ---------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in doc:
        doc.pop("_id")
    email = (doc.get("email") or "").strip().lower()
    raw_role = (doc.get("role") or "Superintendent").strip()
    # Phase V.2 · FL Role Standardization: accept canonical labels
    # (Sr. Superintendent · Superintendent · Foreman · Leadman) AND
    # legacy free-form roles (Truck Boss · Working Supervisor · Field
    # Supervisor · General Foreman) so historical create / patch
    # payloads continue to validate.  Unknown values default to
    # Superintendent to preserve the iter314 behavior.
    role = raw_role if raw_role in ALLOWED_FL_ROLES else "Superintendent"
    return {
        "id": doc.get("id") or str(uuid.uuid4()),
        "name": (doc.get("name") or "").strip(),
        "email": email,
        "phone": (doc.get("phone") or "").strip(),
        "role": role,
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


# Initial roster — seeded once per operator-approved iter314 plan.
INITIAL_FL_USERS: List[Dict[str, str]] = [
    {
        "name": "Field Leader",
        "email": "fieldleader@mascigc.com",
        "role": "Superintendent",
    },
]


async def seed_field_leadership_users(db) -> None:
    """Idempotent seed: index on email + insert initial user if empty."""
    try:
        await db.field_leadership_users.create_index("email", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"field_leadership_users index: {e}")
    if await db.field_leadership_users.count_documents({}) > 0:
        return
    docs = [_normalize(r) for r in INITIAL_FL_USERS]
    if docs:
        await db.field_leadership_users.insert_many(docs)
        logger.info(
            "field_leadership_users seeded %d initial users (no password yet)",
            len(docs),
        )


# ----- token helpers (per-user, bcrypt-bound) --------------------------

def _fl_session_epoch() -> str:
    return os.environ.get("ADMIN_SESSION_EPOCH", "1").strip() or "1"


def make_fl_user_token(user_id: str, password_hash: str) -> str:
    """`<user_id>.<hmac>` — same scheme as HR/PM tokens."""
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    msg = f"epoch={_fl_session_epoch()}|fl_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def parse_fl_user_token(token: str) -> Optional[Tuple[str, str]]:
    if not token or "." not in token:
        return None
    uid, _, sig = token.partition(".")
    if not uid or not sig or len(sig) != 64:
        return None
    return uid, sig


async def is_valid_fl_user_token_async(
    db,
    token: str,
    *,
    allow_unbound_directory_session: bool = False,
) -> Optional[dict]:
    parsed = parse_fl_user_token(token)
    if not parsed:
        return None
    user_id, _ = parsed
    user = await db.field_leadership_users.find_one({"id": user_id}, {"_id": 0})
    if user and not user.get("disabled"):
        pwh = user.get("password_hash") or ""
        if pwh:
            expected = make_fl_user_token(user_id, pwh)
            if hmac.compare_digest(token, expected) and await has_active_session_activity(
                db,
                token,
                allow_unbound_directory_session=allow_unbound_directory_session,
            ):
                return user
    # iter345 · FL Phase B · Hybrid · validate directory-granted FL tokens.
    # If the embedded id isn't in field_leadership_users, look it up in
    # user_directory and require an active `field_leadership` portal
    # grant. The token must still HMAC against the directory user's
    # current password_hash (so revoking via password reset cascades).
    dir_user = await db.user_directory.find_one({"id": user_id}, {"_id": 0})
    if not dir_user or dir_user.get("disabled"):
        return None
    if "field_leadership" not in (dir_user.get("portals") or []):
        return None
    pwh = dir_user.get("password_hash") or ""
    if not pwh:
        return None
    expected = make_fl_user_token(user_id, pwh)
    if not hmac.compare_digest(token, expected):
        return None
    if not await has_active_session_activity(
        db,
        token,
        allow_unbound_directory_session=allow_unbound_directory_session,
    ):
        return None
    # Return a normalized FL-user-shaped view so downstream code that
    # reads `user["id"]`, `user["email"]`, etc. keeps working unchanged.
    return {
        "id": dir_user.get("id"),
        "email": dir_user.get("email"),
        "name": dir_user.get("name") or dir_user.get("email"),
        "role": "Cross-Portal Grant",
        "is_active": True,
        "disabled": bool(dir_user.get("disabled")),
        "must_change_password": False,
        "_directory_user": True,
        "granted_portals": dir_user.get("portals") or [],
    }


# ----- DB ops ----------------------------------------------------------

async def list_fl_users(db, only_active: bool = False) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"is_active": True} if only_active else {}
    cursor = db.field_leadership_users.find(q, {"_id": 0}).sort("name", 1)
    return await cursor.to_list(500)


async def add_fl_user(db, body: Dict[str, Any]) -> Dict[str, Any]:
    doc = _normalize(body)
    if not doc["name"]:
        raise ValueError("name is required")
    if not doc["email"] or "@" not in doc["email"]:
        raise ValueError("a valid email is required")
    if await db.field_leadership_users.find_one({"email": doc["email"]}, {"_id": 0}):
        raise ValueError(
            f"A field leadership user with email {doc['email']} already exists"
        )
    await db.field_leadership_users.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def update_fl_user(
    db, user_id: str, body: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    update_fields: Dict[str, Any] = {"updated_at": _now()}
    if "name" in body:
        update_fields["name"] = (body.get("name") or "").strip()
    if "email" in body:
        new_email = (body.get("email") or "").strip().lower()
        if not new_email or "@" not in new_email:
            raise ValueError("a valid email is required")
        clash = await db.field_leadership_users.find_one(
            {"email": new_email, "id": {"$ne": user_id}}, {"_id": 0}
        )
        if clash:
            raise ValueError(f"Another field leadership user already uses {new_email}")
        update_fields["email"] = new_email
    if "phone" in body:
        update_fields["phone"] = (body.get("phone") or "").strip()
    if "role" in body:
        role = (body.get("role") or "").strip()
        if role not in ALLOWED_FL_ROLES:
            raise ValueError(
                f"role must be one of {sorted(ALLOWED_FL_ROLES)}"
            )
        update_fields["role"] = role
    if "is_active" in body:
        update_fields["is_active"] = bool(body["is_active"])
    if "disabled" in body:
        update_fields["disabled"] = bool(body["disabled"])
    res = await db.field_leadership_users.update_one(
        {"id": user_id}, {"$set": update_fields}
    )
    if res.matched_count == 0:
        return None
    return await db.field_leadership_users.find_one({"id": user_id}, {"_id": 0})


async def delete_fl_user(db, user_id: str) -> bool:
    res = await db.field_leadership_users.delete_one({"id": user_id})
    return res.deleted_count > 0


async def find_fl_user_by_email(db, email: str) -> Optional[dict]:
    if not email:
        return None
    return await db.field_leadership_users.find_one(
        {"email": email.strip().lower()}, {"_id": 0}
    )


async def set_fl_user_password(
    db, user_id: str, plain_password: str, *, must_change: bool
) -> Optional[dict]:
    user = await db.field_leadership_users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return None
    pwh = hash_password(plain_password)
    await db.field_leadership_users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": pwh,
            "must_change_password": bool(must_change),
            "password_set_at": _now(),
            "updated_at": _now(),
        }},
    )
    return await db.field_leadership_users.find_one({"id": user_id}, {"_id": 0})


async def stamp_fl_login(db, user_id: str, ip: Optional[str] = None) -> None:
    fields: dict = {"last_login_at": _now()}
    if ip:
        fields["last_login_ip"] = ip
    await db.field_leadership_users.update_one({"id": user_id}, {"$set": fields})


# ----- Self-service password reset ------------------------------------
# Mirrors hr_users.make_hr_reset_token EXACTLY.

_FL_RESET_TOKEN_TTL_SECONDS = 30 * 60  # 30 minutes


def make_fl_reset_token(user_id: str, password_hash: str) -> str:
    """``<exp_unix>.<user_id>.<hmac>`` — single-use, 30-min TTL."""
    if not user_id or not password_hash:
        raise ValueError("user_id and password_hash required")
    exp = int(_time.time()) + _FL_RESET_TOKEN_TTL_SECONDS
    msg = f"reset|exp={exp}|fl_user:{user_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{user_id}.{sig}"


async def consume_fl_reset_token(db, token: str) -> Optional[dict]:
    if not token or token.count(".") != 2:
        return None
    exp_str, user_id, sig = token.split(".", 2)
    try:
        exp = int(exp_str)
    except ValueError:
        return None
    if exp < int(_time.time()):
        return None
    user = await db.field_leadership_users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("disabled"):
        return None
    pwh = user.get("password_hash") or ""
    if not pwh:
        return None
    msg = f"reset|exp={exp}|fl_user:{user_id}:{pwh[:16]}".encode()
    expected_sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return user


def public_fl_user_view(user: dict) -> dict:
    if not user:
        return {}
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    safe["has_password"] = bool(user.get("password_hash"))
    return safe


__all__ = [
    "ALLOWED_FL_ROLES",
    "FL_CANONICAL_ROLES",
    "FL_ROLE_ALIASES_HARD",
    "FL_ROLE_ALIASES_UNCERTAIN",
    "_canonical_role",
    "seed_field_leadership_users",
    "list_fl_users",
    "add_fl_user",
    "update_fl_user",
    "delete_fl_user",
    "find_fl_user_by_email",
    "set_fl_user_password",
    "stamp_fl_login",
    "make_fl_user_token",
    "is_valid_fl_user_token_async",
    "make_fl_reset_token",
    "consume_fl_reset_token",
    "public_fl_user_view",
    "verify_password",
    "generate_temp_password",
]
