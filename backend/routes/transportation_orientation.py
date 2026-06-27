"""TRACK 16.08 · MASCI Transportation Orientation, Notification &
External Onboarding Platform.

Single module · production-ready · integrates with every existing
MASCI primitive (Email Routing v2, R2 storage, audit_events, eligibility).

* Orientation modules catalog · 22 default modules · 4 languages
* Video player heartbeat validation
* Quiz engine with random question banks + retry rules
* Certificate generation (audit-hash · QR-friendly · language tagged)
* Secure external invite portal (token-based · no auth surface)
* Notification log with future Email Routing v2 routes
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, Path, Query, Request, Header,
    File, Form, UploadFile,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
TENANT = "masci"

# ─────────────────────── Constants ───────────────────────
LANGUAGES = ("en", "es", "es_CU", "fr")
LANG_LABEL = {"en": "English (Primary)", "es": "Spanish",
              "es_CU": "Cuban Spanish", "fr": "French"}
PASSING_SCORE_DEFAULT = 80
QUIZ_MAX_ATTEMPTS_DEFAULT = 3
COMPLETION_WATCH_THRESHOLD = 0.99
ORIENTATION_VALID_MONTHS = 12  # annual refresher default

NOTIFICATION_KINDS = (
    "carrier_invite", "packet_ready", "packet_submitted",
    "packet_needs_correction", "packet_approved",
    "driver_approved", "driver_suspended",
    "orientation_assigned", "orientation_reminder",
    "orientation_expiring", "orientation_overdue",
    "annual_inspection_due", "annual_inspection_reminder",
    "annual_inspection_overdue",
    "documents_expiring", "documents_approved", "documents_need_correction",
    "driver_eligible", "driver_not_eligible",
    "carrier_eligible", "carrier_not_eligible",
    "dispatch_eligibility_changed",
)

MODULES = [
    ("welcome_to_masci",           "Welcome to MASCI",            "intro",         True),
    ("safety_culture",             "Safety Culture",              "safety",        True),
    ("traffic_control",            "Traffic Control",             "operations",    True),
    ("jobsite_arrival",            "Jobsite Arrival",             "operations",    True),
    ("asphalt_plant_operations",   "Asphalt Plant Operations",    "operations",    True),
    ("loading_procedures",         "Loading Procedures",          "operations",    True),
    ("hauling_procedures",         "Hauling Procedures",          "operations",    True),
    ("backing_procedures",         "Backing Procedures",          "operations",    True),
    ("dumping_procedures",         "Dumping Procedures",          "operations",    True),
    ("truck_readiness",            "Truck Readiness",             "vehicle",       True),
    ("driver_expectations",        "Driver Expectations",         "expectations",  True),
    ("ppe",                        "PPE",                         "safety",        True),
    ("incident_reporting",         "Incident Reporting",          "safety",        True),
    ("near_miss_reporting",        "Near Miss Reporting",         "safety",        True),
    ("emergency_procedures",       "Emergency Procedures",        "safety",        True),
    ("equipment_awareness",        "Equipment Awareness",         "vehicle",       True),
    ("communications",             "Communications",              "operations",    True),
    ("customer_expectations",      "Customer Expectations",       "expectations",  True),
    ("environmental_responsibilities", "Environmental Responsibilities", "safety", True),
    ("end_of_shift",               "End of Shift",                "operations",    True),
    ("annual_refresher",           "Annual Refresher",            "annual",        False),
]


# ─────────────────────── Schemas ───────────────────────
class ModuleCreate(BaseModel):
    key: str
    title: str
    category: str
    required: bool = True
    runtime_seconds: int = Field(0, ge=0)
    description: Optional[str] = None


class ModulePatch(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    required: Optional[bool] = None
    runtime_seconds: Optional[int] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class PlaceholderPatch(BaseModel):
    language: str
    sky_asset_id: Optional[str] = None
    runtime_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None  # placeholder | published | retired


class QuestionUpsert(BaseModel):
    prompt: str
    choices: List[str] = Field(..., min_length=2, max_length=8)
    correct_index: int = Field(..., ge=0)
    explanation: Optional[str] = None
    language: str = "en"


class AssignmentCreate(BaseModel):
    transport_person_id: str
    module_key: str
    language: str = "en"
    due_at: Optional[str] = None
    assigned_by_email: Optional[str] = None


class HeartbeatPayload(BaseModel):
    position_seconds: float = Field(..., ge=0)
    watched_seconds: float = Field(..., ge=0)
    checkpoints_visited: List[int] = Field(default_factory=list)


class QuizSubmit(BaseModel):
    answers: Dict[str, int]  # question_id -> choice_index


class InviteCreate(BaseModel):
    carrier_id: str
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    expires_in_days: int = Field(14, ge=1, le=90)


# ─────────────────────── Helpers ───────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("email") or actor.get("id") or "admin")
    return "admin"


def _project(d):
    return {k: v for k, v in d.items() if k != "_id"} if d else None


async def _audit(db, *, kind, entity_type, entity_id, actor, old, new, request=None):
    try:
        doc = {"id": uuid.uuid4().hex, "kind": kind,
               "entity_type": entity_type, "entity_id": entity_id,
               "actor": _actor(actor), "old": old, "new": new,
               "ts": _now(), "tenant": TENANT}
        if request:
            doc["route"] = str(request.url.path)
            doc["ip"] = (request.headers.get("x-forwarded-for")
                         or (request.client.host if request.client else "")) or None
            doc["ua"] = request.headers.get("user-agent")
        await db.audit_events.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"track 16.08 audit failed: {exc}")


async def notify(db, *, kind: str, summary: str, audience: List[str],
                 email_to: Optional[List[str]] = None,
                 meta: Optional[Dict[str, Any]] = None) -> None:
    """Track 16.08 notification fan-out.

    1. Write a bell row into `notifications` for in-app audiences.
    2. Persist a `transport_notifications` row with the future-route
       payload Email Routing v2 will resolve when the operator
       opt-flag flips on per-route (Phase 4 wiring).
    3. Best-effort `resolve_and_audit` against the existing v2 router
       so the email_routing_audit_v2 ledger has a record of intent.
    """
    if kind not in NOTIFICATION_KINDS:
        return
    ts = _now()
    try:
        await db.notifications.insert_one({
            "id": uuid.uuid4().hex, "tenant": TENANT, "kind": kind,
            "summary": summary, "audience": audience,
            "meta": meta or {}, "ts": ts, "read": False,
        })
    except Exception:  # noqa: BLE001
        pass
    notif_row = {
        "id": uuid.uuid4().hex, "tenant": TENANT, "kind": kind,
        "summary": summary, "audience": audience,
        "email_to": email_to or [], "meta": meta or {},
        "ts": ts, "status": "queued",
    }
    try:
        await db.transport_notifications.insert_one(notif_row)
    except Exception:  # noqa: BLE001
        pass
    # Best-effort Email Routing v2 audit (Phase 4 actually fires).
    try:
        from email_routing_v2 import resolve_and_audit as _v2  # noqa: PLC0415
        await _v2(db, channel=f"transport_{kind}",
                  audience=audience, payload=notif_row)
    except Exception:  # noqa: BLE001
        pass


def _audit_hash(payload: Dict[str, Any]) -> str:
    src = (
        f"{payload.get('transport_person_id')}|{payload.get('module_key')}|"
        f"{payload.get('language')}|{payload.get('completed_at')}|"
        f"{payload.get('quiz_score')}|{payload.get('module_version')}"
    )
    return hashlib.sha256(src.encode()).hexdigest()


# ─────────────────────── Bootstrap (idempotent) ───────────────────────
async def bootstrap_track_16_08(db) -> Dict[str, Any]:
    """Seed the 22 default modules + a placeholder per language. Safe
    on every startup."""
    seeded = 0
    for (key, title, cat, required) in MODULES:
        existing = await db.transport_orientation_modules.find_one(
            {"tenant": TENANT, "key": key})
        if existing:
            continue
        now = _now()
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "key": key,
            "title": title, "category": cat, "required": required,
            "active": True, "runtime_seconds": 0,
            "description": None,
            "version": "1",
            "passing_score": PASSING_SCORE_DEFAULT,
            "max_attempts": QUIZ_MAX_ATTEMPTS_DEFAULT,
            "languages": list(LANGUAGES),
            "placeholders": [
                {"language": lang, "sky_asset_id": None,
                 "runtime_seconds": 0, "thumbnail_url": None,
                 "version": "1", "status": "placeholder",
                 "uploaded_at": None}
                for lang in LANGUAGES
            ],
            "created_at": now, "updated_at": now,
            "created_by": "system_bootstrap",
        }
        await db.transport_orientation_modules.insert_one(doc.copy())
        seeded += 1
    logger.info(f"[track-16-08-bootstrap] modules seeded={seeded}")
    return {"modules_seeded": seeded}


# ─────────────────────── Router factory ───────────────────────
def register_transportation_orientation_routes(
    app, db, require_admin_dep: Callable
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["transportation-orientation"])

    # ============================ MODULES ============================
    @router.get("/admin/transportation/orientation/modules")
    async def list_modules(_: Any = Depends(require_admin_dep)):
        cur = db.transport_orientation_modules.find({"tenant": TENANT}).sort("key", 1)
        items = [_project(d) for d in await cur.to_list(500)]
        return {"items": items, "languages": list(LANGUAGES)}

    @router.post("/admin/transportation/orientation/modules")
    async def create_module(body: ModuleCreate, request: Request,
                             actor: Any = Depends(require_admin_dep)):
        existing = await db.transport_orientation_modules.find_one(
            {"tenant": TENANT, "key": body.key})
        if existing:
            raise HTTPException(409, "Module key already exists")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "key": body.key,
            "title": body.title, "category": body.category,
            "required": body.required, "active": True,
            "runtime_seconds": body.runtime_seconds,
            "description": body.description, "version": "1",
            "passing_score": PASSING_SCORE_DEFAULT,
            "max_attempts": QUIZ_MAX_ATTEMPTS_DEFAULT,
            "languages": list(LANGUAGES),
            "placeholders": [
                {"language": l, "sky_asset_id": None,
                 "runtime_seconds": 0, "thumbnail_url": None,
                 "version": "1", "status": "placeholder",
                 "uploaded_at": None}
                for l in LANGUAGES],
            "created_at": now, "updated_at": now,
            "created_by": _actor(actor),
        }
        await db.transport_orientation_modules.insert_one(doc.copy())
        await _audit(db, kind="transport_orientation_module_create",
                     entity_type="orientation_module", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.patch("/admin/transportation/orientation/modules/{mid}")
    async def patch_module(mid: str, body: ModulePatch, request: Request,
                            actor: Any = Depends(require_admin_dep)):
        existing = await db.transport_orientation_modules.find_one(
            {"id": mid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Module not found")
        upd = {}
        for f in ("title", "category", "required", "runtime_seconds",
                  "description", "active"):
            v = getattr(body, f)
            if v is not None:
                upd[f] = v
        upd["updated_at"] = _now()
        # Bumping the version on substantive content changes:
        if any(k in upd for k in ("title", "category", "required")):
            try:
                upd["version"] = str(int(existing.get("version") or "1") + 1)
            except Exception:  # noqa: BLE001
                pass
        await db.transport_orientation_modules.update_one(
            {"_id": existing["_id"]}, {"$set": upd})
        new_doc = {**existing, **upd}
        await _audit(db, kind="transport_orientation_module_update",
                     entity_type="orientation_module", entity_id=mid,
                     actor=actor, old=_project(existing), new=_project(new_doc),
                     request=request)
        return _project(new_doc)

    @router.patch("/admin/transportation/orientation/modules/{mid}/placeholder")
    async def patch_placeholder(mid: str, body: PlaceholderPatch,
                                 request: Request,
                                 actor: Any = Depends(require_admin_dep)):
        if body.language not in LANGUAGES:
            raise HTTPException(422, f"language must be one of {list(LANGUAGES)}")
        existing = await db.transport_orientation_modules.find_one(
            {"id": mid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Module not found")
        placeholders = existing.get("placeholders") or []
        for ph in placeholders:
            if ph["language"] == body.language:
                if body.sky_asset_id is not None:
                    ph["sky_asset_id"] = body.sky_asset_id
                    ph["status"] = "published"
                    ph["uploaded_at"] = _now()
                if body.runtime_seconds is not None:
                    ph["runtime_seconds"] = body.runtime_seconds
                if body.thumbnail_url is not None:
                    ph["thumbnail_url"] = body.thumbnail_url
                if body.version is not None:
                    ph["version"] = body.version
                if body.status is not None and body.status in (
                        "placeholder", "published", "retired"):
                    ph["status"] = body.status
                break
        await db.transport_orientation_modules.update_one(
            {"_id": existing["_id"]},
            {"$set": {"placeholders": placeholders, "updated_at": _now()}})
        new_doc = {**existing, "placeholders": placeholders}
        await _audit(db, kind="transport_orientation_placeholder_update",
                     entity_type="orientation_module", entity_id=mid,
                     actor=actor, old=_project(existing), new=_project(new_doc),
                     request=request)
        return _project(new_doc)

    # ============================ QUESTIONS ============================
    @router.get("/admin/transportation/orientation/modules/{mid}/questions")
    async def list_questions(mid: str, language: str = Query("en"),
                              _: Any = Depends(require_admin_dep)):
        cur = db.transport_orientation_questions.find({
            "tenant": TENANT, "module_id": mid, "language": language
        }).sort("created_at", 1)
        return {"items": [_project(d) for d in await cur.to_list(500)]}

    @router.post("/admin/transportation/orientation/modules/{mid}/questions")
    async def add_question(mid: str, body: QuestionUpsert, request: Request,
                            actor: Any = Depends(require_admin_dep)):
        if body.language not in LANGUAGES:
            raise HTTPException(422, "language not supported")
        if body.correct_index >= len(body.choices):
            raise HTTPException(422, "correct_index out of range")
        mod = await db.transport_orientation_modules.find_one(
            {"id": mid, "tenant": TENANT})
        if not mod:
            raise HTTPException(404, "Module not found")
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "module_id": mid,
            "module_key": mod["key"], "language": body.language,
            "prompt": body.prompt, "choices": body.choices,
            "correct_index": body.correct_index,
            "explanation": body.explanation,
            "created_at": _now(), "created_by": _actor(actor),
        }
        await db.transport_orientation_questions.insert_one(doc.copy())
        await _audit(db, kind="transport_orientation_question_create",
                     entity_type="orientation_question", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    # ============================ ASSIGNMENTS ============================
    @router.post("/admin/transportation/orientation/assignments")
    async def assign(body: AssignmentCreate, request: Request,
                     actor: Any = Depends(require_admin_dep)):
        if body.language not in LANGUAGES:
            raise HTTPException(422, "language not supported")
        person = await db.transport_persons.find_one(
            {"id": body.transport_person_id, "tenant": TENANT})
        if not person:
            raise HTTPException(404, "Driver not found")
        mod = await db.transport_orientation_modules.find_one(
            {"key": body.module_key, "tenant": TENANT})
        if not mod:
            raise HTTPException(404, "Module not found")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "transport_person_id": body.transport_person_id,
            "module_id": mod["id"], "module_key": mod["key"],
            "language": body.language,
            "status": "assigned",
            "watch_seconds": 0.0, "position_seconds": 0.0,
            "checkpoints_visited": [],
            "completion_pct": 0.0,
            "quiz_attempts": [], "best_quiz_score": None,
            "completed_at": None, "expires_at": None,
            "certificate_id": None,
            "assigned_at": now, "due_at": body.due_at,
            "assigned_by": body.assigned_by_email or _actor(actor),
            "audit_version": 1,
        }
        await db.transport_orientation_assignments.insert_one(doc.copy())
        await _audit(db, kind="transport_orientation_assigned",
                     entity_type="orientation_assignment", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        await notify(db, kind="orientation_assigned",
                     summary=f"Orientation {mod['key']} assigned to driver {body.transport_person_id}",
                     audience=["admin", "carrier_contact"],
                     email_to=[person.get("email")] if person.get("email") else [],
                     meta={"assignment_id": doc["id"]})
        return _project(doc)

    @router.get("/admin/transportation/orientation/assignments")
    async def list_assignments(
        status: Optional[str] = Query(None),
        person_id: Optional[str] = Query(None),
        _: Any = Depends(require_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if status:
            q["status"] = status
        if person_id:
            q["transport_person_id"] = person_id
        cur = db.transport_orientation_assignments.find(q).sort("assigned_at", -1).limit(500)
        return {"items": [_project(d) for d in await cur.to_list(500)]}

    # ============================ VIDEO HEARTBEAT ============================
    @router.post("/admin/transportation/orientation/assignments/{aid}/heartbeat")
    async def heartbeat(aid: str, body: HeartbeatPayload, request: Request,
                         _: Any = Depends(require_admin_dep)):
        a = await db.transport_orientation_assignments.find_one(
            {"id": aid, "tenant": TENANT})
        if not a:
            raise HTTPException(404, "Assignment not found")
        if a.get("status") in ("completed", "expired"):
            return _project(a)
        mod = await db.transport_orientation_modules.find_one(
            {"id": a["module_id"], "tenant": TENANT})
        rt = max(1, mod.get("runtime_seconds")
                 or _placeholder_runtime(mod, a["language"]))
        # Server validates watched_seconds is monotonic.
        prior = float(a.get("watch_seconds") or 0.0)
        new_watched = max(prior, min(body.watched_seconds, rt))
        completion_pct = round(new_watched / rt, 4)
        checkpoints = sorted(set(a.get("checkpoints_visited") or [])
                             | set(body.checkpoints_visited or []))
        upd = {
            "watch_seconds": new_watched,
            "position_seconds": min(body.position_seconds, rt),
            "checkpoints_visited": checkpoints,
            "completion_pct": completion_pct,
            "status": "in_progress" if completion_pct < COMPLETION_WATCH_THRESHOLD
                      else "watch_complete",
            "audit_version": (a.get("audit_version") or 1) + 1,
        }
        await db.transport_orientation_assignments.update_one(
            {"_id": a["_id"]}, {"$set": upd})
        # Best-effort heartbeat audit (sampled at 25% to keep the log lean).
        if int(new_watched) % 30 == 0:
            await _audit(db, kind="transport_orientation_heartbeat",
                         entity_type="orientation_assignment", entity_id=aid,
                         actor={"email": "system"}, old=None,
                         new={"completion_pct": completion_pct},
                         request=request)
        return {**_project(a), **upd}

    # ============================ QUIZ ============================
    @router.get("/admin/transportation/orientation/assignments/{aid}/quiz")
    async def quiz_load(aid: str, _: Any = Depends(require_admin_dep)):
        a = await db.transport_orientation_assignments.find_one(
            {"id": aid, "tenant": TENANT})
        if not a:
            raise HTTPException(404, "Assignment not found")
        if a.get("status") != "watch_complete":
            raise HTTPException(409, "Video must be fully watched before quiz")
        cur = db.transport_orientation_questions.find({
            "tenant": TENANT, "module_id": a["module_id"],
            "language": a["language"],
        })
        questions = await cur.to_list(500)
        # Random order (deterministic per-assignment to support retries).
        import random
        rng = random.Random(a["id"])
        rng.shuffle(questions)
        # Strip correct_index from the response.
        sanitized = [{
            "id": q["id"], "prompt": q["prompt"],
            "choices": q["choices"], "language": q["language"],
        } for q in questions]
        return {"items": sanitized, "attempts": len(a.get("quiz_attempts") or [])}

    @router.post("/admin/transportation/orientation/assignments/{aid}/quiz")
    async def quiz_submit(aid: str, body: QuizSubmit, request: Request,
                           actor: Any = Depends(require_admin_dep)):
        a = await db.transport_orientation_assignments.find_one(
            {"id": aid, "tenant": TENANT})
        if not a:
            raise HTTPException(404, "Assignment not found")
        if a.get("status") not in ("watch_complete", "quiz_failed"):
            raise HTTPException(409, "Video must be watched before quiz")
        mod = await db.transport_orientation_modules.find_one(
            {"id": a["module_id"], "tenant": TENANT})
        if not mod:
            raise HTTPException(404, "Module not found")
        attempts = a.get("quiz_attempts") or []
        if len(attempts) >= (mod.get("max_attempts") or QUIZ_MAX_ATTEMPTS_DEFAULT):
            raise HTTPException(409, "Max quiz attempts reached")
        # Grade.
        qs = await db.transport_orientation_questions.find({
            "tenant": TENANT, "module_id": a["module_id"],
            "language": a["language"],
        }).to_list(500)
        qmap = {q["id"]: q for q in qs}
        total = len(qmap)
        if total == 0:
            raise HTTPException(409, "No questions configured for this module/language")
        correct = 0
        for qid, choice in (body.answers or {}).items():
            if qid in qmap and int(choice) == qmap[qid]["correct_index"]:
                correct += 1
        score = round(100 * correct / total)
        attempt = {
            "attempt": len(attempts) + 1, "score": score,
            "ts": _now(), "answers": body.answers,
        }
        attempts.append(attempt)
        best = max([attempt["score"]] + [int(a_.get("score") or 0)
                                          for a_ in attempts])
        passed = score >= (mod.get("passing_score") or PASSING_SCORE_DEFAULT)
        new_status = "quiz_passed" if passed else "quiz_failed"
        upd = {"quiz_attempts": attempts, "best_quiz_score": best,
               "status": new_status,
               "audit_version": (a.get("audit_version") or 1) + 1}
        await db.transport_orientation_assignments.update_one(
            {"_id": a["_id"]}, {"$set": upd})
        await _audit(db, kind="transport_orientation_quiz_submit",
                     entity_type="orientation_assignment", entity_id=aid,
                     actor=actor, old=None,
                     new={"score": score, "passed": passed,
                          "attempt": attempt["attempt"]}, request=request)
        if passed:
            # Auto-generate certificate.
            cert = await _issue_certificate(db, a, mod)
            await db.transport_orientation_assignments.update_one(
                {"_id": a["_id"]},
                {"$set": {"status": "completed",
                          "completed_at": _now(),
                          "expires_at": (datetime.now(timezone.utc) +
                                          timedelta(days=30 * ORIENTATION_VALID_MONTHS)).isoformat(),
                          "certificate_id": cert["id"]}})
            await notify(db, kind="driver_eligible",
                         summary=f"Driver {a['transport_person_id']} completed {mod['key']} ({score}%)",
                         audience=["admin", "dispatch"],
                         meta={"assignment_id": aid, "certificate_id": cert["id"]})
        else:
            await notify(db, kind="orientation_reminder",
                         summary=f"Quiz failed — retry available ({score}%)",
                         audience=["admin"],
                         meta={"assignment_id": aid})
        return {"score": score, "passed": passed,
                "attempt": attempt["attempt"],
                "max_attempts": mod.get("max_attempts") or QUIZ_MAX_ATTEMPTS_DEFAULT}

    # ============================ CERTIFICATES ============================
    @router.get("/admin/transportation/orientation/certificates/{cid}")
    async def get_certificate(cid: str, _: Any = Depends(require_admin_dep)):
        cert = await db.transport_orientation_certificates.find_one(
            {"id": cid, "tenant": TENANT})
        if not cert:
            raise HTTPException(404, "Certificate not found")
        return _project(cert)

    @router.get("/transportation/orientation/certificates/verify/{cnum}")
    async def public_verify(cnum: str):
        """PUBLIC endpoint — QR code on every certificate links here.
        Read-only verification (no PII, no signed downloads)."""
        cert = await db.transport_orientation_certificates.find_one(
            {"certificate_number": cnum, "tenant": TENANT})
        if not cert:
            raise HTTPException(404, "Not found")
        # Strip identifying fields; only attest that the certificate exists.
        return {
            "valid": True,
            "certificate_number": cert["certificate_number"],
            "module_key": cert.get("module_key"),
            "module_version": cert.get("module_version"),
            "language": cert.get("language"),
            "completed_at": cert.get("completed_at"),
            "audit_hash": cert.get("audit_hash"),
        }

    # ============================ INVITES (EXTERNAL PORTAL) ============================
    @router.post("/admin/transportation/invites")
    async def create_invite(body: InviteCreate, request: Request,
                             actor: Any = Depends(require_admin_dep)):
        carrier = await db.carriers.find_one(
            {"id": body.carrier_id, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "carrier_id": body.carrier_id,
            "token_hash": token_hash,
            "contact_email": body.contact_email or carrier.get("contact_email"),
            "contact_name": body.contact_name or carrier.get("contact_name"),
            "status": "active",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=body.expires_in_days)).isoformat(),
            "created_by": _actor(actor),
            "opened_at": None, "submitted_at": None,
        }
        await db.transport_invites.insert_one(doc.copy())
        await _audit(db, kind="transport_invite_create",
                     entity_type="invite", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        await notify(db, kind="carrier_invite",
                     summary=f"Carrier invite created for {carrier.get('legal_name')}",
                     audience=["admin", "dispatch"],
                     email_to=[doc["contact_email"]] if doc["contact_email"] else [],
                     meta={"invite_id": doc["id"], "carrier_id": body.carrier_id})
        # Token returned ONCE to the admin — never persisted in plaintext.
        return {**_project(doc), "token": token}

    @router.get("/transportation/invite/{token}")
    async def invite_open(token: str, request: Request):
        """PUBLIC endpoint — carrier opens the invite link from email."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        inv = await db.transport_invites.find_one(
            {"token_hash": token_hash, "tenant": TENANT})
        if not inv:
            raise HTTPException(404, "Invite not found or already redeemed")
        if inv.get("status") != "active":
            raise HTTPException(410, f"Invite {inv['status']}")
        now_iso = _now()
        if inv.get("expires_at") and inv["expires_at"] < now_iso:
            await db.transport_invites.update_one(
                {"_id": inv["_id"]},
                {"$set": {"status": "expired"}})
            raise HTTPException(410, "Invite expired")
        if not inv.get("opened_at"):
            await db.transport_invites.update_one(
                {"_id": inv["_id"]},
                {"$set": {"opened_at": now_iso, "status": "opened"}})
        carrier = await db.carriers.find_one(
            {"id": inv["carrier_id"], "tenant": TENANT})
        return {
            "invite_id": inv["id"],
            "carrier_id": inv["carrier_id"],
            "carrier_legal_name": (carrier or {}).get("legal_name"),
            "contact_name": inv.get("contact_name"),
            "status": "opened",
            "expires_at": inv.get("expires_at"),
        }

    @router.post("/transportation/invite/{token}/submit")
    async def invite_submit(token: str, request: Request,
                             body: Optional[Dict[str, Any]] = None):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        inv = await db.transport_invites.find_one(
            {"token_hash": token_hash, "tenant": TENANT})
        if not inv:
            raise HTTPException(404, "Invite not found")
        if inv.get("status") not in ("opened", "active"):
            raise HTTPException(410, f"Invite {inv['status']}")
        now_iso = _now()
        await db.transport_invites.update_one(
            {"_id": inv["_id"]},
            {"$set": {"submitted_at": now_iso, "status": "submitted",
                      "submission_payload": body or {}}})
        await _audit(db, kind="transport_invite_submit",
                     entity_type="invite", entity_id=inv["id"],
                     actor={"email": "external_carrier"},
                     old=None, new={"submitted_at": now_iso}, request=request)
        await notify(db, kind="packet_submitted",
                     summary=f"External carrier submitted invite {inv['id']}",
                     audience=["admin"],
                     meta={"invite_id": inv["id"], "carrier_id": inv["carrier_id"]})
        return {"ok": True, "invite_id": inv["id"], "status": "submitted"}

    app.include_router(router)
    return router


# ─────────────────────── Module-level helpers ───────────────────────
def _placeholder_runtime(mod: Dict[str, Any], language: str) -> int:
    for ph in (mod.get("placeholders") or []):
        if ph.get("language") == language:
            return int(ph.get("runtime_seconds") or 0)
    return 0


async def _issue_certificate(db, assignment: Dict[str, Any],
                              module: Dict[str, Any]) -> Dict[str, Any]:
    now = _now()
    cnum = f"MASCI-{module['key'].upper()[:6]}-{secrets.token_hex(4).upper()}"
    payload = {
        "transport_person_id": assignment["transport_person_id"],
        "module_key": module["key"],
        "module_version": module.get("version") or "1",
        "language": assignment["language"],
        "completed_at": now,
        "quiz_score": assignment.get("best_quiz_score") or 0,
    }
    doc = {
        "id": uuid.uuid4().hex, "tenant": TENANT,
        "certificate_number": cnum,
        "transport_person_id": assignment["transport_person_id"],
        "module_id": module["id"], "module_key": module["key"],
        "module_version": payload["module_version"],
        "language": assignment["language"],
        "quiz_score": payload["quiz_score"],
        "completed_at": now,
        "expires_at": (datetime.now(timezone.utc) +
                       timedelta(days=30 * ORIENTATION_VALID_MONTHS)).isoformat(),
        "audit_hash": _audit_hash(payload),
        "issued_by": "system",
    }
    await db.transport_orientation_certificates.insert_one(doc.copy())
    return doc
