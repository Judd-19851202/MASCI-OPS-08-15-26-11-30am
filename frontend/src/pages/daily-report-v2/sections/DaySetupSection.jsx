import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function DaySetupSection() {
  return (
    <SectionCard id="day-setup" title="1 · Day Setup" badge="required">
      <PlaceholderPane testid="dr-v2-daysetup-placeholder" note="Project · date · shift · supervisor · weather · GPS · auto-fill hooks land in Track C." />
    </SectionCard>
  );
}
