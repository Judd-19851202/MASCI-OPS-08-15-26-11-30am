"""Iter176 regression — per-portal logins + anon gate matrix unchanged."""
import os
from pathlib import Path
import requests
import bcrypt
import re
from pymongo import MongoClient

BASE = "http://localhost:8001"

def _load_env(p):
    for line in Path(p).read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

_load_env("/app/backend/.env")


def _refresh_test_fixture_credentials():
    """DEPLOY-GATE-FIX-001 (2026-06-09): refresh stale per-portal seed
    fixtures so this regression suite is deterministic regardless of
    prior test-pollution that may have rotated `must_change_password`
    or `password_hash`. This only writes the documented test creds
    onto the documented test accounts in the *preview* DB. No
    production credential is rotated; no real user account is touched.

    Documented test accounts (from /app/memory/test_credentials.md):
      • hrmanager@mascigc.com   pw=HRTesting2026!
      • testmech@mascigc.com    pw=ResetWorks2026!
    """
    env_raw = Path("/app/backend/.env").read_text()
    m = re.search(r'^MONGO_URL="?([^"\n]+)"?', env_raw, re.MULTILINE)
    if not m:
        return
    url = m.group(1).strip().strip('"')
    db_name_match = re.search(r'^DB_NAME="?([^"\n]+)"?', env_raw, re.MULTILINE)
    db_name = (db_name_match.group(1).strip().strip('"')
               if db_name_match else "masci_safety_preview")
    # Hard guard: never touch a non-preview DB from this fixture.
    if not db_name.endswith("_preview"):
        return

    client = MongoClient(url, serverSelectionTimeoutMS=8000)
    try:
        db = client[db_name]
        for email, pw, collection in (
            ("hrmanager@mascigc.com", "HRTesting2026!", "hr_users"),
            ("testmech@mascigc.com", "ResetWorks2026!", "shop_users"),
        ):
            hash_ = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("ascii")
            db[collection].update_one(
                {"email": email},
                {"$set": {
                    "password_hash": hash_,
                    "must_change_password": False,
                    "is_active": True,
                }},
            )
    finally:
        client.close()


# Refresh once at module import so every test in this file is deterministic.
_refresh_test_fixture_credentials()


def test_admin_legacy_login():
    r = requests.post(f"{BASE}/api/admin/login", json={"password": os.environ["ADMIN_PASSWORD"]}, timeout=10)
    assert r.status_code == 200, r.text
    assert "token" in r.json()


def test_hr_login():
    r = requests.post(f"{BASE}/api/hr/login", json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"}, timeout=10)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_shop_login():
    r = requests.post(f"{BASE}/api/shop/login", json={"email": "testmech@mascigc.com", "password": "ResetWorks2026!"}, timeout=10)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_super_admin_multi_login_grants_all_portals():
    r = requests.post(f"{BASE}/api/auth/multi-login", json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}, timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    portals = j.get("portals") or j.get("portal_tokens") or {}
    # At minimum verify the response surfaces the user portals
    user = j.get("user", {})
    user_portals = set(user.get("portals", []))
    assert {"admin", "pm", "shop", "hr"}.issubset(user_portals), j


def test_anon_gate_matrix_unchanged():
    for path in ("/api/admin/audit", "/api/admin/directory", "/api/admin/integrations/health"):
        r = requests.get(f"{BASE}{path}", timeout=10)
        assert r.status_code in (401, 403), f"{path} returned {r.status_code}"
