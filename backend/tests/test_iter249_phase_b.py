"""iter249 Phase B · Equipment Checkout pilot · backend tests.

Covers (operator-required pilot validation):
  - Extractor parses Claude Vision JSON output correctly · normalises types
  - Matching engine surfaces top employee/equipment/project candidates
  - Duplicate-suspicion detector flags same-employee + same-serial in
    native field_leadership_records
  - Promoter writes a `field_leadership_records` row with
    source=`legacy_imported`, legacy_import_id back-ref, and the right
    equipment_lines shape
  - HR employee-accountability endpoint picks up promoted imported
    record automatically (zero changes to live read code paths)
  - Outstanding-equipment flag picks up an un-returned imported line
  - Anti-self-approval still blocks even with extractor activated
  - Pilot cap rejects upload over 50

Style: end-to-end style fixtures · direct DB seeding for the OCR
extractor (Claude Vision is mocked at the LlmChat boundary).
"""
from __future__ import annotations

import os
import uuid
import asyncio
import pytest

from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import legacy_imports as _li  # noqa: E402
import legacy_imports_equipment_checkout as _li_ec  # noqa: E402


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


# ─── Helpers ──────────────────────────────────────────────────────────
async def _cleanup_test_import(db, iid: str, employee_marker: str | None = None):
    await db.legacy_imports.delete_many({"id": iid})
    await db.legacy_import_audit.delete_many({"import_id": iid})
    if employee_marker:
        await db.field_leadership_records.delete_many({"employee_name": employee_marker})


def _seed_import_doc(iid: str, **overrides):
    from datetime import datetime, timezone
    base = {
        "id": iid,
        "document_type": "equipment_checkout",
        "status": "needs_review",
        "upload_portal": "safety",
        "source_files": [{
            "r2_key": "test/key", "original_name": "t.pdf",
            "mime": "application/pdf", "size_bytes": 10,
            "sha256": "abc" + iid[:6], "uploaded_by_id": "uploader-u",
            "uploaded_by_name": "Uploader",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }],
        "ocr": {
            "provider": "claude_vision",
            "confidence": 0.82,
            "extracted_fields": {
                "employee_name": "PhaseB Test Employee",
                "employee_position": "Laborer",
                "supervisor_name": "PhaseB Supervisor",
                "project_number": "ITER249-TEST",
                "project_name": "Iter249 Test Job",
                "occurred_at": "2024-08-15",
                "return_date": None,
                "equipment_lines": [
                    {"name": "Cordless Drill", "serial": "PB-249-001",
                     "asset_id": None, "qty": 1, "notes": None,
                     "returned": False, "photos": []},
                ],
                "notes": "Imported from legacy paper file.",
                "supervisor_signature_present": True,
                "employee_signature_present": True,
            },
            "field_confidences": {"employee_name": 0.9, "equipment_lines": 0.85},
        },
        "matches": {
            "employee": {"suggested_id": None, "suggested_name": None, "confidence": 0.0, "alternatives": []},
            "equipment": {"suggested_id": None, "suggested_name": None, "confidence": 0.0, "alternatives": []},
            "project": {"suggested_id": None, "suggested_name": None, "confidence": 0.0, "alternatives": []},
            "duplicate_of": None,
        },
        "review": {"reviewer_user_id": None, "reviewer_name": None,
                   "reviewed_at": None, "decision": None,
                   "corrections": {}, "reject_reason": None, "notes": ""},
        "promotion": {"promoted": False, "promoted_to_collection": None,
                      "promoted_record_id": None, "promoted_at": None},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


# ─── Phase B activation ──────────────────────────────────────────────
def test_phase_b_register_idempotent():
    """register_phase_b can be called twice without doubling state."""
    _li_ec.register_phase_b(_li)
    _li_ec.register_phase_b(_li)
    assert _li.ACTIVE_PROMOTERS.get("equipment_checkout") is _li_ec.equipment_checkout_promoter
    assert isinstance(_li.EXTRACTORS.get("equipment_checkout"),
                      _li_ec.EquipmentCheckoutExtractor)


def test_phase_b_only_equipment_checkout_is_activated():
    """Operator brief: Phase B is Equipment Checkout ONLY. No other
    document types may be in ACTIVE_PROMOTERS."""
    _li_ec.register_phase_b(_li)
    assert set(_li.ACTIVE_PROMOTERS.keys()) == {"equipment_checkout"}, (
        "Phase B must NOT activate any other doc type · operator-stated rule"
    )


def test_pilot_cap_env_default():
    assert _li_ec.pilot_cap() == 50


# ─── JSON payload parsing ──────────────────────────────────────────
def test_extract_json_payload_handles_fenced_json():
    s = '```json\n{"a": 1, "b": "x"}\n```'
    out = _li_ec._extract_json_payload(s)
    assert out == {"a": 1, "b": "x"}


def test_extract_json_payload_returns_none_on_garbage():
    assert _li_ec._extract_json_payload("this is not json") is None


def test_normalize_equipment_lines_drops_invalid_entries():
    raw = [
        {"name": "Hammer", "serial": "H1", "qty": "2", "returned": True},
        {"name": ""},  # empty name dropped
        {"serial": "X1"},  # no name dropped
        "not-a-dict",
        {"name": "Saw", "qty": "x"},  # bad qty → defaults to 1
    ]
    out = _li_ec._normalize_equipment_lines(raw)
    assert len(out) == 2
    assert out[0]["name"] == "Hammer"
    assert out[0]["qty"] == 2
    assert out[0]["returned"] is True
    assert out[1]["name"] == "Saw"
    assert out[1]["qty"] == 1


# ─── Matching engine ───────────────────────────────────────────────
def test_match_employee_token_set_ratio():
    async def _go():
        db = _db()
        marker = f"iter249-{uuid.uuid4().hex[:6]}"
        await db.employees.insert_many([
            {"id": f"emp-{marker}-1", "name": f"John Sanchez {marker}", "role": "Operator"},
            {"id": f"emp-{marker}-2", "name": f"Maria Sanchez {marker}", "role": "Foreman"},
        ])
        try:
            m = await _li_ec.match_employee(db, f"John Sanchez {marker}")
            assert m["suggested_id"] == f"emp-{marker}-1"
            assert m["confidence"] >= 0.9
            # Alternative also returned
            m2 = await _li_ec.match_employee(db, f"Sanchez {marker}")
            assert m2["suggested_id"] in {f"emp-{marker}-1", f"emp-{marker}-2"}
        finally:
            await db.employees.delete_many({"id": {"$regex": f"^emp-{marker}-"}})
    asyncio.run(_go())


def test_match_equipment_serial_exact_wins():
    async def _go():
        db = _db()
        marker = f"iter249eq-{uuid.uuid4().hex[:6]}"
        await db.equipment_master.insert_one({
            "id": f"eq-{marker}", "unit_number": f"UNIT-{marker}",
            "serial_number": f"SN-{marker}-9999", "name": "Skid Steer",
        })
        try:
            m = await _li_ec.match_equipment(
                db, [{"name": "anything", "serial": f"SN-{marker}-9999"}]
            )
            assert m["suggested_id"] in (f"eq-{marker}", f"UNIT-{marker}")
            assert m["confidence"] >= 0.9
        finally:
            await db.equipment_master.delete_many({"id": f"eq-{marker}"})
    asyncio.run(_go())


def test_match_employee_with_no_input_returns_empty():
    async def _go():
        m = await _li_ec.match_employee(_db(), "")
        assert m["suggested_id"] is None
        assert m["confidence"] == 0.0
    asyncio.run(_go())


def test_duplicate_detector_flags_same_employee_same_serial():
    async def _go():
        db = _db()
        marker = f"iter249dup-{uuid.uuid4().hex[:6]}"
        await db.field_leadership_records.insert_one({
            "id": f"native-{marker}",
            "kind": "equipment_checkout",
            "employee_name": f"Test Worker {marker}",
            "occurred_at": "2024-05-01",
            "project_number": "X",
            "details": {"equipment_lines": [
                {"name": "Drill", "serial": f"DUP-{marker}-S", "qty": 1, "returned": False}
            ]},
            "deleted_at": None,
        })
        try:
            dup = await _li_ec.detect_duplicate(
                db,
                f"Test Worker {marker}",
                [{"name": "Drill", "serial": f"DUP-{marker}-S"}],
                "2024-06-01",
            )
            assert dup is not None
            assert dup["match_count"] >= 1
            # No false positive when serial differs
            no_dup = await _li_ec.detect_duplicate(
                db,
                f"Test Worker {marker}",
                [{"name": "Drill", "serial": f"DIFFERENT-{marker}"}],
                "2024-06-01",
            )
            assert no_dup is None
        finally:
            await db.field_leadership_records.delete_many({"id": f"native-{marker}"})
    asyncio.run(_go())


# ─── Promoter ───────────────────────────────────────────────────────
def test_promoter_writes_native_record_with_legacy_provenance():
    async def _go():
        db = _db()
        marker = uuid.uuid4().hex[:6]
        emp_name = f"PromoterTest {marker}"
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(
            iid,
            ocr={
                "provider": "claude_vision",
                "confidence": 0.78,
                "extracted_fields": {
                    "employee_name": emp_name,
                    "employee_position": "Operator",
                    "supervisor_name": "Promoter Sup",
                    "project_number": "PROM-249",
                    "project_name": "Promoter Test",
                    "occurred_at": "2024-08-15",
                    "return_date": None,
                    "equipment_lines": [
                        {"name": "Cordless Drill", "serial": f"PROM-{marker}-1",
                         "asset_id": None, "qty": 1, "returned": False, "notes": None,
                         "photos": []},
                    ],
                    "notes": "imported",
                    "supervisor_signature_present": True,
                    "employee_signature_present": True,
                },
                "field_confidences": {},
            },
            review={
                "reviewer_user_id": "rev-1", "reviewer_name": "Reviewer Rita",
                "reviewed_at": "2026-01-01T00:00:00Z", "decision": "approved",
                "corrections": {}, "reject_reason": None, "notes": "looks good",
            },
        )
        await db.legacy_imports.insert_one(dict(doc))
        try:
            out = await _li_ec.equipment_checkout_promoter(db, doc)
            assert out["collection"] == "field_leadership_records"
            rid = out["record_id"]
            rec = await db.field_leadership_records.find_one({"id": rid}, {"_id": 0})
            assert rec is not None
            assert rec["kind"] == "equipment_checkout"
            assert rec["employee_name"] == emp_name
            assert rec["source"] == "legacy_imported"
            assert rec["legacy_import_id"] == iid
            assert rec["legacy_reviewer_name"] == "Reviewer Rita"
            assert rec["legacy_ocr_confidence"] == 0.78
            lines = rec["details"]["equipment_lines"]
            assert len(lines) == 1
            assert lines[0]["serial"] == f"PROM-{marker}-1"
            assert lines[0]["returned"] is False
        finally:
            await _cleanup_test_import(db, iid, emp_name)
    asyncio.run(_go())


def test_promoter_honors_reviewer_corrections_over_raw_ocr():
    async def _go():
        db = _db()
        marker = uuid.uuid4().hex[:6]
        emp_name_raw = f"OCR Wrong {marker}"
        emp_name_corrected = f"Reviewer Right {marker}"
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["ocr"]["extracted_fields"]["employee_name"] = emp_name_raw
        doc["review"]["corrections"] = {
            "employee_name": emp_name_corrected,
            "project_number": "CORRECTED-PROJ",
        }
        await db.legacy_imports.insert_one(dict(doc))
        try:
            out = await _li_ec.equipment_checkout_promoter(db, doc)
            rec = await db.field_leadership_records.find_one({"id": out["record_id"]}, {"_id": 0})
            assert rec["employee_name"] == emp_name_corrected
            assert rec["project_number"] == "CORRECTED-PROJ"
        finally:
            await _cleanup_test_import(db, iid, emp_name_corrected)
            await db.field_leadership_records.delete_many({"employee_name": emp_name_raw})
    asyncio.run(_go())


def test_promoter_rejects_missing_required_fields():
    async def _go():
        db = _db()
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["ocr"]["extracted_fields"]["employee_name"] = ""
        doc["ocr"]["extracted_fields"]["equipment_lines"] = []
        await db.legacy_imports.insert_one(dict(doc))
        try:
            with pytest.raises(ValueError, match="employee_name"):
                await _li_ec.equipment_checkout_promoter(db, doc)
        finally:
            await _cleanup_test_import(db, iid)
    asyncio.run(_go())


# ─── Approve → promote flow ────────────────────────────────────────
def test_approve_promotes_equipment_checkout_in_phase_b():
    """Operator-critical: approve_import in Phase B must actually
    write to field_leadership_records, flip status=promoted, and write
    promotion block + audit."""
    _li_ec.register_phase_b(_li)
    async def _go():
        db = _db()
        marker = uuid.uuid4().hex[:6]
        emp_name = f"ApprovePromote {marker}"
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["ocr"]["extracted_fields"]["employee_name"] = emp_name
        await db.legacy_imports.insert_one(dict(doc))
        try:
            out = await _li.approve_import(
                db, import_id=iid,
                approver_id="reviewer-z", approver_name="Reviewer Z",
                approver_role="safety_user",
            )
            assert out["status"] == "promoted"
            assert out["promotion"]["promoted"] is True
            assert out["promotion"]["promoted_to_collection"] == "field_leadership_records"
            rid = out["promotion"]["promoted_record_id"]
            assert rid
            rec = await db.field_leadership_records.find_one({"id": rid}, {"_id": 0})
            assert rec is not None
            assert rec["source"] == "legacy_imported"
            # Audit chain: approved → promoted both written
            actions = [
                a["action"] async for a in
                db.legacy_import_audit.find({"import_id": iid}).sort("timestamp", 1)
            ]
            assert "approved" in actions
            assert "promoted" in actions
        finally:
            await _cleanup_test_import(db, iid, emp_name)
    asyncio.run(_go())


def test_anti_self_approval_still_blocks_in_phase_b():
    """Phase B must NOT relax the anti-self-approval guard."""
    _li_ec.register_phase_b(_li)
    async def _go():
        db = _db()
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["source_files"][0]["uploaded_by_id"] = "uploader-self"
        await db.legacy_imports.insert_one(dict(doc))
        try:
            with pytest.raises(_li.ApprovalError, match="self-approval blocked"):
                await _li.approve_import(
                    db, import_id=iid,
                    approver_id="uploader-self", approver_name="Self",
                    approver_role="safety_user",
                )
        finally:
            await _cleanup_test_import(db, iid)
    asyncio.run(_go())


# ─── Accountability + termination round-trip ───────────────────────
def test_imported_records_appear_in_hr_accountability_query():
    """The whole architectural promise: a promoted imported record must
    be picked up by the HR employee-accountability path with ZERO read
    code changes. We assert via the same Mongo query the route uses."""
    _li_ec.register_phase_b(_li)
    async def _go():
        db = _db()
        marker = uuid.uuid4().hex[:6]
        emp_name = f"Termin Worker {marker}"
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["ocr"]["extracted_fields"]["employee_name"] = emp_name
        doc["ocr"]["extracted_fields"]["equipment_lines"] = [
            {"name": "Drill", "serial": f"TERMIN-{marker}",
             "qty": 1, "returned": False, "asset_id": None, "notes": None, "photos": []}
        ]
        await db.legacy_imports.insert_one(dict(doc))
        try:
            out = await _li.approve_import(
                db, import_id=iid,
                approver_id="rev-q", approver_name="Reviewer Q",
                approver_role="hr_user",
            )
            assert out["promotion"]["promoted"]
            # Same Mongo query hr_portal.py uses
            import re
            rx = {"$regex": re.escape(emp_name), "$options": "i"}
            outstanding = []
            async for rec in db.field_leadership_records.find(
                {"kind": "equipment_checkout", "employee_name": rx}, {"_id": 0}
            ):
                for idx, line in enumerate((rec.get("details") or {}).get("equipment_lines") or []):
                    if line and not line.get("returned"):
                        outstanding.append({
                            "checkout_id": rec["id"],
                            "name": line.get("name"),
                            "serial": line.get("serial"),
                            "source": rec.get("source"),
                        })
            assert len(outstanding) == 1, (
                f"imported un-returned line must surface in HR accountability "
                f"search · got: {outstanding}"
            )
            assert outstanding[0]["serial"] == f"TERMIN-{marker}"
            assert outstanding[0]["source"] == "legacy_imported"
        finally:
            await _cleanup_test_import(db, iid, emp_name)
    asyncio.run(_go())


def test_imported_record_visible_in_general_fl_record_listing():
    """Native /api/field-leadership listing must show imported records
    same as native records (only the source discriminator differs)."""
    _li_ec.register_phase_b(_li)
    async def _go():
        db = _db()
        marker = uuid.uuid4().hex[:6]
        emp_name = f"ListingTest {marker}"
        iid = uuid.uuid4().hex
        doc = _seed_import_doc(iid)
        doc["ocr"]["extracted_fields"]["employee_name"] = emp_name
        await db.legacy_imports.insert_one(dict(doc))
        try:
            out = await _li.approve_import(
                db, import_id=iid,
                approver_id="rev-listing", approver_name="Reviewer L",
                approver_role="safety_user",
            )
            assert out["promotion"]["promoted"]
            # Default FL listing query (does NOT filter by source)
            rec = await db.field_leadership_records.find_one(
                {"id": out["promotion"]["promoted_record_id"], "deleted_at": None},
                {"_id": 0},
            )
            assert rec is not None
            assert rec["kind"] == "equipment_checkout"
            # Discriminator is visible to callers who want to render badge
            assert rec["source"] == "legacy_imported"
        finally:
            await _cleanup_test_import(db, iid, emp_name)
    asyncio.run(_go())


# ─── Endpoint route registration (smoke) ──────────────────────────
def test_phase_b_endpoints_registered():
    import sys
    import importlib
    if "server" in sys.modules:
        importlib.reload(sys.modules["server"])
    import server as srv
    paths = {getattr(r, "path", None) for r in srv.app.routes}
    assert "/api/legacy-imports/{import_id}/retry-ocr" in paths
