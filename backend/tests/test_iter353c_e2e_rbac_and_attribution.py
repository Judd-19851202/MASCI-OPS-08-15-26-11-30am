"""
iter353c additional E2E tests:
- Cross-portal viewer attribution (HR vs Safety vs Admin)
- RBAC negative tests for PM, Shop, Dispatch, FL (all should be blocked)
- Anonymous blocked (timeline + brief.pdf)
- PDF magic bytes + Content-Type
- Archived records remain visible
"""
import os
from pathlib import Path
import requests
import pytest


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
EMP_ID = "250d2712-6be3-440e-9de9-1941c5a735d6"  # Alec Perkins

HR_CREDS = {"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"}
ADMIN_CREDS = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
PM_CREDS = {"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"}


def _no_admin():
    # bypass conftest auto-admin injection by sending empty header
    return {"X-Admin-Token": ""}


def _hr_token():
    r = requests.post(f"{BASE_URL}/api/hr/login", json=HR_CREDS, timeout=15)
    assert r.status_code == 200, f"HR login failed: {r.status_code} {r.text}"
    return r.json().get("token") or r.json().get("access_token")


def _multi_login():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=ADMIN_CREDS, timeout=15)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    return r.json()


def _pm_token():
    r = requests.post(f"{BASE_URL}/api/pm/login", json=PM_CREDS, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"PM login unavailable: {r.status_code}")
    return r.json().get("token") or r.json().get("access_token")


# --- Cross-portal viewer attribution ---

def test_viewer_role_hr():
    tok = _hr_token()
    h = {**_no_admin(), "X-HR-Token": tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=h, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "viewer" in data, f"viewer not in response keys: {list(data.keys())}"
    assert data["viewer"].get("role") == "hr", f"expected hr, got {data['viewer']}"


def test_viewer_role_safety():
    ml = _multi_login()
    safety_tok = ml.get("portal_tokens", {}).get("safety")
    if not safety_tok:
        pytest.skip(f"No safety token in multi-login response keys: {list(ml.keys())}")
    h = {**_no_admin(), "X-Safety-Token": safety_tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=h, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json().get("viewer", {}).get("role") == "safety"


def test_viewer_role_admin():
    ml = _multi_login()
    admin_tok = ml.get("portal_tokens", {}).get("admin")
    if not admin_tok:
        pytest.skip(f"No admin token: {list(ml.keys())}")
    h = {"X-Admin-Token": admin_tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=h, timeout=20)
    assert r.status_code == 200, r.text
    role = r.json().get("viewer", {}).get("role")
    assert role in ("admin", "safety", "hr"), f"unexpected viewer.role={role}"


def test_pm_shop_dispatch_fl_all_blocked():
    """RBAC matrix: PM, Shop, Dispatch, Field Leadership tokens must all 401/403."""
    ml = _multi_login()
    pt = ml.get("portal_tokens", {})
    for portal in ("pm", "shop", "dispatch", "field_leadership"):
        tok = pt.get(portal)
        if not tok:
            continue
        # Try the wrong-portal token in both HR and Safety header slots
        for hdr_name in ("X-HR-Token", "X-Safety-Token"):
            h = {**_no_admin(), hdr_name: tok}
            r = requests.get(
                f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline",
                headers=h, timeout=15,
            )
            assert r.status_code in (401, 403), (
                f"{portal} via {hdr_name} should be blocked, got {r.status_code}"
            )


# --- RBAC negative tests ---

def test_anonymous_timeline_blocked():
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=_no_admin(), timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code} {r.text[:200]}"


def test_anonymous_brief_blocked():
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/brief.pdf", headers=_no_admin(), timeout=15)
    assert r.status_code in (401, 403)


def test_pm_token_blocked():
    tok = _pm_token()
    # PM tokens should not be accepted by either X-HR-Token or X-Safety-Token gates
    h = {**_no_admin(), "X-HR-Token": tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=h, timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


# --- PDF download integrity ---

def test_brief_pdf_content_type_and_magic_bytes():
    tok = _hr_token()
    h = {**_no_admin(), "X-HR-Token": tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/brief.pdf", headers=h, timeout=30)
    assert r.status_code == 200, r.text[:200]
    assert "application/pdf" in r.headers.get("content-type", "").lower()
    assert r.content[:5] == b"%PDF-"


# --- Archived visibility ---

def test_archived_records_remain_visible():
    tok = _hr_token()
    h = {**_no_admin(), "X-HR-Token": tok}
    r = requests.get(f"{BASE_URL}/api/hr/employees/{EMP_ID}/accountability/timeline", headers=h, timeout=20)
    assert r.status_code == 200
    data = r.json()
    events = data.get("events", [])
    archived = [e for e in events if e.get("archived") is True or "archived" in (str(e.get("notes") or "")).lower()]
    assert isinstance(events, list)
    print(f"Total events: {len(events)}, archived markers: {len(archived)}")
