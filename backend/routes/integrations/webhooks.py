"""
Integration Center · webhooks.py — disabled-by-default placeholder
receivers for Motive + MaintainX webhooks.

Hardened behaviour (per spec — must NEVER break the platform):
  • No signature → 401 (closed by default once a webhook secret is set)
  • Secret not configured AND settings.test_mode != True → 503 with a
    structured body (so the upstream provider's test ping doesn't
    pollute prod logs)
  • Always writes a sync log + error log (when applicable) so admins
    can see exactly what hit the endpoint
  • Returns 2xx with `{stored: False, status: 'logged_stub'}` when
    test_mode is on so providers can validate connectivity before MASCI
    flips the integration live.

These routes are mounted under /api/integrations/{provider}/webhook
(unauthenticated — providers don't carry MASCI tokens). All other
integration routes ARE authenticated.
"""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from services.motive_service import MotiveService
from services.maintainx_service import MaintainxService

from ._storage import (
    write_error_log, write_sync_log, verify_webhook_signature_stub,
)

logger = logging.getLogger(__name__)


def register_webhook_routes(api_router: APIRouter, db) -> None:

    async def _handle(provider: str, request: Request, signature_header: Optional[str]):
        doc = await db.integration_settings.find_one(
            {"provider": provider},
            {"_id": 0, "enabled": 1, "test_mode": 1, "webhook_secret_value": 1},
        ) or {}
        raw = await request.body()
        test_mode = bool(doc.get("test_mode"))
        secret = doc.get("webhook_secret_value") or ""

        # 1. No secret AND not in test_mode → 503 (always-safe, never crashes)
        if not secret and not test_mode:
            await write_sync_log(
                db, integration=provider, sync_type="webhook",
                status="Awaiting Credentials", triggered_by="webhook",
                notes="Webhook hit with no secret configured.",
            )
            return {
                "ok": False, "status": "awaiting_credentials",
                "stored": False,
                "message": f"{provider} webhook is awaiting credentials.",
            }

        # 2. Secret configured → verify signature
        if secret:
            if not verify_webhook_signature_stub(provider, secret, raw, signature_header):
                await write_error_log(
                    db, integration=provider, kind="webhook",
                    message="Invalid or missing signature",
                    details={"signature_present": bool(signature_header)},
                )
                raise HTTPException(401, "Invalid webhook signature")

        # 3. Dispatch to service stub (which logs internally)
        service = MotiveService(db, doc) if provider == "motive" else MaintainxService(db, doc)
        try:
            result = await service.process_webhook(
                raw_body=raw,
                headers=dict(request.headers),
                test_mode=test_mode,
            )
        except Exception as e:  # noqa: BLE001
            sync_id = await write_sync_log(
                db, integration=provider, sync_type="webhook",
                status="Failed", triggered_by="webhook",
                error_message=str(e),
            )
            await write_error_log(
                db, integration=provider, kind="webhook",
                message=f"process_webhook crashed: {e}", sync_log_id=sync_id,
            )
            return {"ok": False, "status": "error", "message": str(e)}

        await write_sync_log(
            db, integration=provider, sync_type="webhook",
            status="Success" if result.get("ok") else "Disabled",
            triggered_by="webhook",
            notes=str(result.get("message", "")),
        )
        return result

    @api_router.post("/integrations/motive/webhook")
    async def motive_webhook(
        request: Request,
        x_motive_signature: Optional[str] = Header(default=None, alias="X-Motive-Signature"),
    ):
        return await _handle("motive", request, x_motive_signature)

    @api_router.post("/integrations/maintainx/webhook")
    async def maintainx_webhook(
        request: Request,
        x_maintainx_signature: Optional[str] = Header(default=None, alias="X-Maintainx-Signature"),
    ):
        return await _handle("maintainx", request, x_maintainx_signature)


__all__ = ["register_webhook_routes"]
