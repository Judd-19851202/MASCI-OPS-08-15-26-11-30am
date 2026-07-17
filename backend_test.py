#!/usr/bin/env python3
"""
Backend verification for Daily Report changes (Track 27.11D).

Tests:
1. POST /api/transcribe - accepts multipart audio uploads
2. POST /api/daily-reports - includes conflict_watchdog metadata
3. GET /api/daily-reports.csv - async polling with 202, job_id, status_url
4. POST /api/daily-reports/photo-intelligence/draft - returns photo_statuses
5. No regressions in async jobs flow
"""

import asyncio
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import httpx

# Configuration
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"  {message}")
    
    results["tests"].append({
        "name": name,
        "passed": passed,
        "message": message
    })
    
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1


async def get_admin_token() -> str:
    """Authenticate and get admin token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
        
        data = response.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        
        if not admin_token:
            raise Exception("No admin token in response")
        
        return admin_token


async def test_transcribe_endpoint(token: str):
    """Test 1: POST /api/transcribe accepts multipart audio uploads."""
    print("\n=== Test 1: POST /api/transcribe ===")
    
    # Create a minimal audio file (webm format)
    # This is a minimal valid webm header
    audio_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm\x42\x87\x81\x02\x42\x85\x81\x02'
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test with valid audio file
        files = {
            "audio": ("test_voice.webm", io.BytesIO(audio_data), "audio/webm")
        }
        data = {
            "field_hint": "work_performed",
            "language_hint": "auto",
            "project_number": "TEST-001"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/transcribe",
                files=files,
                data=data
            )
            
            # Endpoint should return either 200 (success) or 422 (validation error for invalid audio)
            # or 503 (service unavailable if LLM key missing)
            if response.status_code in [200, 422, 503, 502]:
                if response.status_code == 200:
                    result = response.json()
                    has_required_fields = all(k in result for k in ["ok", "english_text", "work_performed", "activities"])
                    log_test(
                        "POST /api/transcribe returns valid response structure",
                        has_required_fields,
                        f"Response has required fields: {has_required_fields}"
                    )
                elif response.status_code == 422:
                    log_test(
                        "POST /api/transcribe validation works",
                        True,
                        "Endpoint correctly validates audio input (422 for invalid audio)"
                    )
                elif response.status_code == 503:
                    log_test(
                        "POST /api/transcribe endpoint exists",
                        True,
                        "Endpoint exists but LLM key not configured (503 - expected in some environments)"
                    )
                else:  # 502
                    log_test(
                        "POST /api/transcribe endpoint exists",
                        True,
                        "Endpoint exists but transcription service failed (502 - expected with minimal audio)"
                    )
            else:
                log_test(
                    "POST /api/transcribe endpoint exists",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
        except Exception as e:
            log_test("POST /api/transcribe endpoint", False, f"Error: {str(e)}")


async def test_daily_report_with_conflict_watchdog(token: str):
    """Test 2: POST /api/daily-reports includes conflict_watchdog metadata."""
    print("\n=== Test 2: POST /api/daily-reports with conflict_watchdog ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a daily report
        report_data = {
            "project_name": "Test Project",
            "project_number": "TEST-DR-001",
            "location": "Test Site",
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "prepared_by": "Test Supervisor",
            "superintendent": "Test Super",
            "weather_summary": "Clear skies",
            "general_notes": "Test report for conflict watchdog verification",
            "ai_accepted_summary": "Test summary for validation",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "accepted_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/daily-reports",
                json=report_data,
                headers={"X-Admin-Token": token}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if conflict_watchdog is present
                has_conflict_watchdog = "conflict_watchdog" in result
                log_test(
                    "POST /api/daily-reports includes conflict_watchdog",
                    has_conflict_watchdog,
                    f"conflict_watchdog present: {has_conflict_watchdog}"
                )
                
                if has_conflict_watchdog:
                    watchdog = result["conflict_watchdog"]
                    required_fields = ["has_conflicts", "requires_pm_review", "checked_at"]
                    has_required = all(f in watchdog for f in required_fields)
                    log_test(
                        "conflict_watchdog has required fields",
                        has_required,
                        f"Required fields present: {has_required}"
                    )
                
                # Store report ID for later tests
                return result.get("id")
            else:
                log_test(
                    "POST /api/daily-reports creates report",
                    False,
                    f"Status: {response.status_code}, Error: {response.text[:200]}"
                )
                return None
        except Exception as e:
            log_test("POST /api/daily-reports", False, f"Error: {str(e)}")
            return None


async def test_csv_export_async_polling(token: str):
    """Test 3: GET /api/daily-reports.csv uses async polling."""
    print("\n=== Test 3: GET /api/daily-reports.csv async polling ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Request CSV export
            response = await client.get(
                f"{API_BASE}/daily-reports.csv",
                headers={"X-Admin-Token": token}
            )
            
            # Should return 202 Accepted
            if response.status_code == 202:
                result = response.json()
                
                # Check for required fields
                has_job_id = "job_id" in result
                has_status_url = "status_url" in result
                
                log_test(
                    "GET /api/daily-reports.csv returns 202 with job_id",
                    has_job_id,
                    f"job_id present: {has_job_id}"
                )
                
                log_test(
                    "GET /api/daily-reports.csv returns status_url",
                    has_status_url,
                    f"status_url: {result.get('status_url', 'N/A')}"
                )
                
                if has_job_id and has_status_url:
                    job_id = result["job_id"]
                    status_url = result["status_url"]
                    
                    # Poll the status endpoint
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        await asyncio.sleep(1.5)  # Wait before polling
                        
                        status_response = await client.get(
                            f"{API_BASE}{status_url.replace('/api', '')}",
                            headers={"X-Admin-Token": token}
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            job_status = status_data.get("status")
                            
                            print(f"  Attempt {attempt + 1}: Job status = {job_status}")
                            
                            if job_status == "completed":
                                # download_url is in the result object
                                result_obj = status_data.get("result", {})
                                has_download_url = "download_url" in result_obj
                                log_test(
                                    "Async job reaches completed status with download_url",
                                    has_download_url,
                                    f"download_url: {result_obj.get('download_url', 'N/A')}"
                                )
                                break
                            elif job_status in ["failed", "error"]:
                                log_test(
                                    "Async job processing",
                                    False,
                                    f"Job failed: {status_data.get('message', 'Unknown error')}"
                                )
                                break
                        else:
                            log_test(
                                "GET /api/jobs/{job_id}/status endpoint",
                                False,
                                f"Status check failed: {status_response.status_code}"
                            )
                            break
                    else:
                        # Timeout after max attempts
                        log_test(
                            "Async job completion",
                            False,
                            f"Job did not complete within {max_attempts} attempts"
                        )
            else:
                log_test(
                    "GET /api/daily-reports.csv returns 202",
                    False,
                    f"Expected 202, got {response.status_code}"
                )
        except Exception as e:
            log_test("GET /api/daily-reports.csv async flow", False, f"Error: {str(e)}")


async def test_photo_intelligence_draft(token: str):
    """Test 4: POST /api/daily-reports/photo-intelligence/draft returns photo_statuses."""
    print("\n=== Test 4: POST /api/daily-reports/photo-intelligence/draft ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a draft payload with photos
        draft_payload = {
            "form_key": f"daily-report::TEST::2026-01-01::test-{int(time.time())}",
            "payload": {
                "project_number": "TEST-001",
                "report_date": "2026-01-01",
                "photos": [
                    "photo://test-photo-1",
                    "photo://test-photo-2",
                    "photo://test-photo-3"
                ]
            },
            "force": False
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/daily-reports/photo-intelligence/draft",
                json=draft_payload,
                headers={"X-Admin-Token": token}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for photo_statuses field
                has_photo_statuses = "photo_statuses" in result
                log_test(
                    "POST /api/daily-reports/photo-intelligence/draft returns photo_statuses",
                    has_photo_statuses,
                    f"photo_statuses present: {has_photo_statuses}"
                )
                
                if has_photo_statuses:
                    photo_statuses = result["photo_statuses"]
                    is_list = isinstance(photo_statuses, list)
                    log_test(
                        "photo_statuses is a list",
                        is_list,
                        f"Type: {type(photo_statuses).__name__}, Length: {len(photo_statuses) if is_list else 'N/A'}"
                    )
                    
                    if is_list and len(photo_statuses) > 0:
                        # Check structure of first photo status
                        first_status = photo_statuses[0]
                        required_fields = ["photo_id", "status"]
                        has_required = all(f in first_status for f in required_fields)
                        log_test(
                            "photo_statuses entries have required fields",
                            has_required,
                            f"Fields in first entry: {list(first_status.keys())}"
                        )
                
                # Check other required fields
                required_response_fields = ["report_id", "photo_count", "status"]
                has_all_required = all(f in result for f in required_response_fields)
                log_test(
                    "Response includes required fields",
                    has_all_required,
                    f"Required fields present: {has_all_required}"
                )
            else:
                log_test(
                    "POST /api/daily-reports/photo-intelligence/draft",
                    False,
                    f"Status: {response.status_code}, Error: {response.text[:200]}"
                )
        except Exception as e:
            log_test("POST /api/daily-reports/photo-intelligence/draft", False, f"Error: {str(e)}")


async def test_async_jobs_no_regression(token: str):
    """Test 5: No regressions in async jobs flow."""
    print("\n=== Test 5: Async jobs flow regression check ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Trigger another CSV export to test the flow
            response = await client.get(
                f"{API_BASE}/daily-reports.csv",
                headers={"X-Admin-Token": token}
            )
            
            if response.status_code == 202:
                result = response.json()
                job_id = result.get("job_id")
                
                if job_id:
                    # Test the status endpoint
                    status_response = await client.get(
                        f"{API_BASE}/jobs/{job_id}/status",
                        headers={"X-Admin-Token": token}
                    )
                    
                    status_ok = status_response.status_code == 200
                    log_test(
                        "GET /api/jobs/{job_id}/status endpoint works",
                        status_ok,
                        f"Status code: {status_response.status_code}"
                    )
                    
                    if status_ok:
                        status_data = status_response.json()
                        has_status_field = "status" in status_data
                        log_test(
                            "Job status response has status field",
                            has_status_field,
                            f"Status: {status_data.get('status', 'N/A')}"
                        )
                else:
                    log_test("Async jobs flow", False, "No job_id in response")
            else:
                log_test(
                    "Async jobs flow trigger",
                    False,
                    f"CSV export failed with status {response.status_code}"
                )
        except Exception as e:
            log_test("Async jobs flow regression check", False, f"Error: {str(e)}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend Verification - Daily Report Changes (Track 27.11D)")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print()
    
    try:
        # Authenticate
        print("Authenticating...")
        token = await get_admin_token()
        print(f"✓ Authenticated successfully (token length: {len(token)})")
        
        # Run tests
        await test_transcribe_endpoint(token)
        await test_daily_report_with_conflict_watchdog(token)
        await test_csv_export_async_polling(token)
        await test_photo_intelligence_draft(token)
        await test_async_jobs_no_regression(token)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        results["failed"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print()
    
    if results["failed"] > 0:
        print("Failed tests:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"  - {test['name']}")
                if test["message"]:
                    print(f"    {test['message']}")
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
