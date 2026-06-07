// Phase 10D · Daily Report compliance engine (pure function)
// Phase 10D.2 · Extended with photo-category intelligence + section
// completion chips.

const REQUIRED_PHOTO_KINDS = [
  { key: "overall",   label: "Overall Work Area" },
  { key: "work",      label: "Work Performed" },
  { key: "crew",      label: "Crew / Equipment" },
  { key: "material",  label: "Materials / Production" },
  { key: "safety",    label: "Safety Condition" },
  { key: "closeout",  label: "End-of-Day / Closeout" },
];

const EXCAVATION_PHOTO_KINDS = [
  { key: "exc_overview",  label: "Excavation Overview" },
  { key: "exc_protect",   label: "Protective System" },
  { key: "exc_access",    label: "Access / Egress" },
  { key: "exc_utility",   label: "Utility Markings" },
];

function _photoTagMatches(photo, kind) {
  const cand = String(photo?.kind || photo?.category || photo?.tag || photo?.label || "").toLowerCase();
  return cand.includes(kind);
}

function computeRequiredPhotoCategories(d, opts) {
  const required = [...REQUIRED_PHOTO_KINDS];
  const isExc = String(d.excavation_activity_today || "").toLowerCase() === "yes";
  const isIncident = d.safety_incidents_today === "Yes" || d.injuries_reported === "Yes";
  const isWeather = d.weather_impact === "Yes";
  if (isExc) required.push(...EXCAVATION_PHOTO_KINDS);
  if (isIncident) required.push({ key: "incident", label: "Incident / Near Miss" });
  if (isWeather) required.push({ key: "weather", label: "Weather Impact" });

  const photos = d.photos || [];
  // If a photo has no kind tag, count it against the first missing required slot.
  const taggedRemaining = photos.filter((p) => !p?.kind && !p?.category && !p?.tag);
  let untaggedPool = taggedRemaining.length;

  return required.map(({ key, label }) => {
    const matched = photos.filter((p) => _photoTagMatches(p, key)).length;
    if (matched > 0) {
      return { key, label, matched, status: "ok" };
    }
    if (untaggedPool > 0) {
      untaggedPool -= 1;
      return { key, label, matched: 0, status: "ok-untagged" };
    }
    return { key, label, matched: 0, status: "missing" };
  });
}

export function computeDailyReportCompliance(d, opts = {}) {
  const photoMin = opts.photoMin || d.photo_min || 6;
  const requirements = [];
  const add = (id, severity, title, why, action) =>
    requirements.push({ id, severity, title, why, action });

  // Job + identity
  if (!String(d.project_name || "").trim()) {
    add("project", "danger", "Project not selected",
      "Pick a MASCI Job (or Custom) so the report ties to a project number.",
      "Use the Job picker at the top of the form.");
  }
  if (!String(d.prepared_by || "").trim()) {
    add("prepared_by", "danger", "Prepared By is empty",
      "Every Daily Report must name the person submitting it.",
      "Pick yourself from the roster or type your name.");
  }
  if (!String(d.location || "").trim()) {
    add("location", "warn", "Location not entered",
      "Owners and the GC look at location for context.",
      "Add the work area / street / station.");
  }

  // Excavation activity gate
  const exc = String(d.excavation_activity_today || "No").toLowerCase();
  if (exc === "yes" && (d.linked_excavation_ids || []).length === 0) {
    add("excavation_link", "danger", "Excavation Activity is YES — link a record",
      "Daily Reports cannot be submitted without an Excavation Record when crews worked in a trench today.",
      "Create New or Link Existing in the Excavation Activity panel below.");
  }

  // Trigger-based gates
  if (d.weather_impact === "Yes" && !(d.constraints || []).some((r) => (r?.constraint_type || "").toLowerCase() === "weather")) {
    add("weather_row", "warn", "Weather Impact = YES — add a Weather row",
      "When weather impacted production, add a Delay/Extra Work row tagged Weather so the schedule team can see it.",
      "Open the Delays / Extra Work section and add a Weather row.");
  }
  if (d.schedule_delays === "Yes" && (d.constraints || []).length === 0) {
    add("delay_row", "warn", "Delays / Extra Work = YES — add a row",
      "Pick the cause and a short note so the PM can act on it.",
      "Open Delays / Extra Work and add one row.");
  }
  const hasIncident = d.safety_incidents_today === "Yes" || d.injuries_reported === "Yes";
  if (hasIncident) {
    if (d.safety_notified !== "Yes") {
      add("safety_notified", "danger", "Safety must be notified",
        "When an incident or injury is reported, Safety must be contacted before this Daily Report can be submitted.",
        "Mark Safety Notified = Yes after calling.");
    }
    if (d.incident_report_filled !== "Yes") {
      add("incident_report", "danger", "Incident/Injury Report missing",
        "An incident or injury also requires a separate Incident Report.",
        "File the Incident Report, then return here.");
    }
  }

  // Crew
  if ((d.masci_crews || []).length === 0 && (d.subcontractors || []).length === 0) {
    add("crew", "warn", "No crew or subs on the report yet",
      "Most Daily Reports list at least one crew or sub on site.",
      "Add MASCI crew rows, or use the 'Use yesterday's crew' button if available.");
  }

  // Phase 10D.2 · Photo category intelligence
  const photoCategories = computeRequiredPhotoCategories(d, opts);
  const photoMissing = photoCategories.filter((p) => p.status === "missing");
  if ((d.photos || []).length < photoMin) {
    const need = photoMin - (d.photos || []).length;
    add("photos", "danger", `Need ${need} more photo${need !== 1 ? "s" : ""}`,
      `Daily Reports need at least ${photoMin} photos showing the day's work.`,
      "Open the Photos section and capture the missing shots.");
  }
  if (photoMissing.length > 0) {
    // One requirement chip per missing category — tells the foreman WHAT,
    // not just HOW MANY, photos are needed.
    photoMissing.slice(0, 6).forEach((cat) => {
      add(`photo_${cat.key}`, "warn", `Photo missing · ${cat.label}`,
        "The platform expects this category for a complete Daily Report.",
        `Add a photo and tag it '${cat.label}'.`);
    });
  }

  // Signature
  if (!d.prepared_by_signature) {
    add("signature", "danger", "Signature missing",
      "Foremen sign off on the day's data so HR and PM trust the record.",
      "Sign at the bottom of the form.");
  }

  // Status
  const hasDanger = requirements.some((r) => r.severity === "danger");
  const hasWarn = requirements.some((r) => r.severity === "warn");
  let status = "Ready to Submit";
  let statusReason = "Every required item is in. Sign and submit.";
  if (hasDanger) {
    status = "Action Required";
    statusReason = "One or more required items need attention before this report can be submitted.";
  } else if (hasWarn) {
    status = "Needs Review";
    statusReason = "You can submit — Safety/PM may follow up on the items below.";
  }

  // Phase 10D.2 · Section completion chips
  const sections = [
    { key: "job",       label: "Job Ready",        ok: !!String(d.project_name || "").trim() },
    { key: "people",    label: "People Ready",     ok: !!String(d.prepared_by || "").trim() },
    { key: "crew",      label: "Crew Ready",       ok: (d.masci_crews || []).length > 0 || (d.subcontractors || []).length > 0 },
    { key: "work",      label: "Work Ready",       ok: !!String(d.work_performed || d.activity_summary || "").trim() },
    { key: "photos",    label: photoMissing.length > 0 ? `Photos · ${photoMissing.length} missing category${photoMissing.length !== 1 ? "ies" : ""}` : "Photos Ready",
                         ok: (d.photos || []).length >= photoMin && photoMissing.length === 0 },
    { key: "excavation", label: exc === "yes" ? ((d.linked_excavation_ids || []).length > 0 ? "Excavation Linked" : "Excavation NOT Linked") : "No Excavation Today",
                          ok: exc !== "yes" || (d.linked_excavation_ids || []).length > 0 },
    { key: "incident", label: hasIncident ? (d.safety_notified === "Yes" && d.incident_report_filled === "Yes" ? "Incident Linked" : "Incident Pending") : "No Incident Today",
                        ok: !hasIncident || (d.safety_notified === "Yes" && d.incident_report_filled === "Yes") },
    { key: "signature", label: "Signature Ready",  ok: !!d.prepared_by_signature },
  ];

  return {
    status,
    statusReason,
    requirements,
    sections,
    photoCategories,
    counts: {
      danger: requirements.filter((r) => r.severity === "danger").length,
      warn:   requirements.filter((r) => r.severity === "warn").length,
      info:   requirements.filter((r) => r.severity === "info").length,
    },
  };
}
