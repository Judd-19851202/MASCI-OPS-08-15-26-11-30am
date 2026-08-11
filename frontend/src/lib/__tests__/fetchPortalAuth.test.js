/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach, afterEach */

import { installPortalFetchAuth } from "@/lib/fetchPortalAuth";

jest.mock("@/lib/authHeaders", () => ({
  buildScopedPortalAuthHeaders: () => ({
    "X-HR-Token": "hr-token",
    "X-Directory-Token": "directory-token",
  }),
}));

describe("installPortalFetchAuth", () => {
  const originalFetch = global.fetch;
  const originalFlag = global.window.__masciPortalFetchAuthInstalled;
  const originalEnv = process.env.REACT_APP_BACKEND_URL;
  let nativeFetchMock;

  beforeEach(() => {
    process.env.REACT_APP_BACKEND_URL = "https://mascidocs.com";
    delete global.window.__masciPortalFetchAuthInstalled;
    nativeFetchMock = jest.fn(async (_input, init) => ({ ok: true, init }));
    global.fetch = nativeFetchMock;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    global.window.__masciPortalFetchAuthInstalled = originalFlag;
    process.env.REACT_APP_BACKEND_URL = originalEnv;
  });

  test("injects scoped portal + directory auth headers into bare /api fetch calls", async () => {
    installPortalFetchAuth();

    await window.fetch("/api/hr/employees?limit=1");

    expect(nativeFetchMock).toHaveBeenCalledTimes(1);
    const [, init] = nativeFetchMock.mock.calls[0];
    const headers = new Headers(init.headers);
    expect(headers.get("X-HR-Token")).toBe("hr-token");
    expect(headers.get("X-Directory-Token")).toBe("directory-token");
  });
});