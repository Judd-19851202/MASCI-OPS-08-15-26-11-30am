"""routes/passkeys.py · iter422 · Phase 24 · Passkey / WebAuthn Continuity.

Walking-skeleton scope (Admin master sign-in pilot ONLY):
  - POST /api/passkeys/register/options  (authed via X-Directory-Token)
  - POST /api/passkeys/register/verify   (authed via X-Directory-Token)
  - POST /api/passkeys/login/options     (public · email-first)
  - POST /api/passkeys/login/verify      (public · mints SAME multi-login response)
  - GET  /api/passkeys/list               (authed · device-management read-only)
  - DELETE /api/passkeys/{credential_id}  (authed · revoke a device)

DOCTRINE GUARDS:
  - NEVER stores biometric data. Only WebAuthn public-key metadata.
  - Reuses py_webauthn (Duo Security · standards-based).
  - Multi-login response shape preserved EXACTLY (mint_multi_login_response).
  - Password fallback unchanged · NO portal/admin token format change.
  - NO selfie · NO camera · NO custom recognition · NO surveillance.
  - Mongo `_id` excluded from every response.
  - Append-only credential records · revoke = `disabled=true` (no destructive ops).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    base64url_to_bytes,
    bytes_to_base64url,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

logger = logging.getLogger("passkeys")

RP_NAME = "MASCI Operations"
PREVIEW_SUFFIX = ".preview.emergentagent.com"
CHALLENGE_TTL_SECONDS = 300  # 5 min
MAX_PASSKEYS_PER_USER = 10   # anti-abuse · per-account ceiling


# ════════════════════════════════════════════════════════════════════
# RP ID derivation · stable across preview subdomains + custom prod domain
# ════════════════════════════════════════════════════════════════════
def _host_from_origin(value: Optional[str]) -> Optional[str]:
    """Extract host from an Origin/Referer header value (`https://host[:port]/...`)."""
    if not value:
        return None
    v = value.strip()
    if "://" in v:
        v = v.split("://", 1)[1]
    v = v.split("/", 1)[0]
    v = v.split(":", 1)[0]
    return v.lower() or None


def _client_visible_host(request: Request) -> str:
    """Resolve the host the user's browser actually used.

    Order (Cloudflare-aware — CF rewrites Origin/Referer to the internal
    cluster hostname but always preserves X-Forwarded-Host):
      1. X-Forwarded-Host (most trusted on this platform)
      2. Origin header (browsers set this on cross-origin POSTs)
      3. Referer header
      4. Host header
      5. URL hostname (last resort · internal cluster name)
    """
    candidates = [
        (request.headers.get("x-forwarded-host") or "").split(",")[0].strip().lower() or None,
        _host_from_origin(request.headers.get("origin")),
        _host_from_origin(request.headers.get("referer")),
        (request.headers.get("host") or "").split(":")[0].strip().lower() or None,
        (request.url.hostname or "").split(":")[0].lower() or None,
    ]
    for h in candidates:
        if h:
            return h
    return os.environ.get("PASSKEY_RP_ID", "localhost")


def derive_rp_id(request: Request) -> str:
    """RP ID rule:
       *.preview.emergentagent.com → preview.emergentagent.com (parent · shared)
       anything else                → the host itself (one-domain prod path)
    """
    host = _client_visible_host(request)
    if host.endswith(PREVIEW_SUFFIX):
        return PREVIEW_SUFFIX.lstrip(".")
    return host


def derive_expected_origins(request: Request) -> List[str]:
    """Build the list of acceptable origins to test against the assertion."""
    host = _client_visible_host(request)
    # Trust X-Forwarded-Proto first (set by ingress on this platform)
    fwd_proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
    if fwd_proto in ("http", "https"):
        scheme = fwd_proto
    else:
        origin = request.headers.get("origin") or ""
        scheme = origin.split("://", 1)[0] if "://" in origin else "https"
    return [f"{scheme}://{host}"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ════════════════════════════════════════════════════════════════════
# Pydantic bodies
# ════════════════════════════════════════════════════════════════════
class LoginOptionsBody(BaseModel):
    email: str


class GenericPayload(BaseModel):
    # WebAuthn ceremony payloads use deep nested JSON · accept dict.
    class Config:
        extra = "allow"


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_passkeys_router(
    db,
    *,
    require_directory_session_dep: Callable[..., Awaitable[Dict[str, Any]]],
    mint_multi_login_response: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Build the passkeys router.

    Args:
      db: Motor/PyMongo async database handle.
      require_directory_session_dep: FastAPI dep that validates
        ``X-Directory-Token`` and returns the directory user row.
      mint_multi_login_response: async callable that, given a directory
        user row + a Request, returns the SAME response shape as
        ``POST /api/auth/multi-login``. This preserves the password
        contract exactly · passkey path is a drop-in substitute.
    """
    router = APIRouter(prefix="/api/passkeys", tags=["passkeys"])

    # ───────────── helpers ─────────────────────────────────────────
    async def _save_challenge(*, kind: str, challenge_b64u: str,
                              rp_id: str, directory_user_id: Optional[str],
                              email: Optional[str]) -> None:
        await db.webauthn_challenges.insert_one({
            "type": kind,
            "challenge": challenge_b64u,
            "rp_id": rp_id,
            "directory_user_id": directory_user_id,
            "email": (email or "").lower() or None,
            "created_at": _now(),
            "used": False,
        })

    async def _consume_challenge(*, kind: str, rp_id: str,
                                 directory_user_id: Optional[str],
                                 email: Optional[str]) -> Optional[Dict[str, Any]]:
        q: Dict[str, Any] = {
            "type": kind, "rp_id": rp_id, "used": False,
        }
        if directory_user_id:
            q["directory_user_id"] = directory_user_id
        elif email:
            q["email"] = email.lower()
        doc = await db.webauthn_challenges.find_one(q, sort=[("created_at", -1)])
        if not doc:
            return None
        # Anti-replay: mark used immediately
        await db.webauthn_challenges.update_one(
            {"_id": doc["_id"]}, {"$set": {"used": True}},
        )
        # TTL check (in case TTL index deletion is lagging).
        # Motor returns datetimes from Mongo as timezone-NAIVE (treated as UTC),
        # so coerce before subtraction to avoid:
        #   "can't subtract offset-naive and offset-aware datetimes"
        created_at = doc.get("created_at")
        if isinstance(created_at, datetime):
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age = (_now() - created_at).total_seconds()
            if age > CHALLENGE_TTL_SECONDS:
                return None
        return doc

    def _public_passkey(doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "credential_id": doc.get("credential_id"),
            "friendly_name": doc.get("friendly_name") or "Device passkey",
            "created_at": (doc.get("created_at").isoformat()
                           if isinstance(doc.get("created_at"), datetime)
                           else doc.get("created_at")),
            "last_used_at": (doc.get("last_used_at").isoformat()
                             if isinstance(doc.get("last_used_at"), datetime)
                             else doc.get("last_used_at")),
            "disabled": bool(doc.get("disabled")),
        }

    # ════════════════════════════════════════════════════════════════
    # REGISTRATION · OPTIONS
    # ════════════════════════════════════════════════════════════════
    @router.post("/register/options")
    async def register_options(
        request: Request,
        actor: Dict[str, Any] = Depends(require_directory_session_dep),
    ):
        rp_id = derive_rp_id(request)
        user_id = str(actor.get("id") or "")
        if not user_id:
            raise HTTPException(401, "Directory session required")

        # Existing credentials to EXCLUDE (avoid re-enrolling same device)
        existing = []
        async for c in db.user_passkeys.find(
            {"directory_user_id": user_id, "disabled": {"$ne": True}},
            {"_id": 0, "credential_id": 1},
        ):
            try:
                existing.append(PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(c["credential_id"])
                ))
            except Exception:  # noqa: BLE001
                continue

        # Per-account ceiling
        if len(existing) >= MAX_PASSKEYS_PER_USER:
            raise HTTPException(400, f"Maximum {MAX_PASSKEYS_PER_USER} device passkeys per user")

        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=RP_NAME,
            user_name=actor.get("email") or user_id,
            user_id=user_id.encode("utf-8"),
            user_display_name=(actor.get("name") or actor.get("email") or user_id),
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            exclude_credentials=existing or None,
        )
        # options_to_json returns a JSON STRING in py_webauthn 2.x — parse back
        import json as _json
        options_json = _json.loads(options_to_json(options))

        await _save_challenge(
            kind="registration",
            challenge_b64u=options_json["challenge"],
            rp_id=rp_id,
            directory_user_id=user_id,
            email=actor.get("email"),
        )
        return {"publicKey": options_json}

    # ════════════════════════════════════════════════════════════════
    # REGISTRATION · VERIFY
    # ════════════════════════════════════════════════════════════════
    @router.post("/register/verify")
    async def register_verify(
        request: Request,
        payload: Dict[str, Any] = Body(...),
        actor: Dict[str, Any] = Depends(require_directory_session_dep),
    ):
        rp_id = derive_rp_id(request)
        origins = derive_expected_origins(request)
        user_id = str(actor.get("id") or "")
        if not user_id:
            raise HTTPException(401, "Directory session required")

        challenge_doc = await _consume_challenge(
            kind="registration", rp_id=rp_id,
            directory_user_id=user_id, email=actor.get("email"),
        )
        if not challenge_doc:
            raise HTTPException(400, "Registration challenge not found or expired")
        expected_challenge = base64url_to_bytes(challenge_doc["challenge"])

        # Parse client payload
        try:
            credential = parse_registration_credential_json(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[passkeys] register parse failed: {exc}")
            raise HTTPException(400, "Invalid registration credential payload")

        # Try each accepted origin (request scheme://host)
        verification = None
        last_err: Optional[Exception] = None
        for origin in origins:
            try:
                verification = verify_registration_response(
                    credential=credential,
                    expected_challenge=expected_challenge,
                    expected_rp_id=rp_id,
                    expected_origin=origin,
                    require_user_verification=True,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
        if not verification:
            logger.warning(f"[passkeys] register verify failed: {last_err}")
            raise HTTPException(400, "WebAuthn registration verification failed")

        cred_id_b64u = bytes_to_base64url(verification.credential_id)
        pubkey_b64u = bytes_to_base64url(verification.credential_public_key)

        await db.user_passkeys.update_one(
            {"directory_user_id": user_id, "credential_id": cred_id_b64u, "rp_id": rp_id},
            {"$set": {
                "directory_user_id": user_id,
                "credential_id": cred_id_b64u,
                "public_key": pubkey_b64u,
                "sign_count": verification.sign_count or 0,
                "rp_id": rp_id,
                "friendly_name": (payload.get("friendly_name") or "Device passkey")[:120],
                "created_at": _now(),
                "last_used_at": None,
                "disabled": False,
            }},
            upsert=True,
        )
        return {"ok": True, "credential_id": cred_id_b64u}

    # ════════════════════════════════════════════════════════════════
    # LOGIN · OPTIONS (public · email-first)
    # ════════════════════════════════════════════════════════════════
    @router.post("/login/options")
    async def login_options(request: Request, body: LoginOptionsBody):
        rp_id = derive_rp_id(request)
        email = (body.email or "").strip().lower()
        if not email:
            raise HTTPException(400, "Email is required")

        # Lookup directory user by email
        user = await db.user_directory.find_one(
            {"email": email}, {"_id": 0, "id": 1, "email": 1},
        )
        # We DO return options either way — this avoids email-enumeration
        # leakage. If no user · empty allowCredentials · UV stays required.
        directory_user_id = user.get("id") if user else None

        allow_creds: List[PublicKeyCredentialDescriptor] = []
        if directory_user_id:
            async for c in db.user_passkeys.find(
                {
                    "directory_user_id": directory_user_id,
                    "rp_id": rp_id,
                    "disabled": {"$ne": True},
                },
                {"_id": 0, "credential_id": 1},
            ):
                try:
                    allow_creds.append(PublicKeyCredentialDescriptor(
                        id=base64url_to_bytes(c["credential_id"])
                    ))
                except Exception:  # noqa: BLE001
                    continue

        options = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=allow_creds or None,
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        import json as _json
        options_json = _json.loads(options_to_json(options))

        await _save_challenge(
            kind="authentication",
            challenge_b64u=options_json["challenge"],
            rp_id=rp_id,
            directory_user_id=directory_user_id,
            email=email,
        )
        return {"publicKey": options_json}

    # ════════════════════════════════════════════════════════════════
    # LOGIN · VERIFY (public · mints same multi-login response)
    # ════════════════════════════════════════════════════════════════
    @router.post("/login/verify")
    async def login_verify(
        request: Request,
        payload: Dict[str, Any] = Body(...),
    ):
        rp_id = derive_rp_id(request)
        origins = derive_expected_origins(request)

        try:
            credential = parse_authentication_credential_json(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[passkeys] login parse failed: {exc}")
            raise HTTPException(400, "Invalid authentication credential payload")

        cred_id_b64u = bytes_to_base64url(credential.raw_id)
        cred_doc = await db.user_passkeys.find_one(
            {"credential_id": cred_id_b64u, "rp_id": rp_id, "disabled": {"$ne": True}},
            {"_id": 0},
        )
        if not cred_doc:
            raise HTTPException(400, "Unknown device passkey")

        directory_user_id = cred_doc["directory_user_id"]

        challenge_doc = await _consume_challenge(
            kind="authentication", rp_id=rp_id,
            directory_user_id=directory_user_id, email=None,
        )
        if not challenge_doc:
            raise HTTPException(400, "Authentication challenge not found or expired")
        expected_challenge = base64url_to_bytes(challenge_doc["challenge"])

        public_key_bytes = base64url_to_bytes(cred_doc["public_key"])
        current_sign_count = int(cred_doc.get("sign_count") or 0)

        verification = None
        last_err: Optional[Exception] = None
        for origin in origins:
            try:
                verification = verify_authentication_response(
                    credential=credential,
                    expected_challenge=expected_challenge,
                    expected_rp_id=rp_id,
                    expected_origin=origin,
                    credential_public_key=public_key_bytes,
                    credential_current_sign_count=current_sign_count,
                    require_user_verification=True,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
        if not verification:
            logger.warning(f"[passkeys] login verify failed: {last_err}")
            raise HTTPException(400, "WebAuthn authentication verification failed")

        # Update credential sign_count + last_used_at
        await db.user_passkeys.update_one(
            {"credential_id": cred_id_b64u, "rp_id": rp_id},
            {"$set": {
                "sign_count": verification.new_sign_count or 0,
                "last_used_at": _now(),
            }},
        )

        # Look up directory user row · MFA gate still applies (preserve doctrine)
        user_row = await db.user_directory.find_one(
            {"id": directory_user_id, "disabled": {"$ne": True}}, {"_id": 0},
        )
        if not user_row:
            raise HTTPException(401, "Account no longer active")

        # Mint EXACTLY the same multi-login response shape as password flow.
        return await mint_multi_login_response(user_row, request)

    # ════════════════════════════════════════════════════════════════
    # LIST · current user's enrolled passkeys (device-management read)
    # ════════════════════════════════════════════════════════════════
    @router.get("/list")
    async def list_passkeys(
        actor: Dict[str, Any] = Depends(require_directory_session_dep),
    ):
        user_id = str(actor.get("id") or "")
        if not user_id:
            raise HTTPException(401, "Directory session required")
        items = []
        async for c in db.user_passkeys.find(
            {"directory_user_id": user_id},
            {"_id": 0, "public_key": 0, "sign_count": 0},
        ):
            items.append(_public_passkey(c))
        return {"passkeys": items, "count": len(items)}

    # ════════════════════════════════════════════════════════════════
    # REVOKE · disable a passkey (lost-device flow)
    # ════════════════════════════════════════════════════════════════
    @router.delete("/{credential_id}")
    async def revoke_passkey(
        credential_id: str,
        actor: Dict[str, Any] = Depends(require_directory_session_dep),
    ):
        user_id = str(actor.get("id") or "")
        if not user_id:
            raise HTTPException(401, "Directory session required")
        res = await db.user_passkeys.update_one(
            {"directory_user_id": user_id, "credential_id": credential_id.strip()},
            {"$set": {"disabled": True, "disabled_at": _now()}},
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Passkey not found")
        return {"ok": True}

    return router


# ════════════════════════════════════════════════════════════════════
# Index management (TTL on challenges)
# ════════════════════════════════════════════════════════════════════
async def ensure_passkey_indexes(db) -> None:
    """Create TTL index on webauthn_challenges + unique index on user_passkeys.

    RC-2.1+ (2026-06-11) · Self-healing TTL index migration.
    The legacy `ttl_webauthn_challenges_created_at` index used a 24-hour
    TTL on the same `created_at` key the canonical `ix_webauthn_challenges_ttl`
    targets, so creating the canonical index failed with
    `IndexOptionsConflict` on every boot. The conflict was harmless
    (the legacy index still purged stale challenges, just at a much
    looser interval than the code intended), but it poisoned boot logs
    with a recurring WARNING. Detect the legacy index, drop it
    surgically (key+conflict proved equivalent), then create the
    canonical 5-minute TTL index. No challenge data is mutated.
    """
    try:
        existing = await db.webauthn_challenges.index_information()
        legacy = existing.get("ttl_webauthn_challenges_created_at")
        canonical = existing.get("ix_webauthn_challenges_ttl")
        legacy_key_matches = bool(
            legacy and any(k[0] == "created_at" for k in legacy.get("key", []))
        )
        if legacy and not canonical and legacy_key_matches:
            # Surgical migration: drop legacy ONLY when its key matches
            # the canonical TTL's key and the canonical doesn't yet exist.
            try:
                await db.webauthn_challenges.drop_index("ttl_webauthn_challenges_created_at")
                logger.info(
                    "[passkeys] migrated legacy TTL index "
                    "'ttl_webauthn_challenges_created_at' → "
                    "'ix_webauthn_challenges_ttl' (5-min TTL)"
                )
            except Exception as drop_exc:  # noqa: BLE001
                logger.warning(
                    f"[passkeys] legacy TTL index drop failed (will retry next boot): {drop_exc}"
                )
        await db.webauthn_challenges.create_index(
            [("created_at", 1)],
            expireAfterSeconds=CHALLENGE_TTL_SECONDS,
            name="ix_webauthn_challenges_ttl",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[passkeys] challenge TTL index ensure failed: {exc}")
    try:
        await db.user_passkeys.create_index(
            [("credential_id", 1), ("rp_id", 1)],
            name="ix_user_passkeys_cred",
            unique=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[passkeys] user_passkeys index ensure failed: {exc}")
    try:
        await db.user_passkeys.create_index(
            [("directory_user_id", 1), ("rp_id", 1)],
            name="ix_user_passkeys_owner",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[passkeys] user_passkeys owner index ensure failed: {exc}")
