/* eslint-env jest */

let mockIdb = {};
jest.mock("idb-keyval", () => ({
  get: jest.fn(async (k) => mockIdb[k]),
  set: jest.fn(async (k, v) => { mockIdb[k] = v; }),
  del: jest.fn(async (k) => { delete mockIdb[k]; }),
}));

describe("dailyReport legacy migration", () => {
  beforeEach(() => {
    mockIdb = {};
    jest.resetModules();
  });

  test("promotes newest valid legacy draft into canonical key and retires source", async () => {
    const mod = require("../draftStore");
    mockIdb["masci.draft.device-1.daily-report-new::dir-1::26-07::2026-07-13::primary"] = {
      savedAt: 10,
      savedByActor: "dir-1",
      form: { project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "A" },
    };
    const out = await mod.promoteLegacyDailyReportDraft({
      targetActorId: "device-1",
      targetFormKey: "daily-report::dir-1::26-07::2026-07-13::primary",
      targetContext: { actor_id: "dir-1", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" },
      candidates: [{
        key: "masci.draft.device-1.daily-report-new::dir-1::26-07::2026-07-13::primary",
        entry: mockIdb["masci.draft.device-1.daily-report-new::dir-1::26-07::2026-07-13::primary"],
      }],
    });
    expect(out.promoted).toBe(true);
    expect(out.retired).toBe(1);
    expect(mockIdb["masci.draft.device-1.daily-report::dir-1::26-07::2026-07-13::primary"]?.form?.prepared_by).toBe("A");
  });

  test("does not overwrite newer canonical draft", async () => {
    const mod = require("../draftStore");
    mockIdb["masci.draft.device-1.daily-report::dir-1::26-07::2026-07-13::primary"] = {
      savedAt: 50,
      savedByActor: "dir-1",
      form: { project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "NEW" },
    };
    const legacy = {
      savedAt: 10,
      savedByActor: "dir-1",
      form: { project_number: "26-07", report_date: "2026-07-13", report_instance: "primary", prepared_by: "OLD" },
    };
    const out = await mod.promoteLegacyDailyReportDraft({
      targetActorId: "device-1",
      targetFormKey: "daily-report::dir-1::26-07::2026-07-13::primary",
      targetContext: { actor_id: "dir-1", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" },
      candidates: [{ key: "masci.draft.device-1.daily-report-new::26-07::2026-07-13::R1", entry: legacy }],
    });
    expect(out.promoted).toBe(false);
    expect(out.reason).toBe("target_newer");
    expect(mockIdb["masci.draft.device-1.daily-report::dir-1::26-07::2026-07-13::primary"]?.form?.prepared_by).toBe("NEW");
  });

  test("preserves malformed or mismatched candidates", async () => {
    const mod = require("../draftStore");
    const bad = { savedAt: 10, savedByActor: "dir-2", form: { project_number: "99-01", report_date: "2026-07-13" } };
    mockIdb["masci.draft.device-1.daily-report-new::99-01::2026-07-13::R1"] = bad;
    const out = await mod.promoteLegacyDailyReportDraft({
      targetActorId: "device-1",
      targetFormKey: "daily-report::dir-1::26-07::2026-07-13::primary",
      targetContext: { actor_id: "dir-1", project_number: "26-07", report_date: "2026-07-13", report_instance: "primary" },
      candidates: [{ key: "masci.draft.device-1.daily-report-new::99-01::2026-07-13::R1", entry: bad }],
    });
    expect(out.promoted).toBe(false);
    expect(out.reason).toBe("no_valid_candidate");
    expect(mockIdb["masci.draft.device-1.daily-report-new::99-01::2026-07-13::R1"]).toBeTruthy();
  });
});