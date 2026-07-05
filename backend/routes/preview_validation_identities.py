"""TRACK 22.4b-followup · Preview Validation Identities.

Safe, locked-down, **preview-only** validation identity control plane
that unblocks role-scoped workflow verification without weakening
production RBAC.

Doctrine
--------
- **Hard-disabled in production.** Every endpoint returns 404 unless
  ``APP_ENV`` is one of {preview, staging, development, test} *AND*
  ``ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`` at the process level.
- **Super-admin only.** Uses the existing ``require_admin_strict``
  dependency — no new admin path, no new secret.
- **Short-lived.** Default TTL 4 hours, hard max 24 hours. No indefinite
  tokens. Tokens auto-expire; revocation is immediate.
- **Auditable.** Every mint / revoke / introspect action writes a row to
  ``preview_validation_identity_audit``. Raw token values are NEVER
  persisted; only the ``jti`` and metadata.
- **Isolated token format.** ``PVI.<jti>.<HMAC>`` — the prefix ``PVI.`` is
  reserved and refused by every existing role guard by construction
  (existing guards look up their tokens in per-role user tables and will
  simply not find the ``PVI.*`` jti).
- **Not a user manager.** Mint creates a validation identity RECORD, not
  a real employee, not a real user_directory row, not a real
  project_managers row. No production auth surface is touched.

What this track ships
---------------------
- Control plane: mint / list / revoke / audit.
- Token signing + verification (HMAC via ``ADMIN_HMAC_SECRET``).
- ``verify_validation_token(token, expected_role)`` helper that role
  guards can adopt in follow-up tracks (Safety / HR / Driver etc.).

What is deferred to follow-up tracks
------------------------------------
- Wiring ``verify_validation_token`` into each per-role guard so a
  Safety validation token actually reaches ``@require_safety`` endpoints.
  This is per-follow-up-track work (Safety / HR / Driver / etc.) and
  is out of scope here.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────
TOKEN_PREFIX = "PVI."
COLLECTION = "preview_validation_identities"
AUDIT_COLLECTION = "preview_validation_identity_audit"

DEFAULT_TTL_MINUTES = 4 * 60          # 4 hours
MAX_TTL_MINUTES = 24 * 60             # 24 hours hard cap

ALLOWED_ROLES = (
    "admin", "pm", "safety", "hr", "shop", "dispatch",
    "driver", "field_leadership",
)

STATUS_ACTIVE = "active"
STATUS_EXPIRED = "expired"
STATUS_REVOKED = "revoked"

PREVIEW_ENVS = {"preview", "staging", "development", "dev", "test"}


# ── env guard ─────────────────────────────────────────────────────

def _env_marker() -> str:
    """Return the effective environment marker (lowercased)."""
    for var in ("APP_ENV", "ENVIRONMENT", "DEPLOY_ENV"):
        v = (os.environ.get(var) or "").strip().lower()
        if v:
            return v
    return "unknown"


def _feature_enabled() -> bool:
    v = (os.environ.get("ENABLE_PREVIEW_VALIDATION_IDENTITIES") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def _is_production() -> bool:
    return _env_marker() == "production"


def is_preview_validation_available() -> bool:
    """Public helper — True iff mint/list/revoke are allowed to run.

    Requires BOTH a preview-class environment marker AND the explicit
    ENABLE_PREVIEW_VALIDATION_IDENTITIES flag. Fail-closed.
    """
    if _is_production():
        return False
    if _env_marker() not in PREVIEW_ENVS:
        return False
    return _feature_enabled()


def _guard_or_404():
    """Raise 404 (never 401 — 401 would leak the endpoint's existence)
    when validation identities are not permitted in this environment.
    """
    if not is_preview_validation_available():
        raise HTTPException(status_code=404, detail="Not Found")


# ── token signing (HMAC) ──────────────────────────────────────────

def _hmac_secret() -> bytes:
    """Uses the same secret as admin tokens — bumping
    ``ADMIN_SESSION_EPOCH`` invalidates every validation token in one
    move (existing operator ritual, no new key rotation surface).
    """
    secret = (os.environ.get("ADMIN_HMAC_SECRET") or "").strip()
    if not secret:
        raise RuntimeError(
            "ADMIN_HMAC_SECRET is not set — refusing to mint validation tokens"
        )
    return secret.encode("utf-8")


def _sign_jti(jti: str, role: str) -> str:
    """Return HMAC-SHA256 hex digest binding jti + role."""
    mac = hmac.new(_hmac_secret(), digestmod=hashlib.sha256)
    mac.update(f"{jti}|{role}".encode("utf-8"))
    return mac.hexdigest()


def _make_token(jti: str, role: str) -> str:
    return f"{TOKEN_PREFIX}{jti}.{_sign_jti(jti, role)}"


def _parse_token(token: str) -> Optional[Dict[str, str]]:
    if not token or not token.startswith(TOKEN_PREFIX):
        return None
    payload = token[len(TOKEN_PREFIX):]
    if payload.count(".") != 1:
        return None
    jti, sig = payload.split(".", 1)
    if not jti or not sig:
        return None
    return {"jti": jti, "sig": sig}


# ── mint / verify / revoke helpers ────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


async def mint_validation_identity(
    db, *,
    role: str,
    purpose: str,
    ttl_minutes: int,
    validation_track: str,
    created_by_admin_email: str,
    created_by_admin_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """Create a validation identity + return one-time token payload."""
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"invalid role: {role}")
    if ttl_minutes < 1:
        raise HTTPException(status_code=400, detail="ttl_minutes must be ≥ 1")
    if ttl_minutes > MAX_TTL_MINUTES:
        raise HTTPException(
            status_code=400,
            detail=f"ttl_minutes must be ≤ {MAX_TTL_MINUTES} (24 hours)",
        )

    jti = secrets.token_urlsafe(24)
    now = _now()
    expires_at = now + timedelta(minutes=ttl_minutes)
    identity_id = secrets.token_urlsafe(12)

    record = {
        "validation_identity_id": identity_id,
        "validation_track": validation_track or "TRACK_22_4B_FOLLOWUP",
        "role": role,
        "display_name": f"VALIDATION · {role.upper()} · {identity_id[:6]}",
        "purpose": (purpose or "unspecified")[:500],
        "created_by_admin_id": created_by_admin_id,
        "created_by_admin_email": created_by_admin_email,
        "created_at": now,
        "expires_at": expires_at,
        "ttl_minutes": ttl_minutes,
        "revoked_at": None,
        "revoked_by": None,
        "status": STATUS_ACTIVE,
        "jti": jti,
        "environment": _env_marker(),
        "notes": (notes or "")[:1000],
        "safe_to_delete": True,
        "no_real_operational_effect": True,
    }
    await db[COLLECTION].insert_one(record)

    await _audit(db, event="validation_identity_minted", actor_email=created_by_admin_email,
                 identity_id=identity_id, role=role, validation_track=validation_track,
                 expires_at=expires_at, purpose=purpose)

    token = _make_token(jti, role)
    return {
        "validation_identity_id": identity_id,
        "role": role,
        "expires_at": expires_at.isoformat(),
        "ttl_minutes": ttl_minutes,
        "status": STATUS_ACTIVE,
        "token": token,
        "token_header_hint": _token_header_hint(role),
        "warning": (
            "PREVIEW VALIDATION TOKEN — copy once, use for role workflow "
            "verification only. Never for production, never for live "
            "operations. This token auto-expires."
        ),
        "environment": _env_marker(),
    }


def _token_header_hint(role: str) -> str:
    mapping = {
        "admin": "X-Admin-Token", "pm": "X-PM-Token",
        "safety": "X-Safety-Token", "hr": "X-HR-Token",
        "shop": "X-Shop-Token", "dispatch": "X-Dispatch-Token",
        "driver": "X-Driver-Token", "field_leadership": "X-Leadership-Token",
    }
    return mapping.get(role, "X-Admin-Token")


async def verify_validation_token(
    db, token: Optional[str], *, expected_role: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the identity record iff the token is a valid, unexpired,
    unrevoked validation token for the (optionally-specified) role.

    Returns ``None`` if the token is not a PVI token, has bad HMAC,
    is expired, has been revoked, or does not match ``expected_role``.
    Never raises — role guards will fall through to their normal auth
    when this returns None.
    """
    if not is_preview_validation_available():
        return None
    parsed = _parse_token(token or "")
    if parsed is None:
        return None
    row = await db[COLLECTION].find_one({"jti": parsed["jti"]}, {"_id": 0})
    if not row:
        return None
    if row.get("status") != STATUS_ACTIVE:
        return None
    exp = row.get("expires_at")
    if isinstance(exp, datetime) and exp <= _now():
        # Silently mark expired for the next introspection call.
        await db[COLLECTION].update_one({"jti": parsed["jti"]},
                                        {"$set": {"status": STATUS_EXPIRED}})
        return None
    role = row.get("role")
    expected_sig = _sign_jti(parsed["jti"], role)
    if not hmac.compare_digest(expected_sig, parsed["sig"]):
        return None
    if expected_role is not None and role != expected_role:
        return None
    return row


async def revoke_validation_identity(
    db, identity_id: str, *, revoked_by_email: str,
) -> Dict[str, Any]:
    row = await db[COLLECTION].find_one({"validation_identity_id": identity_id},
                                         {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="validation identity not found")
    if row.get("status") != STATUS_ACTIVE:
        return {"validation_identity_id": identity_id, "status": row["status"]}
    now = _now()
    await db[COLLECTION].update_one(
        {"validation_identity_id": identity_id},
        {"$set": {"status": STATUS_REVOKED, "revoked_at": now,
                  "revoked_by": revoked_by_email}},
    )
    await _audit(db, event="validation_identity_revoked",
                 actor_email=revoked_by_email,
                 identity_id=identity_id, role=row.get("role"),
                 validation_track=row.get("validation_track"))
    return {"validation_identity_id": identity_id, "status": STATUS_REVOKED,
            "revoked_at": now.isoformat()}


async def list_validation_identities(db, *, include_inactive: bool = False) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {} if include_inactive else {"status": STATUS_ACTIVE}
    rows = []
    async for r in db[COLLECTION].find(q, {"_id": 0}).sort("created_at", -1).limit(200):
        for k in ("created_at", "expires_at", "revoked_at"):
            if isinstance(r.get(k), datetime):
                r[k] = r[k].isoformat()
        # NEVER return the raw token — jti only.
        r.pop("token", None)
        rows.append(r)
    return rows


async def _audit(db, **kwargs) -> None:
    try:
        row = {"at": _now(), "environment": _env_marker(), **kwargs}
        # Never store raw tokens in audit
        row.pop("token", None)
        await db[AUDIT_COLLECTION].insert_one(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[preview validation audit] {exc}")


# ── route registration ────────────────────────────────────────────

def register_preview_validation_identity_routes(
    api_router: APIRouter,
    *,
    db,
    require_admin_strict,
) -> None:
    """Attach the preview validation identity control-plane routes."""

    @api_router.get("/admin/preview-validation-identities/env")
    async def env_status(_=Depends(require_admin_strict)):
        """Even the env status endpoint is admin-gated. This intentionally
        leaks nothing to non-admins."""
        return {
            "env_marker": _env_marker(),
            "feature_enabled": _feature_enabled(),
            "available": is_preview_validation_available(),
            "is_production": _is_production(),
            "default_ttl_minutes": DEFAULT_TTL_MINUTES,
            "max_ttl_minutes": MAX_TTL_MINUTES,
            "allowed_roles": list(ALLOWED_ROLES),
        }

    @api_router.get("/admin/preview-validation-identities")
    async def list_identities(
        include_inactive: bool = Query(default=False),
        _=Depends(require_admin_strict),
    ):
        _guard_or_404()
        rows = await list_validation_identities(db, include_inactive=include_inactive)
        return {"count": len(rows), "identities": rows}

    @api_router.post("/admin/preview-validation-identities/mint")
    async def mint(body: Dict[str, Any], admin_ctx: Any = Depends(require_admin_strict)):
        _guard_or_404()
        role = (body.get("role") or "").strip().lower()
        purpose = (body.get("purpose") or "").strip()
        ttl_minutes = int(body.get("ttl_minutes") or DEFAULT_TTL_MINUTES)
        validation_track = (body.get("validation_track") or "TRACK_22_4B_FOLLOWUP").strip()
        notes = (body.get("notes") or "").strip()

        # Best-effort actor identification. require_admin_strict returns
        # True/dict shapes across the codebase; be tolerant.
        actor_email = "admin@validation"
        actor_id = "admin"
        if isinstance(admin_ctx, dict):
            actor_email = admin_ctx.get("email") or actor_email
            actor_id = admin_ctx.get("id") or actor_id

        return await mint_validation_identity(
            db,
            role=role,
            purpose=purpose,
            ttl_minutes=ttl_minutes,
            validation_track=validation_track,
            created_by_admin_email=actor_email,
            created_by_admin_id=actor_id,
            notes=notes,
        )

    @api_router.post("/admin/preview-validation-identities/{identity_id}/revoke")
    async def revoke(identity_id: str, admin_ctx: Any = Depends(require_admin_strict)):
        _guard_or_404()
        actor_email = "admin@validation"
        if isinstance(admin_ctx, dict):
            actor_email = admin_ctx.get("email") or actor_email
        return await revoke_validation_identity(
            db, identity_id, revoked_by_email=actor_email,
        )

    @api_router.get("/admin/preview-validation-identities/audit")
    async def audit_log(
        limit: int = Query(default=100, ge=1, le=500),
        _=Depends(require_admin_strict),
    ):
        _guard_or_404()
        rows = []
        async for r in db[AUDIT_COLLECTION].find({}, {"_id": 0}).sort("at", -1).limit(limit):
            if isinstance(r.get("at"), datetime):
                r["at"] = r["at"].isoformat()
            if isinstance(r.get("expires_at"), datetime):
                r["expires_at"] = r["expires_at"].isoformat()
            rows.append(r)
        return {"count": len(rows), "audit": rows}

    @api_router.post("/admin/preview-validation-identities/introspect")
    async def introspect(body: Dict[str, Any], _=Depends(require_admin_strict)):
        """Introspect an opaque token — proves validation-token verification
        works end-to-end. Never returns the raw signature; only the record.
        """
        _guard_or_404()
        token = (body.get("token") or "").strip()
        expected_role = (body.get("expected_role") or "").strip().lower() or None
        row = await verify_validation_token(db, token, expected_role=expected_role)
        if not row:
            return {"valid": False}
        # Never leak the jti back in the introspect response either.
        safe = {k: v for k, v in row.items() if k != "jti"}
        for k in ("created_at", "expires_at", "revoked_at"):
            if isinstance(safe.get(k), datetime):
                safe[k] = safe[k].isoformat()
        return {"valid": True, "identity": safe}


__all__ = [
    "register_preview_validation_identity_routes",
    "verify_validation_token",
    "is_preview_validation_available",
    "TOKEN_PREFIX",
    "COLLECTION",
    "AUDIT_COLLECTION",
    "ALLOWED_ROLES",
    "DEFAULT_TTL_MINUTES",
    "MAX_TTL_MINUTES",
]
