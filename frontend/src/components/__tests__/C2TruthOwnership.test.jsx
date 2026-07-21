import React from "react";
import { describe, expect, it, jest } from "@jest/globals";
import { render, screen } from "@testing-library/react";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  Link: ({ to, children, ...rest }) => <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>,
}), { virtual: true });

import { TruthOwnerPanel } from "../admin/trust/TrustPrimitives";

describe("C2 truth ownership UI contract", () => {
  it("canonical owner is displayed", () => {
    render(
      <TruthOwnerPanel
        surface={{
          surface_id: "trust_spine",
          owner_endpoint: "/api/admin/trust-spine",
          owner_module: "backend/routes/admin_trust_spine.py",
          canonical_owner_id: "trust_spine",
          upstream_owner_ids: [],
        }}
        relationship={{
          role: "CANONICAL_OWNER",
          canonical_status: "VERIFIED",
          derived_status: "VERIFIED",
          canonical_owner_id: "trust_spine",
          derivation_explanation: "Direct lifecycle truth.",
          conflicts: [],
        }}
        checkedAt="2026-07-21T21:10:00Z"
        testidPrefix="truth-owner"
      />,
    );
    expect(screen.getByTestId("truth-owner-canonical-owner").textContent).toMatch(/trust_spine/);
  });

  it("derived status is labeled derived", () => {
    render(
      <TruthOwnerPanel
        surface={{ owner_endpoint: "/api/admin/operations-trust-center", owner_module: "backend/routes/admin_operations_trust_center.py", canonical_owner_id: "trust_spine", upstream_owner_ids: ["trust_spine"] }}
        relationship={{ role: "DERIVED_CONSUMER", canonical_status: "VERIFIED", derived_status: "DEGRADED", derivation_explanation: "Derived score.", conflicts: [] }}
        checkedAt="generated_at"
        testidPrefix="derived-owner"
      />,
    );
    expect(screen.getByTestId("derived-owner-derived-status").textContent).toMatch(/Displayed DEGRADED/);
  });

  it("conflict warning is displayed", () => {
    render(
      <TruthOwnerPanel
        surface={{ owner_endpoint: "/api/admin/platform-trust/validate", owner_module: "backend/routes/admin_platform_trust.py", canonical_owner_id: "platform_attestation", upstream_owner_ids: ["platform_attestation"] }}
        relationship={{ role: "VALIDATOR", canonical_status: "VERIFIED", derived_status: "MISMATCH", derivation_explanation: "Validation only.", conflicts: ["Validation result is separate from canonical platform truth."] }}
        checkedAt="generated_at"
        testidPrefix="validator-owner"
      />,
    );
    expect(screen.getByTestId("validator-owner-conflicts").textContent).toMatch(/separate from canonical platform truth/i);
  });

  it("evidence age is displayed", () => {
    render(
      <TruthOwnerPanel
        surface={{ owner_endpoint: "/api/admin/integrations/truth-status", owner_module: "backend/routes/integration_truth.py", canonical_owner_id: "integration_truth", upstream_owner_ids: [] }}
        relationship={{ role: "CANONICAL_OWNER", canonical_status: "VERIFIED", derived_status: "VERIFIED", derivation_explanation: "Integration truth.", conflicts: [] }}
        checkedAt="2 minutes ago"
        testidPrefix="age-owner"
      />,
    );
    expect(screen.getByTestId("age-owner-evidence-age").textContent).toMatch(/2 minutes ago/);
  });
});