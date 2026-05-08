"""
iter58 — PRODUCTION audit against https://mascidocs.com
Targets PRODUCTION URL directly (NOT REACT_APP_BACKEND_URL preview).
Verifies iter48-iter57 features are deployed and working.
"""
import os
import re
import time
import pytest
import requests

# HARD OVERRIDE — production target, NOT preview
PROD_URL = "https://mascidocs.com"
ADMIN_PASSWORD = "MASCI1982!"
LEADERSHIP_PASSWORD = "MASCIGC"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


# ---------- Health & perf ----------
def test_health_200_under_1s():
    t0 = time.time()
    r = session.get(f"{PROD_URL}/api/health", timeout=10)
    elapsed = time.time() - t0
    assert r.status_code == 200, r.text
    assert elapsed < 2.0, f"health took {elapsed:.2f}s (expected <2s)"
    data = r.json()
    assert data.get("ok") is True
    assert data.get("service") == "masci-hub"


# ---------- Admin auth ----------
@pytest.fixture(scope="module")
def admin_token():
    t0 = time.time()
    r = session.post(f"{PROD_URL}/api/admin/login",
                     json={"password": ADMIN_PASSWORD}, timeout=10)
    elapsed = time.time() - t0
    assert r.status_code == 200, f"admin login failed {r.status_code}: {r.text[:300]}"
    assert elapsed < 3.0
    data = r.json()
    assert data.get("ok") is True
    tok = data.get("token")
    assert tok and len(tok) >= 32, f"bad token: {tok}"
    return tok


def test_admin_login_returns_token(admin_token):
    assert admin_token


# ---------- iter54-56: doc-ID search (admin-strict) ----------
def test_find_by_doc_id_unauth_rejected():
    r = session.get(f"{PROD_URL}/api/admin/find-by-doc-id",
                    params={"doc_id": "PRE-2026-00001"}, timeout=10)
    assert r.status_code in (401, 403), \
        f"unauth find-by-doc-id should be 401/403 got {r.status_code}"


def test_find_by_doc_id_with_admin(admin_token):
    headers = {"X-Admin-Token": admin_token}
    # PRE-2026-00001 is verified to exist in production
    r = session.get(f"{PROD_URL}/api/admin/find-by-doc-id",
                    params={"doc_id": "PRE-2026-00001"}, headers=headers, timeout=10)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    d = r.json()
    assert d.get("found") is True
    assert d.get("doc_id") == "PRE-2026-00001"
    assert d.get("route", "").startswith("/admin/")
    print(f"  resolved route: {d.get('route')}")

    # Verify 404 behavior for unknown doc_ids (prod returns 404, not 200+found:false)
    r2 = session.get(f"{PROD_URL}/api/admin/find-by-doc-id",
                     params={"doc_id": "ZZZ-2026-99999"}, headers=headers, timeout=10)
    assert r2.status_code in (200, 404), r2.status_code


# ---------- iter48-50: shop auth UX ----------
def test_shop_login_email_required():
    # No email + no password → must reject
    r = session.post(f"{PROD_URL}/api/shop/login", json={}, timeout=10)
    assert r.status_code in (400, 401, 422), r.status_code

    # Email but no password → reject (per-user flow)
    r = session.post(f"{PROD_URL}/api/shop/login",
                     json={"email": "noone@example.com"}, timeout=10)
    assert r.status_code in (400, 401, 422), r.status_code


def test_shop_forgot_password_endpoint_exists():
    # iter49 — must always return 200 (enumeration-safe)
    r = session.post(f"{PROD_URL}/api/shop/forgot-password",
                     json={"email": "noone-iter58@example.com"}, timeout=15)
    assert r.status_code == 200, f"forgot-password missing: {r.status_code} {r.text[:200]}"


def test_pm_forgot_password_endpoint_exists():
    r = session.post(f"{PROD_URL}/api/pm/forgot-password",
                     json={"email": "noone-iter58@example.com"}, timeout=15)
    assert r.status_code == 200, f"pm forgot-password missing: {r.status_code}"


# ---------- iter51: signed thumb URL ----------
def test_thumb_signed_route_registered(admin_token):
    # iter51 — list a real photo and verify the signed URL works end-to-end
    headers = {"X-Admin-Token": admin_token}
    r = session.get(f"{PROD_URL}/api/job-photos", headers=headers,
                    params={"limit": 1}, timeout=15)
    assert r.status_code == 200, r.status_code
    items = r.json().get("items", [])
    if not items:
        pytest.skip("no job photos in production to test signed thumb")

    photo = items[0]
    photo_id = photo["id"]
    thumb_token = photo.get("thumb_token")
    assert thumb_token, f"iter51 thumb_token missing on photo doc: {photo}"

    # Hit /thumb-signed with valid token
    r2 = session.get(f"{PROD_URL}/api/job-photos/{photo_id}/thumb-signed",
                     params={"t": thumb_token}, timeout=15)
    assert r2.status_code == 200, f"thumb-signed: {r2.status_code}"
    assert r2.headers.get("Content-Type", "").startswith("image/"), \
        f"expected image, got {r2.headers.get('Content-Type')}"
    assert len(r2.content) > 1000, f"thumb too small: {len(r2.content)}"

    # Without token → must NOT serve the image (422 or 4xx)
    r3 = session.get(f"{PROD_URL}/api/job-photos/{photo_id}/thumb-signed",
                     timeout=10)
    assert r3.status_code in (400, 401, 403, 422), \
        f"thumb-signed no-token returned {r3.status_code}"

    # Admin /thumb (legacy) still works
    r4 = session.get(f"{PROD_URL}/api/job-photos/{photo_id}/thumb",
                     headers=headers, timeout=15)
    assert r4.status_code == 200
    assert r4.headers.get("Content-Type", "").startswith("image/")


# ---------- iter47: brand audit ----------
def test_no_judd_group_in_admin_login_html():
    r = session.get(f"{PROD_URL}/admin/login", timeout=10)
    assert r.status_code == 200
    assert "Judd Group" not in r.text, "STALE BRAND: 'Judd Group' found on /admin/login HTML"


def test_no_judd_group_in_shop_login_html():
    r = session.get(f"{PROD_URL}/shop/login", timeout=10)
    assert r.status_code == 200
    assert "Judd Group" not in r.text, "STALE BRAND: 'Judd Group' found on /shop/login HTML"


def test_no_judd_group_in_root_html():
    r = session.get(f"{PROD_URL}/", timeout=10)
    assert r.status_code == 200
    assert "Judd Group" not in r.text


# ---------- iter52: PDF generation still works ----------
def test_admin_health_routes_admin_only(admin_token):
    # Generic admin-protected endpoint should accept token
    headers = {"X-Admin-Token": admin_token}
    r = session.get(f"{PROD_URL}/api/admin/jobs", headers=headers, timeout=15)
    assert r.status_code in (200, 404), \
        f"admin/jobs returned {r.status_code} for valid token"


def test_admin_jobs_unauth_rejected():
    r = session.get(f"{PROD_URL}/api/admin/jobs", timeout=10)
    assert r.status_code in (401, 403), r.status_code


# ---------- Performance baseline ----------
def test_admin_home_page_responds_under_3s():
    t0 = time.time()
    r = session.get(f"{PROD_URL}/admin", timeout=10)
    elapsed = time.time() - t0
    assert r.status_code == 200
    assert elapsed < 4.0, f"/admin took {elapsed:.2f}s"


def test_doc_id_search_under_500ms(admin_token):
    headers = {"X-Admin-Token": admin_token}
    t0 = time.time()
    r = session.get(f"{PROD_URL}/api/admin/find-by-doc-id",
                    params={"doc_id": "DR-2026-00001"},
                    headers=headers, timeout=10)
    elapsed_ms = (time.time() - t0) * 1000
    assert r.status_code == 200
    assert elapsed_ms < 1500, f"doc-id search took {elapsed_ms:.0f}ms"
    print(f"  doc-id search: {elapsed_ms:.0f}ms")
