// TRACK 23.10-E · Daily Report V3 — Excavation Section
//
// Court-defensible excavation workflow. Consumes the Track 23.10-B
// Qualifications Engine via CompetentPersonCombo. No manual CP typing.
// Section collapses fully when "Excavation today = No" — zero clutter.
//
// Parent contract:
//   props.value = excavation payload dict (may be {} or undefined)
//   props.onChange(nextExc: object) → void
//   props.disabled?: boolean
//
// The parent (NewDailyReportV3) MUST place the returned dict at
// `payload.excavation` before POST /api/daily-reports. The server-side
// Track 23.10-E service (`services/daily_report_v3_excavation`) will:
//   * validate CP selection against active registry (rejects free-text),
//   * freeze qualification snapshot,
//   * compute readiness state,
//   * emit ODS facts,
//   * persist excavation block onto the DR document.
import React from "react";
import { Layers, ShieldAlert, AlertTriangle } from "lucide-react";
import CompetentPersonCombo from "./CompetentPersonCombo";

const inputCls =
  "h-9 text-sm border-2 border-slate-300 focus:ring-2 focus:ring-purple-600 rounded px-2 w-full";

function _yn(v) { return String(v || "").toLowerCase() === "yes"; }

function YesNo({ value, onChange, testid }) {
  return (
    <div className="inline-flex gap-1" data-testid={testid}>
      {["Yes", "No"].map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt.toLowerCase())}
          data-testid={`${testid}-${opt.toLowerCase()}`}
          className={`px-2 py-1 rounded text-[11px] font-mono uppercase tracking-[0.15em] font-bold border ${
            String(value).toLowerCase() === opt.toLowerCase()
              ? "bg-purple-700 text-white border-purple-800"
              : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function CheckList({ options, values, onChange, testidPrefix }) {
  const set = new Set(values || []);
  return (
    <div className="flex flex-wrap gap-1" data-testid={testidPrefix}>
      {options.map((opt) => {
        const on = set.has(opt);
        return (
          <button
            key={opt}
            type="button"
            data-testid={`${testidPrefix}-${opt.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}
            onClick={() => {
              const s = new Set(values || []);
              if (s.has(opt)) s.delete(opt); else s.add(opt);
              onChange(Array.from(s));
            }}
            className={`px-2 py-1 rounded text-[11px] font-mono uppercase tracking-[0.1em] font-bold border ${
              on
                ? "bg-purple-700 text-white border-purple-800"
                : "bg-white text-slate-700 border-slate-300"
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

const PROTECTIVE_SYSTEMS = [
  "Sloping", "Benching", "Shield", "Trench Box",
  "Hydraulic Shoring", "Timber Shoring", "Other",
];
const UTILITIES = ["Power", "Gas", "Fiber", "Water", "Sewer", "Storm", "Communications", "Unknown"];
const SOIL_TYPES = ["A", "B", "C", "Mixed", "Unknown"];

export default function DailyReportV3ExcavationSection({
  value = {},
  onChange,
  disabled = false,
}) {
  const exc = value || {};
  const gate = String(exc.excavation_today || "").toLowerCase();
  const isYes = gate === "yes";

  const set = (patch) => onChange({ ...exc, ...patch });

  return (
    <section
      data-testid="dr-v3-excavation-section"
      className="border-2 border-slate-300 rounded bg-white"
    >
      <div className="p-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-600" />
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] font-bold text-slate-600">
              Track 23.10-E
            </div>
            <div className="text-sm font-bold">Excavation / Trench Operations</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-600 font-bold">
            Excavation today?
          </span>
          <YesNo
            value={gate}
            onChange={(v) => set({ excavation_today: v })}
            testid="dr-v3-excavation-gate"
          />
        </div>
      </div>

      {!isYes ? (
        <div className="p-4 text-sm text-slate-500 italic"
             data-testid="dr-v3-excavation-collapsed">
          No excavation work today. This section stays clean.
        </div>
      ) : (
        <div className="p-4 space-y-5" data-testid="dr-v3-excavation-body">
          {/* ── Location / dimensions ─────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Location &amp; dimensions
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              <input type="text" placeholder="Project area" value={exc.project_area || ""}
                     onChange={(e) => set({ project_area: e.target.value })}
                     className={inputCls} data-testid="exc-project-area" disabled={disabled} />
              <input type="text" placeholder="Station from" value={exc.station_from || ""}
                     onChange={(e) => set({ station_from: e.target.value })}
                     className={inputCls} data-testid="exc-station-from" disabled={disabled} />
              <input type="text" placeholder="Station to" value={exc.station_to || ""}
                     onChange={(e) => set({ station_to: e.target.value })}
                     className={inputCls} data-testid="exc-station-to" disabled={disabled} />
              <input type="number" step="0.1" placeholder="Length" value={exc.length ?? ""}
                     onChange={(e) => set({ length: e.target.value })}
                     className={inputCls} data-testid="exc-length" disabled={disabled} />
              <input type="number" step="0.1" placeholder="Width" value={exc.width ?? ""}
                     onChange={(e) => set({ width: e.target.value })}
                     className={inputCls} data-testid="exc-width" disabled={disabled} />
              <input type="number" step="0.1" placeholder="Depth" value={exc.depth ?? ""}
                     onChange={(e) => set({ depth: e.target.value })}
                     className={inputCls} data-testid="exc-depth" disabled={disabled} />
              <select value={exc.dimension_unit || "ft"}
                      onChange={(e) => set({ dimension_unit: e.target.value })}
                      className={inputCls} data-testid="exc-dimension-unit" disabled={disabled}>
                <option value="ft">Feet</option>
                <option value="m">Metres</option>
              </select>
              <input type="text" placeholder="Location notes" value={exc.location_notes || ""}
                     onChange={(e) => set({ location_notes: e.target.value })}
                     className={`${inputCls} md:col-span-2`} data-testid="exc-location-notes"
                     disabled={disabled} />
            </div>
          </div>

          {/* ── Protective system ─────────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Protective system
            </div>
            <CheckList
              options={PROTECTIVE_SYSTEMS}
              values={exc.protective_systems || []}
              onChange={(v) => set({ protective_systems: v })}
              testidPrefix="exc-protective-systems"
            />
            <input type="text" placeholder="Notes" value={exc.protective_system_notes || ""}
                   onChange={(e) => set({ protective_system_notes: e.target.value })}
                   className={`${inputCls} mt-2`} data-testid="exc-protective-notes"
                   disabled={disabled} />
          </div>

          {/* ── Soil ─────────────────────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Soil
            </div>
            <select value={exc.soil_type || ""}
                    onChange={(e) => set({ soil_type: e.target.value })}
                    className={`${inputCls} max-w-xs`}
                    data-testid="exc-soil-type" disabled={disabled}>
              <option value="">— Select —</option>
              {SOIL_TYPES.map((t) => (
                <option key={t} value={t}>{`Type ${t}`}</option>
              ))}
            </select>
            <input type="text" placeholder="Soil notes" value={exc.soil_notes || ""}
                   onChange={(e) => set({ soil_notes: e.target.value })}
                   className={`${inputCls} mt-2`} data-testid="exc-soil-notes"
                   disabled={disabled} />
          </div>

          {/* ── Utilities ─────────────────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Utilities
            </div>
            <CheckList
              options={UTILITIES}
              values={exc.utilities_exposed || []}
              onChange={(v) => set({ utilities_exposed: v })}
              testidPrefix="exc-utilities-exposed"
            />
            <div className="grid grid-cols-2 gap-2 mt-2">
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Conflict encountered?
                <YesNo value={exc.utility_conflict} onChange={(v) => set({ utility_conflict: v })}
                       testid="exc-utility-conflict" />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
                Damage / strike?
                <YesNo value={exc.utility_damage_or_strike}
                       onChange={(v) => set({ utility_damage_or_strike: v })}
                       testid="exc-utility-damage" />
              </label>
            </div>
            {_yn(exc.utility_damage_or_strike) && (
              <div className="mt-2 p-2 border-2 border-rose-400 bg-rose-50 text-rose-900 rounded text-xs"
                   data-testid="exc-utility-damage-warning">
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                Utility strike/damage recorded. Ensure Safety incident + hold workflow is followed.
              </div>
            )}
            <input type="text" placeholder="Utilities notes" value={exc.utilities_notes || ""}
                   onChange={(e) => set({ utilities_notes: e.target.value })}
                   className={`${inputCls} mt-2`} data-testid="exc-utilities-notes"
                   disabled={disabled} />
          </div>

          {/* ── Competent Person ──────────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Competent Person <span className="text-slate-500 normal-case">(Qualifications Engine · registry only · no free text)</span>
            </div>
            <CompetentPersonCombo
              value={exc.competent_person_qualification_id}
              onChange={({ qualification_id, snapshot, row }) => {
                set({
                  competent_person_qualification_id: qualification_id || "",
                  competent_person_employee_id: row?.employee_id || "",
                  competent_person_name_snapshot: row?.employee_name
                    || snapshot?.person_name_snapshot || "",
                  competent_person_trade_snapshot: row?.employee_trade
                    || snapshot?.person_trade_snapshot || "",
                });
              }}
              testidPrefix="exc-cp-combo"
              readOnly={disabled}
            />
          </div>

          {/* ── Inspection / stoppage ─────────────────────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Inspection &amp; work stoppage
            </div>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Inspection required?
                <YesNo value={exc.inspection_required}
                       onChange={(v) => set({ inspection_required: v })}
                       testid="exc-inspection-required" />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Inspection completed?
                <YesNo value={exc.inspection_completed}
                       onChange={(v) => set({ inspection_completed: v })}
                       testid="exc-inspection-completed" />
              </label>
              <input type="text" placeholder="Inspection time (e.g. 07:15)"
                     value={exc.inspection_time || ""}
                     onChange={(e) => set({ inspection_time: e.target.value })}
                     className={inputCls} data-testid="exc-inspection-time" disabled={disabled} />
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Weather / event reinspection?
                <YesNo value={exc.weather_reinspection}
                       onChange={(v) => set({ weather_reinspection: v })}
                       testid="exc-weather-reinspection" />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Hazards identified?
                <YesNo value={exc.hazards_identified}
                       onChange={(v) => set({ hazards_identified: v })}
                       testid="exc-hazards-identified" />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Corrective actions open?
                <YesNo value={exc.corrective_actions_open}
                       onChange={(v) => set({ corrective_actions_open: v })}
                       testid="exc-corrective-actions-open" />
              </label>
              <input type="text" placeholder="Corrective actions description"
                     value={exc.corrective_actions || ""}
                     onChange={(e) => set({ corrective_actions: e.target.value })}
                     className={`${inputCls} md:col-span-2`} data-testid="exc-corrective-actions"
                     disabled={disabled} />
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
                Work stopped?
                <YesNo value={exc.work_stopped}
                       onChange={(v) => set({ work_stopped: v })}
                       testid="exc-work-stopped" />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
                Hold issued?
                <YesNo value={exc.hold_issued}
                       onChange={(v) => set({ hold_issued: v })}
                       testid="exc-hold-issued" />
              </label>
              {_yn(exc.work_stopped) && (
                <input type="text" placeholder="Stop reason" value={exc.work_stop_reason || ""}
                       onChange={(e) => set({ work_stop_reason: e.target.value })}
                       className={`${inputCls} md:col-span-2`} data-testid="exc-work-stop-reason"
                       disabled={disabled} />
              )}
              {_yn(exc.work_stopped) && (
                <input type="text" placeholder="Restart time" value={exc.restart_time || ""}
                       onChange={(e) => set({ restart_time: e.target.value })}
                       className={inputCls} data-testid="exc-restart-time" disabled={disabled} />
              )}
            </div>
            {(_yn(exc.hold_issued) || _yn(exc.work_stopped)) && (
              <div className="mt-2 p-2 border-2 border-amber-400 bg-amber-50 text-amber-900 rounded text-xs"
                   data-testid="exc-hold-stoppage-warning">
                <ShieldAlert className="w-4 h-4 inline mr-1" />
                Hold or work stoppage recorded — Scheduling readiness will be set to BLOCKED.
              </div>
            )}
          </div>

          {/* ── Compact access · atmosphere · water ───────────── */}
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 mb-2">
              Access · Atmosphere · Water
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Access/egress compliant?
                <select value={exc.access_egress_compliant || ""}
                        onChange={(e) => set({ access_egress_compliant: e.target.value })}
                        className={inputCls} data-testid="exc-access-compliant" disabled={disabled}>
                  <option value="">—</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                  <option value="n/a">N/A</option>
                </select>
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Atmospheric testing required?
                <select value={exc.atmospheric_testing_required || ""}
                        onChange={(e) => set({ atmospheric_testing_required: e.target.value })}
                        className={inputCls} data-testid="exc-atm-required" disabled={disabled}>
                  <option value="">—</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                  <option value="n/a">N/A</option>
                </select>
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Atmosphere safe?
                <YesNo value={exc.atmosphere_safe}
                       onChange={(v) => set({ atmosphere_safe: v })}
                       testid="exc-atm-safe" />
              </label>
              <input type="text" placeholder="Atmosphere readings"
                     value={exc.atmosphere_readings || ""}
                     onChange={(e) => set({ atmosphere_readings: e.target.value })}
                     className={inputCls} data-testid="exc-atm-readings" disabled={disabled} />
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700">
                Water accumulation?
                <YesNo value={exc.water_accumulation}
                       onChange={(v) => set({ water_accumulation: v })}
                       testid="exc-water-accumulation" />
              </label>
              <input type="text" placeholder="Water mitigation notes"
                     value={exc.water_mitigation || ""}
                     onChange={(e) => set({ water_mitigation: e.target.value })}
                     className={inputCls} data-testid="exc-water-mitigation" disabled={disabled} />
            </div>
          </div>

          <div className="text-[11px] text-slate-500 border-t border-slate-200 pt-3">
            Photos captured on the main Daily Report photo pipeline will automatically
            surface here — no separate photo store. Readiness state is computed
            server-side on submit and consumed by Scheduling &amp; Safety KPIs.
          </div>
        </div>
      )}
    </section>
  );
}
