// TRACK 15.62 · NarrativeWorkflow — six guided prompts that capture
// the operational story of the day. Writes to `narrative_sections` on
// the Daily Report payload. Mandatory NONE. Guided ALL.
import React from "react";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";

const PROMPTS = [
  { key: "work_completed",     label: "What work was performed today?",
    hint: "Stations, quantities, locations. e.g. 'Backfilled 200 LF station 314-322. Set 3 manholes.'" },
  { key: "delays",             label: "What slowed progress or constrained you?",
    hint: "Weather, utility conflicts, deliveries, inspections, crew shortages. Leave blank if nothing slowed you." },
  { key: "inspections",        label: "What inspections or tests occurred?",
    hint: "Who inspected · what was tested · pass / fail / note. e.g. 'City inspector witnessed manhole #4 set — passed.'" },
  { key: "materials_received", label: "What materials or deliveries arrived?",
    hint: "Supplier · material · quantity · ticket #. e.g. '5 loads crushed concrete from Vulcan @ 9:30am.'" },
  { key: "follow_ups",         label: "What needs follow-up tomorrow or this week?",
    hint: "Issues, approvals needed, safety items, pending decisions." },
  { key: "tomorrow_plan",      label: "What's planned for tomorrow?",
    hint: "Crews · locations · production goals." },
];

export function NarrativeWorkflow({ value = {}, onChange, testIdPrefix = "narrative" }) {
  const set = (k, v) => onChange?.({ ...value, [k]: v });
  return (
    <div className="grid gap-4">
      <div className="text-sm text-slate-600">
        Walk through the day. Leave any prompt blank if it doesn&apos;t apply — but the more you tell us, the easier this report is to read six months from now.
      </div>
      {PROMPTS.map((p) => (
        <div key={p.key} className="grid gap-1.5">
          <Label className="text-sm font-medium text-slate-900" htmlFor={`${testIdPrefix}-${p.key}`}>
            {p.label}
          </Label>
          <Textarea
            id={`${testIdPrefix}-${p.key}`}
            data-testid={`${testIdPrefix}-${p.key}`}
            value={value[p.key] || ""}
            onChange={(e) => set(p.key, e.target.value)}
            placeholder={p.hint}
            rows={2}
            className="resize-y"
          />
          <div className="text-xs text-slate-500">{p.hint}</div>
        </div>
      ))}
    </div>
  );
}

export default NarrativeWorkflow;
