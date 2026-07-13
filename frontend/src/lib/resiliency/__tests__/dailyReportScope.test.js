/* eslint-env jest */
import {
  buildDailyReportInstanceScope,
  buildDailyReportScopedFormKey,
  DAILY_REPORT_FORM_BASE,
} from "../dailyReportScope";

describe("daily report zero-drift scope", () => {
  test("separates projects", () => {
    const a = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_number: "R1" });
    const b = buildDailyReportScopedFormKey({ project_number: "26-08", report_date: "2026-07-13", report_number: "R1" });
    expect(a).not.toBe(b);
  });

  test("separates report dates", () => {
    const a = buildDailyReportInstanceScope({ project_number: "26-07", report_date: "2026-07-13", report_number: "R1" });
    const b = buildDailyReportInstanceScope({ project_number: "26-07", report_date: "2026-07-14", report_number: "R1" });
    expect(a).not.toBe(b);
  });

  test("uses one canonical base form key", () => {
    const k = buildDailyReportScopedFormKey({ project_number: "26-07", report_date: "2026-07-13", report_number: "R1" });
    expect(k.startsWith(`${DAILY_REPORT_FORM_BASE}::`)).toBe(true);
  });
});
