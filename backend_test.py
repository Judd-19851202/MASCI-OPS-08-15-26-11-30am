"""
TRACK 27.10 Backend API Verification Test Suite

Tests the Daily Report V3 Summary Gate backend behavior on the live preview API.
Verifies:
1. Authentication via POST /api/auth/multi-login
2. POST /api/daily-reports validation gates (missing summary, missing metadata, invalid source)
3. Valid POST /api/daily-reports with frozen approved summary
4. GET /api/daily-reports/{id}/pdf returns valid PDF
5. GET /api/daily-reports/{id}/audit-footer works correctly
6. Saved record data integrity (weather_summary, weather_snapshot_meta, approved summary metadata)
"""

import requests
import json
from datetime import datetime, timezone

# Backend URL from frontend/.env
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "errors": []
}

def log_pass(test_name):
    """Log a passed test."""
    print(f"✅ PASS: {test_name}")
    test_results["passed"].append(test_name)

def log_fail(test_name, reason):
    """Log a failed test."""
    print(f"❌ FAIL: {test_name}")
    print(f"   Reason: {reason}")
    test_results["failed"].append({"test": test_name, "reason": reason})

def log_error(test_name, error):
    """Log a test error."""
    print(f"⚠️  ERROR: {test_name}")
    print(f"   Error: {error}")
    test_results["errors"].append({"test": test_name, "error": str(error)})

def authenticate():
    """Authenticate and return admin token."""
    print("\n" + "="*80)
    print("TEST 1: POST /api/auth/multi-login - Admin Authentication")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Get admin token from portal_tokens
            portal_tokens = data.get("portal_tokens", {})
            admin_token = portal_tokens.get("admin")
            if admin_token:
                log_pass("Admin authentication via POST /api/auth/multi-login")
                print(f"   Admin token obtained: {admin_token[:40]}...")
                return admin_token
            else:
                log_fail("Admin authentication", "No admin token in portal_tokens")
                return None
        else:
            log_fail("Admin authentication", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_error("Admin authentication", e)
        return None

def test_missing_approved_summary(admin_token):
    """Test that POST /api/daily-reports rejects missing approved summary."""
    print("\n" + "="*80)
    print("TEST 2: POST /api/daily-reports - Missing Approved Summary (422)")
    print("="*80)
    
    try:
        payload = {
            "project_name": "TRACK 27.10 Test Project",
            "project_number": "TRACK-27-10-TEST",
            "location": "Test Site Alpha",
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "prepared_by": "Test Supervisor",
            "superintendent": "John Smith",
            "weather_summary": "Clear skies, 72°F",
            "weather_snapshot_meta": {
                "source": "openweather",
                "captured_at": datetime.now(timezone.utc).isoformat()
            },
            "masci_crews": [{"name": "Crew A", "count": 5}],
            "activities": [{"description": "Excavation work"}],
            "general_notes": "Daily operations proceeding normally",
            # Missing ai_accepted_summary and ai_accepted_summary_meta
        }
        
        headers = {"X-Admin-Token": admin_token}
        response = requests.post(
            f"{BACKEND_URL}/daily-reports",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", {})
            error_code = detail.get("error") if isinstance(detail, dict) else None
            
            if error_code == "approved_summary_required":
                log_pass("POST /api/daily-reports rejects missing approved summary with 422 approved_summary_required")
                print(f"   Response: {json.dumps(detail, indent=2)}")
            else:
                log_fail("Missing approved summary validation", f"Expected error code 'approved_summary_required', got: {error_code}")
        else:
            log_fail("Missing approved summary validation", f"Expected 422, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("Missing approved summary validation", e)

def test_missing_accepted_at_metadata(admin_token):
    """Test that POST /api/daily-reports rejects missing accepted_at metadata."""
    print("\n" + "="*80)
    print("TEST 3: POST /api/daily-reports - Missing accepted_at Metadata (422)")
    print("="*80)
    
    try:
        payload = {
            "project_name": "TRACK 27.10 Test Project",
            "project_number": "TRACK-27-10-TEST",
            "location": "Test Site Beta",
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "prepared_by": "Test Supervisor",
            "superintendent": "John Smith",
            "weather_summary": "Partly cloudy, 68°F",
            "weather_snapshot_meta": {
                "source": "openweather",
                "captured_at": datetime.now(timezone.utc).isoformat()
            },
            "masci_crews": [{"name": "Crew B", "count": 4}],
            "activities": [{"description": "Paving operations"}],
            "general_notes": "Operations on schedule",
            "ai_accepted_summary": "Today's work included paving operations with Crew B.",
            "ai_accepted_summary_meta": {
                "source": "ai",
                # Missing accepted_at
            }
        }
        
        headers = {"X-Admin-Token": admin_token}
        response = requests.post(
            f"{BACKEND_URL}/daily-reports",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", {})
            error_code = detail.get("error") if isinstance(detail, dict) else None
            
            if error_code == "approved_summary_metadata_required":
                log_pass("POST /api/daily-reports rejects missing accepted_at metadata with 422")
                print(f"   Response: {json.dumps(detail, indent=2)}")
            else:
                log_fail("Missing accepted_at metadata validation", f"Expected error code 'approved_summary_metadata_required', got: {error_code}")
        else:
            log_fail("Missing accepted_at metadata validation", f"Expected 422, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("Missing accepted_at metadata validation", e)

def test_invalid_source_label(admin_token):
    """Test that POST /api/daily-reports rejects invalid source labels."""
    print("\n" + "="*80)
    print("TEST 4: POST /api/daily-reports - Invalid Source Label (422)")
    print("="*80)
    
    try:
        payload = {
            "project_name": "TRACK 27.10 Test Project",
            "project_number": "TRACK-27-10-TEST",
            "location": "Test Site Gamma",
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "prepared_by": "Test Supervisor",
            "superintendent": "John Smith",
            "weather_summary": "Overcast, 65°F",
            "weather_snapshot_meta": {
                "source": "openweather",
                "captured_at": datetime.now(timezone.utc).isoformat()
            },
            "masci_crews": [{"name": "Crew C", "count": 6}],
            "activities": [{"description": "Grading work"}],
            "general_notes": "Steady progress",
            "ai_accepted_summary": "Grading work completed by Crew C today.",
            "ai_accepted_summary_meta": {
                "source": "invalid_source",  # Invalid source
                "accepted_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        headers = {"X-Admin-Token": admin_token}
        response = requests.post(
            f"{BACKEND_URL}/daily-reports",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", {})
            error_code = detail.get("error") if isinstance(detail, dict) else None
            
            if error_code == "approved_summary_source_invalid":
                log_pass("POST /api/daily-reports rejects invalid source label with 422")
                print(f"   Response: {json.dumps(detail, indent=2)}")
            else:
                log_fail("Invalid source label validation", f"Expected error code 'approved_summary_source_invalid', got: {error_code}")
        else:
            log_fail("Invalid source label validation", f"Expected 422, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("Invalid source label validation", e)

def test_valid_daily_report_submission(admin_token):
    """Test valid POST /api/daily-reports with frozen approved summary."""
    print("\n" + "="*80)
    print("TEST 5: POST /api/daily-reports - Valid Submission with Approved Summary")
    print("="*80)
    
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "project_name": "TRACK 27.10 Test Project",
            "project_number": "TRACK-27-10-VALID",
            "location": "Test Site Delta",
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "prepared_by": "Test Supervisor Delta",
            "superintendent": "Jane Doe",
            "weather_summary": "Sunny and clear, 75°F with light breeze",
            "weather_snapshots": [
                {
                    "time": "08:00",
                    "temperature_f": 68,
                    "conditions": "Clear"
                },
                {
                    "time": "12:00",
                    "temperature_f": 75,
                    "conditions": "Sunny"
                }
            ],
            "weather_snapshot_meta": {
                "source": "openweather",
                "captured_at": now_iso,
                "api_version": "2.5"
            },
            "masci_crews": [
                {"name": "Crew Delta", "count": 8, "foreman": "Mike Johnson"}
            ],
            "activities": [
                {"description": "Concrete pouring for foundation", "hours": 6},
                {"description": "Rebar installation", "hours": 4}
            ],
            "general_notes": "All operations completed successfully. Weather conditions were ideal.",
            "ai_accepted_summary": "Today's operations focused on concrete foundation work. Crew Delta successfully completed concrete pouring and rebar installation. Weather conditions were ideal with sunny skies and temperatures reaching 75°F. All safety protocols were followed and no incidents occurred.",
            "ai_accepted_summary_meta": {
                "source": "ai",
                "accepted_at": now_iso,
                "provider": "openai",
                "model": "gpt-4",
                "accepted_by": "Test Supervisor Delta"
            }
        }
        
        headers = {"X-Admin-Token": admin_token}
        response = requests.post(
            f"{BACKEND_URL}/daily-reports",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            report_id = data.get("id")
            doc_id = data.get("doc_id")
            
            # Verify frozen fields are present
            saved_summary = data.get("ai_accepted_summary")
            saved_meta = data.get("ai_accepted_summary_meta")
            saved_weather_summary = data.get("weather_summary")
            saved_weather_meta = data.get("weather_snapshot_meta")
            
            checks = []
            if saved_summary == payload["ai_accepted_summary"]:
                checks.append("✓ ai_accepted_summary frozen correctly")
            else:
                checks.append("✗ ai_accepted_summary mismatch")
            
            if saved_meta and saved_meta.get("source") == "ai" and saved_meta.get("accepted_at"):
                checks.append("✓ ai_accepted_summary_meta frozen correctly")
            else:
                checks.append("✗ ai_accepted_summary_meta missing or incomplete")
            
            if saved_weather_summary == payload["weather_summary"]:
                checks.append("✓ weather_summary retained")
            else:
                checks.append("✗ weather_summary mismatch")
            
            if saved_weather_meta and saved_weather_meta.get("source") == "openweather":
                checks.append("✓ weather_snapshot_meta retained")
            else:
                checks.append("✗ weather_snapshot_meta missing or incomplete")
            
            all_passed = all("✓" in c for c in checks)
            
            if all_passed:
                log_pass("Valid POST /api/daily-reports succeeds with frozen approved summary and metadata")
                print(f"   Report ID: {report_id}")
                print(f"   Doc ID: {doc_id}")
                for check in checks:
                    print(f"   {check}")
                return report_id
            else:
                log_fail("Valid daily report submission", f"Data integrity checks failed: {checks}")
                return report_id
        else:
            log_fail("Valid daily report submission", f"Expected 200, got {response.status_code}: {response.text[:500]}")
            return None
    except Exception as e:
        log_error("Valid daily report submission", e)
        return None

def test_pdf_generation(admin_token, report_id):
    """Test GET /api/daily-reports/{id}/pdf returns valid PDF."""
    print("\n" + "="*80)
    print("TEST 6: GET /api/daily-reports/{id}/pdf - PDF Generation")
    print("="*80)
    
    if not report_id:
        log_fail("PDF generation", "No report_id available from previous test")
        return
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{BACKEND_URL}/daily-reports/{report_id}/pdf",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content_length = len(response.content)
            
            # Check if it's a valid PDF
            is_pdf = content_type == "application/pdf" or response.content[:4] == b"%PDF"
            
            if is_pdf and content_length > 1000:
                log_pass("GET /api/daily-reports/{id}/pdf returns valid PDF")
                print(f"   Content-Type: {content_type}")
                print(f"   PDF Size: {content_length} bytes")
                print(f"   PDF Header: {response.content[:20]}")
            else:
                log_fail("PDF generation", f"Invalid PDF: content_type={content_type}, size={content_length}")
        else:
            log_fail("PDF generation", f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("PDF generation", e)

def test_audit_footer(admin_token, report_id):
    """Test GET /api/daily-reports/{id}/audit-footer works correctly."""
    print("\n" + "="*80)
    print("TEST 7: GET /api/daily-reports/{id}/audit-footer - Audit Footer")
    print("="*80)
    
    if not report_id:
        log_fail("Audit footer", "No report_id available from previous test")
        return
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{BACKEND_URL}/daily-reports/{report_id}/audit-footer",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            has_report_id = data.get("report_id") == report_id
            has_doc_id = bool(data.get("doc_id"))
            has_sha256 = bool(data.get("sha256")) and len(data.get("sha256", "")) == 64
            has_rendered_at = bool(data.get("rendered_at_utc"))
            has_footer_text = bool(data.get("footer_text"))
            
            checks = [
                f"{'✓' if has_report_id else '✗'} report_id matches",
                f"{'✓' if has_doc_id else '✗'} doc_id present",
                f"{'✓' if has_sha256 else '✗'} sha256 hash present (64 chars)",
                f"{'✓' if has_rendered_at else '✗'} rendered_at_utc present",
                f"{'✓' if has_footer_text else '✗'} footer_text present"
            ]
            
            all_passed = all([has_report_id, has_doc_id, has_sha256, has_rendered_at, has_footer_text])
            
            if all_passed:
                log_pass("GET /api/daily-reports/{id}/audit-footer returns complete audit data")
                print(f"   Doc ID: {data.get('doc_id')}")
                print(f"   SHA256: {data.get('sha256')[:32]}...")
                print(f"   Rendered At: {data.get('rendered_at_utc')}")
                for check in checks:
                    print(f"   {check}")
            else:
                log_fail("Audit footer", f"Missing required fields: {checks}")
        else:
            log_fail("Audit footer", f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("Audit footer", e)

def test_saved_record_integrity(admin_token, report_id):
    """Test that saved record retains all required data."""
    print("\n" + "="*80)
    print("TEST 8: GET /api/daily-reports/{id} - Saved Record Data Integrity")
    print("="*80)
    
    if not report_id:
        log_fail("Saved record integrity", "No report_id available from previous test")
        return
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{BACKEND_URL}/daily-reports/{report_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all critical fields are retained
            checks = []
            
            # Check weather_summary
            if data.get("weather_summary"):
                checks.append("✓ weather_summary retained")
            else:
                checks.append("✗ weather_summary missing")
            
            # Check weather_snapshot_meta
            weather_meta = data.get("weather_snapshot_meta")
            if weather_meta and isinstance(weather_meta, dict) and weather_meta.get("source"):
                checks.append("✓ weather_snapshot_meta retained with source")
            else:
                checks.append("✗ weather_snapshot_meta missing or incomplete")
            
            # Check ai_accepted_summary
            if data.get("ai_accepted_summary"):
                checks.append("✓ ai_accepted_summary retained")
            else:
                checks.append("✗ ai_accepted_summary missing")
            
            # Check ai_accepted_summary_meta
            summary_meta = data.get("ai_accepted_summary_meta")
            if summary_meta and isinstance(summary_meta, dict):
                has_source = summary_meta.get("source") in ["ai", "edited", "fallback", "manual"]
                has_accepted_at = bool(summary_meta.get("accepted_at"))
                if has_source and has_accepted_at:
                    checks.append("✓ ai_accepted_summary_meta retained with valid source and accepted_at")
                else:
                    checks.append("✗ ai_accepted_summary_meta incomplete (missing source or accepted_at)")
            else:
                checks.append("✗ ai_accepted_summary_meta missing")
            
            # Check audit_envelope_sha256
            if data.get("audit_envelope_sha256") and len(data.get("audit_envelope_sha256", "")) == 64:
                checks.append("✓ audit_envelope_sha256 computed and stored")
            else:
                checks.append("✗ audit_envelope_sha256 missing or invalid")
            
            all_passed = all("✓" in c for c in checks)
            
            if all_passed:
                log_pass("Saved record retains all required data (weather_summary, weather_snapshot_meta, approved summary metadata)")
                for check in checks:
                    print(f"   {check}")
            else:
                log_fail("Saved record integrity", f"Data integrity checks failed")
                for check in checks:
                    print(f"   {check}")
        else:
            log_fail("Saved record integrity", f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_error("Saved record integrity", e)

def print_summary():
    """Print test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["errors"])
    passed_count = len(test_results["passed"])
    failed_count = len(test_results["failed"])
    error_count = len(test_results["errors"])
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️  Errors: {error_count}")
    
    if test_results["failed"]:
        print("\n--- Failed Tests ---")
        for fail in test_results["failed"]:
            print(f"  • {fail['test']}")
            print(f"    Reason: {fail['reason']}")
    
    if test_results["errors"]:
        print("\n--- Test Errors ---")
        for error in test_results["errors"]:
            print(f"  • {error['test']}")
            print(f"    Error: {error['error']}")
    
    print("\n" + "="*80)
    
    if failed_count == 0 and error_count == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED OR ENCOUNTERED ERRORS")
    print("="*80)

def main():
    """Run all TRACK 27.10 backend tests."""
    print("\n" + "="*80)
    print("TRACK 27.10 BACKEND API VERIFICATION TEST SUITE")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
    
    # Step 1: Authenticate
    admin_token = authenticate()
    if not admin_token:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
        print_summary()
        return
    
    # Step 2: Test missing approved summary
    test_missing_approved_summary(admin_token)
    
    # Step 3: Test missing accepted_at metadata
    test_missing_accepted_at_metadata(admin_token)
    
    # Step 4: Test invalid source label
    test_invalid_source_label(admin_token)
    
    # Step 5: Test valid submission
    report_id = test_valid_daily_report_submission(admin_token)
    
    # Step 6: Test PDF generation
    test_pdf_generation(admin_token, report_id)
    
    # Step 7: Test audit footer
    test_audit_footer(admin_token, report_id)
    
    # Step 8: Test saved record integrity
    test_saved_record_integrity(admin_token, report_id)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
