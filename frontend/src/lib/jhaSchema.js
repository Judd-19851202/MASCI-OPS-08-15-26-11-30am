// Field definitions for the MASCI Job Hazard Analysis (JHA) form.
import { todayLocalIso } from "@/lib/dateUtils";

export const PPE_OPTIONS = [
  { key: "hard_hat", label: "Hard hat" },
  { key: "safety_glasses", label: "Safety glasses" },
  { key: "hi_vis", label: "Hi-visibility apparel" },
  { key: "gloves", label: "Gloves (task-appropriate)" },
  { key: "boots", label: "Steel/composite toe boots" },
  { key: "hearing", label: "Hearing protection" },
  { key: "respirator", label: "Respirator / dust mask" },
  { key: "harness", label: "Full-body harness" },
  { key: "face_shield", label: "Face shield" },
  { key: "cut_gloves", label: "Cut-resistant gloves" },
  { key: "fr_clothing", label: "FR clothing" },
];

export const PERMIT_OPTIONS = [
  { key: "hot_work", label: "Hot Work Permit" },
  { key: "confined_space", label: "Confined Space Entry" },
  { key: "excavation", label: "Excavation / Trench" },
  { key: "loto", label: "Lockout / Tagout" },
  { key: "elevated_work", label: "Elevated / Fall Work Plan" },
  { key: "crane_lift", label: "Crane Lift Plan" },
  { key: "energized", label: "Energized Electrical Work" },
];

export function buildJhaDefaults() {
  return {
    project_name: "",
    project_number: "",
    location: "",
    jha_date: todayLocalIso(),
    job_title: "",
    job_description: "",
    crew_lead: "",
    crew_members: "",
    ppe_required: {},
    permits_required: {},
    tools_equipment: "",
    task_steps: [
      { step: "", hazards: "", controls: "" },
    ],
    stop_work_acknowledged: "Yes",
    nearest_hospital: "",
    emergency_contact: "",
    crew_signoffs: [],
    foreman_signature: "",
    photos: [],
    gps_lat: null,
    gps_lng: null,
    gps_accuracy: null,
  };
}
