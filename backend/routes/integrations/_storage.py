"""
Shared storage helpers + index initialiser + demo data seed for the
Integration Center package.

Why centralised: every route module needs the same projection rules
(masked secrets, denormalised display names), the same constant lists
(statuses, providers), and the same demo-mode dataset. Keep them here so
the route modules stay short and pure.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

PROVIDERS = ("motive", "maintainx")

VALID_STATUSES = (
    "Not Connected",
    "Ready for Credentials",
    "Connected",
    "Syncing",
    "Error",
    "Disabled",
)

# ─── Public projection helpers ────────────────────────────────────────
SECRET_PUBLIC_FIELDS = {"_id": 0, "api_key_value": 0, "webhook_secret_value": 0}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mask_secret(value: Optional[str]) -> Optional[str]:
    """Show only the last 4 chars so admins can confirm the right
    credential is in place without exposing it."""
    if not value or not isinstance(value, str):
        return None
    if len(value) <= 4:
        return "•" * len(value)
    return "•" * (len(value) - 4) + value[-4:]


def settings_public_view(doc: dict) -> dict:
    if not doc:
        return {}
    return {
        "id": doc.get("id"),
        "provider": doc.get("provider"),
        "status": doc.get("status") or "Not Connected",
        "enabled": bool(doc.get("enabled")),
        "demo_mode": bool(doc.get("demo_mode")),
        "test_mode": bool(doc.get("test_mode")),
        "api_key_present": bool(doc.get("api_key_value")),
        "api_key_masked": mask_secret(doc.get("api_key_value")) if doc.get("api_key_value") else None,
        "webhook_secret_present": bool(doc.get("webhook_secret_value")),
        "webhook_secret_masked": mask_secret(doc.get("webhook_secret_value")) if doc.get("webhook_secret_value") else None,
        "webhook_url_path": doc.get("webhook_url_path"),
        "last_sync_at": doc.get("last_sync_at"),
        "last_successful_sync_at": doc.get("last_successful_sync_at"),
        "last_failed_sync_at": doc.get("last_failed_sync_at"),
        "last_sync_error": doc.get("last_sync_error"),
        "records_mapped": int(doc.get("records_mapped") or 0),
        "settings": doc.get("settings") or {},
        "notes": doc.get("notes") or "",
        "updated_at": doc.get("updated_at"),
        "updated_by": doc.get("updated_by") or "",
    }


# ─── Index + seed initialisation ──────────────────────────────────────
async def ensure_indexes_and_seed(db) -> None:
    """Called from server startup. Creates indexes + seeds default
    integration_settings docs for Motive + MaintainX so the Admin UI
    has something to render immediately."""
    try:
        await asyncio.gather(
            db.integration_settings.create_index("provider", unique=True),
            db.asset_mappings.create_index("masci_equipment_id", unique=False),
            db.asset_mappings.create_index("motive.vehicle_id"),
            db.asset_mappings.create_index("maintainx.asset_id"),
            db.employee_mappings.create_index("masci_employee_id", unique=False),
            db.employee_mappings.create_index("motive.driver_id"),
            db.employee_mappings.create_index("maintainx.user_id"),
            db.integration_sync_logs.create_index("started_at"),
            db.integration_sync_logs.create_index("integration"),
            db.integration_error_logs.create_index("occurred_at"),
            db.integration_error_logs.create_index("integration"),
            db.motive_events.create_index("event_at"),
            db.maintainx_work_orders.create_index("created_at"),
            db.integration_wizard_runs.create_index("started_at"),
            db.integration_wizard_runs.create_index("kind"),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[integrations-index] {e}")

    for provider in PROVIDERS:
        existing = await db.integration_settings.find_one({"provider": provider}, {"_id": 0, "id": 1})
        if existing:
            continue
        await db.integration_settings.insert_one({
            "id": str(uuid.uuid4()),
            "provider": provider,
            "status": "Not Connected",
            "enabled": False,
            "demo_mode": False,
            "test_mode": False,
            "api_key_value": "",
            "webhook_secret_value": "",
            "webhook_url_path": f"/api/integrations/{provider}/webhook",
            "last_sync_at": None,
            "last_successful_sync_at": None,
            "last_failed_sync_at": None,
            "last_sync_error": None,
            "records_mapped": 0,
            "settings": {},
            "notes": "",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "updated_by": "system",
        })
        logger.info(f"[integrations-seed] inserted default settings for {provider}")


# ─── Sync log helpers ─────────────────────────────────────────────────
async def write_sync_log(db, *, integration: str, sync_type: str, status: str,
                         triggered_by: str = "system",
                         records_created: int = 0, records_updated: int = 0,
                         records_skipped: int = 0, records_failed: int = 0,
                         error_message: Optional[str] = None, notes: str = "",
                         duration_ms: int = 0) -> str:
    log = {
        "id": str(uuid.uuid4()),
        "integration": integration,
        "sync_type": sync_type,
        "status": status,
        "started_at": now_iso(),
        "completed_at": now_iso(),
        "duration_ms": duration_ms,
        "records_created": records_created,
        "records_updated": records_updated,
        "records_skipped": records_skipped,
        "records_failed": records_failed,
        "error_message": error_message,
        "triggered_by": triggered_by,
        "environment": (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "production").strip(),
        "notes": notes,
    }
    await db.integration_sync_logs.insert_one(log)
    return log["id"]


async def write_error_log(db, *, integration: str, kind: str, message: str,
                          details: Optional[Dict[str, Any]] = None,
                          sync_log_id: Optional[str] = None) -> str:
    log = {
        "id": str(uuid.uuid4()),
        "integration": integration,
        "kind": kind,
        "message": message,
        "details": details or {},
        "occurred_at": now_iso(),
        "resolved": False,
        "sync_log_id": sync_log_id,
    }
    await db.integration_error_logs.insert_one(log)
    return log["id"]


# ─── Webhook signature stub ───────────────────────────────────────────
def verify_webhook_signature_stub(provider: str, secret: str,
                                  body: bytes, header_sig: Optional[str]) -> bool:
    """Placeholder signature verifier — real algo will be provided by
    Motive/MaintainX docs. For now: if no secret is configured, fail
    closed; if a secret is configured, compare against an HMAC-SHA256
    hex digest so the test-mode end-to-end works without surprise."""
    if not secret:
        return False
    if not header_sig:
        return False
    import hmac  # noqa: PLC0415
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_sig.strip().lower())


# ─── Demo dataset (admin demo-toggle) ─────────────────────────────────
# Static, deterministic mock records — generated at request-time when
# `integration_settings.demo_mode` is True so portals can show realistic
# cards in screenshots/presentations without polluting the real DB.
def demo_motive_events() -> List[Dict[str, Any]]:
    base = datetime.now(timezone.utc)
    return [
        {
            "id": "demo-mev-001",
            "event_type": "hard_braking",
            "severity": "high",
            "driver_name": "Alec Perkins",
            "unit_number": "Truck 12",
            "event_at": (base - timedelta(hours=3)).isoformat(),
            "location": {"address": "I-95 N, Mile 142"},
            "speed_mph": 64,
            "details": "Hard brake from 64 mph → 22 mph",
            "coaching_required": True,
            "safety_visible": True,
            "hr_visible": True,
            "is_demo": True,
        },
        {
            "id": "demo-mev-002",
            "event_type": "speeding",
            "severity": "medium",
            "driver_name": "Mike Hernandez",
            "unit_number": "Truck 7",
            "event_at": (base - timedelta(hours=18)).isoformat(),
            "location": {"address": "US-1 S near jobsite 220"},
            "speed_mph": 71,
            "details": "Sustained 71 mph in 55 zone for 0.8 mi",
            "coaching_required": False,
            "safety_visible": True,
            "is_demo": True,
        },
        {
            "id": "demo-mev-003",
            "event_type": "seatbelt_violation",
            "severity": "low",
            "driver_name": "Alec Perkins",
            "unit_number": "Truck 12",
            "event_at": (base - timedelta(days=2)).isoformat(),
            "location": {"address": "Shop yard"},
            "speed_mph": 6,
            "details": "Seat-belt unfastened during low-speed move",
            "coaching_required": True,
            "safety_visible": True,
            "hr_visible": True,
            "is_demo": True,
        },
    ]


def demo_maintainx_work_orders() -> List[Dict[str, Any]]:
    base = datetime.now(timezone.utc)
    return [
        {
            "id": "demo-wo-001",
            "wo_number": "WO-1023",
            "status": "Open",
            "priority": "high",
            "title": "Hydraulic leak — Excavator E-04",
            "unit_number": "E-04",
            "assigned_technician_name": "Tom Diesel",
            "created_at": (base - timedelta(hours=10)).isoformat(),
            "due_date": (base + timedelta(days=2)).isoformat()[:10],
            "source_system": "masci_preop",
            "safety_related": True,
            "equipment_down": True,
            "is_demo": True,
        },
        {
            "id": "demo-wo-002",
            "wo_number": "WO-1019",
            "status": "In Progress",
            "priority": "medium",
            "title": "250-hour PM service — Truck 12",
            "unit_number": "Truck 12",
            "assigned_technician_name": "Diego Rivera",
            "created_at": (base - timedelta(days=1)).isoformat(),
            "due_date": (base + timedelta(days=4)).isoformat()[:10],
            "source_system": "maintainx",
            "safety_related": False,
            "equipment_down": False,
            "is_demo": True,
        },
        {
            "id": "demo-wo-003",
            "wo_number": "WO-1017",
            "status": "Open",
            "priority": "critical",
            "title": "Brake inspection — failed pre-op",
            "unit_number": "Truck 7",
            "assigned_technician_name": "—",
            "created_at": (base - timedelta(days=3)).isoformat(),
            "due_date": (base - timedelta(days=1)).isoformat()[:10],   # overdue
            "source_system": "masci_preop",
            "safety_related": True,
            "equipment_down": True,
            "is_demo": True,
        },
    ]


# ─── Shared provider status (single source of truth for ALL health surfaces) ──
# Used by: routes/integration_health.py::_probe_motive,
#          routes/admin_ops.py::compute_system_health (Integrations card),
#          routes/platform_data_truth.py (integrations.motive section).
#
# Rule (per "P0 — MOTIVE HEALTH SURFACE CORRECTION"):
#   1. Check DB-backed integration_settings row first.
#   2. Fall back to env var(s) second.
#   3. NEVER report MOCKED if: enabled=true AND api_key present AND a successful sync exists.
async def compute_provider_status(
    db,
    provider: str,
    *,
    env_api_key_var: Optional[str] = None,
    recent_sync_window_minutes: int = 15,
) -> Dict[str, Any]:
    """Return a normalised status dict for a single integration provider.

    Output keys:
        provider                — "motive" | "maintainx" | ...
        enabled                 — bool   (settings.enabled)
        configured              — bool   (api key present anywhere — DB or env)
        api_key_present         — bool
        api_key_source          — "db" | "env" | None
        webhook_secret_present  — bool
        webhook_url_path        — str | None
        last_successful_sync_at — ISO str | None
        last_failed_sync_at     — ISO str | None
        last_sync_at            — ISO str | None
        last_sync_error         — str | None
        recent_sync_ok          — bool   (success within recent_sync_window_minutes)
        status                  — "ok" | "degraded" | "disabled"
        mocked                  — bool   (only true when nothing configured anywhere)
        message                 — human-readable summary
    """
    try:
        doc = await db.integration_settings.find_one(
            {"provider": provider}, {"_id": 0}
        ) or {}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[provider-status:{provider}] DB read failed: {e}")
        doc = {}

    db_api_key = (doc.get("api_key_value") or "").strip()
    env_api_key = ""
    if env_api_key_var:
        env_api_key = (os.environ.get(env_api_key_var) or "").strip()
    api_key_present = bool(db_api_key or env_api_key)
    api_key_source = "db" if db_api_key else ("env" if env_api_key else None)

    enabled = bool(doc.get("enabled"))
    webhook_secret_present = bool((doc.get("webhook_secret_value") or "").strip())
    webhook_url_path = doc.get("webhook_url_path")
    last_successful_sync_at = doc.get("last_successful_sync_at")
    last_failed_sync_at = doc.get("last_failed_sync_at")
    last_sync_at = doc.get("last_sync_at")
    last_sync_error = doc.get("last_sync_error")

    # Determine recency of last successful sync.
    recent_sync_ok = False
    if last_successful_sync_at:
        try:
            ts = datetime.fromisoformat(str(last_successful_sync_at).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - ts
            recent_sync_ok = delta.total_seconds() <= recent_sync_window_minutes * 60
        except Exception:  # noqa: BLE001
            recent_sync_ok = False

    # Status resolution.
    if not api_key_present and not enabled:
        status = "disabled"
        mocked = True
        message = f"Not configured — no api key in integration_settings.{provider} or env"
    elif enabled and api_key_present and recent_sync_ok:
        status = "ok"
        mocked = False
        message = (
            f"Live · enabled · synced {last_successful_sync_at}"
            + (" · webhook armed" if webhook_secret_present else " · webhook secret missing")
        )
    elif enabled and api_key_present:
        # Configured but no successful sync within the window.
        status = "degraded"
        mocked = False
        if last_failed_sync_at:
            message = f"Enabled but last sync FAILED at {last_failed_sync_at}: {last_sync_error or 'no detail'}"
        elif last_successful_sync_at:
            message = f"Enabled but last successful sync was stale ({last_successful_sync_at})"
        else:
            message = "Enabled with credentials but no sync yet — awaiting first poll"
    elif api_key_present and not enabled:
        status = "degraded"
        mocked = False
        message = "API key present but integration is disabled in settings"
    else:
        status = "disabled"
        mocked = True
        message = f"Not configured — no api key in integration_settings.{provider} or env"

    return {
        "provider":               provider,
        "enabled":                enabled,
        "configured":             api_key_present,
        "api_key_present":        api_key_present,
        "api_key_source":         api_key_source,
        "webhook_secret_present": webhook_secret_present,
        "webhook_url_path":       webhook_url_path,
        "last_successful_sync_at": last_successful_sync_at,
        "last_failed_sync_at":    last_failed_sync_at,
        "last_sync_at":           last_sync_at,
        "last_sync_error":        last_sync_error,
        "recent_sync_ok":         recent_sync_ok,
        "status":                 status,
        "mocked":                 mocked,
        "message":                message,
    }


__all__ = [
    "PROVIDERS",
    "VALID_STATUSES",
    "SECRET_PUBLIC_FIELDS",
    "now_iso",
    "mask_secret",
    "settings_public_view",
    "ensure_indexes_and_seed",
    "write_sync_log",
    "write_error_log",
    "verify_webhook_signature_stub",
    "compute_provider_status",
    "demo_motive_events",
    "demo_maintainx_work_orders",
]
