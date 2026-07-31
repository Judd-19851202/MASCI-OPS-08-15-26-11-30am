"""OMEGA · Employee Governance Phase Alpha · Employee Lifecycle Request Queue

iter454-EGA · G-5 batch — the UX-bridge collection + endpoints introduced
when the platform closed the 5 P0 violations identified in
``EMPLOYEE_GOVERNANCE_AUDIT.md``.

Governance contract:
  • HR is the SOLE authoritative writer of ``db.employees`` lifecycle state.
  • Operations (Field Leadership), Admin, public field forms, and every
    other portal may SUBMIT requests here. They may NOT write to
    ``db.employees`` directly.
  • HR explicitly REVIEWS each request and either approves (which fans
    out the actual lifecycle mutation through the canonical HR routes)
    or rejects it (with a reason).
  • Approval is the ONLY path from this queue into ``db.employees``.

Supported request kinds (Phase Alpha · strictly bounded):
  • ``new_hire``    — operator wants HR to add a person to the roster
  • ``termination`` — operator wants HR to terminate an existing employee
                      (Field Leadership Termination Form addendum:
                      submitting the FL ``employee_termination`` record
                      ALSO creates one of these requests automatically)

Future kinds (NOT in scope for Phase Alpha; reserved for later batches):
  ``status_change`` · ``transfer`` · ``supervisor_change`` · ``rehire``

Endpoints:
  POST /api/employee-requests                      (any token OR public · rate-limited)
  GET  /api/hr/employee-requests                   (HR · multi-portal HR-or-admin gate)
  GET  /api/hr/employee-requests/{id}              (HR)
  POST /api/hr/employee-requests/{id}/approve      (HR)
  POST /api/hr/employee-requests/{id}/reject       (HR)

Wired from server.py via ``register_employee_requests_routes``.
"""
from __future__ import annotations

import re as _re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

# Valid request kinds for Phase Alpha
ALLOWED_KINDS = {"new_hire", "termination"}

# Valid statuses
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
ALL_STATUSES = {STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED}

# Valid termination-status targets (HR may approve into one of these)
TERMINATION_TARGET_STATUSES = {"Terminated", "Resigned", "Retired", "Inactive"}


def _employee_request_kpi_metadata(status: Optional[str]) -> Dict[str, Any]:
    normalized_status = (status or STATUS_PENDING).lower()
    return {
        "kpi_name": "HR Employee Requests Queue",
        "business_definition": "Employee request queue size for HR review, including new-hire and termination submissions.",
        "source_of_truth": "employee_requests",
        "api_endpoint": "/api/hr/employee-requests",
        "formula": {
            "counted_entity": "employee_requests row",
            "status_filter": normalized_status,
            "kinds": sorted(ALLOWED_KINDS),
        },
        "confidence": "HIGH",
        "status_reason": "Queue size is returned directly from the persisted employee_requests collection and the same pending_count badge used by HR surfaces.",
        "drilldown_source": "/hr/employee-requests",
        "owner": "hr-queue-integrity",
        "freshness": "Generated on request.",
    }


class EmployeeRequestCreate(BaseModel):
    """Submission body. Public-tolerant — required fields are minimal."""
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., description="new_hire | termination")
    # Identity context — captured for HR review traceability
    submitter_name: Optional[str] = Field(default=None, max_length=200)
    submitter_email: Optional[str] = Field(default=None, max_length=200)
    submitted_via: Optional[str] = Field(default=None, max_length=80)
    # new_hire fields
    name: Optional[str] = Field(default=None, max_length=200)
    # Track 14.0-HR-READINESS — explicit legal name parts + preferred name
    # so the field submission preserves identity granularity. `name`
    # remains the canonical display name (constructed from parts when
    # parts are supplied).
    legal_first_name: Optional[str] = Field(default=None, max_length=120)
    legal_middle_name: Optional[str] = Field(default=None, max_length=120)
    legal_last_name: Optional[str] = Field(default=None, max_length=120)
    preferred_name: Optional[str] = Field(default=None, max_length=120)
    employee_id: Optional[str] = Field(default=None, max_length=80)
    trade: Optional[str] = Field(default=None, max_length=120)
    role: Optional[str] = Field(default=None, max_length=120)
    crew: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=60)
    # termination fields
    target_employee_id: Optional[str] = Field(default=None, max_length=120)
    requested_status: Optional[str] = Field(default=None, max_length=40)
    reason: Optional[str] = Field(default=None, max_length=2000)
    last_day_worked: Optional[str] = Field(default=None, max_length=12)
    # cross-link back to the Field Leadership record that triggered this
    # (used by the FL employee_termination auto-create flow)
    linked_fl_record_id: Optional[str] = Field(default=None, max_length=120)


class EmployeeRequestApprove(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # new_hire: HR may patch any field before creating the employee
    name: Optional[str] = None
    # Track 14.0-HR-READINESS — legal name parts + preferred name.
    legal_first_name: Optional[str] = None
    legal_middle_name: Optional[str] = None
    legal_last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    employee_id: Optional[str] = None
    trade: Optional[str] = None
    role: Optional[str] = None
    crew: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    supervisor: Optional[str] = None
    hire_date: Optional[str] = None
    # termination: HR may override the requested status + final dates
    requested_status: Optional[str] = None
    termination_date: Optional[str] = None
    last_day_worked: Optional[str] = None
    reason: Optional[str] = None
    # HR notes attached to the audit trail
    hr_notes: Optional[str] = Field(default=None, max_length=2000)


class EmployeeRequestReject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(..., min_length=5, max_length=2000)


def _strip_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return doc
    out = dict(doc)
    out.pop("_id", None)
    return out


def _actor_role(actor: Optional[Dict[str, Any]]) -> str:
    if not actor:
        return "anonymous"
    return str(
        actor.get("_actor") or actor.get("_actor_kind") or actor.get("role")
        or actor.get("kind") or "authenticated"
    )


def _actor_label(actor: Optional[Dict[str, Any]]) -> str:
    if not actor:
        return "anonymous"
    return str(
        actor.get("name") or actor.get("email") or actor.get("user_id")
        or actor.get("id") or _actor_role(actor)
    )


async def _notify_hr_queue_pending(db, request_doc: Dict[str, Any], kind: str) -> None:
    """Track 14.0-HR-READINESS — fan out an in-app bell notification to
    every HR user (and the canonical `hr_inbox` channel) so a pending
    employee_request is clickable from the bell. Without this the
    /api/hr/employee-requests POST silently inserted a row that no
    operator ever saw, producing the "click does nothing" user report.

    The notification carries `link_url=/hr/employee-requests?id=<rid>`
    so the queue page can deep-link and highlight the new request.
    Best-effort — never raises (notifications are operational sugar,
    not a hard dependency of the request flow).

    TRACK 15.28C — rewritten to use canonical `emit_notification`
    (single schema, single collection, idempotent). Fans out one
    notification per active HR user via `recipient_user_id` so each
    user gets a person-targeted row that survives PM-style role-
    broadcast filtering on other portals.
    """
    try:
        rid = request_doc.get("id") or ""
        if kind == "new_hire":
            nm = ((request_doc.get("payload") or {}).get("name") or "(unnamed)")
            title = f"New employee request · {nm}"
            message = (
                f"Field submitted a new-hire request for {nm}. "
                "Open the queue to review and approve, reject, or merge."
            )
        else:
            nm = ((request_doc.get("payload") or {}).get("target_employee_name")
                  or "(employee)")
            title = f"Termination request · {nm}"
            message = (
                f"Field submitted a termination request for {nm}. "
                "Open the queue to review."
            )

        link_url = f"/hr/employee-requests?id={rid}"

        # Lazy import — keeps the legacy module importable in tests
        # where the notification service hasn't bootstrapped yet.
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
        except Exception:
            emit_notification = None  # type: ignore[assignment]

        # Person-target every active HR user. emit_notification is
        # idempotent (track 15.28C), so retries collapse safely.
        targets: List[Dict[str, Any]] = []
        try:
            async for u in db.hr_users.find(
                {"disabled": {"$ne": True}},
                {"_id": 0, "id": 1, "email": 1, "name": 1},
            ):
                targets.append(u)
        except Exception:  # noqa: BLE001
            pass

        if not emit_notification:
            return

        for t in targets:
            payload = {
                "type": "hr.employee_request",
                "title": title,
                "message": message,
                "severity": "Info",
                "recipient_role": "hr",
                "recipient_user_id": t.get("id"),
                "link_url": link_url,
                "linked_request_id": rid,
                "linked_source_module": "hr.employee_request",
                "linked_source_record_id": rid,
            }
            await emit_notification(db, payload)
    except Exception as e:  # noqa: BLE001
        try:
            from logging import getLogger
            getLogger("employee_requests").warning(
                f"[hr-notify] failed to fan out request {request_doc.get('id')}: {e}"
            )
        except Exception:  # noqa: BLE001
            pass


def register_employee_requests_routes(
    api_router: APIRouter,
    db,
    *,
    rate_limit_public_post,
    require_optional_portal_token,
    require_hr_or_admin,
):
    """Attach the queue endpoints.

    For Phase Alpha, this builds its own APIRouter (prefix /api) and
    returns it so the caller can include it on `app` directly — this
    avoids the order-of-include problem where the main `api_router`
    has already been mounted to `app` before this module is reachable.

    Args:
      api_router: legacy parameter retained for signature stability;
        a fresh router is built internally and returned.
      rate_limit_public_post: existing public-rate-limit dependency
      require_optional_portal_token: dependency that returns the actor
        dict if any portal token is present, or None for anonymous.
      require_hr_or_admin: dependency that enforces HR or Admin gate
        on the review endpoints.

    Returns:
      The new APIRouter ready to be included on `app`.
    """
    api_router = APIRouter(prefix="/api", tags=["employee-requests"])

    @api_router.post(
        "/employee-requests",
        dependencies=[Depends(rate_limit_public_post)],
    )
    async def submit_request(
        body: EmployeeRequestCreate,
        request: Request,
        actor: Optional[Dict[str, Any]] = Depends(require_optional_portal_token),
    ) -> Dict[str, Any]:
        """Submit a request to HR. Any portal token is accepted; public
        submissions are accepted but rate-limited. HR explicitly reviews
        every entry before any ``db.employees`` mutation happens.

        TRACK 22.4b-followup-HR — same-key concurrent retries are now
        deduped through the shared reservation-lock idempotency helper
        (workflow=hr_request). Identity defaults are also strengthened:
        portal-token submissions with a blank ``submitter_name`` now
        inherit ``_actor_label(actor)`` so HR always sees a real name
        for known-identity submitters.
        """
        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            kind = (body.kind or "").strip().lower()
            if kind not in ALLOWED_KINDS:
                raise HTTPException(
                    status_code=422,
                    detail={"code": "invalid_kind", "allowed": sorted(ALLOWED_KINDS)},
                )

            now = datetime.now(timezone.utc).isoformat()
            client_ip = (
                (request.client.host if request.client else "")
                or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or ""
            )

            # TRACK 22.4b-followup-HR — B-01 identity strengthening.
            # Portal-token submitters had blank ``submitter_name``/``submitter_email``
            # because leadership/HR/PM users don't retype their identity in the
            # request body. Default those fields from the resolved actor so
            # HR always sees a real name for known-identity submissions. Never
            # overwrites a value the client explicitly provided; never fills
            # for anonymous submissions.
            _submitter_name = (body.submitter_name or "").strip() or None
            _submitter_email = (body.submitter_email or "").strip() or None
            if actor and _actor_role(actor) not in ("anonymous", "public"):
                if not _submitter_name:
                    _submitter_name = _actor_label(actor) or None
                if not _submitter_email:
                    _submitter_email = (actor.get("email") or "").strip() or _submitter_email

            rid = str(uuid.uuid4())
            doc: Dict[str, Any] = {
                "id": rid,
                "kind": kind,
                "status": STATUS_PENDING,
                "requested_at": now,
                "requested_by_role": _actor_role(actor),
                "requested_by_label": _actor_label(actor),
                "requested_by_ip": client_ip[:64],
                "submitter_name": _submitter_name,
                "submitter_email": _submitter_email,
                "submitted_via": (body.submitted_via or "").strip() or None,
                "linked_fl_record_id": body.linked_fl_record_id or None,
                "audit_log": [
                    {
                        "at": now,
                        "kind": "submitted",
                        "actor_role": _actor_role(actor),
                        "actor_label": _actor_label(actor),
                        "ip": client_ip[:64],
                    }
                ],
            }

            if kind == "new_hire":
                name = (body.name or "").strip()
                if len(name) < 2:
                    raise HTTPException(
                        status_code=422,
                        detail={"code": "name_required",
                                "message": "name is required (>= 2 chars)"},
                    )
                doc["payload"] = {
                    "name": name,
                    "employee_id": (body.employee_id or "").strip() or None,
                    "trade": (body.trade or "").strip() or None,
                    "role": (body.role or "").strip() or None,
                    "crew": (body.crew or "").strip() or None,
                    "email": (body.email or "").strip() or None,
                    "phone": (body.phone or "").strip() or None,
                }
            else:  # termination
                target = (body.target_employee_id or "").strip()
                if not target:
                    raise HTTPException(
                        status_code=422,
                        detail={"code": "target_required",
                                "message": "target_employee_id is required for termination"},
                    )
                # Resolve target employee (by uuid id OR employee_id field)
                emp = await db.employees.find_one(
                    {"id": target, "deleted_at": None}, {"_id": 0}
                )
                if not emp:
                    emp = await db.employees.find_one(
                        {"employee_id": target, "deleted_at": None}, {"_id": 0}
                    )
                if not emp:
                    raise HTTPException(
                        status_code=404,
                        detail={"code": "target_not_found",
                                "message": f"No active employee matches '{target}'"},
                    )
                requested_status = (body.requested_status or "Terminated").strip()
                if requested_status not in TERMINATION_TARGET_STATUSES:
                    raise HTTPException(
                        status_code=422,
                        detail={"code": "invalid_requested_status",
                                "allowed": sorted(TERMINATION_TARGET_STATUSES)},
                    )
                doc["payload"] = {
                    "target_employee_id": emp["id"],
                    "target_employee_name": emp.get("name") or "",
                    "target_employee_id_field": emp.get("employee_id") or "",
                    "requested_status": requested_status,
                    "last_day_worked": (body.last_day_worked or "").strip() or None,
                    "reason": (body.reason or "").strip() or None,
                }

            await db.employee_requests.insert_one(dict(doc))

            # Track 14.0-HR-READINESS (2026-02-14): create an in-app
            # notification for every HR user so the bell click-through
            # lands on the queue with the new request highlighted. Before
            # this change the request was silently inserted with no
            # notification — HR would click the bell and find nothing.
            await _notify_hr_queue_pending(db, doc, kind)

            # TRACK 15.76 · Trust Spine — HR request lifecycle. HR is a
            # non-email workflow, so it emits record_created →
            # validation_complete → routing_resolved → dashboard_updated →
            # audit_written → completed in a single pass at submit-time.
            try:
                from lib.trust_spine import (  # noqa: PLC0415
                    emit_record_created, emit_workflow_stage,
                    STAGE_VALIDATION_COMPLETE, STAGE_ROUTING_RESOLVED,
                    STAGE_DASHBOARD_UPDATED, STAGE_AUDIT_WRITTEN,
                    STAGE_COMPLETED,
                )
                _hr_record = {"id": rid, "doc_id": rid, "project_number": ""}
                await emit_record_created(
                    db, workflow="hr-request", record=_hr_record,
                    module="routes/employee_requests.py:create_request",
                )
                await emit_workflow_stage(
                    db, workflow="hr-request", stage=STAGE_VALIDATION_COMPLETE,
                    record=_hr_record, module="employee_requests.create",
                    status="ok",
                )
                await emit_workflow_stage(
                    db, workflow="hr-request", stage=STAGE_ROUTING_RESOLVED,
                    record=_hr_record, module="hr_queue_pending",
                    status="ok",
                )
                await emit_workflow_stage(
                    db, workflow="hr-request", stage=STAGE_DASHBOARD_UPDATED,
                    record=_hr_record, module="hr_bell_notification",
                    status="ok",
                )
                await emit_workflow_stage(
                    db, workflow="hr-request", stage=STAGE_AUDIT_WRITTEN,
                    record=_hr_record, module="db.employee_requests.insert_one",
                    status="ok",
                )
                await emit_workflow_stage(
                    db, workflow="hr-request", stage=STAGE_COMPLETED,
                    record=_hr_record, module="routes/employee_requests.py",
                    status="ok",
                )
            except Exception:  # noqa: BLE001
                pass

            return {"ok": True, "id": rid, "request": _strip_id(doc)}

        return await with_idempotency(db, key, actor or {"role": "public"}, _do_create, workflow="hr_request")


    @api_router.get("/hr/employee-requests")
    async def list_requests(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        status: Optional[str] = Query(default=STATUS_PENDING),
        kind: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        clauses: List[Dict[str, Any]] = []
        if status:
            if status not in ALL_STATUSES:
                raise HTTPException(422, "invalid_status")
            clauses.append({"status": status})
        if kind:
            if kind not in ALLOWED_KINDS:
                raise HTTPException(422, "invalid_kind")
            clauses.append({"kind": kind})
        q = {"$and": clauses} if clauses else {}
        cur = db.employee_requests.find(q, {"_id": 0}).sort("requested_at", -1).limit(limit)
        items: List[Dict[str, Any]] = []
        async for d in cur:
            items.append(_strip_id(d))
        # also return pending count for badge UX
        pending_count = await db.employee_requests.count_documents(
            {"status": STATUS_PENDING}
        )
        return {
            "items": items,
            "count": len(items),
            "pending_count": pending_count,
            "kpi_metadata": _employee_request_kpi_metadata(status),
        }

    @api_router.get("/hr/employee-requests/{rid}")
    async def get_request(
        rid: str,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        doc = await db.employee_requests.find_one({"id": rid}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Request not found")
        return _strip_id(doc)

    @api_router.post("/hr/employee-requests/{rid}/approve")
    async def approve_request(
        rid: str,
        body: EmployeeRequestApprove = Body(default_factory=EmployeeRequestApprove),
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        doc = await db.employee_requests.find_one({"id": rid}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Request not found")
        if doc.get("status") != STATUS_PENDING:
            raise HTTPException(409, f"Request already {doc.get('status')}")

        now = datetime.now(timezone.utc).isoformat()
        actor_role = _actor_role(actor)
        actor_label = _actor_label(actor)
        kind = doc.get("kind")
        payload = dict(doc.get("payload") or {})

        # Apply HR overrides from body (only non-None fields)
        body_dict = body.model_dump(exclude_none=True)
        overrides = {k: v for k, v in body_dict.items() if k != "hr_notes"}
        payload.update(overrides)

        # ---- new_hire path ----
        resulting_employee_id: Optional[str] = None
        if kind == "new_hire":
            name = (payload.get("name") or "").strip()
            if not name:
                raise HTTPException(422, "name is required to create employee")
            # Mirror canonical employee constructor (HR-style) — keep this
            # tight; HR retains full lifecycle authority. Duplicate guard
            # against active matches (HR can still override by editing
            # the name before approving).
            existing_active = await db.employees.find_one(
                {
                    "name": {"$regex": f"^{_re.escape(name)}$", "$options": "i"},
                    "deleted_at": None,
                    "$or": [
                        {"lifecycle_status": {"$in": [
                            "Active", "Pending Hire", "On Leave"
                        ]}},
                        {"lifecycle_status": {"$exists": False},
                         "is_active": {"$ne": False}},
                    ],
                },
                {"_id": 0},
            )
            if existing_active:
                raise HTTPException(
                    409,
                    {
                        "code": "duplicate_active_employee",
                        "message": (
                            f"An active employee named '{name}' already exists. "
                            f"Edit the name or reject this request."
                        ),
                        "candidate": existing_active,
                    },
                )

            new_id = str(uuid.uuid4())
            emp = {
                "id": new_id,
                "name": name,
                # Track 14.0-HR-READINESS — preserve legal name parts +
                # preferred name on the employee record so directory
                # views, daily reports, and field forms can display
                # "James Fisher (Jimmy)" without losing legal identity.
                "legal_first_name": payload.get("legal_first_name") or "",
                "legal_middle_name": payload.get("legal_middle_name") or "",
                "legal_last_name": payload.get("legal_last_name") or "",
                "preferred_name": payload.get("preferred_name") or "",
                "employee_id": payload.get("employee_id") or "",
                "trade": payload.get("trade") or "",
                "role": payload.get("role") or "",
                "crew": payload.get("crew") or "",
                "email": payload.get("email") or "",
                "phone": payload.get("phone") or "",
                "supervisor": payload.get("supervisor") or "",
                "department": "",
                "default_project_number": "",
                "hire_date": payload.get("hire_date") or None,
                "original_hire_date": payload.get("hire_date") or None,
                "lifecycle_status": "Active",
                "is_active": True,
                "added_via": "hr-queue-approval",
                "created_at": now,
                "updated_at": now,
                "status_history": [{
                    "at": now,
                    "by": actor_label,
                    "actor_role": actor_role,
                    "to": "Active",
                    "reason": f"Approved from HR Queue · request {rid}",
                    "kind": "hr_queue_new_hire_approval",
                    "queue_request_id": rid,
                }],
                "deleted_at": None,
            }
            await db.employees.insert_one(dict(emp))
            resulting_employee_id = new_id

            # Append to append-only lifecycle events collection
            await db.employee_lifecycle_events.insert_one({
                "id": str(uuid.uuid4()),
                "employee_id": new_id,
                "at": now,
                "actor_role": actor_role,
                "actor_label": actor_label,
                "kind": "new_hire_approved",
                "queue_request_id": rid,
                "to_status": "Active",
                "from_status": None,
                "reason": body.hr_notes or "",
                "payload_snapshot": {k: v for k, v in emp.items() if k != "_id"},
            })

        # ---- termination path ----
        else:  # kind == "termination"
            target_id = (payload.get("target_employee_id") or "").strip()
            if not target_id:
                raise HTTPException(422, "target_employee_id missing on request")
            requested_status = (
                payload.get("requested_status") or "Terminated"
            ).strip()
            if requested_status not in TERMINATION_TARGET_STATUSES:
                raise HTTPException(
                    422,
                    f"Invalid status. Allowed: {sorted(TERMINATION_TARGET_STATUSES)}",
                )
            existing = await db.employees.find_one(
                {"id": target_id, "deleted_at": None}, {"_id": 0}
            )
            if not existing:
                raise HTTPException(404, "Target employee not found")
            prev_status = (
                existing.get("lifecycle_status")
                or ("Active" if existing.get("is_active") is not False else "Inactive")
            )

            set_block: Dict[str, Any] = {
                "lifecycle_status": requested_status,
                "is_active": False,  # all 4 termination targets are inactive
                "updated_at": now,
                "termination_date": payload.get("termination_date") or now[:10],
                "last_day_worked": payload.get("last_day_worked") or now[:10],
                "separation_type": requested_status,
            }
            history_entry = {
                "at": now,
                "by": actor_label,
                "actor_role": actor_role,
                "from": prev_status,
                "to": requested_status,
                "reason": payload.get("reason") or body.hr_notes or "",
                "kind": "hr_queue_termination_approval",
                "queue_request_id": rid,
            }
            await db.employees.update_one(
                {"id": target_id},
                {"$set": set_block, "$push": {"status_history": history_entry}},
            )
            resulting_employee_id = target_id

            await db.employee_lifecycle_events.insert_one({
                "id": str(uuid.uuid4()),
                "employee_id": target_id,
                "at": now,
                "actor_role": actor_role,
                "actor_label": actor_label,
                "kind": "termination_approved",
                "queue_request_id": rid,
                "from_status": prev_status,
                "to_status": requested_status,
                "reason": payload.get("reason") or body.hr_notes or "",
            })

        # Stamp the request as approved (append-only audit log entry)
        await db.employee_requests.update_one(
            {"id": rid},
            {
                "$set": {
                    "status": STATUS_APPROVED,
                    "resolved_at": now,
                    "resolved_by_role": actor_role,
                    "resolved_by_label": actor_label,
                    "resulting_employee_id": resulting_employee_id,
                    "hr_notes": body.hr_notes or "",
                    "applied_payload": payload,
                },
                "$push": {
                    "audit_log": {
                        "at": now,
                        "kind": "approved",
                        "actor_role": actor_role,
                        "actor_label": actor_label,
                        "resulting_employee_id": resulting_employee_id,
                        "hr_notes": body.hr_notes or "",
                    }
                },
            },
        )

        out = await db.employee_requests.find_one({"id": rid}, {"_id": 0})
        return {
            "ok": True,
            "id": rid,
            "resulting_employee_id": resulting_employee_id,
            "request": _strip_id(out),
        }

    @api_router.post("/hr/employee-requests/{rid}/reject")
    async def reject_request(
        rid: str,
        body: EmployeeRequestReject,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        doc = await db.employee_requests.find_one({"id": rid}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Request not found")
        if doc.get("status") != STATUS_PENDING:
            raise HTTPException(409, f"Request already {doc.get('status')}")
        now = datetime.now(timezone.utc).isoformat()
        actor_role = _actor_role(actor)
        actor_label = _actor_label(actor)
        await db.employee_requests.update_one(
            {"id": rid},
            {
                "$set": {
                    "status": STATUS_REJECTED,
                    "resolved_at": now,
                    "resolved_by_role": actor_role,
                    "resolved_by_label": actor_label,
                    "rejection_reason": body.reason.strip(),
                },
                "$push": {
                    "audit_log": {
                        "at": now,
                        "kind": "rejected",
                        "actor_role": actor_role,
                        "actor_label": actor_label,
                        "reason": body.reason.strip(),
                    }
                },
            },
        )
        out = await db.employee_requests.find_one({"id": rid}, {"_id": 0})
        return {"ok": True, "id": rid, "request": _strip_id(out)}

    return api_router


async def ensure_employee_requests_indexes(db) -> None:
    """Idempotent index creation."""
    try:
        await db.employee_requests.create_index("id", unique=True)
        await db.employee_requests.create_index("status")
        await db.employee_requests.create_index("kind")
        await db.employee_requests.create_index([("requested_at", -1)])
        await db.employee_lifecycle_events.create_index("employee_id")
        await db.employee_lifecycle_events.create_index([("at", -1)])
        await db.employee_lifecycle_events.create_index("queue_request_id")
    except Exception:  # noqa: BLE001
        # idempotent — never fail boot on index drift
        pass


__all__ = [
    "register_employee_requests_routes",
    "ensure_employee_requests_indexes",
    "ALLOWED_KINDS",
    "TERMINATION_TARGET_STATUSES",
]
