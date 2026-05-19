"""iter249 Phase B · Pilot Debrief tests.

Operator-approved Option A scope: read-only admin-only debrief endpoint
that aggregates all the pilot evidence into one structured JSON.

Coverage:
  - Anon-RBAC: endpoint returns 401 to unauthenticated callers
  - Non-equipment_checkout document_type returns 400 (scope guard)
  - Empty DB: structured response with zero counts + NOT_READY verdict
  - Seeded: all required fields populated · counts correct ·
    diff examples surface · failed extraction shows error text ·
    unmatched employee/equipment rows surface · roundtrip ok/missing
    counted correctly · evidence_access_audit count from audit log
  - Readiness verdict heuristic: READY · NEEDS_TUNING · NOT_READY
    paths each fire under the right conditions
  - Round-trip-missing → NOT_READY (accountability chain check)
"""
from __future__ import annotations

import os
import re
import uuid
import asyncio
import pytest
import requests

from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import legacy_imports as _li  # noqa: E402
import legacy_imports_equipment_checkout as _li_ec  # noqa: E402


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def admin_token():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "MASCI1982!")},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


# ─── HTTP-level tests ──────────────────────────────────────────────────
def test_pilot_debrief_anon_blocked():
    """Anon callers get 401 · admin-strict gate. Uses urllib directly
    so the conftest auto-admin-token patch can't interfere."""
    if not URL:
        pytest.skip("URL not configured")
    import urllib.request
    import urllib.error
    req = urllib.request.Request(f"{URL}/api/admin/legacy-imports/pilot-debrief")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon call should have returned 401/403")
    except urllib.error.HTTPError as e:
        # 401 = app-level admin gate · 403 = edge bot-detection · both
        # confirm the endpoint is not anonymously reachable.
        assert e.code in (401, 403), f"unexpected anon status: {e.code}"


def test_pilot_debrief_rejects_non_equipment_checkout(admin_token):
    """Scope guard · operator approved equipment_checkout only."""
    r = requests.get(
        f"{URL}/api/admin/legacy-imports/pilot-debrief?document_type=osha_card",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert r.status_code == 400
    assert "equipment_checkout" in r.text.lower()


def test_pilot_debrief_returns_required_shape(admin_token):
    """Smoke · live call returns the operator-required JSON keys."""
    r = requests.get(
        f"{URL}/api/admin/legacy-imports/pilot-debrief",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    for k in ("document_type", "counts", "ocr_confidence",
              "reviewer_corrections", "failed_extractions",
              "unmatched_employee_rows", "unmatched_equipment_rows",
              "duplicate_suspicion_count", "evidence_access_audit_count",
              "audit_action_counts", "accountability_roundtrip",
              "termination_flag_verification", "readiness_verdict",
              "readiness_reasons", "scope_note"):
        assert k in d, f"missing required debrief key: {k!r}"
    assert d["document_type"] == "equipment_checkout"
    assert d["readiness_verdict"] in ("READY", "NEEDS_TUNING", "NOT_READY")


# ─── Aggregation correctness (direct function call) ──────────────────
def test_debrief_empty_db_returns_not_ready():
    """Empty pilot → NOT_READY verdict."""
    async def _go():
        db = _db()
        # Snapshot existing equipment_checkout imports (if any) and skip
        # the test cleanly if the env is dirty · we won't mutate prod data.
        existing = await db.legacy_imports.count_documents(
            {"document_type": "equipment_checkout"}
        )
        if existing > 0:
            pytest.skip("preview DB has prior equipment_checkout imports · "
                        "test_debrief_empty_db_returns_not_ready needs a clean slate")
        out = await _li_ec.compute_pilot_debrief(db)
        assert out["counts"]["uploaded"] == 0
        assert out["readiness_verdict"] == "NOT_READY"
        assert any("No imports uploaded" in r for r in out["readiness_reasons"])
    asyncio.run(_go())


def test_debrief_aggregates_seeded_pilot_correctly():
    """Seed a realistic pilot batch + verify counts, diffs, unmatched
    rows, and roundtrip stats all surface correctly."""
    _li_ec.register_phase_b(_li)
    async def _go():
        db = _db()
        marker = f"debrief-{uuid.uuid4().hex[:6]}"
        ids: list = []
        native_ids: list = []
        emp_names: list = []
        try:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()

            # ── Seed 1: needs_review row with low employee match
            i1 = uuid.uuid4().hex
            ids.append(i1)
            await db.legacy_imports.insert_one({
                "id": i1, "document_type": "equipment_checkout",
                "status": "needs_review", "upload_portal": "safety",
                "batch_id": marker,
                "source_files": [{"r2_key": f"{marker}/k1", "original_name": "form1.pdf",
                                   "mime": "application/pdf", "size_bytes": 100,
                                   "sha256": f"sha-{i1}", "uploaded_by_id": "u1",
                                   "uploaded_by_name": "Up1", "uploaded_at": now_iso}],
                "ocr": {"provider": "claude_vision", "confidence": 0.8,
                        "extracted_fields": {"employee_name": f"Unknown Worker {marker}",
                                             "equipment_lines": [
                                                 {"name": "Drill", "serial": f"SN-{marker}-1",
                                                  "qty": 1, "returned": False}
                                             ]}, "error": None,
                        "field_confidences": {}},
                "matches": {
                    "employee": {"suggested_id": None, "suggested_name": None,
                                 "confidence": 0.0, "alternatives": []},
                    "equipment": {"suggested_id": None, "suggested_name": None,
                                  "confidence": 0.0, "alternatives": []},
                    "project": {}, "duplicate_of": None,
                },
                "review": {}, "promotion": {"promoted": False},
                "created_at": now_iso, "updated_at": now_iso,
            })

            # ── Seed 2: ocr_failed row with blank-image error
            i2 = uuid.uuid4().hex
            ids.append(i2)
            await db.legacy_imports.insert_one({
                "id": i2, "document_type": "equipment_checkout",
                "status": "ocr_failed", "upload_portal": "hr",
                "batch_id": marker,
                "source_files": [{"r2_key": f"{marker}/k2", "original_name": "blank.png",
                                   "mime": "image/png", "size_bytes": 250,
                                   "sha256": f"sha-{i2}", "uploaded_by_id": "u2",
                                   "uploaded_by_name": "Up2", "uploaded_at": now_iso}],
                "ocr": {"provider": "claude_vision", "confidence": 0.0,
                        "extracted_fields": {}, "error": "blank image",
                        "field_confidences": {}},
                "matches": {"duplicate_of": None}, "review": {},
                "promotion": {"promoted": False},
                "created_at": now_iso, "updated_at": now_iso,
            })

            # ── Seed 3: rejected with notes
            i3 = uuid.uuid4().hex
            ids.append(i3)
            await db.legacy_imports.insert_one({
                "id": i3, "document_type": "equipment_checkout",
                "status": "rejected", "upload_portal": "safety",
                "batch_id": marker,
                "source_files": [{"r2_key": f"{marker}/k3", "original_name": "wrong.jpg",
                                   "mime": "image/jpeg", "size_bytes": 5000,
                                   "sha256": f"sha-{i3}", "uploaded_by_id": "u3",
                                   "uploaded_by_name": "Up3", "uploaded_at": now_iso}],
                "ocr": {"provider": "claude_vision", "confidence": 0.4,
                        "extracted_fields": {}, "error": None},
                "matches": {"duplicate_of": None},
                "review": {"reviewer_name": "Rev R", "reviewed_at": now_iso,
                           "decision": "rejected", "reject_reason": "wrong_document_type",
                           "notes": "this is actually an OSHA card, not equipment checkout",
                           "corrections": {}},
                "promotion": {"promoted": False},
                "created_at": now_iso, "updated_at": now_iso,
            })

            # ── Seed 4: promoted row that DOES have a matching native record
            i4 = uuid.uuid4().hex
            ids.append(i4)
            emp4 = f"Promoted Worker {marker}"
            emp_names.append(emp4)
            native_4 = uuid.uuid4().hex
            native_ids.append(native_4)
            await db.legacy_imports.insert_one({
                "id": i4, "document_type": "equipment_checkout",
                "status": "promoted", "upload_portal": "safety",
                "batch_id": marker,
                "source_files": [{"r2_key": f"{marker}/k4", "original_name": "good.pdf",
                                   "mime": "application/pdf", "size_bytes": 200000,
                                   "sha256": f"sha-{i4}", "uploaded_by_id": "u4",
                                   "uploaded_by_name": "Up4", "uploaded_at": now_iso}],
                "ocr": {"provider": "claude_vision", "confidence": 0.92,
                        "extracted_fields": {
                            "employee_name": emp4,
                            "equipment_lines": [
                                {"name": "Grinder", "serial": f"SN-{marker}-good",
                                 "qty": 1, "returned": False}
                            ],
                        }, "error": None},
                "matches": {"duplicate_of": None,
                            "employee": {"suggested_id": "x", "suggested_name": "x",
                                         "confidence": 0.9, "alternatives": []},
                            "equipment": {"suggested_id": "y", "suggested_name": "y",
                                          "confidence": 0.95, "alternatives": []},
                            "project": {}},
                "review": {"reviewer_name": "Rev O", "reviewed_at": now_iso,
                           "decision": "approved",
                           "corrections": {"project_number": "CORRECTED-249"},
                           "notes": "everything legible · approved"},
                "promotion": {"promoted": True,
                              "promoted_to_collection": "field_leadership_records",
                              "promoted_record_id": native_4,
                              "promoted_at": now_iso},
                "created_at": now_iso, "updated_at": now_iso,
            })
            await db.field_leadership_records.insert_one({
                "id": native_4, "kind": "equipment_checkout",
                "source": "legacy_imported", "legacy_import_id": i4,
                "employee_name": emp4, "deleted_at": None,
                "details": {"equipment_lines": [
                    {"name": "Grinder", "serial": f"SN-{marker}-good",
                     "qty": 1, "returned": False}]},
                "occurred_at": "2024-08-15",
                "created_at": now_iso, "updated_at": now_iso,
            })

            # ── Seed 5: promoted row but native missing (roundtrip break)
            i5 = uuid.uuid4().hex
            ids.append(i5)
            await db.legacy_imports.insert_one({
                "id": i5, "document_type": "equipment_checkout",
                "status": "promoted", "upload_portal": "safety",
                "batch_id": marker,
                "source_files": [{"r2_key": f"{marker}/k5", "original_name": "missing.pdf",
                                   "mime": "application/pdf", "size_bytes": 100000,
                                   "sha256": f"sha-{i5}", "uploaded_by_id": "u5",
                                   "uploaded_by_name": "Up5", "uploaded_at": now_iso}],
                "ocr": {"provider": "claude_vision", "confidence": 0.7,
                        "extracted_fields": {"employee_name": f"Orphan {marker}",
                                             "equipment_lines": []},
                        "error": None},
                "matches": {"duplicate_of": None,
                            "employee": {"suggested_id": "z", "suggested_name": "z",
                                         "confidence": 0.8, "alternatives": []},
                            "equipment": {"suggested_id": None, "confidence": 0.0,
                                          "alternatives": []},
                            "project": {}},
                "review": {"reviewer_name": "Rev Q", "reviewed_at": now_iso,
                           "decision": "approved",
                           "corrections": {}, "notes": ""},
                "promotion": {"promoted": True,
                              "promoted_to_collection": "field_leadership_records",
                              "promoted_record_id": "does-not-exist-" + marker,
                              "promoted_at": now_iso},
                "created_at": now_iso, "updated_at": now_iso,
            })

            # ── Some evidence-access audit rows
            for _ in range(3):
                await _li.audit_log(
                    db, import_id=i4, batch_id=marker,
                    actor_user_id="evidence-viewer",
                    actor_name="Evidence Viewer",
                    actor_role="admin", action="evidence_accessed",
                )

            out = await _li_ec.compute_pilot_debrief(db)
            counts = out["counts"]
            # Status counts include any prior data, so use >= for safety.
            assert counts["uploaded"] >= 5
            assert counts["ocr_failed"] >= 1
            assert counts["rejected"] >= 1
            assert counts["promoted"] >= 2
            # OCR confidence stats present
            assert out["ocr_confidence"]["sample_size"] >= 4
            assert out["ocr_confidence"]["avg"] is not None
            # Reviewer corrections show project_number diff for i4
            field_counts = out["reviewer_corrections"]["field_counts"]
            assert field_counts.get("project_number", 0) >= 1
            assert any(d["field"] == "project_number"
                       and d["corrected"] == "CORRECTED-249"
                       for d in out["reviewer_corrections"]["diff_examples"])
            # Reviewer notes captured
            assert any(marker in (n.get("notes") or "")
                       for n in out["reviewer_corrections"]["reviewer_notes"]) or \
                   any(n.get("decision") == "rejected"
                       for n in out["reviewer_corrections"]["reviewer_notes"])
            # Failed extraction with the blank image error appears
            assert any(f["error"] == "blank image"
                       for f in out["failed_extractions"])
            # Unmatched employee row (i1) surfaces
            assert any(r["import_id"] == i1 for r in out["unmatched_employee_rows"])
            # Roundtrip OK count = 1 (i4) · missing count = 1 (i5)
            assert out["accountability_roundtrip"]["promoted_native_records_ok"] >= 1
            assert out["accountability_roundtrip"]["promoted_native_records_missing"] >= 1
            # Evidence access count ≥ 3 (we audited 3)
            assert out["evidence_access_audit_count"] >= 3
            # Verdict NOT_READY (because roundtrip missing > 0)
            assert out["readiness_verdict"] == "NOT_READY"
            assert any("accountability chain broken" in r
                       for r in out["readiness_reasons"])
            # Termination flag verification: at least 1 employee checked
            assert out["termination_flag_verification"]["checked_employees"] >= 1
        finally:
            for iid in ids:
                await db.legacy_imports.delete_many({"id": iid})
                await db.legacy_import_audit.delete_many({"import_id": iid})
            for nid in native_ids:
                await db.field_leadership_records.delete_many({"id": nid})
            for ename in emp_names:
                await db.field_leadership_records.delete_many({"employee_name": ename})
    asyncio.run(_go())


# ─── Readiness verdict heuristic (pure-function unit tests) ──────────
def test_readiness_not_ready_when_no_uploads():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=0, ocr_failed_count=0, approved_count=0,
        rejected_count=0, promoted_count=0,
        ocr_confidence={"avg": None}, roundtrip_missing=0,
    )
    assert v == "NOT_READY"


def test_readiness_not_ready_when_roundtrip_missing():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=10, ocr_failed_count=0, approved_count=0,
        rejected_count=0, promoted_count=5,
        ocr_confidence={"avg": 0.9}, roundtrip_missing=1,
    )
    assert v == "NOT_READY"
    assert any("accountability chain" in x for x in r)


def test_readiness_ready_when_thresholds_met():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=12, ocr_failed_count=1, approved_count=2,
        rejected_count=1, promoted_count=8,
        ocr_confidence={"avg": 0.82}, roundtrip_missing=0,
    )
    assert v == "READY", (v, r)


def test_readiness_needs_tuning_on_high_failure_rate():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=12, ocr_failed_count=5, approved_count=2,
        rejected_count=2, promoted_count=3,
        ocr_confidence={"avg": 0.7}, roundtrip_missing=0,
    )
    assert v == "NEEDS_TUNING"
    assert any("OCR failure rate" in x for x in r)


def test_readiness_needs_tuning_on_low_confidence():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=12, ocr_failed_count=0, approved_count=2,
        rejected_count=1, promoted_count=8,
        ocr_confidence={"avg": 0.40}, roundtrip_missing=0,
    )
    assert v == "NEEDS_TUNING"
    assert any("Average OCR confidence" in x for x in r)


def test_readiness_needs_tuning_on_small_sample():
    v, r = _li_ec._readiness_verdict(
        uploaded_count=3, ocr_failed_count=0, approved_count=1,
        rejected_count=0, promoted_count=2,
        ocr_confidence={"avg": 0.9}, roundtrip_missing=0,
    )
    assert v == "NEEDS_TUNING"
    assert any("sample size" in x for x in r)


# ─── Route registration smoke ────────────────────────────────────────
def test_pilot_debrief_endpoint_registered():
    import sys, importlib
    if "server" in sys.modules:
        importlib.reload(sys.modules["server"])
    import server as srv
    paths = {getattr(r, "path", None) for r in srv.app.routes}
    assert "/api/admin/legacy-imports/pilot-debrief" in paths
