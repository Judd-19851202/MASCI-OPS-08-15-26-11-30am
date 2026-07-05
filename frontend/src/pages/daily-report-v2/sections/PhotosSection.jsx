import React from "react";
import { SectionCard, PlaceholderPane } from "../_ui";
export default function PhotosSection({ draft }) {
  const count = draft?.photos?.length || 0;
  return (
    <SectionCard id="photos" title="8 · Photos" badge={`${count} / min 6`}>
      <PlaceholderPane testid="dr-v2-photos-placeholder" note={`Photo minimum 6 is enforced. Photo → Activity Card linking + Vision-agent tags land in Track D. Current: ${count} photos.`} />
    </SectionCard>
  );
}
