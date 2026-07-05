import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function DaySetupSection() {
  return (
    <SectionCard
      id="day-setup"
      title="1 · Day Setup"
      badge="required"
      description="Project, date, shift, supervisor, weather, and GPS. Prefill and auto-fill hooks wire in the next release."
    >
      <PlaceholderPane
        testid="dr-v2-daysetup-placeholder"
        note="Day setup fields (project · date · shift · supervisor · weather · GPS) will use the same JobPicker, date, and weather primitives as the current Daily Report."
      />
    </SectionCard>
  );
}
