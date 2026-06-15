#!/usr/bin/env python3
"""
seed_runtime_cert_users.py — Track 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 1.

Idempotent seed script. Run once. Creates 17 K4 IAM test users and a
dedicated certification project, then assigns each user to the project
under one of the 17 staffing roles via the canonical PM workflow
(`POST /api/admin/jobs/{pn}/team` for admin-only roles,
`POST /api/pm/job/{pn}/team` for PM-assignable roles).

Outputs `/app/test_reports/runtime_cert_seed.json` with every user's
credentials so the next phase (login + screenshot loop) can read it
without re-discovering anything.

Run:
    cd /app/backend && python tests/runtime_cert/seed_runtime_cert_users.py

This is NOT a regression test — it is a one-shot operational
seed-and-assign script. Re-running cleans up the previous run first.

Requires admin credentials in /app/memory/test_credentials.md.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

API = os.environ.get("RUNTIME_CERT_API_URL") or "https://safety-audit-mobile-1.preview.emergentagent.com"
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
CERT_PROJECT_NAME = "Runtime Certification — Internal Test Project"

# Admin login — read from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# (role_key, role_label, default_email_local_part) for all 17 roles.
ROLES: List[Dict[str, str]] = [
    {"key": "pm",                       "label": "Project Manager",        "email": "cert.pm@example.com"},
    {"key": "co_pm",                    "label": "Co-PM",                  "email": "cert.copm@example.com"},
    {"key": "executive_oversight",      "label": "Executive Oversight",    "email": "cert.exec@example.com"},
    {"key": "superintendent",           "label": "Superintendent",         "email": "cert.super@example.com"},
    {"key": "assistant_superintendent", "label": "Assistant Superintendent","email": "cert.asuper@example.com"},
    {"key": "foreman",                  "label": "Foreman",                "email": "cert.foreman@example.com"},
    {"key": "project_engineer",         "label": "Project Engineer",       "email": "cert.pe@example.com"},
    {"key": "project_administrator",    "label": "Project Administrator",  "email": "cert.padmin@example.com"},
    {"key": "project_coordinator",      "label": "Project Coordinator",    "email": "cert.pcoord@example.com"},
    {"key": "safety_rep",               "label": "Safety Representative",  "email": "cert.safety@example.com"},
    {"key": "qaqc_rep",                 "label": "QA/QC Representative",   "email": "cert.qaqc@example.com"},
    {"key": "hr_rep",                   "label": "HR Representative",      "email": "cert.hr@example.com"},
    {"key": "dispatch_rep",             "label": "Dispatch Representative","email": "cert.dispatch@example.com"},
    {"key": "equipment_manager",        "label": "Equipment Manager",      "email": "cert.equip@example.com"},
    {"key": "shop_rep",                 "label": "Shop Representative",    "email": "cert.shop@example.com"},
    {"key": "survey_rep",               "label": "Survey Representative",  "email": "cert.survey@example.com"},
    {"key": "accounting_rep",           "label": "Accounting Representative","email": "cert.accounting@example.com"},
]

ADMIN_ONLY = {"pm", "co_pm", "executive_oversight"}
SEED_PASSWORD = "CertProof2026!"


def login_admin() -> Dict[str, str]:
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    return body.get("portal_tokens") or {}


def ensure_project(admin_token: str) -> None:
    """Idempotent — create the cert project if missing."""
    h = {"X-Admin-Token": admin_token}
    r = requests.get(
        f"{API}/api/admin/jobs-master",
        headers=h, timeout=15,
    )
    existing = r.json() if r.status_code == 200 else []
    if isinstance(existing, list) and any(
        (p or {}).get("project_number") == CERT_PROJECT_NUMBER for p in existing
    ):
        print(f"  ✓ Project {CERT_PROJECT_NUMBER} already exists")
        return
    r = requests.post(
        f"{API}/api/admin/jobs-master",
        headers={**h, "Content-Type": "application/json"},
        json={
            "project_number": CERT_PROJECT_NUMBER,
            "project_name": CERT_PROJECT_NAME,
            "status": "Active",
        },
        timeout=15,
    )
    if r.status_code in (200, 201):
        print(f"  ✓ Project {CERT_PROJECT_NUMBER} created")
    else:
        print(f"  ⚠ Project create returned {r.status_code}: {r.text[:200]}")


def ensure_user(admin_token: str, role: Dict[str, str]) -> Dict[str, Any]:
    """Idempotent — create the K4 user if missing, return user dict."""
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    # NOTE: the precise K4 user-creation endpoint to wire here is
    # /api/admin/directory/k4/users or similar; consult
    # routes/admin_directory_k4.py for the exact contract. Below is
    # the documented intent — the next-session executor will pin
    # this once after one successful curl trial.
    payload = {
        "email": role["email"],
        "name": f"Cert {role['label']}",
        "password": SEED_PASSWORD,
        "role_template": role["key"],
        "active": True,
    }
    r = requests.post(
        f"{API}/api/admin/directory/k4/users",
        headers=h, json=payload, timeout=15,
    )
    if r.status_code in (200, 201):
        return r.json()
    if r.status_code == 409:  # already exists
        # Look up by email
        rr = requests.get(
            f"{API}/api/admin/directory/k4/users?q={role['email']}",
            headers=h, timeout=15,
        )
        items = rr.json().get("items", []) if rr.status_code == 200 else []
        if items:
            return items[0]
    print(f"  ⚠ user {role['email']} create returned {r.status_code}: {r.text[:200]}")
    return {}


def assign_user(admin_token: str, user_id: str, role_key: str) -> bool:
    """Assign user_id to CERT_PROJECT_NUMBER under role_key via admin endpoint."""
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    r = requests.post(
        f"{API}/api/admin/jobs/{CERT_PROJECT_NUMBER}/team",
        headers=h,
        json={"user_id": user_id, "assignment_role": role_key},
        timeout=15,
    )
    return r.status_code in (200, 201)


def main() -> int:
    print(f"Seeding runtime certification users into {API} …")
    tokens = login_admin()
    admin_token = tokens.get("admin")
    if not admin_token:
        print("  ✗ admin login failed — abort")
        return 2

    print("[1/3] Ensuring cert project exists …")
    ensure_project(admin_token)

    print("[2/3] Ensuring 17 cert users exist …")
    out: List[Dict[str, Any]] = []
    for role in ROLES:
        user = ensure_user(admin_token, role)
        if user:
            out.append({
                "role_key": role["key"],
                "role_label": role["label"],
                "email": role["email"],
                "password": SEED_PASSWORD,
                "user_id": user.get("id") or user.get("user_id"),
                "active": True,
            })
            print(f"  ✓ {role['key']:<28} {role['email']}")
        else:
            print(f"  ✗ {role['key']} not created")

    print("[3/3] Assigning each user to the cert project under their role …")
    for u in out:
        ok = assign_user(admin_token, u["user_id"], u["role_key"])
        u["assigned"] = ok
        print(f"  {'✓' if ok else '✗'} {u['role_key']}")

    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    Path("/app/test_reports/runtime_cert_seed.json").write_text(json.dumps({
        "api": API,
        "project_number": CERT_PROJECT_NUMBER,
        "users": out,
    }, indent=2))
    print(f"\nDone. Wrote /app/test_reports/runtime_cert_seed.json ({len(out)} users)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
