/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("daily report public draft continuity contract", () => {
  test("public daily report keeps anonymous-device recovery, fallback recovery, and submit dedupe guards", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/pages/NewDailyReportV3.jsx"),
      "utf8",
    );

    expect(source).toContain("getDeviceScopedActorId()");
    expect(source).toContain("publicAnonymous: true");
    expect(source).toContain("getActiveDailyReportDraftSession");
    expect(source).toContain("ensureActiveDailyReportDraftSession");
    expect(source).toContain("clearActiveDailyReportDraftSession");
    expect(source).toContain("recoverArchivedDraft");
    expect(source).toContain("findDraftEntriesForBase");
    expect(source).toContain("fallbackDraftOffer");
    expect(source).toContain("fetchHrRoster({ publicFallback: true })");
    expect(source).toContain("headers: { \"Idempotency-Key\": idem }");
    expect(source).toContain("clearActiveDailyReportDraftSession(data.draft_session_id || \"\")");
    expect(source).toContain("startAnotherTo: \"/daily/submit\"");
    expect(source).not.toContain("autoRestoredDraftRef");
    expect(source).not.toContain('api.get("/employees"');
  });
});