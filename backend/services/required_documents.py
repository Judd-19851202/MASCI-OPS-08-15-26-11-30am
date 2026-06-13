"""services/required_documents.py · Track 13.31B-D3+D4.

Conservative starter map of operator-facing documentation requirements
per canonical asset_type. The map is *informational only* — it drives
the "Pending Update" surfaces on the Asset Profile + Asset Admin
dashboard and never blocks asset creation, inspections, DVIRs,
transfers, or any other operational workflow.

Hard rules:
  * No fabrication. Unknown asset_types return an empty required list.
  * No legal claim is made — these are MASCI operational expectations,
    not regulatory citations.
  * Photos are NEVER required, only suggested.
  * Driven by the behavior matrix in services/asset_taxonomy.py whenever
    possible (e.g. trucks with ``dot_required=True`` → DOT document
    expected). Static overrides cover the cases the behavior matrix
    cannot speak to (GPS calibration, technology warranties, etc.).
"""
from __future__ import annotations

from typing import Any, Dict, List

# Canonical asset-document categories. These match the values written
# to `operational_attachments.type` for ``host_kind="asset"`` rows.
DOC_REGISTRATION         = "registration"
DOC_INSURANCE_CARD       = "insurance_card"
DOC_INSURANCE_POLICY     = "insurance_policy"
DOC_TITLE                = "title"
DOC_PURCHASE             = "purchase_document"
DOC_WARRANTY             = "warranty"
DOC_DOT                  = "dot_document"
DOC_INSPECTION_CERT      = "inspection_certificate"
DOC_CALIBRATION_CERT     = "calibration_certificate"
DOC_ASSET_PHOTO          = "asset_photo"
DOC_MANUAL               = "operator_manual"
DOC_SAFETY_DOC           = "safety_documentation"
DOC_OTHER                = "other_supporting_document"

ASSET_DOC_TYPES: tuple = (
    DOC_REGISTRATION,
    DOC_INSURANCE_CARD,
    DOC_INSURANCE_POLICY,
    DOC_TITLE,
    DOC_PURCHASE,
    DOC_WARRANTY,
    DOC_DOT,
    DOC_INSPECTION_CERT,
    DOC_CALIBRATION_CERT,
    DOC_ASSET_PHOTO,
    DOC_MANUAL,
    DOC_SAFETY_DOC,
    DOC_OTHER,
)

# Sensitive types — visible only to Admin + Asset Admin role.
SENSITIVE_DOC_TYPES: frozenset = frozenset({
    DOC_INSURANCE_POLICY,
    DOC_TITLE,
    DOC_PURCHASE,
})

# Photo subtype enum (used as ``photo_kind`` on asset_photo rows).
PHOTO_SUBTYPES: tuple = (
    "primary",
    "gallery",
    "serial_plate",
    "vin_plate",
    "dot_plate",
    "registration_card",
    "insurance_card",
    "calibration_sticker",
    "damage",
)

# Renewal-tracked document types and the equipment_master field they
# mirror their expiration date to (for fast dashboard reads).
RENEWAL_MIRROR_FIELDS: Dict[str, str] = {
    DOC_REGISTRATION:     "registration_expiration",
    DOC_INSURANCE_CARD:   "insurance_expiration",
    DOC_INSURANCE_POLICY: "insurance_expiration",
    DOC_DOT:              "dot_expiration",
    DOC_CALIBRATION_CERT: "calibration_expiration",
    DOC_INSPECTION_CERT:  "inspection_expiration",
    DOC_WARRANTY:         "warranty_expiration",
}

# Operator-friendly labels (operator-visible terminology — no engineering language).
DOC_LABELS: Dict[str, str] = {
    DOC_REGISTRATION:     "Registration",
    DOC_INSURANCE_CARD:   "Insurance Card",
    DOC_INSURANCE_POLICY: "Insurance Policy",
    DOC_TITLE:            "Title",
    DOC_PURCHASE:         "Purchase Document",
    DOC_WARRANTY:         "Warranty",
    DOC_DOT:              "DOT Document",
    DOC_INSPECTION_CERT:  "Inspection Certificate",
    DOC_CALIBRATION_CERT: "Calibration Certificate",
    DOC_ASSET_PHOTO:      "Asset Photo",
    DOC_MANUAL:           "Operator Manual",
    DOC_SAFETY_DOC:       "Safety Documentation",
    DOC_OTHER:            "Other Supporting Document",
}


def _truck_set() -> set:
    """Asset types treated as on-road trucks (DOT-tracked)."""
    return {
        "Pickup Truck", "Dump Truck", "Fuel Truck", "Lube Truck",
        "Service Truck", "Water Truck", "Flatbed Truck", "Crew Truck",
        "Semi Tractor",
    }


def _trailer_set() -> set:
    return {
        "Equipment Trailer", "Lowboy Trailer", "Dump Trailer",
        "Tilt Deck Trailer", "Belly Dump Trailer", "End Dump Trailer",
        "Tag Trailer", "Pup Trailer",
    }


def required_documents_for(asset_type: str | None, behavior: Dict[str, Any] | None = None) -> List[str]:
    """Return the conservative set of documents MASCI expects to have on
    file for a given canonical asset_type.

    `behavior` is the optional behavior matrix dict (from
    `asset_taxonomy.behavior_for`). When supplied, behaviour flags
    refine the document list:
      * ``requires_registration`` → Registration
      * ``requires_insurance``    → Insurance Card
      * ``dot_required``          → DOT Document
      * ``renewal_tracking_required`` → keep the renewal docs surfaced
    """
    if not asset_type:
        return []
    req: List[str] = []
    behavior = behavior or {}

    # Trucks · trailers (on-road)
    if asset_type in _truck_set():
        req += [DOC_REGISTRATION, DOC_INSURANCE_CARD]
        if behavior.get("dot_required") or asset_type in {
            "Dump Truck", "Fuel Truck", "Lube Truck", "Service Truck",
            "Water Truck", "Flatbed Truck", "Semi Tractor",
        }:
            req.append(DOC_DOT)
        return req
    if asset_type in _trailer_set():
        return [DOC_REGISTRATION, DOC_INSURANCE_CARD, DOC_INSPECTION_CERT]

    # Heavy Equipment — insurance + photo plate
    HEAVY = {
        "Excavator", "Mini Excavator", "Dozer", "Motor Grader",
        "Wheel Loader", "Loader", "Skid Steer", "Compact Track Loader",
        "Backhoe", "Roller", "Steel Drum Asphalt Roller", "Compactor",
        "Paver", "Milling Machine", "Reclaimer", "Stabilizer", "Sweeper",
        "Tractor",
    }
    if asset_type in HEAVY:
        return [DOC_INSURANCE_CARD, DOC_PURCHASE]

    # Support equipment — manuals + warranties
    SUPPORT = {
        "Pump", "Generator", "Light Tower", "Air Compressor", "Welder",
        "Plate Compactor",
    }
    if asset_type in SUPPORT:
        return [DOC_MANUAL, DOC_WARRANTY]

    # GPS / Survey / Machine Control / Locating · calibration assets.
    SURVEY_GPS_LOCATING = {
        # GPS / Machine Control
        "GPS Base Station", "GPS Rover", "GPS Base", "GNSS Receiver",
        "Topcon Hiper XR", "Topcon Hiper VR",
        "Machine Receiver", "Machine Control Receiver",
        "Machine Control Display", "Machine Control Antenna",
        "Machine Control Mast",
        "Radio", "Base Radio", "Rover Radio", "Repeater Radio",
        "Antenna", "GPS Antenna", "UHF Antenna", "Survey Antenna",
        # Survey instruments
        "Total Station", "Robotic Total Station", "Survey Rover",
        "Base Station", "Data Collector", "Controller", "Survey Controller",
        "Laser Level", "Rotating Laser", "Dual-Slope Laser", "Grade Laser",
        "Pipe Laser", "Alignment Laser", "Digital Level", "Automatic Level",
        "Optical Level", "Dumpy Level", "Builder's Level", "Hand Level",
        "Theodolite", "Transit", "Level",
        # Utility locating
        "Utility Locator", "Utility Locating Receiver",
        "Utility Locating Transmitter", "Pipe Locator", "Cable Locator",
        "Sonde Locator", "Ground Penetrating Radar", "GPR Cart",
        "GPR Controller", "Magnetic Locator", "Valve Locator",
        "Electronic Marker Locator",
    }
    if asset_type in SURVEY_GPS_LOCATING:
        return [DOC_CALIBRATION_CERT, DOC_MANUAL, DOC_ASSET_PHOTO]

    # Survey accessories (rods, prisms, tripods) — photo + manual only
    SURVEY_ACCESSORIES = {
        "Prism", "Prism Pole", "Tripod", "Bipod", "Grade Rod",
        "Level Rod", "Survey Rod", "Measuring Wheel",
    }
    if asset_type in SURVEY_ACCESSORIES:
        return [DOC_ASSET_PHOTO, DOC_MANUAL]

    # Technology / Communication / Drones
    TECH = {
        "Tablet", "iPad", "Laptop", "Desktop", "Workstation",
        "Monitor", "Printer", "Scanner", "Phone", "Smartphone",
        "Hotspot", "Camera",
        "Drone", "Drone Controller", "Drone Battery Set",
        "Handheld Radio", "Mobile Radio", "Base Station Radio",
        "Repeater", "Satellite Communicator", "Satellite Phone",
        "Radio Charger", "Radio Dock", "Radio Battery Bank",
    }
    if asset_type in TECH:
        return [DOC_WARRANTY, DOC_PURCHASE, DOC_ASSET_PHOTO]

    # Trench safety
    if asset_type in {"Trench Box", "Road Plate", "Shoring"}:
        return [DOC_INSPECTION_CERT, DOC_ASSET_PHOTO]

    # Behavior-matrix fallback for unmapped asset_types
    if behavior.get("requires_registration"):
        req.append(DOC_REGISTRATION)
    if behavior.get("requires_insurance"):
        req.append(DOC_INSURANCE_CARD)
    if behavior.get("dot_required"):
        req.append(DOC_DOT)
    return req


def renewal_mirror_field(doc_type: str) -> str | None:
    """Return the `equipment_master` field that mirrors this document
    type's expiration date (for fast dashboard reads), or None if the
    doc type is not renewal-tracked.
    """
    return RENEWAL_MIRROR_FIELDS.get(doc_type)


def doc_label(doc_type: str) -> str:
    return DOC_LABELS.get(doc_type, doc_type.replace("_", " ").title())


def is_sensitive(doc_type: str) -> bool:
    return doc_type in SENSITIVE_DOC_TYPES


def all_doc_types() -> List[str]:
    return list(ASSET_DOC_TYPES)


def all_required_map() -> Dict[str, List[str]]:
    """Read-only view of the full asset-type → required-docs map · used
    by the Asset Admin "Documentation Requirements" config tab.
    """
    # Build by sampling the canonical asset_type universe.
    try:
        from services.asset_taxonomy import ASSET_TYPES_BY_CLASS, behavior_for
        out: Dict[str, List[str]] = {}
        for _cls, types in ASSET_TYPES_BY_CLASS.items():
            for t in types:
                out[t] = required_documents_for(t, behavior_for(t))
        return out
    except Exception:
        return {}
