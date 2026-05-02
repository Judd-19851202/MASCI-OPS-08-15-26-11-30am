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
  };
}
