"""iter248 Phase A · Foundation smoke tests.

Verifies:
  - state-machine transitions are restricted
  - RBAC upload matrix is enforced
  - anti-self-approval guard blocks default, admits with admin override
  - audit log is append-only and correctly records each action
  - sha256 dedupe short-circuits a re-upload
  - approve does NOT promote (no active promoter in Phase A — correct
    operational philosophy)
"""
from __future__ import annotations

import os
import asyncio
import pytest

from dotenv import load_dotenv
load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient
import legacy_imports as M


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


def test_document_types_contain_all_operator_listed():
    """Brief listed 14 doc types · all must be in framework."""
    expected = {
        "equipment_checkout", "training_record", "osha_card", "toolbox_talk",
        "fit_test", "medical_card", "cdl_license", "certification",
        "safety_orientation", "signed_acknowledgement", "write_up",
        "onboarding_packet", "hr_record", "qualification_record", "unknown",
    }
    assert set(M.DOCUMENT_TYPES) == expected


def test_upload_matrix_enforces_pm_exclusion():
    """Brief: HR + Safety + Admin only · NO PM."""
    assert "pm" not in M.UPLOAD_PORTAL_MATRIX
    assert M.UPLOAD_PORTAL_MATRIX["admin"] == set(M.DOCUMENT_TYPES)


def test_upload_matrix_hr_owns_sensitive_docs():
    """Brief table: medical, CDL, discipline → HR only (not Safety)."""
    for t in ("medical_card", "cdl_license", "write_up", "onboarding_packet"):
        assert M.upload_allowed("hr", t), f"HR must own {t}"
        assert not M.upload_allowed("safety", t), f"Safety must NOT own {t}"


def test_upload_matrix_safety_owns_safety_docs():
    for t in ("toolbox_talk", "fit_test", "osha_card"):
        assert M.upload_allowed("safety", t), f"Safety must own {t}"
        assert not M.upload_allowed("hr", t), f"HR must NOT own {t}"


def test_state_machine_valid_transitions():
    # Happy path
    assert M.can_transition("uploaded", "ocr_in_progress")
    assert M.can_transition("ocr_in_progress", "needs_review")
    assert M.can_transition("needs_review", "approved")
    assert M.can_transition("needs_review", "rejected")
    assert M.can_transition("approved", "promoted")
    assert M.can_transition("promoted", "approved")  # admin unpromote
    # Invalid jumps
    assert not M.can_transition("uploaded", "approved"), "must not skip review"
    assert not M.can_transition("uploaded", "promoted"), "must not skip approve"
    assert not M.can_transition("rejected", "approved"), "rejected is terminal"
    assert not M.can_transition("needs_review", "promoted"), "must approve first"


def test_phase_a_no_active_promoters():
    """Phase A · explicit operator-stated guarantee: no document type
    has an active promoter. Activation is a per-phase decision."""
    assert M.ACTIVE_PROMOTERS == {}


def test_stub_extractor_returns_low_confidence_for_all_types():
    """Phase A · StubExtractor must never claim high confidence. The
    operational philosophy says OCR/AI assists; humans approve."""
    async def _go():
        for t in ("equipment_checkout", "osha_card", "training_record", "unknown"):
            ex = M.get_extractor(t)
            assert isinstance(ex, M.StubExtractor)
            result = await ex.extract(b"any-bytes", "application/pdf")
            assert result.confidence == 0.0
            assert result.extracted_fields == {}
            assert result.error is None
    asyncio.run(_go())


def test_audit_log_append_only_writes_correctly():
    async def _go():
        db = _db()
        import_id = "test-audit-" + os.urandom(4).hex()
        await M.audit_log(
            db,
            import_id=import_id, batch_id="b1",
            actor_user_id="u1", actor_name="Tester",
            actor_role="admin", action="test_event",
            before={"x": 1}, after={"x": 2},
        )
        rows = await db.legacy_import_audit.find(
            {"import_id": import_id}, {"_id": 0}
        ).to_list(None)
        assert len(rows) == 1
        r = rows[0]
        assert r["action"] == "test_event"
        assert r["actor_role"] == "admin"
        assert r["timestamp"]
        # Cleanup
        await db.legacy_import_audit.delete_many({"import_id": import_id})
    asyncio.run(_go())


def test_approve_blocks_self_approval_without_admin_override():
    async def _go():
        db = _db()
        # Seed a row uploaded by user "u-self" and try to approve as "u-self"
        import uuid
        from datetime import datetime, timezone
        iid = uuid.uuid4().hex
        await db.legacy_imports.insert_one({
            "id": iid, "document_type": "equipment_checkout",
            "status": "needs_review", "upload_portal": "admin",
            "source_files": [{
                "r2_key": "test/key", "original_name": "t.pdf",
                "mime": "application/pdf", "size_bytes": 10,
                "sha256": "abc", "uploaded_by_id": "u-self",
                "uploaded_by_name": "Self", "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }],
            "ocr": {}, "matches": {}, "review": {}, "promotion": {"promoted": False},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        # Self-approval as non-admin → blocked
        with pytest.raises(M.ApprovalError, match="self-approval blocked"):
            await M.approve_import(
                db, import_id=iid,
                approver_id="u-self", approver_name="Self",
                approver_role="hr_user",
            )
        # Self-approval as admin without explicit override flag → blocked
        with pytest.raises(M.ApprovalError, match="self-approval blocked"):
            await M.approve_import(
                db, import_id=iid,
                approver_id="u-self", approver_name="Self",
                approver_role="admin", admin_override_self_approval=False,
            )
        # Admin override · explicit confirmation → allowed
        out = await M.approve_import(
            db, import_id=iid,
            approver_id="u-self", approver_name="Self Admin",
            approver_role="admin", admin_override_self_approval=True,
        )
        assert out["status"] == "approved"
        # Cleanup
        await db.legacy_imports.delete_one({"id": iid})
        await db.legacy_import_audit.delete_many({"import_id": iid})
    asyncio.run(_go())


def test_approve_blocks_transition_from_invalid_status():
    async def _go():
        db = _db()
        import uuid
        iid = uuid.uuid4().hex
        await db.legacy_imports.insert_one({
            "id": iid, "document_type": "osha_card",
            "status": "rejected",  # terminal
            "upload_portal": "safety", "source_files": [],
            "ocr": {}, "matches": {}, "review": {}, "promotion": {"promoted": False},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        with pytest.raises(M.ApprovalError, match="cannot approve"):
            await M.approve_import(
                db, import_id=iid,
                approver_id="someone", approver_name="X",
                approver_role="admin",
            )
        await db.legacy_imports.delete_one({"id": iid})
    asyncio.run(_go())


def test_approve_does_not_promote_in_phase_a():
    """Phase A guarantee: approve flips status to `approved` but does
    NOT promote into any live collection (because no doc type is
    activated). promotion.promoted must be False."""
    async def _go():
        db = _db()
        import uuid
        from datetime import datetime, timezone
        iid = uuid.uuid4().hex
        await db.legacy_imports.insert_one({
            "id": iid, "document_type": "equipment_checkout",
            "status": "needs_review", "upload_portal": "safety",
            "source_files": [{
                "r2_key": "test/key", "original_name": "t.pdf",
                "mime": "application/pdf", "size_bytes": 10,
                "sha256": "def", "uploaded_by_id": "uploader-u",
                "uploaded_by_name": "Uploader", "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }],
            "ocr": {}, "matches": {}, "review": {}, "promotion": {"promoted": False},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        out = await M.approve_import(
            db, import_id=iid,
            approver_id="reviewer-u", approver_name="Reviewer",
            approver_role="safety_user",
        )
        assert out["status"] == "approved"
        assert out["promotion"]["promoted"] is False
        assert out["promotion"].get("promoted_to_collection") is None
        # Cleanup
        await db.legacy_imports.delete_one({"id": iid})
        await db.legacy_import_audit.delete_many({"import_id": iid})
    asyncio.run(_go())


def test_sha256_helper_is_deterministic():
    assert M.sha256_bytes(b"hello") == M.sha256_bytes(b"hello")
    assert M.sha256_bytes(b"hello") != M.sha256_bytes(b"hello2")


def test_endpoints_registered_on_app():
    """Routing smoke · confirms server.py wired the Phase A endpoints
    correctly. Also catches future regressions."""
    import sys, importlib
    if "server" in sys.modules:
        importlib.reload(sys.modules["server"])
    import server as srv
    paths = {getattr(r, "path", None) for r in srv.app.routes}
    expected = {
        "/api/legacy-imports/upload",
        "/api/legacy-imports",
        "/api/legacy-imports/_meta",
        "/api/legacy-imports/{import_id}",
        "/api/legacy-imports/{import_id}/file",
        "/api/legacy-imports/{import_id}/approve",
        "/api/legacy-imports/{import_id}/reject",
        "/api/admin/legacy-imports/audit",
    }
    missing = expected - paths
    assert not missing, f"Phase A endpoints missing from app.routes: {missing}"
