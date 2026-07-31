#!/usr/bin/env python3
"""
Detailed WP-16A Backend Verification - Check recovery snapshot for app_disk_pressure blockers
"""

import requests
import json

BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

# Login as admin
print("Logging in as admin...")
response = requests.post(
    f"{BACKEND_URL}/auth/multi-login",
    json=ADMIN_CREDS,
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    exit(1)

data = response.json()
admin_token = data["portal_tokens"]["admin"]
directory_token = data["session_token"]

print("✅ Login successful\n")

# Get recovery snapshot
print("Fetching /api/admin/recovery/snapshot...")
headers = {
    "X-Admin-Token": admin_token,
    "X-Directory-Token": directory_token
}

response = requests.get(
    f"{BACKEND_URL}/admin/recovery/snapshot",
    headers=headers,
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Recovery snapshot failed: {response.status_code}")
    exit(1)

data = response.json()

print("✅ Recovery snapshot retrieved\n")

# Check recent jobs for deferrals
recent_jobs = data.get("scheduler", {}).get("backup_runtime", {}).get("recent_complete_jobs", [])

print(f"Found {len(recent_jobs)} recent jobs\n")

deferred_jobs = [j for j in recent_jobs if j.get("state") == "deferred"]
print(f"Found {len(deferred_jobs)} deferred jobs\n")

# Check for app_disk_pressure blockers
app_disk_pressure_deferrals = []
for job in deferred_jobs:
    preflight = job.get("result", {}).get("preflight", {})
    reasons = preflight.get("reasons", [])
    tmp_free = preflight.get("tmp_disk_free_bytes", 0)
    min_required = preflight.get("min_free_bytes_required", 0)
    
    if any("app_disk_pressure" in r for r in reasons):
        app_disk_pressure_deferrals.append({
            "job_id": job.get("job_id"),
            "scheduled_at": job.get("scheduled_at"),
            "tmp_free_gb": round(tmp_free / (1024**3), 2),
            "min_required_gb": round(min_required / (1024**3), 2),
            "tmp_sufficient": tmp_free > min_required,
            "reasons": reasons,
            "result": job.get("result", {})
        })

if app_disk_pressure_deferrals:
    print(f"❌ ISSUE: Found {len(app_disk_pressure_deferrals)} jobs deferred due to app_disk_pressure:\n")
    for i, job in enumerate(app_disk_pressure_deferrals[:3], 1):  # Show first 3
        print(f"Job {i}:")
        print(f"  Job ID: {job['job_id']}")
        print(f"  Scheduled: {job['scheduled_at']}")
        print(f"  Tmp Free: {job['tmp_free_gb']} GB")
        print(f"  Min Required: {job['min_required_gb']} GB")
        print(f"  Tmp Sufficient: {job['tmp_sufficient']}")
        print(f"  Deferral Reasons: {job['reasons']}")
        print(f"  Result: {json.dumps(job['result'], indent=2)}")
        print()
else:
    print("✅ No jobs deferred due to app_disk_pressure when tmp headroom is sufficient")

# Check for resource_preflight_failed in hourly activation blockers
print("\n" + "="*80)
print("Checking hourly activation blockers...")
print("="*80 + "\n")

# Look for any mention of resource_preflight_failed or app_disk_pressure in activation blockers
snapshot_str = json.dumps(data)
if "resource_preflight_failed" in snapshot_str.lower():
    print("❌ Found 'resource_preflight_failed' in snapshot")
else:
    print("✅ No 'resource_preflight_failed' found in snapshot")

if "app_disk_pressure" in snapshot_str.lower() and len(app_disk_pressure_deferrals) > 0:
    print(f"❌ Found 'app_disk_pressure' in snapshot with {len(app_disk_pressure_deferrals)} deferred jobs")
else:
    print("✅ No problematic 'app_disk_pressure' blockers found")

print("\n" + "="*80)
print("Summary:")
print("="*80)
print(f"Total recent jobs: {len(recent_jobs)}")
print(f"Deferred jobs: {len(deferred_jobs)}")
print(f"Jobs deferred due to app_disk_pressure: {len(app_disk_pressure_deferrals)}")
print()

if len(app_disk_pressure_deferrals) > 0:
    print("❌ VERIFICATION FAILED: Backups are still being deferred due to app_disk_pressure")
    print("   even when tmp headroom is sufficient.")
    print(f"   Example: {app_disk_pressure_deferrals[0]['tmp_free_gb']}GB free vs {app_disk_pressure_deferrals[0]['min_required_gb']}GB required")
else:
    print("✅ VERIFICATION PASSED: No backups deferred due to app_disk_pressure when tmp is sufficient")
