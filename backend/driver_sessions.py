"""
driver_sessions.py · iter393 · Phase 11.2 · DLS Driver Magic-Link Sessions.

In-house magic-link + revokable session pattern for the Dispatch
Lifecycle System driver mobile surface.

Doctrine
--------
- **0 passwords, 0 enrollment.** Dispatcher issues a link; driver opens
  it; tap-and-work.
- **Single-use magic token, short-lived** (15 min default).
- **Session token, dispatcher-revokable** (12 h default · shift-bound).
- **No third-party auth provider.** Reuses ``ADMIN_HMAC_SECRET`` +
  ``ADMIN_SESSION_EPOCH`` (same env knobs as every other portal in the
  platform). Mirrors the per-PM/HR/Shop/Safety/Dispatch token pattern.

Two artefacts
-------------
1. **Magic token** (``secrets.token_urlsafe(32)``)
   - Stored as a sha256 hash on the ``dispatch_magic_links`` collection.
   - One row per magic link · ``used_at`` flips on first exchange ·
     ``expires_at`` has a TTL index.
2. **Session token** (``session_id.hmac``)
   - HMAC binds ``ADMIN_SESSION_EPOCH`` + session_id + driver_id.
   - Session row in ``dispatch_driver_sessions`` carries ``revoked_at``
     so dispatcher revocation invalidates the token immediately.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────
# Knobs (sensible defaults; .env overrides honoured)
# ─────────────────────────────────────────────────────────────────────
MAGIC_TOKEN_TTL_SECONDS = int(
    os.environ.get("DRIVER_MAGIC_TTL_SECONDS", "900"),         # 15 min
)
SESSION_TTL_SECONDS = int(
    os.environ.get("DRIVER_SESSION_TTL_SECONDS", "50400"),     # 14 h (shift)
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────
# Shared secret access (reuses the platform HMAC secret + epoch)
# ─────────────────────────────────────────────────────────────────────
def _hmac_secret() -> bytes:
    s = os.environ.get("ADMIN_HMAC_SECRET", "").strip()
    if not s:
        s = secrets.token_urlsafe(64)
        os.environ["ADMIN_HMAC_SECRET"] = s
    return s.encode("utf-8")


def _epoch() -> str:
    v = os.environ.get("ADMIN_SESSION_EPOCH", "1").strip()
    return v or "1"


# ─────────────────────────────────────────────────────────────────────
# Magic token primitives
# ─────────────────────────────────────────────────────────────────────
def generate_magic_token() -> str:
    """Random urlsafe token (~43 chars · ~256 bits of entropy)."""
    return secrets.token_urlsafe(32)


def hash_magic_token(token: str) -> str:
    """Store ONLY the sha256 of the magic token in the DB. Validation
    re-hashes the incoming token and matches on the hash so a DB leak
    never exposes the raw link."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────
# Session token primitives (HMAC pattern — mirrors pm_auth/hr_users)
# ─────────────────────────────────────────────────────────────────────
def make_session_token(session_id: str, driver_id: str) -> str:
    """Build a ``session_id.hmac`` token. Including the session_id lets
    the validator look up the session row in one query."""
    if not session_id or not driver_id:
        raise ValueError("session_id and driver_id are required")
    msg = f"epoch={_epoch()}|drv:{driver_id}:{session_id}".encode("utf-8")
    sig = hmac.new(_hmac_secret(), msg, hashlib.sha256).hexdigest()
    return f"{session_id}.{sig}"


def parse_session_token(token: str) -> Optional[Tuple[str, str]]:
    """Split ``session_id.hmac``. Returns (session_id, hmac) or None."""
    if not token or "." not in token:
        return None
    session_id, _, sig = token.partition(".")
    if not session_id or not sig or len(sig) != 64:
        return None
    return session_id, sig


# ─────────────────────────────────────────────────────────────────────
# Index setup
# ─────────────────────────────────────────────────────────────────────
async def ensure_driver_session_indexes(db) -> None:
    import asyncio
    try:
        await asyncio.gather(
            # Magic links — TTL on expires_at auto-prunes stale rows.
            db.dispatch_magic_links.create_index(
                "token_hash", unique=True, name="dml_token_hash_unique",
            ),
            db.dispatch_magic_links.create_index(
                "expires_at_ts", expireAfterSeconds=0, name="dml_ttl",
            ),
            db.dispatch_magic_links.create_index(
                [("tenant_id", 1), ("driver_id", 1), ("issued_at", -1)],
                name="dml_tenant_driver_issued",
            ),
            # Sessions — TTL on expires_at_ts auto-prunes ended shifts.
            db.dispatch_driver_sessions.create_index(
                "id", unique=True, name="dds_id_unique",
            ),
            db.dispatch_driver_sessions.create_index(
                "expires_at_ts", expireAfterSeconds=0, name="dds_ttl",
            ),
            db.dispatch_driver_sessions.create_index(
                [("tenant_id", 1), ("driver_id", 1), ("issued_at", -1)],
                name="dds_tenant_driver_issued",
            ),
            db.dispatch_driver_sessions.create_index(
                [("tenant_id", 1), ("revoked_at", 1)],
                name="dds_tenant_revoked",
            ),
        )
    except Exception:
        # Index conflicts on first-deploy are harmless; subsequent
        # restarts skip dedupe automatically.
        pass


# ─────────────────────────────────────────────────────────────────────
# DB ops — magic links
# ─────────────────────────────────────────────────────────────────────
class DriverIneligibleError(ValueError):
    """Raised when issue_magic_link is called for an employee that does
    not exist or is disabled. Caller (FastAPI route) should translate
    this into a 4xx response. iter437 Phase Sigma-III · P0 security.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


async def _validate_driver_eligibility(db, driver_id: str) -> Dict[str, Any]:
    """Phase Sigma-III gate: confirm `driver_id` resolves to a real,
    enabled employee row before any magic link is minted.

    Strictness (operator-approved):
      - MUST exist in `employees`.
      - MUST NOT be disabled.
      - We do NOT enforce `is_driver=true` (the flag is not universally
        present across legacy employee rows; dispatch workflow assigns
        magic links to non-CDL roles too).

    Raises `DriverIneligibleError` on any failure. Returns the employee
    document (minus _id) on success.
    """
    if not driver_id or not isinstance(driver_id, str):
        raise DriverIneligibleError("missing_driver_id", "driver_id is required")
    emp = await db.employees.find_one({"id": driver_id}, {"_id": 0})
    if not emp:
        raise DriverIneligibleError(
            "driver_not_found",
            f"no employee with id={driver_id!r}",
        )
    if emp.get("disabled") is True:
        raise DriverIneligibleError(
            "driver_disabled",
            f"employee {driver_id!r} is disabled",
        )
    if emp.get("active") is False:
        raise DriverIneligibleError(
            "driver_inactive",
            f"employee {driver_id!r} is marked inactive",
        )
    return emp


async def issue_magic_link(
    db,
    *,
    tenant_id: str,
    driver_id: str,
    driver_name: str,
    truck_id: Optional[str],
    assignment_id: Optional[str],
    issued_by_name: str,
    issued_by_role: str,
    ttl_seconds: int = MAGIC_TOKEN_TTL_SECONDS,
) -> Dict[str, Any]:
    """Mint a one-time magic token tied to a driver. Returns
    ``{token, expires_at, link_id}``. Caller is responsible for
    surfacing the URL to dispatch (the API response includes it).

    iter437 Phase Sigma-III · validates `driver_id` against the
    `employees` collection BEFORE minting. Invalid driver_ids now
    raise `DriverIneligibleError` instead of silently producing a
    usable magic token for a fictional driver.
    """
    # P0 gate — validate before any side effect.
    await _validate_driver_eligibility(db, driver_id)

    token = generate_magic_token()
    token_hash = hash_magic_token(token)
    link_id = str(uuid.uuid4())
    issued_at = now_dt()
    expires_at = issued_at + timedelta(seconds=ttl_seconds)

    doc = {
        "id": link_id,
        "tenant_id": tenant_id,
        "token_hash": token_hash,
        "driver_id": driver_id,
        "driver_name": driver_name or "",
        "truck_id": (truck_id or "").strip() or None,
        "assignment_id": (assignment_id or "").strip() or None,
        "issued_by_name": issued_by_name or "",
        "issued_by_role": issued_by_role or "",
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_at_ts": expires_at,                 # native datetime for TTL
        "used_at": None,
        "used_session_id": None,
    }
    await db.dispatch_magic_links.insert_one(doc)
    return {
        "token": token,
        "link_id": link_id,
        "expires_at": expires_at.isoformat(),
    }


async def consume_magic_link(
    db,
    *,
    raw_token: str,
    tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Look up a magic link by hash. Returns the row if found and
    NOT yet used and NOT expired. Caller is responsible for marking it
    used (we don't mutate here so the caller can transact alongside
    session creation)."""
    if not raw_token:
        return None
    token_hash = hash_magic_token(raw_token)
    query: Dict[str, Any] = {"token_hash": token_hash}
    if tenant_id:
        query["tenant_id"] = tenant_id
    row = await db.dispatch_magic_links.find_one(query, {"_id": 0})
    if not row:
        return None
    if row.get("used_at"):
        return None
    # Compare ISO strings (timezone-aware) — datetime.fromisoformat is
    # cheap and matches the rest of the platform.
    try:
        exp = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    except Exception:
        return None
    if exp <= now_dt():
        return None
    return row


async def mark_magic_link_used(
    db, *, link_id: str, session_id: str,
) -> None:
    await db.dispatch_magic_links.update_one(
        {"id": link_id},
        {"$set": {"used_at": now_iso(), "used_session_id": session_id}},
    )


# ─────────────────────────────────────────────────────────────────────
# DB ops — sessions
# ─────────────────────────────────────────────────────────────────────
async def create_driver_session(
    db,
    *,
    tenant_id: str,
    driver_id: str,
    driver_name: str,
    truck_id: Optional[str],
    assignment_id: Optional[str],
    issued_by_name: str,
    ttl_seconds: int = SESSION_TTL_SECONDS,
    origin: str = "magic_link",
    company: Optional[str] = None,
    trailer_id: Optional[str] = None,
    material: Optional[str] = None,
    employee_id: Optional[str] = None,
    truck_unit_pk: Optional[str] = None,
    trailer_unit_pk: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a fresh driver session row and return
    ``{session_id, token, expires_at}``. The session token is rebuilt
    by ``make_session_token`` so storage carries no secret.

    ``origin`` differentiates dispatcher-minted magic-link sessions
    (``"magic_link"``) from driver-self-started shift sessions
    (``"self_start"``). ``company``, ``trailer_id``, ``material`` are
    optional shift metadata captured at self-start time (iter401).

    ``employee_id`` / ``truck_unit_pk`` / ``trailer_unit_pk`` are
    optional canonical references (iter402 · Phase 12.9) that link the
    shift to the platform's employee + equipment records when the
    driver picked from the dropdown. Temp / off-roster entries omit
    them and the session is still operationally valid."""
    session_id = str(uuid.uuid4())
    issued_at = now_dt()
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    doc = {
        "id": session_id,
        "tenant_id": tenant_id,
        "driver_id": driver_id,
        "driver_name": driver_name or "",
        "truck_id": (truck_id or "").strip() or None,
        "assignment_id": (assignment_id or "").strip() or None,
        "issued_by_name": issued_by_name or "",
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_at_ts": expires_at,
        "revoked_at": None,
        "revoked_by_name": None,
        "last_seen_at": None,
        "origin": origin or "magic_link",
        "company": (company or "").strip() or None,
        "trailer_id": (trailer_id or "").strip() or None,
        "material": (material or "").strip() or None,
        "employee_id": (employee_id or "").strip() or None,
        "truck_unit_pk": (truck_unit_pk or "").strip() or None,
        "trailer_unit_pk": (trailer_unit_pk or "").strip() or None,
    }
    await db.dispatch_driver_sessions.insert_one(doc)
    token = make_session_token(session_id=session_id, driver_id=driver_id)
    return {
        "session_id": session_id,
        "token": token,
        "expires_at": expires_at.isoformat(),
    }


async def validate_driver_session_token(
    db, raw_token: Optional[str], tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Validate an ``X-Driver-Token``. Returns the session row on
    success (with the driver_id attached for routing); None otherwise.

    Order of checks:
      1. Token shape parsable.
      2. Session row exists.
      3. HMAC re-derived from session matches token signature.
      4. ``revoked_at`` is null.
      5. ``expires_at`` is in the future.
    """
    parsed = parse_session_token(raw_token or "")
    if not parsed:
        return None
    session_id, sig = parsed
    query: Dict[str, Any] = {"id": session_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    row = await db.dispatch_driver_sessions.find_one(query, {"_id": 0})
    if not row:
        return None
    if row.get("revoked_at"):
        return None
    expected = make_session_token(session_id=session_id, driver_id=row["driver_id"])
    # Constant-time compare on the signature portion.
    _, expected_sig = expected.split(".", 1)
    if not hmac.compare_digest(expected_sig, sig):
        return None
    try:
        exp = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    except Exception:
        return None
    if exp <= now_dt():
        return None
    # Touch last_seen_at best-effort (non-blocking on failure).
    try:
        await db.dispatch_driver_sessions.update_one(
            {"id": session_id},
            {"$set": {"last_seen_at": now_iso()}},
        )
    except Exception:
        pass
    return row


async def revoke_driver_session(
    db, *, session_id: str, revoked_by_name: str,
) -> bool:
    res = await db.dispatch_driver_sessions.update_one(
        {"id": session_id, "revoked_at": None},
        {"$set": {
            "revoked_at": now_iso(),
            "revoked_by_name": revoked_by_name or "",
        }},
    )
    return res.modified_count > 0


# ─────────────────────────────────────────────────────────────────────
# FastAPI dependency factory
# ─────────────────────────────────────────────────────────────────────
def make_require_driver_session(
    db,
) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """Returns a FastAPI dependency that validates ``X-Driver-Token``
    and tenant scope.

    Returns the session row (with ``_actor='driver'`` annotation) on
    success; raises 401 on missing/invalid/revoked/expired tokens.
    """
    from fastapi import Header, HTTPException

    async def _require_driver_session(
        x_driver_token: Optional[str] = Header(
            default=None, alias="X-Driver-Token",
        ),
        x_tenant_id: Optional[str] = Header(
            default=None, alias="X-Tenant-Id",
        ),
    ) -> Dict[str, Any]:
        tenant = (x_tenant_id or "").strip() or None
        session = await validate_driver_session_token(
            db, x_driver_token, tenant_id=tenant,
        )
        if session:
            return {**session, "_actor": "driver"}
        # TRACK 22.4b-followup-Driver · preview-only driver validation
        # fallback via the shared seam. Real magic-link session validation
        # runs first; this only fires when it fails, only in preview,
        # only for role="driver" PVI tokens. Never accepts admin tokens.
        try:
            from routes.role_guard_validation_seam import (  # noqa: PLC0415
                try_validation_fallback,
            )
            pvi = await try_validation_fallback(
                db, x_driver_token, expected_role="driver",
            )
        except Exception:  # noqa: BLE001
            pvi = None
        if pvi:
            _pvi_id = pvi.get("validation_identity_id") or "pvi-driver"
            return {
                "_actor": "driver",
                "id": f"pvi-session-{_pvi_id}",
                "driver_id": _pvi_id,
                "driver_name": pvi.get("name"),
                "tenant_id": tenant,
                "truck_id": None,
                "issued_at": None,
                "expires_at": None,
                "last_seen_at": None,
                "validation_identity": True,
                "validation_identity_id": _pvi_id,
                "validation_track": pvi.get("validation_track"),
                "no_real_operational_effect": True,
            }
        raise HTTPException(401, "Driver session required")

    return _require_driver_session


__all__ = [
    # constants
    "MAGIC_TOKEN_TTL_SECONDS", "SESSION_TTL_SECONDS",
    # primitives
    "generate_magic_token", "hash_magic_token",
    "make_session_token", "parse_session_token",
    # db ops
    "ensure_driver_session_indexes",
    "issue_magic_link", "consume_magic_link", "mark_magic_link_used",
    "create_driver_session", "validate_driver_session_token",
    "revoke_driver_session",
    # dep factory
    "make_require_driver_session",
]
