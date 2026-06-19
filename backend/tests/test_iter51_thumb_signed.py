"""Iter51 backend tests — Job Photos thumb-signed pipeline.

Covers:
- /api/job-photos returns thumb_token per item
- /thumb-signed?t=<valid> → 200 + image bytes + X-Thumb-Cache header miss/hit
- /thumb-signed?t=<bogus> → 403
- /thumb-signed without ?t= → 422
- Token is photo_id-bound (token for A used on B → 403)
- /thumb (auth header path) still works
- Content negotiation: AVIF / WebP / JPEG
- Cache-Control header includes 'public, max-age=' and 'immutable' (signed
  URLs are photo-id-bound HMAC tokens that are SAFE to cache publicly at
  the CDN edge — that's exactly what unlocked iter51's perf gains)
- /admin/reindex wipes job_photo_thumb_cache
- pillow_heif registered (import side-effect)
"""
from __future__ import annotations

import base64
import io
import os
import sys
import time

import pytest
import requests

_RAW_BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
import pytest as _pytest
if not _RAW_BASE_URL:
    _pytest.skip(
        "REACT_APP_BACKEND_URL not set · live-HTTP test skipped (parity-lock safe).",
        allow_module_level=True,
    )
BASE_URL = _RAW_BASE_URL.rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Maddix123!")

# Allow `import routes.job_photos` for the HEIF-registration assertion.
sys.path.insert(0, "/app/backend")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    tok = r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token}


@pytest.fixture(scope="module")
def photos_list(admin_headers):
    r = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and isinstance(data["items"], list)
    return data["items"]


def _real_photo_id(items):
    """Find the patched real-JPEG photo on TEST-001."""
    for it in items:
        if it.get("project_number") == "TEST-001" and it.get("photo_index") == 0:
            return it["id"], it["thumb_token"]
    # fallback: first item
    if items:
        return items[0]["id"], items[0]["thumb_token"]
    pytest.skip("no photos in DB")


# 1. List endpoint mints thumb_token on every item
def test_list_includes_thumb_token(photos_list):
    assert len(photos_list) > 0, "no photos in preview DB"
    for it in photos_list:
        assert "thumb_token" in it, f"missing thumb_token on {it.get('id')}"
        assert "." in it["thumb_token"], "token format <exp>.<sig>"


# 2. /thumb-signed?t=<valid> → 200 with image bytes
def test_thumb_signed_valid_token_returns_image(photos_list):
    pid, tok = _real_photo_id(photos_list)
    # First wipe cache via admin reindex so we get a deterministic miss
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": tok},
        headers={"Accept": "image/jpeg"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("Content-Type", "").startswith("image/")
    assert len(r.content) > 0
    # NOTE: validate Cache-Control via direct uvicorn — the preview ingress
    # (Cloudflare) rewrites it to "no-store, no-cache, must-revalidate".
    # Critical finding for production: see iteration_51 test report.
    local = requests.get(
        f"http://localhost:8001/api/job-photos/{pid}/thumb-signed",
        params={"t": tok}, headers={"Accept": "image/jpeg"}, timeout=15,
    )
    cc_local = local.headers.get("Cache-Control", "")
    assert "public" in cc_local and "max-age=" in cc_local and "immutable" in cc_local, (
        f"Backend code-level Cache-Control wrong: {cc_local!r}"
    )
    assert "X-Thumb-Cache" in r.headers


# 3. Cache miss → hit on second call
def test_thumb_signed_cache_miss_then_hit(admin_headers, photos_list):
    # Clear the cache via reindex
    r = requests.post(
        f"{BASE_URL}/api/job-photos/admin/reindex", headers=admin_headers, timeout=60
    )
    assert r.status_code == 200, r.text

    # Re-list (ids stay stable, but thumb_token rotates fine)
    r2 = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30)
    items = r2.json()["items"]
    pid, tok = _real_photo_id(items)

    h = {"Accept": "image/jpeg"}
    r1 = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed", params={"t": tok}, headers=h, timeout=30
    )
    assert r1.status_code == 200, r1.text
    cache1 = r1.headers.get("X-Thumb-Cache")
    r2 = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed", params={"t": tok}, headers=h, timeout=30
    )
    assert r2.status_code == 200
    cache2 = r2.headers.get("X-Thumb-Cache")
    # First call should miss, second should hit
    assert cache1 == "miss", f"expected miss got {cache1}"
    assert cache2 == "hit", f"expected hit got {cache2}"


# 4. /thumb-signed?t=<bogus> → 403
def test_thumb_signed_bogus_token_403(photos_list):
    pid, _ = _real_photo_id(photos_list)
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": "9999999999.deadbeef"},
        timeout=15,
    )
    assert r.status_code == 403, r.text


# 5. /thumb-signed without t= → 422
def test_thumb_signed_missing_token_422(photos_list):
    pid, _ = _real_photo_id(photos_list)
    r = requests.get(f"{BASE_URL}/api/job-photos/{pid}/thumb-signed", timeout=15)
    assert r.status_code == 422, r.text


# 6. Token is photo_id-bound → mint for A, use on B → 403
def test_token_is_photo_id_bound(photos_list):
    if len(photos_list) < 2:
        pytest.skip("need at least 2 photos")
    a = photos_list[0]
    b = next((p for p in photos_list[1:] if p["id"] != a["id"]), None)
    if not b:
        pytest.skip("need 2 distinct photos")
    # Use A's token on B
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{b['id']}/thumb-signed",
        params={"t": a["thumb_token"]},
        timeout=15,
    )
    assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"


# 7. /thumb (auth-header path) still works
def test_thumb_auth_header_path_works(admin_headers, photos_list):
    pid, _ = _real_photo_id(photos_list)
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb",
        headers={**admin_headers, "Accept": "image/jpeg"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("Content-Type", "").startswith("image/")
    assert len(r.content) > 0


# 8. Content negotiation
def test_content_negotiation_avif(photos_list):
    pid, tok = _real_photo_id(photos_list)
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": tok},
        headers={"Accept": "image/avif,image/webp,image/jpeg"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    # AVIF requires libavif compiled into Pillow; gracefully fall back is allowed
    ct = r.headers.get("Content-Type", "")
    assert ct in ("image/avif", "image/webp", "image/jpeg"), ct
    print(f"AVIF accept → {ct}")


def test_content_negotiation_webp(photos_list):
    pid, tok = _real_photo_id(photos_list)
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": tok},
        headers={"Accept": "image/webp,image/jpeg"},
        timeout=30,
    )
    assert r.status_code == 200
    ct = r.headers.get("Content-Type", "")
    assert ct in ("image/webp", "image/jpeg"), ct


def test_content_negotiation_jpeg_only(photos_list):
    pid, tok = _real_photo_id(photos_list)
    r = requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": tok},
        headers={"Accept": "image/jpeg"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.headers.get("Content-Type") == "image/jpeg"


# 9. Reindex wipes thumb cache
def test_admin_reindex_wipes_thumb_cache(admin_headers, photos_list):
    pid, tok = _real_photo_id(photos_list)
    # Prime cache
    requests.get(
        f"{BASE_URL}/api/job-photos/{pid}/thumb-signed",
        params={"t": tok}, headers={"Accept": "image/jpeg"}, timeout=30,
    )
    r = requests.post(
        f"{BASE_URL}/api/job-photos/admin/reindex", headers=admin_headers, timeout=60
    )
    assert r.status_code == 200, r.text
    # Re-mint token (reindex changes record_dates but not ids)
    items = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=30).json()["items"]
    pid2, tok2 = _real_photo_id(items)
    r2 = requests.get(
        f"{BASE_URL}/api/job-photos/{pid2}/thumb-signed",
        params={"t": tok2}, headers={"Accept": "image/jpeg"}, timeout=30,
    )
    assert r2.status_code == 200
    assert r2.headers.get("X-Thumb-Cache") == "miss", "reindex should wipe cache"


# 10. pillow-heif registration verified
def test_pillow_heif_registered():
    """Importing routes.job_photos should not error and HEIF opener should be installed."""
    import routes.job_photos  # noqa: F401
    from PIL import Image
    # If pillow_heif registered, "HEIF" should be in registered extensions
    try:
        import pillow_heif  # noqa: F401
    except ImportError:
        pytest.skip("pillow_heif not installed in this env")
    # Confirm HEIF format is registered
    assert "HEIF" in Image.registered_extensions().values() or "HEIC" in Image.registered_extensions().values() or any(
        "heif" in str(v).lower() or "heic" in str(v).lower() for v in Image.registered_extensions().values()
    ), "HEIF/HEIC opener not registered with Pillow"
