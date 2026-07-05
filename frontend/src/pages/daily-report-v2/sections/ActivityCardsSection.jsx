import React from "react";
import {
  SectionCard, FieldLabel, inputCls, selectCls, addItemBtn, ghostBtn,
} from "../_ui";
import { Plus, X } from "lucide-react";

const EMPTY_CARD = () => ({
  id: `act_${Math.random().toString(36).slice(2, 10)}`,
  area: "",
  activity_type: "",
  quantity: "",
  unit: "LF",
  crew_ids: [],
  equipment_ids: [],
  status: "on-track",
  photo_ids: [],
  notes: "",
});

const STATUS_OPTIONS = [
  ["on-track", "On track"],
  ["ahead", "Ahead"],
  ["delayed", "Delayed"],
  ["blocked", "Blocked"],
  ["complete", "Complete"],
];

const UNITS = ["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"];

export default function ActivityCardsSection({ draft, setDraft }) {
  const cards = draft.activity_cards || [];

  const add = () =>
    setDraft((d) => ({
      ...d,
      activity_cards: [...(d.activity_cards || []), EMPTY_CARD()],
    }));

  const update = (id, patch) =>
    setDraft((d) => ({
      ...d,
      activity_cards: (d.activity_cards || []).map((c) =>
        c.id === id ? { ...c, ...patch } : c,
      ),
    }));

  const remove = (id) =>
    setDraft((d) => ({
      ...d,
      activity_cards: (d.activity_cards || []).filter((c) => c.id !== id),
    }));

  return (
    <SectionCard
      id="activity-cards"
      title="4 · Activity Cards"
      badge={`${cards.length} card${cards.length === 1 ? "" : "s"}`}
      description="One card per work item. Enter area, activity, quantity, unit, and status. Add crew, equipment, and photos in the sections below."
    >
      <div className="space-y-3">
        {cards.length === 0 ? (
          <div
            className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600"
            data-testid="dr-v2-activity-empty"
          >
            No activity cards yet. Add one for each work item completed today.
          </div>
        ) : (
          cards.map((card, idx) => (
            <div
              key={card.id}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3"
              data-testid={`dr-v2-activity-card-${idx}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
                  Activity {idx + 1}
                </span>
                <button
                  type="button"
                  className={ghostBtn}
                  onClick={() => remove(card.id)}
                  data-testid={`dr-v2-activity-remove-${idx}`}
                >
                  <X className="w-4 h-4" /> Remove
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="sm:col-span-2 space-y-1">
                  <FieldLabel>Work area</FieldLabel>
                  <input
                    className={inputCls}
                    value={card.area}
                    onChange={(e) => update(card.id, { area: e.target.value })}
                    placeholder="e.g. Parent Loop East"
                    data-testid={`dr-v2-activity-area-${idx}`}
                  />
                </div>
                <div className="sm:col-span-2 space-y-1">
                  <FieldLabel>Activity</FieldLabel>
                  <input
                    className={inputCls}
                    value={card.activity_type}
                    onChange={(e) =>
                      update(card.id, { activity_type: e.target.value })
                    }
                    placeholder="e.g. Base grading"
                    data-testid={`dr-v2-activity-type-${idx}`}
                  />
                </div>

                <div className="space-y-1">
                  <FieldLabel>Quantity</FieldLabel>
                  <input
                    className={inputCls}
                    value={card.quantity}
                    onChange={(e) =>
                      update(card.id, { quantity: e.target.value })
                    }
                    placeholder="0"
                    inputMode="decimal"
                    data-testid={`dr-v2-activity-qty-${idx}`}
                  />
                </div>
                <div className="space-y-1">
                  <FieldLabel>Unit</FieldLabel>
                  <select
                    className={selectCls}
                    value={card.unit}
                    onChange={(e) => update(card.id, { unit: e.target.value })}
                    data-testid={`dr-v2-activity-unit-${idx}`}
                  >
                    {UNITS.map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2 space-y-1">
                  <FieldLabel>Status</FieldLabel>
                  <select
                    className={selectCls}
                    value={card.status}
                    onChange={(e) =>
                      update(card.id, { status: e.target.value })
                    }
                    data-testid={`dr-v2-activity-status-${idx}`}
                  >
                    {STATUS_OPTIONS.map(([v, l]) => (
                      <option key={v} value={v}>{l}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <button
        type="button"
        className={addItemBtn}
        onClick={add}
        data-testid="dr-v2-activity-add"
      >
        <Plus className="w-4 h-4 mr-2 inline" /> Add Activity Card
      </button>
    </SectionCard>
  );
}
