"""TRACK 22.3 · Integration Truth Surface + AI Key Status + DR-V2 Alias Telemetry.

Admin-only endpoints exposing the RUNTIME truth about:
  • AI provider keys (read from os.environ — NOT dotenv/.env placeholders)
  • Third-party integrations (three-state model: config / connectivity / operational)
  • Legacy /api/dr-v2/* alias usage (30-day TTL detail + permanent aggregate)

Trust doctrine (Track 22.2 F-01 / F-02 remediation)
---------------------------------------------------
- We NEVER declare an integration LIVE_VERIFIED from configuration alone.
- Three states are reported separately so the operator can see the whole
  picture: configured/not, reachable/not, currently doing useful work/not.
- Temporary connectivity failures degrade CONNECTIVITY but do not falsely
  declare the integration dead when recent operational activity exists.
- Secrets are NEVER returned. Only booleans + masked last-4 characters.

Endpoints (all gated by ``require_admin_strict``)
-------------------------------------------------
- ``GET /api/admin/ai/keys/status``
- ``GET /api/admin/integrations/truth-status``
- ``GET /api/admin/dr-v2-alias-telemetry``
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)

from lib.canonical_status import DEGRADED, MISMATCH, NOT_APPLICABLE, UNVERIFIABLE, VERIFIED, to_canonical
from lib.runtime_identity import runtime_identity_public_payload


# ─────────────────── constants / enums ────────────────────────────

# Three-state model — reported separately per integration.
CONFIG_STATUSES = ("CONFIGURED", "PARTIAL_CONFIG", "MISSING_CONFIG", "MOCKED", "DISABLED")
CONNECTIVITY_STATUSES = ("REACHABLE", "UNREACHABLE", "UNKNOWN", "NOT_APPLICABLE")
OPERATIONAL_STATUSES = ("LIVE_VERIFIED", "IDLE", "STALE", "NO_ACTIVITY", "NOT_APPLICABLE")

# Overall roll-up (derived) — never claim LIVE_VERIFIED without proof.
OVERALL_STATUSES = (
    "LIVE_VERIFIED",   # config OK + reachable + recent successful activity
    "CONFIGURED",      # config OK + no proof of recent activity
    "PARTIAL",         # some works, some does not
    "MISSING_CONFIG",  # not fully configured
    "MISSING_SECRET",  # required secret absent
    "UNREACHABLE",     # configured but can't reach provider
    "MOCKED",          # explicitly not connected (e.g. MaintainX)
    "DISABLED",        # feature intentionally off
    "ERROR",           # unexpected failure
)

# Recent-activity window that keeps an integration classified LIVE_VERIFIED
# even when a live ping fails (Motive doctrine from Track 22.3 ask_human).
LIVE_ACTIVITY_WINDOW_MINUTES = 15

# TTL for detailed dr_v2 alias telemetry events. Migration-only signal;
# permanent aggregates live alongside until DR-UNIFY-005 retires the aliases.
DR_V2_ALIAS_TTL_DAYS = 30

# Motive live probe timeout.
MOTIVE_PROBE_TIMEOUT_SECONDS = 3.0


# ─────────────────── helpers ──────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _mask_last4(value: str) -> Optional[str]:
    """Return a masked representation exposing only the last 4 chars.

    Never returns the whole key. Empty/short strings return None so the
    UI can render "not set" cleanly.
    """
    v = (value or "").strip()
    if not v:
        return None
    if len(v) <= 4:
        return "****"
    return f"…{v[-4:]}"


def _env_present(name: str) -> bool:
    """True iff the env var is set to a non-empty string.

    We read from ``os.environ`` directly (never ``dotenv_values``) so the
    Emergent-injected runtime secrets are seen.
    """
    return bool((os.environ.get(name) or "").strip())


def _read_env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


# ─────────────────── AI key status ────────────────────────────────

# Providers we surface in the truth panel. Each row = (provider_key,
# display_name, env_var, whether the emergent universal key can stand in).
_AI_PROVIDERS = (
    ("emergent_llm", "Emergent Universal LLM Key", "EMERGENT_LLM_KEY", False),
    ("anthropic",    "Anthropic (Claude)",         "ANTHROPIC_API_KEY", True),
    ("openai",       "OpenAI (GPT / image)",       "OPENAI_API_KEY",    True),
    ("gemini",       "Google Gemini",              "GEMINI_API_KEY",    True),
    ("google_ai",    "Google AI (alt env)",        "GOOGLE_AI_API_KEY", True),
)


def _ai_key_row(provider_key: str, display_name: str, env_var: str,
                emergent_ok: bool) -> Dict[str, Any]:
    """Compute a single AI key row from live ``os.environ`` state."""
    key_val = _read_env(env_var)
    key_present = bool(key_val)
    emergent_key_val = _read_env("EMERGENT_LLM_KEY")
    covered_by_universal = emergent_ok and bool(emergent_key_val)

    if key_present:
        status = "CONFIGURED"
        detail = f"{env_var} present at runtime"
    elif covered_by_universal:
        status = "CONFIGURED_VIA_UNIVERSAL"
        detail = "Provider key absent; Emergent Universal LLM Key covers this provider"
    else:
        status = "MISSING_SECRET"
        detail = (
            f"{env_var} not set at runtime — configure via Emergent Secrets UI"
            if env_var != "EMERGENT_LLM_KEY"
            else "Universal key missing — AI features off"
        )

    return {
        "provider": provider_key,
        "name": display_name,
        "env_var": env_var,
        "key_present": key_present,
        "key_last4": _mask_last4(key_val),
        "covered_by_universal": covered_by_universal,
        "status": status,
        "detail": detail,
    }


async def _ai_keys_status_payload() -> Dict[str, Any]:
    rows = [_ai_key_row(*p) for p in _AI_PROVIDERS]
    any_present = any(r["key_present"] or r["covered_by_universal"] for r in rows)
    for row in rows:
        row["canonical_status"] = to_canonical(row.get("status"))
    return {
        "status": VERIFIED if any_present else DEGRADED,
        "checked_at": _now_iso(),
        "reads_from": "os.environ (runtime — not dotenv/.env placeholders)",
        "any_provider_available": any_present,
        "providers": rows,
        "doctrine": (
            "Runtime truth only. Emergent-injected secrets bypass .env "
            "placeholders. Never displays raw key values."
        ),
    }


# ─────────────────── Integrations truth ───────────────────────────

async def _motive_truth(db) -> Dict[str, Any]:
    """Motive three-state truth.

    Config:    key present in settings OR env
    Connect:   live 3s GET /v1/users/me — degrades UNREACHABLE on failure
    Ops:       last_successful_sync_at within LIVE_ACTIVITY_WINDOW_MINUTES
    """
    settings_key = ""
    last_success = None
    settings_enabled = None
    try:
        doc = await db.integration_settings.find_one({"provider": "motive"}, {"_id": 0})
        if doc:
            settings_key = (doc.get("api_key_value") or "").strip()
            last_success = doc.get("last_successful_sync_at")
            settings_enabled = doc.get("enabled")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[integration-truth motive settings] {exc}")

    env_key = _read_env("MOTIVE_API_KEY")
    api_key = settings_key or env_key
    api_key_source = (
        "integration_settings" if settings_key
        else ("env" if env_key else "none")
    )

    # 1) Configuration
    if not api_key:
        config_status = "MISSING_CONFIG"
    elif settings_enabled is False:
        config_status = "DISABLED"
    else:
        config_status = "CONFIGURED"

    # 2) Operational — recent successful sync ⇒ LIVE_VERIFIED regardless of
    #    momentary ping trouble.
    operational_status = "NO_ACTIVITY"
    activity_age_seconds: Optional[int] = None
    if last_success:
        try:
            dt = (
                last_success if isinstance(last_success, datetime)
                else datetime.fromisoformat(str(last_success).replace("Z", "+00:00"))
            )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = (_now() - dt).total_seconds()
            activity_age_seconds = int(age)
            operational_status = (
                "LIVE_VERIFIED" if age <= LIVE_ACTIVITY_WINDOW_MINUTES * 60
                else "STALE"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[integration-truth motive age] {exc}")

    # 3) Connectivity — only ping when configured.
    connectivity_status = "NOT_APPLICABLE"
    connectivity_detail = "Skipped (not configured)"
    connectivity_latency_ms: Optional[int] = None
    if config_status == "CONFIGURED":
        base_url = _read_env("MOTIVE_BASE_URL") or "https://api.gomotive.com"
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=MOTIVE_PROBE_TIMEOUT_SECONDS) as client:
                r = await client.get(
                    f"{base_url.rstrip('/')}/v1/users/me",
                    headers={"X-Api-Key": api_key, "Accept": "application/json"},
                )
            connectivity_latency_ms = int((time.monotonic() - t0) * 1000)
            if r.status_code == 200:
                connectivity_status = "REACHABLE"
                connectivity_detail = f"HTTP 200 · {connectivity_latency_ms}ms"
            elif r.status_code in (401, 403):
                connectivity_status = "UNREACHABLE"
                connectivity_detail = f"Auth rejected · HTTP {r.status_code}"
            else:
                connectivity_status = "UNREACHABLE"
                connectivity_detail = f"HTTP {r.status_code}"
        except Exception as exc:  # noqa: BLE001
            connectivity_status = "UNREACHABLE"
            connectivity_detail = f"{type(exc).__name__}: {str(exc)[:120]}"
            connectivity_latency_ms = int((time.monotonic() - t0) * 1000)

    # Overall roll-up — recent activity wins over connectivity blip.
    if config_status == "DISABLED":
        overall = "DISABLED"
    elif config_status == "MISSING_CONFIG":
        overall = "MISSING_SECRET"
    elif operational_status == "LIVE_VERIFIED":
        overall = "LIVE_VERIFIED"
    elif connectivity_status == "REACHABLE":
        overall = "CONFIGURED"  # reachable, no recent sync yet
    elif connectivity_status == "UNREACHABLE":
        overall = "UNREACHABLE"
    else:
        overall = "CONFIGURED"

    return {
        "id": "motive",
        "name": "Motive (Telematics)",
        "expected_state": "LIVE",
        "mocked": False,
        "config_status": config_status,
        "connectivity_status": connectivity_status,
        "operational_status": operational_status,
        "overall": overall,
        "api_key_present": bool(api_key),
        "api_key_source": api_key_source,
        "api_key_last4": _mask_last4(api_key),
        "connectivity_latency_ms": connectivity_latency_ms,
        "connectivity_detail": connectivity_detail,
        "last_successful_sync_at": last_success.isoformat() if isinstance(last_success, datetime) else last_success,
        "activity_age_seconds": activity_age_seconds,
        "live_window_seconds": LIVE_ACTIVITY_WINDOW_MINUTES * 60,
        "canonical_status": to_canonical(overall),
    }


def _maintainx_truth() -> Dict[str, Any]:
    """MaintainX — expected mocked. Never claim LIVE_VERIFIED."""
    api_key = _read_env("MAINTAINX_API_KEY")
    base = _read_env("MAINTAINX_BASE_URL")
    configured = bool(api_key and base)
    return {
        "id": "maintainx",
        "name": "MaintainX (Work Orders)",
        "expected_state": "MOCKED",
        "mocked": True,
        "config_status": "CONFIGURED" if configured else "MOCKED",
        "connectivity_status": "NOT_APPLICABLE",
        "operational_status": "NOT_APPLICABLE",
        "overall": "MOCKED",
        "api_key_present": bool(api_key),
        "api_key_source": "env" if api_key else "none",
        "api_key_last4": _mask_last4(api_key),
        "detail": (
            "MOCKED — no live API integration; events surface via "
            "operations_events. Reality by design."
        ),
        "canonical_status": NOT_APPLICABLE,
    }


def _resend_truth() -> Dict[str, Any]:
    key = _read_env("RESEND_API_KEY")
    auto = _read_env("AUTO_EMAIL_REPORTS").lower() in {"1", "true", "yes", "on"}
    if not key:
        config_status = "MISSING_CONFIG"
        overall = "MISSING_SECRET"
        detail = "RESEND_API_KEY not set at runtime"
    elif not key.startswith("re_"):
        config_status = "PARTIAL_CONFIG"
        overall = "PARTIAL"
        detail = "Key present but does not match `re_…` shape"
    else:
        config_status = "CONFIGURED"
        overall = "CONFIGURED" if auto else "DISABLED"
        detail = f"Key present · auto_email={'ON' if auto else 'OFF'}"
    return {
        "id": "resend",
        "name": "Resend (Email)",
        "expected_state": "LIVE",
        "mocked": False,
        "config_status": config_status,
        "connectivity_status": "UNKNOWN",
        "operational_status": "IDLE",
        "overall": overall,
        "api_key_present": bool(key),
        "api_key_source": "env" if key else "none",
        "api_key_last4": _mask_last4(key),
        "auto_email_enabled": auto,
        "detail": detail,
        "canonical_status": to_canonical(overall),
    }


async def _mongo_truth(db) -> Dict[str, Any]:
    t0 = time.monotonic()
    try:
        await asyncio.wait_for(db.command("ping"), timeout=3.0)
        latency = int((time.monotonic() - t0) * 1000)
        return {
            "id": "mongo",
            "name": "MongoDB (Atlas)",
            "expected_state": "LIVE",
            "mocked": False,
            "config_status": "CONFIGURED",
            "connectivity_status": "REACHABLE",
            "operational_status": "LIVE_VERIFIED",
            "overall": "LIVE_VERIFIED",
            "api_key_present": True,
            "connectivity_latency_ms": latency,
            "detail": f"Ping OK · {latency}ms",
            "canonical_status": VERIFIED,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "id": "mongo",
            "name": "MongoDB (Atlas)",
            "expected_state": "LIVE",
            "mocked": False,
            "config_status": "CONFIGURED",
            "connectivity_status": "UNREACHABLE",
            "operational_status": "NO_ACTIVITY",
            "overall": "ERROR",
            "detail": f"Ping failed: {str(exc)[:120]}",
            "canonical_status": MISMATCH,
        }


def _r2_truth() -> Dict[str, Any]:
    access = _env_present("S3_ACCESS_KEY")
    secret = _env_present("S3_SECRET_KEY")
    bucket = _env_present("S3_BUCKET")
    endpoint = _env_present("S3_ENDPOINT_URL")
    parts = [access, secret, bucket, endpoint]
    if all(parts):
        config_status = "CONFIGURED"
        overall = "CONFIGURED"
        detail = "R2 credentials + bucket + endpoint present"
    elif any(parts):
        config_status = "PARTIAL_CONFIG"
        overall = "PARTIAL"
        detail = "R2 partially configured — some env vars missing"
    else:
        config_status = "MISSING_CONFIG"
        overall = "MISSING_CONFIG"
        detail = "R2 not configured — uploads fall back to inline base64"
    return {
        "id": "r2",
        "name": "Cloudflare R2 (Object Storage)",
        "expected_state": "LIVE",
        "mocked": False,
        "config_status": config_status,
        "connectivity_status": "UNKNOWN",
        "operational_status": "IDLE",
        "overall": overall,
        "api_key_present": access and secret,
        "detail": detail,
        "canonical_status": to_canonical(overall),
    }


def _sentry_truth() -> Dict[str, Any]:
    dsn = _read_env("SENTRY_DSN")
    if not dsn:
        return {
            "id": "sentry",
            "name": "Sentry (Error Tracking)",
            "expected_state": "OPTIONAL",
            "mocked": False,
            "config_status": "MISSING_CONFIG",
            "connectivity_status": "NOT_APPLICABLE",
            "operational_status": "NOT_APPLICABLE",
            "overall": "DISABLED",
            "api_key_present": False,
            "detail": "SENTRY_DSN not set — error tracking off",
            "canonical_status": NOT_APPLICABLE,
        }
    return {
        "id": "sentry",
        "name": "Sentry (Error Tracking)",
        "expected_state": "LIVE",
        "mocked": False,
        "config_status": "CONFIGURED",
        "connectivity_status": "UNKNOWN",
        "operational_status": "IDLE",
        "overall": "CONFIGURED",
        "api_key_present": True,
        "api_key_last4": _mask_last4(dsn),
        "detail": "Sentry DSN present at runtime",
        "canonical_status": VERIFIED,
    }


def _emergent_llm_truth() -> Dict[str, Any]:
    key = _read_env("EMERGENT_LLM_KEY")
    if not key:
        overall = "MISSING_SECRET"
        detail = "EMERGENT_LLM_KEY not set at runtime"
        config_status = "MISSING_CONFIG"
    elif not key.startswith("sk-emergent-"):
        overall = "PARTIAL"
        detail = "Key present but unexpected prefix"
        config_status = "PARTIAL_CONFIG"
    else:
        overall = "CONFIGURED"
        detail = "Universal LLM key present at runtime"
        config_status = "CONFIGURED"
    return {
        "id": "emergent_llm",
        "name": "Emergent Universal LLM Key",
        "expected_state": "LIVE",
        "mocked": False,
        "config_status": config_status,
        "connectivity_status": "UNKNOWN",
        "operational_status": "IDLE",
        "overall": overall,
        "api_key_present": bool(key),
        "api_key_source": "env" if key else "none",
        "api_key_last4": _mask_last4(key),
        "detail": detail,
        "canonical_status": to_canonical(overall),
    }


async def _integrations_truth_payload(db, runtime_identity_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    motive, mongo = await asyncio.gather(
        _motive_truth(db),
        _mongo_truth(db),
        return_exceptions=False,
    )
    integrations = [
        mongo,
        motive,
        _maintainx_truth(),
        _resend_truth(),
        _r2_truth(),
        _sentry_truth(),
        _emergent_llm_truth(),
    ]
    # Roll-up: pessimistic — anything below LIVE_VERIFIED knocks it down,
    # but a single UNREACHABLE integration does not collapse the whole
    # surface (the operator can see per-row status). ERROR is reserved
    # for true failures (e.g. Mongo down).
    runtime_identity_status = (runtime_identity_payload or {}).get("status", UNVERIFIABLE)
    canonical_states = [row.get("canonical_status", UNVERIFIABLE) for row in integrations]
    if runtime_identity_status not in {VERIFIED, NOT_APPLICABLE}:
        overall = runtime_identity_status
    elif MISMATCH in canonical_states:
        overall = MISMATCH
    elif UNVERIFIABLE in canonical_states:
        overall = UNVERIFIABLE
    elif DEGRADED in canonical_states:
        overall = DEGRADED
    elif canonical_states:
        overall = VERIFIED
    else:
        overall = NOT_APPLICABLE
    return {
        "checked_at": _now_iso(),
        "overall": overall,
        "runtime_identity": runtime_identity_payload,
        "integrations": integrations,
        "doctrine": (
            "Three-state truth: configuration, connectivity, and operational "
            "activity reported independently. LIVE_VERIFIED requires recent "
            "successful activity — not just credentials."
        ),
    }


# ─────────────────── DR-V2 alias telemetry ────────────────────────

ALIAS_EVENTS_COLL = "dr_v2_alias_telemetry_events"
ALIAS_AGGREGATE_COLL = "dr_v2_alias_aggregate"


async def ensure_dr_v2_alias_indexes(db) -> None:
    """Create TTL + query indexes for legacy dr-v2 alias telemetry.

    Idempotent; safe to call on every boot. Detail events auto-expire
    after 30 days. Aggregate records live until DR-UNIFY-005 formally
    retires the aliases.
    """
    try:
        await db[ALIAS_EVENTS_COLL].create_index(
            [("at", 1)],
            expireAfterSeconds=DR_V2_ALIAS_TTL_DAYS * 24 * 60 * 60,
            name="dr_v2_alias_events_ttl",
        )
        await db[ALIAS_EVENTS_COLL].create_index(
            [("path", 1), ("at", -1)],
            name="dr_v2_alias_events_by_path_at",
        )
        await db[ALIAS_AGGREGATE_COLL].create_index(
            [("route_key", 1)],
            unique=True,
            name="dr_v2_alias_aggregate_route_key",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[dr-v2 alias indexes] {exc}")


def _classify_role(request) -> str:
    """Best-effort caller role classification from headers.

    Never blocks the request path — used purely for telemetry labeling.
    """
    headers = request.headers
    if headers.get("X-Admin-Token"):
        return "admin"
    if headers.get("X-PM-Token"):
        return "pm"
    if headers.get("X-Shop-Token"):
        return "shop"
    if headers.get("X-HR-Token"):
        return "hr"
    if headers.get("X-Safety-Token"):
        return "safety"
    if headers.get("X-Dispatch-Token"):
        return "dispatch"
    if headers.get("X-FL-Token") or headers.get("X-Leadership-Token"):
        return "field_leadership"
    if headers.get("Authorization"):
        return "bearer"
    return "anonymous"


async def record_dr_v2_alias_hit(db, request) -> None:
    """Persist one alias hit (detail event + aggregate upsert).

    Called from the FastAPI middleware for every request whose path
    starts with ``/api/dr-v2/``. Never raises — failures are swallowed
    and logged. The originating request must NEVER be affected.
    """
    try:
        path = request.url.path
        method = request.method
        route_key = f"{method} {path}"
        now = _now()
        runtime_identity_bundle = getattr(getattr(request, "app", None), "state", None)
        runtime_identity_bundle = getattr(runtime_identity_bundle, "runtime_identity_bundle", None)
        runtime_identity_payload = runtime_identity_public_payload(runtime_identity_bundle) if runtime_identity_bundle else None
        env = (((runtime_identity_payload or {}).get("identity") or {}).get("app_env")) or "unknown"
        role = _classify_role(request)

        # Detail event (TTL-expired after 30 days).
        await db[ALIAS_EVENTS_COLL].insert_one({
            "at": now,
            "path": path,
            "method": method,
            "route_key": route_key,
            "role": role,
            "env": env,
            "ip": (request.client.host if request.client else None),
            "user_agent": (request.headers.get("User-Agent") or "")[:200] or None,
            "request_id": (request.headers.get("X-Request-Id") or "")[:120] or None,
        })

        # Aggregate upsert (permanent until DR-UNIFY-005).
        await db[ALIAS_AGGREGATE_COLL].update_one(
            {"route_key": route_key},
            {
                "$setOnInsert": {
                    "route_key": route_key,
                    "path": path,
                    "method": method,
                    "first_observed_at": now,
                    "retirement_recommendation": "SAFE_TO_RETIRE",
                },
                "$set": {
                    "last_observed_at": now,
                    "last_role": role,
                    "last_env": env,
                },
                "$inc": {"lifetime_hits": 1},
            },
            upsert=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"[dr-v2 alias track] swallowed: {exc}")


def _retirement_recommendation(agg_row: Dict[str, Any]) -> str:
    """Compute a rolling recommendation from aggregate stats.

    Rules:
      • Never seen in production env → SAFE_TO_RETIRE
      • Only anonymous or bearer hits → SAFE_TO_RETIRE
      • Last hit older than 30 days → SAFE_TO_RETIRE
      • Otherwise → REVIEW_BEFORE_RETIRE
    """
    last = agg_row.get("last_observed_at")
    if isinstance(last, datetime):
        age = (_now() - last).total_seconds()
        if age > DR_V2_ALIAS_TTL_DAYS * 24 * 60 * 60:
            return "SAFE_TO_RETIRE"
    role = (agg_row.get("last_role") or "").lower()
    env = (agg_row.get("last_env") or "").lower()
    if env in ("preview", "unknown", "test") and role in ("anonymous", "bearer"):
        return "SAFE_TO_RETIRE"
    return "REVIEW_BEFORE_RETIRE"


async def _dr_v2_alias_telemetry_payload(db, recent_limit: int = 50) -> Dict[str, Any]:
    aggregates: List[Dict[str, Any]] = []
    try:
        cursor = db[ALIAS_AGGREGATE_COLL].find({}, {"_id": 0}).sort("lifetime_hits", -1)
        async for doc in cursor:
            # Recompute recommendation dynamically so operators see the
            # freshest guidance without a background job.
            doc["retirement_recommendation"] = _retirement_recommendation(doc)
            for k in ("first_observed_at", "last_observed_at"):
                if isinstance(doc.get(k), datetime):
                    doc[k] = doc[k].isoformat()
            aggregates.append(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[dr-v2 alias aggregate read] {exc}")

    recent: List[Dict[str, Any]] = []
    try:
        cursor = (
            db[ALIAS_EVENTS_COLL]
            .find({}, {"_id": 0})
            .sort("at", -1)
            .limit(max(1, min(500, recent_limit)))
        )
        async for doc in cursor:
            if isinstance(doc.get("at"), datetime):
                doc["at"] = doc["at"].isoformat()
            recent.append(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[dr-v2 alias events read] {exc}")

    total_hits = sum(a.get("lifetime_hits", 0) for a in aggregates)
    safe_to_retire = sum(
        1 for a in aggregates
        if a.get("retirement_recommendation") == "SAFE_TO_RETIRE"
    )
    return {
        "checked_at": _now_iso(),
        "ttl_days": DR_V2_ALIAS_TTL_DAYS,
        "route_count": len(aggregates),
        "lifetime_hits": total_hits,
        "safe_to_retire_count": safe_to_retire,
        "aggregates": aggregates,
        "recent": recent,
        "doctrine": (
            "Migration telemetry for /api/dr-v2/* aliases. Detail events "
            "auto-expire after 30 days. Aggregates persist until "
            "DR-UNIFY-005 formally removes the aliases, at which point "
            "both collections are retired."
        ),
    }


# ─────────────────── route registration ───────────────────────────

def register_integration_truth_routes(
    api_router: APIRouter,
    *,
    db,
    require_admin_strict,
    require_dispatch_or_admin=None,
    get_runtime_identity=None,
) -> None:
    """Attach TRACK 22.3 routes onto the shared API router.

    ``require_dispatch_or_admin`` is optional — when provided, we expose a
    dispatch-safe subset of the truth surface at ``/api/dispatch/motive-posture``
    so the Dispatch UI can render honest stale-data ribbons without needing
    an admin token (Track 22.4a).
    """

    @api_router.get("/admin/ai/keys/status")
    async def admin_ai_keys_status(_admin=Depends(require_admin_strict)):
        return await _ai_keys_status_payload()

    @api_router.get("/admin/integrations/truth-status")
    async def admin_integrations_truth(_admin=Depends(require_admin_strict)):
        runtime_identity = get_runtime_identity() if callable(get_runtime_identity) else None
        runtime_identity_payload = runtime_identity_public_payload(runtime_identity) if runtime_identity else None
        return await _integrations_truth_payload(db, runtime_identity_payload=runtime_identity_payload)

    @api_router.get("/admin/dr-v2-alias-telemetry")
    async def admin_dr_v2_alias_telemetry(
        recent_limit: int = Query(default=50, ge=1, le=500),
        _admin=Depends(require_admin_strict),
    ):
        return await _dr_v2_alias_telemetry_payload(db, recent_limit=recent_limit)

    # ── TRACK 22.4a · Dispatch-safe Motive posture ──────────────────
    # Same truth model as /admin/integrations/truth-status but scoped
    # to Motive-only and gated by dispatch OR admin. No secrets leak
    # (last-4 mask applied at row builder). Dispatch UI consumes this
    # to render the stale-data ribbon on /dispatch-portal/map.
    if require_dispatch_or_admin is not None:
        @api_router.get("/dispatch/motive-posture")
        async def dispatch_motive_posture(_=Depends(require_dispatch_or_admin)):
            row = await _motive_truth(db)
            # Only surface the fields dispatch needs. Drop admin-only
            # detail such as api_key_source.
            return {
                "checked_at": _now_iso(),
                "id": row["id"],
                "name": row["name"],
                "config_status": row["config_status"],
                "connectivity_status": row["connectivity_status"],
                "operational_status": row["operational_status"],
                "overall": row["overall"],
                "connectivity_detail": row.get("connectivity_detail"),
                "connectivity_latency_ms": row.get("connectivity_latency_ms"),
                "last_successful_sync_at": row.get("last_successful_sync_at"),
                "activity_age_seconds": row.get("activity_age_seconds"),
                "live_window_seconds": row.get("live_window_seconds"),
                "doctrine": (
                    "Dispatch-safe Motive posture. Never claims LIVE unless "
                    "operational_status is LIVE_VERIFIED. Use to render "
                    "stale-data ribbons in the Dispatch UI."
                ),
            }


__all__ = [
    "register_integration_truth_routes",
    "record_dr_v2_alias_hit",
    "ensure_dr_v2_alias_indexes",
    "ALIAS_EVENTS_COLL",
    "ALIAS_AGGREGATE_COLL",
]
