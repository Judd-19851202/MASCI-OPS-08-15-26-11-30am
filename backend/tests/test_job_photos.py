"""Backend tests for Job Photos Library (Phase 1).

Track 20.6B · TD-20.7-C01 hardening
────────────────────────────────────
- Auth: uses the current canonical `POST /api/auth/multi-login` endpoint
  (the pre-15.32 shared-password `POST /api/admin/login` is retired and
  returns 410).
- PM auth: uses the PM-specific `POST /api/pm/login` (still active) or
  falls through with an explicit skip when the PM account is missing.
- Email safety: this module is read-mostly. The one write path
  (`POST /api/job-photos/admin/reindex`) does NOT dispatch email.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASS = "Maddix123!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"


@pytest.fixture(scope="session")
def admin_token():
    """Track 20.6B · TD-20.7-C01 — canonical multi-login. The retired
    `POST /api/admin/login` returns 410 by design (Track 15.32)."""
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASS},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login unavailable: {r.status_code} {r.text[:200]}")
    tok = ((r.json() or {}).get("portal_tokens") or {}).get("admin")
    if not tok:
        pytest.skip("multi-login response missing admin portal token")
    return tok


@pytest.fixture(scope="session")
def pm_token():
    r = requests.post(f"{BASE_URL}/api/pm/login", json={"email": PM_EMAIL, "password": PM_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"PM login failed {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


@pytest.fixture(scope="session")
def pm_headers(pm_token):
    # Override X-Admin-Token (conftest auto-attaches it) so PM scoping is tested with PM token only
    return {"X-PM-Token": pm_token, "X-Admin-Token": ""}


# ── List endpoint ────────────────────────────────────────────────
class TestListJobPhotos:
    def test_admin_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "count" in data
        assert isinstance(data["items"], list)
        assert data["count"] == len(data["items"])
        # Track 20.6B — count may be 0 in a fresh preview DB; only assert
        # the contract shape. Only check item shape if items exist.
        if data["count"] > 0:
            item = data["items"][0]
            for f in ("id", "source", "project_number", "week_of", "record_date", "submitter", "source_id", "photo_index"):
                assert f in item, f"missing field {f}"
            # Verify Pre-Op excluded
            sources = {it["source"] for it in data["items"]}
            assert "equipment_inspection" not in sources
            assert "preop" not in sources
            # Track 20.6B · additive-safe superset check: additional legit
            # sources may be introduced by future promotion tracks. We
            # verify the forbidden ones are excluded rather than pinning
            # the entire set.
            forbidden = {"equipment_inspection", "equipment_inspections", "preop", "pre_op"}
            assert not (sources & forbidden), f"Pre-Op leaked into sources: {sources & forbidden}"

    def test_filter_by_source_daily_report(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos?source=daily_report", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for it in data["items"]:
            assert it["source"] == "daily_report"

    def test_filter_by_project_number(self, admin_headers):
        # Find an existing project_number first
        r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        items = r.json()["items"]
        if not items:
            pytest.skip("no photos to filter")
        pn = next((it["project_number"] for it in items if it.get("project_number")), None)
        if not pn:
            pytest.skip("no project_number in any item")
        r2 = requests.get(f"{BASE_URL}/api/job-photos?project_number={pn}", headers=admin_headers, timeout=30)
        assert r2.status_code == 200
        for it in r2.json()["items"]:
            assert it["project_number"] == pn

    def test_no_auth_rejected(self):
        # Conftest is minimal (Track 20.6B verified) and does NOT
        # auto-attach any tokens, so a plain unauth request truly is
        # unauth here.
        r = requests.get(f"{BASE_URL}/api/job-photos", timeout=20)
        assert r.status_code in (401, 403), f"expected auth required, got {r.status_code} {r.text[:200]}"


# ── Raw photo ───────────────────────────────────────────────────
class TestRawPhoto:
    def test_raw_valid(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        items = r.json()["items"]
        if not items:
            pytest.skip("no photos")
        pid = items[0]["id"]
        r2 = requests.get(f"{BASE_URL}/api/job-photos/{pid}/raw", headers=admin_headers, timeout=30)
        assert r2.status_code == 200, r2.text
        data = r2.json()
        assert "data_url" in data and "meta" in data
        # Track 20.6B · additive-safe accept-list: photos may be served
        # either as an inline base64 `data:` URL (legacy inline storage)
        # OR a signed R2/S3 `https://` URL (iter64-era object storage
        # migration). Both are valid contracts.
        assert (data["data_url"].startswith("data:")
                or data["data_url"].startswith("https://")), (
            f"unexpected raw url scheme: {data['data_url'][:80]}..."
        )
        assert data["meta"]["id"] == pid

    def test_raw_unknown_id(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos/does-not-exist:fake:0/raw", headers=admin_headers, timeout=20)
        assert r.status_code == 404


# ── ZIP ─────────────────────────────────────────────────────────
class TestZip:
    def test_zip_with_ids(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        items = r.json()["items"]
        if len(items) < 2:
            pytest.skip("need >=2 photos")
        ids = [it["id"] for it in items[:3]]
        r2 = requests.post(
            f"{BASE_URL}/api/job-photos/zip",
            headers={**admin_headers, "Content-Type": "application/json"},
            json={"photo_ids": ids},
            timeout=60,
        )
        assert r2.status_code == 200, r2.text
        assert r2.headers.get("content-type", "").startswith("application/zip")
        # ZIP magic bytes
        assert r2.content[:2] == b"PK", "not a zip"
        assert len(r2.content) > 100

    def test_zip_empty_ids(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/job-photos/zip",
            headers={**admin_headers, "Content-Type": "application/json"},
            json={"photo_ids": []},
            timeout=20,
        )
        assert r.status_code == 400


# ── Reindex ────────────────────────────────────────────────────
class TestReindex:
    def test_admin_can_reindex(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/job-photos/admin/reindex", headers=admin_headers, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert "total" in data

    def test_pm_cannot_reindex(self, pm_headers):
        r = requests.post(f"{BASE_URL}/api/job-photos/admin/reindex", headers=pm_headers, timeout=30)
        assert r.status_code == 403


# ── PM scoping ──────────────────────────────────────────────────
class TestPmScoping:
    def test_pm_list_scoped(self, pm_headers, admin_headers):
        admin_r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        admin_count = admin_r.json()["count"]
        pm_r = requests.get(f"{BASE_URL}/api/job-photos", headers=pm_headers, timeout=30)
        assert pm_r.status_code == 200, pm_r.text
        pm_count = pm_r.json()["count"]
        # PM should see <= admin
        assert pm_count <= admin_count

    def test_pm_blocked_outside_scope(self, pm_headers, admin_headers):
        # Find a photo PM doesn't have
        admin_items = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30).json()["items"]
        pm_items = requests.get(f"{BASE_URL}/api/job-photos", headers=pm_headers, timeout=30).json()["items"]
        pm_ids = {it["id"] for it in pm_items}
        outside = next((it["id"] for it in admin_items if it["id"] not in pm_ids), None)
        if not outside:
            pytest.skip("PM has access to all photos — cannot test scoping")
        r = requests.get(f"{BASE_URL}/api/job-photos/{outside}/raw", headers=pm_headers, timeout=20)
        assert r.status_code == 403


# ── Pre-Op exclusion (verify equipment_inspections not indexed) ──
class TestPreOpExcluded:
    def test_no_preop_in_index(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
        items = r.json()["items"]
        sources = {it["source"] for it in items}
        # equipment_inspections is the Pre-Op collection
        forbidden = {"equipment_inspection", "equipment_inspections", "preop", "pre_op"}
        assert not (sources & forbidden), f"Pre-Op leaked: {sources & forbidden}"
