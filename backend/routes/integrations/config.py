"""
Integration Center · config.py — admin settings + cross-portal health.

Endpoints:
  GET    /api/admin/integrations/overview        — both providers at once
  GET    /api/admin/integrations/{provider}      — single provider settings
  PATCH  /api/admin/integrations/{provider}      — update settings (secrets accepted, masked on read)
  POST   /api/admin/integrations/{provider}/test — call service.test_connection()
  GET    /api/integrations/health                — public-to-portals integration health card payload
                                                   (accepts Safety, HR, or Admin token via the safety
                                                   portal's multi-role gate)
"""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from services.motive_service import MotiveService
from services.maintainx_service import MaintainxService

from ._credential_alerts import mark_resolved as _resolve_credential_missing
from ._models import IntegrationSettingsUpdate
from ._storage import (
    PROVIDERS,
    VALID_STATUSES,
    now_iso,
    settings_public_view,
    write_error_log,
)

logger = logging.getLogger(__name__)


def _service_for(db, provider: str, settings_doc: Optional[dict]):
    if provider == "motive":
        return MotiveService(db, settings_doc)
    if provider == "maintainx":
        return MaintainxService(db, settings_doc)
    raise HTTPException(404, f"Unknown provider: {provider}")


def register_config_routes(
    api_router: APIRouter, db, require_admin, require_safety_or_hr_or_admin,
) -> None:

    @api_router.get("/admin/integrations/overview", dependencies=[Depends(require_admin)])
    async def admin_integration_overview():
        docs = await db.integration_settings.find({}, {"_id": 0}).to_list(20)
        by_provider = {d["provider"]: d for d in docs}
        return {
            "providers": [settings_public_view(by_provider.get(p, {})) for p in PROVIDERS],
            "valid_statuses": list(VALID_STATUSES),
        }

    @api_router.get(
        "/admin/integrations/{provider}", dependencies=[Depends(require_admin)],
    )
    async def admin_integration_settings_get(provider: str):
        if provider not in PROVIDERS:
            raise HTTPException(404, "Unknown provider")
        doc = await db.integration_settings.find_one({"provider": provider}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Settings not found")
        return settings_public_view(doc)

    @api_router.patch(
        "/admin/integrations/{provider}", dependencies=[Depends(require_admin)],
    )
    async def admin_integration_settings_update(provider: str, body: IntegrationSettingsUpdate):
        if provider not in PROVIDERS:
            raise HTTPException(404, "Unknown provider")
        update: dict = {"updated_at": now_iso()}
        # Booleans
        if body.enabled is not None:
            update["enabled"] = bool(body.enabled)
        if body.demo_mode is not None:
            update["demo_mode"] = bool(body.demo_mode)
        # Secret writes — never echoed back
        if body.api_key is not None:
            update["api_key_value"] = body.api_key.strip()
        if body.webhook_secret is not None:
            update["webhook_secret_value"] = body.webhook_secret.strip()
        # Free-form
        if body.settings is not None:
            update["settings"] = body.settings
        if body.notes is not None:
            update["notes"] = body.notes.strip()
        # Re-derive status from {enabled, api_key, demo_mode}
        existing = await db.integration_settings.find_one({"provider": provider}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Settings not found")
        merged = {**existing, **update}
        if merged.get("enabled") and merged.get("api_key_value"):
            update["status"] = "Connected"
        elif merged.get("enabled"):
            update["status"] = "Ready for Credentials"
        elif merged.get("demo_mode"):
            update["status"] = "Disabled"
        else:
            update["status"] = "Not Connected"
        res = await db.integration_settings.update_one({"provider": provider}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Settings not found")
        doc = await db.integration_settings.find_one({"provider": provider}, {"_id": 0})
        # MOTIVE-PROD-INCIDENT-001 · auto-resolve any open credential_missing
        # incident for this provider when a secret is now present.
        if (doc or {}).get("webhook_secret_value") or (doc or {}).get("api_key_value"):
            try:
                await _resolve_credential_missing(db, provider=provider, resolved_by="operator")
            except Exception:  # noqa: BLE001
                pass
        return settings_public_view(doc)

    @api_router.post(
        "/admin/integrations/{provider}/test", dependencies=[Depends(require_admin)],
    )
    async def admin_integration_test_connection(provider: str):
        if provider not in PROVIDERS:
            raise HTTPException(404, "Unknown provider")
        doc = await db.integration_settings.find_one({"provider": provider}, {"_id": 0})
        svc = _service_for(db, provider, doc)
        try:
            return await svc.test_connection()
        except Exception as e:  # noqa: BLE001
            await write_error_log(db, integration=provider, kind="api",
                                  message=f"test_connection raised: {e}")
            return {"ok": False, "status": "error", "message": str(e)}

    # ── M-1 · Manual sync triggers (Motive only — Maintainx has its own) ──
    async def _run_sync(provider: str, op: str):
        if provider not in PROVIDERS:
            raise HTTPException(404, "Unknown provider")
        doc = await db.integration_settings.find_one({"provider": provider}, {"_id": 0})
        svc = _service_for(db, provider, doc)
        method = getattr(svc, op, None)
        if method is None:
            raise HTTPException(400, f"Operation {op} not supported by {provider}")
        try:
            return await method(triggered_by="admin")
        except Exception as e:  # noqa: BLE001
            await write_error_log(db, integration=provider, kind="api",
                                  message=f"{op} raised: {e}")
            return {"ok": False, "status": "error", "message": str(e)}

    @api_router.post(
        "/admin/integrations/{provider}/sync-assets",
        dependencies=[Depends(require_admin)],
    )
    async def admin_integration_sync_assets(provider: str):
        return await _run_sync(provider, "sync_assets")

    @api_router.post(
        "/admin/integrations/{provider}/sync-users",
        dependencies=[Depends(require_admin)],
    )
    async def admin_integration_sync_users(provider: str):
        return await _run_sync(provider, "sync_users")

    @api_router.post(
        "/admin/integrations/{provider}/sync-geofences",
        dependencies=[Depends(require_admin)],
    )
    async def admin_integration_sync_geofences(provider: str):
        return await _run_sync(provider, "sync_geofences")

    @api_router.post(
        "/admin/integrations/{provider}/sync-events",
        dependencies=[Depends(require_admin)],
    )
    async def admin_integration_sync_events(provider: str):
        return await _run_sync(provider, "sync_events")

    # ── Public-to-portals (Safety/HR/Admin) health card ─────────────
    @api_router.get(
        "/integrations/health", dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def integration_health_card():
        docs = await db.integration_settings.find({}, {"_id": 0}).to_list(20)
        by = {d["provider"]: settings_public_view(d) for d in docs}
        # Counts for the cross-portal "what's mapped?" card
        try:
            asset_total = await db.asset_mappings.count_documents({})
            asset_mapped = await db.asset_mappings.count_documents({
                "$or": [{"motive.vehicle_id": {"$ne": ""}}, {"maintainx.asset_id": {"$ne": ""}}]
            })
            employee_total = await db.employee_mappings.count_documents({})
            employee_mapped = await db.employee_mappings.count_documents({
                "$or": [{"motive.driver_id": {"$ne": ""}}, {"maintainx.user_id": {"$ne": ""}}]
            })
        except Exception:  # noqa: BLE001
            asset_total = asset_mapped = employee_total = employee_mapped = 0
        return {
            "motive": by.get("motive", {"status": "Not Connected"}),
            "maintainx": by.get("maintainx", {"status": "Not Connected"}),
            "counts": {
                "asset_mappings_total": asset_total,
                "asset_mappings_mapped": asset_mapped,
                "employee_mappings_total": employee_total,
                "employee_mappings_mapped": employee_mapped,
            },
        }


__all__ = ["register_config_routes"]
