#!/usr/bin/env python3
"""
Backend API Testing for WP-18C5 - Schedule Actuals & Daily Work Plan
Verification of PM project controls schedule endpoints.

Tests the following endpoints for project ZZ-RUNTIME-CERT-2026:
1. GET /api/pm/project-controls/projects/{project_number}/schedule/actuals/overview
2. GET /api/pm/project-controls/projects/{project_number}/schedule/actuals/candidates
3. GET /api/pm/project-controls/projects/{project_number}/schedule/daily-work-plan
4. GET /api/pm/project-controls/projects/{project_number}/schedule/export (forecast_schedule_csv)
5. GET /api/pm/project-controls/projects/{project_number}/schedule/export (schedule_actuals_csv)
6. GET /api/pm/project-controls/projects/{project_number}/schedule/export (daily_work_plan_csv)
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
PM_CREDENTIALS = {
    "email": "cert.pm@example.com",
    "password": "CertProof2026!"
}

# Test project number
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.total = 0
    
    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed.append((test_name, details))
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str = ""):
        self.total += 1
        self.failed.append((test_name, details))
        print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   {details}")
    
    def summary(self):
        print("\n" + "="*80)
        print(f"WP-18C5 BACKEND TEST SUMMARY: {len(self.passed)}/{self.total} tests passed")
        print("="*80)
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for test_name, details in self.failed:
                print(f"  - {test_name}")
                if details:
                    print(f"    {details}")
        else:
            print("\n✅ ALL TESTS PASSED - BACKEND FLOW IS HEALTHY")
        return len(self.failed) == 0

def get_pm_token() -> Optional[str]:
    """Login as PM and get authentication token"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/pm/login",
            json=PM_CREDENTIALS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                print(f"✅ PM login successful, token obtained")
                return token
            else:
                print(f"❌ PM login response missing token")
                return None
        else:
            print(f"❌ PM login failed with status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ PM login exception: {str(e)}")
        return None

def get_schedule_version_id(token: str) -> Optional[str]:
    """Get a valid schedule version_id for testing exports"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/versions",
            headers={"X-PM-Token": token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items and len(items) > 0:
                version_id = items[0].get("version_id")
                print(f"✅ Found schedule version: {version_id}")
                return version_id
            else:
                print(f"⚠️  No schedule versions found for project {PROJECT_NUMBER}")
                return None
        else:
            print(f"⚠️  Failed to get schedule versions: status {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Exception getting schedule versions: {str(e)}")
        return None

def test_actuals_overview(results: TestResult, token: str):
    """Test GET /api/pm/project-controls/projects/{project_number}/schedule/actuals/overview"""
    test_name = f"GET /api/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/actuals/overview"
    try:
        response = requests.get(
            f"{BACKEND_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/actuals/overview",
            headers={"X-PM-Token": token},
            timeout=30  # Increased timeout for this endpoint
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected structure
            if isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Response is valid dict with keys: {list(data.keys())}"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response is not a dict: {type(data)}"
                )
        elif response.status_code == 404:
            results.add_fail(
                test_name,
                f"Status: 404 - Endpoint not found or no data for project {PROJECT_NUMBER}"
            )
        elif response.status_code == 500:
            results.add_fail(
                test_name,
                f"Status: 500 - Internal server error"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_actuals_candidates(results: TestResult, token: str):
    """Test GET /api/pm/project-controls/projects/{project_number}/schedule/actuals/candidates"""
    test_name = f"GET /api/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/actuals/candidates"
    try:
        response = requests.get(
            f"{BACKEND_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/actuals/candidates",
            headers={"X-PM-Token": token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected structure (should be a dict with count and items)
            if isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Response type: dict, Keys: {list(data.keys())}"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response is unexpected type: {type(data)}"
                )
        elif response.status_code == 404:
            results.add_fail(
                test_name,
                f"Status: 404 - Endpoint not found or no data for project {PROJECT_NUMBER}"
            )
        elif response.status_code == 500:
            results.add_fail(
                test_name,
                f"Status: 500 - Internal server error"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_daily_work_plan(results: TestResult, token: str):
    """Test GET /api/pm/project-controls/projects/{project_number}/schedule/daily-work-plan"""
    test_name = f"GET /api/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/daily-work-plan"
    try:
        response = requests.get(
            f"{BACKEND_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/daily-work-plan",
            headers={"X-PM-Token": token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected structure
            if isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Response is valid dict with keys: {list(data.keys())}"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response is not a dict: {type(data)}"
                )
        elif response.status_code == 404:
            results.add_fail(
                test_name,
                f"Status: 404 - Endpoint not found or no data for project {PROJECT_NUMBER}"
            )
        elif response.status_code == 500:
            results.add_fail(
                test_name,
                f"Status: 500 - Internal server error"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_schedule_export(results: TestResult, token: str, export_kind: str, version_id: str):
    """Test GET /api/pm/project-controls/projects/{project_number}/schedule/export"""
    test_name = f"GET /api/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/export (export_kind={export_kind})"
    
    if not version_id:
        results.add_fail(
            test_name,
            "Skipped - No valid schedule version_id available for export testing"
        )
        return
    
    try:
        params = {
            "export_kind": export_kind,
            "version_id": version_id
        }
        response = requests.get(
            f"{BACKEND_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/export",
            headers={"X-PM-Token": token},
            params=params,
            timeout=15
        )
        
        if response.status_code == 200:
            # Export endpoints return CSV text, not JSON
            content = response.text
            if content and len(content) > 0:
                # Check if it looks like CSV (has commas and newlines)
                if "," in content and "\n" in content:
                    results.add_pass(
                        test_name,
                        f"Status: {response.status_code}, CSV export received ({len(content)} bytes)"
                    )
                else:
                    results.add_fail(
                        test_name,
                        f"Status: {response.status_code}, but response doesn't look like CSV"
                    )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response is empty"
                )
        elif response.status_code == 404:
            results.add_fail(
                test_name,
                f"Status: 404 - Endpoint not found or no data for export"
            )
        elif response.status_code == 500:
            results.add_fail(
                test_name,
                f"Status: 500 - Internal server error"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def main():
    print("="*80)
    print("WP-18C5 Backend Verification - Schedule Actuals & Daily Work Plan")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Project Number: {PROJECT_NUMBER}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Step 1: Login as PM
    print("Step 1: Authenticating as PM...")
    print()
    token = get_pm_token()
    
    if not token:
        print("\n❌ CRITICAL: Failed to obtain PM authentication token")
        print("Cannot proceed with endpoint testing without authentication")
        return 1
    
    print()
    print("Step 2: Getting schedule version for export testing...")
    print()
    version_id = get_schedule_version_id(token)
    
    print()
    print("Step 3: Testing WP-18C5 endpoints...")
    print()
    
    # Test actuals overview endpoint
    test_actuals_overview(results, token)
    
    # Test actuals candidates endpoint
    test_actuals_candidates(results, token)
    
    # Test daily work plan endpoint
    test_daily_work_plan(results, token)
    
    print()
    print("Step 4: Testing schedule export endpoints...")
    print()
    
    # Test forecast schedule export
    test_schedule_export(results, token, "forecast_schedule_csv", version_id)
    
    # Test schedule actuals export
    test_schedule_export(results, token, "schedule_actuals_csv", version_id)
    
    # Test daily work plan export
    test_schedule_export(results, token, "daily_work_plan_csv", version_id)
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n✅ CONFIRMATION: WP-18C5 backend flow is HEALTHY")
        print("   All endpoints return successful payloads (200 status)")
        print("   No 404 or 500 errors detected")
        print("   PM scope works correctly for project ZZ-RUNTIME-CERT-2026")
    else:
        print("\n⚠️  FAILURES DETECTED: See failed tests above")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
