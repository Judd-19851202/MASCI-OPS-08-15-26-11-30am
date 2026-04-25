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

// Conditional sections: top-level Yes/No. Sub-checklist + notes appear when YES is selected.
// Items are VERBATIM from the original MASCI form (provided by user).
// `autoFail: true` items, when answered NO, flag the report as a critical safety failure.
export const CONDITIONAL_SECTIONS = [
  {
    key: "equipment",
    title: "Equipment & Vehicle Safety",
    trigger: "Is equipment or company vehicle operation taking place onsite?",
    items: [
      { key: "daily_inspections", label: "Daily equipment inspections completed" },
      { key: "seatbelts", label: "Seatbelts used", autoFail: true },
      { key: "backup_alarms", label: "Backup alarms / horns operational" },
      { key: "lights_strobes", label: "Lights, strobes, and beacons operational where required" },
      { key: "fire_extinguishers", label: "Fire extinguishers present, charged, and accessible" },
      { key: "no_leaks_defects", label: "Equipment free of visible leaks or unsafe defects" },
      { key: "spotters", label: "Spotters used where required" },
      { key: "parked_safely", label: "Equipment parked/staged safely when not in use" },
    ],
  },
  {
    key: "traffic_control",
    title: "Traffic Control / MOT Safety",
    trigger: "Is MOT, traffic control, flagging, lane closure, or public traffic exposure present?",
    items: [
      { key: "mot_matches_plan", label: "MOT setup matches approved plan / field condition", autoFail: true },
      { key: "devices_installed", label: "Signs, cones, barrels, barricades, and devices properly installed" },
      { key: "flaggers_trained", label: "Flaggers trained, visible, and positioned safely" },
      { key: "public_exposure", label: "Pedestrian/public exposure controlled" },
      { key: "night_lighting", label: "Night lighting adequate if working at night" },
      { key: "workers_protected", label: "Workers protected from live traffic / equipment movement", autoFail: true },
    ],
  },
  {
    key: "mot_moving_trucks",
    title: "MOT – Work From Moving Trucks / Fall Protection",
    trigger: "Are workers placing/removing MOT or working from the back of moving trucks/equipment?",
    items: [
      { key: "harness_worn", label: "Full-body harness worn by exposed workers", autoFail: true },
      { key: "tied_off", label: "Workers tied off while working from moving vehicle/equipment", autoFail: true },
      { key: "rated_anchor", label: "Approved/rated anchor point used — no improvised tie-off", autoFail: true },
      { key: "tie_off_maintained", label: "Tie-off maintained during operation" },
      { key: "truck_speed", label: "Truck speed controlled and coordinated with crew" },
      { key: "no_mount_dismount", label: "No mounting/dismounting while vehicle is moving" },
      { key: "driver_comms", label: "Driver/crew communication established" },
      { key: "platform_clear", label: "Work platform free of slip/trip hazards" },
      { key: "spotter_awareness", label: "Spotter/traffic awareness maintained" },
    ],
  },
  {
    key: "fall_protection",
    title: "Fall Protection – General",
    trigger: "Is any fall exposure, elevated work, ladder use, openings, edges, structures, or tie-off required?",
    items: [
      { key: "fp_in_place", label: "Fall protection in place where required", autoFail: true },
      { key: "harness_inspected", label: "Harness/lanyard/SRL inspected prior to use" },
      { key: "approved_anchors", label: "Approved anchor points used", autoFail: true },
      { key: "guardrails_covers", label: "Guardrails/covers installed and secured where applicable" },
      { key: "ladders_secured", label: "Ladders used properly and secured as required" },
      { key: "openings_protected", label: "Open holes/edges protected or clearly marked" },
    ],
  },
  {
    key: "excavation",
    title: "Excavation / Trenching / Underground Utilities",
    trigger: "Is excavation, trenching, pipe work, or underground utility work taking place?",
    items: [
      { key: "competent_person", label: "Competent person inspection completed", autoFail: true },
      { key: "utilities_located", label: "Utilities located/marked and respected", autoFail: true },
      { key: "protective_system", label: "Protective system used where required: slope, shield, shoring, or bench", autoFail: true },
      { key: "access_egress", label: "Safe access/egress provided" },
      { key: "spoil_setback", label: "Spoil pile/materials kept back from edge" },
      { key: "water_controlled", label: "Water accumulation controlled" },
      { key: "swing_radius", label: "Employees kept out from under suspended loads and equipment swing radius" },
    ],
  },
  {
    key: "electrical",
    title: "Electrical Safety",
    trigger: "Is electrical work, temporary power, generators, cords, lighting, pumps, or energized equipment present?",
    items: [
      { key: "gfci", label: "GFCI protection used where required", autoFail: true },
      { key: "cords_condition", label: "Cords/tools in good condition with no exposed conductors" },
      { key: "panels_secured", label: "Panels/generators secured and protected" },
      { key: "overhead_underground", label: "Overhead/underground electrical hazards identified" },
      { key: "loto", label: "Lockout/tagout or energy control used when applicable", autoFail: true },
    ],
  },
  {
    key: "concrete_paving",
    title: "Concrete / Asphalt / Paving Operations",
    trigger: "Is concrete, asphalt, milling, paving, forming, sawcutting, or hot work taking place?",
    items: [
      { key: "burn_protection", label: "Burn protection and task-specific PPE used" },
      { key: "rebar_protected", label: "Rebar/dowels protected or capped where exposure exists" },
      { key: "formwork_stable", label: "Formwork stable and access routes maintained" },
      { key: "silica_controls", label: "Silica/dust controls used for cutting/grinding/sawing where required" },
      { key: "separation", label: "Equipment/personnel separation maintained" },
      { key: "hot_materials", label: "Hot materials, tack, fuel, and chemicals handled safely" },
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
