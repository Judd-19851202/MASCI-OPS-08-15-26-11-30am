/* eslint-env jest */
/* global jest, describe, beforeEach, afterEach, test, expect */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

process.env.REACT_APP_BACKEND_URL = "https://example.test";

jest.mock("react-router-dom", () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

jest.mock("lucide-react", () => new Proxy({}, {
  get: (_target, prop) => (props) => <svg data-icon={String(prop)} {...props} />,
}));

jest.mock("@/lib/authHeaders", () => ({
  buildPortalAuthHeaders: () => ({ "X-Admin-Token": "test-admin" }),
}));

jest.mock("@/lib/platformTime", () => ({
  formatRelativeTime: () => "just now",
}));

jest.mock("@/lib/i18n", () => ({
  useT: () => ({ t: (value) => value, lang: "en" }),
}));

jest.mock("../../../design-system", () => ({
  PortalShell: ({ children, primaryActions }) => (
    <div data-testid="portal-shell">
      <div>{primaryActions}</div>
      {children}
    </div>
  ),
}));

jest.mock("@/design-system/responsive", () => ({
  ResponsiveSummaryStrip: ({ left, right, testid }) => (
    <div data-testid={testid}>
      <div>{left}</div>
      <div>{right}</div>
    </div>
  ),
}));

jest.mock("@/components/admin/sidebar/SideNavV3", () => () => <div data-testid="side-nav" />);
jest.mock("@/components/admin/AdminBreadcrumb", () => () => <div data-testid="admin-breadcrumb" />);
jest.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }) => <button type="button" {...props}>{children}</button>,
}));

import AdminOS from "../AdminOS";

const payloads = {
  "/api/admin/platform/status": {
    service: "masci-hub",
    attestation_version: "22.1K",
    readiness: { ready_flag: true },
  },
  "/api/admin/occ/health": {
    overall_status: "MISMATCH",
    overall_canonical: "MISMATCH",
    unique_critical_root_causes: 6,
    canonical_counts: {
      verified: 5,
      degraded: 2,
      mismatch: 6,
      unverifiable: 0,
      not_applicable: 1,
      total_applicable: 13,
    },
    generated_at: "2026-08-09T21:27:46.996073+00:00",
  },
  "/api/admin/recovery/snapshot": {
    pill: "green",
    backup_age_minutes: 24,
    backup_age_target_minutes: 60,
    archive_count: { r2_total: 69 },
    last_backup: { ts: "2026-08-09T21:00:00Z" },
  },
  "/api/ai/gateway/status": {
    gateway_enabled: true,
    resolved_provider_available: false,
    resolved_selected_provider: "claude",
    default_provider: "claude",
  },
  "/api/admin/email-routing/v2/status": {
    band: "amber",
    route_counts: { total: 20 },
    critical_empty_route_keys: [],
    mode: "preview_capture",
    ts: "2026-08-09T21:00:00Z",
  },
  "/api/admin/sessions/recent": {
    count: 50,
    timeouts_enabled: true,
    server_now: "2026-08-09T21:27:59.865620+00:00",
  },
  "/api/admin/governance/summary": {
    health_label: "critical",
    severity_counts: { critical: 54, high: 61 },
    rule_counts: { a: 1, b: 1 },
    freshness: { state: "CURRENT", last_scan_at: "2026-08-09T20:00:00Z" },
    convergence_score: 42,
  },
  "/api/admin/integrations/health": {
    overall_status: "ok",
    checked_at: "2026-08-09T21:27:59.499814+00:00",
    probes: [
      { id: "mongo", status: "ok" },
      { id: "r2", status: "ok" },
      { id: "maintainx", status: "disabled", mocked: true },
    ],
  },
  "/api/admin/system-health": {
    overall_canonical: "DEGRADED",
    counts: {
      verified: 7,
      degraded: 2,
      mismatch: 0,
      unverifiable: 0,
      not_applicable: 0,
      total_applicable: 9,
    },
    generated_at: "2026-08-09T21:28:00+00:00",
  },
  "/api/admin/operations-control/overview": {
    operations: [
      { id: "health.system_overview", status_snapshot: { status: "critical" } },
      { id: "deploy.readiness_check", status_snapshot: { status: "warning" } },
      { id: "integrations.probe_all", status_snapshot: { status: "healthy" } },
    ],
  },
};

describe("AdminOS truth lineage evaluation", () => {
  beforeEach(() => {
    global.fetch = jest.fn(async (url) => {
      const path = Object.keys(payloads).find((candidate) => String(url).includes(candidate));
      const body = path ? payloads[path] : {};
      return {
        ok: true,
        status: 200,
        json: async () => body,
      };
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("renders canonical Admin OS statuses without false green or false critical drift", async () => {
    render(<AdminOS />);

    await waitFor(() => {
      expect(screen.getByTestId("admin-os-card-platform-configuration-metric")).toHaveTextContent("2/2");
    });

    expect(screen.getByTestId("admin-os-card-operations-control-status")).toHaveTextContent("CRITICAL");
    expect(screen.getByTestId("admin-os-card-operations-control-metric")).toHaveTextContent("6");
    expect(screen.getByTestId("admin-os-card-operations-control-detail")).toHaveTextContent("6 critical signal(s) · 6 root cause(s)");

    expect(screen.getByTestId("admin-os-card-communications-status")).toHaveTextContent("ATTENTION");
    expect(screen.getByTestId("admin-os-card-ai-operations-status")).toHaveTextContent("CRITICAL");
    expect(screen.getByTestId("admin-os-card-platform-configuration-status")).toHaveTextContent("HEALTHY");
    expect(screen.getByTestId("admin-os-card-platform-configuration-detail")).toHaveTextContent("2 live probe(s) green · 1 not applicable");
    expect(screen.getByTestId("admin-os-card-diagnostics-status")).toHaveTextContent("ATTENTION");
    expect(screen.getByTestId("admin-os-card-diagnostics-metric")).toHaveTextContent("2");
  });

  test("retries a transient OCC probe failure instead of freezing the card in awaiting-signal state", async () => {
    let occAttempts = 0;
    global.fetch = jest.fn(async (url) => {
      const path = Object.keys(payloads).find((candidate) => String(url).includes(candidate));
      if (path === "/api/admin/occ/health") {
        occAttempts += 1;
        if (occAttempts === 1) {
          throw new DOMException("The operation was aborted.", "AbortError");
        }
      }
      return {
        ok: true,
        status: 200,
        json: async () => payloads[path] || {},
      };
    });

    render(<AdminOS />);

    await waitFor(() => {
      expect(screen.getByTestId("admin-os-card-operations-control-status")).toHaveTextContent("CRITICAL");
    });

    expect(screen.getByTestId("admin-os-card-operations-control-metric")).toHaveTextContent("6");
    expect(occAttempts).toBe(2);
  });
});