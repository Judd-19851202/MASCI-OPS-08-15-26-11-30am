import React from "react";
import { Section } from "@/components/Section";
import { SignaturePad } from "@/components/SignaturePad";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

/**
 * DR-ROI-001F-REPAIR · Signature + Submit — uses the real V1 SignaturePad.
 * Submit is intentionally disabled in preview (Track G will certify cutover).
 */
export default function SignatureSubmitSection({ draft, setDraft }) {
  const set = (k, v) => setDraft((d) => ({ ...d, [k]: v }));
  const photoCount = (draft.photos || []).length;
  const canSubmit = photoCount >= 6 && !!draft.prepared_by_signature;

  return (
    <Section
      number="10"
      title="Signature + Submit"
      testId="dr-v2-section-signature"
    >
      <div className="space-y-4">
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            Prepared by · signature
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
            title="Submit is intentionally disabled in preview · Track G certifies cutover"
            data-testid="dr-v2-submit-btn"
          >
            Submit Daily Report (preview)
          </Button>
          <span
            className={`text-xs font-mono uppercase tracking-wider ${
              canSubmit ? "text-emerald-700" : "text-slate-500"
            }`}
            data-testid="dr-v2-submit-status"
          >
            {canSubmit
              ? "Ready · submit enabled at cutover"
              : `Not ready · ${photoCount < 6 ? `${6 - photoCount} more photo(s) · ` : ""}${!draft.prepared_by_signature ? "signature required · " : ""}preview mode`}
          </span>
        </div>
      </div>
    </Section>
  );
}
