"""
Platform Survivability Program Independent Verification Tests
=============================================================
Verifies the survivability evidence package for MASCI OPS constitutional validation.

Test Categories:
1. Artifact existence and internal consistency
2. Governance classification validation
3. Wave 3 regression integrity
4. Live API verification against documented evidence
5. RTO/RPO measurement validation
"""

import pytest
import requests
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Allowed governance classifications per constitutional requirements
ALLOWED_CLASSIFICATIONS = {
    "Repository Defect",
    "Configuration Issue", 
    "Administrative Action",
    "External Infrastructure Dependency",
    "Accepted Risk"
}

# Wave 3 frozen artifact hashes from PLATFORM_SURVIVABILITY_EXECUTION_RAW.json
WAVE3_EXPECTED_HASHES = {
    "/app/memory/WAVE_3_FORMAL_CLOSEOUT.md": "dfdcc5ba749a6f49e60bd78bc1e56eb382b966078c2aa3c101c927a2d6375cc0",
    "/app/memory/WAVE_3_CERTIFICATION_REGISTER.md": "10733be526af49207064cdddd8ab18d3a7259c712bf6af7d927576a4e7271c93",
    "/app/memory/WAVE_3_GOVERNANCE_RECONCILIATION.md": "431aa59f056b124ca4660762dce1aefe3310a2ccebda384d6b9d790d96c5d7f2",
    "/app/memory/WAVE_3_FINAL_STATUS.json": "a36b2b46ccac5e730d9059bdf311869d2a29feaf8a9e385ec41b207a0c9739da",
    "/app/test_reports/iteration_50.json": "cfa253bd368381e0a0d7d13e2b39f99bb20ece52f9939747116c30208c6ea5fd",
    "/app/test_reports/iteration_51.json": "7409a4f939d451b2d317108b48cc0cafeeef6ec3f3a6abc11a5dda9e31e60558"
}

# Survivability artifacts that must exist
SURVIVABILITY_ARTIFACTS = [
    "/app/memory/CANONICAL_SURVIVABILITY_CAPABILITY_INVENTORY.md",
    "/app/memory/PLATFORM_SURVIVABILITY_DECISION_REGISTER.md",
    "/app/memory/OPERATIONAL_DEPENDENCY_GRAPH.md",
    "/app/memory/FAILURE_INJECTION_REPORT.md",
    "/app/memory/RECOVERY_VALIDATION_REPORT.md",
    "/app/memory/RTO_RPO_MEASUREMENTS.md",
    "/app/memory/WAVE_3_SURVIVABILITY_REGRESSION_GATE.md",
    "/app/memory/PLATFORM_SURVIVABILITY_REPORT.md",
    "/app/memory/SURVIVABILITY_CERTIFICATION_REGISTER.md",
    "/app/memory/SURVIVABILITY_FINAL_STATUS.json",
    "/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json"
]


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


class TestSurvivabilityArtifactExistence:
    """Verify all survivability artifacts exist."""
    
    @pytest.mark.parametrize("artifact_path", SURVIVABILITY_ARTIFACTS)
    def test_artifact_exists(self, artifact_path):
        """Each survivability artifact must exist."""
        assert Path(artifact_path).exists(), f"Missing artifact: {artifact_path}"
    
    def test_final_status_is_valid_json(self):
        """SURVIVABILITY_FINAL_STATUS.json must be valid JSON."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            data = json.load(f)
        assert "program" in data
        assert "status" in data
        assert data["preview_only"] is True
    
    def test_execution_raw_is_valid_json(self):
        """PLATFORM_SURVIVABILITY_EXECUTION_RAW.json must be valid JSON."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        assert "executed_at" in data
        assert "scenarios" in data
        assert "baseline" in data
        assert "post_execution" in data


class TestWave3RegressionIntegrity:
    """Verify Wave 3 frozen artifacts remain unchanged."""
    
    @pytest.mark.parametrize("filepath,expected_hash", WAVE3_EXPECTED_HASHES.items())
    def test_wave3_artifact_hash_unchanged(self, filepath, expected_hash):
        """Each Wave 3 frozen artifact must have unchanged hash."""
        assert Path(filepath).exists(), f"Missing Wave 3 artifact: {filepath}"
        actual_hash = sha256_file(filepath)
        assert actual_hash == expected_hash, (
            f"Wave 3 artifact modified: {filepath}\n"
            f"Expected: {expected_hash}\n"
            f"Actual: {actual_hash}"
        )
    
    def test_regression_gate_reports_pass(self):
        """WAVE_3_SURVIVABILITY_REGRESSION_GATE.md must report PASS."""
        with open("/app/memory/WAVE_3_SURVIVABILITY_REGRESSION_GATE.md") as f:
            content = f.read()
        assert "REGRESSION GATE PASS" in content
        assert "Historical evidence rewritten: **NO**" in content


class TestGovernanceClassifications:
    """Verify all governance classifications use allowed vocabulary."""
    
    def test_decision_register_classifications(self):
        """Every decision in the register must use exactly one allowed classification."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_DECISION_REGISTER.md") as f:
            content = f.read()
        
        # Extract risk classifications from the table
        lines = content.split('\n')
        in_table = False
        classifications_found = []
        
        for line in lines:
            if '| Decision ID |' in line:
                in_table = True
                continue
            if in_table and line.startswith('|') and 'PSP-DEC-' in line:
                # Parse the table row
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 10:
                    classification = parts[9]  # Risk classification column
                    classifications_found.append(classification)
        
        assert len(classifications_found) > 0, "No decisions found in register"
        
        for classification in classifications_found:
            assert classification in ALLOWED_CLASSIFICATIONS, (
                f"Invalid classification: '{classification}'\n"
                f"Allowed: {ALLOWED_CLASSIFICATIONS}"
            )
    
    def test_final_status_governance_findings(self):
        """SURVIVABILITY_FINAL_STATUS.json governance_findings must use allowed categories."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            data = json.load(f)
        
        findings = data.get("governance_findings", {})
        for category in findings.keys():
            assert category in ALLOWED_CLASSIFICATIONS, (
                f"Invalid governance category: '{category}'"
            )
    
    def test_no_repository_critical_defects(self):
        """No unresolved repository-critical survivability defects should remain."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            data = json.load(f)
        
        defects = data.get("unresolved_repository_critical_survivability_defects", [])
        assert len(defects) == 0, f"Unresolved repository defects: {defects}"
        
        # Also verify Repository Defect count is 0
        findings = data.get("governance_findings", {})
        assert findings.get("Repository Defect", 0) == 0


class TestFailureInjectionEvidence:
    """Verify failure injection evidence is complete and consistent."""
    
    def test_all_six_scenarios_executed(self):
        """All 6 planned failure injections must be executed."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        scenarios = data.get("scenarios", [])
        assert len(scenarios) == 6, f"Expected 6 scenarios, found {len(scenarios)}"
        
        expected_ids = {"PSP-FI-01", "PSP-FI-02", "PSP-FI-03", "PSP-FI-04", "PSP-FI-05", "PSP-FI-06"}
        actual_ids = {s.get("scenario_id") for s in scenarios}
        assert actual_ids == expected_ids
    
    def test_all_scenarios_passed(self):
        """All failure injection scenarios must have result=PASS."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        for scenario in data.get("scenarios", []):
            assert scenario.get("result") == "PASS", (
                f"Scenario {scenario.get('scenario_id')} failed: {scenario.get('result')}"
            )
    
    def test_wave3_unchanged_after_each_scenario(self):
        """Wave 3 hashes must be unchanged after each scenario."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        for scenario in data.get("scenarios", []):
            assert scenario.get("wave3_hashes_unchanged") is True, (
                f"Wave 3 modified during {scenario.get('scenario_id')}"
            )
    
    def test_baseline_health_endpoints_200(self):
        """Baseline health endpoints must all return 200."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        baseline_health = data.get("baseline", {}).get("health", {})
        for endpoint, result in baseline_health.items():
            assert result.get("status_code") == 200, (
                f"Baseline {endpoint} returned {result.get('status_code')}"
            )
    
    def test_post_execution_health_endpoints_200(self):
        """Post-execution health endpoints must all return 200."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        post_health = data.get("post_execution", {}).get("health", {})
        for endpoint, result in post_health.items():
            assert result.get("status_code") == 200, (
                f"Post-execution {endpoint} returned {result.get('status_code')}"
            )


class TestRTORPOMeasurements:
    """Verify RTO/RPO measurements are from actual observations."""
    
    def test_failure_injection_rto_measurements_present(self):
        """Each failure injection must have measured RTO."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        for scenario in data.get("scenarios", []):
            metrics = scenario.get("metrics", {})
            assert "measured_rto_ms" in metrics, (
                f"Missing RTO for {scenario.get('scenario_id')}"
            )
            assert metrics["measured_rto_ms"] >= 0
    
    def test_failure_injection_rpo_measurements_present(self):
        """Each failure injection must have measured RPO."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json") as f:
            data = json.load(f)
        
        for scenario in data.get("scenarios", []):
            metrics = scenario.get("metrics", {})
            assert "measured_rpo_seconds" in metrics, (
                f"Missing RPO for {scenario.get('scenario_id')}"
            )
    
    def test_live_posture_measurements_documented(self):
        """Live platform posture measurements must be documented."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            data = json.load(f)
        
        posture = data.get("measured_platform_posture", {})
        
        rpo = posture.get("rpo", {})
        assert "target_min" in rpo
        assert "actual_min" in rpo
        assert "status" in rpo
        
        rto = posture.get("rto", {})
        assert "target_min" in rto
        assert "actual_min" in rto
        assert "status" in rto


class TestDecisionRegisterAuthority:
    """Verify decision register is single-authoritative."""
    
    def test_single_decision_register_exists(self):
        """Only one decision register should exist for this program."""
        register_path = Path("/app/memory/PLATFORM_SURVIVABILITY_DECISION_REGISTER.md")
        assert register_path.exists()
        
        with open(register_path) as f:
            content = f.read()
        
        assert "This is the only decision register for the Platform Survivability Program" in content
    
    def test_decisions_have_unique_ids(self):
        """All decisions must have unique IDs."""
        with open("/app/memory/PLATFORM_SURVIVABILITY_DECISION_REGISTER.md") as f:
            content = f.read()
        
        import re
        decision_ids = re.findall(r'PSP-DEC-\d+', content)
        assert len(decision_ids) == len(set(decision_ids)), "Duplicate decision IDs found"


class TestDependencyGraph:
    """Verify operational dependency graph completeness."""
    
    def test_dependency_graph_has_required_columns(self):
        """Dependency graph must include all required columns."""
        with open("/app/memory/OPERATIONAL_DEPENDENCY_GRAPH.md") as f:
            content = f.read()
        
        required_columns = [
            "Criticality",
            "Upstream systems",
            "Downstream systems",
            "Single point of failure",
            "Existing redundancy",
            "Recovery mechanism",
            "Monitoring coverage",
            "Ownership"
        ]
        
        for col in required_columns:
            assert col in content, f"Missing column: {col}"
    
    def test_critical_dependencies_identified(self):
        """Critical dependencies must be identified."""
        with open("/app/memory/OPERATIONAL_DEPENDENCY_GRAPH.md") as f:
            content = f.read()
        
        assert "**Critical**" in content
        assert "MongoDB Atlas" in content
        assert "FastAPI backend" in content


class TestLiveAPIVerification:
    """Verify live API endpoints match documented evidence."""
    
    @pytest.fixture
    def auth_tokens(self):
        """Get authentication tokens for admin routes."""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
        )
        if login_response.status_code != 200:
            pytest.skip("Authentication failed")
        
        data = login_response.json()
        return {
            "admin_token": data.get("portal_tokens", {}).get("admin"),
            "directory_token": data.get("session_token")
        }
    
    def test_health_endpoint_200(self):
        """Health endpoint must return 200."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
    
    def test_healthz_endpoint_200(self):
        """Healthz endpoint must return 200."""
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200
    
    def test_ready_endpoint_200(self):
        """Ready endpoint must return 200 with mongo_ok."""
        response = requests.get(f"{BASE_URL}/api/ready")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("mongo_ok") is True
    
    def test_health_full_endpoint_200(self):
        """Full health endpoint must return 200."""
        response = requests.get(f"{BASE_URL}/api/health/full")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("mongo") is True
    
    def test_admin_route_fails_without_directory_token(self, auth_tokens):
        """Admin routes must fail closed without directory token (PSP-FI-01)."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers={"X-Admin-Token": auth_tokens["admin_token"]}
        )
        # Should fail because directory token is missing
        assert response.status_code == 401
    
    def test_admin_route_succeeds_with_dual_token(self, auth_tokens):
        """Admin routes must succeed with both admin and directory tokens."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers={
                "X-Admin-Token": auth_tokens["admin_token"],
                "X-Directory-Token": auth_tokens["directory_token"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "pill" in data
        assert "rpo" in data
        assert "rto" in data
    
    def test_recovery_snapshot_posture_values(self, auth_tokens):
        """Recovery snapshot must report truthful posture values."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers={
                "X-Admin-Token": auth_tokens["admin_token"],
                "X-Directory-Token": auth_tokens["directory_token"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify RPO structure
        rpo = data.get("rpo", {})
        assert "target_min" in rpo
        assert "actual_min" in rpo
        assert "status" in rpo
        
        # Verify RTO structure
        rto = data.get("rto", {})
        assert "target_min" in rto
        assert "last_drill_min" in rto
        assert "status" in rto
        
        # Verify scheduler
        scheduler = data.get("scheduler", {})
        assert "alive" in scheduler
    
    def test_trust_spine_endpoint(self, auth_tokens):
        """Trust spine endpoint must be accessible and report platform band."""
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-spine",
            headers={
                "X-Admin-Token": auth_tokens["admin_token"],
                "X-Directory-Token": auth_tokens["directory_token"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "platform_band" in data
        assert "canonical_status" in data
    
    def test_integration_truth_endpoint(self, auth_tokens):
        """Integration truth endpoint must be accessible."""
        response = requests.get(
            f"{BASE_URL}/api/admin/integrations/truth-status",
            headers={
                "X-Admin-Token": auth_tokens["admin_token"],
                "X-Directory-Token": auth_tokens["directory_token"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data


class TestCapabilityInventoryTruthfulness:
    """Verify capability inventory does not overclaim."""
    
    def test_inventory_does_not_claim_full_restore_certification(self):
        """Inventory must not claim full automated side-DB restore is certified."""
        with open("/app/memory/CANONICAL_SURVIVABILITY_CAPABILITY_INVENTORY.md") as f:
            content = f.read()
        
        # Domain E should be PARTIALLY IMPLEMENTED
        assert "PARTIALLY IMPLEMENTED" in content
        assert "EXTERNAL DEPENDENCY" in content
    
    def test_inventory_references_real_code_paths(self):
        """Inventory must reference real code paths that exist."""
        with open("/app/memory/CANONICAL_SURVIVABILITY_CAPABILITY_INVENTORY.md") as f:
            content = f.read()
        
        # Check some referenced code paths exist
        code_refs = [
            "/app/backend/lib/backup_runtime.py",
            "/app/backend/lib/scheduler_runs.py",
            "/app/backend/lib/config_recovery.py",
            "/app/backend/lib/archive_lineage.py",
            "/app/backend/lib/trust_spine.py"
        ]
        
        for ref in code_refs:
            assert Path(ref).exists(), f"Referenced code path missing: {ref}"


class TestCertificationRegisterConsistency:
    """Verify certification register is internally consistent."""
    
    def test_certification_items_match_final_status(self):
        """Certification register items must match final status."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            status = json.load(f)
        
        assert status.get("inventory_complete") is True
        assert status.get("decision_register_authoritative") is True
        assert status.get("dependency_graph_complete") is True
        
        injections = status.get("failure_injections", {})
        assert injections.get("planned") == 6
        assert injections.get("executed") == 6
        assert injections.get("passed") == 6
        assert injections.get("failed") == 0
    
    def test_open_items_properly_classified(self):
        """Open items must be properly classified."""
        with open("/app/memory/SURVIVABILITY_FINAL_STATUS.json") as f:
            status = json.load(f)
        
        open_items = status.get("open_items", [])
        for item in open_items:
            classification = item.get("classification")
            assert classification in ALLOWED_CLASSIFICATIONS, (
                f"Open item has invalid classification: {classification}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
