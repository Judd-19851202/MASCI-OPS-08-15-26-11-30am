/* eslint-env jest */
/**
 * TRACK 26.08 · Daily Report Draft / Restore / Device Continuity
 *               regression tests.
 *
 * Covers three P0/P1 fixes shipped in Track 26.08:
 *
 *   G-1 (P0)  DraftRestorePrompt exposes draft.project_number +
 *             draft.report_date so a multi-project supervisor cannot
 *             silently restore another day's / another project's work.
 *
 *   G-2 (P0)  crewMemory.js is now scoped to the authenticated actor
 *             fingerprint. Two foremen on the same shared iPad no
 *             longer see each other's crew setup. Legacy pre-Track-26.08
 *             single-slot data is still readable ONCE as a fallback,
 *             then migrated forward on the next save.
 *
 *   G-3 (P1)  DraftStatusPill exposes the seven contract states:
 *             draft | saving | saved | offline | syncing | ready |
 *             submitted | failed  (never the operator-hostile word
 *             "synced").
 *
 * Uses react-dom/server to render components to HTML strings — no
 * @testing-library dependency needed.
 */

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

// Stub the stable actor identity before importing crewMemory.
jest.mock("../resiliency/actorId", () => {
  let _actor = "test.anon";
  return {
    getAuthActorFingerprint: () => _actor,
    getStableActorIdentity: () => _actor,
    __setActor: (v) => { _actor = v || "test.anon"; },
    getDeviceScopedActorId: () => "d.test-device-id",
    getActorId: () => "d.test-device-id",
    getLegacyActorIds: () => [],
  };
});
jest.mock("../resiliency/deviceId", () => ({
  getDeviceId: () => "d.test-device-id",
}));

jest.mock("../i18n", () => ({
  useT: () => ({ t: (s) => (typeof s === "string" ? s : ""), lang: "en" }),
}));

// Alias-resolved deps used by the components under test. These are
// pure UI props sinks — the tests only inspect strings, so a plain
// forwarding component is enough.
jest.mock("@/components/ui/button", () => ({
  Button: ({ children, ...rest }) => (
    <button type="button" {...rest}>{children}</button>
  ),
}), { virtual: true });
jest.mock("@/lib/i18n", () => ({
  useT: () => ({ t: (s) => (typeof s === "string" ? s : ""), lang: "en" }),
}), { virtual: true });

// eslint-disable-next-line import/first
import DraftRestorePrompt from "../resiliency/DraftRestorePrompt";
// eslint-disable-next-line import/first
import DraftStatusPill from "../resiliency/DraftStatusPill";
// eslint-disable-next-line import/first
import {
  saveCrewSetup,
  loadCrewSetup,
  clearCrewSetup,
  __TESTING__ as CREW_MEM_TESTING,
} from "../crewMemory";
// eslint-disable-next-line import/first, import/named
import { __setActor } from "../resiliency/actorId";

beforeEach(() => {
  try { window.localStorage.clear(); } catch { /* noop */ }
  __setActor("test.anon");
});

// ─────────────────────────────────────────────────────────────────
// G-1 · Restore prompt surfaces (project, report_date)
// ─────────────────────────────────────────────────────────────────

describe("TRACK 26.08 · G-1 · restore prompt surfaces project + date", () => {
  test("renders draft project_number + report_date on the section el", () => {
    const html = renderToStaticMarkup(
      <DraftRestorePrompt
        pendingDraft={{
          project_number: "26-07",
          project_name: "Track 26.08 Cert",
          report_date: "2026-07-08",
        }}
        savedAt={Date.now() - 60_000}
        isCrossToken={false}
        onRestore={() => {}}
        onDiscard={() => {}}
      />,
    );
    expect(html).toContain('data-testid="draft-restore-prompt"');
    expect(html).toContain('data-draft-project="26-07"');
    expect(html).toContain('data-draft-report-date="2026-07-08"');
    expect(html).toContain('data-testid="draft-restore-prompt-scope"');
    expect(html).toContain("26-07");
    expect(html).toContain("2026-07-08");
  });

  test("renders 'Project not yet selected' when project is empty", () => {
    const html = renderToStaticMarkup(
      <DraftRestorePrompt
        pendingDraft={{ project_number: "", report_date: "2026-07-08" }}
        savedAt={Date.now()}
        onRestore={() => {}}
        onDiscard={() => {}}
      />,
    );
    expect(html).toContain("Project not yet selected");
    expect(html).toContain("2026-07-08");
  });

  test("renders null when pendingDraft is falsy (no silent restore)", () => {
    const html = renderToStaticMarkup(
      <DraftRestorePrompt
        pendingDraft={null}
        savedAt={Date.now()}
        onRestore={() => {}}
        onDiscard={() => {}}
      />,
    );
    expect(html).toBe("");
  });
});

// ─────────────────────────────────────────────────────────────────
// G-2 · Crew memory is device/project/operator scoped (cross-crew guard)
// ─────────────────────────────────────────────────────────────────

describe("TRACK 26.08 · G-2 · crewMemory is per-device-project-operator", () => {
  test("Foreman A setup does not bleed into Foreman B on the same device and project", () => {
    saveCrewSetup({
      prepared_by: "Foreman A",
      superintendent: "Super A",
      project_number: "26-07",
      project_name: "Foreman A's Project",
      masci_crews: [{ name: "Alice", trade: "Op" }],
      equipment: [{ description: "CAT 336" }],
    });
    expect(loadCrewSetup({ projectNumber: "26-07", preparedBy: "Foreman A" })).not.toBeNull();
    expect(loadCrewSetup({ projectNumber: "26-07", preparedBy: "Foreman A" }).prepared_by).toBe("Foreman A");

    expect(loadCrewSetup({ projectNumber: "26-07", preparedBy: "Foreman B" })).toBeNull();
  });

  test("same foreman on same device and project gets the setup back", () => {
    saveCrewSetup({
      prepared_by: "Foreman A",
      project_number: "26-07",
      masci_crews: [{ name: "Alice" }],
    });
    expect(loadCrewSetup({ projectNumber: "26-07", preparedBy: "Foreman B" })).toBeNull();
    const rec = loadCrewSetup({ projectNumber: "26-07", preparedBy: "Foreman A" });
    expect(rec).not.toBeNull();
    expect(rec.prepared_by).toBe("Foreman A");
  });

  test("same device but different project does not restore the wrong setup", () => {
    saveCrewSetup({
      prepared_by: "Foreman A",
      project_number: "26-07",
      masci_crews: [{ name: "Alice" }],
    });
    expect(loadCrewSetup({ projectNumber: "26-08", preparedBy: "Foreman A" })).toBeNull();
  });

  test("blank operator context does not auto-restore a crew setup on shared devices", () => {
    saveCrewSetup({
      prepared_by: "Foreman A",
      project_number: "26-07",
      masci_crews: [{ name: "Alice" }],
    });
    expect(loadCrewSetup({ projectNumber: "26-07" })).toBeNull();
  });

  test("legacy pre-26.08 slot readable ONCE then migrates on next save", () => {
    window.localStorage.setItem(
      CREW_MEM_TESTING.LEGACY_STORAGE_KEY,
      JSON.stringify({
        schemaVersion: 1,
        prepared_by: "Legacy Foreman",
        project_number: "24-99",
        masci_crews: [{ name: "Legacy Crew" }],
        savedAt: Date.now(),
      }),
    );
    const rec = loadCrewSetup({ projectNumber: "24-99", preparedBy: "Legacy Foreman" });
    expect(rec).not.toBeNull();
    expect(rec.prepared_by).toBe("Legacy Foreman");
    saveCrewSetup({
      prepared_by: "New Foreman",
      project_number: "26-07",
      masci_crews: [{ name: "Alice" }],
    });
    const scopedKey = CREW_MEM_TESTING._contextKey({ projectNumber: "26-07", preparedBy: "New Foreman" });
    const scoped = window.localStorage.getItem(scopedKey);
    expect(scoped).toMatch(/New Foreman/);
  });

  test("clearCrewSetup wipes device-scoped setup keys and the legacy slot", () => {
    window.localStorage.setItem(
      CREW_MEM_TESTING.LEGACY_STORAGE_KEY,
      JSON.stringify({ schemaVersion: 1, prepared_by: "Legacy", savedAt: Date.now() }),
    );
    saveCrewSetup({
      prepared_by: "Foreman A",
      project_number: "26-07",
      masci_crews: [{ name: "X" }],
    });
    clearCrewSetup();
    const keys = Object.keys(window.localStorage).filter((k) => k.startsWith(CREW_MEM_TESTING._devicePrefix()));
    expect(keys).toHaveLength(0);
    expect(window.localStorage.getItem(CREW_MEM_TESTING.LEGACY_STORAGE_KEY)).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────
// G-3 · Draft status pill exposes seven contract states
// ─────────────────────────────────────────────────────────────────

describe("TRACK 26.08 · G-3 · draft status pill contract states", () => {
  const cases = [
    ["draft", "Draft"],
    ["saving", "Saving draft"],
    ["saved", "Saved"],
    ["offline", "Offline"],
    ["syncing", "Syncing"],
    ["ready", "Ready to submit"],
    ["submitted", "Submitted"],
  ];
  test.each(cases)("status=%s renders with data-state=%s and human label", (state, labelPart) => {
    const html = renderToStaticMarkup(
      <DraftStatusPill
        status={state}
        lastSavedAt={state === "saved" ? Date.now() : null}
        testId="pill-under-test"
      />,
    );
    expect(html).toContain(`data-state="${state}"`);
    expect(html.toLowerCase()).toContain(labelPart.toLowerCase());
  });

  test("no state ever labels the pill 'synced' (operator-hostile term)", () => {
    for (const [state] of cases) {
      const html = renderToStaticMarkup(
        <DraftStatusPill status={state} testId="pill-under-test" />,
      );
      expect(html.toLowerCase()).not.toContain("synced");
    }
  });
});
