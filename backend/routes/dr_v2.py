"""DR-ROI-001 · Phase C · Daily Report V2 API routes.

ADDITIVE surface. Zero drift on V1 routes, V1 schema, V1 collections.

Endpoints:
  GET  /api/dr-v2/meta                   — provider + feature-flag state
  POST /api/dr-v2/drafts                 — save/update supervisor V2 draft
  GET  /api/dr-v2/drafts/{report_id}     — read a V2 draft
  POST /api/dr-v2/ai/synthesize          — run/return cached AI synthesis
  POST /api/dr-v2/ai/approve             — supervisor approval / edit / reject
  GET  /api/dr-v2/ai/audit/{report_id}   — immutable append-only audit trail

Feature flag: DR_V2_AI_ENABLED (env). When false, /synthesize returns
`ai_available: false` and a supervisor can still save drafts.

Collections (all NEW — never touch daily_reports):
  dr_v2_drafts        — supervisor structured inputs
  dr_v2_ai_cache      — evidence-hash keyed agent outputs
  dr_v2_ai_approvals  — supervisor decisions + append-only log
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from services.dr_ai import (
    AGENTS,
    AGENT_ORDER,
    build_evidence_bundle,
    evidence_hash,
    get_ai_provider,
    provider_meta,
    read_cache,
    write_cache,
)
from services.dr_ai.agents import AGENT_RESPONSE_SCHEMA
from services.dr_ai.cache import ensure_indexes as ensure_ai_cache_indexes
from services.dr_ai.vision import analyze_draft_photos
# TRACK 24.13 · Evidence Manifest — used when the caller requests the
# `manifest_summary` agent so the AI reasons over the full evidence
# manifest (typed fields · photos · extracted docs · reconciled tickets)
# instead of the older whitelist-only bundle.
from services.dr_evidence import build_manifest, manifest_to_ai_bundle
from services.ods_spine import (
    ingest_dr_v2_draft as _ods_ingest_dr_v2_draft,
    ingest_dr_v2_approval as _ods_ingest_dr_v2_approval,
    ods_enabled as _ods_enabled,
    dr_v2_spine_emission_enabled as _ods_emission_on,
)
from services.ods_spine.kpi import compute_kpi_snapshot as _ods_compute_snapshot


DRAFTS_COLL = "dr_v2_drafts"
APPROVALS_COLL = "dr_v2_ai_approvals"          # summary doc (last_action, first/latest ts)
APPROVAL_ENTRIES_COLL = "dr_v2_ai_audit_entries"  # append-only, one doc per entry (16MB-safe)

LEGACY_COMPAT_ERROR = {
    "error": "legacy_daily_report_runtime_retired",
    "message": "Legacy Daily Report V2 authoring is retired. Use the canonical /daily/submit flow.",
    "canonical_route": "/daily/submit",
    "canonical_api": "/api/daily-reports",
    "compat_mode": "read_only",
}


# -----------------------------------------------------------------------------
# Request / response models
# -----------------------------------------------------------------------------

class DraftPayload(BaseModel):
    report_id: Optional[str] = Field(default=None, description="Client-generated; server assigns if missing")
    supervisor_id: Optional[str] = None
    project_number: Optional[str] = None
    project_name: Optional[str] = None
    client: Optional[str] = None
    project_manager: Optional[str] = None
    location: Optional[str] = None
    weather_summary: Optional[str] = None
    supervisor_name: Optional[str] = None
    report_date: Optional[str] = None
    day_setup: Dict[str, Any] = Field(default_factory=dict)
    masci_crews: List[Dict[str, Any]] = Field(default_factory=list)
    visitors: List[Dict[str, Any]] = Field(default_factory=list)
    equipment_used: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    outbound_materials: List[Dict[str, Any]] = Field(default_factory=list)
    subcontractors: List[Dict[str, Any]] = Field(default_factory=list)
    vendors: List[Dict[str, Any]] = Field(default_factory=list)
    activity_cards: List[Dict[str, Any]] = Field(default_factory=list)
    constraint_cards: List[Dict[str, Any]] = Field(default_factory=list)
    # TRACK 26.12 · Previously-dropped field groups (production rows,
    # V1-shaped constraints, day-impact toggles, narrative sections).
    production: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    day_impacts: Dict[str, Any] = Field(default_factory=dict)
    narrative_sections: Dict[str, Any] = Field(default_factory=dict)
    tomorrow_readiness: Dict[str, Any] = Field(default_factory=dict)
    safety: Dict[str, Any] = Field(default_factory=dict)
    safety_quality: Dict[str, Any] = Field(default_factory=dict)
    excavation: Optional[Dict[str, Any]] = None
    competent_person: Optional[Dict[str, Any]] = None
    work_stoppage: Optional[Dict[str, Any]] = None
    general_notes: Optional[str] = ""
    photos: List[Any] = Field(default_factory=list)
    photo_captions: List[str] = Field(default_factory=list)
    photo_observations: List[Dict[str, Any]] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    weather: Optional[Dict[str, Any]] = None


class SynthesizeRequest(BaseModel):
    report_id: str
    force: bool = False                 # bypass cache
    agents: Optional[List[str]] = None  # subset opt-in; default all


class ApprovalRequest(BaseModel):
    report_id: str
    action: str                          # accept | edit | reject | regenerate
    agent: Optional[str] = None          # per-agent decision when applicable
    edited_narrative: Optional[str] = None
    supervisor_id: Optional[str] = None
    reason: Optional[str] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _v2_ai_enabled() -> bool:
    # TRACK 26.12 · Default-enabled. A missing env var in production
    # used to silently kill the entire DR AI path. Explicit false still
    # disables; anything else (including unset) leaves it on — actual
    # availability is still governed by key presence in provider_meta().
    raw = (os.environ.get("DR_V2_AI_ENABLED") or "").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()  # TRACK-27.03-EXEMPT: machine envelope timestamp; frontend renders via formatPlatformTime


def _raise_legacy_write_retired() -> None:
    raise HTTPException(status_code=410, detail=LEGACY_COMPAT_ERROR)


def _draft_to_evidence(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a saved draft into the field-shape the evidence bundle
    whitelist expects.

    TRACK 24.12 · Workstream A · Prior implementation carried only
    ~15 fields. Now forwards every DR field group the V3 shell / V1
    NewDailyReport submits (crew · equipment · materials · outbound
    hauling · subs · visitors · safety · excavation · CP · work
    stoppage · tomorrow · general notes · weather · GPS · photos +
    captions · photo observations · attachment metadata).
    """
    flat: Dict[str, Any] = {}
    setup = draft.get("day_setup") or {}
    for k in ("project_name", "project_number", "report_date", "shift",
              "supervisor_name", "weather", "gps_location",
              "client", "project_manager", "location"):
        if setup.get(k):
            flat[k] = setup[k]
    # Top-level project metadata (V3 draft mirror).
    for k in ("project_name", "project_number", "report_date",
              "client", "project_manager", "location",
              "weather_summary", "supervisor_name"):
        if not flat.get(k) and draft.get(k):
            flat[k] = draft[k]
    # Full field groups.
    for k in (
        # Crew · Labor
        "masci_crews", "crew_hours_total", "absent_early_chips", "visitors",
        # Equipment
        "equipment_used", "equipment_hours", "equipment_idle_reasons",
        # V2 structured entry
        "activity_cards", "constraint_cards", "tomorrow_readiness",
        # TRACK 26.12 · production rows · V1 constraints · day impacts
        "production", "constraints", "day_impacts", "narrative_sections",
        # Materials / hauling
        "materials", "outbound_materials", "subcontractors", "vendors",
        # Safety / quality (structured)
        "safety_quality", "near_misses",
        # Excavation / CP / work-stoppage
        "excavation", "competent_person", "work_stoppage",
        # Free-text narrative + photo captions + photo intelligence
        "general_notes", "photos", "photo_captions", "photo_observations",
        # Attachment metadata — filename/category/size only. AI must
        # NOT claim to have read file contents (enforced by prompt).
        "attachments",
    ):
        if draft.get(k) not in (None, "", [], {}):
            flat[k] = draft[k]
    weather = draft.get("weather") or {}
    for k in ("temperature_f", "precipitation", "wind_mph"):
        if weather.get(k) is not None:
            flat[k] = weather[k]
    safety = draft.get("safety") or {}
    for k in ("safety_incidents", "quality_findings", "jha_ack"):
        if safety.get(k) is not None:
            flat[k] = safety[k]
    # V3 payload sends `safety_quality` at top level. Merge safety_quality's
    # notes/incidents_today/injuries_today/near_misses into the flat bundle
    # under the same top-level key so the AI prompt can cite them.
    sq = draft.get("safety_quality") or {}
    if isinstance(sq, dict) and sq:
        # keep the structured object AND surface flat fields for the AI.
        if "safety_incidents" not in flat and sq.get("incidents_today") is not None:
            flat["safety_incidents"] = bool(sq.get("incidents_today"))
    return flat


# -----------------------------------------------------------------------------
# Route registration
# -----------------------------------------------------------------------------

def register_dr_v2_routes(api_router: APIRouter, db) -> None:
    """Attach all /api/dr-v2/* routes onto the shared api_router.

    Called ONCE from server.py after daily_reports registration. Zero
    impact on V1 route parity.
    """

    # Best-effort index creation for cache + drafts + approvals.
    async def _ensure_all_indexes():
        try:
            await ensure_ai_cache_indexes(db)
            await db[DRAFTS_COLL].create_index("report_id", unique=True, name="dr_v2_drafts_report_id")
            await db[APPROVALS_COLL].create_index("report_id", unique=True, name="dr_v2_approvals_report_id")
            await db[APPROVAL_ENTRIES_COLL].create_index(
                [("report_id", 1), ("ts", 1)], name="dr_v2_ai_audit_entries_by_report_ts"
            )
            await db[APPROVAL_ENTRIES_COLL].create_index(
                "entry_id", unique=True, name="dr_v2_ai_audit_entries_entry_id"
            )
        except Exception:  # noqa: BLE001
            pass

    # Schedule index creation on the running loop without blocking boot.
    try:
        asyncio.get_event_loop().create_task(_ensure_all_indexes())
    except RuntimeError:
        # No running loop yet (module-import time on some environments).
        # First request will still succeed — indexes are best-effort.
        pass

    # -------------------------------------------------------------------
    @api_router.get("/dr-v2/meta")
    async def dr_v2_meta() -> Dict[str, Any]:
        pmeta = provider_meta()
        return {
            "feature_flag": _v2_ai_enabled(),
            "agents": AGENT_ORDER,
            "provider": pmeta["provider"],
            "model": pmeta["model"],
            "ai_available": pmeta["ai_available"] and _v2_ai_enabled(),
            "envelope_schema": AGENT_RESPONSE_SCHEMA,
            "read_only_compatibility": True,
            "legacy_writes_blocked": True,
            "canonical_route": "/daily/submit",
            "canonical_api": "/api/daily-reports",
        }

    # -------------------------------------------------------------------
    @api_router.post("/dr-v2/drafts")
    async def dr_v2_draft_save(payload: DraftPayload = Body(...)) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        report_id = payload.report_id or f"drv2-{uuid.uuid4().hex[:12]}"
        doc = payload.model_dump()
        doc["report_id"] = report_id
        doc["updated_at"] = _now_iso()

        existing = await db[DRAFTS_COLL].find_one({"report_id": report_id}, {"_id": 0, "created_at": 1})
        doc["created_at"] = (existing or {}).get("created_at", doc["updated_at"])

        bundle = build_evidence_bundle(_draft_to_evidence(doc))
        doc["evidence_hash"] = evidence_hash(bundle)

        await db[DRAFTS_COLL].update_one(
            {"report_id": report_id},
            {"$set": doc},
            upsert=True,
        )

        # ODS-001 · fire-and-forget spine emission.
        # Feature-flag gated (ODS_ENABLED + DR_V2_SPINE_EMISSION_ENABLED).
        # Never blocks the save response. Errors are swallowed — the
        # source draft is already durable.
        if _ods_enabled() and _ods_emission_on():
            async def _emit_and_snapshot():
                try:
                    fresh = await db[DRAFTS_COLL].find_one({"report_id": report_id}, {"_id": 0})
                    res = await _ods_ingest_dr_v2_draft(
                        db, fresh or doc, actor=payload.supervisor_id or "supervisor", trigger="event",
                    )
                    if res.get("ok") and res.get("project_id"):
                        await _ods_compute_snapshot(
                            db, tenant_id="masci",
                            project_id=res["project_id"], date=res["date"],
                        )
                except Exception:  # noqa: BLE001
                    pass
            try:
                asyncio.get_event_loop().create_task(_emit_and_snapshot())
            except RuntimeError:
                pass

        return {"report_id": report_id, "evidence_hash": doc["evidence_hash"], "saved_at": doc["updated_at"]}

    # -------------------------------------------------------------------
    @api_router.get("/dr-v2/drafts/{report_id}")
    async def dr_v2_draft_read(report_id: str = Path(...)) -> Dict[str, Any]:
        doc = await db[DRAFTS_COLL].find_one({"report_id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="draft not found")
        return doc

    # -------------------------------------------------------------------
    @api_router.post("/dr-v2/ai/synthesize")
    async def dr_v2_ai_synthesize(payload: SynthesizeRequest = Body(...)) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        draft = await db[DRAFTS_COLL].find_one({"report_id": payload.report_id}, {"_id": 0})
        if not draft:
            raise HTTPException(status_code=404, detail="draft not found for report_id")

        ai_on = _v2_ai_enabled()
        pmeta = provider_meta()
        provider = get_ai_provider() if ai_on else None

        # TRACK 26.12 · Inline photo vision BEFORE the narrative runs.
        # Photos attached to the draft (report photos, material ticket
        # photos, sub photos) are analyzed by the vision model and the
        # grounded observations are merged into the evidence bundle so
        # the narrative can cite actual photo content. Per-photo results
        # are content-hash cached — Regenerate never re-pays vision.
        photo_observations_used = 0
        if ai_on and pmeta["ai_available"]:
            try:
                vision_obs = await analyze_draft_photos(
                    db, report_id=payload.report_id, draft=draft,
                )
            except Exception:  # noqa: BLE001
                vision_obs = []
            if vision_obs:
                existing_obs = [
                    o for o in (draft.get("photo_observations") or [])
                    if isinstance(o, dict)
                ]
                draft["photo_observations"] = existing_obs + vision_obs
                photo_observations_used = len(vision_obs)

        bundle = build_evidence_bundle(_draft_to_evidence(draft))
        ehash = evidence_hash(bundle)
        requested = payload.agents or AGENT_ORDER
        # Reject any unknown agents so callers can't inject prompts.
        requested = [a for a in requested if a in AGENTS]

        outputs: Dict[str, Any] = {}
        cache_hits = 0
        cache_misses = 0

        # First pass — resolve everything the cache can answer synchronously.
        pending: List[str] = []
        for agent_name in requested:
            if not payload.force:
                cached = await read_cache(db, report_id=payload.report_id, agent=agent_name, evidence_hash=ehash)
                if cached and cached.get("result"):
                    outputs[agent_name] = cached["result"]
                    cache_hits += 1
                    continue
            pending.append(agent_name)
            cache_misses += 1

        # Handle disabled/missing key uniformly for pending agents.
        if pending and (not ai_on or not pmeta["ai_available"] or provider is None):
            for agent_name in pending:
                outputs[agent_name] = {
                    "agent": agent_name, "narrative": "", "confidence": 0.0,
                    "evidence_refs": [], "sources_used": [],
                    "uncertainties": ["AI synthesis disabled by feature flag or missing key"],
                    "model": pmeta["model"], "provider": pmeta["provider"],
                    "generated_at": _now_iso(),
                    "ai_available": False, "fallback_reason": "flag_off_or_missing_key",
                }
            pending = []

        # Parallel agent invocation — 3 Claude calls in parallel ≈ latency of 1.
        errors: List[Dict[str, str]] = []
        if pending:
            # TRACK 24.13 · The `manifest_summary` agent consumes the
            # full Evidence Manifest (typed fields + photos + extracted
            # attachments + reconciled tickets), not the older whitelist
            # bundle. We build the manifest once and reuse it for every
            # manifest-driven agent invocation.
            manifest_bundle: Optional[Dict[str, Any]] = None
            if any(a == "manifest_summary" for a in pending):
                try:
                    _ev = _draft_to_evidence(draft)
                    # Legacy `db.daily_reports` docs also carry
                    # `attachments[]` and pre-analyzed photo intel;
                    # V2 drafts do not. `build_manifest` gracefully
                    # produces a manifest with empty attachments/photos
                    # when they are absent — the AI is instructed to
                    # honor that honestly.
                    m_obj = build_manifest(
                        {**_ev, **draft},
                        attachment_extractions=draft.get("attachment_extractions") or [],
                        photo_intel=draft.get("photo_intelligence"),
                    )
                    manifest_bundle = manifest_to_ai_bundle(m_obj)
                except Exception:  # noqa: BLE001
                    manifest_bundle = None

            async def _run(agent_name: str):
                spec = AGENTS[agent_name]
                use_bundle = (
                    manifest_bundle if agent_name == "manifest_summary"
                    and manifest_bundle is not None else bundle
                )
                return agent_name, await provider.synthesize(
                    agent=agent_name,
                    system_message=spec["system"],
                    user_payload=use_bundle,
                    response_schema=AGENT_RESPONSE_SCHEMA,
                    session_id=f"drv2-{payload.report_id}-{agent_name}",
                )

            gathered = await asyncio.gather(
                *[_run(a) for a in pending], return_exceptions=True
            )
            for idx, item in enumerate(gathered):
                if isinstance(item, Exception):
                    errors.append({"agent": pending[idx], "error": item.__class__.__name__})
                    continue
                agent_name, result = item
                result_dict = result.to_dict()
                outputs[agent_name] = result_dict
                if result.ai_available:
                    await write_cache(
                        db,
                        report_id=payload.report_id,
                        agent=agent_name,
                        evidence_hash=ehash,
                        result=result_dict,
                    )

        # Aggregated confidence: min of agent confidences (weakest link).
        confs = [o.get("confidence", 0.0) for o in outputs.values() if o.get("ai_available")]
        aggregate = min(confs) if confs else 0.0

        return {
            "report_id": payload.report_id,
            "evidence_hash": ehash,
            "ai_available": ai_on and pmeta["ai_available"],
            "provider": pmeta["provider"],
            "model": pmeta["model"],
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "aggregate_confidence": aggregate,
            "photo_observations_used": photo_observations_used,
            "outputs": outputs,
            "errors": errors,
        }

    # -------------------------------------------------------------------
    @api_router.post("/dr-v2/ai/approve")
    async def dr_v2_ai_approve(payload: ApprovalRequest = Body(...)) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        action = (payload.action or "").lower()
        if action not in {"accept", "edit", "reject", "regenerate"}:
            raise HTTPException(status_code=400, detail="invalid action")

        draft = await db[DRAFTS_COLL].find_one({"report_id": payload.report_id}, {"_id": 0, "evidence_hash": 1})
        if not draft:
            raise HTTPException(status_code=404, detail="draft not found")

        entry = {
            "ts": _now_iso(),
            "action": action,
            "agent": payload.agent,
            "supervisor_id": payload.supervisor_id,
            "edited_narrative": (payload.edited_narrative or "")[:6000] if action == "edit" else None,
            "reason": (payload.reason or "")[:1000] if action in {"reject", "regenerate"} else None,
            "evidence_hash": draft.get("evidence_hash"),
            "entry_id": uuid.uuid4().hex,
            "report_id": payload.report_id,
        }

        # Append-only: one document per entry avoids the 16MB doc cap and
        # keeps every action immutable at the storage layer.
        await db[APPROVAL_ENTRIES_COLL].insert_one(dict(entry))

        # Summary doc (last_action for UI badge + created_at bookkeeping).
        await db[APPROVALS_COLL].update_one(
            {"report_id": payload.report_id},
            {
                "$setOnInsert": {"report_id": payload.report_id, "created_at": _now_iso()},
                "$set": {"last_action": action, "last_updated": _now_iso()},
                "$inc": {"entries_count": 1},
            },
            upsert=True,
        )
        summary = await db[APPROVALS_COLL].find_one({"report_id": payload.report_id}, {"_id": 0})

        # ODS-001 · Emit an intelligence_fact on ACCEPT so the spine has
        # a supervisor-approved narrative available to consumers.
        if action == "accept" and _ods_enabled() and _ods_emission_on():
            try:
                # Best-effort — pull latest AI cache entry for the accepted agent
                cache_doc = None
                if payload.agent:
                    cache_doc = await db["dr_v2_ai_cache"].find_one(
                        {"report_id": payload.report_id, "agent": payload.agent},
                        sort=[("cached_at", -1)],
                    )
                if cache_doc and (result := cache_doc.get("result")):
                    await _ods_ingest_dr_v2_approval(
                        db,
                        report_id=payload.report_id,
                        action="accept",
                        agent=payload.agent or "",
                        supervisor_id=payload.supervisor_id or "",
                        narrative=result.get("narrative", ""),
                        confidence=result.get("confidence", 0.0),
                        source_facts=result.get("evidence_refs", []),
                        model=result.get("model", ""),
                        provider=result.get("provider", ""),
                    )
            except Exception:  # noqa: BLE001
                pass

        # Return summary + the last N entries so the UI can update without a second fetch.
        recent_cursor = db[APPROVAL_ENTRIES_COLL].find(
            {"report_id": payload.report_id}, {"_id": 0}
        ).sort("ts", -1).limit(50)
        recent = [d async for d in recent_cursor]
        state = {**(summary or {}), "log": list(reversed(recent))}
        return {"report_id": payload.report_id, "entry": entry, "state": state}

    # -------------------------------------------------------------------
    @api_router.get("/dr-v2/ai/audit/{report_id}")
    async def dr_v2_ai_audit(report_id: str = Path(...)) -> Dict[str, Any]:
        summary = await db[APPROVALS_COLL].find_one({"report_id": report_id}, {"_id": 0})
        cursor = db[APPROVAL_ENTRIES_COLL].find(
            {"report_id": report_id}, {"_id": 0}
        ).sort("ts", 1).limit(500)
        log = [d async for d in cursor]
        if not summary and not log:
            return {"report_id": report_id, "log": [], "last_action": None}
        return {**(summary or {"report_id": report_id}), "log": log}
