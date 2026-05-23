"""
mfa.py · iter375 · Phase 4B · TOTP MFA for super-admin directory users.

SCOPE (kept narrow per the Zero Drift + Simplicity directives):
  • Only super-admin directory users (`user_directory` rows with
    `is_super_admin=True`) can enroll in MFA.
  • At multi-login, if the authenticated user has `mfa.enabled=True`,
    we DO NOT mint portal tokens immediately. We issue a short-lived
    "MFA challenge token" instead and require a TOTP (or recovery code)
    verification before the portal tokens are released.
  • Audit-logged in `mfa_audit_events` collection.
  • TOTP only (no SMS, no magic-link).

NOT included (deferred until clearly needed):
  • Step-up verification on individual actions (the existing admin token
    already represents a verified session; once minted, the operator
    trusts it until session-timeout).
  • Per-portal MFA for non-admin users.

Security primitives:
  • Secret encrypted at rest with Fernet (key from MFA_ENCRYPTION_KEY env).
  • Recovery codes bcrypt-hashed; never logged in plaintext.
  • Lockout after 5 consecutive failures (10-minute cool-down).
  • TOTP window tolerance = 1 (±30s clock skew).
"""
from __future__ import annotations

import logging
import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
import pyotp
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

MFA_ISSUER = "MASCI Operations"
TOTP_DIGITS = 6
TOTP_INTERVAL = 30
TOTP_VALID_WINDOW = 1  # ±30s skew tolerance
RECOVERY_CODE_COUNT = 10
RECOVERY_CODE_LENGTH = 10
LOCKOUT_MAX_FAILURES = 5
LOCKOUT_DURATION_MIN = 10
CHALLENGE_TOKEN_TTL_MIN = 5
RECENT_MFA_FRESHNESS_MIN = 30

_RECOVERY_ALPHABET = string.ascii_uppercase + string.digits


# ── Secret cipher (singleton, lazy) ─────────────────────────────────

_cipher: Optional[Fernet] = None


def _get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        key = os.environ.get("MFA_ENCRYPTION_KEY", "")
        if not key:
            raise RuntimeError("MFA_ENCRYPTION_KEY not configured")
        _cipher = Fernet(key.encode() if isinstance(key, str) else key)
    return _cipher


def encrypt_secret(plaintext_secret: str) -> str:
    return _get_cipher().encrypt(plaintext_secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    try:
        return _get_cipher().decrypt(encrypted_secret.encode()).decode()
    except InvalidToken as e:
        raise ValueError("MFA secret decryption failed") from e


# ── Recovery codes ──────────────────────────────────────────────────

def generate_recovery_code() -> str:
    return "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(RECOVERY_CODE_LENGTH))


def hash_recovery_code(code: str) -> str:
    return bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()


def verify_recovery_code(code: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(code.encode(), hashed.encode())
    except Exception:  # noqa: BLE001
        return False


def generate_recovery_codes() -> Tuple[List[str], List[str]]:
    codes = [generate_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
    hashes = [hash_recovery_code(c) for c in codes]
    return codes, hashes


# ── TOTP ────────────────────────────────────────────────────────────

def create_totp_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL).provisioning_uri(
        name=email, issuer_name=MFA_ISSUER,
    )


def verify_totp_code(secret: str, code: str) -> bool:
    code = (code or "").strip()
    if not code.isdigit() or len(code) != TOTP_DIGITS:
        return False
    return pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL).verify(
        code, valid_window=TOTP_VALID_WINDOW,
    )


# ── Challenge tokens (short-lived, signed via mfa cipher) ───────────
# A challenge token is the proof that the user has passed password
# verification but not yet TOTP. We use the existing cipher to encrypt
# a JSON payload so we don't need a new secret. TTL is 5 minutes.

import json


def mint_challenge_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=CHALLENGE_TOKEN_TTL_MIN)).timestamp()),
        "purpose": "mfa_challenge",
    }
    return _get_cipher().encrypt(json.dumps(payload).encode()).decode()


def verify_challenge_token(token: str) -> Optional[str]:
    """Return the user_id if the challenge token is valid + unexpired."""
    if not token:
        return None
    try:
        raw = _get_cipher().decrypt(token.encode(), ttl=CHALLENGE_TOKEN_TTL_MIN * 60).decode()
        payload = json.loads(raw)
    except (InvalidToken, ValueError, json.JSONDecodeError):
        return None
    if payload.get("purpose") != "mfa_challenge":
        return None
    return payload.get("sub")


# ── MongoDB helpers — operate on user_directory rows ────────────────

async def get_mfa_config(db, user_id: str) -> Dict[str, Any]:
    """Returns the user's MFA subdocument (or empty dict)."""
    row = await db.user_directory.find_one(
        {"id": user_id}, {"_id": 0, "mfa": 1},
    )
    return (row or {}).get("mfa") or {}


async def set_mfa_config(db, user_id: str, mfa_update: Dict[str, Any]) -> None:
    """Merge-set the MFA subdocument."""
    set_doc = {f"mfa.{k}": v for k, v in mfa_update.items()}
    await db.user_directory.update_one(
        {"id": user_id}, {"$set": set_doc},
    )


async def clear_mfa_config(db, user_id: str) -> None:
    await db.user_directory.update_one(
        {"id": user_id}, {"$unset": {"mfa": ""}},
    )


# ── Lockout helpers ─────────────────────────────────────────────────

def is_locked(mfa_cfg: Dict[str, Any]) -> bool:
    locked_until = mfa_cfg.get("locked_until")
    if not locked_until:
        return False
    try:
        if isinstance(locked_until, str):
            locked_until_dt = datetime.fromisoformat(locked_until)
        else:
            locked_until_dt = locked_until
        if locked_until_dt.tzinfo is None:
            locked_until_dt = locked_until_dt.replace(tzinfo=timezone.utc)
        return locked_until_dt > datetime.now(timezone.utc)
    except Exception:  # noqa: BLE001
        return False


async def register_failure(db, user_id: str, mfa_cfg: Dict[str, Any]) -> bool:
    """Increment failure counter; lock if threshold reached. Returns
    True if the user is now locked."""
    fails = int(mfa_cfg.get("failed_attempts") or 0) + 1
    update: Dict[str, Any] = {
        "failed_attempts": fails,
        "last_failed_at": datetime.now(timezone.utc).isoformat(),
    }
    locked = False
    if fails >= LOCKOUT_MAX_FAILURES:
        update["locked_until"] = (
            datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MIN)
        ).isoformat()
        locked = True
    await set_mfa_config(db, user_id, update)
    return locked


async def reset_failures(db, user_id: str) -> None:
    await set_mfa_config(db, user_id, {
        "failed_attempts": 0,
        "locked_until": None,
        "last_failed_at": None,
    })


# ── Audit log ───────────────────────────────────────────────────────

async def write_audit(
    db,
    *,
    user_id: str,
    user_email: Optional[str],
    event: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert a row in `mfa_audit_events`. Never logs secrets/codes."""
    try:
        await db.mfa_audit_events.insert_one({
            "id": secrets.token_urlsafe(16),
            "at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "user_email": user_email,
            "event": event,
            "ip": ip,
            "user_agent": (user_agent or "")[:240],
            "metadata": metadata or {},
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[mfa-audit] insert failed: {e}")


__all__ = [
    "MFA_ISSUER",
    "RECENT_MFA_FRESHNESS_MIN",
    "encrypt_secret",
    "decrypt_secret",
    "generate_recovery_codes",
    "verify_recovery_code",
    "create_totp_secret",
    "build_otpauth_uri",
    "verify_totp_code",
    "mint_challenge_token",
    "verify_challenge_token",
    "get_mfa_config",
    "set_mfa_config",
    "clear_mfa_config",
    "is_locked",
    "register_failure",
    "reset_failures",
    "write_audit",
]
