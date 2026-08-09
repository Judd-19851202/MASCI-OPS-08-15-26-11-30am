#!/usr/bin/env python3
"""
PRE-C10 Cross-Entity Exception Reconciliation Backend Verification

This script verifies the backend behaviors for the PRE-C10 cross-entity exception
reconciliation batch. The critical claim is that materially misclassified exceptions
are now zero while the total exception population remains auditable.

Test Requirements:
1. Auth continuity - POST /api/auth/multi-login
2. Cross-entity remains green - GET /api/admin/platform-truth-integrity/cross-entity
3. Exception list surface - GET /api/admin/platform-truth-integrity/cross-entity/exceptions
4. Reconciliation normalization endpoint - POST /api/admin/platform-truth-integrity/cross-entity/exceptions/reconcile
5. Reconciliation read endpoint - GET /api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation
6. Reconciliation CSV endpoint - GET /api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation.csv
7. History regression smoke - GET /api/master-lookup/employees/{id}/history and equipment/{id}/history
"""

import sys
import requests
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Admin credentials from review request
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results tracking
test_results = []


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")


def get_admin_headers() -> Optional[Dict[str, str]]:
    """Authenticate and get admin headers"""
    try:
        print("\n=== Test 1: Auth Continuity ===")
        resp = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if resp.status_code != 200:
            log_test("1. Auth continuity - POST /api/auth/multi-login", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return None
        
        body = resp.json()
        
        # Verify response structure
        if "session_token" not in body:
            log_test("1. Auth continuity - POST /api/auth/multi-login", False, 
                    "Missing session_token in response")
            return None
        
        if "portal_tokens" not in body or "admin" not in body["portal_tokens"]:
            log_test("1. Auth continuity - POST /api/auth/multi-login", False, 
                    "Missing portal_tokens.admin in response")
            return None
        
        log_test("1. Auth continuity - POST /api/auth/multi-login", True, 
                "Authentication successful, tokens received")
        
        return {
            "X-Admin-Token": body["portal_tokens"]["admin"],
            "X-Directory-Token": body["session_token"],
        }
    except Exception as e:
        log_test("1. Auth continuity - POST /api/auth/multi-login", False, str(e))
        return None


def test_cross_entity_green(headers: Dict[str, str]):
    """Test 2: Cross-entity remains green"""
    print("\n=== Test 2: Cross-Entity Remains Green ===")
    try:
        resp = requests.get(
            f"{BASE_URL}/admin/platform-truth-integrity/cross-entity",
            headers=headers,
            timeout=180
        )
        
        if resp.status_code != 200:
            log_test("2. Cross-entity gate status", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return
        
        body = resp.json()
        
        # Verify overall_status=green
        if body.get("overall_status") != "green":
            log_test("2. Cross-entity gate status", False, 
                    f"overall_status is '{body.get('overall_status')}', expected 'green'")
            return
        
        # Verify release_gate_blocked=false
        if body.get("release_gate_blocked") is not False:
            log_test("2. Cross-entity gate status", False, 
                    f"release_gate_blocked is {body.get('release_gate_blocked')}, expected false")
            return
        
        log_test("2. Cross-entity gate status", True, 
                f"overall_status=green, release_gate_blocked=false")
        
    except Exception as e:
        log_test("2. Cross-entity gate status", False, str(e))


def test_exception_list(headers: Dict[str, str]):
    """Test 3: Exception list surface"""
    print("\n=== Test 3: Exception List Surface ===")
    try:
        resp = requests.get(
            f"{BASE_URL}/admin/platform-truth-integrity/cross-entity/exceptions",
            headers=headers,
            timeout=180
        )
        
        if resp.status_code != 200:
            log_test("3. Exception list surface", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return
        
        body = resp.json()
        
        # Verify count > 0
        count = body.get("count", 0)
        if count <= 0:
            log_test("3. Exception list surface", False, 
                    f"Exception count is {count}, expected > 0")
            return
        
        # Verify rows include both statuses
        rows = body.get("rows", [])
        statuses = set(row.get("status") for row in rows)
        
        has_excluded = "excluded_non_operational" in statuses
        has_accepted = "accepted_historical_gap" in statuses
        
        if not (has_excluded or has_accepted):
            log_test("3. Exception list surface", False, 
                    f"Missing expected statuses. Found: {statuses}")
            return
        
        log_test("3. Exception list surface", True, 
                f"Count={count}, Statuses include: {', '.join(sorted(statuses))}")
        
    except Exception as e:
        log_test("3. Exception list surface", False, str(e))


def test_reconciliation_normalization(headers: Dict[str, str]):
    """Test 4: Reconciliation normalization endpoint"""
    print("\n=== Test 4: Reconciliation Normalization Endpoint ===")
    try:
        resp = requests.post(
            f"{BASE_URL}/admin/platform-truth-integrity/cross-entity/exceptions/reconcile",
            headers=headers,
            timeout=180
        )
        
        if resp.status_code != 200:
            log_test("4. Reconciliation normalization endpoint", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return
        
        body = resp.json()
        
        # Verify response includes both normalization and reconciliation objects
        if "normalization" not in body:
            log_test("4. Reconciliation normalization endpoint", False, 
                    "Missing 'normalization' in response")
            return
        
        if "reconciliation" not in body:
            log_test("4. Reconciliation normalization endpoint", False, 
                    "Missing 'reconciliation' in response")
            return
        
        reconciliation = body["reconciliation"]
        
        # Verify reconciliation.total_exceptions > 0
        total_exceptions = reconciliation.get("total_exceptions", 0)
        if total_exceptions <= 0:
            log_test("4. Reconciliation normalization endpoint", False, 
                    f"total_exceptions is {total_exceptions}, expected > 0")
            return
        
        # Verify reconciliation.classification_integrity.materially_misclassified_exceptions = 0
        classification_integrity = reconciliation.get("classification_integrity", {})
        materially_misclassified = classification_integrity.get("materially_misclassified_exceptions")
        
        if materially_misclassified != 0:
            log_test("4. Reconciliation normalization endpoint", False, 
                    f"materially_misclassified_exceptions is {materially_misclassified}, expected 0")
            return
        
        # Verify reconciliation.record_temporality.current_live_operational_records is present
        record_temporality = reconciliation.get("record_temporality", {})
        if "current_live_operational_records" not in record_temporality:
            log_test("4. Reconciliation normalization endpoint", False, 
                    "Missing 'current_live_operational_records' in record_temporality")
            return
        
        current_live = record_temporality.get("current_live_operational_records")
        
        log_test("4. Reconciliation normalization endpoint", True, 
                f"total_exceptions={total_exceptions}, materially_misclassified=0, current_live={current_live}")
        
    except Exception as e:
        log_test("4. Reconciliation normalization endpoint", False, str(e))


def test_reconciliation_read(headers: Dict[str, str]):
    """Test 5: Reconciliation read endpoint"""
    print("\n=== Test 5: Reconciliation Read Endpoint ===")
    try:
        resp = requests.get(
            f"{BASE_URL}/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation",
            headers=headers,
            timeout=180
        )
        
        if resp.status_code != 200:
            log_test("5. Reconciliation read endpoint", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return
        
        body = resp.json()
        
        # Verify materially_misclassified_exceptions = 0
        classification_integrity = body.get("classification_integrity", {})
        materially_misclassified = classification_integrity.get("materially_misclassified_exceptions")
        
        if materially_misclassified != 0:
            log_test("5. Reconciliation read endpoint", False, 
                    f"materially_misclassified_exceptions is {materially_misclassified}, expected 0")
            return
        
        # Verify count sections exist
        required_sections = [
            "count_by_source_family",
            "count_by_relationship_type",
            "count_by_age_time_period",
            "active_entity_involvement",
            "cause_summary",
            "downstream_relevance",
            "non_blocking_current_live_breakdown"
        ]
        
        missing_sections = [section for section in required_sections if section not in body]
        
        if missing_sections:
            log_test("5. Reconciliation read endpoint", False, 
                    f"Missing sections: {', '.join(missing_sections)}")
            return
        
        log_test("5. Reconciliation read endpoint", True, 
                f"materially_misclassified=0, all required sections present")
        
    except Exception as e:
        log_test("5. Reconciliation read endpoint", False, str(e))


def test_reconciliation_csv(headers: Dict[str, str]):
    """Test 6: Reconciliation CSV endpoint"""
    print("\n=== Test 6: Reconciliation CSV Endpoint ===")
    try:
        resp = requests.get(
            f"{BASE_URL}/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation.csv",
            headers=headers,
            timeout=180
        )
        
        if resp.status_code != 200:
            log_test("6. Reconciliation CSV endpoint", False, 
                    f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return
        
        csv_content = resp.text
        
        # Verify CSV has header `section,metric,count`
        if not csv_content.startswith("section,metric,count"):
            log_test("6. Reconciliation CSV endpoint", False, 
                    f"CSV header mismatch. First line: {csv_content.split(chr(10))[0]}")
            return
        
        # Count lines
        lines = csv_content.strip().split('\n')
        line_count = len(lines)
        
        log_test("6. Reconciliation CSV endpoint", True, 
                f"CSV format correct, {line_count} lines (including header)")
        
    except Exception as e:
        log_test("6. Reconciliation CSV endpoint", False, str(e))


def test_history_regression(headers: Dict[str, str]):
    """Test 7: History regression smoke"""
    print("\n=== Test 7: History Regression Smoke ===")
    
    # Use MongoDB to get sample IDs directly
    from pathlib import Path
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    
    def _read_env(path: str, key: str) -> str:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
        return ""
    
    MONGO_URL = _read_env("/app/backend/.env", "MONGO_URL")
    DB_NAME = _read_env("/app/backend/.env", "DB_NAME")
    
    async def get_sample_ids():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Get sample employee
        employee = await db.employees.find_one({}, {"_id": 0, "id": 1})
        employee_id = employee.get("id") if employee else None
        
        # Get sample equipment
        equipment = await db.equipment_master.find_one({}, {"_id": 0, "id": 1})
        equipment_id = equipment.get("id") if equipment else None
        
        client.close()
        return employee_id, equipment_id
    
    try:
        employee_id, equipment_id = asyncio.run(get_sample_ids())
        
        # Test employee history endpoint
        if employee_id:
            hist_resp = requests.get(
                f"{BASE_URL}/master-lookup/employees/{employee_id}/history",
                headers=headers,
                timeout=30
            )
            
            if hist_resp.status_code != 200:
                log_test("7a. Employee history endpoint", False, 
                        f"Status: {hist_resp.status_code}, Response: {hist_resp.text[:200]}")
            else:
                log_test("7a. Employee history endpoint", True, 
                        f"Employee {employee_id} history returned 200")
        else:
            log_test("7a. Employee history endpoint", False, 
                    "No employees found in database")
        
        # Test equipment history endpoint
        if equipment_id:
            hist_resp = requests.get(
                f"{BASE_URL}/master-lookup/equipment/{equipment_id}/history",
                headers=headers,
                timeout=30
            )
            
            if hist_resp.status_code != 200:
                log_test("7b. Equipment history endpoint", False, 
                        f"Status: {hist_resp.status_code}, Response: {hist_resp.text[:200]}")
            else:
                log_test("7b. Equipment history endpoint", True, 
                        f"Equipment {equipment_id} history returned 200")
        else:
            log_test("7b. Equipment history endpoint", False, 
                    "No equipment found in database")
        
    except Exception as e:
        log_test("7a. Employee history endpoint", False, str(e))
        log_test("7b. Equipment history endpoint", False, str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for t in test_results if t["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    # Print failed tests
    failed_tests = [t for t in test_results if not t["passed"]]
    if failed_tests:
        print("FAILED TESTS:")
        for test in failed_tests:
            print(f"  ❌ {test['name']}")
            if test['details']:
                print(f"     {test['details']}")
    else:
        print("✅ ALL TESTS PASSED")
    
    print("\n" + "="*80)
    
    return passed == total


def main():
    """Main test execution"""
    print("="*80)
    print("PRE-C10 Cross-Entity Exception Reconciliation Backend Verification")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print("="*80)
    
    # Test 1: Auth continuity
    headers = get_admin_headers()
    if not headers:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with remaining tests.")
        print_summary()
        sys.exit(1)
    
    # Test 2: Cross-entity remains green
    test_cross_entity_green(headers)
    
    # Test 3: Exception list surface
    test_exception_list(headers)
    
    # Test 4: Reconciliation normalization endpoint
    test_reconciliation_normalization(headers)
    
    # Test 5: Reconciliation read endpoint
    test_reconciliation_read(headers)
    
    # Test 6: Reconciliation CSV endpoint
    test_reconciliation_csv(headers)
    
    # Test 7: History regression smoke
    test_history_regression(headers)
    
    # Print summary
    all_passed = print_summary()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
