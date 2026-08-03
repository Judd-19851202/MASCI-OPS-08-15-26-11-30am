#!/usr/bin/env python3
"""Test script for Daily Report AI Summary 429 fix verification.

Focus:
1. POST /api/daily-reports/summary/draft must no longer return 429 under repeated requests
2. Verify repeated requests with the same X-Device-Id still return 200
3. Verify the response shape remains valid
4. Note that preview tenant AI summary is disabled, so enabled=false is acceptable
"""
import os
import sys
import time
import uuid
import requests

# Backend URL from frontend .env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def log_pass(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def log_fail(msg):
    print(f"{RED}✗{RESET} {msg}")

def log_info(msg):
    print(f"{YELLOW}ℹ{RESET} {msg}")

def log_section(msg):
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")


def main():
    log_section("Daily Report AI Summary 429 Fix Verification")
    
    # Generate a stable device ID for all requests
    device_id = f"test-device-{uuid.uuid4()}"
    log_info(f"Using device ID: {device_id}")
    
    # Test payload - minimal valid daily report draft
    test_payload = {
        "project_name": "Test Project",
        "project_number": "TEST-001",
        "report_date": "2026-07-15",
        "prepared_by": "Test Supervisor",
        "masci_crews": [
            {
                "employee_id": "EMP001",
                "name": "John Smith",
                "trade": "Foreman",
                "hours": 8.0
            }
        ],
        "equipment": [
            {
                "description": "Excavator",
                "unit_number": "EX-101",
                "run_hours": 6.0,
                "idle_hours": 2.0
            }
        ],
        "production": [
            {
                "description": "Excavation",
                "quantity": 100,
                "unit": "CY",
                "percent_complete": 50
            }
        ],
        "photos": []
    }
    
    # Test 1: Single request with device ID
    log_section("Test 1: Single Request with X-Device-Id")
    
    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id
    }
    
    body = {
        "payload": test_payload,
        "form_key": f"daily-report::TEST-001::2026-07-15::primary-{uuid.uuid4()}",
        "tenant_id": "masci",
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/daily-reports/summary/draft",
            json=body,
            headers=headers,
            timeout=30
        )
        
        log_info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            log_pass("Single request returned 200 OK")
            data = response.json()
            
            # Verify response shape
            required_fields = ["ok", "enabled", "summary_text", "language", "warnings", "evidence_refs", "summary_input"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                log_fail(f"Response missing required fields: {missing_fields}")
            else:
                log_pass("Response contains all required fields")
            
            # Check if AI is disabled (expected in preview)
            if data.get("enabled") is False:
                log_info(f"AI summary is disabled (reason: {data.get('reason_disabled')})")
                log_info("This is EXPECTED in preview environment - NOT A BUG")
            else:
                log_info("AI summary is enabled")
            
            # Verify summary_input structure
            summary_input = data.get("summary_input", {})
            if summary_input:
                log_pass(f"summary_input present with keys: {list(summary_input.keys())}")
            else:
                log_fail("summary_input is missing or empty")
                
        elif response.status_code == 429:
            log_fail("Single request returned 429 Too Many Requests - RATE LIMITING NOT DISABLED")
            log_info(f"Response: {response.text}")
            return False
        else:
            log_fail(f"Unexpected status code: {response.status_code}")
            log_info(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log_fail(f"Request failed with exception: {e}")
        return False
    
    # Test 2: Rapid repeated requests with same device ID (should NOT get 429)
    log_section("Test 2: Rapid Repeated Requests with Same X-Device-Id")
    
    num_requests = 10
    log_info(f"Sending {num_requests} rapid requests with same device ID...")
    
    status_codes = []
    response_times = []
    
    for i in range(num_requests):
        body["form_key"] = f"daily-report::TEST-001::2026-07-15::primary-{uuid.uuid4()}"
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{BACKEND_URL}/daily-reports/summary/draft",
                json=body,
                headers=headers,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            status_codes.append(response.status_code)
            response_times.append(elapsed)
            
            log_info(f"Request {i+1}/{num_requests}: {response.status_code} ({elapsed:.2f}s)")
            
            if response.status_code == 429:
                log_fail(f"Request {i+1} returned 429 - RATE LIMITING STILL ACTIVE")
                log_info(f"Response: {response.text}")
                
        except Exception as e:
            log_fail(f"Request {i+1} failed: {e}")
            status_codes.append(0)
            response_times.append(0)
    
    # Analyze results
    success_count = sum(1 for code in status_codes if code == 200)
    rate_limit_count = sum(1 for code in status_codes if code == 429)
    error_count = sum(1 for code in status_codes if code not in [200, 429])
    
    log_info(f"\nResults: {success_count} success, {rate_limit_count} rate limited, {error_count} errors")
    log_info(f"Average response time: {sum(response_times)/len(response_times):.2f}s")
    
    if rate_limit_count > 0:
        log_fail(f"CRITICAL: {rate_limit_count} requests returned 429 - Rate limiting is NOT disabled")
        return False
    elif success_count == num_requests:
        log_pass(f"All {num_requests} requests returned 200 - Rate limiting is properly disabled")
    else:
        log_fail(f"Some requests failed with unexpected status codes")
        return False
    
    # Test 3: Burst test - 20 requests in quick succession
    log_section("Test 3: Burst Test - 20 Requests")
    
    num_burst = 20
    log_info(f"Sending {num_burst} burst requests...")
    
    burst_status_codes = []
    
    for i in range(num_burst):
        body["form_key"] = f"daily-report::TEST-001::2026-07-15::burst-{uuid.uuid4()}"
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/daily-reports/summary/draft",
                json=body,
                headers=headers,
                timeout=30
            )
            burst_status_codes.append(response.status_code)
            
        except Exception as e:
            log_fail(f"Burst request {i+1} failed: {e}")
            burst_status_codes.append(0)
    
    burst_success = sum(1 for code in burst_status_codes if code == 200)
    burst_rate_limited = sum(1 for code in burst_status_codes if code == 429)
    
    log_info(f"Burst results: {burst_success}/{num_burst} success, {burst_rate_limited} rate limited")
    
    if burst_rate_limited > 0:
        log_fail(f"CRITICAL: {burst_rate_limited} burst requests returned 429")
        return False
    elif burst_success == num_burst:
        log_pass(f"All {num_burst} burst requests returned 200")
    else:
        log_fail(f"Some burst requests failed")
        return False
    
    # Test 4: Verify response shape consistency
    log_section("Test 4: Response Shape Consistency")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/daily-reports/summary/draft",
            json=body,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check all expected fields
            expected_structure = {
                "ok": bool,
                "enabled": bool,
                "summary_text": str,
                "language": str,
                "warnings": list,
                "evidence_refs": list,
                "summary_input": dict
            }
            
            all_valid = True
            for field, expected_type in expected_structure.items():
                if field not in data:
                    log_fail(f"Missing field: {field}")
                    all_valid = False
                elif not isinstance(data[field], expected_type):
                    log_fail(f"Field {field} has wrong type: expected {expected_type}, got {type(data[field])}")
                    all_valid = False
                else:
                    log_pass(f"Field {field}: {expected_type.__name__} ✓")
            
            if all_valid:
                log_pass("Response shape is valid and consistent")
            else:
                log_fail("Response shape has issues")
                return False
                
        else:
            log_fail(f"Final verification request returned {response.status_code}")
            return False
            
    except Exception as e:
        log_fail(f"Final verification failed: {e}")
        return False
    
    # Final summary
    log_section("FINAL VERDICT")
    
    log_pass("✓ POST /api/daily-reports/summary/draft no longer returns 429")
    log_pass("✓ Repeated requests with same X-Device-Id return 200")
    log_pass("✓ Response shape is valid and includes usable summary payload")
    log_info("✓ Preview tenant AI summary disabled (enabled=false) - EXPECTED, NOT A BUG")
    
    print(f"\n{GREEN}{BOLD}ALL TESTS PASSED - 429 BLOCKER IS RESOLVED{RESET}\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Test failed with exception: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
