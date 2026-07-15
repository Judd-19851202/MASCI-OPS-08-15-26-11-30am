function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function round2(value) {
  return Math.round((toNumber(value) + Number.EPSILON) * 100) / 100;
}

function computeCrewHours(row = {}) {
  const explicit = [row.hours, row.hours_worked, row.labor_hours].find((v) => v !== undefined && v !== null && v !== "");
  if (explicit !== undefined) return round2(explicit);

  const start = String(row.start_time || "");
  const stop = String(row.stop_time || "");
  if (!start || !stop) return 0;
  const startMatch = start.match(/^(\d{1,2}):(\d{2})$/);
  const stopMatch = stop.match(/^(\d{1,2}):(\d{2})$/);
  if (!startMatch || !stopMatch) return 0;
  let gross = (Number(stopMatch[1]) * 60 + Number(stopMatch[2])) - (Number(startMatch[1]) * 60 + Number(startMatch[2]));
  if (gross < 0) gross += 24 * 60;
  const lunch = Math.max(0, toNumber(row.lunch_minutes));
  return round2(Math.max(0, gross - lunch) / 60);
}

function normalizeCrewRow(row = {}) {
  return {
    employee_id: String(row.employee_id || "").trim(),
    name: String(row.name || row.employee_name_snapshot || "").trim(),
    trade: String(row.trade || row.trade_snapshot || row.trade_role_display || "").trim(),
    start_time: String(row.start_time || "").trim(),
    stop_time: String(row.stop_time || "").trim(),
    lunch_minutes: toNumber(row.lunch_minutes),
    hours: computeCrewHours(row),
    work_performed: String(row.work_performed || row.notes || "").trim(),
  };
}

function normalizeSubcontractorRow(row = {}) {
  return {
    company: String(row.company || row.vendor || row.name || "").trim(),
    trade: String(row.trade || row.scope || "").trim(),
    foreman: String(row.foreman || row.contact || "").trim(),
    count: Math.max(0, Math.trunc(toNumber(row.count || row.headcount))),
    hours: round2(row.hours),
    work_performed: String(row.work_performed || row.notes || "").trim(),
  };
}

function normalizeEquipmentRow(row = {}) {
  const runHours = round2(row.hours_used ?? row.run_time ?? row.run_hours);
  const idleHours = round2(row.idle_hours ?? row.idle_time ?? row.idle);
  return {
    equipment_id: String(row.equipment_id || row.id || "").trim(),
    description: String(row.description || row.equipment || row.label || "").trim(),
    unit_number: String(row.unit_number || row.unit || "").trim(),
    operator: String(row.operator || row.operator_name || "").trim(),
    run_hours: runHours,
    idle_hours: idleHours,
    total_usage_hours: round2(runHours + idleHours),
    notes: String(row.notes || "").trim(),
  };
}

function normalizeProductionRow(row = {}) {
  return {
    description: String(row.description || row.activity || row.name || "").trim(),
    quantity: round2(row.quantity),
    unit: String(row.unit || "").trim(),
    percent_complete: Math.max(0, Math.min(100, Math.trunc(toNumber(row.percent_complete)))),
    cost_code: String(row.cost_code || "").trim(),
    work_area: String(row.station_from || row.work_area || "").trim(),
    notes: String(row.notes || "").trim(),
  };
}

function normalizePhotoIntelStatus(photoIntel, photoCount) {
  if (photoIntel?.status) return String(photoIntel.status);
  if (photoCount > 0) return "not_requested";
  return "no_photos";
}

export function buildDailyReportSummaryPayload(data = {}, photoIntel = null, options = {}) {
  const crews = (data.masci_crews || []).map(normalizeCrewRow).filter((row) => row.name || row.trade || row.hours > 0);
  const subcontractors = (data.subcontractors || []).map(normalizeSubcontractorRow).filter((row) => row.company || row.trade || row.hours > 0 || row.count > 0);
  const equipment = (data.equipment || []).map(normalizeEquipmentRow).filter((row) => row.description || row.unit_number || row.total_usage_hours > 0);
  const production = (data.production || []).map(normalizeProductionRow).filter((row) => row.description || row.quantity > 0);
  const photos = Array.isArray(data.photos) ? data.photos : [];

  const summaryInput = {
    labor: {
      employee_count: crews.length,
      total_employee_hours: round2(crews.reduce((sum, row) => sum + row.hours, 0)),
      rows: crews,
    },
    subcontractors: {
      subcontractor_count: subcontractors.length,
      total_headcount: subcontractors.reduce((sum, row) => sum + row.count, 0),
      total_hours: round2(subcontractors.reduce((sum, row) => sum + row.hours, 0)),
      rows: subcontractors,
    },
    equipment: {
      equipment_count: equipment.length,
      total_run_hours: round2(equipment.reduce((sum, row) => sum + row.run_hours, 0)),
      total_idle_hours: round2(equipment.reduce((sum, row) => sum + row.idle_hours, 0)),
      total_usage_hours: round2(equipment.reduce((sum, row) => sum + row.total_usage_hours, 0)),
      rows: equipment,
    },
    production: {
      rows: production,
    },
    photos: {
      photo_count: photos.length,
      status: normalizePhotoIntelStatus(photoIntel, photos.length),
      lifecycle_status: String(photoIntel?.lifecycle_status || photoIntel?.status || normalizePhotoIntelStatus(photoIntel, photos.length)),
      analyzed: Number(photoIntel?.analyzed || 0),
      pending: Number(photoIntel?.pending || 0),
      queued: Number(photoIntel?.queued || 0),
      processing: Number(photoIntel?.processing || 0),
      failed: Number(photoIntel?.failed || 0),
      observations: Array.isArray(photoIntel?.observations) ? photoIntel.observations : [],
      classification: String(photoIntel?.classification || "").trim(),
    },
  };

  return {
    form_key: options.formKey || data.form_key || "",
    project_name: data.project_name || "",
    project_number: data.project_number || "",
    report_date: data.report_date || "",
    report_instance: data.report_instance || "primary",
    prepared_by: data.prepared_by || "",
    superintendent: data.superintendent || "",
    location: data.location || "",
    weather_summary: data.weather_summary || "",
    general_notes: data.general_notes || "",
    incident_notes: data.incident_notes || "",
    schedule_delays: data.schedule_delays || "",
    schedule_delays_notes: data.schedule_delays_notes || "",
    weather_impact: data.weather_impact || "",
    weather_impact_notes: data.weather_impact_notes || "",
    safety_incidents_today: data.safety_incidents_today || "No",
    injuries_reported: data.injuries_reported || "No",
    narrative_sections: data.narrative_sections || {},
    masci_crews: crews.map((row) => ({
      name: row.name,
      trade: row.trade,
      count: 1,
      hours: row.hours,
      work_performed: row.work_performed,
    })),
    subcontractors: subcontractors.map((row) => ({
      company: row.company,
      trade: row.trade,
      foreman: row.foreman,
      count: row.count,
      hours: row.hours,
      work_performed: row.work_performed,
    })),
    equipment: equipment.map((row) => ({
      description: row.description,
      unit_number: row.unit_number,
      operator: row.operator,
      hours_used: row.run_hours,
      idle_hours: row.idle_hours,
      run_time: row.run_hours,
      idle_time: row.idle_hours,
      notes: row.notes,
    })),
    production,
    photos,
    photo_observations: summaryInput.photos.observations,
    photo_intelligence_status: summaryInput.photos.status,
    summary_input: summaryInput,
  };
}

export function buildDeterministicSummaryFallback(data = {}, photoIntel = null) {
  const payload = buildDailyReportSummaryPayload(data, photoIntel);
  const summaryInput = payload.summary_input;
  const bits = [];

  if (summaryInput.labor.employee_count || summaryInput.labor.total_employee_hours) {
    bits.push(
      `MASCI crew: ${summaryInput.labor.employee_count} ${summaryInput.labor.employee_count === 1 ? "employee" : "employees"}, ${summaryInput.labor.total_employee_hours.toFixed(2)} labor hours.`
    );
  }
  if (summaryInput.subcontractors.subcontractor_count || summaryInput.subcontractors.total_hours) {
    bits.push(
      `Subcontractors/vendors: ${summaryInput.subcontractors.subcontractor_count} company rows, ${summaryInput.subcontractors.total_hours.toFixed(2)} hours.`
    );
  }
  if (summaryInput.equipment.equipment_count || summaryInput.equipment.total_usage_hours) {
    bits.push(
      `Equipment: ${summaryInput.equipment.equipment_count} ${summaryInput.equipment.equipment_count === 1 ? "unit" : "units"}, ${summaryInput.equipment.total_run_hours.toFixed(2)} run hours, ${summaryInput.equipment.total_idle_hours.toFixed(2)} idle hours.`
    );
  }
  if (summaryInput.production.rows.length > 0) {
    const row = summaryInput.production.rows[0];
    bits.push(
      `Production: ${row.quantity ? `${row.quantity} ${row.unit || ""} `.trimStart() : ""}${row.description || "Work activity"}${row.percent_complete ? ` (${row.percent_complete}% complete)` : ""}.`
    );
  }
  if (summaryInput.photos.photo_count > 0) {
    const photoLifecycle = summaryInput.photos.lifecycle_status || summaryInput.photos.status;
    bits.push(
      `${summaryInput.photos.photo_count} ${summaryInput.photos.photo_count === 1 ? "photo" : "photos"} attached${photoLifecycle ? ` · photo intelligence ${photoLifecycle.replaceAll("_", " ")}` : ""}.`
    );
    if (Array.isArray(summaryInput.photos.observations) && summaryInput.photos.observations.length > 0) {
      const snippets = summaryInput.photos.observations.slice(0, 2).flatMap((item) => {
        if (!item || typeof item !== "object") return [];
        const out = [];
        if (item.summary) out.push(String(item.summary).trim());
        if (Array.isArray(item.observations)) out.push(...item.observations.map((v) => String(v).trim()));
        if (item.description) out.push(String(item.description).trim());
        return out.filter(Boolean);
      }).slice(0, 3);
      if (snippets.length > 0) {
        bits.push(`Photo observations: ${snippets.join("; ")}.`);
      }
    }
  }
  return bits.join(" ") || "Daily activity recorded. Summary generated from the current report facts.";
}