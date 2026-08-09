import { describe, expect, it } from "@jest/globals";
import { sanitizeOperatorCopy } from "../operatorLanguage";

describe("operatorLanguage QA/QC governance", () => {
  it("normalizes QA slash QC variants to the canonical QA/QC domain name", () => {
    expect(sanitizeOperatorCopy("QA / QC", "QA / QC")).toBe("QA/QC");
    expect(sanitizeOperatorCopy("qaqc", "qaqc")).toBe("QA/QC");
    expect(sanitizeOperatorCopy("PM Portal · QA / QC", "PM Portal · QA / QC")).toBe("PM Portal · QA/QC");
  });

  it("preserves action phrasing without collapsing the domain into review QC", () => {
    expect(sanitizeOperatorCopy("Open QA / QC", "Open QA / QC")).toBe("Open QA/QC");
    expect(sanitizeOperatorCopy("Review QA / QC inspection", "Review QA / QC inspection")).toBe("Review QA/QC inspection");
    expect(sanitizeOperatorCopy("Quality Assurance · Quality Control", "Quality Assurance · Quality Control")).toBe("Quality Assurance / Quality Control");
  });
});