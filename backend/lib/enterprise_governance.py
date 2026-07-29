from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request

from services.enterprise_governance import evaluate_governance_action, ensure_identity_projection


async def resolve_actor_from_request(db, request: Optional[Request], actor: Any) -> Dict[str, Any]:
    if isinstance(actor, dict) and (actor.get("id") or actor.get("email") or actor.get("user_id")):
        return actor
    req = request
    if req is None:
        return {"id": "unknown", "email": "unknown@masci", "_actor": "admin" if actor is True else "unknown"}
    headers = req.headers
    directory_token = headers.get("X-Directory-Token") or ""
    if directory_token:
        try:
            from user_directory import session_user  # noqa: PLC0415

            row = await session_user(db, token=directory_token)
            if row:
                return {**row, "_actor": "admin" if headers.get("X-Admin-Token") else "directory", "_auth_path": "directory_session"}
        except Exception:
            pass
    try:
        if headers.get("X-Admin-Token"):
            from user_directory import is_valid_directory_admin_token_async  # noqa: PLC0415

            row = await is_valid_directory_admin_token_async(db, headers.get("X-Admin-Token"))
            if row:
                return {**row, "_actor": "admin", "_auth_path": "directory_admin_token"}
        if headers.get("X-PM-Token"):
            from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415

            row = await is_valid_pm_user_token_async(db, headers.get("X-PM-Token"))
            if row:
                return {**row, "_actor": "pm", "_auth_path": "pm_token"}
        if headers.get("X-HR-Token"):
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415

            row = await is_valid_hr_user_token_async(db, headers.get("X-HR-Token"))
            if row:
                return {**row, "_actor": "hr", "_auth_path": "hr_token"}
        if headers.get("X-Safety-Token"):
            from safety_users import is_valid_safety_user_token_async  # noqa: PLC0415

            row = await is_valid_safety_user_token_async(db, headers.get("X-Safety-Token"))
            if row:
                return {**row, "_actor": "safety", "_auth_path": "safety_token"}
        if headers.get("X-Shop-Token"):
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415

            row = await is_valid_shop_user_token_async(db, headers.get("X-Shop-Token"))
            if row:
                return {**row, "_actor": "shop", "_auth_path": "shop_token"}
        if headers.get("X-Dispatch-Token"):
            from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415

            row = await is_valid_dispatch_user_token_async(db, headers.get("X-Dispatch-Token"))
            if row:
                return {**row, "_actor": "dispatch", "_auth_path": "dispatch_token"}
        if headers.get("X-FL-Token"):
            from field_leadership_users import is_valid_fl_user_token_async  # noqa: PLC0415

            row = await is_valid_fl_user_token_async(db, headers.get("X-FL-Token"))
            if row:
                return {**row, "_actor": "field_leadership", "_auth_path": "field_leadership_token"}
    except Exception:
        pass
    return {"id": "unknown", "email": "unknown@masci", "_actor": "admin" if actor is True else "unknown"}


def _resource_id(resource_type: str, resource: Optional[Dict[str, Any]], fallback: Optional[str] = None) -> str:
    row = dict(resource or {})
    return str(row.get("id") or row.get("doc_id") or fallback or resource_type)


async def require_governed_action(
    db,
    *,
    actor: Any,
    action_key: str,
    resource_type: str,
    resource: Optional[Dict[str, Any]] = None,
    requested_context: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    resolved_actor = await resolve_actor_from_request(db, request, actor)
    result = await evaluate_governance_action(
        db,
        actor=resolved_actor,
        action_key=action_key,
        resource_type=resource_type,
        resource_id=_resource_id(resource_type, resource, fallback=(requested_context or {}).get("resource_id")),
        resource=resource,
        requested_context=requested_context,
    )
    if not result.get("allowed"):
        detail = {
            "code": result.get("denial_code") or "governance_denied",
            "reason": result.get("reason") or "Governance policy denied the action.",
            "action_key": action_key,
            "resource_type": resource_type,
            "decision_id": ((result.get("decision_record") or {}).get("id") or ""),
        }
        raise HTTPException(status_code=403, detail=detail)
    return result


async def build_governance_actor_context(db, actor: Dict[str, Any]) -> Dict[str, Any]:
    return await ensure_identity_projection(db, actor)
