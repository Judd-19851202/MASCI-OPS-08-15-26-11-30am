/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("public excavation contract", () => {
  test("public excavation workflow keeps draft continuity, idempotent submit, and public roster fallbacks", () => {
    const formSource = fs.readFileSync(
      path.join(process.cwd(), "src/pages/trench_safety/PublicExcavationForm.jsx"),
      "utf8",
    );
    const pickerSource = fs.readFileSync(
      path.join(process.cwd(), "src/components/trench/EmployeePicker.jsx"),
      "utf8",
    );

    expect(formSource).toContain("useFormDraft");
    expect(formSource).toContain("DraftRestorePrompt");
    expect(formSource).toContain("DraftStatusPill");
    expect(formSource).toContain("publicAnonymous: true");
    expect(formSource).toContain('headers: { "Idempotency-Key": idempotencyKeyRef.current }');
    expect(formSource).toContain('testId="public-excavation-draft-restore"');
    expect(formSource).toContain("publicFallback");

    expect(pickerSource).toContain('fetchHrRoster({ publicFallback })');
    expect(pickerSource).toContain('"/employees/competent-persons/public"');
  });
});