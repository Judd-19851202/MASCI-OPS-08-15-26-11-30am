/* eslint-env jest */
import {
  buildDailyReportInstanceScope,
  buildDailyReportScopedFormKey,
  DAILY_REPORT_FORM_BASE,
} from "../dailyReportScope";

describe("daily report zero-drift scope", () => {
  test("separates projects", () => {
    const a = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    const b = buildDailyReportScopedFormKey({ project_number: "26-08", report_date: "2026-07-13", report_instance: "primary" });
    expect(a).not.toBe(b);
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

  test("ignores actor identifiers for public daily report scope", () => {
    const a = buildDailyReportScopedFormKey({ actor_id: "dir-1", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    const b = buildDailyReportScopedFormKey({ actor_id: "dir-2", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    expect(a).toBe(b);
  });

  test("uses one canonical base form key", () => {
    const k = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" });
    expect(k.startsWith(`${DAILY_REPORT_FORM_BASE}::`)).toBe(true);
  });
});
