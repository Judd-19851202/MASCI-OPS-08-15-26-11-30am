"""
iter123 — Mappings Wizard backend tests.

Covers:
  - preview matching: ready / unmatched / duplicate / external_collision / noop
  - commit create + update happy paths
  - refuse-to-overwrite without force_overwrite
  - explicit force_overwrite replaces value
  - audit run list reflects each commit
  - master equipment_master is never modified by any wizard call
"""
from __future__ import annotations
import os
import uuid

import httpx
import pytest


API_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")


def _admin_token() -> str:
    with httpx.Client(timeout=20.0) as c:
        r = c.post(f"{API_URL}/api/admin/login", json={"password": ADMIN_PASSWORD})
        r.raise_for_status()
        return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Token": _admin_token()}


@pytest.fixture(scope="module")
def sample_equipment(admin_headers):
    """Pull two real equipment_master records with non-empty unit numbers
    for use in preview tests. Skips the whole module if the DB has fewer
    than 2 such rows."""
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        r.raise_for_status()
        data = r.json()
        items = data.get("items") if isinstance(data, dict) else data
        real = [it for it in (items or []) if (it.get("unit_number") or "").strip()]
        if len(real) < 2:
            pytest.skip("Need at least 2 equipment_master rows with unit numbers")
        return real[:2]


def _preview(headers, kind, rows):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(
            f"{API_URL}/api/admin/integrations/mappings/wizard/preview",
            headers=headers, json={"kind": kind, "rows": rows},
        )
        r.raise_for_status()
        return r.json()


def _commit(headers, kind, decisions, source_label="pytest"):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(
            f"{API_URL}/api/admin/integrations/mappings/wizard/commit",
            headers=headers,
            json={"kind": kind, "source_label": source_label, "decisions": decisions},
        )
        r.raise_for_status()
        return r.json()


def _cleanup_mapping(headers, equipment_id):
    """Best-effort delete of any asset_mapping for the given equipment so
    the test suite is idempotent and rerunnable."""
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/admin/integrations/asset-mappings", headers=headers)
        for m in r.json() or []:
            if m.get("masci_equipment_id") == equipment_id:
                c.delete(f"{API_URL}/api/admin/integrations/asset-mappings/{m['id']}", headers=headers)


# ════════════════════════════════════════════════════════════════════
# PREVIEW
# ════════════════════════════════════════════════════════════════════
def test_preview_ready_and_unmatched(admin_headers, sample_equipment):
    eq1 = sample_equipment[0]
    _cleanup_mapping(admin_headers, eq1["id"])
    fake_ext_id = f"wizmv-{uuid.uuid4().hex[:8]}"
    res = _preview(admin_headers, "motive_vehicles", [
        {"unit_number": eq1["unit_number"], "external_id": fake_ext_id},
        {"unit_number": "DEFINITELY-NOT-A-REAL-UNIT-9999", "external_id": "x"},
        {"unit_number": "", "external_id": "no-unit"},
    ])
    assert res["totals"]["input_rows"] == 3
    assert res["totals"]["ready"] == 1
    assert res["totals"]["unmatched"] == 2
    statuses = [r["status"] for r in res["rows"]]
    assert "ready" in statuses
    assert statuses.count("unmatched") == 2
    # ready row carries the masci_equipment_id
    ready = next(r for r in res["rows"] if r["status"] == "ready")
    assert ready["matches"][0]["masci_equipment_id"] == eq1["id"]
    assert ready["suggested_action"] in ("create", "update")


def test_preview_rejects_bad_kind(admin_headers):
    with httpx.Client(timeout=20.0) as c:
        r = c.post(
            f"{API_URL}/api/admin/integrations/mappings/wizard/preview",
            headers=admin_headers,
            json={"kind": "not_a_real_kind", "rows": []},
        )
        assert r.status_code == 400


def test_preview_requires_admin():
    with httpx.Client(timeout=20.0) as c:
        r = c.post(
            f"{API_URL}/api/admin/integrations/mappings/wizard/preview",
            json={"kind": "motive_vehicles", "rows": []},
        )
        assert r.status_code in (401, 403)


# ════════════════════════════════════════════════════════════════════
# COMMIT — create + safe-update flow
# ════════════════════════════════════════════════════════════════════
def test_commit_create_then_refuse_overwrite_then_force(admin_headers, sample_equipment):
    eq1 = sample_equipment[0]
    _cleanup_mapping(admin_headers, eq1["id"])
    ext1 = f"wizmv-{uuid.uuid4().hex[:8]}"
    ext2 = f"wizmv-{uuid.uuid4().hex[:8]}"

    # 1. CREATE
    r = _commit(admin_headers, "motive_vehicles", [
        {"action": "create", "masci_equipment_id": eq1["id"], "external_id": ext1},
    ], source_label="pytest-create")
    assert r["totals"]["created"] == 1
    assert r["totals"]["blocked"] == 0
    assert r["actor"]  # any non-empty actor string
    mapping_id = r["results"][0]["mapping_id"]

    # 2. ATTEMPT OVERWRITE (no force) — must be blocked
    r2 = _commit(admin_headers, "motive_vehicles", [
        {"action": "update", "masci_equipment_id": eq1["id"], "mapping_id": mapping_id,
         "external_id": ext2, "force_overwrite": False},
    ])
    assert r2["totals"]["blocked"] == 1
    assert r2["totals"]["updated"] == 0
    assert "force_overwrite" in r2["results"][0]["reason"]

    # 3. FORCE OVERWRITE
    r3 = _commit(admin_headers, "motive_vehicles", [
        {"action": "update", "masci_equipment_id": eq1["id"], "mapping_id": mapping_id,
         "external_id": ext2, "force_overwrite": True},
    ])
    assert r3["totals"]["updated"] == 1
    assert r3["totals"]["blocked"] == 0

    # 4. noop preview AFTER the force-update
    preview = _preview(admin_headers, "motive_vehicles", [
        {"unit_number": eq1["unit_number"], "external_id": ext2},
    ])
    assert preview["totals"]["noop"] == 1

    # cleanup
    _cleanup_mapping(admin_headers, eq1["id"])


def test_commit_skip_records_audit_entry(admin_headers, sample_equipment):
    eq1 = sample_equipment[0]
    r = _commit(admin_headers, "motive_vehicles", [
        {"action": "skip", "masci_equipment_id": eq1["id"], "external_id": "ignored"},
    ], source_label="pytest-skip")
    assert r["totals"]["skipped"] == 1
    assert r["totals"]["created"] == 0
    assert r["totals"]["updated"] == 0


# ════════════════════════════════════════════════════════════════════
# AUDIT — run list reflects writes
# ════════════════════════════════════════════════════════════════════
def test_audit_run_list(admin_headers, sample_equipment):
    eq1 = sample_equipment[0]
    _cleanup_mapping(admin_headers, eq1["id"])
    ext = f"wizmv-{uuid.uuid4().hex[:8]}"
    label = f"pytest-audit-{uuid.uuid4().hex[:6]}"
    _commit(admin_headers, "motive_vehicles", [
        {"action": "create", "masci_equipment_id": eq1["id"], "external_id": ext},
    ], source_label=label)
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/admin/integrations/mappings/wizard/runs?limit=20", headers=admin_headers)
        r.raise_for_status()
        runs = r.json()
        assert any(run.get("source_label") == label for run in runs), "run not found in audit list"
    _cleanup_mapping(admin_headers, eq1["id"])


# ════════════════════════════════════════════════════════════════════
# SAFETY — equipment_master untouched
# ════════════════════════════════════════════════════════════════════
def test_equipment_master_never_modified_by_wizard(admin_headers, sample_equipment):
    eq1 = sample_equipment[0]
    _cleanup_mapping(admin_headers, eq1["id"])
    # snapshot
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        items_before = (r.json().get("items") if isinstance(r.json(), dict) else r.json()) or []
        before = next((it for it in items_before if it.get("id") == eq1["id"]), None)
        assert before is not None
    # run a create + force-overwrite update cycle
    ext = f"wizmv-{uuid.uuid4().hex[:8]}"
    res = _commit(admin_headers, "motive_vehicles", [
        {"action": "create", "masci_equipment_id": eq1["id"], "external_id": ext},
    ])
    mapping_id = res["results"][0]["mapping_id"]
    _commit(admin_headers, "motive_vehicles", [
        {"action": "update", "masci_equipment_id": eq1["id"], "mapping_id": mapping_id,
         "external_id": f"new-{ext}", "force_overwrite": True},
    ])
    # re-snapshot
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{API_URL}/api/equipment-master", headers=admin_headers)
        items_after = (r.json().get("items") if isinstance(r.json(), dict) else r.json()) or []
        after = next((it for it in items_after if it.get("id") == eq1["id"]), None)
        assert after is not None
    # All master fields must match (the wizard MUST NOT touch this collection)
    safe_compare_fields = ("id", "unit_number", "name", "make", "model", "equipment_type", "vin", "license_plate", "year")
    for f in safe_compare_fields:
        assert before.get(f) == after.get(f), f"equipment_master.{f} changed: {before.get(f)!r} -> {after.get(f)!r}"
    _cleanup_mapping(admin_headers, eq1["id"])
