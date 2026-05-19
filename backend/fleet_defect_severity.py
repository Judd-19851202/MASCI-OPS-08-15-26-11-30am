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
from typing import Any, Dict, Tuple

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
    "Trailer air brakes — engage with hand valve · release fully": {
        "regulation_ref": "49 CFR § 393.43 · CVSA OOS §1.b",
        "rationale": "Trailer brake control is part of the combined-vehicle braking capacity. Failure renders the combination OOS even if tractor brakes are fine.",
        "uncertain": False,
    },
    "Brake chamber / slack adjuster — no visible damage · proper stroke": {
        "regulation_ref": "49 CFR § 393.47 · CVSA OOS §1.d",
        "rationale": "Out-of-adjustment slack adjusters or damaged brake chambers are the most common brake-stroke OOS finding at roadside. Conservative OOS.",
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
    "Tire — no exposed cord / belt / ply": {
        "regulation_ref": "49 CFR § 393.75(a)(3) · CVSA OOS §6.d",
        "rationale": "Exposed cord/belt indicates imminent catastrophic tire failure. Always OOS.",
        "uncertain": False,
    },
    "Tire — no severe sidewall damage (bulge / cut / cord exposed)": {
        "regulation_ref": "49 CFR § 393.75(a)(2)",
        "rationale": "Sidewall bulges/cuts compromise tire structural integrity. Always OOS.",
        "uncertain": False,
    },
    "Tire — properly inflated (no flat · no severe under-inflation)": {
        "regulation_ref": "49 CFR § 393.75(h)",
        "rationale": "Severe under-inflation generates heat and risks blowout. Flat tire is unsafe to operate. OOS.",
        "uncertain": False,
    },
    "Tire — no audible air leak": {
        "regulation_ref": "49 CFR § 393.75",
        "rationale": "Audible leak indicates active deflation. OOS until repaired.",
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
    "Power steering — no leaks · fluid at proper level · normal effort": {
        "regulation_ref": "49 CFR § 393.209",
        "rationale": "Loss of power steering mid-maneuver greatly increases driver effort and crash risk. OOS for major leaks or pump failure.",
        "uncertain": True,
        "uncertainty_note": "Borderline case: a minor weep with normal effort may be MONITOR. Safety to confirm threshold.",
    },
    # ─── Lights ─────────────────────────────────────────────────────
    "Headlights — low beam · both sides functional": {
        "regulation_ref": "49 CFR § 393.24",
        "rationale": "Required lighting for night operation. Loss of either side compromises visibility. OOS for night ops.",
        "uncertain": False,
    },
    "Headlights — high beam · both sides functional": {
        "regulation_ref": "49 CFR § 393.24",
        "rationale": "Required equipment. OOS if both inoperative.",
        "uncertain": True,
        "uncertainty_note": "Single high-beam out (low still functional) may be MONITOR in daytime ops. Safety to set policy.",
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
    "Identification lights (3-light cluster) — all functional": {
        "regulation_ref": "49 CFR § 393.11",
        "rationale": "Compliance lighting · monitor.",
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
    "Strobes / beacons — all flash patterns operational": {
        "regulation_ref": "MASCI operational requirement",
        "rationale": "Worksite visibility · partial pattern loss is monitor-level if at least one beacon still operates.",
        "uncertain": True,
        "uncertainty_note": "MASCI work zone exposure may justify OOS for any beacon loss. Safety + Ops to confirm.",
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
    "Wipers — both blades sweep windshield cleanly · no streaking": {
        "regulation_ref": "49 CFR § 393.78",
        "rationale": "Required for wet-weather visibility. Single-blade failure or severe streaking is OOS for wet/winter ops.",
        "uncertain": True,
        "uncertainty_note": "Dry-summer days a wiper issue is arguably monitor. Conservative OOS chosen.",
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
    "Body — no severe damage affecting safe operation": {
        "regulation_ref": "operational",
        "rationale": "Severe body damage that impairs safe operation (e.g. detached panel, hanging fender) is OOS.",
        "uncertain": True,
        "uncertainty_note": "Subjective threshold · Safety to define 'severe' rubric.",
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
    "Hydraulic system — no visible leaks": {
        "regulation_ref": "operational · OSHA",
        "rationale": "Major hydraulic leaks risk fire (oil on hot surfaces) + loss of bed control. OOS.",
        "uncertain": True,
        "uncertainty_note": "'Visible leak' threshold needs Shop guidance · pinhole vs active drip differs operationally.",
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
    # ─── Interior / cab ─────────────────────────────────────────────
    "Seat belt — present · functional · no fraying": {
        "regulation_ref": "49 CFR § 393.93",
        "rationale": "Required occupant restraint · OOS if non-functional.",
        "uncertain": False,
    },
    "Cab — heater / defroster operational (cold/wet weather)": {
        "regulation_ref": "49 CFR § 393.79",
        "rationale": "Defroster needed for wet/cold visibility · monitor in dry summer but should be OOS in winter (driver discretion / dispatch policy).",
        "uncertain": True,
        "uncertainty_note": "Seasonal sensitivity · Safety to set wet/cold OOS policy.",
    },
    "Cab — interior cleanliness": {
        "regulation_ref": "operational",
        "rationale": "Accountability + lead-driver visibility · monitor.",
        "uncertain": False,
    },
    "Cab — dash gauges functional (oil pressure · temp · fuel)": {
        "regulation_ref": "49 CFR § 393.51",
        "rationale": "Missing engine gauges mask catastrophic failures · OOS.",
        "uncertain": True,
        "uncertainty_note": "Modern trucks with computer-fault warning may be more permissive · Shop to confirm.",
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
    "Tarp system — deploys + retracts · no major tears": {
        "regulation_ref": "MASCI policy · state load-cover regs",
        "rationale": "Load-loss potential is a haul-completion issue, not immediate roadway danger. Monitor unless tear is catastrophic.",
        "uncertain": True,
        "uncertainty_note": "State load-cover requirements may upgrade this to OOS for some loads · Safety/Ops to confirm.",
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
}


_validate_table()

