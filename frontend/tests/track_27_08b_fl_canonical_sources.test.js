/**
 * TRACK 27.08B · Field Leadership canonical-source contract.
 *
 * Locks in source form the finding of the 27.08B audit:
 *   - FL `/api/field-leadership/jobs` reads `db.jobs_master`
 *     (same collection Daily Reports + PM workflows use).
 *   - FL `/api/field-leadership/employees` reads `db.employees`
 *     (HR employee master).
 *   - Equipment picker uses `OutstandingEquipmentLookup`, the
 *     canonical asset-outstanding scanner (equipment master).
 *   - FL submit payload preserves canonical IDs + labels.
 *
 * If any future refactor tries to reintroduce a shadow list, hardcoded
 * array, or free-text substitute where a canonical source exists,
 * this test blocks the change.
 */
const fs = require("fs");
const path = require("path");

const flBackendSrc = fs.readFileSync(
  path.resolve(__dirname, "../../backend/routes/field_leadership.py"),
  "utf-8",
);
const flFormSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/pages/FieldLeadershipFormPage.jsx"),
  "utf-8",
);

describe("TRACK 27.08B · FL canonical-source contract", () => {
  test("FL jobs endpoint reads from jobs_master (same source as DR / PM)", () => {
    expect(flBackendSrc).toMatch(/@router\.get\("\/jobs"\)/);
    expect(flBackendSrc).toMatch(/db\.jobs_master\.find/);
    // Must not read from any shadow/local collection.
    expect(flBackendSrc).not.toMatch(/db\.fl_jobs\.find/);
    expect(flBackendSrc).not.toMatch(/db\.field_leadership_jobs\.find/);
  });

  test("FL employees endpoint reads from HR employees master", () => {
    expect(flBackendSrc).toMatch(/@router\.get\("\/employees"\)/);
    expect(flBackendSrc).toMatch(/db\.employees\.find/);
    // is_active filter matches HR default projection.
    expect(flBackendSrc).toMatch(/"is_active":\s*\{[^}]*\$ne[^}]*\}/);
    // Must not read from any FL-only shadow.
    expect(flBackendSrc).not.toMatch(/db\.fl_employees\.find/);
    expect(flBackendSrc).not.toMatch(/db\.field_leadership_employees\.find/);
  });

  test("FL form uses OutstandingEquipmentLookup for equipment picker", () => {
    expect(flFormSrc).toContain("OutstandingEquipmentLookup");
    // No inline hardcoded equipment array should be present.
    expect(flFormSrc).not.toMatch(/const EQUIPMENT_LIST\s*=\s*\[/);
    expect(flFormSrc).not.toMatch(/const equipmentOptions\s*=\s*\[/);
  });

  test("FL submit payload preserves canonical IDs + labels", () => {
    // Every canonical field must appear on the payload build path.
    expect(flFormSrc).toContain("project_number: selectedJob?.project_number");
    expect(flFormSrc).toContain("project_name: selectedJob?.project_name");
    expect(flFormSrc).toContain("employee_id: selectedEmp?.id");
    expect(flFormSrc).toContain("employee_name: employeeNameFinal");
  });

  test("No inline hardcoded employee/job arrays remain in FL form", () => {
    // Guards against a future refactor that hardcodes a fallback list.
    expect(flFormSrc).not.toMatch(/const EMPLOYEE_LIST\s*=\s*\[/);
    expect(flFormSrc).not.toMatch(/const JOB_LIST\s*=\s*\[/);
    expect(flFormSrc).not.toMatch(/const HARDCODED_EMPLOYEES\s*=/);
    expect(flFormSrc).not.toMatch(/const HARDCODED_JOBS\s*=/);
  });
});
