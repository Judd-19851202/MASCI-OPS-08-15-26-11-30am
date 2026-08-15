/* eslint-env jest */
/* global describe, test, expect */

// PQ v4 regression guard — mobile/touch scroll contract for every shared
// searchable selector. Protects the single shared owner (.masci-selector-scroll)
// and ensures each production selector's open results list opts into it, so the
// platform-wide "cannot finger-scroll the dropdown on mobile" defect cannot
// silently regress. Guards the shared root instead of dozens of route tests.

import fs from "fs";
import path from "path";

const read = (rel) => fs.readFileSync(path.join(process.cwd(), rel), "utf8");

describe("Shared selector mobile touch-scroll contract", () => {
  test("the shared .masci-selector-scroll class defines the full mobile scroll contract", () => {
    const css = read("src/design-system/wp17.css");
    const block = css.slice(css.indexOf(".masci-selector-scroll"));
    expect(block).toContain(".masci-selector-scroll");
    // A bounded, vertically scrollable viewport.
    expect(block).toContain("overflow-y: auto");
    // Vertical panning scrolls the list, not the page/body behind it.
    expect(block).toContain("overscroll-behavior: contain");
    // Browser owns vertical finger panning (tap handlers cannot cancel it).
    expect(block).toContain("touch-action: pan-y");
    // iOS momentum scrolling.
    expect(block).toContain("-webkit-overflow-scrolling: touch");
    // No accidental horizontal scroll.
    expect(block).toContain("overflow-x: hidden");
  });

  test.each([
    "src/components/EmployeeCombo.jsx",
    "src/components/EquipmentCombo.jsx",
    "src/components/SupplierCombo.jsx",
    "src/components/MasterLookupCombobox.jsx",
    "src/components/SearchableSelect.jsx",
    "src/components/AsyncSearchableSelect.jsx",
  ])("selector %s applies the shared scroll contract to its results list", (rel) => {
    const src = read(rel);
    expect(src).toContain("masci-selector-scroll");
    // Guard against re-introducing a bare, momentum-less scroll container.
    expect(src).not.toContain('w-full max-h-72 overflow-auto p-1.5');
    expect(src).not.toContain('w-full max-h-80 overflow-auto p-1.5');
  });

  test("the cmdk-based selectors keep the touch scroll props on CommandList", () => {
    const command = read("src/components/ui/command.jsx");
    expect(command).toContain("overscroll-contain");
    expect(command).toContain("touch-pan-y");
    expect(command).toContain('WebkitOverflowScrolling: "touch"');
  });

  test("the shared browse-first-on-touch helper prevents auto-focus only on coarse pointers", () => {
    const helper = read("src/lib/pickerTouchFocus.js");
    expect(helper).toContain("(pointer: coarse)");
    expect(helper).toContain("preventAutoFocusOnTouch");
    expect(helper).toContain("event.preventDefault()");
  });

  test.each([
    "src/components/JobPicker.jsx",
    "src/components/daily-report-v3/UnitCombo.jsx",
    "src/components/trench/EmployeePicker.jsx",
    "src/components/TopicPicker.jsx",
    "src/components/team/JobTeamRosterPanel.jsx",
  ])("cmdk-in-Popover picker %s opts into browse-first-on-touch (no keyboard over the list)", (rel) => {
    const src = read(rel);
    expect(src).toContain("preventAutoFocusOnTouch");
    expect(src).toContain("onOpenAutoFocus");
  });
});
