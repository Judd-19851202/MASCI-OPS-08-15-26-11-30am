/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("Safety project KPI drilldown contract", () => {
  test("the project drilldown consumes governed project safety metadata", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/components/SafetyOperationalKpisCard.jsx"),
      "utf8",
    );

    expect(source).toContain('metadata={data?.kpi_metadata?.page}');
    expect(source).toContain('metadata={data.kpi_metadata?.cards?.safety_event_count}');
    expect(source).toContain('metadata={data.kpi_metadata?.cards?.near_miss_and_injuries}');
    expect(source).toContain('metadata={data.kpi_metadata?.cards?.meetings_and_jhas}');
    expect(source).toContain('metadata={data.kpi_metadata?.cards?.trench_and_photos}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.safety_sources}');
    expect(source).toContain('metadata={data.kpi_metadata?.sections?.activity_context}');
  });
});