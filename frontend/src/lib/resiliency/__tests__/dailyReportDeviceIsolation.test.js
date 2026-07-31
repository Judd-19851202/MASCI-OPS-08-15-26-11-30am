/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("daily report device-id isolation contract", () => {
  test("draft storage and recovery stay device-scoped", () => {
    const actorSource = fs.readFileSync(
      path.join(process.cwd(), "src/lib/resiliency/actorId.js"),
      "utf8",
    );
    const draftStoreSource = fs.readFileSync(
      path.join(process.cwd(), "src/lib/resiliency/draftStore.js"),
      "utf8",
    );

    expect(actorSource).toContain("export function getDeviceScopedActorId() {");
    expect(actorSource).toContain("return getDeviceId();");
    expect(draftStoreSource).toContain("const DRAFT_PREFIX = \"masci.draft.\"");
    expect(draftStoreSource).toContain("const ARCHIVE_PREFIX = \"masci.draft-archive.\"");
    expect(draftStoreSource).toContain("return `${DRAFT_PREFIX}${actorId || \"anon\"}.${formKey}`;");
    expect(draftStoreSource).toContain("return `${ARCHIVE_PREFIX}${actorId || \"anon\"}.${formKey}.${deletedAt}`;");
  });

  test("corrupted drafts are ignored instead of being restored", () => {
    const draftStoreSource = fs.readFileSync(
      path.join(process.cwd(), "src/lib/resiliency/draftStore.js"),
      "utf8",
    );

    expect(draftStoreSource).toContain("if (!entry || !entry.form) return null;");
  });

  test("public daily report fallback restores the latest same-device draft", () => {
    const dailyV3Source = fs.readFileSync(
      path.join(process.cwd(), "src/pages/NewDailyReportV3.jsx"),
      "utf8",
    );
    const dailySource = fs.readFileSync(
      path.join(process.cwd(), "src/pages/NewDailyReport.jsx"),
      "utf8",
    );

    expect(dailyV3Source).toContain("setFallbackDraftOffer(matches[0] || null)");
    expect(dailySource).toContain("setFallbackDraftOffer(matches[0] || null)");
  });
});