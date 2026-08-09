from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request

from services.enterprise_governance import (
    evaluate_governance_action,
    resolve_governance_actor_context,
)


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

            row = await is_valid_directory_admin_token_async(
                db,
                headers.get("X-Admin-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "admin", "_auth_path": "directory_admin_token"}
        if headers.get("X-PM-Token"):
            from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415

            row = await is_valid_pm_user_token_async(
                db,
                headers.get("X-PM-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "pm", "_auth_path": "pm_token"}
        if headers.get("X-HR-Token"):
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415

            row = await is_valid_hr_user_token_async(
                db,
                headers.get("X-HR-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "hr", "_auth_path": "hr_token"}
        if headers.get("X-Safety-Token"):
            from safety_users import is_valid_safety_user_token_async  # noqa: PLC0415

            row = await is_valid_safety_user_token_async(
                db,
                headers.get("X-Safety-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "safety", "_auth_path": "safety_token"}
        if headers.get("X-Shop-Token"):
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415

            row = await is_valid_shop_user_token_async(
                db,
                headers.get("X-Shop-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "shop", "_auth_path": "shop_token"}
        if headers.get("X-Dispatch-Token"):
            from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415

            row = await is_valid_dispatch_user_token_async(
                db,
                headers.get("X-Dispatch-Token"),
                allow_unbound_directory_session=True,
            )
            if row:
                return {**row, "_actor": "dispatch", "_auth_path": "dispatch_token"}
        if headers.get("X-FL-Token"):
            from field_leadership_users import is_valid_fl_user_token_async  # noqa: PLC0415

            row = await is_valid_fl_user_token_async(
                db,
                headers.get("X-FL-Token"),
                allow_unbound_directory_session=True,
            )
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
        decision_record = result.get("decision_record") or {}
        explanation = result.get("explanation") or decision_record.get("explanation") or {}
        policy = result.get("policy") or decision_record.get("policy_snapshot") or {}
        detail = {
            "code": result.get("denial_code") or "governance_denied",
            "reason": result.get("reason") or "Governance policy denied the action.",
            "action_key": action_key,
            "resource_type": resource_type,
            "decision_id": (decision_record.get("decision_id") or decision_record.get("id") or ""),
            "policy_id": policy.get("policy_id") or decision_record.get("policy_id") or "",
            "policy_version": policy.get("version") or decision_record.get("policy_version") or "",
            "approval_flow_id": policy.get("approval_flow_id") or "",
            "required_permissions": policy.get("required_permissions") or result.get("required_permissions") or [],
            "explanation": explanation,
        }
        raise HTTPException(status_code=403, detail=detail)
    return result


async def build_governance_actor_context(db, actor: Dict[str, Any]) -> Dict[str, Any]:
    return await resolve_governance_actor_context(db, actor)


async def governance_project_scope_numbers(db, actor: Any) -> Optional[List[str]]:
    if actor is True:
        return None
    if not isinstance(actor, dict):
        return []
    email = str(actor.get("email") or "").strip().lower()
    configured_super_email = str(os.environ.get("SUPER_ADMIN_EMAIL") or "").strip().lower()
    if configured_super_email and email == configured_super_email:
        return None
    if actor.get("is_super_admin") is True:
        return None
    resolved = await resolve_governance_actor_context(db, actor)
    if str(resolved.get("governance_scope_mode") or "") == "global":
        return None
    return list(resolved.get("project_numbers") or [])


async def governance_project_scope_filter(
    db,
    actor: Any,
    *,
    field_name: str = "project_number",
    base_filter: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    query = dict(base_filter or {})
    project_numbers = await governance_project_scope_numbers(db, actor)
    if project_numbers is None:
        return query
    if not project_numbers:
        return None
    query[field_name] = {"$in": project_numbers}
    return query


async def governance_project_scope_allows(
    db,
    actor: Any,
    project_number: Optional[str],
) -> bool:
    project_numbers = await governance_project_scope_numbers(db, actor)
    if project_numbers is None:
        return True
    if not project_number:
        return False
    return str(project_number) in set(project_numbers)


@dataclass
class GovernanceProjectScope:
    is_admin: bool
    project_numbers: Optional[List[str]]

    def is_definitively_empty(self) -> bool:
        return self.project_numbers == []

    def allows(self, project_number: Optional[str]) -> bool:
        if self.is_admin:
            return True
        if not project_number:
            return False
        return str(project_number) in set(self.project_numbers or [])

    def filter(self, base_filter: Optional[Dict[str, Any]] = None, *, field_name: str = "project_number") -> Dict[str, Any]:
        query = dict(base_filter or {})
        if self.is_admin:
            return query
        query[field_name] = {"$in": list(self.project_numbers or [])}
        return query


async def governance_project_scope(db, actor: Any) -> GovernanceProjectScope:
    project_numbers = await governance_project_scope_numbers(db, actor)
    return GovernanceProjectScope(
        is_admin=project_numbers is None,
        project_numbers=None if project_numbers is None else list(project_numbers),
    )
