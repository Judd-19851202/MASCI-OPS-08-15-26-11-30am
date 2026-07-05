import React from "react";
import { Section } from "@/components/Section";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { YesNo } from "@/components/YesNo";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

/**
 * DR-ROI-001F-REPAIR · Tomorrow Readiness — plain platform inputs
 * mirroring V1's Section 10b "Tomorrow / Follow-Up".
 */
export default function TomorrowReadinessSection({ draft, setDraft }) {
  const { t } = useDrV2Lang();
  const tr = draft.tomorrow_readiness || {};
  const set = (k, v) =>
    setDraft((d) => ({
      ...d,
      tomorrow_readiness: { ...(d.tomorrow_readiness || {}), [k]: v },
    }));

  const fields = [
    ["crew_needs", t("s06.crew_needs")],
    ["equipment_needs", t("s06.equip_needs")],
    ["material_needs", t("s06.material_needs")],
    ["inspection_needed", t("s06.inspection"), "yesno"],
    ["survey_needed", t("s06.survey"), "yesno"],
    ["decisions_needed", t("s06.decisions")],
  ];

  return (
    <Section number="06" title={t("s06.title")} testId="dr-v2-section-tomorrow">
      <div className="space-y-4">
        {fields.map(([k, label, type]) => (
          <div key={k}>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
              {label}
            </Label>
            {type === "yesno" ? (
              <YesNo
                value={tr[k] || ""}
                onChange={(v) => set(k, v)}
                testId={`dr-v2-tomorrow-${k}`}
              />
            ) : (
              <Textarea
                value={tr[k] || ""}
                onChange={(e) => set(k, e.target.value)}
                className="min-h-[60px] text-base border-2 border-slate-300"
                placeholder={t("s06.optional")}
                data-testid={`dr-v2-tomorrow-${k}`}
              />
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}
