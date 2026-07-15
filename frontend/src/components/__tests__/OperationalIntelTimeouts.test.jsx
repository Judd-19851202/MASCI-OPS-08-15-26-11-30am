/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  Link: ({ to, children, ...rest }) => (
    <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>
  ),
}), { virtual: true });

jest.mock("@/lib/adminAuth", () => ({ getAdminToken: () => "admin-token" }), { virtual: true });
jest.mock("@/lib/safetyAuth", () => ({ getSafetyToken: () => "safety-token" }), { virtual: true });
jest.mock("@/lib/api", () => ({ api: { get: jest.fn() } }), { virtual: true });
jest.mock("../operational_intelligence/GuidanceCard", () => () => null);

import OiAttentionStrip from "../operational_intelligence/OiAttentionStrip.jsx";
import ShopOpsIntelPanel from "../ShopOpsIntelPanel.jsx";
import SafetyOperationalKpisCard from "../SafetyOperationalKpisCard.jsx";
import SafetyTrenchIntelligenceCard from "../SafetyTrenchIntelligenceCard.jsx";
import { api } from "@/lib/api";

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn(() => Promise.reject({ name: "AbortError" }));
});

describe("operational intelligence timeout regressions", () => {
  test("HR strip shows truthful timeout copy and retry", async () => {
    render(
      <OiAttentionStrip
        productIds={["hr_attention"]}
        testId="hr-oi-timeout"
        portal="hr"
      />,
    );
    expect((await screen.findByTestId("hr-oi-timeout-empty")).textContent).toContain("timed out");
    expect(screen.getByTestId("hr-oi-timeout-retry")).toBeTruthy();
  });

  test("shop panel shows timeout state and retry", async () => {
    api.get.mockRejectedValueOnce({ code: "ECONNABORTED", message: "timeout of 5000ms exceeded" });
    render(<ShopOpsIntelPanel />);
    expect((await screen.findByTestId("ois-shop-panel-error")).textContent).toContain("timed out");
    expect(screen.getByTestId("ois-shop-retry")).toBeTruthy();
  });

  test("safety KPI card shows timeout state and retry", async () => {
    api.get.mockRejectedValueOnce({ code: "ECONNABORTED", message: "timeout of 5000ms exceeded" });
    render(<SafetyOperationalKpisCard />);
    expect((await screen.findByTestId("safety-kpis-error")).textContent).toContain("timed out");
    expect(screen.getByTestId("safety-kpis-retry")).toBeTruthy();
  });

  test("safety trench card shows timeout state and retry", async () => {
    render(<SafetyTrenchIntelligenceCard />);
    await waitFor(() => {
      expect(screen.getByTestId("safety-trench-error").textContent).toContain("timed out");
    });
    expect(screen.getByTestId("safety-trench-retry")).toBeTruthy();
  });
});