/* eslint-env jest */
/* global describe, beforeEach, test, expect */

import {
  applyMultiLoginResponse,
  clearDirectorySession,
  getDirectoryToken,
  getDirectoryUser,
} from "@/lib/directoryAuth";

describe("directoryAuth remember-me behavior", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  test("stores directory session in sessionStorage when rememberMe is false", () => {
    applyMultiLoginResponse(
      {
        ok: true,
        session_token: "dir-session-token",
        user: { id: "u-1", portals: ["admin"] },
        portal_tokens: { admin: "admin-token" },
      },
      false,
    );

    expect(window.sessionStorage.getItem("masci.directory.token")).toBe("dir-session-token");
    expect(window.localStorage.getItem("masci.directory.token")).toBeNull();
    expect(getDirectoryToken()).toBe("dir-session-token");
    expect(getDirectoryUser()?.id).toBe("u-1");
  });

  test("clearDirectorySession wipes both storage tiers", () => {
    window.localStorage.setItem("masci.directory.token", "persisted");
    window.sessionStorage.setItem("masci.directory.token", "ephemeral");
    clearDirectorySession();
    expect(getDirectoryToken()).toBe("");
  });
});