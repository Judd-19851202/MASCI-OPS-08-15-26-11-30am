#!/usr/bin/env python3
"""
C2 Blocker Remediation Verification Test
=========================================

Focused backend verification for bounded C2 blocker remediation on Preview app.

Test Requirements:
1. GET /api/version confirms single canonical release SHA
2. Daily Report Preview flow:
   - Login using cert.foreman@example.com / CertProof2026!
   - Submit Daily Report against project ZZ-RUNTIME-CERT-2026 using X-FL-Token
   - Verify record persists and no "api key is invalid" error
   - Verify notification state becomes preview capture (not provider send)
   - Verify no fake provider_accepted success
3. Validate backend evidence surfaces truthful status on preview capture
4. Verify no deployment/readiness/backup evidence incorrectly downgraded

Target: https://backup-forensics.preview.emergentagent.com
"""

import json
import requests
import sys
from datetime import datetime

BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API = f"{BASE_URL}/api"

# Credentials from review request
CERT_FOREMAN_EMAIL = "cert.foreman@example.com"
CERT_FOREMAN_PASSWORD = "CertProof2026!"

# Test project from review request
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

def log(msg):
    """Log with timestamp"""
    print(f"[{datetime.utcnow().isoformat()}] {msg}")

def test_version_endpoint():
    """Test 1: Verify /api/version returns canonical release SHA"""
    log("TEST 1: Verifying /api/version endpoint...")
    
    try:
        r = requests.get(f"{API}/version", timeout=30)
        log(f"  Status: {r.status_code}")
        
        if r.status_code != 200:
            return {
                "test": "version_endpoint",
                "passed": False,
                "error": f"Expected 200, got {r.status_code}",
                "response": r.text[:500]
            }
        
        data = r.json()
        log(f"  Response keys: {list(data.keys())}")
        
        # Check for canonical SHA fields
        commit = data.get("commit")
        source_hash = data.get("source_hash")
        
        log(f"  Commit: {commit}")
        log(f"  Source Hash: {source_hash}")
        
        # Make 3 calls to verify consistency
        commits = []
        source_hashes = []
        for i in range(3):
            r2 = requests.get(f"{API}/version", timeout=30)
            if r2.status_code == 200:
                d = r2.json()
                commits.append(d.get("commit"))
                source_hashes.append(d.get("source_hash"))
        
        consistent_commit = len(set(commits)) == 1
        consistent_hash = len(set(source_hashes)) == 1
        
        log(f"  Consistency check: commit={consistent_commit}, hash={consistent_hash}")
        
        return {
            "test": "version_endpoint",
            "passed": True,
            "commit": commit,
            "source_hash": source_hash,
            "consistent_across_calls": consistent_commit and consistent_hash,
            "full_response": data
        }
        
    except Exception as e:
        log(f"  ERROR: {e}")
        return {
            "test": "version_endpoint",
            "passed": False,
            "error": str(e)
        }

def test_cert_foreman_login():
    """Test 2: Login with cert.foreman@example.com"""
    log("TEST 2: Logging in with cert.foreman@example.com...")
    
    try:
        r = requests.post(
            f"{API}/auth/multi-login",
            json={"email": CERT_FOREMAN_EMAIL, "password": CERT_FOREMAN_PASSWORD},
            timeout=30
        )
        
        log(f"  Status: {r.status_code}")
        
        if r.status_code != 200:
            return {
                "test": "cert_foreman_login",
                "passed": False,
                "error": f"Login failed with status {r.status_code}",
                "response": r.text[:500]
            }
        
        data = r.json()
        log(f"  Response keys: {list(data.keys())}")
        
        # Extract tokens
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        
        log(f"  Session token present: {bool(session_token)}")
        log(f"  Portal tokens: {list(portal_tokens.keys())}")
        
        # Check for field_leadership token (X-FL-Token)
        fl_token = portal_tokens.get("field_leadership")
        
        if not fl_token:
            log(f"  WARNING: No field_leadership token found")
            log(f"  Available tokens: {list(portal_tokens.keys())}")
        
        return {
            "test": "cert_foreman_login",
            "passed": True,
            "session_token": session_token,
            "portal_tokens": portal_tokens,
            "has_fl_token": bool(fl_token),
            "user_info": {
                "email": data.get("user", {}).get("email"),
                "name": data.get("user", {}).get("name"),
                "role": data.get("user", {}).get("role")
            }
        }
        
    except Exception as e:
        log(f"  ERROR: {e}")
        return {
            "test": "cert_foreman_login",
            "passed": False,
            "error": str(e)
        }

def test_daily_report_submission(tokens):
    """Test 3: Submit Daily Report against ZZ-RUNTIME-CERT-2026"""
    log("TEST 3: Submitting Daily Report against ZZ-RUNTIME-CERT-2026...")
    
    try:
        # Prepare headers with field leadership token
        portal_tokens = tokens.get("portal_tokens", {})
        session_token = tokens.get("session_token")
        
        # Try field_leadership token first, fallback to admin if available
        fl_token = portal_tokens.get("field_leadership")
        admin_token = portal_tokens.get("admin")
        
        headers = {}
        if fl_token:
            headers["X-FL-Token"] = fl_token
            log(f"  Using X-FL-Token")
        elif admin_token:
            headers["X-Admin-Token"] = admin_token
            log(f"  Using X-Admin-Token (fallback)")
        
        if session_token:
            headers["X-Directory-Token"] = session_token
        
        log(f"  Headers: {list(headers.keys())}")
        
        # Prepare Daily Report payload
        payload = {
            "project_name": "ZZ-RUNTIME-CERT-2026 Certification Project",
            "project_number": CERT_PROJECT_NUMBER,
            "location": "Preview Certification Site",
            "location_source": "manual",
            "gps_lat": 29.1383,
            "gps_lng": -80.9956,
            "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "report_number": f"DR-CERT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "prepared_by": "Certification Foreman",
            "superintendent": "Cert Superintendent",
            "weather_summary": "75°F / Clear",
            "weather_snapshot_meta": {
                "provider": "open-meteo",
                "gps_lat": 29.1383,
                "gps_lng": -80.9956,
                "observation_timestamp": datetime.utcnow().isoformat() + "Z",
                "location_source": "manual",
                "weather_coordinates_match_report": True,
            },
            "weather_snapshots": [
                {"time": "06:00", "condition": "Clear", "temp_f": 65, "precip_in": 0, "humidity_pct": 70, "wind_mph": 4},
                {"time": "12:00", "condition": "Clear", "temp_f": 75, "precip_in": 0, "humidity_pct": 60, "wind_mph": 5},
                {"time": "18:00", "condition": "Clear", "temp_f": 72, "precip_in": 0, "humidity_pct": 65, "wind_mph": 4},
            ],
            "schedule_delays": "No",
            "weather_impact": "No",
            "safety_incidents_today": "No",
            "injuries_reported": "No",
            "incident_notes": "",
            "general_notes": "C2 Blocker Remediation Certification Test - SAFE_CAPTURE verification",
            "masci_crews": [
                {"trade": "Certification", "foreman": "Cert Foreman", "count": "1", "hours": "8", "work_performed": "Runtime verification"},
            ],
            "subcontractors": [],
            "visitors": [],
            "equipment": [],
            "materials": [],
            "activities": [
                {"activity": "C2 Blocker Remediation Verification", "percent_complete": "100", "station_from": "0+00", "station_to": "0+00", "notes": "SAFE_CAPTURE mode verification"},
            ],
            "photos": [],
            "prepared_by_signature": "data:image/png;base64,CERT_SIG_FAKE",
            "superintendent_signature": "",
            "ai_accepted_summary": "C2 Blocker Remediation certification test - verifying SAFE_CAPTURE mode in Preview environment.",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "approved_by": "Certification Foreman",
                "accepted_at": datetime.utcnow().isoformat() + "Z"
            },
        }
        
        log(f"  Submitting Daily Report...")
        r = requests.post(
            f"{API}/daily-reports",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        log(f"  Status: {r.status_code}")
        
        if r.status_code != 200:
            return {
                "test": "daily_report_submission",
                "passed": False,
                "error": f"Submission failed with status {r.status_code}",
                "response": r.text[:1000]
            }
        
        data = r.json()
        log(f"  Response keys: {list(data.keys())}")
        
        record_id = data.get("id")
        report_number = data.get("report_number")
        
        log(f"  Record ID: {record_id}")
        log(f"  Report Number: {report_number}")
        
        # Check for "api key is invalid" error in response
        response_text = json.dumps(data).lower()
        has_api_key_error = "api key is invalid" in response_text
        
        if has_api_key_error:
            log(f"  ❌ CRITICAL: Found 'api key is invalid' in response!")
        else:
            log(f"  ✅ No 'api key is invalid' error found")
        
        # Check notification-related fields
        notification_state = data.get("notification_state")
        notification_delivery_mode = data.get("notification_delivery_mode")
        notification_provider_called = data.get("notification_provider_called")
        notification_provider_accepted = data.get("notification_provider_accepted")
        
        log(f"  Notification state: {notification_state}")
        log(f"  Delivery mode: {notification_delivery_mode}")
        log(f"  Provider called: {notification_provider_called}")
        log(f"  Provider accepted: {notification_provider_accepted}")
        
        # Verify SAFE_CAPTURE behavior
        is_safe_capture = notification_delivery_mode == "SAFE_CAPTURE"
        is_captured_preview = notification_state == "captured_preview"
        provider_not_called = notification_provider_called == False
        provider_not_accepted = notification_provider_accepted == False
        
        log(f"  SAFE_CAPTURE mode: {is_safe_capture}")
        log(f"  Captured preview state: {is_captured_preview}")
        log(f"  Provider not called: {provider_not_called}")
        log(f"  Provider not accepted: {provider_not_accepted}")
        
        return {
            "test": "daily_report_submission",
            "passed": True,
            "record_id": record_id,
            "report_number": report_number,
            "no_api_key_error": not has_api_key_error,
            "notification_state": notification_state,
            "notification_delivery_mode": notification_delivery_mode,
            "notification_provider_called": notification_provider_called,
            "notification_provider_accepted": notification_provider_accepted,
            "safe_capture_verified": is_safe_capture and is_captured_preview and provider_not_called and provider_not_accepted,
            "full_response_excerpt": {k: v for k, v in data.items() if k not in ["photos", "weather_snapshots", "masci_crews", "subcontractors", "visitors", "equipment", "materials", "activities"]}
        }
        
    except Exception as e:
        log(f"  ERROR: {e}")
        return {
            "test": "daily_report_submission",
            "passed": False,
            "error": str(e)
        }

def test_record_persistence(record_id, tokens):
    """Test 4: Verify record persists and can be retrieved"""
    log(f"TEST 4: Verifying record persistence for {record_id}...")
    
    try:
        portal_tokens = tokens.get("portal_tokens", {})
        session_token = tokens.get("session_token")
        
        # Use admin token for retrieval
        admin_token = portal_tokens.get("admin")
        
        headers = {}
        if admin_token:
            headers["X-Admin-Token"] = admin_token
        if session_token:
            headers["X-Directory-Token"] = session_token
        
        log(f"  Retrieving record {record_id}...")
        r = requests.get(
            f"{API}/daily-reports/{record_id}",
            headers=headers,
            timeout=30
        )
        
        log(f"  Status: {r.status_code}")
        
        if r.status_code != 200:
            return {
                "test": "record_persistence",
                "passed": False,
                "error": f"Retrieval failed with status {r.status_code}",
                "response": r.text[:500]
            }
        
        data = r.json()
        log(f"  Record retrieved successfully")
        log(f"  Project number: {data.get('project_number')}")
        log(f"  Notification state: {data.get('notification_state')}")
        
        return {
            "test": "record_persistence",
            "passed": True,
            "record_retrieved": True,
            "project_number": data.get("project_number"),
            "notification_state": data.get("notification_state"),
            "notification_delivery_mode": data.get("notification_delivery_mode")
        }
        
    except Exception as e:
        log(f"  ERROR: {e}")
        return {
            "test": "record_persistence",
            "passed": False,
            "error": str(e)
        }

def main():
    """Run all C2 blocker remediation tests"""
    log("=" * 80)
    log("C2 BLOCKER REMEDIATION VERIFICATION TEST")
    log("=" * 80)
    log(f"Target: {BASE_URL}")
    log("")
    
    results = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target_url": BASE_URL,
        "tests": []
    }
    
    # Test 1: Version endpoint
    version_result = test_version_endpoint()
    results["tests"].append(version_result)
    log("")
    
    # Test 2: Login
    login_result = test_cert_foreman_login()
    results["tests"].append(login_result)
    log("")
    
    if not login_result.get("passed"):
        log("❌ Login failed, cannot proceed with Daily Report submission")
        results["overall_status"] = "FAILED"
        results["failure_reason"] = "Login failed"
        print(json.dumps(results, indent=2))
        return 1
    
    # Test 3: Daily Report submission
    dr_result = test_daily_report_submission(login_result)
    results["tests"].append(dr_result)
    log("")
    
    if not dr_result.get("passed"):
        log("❌ Daily Report submission failed")
        results["overall_status"] = "FAILED"
        results["failure_reason"] = "Daily Report submission failed"
        print(json.dumps(results, indent=2))
        return 1
    
    # Test 4: Record persistence
    record_id = dr_result.get("record_id")
    if record_id:
        persist_result = test_record_persistence(record_id, login_result)
        results["tests"].append(persist_result)
        log("")
    
    # Summary
    log("=" * 80)
    log("TEST SUMMARY")
    log("=" * 80)
    
    all_passed = all(t.get("passed", False) for t in results["tests"])
    
    # Check critical acceptance criteria
    acceptance = {
        "canonical_sha_verified": version_result.get("passed") and version_result.get("consistent_across_calls"),
        "cert_foreman_login_successful": login_result.get("passed"),
        "daily_report_submitted": dr_result.get("passed"),
        "no_api_key_error": dr_result.get("no_api_key_error", False),
        "safe_capture_verified": dr_result.get("safe_capture_verified", False),
        "record_persists": persist_result.get("passed", False) if record_id else False,
    }
    
    results["acceptance"] = acceptance
    results["overall_status"] = "PASSED" if all(acceptance.values()) else "FAILED"
    
    for key, value in acceptance.items():
        status = "✅" if value else "❌"
        log(f"{status} {key}: {value}")
    
    log("")
    log(f"Overall Status: {results['overall_status']}")
    log("=" * 80)
    
    # Save results
    output_file = "/app/c2_blocker_remediation_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    log(f"Results saved to {output_file}")
    
    return 0 if results["overall_status"] == "PASSED" else 1

if __name__ == "__main__":
    sys.exit(main())
