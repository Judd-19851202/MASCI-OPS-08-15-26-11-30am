"""Track 19.16 · Phase A · BILINGUAL DOMAIN VOCABULARY.

The vocabulary API is the single source of truth for EN↔ES labels used
across the engine. Frontend (Phase B) will consume this endpoint at
mount and cache it — Phase A adds no frontend code.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .constants import (
    ACTION_CLASSES,
    ACTION_STATES,
    CASE_STATES,
    CROSS_LINK_KINDS,
    EVENT_TYPES,
    EVIDENCE_TYPES,
    INCIDENT_TYPES,
    ROLE_MATRIX,
)

# Spanish translations for lifecycle states (canonical EN in code).
_STATES_ES: Dict[str, str] = {
    "DRAFT":               "Borrador",
    "FIELD_SUBMITTED":     "Enviado por Campo",
    "SAFETY_INTAKE":       "Recepción de Seguridad",
    "UNDER_INVESTIGATION": "Bajo Investigación",
    "CORRECTIVE_ACTIONS":  "Acciones Correctivas",
    "VERIFICATION":        "Verificación",
    "CLOSED":              "Cerrado",
    "REOPENED":            "Reabierto",
}

# Spanish for corrective action states.
_ACTION_STATES_ES: Dict[str, str] = {
    "OPEN":         "Abierta",
    "ASSIGNED":     "Asignada",
    "IN_PROGRESS":  "En Progreso",
    "VERIFIED":     "Verificada",
    "CANCELED":     "Cancelada",
}

# Spanish for domain roles.
_ROLES_ES: Dict[str, str] = {
    "field":  "Campo",
    "pm":     "Gerente de Proyecto",
    "safety": "Seguridad",
    "shop":   "Taller",
    "fleet":  "Flota",
    "ops":    "Operaciones",
    "exec":   "Ejecutivo",
    "admin":  "Administrador",
}


def _tuple_to_pairs(items) -> List[Dict[str, str]]:
    """Convert a tuple of (code, en, es[, *extras]) into JSON entries."""
    out: List[Dict[str, str]] = []
    for item in items:
        code, en, es = item[0], item[1], item[2]
        entry = {"code": code, "en": en, "es": es}
        if len(item) > 3:
            entry["side"] = item[3]
        out.append(entry)
    return out


def build_vocabulary() -> Dict[str, Any]:
    """Return the complete bilingual dictionary for the domain."""
    return {
        "incident_types":  _tuple_to_pairs(INCIDENT_TYPES),
        "case_states":     [
            {"code": s, "en": s.replace("_", " ").title(), "es": _STATES_ES[s]}
            for s in CASE_STATES
        ],
        "evidence_types":  _tuple_to_pairs(EVIDENCE_TYPES),
        "action_classes":  _tuple_to_pairs(ACTION_CLASSES),
        "action_states":   [
            {"code": s, "en": s.replace("_", " ").title(), "es": _ACTION_STATES_ES[s]}
            for s in ACTION_STATES
        ],
        "cross_link_kinds": _tuple_to_pairs(CROSS_LINK_KINDS),
        "roles": [
            {"code": r, "en": r.title(), "es": _ROLES_ES.get(r, r.title()),
             "capabilities": sorted(caps)}
            for r, caps in ROLE_MATRIX.items()
        ],
        "event_types": list(EVENT_TYPES),
    }


__all__ = ["build_vocabulary"]
