import { getPortalContext } from "@/lib/portalContext";

const PATH_PORTAL_PREFIXES = [
  ["/admin", "admin"],
  ["/hr", "hr"],
  ["/safety-portal", "safety"],
  ["/safety", "safety"],
  ["/pm", "pm"],
  ["/shop", "shop"],
  ["/transportation-operations", "dispatch"],
  ["/dispatch-portal", "dispatch"],
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
  "/notifications",
  "/notifications/",
  "/tasks",
  "/tasks/",
  "/workflows",
  "/workflows/",
  "/cost-codes",
  "/oppc",
  "/ods",
  "/operations-actions",
  "/operations-map/",
  "/operations/",
  "/operations-center",
  "/employees",
  "/daily-reports",
  "/inspections",
  "/meetings",
  "/equipment-inspections",
  "/qaqc-inspections",
  "/job-photos",
  "/incidents",
  "/safety-forms",
  "/trench-safety",
  "/project-health",
  "/asset-transfers",
  "/asset-spine",
  "/odr",
  "/operational-records",
  "/operational-intelligence/",
  "/jobs-master",
];

const ADMIN_SHARED_CROSS_PORTAL_PREFIXES = [
  "/safety/corrective-actions",
  "/safety/issuance",
  "/safety/training",
];

const ACTIVE_PORTAL_SHARED_API_PREFIXES = [
  "/project-staffing",
  "/job-hazard-files",
  "/legacy-imports",
];

const ADMIN_SHARED_API_PREFIXES = [
  "/equipment-status-board",
  "/ai/health",
  "/auto-email",
  "/jha-acknowledgements",
];

const HR_COMPAT_ADMIN_API_PREFIXES = [
  "/admin/field-leadership-users",
  "/admin/integrations/cleanup",
];

const DISPATCH_COMPAT_ADMIN_API_PREFIXES = [
  "/admin/transportation/intelligence/cleanup-signals",
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
  const routePath = (path.startsWith("/api/") ? path.slice(4) : path).split("?")[0].split("#")[0];

  if (routePath.startsWith("/admin/") || routePath === "/admin") {
    if (activePortal === "dispatch" && (routePath === "/admin/transportation" || routePath.startsWith("/admin/transportation/"))) {
      return ["dispatch"];
    }
    if (
      activePortal === "dispatch" &&
      DISPATCH_COMPAT_ADMIN_API_PREFIXES.some(
        (prefix) => routePath === prefix || routePath.startsWith(`${prefix}/`)
      )
    ) {
      return ["dispatch"];
    }
    if (
      activePortal === "hr" &&
      HR_COMPAT_ADMIN_API_PREFIXES.some(
        (prefix) => routePath === prefix || routePath.startsWith(`${prefix}/`)
      )
    ) {
      return ["hr", "admin"];
    }
    return ["admin"];
  }
  if (routePath.startsWith("/hr/") || routePath === "/hr") return ["hr"];
  if (routePath.startsWith("/safety/") || routePath === "/safety") return ["safety"];
  if (routePath.startsWith("/pm/") || routePath === "/pm") return ["pm"];
  if (routePath.startsWith("/shop/") || routePath === "/shop") return ["shop"];
  if (routePath.startsWith("/dispatch/") || routePath === "/dispatch") return ["dispatch"];
  if (routePath.startsWith("/field-leadership/") || routePath === "/field-leadership") {
    if (activePortal === "admin" || activePortal === "pm") return [activePortal];
    return ["fl"];
  }
  if (routePath.startsWith("/leadership/") || routePath === "/leadership") return ["leadership"];
  if (routePath.startsWith("/auth/me-directory")) return ["directory"];
  if (routePath.startsWith("/auth/issue-portal-token")) return ["directory"];
  if (routePath.startsWith("/auth/")) return [];

  if (
    activePortal === "admin" &&
    ADMIN_SHARED_CROSS_PORTAL_PREFIXES.some(
      (prefix) => routePath === prefix || routePath.startsWith(prefix)
    )
  ) {
    return ["admin"];
  }

  if (
    activePortal === "admin" &&
    ADMIN_SHARED_API_PREFIXES.some(
      (prefix) => routePath === prefix || routePath.startsWith(prefix)
    )
  ) {
    return ["admin"];
  }

  if (
    activePortal &&
    (SHARED_API_PREFIXES.some((prefix) => routePath === prefix || routePath.startsWith(prefix)) ||
      ACTIVE_PORTAL_SHARED_API_PREFIXES.some((prefix) => routePath === prefix || routePath.startsWith(prefix)))
  ) {
    return [activePortal];
  }
  return [];
}
