"""TRACK 24.17 · Operation registry + shared vocabulary."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional


class OperationCategory(str, Enum):
    HEALTH = "health"
    STORAGE = "storage"
    R2 = "r2"
    BACKUPS = "backups"
    GOVERNANCE = "governance"
    DAILY_REPORTS = "daily_reports"
    AI = "ai"
    DOCUMENTS = "documents"
    PHOTOS = "photos"
    EMAIL = "email"
    DATA_INTEGRITY = "data_integrity"
    QUEUES = "queues"
    SECURITY = "security"


class RiskLevel(str, Enum):
    INFO = "info"
    SAFE_CLEANUP = "safe_cleanup"
    DATA_MIGRATION = "data_migration"
    DESTRUCTIVE = "destructive"
    EXTERNAL_PROVIDER = "external_provider"
    SECURITY_SENSITIVE = "security_sensitive"


class OperationStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"
    DRY_RUN_READY = "dry_run_ready"
    APPLY_READY = "apply_ready"
    COMING_SOON = "coming_soon"


HandlerT = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class Operation:
    """One safely-callable maintenance operation."""

    id: str
    title: str
    description: str
    category: OperationCategory
    risk: RiskLevel
    # Handlers. ``status_fn`` is a lightweight read-only probe for the
    # overview cards. ``dry_run_fn`` returns a preview envelope with a
    # server-issued ``dry_run_id``. ``apply_fn`` performs the actual
    # mutation and requires the ``dry_run_id`` if the operation is
    # destructive/data_migration.
    status_fn: Optional[HandlerT] = None
    dry_run_fn: Optional[HandlerT] = None
    apply_fn: Optional[HandlerT] = None
    # Human-readable declarations shown in the UI as truthful contracts.
    reads: List[str] = field(default_factory=list)
    writes: List[str] = field(default_factory=list)
    never_touches: List[str] = field(default_factory=list)
    # High-risk operations require this exact phrase in the payload.
    confirmation_phrase: Optional[str] = None
    # If true, ``apply_fn`` must be preceded by a valid recent dry-run.
    requires_dry_run: bool = False
    # Absent apply_fn means the OCC UI will render this as manual-required.
    manual_reason: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "risk": self.risk.value,
            "reads": list(self.reads),
            "writes": list(self.writes),
            "never_touches": list(self.never_touches),
            "requires_dry_run": self.requires_dry_run,
            "requires_confirmation": bool(self.confirmation_phrase),
            "has_dry_run": self.dry_run_fn is not None,
            "has_apply": self.apply_fn is not None,
            "has_status": self.status_fn is not None,
            "manual_reason": self.manual_reason,
        }


def build_registry(db) -> Dict[str, Operation]:
    """Return the master registry, wiring each Operation to the DB.

    Split by module so future tracks can add operations without editing
    a single monolith.
    """
    from . import (  # noqa: PLC0415
        ai as ai_mod,
        backups as backups_mod,
        daily_reports as dr_mod,
        deploy as deploy_mod,
        email as email_mod,
        governance as governance_mod,
        health as health_mod,
        integrations as integrations_mod,
        queues as queues_mod,
        r2 as r2_mod,
        security as security_mod,
        storage as storage_mod,
    )

    ops: Dict[str, Operation] = {}

    def add(o: Operation) -> None:
        if o.id in ops:
            raise ValueError(f"duplicate operation id: {o.id}")
        ops[o.id] = o

    # Track 25.01 Phase C: ``deploy_mod``, ``integrations_mod`` and
    # ``queues_mod`` fold the scattered maintenance surfaces
    # (deploy-readiness · deploy-recovery · integration-truth ·
    # operations-dashboard · scheduler-runs) into OCC as first-class
    # read-only operations.
    for module in (
        health_mod, deploy_mod, integrations_mod, queues_mod,
        storage_mod, governance_mod, r2_mod, backups_mod, dr_mod,
        ai_mod, email_mod, security_mod,
    ):
        for op in module.operations(db):
            add(op)
    return ops


def _registry_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


def build_operations_control_plane_registry() -> Dict[str, Any]:
    """Return the constitutional WP-14 control-plane registry.

    This registry is the sole authority for:
    - operational workflows
    - registered operational events
    - communication intents
    - template contracts
    - transport providers
    - escalation policies

    Operational code must validate against this registry before emitting
    events or dispatching communications.
    """

    principles = [
        {
            "id": "operational_truth_first",
            "title": "Operational Truth First Principle",
            "statement": (
                "Operational communications are derived from canonical operational truth and "
                "must never become a second source of truth."
            ),
        },
        {
            "id": "registry_before_execution",
            "title": "Registry Before Execution Principle",
            "statement": (
                "No workflow, event, template, escalation, or transport policy may run unless it "
                "is registered in the Operational Registry and Event Catalog first."
            ),
        },
        {
            "id": "transport_independence",
            "title": "Operational Transport Independence Principle",
            "statement": (
                "Operational Communications shall never depend on a specific delivery provider. "
                "Every communication is generated once by the canonical Communications Engine, then "
                "delivered through one or more pluggable transport providers. Replacing or adding a "
                "provider must not require changes to workflow logic."
            ),
        },
        {
            "id": "operational_intent",
            "title": "Operational Intent Principle",
            "statement": (
                "Operational events express operational intent, not implementation. Events declare "
                "that communication, approval, escalation, or action is required while the "
                "Operations Control Plane decides how, when, to whom, and through which transport "
                "those requirements are fulfilled according to canonical registry policy."
            ),
        },
        {
            "id": "preview_fail_safe_capture",
            "title": "Preview Fail-safe Capture Principle",
            "statement": (
                "Preview environments must capture delivery attempts in a fully auditable way and "
                "must not risk unintended live notifications."
            ),
        },
    ]

    workflows = {
        "oppc.daily_report_to_oppc": {
            "id": "oppc.daily_report_to_oppc",
            "title": "Daily Report → OPPC Proof Chain",
            "source_of_truth": ["daily_reports", "jobs_master", "trust_spine_events"],
            "description": (
                "Canonical proof chain that turns a submitted Daily Report into registered events, "
                "communication intents, acknowledgements, escalations, and evidence for OPPC."
            ),
            "trust_workflow": "oppc-daily-report-proof-chain",
            "compatibility_workflows": ["daily-report"],
            "record_type": "daily_report",
        },
    }

    event_catalog = {
        "oppc.daily_report.submitted": {
            "id": "oppc.daily_report.submitted",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Daily Report submitted",
            "severity": "info",
            "operational_intent": "communication_required",
            "source_collection": "daily_reports",
            "communication_intent_ids": ["oppc.daily_report.notify_project_team"],
            "description": (
                "A Daily Report was submitted and OPPC communication is required for project-team "
                "visibility and audit continuity."
            ),
            "evidence_contract": [
                "daily_report.id",
                "daily_report.doc_id",
                "daily_report.project_number",
                "trust_spine.correlation_id",
            ],
        },
        "oppc.daily_report.pending_review": {
            "id": "oppc.daily_report.pending_review",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Daily Report pending review",
            "severity": "warning",
            "operational_intent": "communication_required",
            "source_collection": "daily_reports",
            "communication_intent_ids": ["oppc.daily_report.review_queue"],
            "description": (
                "A Daily Report entered the office review queue and the review board must be notified "
                "through the registered communications engine."
            ),
            "evidence_contract": [
                "daily_report.lifecycle_state",
                "daily_report.report_date",
                "trust_spine.correlation_id",
            ],
        },
        "oppc.daily_report.ack_overdue": {
            "id": "oppc.daily_report.ack_overdue",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Daily Report acknowledgement overdue",
            "severity": "critical",
            "operational_intent": "escalation_required",
            "source_collection": "operations_control_plane_communications",
            "communication_intent_ids": ["oppc.daily_report.escalate_review_board"],
            "description": (
                "A required Daily Report communication passed its acknowledgement SLA and must be "
                "escalated according to canonical policy."
            ),
            "evidence_contract": [
                "communication.id",
                "communication.ack_due_at",
                "communication.escalation_policy_id",
            ],
        },
    }

    communication_intents = {
        "oppc.daily_report.notify_project_team": {
            "id": "oppc.daily_report.notify_project_team",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Notify Daily Report project team",
            "recipient_strategy": "project_pm_distribution",
            "policy_evaluator": "default_daily_report_policy",
            "template_id": "oppc.daily_report.submitted.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": True,
            "ack_sla_minutes": 720,
            "closure_mode": "ack_or_escalate",
            "escalation_policy_id": "oppc.daily_report.review_ack",
            "description": (
                "Notify the responsible PM distribution and create a governed audit trail for the "
                "Daily Report entering the OPPC proof chain."
            ),
        },
        "oppc.daily_report.review_queue": {
            "id": "oppc.daily_report.review_queue",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Notify Daily Report review board",
            "recipient_strategy": "daily_report_review_board",
            "policy_evaluator": "default_review_queue_policy",
            "template_id": "oppc.daily_report.pending_review.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": True,
            "ack_sla_minutes": 240,
            "closure_mode": "ack_or_escalate",
            "escalation_policy_id": "oppc.daily_report.review_ack",
            "description": (
                "Notify the Daily Report review board when office review is required."
            ),
        },
        "oppc.daily_report.escalate_review_board": {
            "id": "oppc.daily_report.escalate_review_board",
            "workflow_id": "oppc.daily_report_to_oppc",
            "title": "Escalate overdue Daily Report communication",
            "recipient_strategy": "ops_admin_escalation",
            "policy_evaluator": "default_escalation_policy",
            "template_id": "oppc.daily_report.escalation.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": False,
            "ack_sla_minutes": 0,
            "closure_mode": "delivery_only",
            "escalation_policy_id": "oppc.daily_report.review_ack",
            "description": (
                "Escalate overdue Daily Report communications to the operational admin lane."
            ),
        },
    }

    templates = {
        "oppc.daily_report.submitted.v1": {
            "id": "oppc.daily_report.submitted.v1",
            "channel_family": "daily_report",
            "title_template": "Daily Report submitted — {project_label}",
            "message_template": (
                "{doc_id} for {report_date} entered the OPPC proof chain. "
                "Communication is required under the registered control-plane policy."
            ),
            "email_note": (
                "This message was created from a registered operational event and issued through the "
                "Operations Control Plane."
            ),
        },
        "oppc.daily_report.pending_review.v1": {
            "id": "oppc.daily_report.pending_review.v1",
            "channel_family": "daily_report",
            "title_template": "Daily Report pending review — {project_label}",
            "message_template": (
                "{doc_id} for {report_date} is waiting for office review. "
                "A review acknowledgement is required."
            ),
            "email_note": (
                "The Daily Report review board was notified from a canonical communication intent."
            ),
        },
        "oppc.daily_report.escalation.v1": {
            "id": "oppc.daily_report.escalation.v1",
            "channel_family": "daily_report",
            "title_template": "Daily Report escalation — {project_label}",
            "message_template": (
                "{doc_id} exceeded its acknowledgement SLA. Operational escalation is required now."
            ),
            "email_note": (
                "This escalation was generated by canonical policy after an acknowledgement SLA breach."
            ),
        },
    }

    transport_providers = {
        "in_app.notification_feed": {
            "id": "in_app.notification_feed",
            "channel": "in_app",
            "provider": "notifications_collection",
            "preview_behavior": "materialize",
            "production_behavior": "materialize",
            "description": "Writes governed bell-feed notifications into the canonical notifications collection.",
        },
        "email.resend": {
            "id": "email.resend",
            "channel": "email",
            "provider": "resend",
            "preview_behavior": "safe_capture",
            "production_behavior": "provider_live",
            "description": "Pluggable email transport. Preview captures; production uses Resend when validated.",
        },
    }

    escalation_policies = {
        "oppc.daily_report.review_ack": {
            "id": "oppc.daily_report.review_ack",
            "title": "Daily Report acknowledgement SLA",
            "description": "Escalate when a required Daily Report communication is not acknowledged within its SLA window.",
            "overdue_transport_ids": ["in_app.notification_feed", "email.resend"],
            "overdue_event_id": "oppc.daily_report.ack_overdue",
            "max_escalations": 1,
        },
    }

    registry = {
        "version": "operations-control-plane-v1",
        "baseline_name": "Operations Control Plane v1",
        "principles": principles,
        "workflows": workflows,
        "event_catalog": event_catalog,
        "communication_intents": communication_intents,
        "templates": templates,
        "transport_providers": transport_providers,
        "escalation_policies": escalation_policies,
    }
    registry["registry_hash"] = _registry_hash(registry)
    return registry


def operations_control_plane_registry_summary() -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    return {
        "version": registry["version"],
        "baseline_name": registry["baseline_name"],
        "registry_hash": registry["registry_hash"],
        "principles": registry["principles"],
        "counts": {
            "workflows": len(registry["workflows"]),
            "events": len(registry["event_catalog"]),
            "communication_intents": len(registry["communication_intents"]),
            "templates": len(registry["templates"]),
            "transports": len(registry["transport_providers"]),
            "escalation_policies": len(registry["escalation_policies"]),
        },
        "workflow_ids": sorted(registry["workflows"].keys()),
        "event_ids": sorted(registry["event_catalog"].keys()),
        "communication_intent_ids": sorted(registry["communication_intents"].keys()),
        "transport_ids": sorted(registry["transport_providers"].keys()),
        "template_ids": sorted(registry["templates"].keys()),
        "escalation_policy_ids": sorted(registry["escalation_policies"].keys()),
    }


def get_registered_workflow(workflow_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    workflow = (registry.get("workflows") or {}).get(workflow_id)
    if not workflow:
        raise ValueError(f"workflow is not registered: {workflow_id}")
    return workflow


def get_registered_event(event_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    event = (registry.get("event_catalog") or {}).get(event_id)
    if not event:
        raise ValueError(f"event is not registered: {event_id}")
    return event


def get_registered_communication_intent(intent_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    intent = (registry.get("communication_intents") or {}).get(intent_id)
    if not intent:
        raise ValueError(f"communication intent is not registered: {intent_id}")
    return intent


def get_registered_template(template_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    template = (registry.get("templates") or {}).get(template_id)
    if not template:
        raise ValueError(f"template is not registered: {template_id}")
    return template


def get_registered_transport(transport_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    transport = (registry.get("transport_providers") or {}).get(transport_id)
    if not transport:
        raise ValueError(f"transport is not registered: {transport_id}")
    return transport


def get_registered_escalation_policy(policy_id: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    policy = (registry.get("escalation_policies") or {}).get(policy_id)
    if not policy:
        raise ValueError(f"escalation policy is not registered: {policy_id}")
    return policy
