/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("PM operational KPI consumer contract", () => {
  test("the PM KPI widget consumes governed metadata in the UI", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/components/PmOperationalKPIs.jsx"),
      "utf8",
    );

    expect(source).toContain('buildKpiHelpContent');
    expect(source).toContain('metadata={data?.kpi_metadata?.page}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.labor}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.equipment}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.materials}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.delays}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.production}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.safety}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.intelligence}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.scheduling_readiness}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.safety_sources}');
  });
});