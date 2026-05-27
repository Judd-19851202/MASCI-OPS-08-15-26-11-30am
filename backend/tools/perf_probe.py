"""Endpoint latency probe — Phase Sigma · Performance Forensics.

Calls a curated list of GET endpoints with the admin token, 5 samples each,
records p50/p99/max in milliseconds. Output: /tmp/perf_forensics.json.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

import requests

# Bootstrap env
for line in Path("/app/backend/.env").read_text().splitlines():
    if "=" not in line or line.strip().startswith("#"):
        continue
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

BASE = next(
    line.split("=", 1)[1].strip().strip('"')
    for line in Path("/app/frontend/.env").read_text().splitlines()
    if line.startswith("REACT_APP_BACKEND_URL")
)

# Login
r = requests.post(
    f"{BASE}/api/auth/multi-login",
    json={"email": os.environ["SUPER_ADMIN_EMAIL"], "password": os.environ["SUPER_ADMIN_BOOTSTRAP_PASSWORD"]},
    timeout=15,
)
tok = r.json()["portal_tokens"]


ENDPOINTS = [
    # path, header, label
    ("/api/health",                              None,                                 "health"),
    ("/api/version",                             None,                                 "version"),
    ("/api/cluster/capacity",                    None,                                 "cluster_capacity"),
    ("/api/employees",                           None,                                 "employees_public"),

    ("/api/admin/jobs",                          {"X-Admin-Token": tok["admin"]},      "admin_jobs"),
    ("/api/daily-reports",                       {"X-Admin-Token": tok["admin"]},      "daily_reports_list"),
    ("/api/incidents",                           {"X-Admin-Token": tok["admin"]},      "incidents_list"),
    ("/api/meetings",                            {"X-Admin-Token": tok["admin"]},      "meetings_list"),
    ("/api/inspections",                         {"X-Admin-Token": tok["admin"]},      "inspections_list"),
    ("/api/jhas",                                {"X-Admin-Token": tok["admin"]},      "jhas_list"),
    ("/api/equipment-inspections",               {"X-Admin-Token": tok["admin"]},      "equip_inspections_list"),
    ("/api/equipment-inspections?limit=1",       {"X-Admin-Token": tok["admin"]},      "equip_inspections_limit1"),
    ("/api/equipment-units",                     {"X-Admin-Token": tok["admin"]},      "equipment_units_admin"),

    ("/api/hr/me",                               {"X-HR-Token": tok["hr"]},            "hr_me"),
    ("/api/hr/time-verification",                {"X-HR-Token": tok["hr"]},            "hr_time_verif"),
    ("/api/hr/training-records",                 {"X-HR-Token": tok["hr"]},            "hr_training"),
    ("/api/hr/driver-qualification/dashboard",   {"X-HR-Token": tok["hr"]},            "hr_driver_qual"),

    ("/api/pm/me",                               {"X-PM-Token": tok["pm"]},            "pm_me"),
    ("/api/safety/me",                           {"X-Safety-Token": tok["safety"]},    "safety_me"),
    ("/api/shop/me",                             {"X-Shop-Token": tok["shop"]},        "shop_me"),
    ("/api/dispatch/me",                         {"X-Dispatch-Token": tok["dispatch"]}, "dispatch_me"),
    ("/api/field-leadership/portal/me",          {"X-FL-Token": tok["field_leadership"]}, "fl_me"),
    ("/api/field-leadership/portal/dispatch-today", {"X-FL-Token": tok["field_leadership"]}, "fl_dispatch_today"),
]


SAMPLES = 5
results = []
for path, headers, label in ENDPOINTS:
    times = []
    sizes = []
    statuses = set()
    for _ in range(SAMPLES):
        t0 = time.monotonic()
        r = requests.get(f"{BASE}{path}", headers=headers or {}, timeout=20)
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        times.append(elapsed_ms)
        sizes.append(len(r.content))
        statuses.add(r.status_code)
    times.sort()
    results.append({
        "label": label,
        "path": path,
        "status": sorted(statuses),
        "min_ms": int(min(times)),
        "p50_ms": int(statistics.median(times)),
        "p99_ms": int(times[-1]),
        "max_ms": int(max(times)),
        "avg_size_kb": int(statistics.mean(sizes) / 1024),
    })

results.sort(key=lambda x: -x["p50_ms"])

Path("/tmp/perf_forensics.json").write_text(json.dumps(results, indent=2))

# Print top 10 slowest
print(f"\n{'label':30s} {'p50':>6} {'p99':>6} {'max':>6} {'size_kb':>8} status path")
print("-" * 100)
for row in results:
    print(f"{row['label']:30s} {row['p50_ms']:>5}ms {row['p99_ms']:>5}ms {row['max_ms']:>5}ms {row['avg_size_kb']:>6}KB {row['status']} {row['path']}")
