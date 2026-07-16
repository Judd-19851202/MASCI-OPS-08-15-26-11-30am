"""ForgedOps AI Gateway · Task router.

Maps a logical task (operational_narrative, photo_vision, ...) to the
`(provider, model)` pair used to serve it. Overridable at runtime via
env or the admin telemetry surface. Never referenced from the field UI.
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

from .env import default_text_model


TaskType = str  # See literal set in TASK_ROUTES.keys().


# Default routing plan per architecture directive.
# Provider names align with adapter registry keys.
TASK_ROUTES: Dict[str, Tuple[str, str]] = {
    "operational_narrative":  ("anthropic", default_text_model()),
    "production_intelligence":("anthropic", default_text_model()),
    "delay_intelligence":     ("anthropic", default_text_model()),
    "safety_intelligence":    ("anthropic", default_text_model()),
    "equipment_intelligence": ("anthropic", default_text_model()),
    "photo_vision":           ("openai",    "gpt-4o"),
    "pm_brief":               ("anthropic", default_text_model()),
    "executive_brief":        ("anthropic", default_text_model()),
    "confidence_validation":  ("anthropic", default_text_model()),
    "evidence_trace":         ("anthropic", default_text_model()),
    "future_task":            ("anthropic", default_text_model()),
    "translation_es_en":      ("anthropic", default_text_model()),
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
