/* eslint-env jest */
/* global describe, beforeEach, it, expect */

import {
  getActivePublicDraftSession,
  ensureActivePublicDraftSession,
  clearActivePublicDraftSession,
  buildPublicDraftSessionScope,
  buildPublicDraftScopedFormKey,
  hasMeaningfulPublicDraft,
} from "../publicDraftScope";

describe("publicDraftScope", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  it("creates and reuses a stable anonymous public draft session id", () => {
    expect(getActivePublicDraftSession("incident-new")).toBe("");
    const first = ensureActivePublicDraftSession("incident-new");
    expect(first).toMatch(/^pds\./);
    expect(getActivePublicDraftSession("incident-new")).toBe(first);
    expect(ensureActivePublicDraftSession("incident-new")).toBe(first);
  });

  it("clears only the expected session when requested", () => {
    const first = ensureActivePublicDraftSession("meeting-new");
    clearActivePublicDraftSession("meeting-new", "different-session");
    expect(getActivePublicDraftSession("meeting-new")).toBe(first);
    clearActivePublicDraftSession("meeting-new", first);
    expect(getActivePublicDraftSession("meeting-new")).toBe("");
  });

  it("builds a scoped form key for device draft isolation", () => {
    const sessionId = "pds.test.123abc";
    expect(buildPublicDraftSessionScope(sessionId)).toBe("session::pds.test.123abc");
    expect(buildPublicDraftScopedFormKey("fleet-dvir", sessionId)).toBe("fleet-dvir::session::pds.test.123abc");
  });

  it("detects meaningful payloads without counting default-only fields", () => {
    expect(hasMeaningfulPublicDraft({ date: "2026-08-09", time: "08:00" }, ["date", "time"])).toBe(false);
    expect(hasMeaningfulPublicDraft({ date: "2026-08-09", truckUnit: "T-14" }, ["date"])).toBe(true);
    expect(hasMeaningfulPublicDraft({ trailers: [{ trailer_unit_number: "TRL-9" }] })).toBe(true);
  });
});