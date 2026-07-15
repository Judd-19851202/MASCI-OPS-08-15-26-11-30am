"""TRACK 22.9B · V1 Daily Report Photo Intelligence Pipeline.

Async, non-blocking wiring of the existing photo analyzer into the V1
Daily Report submit workflow. Uses `dr_v2_photo_intelligence` as the
single storage system (no duplicate storage) and adds a job control
document per (report_id, photo_id) so a reconciler loop can pick up
anything the request-scope BackgroundTasks lost due to a pod restart
or a transient failure.

Doctrine
--------
- Photo analysis MUST NOT block DR submit, upload, or summary render.
- Every failure is logged/audited; nothing surfaces as a scary error
  in the field UI.
- Idempotent: never analyzes the same (report_id, photo_ref) twice —
  the store keys on (report_id, photo_id) with a unique index.
- Grounded only: the analyzer prompt is already strict ("NEVER invent
  quantities…"). This module never fabricates observations of its own.
- V1 only: reads from `daily_reports` collection. The V2 shell is not
  resurrected.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from services.ai_gateway import get_gateway
from services.ai_gateway.capabilities import resolve_ai_capabilities

from .analyzer import analyze_photo, evidence_hash_for_photo
from .store import COLL_PHOTO_INTEL, get_intel, upsert_intel


logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────

COLL_INTEL_JOBS = "dr_v1_photo_intel_jobs"
TENANT_DEFAULT = "masci"

# Reconciler cadence and retry policy.
RECONCILER_INTERVAL_S = 60          # scan every ~60 s
RECONCILER_STALE_AFTER_S = 90       # in_progress claim expires after 90 s
RECONCILER_BATCH_LIMIT = 8          # cap per pass so we never hog CPU
JOB_MAX_ATTEMPTS = 5                # after which the job is marked terminal

# Feature flag guardrail — module-level check so BackgroundTasks
# cost nothing when photo intelligence is intentionally off.
_MODULE = "photo_intelligence"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime] = None) -> str:
    return (dt or _now()).isoformat()


# ── Photo ref helpers ────────────────────────────────────────────────

def _photo_id_for(ref: Any) -> Optional[str]:
    """Stable per-photo id.

    For `photo://` refs the key path is unique, so we hash it to keep
    Mongo doc keys short and to avoid slashes in dotted paths.
    For legacy base64 data URLs we hash the payload.
    For dicts we prefer explicit id/key.
    """
    if isinstance(ref, dict):
        for k in ("id", "key", "ref", "url"):
            v = ref.get(k)
            if v:
                return hashlib.sha1(str(v).encode("utf-8")).hexdigest()[:20]
        return None
    if isinstance(ref, str) and ref:
        if ref.startswith("data:"):
            return "b64_" + hashlib.sha1(ref.encode("utf-8")).hexdigest()[:20]
        return hashlib.sha1(ref.encode("utf-8")).hexdigest()[:20]
    return None


def _extract_data_url_b64(ref: str) -> Optional[str]:
    if not isinstance(ref, str) or not ref.startswith("data:"):
        return None
    idx = ref.find(";base64,")
    if idx == -1:
        return None
    b64 = ref[idx + 8 :].strip()
    return b64 or None


def _extract_photo_refs(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a de-duped list of `{photo_id, ref}` items for every photo
    attached to a V1 daily_reports doc (top-level, subs, materials)."""
    seen: set = set()
    out: List[Dict[str, Any]] = []

    def _walk(items: Any, source_hint: str) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            pid = _photo_id_for(item)
            if not pid or pid in seen:
                continue
            seen.add(pid)
            # Preserve original ref for later reads.
            if isinstance(item, dict):
                ref = item.get("ref") or item.get("url") or item.get("key") or ""
            else:
                ref = str(item)
            if not ref:
                continue
            out.append({"photo_id": pid, "ref": ref, "source": source_hint})

    _walk(report.get("photos"), "photos")
    for sub in (report.get("subcontractors") or []):
        if isinstance(sub, dict):
            _walk(sub.get("photos"), "sub_photos")
    for mat in (report.get("materials") or []):
        if isinstance(mat, dict):
            _walk(mat.get("ticket_photos"), "material_photos")
    return out


def _extract_draft_photo_batches(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Draft-specific photo collector with stable ids plus compact refs
    that line up with the cached draft vision path."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    captions = report.get("photo_captions") or []

    def _add(entry: Any, *, source_hint: str, vision_ref: str, caption: str = "") -> None:
        pid = _photo_id_for(entry)
        if not pid or pid in seen:
            return
        if isinstance(entry, dict):
            raw_ref = (
                entry.get("ref")
                or entry.get("url")
                or entry.get("key")
                or entry.get("dataUrl")
                or entry.get("data_url")
                or entry.get("data")
                or entry.get("base64")
                or ""
            )
        else:
            raw_ref = str(entry or "")
        if not raw_ref:
            return
        b64 = _extract_data_url_b64(raw_ref)
        if not b64 and len(raw_ref) > 1000 and "://" not in raw_ref[:16]:
            b64 = raw_ref
        seen.add(pid)
        out.append(
            {
                "photo_id": pid,
                "ref": raw_ref,
                "source": source_hint,
                "vision_ref": vision_ref,
                "caption": (caption or "")[:240],
                "photo_sha": hashlib.sha256((b64 or raw_ref).encode("utf-8", "ignore")).hexdigest(),
            }
        )

    for idx, entry in enumerate(report.get("photos") or []):
        cap = captions[idx] if idx < len(captions) and isinstance(captions[idx], str) else ""
        _add(entry, source_hint="photos", vision_ref=f"photo:{idx}", caption=cap)
    for mi, mat in enumerate(report.get("materials") or []):
        if not isinstance(mat, dict):
            continue
        for ti, entry in enumerate(mat.get("ticket_photos") or []):
            _add(
                entry,
                source_hint="material_photos",
                vision_ref=f"material:{mi}:ticket:{ti}",
                caption=str(mat.get("material") or "")[:240],
            )
    for si, sub in enumerate(report.get("subcontractors") or []):
        if not isinstance(sub, dict):
            continue
        for pi, entry in enumerate(sub.get("photos") or []):
            _add(
                entry,
                source_hint="sub_photos",
                vision_ref=f"sub:{si}:photo:{pi}",
                caption=str(sub.get("company") or "")[:240],
            )
    return out


def _normalize_operator_photo_status(summary: Dict[str, Any]) -> str:
    total = int(summary.get("photo_count") or 0)
    uploading = int(summary.get("uploading") or 0)
    queued = int(summary.get("queued") or 0)
    processing = int(summary.get("processing") or 0)
    completed = int(summary.get("completed") or 0)
    completed_no_obs = int(summary.get("completed_no_observations") or 0)
    duplicates = int(summary.get("duplicates_reused") or 0)
    failed = int(summary.get("failed") or 0)
    terminal = int(summary.get("terminal_failures") or 0)
    unavailable = int(summary.get("unavailable") or 0)
    ineligible = int(summary.get("ineligible") or 0)
    suppressed = int(summary.get("suppressed") or 0)

    accounted = completed + completed_no_obs + duplicates + terminal + unavailable + ineligible + suppressed
    if total <= 0:
        return "no_photos"
    if uploading > 0:
        return "uploading"
    if queued > 0 and completed == 0 and processing == 0:
        return "queued"
    if processing > 0 and accounted == 0:
        return "analyzing"
    if processing > 0 or queued > 0:
        return "partially_analyzed"
    if accounted >= total and failed == 0 and terminal == 0 and unavailable == 0:
        return "complete"
    if accounted >= total and (failed > 0 or terminal > 0 or unavailable > 0):
        return "complete_with_some_failures"
    if accounted > 0:
        return "partially_analyzed"
    return "analysis_unavailable"


def _operator_status_message(summary: Dict[str, Any]) -> str:
    total = int(summary.get("photo_count") or 0)
    queued = int(summary.get("queued") or 0)
    processing = int(summary.get("processing") or 0)
    reviewed = int(summary.get("reviewed") or 0)
    terminal = int(summary.get("terminal_failures") or 0)
    unavailable = int(summary.get("unavailable") or 0)
    state = str(summary.get("status") or "")
    if state == "no_photos":
        return "No photos attached yet."
    if state == "uploading":
        return f"Uploading {total} photos…"
    if state == "queued":
        return f"Queued {total} photos for analysis."
    if state == "analyzing":
        return f"Analyzing {reviewed} of {total} photos…"
    if state == "partially_analyzed":
        return f"Analyzed {reviewed} of {total} photos so far."
    if state == "complete":
        return f"Photo analysis complete — {total} photos reviewed."
    if state == "complete_with_some_failures":
        missed = max(0, terminal + unavailable)
        return f"{reviewed} of {total} photos analyzed — {missed} could not be processed."
    return "Photo analysis unavailable — your report data is safe."


def _draft_context_from_v1(report: Dict[str, Any]) -> Dict[str, Any]:
    """Compact grounded context for the vision model — supervisor-entered
    items only. Deliberately small so latency + tokens stay low."""
    return {
        "activity_cards": [
            {
                "id": a.get("row_id") or a.get("id"),
                "activity": a.get("description") or a.get("activity") or a.get("name"),
                "area": a.get("location") or a.get("area"),
                "qty": a.get("quantity"),
                "unit": a.get("unit"),
            }
            for a in (report.get("production") or report.get("activities") or [])[:20]
            if isinstance(a, dict)
        ],
        "constraint_cards": [
            {
                "id": c.get("row_id") or c.get("id"),
                "type": c.get("constraint_type") or c.get("type"),
                "note": c.get("notes") or c.get("reason") or c.get("note"),
            }
            for c in (report.get("constraints") or [])[:20]
            if isinstance(c, dict)
        ],
        "equipment_used": [
            {
                "unit": e.get("unit") or e.get("label"),
                "hours": e.get("hours"),
            }
            for e in (report.get("equipment") or [])[:20]
            if isinstance(e, dict)
        ],
        "masci_crews": [
            {
                "crew": c.get("trade") or c.get("crew"),
                "count": c.get("count") or 1,
            }
            for c in (report.get("masci_crews") or [])[:10]
            if isinstance(c, dict)
        ],
        "materials": [
            {
                "material": m.get("material") or m.get("name"),
                "supplier": m.get("supplier"),
            }
            for m in (report.get("materials") or [])[:10]
            if isinstance(m, dict)
        ],
    }


# ── Job control ──────────────────────────────────────────────────────

async def ensure_indexes(db) -> None:
    """Set up job control indexes. Called from lifecycle bootstrap."""
    try:
        await db[COLL_INTEL_JOBS].create_index(
            [("report_id", 1), ("photo_id", 1)],
            unique=True,
            name="dr_v1_intel_job_key",
        )
        await db[COLL_INTEL_JOBS].create_index(
            [("status", 1), ("next_attempt_at", 1)],
            name="dr_v1_intel_job_schedule",
        )
    except Exception:  # noqa: BLE001 — index creation is best-effort
        pass


async def enqueue_report(db, report: Dict[str, Any]) -> Dict[str, Any]:
    """Insert one pending job per attached photo.

    Idempotent: repeated calls with the same report doc leave existing
    jobs untouched (the composite unique index prevents duplicates).
    Returns a small summary the caller can log.
    """
    doc_id = (
        report.get("doc_id")
        or report.get("report_number")
        or report.get("id")
        or ""
    )
    if not doc_id:
        return {"ok": False, "reason": "no_doc_id", "enqueued": 0}

    project_id = (
        report.get("project_number") or report.get("project_id") or ""
    )
    date = report.get("report_date") or ""

    refs = _extract_photo_refs(report)
    if not refs:
        return {"ok": True, "enqueued": 0, "photos": 0}

    now = _iso()
    enqueued = 0
    for ref in refs:
        try:
            res = await db[COLL_INTEL_JOBS].update_one(
                {"report_id": doc_id, "photo_id": ref["photo_id"]},
                {
                    "$setOnInsert": {
                        "report_id": doc_id,
                        "photo_id": ref["photo_id"],
                        "photo_ref": ref["ref"],
                        "source": ref.get("source"),
                        "project_id": project_id,
                        "date": date,
                        "tenant_id": TENANT_DEFAULT,
                        "status": "pending",
                        "attempts": 0,
                        "created_at": now,
                        "next_attempt_at": now,
                    }
                },
                upsert=True,
            )
            if getattr(res, "upserted_id", None):
                enqueued += 1
        except Exception:  # noqa: BLE001
            # Duplicate-key or transient — always safe to ignore, reconciler
            # will find the row anyway.
            pass
    return {"ok": True, "enqueued": enqueued, "photos": len(refs)}


# ── Analysis ─────────────────────────────────────────────────────────

async def _read_photo_bytes_b64(ref: str) -> Optional[str]:
    """Load photo bytes and encode as base64 for the vision adapter.

    Returns None on any failure — the reconciler will retry the job.
    We deliberately keep this best-effort: R2 hiccups must never blow
    up the pipeline.
    """
    if not ref:
        return None
    inline_b64 = _extract_data_url_b64(ref)
    if inline_b64:
        return inline_b64
    try:
        # Local import — photo_storage may not be configured in tests.
        import base64 as _b64  # noqa: PLC0415
        from photo_storage import read_photo_bytes  # noqa: PLC0415
        raw = await read_photo_bytes(ref)
        if not raw:
            return None
        return _b64.b64encode(raw).decode("ascii")
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[photo-intel] read failed for %s: %s", (ref or "")[:60], exc,
        )
        return None


async def _claim_job(
    db,
    *,
    report_id: str,
    photo_id: str,
    allowed_statuses: Sequence[str] = ("pending", "failed"),
) -> bool:
    try:
        claim = await db[COLL_INTEL_JOBS].update_one(
            {
                "report_id": report_id,
                "photo_id": photo_id,
                "status": {"$in": list(allowed_statuses)},
            },
            {"$set": {"status": "in_progress", "claim_at": _iso()}},
        )
        return bool(getattr(claim, "matched_count", 0))
    except Exception:  # noqa: BLE001
        return False


async def _analyze_one(
    db,
    *,
    report_id: str,
    photo_id: str,
    photo_ref: str,
    project_id: str,
    date: str,
    draft_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Run a single photo through the analyzer + upsert the intel row.

    Never raises — returns a small result envelope so the caller can
    update the job record.
    """
    started = _now()

    # Capability check per call so a runtime flag flip is honored.
    try:
        cap = await resolve_ai_capabilities(db, TENANT_DEFAULT, _MODULE)
    except Exception:  # noqa: BLE001
        cap = None
    tenant_gate_only = bool(
        cap
        and not cap.enabled
        and getattr(cap, "reason_disabled", "") == "tenant_ai_disabled"
        and str(report_id or "").startswith("daily-report::")
    )

    ctx_hash = hashlib.sha256(
        json.dumps(draft_context, sort_keys=True).encode("utf-8")
    ).hexdigest()
    b64: Optional[str] = None
    # Only pay the R2 read cost if AI is actually available. If disabled
    # we still write a placeholder intel row so consumers see a stable
    # shape (`analysis_status="unavailable"`).
    if (cap and cap.enabled) or tenant_gate_only:
        b64 = await _read_photo_bytes_b64(photo_ref)

    photo_hash = evidence_hash_for_photo(
        photo_ref=photo_ref,
        photo_bytes_b64=b64,
        draft_context_hash=ctx_hash,
    )

    # Cheap skip: if we've already stored intel for this exact
    # (photo bytes, draft context), do nothing.
    prior = await get_intel(db, report_id=report_id, photo_id=photo_id)
    if prior and prior.get("evidence_hash") == photo_hash:
        return {
            "ok": True, "cached": True,
            "ai_available": prior.get("analysis_status") == "complete",
            "duration_ms": 0,
        }

    if cap and not cap.enabled and not tenant_gate_only:
        # AI off — persist a placeholder so the UI can render "photo
        # intelligence unavailable" without polling forever.
        env_dict = {
            "ai_available": False,
            "fallback_reason": (getattr(cap, "reason_disabled", None)
                                or "photo_intelligence_disabled"),
            "narrative": "",
            "confidence": 0.0,
            "observations": [],
            "suggested_links": [],
            "questions": [],
            "conflicts": [],
        }
        await upsert_intel(
            db,
            report_id=report_id, photo_id=photo_id,
            project_id=project_id, tenant_id=TENANT_DEFAULT,
            evidence_hash=photo_hash, envelope=env_dict,
            provider="gateway", model="",
        )
        return {"ok": True, "cached": False, "ai_available": False, "duration_ms": 0}

    if b64 is None:
        # Bytes unreadable — surface via job status so reconciler retries.
        return {"ok": False, "cached": False, "reason": "photo_unreadable"}

    gw = get_gateway()
    images = [{"content_type": "image/jpeg", "file_content_base64": b64}]
    try:
        env = await analyze_photo(
            gateway=gw,
            session_id=f"drv1-photo-{photo_id}",
            photo_ref=photo_ref,
            images=images,
            draft_context=draft_context,
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("[photo-intel] analyzer failed for %s: %s", photo_id, exc)
        return {"ok": False, "cached": False, "reason": f"analyzer_error:{exc.__class__.__name__}"}

    env_dict = env.to_dict() if hasattr(env, "to_dict") else dict(env or {})
    env_dict["raw"] = getattr(env, "raw", {}) or {}

    await upsert_intel(
        db,
        report_id=report_id, photo_id=photo_id,
        project_id=project_id, tenant_id=TENANT_DEFAULT,
        evidence_hash=photo_hash, envelope=env_dict,
        provider=getattr(env, "provider", "") or "",
        model=getattr(env, "model", "") or "",
    )
    duration_ms = int((_now() - started).total_seconds() * 1000)
    return {
        "ok": True,
        "cached": False,
        "ai_available": bool(env_dict.get("ai_available")),
        "duration_ms": duration_ms,
    }


async def _mark_job(
    db, *, report_id: str, photo_id: str, status: str, note: str = "",
    increment_attempts: bool = True,
) -> None:
    now = _iso()
    update: Dict[str, Any] = {
        "$set": {
            "status": status,
            "updated_at": now,
            "last_note": (note or "")[:400],
        },
    }
    if increment_attempts:
        update["$inc"] = {"attempts": 1}
        update["$set"]["last_attempt_at"] = now
    if status == "failed":
        # Exponential-ish backoff for reconciler retries.
        update["$set"]["next_attempt_at"] = (
            _now() + timedelta(seconds=60 * 2)
        ).isoformat()
    if status in ("complete", "unavailable", "terminal"):
        update["$set"]["completed_at"] = now
    try:
        await db[COLL_INTEL_JOBS].update_one(
            {"report_id": report_id, "photo_id": photo_id}, update,
        )
    except Exception:  # noqa: BLE001
        pass


async def process_report(db, report: Dict[str, Any]) -> Dict[str, Any]:
    """First-pass analysis for a freshly submitted report.

    Meant to be invoked from FastAPI `BackgroundTasks`. Never raises.
    Every photo is enqueued (so the reconciler owns the retry contract)
    and then analyzed inline. If a photo fails here, the job row stays
    with `status="failed"` and `next_attempt_at` in the near future —
    the reconciler picks it up.
    """
    try:
        doc_id = (
            report.get("doc_id")
            or report.get("report_number")
            or report.get("id")
            or ""
        )
        if not doc_id:
            return {"ok": False, "reason": "no_doc_id"}
        await enqueue_report(db, report)

        refs = _extract_photo_refs(report)
        if not refs:
            return {"ok": True, "photos": 0}

        ctx = _draft_context_from_v1(report)
        project_id = report.get("project_number") or report.get("project_id") or ""
        date = report.get("report_date") or ""
        completed = 0
        failed = 0
        for ref in refs:
            # Skip anything already marked complete.
            prior = await db[COLL_INTEL_JOBS].find_one(
                {"report_id": doc_id, "photo_id": ref["photo_id"]},
                {"_id": 0, "status": 1},
            )
            if prior and prior.get("status") == "complete":
                continue
            claimed = await _claim_job(
                db,
                report_id=doc_id,
                photo_id=ref["photo_id"],
                allowed_statuses=("pending", "failed", "unavailable"),
            )
            if not claimed:
                continue
            res = await _analyze_one(
                db,
                report_id=doc_id,
                photo_id=ref["photo_id"],
                photo_ref=ref["ref"],
                project_id=project_id,
                date=date,
                draft_context=ctx,
            )
            if res.get("ok"):
                status = "complete" if res.get("ai_available") else "unavailable"
                await _mark_job(
                    db, report_id=doc_id, photo_id=ref["photo_id"],
                    status=status,
                    note=res.get("reason") or "",
                )
                completed += 1
            else:
                await _mark_job(
                    db, report_id=doc_id, photo_id=ref["photo_id"],
                    status="failed", note=res.get("reason") or "unknown",
                )
                failed += 1
        return {
            "ok": True, "photos": len(refs),
            "completed": completed, "failed": failed,
        }
    except Exception as exc:  # noqa: BLE001
        logger.info("[photo-intel] process_report crashed: %s", exc)
        return {"ok": False, "reason": f"crash:{exc.__class__.__name__}"}


async def enqueue_draft(db, draft_identity: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    draft_identity = str(draft_identity or "").strip()
    if not draft_identity:
        return {"ok": False, "reason": "no_draft_identity", "enqueued": 0}

    refs = _extract_photo_refs(draft)
    if not refs:
        return {"ok": True, "enqueued": 0, "photos": 0}

    project_id = draft.get("project_number") or draft.get("project_id") or ""
    date = draft.get("report_date") or ""
    now = _iso()
    enqueued = 0
    for ref in refs:
        try:
            existing = await db[COLL_INTEL_JOBS].find_one(
                {"report_id": draft_identity, "photo_id": ref["photo_id"]},
                {"_id": 0, "report_id": 1, "photo_id": 1, "status": 1},
            )
            if existing:
                await db[COLL_INTEL_JOBS].update_one(
                    {"report_id": draft_identity, "photo_id": ref["photo_id"]},
                    {
                        "$set": {
                            "photo_ref": ref["ref"],
                            "source": ref.get("source"),
                            "project_id": project_id,
                            "date": date,
                            "draft_mode": True,
                            "updated_at": now,
                        }
                    },
                )
                continue
            await db[COLL_INTEL_JOBS].insert_one(
                {
                    "report_id": draft_identity,
                    "photo_id": ref["photo_id"],
                    "photo_ref": ref["ref"],
                    "source": ref.get("source"),
                    "project_id": project_id,
                    "date": date,
                    "tenant_id": TENANT_DEFAULT,
                    "status": "pending",
                    "attempts": 0,
                    "created_at": now,
                    "next_attempt_at": now,
                    "draft_mode": True,
                }
            )
            enqueued += 1
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True, "enqueued": enqueued, "photos": len(refs)}


async def process_draft(db, *, draft_identity: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from services.dr_ai.vision import analyze_draft_photos  # noqa: PLC0415

        draft_identity = str(draft_identity or "").strip()
        if not draft_identity:
            return {"ok": False, "reason": "no_draft_identity"}

        await enqueue_draft(db, draft_identity, draft)
        refs = _extract_draft_photo_batches(draft)
        if not refs:
            return {"ok": True, "photos": 0, "completed": 0, "failed": 0}

        ctx = _draft_context_from_v1(draft)
        ctx_hash = hashlib.sha256(
            json.dumps(ctx, sort_keys=True).encode("utf-8")
        ).hexdigest()
        project_id = draft.get("project_number") or draft.get("project_id") or ""
        completed = 0
        failed = 0
        skipped = 0
        observations = await analyze_draft_photos(
            db,
            report_id=draft_identity,
            draft=draft,
        )
        obs_by_ref = {
            str(item.get("photo_ref") or ""): item
            for item in observations
            if isinstance(item, dict) and item.get("photo_ref")
        }
        for ref in refs:
            prior = await db[COLL_INTEL_JOBS].find_one(
                {"report_id": draft_identity, "photo_id": ref["photo_id"]},
                {"_id": 0, "status": 1},
            )
            if prior and prior.get("status") in {"complete", "duplicate_reused", "unavailable", "terminal"}:
                skipped += 1
                continue
            claimed = await _claim_job(
                db,
                report_id=draft_identity,
                photo_id=ref["photo_id"],
                allowed_statuses=("pending", "failed", "unavailable"),
            )
            if not claimed:
                skipped += 1
                continue
            obs = obs_by_ref.get(ref.get("vision_ref") or "")
            if obs:
                obs_conf = float(obs.get("confidence") or 0.0)
                duplicate_reused = bool(obs.get("duplicate_reused"))
                is_jobsite_photo = bool(obs.get("is_jobsite_photo", True))
                raw_obs = [
                    {
                        "label": (ref.get("caption") or ref.get("source") or "photo observation")[:80],
                        "description": str(text)[:240],
                        "confidence": obs_conf,
                        "category": "site",
                        "requires_supervisor_confirmation": True,
                    }
                    for text in (obs.get("observations") or [])
                    if str(text or "").strip()
                ]
                if not is_jobsite_photo:
                    await upsert_intel(
                        db,
                        report_id=draft_identity,
                        photo_id=ref["photo_id"],
                        project_id=project_id,
                        tenant_id=TENANT_DEFAULT,
                        evidence_hash=evidence_hash_for_photo(
                            photo_ref=ref["ref"],
                            photo_bytes_b64=_extract_data_url_b64(ref["ref"]),
                            draft_context_hash=ctx_hash,
                        ),
                        envelope={
                            "ai_available": True,
                            "narrative": "",
                            "confidence": obs_conf,
                            "observations": [],
                            "suggested_links": [],
                            "questions": [],
                            "conflicts": [],
                            "raw": {"observations": []},
                            "fallback_reason": str(obs.get("eligibility_reason") or "ineligible_non_jobsite_photo")[:240],
                        },
                        provider="openai",
                        model="gpt-5.4",
                    )
                    await _mark_job(
                        db,
                        report_id=draft_identity,
                        photo_id=ref["photo_id"],
                        status="ineligible",
                        note=str(obs.get("eligibility_reason") or "ineligible_non_jobsite_photo")[:240],
                        increment_attempts=False,
                    )
                    completed += 1
                    continue
                if not raw_obs and obs.get("summary"):
                    raw_obs = [
                        {
                            "label": (ref.get("caption") or ref.get("source") or "photo summary")[:80],
                            "description": str(obs.get("summary") or "")[:240],
                            "confidence": obs_conf,
                            "category": "site",
                            "requires_supervisor_confirmation": True,
                        }
                    ]
                await upsert_intel(
                    db,
                    report_id=draft_identity,
                    photo_id=ref["photo_id"],
                    project_id=project_id,
                    tenant_id=TENANT_DEFAULT,
                    evidence_hash=evidence_hash_for_photo(
                        photo_ref=ref["ref"],
                        photo_bytes_b64=_extract_data_url_b64(ref["ref"]),
                        draft_context_hash=ctx_hash,
                    ),
                    envelope={
                        "ai_available": True,
                        "narrative": str(obs.get("summary") or "")[:600],
                        "confidence": obs_conf,
                        "observations": raw_obs,
                        "suggested_links": [],
                        "questions": [],
                        "conflicts": [],
                        "raw": {"observations": raw_obs},
                    },
                    provider="openai",
                    model="gpt-5.4",
                )
                await _mark_job(
                    db,
                    report_id=draft_identity,
                    photo_id=ref["photo_id"],
                    status="duplicate_reused" if duplicate_reused else "complete",
                    note="draft_cached_vision_duplicate" if duplicate_reused else "draft_cached_vision",
                )
                completed += 1
            else:
                await upsert_intel(
                    db,
                    report_id=draft_identity,
                    photo_id=ref["photo_id"],
                    project_id=project_id,
                    tenant_id=TENANT_DEFAULT,
                    evidence_hash=evidence_hash_for_photo(
                        photo_ref=ref["ref"],
                        photo_bytes_b64=_extract_data_url_b64(ref["ref"]),
                        draft_context_hash=ctx_hash,
                    ),
                    envelope={
                        "ai_available": False,
                        "fallback_reason": "draft_photo_observation_unavailable",
                        "narrative": "",
                        "confidence": 0.0,
                        "observations": [],
                        "suggested_links": [],
                        "questions": [],
                        "conflicts": [],
                        "raw": {"observations": []},
                    },
                    provider="openai",
                    model="gpt-5.4",
                )
                await _mark_job(
                    db,
                    report_id=draft_identity,
                    photo_id=ref["photo_id"],
                    status="terminal",
                    note="draft_photo_observation_unavailable",
                    increment_attempts=False,
                )
                failed += 1
        return {
            "ok": True,
            "photos": len(refs),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
        }
    except Exception as exc:  # noqa: BLE001
        logger.info("[photo-intel] process_draft crashed: %s", exc)
        return {"ok": False, "reason": f"crash:{exc.__class__.__name__}"}


# ── Reconciler ───────────────────────────────────────────────────────

async def reconcile_once(db) -> Dict[str, Any]:
    """One reconciler pass. Safe to call frequently.

    Behavior:
    - Reclaims `in_progress` jobs whose claim went stale (pod restart).
    - Picks up `pending` + `failed` jobs whose `next_attempt_at` has
      arrived.
    - Runs them through `_analyze_one` and updates status.
    - Never blocks longer than ~batch × per-photo timeout.
    """
    now_dt = _now()
    now = _iso(now_dt)

    # 1) Reclaim stale in_progress jobs.
    try:
        stale_before = (now_dt - timedelta(seconds=RECONCILER_STALE_AFTER_S)).isoformat()
        await db[COLL_INTEL_JOBS].update_many(
            {"status": "in_progress", "claim_at": {"$lt": stale_before}},
            {"$set": {"status": "pending"}, "$unset": {"claim_at": ""}},
        )
    except Exception:  # noqa: BLE001
        pass

    # 2) Fetch a small batch of candidate jobs.
    try:
        cursor = db[COLL_INTEL_JOBS].find(
            {
                "status": {"$in": ["pending", "failed"]},
                "next_attempt_at": {"$lte": now},
                "attempts": {"$lt": JOB_MAX_ATTEMPTS},
            },
            {"_id": 0},
        ).sort("next_attempt_at", 1).limit(RECONCILER_BATCH_LIMIT)
        jobs = await cursor.to_list(length=RECONCILER_BATCH_LIMIT)
    except Exception:  # noqa: BLE001
        jobs = []

    completed = 0
    failed = 0
    skipped = 0
    for job in jobs:
        report_id = job.get("report_id") or ""
        photo_id = job.get("photo_id") or ""
        if not report_id or not photo_id:
            continue

        # 3) Claim the job. If the CAS fails, another worker took it.
        try:
            claimed = await _claim_job(
                db,
                report_id=report_id,
                photo_id=photo_id,
                allowed_statuses=("pending", "failed"),
            )
            if not claimed:
                skipped += 1
                continue
        except Exception:  # noqa: BLE001
            skipped += 1
            continue

        # 4) Fetch the parent V1 report to rebuild context freshly.
        try:
            report = await db["daily_reports"].find_one(
                {"$or": [
                    {"doc_id": report_id},
                    {"report_number": report_id},
                    {"id": report_id},
                ]},
                {"_id": 0},
            )
        except Exception:  # noqa: BLE001
            report = None
        if not report:
            await _mark_job(
                db, report_id=report_id, photo_id=photo_id,
                status="terminal", note="report_not_found",
            )
            failed += 1
            continue

        ctx = _draft_context_from_v1(report)
        res = await _analyze_one(
            db,
            report_id=report_id,
            photo_id=photo_id,
            photo_ref=job.get("photo_ref") or "",
            project_id=job.get("project_id") or "",
            date=job.get("date") or "",
            draft_context=ctx,
        )
        if res.get("ok"):
            status = "complete" if res.get("ai_available") else "unavailable"
            await _mark_job(
                db, report_id=report_id, photo_id=photo_id,
                status=status, note=res.get("reason") or "",
            )
            completed += 1
        else:
            # Bump attempt count; if we've exhausted retries, terminal.
            attempts = int(job.get("attempts") or 0) + 1
            status = "terminal" if attempts >= JOB_MAX_ATTEMPTS else "failed"
            await _mark_job(
                db, report_id=report_id, photo_id=photo_id,
                status=status, note=res.get("reason") or "unknown",
            )
            failed += 1
    return {
        "ok": True, "scanned": len(jobs),
        "completed": completed, "failed": failed, "skipped": skipped,
    }


async def reconciler_loop(db, *, interval_s: int = RECONCILER_INTERVAL_S) -> None:
    """Long-running reconciler. Started by a lifecycle step.

    Sleeps `interval_s` between passes. Never dies silently — any
    exception is logged and the loop resumes after a short pause.
    """
    logger.info(
        "[photo-intel] reconciler loop started · interval=%ss batch=%s",
        interval_s, RECONCILER_BATCH_LIMIT,
    )
    while True:
        try:
            if _reconciler_enabled():
                await reconcile_once(db)
        except Exception as exc:  # noqa: BLE001
            logger.info("[photo-intel] reconciler pass crashed: %s", exc)
        await asyncio.sleep(interval_s)


def _reconciler_enabled() -> bool:
    """Env kill-switch. Defaults ON — set
    ``DR_V1_PHOTO_INTEL_RECONCILER_ENABLED=false`` to disable.
    """
    val = (os.environ.get("DR_V1_PHOTO_INTEL_RECONCILER_ENABLED") or "true").strip().lower()
    return val in {"1", "true", "yes", "on"}


# ── Read surface ─────────────────────────────────────────────────────

async def list_report_intelligence(db, report_id: str) -> Dict[str, Any]:
    """Aggregate structured intel for a given V1 report doc_id.

    Returned envelope:
        {
          "report_id": <id>,
          "photo_count": <int>,
          "analyzed": <int>,       # rows with analysis_status=complete
          "pending":  <int>,       # jobs still pending/in_progress/failed
          "observations": [...],   # flat, grounded, supervisor-confirmable
          "narrative": <str>,      # concatenated per-photo narratives (short)
          "photos": [ per-photo intel rows ]
        }
    """
    if not report_id:
        return {"report_id": "", "photo_count": 0, "analyzed": 0,
                "pending": 0, "observations": [], "narrative": "",
                "photos": []}
    doc: Optional[Dict[str, Any]] = None
    ids = {str(report_id)}
    try:
        doc = await db["daily_reports"].find_one(
            {"$or": [{"id": report_id}, {"doc_id": report_id}, {"report_number": report_id}]},
            {
                "_id": 0,
                "id": 1,
                "doc_id": 1,
                "report_number": 1,
                "photos": 1,
                "subcontractors": 1,
                "materials": 1,
                "certification_record": 1,
                "synthetic_record": 1,
                "hidden_from_operations": 1,
            },
        )
    except Exception:  # noqa: BLE001
        doc = None

    if doc:
        for key in ("id", "doc_id", "report_number"):
            value = str(doc.get(key) or "").strip()
            if value:
                ids.add(value)

    rows: List[Dict[str, Any]] = []
    jobs: List[Dict[str, Any]] = []
    for rid in ids:
        try:
            rows.extend(await db[COLL_PHOTO_INTEL].find(
                {"report_id": rid}, {"_id": 0},
            ).to_list(length=200))
        except Exception:  # noqa: BLE001
            pass
        try:
            jobs.extend(await db[COLL_INTEL_JOBS].find(
                {"report_id": rid}, {"_id": 0, "status": 1, "photo_id": 1, "report_id": 1},
            ).to_list(length=200))
        except Exception:  # noqa: BLE001
            pass

    deduped_rows: List[Dict[str, Any]] = []
    seen_row_keys = set()
    for row in rows:
        key = (row.get("report_id"), row.get("photo_id"), row.get("evidence_hash"))
        if key in seen_row_keys:
            continue
        seen_row_keys.add(key)
        deduped_rows.append(row)
    rows = deduped_rows

    deduped_jobs: List[Dict[str, Any]] = []
    seen_job_keys = set()
    for job in jobs:
        key = (job.get("report_id"), job.get("photo_id"))
        if key in seen_job_keys:
            continue
        seen_job_keys.add(key)
        deduped_jobs.append(job)
    jobs = deduped_jobs

    photo_refs = _extract_photo_refs(doc or {}) if doc else []

    analyzed = sum(1 for r in rows if r.get("analysis_status") == "complete")
    processing = sum(1 for j in jobs if j.get("status") == "in_progress")
    queued = sum(1 for j in jobs if j.get("status") == "pending")
    failed_count = sum(1 for j in jobs if j.get("status") == "failed")
    unavailable = sum(1 for r in rows if r.get("analysis_status") == "unavailable")
    observations: List[Dict[str, Any]] = []
    narrative_bits: List[str] = []
    for r in rows:
        if r.get("analysis_status") != "complete":
            continue
        for o in (r.get("observations") or []):
            observations.append({
                "photo_id": r.get("photo_id"),
                "label": o.get("label"),
                "description": o.get("description"),
                "category": o.get("category"),
                "confidence": o.get("confidence"),
                "requires_supervisor_confirmation": bool(
                    o.get("requires_supervisor_confirmation", True)
                ),
            })
        if r.get("narrative"):
            narrative_bits.append(str(r["narrative"])[:280])

    if not photo_refs and not rows and not jobs:
        status = "no_photos"
    elif bool((doc or {}).get("certification_record") or (doc or {}).get("synthetic_record") or (doc or {}).get("hidden_from_operations")):
        status = "suppressed"
    elif processing > 0:
        status = "processing"
    elif queued > 0:
        status = "queued"
    elif failed_count > 0 and analyzed == 0:
        status = "failed"
    elif analyzed > 0:
        status = "complete_with_observations" if observations else "complete_zero_observations"
    elif unavailable > 0:
        status = "unavailable"
    elif photo_refs and not rows and not jobs:
        status = "not_requested"
    elif rows and analyzed == 0:
        status = "complete_zero_observations"
    else:
        status = "unknown"

    return {
        "report_id": (doc or {}).get("doc_id") or report_id,
        "photo_count": len(jobs) or len(photo_refs),
        "analyzed": analyzed,
        "pending": queued + processing + failed_count,
        "queued": queued,
        "processing": processing,
        "failed": failed_count,
        "unavailable": unavailable,
        "status": status,
        "lifecycle_status": status,
        "classification": (
            "EXPECTED — CERTIFICATION/SYNTHETIC ANALYSIS SUPPRESSED"
            if status == "suppressed"
            else "EXPECTED — ANALYSIS WAS NEVER REQUESTED"
            if status == "not_requested"
            else "EXPECTED — PHOTO INTELLIGENCE TEMPORARILY UNAVAILABLE"
            if status == "unavailable"
            else None
        ),
        "observations": observations[:60],
        "narrative": " ".join(narrative_bits)[:1200],
        "photos": rows,
    }


async def list_draft_intelligence(
    db,
    *,
    draft_identity: str,
    draft: Dict[str, Any],
) -> Dict[str, Any]:
    draft_identity = str(draft_identity or "").strip()
    photo_refs = _extract_photo_refs(draft)
    current_photo_ids = {ref.get("photo_id") for ref in photo_refs if ref.get("photo_id")}
    if not draft_identity:
        return {
            "report_id": "",
            "photo_count": len(photo_refs),
            "analyzed": 0,
            "pending": 0,
            "queued": 0,
            "processing": 0,
            "failed": 0,
            "unavailable": 0,
            "status": "no_photos" if not photo_refs else "not_requested",
            "lifecycle_status": "no_photos" if not photo_refs else "not_requested",
            "classification": None,
            "observations": [],
            "narrative": "",
            "photos": [],
        }

    try:
        rows = await db[COLL_PHOTO_INTEL].find(
            {"report_id": draft_identity}, {"_id": 0},
        ).to_list(length=200)
    except Exception:  # noqa: BLE001
        rows = []
    try:
        jobs = await db[COLL_INTEL_JOBS].find(
            {"report_id": draft_identity}, {"_id": 0, "status": 1, "photo_id": 1, "report_id": 1},
        ).to_list(length=200)
    except Exception:  # noqa: BLE001
        jobs = []

    rows = [r for r in rows if (r.get("photo_id") in current_photo_ids)]
    jobs = [j for j in jobs if (j.get("photo_id") in current_photo_ids)]

    rows_by_photo = {r.get("photo_id"): r for r in rows if r.get("photo_id")}
    jobs_by_photo = {j.get("photo_id"): j for j in jobs if j.get("photo_id")}

    completed = 0
    completed_no_observations = 0
    duplicates_reused = 0
    processing = 0
    queued = 0
    failed_count = 0
    terminal_failures = 0
    unavailable = 0
    ineligible = 0
    suppressed = 0
    observations: List[Dict[str, Any]] = []
    narrative_bits: List[str] = []
    for ref in photo_refs:
        pid = ref.get("photo_id")
        row = rows_by_photo.get(pid)
        job = jobs_by_photo.get(pid)
        job_status = str((job or {}).get("status") or "")
        if row and row.get("analysis_status") == "complete":
            row_obs = row.get("observations") or []
            if row_obs:
                if job_status == "duplicate_reused":
                    duplicates_reused += 1
                else:
                    completed += 1
                for o in row_obs:
                    observations.append({
                        "photo_id": row.get("photo_id"),
                        "label": o.get("label"),
                        "description": o.get("description"),
                        "category": o.get("category"),
                        "confidence": o.get("confidence"),
                        "requires_supervisor_confirmation": bool(
                            o.get("requires_supervisor_confirmation", True)
                        ),
                    })
            else:
                completed_no_observations += 1
            if row.get("narrative"):
                narrative_bits.append(str(row["narrative"])[:280])
            continue
        if row and row.get("analysis_status") == "unavailable":
            if job_status == "terminal":
                terminal_failures += 1
            else:
                unavailable += 1
        elif job_status == "in_progress":
            processing += 1
        elif job_status == "pending":
            queued += 1
        elif job_status == "failed":
            failed_count += 1
        elif job_status == "terminal":
            terminal_failures += 1
        elif job_status == "suppressed":
            suppressed += 1
        elif job_status == "ineligible":
            ineligible += 1
        else:
            queued += 1

    reviewed = completed + completed_no_observations + duplicates_reused
    analyzed = reviewed
    state_summary = {
        "photo_count": len(photo_refs),
        "uploading": 0,
        "queued": queued,
        "processing": processing,
        "completed": completed,
        "completed_no_observations": completed_no_observations,
        "duplicates_reused": duplicates_reused,
        "failed": failed_count,
        "terminal_failures": terminal_failures,
        "unavailable": unavailable,
        "ineligible": ineligible,
        "suppressed": suppressed,
        "reviewed": reviewed,
    }
    status = _normalize_operator_photo_status(state_summary)

    return {
        "report_id": draft_identity,
        "photo_count": len(photo_refs),
        "analyzed": analyzed,
        "pending": queued + processing + failed_count,
        "queued": queued,
        "processing": processing,
        "failed": failed_count,
        "unavailable": unavailable,
        "completed": completed,
        "completed_no_observations": completed_no_observations,
        "duplicates_reused": duplicates_reused,
        "terminal_failures": terminal_failures,
        "reviewed": reviewed,
        "status": status,
        "lifecycle_status": status,
        "status_message": _operator_status_message({**state_summary, "status": status}),
        "classification": None,
        "observations": observations[:60],
        "narrative": " ".join(narrative_bits)[:1200],
        "photos": rows,
    }


__all__ = [
    "COLL_INTEL_JOBS",
    "ensure_indexes",
    "enqueue_report",
    "enqueue_draft",
    "process_report",
    "process_draft",
    "reconcile_once",
    "reconciler_loop",
    "list_report_intelligence",
    "list_draft_intelligence",
    "_extract_photo_refs",
    "_draft_context_from_v1",
    "_photo_id_for",
]
