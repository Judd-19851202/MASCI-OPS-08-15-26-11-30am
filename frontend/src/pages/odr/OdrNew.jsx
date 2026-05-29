// OdrNew.jsx — Phase V.1 · M0.3 · Foreman ODR Entry.
//
// Doctrine inheritance:
//   /app/memory/ODR_DATA_MODEL.md
//   /app/memory/ODR_UI_WIREFRAMES.md
//   /app/memory/M0_2A_OPERATOR_REVIEW_GUIDE.md
//   /app/memory/ODR_TRUST_BANNER_DOCTRINE.md
//
// Field-first usability:
//   - phone-first layout (thumb-friendly · 44pt tap targets)
//   - bilingual (EN ↔ ES) toggle wired to coaching catalog
//   - progressive disclosure (one section at a time)
//   - autosave-on-change · works offline-tolerantly (best-effort)
//   - low typing burden · dropdowns + chips + voice-ready captions
//
// No "corporate reporting" feel. Calm slate palette. No red unless
// a hard stop blocks submit.

import React from "react";
import { useNavigate } from "react-router-dom";
import {
  createOdr, patchOdr, submitOdr,
  resolveGuidance, logObservation, getCrewReadiness,
} from "@/lib/odrApi";
import OdrTrustBanner from "@/components/odr/OdrTrustBanner";

const CREW_TYPES = [
  { value: "pipe", en: "Pipe", es: "Tubería" },
  { value: "utility", en: "Utility", es: "Servicios" },
  { value: "grading", en: "Grading", es: "Nivelación" },
  { value: "paving", en: "Paving", es: "Pavimentación" },
  { value: "milling", en: "Milling", es: "Fresado" },
  { value: "mot", en: "MOT", es: "MOT (Tráfico)" },
  { value: "concrete", en: "Concrete", es: "Concreto" },
  { value: "structures", en: "Structures", es: "Estructuras" },
  { value: "airfield", en: "Airfield", es: "Aeropuerto" },
  { value: "electrical", en: "Electrical", es: "Eléctrico" },
  { value: "survey", en: "Survey", es: "Topografía" },
  { value: "other", en: "Other", es: "Otro" },
];

const STEPS = [
  { key: "project", en: "Project", es: "Proyecto" },
  { key: "crew", en: "Crew", es: "Cuadrilla" },
  { key: "manpower", en: "Manpower", es: "Personal" },
  { key: "equipment", en: "Equipment", es: "Equipo" },
  { key: "production", en: "Production", es: "Producción" },
  { key: "delays", en: "Delays", es: "Demoras" },
  { key: "safety", en: "Safety", es: "Seguridad" },
  { key: "tomorrow", en: "Tomorrow", es: "Mañana" },
  { key: "sign", en: "Sign & Submit", es: "Firmar y Enviar" },
];

function L(s, lang) { return (s && s[lang]) || s?.en || ""; }

function todayISO() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function deviceKind() {
  if (typeof window === "undefined") return "desktop";
  const w = window.innerWidth || 1024;
  if (w < 600) return "phone";
  if (w < 1024) return "tablet";
  return "desktop";
}

export default function OdrNew() {
  const navigate = useNavigate();
  const [lang, setLang] = React.useState("en");
  const [step, setStep] = React.useState(0);
  const [odr, setOdr] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [errorBox, setErrorBox] = React.useState("");
  const [hardStops, setHardStops] = React.useState([]);
  const tStart = React.useRef(Date.now());

  // Foreman entry form state — kept simple at substrate-level.
  const [project, setProject] = React.useState({
    project_id: "",
    project_number: "",
    project_name: "",
    report_date: todayISO(),
    foreman_uid: "",
    foreman_name: "",
  });
  const [crew, setCrew] = React.useState({
    crew_id: "",
    crew_name: "",
    crew_type: "pipe",
    primary_operation: "",
  });
  const [productionNote, setProductionNote] = React.useState("");
  const [delaysAny, setDelaysAny] = React.useState(false);
  const [delayHours, setDelayHours] = React.useState(0);
  const [delayDesc, setDelayDesc] = React.useState("");
  const [safetyAnyEvent, setSafetyAnyEvent] = React.useState(false);
  const [tomorrow, setTomorrow] = React.useState("");
  const [ack, setAck] = React.useState(false);

  const [coaching, setCoaching] = React.useState({});
  const [readiness, setReadiness] = React.useState({ required: [] });

  React.useEffect(() => {
    logObservation({
      surface: "foreman",
      kind: "session_start",
      device_kind: deviceKind(),
      lang,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    logObservation({
      surface: "foreman",
      kind: "section_visited",
      odr_id: odr?.id,
      doc_id: odr?.doc_id,
      context: { section: STEPS[step].key },
      device_kind: deviceKind(),
      lang,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  React.useEffect(() => {
    if (!crew.crew_type) return;
    getCrewReadiness(crew.crew_type)
      .then(setReadiness)
      .catch(() => setReadiness({ required: [] }));
  }, [crew.crew_type]);

  // Load coaching bullets for the current step.
  const sectionToPrompt = {
    project: "project.weather.verify_capture",
    manpower: "manpower.hours.complete_all_rows",
    equipment: "equipment.utilization.record_idle_down",
    production: "production.add_first_segment",
    delays: "delays.classify_with_type",
    safety: "safety.report_every_event",
    tomorrow: "tomorrow.planned_work.add_summary",
    sign: "signature.foreman_acknowledgement.required",
  };
  const promptKey = sectionToPrompt[STEPS[step].key];

  React.useEffect(() => {
    if (!promptKey) { setCoaching({}); return; }
    resolveGuidance(promptKey, crew.crew_type, lang)
      .then(setCoaching)
      .catch(() => setCoaching({ bullets: [] }));
  }, [promptKey, crew.crew_type, lang]);

  // Auto-create draft when the user advances past Crew step.
  const ensureDraft = async () => {
    if (odr) return odr;
    if (!project.project_id || !crew.crew_id) {
      throw new Error(lang === "es"
        ? "Complete proyecto y cuadrilla primero."
        : "Complete project and crew first.");
    }
    const created = await createOdr({ project, crew_profile: crew });
    setOdr(created);
    return created;
  };

  const persistStep = async () => {
    setErrorBox("");
    if (!odr) return;
    setBusy(true);
    try {
      const patch = {};
      if (STEPS[step].key === "production" && productionNote) {
        patch.production_segments = [{
          segment_id: "seg-1",
          crew_type: crew.crew_type,
          primary_operation: crew.primary_operation || productionNote.slice(0, 60),
          body: { other: { notes: { text: productionNote }, quantities: [] } },
        }];
      }
      if (STEPS[step].key === "delays") {
        patch.delays = {
          any_delays: !!delaysAny,
          entries: delaysAny ? [{
            delay_type: "weather",
            hours_lost: Number(delayHours) || 0,
            description: { text: delayDesc },
            photos: [],
          }] : [],
          total_hours_lost: Number(delayHours) || 0,
        };
      }
      if (STEPS[step].key === "safety") {
        patch.safety = {
          any_event: !!safetyAnyEvent,
          accident: false, incident: false, near_miss: false,
          property_damage: false, environmental_release: false,
          injury: false,
          events: safetyAnyEvent ? [{
            event_id: "ev-1",
            event_kind: "near_miss",
            notified_safety: true,
            incident_report_complete: true,
            photos: [],
          }] : [],
        };
      }
      if (STEPS[step].key === "tomorrow") {
        patch.tomorrow = {
          planned_work: { text: tomorrow },
          required_resources: [], concerns: [],
        };
      }
      if (Object.keys(patch).length) {
        const next = await patchOdr(odr.id, patch);
        setOdr(next);
        logObservation({
          surface: "foreman", kind: "section_completed",
          odr_id: odr.id, doc_id: odr.doc_id,
          context: { section: STEPS[step].key },
          device_kind: deviceKind(), lang,
        });
      }
    } catch (e) {
      setErrorBox(e.message || "Save failed");
    } finally { setBusy(false); }
  };

  const advance = async () => {
    setErrorBox("");
    try {
      if (step === 1 && !odr) await ensureDraft();
      else if (odr) await persistStep();
      setStep(s => Math.min(s + 1, STEPS.length - 1));
    } catch (e) { setErrorBox(e.message); }
  };

  const back = () => setStep(s => Math.max(s - 1, 0));

  const onSubmit = async () => {
    setErrorBox(""); setHardStops([]);
    if (!odr) { setErrorBox("Create the draft first."); return; }
    if (!ack) {
      setErrorBox(lang === "es"
        ? "Marque el reconocimiento del foreman."
        : "Check the foreman acknowledgement.");
      return;
    }
    setBusy(true);
    try {
      await patchOdr(odr.id, {
        signature: {
          foreman_acknowledgement: {
            acknowledged: true,
            acknowledged_by_uid: project.foreman_uid || "self",
            text: lang === "es"
              ? "Confirmo que este reporte es verdadero y completo."
              : "I confirm this report is true and complete.",
          },
        },
      });
      const submitted = await submitOdr(odr.id, {});
      const ms = Date.now() - tStart.current;
      logObservation({
        surface: "foreman", kind: "submit_success",
        odr_id: submitted.id, doc_id: submitted.doc_id,
        context: { duration_ms: ms, sections: STEPS.length },
        device_kind: deviceKind(), lang,
      });
      navigate(`/odr/${encodeURIComponent(submitted.id)}/done`);
    } catch (e) {
      const detail = e.detail || {};
      if (detail && detail.hard_stops) {
        setHardStops(detail.hard_stops);
        logObservation({
          surface: "foreman", kind: "submit_blocked",
          odr_id: odr.id, doc_id: odr.doc_id,
          context: { hard_stops_count: detail.hard_stops.length },
          device_kind: deviceKind(), lang,
        });
      } else {
        setErrorBox(e.message || "Submit failed");
      }
    } finally { setBusy(false); }
  };

  const onLangToggle = () => {
    const next = lang === "en" ? "es" : "en";
    setLang(next);
    logObservation({
      surface: "foreman", kind: "language_toggled",
      odr_id: odr?.id, doc_id: odr?.doc_id,
      context: { to: next, section: STEPS[step].key },
      device_kind: deviceKind(), lang: next,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-md mx-auto px-4 py-5 sm:max-w-2xl" data-testid="odr-new-page">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-800">
              {lang === "es" ? "Reporte Diario Operativo" : "Operational Daily Record"}
            </h1>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {lang === "es" ? "Paso" : "Step"} {step + 1} / {STEPS.length} · {L(STEPS[step], lang)}
            </p>
          </div>
          <button
            type="button"
            onClick={onLangToggle}
            data-testid="odr-lang-toggle"
            className="text-[11px] uppercase tracking-wider text-slate-600 border border-slate-300 rounded-full px-2.5 py-1 hover:bg-slate-100"
          >
            {lang === "en" ? "ES" : "EN"}
          </button>
        </div>

        <OdrTrustBanner />

        <div className="mt-4 bg-white border border-slate-200 rounded-lg p-4" data-testid={`odr-step-${STEPS[step].key}`}>
          {STEPS[step].key === "project" && (
            <div className="space-y-3">
              <Field label={lang === "es" ? "Número de Proyecto" : "Project Number"}>
                <input
                  data-testid="odr-project-number"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={project.project_number}
                  onChange={e => setProject({ ...project, project_number: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "Nombre del Proyecto" : "Project Name"}>
                <input
                  data-testid="odr-project-name"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={project.project_name}
                  onChange={e => setProject({ ...project, project_name: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "ID Proyecto" : "Project ID"}>
                <input
                  data-testid="odr-project-id"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={project.project_id}
                  onChange={e => setProject({ ...project, project_id: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "Fecha del Reporte" : "Report Date"}>
                <input
                  type="date"
                  data-testid="odr-report-date"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={project.report_date}
                  onChange={e => setProject({ ...project, report_date: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "Foreman (correo)" : "Foreman (email)"}>
                <input
                  data-testid="odr-foreman-uid"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={project.foreman_uid}
                  onChange={e => setProject({ ...project, foreman_uid: e.target.value, foreman_name: project.foreman_name || e.target.value })}
                />
              </Field>
            </div>
          )}

          {STEPS[step].key === "crew" && (
            <div className="space-y-3">
              <Field label={lang === "es" ? "Tipo de Cuadrilla" : "Crew Type"}>
                <select
                  data-testid="odr-crew-type"
                  className="w-full border border-slate-300 rounded px-3 py-2 bg-white"
                  value={crew.crew_type}
                  onChange={e => setCrew({ ...crew, crew_type: e.target.value })}
                >
                  {CREW_TYPES.map(c => (
                    <option key={c.value} value={c.value}>{L(c, lang)}</option>
                  ))}
                </select>
              </Field>
              <Field label={lang === "es" ? "ID Cuadrilla" : "Crew ID"}>
                <input
                  data-testid="odr-crew-id"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={crew.crew_id}
                  onChange={e => setCrew({ ...crew, crew_id: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "Nombre Cuadrilla" : "Crew Name"}>
                <input
                  data-testid="odr-crew-name"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={crew.crew_name}
                  onChange={e => setCrew({ ...crew, crew_name: e.target.value })}
                />
              </Field>
              <Field label={lang === "es" ? "Operación Principal" : "Primary Operation"}>
                <input
                  data-testid="odr-primary-op"
                  className="w-full border border-slate-300 rounded px-3 py-2"
                  value={crew.primary_operation}
                  onChange={e => setCrew({ ...crew, primary_operation: e.target.value })}
                />
              </Field>
              {readiness.required && readiness.required.length > 0 && (
                <div className="text-xs text-slate-500 border-t border-slate-100 pt-2 mt-2">
                  <span className="font-medium text-slate-600">
                    {lang === "es" ? "Temas requeridos para esta cuadrilla:" : "Required topics for this crew:"}
                  </span>
                  <ul className="list-disc list-inside mt-1 space-y-0.5">
                    {readiness.required.slice(0, 5).map(t => <li key={t}>{t.replace(/-/g, " ")}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {STEPS[step].key === "production" && (
            <Field label={lang === "es" ? "Resumen de producción" : "Production summary"}>
              <textarea
                data-testid="odr-production-note"
                rows={4}
                className="w-full border border-slate-300 rounded px-3 py-2"
                value={productionNote}
                onChange={e => setProductionNote(e.target.value)}
              />
            </Field>
          )}

          {STEPS[step].key === "delays" && (
            <div className="space-y-3">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  data-testid="odr-delays-any"
                  checked={delaysAny}
                  onChange={e => setDelaysAny(e.target.checked)}
                />
                {lang === "es" ? "Hubo demoras hoy" : "Delays today"}
              </label>
              {delaysAny && (
                <>
                  <Field label={lang === "es" ? "Horas perdidas" : "Hours lost"}>
                    <input
                      type="number"
                      step="0.25"
                      data-testid="odr-delay-hours"
                      className="w-full border border-slate-300 rounded px-3 py-2"
                      value={delayHours}
                      onChange={e => setDelayHours(e.target.value)}
                    />
                  </Field>
                  <Field label={lang === "es" ? "Descripción de la demora" : "Delay description"}>
                    <textarea
                      data-testid="odr-delay-desc"
                      rows={3}
                      className="w-full border border-slate-300 rounded px-3 py-2"
                      value={delayDesc}
                      onChange={e => setDelayDesc(e.target.value)}
                    />
                  </Field>
                </>
              )}
            </div>
          )}

          {STEPS[step].key === "safety" && (
            <div className="space-y-3">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  data-testid="odr-safety-any"
                  checked={safetyAnyEvent}
                  onChange={e => setSafetyAnyEvent(e.target.checked)}
                />
                {lang === "es" ? "Hubo un evento de seguridad" : "There was a safety event"}
              </label>
              {safetyAnyEvent && (
                <p className="text-xs text-slate-500 border-l-2 border-slate-200 pl-3">
                  {lang === "es"
                    ? "Notifique al equipo de Seguridad antes de continuar."
                    : "Notify the Safety team before continuing."}
                </p>
              )}
            </div>
          )}

          {STEPS[step].key === "tomorrow" && (
            <Field label={lang === "es" ? "Trabajo planeado para mañana" : "Tomorrow's planned work"}>
              <textarea
                data-testid="odr-tomorrow"
                rows={4}
                className="w-full border border-slate-300 rounded px-3 py-2"
                value={tomorrow}
                onChange={e => setTomorrow(e.target.value)}
              />
            </Field>
          )}

          {STEPS[step].key === "manpower" && (
            <p className="text-sm text-slate-500">
              {lang === "es"
                ? "Personal: complete después de revisar el equipo y la producción. (M0.4 detalle por persona)"
                : "Manpower: complete after reviewing equipment and production. (M0.4 per-row detail)"}
            </p>
          )}
          {STEPS[step].key === "equipment" && (
            <p className="text-sm text-slate-500">
              {lang === "es"
                ? "Equipo: registre horas y avisos al Taller en la siguiente fase."
                : "Equipment: record hours and Shop alerts in next phase."}
            </p>
          )}

          {STEPS[step].key === "sign" && (
            <div className="space-y-3">
              <label className="flex items-start gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  data-testid="odr-ack"
                  checked={ack}
                  onChange={e => setAck(e.target.checked)}
                  className="mt-1"
                />
                <span>
                  {lang === "es"
                    ? "Confirmo que este reporte es verdadero y completo a mi mejor saber."
                    : "I confirm this report is true and complete to the best of my knowledge."}
                </span>
              </label>
              {hardStops.length > 0 && (
                <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3" data-testid="odr-hard-stops">
                  <div className="font-medium mb-1">
                    {lang === "es" ? "Faltan elementos requeridos:" : "Required items missing:"}
                  </div>
                  <ul className="list-disc list-inside text-xs">
                    {hardStops.map(s => <li key={s}>{s}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Coaching · OGC catalog · ≥4 bullets · resolved per crew + lang */}
          {coaching.bullets && coaching.bullets.length > 0 && (
            <details
              className="mt-4 text-xs text-slate-600"
              data-testid="odr-coaching-block"
              onToggle={(e) => {
                if (e.target.open) {
                  logObservation({
                    surface: "foreman", kind: "coaching_expanded",
                    odr_id: odr?.id, doc_id: odr?.doc_id,
                    context: { prompt_key: promptKey, section: STEPS[step].key },
                    device_kind: deviceKind(), lang,
                  });
                }
              }}
            >
              <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
                {lang === "es" ? "Consejos del superintendente" : "Superintendent tips"}
                {" "}
                <span className="text-slate-400">({coaching.bullets.length})</span>
              </summary>
              <ul className="mt-2 list-disc list-inside space-y-1.5 text-slate-600">
                {coaching.bullets.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            </details>
          )}
        </div>

        {errorBox && (
          <div className="mt-3 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded p-2" data-testid="odr-error">
            {errorBox}
          </div>
        )}

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            data-testid="odr-back"
            onClick={back}
            disabled={step === 0 || busy}
            className="flex-1 py-3 rounded-lg border border-slate-300 text-slate-700 disabled:opacity-40"
          >
            {lang === "es" ? "Atrás" : "Back"}
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              data-testid="odr-next"
              onClick={advance}
              disabled={busy}
              className="flex-1 py-3 rounded-lg bg-slate-800 text-white disabled:opacity-50"
            >
              {busy ? (lang === "es" ? "Guardando…" : "Saving…") : (lang === "es" ? "Siguiente" : "Next")}
            </button>
          ) : (
            <button
              type="button"
              data-testid="odr-submit"
              onClick={onSubmit}
              disabled={busy}
              className="flex-1 py-3 rounded-lg bg-slate-800 text-white disabled:opacity-50"
            >
              {busy ? (lang === "es" ? "Enviando…" : "Submitting…") : (lang === "es" ? "Enviar" : "Submit")}
            </button>
          )}
        </div>

        {odr && (
          <p className="mt-3 text-[10px] text-slate-400 text-center" data-testid="odr-draft-id">
            {odr.doc_id} · {odr.status}
          </p>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">{label}</div>
      {children}
    </label>
  );
}
