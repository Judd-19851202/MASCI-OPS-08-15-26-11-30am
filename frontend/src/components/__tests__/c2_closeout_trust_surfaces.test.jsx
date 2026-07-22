/* eslint-env jest */
/* global jest, describe, test, expect */
import React from "react";
import { render, screen } from "@testing-library/react";

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn((url) => {
      if (url.startsWith("/admin/operations-trust-center")) {
        return Promise.resolve({
          data: {
            trust_score: 92,
            score_band: "green",
            score_band_label: "Trusted",
            executive_narrative: "Canonical ownership is visible.",
            truth_surface: { surface_name: "Operations Trust Center" },
            truth_relationship: { relationship_type: "DERIVED_CONSUMER", canonical_owner_id: "trust_spine" },
            summary: { last_success_at: "2026-07-21T23:59:00Z", master_data_band: "green" },
            score_inputs: [],
            subsystems: [],
            trend: [],
            operator_actions: [],
            estimated_remediation_seconds: 0,
            critical_problems: [],
            operational_warnings: [],
            cleanup_opportunities: [],
            workflows: [],
          },
        });
      }
      if (url === "/admin/platform-trust/validate") {
        return Promise.resolve({
          data: {
            final_band: "green",
            generated_at: "2026-07-21T23:59:00Z",
            canonical_truth: { validation_surface: { surface_name: "Platform Trust Validator" } },
            truth_relationship: { relationship_type: "VALIDATOR", canonical_owner_id: "platform_attestation" },
            workflow_delivery_health: [],
            system: { ok: true, app_env: "preview", db_name: "masci_safety_preview", mongo: true, scheduler: true, backup_recent: true },
            email_routing: { critical_empty_count: 0, errors_last_24h: 0, mode: "v2", v2_enabled: true, route_total: 1 },
            audit_status_integrity: { pass: true, unknown_status_count: 0, observed_statuses: [], allowed_statuses: [], unknown_statuses: [] },
            pm_email_coverage: { active_missing_unresolved: 0, active_total: 1, active_direct_pm_email: 1, active_roster_resolved: 0 },
            dead_letter_health: { dead_letters_24h: 0, dead_letter_unconfigured_total: 0, shop_recipient_unconfigured_24h: 0 },
            red_reasons: [],
            amber_reasons: [],
          },
        });
      }
      if (url.startsWith("/admin/trust-spine/workflow/")) {
        return Promise.resolve({ data: { workflow: "daily_reports", events: [] } });
      }
      return Promise.resolve({ data: {} });
    }),
  },
}));

jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));
jest.mock("@/components/ui/button", () => ({ Button: ({ children, ...props }) => <button {...props}>{children}</button> }));
jest.mock("react-router-dom", () => ({ Link: ({ children, ...props }) => <a {...props}>{children}</a> }));
jest.mock("@/components/admin/trust/TrustPrimitives", () => ({
  TruthOwnerPanel: ({ title, testidPrefix }) => <div data-testid={`${testidPrefix}-mock`}>{title}</div>,
}));
jest.mock("@/lib/platformTime", () => ({
  formatPlatformTime: () => "formatted-time",
  formatPlatformDate: () => "formatted-date",
  formatPlatformTimeOnly: () => "formatted-time-only",
}));

import OperationsTrustCenter from "../OperationsTrustCenter";
import PlatformTrustValidator from "../PlatformTrustValidator";

describe("C2 closeout trust surfaces", () => {
  test("Operations Trust Center declares its active repaired disposition", async () => {
    render(<OperationsTrustCenter />);
    const node = await screen.findByTestId("operations-trust-center-disposition");
    expect(node.getAttribute("data-trust-surface-id")).toBe("operations_trust_center");
    expect(node.getAttribute("data-trust-disposition")).toBe("ACTIVE_REPAIRED");
    expect(node.getAttribute("data-trust-role")).toBe("DERIVED_CONSUMER");
    expect(node.getAttribute("data-canonical-owner")).toBe("trust_spine");
  });

  test("Platform Trust Validator declares its active repaired disposition", async () => {
    render(<PlatformTrustValidator />);
    const node = await screen.findByTestId("platform-trust-validator-disposition");
    expect(node.getAttribute("data-trust-surface-id")).toBe("platform_trust_validator");
    expect(node.getAttribute("data-trust-disposition")).toBe("ACTIVE_REPAIRED");
    expect(node.getAttribute("data-trust-role")).toBe("VALIDATOR");
    expect(node.getAttribute("data-canonical-owner")).toBe("platform_attestation");
  });
});