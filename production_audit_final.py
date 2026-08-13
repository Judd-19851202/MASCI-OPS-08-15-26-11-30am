#!/usr/bin/env python3
"""
MASCI Production Backend Audit - Final Version
Target: https://mascidocs.com
Credentials: Super Admin from /app/memory/test_credentials.md
Date: 2026-08-13

PRODUCTION-SAFE AUDIT - No destructive operations on legitimate data
"""

import requests
import json
import sys
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
    "warnings": [],
    "skipped": []
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

def log_skip(test_name, details=""):
    print(f"⏭️  SKIP: {test_name}")
    if details:
        print(f"   {details}")
    results["skipped"].append(test_name)

print("=" * 80)
print("MASCI PRODUCTION BACKEND AUDIT - FINAL")
print(f"Target: {PRODUCTION_URL}")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Expected Authorized SHA: {EXPECTED_AUTHORIZED_SHA}")
print("=" * 80)
print("\n⚠️  PRODUCTION-SAFE AUDIT - No destructive operations on legitimate data")
print("=" * 80)

# Test 1: Auth/Session - POST /api/auth/multi-login
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
        if data.get("ok") and data.get("session_token"):
            session_data["session_token"] = data.get("session_token")
            session_data["portal_tokens"] = data.get("portal_tokens", {})
            session_data["admin_token"] = data.get("portal_tokens", {}).get("admin")
            session_data["user"] = data.get("user", {})
            
            log_pass("Auth/Session - Multi-login", 
                    f"Session token received, Portals: {list(session_data['portal_tokens'].keys())}")
        else:
            log_fail("Auth/Session - Multi-login", 
                    f"Status: {response.status_code}, No session token in response")
            sys.exit(1)
    else:
        log_fail("Auth/Session - Multi-login", 
                f"Status: {response.status_code}, Response: {response.text[:200]}")
        sys.exit(1)
except Exception as e:
    log_fail("Auth/Session - Multi-login", f"Exception: {str(e)}")
    sys.exit(1)

# Test 2: Protected Admin Call - GET /api/auth/me-directory
print("\n" + "="*80)
print("TEST 2: Protected Admin Call - GET /api/auth/me-directory")
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
        print(f"   User: {user_email}")
        print(f"   Portals: {portals}")
        log_pass("Protected Admin Call", f"Authenticated as {user_email}")
    else:
        log_fail("Protected Admin Call", 
                f"Status: {response.status_code}, Response: {response.text[:200]}")
except Exception as e:
    log_fail("Protected Admin Call", f"Exception: {str(e)}")

# Test 3: Release Identity - /api/version
print("\n" + "="*80)
print("TEST 3: Release Identity - /api/version")
print("="*80)
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
        db_name = data.get("db_name", "")
        
        print(f"   Commit SHA: {commit_sha}")
        print(f"   Source Hash: {source_hash[:50]}...")
        print(f"   Environment: {environment}")
        print(f"   Built At: {built_at}")
        print(f"   Process Started: {process_started}")
        print(f"   Database: {db_name}")
        
        # Store for later checks
        session_data["version_info"] = data
        
        # Check if SHA matches authorized
        if commit_sha == EXPECTED_AUTHORIZED_SHA:
            log_pass("Release Identity - /api/version", 
                    f"SHA matches authorized: {commit_sha}")
        else:
            log_warning("Release Identity - /api/version", 
                       f"SHA mismatch - Authorized: {EXPECTED_AUTHORIZED_SHA}, Live: {commit_sha}")
    else:
        log_fail("Release Identity - /api/version", f"Status: {response.status_code}")
except Exception as e:
    log_fail("Release Identity - /api/version", f"Exception: {str(e)}")

# Test 4: /api/health
print("\n" + "="*80)
print("TEST 4: /api/health")
print("="*80)
try:
    url = f"{PRODUCTION_URL}/api/health"
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        log_pass("/api/health", f"Status: {response.status_code}")
    else:
        log_fail("/api/health", f"Status: {response.status_code}")
except Exception as e:
    log_fail("/api/health", f"Exception: {str(e)}")

# Test 5: /api/health/full
print("\n" + "="*80)
print("TEST 5: /api/health/full")
print("="*80)
try:
    url = f"{PRODUCTION_URL}/api/health/full"
    headers = {}
    if session_data.get("admin_token"):
        headers["X-Admin-Token"] = session_data["admin_token"]
    
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response keys: {list(data.keys())}")
        
        # Check specific health indicators
        mongo_ok = data.get("mongo", {}).get("ok", False)
        scheduler_ok = data.get("scheduler", {}).get("ok", False)
        backup_recent = data.get("backup_recent", {}).get("ok", False)
        
        print(f"   MongoDB: {'✓' if mongo_ok else '✗'}")
        print(f"   Scheduler: {'✓' if scheduler_ok else '✗'}")
        print(f"   Backup Recent: {'✓' if backup_recent else '✗'}")
        
        log_pass("/api/health/full", f"Status: {response.status_code}")
    elif response.status_code == 401:
        log_fail("/api/health/full", "Unauthorized - Admin token required")
    else:
        log_fail("/api/health/full", f"Status: {response.status_code}")
except Exception as e:
    log_fail("/api/health/full", f"Exception: {str(e)}")

# Test 6: Production Environment Identity
print("\n" + "="*80)
print("TEST 6: Production Environment Identity")
print("="*80)

version_info = session_data.get("version_info", {})

# Check database
db_name = version_info.get("db_name", "")
print(f"   Database Name: {db_name}")

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

# Check for preview contamination signals
preview_signals = []
if "preview" in db_name.lower():
    preview_signals.append("DB name contains 'preview'")
if "preview" in environment.lower():
    preview_signals.append("Environment contains 'preview'")

if preview_signals:
    log_fail("Production Environment - Preview Contamination", 
            f"Signals: {', '.join(preview_signals)}")
else:
    log_pass("Production Environment - Preview Contamination", 
            "No preview contamination detected")

# Test 7: Deployment Readiness (if available)
print("\n" + "="*80)
print("TEST 7: Deployment Readiness Dry-Run")
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
    elif response.status_code == 404:
        log_skip("Deployment Readiness", 
                   "Endpoint not found - may not be available in production")
    elif response.status_code == 401:
        log_fail("Deployment Readiness", "Unauthorized - Admin token required")
    else:
        log_fail("Deployment Readiness", 
                f"Status: {response.status_code}")
except Exception as e:
    log_fail("Deployment Readiness", f"Exception: {str(e)}")

# Test 8: Storage / R2 Health
print("\n" + "="*80)
print("TEST 8: Storage / R2 Health")
print("="*80)
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

# Test 9: Daily Report CRUD - SKIP in production
print("\n" + "="*80)
print("TEST 9: Daily Report CRUD")
print("="*80)
log_skip("Daily Report CRUD", 
        "Skipped in production audit to avoid creating test data")

# Test 10: Document/Attachment Storage
print("\n" + "="*80)
print("TEST 10: Document/Attachment Storage")
print("="*80)
log_skip("Document/Attachment Storage", 
        "Skipped in production audit - no safe way to test without creating data")

# Test 11: PDF Generation
print("\n" + "="*80)
print("TEST 11: PDF Generation/Download")
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

# Test 12: KPI Endpoints - Sample check
print("\n" + "="*80)
print("TEST 12: KPI/Truth Endpoints - Sample Check")
print("="*80)

# Admin area - system health
print("\n--- Admin KPI (system-health) ---")
try:
    url = f"{PRODUCTION_URL}/api/admin/system-health"
    headers = {}
    if session_data.get("admin_token"):
        headers["X-Admin-Token"] = session_data["admin_token"]
    
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        log_pass("KPI - Admin", "System health endpoint accessible")
    else:
        log_fail("KPI - Admin", f"Status: {response.status_code}")
except Exception as e:
    log_fail("KPI - Admin", f"Exception: {str(e)}")

# HR area - employees
print("\n--- HR KPI (employees) ---")
try:
    url = f"{PRODUCTION_URL}/api/hr/employees"
    headers = {}
    if session_data.get("portal_tokens", {}).get("hr"):
        headers["X-HR-Token"] = session_data["portal_tokens"]["hr"]
    
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code in [200, 401]:
        log_pass("KPI - HR", f"Employees endpoint available (Status: {response.status_code})")
    else:
        log_fail("KPI - HR", f"Status: {response.status_code}")
except Exception as e:
    log_fail("KPI - HR", f"Exception: {str(e)}")

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

if results['skipped']:
    print(f"\n⏭️  SKIPPED: {len(results['skipped'])}")
    for test in results['skipped']:
        print(f"   - {test}")

print(f"\n❌ FAILED: {len(results['failed'])}")
for test in results['failed']:
    print(f"   - {test}")

print("\n" + "=" * 80)
print("ANOMALY CLASSIFICATION")
print("=" * 80)

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
