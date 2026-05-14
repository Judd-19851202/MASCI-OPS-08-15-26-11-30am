"""
MaintainX service stub — placeholder methods that return safe responses
until real MaintainX API docs + credentials are confirmed by MASCI.

Same architecture as `motive_service.py` — stable contract today,
hot-swap to real httpx calls when the API is wired.
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

PROVIDER = "maintainx"


class MaintainxService:
    def __init__(self, db, settings_doc: Optional[dict] = None):
        self.db = db
        self.settings = settings_doc or {}

    @property
    def is_live(self) -> bool:
        return bool(self.settings.get("enabled") and self.settings.get("api_key_value"))

    @property
    def is_demo(self) -> bool:
        return bool(self.settings.get("demo_mode"))

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_live:
            return {
                "ok": False,
                "status": "awaiting_credentials",
                "message": "MaintainX credentials not configured yet.",
            }
        return {"ok": True, "status": "stub_live", "message": "Stub — real MaintainX API not wired yet."}

    async def sync_assets(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_assets")

    async def sync_users(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_users")

    async def sync_work_orders(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_work_orders")

    async def process_webhook(self, *, raw_body: bytes, headers: Dict[str, str],
                              test_mode: bool = False) -> Dict[str, Any]:
        if not self.is_live and not test_mode:
            return {
                "ok": False,
                "status": "awaiting_credentials",
                "stored": False,
                "message": "MaintainX integration disabled or credentials missing.",
            }
        logger.info(f"[maintainx-webhook] received {len(raw_body)} bytes (stub) test_mode={test_mode}")
        return {"ok": True, "status": "logged_stub", "stored": False, "bytes": len(raw_body)}

    async def create_work_order_from_failed_preop(self, preop_id: str) -> Dict[str, Any]:
        # TODO(maintainx-api): build WO from failed pre-op payload + asset mapping
        return {"ok": False, "status": "stub", "message": "Will be wired with API."}

    async def create_work_order_from_damage_report(self, damage_id: str) -> Dict[str, Any]:
        return {"ok": False, "status": "stub", "message": "Will be wired with API."}


def _stub_sync_result(op: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "status": "awaiting_credentials",
        "operation": op,
        "records_created": 0,
        "records_updated": 0,
        "message": f"{op} stub — MaintainX API not wired yet.",
    }


__all__ = ["MaintainxService", "PROVIDER"]
