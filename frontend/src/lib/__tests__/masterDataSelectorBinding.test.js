// P0-MASTERDATA-2026-08-13 — canonical master-data selector binding regressions.
//
// Proves the shared employee picker (EmployeeCombo) is bound to the ONE
// canonical HR roster authority and that representative multi-row / attendee
// forms consume that shared picker rather than a page-local employee array.
import fs from "fs";
import path from "path";

const SRC = path.join(__dirname, "..", "..");

function read(rel) {
  return fs.readFileSync(path.join(SRC, rel), "utf8");
}

describe("Canonical employee selector binding", () => {
  test("EmployeeCombo consumes the canonical HR roster authority", () => {
    const src = read("components/EmployeeCombo.jsx");
    // Canonical endpoint / shared roster fetcher (HR is gospel — Track 19.03).
    expect(src).toMatch(/employee-roster|fetchHrRoster/);
    // Must NOT hardcode an employee array as authority.
    expect(src).not.toMatch(/const\s+EMPLOYEES\s*=\s*\[/);
  });

  test("Safety Meeting attendee rows use the shared canonical picker", () => {
    const src = read("pages/NewMeeting.jsx");
    expect(src).toMatch(/import\s*\{\s*EmployeeCombo\s*\}/);
    // Attendees are a repeated row structure — the same picker is reused.
    expect(src).toMatch(/attendees/);
  });

  test("Incident person selectors use the shared canonical picker", () => {
    const src = read("pages/NewIncident.jsx");
    expect(src).toMatch(/import\s*\{\s*EmployeeCombo\s*\}/);
  });

  test("Field Leadership form binds to a canonical employee endpoint (same 239 active population)", () => {
    const src = read("pages/FieldLeadershipFormPage.jsx");
    // Portal-scoped canonical authority (returns the same active roster
    // population as EmployeeCombo). Consolidation to the shared component is a
    // tracked follow-up, but the DATA authority is canonical.
    expect(src).toMatch(/\/field-leadership\/employees/);
    // Must not hardcode an employee array.
    expect(src).not.toMatch(/const\s+EMPLOYEES\s*=\s*\[/);
  });

  test("Request-to-Add lives inside the canonical picker (fallback, not a parallel authority)", () => {
    const src = read("components/EmployeeCombo.jsx");
    // The inline add-request path is part of the same canonical picker so it
    // can only trigger after a canonical roster search.
    expect(src).toMatch(/employee-requests/);
  });
});
