/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */

import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { inferPortalsForApiPath } from "@/lib/portalAuthScope";

describe("portal auth scoping", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("masci.directory.token", "directory-token");
    localStorage.setItem("masci.admin.token", "admin-token");
    localStorage.setItem("masci.pm.token", "pm-token");
    localStorage.setItem("masci.hr.token", "hr-token");
    localStorage.setItem("masci.safety.token", "safety-token");
    localStorage.setItem("masci.dispatch.token", "dispatch-token");
  });

  test("admin-scoped headers exclude unrelated portal tokens", () => {
    const headers = buildScopedPortalAuthHeaders(["admin"]);
    expect(headers["X-Admin-Token"]).toBe("admin-token");
    expect(headers["X-Directory-Token"]).toBe("directory-token");
    expect(headers["X-HR-Token"]).toBeUndefined();
    expect(headers["X-Safety-Token"]).toBeUndefined();
  });

  test("hr-scoped headers exclude admin token", () => {
    const headers = buildScopedPortalAuthHeaders(["hr"]);
    expect(headers["X-HR-Token"]).toBe("hr-token");
    expect(headers["X-Directory-Token"]).toBe("directory-token");
    expect(headers["X-Admin-Token"]).toBeUndefined();
  });

  test("pm job photos endpoints inherit pm auth in shared scope", () => {
    expect(inferPortalsForApiPath("/api/job-photos", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/job-photos?limit=8", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/job-photos/photo-1/raw", "pm")).toEqual(["pm"]);
  });

  test("unrelated photo endpoints are not broadened", () => {
    expect(inferPortalsForApiPath("/api/photos", "pm")).toEqual([]);
    expect(inferPortalsForApiPath("/api/photo-assets", "pm")).toEqual([]);
  });

  // TD-0026 regression: the Phase V-Prelude substrate routers all mount the
  // SAME _require_any_portal_token gate. They were missing from every scope
  // list -> no token attached -> 401 "Portal authentication required"
  // (observed live on BP-0025 constraint detail + BP-0026 constraints list).
  // The active portal token MUST attach; bare /photos stays unscoped.
  test("operational substrate routes inherit the active portal token", () => {
    expect(inferPortalsForApiPath("/api/constraints", "admin")).toEqual(["admin"]);
    expect(inferPortalsForApiPath("/api/constraints?status=open", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/constraints/abc-123", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/operational-links", "safety")).toEqual(["safety"]);
    expect(inferPortalsForApiPath("/api/timeline?project_id=42", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/photos/photo-1/governance", "admin")).toEqual(["admin"]);
    // bare /photos has no endpoint and must NOT be broadened
    expect(inferPortalsForApiPath("/api/photos", "pm")).toEqual([]);
  });

  test("dispatch cleanup endpoints keep dispatch auth even under /admin namespace", () => {
    expect(
      inferPortalsForApiPath(
        "/api/admin/transportation/intelligence/cleanup-signals?days=30",
        "dispatch",
      ),
    ).toEqual(["dispatch"]);

    const headers = buildScopedPortalAuthHeaders(
      inferPortalsForApiPath(
        "/api/admin/transportation/intelligence/cleanup-signals?days=30",
        "dispatch",
      ),
    );
    expect(headers["X-Dispatch-Token"]).toBe("dispatch-token");
    expect(headers["X-Directory-Token"]).toBe("directory-token");
    expect(headers["X-Admin-Token"]).toBeUndefined();
  });

  test("maintainx defect coverage inherits the active portal token", () => {
    expect(
      inferPortalsForApiPath(
        "/api/integrations/maintainx/defect-coverage?sample_limit=1&since_days=60",
        "dispatch",
      ),
    ).toEqual(["dispatch"]);

    const dispatchHeaders = buildScopedPortalAuthHeaders(
      inferPortalsForApiPath(
        "/api/integrations/maintainx/defect-coverage?sample_limit=1&since_days=60",
        "dispatch",
      ),
    );
    expect(dispatchHeaders["X-Dispatch-Token"]).toBe("dispatch-token");
    expect(dispatchHeaders["X-Admin-Token"]).toBeUndefined();
  });

  test("field memory recent inherits the active portal token", () => {
    expect(inferPortalsForApiPath("/api/field-memory/recent?limit=3", "dispatch")).toEqual(["dispatch"]);
  });

  test("employee roster inherits the active non-hr portal token", () => {
    expect(inferPortalsForApiPath("/api/hr/employee-roster", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/hr/employee-roster", "dispatch")).toEqual(["dispatch"]);
    expect(inferPortalsForApiPath("/api/hr/employee-roster/public", "pm")).toEqual([]);
  });

  // TD-0015 regression: equipment-master canonical list MUST attach the active
  // portal token (+ directory) or the panel 401s -> false "0 units / Fleet is
  // empty" (observed live: API 604 vs UI 0). The public lookup MUST stay unscoped.
  test("equipment-master canonical list inherits the active portal token", () => {
    expect(inferPortalsForApiPath("/api/equipment-master", "admin")).toEqual(["admin"]);
    expect(inferPortalsForApiPath("/api/equipment-master", "pm")).toEqual(["pm"]);
    expect(inferPortalsForApiPath("/api/equipment-master", "shop")).toEqual(["shop"]);
    expect(inferPortalsForApiPath("/api/public/equipment-master-lookup", "admin")).toEqual([]);
  });
});