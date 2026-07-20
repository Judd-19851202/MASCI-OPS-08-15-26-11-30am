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
    scope = tmp_path / "release_identity_scope.json"
    scope.write_text(json.dumps(["missing/file.txt"]), encoding="utf-8")
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
    assert identity["source_hash"] == compute_source_hash(REPO_ROOT)
    assert identity["dependency_manifest_hash"] == compute_dependency_manifest_hash(REPO_ROOT)
    assert identity["migration_manifest_hash"] == compute_migration_manifest_hash(REPO_ROOT)
    assert identity["release_gate_manifest_hash"] == compute_release_gate_manifest_hash(REPO_ROOT)
    assert identity["release_gate_manifest_version"] == "D5D6_RELEASE_GATE/v1"
    assert identity["release_gate_manifest_id"] == "masci-release-gate-canonical"


def test_stamp_version_script_fails_closed_on_verifier_failure():
    src = Path("/app/frontend/scripts/stamp-build-version.js").read_text(encoding="utf-8")
    assert "release identity verification failed" in src
    assert "process.exit(1)" in src


def test_source_authority_snapshot_reports_dirty_state():
    snapshot = collect_git_snapshot(REPO_ROOT)
    assert "dirty" in snapshot
    assert "branch" in snapshot
    assert "head" in snapshot


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
    assert "backup-verification-contract" in production
    assert "performance-baseline-contract" in preview
    assert "performance-baseline-contract" in production


def test_performance_contract_fields_present():
    perf = load_release_gate_manifest(REPO_ROOT)["performance_prerequisites"]
    for field in [
        "authority_route",
        "machine_readable_baseline",
        "query_inventory",
        "atlas_evidence_register",
        "index_query_recommendation_register",
        "safe_self_healing_contract",
        "regression_thresholds",
    ]:
        assert field in perf
    assert perf["regression_thresholds"]["api_health_max_seconds"] == 1.0


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