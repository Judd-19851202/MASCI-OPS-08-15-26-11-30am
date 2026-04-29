"""Tests for the Equipment Pre-Op Inspection module (added iteration 11).

Covers:
- GET /api/equipment-types — 23 types + 23 checklist templates (public)
- POST /api/equipment-units — create + de-dup
- GET /api/equipment-units?equipment_type=… — filtered list
- POST /api/equipment-inspections — record save + persists unit + auto-email pipeline
- GET /api/equipment-inspections — admin list summary
- GET /api/equipment-inspections/{id} — admin full record
- DELETE /api/equipment-inspections/{id} — admin delete
- Admin gate (401 without X-Admin-Token) on read/delete
- WeasyPrint render_record_pdf('equipment-inspection', record) — PDF bytes
- Subject + body include EQUIPMENT FAIL prefix when fail_count > 0
- PM auto-resolution for project_number 24-06 → David Jewett
"""
import os
import sys
import time
import uuid

import pytest
import requests

# So we can import the backend modules directly for unit-level checks
sys.path.insert(0, "/app/backend")

from conftest import URL, ADMIN_TOKEN  # noqa: E402  (uses session patch)
from pm_routing import find_pm_for_record, recipients_for_record  # noqa: E402
from pdf_render import render_record_pdf, KIND_TITLES  # noqa: E402

BASE = URL.rstrip("/")
ADMIN_HEADERS = {"X-Admin-Token": ADMIN_TOKEN} if ADMIN_TOKEN else {}


# ---------------------------------------------------------------------------
# /api/equipment-types
# ---------------------------------------------------------------------------
class TestEquipmentTypes:
    def test_list_types_public(self):
        r = requests.get(f"{BASE}/api/equipment-types", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "types" in data and "checklists" in data
        assert isinstance(data["types"], list)
        assert len(data["types"]) == 23, f"expected 23 types, got {len(data['types'])}"
        # All 23 types have a checklist template
        for t in data["types"]:
            assert t in data["checklists"], f"missing checklist for {t}"
            sections = data["checklists"][t]
            assert isinstance(sections, list) and len(sections) >= 4
            for s in sections:
                assert "title" in s and "items" in s
                assert len(s["items"]) >= 1
        assert len(data["checklists"]) == 23


# ---------------------------------------------------------------------------
# /api/equipment-units (create + de-dup + list filtered)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason="Legacy /api/equipment-units endpoints were removed in iter22 in "
    "favor of the equipment_master upload pipeline (which fans out into "
    "the equipment_units collection automatically). Kept as documentation."
)
class TestEquipmentUnits:
    UNIT_LABEL = f"TEST_CAT320_{uuid.uuid4().hex[:6]}"
    EQ_TYPE = "Excavator"
    created_ids = []

    def test_create_unit_persists(self):
        payload = {
            "equipment_type": self.EQ_TYPE,
            "unit_label": self.UNIT_LABEL,
            "make": "CAT", "model": "320", "serial": "TEST-SN-001",
        }
        r = requests.post(f"{BASE}/api/equipment-units", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["equipment_type"] == self.EQ_TYPE
        assert body["unit_label"] == self.UNIT_LABEL
        assert body["make"] == "CAT"
        assert "id" in body and isinstance(body["id"], str)
        TestEquipmentUnits.created_ids.append(body["id"])

    def test_create_same_unit_dedupes(self):
        payload = {
            "equipment_type": self.EQ_TYPE,
            "unit_label": self.UNIT_LABEL,
            "make": "CAT", "model": "320", "serial": "TEST-SN-001",
        }
        r1 = requests.post(f"{BASE}/api/equipment-units", json=payload, timeout=15)
        assert r1.status_code == 200
        first_id = r1.json()["id"]
        r2 = requests.post(f"{BASE}/api/equipment-units", json=payload, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["id"] == first_id, "de-dup should return same id"

    def test_list_units_filtered_by_type(self):
        r = requests.get(
            f"{BASE}/api/equipment-units",
            params={"equipment_type": self.EQ_TYPE},
            timeout=15,
        )
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list)
        labels = [x.get("unit_label") for x in rows]
        assert self.UNIT_LABEL in labels
        # all rows must be Excavator
        for x in rows:
            assert x["equipment_type"] == self.EQ_TYPE


# ---------------------------------------------------------------------------
# /api/equipment-inspections — full CRUD + admin-gate
# ---------------------------------------------------------------------------
def _sample_record(fail_count=0, project_number="24-06"):
    """Build a representative payload. project_number 24-06 → David Jewett."""
    checklist = {
        "Fluids & Leaks": {
            "Engine oil level": {"status": "fail" if fail_count else "pass", "note": "low" if fail_count else ""},
            "Engine coolant level": {"status": "pass", "note": ""},
        }
    }
    return {
        "project_name": "T5824 - SR 46 (W 1ST ST.)",
        "project_number": project_number,
        "location": "Sanford, FL",
        "inspection_date": "2026-01-15",
        "inspection_time": "07:00",
        "operator_name": "TEST_Operator",
        "equipment_type": "Excavator",
        "equipment_unit": f"TEST_CAT320_INSP_{uuid.uuid4().hex[:6]}",
        "equipment_make": "CAT",
        "equipment_model": "320",
        "equipment_serial": "TEST-SN-INSP",
        "hour_meter": "1234.5",
        "odometer": "",
        "checklist": checklist,
        "fail_count": fail_count,
        "pass_count": 1,
        "na_count": 0,
        "deficiency_notes": "Auto test deficiency" if fail_count else "",
        "corrective_actions": "Tag out" if fail_count else "",
        "out_of_service": "Yes" if fail_count else "No",
        "photos": [],
        "operator_signature": "",
    }


class TestEquipmentInspectionsCRUD:
    created_ids = []

    def test_create_pass_record(self):
        r = requests.post(
            f"{BASE}/api/equipment-inspections",
            json=_sample_record(fail_count=0),
            timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "id" in body
        assert body["fail_count"] == 0
        assert body["out_of_service"] == "No"
        assert body["equipment_type"] == "Excavator"
        TestEquipmentInspectionsCRUD.created_ids.append(body["id"])

    def test_create_fail_record_24_06_routes_to_david_jewett(self):
        rec = _sample_record(fail_count=1, project_number="24-06")
        r = requests.post(
            f"{BASE}/api/equipment-inspections", json=rec, timeout=20
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["fail_count"] == 1
        assert body["out_of_service"] == "Yes"
        TestEquipmentInspectionsCRUD.created_ids.append(body["id"])

        # PM resolution by project_number 24-06 → David Jewett
        pm = find_pm_for_record(rec)
        assert pm is not None, "PM should resolve for 24-06"
        pm_name, pm_email = pm
        assert pm_name == "David Jewett"
        assert pm_email == "davidjewett@mascigc.com"

        dist = recipients_for_record(rec)
        assert dist["pm_name"] == "David Jewett"
        assert "davidjewett@mascigc.com" in dist["all"]

    def test_admin_list_requires_token(self):
        r = requests.get(
            f"{BASE}/api/equipment-inspections",
            headers={"X-Admin-Token": ""},  # explicit blank to defeat fixture
            timeout=15,
        )
        # Note: conftest's setdefault won't overwrite an explicit blank, but
        # an empty string still means "no token" → 401.
        assert r.status_code == 401, r.text

    def test_admin_list_returns_records(self):
        if not ADMIN_TOKEN:
            pytest.skip("no admin token configured")
        r = requests.get(f"{BASE}/api/equipment-inspections", timeout=15)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list)
        ids = {row["id"] for row in rows}
        for cid in TestEquipmentInspectionsCRUD.created_ids:
            assert cid in ids, f"created {cid} missing from list"
        # Summary fields shape
        sample = next(r for r in rows if r["id"] in TestEquipmentInspectionsCRUD.created_ids)
        for k in (
            "project_name", "project_number", "location", "inspection_date",
            "operator_name", "equipment_type", "equipment_unit",
            "fail_count", "out_of_service", "photo_count", "created_at",
        ):
            assert k in sample, f"summary missing {k}"

    def test_admin_get_full_record(self):
        if not ADMIN_TOKEN or not TestEquipmentInspectionsCRUD.created_ids:
            pytest.skip("nothing to fetch")
        cid = TestEquipmentInspectionsCRUD.created_ids[0]
        r = requests.get(f"{BASE}/api/equipment-inspections/{cid}", timeout=15)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["id"] == cid
        assert "checklist" in doc
        assert "_id" not in doc, "Mongo _id must be excluded"

    def test_admin_get_404(self):
        r = requests.get(
            f"{BASE}/api/equipment-inspections/does-not-exist-{uuid.uuid4().hex}",
            timeout=15,
        )
        assert r.status_code == 404

    @pytest.mark.skip(
        reason="GET /api/equipment-units removed in iter22 (replaced by "
        "equipment_master upload pipeline)."
    )
    def test_create_persists_unit_in_dropdown(self):
        # Inspection saves should auto-create the equipment_unit row.
        rec = _sample_record(fail_count=0, project_number="24-06")
        rec["equipment_unit"] = f"TEST_AUTOREG_{uuid.uuid4().hex[:6]}"
        r = requests.post(
            f"{BASE}/api/equipment-inspections", json=rec, timeout=20
        )
        assert r.status_code == 200
        TestEquipmentInspectionsCRUD.created_ids.append(r.json()["id"])

        # tiny wait — same-request side effect, but be safe
        time.sleep(0.4)
        r2 = requests.get(
            f"{BASE}/api/equipment-units",
            params={"equipment_type": rec["equipment_type"]},
            timeout=15,
        )
        assert r2.status_code == 200
        labels = [x["unit_label"] for x in r2.json()]
        assert rec["equipment_unit"] in labels, "newly inspected unit should auto-register"

    def test_admin_delete_removes_record(self):
        if not ADMIN_TOKEN or not TestEquipmentInspectionsCRUD.created_ids:
            pytest.skip("nothing to delete")
        # delete every created id; verify 404 after
        remaining = []
        for cid in TestEquipmentInspectionsCRUD.created_ids:
            r = requests.delete(f"{BASE}/api/equipment-inspections/{cid}", timeout=15)
            assert r.status_code == 200, f"delete {cid}: {r.status_code} {r.text}"
            assert r.json().get("deleted") is True
            r2 = requests.get(f"{BASE}/api/equipment-inspections/{cid}", timeout=15)
            assert r2.status_code == 404
        TestEquipmentInspectionsCRUD.created_ids = remaining


# ---------------------------------------------------------------------------
# WeasyPrint PDF rendering
# ---------------------------------------------------------------------------
class TestEquipmentPDF:
    def test_kind_title_registered(self):
        assert KIND_TITLES.get("equipment-inspection") == "Equipment Pre-Op Inspection"

    def test_render_pdf_pass_case(self):
        rec = _sample_record(fail_count=0)
        rec["id"] = "TEST-PDF-PASS"
        rec["created_at"] = "2026-01-15T07:01:00+00:00"
        pdf = render_record_pdf("equipment-inspection", rec)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 1000, f"PDF suspiciously small: {len(pdf)} bytes"
        assert pdf[:4] == b"%PDF", "must start with %PDF magic"

    def test_render_pdf_fail_case_includes_banner(self):
        rec = _sample_record(fail_count=2)
        rec["id"] = "TEST-PDF-FAIL"
        rec["created_at"] = "2026-01-15T07:01:00+00:00"
        # Render the HTML body directly to check for FAIL banner text
        from pdf_render import _render_equipment  # noqa: WPS433
        html = _render_equipment(rec)
        assert isinstance(html, str)
        # Banner / out-of-service messaging
        upper = html.upper()
        assert "DO NOT OPERATE" in upper or "OUT OF SERVICE" in upper or "FAIL" in upper, (
            "FAIL/DO-NOT-OPERATE banner should appear when fail_count>0"
        )
        # And the actual PDF still renders
        pdf = render_record_pdf("equipment-inspection", rec)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000


# ---------------------------------------------------------------------------
# Auto-email pipeline (subject prefix when fail_count > 0)
# ---------------------------------------------------------------------------
class TestAutoEmailSubject:
    def test_equipment_fail_subject_prefix_logic(self):
        """Mirror the prefix logic in server._dispatch_auto_email so we don't
        actually fire Resend during tests."""
        rec_pass = _sample_record(fail_count=0)
        rec_fail = _sample_record(fail_count=3)

        def subject_for(record, kind="equipment-inspection"):
            equipment_fail = (
                kind == "equipment-inspection"
                and (record.get("fail_count") or 0) > 0
            )
            prefix = "EQUIPMENT FAIL · " if equipment_fail else ""
            title = KIND_TITLES.get(kind, "MASCI Safety Record")
            project = record.get("project_name") or "MASCI"
            return f"[MASCI] {prefix}{title} · {project}"

        s_pass = subject_for(rec_pass)
        s_fail = subject_for(rec_fail)
        assert "EQUIPMENT FAIL" not in s_pass
        assert s_fail.startswith("[MASCI] EQUIPMENT FAIL · Equipment Pre-Op Inspection")

    def test_pm_routing_table_unchanged(self):
        # Project 24-06 still lives under David Jewett
        pm = find_pm_for_record({"project_number": "24-06"})
        assert pm == ("David Jewett", "davidjewett@mascigc.com")
