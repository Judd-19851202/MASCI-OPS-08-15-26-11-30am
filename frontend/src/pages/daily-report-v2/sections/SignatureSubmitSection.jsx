import React from "react";
import { Section } from "@/components/Section";
import { SignaturePad } from "@/components/SignaturePad";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

export default function SignatureSubmitSection({ draft, setDraft }) {
  const { t } = useDrV2Lang();
  const set = (k, v) => setDraft((d) => ({ ...d, [k]: v }));
  const photoCount = (draft.photos || []).length;
  const canSubmit = photoCount >= 6 && !!draft.prepared_by_signature;

  const status = canSubmit
    ? t("s10.status.ready")
    : `${t("s10.status.notready_prefix")}${
        photoCount < 6 ? `${6 - photoCount} ${t("s10.status.notready_more_photos")}` : ""
      }${!draft.prepared_by_signature ? t("s10.status.notready_sig") : ""}${t("s10.status.notready_suffix")}`;

  return (
    <Section number="10" title={t("s10.title")} testId="dr-v2-section-signature">
      <div className="space-y-4">
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            {t("s10.sign_label")}
          </Label>
          <SignaturePad
            value={draft.prepared_by_signature}
            onChange={(v) => set("prepared_by_signature", v)}
            label="Prepared By"
            testId="dr-v2-signature-pad"
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            className="h-12 px-6 bg-red-700 hover:bg-red-600 text-white font-bold uppercase tracking-wide"
            disabled
            title={t("s10.submit.hint")}
            data-testid="dr-v2-submit-btn"
          >
            {t("s10.submit")}
          </Button>
          <span
            className={`text-xs font-mono uppercase tracking-wider ${
              canSubmit ? "text-emerald-700" : "text-slate-500"
            }`}
            data-testid="dr-v2-submit-status"
          >
            {status}
          </span>
        </div>
      </div>
    </Section>
  );
}
