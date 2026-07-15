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
VISION_BATCH_SIZE = 6
VISION_MAX_CONCURRENCY = 3

_VISION_SYSTEM = (
    "You are a construction jobsite photo analyst supporting a Daily Job "
    "Report. Analyze the attached photo and report ONLY what is clearly "
    "visible. STRICT RULES:\n"
    "0. First determine whether the image is an eligible construction/jobsite/supporting-evidence photo. "
    "Screenshots, dashboards, browser windows, admin pages, chat UIs, and unrelated screen captures are NOT eligible. "
    "For those, set is_jobsite_photo=false, provide a short eligibility_reason, and return no operational observations.\n"
    "1. Describe the work in progress (paving, milling, forming, pouring, "
    "excavation, grading, hauling, etc.) as specifically as the image allows.\n"
    "2. Identify visible equipment (type, and unit numbers / brand names "
    "only if legible), visible crew activity and approximate crew count, "
    "visible materials, and site conditions.\n"
    "3. If the photo is a delivery / scale / material ticket, transcribe the "
    "legible fields into ticket_text (supplier, ticket number, material, "
    "quantity, date). If partially legible, transcribe only what is legible.\n"
    "4. NEVER invent quantities, activities, incidents, or safety violations "
    "that are not clearly visible.\n"
    "5. Return STRICT JSON only. No markdown, no preface."
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
    refs_by_sha: Dict[str, List[Dict[str, Any]]] = {}
    pending_unique: List[Dict[str, Any]] = []
    for p in photos:
        refs_by_sha.setdefault(p["sha"], []).append(p)
    for sha, grouped in refs_by_sha.items():
        representative = grouped[0]
        try:
            cached = await db[VISION_CACHE_COLL].find_one(
                {"photo_sha": sha}, {"_id": 0, "envelope": 1},
            )
        except Exception:  # noqa: BLE001
            cached = None
        if cached and cached.get("envelope"):
            results_by_sha[sha] = cached["envelope"]
        else:
            pending_unique.append(representative)

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

        async def _one(p: Dict[str, Any]):
            async with semaphore:
                env = await gw.dispatch_vision(
                    task="photo_vision",
                    system=_VISION_SYSTEM,
                    images=[p["b64"]],
                    user=user_body,
                    response_schema=_VISION_SCHEMA,
                    session_id=f"drv2-vision-{p['sha'][:12]}",
                )
                return p, env

        async def _run_batch(batch: List[Dict[str, Any]]):
            return await asyncio.gather(*[_one(p) for p in batch], return_exceptions=True)

        gathered = []
        for idx in range(0, len(pending_unique), VISION_BATCH_SIZE):
            batch = pending_unique[idx: idx + VISION_BATCH_SIZE]
            gathered.extend(await _run_batch(batch))
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
