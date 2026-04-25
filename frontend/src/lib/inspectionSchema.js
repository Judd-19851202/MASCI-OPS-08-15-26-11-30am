// Section + item definitions for the MASCI Job Site Safety Inspection form.
// Each YES/NO item maps to a field stored under the section key.

export const PPE_ITEMS = [
  { key: "all_personnel_ppe", label: "All personnel in required PPE for the task being performed" },
  { key: "hard_hats", label: "Hard hats worn where required" },
  { key: "safety_glasses", label: "Safety glasses / eye protection worn where required" },
  { key: "high_vis", label: "High-visibility apparel appropriate for operation / MOT exposure" },
  { key: "gloves", label: "Gloves appropriate for task" },
  { key: "boots", label: "Steel/composite toe boots or approved work boots" },
  { key: "hearing", label: "Hearing protection used where required" },
  { key: "respiratory", label: "Respiratory protection used where required" },
  { key: "ppe_condition", label: "PPE in good condition" },
];

export const SITE_HAZARD_ITEMS = [
  { key: "walking_surfaces", label: "Walking/working surfaces clear of slip/trip/fall hazards" },
  { key: "struck_by", label: "Struck-by hazards controlled" },
  { key: "caught_between", label: "Caught-between hazards controlled" },
  { key: "materials_stored", label: "Materials stored safely" },
  { key: "access_egress", label: "Access/egress routes clear" },
  { key: "environmental", label: "Heat stress, weather, dust, noise, and environmental exposures addressed" },
  { key: "public_interface", label: "Public interface controlled" },
  { key: "housekeeping", label: "Housekeeping acceptable" },
];

// Conditional sections: top-level Yes/No, with sub-checklist and notes when YES.
export const CONDITIONAL_SECTIONS = [
  {
    key: "equipment",
    title: "Equipment & Vehicle Safety",
    trigger: "Is equipment or company vehicle operation taking place onsite?",
    items: [
      { key: "pre_op_inspection", label: "Pre-operation inspection / walk-around completed" },
      { key: "operator_qualified", label: "Operator qualified / authorized" },
      { key: "seat_belts", label: "Seat belts worn while operating" },
      { key: "backup_alarms", label: "Back-up alarms / spotters in use" },
      { key: "swing_radius", label: "Swing radius / blind spots controlled" },
      { key: "fire_extinguisher", label: "Fire extinguisher present and inspected" },
    ],
  },
  {
    key: "traffic_control",
    title: "Traffic Control / MOT Safety",
    trigger: "Is MOT, traffic control, flagging, lane closure, or public traffic exposure present?",
    items: [
      { key: "tcp_onsite", label: "Approved Traffic Control Plan (TCP) onsite" },
      { key: "signage_devices", label: "Signage and devices match TCP" },
      { key: "flaggers_certified", label: "Flaggers certified and in proper PPE" },
      { key: "buffer_taper", label: "Buffer / taper lengths correct for speed" },
      { key: "night_lighting", label: "Night work lighting / retroreflectivity adequate" },
    ],
  },
  {
    key: "mot_moving_trucks",
    title: "MOT – Work From Moving Trucks / Fall Protection",
    trigger: "Are workers placing/removing MOT or working from the back of moving trucks/equipment?",
    items: [
      { key: "speed_controlled", label: "Truck speed controlled (5 mph or less during placement)" },
      { key: "secure_footing", label: "Workers maintain secure footing / handholds" },
      { key: "no_riding_outside", label: "No personnel riding outside designated areas" },
      { key: "communication", label: "Driver / worker communication established" },
    ],
  },
  {
    key: "fall_protection",
    title: "Fall Protection – General",
    trigger: "Is any fall exposure, elevated work, ladder use, openings, edges, structures, or tie-off required?",
    items: [
      { key: "guardrails", label: "Guardrails / covers / barricades in place" },
      { key: "harness_inspected", label: "Personal fall arrest systems inspected before use" },
      { key: "anchor_points", label: "Anchor points rated 5,000 lbs or engineered" },
      { key: "ladders_secured", label: "Ladders inspected, secured, proper angle (4:1)" },
      { key: "rescue_plan", label: "Rescue plan in place for suspended workers" },
    ],
  },
  {
    key: "excavation",
    title: "Excavation / Trenching / Underground Utilities",
    trigger: "Is excavation, trenching, pipe work, or underground utility work taking place?",
    items: [
      { key: "competent_person", label: "Competent person on site" },
      { key: "utilities_located", label: "Utilities located / 811 ticket valid" },
      { key: "protective_system", label: "Protective system (slope/shore/shield) in use ≥5 ft" },
      { key: "spoils_setback", label: "Spoils set back ≥2 ft from edge" },
      { key: "access_egress_trench", label: "Ladder/ramp access within 25 ft of workers" },
      { key: "atmospheric", label: "Atmospheric testing where required" },
    ],
  },
  {
    key: "electrical",
    title: "Electrical Safety",
    trigger: "Is electrical work, temporary power, generators, cords, lighting, pumps, or energized equipment present?",
    items: [
      { key: "gfci", label: "GFCI protection on all 120V circuits" },
      { key: "cords_inspected", label: "Cords inspected, no damage, proper gauge" },
      { key: "panels_covered", label: "Panels / boxes covered, no exposed conductors" },
      { key: "loto", label: "Lockout / tagout procedures followed where required" },
      { key: "overhead_lines", label: "Overhead line clearance maintained" },
    ],
  },
  {
    key: "concrete_paving",
    title: "Concrete / Asphalt / Paving Operations",
    trigger: "Is concrete, asphalt, milling, paving, forming, sawcutting, or hot work taking place?",
    items: [
      { key: "burn_protection", label: "Burn protection PPE for hot asphalt / concrete" },
      { key: "silica_controls", label: "Silica controls in place (water / vacuum / Table 1)" },
      { key: "saw_guards", label: "Saw blade guards in place and functional" },
      { key: "rebar_caps", label: "Rebar caps / impalement protection in place" },
      { key: "rollover_zones", label: "Roller / paver no-go zones marked, spotters used" },
    ],
  },
];

// Defaults builder
export function buildDefaults() {
  const defaults = {
    project_name: "",
    project_number: "",
    location: "",
    inspection_date: new Date().toISOString().slice(0, 10),
    inspection_time: new Date().toTimeString().slice(0, 5),
    operation: "Day",
    inspector_name: "",
    foreman_name: "",
    crew_personnel: "",
    subcontractors: "",
    weather_conditions: "",
    work_activity: "",
    ppe_compliance: {},
    site_hazards: {},
    hazards_observed: "No",
    stop_work_issued: "No",
    corrected_on_site: "N/A",
    responsible_party: "",
    corrective_action_notes: "",
    photos: [],
    inspector_signature: "",
    foreman_signature: "",
  };
  PPE_ITEMS.forEach((it) => (defaults.ppe_compliance[it.key] = ""));
  SITE_HAZARD_ITEMS.forEach((it) => (defaults.site_hazards[it.key] = ""));
  CONDITIONAL_SECTIONS.forEach((sec) => {
    defaults[sec.key] = { applies: "No", notes: "", items: {} };
    sec.items.forEach((it) => (defaults[sec.key].items[it.key] = ""));
  });
  return defaults;
}
