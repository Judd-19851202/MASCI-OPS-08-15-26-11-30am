/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

const mockGet = jest.fn();

jest.mock("@/lib/api", () => ({ api: { get: (...args) => mockGet(...args) } }));
jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));
jest.mock("@/components/ui/button", () => ({ Button: ({ children, ...props }) => <button {...props}>{children}</button> }));
jest.mock("react-router-dom", () => ({ Link: ({ children, ...props }) => <a {...props}>{children}</a> }));
jest.mock("@/components/admin/trust/TrustPrimitives", () => ({
  TruthOwnerPanel: ({ relationship, surface, testidPrefix }) => (
    <div data-testid={testidPrefix}>
      <span data-testid={`${testidPrefix}-role`}>{relationship?.role || surface?.role}</span>
      <span data-testid={`${testidPrefix}-owner`}>{relationship?.canonical_owner_id || surface?.canonical_owner_id}</span>
    </div>
  ),
}));
jest.mock("@/lib/platformTime", () => ({
  formatPlatformTime: () => "formatted-time",
  formatPlatformDate: () => "formatted-date",
  formatPlatformTimeOnly: () => "formatted-time-only",
}));

import OperationsTrustCenter from "../OperationsTrustCenter";

function payload(overrides = {}) {
  return {
    trust_score: 94,
    score_band: "green",
    score_band_label: "Green score band",
    executive_narrative: "Derived operational score is in the green band. No immediate derived action is surfaced by the current scoring model.",
    truth_surface: { surface_id: "operations_trust_center", canonical_owner_id: "trust_spine", role: "DERIVED_CONSUMER", owner_endpoint: "/api/admin/operations-trust-center", owner_module: "backend/routes/admin_operations_trust_center.py", upstream_owner_ids: ["trust_spine"] },
    truth_relationship: { role: "DERIVED_CONSUMER", canonical_owner_id: "trust_spine", canonical_owner_route: "/api/admin/trust-spine", canonical_status: "VERIFIED", derived_status: "DEGRADED", derivation_explanation: "Derived summary only.", conflicts: ["Derived operational score is green while Trust Spine supports only OBSERVED owner truth."] },
    ots_truth: {
      truth_subject: "shared_operational_trust_score",
      canonical_owner: "trust_spine",
      truth_surface: { surface_id: "operations_trust_center" },
      evidence_state: "partial",
      evidence_quality: "DURABLE_OBSERVED",
      evidence_confidence: "LOW",
      truth_evaluation: "DEGRADED",
      permitted_claim: "OBSERVED",
      claim_ceiling: "CORRELATED",
      claim_basis: ["trust_spine_owner_truth", "master_data_findings"],
      audit_reference: "C2-R1-OPERATIONS-TRUST-CENTER",
      unknowns: ["Master-data evaluation was unavailable, so the score cannot stand as complete evidence."],
      contradictory_evidence: ["Derived operational score is green while Trust Spine supports only OBSERVED owner truth."],
    },
    compatibility: { preserved_fields: 25, deprecated_fields: 0, new_additive_fields: 2, legacy_aliases_retained: [], breaking_api_changes: 0 },
    summary: { master_data_band: "green", last_success_at: "2026-07-25T00:00:00Z" },
    score_inputs: [],
    subsystems: [],
    trend: [{ ts: "2026-07-25T00:00:00Z", score: 94, band: "green" }, { ts: "2026-07-25T01:00:00Z", score: 92, band: "amber" }],
    operator_actions: [],
    estimated_remediation_seconds: 0,
    critical_problems: [],
    operational_warnings: [],
    cleanup_opportunities: [],
    workflows: [],
    ...overrides,
  };
}

describe("OperationsTrustCenter OTS", () => {
  beforeEach(() => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith("/admin/operations-trust-center")) return Promise.resolve({ data: payload() });
      if (url.startsWith("/admin/trust-spine/workflow/")) return Promise.resolve({ data: { workflow: "meeting", events: [] } });
      return Promise.resolve({ data: {} });
    });
  });

  test("renders bounded claim disclosure and ownership", async () => {
    render(<OperationsTrustCenter />);
    expect(await screen.findByTestId("otc-score-value")).toHaveTextContent("94");
    expect(screen.getByTestId("otc-bounded-headline").textContent).toMatch(/bounded disclosure/i);
    expect(screen.getByTestId("otc-truth-disclosure-claim")).toHaveTextContent("OBSERVED");
    expect(screen.getByTestId("otc-truth-disclosure-ceiling")).toHaveTextContent("CORRELATED");
    expect(screen.getByTestId("otc-truth-disclosure-score-vs-claim").textContent).toMatch(/cannot exceed Trust Spine/i);
    expect(screen.getByTestId("operations-trust-owner-panel-role")).toHaveTextContent("DERIVED_CONSUMER");
    expect(screen.getByTestId("operations-trust-owner-panel-owner")).toHaveTextContent("trust_spine");
  });

  test("renders unknowns and contradictions and removes trusted wording", async () => {
    render(<OperationsTrustCenter />);
    expect(await screen.findByTestId("otc-truth-disclosure-unknowns")).toHaveTextContent(/Master-data evaluation was unavailable/i);
    expect(screen.getByTestId("otc-truth-disclosure-contradictions")).toHaveTextContent(/Trust Spine supports only OBSERVED/i);
    expect(screen.queryByText("Trusted")).toBeNull();
    expect(screen.queryByText(/fully verified/i)).toBeNull();
    expect(screen.queryByText(/certified/i)).toBeNull();
    expect(screen.queryByText(/deployment ready/i)).toBeNull();
  });
});