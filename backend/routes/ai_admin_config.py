"""AI-ADMIN-001 · Admin AI Configuration Center — backend routes.

Admin-only surface for managing tenant AI capabilities. Companion to
AI-CONFIG-001. All endpoints are gated by ``require_admin_strict`` so
PM/HR/Field/Shop tokens are rejected — this is a super-admin surface.

Doctrine
--------
- No raw API key values are ever returned.
- No live provider calls unless explicitly requested via the safe
  admin-only ``/test`` endpoint (bounded, mocked in tests).
- Every mutation is audited (before/after/actor/note).
- Tenant isolation: updates to tenant A never touch tenant B.
- AI OFF must remain a first-class, fully-supported state.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from services.ai_gateway.capabilities import (
    MODULE_ENV_MAP,
    PROVIDER_KEY_MAP,
    gateway_status_snapshot,
    resolve_ai_capabilities,
)


# ─────────────────────── constants ────────────────────────────────

# The seven mutable capability booleans on a tenant document. Any field
# outside this allow-list is silently dropped from update payloads.
_TENANT_ALLOWED_FIELDS = (
    "tenant_ai_enabled",
    "daily_report_summary_enabled",
    "photo_intelligence_enabled",
    "pm_intelligence_enabled",
    "admin_intelligence_enabled",
    "safety_intelligence_enabled",
    "translation_enabled",
)

# Canonical tenant known to the platform today. In multi-tenant deployments
# this list is derived from the ``tenant_ai_capabilities`` collection plus
# any registered tenants; for MASCI it's the single home tenant.
_DEFAULT_TENANT_ID = "masci"
_DEFAULT_TENANT_NAME = "MASCI (default)"


# ─────────────────────── payload models ───────────────────────────

class TenantCapabilityUpdateBody(BaseModel):
    """Partial update payload — only the seven allow-listed booleans
    plus an optional operator note are honoured."""

    tenant_ai_enabled: Optional[bool] = None
    daily_report_summary_enabled: Optional[bool] = None
    photo_intelligence_enabled: Optional[bool] = None
    pm_intelligence_enabled: Optional[bool] = None
    admin_intelligence_enabled: Optional[bool] = None
    safety_intelligence_enabled: Optional[bool] = None
    translation_enabled: Optional[bool] = None
    note: Optional[str] = Field(default=None, max_length=1000)


class ProviderConnectionTestBody(BaseModel):
    tenant_id: Optional[str] = None


# ─────────────────────── helpers ──────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _sanitize_tenant_doc(doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a doc with predictable keys and no Mongo internals."""
    if not doc:
        return {}
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


def _actor_label(request: Request) -> str:
    """Best-effort actor label — audit is admin-only so a token was
    validated upstream, but we do not have a user dict here. Use the
    ``X-Admin-Actor`` optional header if the frontend supplies it,
    else fall back to a redacted admin marker."""
    actor = (request.headers.get("X-Admin-Actor") or "").strip()
    return actor[:120] if actor else "admin"


async def _write_audit_entry(
    db,
    *,
    tenant_id: str,
    actor: str,
    before: Dict[str, Any],
    after: Dict[str, Any],
    changed_fields: List[str],
    note: Optional[str],
    request: Request,
) -> None:
    """Insert a single immutable audit row. Never contains secrets."""
    entry = {
        "tenant_id": tenant_id,
        "actor": actor,
        "before": before,
        "after": after,
        "changed_fields": changed_fields,
        "note": (note or "").strip()[:1000] or None,
        "timestamp": _iso(_now()),
        "request_id": (request.headers.get("X-Request-Id") or "").strip()[:120] or None,
        "ip": (request.client.host if request.client else None),
        "user_agent": (request.headers.get("User-Agent") or "").strip()[:200] or None,
    }
    try:
        await db["tenant_ai_capability_audit"].insert_one(entry)
    except Exception:  # noqa: BLE001
        # Audit is best-effort; never surface a 500 because a write log
        # failed. The mutation itself already succeeded.
        pass


# ─────────────────────── registration ─────────────────────────────

def register_ai_admin_config_routes(
    api_router: APIRouter,
    *,
    db,
    require_admin_strict,
) -> None:
    """Mount all AI-ADMIN-001 routes onto ``api_router``."""

    # ────────────── GET /api/admin/ai/config/status ────────────────
    @api_router.get("/admin/ai/config/status")
    async def admin_ai_config_status(_admin=Depends(require_admin_strict)):
        """Sanitised deployment-scope switchboard state.

        NEVER returns raw API key values — booleans only for key presence.
        Identical envelope shape to ``/api/ai/gateway/status`` so admins
        can rely on one JSON contract.
        """
        return gateway_status_snapshot()

    # ────────────── GET /api/admin/ai/tenants ─────────────────────
    @api_router.get("/admin/ai/tenants")
    async def admin_ai_list_tenants(_admin=Depends(require_admin_strict)):
        """List tenants known to the AI switchboard.

        Sources:
          - Every document in ``tenant_ai_capabilities``.
          - The canonical default tenant (``masci``) if not present.
        """
        tenants: Dict[str, Dict[str, Any]] = {}
        try:
            cursor = db["tenant_ai_capabilities"].find({}, {"_id": 0})
            docs = await cursor.to_list(length=500)
        except Exception:  # noqa: BLE001
            docs = []
        for d in docs:
            tid = str(d.get("tenant_id") or "").strip()
            if not tid:
                continue
            tenants[tid] = {
                "tenant_id": tid,
                "tenant_name": d.get("tenant_name") or tid,
                "tenant_ai_enabled": bool(d.get("tenant_ai_enabled")),
                "has_override_doc": True,
                "updated_at": d.get("updated_at"),
                "updated_by": d.get("updated_by"),
            }
        if _DEFAULT_TENANT_ID not in tenants:
            tenants[_DEFAULT_TENANT_ID] = {
                "tenant_id": _DEFAULT_TENANT_ID,
                "tenant_name": _DEFAULT_TENANT_NAME,
                "tenant_ai_enabled": (
                    (os.environ.get("TENANT_AI_ENABLED") or "").strip().lower()
                    in {"1", "true", "yes", "on"}
                ),
                "has_override_doc": False,
                "updated_at": None,
                "updated_by": None,
            }
        return {"tenants": sorted(tenants.values(), key=lambda t: t["tenant_id"])}

    # ────── GET /api/admin/ai/tenants/{tenant_id}/capabilities ─────
    @api_router.get("/admin/ai/tenants/{tenant_id}/capabilities")
    async def admin_ai_get_tenant_capabilities(
        tenant_id: str,
        _admin=Depends(require_admin_strict),
    ):
        """Resolved capabilities + tenant override doc for one tenant.

        Returns:
            {
              tenant_id, tenant_name, has_override_doc,
              overrides: {...},         # what's stored in Mongo (or {})
              modules: {                # per-module resolved verdict
                <module>: {
                  enabled: bool,
                  reason_disabled: str|null,
                  selected_provider, fallback_provider,
                  provider_available, tenant_ai_enabled
                }
              }
            }
        """
        tenant_id = (tenant_id or "").strip()
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required")

        try:
            doc = await db["tenant_ai_capabilities"].find_one(
                {"tenant_id": tenant_id}, {"_id": 0}
            )
        except Exception:  # noqa: BLE001
            doc = None
        overrides = _sanitize_tenant_doc(doc)

        modules: Dict[str, Dict[str, Any]] = {}
        for module in MODULE_ENV_MAP.keys():
            cap = await resolve_ai_capabilities(db, tenant_id, module)
            modules[module] = cap.to_dict()

        return {
            "tenant_id": tenant_id,
            "tenant_name": overrides.get("tenant_name") or (
                _DEFAULT_TENANT_NAME if tenant_id == _DEFAULT_TENANT_ID else tenant_id
            ),
            "has_override_doc": bool(doc),
            "overrides": overrides,
            "modules": modules,
        }

    # ────── PUT /api/admin/ai/tenants/{tenant_id}/capabilities ─────
    @api_router.put("/admin/ai/tenants/{tenant_id}/capabilities")
    async def admin_ai_update_tenant_capabilities(
        tenant_id: str,
        body: TenantCapabilityUpdateBody,
        request: Request,
        _admin=Depends(require_admin_strict),
    ):
        """Upsert a tenant's AI capability booleans. Audit-logged.

        - Only the seven allow-listed booleans are honoured.
        - Provider API key values can NEVER be written through this endpoint.
        - Tenant isolation: only the specified tenant_id doc is touched.
        """
        tenant_id = (tenant_id or "").strip()
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required")

        # 1) Snapshot the "before" state for audit.
        try:
            before_doc = await db["tenant_ai_capabilities"].find_one(
                {"tenant_id": tenant_id}, {"_id": 0}
            ) or {}
        except Exception:  # noqa: BLE001
            before_doc = {}

        # 2) Build the sanitised patch — allow-list only.
        patch: Dict[str, Any] = {}
        payload = body.model_dump(exclude_none=True)
        for field in _TENANT_ALLOWED_FIELDS:
            if field in payload:
                patch[field] = bool(payload[field])
        if not patch:
            raise HTTPException(
                status_code=400,
                detail="no updatable fields supplied — allow-list: "
                + ", ".join(_TENANT_ALLOWED_FIELDS),
            )

        # 3) Merge into new "after" doc.
        now = _iso(_now())
        actor = _actor_label(request)
        new_doc = {
            **{k: v for k, v in before_doc.items() if k != "_id"},
            **patch,
            "tenant_id": tenant_id,
            "updated_at": now,
            "updated_by": actor,
        }
        if not before_doc:
            new_doc.setdefault("created_at", now)
        # Version stamp increments each write.
        new_doc["version"] = int(before_doc.get("version") or 0) + 1
        if payload.get("note"):
            new_doc["note"] = str(payload["note"])[:1000]

        # 4) Persist atomically.
        try:
            await db["tenant_ai_capabilities"].update_one(
                {"tenant_id": tenant_id},
                {"$set": new_doc},
                upsert=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"tenant update failed: {exc}")

        # 5) Compute changed field list for audit.
        changed = [
            f for f in _TENANT_ALLOWED_FIELDS
            if before_doc.get(f) != new_doc.get(f) and f in patch
        ]
        await _write_audit_entry(
            db,
            tenant_id=tenant_id,
            actor=actor,
            before=_sanitize_tenant_doc(before_doc),
            after=_sanitize_tenant_doc(new_doc),
            changed_fields=changed,
            note=payload.get("note"),
            request=request,
        )

        # 6) Recompute resolved verdicts so the UI can render instantly.
        modules = {}
        for module in MODULE_ENV_MAP.keys():
            cap = await resolve_ai_capabilities(db, tenant_id, module)
            modules[module] = cap.to_dict()

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "overrides": _sanitize_tenant_doc(new_doc),
            "changed_fields": changed,
            "modules": modules,
        }

    # ────── GET /api/admin/ai/tenants/{tenant_id}/audit ────────────
    @api_router.get("/admin/ai/tenants/{tenant_id}/audit")
    async def admin_ai_get_tenant_audit(
        tenant_id: str,
        limit: int = 50,
        _admin=Depends(require_admin_strict),
    ):
        tenant_id = (tenant_id or "").strip()
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required")
        limit = max(1, min(200, int(limit)))
        try:
            cursor = (
                db["tenant_ai_capability_audit"]
                .find({"tenant_id": tenant_id}, {"_id": 0})
                .sort("timestamp", -1)
                .limit(limit)
            )
            entries = await cursor.to_list(length=limit)
        except Exception:  # noqa: BLE001
            entries = []
        return {"tenant_id": tenant_id, "entries": entries}

    # ────── POST /api/admin/ai/providers/{provider}/test ───────────
    @api_router.post("/admin/ai/providers/{provider}/test")
    async def admin_ai_provider_connection_test(
        provider: str,
        _admin=Depends(require_admin_strict),
    ):
        """Safe, bounded connection sanity check.

        Does NOT make a live provider call. Reports whether the provider
        is *configurable* (flag on + key present). Live-call testing is
        out of scope for AI-ADMIN-001 and belongs on the per-module
        tracks (DR-ROI-001C/D). Returns booleans only, never secrets.
        """
        provider = (provider or "").strip().lower()
        if provider not in PROVIDER_KEY_MAP:
            raise HTTPException(
                status_code=404,
                detail=f"unknown provider — expected one of {list(PROVIDER_KEY_MAP)}",
            )
        flag_env, key_env = PROVIDER_KEY_MAP[provider]
        flag_on = (os.environ.get(flag_env) or "").strip().lower() in {
            "1", "true", "yes", "on",
        }
        key_present = bool((os.environ.get(key_env) or "").strip())
        status = (
            "ready" if flag_on and key_present
            else "missing_key" if flag_on and not key_present
            else "flag_disabled" if not flag_on and key_present
            else "unavailable"
        )
        return {
            "provider": provider,
            "flag_env": flag_env,
            "flag_enabled": flag_on,
            "key_env": key_env,
            "key_present": key_present,
            "status": status,
            "note": (
                "This endpoint does NOT issue a live provider call. "
                "Configure flags/keys via the Emergent Secrets UI, then "
                "re-check status."
            ),
        }


__all__ = ["register_ai_admin_config_routes"]
