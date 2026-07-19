from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from lib.release_gate_governance import (
    collect_git_snapshot,
    compute_dependency_manifest_hash,
    compute_migration_manifest_hash,
    compute_release_gate_manifest_hash,
    workflow_inventory,
)


DOCS = REPO_ROOT / "docs"
GOV = DOCS / "governance"
REC = DOCS / "recovery"
OWNER = "jaymn.judd@mascigc.com"


def _ensure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write(path: Path, content: str) -> None:
    _ensure(path)
    path.write_text(content, encoding="utf-8")


def build_manifest() -> dict:
    return {
        "schema_version": "D5D6_RELEASE_GATE/v1",
        "manifest_id": "masci-release-gate-canonical",
        "owner": OWNER,
        "repository": "REAL MASCI platform workspace (/app)",
        "governed_branches": {
            "preview": ["main"],
            "production": ["main"],
            "legacy_detected_but_not_governed": ["master"],
        },
        "release_identity_files": {
            "scope": "release_identity_scope.json",
            "backend_authority": "backend/lib/release_identity.py",
            "backend_verifier": "backend/scripts/verify_release_identity.py",
            "frontend_stamp": "frontend/scripts/stamp-build-version.js",
            "frontend_generated": "frontend/src/buildVersion.generated.js",
        },
        "deployment_source_authority": {
            "platform": "Emergent",
            "preview_source": "workspace_state",
            "production_source": "workspace_state",
            "github_required_for_deploy": False,
            "github_checks_are_mandatory_for_platform_deploy": False,
            "branch_protection_proven_locally": False,
            "workspace_dirty_state_equivalent_to_commit": False,
            "traceable_to_exact_git_sha_without_local_governance": False,
            "governance_position": "Workspace state is the real Emergent deploy source; canonical release gate + git metadata + governed source hash are required for authority.",
        },
        "one_body_authorities": {
            "runtime_identity": "backend/lib/runtime_identity.py",
            "database_authority": "backend/lib/database_authority.py",
            "dependency_authority": "docs/governance/dependency_inventory.json",
            "trust_spine": "backend/lib/trust_spine.py",
            "backup_recovery": "backend/routes/recovery_dashboard.py",
            "deployment": "scripts/release_gate.py",
            "runtime_health": "backend/lib/runtime_reliability.py",
        },
        "mandatory_checks": [
            {
                "gate_id": "source-authority",
                "description": "Prove governed workspace/branch/HEAD and fail dirty or ungoverned deploy source.",
                "command_or_verifier": "python3 scripts/release_gate.py --target <preview|production> --json",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 60,
                "evidence_output": "release_gate_report.gates[source-authority]",
                "owner": OWNER,
                "failure_action": "BLOCKED — DEPLOYMENT SOURCE AUTHORITY UNPROVEN",
                "applicability": ["preview", "production"],
                "dependencies": [],
                "severity": "P0",
                "failure_message": "Workspace source/branch/HEAD could not be proven as the canonical deploy candidate.",
                "remediation_reference": "docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md#source-authority",
            },
            {
                "gate_id": "release-identity-verifier",
                "description": "Verify deterministic backend/frontend release identity, manifest hashes, and stale-generated-file failure.",
                "command_or_verifier": "python3 backend/scripts/verify_release_identity.py --strict",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[release-identity-verifier]",
                "owner": OWNER,
                "failure_action": "Stop build and repair release identity mismatch",
                "applicability": ["preview", "production"],
                "dependencies": ["source-authority"],
                "severity": "P0",
                "failure_message": "Release identity mismatch, missing verifier, or stale generated artifact detected.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#canonical-authority",
            },
            {
                "gate_id": "release-gate-manifest",
                "description": "Validate canonical release gate manifest structure, ownership, and stronger Production gate set.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k manifest",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[release-gate-manifest]",
                "owner": OWNER,
                "failure_action": "Fix manifest contract before certification",
                "applicability": ["preview", "production"],
                "dependencies": ["source-authority"],
                "severity": "P0",
                "failure_message": "Release gate manifest missing, malformed, or anonymous.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#mandatory-blocking-gates",
            },
            {
                "gate_id": "one-body-authorities",
                "description": "Ensure deployment, runtime identity, database authority, dependency authority, trust spine, backup/recovery, and runtime health consume the same canonical truths.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k one_body",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[one-body-authorities]",
                "owner": OWNER,
                "failure_action": "Fail release gate and repair competing truth sources",
                "applicability": ["preview", "production"],
                "dependencies": ["release-gate-manifest"],
                "severity": "P0",
                "failure_message": "A subsystem is defining competing truth outside the canonical authority graph.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#one-body-enforcement",
            },
            {
                "gate_id": "workflow-audit",
                "description": "Validate governed workflow branches, YAML parseability, and no continue-on-error on mandatory surfaces.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k workflow",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[workflow-audit]",
                "owner": OWNER,
                "failure_action": "Repair workflow governance before certification",
                "applicability": ["preview", "production"],
                "dependencies": ["release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Mandatory workflow governance is bypassable or malformed.",
                "remediation_reference": "docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md#workflow-audit",
            },
            {
                "gate_id": "secret-scan",
                "description": "Run the governed secret exposure regression.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_track_15_80_no_secrets_in_repo.py",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 600,
                "evidence_output": "release_gate_report.gates[secret-scan]",
                "owner": OWNER,
                "failure_action": "Stop and remove sensitive material",
                "applicability": ["preview", "production"],
                "dependencies": ["source-authority"],
                "severity": "P0",
                "failure_message": "Secret scan failed or did not run.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#deployment-reproducibility-doctrine",
            },
            {
                "gate_id": "prd-governance-lint",
                "description": "Run the Preview ≠ Production PRD discipline lint.",
                "command_or_verifier": "python3 scripts/lint-iteration-summary.py",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 120,
                "evidence_output": "release_gate_report.gates[prd-governance-lint]",
                "owner": OWNER,
                "failure_action": "Repair PRD iteration block discipline",
                "applicability": ["preview", "production"],
                "dependencies": ["source-authority"],
                "severity": "P1",
                "failure_message": "PRD discipline lint failed or was skipped.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#prd-governance-lint",
            },
            {
                "gate_id": "clean-backend-build",
                "description": "Fresh isolated backend install, compile, import, and strict release identity verification.",
                "command_or_verifier": "python3 scripts/release_gate.py --target <preview|production> --json",
                "execution_environment": "fresh_isolated_environment",
                "blocking_status": "BLOCK",
                "timeout_seconds": 1800,
                "evidence_output": "release_gate_report.gates[clean-backend-build]",
                "owner": OWNER,
                "failure_action": "Fix backend reproducibility before certification",
                "applicability": ["preview", "production"],
                "dependencies": ["release-identity-verifier", "release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Backend clean build cannot be reproduced from clean source.",
                "remediation_reference": "docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md#build-and-startup-commands",
            },
            {
                "gate_id": "clean-frontend-build",
                "description": "Fresh isolated frozen-lockfile install, strict version stamping, and production build.",
                "command_or_verifier": "python3 scripts/release_gate.py --target <preview|production> --json",
                "execution_environment": "fresh_isolated_environment",
                "blocking_status": "BLOCK",
                "timeout_seconds": 1800,
                "evidence_output": "release_gate_report.gates[clean-frontend-build]",
                "owner": OWNER,
                "failure_action": "Fix frontend reproducibility before certification",
                "applicability": ["preview", "production"],
                "dependencies": ["release-identity-verifier", "release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Frontend clean build cannot be reproduced from clean source.",
                "remediation_reference": "docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md#build-and-startup-commands",
            },
            {
                "gate_id": "focused-regressions",
                "description": "Run focused A–D regressions plus D5/D6 gate tests.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_runtime_identity_contract.py backend/tests/test_checkpoint_d2_runtime_truth_normalization.py backend/tests/test_checkpoint_d3_database_authority.py backend/tests/test_checkpoint_d4_dependency_governance.py backend/tests/test_checkpoint_d5_d6_release_gate.py",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 1800,
                "evidence_output": "release_gate_report.gates[focused-regressions]",
                "owner": OWNER,
                "failure_action": "Repair regression before certification",
                "applicability": ["preview", "production"],
                "dependencies": ["one-body-authorities"],
                "severity": "P0",
                "failure_message": "D1–D4 or D5/D6 protections regressed.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#mandatory-blocking-gates",
            },
            {
                "gate_id": "backup-verification-contract",
                "description": "Validate Production backup verification contract presence and verification-only discipline.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k backup_contract",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[backup-verification-contract]",
                "owner": OWNER,
                "failure_action": "Block Production certification until backup verification contract is complete",
                "applicability": ["production"],
                "dependencies": ["release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Production backup verification contract is incomplete or would execute backup/restore work.",
                "remediation_reference": "docs/governance/RELEASE_GATE_REGISTER.md#backup-verification-integration",
            },
            {
                "gate_id": "migration-compatibility-contract",
                "description": "Validate migration compatibility register and Production block rules.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k migration",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[migration-compatibility-contract]",
                "owner": OWNER,
                "failure_action": "Block Production certification until migration compatibility is governed",
                "applicability": ["production"],
                "dependencies": ["release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Migration compatibility state is unknown or not governed.",
                "remediation_reference": "docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md",
            },
            {
                "gate_id": "post-deploy-certificate-contract",
                "description": "Validate canonical post-deploy certificate schema and required probe fields.",
                "command_or_verifier": "python3 -m pytest -q backend/tests/test_checkpoint_d5_d6_release_gate.py -k post_deploy_schema",
                "execution_environment": "workspace",
                "blocking_status": "BLOCK",
                "timeout_seconds": 180,
                "evidence_output": "release_gate_report.gates[post-deploy-certificate-contract]",
                "owner": OWNER,
                "failure_action": "Block Production certification until post-deploy certificate contract is complete",
                "applicability": ["production"],
                "dependencies": ["release-gate-manifest"],
                "severity": "P0",
                "failure_message": "Post-deploy certificate schema is missing or incomplete.",
                "remediation_reference": "docs/recovery/POST_DEPLOY_CERTIFICATE_SCHEMA.json",
            },
        ],
        "test_groups": {
            "focused_a_to_d": {
                "description": "Checkpoint A–D plus D5/D6 focused slice",
                "paths": [
                    "backend/tests/test_runtime_identity_contract.py",
                    "backend/tests/test_checkpoint_d2_runtime_truth_normalization.py",
                    "backend/tests/test_checkpoint_d3_database_authority.py",
                    "backend/tests/test_checkpoint_d4_dependency_governance.py",
                    "backend/tests/test_checkpoint_d5_d6_release_gate.py"
                ]
            },
            "trust_gate_regression": {
                "description": "Legacy deployment trust regression inventory now governed by this manifest",
                "paths": [
                    "backend/tests/test_track_15_76_trust_spine.py",
                    "backend/tests/test_track_15_76_trust_spine_extended.py",
                    "backend/tests/test_track_15_76_email_render_wl_regression.py",
                    "backend/tests/test_track_15_76a_operations_trust_center.py",
                    "backend/tests/test_track_15_76b_finalization.py",
                    "backend/tests/test_track_15_77_production_lock.py",
                    "backend/tests/test_track_15_78_deployment_gate.py",
                    "backend/tests/test_track_15_79b_dr_forensics.py",
                    "backend/tests/test_track_15_79c_dispatch_task_retention.py",
                    "backend/tests/test_track_15_79e_production_certification.py",
                    "backend/tests/test_track_15_80_no_secrets_in_repo.py",
                    "backend/tests/test_track_15_81_dispatch_map_portal.py",
                    "backend/tests/test_track_15_82_dispatch_layout_rolloff.py",
                    "backend/tests/test_track_15_82b_dispatch_landing_rolloff_action.py",
                    "backend/tests/test_track_15_83_production_excellence_lockup.py",
                    "backend/tests/test_track_15_83b_production_excellence_sweep.py",
                    "backend/tests/test_track_15_84_forgedops_production_excellence_certification.py",
                    "backend/tests/test_track_15_85_mandatory_full_platform_certification.py",
                    "backend/tests/test_track_15_86_browser_smoke_gate.py",
                    "backend/tests/test_track_15_87_multi_portal_access_authority.py",
                    "backend/tests/test_track_15_88_people_access_credential_usability_clarity.py",
                    "backend/tests/test_track_15_93_zero_touch_bootstrap.py",
                    "backend/tests/test_track_15_95_operations_map_phone_overflow.py",
                    "backend/tests/test_track_15_97_github_actions_health_probe.py",
                    "backend/tests/test_track_16_00_github_lifecycle_hardening.py"
                ]
            }
        },
        "build_commands": {
            "backend": "python3 -m compileall backend && python3 backend/scripts/verify_release_identity.py --strict",
            "frontend": "cd frontend && yarn build"
        },
        "clean_install_commands": {
            "backend": "python3 -m venv <tmp>/venv && . <tmp>/venv/bin/activate && pip install --no-cache-dir -r backend/requirements.txt",
            "frontend": "cd frontend && yarn install --frozen-lockfile --ignore-scripts"
        },
        "source_exclusions": [".git/", ".emergent/", "backend/.env", "frontend/.env", "frontend/build/", "frontend/node_modules/", "deploy_reports/", "test_reports/", "walkthrough_reports/"],
        "secret_scan_contract": {
            "authoritative_test": "backend/tests/test_track_15_80_no_secrets_in_repo.py",
            "forbidden_inputs": [".env", "credentials.json", "connection strings", "sealed env templates", "pem/key material"]
        },
        "runtime_identity_contract": {
            "authority": "backend/lib/runtime_identity.py",
            "proof_tests": ["backend/tests/test_runtime_identity_contract.py", "backend/tests/test_d1_runtime_identity_http.py"]
        },
        "database_authority_contract": {
            "authority": "backend/lib/database_authority.py",
            "proof_tests": ["backend/tests/test_checkpoint_d3_database_authority.py", "backend/tests/test_checkpoint_d3_database_client_governance.py"]
        },
        "dependency_authority_contract": {
            "authority": "docs/governance/dependency_inventory.json",
            "proof_tests": ["backend/tests/test_checkpoint_d4_dependency_governance.py"]
        },
        "backup_dr_prerequisites": {
            "latest_scheduled_backup_completed_successfully": "required",
            "r2_destination_reachable": "required",
            "restore_metadata_present": "required",
            "backup_integrity_hash_verification_passed": "required",
            "restore_drill_certification_current": "required",
            "no_backup_job_currently_failing": "required",
            "verification_only": True,
            "no_backup_or_restore_execution": True
        },
        "backup_verification_contract": {
            "authority_route": "backend/routes/backup_verification_routes.py",
            "verification_only": True,
            "no_backup_or_restore_execution": True,
            "required_checks": [
                "latest_scheduled_backup_completed_successfully",
                "r2_destination_reachable",
                "restore_metadata_present",
                "backup_integrity_hash_verification_passed",
                "restore_drill_certification_current",
                "no_backup_job_currently_failing"
            ]
        },
        "backup_verification_contract": {
            "authority_route": "backend/routes/backup_verification_routes.py",
            "verification_only": True,
            "no_backup_or_restore_execution": True,
            "required_checks": [
                "latest_scheduled_backup_completed_successfully",
                "r2_destination_reachable",
                "restore_metadata_present",
                "backup_integrity_hash_verification_passed",
                "restore_drill_certification_current",
                "no_backup_job_currently_failing"
            ]
        },
        "performance_prerequisites": {
            "baseline_capture_only": True,
            "metrics": ["backend_startup_time_seconds", "api_readiness_time_seconds", "frontend_build_duration_seconds", "backend_build_duration_seconds", "bundle_size_bytes", "python_dependency_count", "node_dependency_count"]
        },
        "preview_acceptance_gates": ["source-authority", "release-identity-verifier", "release-gate-manifest", "one-body-authorities", "workflow-audit", "secret-scan", "prd-governance-lint", "clean-backend-build", "clean-frontend-build", "focused-regressions"],
        "production_acceptance_gates": ["source-authority", "release-identity-verifier", "release-gate-manifest", "one-body-authorities", "workflow-audit", "secret-scan", "prd-governance-lint", "clean-backend-build", "clean-frontend-build", "focused-regressions", "backup-verification-contract", "migration-compatibility-contract", "post-deploy-certificate-contract"],
        "rollback_gates": ["application_only_scope_confirmed", "database_untouched_confirmed", "rollback_candidate_identified", "post_rollback_probes_defined", "rollback_back_contract_defined"],
        "post_deploy_probes": ["/api/version", "/api/health", "/api/ready", "/api/health/full", "/api/platform/data-truth", "runtime_identity", "database_authority", "frontend_backend_release_identity", "authentication", "representative_authorized_read", "representative_business_workflow_smoke", "photos_files_pdf_read", "notifications_providers", "scheduler_authority", "backup_health", "error_log_spike", "query_performance_baseline", "security_headers", "hsts_in_production_https", "cors_webauthn_domain_behavior"],
        "stop_conditions": ["deployment_source_authority_unproven", "release_identity_mismatch", "mandatory_gate_missing_or_skipped", "workspace_dirty_for_deployable_candidate", "backup_verification_unavailable_for_production", "migration_state_unknown_for_production", "post_deploy_probe_not_exercised_but_reported_green"],
        "severity_rules": {
            "P0": "deploy/source authority unproven, mandatory gate bypass, wrong cluster can start, rollback can mutate data, reproducibility failure",
            "P1": "deploy branch ungoverned, verifier absence can silently pass, clean build failure, frontend/backend identity drift, migration state unknown",
            "P2": "ownership/evidence gaps, brittle lists, incomplete baseline metrics",
            "P3": "naming or formatting cleanup"
        },
        "expiration_review_date": "2026-10-19",
        "evidence_artifacts": {
            "release_identity_certificate": "release_gate_report.gates[release-identity-verifier]",
            "build_certificate": "release_gate_report.gates[clean-backend-build] + release_gate_report.gates[clean-frontend-build]",
            "test_certificate": "release_gate_report.gates[focused-regressions]",
            "dependency_certificate": "docs/governance/dependency_inventory.json",
            "runtime_identity_certificate": "docs/governance/RUNTIME_IDENTITY_CONSUMPTION_MATRIX.md",
            "database_authority_certificate": "docs/governance/DATABASE_CLIENT_AUTHORITY_REGISTER.md",
            "secret_scan_certificate": "release_gate_report.gates[secret-scan]",
            "preview_certification": "docs/recovery/PREVIEW_DEPLOYMENT_CERTIFICATION_CONTRACT.md",
            "production_certification": "docs/recovery/PRODUCTION_DEPLOYMENT_CERTIFICATION_CONTRACT.md",
            "rollback_manifest": "docs/recovery/DEPLOYMENT_ROLLBACK_RUNBOOK.md",
            "open_owner_gates_list": "docs/governance/MASTER_DEFECT_REGISTER.md"
        }
    }


def main() -> None:
    manifest = build_manifest()
    _write(GOV / "release_gate_manifest.json", json.dumps(manifest, indent=2))
    snapshot = collect_git_snapshot(REPO_ROOT)
    workflows = workflow_inventory(REPO_ROOT)
    workflow_rows = "\n".join([f"| `{w['path']}` | `{w['name']}` | {', '.join(w['triggers']) or 'none'} | {'YES' if w['uses_manifest_gate'] else 'NO'} | {'YES' if w['continue_on_error_present'] else 'NO'} |" for w in workflows])
    _write(GOV / "RELEASE_GATE_REGISTER.md", f"# RELEASE GATE REGISTER\n\nDate: {date.today().isoformat()}  \nCheckpoint: D5/D6\n\nMachine-readable authority: `docs/governance/release_gate_manifest.json`\n\nEvery blocking gate now has a stable ID, owner, evidence output, severity, failure message, and remediation reference. Production acceptance is strictly stronger than Preview acceptance. The gate fails if One Body authorities diverge.\n\n## PRD-governance-lint\n\n`python3 scripts/lint-iteration-summary.py` remains mandatory and may not be skipped or weakened.\n")
    _write(GOV / "DEPLOYMENT_PIPELINE_REGISTER.md", f"# DEPLOYMENT PIPELINE REGISTER\n\nDate: {date.today().isoformat()}  \nCheckpoint: D5/D6\n\n## Source authority\n- Workspace: `{snapshot.get('workspace')}`\n- Branch: `{snapshot.get('branch')}`\n- HEAD: `{snapshot.get('head')}`\n- Dirty state: `{'DIRTY' if snapshot.get('dirty') else 'CLEAN'}`\n- Remote configuration: `{snapshot.get('remote_configuration') or ['UNPROVEN']}`\n- Emergent workspace identity: `{snapshot.get('emergent_workspace_identity')}`\n- Platform truth: Emergent deploys from workspace state, not enforced GitHub status.\n- Known Preview deployed SHA: `UNPROVEN_FROM_LOCAL_WORKSPACE_ONLY`\n- Known Production deployed SHA: `UNPROVEN_FROM_LOCAL_WORKSPACE_ONLY`\n\n## Workflow audit\n| Workflow | Name | Triggers | Uses canonical release gate | continue-on-error on mandatory surface |\n|---|---|---|---|---|\n{workflow_rows}\n\n## Build/startup truth\n- Frontend build: `cd frontend && yarn build`\n- Backend verifier: `python3 backend/scripts/verify_release_identity.py --strict`\n- Supervisor-managed runtime ports remain unchanged (frontend 3000, backend 8001).\n")
    _write(GOV / "MIGRATION_COMPATIBILITY_REGISTER.md", f"# MIGRATION COMPATIBILITY REGISTER\n\nDate: {date.today().isoformat()}  \nCheckpoint: D6\n\nProduction deployment is blocked whenever migration state is unknown or rollback compatibility is unproven. No migrations executed in D5/D6.\n\n| Migration ID | File | Change summary | Backward compatibility | Forward compatibility | Required order | Dry-run | Idempotency | Rollback | Backup prerequisite | Owner | Gate status |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n| MIG-001 | `backend/photo_migration.py` | photo/document data shape migration helper | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | {OWNER} | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |\n| MIG-002 | `backend/routes/signature_migration.py` | signature migration route surface | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | {OWNER} | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |\n| MIG-003 | `backend/scripts/track_15_28c_canonicalization_migration.py` | daily-report canonicalization migration | PARTIAL | PARTIAL | explicit operator order | script-level only | unknown | manual only | required | {OWNER} | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |\n")
    _write(REC / "PREVIEW_DEPLOYMENT_CERTIFICATION_CONTRACT.md", f"# PREVIEW DEPLOYMENT CERTIFICATION CONTRACT\n\nDate: {date.today().isoformat()}  \n\nPreview is sandbox only, never silently connected to Production. Required acceptance: canonical Preview identity, Preview-only data resources, D1 fail-closed, frontend/backend release match, dependency/build success, no Production secrets, governed providers/schedulers, visible Preview banner, and truth-surface consistency across `/api/version`, `/api/ready`, `/api/health/full`, `/api/platform/data-truth`. Current preview-down behavior remains expected until owner-governed config exists.\n")
    _write(REC / "PRODUCTION_DEPLOYMENT_CERTIFICATION_CONTRACT.md", f"# PRODUCTION DEPLOYMENT CERTIFICATION CONTRACT\n\nDate: {date.today().isoformat()}  \n\nProduction acceptance requires approved branch/commit, green canonical release gate, runtime identity verified, correct Atlas cluster and `DB_NAME=masci_safety`, canonical database authority, correct domain/TLS, externally supplied secrets only, backup verification green, migration compatibility known, and rollback candidate identified before traffic acceptance. D5/D6 does not deploy.\n")
    _write(REC / "DEPLOYMENT_ROLLBACK_RUNBOOK.md", f"# DEPLOYMENT ROLLBACK RUNBOOK\n\nDate: {date.today().isoformat()}  \n\nApplication rollback is source/image only by default. It does not imply configuration rollback, migration rollback, data restore, or domain rollback. Required steps: identify current and prior known-good SHA/source hash, confirm migration compatibility, keep DB/R2 untouched, redeploy prior app artifact only, verify runtime/database identity, run post-rollback probes, capture evidence, and define rollback failure response. Rollback-back requires reapplying the corrected candidate, verifying exact source identity/no config drift/DB untouched, rerunning full post-deploy certificate, and comparing error/performance metrics. Automatic Production rollback is not implemented.\n")
    _write(REC / "POST_DEPLOY_CERTIFICATE_SCHEMA.json", json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MASCI Post Deploy Certificate",
        "type": "array",
        "items": {
            "type": "object",
            "required": ["probe_id", "timestamp", "environment", "source_sha", "result", "evidence", "blocker_severity"],
            "properties": {
                "probe_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "environment": {"type": "string", "enum": ["preview", "production"]},
                "source_sha": {"type": "string"},
                "result": {"type": "string", "enum": ["PASS", "FAIL", "NOT_EXERCISED"]},
                "evidence": {"type": "string"},
                "blocker_severity": {"type": "string", "enum": ["P0", "P1", "P2", "P3", "NONE"]},
                "notes": {"type": "string"}
            }
        }
    }, indent=2))
    _write(GOV / "MASTER_DEFECT_REGISTER.md", f"# MASTER DEFECT REGISTER\n\nDate: {date.today().isoformat()}  \nCheckpoint: D5/D6\n\n## Defects fixed in D5/D6\n\n| ID | Severity | Title | Status | Owner | Evidence |\n|---|---:|---|---|---|---|\n| D5D6-001 | P0 | Deployment source authority undocumented for Emergent workspace deploys | FIXED | Main agent | `docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md` |\n| D5D6-002 | P0 | Canonical release gate manifest absent | FIXED | Main agent | `docs/governance/release_gate_manifest.json` |\n| D5D6-003 | P0 | Frontend build identity could fail open on verifier errors | FIXED | Main agent | `frontend/scripts/stamp-build-version.js` |\n| D5D6-004 | P0 | Release identity missing deterministic manifest hashes for artifact traceability | FIXED | Main agent | `backend/lib/release_identity.py`, tests |\n| D5D6-005 | P1 | Legacy workflow governance still included `master` deploy branches | FIXED | Main agent | workflow diffs + tests |\n\n## Owned / deferred\n\n| ID | Severity | Title | Status | Owner | Target checkpoint |\n|---|---:|---|---|---|---|\n| D5D6-OWN-001 | P2 | Performance optimization beyond baseline capture deferred intentionally | OWNED | Main agent | D7 |\n| D5D6-OWN-002 | P2 | Live deployed Preview/Production SHA remains unprovable from local workspace without owner deployment evidence | OWNED | Main agent + Owner | Post-owner deployment certification |\n")
    _write(REC / "REAL_MASCI_CODEBASE_REMEDIATION_CERTIFICATION.md", f"# REAL MASCI CODEBASE REMEDIATION CERTIFICATION\n\nDate: {date.today().isoformat()}  \nCheckpoint: D5/D6\n\n- Canonical deployment source authority documented\n- Canonical release gate manifest established\n- Deterministic release identity expanded across backend/frontend/manifests\n- Clean backend/frontend build certification wired\n- Preview/Production contracts, post-deploy schema, rollback runbook, and migration compatibility governance added\n\nSafety accounting: no deployment, no GitHub save, no `.env` changes, no `MONGO_URL` changes, no `DB_NAME` changes, no Atlas/R2/provider mutations, no migration/seed/restore/purge/reindex/backup execution.\n")
    print(json.dumps({
        "release_gate_manifest_hash": compute_release_gate_manifest_hash(REPO_ROOT),
        "dependency_manifest_hash": compute_dependency_manifest_hash(REPO_ROOT),
        "migration_manifest_hash": compute_migration_manifest_hash(REPO_ROOT),
    }, indent=2))


if __name__ == "__main__":
    main()