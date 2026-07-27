"""
Wave 3 Formal Closeout Verification Tests

This test suite verifies the governance-only constitutional checkpoint for Wave 3 Formal Closeout.
It validates:
1. Repository freeze baseline is recorded and closeout outputs exist
2. Every Wave 3 family has exactly one final disposition with allowed vocabulary
3. ROADMAP.md current-state claims match closeout outputs
4. S1-4 is documented as repository-complete with governance-deferred Preview boundary
5. Historical evidence artifacts are present and valid JSON
6. No runtime implementation work was introduced during closeout
7. Transition gate result is coherent
"""

import pytest
import json
import os
from pathlib import Path

# Paths
MEMORY_DIR = Path("/app/memory")
TEST_REPORTS_DIR = Path("/app/test_reports")

# Allowed disposition vocabulary per WAVE_3_CERTIFICATION_REGISTER.md
ALLOWED_DISPOSITIONS = {
    "ADOPTED",
    "ADOPTED WITH GOVERNANCE BOUNDARY",
    "ACCEPTED RISK",
    "DEFERRED",
    "REJECTED"
}

# Expected Wave 3 families and their dispositions
EXPECTED_FAMILY_DISPOSITIONS = {
    "family_1": "ADOPTED",
    "family_2": "ADOPTED",
    "family_3a": "ADOPTED",
    "family_3b": "ADOPTED",
    "family_3c": "ADOPTED",
    "family_3d_1": "ADOPTED",
    "family_3d_2": "REJECTED"
}

# Expected closeout output files
CLOSEOUT_OUTPUT_FILES = [
    "WAVE_3_FORMAL_CLOSEOUT.md",
    "WAVE_3_CERTIFICATION_REGISTER.md",
    "WAVE_3_GOVERNANCE_RECONCILIATION.md",
    "WAVE_3_FINAL_STATUS.json"
]

# Historical evidence files that should be restored
HISTORICAL_EVIDENCE_FILES = [
    "iteration_39.json",
    "iteration_40.json"
]

# Repository freeze baseline commit
EXPECTED_BASELINE_COMMIT = "8d3c5de441ad91799dd96e308a10ba3e29da4604"


class TestCloseoutOutputsExist:
    """Test 1: Repository freeze baseline is recorded and closeout outputs exist"""
    
    def test_all_closeout_outputs_exist(self):
        """All four canonical closeout outputs must exist"""
        for filename in CLOSEOUT_OUTPUT_FILES:
            filepath = MEMORY_DIR / filename
            assert filepath.exists(), f"Missing closeout output: {filename}"
            assert filepath.stat().st_size > 0, f"Empty closeout output: {filename}"
        print("PASS: All 4 closeout outputs exist")
    
    def test_wave3_final_status_is_valid_json(self):
        """WAVE_3_FINAL_STATUS.json must be valid JSON"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        assert "track" in data
        assert "status" in data
        assert "repository_baseline" in data
        print("PASS: WAVE_3_FINAL_STATUS.json is valid JSON")
    
    def test_repository_baseline_commit_recorded(self):
        """Repository freeze baseline commit must be recorded"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        baseline = data.get("repository_baseline", {})
        assert baseline.get("commit") == EXPECTED_BASELINE_COMMIT, \
            f"Expected baseline commit {EXPECTED_BASELINE_COMMIT}, got {baseline.get('commit')}"
        print(f"PASS: Repository baseline commit recorded: {EXPECTED_BASELINE_COMMIT}")


class TestFamilyDispositions:
    """Test 2: Every Wave 3 family has exactly one final disposition with allowed vocabulary"""
    
    def test_all_families_have_disposition(self):
        """Every Wave 3 family must have exactly one disposition"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        families = data.get("wave_3_families", {})
        
        # Check all expected families are present
        for family_key in EXPECTED_FAMILY_DISPOSITIONS:
            assert family_key in families, f"Missing family: {family_key}"
        
        # Check no extra families
        for family_key in families:
            assert family_key in EXPECTED_FAMILY_DISPOSITIONS, f"Unexpected family: {family_key}"
        
        print(f"PASS: All {len(EXPECTED_FAMILY_DISPOSITIONS)} families have dispositions")
    
    def test_dispositions_match_expected(self):
        """Family dispositions must match expected values"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        families = data.get("wave_3_families", {})
        
        for family_key, expected_disposition in EXPECTED_FAMILY_DISPOSITIONS.items():
            actual = families.get(family_key)
            assert actual == expected_disposition, \
                f"Family {family_key}: expected {expected_disposition}, got {actual}"
        
        print("PASS: All family dispositions match expected values")
    
    def test_dispositions_use_allowed_vocabulary(self):
        """All dispositions must use allowed vocabulary"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        families = data.get("wave_3_families", {})
        deps = data.get("governing_certification_dependencies", {})
        
        all_dispositions = list(families.values()) + list(deps.values())
        
        for disposition in all_dispositions:
            assert disposition in ALLOWED_DISPOSITIONS, \
                f"Invalid disposition: {disposition}. Allowed: {ALLOWED_DISPOSITIONS}"
        
        print("PASS: All dispositions use allowed vocabulary")


class TestRoadmapConsistency:
    """Test 3: ROADMAP.md current-state claims match closeout outputs"""
    
    def test_roadmap_wave3_status_complete(self):
        """ROADMAP.md must show Wave 3 Formal Closeout as COMPLETE"""
        filepath = MEMORY_DIR / "ROADMAP.md"
        content = filepath.read_text()
        
        assert "Wave 3 Formal Closeout: **COMPLETE**" in content, \
            "ROADMAP.md must show Wave 3 Formal Closeout as COMPLETE"
        print("PASS: ROADMAP.md shows Wave 3 Formal Closeout as COMPLETE")
    
    def test_roadmap_survivability_ready(self):
        """ROADMAP.md must show Platform Survivability as READY TO RESUME"""
        filepath = MEMORY_DIR / "ROADMAP.md"
        content = filepath.read_text()
        
        assert "Platform Survivability Program: **READY TO RESUME**" in content, \
            "ROADMAP.md must show Platform Survivability as READY TO RESUME"
        print("PASS: ROADMAP.md shows Platform Survivability as READY TO RESUME")
    
    def test_roadmap_prr_not_authorized(self):
        """ROADMAP.md must show PRR as NOT AUTHORIZED"""
        filepath = MEMORY_DIR / "ROADMAP.md"
        content = filepath.read_text()
        
        assert "Production Readiness Review (PRR): **NOT AUTHORIZED**" in content, \
            "ROADMAP.md must show PRR as NOT AUTHORIZED"
        print("PASS: ROADMAP.md shows PRR as NOT AUTHORIZED")
    
    def test_roadmap_production_not_authorized(self):
        """ROADMAP.md must show Production deployment as NOT AUTHORIZED"""
        filepath = MEMORY_DIR / "ROADMAP.md"
        content = filepath.read_text()
        
        assert "Production deployment: **NOT AUTHORIZED**" in content, \
            "ROADMAP.md must show Production deployment as NOT AUTHORIZED"
        print("PASS: ROADMAP.md shows Production deployment as NOT AUTHORIZED")
    
    def test_roadmap_family_statuses_match_closeout(self):
        """ROADMAP.md family statuses must match closeout"""
        filepath = MEMORY_DIR / "ROADMAP.md"
        content = filepath.read_text()
        
        # Check each family status in ROADMAP matches expected
        assert "Family 1 — OCC Health Aggregator: **ADOPTED**" in content
        assert "Family 2 — OCC Trust Events: **ADOPTED**" in content
        assert "Family 3A — Core Admin Operations: **ADOPTED**" in content
        assert "Family 3B — Operations Actions: **ADOPTED**" in content
        assert "Family 3C — Operational Events: **ADOPTED**" in content
        assert "Family 3D-1 — Asset Spine Canonical Registry: **ADOPTED**" in content
        assert "Family 3D-2 — External Asset Mapping & Reconciliation: **REJECTED**" in content
        
        print("PASS: ROADMAP.md family statuses match closeout")


class TestS14PreviewBoundary:
    """Test 4: S1-4 is documented as repository-complete with governance-deferred Preview boundary"""
    
    def test_s14_repository_complete(self):
        """S1-4 must be documented as repository implementation complete"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "Repository implementation complete" in content, \
            "S1-4 must be documented as repository implementation complete"
        print("PASS: S1-4 documented as repository implementation complete")
    
    def test_s14_not_repository_defect(self):
        """S1-4 must not be documented as a repository defect"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "No repository defect exists" in content, \
            "S1-4 must state no repository defect exists"
        print("PASS: S1-4 documented as not a repository defect")
    
    def test_s14_governance_deferred(self):
        """S1-4 live provider validation must be governance-deferred"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "Live provider validation deferred by governance" in content, \
            "S1-4 live provider validation must be governance-deferred"
        print("PASS: S1-4 live provider validation is governance-deferred")
    
    def test_s14_failed_run_preserved(self):
        """Failed run s1-4-cert-e217a5ffd8 must be preserved as historical evidence"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "s1-4-cert-e217a5ffd8" in content, \
            "Failed run s1-4-cert-e217a5ffd8 must be referenced"
        assert "preserved as historical evidence" in content, \
            "Failed run must be preserved as historical evidence"
        print("PASS: Failed run s1-4-cert-e217a5ffd8 preserved as historical evidence")
    
    def test_s14_safe_capture_retained(self):
        """Preview SAFE_CAPTURE must be intentionally retained"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "SAFE_CAPTURE" in content and "intentionally retained" in content, \
            "Preview SAFE_CAPTURE must be intentionally retained"
        print("PASS: Preview SAFE_CAPTURE intentionally retained")
    
    def test_s14_disposition_in_register(self):
        """S1-4 must have ADOPTED WITH GOVERNANCE BOUNDARY disposition"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        deps = data.get("governing_certification_dependencies", {})
        s14_disposition = deps.get("s1_4_notification_delivery_repository_work")
        
        assert s14_disposition == "ADOPTED WITH GOVERNANCE BOUNDARY", \
            f"S1-4 disposition must be ADOPTED WITH GOVERNANCE BOUNDARY, got {s14_disposition}"
        print("PASS: S1-4 has ADOPTED WITH GOVERNANCE BOUNDARY disposition")


class TestHistoricalEvidence:
    """Test 5: Historical evidence artifacts are present and valid JSON"""
    
    def test_iteration_39_exists_and_valid(self):
        """iteration_39.json must exist and be valid JSON"""
        filepath = TEST_REPORTS_DIR / "iteration_39.json"
        assert filepath.exists(), "iteration_39.json must exist"
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert "summary" in data, "iteration_39.json must have summary field"
        print("PASS: iteration_39.json exists and is valid JSON")
    
    def test_iteration_40_exists_and_valid(self):
        """iteration_40.json must exist and be valid JSON"""
        filepath = TEST_REPORTS_DIR / "iteration_40.json"
        assert filepath.exists(), "iteration_40.json must exist"
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert "summary" in data, "iteration_40.json must have summary field"
        print("PASS: iteration_40.json exists and is valid JSON")
    
    def test_restoration_documented(self):
        """Historical evidence restoration must be documented"""
        filepath = MEMORY_DIR / "WAVE_3_GOVERNANCE_RECONCILIATION.md"
        content = filepath.read_text()
        
        assert "iteration_39.json" in content, "iteration_39.json restoration must be documented"
        assert "iteration_40.json" in content, "iteration_40.json restoration must be documented"
        assert "historical evidence recovery" in content, \
            "Restoration must be classified as historical evidence recovery"
        print("PASS: Historical evidence restoration documented")
    
    def test_restoration_not_new_implementation(self):
        """Restoration must be classified as evidence recovery, not new implementation"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "historical evidence recovery" in content, \
            "Restoration must be classified as historical evidence recovery"
        assert "not new implementation" in content or "not implementation" in content, \
            "Restoration must not be classified as new implementation"
        print("PASS: Restoration classified as evidence recovery, not implementation")


class TestNoRuntimeChanges:
    """Test 6: No runtime implementation work was introduced during closeout"""
    
    def test_regression_check_no_runtime_changes(self):
        """WAVE_3_FINAL_STATUS.json must confirm no runtime changes"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        regression = data.get("regression_check", {})
        
        assert regression.get("runtime_implementation_changed_during_closeout") == False, \
            "runtime_implementation_changed_during_closeout must be False"
        assert regression.get("documentation_only_reconciliation") == True, \
            "documentation_only_reconciliation must be True"
        assert regression.get("closeout_invalidated_by_drift") == False, \
            "closeout_invalidated_by_drift must be False"
        
        print("PASS: No runtime implementation changes during closeout")
    
    def test_closeout_documents_no_runtime_changes(self):
        """WAVE_3_FORMAL_CLOSEOUT.md must document no runtime changes"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "no runtime implementation files were changed" in content, \
            "Closeout must document no runtime implementation files changed"
        print("PASS: Closeout documents no runtime implementation changes")


class TestTransitionGate:
    """Test 7: Transition gate result is coherent"""
    
    def test_transition_gate_ready(self):
        """Transition gate must be READY"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        assert data.get("transition_gate") == "READY", \
            f"Transition gate must be READY, got {data.get('transition_gate')}"
        print("PASS: Transition gate is READY")
    
    def test_status_complete(self):
        """Status must be COMPLETE"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        assert data.get("status") == "COMPLETE", \
            f"Status must be COMPLETE, got {data.get('status')}"
        print("PASS: Status is COMPLETE")
    
    def test_platform_survivability_may_resume(self):
        """Platform Survivability must be authorized to resume"""
        filepath = MEMORY_DIR / "WAVE_3_FORMAL_CLOSEOUT.md"
        content = filepath.read_text()
        
        assert "Platform Survivability Program may resume" in content or \
               "Platform Survivability may resume" in content, \
            "Platform Survivability must be authorized to resume"
        print("PASS: Platform Survivability may resume")
    
    def test_prr_not_authorized(self):
        """PRR must remain unauthorized"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        remaining = data.get("remaining_work", {})
        production_work = remaining.get("production_work", [])
        
        assert "Production Readiness Review" in production_work, \
            "PRR must be in remaining production work"
        print("PASS: PRR remains unauthorized (in remaining production work)")
    
    def test_production_not_authorized(self):
        """Production deployment must remain unauthorized"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        remaining = data.get("remaining_work", {})
        production_work = remaining.get("production_work", [])
        
        # Check for production deployment in remaining work
        has_production = any("Production deployment" in item or "production deployment" in item.lower() 
                           for item in production_work)
        assert has_production, "Production deployment must be in remaining production work"
        print("PASS: Production deployment remains unauthorized")
    
    def test_no_contradictory_status(self):
        """No contradictory current-state status values must remain"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        evidence = data.get("evidence_reconciliation", {})
        contradictions = evidence.get("contradictory_current_status_values_remaining", -1)
        
        assert contradictions == 0, \
            f"Contradictory status values must be 0, got {contradictions}"
        print("PASS: No contradictory current-state status values remain")


class TestEvidenceIntegrity:
    """Additional evidence integrity checks"""
    
    def test_all_referenced_evidence_exists(self):
        """All evidence files referenced in closeout must exist"""
        evidence_files = [
            "iteration_39.json",
            "iteration_40.json",
            "iteration_42.json",
            "iteration_43.json",
            "iteration_44.json",
            "iteration_45.json",
            "iteration_46.json",
            "iteration_47.json",
            "iteration_49.json",
            "iteration_50.json"
        ]
        
        for filename in evidence_files:
            filepath = TEST_REPORTS_DIR / filename
            assert filepath.exists(), f"Referenced evidence file missing: {filename}"
        
        print(f"PASS: All {len(evidence_files)} referenced evidence files exist")
    
    def test_historical_evidence_frozen(self):
        """Historical evidence must be marked as frozen"""
        filepath = MEMORY_DIR / "WAVE_3_FINAL_STATUS.json"
        with open(filepath) as f:
            data = json.load(f)
        
        evidence = data.get("evidence_reconciliation", {})
        assert evidence.get("historical_evidence_frozen") == True, \
            "Historical evidence must be frozen"
        print("PASS: Historical evidence is frozen")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
