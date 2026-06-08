// OA-1 · API client wrapper. Pure delegation to the global `api`
// axios instance which already attaches every portal token header.
import { api } from "@/lib/api";

const BASE = "/operations-actions";

export const oaApi = {
  list: (params = {}) => api.get(BASE, { params }),
  summary: () => api.get(`${BASE}/summary`),
  ownerSearch: (q, limit = 20) =>
    api.get(`${BASE}/owner-search`, { params: { q, limit } }),
  create: (body) => api.post(BASE, body),
  read: (id) => api.get(`${BASE}/${id}`),
  patch: (id, body) => api.patch(`${BASE}/${id}`, body),
  assign: (id, owner) => api.post(`${BASE}/${id}/assign`, { owner }),
  changeStatus: (id, status, note) =>
    api.post(`${BASE}/${id}/status`, { status, note }),
  addNote: (id, body_en) => api.post(`${BASE}/${id}/notes`, { body_en }),
  photoUrl: (oaId, photoId) =>
    api.get(`${BASE}/${oaId}/photos/${photoId}/url`),
  deletePhoto: (oaId, photoId) =>
    api.delete(`${BASE}/${oaId}/photos/${photoId}`),
  uploadPhoto: (oaId, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post(`${BASE}/${oaId}/photos`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export const STATUSES = ["open", "assigned", "in_progress", "waiting", "completed", "closed"];
export const STATUS_LABEL = {
  open: "Open", assigned: "Assigned", in_progress: "In Progress",
  waiting: "Waiting", completed: "Completed", closed: "Closed",
};
export const STATUS_TONE = {
  open:        "bg-slate-100 text-slate-900 border-slate-300",
  assigned:    "bg-indigo-100 text-indigo-900 border-indigo-300",
  in_progress: "bg-sky-100 text-sky-900 border-sky-300",
  waiting:     "bg-amber-100 text-amber-900 border-amber-300",
  completed:   "bg-emerald-100 text-emerald-900 border-emerald-300",
  closed:      "bg-slate-200 text-slate-700 border-slate-400",
};

export const CATEGORIES = [
  "truck_down", "utility_conflict", "missing_mot", "gps_issue",
  "plant_delay", "survey_required", "near_miss", "safety_concern",
  "material_shortage", "customer_request", "other",
];
export const CATEGORY_LABEL = {
  truck_down: "Truck Down",
  utility_conflict: "Utility Conflict",
  missing_mot: "Missing MOT",
  gps_issue: "GPS Equipment Issue",
  plant_delay: "Plant Delay",
  survey_required: "Survey Required",
  near_miss: "Near Miss",
  safety_concern: "Safety Concern",
  material_shortage: "Material Shortage",
  customer_request: "Customer Request",
  other: "Other",
};

export const PRIORITIES = ["low", "normal", "high", "critical"];
export const PRIORITY_LABEL = {
  low: "Low", normal: "Normal", high: "High", critical: "Critical",
};
export const PRIORITY_TONE = {
  low:      "bg-slate-50 text-slate-700 border-slate-200",
  normal:   "bg-slate-100 text-slate-800 border-slate-300",
  high:     "bg-amber-100 text-amber-900 border-amber-300",
  critical: "bg-rose-100 text-rose-900 border-rose-300",
};
