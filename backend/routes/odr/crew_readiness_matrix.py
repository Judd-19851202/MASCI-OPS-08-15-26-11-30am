"""
routes/odr/crew_readiness_matrix.py — Crew-Type Readiness Matrix (M0.2A).

Doctrine:
  /app/memory/CREW_TYPE_READINESS_MATRIX.md (this implementation)

Three categories per crew_type:
  required     — must be addressed in every ODR for this crew
  recommended  — frequently relevant · readiness engine nudges
  advanced     — context-specific · used by FL Training Center

The keys are topic slugs; the catalog (`guidance_catalog.py`)
resolves topic-related prompt_keys per section.

This matrix powers:
  * Readiness engine targeted prompts per crew
  * FL Training Center curriculum
  * Future RFI / Schedule contextual suggestion
"""
from __future__ import annotations

from typing import Any, Dict, List

CREW_READINESS_MATRIX: Dict[str, Dict[str, List[str]]] = {

    "pipe": {
        "required": [
            "utility-verification",
            "trench-safety",
            "grade-control",
            "pipe-installation",
            "compaction",
            "joint-inspection",
            "material-handling",
        ],
        "recommended": [
            "bedding-prep-photos",
            "dewatering-strategy",
            "structure-set-photos",
            "as-built-stationing",
        ],
        "advanced": [
            "deep-trench-protection-engineered",
            "live-utility-crossing",
            "open-cut-vs-bore-decision",
        ],
    },

    "utility": {
        "required": [
            "utility-locates-verified",
            "trench-safety",
            "as-builts-captured",
            "permit-compliance",
            "compaction",
        ],
        "recommended": [
            "tie-in-photos",
            "valve-box-set",
            "hydrostatic-test-record",
        ],
        "advanced": [
            "cathodic-protection",
            "directional-bore",
        ],
    },

    "drainage": {  # alias-friendly
        "required": [
            "utility-verification",
            "structure-set-photos",
            "pipe-installation",
            "grade-control",
            "compaction",
            "outfall-protection",
        ],
        "recommended": [
            "inlet-protection-photos",
            "erosion-control",
            "tail-water-management",
        ],
        "advanced": [
            "tidal-influence-windows",
        ],
    },

    "grading": {
        "required": [
            "subgrade-prep",
            "moisture-control",
            "compaction-density",
            "grade-control",
            "haul-route-management",
        ],
        "recommended": [
            "stake-protection",
            "rain-event-recovery",
            "rough-grade-vs-fine-grade-handoff",
        ],
        "advanced": [
            "geosynthetic-placement",
            "lime-stabilization-curing",
        ],
    },

    "earthwork": {  # alias for grading at field-nomenclature level
        "required": [
            "subgrade-prep",
            "compaction-density",
            "haul-route-management",
            "stockpile-management",
            "erosion-control",
        ],
        "recommended": [
            "rain-event-recovery",
            "import-export-tracking",
        ],
        "advanced": [
            "rock-encounter-procedures",
            "deep-fill-staged-lifts",
        ],
    },

    "fine_grade": {
        "required": [
            "string-line-check",
            "compaction-density",
            "smoothness-tolerance",
            "surface-prep",
        ],
        "recommended": [
            "machine-control-verification",
            "transition-area-photos",
        ],
        "advanced": [
            "automated-grade-control-calibration",
        ],
    },

    "stabilization": {
        "required": [
            "mix-design-verified",
            "moisture-control",
            "curing-protocol",
            "depth-verification",
            "density-test",
        ],
        "recommended": [
            "cement-or-lime-application-rate",
            "moisture-mapping",
        ],
        "advanced": [
            "subgrade-treatment-redo-decision",
        ],
    },

    "paving": {
        "required": [
            "mix-temperature",
            "compaction-density",
            "mat-thickness",
            "joint-construction",
            "smoothness",
            "rolling-pattern",
        ],
        "recommended": [
            "longitudinal-joint-photos",
            "transverse-joint-construction",
            "tack-coat-rate",
            "truck-cycle-time-recording",
        ],
        "advanced": [
            "night-paving-lighting-doctrine",
            "weather-window-decision",
            "echelon-paving-coordination",
        ],
    },

    "asphalt": {  # alias for paving
        "required": [
            "mix-temperature",
            "compaction-density",
            "mat-thickness",
            "joint-construction",
            "smoothness",
        ],
        "recommended": [
            "tack-coat-rate",
            "rolling-pattern",
            "core-locations",
        ],
        "advanced": [
            "polymer-modified-mix-handling",
        ],
    },

    "milling": {
        "required": [
            "depth-verification",
            "haul-out-coordination",
            "underlying-condition-photo",
            "underground-utility-clearance",
            "sweep-and-clean",
        ],
        "recommended": [
            "tack-coat-coordination",
            "drum-wear-check",
            "transition-taper",
        ],
        "advanced": [
            "variable-depth-milling-program",
        ],
    },

    "mot": {
        "required": [
            "setup-conformance",
            "device-count",
            "sign-spacing",
            "shift-change-doctrine",
            "advance-warning-distance",
            "lane-closure-permits",
        ],
        "recommended": [
            "night-setup-photos",
            "incident-response-readiness",
            "channelizer-condition-check",
        ],
        "advanced": [
            "complex-detour-routing",
            "high-speed-corridor-protections",
        ],
    },

    "striping": {  # MOT sub-discipline · stripe + RPMs + symbols
        "required": [
            "layout-verification",
            "weather-window",
            "no-track-area-protection",
            "removal-method",
            "tape-vs-paint-decision",
        ],
        "recommended": [
            "rpm-spacing-verification",
            "symbol-placement-photos",
        ],
        "advanced": [
            "thermoplastic-temperature-control",
            "preform-application-environment",
        ],
    },

    "concrete": {
        "required": [
            "mix-design-verification",
            "slump-air-tests",
            "form-inspection",
            "rebar-placement",
            "cylinders-cast",
            "finish-quality",
            "curing-protocol",
        ],
        "recommended": [
            "weather-window-decision",
            "control-joint-placement",
            "cold-joint-prevention",
        ],
        "advanced": [
            "post-tension-protocol",
            "mass-concrete-temperature-monitoring",
        ],
    },

    "structures": {
        "required": [
            "bedding-prep-photos",
            "elevation-verification",
            "grade-adjustments",
            "manufacturer-tickets",
            "manhole-frame-set",
        ],
        "recommended": [
            "watertightness-test",
            "channel-and-bench",
        ],
        "advanced": [
            "precast-warranty-rejection-protocol",
        ],
    },

    "curb": {
        "required": [
            "string-line-check",
            "joint-spacing",
            "form-verification",
            "finish-quality",
        ],
        "recommended": [
            "curb-cut-detail",
            "ada-ramp-compliance",
        ],
        "advanced": [
            "slip-form-program",
        ],
    },

    "sidewalk": {
        "required": [
            "string-line-check",
            "compaction-of-subgrade",
            "joint-pattern",
            "finish-quality",
            "ada-cross-slope-verification",
        ],
        "recommended": [
            "color-and-texture-conformance",
        ],
        "advanced": [
            "decorative-stamp-protocol",
        ],
    },

    "airfield": {
        "required": [
            "escort-requirements",
            "runway-access-window",
            "fod-control",
            "faa-restrictions",
            "operational-window-adherence",
            "tower-radio-protocols",
            "notam-status",
        ],
        "recommended": [
            "lighting-coordination",
            "deicing-influence",
        ],
        "advanced": [
            "active-runway-side-by-side-work",
            "low-visibility-procedure-areas",
        ],
    },

    "electrical": {
        "required": [
            "lockout-tagout",
            "circuit-identification",
            "termination-photos",
            "test-records-attached",
            "energization-witness",
        ],
        "recommended": [
            "raceway-photos",
            "conduit-bend-radius-verification",
        ],
        "advanced": [
            "high-voltage-protocol",
        ],
    },

    "survey": {
        "required": [
            "control-point-set",
            "benchmark-check",
            "stationing-survey",
            "discrepancy-rfi-flag",
        ],
        "recommended": [
            "control-photo-monumentation",
            "as-built-handoff",
        ],
        "advanced": [
            "lidar-scan-coordination",
        ],
    },

    "demo": {
        "required": [
            "utility-disconnect-verified",
            "abatement-clearance",
            "dust-control",
            "haul-out-coordination",
            "asbestos-survey-status",
        ],
        "recommended": [
            "selective-demo-photo",
            "salvage-tracking",
        ],
        "advanced": [
            "controlled-blasting-protocol",
        ],
    },

    "other": {
        "required": [
            "operation-description",
            "manpower-and-equipment-record",
            "safety-self-check",
            "photo-of-work-performed",
        ],
        "recommended": [
            "tie-back-to-cleat-discipline",
        ],
        "advanced": [],
    },
}


def crew_required_topics(crew_type: str) -> List[str]:
    return list(CREW_READINESS_MATRIX.get(crew_type, {}).get("required", []))


def matrix_health() -> Dict[str, Any]:
    return {
        "crews": sorted(CREW_READINESS_MATRIX.keys()),
        "count": len(CREW_READINESS_MATRIX),
        "required_floor_4": [
            c for c, m in CREW_READINESS_MATRIX.items()
            if len(m.get("required") or []) < 4
        ],
    }


__all__ = ["CREW_READINESS_MATRIX", "crew_required_topics", "matrix_health"]
