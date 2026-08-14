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
  // TD-0015 · Equipment Master canonical list. Uses the same
  // `_require_any_portal_read` (portal token + directory) gate as
  // `/employees`. It was MISSING from every scope list, so
  // `api.get("/equipment-master")` attached NO tokens -> 401 ->
  // EquipmentMasterPanel rendered a FALSE "0 units / Fleet is empty"
  // (observed on live production: API total 604 vs UI 0). Scoping it
  // here attaches the active portal token + directory token so the
  // canonical 604-unit fleet renders for every portal picker.
  "/equipment-master",
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
  "/bilingual-records",
  "/field-memory",
  "/field-memory/",
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
  "/email-report",
  "/integrations/maintainx/defect-coverage",
];

const ADMIN_SHARED_API_PREFIXES = [
  "/equipment-status-board",
  "/equipment-parts",
  "/ai/health",
  "/auto-email",
  "/jha-acknowledgements",
  "/draft-telemetry",
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

  // Canonical employee roster is a cross-platform lookup surface. The
  // backend accepts ANY valid portal token for `/api/hr/employee-roster`
  // so PM / Safety / Shop / Dispatch / FL forms can resolve employees
  // without borrowing the HR token slot. The public projection stays
  // anonymous by contract.
  if (routePath === "/hr/employee-roster/public" || routePath.startsWith("/hr/employee-roster/public/")) {
    return [];
  }
  if (routePath === "/hr/employee-roster" || routePath.startsWith("/hr/employee-roster/")) {
    return activePortal ? [activePortal] : ["hr"];
  }

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
