import React from "react";
import { SectionCard, StatusChip } from "../_ui";

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
      setDraft((d) => ({
        ...d,
        constraint_cards: (d.constraint_cards || []).filter(
          (c) => c.category !== cat,
        ),
      }));
    } else {
      setDraft((d) => ({
        ...d,
        constraint_cards: [
          ...(d.constraint_cards || []),
          {
            id: `cst_${Math.random().toString(36).slice(2, 10)}`,
            category: cat,
            what_happened: "",
            duration_minutes: 0,
            responsible_party: "",
          },
        ],
      }));
    }
  };

  return (
    <SectionCard
      id="constraint-chips"
      title="5 · Delays · Constraints · Extra Work"
      badge={`${chips.length} selected`}
      description="Tap what happened today. Each selection opens a structured follow-up card with duration, responsible party, impact, and optional photos."
    >
      <div
        className="flex flex-wrap gap-2"
        data-testid="dr-v2-constraint-chips"
      >
        {CATEGORIES.map(([key, label]) => {
          const active = activeIds.has(key);
          return (
            <button
              key={key}
              type="button"
              onClick={() => toggle(key)}
              className={`text-xs rounded-full px-3 py-1.5 border-2 font-semibold transition ${
                active
                  ? "border-red-600 bg-red-50 text-red-800"
                  : "border-slate-300 bg-white text-slate-700 hover:border-slate-500"
              }`}
              data-testid={`dr-v2-constraint-chip-${key}`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {chips.length > 0 ? (
        <div className="space-y-2 mt-2">
          {chips.map((c, idx) => (
            <div
              key={c.id}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              data-testid={`dr-v2-constraint-card-${idx}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
                  {CATEGORIES.find((x) => x[0] === c.category)?.[1] || c.category}
                </span>
                <StatusChip tone="amber">follow-up pending</StatusChip>
              </div>
              <p className="text-xs text-slate-600">
                Duration, responsible party, impact, and photos land with the
                follow-up form in the next release.
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </SectionCard>
  );
}
