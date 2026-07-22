#!/usr/bin/env python3
"""
Daily Report Reliability Incident Fix - Final Backend Verification
Tests endpoints on http://localhost:8001 per review request
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8001"

def test_ready_endpoint() -> Dict[str, Any]:
    """Test 1: GET /api/ready -> should return 200 with ok=true and state=ready"""
    print("\n[TEST 1] GET /api/ready")
    try:
        response = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("ok") is True and
            data.get("state") == "ready"
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
        
        return {
            "test": "ready_endpoint",
            "passed": passed,
            "status_code": response.status_code,
            "response": data
        }
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return {"test": "ready_endpoint", "passed": False, "error": str(e)}


def test_health_full_endpoint() -> Dict[str, Any]:
    """Test 2: GET /api/health/full -> should return 200 with ok=true, mongo=true, scheduler=true"""
    print("\n[TEST 2] GET /api/health/full")
    try:
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("ok") is True and
            data.get("mongo") is True and
            data.get("scheduler") is True
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
        
        return {
            "test": "health_full_endpoint",
            "passed": passed,
            "status_code": response.status_code,
            "response": data
        }
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return {"test": "health_full_endpoint", "passed": False, "error": str(e)}


def test_version_endpoint() -> Dict[str, Any]:
    """Test 3: GET /api/version -> should return commit 8f97a9fc49fdc0f8e0066195388654e2e445e397"""
    print("\n[TEST 3] GET /api/version")
    expected_commit = "8f97a9fc49fdc0f8e0066195388654e2e445e397"
    
    try:
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()
        
        actual_commit = data.get("commit", "")
        passed = (
            response.status_code == 200 and
            actual_commit == expected_commit
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Expected commit: {expected_commit}")
        print(f"  Actual commit: {actual_commit}")
        print(f"  Match: {actual_commit == expected_commit}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
        
        return {
            "test": "version_endpoint",
            "passed": passed,
            "status_code": response.status_code,
            "expected_commit": expected_commit,
            "actual_commit": actual_commit,
            "response": data
        }
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return {"test": "version_endpoint", "passed": False, "error": str(e)}


def test_public_endpoints() -> Dict[str, Any]:
    """Test 4: Public Daily Report support endpoints should return 200 without auth"""
    print("\n[TEST 4] Public Daily Report Support Endpoints (no auth required)")
    
    endpoints = [
        "/api/hr/employee-roster/public",
        "/api/jobs",
        "/api/field-leadership-roster",
        "/api/equipment-master"
    ]
    
    results = []
    all_passed = True
    
    for endpoint in endpoints:
        print(f"\n  Testing: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            
            passed = response.status_code == 200
            all_passed = all_passed and passed
            
            print(f"    Status: {response.status_code}")
            if isinstance(data, dict) or isinstance(data, list):
                print(f"    Response type: {type(data).__name__}")
                if isinstance(data, list):
                    print(f"    Response length: {len(data)} items")
                else:
                    print(f"    Response keys: {list(data.keys())}")
            print(f"    Result: {'✅ PASS' if passed else '❌ FAIL'}")
            
            results.append({
                "endpoint": endpoint,
                "passed": passed,
                "status_code": response.status_code,
                "response_type": type(data).__name__
            })
        except Exception as e:
            print(f"    ❌ FAIL - Exception: {e}")
            all_passed = False
            results.append({
                "endpoint": endpoint,
                "passed": False,
                "error": str(e)
            })
    
    print(f"\n  Overall Result: {'✅ ALL PASS' if all_passed else '❌ SOME FAILED'}")
    
    return {
        "test": "public_endpoints",
        "passed": all_passed,
        "results": results
    }


def test_admin_backup_integrity() -> Dict[str, Any]:
    """Test 5: Admin backup integrity check should still pass using admin credentials"""
    print("\n[TEST 5] Admin Backup Integrity Check (with auth)")
    
    # First, login to get admin token
    print("  Step 1: Authenticating as super admin...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": "jaymn.judd@mascigc.com",
                "password": "Maddix123!"
            },
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"    ❌ Login failed with status {login_response.status_code}")
            return {
                "test": "admin_backup_integrity",
                "passed": False,
                "error": f"Login failed: {login_response.status_code}"
            }
        
        login_data = login_response.json()
        admin_token = login_data.get("portal_tokens", {}).get("admin")
        directory_token = login_data.get("session_token")
        
        if not admin_token or not directory_token:
            print(f"    ❌ Failed to get tokens from login response")
            return {
                "test": "admin_backup_integrity",
                "passed": False,
                "error": "Missing tokens in login response"
            }
        
        print(f"    ✅ Login successful, got admin and directory tokens")
        
        # Now test backup integrity endpoint
        print("  Step 2: Testing /api/admin/backups/integrity-check...")
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        
        integrity_response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=90
        )
        
        integrity_data = integrity_response.json()
        
        passed = (
            integrity_response.status_code == 200 and
            integrity_data.get("integrity_result") == "PASS"
        )
        
        print(f"    Status: {integrity_response.status_code}")
        print(f"    Integrity result: {integrity_data.get('integrity_result')}")
        print(f"    Backup incomplete: {integrity_data.get('backup_incomplete')}")
        print(f"    Collections captured: {integrity_data.get('collections_captured')}")
        print(f"    Documents captured: {integrity_data.get('documents_captured')}")
        
        # Check for notification_capture_v1
        captured_collections = integrity_data.get("captured_collections", [])
        has_notification_capture = "notification_capture_v1" in captured_collections
        print(f"    notification_capture_v1 present: {has_notification_capture}")
        
        print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
        
        return {
            "test": "admin_backup_integrity",
            "passed": passed,
            "status_code": integrity_response.status_code,
            "integrity_result": integrity_data.get("integrity_result"),
            "backup_incomplete": integrity_data.get("backup_incomplete"),
            "has_notification_capture_v1": has_notification_capture,
            "response": integrity_data
        }
        
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return {"test": "admin_backup_integrity", "passed": False, "error": str(e)}


def main():
    print("=" * 80)
    print("Daily Report Reliability Incident Fix - Final Backend Verification")
    print("Testing against: http://localhost:8001")
    print("=" * 80)
    
    results = []
    
    # Run all tests
    results.append(test_ready_endpoint())
    results.append(test_health_full_endpoint())
    results.append(test_version_endpoint())
    results.append(test_public_endpoints())
    results.append(test_admin_backup_integrity())
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for r in results if r.get("passed"))
    total_count = len(results)
    
    for result in results:
        test_name = result.get("test", "unknown")
        passed = result.get("passed", False)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    # Save detailed results
    output_file = "/app/daily_report_reliability_final_backend_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "total_tests": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    main()
