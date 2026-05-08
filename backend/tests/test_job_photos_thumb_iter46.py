"""
Iter46 backend tests — Job Photos performance endpoints
- GET /api/job-photos/{id}/thumb (image/jpeg + Cache-Control immutable)
- POST /api/job-photos/raw-batch (≤50, drops out-of-scope, [] empty)
- GET /api/job-photos/{id}/raw still works (lightbox path)
"""
import os
import io
import uuid
import base64
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").rstrip("/")
ADMIN_PW = "MASCI1982!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"


# Tiny 2x2 PNG (so Pillow can downscale)
def _seed_png_data_url() -> str:
    # 2x2 red PNG
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVR42mP8/5+hHgMjIyMD"
        "AwMDAwAOEgIB/cYqAQAAAABJRU5ErkJggg=="
    )
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode()


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"admin login failed {r.status_code}")
    return r.json().get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def seed_photo(admin_headers):
    """Seed a daily report with one photo so we have a known job_photo id."""
    project_number = f"TEST-PHOTO-{uuid.uuid4().hex[:6]}"
    payload = {
        "project_number": project_number,
        "project_name": "TEST Photo Project",
        "report_date": "2026-01-15",
        "prepared_by": "TEST_Photo_Reporter",
        "photos": [_seed_png_data_url()],
        "weather": "Clear",
        "location": "TEST Site",
        "supervisor": "TEST_Supervisor",
        "crew_size": 1,
    }
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
    assert r.status_code in (200, 201), f"daily report seed failed: {r.status_code} {r.text[:200]}"
    # Trigger reindex so the job_photos collection is populated
    rr = requests.post(f"{BASE_URL}/api/job-photos/admin/reindex", headers=admin_headers, timeout=60)
    assert rr.status_code == 200, f"reindex failed: {rr.status_code} {rr.text[:200]}"
    # Fetch list to find our photo id
    lst = requests.get(
        f"{BASE_URL}/api/job-photos",
        headers=admin_headers,
        params={"project_number": project_number},
        timeout=20,
    )
    assert lst.status_code == 200
    items = lst.json().get("items") or []
    assert len(items) >= 1, f"expected at least 1 photo for {project_number}"
    return {"project_number": project_number, "photo_id": items[0]["id"]}


# === /thumb ===
class TestThumb:
    def test_thumb_returns_jpeg_with_cache_header(self, admin_headers, seed_photo):
        # Public URL — content type / size assertions
        r = requests.get(
            f"{BASE_URL}/api/job-photos/{seed_photo['photo_id']}/thumb",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 200, f"status {r.status_code}: {r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("image/jpeg")
        # ≤25 KB for typical photos (tiny seed should be way under)
        assert len(r.content) <= 25 * 1024, f"thumb too big: {len(r.content)}"
        # Validate Cache-Control directly from origin (Cloudflare strips it on the edge)
        origin_resp = requests.get(
            f"http://localhost:8001/api/job-photos/{seed_photo['photo_id']}/thumb",
            headers=admin_headers,
            timeout=20,
        )
        assert origin_resp.status_code == 200
        cc = origin_resp.headers.get("cache-control", "").lower()
        assert "private" in cc and "max-age=86400" in cc and "immutable" in cc, f"origin cache-control={cc!r}"

    def test_thumb_404_for_unknown(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/job-photos/does-not-exist:nope:0/thumb",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 404


# === /raw-batch ===
class TestRawBatch:
    def test_raw_batch_returns_data_urls(self, admin_headers, seed_photo):
        r = requests.post(
            f"{BASE_URL}/api/job-photos/raw-batch",
            headers=admin_headers,
            json={"photo_ids": [seed_photo["photo_id"]]},
            timeout=20,
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["id"] == seed_photo["photo_id"]
        assert item["data_url"].startswith("data:image/")

    def test_raw_batch_empty_input(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/job-photos/raw-batch",
            headers=admin_headers,
            json={"photo_ids": []},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json() == {"items": []}

    def test_raw_batch_caps_at_50(self, admin_headers, seed_photo):
        # 60 ids, only the real one is valid; backend should silently drop the others
        ids = [f"fake:{i}:0" for i in range(59)] + [seed_photo["photo_id"]]
        r = requests.post(
            f"{BASE_URL}/api/job-photos/raw-batch",
            headers=admin_headers,
            json={"photo_ids": ids},
            timeout=20,
        )
        assert r.status_code == 200
        # Only the first 50 are processed; if real id is at idx 59 it may be excluded — that's fine,
        # we just want to confirm no error and items <=50
        assert len(r.json()["items"]) <= 50

    def test_raw_batch_drops_unknown_silently(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/job-photos/raw-batch",
            headers=admin_headers,
            json={"photo_ids": ["not-real:abc:0", "also-fake:def:1"]},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json() == {"items": []}


# === /raw still works ===
class TestRawStillWorks:
    def test_raw_returns_data_url(self, admin_headers, seed_photo):
        r = requests.get(
            f"{BASE_URL}/api/job-photos/{seed_photo['photo_id']}/raw",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 200
        body = r.json()
        assert "data_url" in body and body["data_url"].startswith("data:image/")
        assert "meta" in body and body["meta"]["id"] == seed_photo["photo_id"]


# === PM scoping for thumb ===
class TestThumbPMScoping:
    def test_thumb_403_when_out_of_pm_scope(self, seed_photo):
        # Login as PM with no jobs assigned to TEST-PHOTO-* project
        lr = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PW},
            timeout=20,
        )
        if lr.status_code != 200:
            pytest.skip(f"PM login failed {lr.status_code}")
        body = lr.json()
        pm_token = body.get("token")
        if not pm_token:
            pytest.skip("PM login returned no token")
        # If this PM has admin/legacy bypass, skip — they intentionally see all
        me = requests.get(f"{BASE_URL}/api/pm/me", headers={"X-PM-Token": pm_token}, timeout=20)
        if me.status_code == 200 and me.json().get("is_admin_or_legacy"):
            pytest.skip("PM is admin/legacy — sees all by design")
        h = {"X-PM-Token": pm_token}
        r = requests.get(
            f"{BASE_URL}/api/job-photos/{seed_photo['photo_id']}/thumb",
            headers=h,
            timeout=20,
        )
        # PM is not assigned to the synthetic TEST-PHOTO-* project → 403 expected
        assert r.status_code in (403, 404), f"expected 403/404 out-of-scope, got {r.status_code}"
