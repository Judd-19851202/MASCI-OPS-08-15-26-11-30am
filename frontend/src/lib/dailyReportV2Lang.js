/**
 * DR-ROI-001F-FINAL-REPAIR · Amendment · EN/ES field mode.
 *
 * Bilingual dictionary + React context for the Daily Job Report V2.
 * English is the canonical language of the submitted record. Spanish is
 * a field-facing convenience for supervisors and crews. See
 * `/app/memory/DR_ROI_001F_FINAL_REPAIR_EN_ES_MODE.md` for the full
 * bilingual audit contract.
 *
 * Guarantees:
 *   · Every field-facing string used by the DR-V2 shell + sections is
 *     keyed here — no hard-coded strings on the shell/sections.
 *   · Every key MUST have an EN and ES value. `t(key)` falls back to
 *     the key itself in dev if a translation is missing — CI blocks the
 *     miss via `test_dr_roi_001f_en_es_lock.py`.
 *   · Freeform user input (activity notes, delay reasons, safety notes,
 *     tomorrow notes, edited summary, etc.) is NEVER translated by this
 *     module — it is preserved verbatim and canonicalized server-side
 *     via /api/dr-v2/reports/{id}/canonicalize on submit.
 */
import React from "react";

export const DICTIONARY = {
  // Header
  "header.eyebrow":            { en: "MASCI Field Operations", es: "Operaciones de Campo MASCI" },
  "header.title":              { en: "Daily Job Report",       es: "Reporte Diario de Obra" },
  "header.draft":              { en: "Draft",                  es: "Borrador" },
  "status.saving":             { en: "Saving…",                es: "Guardando…" },
  "status.saved":              { en: "Draft saved",            es: "Borrador guardado" },
  "status.idle":               { en: "Not saved yet",          es: "Sin guardar" },
  "lang.toggle_label":         { en: "Language",               es: "Idioma" },
  "footer.autosave":           { en: "Draft autosaves as you work · refreshing this page restores your entries · minimum six field photos required before submit.",
                                 es: "El borrador se guarda automáticamente · si actualizas la página se restauran tus datos · mínimo seis fotos son requeridas antes de enviar." },
  // Disabled preview state
  "preview.title":             { en: "Daily Job Report · preview only",       es: "Reporte Diario de Obra · sólo vista previa" },
  "preview.body":              { en: "The next generation of the Daily Job Report is not enabled for your account yet. Your team continues to use the current Daily Job Report.",
                                 es: "La próxima versión del Reporte Diario de Obra aún no está habilitada para tu cuenta. Tu equipo sigue usando el reporte actual." },
  "preview.back":              { en: "Go to the current Daily Job Report",   es: "Ir al Reporte Diario de Obra actual" },

  // Section 01
  "s01.title":                 { en: "Day Setup",              es: "Configuración del Día" },
  "s01.project":               { en: "Project",                es: "Proyecto" },
  "s01.report_date":           { en: "Report date",            es: "Fecha del reporte" },
  "s01.shift":                 { en: "Shift",                  es: "Turno" },
  "s01.shift.day":             { en: "Day",                    es: "Día" },
  "s01.shift.night":           { en: "Night",                  es: "Noche" },
  "s01.shift.weekend":         { en: "Weekend",                es: "Fin de semana" },
  "s01.supervisor":            { en: "Supervisor / Prepared by", es: "Supervisor / Preparado por" },
  "s01.supervisor.ph":         { en: "Full name",              es: "Nombre completo" },
  "s01.gps":                   { en: "Capture GPS",            es: "Capturar GPS" },
  "s01.weather":               { en: "Fetch weather",          es: "Obtener clima" },

  // Section 02
  "s02.title":                 { en: "MASCI Crews on Site",    es: "Cuadrillas MASCI en el sitio" },
  "s02.desc":                  { en: "HR-linked. Employees come from the canonical roster · hours flow to payroll and time verification as they do today.",
                                 es: "Vinculado a RH. Los empleados vienen del listado oficial · las horas van a nómina y verificación de tiempo como hoy." },
  "s02.empty":                 { en: "No crew yet. Add employees below.", es: "Sin cuadrilla aún. Agrega empleados abajo." },
  "s02.crew_member":           { en: "Crew Member",            es: "Miembro de cuadrilla" },
  "s02.employee":              { en: "Employee",               es: "Empleado" },
  "s02.hours":                 { en: "Hours",                  es: "Horas" },
  "s02.role":                  { en: "Role / cost code",       es: "Rol / código de costo" },
  "s02.role.ph":               { en: "Optional",               es: "Opcional" },
  "s02.remove":                { en: "Remove",                 es: "Quitar" },
  "s02.add":                   { en: "Add Crew Member",        es: "Agregar miembro" },

  // Section 03
  "s03.title":                 { en: "Equipment on Site",      es: "Equipo en el sitio" },
  "s03.desc":                  { en: "Equipment master is HR/Shop-linked. Idle / breakdown flags feed the Pre-Op + shop workflows unchanged.",
                                 es: "El listado de equipo está vinculado a RH/Taller. Las marcas de inactivo/avería alimentan Pre-Op y taller sin cambios." },
  "s03.empty":                 { en: "No equipment yet. Add units used today.", es: "Sin equipo aún. Agrega las unidades usadas hoy." },
  "s03.unit":                  { en: "Unit",                   es: "Unidad" },
  "s03.operator":              { en: "Operator",               es: "Operador" },
  "s03.status":                { en: "Status",                 es: "Estado" },
  "s03.status.in_service":     { en: "In service",             es: "En servicio" },
  "s03.status.idle":           { en: "Idle",                   es: "Inactivo" },
  "s03.status.breakdown":      { en: "Breakdown",              es: "Avería" },
  "s03.status.off_site":       { en: "Off site",               es: "Fuera del sitio" },
  "s03.add":                   { en: "Add Equipment",          es: "Agregar equipo" },

  // Section 04 — Activity Cards
  "s04.title":                 { en: "Activity Cards",         es: "Tarjetas de Actividad" },
  "s04.desc":                  { en: "One card per work item. Feeds ODS production facts on submit.",
                                 es: "Una tarjeta por actividad. Alimenta las bases de producción al enviar." },
  "s04.empty":                 { en: "No activity cards yet. Add one for each work item completed today.",
                                 es: "Sin tarjetas aún. Agrega una por cada actividad completada hoy." },
  "s04.area":                  { en: "Work area",              es: "Área de trabajo" },
  "s04.area.ph":               { en: "e.g. Parent Loop East",  es: "ej. Loop Este" },
  "s04.activity":              { en: "Activity",               es: "Actividad" },
  "s04.activity.ph":           { en: "e.g. Base grading",      es: "ej. Nivelación de base" },
  "s04.quantity":              { en: "Quantity",               es: "Cantidad" },
  "s04.unit":                  { en: "Unit",                   es: "Unidad" },
  "s04.status":                { en: "Status",                 es: "Estado" },
  "s04.status.on_track":       { en: "On track",               es: "En curso" },
  "s04.status.ahead":          { en: "Ahead",                  es: "Adelantado" },
  "s04.status.delayed":        { en: "Delayed",                es: "Retrasado" },
  "s04.status.blocked":        { en: "Blocked",                es: "Bloqueado" },
  "s04.status.complete":       { en: "Complete",               es: "Completo" },
  "s04.notes":                 { en: "Notes (optional)",       es: "Notas (opcional)" },
  "s04.notes.ph":              { en: "Anything the PM should know about this activity",
                                 es: "Cualquier cosa que el PM deba saber sobre esta actividad" },
  "s04.add":                   { en: "Add Activity Card",      es: "Agregar tarjeta" },

  // Section 05 — Constraints
  "s05.title":                 { en: "Delays · Constraints · Extra Work", es: "Retrasos · Restricciones · Trabajo extra" },
  "s05.desc":                  { en: "Tap what happened. Each selection opens a structured follow-up card.",
                                 es: "Toca lo que pasó. Cada selección abre una tarjeta de detalle." },
  "s05.what":                  { en: "What happened",          es: "Qué pasó" },
  "s05.duration":              { en: "Duration (minutes)",     es: "Duración (minutos)" },
  "s05.party":                 { en: "Responsible party",      es: "Responsable" },
  "s05.party.ph":              { en: "Who owns the resolution", es: "Quién resolverá" },
  "s05.impact":                { en: "Impact / needed action", es: "Impacto / acción necesaria" },
  "s05.remove":                { en: "Remove",                 es: "Quitar" },
  "s05.cat.weather":           { en: "Weather",                es: "Clima" },
  "s05.cat.equipment":         { en: "Equipment",              es: "Equipo" },
  "s05.cat.utility_conflict":  { en: "Utility conflict",       es: "Conflicto de servicios" },
  "s05.cat.inspection_delay":  { en: "Inspection delay",       es: "Retraso de inspección" },
  "s05.cat.material_delay":    { en: "Material delay",         es: "Retraso de material" },
  "s05.cat.survey_model_issue":{ en: "Survey / model",         es: "Topografía / modelo" },
  "s05.cat.subcontractor_issue":{ en:"Subcontractor",          es: "Subcontratista" },
  "s05.cat.owner_ceo_decision":{ en: "Owner / CEI decision",   es: "Cliente / decisión CEI" },
  "s05.cat.traffic_control":   { en: "Traffic control",        es: "Control de tráfico" },
  "s05.cat.manpower":          { en: "Manpower",               es: "Mano de obra" },
  "s05.cat.extra_work":        { en: "Extra work",             es: "Trabajo extra" },
  "s05.cat.safety_stop":       { en: "Safety stop",            es: "Alto de seguridad" },
  "s05.cat.quality_rework":    { en: "Quality / rework",       es: "Calidad / retrabajo" },
  "s05.cat.other":             { en: "Other",                  es: "Otro" },

  // Section 06 — Tomorrow
  "s06.title":                 { en: "Tomorrow / Follow-Up",    es: "Mañana / Seguimiento" },
  "s06.crew_needs":            { en: "Crew needs for tomorrow", es: "Necesidades de cuadrilla mañana" },
  "s06.equip_needs":           { en: "Equipment needs for tomorrow", es: "Necesidades de equipo mañana" },
  "s06.material_needs":        { en: "Materials needed",        es: "Materiales necesarios" },
  "s06.inspection":            { en: "Inspection needed?",      es: "¿Se necesita inspección?" },
  "s06.survey":                { en: "Survey / model needed?",  es: "¿Se necesita topografía/modelo?" },
  "s06.decisions":             { en: "Decisions needed from PM / CEI", es: "Decisiones necesarias del PM / CEI" },
  "s06.optional":              { en: "Optional",                es: "Opcional" },

  // Section 07 — Safety
  "s07.title":                 { en: "Safety · Quality",        es: "Seguridad · Calidad" },
  "s07.incident":              { en: "Any safety incident or near-miss today?", es: "¿Hubo incidente o casi-incidente de seguridad hoy?" },
  "s07.injuries":              { en: "Any injuries reported?",  es: "¿Se reportaron lesiones?" },
  "s07.notified":              { en: "Safety notified of incidents / near-misses?",
                                 es: "¿Se notificó a Seguridad de incidentes o casi-incidentes?" },
  "s07.quality_notes":         { en: "Quality / QA-QC concerns or rework today?",
                                 es: "¿Hubo temas de Calidad / QA-QC o retrabajos hoy?" },

  // Section 08 — Photos
  "s08.title":                 { en: "Field Photos",            es: "Fotos de campo" },
  "s08.desc":                  { en: "At least six field photos are required. Photos flow to the Job Photos mirror and become evidence for activities and constraints.",
                                 es: "Se requieren al menos seis fotos. Las fotos van al espejo Job Photos y se usan como evidencia." },
  "s08.min.warn":              { en: "more photo(s) needed before submit.", es: "más foto(s) antes de enviar." },
  "s08.min.ok":                { en: "Minimum photo requirement met.", es: "Requisito mínimo de fotos cumplido." },
  "s08.badge":                 { en: "required",                es: "requerido" },
  // Section 08b — Items to Verify
  "s08b.title":                { en: "Items To Verify From Photos", es: "Elementos a verificar de las fotos" },
  "s08b.desc":                 { en: "A couple of photos look like they may need a quick check. Confirm or mark not applicable.",
                                 es: "Algunas fotos podrían necesitar una revisión rápida. Confirma o marca no aplica." },
  "s08b.confirm":              { en: "Confirm",                 es: "Confirmar" },
  "s08b.na":                   { en: "Not applicable",          es: "No aplica" },

  // Section 09 — Daily Operational Summary
  "s09.title":                 { en: "Daily Operational Summary", es: "Resumen Operacional del Día" },
  "s09.desc":                  { en: "Review the summary below before submitting. Edit anything that needs corrected · you remain the source of truth.",
                                 es: "Revisa el resumen antes de enviar. Corrige cualquier cosa que haga falta · tú eres la fuente de la verdad." },
  "s09.empty":                 { en: "Add Day Setup, at least one Activity Card, and Photos. A summary will be drafted for you here.",
                                 es: "Agrega la Configuración del Día, al menos una tarjeta de actividad y fotos. Aquí se preparará un resumen." },
  "s09.loading":               { en: "Drafting your daily summary from what you entered…",
                                 es: "Preparando el resumen del día con lo que ingresaste…" },
  "s09.accepted":              { en: "accepted",                es: "aceptado" },
  "s09.draft":                 { en: "draft",                   es: "borrador" },
  "s09.accept":                { en: "Accept Summary",          es: "Aceptar resumen" },
  "s09.save":                  { en: "Save Summary",            es: "Guardar resumen" },
  "s09.edit":                  { en: "Edit Summary",            es: "Editar resumen" },
  "s09.cancel":                { en: "Cancel Edit",             es: "Cancelar edición" },
  "s09.regenerate":            { en: "Regenerate Summary",      es: "Regenerar resumen" },
  "s09.regenerating":          { en: "Regenerating…",           es: "Regenerando…" },

  // Section 10 — Signature + Submit
  "s10.title":                 { en: "Signature + Submit",      es: "Firma + Envío" },
  "s10.sign_label":            { en: "Prepared by · signature", es: "Preparado por · firma" },
  "s10.badge":                 { en: "submit blocked",          es: "envío bloqueado" },
  "s10.submit":                { en: "Submit Daily Report (preview)", es: "Enviar Reporte Diario (vista previa)" },
  "s10.submit.hint":           { en: "Submit is intentionally disabled in preview · Track G certifies cutover",
                                 es: "El envío está deshabilitado en vista previa · Track G certifica la migración" },
  "s10.status.ready":          { en: "Ready · submit enabled at cutover", es: "Listo · envío habilitado en la migración" },
  "s10.status.notready_more_photos": { en: "more photo(s) · ", es: "más foto(s) · " },
  "s10.status.notready_sig":   { en: "signature required · ",   es: "firma requerida · " },
  "s10.status.notready_prefix":{ en: "Not ready · ",            es: "No listo · " },
  "s10.status.notready_suffix":{ en: "preview mode",            es: "modo vista previa" },
};

const LSKEY = "dr_v2_field_lang";

function readInitialLang() {
  try {
    const v = localStorage.getItem(LSKEY);
    return v === "es" ? "es" : "en";
  } catch (_) {
    return "en";
  }
}

const LangCtx = React.createContext({
  lang: "en",
  setLang: () => {},
  t: (k) => k,
});

export function DrV2LangProvider({ children }) {
  const [lang, setLangState] = React.useState(readInitialLang);
  const setLang = React.useCallback((v) => {
    const next = v === "es" ? "es" : "en";
    setLangState(next);
    try {
      localStorage.setItem(LSKEY, next);
    } catch (_) {
      /* ignore */
    }
  }, []);
  const t = React.useCallback(
    (key) => {
      const row = DICTIONARY[key];
      if (!row) {
        // eslint-disable-next-line no-console
        if (process.env.NODE_ENV !== "production") console.warn("[dr-v2-lang] missing key", key);
        return key;
      }
      return row[lang] || row.en || key;
    },
    [lang],
  );
  return (
    <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>
  );
}

export function useDrV2Lang() {
  return React.useContext(LangCtx);
}

/** Simple bilingual toggle used in the header. */
export function LangToggle({ testid = "dr-v2-lang-toggle" }) {
  const { lang, setLang, t } = useDrV2Lang();
  const btn = (val, label) => (
    <button
      key={val}
      type="button"
      onClick={() => setLang(val)}
      className={`h-9 px-3 text-xs font-mono uppercase tracking-widest font-bold border-2 ${
        lang === val
          ? "bg-red-700 text-white border-red-700"
          : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
      } ${val === "en" ? "rounded-l-md" : "rounded-r-md -ml-[2px]"}`}
      data-testid={`${testid}-${val}`}
      aria-label={t("lang.toggle_label")}
      aria-pressed={lang === val}
    >
      {label}
    </button>
  );
  return (
    <div className="inline-flex" data-testid={testid}>
      {btn("en", "EN")}
      {btn("es", "ES")}
    </div>
  );
}
