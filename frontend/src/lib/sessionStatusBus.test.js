/**
 * sessionStatusBus.test.js — TRUST-DIAGNOSTICS-001 bus contract.
 *
 * Run with: cd /app/frontend && CI=true yarn test --watchAll=false src/lib/sessionStatusBus.test.js
 */
/* eslint-env jest */
/* global describe, test, expect, beforeEach, jest */

import {
  publishSessionStatus,
  subscribeSessionStatus,
  getSessionStatus,
  clearSessionStatus,
  _testReset,
} from "./sessionStatusBus";

beforeEach(() => _testReset());

describe("sessionStatusBus", () => {
  test("publish session_expired updates state and notifies subscribers", () => {
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    cb.mockClear();
    publishSessionStatus({ kind: "session_expired", status: 401 });
    expect(getSessionStatus().kind).toBe("session_expired");
    expect(cb).toHaveBeenCalled();
  });

  test("kind:null is a no-op", () => {
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    cb.mockClear();
    publishSessionStatus({ kind: null, status: 404 });
    expect(getSessionStatus().kind).toBeNull();
    expect(cb).not.toHaveBeenCalled();
  });

  test("success_loaded clears any active state", () => {
    publishSessionStatus({ kind: "session_expired", status: 401 });
    expect(getSessionStatus().kind).toBe("session_expired");
    publishSessionStatus({ kind: "success_loaded", status: 200 });
    expect(getSessionStatus().kind).toBeNull();
  });

  test("success_empty does NOT change overlay state", () => {
    publishSessionStatus({ kind: "session_expired", status: 401 });
    publishSessionStatus({ kind: "success_empty", status: 200 });
    expect(getSessionStatus().kind).toBe("session_expired");
  });

  test("debounce: rapid identical events do not re-notify", () => {
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    cb.mockClear();
    publishSessionStatus({ kind: "session_expired", status: 401 });
    publishSessionStatus({ kind: "session_expired", status: 401 });
    publishSessionStatus({ kind: "session_expired", status: 401 });
    // first call notifies; next two are within DEBOUNCE_MS window
    expect(cb).toHaveBeenCalledTimes(1);
  });

  test("different kinds flow through even if rapid", () => {
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    cb.mockClear();
    publishSessionStatus({ kind: "session_expired", status: 401 });
    publishSessionStatus({ kind: "backend_unavailable", status: 503 });
    expect(cb).toHaveBeenCalledTimes(2);
    expect(getSessionStatus().kind).toBe("backend_unavailable");
  });

  test("clearSessionStatus resets state and notifies", () => {
    publishSessionStatus({ kind: "session_expired", status: 401 });
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    cb.mockClear();
    clearSessionStatus();
    expect(getSessionStatus().kind).toBeNull();
    expect(cb).toHaveBeenCalled();
  });

  test("subscribe replays current state immediately", () => {
    publishSessionStatus({ kind: "backend_unavailable", status: 502 });
    const cb = jest.fn();
    subscribeSessionStatus(cb);
    expect(cb).toHaveBeenCalledWith(
      expect.objectContaining({ kind: "backend_unavailable", status: 502 }),
    );
  });
});
