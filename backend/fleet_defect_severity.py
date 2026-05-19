"""iter251 Phase A · Fleet Operations Foundation · Defect Severity Table.

🔒  v1.2 APPROVED 2026-05-19 — Operator-ruled v1 + v1.1 commercial DVIR
     refinements + v1.2 coverage-hardening pass against standard commercial
     DVIR baseline. Safety field sign-off pending field deployment. 🔒

CHANGELOG (v1.1 → v1.2, 2026-05-19 PM/2):
  • 10 commercial-DVIR coverage additions (driver-walkaround scope only ·
    no compliance theater · no checkbox bloat):
      - Engine drive belts (visible cracking / missing piece) · OOS-escalating Monitor
      - Engine hoses (coolant / heater · bulges / leaks) · OOS-escalating Monitor
      - Engine start-up health (noise / smoke / vibration) · OOS-escalating Monitor
      - Radiator (leak at neck / hoses · fins not debris-fouled) · Monitor
      - Drive line / U-joints (visual play / boot tear) · Monitor
      - Front axle (spindle nuts in place · no obvious damage) · Monitor
      - Fuel tank mounting (straps / no abrasion) · Monitor (OOS if loose)
      - Transmission operation (engages cleanly · no slip / abnormal) · OOS
      - Clutch (manual-trans only · free play · smooth engagement) · OOS
      - Trailer suspension (leaf springs / air bags · parallel to truck) · OOS
  • Intentionally NOT added (operationally not real for MASCI):
      - Tire chains (FL/TX paving ops · no snow / mountain pass)
      - Trailer roof (MASCI runs open dump / lowboy / equipment trailers)

CHANGELOG (v1 → v1.1, 2026-05-19 PM):
  • Added 5 commercial-vehicle items missing from v1:
      - Exhaust system (§ 393.83) · OOS
      - Battery hold-down / corrosion (§ 393.30) · OOS
      - Cargo securement — chains / binders / straps (§ 393.100) · OOS
      - DOT number / company markings visible (§ 390.21) · MONITOR
      - Trailer mudflaps / spray suppression (§ 393.86) · MONITOR
  • Consolidated 2 redundant tire pairs into 2 single items.
  • Tightened wording on 4 items for field clarity.
  • Removed "Cab — interior cleanliness" (operationally low-value).
  • Bumped version stamp · approval record reissued.

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
from typing import Any, Dict, Tuple

# Defect severity verdicts:
#   "oos"     · OUT OF SERVICE · truck/trailer cannot operate until
#               a defect is closed by Shop and re-enabled by Dispatch
#   "monitor" · log + photo · shop sees it · truck still operates
SEVERITY_OOS = "oos"
SEVERITY_MONITOR = "monitor"
VALID_SEVERITIES = (SEVERITY_OOS, SEVERITY_MONITOR)


# Severity table version stamp · single source of truth.
# Bump when the table changes · audit endpoint surfaces this for governance.
SEVERITY_TABLE_VERSION = "v1.2-approved-2026-05-19"
SEVERITY_TABLE_APPROVAL = {
    "version": SEVERITY_TABLE_VERSION,
    "approved_at": "2026-05-19",
    "approved_by": "Operator (Jaymn) · v1 rulings + v1.1 CFR alignment + v1.2 commercial-DVIR coverage hardening",
    "approval_record": "/app/SEVERITY_RULINGS_iter251.md",
    "status": "approved · pending Safety field deployment",
    "rulings_count": 9,
    "uncertainty_resolved": True,
    "v1_1_refinements": [
        "added: exhaust system · battery · cargo securement · DOT marking · mudflaps",
        "consolidated: 2 redundant tire pairs",
        "tightened: 4 wordings for commercial-vehicle field clarity",
        "removed: cab interior cleanliness (operationally low-value)",
    ],
    "v1_2_coverage_hardening": [
        "added: engine drive belts · engine hoses · engine start-up health",
        "added: radiator · drive line / U-joints · front axle · fuel tank mounting",
        "added: transmission operation · clutch (manual trans) · trailer suspension",
        "skipped (operational reality): tire chains · enclosed trailer roof",
    ],
}


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
# v1.1 · 2026-05-19 PM · commercial-vehicle additions
CATEGORY_EXHAUST = "exhaust"
CATEGORY_ELECTRICAL = "electrical"
CATEGORY_CARGO_SECUREMENT = "cargo_securement"
CATEGORY_MARKINGS = "markings"
# v1.2 · 2026-05-19 PM/2 · commercial-DVIR coverage hardening
CATEGORY_ENGINE = "engine"
CATEGORY_DRIVELINE = "driveline"
CATEGORY_TRANSMISSION = "transmission"
CATEGORY_FRONT_AXLE = "front_axle"
CATEGORY_OTHER = "other"


# Per-item classification: item_text → (severity, category)
# Item text MUST match the exact strings emitted by checklists_fleet.py.
FLEET_DEFECT_SEVERITY: Dict[str, Tuple[str, str]] = {
    # ─── TRUCK · BRAKES ────────────────────────────────────────────
    "Service brakes — apply firmly · stop straight · no pulling":     (SEVERITY_OOS, CATEGORY_BRAKES),
    "Parking brake — holds truck against engine torque":              (SEVERITY_OOS, CATEGORY_BRAKES),
    "Trailer hand valve — applies trailer service brakes from tractor · releases fully":    (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake chamber / slack adjuster — no visible damage · slack adjuster travel within normal range":  (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake hoses / lines — no cracks · no abrasion · no leaks":       (SEVERITY_OOS, CATEGORY_BRAKES),
    "Brake warning light / low-air buzzer — operates correctly":      (SEVERITY_OOS, CATEGORY_BRAKES),

    # ─── TRUCK · TIRES ─────────────────────────────────────────────
    # v1.1 · 2026-05-19 PM · consolidated 2 redundant tire pairs
    "Steer tire tread depth — ≥ 4/32\" across full width":            (SEVERITY_OOS, CATEGORY_TIRES),
    "Drive / trailer tire tread depth — ≥ 2/32\" across full width":  (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — no sidewall bulge · no exposed cord / belt / ply · no severe cut":  (SEVERITY_OOS, CATEGORY_TIRES),
    "Tire — properly inflated · no audible leak · no flat":           (SEVERITY_OOS, CATEGORY_TIRES),
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
    # Power steering · ruling #1 · split by drip-rate threshold (2026-05-19)
    "Power steering — fluid AT or ABOVE MIN · normal effort · no active drip":         (SEVERITY_OOS, CATEGORY_STEERING),
    "Power steering — stable seep / weep · normal effort · fluid AT MIN or above":     (SEVERITY_MONITOR, CATEGORY_STEERING),

    # ─── TRUCK · LIGHTS ────────────────────────────────────────────
    "Headlights — low beam · both sides functional":                  (SEVERITY_OOS, CATEGORY_LIGHTS),
    # High-beam · ruling #2 · split by day/night assignment (2026-05-19)
    "Headlights — both low-beams functional · at least one high-beam functional":  (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Headlights — single high-beam out · both low-beams functional · daylight-only ops":  (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Brake lights — both sides functional":                           (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Tail lights — both sides functional":                            (SEVERITY_OOS, CATEGORY_LIGHTS),
    "Clearance / marker lights — all functional":                     (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Identification lights (3-light cluster · top of cab) — all functional":       (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "License plate light — functional":                               (SEVERITY_MONITOR, CATEGORY_LIGHTS),
    "Reflectors — clean · undamaged · in place":                      (SEVERITY_MONITOR, CATEGORY_REFLECTORS),

    # ─── TRUCK · SIGNALS / ALARMS ─────────────────────────────────
    "Turn signals — left + right · front + rear functional":          (SEVERITY_OOS, CATEGORY_SIGNALS),
    "4-way hazard flashers — operate · synchronized":                 (SEVERITY_OOS, CATEGORY_SIGNALS),
    # Strobes / beacons · ruling #3 · OOS on work-zone ops · MONITOR on yard moves (2026-05-19)
    "Strobes / beacons — all flash patterns operational (work-zone / lane closure / paving / shoulder / airport ops)":  (SEVERITY_OOS, CATEGORY_SIGNALS),
    "Strobes / beacons — partial pattern acceptable for yard-only / shop-shuffle moves":  (SEVERITY_MONITOR, CATEGORY_SIGNALS),
    "Strobes / beacons — at least one operational":                   (SEVERITY_OOS, CATEGORY_SIGNALS),
    "Backup alarm — audible when reverse engaged":                    (SEVERITY_OOS, CATEGORY_ALARMS),
    "Raised-bed alarm — audible when bed raised":                     (SEVERITY_OOS, CATEGORY_ALARMS),
    "Horn — sounds at normal volume":                                 (SEVERITY_OOS, CATEGORY_HORN),

    # ─── TRUCK · MIRRORS / GLASS / WIPERS ─────────────────────────
    "Mirrors — both sides present · adjustable · clear visibility":   (SEVERITY_OOS, CATEGORY_MIRRORS),
    "Mirror — minor crack / chip with visible image":                 (SEVERITY_MONITOR, CATEGORY_MIRRORS),
    "Windshield — no cracks in driver line of sight":                 (SEVERITY_OOS, CATEGORY_GLASS),
    "Windshield — minor cracks / pitting outside line of sight":      (SEVERITY_MONITOR, CATEGORY_GLASS),
    # Wipers · ruling #4 · driver-side strict · passenger conditional on weather (2026-05-19)
    "Driver-side wiper — sweeps cleanly · no streaking · no torn blade":  (SEVERITY_OOS, CATEGORY_WIPERS),
    "Passenger-side wiper — sweeps cleanly when rain forecast in shift window":  (SEVERITY_OOS, CATEGORY_WIPERS),
    "Passenger-side wiper — minor streak acceptable · dry forecast in shift window · 3-day shop window":  (SEVERITY_MONITOR, CATEGORY_WIPERS),
    "Washer fluid — sprays · reservoir not empty":                    (SEVERITY_MONITOR, CATEGORY_WIPERS),

    # ─── TRUCK · SUSPENSION / FRAME ───────────────────────────────
    "Suspension — leaf springs · u-bolts · shackles intact":          (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Suspension — air bags inflate · no leaks · no severe sag":       (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Frame — no cracks · no severe rust-through":                     (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    # Body damage rubric · ruling #5 · 5-test objective rubric replaces vague "severe damage" (2026-05-19)
    "Body — no frame/cab-mount fracture · no projecting metal or sharp edge · no loose panel/door · no rust-through on cab floor or fuel tank · no damage blocking mirror or windshield visibility":  (SEVERITY_OOS, CATEGORY_BODY),
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
    # Hydraulic · ruling #6 · split by drip-rate + circuit role (2026-05-19)
    "Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit":  (SEVERITY_OOS, CATEGORY_HYDRAULIC),
    "Hydraulic system — stable seep / film without active drip · reservoir AT or ABOVE MIN · not on load-supporting circuit":  (SEVERITY_MONITOR, CATEGORY_HYDRAULIC),
    "Hydraulic — bed raise + lower smoothly · no drift":              (SEVERITY_OOS, CATEGORY_HYDRAULIC),
    "PTO engages + disengages normally":                              (SEVERITY_MONITOR, CATEGORY_PTO),

    # ─── TRUCK · FLUIDS ───────────────────────────────────────────
    "Engine oil — proper level · no major leak":                      (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Coolant — proper level · no major leak":                         (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Fuel — no leaks · cap secure":                                   (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Transmission fluid — proper level":                              (SEVERITY_MONITOR, CATEGORY_FLUIDS),
    "Windshield washer fluid":                                        (SEVERITY_MONITOR, CATEGORY_FLUIDS),

    # ─── TRUCK · EXHAUST / ELECTRICAL · v1.1 additions ───────────
    "Exhaust system — no leaks ahead of muffler · no fumes entering cab":  (SEVERITY_OOS, CATEGORY_EXHAUST),
    "Battery — securely mounted · no severe corrosion · cables tight":     (SEVERITY_OOS, CATEGORY_ELECTRICAL),

    # ─── TRUCK · CARGO SECUREMENT · v1.1 addition ────────────────
    "Cargo securement — chains / binders / straps rated and applied per load (flatbed / service truck)":  (SEVERITY_OOS, CATEGORY_CARGO_SECUREMENT),

    # ─── TRUCK · DOT MARKINGS · v1.1 addition ────────────────────
    "DOT number / company markings — legible · readable from 50 ft":  (SEVERITY_MONITOR, CATEGORY_MARKINGS),

    # ─── TRUCK · INTERIOR / CAB ───────────────────────────────────
    "Seat belt — present · functional · no fraying":                  (SEVERITY_OOS, CATEGORY_INTERIOR),
    # Heater/defroster · ruling #7 · defroster conditional OOS on visibility (2026-05-19)
    "Defroster — functional when ambient ≤ 40°F or precipitation forecast in shift window":  (SEVERITY_OOS, CATEGORY_INTERIOR),
    "Cab heater — functional · escalates to OOS if window fogging affects visibility":  (SEVERITY_MONITOR, CATEGORY_INTERIOR),
    # v1.1 · 2026-05-19 PM · removed "Cab — interior cleanliness" (low operational value)
    # Dash gauges · ruling #8 · tiered by ECM presence (2026-05-19)
    "Oil pressure & coolant temp gauges OR equivalent ECM warning system functional":  (SEVERITY_OOS, CATEGORY_INTERIOR),
    "Fuel gauge — functional · driver may estimate by miles · 7-day shop window":  (SEVERITY_MONITOR, CATEGORY_INTERIOR),
    "Dash gauges (oil / temp) inop on units with ECM check-engine + fault display fully functional · 14-day shop window":  (SEVERITY_MONITOR, CATEGORY_INTERIOR),

    # ─── TRUCK · ENGINE / DRIVETRAIN · v1.2 additions ────────────
    "Engine drive belts — no severe cracking · no missing piece · proper tension":  (SEVERITY_OOS, CATEGORY_ENGINE),
    "Engine hoses (coolant / heater) — no bulges · no soft spots · no active leak":  (SEVERITY_OOS, CATEGORY_ENGINE),
    "Engine start-up — starts cleanly · no abnormal noise · no excess smoke · no severe vibration":  (SEVERITY_OOS, CATEGORY_ENGINE),
    "Radiator — no leak at neck or hoses · cooling fins not severely debris-fouled":  (SEVERITY_MONITOR, CATEGORY_ENGINE),
    "Drive line / U-joints — no visible play · no boot tear · no missing strap (walk-around visual)":  (SEVERITY_MONITOR, CATEGORY_DRIVELINE),
    "Front axle — spindle nuts in place · no obvious damage to axle or knuckle":  (SEVERITY_MONITOR, CATEGORY_FRONT_AXLE),
    "Fuel tank — straps / mounts secure · no abrasion against frame":  (SEVERITY_OOS, CATEGORY_FLUIDS),
    "Transmission — engages / shifts cleanly · no slipping · no abnormal grind":  (SEVERITY_OOS, CATEGORY_TRANSMISSION),
    "Clutch (manual transmission only) — free play within range · engages smoothly":  (SEVERITY_OOS, CATEGORY_TRANSMISSION),

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
    # Tarp · ruling #9 · split by load-haul scope (2026-05-19)
    "Tarp system — deploys + retracts · no tear > 6\"×6\" · functional on units assigned to aggregate / asphalt / dust-producing load haul":  (SEVERITY_OOS, CATEGORY_TARP),
    "Tarp system — minor tear < 6\"×6\" OR unit assigned to empty / equipment / non-dust haul · 5-day shop window":  (SEVERITY_MONITOR, CATEGORY_TARP),
    "Trailer hydraulic system — no leaks · raises + lowers":          (SEVERITY_OOS, CATEGORY_HYDRAULIC),

    # ─── TRAILER · STRUCTURAL ─────────────────────────────────────
    "Trailer frame — no cracks · no severe rust":                     (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer cross members — no broken / missing":                    (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer floor — no major holes · structurally sound":            (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    "Trailer headboard / bulkhead — intact":                          (SEVERITY_OOS, CATEGORY_STRUCTURAL),
    # v1.2 · 2026-05-19 PM/2 · trailer suspension (parallel to truck suspension)
    "Trailer suspension — leaf springs · u-bolts · shackles intact (where applicable)":  (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Trailer suspension — air bags inflate · no leaks · no severe sag (where applicable)":  (SEVERITY_OOS, CATEGORY_SUSPENSION),
    "Trailer body — cosmetic damage":                                 (SEVERITY_MONITOR, CATEGORY_BODY),
    # v1.1 · 2026-05-19 PM · commercial spray-suppression
    "Trailer mudflaps / spray suppression — present · secure · no major tears":  (SEVERITY_MONITOR, CATEGORY_STRUCTURAL),
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


# ─── Per-item review metadata ────────────────────────────────────────
# Companion table consumed by the review package generator and the
# read-only severity-audit endpoint. Runtime `classify()` ignores this
# entirely — it exists purely for human review / Safety sign-off.
#
# Schema per entry:
#   regulation_ref : str   · e.g. "49 CFR § 393.40" / "CVSA OOS §1.b"
#   rationale      : str   · 1-2 sentence operational justification
#   uncertain      : bool  · True if Safety + Shop need to confirm before reliance
#
# An item missing from this table will be flagged "no_metadata" by the
# audit endpoint — forcing function so the table doesn't decay silently.

FLEET_DEFECT_SEVERITY_META: Dict[str, Dict[str, Any]] = {
    # ─── Brakes ─────────────────────────────────────────────────────
    "Service brakes — apply firmly · stop straight · no pulling": {
        "regulation_ref": "49 CFR § 393.40 · CVSA OOS §1.b",
        "rationale": "Service brake failure is the single largest OOS category in CVSA roadside inspections. Inoperable service brake on any axle or stopping-distance failure removes a CMV from service.",
        "uncertain": False,
    },
    "Parking brake — holds truck against engine torque": {
        "regulation_ref": "49 CFR § 393.41",
        "rationale": "A non-functioning parking brake creates a rollaway hazard particularly on the grades and yard slopes MASCI operates on. Always OOS.",
        "uncertain": False,
    },
    "Trailer hand valve — applies trailer service brakes from tractor · releases fully": {
        "regulation_ref": "49 CFR § 393.43 · CVSA OOS §1.b",
        "rationale": "Trailer brake control via tractor hand valve is part of the combined-vehicle braking capacity. Failure renders the combination OOS even if tractor brakes are fine. (v1.1 wording clarification 2026-05-19 PM)",
        "uncertain": False,
    },
    "Brake chamber / slack adjuster — no visible damage · slack adjuster travel within normal range": {
        "regulation_ref": "49 CFR § 393.47 · CVSA OOS §1.d",
        "rationale": "Out-of-adjustment slack adjusters or damaged brake chambers are the most common brake-stroke OOS finding at roadside. Driver checks visually for damage + extended travel · the precise stroke measurement is a shop function. (v1.1 wording clarification 2026-05-19 PM)",
        "uncertain": False,
    },
    "Brake hoses / lines — no cracks · no abrasion · no leaks": {
        "regulation_ref": "49 CFR § 393.45",
        "rationale": "Damaged brake lines lead to sudden air loss or brake fluid loss. OOS until repaired.",
        "uncertain": False,
    },
    "Brake warning light / low-air buzzer — operates correctly": {
        "regulation_ref": "49 CFR § 393.51",
        "rationale": "Driver must have audible/visual warning when air pressure drops below safe threshold. Inoperable warning system masks impending brake failure.",
        "uncertain": False,
    },
    # ─── Tires ──────────────────────────────────────────────────────
    "Steer tire tread depth — ≥ 4/32\" across full width": {
        "regulation_ref": "49 CFR § 393.75(c) · CVSA OOS §6.a",
        "rationale": "Steer tires below 4/32\" tread depth lose wet-weather grip and steering control. Federal OOS minimum.",
        "uncertain": False,
    },
    "Drive / trailer tire tread depth — ≥ 2/32\" across full width": {
        "regulation_ref": "49 CFR § 393.75(d) · CVSA OOS §6.b",
        "rationale": "Drive/trailer tires below 2/32\" tread depth · federal OOS minimum.",
        "uncertain": False,
    },
    "Tire — no sidewall bulge · no exposed cord / belt / ply · no severe cut": {
        "regulation_ref": "49 CFR § 393.75(a)(2)(3) · CVSA OOS §6.d",
        "rationale": "Sidewall bulge/cut OR exposed cord/belt/ply indicates compromised tire structural integrity · imminent catastrophic failure risk. Always OOS. (v1.1 · consolidated 2 prior items 2026-05-19 PM)",
        "uncertain": False,
    },
    "Tire — properly inflated · no audible leak · no flat": {
        "regulation_ref": "49 CFR § 393.75(h)",
        "rationale": "Severe under-inflation generates heat and risks blowout · audible leak indicates active deflation · flat tire is unsafe to operate. OOS until repaired. (v1.1 · consolidated 2 prior items 2026-05-19 PM)",
        "uncertain": False,
    },
    "Tire — minor sidewall scuff / cosmetic": {
        "regulation_ref": "operational",
        "rationale": "Cosmetic scuff with no structural compromise is not an FMCSA defect. Monitor so shop tracks wear pattern over time.",
        "uncertain": False,
    },
    # ─── Wheels ─────────────────────────────────────────────────────
    "Wheel — all lug nuts present": {
        "regulation_ref": "49 CFR § 393.205 · CVSA OOS §7.a",
        "rationale": "Any missing lug nut is OOS · risk of wheel separation.",
        "uncertain": False,
    },
    "Wheel — all lug nuts tight · no loose / clean ring": {
        "regulation_ref": "49 CFR § 393.205 · CVSA OOS §7.a",
        "rationale": "Loose lug nuts (telltale rust ring) precede wheel separation. OOS.",
        "uncertain": False,
    },
    "Wheel rim — no cracks · no welds · no severe corrosion": {
        "regulation_ref": "49 CFR § 393.205",
        "rationale": "Cracked or welded rims fail under load. OOS.",
        "uncertain": False,
    },
    "Wheel — no oil / grease leak from hub seal": {
        "regulation_ref": "49 CFR § 393.207",
        "rationale": "Hub seal leak indicates wheel bearing problem · risk of bearing seizure or wheel separation. OOS.",
        "uncertain": False,
    },
    "Wheel — no surface rust streaks (cosmetic)": {
        "regulation_ref": "operational",
        "rationale": "Surface rust is cosmetic and doesn't impair function. Monitor for shop tracking.",
        "uncertain": False,
    },
    # ─── Steering ───────────────────────────────────────────────────
    "Steering wheel free play — within spec (≤ 10° on light truck · ≤ 30° on heavy)": {
        "regulation_ref": "49 CFR § 393.209 · CVSA OOS §10",
        "rationale": "Excessive steering free play indicates worn linkage and impaired directional control. OOS.",
        "uncertain": False,
    },
    "Steering linkage / drag link / pitman arm — no missing or broken parts": {
        "regulation_ref": "49 CFR § 393.209 · CVSA OOS §10",
        "rationale": "Missing or broken steering components = imminent loss of control. Always OOS.",
        "uncertain": False,
    },
    "Power steering — fluid AT or ABOVE MIN · normal effort · no active drip": {
        "regulation_ref": "49 CFR § 393.209 · CVSA OOS criteria",
        "rationale": "Active drip / fluid below MIN / abnormal effort / pump whine = imminent steering loss · OOS. (Ruling #1 · 2026-05-19)",
        "uncertain": False,
    },
    "Power steering — stable seep / weep · normal effort · fluid AT MIN or above": {
        "regulation_ref": "49 CFR § 393.209 (operational threshold)",
        "rationale": "Stable seep without active drip + normal steering effort + fluid at or above MIN is Monitor · 5-day shop window. Active drip, abnormal effort, pump squeal, or fluid below MIN escalates to OOS. (Ruling #1 · 2026-05-19)",
        "uncertain": False,
    },
    # ─── Lights ─────────────────────────────────────────────────────
    "Headlights — low beam · both sides functional": {
        "regulation_ref": "49 CFR § 393.24",
        "rationale": "Required lighting for night operation. Loss of either side compromises visibility. OOS for night ops.",
        "uncertain": False,
    },
    "Headlights — both low-beams functional · at least one high-beam functional": {
        "regulation_ref": "49 CFR § 393.24 · CVSA OOS criteria",
        "rationale": "Both low-beams must be operational at all times. At least one high-beam must function for night ops. Any low-beam failure or both high-beams out = OOS. (Ruling #2 · 2026-05-19)",
        "uncertain": False,
    },
    "Headlights — single high-beam out · both low-beams functional · daylight-only ops": {
        "regulation_ref": "49 CFR § 393.24 (operational tier)",
        "rationale": "Single high-beam failure with both low-beams functional is Monitor for daylight-only paving/haul ops · 3-day shop window. Escalates to OOS if night work assigned. (Ruling #2 · 2026-05-19)",
        "uncertain": False,
    },
    "Brake lights — both sides functional": {
        "regulation_ref": "49 CFR § 393.25 · CVSA OOS §8.a",
        "rationale": "Both-side brake light failure is an OOS criterion. Critical for trailing-vehicle awareness.",
        "uncertain": False,
    },
    "Tail lights — both sides functional": {
        "regulation_ref": "49 CFR § 393.25 · CVSA OOS §8.a",
        "rationale": "Required for rear visibility. Both-side failure is OOS.",
        "uncertain": False,
    },
    "Clearance / marker lights — all functional": {
        "regulation_ref": "49 CFR § 393.11",
        "rationale": "Loss of one or two marker lights doesn't impair operational safety in daylight. Monitor; replace at next shop touch.",
        "uncertain": False,
    },
    "Identification lights (3-light cluster · top of cab) — all functional": {
        "regulation_ref": "49 CFR § 393.11",
        "rationale": "Required commercial lighting · top-of-cab 3-light cluster signals vehicle width to following traffic. Conservative monitor since they don't impede operation. (v1.1 wording clarification 2026-05-19 PM)",
        "uncertain": False,
    },
    "License plate light — functional": {
        "regulation_ref": "state regs",
        "rationale": "State-level requirement · monitor.",
        "uncertain": False,
    },
    "Reflectors — clean · undamaged · in place": {
        "regulation_ref": "49 CFR § 393.13 (conspicuity)",
        "rationale": "Conspicuity loss is monitor-level unless severe (handled by 'reflective tape' trailer item).",
        "uncertain": False,
    },
    # ─── Signals / alarms / horn ────────────────────────────────────
    "Turn signals — left + right · front + rear functional": {
        "regulation_ref": "49 CFR § 393.25",
        "rationale": "Required for safe lane changes/turns. Total side failure is OOS.",
        "uncertain": False,
    },
    "4-way hazard flashers — operate · synchronized": {
        "regulation_ref": "49 CFR § 393.25(d)",
        "rationale": "Required emergency warning device. OOS.",
        "uncertain": False,
    },
    "Strobes / beacons — all flash patterns operational (work-zone / lane closure / paving / shoulder / airport ops)": {
        "regulation_ref": "MASCI work-zone struck-by control · OSHA 1926 Subpart G",
        "rationale": "Work-zone struck-by is a top OSHA fatality cause in highway construction. Strobe/beacon is a primary worker-protection control · partial pattern = degraded control. OOS for any unit assigned to MOT, paving train, lane closure, shoulder, or airport ops. (Ruling #3 · 2026-05-19)",
        "uncertain": False,
    },
    "Strobes / beacons — partial pattern acceptable for yard-only / shop-shuffle moves": {
        "regulation_ref": "MASCI operational tier",
        "rationale": "Partial flash pattern acceptable for yard-only or shop-shuffle moves with no work-zone exposure · Monitor with 5-day shop window. Escalates to OOS the moment unit is assigned to work-zone ops. (Ruling #3 · 2026-05-19)",
        "uncertain": False,
    },
    "Strobes / beacons — at least one operational": {
        "regulation_ref": "MASCI operational requirement",
        "rationale": "Total beacon loss in active work zones eliminates upstream-driver warning · OOS.",
        "uncertain": False,
    },
    "Backup alarm — audible when reverse engaged": {
        "regulation_ref": "OSHA 1926.601(b)(4) · ANSI Z245.1",
        "rationale": "Required safety device for vehicles with obstructed rear vision. Pedestrian-strike risk. OOS.",
        "uncertain": False,
    },
    "Raised-bed alarm — audible when bed raised": {
        "regulation_ref": "MASCI operational standard",
        "rationale": "Critical for power-line strike avoidance and accidental drive-away with bed raised. OOS.",
        "uncertain": False,
    },
    "Horn — sounds at normal volume": {
        "regulation_ref": "49 CFR § 393.81",
        "rationale": "Required equipment. OOS.",
        "uncertain": False,
    },
    # ─── Mirrors / glass / wipers ───────────────────────────────────
    "Mirrors — both sides present · adjustable · clear visibility": {
        "regulation_ref": "49 CFR § 393.80",
        "rationale": "Required equipment. Total mirror loss on either side is OOS.",
        "uncertain": False,
    },
    "Mirror — minor crack / chip with visible image": {
        "regulation_ref": "operational",
        "rationale": "Cracked mirror that still gives a usable reflected image is monitor-level. Schedule replacement.",
        "uncertain": False,
    },
    "Windshield — no cracks in driver line of sight": {
        "regulation_ref": "49 CFR § 393.60 · CVSA OOS §11.a",
        "rationale": "Cracks in driver sight lines impair visibility. OOS.",
        "uncertain": False,
    },
    "Windshield — minor cracks / pitting outside line of sight": {
        "regulation_ref": "49 CFR § 393.60",
        "rationale": "Cosmetic damage outside vision area is monitor. Replace at next shop visit.",
        "uncertain": False,
    },
    "Driver-side wiper — sweeps cleanly · no streaking · no torn blade": {
        "regulation_ref": "49 CFR § 393.78 · CVSA OOS criteria",
        "rationale": "Driver-side visibility is non-negotiable · any streaking, torn blade, or inop wiper on driver side = OOS. Florida/Texas storms develop fast. (Ruling #4 · 2026-05-19)",
        "uncertain": False,
    },
    "Passenger-side wiper — sweeps cleanly when rain forecast in shift window": {
        "regulation_ref": "49 CFR § 393.78",
        "rationale": "Passenger-side wiper must be functional if rain is forecast in the shift window. Driver checks forecast at DVIR submission. (Ruling #4 · 2026-05-19)",
        "uncertain": False,
    },
    "Passenger-side wiper — minor streak acceptable · dry forecast in shift window · 3-day shop window": {
        "regulation_ref": "49 CFR § 393.78 (operational tier)",
        "rationale": "Minor streak on passenger-side with dry forecast is Monitor with 3-day shop window. Escalates to OOS if forecast updates to rain. (Ruling #4 · 2026-05-19)",
        "uncertain": False,
    },
    "Washer fluid — sprays · reservoir not empty": {
        "regulation_ref": "operational",
        "rationale": "Comfort/maintenance · monitor.",
        "uncertain": False,
    },
    # ─── Suspension / frame / body ──────────────────────────────────
    "Suspension — leaf springs · u-bolts · shackles intact": {
        "regulation_ref": "49 CFR § 393.207 · CVSA OOS §9",
        "rationale": "Broken springs or missing U-bolts compromise axle integrity. OOS.",
        "uncertain": False,
    },
    "Suspension — air bags inflate · no leaks · no severe sag": {
        "regulation_ref": "49 CFR § 393.207",
        "rationale": "Air suspension failure changes ride height and brake geometry. OOS.",
        "uncertain": False,
    },
    "Frame — no cracks · no severe rust-through": {
        "regulation_ref": "49 CFR § 393.201 · CVSA OOS §3",
        "rationale": "Frame cracks are structural failures · always OOS.",
        "uncertain": False,
    },
    "Body — no frame/cab-mount fracture · no projecting metal or sharp edge · no loose panel/door · no rust-through on cab floor or fuel tank · no damage blocking mirror or windshield visibility": {
        "regulation_ref": "CVSA OOS criteria · 49 CFR § 393.201 (structural)",
        "rationale": "Objective 5-test rubric replacing vague 'severe damage' wording. OOS only if damage meets one of: (a) frame/cab-mount fracture, (b) projecting metal hazardous to ground personnel, (c) loose panel/door/component at risk of falling, (d) rust-through on cab floor or fuel tank, (e) visibility-blocking damage to mirrors or windshield. Cosmetic damage = Monitor only. (Ruling #5 · 2026-05-19)",
        "uncertain": False,
    },
    "Body — cosmetic dings · scrapes · paint": {
        "regulation_ref": "operational",
        "rationale": "Cosmetic only · monitor for accountability tracking and dispute defense.",
        "uncertain": False,
    },
    # ─── Air system ─────────────────────────────────────────────────
    "Air pressure — builds to ≥ 95 psi within normal time": {
        "regulation_ref": "49 CFR § 393.50 · CVSA OOS §1.f",
        "rationale": "Build-time failure indicates compressor or governor issue · brake performance compromised. OOS.",
        "uncertain": False,
    },
    "Air system — pressure holds with engine off · ≤ 4 psi/min loss": {
        "regulation_ref": "49 CFR § 393.50 · CVSA OOS §1.c",
        "rationale": "Excessive leak-down rate is a federal OOS criterion · risk of brake failure mid-trip.",
        "uncertain": False,
    },
    "Airlines / gladhands — no audible leaks · seals intact": {
        "regulation_ref": "49 CFR § 393.45 · CVSA OOS §1",
        "rationale": "Audible leak = active air loss. OOS until repaired.",
        "uncertain": False,
    },
    "Low air warning — buzzer + light at ≤ 60 psi": {
        "regulation_ref": "49 CFR § 393.51",
        "rationale": "Required warning system. OOS.",
        "uncertain": False,
    },
    # ─── Coupling ───────────────────────────────────────────────────
    "Fifth wheel — locked · jaws fully engaged on kingpin": {
        "regulation_ref": "49 CFR § 393.70 · CVSA OOS §2.a",
        "rationale": "Unlocked or partially engaged fifth wheel = trailer separation risk. Always OOS.",
        "uncertain": False,
    },
    "Fifth wheel — mounting bolts present · no cracks": {
        "regulation_ref": "49 CFR § 393.70 · CVSA OOS §2.c",
        "rationale": "Mounting failures lead to fifth-wheel separation under load. OOS.",
        "uncertain": False,
    },
    "Safety chains — attached · no broken links · proper rating": {
        "regulation_ref": "49 CFR § 393.71",
        "rationale": "Required secondary attachment · OOS.",
        "uncertain": False,
    },
    "Pintle hook — locked · safety pin in place": {
        "regulation_ref": "49 CFR § 393.70",
        "rationale": "Pintle hitch failure = trailer separation. OOS.",
        "uncertain": False,
    },
    # ─── Hydraulic / PTO ────────────────────────────────────────────
    "Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit": {
        "regulation_ref": "OSHA 1926.602 · operational",
        "rationale": "Active drip (forms a drop within 60 sec), any leak from brake-assist line, any leak from bed-lift / boom / outrigger pressure circuit, or fluid below MIN reservoir = OOS. Bed-lift failure under load = OSHA-reportable crush hazard. (Ruling #6 · 2026-05-19)",
        "uncertain": False,
    },
    "Hydraulic system — stable seep / film without active drip · reservoir AT or ABOVE MIN · not on load-supporting circuit": {
        "regulation_ref": "OSHA 1926.602 (operational tier)",
        "rationale": "Stable seep or film without drip formation + reservoir at or above MIN + not on a load-supporting / brake-assist circuit = Monitor with 5-day shop window. (Ruling #6 · 2026-05-19)",
        "uncertain": False,
    },
    "Hydraulic — bed raise + lower smoothly · no drift": {
        "regulation_ref": "operational",
        "rationale": "Bed drift while raised is power-line and crush hazard · OOS.",
        "uncertain": False,
    },
    "PTO engages + disengages normally": {
        "regulation_ref": "operational",
        "rationale": "PTO issues stop the work the truck is dispatched for but don't make the truck unsafe to drive. Monitor.",
        "uncertain": False,
    },
    # ─── Fluids ─────────────────────────────────────────────────────
    "Engine oil — proper level · no major leak": {
        "regulation_ref": "operational",
        "rationale": "Major oil leak = engine failure or fire risk. OOS.",
        "uncertain": False,
    },
    "Coolant — proper level · no major leak": {
        "regulation_ref": "operational",
        "rationale": "Major coolant loss = engine seizure risk. OOS.",
        "uncertain": False,
    },
    "Fuel — no leaks · cap secure": {
        "regulation_ref": "49 CFR § 393.65 · CVSA OOS §4",
        "rationale": "Fuel leak = fire hazard · federal OOS criterion.",
        "uncertain": False,
    },
    "Transmission fluid — proper level": {
        "regulation_ref": "operational",
        "rationale": "Slow consumption is monitor-level · severe loss → engine/trans damage but not immediate roadway danger.",
        "uncertain": False,
    },
    "Windshield washer fluid": {
        "regulation_ref": "operational",
        "rationale": "Comfort · monitor.",
        "uncertain": False,
    },
    # ─── v1.1 additions · Exhaust / Electrical / Cargo / Markings ─
    "Exhaust system — no leaks ahead of muffler · no fumes entering cab": {
        "regulation_ref": "49 CFR § 393.83 · CVSA OOS criteria",
        "rationale": "Exhaust leaks ahead of the muffler can introduce carbon monoxide into the cab · CO poisoning is a documented commercial-driver fatality cause. Federal rule requires discharge to the outside atmosphere. OOS until repaired. (v1.1 commercial-vehicle addition 2026-05-19 PM)",
        "uncertain": False,
    },
    "Battery — securely mounted · no severe corrosion · cables tight": {
        "regulation_ref": "49 CFR § 393.30",
        "rationale": "Battery hold-down failure can drop the battery into the engine bay; severe corrosion can break the connection under load creating no-start on remote routes or interrupting safety lighting. OOS for any unsecured battery / heavy corrosion / loose cable. (v1.1 commercial-vehicle addition 2026-05-19 PM)",
        "uncertain": False,
    },
    "Cargo securement — chains / binders / straps rated and applied per load (flatbed / service truck)": {
        "regulation_ref": "49 CFR § 393.100 · CVSA OOS criteria",
        "rationale": "Load shedding from a CMV is a leading struck-by fatality cause for following traffic. Securement rule applies to any rigid cargo (equipment, pipe, pallets) on flatbed / service truck. Each tie-down rated; minimum count per length per § 393.100. OOS if missing or under-rated. (v1.1 commercial-vehicle addition 2026-05-19 PM)",
        "uncertain": False,
    },
    "DOT number / company markings — legible · readable from 50 ft": {
        "regulation_ref": "49 CFR § 390.21",
        "rationale": "Federally required CMV identification · legible from 50 feet · letters at least 2 inches tall. Monitor for fading / dirt buildup that obscures the marking. (v1.1 commercial-vehicle addition 2026-05-19 PM)",
        "uncertain": False,
    },
    # ─── Interior / cab ─────────────────────────────────────────────
    "Seat belt — present · functional · no fraying": {
        "regulation_ref": "49 CFR § 393.93",
        "rationale": "Required occupant restraint · OOS if non-functional.",
        "uncertain": False,
    },
    "Defroster — functional when ambient ≤ 40°F or precipitation forecast in shift window": {
        "regulation_ref": "49 CFR § 393.79",
        "rationale": "Defroster must be operational when ambient ≤ 40°F or precipitation forecast · driver cannot safely clear windshield/fogging without it. (Ruling #7 · 2026-05-19)",
        "uncertain": False,
    },
    "Cab heater — functional · escalates to OOS if window fogging affects visibility": {
        "regulation_ref": "49 CFR § 393.79 (operational tier)",
        "rationale": "Cab heater inop is driver-comfort Monitor only when above 40°F + dry forecast + no fogging. Escalates to OOS if fogging conditions affect windshield visibility (visibility is the actual safety concern, not comfort). 7-day shop window. (Ruling #7 · 2026-05-19)",
        "uncertain": False,
    },
    # v1.1 · 2026-05-19 PM · removed "Cab — interior cleanliness" metadata
    "Oil pressure & coolant temp gauges OR equivalent ECM warning system functional": {
        "regulation_ref": "49 CFR § 393.51 (spirit) · operational",
        "rationale": "Engine protection signal (oil pressure + coolant temp) must be functional via dash gauge OR ECM warning system. Loss of both = engine destruction risk. OOS. (Ruling #8 · 2026-05-19)",
        "uncertain": False,
    },
    "Fuel gauge — functional · driver may estimate by miles · 7-day shop window": {
        "regulation_ref": "operational",
        "rationale": "Fuel gauge inop is Monitor only · driver can estimate by miles + fuel-up records. 7-day shop window. (Ruling #8 · 2026-05-19)",
        "uncertain": False,
    },
    "Dash gauges (oil / temp) inop on units with ECM check-engine + fault display fully functional · 14-day shop window": {
        "regulation_ref": "49 CFR § 393.51 (operational tier · modern truck)",
        "rationale": "On modern trucks (≥ 2010 model year) with functional ECM check-engine + fault display, analog dash gauges are supplemental · inop gauges acceptable for Monitor with 14-day shop window. Older / non-ECM trucks remain OOS for oil-pressure or temp gauge failure. (Ruling #8 · 2026-05-19)",
        "uncertain": False,
    },
    # ─── Emergency equipment ────────────────────────────────────────
    "Fire extinguisher — present · charged · sealed · tag current": {
        "regulation_ref": "49 CFR § 393.95(a) · CVSA OOS §4.c",
        "rationale": "Federal-required equipment · missing/discharged is OOS.",
        "uncertain": False,
    },
    "Fire extinguisher — minor scuff / tag near expiry": {
        "regulation_ref": "49 CFR § 393.95(a)",
        "rationale": "Functional but cosmetic/tag-renewal needed · monitor.",
        "uncertain": False,
    },
    "Reflective triangles — 3 present · case intact": {
        "regulation_ref": "49 CFR § 393.95(f)",
        "rationale": "Federal-required emergency equipment · missing is OOS.",
        "uncertain": False,
    },
    "Reflective triangles — case scuffed (functional)": {
        "regulation_ref": "49 CFR § 393.95(f)",
        "rationale": "Equipment functional, cosmetic only · monitor.",
        "uncertain": False,
    },
    "Spare fuses — kit present": {
        "regulation_ref": "49 CFR § 393.95(c)",
        "rationale": "Required (where fuses used). Monitor.",
        "uncertain": False,
    },
    "First aid kit — present · sealed · contents not expired": {
        "regulation_ref": "OSHA 1910.151 · MASCI policy",
        "rationale": "Operational + worker-comp expectation · monitor.",
        "uncertain": False,
    },
    "Reflective safety vest — present in cab": {
        "regulation_ref": "OSHA 1926.651 · MUTCD",
        "rationale": "Required PPE for work-zone exits · monitor.",
        "uncertain": False,
    },
    # ─── Trailer items (sharing FMCSA criteria with truck side) ────
    "Trailer tire tread — ≥ 2/32\" across full width": {
        "regulation_ref": "49 CFR § 393.75(d) · CVSA OOS §6.b",
        "rationale": "Federal OOS minimum.",
        "uncertain": False,
    },
    "Trailer tire — no exposed cord / belt / sidewall damage": {
        "regulation_ref": "49 CFR § 393.75 · CVSA OOS §6.d",
        "rationale": "Imminent failure risk. OOS.",
        "uncertain": False,
    },
    "Trailer tire — properly inflated · no audible leak": {
        "regulation_ref": "49 CFR § 393.75(h)",
        "rationale": "Active deflation. OOS.",
        "uncertain": False,
    },
    "Trailer brake lights — both sides functional": {
        "regulation_ref": "49 CFR § 393.25 · CVSA OOS §8.a",
        "rationale": "Both-side failure is OOS · critical signal to following traffic.",
        "uncertain": False,
    },
    "Trailer tail lights — both sides functional": {
        "regulation_ref": "49 CFR § 393.25 · CVSA OOS §8.a",
        "rationale": "Both-side failure is OOS.",
        "uncertain": False,
    },
    "Trailer turn signals — left + right functional": {
        "regulation_ref": "49 CFR § 393.25",
        "rationale": "Required for lane changes/turns. OOS.",
        "uncertain": False,
    },
    "Trailer clearance / marker lights — all functional": {
        "regulation_ref": "49 CFR § 393.11",
        "rationale": "Conspicuity · monitor.",
        "uncertain": False,
    },
    "Trailer identification light cluster — functional": {
        "regulation_ref": "49 CFR § 393.11",
        "rationale": "Compliance lighting · monitor.",
        "uncertain": False,
    },
    "Trailer ABS lamp — operates per startup cycle": {
        "regulation_ref": "49 CFR § 393.55",
        "rationale": "ABS system status indicator · monitor (system has fallback to standard braking).",
        "uncertain": False,
    },
    "Trailer reflective tape (DOT conspicuity) — clean · undamaged": {
        "regulation_ref": "49 CFR § 393.13",
        "rationale": "Conspicuity tape · monitor.",
        "uncertain": False,
    },
    "Trailer service brakes — engage · release · no drag": {
        "regulation_ref": "49 CFR § 393.43 · CVSA OOS §1.b",
        "rationale": "Trailer brake failure compromises combination braking. OOS.",
        "uncertain": False,
    },
    "Trailer brake hoses — no cracks · no abrasion": {
        "regulation_ref": "49 CFR § 393.45",
        "rationale": "Brake line integrity · OOS.",
        "uncertain": False,
    },
    "Trailer coupler / kingpin — no cracks · no excess wear": {
        "regulation_ref": "49 CFR § 393.70 · CVSA OOS §2",
        "rationale": "Coupler failure = trailer separation. OOS.",
        "uncertain": False,
    },
    "Trailer safety chains — attached · no broken links": {
        "regulation_ref": "49 CFR § 393.71",
        "rationale": "Secondary attachment · OOS.",
        "uncertain": False,
    },
    "Landing gear — cranks freely · pads in place · no damage": {
        "regulation_ref": "49 CFR § 393.207",
        "rationale": "Landing gear failure during drop or pickup is property-damage + worker-injury risk. OOS.",
        "uncertain": False,
    },
    "Landing gear — minor cosmetic wear": {
        "regulation_ref": "operational",
        "rationale": "Cosmetic only · monitor.",
        "uncertain": False,
    },
    "Tarp system — deploys + retracts · no tear > 6\"×6\" · functional on units assigned to aggregate / asphalt / dust-producing load haul": {
        "regulation_ref": "Tex. Transp. Code § 725.021 · 49 CFR § 393.100 (load securement)",
        "rationale": "Functional tarp + no tear larger than 6\"×6\" is required for any unit assigned to aggregate, asphalt, or dust-producing load haul. Uncovered load = state ticket + struck-by debris on highway. OOS for load-haul ops. (Ruling #9 · 2026-05-19)",
        "uncertain": False,
    },
    "Tarp system — minor tear < 6\"×6\" OR unit assigned to empty / equipment / non-dust haul · 5-day shop window": {
        "regulation_ref": "MASCI operational tier",
        "rationale": "Minor tear (< 6\"×6\") OR unit assigned to empty / equipment / non-dust haul = Monitor with 5-day shop window. Escalates to OOS the moment unit reassigned to aggregate / asphalt / dust haul. (Ruling #9 · 2026-05-19)",
        "uncertain": False,
    },
    "Trailer hydraulic system — no leaks · raises + lowers": {
        "regulation_ref": "operational · OSHA",
        "rationale": "Hydraulic dump-trailer failure is operational + fire risk. OOS.",
        "uncertain": False,
    },
    "Trailer frame — no cracks · no severe rust": {
        "regulation_ref": "49 CFR § 393.201 · CVSA OOS §3",
        "rationale": "Structural failure risk. OOS.",
        "uncertain": False,
    },
    "Trailer cross members — no broken / missing": {
        "regulation_ref": "49 CFR § 393.201",
        "rationale": "Load floor integrity · OOS.",
        "uncertain": False,
    },
    "Trailer floor — no major holes · structurally sound": {
        "regulation_ref": "49 CFR § 393.201",
        "rationale": "Load drop or worker fall-through risk · OOS.",
        "uncertain": False,
    },
    "Trailer headboard / bulkhead — intact": {
        "regulation_ref": "49 CFR § 393.106",
        "rationale": "Load-shift protection for cab · OOS if compromised.",
        "uncertain": False,
    },
    "Trailer body — cosmetic damage": {
        "regulation_ref": "operational",
        "rationale": "Cosmetic only · monitor for accountability.",
        "uncertain": False,
    },
    # v1.1 commercial-vehicle addition (2026-05-19 PM)
    "Trailer mudflaps / spray suppression — present · secure · no major tears": {
        "regulation_ref": "49 CFR § 393.86 · state regs",
        "rationale": "Mudflaps protect following traffic from stones and spray kicked up from drive / trailer tires. Federal rule plus most state codes require functional flaps on commercial trailers. Monitor for partial tear, missing flap, or loose hardware · escalates to OOS if completely absent / dragging on highway. (v1.1 commercial-vehicle addition 2026-05-19 PM)",
        "uncertain": False,
    },

    # ─── v1.2 additions · Engine / Drivetrain / Trailer suspension ─
    "Engine drive belts — no severe cracking · no missing piece · proper tension": {
        "regulation_ref": "49 CFR § 393.5 · operational",
        "rationale": "Failed belt can shut down power steering, alternator, water pump, or A/C compressor mid-route. Driver pops hood and visually checks for severe cracking, glazing, or chunks missing. Tight enough that there's no slip. OOS if missing piece or imminent failure. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Engine hoses (coolant / heater) — no bulges · no soft spots · no active leak": {
        "regulation_ref": "49 CFR § 393.5 · operational",
        "rationale": "Burst coolant hose strands the truck and risks engine overheating damage. Driver checks for bulges (soft spots under pressure), staining around clamps, and dampness on the hose surface. Active leak or bulge = OOS. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Engine start-up — starts cleanly · no abnormal noise · no excess smoke · no severe vibration": {
        "regulation_ref": "operational · driver judgment",
        "rationale": "Driver knows their truck and what's normal. A hot start producing blue/white smoke, a knock, or severe vibration is real engine distress and a refusal-to-roll trigger. OOS if severe; Monitor for borderline. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Radiator — no leak at neck or hoses · cooling fins not severely debris-fouled": {
        "regulation_ref": "operational",
        "rationale": "Radiator leak at fill neck or hose joint is a coolant-loss precursor. Cooling fins packed with mud/asphalt millings reduce cooling capacity on summer haul routes. Monitor unless active drip during hot-running test. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Drive line / U-joints — no visible play · no boot tear · no missing strap (walk-around visual)": {
        "regulation_ref": "49 CFR § 393.89 · operational",
        "rationale": "True U-joint play check requires getting under the truck with a pry bar (shop function), but a walk-around can catch missing safety strap, torn boot, or grease slung around indicating bearing wear. Monitor catches these before the shaft drops. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Front axle — spindle nuts in place · no obvious damage to axle or knuckle": {
        "regulation_ref": "49 CFR § 393.205 · operational",
        "rationale": "Missing spindle nut = wheel-off hazard. Visible cracking at the steering knuckle = imminent steering failure. Quick visual during the walk-around catches these. Monitor unless something obvious found, then OOS. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Fuel tank — straps / mounts secure · no abrasion against frame": {
        "regulation_ref": "49 CFR § 393.65 · CVSA OOS criteria",
        "rationale": "Fuel tank straps loose or abraded against frame = imminent fuel leak / tank loss · fire / fuel-spill hazard. Driver sees the strap during walk-around. OOS for loose or severely abraded mount. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Transmission — engages / shifts cleanly · no slipping · no abnormal grind": {
        "regulation_ref": "operational",
        "rationale": "Slipping clutch on a manual or transmission slip on an automatic = imminent breakdown and a load-stranding risk. Driver feels this on the yard shake-down. OOS until shop diagnoses. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Clutch (manual transmission only) — free play within range · engages smoothly": {
        "regulation_ref": "operational",
        "rationale": "Manual-trans only · driver feels free play through the pedal. No free play (worn) or slipping (smoke smell · won't grab) = OOS until adjusted/replaced. Skip on automatic-trans trucks (mark N/A). (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Trailer suspension — leaf springs · u-bolts · shackles intact (where applicable)": {
        "regulation_ref": "49 CFR § 393.207 · CVSA OOS criteria",
        "rationale": "Trailer-axle suspension failures (broken leaf, cracked u-bolt, missing shackle) are CVSA OOS criteria for combination vehicles. Driver visually inspects under the trailer during walk-around. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
    "Trailer suspension — air bags inflate · no leaks · no severe sag (where applicable)": {
        "regulation_ref": "49 CFR § 393.207",
        "rationale": "Air-suspension trailers · driver checks that all bags hold pressure (no severe sag on one side) and listens for hissing leaks. Severe sag indicates broken bag or air-line failure. OOS until repaired. (v1.2 commercial-DVIR coverage 2026-05-19 PM/2)",
        "uncertain": False,
    },
}


_validate_table()

