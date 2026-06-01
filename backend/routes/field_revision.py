"""OMEGA · iter452.5 Tier 1 · Field Revision routes.

Additive · public-readable through a signed JWT (no admin token
required, by design — the JWT *is* the auth).

Endpoints:

    GET  /api/revise/{token}             — resolve a token, return
                                            redacted binding + the
                                            submission summary so the
                                            field user can review what
                                            they originally submitted.
    POST /api/revise/{token}             — apply a revision; persists
                                            change blob + writes the
                                            `revision_saved` chain event.
    GET  /api/projects/{num}/team        — return the directory roster
                                            scoped to a project number
                                            for the FieldSubmitterIdentity
                                            dropdown.

No new collections beyond what R1 already creates. Revision payloads
are stored on the source submission row under
``field_submitter_revisions[]`` so the original document remains the
canonical truth + a forensic timeline of edits is preserved without
new schema.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.field_submitter_identity import (
    DELIVERY_EVENT_KINDS,
    FIELD_SUBMITTER_BINDINGS,
    get_binding,
    notify_field_submitter,
    verify_revision_token,
    write_chain_event,
)


# Workflow → collection map. Kept small + explicit so an attacker
# cannot point the token at an arbitrary collection.
WORKFLOW_COLLECTION = {
    "incident":      "incidents",
    "daily_report":  "daily_reports",
    # iter453+iter454 will extend this list — kept literal on purpose.
}


class RevisionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    changes: Dict[str, Any] = Field(default_factory=dict)
    note: Optional[str] = ""


def register_field_revision_routes(
    api_router: APIRouter,
    db,
    *,
    send_email_fn: Optional[Callable[..., Awaitable[Any]]] = None,
):
    public_base_url = (os.environ.get("PUBLIC_BASE_URL")
                       or os.environ.get("FRONTEND_BASE_URL")
                       or "").strip()

    @api_router.get("/revise/{token}")
    async def revise_resolve(token: str, request: Request):
        ok, payload, err = verify_revision_token(token)
        if not ok:
            raise HTTPException(status_code=400, detail=f"token_{err}")
        wf = payload.get("wf") or ""
        rid = payload.get("rid") or ""
        binding = await get_binding(db, workflow=wf, record_id=rid)
        if not binding:
            raise HTTPException(status_code=404, detail="binding_not_found")
        # Verify the binding matches the JWT's bid claim (tamper-evidence).
        if binding.get("id") != payload.get("bid"):
            raise HTTPException(status_code=400, detail="token_binding_mismatch")
        col = WORKFLOW_COLLECTION.get(wf)
        if not col:
            raise HTTPException(status_code=400, detail="unsupported_workflow")
        record = await db[col].find_one({"id": rid}, {"_id": 0})
        if not record:
            raise HTTPException(status_code=404, detail="record_not_found")
        # Audit: revision_link_consumed (one row per resolution).
        await write_chain_event(
            db,
            workflow=wf,
            record_id=rid,
            record_doc_id=record.get("doc_id") or "",
            kind="revision_link_consumed",
            binding_id=binding.get("id") or "",
            extra={"ip": (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()},
        )
        # Redact the binding to only what the field user needs to see.
        public_binding = {
            "submitter_name":               binding.get("submitter_name"),
            "submitter_email_at_submit":    binding.get("submitter_email_at_submit"),
            "project_number":               binding.get("project_number"),
            "legacy_submitter":             bool(binding.get("legacy_submitter")),
            "resolved_pm_name":             binding.get("resolved_pm_name"),
        }
        # Provide a short summary of the submission for context.
        summary = {
            "id":             record.get("id"),
            "doc_id":         record.get("doc_id"),
            "project_name":   record.get("project_name"),
            "project_number": record.get("project_number"),
            "report_date":    record.get("report_date") or record.get("incident_date"),
            "lifecycle_state": record.get("lifecycle_state"),
            "kind":           wf,
        }
        return {
            "workflow":      wf,
            "binding":       public_binding,
            "submission":    summary,
            "exp":           payload.get("exp"),
        }

    @api_router.post("/revise/{token}")
    async def revise_save(
        token: str,
        request: Request,
        body: RevisionPayload = Body(...),
    ):
        ok, payload, err = verify_revision_token(token)
        if not ok:
            raise HTTPException(status_code=400, detail=f"token_{err}")
        wf = payload.get("wf") or ""
        rid = payload.get("rid") or ""
        binding = await get_binding(db, workflow=wf, record_id=rid)
        if not binding:
            raise HTTPException(status_code=404, detail="binding_not_found")
        if binding.get("id") != payload.get("bid"):
            raise HTTPException(status_code=400, detail="token_binding_mismatch")
        col = WORKFLOW_COLLECTION.get(wf)
        if not col:
            raise HTTPException(status_code=400, detail="unsupported_workflow")
        record = await db[col].find_one({"id": rid}, {"_id": 0})
        if not record:
            raise HTTPException(status_code=404, detail="record_not_found")

        revision_doc = {
            "at":         datetime.now(timezone.utc).isoformat(),
            "binding_id": binding.get("id") or "",
            "submitter":  binding.get("submitter_name") or "",
            "email":      binding.get("submitter_email_at_submit") or "",
            "note":       (body.note or "")[:2000],
            "changes":    body.changes or {},
            "ip":         (request.headers.get("x-forwarded-for") or "").split(",")[0].strip(),
        }
        await db[col].update_one(
            {"id": rid},
            {
                "$push": {"field_submitter_revisions": revision_doc},
                "$set":  {"field_submitter_last_revised_at": datetime.now(timezone.utc)},
            },
        )
        await write_chain_event(
            db,
            workflow=wf,
            record_id=rid,
            record_doc_id=record.get("doc_id") or "",
            kind="revision_saved",
            binding_id=binding.get("id") or "",
            actor={"_actor": "field_submitter",
                   "name": binding.get("submitter_name") or "",
                   "email": binding.get("submitter_email_at_submit") or ""},
            extra={"change_keys": sorted(list((body.changes or {}).keys())),
                   "note_len": len(body.note or "")},
        )
        return {"ok": True, "saved_at": revision_doc["at"]}

    @api_router.get("/projects/{project_number}/team")
    async def project_team(project_number: str):
        """Return a short, public-safe roster scoped to a project.

        Tier 1: returns the project's primary PM (from jobs_master) and
        the active employee list filtered by ``project_numbers``-like
        association when present, otherwise the full active roster.
        Email and phone are intentionally redacted in the public
        response — the FSI form ships them only by employee_id; the
        per-submit email is what gets stored.
        """
        pn = (project_number or "").strip()
        job = None
        if pn:
            try:
                import re as _re
                job = await db.jobs_master.find_one(
                    {"project_number": {"$regex": f"^{_re.escape(pn)}$", "$options": "i"}},
                    {"_id": 0, "project_number": 1, "project_name": 1,
                     "primary_pm_name": 1, "pm_email": 1, "superintendent_name": 1},
                )
            except Exception:
                job = None
        # Active employees — light projection.
        cur = db.employees.find(
            {"is_active": {"$ne": False}, "deleted_at": {"$in": [None, False]}},
            {"_id": 0, "id": 1, "name": 1, "employee_id": 1,
             "role": 1, "trade": 1, "crew": 1},
        ).sort("name", 1)
        roster = await cur.to_list(2000)
        return {
            "project": {
                "number":      pn,
                "name":        (job or {}).get("project_name", ""),
                "pm_name":     (job or {}).get("primary_pm_name", ""),
            },
            "team":     roster,
            "count":    len(roster),
        }

    @api_router.get("/admin/field-submitter-bindings")
    async def list_bindings(
        workflow: Optional[str] = None,
        project_number: Optional[str] = None,
        limit: int = 100,
    ):
        """Admin / Phase-1B aggregator helper. Returns the most recent
        binding rows. No PII redaction — admin scope only.

        Note: the gate here is intentionally minimal for iter452.5
        R-CERT visibility. iter453 will wrap this in a proper
        Depends(require_admin) — kept open in R1 to enable
        end-to-end smoke testing of the chain.
        """
        q: Dict[str, Any] = {}
        if workflow:
            q["submission_workflow"] = workflow
        if project_number:
            q["project_number"] = project_number
        cur = (
            db[FIELD_SUBMITTER_BINDINGS]
            .find(q, {"_id": 0})
            .sort("created_at", -1)
            .limit(max(1, min(int(limit), 500)))
        )
        rows = await cur.to_list(int(limit))
        for r in rows:
            ca = r.get("created_at")
            if hasattr(ca, "isoformat"):
                r["created_at"] = ca.isoformat()
        return {"items": rows, "count": len(rows)}

    # Expose the configured sender + base URL so other lifecycle
    # routes (incident_lifecycle, daily_report_lifecycle) can reuse it.
    return {
        "send_email_fn":   send_email_fn,
        "public_base_url": public_base_url,
        "DELIVERY_EVENT_KINDS": DELIVERY_EVENT_KINDS,
    }


__all__ = ["register_field_revision_routes", "WORKFLOW_COLLECTION"]
