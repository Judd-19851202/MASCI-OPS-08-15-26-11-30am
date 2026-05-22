"""
test_iter347_promo_asset_library.py — Promo Asset Library regression.

iter347 ships the admin-only promo asset library:
  • R2-backed object storage under promo-assets/ prefix
  • POST upload / GET list+filter / GET detail (signed url) /
    PATCH metadata / DELETE / GET manifest / GET categories
  • /api/admin/promo-assets/* — all admin-strict
  • New frontend page /admin/promo-assets
  • Optional homepage hero loop player (env-driven, zero footprint until wired)
  • Production brief at /app/memory/MASCI_OPS_FILM_PRODUCTION_BRIEF.md
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path

import httpx
import pytest

API_URL = os.environ.get(
    "API_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend/src"
PROMO_PAGE = FRONTEND_SRC / "pages/admin/AdminPromoAssets.jsx"
HERO_LOOP = FRONTEND_SRC / "components/PromoHeroLoop.jsx"
ADMIN_SHELL = FRONTEND_SRC / "components/AdminShell.jsx"
APP_JS = FRONTEND_SRC / "App.js"
BRIEF = ROOT / "memory/MASCI_OPS_FILM_PRODUCTION_BRIEF.md"
STORAGE = ROOT / "backend/promo_assets_storage.py"
ROUTE = ROOT / "backend/routes/promo_assets.py"


# ── Source-level structural locks ───────────────────────────────────


def test_storage_module_exists_and_reuses_r2_client():
    """promo_assets_storage piggybacks on photo_storage's R2 client —
    no second SDK surface, no second env-var set."""
    src = STORAGE.read_text()
    assert "import photo_storage" in src
    assert "PROMO_KEY_PREFIX" in src and '"promo-assets"' in src
    assert "presigned_url" in src
    assert "upload_bytes" in src
    assert "delete_ref" in src


def test_route_module_exists():
    src = ROUTE.read_text()
    assert "build_promo_assets_router" in src
    assert "PROMO_CATEGORIES" in src
    # Admin-strict dependency wired at router level
    assert "dependencies=[Depends(require_admin_strict_dep)]" in src
    # All required endpoints
    for snippet in [
        '@router.get("/categories")',
        '@router.get("")',
        '@router.post("")',
        '@router.get("/manifest.json")',
        '@router.get("/{asset_id}")',
        '@router.patch("/{asset_id}")',
        '@router.delete("/{asset_id}")',
        '@router.get("/{asset_id}/download")',
    ]:
        assert snippet in src, f"missing route: {snippet}"


def test_frontend_page_exists_with_required_testids():
    src = PROMO_PAGE.read_text()
    # data-testid literals in JSX
    for tid in [
        "admin-promo-assets-page",
        "promo-upload-btn",
        "promo-empty-state",
        "promo-manifest-export",
        "promo-refresh",
        "promo-search-input",
        "promo-filter-category",
        "promo-filter-visibility",
        "promo-clear-filters",
        "promo-upload-dialog",
        "promo-upload-file",
        "promo-upload-submit",
        "promo-preview-dialog",
        "promo-edit-dialog",
    ]:
        assert f'data-testid="{tid}"' in src, f"missing data-testid: {tid}"
    # StatPill children get their testids via the `testid` prop
    for tid in [
        "promo-stat-total",
        "promo-stat-categories",
        "promo-stat-public",
        "promo-stat-size",
    ]:
        assert f'testid="{tid}"' in src, f"missing StatPill testid prop: {tid}"
    # Uses the shared sanitizer
    assert 'from "@/lib/errors"' in src and "operationalError(e," in src
    # Bilingual
    assert "useT" in src and "t(" in src


def test_hero_loop_component_is_env_gated_and_safe():
    src = HERO_LOOP.read_text()
    # Reads three env vars
    for env in (
        "REACT_APP_PROMO_HERO_LOOP_URL",
        "REACT_APP_PROMO_FULL_VIDEO_URL",
        "REACT_APP_PROMO_POSTER_URL",
    ):
        assert env in src
    # Returns null until env is wired — zero footprint
    assert "if (!HERO_URL) return null;" in src
    # ESC closes modal
    assert "Escape" in src
    # iOS-safe autoplay
    assert "muted" in src and "playsInline" in src
    # data-testids for the player + modal
    for tid in ("promo-hero-loop", "promo-hero-loop-video", "promo-hero-modal", "promo-hero-modal-video", "promo-hero-modal-close"):
        assert f'data-testid="{tid}"' in src


def test_app_route_wired():
    src = APP_JS.read_text()
    assert "AdminPromoAssets" in src
    assert '/admin/promo-assets' in src


def test_capture_mode_util_exists():
    """`?capture=1` capture-mode utility exists and is wired into the
    three operational banners (BannerStrip, BackendStatusBanner,
    PersistenceHealthBanner). Promo clips stay clean without disabling
    banners for normal operators."""
    capture_lib = FRONTEND_SRC / "lib/captureMode.js"
    assert capture_lib.exists()
    src = capture_lib.read_text()
    assert "useCaptureMode" in src
    assert 'capture=1' in src or "get(\"capture\")" in src
    assert "sessionStorage" in src

    # Each operational banner short-circuits on capture mode
    for rel in [
        "components/BannerStrip.jsx",
        "components/BackendStatusBanner.jsx",
        "components/PersistenceHealthBanner.jsx",
    ]:
        s = (FRONTEND_SRC / rel).read_text()
        assert "useCaptureMode" in s, f"{rel} not importing useCaptureMode"
        assert "if (captureMode) return null;" in s, (
            f"{rel} not short-circuiting in capture mode"
        )


def test_admin_sidebar_has_promo_assets_link():
    src = ADMIN_SHELL.read_text()
    assert 'to: "/admin/promo-assets"' in src
    assert '"Promo Assets"' in src


def test_production_brief_exists_with_required_sections():
    assert BRIEF.exists(), "production brief missing"
    src = BRIEF.read_text()
    for must in [
        "Production Brief",
        "Voiceover script",
        "Shot list",
        "Export matrix",
        "Asset naming conventions",
        "REACT_APP_PROMO_HERO_LOOP_URL",
        "Hours Saved. Every Day.",
        "Built For The Field.",
        # iter347 follow-up — capture-mode documented in the brief
        "?capture=1",
        "capture-mode",
    ]:
        assert must in src, f"brief missing required section: {must}"


# ── E2E auth + CRUD against the live backend ────────────────────────


@pytest.fixture(scope="module")
def admin_token():
    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{API_URL}/api/auth/multi-login",
                json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            )
            r.raise_for_status()
            return r.json()["portal_tokens"]["admin"]

    return asyncio.get_event_loop().run_until_complete(_run())


def test_categories_endpoint(admin_token):
    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets/categories",
                headers={"X-Admin-Token": admin_token},
            )
            assert r.status_code == 200
            d = r.json()
            # 26 categories per the bounded enum
            assert len(d["categories"]) == 26
            assert "Hero Loops" in d["categories"]
            assert "Final Exports" in d["categories"]
            assert set(d["visibilities"]) == {"internal", "public"}

    asyncio.get_event_loop().run_until_complete(_run())


def test_rbac_anon_blocked():
    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            for path in (
                "",
                "/categories",
                "/manifest.json",
            ):
                r = await client.get(f"{API_URL}/api/admin/promo-assets{path}")
                assert r.status_code == 401, f"anon got {r.status_code} on {path}"

    asyncio.get_event_loop().run_until_complete(_run())


def test_full_crud_lifecycle(admin_token):
    """Upload tiny file → list → get → patch → delete → 404."""

    async def _run():
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {
                "file": ("iter347_lifecycle.mp4", b"\x00" * 1024, "video/mp4"),
            }
            data = {
                "name": "Iter347 Lifecycle Test",
                "category": "Raw Screen Captures",
                "description": "regression test",
                "tags": "iter347,lifecycle",
                "visibility": "internal",
                "duration_seconds": "8",
                "resolution": "1920x1080",
                "aspect_ratio": "16:9",
            }
            r = await client.post(
                f"{API_URL}/api/admin/promo-assets",
                headers={"X-Admin-Token": admin_token},
                files=files,
                data=data,
            )
            assert r.status_code == 200, r.text[:300]
            asset = r.json()["asset"]
            asset_id = asset["id"]
            assert asset["file_ref"].startswith("promo://")
            assert asset["category"] == "Raw Screen Captures"
            assert "iter347" in asset["tags"]

            # GET — should attach a presigned playback_url
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets/{asset_id}",
                headers={"X-Admin-Token": admin_token},
            )
            assert r.status_code == 200
            assert r.json()["asset"]["playback_url"]

            # LIST with filter
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets",
                headers={"X-Admin-Token": admin_token},
                params={"category": "Raw Screen Captures", "q": "Lifecycle"},
            )
            assert r.status_code == 200
            d = r.json()
            assert d["count"] >= 1
            assert any(a["id"] == asset_id for a in d["items"])

            # MANIFEST should include our row
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets/manifest.json",
                headers={"X-Admin-Token": admin_token},
            )
            assert r.status_code == 200
            man = r.json()
            assert man["version"] == 1
            assert any(a["id"] == asset_id for a in man["items"])
            assert "Content-Disposition" in r.headers

            # DOWNLOAD redirect
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets/{asset_id}/download",
                headers={"X-Admin-Token": admin_token},
                follow_redirects=False,
            )
            assert r.status_code == 302
            assert "X-Amz-Signature" in (r.headers.get("location") or "")

            # PATCH
            r = await client.patch(
                f"{API_URL}/api/admin/promo-assets/{asset_id}",
                headers={"X-Admin-Token": admin_token},
                json={"name": "Iter347 Lifecycle (renamed)", "visibility": "public"},
            )
            assert r.status_code == 200
            a = r.json()["asset"]
            assert a["name"] == "Iter347 Lifecycle (renamed)"
            assert a["visibility"] == "public"

            # DELETE
            r = await client.delete(
                f"{API_URL}/api/admin/promo-assets/{asset_id}",
                headers={"X-Admin-Token": admin_token},
            )
            assert r.status_code == 200
            assert r.json()["deleted"] == asset_id

            # GET after delete → 404
            r = await client.get(
                f"{API_URL}/api/admin/promo-assets/{asset_id}",
                headers={"X-Admin-Token": admin_token},
            )
            assert r.status_code == 404

    asyncio.get_event_loop().run_until_complete(_run())


def test_invalid_category_rejected(admin_token):
    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("x.mp4", b"\x00" * 128, "video/mp4")}
            data = {
                "name": "x",
                "category": "Made Up Category That Doesn't Exist",
                "visibility": "internal",
            }
            r = await client.post(
                f"{API_URL}/api/admin/promo-assets",
                headers={"X-Admin-Token": admin_token},
                files=files,
                data=data,
            )
            assert r.status_code == 400

    asyncio.get_event_loop().run_until_complete(_run())


def test_invalid_visibility_rejected(admin_token):
    async def _run():
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("x.mp4", b"\x00" * 128, "video/mp4")}
            data = {
                "name": "x",
                "category": "Raw Screen Captures",
                "visibility": "ghost",
            }
            r = await client.post(
                f"{API_URL}/api/admin/promo-assets",
                headers={"X-Admin-Token": admin_token},
                files=files,
                data=data,
            )
            assert r.status_code == 400

    asyncio.get_event_loop().run_until_complete(_run())
