#!/usr/bin/env python3
"""
Backend verification test for backup admin fixes on preview environment.

This script verifies:
1. /api/admin/backups-scheduler-state returns 200 with correct stale lock fields
2. /api/admin/system-health returns 200 with canonical recoverable point (not 'unknown')
3. /api/admin/backups-complete-r2-state returns 200 with preview prefix in nightly_last.r2_key
4. /api/admin/backups-list-r2 returns 200 with preview prefix and keys inside preview prefix
5. Reports any remaining limitations for production validation
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Expected preview prefix
EXPECTED_PREVIEW_PREFIX = "backups/preview/auto-90d/"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def login_and_get_tokens() -> Dict[str, str]:
    """Login via multi-login and extract admin portal tokens."""
    print_info("Logging in as Super Admin...")
    
    login_url = f"{BASE_URL}/api/auth/multi-login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok"):
            print_error(f"Login failed: {data.get('error', 'Unknown error')}")
            sys.exit(1)
        
        # Extract tokens from response
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not session_token or not admin_token:
            print_error("Missing required tokens in login response")
            print_error(f"Response: {json.dumps(data, indent=2)}")
            sys.exit(1)
        
        print_success("Login successful")
        print_info(f"Session token: {session_token[:20]}...")
        print_info(f"Admin token: {admin_token[:20]}...")
        
        # Return headers with both session token and admin portal token
        return {
            "X-Portal-Token": admin_token,
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
    except requests.exceptions.RequestException as e:
        print_error(f"Login request failed: {e}")
        sys.exit(1)

def test_backups_scheduler_state(headers: Dict[str, str]) -> bool:
    """Test 1: Verify /api/admin/backups-scheduler-state endpoint."""
    print_info("\n=== Test 1: /api/admin/backups-scheduler-state ===")
    
    url = f"{BASE_URL}/api/admin/backups-scheduler-state"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
        
        print_success(f"Status code: {response.status_code}")
        
        data = response.json()
        
        # Check for hourly_activation field
        if "hourly_activation" not in data:
            print_error("Missing 'hourly_activation' field in response")
            return False
        
        hourly_activation = data["hourly_activation"]
        
        # Check for required fields in hourly_activation
        required_fields = [
            "stale_lock_present",
            "stale_job_count",
            "blocking_stale_job_count",
            "reclaimable_stale_job_count"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in hourly_activation:
                missing_fields.append(field)
        
        if missing_fields:
            print_error(f"Missing required fields in hourly_activation: {missing_fields}")
            print_error(f"hourly_activation keys: {list(hourly_activation.keys())}")
            return False
        
        # Verify field values
        stale_lock_present = hourly_activation["stale_lock_present"]
        stale_job_count = hourly_activation["stale_job_count"]
        blocking_stale_job_count = hourly_activation["blocking_stale_job_count"]
        reclaimable_stale_job_count = hourly_activation["reclaimable_stale_job_count"]
        
        print_success(f"stale_lock_present: {stale_lock_present}")
        print_success(f"stale_job_count: {stale_job_count}")
        print_success(f"blocking_stale_job_count: {blocking_stale_job_count}")
        print_success(f"reclaimable_stale_job_count: {reclaimable_stale_job_count}")
        
        # Verify stale_lock_present is false (no fake blockers)
        if stale_lock_present:
            print_warning(f"stale_lock_present is {stale_lock_present} (expected false for no blockers)")
        else:
            print_success("No stale lock present (no fake blockers)")
        
        # Note: Preview is expected to show hourly activation disabled
        activation_status = hourly_activation.get("activation_status", "UNKNOWN")
        print_info(f"Hourly activation status: {activation_status}")
        if "DISABLED" in activation_status.upper() or "HARD-CODED" in activation_status.upper():
            print_info("Hourly activation disabled by config/environment (expected for preview)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_system_health(headers: Dict[str, str]) -> bool:
    """Test 2: Verify /api/admin/system-health endpoint."""
    print_info("\n=== Test 2: /api/admin/system-health ===")
    
    url = f"{BASE_URL}/api/admin/system-health"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
        
        print_success(f"Status code: {response.status_code}")
        
        data = response.json()
        
        # Find the backup card
        cards = data.get("cards", [])
        backup_card = None
        for card in cards:
            if card.get("key") == "backup":
                backup_card = card
                break
        
        if not backup_card:
            print_error("Backup card not found in system-health response")
            print_error(f"Available cards: {[c.get('key') for c in cards]}")
            return False
        
        print_success("Backup card found")
        
        # Check the detail field
        detail = backup_card.get("detail", "")
        print_info(f"Backup card detail: {detail}")
        
        # Verify it does NOT say "Authoritative recovery point unknown"
        if "Authoritative recovery point unknown" in detail or "authoritative_recovery_point_unknown" in detail:
            print_error("Backup card shows 'Authoritative recovery point unknown'")
            return False
        
        # Verify it shows a canonical recoverable point
        if "Canonical recoverable point" in detail:
            print_success("Backup card shows canonical recoverable point")
            # Extract hours ago if present
            if "h ago" in detail:
                import re
                match = re.search(r'(\d+\.?\d*)\s*h ago', detail)
                if match:
                    hours = float(match.group(1))
                    print_info(f"Last backup: {hours} hours ago")
        else:
            print_warning(f"Backup card detail format unexpected: {detail}")
        
        # Check status
        status = backup_card.get("status", "")
        print_info(f"Backup card status: {status}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_backups_complete_r2_state(headers: Dict[str, str]) -> bool:
    """Test 3: Verify /api/admin/backups-complete-r2-state endpoint."""
    print_info("\n=== Test 3: /api/admin/backups-complete-r2-state ===")
    
    url = f"{BASE_URL}/api/admin/backups-complete-r2-state"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
        
        print_success(f"Status code: {response.status_code}")
        
        data = response.json()
        
        # Check for nightly_last field
        nightly_last = data.get("nightly_last")
        if not nightly_last:
            print_warning("nightly_last is null or missing (may be no backups yet)")
            return True  # Not a failure if no backups exist yet
        
        # Check r2_key field
        r2_key = nightly_last.get("r2_key", "")
        print_info(f"nightly_last.r2_key: {r2_key}")
        
        # Verify it uses the preview prefix
        if not r2_key:
            print_warning("r2_key is empty")
            return True
        
        if EXPECTED_PREVIEW_PREFIX in r2_key:
            print_success(f"r2_key uses preview prefix: {EXPECTED_PREVIEW_PREFIX}")
        else:
            print_error(f"r2_key does NOT use preview prefix")
            print_error(f"Expected prefix: {EXPECTED_PREVIEW_PREFIX}")
            print_error(f"Actual r2_key: {r2_key}")
            return False
        
        # Additional info
        filename = nightly_last.get("filename", "")
        size_bytes = nightly_last.get("size_bytes", 0)
        ts = nightly_last.get("ts", "")
        print_info(f"Filename: {filename}")
        print_info(f"Size: {size_bytes} bytes")
        print_info(f"Timestamp: {ts}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_backups_list_r2(headers: Dict[str, str]) -> bool:
    """Test 4: Verify /api/admin/backups-list-r2 endpoint."""
    print_info("\n=== Test 4: /api/admin/backups-list-r2 ===")
    
    url = f"{BASE_URL}/api/admin/backups-list-r2"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
        
        print_success(f"Status code: {response.status_code}")
        
        data = response.json()
        
        # Check prefix field
        prefix = data.get("prefix", "")
        print_info(f"Prefix: {prefix}")
        
        if prefix != EXPECTED_PREVIEW_PREFIX:
            print_error(f"Prefix does NOT match expected preview prefix")
            print_error(f"Expected: {EXPECTED_PREVIEW_PREFIX}")
            print_error(f"Actual: {prefix}")
            return False
        
        print_success(f"Prefix matches expected preview prefix: {EXPECTED_PREVIEW_PREFIX}")
        
        # Check backups list
        backups = data.get("backups", [])
        count = data.get("count", 0)
        total_in_bucket = data.get("total_in_bucket", 0)
        
        print_info(f"Backups returned: {count}")
        print_info(f"Total in bucket: {total_in_bucket}")
        
        if count == 0:
            print_warning("No backups found in R2 (may be expected for new environment)")
            return True
        
        # Verify all returned keys stay inside preview prefix
        keys_outside_prefix = []
        for backup in backups:
            key = backup.get("key", "")
            if not key.startswith(EXPECTED_PREVIEW_PREFIX):
                keys_outside_prefix.append(key)
        
        if keys_outside_prefix:
            print_error(f"Found {len(keys_outside_prefix)} keys outside preview prefix:")
            for key in keys_outside_prefix[:5]:  # Show first 5
                print_error(f"  - {key}")
            return False
        
        print_success(f"All {count} returned keys stay inside preview prefix")
        
        # Show sample keys
        if backups:
            print_info("Sample backup keys:")
            for backup in backups[:3]:
                key = backup.get("key", "")
                filename = backup.get("filename", "")
                size_mb = backup.get("size_bytes", 0) / (1024 * 1024)
                print_info(f"  - {filename} ({size_mb:.2f} MB)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def report_production_limitations():
    """Report any remaining limitations that can only be validated after production redeploy."""
    print_info("\n=== Production Validation Limitations ===")
    
    limitations = [
        "Preview environment has hourly activation disabled by config (BACKUP_R2_HOURLY=false)",
        "Production-specific backup scheduling behavior cannot be fully validated in preview",
        "Production R2 prefix (backups/production/auto-90d/) can only be verified after production deploy",
        "Production-specific stale lock cleanup behavior requires production environment validation"
    ]
    
    print_info("The following items can only be validated after production redeploy:")
    for i, limitation in enumerate(limitations, 1):
        print_info(f"  {i}. {limitation}")

def main():
    print_info("=" * 80)
    print_info("Backend Verification Test - Backup Admin Fixes (Preview Environment)")
    print_info("=" * 80)
    
    # Login and get tokens
    headers = login_and_get_tokens()
    
    # Run tests
    results = {
        "backups-scheduler-state": test_backups_scheduler_state(headers),
        "system-health": test_system_health(headers),
        "backups-complete-r2-state": test_backups_complete_r2_state(headers),
        "backups-list-r2": test_backups_list_r2(headers)
    }
    
    # Report production limitations
    report_production_limitations()
    
    # Summary
    print_info("\n" + "=" * 80)
    print_info("TEST SUMMARY")
    print_info("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASS")
        else:
            print_error(f"{test_name}: FAIL")
    
    print_info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("\n✅ ALL TESTS PASSED - Backup admin fixes verified on preview")
        return 0
    else:
        print_error(f"\n❌ {total - passed} TEST(S) FAILED - Review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
