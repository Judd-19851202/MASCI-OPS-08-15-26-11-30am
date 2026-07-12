#!/usr/bin/env python3
"""
seed_runtime_cert_users.py — Track 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 1+2.

Idempotent seed script. Creates 17 directory test users (one per
staffing role) and a dedicated certification project, then assigns
each user to the project under their canonical role via the real
admin staffing workflow (POST /api/admin/jobs/{pn}/team).

Outputs /app/test_reports/runtime_cert_seed.json with every user's
credentials so the next phase (login + screenshot loop) can read it
without re-discovering anything.

Endpoints used:
  - POST /api/auth/multi-login                       (admin auth)
  - GET  /api/admin/jobs-master                      (project list)
  - POST /api/admin/jobs-master                      (project create)
  - GET  /api/admin/directory                        (user list)
  - POST /api/admin/directory                        (user create)
  - POST /api/admin/directory/{user_id}/reset-password (password rotate
        — used to set a known password for already-created users)
  - POST /api/admin/jobs/{pn}/team                   (assignment)
  - GET  /api/admin/jobs/{pn}/team                   (verify)

Run:
    cd /app/backend && python3 tests/runtime_cert/seed_runtime_cert_users.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API = os.environ.get("RUNTIME_CERT_API_URL") or "https://backup-forensics.preview.emergentagent.com"
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
CERT_PROJECT_NAME = "Runtime Certification — Internal Test Project"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

SEED_PASSWORD = "CertProof2026!"

# Role → portal mapping (derived from PORTAL_EXPERIENCE_MATRIX.md +
# landingFor() in /app/frontend/src/lib/directoryAuth.js).
ROLES: List[Dict[str, Any]] = [
    {"key": "pm",                        "label": "Project Manager",          "email": "cert.pm@example.com",          "portals": ["pm"]},
    {"key": "co_pm",                     "label": "Co-PM",                    "email": "cert.copm@example.com",        "portals": ["pm"]},
    {"key": "executive_oversight",       "label": "Executive Oversight",      "email": "cert.exec@example.com",        "portals": ["pm"]},
    {"key": "superintendent",            "label": "Superintendent",           "email": "cert.super@example.com",       "portals": ["pm"]},
    {"key": "assistant_superintendent",  "label": "Assistant Superintendent", "email": "cert.asuper@example.com",      "portals": ["pm"]},
    {"key": "foreman",                   "label": "Foreman",                  "email": "cert.foreman@example.com",     "portals": ["field_leadership"]},
    {"key": "project_engineer",          "label": "Project Engineer",         "email": "cert.pe@example.com",          "portals": ["pm"]},
    {"key": "project_administrator",     "label": "Project Administrator",    "email": "cert.padmin@example.com",      "portals": ["pm"]},
    {"key": "project_coordinator",       "label": "Project Coordinator",      "email": "cert.pcoord@example.com",      "portals": ["pm"]},
    {"key": "safety_rep",                "label": "Safety Representative",    "email": "cert.safety@example.com",      "portals": ["safety"]},
    {"key": "qaqc_rep",                  "label": "QA/QC Representative",     "email": "cert.qaqc@example.com",        "portals": ["pm"]},
    {"key": "hr_rep",                    "label": "HR Representative",        "email": "cert.hr@example.com",          "portals": ["hr"]},
    {"key": "dispatch_rep",              "label": "Dispatch Representative",  "email": "cert.dispatch@example.com",    "portals": ["dispatch"]},
    {"key": "equipment_manager",         "label": "Equipment Manager",        "email": "cert.equip@example.com",       "portals": ["shop"]},
    {"key": "shop_rep",                  "label": "Shop Representative",      "email": "cert.shop@example.com",        "portals": ["shop"]},
    {"key": "survey_rep",                "label": "Survey Representative",    "email": "cert.survey@example.com",      "portals": ["pm"]},
    {"key": "accounting_rep",            "label": "Accounting Representative","email": "cert.accounting@example.com",  "portals": ["pm"]},
]


def login_admin() -> str:
    last = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{API}/api/auth/multi-login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=90,
            )
            r.raise_for_status()
            body = r.json()
            tokens = body.get("portal_tokens") or {}
            tok = tokens.get("admin")
            if not tok:
                raise RuntimeError(f"admin token not granted; portals={list(tokens)}")
            return tok
        except Exception as e:
            last = e
            print(f"  ⚠ login attempt {attempt+1}/3 failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"admin login failed after retries: {last}")


def ensure_project(admin_token: str) -> None:
    """Idempotent — create the cert project if missing via POST /api/admin/jobs."""
    h = {"X-Admin-Token": admin_token}
    r = requests.get(f"{API}/api/admin/jobs", headers=h, timeout=45)
    items: List[Dict[str, Any]] = []
    if r.status_code == 200:
        body = r.json()
        items = body if isinstance(body, list) else body.get("items") or body.get("jobs") or []
    if any((p or {}).get("project_number") == CERT_PROJECT_NUMBER for p in items):
        print(f"  ✓ project {CERT_PROJECT_NUMBER} already exists")
        return
    payload = {
        "project_number": CERT_PROJECT_NUMBER,
        "project_name": CERT_PROJECT_NAME,
        "location": "Cert Lab · Preview",
        "client": "MASCI Internal",
        "project_manager": "Jaymn Judd",
        "pm_email": ADMIN_EMAIL,
        "active": True,
    }
    r = requests.post(
        f"{API}/api/admin/jobs",
        headers={**h, "Content-Type": "application/json"},
        json=payload, timeout=45,
    )
    if r.status_code in (200, 201):
        print(f"  ✓ project {CERT_PROJECT_NUMBER} created")
    else:
        print(f"  ⚠ project create returned {r.status_code}: {r.text[:300]}")


def find_user_by_email(admin_token: str, email: str) -> Optional[Dict[str, Any]]:
    h = {"X-Admin-Token": admin_token}
    r = requests.get(f"{API}/api/admin/directory?q={email}", headers=h, timeout=20)
    if r.status_code != 200:
        return None
    body = r.json()
    for u in body.get("users") or []:
        if (u.get("email") or "").lower() == email.lower():
            return u
    return None


def ensure_user(admin_token: str, role: Dict[str, Any]) -> Dict[str, Any]:
    """Idempotent — create the directory user if missing; rotate to
    known password regardless so login is deterministic."""
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    existing = find_user_by_email(admin_token, role["email"])
    if existing:
        # rotate password to SEED_PASSWORD so tests can log in
        uid = existing["id"]
        r = requests.post(
            f"{API}/api/admin/directory/{uid}/reset-password",
            headers=h,
            json={"new_password": SEED_PASSWORD, "must_change": False, "delivery": "show"},
            timeout=45,
        )
        # update portals if drifted
        if sorted(existing.get("portals") or []) != sorted(role["portals"]):
            requests.patch(
                f"{API}/api/admin/directory/{uid}",
                headers=h,
                json={"portals": role["portals"], "disabled": False},
                timeout=45,
            )
        return {"id": uid, "email": role["email"], "name": existing.get("name") or f"Cert {role['label']}"}

    payload = {
        "email": role["email"],
        "name": f"Cert {role['label']}",
        "portals": role["portals"],
        "password": SEED_PASSWORD,
        "must_change_password": False,
        "delivery": "show",
    }
    r = requests.post(f"{API}/api/admin/directory", headers=h, json=payload, timeout=20)
    if r.status_code in (200, 201):
        body = r.json()
        return body.get("user") or {}
    print(f"  ⚠ user {role['email']} create returned {r.status_code}: {r.text[:300]}")
    return {}


def assign_user(admin_token: str, user_id: str, role_key: str, email: str, name: str) -> Dict[str, Any]:
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    # First, check if already assigned (idempotency)
    r = requests.get(
        f"{API}/api/admin/jobs/{CERT_PROJECT_NUMBER}/team",
        headers=h, timeout=45,
    )
    if r.status_code == 200:
        items = r.json().get("items") or []
        for it in items:
            if (it.get("user_id") == user_id
                and it.get("assignment_role") == role_key
                and it.get("active") is True):
                return {"ok": True, "assignment_id": it.get("id"), "reused": True}

    body = {
        "user_id": user_id,
        "email": email,
        "display_name": name,
        "assignment_role": role_key,
        "assignment_scope": "full",
        "is_primary": role_key in {"pm", "superintendent"},
    }
    r = requests.post(
        f"{API}/api/admin/jobs/{CERT_PROJECT_NUMBER}/team",
        headers=h, json=body, timeout=45,
    )
    if r.status_code in (200, 201):
        a = (r.json() or {}).get("assignment") or {}
        return {"ok": True, "assignment_id": a.get("id"), "reused": False}
    return {"ok": False, "status": r.status_code, "error": r.text[:300]}


def main() -> int:
    print(f"Seeding runtime certification users into {API} …")
    admin_token = login_admin()
    print("  ✓ admin login OK")

    print("[1/3] Ensuring cert project exists …")
    ensure_project(admin_token)

    print("[2/3] Ensuring 17 cert users exist …")
    out: List[Dict[str, Any]] = []
    for role in ROLES:
        u = ensure_user(admin_token, role)
        if u and u.get("id"):
            out.append({
                "role_key": role["key"],
                "role_label": role["label"],
                "email": role["email"],
                "password": SEED_PASSWORD,
                "user_id": u["id"],
                "name": u.get("name") or f"Cert {role['label']}",
                "portals": role["portals"],
            })
            print(f"  ✓ {role['key']:<30} {role['email']}")
        else:
            print(f"  ✗ {role['key']}: FAILED to create/find user")

    print("[3/3] Assigning each user to the cert project under their role …")
    for u in out:
        res = assign_user(admin_token, u["user_id"], u["role_key"], u["email"], u["name"])
        u["assignment"] = res
        flag = "✓" if res.get("ok") else "✗"
        suffix = " (re-used)" if res.get("reused") else ""
        if not res.get("ok"):
            suffix = f" [{res.get('status')}: {res.get('error','')[:120]}]"
        print(f"  {flag} {u['role_key']:<30}{suffix}")

    # Verify roster
    h = {"X-Admin-Token": admin_token}
    r = requests.get(f"{API}/api/admin/jobs/{CERT_PROJECT_NUMBER}/team", headers=h, timeout=20)
    roster = (r.json() or {}).get("items", []) if r.status_code == 200 else []
    print(f"  Final roster count on cert project: {len(roster)}")

    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    Path("/app/test_reports/runtime_cert_seed.json").write_text(json.dumps({
        "api": API,
        "project_number": CERT_PROJECT_NUMBER,
        "project_name": CERT_PROJECT_NAME,
        "admin_email": ADMIN_EMAIL,
        "seed_password": SEED_PASSWORD,
        "users": out,
        "roster_size": len(roster),
        "seeded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2))
    print(f"\nDone. Wrote /app/test_reports/runtime_cert_seed.json ({len(out)} users)")
    return 0 if len(roster) >= len(out) else 1


if __name__ == "__main__":
    sys.exit(main())
