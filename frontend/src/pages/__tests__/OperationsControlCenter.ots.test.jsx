/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import axios from "axios";

const mockGet = jest.fn();

jest.mock("axios", () => {
  const axiosMock = {
    get: (...args) => mockGet(...args),
    post: jest.fn(),
    create: jest.fn(() => ({
      get: (...args) => mockGet(...args),
      post: jest.fn(),
      interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    })),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  };
  return {
    __esModule: true,
    default: axiosMock,
    get: axiosMock.get,
    post: axiosMock.post,
    create: axiosMock.create,
    interceptors: axiosMock.interceptors,
  };
});

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock("react-router-dom", () => ({ Link: ({ children, ...props }) => <a {...props}>{children}</a> }));
jest.mock("lucide-react", () => new Proxy({}, { get: (_target, prop) => (props) => <svg data-icon={String(prop)} {...props} /> }));
jest.mock("@/design-system", () => ({ PortalShell: ({ children }) => <div data-testid="portal-shell">{children}</div> }));
jest.mock("@/components/admin/sidebar/SideNavV3", () => () => <div data-testid="side-nav" />);
jest.mock("@/components/admin/AdminBreadcrumb", () => () => <div data-testid="admin-breadcrumb" />);
jest.mock("@/lib/platformTime", () => ({ formatPlatformTime: () => "formatted-time" }));
jest.mock("@/components/admin/trust/TrustPrimitives", () => ({
  EvidenceDrawer: () => null,
  EvidenceSummary: ({ value }) => <div data-testid="mock-evidence-summary">{JSON.stringify(value)}</div>,
  HealthCard: ({ card }) => (
    <div data-testid={`mock-health-card-${card.id}`}>
      <span data-testid={`mock-health-card-${card.id}-status`}>{card.status}</span>
      <span>{card.title}</span>
    </div>
  ),
  TrustStatusPill: ({ status, testid }) => <div data-testid={testid}>{status}</div>,
  TruthOwnerPanel: ({ relationship, surface, testidPrefix }) => (
    <div data-testid={testidPrefix}>
      <span data-testid={`${testidPrefix}-role`}>{relationship?.role || surface?.role}</span>
      <span data-testid={`${testidPrefix}-owner`}>{relationship?.canonical_owner_id || surface?.canonical_owner_id}</span>
      <span data-testid={`${testidPrefix}-owner-route`}>{relationship?.canonical_owner_route || "—"}</span>
    </div>
  ),
  TRUST_STATUS_STYLES: {
    all: { label: "ALL" },
    red: { label: "CRITICAL" },
    yellow: { label: "ATTENTION" },
    unknown: { label: "UNKNOWN" },
    green: { label: "HEALTHY" },
  },
  sortCardsByAttention: (cards) => cards,
}));

import OperationsControlCenter from "../OperationsControlCenter";

function trustPayload(overrides = {}) {
  return {
    generated_at: "2026-07-25T00:00:00Z",
    overall_status: "MISMATCH",
    overall_canonical: "MISMATCH",
    truth_surface: {
      surface_id: "occ_health_aggregator",
      truth_subject: "shared_operational_posture",
      role: "AGGREGATOR",
      canonical_owner_id: "platform_attestation",
      owner_endpoint: "/api/admin/occ/health",
      owner_module: "backend/routes/occ_health_aggregator.py",
      upstream_owner_ids: ["platform_attestation", "integration_truth", "shared_auth_session"],
    },
    truth_relationship: {
      role: "AGGREGATOR",
      canonical_owner_id: "platform_attestation",
      canonical_owner_route: "/api/admin/platform/status",
      canonical_status: "MISMATCH",
      derived_status: "MISMATCH",
      derivation_explanation: "OCC health is a derived aggregator over fresh child probes; upstream canonical owners remain authoritative for their own subjects.",
      conflicts: [],
    },
    canonical_counts: {
      verified: 1,
      degraded: 1,
      mismatch: 1,
      unverifiable: 2,
      not_applicable: 1,
      total_applicable: 5,
    },
    counts: { VERIFIED: 1, DEGRADED: 1, MISMATCH: 1, UNVERIFIABLE: 2, NOT_APPLICABLE: 1 },
    sections: [
      {
        id: "platform_runtime",
        label: "Platform Runtime",
        status: "MISMATCH",
        cards: [
          { id: "api_health", title: "API Health", status: "MISMATCH", summary: "API not reachable.", endpoint: "/api/health", drilldown: "/admin/system-health", evidence: {}, checked_at: "2026-07-25T00:00:00Z" },
          { id: "version", title: "Build & Uptime", status: "VERIFIED", summary: "svc", endpoint: "/api/version", drilldown: "/admin/system-health", evidence: {}, checked_at: "2026-07-25T00:00:00Z" },
        ],
      },
    ],
    ...overrides,
  };
}

describe("OperationsControlCenter OTS hardening", () => {
  beforeEach(() => {
    mockGet.mockReset();
    axios.create.mockReset();
    axios.create.mockImplementation(() => ({
      get: (...args) => mockGet(...args),
      post: jest.fn(),
      interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    }));
    mockGet.mockImplementation((url) => {
      if (url.includes("/admin/operations-control/overview")) {
        return Promise.resolve({ data: { operations: [] } });
      }
      if (url.includes("/admin/operations-control/audit")) {
        return Promise.resolve({ data: { audit: [] } });
      }
      if (url.includes("/admin/occ/health")) {
        return Promise.resolve({ data: trustPayload() });
      }
      return Promise.resolve({ data: {} });
    });
  });

  test("renders bounded aggregator ownership and canonical route", async () => {
    render(<OperationsControlCenter />);

    expect(await screen.findByTestId("trust-layer-bounded-subject")).toHaveTextContent("shared_operational_posture");
    expect(screen.getByTestId("trust-layer-bounded-role")).toHaveTextContent("AGGREGATOR");
    expect(screen.getByTestId("trust-layer-bounded-owner")).toHaveTextContent("platform_attestation");
    expect(screen.getByTestId("trust-layer-bounded-owner-route")).toHaveTextContent("/api/admin/platform/status");
  });

  test("maps canonical statuses honestly for the OCC trust layer UI", async () => {
    render(<OperationsControlCenter />);

    await waitFor(() => {
      expect(screen.getByTestId("trust-layer-overall-pill")).toHaveTextContent("red");
    });
    expect(screen.getByTestId("trust-layer-count-healthy")).toHaveTextContent("1");
    expect(screen.getByTestId("trust-layer-count-attention")).toHaveTextContent("1");
    expect(screen.getByTestId("trust-layer-count-critical")).toHaveTextContent("1");
    expect(screen.getByTestId("trust-layer-count-unknown")).toHaveTextContent("2");
    expect(screen.getByTestId("trust-layer-count-neutral")).toHaveTextContent("1");
    expect(screen.getAllByTestId("mock-health-card-api_health-status")[0]).toHaveTextContent("red");
    expect(screen.getAllByTestId("mock-health-card-version-status")[0]).toHaveTextContent("green");
    expect(screen.queryByText(/Trust snapshot unavailable/i)).toBeNull();
  });
});