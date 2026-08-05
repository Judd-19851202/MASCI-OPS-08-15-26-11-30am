// TRACK 23.1 · V3 Sections 02–08 · single-file module.
//
// Each section is a small, focused presentational component that
// composes existing shared primitives (EmployeeCombo, EquipmentCombo,
// PhotoUpload, DailySummaryAssist). Same payload keys as V1.
import React, { useMemo, useRef, useState } from "react";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { EquipmentCombo } from "@/components/EquipmentCombo";
import { SupplierCombo } from "@/components/SupplierCombo";
import { PhotoUpload } from "@/components/PhotoUpload";
import AttachmentUpload from "@/components/AttachmentUpload";
import { SignaturePad } from "@/components/SignaturePad";
import DailySummaryAssist from "@/components/daily-report/DailySummaryAssist";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Plus, Trash2, ShieldAlert, TrafficCone, Clock, Camera, Users, Wrench,
  Truck, AlertTriangle, ExternalLink,
  Mic, Loader2, Languages,
} from "lucide-react";
import { computeCrewHours, grossNetPreview, sumCrewHours, sumEquipmentHours }
  from "@/lib/crewHoursMath";
import { UnitCombo } from "@/components/daily-report-v3/UnitCombo";
import { fetchHrRoster } from "@/lib/hrRoster";
import { resolveEmployeeByTypedName, pickHrFields } from "@/lib/hrAutofill";
import { Link } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { DEFAULT_MATERIAL_UNITS } from "@/components/daily-report-v3/UnitCombo";

const UNIT_LIBRARY_MAP = new Map(DEFAULT_MATERIAL_UNITS.map((u) => [u.code, u]));

function normalizeNumericInputValue(raw) {
  if (raw == null) return "";
  const value = String(raw);
  if (/^-?0\d+/.test(value) && !/^0\./.test(value)) {
    return value.replace(/^(-?)0+(\d)/, "$1$2");
  }
  return value;
}

function parseNumericField(raw, { integer = false, min = null, max = null } = {}) {
  if (raw === "") return "";
  const parsed = integer ? parseInt(raw, 10) : parseFloat(raw);
  let next = Number.isFinite(parsed) ? parsed : 0;
  if (min != null) next = Math.max(min, next);
  if (max != null) next = Math.min(max, next);
  return next;
}

function numberInputProps(value) {
  const displayValue = value === 0 ? "" : (value ?? "");
  return {
    value: displayValue,
    onFocus: (e) => {
      if (String(e.target.value) === "0") e.target.select();
    },
    onClick: (e) => {
      if (String(e.target.value) === "0") e.target.select();
    },
  };
}

function resolveUnitDraftValue(row) {
  const code = (row?.unit || "").trim();
  const unitMeta = UNIT_LIBRARY_MAP.get(code);
  const custom = (row?.custom_unit_label || row?.unit_snapshot || "").trim();
  if (code === "OTHER") return custom ? `OTHER — ${custom}` : "OTHER — Other";
  if (unitMeta) return `${unitMeta.code} — ${unitMeta.label}`;
  return custom || code;
}

function applyPickedUnit(row, picked) {
  if (!picked) return row;
  const isOther = picked.code === "OTHER";
  return {
    ...row,
    unit: picked.code,
    unit_code: picked.code,
    unit_snapshot: picked.label,
    custom_unit_label: isOther ? (row?.custom_unit_label || "") : "",
  };
}

function updateOtherUnitDescription(row, raw) {
  const typed = (raw || "").trim();
  return {
    ...row,
    unit: "OTHER",
    unit_code: "OTHER",
    unit_snapshot: typed ? `Other — ${typed}` : "Other",
    custom_unit_label: typed,
  };
}

function numericFieldClass() {
  return "w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm";
}

function buildWorkBlockPreview(data) {
  const costRows = (data.cost_code_quantities || []).filter((row) =>
    Number(row?.installed_quantity || 0) > 0 || String(row?.notes || "").trim() || String(row?.cost_code || "").trim()
  );
  if (costRows.length > 0) {
    return costRows.map((row, index) => ({
      id: row.row_id || row.cost_code || `cost-row-${index}`,
      title: row.item_name || row.cost_code || `Work Block ${index + 1}`,
      code: row.customer_pay_item_number || row.cost_code || "No governed code yet",
      quantity: row.installed_quantity || "0",
      unit: row.unit_of_measure || row.unit || "",
      activity: row.cpm_activity_name || row.cpm_activity_id || "",
      crewCount: (data.masci_crews || []).length,
      equipmentCount: (data.equipment || []).length,
      materialCount: (data.materials || []).length,
      sourceMode: "cost-code-linked",
    }));
  }
  const productionRows = (data.production || []).filter((row) =>
    Number(row?.quantity || 0) > 0 || String(row?.description || "").trim()
  );
  if (productionRows.length > 0) {
    return productionRows.map((row, index) => ({
      id: row.row_id || `production-row-${index}`,
      title: row.description || `Work Block ${index + 1}`,
      code: row.cost_code || "No governed code yet",
      quantity: row.quantity || "0",
      unit: row.unit || "",
      activity: row.schedule_activity_name || row.activity_code || "",
      crewCount: (data.masci_crews || []).length,
      equipmentCount: (data.equipment || []).length,
      materialCount: (data.materials || []).length,
      sourceMode: "production-linked",
    }));
  }
  if ((data.masci_crews || []).length || (data.equipment || []).length || (data.materials || []).length) {
    return [{
      id: "general-field-work",
      title: "General Field Work",
      code: "Derived from report resources",
      quantity: "0",
      unit: "",
      activity: "",
      crewCount: (data.masci_crews || []).length,
      equipmentCount: (data.equipment || []).length,
      materialCount: (data.materials || []).length,
      sourceMode: "resource-linked",
    }];
  }
  return [];
}

function VoiceToReportCard({ data, patch }) {
  const { t } = useT();
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [voiceMode, setVoiceMode] = useState("work_performed");
  const [lastVoiceDraft, setLastVoiceDraft] = useState("");

  const applyVoiceDraft = (englishText, mode) => {
    const cleanText = String(englishText || "").trim();
    if (!cleanText) return;
    if (mode === "activities") {
      const next = [...(data.production || [])];
      next.push({ description: cleanText, quantity: 0, unit: "LF", unit_snapshot: "Linear Feet", notes: "Voice draft" });
      patch({ production: next, activities: [...(data.activities || []), { description: cleanText, notes: "Voice draft" }] });
    } else {
      const ns = data.narrative_sections || {};
      patch({ narrative_sections: { ...ns, work_completed: [ns.work_completed, cleanText].filter(Boolean).join(" ").trim() } });
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === "inactive") return;
    mediaRecorderRef.current.stop();
  };

  const startRecording = async () => {
    if (busy || recording) return;
    if (!navigator?.mediaDevices?.getUserMedia) {
      toast.error(t("Voice capture is not available on this device."));
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        setRecording(false);
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (!blob.size) return;
        setBusy(true);
        try {
          const form = new FormData();
          form.append("audio", new File([blob], "voice-note.webm", { type: "audio/webm" }));
          form.append("field_hint", voiceMode);
          form.append("language_hint", "auto");
          form.append("project_number", String(data.project_number || ""));
          const { data: response } = await api.post("/transcribe", form, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          const englishText = String(response?.english_text || response?.work_performed || response?.activities || "").trim();
          setLastVoiceDraft(englishText);
          applyVoiceDraft(englishText, voiceMode);
          toast.success(t("Voice note translated to English and added."));
        } catch (error) {
          toast.error(error?.response?.data?.detail || t("Voice note could not be processed."));
        } finally {
          setBusy(false);
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      toast.error(t("Microphone permission is required to record."));
    }
  };

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4" data-testid="dr-v3-voice-report-card">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
            <Languages className="h-3.5 w-3.5" /> {t("Voice to report")}
          </div>
          <p className="mt-1 text-sm text-slate-700" data-testid="dr-v3-voice-report-helper">
            {t("Hold the mic, speak in any language, and I’ll add English text to Work Performed or Activities.")}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setVoiceMode("work_performed")}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${voiceMode === "work_performed" ? "bg-slate-900 text-white" : "bg-white text-slate-700 border border-slate-200"}`}
            data-testid="dr-v3-voice-mode-work"
          >
            {t("Work Performed")}
          </button>
          <button
            type="button"
            onClick={() => setVoiceMode("activities")}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${voiceMode === "activities" ? "bg-slate-900 text-white" : "bg-white text-slate-700 border border-slate-200"}`}
            data-testid="dr-v3-voice-mode-activities"
          >
            {t("Activities")}
          </button>
        </div>
      </div>
      <button
        type="button"
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={stopRecording}
        onTouchStart={(e) => { e.preventDefault(); startRecording(); }}
        onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }}
        disabled={busy}
        className={`mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-4 text-sm font-semibold transition-colors ${recording ? "bg-red-600 text-white" : "bg-slate-900 text-white hover:bg-slate-800"} ${busy ? "opacity-70" : ""}`}
        data-testid="dr-v3-voice-record-button"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic className="h-4 w-4" />}
        {recording ? t("Recording — release to insert") : busy ? t("Translating to English…") : t("Hold to speak")}
      </button>
      {lastVoiceDraft ? (
        <div className="mt-3 rounded-xl bg-white/90 p-3 text-sm text-slate-700" data-testid="dr-v3-voice-last-draft">
          {lastVoiceDraft}
        </div>
      ) : null}
    </div>
  );
}

// ── Shared section shell ──────────────────────────────────────────
export function SectionShell({ step, title, testId, right = null, children }) {
  const { t } = useT();
  return (
    <section
      data-testid={testId}
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
            {step}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">{title}</h2>
        </div>
        {right}
      </header>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

const rowBtn =
  "inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100";

// ── Section 02 · Crew + Equipment ─────────────────────────────────
export function SectionCrewEquipment({ data, patch, costCodes }) {
  const { t } = useT();
  const crews = useMemo(() => (data.masci_crews || []), [data.masci_crews]);
  const equipment = useMemo(() => (data.equipment || []), [data.equipment]);
  const subs = useMemo(() => (data.subcontractors || []), [data.subcontractors]);
  const hasCodes = (costCodes?.length || 0) > 0;

  // TRACK 23.4C · Keep a live roster reference so typed-and-blur
  // (Jaymn Judd path) still resolves against Employee Master. This
  // closes the gap where EmployeeCombo only fires onPick when the
  // user *clicks* a dropdown item. Same roster the picker uses.
  const rosterRef = React.useRef(null);
  React.useEffect(() => {
    let alive = true;
    fetchHrRoster({ publicFallback: true })
      .then((items) => { if (alive) rosterRef.current = items || []; })
      .catch(() => { if (alive) rosterRef.current = []; });
    return () => { alive = false; };
  }, []);

  const _applyHrPick = (i, emp, currentRow) => {
    const hr = pickHrFields(emp);
    updateCrew(i, {
      name: hr.name || currentRow.name,
      employee_id: hr.employee_id || currentRow.employee_id || "",
      employee_name_snapshot: hr.name || currentRow.name || "",
      trade: hr.trade || currentRow.trade || "",
      trade_snapshot: hr.trade || currentRow.trade || "",
      trade_autofilled: !!hr.trade,
      crew_snapshot: hr.crew,
      division_snapshot: hr.crew,
      supervisor_snapshot: hr.supervisor,
      // TRACK 23.5 · normalized display snapshots. Downstream (ODS
      // labor_fact / PDF / HR Time Verification / Payroll Variance /
      // PM Intelligence) reads these keys directly.
      trade_role_display: hr.trade,
      crew_display: hr.crew,
      supervisor_display: hr.supervisor,
    });
  };

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
      step={t("Step 2 · Who was there?")}
      title={t("Crew, Equipment & Subcontractors")}
      testId="dr-v3-section-crew-equipment"
    >
      {/* ═════════════════════════════════════════════════════════ */}
      {/* Crew · start / stop / lunch / calculated hours            */}
      {/* ═════════════════════════════════════════════════════════ */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Users className="h-4 w-4 text-red-700" />{t("MASCI Crew")}</div>
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
            <Plus className="mr-1 h-4 w-4" />{t("Add crew")}</Button>
        </div>
        {crews.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">{t("No MASCI crew today.")}</p>
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
                  publicFallback
                  onChange={(name) => {
                    // TRACK 23.4C · Resolve the typed name against the
                    // HR roster. TRACK 26.12 fix: only autofill when the
                    // typed value is an EXACT match. The previous
                    // single-partial-match resolve fired on every
                    // keystroke and REPLACED the value mid-typing
                    // ("Jaym" → "Jaymn Judd" while the user kept
                    // typing → "Jaymn Juddmn Judd" + update-depth
                    // errors under fast input). Dropdown onPick still
                    // covers partial selection.
                    const roster = rosterRef.current;
                    const emp = resolveEmployeeByTypedName(name, roster);
                    const typed = (name || "").trim().toLowerCase();
                    const exact = emp && [
                      emp.name, emp.legal_name, emp.preferred_name,
                      emp.display_name, emp.employee_id,
                    ].some((v) => (v || "").trim().toLowerCase() === typed);
                    if (exact) {
                      _applyHrPick(i, emp, { ...c, name });
                    } else {
                      updateCrew(i, { name });
                    }
                  }}
                  onPick={(emp) => _applyHrPick(i, emp, c)}
                  testId={`dr-v3-crew-name-${i}`}
                />
                <div className="min-w-0">
                  <input
                    type="text"
                    placeholder={
                      c.name && !c.trade
                        ? "Trade not on employee record"
                        : "Trade"
                    }
                    value={c.trade || ""}
                    onChange={(e) => updateCrew(i, { trade: e.target.value, trade_snapshot: e.target.value, trade_autofilled: false })}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                    data-testid={`dr-v3-crew-trade-${i}`}
                  />
                  {c.trade && c.trade_autofilled && (
                    <p
                      className="mt-0.5 text-[11px] text-emerald-700"
                      data-testid={`dr-v3-crew-trade-autofill-${i}`}
                    >{t("Auto-filled from HR")}</p>
                  )}
                  {(c.crew_snapshot || c.supervisor_snapshot) && (
                    <p
                      className="mt-0.5 truncate text-[11px] text-slate-500"
                      data-testid={`dr-v3-crew-hr-meta-${i}`}
                    >
                      {[
                        c.crew_snapshot && `Crew: ${c.crew_snapshot}`,
                        c.supervisor_snapshot && `Sup: ${c.supervisor_snapshot}`,
                      ].filter(Boolean).join(" · ")}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className={rowBtn}
                  onClick={() =>
                    patch({ masci_crews: crews.filter((_, j) => j !== i) })
                  }
                  data-testid={`dr-v3-crew-remove-${i}`}
                  aria-label={t("Remove crew row")}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Time row */}
              <div className="mt-2 grid gap-2 sm:grid-cols-4">
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">{t("Start")}</span>
                  <input
                    type="time"
                    value={c.start_time || ""}
                    onChange={(e) => updateCrew(i, { start_time: e.target.value })}
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-start-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">{t("Stop")}</span>
                  <input
                    type="time"
                    value={c.stop_time || ""}
                    onChange={(e) => updateCrew(i, { stop_time: e.target.value })}
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-stop-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">{t("Lunch (min)")}</span>
                  <input
                    type="number"
                    min="0"
                    step="5"
                    placeholder="0"
                    {...numberInputProps(c.lunch_minutes)}
                    onChange={(e) =>
                      updateCrew(i, {
                        lunch_minutes: parseNumericField(normalizeNumericInputValue(e.target.value), {
                          integer: true,
                          min: 0,
                        }),
                      })
                    }
                    className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                    data-testid={`dr-v3-crew-lunch-${i}`}
                  />
                </label>
                <label className="flex flex-col text-xs text-slate-600">
                  <span className="mb-0.5">{t("Hours (auto)")}</span>
                  <input
                    type="number"
                    step="0.25"
                    min="0"
                    {...numberInputProps(c.hours)}
                    onChange={(e) => {
                      const next = crews.slice();
                      next[i] = {
                        ...c,
                        hours: parseNumericField(normalizeNumericInputValue(e.target.value), { min: 0 }),
                      };
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
                  <AlertTriangle className="h-3 w-3" />{t("Stop must be after start. Use overnight only if stop wraps past midnight.")}</p>
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
            <Wrench className="h-4 w-4 text-red-700" />{t("Equipment")}</div>
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
            <Plus className="mr-1 h-4 w-4" />{t("Add equipment")}</Button>
        </div>
        {equipment.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">{t("No equipment today.")}</p>
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
                aria-label={t("Remove equipment row")}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">{t("Run hours")}</span>
                <input
                  type="number"
                  step="0.25"
                  min="0"
                  placeholder="0.00"
                  {...numberInputProps(e.hours_used)}
                  onChange={(ev) => {
                    const runValue = parseNumericField(normalizeNumericInputValue(ev.target.value), { min: 0 });
                    const next = equipment.slice();
                    next[i] = {
                      ...e,
                      hours_used: runValue,
                      run_time: runValue,
                    };
                    patch({ equipment: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-eq-hours-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">{t("Idle hours")}</span>
                <input
                  type="number"
                  step="0.25"
                  min="0"
                  placeholder="0.00"
                  {...numberInputProps(e.idle_hours)}
                  onChange={(ev) => {
                    const idleValue = parseNumericField(normalizeNumericInputValue(ev.target.value), { min: 0 });
                    const next = equipment.slice();
                    next[i] = {
                      ...e,
                      idle_hours: idleValue,
                      idle_time: idleValue,
                    };
                    patch({ equipment: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-eq-idle-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">{t("Total (run + idle)")}</span>
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
              placeholder={t("Issues / notes (optional)")}
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
            {t("Subcontractors & Vendors")}
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
            <Plus className="mr-1 h-4 w-4" />{t("Add sub / vendor")}</Button>
        </div>
        {subs.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">{t("No subcontractors or vendors on site today.")}</p>
        )}
        {subs.map((s, i) => (
          <div
            key={i}
            data-testid={`dr-v3-sub-row-${i}`}
            className="rounded-xl border border-slate-200 p-3"
          >
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-[minmax(0,2.2fr)_minmax(0,1.05fr)_minmax(0,1.05fr)_auto]">
              <SupplierCombo
                value={s.company || ""}
                onChange={(v) => {
                  const next = subs.slice();
                  next[i] = { ...s, company: v };
                  patch({ subcontractors: next });
                }}
                placeholder={t("Pick a subcontractor / vendor — or type")}
                data-testid={`dr-v3-sub-company-${i}`}
                className="md:col-span-2 xl:col-span-1"
              />
              <input
                type="text"
                placeholder={t("Trade / scope")}
                value={s.trade || ""}
                onChange={(ev) => {
                  const next = subs.slice();
                  next[i] = { ...s, trade: ev.target.value };
                  patch({ subcontractors: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-3 py-2.5 text-[0.95rem]"
                data-testid={`dr-v3-sub-trade-${i}`}
              />
              <input
                type="text"
                placeholder={t("Foreman / contact")}
                value={s.foreman || ""}
                onChange={(ev) => {
                  const next = subs.slice();
                  next[i] = { ...s, foreman: ev.target.value };
                  patch({ subcontractors: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-3 py-2.5 text-[0.95rem]"
                data-testid={`dr-v3-sub-foreman-${i}`}
              />
              <button
                type="button"
                className={rowBtn + " justify-self-end xl:self-start"}
                onClick={() =>
                  patch({
                    subcontractors: subs.filter((_, j) => j !== i),
                  })
                }
                data-testid={`dr-v3-sub-remove-${i}`}
                aria-label={t("Remove subcontractor row")}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr_3fr]">
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">{t("Headcount")}</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                    {...numberInputProps(s.count)}
                  onChange={(ev) => {
                    const next = subs.slice();
                    next[i] = {
                      ...s,
                        count: parseNumericField(normalizeNumericInputValue(ev.target.value), {
                          integer: true,
                          min: 0,
                        }),
                    };
                    patch({ subcontractors: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-sub-count-${i}`}
                />
              </label>
              <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-0.5">{t("Hours")}</span>
                <input
                  type="number"
                  min="0"
                  step="0.25"
                    {...numberInputProps(s.hours)}
                  onChange={(ev) => {
                    const next = subs.slice();
                    next[i] = {
                      ...s,
                        hours: parseNumericField(normalizeNumericInputValue(ev.target.value), { min: 0 }),
                    };
                    patch({ subcontractors: next });
                  }}
                  className="rounded-md border border-slate-300 px-2 py-2 text-sm"
                  data-testid={`dr-v3-sub-hours-${i}`}
                />
              </label>
              <input
                type="text"
                placeholder={t("Work performed / notes")}
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
  const { t } = useT();
  if (!options || options.length === 0) return null;
  return (
    <div className="mt-2">
      <label className="mb-1 block text-xs font-medium text-slate-500">{t("Cost code")}</label>
      <select
        data-testid={testId}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="wp17-native-select"
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
export function SectionWorkProduction({ data, patch, costCodes, projectCostAssignments = [], projectCostProgress = null }) {
  const { t } = useT();
  const prod = data.production || [];
  const costQuantities = data.cost_code_quantities || [];
  const hasCodes = (costCodes?.length || 0) > 0;
  const workBlockPreview = useMemo(() => buildWorkBlockPreview(data), [data]);

  const updateCostQuantity = (index, delta) => {
    const next = costQuantities.slice();
    next[index] = { ...next[index], ...delta };
    patch({ cost_code_quantities: next });
  };

  return (
    <SectionShell
      step={t("Step 3 · What got done?")}
      title={t("Work Performed & Production")}
      testId="dr-v3-section-work"
    >
      <div className="space-y-3">
        <VoiceToReportCard data={data} patch={patch} />
        <div className="rounded-2xl border border-blue-100 bg-blue-50/70 p-4" data-testid="dr-v3-cost-quantity-card">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">{t("Field quantity tracking")}</div>
              <p className="mt-1 text-sm text-slate-700" data-testid="dr-v3-cost-quantity-helper">
                {t("Assigned project cost codes appear here so crews can log today’s installed quantity against bid quantity.")}
              </p>
            </div>
            {projectCostProgress ? (
              <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700" data-testid="dr-v3-cost-progress-pill">
                {t("Job progress")}: {Number(projectCostProgress?.overall_percent_complete || 0).toFixed(2)}%
              </div>
            ) : null}
          </div>
          {projectCostAssignments.length === 0 ? (
            <p className="mt-3 rounded-xl bg-white/80 px-3 py-2 text-sm text-slate-500" data-testid="dr-v3-cost-quantity-empty">
              {t("No assigned project cost codes yet. PM job setup will populate this section.")}
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {costQuantities.map((row, index) => {
                const progressRow = (projectCostProgress?.codes || []).find((item) => item.code === row.cost_code);
                return (
                  <div key={row.row_id || row.cost_code || index} className="rounded-xl border border-blue-100 bg-white/90 p-3" data-testid={`dr-v3-cost-quantity-row-${index}`}>
                    <div className="grid gap-3 lg:grid-cols-[1.25fr_0.7fr_0.8fr_1fr]">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{row.cost_code} · {row.item_name || t("Assigned code")}</div>
                        <div className="mt-1 text-xs text-slate-500" data-testid={`dr-v3-cost-quantity-row-meta-${index}`}>
                          {t("Authorized Qty")}: {progressRow?.authorized_quantity ?? progressRow?.bid_quantity ?? "—"} {row.unit_of_measure || ""}
                          {row.cpm_activity_id ? ` · CPM ${row.cpm_activity_id}` : ""}
                          {row.schedule_phase ? ` · ${row.schedule_phase}` : ""}
                        </div>
                        <div className="mt-2 text-xs text-slate-600" data-testid={`dr-v3-cost-quantity-planned-performer-${index}`}>
                          {t("Planned performer")}: {row.planned_performer || t("Not assigned")}
                        </div>
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Installed today")}</label>
                        <input
                          type="number"
                          step="0.01"
                          value={row.installed_quantity ?? ""}
                          onChange={(e) => updateCostQuantity(index, { installed_quantity: e.target.value })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          data-testid={`dr-v3-cost-quantity-input-${index}`}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Unit")}</label>
                        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700" data-testid={`dr-v3-cost-quantity-unit-${index}`}>
                          {row.unit_of_measure || "—"}
                        </div>
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Notes")}</label>
                        <input
                          type="text"
                          value={row.notes || ""}
                          onChange={(e) => updateCostQuantity(index, { notes: e.target.value })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          data-testid={`dr-v3-cost-quantity-notes-${index}`}
                        />
                      </div>
                    </div>
                    <div className="mt-3 grid gap-3 lg:grid-cols-4">
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Actual performer")}</label>
                        <input
                          type="text"
                          value={row.actual_performer || ""}
                          onChange={(e) => updateCostQuantity(index, { actual_performer: e.target.value })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          data-testid={`dr-v3-cost-quantity-actual-performer-${index}`}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Location")}</label>
                        <input
                          type="text"
                          value={row.location || ""}
                          onChange={(e) => updateCostQuantity(index, { location: e.target.value })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          data-testid={`dr-v3-cost-quantity-location-${index}`}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Work area")}</label>
                        <input
                          type="text"
                          value={row.work_area || ""}
                          onChange={(e) => updateCostQuantity(index, { work_area: e.target.value })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          data-testid={`dr-v3-cost-quantity-work-area-${index}`}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{t("Evidence links")}</label>
                        <input
                          type="text"
                          value={(row.evidence_links || []).join(", ")}
                          onChange={(e) => updateCostQuantity(index, { evidence_links: e.target.value.split(",").map((part) => part.trim()).filter(Boolean) })}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          placeholder={t("Comma-separated links or refs")}
                          data-testid={`dr-v3-cost-quantity-evidence-links-${index}`}
                        />
                      </div>
                    </div>
                    {progressRow ? (
                      <div className="mt-2 text-xs text-slate-600" data-testid={`dr-v3-cost-quantity-progress-${index}`}>
                        {t("Overall")}: {Number(progressRow.progress_percent || 0).toFixed(2)}% · {t("Installed to date")}: {progressRow.installed_quantity} / {progressRow.authorized_quantity || progressRow.bid_quantity} {progressRow.unit_of_measure}
                        {Number(progressRow.overrun_quantity || 0) > 0 ? ` · ${t("Overrun")}: ${progressRow.overrun_quantity}` : ""}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">{t("Production rows")}</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-prod-add"
            onClick={() =>
              patch({
                production: [
                  ...prod,
                  { description: "", quantity: 0, unit: "LF", unit_snapshot: "Linear Feet", notes: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" />{t("Add row")}</Button>
        </div>
        <div className="rounded-2xl border border-violet-100 bg-violet-50/70 p-4" data-testid="dr-v3-work-block-preview-card">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-700">{t("Governed work blocks")}</div>
              <p className="mt-1 text-sm text-slate-700" data-testid="dr-v3-work-block-preview-helper">
                {t("The system will preserve today's field entries and build governed work blocks from production, cost-code quantities, crews, equipment, materials, and constraints without replacing the Daily Report.")}
              </p>
            </div>
            <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700" data-testid="dr-v3-work-block-preview-count">
              {t("Preview blocks")}: {workBlockPreview.length}
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {workBlockPreview.length === 0 ? (
              <div className="rounded-xl bg-white/90 px-3 py-2 text-sm text-slate-500" data-testid="dr-v3-work-block-preview-empty">
                {t("Enter production, a cost-code quantity, or report-level resources to preview governed work blocks.")}
              </div>
            ) : workBlockPreview.map((row, index) => (
              <div key={row.id} className="rounded-xl border border-violet-100 bg-white/90 p-3" data-testid={`dr-v3-work-block-preview-row-${index}`}>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{row.title}</div>
                    <div className="mt-1 text-xs text-slate-500">{row.code}{row.activity ? ` · ${row.activity}` : ""}</div>
                  </div>
                  <span className="rounded-full bg-violet-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-violet-700">{row.sourceMode}</span>
                </div>
                <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-4">
                  <div data-testid={`dr-v3-work-block-preview-qty-${index}`}>{t("Installed")}: <span className="font-semibold text-slate-900">{row.quantity}</span> {row.unit}</div>
                  <div>{t("Crew rows")}: <span className="font-semibold text-slate-900">{row.crewCount}</span></div>
                  <div>{t("Equipment rows")}: <span className="font-semibold text-slate-900">{row.equipmentCount}</span></div>
                  <div>{t("Material rows")}: <span className="font-semibold text-slate-900">{row.materialCount}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
        {prod.length === 0 && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">{t("No production tracked today.")}</p>
        )}
        {prod.map((p, i) => (
          <div
            key={i}
            data-testid={`dr-v3-prod-row-${i}`}
            className="rounded-xl border border-slate-200 p-3"
          >
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,3fr)_minmax(0,1fr)_minmax(0,1.4fr)_auto]">
              <input
                type="text"
                placeholder={t("What was installed / performed")}
                value={p.description || ""}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, description: e.target.value };
                  patch({ production: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-prod-desc-${i}`}
              />
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Production Quantity")}</span>
              <input
                type="number"
                step="0.01"
                placeholder="0"
                {...numberInputProps(p.quantity)}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = {
                    ...p,
                    quantity: parseNumericField(normalizeNumericInputValue(e.target.value), { min: 0 }),
                  };
                  patch({ production: next });
                }}
                className={numericFieldClass()}
                data-testid={`dr-v3-prod-qty-${i}`}
              />
              </label>
              <UnitCombo
                value={resolveUnitDraftValue(p)}
                selectedCode={p.unit || ""}
                onChange={() => {}}
                onPick={(u) => {
                  const next = prod.slice();
                  next[i] = applyPickedUnit(p, u);
                  patch({ production: next });
                }}
                testId={`dr-v3-prod-unit-${i}`}
              />
              <button
                type="button"
                className={rowBtn + " justify-self-end shrink-0"}
                onClick={() => patch({ production: prod.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-prod-remove-${i}`}
                aria-label={t("Remove production row")}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            {/* TRACK 23.4B · Station from/to + percent complete — critical
                for linear heavy-civil work (road, pipeline, MOT). Feeds
                PM linear-progress KPIs and downstream schedule linkage. */}
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder={t("Sta from (e.g. 12+00)")}
                value={p.station_from || ""}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, station_from: e.target.value };
                  patch({ production: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
                data-testid={`dr-v3-prod-sta-from-${i}`}
              />
              <input
                type="text"
                placeholder={t("Sta to (e.g. 15+50)")}
                value={p.station_to || ""}
                onChange={(e) => {
                  const next = prod.slice();
                  next[i] = { ...p, station_to: e.target.value };
                  patch({ production: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
                data-testid={`dr-v3-prod-sta-to-${i}`}
              />
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Percent Complete")}</span>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                placeholder="0"
                {...numberInputProps(p.percent_complete)}
                onChange={(e) => {
                  const next = prod.slice();
                  const v = parseNumericField(normalizeNumericInputValue(e.target.value), {
                    integer: true,
                    min: 0,
                    max: 100,
                  });
                  next[i] = { ...p, percent_complete: v };
                  patch({ production: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
                data-testid={`dr-v3-prod-percent-${i}`}
              />
              </label>
            </div>
            {p.unit === "OTHER" && (
              <label className="mt-2 flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Other Unit Description")}</span>
                <input
                  type="text"
                  placeholder={t("Short unit description")}
                  value={p.custom_unit_label || ""}
                  onChange={(e) => {
                    const next = prod.slice();
                    next[i] = updateOtherUnitDescription(p, e.target.value);
                    patch({ production: next });
                  }}
                  className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                  data-testid={`dr-v3-prod-other-unit-${i}`}
                />
              </label>
            )}
            <input
              type="text"
              placeholder={t("Notes (optional)")}
              value={p.notes || ""}
              onChange={(e) => {
                const next = prod.slice();
                next[i] = { ...p, notes: e.target.value };
                patch({ production: next });
              }}
              className="mt-2 w-full min-w-0 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
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
  const { t } = useT();
  const mats = data.materials || [];
  const outs = data.outbound_materials || [];
  const hasCodes = (costCodes?.length || 0) > 0;
  return (
    <SectionShell
      step={t("Step 4 · What moved?")}
      title={t("Materials & Tickets")}
      testId="dr-v3-section-materials"
    >
      {/* Materials in */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">{t("Materials delivered")}</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-mat-add"
            onClick={() =>
              patch({
                materials: [
                  ...mats,
                  { description: "", quantity: 0, unit: "TON", unit_snapshot: "Tons", supplier: "", ticket_number: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" />{t("Delivered")}</Button>
        </div>
        {mats.map((m, i) => (
          <div key={i} data-testid={`dr-v3-mat-row-${i}`} className="rounded-xl border border-slate-200 p-3">
            {/* Row 1 · Material · Qty · Unit · Delete */}
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,3fr)_minmax(0,1fr)_minmax(0,1.4fr)_auto]">
              <input
                type="text"
                placeholder={t("Material")}
                value={m.description || ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, description: e.target.value };
                  patch({ materials: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-mat-desc-${i}`}
              />
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Material Quantity")}</span>
              <input
                type="number"
                step="0.01"
                placeholder="0"
                {...numberInputProps(m.quantity)}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = {
                    ...m,
                    quantity: parseNumericField(normalizeNumericInputValue(e.target.value), { min: 0 }),
                  };
                  patch({ materials: next });
                }}
                className={numericFieldClass()}
                data-testid={`dr-v3-mat-qty-${i}`}
              />
              </label>
              <UnitCombo
                value={resolveUnitDraftValue(m)}
                selectedCode={m.unit || ""}
                onChange={() => {}}
                onPick={(u) => {
                  const next = mats.slice();
                  next[i] = applyPickedUnit(m, u);
                  patch({ materials: next });
                }}
                testId={`dr-v3-mat-unit-${i}`}
              />
              <button
                type="button"
                className={rowBtn + " justify-self-end shrink-0"}
                onClick={() => patch({ materials: mats.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-mat-remove-${i}`}
                aria-label={t("Remove material row")}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            {m.unit === "OTHER" && (
              <label className="mt-2 flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Other Unit Description")}</span>
                <input
                  type="text"
                  placeholder={t("Short unit description")}
                  value={m.custom_unit_label || ""}
                  onChange={(e) => {
                    const next = mats.slice();
                    next[i] = updateOtherUnitDescription(m, e.target.value);
                    patch({ materials: next });
                  }}
                  className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                  data-testid={`dr-v3-mat-other-unit-${i}`}
                />
              </label>
            )}

            {/* Row 2 · Carrier — canonical SupplierCombo (single source of truth) */}
            <div className="mt-2 min-w-0">
              <label className="mb-1 block text-xs font-medium text-slate-600">{t("Carrier")} <span className="text-red-600">*</span>
              </label>
              <SupplierCombo
                value={m.carrier || ""}
                onChange={(v) => {
                  const next = mats.slice();
                  next[i] = { ...m, carrier: v };
                  patch({ materials: next });
                }}
                onPick={(sup) => {
                  const next = mats.slice();
                  next[i] = {
                    ...m,
                    carrier: sup?.name || m.carrier,
                    carrier_id: sup?.id || sup?.supplier_id || "",
                    carrier_name_snapshot: sup?.name || m.carrier || "",
                  };
                  patch({ materials: next });
                }}
                placeholder={t("Pick carrier — or type one-time hauler")}
                data-testid={`dr-v3-mat-carrier-${i}`}
              />
            </div>

            {/* Row 3 · Ticket # + Photos */}
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <input
                type="text"
                placeholder={t("Ticket #")}
                value={m.ticket_number || ""}
                onChange={(e) => {
                  const next = mats.slice();
                  next[i] = { ...m, ticket_number: e.target.value };
                  patch({ materials: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-200 px-2.5 py-1.5 text-sm"
                data-testid={`dr-v3-mat-ticket-${i}`}
              />
              <div className="min-w-0">
                <PhotoUpload
                  photos={m.ticket_photos || []}
                  onChange={(next) => {
                    const rows = mats.slice();
                    rows[i] = { ...m, ticket_photos: next };
                    patch({ materials: rows });
                  }}
                  placeholderLabel="Add ticket photo"
                  testIdBase={`dr-v3-mat-ticketphoto-${i}`}
                />
              </div>
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
          <div className="text-sm font-medium text-slate-700">{t("Hauled off / outbound")}</div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-out-add"
            onClick={() =>
              patch({
                outbound_materials: [
                  ...outs,
                  { material: "", quantity: 0, unit: "LOAD", unit_snapshot: "Loads", hauler: "", destination: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" />{t("Outbound")}</Button>
        </div>
        {outs.map((o, i) => (
          <div key={i} data-testid={`dr-v3-out-row-${i}`} className="rounded-xl border border-slate-200 p-3">
            {/* Row 1 · Material · Qty · Unit · Delete */}
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,3fr)_minmax(0,1fr)_minmax(0,1.4fr)_auto]">
              <input
                type="text"
                placeholder={t("Material")}
                value={o.material || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, material: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-mat-${i}`}
              />
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Outbound Quantity")}</span>
              <input
                type="number"
                step="0.01"
                placeholder="0"
                {...numberInputProps(o.quantity)}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = {
                    ...o,
                    quantity: parseNumericField(normalizeNumericInputValue(e.target.value), { min: 0 }),
                  };
                  patch({ outbound_materials: next });
                }}
                className={numericFieldClass()}
                data-testid={`dr-v3-out-qty-${i}`}
              />
              </label>
              <UnitCombo
                value={resolveUnitDraftValue(o)}
                selectedCode={o.unit || ""}
                onChange={() => {}}
                onPick={(u) => {
                  const next = outs.slice();
                  next[i] = applyPickedUnit(o, u);
                  patch({ outbound_materials: next });
                }}
                testId={`dr-v3-out-unit-${i}`}
              />
              <button
                type="button"
                className={rowBtn + " justify-self-end shrink-0"}
                onClick={() => patch({ outbound_materials: outs.filter((_, j) => j !== i) })}
                data-testid={`dr-v3-out-remove-${i}`}
                aria-label={t("Remove outbound row")}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            {o.unit === "OTHER" && (
              <label className="mt-2 flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">{t("Other Unit Description")}</span>
                <input
                  type="text"
                  placeholder={t("Short unit description")}
                  value={o.custom_unit_label || ""}
                  onChange={(e) => {
                    const next = outs.slice();
                    next[i] = updateOtherUnitDescription(o, e.target.value);
                    patch({ outbound_materials: next });
                  }}
                  className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                  data-testid={`dr-v3-out-other-unit-${i}`}
                />
              </label>
            )}

            {/* Row 2 · Carrier (SupplierCombo, canonical vendor master) */}
            <div className="mt-2 min-w-0">
              <label className="mb-1 block text-xs font-medium text-slate-600">{t("Carrier")} <span className="text-red-600">*</span>
              </label>
              <SupplierCombo
                value={o.hauler || ""}
                onChange={(v) => {
                  const next = outs.slice();
                  next[i] = { ...o, hauler: v };
                  patch({ outbound_materials: next });
                }}
                onPick={(sup) => {
                  const next = outs.slice();
                  next[i] = {
                    ...o,
                    hauler: sup?.name || o.hauler,
                    hauler_id: sup?.id || sup?.supplier_id || "",
                    hauler_name_snapshot: sup?.name || o.hauler || "",
                  };
                  patch({ outbound_materials: next });
                }}
                placeholder={t("Pick carrier — or type one-time hauler")}
                data-testid={`dr-v3-out-carrier-${i}`}
              />
            </div>

            {/* Row 3 · Destination · Ticket/manifest · Photos */}
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
              <input
                type="text"
                placeholder={t("Destination")}
                value={o.destination || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, destination: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-dest-${i}`}
              />
              <input
                type="text"
                placeholder={t("Manifest / ticket #")}
                value={o.ticket_number || o.manifest_number || ""}
                onChange={(e) => {
                  const next = outs.slice();
                  next[i] = { ...o, ticket_number: e.target.value };
                  patch({ outbound_materials: next });
                }}
                className="w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm"
                data-testid={`dr-v3-out-ticket-${i}`}
              />
            </div>
            <div className="mt-2 min-w-0">
              <PhotoUpload
                photos={o.ticket_photos || []}
                onChange={(next) => {
                  const rows = outs.slice();
                  rows[i] = { ...o, ticket_photos: next };
                  patch({ outbound_materials: rows });
                }}
                placeholderLabel="Add manifest / ticket photo"
                testIdBase={`dr-v3-out-photo-${i}`}
              />
            </div>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}

// ── Section 05 · Photos + Evidence ─────────────────────────────
export function SectionPhotos({ data, patch, photoMin, photoIntelStatus, onPhotoBatchStateChange, onPhotoReady }) {
  const { t } = useT();
  const photos = data.photos || [];
  const attachments = data.attachments || [];
  const short = Math.max(0, (photoMin || 6) - photos.length);
  return (
    <SectionShell
      step={t("Step 5 · What can we prove?")}
      title={t("Photos & Evidence")}
      testId="dr-v3-section-photos"
      right={
        <span
          data-testid="dr-v3-photo-count"
          className={
            "rounded-full px-3 py-1 text-xs font-medium " +
            (short === 0 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700")
          }
        >
          <Camera className="mr-1 inline h-3.5 w-3.5" /> {photos.length}/{photoMin} {t("required")}
        </span>
      }
    >
      <PhotoUpload
        photos={photos}
        onChange={(next) => patch({ photos: next })}
        photoStatuses={(photoIntelStatus?.photo_statuses || []).filter((item) => item?.source === "photos")}
        onBatchStateChange={onPhotoBatchStateChange}
        onPhotoReady={onPhotoReady}
        placeholderLabel="Add photo"
        testIdBase="dr-v3-photos"
      />
      {short > 0 && (
        <p className="mt-3 text-xs text-amber-700" data-testid="dr-v3-photo-short">
          {short === 1
            ? t("Add at least 1 more photo before submit.")
            : `${t("Add at least")} ${short} ${t("more photos before submit.")}`}
        </p>
      )}
      <div className="mt-5 border-t border-slate-200 pt-4" data-testid="dr-v3-attachments-section">
        <div className="mb-2 flex items-center justify-between gap-2">
          <div>
            <div className="text-sm font-medium text-slate-800">{t("Attachments & document evidence")}</div>
            <p className="mt-1 text-xs text-slate-500">
              {t("Upload delivery tickets, quantity spreadsheets, CEI notes, or other supporting files.")}
            </p>
          </div>
          <span
            className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
            data-testid="dr-v3-attachments-count"
          >
            {attachments.length} {attachments.length === 1 ? t("file") : t("files")}
          </span>
        </div>
        <AttachmentUpload
          attachments={attachments}
          onChange={(next) => patch({ attachments: next })}
          testIdBase="dr-v3-attachments"
        />
      </div>
    </SectionShell>
  );
}

// ── Section 06 · Combined Impact / Safety gate ────────────────
const IMPACT_TYPES = [
  { key: "weather", label: "Weather", hoursLabel: "Hours Delayed", helper: "Weather delay charged to the day." },
  { key: "material", label: "Material", hoursLabel: "Hours Delayed", helper: "Material wait or shortage time." },
  { key: "equipment", label: "Equipment", hoursLabel: "Hours Delayed", helper: "Equipment downtime impacting work." },
  { key: "utility", label: "Utility Conflict", hoursLabel: "Hours Delayed", helper: "Utility conflict time affecting production." },
  { key: "inspection", label: "Inspection", hoursLabel: "Hours Delayed", helper: "Inspection-related waiting time." },
  { key: "owner_eng", label: "Owner", hoursLabel: "Hours Delayed", helper: "Owner / engineer direction delaying work." },
  { key: "subcontractor", label: "Subcontractor", hoursLabel: "Hours Delayed", helper: "Subcontractor dependency or standby time." },
  { key: "traffic_mot", label: "Traffic", hoursLabel: "Hours Delayed", helper: "Traffic / MOT restrictions slowing work." },
  { key: "extra_work", label: "Extra Work", hoursLabel: "Extra Work Hours", helper: "Additional work added beyond planned production." },
  { key: "other", label: "Other", hoursLabel: "Hours Impacted", helper: "Use only when no standard delay type fits." },
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
  const { t } = useT();
  const anyImpact = data.impact_present === "Yes";
  const anySafety = data.safety_present === "Yes";
  const constraints = data.constraints || [];
  const visitors = data.visitors || [];

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
      step={t("Step 6 · What impacted today?")}
      title={t("Delays, Extra Work & Safety")}
      testId="dr-v3-section-impact-safety"
    >
      {/* Impact gate */}
      <div className="rounded-xl border border-slate-200 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <TrafficCone className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-medium text-slate-800">{t("Did anything reduce or add to production today?")}</span>
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
            <p className="mb-2 text-xs text-slate-500">{t("Tap a type to add a row.")}</p>
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
                    <div className="min-w-0">
                      <span className="text-xs font-medium text-slate-700">
                        {IMPACT_TYPES.find((t) => t.key === c.constraint_type)?.label || c.constraint_type}
                      </span>
                      <p className="mt-1 text-[11px] text-slate-500" data-testid={`dr-v3-constraint-helper-${i}`}>
                        {t(IMPACT_TYPES.find((t) => t.key === c.constraint_type)?.helper || "Describe the impact on today’s work.")}
                      </p>
                    </div>
                    <label className="flex flex-col gap-1">
                      <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                        {t(IMPACT_TYPES.find((t) => t.key === c.constraint_type)?.hoursLabel || "Hours Impacted")}
                      </span>
                    <input
                      type="number"
                      step="0.25"
                      placeholder="0"
                      {...numberInputProps(c.hours_impact)}
                      onChange={(e) => {
                        const next = constraints.slice();
                        next[i] = {
                          ...c,
                          hours_impact: parseNumericField(normalizeNumericInputValue(e.target.value), { min: 0 }),
                        };
                        patch({ constraints: next });
                      }}
                      className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                      data-testid={`dr-v3-constraint-hours-${i}`}
                    />
                    </label>
                    <input
                      type="text"
                      placeholder={t("What caused the delay or extra work?")}
                      value={c.notes || ""}
                      onChange={(e) => {
                        const next = constraints.slice();
                        next[i] = { ...c, notes: e.target.value };
                        patch({ constraints: next });
                      }}
                      className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                      data-testid={`dr-v3-constraint-notes-${i}`}
                    />
                    <button
                      type="button"
                      className={rowBtn}
                      onClick={() =>
                        patch({ constraints: constraints.filter((_, j) => j !== i) })
                      }
                      data-testid={`dr-v3-constraint-remove-${i}`}
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
            <span className="text-sm font-medium text-slate-800">{t("Did anything safety-related occur today?")}</span>
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
              <label className="mb-1 block text-xs font-medium text-slate-600">{t("What kind of event?")} <span className="text-red-600">*</span>
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
                className="wp17-native-select"
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
              placeholder={t("What happened? (required for supervisor review)")}
              value={data.incident_notes || ""}
              onChange={(e) => patch({ incident_notes: e.target.value })}
              data-testid="dr-v3-incident-notes"
            />

            {/* ── Safety contact escalation ────────────────────── */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("Was Safety contacted?")} <span className="text-red-600">*</span>
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
                    <span className="mb-0.5">{t("Who at Safety?")} <span className="text-red-600">*</span>
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
                    <span className="mb-0.5">{t("Time contacted")} <span className="text-red-600">*</span>
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
                    <span className="mb-0.5">{t("Method")}</span>
                    <select
                      value={data.safety_contact_method || ""}
                      onChange={(e) =>
                        patch({ safety_contact_method: e.target.value })
                      }
                      className="wp17-native-select"
                      data-testid="dr-v3-safety-contact-method"
                    >
                      <option value="">— Select —</option>
                      <option value="phone">{t("Phone")}</option>
                      <option value="text">{t("Text")}</option>
                      <option value="in_person">{t("In person")}</option>
                      <option value="email">{t("Email")}</option>
                      <option value="other">{t("Other")}</option>
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
                    <AlertTriangle className="h-4 w-4" />{t("Stop and contact Safety before submitting.")}</div>
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
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("Incident / Accident report filed?")} <span className="text-red-600">*</span>
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
                    <span className="mb-0.5">{t("Time filed")} <span className="text-red-600">*</span>
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
                    <span className="mb-0.5">{t("Reference / report #")}</span>
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
                    <AlertTriangle className="h-4 w-4" />{t("Action required: file the Accident / Incident report.")}</div>
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
                    <ExternalLink className="h-3 w-3" />{t("Open Accident / Incident Report")}</Link>
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
                />{t("Injuries reported")}</label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={data.work_stopped === "Yes"}
                  onChange={(e) =>
                    patch({ work_stopped: e.target.checked ? "Yes" : "No" })
                  }
                  data-testid="dr-v3-work-stopped"
                />{t("Work stopped")}</label>
            </div>

            <p className="text-[11px] text-slate-500">
              Photos of the scene / conditions are strongly recommended.
              Add them in Step 5 · Photos &amp; Evidence.
            </p>
          </div>
        )}
      </div>

      {/* TRACK 23.4B · Visitors on site (OSHA / insurance / access log). */}
      <div className="mt-4 rounded-xl border border-slate-200 p-4" data-testid="dr-v3-visitors-block">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
            <Users className="h-4 w-4 text-slate-600" />{t("Visitors on site")}<span className="ml-1 text-[11px] text-slate-500">{t("(optional — inspectors, owners, subs' PMs)")}</span>
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            data-testid="dr-v3-visitor-add"
            onClick={() =>
              patch({
                visitors: [
                  ...visitors,
                  { name: "", company: "", time_in: "", time_out: "", purpose: "" },
                ],
              })
            }
          >
            <Plus className="mr-1 h-4 w-4" />{t("Add visitor")}</Button>
        </div>
        {visitors.length === 0 ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">{t("No outside visitors logged.")}</p>
        ) : (
          <div className="space-y-2">
            {visitors.map((v, i) => (
              <div
                key={i}
                data-testid={`dr-v3-visitor-row-${i}`}
                className="rounded-md border border-slate-200 p-2"
              >
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,2fr)_minmax(0,2fr)_auto]">
                  <input
                    type="text"
                    placeholder={t("Name")}
                    value={v.name || ""}
                    onChange={(e) => {
                      const next = visitors.slice();
                      next[i] = { ...v, name: e.target.value };
                      patch({ visitors: next });
                    }}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    data-testid={`dr-v3-visitor-name-${i}`}
                  />
                  <input
                    type="text"
                    placeholder={t("Company / affiliation")}
                    value={v.company || ""}
                    onChange={(e) => {
                      const next = visitors.slice();
                      next[i] = { ...v, company: e.target.value };
                      patch({ visitors: next });
                    }}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    data-testid={`dr-v3-visitor-company-${i}`}
                  />
                  <button
                    type="button"
                    className={rowBtn + " justify-self-end shrink-0"}
                    onClick={() =>
                      patch({ visitors: visitors.filter((_, j) => j !== i) })
                    }
                    data-testid={`dr-v3-visitor-remove-${i}`}
                    aria-label={t("Remove visitor")}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,3fr)]">
                  <input
                    type="time"
                    value={v.time_in || ""}
                    onChange={(e) => {
                      const next = visitors.slice();
                      next[i] = { ...v, time_in: e.target.value };
                      patch({ visitors: next });
                    }}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    data-testid={`dr-v3-visitor-tin-${i}`}
                    aria-label={t("Time in")}
                  />
                  <input
                    type="time"
                    value={v.time_out || ""}
                    onChange={(e) => {
                      const next = visitors.slice();
                      next[i] = { ...v, time_out: e.target.value };
                      patch({ visitors: next });
                    }}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    data-testid={`dr-v3-visitor-tout-${i}`}
                    aria-label={t("Time out")}
                  />
                  <input
                    type="text"
                    placeholder={t("Purpose")}
                    value={v.purpose || ""}
                    onChange={(e) => {
                      const next = visitors.slice();
                      next[i] = { ...v, purpose: e.target.value };
                      patch({ visitors: next });
                    }}
                    className="w-full min-w-0 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    data-testid={`dr-v3-visitor-purpose-${i}`}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </SectionShell>
  );
}

function YesNoInline({ value, onChange, testId }) {
  const { t } = useT();
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
          {t(v)}
        </button>
      ))}
    </div>
  );
}

// ── Section 07 · Tomorrow / Needs / PM Attention ────────────────
export function SectionTomorrow({ data, patch }) {
  const { t } = useT();
  const ns = data.narrative_sections || {};
  const set = (key, v) => patch({ narrative_sections: { ...ns, [key]: v } });
  return (
    <SectionShell
      step={t("Step 7 · What's next?")}
      title={t("Tomorrow & PM Attention")}
      testId="dr-v3-section-tomorrow"
    >
      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t("Tomorrow / next work")}</label>
          <Textarea
            rows={2}
            value={ns.tomorrow_plan || ""}
            onChange={(e) => set("tomorrow_plan", e.target.value)}
            placeholder={t("Which crew · what work · which station")}
            data-testid="dr-v3-tomorrow-plan"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t("Needs / blockers for the PM")}<Clock className="ml-1 inline h-3.5 w-3.5 text-slate-400" />
          </label>
          <Textarea
            rows={2}
            value={ns.follow_ups || ""}
            onChange={(e) => set("follow_ups", e.target.value)}
            placeholder={t("RFI, submittal, material, equipment, permit …")}
            data-testid="dr-v3-follow-ups"
          />
        </div>
      </div>
    </SectionShell>
  );
}

// ── Section 08 · AI shift story draft ─────────────────────────────
export function SectionAiSummary({ data, reportId, formKey, photoUploadState, onAccepted, onStateChange, onPhotoIntelChange }) {
  const { t } = useT();

  return (
    <SectionShell
      step={t("Step 8 · Shift story draft")}
      title={t("AI Shift Story")}
      testId="dr-v3-section-ai-summary"
    >
      <p className="mb-3 text-xs text-slate-500" data-testid="dr-v3-ai-summary-help">
        {t("AI analyzes the photos, weather, crew, production, notes, and every report detail to draft the story of this shift. Approve it, regenerate it, or reject AI and write your own before submit.")}
      </p>
      <DailySummaryAssist
        reportId={reportId}
        reportNumber={data.report_number}
        formKey={formKey}
        photoUploadState={photoUploadState}
        data={data}
        onStateChange={onStateChange}
        onPhotoIntelChange={onPhotoIntelChange}
        onAccept={(text, meta) => onAccepted?.({ summary: text, meta })}
      />
    </SectionShell>
  );
}

// ── Section 09 · Submit Readiness + Sign-Off ─────────────────
export function SectionSignoff({
  data, patch, readiness, onSubmit, saving, canSubmit, submitLabel, showInlineSubmit = true,
}) {
  const { t } = useT();
  return (
    <SectionShell
      step={t("Step 9 · Sign & submit")}
      title={t("Submit Readiness & Sign-Off")}
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
            <>{t("Ready to submit —")}<strong>{readiness.completed}/{readiness.total}</strong>{t(" items complete.")}</>
          ) : (
            <>
              {t("Still needed:")}{" "}
              <strong>{readiness.missing.join(" · ") || t("checking…")}</strong>
            </>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            {t("Prepared By Signature")} <span className="text-red-600">*</span>
          </label>
          <SignaturePad
            value={data.prepared_by_signature || ""}
            onChange={(v) => patch({ prepared_by_signature: v })}
            testId="dr-v3-signature"
          />
        </div>

        {showInlineSubmit ? (
          <Button
            type="button"
            className="w-full bg-emerald-600 py-6 text-base font-semibold hover:bg-emerald-700"
            disabled={!canSubmit || saving}
            onClick={onSubmit}
            data-testid="dr-v3-submit-btn"
          >
            {saving ? t("Submitting Daily Report…") : (submitLabel || t("Submit Daily Report"))}
          </Button>
        ) : null}
      </div>
    </SectionShell>
  );
}
