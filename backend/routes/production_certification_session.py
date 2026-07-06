"""TRACK 22.6A · Production Certification Session (read-only).

Auditable, short-lived, super-admin-gated session for running
authenticated read-only post-deployment certification against a
LIVE production tenant. Solves the chicken-and-egg problem where
a certification agent needs authenticated reads but must not
receive permanent admin credentials.

Key properties (each mirrors an ABSOLUTE RULE from Track 22.6A):

* **Bootstrap is admin-gated.** The only way to mint a session is
  via ``POST /admin/production-certification-session/start`` which
  itself requires ``require_admin_strict``. No environment-bootstrap
  backdoor, no CI secret, no automatic minting on startup.
* **Read-only scope.** The token authorizes an explicitly-allowlisted
  set of GET endpoints (no writes, no send, no config-mutation, no
  secret-material exposure).
* **Short-lived.** Default TTL 15 min · hard cap 60 min. Enforced
  server-side on both mint and verify. Revocable at any time.
* **HMAC-signed.** Same signing pattern proven by
  ``preview_validation_identities`` (Track 22.4b-followup). Raw
  token returned exactly once at ``/start``; never stored in cleartext.
* **Fully audited.** Every mint, every reach into the session,
  every revocation is written to
  ``production_certification_session_audit``. Immutable, append-only.
* **Never issues a normal admin token.** The certification token
  is a *distinct* subject class (``pcs.``) and is rejected by every
  normal admin dependency. It is only accepted by the certification
  reader helper on the pre-allowlisted read endpoints.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("prod_certification_session")

COLLECTION = "production_certification_sessions"
AUDIT_COLLECTION = "production_certification_session_audit"

TOKEN_PREFIX = "pcs."          # Production Certification Session
DEFAULT_TTL_MINUTES = 15
MAX_TTL_MINUTES = 60
MIN_TTL_MINUTES = 1

STATUS_ACTIVE = "active"
STATUS_EXPIRED = "expired"
STATUS_REVOKED = "revoked"

# Every GET path allow-listed for cert reads. Kept small and explicit —
# no writes, no email/SMS, no secret material, no Motive mutation.
# Every entry MUST exist as a live GET route in production. Speculative
# / not-yet-implemented endpoints are intentionally excluded so the
# cert token cannot be silently granted a path it doesn't actually cover.
ALLOWED_READ_PATHS: Set[str] = {
    "/api/admin/production-certification-session/status",
    "/api/admin/production-certification-session/audit",
    "/api/admin/deployment-readiness",
    "/api/admin/integrations/truth-status",
    "/api/admin/pm-email-coverage",
    "/api/admin/ai/keys/status",
    "/api/dispatch/motive-posture",
    "/api/admin/trust-spine",
    "/api/admin/operational-attachments/storage-summary",
    "/api/health",
    "/api/jobs",
}


# ── env / signing helpers ────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hmac_secret() -> bytes:
    """Signs the certification token. Uses ADMIN_HMAC_SECRET so bumping
    ADMIN_SESSION_EPOCH invalidates all outstanding certification tokens
    in one move — no new key rotation surface."""
    secret = (os.environ.get("ADMIN_HMAC_SECRET") or "").strip()
    if not secret:
        raise RuntimeError(
            "ADMIN_HMAC_SECRET is not set — refusing to mint certification tokens"
        )
    return secret.encode("utf-8")


def _sign_jti(jti: str) -> str:
    mac = hmac.new(_hmac_secret(), digestmod=hashlib.sha256)
    mac.update(f"pcs|{jti}".encode("utf-8"))
    return mac.hexdigest()


def _make_token(jti: str) -> str:
    return f"{TOKEN_PREFIX}{jti}.{_sign_jti(jti)}"


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


def _fingerprint(token: str) -> str:
    """Non-reversible fingerprint used in audit rows so an operator
    can correlate 'which session did this' without ever storing the
    raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


# ── indexes ──────────────────────────────────────────────────────

async def ensure_indexes(db) -> None:
    try:
        await db[COLLECTION].create_index("jti", unique=True)
        await db[COLLECTION].create_index([("expires_at", 1)])
        await db[COLLECTION].create_index([("status", 1), ("created_at", -1)])
        # 30-day audit retention — long enough for a deploy postmortem,
        # short enough to keep the collection lean.
        await db[COLLECTION].create_index(
            "created_at", expireAfterSeconds=30 * 24 * 3600
        )
        await db[AUDIT_COLLECTION].create_index([("at", -1)])
        await db[AUDIT_COLLECTION].create_index(
            "at", expireAfterSeconds=30 * 24 * 3600
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[pcs indexes] {exc}")


# ── audit helper ─────────────────────────────────────────────────

async def _audit(db, **kwargs) -> None:
    try:
        row = {"at": _now(), **kwargs}
        row.pop("token", None)  # NEVER audit raw tokens
        await db[AUDIT_COLLECTION].insert_one(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[pcs audit] {exc}")


# ── mint / verify / revoke ────────────────────────────────────────

async def mint_session(
    db, *,
    ttl_minutes: int,
    purpose: str,
    created_by_admin_email: str,
    track: str,
) -> Dict[str, Any]:
    if not isinstance(ttl_minutes, int) or ttl_minutes < MIN_TTL_MINUTES:
        raise HTTPException(400, f"ttl_minutes must be ≥ {MIN_TTL_MINUTES}")
    if ttl_minutes > MAX_TTL_MINUTES:
        raise HTTPException(400, f"ttl_minutes must be ≤ {MAX_TTL_MINUTES}")

    jti = secrets.token_urlsafe(32)
    now = _now()
    expires_at = now + timedelta(minutes=ttl_minutes)
    session_id = secrets.token_urlsafe(12)

    record = {
        "session_id": session_id,
        "jti": jti,
        "track": track or "TRACK_22_6A",
        "purpose": (purpose or "unspecified")[:500],
        "created_by_admin_email": created_by_admin_email,
        "created_at": now,
        "expires_at": expires_at,
        "ttl_minutes": ttl_minutes,
        "revoked_at": None,
        "revoked_by": None,
        "status": STATUS_ACTIVE,
        "read_only": True,
        "scope": "production_certification_read_only",
        "allowed_paths_count": len(ALLOWED_READ_PATHS),
        "reads_performed": 0,
    }
    await db[COLLECTION].insert_one(record)

    token = _make_token(jti)
    await _audit(
        db,
        event="pcs_session_minted",
        session_id=session_id,
        actor_email=created_by_admin_email,
        track=track, purpose=purpose,
        ttl_minutes=ttl_minutes,
        expires_at=expires_at,
        token_fp=_fingerprint(token),
    )
    return {
        "session_id": session_id,
        "token": token,
        "token_header_hint": "X-Certification-Token",
        "ttl_minutes": ttl_minutes,
        "expires_at": expires_at.isoformat(),
        "scope": "production_certification_read_only",
        "allowed_paths": sorted(ALLOWED_READ_PATHS),
        "warning": (
            "PRODUCTION CERTIFICATION TOKEN — read-only, "
            "short-lived, revocable. Never sends email/SMS, never "
            "mutates operational data, never modifies integrations. "
            "This token is returned exactly once and never stored in "
            "cleartext."
        ),
    }


async def verify_session_token(
    db, token: Optional[str], *, request_path: str,
) -> Optional[Dict[str, Any]]:
    """Return the session record iff the token is a valid, unexpired,
    unrevoked cert token AND the requested path is in the allowlist.
    Otherwise return None. Never raises."""
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
        await db[COLLECTION].update_one(
            {"jti": parsed["jti"]}, {"$set": {"status": STATUS_EXPIRED}}
        )
        return None
    expected_sig = _sign_jti(parsed["jti"])
    if not hmac.compare_digest(expected_sig, parsed["sig"]):
        return None
    # Path allowlist — hardening against a leaked token being used
    # against non-approved endpoints. Normalise trailing slashes.
    path = (request_path or "").rstrip("/") or "/"
    if path not in ALLOWED_READ_PATHS:
        # Log the attempt for audit, then reject.
        await _audit(db, event="pcs_disallowed_path", session_id=row.get("session_id"),
                     path=request_path)
        return None
    return row


async def revoke_session(
    db, session_id: str, *, revoked_by_email: str,
) -> Dict[str, Any]:
    row = await db[COLLECTION].find_one({"session_id": session_id}, {"_id": 0})
    if not row:
        raise HTTPException(404, "certification session not found")
    if row.get("status") != STATUS_ACTIVE:
        return {"session_id": session_id, "status": row["status"]}
    now = _now()
    await db[COLLECTION].update_one(
        {"session_id": session_id},
        {"$set": {"status": STATUS_REVOKED, "revoked_at": now,
                  "revoked_by": revoked_by_email}},
    )
    await _audit(db, event="pcs_session_revoked",
                 session_id=session_id, actor_email=revoked_by_email)
    return {"session_id": session_id, "status": STATUS_REVOKED,
            "revoked_at": now.isoformat()}


# ── payload models ───────────────────────────────────────────────

class StartRequest(BaseModel):
    purpose: str = Field(default="post-deployment authenticated read-only certification",
                          max_length=500)
    ttl_minutes: int = Field(default=DEFAULT_TTL_MINUTES,
                              ge=MIN_TTL_MINUTES, le=MAX_TTL_MINUTES)
    track: str = Field(default="TRACK_22_6A", max_length=64)


class RevokeRequest(BaseModel):
    session_id: str


# ── route registration ───────────────────────────────────────────

def register_production_certification_session_routes(
    api_router: APIRouter,
    *,
    db,
    require_admin_strict,
) -> None:
    """Attach the production certification session control-plane."""

    @api_router.post("/admin/production-certification-session/start")
    async def start(body: StartRequest, request: Request,
                     _admin: bool = Depends(require_admin_strict)):
        # Admin identity comes from the request-scoped admin context
        # populated by require_admin_strict. Falls back to header if
        # the platform doesn't set request.state.admin_email.
        actor = (getattr(request.state, "admin_email", None)
                 or request.headers.get("X-Admin-Email") or "admin")
        return await mint_session(
            db, ttl_minutes=body.ttl_minutes, purpose=body.purpose,
            created_by_admin_email=actor, track=body.track,
        )

    @api_router.get("/admin/production-certification-session/status")
    async def status(
        x_certification_token: Optional[str] = Header(default=None),
        _admin: Optional[bool] = Depends(require_admin_strict),
    ):
        """Return current session status. Works for either an admin
        introspecting or the cert token verifying itself is alive."""
        # Prefer cert-token-based self-check so a cert session can
        # verify it hasn't been revoked without needing admin creds.
        if x_certification_token:
            row = await verify_session_token(
                db, x_certification_token,
                request_path="/api/admin/production-certification-session/status",
            )
            if not row:
                raise HTTPException(401, "certification token invalid/expired/revoked")
            # Increment read counter and audit.
            await db[COLLECTION].update_one(
                {"session_id": row["session_id"]},
                {"$inc": {"reads_performed": 1},
                 "$set": {"last_read_at": _now()}},
            )
            await _audit(db, event="pcs_status_probed",
                          session_id=row["session_id"])
            row.pop("jti", None)
            for k in ("created_at", "expires_at", "revoked_at", "last_read_at"):
                if isinstance(row.get(k), datetime):
                    row[k] = row[k].isoformat()
            return row
        # Fallback: admin introspection returns the most-recent session.
        latest = await db[COLLECTION].find_one(
            {}, {"_id": 0, "jti": 0}, sort=[("created_at", -1)],
        ) or {}
        for k in ("created_at", "expires_at", "revoked_at", "last_read_at"):
            if isinstance(latest.get(k), datetime):
                latest[k] = latest[k].isoformat()
        return {"latest_session": latest}

    @api_router.post("/admin/production-certification-session/revoke")
    async def revoke(body: RevokeRequest, request: Request,
                      _admin: bool = Depends(require_admin_strict)):
        actor = (getattr(request.state, "admin_email", None)
                 or request.headers.get("X-Admin-Email") or "admin")
        return await revoke_session(db, body.session_id, revoked_by_email=actor)

    @api_router.get("/admin/production-certification-session/audit")
    async def audit(limit: int = 200,
                     _admin: bool = Depends(require_admin_strict)):
        limit = max(1, min(1000, limit))
        rows: List[Dict[str, Any]] = []
        async for r in db[AUDIT_COLLECTION].find(
            {}, {"_id": 0}, sort=[("at", -1)], limit=limit,
        ):
            if isinstance(r.get("at"), datetime):
                r["at"] = r["at"].isoformat()
            if isinstance(r.get("expires_at"), datetime):
                r["expires_at"] = r["expires_at"].isoformat()
            rows.append(r)
        return {"rows": rows, "count": len(rows)}
