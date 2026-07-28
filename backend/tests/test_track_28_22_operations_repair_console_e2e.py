"""
TRACK 28.22 · Operations Repair Console E2E Tests

Tests for:
1. Operations Control Center endpoints (overview, audit/summary)
2. R2 lifecycle retention endpoints (retention, retention/policy, latest)
3. Admin health endpoints stability after scheduler truth refactor
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL not set", allow_module_level=True)

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


class TestAuthAndTokens:
    """Verify multi-login returns both admin and directory tokens."""

    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get admin and directory tokens via multi-login."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Multi-login failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        directory_token = data.get("session_token")
        assert admin_token, "No admin_token in portal_tokens"
        assert directory_token, "No session_token (directory token)"
        return {"admin_token": admin_token, "directory_token": directory_token}

    def test_multi_login_returns_tokens(self, auth_tokens):
        """Verify multi-login returns admin_token and directory_token."""
        assert auth_tokens.get("admin_token"), "admin_token missing"
        assert auth_tokens.get("directory_token"), "directory_token missing"
        print(f"✓ Multi-login successful, both tokens present")


class TestOperationsControlCenter:
    """Test Operations Control Center endpoints."""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for admin endpoints.
        
        Admin routes require BOTH X-Admin-Token and X-Directory-Token.
        - X-Admin-Token: portal_tokens.admin from multi-login
        - X-Directory-Token: session_token from multi-login
        """
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Multi-login failed: {resp.status_code}"
        data = resp.json()
        # Admin token is in portal_tokens.admin
        admin_token = data.get("portal_tokens", {}).get("admin")
        # Directory token is the session_token
        directory_token = data.get("session_token")
        assert admin_token, "No admin token in portal_tokens"
        assert directory_token, "No session_token (directory token)"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token,
        }
        return headers

    def test_operations_control_overview(self, auth_headers):
        """Test /api/admin/operations-control/overview returns operations with repair_contract."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/operations-control/overview",
            headers=auth_headers,
            timeout=60,
        )
        assert resp.status_code == 200, f"Overview failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "operations" in data, "Missing 'operations' key"
        assert "count" in data, "Missing 'count' key"
        
        # Check for governance operations
        ops = data["operations"]
        op_ids = [op.get("id") for op in ops]
        assert "governance.employee_link_backfill" in op_ids, "Missing governance.employee_link_backfill"
        assert "governance.issue_missing_ppe" in op_ids, "Missing governance.issue_missing_ppe"
        
        # Check repair_contract metadata on governance operations
        for op in ops:
            if op.get("id", "").startswith("governance."):
                assert "repair_contract" in op, f"Missing repair_contract on {op.get('id')}"
                contract = op["repair_contract"]
                assert "dry_run_required" in contract, "Missing dry_run_required in repair_contract"
                assert "confirmation_phrase" in contract, "Missing confirmation_phrase in repair_contract"
                assert "last_dry_run" in contract, "Missing last_dry_run in repair_contract"
                assert "last_apply" in contract, "Missing last_apply in repair_contract"
                print(f"✓ {op.get('id')} has repair_contract metadata")
        
        print(f"✓ Overview returned {data['count']} operations")

    def test_operations_control_audit_summary(self, auth_headers):
        """Test /api/admin/operations-control/audit/summary returns aggregated audit data."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/operations-control/audit/summary",
            headers=auth_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Audit summary failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "count" in data, "Missing 'count' key"
        assert "by_mode" in data, "Missing 'by_mode' key"
        assert "failure_count" in data, "Missing 'failure_count' key"
        assert "top_operations" in data, "Missing 'top_operations' key"
        print(f"✓ Audit summary: {data['count']} entries, {data['failure_count']} failures")

    def test_operations_control_audit_list(self, auth_headers):
        """Test /api/admin/operations-control/audit returns audit rows."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/operations-control/audit?limit=10",
            headers=auth_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Audit list failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "audit" in data, "Missing 'audit' key"
        assert "count" in data, "Missing 'count' key"
        print(f"✓ Audit list returned {data['count']} entries")


class TestR2LifecycleRetention:
    """Test R2 lifecycle retention endpoints."""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for admin endpoints."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Multi-login failed: {resp.status_code}"
        data = resp.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        directory_token = data.get("session_token")
        assert admin_token, "No admin token"
        assert directory_token, "No directory token"
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token,
        }

    def test_r2_lifecycle_latest(self, auth_headers):
        """Test /api/admin/r2/lifecycle/latest returns retention data."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/latest",
            headers=auth_headers,
            timeout=60,
        )
        # May return 404 if R2 lifecycle not configured on this environment
        if resp.status_code == 404:
            print("✓ R2 lifecycle not available on this environment (expected)")
            return
        assert resp.status_code == 200, f"Latest failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "retention" in data, "Missing 'retention' key"
        assert "health" in data, "Missing 'health' key"
        print(f"✓ R2 lifecycle latest returned with retention data")

    def test_r2_lifecycle_retention(self, auth_headers):
        """Test /api/admin/r2/lifecycle/retention returns authoritative retention data."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/retention",
            headers=auth_headers,
            timeout=60,
        )
        if resp.status_code == 404:
            print("✓ R2 lifecycle retention not available on this environment (expected)")
            return
        assert resp.status_code == 200, f"Retention failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "policy" in data, "Missing 'policy' key"
        assert "decisions" in data, "Missing 'decisions' key"
        assert "archive_count" in data, "Missing 'archive_count' key"
        
        # Verify policy structure
        policy = data["policy"]
        assert "architecture" in policy, "Missing architecture in policy"
        assert "hourly_hours" in policy, "Missing hourly_hours in policy"
        assert "daily_days" in policy, "Missing daily_days in policy"
        assert "weekly_days" in policy, "Missing weekly_days in policy"
        assert "monthly_months" in policy, "Missing monthly_months in policy"
        
        print(f"✓ R2 retention: {data['archive_count']} archives, policy architecture={policy['architecture']}")

    def test_r2_lifecycle_retention_policy(self, auth_headers):
        """Test /api/admin/r2/lifecycle/retention/policy returns policy metadata."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/retention/policy",
            headers=auth_headers,
            timeout=30,
        )
        if resp.status_code == 404:
            print("✓ R2 lifecycle retention/policy not available on this environment (expected)")
            return
        assert resp.status_code == 200, f"Retention policy failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "policy" in data, "Missing 'policy' key"
        assert "survivors_by_tier" in data, "Missing 'survivors_by_tier' key"
        assert "deleted_by_tier" in data, "Missing 'deleted_by_tier' key"
        print(f"✓ R2 retention policy returned with tier summaries")


class TestAdminHealthEndpoints:
    """Test admin health endpoints stability after scheduler truth refactor."""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for admin endpoints."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Multi-login failed: {resp.status_code}"
        data = resp.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        directory_token = data.get("session_token")
        assert admin_token, "No admin token"
        assert directory_token, "No directory token"
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token,
        }

    def test_backups_scheduler_state(self, auth_headers):
        """Test /api/admin/backups-scheduler-state returns scheduler truth."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=auth_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Scheduler state failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "scheduler" in data, "Missing 'scheduler' key"
        scheduler = data["scheduler"]
        assert "alive" in scheduler, "Missing 'alive' in scheduler"
        print(f"✓ Scheduler state: alive={scheduler.get('alive')}")

    def test_recovery_snapshot(self, auth_headers):
        """Test /api/admin/recovery/snapshot returns recovery truth."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=auth_headers,
            timeout=60,
        )
        assert resp.status_code == 200, f"Recovery snapshot failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "pill" in data, "Missing 'pill' key"
        assert "computed_at" in data, "Missing 'computed_at' key"
        print(f"✓ Recovery snapshot: pill={data.get('pill')}")

    def test_occ_health(self, auth_headers):
        """Test /api/admin/occ/health returns trust layer snapshot."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers=auth_headers,
            timeout=120,
        )
        assert resp.status_code == 200, f"OCC health failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "sections" in data or "overall_status" in data, "Missing expected keys in OCC health"
        print(f"✓ OCC health returned successfully")

    def test_integrations_health(self, auth_headers):
        """Test /api/admin/integrations/health returns integration probes."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/integrations/health",
            headers=auth_headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Integrations health failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "probes" in data or "status" in data, "Missing expected keys in integrations health"
        print(f"✓ Integrations health returned successfully")


class TestGovernanceRepairOperations:
    """Test governance repair operations dry-run endpoints."""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for admin endpoints."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Multi-login failed: {resp.status_code}"
        data = resp.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        directory_token = data.get("session_token")
        assert admin_token, "No admin token"
        assert directory_token, "No directory token"
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token,
        }

    def test_employee_link_backfill_dry_run(self, auth_headers):
        """Test governance.employee_link_backfill dry-run endpoint."""
        resp = requests.post(
            f"{BASE_URL}/api/admin/operations-control/operations/governance.employee_link_backfill/dry-run",
            headers=auth_headers,
            json={},
            timeout=60,
        )
        assert resp.status_code == 200, f"Employee link backfill dry-run failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "result" in data, "Missing 'result' key"
        result = data["result"]
        assert "status" in result, "Missing 'status' in result"
        assert "candidate_count" in result, "Missing 'candidate_count' in result"
        print(f"✓ Employee link backfill dry-run: status={result.get('status')}, candidates={result.get('candidate_count')}")

    def test_issue_missing_ppe_dry_run(self, auth_headers):
        """Test governance.issue_missing_ppe dry-run endpoint."""
        resp = requests.post(
            f"{BASE_URL}/api/admin/operations-control/operations/governance.issue_missing_ppe/dry-run",
            headers=auth_headers,
            json={},
            timeout=60,
        )
        assert resp.status_code == 200, f"Issue missing PPE dry-run failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        assert "result" in data, "Missing 'result' key"
        result = data["result"]
        assert "status" in result, "Missing 'status' in result"
        assert "candidate_count" in result, "Missing 'candidate_count' in result"
        print(f"✓ Issue missing PPE dry-run: status={result.get('status')}, candidates={result.get('candidate_count')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
