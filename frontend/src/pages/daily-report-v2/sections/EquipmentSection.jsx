import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function EquipmentSection() {
  return (
    <SectionCard
      id="equipment"
      title="3 · Equipment"
      description="Equipment used today, hours, operator, and idle / breakdown flags. Links into activities."
    >
      <PlaceholderPane
        testid="dr-v2-equipment-placeholder"
        note="Equipment schema already exists on the backend. UI wire lands in the next release using the same EquipmentCombo used by the current Daily Report."
      />
    </SectionCard>
  );
}
