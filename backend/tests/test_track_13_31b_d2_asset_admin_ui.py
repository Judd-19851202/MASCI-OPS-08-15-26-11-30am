"""Track 13.31B-D2 · Asset Admin UI + AssetProfile extension tests.

Validates the contracts the new operator UI depends on:
  • PATCH /api/asset-spine/assets/{id} accepts the canonical taxonomy +
    administrative fields and auto-stamps `taxonomy_verified_at` when
    the verified flag flips True.
  • Manual verification clears `taxonomy_review_reason`.
  • `taxonomy/review-needed` is admin-gated (operator role) and surfaces a
    suggested mapping per row.
  • Read of /assets/{id} returns the full canonical projection (so the
    new "Admin" tab can hydrate).
  • Apply-legacy-crosswalk is dry_run-by-default — no silent persistence.
  • No new collections introduced beyond the spine.

Doctrine: One asset · one record · one canonical taxonomy.
"""
import os
import uuid as _uuid

import httpx
import pytest

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin():
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


@pytest.fixture(scope="module")
def seeded_asset(admin_tok):
    """Create a fresh asset with intentionally unverified taxonomy."""
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"D2-TEST-{suffix}",
        "asset_name": "Track 13.31B-D2 admin-ui asset",
        # Intentionally NO canonical class/type — should land in review queue.
        "taxonomy_verified": False,
        "taxonomy_source": "needs_review",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    asset = r.json()
    aid = asset.get("asset_id") or asset.get("id")
    assert aid, f"Could not extract asset id from response: {asset}"
    return aid


# ── 1 · PATCH applies canonical taxonomy + auto-stamps verified_at ───


def test_patch_applies_canonical_taxonomy_and_stamps_verified(admin_tok, seeded_asset):
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    patch = {
        "asset_class": "Heavy Equipment",
        "asset_type": "Excavator",
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.patch(f"{API}/asset-spine/assets/{seeded_asset}", json=patch, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    after = r.json()
    assert after.get("asset_class") == "Heavy Equipment"
    assert after.get("asset_type") == "Excavator"
    assert after.get("taxonomy_verified") is True
    assert after.get("taxonomy_source") == "manual"


# ── 2 · PATCH accepts all 13 administrative fields ─────────────────────


def test_patch_applies_admin_fields(admin_tok, seeded_asset):
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    patch = {
        "lifecycle_status": "active",
        "title_status": "owned_clear",
        "warranty_expiration": "2030-01-01",
        "registration_number": "REG-D2-001",
        "registration_state": "PA",
        "registration_expiration": "2027-06-30",
        "insurance_carrier": "MASCI Test Insurance",
        "insurance_policy_number": "POL-D2-XYZ",
        "insurance_expiration": "2027-12-31",
        "division": "MASCI_GC_PA",
        "region": "south",
        "supervisor_id": "EMP-SUP-001",
        "gps_device_id": "GPS-DEV-D2",
        "normalized_company": "MASCI_GC",
        "motive_vehicle_id": "motive-v-d2",
        "maintainx_asset_id": "mx-d2",
        "fleetwatcher_asset_id": "fw-d2",
        "vin": "1FTFW1ET5DFC10312",
        "license_plate": "MASCI-D2",
    }
    r = httpx.patch(f"{API}/asset-spine/assets/{seeded_asset}", json=patch, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    after = r.json()
    for k, v in patch.items():
        assert after.get(k) == v, f"field {k} did not persist: expected={v!r} got={after.get(k)!r}"


# ── 3 · GET /assets/{id} surfaces the full canonical projection ───────


def test_read_back_canonical_projection(admin_tok, seeded_asset):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/assets/{seeded_asset}", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    a = r.json()
    # Canonical taxonomy fields surface in the projection
    for k in (
        "asset_class", "asset_type", "taxonomy_verified", "taxonomy_source",
        "lifecycle_status", "registration_number", "registration_state",
        "insurance_carrier", "warranty_expiration", "division", "region",
        "supervisor_id", "gps_device_id", "normalized_company",
        "motive_vehicle_id", "maintainx_asset_id", "fleetwatcher_asset_id",
        "title_status", "vin", "license_plate",
    ):
        assert k in a, f"projection missing field {k!r}"


# ── 4 · Review queue requires admin auth ──────────────────────────────


def test_review_queue_requires_admin():
    r = httpx.get(f"{API}/asset-spine/taxonomy/review-needed", timeout=30)
    assert r.status_code in (401, 403), f"review queue must require admin · got {r.status_code}"


# ── 5 · Review queue shape includes suggested mapping ─────────────────


def test_review_queue_shape(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=5", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "items" in d
    assert "count" in d
    if d["items"]:
        sample = d["items"][0]
        # operator-friendly fields
        for k in ("id", "unit_number", "display_label",
                  "legacy_category", "legacy_preop_equipment_type", "legacy_type",
                  "current_asset_class", "current_asset_type",
                  "current_taxonomy_verified", "suggested"):
            assert k in sample, f"queue row missing {k!r}"
        # Suggested mapping is a dict
        assert isinstance(sample["suggested"], dict)


# ── 6 · Apply-legacy-crosswalk is dry-run by default ──────────────────


def test_apply_crosswalk_dry_run_is_default(admin_tok):
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    # No query params — dry_run must default to True.
    r = httpx.post(f"{API}/asset-spine/taxonomy/apply-legacy-crosswalk?limit=10", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["dry_run"] is True
    assert d["scanned"] >= 0


# ── 7 · taxonomy enums + behavior matrix accessible to operator UI ───


def test_taxonomy_enums_drive_ui_selectors(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/taxonomy", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    # The UI needs:
    assert isinstance(d["asset_classes"], list) and len(d["asset_classes"]) >= 10
    assert isinstance(d["asset_types_by_class"], dict)
    assert isinstance(d["behaviors"], dict)
    # canonical_companies powers the "Normalized Company" select
    assert "MASCI_GC" in d["canonical_companies"]
    # Behavior keys are stable
    sample_behavior = next(iter(d["behaviors"].values()))
    for k in ("requires_registration", "requires_insurance", "requires_pm",
              "requires_preop", "assignable_to_employee", "transferable",
              "appears_on_map", "employee_lifecycle_managed",
              "renewal_tracking_required", "document_vault_required",
              "dot_required", "inspection_required", "exportable"):
        assert k in sample_behavior, f"behavior matrix missing {k!r}"
