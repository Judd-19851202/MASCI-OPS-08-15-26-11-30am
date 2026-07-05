import React from "react";
import { SectionCard } from "../_ui";

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

export default function ActivityCardsSection({ draft, setDraft }) {
  const cards = draft.activity_cards || [];
  const add = () => setDraft((d) => ({ ...d, activity_cards: [...(d.activity_cards || []), EMPTY_CARD()] }));
  const update = (id, patch) =>
    setDraft((d) => ({
      ...d,
      activity_cards: (d.activity_cards || []).map((c) => (c.id === id ? { ...c, ...patch } : c)),
    }));
  const remove = (id) => setDraft((d) => ({ ...d, activity_cards: (d.activity_cards || []).filter((c) => c.id !== id) }));

  return (
    <SectionCard id="activity-cards" title="4 · Activity Cards" badge={`${cards.length} cards`}>
      <p className="text-sm opacity-70">
        One card per work item. Enter area · activity · quantity · unit · crew ·
        equipment · photos. Notes optional. Replaces the freeform activities log.
      </p>

      <div className="space-y-3">
        {cards.length === 0 ? (
          <div className="rounded-md border border-dashed border-neutral-700 bg-neutral-950/40 px-4 py-6 text-sm opacity-75" data-testid="dr-v2-activity-empty">
            No activity cards yet. Add one for each work item completed today.
          </div>
        ) : (
          cards.map((card, idx) => (
            <div
              key={card.id}
              className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-4 space-y-3"
              data-testid={`dr-v2-activity-card-${idx}`}
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <label className="text-xs opacity-70 col-span-2">
                  Work area
                  <input
                    className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
                    value={card.area}
                    onChange={(e) => update(card.id, { area: e.target.value })}
                    data-testid={`dr-v2-activity-area-${idx}`}
                    placeholder="e.g. Parent Loop East"
                  />
                </label>
                <label className="text-xs opacity-70 col-span-2">
                  Activity
                  <input
                    className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
                    value={card.activity_type}
                    onChange={(e) => update(card.id, { activity_type: e.target.value })}
                    data-testid={`dr-v2-activity-type-${idx}`}
                    placeholder="e.g. Base grading"
                  />
                </label>
                <label className="text-xs opacity-70">
                  Quantity
                  <input
                    className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
                    value={card.quantity}
                    onChange={(e) => update(card.id, { quantity: e.target.value })}
                    data-testid={`dr-v2-activity-qty-${idx}`}
                    placeholder="0"
                  />
                </label>
                <label className="text-xs opacity-70">
                  Unit
                  <select
                    className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
                    value={card.unit}
                    onChange={(e) => update(card.id, { unit: e.target.value })}
                    data-testid={`dr-v2-activity-unit-${idx}`}
                  >
                    {["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"].map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </label>
                <label className="text-xs opacity-70 col-span-2">
                  Status
                  <select
                    className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
                    value={card.status}
                    onChange={(e) => update(card.id, { status: e.target.value })}
                    data-testid={`dr-v2-activity-status-${idx}`}
                  >
                    {[
                      ["on-track", "On track"],
                      ["ahead", "Ahead"],
                      ["delayed", "Delayed"],
                      ["blocked", "Blocked"],
                      ["complete", "Complete"],
                    ].map(([v, l]) => (
                      <option key={v} value={v}>{l}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="flex justify-end">
                <button
                  className="text-xs px-2 py-1 rounded-md border border-neutral-700 hover:border-red-500 hover:text-red-400 transition"
                  onClick={() => remove(card.id)}
                  data-testid={`dr-v2-activity-remove-${idx}`}
                >
                  Remove
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <button
        className="text-sm rounded-md bg-red-700 hover:bg-red-600 px-3 py-2"
        onClick={add}
        data-testid="dr-v2-activity-add"
      >
        + Add Activity Card
      </button>
    </SectionCard>
  );
}
