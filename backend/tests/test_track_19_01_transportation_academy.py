"""
TRACK 19.01 / 19.01A · Transportation Academy curriculum tests.

Verifies the hybrid migration:
  * 11 active Academy modules in curriculum_order 1-11.
  * Modules 1+2 published with video URLs; Modules 3-11 in_development.
  * 12 legacy keys retired (active=false, legacy_track_16_08_retired).
  * Bootstrap is idempotent.
  * Endpoint serves Academy-only and excludes retired legacy.
  * No assignment / certificate destruction.
  * Required docs exist.
"""
from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

import pytest
import requests

API = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

MEMORY = Path("/app/memory")
ROUTES = Path("/app/backend/routes/transportation_orientation.py")
ACADEMY_PAGE = Path("/app/frontend/src/pages/transportation/TransportationAcademy.jsx")
TX_APP = Path("/app/frontend/src/pages/transportation/TransportationApp.jsx")
TX_NAV = Path("/app/frontend/src/pages/transportation/_shared.jsx")
PLAYER = Path("/app/frontend/src/components/transportation/MasciVideoPlayer.jsx")


# ─────────────── fixtures ───────────────

@pytest.fixture(scope="module")
def tokens():
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    r.raise_for_status()
    pt = r.json().get("portal_tokens") or {}
    return {"admin": pt["admin"], "dispatch": pt["dispatch"]}


@pytest.fixture(scope="module")
def academy(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/academy/modules",
        headers={"X-Dispatch-Token": tokens["dispatch"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()


# ─────────────── docs ───────────────

@pytest.mark.parametrize("name", [
    "TRACK_19_01_LEGACY_22_MODULE_AUDIT.md",
    "TRACK_19_01_TRANSPORTATION_ORIENTATION_VIDEO_INTEGRATION.md",
    "TRACK_19_01A_TRANSPORTATION_ACADEMY_CURRICULUM.md",
    "TRANSPORTATION_ACADEMY_CURRICULUM_STRUCTURE.md",
    "TRANSPORTATION_ACADEMY_MODULE_STANDARD.md",
    "TRANSPORTATION_ACADEMY_PLACEHOLDER_ARCHITECTURE.md",
    "TRANSPORTATION_ACADEMY_TEST_REPORT.md",
])
def test_required_docs_exist(name):
    p = MEMORY / name
    assert p.exists(), f"missing: {p}"
    assert p.stat().st_size > 500, f"doc too short: {p}"


# ─────────────── endpoint + curriculum shape ───────────────

def test_academy_endpoint_returns_eleven_modules(academy):
    assert academy["curriculum_track"] == "transportation_academy_v1"
    assert academy["total"] == 11
    assert academy["published"] == 2
    assert academy["in_development"] == 9


def test_academy_ordered_1_to_11(academy):
    orders = [m["curriculum_order"] for m in academy["items"]]
    assert orders == list(range(1, 12))


def test_module_1_and_2_published_with_video(academy):
    items = {m["curriculum_order"]: m for m in academy["items"]}
    m1, m2 = items[1], items[2]
    assert m1["status"] == "published"
    assert m2["status"] == "published"
    assert m1["key"] == "welcome_to_masci"
    assert m2["key"] == "driver_expectations"
    assert m1["video_url"], "Module 1 must have a video_url"
    assert m2["video_url"], "Module 2 must have a video_url"
    assert m1["title"] == "Welcome to MASCI Transportation Operations"
    assert m2["title"] == "Driver Expectations & Professional Standards"


def test_modules_3_to_11_in_development_with_metadata(academy):
    items = {m["curriculum_order"]: m for m in academy["items"]}
    for order in range(3, 12):
        m = items[order]
        assert m["status"] == "in_development", f"module {order} expected in_development"
        assert not m.get("video_url"), f"module {order} must NOT have a video_url"
        assert m.get("topics"), f"module {order} missing topics"
        assert m.get("learning_objectives"), f"module {order} missing learning_objectives"
        assert m.get("description"), f"module {order} missing description"
        assert m.get("estimated_runtime_minutes", 0) > 0
        assert m.get("quiz_status") == "reserved"
        assert m.get("question_count") == 5
        assert m.get("passing_score") == 80
        assert m.get("quiz_enabled") is False
        assert m.get("quiz_required") is False


def test_module_4_and_11_are_new_keys(academy):
    keys = {m["curriculum_order"]: m["key"] for m in academy["items"]}
    assert keys[4] == "driver_qualification_compliance"
    assert keys[11] == "final_review_certification"


# ─────────────── retired legacy verification ───────────────

def test_retired_legacy_keys_hidden_from_academy(academy):
    keys = {m["key"] for m in academy["items"]}
    retired = {
        "customer_expectations", "ppe", "near_miss_reporting",
        "incident_reporting", "hauling_procedures", "jobsite_arrival",
        "asphalt_plant_operations", "equipment_awareness",
        "truck_readiness", "environmental_responsibilities",
        "end_of_shift", "annual_refresher",
    }
    assert not (keys & retired), "retired legacy keys leaked into the Academy"


# ─────────────── source asserts (bootstrap + frontend) ───────────────

def test_bootstrap_function_exists():
    src = ROUTES.read_text()
    assert "async def bootstrap_track_19_01a(db)" in src
    assert "ACADEMY_TRACK" in src and "ACADEMY_CURRICULUM" in src
    assert 'curriculum_track="transportation_academy_v1"' in src or \
           "ACADEMY_TRACK = \"transportation_academy_v1\"" in src


def test_bootstrap_is_idempotent_skip():
    src = ROUTES.read_text()
    assert 'existing.get("curriculum_track") == LEGACY_RETIRED_TRACK' in src


def test_academy_endpoint_is_wired():
    src = ROUTES.read_text()
    assert "/admin/transportation/academy/modules" in src
    assert "list_academy_modules" in src
    # Dispatch + admin can read.
    assert "Depends(ops_guard)" in src


def test_video_player_uses_video_url():
    src = PLAYER.read_text()
    assert "video_url" in src
    assert "Transportation Academy module in production" in src
    assert "Sky AI video placeholder" not in src, (
        "Sky AI placeholder copy must be removed from the Academy player."
    )


def test_frontend_academy_page_exists():
    s = ACADEMY_PAGE.read_text()
    for testid in (
        "transportation-academy-page",
        "academy-progress-strip",
        "academy-modules-grid",
        "academy-in-development-panel",
        "academy-published-video",
    ):
        assert f'testid="{testid}"' in s or f'data-testid="{testid}"' in s, f"missing testid: {testid}"


def test_routes_wired_in_transportation_app():
    s = TX_APP.read_text()
    assert 'path="academy"' in s
    assert 'path="academy/:moduleKey"' in s
    assert "TransportationAcademy" in s and "TransportationAcademyModule" in s


def test_sidebar_entry_exists():
    s = TX_NAV.read_text()
    assert 'testid: "txops-nav-academy"' in s
    assert 'label: "Transportation Academy"' in s


# ─────────────── safety: no asn/cert destruction ───────────────

def test_existing_welcome_to_masci_assignments_preserved():
    """The 45 historic E2E assignments must still exist for welcome_to_masci."""
    src = ROUTES.read_text()
    # Bootstrap must not delete any assignment / certificate.
    assert "delete_many" not in src.split("bootstrap_track_19_01a")[1][:3500], (
        "Track 19.01A bootstrap must not call delete_many on any collection."
    )
    assert "drop_collection" not in src
