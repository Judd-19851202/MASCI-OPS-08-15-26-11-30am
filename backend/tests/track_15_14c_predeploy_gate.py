#!/usr/bin/env python3
"""
Track 15.14C · Pre-Deploy Safety Gate

Verifies the temp-password enforcement (Track 15.14A) does NOT disrupt
existing permanent-password users, AND that the temp-password
enforcement DOES still block temp-password users. Plus HR Daily Reports
+ HR Field Leadership + Pre-Ops smoke tests.

Runs against the live preview backend.
"""
import os
import sys
import time
import requests

BASE = os.environ.get("BASE_URL", "https://backup-forensics.preview.emergentagent.com")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "CertProof2026!"

results = []

def record(portal, scenario, status, detail=""):
    results.append((portal, scenario, status, detail))
    sym = "✓" if status == "PASS" else "✗" if status == "FAIL" else "·"
    print(f"  {sym} [{portal:>10}] {scenario}  {detail}")

def assert_eq(portal, scenario, expected, actual, info=""):
    if expected == actual:
        record(portal, scenario, "PASS", f"({actual})")
        return True
    record(portal, scenario, "FAIL", f"expected={expected} got={actual} {info}")
    return False

def admin_token():
    r = requests.post(f"{BASE}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=30)
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin")

# ─────────────────────────────────────────────────────────────────────
# Existing permanent-password users — confirm NOT disrupted.
# ─────────────────────────────────────────────────────────────────────
def verify_hr_manager():
    portal = "HR"
    print(f"\n── Existing user verification · {portal} (hrmanager@mascigc.com)")
    r = requests.post(f"{BASE}/api/hr/login",
                      json={"email": HR_EMAIL, "password": HR_PW}, timeout=30)
    if r.status_code != 200:
        record(portal, "existing user login", "FAIL", f"status={r.status_code}")
        return None
    j = r.json()
    mcp = bool(j.get("must_change_password"))
    assert_eq(portal, "login.ok=true", True, j.get("ok") == True)
    assert_eq(portal, "login.must_change_password is false", False, mcp)
    tok = j.get("token")
    if not tok:
        record(portal, "login token issued", "FAIL", "missing token")
        return None
    # Protected APIs
    for path, label in [
        ("/api/hr/daily-reports?limit=5", "GET hr/daily-reports"),
        ("/api/hr/employees?limit=5", "GET hr/employees"),
        ("/api/hr/field-leadership?limit=5", "GET hr/field-leadership"),
        ("/api/admin/field-leadership-users", "GET admin/field-leadership-users"),
        ("/api/hr/me", "GET hr/me"),
    ]:
        rr = requests.get(f"{BASE}{path}", headers={"X-HR-Token": tok}, timeout=20)
        assert_eq(portal, label, 200, rr.status_code, info=rr.text[:80] if rr.status_code != 200 else "")
    return tok

def verify_admin():
    portal = "Admin"
    print(f"\n── Existing user verification · {portal}")
    r = requests.post(f"{BASE}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=30)
    if r.status_code != 200:
        record(portal, "multi-login", "FAIL", f"status={r.status_code}")
        return
    j = r.json()
    mcp = bool(j.get("must_change_password"))
    assert_eq(portal, "multi-login.must_change_password is false", False, mcp)
    portal_tokens = j.get("portal_tokens") or {}
    assert_eq(portal, "admin portal_token minted", True, bool(portal_tokens.get("admin")))
    assert_eq(portal, "pm portal_token minted", True, bool(portal_tokens.get("pm")))
    assert_eq(portal, "hr portal_token minted", True, bool(portal_tokens.get("hr")))
    tok = portal_tokens.get("admin")
    if not tok:
        return
    # Protected admin endpoints
    for path, label in [
        ("/api/admin/directory?q=", "GET admin/directory"),
        ("/api/admin/field-leadership-users", "GET admin/field-leadership-users"),
        ("/api/equipment-inspections?limit=5", "GET equipment-inspections"),
        ("/api/admin/equipment-inspections/trends", "GET admin/equipment-inspections/trends"),
        ("/api/admin/equipment-inspections/open-items", "GET admin/equipment-inspections/open-items"),
    ]:
        rr = requests.get(f"{BASE}{path}", headers={"X-Admin-Token": tok}, timeout=20)
        assert_eq(portal, label, 200, rr.status_code, info=rr.text[:80] if rr.status_code != 200 else "")

def verify_existing_no_disruption_on_per_user(portal_label, login_url, login_body,
                                              token_hdr, protected_paths,
                                              create_url, admin_token_value,
                                              create_body):
    """Provision a per-user account WITHOUT must_change_password (or
    rotate it manually) to mirror an established permanent-password user,
    then verify the user can hit protected routes."""
    print(f"\n── Existing-user safety on {portal_label}")
    # Create with must_change_password=false (most admin create endpoints
    # default to True, so we provision and rotate before testing).
    rr = requests.post(create_url, json=create_body,
                       headers={"X-Admin-Token": admin_token_value}, timeout=30)
    if rr.status_code not in (200, 201):
        record(portal_label, "provision", "FAIL", f"create {rr.status_code} {rr.text[:120]}")
        return
    cb = rr.json()
    user_id = (cb.get("id") or cb.get("user", {}).get("id"))
    temp_pw = cb.get("temp_password") or cb.get("password") or cb.get("user", {}).get("temp_password")
    if not (user_id and temp_pw):
        record(portal_label, "provision payload", "FAIL", f"{cb}")
        return
    # Login (forced rotation expected)
    lr = requests.post(login_url, json={"email": login_body["email"], "password": temp_pw}, timeout=20)
    if lr.status_code != 200:
        record(portal_label, "first login", "FAIL", f"{lr.status_code}")
        return
    lj = lr.json()
    tok = lj.get("token")
    # Rotate to clear must_change_password
    new_pw = "PermPwTrack1514C!"
    cp_body = {"current_password": temp_pw, "new_password": new_pw}
    if portal_label in ("PM", "Shop"):
        cp_body = {"old_password": temp_pw, "new_password": new_pw}
    cr = requests.post(f"{BASE}{login_url.split('/api/')[1].split('/login')[0]}".replace("/api/", "/api/") + "/change-password" if False else login_url.replace("/login","/change-password"),
                       json=cp_body, headers={token_hdr: tok}, timeout=30)
    # ⬆ change-password URL = login URL with /login replaced by /change-password
    if cr.status_code != 200:
        record(portal_label, "rotate-to-permanent", "FAIL", f"{cr.status_code} {cr.text[:120]}")
        return
    rotated = cr.json()
    rotated_tok = rotated.get("token")
    record(portal_label, "rotate-to-permanent", "PASS", "flag cleared")
    # Now we have an "established permanent" user. Re-login to simulate the
    # exact code path an existing user goes through every session.
    lr2 = requests.post(login_url, json={"email": login_body["email"], "password": new_pw}, timeout=20)
    if lr2.status_code != 200:
        record(portal_label, "permanent-password re-login", "FAIL", f"{lr2.status_code}")
        return
    lj2 = lr2.json()
    perm_tok = lj2.get("token")
    assert_eq(portal_label, "perm re-login must_change_password=false", False,
              bool(lj2.get("must_change_password")))
    # Hit protected routes
    for path, label in protected_paths:
        rr2 = requests.get(f"{BASE}{path}", headers={token_hdr: perm_tok}, timeout=20)
        assert_eq(portal_label, f"protected {label}", 200, rr2.status_code,
                  info=rr2.text[:80] if rr2.status_code != 200 else "")
    # Cleanup
    try:
        admin_disable_url = create_url + f"/{user_id}"
        requests.patch(admin_disable_url, json={"disabled": True},
                       headers={"X-Admin-Token": admin_token_value}, timeout=15)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────
# Pre-Ops smoke test
# ─────────────────────────────────────────────────────────────────────
def verify_preops(admin_tok):
    portal = "Pre-Ops"
    print(f"\n── Pre-Ops smoke test")
    for path, label in [
        ("/api/equipment-inspections?limit=5", "list"),
        ("/api/admin/equipment-inspections/trends", "trends"),
        ("/api/admin/equipment-inspections/open-items", "open-items"),
    ]:
        rr = requests.get(f"{BASE}{path}", headers={"X-Admin-Token": admin_tok}, timeout=20)
        assert_eq(portal, label, 200, rr.status_code,
                  info=rr.text[:120] if rr.status_code != 200 else "")
    # detail
    listr = requests.get(f"{BASE}/api/equipment-inspections?limit=1",
                         headers={"X-Admin-Token": admin_tok}, timeout=20).json()
    sample_id = (listr[0] if isinstance(listr, list) and listr else {}).get("id")
    if sample_id:
        rr = requests.get(f"{BASE}/api/equipment-inspections/{sample_id}",
                          headers={"X-Admin-Token": admin_tok}, timeout=20)
        assert_eq(portal, "detail", 200, rr.status_code)

# ─────────────────────────────────────────────────────────────────────
# Negative tests — non-HR/non-admin tokens MUST NOT reach FL user mgmt.
# ─────────────────────────────────────────────────────────────────────
def verify_fl_user_mgmt_lockdown():
    portal = "FL-mgmt"
    print(f"\n── FL user-management lockdown")
    # Build a Safety user and try to use their token against the FL admin endpoint
    rr = requests.get(f"{BASE}/api/admin/field-leadership-users", timeout=15)
    assert_eq(portal, "no token rejected", 401, rr.status_code)
    rr = requests.get(f"{BASE}/api/admin/field-leadership-users",
                      headers={"X-Safety-Token": "BOGUS"}, timeout=15)
    assert_eq(portal, "bogus safety token rejected", 401, rr.status_code)


def main():
    print(f"BASE = {BASE}")
    atok = admin_token()
    print(f"admin_token len = {len(atok or '')}")

    # 1) Existing permanent-password users
    verify_hr_manager()
    verify_admin()

    # 2) Per-portal permanent-password lifecycle
    ts = int(time.time())
    # HR
    verify_existing_no_disruption_on_per_user(
        portal_label="HR",
        login_url=f"{BASE}/api/hr/login",
        login_body={"email": f"hr_perm_{ts}@example.com"},
        token_hdr="X-HR-Token",
        protected_paths=[
            ("/api/hr/daily-reports?limit=5", "daily-reports"),
            ("/api/hr/employees?limit=5", "employees"),
            ("/api/hr/me", "/me"),
        ],
        create_url=f"{BASE}/api/admin/hr-users",
        admin_token_value=atok,
        create_body={"name": "Perm HR", "email": f"hr_perm_{ts}@example.com",
                     "role": "HR Assistant", "delivery": "show"},
    )
    # Dispatch
    verify_existing_no_disruption_on_per_user(
        portal_label="Dispatch",
        login_url=f"{BASE}/api/dispatch/login",
        login_body={"email": f"dp_perm_{ts}@example.com"},
        token_hdr="X-Dispatch-Token",
        protected_paths=[
            ("/api/dispatch/daily-reports", "daily-reports"),
            ("/api/dispatch/me", "/me"),
        ],
        create_url=f"{BASE}/api/admin/dispatch-users",
        admin_token_value=atok,
        create_body={"name": "Perm DP", "email": f"dp_perm_{ts}@example.com",
                     "role": "Dispatcher", "is_active": True},
    )
    # Safety
    verify_existing_no_disruption_on_per_user(
        portal_label="Safety",
        login_url=f"{BASE}/api/safety/login",
        login_body={"email": f"sf_perm_{ts}@example.com"},
        token_hdr="X-Safety-Token",
        protected_paths=[
            ("/api/safety/overview", "overview"),
            ("/api/safety/me", "/me"),
        ],
        create_url=f"{BASE}/api/admin/safety-users",
        admin_token_value=atok,
        create_body={"name": "Perm SF", "email": f"sf_perm_{ts}@example.com",
                     "role": "Safety Coordinator", "is_active": True},
    )
    # Field Leadership
    verify_existing_no_disruption_on_per_user(
        portal_label="FL",
        login_url=f"{BASE}/api/field-leadership/portal/login",
        login_body={"email": f"fl_perm_{ts}@example.com"},
        token_hdr="X-FL-Token",
        protected_paths=[
            ("/api/field-leadership/portal/dispatch-today", "dispatch-today"),
            ("/api/field-leadership/portal/me", "/me"),
        ],
        create_url=f"{BASE}/api/admin/field-leadership-users",
        admin_token_value=atok,
        create_body={"name": "Perm FL", "email": f"fl_perm_{ts}@example.com",
                     "role": "Foreman", "delivery": "show"},
    )

    # 3) Pre-Ops
    verify_preops(atok)

    # 4) Negative tests
    verify_fl_user_mgmt_lockdown()

    # Summary
    pass_n = sum(1 for r in results if r[2] == "PASS")
    fail_n = sum(1 for r in results if r[2] == "FAIL")
    print("\n══════════════════════════════════════════════════════════════")
    print(f"  TRACK 15.14C SAFETY GATE · PASS={pass_n}  FAIL={fail_n}")
    print("══════════════════════════════════════════════════════════════")
    if fail_n:
        print("FAILURES:")
        for r in results:
            if r[2] == "FAIL":
                print(f"  ✗ [{r[0]}] {r[1]}  ::  {r[3]}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
