"""
WP-18C9 Frozen Closeout Backend Verification

Final backend-focused verification using curl/API validation.
Tests admin and PM authentication and core C9 admin surfaces.

Required checks:
1. Admin authentication through /api/auth/multi-login
2. Admin session can read core C9 admin surfaces/APIs
3. PM authentication through /api/auth/multi-login
4. PM session can read PM operational APIs
5. No backend auth regression
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import httpx

# Backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

# Test results
results = {
    "test_suite": "WP-18C9 Frozen Closeout Backend Verification",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": [],
    "summary": {"passed": 0, "failed": 0}
}


def log_test(name: str, status: str, details: str = ""):
    """Log a test result"""
    result = {
        "name": name,
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    results["tests"].append(result)
    
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ {name}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ {name}")
    
    if details:
        print(f"   {details}")


async def test_admin_login() -> Optional[Dict[str, str]]:
    """Test 1: Admin authentication through /api/auth/multi-login"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.post(
                f"{API_BASE}/auth/multi-login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract tokens from response (new structure: portal_tokens)
                tokens = {}
                portal_tokens = data.get("portal_tokens", {})
                if "admin" in portal_tokens:
                    tokens["X-Admin-Token"] = portal_tokens["admin"]
                if "pm" in portal_tokens:
                    tokens["X-PM-Token"] = portal_tokens["pm"]
                
                # Add session token if present
                if "session_token" in data:
                    tokens["X-Directory-Token"] = data["session_token"]
                
                # Check for directory token in cookies
                cookies = response.cookies
                if "directory_token" in cookies:
                    tokens["X-Directory-Token"] = cookies["directory_token"]
                
                # Get portals from user object
                user = data.get("user", {})
                portals = user.get("portals", [])
                has_admin = "admin" in portals
                
                if has_admin and tokens:
                    log_test(
                        "1. Admin Authentication",
                        "PASS",
                        f"Authenticated successfully. Portals: {portals}. Tokens received: {list(tokens.keys())}"
                    )
                    return tokens
                elif has_admin:
                    log_test(
                        "1. Admin Authentication",
                        "FAIL",
                        f"Admin portal granted but no tokens received. Response: {json.dumps(data, indent=2)}"
                    )
                    return None
                else:
                    log_test(
                        "1. Admin Authentication",
                        "FAIL",
                        f"Admin portal not granted. Portals: {portals}"
                    )
                    return None
            else:
                log_test(
                    "1. Admin Authentication",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return None
    except Exception as e:
        log_test("1. Admin Authentication", "FAIL", f"Exception: {str(e)}")
        return None


async def test_pm_login() -> Optional[Dict[str, str]]:
    """Test 3: PM authentication through /api/auth/multi-login"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.post(
                f"{API_BASE}/auth/multi-login",
                json={
                    "email": PM_EMAIL,
                    "password": PM_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract tokens from response (new structure: portal_tokens)
                tokens = {}
                portal_tokens = data.get("portal_tokens", {})
                if "pm" in portal_tokens:
                    tokens["X-PM-Token"] = portal_tokens["pm"]
                
                # Add session token if present
                if "session_token" in data:
                    tokens["X-Directory-Token"] = data["session_token"]
                
                # Check for directory token in cookies
                cookies = response.cookies
                if "directory_token" in cookies:
                    tokens["X-Directory-Token"] = cookies["directory_token"]
                
                # Get portals from user object
                user = data.get("user", {})
                portals = user.get("portals", [])
                has_pm = "pm" in portals
                
                if has_pm and tokens:
                    log_test(
                        "3. PM Authentication",
                        "PASS",
                        f"Authenticated successfully. Portals: {portals}. Tokens received: {list(tokens.keys())}"
                    )
                    return tokens
                elif has_pm:
                    log_test(
                        "3. PM Authentication",
                        "FAIL",
                        f"PM portal granted but no tokens received. Response: {json.dumps(data, indent=2)}"
                    )
                    return None
                else:
                    log_test(
                        "3. PM Authentication",
                        "FAIL",
                        f"PM portal not granted. Portals: {portals}"
                    )
                    return None
            else:
                log_test(
                    "3. PM Authentication",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return None
    except Exception as e:
        log_test("3. PM Authentication", "FAIL", f"Exception: {str(e)}")
        return None


async def test_admin_command_center_api(admin_tokens: Dict[str, str]):
    """Test 2a: Admin can access PM command center APIs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/command-center/overview",
                headers=admin_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                # Overview returns a dict with KPIs, not a list
                active_trucks = data.get("active_trucks", 0)
                active_drivers = data.get("active_drivers", 0)
                log_test(
                    "2a. Admin → PM Command Center API",
                    "PASS",
                    f"Overview: {active_trucks} trucks, {active_drivers} drivers"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "2a. Admin → PM Command Center API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "2a. Admin → PM Command Center API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("2a. Admin → PM Command Center API", "FAIL", f"Exception: {str(e)}")
        return False


async def test_admin_executive_overview_api(admin_tokens: Dict[str, str]):
    """Test 2b: Admin can access executive overview APIs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/project-controls/portfolio-intelligence",
                headers=admin_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                project_count = len(data) if isinstance(data, list) else 0
                log_test(
                    "2b. Admin → Executive Overview API",
                    "PASS",
                    f"Retrieved {project_count} projects"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "2b. Admin → Executive Overview API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "2b. Admin → Executive Overview API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("2b. Admin → Executive Overview API", "FAIL", f"Exception: {str(e)}")
        return False


async def test_admin_jobs_api(admin_tokens: Dict[str, str]):
    """Test 2c: Admin can access PM jobs API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/jobs",
                headers=admin_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                job_count = len(data) if isinstance(data, list) else 0
                log_test(
                    "2c. Admin → PM Jobs API",
                    "PASS",
                    f"Retrieved {job_count} jobs"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "2c. Admin → PM Jobs API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "2c. Admin → PM Jobs API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("2c. Admin → PM Jobs API", "FAIL", f"Exception: {str(e)}")
        return False


async def test_version_endpoint(admin_tokens: Dict[str, str]):
    """Test 2d: Check version/release identity endpoint"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/version",
                headers=admin_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                source_hash = data.get("source_hash", "unknown")[:8]
                log_test(
                    "2d. Version/Release Identity",
                    "PASS",
                    f"Version: {version}, Source: {source_hash}"
                )
                return True
            else:
                log_test(
                    "2d. Version/Release Identity",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("2d. Version/Release Identity", "FAIL", f"Exception: {str(e)}")
        return False


async def test_pm_command_center_api(pm_tokens: Dict[str, str]):
    """Test 4a: PM can access command center APIs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/command-center/overview",
                headers=pm_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                # Overview returns a dict with KPIs, not a list
                active_trucks = data.get("active_trucks", 0)
                active_drivers = data.get("active_drivers", 0)
                log_test(
                    "4a. PM → Command Center API",
                    "PASS",
                    f"Overview: {active_trucks} trucks, {active_drivers} drivers"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "4a. PM → Command Center API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "4a. PM → Command Center API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("4a. PM → Command Center API", "FAIL", f"Exception: {str(e)}")
        return False


async def test_pm_jobs_api(pm_tokens: Dict[str, str]):
    """Test 4b: PM can access jobs API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/jobs",
                headers=pm_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                job_count = len(data) if isinstance(data, list) else 0
                log_test(
                    "4b. PM → Jobs API",
                    "PASS",
                    f"Retrieved {job_count} jobs (PM-scoped)"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "4b. PM → Jobs API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "4b. PM → Jobs API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("4b. PM → Jobs API", "FAIL", f"Exception: {str(e)}")
        return False


async def test_pm_operational_intelligence_api(pm_tokens: Dict[str, str]):
    """Test 4c: PM can access operational intelligence APIs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/pm/project-controls/portfolio-intelligence",
                headers=pm_tokens
            )
            
            if response.status_code == 200:
                data = response.json()
                project_count = len(data) if isinstance(data, list) else 0
                log_test(
                    "4c. PM → Operational Intelligence API",
                    "PASS",
                    f"Retrieved {project_count} projects"
                )
                return True
            elif response.status_code == 403:
                log_test(
                    "4c. PM → Operational Intelligence API",
                    "FAIL",
                    f"403 Forbidden - Auth regression detected. Response: {response.text[:200]}"
                )
                return False
            else:
                log_test(
                    "4c. PM → Operational Intelligence API",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        log_test("4c. PM → Operational Intelligence API", "FAIL", f"Exception: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("=" * 80)
    print("WP-18C9 Frozen Closeout Backend Verification")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    print()
    
    # Test 1: Admin authentication
    print("Test 1: Admin Authentication")
    print("-" * 80)
    admin_tokens = await test_admin_login()
    print()
    
    if admin_tokens:
        # Test 2: Admin can access core C9 admin surfaces
        print("Test 2: Admin Access to Core C9 Admin Surfaces")
        print("-" * 80)
        await test_admin_command_center_api(admin_tokens)
        await test_admin_executive_overview_api(admin_tokens)
        await test_admin_jobs_api(admin_tokens)
        await test_version_endpoint(admin_tokens)
        print()
    else:
        print("⚠️  Skipping admin API tests (authentication failed)")
        print()
    
    # Test 3: PM authentication
    print("Test 3: PM Authentication")
    print("-" * 80)
    pm_tokens = await test_pm_login()
    print()
    
    if pm_tokens:
        # Test 4: PM can access PM operational APIs
        print("Test 4: PM Access to Operational Intelligence APIs")
        print("-" * 80)
        await test_pm_command_center_api(pm_tokens)
        await test_pm_jobs_api(pm_tokens)
        await test_pm_operational_intelligence_api(pm_tokens)
        print()
    else:
        print("⚠️  Skipping PM API tests (authentication failed)")
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(results['tests'])}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print()
    
    # Save results to file
    with open("/app/wp18c9_backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to: /app/wp18c9_backend_test_results.json")
    print()
    
    # Exit code
    if results['summary']['failed'] > 0:
        print("❌ OVERALL STATUS: FAIL - Some tests failed")
        sys.exit(1)
    else:
        print("✅ OVERALL STATUS: PASS - All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
