// Phase 10D.2 (Path A) · Day Activity Triggers — single compact row.
//
// "What happened today?" — a 10-checkbox row. Tap to add. Otherwise the
// related section stays hidden. Mirrors persisted Yes/No fields where
// they exist (`weather_impact`, `schedule_delays`, `safety_incidents_today`,
// `injuries_reported`, `excavation_activity_today`). Adds five derived
// triggers (subs_today, visitors_today, equipment_today, deliveries_today,
// production_today) that live in local component state — schema untouched.
//
// No coaching text. No paragraphs. Just chips.
import React from "react";
import { useT } from "@/lib/i18n";

const TRIGGERS = [
  { key: "normal",                    label: "Normal Production",  dataKey: null },
  { key: "subs_today",                label: "Subcontractors",      listKey: "subcontractors" },
  { key: "visitors_today",            label: "Visitors",            listKey: "visitors" },
  { key: "equipment_today",           label: "Equipment",           listKey: "equipment" },
  { key: "deliveries_today",          label: "Deliveries",          listKey: "material_deliveries" },
  { key: "production_today",          label: "Production",          listKey: "production" },
  { key: "schedule_delays",           label: "Delays / Extra",      dataKey: "schedule_delays",       listKey: "constraints" },
  { key: "weather_impact",            label: "Weather",             dataKey: "weather_impact" },
  { key: "safety_incidents_today",    label: "Incident",            dataKey: "safety_incidents_today" },
  { key: "injuries_reported",         label: "Injury",              dataKey: "injuries_reported" },
  { key: "excavation_activity_today", label: "Excavation",          dataKey: "excavation_activity_today" },
];

export default function DayActivityTriggers({ data, triggers, setTriggers, setData, testId = "dr-day-triggers" }) {
  const { t } = useT();

  const isOn = (def) => {
    const persisted = def.dataKey ? data[def.dataKey] : undefined;
    if (persisted === "Yes") return true;
    if (def.listKey && (data[def.listKey] || []).length > 0) return true;
    return !!triggers[def.key];
  };

  const toggle = (def) => {
    const next = !isOn(def);
    if (def.dataKey) setData((p) => ({ ...p, [def.dataKey]: next ? "Yes" : "No" }));
    setTriggers((p) => ({ ...p, [def.key]: next }));
  };

  return (
    <div data-testid={testId}>
      <div className="font-bold text-sm text-slate-900 mb-2">{t("What happened today?")}</div>
      <div className="flex flex-wrap gap-1.5" data-testid={`${testId}-chips`}>
        {TRIGGERS.map((def) => {
          const on = isOn(def);
          const isWarn = on && ["safety_incidents_today", "injuries_reported"].includes(def.key);
          const cls = on
            ? (isWarn
                ? "bg-red-700 border-red-800 text-white"
                : "bg-cyan-700 border-cyan-800 text-white")
            : "bg-white border-slate-300 text-slate-700 hover:border-cyan-500";
          return (
            <button
              key={def.key}
              type="button"
              onClick={() => toggle(def)}
              className={"px-3 py-1.5 rounded-full border text-xs font-bold uppercase tracking-[0.06em] transition " + cls}
              data-testid={`${testId}-${def.key}`}
              aria-pressed={on}
            >
              {on ? "✓ " : "+ "}{t(def.label)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Helper: returns boolean "was this trigger on" for the parent form to
// decide whether to render each CollapseCard.
export function isTriggerOn(triggerState, data, key) {
  const def = TRIGGERS.find((d) => d.key === key);
  if (!def) return false;
  if (def.dataKey && data[def.dataKey] === "Yes") return true;
  if (def.listKey && (data[def.listKey] || []).length > 0) return true;
  return !!triggerState[key];
}
