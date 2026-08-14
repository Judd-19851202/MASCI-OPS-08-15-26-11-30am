/* global describe, test, expect */
/**
 * UI CONTRACT — Equipment Master (all assets) vs Equipment Status (inspection units)
 * are GOVERNED_DISTINCT populations (live prod: 604 vs 509). This test fails the
 * build if the human-visible copy ever implies they are the same fleet denominator.
 * Static source read (no runtime) so it is robust and CI-safe.
 */
import fs from "fs";
import path from "path";

const SRC = path.resolve(__dirname, "..");
const statusBoard = fs.readFileSync(path.join(SRC, "EquipmentStatusBoard.jsx"), "utf8");
const masterPanel = fs.readFileSync(path.join(SRC, "EquipmentMasterPanel.jsx"), "utf8");

describe("equipment population label contract (GOVERNED_DISTINCT)", () => {
  test("status board copy names inspection/status units", () => {
    expect(statusBoard).toMatch(/inspection unit/i);
    expect(statusBoard).toMatch(/distinct from the Equipment Master/i);
  });

  test("master panel copy names the canonical all-assets master", () => {
    expect(masterPanel).toMatch(/Equipment Master \(all assets\)/i);
  });

  test("the two count labels are NOT the identical generic 'units tracked'/'units in fleet' pair", () => {
    // regression guard: the old ambiguous copy implied a shared denominator
    expect(statusBoard).not.toMatch(/\{summary\.total_units\} unit\{[^}]*\} tracked\s*<\/p>/);
    expect(masterPanel).not.toMatch(/>\s*units in fleet\s*</);
  });
});
