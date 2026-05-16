"""Iter176 regression — per-portal logins + anon gate matrix unchanged."""
import os
from pathlib import Path
import requests

BASE = "http://localhost:8001"

def _load_env(p):
    for line in Path(p).read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

_load_env("/app/backend/.env")


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
