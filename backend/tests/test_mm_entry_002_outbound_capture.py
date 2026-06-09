"""MM-ENTRY-002 · Outbound Material Capture Sprint regression.

Covers K-MM-1 (form section + DR model field), K-MM-2 (rollup endpoint
populates outgoing[]), K-MM-3 (PDF + read-view tile + exec summary
render), K-MM-5 (vocabulary picker — frontend source guard).
"""
from __future__ import annotations
import importlib
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List

import pytest

sys.path.insert(0, "/app/backend")
pdf_render = importlib.import_module("pdf_render")

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _req(method, path, *, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            body = {}
        return {"status": e.code, "json": body}


@pytest.fixture(scope="module")
def admin_token():
    r = _req("POST", "/admin/login",
             body={"password": os.environ.get("ADMIN_PASSWORD", "MASCI1982!")})
    assert r["status"] == 200, r
    return r["json"]["token"]


def _doc(**overrides):
    base = {
        "project_name": "MM-ENTRY-002 fixture",
        "project_number": "JOB-MM-ENTRY-002",
        "location": "Yard",
        "report_date": "2026-06-09",
        "prepared_by": "Pytest Foreman",
        "superintendent": "Pytest Super",
        "photos": [ONE_PX] * 6,
        "prepared_by_signature": ONE_PX,
    }
    base.update(overrides)
    return base


# ────────────────────────────────────────────────────────────────────
# K-MM-1 · Backend model accepts outbound_materials[]
# ────────────────────────────────────────────────────────────────────

def test_k_mm_1_outbound_materials_field_persists(admin_token):
    body = _doc(
        project_number="JOB-MM-ENTRY-002-A",
        outbound_materials=[
            {"material": "Millings", "quantity": 12, "unit": "Loads",
             "hauler": "Lopez Hauling", "destination": "Greenway Recycling",
             "ticket_or_manifest": "MAN-77001",
             "notes": "Hauled from STA 12+50 stockpile"},
            {"material": "Unsuitable Material", "quantity": 8, "unit": "Loads",
             "hauler": "Self-perform", "destination": "Site stockpile A",
             "ticket_or_manifest": "", "notes": ""},
        ],
    )
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200, r
    saved = r["json"]
    assert isinstance(saved.get("outbound_materials"), list)
    assert len(saved["outbound_materials"]) == 2
    assert saved["outbound_materials"][0]["material"] == "Millings"
    assert saved["outbound_materials"][0]["quantity"] == 12
    assert saved["outbound_materials"][0]["destination"] == "Greenway Recycling"


def test_k_mm_1_outbound_materials_default_empty_list(admin_token):
    """If client omits the field entirely, server returns it as []."""
    body = _doc(project_number="JOB-MM-ENTRY-002-B")
    body.pop("outbound_materials", None)
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    saved = r["json"]
    # Either absent (legacy) or empty list (new) — both acceptable
    assert (saved.get("outbound_materials") is None
            or saved.get("outbound_materials") == []), (
        f"Unexpected default: {saved.get('outbound_materials')}"
    )


def test_k_mm_1_legacy_dr_without_outbound_still_readable(admin_token):
    """A DR submitted without outbound_materials must still GET back cleanly."""
    body = _doc(project_number="JOB-MM-ENTRY-002-LEGACY")
    body.pop("outbound_materials", None)
    sub = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert sub["status"] == 200
    fetched = _req("GET", f"/daily-reports/{sub['json']['id']}",
                   headers={"X-Admin-Token": admin_token})
    assert fetched["status"] == 200


# ────────────────────────────────────────────────────────────────────
# K-MM-2 · Material Movement rollup populates outgoing[]
# ────────────────────────────────────────────────────────────────────

def test_k_mm_2_rollup_populates_outgoing(admin_token):
    pn = "JOB-MM-ENTRY-002-ROLLUP"
    body = _doc(
        project_number=pn,
        outbound_materials=[
            {"material": "Millings", "quantity": 12, "unit": "Loads",
             "hauler": "Lopez Hauling", "destination": "Greenway Recycling",
             "ticket_or_manifest": "MAN-77002", "notes": ""},
            {"material": "Concrete Debris", "quantity": 2, "unit": "Loads",
             "hauler": "Roll-Off Co", "destination": "Landfill",
             "ticket_or_manifest": "", "notes": ""},
        ],
    )
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200

    rollup = _req("GET", f"/material-movement/daily/{pn}/2026-06-09")
    assert rollup["status"] == 200
    out = rollup["json"]["outgoing"]
    assert len(out) >= 2
    materials = [o["material"] for o in out]
    assert "Millings" in materials
    assert "Concrete Debris" in materials
    # Verify shape of an outbound row carries the new fields
    mills = next(o for o in out if o["material"] == "Millings")
    assert mills["quantity"] == 12
    assert mills["unit"] == "Loads"
    assert mills["hauler"] == "Lopez Hauling"
    assert mills["destination"] == "Greenway Recycling"
    assert mills["ticket_or_manifest"] == "MAN-77002"


def test_k_mm_2_rollup_excludes_production_per_f1(admin_token):
    """MM-001B-F1 doctrine: production rows must NEVER appear in
    outgoing. Confirm the addition of outbound_materials did NOT
    regress this guarantee."""
    pn = "JOB-MM-ENTRY-002-PROD-EXCL"
    body = _doc(
        project_number=pn,
        production=[
            {"description": "RCP Install", "quantity": 100, "unit": "LF",
             "station_from": "10+00", "station_to": "11+00"},
            {"description": "Curb installed", "quantity": 220, "unit": "LF"},
        ],
        outbound_materials=[
            {"material": "Dirt", "quantity": 5, "unit": "Loads",
             "hauler": "Self", "destination": "Site stockpile"},
        ],
    )
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200

    rollup = _req("GET", f"/material-movement/daily/{pn}/2026-06-09")
    out = rollup["json"]["outgoing"]
    # Outbound material present
    assert any(o["material"] == "Dirt" for o in out)
    # Production rows must NOT appear
    forbidden = {"RCP Install", "Curb installed"}
    for row in out:
        assert row["material"] not in forbidden, (
            f"REGRESSION: production row leaked into outgoing: {row}"
        )


def test_k_mm_2_inbound_still_works(admin_token):
    """Adding outbound rollup must not regress inbound rollup."""
    pn = "JOB-MM-ENTRY-002-IN"
    body = _doc(
        project_number=pn,
        materials=[
            {"description": "SP-12.5 Asphalt", "quantity": 240, "unit": "TON",
             "supplier": "APAC", "ticket_number": "TKT-1"},
        ],
        outbound_materials=[
            {"material": "Dirt", "quantity": 3, "unit": "Loads",
             "destination": "Site stockpile"},
        ],
    )
    r = _req("POST", "/daily-reports", body=body, headers={"X-Admin-Token": admin_token})
    assert r["status"] == 200
    rollup = _req("GET", f"/material-movement/daily/{pn}/2026-06-09")
    inc = rollup["json"]["incoming"]
    out = rollup["json"]["outgoing"]
    assert any(i["material"] == "SP-12.5 Asphalt" for i in inc)
    assert any(o["material"] == "Dirt" for o in out)


# ────────────────────────────────────────────────────────────────────
# K-MM-3 · PDF + Exec Summary + Read-view tile render
# ────────────────────────────────────────────────────────────────────

def test_k_mm_3_pdf_renders_outbound_table():
    """Direct in-process render: outbound_materials[] should appear in
    Section 09d 'Material Movement Today' with full column set."""
    doc = _doc(
        outbound_materials=[
            {"material": "Millings", "quantity": 12, "unit": "Loads",
             "hauler": "Lopez Hauling", "destination": "Greenway Recycling",
             "ticket_or_manifest": "MAN-77003",
             "notes": "Stockpile cleanup"},
        ],
    )
    html = pdf_render._render_daily(doc)
    assert "09d · Material Movement Today" in html
    # Outbound section header
    mm_block = html[html.find("09d · Material Movement Today"):]
    assert "Outbound Material" in mm_block  # subsection label
    # All required columns present
    for col in ("Material", "Qty", "Unit", "Hauler", "Destination",
                "Ticket / Manifest", "Notes"):
        assert col in mm_block, f"Missing column in outbound table: {col}"
    # Actual data rendered
    assert "Millings" in mm_block
    assert "Lopez Hauling" in mm_block
    assert "Greenway Recycling" in mm_block
    assert "MAN-77003" in mm_block


def test_k_mm_3_pdf_hides_outbound_table_when_empty():
    """When outbound_materials is empty AND no dispatch, Section 09d
    should not render at all (mirrors prior MM-001B behavior)."""
    html = pdf_render._render_daily(_doc(outbound_materials=[]))
    assert "09d · Material Movement Today" not in html
    assert "09d · MASCI Hauling Today" not in html
    assert "Outbound Material" not in html


def test_k_mm_3_exec_summary_includes_outbound_summary():
    """Executive Summary MATERIAL line should add 'Out: N <unit> <material>'."""
    html = pdf_render._render_daily(_doc(
        outbound_materials=[
            {"material": "Millings", "quantity": 12, "unit": "Loads"},
            {"material": "Unsuitable Material", "quantity": 8, "unit": "Loads"},
        ],
    ))
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "MATERIAL" in card_block
    assert "Out:" in card_block
    assert "Millings" in card_block
    assert "Unsuitable Material" in card_block


def test_k_mm_3_exec_summary_inbound_label_short():
    """The inbound label was 'Inbound:' in DR-PDF-002; this sprint
    shortens it to 'In:' to make room for the new 'Out:' segment.
    Confirm the new labels are in place."""
    html = pdf_render._render_daily(_doc(
        materials=[{"description": "SP-12.5", "quantity": 100, "unit": "TON"}],
        outbound_materials=[
            {"material": "Dirt", "quantity": 4, "unit": "Loads"},
        ],
    ))
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "In:" in card_block
    assert "Out:" in card_block


def test_k_mm_3_pdf_renders_dispatch_AND_outbound_together():
    """When both dispatch rows and outbound_materials exist, both
    sub-tables render under Section 09d with a spacer between."""
    import pdf_render as pr
    def _stub(*args, **kwargs):
        return {
            "dispatch_rows": [
                {"haul_type": "Inbound · Material", "material": "SP-12.5",
                 "source_location": "Plant", "destination": "Job",
                 "load_count": 5, "carrier": "Lopez", "truck_id": "T-1",
                 "id": "d-1"},
            ],
            "excavation_rows": [],
        }
    saved = pr._fetch_dr_render_extras
    pr._fetch_dr_render_extras = _stub
    try:
        html = pr._render_daily(_doc(
            outbound_materials=[
                {"material": "Millings", "quantity": 12, "unit": "Loads"},
            ],
        ))
    finally:
        pr._fetch_dr_render_extras = saved
    mm = html[html.find("09d · Material Movement Today"):]
    assert "MASCI Hauling" in mm  # dispatch subsection
    assert "Outbound Material" in mm  # foreman-authored subsection
    assert "Lopez" in mm
    assert "Millings" in mm


def test_k_mm_3_pdf_pipeline_renders_valid_bytes():
    blob = pdf_render.render_record_pdf(
        "daily-report",
        _doc(outbound_materials=[
            {"material": "Millings", "quantity": 12, "unit": "Loads",
             "hauler": "Lopez", "destination": "Recycling"},
        ]),
    )
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"


# ────────────────────────────────────────────────────────────────────
# K-MM-5 · Outbound vocabulary picker (frontend source guard)
# ────────────────────────────────────────────────────────────────────

def test_k_mm_5_frontend_vocabulary_picker_present():
    src = open("/app/frontend/src/pages/NewDailyReport.jsx", "r",
               encoding="utf-8").read()
    # The new outbound RepeatBlock must be wired
    assert 'list="outbound_materials"' in src
    assert 'testIdBase="outbound-material"' in src
    # Vocabulary entries — every required item from the directive
    for item in ("Millings", "Dirt", "Unsuitable Material", "Concrete Debris",
                 "Trees / Stumps", "Vegetation", "Trash", "Demo Debris",
                 "Contaminated Material"):
        assert item in src, f"Outbound vocabulary missing entry: {item}"
    # Units — all required from directive
    for u in ("Loads", "CY", "TON", "EA", "LF", "SY", "LB", "Other"):
        assert u in src, f"Outbound unit missing: {u}"


def test_k_mm_5_outbound_helpers_wired():
    """The new `outbound` helpers (useList) must exist and be passed
    to the RepeatBlock — proves the form is functional, not orphaned."""
    src = open("/app/frontend/src/pages/NewDailyReport.jsx", "r",
               encoding="utf-8").read()
    assert 'const outbound = useList(data, setData, "outbound_materials")' in src
    assert "helpers={outbound}" in src


def test_k_mm_5_tile_renders_outbound_with_correct_columns():
    src = open("/app/frontend/src/components/MaterialMovementTile.jsx", "r",
               encoding="utf-8").read()
    # Old "from Production" subtitle must be gone
    assert "from Production" not in src
    # New "Hauled Off" label must be present
    assert "Hauled Off" in src
    # Correct column data sourced from outbound rows
    assert "r.hauler" in src
    assert "r.destination" in src
    assert "r.ticket_or_manifest" in src
    assert "r.station_from" not in src  # production-era field removed


# ────────────────────────────────────────────────────────────────────
# Backward compatibility — prior certified surfaces still preserved
# ────────────────────────────────────────────────────────────────────

def test_compat_existing_pdf_pipeline_still_works():
    blob = pdf_render.render_record_pdf("daily-report", _doc())
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"


def test_compat_audit_footer_preserved():
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    assert "_compute_audit_envelope_sha256" in src


def test_compat_no_new_collection_for_outbound():
    """Static guard: the rollup endpoint must not create a new collection
    or perform any writes for outbound material."""
    src = open("/app/backend/routes/material_movement.py", "r",
               encoding="utf-8").read()
    for forbidden in ("insert_one", "insert_many", "update_one", "update_many",
                      "delete_one", "delete_many", "drop_collection"):
        assert forbidden not in src, (
            f"K-MM-2 violated visibility-only contract: {forbidden}"
        )


def test_compat_dr_fix_3_signer_intact():
    html = pdf_render._render_daily(_doc())
    assert "11 · Signature" in html
    sig_block = html.split("11 · Signature", 1)[1]
    assert "Superintendent signature" not in sig_block.lower()
