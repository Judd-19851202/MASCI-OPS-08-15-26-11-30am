"""TRACK 23.10-B · Qualification type registry.

The full enum ships on day one. Competent Person is the pilot type
that is fully wired to downstream consumers in follow-up sub-tracks;
every other type is storable/queryable from day one so adding a new
consumer is a configuration change, never a redesign.

Rules
-----
* `QUALIFICATION_ENGINE_TYPES` — the closed set of qualification types
  managed by the engine. Additions require a code change here + an
  entry in `TYPE_METADATA_SPEC` if the type carries type-specific
  extras. No new collection. No new endpoint.
* `QUALIFICATION_STATUS` — closed set. "active" is the only status
  that makes a row selectable in the active registry (§ registry
  service). "pending" · "expired" · "suspended" · "revoked" are never
  active-selectable.
* `validate_type_metadata` — cheap synchronous check called by the
  write endpoints. Returns None if valid, else a human error string.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple


# ─── Qualification types ────────────────────────────────────────────
# Order matters only for UI defaults; storage is by string value.
QUALIFICATION_ENGINE_TYPES: Tuple[str, ...] = (
    "COMPETENT_PERSON",
    "OSHA_10",
    "OSHA_30",
    "FIRST_AID_CPR",
    "SIGNAL_PERSON",
    "CONFINED_SPACE",
    "RIGGING",
    "CRANE_OPERATOR",
    "EQUIPMENT_OPERATOR",
    "TRAFFIC_CONTROL_FLAGGER",
    "MSHA",
    "HAZWOPER",
    "DOT_MEDICAL",
    "CDL_ENDORSEMENT",
    "MANUFACTURER_CERT",
    "COMPANY_SPECIFIC",
)

# Public label mapping for UI. Keep concise; no editorial.
QUALIFICATION_TYPE_LABELS: Dict[str, str] = {
    "COMPETENT_PERSON": "Competent Person",
    "OSHA_10": "OSHA 10",
    "OSHA_30": "OSHA 30",
    "FIRST_AID_CPR": "First Aid / CPR",
    "SIGNAL_PERSON": "Signal Person",
    "CONFINED_SPACE": "Confined Space",
    "RIGGING": "Rigging",
    "CRANE_OPERATOR": "Crane Operator",
    "EQUIPMENT_OPERATOR": "Equipment Operator",
    "TRAFFIC_CONTROL_FLAGGER": "Traffic Control / Flagger",
    "MSHA": "MSHA",
    "HAZWOPER": "HAZWOPER",
    "DOT_MEDICAL": "DOT Medical",
    "CDL_ENDORSEMENT": "CDL Endorsement",
    "MANUFACTURER_CERT": "Manufacturer Certification",
    "COMPANY_SPECIFIC": "Company-Specific",
}

# Backwards-compatibility alias — legacy readers referencing
# `QUALIFICATION_TYPES` get the same closed tuple.
QUALIFICATION_TYPES: Tuple[str, ...] = QUALIFICATION_ENGINE_TYPES


# ─── Verification status ────────────────────────────────────────────
QUALIFICATION_STATUS: Tuple[str, ...] = (
    "active",
    "expired",
    "suspended",
    "revoked",
    "pending",
)

# Only "active" is selectable. Every other value MUST be excluded from
# the active registry query. Consumers rely on this — do not weaken.
QUALIFICATION_STATUS_SELECTABLE: Tuple[str, ...] = ("active",)


# ─── Type-specific metadata specs ───────────────────────────────────
# Each entry: qualification_type → {required: [keys], optional: [keys]}.
# `validate_type_metadata` enforces required keys are present + non-empty.
TYPE_METADATA_SPEC: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "CDL_ENDORSEMENT": {
        "required": ("sub_code",),           # A, B, H, N, P, S, T, X ...
        "optional": ("state", "class"),
    },
    "MANUFACTURER_CERT": {
        "required": ("manufacturer", "product_model"),
        "optional": ("serial_number",),
    },
    "COMPANY_SPECIFIC": {
        "required": ("program_name",),
        "optional": ("program_id",),
    },
    "COMPETENT_PERSON": {
        "required": (),
        "optional": ("standard_reference",),   # e.g. "OSHA_29_CFR_1926_651"
    },
}


def is_engine_type(t: Optional[str]) -> bool:
    """True iff `t` is a recognised engine qualification type."""
    return bool(t) and t in QUALIFICATION_ENGINE_TYPES


def validate_type_metadata(
    qualification_type: Optional[str],
    type_metadata: Optional[Mapping[str, Any]],
) -> Optional[str]:
    """Validate the `type_metadata` blob for a given qualification type.

    Returns None on success, else a human error string suitable to be
    returned directly by an HTTP handler.
    """
    if not qualification_type:
        return "qualification_type is required"
    if qualification_type not in QUALIFICATION_ENGINE_TYPES:
        return f"unknown qualification_type: {qualification_type}"
    spec = TYPE_METADATA_SPEC.get(qualification_type)
    if not spec:
        return None                                # no extras required
    required = spec.get("required") or ()
    meta = dict(type_metadata or {})
    for k in required:
        v = meta.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            return f"type_metadata.{k} is required for {qualification_type}"
    return None


def validate_status(status: Optional[str]) -> Optional[str]:
    """Validate a verification_status write. Returns None or error."""
    if not status:
        return None                                # engine handles default
    if status not in QUALIFICATION_STATUS:
        return f"unknown verification_status: {status}"
    return None


__all__ = [
    "QUALIFICATION_TYPES",
    "QUALIFICATION_ENGINE_TYPES",
    "QUALIFICATION_TYPE_LABELS",
    "QUALIFICATION_STATUS",
    "QUALIFICATION_STATUS_SELECTABLE",
    "TYPE_METADATA_SPEC",
    "is_engine_type",
    "validate_type_metadata",
    "validate_status",
]
