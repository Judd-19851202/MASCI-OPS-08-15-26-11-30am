// Field definitions for the MASCI Accident / Incident Report form.

export const INCIDENT_TYPES = [
  "Injury / Illness",
  "Near Miss",
  "Property / Equipment Damage",
  "Vehicle / Mobile Equipment",
  "Environmental Release / Spill",
  "Utility Strike",
  "Public / Third Party",
  "Security",
  "Other",
];

// TRACK 15.47 · G1 · Multi-select classifications. These are NOT the
// same as `incident_type` (which is single-select and stays in place).
// Operators tick every classification that applies. Workplace
// Violence flags automatic exec/operations notification (see backend
// safety.py G6/G10 fan-out).
export const INCIDENT_CLASSIFICATIONS = [
  "Public Interaction",
  "Verbal Confrontation",
  "Threat",
  "Harassment",
  "Trespass",
  "Property Damage",
  "Physical Contact",
  "Physical Assault",
  "Workplace Violence",
  "Weapon Displayed",
  "Weapon Used",
  "Near-Miss",
  "Media Filmed",
  "Social Media Exposure",
];

// TRACK 15.47 · G4 · Witness role enum
export const WITNESS_TYPES = [
  "employee",
  "subcontractor",
  "public",
  "police",
  "other",
];

// TRACK 15.47 · G7 · Attachment kinds
export const ATTACHMENT_KINDS = [
  { key: "photo", label: "Photo" },
  { key: "video", label: "Video" },
  { key: "witness_statement", label: "Witness Statement" },
  { key: "police_report", label: "Police Report" },
  { key: "medical", label: "Medical Documentation" },
  { key: "insurance", label: "Insurance Documentation" },
  { key: "other", label: "Other Document" },
];

// OSHA-style severity tiers — left to right increases consequence.
export const SEVERITY_LEVELS = [
  {
    key: "near_miss",
    label: "Near Miss",
    desc: "No injury, no damage — but could have happened.",
    color: "bg-slate-700",
  },
  {
    key: "first_aid",
    label: "First Aid",
    desc: "Minor — treated on-site, no further care.",
    color: "bg-emerald-600",
  },
  {
    key: "medical",
    label: "Medical Treatment",
    desc: "Required clinic / urgent-care treatment beyond first aid.",
    color: "bg-amber-500",
  },
  {
    key: "restricted",
    label: "Restricted / Light Duty",
    desc: "Worker on restricted duty after the event.",
    color: "bg-amber-600",
  },
  {
    key: "lost_time",
    label: "Lost Time (DART)",
    desc: "Days away or restricted — OSHA recordable.",
    color: "bg-red-600",
  },
  {
    key: "fatality",
    label: "Fatality / Catastrophic",
    desc: "Fatality, hospitalization, amputation, loss of eye.",
    color: "bg-red-900",
  },
];

export const BODY_PARTS = [
  "Head / Skull",
  "Face",
  "Eye",
  "Ear",
  "Neck",
  "Shoulder",
  "Upper Arm",
  "Elbow",
  "Forearm",
  "Wrist",
  "Hand",
  "Finger / Thumb",
  "Chest",
  "Back / Spine",
  "Abdomen",
  "Hip / Groin",
  "Upper Leg",
  "Knee",
  "Lower Leg",
  "Ankle",
  "Foot",
  "Toe",
  "Multiple",
  "Internal / Systemic",
];

export const INJURY_NATURES = [
  "Strain / Sprain",
  "Cut / Laceration",
  "Puncture",
  "Bruise / Contusion",
  "Fracture",
  "Burn — Heat",
  "Burn — Chemical",
  "Burn — Electrical",
  "Foreign Body in Eye",
  "Heat Illness",
  "Cold Illness / Frostbite",
  "Respiratory / Inhalation",
  "Crush",
  "Amputation",
  "Concussion / Head Injury",
  "Electric Shock",
  "Other",
];

export const ROOT_CAUSE_CATEGORIES = [
  { key: "ppe", label: "PPE not used / inadequate" },
  { key: "training", label: "Inadequate training / knowledge" },
  { key: "procedure", label: "Procedure not followed" },
  { key: "supervision", label: "Inadequate supervision" },
  { key: "equipment", label: "Equipment / tool failure" },
  { key: "design", label: "Design / engineering" },
  { key: "communication", label: "Communication breakdown" },
  { key: "fatigue", label: "Fatigue / human factors" },
  { key: "housekeeping", label: "Housekeeping / site conditions" },
  { key: "weather", label: "Weather / environment" },
  { key: "other", label: "Other" },
];

import { todayLocalIso } from "@/lib/dateUtils";

export function buildIncidentDefaults() {
  const now = new Date();
  return {
    // 01 — Report metadata
    project_name: "",
    project_number: "",
    location: "",
    incident_date: todayLocalIso(now),
    incident_time: now.toTimeString().slice(0, 5),
    reported_date: todayLocalIso(now),
    reported_by: "",
    supervisor_name: "",

    // 02 — Classification
    incident_type: "Injury / Illness",
    severity: "near_miss",
    osha_recordable: "No", // Yes / No / Unsure
    work_stopped: "No",

    // 03 — Person involved
    person_name: "",
    person_role: "",
    person_employer: "", // MASCI / subcontractor name
    person_years_experience: "",
    body_part: "",
    injury_nature: "",
    treatment_provided: "",
    medical_facility: "",
    sent_home: "No",
    // iter139 — SOT bindings (optional; freetext above still saved)
    employee_master_id: "",
    employee_master_label: "",
    equipment_master_id: "",
    equipment_master_label: "",

    // 04 — Description
    description: "",
    immediate_cause: "",
    contributing_factors: "",
    root_causes: {}, // map<key,bool> from ROOT_CAUSE_CATEGORIES
    root_cause_notes: "",

    // 05 — Witnesses
    witnesses: [], // [{name, statement}]

    // 06 — Corrective actions / follow-up
    immediate_actions_taken: "",
    corrective_actions: "", // longer-term
    responsible_party: "",
    target_completion_date: "",

    // 07 — Notifications
    notified_safety_manager: "No",
    notified_pm: "No",
    notified_gc: "No",
    notified_owner: "No",
    notified_osha: "No",
    notified_other: "",

    // 07b — Extra distribution list (PM/GC/DOT/insurance emails)
    distribution_list: [],

    // 08 — Evidence
    photos: [], // base64 dataURLs (legacy — kept working)

    // TRACK 15.47 · G7 · typed attachments. Each: {kind, label,
    // data_url, uploaded_at}. PDF renderer surfaces these in a
    // dedicated "Evidence Attachments" block.
    attachments: [],

    // TRACK 15.47 · G1 · multi-select classifications
    classifications: [],

    // TRACK 15.47 · G2 · structured threat & contact
    threat_made: false,
    threat_description: "",
    physical_contact: false,
    physical_assault: false,
    weapon_displayed: false,
    weapon_used: false,
    weapon_description: "",
    media_filmed: false,
    social_media_posted: false,

    // TRACK 15.47 · G3 · police involvement
    police_called: false,
    police_arrived: false,
    police_agency: "",
    police_officer_name: "",
    police_badge: "",
    police_case_number: "",
    police_report_number: "",
    police_report_obtained: false,
    arrest_made: false,
    citation_issued: false,

    // TRACK 15.47 · G5 · damage & claim
    damage_description: "",
    damage_estimated_value: "",
    vehicle_make_model: "",
    vehicle_vin: "",
    vehicle_plate: "",
    asset_number: "",
    insurance_claim_number: "",
    insurance_carrier: "",

    // 09 — Sign-offs
    reporter_signature: "",
    supervisor_signature: "",

    // GPS
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
  };
}
