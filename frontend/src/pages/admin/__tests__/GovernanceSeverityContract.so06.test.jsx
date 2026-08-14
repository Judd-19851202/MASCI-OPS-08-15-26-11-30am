/* eslint-env jest */
/* global describe, test, expect, jest, beforeEach */
// SO-06 blast radius — governance advisory backlog must NOT render red/critical
// in frontend domain cards. Live production: severity_counts {critical:0,
// high:46, medium:312}, health_label "critical" (pre-backend-fix). These card
// evaluators independently re-derived red/critical from raw counts
// (AdminGovernanceTrust: highs>20; AdminOS: highs>0), bypassing the governed
// contract. A red/critical requires a GENUINE critical condition.
import React from "react";
import { render, cleanup } from "@testing-library/react";

const manifests = {};
jest.mock("lucide-react", () => new Proxy({}, { get: () => () => null }));
jest.mock("@/components/admin/trust/DomainLandingShell", () => ({
  __esModule: true,
  default: ({ manifest, testidPrefix }) => {
    manifests[testidPrefix] = manifest;
    return null;
  },
}));
jest.mock("@/lib/versionCache", () => ({ canonicalReleaseShaShort: () => "3DC83374" }));

import AdminGovernanceTrust from "../AdminGovernanceTrust";

function govProbe(sev, health, freshState = "STALE") {
  return { governance: { ok: true, body: {
    severity_counts: sev, health_label: health,
    freshness: { state: freshState }, convergence_score: 0, rule_counts: {},
  } } };
}

describe("SO-06 governance severity contract (frontend consumers)", () => {
  beforeEach(() => { Object.keys(manifests).forEach((k) => delete manifests[k]); cleanup(); });

  function govCard() {
    render(<AdminGovernanceTrust />);
    return manifests["admin-governance-trust"].cards.find((c) => c.id === "governance-summary").evaluator;
  }

  test("advisory high/medium backlog with 0 critical is yellow, not red", () => {
    const evalr = govCard();
    const r = evalr(govProbe({ critical: 0, high: 46, medium: 312 }, "degraded"));
    expect(r.status).toBe("yellow");
  });

  test("legacy false 'critical' label with 0 critical severity is still respected but advisory counts alone are not red", () => {
    const evalr = govCard();
    // 0 critical, health degraded, high backlog -> yellow (no false red from highs>20)
    const r = evalr(govProbe({ critical: 0, high: 99, medium: 0 }, "degraded"));
    expect(r.status).toBe("yellow");
  });

  test("genuine critical-severity finding is red", () => {
    const evalr = govCard();
    const r = evalr(govProbe({ critical: 2, high: 3, medium: 0 }, "critical"));
    expect(r.status).toBe("red");
  });

  test("failed scan is red (data untrustworthy)", () => {
    const evalr = govCard();
    const r = evalr(govProbe({ critical: 0, high: 0, medium: 0 }, "healthy", "SCAN_FAILED"));
    expect(r.status).toBe("red");
  });

  test("clean current governance is green", () => {
    const evalr = govCard();
    const r = evalr(govProbe({ critical: 0, high: 0, medium: 0 }, "healthy", "CURRENT"));
    expect(r.status).toBe("green");
  });
});
