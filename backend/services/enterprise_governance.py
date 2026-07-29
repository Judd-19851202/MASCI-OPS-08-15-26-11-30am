from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from lib.trust_spine import attach_correlation, emit_record_created, emit_workflow_stage

COLLECTION_IDENTITY_PROJECTIONS = "enterprise_governance_identity_projections"
COLLECTION_REGISTRY = "enterprise_governance_registry"
COLLECTION_DECISIONS = "enterprise_governance_decisions"
COLLECTION_DELEGATIONS = "enterprise_governance_delegations"
COLLECTION_APPROVALS = "enterprise_governance_approval_flows"
COLLECTION_APPROVAL_REQUESTS = "enterprise_governance_approval_requests"
COLLECTION_OVERRIDES = "enterprise_governance_emergency_overrides"
COLLECTION_AUDIT = "enterprise_governance_audit"
COLLECTION_ORG = "enterprise_governance_organization"

REGISTRY_DOC_ID = "enterprise-governance-v1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_")


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _dedupe_texts(values: List[Any]) -> List[str]:
    seen = []
    for value in values:
        text = _clean(value)
        if text and text not in seen:
            seen.append(text)
    return seen


def build_enterprise_governance_registry() -> Dict[str, Any]:
    permissions = {
        "daily_reports.read": {"label": "Read Daily Reports", "domain": "daily_reports", "action": "read"},
        "daily_reports.update": {"label": "Update Daily Reports", "domain": "daily_reports", "action": "update"},
        "daily_reports.review": {"label": "Review Daily Reports", "domain": "daily_reports", "action": "review"},
        "daily_reports.close": {"label": "Close Daily Reports", "domain": "daily_reports", "action": "close"},
        "schedule.update": {"label": "Update Schedule", "domain": "schedule", "action": "update"},
        "forecast.approve": {"label": "Approve Forecast", "domain": "forecast", "action": "approve"},
        "briefing.approve": {"label": "Approve Briefing", "domain": "briefing", "action": "approve"},
        "oppc.view": {"label": "View OPPC", "domain": "oppc", "action": "read"},
        "oppc.executive.view": {"label": "View Executive OPPC", "domain": "oppc", "action": "view_executive"},
        "operations_control.admin": {"label": "Administer Operations Control", "domain": "operations_control", "action": "administer"},
        "operational_case.read": {"label": "Read Operational Cases", "domain": "operational_case", "action": "read"},
        "operational_case.transition": {"label": "Transition Operational Cases", "domain": "operational_case", "action": "update"},
        "operational_case.close": {"label": "Close Operational Cases", "domain": "operational_case", "action": "close"},
        "operational_case.export": {"label": "Export Operational Case Evidence", "domain": "operational_case", "action": "export"},
        "task.assign": {"label": "Assign Tasks", "domain": "tasks", "action": "assign"},
        "task.close": {"label": "Close Tasks", "domain": "tasks", "action": "close"},
        "notification.ack": {"label": "Acknowledge Notifications", "domain": "notifications", "action": "acknowledge"},
        "baseline.capture": {"label": "Capture Baselines", "domain": "baseline", "action": "create"},
        "baseline.export": {"label": "Export Baselines", "domain": "baseline", "action": "export"},
        "evidence.export": {"label": "Export Evidence", "domain": "evidence", "action": "export"},
        "governance.admin": {"label": "Administer Governance", "domain": "governance", "action": "administer"},
        "governance.override": {"label": "Emergency Override", "domain": "governance", "action": "override"},
        "audit.view": {"label": "View Audit", "domain": "governance", "action": "audit"},
        "executive.view": {"label": "View Executive Surfaces", "domain": "executive", "action": "view_executive"},
        "admin_reporting.view": {"label": "View Administrative Reporting", "domain": "admin_reporting", "action": "read"},
    }
    roles = {
        "system_administrator": {
            "label": "System Administrator",
            "portal_hints": ["admin"],
            "permissions": list(permissions.keys()),
            "authority_level": "platform_admin",
        },
        "executive": {
            "label": "Executive",
            "portal_hints": ["leadership", "admin"],
            "permissions": [
                "oppc.executive.view",
                "executive.view",
                "admin_reporting.view",
                "audit.view",
                "operational_case.read",
                "evidence.export",
            ],
            "authority_level": "executive",
        },
        "project_manager": {
            "label": "Project Manager",
            "portal_hints": ["pm", "admin"],
            "permissions": [
                "daily_reports.read",
                "daily_reports.update",
                "daily_reports.review",
                "schedule.update",
                "forecast.approve",
                "briefing.approve",
                "oppc.view",
                "operational_case.read",
                "task.assign",
                "notification.ack",
            ],
            "authority_level": "project",
        },
        "hr": {
            "label": "HR",
            "portal_hints": ["hr", "admin"],
            "permissions": ["daily_reports.read", "admin_reporting.view", "audit.view", "notification.ack"],
            "authority_level": "department",
        },
        "safety": {
            "label": "Safety",
            "portal_hints": ["safety", "admin"],
            "permissions": ["daily_reports.read", "operational_case.read", "notification.ack", "evidence.export"],
            "authority_level": "department",
        },
        "shop": {
            "label": "Shop",
            "portal_hints": ["shop", "admin"],
            "permissions": ["task.assign", "task.close", "notification.ack"],
            "authority_level": "department",
        },
        "dispatch": {
            "label": "Dispatcher",
            "portal_hints": ["dispatch", "admin"],
            "permissions": ["notification.ack", "task.assign"],
            "authority_level": "department",
        },
        "field_leadership": {
            "label": "Field Leadership",
            "portal_hints": ["field_leadership", "admin"],
            "permissions": ["daily_reports.read", "notification.ack"],
            "authority_level": "project",
        },
    }
    policies = {
        "operational_case_close_policy": {
            "version": "1.0",
            "action_key": "operational_case.close",
            "required_permissions": ["operational_case.close"],
            "require_project_access": True,
            "require_approval_flow": "critical_case_close",
            "separation_rules": ["creator_cannot_close_without_override_review", "audit_closer_separation"],
        },
        "evidence_export_policy": {
            "version": "1.0",
            "action_key": "evidence.export",
            "required_permissions": ["evidence.export"],
            "require_project_access": False,
            "require_approval_flow": "sensitive_export_review",
            "separation_rules": [],
        },
        "schedule_change_policy": {
            "version": "1.0",
            "action_key": "schedule.update",
            "required_permissions": ["schedule.update"],
            "require_project_access": True,
            "require_approval_flow": "schedule_change_review",
            "separation_rules": ["submitter_cannot_self_approve"],
        },
        "forecast_approval_policy": {
            "version": "1.0",
            "action_key": "forecast.approve",
            "required_permissions": ["forecast.approve"],
            "require_project_access": True,
            "require_approval_flow": "forecast_approval",
            "separation_rules": ["submitter_cannot_self_approve"],
        },
        "baseline_protection_policy": {
            "version": "1.0",
            "action_key": "baseline.capture",
            "required_permissions": ["baseline.capture"],
            "require_project_access": False,
            "require_approval_flow": "baseline_control_review",
            "separation_rules": ["baseline_approver_cannot_be_requestor"],
        },
    }
    approval_flows = {
        "critical_case_close": {
            "label": "Critical Case Closure Approval",
            "required_roles": ["system_administrator", "executive"],
            "min_approvals": 1,
        },
        "sensitive_export_review": {
            "label": "Sensitive Evidence Export Review",
            "required_roles": ["system_administrator", "executive", "hr", "safety"],
            "min_approvals": 1,
        },
        "schedule_change_review": {
            "label": "Schedule Change Review",
            "required_roles": ["project_manager", "system_administrator"],
            "min_approvals": 1,
        },
        "forecast_approval": {
            "label": "Forecast Approval",
            "required_roles": ["project_manager", "executive"],
            "min_approvals": 1,
        },
        "baseline_control_review": {
            "label": "Baseline Control Review",
            "required_roles": ["system_administrator", "executive"],
            "min_approvals": 1,
        },
        "emergency_override_review": {
            "label": "Emergency Override Review",
            "required_roles": ["system_administrator", "executive"],
            "min_approvals": 1,
        },
    }
    separation_rules = {
        "creator_cannot_close_without_override_review": {
            "label": "Creator cannot close without override review",
            "forbidden_actor_match": ["created_by.user_id"],
        },
        "audit_closer_separation": {
            "label": "Auditor cannot close audited case",
            "forbidden_actor_match": ["resolution.verified_by_user_id"],
        },
        "submitter_cannot_self_approve": {
            "label": "Submitter cannot self-approve",
            "forbidden_actor_match": ["submitted_by.user_id", "created_by.user_id"],
        },
        "baseline_approver_cannot_be_requestor": {
            "label": "Baseline approver cannot be requestor",
            "forbidden_actor_match": ["requested_by.user_id"],
        },
        "override_requestor_cannot_self_approve": {
            "label": "Override requestor cannot self-approve",
            "forbidden_actor_match": ["requesting_identity.user_id"],
        },
    }
    return {
        "id": REGISTRY_DOC_ID,
        "version": "1.0",
        "constitutional_principles": [
            "enterprise_governance_principle",
            "policy_before_permission",
            "authentication_and_authorization_are_separate_responsibilities",
            "backend_enforcement_is_authoritative",
            "denials_are_governed_outcomes",
            "no_module_may_keep_an_ungoverned_alternate_path",
            "no_emergency_override_is_silent_permanent_self_approved_or_unaudited",
        ],
        "permissions": permissions,
        "roles": roles,
        "policies": policies,
        "approval_flows": approval_flows,
        "separation_rules": separation_rules,
        "authority_levels": {
            "platform_admin": {"rank": 100},
            "executive": {"rank": 80},
            "department": {"rank": 60},
            "project": {"rank": 40},
        },
        "delegation_rules": {
            "temporary_delegation": {"max_days": 30},
            "vacation_delegation": {"max_days": 45},
            "emergency_delegation": {"max_hours": 72},
        },
        "emergency_override_types": {
            "case_closure": {"requires_reason": True, "requires_evidence": True},
            "evidence_export": {"requires_reason": True, "requires_evidence": True},
            "schedule_change": {"requires_reason": True, "requires_evidence": True},
        },
        "managed_scope": [
            "daily_reports",
            "cost_codes",
            "schedule",
            "oppc",
            "operations_control",
            "operational_case",
            "tasks",
            "notifications",
            "executive_dashboards",
            "administrative_reporting",
            "evidence_exports",
            "baseline_and_certification",
        ],
        "updated_at": _now_iso(),
    }


async def ensure_enterprise_governance_indexes(db) -> None:
    await db[COLLECTION_IDENTITY_PROJECTIONS].create_index("id", unique=True)
    await db[COLLECTION_IDENTITY_PROJECTIONS].create_index("canonical_user_id", unique=True)
    await db[COLLECTION_IDENTITY_PROJECTIONS].create_index([("email", 1)])
    await db[COLLECTION_REGISTRY].create_index("id", unique=True)
    await db[COLLECTION_DECISIONS].create_index("id", unique=True)
    await db[COLLECTION_DECISIONS].create_index([("action_key", 1), ("decided_at", -1)])
    await db[COLLECTION_DECISIONS].create_index([("correlation_id", 1)])
    await db[COLLECTION_DELEGATIONS].create_index("id", unique=True)
    await db[COLLECTION_DELEGATIONS].create_index([("delegator_user_id", 1), ("status", 1)])
    await db[COLLECTION_APPROVALS].create_index("id", unique=True)
    await db[COLLECTION_APPROVAL_REQUESTS].create_index("id", unique=True)
    await db[COLLECTION_APPROVAL_REQUESTS].create_index([("approval_flow_id", 1), ("status", 1), ("created_at", -1)])
    await db[COLLECTION_OVERRIDES].create_index("id", unique=True)
    await db[COLLECTION_OVERRIDES].create_index([("status", 1), ("expires_at", 1)])
    await db[COLLECTION_AUDIT].create_index("id", unique=True)
    await db[COLLECTION_AUDIT].create_index([("created_at", -1)])
    await db[COLLECTION_ORG].create_index("id", unique=True)
    await db[COLLECTION_ORG].create_index([("kind", 1), ("parent_id", 1), ("name", 1)])


async def ensure_enterprise_governance_registry(db) -> Dict[str, Any]:
    await ensure_enterprise_governance_indexes(db)
    existing = await db[COLLECTION_REGISTRY].find_one({"id": REGISTRY_DOC_ID}, {"_id": 0})
    doc = build_enterprise_governance_registry()
    if not existing:
        await db[COLLECTION_REGISTRY].insert_one(dict(doc))
        return doc
    merged = {**existing, **doc, "updated_at": _now_iso()}
    await db[COLLECTION_REGISTRY].update_one({"id": REGISTRY_DOC_ID}, {"$set": merged})
    return merged


async def get_enterprise_governance_registry(db) -> Dict[str, Any]:
    row = await db[COLLECTION_REGISTRY].find_one({"id": REGISTRY_DOC_ID}, {"_id": 0})
    if row:
        return row
    return await ensure_enterprise_governance_registry(db)


def _actor_portals(actor: Dict[str, Any]) -> List[str]:
    portals = _ensure_list((actor or {}).get("portals"))
    out = _dedupe_texts(portals)
    role = _slug((actor or {}).get("_actor") or (actor or {}).get("role") or (actor or {}).get("_actor_kind"))
    if role and role not in out:
        out.append(role)
    return out


def _projection_defaults(actor: Dict[str, Any]) -> Dict[str, Any]:
    email = _clean(actor.get("email")).lower()
    role_hint = _slug(actor.get("role") or actor.get("_actor") or actor.get("_actor_kind"))
    default_roles = []
    mapping = {
        "admin": "system_administrator",
        "pm": "project_manager",
        "hr": "hr",
        "safety": "safety",
        "shop": "shop",
        "dispatch": "dispatch",
        "fl": "field_leadership",
        "field_leadership": "field_leadership",
        "leadership": "executive",
    }
    if role_hint in mapping:
        default_roles.append(mapping[role_hint])
    if actor.get("is_super_admin"):
        default_roles = ["system_administrator"]
    return {
        "id": str(uuid.uuid4()),
        "canonical_user_id": _clean(actor.get("id") or actor.get("user_id")) or str(uuid.uuid4()),
        "email": email,
        "display_name": _clean(actor.get("name") or email) or "Unknown User",
        "identity_source": _clean(actor.get("_auth_path") or actor.get("_actor") or "directory"),
        "tenant_id": _clean(actor.get("tenant_id") or "masci"),
        "company_id": _clean(actor.get("company_id") or "masci"),
        "division_id": _clean(actor.get("division_id")),
        "department_id": _clean(actor.get("department_id")),
        "region_id": _clean(actor.get("region_id")),
        "project_numbers": _dedupe_texts(_ensure_list(actor.get("project_numbers") or actor.get("projects"))),
        "crew_ids": _dedupe_texts(_ensure_list(actor.get("crews_managed") or actor.get("crew_ids") or actor.get("crew"))),
        "team_ids": _dedupe_texts(_ensure_list(actor.get("team_ids") or actor.get("teams"))),
        "reports_to_user_id": _clean(actor.get("reports_to_user_id") or actor.get("supervisor_user_id")),
        "employee_id": _clean(actor.get("employee_id") or actor.get("employee_master_id")),
        "employment_status": _clean(actor.get("employment_status") or actor.get("status") or "active"),
        "actor_kind": _clean(actor.get("_actor") or actor.get("_actor_kind") or actor.get("role")),
        "active_roles": default_roles,
        "direct_permissions": [],
        "delegated_permissions": [],
        "temporary_authority": [],
        "governance_restrictions": [],
        "portals": _actor_portals(actor),
        "effective_from": _now_iso(),
        "effective_to": "",
        "policy_attributes": {
            "is_super_admin": bool(actor.get("is_super_admin")),
            "disabled": bool(actor.get("disabled")),
            "must_change_password": bool(actor.get("must_change_password")),
        },
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


async def ensure_identity_projection(db, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_enterprise_governance_registry(db)
    canonical_user_id = _clean(actor.get("id") or actor.get("user_id"))
    email = _clean(actor.get("email")).lower()
    query = {"canonical_user_id": canonical_user_id} if canonical_user_id else {"email": email}
    row = await db[COLLECTION_IDENTITY_PROJECTIONS].find_one(query, {"_id": 0})
    default = _projection_defaults(actor)
    if not row:
        await db[COLLECTION_IDENTITY_PROJECTIONS].insert_one(dict(default))
        return default
    merged = {
        **row,
        "email": default["email"] or row.get("email"),
        "display_name": default["display_name"] or row.get("display_name"),
        "identity_source": default["identity_source"] or row.get("identity_source"),
        "tenant_id": default["tenant_id"] or row.get("tenant_id"),
        "company_id": default["company_id"] or row.get("company_id"),
        "actor_kind": default["actor_kind"] or row.get("actor_kind"),
        "portals": _dedupe_texts([*(row.get("portals") or []), *default["portals"]]),
        "active_roles": _dedupe_texts([*(row.get("active_roles") or []), *default["active_roles"]]),
        "policy_attributes": {**(row.get("policy_attributes") or {}), **default["policy_attributes"]},
        "updated_at": _now_iso(),
    }
    if default["project_numbers"]:
        merged["project_numbers"] = _dedupe_texts([*(row.get("project_numbers") or []), *default["project_numbers"]])
    if default["crew_ids"]:
        merged["crew_ids"] = _dedupe_texts([*(row.get("crew_ids") or []), *default["crew_ids"]])
    if default["team_ids"]:
        merged["team_ids"] = _dedupe_texts([*(row.get("team_ids") or []), *default["team_ids"]])
    if default["reports_to_user_id"]:
        merged["reports_to_user_id"] = default["reports_to_user_id"]
    if default["employee_id"]:
        merged["employee_id"] = default["employee_id"]
    await db[COLLECTION_IDENTITY_PROJECTIONS].update_one({"id": row["id"]}, {"$set": merged})
    return merged


async def list_identity_projections(db, *, limit: int = 200) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_IDENTITY_PROJECTIONS].find({"identity_source": {"$ne": ""}}, {"_id": 0}).sort("updated_at", -1).limit(limit)
    return [row async for row in cur]


async def _load_dynamic_context(db, projection: Dict[str, Any], actor: Dict[str, Any]) -> Dict[str, Any]:
    context = dict(projection)
    try:
        if "project_manager" in (projection.get("active_roles") or []) or actor.get("_actor") == "pm":
            from pm_auth import compute_pm_scope  # noqa: PLC0415

            scope = await compute_pm_scope(db, actor)
            if getattr(scope, "project_numbers", None):
                context["project_numbers"] = _dedupe_texts(list(scope.project_numbers or []))
    except Exception:
        pass
    active_delegations = [
        row
        async for row in db[COLLECTION_DELEGATIONS].find(
            {
                "delegate_user_id": projection.get("canonical_user_id"),
                "status": "active",
                "$or": [{"expires_at": ""}, {"expires_at": {"$gt": _now_iso()}}],
            },
            {"_id": 0},
        )
    ]
    context["delegations"] = active_delegations
    context["delegated_permissions"] = _dedupe_texts(
        [perm for row in active_delegations for perm in _ensure_list(row.get("permissions"))]
    )
    context["temporary_authority"] = [row.get("id") for row in active_delegations]
    return context


def _effective_permissions(registry: Dict[str, Any], projection: Dict[str, Any]) -> List[str]:
    permissions = list(projection.get("direct_permissions") or [])
    roles = list(projection.get("active_roles") or [])
    role_map = dict(registry.get("roles") or {})
    for role_id in roles:
        permissions.extend(role_map.get(role_id, {}).get("permissions") or [])
    permissions.extend(projection.get("delegated_permissions") or [])
    return _dedupe_texts(permissions)


def _actor_matches_rule(actor_user_id: str, actor_email: str, resource: Dict[str, Any], forbidden_paths: List[str]) -> bool:
    for path in forbidden_paths:
        parts = [segment for segment in path.split(".") if segment]
        cursor: Any = resource
        for part in parts:
            if not isinstance(cursor, dict):
                cursor = None
                break
            cursor = cursor.get(part)
        if cursor and str(cursor) in {actor_user_id, actor_email}:
            return True
    return False


async def _write_audit(db, *, kind: str, payload: Dict[str, Any]) -> None:
    row = {"id": str(uuid.uuid4()), "kind": kind, "created_at": _now_iso(), **payload}
    await db[COLLECTION_AUDIT].insert_one(dict(row))


async def record_governance_decision(
    db,
    *,
    projection: Dict[str, Any],
    action_key: str,
    resource_type: str,
    resource_id: str,
    resource: Dict[str, Any],
    policy_id: str,
    decision: str,
    reason: str,
    required_permissions: List[str],
    approval_required: bool,
    delegation_used: bool,
    override_used: bool,
    denial_code: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    correlation_id = attach_correlation({"id": resource_id, "doc_id": resource_id, "project_number": _clean(resource.get("project_number"))})
    row = {
        "id": str(uuid.uuid4()),
        "canonical_user_id": projection.get("canonical_user_id"),
        "actor_email": projection.get("email"),
        "actor_roles": list(projection.get("active_roles") or []),
        "action_key": action_key,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "policy_id": policy_id,
        "policy_version": _clean(resource.get("policy_version") or "1.0"),
        "decision": decision,
        "reason": reason,
        "denial_code": denial_code,
        "required_permissions": required_permissions,
        "approval_required": approval_required,
        "delegation_used": delegation_used,
        "override_used": override_used,
        "correlation_id": correlation_id,
        "causation_ids": _dedupe_texts([resource_id, _clean(resource.get("id"))]),
        "evidence": dict(evidence or {}),
        "decided_at": _now_iso(),
    }
    await db[COLLECTION_DECISIONS].insert_one(dict(row))
    await _write_audit(db, kind="decision", payload=row)
    governance_ref = {"id": row["id"], "doc_id": row["id"], "project_number": _clean(resource.get("project_number")), "_trust_cid": correlation_id}
    await emit_record_created(
        db,
        workflow="enterprise-governance",
        record=governance_ref,
        module="services/enterprise_governance.py:record_governance_decision",
        event_name=f"governance.decision.{decision}",
    )
    await emit_workflow_stage(
        db,
        workflow="enterprise-governance",
        stage="actor_reviewed",
        record=governance_ref,
        module="services/enterprise_governance.py:record_governance_decision",
        status="ok" if decision == "allow" else "failed",
        event_name=f"governance.decision.{decision}",
        failure_reason=reason if decision != "allow" else None,
    )
    return row


async def evaluate_governance_action(
    db,
    *,
    actor: Dict[str, Any],
    action_key: str,
    resource_type: str,
    resource_id: str,
    resource: Optional[Dict[str, Any]] = None,
    requested_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    registry = await get_enterprise_governance_registry(db)
    projection = await ensure_identity_projection(db, actor)
    projection = await _load_dynamic_context(db, projection, actor)
    policy = dict((registry.get("policies") or {}).get(action_key if action_key in (registry.get("policies") or {}) else {
        "operational_case.close": "operational_case_close_policy",
        "evidence.export": "evidence_export_policy",
        "schedule.update": "schedule_change_policy",
        "forecast.approve": "forecast_approval_policy",
        "baseline.capture": "baseline_protection_policy",
    }.get(action_key, "")) or {})
    if not policy:
        policy = {
            "version": "1.0",
            "action_key": action_key,
            "required_permissions": [action_key],
            "require_project_access": False,
            "require_approval_flow": "",
            "separation_rules": [],
        }
    effective_permissions = _effective_permissions(registry, projection)
    resource_doc = dict(resource or {})
    resource_doc.setdefault("id", resource_id)
    resource_doc.setdefault("project_number", _clean((requested_context or {}).get("project_number") or resource_doc.get("project_number")))
    reason = "allowed"
    decision = "allow"
    denial_code = ""
    approval_required = bool(policy.get("require_approval_flow"))
    delegation_used = bool(projection.get("delegated_permissions"))
    override_used = False
    required_permissions = _ensure_list(policy.get("required_permissions"))
    missing = [perm for perm in required_permissions if perm not in effective_permissions]
    if projection.get("policy_attributes", {}).get("disabled"):
        decision, reason, denial_code = "deny", "Identity is disabled.", "identity_disabled"
    elif projection.get("policy_attributes", {}).get("must_change_password"):
        decision, reason, denial_code = "deny", "Password rotation required before privileged action.", "password_rotation_required"
    elif missing:
        decision, reason, denial_code = "deny", f"Missing required permissions: {', '.join(missing)}", "missing_permission"
    elif policy.get("require_project_access"):
        project_number = _clean(resource_doc.get("project_number") or (requested_context or {}).get("project_number"))
        allowed_projects = set(_ensure_list(projection.get("project_numbers")))
        if project_number and allowed_projects and project_number not in allowed_projects and "system_administrator" not in (projection.get("active_roles") or []):
            decision, reason, denial_code = "deny", f"Project {project_number} is outside the actor governance boundary.", "project_scope_denied"
    if decision == "allow":
        actor_user_id = _clean(projection.get("canonical_user_id"))
        actor_email = _clean(projection.get("email"))
        for rule_id in _ensure_list(policy.get("separation_rules")):
            rule = dict((registry.get("separation_rules") or {}).get(rule_id) or {})
            if _actor_matches_rule(actor_user_id, actor_email, resource_doc, _ensure_list(rule.get("forbidden_actor_match"))):
                decision, reason, denial_code = "deny", f"Separation-of-duties blocked action via {rule_id}.", "separation_of_duties"
                break
    if decision == "allow" and approval_required:
        approval_row = await ensure_approval_request(
            db,
            actor_projection=projection,
            approval_flow_id=_clean(policy.get("require_approval_flow")),
            action_key=action_key,
            resource_type=resource_type,
            resource_id=resource_id,
            resource=resource_doc,
        )
        if approval_row.get("status") != "approved":
            decision, reason, denial_code = "deny", "Approval flow is required and is not yet approved.", "approval_required"
    decision_row = await record_governance_decision(
        db,
        projection=projection,
        action_key=action_key,
        resource_type=resource_type,
        resource_id=resource_id,
        resource=resource_doc,
        policy_id=_clean(policy.get("action_key") or action_key),
        decision=decision,
        reason=reason,
        required_permissions=required_permissions,
        approval_required=approval_required,
        delegation_used=delegation_used,
        override_used=override_used,
        denial_code=denial_code,
        evidence={"requested_context": requested_context or {}},
    )
    return {
        "decision": decision,
        "allowed": decision == "allow",
        "reason": reason,
        "denial_code": denial_code,
        "projection": projection,
        "effective_permissions": effective_permissions,
        "policy": policy,
        "decision_record": decision_row,
    }


async def ensure_approval_request(
    db,
    *,
    actor_projection: Dict[str, Any],
    approval_flow_id: str,
    action_key: str,
    resource_type: str,
    resource_id: str,
    resource: Dict[str, Any],
) -> Dict[str, Any]:
    registry = await get_enterprise_governance_registry(db)
    flow = dict((registry.get("approval_flows") or {}).get(approval_flow_id) or {})
    if not flow:
        return {"status": "not_required"}
    existing = await db[COLLECTION_APPROVAL_REQUESTS].find_one(
        {"approval_flow_id": approval_flow_id, "action_key": action_key, "resource_type": resource_type, "resource_id": resource_id, "status": {"$in": ["pending", "approved"]}},
        {"_id": 0},
    )
    if existing:
        return existing
    row = {
        "id": str(uuid.uuid4()),
        "approval_flow_id": approval_flow_id,
        "action_key": action_key,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_snapshot": resource,
        "requested_by": {
            "user_id": actor_projection.get("canonical_user_id"),
            "email": actor_projection.get("email"),
            "roles": list(actor_projection.get("active_roles") or []),
        },
        "required_roles": list(flow.get("required_roles") or []),
        "min_approvals": int(flow.get("min_approvals") or 1),
        "status": "pending",
        "approvals": [],
        "communications": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db[COLLECTION_APPROVAL_REQUESTS].insert_one(dict(row))
    await _write_audit(db, kind="approval_request_created", payload=row)
    await _emit_governance_communication(
        db,
        event_id="operational_case.pending_verification",
        record={
            "id": row["id"],
            "doc_id": row["id"],
            "project_number": _clean(resource.get("project_number")),
            "case_owner_email": actor_projection.get("email"),
            "case_owner_name": actor_projection.get("display_name"),
            "assigned_role": "admin",
            "preview_ack_sla_minutes": 5,
        },
        context={
            "approval_request_id": row["id"],
            "approval_flow_id": approval_flow_id,
            "required_roles": row["required_roles"],
        },
        actor_label=actor_projection.get("display_name") or actor_projection.get("email") or "governance",
    )
    return row


async def approve_request(
    db,
    *,
    request_id: str,
    actor: Dict[str, Any],
    note: str = "",
) -> Dict[str, Any]:
    projection = await ensure_identity_projection(db, actor)
    row = await db[COLLECTION_APPROVAL_REQUESTS].find_one({"id": request_id}, {"_id": 0})
    if not row:
        raise LookupError(f"Unknown approval request: {request_id}")
    actor_roles = set(projection.get("active_roles") or [])
    if not actor_roles.intersection(set(row.get("required_roles") or [])) and "system_administrator" not in actor_roles:
        raise PermissionError("Approver does not hold a required governance role")
    approvals = list(row.get("approvals") or [])
    existing_actor = {a.get("user_id") for a in approvals}
    if projection.get("canonical_user_id") not in existing_actor:
        approvals.append(
            {
                "user_id": projection.get("canonical_user_id"),
                "email": projection.get("email"),
                "roles": list(actor_roles),
                "note": _clean(note),
                "approved_at": _now_iso(),
            }
        )
    status = "approved" if len(approvals) >= int(row.get("min_approvals") or 1) else "pending"
    await db[COLLECTION_APPROVAL_REQUESTS].update_one(
        {"id": request_id},
        {"$set": {"approvals": approvals, "status": status, "updated_at": _now_iso()}},
    )
    fresh = await db[COLLECTION_APPROVAL_REQUESTS].find_one({"id": request_id}, {"_id": 0})
    await _write_audit(db, kind="approval_request_updated", payload={"request_id": request_id, "status": status, "approver": projection.get("email")})
    return fresh or row


async def create_delegation(
    db,
    *,
    actor: Dict[str, Any],
    delegator_projection: Dict[str, Any],
    delegate_user_id: str,
    delegate_email: str,
    permissions: List[str],
    delegation_type: str,
    reason: str,
    expires_at: str,
) -> Dict[str, Any]:
    await ensure_enterprise_governance_registry(db)
    row = {
        "id": str(uuid.uuid4()),
        "delegator_user_id": delegator_projection.get("canonical_user_id"),
        "delegator_email": delegator_projection.get("email"),
        "delegate_user_id": _clean(delegate_user_id),
        "delegate_email": _clean(delegate_email).lower(),
        "permissions": _dedupe_texts(permissions),
        "delegation_type": _slug(delegation_type) or "temporary_delegation",
        "reason": _clean(reason),
        "created_by": _clean(actor.get("email") or actor.get("name") or actor.get("role")),
        "status": "active",
        "created_at": _now_iso(),
        "starts_at": _now_iso(),
        "expires_at": _clean(expires_at),
    }
    await db[COLLECTION_DELEGATIONS].insert_one(dict(row))
    await _write_audit(db, kind="delegation_created", payload=row)
    return row


async def create_emergency_override(
    db,
    *,
    actor: Dict[str, Any],
    projection: Dict[str, Any],
    action_key: str,
    module_key: str,
    record_type: str,
    record_id: str,
    company_id: str,
    project_number: str,
    denied_policy_id: str,
    justification: str,
    operational_urgency: str,
    evidence: List[str],
    expires_at: str,
) -> Dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "requesting_identity": {
            "user_id": projection.get("canonical_user_id"),
            "email": projection.get("email"),
            "roles": list(projection.get("active_roles") or []),
        },
        "acting_identity": {
            "user_id": projection.get("canonical_user_id"),
            "email": projection.get("email"),
        },
        "company_id": _clean(company_id) or projection.get("company_id") or "masci",
        "project_number": _clean(project_number),
        "module_key": _clean(module_key),
        "record_type": _clean(record_type),
        "record_id": _clean(record_id),
        "requested_capability": action_key,
        "denied_policy_id": _clean(denied_policy_id),
        "justification": _clean(justification),
        "operational_urgency": _clean(operational_urgency),
        "evidence": _dedupe_texts(evidence),
        "required_reviewers": ["system_administrator", "executive"],
        "ack_required": True,
        "status": "pending_review",
        "starts_at": _now_iso(),
        "expires_at": _clean(expires_at),
        "resulting_action": "",
        "correlation_id": attach_correlation({"id": record_id, "doc_id": record_id, "project_number": _clean(project_number)}),
        "causation_ids": _dedupe_texts([record_id, projection.get("canonical_user_id")]),
        "communications": [],
        "disposition": {},
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db[COLLECTION_OVERRIDES].insert_one(dict(row))
    await _write_audit(db, kind="override_created", payload=row)
    await _emit_governance_communication(
        db,
        event_id="operational_case.escalated",
        record={
            "id": row["id"],
            "doc_id": row["id"],
            "project_number": row["project_number"],
            "project_name": row["module_key"],
            "case_owner_email": projection.get("email"),
            "case_owner_name": projection.get("display_name"),
            "assigned_role": "admin",
            "preview_ack_sla_minutes": 5,
        },
        context={"override_id": row["id"], "requested_capability": action_key, "denied_policy_id": denied_policy_id},
        actor_label=projection.get("display_name") or projection.get("email") or "governance-override",
    )
    return row


async def _emit_governance_communication(
    db,
    *,
    event_id: str,
    record: Dict[str, Any],
    context: Dict[str, Any],
    actor_label: str,
) -> Dict[str, Any]:
    try:
        from services.operations_control.control_plane import emit_operational_event  # noqa: PLC0415

        return await emit_operational_event(db, event_id=event_id, record=record, actor_label=actor_label, context=context)
    except Exception:
        return {"event": None, "communications": []}


async def seed_governance_admin_surface(db) -> Dict[str, Any]:
    await ensure_enterprise_governance_registry(db)
    existing = await db[COLLECTION_ORG].find_one({"id": "org-root-masci"}, {"_id": 0})
    if existing:
        return existing
    nodes = [
        {"id": "org-root-masci", "kind": "company", "name": "MASCI", "parent_id": "", "path": ["MASCI"]},
        {"id": "org-division-operations", "kind": "division", "name": "Operations", "parent_id": "org-root-masci", "path": ["MASCI", "Operations"]},
        {"id": "org-department-pm", "kind": "department", "name": "Project Management", "parent_id": "org-division-operations", "path": ["MASCI", "Operations", "Project Management"]},
        {"id": "org-department-field", "kind": "department", "name": "Field Operations", "parent_id": "org-division-operations", "path": ["MASCI", "Operations", "Field Operations"]},
        {"id": "org-department-shop", "kind": "department", "name": "Shop", "parent_id": "org-division-operations", "path": ["MASCI", "Operations", "Shop"]},
        {"id": "org-department-safety", "kind": "department", "name": "Safety", "parent_id": "org-division-operations", "path": ["MASCI", "Operations", "Safety"]},
        {"id": "org-department-hr", "kind": "department", "name": "HR", "parent_id": "org-root-masci", "path": ["MASCI", "HR"]},
    ]
    await db[COLLECTION_ORG].insert_many(nodes)
    return nodes[0]


async def get_governance_overview(db) -> Dict[str, Any]:
    registry = await get_enterprise_governance_registry(db)
    identity_count = await db[COLLECTION_IDENTITY_PROJECTIONS].count_documents({})
    active_delegations = await db[COLLECTION_DELEGATIONS].count_documents({"status": "active"})
    pending_approvals = await db[COLLECTION_APPROVAL_REQUESTS].count_documents({"status": "pending"})
    pending_overrides = await db[COLLECTION_OVERRIDES].count_documents({"status": {"$in": ["pending_review", "active"]}})
    recent_decisions = [
        row
        async for row in db[COLLECTION_DECISIONS].find({}, {"_id": 0}).sort("decided_at", -1).limit(20)
    ]
    denied_recent = sum(1 for row in recent_decisions if row.get("decision") == "deny")
    return {
        "registry_version": registry.get("version"),
        "counts": {
            "roles": len(registry.get("roles") or {}),
            "permissions": len(registry.get("permissions") or {}),
            "policies": len(registry.get("policies") or {}),
            "approval_flows": len(registry.get("approval_flows") or {}),
            "separation_rules": len(registry.get("separation_rules") or {}),
            "identity_projections": identity_count,
            "active_delegations": active_delegations,
            "pending_approvals": pending_approvals,
            "pending_overrides": pending_overrides,
            "recent_denials": denied_recent,
        },
        "recent_decisions": recent_decisions,
    }


async def list_decisions(db, *, limit: int = 200) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_DECISIONS].find({}, {"_id": 0}).sort("decided_at", -1).limit(limit)
    return [row async for row in cur]


async def list_overrides(db, *, limit: int = 200) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_OVERRIDES].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def list_delegations(db, *, limit: int = 200) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_DELEGATIONS].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def list_approval_requests(db, *, limit: int = 200) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_APPROVAL_REQUESTS].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def list_org_nodes(db) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_ORG].find({}, {"_id": 0}).sort([("kind", 1), ("name", 1)])
    return [row async for row in cur]
