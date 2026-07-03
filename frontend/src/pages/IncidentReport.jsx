// Track 19.16 · Phase B1 · Incident Intelligence Engine — Field Reporting Page
// -----------------------------------------------------------------------------
// The world's fastest, calmest field incident reporting workflow.
//
// Consumes ForgedOps primitives:
//   • FormShell      — page scaffold + language toggle + sticky footer
//   • ProgressRail   — step position + percentage
//   • HelpDrawer     — contextual guidance (per step)
//   • PresenceGate   — Yes/No/Not-sure with follow-up disclosure
//   • SubmitReviewPanel — reused for the final review card (custom rows)
//
// Data path:
//   1. Field selects an incident type card.
//   2. Progressive-disclosure walk through 7 shared + 1 branch step.
//   3. Draft snapshots to localStorage on every keystroke.
//   4. Submit: POST /api/incident-cases → PATCH field_block → POST transitions
//      to FIELD_SUBMITTED → emits case.field_submitted event server-side.
//   5. Success screen shows Case ID + expectations. Draft cleared.
//
// Zero legacy mutation. Mounts at /incidents/report (new route).

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { FormShell } from "@/components/FormShell";
import { ProgressRail } from "@/components/ProgressRail";
import { HelpDrawer } from "@/components/HelpDrawer";
import { PresenceGate } from "@/components/PresenceGate";
import { INCIDENT_FLOWS, INCIDENT_TYPE_ORDER, hasValue, requiredFieldsForStep, stepsFor } from "@/lib/incidentReportSchema";
import IncidentFieldDoctrineBanner from "@/components/incident/IncidentFieldDoctrineBanner";
import { clearDraft, currentDraftId, ensureActiveDraftId, loadDraft, saveDraft } from "@/lib/incidentDraft";
import { createCase, patchFieldBlock, transitionCase, addEvidence, fetchDirectoryMe, fetchProjectContext, fetchWeather } from "@/lib/incidentReportApi";
import { DraftResumeBanner } from "@/components/DraftResumeBanner";
import { JobPicker } from "@/components/JobPicker";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { EquipmentCombo } from "@/components/EquipmentCombo";
import {
  AlertTriangle,
  Car,
  Check,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  CloudSun,
  Droplet,
  Heart,
  Home,
  Lock,
  Megaphone,
  Pencil,
  Shield,
  UserCheck,
  Wrench,
  X,
  Zap,
} from "lucide-react";

const ICONS = {
  car: Car,
  wrench: Wrench,
  zap: Zap,
  heart: Heart,
  "alert-triangle": AlertTriangle,
  home: Home,
  droplet: Droplet,
  shield: Shield,
  megaphone: Megaphone,
};

const ACCENTS = {
  amber: "bg-amber-50 text-amber-900 border-amber-300 hover:border-amber-500",
  red: "bg-red-50 text-red-900 border-red-300 hover:border-red-500",
  yellow: "bg-yellow-50 text-yellow-900 border-yellow-300 hover:border-yellow-500",
  emerald: "bg-emerald-50 text-emerald-900 border-emerald-300 hover:border-emerald-500",
  slate: "bg-slate-50 text-slate-800 border-slate-300 hover:border-slate-500",
};

// ── Incident-type picker ────────────────────────────────────────────
function IncidentTypePicker({ onPick, draft, onResume, onDiscard }) {
  const { t } = useT();
  const hasResumableDraft = draft && draft.incident_type;
  return (
    <div data-testid="incident-type-picker" className="space-y-4">
      {/* Track 19.34 · Field-vs-Safety doctrine banner.
          Renders once at the picker screen so every field user starts with
          the explicit expectation: field captures facts, Safety investigates. */}
      <IncidentFieldDoctrineBanner />
      {hasResumableDraft && (
        <DraftResumeBanner
          draft={draft}
          onResume={onResume}
          onDiscard={onDiscard}
        />
      )}
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          {t("Step 1 of 2")}
        </div>
        <h2 className="mt-1 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
          {t("What happened?")}
        </h2>
        <p className="mt-2 text-slate-700 leading-snug">
          {t("Pick the closest match. You can add detail on the next screen.")}
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {INCIDENT_TYPE_ORDER.map((code) => {
          const flow = INCIDENT_FLOWS[code];
          const Ico = ICONS[flow.icon] || AlertTriangle;
          return (
            <button
              type="button"
              key={code}
              data-testid={`incident-type-card-${code}`}
              onClick={() => onPick(code)}
              className={`text-left rounded-xl border-2 p-4 transition-colors ${ACCENTS[flow.accent] || ACCENTS.slate}`}
            >
              <div className="flex items-start gap-3">
                <div className="rounded-md bg-white/70 p-2 border border-white shrink-0">
                  <Ico className="w-5 h-5" aria-hidden />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-display text-base font-black leading-tight">
                    {t(flow.label)}
                  </div>
                  <p className="mt-1 text-sm leading-snug">
                    {t(flow.description)}
                  </p>
                  <p className="mt-1 text-[11px] font-mono uppercase tracking-[0.12em] opacity-70">
                    {t(flow.examples)}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Personnel list editor (repeatable) ──────────────────────────────
function PersonnelListField({ value, onChange, testId, ctx }) {
  const { t } = useT();
  const rows = Array.isArray(value) ? value : [];
  const set = (i, patch) => {
    const next = rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r));
    onChange(next);
  };
  const add = () => onChange([...rows, { name: "", role: "", __source__: "" }]);
  const remove = (i) => onChange(rows.filter((_, idx) => idx !== i));
  return (
    <div className="space-y-2" data-testid={testId}>
      {rows.map((r, i) => (
        <div key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-2 space-y-2" data-testid={`${testId}-row-${i}`}>
          <div className="flex items-stretch gap-2">
            <div className="flex-1 min-w-0">
              <EmployeeCombo
                value={r.name || ""}
                testId={`${testId}-row-${i}-name`}
                placeholder={t("Search or type…")}
                onChange={(v) => set(i, { name: v, __source__: "" })}
                onPick={(emp) => {
                  if (!emp) return;
                  set(i, {
                    name: emp.name || "",
                    role: r.role || emp.role || emp.trade || "",
                    __source__: "employees",
                    __employee_id__: emp.employee_id || "",
                    __crew__: emp.crew || "",
                  });
                }}
              />
            </div>
            <input
              type="text"
              className="w-32 h-11 rounded-md border border-slate-300 px-3 text-base"
              placeholder={t("Role")}
              value={r.role || ""}
              onChange={(e) => set(i, { role: e.target.value })}
              data-testid={`${testId}-row-${i}-role`}
              aria-label={t("Role")}
            />
            <button
              type="button"
              className="h-11 px-3 rounded-md border border-slate-300 text-slate-600 hover:border-red-500 hover:text-red-700"
              onClick={() => remove(i)}
              data-testid={`${testId}-row-${i}-remove`}
              aria-label={t("Remove")}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          {r.__source__ === "employees" ? (
            <p className="text-[10px] font-mono uppercase tracking-[0.14em] text-emerald-800"
               data-testid={`${testId}-row-${i}-roster-hint`}>
              <Lock className="w-2.5 h-2.5 inline mr-1" />
              {t("Selected from roster")}
              {r.__crew__ ? ` · ${t("Crew")} ${r.__crew__}` : ""}
            </p>
          ) : null}
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="h-10 px-3 rounded-md border-2 border-dashed border-slate-300 text-slate-700 hover:border-slate-500 w-full"
        data-testid={`${testId}-add`}
      >
        + {t("Add person")}
      </button>
    </div>
  );
}

// ── Witnesses editor ────────────────────────────────────────────────
const WITNESS_KINDS = [
  { v: "internal_employee", en: "Internal employee", es: "Empleado interno" },
  { v: "visitor",           en: "Visitor",           es: "Visitante" },
  { v: "contractor",        en: "Contractor",        es: "Contratista" },
  { v: "public",            en: "Public",            es: "Público" },
  { v: "police",            en: "Police",            es: "Policía" },
  { v: "utility_rep",       en: "Utility representative", es: "Representante de servicio público" },
];

function WitnessesField({ value, onChange, testId }) {
  const { t } = useT();
  const rows = Array.isArray(value) ? value : [];
  const set = (i, patch) => onChange(rows.map((r, idx) => idx === i ? { ...r, ...patch } : r));
  const add = () => onChange([...rows, { kind: "internal_employee", name: "", contact: "", statement: "", __source__: "" }]);
  const remove = (i) => onChange(rows.filter((_, idx) => idx !== i));
  return (
    <div className="space-y-3" data-testid={testId}>
      {rows.map((r, i) => (
        <div key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-2" data-testid={`${testId}-row-${i}`}>
          <div className="flex flex-wrap gap-2">
            {WITNESS_KINDS.map((k) => (
              <button
                key={k.v}
                type="button"
                onClick={() => set(i, { kind: k.v, __source__: "" })}
                className={`min-h-11 h-11 px-3 rounded-md text-xs font-mono uppercase tracking-[0.12em] border-2 ${
                  r.kind === k.v
                    ? "bg-slate-900 text-white border-transparent"
                    : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
                }`}
                data-testid={`${testId}-row-${i}-kind-${k.v}`}
                aria-pressed={r.kind === k.v}
                aria-label={t(k.en)}
              >
                {t(k.en)}
              </button>
            ))}
          </div>
          {r.kind === "internal_employee" ? (
            <div>
              <EmployeeCombo
                value={r.name || ""}
                testId={`${testId}-row-${i}-name`}
                placeholder={t("Search employee…")}
                onChange={(v) => set(i, { name: v, __source__: "" })}
                onPick={(emp) => {
                  if (!emp) return;
                  set(i, {
                    name: emp.name || "",
                    __source__: "employees",
                    __employee_id__: emp.employee_id || "",
                  });
                }}
              />
              {r.__source__ === "employees" ? (
                <p className="mt-1 text-[10px] font-mono uppercase tracking-[0.14em] text-emerald-800"
                   data-testid={`${testId}-row-${i}-roster-hint`}>
                  <Lock className="w-2.5 h-2.5 inline mr-1" />
                  {t("Selected from roster")}
                </p>
              ) : null}
            </div>
          ) : (
            <input
              type="text"
              className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
              placeholder={t("Name")}
              value={r.name || ""}
              onChange={(e) => set(i, { name: e.target.value })}
              data-testid={`${testId}-row-${i}-name`}
              aria-label={t("Name")}
            />
          )}
          <input
            type="text"
            className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Phone or email")}
            value={r.contact || ""}
            onChange={(e) => set(i, { contact: e.target.value })}
            data-testid={`${testId}-row-${i}-contact`}
            aria-label={t("Phone or email")}
          />
          <textarea
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-base"
            rows={3}
            placeholder={t("Statement / notes")}
            value={r.statement || ""}
            onChange={(e) => set(i, { statement: e.target.value })}
            data-testid={`${testId}-row-${i}-statement`}
            aria-label={t("Statement / notes")}
          />
          <div className="flex justify-end">
            <button
              type="button"
              className="h-11 px-3 rounded-md border border-slate-300 text-slate-600 hover:border-red-500 hover:text-red-700 text-sm"
              onClick={() => remove(i)}
              data-testid={`${testId}-row-${i}-remove`}
              aria-label={t("Remove witness")}
            >
              {t("Remove witness")}
            </button>
          </div>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="h-11 px-3 rounded-md border-2 border-dashed border-slate-300 text-slate-700 hover:border-slate-500 w-full"
        data-testid={`${testId}-add`}
      >
        + {t("Add witness")}
      </button>
    </div>
  );
}

// ── Photo capture with GPS + timestamp metadata ────────────────────
function PhotoField({ value, onChange, testId }) {
  const { t } = useT();
  const photos = Array.isArray(value) ? value : [];
  const inputRef = useRef(null);
  const [previewId, setPreviewId] = useState(null);

  const captureGps = () => new Promise((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { timeout: 3000, maximumAge: 60000 },
    );
  });

  const onFile = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const gps = await captureGps();
    const additions = await Promise.all(files.map((f) => new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve({
        id: `photo_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        name: f.name,
        size: f.size,
        mime: f.type,
        data_url: reader.result,
        captured_at: new Date().toISOString(),
        gps,
        upload_state: "pending",
      });
      reader.readAsDataURL(f);
    })));
    onChange([...photos, ...additions]);
    if (inputRef.current) inputRef.current.value = "";
  };

  const remove = (id) => {
    onChange(photos.filter((p) => p.id !== id));
    if (previewId === id) setPreviewId(null);
  };
  const move = (id, delta) => {
    const idx = photos.findIndex((p) => p.id === id);
    if (idx < 0) return;
    const next = idx + delta;
    if (next < 0 || next >= photos.length) return;
    const arr = photos.slice();
    const [row] = arr.splice(idx, 1);
    arr.splice(next, 0, row);
    onChange(arr);
  };

  const preview = photos.find((p) => p.id === previewId) || null;

  return (
    <div className="space-y-3" data-testid={testId}>
      <div className="flex items-center justify-between text-xs font-mono uppercase tracking-[0.14em] text-slate-500">
        <span data-testid={`${testId}-count`}>
          {photos.length} {photos.length === 1 ? t("photo") : t("photos")}
        </span>
        {photos.length > 0 ? (
          <span className="text-slate-400">{t("Tap to preview · use ↑↓ to reorder")}</span>
        ) : null}
      </div>
      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-2" data-testid={`${testId}-strip`}>
          {photos.map((p, i) => (
            <div
              key={p.id}
              className="relative rounded-md overflow-hidden border border-slate-200 group"
              data-testid={`${testId}-photo-${p.id}`}
            >
              <button
                type="button"
                onClick={() => setPreviewId(p.id)}
                className="block w-full focus:outline-none focus:ring-2 focus:ring-slate-900"
                aria-label={t("Preview photo")}
                data-testid={`${testId}-photo-${p.id}-preview`}
              >
                <img src={p.data_url} alt={p.name || `photo ${i + 1}`} className="w-full h-24 object-cover" />
              </button>
              <div className="absolute top-1 right-1 flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => remove(p.id)}
                  className="h-6 w-6 rounded-full bg-white/95 text-red-700 text-xs font-bold shadow flex items-center justify-center"
                  data-testid={`${testId}-photo-${p.id}-remove`}
                  aria-label={t("Remove photo")}
                >×</button>
              </div>
              <div className="absolute bottom-1 left-1 right-1 flex justify-between">
                <button
                  type="button"
                  onClick={() => move(p.id, -1)}
                  disabled={i === 0}
                  className="h-6 w-6 rounded-full bg-white/90 text-slate-700 shadow disabled:opacity-40 flex items-center justify-center"
                  data-testid={`${testId}-photo-${p.id}-up`}
                  aria-label={t("Move photo earlier")}
                >
                  <ChevronUp className="w-3.5 h-3.5" />
                </button>
                <span
                  className="h-6 px-2 rounded-full bg-slate-900/85 text-white text-[10px] font-mono flex items-center"
                  data-testid={`${testId}-photo-${p.id}-order`}
                >{i + 1}</span>
                <button
                  type="button"
                  onClick={() => move(p.id, +1)}
                  disabled={i === photos.length - 1}
                  className="h-6 w-6 rounded-full bg-white/90 text-slate-700 shadow disabled:opacity-40 flex items-center justify-center"
                  data-testid={`${testId}-photo-${p.id}-down`}
                  aria-label={t("Move photo later")}
                >
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        onChange={onFile}
        className="hidden"
        data-testid={`${testId}-input`}
        aria-label={t("Add photo")}
      />
      <button
        type="button"
        onClick={() => inputRef.current && inputRef.current.click()}
        className="min-h-11 h-11 w-full rounded-md border-2 border-dashed border-slate-400 text-slate-800 font-medium hover:border-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900"
        data-testid={`${testId}-capture`}
        aria-label={t("Add photo")}
      >
        + {t("Add photo")}
      </button>
      <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-slate-500">
        {t("GPS + timestamp are attached automatically.")}
      </p>

      {preview ? (
        <div
          role="dialog"
          aria-label={t("Preview photo")}
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          data-testid={`${testId}-preview-modal`}
          onClick={() => setPreviewId(null)}
        >
          <div className="max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <img src={preview.data_url} alt={preview.name || "preview"} className="w-full max-h-[70vh] object-contain rounded-md bg-black" />
            <div className="mt-3 flex items-center justify-between text-xs text-slate-100">
              <div className="truncate">{preview.name || "photo"}{preview.captured_at ? ` · ${preview.captured_at}` : ""}</div>
              <button
                type="button"
                onClick={() => setPreviewId(null)}
                className="h-9 px-3 rounded-md bg-white text-slate-900 text-sm font-semibold"
                data-testid={`${testId}-preview-close`}
                aria-label={t("Close preview")}
              >
                {t("Close")}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// ── GPS button ───────────────────────────────────────────────────────
function GpsField({ value, onChange, testId }) {
  const { t } = useT();
  const [busy, setBusy] = useState(false);
  const capture = () => {
    if (typeof navigator === "undefined" || !navigator.geolocation) return;
    setBusy(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onChange({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setBusy(false);
      },
      () => setBusy(false),
      { timeout: 5000, maximumAge: 60000 },
    );
  };
  return (
    <div className="space-y-2" data-testid={testId}>
      {value && value.lat != null && (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-sm text-slate-800 font-mono" data-testid={`${testId}-value`}>
          {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
        </div>
      )}
      <button
        type="button"
        onClick={capture}
        disabled={busy}
        className="h-11 w-full rounded-md border border-slate-300 text-slate-800 hover:border-slate-700 disabled:opacity-60"
        data-testid={`${testId}-capture`}
      >
        {busy ? t("Locating…") : (value && value.lat != null ? t("Update GPS") : t("Capture GPS"))}
      </button>
    </div>
  );
}

// ── TRACK 19.16 · UX Hardening Batch 1 ─────────────────────────────
// Auto-fill field renderers. Selection beats typing. All three flag
// the parent's `__auto__` map so the Review panel can distinguish
// auto-filled values from typed ones.

function ProjectPickerField({ value, onChange, testId, onSelectProject }) {
  const { t } = useT();
  const [manual, setManual] = useState(false);
  const displayLabel = value || "";
  return (
    <div className="space-y-2" data-testid={testId}>
      {!manual ? (
        <>
          <JobPicker
            projectName=""
            projectNumber={displayLabel}
            onSelect={(job) => {
              if (!job) return;
              const num = job.project_number || "";
              onChange(num);
              try { onSelectProject && onSelectProject(job); } catch (_e) { /* noop */ }
            }}
            allowCustom={false}
          />
          <button
            type="button"
            onClick={() => setManual(true)}
            className="text-xs font-mono uppercase tracking-[0.14em] text-slate-500 hover:text-slate-800 underline"
            data-testid={`${testId}-manual-toggle`}
          >
            {t("Temporary or unlisted project — enter manually")}
          </button>
        </>
      ) : (
        <>
          <input
            type="text"
            className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Job number")}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            data-testid={`${testId}-manual-input`}
          />
          <button
            type="button"
            onClick={() => setManual(false)}
            className="text-xs font-mono uppercase tracking-[0.14em] text-slate-500 hover:text-slate-800 underline"
            data-testid={`${testId}-picker-toggle`}
          >
            {t("Back to project picker")}
          </button>
        </>
      )}
    </div>
  );
}

function IdentityConfirmField({ value, identity, onChange, testId }) {
  const { t } = useT();
  const [manual, setManual] = useState(false);
  const suggestedName = identity?.name || identity?.email || "";
  useEffect(() => {
    // First-load suggestion: adopt the directory name if the field is empty.
    if (!value && suggestedName && !manual) {
      onChange(suggestedName);
    }
  }, [suggestedName]);

  if (manual || !suggestedName) {
    return (
      <input
        type="text"
        className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
        placeholder={t("Your name")}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        data-testid={`${testId}-input`}
      />
    );
  }

  const matches = (value || "").trim() === suggestedName.trim();
  return (
    <div
      className={`flex items-center gap-2 rounded-md border-2 p-3 ${
        matches
          ? "border-emerald-300 bg-emerald-50"
          : "border-amber-300 bg-amber-50"
      }`}
      data-testid={testId}
    >
      <UserCheck className={`w-5 h-5 ${matches ? "text-emerald-700" : "text-amber-700"}`} />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
          {t("Signed in as")}
        </div>
        <div className="font-bold text-slate-900 truncate">{suggestedName}</div>
        {identity?.email ? (
          <div className="text-xs text-slate-500 truncate">{identity.email}</div>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => setManual(true)}
        className="text-xs font-mono uppercase tracking-[0.14em] text-slate-600 hover:text-slate-900 underline"
        data-testid={`${testId}-not-me`}
      >
        {t("Not me")}
      </button>
    </div>
  );
}

function WeatherAutoField({ value, weatherAuto, onChange, onRefetch, testId }) {
  const { t } = useT();
  const auto = weatherAuto || null;
  const [busy, setBusy] = useState(false);
  const doRefetch = async () => {
    if (!onRefetch) return;
    setBusy(true);
    try { await onRefetch(); } finally { setBusy(false); }
  };
  return (
    <div className="space-y-2" data-testid={testId}>
      {auto ? (
        <div
          className="rounded-md border-2 border-sky-300 bg-sky-50 p-3"
          data-testid={`${testId}-auto`}
        >
          <div className="flex items-center gap-2">
            <CloudSun className="w-5 h-5 text-sky-700" />
            <div className="font-bold text-slate-900 truncate">{auto.summary || value || "—"}</div>
          </div>
          <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-slate-700">
            {auto.temperature_f != null && (
              <span>{t("Temp")}: {Math.round(auto.temperature_f)}°F</span>
            )}
            {auto.wind_speed_mph != null && (
              <span>{t("Wind")}: {Math.round(auto.wind_speed_mph)} mph</span>
            )}
            {auto.relative_humidity != null && (
              <span>{t("Humidity")}: {Math.round(auto.relative_humidity)}%</span>
            )}
            {auto.precipitation_in != null && (
              <span>{t("Rain")}: {auto.precipitation_in.toFixed(2)} in</span>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid={`${testId}-empty`}>
          {t("Capture GPS to auto-fetch weather.")}
        </div>
      )}
      <input
        type="text"
        className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
        placeholder={t("Weather (optional override)")}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        data-testid={`${testId}-override`}
      />
      <button
        type="button"
        onClick={doRefetch}
        disabled={busy || !onRefetch}
        className="h-9 px-3 rounded-md border border-slate-300 text-slate-700 text-xs font-mono uppercase tracking-[0.14em] hover:border-slate-600 disabled:opacity-60"
        data-testid={`${testId}-refetch`}
      >
        {busy ? t("Fetching…") : t("Refresh weather")}
      </button>
    </div>
  );
}

// ── TRACK 19.16 · UX Hardening Batch 2 ─────────────────────────────
// Employee / Equipment / Vehicle picker renderers. Each stores the
// human-readable label on the draft as a string (so the existing
// field_block schema doesn't drift) but hydrates a sidecar map on
// the draft (`__selected__[<field>] = { source, id, meta }`) so the
// Review can distinguish platform-selected from typed values, and
// downstream reports can show richer metadata via the sidecar.

function _selMeta(draft, key) {
  return (draft && draft.__selected__ && draft.__selected__[key]) || null;
}

function _writeSelMeta(setDraft, markAuto, key, meta) {
  setDraft((d) => {
    const map = { ...(d.__selected__ || {}) };
    if (meta) map[key] = meta;
    else delete map[key];
    // TRACK 19.16 · Closeout · Fleet cross-link.
    // Maintain a flat, backend-visible list of every equipment_master
    // unit_number the user has selected across any picker. The Fleet /
    // Equipment Status Board joins on this to surface a "Recent
    // Incident" pill without duplicating incident truth.
    const units = new Set();
    for (const m of Object.values(map)) {
      if (m && m.source === "equipment_master" && m.unit_number) {
        units.add(String(m.unit_number));
      }
    }
    return {
      ...d,
      __selected__: map,
      selected_unit_numbers: Array.from(units),
    };
  });
  if (meta) markAuto([key]);
}

function EmployeePickerField({ value, onChange, testId, fieldKey, ctx }) {
  const { t } = useT();
  return (
    <div data-testid={testId} className="space-y-1">
      <EmployeeCombo
        value={value || ""}
        testId={testId}
        onChange={(v) => {
          onChange(v);
          // Free-text edit — drop any prior selection metadata.
          if (ctx?.setSelectedMeta) ctx.setSelectedMeta(fieldKey, null);
        }}
        onPick={(emp) => {
          if (!emp) return;
          const label = emp.preferred_name && emp.preferred_name !== emp.name
            ? `${emp.name} (${emp.preferred_name})` : (emp.name || "");
          onChange(label);
          if (ctx?.setSelectedMeta) ctx.setSelectedMeta(fieldKey, {
            source: "employees",
            id: emp.id || null,
            employee_id: emp.employee_id || "",
            name: emp.name || "",
            role: emp.role || "",
            trade: emp.trade || "",
            crew: emp.crew || "",
          });
        }}
      />
      {(() => {
        const meta = _selMeta(ctx?.draft, fieldKey);
        return meta ? (
          <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-emerald-800"
             data-testid={`${testId}-selected-hint`}>
            <Lock className="w-2.5 h-2.5 inline mr-1" />
            {t("Selected from roster")}
            {meta.role ? ` · ${meta.role}` : ""}
            {meta.crew ? ` · ${t("Crew")} ${meta.crew}` : ""}
          </p>
        ) : (
          <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-slate-500">
            {t("Search or type. Selecting a name from the list auto-fills roster data.")}
          </p>
        );
      })()}
    </div>
  );
}

// Vehicle-ish equipment categories in the master roster.
const VEHICLE_CATEGORIES = [
  "Pickup Trucks", "Dump Trucks", "Flatbed Trucks", "Service Trucks",
  "Supervisor / Mgmt Trucks", "Tractor Trailer Trucks", "Water Trucks",
  "Misc Trucks", "Sweepers",
];

function EquipmentPickerField({ value, onChange, testId, fieldKey, ctx, filterCategories }) {
  const { t } = useT();
  return (
    <div data-testid={testId} className="space-y-1">
      <EquipmentCombo
        value={value || ""}
        testId={testId}
        placeholder={t("Search by unit #, make, model, plate, VIN…")}
        filterCategories={filterCategories}
        onChange={(v) => {
          onChange(v);
          if (ctx?.setSelectedMeta) ctx.setSelectedMeta(fieldKey, null);
        }}
        onPick={(unit) => {
          if (!unit) return;
          const bits = [];
          if (unit.unit_number) bits.push(unit.unit_number);
          if (unit.year) bits.push(unit.year);
          if (unit.make) bits.push(unit.make);
          if (unit.model) bits.push(unit.model);
          if (unit.plate) bits.push(`plate ${unit.plate}`);
          const label = bits.length ? bits.join(" · ") : (unit.display_label || unit.make_model || "");
          onChange(label);
          if (ctx?.setSelectedMeta) ctx.setSelectedMeta(fieldKey, {
            source: "equipment_master",
            id: unit.id || null,
            unit_number: unit.unit_number || "",
            category: unit.category || "",
            make: unit.make || "",
            model: unit.model || "",
            year: unit.year || null,
            plate: unit.plate || "",
            vin: unit.vin_serial_number || "",
            company: unit.company || "",
          });
        }}
      />
      {(() => {
        const meta = _selMeta(ctx?.draft, fieldKey);
        return meta ? (
          <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-emerald-800"
             data-testid={`${testId}-selected-hint`}>
            <Lock className="w-2.5 h-2.5 inline mr-1" />
            {t("Selected from fleet")}
            {meta.plate ? ` · plate ${meta.plate}` : ""}
            {meta.vin ? ` · VIN ${meta.vin.slice(-6)}` : ""}
          </p>
        ) : (
          <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-slate-500">
            {filterCategories ? t("Third-party or unlisted vehicle? Type it in.")
                              : t("Third-party or unlisted equipment? Type it in.")}
          </p>
        );
      })()}
    </div>
  );
}

// ── Generic field renderer ───────────────────────────────────────────
function FieldRenderer({ field, value, onChange, testIdPrefix, ctx }) {
  const { t } = useT();
  const tid = `${testIdPrefix}-field-${field.key}`;
  const commonProps = {
    "data-testid": `${tid}-input`,
    className: "w-full h-11 rounded-md border border-slate-300 px-3 text-base",
    value: value ?? "",
    onChange: (e) => onChange(e.target.value),
  };

  if (field.type === "text") return <input type="text" {...commonProps} />;
  if (field.type === "number") return (
    <input type="number" inputMode="decimal" {...commonProps} />
  );
  if (field.type === "date") return <input type="date" {...commonProps} />;
  if (field.type === "time") return <input type="time" {...commonProps} />;
  if (field.type === "textarea") return (
    <textarea
      {...commonProps}
      rows={field.rows || 4}
      className="w-full rounded-md border border-slate-300 px-3 py-2 text-base"
    />
  );
  if (field.type === "select") return (
    <select {...commonProps}>
      <option value="">{t("Choose…")}</option>
      {(field.options || []).map((o) => (
        <option key={o.v} value={o.v}>{t(o.label)}</option>
      ))}
    </select>
  );
  if (field.type === "yesno") return (
    <PresenceGate
      label=""
      value={value || ""}
      onChange={onChange}
      testIdPrefix={tid}
      options={[
        { v: "yes", label: t("Yes"), testId: `${tid}-yes` },
        { v: "no",  label: t("No"),  testId: `${tid}-no` },
      ]}
    />
  );
  if (field.type === "yesno_unsure") return (
    <PresenceGate
      label=""
      value={value || ""}
      onChange={onChange}
      testIdPrefix={tid}
    />
  );
  if (field.type === "personnel_list") return (
    <PersonnelListField value={value} onChange={onChange} testId={tid} ctx={ctx} />
  );
  if (field.type === "gps") return (
    <GpsField value={value} onChange={onChange} testId={tid} />
  );
  if (field.type === "photos") return (
    <PhotoField value={value} onChange={onChange} testId={tid} />
  );
  if (field.type === "witnesses") return (
    <WitnessesField value={value} onChange={onChange} testId={tid} />
  );
  if (field.type === "employee_picker") return (
    <EmployeePickerField
      value={value}
      onChange={onChange}
      testId={tid}
      fieldKey={field.key}
      ctx={ctx}
    />
  );
  if (field.type === "equipment_picker") return (
    <EquipmentPickerField
      value={value}
      onChange={onChange}
      testId={tid}
      fieldKey={field.key}
      ctx={ctx}
    />
  );
  if (field.type === "vehicle_picker") return (
    <EquipmentPickerField
      value={value}
      onChange={onChange}
      testId={tid}
      fieldKey={field.key}
      ctx={ctx}
      filterCategories={VEHICLE_CATEGORIES}
    />
  );
  if (field.type === "project_picker") return (
    <ProjectPickerField
      value={value}
      onChange={onChange}
      onSelectProject={ctx?.onSelectProject}
      testId={tid}
    />
  );
  if (field.type === "identity_confirm") return (
    <IdentityConfirmField
      value={value}
      identity={ctx?.identity}
      onChange={onChange}
      testId={tid}
    />
  );
  if (field.type === "weather_auto") return (
    <WeatherAutoField
      value={value}
      weatherAuto={ctx?.weatherAuto}
      onChange={onChange}
      onRefetch={ctx?.onRefetchWeather}
      testId={tid}
    />
  );

  return null;
}

// ── One step of the form ─────────────────────────────────────────────
function StepPanel({ step, draft, setField, testIdPrefix, ctx, autoMap }) {
  const { t } = useT();
  return (
    <div className="space-y-4" data-testid={`${testIdPrefix}-step-${step.key}`}>
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          {t(step.label)}
        </div>
      </div>
      <div className="space-y-4">
        {(step.fields || [])
          .filter((f) => (typeof f.showIf === "function" ? f.showIf(draft) : true))
          .map((f) => (
            <div key={f.key} className="space-y-1" data-testid={`${testIdPrefix}-field-${f.key}`}>
              <label className="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                {t(f.label)}
                {f.required && <span className="text-red-700">*</span>}
                {autoMap && autoMap[f.key] ? (
                  <span
                    className="ml-1 inline-flex items-center gap-0.5 rounded-full bg-emerald-100 text-emerald-800 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em]"
                    data-testid={`${testIdPrefix}-field-${f.key}-auto-badge`}
                    title={t("Auto-filled from platform data")}
                  >
                    <Lock className="w-2.5 h-2.5" />
                    {t("auto")}
                  </span>
                ) : null}
              </label>
              <FieldRenderer
                field={f}
                value={draft[f.key]}
                onChange={(v) => setField(f.key, v)}
                testIdPrefix={testIdPrefix}
                ctx={ctx}
              />
            </div>
          ))}
      </div>
    </div>
  );
}

// ── Review card ──────────────────────────────────────────────────────
function ReviewCard({ draft, steps, missing, onEditStep, autoMap }) {
  const { t } = useT();
  const flow = INCIDENT_FLOWS[draft.incident_type];
  const autoCount = Object.keys(autoMap || {}).length;
  const projectCtx = draft.__project_context__ || null;
  const selMap = draft.__selected__ || {};
  const selectedCount = Object.keys(selMap).length;
  const photoCount = Array.isArray(draft.photos) ? draft.photos.length : 0;
  const witnessCount = Array.isArray(draft.witnesses) ? draft.witnesses.length : 0;
  return (
    <div className="space-y-4" data-testid="incident-report-review">
      <div className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          {t("Review")}
        </div>
        <h3 className="mt-1 font-display text-xl font-black text-slate-900">
          {flow ? t(flow.label) : t("Incident")}
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          {t("Everything you entered. Tap a section to jump back.")}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span
            className="inline-flex items-center gap-1 rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 font-mono uppercase tracking-[0.12em]"
            data-testid="incident-report-review-auto-count"
          >
            <Lock className="w-3 h-3" />
            {autoCount} {t("auto-filled")}
          </span>
          <span
            className="inline-flex items-center gap-1 rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 font-mono uppercase tracking-[0.12em]"
            data-testid="incident-report-review-typed-count"
          >
            <Pencil className="w-3 h-3" />
            {t("typed by you")}
          </span>
          <span
            className="inline-flex items-center gap-1 rounded-full bg-sky-100 text-sky-800 px-2 py-0.5 font-mono uppercase tracking-[0.12em]"
            data-testid="incident-report-review-selected-count"
          >
            <UserCheck className="w-3 h-3" />
            {selectedCount} {t("platform-selected")}
          </span>
          <span
            className="inline-flex items-center gap-1 rounded-full bg-amber-100 text-amber-900 px-2 py-0.5 font-mono uppercase tracking-[0.12em]"
            data-testid="incident-report-review-photo-count"
          >
            {photoCount} {t("photos")}
          </span>
          <span
            className="inline-flex items-center gap-1 rounded-full bg-indigo-100 text-indigo-900 px-2 py-0.5 font-mono uppercase tracking-[0.12em]"
            data-testid="incident-report-review-witness-count"
          >
            {witnessCount} {t("witnesses")}
          </span>
        </div>
        {projectCtx ? (
          <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm"
               data-testid="incident-report-review-project-context">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
              {t("Project details")}
            </div>
            <div className="mt-1 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-0.5 text-slate-800">
              <span>{t("Project")}: <b>{projectCtx.project_name || "—"}</b></span>
              <span>{t("Client")}: <b>{projectCtx.client || "—"}</b></span>
              <span>{t("PM")}: <b>{projectCtx.project_manager || "—"}</b></span>
              <span>{t("Superintendent")}: <b>{projectCtx.superintendent || "—"}</b></span>
            </div>
          </div>
        ) : null}
        {selectedCount > 0 ? (
          <div className="mt-3 rounded-md border border-sky-200 bg-sky-50 p-3 text-sm"
               data-testid="incident-report-review-selected-block">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-sky-700">
              {t("Platform-selected records")}
            </div>
            <ul className="mt-1 space-y-1 text-slate-800">
              {Object.entries(selMap).map(([k, m]) => (
                <li key={k} data-testid={`incident-report-review-selected-${k}`}>
                  <span className="font-mono text-[10px] uppercase text-slate-500">{k}</span>
                  {" · "}
                  <b>{m.name || m.unit_number || "—"}</b>
                  {m.source === "employees" && m.employee_id ? ` · ID ${m.employee_id}` : ""}
                  {m.source === "equipment_master" && m.plate ? ` · plate ${m.plate}` : ""}
                  {m.source === "equipment_master" && m.vin ? ` · VIN ${m.vin.slice(-6)}` : ""}
                  {m.role ? ` · ${m.role}` : ""}
                  {m.crew ? ` · ${t("Crew")} ${m.crew}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
      {steps.map((step, i) => {
        const stepMissing = (missing[step.key] || []).length;
        const done = stepMissing === 0;
        return (
          <button
            key={step.key}
            type="button"
            onClick={() => onEditStep(i)}
            className={`w-full text-left rounded-xl border-2 p-4 transition-colors ${
              done
                ? "border-emerald-300 bg-emerald-50 hover:border-emerald-500"
                : "border-amber-400 bg-amber-50 hover:border-amber-600"
            }`}
            data-testid={`incident-report-review-step-${step.key}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  {t("Section")} {i + 1}
                </div>
                <div className="font-display text-base font-bold text-slate-900">
                  {t(step.label)}
                </div>
              </div>
              {done ? (
                <span className="inline-flex items-center gap-1 text-emerald-800 text-sm font-bold" data-testid={`incident-report-review-step-${step.key}-done`}>
                  <Check className="w-4 h-4" /> {t("Complete")}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-800 text-sm font-bold" data-testid={`incident-report-review-step-${step.key}-missing`}>
                  <AlertTriangle className="w-4 h-4" /> {stepMissing} {t("missing")}
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ── Success screen ───────────────────────────────────────────────────
function SuccessScreen({ caseNumber, caseId, onDone }) {
  const { t } = useT();
  return (
    <div className="min-h-screen bg-emerald-50 flex flex-col items-center justify-center p-6" data-testid="incident-report-success">
      <div className="max-w-md w-full bg-white rounded-2xl border-2 border-emerald-300 p-6 space-y-4 shadow-lg">
        <div className="rounded-full bg-emerald-100 w-14 h-14 flex items-center justify-center">
          <Check className="w-8 h-8 text-emerald-700" />
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-800">
            {t("Report submitted")}
          </div>
          <h2 className="mt-1 font-display text-2xl font-black tracking-tight text-slate-900">
            {t("Safety has received your report.")}
          </h2>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3" data-testid="incident-report-case-number">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-800">
            {t("Case number")}
          </div>
          <div className="font-mono text-lg font-black text-emerald-900">{caseNumber || caseId}</div>
        </div>
        <ul className="space-y-2 text-sm text-slate-800">
          <li>{t("Your field observations are locked and cannot be changed.")}</li>
          <li>{t("Safety will begin intake and reach out if they need anything.")}</li>
          <li>{t("You can close this page — nothing else is required from you right now.")}</li>
        </ul>
        <button
          type="button"
          onClick={onDone}
          className="w-full h-12 rounded-md bg-emerald-700 text-white font-bold hover:bg-emerald-800"
          data-testid="incident-report-done"
        >
          {t("Done")}
        </button>
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────
export default function IncidentReport() {
  const { t } = useT();
  const navigate = useNavigate();

  // Draft persistence. Resolve draft id + hydrate BEFORE first render
  // (synchronous localStorage read) so reload lands back on the exact
  // step the user was on with values restored.
  const draftIdRef = useRef(null);
  const [draft, setDraft] = useState(() => {
    const id = currentDraftId() || ensureActiveDraftId();
    draftIdRef.current = id;
    return loadDraft(id) || {};
  });
  const [phase, setPhase] = useState(() => {
    const initial = loadDraft(draftIdRef.current) || {};
    return initial.incident_type ? "steps" : "picker";
  });
  const [stepIndex, setStepIndex] = useState(() => {
    const initial = loadDraft(draftIdRef.current) || {};
    return Math.max(0, Number.isInteger(initial.__step_index__) ? initial.__step_index__ : 0);
  });
  const [helpOpen, setHelpOpen] = useState(false);
  const [submitState, setSubmitState] = useState({ error: "", caseNumber: "", caseId: "" });

  // TRACK 19.16 · UX Hardening Batch 1 ─────────────────────────────
  // Auto-fill state. `identity` = current directory user (name/email).
  // `weatherAuto` = last-fetched Open-Meteo payload. `autoMap` marks
  // which draft fields were auto-populated so the Review shows a lock
  // badge instead of pretending the user typed them.
  const [identity, setIdentity] = useState(null);
  const [weatherAuto, setWeatherAuto] = useState(null);
  const [autoMap, setAutoMap] = useState({});
  const markAuto = (keys) => setAutoMap((m) => {
    const next = { ...m };
    for (const k of keys) next[k] = true;
    return next;
  });
  // On mount: fetch directory identity + default date/time to now.
  useEffect(() => {
    let alive = true;
    fetchDirectoryMe().then((who) => { if (alive && who) setIdentity(who); });
    setDraft((d) => {
      const now = new Date();
      const yyyy = now.getFullYear();
      const mm = String(now.getMonth() + 1).padStart(2, "0");
      const dd = String(now.getDate()).padStart(2, "0");
      const hh = String(now.getHours()).padStart(2, "0");
      const mi = String(now.getMinutes()).padStart(2, "0");
      const patch = {};
      const filled = [];
      if (!d.occurred_at_date) { patch.occurred_at_date = `${yyyy}-${mm}-${dd}`; filled.push("occurred_at_date"); }
      if (!d.occurred_at_time) { patch.occurred_at_time = `${hh}:${mi}`; filled.push("occurred_at_time"); }
      if (filled.length) markAuto(filled);
      return { ...d, ...patch };
    });
    return () => { alive = false; };
  }, []);

  // When a project is picked, auto-fill location + weather (if GPS).
  const onSelectProject = async (job) => {
    if (!job) return;
    // Auto-fill the human-readable location label if empty. Keep any
    // user-authored value intact — never silently overwrite.
    setDraft((d) => {
      const patch = {};
      const filled = [];
      if (!d.location_label && job.location) {
        patch.location_label = job.location;
        filled.push("location_label");
      }
      if (filled.length) markAuto(filled);
      return { ...d, ...patch };
    });
    // Deep project context (superintendent, client, PM) — attach as a
    // sidecar; not persisted server-side because the field_block schema
    // owns only project_number, but we expose it in Review.
    try {
      const ctx = await fetchProjectContext(job.project_number);
      if (ctx) {
        setDraft((d) => ({ ...d, __project_context__: ctx }));
      }
    } catch { /* silent */ }
  };

  // Refetch weather from current GPS coordinates.
  const refetchWeatherFromGps = async () => {
    const gps = draft.location_gps;
    if (!gps || typeof gps.lat !== "number" || typeof gps.lng !== "number") return;
    const w = await fetchWeather(gps.lat, gps.lng);
    if (w) {
      setWeatherAuto(w);
      if (!draft.weather && w.summary) {
        setDraft((d) => ({ ...d, weather: w.summary }));
        markAuto(["weather"]);
      }
    }
  };

  // Auto-fetch weather whenever GPS lands and no manual override exists.
  useEffect(() => {
    const gps = draft.location_gps;
    if (!gps || typeof gps.lat !== "number" || typeof gps.lng !== "number") return;
    let alive = true;
    fetchWeather(gps.lat, gps.lng).then((w) => {
      if (!alive || !w) return;
      setWeatherAuto(w);
      if (!draft.weather && w.summary) {
        setDraft((d) => (d.weather ? d : { ...d, weather: w.summary }));
        markAuto(["weather"]);
      }
    });
    return () => { alive = false; };
  }, [draft.location_gps?.lat, draft.location_gps?.lng]);

  const ctx = useMemo(() => ({
    identity,
    weatherAuto,
    draft,
    onSelectProject,
    onRefetchWeather: refetchWeatherFromGps,
    setSelectedMeta: (key, meta) => _writeSelMeta(setDraft, markAuto, key, meta),
  }), [identity, weatherAuto, draft, draft.location_gps?.lat, draft.location_gps?.lng]);

  // Autosave draft on any change. Persist stepIndex alongside so the
  // user resumes on the exact step they left.
  useEffect(() => {
    saveDraft(draftIdRef.current, { ...draft, __step_index__: stepIndex });
  }, [draft, stepIndex]);

  const setField = (k, v) => setDraft((d) => ({ ...d, [k]: v }));

  const steps = useMemo(
    () => (draft.incident_type ? stepsFor(draft.incident_type) : []),
    [draft.incident_type],
  );

  // Compute missing required keys per step.
  const missing = useMemo(() => {
    const out = {};
    for (const step of steps) {
      const need = requiredFieldsForStep(step, draft);
      out[step.key] = need.filter((k) => !hasValue(draft[k]));
    }
    // TRACK 19.17 · Pencil-whip guardrails. High-severity branches
    // (employee/public injury, fire, utility strike, vehicle accident)
    // must ship with at least one photo. Injury cases must ship with a
    // witness OR an explicit "attempted contact" note. These pseudo-
    // requirements piggyback on the missing map so the Review already-
    // built UX highlights them.
    const t = draft.incident_type;
    const HIGH_SEVERITY = new Set([
      "employee_injury", "public_injury", "utility_strike",
      "vehicle_accident", "fire",
    ]);
    const photos = Array.isArray(draft.photos) ? draft.photos : [];
    if (HIGH_SEVERITY.has(t) && photos.length === 0) {
      const key = t === "utility_strike" ? "utility" : (t === "fire" ? "fire" : (
        t === "employee_injury" ? "injury" : (
          t === "public_injury" ? "public_injury" : "vehicle"
        )
      ));
      const list = out[key] || out.photos || [];
      out[key] = [...(list || []), "photos_required"];
    }
    if (t === "employee_injury" || t === "public_injury") {
      const w = Array.isArray(draft.witnesses) ? draft.witnesses : [];
      const anyWitness = w.some((r) => (r?.name || "").trim() || (r?.contact || "").trim());
      const attempted = String(draft.witness_attempted_contact_note || "").trim();
      if (!anyWitness && !attempted) {
        const key = "witnesses";
        out[key] = [...(out[key] || []), "witness_or_attempted_contact_required"];
      }
    }
    if (t === "employee_injury" || t === "utility_strike") {
      if (!hasValue(draft.immediate_actions)) {
        const key = "immediate";
        out[key] = [...(out[key] || []), "immediate_actions_required"];
      }
    }
    return out;
  }, [steps, draft]);

  const totalMissing = Object.values(missing).reduce((a, b) => a + b.length, 0);

  const pickType = (code) => {
    setDraft((d) => ({ ...d, incident_type: code }));
    setPhase("steps");
    setStepIndex(0);
  };

  const goNext = () => {
    if (stepIndex < steps.length - 1) {
      setStepIndex((i) => i + 1);
      return;
    }
    setPhase("review");
  };

  const goPrev = () => {
    if (stepIndex > 0) {
      setStepIndex((i) => i - 1);
    } else {
      setPhase("picker");
    }
  };

  // Assemble the field_block payload the backend expects. This mirrors
  // `FieldBlock` in `incident_engine/models.py`.
  const buildFieldBlock = () => {
    const occurredAt = draft.occurred_at_date && draft.occurred_at_time
      ? new Date(`${draft.occurred_at_date}T${draft.occurred_at_time}:00`).toISOString()
      : new Date().toISOString();
    return {
      incident_type: draft.incident_type,
      occurred_at: occurredAt,
      reported_at: new Date().toISOString(),
      location_label: draft.location_label || "",
      location_gps: draft.location_gps || null,
      job_number: draft.job_number || "",
      reporter_name: draft.reporter_name || "",
      reporter_role: draft.reporter_role || "",
      personnel_present: Array.isArray(draft.personnel_present) ? draft.personnel_present : [],
      weather: draft.weather || "",
      immediate_actions: draft.immediate_actions || "",
      immediate_notifications: (draft.immediate_notifications || "")
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      observed_conditions: draft.observed_conditions || "",
      // Type-specific fields are stored under `extra_<type>` inside the block
      // (Pydantic `extra="allow"` on FieldBlock lets them through as-is).
      ...typeSpecificPayload(draft),
    };
  };

  const submit = async () => {
    setPhase("submitting");
    setSubmitState((s) => ({ ...s, error: "" }));
    try {
      const fb = buildFieldBlock();
      const created = await createCase(fb);
      // Attach photos as evidence.
      const photos = Array.isArray(draft.photos) ? draft.photos : [];
      for (const p of photos) {
        try {
          await addEvidence(created.id, {
            evidence_type: "photo",
            label: p.name || "photo",
            metadata: {
              size: p.size, mime: p.mime,
              captured_at: p.captured_at, gps: p.gps,
            },
          });
        } catch { /* photo failure is non-fatal for submit */ }
      }
      // Attach witnesses as evidence rows (typed witness_statement).
      const witnesses = Array.isArray(draft.witnesses) ? draft.witnesses : [];
      for (const w of witnesses) {
        try {
          await addEvidence(created.id, {
            evidence_type: "witness_statement",
            label: w.name || "witness",
            description: w.statement || "",
            metadata: { kind: w.kind, contact: w.contact },
          });
        } catch { /* non-fatal */ }
      }
      // Transition to FIELD_SUBMITTED — Field Block becomes immutable.
      const submitted = await transitionCase(created.id, "FIELD_SUBMITTED");
      setSubmitState({
        error: "",
        caseNumber: submitted.case_number || created.case_number || "",
        caseId: created.id,
      });
      clearDraft(draftIdRef.current);
      setPhase("done");
    } catch (e) {
      const msg = e?.response?.data?.detail?.detail || e?.response?.data?.detail?.code || e.message || "submit_failed";
      setSubmitState((s) => ({ ...s, error: String(msg) }));
      setPhase("review");
    }
  };

  // Help sections for the current step.
  const helpSections = useMemo(() => {
    const step = steps[stepIndex];
    if (!step) return [];
    return [
      {
        title: t("Report only the facts you observed."),
        body: t("Field-owned observations are locked once you submit. Safety takes over investigation from there — you don't need to write conclusions."),
      },
      {
        title: t("Skip what you don't know."),
        body: t("Only red-star fields are required. Leave anything else blank if you're not certain."),
      },
      {
        title: t("Your draft is saved automatically."),
        body: t("Every keystroke is stored on this device. You can close the app and come back to finish."),
      },
    ];
  }, [steps, stepIndex, t]);

  if (phase === "done") {
    return (
      <SuccessScreen
        caseNumber={submitState.caseNumber}
        caseId={submitState.caseId}
        onDone={() => navigate("/", { replace: true })}
      />
    );
  }

  return (
    <FormShell
      kicker={t("Field Incident Report")}
      title={draft.incident_type ? t(INCIDENT_FLOWS[draft.incident_type].label) : t("Report an incident")}
      subtitle={t("Report the facts you observed. Safety takes over from there.")}
      progressSlot={phase === "steps" ? (
        <ProgressRail
          steps={steps.map((s) => ({ key: s.key, label: t(s.label) }))}
          currentIndex={stepIndex}
          onJump={(i) => setStepIndex(i)}
          testId="incident-report-progress"
        />
      ) : null}
      headerRightSlot={(phase === "steps" || phase === "review") ? (
        <HelpDrawer
          open={helpOpen}
          onOpenChange={setHelpOpen}
          triggerLabel={t("Help")}
          title={t("How to fill this out")}
          sections={helpSections}
          testIdPrefix="incident-report-help"
        />
      ) : null}
      draftSlot={phase !== "picker" ? (
        <span
          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2 py-1 text-[10px] font-mono uppercase tracking-[0.14em] text-slate-600"
          data-testid="incident-report-draft-indicator"
          title={t("Autosaved on this device")}
        >
          {t("Draft saved")}
        </span>
      ) : null}
      containerTestId="incident-report"
      stickyFooter={
        phase === "picker" ? null :
        phase === "steps" ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={goPrev}
              className="h-11 px-4 rounded-md border border-slate-300 text-slate-700 hover:border-slate-500 inline-flex items-center gap-1"
              data-testid="incident-report-prev"
            >
              <ChevronLeft className="w-4 h-4" /> {t("Back")}
            </button>
            <button
              type="button"
              onClick={goNext}
              className="flex-1 h-11 rounded-md bg-slate-900 text-white font-bold hover:bg-slate-800"
              data-testid="incident-report-next"
            >
              {stepIndex < steps.length - 1 ? t("Next") : t("Review")}
            </button>
          </div>
        ) : phase === "review" ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => { setPhase("steps"); setStepIndex(0); }}
              className="h-11 px-4 rounded-md border border-slate-300 text-slate-700 hover:border-slate-500"
              data-testid="incident-report-review-back"
            >
              {t("Edit")}
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={totalMissing > 0}
              className="flex-1 h-11 rounded-md bg-red-700 text-white font-bold hover:bg-red-800 disabled:bg-slate-300 disabled:cursor-not-allowed"
              data-testid="incident-report-submit"
            >
              {totalMissing > 0
                ? t("Complete required fields to submit")
                : t("Submit report")}
            </button>
          </div>
        ) : (
          <div className="h-11 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center" data-testid="incident-report-submitting">
            {t("Submitting…")}
          </div>
        )
      }
    >
      {phase === "picker" && (
        <IncidentTypePicker
          onPick={pickType}
          draft={hasValue(draft?.incident_type) ? draft : null}
          onResume={() => { setPhase("steps"); setStepIndex(Math.max(0, draft.__step_index__ || 0)); }}
          onDiscard={() => { clearDraft(draftIdRef.current); draftIdRef.current = ensureActiveDraftId(); setDraft({}); setStepIndex(0); }}
        />
      )}
      {phase === "steps" && steps[stepIndex] && (
        <StepPanel
          step={steps[stepIndex]}
          draft={draft}
          setField={setField}
          testIdPrefix="incident-report"
          ctx={ctx}
          autoMap={autoMap}
        />
      )}
      {phase === "review" && (
        <>
          {submitState.error && (
            <div className="rounded-md border-2 border-red-400 bg-red-50 p-3 text-sm text-red-900" data-testid="incident-report-submit-error">
              {t("We could not submit. Please try again.")} — {submitState.error}
            </div>
          )}
          <ReviewCard
            draft={draft}
            steps={steps}
            missing={missing}
            onEditStep={(i) => { setPhase("steps"); setStepIndex(i); }}
            autoMap={autoMap}
          />
        </>
      )}
    </FormShell>
  );
}

// Type-specific keys captured under the FieldBlock (Pydantic extra="allow").
function typeSpecificPayload(draft) {
  const keys = [
    // vehicle
    "vehicle_ids", "drivers", "passengers", "police_response", "police_case_number",
    "tow_required", "traffic_control", "third_party_involved", "third_party_info",
    // equipment
    "equipment_id", "operator_name", "damage_severity", "out_of_service", "damage_description",
    // utility
    "utility_type", "utility_owner", "locate_ticket_number", "locate_valid",
    "service_interrupted", "emergency_response_called", "isp_information",
    // injury
    "injured_employee", "injury_body_part", "injury_severity",
    "first_aid_given", "ems_transported", "hospital_name", "injury_description",
    // near miss
    "potential_consequence", "what_prevented_injury", "severity_potential",
    // property
    "property_owner", "property_owner_contact", "affected_assets", "estimated_damage_usd",
    // environmental
    "spill_material", "spill_volume", "containment_achieved", "waterway_impact",
    "agency_notified", "agency_name", "cleanup_actions",
    // violence
    "individuals_involved", "immediate_separation", "law_enforcement_called",
    "restraining_order", "threat_ongoing",
    // complaint
    "citizen_name", "citizen_contact", "complaint_category", "resolution_attempt",
    // shared immediate status
    "everyone_safe", "ems_needed", "ems_on_scene", "hazard_controlled",
  ];
  const out = {};
  for (const k of keys) {
    if (hasValue(draft[k])) out[k] = draft[k];
  }
  return out;
}
