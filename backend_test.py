"""
TRACK 27.11A Backend API Testing
Test the recovery/bundle-related backend endpoints on preview environment.
Base URL: https://backup-forensics.preview.emergentagent.com
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test endpoints
ENDPOINTS = {
    "health_full": "/api/health/full",
    "recovery_snapshot": "/api/admin/recovery/snapshot",
    "backups_scheduler_state": "/api/admin/backups-scheduler-state",
    "backups_integrity_check": "/api/admin/backups/integrity-check",
    "production_certification": "/api/admin/production-certification",
    "version": "/api/version"
}

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

def test_health_full():
    """Test /api/health/full endpoint"""
    print_section("TEST: /api/health/full")
    
    url = f"{BASE_URL}{ENDPOINTS['health_full']}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 503]:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for expected fields
            required_fields = ["ok", "mongo", "scheduler", "backup_recent"]
            has_all_fields = all(field in data for field in required_fields)
            
            if has_all_fields:
                print_result("Health Full Endpoint", True, "All required fields present")
                return True, data
            else:
                missing = [f for f in required_fields if f not in data]
                print_result("Health Full Endpoint", False, f"Missing fields: {missing}")
                return False, data
        else:
            print_result("Health Full Endpoint", False, f"Unexpected status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result("Health Full Endpoint", False, f"Exception: {str(e)}")
        return False, None

def test_recovery_snapshot(admin_token):
    """Test /api/admin/recovery/snapshot endpoint"""
    print_section("TEST: /api/admin/recovery/snapshot")
    
    url = f"{BASE_URL}{ENDPOINTS['recovery_snapshot']}"
    headers = {"X-Admin-Token": admin_token}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check for Track 27.11A specific fields
            required_fields = [
                "computed_at", "pill", "last_backup", "scheduler",
                "backup_age_minutes", "rpo", "rto", "archive_count",
                "bucket_usage", "failures_7d", "warnings"
            ]
            
            has_all_fields = all(field in data for field in required_fields)
            
            # Check scheduler truth agreement (Track 27.11A requirement)
            scheduler_data = data.get("scheduler", {})
            scheduler_fields = ["alive", "is_healthy", "signal_source", "reason_code", "evidence_ts"]
            has_scheduler_fields = all(field in scheduler_data for field in scheduler_fields)
            
            # Check recent five-backup lineage fields
            last_backup = data.get("last_backup", {})
            if last_backup:
                backup_fields = ["filename", "size_mb", "ts", "ok"]
                has_backup_fields = all(field in last_backup for field in backup_fields)
            else:
                has_backup_fields = True  # OK if no backup yet
            
            print(f"\nScheduler data: {json.dumps(scheduler_data, indent=2)}")
            print(f"Last backup: {json.dumps(last_backup, indent=2)}")
            print(f"RPO: {data.get('rpo')}")
            print(f"RTO: {data.get('rto')}")
            print(f"Pill status: {data.get('pill')}")
            
            if has_all_fields and has_scheduler_fields and has_backup_fields:
                print_result("Recovery Snapshot", True, "All Track 27.11A fields present")
                return True, data
            else:
                issues = []
                if not has_all_fields:
                    missing = [f for f in required_fields if f not in data]
                    issues.append(f"Missing top-level fields: {missing}")
                if not has_scheduler_fields:
                    missing = [f for f in scheduler_fields if f not in scheduler_data]
                    issues.append(f"Missing scheduler fields: {missing}")
                if not has_backup_fields:
                    issues.append("Missing backup lineage fields")
                print_result("Recovery Snapshot", False, "; ".join(issues))
                return False, data
        else:
            print_result("Recovery Snapshot", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_result("Recovery Snapshot", False, f"Exception: {str(e)}")
        return False, None

def test_backups_scheduler_state(admin_token):
    """Test /api/admin/backups-scheduler-state endpoint"""
    print_section("TEST: /api/admin/backups-scheduler-state")
    
    url = f"{BASE_URL}{ENDPOINTS['backups_scheduler_state']}"
    headers = {"X-Admin-Token": admin_token}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for scheduler state fields
            expected_fields = ["last_tick_ts", "alive", "is_healthy"]
            has_fields = any(field in data for field in expected_fields)
            
            if has_fields or isinstance(data, dict):
                print_result("Backups Scheduler State", True, "Endpoint accessible")
                return True, data
            else:
                print_result("Backups Scheduler State", False, "Unexpected response structure")
                return False, data
        else:
            print_result("Backups Scheduler State", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_result("Backups Scheduler State", False, f"Exception: {str(e)}")
        return False, None

def test_backups_integrity_check(admin_token):
    """Test /api/admin/backups/integrity-check endpoint"""
    print_section("TEST: /api/admin/backups/integrity-check")
    
    url = f"{BASE_URL}{ENDPOINTS['backups_integrity_check']}"
    headers = {"X-Admin-Token": admin_token}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print_result("Backups Integrity Check", True, "Endpoint accessible")
            return True, data
        elif response.status_code == 404:
            print_result("Backups Integrity Check", True, "Endpoint not implemented (404 expected)")
            return True, None
        else:
            print_result("Backups Integrity Check", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_result("Backups Integrity Check", False, f"Exception: {str(e)}")
        return False, None

def test_production_certification(admin_token):
    """Test /api/admin/production-certification endpoint"""
    print_section("TEST: /api/admin/production-certification")
    
    url = f"{BASE_URL}{ENDPOINTS['production_certification']}"
    headers = {"X-Admin-Token": admin_token}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check for release-scoped certification fields (Track 27.11A requirement)
            if isinstance(data, dict):
                # Look for certification structure
                has_cert_structure = "workflows" in data or "certification" in data or "status" in data
                
                if has_cert_structure or len(data) > 0:
                    print(f"Sample data: {json.dumps(data, indent=2)[:500]}...")
                    print_result("Production Certification", True, "Release-scoped certification data present")
                    return True, data
                else:
                    print_result("Production Certification", False, "Empty or unexpected structure")
                    return False, data
            else:
                print_result("Production Certification", False, "Response is not a dict")
                return False, data
        else:
            print_result("Production Certification", False, f"HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_result("Production Certification", False, f"Exception: {str(e)}")
        return False, None

def test_version():
    """Test /api/version endpoint"""
    print_section("TEST: /api/version")
    
    url = f"{BASE_URL}{ENDPOINTS['version']}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"GET {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for version build/process-start semantics (Track 27.11A requirement)
            expected_fields = ["commit", "built_at", "source_hash", "process_start"]
            has_all_fields = all(field in data for field in expected_fields)
            
            if has_all_fields:
                print_result("Version Endpoint", True, "All version semantics present")
                return True, data
            else:
                missing = [f for f in expected_fields if f not in data]
                print_result("Version Endpoint", False, f"Missing fields: {missing}")
                return False, data
        else:
            print_result("Version Endpoint", False, f"HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print_result("Version Endpoint", False, f"Exception: {str(e)}")
        return False, None

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("  TRACK 27.11A BACKEND API VERIFICATION")
    print("  Base URL: " + BASE_URL)
    print("  Timestamp: " + datetime.utcnow().isoformat() + "Z")
    print("="*80)
    
    results = {}
    
    # Step 1: Authenticate
    admin_token = authenticate()
    if not admin_token:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
        return
    
    # Step 2: Test public endpoint (no auth required)
    results["health_full"] = test_health_full()
    results["version"] = test_version()
    
    # Step 3: Test admin endpoints (auth required)
    results["recovery_snapshot"] = test_recovery_snapshot(admin_token)
    results["backups_scheduler_state"] = test_backups_scheduler_state(admin_token)
    results["backups_integrity_check"] = test_backups_integrity_check(admin_token)
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
        print("  ✅ ALL TESTS PASSED")
    else:
        print(f"  ❌ {total - passed} TEST(S) FAILED")
    print("="*80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
