"""iter256 pre-deploy readiness backend audit."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_PASSWORD = "Maddix123!"

FLEET_SLUGS = [
    "fleet-daily-dvir", "fleet-weekly-lead", "fleet-weekly-emergency",
    "fleet-severity-oos-vs-monitor", "fleet-repair-lifecycle", "fleet-return-to-service",
]

FRONTEND_ROUTES = [
    "/", "/shop/login", "/dispatch-portal/login", "/safety-portal/login",
    "/leadership/login", "/pm/login", "/hr/login", "/admin/login",
    "/field", "/fleet/dvir/new", "/fleet/weekly-lead/new",
    "/fleet/weekly-emergency/new", "/shop/fleet", "/dispatch-portal/fleet",
    "/safety-portal/fleet", "/guidance", "/guidance/fleet-daily-dvir",
    "/guidance/fleet-severity-oos-vs-monitor",
]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    return r.json().get("token")


@pytest.mark.parametrize("slug", FLEET_SLUGS)
def test_guidance_article_en(slug):
    r = requests.get(f"{BASE_URL}/api/guidance/articles/{slug}", timeout=15)
    assert r.status_code == 200, f"EN {slug}: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert body and any(k in body for k in ("title", "body", "html", "content", "sections", "intro")), f"EN {slug}: keys={list(body.keys())}"


@pytest.mark.parametrize("slug", FLEET_SLUGS)
def test_guidance_article_es(slug):
    r = requests.get(f"{BASE_URL}/api/guidance/articles/{slug}?lang=es", timeout=15)
    assert r.status_code == 200, f"ES {slug}: {r.status_code} {r.text[:200]}"
    assert r.json(), f"ES {slug}: empty body"


ANON_ENDPOINTS = [
    "/api/admin/dispatch-users", "/api/admin/safety-users",
    "/api/admin/fleet/severity-audit", "/api/admin/fleet/severity-reference-card.pdf",
    "/api/shop/fleet/by-unit", "/api/dispatch/fleet/status",
    "/api/admin/audit-log", "/api/safety/exports/inspections",
    "/api/fleet/defects/anything/detail",
]


@pytest.mark.parametrize("path", ANON_ENDPOINTS)
def test_rbac_anonymous_blocked(path):
    r = requests.get(f"{BASE_URL}{path}", timeout=15)
    assert r.status_code in (401, 403), f"{path}: {r.status_code} {r.text[:120]}"


def test_rbac_admin_severity_audit(admin_token):
    r = requests.get(f"{BASE_URL}/api/admin/fleet/severity-audit",
                     headers={"X-Admin-Token": admin_token}, timeout=15)
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"


def test_rbac_admin_shop_fleet_by_unit(admin_token):
    r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit",
                     headers={"X-Admin-Token": admin_token}, timeout=15)
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("hdr", ["X-Shop-Token", "X-Dispatch-Token", "X-Safety-Token"])
def test_rbac_invalid_token_shop_fleet(hdr):
    r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit",
                     headers={hdr: "invalid_token_xyz"}, timeout=15)
    assert r.status_code == 401, f"{hdr}: {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("route", FRONTEND_ROUTES)
def test_route_reachable(route):
    r = requests.get(f"{BASE_URL}{route}", timeout=20, allow_redirects=True)
    assert r.status_code == 200, f"{route}: {r.status_code}"
    assert "page not found" not in r.text.lower(), f"{route}: 'page not found' present"
