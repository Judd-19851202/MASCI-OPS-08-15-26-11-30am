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
import { clearDraft, currentDraftId, ensureActiveDraftId, loadDraft, saveDraft } from "@/lib/incidentDraft";
import { createCase, patchFieldBlock, transitionCase, addEvidence, fetchDirectoryMe, fetchProjectContext, fetchWeather } from "@/lib/incidentReportApi";
import { DraftResumeBanner } from "@/components/DraftResumeBanner";
import { JobPicker } from "@/components/JobPicker";
import {
  AlertTriangle,
  Car,
  Check,
  ChevronLeft,
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
function PersonnelListField({ value, onChange, testId }) {
  const { t } = useT();
  const rows = Array.isArray(value) ? value : [];
  const set = (i, patch) => {
    const next = rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r));
    onChange(next);
  };
  const add = () => onChange([...rows, { name: "", role: "" }]);
  const remove = (i) => onChange(rows.filter((_, idx) => idx !== i));
  return (
    <div className="space-y-2" data-testid={testId}>
      {rows.map((r, i) => (
        <div key={i} className="flex gap-2 items-center" data-testid={`${testId}-row-${i}`}>
          <input
            type="text"
            className="flex-1 h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Name")}
            value={r.name || ""}
            onChange={(e) => set(i, { name: e.target.value })}
            data-testid={`${testId}-row-${i}-name`}
          />
          <input
            type="text"
            className="flex-1 h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Role")}
            value={r.role || ""}
            onChange={(e) => set(i, { role: e.target.value })}
            data-testid={`${testId}-row-${i}-role`}
          />
          <button
            type="button"
            className="h-11 px-3 rounded-md border border-slate-300 text-slate-600 hover:border-red-500 hover:text-red-700"
            onClick={() => remove(i)}
            data-testid={`${testId}-row-${i}-remove`}
          >
            {t("Remove")}
          </button>
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
  const add = () => onChange([...rows, { kind: "internal_employee", name: "", contact: "", statement: "" }]);
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
                onClick={() => set(i, { kind: k.v })}
                className={`h-9 px-3 rounded-md text-xs font-mono uppercase tracking-[0.12em] border-2 ${
                  r.kind === k.v
                    ? "bg-slate-900 text-white border-transparent"
                    : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
                }`}
                data-testid={`${testId}-row-${i}-kind-${k.v}`}
              >
                {t(k.en)}
              </button>
            ))}
          </div>
          <input
            type="text"
            className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Name")}
            value={r.name || ""}
            onChange={(e) => set(i, { name: e.target.value })}
            data-testid={`${testId}-row-${i}-name`}
          />
          <input
            type="text"
            className="w-full h-11 rounded-md border border-slate-300 px-3 text-base"
            placeholder={t("Phone or email")}
            value={r.contact || ""}
            onChange={(e) => set(i, { contact: e.target.value })}
            data-testid={`${testId}-row-${i}-contact`}
          />
          <textarea
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-base"
            rows={3}
            placeholder={t("Statement / notes")}
            value={r.statement || ""}
            onChange={(e) => set(i, { statement: e.target.value })}
            data-testid={`${testId}-row-${i}-statement`}
          />
          <div className="flex justify-end">
            <button
              type="button"
              className="h-9 px-3 rounded-md border border-slate-300 text-slate-600 hover:border-red-500 hover:text-red-700 text-sm"
              onClick={() => remove(i)}
              data-testid={`${testId}-row-${i}-remove`}
            >
              {t("Remove witness")}
            </button>
          </div>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="h-10 px-3 rounded-md border-2 border-dashed border-slate-300 text-slate-700 hover:border-slate-500 w-full"
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
      });
      reader.readAsDataURL(f);
    })));
    onChange([...photos, ...additions]);
    if (inputRef.current) inputRef.current.value = "";
  };

  const remove = (id) => onChange(photos.filter((p) => p.id !== id));

  return (
    <div className="space-y-3" data-testid={testId}>
      <div className="grid grid-cols-3 gap-2">
        {photos.map((p) => (
          <div key={p.id} className="relative rounded-md overflow-hidden border border-slate-200" data-testid={`${testId}-photo-${p.id}`}>
            <img src={p.data_url} alt="" className="w-full h-24 object-cover" />
            <button
              type="button"
              onClick={() => remove(p.id)}
              className="absolute top-1 right-1 h-6 w-6 rounded-full bg-white/90 text-red-700 text-xs font-bold shadow"
              data-testid={`${testId}-photo-${p.id}-remove`}
            >×</button>
          </div>
        ))}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        onChange={onFile}
        className="hidden"
        data-testid={`${testId}-input`}
      />
      <button
        type="button"
        onClick={() => inputRef.current && inputRef.current.click()}
        className="h-11 w-full rounded-md border-2 border-dashed border-slate-400 text-slate-800 font-medium hover:border-slate-700"
        data-testid={`${testId}-capture`}
      >
        + {t("Add photo")}
      </button>
      <p className="text-[11px] font-mono uppercase tracking-[0.12em] text-slate-500">
        {t("GPS + timestamp are attached automatically.")}
      </p>
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    <PersonnelListField value={value} onChange={onChange} testId={tid} />
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft.location_gps?.lat, draft.location_gps?.lng]);

  const ctx = useMemo(() => ({
    identity,
    weatherAuto,
    onSelectProject,
    onRefetchWeather: refetchWeatherFromGps,
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [identity, weatherAuto, draft.location_gps?.lat, draft.location_gps?.lng]);

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
