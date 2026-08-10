/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("Executive Overview KPI consumer contract", () => {
  test("the page consumes the executive overview KPI API and tile metadata", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/pages/ExecutiveOverview.jsx"),
      "utf8",
    );

    expect(source).toContain('api.get(`/admin/executive/overview');
    expect(source).toContain('overview?.tiles');
    expect(source).toContain('metadata={overview.tiles.jobs?.kpi_metadata}');
    expect(source).toContain('metadata={overview.tiles.overdue?.kpi_metadata}');
    expect(source).toContain('metadata={overview.tiles.staffing?.kpi_metadata}');
    expect(source).toContain('metadata={overview.tiles.equipment?.kpi_metadata}');
    expect(source).toContain('metadata={overview.tiles.safety?.kpi_metadata}');
    expect(source).toContain('metadata={overview.tiles.activity?.kpi_metadata}');
  });
});