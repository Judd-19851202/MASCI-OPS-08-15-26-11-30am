"""
integration_health.py — Iter142 (Phase-1 Iter D). Unified integration
health probe surface. Each integration has a single async probe that
returns a normalized record:

    {
        "id":          "r2",
        "name":        "Cloudflare R2",
        "status":      "ok" | "degraded" | "down" | "disabled",
        "latency_ms":  120,
        "message":     "Bucket reachable",
        "checked_at":  ISO-8601 UTC,
    }

The /api/admin/integrations/health endpoint runs every probe in parallel
(asyncio.gather) and returns:

    {
        "overall_status": "ok" | "degraded" | "down",
        "checked_at":     ISO,
        "probes":         [ { ...probe payload... } ],
    }

Every probe is wrapped in a hard try/except + 5-second timeout so a
slow third-party CANNOT block the rest of the response. A failed probe
returns status="down" with the exception text — it NEVER raises.

Coverage:
  • R2 (Cloudflare object storage)         — live HEAD on the bucket
  • Resend (transactional email)           — API-key shape + presence
  • MaintainX (work-order sync)            — MOCKED — config-only check
  • Motive (telematics)                    — MOCKED — config-only check
  • Emergent LLM key (Universal Key)       — config-only check
  • MongoDB                                — ping
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)

# Cap every probe so a hung third-party can't block the dashboard.
PROBE_TIMEOUT_S = 5.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _result(probe_id: str, name: str, status: str, latency_ms: int,
            message: str, **extras) -> Dict[str, Any]:
    return {
        "id": probe_id, "name": name, "status": status,
        "latency_ms": latency_ms, "message": message,
        "checked_at": _now_iso(), **extras,
    }


# ──────────────────────────────────────────────────────────────────
# Individual probes
# ──────────────────────────────────────────────────────────────────
async def _probe_r2() -> Dict[str, Any]:
    t0 = time.monotonic()
    try:
        import safety_doc_storage as sds  # noqa: PLC0415
        if not sds.is_configured():
            return _result("r2", "Cloudflare R2", "disabled", 0,
                           "Not configured — uploads fall back to inline base64",
                           mocked=False)
        client = sds._client()  # noqa: SLF001
        if client is None:
            return _result("r2", "Cloudflare R2", "down",
                           int((time.monotonic() - t0) * 1000),
                           "Client init failed (see backend logs)")
        bucket = sds._bucket()  # noqa: SLF001
        # head_bucket is the cheapest reachability probe; run off-thread
        # so we don't block the event loop on boto3's sync stack.
        await asyncio.to_thread(client.head_bucket, Bucket=bucket)
        return _result("r2", "Cloudflare R2", "ok",
                       int((time.monotonic() - t0) * 1000),
                       f"Bucket `{bucket}` reachable")
    except Exception as e:  # noqa: BLE001
        return _result("r2", "Cloudflare R2", "down",
                       int((time.monotonic() - t0) * 1000),
                       f"Probe failed: {str(e)[:160]}")


async def _probe_resend() -> Dict[str, Any]:
    t0 = time.monotonic()
    key = os.environ.get("RESEND_API_KEY", "").strip()
    auto = (os.environ.get("AUTO_EMAIL_REPORTS", "false") or "").lower() == "true"
    if not key:
        return _result("resend", "Resend Email", "disabled", 0,
                       "RESEND_API_KEY missing — password reset emails will not fire",
                       auto_email_enabled=auto)
    if not key.startswith("re_"):
        return _result("resend", "Resend Email", "degraded",
                       int((time.monotonic() - t0) * 1000),
                       "API key present but does not match `re_…` shape — verify rotation",
                       auto_email_enabled=auto)
    return _result("resend", "Resend Email", "ok",
                   int((time.monotonic() - t0) * 1000),
                   "Key present" + (" · auto-email ON" if auto else " · auto-email OFF"),
                   auto_email_enabled=auto)


async def _probe_maintainx() -> Dict[str, Any]:
    """MOCKED integration — config-only check."""
    api_key = os.environ.get("MAINTAINX_API_KEY", "").strip()
    base = os.environ.get("MAINTAINX_BASE_URL", "").strip()
    if not (api_key and base):
        return _result("maintainx", "MaintainX (Work Orders)", "disabled", 0,
                       "MOCKED — live API not configured; events surfaced via operations_events",
                       mocked=True)
    return _result("maintainx", "MaintainX (Work Orders)", "ok", 0,
                   "Configured (live probe not yet implemented)",
                   mocked=True)


async def _probe_motive(db) -> Dict[str, Any]:
    """Single source of truth for Motive health.

    Uses `compute_provider_status(db, "motive", env_api_key_var="MOTIVE_API_KEY")`
    so this probe matches what the active Motive sync service is actually doing
    (services/motive_service.py reads `integration_settings.motive.api_key_value`
    first, env second). Never reports MOCKED when the integration is enabled with
    credentials and a successful sync exists.

    When the DB shows no recent successful sync, fall back to a live ping against
    `/v1/users/me` so we don't mark an enabled-but-fresh deploy as `degraded`
    purely on timing.
    """
    from routes.integrations._storage import compute_provider_status  # noqa: PLC0415

    snap = await compute_provider_status(
        db, "motive", env_api_key_var="MOTIVE_API_KEY",
    )

    # Fully unconfigured → mocked, as before.
    if snap["status"] == "disabled" and not snap["api_key_present"]:
        return _result("motive", "Motive (Telematics)", "disabled", 0,
                       snap["message"], mocked=True,
                       last_successful_sync_at=snap["last_successful_sync_at"],
                       webhook_secret_present=snap["webhook_secret_present"])

    # Configured + enabled + recent sync → ok (no live ping needed; the sync
    # service is already pinging Motive every minute).
    if snap["status"] == "ok":
        return _result("motive", "Motive (Telematics)", "ok", 0,
                       snap["message"], mocked=False,
                       last_successful_sync_at=snap["last_successful_sync_at"],
                       webhook_secret_present=snap["webhook_secret_present"],
                       api_key_source=snap["api_key_source"])

    # Configured but no recent successful sync — do a live ping to disambiguate
    # "just deployed, sync hasn't fired yet" from "Motive is rejecting our key".
    api_key = ""
    try:
        doc = await db.integration_settings.find_one({"provider": "motive"}, {"_id": 0}) or {}
        api_key = (doc.get("api_key_value") or "").strip() or os.environ.get("MOTIVE_API_KEY", "").strip()
    except Exception:  # noqa: BLE001
        api_key = os.environ.get("MOTIVE_API_KEY", "").strip()

    if not api_key:
        return _result("motive", "Motive (Telematics)", snap["status"], 0,
                       snap["message"], mocked=snap["mocked"],
                       last_successful_sync_at=snap["last_successful_sync_at"],
                       webhook_secret_present=snap["webhook_secret_present"])

    base_url = os.environ.get("MOTIVE_BASE_URL", "https://api.gomotive.com").rstrip("/")
    t0 = time.monotonic()
    try:
        import httpx  # noqa: PLC0415
        async with httpx.AsyncClient(timeout=4.0) as c:
            r = await c.get(
                f"{base_url}/v1/users/me",
                headers={"X-Api-Key": api_key, "Accept": "application/json"},
            )
        latency_ms = int((time.monotonic() - t0) * 1000)
        if r.status_code == 200:
            return _result("motive", "Motive (Telematics)", "ok", latency_ms,
                           f"Live · HTTP 200 · {latency_ms}ms (no recent sync yet)",
                           mocked=False,
                           last_successful_sync_at=snap["last_successful_sync_at"],
                           webhook_secret_present=snap["webhook_secret_present"],
                           api_key_source=snap["api_key_source"])
        if r.status_code in (401, 403):
            return _result("motive", "Motive (Telematics)", "degraded", latency_ms,
                           f"API key rejected (HTTP {r.status_code}) — check key scope",
                           mocked=False,
                           webhook_secret_present=snap["webhook_secret_present"])
        return _result("motive", "Motive (Telematics)", "degraded", latency_ms,
                       f"Unexpected HTTP {r.status_code} from /v1/users/me",
                       mocked=False,
                       webhook_secret_present=snap["webhook_secret_present"])
    except Exception as e:  # noqa: BLE001
        latency_ms = int((time.monotonic() - t0) * 1000)
        return _result("motive", "Motive (Telematics)", "degraded", latency_ms,
                       f"Live probe error: {type(e).__name__}: {str(e)[:120]} · "
                       f"last_success={snap['last_successful_sync_at']}",
                       mocked=False,
                       webhook_secret_present=snap["webhook_secret_present"])


async def _probe_emergent_llm() -> Dict[str, Any]:
    key = os.environ.get("EMERGENT_LLM_KEY", "").strip()
    if not key:
        return _result("emergent_llm", "Emergent Universal LLM Key", "disabled", 0,
                       "EMERGENT_LLM_KEY missing — translate/LLM features off")
    if not key.startswith("sk-emergent-"):
        return _result("emergent_llm", "Emergent Universal LLM Key", "degraded", 0,
                       "Key present but unexpected prefix")
    return _result("emergent_llm", "Emergent Universal LLM Key", "ok", 0,
                   "Key present (universal — OpenAI/Anthropic/Gemini)")


async def _probe_mongo(db) -> Dict[str, Any]:
    t0 = time.monotonic()
    try:
        await db.command("ping")
        return _result("mongo", "MongoDB", "ok",
                       int((time.monotonic() - t0) * 1000),
                       "Ping OK")
    except Exception as e:  # noqa: BLE001
        return _result("mongo", "MongoDB", "down",
                       int((time.monotonic() - t0) * 1000),
                       f"Ping failed: {str(e)[:160]}")


# ──────────────────────────────────────────────────────────────────
# Aggregation
# ──────────────────────────────────────────────────────────────────
def _overall(probes: List[Dict[str, Any]]) -> str:
    statuses = [p["status"] for p in probes]
    if any(s == "down" for s in statuses):
        return "down"
    if any(s == "degraded" for s in statuses):
        return "degraded"
    return "ok"


async def _run_with_timeout(coro, fallback_id: str, fallback_name: str):
    """Wrap a probe in a 5s timeout. On timeout/exception, return a
    `down` result instead of raising — the dashboard MUST always render."""
    try:
        return await asyncio.wait_for(coro, timeout=PROBE_TIMEOUT_S)
    except asyncio.TimeoutError:
        return _result(fallback_id, fallback_name, "down",
                       int(PROBE_TIMEOUT_S * 1000),
                       f"Probe exceeded {PROBE_TIMEOUT_S}s timeout")
    except Exception as e:  # noqa: BLE001
        return _result(fallback_id, fallback_name, "down", 0,
                       f"Probe crashed: {str(e)[:160]}")


async def run_all_probes(db) -> Dict[str, Any]:
    """Public entrypoint — used by both the admin endpoint and the
    deploy-readiness rollup."""
    probes = await asyncio.gather(
        _run_with_timeout(_probe_mongo(db),          "mongo",        "MongoDB"),
        _run_with_timeout(_probe_r2(),               "r2",           "Cloudflare R2"),
        _run_with_timeout(_probe_resend(),           "resend",       "Resend Email"),
        _run_with_timeout(_probe_maintainx(),        "maintainx",    "MaintainX"),
        _run_with_timeout(_probe_motive(db),         "motive",       "Motive"),
        _run_with_timeout(_probe_emergent_llm(),     "emergent_llm", "Emergent LLM"),
    )
    # Track 14.0-I1 (2026-02-14): annotate every probe with the
    # platform-standard honesty status vocabulary
    # (LIVE / CONFIGURED / PARTIAL / DISCONNECTED / ERROR).
    # We never overwrite the raw probe status — the UI can show both.
    for p in probes:
        p["honesty_status"] = _normalize_honesty_status(p)
    return {
        "overall_status": _overall(probes),
        "checked_at":     _now_iso(),
        "probes":         probes,
    }


def _normalize_honesty_status(probe: Dict[str, Any]) -> str:
    """Map raw probe state → platform honesty vocabulary.

    LIVE         — credentials present + recent successful comm + real data.
    CONFIGURED   — credentials present but no recent success proven yet.
    PARTIAL      — some functionality works, some does not.
    DISCONNECTED — supported integration with no credentials.
    ERROR        — configured but failing validation / communication.
    """
    raw_status = (probe.get("status") or "").lower()
    mocked = bool(probe.get("mocked"))
    api_key_present = probe.get("api_key_present")
    # Motive uses `webhook_secret_present` as its credential signal.
    if api_key_present is None and probe.get("webhook_secret_present") is not None:
        api_key_present = probe.get("webhook_secret_present")
    # Probes that don't expose api_key_present (mongo, r2, emergent_llm)
    # imply presence from a successful `ok` status.
    if api_key_present is None:
        api_key_present = raw_status == "ok"

    if mocked:
        # `disabled` + `mocked=true` (e.g. MaintainX) = explicitly not connected.
        return "DISCONNECTED"
    if raw_status == "ok":
        return "LIVE"
    if raw_status == "disabled":
        # Disabled-but-credentials-present = CONFIGURED awaiting proof.
        return "CONFIGURED" if api_key_present else "DISCONNECTED"
    if raw_status == "degraded":
        return "PARTIAL" if api_key_present else "ERROR"
    if raw_status == "down":
        return "ERROR"
    return "ERROR"


# ──────────────────────────────────────────────────────────────────
# Alert hook — append-only, log-only for now. iter142 deferred wiring
# to email/Slack until those integrations are formally adopted.
# ──────────────────────────────────────────────────────────────────
async def maybe_emit_alerts(db, payload: Dict[str, Any]) -> int:
    """For every non-ok probe, write one row to db.alert_events.
    Idempotent: only emits if the LAST stored event for this probe
    has a different status — prevents duplicate noise on every
    dashboard refresh."""
    written = 0
    for p in payload.get("probes", []):
        # `disabled` is INTENTIONAL config — only alert on degraded/down.
        if p["status"] in ("ok", "disabled"):
            continue
        last = await db.alert_events.find_one(
            {"probe_id": p["id"]},
            sort=[("at", -1)],
            projection={"_id": 0, "status": 1},
        )
        if last and last.get("status") == p["status"]:
            continue
        await db.alert_events.insert_one({
            "id":         f"alert-{p['id']}-{int(time.time())}",
            "probe_id":   p["id"],
            "name":       p["name"],
            "status":     p["status"],
            "message":    p["message"],
            "at":         datetime.now(timezone.utc),
            "severity":   "high" if p["status"] == "down" else "warn",
            "channel":    "log_only",
        })
        logger.warning(f"[alert] {p['id']} → {p['status']}: {p['message']}")
        written += 1
    return written


def build_integration_health_router(db, require_admin: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/admin", tags=["admin-integrations"])

    @router.get("/integrations/health", dependencies=[Depends(require_admin)])
    async def integrations_health(emit_alerts: bool = False):
        payload = await run_all_probes(db)
        if emit_alerts:
            payload["alerts_emitted"] = await maybe_emit_alerts(db, payload)
        return payload

    @router.get("/integrations/alerts", dependencies=[Depends(require_admin)])
    async def list_alerts(limit: int = 50):
        rows = []
        async for d in db.alert_events.find({}, {"_id": 0}).sort("at", -1).limit(limit):
            if isinstance(d.get("at"), datetime):
                d["at"] = d["at"].isoformat()
            rows.append(d)
        return {"rows": rows, "count": len(rows)}

    return router


async def ensure_alert_indexes(db) -> None:
    """TTL on alert_events — keep 90 days."""
    try:
        await db.alert_events.create_index([("at", 1)], expireAfterSeconds=60 * 60 * 24 * 90)
        await db.alert_events.create_index([("probe_id", 1), ("at", -1)])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[alert-events] index ensure failed: {e}")


__all__ = ["run_all_probes", "maybe_emit_alerts",
           "build_integration_health_router", "ensure_alert_indexes"]
