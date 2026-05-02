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

    // GPS + auto weather
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
    weather_summary: "", // e.g. "Sunny, high 82°F"
    weather_snapshots: [
      // [{time:"06:00", condition, temp_f, precip_in, humidity_pct, wind_mph}, ...]
    ],

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

    // Photos — MIN 6
    photos: [],
    photo_min: 6,

    // Sign-off
    prepared_by_signature: "",
    superintendent_signature: "",
  };
}
