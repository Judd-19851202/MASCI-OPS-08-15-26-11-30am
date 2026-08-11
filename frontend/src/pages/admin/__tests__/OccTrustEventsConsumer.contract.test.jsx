/* eslint-env jest */
/* global jest, describe, beforeEach, test, expect */
import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";

const manifests = {};

jest.mock("lucide-react", () => new Proxy({}, { get: (_target, prop) => (props) => <svg data-icon={String(prop)} {...props} /> }));
jest.mock("@/components/admin/trust/DomainLandingShell", () => ({
  __esModule: true,
  default: ({ manifest, testidPrefix }) => {
    manifests[testidPrefix] = manifest;
    return <div data-testid={testidPrefix}>{manifest.label}</div>;
  },
}));

import AdminGovernanceTrust from "../AdminGovernanceTrust";
import AdminIdentitySecurity from "../AdminIdentitySecurity";

function trustEventsBody(overrides = {}) {
  return {
    generated_at: "2026-07-25T20:00:00+00:00",
    counts: { info: 2, warning: 1, critical: 3 },
    by_kind: { auth: 4, deploy_blocker: 2, ops_audit: 1 },
    auth_failures_in_window: 2,
    unresolved_blockers: [{ id: "gate-1", severity: "critical", summary: "deploy blocker" }],
    events: [
      { ts: "2026-07-25T20:00:00+00:00", kind: "auth", severity: "warning", summary: "auth fail", source_endpoint: "/api/admin/audit", evidence: {} },
      { ts: "2026-07-25T19:59:00+00:00", kind: "deploy_blocker", severity: "critical", summary: "deploy blocker", source_endpoint: "/api/admin/deployment-readiness", evidence: {} },
    ],
    probe_errors: {},
    truth_surface: { surface_id: "occ_trust_events", role: "AGGREGATOR", canonical_owner_id: "trust_spine" },
    truth_relationship: { role: "AGGREGATOR", canonical_owner_id: "trust_spine", canonical_owner_route: "/api/admin/trust-spine" },
    ots_truth: { truth_subject: "shared_operational_trust_event_feed", claim_ceiling: "OBSERVED" },
    compatibility: { breaking_api_changes: 0 },
    duplicate_suppression_count: 1,
    ...overrides,
  };
}

describe("OCC Trust Events consumer contract compatibility", () => {
  beforeEach(() => {
    Object.keys(manifests).forEach((key) => delete manifests[key]);
    cleanup();
  });

  test("AdminGovernanceTrust still evaluates trust-event cards with additive OTS fields present", () => {
    render(<AdminGovernanceTrust />);

    expect(screen.getByTestId("admin-governance-trust")).toHaveTextContent("Standards & Readiness");
    const manifest = manifests["admin-governance-trust"];
    const trustProbe = { ok: true, body: trustEventsBody() };

    const unified = manifest.cards.find((card) => card.id === "unified-trust-events").evaluator({ trust_events: trustProbe });

    expect(unified.status).toBe("red");
    expect(unified.summary).toMatch(/2 recent events/i);
    expect(unified.evidence.probe_errors).toEqual({});
    expect(unified.evidence.unresolved_blockers_count).toBe(1);
  });

  test("AdminIdentitySecurity still derives auth-failure status from the stable trust-events envelope", () => {
    render(<AdminIdentitySecurity />);

    expect(screen.getByTestId("admin-identity-security")).toHaveTextContent("Identity & Security");
    const manifest = manifests["admin-identity-security"];
    const trustProbe = { ok: true, body: trustEventsBody() };

    const authFailures = manifest.cards.find((card) => card.id === "auth-failures").evaluator({ trust_events: trustProbe });

    expect(authFailures.status).toBe("yellow");
    expect(authFailures.summary).toMatch(/2 auth failure\/lock event/i);
    expect(authFailures.evidence.recent_auth_events).toHaveLength(1);
  });
});