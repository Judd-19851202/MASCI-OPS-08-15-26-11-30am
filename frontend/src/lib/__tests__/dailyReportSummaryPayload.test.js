/* eslint-env jest */

import { describe, expect, test } from "@jest/globals";
import { buildDailyReportSummaryPayload, buildDeterministicSummaryFallback } from "@/lib/dailyReportSummaryPayload";
import { normalizeOperatorError } from "@/lib/operatorError";

const FIXTURE = {
  project_name: "D Curb Test",
  project_number: "27-DR03",
  report_date: "2026-07-15",
  prepared_by: "Jaymn Judd",
  location: "North lot",
  weather_summary: "Sunny",
  masci_crews: [
    {
      employee_id: "E-1",
      name: "Crew One",
      trade: "Concrete",
      start_time: "06:00",
      stop_time: "17:45",
      lunch_minutes: 30,
    },
  ],
  subcontractors: [
    {
      company: "Acme Concrete",
      count: 1,
      hours: 11,
      work_performed: "Finish support",
    },
  ],
  equipment: [
    {
      description: "Skid Steer",
      hours_used: 4,
      idle_hours: 6,
    },
  ],
  production: [
    {
      description: "D curb",
      quantity: 875,
      unit: "LF",
      percent_complete: 65,
    },
  ],
  photos: ["a", "b", "c", "d", "e", "f"],
};

describe("daily report summary payload", () => {
  test("normalizes the live Gate 5 fixture exactly", () => {
    const payload = buildDailyReportSummaryPayload(FIXTURE, {
      status: "not_requested",
      observations: [],
    });

    expect(payload.summary_input.labor.employee_count).toBe(1);
    expect(payload.summary_input.labor.total_employee_hours).toBe(11.25);
    expect(payload.summary_input.subcontractors.subcontractor_count).toBe(1);
    expect(payload.summary_input.subcontractors.total_hours).toBe(11);
    expect(payload.summary_input.equipment.equipment_count).toBe(1);
    expect(payload.summary_input.equipment.total_run_hours).toBe(4);
    expect(payload.summary_input.equipment.total_idle_hours).toBe(6);
    expect(payload.summary_input.production.rows[0]).toMatchObject({
      description: "D curb",
      quantity: 875,
      unit: "LF",
      percent_complete: 65,
    });
    expect(payload.summary_input.photos.photo_count).toBe(6);
    expect(payload.summary_input.photos.status).toBe("not_requested");
  });

  test("builds a fallback that preserves exact totals", () => {
    const text = buildDeterministicSummaryFallback(FIXTURE, { status: "not_requested" });
    expect(text).toContain("1 employee");
    expect(text).toContain("11.25 labor hours");
    expect(text).toContain("11.00 hours");
    expect(text).toContain("4.00 run hours");
    expect(text).toContain("6.00 idle hours");
    expect(text).toContain("875 LF D curb");
    expect(text).toContain("65% complete");
    expect(text).toContain("6 photos");
  });

  test("sanitizes photo-supported evidence punctuation joins", () => {
    const text = buildDeterministicSummaryFallback(FIXTURE, {
      status: "complete_with_observations",
      analyzed: 2,
      observations: [
        { description: "paving machine is in operation with fresh asphalt being laid." },
        { description: "illuminated work area indicates night operation.." },
      ],
    });
    expect(text).toContain("Photo-supported evidence: Paving machine is in operation with fresh asphalt being laid; Illuminated work area indicates night operation.");
    expect(text).not.toContain(".;");
    expect(text).not.toContain("..");
  });
});

describe("operator error normalization", () => {
  test("never returns raw object text", () => {
    const out = normalizeOperatorError({ response: { data: { detail: { error: "provider_unavailable", debug: { raw: true } } } } });
    expect(out.message).not.toBe("[object Object]");
    expect(out.message).not.toMatch(/^\{/);
    expect(out.code).toBe("provider_unavailable");
  });

  test("converts validation arrays to a calm operator message", () => {
    const out = normalizeOperatorError({
      response: {
        status: 422,
        data: {
          detail: [{ loc: ["body", "summary"], msg: "field required", type: "missing" }],
        },
      },
    });
    expect(out.message).toContain("summary");
    expect(out.code).toBe("validation_failed");
  });
});