"""Ad-hoc survey: probe a broad set of Wave-4 touched GET endpoints and print
status + whether count/total are present and consistent."""
import json
import os
import sys

import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
BASE = (os.environ.get("REACT_APP_BACKEND_URL") or _env["REACT_APP_BACKEND_URL"]).rstrip("/")

s = requests.Session()


def login(email, pw):
    r = s.post(f"{BASE}/api/auth/multi-login", json={"email": email, "password": pw}, timeout=60)
    r.raise_for_status()
    return r.json()


sa = login("jaymn.judd@mascigc.com", "Maddix123!")
ADMIN = {"X-Admin-Token": sa["portal_tokens"]["admin"], "X-Directory-Token": sa["session_token"]}

PATHS = [
    "/api/equipment-master",
    "/api/promo-assets",
    "/api/asset-spine/assets",
    "/api/job-photos",
    "/api/operations/utilization-overview",
    "/api/equipment-status-board",
    "/api/trench-safety/excavations",
    "/api/trench-safety/pulse/overview",
    "/api/employee-records/records",
    "/api/employee-records/batches",
    "/api/jha-acknowledgements/compliance",
    "/api/suppliers",
    "/api/jobs",
    "/api/employees",
    "/api/admin/governance/audit",
    "/api/field-leadership/time-off/stats",
    "/api/transportation/fleet-adoption",
    "/api/trench-safety/reports/digest/history",
]

for p in PATHS:
    try:
        r = s.get(f"{BASE}{p}", headers=ADMIN, timeout=60)
    except Exception as e:  # noqa: BLE001
        print(f"{p}: EXC {e}")
        continue
    line = f"{r.status_code} {p}"
    if r.status_code == 200:
        try:
            d = r.json()
        except Exception:  # noqa: BLE001
            print(line + " (non-json)")
            continue
        if isinstance(d, dict):
            c, t = d.get("count"), d.get("total")
            items = d.get("items")
            line += f" count={c!r} total={t!r} len(items)={len(items) if isinstance(items, list) else None}"
            if isinstance(c, int) and isinstance(t, int) and t < c:
                line += "  <<< TOTAL<COUNT"
            line += f" keys={list(d)[:10]}"
        else:
            line += f" (list len={len(d)}) <<< BARE LIST"
    else:
        line += f" -> {r.text[:120]}"
    print(line)
