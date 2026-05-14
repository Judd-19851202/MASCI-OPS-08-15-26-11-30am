"""
Motive service stub — placeholder methods that return safe responses
until real Motive API docs + credentials are confirmed by MASCI.

Every method here is intentionally a no-op for production sync
behaviour. The shapes are stable so the routing layer can call them
TODAY and still get well-formed responses (status="awaiting_credentials"
etc.) without crashing the platform.

When the Motive API contract is finalised:
  • Replace each method body with real httpx calls to Motive
  • Re-use the existing routing layer + signature verifier
  • Promote `test_connection` to a real ping
  • Wire `process_webhook` to the real event router
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROVIDER = "motive"


class MotiveService:
    """All methods are async to give the router a stable contract
    regardless of whether the eventual SDK is sync or async."""

    def __init__(self, db, settings_doc: Optional[dict] = None):
        self.db = db
        self.settings = settings_doc or {}

    @property
    def is_live(self) -> bool:
        return bool(self.settings.get("enabled") and self.settings.get("api_key_value"))

    @property
    def is_demo(self) -> bool:
        return bool(self.settings.get("demo_mode"))

    # ── Live API methods (all stubs until creds confirmed) ───────────
    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_live:
            return {
                "ok": False,
                "status": "awaiting_credentials",
                "message": "Motive credentials not configured yet.",
            }
        # TODO(motive-api): replace with real ping endpoint
        return {"ok": True, "status": "stub_live", "message": "Stub — real Motive API not wired yet."}

    async def sync_assets(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_assets")

    async def sync_users(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_users")

    async def sync_events(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        return _stub_sync_result("sync_events")

    async def process_webhook(self, *, raw_body: bytes, headers: Dict[str, str],
                              test_mode: bool = False) -> Dict[str, Any]:
        """Webhook intake. In test mode we log the payload and return
        ok=true. In production mode we require valid signature; with
        no credentials we return 503-safe response without raising."""
        if not self.is_live and not test_mode:
            return {
                "ok": False,
                "status": "awaiting_credentials",
                "stored": False,
                "message": "Motive integration disabled or credentials missing.",
            }
        # TODO(motive-api): route by event type, persist motive_events,
        # link to asset/employee mappings, create corrective action if
        # safety-critical, broadcast to Safety Portal.
        logger.info(f"[motive-webhook] received {len(raw_body)} bytes (stub) test_mode={test_mode}")
        return {"ok": True, "status": "logged_stub", "stored": False, "bytes": len(raw_body)}

    async def create_corrective_action_from_event(self, motive_event_id: str) -> Dict[str, Any]:
        # TODO(motive-api): build CA from event payload + mapping
        return {"ok": False, "status": "stub", "message": "Will be wired with API."}


def _stub_sync_result(op: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "status": "awaiting_credentials",
        "operation": op,
        "records_created": 0,
        "records_updated": 0,
        "message": f"{op} stub — Motive API not wired yet.",
    }


__all__ = ["MotiveService", "PROVIDER"]
