"""iter251 Phase A · Fleet Operations Foundation · DVIR Checklists.

FMCSA-aligned checklist item generators. Items are emitted as strings
that MUST exactly match keys in `fleet_defect_severity.FLEET_DEFECT_SEVERITY`.
This pairing is enforced at submission time (unknown items refused) and
at import time (the test suite cross-checks the two modules).

Pattern mirrors existing `checklists.py` for Pre-Op inspections —
plain functions returning ordered lists, no per-equipment-type
branching here (one DVIR checklist for trucks · one for trailers ·
one for emergency equipment).

No frontend coupling. The driver UX (Phase B) renders whatever this
returns into PASS / FAIL / N/A pills.
"""
from __future__ import annotations
from typing import List


def dvir_truck_items() -> List[str]:
    """Daily driver vehicle inspection report · truck / tractor section.
    Order is operator-friendly walk-around: brakes → tires → wheels →
    steering → lights → signals → mirrors → glass → wipers → suspension
    → frame/body → air system → coupling → hydraulic/PTO → fluids →
    interior → emergency equipment."""
    return [
        # Brakes
        "Service brakes — apply firmly · stop straight · no pulling",
        "Parking brake — holds truck against engine torque",
        "Trailer air brakes — engage with hand valve · release fully",
        "Brake chamber / slack adjuster — no visible damage · proper stroke",
        "Brake hoses / lines — no cracks · no abrasion · no leaks",
        "Brake warning light / low-air buzzer — operates correctly",
        # Tires
        "Steer tire tread depth — ≥ 4/32\" across full width",
        "Drive / trailer tire tread depth — ≥ 2/32\" across full width",
        "Tire — no exposed cord / belt / ply",
        "Tire — no severe sidewall damage (bulge / cut / cord exposed)",
        "Tire — properly inflated (no flat · no severe under-inflation)",
        "Tire — no audible air leak",
        "Tire — minor sidewall scuff / cosmetic",
        # Wheels / lugs
        "Wheel — all lug nuts present",
        "Wheel — all lug nuts tight · no loose / clean ring",
        "Wheel rim — no cracks · no welds · no severe corrosion",
        "Wheel — no oil / grease leak from hub seal",
        "Wheel — no surface rust streaks (cosmetic)",
        # Steering
        "Steering wheel free play — within spec (≤ 10° on light truck · ≤ 30° on heavy)",
        "Steering linkage / drag link / pitman arm — no missing or broken parts",
        "Power steering — no leaks · fluid at proper level · normal effort",
        # Lights
        "Headlights — low beam · both sides functional",
        "Headlights — high beam · both sides functional",
        "Brake lights — both sides functional",
        "Tail lights — both sides functional",
        "Clearance / marker lights — all functional",
        "Identification lights (3-light cluster) — all functional",
        "License plate light — functional",
        "Reflectors — clean · undamaged · in place",
        # Signals / alarms / horn
        "Turn signals — left + right · front + rear functional",
        "4-way hazard flashers — operate · synchronized",
        "Strobes / beacons — all flash patterns operational",
        "Strobes / beacons — at least one operational",
        "Backup alarm — audible when reverse engaged",
        "Raised-bed alarm — audible when bed raised",
        "Horn — sounds at normal volume",
        # Mirrors / glass / wipers
        "Mirrors — both sides present · adjustable · clear visibility",
        "Mirror — minor crack / chip with visible image",
        "Windshield — no cracks in driver line of sight",
        "Windshield — minor cracks / pitting outside line of sight",
        "Wipers — both blades sweep windshield cleanly · no streaking",
        "Washer fluid — sprays · reservoir not empty",
        # Suspension / frame / body
        "Suspension — leaf springs · u-bolts · shackles intact",
        "Suspension — air bags inflate · no leaks · no severe sag",
        "Frame — no cracks · no severe rust-through",
        "Body — no severe damage affecting safe operation",
        "Body — cosmetic dings · scrapes · paint",
        # Air system
        "Air pressure — builds to ≥ 95 psi within normal time",
        "Air system — pressure holds with engine off · ≤ 4 psi/min loss",
        "Airlines / gladhands — no audible leaks · seals intact",
        "Low air warning — buzzer + light at ≤ 60 psi",
        # Coupling (tractor)
        "Fifth wheel — locked · jaws fully engaged on kingpin",
        "Fifth wheel — mounting bolts present · no cracks",
        "Safety chains — attached · no broken links · proper rating",
        "Pintle hook — locked · safety pin in place",
        # Hydraulic / PTO
        "Hydraulic system — no visible leaks",
        "Hydraulic — bed raise + lower smoothly · no drift",
        "PTO engages + disengages normally",
        # Fluids
        "Engine oil — proper level · no major leak",
        "Coolant — proper level · no major leak",
        "Fuel — no leaks · cap secure",
        "Transmission fluid — proper level",
        "Windshield washer fluid",
        # Interior / cab
        "Seat belt — present · functional · no fraying",
        "Cab — heater / defroster operational (cold/wet weather)",
        "Cab — interior cleanliness",
        "Cab — dash gauges functional (oil pressure · temp · fuel)",
        # Emergency equipment (carried on the truck)
        "Fire extinguisher — present · charged · sealed · tag current",
        "Fire extinguisher — minor scuff / tag near expiry",
        "Reflective triangles — 3 present · case intact",
        "Reflective triangles — case scuffed (functional)",
        "Spare fuses — kit present",
        "First aid kit — present · sealed · contents not expired",
        "Reflective safety vest — present in cab",
    ]


def dvir_trailer_items() -> List[str]:
    """Daily driver vehicle inspection report · trailer section.
    Drivers may pick zero or more trailers (single, doubles, equipment
    trailer + lowboy combinations) — the same checklist applies to each
    trailer selected."""
    return [
        # Tires
        "Trailer tire tread — ≥ 2/32\" across full width",
        "Trailer tire — no exposed cord / belt / sidewall damage",
        "Trailer tire — properly inflated · no audible leak",
        # Lights / signals / reflectors
        "Trailer brake lights — both sides functional",
        "Trailer tail lights — both sides functional",
        "Trailer turn signals — left + right functional",
        "Trailer clearance / marker lights — all functional",
        "Trailer identification light cluster — functional",
        "Trailer ABS lamp — operates per startup cycle",
        "Trailer reflective tape (DOT conspicuity) — clean · undamaged",
        # Brakes
        "Trailer service brakes — engage · release · no drag",
        "Trailer brake hoses — no cracks · no abrasion",
        # Coupler / landing gear
        "Trailer coupler / kingpin — no cracks · no excess wear",
        "Trailer safety chains — attached · no broken links",
        "Landing gear — cranks freely · pads in place · no damage",
        "Landing gear — minor cosmetic wear",
        # Tarp / hydraulic
        "Tarp system — deploys + retracts · no major tears",
        "Trailer hydraulic system — no leaks · raises + lowers",
        # Structural
        "Trailer frame — no cracks · no severe rust",
        "Trailer cross members — no broken / missing",
        "Trailer floor — no major holes · structurally sound",
        "Trailer headboard / bulkhead — intact",
        "Trailer body — cosmetic damage",
    ]


def dvir_emergency_items() -> List[str]:
    """Weekly emergency equipment & safety systems inspection.
    Compliance-focused subset — lights, signals, alarms, on-board
    safety equipment. Routes to BOTH Dispatch (operational) and
    Safety (compliance) dashboards in Phase C."""
    return [
        # Lights (compliance-critical subset)
        "Headlights — low beam · both sides functional",
        "Headlights — high beam · both sides functional",
        "Brake lights — both sides functional",
        "Tail lights — both sides functional",
        "Clearance / marker lights — all functional",
        # Signals & alarms
        "Turn signals — left + right · front + rear functional",
        "4-way hazard flashers — operate · synchronized",
        "Strobes / beacons — at least one operational",
        "Backup alarm — audible when reverse engaged",
        "Raised-bed alarm — audible when bed raised",
        "Horn — sounds at normal volume",
        # On-board safety equipment
        "Fire extinguisher — present · charged · sealed · tag current",
        "Reflective triangles — 3 present · case intact",
        "Spare fuses — kit present",
        "First aid kit — present · sealed · contents not expired",
        "Reflective safety vest — present in cab",
    ]


def dvir_weekly_lead_items() -> List[str]:
    """Weekly lead-driver overall accountability inspection · truck
    boss responsibility. Operational hygiene + recurring-issue
    awareness — distinct from the daily compliance DVIR."""
    return [
        # Body / cosmetic accountability
        "Body — cosmetic dings · scrapes · paint",
        "Cab — interior cleanliness",
        # Recurring issues to flag for shop visibility
        "Tire — minor sidewall scuff / cosmetic",
        "Mirror — minor crack / chip with visible image",
        # Cleanliness / organization (no severity entry · MONITOR-default)
        "Cab — heater / defroster operational (cold/wet weather)",
        "Wheel — no surface rust streaks (cosmetic)",
        "Landing gear — minor cosmetic wear",
        # Critical items the lead should re-verify even though daily DVIR covers them
        "Seat belt — present · functional · no fraying",
        "Fire extinguisher — present · charged · sealed · tag current",
        "Reflective triangles — 3 present · case intact",
    ]


# Public registry of inspection kinds the platform recognises in Phase A.
# Adding a new kind requires (1) an entry here, (2) an item-list function
# above, (3) submission-route allow-listing in fleet_ops.py, (4) tests.
DVIR_KIND_PRE_OP = "pre_op"          # existing equipment_inspections data
DVIR_KIND_DAILY = "dvir"             # daily fleet DVIR
DVIR_KIND_WEEKLY_LEAD = "weekly_lead"
DVIR_KIND_WEEKLY_EMERGENCY = "weekly_emergency"

FLEET_INSPECTION_KINDS = {
    DVIR_KIND_DAILY: {
        "label": "Daily DVIR",
        "truck_items": dvir_truck_items,
        "trailer_items": dvir_trailer_items,
        "emergency_items": None,
        "allows_trailers": True,
    },
    DVIR_KIND_WEEKLY_LEAD: {
        "label": "Weekly Lead Driver Inspection",
        "truck_items": dvir_weekly_lead_items,
        "trailer_items": None,
        "emergency_items": None,
        "allows_trailers": False,
    },
    DVIR_KIND_WEEKLY_EMERGENCY: {
        "label": "Weekly Emergency Equipment Inspection",
        "truck_items": dvir_emergency_items,
        "trailer_items": None,
        "emergency_items": None,
        "allows_trailers": False,
    },
}


def is_fleet_kind(kind: str) -> bool:
    """`kind` discriminator predicate used by the migration backfill +
    submission route allow-listing."""
    return kind in FLEET_INSPECTION_KINDS
