/* eslint-env jest */
/* global describe, test, expect */
import fs from "fs";

describe("AppRoutes trust spine continuation", () => {
  const source = fs.readFileSync("/app/frontend/src/app/routing/AppRoutes.jsx", "utf8");

  test("adds exactly one admin trust-spine route", () => {
    const matches = source.match(/<Route path="\/admin\/trust-spine" element=\{A\(<PlatformTrustDashboard \/>\)\} \/>/g) || [];
    expect(matches).toHaveLength(1);
  });

  test("uses existing admin guard and preserves fallback route", () => {
    expect(source).toContain("<Route path=\"/admin/trust-spine\" element={A(<PlatformTrustDashboard />)} />");
    expect(source).toContain("const A = (el) => (");
    expect(source).toContain('<Route path="*" element={<NotFound />} />');
  });

  test("does not redirect trust-spine to another surface", () => {
    expect(source).not.toContain('Navigate to="/admin/trust-spine"');
    expect(source).not.toContain('path="/admin/trust-spine" element={<Navigate');
  });
});