/* eslint-env jest */
/* global describe, beforeEach, test, expect */
import {
  buildDailyReportInstanceScope,
  buildDailyReportScopedFormKey,
  buildDailyReportSessionScope,
  clearActiveDailyReportDraftSession,
  DAILY_REPORT_FORM_BASE,
  ensureActiveDailyReportDraftSession,
  getActiveDailyReportDraftSession,
} from "../dailyReportScope";

describe("daily report zero-drift scope", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  test("creates and reuses a stable daily-report draft session id", () => {
    expect(getActiveDailyReportDraftSession()).toBe("");
    const first = ensureActiveDailyReportDraftSession();
    expect(first).toMatch(/^drs\./);
    expect(getActiveDailyReportDraftSession()).toBe(first);
    expect(ensureActiveDailyReportDraftSession()).toBe(first);
  });

  test("clears only the expected daily-report session", () => {
    const first = ensureActiveDailyReportDraftSession();
    clearActiveDailyReportDraftSession("different-session");
    expect(getActiveDailyReportDraftSession()).toBe(first);
    clearActiveDailyReportDraftSession(first);
    expect(getActiveDailyReportDraftSession()).toBe("");
  });

  test("separates projects", () => {
    const a = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    const b = buildDailyReportScopedFormKey({ project_number: "26-08", report_date: "2026-07-13", report_instance: "primary" });
    expect(a).not.toBe(b);
  });

  test("prefers explicit draft session scope when one exists", () => {
    expect(buildDailyReportInstanceScope({ draft_session_id: "drs.test.123" })).toBe("session::drs.test.123");
    expect(buildDailyReportSessionScope("drs.test.123")).toBe("session::drs.test.123");
  });

  test("separates report dates", () => {
    const a = buildDailyReportInstanceScope({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    const b = buildDailyReportInstanceScope({ project_number: "26-07", report_date: "2026-07-14", report_instance: "primary" });
    expect(a).not.toBe(b);
  });

  test("separates report instances", () => {
    const a = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    const b = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "shift-b" });
    expect(a).not.toBe(b);
  });

  test("separates operators on the same project/date", () => {
    const a = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "Foreman A" });
    const b = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "Foreman B" });
    expect(a).not.toBe(b);
  });

  test("ignores actor identifiers for public daily report scope", () => {
    const a = buildDailyReportScopedFormKey({ actor_id: "dir-1", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "Foreman A" });
    const b = buildDailyReportScopedFormKey({ actor_id: "dir-2", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "Foreman A" });
    expect(a).toBe(b);
  });

  test("uses one canonical base form key", () => {
    const k = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    expect(k.startsWith(`${DAILY_REPORT_FORM_BASE}::`)).toBe(true);
  });
});
