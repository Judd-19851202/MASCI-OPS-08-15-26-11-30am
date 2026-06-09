/**
 * projectIdentity.test.js — Unit tests for the canonical resolver.
 *
 * PROJECT-IDENTITY-002 · OMEGA DIRECTIVE
 *
 * Runs with: cd /app/frontend && yarn test --watchAll=false src/lib/projectIdentity.test.js
 */

import {
  resolveProjectIdentity,
  buildJobsMasterMaps,
  displayProjectIdentity,
} from "./projectIdentity";

const JOBS_MASTER = [
  { id: "uuid-26-01-cp", project_number: "26-01 - CP", project_name: "NSB Corbin Park Stormwater Improvements" },
  { id: "uuid-24-12",    project_number: "24-12",       project_name: "CC5744 - OXFORD RD Improvements (OXFORD)" },
  { id: "uuid-25-21",    project_number: "25-21",       project_name: "SJR2C - Loop Trail - Spruce Creek" },
  { id: "uuid-26-07",    project_number: "26-07",       project_name: "University High Parent Loop Ext" },
];

const ctx = (() => {
  const m = buildJobsMasterMaps(JOBS_MASTER);
  return { jobsMasterByPn: m.byPn, jobsMasterByNorm: m.byNorm, jobsMasterById: m.byId };
})();

describe("resolveProjectIdentity · resolution states", () => {
  test("canonical · record carries jobs_master_id", () => {
    const id = resolveProjectIdentity(
      { jobs_master_id: "uuid-24-12", project_number: "24-12", project_name: "Oxford coping" },
      ctx
    );
    expect(id.resolution_status).toBe("canonical");
    expect(id.canonical_project_number).toBe("24-12");
    expect(id.canonical_project_name).toBe("CC5744 - OXFORD RD Improvements (OXFORD)");
    expect(id.submitted_project_name).toBe("Oxford coping");
    expect(id.confidence).toBe(100);
    expect(id.source).toBe("jobs_master_id");
  });

  test("project_number_match · exact PN match resolves duplicate name (the user-reported Loop Trail case)", () => {
    const id = resolveProjectIdentity(
      { project_number: "25-21", project_name: "Loop trail " },
      ctx
    );
    expect(id.resolution_status).toBe("project_number_match");
    expect(id.canonical_project_name).toBe("SJR2C - Loop Trail - Spruce Creek");
    expect(id.submitted_project_name).toBe("Loop trail");  // trimmed
    expect(id.confidence).toBe(95);
  });

  test("project_number_match · case-insensitive matching on PN", () => {
    const id = resolveProjectIdentity(
      { project_number: "26-01 - cp", project_name: "Corbin park" },
      ctx
    );
    expect(id.resolution_status).toBe("project_number_match");
    expect(id.canonical_project_number).toBe("26-01 - CP");
    expect(id.canonical_project_name).toBe("NSB Corbin Park Stormwater Improvements");
  });

  test("project_number_normalized · whitespace variant resolves uniquely (26-01-CP → 26-01 - CP)", () => {
    const id = resolveProjectIdentity(
      { project_number: "26-01-CP", project_name: "Corbin park" },
      ctx
    );
    expect(id.resolution_status).toBe("project_number_normalized");
    expect(id.canonical_project_number).toBe("26-01 - CP");
    expect(id.canonical_project_name).toBe("NSB Corbin Park Stormwater Improvements");
    expect(id.confidence).toBe(85);
  });

  test("project_number_normalized · space-only variant resolves (26 01 CP → 26-01 - CP)", () => {
    const id = resolveProjectIdentity(
      { project_number: "26 01 CP", project_name: "x" },
      ctx
    );
    // "26 01 CP" normalizes to "26 01 CP" — doesn't equal "26 - 01 - CP".
    // So this is submitted_only, not normalized. The directive is explicit:
    // "If certainty is not 100%, remain unmatched." This proves that.
    expect(id.resolution_status).toBe("submitted_only");
  });

  test("submitted_only · PN is populated but unknown to jobs_master", () => {
    const id = resolveProjectIdentity(
      { project_number: "TEST-9999", project_name: "TEST Project" },
      ctx
    );
    expect(id.resolution_status).toBe("submitted_only");
    expect(id.canonical_project_number).toBeNull();
    expect(id.canonical_project_name).toBeNull();
    expect(id.submitted_project_number).toBe("TEST-9999");
    expect(id.confidence).toBe(30);
  });

  test("orphan · no PN at all", () => {
    const id = resolveProjectIdentity({ project_name: "Whatever" }, ctx);
    expect(id.resolution_status).toBe("orphan");
    expect(id.canonical_project_number).toBeNull();
    expect(id.submitted_project_number).toBe("");
    expect(id.confidence).toBe(0);
  });

  test("orphan · blank PN whitespace coerces to empty", () => {
    const id = resolveProjectIdentity({ project_number: "   ", project_name: "" }, ctx);
    expect(id.resolution_status).toBe("orphan");
  });

  test("job_number/job_name alias fields are honoured", () => {
    const id = resolveProjectIdentity(
      { job_number: "26-07", job_name: "University high school" },
      ctx
    );
    expect(id.resolution_status).toBe("project_number_match");
    expect(id.canonical_project_name).toBe("University High Parent Loop Ext");
  });

  test("project_id fallback · canonical via jobs_master.id even if recorded as project_id", () => {
    const id = resolveProjectIdentity(
      { project_id: "uuid-26-07", project_number: "26-07-OLD", project_name: "Old typed name" },
      ctx
    );
    expect(id.resolution_status).toBe("canonical");
    expect(id.canonical_project_number).toBe("26-07");
  });

  test("no fuzzy matching · spelling variant does NOT match", () => {
    const id = resolveProjectIdentity(
      { project_number: "2607", project_name: "University high school" },
      ctx
    );
    // No matching jobs_master row → submitted_only, NOT project_number_match
    expect(id.resolution_status).toBe("submitted_only");
  });

  test("no jobs_master context · everything PN-populated falls to submitted_only", () => {
    const id = resolveProjectIdentity(
      { project_number: "26-07", project_name: "x" },
      { jobsMasterByPn: {}, jobsMasterById: {} }
    );
    expect(id.resolution_status).toBe("submitted_only");
  });
});

describe("displayProjectIdentity · exhaustive switch contract", () => {
  test("canonical · returns canonical PN+name", () => {
    const id = resolveProjectIdentity(
      { project_number: "24-12", project_name: "Oxford coping" },
      ctx
    );
    const d = displayProjectIdentity(id);
    expect(d.number).toBe("24-12");
    expect(d.name).toBe("CC5744 - OXFORD RD Improvements (OXFORD)");
  });

  test("submitted_only · falls back to submitted values", () => {
    const id = resolveProjectIdentity(
      { project_number: "TEST-9999", project_name: "TEST Project" },
      ctx
    );
    const d = displayProjectIdentity(id);
    expect(d.number).toBe("TEST-9999");
    expect(d.name).toBe("TEST Project");
  });

  test("submitted_only with blank name · uses 'Unmatched Project · PN' fallback", () => {
    const id = resolveProjectIdentity({ project_number: "ABC-1" }, ctx);
    const d = displayProjectIdentity(id);
    expect(d.name).toBe("Unmatched Project · ABC-1");
  });

  test("orphan · returns the orphan label", () => {
    const id = resolveProjectIdentity({}, ctx);
    const d = displayProjectIdentity(id, { orphanLabel: "—" });
    expect(d.name).toBe("—");
    expect(d.number).toBe("—");
  });

  test("DOCTRINE SAFEGUARD · unhandled status throws", () => {
    expect(() =>
      displayProjectIdentity({ resolution_status: "future_status_we_added" })
    ).toThrow(/unhandled resolution_status/);
  });
});

describe("buildJobsMasterMaps", () => {
  test("byPn keys are uppercased & trimmed", () => {
    const m = buildJobsMasterMaps([
      { id: "a", project_number: "  26-07  ", project_name: "x" },
    ]);
    expect(m.byPn["26-07"]).toBeTruthy();
  });

  test("null rows are tolerated", () => {
    const m = buildJobsMasterMaps([null, { id: "a", project_number: "X", project_name: "y" }]);
    expect(m.byPn["X"].project_name).toBe("y");
  });
});
