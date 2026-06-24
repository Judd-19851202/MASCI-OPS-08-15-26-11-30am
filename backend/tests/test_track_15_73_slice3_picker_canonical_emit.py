"""TRACK 15.73 SLICE 4 · Picker Canonical-Emit · CI Guardrail.

Static analysis that prevents canonical-identity picker components from
silently regressing back to emitting `display_label` / `name` as the
primary key.

This is a structural test (no Playwright dependency, runnable in any CI
environment). It greps the frontend source tree for the regression
patterns and asserts that the curated allow-list of pickers either uses
canonical identifiers or explicitly accepts display values in
component-internal helpers only.

Specifically:

* ``EquipmentCombo.pick()`` MUST prefer `it.unit_number` first.
* ``NewEquipmentInspection.onPick`` MUST store `it.unit_number` in
  `equipment_unit` AND capture `equipment_master_id: it.id`.
* ``AttendeeBulkAddDialog`` MUST emit `attendee_type` + `source` +
  identity flags + a tenant-canonical company.
* ``PoRequests.onPick`` MUST capture `vendor_id` alongside the display
  name.
"""
from __future__ import annotations

import re
from pathlib import Path


FE = Path("/app/frontend/src")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def test_equipment_combo_pick_prefers_unit_number():
    src = _read(FE / "components" / "EquipmentCombo.jsx")
    # Picker must order: it.unit_number FIRST in the fallback chain.
    assert re.search(
        r'const\s+label\s*=\s*it\.unit_number\s*\|\|', src
    ), "EquipmentCombo.pick() must emit it.unit_number as the canonical key first."


def test_new_equipment_inspection_stores_canonical_unit_and_fk():
    src = _read(FE / "pages" / "NewEquipmentInspection.jsx")
    assert "it.unit_number || it.display_label" in src, (
        "NewEquipmentInspection.onPick must emit it.unit_number first."
    )
    assert "equipment_master_id: it.id" in src, (
        "NewEquipmentInspection.onPick must capture equipment_master_id FK."
    )


def test_attendee_bulk_add_uses_tenant_canonical_default():
    src = _read(FE / "components" / "AttendeeBulkAddDialog.jsx")
    assert 'brandCompanyName("MASCI")' in src, (
        "AttendeeBulkAddDialog bulk-add must default to MASCI (tenant canonical), "
        "never the generic 'Customer' fallback."
    )
    assert 'attendee_type: "employee"' in src, (
        "AttendeeBulkAddDialog must emit attendee_type='employee' for roster picks."
    )
    assert 'source: "employee_master"' in src, (
        "AttendeeBulkAddDialog must emit source='employee_master' for roster picks."
    )


def test_po_requests_picker_captures_vendor_id():
    src = _read(FE / "pages" / "PoRequests.jsx")
    assert "vendor_id: sup?.id" in src, (
        "PoRequests onPick must capture vendor_id alongside the display name."
    )


def test_equipment_master_panel_defaults_to_masci():
    src = _read(FE / "components" / "EquipmentMasterPanel.jsx")
    assert 'brandCompanyName("MASCI")' in src, (
        "EquipmentMasterPanel must default company to MASCI, not 'Customer'."
    )
    assert 'brandCompanyName("Customer")' not in src, (
        "EquipmentMasterPanel must NOT use the unsafe Customer fallback."
    )
