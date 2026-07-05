import React from "react";
import { Section } from "@/components/Section";
import { PhotoUpload } from "@/components/PhotoUpload";

/**
 * DR-ROI-001F-REPAIR · Photos — uses the real platform PhotoUpload
 * component with the minimum-6-photo rule enforced. Same R2 pipeline,
 * same base64 photos schema, same mobile / iPad / ToughBook fallback.
 */
export default function PhotosSection({ draft, setDraft }) {
  const photos = draft.photos || [];
  const count = photos.length;
  const meetsMin = count >= 6;
  const set = (arr) => setDraft((d) => ({ ...d, photos: arr }));

  return (
    <Section
      number="08"
      title="Field Photos"
      testId="dr-v2-section-photos"
      highlight={!meetsMin}
      highlightLabel={`${count} / 6 required`}
      accent={meetsMin ? "emerald" : "red"}
    >
      <p className="text-sm text-slate-600 -mt-2 mb-2">
        At least six field photos are required. Photos flow to the Job
        Photos mirror and become evidence for activities and constraints.
      </p>
      <PhotoUpload
        photos={photos}
        onChange={set}
        testIdBase="dr-v2-photos"
      />
      {!meetsMin ? (
        <p className="mt-3 text-sm font-semibold text-red-700" data-testid="dr-v2-photos-min-warning">
          {6 - count} more photo{6 - count === 1 ? "" : "s"} needed before submit.
        </p>
      ) : (
        <p className="mt-3 text-sm font-semibold text-emerald-700" data-testid="dr-v2-photos-min-ok">
          Minimum photo requirement met.
        </p>
      )}
    </Section>
  );
}
