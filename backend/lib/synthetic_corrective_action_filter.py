from __future__ import annotations

import re
from typing import Any, Dict, List


_TITLE_PREFIX_RE = re.compile(r"^(TEST[_\-]|SMOKE[_\-]|SYNTHETIC[_\-]|ITER[0-9])", re.IGNORECASE)
_PROJECT_RE = re.compile(
    r"^(TEST[_\-]|SMOKE[_\-]|SYNTHETIC[_\-]|ITER[0-9]|QA_SMOKE|CERT_TEST|RECERT|PARITY)",
    re.IGNORECASE,
)
_TITLE_OR_DESC_RE = re.compile(r"\b(synthetic|integration test|lifecycle test)\b", re.IGNORECASE)
_EXPLICIT_MARKERS = ["synthetic_record", "hidden_from_operations", "certification_record"]


def synthetic_corrective_action_exclusion_clauses() -> List[Dict[str, Any]]:
    return [
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"certification_record": {"$ne": True}},
        {"title": {"$not": {"$regex": _TITLE_PREFIX_RE.pattern, "$options": "i"}}},
        {"title": {"$not": {"$regex": _TITLE_OR_DESC_RE.pattern, "$options": "i"}}},
        {"description": {"$not": {"$regex": _TITLE_OR_DESC_RE.pattern, "$options": "i"}}},
        {"project_number": {"$not": {"$regex": _PROJECT_RE.pattern, "$options": "i"}}},
    ]


def apply_synthetic_corrective_action_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(query or {})
    extra = synthetic_corrective_action_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_synthetic_corrective_action(doc: Dict[str, Any]) -> bool:
    if not doc:
        return False
    for marker in _EXPLICIT_MARKERS:
        if doc.get(marker) is True:
            return True
    title = (doc.get("title") or "").strip()
    description = (doc.get("description") or "").strip()
    project_number = (doc.get("project_number") or "").strip()
    return bool(
        _TITLE_PREFIX_RE.search(title)
        or _TITLE_OR_DESC_RE.search(title)
        or _TITLE_OR_DESC_RE.search(description)
        or _PROJECT_RE.search(project_number)
    )


def synthetic_corrective_action_markers(doc: Dict[str, Any]) -> Dict[str, bool]:
    is_synth = is_synthetic_corrective_action(doc)
    return {
        "synthetic_record": is_synth,
        "hidden_from_operations": is_synth,
        "certification_record": is_synth,
    }


__all__ = [
    "apply_synthetic_corrective_action_exclusion",
    "is_synthetic_corrective_action",
    "synthetic_corrective_action_exclusion_clauses",
    "synthetic_corrective_action_markers",
]