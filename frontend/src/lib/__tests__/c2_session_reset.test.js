import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";

const mockFn = () => jest.fn();

jest.mock("../adminAuth", () => ({ clearAdminToken: () => {} }));
jest.mock("../pmAuth", () => ({ clearPmToken: () => {} }));
jest.mock("../shopAuth", () => ({ clearShopToken: () => {} }));
jest.mock("../hrAuth", () => ({ clearHrToken: () => {} }));
jest.mock("../safetyAuth", () => ({ clearSafetyToken: () => {} }));
jest.mock("../dispatchAuth", () => ({ clearDispatchToken: () => {} }));
jest.mock("../devAuth", () => ({ clearDevToken: () => {} }));
jest.mock("../flAuth", () => ({ clearFlToken: () => {} }));
jest.mock("../leadershipAuth", () => ({ clearLeadershipToken: () => {} }));
jest.mock("../safetyFormsAuth", () => ({ clearSafetyFormsToken: () => {} }));
jest.mock("../jwtAuth", () => ({ clearJwt: () => {} }));
jest.mock("../driverAuth", () => ({ clearDriverSession: () => {} }));
jest.mock("../directoryAuth", () => ({
  clearDirectorySession: () => {},
  getDirectoryToken: () => "dir-token",
}));

import { clearAllSessions } from "../sessionReset";

describe("C2 shared sign-out contract", () => {
  beforeEach(() => {
    localStorage.setItem("masci.directory.token", "dir-token");
    global.fetch = jest.fn(() => Promise.resolve({ ok: true }));
  });

  afterEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    jest.clearAllMocks();
  });

  it("sign-out clears authenticated state and calls multi-logout", async () => {
    await clearAllSessions();
    expect(localStorage.getItem("masci.directory.token")).toBeNull();
    expect(global.fetch).toHaveBeenCalled();
  });
});