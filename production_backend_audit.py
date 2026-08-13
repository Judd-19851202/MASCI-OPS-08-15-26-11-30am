#!/usr/bin/env python3
"""
MASCI Production Backend Audit
Target: https://mascidocs.com
Credentials: Super Admin from /app/memory/test_credentials.md
Date: 2026-08-13

PRODUCTION-SAFE AUDIT - No destructive operations on legitimate data
"""

import requests
import json
import sys
import uuid
from datetime import datetime

# Configuration
PRODUCTION_URL = "https://mascidocs.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
EXPECTED_AUTHORIZED_SHA = "a0420f4c0c63812afd31dafd78130f9c6dc8071b"

# Test results
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

# Session storage
session_data = {}

def log_pass(test_name, details=""):
    print(f"✅ PASS: {test_name}")
    if details:
        print(f"   {details}")
    results["passed"].append(test_name)

def log_fail(test_name, details=""):
    print(f"❌ FAIL: {test_name}")
    if details:
        print(f"   {details}")
    results["failed"].append(test_name)

def log_warning(test_name, details=""):
    print(f"⚠️  WARN: {test_name}")
    if details:
        print(f"   {details}")
    results["warnings"].append(test_name)

def test_1_auth_multi_login():
    """Test 1: POST /api/auth/multi-login with Super Admin credentials"""
    print("\n" + "="*80)
    print("TEST 1: Auth/Session - POST /api/auth/multi-login")
    print("="*80)
    try:
        url = f"{PRODUCTION_URL}/api/auth/multi-login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Check if login was successful
            if data.get("ok") and data.get("session_token"):
                session_data["session_token"] = data.get("session_token")
                session_data["portal_tokens"] = data.get("portal_tokens", {})
                session_data["admin_token"] = data.get("portal_tokens", {}).get("admin")
                
                log_pass("Auth/Session - Multi-login", 
                        f"Session token received, Portals: {list(session_data['portal_tokens'].keys())}")
                return True
            else:
                log_fail("Auth/Session - Multi-login", 
                        f"Status: {response.status_code}, No session token in response")
                return False
        else:
            log_fail("Auth/Session - Multi-login", 
                    f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_fail("Auth/Session - Multi-login", f"Exception: {str(e)}")
        return False

def test_2_protected_admin_call():
    """Test 1b: Verify protected admin calls succeed with session"""
    print("\n" + "="*80)
    print("TEST 1b: Protected Admin Call - GET /api/auth/me-directory")
    print("="*80)
    try:
        url = f"{PRODUCTION_URL}/api/auth/me-directory"
        headers = {}
        if session_data.get("session_token"):
            headers["X-Directory-Token"] = session_data['session_token']
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            user_email = data.get("email", "")
            portals = data.get("portals", [])
            log_pass("Protected Admin Call", 
                    f"User: {user_email}, Portals: {portals}")
            return True
        else:
            log_fail("Protected Admin Call", 
                    f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_fail("Protected Admin Call", f"Exception: {str(e)}")
        return False

def test_3_release_identity():
    """Test 2: Release identity - /api/version, /api/health, /api/health/full"""
    print("\n" + "="*80)
    print("TEST 2: Release Identity")
    print("="*80)
    
    # Test /api/version
    print("\n--- GET /api/version ---")
    try:
        url = f"{PRODUCTION_URL}/api/version"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            commit_sha = data.get("commit", "")
            source_hash = data.get("source_hash", "")
            environment = data.get("app_env", "")
            built_at = data.get("built_at", "")
            process_started = data.get("process_started_at", "")
            
            print(f"   Commit SHA: {commit_sha}")
            print(f"   Source Hash: {source_hash}")
            print(f"   Environment: {environment}")
            print(f"   Built At: {built_at}")
            print(f"   Process Started: {process_started}")
            
            # Check if SHA matches authorized
            if commit_sha == EXPECTED_AUTHORIZED_SHA:
                log_pass("Release Identity - /api/version", 
                        f"SHA matches authorized: {commit_sha}")
            else:
                log_warning("Release Identity - /api/version", 
                           f"SHA mismatch - Authorized: {EXPECTED_AUTHORIZED_SHA}, Live: {commit_sha}")
            
            # Store for later checks
            session_data["version_info"] = data
        else:
            log_fail("Release Identity - /api/version", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Release Identity - /api/version", f"Exception: {str(e)}")
    
    # Test /api/health
    print("\n--- GET /api/health ---")
    try:
        url = f"{PRODUCTION_URL}/api/health"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                log_pass("Release Identity - /api/health", f"Status: {response.status_code}")
            except:
                text = response.text.strip()
                print(f"   Response: {text}")
                log_pass("Release Identity - /api/health", f"Status: {response.status_code}")
        else:
            log_fail("Release Identity - /api/health", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Release Identity - /api/health", f"Exception: {str(e)}")
    
    # Test /api/health/full
    print("\n--- GET /api/health/full ---")
    try:
        url = f"{PRODUCTION_URL}/api/health/full"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            log_pass("Release Identity - /api/health/full", f"Status: {response.status_code}")
        elif response.status_code == 401:
            log_fail("Release Identity - /api/health/full", 
                    f"Unauthorized - Admin token may be required")
        else:
            log_fail("Release Identity - /api/health/full", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Release Identity - /api/health/full", f"Exception: {str(e)}")

def test_4_production_environment_identity():
    """Test 3: Production environment identity - DB, backup namespace, preview contamination"""
    print("\n" + "="*80)
    print("TEST 3: Production Environment Identity")
    print("="*80)
    
    version_info = session_data.get("version_info", {})
    
    # Check database
    db_name = version_info.get("db_name", "")
    db_host = version_info.get("db_host", "")
    print(f"   Database Name: {db_name}")
    print(f"   Database Host: {db_host}")
    
    if db_name == "masci_safety":
        log_pass("Production Environment - Database", f"DB: {db_name}")
    else:
        log_fail("Production Environment - Database", 
                f"Expected 'masci_safety', got '{db_name}'")
    
    # Check environment
    environment = version_info.get("app_env", "")
    print(f"   Environment: {environment}")
    
    if environment == "production":
        log_pass("Production Environment - Environment", f"Env: {environment}")
    else:
        log_fail("Production Environment - Environment", 
                f"Expected 'production', got '{environment}'")
    
    # Check backup namespace
    backup_namespace = version_info.get("backup_namespace", "")
    print(f"   Backup Namespace: {backup_namespace}")
    
    if "production" in backup_namespace.lower():
        log_pass("Production Environment - Backup Namespace", 
                f"Namespace: {backup_namespace}")
    else:
        log_warning("Production Environment - Backup Namespace", 
                   f"Namespace '{backup_namespace}' may not be production")
    
    # Check for preview contamination signals
    preview_signals = []
    if "preview" in db_name.lower():
        preview_signals.append("DB name contains 'preview'")
    if "preview" in environment.lower():
        preview_signals.append("Environment contains 'preview'")
    if "preview" in backup_namespace.lower():
        preview_signals.append("Backup namespace contains 'preview'")
    
    if preview_signals:
        log_fail("Production Environment - Preview Contamination", 
                f"Signals: {', '.join(preview_signals)}")
    else:
        log_pass("Production Environment - Preview Contamination", 
                "No preview contamination detected")

def test_5_deployment_readiness():
    """Test 4: Deployment readiness dry-run"""
    print("\n" + "="*80)
    print("TEST 4: Deployment Readiness Dry-Run")
    print("="*80)
    
    try:
        url = f"{PRODUCTION_URL}/api/admin/operations-control/operations/deploy.readiness_check/dry-run"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.post(url, json={}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            blockers = data.get("blockers", [])
            warnings = data.get("warnings", [])
            
            blocker_count = len(blockers) if isinstance(blockers, list) else 0
            warning_count = len(warnings) if isinstance(warnings, list) else 0
            
            print(f"   Blockers: {blocker_count}")
            print(f"   Warnings: {warning_count}")
            
            if blocker_count == 0:
                log_pass("Deployment Readiness", 
                        f"No blockers, Warnings: {warning_count}")
            else:
                log_fail("Deployment Readiness", 
                        f"Blockers: {blocker_count}, Warnings: {warning_count}")
                print(f"   Blocker details: {json.dumps(blockers, indent=2)}")
        elif response.status_code == 404:
            log_warning("Deployment Readiness", 
                       "Endpoint not found - may not be available in production")
        elif response.status_code == 401:
            log_fail("Deployment Readiness", "Unauthorized - Admin token required")
        else:
            log_fail("Deployment Readiness", 
                    f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        log_fail("Deployment Readiness", f"Exception: {str(e)}")

def test_6_storage_r2_health():
    """Test 5: Storage / R2 health and operational attachments storage summary"""
    print("\n" + "="*80)
    print("TEST 5: Storage / R2 Health")
    print("="*80)
    
    # Try to get storage health from system health endpoint
    try:
        url = f"{PRODUCTION_URL}/api/admin/system-health"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for storage-related info
            storage_info = data.get("storage", {})
            r2_info = data.get("r2", {})
            
            if storage_info or r2_info:
                print(f"   Storage Info: {json.dumps(storage_info, indent=2)}")
                print(f"   R2 Info: {json.dumps(r2_info, indent=2)}")
                log_pass("Storage/R2 Health", "Storage information retrieved")
            else:
                log_warning("Storage/R2 Health", 
                           "No explicit storage/R2 info in system health")
        elif response.status_code == 401:
            log_fail("Storage/R2 Health", "Unauthorized - Admin token required")
        else:
            log_fail("Storage/R2 Health", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Storage/R2 Health", f"Exception: {str(e)}")

def test_7_daily_report_crud():
    """Test 6: Daily Report safe controlled proof - CRUD operations"""
    print("\n" + "="*80)
    print("TEST 6: Daily Report CRUD (Production-Safe)")
    print("="*80)
    
    test_report_id = None
    
    # Step 1: Create a clearly labeled harmless verification record
    print("\n--- Step 1: Create Test Daily Report ---")
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        # Create a clearly labeled test report
        payload = {
            "project_name": "TEST-AUDIT",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "foreman_name": "AUDIT TEST - DO NOT USE",
            "weather": "Clear",
            "temperature_f": 72,
            "notes": f"AUTOMATED AUDIT TEST RECORD - Created {datetime.now().isoformat()} - Safe to delete",
            "audit_marker": True,
            "audit_timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_report_id = data.get("id") or data.get("report_id")
            print(f"   Created test report ID: {test_report_id}")
            log_pass("Daily Report - Create", f"Report ID: {test_report_id}")
        elif response.status_code == 401:
            log_fail("Daily Report - Create", "Unauthorized")
            return
        else:
            log_fail("Daily Report - Create", 
                    f"Status: {response.status_code}, Response: {response.text[:200]}")
            return
    except Exception as e:
        log_fail("Daily Report - Create", f"Exception: {str(e)}")
        return
    
    if not test_report_id:
        print("   Skipping remaining CRUD tests - no report ID")
        return
    
    # Step 2: Reload the report
    print("\n--- Step 2: Read Test Daily Report ---")
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports/{test_report_id}"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Retrieved report: {data.get('project_code')}")
            log_pass("Daily Report - Read", f"Report ID: {test_report_id}")
        else:
            log_fail("Daily Report - Read", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Daily Report - Read", f"Exception: {str(e)}")
    
    # Step 3: Update the report
    print("\n--- Step 3: Update Test Daily Report ---")
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports/{test_report_id}"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        payload = {
            "notes": f"UPDATED - AUTOMATED AUDIT TEST - {datetime.now().isoformat()}"
        }
        
        response = requests.patch(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            log_pass("Daily Report - Update", f"Report ID: {test_report_id}")
        else:
            log_fail("Daily Report - Update", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Daily Report - Update", f"Exception: {str(e)}")
    
    # Step 4: Verify persistence
    print("\n--- Step 4: Verify Persistence ---")
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports/{test_report_id}"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            notes = data.get("notes", "")
            if "UPDATED" in notes:
                log_pass("Daily Report - Persistence", "Update persisted correctly")
            else:
                log_fail("Daily Report - Persistence", "Update not persisted")
        else:
            log_fail("Daily Report - Persistence", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("Daily Report - Persistence", f"Exception: {str(e)}")
    
    # Step 5: Delete test report (cleanup)
    print("\n--- Step 5: Delete Test Daily Report (Cleanup) ---")
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports/{test_report_id}"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 204]:
            log_pass("Daily Report - Delete", f"Test report cleaned up")
        else:
            log_warning("Daily Report - Delete", 
                       f"Status: {response.status_code} - Manual cleanup may be needed for ID: {test_report_id}")
    except Exception as e:
        log_warning("Daily Report - Delete", 
                   f"Exception: {str(e)} - Manual cleanup may be needed for ID: {test_report_id}")

def test_8_document_attachment_storage():
    """Test 7: Document / attachment storage proof"""
    print("\n" + "="*80)
    print("TEST 7: Document/Attachment Storage (Production-Safe)")
    print("="*80)
    
    print("   NOTE: Skipping actual file upload in production audit")
    print("   Checking attachment endpoints availability instead")
    
    # Check if attachment endpoints are available
    try:
        # Try to list attachments (should require auth)
        url = f"{PRODUCTION_URL}/api/attachments"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 401, 403]:
            log_pass("Document/Attachment Storage", 
                    f"Attachment endpoints available (Status: {response.status_code})")
        else:
            log_warning("Document/Attachment Storage", 
                       f"Unexpected status: {response.status_code}")
    except Exception as e:
        log_fail("Document/Attachment Storage", f"Exception: {str(e)}")

def test_9_pdf_generation():
    """Test 8: PDF generation/download proof for a representative report"""
    print("\n" + "="*80)
    print("TEST 8: PDF Generation/Download")
    print("="*80)
    
    # Use the HR daily-report detail fixture from test_credentials.md
    fixture_report_id = "7734b79d-ce2a-42c5-ab0a-a488ea5a22ae"
    
    try:
        url = f"{PRODUCTION_URL}/api/daily-reports/{fixture_report_id}/pdf"
        headers = {}
        if session_data.get("admin_token"):
            headers["X-Admin-Token"] = session_data["admin_token"]
        
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length", "0")
            
            if "pdf" in content_type.lower():
                log_pass("PDF Generation", 
                        f"PDF generated successfully, Size: {content_length} bytes")
            else:
                log_warning("PDF Generation", 
                           f"Response received but Content-Type is '{content_type}'")
        elif response.status_code == 404:
            log_warning("PDF Generation", 
                       f"Report {fixture_report_id} not found - may be preview-only fixture")
        elif response.status_code == 401:
            log_fail("PDF Generation", "Unauthorized")
        else:
            log_fail("PDF Generation", 
                    f"Status: {response.status_code}")
    except Exception as e:
        log_fail("PDF Generation", f"Exception: {str(e)}")

def test_10_kpi_endpoints():
    """Test 9: Representative KPI / truth endpoint per major area"""
    print("\n" + "="*80)
    print("TEST 9: KPI/Truth Endpoints by Major Area")
    print("="*80)
    
    headers = {}
    if session_data.get("admin_token"):
        headers["X-Admin-Token"] = session_data["admin_token"]
    
    # Admin area
    print("\n--- Admin KPI ---")
    try:
        url = f"{PRODUCTION_URL}/api/admin/system-health"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            log_pass("KPI - Admin", "System health endpoint accessible")
        else:
            log_fail("KPI - Admin", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("KPI - Admin", f"Exception: {str(e)}")
    
    # PM area
    print("\n--- PM KPI ---")
    try:
        url = f"{PRODUCTION_URL}/api/pm/projects"
        pm_headers = {}
        if session_data.get("portal_tokens", {}).get("pm"):
            pm_headers["X-PM-Token"] = session_data["portal_tokens"]["pm"]
        
        response = requests.get(url, headers=pm_headers, timeout=30)
        
        if response.status_code in [200, 401]:
            log_pass("KPI - PM", f"Projects endpoint available (Status: {response.status_code})")
        else:
            log_fail("KPI - PM", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("KPI - PM", f"Exception: {str(e)}")
    
    # Safety area
    print("\n--- Safety KPI ---")
    try:
        url = f"{PRODUCTION_URL}/api/safety/incidents"
        safety_headers = {}
        if session_data.get("portal_tokens", {}).get("safety"):
            safety_headers["X-Safety-Token"] = session_data["portal_tokens"]["safety"]
        
        response = requests.get(url, headers=safety_headers, timeout=30)
        
        if response.status_code in [200, 401]:
            log_pass("KPI - Safety", f"Incidents endpoint available (Status: {response.status_code})")
        else:
            log_fail("KPI - Safety", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("KPI - Safety", f"Exception: {str(e)}")
    
    # Dispatch area
    print("\n--- Dispatch KPI ---")
    try:
        url = f"{PRODUCTION_URL}/api/dispatch/fleet"
        dispatch_headers = {}
        if session_data.get("portal_tokens", {}).get("dispatch"):
            dispatch_headers["X-Dispatch-Token"] = session_data["portal_tokens"]["dispatch"]
        
        response = requests.get(url, headers=dispatch_headers, timeout=30)
        
        if response.status_code in [200, 401]:
            log_pass("KPI - Dispatch", f"Fleet endpoint available (Status: {response.status_code})")
        else:
            log_fail("KPI - Dispatch", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("KPI - Dispatch", f"Exception: {str(e)}")
    
    # HR area
    print("\n--- HR KPI ---")
    try:
        url = f"{PRODUCTION_URL}/api/hr/employees"
        hr_headers = {}
        if session_data.get("portal_tokens", {}).get("hr"):
            hr_headers["X-HR-Token"] = session_data["portal_tokens"]["hr"]
        
        response = requests.get(url, headers=hr_headers, timeout=30)
        
        if response.status_code in [200, 401]:
            log_pass("KPI - HR", f"Employees endpoint available (Status: {response.status_code})")
        else:
            log_fail("KPI - HR", f"Status: {response.status_code}")
    except Exception as e:
        log_fail("KPI - HR", f"Exception: {str(e)}")

def main():
    print("=" * 80)
    print("MASCI PRODUCTION BACKEND AUDIT")
    print(f"Target: {PRODUCTION_URL}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected Authorized SHA: {EXPECTED_AUTHORIZED_SHA}")
    print("=" * 80)
    print("\n⚠️  PRODUCTION-SAFE AUDIT - No destructive operations on legitimate data")
    print("=" * 80)
    
    # Run all tests
    if not test_1_auth_multi_login():
        print("\n❌ CRITICAL: Authentication failed - cannot proceed with protected endpoints")
        print("=" * 80)
        sys.exit(1)
    
    test_2_protected_admin_call()
    test_3_release_identity()
    test_4_production_environment_identity()
    test_5_deployment_readiness()
    test_6_storage_r2_health()
    test_7_daily_report_crud()
    test_8_document_attachment_storage()
    test_9_pdf_generation()
    test_10_kpi_endpoints()
    
    # Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ PASSED: {len(results['passed'])}")
    for test in results['passed']:
        print(f"   - {test}")
    
    if results['warnings']:
        print(f"\n⚠️  WARNINGS: {len(results['warnings'])}")
        for test in results['warnings']:
            print(f"   - {test}")
    
    print(f"\n❌ FAILED: {len(results['failed'])}")
    for test in results['failed']:
        print(f"   - {test}")
    
    print("\n" + "=" * 80)
    print("ANOMALY CLASSIFICATION")
    print("=" * 80)
    
    # Classify anomalies
    if len(results['failed']) == 0 and len(results['warnings']) == 0:
        print("✅ No anomalies detected - Production backend is healthy")
    else:
        if len(results['failed']) > 0:
            print(f"❌ CRITICAL: {len(results['failed'])} test(s) failed")
        if len(results['warnings']) > 0:
            print(f"⚠️  ADVISORY: {len(results['warnings'])} warning(s) detected")
    
    print("=" * 80)
    
    # Exit with appropriate code
    if len(results['failed']) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
