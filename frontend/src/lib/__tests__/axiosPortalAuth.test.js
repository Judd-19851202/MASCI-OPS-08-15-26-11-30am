/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach, afterEach */

import axios from "axios";
import { installPortalAxiosAuth } from "@/lib/axiosPortalAuth";

jest.mock("@/lib/authHeaders", () => ({
  buildPortalAuthHeaders: () => ({
    "X-Admin-Token": "admin-token",
    "X-Directory-Token": "directory-token",
  }),
}));

describe("installPortalAxiosAuth", () => {
  const originalCreate = axios.create;
  const originalFlag = axios.__masciPortalAxiosPatched;
  const originalEnv = process.env.REACT_APP_BACKEND_URL;

  beforeEach(() => {
    process.env.REACT_APP_BACKEND_URL = "https://mascidocs.com";
    delete axios.__masciPortalAxiosPatched;
  });

  afterEach(() => {
    axios.create = originalCreate;
    axios.__masciPortalAxiosPatched = originalFlag;
    process.env.REACT_APP_BACKEND_URL = originalEnv;
  });

  test("injects directory-bound auth into created axios clients for /api routes", async () => {
    installPortalAxiosAuth();
    const client = axios.create({ baseURL: "https://mascidocs.com/api" });
    const handler = client.interceptors.request.handlers[0].fulfilled;
    const config = await handler({ url: "/api/hr/employee-requests", baseURL: "https://mascidocs.com", headers: {} });

    expect(config.headers["X-Admin-Token"]).toBe("admin-token");
    expect(config.headers["X-Directory-Token"]).toBe("directory-token");
  });
});