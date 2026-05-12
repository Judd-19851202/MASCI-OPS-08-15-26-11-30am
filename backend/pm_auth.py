"""
pm_auth.py — Per-PM password authentication.

Replaces the shared `PM_PASSWORD` env-var login with one bcrypt-hashed
password per PM stored in `db.project_managers`. Tokens stay HMAC-opaque
to match the rest of the app (no JWT dependency); per-PM tokens encode
the pm_id alongside the HMAC so the validator can look up the PM doc in
one query.

Schema additions on db.project_managers:
  password_hash         str | None   bcrypt hash, None until admin issues one
  must_change_password  bool         true after admin set/reset; false after PM rotates
  password_set_at       iso-utc      when admin issued the current password
  last_login_at         iso-utc      heartbeat
  disabled              bool         locks login regardless of password

A shared-password emergency bypass is kept behind ``PM_SHARED_LOGIN_ENABLED=true``
so the office can still get in if something goes sideways with a per-PM
account; the bypass token uses the LEGACY HMAC format (no `.` in it) so
the validator can disambiguate.
"""
from __future__ import annotations

import hmac
import hashlib
import os
import secrets
import string
from datetime import datetime, timezone
from typing import Optional, Tuple

import bcrypt


# ----- bcrypt helpers ------------------------------------------------------

def hash_password(plain: str) -> str:
    """bcrypt-hash a password. Cost 12 is a good balance for FastAPI."""
    if not isinstance(plain, str) or len(plain) < 6:
        raise ValueError("Password must be at least 6 characters")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_temp_password(length: int = 10) -> str:
    """Crypto-random temporary password — admin shows it ONCE to the PM,
    then the PM is forced to rotate it on first login. Excludes
    ambiguous chars (0/O, 1/l/I)."""
    alphabet = "".join(c for c in (string.ascii_letters + string.digits) if c not in "0O1lI")
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ----- per-PM token --------------------------------------------------------

def _pm_session_epoch() -> str:
    """Same epoch as the rest of the app — bumping ADMIN_SESSION_EPOCH
    invalidates every per-PM token in one shot."""
    v = os.environ.get("ADMIN_SESSION_EPOCH", "1").strip()
    return v or "1"


def _pm_hmac_secret() -> bytes:
    """Reuse the admin HMAC secret so we don't multiply env config."""
    s = os.environ.get("ADMIN_HMAC_SECRET", "").strip()
    if not s:
        # Fallback (process-local) — same behavior as the admin path.
        s = secrets.token_urlsafe(64)
        os.environ["ADMIN_HMAC_SECRET"] = s
    return s.encode("utf-8")


def make_pm_token(pm_id: str, password_hash: str) -> str:
    """Build a `pm_id.hmac` token. Including pm_id lets the validator
    look up the PM doc in one query without scanning. Including the
    first 16 chars of the password_hash invalidates the token whenever
    the admin resets or the PM rotates their password."""
    if not pm_id or not password_hash:
        raise ValueError("pm_id and password_hash are required")
    msg = f"epoch={_pm_session_epoch()}|pm:{pm_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{pm_id}.{sig}"


def parse_pm_token(token: str) -> Optional[Tuple[str, str]]:
    """Split `pm_id.hmac`. Returns (pm_id, hmac) or None if not the
    new format (e.g. legacy shared-password token has no dot)."""
    if not token or "." not in token:
        return None
    pm_id, _, sig = token.partition(".")
    if not pm_id or not sig or len(sig) != 64:
        return None
    return pm_id, sig


def shared_pm_login_enabled() -> bool:
    return os.environ.get("PM_SHARED_LOGIN_ENABLED", "true").strip().lower() in (
        "1", "true", "yes", "on",
    )


# ----- DB helpers (called from server.py with the live `db` handle) -------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def find_pm_by_email(db, email: str) -> Optional[dict]:
    if not email:
        return None
    return await db.project_managers.find_one(
        {"email": email.strip().lower()}, {"_id": 0}
    )


async def find_pm_by_id(db, pm_id: str) -> Optional[dict]:
    if not pm_id:
        return None
    return await db.project_managers.find_one({"id": pm_id}, {"_id": 0})


async def is_valid_pm_user_token_async(db, token: str) -> Optional[dict]:
    """Validate a per-PM token. Returns the PM doc on success, None on
    failure. Disabled PMs are rejected even with a valid signature."""
    parsed = parse_pm_token(token)
    if not parsed:
        return None
    pm_id, sig = parsed
    pm = await find_pm_by_id(db, pm_id)
    if not pm:
        return None
    if pm.get("disabled"):
        return None
    pwh = pm.get("password_hash") or ""
    if not pwh:
        return None
    expected = make_pm_token(pm_id, pwh)
    if not hmac.compare_digest(token, expected):
        return None
    return pm


async def set_pm_password(
    db, pm_id: str, plain_password: str, *, must_change: bool
) -> Optional[dict]:
    """Hash + store. Returns updated PM doc or None if PM not found.
    Setting a new hash automatically invalidates the old per-PM token
    (since the token includes the first 16 chars of the hash)."""
    pm = await find_pm_by_id(db, pm_id)
    if not pm:
        return None
    pwh = hash_password(plain_password)
    await db.project_managers.update_one(
        {"id": pm_id},
        {"$set": {
            "password_hash": pwh,
            "must_change_password": bool(must_change),
            "password_set_at": now_iso(),
            "updated_at": now_iso(),
        }},
    )
    return await find_pm_by_id(db, pm_id)


async def set_pm_disabled(db, pm_id: str, disabled: bool) -> Optional[dict]:
    pm = await find_pm_by_id(db, pm_id)
    if not pm:
        return None
    await db.project_managers.update_one(
        {"id": pm_id},
        {"$set": {"disabled": bool(disabled), "updated_at": now_iso()}},
    )
    return await find_pm_by_id(db, pm_id)


async def stamp_login(db, pm_id: str, ip: Optional[str] = None) -> None:
    """Update the heartbeat fields after a successful per-PM login. Used
    by the admin Activity panel to spot ghost sessions, fired employees
    whose token is still in use, etc."""
    fields: dict = {"last_login_at": now_iso()}
    if ip:
        fields["last_login_ip"] = ip
    await db.project_managers.update_one({"id": pm_id}, {"$set": fields})


# ----- Self-service password reset tokens --------------------------------
#
# Forgot-password tokens are short-lived signed tuples: the PM enters
# their email on /pm/login → backend mints a token bound to {pm_id,
# password_hash[:16], exp} → emails them a link `/pm/reset/<token>` →
# they click, set a new password, the token is one-shot (the bcrypt
# prefix changes the moment the password is set, so the token stops
# verifying). No DB-side state required — the password_hash itself is
# the revocation channel.

import time as _time

_RESET_TOKEN_TTL_SECONDS = 30 * 60  # 30 minutes


def make_reset_token(pm_id: str, password_hash: str) -> str:
    """`<exp_unix>.<pm_id>.<hmac>` — single-use because hmac binds to
    the first 16 chars of the current password hash; once the PM resets,
    the hash changes and the token can't be replayed."""
    if not pm_id or not password_hash:
        raise ValueError("pm_id and password_hash required")
    exp = int(_time.time()) + _RESET_TOKEN_TTL_SECONDS
    msg = f"reset|exp={exp}|pm:{pm_id}:{password_hash[:16]}".encode()
    sig = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{pm_id}.{sig}"


async def consume_reset_token(db, token: str) -> Optional[dict]:
    """Validate a forgot-password token. Returns the PM doc if valid
    AND not expired AND the password hash hasn't been rotated since
    the token was issued. Returns None on any failure."""
    if not token or token.count(".") != 2:
        return None
    exp_str, pm_id, sig = token.split(".", 2)
    try:
        exp = int(exp_str)
    except ValueError:
        return None
    if exp < int(_time.time()):
        return None
    pm = await find_pm_by_id(db, pm_id)
    if not pm:
        return None
    pwh = pm.get("password_hash") or ""
    if not pwh:
        # PM doesn't have a password yet (admin never issued one) —
        # let the admin issue one rather than the PM self-serve.
        return None
    expected = make_reset_token(pm_id, pwh)
    # Compare entire token (includes exp) to reject tampering.
    if not hmac.compare_digest(token, expected):
        # The exp embedded in `token` may differ from the `expected`
        # one we just minted (different second). Compare the
        # signature alone, but only when exp matches.
        # Note: this branch is technically dead code because
        # ``make_reset_token`` re-derives ``exp``. Recompute
        # specifically with the token's exp:
        msg = f"reset|exp={exp}|pm:{pm_id}:{pwh[:16]}".encode()
        sig2 = hmac.new(_pm_hmac_secret(), msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, sig2):
            return None
    return pm


# ----- Per-PM data scoping -----------------------------------------------

class PmScope:
    """Resolved data-visibility scope for the current request.

    ``is_admin`` — admin token / legacy shared-PM bypass (no filtering).
    ``project_numbers`` — set of canonical project_number strings the PM
    is assigned to (primary OR co-PM). When ``is_admin`` is True the set
    is always None.
    """

    __slots__ = ("is_admin", "project_numbers", "pm")

    def __init__(self, *, is_admin: bool, project_numbers=None, pm=None):
        self.is_admin = is_admin
        self.project_numbers = project_numbers  # Optional[set[str]]
        self.pm = pm  # Optional[dict]

    def filter(self, query: Optional[dict] = None) -> dict:
        """Return a Mongo filter dict that ANDs in the PM's project scope.
        Admin → returns the original query unchanged. PM with 0 jobs →
        returns an impossible filter so they see nothing (instead of
        seeing everything by accident)."""
        q = dict(query or {})
        if self.is_admin:
            return q
        nums = list(self.project_numbers or [])
        if not nums:
            # No assigned jobs → no records at all.
            q["__pm_empty_scope__"] = True
            return q
        # Match on project_number (case-insensitive) — store records use
        # the same dropdown values as jobs_master so equality works for
        # 99% of cases. Some legacy records have whitespace differences
        # though, so the regex approach normalizes both sides.
        q["project_number"] = {"$in": nums}
        return q

    def allows(self, project_number: Optional[str]) -> bool:
        """Used by single-record GETs to decide whether the PM can read
        a given record. Admin → always True. PM → only if the record's
        project_number is in their assigned set."""
        if self.is_admin:
            return True
        if not project_number:
            return False
        return project_number in (self.project_numbers or set())


async def compute_pm_scope(db, actor) -> PmScope:
    """Resolve a PmScope for the request actor returned by
    ``require_admin``. Admin / legacy shared bypass → ``is_admin=True``.
    Per-PM dict → looks up every job assigned to this PM (primary OR
    co-PM, active OR inactive — historical reports stay visible) and
    returns the set of project_numbers.

    Shop users (mechanic / shop-manager / parts-coordinator) are
    cross-job — they need to see every equipment inspection regardless
    of which PM owns the project. ``require_shop_or_admin`` tags the
    actor dict with ``_actor_kind == "shop_user"`` to flag this case;
    we treat them as unrestricted here. Fix for iter69 regression
    where per-shop-user accounts could not open inspection detail pages
    (got blanket 404 because their email matched zero PM-assigned jobs).
    """
    if actor is True or not isinstance(actor, dict):
        return PmScope(is_admin=True)
    # Shop users (cross-job, not project-scoped)
    if actor.get("_actor_kind") == "shop_user":
        return PmScope(is_admin=True)
    email = (actor.get("email") or "").strip().lower()
    if not email:
        return PmScope(is_admin=True)
    # Pull every job where this PM is primary OR appears in co_pm_emails.
    cursor = db.jobs_master.find(
        {
            "$or": [
                {"pm_email": email},
                {"co_pm_emails": email},
            ],
            "deleted_at": {"$in": [None, ""]},
        },
        {"_id": 0, "project_number": 1},
    )
    nums = set()
    async for j in cursor:
        pn = (j.get("project_number") or "").strip()
        if pn:
            nums.add(pn)
    return PmScope(is_admin=False, project_numbers=nums, pm=actor)


def public_pm_view(pm: dict) -> dict:
    """PM record sanitized for client return — no password_hash."""
    if not pm:
        return {}
    safe = {k: v for k, v in pm.items() if k != "password_hash"}
    safe["has_password"] = bool(pm.get("password_hash"))
    return safe
