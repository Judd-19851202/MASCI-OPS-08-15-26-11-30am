// Phase 10D · Daily Report compliance engine (pure function)
// Path A simplification — short labels only. No paragraph why/action.
// The card shows what's left in 1–3 words. That's it.

export function computeDailyReportCompliance(d, opts = {}) {
  const photoMin = opts.photoMin || d.photo_min || 6;
  const items = [];
  const add = (id, severity, label, jumpTo) =>
    items.push({ id, severity, label, jumpTo });

  // Job
  if (!String(d.project_name || "").trim())     add("project",      "danger", "Pick Job",        "exc-job-section");
  if (!String(d.prepared_by || "").trim())      add("prepared_by",  "danger", "Add Prepared By", "input-prepared-by");

  // Excavation gate (Phase 10A-B Correction 1)
  if (String(d.excavation_activity_today || "No").toLowerCase() === "yes" &&
      (d.linked_excavation_ids || []).length === 0) {
    add("excavation_link", "danger", "Link Excavation", "dr-excavation-activity");
  }

  // Incident gate
  const hasIncident = d.safety_incidents_today === "Yes" || d.injuries_reported === "Yes";
  if (hasIncident && d.incident_report_filled !== "Yes") {
    add("incident_report", "danger", "Add Incident Report", "dr-incident-trigger");
  }

  // Crew
  if ((d.masci_crews || []).length === 0 && (d.subcontractors || []).length === 0) {
    add("crew", "warn", "Add Crew", "dr-crew-section");
  }

  // Photos
  const need = photoMin - (d.photos || []).length;
  if (need > 0) add("photos", "danger", `Add ${need} Photo${need !== 1 ? "s" : ""}`, "dr-photos-section");

  // Signature
  if (!d.prepared_by_signature) add("signature", "danger", "Sign Report", "dr-signature-section");

  const hasDanger = items.some((r) => r.severity === "danger");
  const hasWarn = items.some((r) => r.severity === "warn");
  let status = "Ready to Submit";
  if (hasDanger) status = "Action Required";
  else if (hasWarn) status = "Needs Review";

  return {
    status,
    items,
    counts: {
      danger: items.filter((r) => r.severity === "danger").length,
      warn:   items.filter((r) => r.severity === "warn").length,
    },
  };
}
