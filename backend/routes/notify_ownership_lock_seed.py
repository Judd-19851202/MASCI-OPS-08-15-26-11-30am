"""
Track 14.0-NOTIFY-OWNERSHIP-LOCK · admin-only test seed routes.

Strictly admin-token gated. Used by `tests/test_notify_ownership_lock.py`
to insert / clean up scratch notification rows during leakage and
asset-admin scope verification. Preview / test environment only — these
routes are no-ops in production deploys (read DB_NAME guard).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel


class SeedItem(BaseModel):
    type: str
    recipient_role: str
    recipient_user_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    severity: Optional[str] = "Info"


class SeedBatch(BaseModel):
    items: List[SeedItem]
    prefix: str = "notify-ownlock-test-"


class FlagBody(BaseModel):
    email: str
    is_asset_admin: bool


def _is_preview_db() -> bool:
    name = (os.environ.get("DB_NAME") or "").lower()
    return "preview" in name or "test" in name


def register_notify_ownership_lock_seed(
    app, db, require_admin_dep: Callable,
) -> APIRouter:
    router = APIRouter(tags=["notify-ownership-lock-seed"])

    @router.post("/api/admin/notify-ownership-lock/seed")
    async def seed(
        body: SeedBatch = Body(...),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        if not _is_preview_db():
            raise HTTPException(
                403, "Test seed endpoint disabled in production DB.",
            )
        now = datetime.now(timezone.utc)
        inserted = 0
        for spec in body.items:
            doc = {
                "id": f"{body.prefix}{uuid.uuid4().hex[:12]}",
                "type": spec.type,
                "title": spec.title,
                "message": spec.message or spec.title,
                "severity": spec.severity or "Info",
                "recipient_role": spec.recipient_role,
                "recipient_user_id": spec.recipient_user_id,
                "linked_task_id": None,
                "created_at": now,
                "expires_at": now + timedelta(hours=1),
                "read_by": [],
                "acknowledged_by": None,
                "acknowledged_at": None,
                "delivery": {"internal": True, "email": False,
                             "push": False, "sms": False},
            }
            await db.notifications.insert_one(doc)
            inserted += 1
        return {"ok": True, "inserted": inserted, "prefix": body.prefix}

    @router.delete("/api/admin/notify-ownership-lock/seed")
    async def cleanup(
        prefix: str = Query(default="notify-ownlock-test-"),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        if not _is_preview_db():
            raise HTTPException(
                403, "Test seed endpoint disabled in production DB.",
            )
        res = await db.notifications.delete_many(
            {"id": {"$regex": f"^{prefix}"}},
        )
        return {"ok": True, "deleted": res.deleted_count}

    @router.post("/api/admin/notify-ownership-lock/seed-flag")
    async def seed_flag(
        body: FlagBody = Body(...),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        """Toggle `is_asset_admin` on the directory row by email. Used by
        D3 scope test to make the X-Asset-Admin path deterministic."""
        if not _is_preview_db():
            raise HTTPException(
                403, "Test seed endpoint disabled in production DB.",
            )
        res = await db.user_directory.update_one(
            {"email": body.email.lower().strip()},
            {"$set": {"is_asset_admin": bool(body.is_asset_admin)}},
        )
        return {"ok": True, "modified": res.modified_count}

    app.include_router(router)
    return router


__all__ = ["register_notify_ownership_lock_seed"]
