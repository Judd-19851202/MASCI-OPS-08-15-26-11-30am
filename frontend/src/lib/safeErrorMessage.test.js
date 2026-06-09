/* eslint-env jest */
/* global describe, test, expect */
import { safeErrorMessage } from "./safeErrorMessage";

describe("safeErrorMessage · PROD-FRONTEND-ERROR-001 contract", () => {
  test("string passes through", () => {
    expect(safeErrorMessage("boom")).toBe("boom");
  });
  test("Error instance returns .message", () => {
    expect(safeErrorMessage(new Error("kaboom"))).toBe("kaboom");
  });
  test("Pydantic single-detail object renders .msg", () => {
    expect(safeErrorMessage({ msg: "field required" })).toBe("field required");
  });
  test("Full Pydantic detail object (type+loc+msg+input+url) renders .msg only", () => {
    const v = { type: "missing", loc: ["body", "x"], msg: "field required", input: null, url: "https://errors.pydantic.dev/" };
    expect(safeErrorMessage(v)).toBe("field required");
    // CRITICAL: result is a primitive string, not the object
    expect(typeof safeErrorMessage(v)).toBe("string");
  });
  test("Array of Pydantic details joins .msg", () => {
    expect(safeErrorMessage([{ msg: "a" }, { msg: "b" }])).toBe("a; b");
  });
  test("Wrapper {detail:[...]}", () => {
    expect(safeErrorMessage({ detail: [{ msg: "x" }] })).toBe("x");
  });
  test("Wrapper {detail: object}", () => {
    expect(safeErrorMessage({ detail: { msg: "field required" } })).toBe("field required");
  });
  test("Wrapper {detail: 'string'}", () => {
    expect(safeErrorMessage({ detail: "plain text error" })).toBe("plain text error");
  });
  test("Unknown object → fallback", () => {
    expect(safeErrorMessage({ random: "thing" })).toBe("Something went wrong. Please try again.");
  });
  test("Undefined → fallback", () => {
    expect(safeErrorMessage(undefined)).toBe("Something went wrong. Please try again.");
  });
  test("Null → fallback", () => {
    expect(safeErrorMessage(null)).toBe("Something went wrong. Please try again.");
  });
  test("Custom fallback respected", () => {
    expect(safeErrorMessage(null, "Save failed")).toBe("Save failed");
  });
  test("Array of strings joins", () => {
    expect(safeErrorMessage(["a", "b"])).toBe("a; b");
  });
  test("Result is ALWAYS a string (never an object)", () => {
    const inputs = [
      undefined, null, "", "x", 42, true, false,
      new Error("e"), { msg: "y" }, [{ msg: "z" }],
      { detail: [{ msg: "q" }] }, { type: "x", loc: [], msg: "m" },
      { random: true }, [], {},
    ];
    inputs.forEach((v) => {
      expect(typeof safeErrorMessage(v)).toBe("string");
    });
  });
});
