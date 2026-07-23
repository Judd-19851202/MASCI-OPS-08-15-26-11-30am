/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */

import { validateStoredTokens } from "@/lib/tokenValidation";

jest.mock("@/lib/adminAuth", () => ({
  getAdminToken: () => "admin-token",
  clearAdminToken: jest.fn(),
}));
jest.mock("@/lib/pmAuth", () => ({ getPmToken: () => "", clearPmToken: jest.fn() }));
jest.mock("@/lib/shopAuth", () => ({ getShopToken: () => "", clearShopToken: jest.fn() }));
jest.mock("@/lib/devAuth", () => ({ getDevToken: () => "", clearDevToken: jest.fn() }));
jest.mock("@/lib/hrAuth", () => ({ getHrToken: () => "", clearHrToken: jest.fn() }));
jest.mock("@/lib/safetyAuth", () => ({ getSafetyToken: () => "", clearSafetyToken: jest.fn() }));
jest.mock("@/lib/dispatchAuth", () => ({ getDispatchToken: () => "", clearDispatchToken: jest.fn() }));
jest.mock("@/lib/directoryAuth", () => ({
  getDirectoryToken: () => "directory-token",
  clearDirectorySession: jest.fn(),
}));

describe("tokenValidation directory headers", () => {
  beforeEach(() => {
    global.fetch = jest.fn(async (_url, opts) => ({
      status: 200,
      ok: true,
      headers: { get: () => null },
      json: async () => ({}),
      text: async () => "",
      request: { headers: opts?.headers || {} },
    }));
  });

  test("includes X-Directory-Token when validating admin access", async () => {
    await validateStoredTokens();

    expect(global.fetch).toHaveBeenCalled();
    const adminCall = global.fetch.mock.calls.find(([url]) => String(url).includes("/api/admin/check"));
    expect(adminCall).toBeTruthy();
    expect(adminCall[1].headers["X-Admin-Token"]).toBe("admin-token");
    expect(adminCall[1].headers["X-Directory-Token"]).toBe("directory-token");
  });
});