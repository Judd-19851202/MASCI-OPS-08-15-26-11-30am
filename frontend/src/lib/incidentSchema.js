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

export function buildIncidentDefaults() {
  const now = new Date();
  return {
    // 01 — Report metadata
    project_name: "",
    project_number: "",
    location: "",
    incident_date: now.toISOString().slice(0, 10),
    incident_time: now.toTimeString().slice(0, 5),
    reported_date: now.toISOString().slice(0, 10),
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

    // 08 — Evidence
    photos: [], // base64 dataURLs

    // 09 — Sign-offs
    reporter_signature: "",
    supervisor_signature: "",

    // GPS
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
  };
}
