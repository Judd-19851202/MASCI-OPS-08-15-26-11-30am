"""TRACK 26.12 · Inline draft-time photo vision for the DR AI summary.

Runs REAL vision analysis on the photos attached to a Daily Report
draft at generate time — before the narrative agent runs — so the
summary can cite what is actually in the photos. Per-photo results are
cached by content hash, so Regenerate never re-pays vision for
unchanged photos.

Gating: same DR_V2 path as the narrative (DR_V2_AI_ENABLED + a usable
provider key via the AI Gateway). Never raises — returns [] on any
failure so the summary still generates from typed fields.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import photo_storage

from services.ai_gateway import get_gateway

VISION_CACHE_COLL = "dr_v2_photo_vision_cache"
VISION_BATCH_SIZE = 24
VISION_MAX_CONCURRENCY = 8
VISION_RETRY_ATTEMPTS = 3
VISION_RETRY_BASE_DELAY_SECONDS = 0.75

_VISION_SYSTEM = (
    "You are a senior construction superintendent and forensic jobsite photo analyst "
    "supporting a Daily Job Report. Analyze the attached image and return ONLY what is "
    "clearly visible and operationally meaningful. STRICT RULES:\n"
    "0. First classify the image truthfully into one of these evidence types: "
    "jobsite_construction_photo, document_or_ticket_evidence, screenshot_or_ui_artifact, "
    "duplicate_image, or unsupported_or_ineligible. Screenshots, dashboards, browser windows, "
    "admin pages, chat UIs, and unrelated screen captures are NOT jobsite evidence. "
    "For those, set is_jobsite_photo=false, provide a short eligibility_reason, and return no "
    "operational observations.\n"
    "1. When the image is a genuine jobsite/construction photo, write like an elite field superintendent "
    "briefing a high-level PM. Focus on specific work activity, measurable progress, equipment in use, "
    "material placement, access conditions, traffic control, visible safety controls, visible "
    "quality concerns, and whether the photo supports or conflicts with the typed report. Extract the "
    "highest-value facts first.\n"
    "2. Be technically specific when the image supports it. Identify equipment by best-supported "
    "construction class first (excavator, skid steer, paver, roller, dump truck, loader, crane, "
    "concrete chute, pump hose, trench box, shoring, etc.). Mention manufacturer or model only if "
    "the marking is clearly legible. Capture unit numbers, placards, or fleet IDs if clearly visible. "
    "Do not guess. For example, say 'tracked excavator' unless 'John Deere', 'CAT 320', 'EXC-1934', or "
    "another marking is clearly readable.\n"
    "3. Prioritize project-critical extraction over generic description. Pull out material quantities, "
    "ticket quantities, station limits, curb footage, trench reach, load counts, safety control devices, "
    "workfront location, and measurable production clues whenever they are clearly visible.\n"
    "4. Do NOT waste summary value on low-signal trivia such as logos, colors, generic close-up "
    "descriptions, browser text, or statements like 'no workers visible' unless that absence is "
    "operationally meaningful.\n"
    "5. If the photo is a delivery / scale / material ticket, transcribe only the clearly legible "
    "fields into ticket_text (supplier, ticket number, material, quantity, date, load details). "
    "Do not infer missing text.\n"
    "6. NEVER invent quantities, completed work, incidents, violations, crew counts, or safety "
    "conditions that are not clearly visible.\n"
    "7. Observations must be short, technical, and PM-relevant. Prefer statements like: "
    "'Fresh concrete is being discharged through a chute into the work area', "
    "'curb alignment is visible along the trench line', "
    "'traffic-control drums separate the live lane from the work zone', "
    "'standing water is visible in the excavation', "
    "'equipment is staged but no active placement is visible in this frame'.\n"
    "8. Return STRICT JSON only. No markdown, no preface."
)

_VISION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["narrative", "confidence", "observations", "is_jobsite_photo", "eligibility_reason"],
    "properties": {
        "narrative": {"type": "string", "maxLength": 600,
                      "description": "One-to-three sentence factual summary of what the photo shows"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "is_jobsite_photo": {"type": "boolean"},
        "eligibility_reason": {"type": "string", "maxLength": 240},
        "observations": {"type": "array", "maxItems": 8,
                         "items": {"type": "string", "maxLength": 240},
                         "description": "Short grounded facts visible in the photo"},
        "ticket_text": {"type": "string", "maxLength": 400,
                        "description": "Transcription if the photo is a ticket/document, else empty string"},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
        "sources_used": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _b64_of(entry: Any) -> Optional[str]:
    """Extract raw base64 (no data: prefix) from a photo entry."""
    if isinstance(entry, dict):
        entry = entry.get("dataUrl") or entry.get("data_url") or entry.get("data") or entry.get("base64") or ""
    if not isinstance(entry, str) or not entry:
        return None
    if entry.startswith("data:"):
        idx = entry.find(";base64,")
        if idx == -1:
            return None
        return entry[idx + 8:]
    # Raw base64 string (heuristic: long and no URL scheme)
    if len(entry) > 1000 and "://" not in entry[:16]:
        return entry
    return None  # storage refs / URLs — handled by the post-submit pipeline


async def _b64_of_async(entry: Any) -> Optional[str]:
    b64 = _b64_of(entry)
    if b64:
        return b64
    if isinstance(entry, str) and entry.startswith("photo://"):
        try:
            data_url = photo_storage.resolve_to_data_url_sync(entry)
        except Exception:  # noqa: BLE001
            return None
        if isinstance(data_url, str) and data_url.startswith("data:"):
            idx = data_url.find(";base64,")
            if idx != -1:
                return data_url[idx + 8:]
    return None


async def extract_draft_photos(draft: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect analyzable base64 photos from every place the DR form
    attaches them: top-level photos[], material ticket photos, and
    subcontractor photos."""
    captions = draft.get("photo_captions") or []
    out: List[Dict[str, Any]] = []

    async def _add(entry: Any, ref: str, source: str, caption: str = "") -> None:
        b64 = await _b64_of_async(entry)
        if not b64:
            return
        sha = hashlib.sha256(b64.encode("ascii", "ignore")).hexdigest()
        out.append({"ref": ref, "b64": b64, "sha": sha, "source": source,
                    "caption": (caption or "")[:240]})

    for i, p in enumerate(draft.get("photos") or []):
        cap = captions[i] if i < len(captions) and isinstance(captions[i], str) else ""
        await _add(p, f"photo:{i}", "report_photos", cap)
    for mi, m in enumerate(draft.get("materials") or []):
        if isinstance(m, dict):
            for ti, tp in enumerate(m.get("ticket_photos") or []):
                await _add(tp, f"material:{mi}:ticket:{ti}", "material_ticket",
                           str(m.get("material") or ""))
    for si, s in enumerate(draft.get("subcontractors") or []):
        if isinstance(s, dict):
            for pi, sp in enumerate(s.get("photos") or []):
                await _add(sp, f"sub:{si}:photo:{pi}", "subcontractor",
                           str(s.get("company") or ""))
    return out


def _compact_context(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Tiny grounding context so the vision model can relate photos to
    the supervisor's entries (never large enough to matter for tokens)."""
    acts = [str((a or {}).get("description") or (a or {}).get("text") or "")[:120]
            for a in (draft.get("activity_cards") or [])[:6] if isinstance(a, dict)]
    mats = [str((m or {}).get("material") or "")[:60]
            for m in (draft.get("materials") or [])[:6] if isinstance(m, dict)]
    subs = [str((s or {}).get("company") or "")[:60]
            for s in (draft.get("subcontractors") or [])[:6] if isinstance(s, dict)]
    return {
        "project": str(draft.get("project_name") or "")[:120],
        "project_number": str(draft.get("project_number") or "")[:40],
        "date": str(draft.get("report_date") or "")[:20],
        "activities": [a for a in acts if a],
        "materials": [m for m in mats if m],
        "subcontractors": [s for s in subs if s],
    }


def _to_observation(photo: Dict[str, Any], envelope: Dict[str, Any]) -> Dict[str, Any]:
    obs = {
        "photo_ref": photo["ref"],
        "source": photo["source"],
        "summary": str(envelope.get("summary") or "")[:600],
        "observations": [str(x)[:240] for x in (envelope.get("observations") or [])][:8],
        "confidence": float(envelope.get("confidence") or 0.0),
        "is_jobsite_photo": bool(envelope.get("is_jobsite_photo", True)),
        "eligibility_reason": str(envelope.get("eligibility_reason") or "")[:240],
    }
    if photo.get("caption"):
        obs["caption"] = photo["caption"]
    if envelope.get("ticket_text"):
        obs["ticket_text"] = str(envelope["ticket_text"])[:400]
    return obs


async def _ensure_cache_index(db) -> None:
    try:
        await db[VISION_CACHE_COLL].create_index(
            "photo_sha", unique=True, name="dr_v2_photo_vision_sha",
        )
    except Exception:  # noqa: BLE001
        pass


async def analyze_draft_photos(db, *, report_id: str, draft: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze every photo attached to the draft. Cached per photo
    content hash. Returns a list of grounded observation dicts for the
    evidence bundle's `photo_observations`. Never raises."""
    try:
        photos = await extract_draft_photos(draft)
    except Exception:  # noqa: BLE001
        return []
    if not photos:
        return []

    await _ensure_cache_index(db)

    results_by_sha: Dict[str, Dict[str, Any]] = {}
    pending_unique: List[Dict[str, Any]] = []
    seen_input_shas: set[str] = set()
    for p in photos:
        if p["sha"] in seen_input_shas:
            continue
        seen_input_shas.add(p["sha"])
        try:
            cached = await db[VISION_CACHE_COLL].find_one(
                {"photo_sha": p["sha"]}, {"_id": 0, "envelope": 1},
            )
        except Exception:  # noqa: BLE001
            cached = None
        if cached and cached.get("envelope"):
            results_by_sha[p["sha"]] = cached["envelope"]
        else:
            pending_unique.append(p)

    if pending_unique:
        gw = get_gateway()
        context = _compact_context(draft)
        user_body = (
            "Report context (json):\n"
            + json.dumps(context, sort_keys=True, ensure_ascii=False)
            + "\n\nAnalyze the attached jobsite photo. If it is a delivery or "
            "scale ticket, transcribe legible fields into ticket_text."
        )

        semaphore = asyncio.Semaphore(VISION_MAX_CONCURRENCY)
        timeout_s = 25.0

        async def _dispatch_with_retry(p: Dict[str, Any]):
            last_exc = None
            for attempt in range(1, VISION_RETRY_ATTEMPTS + 1):
                try:
                    return await asyncio.wait_for(
                        gw.dispatch_vision(
                            task="photo_vision",
                            system=_VISION_SYSTEM,
                            images=[p["b64"]],
                            user=user_body,
                            response_schema=_VISION_SCHEMA,
                            session_id=f"drv2-vision-{p['sha'][:12]}",
                        ),
                        timeout=timeout_s,
                    )
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt >= VISION_RETRY_ATTEMPTS:
                        raise
                    await asyncio.sleep(VISION_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)))
            raise last_exc  # pragma: no cover

        async def _one(p: Dict[str, Any]):
            async with semaphore:
                env = await _dispatch_with_retry(p)
                return p, env

        gathered = await asyncio.gather(*[_one(p) for p in pending_unique], return_exceptions=True)
        for item in gathered:
            if isinstance(item, BaseException):
                continue
            p, env = item
            if not getattr(env, "ai_available", False):
                continue
            raw = getattr(env, "raw", None) or {}
            envelope = {
                "summary": (getattr(env, "narrative", "") or "")[:600],
                "observations": [str(x)[:240] for x in (raw.get("observations") or [])][:8],
                "ticket_text": str(raw.get("ticket_text") or "")[:400],
                "confidence": float(getattr(env, "confidence", 0.0) or 0.0),
                "is_jobsite_photo": bool(raw.get("is_jobsite_photo", True)),
                "eligibility_reason": str(raw.get("eligibility_reason") or "")[:240],
            }
            try:
                await db[VISION_CACHE_COLL].update_one(
                    {"photo_sha": p["sha"]},
                    {"$set": {
                        "photo_sha": p["sha"],
                        "envelope": envelope,
                        "provider": getattr(env, "provider", "") or "",
                        "model": getattr(env, "model", "") or "",
                        "report_id": report_id,
                        "created_at": _now_iso(),
                    }},
                    upsert=True,
                )
            except Exception:  # noqa: BLE001
                pass
            results_by_sha[p["sha"]] = envelope

    ordered_results: List[Dict[str, Any]] = []
    seen_sha: set[str] = set()
    for p in photos:
        envelope = results_by_sha.get(p["sha"])
        if not envelope:
            ordered_results.append(
                {
                    "photo_ref": p["ref"],
                    "source": p["source"],
                    "summary": "",
                    "observations": [],
                    "confidence": 0.0,
                    "is_jobsite_photo": False,
                    "eligibility_reason": "analysis_unavailable_for_this_photo",
                    "duplicate_reused": False,
                }
            )
            continue
        obs = _to_observation(p, envelope)
        if not obs.get("is_jobsite_photo", True):
            obs["summary"] = ""
            obs["observations"] = []
        if p["sha"] in seen_sha:
            obs["duplicate_reused"] = True
        else:
            seen_sha.add(p["sha"])
            obs["duplicate_reused"] = False
        ordered_results.append(obs)

    return ordered_results


__all__ = ["analyze_draft_photos", "extract_draft_photos", "VISION_CACHE_COLL"]
