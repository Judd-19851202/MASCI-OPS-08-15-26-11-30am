"""DR-ROI-001 · Phase C · Evidence bundler + deterministic hasher.

The supervisor is the sole source of truth. Every AI narrative must
be traceable to a specific field on the report. The evidence bundle
collects those fields in a normalized, hashable structure so we only
re-run agents when the underlying evidence changes.

Zero drift: reads V1 fields WITHOUT mutating any document.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


# Canonical whitelist of V1/V2/V3 fields the AI is allowed to cite.
# Anything outside this list will NOT appear in evidence_refs so an
# agent that hallucinates a field id fails the evidence check.
#
# TRACK 24.12 · Workstream A · EVIDENCE REBUILD
# ─────────────────────────────────────────────
# Prior whitelist covered ~15 fields. Field crews were seeing shallow
# AI narratives because every V3 field group past crew/equipment/
# weather was being silently stripped by `build_evidence_bundle`.
# The rebuild widens the whitelist to include every DR field group
# the V3 shell submits, plus photo captions / photo-observation
# metadata (from Track 22.9B) and attachment metadata (from Track
# 19.04 / 24.11) so the AI can honestly reference an uploaded permit
# without hallucinating file contents.
EVIDENCE_FIELD_WHITELIST = {
    # ── Day setup / identity ──────────────────────────────────
    "project_name", "project_number", "report_date", "shift",
    "supervisor_name", "weather", "gps_location",
    # TRACK 24.12 · project metadata snapshot from the DR payload.
    "client", "project_manager", "location", "weather_summary",
    "day_setup",
    # ── Crew / labor ──────────────────────────────────────────
    "masci_crews", "crew_hours_total", "absent_early_chips",
    "visitors",
    # ── Equipment ─────────────────────────────────────────────
    "equipment_used", "equipment_hours", "equipment_idle_reasons",
    # ── V2 / V3 structured entry ──────────────────────────────
    "activity_cards", "constraint_cards", "tomorrow_readiness",
    # ── TRACK 26.12 · production rows · V1 constraints · impacts ──
    "production", "constraints", "day_impacts", "narrative_sections",
    # ── Materials / hauling ───────────────────────────────────
    "materials", "outbound_materials", "subcontractors", "vendors",
    # ── Safety / quality ──────────────────────────────────────
    "safety_incidents", "quality_findings", "jha_ack",
    "safety_quality", "near_misses",
    # ── Excavation / trench (Track 23.10-E) ───────────────────
    "excavation", "competent_person", "work_stoppage",
    # ── Free-text narrative ───────────────────────────────────
    "general_notes",
    # ── Photos + photo intel ──────────────────────────────────
    "photos", "photo_captions", "photo_observations",
    # ── Attachment metadata (never file contents) ─────────────
    "attachments",
    # ── Weather / production context ──────────────────────────
    "temperature_f", "precipitation", "wind_mph",
}


def _canon(value: Any) -> Any:
    """Return a JSON-stable representation of value for hashing."""
    if isinstance(value, dict):
        return {k: _canon(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_canon(v) for v in value]
    return value


# TRACK 26.12 · Binary payload guard.
# The DR form attaches photos as base64 data URLs. Prior to this track
# those raw bytes were JSON-dumped INTO the text prompt (~1M tokens for
# 8 photos), which made every provider call fail instantly and silently
# dropped the app to the deterministic fallback. Photos are now reduced
# to citable metadata refs; actual pixels go to the vision model via
# `services/dr_ai/vision.py` and come back as `photo_observations`.

def _is_data_url(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("data:") and ";base64," in v[:80]


def _photo_meta(photos: List[Any], captions: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, p in enumerate(photos[:24]):
        raw = p if isinstance(p, str) else json.dumps(p, sort_keys=True, default=str)
        meta: Dict[str, Any] = {
            "ref": f"photo:{i}",
            "sha12": hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:12],
        }
        if i < len(captions) and isinstance(captions[i], str) and captions[i].strip():
            meta["caption"] = captions[i].strip()[:240]
        out.append(meta)
    return out


def _strip_binary(v: Any) -> Any:
    """Recursively replace embedded images / oversized blobs so no raw
    binary ever reaches a text prompt."""
    if isinstance(v, str):
        if _is_data_url(v):
            return f"[image_omitted:{len(v)}b — see photo_observations]"
        if len(v) > 6000:
            return v[:2000] + f"…[truncated {len(v)} chars]"
        return v
    if isinstance(v, dict):
        return {k: _strip_binary(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_strip_binary(x) for x in v]
    return v


def build_evidence_bundle(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Build a normalized evidence bundle from a V2 draft payload.

    Only whitelisted keys are included. Unknown keys are dropped so
    prompt injection or accidental new fields cannot leak into the
    agent context. Photos are reduced to metadata refs and every value
    is scrubbed of embedded binary before it can reach a prompt.
    """
    bundle: Dict[str, Any] = {}
    for key in EVIDENCE_FIELD_WHITELIST:
        if key in draft and draft[key] not in (None, "", [], {}):
            bundle[key] = _canon(draft[key])
    if isinstance(bundle.get("photos"), list):
        bundle["photos"] = _photo_meta(
            bundle["photos"], list(draft.get("photo_captions") or []),
        )
    return _strip_binary(bundle)


def evidence_hash(bundle: Dict[str, Any]) -> str:
    """Deterministic sha256 over a canonicalized evidence bundle."""
    blob = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def cited_fields(bundle: Dict[str, Any]) -> List[str]:
    """List every whitelisted field present in the bundle (for the UI)."""
    return sorted(bundle.keys())
