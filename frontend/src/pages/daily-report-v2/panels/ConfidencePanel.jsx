import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function ConfidencePanel() {
  return (
    <SectionCard id="panel-confidence" title="Confidence & Validation" badge="Track C">
      <PlaceholderPane testid="dr-v2-panel-confidence-placeholder" note="Aggregated confidence score across agents. Uncertainty flags shown here." />
    </SectionCard>
  );
}
