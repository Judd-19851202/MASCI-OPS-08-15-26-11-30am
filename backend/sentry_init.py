"""sentry_init.py — env-gated Sentry initialization for the FastAPI backend.

Scope (per Initiative 1, Phase 2 hardening):
    • Production-only by intent; the actual gate is the presence of
      ``SENTRY_DSN``. If DSN is absent → complete no-op (no exceptions,
      no warnings, no side effects).
    • Release identifier comes from ``/api/version``'s ``source_hash``
      so release health groups crashes by deployed code automatically.
    • Environment tag from ``SENTRY_ENV`` (defaults to "production"
      when ``ENVIRONMENT`` is unset, but the integration only fires at
      all when DSN is present, so dev/staging stays clean unless an
      operator explicitly opts in).
    • PII scrubber: deny-list of password*, token*, secret*, api_key*,
      Authorization / Cookie headers, and request body keys matching
      the same patterns.
    • Release-health (session tracking) enabled when supported.

This module exposes ONE public function:

    init_sentry_if_configured() -> bool

Returns True if Sentry was initialized, False otherwise. Safe to call
multiple times — second call is a no-op.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_INITIALIZED = False
_RELEASE_OVERRIDE: Optional[str] = None

# Field-name patterns we never want in a Sentry event. Case-insensitive
# substring match against dict keys, query-string keys, and form keys.
_PII_KEY_PATTERNS = re.compile(
    r"(password|secret|token|api[_-]?key|bearer|private[_-]?key|"
    r"session|cookie|auth)", re.IGNORECASE,
)

# Headers always stripped from breadcrumbs / request context.
_DENY_HEADERS = {
    "authorization", "cookie", "set-cookie",
    "x-admin-token", "x-pm-token", "x-hr-token", "x-shop-token",
    "x-dispatch-token", "x-safety-token", "x-field-leadership-token",
    "x-dev-token",
}


def _truthy(v: Optional[str]) -> bool:
    return bool(v and v.strip().lower() in ("1", "true", "yes", "on"))


def _read_release_identifier() -> str:
    """Try to read the deterministic deploy-version source_hash. Falls
    back to the platform's commit env vars and finally "unknown"."""
    for var in ("DEPLOY_VERSION_HASH", "DEPLOY_VERSION",
                "GIT_COMMIT", "RAILWAY_GIT_COMMIT_SHA",
                "VERCEL_GIT_COMMIT_SHA"):
        v = os.environ.get(var, "").strip()
        if v:
            return v[:16]
    # Last resort: re-derive from server.py (matches /api/version source_hash)
    try:
        from pathlib import Path
        import hashlib as _h
        srv = Path(__file__).parent / "server.py"
        if srv.exists():
            return _h.sha256(srv.read_bytes()).hexdigest()[:16]
    except Exception:
        pass
    return "unknown"


def _scrub_value(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: ("***SCRUBBED***" if _PII_KEY_PATTERNS.search(str(k)) else _scrub_value(val))
                for k, val in v.items()}
    if isinstance(v, list):
        return [_scrub_value(x) for x in v]
    return v


def _scrub_request(req: dict) -> dict:
    """Strip auth/PII from the captured request dict in-place."""
    if not isinstance(req, dict):
        return req
    headers = req.get("headers")
    if isinstance(headers, dict):
        for h in list(headers.keys()):
            if h.lower() in _DENY_HEADERS:
                headers[h] = "***SCRUBBED***"
    elif isinstance(headers, list):
        # weasyprint sometimes encodes as list of [k, v]
        for pair in headers:
            if isinstance(pair, list) and pair and isinstance(pair[0], str):
                if pair[0].lower() in _DENY_HEADERS:
                    pair[1] = "***SCRUBBED***"
    qs = req.get("query_string")
    if isinstance(qs, dict):
        req["query_string"] = _scrub_value(qs)
    data = req.get("data")
    if isinstance(data, (dict, list)):
        req["data"] = _scrub_value(data)
    cookies = req.get("cookies")
    if cookies:
        req["cookies"] = "***SCRUBBED***"
    return req


def _before_send(event: dict, _hint: dict) -> Optional[dict]:
    """Sentry hook — scrub PII before the event leaves the process."""
    try:
        if "request" in event:
            event["request"] = _scrub_request(event["request"])
        if "extra" in event and isinstance(event["extra"], dict):
            event["extra"] = _scrub_value(event["extra"])
        if "contexts" in event and isinstance(event["contexts"], dict):
            event["contexts"] = _scrub_value(event["contexts"])
        # Strip token-shaped strings out of logentry messages defensively.
        msg = event.get("logentry", {}).get("message")
        if isinstance(msg, str) and len(msg) > 32:
            # If the message looks like it contains a 64-char hex blob
            # (HMAC token shape) — redact it.
            event["logentry"]["message"] = re.sub(r"[a-f0-9]{40,}", "***SCRUBBED***", msg)
    except Exception:  # noqa: BLE001
        # Never let the scrubber crash the event.
        pass
    return event


def init_sentry_if_configured(release_override: Optional[str] = None) -> bool:
    """Initialise Sentry if and only if SENTRY_DSN is set. Returns True
    on success, False otherwise. Safe to call multiple times.

    ``release_override`` lets the caller (server.py) pass the
    canonical _SOURCE_HASH so /api/version's ``source_hash`` and
    Sentry's ``release`` are exactly the same string."""
    global _INITIALIZED
    if _INITIALIZED:
        return True

    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        # No DSN → complete no-op. This is the production-safe default.
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError as e:
        logger.warning("[sentry] DSN set but sentry-sdk not installed: %s", e)
        return False

    env = os.environ.get("SENTRY_ENV") or os.environ.get("ENVIRONMENT") or "production"
    release = release_override or _read_release_identifier()
    if release_override:
        # Cache so get_release_identifier() agrees.
        global _RELEASE_OVERRIDE
        _RELEASE_OVERRIDE = release_override
    traces_rate = float(os.environ.get("SENTRY_TRACES_RATE", "0") or 0)
    profiles_rate = float(os.environ.get("SENTRY_PROFILES_RATE", "0") or 0)
    send_default_pii = False  # Always False — we control PII via before_send.

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=env,
            release=release,
            send_default_pii=send_default_pii,
            traces_sample_rate=traces_rate,
            profiles_sample_rate=profiles_rate,
            auto_session_tracking=True,
            attach_stacktrace=True,
            before_send=_before_send,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.INFO,         # capture INFO+ as breadcrumbs
                    event_level=logging.ERROR,  # ERROR+ becomes an event
                ),
            ],
        )
        # Tag every event with the platform name so dashboards can filter.
        sentry_sdk.set_tag("platform", "masci-hub")
        sentry_sdk.set_tag("component", "backend")
        _INITIALIZED = True
        logger.info("[sentry] initialised · env=%s release=%s", env, release)
        return True
    except Exception as e:  # noqa: BLE001
        # NEVER let Sentry init blow up the app.
        logger.warning("[sentry] init failed: %s", e)
        return False


def is_initialized() -> bool:
    return _INITIALIZED


def get_release_identifier() -> str:
    """Public helper so /api/version and the frontend bundle can agree
    on the same release string. Returns the override passed at init
    time if set, else falls back to env/source-file detection."""
    if _RELEASE_OVERRIDE:
        return _RELEASE_OVERRIDE
    return _read_release_identifier()
