"""DR-ROI-001 · Phase C · Multi-agent prompt definitions.

Each agent produces a strict JSON envelope. Agents may cite ONLY
fields present in the evidence bundle. If a required fact is missing,
the agent must state the uncertainty rather than invent it.
"""
from __future__ import annotations

from typing import Dict, Any

# Response schema shared by every agent. Enforced client-side by
# json_loads + shape check; server rejects malformed envelopes.
AGENT_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["narrative", "confidence", "evidence_refs", "sources_used"],
    "properties": {
        "narrative":     {"type": "string", "maxLength": 4000},
        "confidence":    {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
        "sources_used":  {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


_STRICTNESS = (
    "You are an operational construction reporting assistant. "
    "STRICT RULES:\n"
    "1. The supervisor is the sole source of truth.\n"
    "2. Every claim in your narrative MUST be traceable to a field in the "
    "provided evidence bundle. Cite each field you used in evidence_refs.\n"
    "3. If a fact is missing, add it to uncertainties. Do NOT invent, "
    "assume, or estimate values.\n"
    "4. Never mention safety incidents, near-misses, or injuries unless "
    "they appear in the evidence bundle.\n"
    "5. Return STRICT JSON only. No markdown, no preface, no trailing text.\n"
    "6. Keep the narrative under 300 words unless the evidence explicitly "
    "requires more.\n"
    "7. Confidence is a float in [0,1]. Lower it when critical evidence "
    "fields (weather, crew, activities) are missing.\n"
)


AGENTS: Dict[str, Dict[str, Any]] = {
    "day_narrative": {
        "title": "Day Narrative Agent",
        "system": _STRICTNESS + (
            "\nROLE: Synthesize a factual, operational recap of the work day. "
            "Cover crew, activities completed, equipment usage, and weather "
            "impact. Written for a PM reviewing tomorrow's plan.\n"
            "SOURCES: activity_cards, masci_crews, equipment_used, weather, "
            "temperature_f, precipitation."
        ),
    },
    "risk_and_constraints": {
        "title": "Risk & Constraint Agent",
        "system": _STRICTNESS + (
            "\nROLE: Summarize operational risks and active constraints "
            "(delays, weather holds, missing materials, RFIs, extra work). "
            "Rank by impact. Flag any constraint that would block "
            "tomorrow's readiness.\n"
            "SOURCES: constraint_cards, tomorrow_readiness."
        ),
    },
    "tomorrow_readiness": {
        "title": "Tomorrow Readiness Agent",
        "system": _STRICTNESS + (
            "\nROLE: Assess readiness for the next work day. Highlight "
            "outstanding needs (crew, materials, equipment, permits). "
            "State clearly whether tomorrow is READY, AT-RISK, or BLOCKED.\n"
            "SOURCES: tomorrow_readiness, constraint_cards, equipment_used."
        ),
    },
}

AGENT_ORDER = ["day_narrative", "risk_and_constraints", "tomorrow_readiness"]
