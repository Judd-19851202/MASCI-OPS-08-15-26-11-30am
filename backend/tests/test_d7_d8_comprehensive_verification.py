"""
D7/D8 Comprehensive Verification Tests
Tests for:
1. operational_facts one-row query path is project-bounded and tenant-aware
2. Definitively empty PM scope returns empty payloads before Mongo is queried
3. D7/D8 documentation artifacts and machine-readable baseline exist and are coherent
4. Release-gate performance-baseline contract is wired
5. Runtime/admin diagnostics expose bounded self-healing foundation
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT = Path("/app")


class TestOperationalFactsQueryTargeting:
    """Verify operational_facts queries are project-bounded and tenant-aware."""

    def test_trench_kpi_lift_fact_query_helper_accepts_project_id(self):
        """The _fact_query helper must accept project_id parameter."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from services.safety_portal_trench.trench_kpi_lift import _fact_query
        from services.trench_safety.facts_emitter import SOURCE_TYPE_TRENCH
        
        # Without project_id
        q1 = _fact_query("excavation_day_fact")
        assert "project_id" not in q1
        assert q1["tenant_id"] == "masci"
        assert q1["source_type"] == SOURCE_TYPE_TRENCH  # "safety_form"
        assert q1["is_current"] is True
        
        # With project_id
        q2 = _fact_query("excavation_day_fact", project_id="20-01")
        assert q2["project_id"] == "20-01"
        assert q2["tenant_id"] == "masci"

    def test_trench_project_intelligence_facts_query_includes_project_id(self):
        """The _facts_query helper must include project_id."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from routes.trench_project_intelligence import _facts_query
        from services.trench_safety.facts_emitter import SOURCE_TYPE_TRENCH
        
        q = _facts_query("20-01", "excavation_day_fact")
        assert q["project_id"] == "20-01"
        assert q["tenant_id"] == "masci"
        assert q["source_type"] == SOURCE_TYPE_TRENCH  # "safety_form"
        assert q["source_id"] == "trench_safety"
        assert q["fact_type"] == "excavation_day_fact"
        assert q["is_current"] is True

    def test_derived_views_excavation_activity_includes_project_id(self):
        """excavation_activity_view query must include project_id."""
        # Verify the code structure includes project_id in query
        code = (REPO_ROOT / "backend/services/trench_safety/derived_views.py").read_text()
        assert '"project_id": str(project_number)' in code
        assert '"tenant_id": TENANT_DEFAULT' in code


class TestPmScopeShortCircuit:
    """Verify definitively empty PM scope short-circuits before Mongo."""

    def test_pm_scope_is_definitively_empty_logic(self):
        """PmScope.is_definitively_empty() returns True only for non-admin with no projects."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from pm_auth import PmScope
        
        # Non-admin with no projects = definitively empty
        assert PmScope(is_admin=False, project_numbers=[]).is_definitively_empty() is True
        
        # Non-admin with projects = not empty
        assert PmScope(is_admin=False, project_numbers=["20-01"]).is_definitively_empty() is False
        
        # Admin with no projects = not empty (admin sees all)
        assert PmScope(is_admin=True, project_numbers=[]).is_definitively_empty() is False

    def test_qaqc_route_has_short_circuit(self):
        """qaqc.py must check is_definitively_empty() before Mongo queries."""
        code = (REPO_ROOT / "backend/routes/qaqc.py").read_text()
        assert "is_definitively_empty()" in code
        # Should return empty list when scope is empty
        assert "return []" in code or "return {" in code

    def test_daily_reports_route_has_short_circuit(self):
        """daily_reports.py must check is_definitively_empty() before Mongo queries."""
        code = (REPO_ROOT / "backend/routes/daily_reports.py").read_text()
        assert "is_definitively_empty()" in code

    def test_safety_route_has_short_circuit(self):
        """safety.py must check is_definitively_empty() before Mongo queries."""
        code = (REPO_ROOT / "backend/routes/safety.py").read_text()
        assert "is_definitively_empty()" in code

    def test_equipment_route_has_short_circuit(self):
        """equipment.py must check is_definitively_empty() before Mongo queries."""
        code = (REPO_ROOT / "backend/routes/equipment.py").read_text()
        assert "is_definitively_empty()" in code

    def test_job_photos_route_has_short_circuit(self):
        """job_photos.py must check is_definitively_empty() before Mongo queries."""
        code = (REPO_ROOT / "backend/routes/job_photos.py").read_text()
        assert "is_definitively_empty()" in code


class TestD7D8DocumentationArtifacts:
    """Verify D7/D8 documentation artifacts exist and are coherent."""

    REQUIRED_DOCS = [
        "docs/performance/performance_baseline.json",
        "docs/performance/PERFORMANCE_BASELINE.md",
        "docs/performance/ATLAS_ALERT_EVIDENCE_REGISTER.md",
        "docs/performance/query_inventory.json",
        "docs/performance/INDEX_QUERY_RECOMMENDATION_REGISTER.md",
        "docs/architecture/PERFORMANCE_EVENT_CONTRACT.md",
        "docs/architecture/SAFE_SELF_HEALING_FOUNDATION.md",
    ]

    def test_all_required_docs_exist(self):
        """All D7/D8 documentation artifacts must exist."""
        for rel_path in self.REQUIRED_DOCS:
            path = REPO_ROOT / rel_path
            assert path.exists(), f"Missing: {rel_path}"

    def test_performance_baseline_json_is_valid(self):
        """performance_baseline.json must be valid JSON with required fields."""
        path = REPO_ROOT / "docs/performance/performance_baseline.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        
        required_fields = ["checkpoint", "captured_at", "backend", "frontend", "scheduler", "workspace_resources"]
        for field in required_fields:
            assert field in payload, f"Missing field: {field}"
        
        assert payload["checkpoint"] == "D7/D8"

    def test_query_inventory_json_is_valid(self):
        """query_inventory.json must be valid JSON with collections."""
        path = REPO_ROOT / "docs/performance/query_inventory.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        
        assert "checkpoint" in payload
        assert "collections" in payload
        assert isinstance(payload["collections"], list)
        
        # Should have operational_facts collection
        coll_names = [c["collection"] for c in payload["collections"]]
        assert "operational_facts" in coll_names

    def test_performance_baseline_md_references_d7_d8(self):
        """PERFORMANCE_BASELINE.md must reference D7/D8."""
        path = REPO_ROOT / "docs/performance/PERFORMANCE_BASELINE.md"
        content = path.read_text(encoding="utf-8")
        assert "D7/D8" in content

    def test_safe_self_healing_foundation_md_exists_and_coherent(self):
        """SAFE_SELF_HEALING_FOUNDATION.md must exist and reference runtime_reliability."""
        path = REPO_ROOT / "docs/architecture/SAFE_SELF_HEALING_FOUNDATION.md"
        content = path.read_text(encoding="utf-8")
        assert "runtime_reliability" in content
        assert "bounded" in content.lower()


class TestReleaseGatePerformanceBaseline:
    """Verify release-gate performance-baseline contract is wired."""

    def test_release_gate_manifest_has_performance_baseline_contract(self):
        """release_gate_manifest.json must have performance-baseline-contract gate."""
        path = REPO_ROOT / "docs/governance/release_gate_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        
        gate_ids = [g["gate_id"] for g in manifest.get("mandatory_checks", [])]
        assert "performance-baseline-contract" in gate_ids

    def test_release_gate_manifest_has_performance_prerequisites(self):
        """release_gate_manifest.json must have performance_prerequisites."""
        path = REPO_ROOT / "docs/governance/release_gate_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        
        perf = manifest.get("performance_prerequisites", {})
        assert perf.get("machine_readable_baseline") == "docs/performance/performance_baseline.json"
        assert perf.get("query_inventory") == "docs/performance/query_inventory.json"
        assert perf.get("safe_self_healing_contract") == "docs/architecture/SAFE_SELF_HEALING_FOUNDATION.md"

    def test_release_gate_script_has_performance_baseline_gate(self):
        """release_gate.py must have _performance_baseline_gate function."""
        code = (REPO_ROOT / "scripts/release_gate.py").read_text()
        assert "_performance_baseline_gate" in code
        assert '"performance-baseline-contract"' in code


class TestRuntimeAdminDiagnostics:
    """Verify runtime/admin diagnostics expose bounded self-healing foundation."""

    def test_admin_runtime_reliability_router_exists(self):
        """admin_runtime_reliability.py must exist and define router."""
        path = REPO_ROOT / "backend/routes/admin_runtime_reliability.py"
        assert path.exists()
        code = path.read_text()
        assert "build_runtime_reliability_router" in code

    def test_admin_router_has_runtime_health_endpoint(self):
        """Admin router must have /runtime-health endpoint."""
        code = (REPO_ROOT / "backend/routes/admin_runtime_reliability.py").read_text()
        assert "/runtime-health" in code

    def test_admin_router_has_performance_baseline_endpoint(self):
        """Admin router must have /performance-baseline endpoint."""
        code = (REPO_ROOT / "backend/routes/admin_runtime_reliability.py").read_text()
        assert "/performance-baseline" in code

    def test_runtime_reliability_has_safe_self_healing_state(self):
        """runtime_reliability.py must have safe_self_healing state."""
        code = (REPO_ROOT / "backend/lib/runtime_reliability.py").read_text()
        assert "safe_self_healing" in code
        assert "resource_relief_actions" in code

    def test_runtime_reliability_has_bounded_cleanup(self):
        """runtime_reliability.py must have bounded cleanup logic."""
        code = (REPO_ROOT / "backend/lib/runtime_reliability.py").read_text()
        # Should have disk threshold constants
        assert "DISK_WARN_PERCENT" in code or "DISK_FAIL_PERCENT" in code


class TestD1FailClosedPreservation:
    """Verify D1 fail-closed behavior is preserved."""

    def test_performance_baseline_notes_intentional_fail_closed(self):
        """performance_baseline.json must note intentional fail-closed."""
        path = REPO_ROOT / "docs/performance/performance_baseline.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        
        notes = payload.get("notes", [])
        assert any("fail-closed" in note.lower() or "502" in note for note in notes)

    def test_preview_probe_disposition_is_intentional(self):
        """Preview probe disposition must be INTENTIONAL_FAIL_CLOSED."""
        path = REPO_ROOT / "docs/performance/performance_baseline.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        
        backend = payload.get("backend", {})
        preview_probe = backend.get("preview_probe", {})
        
        # All probes should have INTENTIONAL_FAIL_CLOSED disposition
        for probe_name in ["health", "ready", "version", "health_full"]:
            probe = preview_probe.get(probe_name, {})
            if probe.get("status") == 502:
                assert probe.get("disposition") == "INTENTIONAL_FAIL_CLOSED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
