import React from "react";
import { Section } from "@/components/Section";
import { YesNo } from "@/components/YesNo";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import DailyReportExcavationActivity from "@/components/trench/DailyReportExcavationActivity";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

/**
 * DR-ROI-001F-REPAIR · Safety & Quality — wires the existing safety
 * gates verbatim. Excavation / JHA / JHP gate uses the same
 * DailyReportExcavationActivity component V1 uses. YesNo chips match
 * the platform grammar (h-12, red-700 active).
 */
export default function SafetyQualitySection({ draft, setDraft }) {
  const { t } = useDrV2Lang();
  const safety = draft.safety || {};
  const set = (k, v) =>
    setDraft((d) => ({ ...d, safety: { ...(d.safety || {}), [k]: v } }));

  return (
    <Section number="07" title={t("s07.title")} testId="dr-v2-section-safety-quality">
      <div className="space-y-4">
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            {t("s07.incident")}
          </Label>
          <YesNo
            value={safety.incident_today || ""}
            onChange={(v) => set("incident_today", v)}
            testId="dr-v2-safety-incident"
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            {t("s07.injuries")}
          </Label>
          <YesNo
            value={safety.injuries || ""}
            onChange={(v) => set("injuries", v)}
            testId="dr-v2-safety-injuries"
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            {t("s07.notified")}
          </Label>
          <YesNo
            value={safety.safety_notified || ""}
            onChange={(v) => set("safety_notified", v)}
            options={["Yes", "No", "N/A"]}
            testId="dr-v2-safety-notified"
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
            {t("s07.quality_notes")}
          </Label>
          <Textarea
            value={safety.quality_notes || ""}
            onChange={(e) => set("quality_notes", e.target.value)}
            className="min-h-[80px] text-base border-2 border-slate-300"
            placeholder="Optional"
            data-testid="dr-v2-safety-quality-notes"
          />
        </div>

        {/* Excavation / JHA / JHP gate — verbatim from V1. Same schema,
            same gate, same required-plan enforcement. */}
        <DailyReportExcavationActivity data={draft} setData={setDraft} />
      </div>
    </Section>
  );
}
