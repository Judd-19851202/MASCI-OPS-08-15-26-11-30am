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
});