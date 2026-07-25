/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */
import React from "react";
import { render, screen } from "@testing-library/react";

const mockApiGet = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args) => mockApiGet(...args),
  },
}));

jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));
jest.mock("@/components/ui/button", () => ({ Button: ({ children, ...props }) => <button {...props}>{children}</button> }));
jest.mock("@/components/admin/trust/TrustPrimitives", () => ({
  TruthOwnerPanel: ({ title, testidPrefix }) => <div data-testid={`${testidPrefix}-mock`}>{title}</div>,
}));
jest.mock("@/lib/platformTime", () => ({
  formatPlatformTime: () => "formatted-time",
}));

import PlatformTrustValidator from "../PlatformTrustValidator";

describe("PlatformTrustValidator OTS adoption", () => {
  beforeEach(() => {
    mockApiGet.mockReset();
  });

  test("renders bounded validator disclosure without unconditional trusted wording", async () => {
    mockApiGet.mockResolvedValue({
      data: {
        final_band: "green",
        generated_at: "2026-07-25T00:00:00Z",
        canonical_truth: {
          validation_surface: { surface_name: "Platform Trust Validator" },
        },
        truth_relationship: {
          role: "VALIDATOR",
          canonical_owner_id: "platform_attestation",
          canonical_status: "VERIFIED",
          derived_status: "VERIFIED",
          conflicts: [],
        },
        ots_truth: {
          truth_subject: "platform_validation_truth",
          permitted_claim: "VALIDATED",
          claim_ceiling: "VALIDATED",
          evidence_confidence: "HIGH",
          evidence_state: "validated",
          evidence_quality: "VALIDATED",
          claim_basis: ["platform_attestation", "workflow_delivery_health"],
          truth_evaluation: "VERIFIED",
          unknowns: [],
          contradictory_evidence: [],
          audit_reference: "OTS-C7-PLATFORM-TRUST-VALIDATOR",
        },
        compatibility: { preserved_fields: 11, new_additive_fields: 2, breaking_api_changes: 0 },
        workflow_delivery_health: [],
        system: { ok: true, app_env: "preview", db_name: "masci_safety_preview", mongo: true, scheduler: true, backup_recent: true },
        email_routing: { critical_empty_count: 0, errors_last_24h: 0, mode: "v2", v2_enabled: true, route_total: 4 },
        audit_status_integrity: { pass: true, unknown_status_count: 0, observed_statuses: [], allowed_statuses: [], unknown_statuses: [] },
        pm_email_coverage: { active_missing_unresolved: 0, active_total: 3, active_direct_pm_email: 2, active_roster_resolved: 1 },
        dead_letter_health: { dead_letters_24h: 0, dead_letter_unconfigured_total: 0, shop_recipient_unconfigured_24h: 0 },
        red_reasons: [],
        amber_reasons: [],
      },
    });

    render(<PlatformTrustValidator />);

    expect((await screen.findByTestId("platform-trust-bounded-headline")).textContent).toContain(
      "validated in scope without claiming platform ownership",
    );
    expect(screen.getByTestId("platform-trust-ots-disclosure-claim").textContent).toContain("VALIDATED");
    expect(screen.getByTestId("platform-trust-ots-disclosure-ceiling").textContent).toContain("VALIDATED");
    expect(screen.getByTestId("platform-trust-compatibility").textContent).toContain("breaking changes 0");
    expect(screen.queryByText("Trusted")).toBeNull();
  });

  test("renders unknowns and contradictions when validator evidence is bounded down", async () => {
    mockApiGet.mockResolvedValue({
      data: {
        final_band: "red",
        generated_at: "2026-07-25T00:00:00Z",
        canonical_truth: {
          validation_surface: { surface_name: "Platform Trust Validator" },
        },
        truth_relationship: {
          role: "VALIDATOR",
          canonical_owner_id: "platform_attestation",
          canonical_status: "MISMATCH",
          derived_status: "MISMATCH",
          conflicts: ["Validation evidence contradicts a clean platform-wide claim."],
        },
        ots_truth: {
          truth_subject: "platform_validation_truth",
          permitted_claim: "CORRELATED",
          claim_ceiling: "VALIDATED",
          evidence_confidence: "MEDIUM",
          evidence_state: "contradicted",
          evidence_quality: "CORRELATED",
          claim_basis: ["email_routing_audit_v2", "platform_attestation"],
          truth_evaluation: "MISMATCH",
          unknowns: ["Backup recency could not be confirmed from the validator surface."],
          contradictory_evidence: ["Audit status integrity observed 1 unsupported audit status event(s)."],
          audit_reference: "OTS-C7-PLATFORM-TRUST-VALIDATOR",
        },
        compatibility: { preserved_fields: 11, new_additive_fields: 2, breaking_api_changes: 0 },
        workflow_delivery_health: [],
        system: { ok: false, app_env: "preview", db_name: "masci_safety_preview", mongo: true, scheduler: true, backup_recent: null },
        email_routing: { critical_empty_count: 0, errors_last_24h: 0, mode: "legacy", v2_enabled: false, route_total: 2 },
        audit_status_integrity: { pass: false, unknown_status_count: 1, observed_statuses: ["mystery"], allowed_statuses: [], unknown_statuses: ["mystery"] },
        pm_email_coverage: { active_missing_unresolved: 1, active_total: 3, active_direct_pm_email: 1, active_roster_resolved: 1 },
        dead_letter_health: { dead_letters_24h: 1, dead_letter_unconfigured_total: 0, shop_recipient_unconfigured_24h: 0 },
        red_reasons: ["unknown_audit_status:mystery"],
        amber_reasons: ["pm_unresolved:1"],
      },
    });

    render(<PlatformTrustValidator />);

    expect((await screen.findByTestId("platform-trust-bounded-headline")).textContent).toContain(
      "contradictions or failing signals",
    );
    expect(screen.getByTestId("platform-trust-ots-disclosure-unknowns").textContent).toContain(
      "Backup recency could not be confirmed",
    );
    expect(screen.getByTestId("platform-trust-ots-disclosure-contradictions").textContent).toContain(
      "unsupported audit status",
    );
    expect(screen.getByTestId("platform-trust-red-reasons").textContent).toContain("unknown_audit_status:mystery");
  });
});