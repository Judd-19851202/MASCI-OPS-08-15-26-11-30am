"""
routes/document_expirations.py — Iter151 (Phase 2.5) · Phase B.

DOCUMENT EXPIRATION ENGINE.

Tracks expiration dates across:
  * Employees   — OSHA cards · TWIC · CDL medical · DL · operator certs
  * Safety      — competent-person docs · fall-protection · CPR/First Aid
  * Equipment   — registrations · annual inspections · insurance · calibration
  * Company     — insurance certificates · licenses · permits · compliance

NOT a replacement for:
  * db.safety_training_records (existing) — those still own training rows.
  * db.fire_extinguishers (existing)        — those still own inspections.

INTEGRATION: when a document crosses a warning threshold (60/30/14/7d
or expires), the scanner uses task_service + notification_service from
Iter150 Phase A to emit accountability and awareness signals — NO
duplicate notification/task plumbing here.

ROLE-AWARE VIEWS:
  admin    → everything
  hr       → category in {employee, training_cert}
  safety   → category in {safety, training_cert, employee} read-only
  shop     → category in {equipment}
  pm       → category in {project, company} (read-only)
"""
from __future__ import annotations

from lib.mongo_query import safe_regex
from lib.kpi_expiry import expiry_status

import logging
import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from lib.enterprise_governance import (
    build_governance_actor_context,
    require_governed_action,
)

logger = logging.getLogger(__name__)

# Closed-set enums
ALLOWED_CATEGORIES = {"employee", "safety", "equipment", "company",
                      "training_cert", "project"}
ALLOWED_STATUSES = {"Current", "Expiring Soon", "Expired",
                    "Archived", "Not Applicable"}

# Warning thresholds (days until expiration). Order matters — descending.
WARN_THRESHOLDS = [60, 30, 14, 7]


# ──────────────────────────────────────────────────────────────────
# Pydantic
# ──────────────────────────────────────────────────────────────────
class DocExpirationCreate(BaseModel):
    document_type: str = Field(..., min_length=2, max_length=80)
    category: str = Field(..., max_length=24)
    title: Optional[str] = Field(default=None, max_length=160)
    linked_employee_id: Optional[str] = Field(default=None, max_length=64)
    linked_equipment_id: Optional[str] = Field(default=None, max_length=64)
    linked_project_number: Optional[str] = Field(default=None, max_length=64)
    issue_date: Optional[date] = None
    expiration_date: date
    renewal_required: bool = True
    notes: Optional[str] = Field(default=None, max_length=2000)
    file_url: Optional[str] = Field(default=None, max_length=512)

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(ALLOWED_CATEGORIES)}")
        return v


class DocExpirationPatch(BaseModel):
    document_type: Optional[str] = None
    title: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    renewal_required: Optional[bool] = None
    notes: Optional[str] = None
    file_url: Optional[str] = None
    status: Optional[str] = None


def compute_status(exp_date: Optional[date]) -> str:
    # PC/EXPIRY canonical (Wave 5): governed UTC boundary, missing -> Not Applicable.
    return expiry_status(exp_date, horizon_days=max(WARN_THRESHOLDS))


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce dates to ISO strings + drop _id (for JSON-safe response)."""
    if not doc:
        return doc
    out = dict(doc)
    out.pop("_id", None)
    for k in ("issue_date", "expiration_date"):
        if isinstance(out.get(k), date) and not isinstance(out.get(k), datetime):
            out[k] = out[k].isoformat()
    return out


# ──────────────────────────────────────────────────────────────────
# Threshold scanner
# ──────────────────────────────────────────────────────────────────
async def scan_thresholds(db, dry_run: bool = False) -> Dict[str, Any]:
    """Walk every non-archived expiration. For each unfired threshold
    that the document has now crossed, emit one task + one notification
    (idempotent — fires_at_threshold list prevents duplicates).

    Returns: {'scanned': N, 'fired': [{doc_id, threshold, action}], 'dry_run': bool}
    """
    from routes.tasks_notifications import task_service, notification_service  # noqa: PLC0415
    today = datetime.now(timezone.utc).date()
    fired: List[Dict[str, Any]] = []
    scanned = 0

    cur = db.document_expirations.find(
        {"status": {"$nin": ["Archived", "Not Applicable"]}},
        {"_id": 0},
    )
    async for d in cur:
        scanned += 1
        exp_raw = d.get("expiration_date")
        if not exp_raw:
            continue
        if isinstance(exp_raw, str):
            try:
                exp_date = date.fromisoformat(exp_raw[:10])
            except Exception:
                continue
        elif isinstance(exp_raw, datetime):
            exp_date = exp_raw.date()
        else:
            exp_date = exp_raw

        days_until = (exp_date - today).days
        already_fired: List[int] = list(d.get("fires_at_threshold", []))
        prev_status = d.get("status", "Current")
        new_status = compute_status(exp_date)

        # Choose threshold buckets to fire. "expired" = -1 sentinel.
        # Rule: fire the SMALLEST (most urgent) applicable threshold and
        # mark larger ones already-fired so a doc that jumps from 65d to
        # 5d in a single scan only emits ONE "7-day warning" instead of
        # four noisy ones (60d, 30d, 14d, 7d).
        targets: List[int] = []
        already_marked: List[int] = []
        if days_until < 0 and -1 not in already_fired:
            targets.append(-1)
            # Suppress any prior warning thresholds the doc skipped over.
            for thr in WARN_THRESHOLDS:
                if thr not in already_fired:
                    already_marked.append(thr)
        else:
            # Sort ascending so we test 7→14→30→60. Stop at the first hit.
            for thr in sorted(WARN_THRESHOLDS):
                if 0 <= days_until <= thr and thr not in already_fired:
                    targets.append(thr)
                    # Mark all LARGER thresholds as also-fired so they
                    # don't re-fire on later scans.
                    for larger in WARN_THRESHOLDS:
                        if larger > thr and larger not in already_fired:
                            already_marked.append(larger)
                    break

        if not targets and new_status == prev_status:
            continue

        # Fire each target
        for thr in targets:
            label = "Expired" if thr == -1 else f"Expiring in ≤{thr} days"
            sev = "Critical" if thr == -1 else (
                "Warning" if thr <= 14 else "Info")
            priority = "Critical" if thr == -1 else (
                "High" if thr <= 14 else "Medium")

            # Choose assignee role from category
            cat = d.get("category", "company")
            role = {
                "employee": "hr", "training_cert": "hr",
                "safety": "safety", "equipment": "shop",
                "project": "pm", "company": "admin",
            }.get(cat, "admin")

            payload_task = {
                "title": f"{label}: {d.get('document_type', 'document')}"
                         + (f" — {d.get('title','')[:60]}" if d.get("title") else ""),
                "description": (
                    f"Document {d.get('document_type','')} for "
                    f"{d.get('linked_employee_id') or d.get('linked_equipment_id') or 'company'} "
                    f"is {label.lower()} (expiration={exp_date.isoformat()})."
                )[:2000],
                "source_module": "documents.expiration",
                "source_record_id": d.get("id"),
                "linked_employee_id": d.get("linked_employee_id"),
                "linked_equipment_id": d.get("linked_equipment_id"),
                "linked_project_number": d.get("linked_project_number"),
                "assignee_role": role,
                "priority": priority,
                "due_at": (
                    datetime.combine(exp_date, datetime.min.time(),
                                     tzinfo=timezone.utc)
                    if thr != -1 else
                    datetime.now(timezone.utc)
                ),
                "created_by": {"role": "system",
                               "name": "Document Expiration Scanner"},
            }
            payload_notif = {
                "type": "document.expired" if thr == -1
                else "document.expiring",
                "title": payload_task["title"],
                "message": payload_task["description"][:200],
                "severity": sev,
                "recipient_role": role,
                "linked_source_module": "documents.expiration",
                "linked_source_record_id": d.get("id"),
                "linked_employee_id": d.get("linked_employee_id"),
                "linked_equipment_id": d.get("linked_equipment_id"),
                "linked_project_number": d.get("linked_project_number"),
            }

            if not dry_run:
                try:
                    task_id = await task_service.create(db, payload_task)
                except Exception as e:  # pragma: no cover
                    logger.warning("expiration task create failed: %s", e)
                    task_id = None
                try:
                    await notification_service.fanout(db, payload_notif)
                except Exception as e:  # pragma: no cover
                    logger.warning("expiration notification failed: %s", e)
                # Iter160 · Operational signal — doc threshold fire.
                try:
                    from lib.operational_signals import record_signal  # noqa: PLC0415
                    await record_signal(
                        db, signal="doc.threshold_fired",
                        module="documents.expiration",
                        dims={"threshold": int(thr),
                              "category": (d.get("category") or "")[:24]},
                    )
                except Exception:
                    pass
                # Mark threshold fired
                await db.document_expirations.update_one(
                    {"id": d["id"]},
                    {
                        "$push": {"fires_at_threshold": {
                            "$each": [thr, *already_marked],
                        }},
                        "$set": {
                            "status": new_status,
                            "last_scanned_at": datetime.now(timezone.utc),
                            "linked_task_ids": (
                                (d.get("linked_task_ids") or []) + ([task_id] if task_id else [])
                            ),
                        },
                    },
                )

            fired.append({
                "doc_id": d.get("id"),
                "threshold": thr,
                "label": label,
                "role": role,
                "action": "would-fire" if dry_run else "fired",
            })

        # Status drift only (no threshold crossed) — quietly update.
        if not targets and new_status != prev_status and not dry_run:
            await db.document_expirations.update_one(
                {"id": d["id"]},
                {"$set": {
                    "status": new_status,
                    "last_scanned_at": datetime.now(timezone.utc),
                }},
            )

    return {"scanned": scanned, "fired": fired, "dry_run": dry_run,
            "at": datetime.now(timezone.utc).isoformat()}


async def ensure_document_expirations_indexes(db) -> None:
    try:
        await db.document_expirations.create_index("id", unique=True)
        await db.document_expirations.create_index("category")
        await db.document_expirations.create_index("status")
        await db.document_expirations.create_index("expiration_date")
        await db.document_expirations.create_index("linked_employee_id")
        await db.document_expirations.create_index("linked_equipment_id")
        await db.document_expirations.create_index("linked_project_number")
    except Exception as e:  # pragma: no cover
        logger.warning("document_expirations index bootstrap failed: %s", e)


# ──────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────
def build_document_expirations_router(db, require_any_portal_token, require_admin):
    router = APIRouter(tags=["document-expirations"])

    def _governed_actor(actor: Dict[str, Any]) -> Dict[str, Any]:
        raw = dict(actor or {})
        role = str(raw.get("_actor") or raw.get("role") or "").strip().lower()
        role = {
            "leadership": "executive",
            "dispatcher": "dispatch",
            "project manager": "pm",
            "shop manager": "shop",
            "safety": "safety",
            "hr": "hr",
            "admin": "admin",
        }.get(role, role)
        raw.setdefault("id", raw.get("user_id") or raw.get("email") or role or "document-expirations")
        raw.setdefault("email", f"{role or 'operator'}@document-expirations.local")
        raw["_actor"] = role or "admin"
        raw["role"] = role or "admin"
        return raw

    async def _read_scope(actor: Dict[str, Any]) -> Dict[str, Any]:
        governed_actor = _governed_actor(actor)
        context = await build_governance_actor_context(db, governed_actor)
        # Global-authority actors (system admin / executive / cross-project portals)
        # see every category. The governance context surfaces this as
        # governance_scope_mode == "global" (see enterprise_governance._is_cross_project_actor).
        if context.get("governance_scope_mode") == "global":
            return {}
        # Category-scoped actors: read permissions come from direct + delegated permissions.
        perms = set(context.get("direct_permissions") or []) | set(context.get("delegated_permissions") or [])
        category_map = {
            "employee": "document_expirations.read.employee",
            "training_cert": "document_expirations.read.training_cert",
            "safety": "document_expirations.read.safety",
            "equipment": "document_expirations.read.equipment",
            "project": "document_expirations.read.project",
            "company": "document_expirations.read.company",
        }
        cats = [category for category, perm in category_map.items() if perm in perms]
        if not cats:
            return {"_unreachable": True}
        return {"category": {"$in": cats}}

    async def _require_doc_expiration_access(
        *,
        actor: Dict[str, Any],
        request: Request,
        action_key: str,
        resource: Optional[Dict[str, Any]] = None,
    ) -> None:
        await require_governed_action(
            db,
            actor=_governed_actor(actor),
            action_key=action_key,
            resource_type="document_expiration",
            resource=resource or {"id": "document-expirations", "project_number": ""},
            requested_context={"module": "document_expirations"},
            request=request,
        )

    @router.get("/api/document-expirations")
    async def list_expirations(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None),
        linked_employee_id: Optional[str] = Query(default=None),
        linked_equipment_id: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        await _require_doc_expiration_access(
            actor=actor,
            request=request,
            action_key="document_expirations.read",
        )
        filt = await _read_scope(actor)
        if filt.get("_unreachable"):
            return {"items": [], "count": 0}
        clauses: List[Dict[str, Any]] = []
        if filt:
            clauses.append(filt)
        if status:
            clauses.append({"status": status})
        if category:
            clauses.append({"category": category})
        if linked_employee_id:
            clauses.append({"linked_employee_id": linked_employee_id})
        if linked_equipment_id:
            clauses.append({"linked_equipment_id": linked_equipment_id})
        if q:
            clauses.append({"$or": [
                {"document_type": safe_regex(q)},
                {"title": safe_regex(q)},
            ]})
        final = {"$and": clauses} if clauses else {}
        cur = db.document_expirations.find(final, {"_id": 0}).sort(
            "expiration_date", 1).limit(limit)
        items = [_serialize(d) async for d in cur]
        return {"items": items, "count": len(items)}

    @router.get("/api/document-expirations/summary")
    async def summary(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _require_doc_expiration_access(
            actor=actor,
            request=request,
            action_key="document_expirations.read",
        )
        filt = await _read_scope(actor)
        if filt.get("_unreachable"):
            return {"by_status": {}, "expiring_30d": 0, "expired": 0}
        today = datetime.now(timezone.utc).date()
        match = filt or {}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        by_status = {}
        async for d in db.document_expirations.aggregate(pipeline):
            by_status[d["_id"] or "Current"] = d["count"]
        # 30d window expiring
        match30 = {**match, "expiration_date": {
            "$gte": today.isoformat(),
            "$lte": (today + timedelta(days=30)).isoformat(),
        }, "status": {"$nin": ["Archived", "Not Applicable", "Expired"]}}
        # NOTE: dates stored as ISO strings so a lexicographic compare works.
        expiring_30d = await db.document_expirations.count_documents(match30)
        expired = await db.document_expirations.count_documents({
            **match, "status": "Expired",
        })
        return {"by_status": by_status, "expiring_30d": expiring_30d,
                "expired": expired}

    @router.post("/api/document-expirations")
    async def create_expiration(
        body: DocExpirationCreate,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _require_doc_expiration_access(
            actor=actor,
            request=request,
            action_key="document_expirations.manage",
            resource={
                "id": body.linked_project_number or body.linked_employee_id or body.linked_equipment_id or "document-expirations",
                "project_number": body.linked_project_number or "",
                "category": body.category,
            },
        )
        now = datetime.now(timezone.utc)
        role = _governed_actor(actor).get("role") or "admin"
        doc = {
            "id": str(uuid.uuid4()),
            "document_type": body.document_type.strip(),
            "category": body.category,
            "title": (body.title or "").strip() or None,
            "linked_employee_id": body.linked_employee_id,
            "linked_equipment_id": body.linked_equipment_id,
            "linked_project_number": body.linked_project_number,
            "issue_date": body.issue_date.isoformat() if body.issue_date else None,
            "expiration_date": body.expiration_date.isoformat(),
            "renewal_required": body.renewal_required,
            "notes": (body.notes or "").strip() or None,
            "file_url": body.file_url,
            "status": compute_status(body.expiration_date),
            "fires_at_threshold": [],
            "linked_task_ids": [],
            "created_at": now,
            "updated_at": now,
            "created_by": {"role": role,
                           "name": actor.get("name") or actor.get("email")},
            "last_scanned_at": None,
        }
        await db.document_expirations.insert_one(doc)
        return _serialize(doc)

    @router.patch("/api/document-expirations/{doc_id}")
    async def patch_expiration(
        doc_id: str,
        body: DocExpirationPatch,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.document_expirations.find_one(
            {"id": doc_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        await _require_doc_expiration_access(
            actor=actor,
            request=request,
            action_key="document_expirations.manage",
            resource={
                "id": doc_id,
                "project_number": existing.get("linked_project_number") or "",
                "category": existing.get("category") or "",
            },
        )
        update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        for k, v in body.model_dump(exclude_none=True).items():
            if k in ("issue_date", "expiration_date") and isinstance(v, date):
                update[k] = v.isoformat()
            elif k == "status" and v in ALLOWED_STATUSES:
                update[k] = v
            elif k == "status":
                continue
            else:
                update[k] = v
        # If expiration_date changed → reset fires_at_threshold so the
        # scanner can fire fresh warnings for the new date.
        if "expiration_date" in update and update["expiration_date"] != existing.get("expiration_date"):
            update["fires_at_threshold"] = []
            try:
                new_date = date.fromisoformat(update["expiration_date"])
                update["status"] = compute_status(new_date)
            except Exception:
                pass
        await db.document_expirations.update_one(
            {"id": doc_id}, {"$set": update})
        doc = await db.document_expirations.find_one(
            {"id": doc_id}, {"_id": 0})
        return _serialize(doc)

    @router.delete("/api/document-expirations/{doc_id}")
    async def archive_expiration(
        doc_id: str,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.document_expirations.find_one({"id": doc_id}, {"_id": 0})
        await _require_doc_expiration_access(
            actor=actor,
            request=request,
            action_key="document_expirations.manage",
            resource={
                "id": doc_id,
                "project_number": (existing or {}).get("linked_project_number") or "",
                "category": (existing or {}).get("category") or "",
            },
        )
        role = _governed_actor(actor).get("role") or "admin"
        await db.document_expirations.update_one(
            {"id": doc_id},
            {"$set": {
                "status": "Archived",
                "updated_at": datetime.now(timezone.utc),
                "archived_by": {"role": role,
                                "name": actor.get("name") or actor.get("email")},
            }},
        )
        return {"ok": True}

    # ── Admin-only scanner controls ────────────────────────────────
    @router.post("/api/admin/document-expirations/scan",
                 dependencies=[Depends(require_admin)])
    async def admin_scan(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
        return await scan_thresholds(db, dry_run=False)

    @router.get("/api/admin/document-expirations/scan/preview",
                dependencies=[Depends(require_admin)])
    async def admin_scan_preview() -> Dict[str, Any]:
        """Dry-run — returns what WOULD fire without writing anything."""
        return await scan_thresholds(db, dry_run=True)

    return router


__all__ = [
    "build_document_expirations_router",
    "ensure_document_expirations_indexes",
    "scan_thresholds",
    "WARN_THRESHOLDS",
    "ALLOWED_CATEGORIES",
    "ALLOWED_STATUSES",
]
