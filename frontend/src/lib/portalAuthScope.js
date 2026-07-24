import { getPortalContext } from "@/lib/portalContext";

const PATH_PORTAL_PREFIXES = [
  ["/admin", "admin"],
  ["/hr", "hr"],
  ["/safety", "safety"],
  ["/pm", "pm"],
  ["/shop", "shop"],
  ["/dispatch", "dispatch"],
  ["/field-leadership", "fl"],
  ["/leadership", "leadership"],
  ["/dev", "dev"],
];

const CONTEXT_PORTAL_MAP = {
  admin: "admin",
  hr: "hr",
  safety: "safety",
  pm: "pm",
  shop: "shop",
  dispatch: "dispatch",
  "field-leadership": "fl",
  leadership: "leadership",
  public: null,
  unknown: null,
};

const SHARED_API_PREFIXES = [
  "/notifications/",
  "/tasks/",
  "/workflows/",
  "/operations-actions",
  "/operations-map/",
  "/operations/",
  "/operations-center",
  "/employees",
  "/daily-reports",
  "/incidents",
  "/project-health",
  "/asset-transfers",
  "/odr",
  "/operational-records",
  "/operational-intelligence/",
  "/jobs-master",
];

function normalizePath(pathname = "") {
  if (!pathname) return "";
  return pathname.startsWith("/") ? pathname : `/${pathname}`;
}

export function inferActivePortalForAuth(pathname = "") {
  const path = normalizePath(pathname);
  for (const [prefix, portal] of PATH_PORTAL_PREFIXES) {
    if (path === prefix || path.startsWith(`${prefix}/`)) return portal;
  }

  if (path === "/project-health" || path.startsWith("/project-health/")) return "pm";
  if (path === "/asset-transfers" || path.startsWith("/asset-transfers/")) return "pm";
  if (path === "/operational-records" || path.startsWith("/operational-records/")) return "fl";
  if (path === "/odr" || path.startsWith("/odr/")) return "fl";
  if (path === "/operations-actions" || path.startsWith("/operations-actions/")) return "admin";

  try {
    const contextPortal = CONTEXT_PORTAL_MAP[getPortalContext()];
    if (contextPortal) return contextPortal;
  } catch {
    // ignore context failures
  }

  return null;
}

export function inferPortalsForApiPath(pathname = "", activePortal = null) {
  const path = normalizePath(pathname);
  if (!path) return [];
  if (path.startsWith("/api/admin/") || path === "/api/admin") return ["admin"];
  if (path.startsWith("/api/hr/") || path === "/api/hr") return ["hr"];
  if (path.startsWith("/api/safety/") || path === "/api/safety") return ["safety"];
  if (path.startsWith("/api/pm/") || path === "/api/pm") return ["pm"];
  if (path.startsWith("/api/shop/") || path === "/api/shop") return ["shop"];
  if (path.startsWith("/api/dispatch/") || path === "/api/dispatch") return ["dispatch"];
  if (path.startsWith("/api/field-leadership/") || path === "/api/field-leadership") return ["fl"];
  if (path.startsWith("/api/leadership/") || path === "/api/leadership") return ["leadership"];
  if (path.startsWith("/api/auth/me-directory")) return ["directory"];
  if (path.startsWith("/api/auth/issue-portal-token")) return ["directory"];
  if (path.startsWith("/api/auth/")) return [];
  if (activePortal && SHARED_API_PREFIXES.some((prefix) => path === `/api${prefix}` || path.startsWith(`/api${prefix}`))) {
    return [activePortal];
  }
  return [];
}
