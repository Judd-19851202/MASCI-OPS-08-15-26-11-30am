// TRACK 23.1 · V3 Sections 02–08 · single-file module.
//
// Each section is a small, focused presentational component that
// composes existing shared primitives (EmployeeCombo, EquipmentCombo,
// PhotoUpload, DailySummaryAssist). Same payload keys as V1.
import React, { useMemo } from "react";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { EquipmentCombo } from "@/components/EquipmentCombo";
import { SupplierCombo } from "@/components/SupplierCombo";
import { PhotoUpload } from "@/components/PhotoUpload";
import { SignaturePad } from "@/components/SignaturePad";
import DailySummaryAssist from "@/components/daily-report/DailySummaryAssist";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Plus, Trash2, ShieldAlert, TrafficCone, Clock, Camera, Users, Wrench,
  Truck, AlertTriangle, ExternalLink,
} from "lucide-react";
import { computeCrewHours, grossNetPreview, sumCrewHours, sumEquipmentHours }
  from "@/lib/crewHoursMath";
import { Link } from "react-router-dom";

// ── Shared section shell ──────────────────────────────────────────
export function SectionShell({ step, title, testId, right = null, children }) {
  return (
    <section
      data-testid={testId}
      className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
            {step}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">{title}</h2>
        </div>
        {right}
      </header>
      {children}
    </section>
  );
}

const rowBtn =
  "inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100";

// ── Section 02 · Crew + Equipment ─────────────────────────────────
export function SectionCrewEquipment({ data, patch, costCodes }) {
  const crews = data.masci_crews || [];
  const equipment = data.equipment || [];
  const subs = data.subcontractors || [];
  const hasCodes = (costCodes?.length || 0) > 0;

  // ── Live totals (visible summary strip) ─────────────────────────
  const crewTotals = useMemo(() => {
    const totalHours = sumCrewHours(crews);
    const totalLunch = (crews || []).reduce(
      (a, c) => a + (Number(c?.lunch_minutes) || 0), 0,
    );
    const byCode = {};
    (crews || []).forEach((c) => {
      const code = (c?.cost_code || "").trim();
      if (!code) return;
      byCode[code] = (byCode[code] || 0) + (Number(c?.hours) || 0);
    });
    return { count: crews.length, totalHours, totalLunch, byCode };
  }, [crews]);

  const equipTotals = useMemo(() => {
    const run = sumEquipmentHours(equipment, "hours_used");
    const idle = sumEquipmentHours(equipment, "idle_hours");
    const total = run + idle;
    const util = total > 0 ? (run / total) * 100 : null;
    const withIssues = (equipment || []).filter(
      (e) => (e?.notes || "").trim().length > 0,
    ).length;
    return { count: equipment.length, run, idle, total, util, withIssues };
  }, [equipment]);

  const subsTotals = useMemo(() => {
    const totalHours = (subs || []).reduce(
      (a, s) => a + (Number(s?.hours) || 0), 0,
    );
    const totalCount = (subs || []).reduce(
      (a, s) => a + (Number(s?.count) || 0), 0,
    );
    return { rows: subs.length, totalHours, totalCount };
  }, [subs]);

  // ── Row helpers ─────────────────────────────────────────────────
  const updateCrew = (i, delta) => {
    const next = crews.slice();
    const merged = { ...crews[i], ...delta };
    // Auto-compute hours from start/stop/lunch. Preserves explicit
    // user overrides only when they typed the hours field themselves
    // AFTER blanking start/stop (V1 parity: computed hours always win
    // when start+stop are present).
    if (
      merged.start_time || merged.stop_time || merged.lunch_minutes !== undefined
    ) {
      const auto = computeCrewHours(
        merged.start_time,
        merged.stop_time,
        merged.lunch_minutes,
      );
      if (auto !== "") merged.hours = parseFloat(auto) || 0;
    }
    next[i] = merged;
    patch({ masci_crews: next });
  };

  return (
    <SectionShell
      step="Step 2 · Who was there?"
      title="Crew, Equipment &amp; Subcontractors"
      testId="dr-v3-section-crew-equipment"
    >
      {/* ═════════════════════════════════════════════════════════ */}
      {/* Crew · start / stop / lunch / calculated hours            */}
      {/* ═════════════════════════════════════════════════════════ */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Users className="h-4 w-4 text-red-700" />
            MASCI Crew
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-crew-add"
            onClick={() =>
              patch({
                masci_crews: [
                  ...crews,
                  {
                    name: "", trade: "",
                    start_time: "", stop_time: "", lunch_minutes: "",
                    hours: 0,
                  },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Add crew
          </Button>
        </div>
        {crews.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
            No MASCI crew today.
          </p>
        )}
        {crews.map((c, i) => {
          const preview = grossNetPreview(c.start_time, c.stop_time, c.lunch_minutes);
          const startAfterStop = (() => {
            if (!c.start_time || !c.stop_time) return false;
            const [sh, sm] = c.start_time.split(":").map(Number);
            const [eh, em] = c.stop_time.split(":").map(Number);
            if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return false;
            return eh * 60 + em <= sh * 60 + sm;
          })();
          return (
            <div
              key={i}
              data-testid={`dr-v3-crew-row-${i}`}
              className="rounded-xl border border-slate-200 p-3"
            >
              <div className="grid gap-2 sm:grid-cols-[2fr_1fr_auto]">
                <EmployeeCombo
                  value={c.name || ""}
                  onChange={(name, meta) =>
                    updateCrew(i, {
                      name,
                      employee_id: meta?.employee_id,
                      trade: meta?.trade || c.trade,
                    })
                  }
                  data-testid={`dr-v3-crew-name-${i}`}
                />
                <input
                  type="text"
                  placeholder="Trade"
                  value={c.trade || ""}
                  onChange={(e) => updateCrew(i, { trade: e.target.value })}
                  className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                  data-testid={`dr-v3-crew-trade-${i}`}
                />
                <button
                  type="button"
                  className={rowBtn}
                  onClick={() =>
                    patch({ masci_crews: crews.filter((_, j) => j !== i) })
                  }
                  data-testid={`dr-v3-crew-remove-${i}`}
                  aria-label="Remove crew row"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Time row */}
              <div className="mt-2 grid gap-2 sm:grid-cols-4">
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">Start</span>
                  <input
                    type="time"
                    value={c.start_time || ""}
                    onChange={(e) => updateCrew(i, { start_time: e.target.value })}
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-start-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">Stop</span>
                  <input
                    type="time"
                    value={c.stop_time || ""}
                    onChange={(e) => updateCrew(i, { stop_time: e.target.value })}
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-stop-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">Lunch (min)</span>
                  <input
                    type="number"
                    min="0"
                    step="5"
                    placeholder="0"
                    value={c.lunch_minutes ?? ""}
                    onChange={(e) =>
                      updateCrew(i, {
                        lunch_minutes:
                          e.target.value === "" ? "" : Math.max(0, parseInt(e.target.value, 10) || 0),
                      })
                    }
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-lunch-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">Hours (auto)</span>
                  <input
                    type="number"
                    step="0.25"
                    min="0"
                    value={c.hours ?? ""}
                    onChange={(e) => {
                      const next = crews.slice();
                      next[i] = { ...c, hours: parseFloat(e.target.value) || 0 };
                      patch({ masci_crews: next });
                    }}
                    className="rounded-md border border-slate-300 bg-slate-50 px-2 py-2 text-sm font-medium"
                    data-testid={`dr-v3-crew-hours-${i}`}
                  />
                </label>
              </div>

              {preview && !startAfterStop && (
                <p
                  className="mt-1 text-[11px] text-slate-500"
                  data-testid={`dr-v3-crew-preview-${i}`}
                >
                  {preview.label} · {preview.math}
                </p>
              )}
              {startAfterStop && (
                <p
                  className="mt-1 flex items-center gap-1 text-[11px] font-medium text-red-700"
                  data-testid={`dr-v3-crew-time-error-${i}`}
                >
                  <AlertTriangle className="h-3 w-3" />
                  Stop must be after start. Use overnight only if stop wraps past midnight.
                </p>
              )}

              {hasCodes && (
                <CostCodePicker
                  testId={`dr-v3-crew-cost-code-${i}`}
                  value={c.cost_code || ""}
                  options={costCodes}
                  onChange={(v) => {
                    const next = crews.slice();
                    next[i] = { ...c, cost_code: v };
                    patch({ masci_crews: next });
                  }}
                />
              )}
            </div>
          );
        })}

        {/* Crew totals summary strip */}
        {crews.length > 0 && (
          <div
            className="mt-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs"
            data-testid="dr-v3-crew-totals"
          >
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-700">
              <span>
                <span className="font-semibold text-slate-900">
                  {crewTotals.count}
                </span>{" "}
                {crewTotals.count === 1 ? "employee" : "employees"}
              </span>
              <span>·</span>
              <span data-testid="dr-v3-crew-total-hours">
                <span className="font-semibold text-slate-900">
                  {crewTotals.totalHours.toFixed(2)}
                </span>{" "}
                total man-hours
              </span>
              {crewTotals.totalLunch > 0 && (
                <>
                  <span>·</span>
                  <span>
                    <span className="font-semibold text-slate-900">
                      {(crewTotals.totalLunch / 60).toFixed(2)}
                    </span>{" "}
                    h lunch
                  </span>
                </>
              )}
            </div>
            {Object.keys(crewTotals.byCode).length > 0 && (
              <div
                className="mt-1 flex flex-wrap gap-1"
                data-testid="dr-v3-crew-total-by-code"
              >
                {Object.entries(crewTotals.byCode)
                  .sort((a, b) => b[1] - a[1])
                  .map(([code, hrs]) => (
                    <span
                      key={code}
                      className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] text-slate-700"
                    >
                      <span className="font-mono">{code}</span>
                      <span className="tabular-nums font-semibold">
                        {hrs.toFixed(2)}
                      </span>
                    </span>
                  ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═════════════════════════════════════════════════════════ */}
      {/* Equipment · run / idle / totals                           */}
      {/* ═════════════════════════════════════════════════════════ */}
      <div className="mt-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Wrench className="h-4 w-4 text-red-700" />
            Equipment
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-eq-add"
            onClick={() =>
              patch({
                equipment: [
                  ...equipment,
                  { description: "", hours_used: 0, idle_hours: 0, notes: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Add equipment
          </Button>
        </div>
        {equipment.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
            No equipment today.
          </p>
        )}
        {equipment.map((e, i) => (
          <div
            key={i}
            data-testid={`dr-v3-eq-row-${i}`}
            className="rounded-xl border border-slate-200 p-3"
          >
            <div className="grid gap-2 sm:grid-cols-[2fr_auto]">
              <EquipmentCombo
                value={e.description || ""}
                onChange={(v) => {
                  const next = equipment.slice();
                  next[i] = { ...e, description: v };
                  patch({ equipment: next });
                }}
                data-testid={`dr-v3-eq-desc-${i}`}
              />
              <button
                type="button"
                className={rowBtn}
                onClick={() =>
                  patch({ equipment: equipment.filter((_, j) => j !== i) })
                }
                data-testid={`dr-v3-eq-remove-${i}`}
                aria-label="Remove equipment row"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">Run hours</span>
                <input
                  type="number"
                  step="0.25"
                  min="0"
                  placeholder="0.00"
                  value={e.hours_used ?? ""}
                  onChange={(ev) => {
                    const next = equipment.slice();
                    next[i] = {
                      ...e,
                      hours_used: Math.max(0, parseFloat(ev.target.value) || 0),
                    };
                    patch({ equipment: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-eq-hours-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">Idle hours</span>
                <input
                  type="number"
                  step="0.25"
                  min="0"
                  placeholder="0.00"
                  value={e.idle_hours ?? ""}
                  onChange={(ev) => {
                    const next = equipment.slice();
                    next[i] = {
                      ...e,
                      idle_hours: Math.max(0, parseFloat(ev.target.value) || 0),
                    };
                    patch({ equipment: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-eq-idle-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">Total (run + idle)</span>
                <input
                  type="text"
                  value={(
                    (Number(e.hours_used) || 0) + (Number(e.idle_hours) || 0)
                  ).toFixed(2)}
                  readOnly
                  className="rounded-md border border-slate-200 bg-slate-50 px-2 py-2 text-sm font-medium text-slate-700"
                  data-testid={`dr-v3-eq-total-${i}`}
                />
              </label>
            </div>
            <input
              type="text"
              placeholder="Issues / notes (optional)"
              value={e.notes || ""}
              onChange={(ev) => {
                const next = equipment.slice();
                next[i] = { ...e, notes: ev.target.value };
                patch({ equipment: next });
              }}
              className="mt-2 w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
              data-testid={`dr-v3-eq-notes-${i}`}
            />
            {hasCodes && (
              <CostCodePicker
                testId={`dr-v3-eq-cost-code-${i}`}
                value={e.cost_code || ""}
                options={costCodes}
                onChange={(v) => {
                  const next = equipment.slice();
                  next[i] = { ...e, cost_code: v };
                  patch({ equipment: next });
                }}
              />
            )}
          </div>
        ))}

        {/* Equipment totals strip */}
        {equipment.length > 0 && (
          <div
            className="mt-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs"
            data-testid="dr-v3-eq-totals"
          >
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-700">
              <span>
                <span className="font-semibold text-slate-900">
                  {equipTotals.count}
                </span>{" "}
                {equipTotals.count === 1 ? "unit" : "units"}
              </span>
              <span>·</span>
              <span data-testid="dr-v3-eq-total-run">
                <span className="font-semibold text-slate-900">
                  {equipTotals.run.toFixed(2)}
                </span>{" "}
                run h
              </span>
              <span>·</span>
              <span data-testid="dr-v3-eq-total-idle">
                <span className="font-semibold text-slate-900">
                  {equipTotals.idle.toFixed(2)}
                </span>{" "}
                idle h
              </span>
              {equipTotals.util !== null && (
                <>
                  <span>·</span>
                  <span data-testid="dr-v3-eq-util">
                    <span className="font-semibold text-slate-900">
                      {equipTotals.util.toFixed(0)}%
                    </span>{" "}
                    utilization
                  </span>
                </>
              )}
              {equipTotals.withIssues > 0 && (
                <>
                  <span>·</span>
                  <span
                    className="text-amber-700"
                    data-testid="dr-v3-eq-issues-count"
                  >
                    <span className="font-semibold">
                      {equipTotals.withIssues}
                    </span>{" "}
                    with notes
                  </span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ═════════════════════════════════════════════════════════ */}
      {/* Subcontractors & Vendors                                  */}
      {/* ═════════════════════════════════════════════════════════ */}
      <div className="mt-6 space-y-3" data-testid="dr-v3-subs-block">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Truck className="h-4 w-4 text-red-700" />
            Subcontractors &amp; Vendors
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-sub-add"
            onClick={() =>
              patch({
                subcontractors: [
                  ...subs,
                  {
                    company: "", trade: "", foreman: "",
                    count: 0, hours: 0, work_performed: "",
                  },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Add sub / vendor
          </Button>
        </div>
        {subs.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
            No subcontractors or vendors on site today.
          </p>
        )}
        {subs.map((s, i) => (
          <div
            key={i}
            data-testid={`dr-v3-sub-row-${i}`}
            className="rounded-xl border border-slate-200 p-3"
          >
            <div className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_auto]">
              <SupplierCombo
                value={s.company || ""}
                onChange={(v) => {
                  const next = subs.slice();
                  next[i] = { ...s, company: v };
                  patch({ subcontractors: next });
                }}
                placeholder="Pick a subcontractor / vendor — or type"
                data-testid={`dr-v3-sub-company-${i}`}
              />
              <input
                type="text"
                placeholder="Trade / scope"
                value={s.trade || ""}
                onChange={(ev) => {
                  const next = subs.slice();
                  next[i] = { ...s, trade: ev.target.value };
                  patch({ subcontractors: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-sub-trade-${i}`}
              />
              <input
                type="text"
                placeholder="Foreman / contact"
                value={s.foreman || ""}
                onChange={(ev) => {
                  const next = subs.slice();
                  next[i] = { ...s, foreman: ev.target.value };
                  patch({ subcontractors: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-sub-foreman-${i}`}
              />
              <button
                type="button"
                className={rowBtn}
                onClick={() =>
                  patch({
                    subcontractors: subs.filter((_, j) => j !== i),
                  })
                }
                data-testid={`dr-v3-sub-remove-${i}`}
                aria-label="Remove subcontractor row"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr_3fr]">
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">Headcount</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={s.count ?? ""}
                  onChange={(ev) => {
                    const next = subs.slice();
                    next[i] = {
                      ...s,
                      count: Math.max(0, parseInt(ev.target.value, 10) || 0),
                    };
                    patch({ subcontractors: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-sub-count-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">Hours</span>
                <input
                  type="number"
                  min="0"
                  step="0.25"
                  value={s.hours ?? ""}
                  onChange={(ev) => {
                    const next = subs.slice();
                    next[i] = {
                      ...s,
                      hours: Math.max(0, parseFloat(ev.target.value) || 0),
                    };
                    patch({ subcontractors: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-sub-hours-${i}`}
                />
              </label>
              <input
                type="text"
                placeholder="Work performed / notes"
                value={s.work_performed || ""}
                onChange={(ev) => {
                  const next = subs.slice();
                  next[i] = { ...s, work_performed: ev.target.value };
                  patch({ subcontractors: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-sub-work-${i}`}
              />
            </div>
          </div>
        ))}
        {subs.length > 0 && (
          <div
            className="mt-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700"
            data-testid="dr-v3-sub-totals"
          >
            <span>
              <span className="font-semibold text-slate-900">{subsTotals.rows}</span>{" "}
              {subsTotals.rows === 1 ? "sub / vendor" : "subs / vendors"}
            </span>
            <span className="mx-2">·</span>
            <span>
              <span className="font-semibold text-slate-900">
                {subsTotals.totalCount}
              </span>{" "}
              total headcount
            </span>
            <span className="mx-2">·</span>
            <span>
              <span className="font-semibold text-slate-900">
                {subsTotals.totalHours.toFixed(2)}
              </span>{" "}
              total hours
            </span>
          </div>
        )}
      </div>
    </SectionShell>
  );
}

// ── Cost Code picker — hidden when no codes ────────────────────
export function CostCodePicker({ value, options, onChange, testId }) {
  if (!options || options.length === 0) return null;
  return (
    <div className="mt-2">
      <label className="mb-1 block text-xs font-medium text-slate-500">
        Cost code
      </label>
      <select
        data-testid={testId}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm"
      >
        <option value="">— Select —</option>
        {options.map((cc) => (
          <option key={cc.code} value={cc.code}>
            {cc.code} · {cc.description || ""}
          </option>
        ))}
      </select>
    </div>
  );
}

// ── Section 03 · Work Performed + Production ───────────────────
export function SectionWorkProduction({ data, patch, costCodes }) {
  const prod = data.production || [];
  const hasCodes = (costCodes?.length || 0) > 0;
  return (
    <SectionShell
      step="Step 3 · What got done?"
      title="Work Performed &amp; Production"
      testId="dr-v3-section-work"
    >
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">Production rows</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-prod-add"
            onClick={() =>
              patch({
                production: [
                  ...prod,
                  { description: "", quantity: 0, unit: "LF", notes: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Add row
          </Button>
        </div>
        {prod.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
            No production tracked today.
          </p>
        )}
        {prod.map((p, i) => (
          <div
            key={i}
            data-testid={`dr-v3-prod-row-${i}`}
            className="rounded-xl border border-slate-200 p-3"
          >
            <div className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_auto]">
              <input
                type="text"
                placeholder="What was installed / performed"
                value={p.description || ""}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, description: e.target.value };
                  patch({ production: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-prod-desc-${i}`}
              />
              <input
                type="number"
                step="0.01"
                placeholder="Qty"
                value={p.quantity ?? ""}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, quantity: parseFloat(e.target.value) || 0 };
                  patch({ production: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-prod-qty-${i}`}
              />
              <select
                value={p.unit || "LF"}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, unit: e.target.value };
                  patch({ production: next });
                }}
                className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm"
                data-testid={`dr-v3-prod-unit-${i}`}
              >
                {["LF", "SY", "SF", "CY", "TN", "EA", "OTHER"].map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className={rowBtn}
                onClick={() => patch({ production: prod.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-prod-remove-${i}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <input
              type="text"
              placeholder="Notes (optional)"
              value={p.notes || ""}
              onChange={(e) => {
                const next = prod.slice();
                next[i] = { ...p, notes: e.target.value };
                patch({ production: next });
              }}
              className="mt-2 w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
              data-testid={`dr-v3-prod-notes-${i}`}
            />
            {hasCodes && (
              <CostCodePicker
                testId={`dr-v3-prod-cost-code-${i}`}
                value={p.cost_code || ""}
                options={costCodes}
                onChange={(v) => {
                  const next = prod.slice();
                  next[i] = { ...p, cost_code: v };
                  patch({ production: next });
                }}
              />
            )}
          </div>
        ))}
      </div>
    </SectionShell>
  );
}

// ── Section 04 · Materials In + Out + Tickets ───────────────────
export function SectionMaterials({ data, patch, costCodes }) {
  const mats = data.materials || [];
  const outs = data.outbound_materials || [];
  const hasCodes = (costCodes?.length || 0) > 0;
  return (
    <SectionShell
      step="Step 4 · What moved?"
      title="Materials &amp; Tickets"
      testId="dr-v3-section-materials"
    >
      {/* Materials in */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">Materials delivered</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-mat-add"
            onClick={() =>
              patch({
                materials: [
                  ...mats,
                  { description: "", quantity: 0, unit: "TN", supplier: "", ticket_number: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Delivered
          </Button>
        </div>
        {mats.map((m, i) => (
          <div key={i} data-testid={`dr-v3-mat-row-${i}`} className="rounded-xl border border-slate-200 p-3">
            <div className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_2fr_auto]">
              <input
                type="text"
                placeholder="Description"
                value={m.description || ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, description: e.target.value };
                  patch({ materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-mat-desc-${i}`}
              />
              <input
                type="number"
                step="0.01"
                placeholder="Qty"
                value={m.quantity ?? ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, quantity: parseFloat(e.target.value) || 0 };
                  patch({ materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-mat-qty-${i}`}
              />
              <input
                type="text"
                placeholder="Unit"
                value={m.unit || ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, unit: e.target.value };
                  patch({ materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-mat-unit-${i}`}
              />
              <SupplierCombo
                value={m.supplier || ""}
                onChange={(v) => {
                  const next = mats.slice();
                  next[i] = { ...m, supplier: v };
                  patch({ materials: next });
                }}
                data-testid={`dr-v3-mat-supplier-${i}`}
              />
              <button
                type="button"
                className={rowBtn}
                onClick={() => patch({ materials: mats.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-mat-remove-${i}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <input
                type="text"
                placeholder="Ticket #"
                value={m.ticket_number || ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, ticket_number: e.target.value };
                  patch({ materials: next });
                }}
                className="rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
                data-testid={`dr-v3-mat-ticket-${i}`}
              />
              <PhotoUpload
                value={m.ticket_photos || []}
                onChange={(next) => {
                  const rows = mats.slice();
                  rows[i] = { ...m, ticket_photos: next };
                  patch({ materials: rows });
                }}
                placeholderLabel="Add ticket photo"
                testIdBase={`dr-v3-mat-ticketphoto-${i}`}
              />
            </div>
            {hasCodes && (
              <CostCodePicker
                testId={`dr-v3-mat-cost-code-${i}`}
                value={m.cost_code || ""}
                options={costCodes}
                onChange={(v) => {
                  const next = mats.slice();
                  next[i] = { ...m, cost_code: v };
                  patch({ materials: next });
                }}
              />
            )}
          </div>
        ))}
      </div>

      {/* Materials out */}
      <div className="mt-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">Hauled off / outbound</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-out-add"
            onClick={() =>
              patch({
                outbound_materials: [
                  ...outs,
                  { material: "", quantity: 0, unit: "TN", hauler: "", destination: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" /> Outbound
          </Button>
        </div>
        {outs.map((o, i) => (
          <div key={i} data-testid={`dr-v3-out-row-${i}`} className="rounded-xl border border-slate-200 p-3">
            <div className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_2fr_auto]">
              <input
                type="text"
                placeholder="Material"
                value={o.material || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, material: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-mat-${i}`}
              />
              <input
                type="number"
                step="0.01"
                placeholder="Qty"
                value={o.quantity ?? ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, quantity: parseFloat(e.target.value) || 0 };
                  patch({ outbound_materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-qty-${i}`}
              />
              <input
                type="text"
                placeholder="Unit"
                value={o.unit || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, unit: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-unit-${i}`}
              />
              <input
                type="text"
                placeholder="Destination"
                value={o.destination || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, destination: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-dest-${i}`}
              />
              <button
                type="button"
                className={rowBtn}
                onClick={() => patch({ outbound_materials: outs.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-out-remove-${i}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}

// ── Section 05 · Photos + Evidence ─────────────────────────────
export function SectionPhotos({ data, patch, photoMin }) {
  const photos = data.photos || [];
  const short = Math.max(0, (photoMin || 6) - photos.length);
  return (
    <SectionShell
      step="Step 5 · What can we prove?"
      title="Photos &amp; Evidence"
      testId="dr-v3-section-photos"
      right={
        <span
          data-testid="dr-v3-photo-count"
          className={
            "rounded-full px-3 py-1 text-xs font-medium " +
            (short === 0 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700")
          }
        >
          <Camera className="mr-1 inline h-3.5 w-3.5" /> {photos.length}/{photoMin} required
        </span>
      }
    >
      <PhotoUpload
        value={photos}
        onChange={(next) => patch({ photos: next })}
        placeholderLabel="Add photo"
        testIdBase="dr-v3-photos"
      />
      {short > 0 && (
        <p className="mt-3 text-xs text-amber-700" data-testid="dr-v3-photo-short">
          Add at least {short} more photo{short === 1 ? "" : "s"} before submit.
        </p>
      )}
    </SectionShell>
  );
}

// ── Section 06 · Combined Impact / Safety gate ────────────────
const IMPACT_TYPES = [
  { key: "weather", label: "Weather" },
  { key: "material", label: "Material" },
  { key: "equipment", label: "Equipment" },
  { key: "utility", label: "Utility conflict" },
  { key: "inspection", label: "Inspection" },
  { key: "owner_eng", label: "Owner / Engineering" },
  { key: "subcontractor", label: "Subcontractor" },
  { key: "traffic_mot", label: "Traffic / MOT" },
  { key: "extra_work", label: "Extra work" },
  { key: "other", label: "Other" },
];

const SAFETY_TYPES = [
  { key: "near_miss", label: "Near miss" },
  { key: "incident", label: "Incident" },
  { key: "accident", label: "Accident" },
  { key: "property_damage", label: "Property damage" },
  { key: "utility_strike", label: "Utility strike" },
  { key: "inspection", label: "Safety inspection" },
  { key: "other", label: "Other" },
];

export function SectionImpactSafety({ data, patch }) {
  const anyImpact = data.impact_present === "Yes";
  const anySafety = data.safety_present === "Yes";
  const constraints = data.constraints || [];

  const addConstraint = (type) => {
    patch({
      constraints: [
        ...constraints,
        { constraint_type: type, hours_impact: 0, notes: "" },
      ],
    });
  };

  return (
    <SectionShell
      step="Step 6 · What impacted today?"
      title="Delays, Extra Work &amp; Safety"
      testId="dr-v3-section-impact-safety"
    >
      {/* Impact gate */}
      <div className="rounded-xl border border-slate-200 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <TrafficCone className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-medium text-slate-800">
              Did anything reduce or add to production today?
            </span>
          </div>
          <YesNoInline
            value={data.impact_present || ""}
            onChange={(v) => {
              const patchObj = { impact_present: v };
              if (v === "No") {
                patchObj.constraints = [];
                patchObj.schedule_delays = "No";
                patchObj.weather_impact = "No";
              }
              patch(patchObj);
            }}
            testId="dr-v3-impact-gate"
          />
        </div>
        {anyImpact && (
          <>
            <p className="mb-2 text-xs text-slate-500">Tap a type to add a row.</p>
            <div className="flex flex-wrap gap-1.5">
              {IMPACT_TYPES.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 hover:bg-slate-50"
                  onClick={() => {
                    if (t.key === "weather") patch({ weather_impact: "Yes" });
                    addConstraint(t.key);
                  }}
                  data-testid={`dr-v3-impact-chip-${t.key}`}
                >
                  + {t.label}
                </button>
              ))}
            </div>
            {constraints.length > 0 && (
              <div className="mt-3 space-y-2">
                {constraints.map((c, i) => (
                  <div
                    key={i}
                    data-testid={`dr-v3-constraint-row-${i}`}
                    className="grid gap-2 rounded-md border border-slate-200 p-2 sm:grid-cols-[1fr_100px_2fr_auto]"
                  >
                    <span className="text-xs font-medium text-slate-700">
                      {IMPACT_TYPES.find((t) => t.key === c.constraint_type)?.label ||
                        c.constraint_type}
                    </span>
                    <input
                      type="number"
                      step="0.25"
                      placeholder="Hrs"
                      value={c.hours_impact ?? ""}
                      onChange={(e) => {
                        const next = constraints.slice();
                        next[i] = { ...c, hours_impact: parseFloat(e.target.value) || 0 };
                        patch({ constraints: next });
                      }}
                      className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                    />
                    <input
                      type="text"
                      placeholder="Notes"
                      value={c.notes || ""}
                      onChange={(e) => {
                        const next = constraints.slice();
                        next[i] = { ...c, notes: e.target.value };
                        patch({ constraints: next });
                      }}
                      className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                    />
                    <button
                      type="button"
                      className={rowBtn}
                      onClick={() =>
                        patch({ constraints: constraints.filter((_, j) => j !== i) })
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Safety gate */}
      <div className="mt-4 rounded-xl border border-slate-200 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-slate-800">
              Did anything safety-related occur today?
            </span>
          </div>
          <YesNoInline
            value={data.safety_present || ""}
            onChange={(v) => {
              const patchObj = { safety_present: v };
              if (v === "No") {
                patchObj.safety_incidents_today = "No";
                patchObj.injuries_reported = "No";
                patchObj.safety_notified = "";
                patchObj.incident_report_filled = "";
                patchObj.safety_contact_person = "";
                patchObj.safety_contact_time = "";
                patchObj.safety_contact_method = "";
                patchObj.incident_report_time = "";
                patchObj.incident_report_reference = "";
                patchObj.incident_notes = "";
                patchObj.safety_event_type = "";
                patchObj.safety_ack_no_contact = false;
              } else if (v === "Yes") {
                patchObj.safety_incidents_today = "Yes";
              }
              patch(patchObj);
            }}
            testId="dr-v3-safety-gate"
          />
        </div>
        {anySafety && (
          <div className="space-y-3" data-testid="dr-v3-safety-escalation">
            {/* Event type */}
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                What kind of event? <span className="text-red-600">*</span>
              </label>
              <select
                value={data.safety_event_type || ""}
                onChange={(e) => {
                  const v = e.target.value;
                  const p = { safety_event_type: v };
                  // Injury / accident triggers injuries_reported so the
                  // V1 downstream (HR / Trust Spine / notifications) fires
                  // the same escalation as before.
                  p.injuries_reported = (v === "injury" || v === "accident") ? "Yes" : "No";
                  patch(p);
                }}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                data-testid="dr-v3-safety-event-type"
              >
                <option value="">— Select —</option>
                {SAFETY_TYPES.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <Textarea
              rows={3}
              placeholder="What happened? (required for supervisor review)"
              value={data.incident_notes || ""}
              onChange={(e) => patch({ incident_notes: e.target.value })}
              data-testid="dr-v3-incident-notes"
            />

            {/* ── Safety contact escalation ────────────────────── */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                  Was Safety contacted? <span className="text-red-600">*</span>
                </span>
                <YesNoInline
                  value={data.safety_notified || ""}
                  onChange={(v) => {
                    const p = { safety_notified: v };
                    if (v === "No") {
                      p.safety_contact_person = "";
                      p.safety_contact_time = "";
                      p.safety_contact_method = "";
                    }
                    if (v === "Yes") p.safety_ack_no_contact = false;
                    patch(p);
                  }}
                  testId="dr-v3-safety-notified"
                />
              </div>

              {data.safety_notified === "Yes" && (
                <div
                  className="grid gap-2 sm:grid-cols-3"
                  data-testid="dr-v3-safety-contact-fields"
                >
                  <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-0.5">
                      Who at Safety? <span className="text-red-600">*</span>
                    </span>
                    <input
                      type="text"
                      value={data.safety_contact_person || ""}
                      onChange={(e) =>
                        patch({ safety_contact_person: e.target.value })
                      }
                      className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                      data-testid="dr-v3-safety-contact-person"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-0.5">
                      Time contacted <span className="text-red-600">*</span>
                    </span>
                    <input
                      type="time"
                      value={data.safety_contact_time || ""}
                      onChange={(e) =>
                        patch({ safety_contact_time: e.target.value })
                      }
                      className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                      data-testid="dr-v3-safety-contact-time"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-0.5">Method</span>
                    <select
                      value={data.safety_contact_method || ""}
                      onChange={(e) =>
                        patch({ safety_contact_method: e.target.value })
                      }
                      className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm"
                      data-testid="dr-v3-safety-contact-method"
                    >
                      <option value="">— Select —</option>
                      <option value="phone">Phone</option>
                      <option value="text">Text</option>
                      <option value="in_person">In person</option>
                      <option value="email">Email</option>
                      <option value="other">Other</option>
                    </select>
                  </label>
                </div>
              )}

              {data.safety_notified === "No" && (
                <div
                  className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800"
                  data-testid="dr-v3-safety-not-contacted-warn"
                >
                  <div className="mb-2 flex items-center gap-2 font-semibold">
                    <AlertTriangle className="h-4 w-4" />
                    Stop and contact Safety before submitting.
                  </div>
                  <label className="flex items-start gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={!!data.safety_ack_no_contact}
                      onChange={(e) =>
                        patch({ safety_ack_no_contact: e.target.checked })
                      }
                      data-testid="dr-v3-safety-ack-no-contact"
                    />
                    <span>
                      I understand this Daily Report cannot be submitted
                      until Safety has been contacted. I will not submit
                      before that call.
                    </span>
                  </label>
                </div>
              )}
            </div>

            {/* ── Incident/accident report gate ─────────────────── */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                  Incident / Accident report filed? <span className="text-red-600">*</span>
                </span>
                <YesNoInline
                  value={data.incident_report_filled || ""}
                  onChange={(v) => {
                    const p = { incident_report_filled: v };
                    if (v === "No") {
                      p.incident_report_time = "";
                      p.incident_report_reference = "";
                    }
                    patch(p);
                  }}
                  testId="dr-v3-incident-report-filled"
                />
              </div>

              {data.incident_report_filled === "Yes" && (
                <div
                  className="grid gap-2 sm:grid-cols-2"
                  data-testid="dr-v3-incident-report-fields"
                >
                  <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-0.5">
                      Time filed <span className="text-red-600">*</span>
                    </span>
                    <input
                      type="time"
                      value={data.incident_report_time || ""}
                      onChange={(e) =>
                        patch({ incident_report_time: e.target.value })
                      }
                      className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                      data-testid="dr-v3-incident-report-time"
                    />
                  </label>
                  <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-0.5">Reference / report #</span>
                    <input
                      type="text"
                      value={data.incident_report_reference || ""}
                      onChange={(e) =>
                        patch({ incident_report_reference: e.target.value })
                      }
                      className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                      data-testid="dr-v3-incident-report-reference"
                    />
                  </label>
                </div>
              )}

              {data.incident_report_filled === "No" && (
                <div
                  className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900"
                  data-testid="dr-v3-incident-report-action-required"
                >
                  <div className="mb-2 flex items-center gap-2 font-semibold">
                    <AlertTriangle className="h-4 w-4" />
                    Action required: file the Accident / Incident report.
                  </div>
                  <p className="mb-2 text-xs">
                    Your Daily Report draft is autosaved. Open the
                    Accident / Incident form, submit it, then return here
                    and mark this Yes with the time filed.
                  </p>
                  <Link
                    to="/safety/incident-report"
                    className="inline-flex items-center gap-1 rounded-md border border-amber-400 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 hover:bg-amber-100"
                    data-testid="dr-v3-open-incident-report"
                  >
                    <ExternalLink className="h-3 w-3" /> Open Accident / Incident Report
                  </Link>
                </div>
              )}
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={data.injuries_reported === "Yes"}
                  onChange={(e) =>
                    patch({ injuries_reported: e.target.checked ? "Yes" : "No" })
                  }
                  data-testid="dr-v3-injuries-reported"
                />
                Injuries reported
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={data.work_stopped === "Yes"}
                  onChange={(e) =>
                    patch({ work_stopped: e.target.checked ? "Yes" : "No" })
                  }
                  data-testid="dr-v3-work-stopped"
                />
                Work stopped
              </label>
            </div>

            <p className="text-[11px] text-slate-500">
              Photos of the scene / conditions are strongly recommended.
              Add them in Step 5 · Photos &amp; Evidence.
            </p>
          </div>
        )}
      </div>
    </SectionShell>
  );
}

function YesNoInline({ value, onChange, testId }) {
  return (
    <div className="inline-flex overflow-hidden rounded-md border border-slate-200 text-xs">
      {["Yes", "No"].map((v) => (
        <button
          key={v}
          type="button"
          className={
            "px-3 py-1 " +
            (value === v
              ? v === "Yes"
                ? "bg-red-50 text-red-800"
                : "bg-slate-100 text-slate-800"
              : "bg-white text-slate-600 hover:bg-slate-50")
          }
          onClick={() => onChange(v)}
          data-testid={`${testId}-${v.toLowerCase()}`}
        >
          {v}
        </button>
      ))}
    </div>
  );
}

// ── Section 07 · Tomorrow / Needs / PM Attention ────────────────
export function SectionTomorrow({ data, patch }) {
  const ns = data.narrative_sections || {};
  const set = (key, v) => patch({ narrative_sections: { ...ns, [key]: v } });
  return (
    <SectionShell
      step="Step 7 · What's next?"
      title="Tomorrow &amp; PM Attention"
      testId="dr-v3-section-tomorrow"
    >
      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Tomorrow / next work
          </label>
          <Textarea
            rows={2}
            value={ns.tomorrow_plan || ""}
            onChange={(e) => set("tomorrow_plan", e.target.value)}
            placeholder="Which crew · what work · which station"
            data-testid="dr-v3-tomorrow-plan"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Needs / blockers for the PM
            <Clock className="ml-1 inline h-3.5 w-3.5 text-slate-400" />
          </label>
          <Textarea
            rows={2}
            value={ns.follow_ups || ""}
            onChange={(e) => set("follow_ups", e.target.value)}
            placeholder="RFI, submittal, material, equipment, permit …"
            data-testid="dr-v3-follow-ups"
          />
        </div>
      </div>
    </SectionShell>
  );
}

// ── Section 08 · Operational Summary Assist (single AI card) ────
export function SectionAiSummary({ data, reportId, onAccepted }) {
  return (
    <SectionShell
      step="Step 8 · Draft your report summary"
      title="Operational Summary Assist"
      testId="dr-v3-section-ai-summary"
    >
      <p className="mb-3 text-xs text-slate-500">
        AI drafts a summary from what you entered. You stay the source of truth — accept, edit,
        or ignore. This is what your PM will see.
      </p>
      <DailySummaryAssist
        reportId={reportId}
        reportNumber={data.report_number}
        data={data}
        onAccepted={onAccepted}
      />
    </SectionShell>
  );
}

// ── Section 09 · Submit Readiness + Sign-Off ─────────────────
export function SectionSignoff({
  data, patch, readiness, onSubmit, saving, canSubmit,
}) {
  return (
    <SectionShell
      step="Step 9 · Sign &amp; submit"
      title="Submit Readiness &amp; Sign-Off"
      testId="dr-v3-section-signoff"
    >
      <div className="space-y-4">
        <div
          data-testid="dr-v3-readiness"
          className={
            "rounded-xl px-4 py-3 text-sm " +
            (canSubmit
              ? "bg-emerald-50 text-emerald-800"
              : "bg-amber-50 text-amber-800")
          }
        >
          {canSubmit ? (
            <>Ready to submit — <strong>{readiness.completed}/{readiness.total}</strong> items complete.</>
          ) : (
            <>
              Still needed:{" "}
              <strong>{readiness.missing.join(" · ") || "checking…"}</strong>
            </>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Prepared By Signature *
          </label>
          <SignaturePad
            value={data.prepared_by_signature || ""}
            onChange={(v) => patch({ prepared_by_signature: v })}
            data-testid="dr-v3-signature"
          />
        </div>

        <Button
          type="button"
          className="w-full bg-emerald-600 py-6 text-base font-semibold hover:bg-emerald-700"
          disabled={!canSubmit || saving}
          onClick={onSubmit}
          data-testid="dr-v3-submit-btn"
        >
          {saving ? "Submitting…" : "Submit Daily Report"}
        </Button>
      </div>
    </SectionShell>
  );
}
