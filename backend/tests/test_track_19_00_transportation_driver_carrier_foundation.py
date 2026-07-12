"""
TRACK 19.00 · Transportation Driver + Carrier Operations Foundation tests.

These tests cover:
  1. Documentation deliverables exist.
  2. Backend route exposure (eligible-hr-cdl-drivers, link-from-hr, open
     POST/PATCH for /persons and /carriers).
  3. Permission policy — dispatcher can write to drivers + carriers
     while admin-only governance endpoints stay admin-only.
  4. CDL vs non-CDL classification — non-CDL approved drivers cannot
     enter the Transportation haul-driver list via link-from-hr.
  5. Idempotency / duplicate prevention.
  6. Backfill script (dry-run default · no boot wiring).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests

API = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
MEMORY = Path("/app/memory")
ROUTES_FILE = Path("/app/backend/routes/transportation.py")
SCRIPT_FILE = Path("/app/backend/scripts/track_19_00_link_hr_cdl_to_transport.py")


# ─────────────────────── fixtures ───────────────────────

@pytest.fixture(scope="module")
def tokens():
    """Multi-login → admin + dispatch tokens."""
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    r.raise_for_status()
    body = r.json()
    pt = body.get("portal_tokens") or {}
    assert pt.get("admin"), "admin portal token missing"
    assert pt.get("dispatch"), "dispatch portal token missing"
    return {"admin": pt["admin"], "dispatch": pt["dispatch"]}


def _dispatch(token):
    return {"X-Dispatch-Token": token, "Content-Type": "application/json"}


def _admin(token):
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


# ─────────────────────── 1 · Doc deliverables ───────────────────────

@pytest.mark.parametrize("name", [
    "TRACK_19_00_TRANSPORTATION_DRIVER_CARRIER_FOUNDATION.md",
    "TRACK_19_00_HR_DRIVER_MODEL_AUDIT.md",
    "TRACK_19_00_TRANSPORTATION_DRIVER_MODEL_AUDIT.md",
    "TRACK_19_00_CARRIER_MODEL_AUDIT.md",
    "TRANSPORTATION_DRIVER_CLASSIFICATION_STANDARD.md",
    "TRANSPORTATION_DRIVER_CARRIER_PERMISSION_MATRIX.md",
    "TRANSPORTATION_DRIVER_CARRIER_BACKFILL_PLAN.md",
])
def test_required_docs_exist(name):
    path = MEMORY / name
    assert path.exists(), f"required doc missing: {path}"
    assert path.stat().st_size > 600, f"required doc too short: {path}"


# ─────────────────────── 2 · eligible-hr-cdl-drivers ───────────────────────

def test_eligible_hr_cdl_drivers_accepts_dispatch_token(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/eligible-hr-cdl-drivers?limit=5",
        headers={"X-Dispatch-Token": tokens["dispatch"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "count" in body
    # Every returned row must be a CDL holder; non-CDL approved drivers
    # must not pollute this list.
    for row in body["items"]:
        assert row["cdl_holder"] is True


def test_eligible_hr_cdl_drivers_excludes_already_linked(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/eligible-hr-cdl-drivers?limit=50",
        headers={"X-Dispatch-Token": tokens["dispatch"]},
        timeout=15,
    )
    assert r.status_code == 200
    for row in r.json()["items"]:
        # Default scope hides already-linked rows.
        assert row.get("already_linked") is False


def test_eligible_hr_cdl_drivers_accepts_admin_token(tokens):
    r = requests.get(
        f"{API}/api/admin/transportation/eligible-hr-cdl-drivers?limit=3",
        headers={"X-Admin-Token": tokens["admin"]},
        timeout=15,
    )
    assert r.status_code == 200


# ─────────────────────── 3 · link-from-hr ───────────────────────

def test_link_from_hr_rejects_unknown_employee(tokens):
    r = requests.post(
        f"{API}/api/admin/transportation/persons/link-from-hr",
        headers=_dispatch(tokens["dispatch"]),
        json={"employee_id": "TRACK_19_00_NONEXISTENT_EMPLOYEE"},
        timeout=15,
    )
    assert r.status_code == 404, r.text
    assert "not found" in r.text.lower()


def test_link_from_hr_idempotent_and_succeeds(tokens):
    # Pick a real eligible CDL driver
    r0 = requests.get(
        f"{API}/api/admin/transportation/eligible-hr-cdl-drivers?include_linked=true&limit=10",
        headers={"X-Dispatch-Token": tokens["dispatch"]},
        timeout=15,
    )
    assert r0.status_code == 200
    items = r0.json().get("items") or []
    assert items, "no eligible HR CDL drivers in preview DB to drive idempotency test"
    target = items[0]
    emp_id = target["employee_id"]

    # First call → either new or already linked
    r1 = requests.post(
        f"{API}/api/admin/transportation/persons/link-from-hr",
        headers=_dispatch(tokens["dispatch"]),
        json={"employee_id": emp_id},
        timeout=15,
    )
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert "id" in body1
    assert body1["kind"] == "masci_employee"

    # Second call → must report already_linked=True with the same id
    r2 = requests.post(
        f"{API}/api/admin/transportation/persons/link-from-hr",
        headers=_dispatch(tokens["dispatch"]),
        json={"employee_id": emp_id},
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2.get("already_linked") is True
    assert body2["id"] == body1["id"]


# ─────────────────────── 4 · carrier write opened to dispatch ───────────────────────

@pytest.fixture(scope="module")
def carrier_created(tokens):
    import time
    unique_name = f"Track 19.00 Pytest Carrier LLC {int(time.time() * 1000)}"
    r = requests.post(
        f"{API}/api/admin/transportation/carriers",
        headers=_dispatch(tokens["dispatch"]),
        json={
            "legal_name": unique_name,
            "carrier_type": "leased_hauler",
            "dot_number": f"19{int(time.time()) % 1000000}",
            "status": "pending_review",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    body["_expected_legal_name"] = unique_name
    return body


def test_dispatch_can_create_carrier(carrier_created):
    assert carrier_created["id"]
    assert carrier_created["legal_name"] == carrier_created["_expected_legal_name"]


def test_dispatch_can_patch_carrier(tokens, carrier_created):
    r = requests.patch(
        f"{API}/api/admin/transportation/carriers/{carrier_created['id']}",
        headers=_dispatch(tokens["dispatch"]),
        json={"contact_name": "Track 19 Pytest Contact", "status": "active"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["contact_name"] == "Track 19 Pytest Contact"
    assert body["status"] == "active"


# ─────────────────────── 5 · admin governance preserved ───────────────────────

def test_anonymous_blocked_on_link_from_hr():
    r = requests.post(
        f"{API}/api/admin/transportation/persons/link-from-hr",
        headers={"Content-Type": "application/json"},
        json={"employee_id": "anything"},
        timeout=15,
    )
    assert r.status_code in (401, 403), r.text


def test_anonymous_blocked_on_carrier_create():
    r = requests.post(
        f"{API}/api/admin/transportation/carriers",
        headers={"Content-Type": "application/json"},
        json={"legal_name": "anon attempt", "carrier_type": "leased_hauler"},
        timeout=15,
    )
    assert r.status_code in (401, 403), r.text


# ─────────────────────── 6 · CDL classification source code ───────────────────────

def test_link_from_hr_enforces_cdl_holder_in_source():
    src = ROUTES_FILE.read_text()
    assert 'if not bool(emp.get("cdl_holder")):' in src, (
        "link-from-hr must explicitly require cdl_holder=true in the "
        "HR employee document. Non-CDL approved drivers must not enter "
        "the Transportation haul-driver list."
    )
    assert "approved_company_driver" not in src.split("link_person_from_hr")[1][:2000].replace("# ", " "), (
        "link-from-hr must not silently accept approved_company_driver=true "
        "as a substitute for cdl_holder."
    )


def test_classification_doc_distinguishes_cdl_vs_non_cdl():
    body = (MEMORY / "TRANSPORTATION_DRIVER_CLASSIFICATION_STANDARD.md").read_text().lower()
    assert "cdl_holder" in body
    assert "approved_company_driver" in body
    assert "non-cdl" in body or "non cdl" in body


# ─────────────────────── 7 · Backfill script ───────────────────────

def test_backfill_script_exists_and_default_dry_run():
    assert SCRIPT_FILE.exists()
    src = SCRIPT_FILE.read_text()
    assert "--commit" in src
    assert "--dry-run" in src or "DRY-RUN" in src
    assert "default mode is DRY-RUN" in src.lower() or "default: dry-run" in src.lower()


def test_backfill_script_not_wired_to_boot():
    # If anyone wires the script into server boot, this assertion will
    # catch it. The script must be operator-run only.
    server = Path("/app/backend/server.py").read_text()
    assert "track_19_00_link_hr_cdl_to_transport" not in server, (
        "Backfill script must NOT be imported / scheduled from server.py."
    )


# ─────────────────────── 8 · Frontend modal wiring (source-level) ───────────────────────

def test_frontend_modals_file_exists():
    p = Path("/app/frontend/src/pages/transportation/_modals.jsx")
    assert p.exists(), "Track 19.00 modal file missing"
    s = p.read_text()
    for testid in (
        "link-hr-driver-modal",
        "add-leased-driver-modal",
        "add-carrier-modal",
        "edit-carrier-modal",
    ):
        assert f'testid="{testid}"' in s, f"missing testid in modals: {testid}"


def test_drivers_and_carriers_lists_render_track_19_ctas():
    s = Path("/app/frontend/src/pages/transportation/_lists.jsx").read_text()
    assert 'data-testid="drivers-list-link-hr"' in s
    assert 'data-testid="drivers-list-add-leased"' in s
    assert 'data-testid="carriers-list-add"' in s
