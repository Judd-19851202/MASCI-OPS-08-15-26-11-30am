import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function SignatureSubmitSection() {
  return (
    <SectionCard id="signature" title="10 · Signature + Submit" badge="submit blocked">
      <PlaceholderPane testid="dr-v2-signature-placeholder" note="Existing signature flow will be reused verbatim. Submit is intentionally disabled during preview — Track G certifies cutover." />
    </SectionCard>
  );
}
