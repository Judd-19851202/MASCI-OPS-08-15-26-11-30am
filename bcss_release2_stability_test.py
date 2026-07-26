#!/usr/bin/env python3
"""
BCSS Release 2 Platform Survivability Program - Backend Runtime Stability Verification
Test bounded Preview backend runtime stability repair.

Scope: Backend only. Do NOT test frontend.
Focus: Health endpoints, manifest timeout prevention, supervisor stability, process stability.
"""

import requests
import time
import json
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://backup-forensics.preview.emergentagent.com"

def test_health_endpoint_stability():
    """
    Requirement 1: /api/health responds 10/10 times with HTTP 200 and ok=true
    """
    print("\n=== TEST 1: /api/health endpoint stability (10 cycles) ===")
    results = []
    
    for i in range(10):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/health", timeout=30)
            latency = time.time() - start
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("ok") == True
            
            results.append({
                "cycle": i + 1,
                "status_code": response.status_code,
                "ok": data.get("ok") if response.status_code == 200 else None,
                "latency_seconds": round(latency, 3),
                "success": success
            })
            
            print(f"  Cycle {i+1}/10: status={response.status_code}, ok={data.get('ok') if response.status_code == 200 else 'N/A'}, latency={latency:.3f}s - {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "cycle": i + 1,
                "error": str(e),
                "success": False
            })
            print(f"  Cycle {i+1}/10: ❌ FAIL - {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    pass_count = sum(1 for r in results if r.get("success"))
    max_latency = max(r.get("latency_seconds", 0) for r in results if "latency_seconds" in r)
    
    print(f"\n  RESULT: {pass_count}/10 cycles passed")
    print(f"  MAX LATENCY: {max_latency:.3f}s")
    
    return {
        "test": "health_endpoint_stability",
        "requirement": "/api/health responds 10/10 times with HTTP 200 and ok=true",
        "pass_count": pass_count,
        "total_count": 10,
        "max_latency_seconds": max_latency,
        "results": results,
        "verdict": "PASS" if pass_count == 10 else "FAIL"
    }


def test_healthz_endpoint_stability():
    """
    Requirement 2: /api/healthz responds 10/10 times with HTTP 200 and ok=true
    """
    print("\n=== TEST 2: /api/healthz endpoint stability (10 cycles) ===")
    results = []
    
    for i in range(10):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/healthz", timeout=30)
            latency = time.time() - start
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("ok") == True
            
            results.append({
                "cycle": i + 1,
                "status_code": response.status_code,
                "ok": data.get("ok") if response.status_code == 200 else None,
                "latency_seconds": round(latency, 3),
                "success": success
            })
            
            print(f"  Cycle {i+1}/10: status={response.status_code}, ok={data.get('ok') if response.status_code == 200 else 'N/A'}, latency={latency:.3f}s - {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "cycle": i + 1,
                "error": str(e),
                "success": False
            })
            print(f"  Cycle {i+1}/10: ❌ FAIL - {e}")
        
        time.sleep(0.5)
    
    pass_count = sum(1 for r in results if r.get("success"))
    max_latency = max(r.get("latency_seconds", 0) for r in results if "latency_seconds" in r)
    
    print(f"\n  RESULT: {pass_count}/10 cycles passed")
    print(f"  MAX LATENCY: {max_latency:.3f}s")
    
    return {
        "test": "healthz_endpoint_stability",
        "requirement": "/api/healthz responds 10/10 times with HTTP 200 and ok=true",
        "pass_count": pass_count,
        "total_count": 10,
        "max_latency_seconds": max_latency,
        "results": results,
        "verdict": "PASS" if pass_count == 10 else "FAIL"
    }


def test_ready_endpoint_stability():
    """
    Requirement 3: /api/ready responds 10/10 times with HTTP 200, ok=true, and state=ready
    """
    print("\n=== TEST 3: /api/ready endpoint stability (10 cycles) ===")
    results = []
    
    for i in range(10):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/ready", timeout=30)
            latency = time.time() - start
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("ok") == True and data.get("state") == "ready"
            
            results.append({
                "cycle": i + 1,
                "status_code": response.status_code,
                "ok": data.get("ok") if response.status_code == 200 else None,
                "state": data.get("state") if response.status_code == 200 else None,
                "latency_seconds": round(latency, 3),
                "success": success
            })
            
            print(f"  Cycle {i+1}/10: status={response.status_code}, ok={data.get('ok') if response.status_code == 200 else 'N/A'}, state={data.get('state') if response.status_code == 200 else 'N/A'}, latency={latency:.3f}s - {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "cycle": i + 1,
                "error": str(e),
                "success": False
            })
            print(f"  Cycle {i+1}/10: ❌ FAIL - {e}")
        
        time.sleep(0.5)
    
    pass_count = sum(1 for r in results if r.get("success"))
    max_latency = max(r.get("latency_seconds", 0) for r in results if "latency_seconds" in r)
    
    print(f"\n  RESULT: {pass_count}/10 cycles passed")
    print(f"  MAX LATENCY: {max_latency:.3f}s")
    
    return {
        "test": "ready_endpoint_stability",
        "requirement": "/api/ready responds 10/10 times with HTTP 200, ok=true, and state=ready",
        "pass_count": pass_count,
        "total_count": 10,
        "max_latency_seconds": max_latency,
        "results": results,
        "verdict": "PASS" if pass_count == 10 else "FAIL"
    }


def test_health_full_endpoint_stability():
    """
    Requirement 4: /api/health/full responds 10/10 times with HTTP 200, no timeout, 
    and preserves legacy boolean contract fields (ok, mongo, scheduler, backup_recent)
    """
    print("\n=== TEST 4: /api/health/full endpoint stability (10 cycles) ===")
    results = []
    
    for i in range(10):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/health/full", timeout=30)
            latency = time.time() - start
            
            success = response.status_code == 200
            if success:
                data = response.json()
                # Check legacy boolean contract fields
                has_ok = "ok" in data
                has_mongo = "mongo" in data
                has_scheduler = "scheduler" in data
                has_backup_recent = "backup_recent" in data
                
                success = has_ok and has_mongo and has_scheduler and has_backup_recent
            
            results.append({
                "cycle": i + 1,
                "status_code": response.status_code,
                "ok": data.get("ok") if response.status_code == 200 else None,
                "mongo": data.get("mongo") if response.status_code == 200 else None,
                "scheduler": data.get("scheduler") if response.status_code == 200 else None,
                "backup_recent": data.get("backup_recent") if response.status_code == 200 else None,
                "latency_seconds": round(latency, 3),
                "success": success
            })
            
            print(f"  Cycle {i+1}/10: status={response.status_code}, ok={data.get('ok') if response.status_code == 200 else 'N/A'}, mongo={data.get('mongo') if response.status_code == 200 else 'N/A'}, scheduler={data.get('scheduler') if response.status_code == 200 else 'N/A'}, backup_recent={data.get('backup_recent') if response.status_code == 200 else 'N/A'}, latency={latency:.3f}s - {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "cycle": i + 1,
                "error": str(e),
                "success": False
            })
            print(f"  Cycle {i+1}/10: ❌ FAIL - {e}")
        
        time.sleep(0.5)
    
    pass_count = sum(1 for r in results if r.get("success"))
    max_latency = max(r.get("latency_seconds", 0) for r in results if "latency_seconds" in r)
    
    print(f"\n  RESULT: {pass_count}/10 cycles passed")
    print(f"  MAX LATENCY: {max_latency:.3f}s")
    
    return {
        "test": "health_full_endpoint_stability",
        "requirement": "/api/health/full responds 10/10 times with HTTP 200, no timeout, and preserves legacy boolean contract fields",
        "pass_count": pass_count,
        "total_count": 10,
        "max_latency_seconds": max_latency,
        "results": results,
        "verdict": "PASS" if pass_count == 10 else "FAIL"
    }


def main():
    print("=" * 80)
    print("BCSS RELEASE 2 PLATFORM SURVIVABILITY PROGRAM")
    print("Backend Runtime Stability Verification")
    print("=" * 80)
    print(f"\nTarget: {BASE_URL}")
    print(f"Test Start: {datetime.utcnow().isoformat()}Z")
    
    all_results = {}
    
    # Run all endpoint stability tests
    all_results["test1_health"] = test_health_endpoint_stability()
    all_results["test2_healthz"] = test_healthz_endpoint_stability()
    all_results["test3_ready"] = test_ready_endpoint_stability()
    all_results["test4_health_full"] = test_health_full_endpoint_stability()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for test_key, result in all_results.items():
        verdict = result.get("verdict", "UNKNOWN")
        pass_count = result.get("pass_count", 0)
        total_count = result.get("total_count", 0)
        max_latency = result.get("max_latency_seconds", 0)
        
        status_icon = "✅" if verdict == "PASS" else "❌"
        print(f"{status_icon} {result['test']}: {pass_count}/{total_count} cycles passed, max latency {max_latency:.3f}s - {verdict}")
    
    # Overall verdict
    all_passed = all(r.get("verdict") == "PASS" for r in all_results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ OVERALL VERDICT: PASS - All endpoint stability tests passed")
    else:
        print("❌ OVERALL VERDICT: FAIL - Some endpoint stability tests failed")
    print("=" * 80)
    
    # Save results
    output_file = "/app/bcss_release2_stability_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "test_start": datetime.utcnow().isoformat() + "Z",
            "target": BASE_URL,
            "overall_verdict": "PASS" if all_passed else "FAIL",
            "tests": all_results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
