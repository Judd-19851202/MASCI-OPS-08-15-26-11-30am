import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function TomorrowReadinessSection() {
  return (
    <SectionCard
      id="tomorrow"
      title="6 · Tomorrow Readiness"
      description="Crew, equipment, materials, inspection, survey, traffic control, and decisions needed for tomorrow."
    >
      <PlaceholderPane
        testid="dr-v2-tomorrow-placeholder"
        note="Structured readiness schema is defined in DR_ROI_001_SCHEMA_PLAN.md. UI wire lands in the next release."
      />
    </SectionCard>
  );
}
