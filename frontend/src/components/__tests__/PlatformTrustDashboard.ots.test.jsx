/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */
import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

const mockApiGet = jest.fn();

jest.mock("@/lib/api", () => ({
  api: {
    get: (...args) => mockApiGet(...args),
  },
}));

jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));
jest.mock("@/components/ui/button", () => ({ Button: ({ children, ...props }) => <button {...props}>{children}</button> }));
jest.mock("@/components/admin/LegacyAdminModernShell", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="legacy-admin-shell">{children}</div>,
}));
jest.mock("@/components/admin/trust/TrustPrimitives", () => ({
  TruthOwnerPanel: ({ title, testidPrefix }) => <div data-testid={`${testidPrefix}-mock`}>{title}</div>,
}));
jest.mock("@/lib/platformTime", () => ({
  formatPlatformTime: (value) => value || "formatted-time",
}));

import PlatformTrustDashboard from "../PlatformTrustDashboard";

describe("PlatformTrustDashboard OTS adoption", () => {
  beforeEach(() => {
    mockApiGet.mockReset();
  });

  test("renders canonical route disclosure and bounded headline", async () => {
    mockApiGet.mockImplementation((url) => {
      if (url === "/admin/trust-spine") {
        return Promise.resolve({
          data: {
            generated_at: "2026-07-25T00:00:00Z",
            platform_band: "green",
            canonical_status: "VERIFIED",
            truth_surface: { surface_name: "Platform Trust Spine" },
            truth_relationship: { canonical_owner_id: "trust_spine", role: "CANONICAL_OWNER", canonical_status: "VERIFIED", derived_status: "VERIFIED", conflicts: [] },
            ots_truth: {
              truth_subject: "workflow_lifecycle_truth",
              permitted_claim: "VALIDATED",
              claim_ceiling: "VALIDATED",
              evidence_confidence: "HIGH",
              evidence_state: "validated",
              evidence_quality: "VALIDATED",
              claim_basis: ["trust_spine_events", "expected_stage_contract"],
              truth_evaluation: "VERIFIED",
              unknowns: ["Idle workflows are evidence gaps, not proof of workflow health."],
              contradictory_evidence: ["Conflicting delivery-path evidence observed in the evaluation window: both provider acceptance and preview capture were recorded."],
              audit_reference: "OTS-C6-TRUST-SPINE",
            },
            total_events_24h: 12,
            total_failed_24h: 0,
            workflow_count: 1,
            allowed_stages: ["record_created", "completed"],
            workflows: [
              {
                workflow: "daily-report",
                band: "green",
                events_24h: 12,
                failed_24h: 0,
                success_rate_24h: 1,
                expected_stages: ["record_created", "completed"],
                missing_stages: [],
                reason: "12 ok events across 2/2 expected stages",
                remediation: null,
                last_success: { ts: "2026-07-25T00:00:00Z" },
                last_failure: null,
                ots_truth: {
                  truth_subject: "workflow_lifecycle_truth",
                  permitted_claim: "VALIDATED",
                  claim_ceiling: "VALIDATED",
                  evidence_confidence: "HIGH",
                  evidence_state: "validated",
                  evidence_quality: "VALIDATED",
                  claim_basis: ["trust_spine_events"],
                  truth_evaluation: "VERIFIED",
                  unknowns: [],
                  contradictory_evidence: [],
                  audit_reference: "OTS-C6-TRUST-SPINE-WORKFLOW",
                },
              },
            ],
          },
        });
      }
      if (url.startsWith("/admin/trust-spine/workflow/")) {
        return Promise.resolve({ data: { workflow: "daily-report", events: [] } });
      }
      return Promise.resolve({ data: {} });
    });

    render(<PlatformTrustDashboard />);

    const [headline] = await screen.findAllByTestId("trust-spine-bounded-headline");
    expect(headline.textContent).toContain(
      "Lifecycle evidence validated in scope.",
    );
    expect(screen.getByTestId("trust-spine-ots-disclosure-claim").textContent).toContain("VALIDATED");
    expect(screen.getByTestId("trust-spine-ots-disclosure-ceiling").textContent).toContain("VALIDATED");
    expect(screen.getByTestId("trust-spine-ots-disclosure-confidence").textContent).toContain("HIGH");
    expect(screen.getByTestId("trust-spine-ots-disclosure-unknowns").textContent).toContain("Idle workflows are evidence gaps");
    expect(screen.getByTestId("trust-spine-ots-disclosure-contradictions").textContent).toMatch(/Conflicting Delivery Path Evidence/i);
  });

  test("expanded workflow shows per-workflow truth disclosure for stale evidence", async () => {
    mockApiGet.mockImplementation((url) => {
      if (url === "/admin/trust-spine") {
        return Promise.resolve({
          data: {
            generated_at: "2026-07-25T00:00:00Z",
            platform_band: "amber-no-activity",
            canonical_status: "DEGRADED",
            truth_surface: { surface_name: "Platform Trust Spine" },
            truth_relationship: { canonical_owner_id: "trust_spine", role: "CANONICAL_OWNER", canonical_status: "DEGRADED", derived_status: "DEGRADED", conflicts: [] },
            ots_truth: {
              truth_subject: "workflow_lifecycle_truth",
              permitted_claim: "OBSERVED",
              claim_ceiling: "VALIDATED",
              evidence_confidence: "LOW",
              evidence_state: "observed",
              evidence_quality: "DURABLE_OBSERVED",
              claim_basis: ["per_workflow_rollup_24h"],
              truth_evaluation: "DEGRADED",
              unknowns: [],
              contradictory_evidence: [],
              audit_reference: "OTS-C6-TRUST-SPINE",
            },
            total_events_24h: 0,
            total_failed_24h: 0,
            workflow_count: 1,
            allowed_stages: ["record_created", "completed"],
            workflows: [
              {
                workflow: "daily-report",
                band: "amber-no-activity",
                events_24h: 0,
                failed_24h: 0,
                success_rate_24h: 0,
                expected_stages: ["record_created", "completed"],
                missing_stages: ["record_created", "completed"],
                reason: "no lifecycle events in last 24h",
                remediation: "Submit a record for this workflow to refresh its evidence.",
                last_success: null,
                last_failure: null,
                ots_truth: {
                  truth_subject: "workflow_lifecycle_truth",
                  permitted_claim: "OBSERVED",
                  claim_ceiling: "VALIDATED",
                  evidence_confidence: "LOW",
                  evidence_state: "stale",
                  evidence_quality: "DURABLE_OBSERVED",
                  claim_basis: ["latest_workflow_event"],
                  truth_evaluation: "DEGRADED",
                  unknowns: ["No lifecycle events were observed for this workflow in the last 24 hours."],
                  contradictory_evidence: [],
                  audit_reference: "OTS-C6-TRUST-SPINE-WORKFLOW",
                },
              },
            ],
          },
        });
      }
      if (url.startsWith("/admin/trust-spine/workflow/")) {
        return Promise.resolve({ data: { workflow: "daily-report", events: [] } });
      }
      return Promise.resolve({ data: {} });
    });

    render(<PlatformTrustDashboard />);
    const row = await screen.findByTestId("trust-spine-row-daily-report");
    fireEvent.click(row);

    expect((await screen.findByTestId("trust-spine-workflow-truth-daily-report-claim")).textContent).toContain("OBSERVED");
    expect(screen.getByTestId("trust-spine-workflow-truth-daily-report-state").textContent).toContain("Stale");
    expect(screen.getByTestId("trust-spine-workflow-truth-daily-report-unknowns").textContent).toContain(
      "No lifecycle events were observed for this workflow in the last 24 hours",
    );
  });
});