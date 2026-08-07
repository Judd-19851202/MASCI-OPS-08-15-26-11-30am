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
        {
            "id": "operational_case_principle",
            "title": "Operational Case Principle",
            "statement": (
                "Every significant operational event shall be capable of being reconstructed as a "
                "complete Operational Case from canonical records. Operational Cases do not create "
                "or replace operational truth. They assemble, link, preserve, and present "
                "authoritative records, communications, acknowledgements, escalations, decisions, "
                "recovery actions, evidence, and Trust Spine events into one governed investigative "
                "and operational view. No Case may silently alter, duplicate, reinterpret, or "
                "supersede the authoritative source records it references."
            ),
        },
        {
            "id": "canonical_truth_rule",
            "title": "Canonical Truth Rule",
            "statement": "Every value displayed in an Operational Case must identify its canonical source.",
        },
        {
            "id": "no_silent_mutation_rule",
            "title": "No Silent Mutation Rule",
            "statement": "A Case may not directly modify authoritative records unless it invokes the existing authorized workflow owned by that canonical system.",
        },
        {
            "id": "reconstruction_rule",
            "title": "Reconstruction Rule",
            "statement": "A Case must be reconstructable from persisted canonical records and Trust Spine evidence after refresh, restart, logout/login, deployment, restore, or operator change.",
        },
        {
            "id": "referential_integrity_rule",
            "title": "Referential Integrity Rule",
            "statement": "Every Case link must resolve to a valid canonical record or explicitly surface unavailable, archived, deleted-under-policy, or access-restricted state.",
        },
        {
            "id": "immutable_history_rule",
            "title": "Immutable History Rule",
            "statement": "Case history, acknowledgement history, escalation history, ownership changes, severity changes, and closure decisions must be append-only and auditable.",
        },
        {
            "id": "case_assembly_rule",
            "title": "Case Assembly Rule",
            "statement": "Operational Cases assemble truth. They do not invent truth.",
        },
        {
            "id": "case_creation_policy_principle",
            "title": "Case Creation Policy Principle",
            "statement": "Automatic Operational Case creation must be driven only by versioned registry policy applied to registered operational events. The decision to create, suppress, suggest, link, or update a Case must be deterministic, explainable, auditable, and reproducible from persisted inputs.",
        },
        {
            "id": "one_event_one_governed_outcome",
            "title": "One Event, One Governed Outcome",
            "statement": "For the same originating event and policy version, repeated processing must produce the same governed result: create one Case, update the existing Case, link to an existing Case, suggest Case creation, or suppress Case creation with a recorded reason. Retries and replays must not create duplicates.",
        },
        {
            "id": "proof_record_isolation",
            "title": "Proof Record Isolation",
            "statement": "Preview proof records must remain clearly identified as certification evidence, use preview-safe communications, allow accelerated SLA only within test scope, preserve production defaults, remain visible in Trust Spine/evidence, and never masquerade as production records.",
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
        "oppc.operational_case_management": {
            "id": "oppc.operational_case_management",
            "title": "Operational Case Management",
            "source_of_truth": [
                "daily_reports",
                "operations_control_plane_events",
                "operations_control_plane_communications",
                "operational_variance_reviews",
                "trust_spine_events",
                "tasks",
            ],
            "description": (
                "Governed assembly of authoritative operational truth into one reconstructable "
                "Operational Case without duplicating the source systems."
            ),
            "trust_workflow": "oppc-operational-case-management",
            "compatibility_workflows": [],
            "record_type": "operational_case",
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
        "operational_case.created": {
            "id": "operational_case.created",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case created",
            "severity": "warning",
            "operational_intent": "case_created",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.opened"],
            "description": "A governed Operational Case was created from a registered policy decision.",
            "evidence_contract": ["case.case_id", "case.origin.originating_event_id", "case.policy_decision"],
        },
        "operational_case.assigned": {
            "id": "operational_case.assigned",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case assigned",
            "severity": "info",
            "operational_intent": "case_assignment_required",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.assigned"],
            "description": "A Case owner or assigned role changed under governed policy.",
            "evidence_contract": ["case.case_id", "case.case_owner", "case.assigned_role"],
        },
        "operational_case.escalated": {
            "id": "operational_case.escalated",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case escalated",
            "severity": "critical",
            "operational_intent": "case_escalation_required",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.escalated"],
            "description": "A Case crossed an escalation threshold and requires higher attention.",
            "evidence_contract": ["case.case_id", "case.status", "case.escalation_state"],
        },
        "operational_case.pending_verification": {
            "id": "operational_case.pending_verification",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case pending verification",
            "severity": "warning",
            "operational_intent": "case_pending_verification",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.pending_verification"],
            "description": "A Case is awaiting final verification before resolution/closure.",
            "evidence_contract": ["case.case_id", "case.status", "case.lifecycle"],
        },
        "operational_case.resolved": {
            "id": "operational_case.resolved",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case resolved",
            "severity": "info",
            "operational_intent": "case_resolved",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.resolved"],
            "description": "A Case resolution was proposed or recorded.",
            "evidence_contract": ["case.case_id", "case.closure", "case.status"],
        },
        "operational_case.closed": {
            "id": "operational_case.closed",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case closed",
            "severity": "info",
            "operational_intent": "case_closed",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.closed"],
            "description": "A Case closure was authorized and recorded.",
            "evidence_contract": ["case.case_id", "case.closure", "case.audit"],
        },
        "operational_case.reopened": {
            "id": "operational_case.reopened",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case reopened",
            "severity": "warning",
            "operational_intent": "case_reopened",
            "source_collection": "operations_control_plane_cases",
            "communication_intent_ids": ["operational_case.reopened"],
            "description": "A previously closed Case was reopened under governed policy.",
            "evidence_contract": ["case.case_id", "case.reopened_at", "case.closure"],
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
                "Daily Report filing and project-team distribution."
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
        "operational_case.opened": {
            "id": "operational_case.opened",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case opened",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_open_policy",
            "template_id": "operational_case.opened.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": True,
            "ack_sla_minutes": 240,
            "closure_mode": "ack_or_escalate",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify accountable ownership that a new Operational Case has been opened.",
        },
        "operational_case.assigned": {
            "id": "operational_case.assigned",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case assigned",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_assignment_policy",
            "template_id": "operational_case.assigned.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": False,
            "ack_sla_minutes": 0,
            "closure_mode": "delivery_only",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify Case ownership changes.",
        },
        "operational_case.escalated": {
            "id": "operational_case.escalated",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case escalated",
            "recipient_strategy": "case_escalation_path",
            "policy_evaluator": "default_case_escalation_policy",
            "template_id": "operational_case.escalated.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": True,
            "ack_sla_minutes": 120,
            "closure_mode": "ack_or_escalate",
            "escalation_policy_id": "operational_case.ack",
            "description": "Escalate a Case to higher operational authority.",
        },
        "operational_case.pending_verification": {
            "id": "operational_case.pending_verification",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case pending verification",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_pending_verification_policy",
            "template_id": "operational_case.pending_verification.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": False,
            "ack_sla_minutes": 0,
            "closure_mode": "delivery_only",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify pending verification status for a Case.",
        },
        "operational_case.resolved": {
            "id": "operational_case.resolved",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case resolved",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_resolution_policy",
            "template_id": "operational_case.resolved.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": False,
            "ack_sla_minutes": 0,
            "closure_mode": "delivery_only",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify that a Case has been resolved.",
        },
        "operational_case.closed": {
            "id": "operational_case.closed",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case closed",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_closure_policy",
            "template_id": "operational_case.closed.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": False,
            "ack_sla_minutes": 0,
            "closure_mode": "delivery_only",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify that a Case has been closed.",
        },
        "operational_case.reopened": {
            "id": "operational_case.reopened",
            "workflow_id": "oppc.operational_case_management",
            "title": "Operational Case reopened",
            "recipient_strategy": "case_primary_owner_and_admin",
            "policy_evaluator": "default_case_reopen_policy",
            "template_id": "operational_case.reopened.v1",
            "transport_ids": ["in_app.notification_feed", "email.resend"],
            "ack_required": True,
            "ack_sla_minutes": 240,
            "closure_mode": "ack_or_escalate",
            "escalation_policy_id": "operational_case.ack",
            "description": "Notify that a Case has been reopened.",
        },
    }

    templates = {
        "oppc.daily_report.submitted.v1": {
            "id": "oppc.daily_report.submitted.v1",
            "channel_family": "daily_report",
            "title_template": "Daily Report submitted — {project_label}",
            "message_template": (
                "{doc_id} for {report_date} has been filed and sent to the project team. "
                "Review the attached Daily Report and follow the standard project closeout process."
            ),
            "email_note": (
                "This Daily Report was filed in MASCI OPS and sent to the assigned project distribution."
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
        "operational_case.opened.v1": {
            "id": "operational_case.opened.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case opened — {doc_id}",
            "message_template": "A governed Operational Case has been opened for {project_label}.",
            "email_note": "This Case was created automatically by registered policy and remains linked to canonical operational truth.",
        },
        "operational_case.assigned.v1": {
            "id": "operational_case.assigned.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case assigned — {doc_id}",
            "message_template": "Ownership or assignment changed for Operational Case {doc_id}.",
            "email_note": "Assignment was recorded through the Operations Control Plane case workflow.",
        },
        "operational_case.escalated.v1": {
            "id": "operational_case.escalated.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case escalated — {doc_id}",
            "message_template": "Operational Case {doc_id} crossed an escalation threshold and needs action now.",
            "email_note": "This escalation was generated by canonical Case policy.",
        },
        "operational_case.pending_verification.v1": {
            "id": "operational_case.pending_verification.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case pending verification — {doc_id}",
            "message_template": "Operational Case {doc_id} is waiting for verification before closure.",
            "email_note": "Verification remains required before policy-driven closure.",
        },
        "operational_case.resolved.v1": {
            "id": "operational_case.resolved.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case resolved — {doc_id}",
            "message_template": "Operational Case {doc_id} has a proposed or recorded resolution.",
            "email_note": "Resolution was recorded in the canonical Case ledger.",
        },
        "operational_case.closed.v1": {
            "id": "operational_case.closed.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case closed — {doc_id}",
            "message_template": "Operational Case {doc_id} has been closed under policy.",
            "email_note": "Closure was authorized and captured by the Operations Control Plane.",
        },
        "operational_case.reopened.v1": {
            "id": "operational_case.reopened.v1",
            "channel_family": "operational_case",
            "title_template": "Operational Case reopened — {doc_id}",
            "message_template": "Operational Case {doc_id} has been reopened and requires attention again.",
            "email_note": "The original closure record remains preserved; this is a governed reopening event.",
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
        "operational_case.ack": {
            "id": "operational_case.ack",
            "title": "Operational Case acknowledgement SLA",
            "description": "Escalate when a required Case acknowledgement is not completed within policy.",
            "overdue_transport_ids": ["in_app.notification_feed", "email.resend"],
            "overdue_event_id": "operational_case.escalated",
            "max_escalations": 1,
        },
    }

    case_types_raw = [
        ("daily_report_exception", "Daily Report Exception", "daily_reports", "moderate", ["informational", "low", "moderate", "high", "critical"]),
        ("schedule_variance", "Schedule Variance", "oppc_variance", "moderate", ["low", "moderate", "high", "critical", "emergency"]),
        ("forecast_change", "Forecast Change", "forecasting", "moderate", ["low", "moderate", "high", "critical"]),
        ("production_shortfall", "Production Shortfall", "oppc_variance", "high", ["moderate", "high", "critical", "emergency"]),
        ("cost_code_variance", "Cost Code Variance", "oppc_variance", "moderate", ["low", "moderate", "high", "critical"]),
        ("recovery_plan", "Recovery Plan", "recovery", "high", ["moderate", "high", "critical"]),
        ("payroll_exception", "Payroll Exception", "payroll", "moderate", ["low", "moderate", "high"]),
        ("labor_staffing_constraint", "Labor or Staffing Constraint", "staffing", "moderate", ["low", "moderate", "high", "critical"]),
        ("equipment_failure", "Equipment Failure", "equipment", "high", ["moderate", "high", "critical", "emergency"]),
        ("fleet_dispatch_conflict", "Fleet or Dispatch Conflict", "dispatch", "moderate", ["low", "moderate", "high"]),
        ("material_delay", "Material Delay", "materials", "moderate", ["low", "moderate", "high", "critical"]),
        ("plant_capacity_constraint", "Plant Capacity Constraint", "plant", "moderate", ["low", "moderate", "high", "critical"]),
        ("survey_constraint", "Survey Constraint", "survey", "moderate", ["low", "moderate", "high"]),
        ("testing_inspection_constraint", "Testing or Inspection Constraint", "inspection", "moderate", ["low", "moderate", "high", "critical"]),
        ("quality_issue", "Quality Issue", "quality", "high", ["moderate", "high", "critical", "emergency"]),
        ("safety_event", "Safety Event", "safety", "critical", ["high", "critical", "emergency"]),
        ("environmental_event", "Environmental Event", "environment", "high", ["moderate", "high", "critical", "emergency"]),
        ("utility_conflict", "Utility Conflict", "utilities", "moderate", ["moderate", "high", "critical"]),
        ("owner_engineer_delay", "Owner or Engineer Delay", "owner_engineer", "moderate", ["low", "moderate", "high"]),
        ("subcontractor_performance_issue", "Subcontractor Performance Issue", "subcontractor", "moderate", ["low", "moderate", "high", "critical"]),
        ("executive_decision", "Executive Decision", "executive", "high", ["moderate", "high", "critical"]),
        ("operational_communication_failure", "Operational Communication Failure", "communications", "high", ["moderate", "high", "critical"]),
        ("escalation_failure", "Escalation Failure", "communications", "critical", ["high", "critical", "emergency"]),
        ("data_trust_integrity_issue", "Data Trust or Integrity Issue", "data_trust", "high", ["moderate", "high", "critical"]),
        ("general_operational_exception", "General Operational Exception", "operations", "moderate", ["informational", "low", "moderate", "high"]),
    ]
    case_allowed_statuses = [
        "DRAFT", "OPEN", "ACKNOWLEDGEMENT_REQUIRED", "UNDER_REVIEW", "INVESTIGATING",
        "ACTION_REQUIRED", "RECOVERY_ACTIVE", "ESCALATED", "MONITORING", "PENDING_VERIFICATION",
        "RESOLVED", "CLOSED", "REOPENED", "ARCHIVED", "CANCELLED", "DUPLICATE",
    ]
    case_types = {
        type_id: {
            "id": type_id,
            "display_name": label,
            "description": label,
            "canonical_owning_domain": owner,
            "default_severity": default_severity,
            "allowed_severity_range": severity_range,
            "eligible_originating_event_types": ["oppc.daily_report.submitted", "oppc.daily_report.pending_review"],
            "eligible_related_record_types": ["daily_report", "communication", "variance", "task", "baseline", "evidence_package"],
            "acknowledgement_expectations": "required_when_case_opened",
            "escalation_eligibility": True,
            "retention_class": "operations_control_plane_v1",
            "closure_requirements": ["status_history", "root_cause_or_reason", "evidence_package"],
            "evidence_requirements": ["trust_spine", "communications", "source_record"],
            "required_roles": ["admin", "pm"],
            "allowed_statuses": case_allowed_statuses,
            "state": "active",
            "version": "1.0",
        }
        for type_id, label, owner, default_severity, severity_range in case_types_raw
    }

    case_lifecycle = {
        "statuses": case_allowed_statuses,
        "default_status": "OPEN",
        "transitions": {
            "DRAFT": ["OPEN", "CANCELLED"],
            "OPEN": ["ACKNOWLEDGEMENT_REQUIRED", "UNDER_REVIEW", "DUPLICATE"],
            "ACKNOWLEDGEMENT_REQUIRED": ["UNDER_REVIEW", "ESCALATED"],
            "UNDER_REVIEW": ["INVESTIGATING", "ACTION_REQUIRED", "ESCALATED"],
            "INVESTIGATING": ["ACTION_REQUIRED", "RECOVERY_ACTIVE", "ESCALATED"],
            "ACTION_REQUIRED": ["RECOVERY_ACTIVE", "MONITORING", "ESCALATED"],
            "RECOVERY_ACTIVE": ["MONITORING", "PENDING_VERIFICATION", "ESCALATED"],
            "ESCALATED": ["UNDER_REVIEW", "ACTION_REQUIRED", "RECOVERY_ACTIVE", "PENDING_VERIFICATION"],
            "MONITORING": ["PENDING_VERIFICATION", "ESCALATED"],
            "PENDING_VERIFICATION": ["RESOLVED", "ESCALATED"],
            "RESOLVED": ["CLOSED", "REOPENED"],
            "CLOSED": ["REOPENED", "ARCHIVED"],
            "REOPENED": ["UNDER_REVIEW", "INVESTIGATING"],
            "DUPLICATE": ["ARCHIVED"],
            "CANCELLED": [],
            "ARCHIVED": [],
        },
        "severity_levels": ["informational", "low", "moderate", "high", "critical", "emergency"],
        "priority_levels": ["P4", "P3", "P2", "P1", "P0"],
    }

    case_creation_policies = {
        "oppc.daily_report.submitted": {
            "id": "oppc.daily_report.submitted.case_policy.v1",
            "version": "1.0",
            "event_id": "oppc.daily_report.submitted",
            "default_case_type_id": "daily_report_exception",
            "decision_mode": "auto",
            "eligible_outcomes": ["create", "update", "link", "suggest", "suppress"],
            "create_threshold": 3,
            "proof_scope_accelerated_ack_sla_minutes": 1,
            "proof_scope_requires_flags": ["certification_record", "synthetic_record", "hidden_from_operations"],
            "evaluation_factors": [
                "severity",
                "variance_threshold",
                "forecast_impact",
                "confidence_impact",
                "critical_path_impact",
                "acknowledgement_requirement",
                "escalation_eligibility",
                "recurrence",
                "executive_attention_requirement",
            ],
            "one_event_one_outcome": True,
        }
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
        "case_types": case_types,
        "case_lifecycle": case_lifecycle,
        "case_creation_policies": case_creation_policies,
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
            "case_types": len(registry.get("case_types") or {}),
        },
        "workflow_ids": sorted(registry["workflows"].keys()),
        "event_ids": sorted(registry["event_catalog"].keys()),
        "communication_intent_ids": sorted(registry["communication_intents"].keys()),
        "transport_ids": sorted(registry["transport_providers"].keys()),
        "template_ids": sorted(registry["templates"].keys()),
        "escalation_policy_ids": sorted(registry["escalation_policies"].keys()),
        "case_type_ids": sorted((registry.get("case_types") or {}).keys()),
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
