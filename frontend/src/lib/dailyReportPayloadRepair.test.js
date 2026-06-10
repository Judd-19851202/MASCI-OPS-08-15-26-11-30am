/**
 * dailyReportPayloadRepair.test.js — OFFLINE-UPLOAD-002 pinning.
 *
 * Verifies the pure-function contract of the Daily Report payload
 * normalizer used by the resiliency queue's per-attempt repair hook.
 *
 * Runs with: cd /app/frontend && yarn test --watchAll=false src/lib/dailyReportPayloadRepair.test.js
 */
/* eslint-env jest */
/* global describe, test, expect */

import {
  normalizeDailyReportPayload,
  formatUnrepairableErrors,
} from "./dailyReportPayloadRepair";

describe("normalizeDailyReportPayload", () => {
  test("returns body unchanged when there are no numeric fields to repair", () => {
    const body = {
      project_name: "X", location: "Y", report_date: "2026-02-10",
      prepared_by: "Z",
    };
    const r = normalizeDailyReportPayload(body);
    expect(r.errors).toEqual([]);
    expect(r.warnings).toEqual([]);
    expect(r.repaired).toBe(false);
    expect(r.body).toEqual(body);
  });

  test("production[].quantity blank string → 0 (required float)", () => {
    const body = { production: [{ description: "concrete", quantity: "" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0].quantity).toBe(0);
    expect(r.warnings).toHaveLength(1);
    expect(r.warnings[0].path).toBe("production[0].quantity");
    expect(r.errors).toEqual([]);
    expect(r.repaired).toBe(true);
  });

  test('production[].quantity numeric string "2.5" → 2.5', () => {
    const body = { production: [{ description: "x", quantity: "2.5" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0].quantity).toBe(2.5);
    expect(r.errors).toEqual([]);
    expect(r.repaired).toBe(true);
  });

  test("production[].quantity 'abc' → error reported, value preserved", () => {
    const body = { production: [{ description: "x", quantity: "abc" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0].quantity).toBe("abc");
    expect(r.errors).toHaveLength(1);
    expect(r.errors[0].path).toBe("production[0].quantity");
    expect(r.errors[0].reason).toBe("not a number");
  });

  test("production[].quantity null → 0 (required default)", () => {
    const body = { production: [{ description: "x", quantity: null }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0].quantity).toBe(0);
    expect(r.errors).toEqual([]);
  });

  test("production[].quantity missing → 0 (required default)", () => {
    const body = { production: [{ description: "x" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0].quantity).toBe(0);
  });

  test("constraints[].hours_impact blank string → null (Optional float)", () => {
    const body = { constraints: [{ constraint_type: "weather", hours_impact: "" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.constraints[0].hours_impact).toBeNull();
    expect(r.errors).toEqual([]);
    expect(r.repaired).toBe(true);
  });

  test('constraints[].hours_impact numeric string "1.5" → 1.5', () => {
    const body = { constraints: [{ constraint_type: "weather", hours_impact: "1.5" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.constraints[0].hours_impact).toBe(1.5);
  });

  test("constraints[].hours_impact null/undefined → null (Optional, explicit)", () => {
    const body = { constraints: [
      { constraint_type: "weather", hours_impact: null },
      { constraint_type: "weather" },
    ]};
    const r = normalizeDailyReportPayload(body);
    expect(r.body.constraints[0].hours_impact).toBeNull();
    expect(r.body.constraints[1].hours_impact).toBeNull();
    expect(r.errors).toEqual([]);
  });

  test("outbound_materials[].quantity blank → null (treated optional)", () => {
    const body = { outbound_materials: [{ material: "millings", quantity: "" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.outbound_materials[0].quantity).toBeNull();
  });

  test("does not mutate the input body", () => {
    const original = {
      production: [{ description: "x", quantity: "" }],
      constraints: [{ constraint_type: "weather", hours_impact: "" }],
    };
    const snapshot = JSON.parse(JSON.stringify(original));
    normalizeDailyReportPayload(original);
    expect(original).toEqual(snapshot);
  });

  test("multiple rows + mixed shapes: repairs all repairable, flags malformed", () => {
    const body = {
      production: [
        { description: "a", quantity: "" },     // blank → 0
        { description: "b", quantity: "3" },    // string → 3
        { description: "c", quantity: 5 },      // number → 5
        { description: "d", quantity: "oops" }, // malformed → error
        { description: "e" },                   // missing → 0
      ],
      constraints: [
        { constraint_type: "weather", hours_impact: "" },     // blank → null
        { constraint_type: "weather", hours_impact: "2.0" },  // string → 2
        { constraint_type: "weather", hours_impact: "nope" }, // malformed → error
      ],
    };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production.map((p) => p.quantity)).toEqual([0, 3, 5, "oops", 0]);
    expect(r.body.constraints.map((c) => c.hours_impact)).toEqual([null, 2, "nope"]);
    expect(r.errors).toHaveLength(2);
    expect(r.errors[0].path).toBe("production[3].quantity");
    expect(r.errors[1].path).toBe("constraints[2].hours_impact");
    expect(r.repaired).toBe(true);
  });

  test("non-object body returns unchanged", () => {
    expect(normalizeDailyReportPayload(null).body).toBeNull();
    expect(normalizeDailyReportPayload(undefined).body).toBeUndefined();
    expect(normalizeDailyReportPayload("string").body).toBe("string");
    expect(normalizeDailyReportPayload(42).body).toBe(42);
  });

  test("rows that are not objects are left untouched", () => {
    const body = { production: [null, "not-an-object", { description: "x", quantity: "" }] };
    const r = normalizeDailyReportPayload(body);
    expect(r.body.production[0]).toBeNull();
    expect(r.body.production[1]).toBe("not-an-object");
    expect(r.body.production[2].quantity).toBe(0);
  });
});

describe("formatUnrepairableErrors", () => {
  test("empty array returns empty string", () => {
    expect(formatUnrepairableErrors([])).toBe("");
    expect(formatUnrepairableErrors(null)).toBe("");
  });
  test("single error formats with path + value", () => {
    const s = formatUnrepairableErrors([
      { path: "production[0].quantity", value: "abc", reason: "not a number" },
    ]);
    expect(s).toContain("production[0].quantity");
    expect(s).toContain("not a number");
    expect(s).toContain('"abc"');
  });
  test("more than 3 errors are truncated with '(+N more)'", () => {
    const errs = Array.from({ length: 5 }, (_, i) => ({
      path: `production[${i}].quantity`, value: "x", reason: "not a number",
    }));
    const s = formatUnrepairableErrors(errs);
    expect(s).toContain("(+2 more)");
  });
});
