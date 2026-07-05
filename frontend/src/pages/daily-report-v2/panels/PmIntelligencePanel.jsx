import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function PmIntelligencePanel() {
  return (
    <SectionCard id="panel-pm" title="PM Intelligence" badge="Track E">
      <PlaceholderPane testid="dr-v2-panel-pm-placeholder" note="Today's PM brief · open action items · tomorrow readiness risks · KPI signals." />
    </SectionCard>
  );
}
