"""Track 13.31B-D5.2 · Canonical Pre-Op + DVIR inspection template registry.

Pure-python registry keyed by canonical ``asset_type`` (matching the spine
emitted by ``services.asset_taxonomy``). Consumed by:

  • ``services.inspection_classification.stamp_inspection_canonical`` to
    decide ``template_status="available" | "missing_template"`` and stamp
    ``template_key`` / ``template_label``.
  • ``GET /api/asset-spine/inspection-templates/{asset_type}`` — operator
    UI hydration (sections + items per asset type).
  • ``GET /api/asset-spine/inspection-templates/missing-backlog`` — the
    Asset Administrator's live backlog of asset types with active rows in
    ``equipment_master`` that still have no canonical template.

Doctrine:
  • Equipment Master is canonical · this registry CONSUMES taxonomy, never
    redefines it.
  • One template per canonical ``asset_type``.
  • Truck variants → ``applies_to="dvir"``. Everything else → ``"pre_op"``.
  • No silent "Other" template for known asset types — if no template
    exists, ``missing_template`` is the honest answer.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any


# ─────────────────────────────────────────────────────────────────────
# Template payload helpers
# ─────────────────────────────────────────────────────────────────────
def _t(label: str, items: List[str]) -> Dict[str, Any]:
    return {"label": label, "items": items}


# ─────────────────────────────────────────────────────────────────────
# Pre-Op templates — Heavy Equipment + Support Equipment
# ─────────────────────────────────────────────────────────────────────
_HEAVY = {
    "Excavator": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks", "Damage report"]),
        _t("Tracks & Undercarriage", ["Tracks", "Rollers", "Idlers", "Sprockets"]),
        _t("Boom / Stick / Bucket", ["Boom", "Stick", "Bucket", "Pins & bushings"]),
        _t("Hydraulics", ["Hoses", "Cylinders", "Swing"]),
        _t("Cab & Controls", ["Controls", "Counterweight", "ROPS / seat belt"]),
        _t("Safety", ["Lights", "Backup alarm", "Fire extinguisher"]),
    ],
    "Mini Excavator": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tracks & Undercarriage", ["Tracks", "Rollers", "Sprockets"]),
        _t("Boom / Stick / Bucket", ["Boom", "Stick", "Bucket", "Pins"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Safety", ["Lights", "Backup alarm", "ROPS / seat belt"]),
    ],
    "Dozer": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Undercarriage", ["Tracks", "Rollers", "Idlers", "Sprockets"]),
        _t("Blade", ["Blade", "Cutting edges", "Tilt/angle cylinders"]),
        _t("Rear Attachments", ["Ripper", "Winch (if equipped)"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Motor Grader": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Running Gear", ["Tires", "Articulation"]),
        _t("Blade Assembly", ["Circle", "Moldboard", "Cutting edges"]),
        _t("Rear Attachments", ["Scarifier", "Ripper"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Wheel Loader": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires & Articulation", ["Tires", "Articulation joint"]),
        _t("Bucket Assembly", ["Bucket", "Cutting edge", "Lift arms"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Loader": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires & Articulation", ["Tires", "Articulation"]),
        _t("Bucket Assembly", ["Bucket", "Cutting edge", "Lift arms"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Skid Steer": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Running Gear", ["Tires"]),
        _t("Boom & Attachment", ["Lift arms", "Bucket / attachment", "Quick coupler"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["Door / lap bar / seat belt", "Lights", "Backup alarm"]),
    ],
    "Compact Track Loader": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tracks", ["Tracks", "Rollers", "Sprockets"]),
        _t("Boom & Attachment", ["Lift arms", "Bucket / attachment", "Quick coupler"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["Door / lap bar / seat belt", "Lights", "Backup alarm"]),
    ],
    "Backhoe": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires & Stabilizers", ["Tires", "Stabilizers"]),
        _t("Loader End", ["Loader bucket", "Lift arms"]),
        _t("Backhoe End", ["Boom", "Stick", "Bucket", "Pins & bushings"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Roller": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Drum", ["Drum condition", "Scrapers"]),
        _t("Compaction System", ["Vibration system"]),
        _t("Water System", ["Tank", "Sprayers", "Pump"]),
        _t("Running Gear", ["Tires (if pneumatic)", "Steering / articulation"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Steel Drum Asphalt Roller": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Drum", ["Steel drum condition", "Scrapers"]),
        _t("Compaction System", ["Vibration system"]),
        _t("Water System", ["Tank", "Sprayers", "Pump"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Compactor": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Drum", ["Drum / padfoot condition", "Scrapers"]),
        _t("Compaction System", ["Vibration system"]),
        _t("Running Gear", ["Steering / articulation"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Plate Compactor": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Plate", ["Plate condition"]),
        _t("Engine", ["Engine", "Belts / guards"]),
        _t("Handle & Controls", ["Handle", "Throttle"]),
    ],
    "Paver": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Running Gear", ["Tracks", "Tires (if applicable)"]),
        _t("Hopper", ["Hopper", "Wings"]),
        _t("Conveyor / Auger", ["Conveyor system", "Augers"]),
        _t("Screed", ["Screed plates", "Extensions", "Crown adjustment"]),
        _t("Heating System", ["Heat system"]),
        _t("Controls & Safety", ["Emergency stops", "Lights", "Backup alarm", "Safety guards"]),
    ],
    "Milling Machine": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tracks", ["Tracks"]),
        _t("Cutting Drum", ["Drum / picks"]),
        _t("Conveyor", ["Conveyor system"]),
        _t("Water System", ["Tank", "Sprayers"]),
        _t("Controls & Safety", ["Lights", "Backup alarm", "Safety guards"]),
    ],
    "Reclaimer": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires", ["Tires"]),
        _t("Cutting Drum", ["Drum / picks"]),
        _t("Hydraulics", ["Hoses", "Cylinders"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Stabilizer": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires", ["Tires"]),
        _t("Mixing System", ["Drum / picks"]),
        _t("Water/Cement System", ["Tank", "Spray bar"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights", "Backup alarm"]),
    ],
    "Sweeper": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires", ["Tires"]),
        _t("Broom System", ["Main broom", "Side broom", "Brushes"]),
        _t("Hopper / Vacuum", ["Hopper", "Vacuum"]),
        _t("Cab & Safety", ["Lights", "Backup alarm"]),
    ],
}

_SUPPORT = {
    "Pump": [
        _t("General", ["General condition", "Leaks"]),
        _t("Engine / Motor", ["Engine / motor", "Fuel/oil/coolant (if applicable)"]),
        _t("Plumbing", ["Hoses", "Fittings", "Priming system"]),
        _t("Safety", ["Guards", "Trailer / skid condition (if applicable)"]),
    ],
    "Generator": [
        _t("General", ["General condition", "Leaks"]),
        _t("Engine", ["Fuel", "Oil / coolant", "Battery"]),
        _t("Electrical", ["Electrical panel", "Cords / receptacles", "Grounding"]),
        _t("Safety", ["Trailer / skid condition (if applicable)"]),
    ],
    "Light Tower": [
        _t("General", ["General condition"]),
        _t("Mast", ["Mast", "Winch / cables"]),
        _t("Lights", ["Lamps", "Fixtures"]),
        _t("Engine", ["Generator / engine", "Fuel / oil / coolant"]),
        _t("Safety", ["Outriggers", "Trailer condition"]),
    ],
    "Air Compressor": [
        _t("General", ["General condition", "Leaks"]),
        _t("Engine", ["Engine", "Oil / coolant"]),
        _t("Air System", ["Hoses", "Couplers", "Pressure gauges", "Safety valves"]),
        _t("Safety", ["Trailer / skid condition"]),
    ],
    "Welder": [
        _t("General", ["General condition"]),
        _t("Engine", ["Engine", "Fuel / oil / coolant"]),
        _t("Welding System", ["Leads / cables", "Ground clamp", "Controls"]),
        _t("Safety", ["Fire extinguisher (if mounted)", "Trailer / skid condition"]),
    ],
    "Tractor": [
        _t("Walkaround", ["Walkaround visual", "Fluid leaks"]),
        _t("Tires", ["Tires"]),
        _t("PTO / 3-Point", ["PTO", "3-point hitch"]),
        _t("Cab & Safety", ["ROPS / seat belt", "Lights"]),
    ],
}

_TRENCH = {
    "Trench Box": [
        _t("Inspection (Trench Safety subsystem)",
           ["See Trench Safety inspection · this asset's safety inspections are owned by the trench safety subsystem"]),
    ],
    "Road Plate": [
        _t("Inspection", ["Surface condition", "Edges", "Anchoring"]),
    ],
}

# ─────────────────────────────────────────────────────────────────────
# DVIR templates — Trucks
# ─────────────────────────────────────────────────────────────────────
_TRUCKS = {
    "Dump Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights", "Wipers"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Dump Body", ["Bed / body", "Tailgate", "Tarp system (if equipped)"]),
        _t("Hydraulics", ["Hydraulics", "Fluid leaks"]),
        _t("Safety", ["Backup alarm", "Fire extinguisher / safety kit"]),
    ],
    "Service Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Service Body", ["Service body compartments", "Tools secured"]),
        _t("Attachments", ["Crane / compressor (if equipped)", "Fluid tanks (if equipped)"]),
        _t("Safety", ["Fire extinguisher / safety kit", "Fluid leaks"]),
    ],
    "Fuel Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Tank & Pump", ["Tank condition", "Pump / meter", "Hoses / nozzles"]),
        _t("Hazmat", ["Spill kit", "Placards", "Fire extinguisher"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Lube Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Tanks & Pumps", ["Tanks", "Pumps", "Hoses", "Grease system"]),
        _t("Hazmat", ["Spill kit", "Fire extinguisher"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Water Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Water System", ["Tank", "Spray bar", "Pump", "Valves", "Hoses"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Pickup Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Wipers", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Safety", ["Fluid leaks", "Fire extinguisher (if required)"]),
    ],
    "Crew Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Flatbed Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Bed", ["Bed", "Tie-down points", "Straps / chains storage"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Semi Tractor": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Wipers", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering", "Suspension"]),
        _t("Coupling", ["Fifth wheel", "Air lines", "Electrical line"]),
        _t("Safety", ["Fluid leaks", "Fire extinguisher / safety kit"]),
    ],
    "Other Truck": [
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Safety", ["Fluid leaks"]),
    ],
    "Haul Truck": [
        # Catch-all kept for legacy crosswalk reads; alias to Dump Truck content
        _t("Driver Cab", ["Mirrors", "Horn", "Seat belts", "Lights"]),
        _t("Running Gear", ["Tires", "Brakes", "Steering"]),
        _t("Body / Bed", ["Bed / body", "Tailgate"]),
        _t("Safety", ["Backup alarm", "Fluid leaks"]),
    ],
}

# ─────────────────────────────────────────────────────────────────────
# DVIR templates — Trailers
# ─────────────────────────────────────────────────────────────────────
_TRAILERS = {
    "Equipment Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Brakes", "Coupler / pintle", "Safety chains", "Breakaway system"]),
        _t("Deck", ["Deck", "Ramps", "Tie-down points"]),
    ],
    "Tag Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Brakes", "Coupler / pintle", "Safety chains", "Breakaway system"]),
        _t("Deck", ["Deck", "Ramps", "Tie-down points"]),
    ],
    "Lowboy Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Brakes", "Coupler / fifth wheel", "Safety chains", "Air lines"]),
        _t("Deck", ["Deck", "Detach neck / ramps"]),
        _t("Hydraulics", ["Hydraulics (if applicable)"]),
        _t("Cargo", ["Tie-down points"]),
    ],
    "Utility Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Coupler", "Safety chains", "Breakaway system (if applicable)"]),
        _t("Deck", ["Deck", "Gate / ramp"]),
    ],
    "Office Trailer": [
        _t("Walkaround", ["Tires", "Lights"]),
        _t("Site Setup", ["Stairs / steps", "Doors / locks", "Anchoring / blocking"]),
        _t("Utilities", ["Electrical", "HVAC (if applicable)"]),
    ],
    "Storage Trailer": [
        _t("Walkaround", ["Tires", "Lights"]),
        _t("Site Setup", ["Doors / locks", "Anchoring / blocking"]),
    ],
    "Other Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Brakes", "Coupler", "Safety chains"]),
        _t("Deck", ["Deck condition"]),
    ],
    "Flatbed Trailer": [
        _t("Trailer Walkaround", ["Tires", "Lights"]),
        _t("Brakes & Couplers", ["Brakes", "Coupler", "Safety chains"]),
        _t("Deck", ["Deck", "Tie-down points"]),
    ],
}

# Combine into the public registry.
INSPECTION_TEMPLATES: Dict[str, Dict[str, Any]] = {}


def _register(asset_type: str, asset_class: str, applies_to: str, sections: List[Dict[str, Any]]) -> None:
    key = asset_type.lower().replace(" ", "_").replace("/", "_").replace("__", "_")
    INSPECTION_TEMPLATES[asset_type] = {
        "asset_type": asset_type,
        "asset_class": asset_class,
        "template_key": key,
        "template_label": f"{asset_type} {'DVIR' if applies_to == 'dvir' else 'Pre-Op'}",
        "applies_to": applies_to,
        "sections": sections,
    }


for at, sections in _HEAVY.items():
    _register(at, "Heavy Equipment", "pre_op", sections)
for at, sections in _SUPPORT.items():
    _register(at, "Support Equipment", "pre_op", sections)
for at, sections in _TRENCH.items():
    _register(at, "Trench Safety", "pre_op", sections)
for at, sections in _TRUCKS.items():
    _register(at, "Truck", "dvir", sections)
for at, sections in _TRAILERS.items():
    _register(at, "Trailer", "dvir", sections)


# ─────────────────────────────────────────────────────────────────────
# Public lookups
# ─────────────────────────────────────────────────────────────────────
def has_template(asset_type: Optional[str]) -> bool:
    return bool(asset_type) and asset_type in INSPECTION_TEMPLATES


def template_for(asset_type: Optional[str]) -> Optional[Dict[str, Any]]:
    return INSPECTION_TEMPLATES.get(asset_type or "")


def template_status_for(asset_type: Optional[str]) -> str:
    return "available" if has_template(asset_type) else "missing_template"


def template_key_for(asset_type: Optional[str]) -> Optional[str]:
    t = template_for(asset_type)
    return t["template_key"] if t else None


def all_templates() -> List[Dict[str, Any]]:
    return list(INSPECTION_TEMPLATES.values())


__all__ = [
    "INSPECTION_TEMPLATES",
    "has_template",
    "template_for",
    "template_status_for",
    "template_key_for",
    "all_templates",
]
