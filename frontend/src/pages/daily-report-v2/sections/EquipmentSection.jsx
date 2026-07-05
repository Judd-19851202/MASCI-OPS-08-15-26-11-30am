import React from "react";
import { Section } from "@/components/Section";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { EquipmentCombo } from "@/components/EquipmentCombo";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { Plus, X } from "lucide-react";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/**
 * DR-ROI-001F-REPAIR · Equipment — wired to the platform EquipmentCombo
 * fed by GET /api/equipment-master. Operators come from EmployeeCombo.
 */
export default function EquipmentSection({ draft, setDraft }) {
  const rows = draft.equipment_used || [];
  const update = (i, patch) =>
    setDraft((d) => ({
      ...d,
      equipment_used: (d.equipment_used || []).map((r, idx) =>
        idx === i ? { ...r, ...patch } : r,
      ),
    }));
  const add = () =>
    setDraft((d) => ({
      ...d,
      equipment_used: [
        ...(d.equipment_used || []),
        { unit: "", hours: "", operator: "", status: "in-service" },
      ],
    }));
  const remove = (i) =>
    setDraft((d) => ({
      ...d,
      equipment_used: (d.equipment_used || []).filter((_, idx) => idx !== i),
    }));

  return (
    <Section
      number="03"
      title="Equipment on Site"
      testId="dr-v2-section-equipment"
    >
      <p className="text-sm text-slate-600 -mt-2 mb-2">
        Equipment master is HR/Shop-linked. Idle / breakdown flags feed the
        Pre-Op + shop workflows unchanged.
      </p>
      <div className="space-y-3">
        {rows.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600" data-testid="dr-v2-equip-empty">
            No equipment yet. Add units used today.
          </div>
        ) : (
          rows.map((row, i) => (
            <div
              key={i}
              className="rounded-md border border-slate-200 bg-white p-3 sm:p-4 space-y-2"
              data-testid={`dr-v2-equip-row-${i}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Equipment {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => remove(i)}
                  className="text-slate-500 hover:text-red-600 h-9"
                  data-testid={`dr-v2-equip-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Unit
                  </Label>
                  <EquipmentCombo
                    value={row.unit || ""}
                    onChange={(v) => update(i, { unit: v })}
                    testId={`dr-v2-equip-unit-${i}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Operator
                  </Label>
                  <EmployeeCombo
                    value={row.operator || ""}
                    onChange={(v) => update(i, { operator: v })}
                    testId={`dr-v2-equip-operator-${i}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Hours
                  </Label>
                  <Input
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.25"
                    value={row.hours || ""}
                    onChange={(e) => update(i, { hours: e.target.value })}
                    className={inputCls}
                    placeholder="8"
                    data-testid={`dr-v2-equip-hours-${i}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Status
                  </Label>
                  <select
                    value={row.status || "in-service"}
                    onChange={(e) => update(i, { status: e.target.value })}
                    className={inputCls + " w-full rounded-md bg-white"}
                    data-testid={`dr-v2-equip-status-${i}`}
                  >
                    <option value="in-service">In service</option>
                    <option value="idle">Idle</option>
                    <option value="breakdown">Breakdown</option>
                    <option value="off-site">Off site</option>
                  </select>
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
        data-testid="dr-v2-equip-add"
      >
        <Plus className="w-4 h-4 mr-2" /> Add Equipment
      </Button>
    </Section>
  );
}
