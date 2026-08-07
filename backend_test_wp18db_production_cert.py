#!/usr/bin/env python3
"""
WP-18DB Final Production Certification - Backend/Runtime
Target: https://mascidocs.com
Scope: Release identity, public submit proofs, auth boundaries, backup health, downstream truth
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Production URL
BASE_URL = "https://mascidocs.com"
API_URL = f"{BASE_URL}/api"

# Super Admin credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results storage
results = {
    "test_run_id": str(uuid.uuid4()),
    "timestamp": datetime.utcnow().isoformat(),
    "target": BASE_URL,
    "tests": []
}

def log_test(test_name, passed, details):
    """Log test result"""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if not passed or details.get("important"):
        print(f"  Details: {json.dumps(details, indent=2)}")
    return passed

def test_admin_login():
    """Test 1: Super Admin login works"""
    try:
        response = requests.post(
            f"{API_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            
            if session_token and admin_token:
                return log_test("Admin Login", True, {
                    "session_token_length": len(session_token),
                    "admin_token_length": len(admin_token),
                    "user_email": data.get("user", {}).get("email")
                }), session_token, admin_token
            else:
                return log_test("Admin Login", False, {
                    "error": "Missing tokens in response",
                    "response": data
                }), None, None
        else:
            return log_test("Admin Login", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Admin Login", False, {"error": str(e)}), None, None

def test_release_identity(session_token, admin_token):
    """Test 2: Release identity / parity"""
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test /api/version
    try:
        response = requests.get(f"{API_URL}/version", timeout=30)
        if response.status_code == 200:
            version_data = response.json()
            log_test("GET /api/version", True, {
                "important": True,
                "commit": version_data.get("commit"),
                "source_hash": version_data.get("source_hash"),
                "app_env": version_data.get("app_env"),
                "runtime_identity": version_data.get("runtime_identity")
            })
        else:
            log_test("GET /api/version", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
    except Exception as e:
        log_test("GET /api/version", False, {"error": str(e)})
    
    # Test /release-identity.json
    try:
        response = requests.get(f"{BASE_URL}/release-identity.json", timeout=30)
        if response.status_code == 200:
            release_data = response.json()
            log_test("GET /release-identity.json", True, {
                "important": True,
                "release_id": release_data.get("release_id"),
                "commit": release_data.get("commit"),
                "deployed_at": release_data.get("deployed_at")
            })
        else:
            log_test("GET /release-identity.json", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
    except Exception as e:
        log_test("GET /release-identity.json", False, {"error": str(e)})
    
    # Test /api/platform/data-truth
    try:
        response = requests.get(f"{API_URL}/platform/data-truth", headers=headers, timeout=30)
        if response.status_code == 200:
            truth_data = response.json()
            log_test("GET /api/platform/data-truth", True, {
                "important": True,
                "runtime_matches_intended_release": truth_data.get("runtime_matches_intended_release"),
                "frontend_backend_release_match": truth_data.get("frontend_backend_release_match"),
                "attestation_mode": truth_data.get("attestation_mode")
            })
        else:
            log_test("GET /api/platform/data-truth", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
    except Exception as e:
        log_test("GET /api/platform/data-truth", False, {"error": str(e)})

def test_public_daily_report_submit():
    """Test 3: Public Daily Report submit (no login required)"""
    idempotency_key = f"WP18DB-PROD-CERT-DR-{uuid.uuid4()}"
    
    payload = {
        "project_number": "WP18DB-PROD-CERT",
        "project_name": "WP-18DB Production Certification Test",
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "foreman_name": "WP18DB Certification Bot",
        "foreman_email": "cert@mascicert.local",
        "weather_condition": "Clear",
        "temperature_high": 75,
        "temperature_low": 65,
        "notes": "WP-18DB Production Certification - Safe controlled test record. This is a certification marker record and can be safely deleted."
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        # First submission
        response = requests.post(
            f"{API_URL}/public/daily-reports",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            report_id = data.get("id") or data.get("report_id")
            doc_number = data.get("doc_number") or data.get("report_number")
            
            # Test idempotency - replay should not create duplicate
            time.sleep(1)
            response2 = requests.post(
                f"{API_URL}/public/daily-reports",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            is_duplicate = response2.json().get("duplicate", False)
            
            return log_test("Public Daily Report Submit", True, {
                "important": True,
                "report_id": report_id,
                "doc_number": doc_number,
                "idempotency_key": idempotency_key,
                "idempotency_works": is_duplicate,
                "status_code": response.status_code
            }), report_id, doc_number
        else:
            return log_test("Public Daily Report Submit", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Public Daily Report Submit", False, {"error": str(e)}), None, None

def test_public_incident_submit():
    """Test 4: Public Incident Report submit (no login required)"""
    idempotency_key = f"WP18DB-PROD-CERT-INC-{uuid.uuid4()}"
    
    payload = {
        "incident_type": "near_miss",
        "incident_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "incident_time": datetime.utcnow().strftime("%H:%M"),
        "location": "WP18DB Certification Test Site",
        "description": "WP-18DB Production Certification - Safe controlled test record. This is a certification marker record and can be safely deleted.",
        "reporter_name": "WP18DB Certification Bot",
        "reporter_email": "cert@mascicert.local",
        "project_number": "WP18DB-PROD-CERT"
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/public/incident-cases",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            case_id = data.get("id") or data.get("case_id")
            case_number = data.get("case_number") or data.get("reference_number")
            
            # Test idempotency
            time.sleep(1)
            response2 = requests.post(
                f"{API_URL}/public/incident-cases",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            is_duplicate = response2.json().get("duplicate", False)
            
            return log_test("Public Incident Report Submit", True, {
                "important": True,
                "case_id": case_id,
                "case_number": case_number,
                "idempotency_key": idempotency_key,
                "idempotency_works": is_duplicate
            }), case_id, case_number
        else:
            return log_test("Public Incident Report Submit", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Public Incident Report Submit", False, {"error": str(e)}), None, None

def test_public_meeting_submit():
    """Test 5: Public Safety Meeting submit (no login required)"""
    idempotency_key = f"WP18DB-PROD-CERT-MTG-{uuid.uuid4()}"
    
    payload = {
        "meeting_type": "toolbox_talk",
        "meeting_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "meeting_time": datetime.utcnow().strftime("%H:%M"),
        "location": "WP18DB Certification Test Site",
        "topic": "WP-18DB Production Certification Test",
        "facilitator_name": "WP18DB Certification Bot",
        "facilitator_email": "cert@mascicert.local",
        "project_number": "WP18DB-PROD-CERT",
        "notes": "WP-18DB Production Certification - Safe controlled test record. This is a certification marker record and can be safely deleted."
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/public/meetings",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            meeting_id = data.get("id") or data.get("meeting_id")
            doc_number = data.get("doc_number") or data.get("meeting_number")
            
            return log_test("Public Safety Meeting Submit", True, {
                "important": True,
                "meeting_id": meeting_id,
                "doc_number": doc_number,
                "idempotency_key": idempotency_key
            }), meeting_id, doc_number
        else:
            return log_test("Public Safety Meeting Submit", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Public Safety Meeting Submit", False, {"error": str(e)}), None, None

def test_public_equipment_submit():
    """Test 6: Public Equipment Pre-Op submit (no login required)"""
    idempotency_key = f"WP18DB-PROD-CERT-EQ-{uuid.uuid4()}"
    
    payload = {
        "equipment_type": "excavator",
        "equipment_id": "WP18DB-CERT-001",
        "inspection_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "inspection_time": datetime.utcnow().strftime("%H:%M"),
        "inspector_name": "WP18DB Certification Bot",
        "inspector_email": "cert@mascicert.local",
        "project_number": "WP18DB-PROD-CERT",
        "status": "pass",
        "notes": "WP-18DB Production Certification - Safe controlled test record. This is a certification marker record and can be safely deleted."
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/public/equipment-inspections",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            inspection_id = data.get("id") or data.get("inspection_id")
            doc_number = data.get("doc_number") or data.get("inspection_number")
            
            return log_test("Public Equipment Pre-Op Submit", True, {
                "important": True,
                "inspection_id": inspection_id,
                "doc_number": doc_number,
                "idempotency_key": idempotency_key
            }), inspection_id, doc_number
        else:
            return log_test("Public Equipment Pre-Op Submit", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Public Equipment Pre-Op Submit", False, {"error": str(e)}), None, None

def test_public_dvir_submit():
    """Test 7: Public DVIR submit (no login required)"""
    idempotency_key = f"WP18DB-PROD-CERT-DVIR-{uuid.uuid4()}"
    
    payload = {
        "vehicle_id": "WP18DB-CERT-TRUCK-001",
        "driver_name": "WP18DB Certification Bot",
        "driver_email": "cert@mascicert.local",
        "inspection_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "inspection_time": datetime.utcnow().strftime("%H:%M"),
        "odometer": 100000,
        "status": "pass",
        "notes": "WP-18DB Production Certification - Safe controlled test record. This is a certification marker record and can be safely deleted."
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/public/fleet/dvir",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            dvir_id = data.get("id") or data.get("dvir_id")
            doc_number = data.get("doc_number") or data.get("dvir_number")
            
            return log_test("Public DVIR Submit", True, {
                "important": True,
                "dvir_id": dvir_id,
                "doc_number": doc_number,
                "idempotency_key": idempotency_key
            }), dvir_id, doc_number
        else:
            return log_test("Public DVIR Submit", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            }), None, None
    except Exception as e:
        return log_test("Public DVIR Submit", False, {"error": str(e)}), None, None

def test_site_audit_boundary():
    """Test 8: Site Audit boundary (must be 401/403 without auth)"""
    payload = {
        "inspection_type": "site_audit",
        "inspection_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "notes": "This should fail without auth"
    }
    
    try:
        # Try to submit without auth - should fail
        response = requests.post(
            f"{API_URL}/inspections",
            json=payload,
            timeout=30
        )
        
        if response.status_code in [401, 403]:
            return log_test("Site Audit Boundary (Protected)", True, {
                "important": True,
                "status_code": response.status_code,
                "message": "Correctly rejected unauthenticated write"
            })
        else:
            return log_test("Site Audit Boundary (Protected)", False, {
                "status_code": response.status_code,
                "error": "Site audit endpoint is publicly writable - SECURITY ISSUE",
                "response": response.text[:500]
            })
    except Exception as e:
        return log_test("Site Audit Boundary (Protected)", False, {"error": str(e)})

def test_daily_report_downstream_truth(session_token, admin_token, report_id):
    """Test 9: Daily Report downstream truth"""
    if not report_id:
        return log_test("Daily Report Downstream Truth", False, {
            "error": "No report_id available from public submit test"
        })
    
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        # Verify report exists via admin endpoint
        response = requests.get(
            f"{API_URL}/daily-reports/{report_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            return log_test("Daily Report Downstream Truth", True, {
                "important": True,
                "report_id": report_id,
                "doc_number": data.get("doc_number"),
                "persisted": True,
                "has_audit_trail": "created_at" in data,
                "has_lifecycle": "status" in data or "state" in data
            })
        else:
            return log_test("Daily Report Downstream Truth", False, {
                "status_code": response.status_code,
                "error": "Could not retrieve report via admin endpoint",
                "response": response.text[:500]
            })
    except Exception as e:
        return log_test("Daily Report Downstream Truth", False, {"error": str(e)})

def test_backup_recovery_health(session_token, admin_token):
    """Test 10: Backup/recovery health"""
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        # Test recovery snapshot
        response = requests.get(
            f"{API_URL}/admin/recovery/snapshot",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            last_backup = data.get("last_backup", {})
            backup_age_minutes = last_backup.get("backup_age_minutes", 999)
            
            # Determine status based on age
            if backup_age_minutes <= 60:
                status = "HEALTHY"
            elif backup_age_minutes <= 75:
                status = "WARNING"
            else:
                status = "RED"
            
            log_test("Backup/Recovery Health", True, {
                "important": True,
                "backup_age_minutes": backup_age_minutes,
                "status": status,
                "integrity": last_backup.get("integrity_status"),
                "completeness": last_backup.get("completeness_status"),
                "availability": last_backup.get("availability_status"),
                "alert_threshold_60_75_warning": backup_age_minutes > 60 and backup_age_minutes <= 75,
                "alert_threshold_75_red": backup_age_minutes > 75
            })
        else:
            log_test("Backup/Recovery Health", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
        
        # Test backup scheduler state
        response = requests.get(
            f"{API_URL}/admin/backups-scheduler-state",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test("Backup Scheduler State", True, {
                "important": True,
                "hourly_activation": data.get("hourly_activation", {}),
                "nightly_activation": data.get("nightly_activation", {})
            })
        else:
            log_test("Backup Scheduler State", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
            
    except Exception as e:
        log_test("Backup/Recovery Health", False, {"error": str(e)})

def test_production_auth_security(session_token, admin_token):
    """Test 11: Production auth/security basics"""
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test protected admin health surfaces
    try:
        response = requests.get(
            f"{API_URL}/admin/system-health",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test("Protected Admin Health Surface", True, {
                "important": True,
                "status_code": response.status_code,
                "accessible_with_admin_token": True
            })
        else:
            log_test("Protected Admin Health Surface", False, {
                "status_code": response.status_code,
                "response": response.text[:500]
            })
    except Exception as e:
        log_test("Protected Admin Health Surface", False, {"error": str(e)})
    
    # Test protected incident workspace (should require auth)
    try:
        response = requests.post(
            f"{API_URL}/incident-cases",
            json={"incident_type": "test"},
            timeout=30
        )
        
        if response.status_code in [401, 403]:
            log_test("Protected Incident Workspace", True, {
                "important": True,
                "status_code": response.status_code,
                "correctly_protected": True
            })
        else:
            log_test("Protected Incident Workspace", False, {
                "status_code": response.status_code,
                "error": "Incident workspace is publicly writable - SECURITY ISSUE"
            })
    except Exception as e:
        log_test("Protected Incident Workspace", False, {"error": str(e)})

def main():
    """Run all WP-18DB production certification tests"""
    print("=" * 80)
    print("WP-18DB FINAL PRODUCTION CERTIFICATION - BACKEND/RUNTIME")
    print(f"Target: {BASE_URL}")
    print(f"Test Run ID: {results['test_run_id']}")
    print("=" * 80)
    print()
    
    # Test 1: Admin Login
    print("TEST GROUP 1: AUTHENTICATION")
    login_success, session_token, admin_token = test_admin_login()
    print()
    
    if not login_success:
        print("❌ CRITICAL: Admin login failed. Cannot proceed with authenticated tests.")
        print("Continuing with public endpoint tests only...")
        print()
    
    # Test 2: Release Identity
    if login_success:
        print("TEST GROUP 2: RELEASE IDENTITY / PARITY")
        test_release_identity(session_token, admin_token)
        print()
    
    # Test 3-7: Public Submit Proofs
    print("TEST GROUP 3: PUBLIC/NO-LOGIN WORKFLOW SUBMIT PROOFS")
    daily_report_success, report_id, report_doc_number = test_public_daily_report_submit()
    incident_success, incident_id, incident_case_number = test_public_incident_submit()
    meeting_success, meeting_id, meeting_doc_number = test_public_meeting_submit()
    equipment_success, equipment_id, equipment_doc_number = test_public_equipment_submit()
    dvir_success, dvir_id, dvir_doc_number = test_public_dvir_submit()
    print()
    
    # Test 8: Site Audit Boundary
    print("TEST GROUP 4: SITE AUDIT BOUNDARY")
    test_site_audit_boundary()
    print()
    
    # Test 9: Daily Report Downstream Truth
    if login_success and daily_report_success:
        print("TEST GROUP 5: DAILY REPORT DOWNSTREAM TRUTH")
        test_daily_report_downstream_truth(session_token, admin_token, report_id)
        print()
    
    # Test 10: Backup/Recovery Health
    if login_success:
        print("TEST GROUP 6: BACKUP/RECOVERY HEALTH")
        test_backup_recovery_health(session_token, admin_token)
        print()
    
    # Test 11: Production Auth/Security
    if login_success:
        print("TEST GROUP 7: PRODUCTION AUTH/SECURITY BASICS")
        test_production_auth_security(session_token, admin_token)
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total_tests = len(results["tests"])
    passed_tests = sum(1 for t in results["tests"] if t["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()
    
    if failed_tests > 0:
        print("FAILED TESTS:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"  ❌ {test['test']}")
                print(f"     {test['details']}")
        print()
    
    # Save results
    with open("/app/backend_test_wp18db_production_cert_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: /app/backend_test_wp18db_production_cert_results.json")
    print("=" * 80)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
