"""
TRACK 27.11C/27.11B Backend Closeout Verification
NARROW SCOPE: Only verify 3 specific endpoints with exact contract requirements.
Base URL: https://backup-forensics.preview.emergentagent.com
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Expected values for Track 27.11C/27.11B closeout
EXPECTED_BACKUP_FILENAME = "MASCI_complete_backup_2026-07-13_031902Z.zip"
EXPECTED_INTEGRITY_RESULT = "PASS"
EXPECTED_CLASSIFICATION = "PASS"
EXPECTED_CAPTURED_COUNT = 251
EXPECTED_EXPECTED_COUNT = 251
EXPECTED_MISSING_COUNT = 0

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

def authenticate():
    """Authenticate and get admin token"""
    print_section("AUTHENTICATION")
    
    url = f"{BASE_URL}/api/auth/multi-login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"POST {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get("portal_tokens", {}).get("admin")
            if admin_token:
                print_result("Authentication", True, f"Admin token obtained (length: {len(admin_token)})")
                return admin_token
            else:
                print_result("Authentication", False, "No admin token in response")
                print(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print_result("Authentication", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print_result("Authentication", False, f"Exception: {str(e)}")
        return None

def test_backups_integrity_check(admin_token):
    """Test /api/admin/backups/integrity-check endpoint with specific contract requirements"""
    print_section("TEST 1: /api/admin/backups/integrity-check")
    
    url = f"{BASE_URL}/api/admin/backups/integrity-check"
    headers = {"X-Admin-Token": admin_token}
    
    print(f"GET {url}")
    print(f"Expected backup filename: {EXPECTED_BACKUP_FILENAME}")
    print(f"Expected captured_collection_count: {EXPECTED_CAPTURED_COUNT}")
    print(f"Expected expected_collection_count: {EXPECTED_EXPECTED_COUNT}")
    print(f"Expected missing_count: {EXPECTED_MISSING_COUNT}")
    
    try:
        # Increase timeout for this endpoint as it performs heavy computation
        response = requests.get(url, headers=headers, timeout=60)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields based on actual API structure (all at top level)
            issues = []
            
            # Check for backup filename (at top level)
            filename = data.get("last_backup_filename", "")
            print(f"  last_backup_filename: {filename}")
            
            if filename != EXPECTED_BACKUP_FILENAME:
                issues.append(f"Filename mismatch: got '{filename}', expected '{EXPECTED_BACKUP_FILENAME}'")
            
            # Check integrity_result (at top level)
            integrity_result = data.get("integrity_result", "")
            print(f"  integrity_result: {integrity_result}")
            if integrity_result != EXPECTED_INTEGRITY_RESULT:
                issues.append(f"integrity_result mismatch: got '{integrity_result}', expected '{EXPECTED_INTEGRITY_RESULT}'")
            
            # Check classification (at top level)
            classification = data.get("classification", "")
            print(f"  classification: {classification}")
            if classification != EXPECTED_CLASSIFICATION:
                issues.append(f"classification mismatch: got '{classification}', expected '{EXPECTED_CLASSIFICATION}'")
            
            # Check captured_collection_count (at top level)
            captured_count = data.get("captured_collection_count", 0)
            print(f"  captured_collection_count: {captured_count}")
            if captured_count != EXPECTED_CAPTURED_COUNT:
                issues.append(f"captured_collection_count mismatch: got {captured_count}, expected {EXPECTED_CAPTURED_COUNT}")
            
            # Check expected_collection_count (at top level)
            expected_count = data.get("expected_collection_count", 0)
            print(f"  expected_collection_count: {expected_count}")
            if expected_count != EXPECTED_EXPECTED_COUNT:
                issues.append(f"expected_collection_count mismatch: got {expected_count}, expected {EXPECTED_EXPECTED_COUNT}")
            
            # Check missing_from_backup (at top level)
            missing_from_backup = data.get("missing_from_backup", [])
            missing_count = len(missing_from_backup)
            print(f"  missing_from_backup: {missing_from_backup}")
            print(f"  missing_count: {missing_count}")
            
            if missing_count != EXPECTED_MISSING_COUNT:
                issues.append(f"missing_count mismatch: got {missing_count}, expected {EXPECTED_MISSING_COUNT}")
            
            if issues:
                print_result("Backups Integrity Check", False, "; ".join(issues))
                return False, data
            else:
                print_result("Backups Integrity Check", True, "All contract requirements verified")
                return True, data
        else:
            print_result("Backups Integrity Check", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
    except requests.exceptions.Timeout:
        print_result("Backups Integrity Check", False, "Request timeout (60s)")
        return False, None
    except Exception as e:
        print_result("Backups Integrity Check", False, f"Exception: {str(e)}")
        return False, None

def test_backups_complete_r2_state(admin_token):
    """Test /api/admin/backups-complete-r2-state endpoint"""
    print_section("TEST 2: /api/admin/backups-complete-r2-state")
    
    url = f"{BASE_URL}/api/admin/backups-complete-r2-state"
    headers = {"X-Admin-Token": admin_token}
    
    print(f"GET {url}")
    print(f"Expected last.filename: {EXPECTED_BACKUP_FILENAME}")
    print(f"Expected last.outcome: ok (or equivalent success state)")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
            
            # Verify required fields
            issues = []
            
            # Check for last.filename
            last = data.get("last", {})
            filename = last.get("filename", "")
            
            if filename != EXPECTED_BACKUP_FILENAME:
                issues.append(f"last.filename mismatch: got '{filename}', expected '{EXPECTED_BACKUP_FILENAME}'")
            
            # Check for last.outcome (ok or equivalent success state)
            outcome = last.get("outcome", "")
            success_states = ["ok", "success", "completed", "pass"]
            if outcome.lower() not in success_states:
                issues.append(f"last.outcome not in success states: got '{outcome}', expected one of {success_states}")
            
            if issues:
                print_result("Backups Complete R2 State", False, "; ".join(issues))
                return False, data
            else:
                print_result("Backups Complete R2 State", True, f"last.filename={filename}, last.outcome={outcome}")
                return True, data
        else:
            print_result("Backups Complete R2 State", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
    except Exception as e:
        print_result("Backups Complete R2 State", False, f"Exception: {str(e)}")
        return False, None

def test_production_certification(admin_token):
    """Test /api/admin/production-certification endpoint with specific contract requirements"""
    print_section("TEST 3: /api/admin/production-certification")
    
    url = f"{BASE_URL}/api/admin/production-certification"
    headers = {"X-Admin-Token": admin_token}
    
    print(f"GET {url}")
    print(f"Expected fields: release_reason, release_source_hash, release_required_workflows")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse keys: {list(data.keys())}")
            print(f"Sample data: {json.dumps(data, indent=2)[:1000]}...")
            
            # Verify required fields
            issues = []
            required_fields = ["release_reason", "release_source_hash", "release_required_workflows"]
            
            for field in required_fields:
                if field not in data:
                    issues.append(f"Missing field: {field}")
                else:
                    value = data[field]
                    print(f"  {field}: {value if not isinstance(value, (list, dict)) else type(value).__name__}")
            
            if issues:
                print_result("Production Certification", False, "; ".join(issues))
                return False, data
            else:
                print_result("Production Certification", True, "All required fields present")
                return True, data
        else:
            print_result("Production Certification", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
    except Exception as e:
        print_result("Production Certification", False, f"Exception: {str(e)}")
        return False, None

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("  TRACK 27.11C/27.11B BACKEND CLOSEOUT VERIFICATION")
    print("  Base URL: " + BASE_URL)
    print("  Timestamp: " + datetime.utcnow().isoformat() + "Z")
    print("  Scope: NARROW - 3 endpoints only")
    print("="*80)
    
    results = {}
    
    # Step 1: Authenticate
    admin_token = authenticate()
    if not admin_token:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
        return False
    
    # Step 2: Test the 3 specific endpoints
    results["backups_integrity_check"] = test_backups_integrity_check(admin_token)
    results["backups_complete_r2_state"] = test_backups_complete_r2_state(admin_token)
    results["production_certification"] = test_production_certification(admin_token)
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    
    print("\nDetailed Results:")
    for endpoint, (success, _) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {endpoint}")
    
    print("\n" + "="*80)
    if passed == total:
        print("  ✅ ALL TESTS PASSED - Track 27.11C/27.11B closeout verified")
    else:
        print(f"  ❌ {total - passed} TEST(S) FAILED - Track 27.11C/27.11B closeout incomplete")
    print("="*80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
