// MASCI Daily Job Report — schema + defaults
//
// Captures everything that happened on the job today: crews, subs,
// visitors, equipment, materials, activities, weather, photos, signatures.
// Designed to replace the Fieldwire Daily Report.

import { todayLocalIso } from "@/lib/dateUtils";

export function buildDailyReportDefaults() {
  return {
    // Report header
    project_name: "",
    project_number: "",
    location: "",
    report_date: todayLocalIso(),
    report_number: "", // optional, auto-incremented externally
    prepared_by: "",
    superintendent: "",
    // TRACK 24.9 Phase C · Project metadata snapshot.
    //
    // These are populated at project-select time (from
    // /api/jobs) so the field crew can see WHICH project their
    // report is bound to. They are NOT authoritative — the
    // server derives PM/co-PM routing from jobs_master keyed on
    // `project_number` at email/PDF time — but capturing them
    // in the payload gives every downstream consumer (PDF,
    // trust spine, ODS facts) a truthful project snapshot even
    // if the jobs_master row is edited between DR submission
    // and PDF render. Empty string when the source row lacks
    // the field (honest fallback, never fabricated).
    client: "",
    project_manager: "",
    pm_email: "",
    co_pm_emails: [],

    // GPS + auto weather
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
    weather_summary: "", // e.g. "Sunny, high 82°F"
    weather_snapshots: [
      // [{time:"06:00", condition, temp_f, precip_in, humidity_pct, wind_mph}, ...]
    ],
    weather_snapshot_meta: null,

    // General info / flags
    schedule_delays: "No",
    schedule_delays_notes: "",
    weather_impact: "No",
    weather_impact_notes: "",
    safety_incidents_today: "No", // any accidents
    injuries_reported: "No",
    incident_notes: "",
    // Safety-escalation gate: required when accident=Yes OR injury=Yes
    safety_notified: "", // "Yes" | "No"
    safety_contact_person: "",
    safety_contact_time: "",
    incident_report_filled: "", // "Yes" | "No"
    incident_report_time: "",
    general_notes: "",

    // Phase 10A-B · Excavation Activity Today (OMEGA Correction 1)
    // When YES, the Daily Report cannot be submitted until at least one
    // excavation record is created or linked. Backend enforces (422).
    excavation_activity_today: "No",
    linked_excavation_ids: [],

    // Distribution list — extra emails to CC on the PDF (PM/GC/DOT/insurance)
    distribution_list: [],

    // MASCI crews on site — flat list of crew members (one per row).
    // Each row: { name, trade, start_time, lunch_minutes, stop_time, hours,
    // work_performed }. Hours auto-calculate from start/lunch/stop.
    masci_crews: [],

    // Subcontractors on site
    subcontractors: [
      // [{company, trade, foreman, count, hours, work_performed}]
    ],

    // Site visitors
    visitors: [
      // [{name, company, time_in, time_out, purpose}]
    ],

    // Equipment log
    equipment: [
      // [{description, hours_used, time_delivered, time_removed, notes}]
    ],

    // Material deliveries
    materials: [
      // [{description, quantity, unit, supplier, ticket_number, notes}]
    ],

    // Activity / production log
    activities: [
      // [{activity, percent_complete, station_from, station_to, notes}]
    ],

    // Phase V.2 · Wave-1B — Structured Production Quantities (optional).
    // Closed-enum unit list enforced server-side
    // (LF / SY / CY / TON / EA / ACRE / OTHER). Empty by default —
    // foreman 9-step contract preserved (Doctrine Lock #1).
    // Per row: { description, quantity, unit, custom_unit_label,
    //            station_from, station_to, notes }
    production: [],

    // Phase V.2 · Wave-1B — Structured Constraint rows (optional).
    // Closed-enum constraint_type taxonomy enforced server-side.
    // Advisory flags (may_require_rfi · may_affect_schedule)
    // derived by backend — UI is signal-only. Empty by default.
    // Per row: { constraint_type, hours_impact, notes }
    constraints: [],

    // Photos — MIN 6
    photos: [],
    photo_min: 6,

    // Executive summary gate — must be frozen before submit.
    ai_accepted_summary: "",
    ai_accepted_summary_meta: null,

    // TRACK 19.04 · Unified document attachments (PDF, XLSX, XLS, CSV).
    // Each entry is the metadata envelope returned by
    // `POST /api/daily-reports/attachments/upload` — never raw bytes.
    attachments: [],

    // Sign-off
    prepared_by_signature: "",
    superintendent_signature: "",
  };
}
