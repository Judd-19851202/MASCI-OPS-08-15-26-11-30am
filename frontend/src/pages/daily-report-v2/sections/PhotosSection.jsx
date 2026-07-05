import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";

export default function PhotosSection({ draft }) {
  const count = draft?.photos?.length || 0;
  return (
    <SectionCard
      id="photos"
      title="8 · Photos"
      badge={`${count} / min 6`}
      description="At least six field photos are required. The same PhotoUpload component from the current Daily Report handles capture, gallery fallback, and mobile / iPad / ToughBook devices."
    >
      <PlaceholderPane
        testid="dr-v2-photos-placeholder"
        note={`Photo minimum 6 is enforced at submit. Photo → activity linking + vision-based evidence tags live in Photo Evidence above. Current: ${count} photo${count === 1 ? "" : "s"}.`}
      />
    </SectionCard>
  );
}
