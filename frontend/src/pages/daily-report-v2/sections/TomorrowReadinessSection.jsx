import React from "react";
import { Section } from "@/components/Section";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { YesNo } from "@/components/YesNo";

/**
 * DR-ROI-001F-REPAIR · Tomorrow Readiness — plain platform inputs
 * mirroring V1's Section 10b "Tomorrow / Follow-Up".
 */
export default function TomorrowReadinessSection({ draft, setDraft }) {
  const t = draft.tomorrow_readiness || {};
  const set = (k, v) =>
    setDraft((d) => ({
      ...d,
      tomorrow_readiness: { ...(d.tomorrow_readiness || {}), [k]: v },
    }));

  const fields = [
    ["crew_needs", "Crew needs for tomorrow"],
    ["equipment_needs", "Equipment needs for tomorrow"],
    ["material_needs", "Materials needed"],
    ["inspection_needed", "Inspection needed?", "yesno"],
    ["survey_needed", "Survey / model needed?", "yesno"],
    ["decisions_needed", "Decisions needed from PM / CEI"],
  ];

  return (
    <Section number="06" title="Tomorrow / Follow-Up" testId="dr-v2-section-tomorrow">
      <div className="space-y-4">
        {fields.map(([k, label, type]) => (
          <div key={k}>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
              {label}
            </Label>
            {type === "yesno" ? (
              <YesNo
                value={t[k] || ""}
                onChange={(v) => set(k, v)}
                testId={`dr-v2-tomorrow-${k}`}
              />
            ) : (
              <Textarea
                value={t[k] || ""}
                onChange={(e) => set(k, e.target.value)}
                className="min-h-[60px] text-base border-2 border-slate-300"
                placeholder="Optional"
                data-testid={`dr-v2-tomorrow-${k}`}
              />
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}
