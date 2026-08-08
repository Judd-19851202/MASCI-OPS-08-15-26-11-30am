import { describe, expect, test } from "@jest/globals";
import { getTruthfulValuePresentation, TRUTHFUL_DATA_STATE } from "./truthfulDataState";

describe("truthful data state presentation", () => {
  test("loading is not rendered as zero", () => {
    const out = getTruthfulValuePresentation({ isLoading: true, value: 0 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.LOADING);
    expect(out.displayValue).not.toBe("0");
  });

  test("unknown is not rendered as zero", () => {
    const out = getTruthfulValuePresentation({ isUnknown: true, value: 0 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.UNKNOWN);
    expect(out.displayValue).not.toBe("0");
  });

  test("error is not rendered as zero", () => {
    const out = getTruthfulValuePresentation({ error: new Error("boom"), value: 0 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.ERROR);
    expect(out.displayValue).not.toBe("0");
  });

  test("no access is not rendered as zero", () => {
    const out = getTruthfulValuePresentation({ hasAccess: false, value: 0 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.NO_ACCESS);
    expect(out.displayValue).not.toBe("0");
  });

  test("stale is not rendered as current", () => {
    const out = getTruthfulValuePresentation({ isStale: true, value: 14 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.STALE);
    expect(out.displayValue).toBe("—");
  });

  test("true zero remains a real zero", () => {
    const out = getTruthfulValuePresentation({ value: 0 });
    expect(out.state).toBe(TRUTHFUL_DATA_STATE.TRUE_ZERO);
    expect(out.displayValue).toBe("0");
  });
});
