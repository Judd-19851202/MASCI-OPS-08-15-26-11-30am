import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test } from "@jest/globals";
import ProjectIntelligenceStrip from "../ProjectIntelligenceStrip";

const makeRollup = (name, idx) => ({
  name,
  total: idx + 1,
  connected_count: idx,
  attention_required_count: idx % 2,
  offline_count: 0,
  assignment_source: "gps_location",
  assignment_confidence: idx % 2 ? "medium" : "high",
  last_activity_at: "2026-08-05T18:00:00Z",
});

describe("ProjectIntelligenceStrip overflow toggle", () => {
  test("reveals and collapses overflow areas", () => {
    const allRollups = Array.from({ length: 8 }, (_, idx) => makeRollup(`Area ${idx + 1}`, idx));

    render(
      <ProjectIntelligenceStrip
        rollups={allRollups.slice(0, 5)}
        allRollups={allRollups}
        overflow={3}
        total={8}
      />,
    );

    const visibleCards = () => screen.getAllByTestId(/^ops-map-project-card-\d+$/);

    expect(visibleCards()).toHaveLength(5);
    expect(screen.getByTestId("ops-map-projects-overflow").textContent).toContain("+3");

    fireEvent.click(screen.getByTestId("ops-map-projects-overflow"));
    expect(visibleCards()).toHaveLength(8);
    expect(screen.getByTestId("ops-map-projects-overflow").textContent).toContain("Top 5");

    fireEvent.click(screen.getByTestId("ops-map-projects-overflow"));
    expect(visibleCards()).toHaveLength(5);
  });
});