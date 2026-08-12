from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from lib.release_gate_governance import (
    ONE_BODY_REQUIRED_AUTHORITIES,
    collect_git_snapshot,
    compute_dependency_manifest_hash,
    evaluate_pre_save_candidate,
    evaluate_workspace_state_source_authority,
    compute_migration_manifest_hash,
    compute_release_gate_manifest_hash,
    load_release_gate_manifest,
    one_body_contract_failures,
    read_frontend_build_identity,
    validate_release_gate_manifest,
    validate_workflows,
)
from lib.release_identity import compute_source_hash


REPO_ROOT = Path("/app")


def test_release_gate_outputs_exist():
    for path in [
        "/app/docs/governance/release_gate_manifest.json",
        "/app/docs/governance/RELEASE_GATE_REGISTER.md",
        "/app/docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md",
        "/app/docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md",
        "/app/docs/recovery/PREVIEW_DEPLOYMENT_CERTIFICATION_CONTRACT.md",
        "/app/docs/recovery/PRODUCTION_DEPLOYMENT_CERTIFICATION_CONTRACT.md",
        "/app/docs/recovery/DEPLOYMENT_ROLLBACK_RUNBOOK.md",
        "/app/docs/recovery/POST_DEPLOY_CERTIFICATE_SCHEMA.json",
    ]:
        assert Path(path).exists(), path


def test_release_gate_manifest_is_valid_and_owned():
    errors = validate_release_gate_manifest(load_release_gate_manifest(REPO_ROOT), REPO_ROOT)
    assert not errors, errors


def test_one_body_contract_is_explicit_and_resolves():
    manifest = load_release_gate_manifest(REPO_ROOT)
    assert manifest["one_body_authorities"] == ONE_BODY_REQUIRED_AUTHORITIES
    failures = one_body_contract_failures(manifest, REPO_ROOT)
    assert not failures, failures


def test_workflows_are_governed_and_valid():
    errors = validate_workflows(REPO_ROOT)
    assert not errors, errors
    ci = Path("/app/.github/workflows/ci.yml").read_text(encoding="utf-8")
    sigma = Path("/app/.github/workflows/sigma3-deploy-gate.yml").read_text(encoding="utf-8")
    assert "branches: [main]" in ci
    assert "branches: [main]" in sigma
    assert "branches: [main, master]" not in ci
    assert "branches: [main, master]" not in sigma


def test_deployment_gate_consumes_manifest_regression_inventory():
    src = Path("/app/scripts/deployment_gate.py").read_text(encoding="utf-8")
    assert "release_gate_manifest.json" in src
    assert "trust_gate_regression" in src


def test_release_identity_determinism_for_missing_files_uses_relative_shape(tmp_path: Path):
    contract_dir = tmp_path / "docs" / "governance"
    contract_dir.mkdir(parents=True)
    (contract_dir / "release_content_fingerprint_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "TEST/v1",
                "algorithm_version": "test-sha256-v1",
                "include_roots": ["."],
                "exclude_exact": [],
                "exclude_globs": [".git/**"],
                "normalize": {},
            }
        ),
        encoding="utf-8",
    )
    backend = tmp_path / "backend"
    backend.mkdir()
    lib = backend / "lib"
    lib.mkdir()
    (lib / "release_identity.py").write_text(Path("/app/backend/lib/release_identity.py").read_text(encoding="utf-8"), encoding="utf-8")
    import sys
    sys.path.insert(0, str(backend))
    try:
        from lib.release_identity import compute_source_hash as local_hash  # type: ignore

        assert local_hash(tmp_path) == local_hash(tmp_path)
    finally:
        sys.path.pop(0)


def test_frontend_build_identity_contains_extended_release_fields():
    identity = read_frontend_build_identity(REPO_ROOT)
    assert identity["identity_mode"] == "runtime-api-version"
    assert identity["identity_endpoint"] == "/api/version"
    assert identity["runtime_binding_required"] is True
    assert identity["post_save_source_mutation_required"] is False
    assert identity["tracked_commit_embed_allowed"] is False


def test_stamp_version_script_fails_closed_on_verifier_failure():
    src = Path("/app/frontend/scripts/stamp-build-version.js").read_text(encoding="utf-8")
    assert "verify_release_identity.py" in src
    assert "process.exit(verify.status || 1)" in src


def test_source_authority_snapshot_reports_dirty_state():
    snapshot = collect_git_snapshot(REPO_ROOT)
    assert "dirty" in snapshot
    assert "branch" in snapshot
    assert "head" in snapshot


def test_pre_save_candidate_policy_is_governed_and_specific():
    manifest = load_release_gate_manifest(REPO_ROOT)
    policy = manifest.get("pre_save_candidate_policy") or {}
    assert policy.get("allow_dirty_workspace_for_certification") is True
    assert policy.get("deployed_source_must_be_clean_sha") is True
    assert policy.get("classification_label") == "UNSAVED_FINAL_CANDIDATE"
    allowed = policy.get("allowed_dirty_entries") or []
    allowed_paths = {entry.get("path") for entry in allowed if entry.get("path")}
    allowed_patterns = {entry.get("path_pattern") for entry in allowed if entry.get("path_pattern")}
    for required_path in {
        "backend/lib/release_identity.py",
        "backend/lib/release_fingerprint.py",
        "backend/lib/release_gate_governance.py",
        "backend/scripts/verify_release_identity.py",
        "backend/server.py",
        "backend/tests/test_release_content_fingerprint.py",
        "backend/tests/test_release_identity_build_guard.py",
        "backend/tests/test_c2_phase2_release_identity_contract.py",
        "backend/tests/test_dr03_release_identity.py",
        "backend/tests/test_c2_deployment_governance.py",
        "backend/tests/test_wp18db_production_identity_parity.py",
        "backend/tests/test_checkpoint_d5_d6_release_gate.py",
        "docs/governance/release_gate_manifest.json",
        "docs/governance/release_content_fingerprint_contract.json",
        "memory/PRE_SAVE_CONTENT_FINGERPRINT.json",
        "scripts/release_fingerprint.py",
        "frontend/scripts/stamp-build-version.js",
        "frontend/src/buildVersion.generated.js",
        "frontend/public/release-identity.json",
        "frontend/src/lib/versionCache.js",
        "frontend/src/components/ForgedOpsAttribution.jsx",
    }:
        assert required_path in allowed_paths
    assert "memory/WP18DB_*" in allowed_patterns
    assert "memory/WP18_OPERATOR_*" in allowed_patterns


def test_pre_save_candidate_allows_only_governed_inventory():
    manifest = load_release_gate_manifest(REPO_ROOT)
    snapshot = {
        "dirty": True,
        "status_lines": [
            "M backend/lib/release_fingerprint.py",
            "M backend/lib/release_gate_governance.py",
            "M backend/lib/release_identity.py",
            "M backend/scripts/verify_release_identity.py",
            "M backend/server.py",
            "M backend/tests/test_c2_deployment_governance.py",
            "M backend/tests/test_c2_phase2_release_identity_contract.py",
            "M backend/tests/test_checkpoint_d5_d6_release_gate.py",
            "M backend/tests/test_dr03_release_identity.py",
            "M backend/tests/test_release_identity_build_guard.py",
            "M backend/tests/test_wp18db_production_identity_parity.py",
            "M docs/governance/release_gate_manifest.json",
            "?? docs/governance/release_content_fingerprint_contract.json",
            "M memory/PRE_SAVE_CONTENT_FINGERPRINT.json",
            "M frontend/public/release-identity.json",
            "M frontend/scripts/stamp-build-version.js",
            "M frontend/src/buildVersion.generated.js",
            "M frontend/src/components/ForgedOpsAttribution.jsx",
            "M frontend/src/lib/versionCache.js",
            "?? scripts/release_fingerprint.py",
            "?? backend/tests/test_release_content_fingerprint.py",
        ],
    }
    result = evaluate_pre_save_candidate(snapshot, manifest)
    assert result["passed"] is True
    assert result["classification"] == "UNSAVED_FINAL_CANDIDATE"
    assert result["unknown_dirty_files"] == []


def test_pre_save_candidate_rejects_unrelated_dirty_files():
    manifest = load_release_gate_manifest(REPO_ROOT)
    snapshot = {
        "dirty": True,
        "status_lines": [" M frontend/yarn.lock", "?? scratch.txt"],
    }
    result = evaluate_pre_save_candidate(snapshot, manifest)
    assert result["passed"] is False
    assert result["classification"] == "DIRTY_UNGOVERNED"
    assert result["unknown_dirty_files"]
    assert any("uninventoried files" in err for err in result["errors"])


def test_post_deploy_schema_allows_not_exercised():
    schema = json.loads(Path("/app/docs/recovery/POST_DEPLOY_CERTIFICATE_SCHEMA.json").read_text(encoding="utf-8"))
    assert "NOT_EXERCISED" in schema["items"]["properties"]["result"]["enum"]


def test_backup_contract_fields_present():
    backup = load_release_gate_manifest(REPO_ROOT)["backup_dr_prerequisites"]
    for field in [
        "latest_scheduled_backup_completed_successfully",
        "r2_destination_reachable",
        "restore_metadata_present",
        "backup_integrity_hash_verification_passed",
        "restore_drill_certification_current",
        "no_backup_job_currently_failing",
    ]:
        assert backup[field] == "required"
    assert backup["verification_only"] is True


def test_preview_and_production_acceptance_gates_are_distinct():
    manifest = load_release_gate_manifest(REPO_ROOT)
    preview = set(manifest["preview_acceptance_gates"])
    production = set(manifest["production_acceptance_gates"])
    assert production > preview
    assert "operator-language-hard-fail" in preview
    assert "runtime-screenshot-ledger" in preview
    assert "runtime-screenshot-ledger" in production
    assert "backup-verification-contract" in production
    assert "performance-baseline-contract" in preview
    assert "performance-baseline-contract" in production


def test_performance_contract_fields_present():
    perf = load_release_gate_manifest(REPO_ROOT)["performance_prerequisites"]
    for field in [
        "authority_route",
        "machine_readable_baseline",
        "performance_budget_register",
        "query_inventory",
        "atlas_evidence_register",
        "index_query_recommendation_register",
        "safe_self_healing_contract",
        "regression_thresholds",
    ]:
        assert field in perf
    assert perf["regression_thresholds"]["api_health_max_seconds"] == 1.0
    assert "api_health_preview" in perf["required_budget_keys"]


def test_workspace_state_source_authority_allows_clean_detached_emergent_candidate():
    manifest = load_release_gate_manifest(REPO_ROOT)
    result = evaluate_workspace_state_source_authority(
        {
            "branch": "",
            "head": "43ef229fe68a0bbc62dc96f7bf68f1a1697b4ff1",
            "dirty": False,
            "emergent_workspace_identity": {"job_id": "preview-job"},
        },
        manifest,
        target="preview",
    )
    assert result["passed"] is True
    assert result["classification"] == "DETACHED_WORKSPACE_STATE_CLEAN_SHA"


def test_workspace_state_source_authority_rejects_dirty_detached_candidate():
    manifest = load_release_gate_manifest(REPO_ROOT)
    result = evaluate_workspace_state_source_authority(
        {
            "branch": "",
            "head": "43ef229fe68a0bbc62dc96f7bf68f1a1697b4ff1",
            "dirty": True,
            "emergent_workspace_identity": {"job_id": "preview-job"},
        },
        manifest,
        target="preview",
    )
    assert result["passed"] is False
    assert result["reason"] == "workspace_dirty"


def test_pre_save_candidate_can_authorize_detached_workspace_state():
    manifest = load_release_gate_manifest(REPO_ROOT)
    snapshot = {
        "branch": "",
        "head": "43ef229fe68a0bbc62dc96f7bf68f1a1697b4ff1",
        "dirty": True,
        "emergent_workspace_identity": {"job_id": "preview-job"},
        "status_lines": [
            "M backend/lib/release_gate_governance.py",
            " M backend/tests/test_checkpoint_d5_d6_release_gate.py",
            " M docs/governance/release_gate_manifest.json",
            " M scripts/release_gate.py",
        ],
    }
    result = evaluate_pre_save_candidate(snapshot, manifest)
    assert result["passed"] is True


def test_failure_injection_contract_cases_present():
    stop_conditions = set(load_release_gate_manifest(REPO_ROOT)["stop_conditions"])
    for value in {
        "deployment_source_authority_unproven",
        "release_identity_mismatch",
        "mandatory_gate_missing_or_skipped",
        "workspace_dirty_for_deployable_candidate",
        "backup_verification_unavailable_for_production",
        "migration_state_unknown_for_production",
    }:
        assert value in stop_conditions


def test_preview_production_and_rollback_contract_docs_are_explicit():
    preview = Path("/app/docs/recovery/PREVIEW_DEPLOYMENT_CERTIFICATION_CONTRACT.md").read_text(encoding="utf-8")
    production = Path("/app/docs/recovery/PRODUCTION_DEPLOYMENT_CERTIFICATION_CONTRACT.md").read_text(encoding="utf-8")
    rollback = Path("/app/docs/recovery/DEPLOYMENT_ROLLBACK_RUNBOOK.md").read_text(encoding="utf-8")
    assert "never silently connected to Production" in preview
    assert "DB_NAME=masci_safety" in production
    assert "Application rollback is source/image only by default" in rollback
    assert "Rollback-back requires reapplying the corrected candidate" in rollback


def test_release_gate_cli_emits_manifest_hashes():
    if os.environ.get("RELEASE_GATE_RUNNING") == "1":
        pytest.skip("avoid recursive release-gate invocation inside focused regressions")
    env = os.environ.copy()
    env["RELEASE_GATE_SKIP_HEAVY_BUILDS"] = "1"
    completed = subprocess.run(
        ["python3", "/app/scripts/release_gate.py", "--target", "preview", "--json"],
        cwd="/app",
        capture_output=True,
        text=True,
        env=env,
        timeout=3600,
    )
    payload = json.loads(completed.stdout)
    assert payload["manifest_id"] == "masci-release-gate-canonical"
    assert payload["dependency_manifest_hash"] == compute_dependency_manifest_hash(REPO_ROOT)
    assert payload["migration_manifest_hash"] == compute_migration_manifest_hash(REPO_ROOT)
    assert payload["release_gate_manifest_hash"] == compute_release_gate_manifest_hash(REPO_ROOT)
    assert payload["decision"] in {"pass", "fail"}


@pytest.mark.parametrize("field_name", [
    "release_identity_certificate",
    "build_certificate",
    "test_certificate",
    "runtime_screenshot_ledger",
    "performance_baseline",
    "atlas_alert_evidence_register",
    "query_inventory",
    "index_query_recommendation_register",
    "safe_self_healing_foundation",
    "dependency_certificate",
    "runtime_identity_certificate",
    "database_authority_certificate",
    "secret_scan_certificate",
    "preview_certification",
    "production_certification",
    "rollback_manifest",
    "open_owner_gates_list",
])
def test_evidence_artifacts_are_named(field_name: str):
    assert field_name in load_release_gate_manifest(REPO_ROOT)["evidence_artifacts"]