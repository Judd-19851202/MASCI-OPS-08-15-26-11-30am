/**
 * QA/QC inspection schema — three kinds (concrete-form, rebar,
 * subcontractor-work) share a single form component. Each kind contributes
 * its own checklist; everything else (job picker, subcontractor, photos,
 * signatures, notes) is shared.
 */

export const QAQC_KINDS = [
  {
    slug: "concrete-form",
    api_kind: "concrete_form",
    title: "Concrete Form Inspection",
    title_es: "Inspección de Formas de Concreto",
    blurb:
      "Document inspection of concrete formwork before placement.",
    blurb_es:
      "Documente la inspección de los encofrados de concreto antes del vaciado.",
    accent: "blue",
  },
  {
    slug: "rebar",
    api_kind: "rebar",
    title: "Rebar Inspection",
    title_es: "Inspección de Acero de Refuerzo",
    blurb: "Document reinforcing steel inspection before concrete placement.",
    blurb_es: "Documente la inspección del acero de refuerzo antes del vaciado de concreto.",
    accent: "amber",
  },
  {
    slug: "subcontractor-work",
    api_kind: "subcontractor_work",
    title: "Subcontractor Work Inspection",
    title_es: "Inspección de Trabajo de Subcontratista",
    blurb: "General QA/QC inspection form for any subcontractor work onsite.",
    blurb_es: "Formulario general de QA/QC para cualquier trabajo de subcontratista en obra.",
    accent: "slate",
  },
];

export function findKind(slug) {
  return QAQC_KINDS.find((k) => k.slug === slug);
}

const CONCRETE_FORM_CHECKLIST = [
  ["correct_job", "Correct job selected"],
  ["correct_location", "Correct location / station"],
  ["formwork_per_plans", "Formwork installed per plans"],
  ["line_grade", "Line and grade checked"],
  ["dimensions", "Dimensions verified"],
  ["elevation", "Elevation checked"],
  ["braced_secured", "Forms braced and secured"],
  ["clean_debris", "Forms clean and free of debris"],
  ["chamfer_keyway", "Chamfer / keyway / blockouts installed where required"],
  ["expansion_joints", "Expansion / construction joints installed where required"],
  ["embedded_items", "Embedded items / sleeves / inserts verified"],
  ["pour_area_ready", "Access and pour area ready"],
  ["safety_access", "Safety / access around formwork acceptable"],
];

const REBAR_CHECKLIST = [
  ["correct_job", "Correct job selected"],
  ["correct_location", "Correct location / station"],
  ["rebar_per_plans", "Rebar installed per plans"],
  ["bar_size", "Bar size verified"],
  ["bar_spacing", "Bar spacing verified"],
  ["bar_quantity", "Bar quantity verified"],
  ["bar_lap_lengths", "Bar lap lengths verified"],
  ["tie_spacing", "Tie spacing acceptable"],
  ["chairs_supports", "Chairs / supports installed"],
  ["concrete_cover", "Required concrete cover verified"],
  ["dowels_anchors", "Dowels / embeds / anchor bolts checked"],
  ["clean_rebar", "Rebar clean and free of mud, oil, or debris"],
  ["openings_blockouts", "Openings / blockouts verified"],
  ["ready_for_pour", "Inspection ready for concrete placement"],
];

const SUBCONTRACTOR_CHECKLIST = [
  ["matches_specs", "Work matches plans/specifications"],
  ["safe_accessible", "Work area safe and accessible"],
  ["manpower_adequate", "Subcontractor manpower adequate"],
  ["equipment_appropriate", "Equipment / materials appropriate"],
  ["workmanship", "Quality of workmanship acceptable"],
  ["layout_grade", "Layout / line / grade acceptable if applicable"],
  ["materials_correct", "Materials appear correct"],
  ["permits_approvals", "Required permits / approvals in place if applicable"],
  ["cleanup", "Work area cleaned up"],
  ["rework_required", "Rework required"],
  ["followup_required", "Follow-up inspection required"],
];

export function checklistFor(slug) {
  if (slug === "concrete-form") return CONCRETE_FORM_CHECKLIST;
  if (slug === "rebar") return REBAR_CHECKLIST;
  if (slug === "subcontractor-work") return SUBCONTRACTOR_CHECKLIST;
  return [];
}

/** Concrete-Form inspection requires extra placement-control inputs. */
export function hasConcreteFields(slug) {
  return slug === "concrete-form";
}

/** Build the empty checklist object the form starts with. */
export function buildChecklist(slug) {
  return checklistFor(slug).map(([key, label]) => ({
    key, label, result: "na", note: "",
  }));
}
