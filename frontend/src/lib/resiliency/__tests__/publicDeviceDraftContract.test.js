/* eslint-env jest */
/* global describe, it, expect */

import fs from "fs";

const PUBLIC_DRAFT_FILES = [
  "/app/frontend/src/pages/NewInspection.jsx",
  "/app/frontend/src/pages/NewMeeting.jsx",
  "/app/frontend/src/pages/NewIncident.jsx",
  "/app/frontend/src/pages/NewSafetyEquipmentIssuance.jsx",
  "/app/frontend/src/pages/NewSafetyEquipmentTraining.jsx",
  "/app/frontend/src/pages/NewEquipmentInspection.jsx",
  "/app/frontend/src/pages/NewFleetDVIR.jsx",
];

describe("public device draft contract wiring", () => {
  it.each(PUBLIC_DRAFT_FILES)("%s uses anonymous device draft protections", (filePath) => {
    const source = fs.readFileSync(filePath, "utf8");
    expect(source).toContain("getDeviceScopedActorId");
    expect(source).toContain("publicAnonymous: true");
    expect(source).toContain("DraftRestorePrompt");
    expect(source).toContain("DraftStatusPill");
    expect(source).toContain("ensureActivePublicDraftSession");
    expect(source).toContain("clearActivePublicDraftSession");
  });
});