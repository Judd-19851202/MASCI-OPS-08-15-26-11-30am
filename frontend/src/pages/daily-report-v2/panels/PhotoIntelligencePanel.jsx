import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function PhotoIntelligencePanel() {
  return (
    <SectionCard id="panel-photo-intel" title="Photo Intelligence" badge="Track D">
      <PlaceholderPane testid="dr-v2-panel-photointel-placeholder" note="Vision-detected tags · activity-link suggestions · missing-activity questions. Evidence-only; never final narrative." />
    </SectionCard>
  );
}
