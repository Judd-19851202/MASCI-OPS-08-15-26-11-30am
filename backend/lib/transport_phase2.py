"""TRACK 16.05 · Transportation Onboarding & Compliance Center · Phase 2.

Constants, packet-requirements catalog, MASCI Hauler Truck Readiness
Inspection checklist, default rate schedule, and bootstrap helper.
Bootstrap is idempotent · admin-safe · never overwrites operator edits.

MASCI Hauler Truck Readiness Inspection is an operational readiness
check only — it does NOT replace DOT / FMCSA inspections, the driver
pre-trip inspection, maintenance obligations, insurance obligations,
or the carrier's legal responsibility for safe operation.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TENANT = "masci"

# ---------------------------------------------------------------------------
# Disclaimer (locked in tests · must appear in every inspection record + UI).
# ---------------------------------------------------------------------------
INSPECTION_DISCLAIMER = (
    "MASCI Hauler Truck Readiness Inspection is an operational readiness "
    "check only. It does not replace the carrier's required DOT/FMCSA "
    "inspections, driver pre-trip inspection, maintenance obligations, "
    "insurance obligations, or legal responsibility for safe operation."
)

# ---------------------------------------------------------------------------
# Rate schedule constants.
# ---------------------------------------------------------------------------
DEFAULT_HOURLY_RATE = 85.00
DEFAULT_CURRENCY = "USD"

PAYMENT_RULES_TEXT = (
    "Payment is in increments of 2 hours within scheduled shifts:\n"
    "  • 0:15 to 2:00 = pays 2 hours\n"
    "  • 2:01 to 4:00 = pays 4 hours\n"
    "  • 4:01 to 6:00 = pays 6 hours\n"
    "  • 6:01 and above = pays actual time worked plus 1 hour travel time.\n"
    "Standby time is paid at 2 hours. MASCI does not pay shift minimums for "
    "standby."
)

TICKET_RULES_TEXT = (
    "Tickets must be received by 5 PM Tuesday by email or drop-off to MASCI. "
    "Tickets must be fully completed and include: company name, date, project "
    "number, truck number, start time, stop time, setup time, time loaded, "
    "arrival time on job, return time, ticket number, hold time/comments, and "
    "driver signature. Tickets without FleetWatcher GPS verification will not "
    "be paid. FleetWatcher is the only GPS system used to verify work performed."
)

DEDUCTION_RULES_TEXT = (
    "Unauthorized stops are deducted in 0.15-hour increments. An unauthorized "
    "stop while carrying hot asphalt results in an automatic 1-hour deduction "
    "regardless of stop length when less than one hour. An unauthorized stop "
    "that causes loss of asphalt may be charged back to the owner/operator."
)

# ---------------------------------------------------------------------------
# Packet requirement catalog (the Phase-1 admin UI checklist).
# ---------------------------------------------------------------------------
DOCUMENT_TYPES_CARRIER = (
    "sunbiz_certificate", "mcs_company_snapshot", "w9",
    "insurance_certificate", "hauling_agreement", "vehicle_registration",
    "lien_release_authorization", "payment_pickup_authorization", "other",
)
DOCUMENT_TYPES_DRIVER = (
    "cdl", "medical_card", "clearinghouse", "driver_license",
    "dot_certification", "drug_alcohol_acknowledgement",
    "orientation_acknowledgement_placeholder", "other",
)
REVIEW_STATUSES = (
    "pending_review", "accepted", "needs_correction", "expired", "not_applicable",
)
PACKET_STATUSES = (
    "draft", "sent", "opened", "in_progress", "submitted",
    "pending_review", "needs_correction", "approved", "suspended",
)
PACKET_TRANSITIONS = {
    "draft":              {"sent", "in_progress", "submitted"},
    "sent":               {"opened", "in_progress", "submitted", "draft"},
    "opened":             {"in_progress", "submitted"},
    "in_progress":        {"submitted", "draft"},
    "submitted":          {"pending_review", "in_progress"},
    "pending_review":     {"needs_correction", "approved", "suspended"},
    "needs_correction":   {"in_progress", "submitted", "suspended"},
    "approved":           {"suspended", "pending_review"},
    "suspended":          {"pending_review", "approved"},
}

REQUIREMENTS_CATALOG: List[Dict[str, Any]] = [
    # Carrier company-level identity
    {"requirement_key": "company_info", "target_type": "carrier",
     "label": "Company Information",
     "description": "Legal name, FEIN, FDOT/DOT, address, primary contact.",
     "required": True, "document_type": None, "expires": False,
     "default_status": "pending_review", "sort_order": 10},
    {"requirement_key": "sunbiz_certificate", "target_type": "carrier",
     "label": "Certificate of Corporation / Sunbiz Active Entity",
     "description": "Sunbiz active-entity proof.",
     "required": True, "document_type": "sunbiz_certificate",
     "expires": True, "default_status": "pending_review", "sort_order": 20},
    {"requirement_key": "mcs_company_snapshot", "target_type": "carrier",
     "label": "MCS Company Snapshot / FMCSA Proof",
     "description": "Current FMCSA / MCS company snapshot.",
     "required": True, "document_type": "mcs_company_snapshot",
     "expires": True, "default_status": "pending_review", "sort_order": 30},
    {"requirement_key": "w9", "target_type": "carrier", "label": "W-9",
     "description": "IRS Form W-9 for the carrier.",
     "required": True, "document_type": "w9", "expires": False,
     "default_status": "pending_review", "sort_order": 40},
    {"requirement_key": "insurance_certificate", "target_type": "carrier",
     "label": "Insurance Certificate",
     "description": (
         "Minimum $300,000 coverage. MASCI GENERAL CONTRACTORS, "
         "5752 S RIDGEWOOD AVE, PORT ORANGE FL 32127 listed as certificate "
         "holder / additional insured. Waiver of subrogation for general "
         "liability and workers compensation where applicable. 30-day "
         "cancellation notice (10 days for nonpayment)."),
     "required": True, "document_type": "insurance_certificate",
     "expires": True, "default_status": "pending_review", "sort_order": 50},
    {"requirement_key": "hauling_agreement", "target_type": "agreement",
     "label": "Signed Subcontractor Hauling Agreement",
     "description": (
         "Independent contractor language, no employee relationship, "
         "indemnification / hold harmless, non-discrimination, non-exclusive, "
         "trucking-law compliance responsibility, attorney fees / costs."),
     "required": True, "document_type": "hauling_agreement",
     "expires": False, "default_status": "pending_review", "sort_order": 60},
    {"requirement_key": "lien_release_authorization", "target_type": "carrier",
     "label": "Lien Release Authorization",
     "description": ("Authorized signers for lien release before the "
                     "following week's check. Photo ID required."),
     "required": True, "document_type": "lien_release_authorization",
     "expires": False, "default_status": "pending_review", "sort_order": 70},
    {"requirement_key": "payment_pickup_authorization", "target_type": "carrier",
     "label": "Payment Pickup Authorization",
     "description": "Authorized people allowed to pick up payment. ID required.",
     "required": True, "document_type": "payment_pickup_authorization",
     "expires": False, "default_status": "pending_review", "sort_order": 80},
    # Rate + acknowledgements
    {"requirement_key": "rate_acknowledgement", "target_type": "rate",
     "label": "Rate Schedule Acknowledgement",
     "description": "Acknowledges current $/hour, payment increment rules, "
                    "ticket rules, and deduction rules.",
     "required": True, "document_type": None, "expires": False,
     "default_status": "pending_review", "sort_order": 90},
    {"requirement_key": "dispatch_rules_ack", "target_type": "carrier",
     "label": "Dispatch Rules Acknowledgement",
     "description": "Truck-down notification, missed-truck replacement, "
                    "rain check-in, afternoon dispatch check-in.",
     "required": True, "document_type": None, "expires": False,
     "default_status": "pending_review", "sort_order": 100},
    {"requirement_key": "gps_fleetwatcher_ack", "target_type": "carrier",
     "label": "GPS / FleetWatcher Acknowledgement",
     "description": "Drivers clock in/out of MASCI GPS app. Only FleetWatcher "
                    "verifies tickets. Unverified tickets are not paid.",
     "required": True, "document_type": None, "expires": False,
     "default_status": "pending_review", "sort_order": 110},
    {"requirement_key": "safety_rules_ack", "target_type": "carrier",
     "label": "Safety Rules Acknowledgement",
     "description": "Firearms prohibited. Unlawful roadway discharge "
                    "prohibited. Accident/injury reporting. Damage docs.",
     "required": True, "document_type": None, "expires": False,
     "default_status": "pending_review", "sort_order": 120},
    # Driver-level rolls up via the driver_documents collection
    {"requirement_key": "driver_cdl", "target_type": "driver",
     "label": "Driver CDL (per driver)",
     "description": "Class A/B CDL copy with expiration.",
     "required": True, "document_type": "cdl", "expires": True,
     "default_status": "pending_review", "sort_order": 130},
    {"requirement_key": "driver_medical_card", "target_type": "driver",
     "label": "Driver Medical Card (per driver)",
     "description": "DOT medical certificate.",
     "required": True, "document_type": "medical_card", "expires": True,
     "default_status": "pending_review", "sort_order": 140},
    {"requirement_key": "driver_clearinghouse", "target_type": "driver",
     "label": "FMCSA Clearinghouse Documentation",
     "description": "Pre-employment Clearinghouse query result on file.",
     "required": True, "document_type": "clearinghouse", "expires": True,
     "default_status": "pending_review", "sort_order": 150},
    # Truck-level rolls up via transport_truck_inspections
    {"requirement_key": "truck_readiness_inspection", "target_type": "truck",
     "label": "MASCI Hauler Truck Readiness Inspection",
     "description": ("Operational readiness check. Does NOT replace DOT / "
                     "FMCSA inspection. Required before leased truck may haul."),
     "required": True, "document_type": None, "expires": True,
     "default_status": "pending_review", "sort_order": 160},
]

# ---------------------------------------------------------------------------
# MASCI Hauler Truck Readiness Inspection checklist.
# ---------------------------------------------------------------------------
INSPECTION_VERSION = "1.0"
INSPECTION_TYPE = "masci_hauler_readiness"
INSPECTION_DEFAULT_EXPIRATION_MONTHS = 12

INSPECTION_TRIGGERS = (
    "initial_onboarding", "annual_recertification", "random",
    "safety_concern", "customer_complaint", "incident_or_accident",
    "vehicle_replacement", "major_modification", "management_requested",
    "dispatch_requested", "safety_requested",
)

ITEM_STATUSES = ("pass", "needs_correction", "not_applicable", "not_observed")
RESULT_STATUSES = ("ready", "pending_correction", "not_ready", "expired")

# Each entry: (key, category, label, critical)
INSPECTION_CHECKLIST = [
    # ── Truck Exterior / Road Readiness ────────────────────────────────
    ("tires_serviceable",        "exterior", "Tires appear serviceable", True),
    ("lug_nuts_present",         "exterior", "All lug nuts present", True),
    ("doors_secure",             "exterior", "Doors present and secure", False),
    ("tailgate_secure",          "exterior", "Tailgate present, locks, and seals reasonably", True),
    ("bed_condition",            "exterior", "Bed condition acceptable for hauling", True),
    ("side_boards_secure",       "exterior", "Side boards present and secure where required", False),
    ("tarp_system_operational",  "exterior", "Tarp system present and operational", True),
    ("tarp_covers_bed",          "exterior", "Tarp covers bed / flips over tailgate where required", True),
    ("no_major_fluid_leaks",     "exterior", "No obvious major fluid leaks", True),
    ("no_unsafe_body_damage",    "exterior", "No obvious unsafe body damage", True),
    ("mirrors_usable",           "exterior", "Mirrors present and usable", False),
    ("windshield_acceptable",    "exterior", "Windshield condition acceptable", False),
    ("wipers_working",           "exterior", "Wipers present / working", False),
    # ── Lights / Warning Equipment ────────────────────────────────────
    ("headlights_working",       "lights", "Headlights working", True),
    ("taillights_working",       "lights", "Taillights working", True),
    ("brake_lights_working",     "lights", "Brake lights working", True),
    ("turn_signals_working",     "lights", "Turn signals working", True),
    ("four_way_flashers",        "lights", "Four-way flashers working", True),
    ("reverse_lights",           "lights", "Reverse lights working where applicable", False),
    ("backup_alarm_present",     "lights", "Backup alarm / warning device present", True),
    ("beacons_strobes",          "lights", "Beacons / strobes present where required", False),
    ("reflective_tape_visible",  "lights", "DOT reflective tape present and visible", False),
    # ── Identification / Markings ─────────────────────────────────────
    ("company_logo_displayed",   "markings", "Company logo / name displayed", True),
    ("dot_number_displayed",     "markings", "DOT number displayed where applicable", False),
    ("truck_number_displayed",   "markings", "Truck number displayed", True),
    ("masci_truck_number",       "markings", "MASCI-assigned truck number / sticker (if applicable)", False),
    ("license_plate_present",    "markings", "License plate present", True),
    ("registration_available",   "markings", "Registration available or uploaded", False),
    # ── Safety / Driver Cab ───────────────────────────────────────────
    ("seatbelt_usable",          "cab", "Seatbelt present and usable", True),
    ("cab_no_loose_objects",     "cab", "Cab generally free of unsafe loose objects", False),
    ("fire_extinguisher",        "cab", "Fire extinguisher present where required", False),
    ("cb_radio_working",         "cab", "CB radio present / working where required by MASCI", False),
    ("fleetwatcher_ready",       "cab", "FleetWatcher / GPS readiness confirmed", True),
    # ── Driver PPE / Appearance ───────────────────────────────────────
    ("ppe_hard_hat",             "ppe", "Hard hat available", True),
    ("ppe_high_vis",             "ppe", "Safety vest / high-vis available", True),
    ("ppe_safety_glasses",       "ppe", "Safety glasses available", True),
    ("ppe_work_boots",           "ppe", "Work boots appropriate", True),
    ("ppe_long_pants",           "ppe", "Long pants required — no shorts", True),
    ("ppe_shirt_required",       "ppe", "Shirt required", True),
    ("ppe_gloves",               "ppe", "Gloves available where required", False),
    ("ppe_hearing_protection",   "ppe", "Hearing protection available where required", False),
    ("ppe_acknowledged",         "ppe", "Driver understands PPE is required on MASCI jobsites", True),
]


def inspection_item_keys() -> List[str]:
    return [k for (k, _c, _l, _crit) in INSPECTION_CHECKLIST]


def critical_inspection_keys() -> List[str]:
    return [k for (k, _c, _l, crit) in INSPECTION_CHECKLIST if crit]


# ---------------------------------------------------------------------------
# Inspection result derivation.
# ---------------------------------------------------------------------------
def derive_inspection_result(items: List[Dict[str, Any]],
                             *, expires_at: Optional[str] = None
                             ) -> str:
    """Compute the overall result from item-level statuses.

    Rules:
      • If expires_at is in the past → "expired".
      • Any critical item with status=needs_correction → "not_ready".
      • Any non-critical item with status=needs_correction → "pending_correction".
      • Otherwise → "ready".
    """
    if expires_at:
        try:
            dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if dt < datetime.now(timezone.utc):
                return "expired"
        except Exception:  # noqa: BLE001
            pass
    crit = set(critical_inspection_keys())
    has_crit_nc = False
    has_nc = False
    for it in items or []:
        if it.get("status") == "needs_correction":
            if it.get("key") in crit:
                has_crit_nc = True
            else:
                has_nc = True
    if has_crit_nc:
        return "not_ready"
    if has_nc:
        return "pending_correction"
    return "ready"


def compute_next_due(inspected_at: datetime,
                     months: int = INSPECTION_DEFAULT_EXPIRATION_MONTHS
                     ) -> datetime:
    """Compute the next-due timestamp for a Readiness Inspection. We
    approximate 1 month as 30 days for predictable scheduling."""
    return inspected_at + timedelta(days=30 * months)


# ---------------------------------------------------------------------------
# Bootstrap: default rate schedule + requirements catalog.
# ---------------------------------------------------------------------------
async def bootstrap_track_16_05(db) -> Dict[str, Any]:
    """Idempotent. Safe to call on every startup. Returns a small
    summary dict for logging."""
    now = datetime.now(timezone.utc).isoformat()
    summary: Dict[str, Any] = {"rate_seeded": False, "requirements_seeded": 0}

    # ── Rate schedule ──
    existing_active = await db.transport_rate_schedules.find_one(
        {"tenant": TENANT, "status": "active"})
    if not existing_active:
        rs = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "version": "1",
            "hourly_rate": DEFAULT_HOURLY_RATE,
            "currency": DEFAULT_CURRENCY,
            "effective_date": now,
            "status": "active",
            "payment_rules_text": PAYMENT_RULES_TEXT,
            "ticket_rules_text": TICKET_RULES_TEXT,
            "deduction_rules_text": DEDUCTION_RULES_TEXT,
            "created_at": now,
            "updated_at": now,
            "created_by": "system_bootstrap",
            "updated_by": "system_bootstrap",
        }
        await db.transport_rate_schedules.insert_one(rs.copy())
        summary["rate_seeded"] = True
        try:
            await db.audit_events.insert_one({
                "id": uuid.uuid4().hex, "kind": "transport_rate_schedule_create",
                "entity_type": "rate_schedule", "entity_id": rs["id"],
                "actor": "system_bootstrap", "old": None, "new": rs,
                "ts": now, "tenant": TENANT, "route": "bootstrap",
            })
        except Exception:  # noqa: BLE001
            pass

    # ── Requirements catalog ──
    for req in REQUIREMENTS_CATALOG:
        existing = await db.transport_packet_requirements.find_one(
            {"tenant": TENANT, "requirement_key": req["requirement_key"]})
        if existing:
            continue
        doc = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "active": True,
            "created_at": now,
            "updated_at": now,
            **req,
        }
        await db.transport_packet_requirements.insert_one(doc)
        summary["requirements_seeded"] += 1

    logger.info(f"[track-16-05-bootstrap] OK · {summary}")
    return summary
