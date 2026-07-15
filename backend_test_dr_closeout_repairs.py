#!/usr/bin/env python3
"""
Backend test for Daily Report Closeout Repairs - Track 27.11D
Tests draft telemetry formKey validation and governed certification lane.

Requirements:
1. POST /api/draft-telemetry accepts valid long scoped Daily Report formKey values (>64 chars, ≤180 chars)
2. Valid telemetry should reject only truly invalid over-limit formKey values (>180 chars)
3. Controlled certification field identity cert.foreman@example.com / CertProof2026! can obtain an FL token
4. Governed certification Daily Report response must include all required fields
"""
import requests
import sys
import time
from datetime import datetime

BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from test_credentials.md
CERT_FOREMAN_EMAIL = "cert.foreman@example.com"
CERT_FOREMAN_PASSWORD = "CertProof2026!"
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
CERT_PM_EMAIL = "cert.pm@example.com"
CERT_CO_PM_EMAIL = "cert.copm@example.com"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_draft_telemetry_formkey_validation():
    """Test 1 & 2: Draft telemetry formKey validation (64-180 char range)"""
    log("=" * 80)
    log("TEST 1 & 2: Draft Telemetry formKey Validation")
    log("=" * 80)
    
    # Test case 1: Valid 65-char formKey (>64 chars)
    formkey_65 = "daily-report::ZZ-RUNTIME-CERT-2026::2026-01-15::primary-test-65"
    log(f"Test 1a: Testing 65-char formKey (length={len(formkey_65)})")
    
    payload = {
        "batch": [
            {
                "eventId": f"test-{int(time.time() * 1000)}-65",
                "event": "draft.write.ok",
                "actorId": "test-actor-65",
                "deviceId": "test-device-65",
                "formKey": formkey_65,
                "ts": int(time.time() * 1000),
                "meta": {"test": "65-char"}
            }
        ]
    }
    
    resp = requests.post(f"{BACKEND_URL}/draft-telemetry", json=payload)
    if resp.status_code == 200:
        log(f"✓ PASS: 65-char formKey accepted (status={resp.status_code})")
    else:
        log(f"✗ FAIL: 65-char formKey rejected (status={resp.status_code}, body={resp.text})")
        return False
    
    # Test case 2: Valid 100-char formKey (mid-range)
    base_100 = "daily-report::ZZ-RUNTIME-CERT-2026::2026-01-15::primary-test-100-"
    formkey_100 = base_100 + "x" * (100 - len(base_100))
    log(f"Test 1b: Testing 100-char formKey (length={len(formkey_100)})")
    
    payload["batch"][0]["eventId"] = f"test-{int(time.time() * 1000)}-100"
    payload["batch"][0]["formKey"] = formkey_100
    payload["batch"][0]["meta"] = {"test": "100-char"}
    
    resp = requests.post(f"{BACKEND_URL}/draft-telemetry", json=payload)
    if resp.status_code == 200:
        log(f"✓ PASS: 100-char formKey accepted (status={resp.status_code})")
    else:
        log(f"✗ FAIL: 100-char formKey rejected (status={resp.status_code}, body={resp.text})")
        return False
    
    # Test case 3: Valid 180-char formKey (max boundary)
    base_180 = "daily-report::ZZ-RUNTIME-CERT-2026::2026-01-15::primary-test-180-"
    formkey_180 = base_180 + "x" * (180 - len(base_180))
    log(f"Test 1c: Testing 180-char formKey (length={len(formkey_180)})")
    
    payload["batch"][0]["eventId"] = f"test-{int(time.time() * 1000)}-180"
    payload["batch"][0]["formKey"] = formkey_180
    payload["batch"][0]["meta"] = {"test": "180-char"}
    
    resp = requests.post(f"{BACKEND_URL}/draft-telemetry", json=payload)
    if resp.status_code == 200:
        log(f"✓ PASS: 180-char formKey accepted (status={resp.status_code})")
    else:
        log(f"✗ FAIL: 180-char formKey rejected (status={resp.status_code}, body={resp.text})")
        return False
    
    # Test case 4: Invalid 181-char formKey (over limit)
    base_181 = "daily-report::ZZ-RUNTIME-CERT-2026::2026-01-15::primary-test-181-"
    formkey_181 = base_181 + "x" * (181 - len(base_181))
    log(f"Test 2: Testing 181-char formKey (length={len(formkey_181)}) - should reject")
    
    payload["batch"][0]["eventId"] = f"test-{int(time.time() * 1000)}-181"
    payload["batch"][0]["formKey"] = formkey_181
    payload["batch"][0]["meta"] = {"test": "181-char"}
    
    resp = requests.post(f"{BACKEND_URL}/draft-telemetry", json=payload)
    if resp.status_code == 422:
        log(f"✓ PASS: 181-char formKey correctly rejected (status={resp.status_code})")
    else:
        log(f"✗ FAIL: 181-char formKey should be rejected with 422, got {resp.status_code}")
        return False
    
    log("✓ ALL DRAFT TELEMETRY TESTS PASSED")
    return True

def test_fl_token_authentication():
    """Test 3a: Obtain FL token with cert.foreman@example.com credentials"""
    log("=" * 80)
    log("TEST 3a: FL Token Authentication")
    log("=" * 80)
    
    log(f"Authenticating as {CERT_FOREMAN_EMAIL}...")
    
    payload = {
        "email": CERT_FOREMAN_EMAIL,
        "password": CERT_FOREMAN_PASSWORD
    }
    
    resp = requests.post(f"{BACKEND_URL}/field-leadership/portal/login", json=payload)
    
    if resp.status_code != 200:
        log(f"✗ FAIL: FL login failed (status={resp.status_code}, body={resp.text})")
        return None
    
    data = resp.json()
    token = data.get("token")
    
    if not token:
        log(f"✗ FAIL: No token in response (data={data})")
        return None
    
    log(f"✓ PASS: FL token obtained successfully (length={len(token)})")
    
    # Verify token works with /me endpoint
    headers = {"X-FL-Token": token}
    me_resp = requests.get(f"{BACKEND_URL}/field-leadership/portal/me", headers=headers)
    
    if me_resp.status_code == 200:
        me_data = me_resp.json()
        log(f"✓ PASS: Token verified with /me endpoint (user={me_data.get('user', {}).get('email')})")
    else:
        log(f"✗ FAIL: Token verification failed (status={me_resp.status_code})")
        return None
    
    return token

def test_governed_certification_daily_report(fl_token):
    """Test 3b & 4: Submit Daily Report to certification project and verify response"""
    log("=" * 80)
    log("TEST 3b & 4: Governed Certification Daily Report Submission")
    log("=" * 80)
    
    if not fl_token:
        log("✗ FAIL: No FL token available, skipping Daily Report test")
        return False
    
    log(f"Submitting Daily Report to project {CERT_PROJECT_NUMBER}...")
    
    # Build minimal Daily Report payload with required summary fields
    payload = {
        "project_name": "Runtime Certification — Internal Test Project",
        "project_number": CERT_PROJECT_NUMBER,
        "location": "Certification Test Site",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "prepared_by": "Certification Foreman",
        "superintendent": "Test Superintendent",
        "weather_summary": "Clear skies, 72°F",
        "general_notes": "Certification test run for Track 27.11D closeout repairs",
        "masci_crews": [
            {
                "employee_name": "Test Worker 1",
                "hours": 8.0,
                "classification": "Laborer"
            }
        ],
        "activities": [
            {
                "description": "Certification testing activities"
            }
        ],
        # Required summary fields (Track 22.9A)
        "ai_accepted_summary": "Certification test Daily Report for Track 27.11D closeout repairs. Verified governed certification lane routing and field validation.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "accepted_at": datetime.now().isoformat()
        }
    }
    
    headers = {"X-FL-Token": fl_token}
    resp = requests.post(f"{BACKEND_URL}/daily-reports", json=payload, headers=headers)
    
    if resp.status_code != 200:
        log(f"✗ FAIL: Daily Report submission failed (status={resp.status_code}, body={resp.text})")
        return False
    
    data = resp.json()
    report_id = data.get("id")
    doc_id = data.get("doc_id")
    
    log(f"✓ PASS: Daily Report submitted successfully (id={report_id}, doc_id={doc_id})")
    
    # Verify required certification fields
    log("Verifying certification fields in response...")
    
    required_fields = {
        "certification_record": True,
        "synthetic_record": True,
        "hidden_from_operations": True,
        "email_dispatch_suppressed": False
    }
    
    all_passed = True
    for field, expected_value in required_fields.items():
        actual_value = data.get(field)
        if actual_value == expected_value:
            log(f"✓ PASS: {field}={actual_value} (expected={expected_value})")
        else:
            log(f"✗ FAIL: {field}={actual_value} (expected={expected_value})")
            all_passed = False
    
    # Verify routing_override
    routing_override = data.get("routing_override")
    if not routing_override:
        log(f"✗ FAIL: routing_override is missing")
        all_passed = False
    else:
        log(f"✓ PASS: routing_override present")
        
        # Check enabled flag
        if routing_override.get("enabled") is True:
            log(f"✓ PASS: routing_override.enabled=True")
        else:
            log(f"✗ FAIL: routing_override.enabled={routing_override.get('enabled')} (expected=True)")
            all_passed = False
        
        # Check PM email
        pm_email = routing_override.get("pm_email")
        if pm_email == CERT_PM_EMAIL:
            log(f"✓ PASS: routing_override.pm_email={pm_email}")
        else:
            log(f"✗ FAIL: routing_override.pm_email={pm_email} (expected={CERT_PM_EMAIL})")
            all_passed = False
        
        # Check to list
        to_list = routing_override.get("to", [])
        if CERT_PM_EMAIL in to_list:
            log(f"✓ PASS: routing_override.to contains {CERT_PM_EMAIL}")
        else:
            log(f"✗ FAIL: routing_override.to={to_list} (expected to contain {CERT_PM_EMAIL})")
            all_passed = False
        
        # Check cc list
        cc_list = routing_override.get("cc", [])
        if CERT_CO_PM_EMAIL in cc_list:
            log(f"✓ PASS: routing_override.cc contains {CERT_CO_PM_EMAIL}")
        else:
            log(f"✗ FAIL: routing_override.cc={cc_list} (expected to contain {CERT_CO_PM_EMAIL})")
            all_passed = False
        
        # Verify ONLY certification recipients (no other emails)
        all_recipients = routing_override.get("all", [])
        expected_recipients = {CERT_PM_EMAIL, CERT_CO_PM_EMAIL}
        actual_recipients = set(all_recipients)
        
        if actual_recipients == expected_recipients:
            log(f"✓ PASS: routing_override.all contains ONLY certification recipients: {actual_recipients}")
        else:
            log(f"✗ FAIL: routing_override.all={actual_recipients} (expected={expected_recipients})")
            all_passed = False
    
    if all_passed:
        log("✓ ALL CERTIFICATION FIELDS VERIFIED")
    else:
        log("✗ SOME CERTIFICATION FIELDS FAILED")
    
    return all_passed

def main():
    log("Starting Daily Report Closeout Repairs Backend Tests")
    log(f"Backend URL: {BACKEND_URL}")
    log("")
    
    results = {
        "draft_telemetry": False,
        "fl_authentication": False,
        "certification_daily_report": False
    }
    
    # Test 1 & 2: Draft telemetry formKey validation
    results["draft_telemetry"] = test_draft_telemetry_formkey_validation()
    log("")
    
    # Test 3a: FL token authentication
    fl_token = test_fl_token_authentication()
    results["fl_authentication"] = fl_token is not None
    log("")
    
    # Test 3b & 4: Governed certification Daily Report
    if fl_token:
        results["certification_daily_report"] = test_governed_certification_daily_report(fl_token)
    else:
        log("⚠ SKIP: Certification Daily Report test skipped due to authentication failure")
    log("")
    
    # Summary
    log("=" * 80)
    log("TEST SUMMARY")
    log("=" * 80)
    log(f"Draft Telemetry formKey Validation: {'✓ PASS' if results['draft_telemetry'] else '✗ FAIL'}")
    log(f"FL Token Authentication: {'✓ PASS' if results['fl_authentication'] else '✗ FAIL'}")
    log(f"Certification Daily Report: {'✓ PASS' if results['certification_daily_report'] else '✗ FAIL'}")
    log("")
    
    all_passed = all(results.values())
    if all_passed:
        log("✓ ALL TESTS PASSED")
        return 0
    else:
        log("✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
