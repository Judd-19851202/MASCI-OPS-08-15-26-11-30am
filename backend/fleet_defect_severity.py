"""iter251 Phase A · Fleet Operations Foundation · Defect Severity Table.

⚠️  DRAFT v1 — PENDING SAFETY / OPERATOR REVIEW BEFORE PRODUCTION RELIANCE ⚠️

This module is the SINGLE SOURCE OF TRUTH for whether a failed DVIR
checklist item puts a truck/trailer OUT OF SERVICE or merely flags it
for shop attention. Drivers do NOT pick severity in the field — the
platform does, eliminating in-field judgement calls.

Sources (operational intent · NOT a legal claim of compliance):
  - 49 CFR § 393 (Parts and Accessories Necessary for Safe Operation)
  - 49 CFR § 396.7 (Unsafe operations forbidden)
  - 49 CFR § 396.11 (Driver Vehicle Inspection Report)
  - CVSA North American Standard Out-of-Service Criteria (operational
    reference · MASCI operates local/in-state and is not subject to
    full federal carrier OOS enforcement, but the criteria are a sound
    operational floor)

Editing rules:
  1. Every checklist item in `checklists_fleet.py` MUST have an entry
     here. The submission endpoint REFUSES to write a defect for an
     unknown item · forcing function for thoughtful classification.
  2. Default policy on uncertainty = "monitor" (truck still operable ·
     shop sees it). Never default to "oos" silently.
  3. Changes require a follow-up PR with Safety sign-off in commit msg
     ("Reviewed-by: Jaymn / Safety · YYYY-MM-DD").
  4. This table is the audit-of-record. Every defect created by the
     submission endpoint stamps its severity from THIS dict at
     submission time · so historical defects keep their original
     classification even if the table changes later.

The table is intentionally conservative: when a CVSA criterion has any
ambiguity (e.g. "20% of brake system inoperative"), we mark it OOS so
the truck doesn't roll. False positives cost productivity; false
negatives cost lives.
"""
from __future__ import annotations
from typing import Dict, Tuple

# Defect severity verdicts:
#   "oos"     · OUT OF SERVICE · truck/trailer cannot operate until
#               a defect is closed by Shop and re-enabled by Dispatch
#   "monitor" · log + photo · shop sees it · truck still operates
SEVERITY_OOS = "oos"
SEVERITY_MONITOR = "monitor"
VALID_SEVERITIES = (SEVERITY_OOS, SEVERITY_MONITOR)


# Defect categories — used by dashboards to scope queues
# (Shop sees all · Safety sees emergency_equipment + signals · Dispatch
# sees oos summary). Keep this list short and stable.
CATEGORY_BRAKES = "brakes"
CATEGORY_TIRES = "tires"
CATEGORY_WHEELS = "wheels"
CATEGORY_STEERING = "steering"
CATEGORY_LIGHTS = "lights"
CATEGORY_SIGNALS = "signals"
CATEGORY_MIRRORS = "mirrors"
CATEGORY_GLASS = "glass"
CATEGORY_WIPERS = "wipers"
CATEGORY_SUSPENSION = "suspension"
CATEGORY_AIR_SYSTEM = "air_system"
CATEGORY_COUPLING = "coupling"
CATEGORY_HYDRAULIC = "hydraulic"
CATEGORY_PTO = "pto"
CATEGORY_FLUIDS = "fluids"
CATEGORY_ALARMS = "alarms"
CATEGORY_HORN = "horn"
CATEGORY_EMERGENCY_EQUIPMENT = "emergency_equipment"
CATEGORY_REFLECTORS = "reflectors"
CATEGORY_BODY = "body"
CATEGORY_INTERIOR = "interior"
CATEGORY_STRUCTURAL = "structural"
CATEGORY_TARP = "tarp"
CATEGORY_LANDING_GEAR = "landing_gear"
CATEGORY_OTHER = "other"


# Per-item classification: item_text → (severity, category)
# Item text MUST match the exact strings emitted by checklists_fleet.py.
FLEET_DEFECT_SEVERITY: Dict[str, Tuple[str, str]] = {
    # ─── TRUCK · BRAKES ────────────────────────────────────────────
    "Service brakes — apply firmly · stop straight · no pulling":     (SEVERITY_OOS, CATEGORY_BRAKES),
    "Parking brake — holds truck against engine torque":              (SEVERITY_OOS, CATEGORY_BRAKES),
    "Trailer air brakes — engage with hand valve · release fully":    (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake chamber / slack adjuster — no visible damage · proper stroke":  (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake hoses / lines — no cracks · no abrasion · no leaks":       (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake warning light / low-air buzzer — operates correctly":      (SEVERITY_OOS, CATEGORY_BRAKES),

    # ─── TRUCK · TIRES ─────────────────────────────────────────────
    "Steer tire tread depth — ≥ 4/32\" across full width":            (SEVERITY_OOS, CATEGORY_TIRES),
    "Drive / trailer tire tread depth — ≥ 2/32\" across full width":  (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — no exposed cord / belt / ply":                            (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — no severe sidewall damage (bulge / cut / cord exposed)":  (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — properly inflated (no flat · no severe under-inflation)": (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — no audible air leak":                                     (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — minor sidewall scuff / cosmetic":                         (SEVERITY_MONITOR, CATEGORY_TIRES),

    # ─── TRUCK · WHEELS / LUGS ─────────────────────────────────────
    "Wheel — all lug nuts present":                                   (SEVERITY_OOS, CATEGORY_WHEELS),
    "Wheel — all lug nuts tight · no loose / clean ring":             (SEVERITY_OOS, CATEGORY_WHEELS),
    "Wheel rim — no cracks · no welds · no severe corrosion":         (SEVERITY_OOS, CATEGORY_WHEELS),
    "Wheel — no oil / grease leak from hub seal":                     (SEVERITY_OOS, CATEGORY_WHEELS),
    "Wheel — no surface rust streaks (cosmetic)":                     (SEVERITY_MONITOR, CATEGORY_WHEELS),

    # ─── TRUCK · STEERING ──────────────────────────────────────────
    "Steering wheel free play — within spec (≤ 10° on light truck · ≤ 30° on heavy)":  (SEVERITY_OOS, CATEGORY_STEERING),
    "Steering linkage / drag link / pitman arm — no missing or broken parts":          (SEVERITY_OOS, CATEGORY_STEERING),
    "Power steering — no leaks · fluid at proper level · normal effort":               (SEVERITY_OOS, CATEGORY_STEERING),

    # ─── TRUCK · LIGHTS ────────────────────────────────────────────
    "Headlights — low beam · both sides functional":                  (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Headlights — high beam · both sides functional":                 (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Brake lights — both sides functional":                           (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Tail lights — both sides functional":                            (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Clearance / marker lights — all functional":                     (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Identification lights (3-light cluster) — all functional":       (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "License plate light — functional":                               (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Reflectors — clean · undamaged · in place":                      (SEVERITY_MONITOR, CATEGORY_REFLECTORS),

    # ─── TRUCK · SIGNALS / ALARMS ─────────────────────────────────
    "Turn signals — left + right · front + rear functional":          (SEVERITY_OOS, CATEGORY_SIGNALS),
    "4-way hazard flashers — operate · synchronized":                 (SEVERITY_OOS, CATEGORY_SIGNALS),
    "Strobes / beacons — all flash patterns operational":             (SEVERITY_MONITOR, CATEGORY_SIGNALS),
    "Strobes / beacons — at least one operational":                   (SEVERITY_OOS, CATEGORY_SIGNALS),
    "Backup alarm — audible when reverse engaged":                    (SEVERITY_OOS, CATEGORY_ALARMS),
    "Raised-bed alarm — audible when bed raised":                     (SEVERITY_OOS, CATEGORY_ALARMS),
    "Horn — sounds at normal volume":                                 (SEVERITY_OOS, CATEGORY_HORN),

    # ─── TRUCK · MIRRORS / GLASS / WIPERS ─────────────────────────
    "Mirrors — both sides present · adjustable · clear visibility":   (SEVERITY_OOS, CATEGORY_MIRRORS),
    "Mirror — minor crack / chip with visible image":                 (SEVERITY_MONITOR, CATEGORY_MIRRORS),
    "Windshield — no cracks in driver line of sight":                 (SEVERITY_OOS, CATEGORY_GLASS),
    "Windshield — minor cracks / pitting outside line of sight":      (SEVERITY_MONITOR, CATEGORY_GLASS),
    "Wipers — both blades sweep windshield cleanly · no streaking":   (SEVERITY_OOS, CATEGORY_WIPERS),
    "Washer fluid — sprays · reservoir not empty":                    (SEVERITY_MONITOR, CATEGORY_WIPERS),

    # ─── TRUCK · SUSPENSION / FRAME ───────────────────────────────
    "Suspension — leaf springs · u-bolts · shackles intact":          (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Suspension — air bags inflate · no leaks · no severe sag":       (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Frame — no cracks · no severe rust-through":                     (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Body — no severe damage affecting safe operation":               (SEVERITY_OOS, CATEGORY_BODY),
    "Body — cosmetic dings · scrapes · paint":                        (SEVERITY_MONITOR, CATEGORY_BODY),

    # ─── TRUCK · AIR SYSTEM ───────────────────────────────────────
    "Air pressure — builds to ≥ 95 psi within normal time":           (SEVERITY_OOS, CATEGORY_AIR_SYSTEM),
    "Air system — pressure holds with engine off · ≤ 4 psi/min loss": (SEVERITY_OOS, CATEGORY_AIR_SYSTEM),
    "Airlines / gladhands — no audible leaks · seals intact":         (SEVERITY_OOS, CATEGORY_AIR_SYSTEM),
    "Low air warning — buzzer + light at ≤ 60 psi":                   (SEVERITY_OOS, CATEGORY_AIR_SYSTEM),

    # ─── TRUCK · COUPLING (tractor) ───────────────────────────────
    "Fifth wheel — locked · jaws fully engaged on kingpin":           (SEVERITY_OOS, CATEGORY_COUPLING),
    "Fifth wheel — mounting bolts present · no cracks":               (SEVERITY_OOS, CATEGORY_COUPLING),
    "Safety chains — attached · no broken links · proper rating":     (SEVERITY_OOS, CATEGORY_COUPLING),
    "Pintle hook — locked · safety pin in place":                     (SEVERITY_OOS, CATEGORY_COUPLING),

    # ─── TRUCK · HYDRAULIC / PTO ──────────────────────────────────
    "Hydraulic system — no visible leaks":                            (SEVERITY_OOS, CATEGORY_HYDRAULIC),
    "Hydraulic — bed raise + lower smoothly · no drift":              (SEVERITY_OOS, CATEGORY_HYDRAULIC),
    "PTO engages + disengages normally":                              (SEVERITY_MONITOR, CATEGORY_PTO),

    # ─── TRUCK · FLUIDS ───────────────────────────────────────────
    "Engine oil — proper level · no major leak":                      (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Coolant — proper level · no major leak":                         (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Fuel — no leaks · cap secure":                                   (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Transmission fluid — proper level":                              (SEVERITY_MONITOR, CATEGORY_FLUIDS),
    "Windshield washer fluid":                                        (SEVERITY_MONITOR, CATEGORY_FLUIDS),

    # ─── TRUCK · INTERIOR / CAB ───────────────────────────────────
    "Seat belt — present · functional · no fraying":                  (SEVERITY_OOS, CATEGORY_INTERIOR),
    "Cab — heater / defroster operational (cold/wet weather)":        (SEVERITY_MONITOR, CATEGORY_INTERIOR),
    "Cab — interior cleanliness":                                     (SEVERITY_MONITOR, CATEGORY_INTERIOR),
    "Cab — dash gauges functional (oil pressure · temp · fuel)":      (SEVERITY_OOS, CATEGORY_INTERIOR),

    # ─── TRUCK · EMERGENCY EQUIPMENT ──────────────────────────────
    "Fire extinguisher — present · charged · sealed · tag current":   (SEVERITY_OOS, CATEGORY_EMERGENCY_EQUIPMENT),
    "Fire extinguisher — minor scuff / tag near expiry":              (SEVERITY_MONITOR, CATEGORY_EMERGENCY_EQUIPMENT),
    "Reflective triangles — 3 present · case intact":                 (SEVERITY_OOS, CATEGORY_EMERGENCY_EQUIPMENT),
    "Reflective triangles — case scuffed (functional)":               (SEVERITY_MONITOR, CATEGORY_EMERGENCY_EQUIPMENT),
    "Spare fuses — kit present":                                      (SEVERITY_MONITOR, CATEGORY_EMERGENCY_EQUIPMENT),
    "First aid kit — present · sealed · contents not expired":        (SEVERITY_MONITOR, CATEGORY_EMERGENCY_EQUIPMENT),
    "Reflective safety vest — present in cab":                        (SEVERITY_MONITOR, CATEGORY_EMERGENCY_EQUIPMENT),

    # ─── TRAILER · TIRES (re-use tire criteria) ───────────────────
    "Trailer tire tread — ≥ 2/32\" across full width":                (SEVERITY_OOS, CATEGORY_TIRES),
    "Trailer tire — no exposed cord / belt / sidewall damage":        (SEVERITY_OOS, CATEGORY_TIRES),
    "Trailer tire — properly inflated · no audible leak":             (SEVERITY_OOS, CATEGORY_TIRES),

    # ─── TRAILER · LIGHTS ─────────────────────────────────────────
    "Trailer brake lights — both sides functional":                   (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Trailer tail lights — both sides functional":                    (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Trailer turn signals — left + right functional":                 (SEVERITY_OOS, CATEGORY_SIGNALS),
    "Trailer clearance / marker lights — all functional":             (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Trailer identification light cluster — functional":              (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Trailer ABS lamp — operates per startup cycle":                  (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Trailer reflective tape (DOT conspicuity) — clean · undamaged":  (SEVERITY_MONITOR, CATEGORY_REFLECTORS),

    # ─── TRAILER · BRAKES ─────────────────────────────────────────
    "Trailer service brakes — engage · release · no drag":            (SEVERITY_OOS, CATEGORY_BRAKES),
    "Trailer brake hoses — no cracks · no abrasion":                  (SEVERITY_OOS, CATEGORY_BRAKES),

    # ─── TRAILER · COUPLING / LANDING GEAR ────────────────────────
    "Trailer coupler / kingpin — no cracks · no excess wear":         (SEVERITY_OOS, CATEGORY_COUPLING),
    "Trailer safety chains — attached · no broken links":             (SEVERITY_OOS, CATEGORY_COUPLING),
    "Landing gear — cranks freely · pads in place · no damage":       (SEVERITY_OOS, CATEGORY_LANDING_GEAR),
    "Landing gear — minor cosmetic wear":                             (SEVERITY_MONITOR, CATEGORY_LANDING_GEAR),

    # ─── TRAILER · TARP / HYDRAULIC ───────────────────────────────
    "Tarp system — deploys + retracts · no major tears":              (SEVERITY_MONITOR, CATEGORY_TARP),
    "Trailer hydraulic system — no leaks · raises + lowers":          (SEVERITY_OOS, CATEGORY_HYDRAULIC),

    # ─── TRAILER · STRUCTURAL ─────────────────────────────────────
    "Trailer frame — no cracks · no severe rust":                     (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer cross members — no broken / missing":                    (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer floor — no major holes · structurally sound":            (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer headboard / bulkhead — intact":                          (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer body — cosmetic damage":                                 (SEVERITY_MONITOR, CATEGORY_BODY),
}


def classify(item_text: str) -> Tuple[str, str]:
    """Look up severity + category for a failed checklist item.
    Returns (severity, category). Raises KeyError if unknown · the
    submission endpoint converts that into a 400 so unclassified items
    cannot create silently-misrouted defects."""
    return FLEET_DEFECT_SEVERITY[item_text]


def is_oos(item_text: str) -> bool:
    """Convenience predicate for the OOS gate at submit time."""
    try:
        return FLEET_DEFECT_SEVERITY[item_text][0] == SEVERITY_OOS
    except KeyError:
        return False


# Sanity check at import time · keeps the table from being silently broken
def _validate_table() -> None:
    for item, value in FLEET_DEFECT_SEVERITY.items():
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError(f"severity table malformed for {item!r}: {value!r}")
        sev, cat = value
        if sev not in VALID_SEVERITIES:
            raise ValueError(f"severity table {item!r} has bad severity {sev!r}")
        if not cat or not isinstance(cat, str):
            raise ValueError(f"severity table {item!r} missing category")


_validate_table()
