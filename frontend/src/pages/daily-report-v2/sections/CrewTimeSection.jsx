import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function CrewTimeSection() {
  return (
    <SectionCard id="crew-time" title="2 · Crew Time" badge="HR-linked">
      <PlaceholderPane testid="dr-v2-crewtime-placeholder" note="HR-linked masci_crews[] preserved verbatim. Prefill · quick hours · absent/left-early chips arrive in Track C." />
    </SectionCard>
  );
}
