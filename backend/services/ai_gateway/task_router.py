"""ForgedOps AI Gateway · Task router.

Maps a logical task (operational_narrative, photo_vision, ...) to the
`(provider, model)` pair used to serve it. Overridable at runtime via
env or the admin telemetry surface. Never referenced from the field UI.
"""
from __future__ import annotations

import os
from typing import Dict, Tuple


TaskType = str  # See literal set in TASK_ROUTES.keys().


# Default routing plan per architecture directive.
# Provider names align with adapter registry keys.
TASK_ROUTES: Dict[str, Tuple[str, str]] = {
    "operational_narrative":  ("anthropic", "claude-sonnet-4-5-20250929"),
    "production_intelligence":("anthropic", "claude-sonnet-4-5-20250929"),
    "delay_intelligence":     ("anthropic", "claude-sonnet-4-5-20250929"),
    "safety_intelligence":    ("anthropic", "claude-sonnet-4-5-20250929"),
    "equipment_intelligence": ("anthropic", "claude-sonnet-4-5-20250929"),
    "photo_vision":           ("openai",    "gpt-5.2-vision"),
    "pm_brief":               ("anthropic", "claude-sonnet-4-5-20250929"),
    "executive_brief":        ("anthropic", "claude-sonnet-4-5-20250929"),
    "confidence_validation":  ("anthropic", "claude-sonnet-4-5-20250929"),
    "evidence_trace":         ("anthropic", "claude-sonnet-4-5-20250929"),
    "future_task":            ("anthropic", "claude-sonnet-4-5-20250929"),
    "translation_es_en":      ("anthropic", "claude-sonnet-4-5-20250929"),
}


def route(task: str) -> Tuple[str, str]:
    """Resolve `(provider, model)` for a task, honoring env overrides."""
    # Env overrides — e.g. AI_TASK_ROUTE__photo_vision="google:gemini-2.0-flash"
    key = f"AI_TASK_ROUTE__{task}"
    override = os.environ.get(key)
    if override and ":" in override:
        p, m = override.split(":", 1)
        return p.strip().lower(), m.strip()
    return TASK_ROUTES.get(task, TASK_ROUTES["future_task"])
