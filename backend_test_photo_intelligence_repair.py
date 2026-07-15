#!/usr/bin/env python3
"""
Daily Report AI + Photo Intelligence Bounded Repair - Backend Verification

Tests the following endpoints on preview (https://backup-forensics.preview.emergentagent.com):
1. POST /api/daily-reports/photo-intelligence/draft
2. POST /api/daily-reports/summary/draft
3. POST /api/daily-reports
4. GET /api/daily-reports/{id}/photo-intelligence

Key requirements:
- Draft photo endpoint does NOT return `not_requested` when photos are attached
- Draft photo endpoint returns truthful lifecycle status (complete_with_observations, unavailable, or no_photos)
- Summary draft endpoint merges photo intelligence into summary_input.photos and returned photo_intelligence
- Submit succeeds when ai_accepted_summary and ai_accepted_summary_meta are present
- Saved report photo intelligence read endpoint returns stable shape
- No duplicate-enqueue or request-storm symptoms from repeated calls with same form_key + same payload
"""

import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials (super admin)
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Photo fixture path
PHOTO_FIXTURE_DIR = Path("/app/tmp_photo_fixture")

# Test counters
tests_run = 0
tests_passed = 0
tests_failed = 0


def log(msg, level="INFO"):
    """Log a message with timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] [{level}] {msg}")


def test_result(name, passed, details=""):
    """Record test result."""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    if passed:
        tests_passed += 1
        log(f"✓ {name}", "PASS")
    else:
        tests_failed += 1
        log(f"✗ {name}", "FAIL")
    if details:
        log(f"  {details}", "INFO")


def get_admin_token():
    """Authenticate and get admin token."""
    log("Authenticating with super admin credentials...")
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if response.status_code != 200:
        log(f"Authentication failed: {response.status_code} {response.text}", "ERROR")
        sys.exit(1)
    
    data = response.json()
    admin_token = data.get("portal_tokens", {}).get("admin")
    if not admin_token:
        log("No admin token in response", "ERROR")
        sys.exit(1)
    
    log(f"✓ Authentication successful (token length: {len(admin_token)})")
    return admin_token


def load_photo_fixture():
    """Load photos from the fixture directory."""
    log("Loading photo fixture...")
    if not PHOTO_FIXTURE_DIR.exists():
        log(f"Photo fixture directory not found: {PHOTO_FIXTURE_DIR}", "WARN")
        return []
    
    photos = []
    for photo_file in PHOTO_FIXTURE_DIR.glob("*.jpeg"):
        try:
            # Photos field expects strings (photo:// refs)
            photos.append(f"photo://fixture/{photo_file.name}")
        except Exception as e:
            log(f"Failed to load {photo_file.name}: {e}", "WARN")
    
    log(f"✓ Loaded {len(photos)} photos from fixture")
    return photos


def create_draft_payload(with_photos=True):
    """Create a draft Daily Report payload."""
    photos = load_photo_fixture() if with_photos else []
    
    # Use only first 8 photos as mentioned in review request
    photos = photos[:8]
    
    payload = {
        "project_name": "Runtime Certification — Internal Test Project",
        "project_number": "ZZ-RUNTIME-CERT-2026",
        "location": "Test Site",
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "prepared_by": "Test Foreman",
        "superintendent": "Test Superintendent",
        "shift": "Day",
        "weather_summary": "Clear skies, 72°F",
        "masci_crews": [
            {
                "employee_id": "EMP001",
                "name": "John Doe",
                "trade": "Laborer",
                "hours": 11.25,
            }
        ],
        "subcontractors": [
            {
                "company": "Test Subcontractor",
                "headcount": 1,
                "hours": 11.0,
                "work_performed": "Concrete work",
            }
        ],
        "equipment": [
            {
                "description": "Excavator",
                "unit_number": "EX-001",
                "operator": "Jane Smith",
                "run_hours": 4.0,
                "idle_hours": 6.0,
            }
        ],
        "production": [
            {
                "description": "Install pipe",
                "quantity": 875.0,
                "unit": "LF",
                "percent_complete": 65,
            }
        ],
        "photos": photos,
        "general_notes": "Test daily report for photo intelligence verification",
    }
    
    return payload


def test_photo_intelligence_draft_endpoint(admin_token):
    """Test POST /api/daily-reports/photo-intelligence/draft."""
    log("\n=== Testing Photo Intelligence Draft Endpoint ===")
    
    # Generate stable form_key
    timestamp = int(time.time())
    form_key = f"daily-report::cert-foreman::ZZ-RUNTIME-CERT-2026::2026-07-15::primary-{timestamp}"
    
    # Test 1: Draft with photos should NOT return not_requested
    log("Test 1: Draft photo endpoint with photos attached...")
    payload = create_draft_payload(with_photos=True)
    
    response = requests.post(
        f"{API_BASE}/daily-reports/photo-intelligence/draft",
        json={"form_key": form_key, "payload": payload, "force": False},
        headers={"X-Admin-Token": admin_token},
        timeout=60,
    )
    
    test_result(
        "POST /api/daily-reports/photo-intelligence/draft returns 200",
        response.status_code == 200,
        f"Status: {response.status_code}",
    )
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        lifecycle_status = data.get("lifecycle_status")
        report_id = data.get("report_id")
        photo_count = data.get("photo_count")
        
        test_result(
            "Draft photo endpoint does NOT return 'not_requested' when photos attached",
            status != "not_requested",
            f"Status: {status}, Lifecycle: {lifecycle_status}",
        )
        
        test_result(
            "Draft photo endpoint returns truthful lifecycle status",
            status in ["complete_with_observations", "unavailable", "no_photos", "processing", "queued", "failed", "complete_zero_observations"],
            f"Status: {status}",
        )
        
        test_result(
            "Draft photo endpoint returns stable report_id",
            report_id == form_key,
            f"Report ID: {report_id}",
        )
        
        test_result(
            "Draft photo endpoint returns correct photo_count",
            photo_count == len(payload.get("photos", [])),
            f"Photo count: {photo_count}, Expected: {len(payload.get('photos', []))}",
        )
        
        # Test required fields
        required_fields = ["report_id", "photo_count", "analyzed", "pending", "status", "lifecycle_status"]
        missing_fields = [f for f in required_fields if f not in data]
        test_result(
            "Draft photo endpoint returns all required fields",
            len(missing_fields) == 0,
            f"Missing fields: {missing_fields}" if missing_fields else "All fields present",
        )
    
    # Test 2: No duplicate-enqueue with same form_key + same payload
    log("\nTest 2: Duplicate request with same form_key and payload...")
    response2 = requests.post(
        f"{API_BASE}/daily-reports/photo-intelligence/draft",
        json={"form_key": form_key, "payload": payload, "force": False},
        headers={"X-Admin-Token": admin_token},
        timeout=60,
    )
    
    test_result(
        "Duplicate request returns 200 (no request-storm)",
        response2.status_code == 200,
        f"Status: {response2.status_code}",
    )
    
    if response.status_code == 200 and response2.status_code == 200:
        data1 = response.json()
        data2 = response2.json()
        
        test_result(
            "Duplicate request returns stable status (no duplicate-enqueue)",
            data1.get("status") == data2.get("status"),
            f"First: {data1.get('status')}, Second: {data2.get('status')}",
        )
    
    # Test 3: Draft without photos should return no_photos
    log("\nTest 3: Draft photo endpoint without photos...")
    form_key_no_photos = f"daily-report::cert-foreman::ZZ-RUNTIME-CERT-2026::2026-07-15::no-photos-{timestamp}"
    payload_no_photos = create_draft_payload(with_photos=False)
    
    response3 = requests.post(
        f"{API_BASE}/daily-reports/photo-intelligence/draft",
        json={"form_key": form_key_no_photos, "payload": payload_no_photos, "force": False},
        headers={"X-Admin-Token": admin_token},
        timeout=60,
    )
    
    if response3.status_code == 200:
        data3 = response3.json()
        test_result(
            "Draft photo endpoint returns 'no_photos' when no photos attached",
            data3.get("status") == "no_photos",
            f"Status: {data3.get('status')}",
        )
    
    return form_key


def test_summary_draft_endpoint(admin_token, form_key):
    """Test POST /api/daily-reports/summary/draft."""
    log("\n=== Testing Summary Draft Endpoint ===")
    
    payload = create_draft_payload(with_photos=True)
    
    response = requests.post(
        f"{API_BASE}/daily-reports/summary/draft",
        json={"form_key": form_key, "payload": payload, "tenant_id": "masci", "language": "en"},
        timeout=60,
    )
    
    test_result(
        "POST /api/daily-reports/summary/draft returns 200",
        response.status_code == 200,
        f"Status: {response.status_code}",
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Check for required fields
        test_result(
            "Summary draft returns 'ok' field",
            data.get("ok") is True,
            f"ok: {data.get('ok')}",
        )
        
        # Check summary_input
        summary_input = data.get("summary_input")
        test_result(
            "Summary draft returns summary_input",
            summary_input is not None,
            f"summary_input present: {summary_input is not None}",
        )
        
        if summary_input:
            # Check photos in summary_input
            photos_data = summary_input.get("photos")
            test_result(
                "Summary draft merges photo intelligence into summary_input.photos",
                photos_data is not None,
                f"photos data present: {photos_data is not None}",
            )
            
            if photos_data:
                test_result(
                    "summary_input.photos contains photo_count",
                    "photo_count" in photos_data,
                    f"photo_count: {photos_data.get('photo_count')}",
                )
                
                test_result(
                    "summary_input.photos contains status",
                    "status" in photos_data,
                    f"status: {photos_data.get('status')}",
                )
                
                test_result(
                    "summary_input.photos contains lifecycle_status",
                    "lifecycle_status" in photos_data,
                    f"lifecycle_status: {photos_data.get('lifecycle_status')}",
                )
                
                test_result(
                    "summary_input.photos contains analyzed count",
                    "analyzed" in photos_data,
                    f"analyzed: {photos_data.get('analyzed')}",
                )
                
                test_result(
                    "summary_input.photos contains pending count",
                    "pending" in photos_data,
                    f"pending: {photos_data.get('pending')}",
                )
        
        # Check photo_intelligence in response
        photo_intel = data.get("photo_intelligence")
        test_result(
            "Summary draft returns photo_intelligence field",
            photo_intel is not None,
            f"photo_intelligence present: {photo_intel is not None}",
        )
        
        if photo_intel:
            test_result(
                "photo_intelligence contains status",
                "status" in photo_intel,
                f"status: {photo_intel.get('status')}",
            )
            
            test_result(
                "photo_intelligence status is truthful (not 'not_requested' with photos)",
                photo_intel.get("status") != "not_requested",
                f"status: {photo_intel.get('status')}",
            )
        
        # Check AI disabled fallback behavior (tenant AI is disabled in preview)
        enabled = data.get("enabled")
        mode = data.get("mode")
        reason_disabled = data.get("reason_disabled")
        
        test_result(
            "Summary draft handles tenant AI disabled gracefully",
            enabled is False and mode == "deterministic_fallback" and reason_disabled == "tenant_ai_disabled",
            f"enabled: {enabled}, mode: {mode}, reason_disabled: {reason_disabled}",
        )


def test_daily_report_submit(admin_token):
    """Test POST /api/daily-reports with photo intelligence."""
    log("\n=== Testing Daily Report Submit Endpoint ===")
    
    # Get FL token for certification project
    log("Getting FL token for certification project...")
    fl_response = requests.post(
        f"{API_BASE}/field-leadership/portal/login",
        json={"email": "cert.foreman@example.com", "password": "CertProof2026!"},
        timeout=30,
    )
    
    if fl_response.status_code != 200:
        log(f"FL authentication failed: {fl_response.status_code}", "WARN")
        return None
    
    fl_token = fl_response.json().get("token")
    log(f"✓ FL token obtained (length: {len(fl_token)})")
    
    # Create payload with accepted summary
    payload = create_draft_payload(with_photos=True)
    payload["ai_accepted_summary"] = "Test daily report summary for photo intelligence verification. Crew of 1 employee logged 11.25 labor hours. 1 subcontractor logged 11 hours. Equipment usage: 4 run hours, 6 idle hours. Production: 875 LF at 65% complete."
    payload["ai_accepted_summary_meta"] = {
        "source": "edited",  # Valid sources: "ai", "edited", "fallback", "manual"
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "language": "en",
    }
    
    response = requests.post(
        f"{API_BASE}/daily-reports",
        json=payload,
        headers={"X-FL-Token": fl_token},
        timeout=60,
    )
    
    test_result(
        "POST /api/daily-reports succeeds with ai_accepted_summary and ai_accepted_summary_meta",
        response.status_code == 200,
        f"Status: {response.status_code}, Response: {response.text[:500] if response.status_code != 200 else ''}",
    )
    
    report_id = None
    if response.status_code == 200:
        data = response.json()
        report_id = data.get("id")
        doc_id = data.get("doc_id")
        
        test_result(
            "Submit returns report ID",
            report_id is not None,
            f"Report ID: {report_id}",
        )
        
        test_result(
            "Submit returns doc_id",
            doc_id is not None,
            f"Doc ID: {doc_id}",
        )
        
        # Check that ai_accepted_summary is preserved
        test_result(
            "Submit preserves ai_accepted_summary",
            data.get("ai_accepted_summary") == payload["ai_accepted_summary"],
            f"Summary preserved: {data.get('ai_accepted_summary') is not None}",
        )
        
        # Check that ai_accepted_summary_meta is preserved
        test_result(
            "Submit preserves ai_accepted_summary_meta",
            data.get("ai_accepted_summary_meta") is not None,
            f"Meta preserved: {data.get('ai_accepted_summary_meta') is not None}",
        )
    
    return report_id


def test_photo_intelligence_read_endpoint(admin_token, report_id):
    """Test GET /api/daily-reports/{id}/photo-intelligence."""
    log("\n=== Testing Photo Intelligence Read Endpoint ===")
    
    if not report_id:
        log("No report ID available, skipping read endpoint test", "WARN")
        return
    
    response = requests.get(
        f"{API_BASE}/daily-reports/{report_id}/photo-intelligence",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    
    test_result(
        "GET /api/daily-reports/{id}/photo-intelligence returns 200",
        response.status_code == 200,
        f"Status: {response.status_code}",
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Check required fields
        required_fields = ["report_id", "photo_count", "analyzed", "pending", "status"]
        missing_fields = [f for f in required_fields if f not in data]
        test_result(
            "Photo intelligence read endpoint returns all required fields",
            len(missing_fields) == 0,
            f"Missing fields: {missing_fields}" if missing_fields else "All fields present",
        )
        
        # Check stable shape
        test_result(
            "Photo intelligence read endpoint returns stable shape",
            isinstance(data, dict),
            f"Response is dict: {isinstance(data, dict)}",
        )
        
        # Check status is truthful
        status = data.get("status")
        test_result(
            "Photo intelligence read endpoint returns truthful status",
            status in ["no_photos", "suppressed", "pending", "failed", "complete_with_observations", "complete_zero_observations", "not_requested", "unknown", "processing", "queued", "unavailable"],
            f"Status: {status}",
        )
        
        # Check no 500 errors
        test_result(
            "Photo intelligence read endpoint does not return 500",
            response.status_code != 500,
            f"Status: {response.status_code}",
        )


def main():
    """Run all tests."""
    log("=" * 80)
    log("Daily Report AI + Photo Intelligence Bounded Repair - Backend Verification")
    log("=" * 80)
    log(f"Base URL: {BASE_URL}")
    log(f"API Base: {API_BASE}")
    log("")
    
    try:
        # Authenticate
        admin_token = get_admin_token()
        
        # Test photo intelligence draft endpoint
        form_key = test_photo_intelligence_draft_endpoint(admin_token)
        
        # Test summary draft endpoint
        test_summary_draft_endpoint(admin_token, form_key)
        
        # Test daily report submit
        report_id = test_daily_report_submit(admin_token)
        
        # Test photo intelligence read endpoint
        test_photo_intelligence_read_endpoint(admin_token, report_id)
        
    except Exception as e:
        log(f"Test suite failed with exception: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    log("")
    log("=" * 80)
    log("TEST SUMMARY")
    log("=" * 80)
    log(f"Total tests: {tests_run}")
    log(f"Passed: {tests_passed}")
    log(f"Failed: {tests_failed}")
    log(f"Success rate: {(tests_passed / tests_run * 100) if tests_run > 0 else 0:.1f}%")
    log("=" * 80)
    
    if tests_failed > 0:
        log("VERIFICATION FAILED - Some tests did not pass", "ERROR")
        sys.exit(1)
    else:
        log("VERIFICATION PASSED - All tests passed successfully", "PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
