import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function EquipmentSection() {
  return (
    <SectionCard id="equipment" title="3 · Equipment">
      <PlaceholderPane testid="dr-v2-equipment-placeholder" note="Equipment used · hours · operator · idle/breakdown flags · activity link. Backend fields already exist; UI wire lands Track C." />
    </SectionCard>
  );
}
