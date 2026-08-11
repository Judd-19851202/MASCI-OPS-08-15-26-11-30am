/* eslint-env jest */

/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */

jest.mock("../deviceId", () => ({ getDeviceId: () => "device-123" }));
jest.mock("../actorId", () => ({
  getActorId: () => "actor-123",
  getStableActorIdentity: () => "stable-actor-123",
}));
jest.mock("@/lib/adminAuth", () => ({ getAdminToken: () => "" }), { virtual: true });
jest.mock("@/lib/pmAuth", () => ({ getPmToken: () => "" }), { virtual: true });
jest.mock("@/lib/hrAuth", () => ({ getHrToken: () => "" }), { virtual: true });
jest.mock("@/lib/safetyAuth", () => ({ getSafetyToken: () => "" }), { virtual: true });
jest.mock("@/lib/dispatchAuth", () => ({ getDispatchToken: () => "" }), { virtual: true });
jest.mock("@/lib/leadershipAuth", () => ({ getLeadershipToken: () => "" }), { virtual: true });
jest.mock("@/lib/shopAuth", () => ({ getShopToken: () => "" }), { virtual: true });
jest.mock("@/lib/flAuth", () => ({ getFlToken: () => "" }), { virtual: true });

import {
  DRAFT_TELEMETRY_FORM_KEY_MAX,
  _drainBufferForTests,
  emitDraftEvent,
  flushDraftTelemetryBeacon,
  sanitizeDraftTelemetryFormKey,
} from "../draftTelemetry";

beforeEach(() => {
  _drainBufferForTests();
  global.fetch = jest.fn(() => Promise.resolve({ ok: true }));
  Object.defineProperty(window, "navigator", {
    value: { sendBeacon: jest.fn() },
    configurable: true,
  });
});

describe("draft telemetry contract", () => {
  test("sanitizes overlong scoped form keys deterministically", () => {
    const raw = `daily-report::PROJECT-LONG-NUMBER-12345678901234567890::2026-07-08::primary::${"extra-segment::".repeat(16)}suffix`;
    const out = sanitizeDraftTelemetryFormKey(raw);
    expect(out.length).toBeLessThanOrEqual(DRAFT_TELEMETRY_FORM_KEY_MAX);
    expect(out.startsWith("daily-report::PROJECT-LONG")).toBe(true);
    expect(out).toContain("…");
  });

  test("emitDraftEvent hoists and sanitizes formKey", () => {
    const raw = `daily-report::PROJECT-LONG-NUMBER-12345678901234567890::2026-07-08::primary::${"extra-segment::".repeat(16)}suffix`;
    emitDraftEvent("draft.write.ok", { formKey: raw, trigger: "debounce" });
    const [event] = _drainBufferForTests();
    expect(event.formKey.length).toBeLessThanOrEqual(DRAFT_TELEMETRY_FORM_KEY_MAX);
    expect(event.meta.formKey).toBeUndefined();
    expect(event.meta.trigger).toBe("debounce");
  });

  test("pagehide beacon still flushes anonymous telemetry", () => {
    emitDraftEvent("draft.write.ok", { formKey: "daily-report::26-07::2026-07-08::primary" });
    flushDraftTelemetryBeacon();
    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [, options] = global.fetch.mock.calls[0];
    expect(options.keepalive).toBe(true);
  });
});