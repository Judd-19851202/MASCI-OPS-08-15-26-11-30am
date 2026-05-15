"""
admin_digest_config.py — iter133. Admin-only endpoints to view, edit,
and manually trigger the Weekly Safety Digest. The scheduler loop in
safety_digest.py reads DB overrides (if any) before falling back to env.

Routes (admin gate):
  GET  /api/admin/digest-settings     — read current config + last-run summary
  PATCH /api/admin/digest-settings    — update recipients / schedule / enabled
  POST /api/admin/digest-settings/send-now — trigger a manual send

Schema (single doc, key="safety"):
  {
    "key": "safety",
    "enabled": true,
    "recipients": ["safety@mascigc.com"],
    "weekday": 0,                  # 0=Mon..6=Sun
    "hour_utc": 14,
    "dashboard_url": "https://mascidocs.com/safety-portal",
    "updated_at": "ISO",
    "updated_by": "actor email"
  }
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DigestSettings(BaseModel):
    enabled: Optional[bool] = None
    recipients: Optional[List[str]] = Field(default=None, max_length=20)
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    hour_utc: Optional[int] = Field(default=None, ge=0, le=23)
    dashboard_url: Optional[str] = None


def build_admin_digest_router(
    db,
    require_admin: Callable,
    build_payload: Callable,
    render_html: Callable,
    send_email_fn: Optional[Callable] = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/admin/digest-settings", tags=["admin-digest"])

    async def _current() -> dict:
        doc = await db.digest_settings.find_one({"key": "safety"}, {"_id": 0}) or {}
        defaults = {
            "key": "safety",
            "enabled": (os.environ.get("SAFETY_DIGEST_ENABLED") or "true").lower() in ("1", "true", "yes", "on"),
            "recipients": [
                (os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com").strip(),
            ],
            "weekday": int(os.environ.get("SAFETY_DIGEST_WEEKDAY") or "0"),
            "hour_utc": int(os.environ.get("SAFETY_DIGEST_HOUR_UTC") or "14"),
            "dashboard_url": (
                os.environ.get("DEPLOY_PUBLIC_URL", "https://mascidocs.com").rstrip("/")
                + "/safety-portal"
            ),
        }
        # DB values override defaults
        for k, v in (doc or {}).items():
            if v is not None:
                defaults[k] = v
        # Latest send run if recorded
        last_run = await db.digest_runs.find_one(
            {}, {"_id": 0}, sort=[("at", -1)],
        )
        defaults["last_run"] = last_run or None
        return defaults

    @router.get("", dependencies=[Depends(require_admin)])
    async def get_digest_settings():
        return await _current()

    @router.patch("", dependencies=[Depends(require_admin)])
    async def patch_digest_settings(payload: DigestSettings):
        update = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not update:
            raise HTTPException(status_code=400, detail="No fields to update")
        update["updated_at"] = _now_iso()
        await db.digest_settings.update_one(
            {"key": "safety"},
            {"$set": {"key": "safety", **update}},
            upsert=True,
        )
        return await _current()

    @router.post("/send-now", dependencies=[Depends(require_admin)])
    async def manual_send_now():
        cfg = await _current()
        if not cfg.get("enabled"):
            raise HTTPException(status_code=409, detail="Digest is disabled — enable it before sending")
        payload = await build_payload()
        html = render_html(payload)
        sent_to: List[str] = []
        send_errors: List[str] = []
        if send_email_fn and os.environ.get("AUTO_EMAIL_REPORTS", "false").lower() in ("1", "true", "yes"):
            for r in cfg.get("recipients") or []:
                try:
                    await send_email_fn(r, "[MASCI] Weekly Safety Digest (manual)", html)
                    sent_to.append(r)
                except Exception as e:  # noqa: BLE001
                    send_errors.append(f"{r}: {e!s}")
        else:
            # Preview-only mode in environments without Resend
            sent_to = []
        # `at` is BSON datetime so the 30-day TTL index fires.
        now_dt = datetime.now(timezone.utc).replace(microsecond=0)
        run = {
            "at": now_dt,
            "iso_at": now_dt.isoformat(),
            "kind": "manual",
            "recipients": cfg.get("recipients") or [],
            "sent_to": sent_to,
            "errors": send_errors,
            "auto_email_reports": os.environ.get("AUTO_EMAIL_REPORTS", "false"),
        }
        await db.digest_runs.insert_one({**run})
        return {
            "ok": True,
            "sent": bool(sent_to),
            "sent_to": sent_to,
            "errors": send_errors,
            "payload": payload,
        }

    return router


__all__ = ["build_admin_digest_router"]
