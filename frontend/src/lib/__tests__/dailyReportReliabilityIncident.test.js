/* eslint-env jest */
/* global describe, test, expect, beforeEach, jest */

import { fetchHrRoster } from "../hrRoster";
import {
  publishSessionStatus,
  getSessionStatus,
  clearSessionStatus,
  _testReset,
} from "../sessionStatusBus";

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
  },
}), { virtual: true });

jest.mock("@/lib/authHeaders", () => ({
  hasAnyPortalAuthToken: jest.fn(() => false),
}), { virtual: true });

const { api } = jest.requireMock("@/lib/api");
const { hasAnyPortalAuthToken } = jest.requireMock("@/lib/authHeaders");

beforeEach(() => {
  _testReset();
  api.get.mockReset();
  hasAnyPortalAuthToken.mockReset();
  hasAnyPortalAuthToken.mockReturnValue(false);
});

describe("Daily Report reliability incident regressions", () => {
  test("public Daily Report roster loads the public endpoint directly without auth churn", async () => {
    api.get.mockResolvedValueOnce({
        data: {
          items: [{ id: "emp-1", name: "Field User", employee_id: "1001", trade: "Operator" }],
        },
      });

    const items = await fetchHrRoster({ publicFallback: true });

    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenNthCalledWith(1, "/hr/employee-roster/public", {
      params: {},
      timeout: 30000,
      skipSessionStatus: true,
    });
    expect(items).toHaveLength(1);
    expect(items[0].name).toBe("Field User");
  });

  test("anonymous employee lookups auto-use the public roster endpoint", async () => {
    api.get.mockResolvedValueOnce({
      data: {
        items: [{ id: "emp-2", name: "Anonymous Crew", employee_id: "2002", trade: "Laborer" }],
      },
    });

    const items = await fetchHrRoster();

    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenNthCalledWith(1, "/hr/employee-roster/public", {
      params: {},
      timeout: 30000,
      skipSessionStatus: true,
    });
    expect(items[0].name).toBe("Anonymous Crew");
  });

  test("401 without public fallback returns last known snapshot instead of escalating form state", async () => {
    hasAnyPortalAuthToken.mockReturnValue(true);
    api.get.mockResolvedValueOnce({
      data: {
        items: [{ id: "emp-1", name: "Cached User", employee_id: "1001" }],
      },
    });
    const first = await fetchHrRoster();
    expect(first[0].name).toBe("Cached User");

    api.get.mockRejectedValueOnce({ response: { status: 401 } });
    const second = await fetchHrRoster();
    expect(second[0].name).toBe("Cached User");
  });

  test("session status bus preserves retry metadata", () => {
    const retry = jest.fn();
    publishSessionStatus({
      kind: "backend_unavailable",
      status: 503,
      meta: { endpoint: "/daily-reports", method: "POST", retry },
    });
    const state = getSessionStatus();
    expect(state.kind).toBe("backend_unavailable");
    expect(state.meta.endpoint).toBe("/daily-reports");
    expect(state.meta.method).toBe("POST");
    expect(state.meta.retry).toBe(retry);
  });

  test("clearing session status also clears retry metadata", () => {
    publishSessionStatus({
      kind: "network_unreachable",
      status: null,
      meta: { endpoint: "/daily-reports", method: "POST", retry: jest.fn() },
    });
    clearSessionStatus();
    const state = getSessionStatus();
    expect(state.kind).toBeNull();
    expect(state.meta).toBeNull();
  });
});