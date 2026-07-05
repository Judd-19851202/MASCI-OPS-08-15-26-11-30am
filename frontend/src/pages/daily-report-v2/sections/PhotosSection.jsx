import React from "react";
import { Section } from "@/components/Section";
import { PhotoUpload } from "@/components/PhotoUpload";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

export default function PhotosSection({ draft, setDraft }) {
  const { t } = useDrV2Lang();
  const photos = draft.photos || [];
  const count = photos.length;
  const meetsMin = count >= 6;
  const set = (arr) => setDraft((d) => ({ ...d, photos: arr }));

  return (
    <Section
      number="08"
      title={t("s08.title")}
      testId="dr-v2-section-photos"
      highlight={!meetsMin}
      highlightLabel={`${count} / 6 ${t("s08.badge")}`}
      accent={meetsMin ? "emerald" : "red"}
    >
      <p className="text-sm text-slate-600 -mt-2 mb-2">{t("s08.desc")}</p>
      <PhotoUpload photos={photos} onChange={set} testIdBase="dr-v2-photos" />
      {!meetsMin ? (
        <p className="mt-3 text-sm font-semibold text-red-700" data-testid="dr-v2-photos-min-warning">
          {6 - count} {t("s08.min.warn")}
        </p>
      ) : (
        <p className="mt-3 text-sm font-semibold text-emerald-700" data-testid="dr-v2-photos-min-ok">
          {t("s08.min.ok")}
        </p>
      )}
    </Section>
  );
}
