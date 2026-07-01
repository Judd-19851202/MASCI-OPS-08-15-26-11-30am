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
  resetSessionAck,
  getSessionAckState,
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

  // TRACK 19.11 AMENDMENT — sticky ack-suppression on auth kinds.
  describe("session-expired loop fix (Track 19.11 amendment)", () => {
    test("after user dismiss, further session_expired publishes are suppressed", () => {
      const cb = jest.fn();
      subscribeSessionStatus(cb);
      cb.mockClear();
      // Initial 401 → modal opens.
      publishSessionStatus({ kind: "session_expired", status: 401 });
      expect(getSessionStatus().kind).toBe("session_expired");
      // User taps "Stay Here" → bus clears + marks ack-suppressed.
      clearSessionStatus();
      expect(getSessionStatus().kind).toBeNull();
      expect(getSessionAckState().suppressed).toEqual(["session_expired"]);
      cb.mockClear();
      // 800 ms passes, another background 401 fires — the modal must
      // NOT re-open until the session recovers.
      const later = Date.now() + 5000;
      const origNow = Date.now;
      global.Date.now = () => later;
      try {
        publishSessionStatus({ kind: "session_expired", status: 401 });
        publishSessionStatus({ kind: "session_expired", status: 401 });
        publishSessionStatus({ kind: "session_expired", status: 401 });
      } finally {
        global.Date.now = origNow;
      }
      expect(getSessionStatus().kind).toBeNull();
      expect(cb).not.toHaveBeenCalled();
    });

    test("access_restricted dismissal is also ack-suppressed", () => {
      publishSessionStatus({ kind: "access_restricted", status: 403 });
      clearSessionStatus();
      expect(getSessionAckState().suppressed).toContain("access_restricted");
      const cb = jest.fn();
      subscribeSessionStatus(cb);
      cb.mockClear();
      const later = Date.now() + 10000;
      const origNow = Date.now;
      global.Date.now = () => later;
      try {
        publishSessionStatus({ kind: "access_restricted", status: 403 });
      } finally {
        global.Date.now = origNow;
      }
      expect(getSessionStatus().kind).toBeNull();
      expect(cb).not.toHaveBeenCalled();
    });

    test("success_loaded lifts ack-suppression so genuinely-new expiry can re-fire", () => {
      publishSessionStatus({ kind: "session_expired", status: 401 });
      clearSessionStatus();
      expect(getSessionAckState().suppressed).toContain("session_expired");
      // Session recovers (user logged back in, backend responds 2xx).
      publishSessionStatus({ kind: "success_loaded", status: 200 });
      expect(getSessionAckState().suppressed).toEqual([]);
      // A NEW expiry event later can raise the modal again.
      const later = Date.now() + 60000;
      const origNow = Date.now;
      global.Date.now = () => later;
      try {
        publishSessionStatus({ kind: "session_expired", status: 401 });
      } finally {
        global.Date.now = origNow;
      }
      expect(getSessionStatus().kind).toBe("session_expired");
    });

    test("resetSessionAck lifts suppression without touching overlay state", () => {
      publishSessionStatus({ kind: "session_expired", status: 401 });
      clearSessionStatus();
      expect(getSessionAckState().suppressed).toContain("session_expired");
      resetSessionAck();
      expect(getSessionAckState().suppressed).toEqual([]);
      expect(getSessionStatus().kind).toBeNull();
    });

    test("dismissing NETWORK_UNREACHABLE does NOT ack-suppress (retryable UX)", () => {
      publishSessionStatus({ kind: "network_unreachable", status: null });
      clearSessionStatus();
      expect(getSessionAckState().suppressed).toEqual([]);
      // Next unreachable event outside the debounce window should re-open.
      const later = Date.now() + 5000;
      const origNow = Date.now;
      global.Date.now = () => later;
      try {
        publishSessionStatus({ kind: "network_unreachable", status: null });
      } finally {
        global.Date.now = origNow;
      }
      expect(getSessionStatus().kind).toBe("network_unreachable");
    });

    test("dismissing BACKEND_UNAVAILABLE does NOT ack-suppress (retryable UX)", () => {
      publishSessionStatus({ kind: "backend_unavailable", status: 503 });
      clearSessionStatus();
      expect(getSessionAckState().suppressed).toEqual([]);
    });

    test("clearSessionStatus on empty state is a no-op", () => {
      const cb = jest.fn();
      subscribeSessionStatus(cb);
      cb.mockClear();
      clearSessionStatus();
      expect(cb).not.toHaveBeenCalled();
      expect(getSessionAckState().suppressed).toEqual([]);
    });
  });
});
