"""Track 19.16 · Phase B2 · PUBLIC GATE — Near-Miss Kiosk.

Additive HTTP surface for anonymous / self-identified near-miss reports.
Bypasses the authenticated ``require_safety_admin_or_pm`` gate but
routes the resulting case through the exact same Phase A domain engine.
No legacy code is touched. No Phase A guarantee is weakened.

Zero-Drift guarantees preserved:
    * Legacy ``/api/incidents/*`` untouched.
    * Phase A ``/api/incident-cases/*`` untouched.
    * All near-miss cases created here go through ``case_service.create_case``
      and ``case_service.transition_case`` — the exact same helpers used by
      authenticated flows. Same audit, same events, same immutability.

Idempotency:
    Clients pass ``X-Idempotency-Key`` (or JSON ``idempotency_key``). A
    duplicate submit within 24h returns the SAME case instead of creating
    a second one. Uses ``incident_case_public_submissions`` collection.

Anonymity model:
    ``submitter_kind`` = ``anonymous`` | ``self_identified`` | ``fsi_matched``
    Nothing is faked. If no identifying data is provided → anonymous.
    Field Submitter Identity matching is deferred (best-effort hook only —
    the FSI service can populate the marker in a follow-up track).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from . import case_service
from .constants import INCIDENT_TYPE_CODES
from .evidence import add_evidence
from .events import emit_event


COLLECTION_PUBLIC_SUBS = "incident_case_public_submissions"


class NearMissPublicSubmission(BaseModel):
    """Body accepted by the public near-miss kiosk."""
    model_config = ConfigDict(extra="forbid")

    what_almost_happened: str
    location_label: str
    immediate_danger: bool = False
    submitter_name: str = ""
    submitter_contact: str = ""
    submitter_company: str = ""
    location_gps: Optional[Dict[str, float]] = None
    photo_data_url: str = ""
    photo_metadata: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = ""
    language: str = "en"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_for_public_submission(sub: NearMissPublicSubmission) -> Dict[str, Any]:
    """Synthesize an actor for the domain engine. Public-gate is treated
    as a synthetic ``safety`` role so it clears the capability gates —
    but the case ledger clearly attributes the action to
    ``public_gate_near_miss`` in the payload."""
    if sub.submitter_name.strip():
        name = sub.submitter_name.strip()
    else:
        name = "Public Near-Miss Kiosk"
    return {"role": "safety", "name": name, "_source": "public_gate_near_miss"}


def _submitter_kind(sub: NearMissPublicSubmission) -> str:
    if not sub.submitter_name.strip() and not sub.submitter_contact.strip():
        return "anonymous"
    return "self_identified"


async def _find_previous_submission(
    db, idempotency_key: str,
) -> Optional[Dict[str, Any]]:
    if not idempotency_key.strip():
        return None
    return await db[COLLECTION_PUBLIC_SUBS].find_one(
        {"idempotency_key": idempotency_key}, {"_id": 0},
    )


async def _record_submission(
    db,
    *,
    idempotency_key: str,
    case_id: str,
    case_number: str,
    submitter_kind: str,
) -> None:
    await db[COLLECTION_PUBLIC_SUBS].insert_one({
        "idempotency_key": idempotency_key,
        "case_id": case_id,
        "case_number": case_number,
        "submitter_kind": submitter_kind,
        "created_at": _now(),
    })


async def submit_public_near_miss(
    db,
    submission: NearMissPublicSubmission,
) -> Dict[str, Any]:
    """Create a near-miss incident case from a public-gate submission."""
    # Idempotency check first.
    prev = await _find_previous_submission(db, submission.idempotency_key)
    if prev:
        existing = await case_service.get_case(db, prev["case_id"])
        if existing:
            return {
                "case": existing,
                "case_number": existing.get("case_number") or "",
                "case_id": existing["id"],
                "submitter_kind": prev.get("submitter_kind", "anonymous"),
                "duplicate": True,
                "immediate_danger": submission.immediate_danger,
            }

    actor = _actor_for_public_submission(submission)
    kind = _submitter_kind(submission)

    field_block = {
        "incident_type": "near_miss",
        "occurred_at": _now(),
        "reported_at": _now(),
        "location_label": (submission.location_label or "").strip(),
        "location_gps": submission.location_gps or None,
        "reporter_name": submission.submitter_name.strip() or "Anonymous",
        "reporter_role": "public",
        "observed_conditions": submission.what_almost_happened.strip(),
        # Extra fields (Pydantic extra="allow" on FieldBlock)
        "public_gate_source": "public_gate_near_miss",
        "submitter_kind": kind,
        "submitter_contact": submission.submitter_contact.strip(),
        "submitter_company": submission.submitter_company.strip(),
        "submitter_language": submission.language,
        "immediate_danger_flag": bool(submission.immediate_danger),
    }

    # ``near_miss`` is one of the 9 canonical types — belt-and-braces guard.
    if field_block["incident_type"] not in INCIDENT_TYPE_CODES:
        raise HTTPException(500, detail={"code": "type_unavailable"})

    created = await case_service.create_case(
        db, actor=actor, field_block=field_block,
    )

    # Attach a domain event that unambiguously flags the source. This is
    # separate from the standard case.created event so subscribers can
    # filter public-gate volume.
    await emit_event(
        db,
        case_id=created["id"],
        event_type="case.created",  # secondary marker; primary is auto-emitted
        actor=actor,
        payload={
            "kiosk": True,
            "submitter_kind": kind,
            "immediate_danger": bool(submission.immediate_danger),
            "language": submission.language,
        },
    )

    # Optional photo evidence.
    if submission.photo_data_url:
        try:
            await add_evidence(
                db,
                case_id=created["id"],
                evidence_type="photo",
                actor=actor,
                label="public_kiosk_photo",
                metadata={
                    **(submission.photo_metadata or {}),
                    "public_gate": True,
                },
            )
        except Exception:
            # Photo failure is non-fatal for public submission.
            pass

    # Immediately transition to FIELD_SUBMITTED — the field observations
    # are locked. Safety picks up during intake.
    submitted = await case_service.transition_case(
        db,
        case_id=created["id"],
        to_state="FIELD_SUBMITTED",
        actor=actor,
    )

    # Record the idempotency mapping so replays return the same case.
    if submission.idempotency_key.strip():
        await _record_submission(
            db,
            idempotency_key=submission.idempotency_key.strip(),
            case_id=submitted["id"],
            case_number=submitted.get("case_number", ""),
            submitter_kind=kind,
        )

    return {
        "case": submitted,
        "case_number": submitted.get("case_number", ""),
        "case_id": submitted["id"],
        "submitter_kind": kind,
        "duplicate": False,
        "immediate_danger": bool(submission.immediate_danger),
    }


def register_public_routes(api_router: APIRouter, db) -> None:
    """Attach public no-auth routes.

    Endpoint namespace: ``/api/public/*``. This is deliberately isolated
    from the authenticated ``/api/incident-cases/*`` surface so proxies
    or WAFs can apply different policies (rate limits, captchas, etc.)
    without impacting the internal API.
    """

    @api_router.post("/public/near-miss")
    async def public_near_miss_route(
        request: Request,
        body: NearMissPublicSubmission = Body(...),
    ) -> Dict[str, Any]:
        # Header-based idempotency key wins over body if both are present.
        header_key = request.headers.get("X-Idempotency-Key") or ""
        if header_key and not body.idempotency_key:
            body = body.model_copy(update={"idempotency_key": header_key})
        try:
            return await submit_public_near_miss(db, body)
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(422, detail={"code": "invalid", "detail": str(e)})
        except Exception as e:  # pragma: no cover — defensive
            raise HTTPException(500, detail={"code": "internal_error", "detail": str(e)})


__all__ = [
    "NearMissPublicSubmission",
    "submit_public_near_miss",
    "register_public_routes",
    "COLLECTION_PUBLIC_SUBS",
]
