/* global describe, test, expect */
/**
 * Regression: governed API errors arrive as an OBJECT detail
 * (e.g. { code:'project_scope_denied', message:'...' }). sanitizeOperatorError
 * must never emit "[object Object]" — it must extract a human string or fall back.
 * (Observed defect: PM Monday Review 403 toast rendered "[object Object]".)
 */
import { sanitizeOperatorError } from "@/lib/operatorLanguage";

describe("sanitizeOperatorError object-detail handling", () => {
  test("never returns the literal [object Object]", () => {
    const out = sanitizeOperatorError({ code: "project_scope_denied", message: "Access is restricted for this project." });
    expect(out).not.toMatch(/\[object Object\]/);
    expect(out.length).toBeGreaterThan(0);
  });

  test("extracts message from an object detail", () => {
    const out = sanitizeOperatorError({ message: "Access is restricted for this project." });
    expect(out).toMatch(/restricted/i);
  });

  test("object without usable string falls back", () => {
    const fb = "Could not complete the request.";
    expect(sanitizeOperatorError({}, fb)).toBe(fb);
  });

  test("plain string still works", () => {
    expect(sanitizeOperatorError("Needs review")).toMatch(/review/i);
  });
});
