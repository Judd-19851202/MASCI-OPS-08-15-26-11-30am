/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("public equipment pre-op reliability guards", () => {
  test("public pre-op passes publicFallback into the operator roster picker", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/pages/NewEquipmentInspection.jsx"),
      "utf8",
    );

    expect(source).toContain("publicFallback={publicMode}");
  });

  test("public asset lookup helpers suppress the global session-expired modal", () => {
    const chip = fs.readFileSync(
      path.join(process.cwd(), "src/components/SmartUnitClassificationChip.jsx"),
      "utf8",
    );
    const sections = fs.readFileSync(
      path.join(process.cwd(), "src/components/CanonicalInspectionSections.jsx"),
      "utf8",
    );

    expect(chip).toContain("skipSessionStatus: true");
    expect(sections).toContain("skipSessionStatus: true");
  });
});