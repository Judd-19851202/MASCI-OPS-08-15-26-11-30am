/* eslint-env jest */

jest.mock("@/lib/directoryAuth", () => ({
  getDirectoryUser: () => ({ id: "dir-1" }),
}), { virtual: true });
jest.mock("@/lib/flAuth", () => ({
  getFlToken: () => "fl.token",
  getFlUser: () => ({ id: "fl-1" }),
}), { virtual: true });
jest.mock("@/lib/hrAuth", () => ({ getHrToken: () => "", getHrUser: () => null }), { virtual: true });
jest.mock("@/lib/safetyAuth", () => ({ getSafetyToken: () => "", getSafetyUser: () => null }), { virtual: true });
jest.mock("@/lib/dispatchAuth", () => ({ getDispatchToken: () => "", getDispatchUser: () => null }), { virtual: true });
jest.mock("@/lib/adminAuth", () => ({ getAdminToken: () => "" }), { virtual: true });
jest.mock("@/lib/pmAuth", () => ({ getPmToken: () => "" }), { virtual: true });
jest.mock("@/lib/shopAuth", () => ({ getShopToken: () => "" }), { virtual: true });
jest.mock("@/lib/leadershipAuth", () => ({ getLeadershipToken: () => "" }), { virtual: true });

import { getStableActorIdentity } from "../actorId";

describe("stable continuity identity", () => {
  test("prefers stable directory user id over token slice", () => {
    expect(getStableActorIdentity()).toBe("directory.dir-1");
  });
});
