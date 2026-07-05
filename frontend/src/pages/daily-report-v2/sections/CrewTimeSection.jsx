import React from "react";
import { Section } from "@/components/Section";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { Plus, X } from "lucide-react";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/**
 * DR-ROI-001F-REPAIR · Crew Time — wired to the HR-gospel EmployeeCombo.
 * Preserves the V1 masci_crews[] schema {employee_name, hours}.
 */
export default function CrewTimeSection({ draft, setDraft }) {
  const rows = draft.masci_crews || [];
  const update = (i, patch) =>
    setDraft((d) => ({
      ...d,
      masci_crews: (d.masci_crews || []).map((r, idx) =>
        idx === i ? { ...r, ...patch } : r,
      ),
    }));
  const add = () =>
    setDraft((d) => ({
      ...d,
      masci_crews: [
        ...(d.masci_crews || []),
        { employee_name: "", hours: "", role: "" },
      ],
    }));
  const remove = (i) =>
    setDraft((d) => ({
      ...d,
      masci_crews: (d.masci_crews || []).filter((_, idx) => idx !== i),
    }));

  return (
    <Section
      number="02"
      title="MASCI Crews on Site"
      testId="dr-v2-section-crew-time"
    >
      <p className="text-sm text-slate-600 -mt-2 mb-2">
        HR-linked. Employees come from the canonical roster · hours flow to
        payroll and time verification as they do today.
      </p>
      <div className="space-y-3">
        {rows.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600" data-testid="dr-v2-crewtime-empty">
            No crew yet. Add employees below.
          </div>
        ) : (
          rows.map((row, i) => (
            <div
              key={i}
              className="rounded-md border border-slate-200 bg-white p-3 sm:p-4 space-y-2"
              data-testid={`dr-v2-crew-row-${i}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Crew Member {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => remove(i)}
                  className="text-slate-500 hover:text-red-600 h-9"
                  data-testid={`dr-v2-crew-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="lg:col-span-2">
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Employee
                  </Label>
                  <EmployeeCombo
                    value={row.employee_name || ""}
                    onChange={(v) => update(i, { employee_name: v })}
                    testId={`dr-v2-crew-employee-${i}`}
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
                    data-testid={`dr-v2-crew-hours-${i}`}
                  />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                    Role / cost code
                  </Label>
                  <Input
                    value={row.role || ""}
                    onChange={(e) => update(i, { role: e.target.value })}
                    className={inputCls}
                    placeholder="Optional"
                    data-testid={`dr-v2-crew-role-${i}`}
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
        data-testid="dr-v2-crew-add"
      >
        <Plus className="w-4 h-4 mr-2" /> Add Crew Member
      </Button>
    </Section>
  );
}
