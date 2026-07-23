/* eslint-env jest */
/* global jest, describe, test, expect */

import { buildPortalAuthHeaders } from "@/lib/authHeaders";

jest.mock("@/lib/adminAuth", () => ({ getAdminToken: () => "admin-token" }));
jest.mock("@/lib/pmAuth", () => ({ getPmToken: () => "" }));
jest.mock("@/lib/hrAuth", () => ({ getHrToken: () => "hr-token" }));
jest.mock("@/lib/shopAuth", () => ({ getShopToken: () => "" }));
jest.mock("@/lib/safetyAuth", () => ({ getSafetyToken: () => "" }));
jest.mock("@/lib/dispatchAuth", () => ({ getDispatchToken: () => "" }));
jest.mock("@/lib/leadershipAuth", () => ({ getLeadershipToken: () => "" }));
jest.mock("@/lib/flAuth", () => ({ getFlToken: () => "" }));
jest.mock("@/lib/directoryAuth", () => ({ getDirectoryToken: () => "directory-token" }));

describe("buildPortalAuthHeaders", () => {
  test("forwards directory token alongside admin/hr tokens", () => {
    const headers = buildPortalAuthHeaders({ "Content-Type": "application/json" });

    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["X-Admin-Token"]).toBe("admin-token");
    expect(headers["X-HR-Token"]).toBe("hr-token");
    expect(headers["X-Directory-Token"]).toBe("directory-token");
  });
});