import React from "react";
import { Section } from "@/components/Section";
import { SupplierCombo } from "@/components/SupplierCombo";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { X } from "lucide-react";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

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
const SUBCON_LIKE = new Set(["subcontractor_issue", "material_delay"]);

/**
 * DR-ROI-001F-REPAIR · Constraint Chips — chips + structured follow-up
 * form (duration, responsible party, impact, notes). Subcontractor /
 * vendor field uses the platform SupplierCombo. Feeds ODS delay facts.
 */
export default function ConstraintChipsSection({ draft, setDraft }) {
  const { t } = useDrV2Lang();
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
            duration_minutes: "",
            responsible_party: "",
            impact: "",
          },
        ],
      }));
    }
  };
  const update = (id, patch) =>
    setDraft((d) => ({
      ...d,
      constraint_cards: (d.constraint_cards || []).map((c) =>
        c.id === id ? { ...c, ...patch } : c,
      ),
    }));
  const remove = (id) =>
    setDraft((d) => ({
      ...d,
      constraint_cards: (d.constraint_cards || []).filter((c) => c.id !== id),
    }));

  return (
    <Section
      number="05"
      title={t("s05.title")}
      testId="dr-v2-section-constraint-chips"
    >
      <p className="text-sm text-slate-600 -mt-2 mb-2">
        {t("s05.desc")}
      </p>
      <div className="flex flex-wrap gap-2" data-testid="dr-v2-constraint-chips">
        {CATEGORIES.map(([key, _label]) => {
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
              {t(`s05.cat.${key}`)}
            </button>
          );
        })}
      </div>

      {chips.length > 0 ? (
        <div className="space-y-3 mt-3">
          {chips.map((c, idx) => (
            <div
              key={c.id}
              className="rounded-md border border-slate-200 bg-white p-3 sm:p-4 space-y-3"
              data-testid={`dr-v2-constraint-card-${idx}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  {CATEGORIES.find((x) => x[0] === c.category)?.[1] || c.category}
                </span>
                <button
                  type="button"
                  onClick={() => remove(c.id)}
                  className="text-slate-500 hover:text-red-600 text-xs font-semibold"
                  data-testid={`dr-v2-constraint-remove-${idx}`}
                >
                  <X className="w-4 h-4 inline mr-1" /> Remove
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                <div className="lg:col-span-2">
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    What happened
                  </Label>
                  <Textarea
                    value={c.what_happened || ""}
                    onChange={(e) => update(c.id, { what_happened: e.target.value })}
                    className="min-h-[60px] text-base border-2 border-slate-300"
                    data-testid={`dr-v2-constraint-what-${idx}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Duration (minutes)
                  </Label>
                  <Input
                    type="number"
                    inputMode="numeric"
                    min="0"
                    step="15"
                    value={c.duration_minutes || ""}
                    onChange={(e) => update(c.id, { duration_minutes: e.target.value })}
                    className={inputCls}
                    data-testid={`dr-v2-constraint-duration-${idx}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Responsible party
                  </Label>
                  {SUBCON_LIKE.has(c.category) ? (
                    <SupplierCombo
                      value={c.responsible_party || ""}
                      onChange={(v) => update(c.id, { responsible_party: v })}
                      testId={`dr-v2-constraint-party-${idx}`}
                    />
                  ) : (
                    <Input
                      value={c.responsible_party || ""}
                      onChange={(e) => update(c.id, { responsible_party: e.target.value })}
                      className={inputCls}
                      placeholder="Who owns the resolution"
                      data-testid={`dr-v2-constraint-party-${idx}`}
                    />
                  )}
                </div>
                <div className="lg:col-span-2">
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Impact / needed action
                  </Label>
                  <Textarea
                    value={c.impact || ""}
                    onChange={(e) => update(c.id, { impact: e.target.value })}
                    className="min-h-[60px] text-base border-2 border-slate-300"
                    data-testid={`dr-v2-constraint-impact-${idx}`}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </Section>
  );
}
