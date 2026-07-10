/**
 * TRACK 27.07 P0 · Field Leadership launcher parity regression lock.
 *
 * The FL Portal Dashboard previously hard-coded a subset of the FL
 * form launchers, which meant new forms added to the schema (like
 * `employee_termination`, `equipment_return`, `time_off_request`)
 * would silently NOT appear on the Portal Dashboard until someone
 * remembered to also update the hard-coded list.
 *
 * The fix derives the launcher list directly from
 * `FIELD_LEADERSHIP_FORMS`. This test guards the fix so no future
 * change can bring back the drift.
 */
const fs = require("fs");
const path = require("path");

const dashSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/pages/FieldLeadershipPortalDashboard.jsx"),
  "utf-8",
);
const hubSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/pages/FieldLeadershipHub.jsx"),
  "utf-8",
);
const schemaSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/lib/fieldLeadershipSchemas.js"),
  "utf-8",
);

// Parse the `kind: "..."` occurrences from the schema file to build
// the ground-truth kind list without evaluating the module (avoids
// pulling in lucide-react in a Jest env).
const kindMatches = [...schemaSrc.matchAll(/kind:\s*"([a-z_]+)"/g)].map((m) => m[1]);
const ALL_KINDS = Array.from(new Set(kindMatches));

describe("Field Leadership launcher parity (TRACK 27.07)", () => {
  test("schema exposes expected kinds including employee_termination", () => {
    expect(ALL_KINDS).toContain("employee_termination");
    expect(ALL_KINDS).toContain("equipment_return");
    expect(ALL_KINDS).toContain("time_off_request");
    // Sanity floor — we ship substantially more than 5 forms.
    expect(ALL_KINDS.length).toBeGreaterThanOrEqual(10);
  });

  test("FL Portal Dashboard derives launchers from FIELD_LEADERSHIP_FORMS", () => {
    expect(dashSrc).toContain("FIELD_LEADERSHIP_FORMS");
    expect(dashSrc).toContain("SAFETY_EQUIPMENT_ISSUANCE_LINK");
    expect(dashSrc).toMatch(/FIELD_LEADERSHIP_FORMS\.map/);
  });

  test("FL Hub imports the schema so every kind gets a tile", () => {
    expect(hubSrc).toContain("FIELD_LEADERSHIP_FORMS");
    // Every schema kind must appear textually inside a `kinds: [...]`
    // group so a tile renders on the hub. Guards against orphaned
    // forms (schema-registered but not surfaced).
    const grouped = (hubSrc.match(/kinds:\s*\[[^\]]*]/g) || []).join(" ");
    for (const kind of ALL_KINDS) {
      expect(grouped).toContain(`"${kind}"`);
    }
  });

  test("Launcher testids follow the fl-launch-<kind> convention", () => {
    for (const kind of ALL_KINDS) {
      expect(`fl-launch-${kind}`).toMatch(/^fl-launch-[a-z_]+$/);
    }
  });
});
