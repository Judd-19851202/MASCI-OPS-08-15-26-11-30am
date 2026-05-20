// Field definitions for the MASCI Site Safety Meeting (Toolbox Talk) form.
import { todayLocalIso } from "@/lib/dateUtils";

export const TOPIC_CATEGORIES = [
  "Hazard-Specific",
  "Tool / Equipment Specific",
  "Procedure / SOP",
  "Incident Review",
  "Stretch & Flex",
  "Other",
];

// E1 · operational context chips/dropdowns for meeting setup.
// Keep these short — meant to be one-tap inputs at the top of Section 01.
export const SHIFT_OPTIONS = ["Day", "Swing", "Night"];

export const WEATHER_OPTIONS = [
  { key: "clear", en: "Clear", es: "Despejado" },
  { key: "hot", en: "Hot", es: "Calor" },
  { key: "cold", en: "Cold", es: "Frío" },
  { key: "rain", en: "Rain", es: "Lluvia" },
  { key: "wind", en: "Wind", es: "Viento" },
  { key: "storm_risk", en: "Storm Risk", es: "Riesgo Tormenta" },
];

export function buildMeetingDefaults() {
  return {
    project_name: "",
    project_number: "",
    location: "",
    meeting_date: todayLocalIso(),
    meeting_time: new Date().toTimeString().slice(0, 5),
    conducted_by: "",
    topic: "",
    topic_category: "Hazard-Specific",
    hazards_reviewed: "",
    discussion_notes: "",
    references_cited: "",
    action_items: "",
    attendees: [],
    photos: [],
    conductor_signature: "",
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
    // E1 · operational context captures
    crew_size: null,           // integer · optional · "how many were here, including no-shows"
    shift: "",                 // "" | "Day" | "Swing" | "Night"
    weather: [],               // array of WEATHER_OPTIONS keys
    subcontractor_present: false,
    subcontractor_name: "",
    high_risk_activity: false,
  };
}
