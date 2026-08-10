/* eslint-env jest */
/* global describe, test, expect, beforeEach, jest */

const state = {
  admin: false,
  pm: false,
  shop: false,
  hr: false,
  fl: false,
  legacyLeadership: false,
};

jest.mock("@/lib/adminAuth", () => ({ isAdmin: () => state.admin }));
jest.mock("@/lib/pmAuth", () => ({ isPm: () => state.pm }));
jest.mock("@/lib/shopAuth", () => ({ isShop: () => state.shop }));
jest.mock("@/lib/hrAuth", () => ({ isHr: () => state.hr }));
jest.mock("@/lib/flAuth", () => ({ isFl: () => state.fl }));
jest.mock("@/lib/leadershipAuth", () => ({ isLeadershipAuthed: () => state.legacyLeadership }));

const {
  supportsTrainingPacket,
  trainingAudienceAllowed,
  trainingAudienceLabel,
  trainingAudienceLoginPath,
} = require("@/lib/trainingAccess");

describe("training access contract", () => {
  beforeEach(() => {
    Object.assign(state, {
      admin: false,
      pm: false,
      shop: false,
      hr: false,
      fl: false,
      legacyLeadership: false,
    });
  });

  test("field leadership training accepts the governed FL portal token", () => {
    state.fl = true;
    expect(trainingAudienceAllowed("leadership")).toBe(true);
  });

  test("hr training remains protected until an HR or Admin session exists", () => {
    expect(trainingAudienceAllowed("hr")).toBe(false);
    state.hr = true;
    expect(trainingAudienceAllowed("hr")).toBe(true);
  });

  test("leadership login CTA points at the governed portal login", () => {
    expect(trainingAudienceLoginPath("leadership")).toBe("/field-leadership/portal/login");
  });

  test("packet support stays explicit by track", () => {
    expect(supportsTrainingPacket("field")).toBe(true);
    expect(supportsTrainingPacket("hr")).toBe(true);
    expect(supportsTrainingPacket("leadership")).toBe(false);
  });

  test("audience labels remain operator-friendly in both languages", () => {
    expect(trainingAudienceLabel("leadership", "en")).toBe("Field Leadership");
    expect(trainingAudienceLabel("leadership", "es")).toBe("Liderazgo de Campo");
  });
});