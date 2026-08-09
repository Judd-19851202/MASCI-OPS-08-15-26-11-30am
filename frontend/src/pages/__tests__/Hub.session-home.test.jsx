import React from "react";
import { describe, expect, it, jest, beforeEach } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockNavigate = jest.fn();
const mockClearAllSessions = jest.fn(() => Promise.resolve());

const authState = {
  adminToken: null,
};

jest.mock("react-router-dom", () => ({
  __esModule: true,
  MemoryRouter: ({ children }) => children,
  Link: ({ to, children, ...rest }) => <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>,
  NavLink: ({ to, children, ...rest }) => <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: "/", search: "", hash: "", state: null }),
  useParams: () => ({}),
  Outlet: () => null,
}), { virtual: true });

jest.mock("@/lib/adminAuth", () => ({
  __esModule: true,
  getAdminToken: () => authState.adminToken,
  clearAdminToken: () => {},
}));

jest.mock("@/lib/pmAuth", () => ({ __esModule: true, getPmToken: () => null, clearPmToken: () => {} }));
jest.mock("@/lib/shopAuth", () => ({ __esModule: true, getShopToken: () => null, clearShopToken: () => {} }));
jest.mock("@/lib/dispatchAuth", () => ({
  __esModule: true,
  getDispatchToken: () => null,
  clearDispatchToken: () => {},
  getDispatchUser: () => null,
}));
jest.mock("@/lib/hrAuth", () => ({
  __esModule: true,
  getHrToken: () => null,
  getHrUser: () => null,
  clearHrToken: () => {},
}));
jest.mock("@/lib/safetyAuth", () => ({
  __esModule: true,
  getSafetyToken: () => null,
  getSafetyUser: () => null,
  clearSafetyToken: () => {},
}));
jest.mock("@/lib/flAuth", () => ({ __esModule: true, getFlToken: () => null, clearFlToken: () => {} }));
jest.mock("@/lib/leadershipAuth", () => ({ __esModule: true, isLeadershipAuthed: () => false, clearLeadershipToken: () => {} }));

jest.mock("@/lib/permissions", () => ({
  __esModule: true,
  authorizedPortals: () => ["admin", "pm"],
  isSignedInAnywhere: () => Boolean(authState.adminToken),
  PORTAL_HOME: { admin: "/admin", pm: "/pm", hr: "/hr", dispatch: "/dispatch-portal" },
  PORTAL_LABEL: { admin: "Admin", pm: "Project Management", hr: "HR", dispatch: "Transportation Operations" },
}));

jest.mock("@/lib/sessionReset", () => ({
  __esModule: true,
  clearAllSessions: (...args) => mockClearAllSessions(...args),
  redirectToPublicHome: (navigate) => {
    if (typeof navigate === "function") navigate("/");
  },
}));

import { MemoryRouter } from "react-router-dom";
import Hub from "../Hub.jsx";

function renderHub() {
  return render(
    <MemoryRouter>
      <Hub />
    </MemoryRouter>,
  );
}

describe("Hub authenticated session treatment", () => {
  beforeEach(() => {
    authState.adminToken = null;
    mockNavigate.mockReset();
    mockClearAllSessions.mockClear();
  });

  it("keeps the signed-out home state intact when no session is active", () => {
    renderHub();
    expect(screen.getByTestId("hub-sign-in-link")).toBeTruthy();
    expect(screen.queryByTestId("home-session-control")).toBeNull();
  });

  it("shows a compact signed-in control instead of the old oversized home banner", () => {
    authState.adminToken = "admin-token";
    renderHub();

    expect(screen.queryByTestId("hub-welcome-back")).toBeNull();
    expect(screen.getByTestId("home-session-control")).toBeTruthy();
    expect(screen.getByTestId("hub-resume-link").getAttribute("href")).toBe("/admin");
  });

  it("signs out back to the public home from the compact session menu", async () => {
    authState.adminToken = "admin-token";
    renderHub();

    fireEvent.click(screen.getByTestId("home-session-control-trigger"));
    fireEvent.click(await screen.findByTestId("home-session-control-signout"));

    await waitFor(() => {
      expect(mockClearAllSessions).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });
});