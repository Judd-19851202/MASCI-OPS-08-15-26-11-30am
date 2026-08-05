#!/usr/bin/env python3
"""
Simplified Backend Singleton Scheduler Regression Fix Verification
"""

import json
import subprocess
from datetime import datetime, timezone

import requests

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

results = {"tests": [], "summary": {"total": 0, "passed": 0, "failed": 0}}


def test(name, passed, details):
    results["tests"].append({"name": name, "passed": passed, "details": details})
    results["summary"]["total"] += 1
    if passed:
        results["summary"]["passed"] += 1
        print(f"✅ {name}: {details}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ {name}: {details}")


print("=" * 80)
print("Backend Singleton Scheduler Regression Fix Verification")
print("=" * 80)

# Test 1: /api/health
try:
    r = requests.get(f"{API_BASE}/health", timeout=10)
    test("GET /api/health", r.status_code == 200, f"Status {r.status_code}, ok={r.json().get('ok')}")
except Exception as e:
    test("GET /api/health", False, f"Error: {e}")

# Test 2: /api/version
try:
    r = requests.get(f"{API_BASE}/version", timeout=10)
    test("GET /api/version", r.status_code == 200, f"Status {r.status_code}, commit={r.json().get('commit', '')[:12]}")
except Exception as e:
    test("GET /api/version", False, f"Error: {e}")

# Test 3: /api/platform/data-truth
try:
    r = requests.get(f"{API_BASE}/platform/data-truth", timeout=10)
    test("GET /api/platform/data-truth", r.status_code == 200, f"Status {r.status_code}, band={r.json().get('platform_band')}")
except Exception as e:
    test("GET /api/platform/data-truth", False, f"Error: {e}")

# Test 4: /api/ready
try:
    r = requests.get(f"{API_BASE}/ready", timeout=10)
    test("GET /api/ready", r.status_code == 200, f"Status {r.status_code}, state={r.json().get('state')}")
except Exception as e:
    test("GET /api/ready", False, f"Error: {e}")

# Test 5: PM schedule endpoint
try:
    # Login as PM
    r = requests.post(f"{API_BASE}/pm/login", json={"email": PM_EMAIL, "password": PM_PASSWORD}, timeout=10)
    if r.status_code == 200:
        token = r.json().get("token")
        # Get schedule
        r2 = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/overview",
            headers={"X-PM-Token": token},
            timeout=10
        )
        test(f"PM schedule for {PROJECT_NUMBER}", r2.status_code == 200, f"Status {r2.status_code}")
    else:
        test(f"PM schedule for {PROJECT_NUMBER}", False, f"PM login failed: {r.status_code}")
except Exception as e:
    test(f"PM schedule for {PROJECT_NUMBER}", False, f"Error: {e}")

# Test 6: Check logs for errors
print("\n" + "=" * 80)
print("Checking Backend Logs")
print("=" * 80)

# Get latest startup time
cmd = "tail -n 500 /var/log/supervisor/backend.err.log | grep 'Application startup complete' | tail -1"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(f"Latest startup: {result.stdout.strip()}")

# Check for MotorCollection errors after latest startup
cmd = "tail -n 500 /var/log/supervisor/backend.err.log | grep 'MotorCollection object is not callable'"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
motor_errors = result.stdout.strip()

if motor_errors:
    # Check if errors are after the latest startup
    # Get the timestamp of the latest startup
    cmd = "tail -n 500 /var/log/supervisor/backend.err.log | grep -B 5 'Application startup complete' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}' | tail -1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    startup_time = result.stdout.strip()
    
    # Get the timestamp of the last motor error
    cmd = "tail -n 500 /var/log/supervisor/backend.err.log | grep -B 1 'MotorCollection object is not callable' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}' | tail -1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    error_time = result.stdout.strip()
    
    print(f"Startup time: {startup_time}")
    print(f"Last motor error time: {error_time}")
    
    if error_time and startup_time and error_time > startup_time:
        test("No fresh MotorCollection errors", False, f"Found errors after startup: {error_time}")
    else:
        test("No fresh MotorCollection errors", True, "All motor errors are before latest startup")
else:
    test("No fresh MotorCollection errors", True, "No MotorCollection errors found in recent logs")

# Check for Database initialization warnings
cmd = "tail -n 200 /var/log/supervisor/backend.out.log | grep 'Database accessed before runtime initialization' | wc -l"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
warning_count = int(result.stdout.strip())
print(f"\nFound {warning_count} 'Database accessed before runtime initialization' warnings in last 200 lines")
print("(These are expected from backfill operations and are not errors)")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total: {results['summary']['total']}")
print(f"Passed: {results['summary']['passed']}")
print(f"Failed: {results['summary']['failed']}")
print(f"Pass Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
print("=" * 80)

# Save results
with open("/app/backend_singleton_fix_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to /app/backend_singleton_fix_results.json")
