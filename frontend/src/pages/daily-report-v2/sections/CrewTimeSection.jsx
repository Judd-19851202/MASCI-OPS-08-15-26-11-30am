import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function CrewTimeSection() {
  return (
    <SectionCard
      id="crew-time"
      title="2 · Crew Time"
      badge="HR-linked"
      description="HR-linked crew hours. Quick hours, absent, and left-early affordances arrive in the next release."
    >
      <PlaceholderPane
        testid="dr-v2-crewtime-placeholder"
        note="HR-linked masci_crews[] is preserved verbatim from V1. Payroll and time verification pipelines remain untouched."
      />
    </SectionCard>
  );
}
