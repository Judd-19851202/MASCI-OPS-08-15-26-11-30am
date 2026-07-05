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


# Canonical whitelist of V1/V2 fields the AI is allowed to cite.
# Anything outside this list will NOT appear in evidence_refs so an
# agent that hallucinates a field id fails the evidence check.
EVIDENCE_FIELD_WHITELIST = {
    # Day setup
    "project_name", "project_number", "report_date", "shift",
    "supervisor_name", "weather", "gps_location",
    # Crew
    "masci_crews", "crew_hours_total", "absent_early_chips",
    # Equipment
    "equipment_used", "equipment_hours", "equipment_idle_reasons",
    # V2 structured entry
    "activity_cards", "constraint_cards", "tomorrow_readiness",
    # Safety / quality
    "safety_incidents", "quality_findings", "jha_ack",
    # Photos (Phase D will enrich)
    "photos",
    # Weather / production context
    "temperature_f", "precipitation", "wind_mph",
}


def _canon(value: Any) -> Any:
    """Return a JSON-stable representation of value for hashing."""
    if isinstance(value, dict):
        return {k: _canon(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_canon(v) for v in value]
    return value


def build_evidence_bundle(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Build a normalized evidence bundle from a V2 draft payload.

    Only whitelisted keys are included. Unknown keys are dropped so
    prompt injection or accidental new fields cannot leak into the
    agent context.
    """
    bundle: Dict[str, Any] = {}
    for key in EVIDENCE_FIELD_WHITELIST:
        if key in draft and draft[key] not in (None, "", [], {}):
            bundle[key] = _canon(draft[key])
    return bundle


def evidence_hash(bundle: Dict[str, Any]) -> str:
    """Deterministic sha256 over a canonicalized evidence bundle."""
    blob = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def cited_fields(bundle: Dict[str, Any]) -> List[str]:
    """List every whitelisted field present in the bundle (for the UI)."""
    return sorted(bundle.keys())
