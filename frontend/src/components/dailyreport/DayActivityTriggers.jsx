// Phase 10D.2 · Day Activity Triggers
//
// "What happened today?" — a single trigger panel above the optional
// collapse cards. Each YES/NO answer either reveals or hides the
// corresponding CollapseCard. NO → the card is hidden completely;
// foremen don't have to scroll through paperwork that doesn't apply.
//
// Mirrors the Excavation Form Section 6b pattern (yes/no chip then
// expand). Reuses existing data fields where they already exist:
//   • weather_impact, schedule_delays, safety_incidents_today,
//     injuries_reported, excavation_activity_today.
// Adds five new derived-only triggers (NOT persisted to the backend —
// they live in component state so existing schema is untouched):
//   • subs_today, visitors_today, equipment_today, deliveries_today,
//     production_today.
//
// If a list already has rows, the answer auto-locks to "Yes" so prior
// data is never accidentally hidden.
import React from "react";
import { CheckCircle2, MinusCircle, ChevronDown } from "lucide-react";
import { useT } from "@/lib/i18n";

const TRIGGERS = [
  { key: "subs_today",         label: "Subcontractors on site today?",        listKey: "subcontractors" },
  { key: "visitors_today",     label: "Visitors today?",                       listKey: "visitors" },
  { key: "equipment_today",    label: "Equipment used today?",                 listKey: "equipment" },
  { key: "deliveries_today",   label: "Material deliveries today?",            listKey: "material_deliveries" },
  { key: "production_today",   label: "Production quantities to report?",      listKey: "production" },
  { key: "schedule_delays",    label: "Delays or extra work today?",           dataKey: "schedule_delays",       listKey: "constraints" },
  { key: "weather_impact",     label: "Weather impact today?",                 dataKey: "weather_impact" },
  { key: "safety_incidents_today", label: "Incident or near miss today?",       dataKey: "safety_incidents_today" },
  { key: "injuries_reported",  label: "Injury today?",                          dataKey: "injuries_reported" },
  { key: "excavation_activity_today", label: "Excavation / trenching today?",   dataKey: "excavation_activity_today" },
];

export default function DayActivityTriggers({ data, triggers, setTriggers, setData, testId = "dr-day-triggers" }) {
  const { t } = useT();
  const setOne = (key, dataKey, value) => {
    if (dataKey) setData((p) => ({ ...p, [dataKey]: value }));
    setTriggers((p) => ({ ...p, [key]: value }));
  };

  return (
    <div className="bg-white border-2 border-slate-200 rounded-md p-3" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1.5 flex items-center gap-2">
        <ChevronDown className="w-3.5 h-3.5" />
        {t("Today's Activity — quick scan")}
      </div>
      <div className="text-xs text-slate-600 mb-2">
        {t("Tap Yes to open a section. Anything you say No to stays hidden — no paperwork you don't need.")}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
        {TRIGGERS.map(({ key, label, dataKey, listKey }) => {
          const persistedValue = dataKey ? data[dataKey] : undefined;
          const tValue = triggers[key];
          const hasRows = listKey ? (data[listKey] || []).length > 0 : false;
          // Auto-lock YES when persisted "Yes" or list already populated
          const effective = persistedValue === "Yes" || hasRows
            ? "Yes"
            : (tValue ?? persistedValue ?? "No");
          const locked = hasRows;

          return (
            <div key={key} className="flex items-center justify-between gap-2 bg-slate-50 border border-slate-200 rounded px-2 py-1.5" data-testid={`${testId}-row-${key}`}>
              <div className="flex-1 min-w-0 text-xs text-slate-800 truncate">{t(label)}</div>
              <div className="flex gap-1">
                {["Yes", "No"].map((v) => {
                  const active = effective === v;
                  const Icon = v === "Yes" ? CheckCircle2 : MinusCircle;
                  return (
                    <button
                      key={v}
                      type="button"
                      disabled={locked && v === "No"}
                      onClick={() => setOne(key, dataKey, v)}
                      className={"inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] font-bold uppercase tracking-[0.08em] transition " +
                        (active
                          ? (v === "Yes" ? "bg-emerald-600 border-emerald-700 text-white" : "bg-slate-700 border-slate-800 text-white")
                          : "bg-white border-slate-300 text-slate-700 hover:border-cyan-500") +
                        (locked && v === "No" ? " opacity-50 cursor-not-allowed" : "")}
                      data-testid={`${testId}-${key}-${v.toLowerCase()}`}
                    >
                      <Icon className="w-3 h-3" /> {t(v)}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Helper: returns "Yes" / "No" effective value used by the parent form to
// decide whether to render each CollapseCard. Mirrors the rule used
// inside the component (list-with-rows auto-locks to Yes).
export function effectiveTrigger(triggerState, data, key) {
  const def = TRIGGERS.find((t) => t.key === key);
  if (!def) return "No";
  if (def.dataKey && data[def.dataKey] === "Yes") return "Yes";
  if (def.listKey && (data[def.listKey] || []).length > 0) return "Yes";
  return triggerState[key] || data[def.dataKey] || "No";
}
