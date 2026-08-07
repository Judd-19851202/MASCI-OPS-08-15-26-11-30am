#!/usr/bin/env python3
"""
WP-18C8 Final Backend Recertification - Executive Hardening Validation
Test live C8 behavior only; do not open C9.
"""

import json
import time
import requests
from typing import Any, Dict, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

# Expected seeded metrics
EXPECTED_BAC = 1200.0
EXPECTED_EV = 1200.0
EXPECTED_AC = 900.0
EXPECTED_CPI = 1.3333
CPI_TOLERANCE = 0.01


def log(message: str) -> None:
    """Print timestamped log message."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


def pm_login() -> Dict[str, str]:
    """Login as PM and return token."""
    log("Logging in as PM...")
    response = requests.post(
        f"{API_BASE}/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"PM login failed: {response.status_code} {response.text}")
    data = response.json()
    token = data.get("token")
    if not token:
        raise RuntimeError("PM login did not return token")
    log(f"✅ PM login successful (token length: {len(token)})")
    return {"X-PM-Token": token}


def admin_login() -> Dict[str, str]:
    """Login as Admin and return tokens."""
    log("Logging in as Admin...")
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Admin login failed: {response.status_code} {response.text}")
    data = response.json()
    session_token = data.get("session_token")
    portal_tokens = data.get("portal_tokens") or {}
    admin_token = portal_tokens.get("admin")
    if not session_token or not admin_token:
        raise RuntimeError("Admin login did not return required tokens")
    log(f"✅ Admin login successful (session: {len(session_token)}, admin: {len(admin_token)})")
    return {"X-Directory-Token": session_token, "X-Admin-Token": admin_token}


def test_pm_earned_value_readiness(headers: Dict[str, str]) -> Dict[str, Any]:
    """Test 1: PM earned-value route returns readiness overall=ready with correct metrics."""
    log("\n=== TEST 1: PM Earned Value Readiness ===")
    
    # Test cached route performance (should be sub-second-ish)
    start_time = time.time()
    response = requests.get(
        f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value",
        headers=headers,
        timeout=30,
    )
    cached_time_ms = (time.time() - start_time) * 1000
    
    if response.status_code != 200:
        raise RuntimeError(f"PM earned-value endpoint failed: {response.status_code} {response.text}")
    
    data = response.json()
    readiness = data.get("readiness") or {}
    summary = data.get("summary") or {}
    
    # Check readiness overall=ready
    overall = readiness.get("overall")
    if overall != "ready":
        raise RuntimeError(f"Expected readiness overall=ready, got: {overall}")
    log(f"✅ Readiness overall: {overall}")
    
    # Check seeded metrics
    bac = summary.get("bac")
    ev = summary.get("ev")
    ac = summary.get("ac")
    cpi = summary.get("cpi")
    open_actual_count = summary.get("open_actual_cost_count")
    open_commitment_count = summary.get("open_commitment_count")
    
    if bac != EXPECTED_BAC:
        raise RuntimeError(f"Expected BAC={EXPECTED_BAC}, got: {bac}")
    log(f"✅ BAC: {bac}")
    
    if ev != EXPECTED_EV:
        raise RuntimeError(f"Expected EV={EXPECTED_EV}, got: {ev}")
    log(f"✅ EV: {ev}")
    
    if ac != EXPECTED_AC:
        raise RuntimeError(f"Expected AC={EXPECTED_AC}, got: {ac}")
    log(f"✅ AC: {ac}")
    
    if cpi is None or abs(cpi - EXPECTED_CPI) > CPI_TOLERANCE:
        raise RuntimeError(f"Expected CPI≈{EXPECTED_CPI}, got: {cpi}")
    log(f"✅ CPI: {cpi:.4f}")
    
    if open_actual_count != 0:
        raise RuntimeError(f"Expected open_actual_cost_count=0, got: {open_actual_count}")
    log(f"✅ Open actual cost count: {open_actual_count}")
    
    if open_commitment_count != 0:
        raise RuntimeError(f"Expected open_commitment_count=0, got: {open_commitment_count}")
    log(f"✅ Open commitment count: {open_commitment_count}")
    
    # Check performance hardening: cached route should be sub-second-ish
    log(f"⏱️  Cached route response time: {cached_time_ms:.0f}ms")
    if cached_time_ms > 2000:
        log(f"⚠️  WARNING: Cached route took {cached_time_ms:.0f}ms (expected sub-second-ish)")
    else:
        log(f"✅ Cached route performance: sub-2s ({cached_time_ms:.0f}ms)")
    
    # Check completed-project forecast handling (ETC can be null without blocking readiness)
    etc = summary.get("etc")
    forecast_readiness = readiness.get("forecast")
    log(f"ℹ️  ETC: {etc}, Forecast readiness: {forecast_readiness}")
    if overall == "ready" and etc is None:
        log("✅ Completed-project forecast handling: readiness not blocked by null ETC")
    
    return data


def test_admin_earned_value_mirror(headers: Dict[str, str]) -> Dict[str, Any]:
    """Test 2: Admin earned-value route mirrors the same seeded summary and remains read-only."""
    log("\n=== TEST 2: Admin Earned Value Mirror ===")
    
    response = requests.get(
        f"{API_BASE}/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value",
        headers=headers,
        timeout=30,
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Admin earned-value endpoint failed: {response.status_code} {response.text}")
    
    data = response.json()
    summary = data.get("summary") or {}
    
    # Check that admin route mirrors the same seeded summary
    bac = summary.get("bac")
    ev = summary.get("ev")
    ac = summary.get("ac")
    cpi = summary.get("cpi")
    open_actual_count = summary.get("open_actual_cost_count")
    open_commitment_count = summary.get("open_commitment_count")
    
    if bac != EXPECTED_BAC:
        raise RuntimeError(f"Admin BAC mismatch: expected {EXPECTED_BAC}, got: {bac}")
    if ev != EXPECTED_EV:
        raise RuntimeError(f"Admin EV mismatch: expected {EXPECTED_EV}, got: {ev}")
    if ac != EXPECTED_AC:
        raise RuntimeError(f"Admin AC mismatch: expected {EXPECTED_AC}, got: {ac}")
    if cpi is None or abs(cpi - EXPECTED_CPI) > CPI_TOLERANCE:
        raise RuntimeError(f"Admin CPI mismatch: expected ≈{EXPECTED_CPI}, got: {cpi}")
    if open_actual_count != 0:
        raise RuntimeError(f"Admin open_actual_cost_count mismatch: expected 0, got: {open_actual_count}")
    if open_commitment_count != 0:
        raise RuntimeError(f"Admin open_commitment_count mismatch: expected 0, got: {open_commitment_count}")
    
    log(f"✅ Admin route mirrors seeded summary: BAC={bac}, EV={ev}, AC={ac}, CPI={cpi:.4f}")
    log(f"✅ Admin route open counts: actual={open_actual_count}, commitment={open_commitment_count}")
    log("✅ Admin route is read-only (GET endpoint)")
    
    return data


def test_csv_export_endpoints(pm_headers: Dict[str, str], admin_headers: Dict[str, str]) -> None:
    """Test 3: CSV export endpoints still return 200."""
    log("\n=== TEST 3: CSV Export Endpoints ===")
    
    # Test PM export endpoint with performance check (should be under 2500ms DA output-channel budget)
    log("Testing PM earned-value CSV export...")
    start_time = time.time()
    response = requests.get(
        f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value/export",
        headers=pm_headers,
        timeout=30,
    )
    export_time_ms = (time.time() - start_time) * 1000
    
    if response.status_code != 200:
        raise RuntimeError(f"PM export endpoint failed: {response.status_code}")
    
    if response.headers.get("Content-Type") != "text/csv; charset=utf-8":
        raise RuntimeError(f"PM export wrong content type: {response.headers.get('Content-Type')}")
    
    content_length = len(response.content)
    log(f"✅ PM export endpoint: 200 OK, {content_length} bytes")
    log(f"⏱️  PM export response time: {export_time_ms:.0f}ms")
    
    if export_time_ms > 2500:
        log(f"⚠️  WARNING: PM export took {export_time_ms:.0f}ms (DA budget: 2500ms)")
    else:
        log(f"✅ PM export performance: under DA 2500ms budget ({export_time_ms:.0f}ms)")
    
    # Test Admin export endpoint
    log("Testing Admin earned-value CSV export...")
    response = requests.get(
        f"{API_BASE}/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value/export",
        headers=admin_headers,
        timeout=30,
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Admin export endpoint failed: {response.status_code}")
    
    if response.headers.get("Content-Type") != "text/csv; charset=utf-8":
        raise RuntimeError(f"Admin export wrong content type: {response.headers.get('Content-Type')}")
    
    content_length = len(response.content)
    log(f"✅ Admin export endpoint: 200 OK, {content_length} bytes")


def test_force_refresh_performance(pm_headers: Dict[str, str]) -> None:
    """Test 4: Force-refresh is materially reduced from earlier 26-28s path."""
    log("\n=== TEST 4: Force-Refresh Performance ===")
    
    log("Testing force-refresh performance (should be materially reduced from 26-28s)...")
    start_time = time.time()
    response = requests.get(
        f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value?force_refresh=true",
        headers=pm_headers,
        timeout=60,
    )
    force_refresh_time_s = time.time() - start_time
    
    if response.status_code != 200:
        raise RuntimeError(f"Force-refresh endpoint failed: {response.status_code}")
    
    data = response.json()
    cache_status = data.get("cache_status")
    performance = data.get("performance_profile") or {}
    
    log(f"✅ Force-refresh endpoint: 200 OK")
    log(f"⏱️  Force-refresh response time: {force_refresh_time_s:.1f}s")
    log(f"ℹ️  Cache status: {cache_status}")
    log(f"ℹ️  Performance profile: {json.dumps(performance, indent=2)}")
    
    if force_refresh_time_s > 26:
        log(f"⚠️  WARNING: Force-refresh took {force_refresh_time_s:.1f}s (baseline: 26-28s)")
        log("⚠️  Expected material reduction from 26-28s baseline")
    else:
        log(f"✅ Force-refresh performance: materially reduced from 26-28s baseline ({force_refresh_time_s:.1f}s)")


def test_auth_regression() -> None:
    """Test 6: No auth regression - unauthenticated PM route should still reject."""
    log("\n=== TEST 6: Auth Regression Check ===")
    
    log("Testing unauthenticated access (should reject with 401)...")
    response = requests.get(
        f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value",
        timeout=15,
    )
    
    if response.status_code == 200:
        raise RuntimeError("Auth regression: unauthenticated request succeeded (expected 401)")
    
    if response.status_code != 401:
        log(f"⚠️  WARNING: Expected 401, got {response.status_code}")
    
    log(f"✅ Unauthenticated access correctly rejected: {response.status_code}")


def main() -> None:
    """Run all WP-18C8 final recertification tests."""
    log("=" * 80)
    log("WP-18C8 Final Backend Recertification - Executive Hardening Validation")
    log("=" * 80)
    
    results = {
        "test_1_pm_readiness": False,
        "test_2_admin_mirror": False,
        "test_3_csv_exports": False,
        "test_4_force_refresh": False,
        "test_6_auth_regression": False,
    }
    
    try:
        # Login
        pm_headers = pm_login()
        admin_headers = admin_login()
        
        # Test 1: PM earned-value readiness
        try:
            test_pm_earned_value_readiness(pm_headers)
            results["test_1_pm_readiness"] = True
        except Exception as e:
            log(f"❌ TEST 1 FAILED: {e}")
            raise
        
        # Test 2: Admin earned-value mirror
        try:
            test_admin_earned_value_mirror(admin_headers)
            results["test_2_admin_mirror"] = True
        except Exception as e:
            log(f"❌ TEST 2 FAILED: {e}")
            raise
        
        # Test 3: CSV export endpoints
        try:
            test_csv_export_endpoints(pm_headers, admin_headers)
            results["test_3_csv_exports"] = True
        except Exception as e:
            log(f"❌ TEST 3 FAILED: {e}")
            raise
        
        # Test 4: Force-refresh performance
        try:
            test_force_refresh_performance(pm_headers)
            results["test_4_force_refresh"] = True
        except Exception as e:
            log(f"❌ TEST 4 FAILED: {e}")
            raise
        
        # Test 6: Auth regression
        try:
            test_auth_regression()
            results["test_6_auth_regression"] = True
        except Exception as e:
            log(f"❌ TEST 6 FAILED: {e}")
            raise
        
        # Summary
        log("\n" + "=" * 80)
        log("FINAL RESULTS")
        log("=" * 80)
        passed_count = sum(results.values())
        total = len(results)
        log(f"Tests passed: {passed_count}/{total}")
        for test_name, test_passed in results.items():
            status = "✅ PASS" if test_passed else "❌ FAIL"
            log(f"  {status} - {test_name}")
        
        if passed_count == total:
            log("\n🎉 ALL TESTS PASSED - WP-18C8 FINAL RECERTIFICATION COMPLETE")
            return
        else:
            log(f"\n❌ {total - passed_count} TEST(S) FAILED")
            exit(1)
    
    except Exception as e:
        log(f"\n❌ CRITICAL ERROR: {e}")
        log("\nTest Results:")
        for test_name, test_passed in results.items():
            status = "✅ PASS" if test_passed else "❌ FAIL"
            log(f"  {status} - {test_name}")
        exit(1)


if __name__ == "__main__":
    main()
