"""Rate-limiting and login-lockout helpers — extracted from server.py in Track 22.1.

Public POST endpoints (form submissions, translate) are unauthenticated by
design — crews submit without logging in. To prevent spam / bot abuse we
cap each IP to N submissions per hour per endpoint. Single-instance backend
so a process-local dict is sufficient — no Redis required.

Login-fail lockout uses the same in-memory buckets to short-circuit
repeat-fail admin/user login attempts.

Extraction rule (Zero-Drift, Track 22.1):
- All public names below are re-imported into `backend/server.py`
  under identical names so every existing bare-name reference and every
  `Depends(rate_limit_public_post)` resolves to the same callable object.
- The in-memory buckets live here now; they were previously module-locals
  of server.py. There are no cross-module writers of the buckets, so the
  move is behavior-identical (same process, same lock, same lifecycle).
"""
from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List

from fastapi import HTTPException, Request

# ---------------------------------------------------------------------------
# Module-local state (single-process, in-memory — same as pre-22.1 server.py).
# ---------------------------------------------------------------------------
_RATE_LOCK = Lock()
_PUBLIC_POST_BUCKETS: Dict[str, List[float]] = defaultdict(list)
_LOGIN_FAIL_BUCKETS: Dict[str, List[float]] = defaultdict(list)

PUBLIC_POST_LIMIT_PER_HOUR = int(os.environ.get("PUBLIC_POST_LIMIT_PER_HOUR", "30"))
LOGIN_MAX_FAILS_PER_WINDOW = int(os.environ.get("LOGIN_MAX_FAILS", "10"))
LOGIN_LOCKOUT_SECONDS = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min


def _is_test_request(request: Request | None = None) -> bool:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if request is not None and app_env != "production":
        if (request.headers.get("x-test-rate-limit-bypass") or "").strip() == "1":
            return True
    if request is not None and getattr(getattr(request, "app", None), "state", None):
        return bool(getattr(request.app.state, "testing", False))
    return False


def _client_ip(request: Request) -> str:
    """Best-effort per-device / per-user rate-limit identity.

    Order of preference:
    1. Stable frontend device id header
    2. Authenticated caller token hash (prevents all ingress traffic sharing one bucket)
    3. Forwarded/peer IP as a last resort
    """
    device_id = (request.headers.get("x-device-id") or "").strip()
    if device_id:
        return f"device:{device_id[:120]}"

    auth_headers = (
        "x-directory-token",
        "x-admin-token",
        "x-pm-token",
        "x-hr-token",
        "x-shop-token",
        "x-safety-token",
        "x-dispatch-token",
        "x-fl-token",
        "x-leadership-token",
        "authorization",
    )
    for header_name in auth_headers:
        raw = (request.headers.get(header_name) or "").strip()
        if not raw:
            continue
        digest = hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:24]
        return f"auth:{header_name}:{digest}"

    xff = request.headers.get("x-forwarded-for") or ""
    if xff:
        return f"ip:{xff.split(',')[0].strip()}"
    return f"ip:{request.client.host}" if request.client else "ip:unknown"


def rate_limit_public_post(request: Request):
    """FastAPI dependency that throttles each (IP, endpoint) to
    PUBLIC_POST_LIMIT_PER_HOUR submissions. Raises 429 when exceeded.
    Set RATE_LIMITING=off in .env to disable (e.g., automated tests)."""
    if os.environ.get("RATE_LIMITING", "on").lower() in ("off", "false", "0"):
        return
    if _is_test_request(request):
        return
    ip = _client_ip(request)
    key = f"{request.url.path}:{ip}"
    now = time.time()
    cutoff = now - 3600
    with _RATE_LOCK:
        bucket = _PUBLIC_POST_BUCKETS[key]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= PUBLIC_POST_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many submissions from this device "
                    f"(limit {PUBLIC_POST_LIMIT_PER_HOUR}/hour). "
                    f"Try again later or contact MASCI safety."
                ),
            )
        bucket.append(now)


def _check_login_lockout(ip: str) -> None:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    cutoff = time.time() - LOGIN_LOCKOUT_SECONDS
    with _RATE_LOCK:
        bucket = _LOGIN_FAIL_BUCKETS[ip]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= LOGIN_MAX_FAILS_PER_WINDOW:
            oldest = bucket[0]
            wait_s = int(LOGIN_LOCKOUT_SECONDS - (time.time() - oldest))
            wait_min = max(1, (wait_s + 59) // 60)
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many failed login attempts. "
                    f"Try again in ~{wait_min} minute(s)."
                ),
            )


def _record_login_fail(ip: str) -> None:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS[ip].append(time.time())


def _reset_login_fails(ip: str) -> None:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS.pop(ip, None)
