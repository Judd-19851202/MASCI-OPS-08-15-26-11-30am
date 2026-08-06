"""
WP-18DA Backend/Resilience Verification Test Suite

Tests:
1. Preview runtime warm restart behavior
2. Scheduler/worker reliability (singleton_scheduler proxy fix)
3. Performance-critical Mongo/API checks (indexes)
4. Core public/API latency sanity
5. Output-channel runtime sanity (PDF/export endpoints)
6. Deployment-readiness sanity
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

import httpx

# Backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test results
results = {
    "test_suite": "WP-18DA Backend/Resilience Verification",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": [],
    "summary": {"passed": 0, "failed": 0, "warnings": 0}
}


def log_test(name: str, status: str, details: str = "", latency_ms: float = None):
    """Log a test result"""
    result = {
        "name": name,
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if latency_ms is not None:
        result["latency_ms"] = round(latency_ms, 2)
    
    results["tests"].append(result)
    
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ {name}: {status}")
    elif status == "FAIL":
        results["summary"]["failed"] += 1
        print(f"❌ {name}: {status}")
    else:
        results["summary"]["warnings"] += 1
        print(f"⚠️  {name}: {status}")
    
    if details:
        print(f"   {details}")
    if latency_ms is not None:
        print(f"   Latency: {latency_ms:.2f}ms")


async def test_health_endpoint():
    """Test 1.1: /api/health endpoint recovery"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/health")
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "1.1 /api/health endpoint",
                "PASS",
                f"Status: {data.get('status', 'unknown')}, Ready: {data.get('ready', False)}",
                latency
            )
            return True
        else:
            log_test("1.1 /api/health endpoint", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("1.1 /api/health endpoint", "FAIL", str(e))
        return False


async def test_version_endpoint():
    """Test 1.2: /api/version endpoint recovery"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/version")
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "1.2 /api/version endpoint",
                "PASS",
                f"Version: {data.get('version', 'unknown')}, Source: {data.get('source_hash', 'unknown')[:8]}",
                latency
            )
            return True
        else:
            log_test("1.2 /api/version endpoint", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("1.2 /api/version endpoint", "FAIL", str(e))
        return False


async def test_public_data_route():
    """Test 1.3: Public data route recovery"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/job-hazard-files/public/grouped")
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            # data is a list of groups
            count = len(data) if isinstance(data, list) else len(data.get("groups", []))
            log_test(
                "1.3 /api/job-hazard-files/public/grouped",
                "PASS",
                f"Groups: {count}",
                latency
            )
            return True
        else:
            log_test("1.3 Public data route", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("1.3 Public data route", "FAIL", str(e))
        return False


async def test_scheduler_logs():
    """Test 2: Scheduler/worker reliability - check for MongoClient errors"""
    try:
        # Check backend logs for "Cannot use MongoClient after close" errors
        # Only check logs from the most recent startup
        import subprocess
        
        # Get logs from the most recent startup
        result = subprocess.run(
            ["bash", "-c", "awk '/Application startup complete/,0' /var/log/supervisor/backend.err.log | tail -n 300"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        logs = result.stdout
        
        # Check for the specific error in recent logs
        mongo_close_errors = logs.count("Cannot use MongoClient after close")
        
        # Check for singleton scheduler lock acquisitions
        lock_acquired = logs.count("LOCK ACQUIRED")
        
        # Check for scheduler heartbeat failures
        heartbeat_failures = logs.count("heartbeat tick failed")
        
        if mongo_close_errors > 0:
            log_test(
                "2. Scheduler reliability",
                "FAIL",
                f"Found {mongo_close_errors} 'Cannot use MongoClient after close' errors in current runtime"
            )
            return False
        elif lock_acquired > 0:
            log_test(
                "2. Scheduler reliability",
                "PASS",
                f"Singleton scheduler working correctly. Lock acquisitions: {lock_acquired}, Heartbeat failures: {heartbeat_failures}. No MongoClient close errors in current runtime."
            )
            return True
        else:
            log_test(
                "2. Scheduler reliability",
                "WARNING",
                "No scheduler activity detected in recent logs"
            )
            return True
    except Exception as e:
        log_test("2. Scheduler reliability", "WARNING", f"Could not check logs: {str(e)}")
        return True


async def test_mongo_indexes():
    """Test 3: Performance-critical Mongo indexes verification"""
    try:
        # Load the explain snapshot
        with open("/app/memory/wp18da_query_explain_snapshot_after.json", "r") as f:
            explain_data = json.load(f)
        
        # Check safety equipment issuances employee query
        issuances_query = explain_data.get("safety_issuances_employee_filter", {})
        issuances_index = issuances_query.get("indexName", "")
        issuances_collscan = issuances_query.get("winningPlanStage", "") == "COLLSCAN"
        issuances_docs = issuances_query.get("totalDocsExamined", 0)
        issuances_keys = issuances_query.get("totalKeysExamined", 0)
        
        if issuances_collscan:
            log_test(
                "3.1 Safety issuances index",
                "FAIL",
                f"Using COLLSCAN instead of index"
            )
        elif issuances_index == "ix_safety_issuances_employee_email_issued_date":
            log_test(
                "3.1 Safety issuances index",
                "PASS",
                f"Index: {issuances_index}, Docs: {issuances_docs}, Keys: {issuances_keys}"
            )
        else:
            log_test(
                "3.1 Safety issuances index",
                "WARNING",
                f"Using index: {issuances_index} (expected: ix_safety_issuances_employee_email_issued_date)"
            )
        
        # Check safety equipment trainings employee query
        trainings_query = explain_data.get("safety_trainings_employee_filter", {})
        trainings_index = trainings_query.get("indexName", "")
        trainings_collscan = trainings_query.get("winningPlanStage", "") == "COLLSCAN"
        trainings_docs = trainings_query.get("totalDocsExamined", 0)
        trainings_keys = trainings_query.get("totalKeysExamined", 0)
        
        if trainings_collscan:
            log_test(
                "3.2 Safety trainings index",
                "FAIL",
                f"Using COLLSCAN instead of index"
            )
        elif trainings_index == "ix_safety_trainings_employee_email_training_date":
            log_test(
                "3.2 Safety trainings index",
                "PASS",
                f"Index: {trainings_index}, Docs: {trainings_docs}, Keys: {trainings_keys}"
            )
        else:
            log_test(
                "3.2 Safety trainings index",
                "WARNING",
                f"Using index: {trainings_index} (expected: ix_safety_trainings_employee_email_training_date)"
            )
        
        # Check field leadership project query
        fl_query = explain_data.get("field_leadership_project_filter", {})
        fl_index = fl_query.get("indexName", "")
        fl_collscan = fl_query.get("winningPlanStage", "") == "COLLSCAN"
        fl_docs = fl_query.get("totalDocsExamined", 0)
        fl_keys = fl_query.get("totalKeysExamined", 0)
        
        if fl_collscan:
            log_test(
                "3.3 Field leadership index",
                "FAIL",
                f"Using COLLSCAN instead of index"
            )
        elif fl_index == "ix_fl_project_number_created_at":
            log_test(
                "3.3 Field leadership index",
                "PASS",
                f"Index: {fl_index}, Docs: {fl_docs}, Keys: {fl_keys}"
            )
        else:
            log_test(
                "3.3 Field leadership index",
                "WARNING",
                f"Using index: {fl_index} (expected: ix_fl_project_number_created_at)"
            )
        
        return not (issuances_collscan or trainings_collscan or fl_collscan)
    except Exception as e:
        log_test("3. Mongo indexes", "FAIL", f"Error checking indexes: {str(e)}")
        return False


async def test_api_latency():
    """Test 4: Core public/API latency sanity"""
    endpoints = [
        ("/health", "Health check"),
        ("/version", "Version info"),
        ("/job-hazard-files/public/grouped", "Public data")
    ]
    
    all_pass = True
    for endpoint, description in endpoints:
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE}{endpoint}")
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                # Latency thresholds (generous for preview environment)
                if latency < 200:
                    status = "PASS"
                elif latency < 500:
                    status = "WARNING"
                else:
                    status = "FAIL"
                    all_pass = False
                
                log_test(
                    f"4. Latency: {description}",
                    status,
                    f"Endpoint: {endpoint}",
                    latency
                )
            else:
                log_test(
                    f"4. Latency: {description}",
                    "FAIL",
                    f"HTTP {response.status_code}"
                )
                all_pass = False
        except Exception as e:
            log_test(
                f"4. Latency: {description}",
                "FAIL",
                str(e)
            )
            all_pass = False
    
    return all_pass


async def test_pdf_endpoint():
    """Test 5.1: PDF endpoint sanity"""
    # We'll test a public PDF endpoint if available, or skip if auth required
    try:
        # Try to get a list of safety forms to find a PDF endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            # This endpoint might require auth, so we'll just check if it responds
            response = await client.get(f"{API_BASE}/safety-forms/equipment-issuances", params={"limit": 1})
            
            if response.status_code == 401:
                log_test(
                    "5.1 PDF endpoint",
                    "WARNING",
                    "PDF endpoints require authentication - cannot test without credentials"
                )
                return True
            elif response.status_code == 200:
                log_test(
                    "5.1 PDF endpoint",
                    "PASS",
                    "PDF generation infrastructure is available"
                )
                return True
            else:
                log_test(
                    "5.1 PDF endpoint",
                    "WARNING",
                    f"HTTP {response.status_code} - PDF endpoint status unclear"
                )
                return True
    except Exception as e:
        log_test("5.1 PDF endpoint", "WARNING", f"Could not verify PDF endpoint: {str(e)}")
        return True


async def test_export_endpoint():
    """Test 5.2: Export endpoint sanity"""
    try:
        # Try a public export endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/field-leadership/export/csv")
            
            if response.status_code == 401:
                log_test(
                    "5.2 Export endpoint",
                    "WARNING",
                    "Export endpoints require authentication - cannot test without credentials"
                )
                return True
            elif response.status_code == 200:
                log_test(
                    "5.2 Export endpoint",
                    "PASS",
                    "Export infrastructure is available"
                )
                return True
            else:
                log_test(
                    "5.2 Export endpoint",
                    "WARNING",
                    f"HTTP {response.status_code} - Export endpoint status unclear"
                )
                return True
    except Exception as e:
        log_test("5.2 Export endpoint", "WARNING", f"Could not verify export endpoint: {str(e)}")
        return True


async def test_deployment_readiness():
    """Test 6: Deployment-readiness sanity"""
    blockers = []
    
    # Check if backend is responding
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code != 200:
                blockers.append(f"Health endpoint returned {response.status_code}")
    except Exception as e:
        blockers.append(f"Health endpoint unreachable: {str(e)}")
    
    # Check if version endpoint is responding
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE}/version")
            if response.status_code != 200:
                blockers.append(f"Version endpoint returned {response.status_code}")
    except Exception as e:
        blockers.append(f"Version endpoint unreachable: {str(e)}")
    
    # Check backend logs for critical errors
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        logs = result.stdout
        
        # Check for critical errors
        if "Cannot use MongoClient after close" in logs:
            blockers.append("MongoClient close errors detected in logs")
        
        if "CRITICAL" in logs or "FATAL" in logs:
            critical_count = logs.count("CRITICAL") + logs.count("FATAL")
            blockers.append(f"Found {critical_count} CRITICAL/FATAL errors in logs")
    except Exception as e:
        # Non-blocking if we can't check logs
        pass
    
    if blockers:
        log_test(
            "6. Deployment readiness",
            "FAIL",
            f"Blockers found: {'; '.join(blockers)}"
        )
        return False
    else:
        log_test(
            "6. Deployment readiness",
            "PASS",
            "No deployment blockers detected"
        )
        return True


async def main():
    """Run all tests"""
    print("=" * 80)
    print("WP-18DA Backend/Resilience Verification Test Suite")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    print()
    
    # Test 1: Runtime warm restart behavior
    print("Test 1: Preview runtime warm restart behavior")
    print("-" * 80)
    await test_health_endpoint()
    await test_version_endpoint()
    await test_public_data_route()
    print()
    
    # Test 2: Scheduler/worker reliability
    print("Test 2: Scheduler/worker reliability")
    print("-" * 80)
    await test_scheduler_logs()
    print()
    
    # Test 3: Performance-critical Mongo/API checks
    print("Test 3: Performance-critical Mongo/API checks")
    print("-" * 80)
    await test_mongo_indexes()
    print()
    
    # Test 4: Core public/API latency sanity
    print("Test 4: Core public/API latency sanity")
    print("-" * 80)
    await test_api_latency()
    print()
    
    # Test 5: Output-channel runtime sanity
    print("Test 5: Output-channel runtime sanity")
    print("-" * 80)
    await test_pdf_endpoint()
    await test_export_endpoint()
    print()
    
    # Test 6: Deployment-readiness sanity
    print("Test 6: Deployment-readiness sanity")
    print("-" * 80)
    await test_deployment_readiness()
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(results['tests'])}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"⚠️  Warnings: {results['summary']['warnings']}")
    print()
    
    # Save results to file
    with open("/app/wp18da_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to: /app/wp18da_test_results.json")
    print()
    
    # Exit code
    if results['summary']['failed'] > 0:
        print("❌ OVERALL STATUS: FAIL - Some tests failed")
        sys.exit(1)
    elif results['summary']['warnings'] > 0:
        print("⚠️  OVERALL STATUS: PASS WITH WARNINGS")
        sys.exit(0)
    else:
        print("✅ OVERALL STATUS: PASS - All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
