import React from "react";
import { Section } from "@/components/Section";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Plus, X } from "lucide-react";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

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

const UNITS = ["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"];
const STATUS = [
  ["on-track", "On track"],
  ["ahead", "Ahead"],
  ["delayed", "Delayed"],
  ["blocked", "Blocked"],
  ["complete", "Complete"],
];

/**
 * DR-ROI-001F-REPAIR · Activity Cards — one card per work item, wired
 * with the V1 Section grammar + platform inputs. Cost-code aware; feeds
 * ODS production facts on submit (unchanged pipeline).
 */
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
    <Section number="04" title="Activity Cards" testId="dr-v2-section-activity-cards">
      <p className="text-sm text-slate-600 -mt-2 mb-2">
        One card per work item. Feeds ODS production facts on submit.
      </p>
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
              className="rounded-md border border-slate-200 bg-white p-3 sm:p-4 space-y-3"
              data-testid={`dr-v2-activity-card-${idx}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Activity {idx + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => remove(card.id)}
                  className="text-slate-500 hover:text-red-600 h-9"
                  data-testid={`dr-v2-activity-remove-${idx}`}
                >
                  <X className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Work area
                  </Label>
                  <Input
                    value={card.area}
                    onChange={(e) => update(card.id, { area: e.target.value })}
                    className={inputCls}
                    placeholder="e.g. Parent Loop East"
                    data-testid={`dr-v2-activity-area-${idx}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Activity
                  </Label>
                  <Input
                    value={card.activity_type}
                    onChange={(e) =>
                      update(card.id, { activity_type: e.target.value })
                    }
                    className={inputCls}
                    placeholder="e.g. Base grading"
                    data-testid={`dr-v2-activity-activity-${idx}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Quantity
                  </Label>
                  <Input
                    type="number"
                    inputMode="decimal"
                    value={card.quantity}
                    onChange={(e) =>
                      update(card.id, { quantity: e.target.value })
                    }
                    className={inputCls}
                    placeholder="0"
                    data-testid={`dr-v2-activity-quantity-${idx}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Unit
                  </Label>
                  <select
                    value={card.unit}
                    onChange={(e) => update(card.id, { unit: e.target.value })}
                    className={inputCls + " w-full rounded-md bg-white"}
                    data-testid={`dr-v2-activity-unit-${idx}`}
                  >
                    {UNITS.map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Status
                  </Label>
                  <select
                    value={card.status}
                    onChange={(e) =>
                      update(card.id, { status: e.target.value })
                    }
                    className={inputCls + " w-full rounded-md bg-white"}
                    data-testid={`dr-v2-activity-status-${idx}`}
                  >
                    {STATUS.map(([v, l]) => (
                      <option key={v} value={v}>{l}</option>
                    ))}
                  </select>
                </div>
                <div className="lg:col-span-2">
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Notes (optional)
                  </Label>
                  <Textarea
                    value={card.notes || ""}
                    onChange={(e) => update(card.id, { notes: e.target.value })}
                    className="min-h-[60px] text-base border-2 border-slate-300"
                    placeholder="Anything the PM should know about this activity"
                    data-testid={`dr-v2-activity-notes-${idx}`}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={add}
        className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm mt-3"
        data-testid="dr-v2-activity-add"
      >
        <Plus className="w-4 h-4 mr-2" /> Add Activity Card
      </Button>
    </Section>
  );
}
