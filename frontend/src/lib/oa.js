import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { getPortalContext } from "@/lib/portalContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const BASE = "/operations-actions";
const OA_SCOPE_KEY = "masci.oa.portal-scope";

const OA_PORTAL_HEADER_MAP = {
  admin: "X-Admin-Token",
  pm: "X-PM-Token",
  hr: "X-HR-Token",
  safety: "X-Safety-Token",
  shop: "X-Shop-Token",
  dispatch: "X-Dispatch-Token",
  fl: "X-FL-Token",
};

const OA_FALLBACK_ORDER = ["admin", "pm", "dispatch", "safety", "shop", "hr", "fl"];

function normalizePortalScope(value) {
  const v = String(value || "").trim().toLowerCase();
  if (v === "field-leadership" || v === "field_leadership") return "fl";
  return OA_PORTAL_HEADER_MAP[v] ? v : "";
}

export function inferOperationsActionsPortalFromPath(pathname = "") {
  const path = String(pathname || "");
  if (path === "/admin" || path.startsWith("/admin/")) return "admin";
  if (path === "/pm" || path.startsWith("/pm/")) return "pm";
  if (path === "/hr" || path.startsWith("/hr/")) return "hr";
  if (path === "/safety" || path.startsWith("/safety/") || path === "/safety-portal" || path.startsWith("/safety-portal/")) return "safety";
  if (path === "/shop" || path.startsWith("/shop/")) return "shop";
  if (path === "/dispatch" || path.startsWith("/dispatch/") || path === "/dispatch-portal" || path.startsWith("/dispatch-portal/")) return "dispatch";
  if (path === "/field-leadership" || path.startsWith("/field-leadership/") || path === "/leadership" || path.startsWith("/leadership/")) return "fl";
  return "";
}

export function setOperationsActionsPortalScope(portal) {
  const normalized = normalizePortalScope(portal);
  if (!normalized) return;
  try {
    window.sessionStorage.setItem(OA_SCOPE_KEY, normalized);
  } catch {
    /* ignore */
  }
}

function getStoredOperationsActionsPortalScope() {
  try {
    return normalizePortalScope(window.sessionStorage.getItem(OA_SCOPE_KEY) || "");
  } catch {
    return "";
  }
}

function readPortalToken(portal) {
  const headers = buildScopedPortalAuthHeaders([portal]);
  return headers[OA_PORTAL_HEADER_MAP[portal]] || "";
}

function resolveOperationsActionsPortal() {
  const candidates = [];
  const storedPortal = getStoredOperationsActionsPortalScope();
  const pathPortal = inferOperationsActionsPortalFromPath(
    typeof window !== "undefined" ? window.location?.pathname || "" : ""
  );
  const contextPortal = normalizePortalScope(getPortalContext());
  if (storedPortal) candidates.push(storedPortal);
  if (contextPortal && !candidates.includes(contextPortal)) candidates.push(contextPortal);
  if (pathPortal && !candidates.includes(pathPortal)) candidates.push(pathPortal);

  for (const portal of candidates) {
    if (readPortalToken(portal)) return portal;
  }

  const available = OA_FALLBACK_ORDER.filter((portal) => !!readPortalToken(portal));
  if (available.length === 1) return available[0];
  if (available.includes("admin")) return "admin";
  return available[0] || "";
}

export function buildOperationsActionsAuthHeaders(extra = {}) {
  const portal = resolveOperationsActionsPortal();
  const headers = { ...extra };
  if (!portal) return headers;
  return buildScopedPortalAuthHeaders([portal], headers);
}

const oaClient = axios.create({
  baseURL: `${API}${BASE}`,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
  maxContentLength: 50 * 1024 * 1024,
  maxBodyLength: 50 * 1024 * 1024,
  timeout: 60000,
});

oaClient.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  Object.assign(config.headers, buildOperationsActionsAuthHeaders(config.headers));
  return config;
});

export const oaApi = {
  list: (params = {}) => oaClient.get("", { params }),
  summary: () => oaClient.get("/summary"),
  ownerSearch: (q, limit = 20) => oaClient.get("/owner-search", { params: { q, limit } }),
  create: (body) => oaClient.post("", body),
  read: (id) => oaClient.get(`/${id}`),
  patch: (id, body) => oaClient.patch(`/${id}`, body),
  assign: (id, owner) => oaClient.post(`/${id}/assign`, { owner }),
  changeStatus: (id, status, note) => oaClient.post(`/${id}/status`, { status, note }),
  addNote: (id, body_en) => oaClient.post(`/${id}/notes`, { body_en }),
  photoUrl: (oaId, photoId) => oaClient.get(`/${oaId}/photos/${photoId}/url`),
  deletePhoto: (oaId, photoId) => oaClient.delete(`/${oaId}/photos/${photoId}`),
  uploadPhoto: (oaId, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return oaClient.post(`/${oaId}/photos`, fd, {
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