from __future__ import annotations

from typing import Any, Dict, List


CONTRACT_VERSION = "C2.13"


def capability_contract(**kwargs: Any) -> Dict[str, Any]:
    return {
        "capability_id": kwargs["capability_id"],
        "name": kwargs["name"],
        "canonical_owner": kwargs["canonical_owner"],
        "domain": kwargs["domain"],
        "action_type": kwargs["action_type"],
        "endpoint": kwargs["endpoint"],
        "permission": kwargs["permission"],
        "role_requirements": kwargs.get("role_requirements", []),
        "tenant_scope": kwargs["tenant_scope"],
        "project_scope": kwargs["project_scope"],
        "environment_scope": kwargs["environment_scope"],
        "provider_requirements": kwargs.get("provider_requirements", []),
        "prerequisites": kwargs.get("prerequisites", []),
        "available": kwargs["available"],
        "disabled_reason": kwargs.get("disabled_reason", ""),
        "destructive": kwargs.get("destructive", False),
        "dry_run_required": kwargs.get("dry_run_required", False),
        "confirmation_required": kwargs.get("confirmation_required", False),
        "confirmation_phrase": kwargs.get("confirmation_phrase", ""),
        "idempotency_key_required": kwargs.get("idempotency_key_required", False),
        "duplicate_prevention": kwargs.get("duplicate_prevention", ""),
        "retry_safe": kwargs.get("retry_safe", True),
        "completion_evidence": kwargs.get("completion_evidence", []),
        "audit_events": kwargs.get("audit_events", []),
        "recovery_behavior": kwargs.get("recovery_behavior", ""),
        "contract_version": CONTRACT_VERSION,
    }


def occ_operation_capability(operation: Dict[str, Any], *, available: bool, disabled_reason: str = "") -> Dict[str, Any]:
    op_id = operation.get("id") or "unknown"
    return capability_contract(
        capability_id=f"occ.{op_id}",
        name=operation.get("title") or op_id,
        canonical_owner="shared_admin_shell",
        domain="operations_control_center",
        action_type="apply" if operation.get("has_apply") else "view",
        endpoint=f"/api/admin/operations-control/operations/{op_id}/apply" if operation.get("has_apply") else f"/api/admin/operations-control/operations/{op_id}",
        permission="admin",
        role_requirements=["admin"],
        tenant_scope="shared",
        project_scope="global",
        environment_scope="preview_and_production",
        prerequisites=(['dry_run_completed'] if operation.get('requires_dry_run') else []) + (["confirmation_phrase"] if operation.get("confirmation_phrase") else []),
        available=available,
        disabled_reason=disabled_reason,
        destructive=bool(operation.get("confirmation_phrase")),
        dry_run_required=bool(operation.get("requires_dry_run")),
        confirmation_required=bool(operation.get("confirmation_phrase")),
        confirmation_phrase=operation.get("confirmation_phrase") or "",
        idempotency_key_required=False,
        duplicate_prevention="server-side dry_run_id gating",
        retry_safe=not bool(operation.get("confirmation_phrase")),
        completion_evidence=["operations_audit.action_id", "result envelope"],
        audit_events=["dry_run", "apply"],
        recovery_behavior="Operator can inspect audit row and retry after dry-run.",
    )


def shell_signout_capability(*, portal: str, route: str) -> Dict[str, Any]:
    return capability_contract(
        capability_id=f"shared-shell.sign-out.{portal}",
        name=f"Sign out ({portal})",
        canonical_owner="shared_auth_session",
        domain="shared_shell",
        action_type="sign_out",
        endpoint=route,
        permission="authenticated",
        role_requirements=[portal, "admin"],
        tenant_scope="shared",
        project_scope="global",
        environment_scope="preview_and_production",
        available=True,
        disabled_reason="",
        destructive=False,
        dry_run_required=False,
        confirmation_required=False,
        confirmation_phrase="",
        idempotency_key_required=False,
        duplicate_prevention="clearAllSessions wipes browser auth artifacts",
        retry_safe=True,
        completion_evidence=["local/session storage cleared", "server session invalidated when supported"],
        audit_events=["multi_logout", "admin_logout", "pm_logout"],
        recovery_behavior="Route guards redirect to the correct login screen.",
    )


def truth_action_capability(*, surface_id: str, route: str, available: bool = True) -> Dict[str, Any]:
    return capability_contract(
        capability_id=f"truth.{surface_id}.refresh",
        name=f"Refresh {surface_id}",
        canonical_owner=surface_id,
        domain="shared_truth_surface",
        action_type="refresh",
        endpoint=route,
        permission="admin",
        role_requirements=["admin"],
        tenant_scope="shared",
        project_scope="global",
        environment_scope="preview_and_production",
        available=available,
        disabled_reason="" if available else "Truth route unavailable.",
        destructive=False,
        dry_run_required=False,
        confirmation_required=False,
        confirmation_phrase="",
        idempotency_key_required=False,
        duplicate_prevention="read-only GET",
        retry_safe=True,
        completion_evidence=["updated checked_at/generated_at in response"],
        audit_events=[],
        recovery_behavior="Retry read-only refresh.",
    )


__all__ = ["CONTRACT_VERSION", "capability_contract", "occ_operation_capability", "shell_signout_capability", "truth_action_capability"]