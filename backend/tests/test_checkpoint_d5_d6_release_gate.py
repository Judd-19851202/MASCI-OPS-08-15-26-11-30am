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


def test_pre_save_candidate_policy_is_governed_and_specific():
    manifest = load_release_gate_manifest(REPO_ROOT)
    policy = manifest.get("pre_save_candidate_policy") or {}
    assert policy.get("allow_dirty_workspace_for_certification") is True
    assert policy.get("deployed_source_must_be_clean_sha") is True
    allowed = policy.get("allowed_dirty_entries") or []
    assert allowed == [
        {
            "path": "frontend/yarn.lock",
            "mission_ref": "PDC-01A Blocker 1 and Blocker 3",
            "rationale": "Dependency lockfile drift is explicitly inventoried as the governed pre-save candidate delta that must be reconciled before clean-SHA deploy certification.",
        },
        {
            "path": "backend/lib/release_gate_governance.py",
            "mission_ref": "PDC-01A Blocker 1",
            "rationale": "PRE_SAVE_CANDIDATE authority parsing and inventory enforcement live here and are allowed as a governed pre-save delta only.",
        },
        {
            "path": "docs/governance/release_gate_manifest.json",
            "mission_ref": "PDC-01A Blocker 1 and Blocker 4",
            "rationale": "The canonical manifest itself must carry the governed pre-save inventory and auth continuity reference updates for this remediation slice.",
        },
        {
            "path": "frontend/src/buildVersion.generated.js",
            "mission_ref": "PDC-01A Blocker 3",
            "rationale": "Canonical build stamping regenerates the frontend release identity artifact for the governed pre-save candidate source.",
        },
        {
            "path": "backend/scripts/verify_release_identity.py",
            "mission_ref": "PDC-01A Blocker 3",
            "rationale": "The release identity verifier now classifies PRE_SAVE_CANDIDATE workspaces honestly and is part of the governed identity reconciliation change-set.",
        },
        {
            "path": "backend/tests/test_checkpoint_d5_d6_release_gate.py",
            "mission_ref": "PDC-01A Blocker 1",
            "rationale": "The release-gate regression suite itself is updated to lock the governed PRE_SAVE_CANDIDATE contract and reject unknown dirty files.",
        },
        {
            "path": "backend/static/runtime-data/DEPLOYMENT_HISTORY.json",
            "mission_ref": "PDC-01A Focused validation",
            "rationale": "Release-gate execution appends governed workspace certification history here; the file is explicitly inventoried to avoid hidden validation-side drift.",
        },
        {
            "path": "memory/PRD.md",
            "mission_ref": "PDC-01A Blocker 4",
            "rationale": "The project record is updated to reference the new canonical auth continuity artifact and the exact blocker-remediation scope.",
        },
        {
            "path_pattern": "memory/OPS8_DRILL_*_REPORT.md",
            "mission_ref": "PDC-01B Restore certification evidence",
            "rationale": "Namespace-isolated restore drill closeout reports are governed preview evidence artifacts and must not invalidate PRE_SAVE_CANDIDATE authority while the resilience package is still in progress.",
        },
        {
            "path_pattern": "memory/WP18DB_*",
            "mission_ref": "PDC-01B WP-18DB resilience certification artifacts",
            "rationale": "WP-18DB evidence artifacts are governed in-package certification outputs and must remain eligible PRE_SAVE_CANDIDATE dirty entries until package closeout is finalized.",
        },
        {
            "path": "backend/routes/admin_runtime_reliability.py",
            "mission_ref": "PDC-01B Executive reliability contract",
            "rationale": "The governed runtime diagnostics surface now exposes the enforced performance-budget contract for WP-18DB executive reliability evidence.",
        },
        {
            "path": "backend/routes/recovery_dashboard.py",
            "mission_ref": "PDC-01B Recovery posture truth refinement",
            "rationale": "Recovery posture now stays green for a fresh valid archive when only historical backup failures remain as informational context, preventing false amber closeout state.",
        },
        {
            "path": "backend/lib/singleton_scheduler.py",
            "mission_ref": "PDC-01B Scheduler shutdown resilience",
            "rationale": "The singleton scheduler now exits cleanly when runtime DB availability disappears during shutdown, preventing false post-shutdown retry loops from contaminating reliability evidence.",
        },
        {
            "path": "backend/tests/test_iter445_scheduler_hardening.py",
            "mission_ref": "PDC-01B Scheduler shutdown resilience",
            "rationale": "Scheduler regressions now prove shutdown cancellation exits cleanly once runtime DB access is gone.",
        },
        {
            "path": "backend/tests/test_backup_admin_endpoints_preview.py",
            "mission_ref": "PDC-01B Preview admin evidence stability",
            "rationale": "The preview admin endpoint suite now retries transient ingress failures so governed runtime evidence is measured against the actual backend instead of cold-path transport noise.",
        },
        {
            "path": "backend/services/enterprise_governance.py",
            "mission_ref": "PDC-01B Governance remediation truth",
            "rationale": "Enterprise-governance failures now emit remediation guidance so deployment readiness no longer misclassifies preview trust-spine failures as silent failures.",
        },
        {
            "path": "backend/routes/admin_deployment_readiness.py",
            "mission_ref": "PDC-01B Deployment readiness truth surface",
            "rationale": "Deployment readiness now exposes the same governed performance-budget contract used by the executive recovery dashboard without relying on admin-strict tokens.",
        },
        {
            "path": "backend/lib/performance_budget_contract.py",
            "mission_ref": "PDC-01B Shared performance-budget truth",
            "rationale": "The performance-budget contract was factored into a shared governed helper so multiple admin surfaces reuse the same release-control truth instead of duplicating CSV parsing logic.",
        },
        {
            "path": "backend/tests/test_ai_gateway.py",
            "mission_ref": "PDC-01B AI fallback certification stability",
            "rationale": "AI gateway tests now use isolated event loops so fallback evidence remains stable under current pytest runtime behavior.",
        },
        {
            "path": "backend/tests/test_iter370_r7_admin_strict_fail_closed.py",
            "mission_ref": "PDC-01B Admin strict auth certification stability",
            "rationale": "Admin strict fail-closed regression now validates the current multi-login token path and skips only on transport noise instead of reporting false app failures.",
        },
        {
            "path": "frontend/src/pages/admin/AdminRecovery.jsx",
            "mission_ref": "PDC-01B Executive reliability dashboard extension",
            "rationale": "The existing governed recovery dashboard was extended to show platform reliability, capacity, deployment readiness, and performance-budget evidence without creating a duplicate executive dashboard.",
        },
        {
            "path": "memory/ROADMAP.md",
            "mission_ref": "PDC-01B Closeout governance records",
            "rationale": "ROADMAP was updated at final closeout to reflect that WP-18DB is complete and WP-18DC remains blocked until future authorization.",
        },
        {
            "path": "memory/CHANGELOG.md",
            "mission_ref": "PDC-01B Closeout governance records",
            "rationale": "CHANGELOG was updated at final closeout to record the exact WP-18DB repairs, final archive, release-gate result, and dashboard extension.",
        },
        {
            "path_pattern": "docs/governance/PRE_C10_*",
            "mission_ref": "PRE-C10 final denominator closeout",
            "rationale": "The governing PRE-C10 closeout register and related bounded denominator artifacts are allowed PRE_SAVE_CANDIDATE deltas while the non-final denominator is being explicitly dispositioned before the frozen final certification chain.",
        },
        {
            "path_pattern": "docs/governance/PLATFORM_*",
            "mission_ref": "PRE-C10 platform truth closeout",
            "rationale": "Platform truth, KPI, synthetic-governance, and stale-derived-state closeout artifacts are governed PRE_SAVE_CANDIDATE evidence while PRE-C10 denominator closure is being finalized.",
        },
        {
            "path": "docs/governance/C1_C9_PLATFORM_INTEGRATION_TRUTH_REGISTER.md",
            "mission_ref": "PRE-C10 C1-C9 closeout",
            "rationale": "The canonical C1–C9 integration truth register is allowed as a governed PRE_SAVE_CANDIDATE delta while the remaining long-tail consumer families are explicitly dispositioned.",
        },
        {
            "path": "docs/governance/PERMANENT_FIX_CLOSURE_REGISTER.csv",
            "mission_ref": "PRE-C10 permanent-fix closeout",
            "rationale": "The canonical permanent-fix closure ledger is allowed as a governed PRE_SAVE_CANDIDATE delta while final closeout rows are reconciled and frozen for certification.",
        },
        {
            "path_pattern": "memory/WP18_OPERATOR_*",
            "mission_ref": "PRE-C10 operator-language certification evidence",
            "rationale": "WP18 operator-language comprehension and exception ledgers are governed certification evidence artifacts and may remain dirty within the bounded PRE_SAVE_CANDIDATE closeout package.",
        },
        {
            "path_pattern": "memory/WP18C9_*",
            "mission_ref": "WP18C9 Closeout evidence pack",
            "rationale": "WP-18C9 portfolio intelligence closeout artifacts are governed certification outputs and must remain eligible PRE_SAVE_CANDIDATE dirty entries until final closeout is saved.",
        },
        {
            "path": "backend/services/portfolio_intelligence.py",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "The governed C9 closeout explicitly rebuilds portfolio condition hierarchy, project identity recovery, and attention-first semantics without changing the underlying C7/C8 math engines.",
        },
        {
            "path": "frontend/src/components/project_controls/PortfolioIntelligenceWorkspace.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "The core C9 workspace was intentionally rebuilt to deliver the required attention-first executive and PM information architecture.",
        },
        {
            "path": "frontend/src/pages/ExecutiveOverview.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "Executive Overview now defines the governed purpose split between overview, portfolio performance, and immediate operations.",
        },
        {
            "path": "frontend/src/pages/PmPortfolioIntelligence.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "PM portfolio framing was rebuilt so PMs see assigned-project performance instead of generic cross-product language.",
        },
        {
            "path": "frontend/src/pages/PmCommandCenter.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "PM Management Center now avoids the admin-only intelligence strip dependency and carries governed scoped identity framing.",
        },
        {
            "path": "frontend/src/components/pm/command/PmProjectFirstHome.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "The PM project-first surface now resolves project names from scoped portfolio data and removes operator-facing architecture explanations.",
        },
        {
            "path": "frontend/src/components/pm/command/PmProjectSelector.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "PM selector behavior was aligned with scoped identity requirements for the C9 closeout.",
        },
        {
            "path": "frontend/src/lib/projectControlsPresentation.js",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "Shared KPI presentation now uses governed operator-readable cost and schedule language across C8/C9 surfaces.",
        },
        {
            "path": "frontend/src/lib/operatorLanguage.js",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "Operator identity sanitation now removes fixture markers while preserving legitimate project identity on governed C9 surfaces.",
        },
        {
            "path": "frontend/src/pages/ExecutiveOperationalIntelligence.jsx",
            "mission_ref": "WP18C9 Executive / PM IA rebuild",
            "rationale": "Executive Operations Dashboard copy and hierarchy were refined so it complements rather than duplicates the rebuilt portfolio experience.",
        },
        {
            "path": "frontend/src/components/ods/HorizonPrimitives.jsx",
            "mission_ref": "WP18C9 Runtime screenshot ledger hardening",
            "rationale": "Executive operational-intelligence primitives were updated to remove operator-facing software-language references and support the governed screenshot-ledger certification standard.",
        },
        {
            "path": "frontend/src/components/operational/OperationalTimelineSidecar.jsx",
            "mission_ref": "WP18C9 Runtime screenshot ledger hardening",
            "rationale": "Project-detail runtime certification required removal of generic project fallback language from the operational timeline sidecar.",
        },
        {
            "path": "frontend/src/pages/NewDailyReportV3.jsx",
            "mission_ref": "WP18C9 Runtime screenshot ledger hardening",
            "rationale": "The daily-report filing experience is part of the permanent screenshot-ledger scope, so operator-facing copy was reconciled to the certified comprehension standard.",
        },
        {
            "path": "frontend/src/pages/PmOperationalIntelligence.jsx",
            "mission_ref": "WP18C9 Runtime screenshot ledger hardening",
            "rationale": "PM project-performance copy was aligned to the operator-comprehension standard and is now governed as part of the permanent runtime screenshot ledger.",
        },
        {
            "path": "frontend/src/pages/PmProjectDetail.jsx",
            "mission_ref": "WP18C9 Runtime screenshot ledger hardening",
            "rationale": "PM project-detail runtime certification required elimination of generic fallback identity on the certified route.",
        },
        {
            "path": "scripts/premerge_operator_language_check.py",
            "mission_ref": "WP18C9 Recurrence prevention",
            "rationale": "The lightweight pre-merge operator-language guard is part of the governed C9 closeout because it prevents recurrence of the exact operator-comprehension defect class remediated here.",
        },
        {
            "path": "scripts/runtime_screenshot_ledger_gate.py",
            "mission_ref": "WP18C9 Runtime screenshot ledger enforcement",
            "rationale": "The permanent runtime screenshot-ledger gate is part of the constitutional C9 closeout and must remain governed for all future operator-facing certification runs.",
        },
        {
            "path": "pytest.ini",
            "mission_ref": "WP18C9 Warning reconciliation",
            "rationale": "The final C9 closeout required zero unexplained warnings, so the exact third-party Starlette multipart PendingDeprecationWarning is narrowly filtered here without muting other warnings.",
        },
        {
            "path": "backend/server.py",
            "mission_ref": "PDC-01B Build and backup evidence",
            "rationale": "The complete archive export path was hardened to derive database authority truth in verification contexts without weakening runtime database authority protections.",
        },
        {
            "path": "backend/tests/test_track_27_09b_integrity_scheduler_closeout.py",
            "mission_ref": "PDC-01B Backup evidence",
            "rationale": "The recovery scheduler closeout regression now matches the canonical informational-warning classification used by the governed backup OCC surface.",
        },
        {
            "path": "backend/tests/test_track_28_09d_backup_health_aggregator.py",
            "mission_ref": "PDC-01B Backup evidence",
            "rationale": "The backup health aggregator regression now matches the canonical D2 backup/recovery status vocabulary for this governed release.",
        },
        {
            "path": "docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md",
            "mission_ref": "PDC-01B Migration continuity",
            "rationale": "The migration register now records exact-release dispositions proving this candidate does not introduce or require a migration.",
        },
        {
            "path": "docs/governance/BACKUP_RECOVERY_RELEASE_CERTIFICATE.md",
            "mission_ref": "PDC-01B Backup evidence",
            "rationale": "Canonical release-facing backup/recovery evidence is captured here with honest VERIFIED / STALE / NOT_EXERCISED / OWNER_EVIDENCE_REQUIRED classifications.",
        },
        {
            "path": "docs/governance/PDC_01B_RELEASE_EVIDENCE.md",
            "mission_ref": "PDC-01B Build certification",
            "rationale": "This bounded closure pass records exact-candidate build, gate, and regression evidence for the current PRE_SAVE_CANDIDATE.",
        },
        {
            "path": "scripts/release_gate.py",
            "mission_ref": "PDC-01B Build certification",
            "rationale": "The release gate itself was repaired to avoid recursive self-invocation in focused regressions and to return correct top-level build gate statuses for this candidate.",
        },
    ]


def test_pre_save_candidate_allows_only_governed_inventory():
    manifest = load_release_gate_manifest(REPO_ROOT)
    snapshot = {
        "dirty": True,
        "status_lines": [
            "M backend/lib/release_gate_governance.py",
            " M frontend/yarn.lock",
            "M docs/governance/release_gate_manifest.json",
            "M frontend/src/buildVersion.generated.js",
            "M backend/scripts/verify_release_identity.py",
            "M backend/tests/test_checkpoint_d5_d6_release_gate.py",
            "M backend/static/runtime-data/DEPLOYMENT_HISTORY.json",
            "M memory/PRD.md",
            "M backend/server.py",
            "M backend/tests/test_track_27_09b_integrity_scheduler_closeout.py",
            "M backend/tests/test_track_28_09d_backup_health_aggregator.py",
            "M docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md",
            "?? docs/governance/BACKUP_RECOVERY_RELEASE_CERTIFICATE.md",
            "?? docs/governance/PDC_01B_RELEASE_EVIDENCE.md",
            "M scripts/release_gate.py",
        ],
    }
    result = evaluate_pre_save_candidate(snapshot, manifest)
    assert result["passed"] is True
    assert result["classification"] == "PRE_SAVE_CANDIDATE"
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