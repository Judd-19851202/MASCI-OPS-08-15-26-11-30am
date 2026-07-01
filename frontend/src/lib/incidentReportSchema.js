// Track 19.16 · Phase B1 · Incident Intelligence Engine — Field Reporting Schema
// -----------------------------------------------------------------------------
// Declarative source of truth for the 9 incident-type flows. Each type owns
// a list of "steps"; each step owns a list of "fields". Progressive
// disclosure is driven by field-level `showIf` predicates on the current
// draft state.
//
// Every visible string is provided as an ENGLISH key. The i18n layer
// (frontend/src/lib/i18n.js) translates to Spanish at render time. Any
// new string added here MUST also live in the ES dictionary.
//
// Field types:
//   text · textarea · number · select · yesno · yesno_unsure · date · time
//   personnel_list · gps · witnesses · photos
//
// Every field is optional by default. Mark `required: true` to enforce.

// ── Shared step: Immediate Safety Status ────────────────────────────
const STEP_IMMEDIATE = {
  key: "immediate",
  label: "Immediate Safety",
  fields: [
    {
      key: "everyone_safe",
      type: "yesno_unsure",
      label: "Is everyone currently safe on scene?",
      required: true,
    },
    {
      key: "ems_needed",
      type: "yesno",
      label: "Was emergency medical response required?",
      required: true,
    },
    {
      key: "ems_on_scene",
      type: "yesno",
      label: "Is EMS on scene now?",
      showIf: (d) => d.ems_needed === "yes",
    },
    {
      key: "hazard_controlled",
      type: "yesno_unsure",
      label: "Is the immediate hazard controlled?",
      required: true,
    },
  ],
};

// ── Shared step: Location ───────────────────────────────────────────
const STEP_LOCATION = {
  key: "location",
  label: "Location",
  fields: [
    // TRACK 19.16 · UX Hardening Batch 1 — Project Picker replaces
    // manual job_number entry. `project_picker` renderer handles
    // selection + auto-fill; `project_manual_toggle` reveals plain-text
    // job_number for temporary / unlisted projects only.
    { key: "job_number", type: "project_picker", label: "Project", required: true },
    { key: "location_label", type: "text", label: "Location description", required: true },
    // GPS + weather auto-capture on the same step. Weather is derived
    // from GPS via /api/incident-intelligence/weather (no typing).
    { key: "location_gps", type: "gps", label: "GPS coordinate" },
    { key: "weather", type: "weather_auto", label: "Weather" },
  ],
};

// ── Shared step: Who Was Involved ───────────────────────────────────
const STEP_PEOPLE = {
  key: "people",
  label: "Who was involved",
  fields: [
    // Auto-filled from the current directory session; user only
    // confirms or overrides — never retypes.
    { key: "reporter_name", type: "identity_confirm", label: "Reporter", required: true },
    { key: "reporter_role", type: "text", label: "Your role", required: true },
    { key: "personnel_present", type: "personnel_list", label: "Personnel present" },
  ],
};

// ── Shared step: What Happened ──────────────────────────────────────
const STEP_WHAT_HAPPENED = {
  key: "what_happened",
  label: "What happened",
  fields: [
    { key: "occurred_at_date", type: "date", label: "Date of incident", required: true },
    { key: "occurred_at_time", type: "time", label: "Time of incident", required: true },
    {
      key: "observed_conditions",
      type: "textarea",
      label: "Describe what happened in your own words",
      required: true,
      rows: 6,
    },
  ],
};

// ── Shared step: Immediate Actions ──────────────────────────────────
const STEP_IMMEDIATE_ACTIONS = {
  key: "immediate_actions",
  label: "Immediate actions",
  fields: [
    {
      key: "immediate_actions",
      type: "textarea",
      label: "What was done immediately after?",
      required: true,
      rows: 4,
    },
    {
      key: "immediate_notifications",
      type: "textarea",
      label: "Who was notified? (one per line)",
      rows: 3,
    },
  ],
};

// ── Shared step: Evidence & Media ───────────────────────────────────
const STEP_EVIDENCE = {
  key: "evidence",
  label: "Photos & evidence",
  fields: [
    { key: "photos", type: "photos", label: "Photos" },
  ],
};

// ── Shared step: Witnesses ──────────────────────────────────────────
const STEP_WITNESSES = {
  key: "witnesses",
  label: "Witnesses",
  fields: [
    { key: "witnesses", type: "witnesses", label: "Witnesses" },
  ],
};

// ── Per-type branching steps ────────────────────────────────────────
const STEP_VEHICLE = {
  key: "vehicle",
  label: "Vehicle details",
  fields: [
    { key: "vehicle_ids", type: "vehicle_picker", label: "Vehicle(s) involved", required: true },
    { key: "drivers", type: "employee_picker", label: "Driver name(s)", required: true },
    { key: "passengers", type: "text", label: "Passenger name(s)" },
    { key: "police_response", type: "yesno", label: "Did police respond?", required: true },
    {
      key: "police_case_number",
      type: "text",
      label: "Police case number",
      showIf: (d) => d.police_response === "yes",
    },
    { key: "tow_required", type: "yesno", label: "Is tow required?", required: true },
    { key: "traffic_control", type: "yesno", label: "Is traffic control needed?" },
    { key: "third_party_involved", type: "yesno", label: "Third party involved?" },
    {
      key: "third_party_info",
      type: "textarea",
      label: "Third party name / contact / insurance",
      showIf: (d) => d.third_party_involved === "yes",
      rows: 3,
    },
  ],
};

const STEP_EQUIPMENT = {
  key: "equipment",
  label: "Equipment details",
  fields: [
    { key: "equipment_id", type: "equipment_picker", label: "Equipment involved", required: true },
    { key: "operator_name", type: "employee_picker", label: "Operator name", required: true },
    {
      key: "damage_severity",
      type: "select",
      label: "Damage severity",
      required: true,
      options: [
        { v: "minor", label: "Minor" },
        { v: "moderate", label: "Moderate" },
        { v: "major", label: "Major" },
        { v: "total_loss", label: "Total loss" },
      ],
    },
    { key: "out_of_service", type: "yesno", label: "Mark equipment out of service?", required: true },
    { key: "damage_description", type: "textarea", label: "Describe the damage", rows: 4 },
  ],
};

const STEP_UTILITY = {
  key: "utility",
  label: "Utility strike details",
  fields: [
    { key: "utility_type", type: "select", label: "Utility type", required: true, options: [
      { v: "electric", label: "Electric" },
      { v: "gas", label: "Gas" },
      { v: "water", label: "Water" },
      { v: "sewer", label: "Sewer" },
      { v: "telecom", label: "Telecom / phone" },
      { v: "fiber", label: "Fiber" },
      { v: "cable", label: "Cable / TV" },
      { v: "other", label: "Other" },
    ]},
    { key: "utility_owner", type: "text", label: "Utility owner / company", required: true },
    { key: "locate_ticket_number", type: "text", label: "811 locate ticket number", required: true },
    { key: "locate_valid", type: "yesno_unsure", label: "Was the locate valid at time of strike?" },
    { key: "service_interrupted", type: "yesno", label: "Was service interrupted?", required: true },
    { key: "emergency_response_called", type: "yesno", label: "Was emergency response called?" },
    {
      key: "isp_information",
      type: "textarea",
      label: "ISP information (for fiber)",
      showIf: (d) => d.utility_type === "fiber",
      rows: 3,
    },
  ],
};

const STEP_INJURY = {
  key: "injury",
  label: "Injury details",
  fields: [
    { key: "injured_employee", type: "employee_picker", label: "Injured employee name", required: true },
    { key: "injury_body_part", type: "text", label: "Body part affected", required: true },
    {
      key: "injury_severity",
      type: "select",
      label: "Severity",
      required: true,
      options: [
        { v: "minor", label: "Minor" },
        { v: "first_aid", label: "First aid only" },
        { v: "medical_treatment", label: "Medical treatment" },
        { v: "hospitalization", label: "Hospitalization" },
        { v: "fatality", label: "Fatality" },
      ],
    },
    { key: "first_aid_given", type: "yesno", label: "Was first aid given on scene?" },
    { key: "ems_transported", type: "yesno", label: "Did EMS transport the employee?" },
    {
      key: "hospital_name",
      type: "text",
      label: "Hospital name",
      showIf: (d) => d.injury_severity === "hospitalization" || d.ems_transported === "yes",
    },
    {
      key: "injury_description",
      type: "textarea",
      label: "Injury description",
      rows: 4,
    },
  ],
};

const STEP_NEAR_MISS = {
  key: "near_miss",
  label: "Near miss details",
  fields: [
    {
      key: "potential_consequence",
      type: "textarea",
      label: "Potential consequence if events had continued",
      required: true,
      rows: 4,
    },
    {
      key: "what_prevented_injury",
      type: "textarea",
      label: "What prevented an injury or damage?",
      required: true,
      rows: 4,
    },
    {
      key: "severity_potential",
      type: "select",
      label: "Potential severity",
      options: [
        { v: "low", label: "Low" },
        { v: "moderate", label: "Moderate" },
        { v: "high", label: "High" },
        { v: "catastrophic", label: "Catastrophic" },
      ],
    },
  ],
};

const STEP_PROPERTY = {
  key: "property_damage",
  label: "Property damage",
  fields: [
    { key: "property_owner", type: "text", label: "Property owner", required: true },
    { key: "property_owner_contact", type: "text", label: "Owner contact" },
    { key: "affected_assets", type: "textarea", label: "Affected assets", rows: 3 },
    {
      key: "estimated_damage_usd",
      type: "number",
      label: "Estimated damage (USD)",
    },
    { key: "damage_description", type: "textarea", label: "Damage description", rows: 4 },
  ],
};

const STEP_ENVIRONMENTAL = {
  key: "environmental",
  label: "Environmental details",
  fields: [
    { key: "spill_material", type: "text", label: "Material spilled", required: true },
    {
      key: "spill_volume",
      type: "text",
      label: "Estimated volume (gallons / units)",
    },
    { key: "containment_achieved", type: "yesno_unsure", label: "Is containment achieved?" },
    { key: "waterway_impact", type: "yesno_unsure", label: "Any waterway or storm-drain impact?" },
    { key: "agency_notified", type: "yesno", label: "Was a regulatory agency notified?" },
    {
      key: "agency_name",
      type: "text",
      label: "Agency name",
      showIf: (d) => d.agency_notified === "yes",
    },
    { key: "cleanup_actions", type: "textarea", label: "Cleanup actions taken", rows: 3 },
  ],
};

const STEP_VIOLENCE = {
  key: "violence",
  label: "Workplace violence details",
  fields: [
    { key: "individuals_involved", type: "textarea", label: "Individuals involved", required: true, rows: 3 },
    { key: "immediate_separation", type: "yesno", label: "Have individuals been separated?", required: true },
    { key: "law_enforcement_called", type: "yesno", label: "Was law enforcement called?", required: true },
    {
      key: "police_case_number",
      type: "text",
      label: "Police case / report number",
      showIf: (d) => d.law_enforcement_called === "yes",
    },
    { key: "restraining_order", type: "yesno_unsure", label: "Is a restraining order in place?" },
    { key: "threat_ongoing", type: "yesno_unsure", label: "Is the threat ongoing?" },
  ],
};

const STEP_COMPLAINT = {
  key: "complaint",
  label: "Public complaint details",
  fields: [
    { key: "citizen_name", type: "text", label: "Citizen name", required: true },
    { key: "citizen_contact", type: "text", label: "Citizen contact (phone / email)" },
    {
      key: "complaint_category",
      type: "select",
      label: "Complaint category",
      required: true,
      options: [
        { v: "noise", label: "Noise" },
        { v: "dust", label: "Dust" },
        { v: "traffic", label: "Traffic / detour" },
        { v: "property", label: "Property / driveway" },
        { v: "damage", label: "Alleged damage" },
        { v: "conduct", label: "Employee conduct" },
        { v: "other", label: "Other" },
      ],
    },
    { key: "resolution_attempt", type: "textarea", label: "Resolution attempted on scene", rows: 3 },
  ],
};

// ── Per-type flow assembly ──────────────────────────────────────────
const BASE_FRONT = [STEP_IMMEDIATE, STEP_LOCATION, STEP_PEOPLE, STEP_WHAT_HAPPENED];
const BASE_BACK = [STEP_IMMEDIATE_ACTIONS, STEP_EVIDENCE, STEP_WITNESSES];

export const INCIDENT_FLOWS = {
  vehicle_accident: {
    label: "Vehicle Accident",
    icon: "car",
    accent: "amber",
    description: "Company vehicle, third-party vehicle, or fleet asset collision.",
    examples: "Rear-end collision · rollover · single-vehicle · third-party impact",
    steps: [...BASE_FRONT, STEP_VEHICLE, ...BASE_BACK],
  },
  equipment_accident: {
    label: "Equipment Accident",
    icon: "wrench",
    accent: "amber",
    description: "Heavy equipment or asset involved in an accident or damage event.",
    examples: "Excavator rollover · tipped loader · struck-by · dropped load",
    steps: [...BASE_FRONT, STEP_EQUIPMENT, ...BASE_BACK],
  },
  utility_strike: {
    label: "Utility Strike",
    icon: "zap",
    accent: "red",
    description: "Contact with underground or overhead utility line.",
    examples: "Gas line · electric · fiber · water · sewer · telecom",
    steps: [...BASE_FRONT, STEP_UTILITY, ...BASE_BACK],
  },
  employee_injury: {
    label: "Employee Injury",
    icon: "heart",
    accent: "red",
    description: "An employee was hurt or required medical attention.",
    examples: "Sprain · cut · fall · struck-by · heat illness",
    steps: [...BASE_FRONT, STEP_INJURY, ...BASE_BACK],
  },
  near_miss: {
    label: "Near Miss",
    icon: "alert-triangle",
    accent: "yellow",
    description: "Something almost went wrong — no injury or damage occurred.",
    examples: "Close call · unsafe act observed · potential hazard averted",
    steps: [...BASE_FRONT, STEP_NEAR_MISS, ...BASE_BACK],
  },
  property_damage: {
    label: "Property Damage",
    icon: "home",
    accent: "amber",
    description: "Third-party or company property was damaged (no injury).",
    examples: "Fence · driveway · landscaping · sign · gate",
    steps: [...BASE_FRONT, STEP_PROPERTY, ...BASE_BACK],
  },
  environmental: {
    label: "Environmental",
    icon: "droplet",
    accent: "emerald",
    description: "Spill, release, or environmental exposure event.",
    examples: "Fuel spill · hydraulic release · concrete washout · waterway impact",
    steps: [...BASE_FRONT, STEP_ENVIRONMENTAL, ...BASE_BACK],
  },
  workplace_violence: {
    label: "Workplace Violence",
    icon: "shield",
    accent: "red",
    description: "Threat, assault, harassment, or violent conduct on site.",
    examples: "Threat · assault · harassment · verbal escalation",
    steps: [...BASE_FRONT, STEP_VIOLENCE, ...BASE_BACK],
  },
  public_complaint: {
    label: "Public Complaint",
    icon: "megaphone",
    accent: "slate",
    description: "A member of the public raised a concern about the project.",
    examples: "Noise · dust · traffic · property · conduct",
    steps: [...BASE_FRONT, STEP_COMPLAINT, ...BASE_BACK],
  },
};

// Ordered tuple used by the picker; matches Phase A INCIDENT_TYPES order.
export const INCIDENT_TYPE_ORDER = [
  "vehicle_accident",
  "equipment_accident",
  "utility_strike",
  "employee_injury",
  "near_miss",
  "property_damage",
  "environmental",
  "workplace_violence",
  "public_complaint",
];

// Utility: get the effective step list for a chosen type (guards against
// unknown keys by returning a minimal generic flow).
export function stepsFor(incidentType) {
  const flow = INCIDENT_FLOWS[incidentType];
  if (!flow) {
    return [...BASE_FRONT, ...BASE_BACK];
  }
  return flow.steps;
}

// Utility: return the list of field keys that are currently REQUIRED
// given the draft state. `showIf` gates skip hidden fields.
export function requiredFieldsForStep(step, draft) {
  return (step.fields || [])
    .filter((f) => f.required)
    .filter((f) => (typeof f.showIf === "function" ? f.showIf(draft) : true))
    .map((f) => f.key);
}

// Utility: has the user answered a field with a non-empty value?
export function hasValue(v) {
  if (v == null) return false;
  if (typeof v === "string") return v.trim().length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v).length > 0;
  return true;
}

export default INCIDENT_FLOWS;
