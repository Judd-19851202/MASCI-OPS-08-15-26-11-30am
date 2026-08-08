"""Track 19.16 · Phase A · Incident Intelligence Engine — CONSTANTS.

Single source of truth for:
    * The 9 incident types (extensible without redesign).
    * The 8-state case lifecycle state machine.
    * Typed evidence taxonomy.
    * Corrective action classes.
    * Domain event types (the event spine).
    * Role → capability matrix.
    * Cross-link relationship kinds.

Everything here is data. No I/O. No side effects. Pure Python constants
so the lock test suite can import them without initialising the app.
"""
from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

# ---------------------------------------------------------------------------
# 1 · INCIDENT TYPES
# ---------------------------------------------------------------------------
# Order matters — this is the exact ordering the UI will render in
# progressive-disclosure Phase B. Extending is O(1): append a new tuple.
INCIDENT_TYPES: Tuple[Tuple[str, str, str], ...] = (
    ("vehicle_accident",     "Vehicle Accident",      "Accidente de Vehículo"),
    ("equipment_accident",   "Equipment Accident",    "Accidente de Equipo"),
    ("utility_strike",       "Utility Strike",        "Impacto a Servicio Público"),
    ("employee_injury",      "Employee Injury",       "Lesión de Empleado"),
    ("public_injury",        "Public Injury",         "Lesión al Público"),
    ("near_miss",            "Near Miss",             "Casi Accidente"),
    ("property_damage",      "Property Damage",       "Daño a la Propiedad"),
    ("environmental",        "Environmental",         "Ambiental"),
    ("workplace_violence",   "Workplace Violence",    "Violencia en el Trabajo"),
    ("public_complaint",     "Public Complaint",      "Queja del Público"),
    # ── TRACK 19.17 · additional intelligent incident types ────────
    ("fire",                 "Fire",                  "Incendio"),
    ("threat",               "Threat",                "Amenaza"),
    ("theft",                "Theft",                 "Robo"),
    ("vandalism",            "Vandalism",             "Vandalismo"),
    ("security",             "Site Security",         "Seguridad del Sitio"),
    ("hazard",               "Hazard",                "Peligro Identificado"),
    ("other",                "Other",                 "Otro"),
)

INCIDENT_TYPE_CODES: FrozenSet[str] = frozenset(t[0] for t in INCIDENT_TYPES)

# ---------------------------------------------------------------------------
# 2 · CASE LIFECYCLE STATE MACHINE
# ---------------------------------------------------------------------------
# Distinct from the LEGACY /api/incidents lifecycle. Do not merge.
CASE_STATES: Tuple[str, ...] = (
    "DRAFT",
    "FIELD_SUBMITTED",
    "SAFETY_INTAKE",
    "UNDER_INVESTIGATION",
    "CORRECTIVE_ACTIONS",
    "VERIFICATION",
    "CLOSED",
    "REOPENED",
)
CASE_DEFAULT_STATE: str = "DRAFT"

# from_state → list[to_state]
CASE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "DRAFT":               ("FIELD_SUBMITTED",),
    "FIELD_SUBMITTED":     ("SAFETY_INTAKE",),
    "SAFETY_INTAKE":       ("UNDER_INVESTIGATION",),
    "UNDER_INVESTIGATION": ("CORRECTIVE_ACTIONS",),
    "CORRECTIVE_ACTIONS":  ("VERIFICATION",),
    "VERIFICATION":        ("CLOSED",),
    "CLOSED":              ("REOPENED",),
    "REOPENED":            ("UNDER_INVESTIGATION",),
}

# States after which the Field Block becomes IMMUTABLE.
# Any subsequent attempt to mutate field-owned observations returns 409
# with code=field_block_immutable. This is the Trusted-pillar guarantee.
IMMUTABLE_AFTER_STATES: FrozenSet[str] = frozenset({
    "FIELD_SUBMITTED",
    "SAFETY_INTAKE",
    "UNDER_INVESTIGATION",
    "CORRECTIVE_ACTIONS",
    "VERIFICATION",
    "CLOSED",
    "REOPENED",
})

# ---------------------------------------------------------------------------
# 3 · EVIDENCE TYPES  (typed evidence with chain-of-custody)
# ---------------------------------------------------------------------------
EVIDENCE_TYPES: Tuple[Tuple[str, str, str, str], ...] = (
    # (code, EN label, ES label, owning_side)
    ("photo",              "Photograph",             "Fotografía",                "field"),
    ("video",              "Video",                  "Video",                     "field"),
    ("document",           "Document",               "Documento",                 "either"),
    ("gps_pin",            "GPS Coordinate",         "Coordenada GPS",            "field"),
    ("locate_ticket",      "Utility Locate Ticket",  "Boleto de Localización",    "either"),
    ("police_report",      "Police Report",          "Reporte Policial",          "safety"),
    ("medical_document",   "Medical Documentation",  "Documentación Médica",      "safety"),
    ("witness_statement",  "Witness Statement",      "Declaración de Testigo",    "safety"),
    ("inspection_record",  "Inspection Record",      "Registro de Inspección",    "safety"),
    ("equipment_record",   "Equipment Record",       "Registro de Equipo",        "safety"),
    ("external_file",      "External File",          "Archivo Externo",           "safety"),
)
EVIDENCE_TYPE_CODES: FrozenSet[str] = frozenset(e[0] for e in EVIDENCE_TYPES)

# ---------------------------------------------------------------------------
# 4 · CORRECTIVE ACTION CLASSES  (platform-wide, not incident-specific)
# ---------------------------------------------------------------------------
# The Corrective Action engine is a PLATFORM primitive — future consumers
# include JHP, Daily Reports, QA/QC, Fleet, HR, Environmental, Customer.
ACTION_CLASSES: Tuple[Tuple[str, str, str], ...] = (
    ("engineering_control",       "Engineering Control",       "Control de Ingeniería"),
    ("administrative_control",    "Administrative Control",    "Control Administrativo"),
    ("ppe",                       "Personal Protective Equipment", "Equipo de Protección Personal"),
    ("training",                  "Training",                  "Capacitación"),
    ("policy_update",             "Policy Update",             "Actualización de Política"),
    ("equipment_repair",          "Equipment Repair",          "Reparación de Equipo"),
    ("disciplinary",              "Disciplinary",              "Disciplinaria"),
    ("monitoring",                "Monitoring",                "Monitoreo"),
    ("communication",             "Communication",             "Comunicación"),
    ("root_cause_elimination",    "Root Cause Elimination",    "Eliminación de Causa Raíz"),
)
ACTION_CLASS_CODES: FrozenSet[str] = frozenset(a[0] for a in ACTION_CLASSES)

# Corrective action lifecycle
ACTION_STATES: Tuple[str, ...] = (
    "OPEN", "ASSIGNED", "IN_PROGRESS", "VERIFIED", "CANCELED",
)
ACTION_DEFAULT_STATE: str = "OPEN"

# ---------------------------------------------------------------------------
# 5 · DOMAIN EVENT TYPES  (the event spine — future consumers plug in)
# ---------------------------------------------------------------------------
# Never couple workflows to notifications directly. Emit structured events;
# let notification / dashboard / integration systems subscribe.
EVENT_TYPES: Tuple[str, ...] = (
    "case.created",
    "case.field_submitted",
    "case.state_changed",
    "case.archived",
    "case.reopened",
    "field_block.updated",
    "safety_block.updated",
    "evidence.added",
    "evidence.withdrawn",
    "witness.added",
    "corrective_action.assigned",
    "corrective_action.verified",
    "corrective_action.canceled",
    "cross_link.attached",
    "cross_link.removed",
    "recordability.changed",
    "root_cause.updated",
    "executive_review.recorded",
    "case.closed",
)
EVENT_TYPES_SET: FrozenSet[str] = frozenset(EVENT_TYPES)

# ---------------------------------------------------------------------------
# 6 · ROLE MATRIX  (who can do what)
# ---------------------------------------------------------------------------
# Roles map from the existing auth surface:
#   field  ← Field Leadership token, PM token (read-write on field_block)
#   safety ← Safety token, Admin token   (read-write on safety_block, all evidence, CAPA)
#   pm     ← PM token                    (read cases scoped to their projects)
#   shop   ← Shop token                  (read cases involving their equipment)
#   fleet  ← Fleet token                 (read cases involving their vehicles)
#   ops    ← Admin token acting as Ops   (read all)
#   exec   ← Admin token acting as Exec  (read all + reopen + override)
CAPABILITIES: Tuple[str, ...] = (
    "case.create",
    "case.read_own",
    "case.read_all",
    "field_block.write",
    "safety_block.write",
    "transition.submit",           # DRAFT → FIELD_SUBMITTED
    "transition.intake",           # FIELD_SUBMITTED → SAFETY_INTAKE
    "transition.investigate",      # SAFETY_INTAKE → UNDER_INVESTIGATION
    "transition.capa",             # UNDER_INVESTIGATION → CORRECTIVE_ACTIONS
    "transition.verify",           # CORRECTIVE_ACTIONS → VERIFICATION
    "transition.close",            # VERIFICATION → CLOSED
    "transition.reopen",           # CLOSED → REOPENED
    "evidence.add_field",
    "evidence.add_safety",
    "evidence.withdraw",
    "corrective_action.assign",
    "corrective_action.verify",
    "cross_link.write",
    "executive_review.record",
)

ROLE_MATRIX: Dict[str, FrozenSet[str]] = {
    "field": frozenset({
        "case.create",
        "case.read_own",
        "field_block.write",
        "transition.submit",
        "evidence.add_field",
    }),
    "pm": frozenset({
        "case.read_own",
        "cross_link.write",
    }),
    "safety": frozenset({
        "case.create",
        "case.read_all",
        "field_block.write",
        "safety_block.write",
        "transition.submit",
        "transition.intake",
        "transition.investigate",
        "transition.capa",
        "transition.verify",
        "transition.close",
        "transition.reopen",
        "evidence.add_field",
        "evidence.add_safety",
        "evidence.withdraw",
        "corrective_action.assign",
        "corrective_action.verify",
        "cross_link.write",
    }),
    "shop": frozenset({
        "case.read_own",
    }),
    "fleet": frozenset({
        "case.read_own",
    }),
    "ops": frozenset({
        "case.read_all",
    }),
    "exec": frozenset({
        "case.read_all",
        "transition.reopen",
        "transition.close",
        "executive_review.record",
    }),
    "admin": frozenset({  # Admin gets everything Safety has plus exec powers.
        "case.create",
        "case.read_all",
        "field_block.write",
        "safety_block.write",
        "transition.submit",
        "transition.intake",
        "transition.investigate",
        "transition.capa",
        "transition.verify",
        "transition.close",
        "transition.reopen",
        "evidence.add_field",
        "evidence.add_safety",
        "evidence.withdraw",
        "corrective_action.assign",
        "corrective_action.verify",
        "cross_link.write",
        "executive_review.record",
    }),
}

# ---------------------------------------------------------------------------
# 7 · CROSS-LINK KINDS  (cases relate to the rest of the operational graph)
# ---------------------------------------------------------------------------
CROSS_LINK_KINDS: Tuple[Tuple[str, str, str], ...] = (
    ("daily_report",   "Daily Report",   "Reporte Diario"),
    ("jhp",            "JHP",            "JHP"),
    ("employee",       "Employee",       "Empleado"),
    ("equipment",      "Equipment",      "Equipo"),
    ("fleet_asset",    "Fleet Asset",    "Activo de Flota"),
    ("job",            "Job",            "Trabajo"),
    ("customer",       "Customer",       "Cliente"),
    ("organization",   "Organization",   "Organización"),
    ("photo",          "Photo",          "Fotografía"),
    ("document",       "Document",       "Documento"),
)
CROSS_LINK_KIND_CODES: FrozenSet[str] = frozenset(k[0] for k in CROSS_LINK_KINDS)

# ---------------------------------------------------------------------------
# 8 · TRANSITION → CAPABILITY MAP
# ---------------------------------------------------------------------------
# When validating a transition, the state machine consults this map to
# resolve the capability the actor must own.
TRANSITION_CAPABILITY: Dict[Tuple[str, str], str] = {
    ("DRAFT",               "FIELD_SUBMITTED"):     "transition.submit",
    ("FIELD_SUBMITTED",     "SAFETY_INTAKE"):       "transition.intake",
    ("SAFETY_INTAKE",       "UNDER_INVESTIGATION"): "transition.investigate",
    ("UNDER_INVESTIGATION", "CORRECTIVE_ACTIONS"):  "transition.capa",
    ("CORRECTIVE_ACTIONS",  "VERIFICATION"):        "transition.verify",
    ("VERIFICATION",        "CLOSED"):              "transition.close",
    ("CLOSED",              "REOPENED"):            "transition.reopen",
    ("REOPENED",            "UNDER_INVESTIGATION"): "transition.investigate",
}

# ---------------------------------------------------------------------------
# 9 · COLLECTION NAMES  (isolated from legacy)
# ---------------------------------------------------------------------------
COLLECTION_CASES:              str = "incident_cases"
COLLECTION_CASE_EVENTS:        str = "incident_case_events"          # unified timeline + audit
COLLECTION_CASE_EVIDENCE:      str = "incident_case_evidence"
COLLECTION_CORRECTIVE_ACTIONS: str = "corrective_actions"            # PLATFORM primitive
COLLECTION_LEGACY_INCIDENTS:   str = "incidents"                     # READ-ONLY reference

__all__ = [
    "INCIDENT_TYPES", "INCIDENT_TYPE_CODES",
    "CASE_STATES", "CASE_DEFAULT_STATE", "CASE_TRANSITIONS",
    "IMMUTABLE_AFTER_STATES",
    "EVIDENCE_TYPES", "EVIDENCE_TYPE_CODES",
    "ACTION_CLASSES", "ACTION_CLASS_CODES", "ACTION_STATES", "ACTION_DEFAULT_STATE",
    "EVENT_TYPES", "EVENT_TYPES_SET",
    "CAPABILITIES", "ROLE_MATRIX",
    "CROSS_LINK_KINDS", "CROSS_LINK_KIND_CODES",
    "TRANSITION_CAPABILITY",
    "COLLECTION_CASES", "COLLECTION_CASE_EVENTS", "COLLECTION_CASE_EVIDENCE",
    "COLLECTION_CORRECTIVE_ACTIONS", "COLLECTION_LEGACY_INCIDENTS",
]
