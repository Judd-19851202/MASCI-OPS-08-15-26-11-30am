import React from "react";
import { SectionCard, PlaceholderPane, StatusChip } from "../_ui";

export default function SignatureSubmitSection() {
  return (
    <SectionCard
      id="signature"
      title="10 · Signature + Submit"
      badge="submit blocked"
      description="Supervisor signature closes the report. Submit is intentionally disabled during preview — the PDF renderer and cutover certification arrive in the next session."
      action={<StatusChip tone="amber">preview only</StatusChip>}
    >
      <PlaceholderPane
        testid="dr-v2-signature-placeholder"
        note="The existing SignaturePad from V1 will be reused verbatim. Submit remains disabled until Track G certifies cutover."
      />
    </SectionCard>
  );
}
