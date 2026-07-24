from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lib.canonical_status import DEGRADED, DISABLED, MISMATCH, NOT_APPLICABLE, UNVERIFIABLE, VERIFIED

CONTRACT_VERSION = "C2.11"

CANONICAL_OWNER = "CANONICAL_OWNER"
DOMAIN_OWNER = "DOMAIN_OWNER"
DERIVED_CONSUMER = "DERIVED_CONSUMER"
AGGREGATOR = "AGGREGATOR"
VALIDATOR = "VALIDATOR"
LEGACY_COMPATIBILITY = "LEGACY_COMPATIBILITY"
UNREGISTERED = "UNREGISTERED"
DUPLICATE_DERIVATION = "DUPLICATE_DERIVATION"
RETIRED = "RETIRED"

OPEN = "OPEN"
CONFIRMED = "CONFIRMED"
MITIGATED = "MITIGATED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TruthSurface:
    surface_id: str
    surface_name: str
    role: str
    owner_type: str
    canonical_owner_id: Optional[str]
    upstream_owner_ids: List[str]
    owner_endpoint: str
    owner_module: str
    truth_subject: str
    status_authority: str
    kpi_authority: str
    threshold_authority: str
    freshness_authority: str
    evidence_sources: List[str]
    derived_fields: List[str]
    derivation_formula: str
    allowed_status_outputs: List[str]
    operator_surfaces: List[str]
    environment_scope: str
    runtime_reachability: str
    production_reachability: str
    registered_at: str
    contract_version: str
    deprecation_state: str
    audit_reference: str
    contract: str = ""
    duplicate_derivation_keys: List[str] = field(default_factory=list)
    ui_consumer_routes: List[str] = field(default_factory=list)
    capability_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_SURFACES: Dict[str, TruthSurface] = {
    "platform_attestation": TruthSurface(
        surface_id="platform_attestation",
        surface_name="Platform Runtime Attestation",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="platform_attestation",
        upstream_owner_ids=[],
        owner_endpoint="/api/admin/platform/status",
        owner_module="backend/lib/platform_status.py",
        truth_subject="platform_runtime_truth",
        status_authority="platform_attestation",
        kpi_authority="platform_attestation",
        threshold_authority="platform_attestation",
        freshness_authority="platform_attestation",
        evidence_sources=["app.state.runtime_identity_bundle", "FastAPI route registry", "runtime middleware state", "lifespan registry state"],
        derived_fields=[],
        derivation_formula="direct_runtime_attestation",
        allowed_status_outputs=[VERIFIED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["Admin runtime attestation consumers", "Diagnostics and governance trust consumers"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-RUNTIME-ATTESTATION",
        contract="Canonical runtime attestation owner for shared platform truth.",
        ui_consumer_routes=["/admin", "/admin/diagnostics"],
    ),
    "trust_spine": TruthSurface(
        surface_id="trust_spine",
        surface_name="Platform Trust Spine Lifecycle Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="trust_spine",
        upstream_owner_ids=[],
        owner_endpoint="/api/admin/trust-spine",
        owner_module="backend/routes/admin_trust_spine.py",
        truth_subject="workflow_lifecycle_truth",
        status_authority="trust_spine",
        kpi_authority="trust_spine",
        threshold_authority="trust_spine",
        freshness_authority="trust_spine",
        evidence_sources=["trust_spine_events", "backend/lib/trust_spine.py", "WORKFLOW_EXPECTED_STAGES"],
        derived_fields=[],
        derivation_formula="expected_stage_rollup_over_last_24h",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["frontend/src/components/PlatformTrustDashboard.jsx", "frontend/src/components/OperationsTrustCenter.jsx", "frontend/src/components/PlatformTrustValidator.jsx"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-TRUST-SPINE",
        contract="Canonical lifecycle truth owner for workflow health and failure-stage evidence.",
        ui_consumer_routes=["/admin/governance-trust", "/admin/operations-control"],
    ),
    "integration_truth": TruthSurface(
        surface_id="integration_truth",
        surface_name="Integration Truth Surface",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="integration_truth",
        upstream_owner_ids=[],
        owner_endpoint="/api/admin/integrations/truth-status",
        owner_module="backend/routes/integration_truth.py",
        truth_subject="integration_truth",
        status_authority="integration_truth",
        kpi_authority="integration_truth",
        threshold_authority="integration_truth",
        freshness_authority="integration_truth",
        evidence_sources=["os.environ runtime values", "integration_settings", "dr_v2_alias_telemetry_events", "dr_v2_alias_aggregate"],
        derived_fields=[],
        derivation_formula="config_connectivity_activity_truth_model",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, NOT_APPLICABLE],
        operator_surfaces=["frontend/src/pages/admin/IntegrationTruth.jsx"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-INTEGRATION-TRUTH",
        contract="Canonical owner for integration configuration, connectivity, and recent activity truth.",
        ui_consumer_routes=["/admin/integration-truth"],
    ),
    "shared_auth_session": TruthSurface(
        surface_id="shared_auth_session",
        surface_name="Shared Directory Authentication and Session Continuity",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="shared_auth_session",
        upstream_owner_ids=[],
        owner_endpoint="/api/auth/multi-login",
        owner_module="backend/routes/auth_directory_routes.py",
        truth_subject="shared_auth_session_truth",
        status_authority="shared_auth_session",
        kpi_authority="shared_auth_session",
        threshold_authority="shared_auth_session",
        freshness_authority="shared_auth_session",
        evidence_sources=["user_directory", "directory_sessions", "session_activity", "frontend/src/lib/directoryAuth.js", "frontend/src/lib/usePortalHydration.js"],
        derived_fields=["portal_tokens", "must_change_password"],
        derivation_formula="directory_session_plus_portal_token_fanout",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["shared multi-portal sign-in", "route guards", "shared sign-out flows"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-AUTH-SESSION",
        contract="Canonical owner for shared auth, session continuity, and sign-out provenance.",
        ui_consumer_routes=["/sign-in", "/admin/login", "/pm/login", "/hr/login", "/shop/login", "/safety-portal/login", "/dispatch-portal/login"],
        capability_ids=["shared-shell.sign-out.admin"],
    ),
    "shared_admin_shell": TruthSurface(
        surface_id="shared_admin_shell",
        surface_name="Shared Admin Shell",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="shared_admin_shell",
        upstream_owner_ids=["shared_auth_session"],
        owner_endpoint="frontend-shell",
        owner_module="frontend/src/components/AdminShell.jsx",
        truth_subject="shared_admin_shell_truth",
        status_authority="shared_admin_shell",
        kpi_authority="shared_admin_shell",
        threshold_authority="shared_admin_shell",
        freshness_authority="shared_admin_shell",
        evidence_sources=["frontend/src/components/AdminShell.jsx", "frontend/src/components/admin/LegacyAdminModernShell.jsx", "frontend/src/design-system/PortalShell.jsx"],
        derived_fields=["breadcrumbs", "shared portal shell actions"],
        derivation_formula="single_shell_composition",
        allowed_status_outputs=[VERIFIED, DEGRADED],
        operator_surfaces=["Admin OS pages", "shared shell actions"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-ADMIN-SHELL",
        contract="Canonical shared-shell owner for Admin OS presentation and shell actions.",
        ui_consumer_routes=["/admin/*"],
        capability_ids=["shared-shell.sign-out.admin"],
    ),
    "occ_health_aggregator": TruthSurface(
        surface_id="occ_health_aggregator",
        surface_name="OCC Health Aggregator",
        role=AGGREGATOR,
        owner_type="derived",
        canonical_owner_id="platform_attestation",
        upstream_owner_ids=["platform_attestation", "integration_truth", "shared_auth_session"],
        owner_endpoint="/api/admin/occ/health",
        owner_module="backend/routes/occ_health_aggregator.py",
        truth_subject="shared_operational_posture",
        status_authority="derived_from_upstream_owners",
        kpi_authority="derived_from_child_endpoints",
        threshold_authority="occ_health_aggregator",
        freshness_authority="occ_health_aggregator",
        evidence_sources=["child endpoint fanout", "runtime_identity_bundle", "per-card evaluator evidence"],
        derived_fields=["overall_status", "canonical_counts", "root_cause_groups"],
        derivation_formula="fresh_fanout_probe_with_worst_status_and_root_cause_grouping",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, NOT_APPLICABLE],
        operator_surfaces=["frontend/src/pages/OperationsControlCenter.jsx"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T21:20:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-R2-OCC-HEALTH",
        contract="Derived aggregator over upstream canonical owners. Never authoritative over child source truth.",
        ui_consumer_routes=["/admin/operations-control"],
        notes=["Aggregator may not override child canonical owners.", "Probe failure must be disclosed separately from source failure."],
    ),
    "operations_trust_center": TruthSurface(
        surface_id="operations_trust_center",
        surface_name="Operations Trust Center",
        role=DERIVED_CONSUMER,
        owner_type="derived",
        canonical_owner_id="trust_spine",
        upstream_owner_ids=["trust_spine", "platform_attestation"],
        owner_endpoint="/api/admin/operations-trust-center",
        owner_module="backend/routes/admin_operations_trust_center.py",
        truth_subject="shared_operational_trust_score",
        status_authority="derived_from_trust_spine_and_master_data",
        kpi_authority="operations_trust_center",
        threshold_authority="operations_trust_center",
        freshness_authority="trust_spine",
        evidence_sources=["trust spine payload", "master data trust findings", "email_routing_audit_v2", "trust_score_history"],
        derived_fields=["trust_score", "score_band", "score_inputs", "executive_narrative", "operator_actions"],
        derivation_formula="compute_score and compute_categorized_score over canonical trust spine plus master data",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH],
        operator_surfaces=["frontend/src/components/OperationsTrustCenter.jsx"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T21:20:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-R1-OPERATIONS-TRUST-CENTER",
        contract="Derived operational trust score consumer; never canonical platform truth.",
        ui_consumer_routes=["/admin/email"],
        duplicate_derivation_keys=["platform_operational_score"],
        notes=["Derived consumer only. It may not represent itself as canonical platform truth."],
    ),
    "platform_trust_validator": TruthSurface(
        surface_id="platform_trust_validator",
        surface_name="Platform Trust Validator",
        role=VALIDATOR,
        owner_type="derived",
        canonical_owner_id="platform_attestation",
        upstream_owner_ids=["trust_spine", "integration_truth", "platform_attestation"],
        owner_endpoint="/api/admin/platform-trust/validate",
        owner_module="backend/routes/admin_platform_trust.py",
        truth_subject="platform_validation_truth",
        status_authority="validator_only",
        kpi_authority="validator_only",
        threshold_authority="platform_trust_validator",
        freshness_authority="platform_trust_validator",
        evidence_sources=["health/full heartbeat", "email routing status", "pm coverage", "email_routing_audit_v2"],
        derived_fields=["final_band", "red_reasons", "amber_reasons"],
        derivation_formula="defensive validation over admin-safe evidence only",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH],
        operator_surfaces=["frontend/src/components/PlatformTrustValidator.jsx"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-21T21:20:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="C2-R3-PLATFORM-TRUST-VALIDATOR",
        contract="Validator-only surface. Validation verdicts are separate from canonical platform truth.",
        ui_consumer_routes=["/admin/email"],
        notes=["Validator may emit validation result only; it may not claim canonical platform ownership."],
    ),
    "bcss_runtime_state_authority": TruthSurface(
        surface_id="bcss_runtime_state_authority",
        surface_name="BCSS Runtime State Authority",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_runtime_state_authority",
        upstream_owner_ids=[],
        owner_endpoint="/api/admin/platform/status",
        owner_module="backend/lib/database_authority.py",
        truth_subject="bcss_runtime_state_authority",
        status_authority="bcss_runtime_state_authority",
        kpi_authority="bcss_runtime_state_authority",
        threshold_authority="bcss_runtime_state_authority",
        freshness_authority="bcss_runtime_state_authority",
        evidence_sources=["runtime_identity_public_payload", "database_authority_public_payload", "backend/lib/database_authority.py"],
        derived_fields=["identity_valid", "read_write_authority", "connection_state"],
        derivation_formula="runtime_identity_validation_plus_database_authority_plan",
        allowed_status_outputs=[VERIFIED, MISMATCH, UNVERIFIABLE, DEGRADED],
        operator_surfaces=["/api/admin/platform/status", "admin persistence health database authority payload"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-RUNTIME-STATE-AUTHORITY",
        contract="BCSS canonical owner for runtime legitimacy, environment identity, and database authority truth.",
        ui_consumer_routes=["/admin/diagnostics", "/admin/system"],
        capability_ids=["bcss.runtime.authority"],
        notes=["Extends existing canonical truth registry; does not create a parallel authority system."],
    ),
    "bcss_backup_slot_execution": TruthSurface(
        surface_id="bcss_backup_slot_execution",
        surface_name="BCSS Backup Slot Execution Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_backup_slot_execution",
        upstream_owner_ids=["bcss_runtime_state_authority"],
        owner_endpoint="/api/admin/scheduler-runs",
        owner_module="backend/lib/scheduler_runs.py",
        truth_subject="bcss_backup_slot_execution",
        status_authority="bcss_backup_slot_execution",
        kpi_authority="bcss_backup_slot_execution",
        threshold_authority="bcss_backup_slot_execution",
        freshness_authority="bcss_backup_slot_execution",
        evidence_sources=["scheduler_runs", "scheduler_locks", "backend/lib/scheduler_runs.py"],
        derived_fields=["dedup_attempts", "duration_s", "status"],
        derivation_formula="unique_slot_claim_plus_completion_audit",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["/api/admin/scheduler-runs", "/api/admin/recovery/snapshot"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-BACKUP-SLOT-EXECUTION",
        contract="BCSS canonical owner for scheduler slot ownership, duplicate prevention, and slot-bounded execution truth.",
        ui_consumer_routes=["/admin/recovery"],
        capability_ids=["bcss.backup.slot-execution"],
    ),
    "bcss_backup_job_execution": TruthSurface(
        surface_id="bcss_backup_job_execution",
        surface_name="BCSS Backup Job Execution Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_backup_job_execution",
        upstream_owner_ids=["bcss_runtime_state_authority", "bcss_backup_slot_execution"],
        owner_endpoint="/api/admin/backups-complete-r2-state",
        owner_module="backend/lib/backup_runtime.py",
        truth_subject="bcss_backup_job_execution",
        status_authority="bcss_backup_job_execution",
        kpi_authority="bcss_backup_job_execution",
        threshold_authority="bcss_backup_job_execution",
        freshness_authority="bcss_backup_job_execution",
        evidence_sources=["backup_jobs", "backend/lib/backup_runtime.py", "backup_runtime state collectors"],
        derived_fields=["overlap_blocked", "heartbeat_failure", "attempt_count", "state"],
        derivation_formula="durable_job_lease_plus_heartbeat_plus_overlap_classification",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["/api/admin/backups-complete-r2-state", "/api/admin/recovery/snapshot"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-BACKUP-JOB-EXECUTION",
        contract="BCSS canonical owner for durable backup and restore job execution state.",
        ui_consumer_routes=["/admin/recovery", "/admin/system"],
        capability_ids=["bcss.backup.job-execution"],
    ),
    "bcss_backup_archive_lineage": TruthSurface(
        surface_id="bcss_backup_archive_lineage",
        surface_name="BCSS Backup Archive Lineage Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_backup_archive_lineage",
        upstream_owner_ids=["bcss_runtime_state_authority", "bcss_backup_job_execution"],
        owner_endpoint="/api/admin/backup-verification/state",
        owner_module="backend/routes/backup_verification_routes.py",
        truth_subject="bcss_backup_archive_lineage",
        status_authority="bcss_backup_archive_lineage",
        kpi_authority="bcss_backup_archive_lineage",
        threshold_authority="bcss_backup_archive_lineage",
        freshness_authority="bcss_backup_archive_lineage",
        evidence_sources=["backup_health", "Cloudflare R2 object metadata", "archive manifests", "backup verification reports"],
        derived_fields=["filename", "size_bytes", "records", "max_age_threshold_hrs"],
        derivation_formula="local_backup_health_plus_r2_object_facts_plus_integrity_report_context",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["/api/admin/backup-verification/state", "/api/admin/recovery/snapshot"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-BACKUP-ARCHIVE-LINEAGE",
        contract="BCSS canonical owner for archive presence, origin linkage, and freshness-bounded lineage truth.",
        ui_consumer_routes=["/admin/recovery", "/admin/system"],
        capability_ids=["bcss.archive.lineage"],
        notes=["Registration does not resolve the separate BCSS-R02 precedence-convergence gap."],
    ),
    "bcss_restore_execution": TruthSurface(
        surface_id="bcss_restore_execution",
        surface_name="BCSS Restore Execution Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_restore_execution",
        upstream_owner_ids=["bcss_runtime_state_authority", "bcss_backup_job_execution", "bcss_backup_archive_lineage"],
        owner_endpoint="/api/exports/restore",
        owner_module="backend/server.py",
        truth_subject="bcss_restore_execution",
        status_authority="bcss_restore_execution",
        kpi_authority="bcss_restore_execution",
        threshold_authority="bcss_restore_execution",
        freshness_authority="bcss_restore_execution",
        evidence_sources=["audit_events", "backup_jobs", "restore replay summary", "manifest validation outcomes"],
        derived_fields=["dry_run", "processed", "failed", "origin_validation"],
        derivation_formula="guarded_restore_request_plus_manifest_origin_validation_plus_replay_result",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, DISABLED],
        operator_surfaces=["admin restore flows", "/api/admin/recovery/snapshot"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-RESTORE-EXECUTION",
        contract="BCSS canonical owner for restore request guardrails, execution outcomes, and replay truth.",
        ui_consumer_routes=["/admin/recovery"],
        capability_ids=["bcss.restore.execution"],
    ),
    "bcss_restore_drill_evidence": TruthSurface(
        surface_id="bcss_restore_drill_evidence",
        surface_name="BCSS Restore Drill Evidence Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_restore_drill_evidence",
        upstream_owner_ids=["bcss_restore_execution", "bcss_backup_archive_lineage"],
        owner_endpoint="/api/admin/recovery/snapshot",
        owner_module="backend/routes/recovery_dashboard.py",
        truth_subject="bcss_restore_drill_evidence",
        status_authority="bcss_restore_drill_evidence",
        kpi_authority="bcss_restore_drill_evidence",
        threshold_authority="bcss_restore_drill_evidence",
        freshness_authority="bcss_restore_drill_evidence",
        evidence_sources=["drill_runs", "restore drill audit evidence", "archive_filename linkage"],
        derived_fields=["duration_min", "records", "photos", "archive_filename"],
        derivation_formula="latest_completed_drill_with_scope_bounded_restore_evidence",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE],
        operator_surfaces=["/api/admin/recovery/snapshot", "/api/admin/backup-trust-score"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-RESTORE-DRILL-EVIDENCE",
        contract="BCSS canonical owner for bounded restore-drill evidence and freshness-aware exercise truth.",
        ui_consumer_routes=["/admin/recovery"],
        capability_ids=["bcss.restore.drill-evidence"],
    ),
    "bcss_recovery_posture": TruthSurface(
        surface_id="bcss_recovery_posture",
        surface_name="BCSS Recovery Posture Truth",
        role=AGGREGATOR,
        owner_type="derived",
        canonical_owner_id="bcss_backup_archive_lineage",
        upstream_owner_ids=["bcss_backup_slot_execution", "bcss_backup_job_execution", "bcss_backup_archive_lineage", "bcss_restore_drill_evidence", "bcss_runtime_state_authority"],
        owner_endpoint="/api/admin/recovery/snapshot",
        owner_module="backend/routes/recovery_dashboard.py",
        truth_subject="bcss_recovery_posture",
        status_authority="derived_from_upstream_owners",
        kpi_authority="bcss_recovery_posture",
        threshold_authority="bcss_recovery_posture",
        freshness_authority="bcss_recovery_posture",
        evidence_sources=["recovery snapshot fan-in", "backup_health", "drill_runs", "scheduler state", "capacity signals"],
        derived_fields=["pill", "warnings", "rpo", "rto", "hourly_activation"],
        derivation_formula="bounded_recovery_snapshot_over_registered_bcss_inputs",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, NOT_APPLICABLE],
        operator_surfaces=["/api/admin/recovery/snapshot", "Admin Recovery page"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R03-RECOVERY-POSTURE",
        contract="BCSS recovery posture is an aggregator only; it summarizes registered upstream truth and does not certify recovery.",
        ui_consumer_routes=["/admin/recovery"],
        capability_ids=["bcss.recovery.posture"],
        notes=["Formalizes BCSS-R03 role separation without creating a new posture engine."],
    ),
    "bcss_recovery_trust": TruthSurface(
        surface_id="bcss_recovery_trust",
        surface_name="BCSS Recovery Trust Truth",
        role=DERIVED_CONSUMER,
        owner_type="derived",
        canonical_owner_id="bcss_recovery_posture",
        upstream_owner_ids=["bcss_recovery_posture", "bcss_restore_drill_evidence", "bcss_backup_archive_lineage", "bcss_backup_job_execution"],
        owner_endpoint="/api/admin/backup-trust-score",
        owner_module="backend/lib/trust_score.py",
        truth_subject="bcss_recovery_trust",
        status_authority="derived_from_bcss_evidence",
        kpi_authority="bcss_recovery_trust",
        threshold_authority="bcss_recovery_trust",
        freshness_authority="bcss_backup_archive_lineage",
        evidence_sources=["compute_backup_trust_score", "backup_health", "drill_runs", "bucket usage state", "backup_runtime overlap state"],
        derived_fields=["trust_score", "score_band", "score_inputs"],
        derivation_formula="deterministic_penalty_model_over_bcss_recovery_inputs",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH],
        operator_surfaces=["/api/admin/backup-trust-score", "Admin Recovery page"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R03-RECOVERY-TRUST",
        contract="BCSS recovery trust is a derived consumer only; it expresses confidence and penalties and may not claim certification authority.",
        ui_consumer_routes=["/admin/recovery"],
        capability_ids=["bcss.recovery.trust"],
        notes=["Formalizes BCSS-R03 role separation without creating a new trust engine."],
    ),
    "bcss_recovery_certification": TruthSurface(
        surface_id="bcss_recovery_certification",
        surface_name="BCSS Recovery Certification Truth",
        role=CANONICAL_OWNER,
        owner_type="authoritative",
        canonical_owner_id="bcss_recovery_certification",
        upstream_owner_ids=["bcss_recovery_posture", "bcss_recovery_trust", "bcss_restore_drill_evidence", "bcss_backup_archive_lineage"],
        owner_endpoint="/api/admin/deployment-readiness",
        owner_module="backend/routes/admin_deployment_readiness.py",
        truth_subject="bcss_recovery_certification",
        status_authority="bcss_recovery_certification",
        kpi_authority="bcss_recovery_certification",
        threshold_authority="bcss_recovery_certification",
        freshness_authority="bcss_recovery_certification",
        evidence_sources=["deployment-readiness findings", "deployment_decisions", "independent verification review artifacts"],
        derived_fields=["decision", "blocking_gates", "advisory_findings", "regression_gate_count"],
        derivation_formula="bounded_certification_decision_record_over_registered_recovery_inputs",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, NOT_APPLICABLE],
        operator_surfaces=["/api/admin/deployment-readiness", "deployment readiness history"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-RECOVERY-CERTIFICATION",
        contract="Current BCSS certification owner is registration-only at this checkpoint; deployment readiness exists as bounded certification evidence but is not equivalent to recovery-class certification.",
        ui_consumer_routes=["/admin/deployment-readiness"],
        capability_ids=["bcss.recovery.certification"],
        notes=["Registration establishes ownership only. Shared class model remains future work under BCSS-R13."],
    ),
    "bcss_external_dependency_continuity": TruthSurface(
        surface_id="bcss_external_dependency_continuity",
        surface_name="BCSS External Dependency Continuity Truth",
        role=AGGREGATOR,
        owner_type="derived",
        canonical_owner_id="integration_truth",
        upstream_owner_ids=["integration_truth", "bcss_runtime_state_authority"],
        owner_endpoint="/api/admin/integrations/truth-status",
        owner_module="backend/routes/integration_truth.py",
        truth_subject="bcss_external_dependency_continuity",
        status_authority="derived_from_upstream_owners",
        kpi_authority="bcss_external_dependency_continuity",
        threshold_authority="bcss_external_dependency_continuity",
        freshness_authority="integration_truth",
        evidence_sources=["integration_settings", "integration truth payload", "notification delivery contract", "runtime identity"],
        derived_fields=["overall", "connectivity_status", "operational_status", "provider_validation_status"],
        derivation_formula="dependency_continuity_posture_over_existing_integration_truth_and_delivery_contract",
        allowed_status_outputs=[VERIFIED, DEGRADED, MISMATCH, UNVERIFIABLE, NOT_APPLICABLE],
        operator_surfaces=["/api/admin/integrations/truth-status", "Integration Truth admin page"],
        environment_scope="preview_and_production",
        runtime_reachability="reachable",
        production_reachability="reachable",
        registered_at="2026-07-24T00:00:00Z",
        contract_version=CONTRACT_VERSION,
        deprecation_state="active",
        audit_reference="BCSS-R01-EXTERNAL-DEPENDENCY-CONTINUITY",
        contract="BCSS dependency continuity posture extends the existing integration truth system and must not create a parallel dependency engine.",
        ui_consumer_routes=["/admin/integration-truth"],
        capability_ids=["bcss.external.dependency.continuity"],
        notes=["Registration resolves ownership declaration only. Centralized dependency continuity remains future BCSS-R07 work."],
    ),
}


def canonical_truth_surface(surface_id: str) -> Dict[str, Any]:
    surface = _SURFACES.get(surface_id)
    return deepcopy(surface.to_dict()) if surface else {}


def canonical_truth_registry() -> Dict[str, Dict[str, Any]]:
    return {surface_id: canonical_truth_surface(surface_id) for surface_id in _SURFACES}


def owner_role_counts() -> Dict[str, int]:
    counts = {CANONICAL_OWNER: 0, DOMAIN_OWNER: 0, DERIVED_CONSUMER: 0, AGGREGATOR: 0, VALIDATOR: 0, LEGACY_COMPATIBILITY: 0, RETIRED: 0}
    for surface in _SURFACES.values():
        counts[surface.role] = counts.get(surface.role, 0) + 1
    return counts


def canonical_truth_contract() -> Dict[str, Any]:
    shared_owners = {
        surface_id: surface
        for surface_id, surface in canonical_truth_registry().items()
        if surface.get("role") == CANONICAL_OWNER
    }
    return {
        "checkpoint": "C2",
        "contract_version": CONTRACT_VERSION,
        "status": VERIFIED,
        "source_of_truth_policy": [
            "Exactly one canonical owner per shared truth subject.",
            "Derived consumers, aggregators, and validators may summarize but never replace canonical truth.",
            "Primary operator experience must be structured evidence, not raw JSON.",
            "Missing or conflicting ownership must produce deterministic findings.",
        ],
        "status_vocabulary": [VERIFIED, MISMATCH, UNVERIFIABLE, DEGRADED, NOT_APPLICABLE, DISABLED],
        "owners": shared_owners,
        "role_counts": owner_role_counts(),
    }


def _finding(**kwargs: Any) -> Dict[str, Any]:
    now = _now_iso()
    return {
        "finding_id": kwargs["finding_id"],
        "finding_type": kwargs["finding_type"],
        "subject": kwargs["subject"],
        "surface_id": kwargs["surface_id"],
        "files": kwargs["files"],
        "routes": kwargs["routes"],
        "severity": kwargs["severity"],
        "status": kwargs["status"],
        "first_detected_at": now,
        "last_detected_at": now,
        "evidence": kwargs["evidence"],
        "canonical_owner": kwargs.get("canonical_owner"),
        "conflicting_owner": kwargs.get("conflicting_owner"),
        "operator_impact": kwargs["operator_impact"],
        "production_impact": kwargs["production_impact"],
        "owner": kwargs["owner"],
        "target_checkpoint": kwargs["target_checkpoint"],
        "required_remediation": kwargs["required_remediation"],
        "resolved_at": None,
        "resolution_evidence": [],
        "blocking_status": kwargs["blocking_status"],
        "checkpoint": "C2.11",
        "route": kwargs["routes"][0] if kwargs["routes"] else "",
        "file": kwargs["files"][0] if kwargs["files"] else "",
        "remediation": kwargs["required_remediation"],
    }


def validate_truth_registry(additional_surfaces: Optional[Iterable[Dict[str, Any]]] = None) -> Dict[str, Any]:
    registry = canonical_truth_registry()
    combined_registry = dict(registry)
    surfaces = list(registry.values())
    if additional_surfaces:
        extra = deepcopy(list(additional_surfaces))
        surfaces.extend(extra)
        for surface in extra:
            sid = surface.get("surface_id") or "unknown"
            combined_registry[sid] = surface

    findings: List[Dict[str, Any]] = []
    subject_authorities: Dict[Tuple[str, str], List[str]] = {}
    duplicate_derivations: Dict[str, List[str]] = {}

    for surface in surfaces:
        sid = surface.get("surface_id") or "unknown"
        role = surface.get("role") or UNREGISTERED
        subject = surface.get("truth_subject") or sid

        if not surface.get("owner_endpoint") or not surface.get("owner_module"):
            findings.append(_finding(
                finding_id=f"missing-owner:{sid}",
                finding_type="MISSING_OWNER_METADATA",
                subject=subject,
                surface_id=sid,
                files=[surface.get("owner_module") or "unknown"],
                routes=[surface.get("owner_endpoint") or "unknown"],
                severity="P0",
                status=CONFIRMED,
                evidence=["Shared truth surface missing required owner metadata."],
                canonical_owner=surface.get("canonical_owner_id"),
                conflicting_owner=None,
                operator_impact="Operators cannot verify truth provenance.",
                production_impact="Truth contract is incomplete.",
                owner="platform-trust-program",
                target_checkpoint="C2",
                required_remediation="Register full owner metadata for this surface.",
                blocking_status=True,
            ))

        if role in {DERIVED_CONSUMER, AGGREGATOR, VALIDATOR} and not surface.get("upstream_owner_ids"):
            findings.append(_finding(
                finding_id=f"missing-upstream:{sid}",
                finding_type="MISSING_UPSTREAM_OWNER",
                subject=subject,
                surface_id=sid,
                files=[surface.get("owner_module") or "unknown"],
                routes=[surface.get("owner_endpoint") or "unknown"],
                severity="P0",
                status=CONFIRMED,
                evidence=["Derived/aggregator/validator surface missing upstream owner references."],
                canonical_owner=surface.get("canonical_owner_id"),
                conflicting_owner=None,
                operator_impact="Derived output can impersonate source truth.",
                production_impact="Reconciliation cannot resolve upstream authority.",
                owner="platform-trust-program",
                target_checkpoint="C2",
                required_remediation="Declare upstream_owner_ids.",
                blocking_status=True,
            ))

        if role == VALIDATOR and surface.get("canonical_owner_id") == sid:
            findings.append(_finding(
                finding_id=f"validator-canonical:{sid}",
                finding_type="VALIDATOR_CLAIMS_CANONICAL_AUTHORITY",
                subject=subject,
                surface_id=sid,
                files=[surface.get("owner_module") or "unknown"],
                routes=[surface.get("owner_endpoint") or "unknown"],
                severity="P0",
                status=CONFIRMED,
                evidence=["Validator is configured as its own canonical owner."],
                canonical_owner=sid,
                conflicting_owner=None,
                operator_impact="Validation can be misread as platform truth.",
                production_impact="Canonical truth can be overridden by validator logic.",
                owner="platform-trust-program",
                target_checkpoint="C2",
                required_remediation="Attach validator to upstream canonical owner.",
                blocking_status=True,
            ))

        if role == CANONICAL_OWNER:
            for authority_key in ["status_authority", "kpi_authority", "threshold_authority", "freshness_authority"]:
                subject_authorities.setdefault((subject, authority_key), []).append(sid)

        for derivation_key in surface.get("duplicate_derivation_keys") or []:
            duplicate_derivations.setdefault(derivation_key, []).append(sid)

    for (subject, authority_key), ids in subject_authorities.items():
        if len(ids) > 1:
            findings.append(_finding(
                finding_id=f"owner-conflict:{subject}:{authority_key}",
                finding_type="OWNER_CONFLICT",
                subject=subject,
                surface_id=ids[0],
                    files=[combined_registry[ids[0]]["owner_module"], combined_registry[ids[1]]["owner_module"]],
                    routes=[combined_registry[ids[0]]["owner_endpoint"], combined_registry[ids[1]]["owner_endpoint"]],
                severity="P0",
                status=CONFIRMED,
                evidence=[f"Multiple canonical owners claim {authority_key} for {subject}.", f"{ids[0]} vs {ids[1]}"],
                canonical_owner=ids[0],
                conflicting_owner=ids[1],
                operator_impact="Operators can receive contradictory canonical truth.",
                production_impact="Truth ownership is non-deterministic.",
                owner="platform-trust-program",
                target_checkpoint="C2",
                required_remediation="Resolve duplicate canonical ownership.",
                blocking_status=True,
            ))

    for key, ids in duplicate_derivations.items():
        if len(ids) > 1:
            findings.append(_finding(
                finding_id=f"duplicate-derivation:{key}",
                finding_type="DUPLICATE_DERIVATION",
                subject=key,
                surface_id=ids[0],
                    files=[combined_registry[ids[0]]["owner_module"], combined_registry[ids[1]]["owner_module"]],
                    routes=[combined_registry[ids[0]]["owner_endpoint"], combined_registry[ids[1]]["owner_endpoint"]],
                severity="P1",
                status=MITIGATED,
                evidence=[f"Multiple derived surfaces compute {key}.", f"{ids[0]} vs {ids[1]}"],
                    canonical_owner=combined_registry[ids[0]].get("canonical_owner_id"),
                conflicting_owner=ids[1],
                operator_impact="Derived score duplication can confuse operators if unlabeled.",
                production_impact="Derived KPI drift possible.",
                owner="platform-trust-program",
                target_checkpoint="C2",
                required_remediation="Label both surfaces as derived and prevent canonical override.",
                blocking_status=False,
            ))

    return {
        "executed_at": _now_iso(),
        "contract_version": CONTRACT_VERSION,
        "findings": findings,
        "summary": {
            "surface_count": len(surfaces),
            "registered_surface_count": len(registry),
            "finding_count": len(findings),
            "p0_open_count": len([f for f in findings if f["severity"] == "P0" and f["blocking_status"]]),
            "owner_conflicts": len([f for f in findings if f["finding_type"] == "OWNER_CONFLICT"]),
            "duplicate_derivations": len([f for f in findings if f["finding_type"] == "DUPLICATE_DERIVATION"]),
        },
        "role_counts": owner_role_counts(),
    }


def derived_truth_payload(surface_id: str, *, canonical_owner_route: Optional[str], derivation_explanation: str, canonical_status: str, derived_status: Optional[str] = None, conflicts: Optional[List[str]] = None, evidence_age_source: Optional[str] = None, stale_evidence: bool = False) -> Dict[str, Any]:
    surface = canonical_truth_surface(surface_id)
    return {
        "surface": surface,
        "relationship": {
            "is_canonical": surface.get("role") in {CANONICAL_OWNER, DOMAIN_OWNER},
            "role": surface.get("role"),
            "canonical_owner_id": surface.get("canonical_owner_id"),
            "canonical_owner_route": canonical_owner_route or surface.get("owner_endpoint"),
            "upstream_owner_ids": surface.get("upstream_owner_ids") or [],
            "canonical_status": canonical_status,
            "derived_status": derived_status or canonical_status,
            "derivation_explanation": derivation_explanation,
            "conflicts": conflicts or [],
            "has_conflict": bool(conflicts),
            "evidence_age_source": evidence_age_source,
            "stale_evidence": stale_evidence,
        },
    }


__all__ = [
    "AGGREGATOR",
    "CANONICAL_OWNER",
    "CONTRACT_VERSION",
    "DERIVED_CONSUMER",
    "DOMAIN_OWNER",
    "DUPLICATE_DERIVATION",
    "LEGACY_COMPATIBILITY",
    "RETIRED",
    "UNREGISTERED",
    "VALIDATOR",
    "canonical_truth_contract",
    "canonical_truth_registry",
    "canonical_truth_surface",
    "derived_truth_payload",
    "owner_role_counts",
    "validate_truth_registry",
]