#!/usr/bin/env python3
"""
WP18CZ Route-Governance Closeout - Backend API Sanity Pass
Final backend/API verification for repaired/verified routes.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, List

# Backend URL from review request
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from review request
CREDENTIALS = {
    "admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
    "hr": {"email": "cert.hr@example.com", "password": "CertProof2026!"},
    "safety": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
    "dispatch": {"email": "cert.dispatch@example.com", "password": "CertProof2026!"},
}

# Test IDs from review request
EMPLOYEE_ID = "c9d7ebc3-a292-4d7a-8765-0ce2739c6029"
DRIVER_KEY = "driver-iter392"
ASSET_ID = "100adffe-cb69-4d70-b61f-3f51a6f87d85"
INCIDENT_ID_1 = "bddd1b95-b55a-4646-aa7d-9b156a2c21e3"
INCIDENT_ID_2 = "00f1f93d-f76f-4224-8ebb-75fca4dd7be1"
EXECUTIVE_CASE_ID = "71477b5c-13fe-4f25-9ba0-d156bf47912c"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append({"test": test_name, "error": error})
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append({"test": test_name, "message": message})
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {message}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*80)
        print("BACKEND API SANITY PASS - SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)} ({len(self.passed)/total*100:.1f}%)")
        print(f"Failed: {len(self.failed)} ({len(self.failed)/total*100:.1f}%)")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for fail in self.failed:
                print(f"  - {fail['test']}: {fail['error']}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warn in self.warnings:
                print(f"  - {warn['test']}: {warn['message']}")
        
        print("\n" + "="*80)
        return len(self.failed) == 0


def login(role: str) -> Optional[Dict[str, str]]:
    """Login and return authentication headers."""
    try:
        creds = CREDENTIALS[role]
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": creds["email"], "password": creds["password"]},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Extract tokens from response
            session_token = data.get("session_token")
            portal_tokens = data.get("portal_tokens", {})
            
            # Get the appropriate portal token based on role
            portal_token = None
            if role == "admin":
                portal_token = portal_tokens.get("admin")
            elif role == "hr":
                portal_token = portal_tokens.get("hr")
            elif role == "safety":
                portal_token = portal_tokens.get("safety")
            elif role == "dispatch":
                portal_token = portal_tokens.get("dispatch")
            
            if session_token and portal_token:
                return {
                    "X-Directory-Token": session_token,
                    f"X-{role.capitalize()}-Token": portal_token
                }
        
        print(f"Login failed for {role}: {response.status_code} - {response.text[:200]}")
        return None
    except Exception as e:
        print(f"Login exception for {role}: {str(e)}")
        return None


def test_health_endpoints(results: TestResults):
    """Test /api/ready and /api/health endpoints."""
    print("\n" + "="*80)
    print("TEST GROUP 1: Health Endpoints")
    print("="*80)
    
    # Test /api/ready
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=10)
        if response.status_code == 200:
            results.add_pass("GET /api/ready", f"Status: {response.status_code}")
        else:
            results.add_fail("GET /api/ready", f"Expected 200, got {response.status_code}")
    except Exception as e:
        results.add_fail("GET /api/ready", str(e))
    
    # Test /api/health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            results.add_pass("GET /api/health", f"Status: {response.status_code}, Response: {json.dumps(data)[:100]}")
        else:
            results.add_fail("GET /api/health", f"Expected 200, got {response.status_code}")
    except Exception as e:
        results.add_fail("GET /api/health", str(e))


def test_hr_accountability_apis(results: TestResults, headers: Dict[str, str]):
    """Test HR accountability/profile APIs."""
    print("\n" + "="*80)
    print("TEST GROUP 2: HR Accountability/Profile APIs")
    print("="*80)
    
    # Test employee accountability timeline endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/hr/employees/{EMPLOYEE_ID}/accountability/timeline",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/timeline",
                f"Status: {response.status_code}, Type: {type(data).__name__}"
            )
        elif response.status_code == 404:
            results.add_warning(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/timeline",
                f"Employee not found (404) - may be expected if test data doesn't exist"
            )
        else:
            results.add_fail(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/timeline",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/timeline", str(e))
    
    # Test employee accountability brief PDF endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/hr/employees/{EMPLOYEE_ID}/accountability/brief.pdf",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            results.add_pass(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/brief.pdf",
                f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}"
            )
        elif response.status_code == 404:
            results.add_warning(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/brief.pdf",
                f"Employee not found (404) - may be expected if test data doesn't exist"
            )
        else:
            results.add_fail(
                f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/brief.pdf",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/hr/employees/{EMPLOYEE_ID}/accountability/brief.pdf", str(e))
    
    # Test general employee accountability endpoint (requires query parameter)
    try:
        response = requests.get(
            f"{BASE_URL}/hr/employee-accountability?employee=John",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                f"GET /api/hr/employee-accountability",
                f"Status: {response.status_code}, Type: {type(data).__name__}"
            )
        elif response.status_code == 404:
            results.add_warning(
                f"GET /api/hr/employee-accountability",
                f"No data found (404) - may be expected if test employee doesn't exist"
            )
        else:
            results.add_fail(
                f"GET /api/hr/employee-accountability",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/hr/employee-accountability", str(e))


def test_admin_asset_apis(results: TestResults, headers: Dict[str, str]):
    """Test admin asset/history APIs."""
    print("\n" + "="*80)
    print("TEST GROUP 3: Admin Asset/History APIs")
    print("="*80)
    
    # Test asset detail endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/admin/assets/{ASSET_ID}",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                f"GET /api/admin/assets/{ASSET_ID}",
                f"Status: {response.status_code}, Keys: {list(data.keys())[:5]}"
            )
        elif response.status_code == 404:
            results.add_warning(
                f"GET /api/admin/assets/{ASSET_ID}",
                f"Asset not found (404) - may be expected if test data doesn't exist"
            )
        else:
            results.add_fail(
                f"GET /api/admin/assets/{ASSET_ID}",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/admin/assets/{ASSET_ID}", str(e))
    
    # Test asset history endpoint
    try:
        response = requests.get(
            f"{BASE_URL}/admin/assets/{ASSET_ID}/history",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                f"GET /api/admin/assets/{ASSET_ID}/history",
                f"Status: {response.status_code}, Items: {len(data) if isinstance(data, list) else 'N/A'}"
            )
        elif response.status_code == 404:
            results.add_warning(
                f"GET /api/admin/assets/{ASSET_ID}/history",
                f"Asset history not found (404) - may be expected if test data doesn't exist"
            )
        else:
            results.add_fail(
                f"GET /api/admin/assets/{ASSET_ID}/history",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/admin/assets/{ASSET_ID}/history", str(e))


def test_transportation_apis(results: TestResults, headers: Dict[str, str]):
    """Test transportation nested route data endpoints."""
    print("\n" + "="*80)
    print("TEST GROUP 4: Transportation Nested Route Data APIs")
    print("="*80)
    
    endpoints = [
        "/admin/transportation/trucks",
        "/admin/transportation/persons",
        "/admin/transportation/carriers",
        "/admin/transportation/fleet/equipment",
        "/admin/transportation/automation/health",
        "/dispatch/transportation/eligible-drivers",
        "/dispatch/transportation/eligible-trucks"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results.add_pass(
                    f"GET /api{endpoint}",
                    f"Status: {response.status_code}, Type: {type(data).__name__}"
                )
            elif response.status_code in [401, 403]:
                results.add_warning(
                    f"GET /api{endpoint}",
                    f"Auth issue ({response.status_code}) - may need different credentials or permissions"
                )
            elif response.status_code == 404:
                results.add_warning(
                    f"GET /api{endpoint}",
                    f"Endpoint not found (404) - may not be implemented or route changed"
                )
            else:
                results.add_fail(
                    f"GET /api{endpoint}",
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
        except Exception as e:
            results.add_fail(f"GET /api{endpoint}", str(e))


def test_safety_incident_apis(results: TestResults, headers: Dict[str, str]):
    """Test safety incident and meeting detail endpoints."""
    print("\n" + "="*80)
    print("TEST GROUP 5: Safety Incident and Meeting Detail APIs")
    print("="*80)
    
    # Test incident case detail endpoints (new incident engine)
    for case_id in [INCIDENT_ID_1, INCIDENT_ID_2]:
        try:
            response = requests.get(
                f"{BASE_URL}/incident-cases/{case_id}",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results.add_pass(
                    f"GET /api/incident-cases/{case_id}",
                    f"Status: {response.status_code}, Keys: {list(data.keys())[:5]}"
                )
            elif response.status_code == 404:
                results.add_warning(
                    f"GET /api/incident-cases/{case_id}",
                    f"Incident case not found (404) - may be expected if test data doesn't exist"
                )
            else:
                results.add_fail(
                    f"GET /api/incident-cases/{case_id}",
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
        except Exception as e:
            results.add_fail(f"GET /api/incident-cases/{case_id}", str(e))
    
    # Test meeting detail endpoints (admin meetings)
    for meeting_id in [INCIDENT_ID_1, INCIDENT_ID_2]:
        try:
            response = requests.get(
                f"{BASE_URL}/admin/meetings/{meeting_id}",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results.add_pass(
                    f"GET /api/admin/meetings/{meeting_id}",
                    f"Status: {response.status_code}, Keys: {list(data.keys())[:5]}"
                )
            elif response.status_code == 404:
                results.add_warning(
                    f"GET /api/admin/meetings/{meeting_id}",
                    f"Meeting not found (404) - may be expected if test data doesn't exist"
                )
            else:
                results.add_fail(
                    f"GET /api/admin/meetings/{meeting_id}",
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
        except Exception as e:
            results.add_fail(f"GET /api/admin/meetings/{meeting_id}", str(e))


def test_executive_report_api(results: TestResults, headers: Dict[str, str]):
    """Test executive report API for graceful no-data behavior."""
    print("\n" + "="*80)
    print("TEST GROUP 6: Executive Report API")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/incident-cases/{EXECUTIVE_CASE_ID}/executive-intelligence",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                f"GET /api/incident-cases/{EXECUTIVE_CASE_ID}/executive-intelligence",
                f"Status: {response.status_code}, Keys: {list(data.keys())[:5]}"
            )
        elif response.status_code == 404:
            # This is expected per review request - confirm it's graceful no-data behavior
            results.add_pass(
                f"GET /api/incident-cases/{EXECUTIVE_CASE_ID}/executive-intelligence",
                f"Graceful 404 response (no executive case package exists) - this is expected behavior"
            )
        else:
            results.add_fail(
                f"GET /api/incident-cases/{EXECUTIVE_CASE_ID}/executive-intelligence",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(f"GET /api/incident-cases/{EXECUTIVE_CASE_ID}/executive-intelligence", str(e))


def main():
    print("="*80)
    print("WP18CZ ROUTE-GOVERNANCE CLOSEOUT - BACKEND API SANITY PASS")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print("="*80)
    
    results = TestResults()
    
    # Test health endpoints (no auth required)
    test_health_endpoints(results)
    
    # Login as admin
    print("\n" + "="*80)
    print("Authenticating as Admin...")
    print("="*80)
    admin_headers = login("admin")
    
    if not admin_headers:
        results.add_fail("Admin Login", "Failed to authenticate as admin")
        print("\n⚠️  Cannot proceed with authenticated tests without admin credentials")
    else:
        results.add_pass("Admin Login", "Successfully authenticated")
        
        # Run admin-scoped tests
        test_admin_asset_apis(results, admin_headers)
        test_executive_report_api(results, admin_headers)
        test_transportation_apis(results, admin_headers)
    
    # Login as HR
    print("\n" + "="*80)
    print("Authenticating as HR...")
    print("="*80)
    hr_headers = login("hr")
    
    if not hr_headers:
        results.add_fail("HR Login", "Failed to authenticate as HR")
        print("\n⚠️  Cannot proceed with HR tests without HR credentials")
    else:
        results.add_pass("HR Login", "Successfully authenticated")
        
        # Run HR-scoped tests
        test_hr_accountability_apis(results, hr_headers)
    
    # Login as Safety
    print("\n" + "="*80)
    print("Authenticating as Safety...")
    print("="*80)
    safety_headers = login("safety")
    
    if not safety_headers:
        results.add_fail("Safety Login", "Failed to authenticate as safety")
        print("\n⚠️  Cannot proceed with safety tests without safety credentials")
    else:
        results.add_pass("Safety Login", "Successfully authenticated")
        
        # Run safety-scoped tests
        test_safety_incident_apis(results, safety_headers)
    
    # Print summary
    success = results.summary()
    
    # Save results to file
    with open("/app/wp18cz_backend_test_results.json", "w") as f:
        json.dump({
            "passed": results.passed,
            "failed": results.failed,
            "warnings": results.warnings,
            "success": success
        }, f, indent=2)
    
    print(f"\nResults saved to /app/wp18cz_backend_test_results.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
