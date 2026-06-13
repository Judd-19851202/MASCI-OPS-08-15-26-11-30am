"""Track 13.31B Day-0 · Canonical Asset Taxonomy.

Single source of truth for asset classification across the MASCI platform.

After this module ships, every consumer (PM Engine · Pre-Op · Shop · Dispatch ·
Daily Reports · Fuel/Lube · Asset Administration) MUST read its taxonomy from
here. No module is permitted to invent or maintain its own asset_class /
asset_type list.

Doctrine preserved:
* One asset · one record · one taxonomy.
* equipment_master remains the canonical record.
* Motive enriches telemetry — never overrides verified classification.
* Unknown taxonomy is honest `needs_review` — never fabricated.
"""
from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional, Tuple

TAXONOMY_VERSION: str = "1.0.0"

# ── Level 1 — Asset Classes (closed set) ──────────────────────────────
ASSET_CLASSES: Tuple[str, ...] = (
    "Heavy Equipment",
    "Truck",
    "Trailer",
    "Trench Safety",
    "Roadway / Traffic Control",
    "Survey Equipment",
    "GPS / Machine Control",
    "Technology Equipment",
    "Safety Equipment",
    "Support Equipment",
    "Facility Asset",
    "Temporary Asset",
    "Other Asset",
)

# ── Level 2 — Asset Types per class (closed set) ──────────────────────
ASSET_TYPES_BY_CLASS: Dict[str, Tuple[str, ...]] = {
    "Heavy Equipment": (
        "Excavator", "Dozer", "Motor Grader", "Loader", "Roller",
        "Milling Machine", "Paver", "Skid Steer", "Backhoe", "Sweeper",
        "Forklift", "Crane", "Compactor", "Other Heavy Equipment",
    ),
    "Truck": (
        "Pickup Truck", "Dump Truck", "Fuel Truck", "Lube Truck",
        "Service Truck", "Water Truck", "Flatbed Truck", "Crew Truck",
        "Semi Tractor", "Other Truck",
    ),
    "Trailer": (
        "Equipment Trailer", "Lowboy Trailer", "Tag Trailer",
        "Utility Trailer", "Office Trailer", "Storage Trailer",
        "Other Trailer",
    ),
    "Trench Safety": (
        "Trench Box", "Trench Plate", "Road Plate", "Shoring Equipment",
        "Other Trench Safety",
    ),
    "Roadway / Traffic Control": (
        "Message Board", "Arrow Board", "Traffic Signal", "Cone Package",
        "Barricade", "Light Tower", "Generator", "Other Traffic Control",
    ),
    "Survey Equipment": (
        "Total Station", "Survey Rover", "Base Station", "Data Collector",
        "Survey Controller", "Level", "Tripod", "Prism",
        "Other Survey Equipment",
    ),
    "GPS / Machine Control": (
        "GPS Rover", "GPS Base", "Machine Receiver",
        "Machine Control Display", "Radio", "Antenna",
        "Other GPS Equipment",
    ),
    "Technology Equipment": (
        "Laptop", "Desktop", "Monitor", "Tablet", "iPad", "Phone",
        "Hotspot", "Printer", "Scanner", "Camera",
        "Other Technology Equipment",
    ),
    "Safety Equipment": (
        "Harness", "Gas Monitor", "Confined Space Equipment", "Respirator",
        "Fall Protection", "Other Safety Equipment",
    ),
    "Support Equipment": (
        "Tool", "Specialty Tool", "Pump", "Compressor", "Welder",
        "Other Support Equipment",
    ),
    "Facility Asset": (
        "Office Equipment", "Shop Equipment", "Yard Equipment",
        "Other Facility Asset",
    ),
    "Temporary Asset": (
        "Rental Equipment", "Loaner Equipment", "Temporary Device",
        "Other Temporary Asset",
    ),
    "Other Asset": ("Other Asset",),
}

# Convenience: flat set of all valid (class, type) tuples
VALID_PAIRS: FrozenSet[Tuple[str, str]] = frozenset(
    (cls, typ) for cls, types in ASSET_TYPES_BY_CLASS.items() for typ in types
)

VALID_ASSET_TYPES: FrozenSet[str] = frozenset(
    t for types in ASSET_TYPES_BY_CLASS.values() for t in types
)


# ── Behavior matrix per asset_type ────────────────────────────────────
# Properties are derived from the asset_type, not invented per-row.
# Defaults are conservative; explicit overrides per type.
_DEFAULT_BEHAVIOR: Dict[str, bool] = {
    "requires_registration": False,
    "requires_insurance": False,
    "requires_pm": False,
    "requires_preop": False,
    "assignable_to_employee": True,
    "transferable": True,
    "appears_on_map": False,
    "employee_lifecycle_managed": True,
    "renewal_tracking_required": False,
    "document_vault_required": True,
    "dot_required": False,
    "inspection_required": False,
    "exportable": True,
}

_BEHAVIOR_OVERRIDES: Dict[str, Dict[str, bool]] = {
    # Heavy equipment defaults
    "Excavator":     {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Dozer":         {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Motor Grader":  {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Loader":        {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Roller":        {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Milling Machine":{"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Paver":         {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Skid Steer":    {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Backhoe":       {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    "Sweeper":       {"requires_pm": True, "requires_preop": True, "requires_insurance": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True},
    # Trucks — full DOT
    "Pickup Truck":  {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": False},
    "Dump Truck":    {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Fuel Truck":    {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Lube Truck":    {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Service Truck": {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Water Truck":   {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Flatbed Truck": {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    "Crew Truck":    {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": False},
    "Semi Tractor":  {"requires_registration": True, "requires_insurance": True, "requires_pm": True, "requires_preop": True, "appears_on_map": True, "inspection_required": True, "renewal_tracking_required": True, "dot_required": True},
    # Trailers — registration but no PM by default
    "Equipment Trailer": {"requires_registration": True, "requires_insurance": True, "requires_preop": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": True},
    "Lowboy Trailer":    {"requires_registration": True, "requires_insurance": True, "requires_preop": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": True},
    "Tag Trailer":       {"requires_registration": True, "requires_insurance": True, "requires_preop": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": True},
    "Utility Trailer":   {"requires_registration": True, "requires_insurance": True, "requires_preop": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": True},
    "Office Trailer":    {"requires_registration": True, "requires_insurance": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": False},
    "Storage Trailer":   {"requires_registration": True, "requires_insurance": True, "appears_on_map": True, "renewal_tracking_required": True, "inspection_required": False},
    # Trench safety
    "Trench Box":   {"inspection_required": True, "document_vault_required": True},
    "Trench Plate": {},
    "Road Plate":   {},
    "Shoring Equipment": {"inspection_required": True},
    # Roadway / TC
    "Light Tower":   {"requires_pm": True, "requires_preop": True, "appears_on_map": False},
    "Generator":     {"requires_pm": True, "requires_preop": True},
    # Survey / GPS
    "Total Station":   {"document_vault_required": True},
    "Survey Rover":    {"document_vault_required": True},
    "Base Station":    {"document_vault_required": True},
    "GPS Rover":       {"document_vault_required": True},
    "GPS Base":        {"document_vault_required": True},
    "Machine Receiver":{"document_vault_required": True},
    # Technology (high value · serial-tracked but no PM/registration)
    "Laptop":  {"employee_lifecycle_managed": True, "document_vault_required": True},
    "Desktop": {"employee_lifecycle_managed": True, "document_vault_required": True},
    "Tablet":  {"employee_lifecycle_managed": True, "document_vault_required": True},
    "iPad":    {"employee_lifecycle_managed": True, "document_vault_required": True},
    "Phone":   {"employee_lifecycle_managed": True, "document_vault_required": True},
    "Hotspot": {"employee_lifecycle_managed": True, "document_vault_required": True},
    "Printer": {"employee_lifecycle_managed": True, "document_vault_required": True},
    # Safety equipment (PPE) — consumable nuance: issuance via safety_equipment_issuances
    "Harness":       {"requires_preop": False, "appears_on_map": False, "document_vault_required": False, "inspection_required": True},
    "Gas Monitor":   {"inspection_required": True, "document_vault_required": True},
    "Confined Space Equipment": {"inspection_required": True, "document_vault_required": True},
    "Respirator":    {"inspection_required": True},
    "Fall Protection": {"inspection_required": True},
    # Support
    "Pump":       {"requires_pm": True, "requires_preop": True},
    "Compressor": {"requires_pm": True, "requires_preop": True},
    "Welder":     {"requires_pm": True, "requires_preop": True},
    # Facility / Temporary defaults inherit conservative
    "Rental Equipment": {"renewal_tracking_required": True, "document_vault_required": True},
    "Loaner Equipment": {"renewal_tracking_required": True, "document_vault_required": True},
}


def behavior_for(asset_type: Optional[str]) -> Dict[str, bool]:
    """Return the merged behavior dict for a given asset_type.

    Unknown / None asset_type returns the conservative default (no PM, no
    inspections, no registration, etc.). Callers must check
    `is_valid_asset_type(...)` if they need to distinguish "unknown" from
    "conservative default".
    """
    if not asset_type or asset_type not in VALID_ASSET_TYPES:
        return dict(_DEFAULT_BEHAVIOR)
    merged = dict(_DEFAULT_BEHAVIOR)
    merged.update(_BEHAVIOR_OVERRIDES.get(asset_type, {}))
    return merged


def is_valid_asset_class(c: Optional[str]) -> bool:
    return bool(c) and c in ASSET_CLASSES


def is_valid_asset_type(t: Optional[str]) -> bool:
    return bool(t) and t in VALID_ASSET_TYPES


def is_valid_pair(cls: Optional[str], typ: Optional[str]) -> bool:
    return bool(cls) and bool(typ) and (cls, typ) in VALID_PAIRS


# ── Legacy crosswalk ──────────────────────────────────────────────────
# Each entry maps a legacy `equipment_master.category` and/or
# `equipment_master.preop_equipment_type` / `equipment_master.type` value
# to a canonical (asset_class, asset_type) tuple.
# Keys are case-folded for lookup. Multi-source mapping is supported.

_CROSSWALK_CATEGORY: Dict[str, Tuple[str, str]] = {
    "excavators":              ("Heavy Equipment", "Excavator"),
    "dozers":                  ("Heavy Equipment", "Dozer"),
    "road graders":            ("Heavy Equipment", "Motor Grader"),
    "loaders":                 ("Heavy Equipment", "Loader"),
    "rollers":                 ("Heavy Equipment", "Roller"),
    "paving equipment":        ("Heavy Equipment", "Paver"),
    "skid steers":             ("Heavy Equipment", "Skid Steer"),
    "backhoes":                ("Heavy Equipment", "Backhoe"),
    "sweepers":                ("Truck",           "Other Truck"),  # ambiguous (truck-mounted vs walk-behind)
    "dump trucks":             ("Truck",           "Dump Truck"),
    "service trucks":          ("Truck",           "Service Truck"),
    "water trucks":            ("Truck",           "Water Truck"),
    "flatbed trucks":          ("Truck",           "Flatbed Truck"),
    "pickup trucks":           ("Truck",           "Pickup Truck"),
    "supervisor / mgmt trucks":("Truck",           "Pickup Truck"),
    "tractor trailer trucks":  ("Truck",           "Semi Tractor"),
    "misc trucks":             ("Truck",           "Other Truck"),
    "trailers":                ("Trailer",         "Other Trailer"),
    "compactors":              ("Heavy Equipment", "Compactor"),
    "air compressors":         ("Support Equipment", "Compressor"),
    "generators":              ("Roadway / Traffic Control", "Generator"),
    "light towers":            ("Roadway / Traffic Control", "Light Tower"),
    "pumps":                   ("Support Equipment", "Pump"),
    "welders":                 ("Support Equipment", "Welder"),
    "storage / containers":    ("Facility Asset", "Yard Equipment"),
    "trench safety":           ("Trench Safety",  "Trench Box"),
    "misc equipment":          ("Support Equipment", "Other Support Equipment"),
    "attachments":             ("Other Asset",    "Other Asset"),  # actually a relation
}

_CROSSWALK_TYPE: Dict[str, Tuple[str, str]] = {
    "trench box":  ("Trench Safety", "Trench Box"),
    "road plate":  ("Trench Safety", "Road Plate"),
}

_CROSSWALK_PREOP: Dict[str, Tuple[str, str]] = {
    "excavator":                 ("Heavy Equipment", "Excavator"),
    "dozer":                     ("Heavy Equipment", "Dozer"),
    "motor grader":              ("Heavy Equipment", "Motor Grader"),
    "loader":                    ("Heavy Equipment", "Loader"),
    "roller":                    ("Heavy Equipment", "Roller"),
    "steel drum asphalt roller": ("Heavy Equipment", "Roller"),
    "paver":                     ("Heavy Equipment", "Paver"),
    "skid steer":                ("Heavy Equipment", "Skid Steer"),
    "backhoe":                   ("Heavy Equipment", "Backhoe"),
    "broom":                     ("Truck",           "Other Truck"),
    "haul truck":                ("Truck",           "Dump Truck"),
    "water truck":               ("Truck",           "Water Truck"),
    "plate compactor":           ("Heavy Equipment", "Compactor"),
    "other":                     ("Other Asset",    "Other Asset"),
}


def classify_legacy(
    *,
    category: Optional[str] = None,
    preop_equipment_type: Optional[str] = None,
    type_: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Map legacy equipment_master fields to canonical (asset_class, asset_type).

    Returns:
        {
            "asset_class": str | None,
            "asset_type": str | None,
            "taxonomy_verified": bool,
            "taxonomy_source": "legacy_mapped" | "manual" | "needs_review",
            "taxonomy_review_reason": str | None,
        }

    Resolution order:
      1. legacy `type` (most specific — Road Plate / Trench Box override)
      2. legacy `category` (primary fleet taxonomy)
      3. legacy `preop_equipment_type` (asset-type fidelity for heavy equipment)

    If multiple sources agree → ``taxonomy_verified=True``.
    If only one source matches → ``taxonomy_verified=True``, source=legacy_mapped.
    If sources conflict → ``taxonomy_verified=False``, ``taxonomy_source=needs_review``
        with a structured reason string.
    If no source matches → ``taxonomy_verified=False``, ``taxonomy_source=needs_review``.
    """
    def _norm(s):
        return (s or "").strip().lower()

    hits: List[Tuple[str, Tuple[str, str]]] = []
    if type_:
        m = _CROSSWALK_TYPE.get(_norm(type_))
        if m:
            hits.append(("type", m))
    if category:
        m = _CROSSWALK_CATEGORY.get(_norm(category))
        if m:
            hits.append(("category", m))
    if preop_equipment_type:
        m = _CROSSWALK_PREOP.get(_norm(preop_equipment_type))
        if m:
            hits.append(("preop_equipment_type", m))

    if not hits:
        return {
            "asset_class": None,
            "asset_type": None,
            "taxonomy_verified": False,
            "taxonomy_source": "needs_review",
            "taxonomy_review_reason": "no_legacy_field_matched",
        }

    # Prefer the most specific source (type > preop > category) when conflict
    priority = {"type": 3, "preop_equipment_type": 2, "category": 1}
    hits_sorted = sorted(hits, key=lambda h: -priority[h[0]])
    chosen_src, chosen_pair = hits_sorted[0]

    # Detect conflict among hits
    distinct_pairs = {pair for _, pair in hits}
    if len(distinct_pairs) > 1:
        return {
            "asset_class": chosen_pair[0],
            "asset_type": chosen_pair[1],
            "taxonomy_verified": False,
            "taxonomy_source": "needs_review",
            "taxonomy_review_reason": (
                f"legacy_field_conflict · {[h[0] for h in hits]} · pairs={list(distinct_pairs)}"
            ),
        }

    return {
        "asset_class": chosen_pair[0],
        "asset_type": chosen_pair[1],
        "taxonomy_verified": True,
        "taxonomy_source": "legacy_mapped",
        "taxonomy_review_reason": None,
    }


# ── Company normalization ─────────────────────────────────────────────
CANONICAL_COMPANIES: Tuple[str, ...] = ("MASCI_GC", "FERIA", "LEO", "MC")

_COMPANY_MAP: Dict[str, str] = {
    "masci": "MASCI_GC",
    "masci gc": "MASCI_GC",
    "masci corp": "MASCI_GC",
    "mgc": "MASCI_GC",
    "feria": "FERIA",
    "leo": "LEO",
    "mc": "MC",
    "?": "MASCI_GC",  # operator default per audit · review-needed
}


def normalize_company(value: Optional[str]) -> Tuple[Optional[str], bool]:
    """Return (canonical_company, needs_review).

    needs_review=True when the input was the literal "?" or did not map cleanly.
    """
    if not value:
        return (None, True)
    raw = value.strip().lower()
    if raw == "?":
        return ("MASCI_GC", True)
    canonical = _COMPANY_MAP.get(raw)
    if canonical:
        return (canonical, False)
    return (None, True)


__all__ = [
    "TAXONOMY_VERSION",
    "ASSET_CLASSES",
    "ASSET_TYPES_BY_CLASS",
    "VALID_ASSET_TYPES",
    "VALID_PAIRS",
    "behavior_for",
    "is_valid_asset_class",
    "is_valid_asset_type",
    "is_valid_pair",
    "classify_legacy",
    "CANONICAL_COMPANIES",
    "normalize_company",
]
