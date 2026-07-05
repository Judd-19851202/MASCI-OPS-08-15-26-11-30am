import React from "react";
import { SectionCard } from "../_ui";

const CATEGORIES = [
  ["weather", "Weather"],
  ["equipment", "Equipment"],
  ["utility_conflict", "Utility conflict"],
  ["inspection_delay", "Inspection delay"],
  ["material_delay", "Material delay"],
  ["survey_model_issue", "Survey / model"],
  ["subcontractor_issue", "Subcontractor"],
  ["owner_ceo_decision", "Owner / CEI decision"],
  ["traffic_control", "Traffic control"],
  ["manpower", "Manpower"],
  ["extra_work", "Extra work"],
  ["safety_stop", "Safety stop"],
  ["quality_rework", "Quality / rework"],
  ["other", "Other"],
];

export default function ConstraintChipsSection({ draft, setDraft }) {
  const chips = draft.constraint_cards || [];
  const activeIds = new Set(chips.map((c) => c.category));

  const toggle = (cat) => {
    if (activeIds.has(cat)) {
      setDraft((d) => ({ ...d, constraint_cards: (d.constraint_cards || []).filter((c) => c.category !== cat) }));
    } else {
      setDraft((d) => ({
        ...d,
        constraint_cards: [
          ...(d.constraint_cards || []),
          { id: `cst_${Math.random().toString(36).slice(2, 10)}`, category: cat, what_happened: "", duration_minutes: 0, responsible_party: "" },
        ],
      }));
    }
  };

  return (
    <SectionCard id="constraint-chips" title="5 · Delays · Constraints · Extra Work" badge={`${chips.length} selected`}>
      <p className="text-sm opacity-70">
        Tap what happened. Each chip opens a structured follow-up card with
        duration · responsible party · impact · optional photos.
      </p>
      <div className="flex flex-wrap gap-2" data-testid="dr-v2-constraint-chips">
        {CATEGORIES.map(([key, label]) => (
          <button
            key={key}
            onClick={() => toggle(key)}
            className={`text-xs rounded-full px-3 py-1.5 border transition ${
              activeIds.has(key)
                ? "border-red-500 bg-red-950/50 text-red-200"
                : "border-neutral-700 opacity-70 hover:opacity-100 hover:border-neutral-500"
            }`}
            data-testid={`dr-v2-constraint-chip-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {chips.length > 0 ? (
        <div className="space-y-3">
          {chips.map((c, idx) => (
            <div key={c.id} className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-4" data-testid={`dr-v2-constraint-card-${idx}`}>
              <div className="text-xs uppercase tracking-widest opacity-60 mb-2">
                {CATEGORIES.find((x) => x[0] === c.category)?.[1] || c.category}
              </div>
              <div className="text-xs opacity-60">Follow-up form (duration, responsible party, impact, photos) lands in Track C.</div>
            </div>
          ))}
        </div>
      ) : null}
    </SectionCard>
  );
}
