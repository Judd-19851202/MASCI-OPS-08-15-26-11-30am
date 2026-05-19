"""legacy_imports.py — iter248 Phase A · Foundation

Operational philosophy enforced architecturally:
  - OCR/AI assists, never decides.
  - Promotion to live collections requires explicit human approval.
  - Approved records carry full provenance (uploader · reviewer · OCR
    confidence · extraction method · original-file URL · batch ID).
  - Anti-self-approval: uploader cannot also be approver (Admin override
    is logged in the audit collection).
  - Promotion path is scaffolded but NOT yet activated for any
    document type. Phase A ships the framework; Phase B activates
    Equipment Checkout end-to-end after operator approval.

State machine (one-way except admin unpromote):
  uploaded
    -> ocr_in_progress (worker picks up)
    -> needs_review (OCR done)  OR  ocr_failed
    -> approved  (reviewer approves; promotion deferred to Phase B+)
    -> rejected  (reviewer rejects)
  approved
    -> promoted  (Phase B: actually written into live collection)
  promoted
    -> approved  (admin unpromote · keeps audit chain)

All transitions write to `legacy_import_audit` (append-only).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── Supported document types (Phase A: framework only · not activated) ──
DOCUMENT_TYPES = (
    "equipment_checkout",
    "training_record",
    "osha_card",
    "toolbox_talk",
    "fit_test",
    "medical_card",
    "cdl_license",
    "certification",
    "safety_orientation",
    "signed_acknowledgement",
    "write_up",
    "onboarding_packet",
    "hr_record",
    "qualification_record",
    "unknown",
)

# Phase A: no document type is activated for live-collection promotion.
# Phase B will set this to {"equipment_checkout": equipment_checkout_promoter}.
ACTIVE_PROMOTERS: Dict[str, Any] = {}

# RBAC matrix · which upload portals can submit which document types.
# Operator brief: HR / Safety / Admin only. NO PM uploads in Phase A.
UPLOAD_PORTAL_MATRIX: Dict[str, set] = {
    "hr": {
        "medical_card", "cdl_license", "signed_acknowledgement",
        "write_up", "onboarding_packet", "hr_record", "licensing",
        "certification", "safety_orientation", "qualification_record",
        "equipment_checkout",  # HR sometimes finds in onboarding packets
        "unknown",
    },
    "safety": {
        "equipment_checkout", "training_record", "osha_card",
        "toolbox_talk", "fit_test", "certification",
        "safety_orientation", "qualification_record", "unknown",
    },
    "admin": set(DOCUMENT_TYPES),  # Admin can route anything
}


def upload_allowed(upload_portal: str, document_type: str) -> bool:
    return document_type in UPLOAD_PORTAL_MATRIX.get(upload_portal, set())


# ── Pydantic models · API surface ──────────────────────────────────────
class SourceFile(BaseModel):
    r2_key: str
    original_name: str
    mime: str
    size_bytes: int
    sha256: str
    uploaded_by_id: str
    uploaded_by_name: str
    uploaded_at: str


class MatchSuggestion(BaseModel):
    suggested_id: Optional[str] = None
    suggested_name: Optional[str] = None
    confidence: float = 0.0
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)


class OcrBlock(BaseModel):
    provider: str = "stub"  # Phase A: stub. Phase B+: "claude_vision"
    completed_at: Optional[str] = None
    raw_text: str = ""
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    classifier_score: float = 0.0
    error: Optional[str] = None


class MatchesBlock(BaseModel):
    employee: MatchSuggestion = Field(default_factory=MatchSuggestion)
    equipment: MatchSuggestion = Field(default_factory=MatchSuggestion)
    project: MatchSuggestion = Field(default_factory=MatchSuggestion)
    duplicate_of: Optional[Dict[str, Any]] = None


class ReviewBlock(BaseModel):
    reviewer_user_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[str] = None
    decision: Optional[str] = None
    corrections: Dict[str, Any] = Field(default_factory=dict)
    reject_reason: Optional[str] = None
    notes: str = ""


class PromotionBlock(BaseModel):
    promoted: bool = False
    promoted_to_collection: Optional[str] = None
    promoted_record_id: Optional[str] = None
    promoted_at: Optional[str] = None


class LegacyImport(BaseModel):
    id: str
    document_type: str
    status: str = "uploaded"
    source_files: List[SourceFile] = Field(default_factory=list)
    upload_portal: str
    batch_id: Optional[str] = None
    ocr: OcrBlock = Field(default_factory=OcrBlock)
    matches: MatchesBlock = Field(default_factory=MatchesBlock)
    review: ReviewBlock = Field(default_factory=ReviewBlock)
    promotion: PromotionBlock = Field(default_factory=PromotionBlock)
    created_at: str
    updated_at: str


# ── Audit helpers ──────────────────────────────────────────────────────
async def audit_log(
    db,
    *,
    import_id: str,
    batch_id: Optional[str],
    actor_user_id: str,
    actor_name: str,
    actor_role: str,
    action: str,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    ip: str = "",
    user_agent: str = "",
) -> None:
    """Append-only audit row · powers HR/legal chain-of-custody reports."""
    row = {
        "id": uuid.uuid4().hex,
        "import_id": import_id,
        "batch_id": batch_id,
        "actor_user_id": actor_user_id,
        "actor_name": actor_name,
        "actor_role": actor_role,
        "action": action,
        "before": before,
        "after": after,
        "ip": ip,
        "user_agent": user_agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.legacy_import_audit.insert_one(row)
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[legacy-imports] audit write failed: {e}")


# ── Index bootstrap ────────────────────────────────────────────────────
async def ensure_indexes(db) -> None:
    try:
        await db.legacy_imports.create_index(
            [("status", 1), ("upload_portal", 1), ("created_at", -1)]
        )
        await db.legacy_imports.create_index([("source_files.sha256", 1)])
        await db.legacy_imports.create_index([("document_type", 1), ("status", 1)])
        await db.legacy_imports.create_index([("matches.employee.suggested_id", 1)])
        await db.legacy_imports.create_index([("batch_id", 1)])
        await db.legacy_import_audit.create_index([("import_id", 1), ("timestamp", -1)])
        await db.legacy_import_audit.create_index([("actor_user_id", 1), ("timestamp", -1)])
        logger.info("[legacy-imports] indexes ensured")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[legacy-imports] index bootstrap: {e}")


# ── Duplicate-upload short-circuit ─────────────────────────────────────
async def find_by_sha256(db, sha256: str) -> Optional[Dict[str, Any]]:
    return await db.legacy_imports.find_one(
        {"source_files.sha256": sha256}, {"_id": 0}
    )


# ── OCR provider abstraction (clean, NOT over-engineered) ──────────────
class OcrResult(BaseModel):
    raw_text: str = ""
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0
    classifier_score: float = 0.0
    classifier_doc_type: str = "unknown"
    error: Optional[str] = None


class BaseExtractor:
    """One concrete extractor per document type. Phase A ships only
    the base class + a no-op `StubExtractor`. Phase B will add
    `EquipmentCheckoutExtractor(BaseExtractor)`."""

    document_type: str = "unknown"
    required_fields: tuple = ()

    async def extract(self, file_bytes: bytes, mime: str) -> OcrResult:
        raise NotImplementedError


class StubExtractor(BaseExtractor):
    """Phase A · returns an empty result with low confidence so the
    reviewer has to manually fill every field. Proves the pipeline
    end-to-end without making any AI claims about the content."""

    document_type = "unknown"

    async def extract(self, file_bytes: bytes, mime: str) -> OcrResult:
        await asyncio.sleep(0)  # cooperative yield
        return OcrResult(
            raw_text="",
            extracted_fields={},
            field_confidences={},
            confidence=0.0,
            classifier_score=0.0,
            classifier_doc_type="unknown",
            error=None,
        )


# Phase B will register real extractors here.
EXTRACTORS: Dict[str, BaseExtractor] = {}


def get_extractor(document_type: str) -> BaseExtractor:
    return EXTRACTORS.get(document_type, StubExtractor())


# ── State-machine transitions ──────────────────────────────────────────
VALID_TRANSITIONS = {
    "uploaded": {"ocr_in_progress", "needs_review", "ocr_failed"},
    "ocr_in_progress": {"needs_review", "ocr_failed"},
    "ocr_failed": {"needs_review", "rejected"},  # reviewer can rescue
    "needs_review": {"approved", "rejected"},
    "approved": {"promoted", "rejected"},  # promotion or admin retract
    "promoted": {"approved"},  # admin unpromote
    "rejected": set(),  # terminal (admin can reopen via repair endpoint later)
    "duplicate": {"rejected"},  # terminal-ish
}


def can_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


# ── OCR worker · long-running async ────────────────────────────────────
_worker_task: Optional[asyncio.Task] = None


async def _load_source_bytes(doc: Dict[str, Any]) -> tuple[bytes, str]:
    """Fetch the first source_file's bytes from R2. Returns (bytes, mime).
    Empty bytes on failure · caller treats that as OCR failure."""
    files = doc.get("source_files") or []
    if not files:
        return b"", "application/octet-stream"
    f = files[0]
    key = f.get("r2_key")
    mime = f.get("mime") or "application/octet-stream"
    if not key:
        return b"", mime
    try:
        import photo_storage as _ps  # noqa: PLC0415
        c = _ps._client()
        if c is None:
            return b"", mime
        obj = await asyncio.to_thread(c.get_object, Bucket=_ps._bucket(), Key=key)
        body = obj["Body"]
        chunks = []
        while True:
            chunk = await asyncio.to_thread(body.read, 1024 * 512)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), mime
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[legacy-imports] r2 fetch failed for {key}: {e}")
        return b"", mime


async def ocr_worker_loop(db) -> None:
    """Picks up rows in `uploaded` · runs the appropriate extractor ·
    Phase A used StubExtractor universally · Phase B activates a real
    Claude Vision extractor for equipment_checkout (registered into
    EXTRACTORS by `legacy_imports_equipment_checkout.register_phase_b`).

    Stale-import sweeper: any row stuck in `ocr_in_progress` for >10
    min is reset to `uploaded` (crash-loop guard · same pattern as
    iter120 safety_digest and iter246 po_digest).

    After OCR completes successfully and a per-doc-type matcher is
    registered (Phase B: equipment_checkout), the worker also computes
    the matches block (employee · equipment · project · duplicate
    suspicion) so the reviewer has everything in front of them.
    """
    while True:
        try:
            # Reset stale in-progress rows (orphan workers from old restarts).
            cutoff = (datetime.now(timezone.utc).timestamp() - 600)
            cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
            await db.legacy_imports.update_many(
                {"status": "ocr_in_progress", "updated_at": {"$lt": cutoff_iso}},
                {"$set": {"status": "uploaded"}},
            )

            # Pick up the oldest uploaded row.
            doc = await db.legacy_imports.find_one_and_update(
                {"status": "uploaded"},
                {"$set": {
                    "status": "ocr_in_progress",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
                projection={"_id": 0},
            )
            if not doc:
                await asyncio.sleep(5)
                continue

            extractor = get_extractor(doc["document_type"])
            is_stub = isinstance(extractor, StubExtractor)
            matches_block: Optional[Dict[str, Any]] = None
            try:
                # Phase A stub doesn't need bytes. Phase B extractors do.
                if is_stub:
                    file_bytes, mime = b"", "application/octet-stream"
                else:
                    file_bytes, mime = await _load_source_bytes(doc)
                result = await extractor.extract(file_bytes, mime)
                new_status = "needs_review"
                ocr_block = {
                    "provider": ("stub" if is_stub else "claude_vision"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "raw_text": result.raw_text,
                    "extracted_fields": result.extracted_fields,
                    "confidence": result.confidence,
                    "field_confidences": result.field_confidences,
                    "classifier_score": result.classifier_score,
                    "error": result.error,
                }
                # Phase B · equipment_checkout matcher
                if (not is_stub
                        and not result.error
                        and result.extracted_fields
                        and doc["document_type"] == "equipment_checkout"):
                    try:
                        from legacy_imports_equipment_checkout import (  # noqa: PLC0415
                            compute_matches_block,
                        )
                        matches_block = await compute_matches_block(
                            db, result.extracted_fields
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.warning(
                            f"[legacy-imports] match build failed for {doc['id']}: {e}"
                        )
            except Exception as e:  # noqa: BLE001
                logger.exception(f"[legacy-imports] OCR crashed for {doc['id']}: {e}")
                new_status = "ocr_failed"
                ocr_block = {
                    "provider": ("claude_vision" if not is_stub else "stub"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)[:200],
                }

            update_set = {
                "status": new_status,
                "ocr": ocr_block,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if matches_block is not None:
                update_set["matches"] = matches_block
            await db.legacy_imports.update_one(
                {"id": doc["id"]},
                {"$set": update_set},
            )
            await audit_log(
                db,
                import_id=doc["id"],
                batch_id=doc.get("batch_id"),
                actor_user_id="system",
                actor_name="OCR Worker",
                actor_role="system",
                action="ocr_completed" if new_status == "needs_review" else "ocr_failed",
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[legacy-imports] worker iter crashed: {e}")
            await asyncio.sleep(60)


def start_worker(db) -> Optional[asyncio.Task]:
    """Idempotent worker start."""
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        return _worker_task
    _worker_task = asyncio.create_task(ocr_worker_loop(db))
    return _worker_task


# ── Approval/promotion (anti-self-approval guard) ─────────────────────
class ApprovalError(Exception):
    pass


async def approve_import(
    db,
    *,
    import_id: str,
    approver_id: str,
    approver_name: str,
    approver_role: str,  # "hr_user" | "safety_user" | "admin"
    corrections: Optional[Dict[str, Any]] = None,
    notes: str = "",
    admin_override_self_approval: bool = False,
) -> Dict[str, Any]:
    """Approve a legacy import. Phase A: marks status=approved, records
    reviewer, writes audit. Phase B+: branches on document_type to
    invoke the appropriate promoter (ACTIVE_PROMOTERS dict)."""
    doc = await db.legacy_imports.find_one({"id": import_id}, {"_id": 0})
    if not doc:
        raise ApprovalError("import not found")
    if not can_transition(doc["status"], "approved"):
        raise ApprovalError(
            f"cannot approve from status={doc['status']!r}"
        )

    # Anti-self-approval guard
    uploader_ids = [f.get("uploaded_by_id") for f in doc.get("source_files", [])]
    if approver_id in uploader_ids:
        if approver_role != "admin" or not admin_override_self_approval:
            raise ApprovalError(
                "self-approval blocked: uploader cannot be the approver "
                "(Admin override available with explicit confirmation)"
            )

    now = datetime.now(timezone.utc).isoformat()
    review_update = {
        "review.reviewer_user_id": approver_id,
        "review.reviewer_name": approver_name,
        "review.reviewed_at": now,
        "review.decision": "approved",
        "review.notes": notes,
        "status": "approved",
        "updated_at": now,
    }
    if corrections:
        review_update["review.corrections"] = corrections

    await db.legacy_imports.update_one(
        {"id": import_id},
        {"$set": review_update},
    )

    await audit_log(
        db,
        import_id=import_id,
        batch_id=doc.get("batch_id"),
        actor_user_id=approver_id,
        actor_name=approver_name,
        actor_role=approver_role,
        action="approved",
        before={"status": doc["status"]},
        after={
            "status": "approved",
            "corrections": corrections or {},
            "admin_override_self_approval": (
                bool(admin_override_self_approval)
                and approver_id in uploader_ids
            ),
        },
    )

    # Phase A: no per-doc-type promoter activated yet.
    promoter = ACTIVE_PROMOTERS.get(doc["document_type"])
    if promoter is None:
        logger.info(
            f"[legacy-imports] {import_id} approved (status=approved); "
            f"document_type={doc['document_type']!r} has no active promoter — "
            f"awaiting Phase B activation. Promotion deferred."
        )
    else:
        # Phase B will land here. Promoter contract:
        #   promoter(db, import_doc) -> {"collection": str, "record_id": str}
        try:
            promoted = await promoter(db, doc)
            await db.legacy_imports.update_one(
                {"id": import_id},
                {"$set": {
                    "promotion": {
                        "promoted": True,
                        "promoted_to_collection": promoted["collection"],
                        "promoted_record_id": promoted["record_id"],
                        "promoted_at": datetime.now(timezone.utc).isoformat(),
                    },
                    "status": "promoted",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            await audit_log(
                db,
                import_id=import_id,
                batch_id=doc.get("batch_id"),
                actor_user_id=approver_id,
                actor_name=approver_name,
                actor_role=approver_role,
                action="promoted",
                after={"collection": promoted["collection"], "record_id": promoted["record_id"]},
            )
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[legacy-imports] promotion failed for {import_id}: {e}")
            # Stay in "approved" — reviewer can retry via admin retry endpoint (Phase B).

    return await db.legacy_imports.find_one({"id": import_id}, {"_id": 0})


async def reject_import(
    db,
    *,
    import_id: str,
    reviewer_id: str,
    reviewer_name: str,
    reviewer_role: str,
    reason: str,
    notes: str = "",
) -> Dict[str, Any]:
    doc = await db.legacy_imports.find_one({"id": import_id}, {"_id": 0})
    if not doc:
        raise ApprovalError("import not found")
    if not can_transition(doc["status"], "rejected"):
        raise ApprovalError(f"cannot reject from status={doc['status']!r}")

    now = datetime.now(timezone.utc).isoformat()
    await db.legacy_imports.update_one(
        {"id": import_id},
        {"$set": {
            "status": "rejected",
            "review.reviewer_user_id": reviewer_id,
            "review.reviewer_name": reviewer_name,
            "review.reviewed_at": now,
            "review.decision": "rejected",
            "review.reject_reason": reason,
            "review.notes": notes,
            "updated_at": now,
        }},
    )
    await audit_log(
        db,
        import_id=import_id,
        batch_id=doc.get("batch_id"),
        actor_user_id=reviewer_id,
        actor_name=reviewer_name,
        actor_role=reviewer_role,
        action="rejected",
        before={"status": doc["status"]},
        after={"reason": reason},
    )
    return await db.legacy_imports.find_one({"id": import_id}, {"_id": 0})


# ── Hash + R2 helpers (thin) ───────────────────────────────────────────
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
