import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function SafetyQualitySection() {
  return (
    <SectionCard id="safety-quality" title="7 · Safety · Quality" badge="gate-preserving">
      <PlaceholderPane testid="dr-v2-safety-placeholder" note="Existing safety escalation + excavation/JHA/JHP gates preserved verbatim. Simpler yes/no chips with branch-into-existing-workflow · Track C." />
    </SectionCard>
  );
}
