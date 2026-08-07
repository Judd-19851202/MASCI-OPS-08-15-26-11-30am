"""
WP-18C7 Forecasting & Commitments Backend Validation
=====================================================
Backend-only verification for WP-18C7 Forecasting & Commitments after implementation.

Test Coverage:
1. PM login via /api/pm/login
2. PM forecasting workspace GET
3. PM commitment create
4. PM commitment update
5. PM snapshot capture
6. Admin multi-login
7. Admin forecasting workspace GET
8. FL login
9. FL forecasting GET

Credentials from /app/memory/test_credentials.md:
- PM: pm.scope.forensic@example.com / ForensicPm2026!
- Admin: jaymn.judd@mascigc.com / Maddix123!
- FL: cert.foreman@example.com / CertProof2026!
- Projects: ZZ-FOR-ASSIGN-01, ZZ-RUNTIME-CERT-2026
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials
PM_EMAIL = "pm.scope.forensic@example.com"
PM_PASSWORD = "ForensicPm2026!"
PM_PROJECT = "ZZ-FOR-ASSIGN-01"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
ADMIN_PROJECT = "ZZ-RUNTIME-CERT-2026"

FL_EMAIL = "cert.foreman@example.com"
FL_PASSWORD = "CertProof2026!"
FL_PROJECT = "ZZ-RUNTIME-CERT-2026"

# Test results
results = {
    "timestamp": datetime.utcnow().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def log_test(test_name, status, details="", response_data=None):
    """Log test result"""
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "response_data": response_data
    }
    results["tests"].append(result)
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ {test_name}: {status}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ {test_name}: {status}")
    if details:
        print(f"   {details}")
    print()

def test_pm_login():
    """Test 1: PM login via /api/pm/login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                log_test(
                    "Test 1: PM Login",
                    "PASS",
                    f"PM logged in successfully. Token received.",
                    {"status_code": 200, "has_token": True}
                )
                return token
            else:
                log_test(
                    "Test 1: PM Login",
                    "FAIL",
                    "No token in response",
                    {"status_code": 200, "response": data}
                )
                return None
        else:
            log_test(
                "Test 1: PM Login",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return None
    except Exception as e:
        log_test("Test 1: PM Login", "FAIL", f"Exception: {str(e)}")
        return None

def test_pm_forecasting_workspace(pm_token):
    """Test 2: PM forecasting workspace GET"""
    if not pm_token:
        log_test("Test 2: PM Forecasting Workspace GET", "SKIP", "No PM token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            required_fields = ["audience", "authority_boundaries", "schedule", "production", "commitments", "confidence", "versioning"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_test(
                    "Test 2: PM Forecasting Workspace GET",
                    "PASS",
                    f"Workspace loaded successfully. Audience: {data.get('audience')}, Schedule status: {data.get('schedule', {}).get('status')}",
                    {"status_code": 200, "audience": data.get("audience"), "has_all_fields": True}
                )
                return True
            else:
                log_test(
                    "Test 2: PM Forecasting Workspace GET",
                    "FAIL",
                    f"Missing required fields: {missing_fields}",
                    {"status_code": 200, "missing_fields": missing_fields}
                )
                return False
        else:
            log_test(
                "Test 2: PM Forecasting Workspace GET",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return False
    except Exception as e:
        log_test("Test 2: PM Forecasting Workspace GET", "FAIL", f"Exception: {str(e)}")
        return False

def test_pm_commitment_create(pm_token):
    """Test 3: PM commitment create"""
    if not pm_token:
        log_test("Test 3: PM Commitment Create", "SKIP", "No PM token available")
        return None
    
    try:
        payload = {
            "family": "milestone_quantity",
            "status": "proposed",
            "title": "TEST_WP18C7_Commitment_Create",
            "description": "Test commitment created by WP-18C7 testing agent",
            "due_date": "2026-12-31",
            "linked_unit": "LF",
            "target_quantity": 100.0,
            "confidence": "medium",
            "evidence_note": "Testing WP-18C7 commitment creation",
            "note": "Initial creation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/commitments",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "commitment" in data:
                commitment = data["commitment"]
                commitment_id = commitment.get("commitment_id")
                log_test(
                    "Test 3: PM Commitment Create",
                    "PASS",
                    f"Commitment created successfully. ID: {commitment_id}, Status: {commitment.get('status')}",
                    {"status_code": 200, "commitment_id": commitment_id}
                )
                return commitment_id
            else:
                log_test(
                    "Test 3: PM Commitment Create",
                    "FAIL",
                    "Response missing 'ok' or 'commitment' field",
                    {"status_code": 200, "response": data}
                )
                return None
        else:
            log_test(
                "Test 3: PM Commitment Create",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return None
    except Exception as e:
        log_test("Test 3: PM Commitment Create", "FAIL", f"Exception: {str(e)}")
        return None

def test_pm_commitment_update(pm_token, commitment_id):
    """Test 4: PM commitment update"""
    if not pm_token:
        log_test("Test 4: PM Commitment Update", "SKIP", "No PM token available")
        return False
    
    if not commitment_id:
        log_test("Test 4: PM Commitment Update", "SKIP", "No commitment ID available")
        return False
    
    try:
        payload = {
            "family": "milestone_quantity",
            "status": "committed",
            "title": "TEST_WP18C7_Commitment_Create",
            "description": "Test commitment updated by WP-18C7 testing agent",
            "due_date": "2026-12-31",
            "linked_unit": "LF",
            "target_quantity": 100.0,
            "confidence": "high",
            "evidence_note": "Testing WP-18C7 commitment update",
            "note": "Status updated to committed"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/commitments/{commitment_id}",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "commitment" in data:
                commitment = data["commitment"]
                log_test(
                    "Test 4: PM Commitment Update",
                    "PASS",
                    f"Commitment updated successfully. Status: {commitment.get('status')}, Confidence: {commitment.get('confidence')}",
                    {"status_code": 200, "status": commitment.get("status")}
                )
                return True
            else:
                log_test(
                    "Test 4: PM Commitment Update",
                    "FAIL",
                    "Response missing 'ok' or 'commitment' field",
                    {"status_code": 200, "response": data}
                )
                return False
        else:
            log_test(
                "Test 4: PM Commitment Update",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return False
    except Exception as e:
        log_test("Test 4: PM Commitment Update", "FAIL", f"Exception: {str(e)}")
        return False

def test_pm_snapshot_capture(pm_token):
    """Test 5: PM snapshot capture"""
    if not pm_token:
        log_test("Test 5: PM Snapshot Capture", "SKIP", "No PM token available")
        return False
    
    try:
        payload = {"note": "TEST_WP18C7_Snapshot_Capture"}
        
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/snapshots",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "versioning" in data:
                versioning = data["versioning"]
                log_test(
                    "Test 5: PM Snapshot Capture",
                    "PASS",
                    f"Snapshot captured successfully. Version: {versioning.get('version_number')}, Persisted: {versioning.get('persisted')}",
                    {"status_code": 200, "version_number": versioning.get("version_number")}
                )
                return True
            else:
                log_test(
                    "Test 5: PM Snapshot Capture",
                    "FAIL",
                    "Response missing 'versioning' field",
                    {"status_code": 200, "response": data}
                )
                return False
        else:
            log_test(
                "Test 5: PM Snapshot Capture",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return False
    except Exception as e:
        log_test("Test 5: PM Snapshot Capture", "FAIL", f"Exception: {str(e)}")
        return False

def test_admin_multi_login():
    """Test 6: Admin multi-login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # New multi-login response structure
            session_token = data.get("session_token")
            portal_tokens = data.get("portal_tokens", {})
            admin_token = portal_tokens.get("admin")
            
            if session_token and admin_token:
                log_test(
                    "Test 6: Admin Multi-Login",
                    "PASS",
                    "Admin logged in successfully via multi-login. Tokens received.",
                    {"status_code": 200, "has_tokens": True}
                )
                return {"directory_token": session_token, "admin_token": admin_token}
            else:
                log_test(
                    "Test 6: Admin Multi-Login",
                    "FAIL",
                    "Missing tokens in response",
                    {"status_code": 200, "response": data}
                )
                return None
        else:
            log_test(
                "Test 6: Admin Multi-Login",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return None
    except Exception as e:
        log_test("Test 6: Admin Multi-Login", "FAIL", f"Exception: {str(e)}")
        return None

def test_admin_forecasting_workspace(admin_tokens):
    """Test 7: Admin forecasting workspace GET"""
    if not admin_tokens:
        log_test("Test 7: Admin Forecasting Workspace GET", "SKIP", "No admin tokens available")
        return False
    
    try:
        headers = {
            "X-Admin-Token": admin_tokens.get("admin_token", ""),
            "X-Directory-Token": admin_tokens.get("directory_token", "")
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{ADMIN_PROJECT}/forecasting/workspace",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            required_fields = ["audience", "authority_boundaries", "schedule", "production", "commitments", "confidence", "versioning"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_test(
                    "Test 7: Admin Forecasting Workspace GET",
                    "PASS",
                    f"Workspace loaded successfully. Audience: {data.get('audience')}, Schedule status: {data.get('schedule', {}).get('status')}",
                    {"status_code": 200, "audience": data.get("audience"), "has_all_fields": True}
                )
                return True
            else:
                log_test(
                    "Test 7: Admin Forecasting Workspace GET",
                    "FAIL",
                    f"Missing required fields: {missing_fields}",
                    {"status_code": 200, "missing_fields": missing_fields}
                )
                return False
        else:
            log_test(
                "Test 7: Admin Forecasting Workspace GET",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return False
    except Exception as e:
        log_test("Test 7: Admin Forecasting Workspace GET", "FAIL", f"Exception: {str(e)}")
        return False

def test_fl_login():
    """Test 8: FL login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json={"email": FL_EMAIL, "password": FL_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                log_test(
                    "Test 8: FL Login",
                    "PASS",
                    "FL logged in successfully. Token received.",
                    {"status_code": 200, "has_token": True}
                )
                return token
            else:
                log_test(
                    "Test 8: FL Login",
                    "FAIL",
                    "No token in response",
                    {"status_code": 200, "response": data}
                )
                return None
        else:
            log_test(
                "Test 8: FL Login",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return None
    except Exception as e:
        log_test("Test 8: FL Login", "FAIL", f"Exception: {str(e)}")
        return None

def test_fl_forecasting(fl_token):
    """Test 9: FL forecasting GET"""
    if not fl_token:
        log_test("Test 9: FL Forecasting GET", "SKIP", "No FL token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/portal/projects/{FL_PROJECT}/forecasting",
            headers={"X-FL-Token": fl_token},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            if data.get("ok") and "workspace" in data:
                workspace = data["workspace"]
                required_fields = ["field_summary", "production", "commitments", "schedule", "drivers", "constraints", "confidence"]
                missing_fields = [f for f in required_fields if f not in workspace]
                
                if not missing_fields:
                    log_test(
                        "Test 9: FL Forecasting GET",
                        "PASS",
                        f"FL workspace loaded successfully. Project: {data.get('project_number')}, Has field_summary: {bool(workspace.get('field_summary'))}",
                        {"status_code": 200, "project_number": data.get("project_number"), "has_all_fields": True}
                    )
                    return True
                else:
                    log_test(
                        "Test 9: FL Forecasting GET",
                        "FAIL",
                        f"Missing required fields in workspace: {missing_fields}",
                        {"status_code": 200, "missing_fields": missing_fields}
                    )
                    return False
            else:
                log_test(
                    "Test 9: FL Forecasting GET",
                    "FAIL",
                    "Response missing 'ok' or 'workspace' field",
                    {"status_code": 200, "response": data}
                )
                return False
        else:
            log_test(
                "Test 9: FL Forecasting GET",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                {"status_code": response.status_code}
            )
            return False
    except Exception as e:
        log_test("Test 9: FL Forecasting GET", "FAIL", f"Exception: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 80)
    print("WP-18C7 Forecasting & Commitments Backend Validation")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    print()
    
    # PM Flow Tests
    print("PM FLOW TESTS")
    print("-" * 80)
    pm_token = test_pm_login()
    test_pm_forecasting_workspace(pm_token)
    commitment_id = test_pm_commitment_create(pm_token)
    test_pm_commitment_update(pm_token, commitment_id)
    test_pm_snapshot_capture(pm_token)
    print()
    
    # Admin Flow Tests
    print("ADMIN FLOW TESTS")
    print("-" * 80)
    admin_tokens = test_admin_multi_login()
    test_admin_forecasting_workspace(admin_tokens)
    print()
    
    # FL Flow Tests
    print("FL FLOW TESTS")
    print("-" * 80)
    fl_token = test_fl_login()
    test_fl_forecasting(fl_token)
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
    print("=" * 80)
    
    # Save results to file
    with open("/app/wp18c7_backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: /app/wp18c7_backend_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
