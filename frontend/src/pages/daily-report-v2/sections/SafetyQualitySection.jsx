import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function SafetyQualitySection() {
  return (
    <SectionCard
      id="safety-quality"
      title="7 · Safety · Quality"
      badge="gates preserved"
      description="Safety escalation and excavation / JHA / JHP gates from V1 are preserved verbatim."
    >
      <PlaceholderPane
        testid="dr-v2-safety-placeholder"
        note="Yes / no chips branch into the existing safety workflows. No permission widening. No gate bypass."
      />
    </SectionCard>
  );
}
