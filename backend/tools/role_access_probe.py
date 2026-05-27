"""Role Access Certification probe — Phase Sigma.

Methodology:
  - One canonical token per role (super-admin multi-login fan-out + direct per-portal logins).
  - Probe a representative set of endpoint families with each role's token.
  - Record HTTP status + token-header used.
  - Classify each cell: 200=accept, 401=reject-no-auth, 403=reject-forbidden,
    404=not-found (endpoint may be path-mismatched), 5xx=server-error.

The matrix that comes out is the source of truth for /app/memory/ROLE_ACCESS_CERTIFICATION.md.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests


# ---------------------------------------------------------------------------
# Bootstrap state from earlier
# ---------------------------------------------------------------------------
state = json.loads(Path("/tmp/role_cert_state.json").read_text())
BASE = state["base_url"]

# Map role label → (header, token).
# Use multi-login tokens by default (they're the "issued from directory" path).
# Use direct-portal login tokens where available to ALSO certify the per-user
# portal-login round-trip works end-to-end.
ROLES = {
    "super_admin (admin)":     ("X-Admin-Token",    state["tokens_from_multilogin"]["admin"]),
    "super_admin (pm)":        ("X-PM-Token",       state["tokens_from_multilogin"]["pm"]),
    "super_admin (hr)":        ("X-HR-Token",       state["tokens_from_multilogin"]["hr"]),
    "super_admin (shop)":      ("X-Shop-Token",     state["tokens_from_multilogin"]["shop"]),
    "super_admin (safety)":    ("X-Safety-Token",   state["tokens_from_multilogin"]["safety"]),
    "super_admin (dispatch)":  ("X-Dispatch-Token", state["tokens_from_multilogin"]["dispatch"]),
    "super_admin (FL)":        ("X-FL-Token",       state["tokens_from_multilogin"]["field_leadership"]),
}

# Direct per-portal logins (where we have them) — proves per-portal auth flow.
if "dispatch_token" in state:
    ROLES["dispatch (direct)"] = ("X-Dispatch-Token", state["dispatch_token"])
if "safety_token" in state:
    ROLES["safety (direct)"] = ("X-Safety-Token", state["safety_token"])
if "hr_token_direct" in state:
    ROLES["hr_manager (direct)"] = ("X-HR-Token", state["hr_token_direct"])
if "pm_token_direct" in state:
    ROLES["pm_chris (direct)"] = ("X-PM-Token", state["pm_token_direct"])
if "fl_token_direct" in state:
    ROLES["fl_user (direct)"] = ("X-FL-Token", state["fl_token_direct"])

ROLES["no_auth (anonymous)"] = (None, None)

# ---------------------------------------------------------------------------
# Endpoint families. Each tuple: (path, method, family_label, expectation_rule)
# expectation_rule is a function (role_label) -> set of acceptable status codes.
# ---------------------------------------------------------------------------

def _admin_only(role):
    return {200} if "admin" in role.lower() and "super_admin" in role.lower() else {401, 403}

def _hr_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (hr)" in role or "hr_manager" in role:
        return {200}
    return {401, 403}

def _pm_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (pm)" in role or "pm_chris" in role:
        return {200}
    return {401, 403}

def _shop_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (shop)" in role:
        return {200}
    return {401, 403}

def _safety_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (safety)" in role or "safety (direct)" in role:
        return {200}
    return {401, 403}

def _dispatch_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (dispatch)" in role or "dispatch (direct)" in role:
        return {200}
    return {401, 403}

def _fl_or_admin(role):
    if "super_admin (admin)" in role or "super_admin (FL)" in role or "fl_user" in role:
        return {200}
    return {401, 403}

def _any_portal_or_admin(role):
    # Read-only ops endpoints accept ANY signed portal token (iter126).
    if role.startswith("no_auth"):
        return {401, 403}
    return {200}

def _public(role):
    return {200}


ENDPOINTS = [
    # path, method, family, expectation_rule
    ("/api/health",                           "GET", "public",      _public),
    ("/api/version",                          "GET", "public",      _public),
    ("/api/cluster/capacity",                 "GET", "public",      _public),
    ("/api/employees",                        "GET", "public",      _public),

    # Admin-only
    ("/api/admin/jobs",                       "GET", "admin",       _admin_only),
    ("/api/admin/dispatch-users",             "GET", "admin",       _admin_only),
    ("/api/admin/hr-users",                   "GET", "admin",       _admin_only),
    ("/api/admin/safety-users",               "GET", "admin",       _admin_only),
    ("/api/admin/shop-users",                 "GET", "admin",       _admin_only),
    ("/api/admin/project-managers/activity",  "GET", "admin",       _admin_only),

    # Daily ops — actually require admin (PM also via shared admin token in some routes).
    ("/api/daily-reports",                    "GET", "admin",       _admin_only),
    ("/api/incidents",                        "GET", "admin",       _admin_only),
    ("/api/meetings",                         "GET", "admin",       _admin_only),
    ("/api/inspections",                      "GET", "admin",       _admin_only),
    ("/api/jhas",                             "GET", "admin",       _admin_only),
    ("/api/equipment-inspections",            "GET", "admin",       _admin_only),

    # Per-portal /me endpoints
    ("/api/pm/me",                            "GET", "pm",          _pm_or_admin),
    ("/api/hr/me",                            "GET", "hr",          _hr_or_admin),
    ("/api/shop/me",                          "GET", "shop",        _shop_or_admin),
    ("/api/safety/me",                        "GET", "safety",      _safety_or_admin),
    ("/api/dispatch/me",                      "GET", "dispatch",    _dispatch_or_admin),
    ("/api/field-leadership/portal/me",       "GET", "fl",          _fl_or_admin),

    # HR-specific
    ("/api/hr/time-verification",             "GET", "hr",          _hr_or_admin),
    ("/api/hr/training-records",              "GET", "hr",          _hr_or_admin),
    ("/api/hr/driver-qualification/dashboard","GET", "hr",          _hr_or_admin),

    # Field-leadership-specific
    ("/api/field-leadership/portal/dispatch-today", "GET", "fl",    _fl_or_admin),
]


# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------
results = []

for role, (header_name, token) in ROLES.items():
    for path, method, family, expect_fn in ENDPOINTS:
        headers = {}
        if header_name and token:
            headers[header_name] = token
        t0 = time.monotonic()
        try:
            r = requests.request(method, f"{BASE}{path}", headers=headers, timeout=10)
            status = r.status_code
            elapsed_ms = int((time.monotonic() - t0) * 1000)
        except Exception:
            status = -1
            elapsed_ms = -1
        expected = expect_fn(role)
        verdict = "VERIFIED" if status in expected else "FAIL"
        results.append({
            "role": role,
            "endpoint": path,
            "method": method,
            "family": family,
            "expected": sorted(expected),
            "actual": status,
            "verdict": verdict,
            "elapsed_ms": elapsed_ms,
        })

# ---------------------------------------------------------------------------
# Persist + print summary
# ---------------------------------------------------------------------------
Path("/tmp/role_cert_results.json").write_text(json.dumps(results, indent=2, default=str))

verified = sum(1 for r in results if r["verdict"] == "VERIFIED")
failed = sum(1 for r in results if r["verdict"] == "FAIL")
print(f"\nTOTAL: {len(results)} cells · VERIFIED={verified} · FAIL={failed}")

# Print failures with details
if failed:
    print("\n=== FAILURES ===")
    for r in results:
        if r["verdict"] == "FAIL":
            print(f"  {r['role']:30s} {r['endpoint']:50s} actual={r['actual']} expected={r['expected']}")
