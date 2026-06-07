// Phase 10D · Daily Report compliance engine (pure function).
//
// Same pattern as /lib/excavationCompliance.js. Reads the Daily Report
// form state and returns a live operational summary.
//
//   {
//     status: "Ready to Submit" | "Needs Review" | "Action Required",
//     statusReason: "…",
//     requirements: [ { id, severity, title, why, action } ],
//     counts: { danger, warn, info }
//   }
//
// Coaching language — no punitive vocabulary.

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

  // Excavation activity gate (Phase 10A-B Correction 1)
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

  // Photos
  const photoCount = (d.photos || []).length;
  if (photoCount < photoMin) {
    add("photos", "danger", `Need ${photoMin - photoCount} more photo${(photoMin - photoCount) !== 1 ? "s" : ""}`,
      `Daily Reports need at least ${photoMin} photos showing the day's work.`,
      "Open the Photos section and capture the missing shots.");
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

  return {
    status,
    statusReason,
    requirements,
    counts: {
      danger: requirements.filter((r) => r.severity === "danger").length,
      warn:   requirements.filter((r) => r.severity === "warn").length,
      info:   requirements.filter((r) => r.severity === "info").length,
    },
  };
}
