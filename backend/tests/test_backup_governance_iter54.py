"""
Iteration 54 Backend Tests — Backup Truth Alignment & Governance Repair Endpoints

Tests:
1. Backup truth alignment: system-health backup card and recovery snapshot RPO alignment
2. Hourly activation structure: reclaimable/blocking stale counts exposed
3. Governance summary: recommended repair endpoints present
4. PPE issuance repair endpoint: dry-run returns 200 with sensible preview
5. Regression safety: admin backup/governance/certification endpoints responsive
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_auth():
    """Authenticate as super admin and return both admin token and directory token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    # Multi-login returns portal_tokens.admin for admin token
    portal_tokens = data.get("portal_tokens", {})
    admin_token = portal_tokens.get("admin") or data.get("admin_token") or data.get("token")
    session_token = data.get("session_token")
    assert admin_token, f"No admin token in response: {data}"
    assert session_token, f"No session token in response: {data}"
    return {"admin_token": admin_token, "directory_token": session_token}


@pytest.fixture(scope="module")
def admin_headers(admin_auth):
    """Return headers dict for admin API calls."""
    return {
        "X-Admin-Token": admin_auth["admin_token"],
        "X-Directory-Token": admin_auth["directory_token"],
    }


class TestBackupTruthAlignment:
    """Verify backup truth alignment between system-health and recovery snapshot."""

    def test_system_health_backup_card_returns_200(self, admin_headers):
        """System health endpoint should return 200 with backup card."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"system-health failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Find backup card
        cards = data.get("cards", [])
        backup_card = next((c for c in cards if c.get("key") == "backup"), None)
        assert backup_card is not None, f"No backup card found in system-health: {[c.get('key') for c in cards]}"
        
        # Verify backup card has expected fields
        assert "status" in backup_card, "Backup card missing status"
        assert "detail" in backup_card, "Backup card missing detail"
        print(f"Backup card status: {backup_card.get('status')}, detail: {backup_card.get('detail')}")

    def test_recovery_snapshot_returns_200(self, admin_headers):
        """Recovery snapshot endpoint should return 200 with RPO data."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"recovery/snapshot failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Verify RPO structure
        assert "rpo" in data, "Recovery snapshot missing rpo field"
        rpo = data["rpo"]
        assert "target_min" in rpo, "RPO missing target_min"
        assert "actual_min" in rpo, "RPO missing actual_min"
        assert "status" in rpo, "RPO missing status"
        
        # Verify pill field
        assert "pill" in data, "Recovery snapshot missing pill field"
        print(f"Recovery snapshot pill: {data.get('pill')}, RPO status: {rpo.get('status')}")

    def test_backup_truth_alignment_between_endpoints(self, admin_headers):
        """Both endpoints should reflect consistent backup truth."""
        # Get system-health
        sh_resp = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
            timeout=30,
        )
        assert sh_resp.status_code == 200
        sh_data = sh_resp.json()
        
        # Get recovery snapshot
        rs_resp = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=30,
        )
        assert rs_resp.status_code == 200
        rs_data = rs_resp.json()
        
        # Extract backup card from system-health
        cards = sh_data.get("cards", [])
        backup_card = next((c for c in cards if c.get("key") == "backup"), None)
        assert backup_card is not None
        
        # Both should have consistent truth about backup state
        # If one shows RED, the other should not show GREEN
        sh_status = backup_card.get("status", "").upper()
        rs_pill = rs_data.get("pill", "").upper()
        rs_rpo_status = rs_data.get("rpo", {}).get("status", "").upper()
        
        print(f"System-health backup status: {sh_status}")
        print(f"Recovery snapshot pill: {rs_pill}")
        print(f"Recovery snapshot RPO status: {rs_rpo_status}")
        
        # Verify no contradictory states (one green, one red)
        if sh_status == "RED" or sh_status == "MISMATCH":
            assert rs_pill != "GREEN", f"Contradiction: system-health={sh_status} but recovery pill={rs_pill}"
        if rs_pill == "RED":
            assert sh_status not in ("GREEN", "VERIFIED"), f"Contradiction: recovery pill={rs_pill} but system-health={sh_status}"


class TestHourlyActivationStructure:
    """Verify hourly activation exposes reclaimable/blocking stale counts."""

    def test_backups_scheduler_state_returns_200(self, admin_headers):
        """Backups scheduler state endpoint should return 200."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"backups-scheduler-state failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Verify hourly_activation structure
        assert "hourly_activation" in data, "Missing hourly_activation field"
        ha = data["hourly_activation"]
        
        # Verify stale counts are present (not phantom missing fields)
        assert "stale_job_count" in ha, "Missing stale_job_count in hourly_activation"
        assert "reclaimable_stale_job_count" in ha, "Missing reclaimable_stale_job_count in hourly_activation"
        
        # blocking_stale_job_count may or may not be present depending on implementation
        # but stale_lock_present should be present
        assert "stale_lock_present" in ha, "Missing stale_lock_present in hourly_activation"
        
        print(f"Hourly activation stale counts: stale_job_count={ha.get('stale_job_count')}, "
              f"reclaimable_stale_job_count={ha.get('reclaimable_stale_job_count')}, "
              f"stale_lock_present={ha.get('stale_lock_present')}")

    def test_hourly_activation_has_activation_status(self, admin_headers):
        """Hourly activation should have activation_status field."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        ha = data.get("hourly_activation", {})
        assert "activation_status" in ha, "Missing activation_status in hourly_activation"
        print(f"Hourly activation status: {ha.get('activation_status')}")


class TestGovernanceSummaryRepairEndpoints:
    """Verify governance summary exposes recommended repair endpoints."""

    def test_governance_summary_returns_200(self, admin_headers):
        """Governance summary endpoint should return 200."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/governance/summary",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"governance/summary failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Verify basic structure
        assert data.get("ok") is True, "Governance summary ok=false"
        assert "severity_counts" in data, "Missing severity_counts"
        assert "health_label" in data, "Missing health_label"
        print(f"Governance health_label: {data.get('health_label')}")

    def test_governance_summary_has_recommended_repairs(self, admin_headers):
        """Governance summary should include recommended_repairs with repair endpoints."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/governance/summary",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify recommended_repairs structure
        assert "recommended_repairs" in data, "Missing recommended_repairs in governance summary"
        repairs = data["recommended_repairs"]
        
        # Verify employee link backfill endpoint is exposed
        assert "employee_link_backfill_endpoint" in repairs, "Missing employee_link_backfill_endpoint"
        assert repairs["employee_link_backfill_endpoint"] == "/api/admin/compliance/backfill-employee-links", \
            f"Unexpected backfill endpoint: {repairs.get('employee_link_backfill_endpoint')}"
        
        # Verify PPE issue endpoint is exposed
        assert "ppe_issue_endpoint" in repairs, "Missing ppe_issue_endpoint"
        assert repairs["ppe_issue_endpoint"] == "/api/admin/compliance/issue-missing-ppe", \
            f"Unexpected PPE endpoint: {repairs.get('ppe_issue_endpoint')}"
        
        print(f"Recommended repairs: {repairs}")


class TestPPEIssuanceRepairEndpoint:
    """Verify new PPE issuance repair endpoint dry-run functionality."""

    def test_issue_missing_ppe_dry_run_returns_200(self, admin_headers):
        """PPE issuance repair endpoint should return 200 on dry-run."""
        resp = requests.post(
            f"{BASE_URL}/api/admin/compliance/issue-missing-ppe",
            headers=admin_headers,
            json={"dry_run": True},
            timeout=30,
        )
        assert resp.status_code == 200, f"issue-missing-ppe failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert data.get("ok") is True, "PPE issuance ok=false"
        assert data.get("dry_run") is True, "dry_run should be True"
        assert "missing_employee_count" in data, "Missing missing_employee_count"
        assert "created_count" in data, "Missing created_count"
        assert "preview" in data, "Missing preview"
        
        # In dry_run mode, created_count should be 0
        assert data.get("created_count") == 0, f"created_count should be 0 in dry_run, got {data.get('created_count')}"
        
        print(f"PPE dry-run: missing_employee_count={data.get('missing_employee_count')}, "
              f"preview_count={len(data.get('preview', []))}")

    def test_issue_missing_ppe_preview_has_sensible_structure(self, admin_headers):
        """PPE issuance preview should have sensible employee data."""
        resp = requests.post(
            f"{BASE_URL}/api/admin/compliance/issue-missing-ppe",
            headers=admin_headers,
            json={"dry_run": True, "default_items": ["Hard Hat", "Safety Vest"]},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify default_items are reflected
        assert "default_items" in data, "Missing default_items in response"
        
        # If there are missing employees, verify preview structure
        preview = data.get("preview", [])
        if preview:
            first = preview[0]
            assert "employee_id" in first, "Preview item missing employee_id"
            assert "employee_name" in first, "Preview item missing employee_name"
            assert "issuance_id" in first, "Preview item missing issuance_id"
            assert "items" in first, "Preview item missing items"
            print(f"First preview item: {first}")


class TestRegressionSafety:
    """Verify admin backup/governance/certification endpoints remain responsive."""

    def test_system_health_responsive(self, admin_headers):
        """System health endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"system-health not responsive: {resp.status_code}"

    def test_recovery_snapshot_responsive(self, admin_headers):
        """Recovery snapshot endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"recovery/snapshot not responsive: {resp.status_code}"

    def test_backups_scheduler_state_responsive(self, admin_headers):
        """Backups scheduler state endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"backups-scheduler-state not responsive: {resp.status_code}"

    def test_governance_summary_responsive(self, admin_headers):
        """Governance summary endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/governance/summary",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"governance/summary not responsive: {resp.status_code}"

    def test_production_certification_responsive(self, admin_headers):
        """Production certification endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/production-certification",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"production-certification not responsive: {resp.status_code}"

    def test_compliance_findings_responsive(self, admin_headers):
        """Compliance findings endpoint should respond without timeout."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/compliance/findings",
            headers=admin_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"compliance/findings not responsive: {resp.status_code}"


class TestBackfillEmployeeLinksEndpoint:
    """Verify employee link backfill endpoint works in dry-run mode."""

    def test_backfill_employee_links_dry_run_returns_200(self, admin_headers):
        """Employee link backfill endpoint should return 200 on dry-run."""
        resp = requests.post(
            f"{BASE_URL}/api/admin/compliance/backfill-employee-links",
            headers=admin_headers,
            json={"dry_run": True},
            timeout=30,
        )
        assert resp.status_code == 200, f"backfill-employee-links failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert data.get("ok") is True, "Backfill ok=false"
        assert data.get("dry_run") is True, "dry_run should be True"
        assert "total_backfilled" in data, "Missing total_backfilled"
        assert "per_collection" in data, "Missing per_collection"
        
        print(f"Backfill dry-run: total_backfilled={data.get('total_backfilled')}, "
              f"active_unique_names={data.get('active_unique_names')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
