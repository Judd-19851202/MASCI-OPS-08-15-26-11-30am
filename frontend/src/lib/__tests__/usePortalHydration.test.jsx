/* eslint-env jest */
import React from "react";
import { afterEach, beforeEach, describe, expect, jest, test } from "@jest/globals";
import { render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { usePortalHydration } from "@/lib/usePortalHydration";

const mockPost = jest.fn();
const mockDirUser = jest.fn();
const mockDirToken = jest.fn();

jest.mock("@/lib/api", () => ({
  api: { post: (...args) => mockPost(...args) },
}));

jest.mock("@/lib/directoryAuth", () => ({
  getDirectoryUser: () => mockDirUser(),
  getDirectoryToken: () => mockDirToken(),
}));

jest.mock("@/lib/adminAuth", () => ({ setAdminToken: jest.fn() }));
jest.mock("@/lib/pmAuth", () => ({ setPmToken: jest.fn() }));
jest.mock("@/lib/shopAuth", () => ({ setShopToken: jest.fn() }));
jest.mock("@/lib/hrAuth", () => ({ setHrToken: jest.fn() }));
jest.mock("@/lib/safetyAuth", () => ({ setSafetyToken: jest.fn() }));
jest.mock("@/lib/dispatchAuth", () => ({ setDispatchToken: jest.fn() }));
jest.mock("@/lib/flAuth", () => ({ setFlToken: jest.fn() }));

function Probe({ portal = "admin", hasToken = false }) {
  const state = usePortalHydration(portal, hasToken);
  return <div data-testid="hydration-state">{state}</div>;
}

describe("usePortalHydration", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockPost.mockReset();
    mockDirUser.mockReset();
    mockDirToken.mockReset();
    mockDirUser.mockReturnValue({ portals: ["admin"] });
    mockDirToken.mockReturnValue("dir-token");
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("falls back to deny when portal token issuance hangs", async () => {
    mockPost.mockImplementation(() => new Promise(() => {}));
    render(<Probe />);

    expect(screen.getByTestId("hydration-state").textContent).toBe("hydrating");

    await act(async () => {
      jest.advanceTimersByTime(5100);
    });

    await waitFor(() => {
      expect(screen.getByTestId("hydration-state").textContent).toBe("deny");
    });
  });

  test("falls back to deny immediately on 401 portal issuance", async () => {
    const err = new Error("unauthorized");
    err.response = { status: 401 };
    mockPost.mockRejectedValue(err);
    render(<Probe />);

    await waitFor(() => {
      expect(screen.getByTestId("hydration-state").textContent).toBe("deny");
    });
  });
});