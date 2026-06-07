// Lightweight bilingual support for the MASCI Safety Hub.
// English is the canonical language — all submitted data is stored in English.
// Spanish is a read/fill aid for Spanish-speaking crew members on forms.
//
// Usage:
//   import { useT } from "@/lib/i18n";
//   const { t, lang, setLang } = useT();
//   <h1>{t("Job Site Safety Inspection")}</h1>

import { useSyncExternalStore } from "react";

const STORAGE_KEY = "masci.lang";
const VALID = new Set(["en", "es"]);

let _listeners = new Set();
let _current = "en";

// Mirror current language onto the <html lang="…"> attribute. Browsers use
// this to pick the dictionary for native spell-check on <input>/<textarea>,
// which gives Spanish-speaking crews Spanish red-underline spell check while
// they fill out the form.
const _syncHtmlLang = () => {
  if (typeof document !== "undefined" && document.documentElement) {
    document.documentElement.lang = _current;
  }
};

if (typeof window !== "undefined") {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored && VALID.has(stored)) _current = stored;
  } catch {
    /* localStorage unavailable */
  }
  _syncHtmlLang();
}

export const getLang = () => _current;

export const setLang = (l) => {
  if (!VALID.has(l) || l === _current) return;
  _current = l;
  try {
    window.localStorage.setItem(STORAGE_KEY, l);
  } catch {
    /* noop */
  }
  _syncHtmlLang();
  _listeners.forEach((fn) => fn());
};

const subscribe = (cb) => {
  _listeners.add(cb);
  return () => _listeners.delete(cb);
};

// ---- Spanish dictionary ---------------------------------------------------
// Keys are the exact English strings used in the UI. Missing key → fall back
// to the English key itself, so wrapping a string with t(...) is safe even
// before the Spanish translation lands.
const ES = {
  // iter432 · Phase 30 · Part 6 · Field Memory glance (calm role-hub
  // additive operational-attention surface). Operational language only.
  "Recent field memory": "Memoria operacional reciente",
  "No recent operational notes.": "No hay notas operacionales recientes.",
  "Project": "Proyecto",
  "Equipment": "Equipo",
  "Assignment": "Asignación",
  "Recovery": "Recuperación",
  "Note": "Nota",
  "just now": "ahora",
  "min ago": "min atrás",
  "hr ago": "h atrás",
  // iter434 · Phase 31 · Work Recovery Continuity strings.
  "You have unsaved work from earlier.": "Tienes trabajo sin guardar de antes.",
  "Your work is saved on this device until it is submitted.":
    "Tu trabajo se guarda en este dispositivo hasta que se envíe.",
  "Restore": "Restaurar",
  "Discard": "Descartar",
  "Draft restored": "Borrador restaurado",
  "Draft discarded": "Borrador descartado",
  "Photo saved on this device · will send when online.":
    "Foto guardada en este dispositivo · se enviará cuando haya conexión.",
  "waiting to send": "esperando enviar",
  // iter437 · Phase 31.1 · Daily Report Crew Memory Continuity strings.
  // Operational language ONLY · banned-word list enforced
  // (no profile / template / cache / autofill / synced / account / memory).
  "Use yesterday's crew and equipment setup from this device?":
    "¿Usar la configuración de cuadrilla y equipo de ayer de este dispositivo?",
  "Saved setups stay only on this device.":
    "Las configuraciones guardadas permanecen solo en este dispositivo.",
  "Use this option only if this is your crew device or personal device.":
    "Usa esta opción solo si este es el dispositivo de tu cuadrilla o personal.",
  "You can edit crew and equipment after loading.":
    "Puedes editar cuadrilla y equipo después de cargar.",
  "Starting blank will not erase previously submitted reports.":
    "Empezar en blanco no borra los informes ya enviados.",
  "Use Setup": "Usar configuración",
  "Start Blank": "Empezar en blanco",
  "Clear Saved Setup": "Borrar configuración guardada",
  "Name this setup": "Nombrar esta configuración",
  "Optional · name this setup": "Opcional · nombrar esta configuración",
  "e.g. Paving Crew A": "p.ej. Cuadrilla de Pavimentación A",
  "Save name": "Guardar nombre",
  "saved": "guardada",
  "today": "hoy",
  "yesterday": "ayer",
  "days ago": "días atrás",
  "crew member": "miembro de cuadrilla",
  "crew members": "miembros de cuadrilla",
  "subcontractor": "subcontratista",
  "subcontractors": "subcontratistas",
  "equipment item": "equipo",
  "equipment items": "equipos",
  "Crew setup loaded · edit anything as needed.":
    "Configuración cargada · edita lo que necesites.",
  "Saved setup cleared from this device.":
    "Configuración guardada borrada de este dispositivo.",
  // iter438 · Phase 31.1 load-trace + Phase 31 Pass C wirings.
  "Loaded from your saved setup · edit anything as needed.":
    "Cargado desde tu configuración guardada · edita lo que necesites.",
  "Loaded from {nickname} · edit anything as needed.":
    "Cargado desde {nickname} · edita lo que necesites.",
  "Saved · will send when online.":
    "Guardado · se enviará cuando haya conexión.",
  "This inspection is on this device and will upload automatically.":
    "Esta inspección está en este dispositivo y se cargará automáticamente.",
  // iter439 · Item I · Production health line strings.
  "Production verified": "Producción verificada",
  "Production unreachable": "Producción no accesible",
  "Checking production…": "Verificando producción…",
  "healthy": "sano",
  "a moment ago": "hace un momento",
  // iter440 · Last Activity line strings per portal write kind.
  "Activity": "Actividad",
  "Assignment created": "Asignación creada",
  "Operational moment logged": "Momento operacional registrado",
  "Recovery moment logged": "Momento de recuperación registrado",
  "Daily report filed": "Informe diario enviado",
  "Inspection filed": "Inspección enviada",
  "Equipment inspection filed": "Inspección de equipo enviada",
  "QA/QC inspection filed": "Inspección QA/QC enviada",
  "Incident filed": "Incidente enviado",
  "Photos waiting to send will upload when connection returns.":
    "Las fotos pendientes se enviarán cuando vuelva la conexión.",
  "Submitted reports are stored in the platform. Drafts only stay on this device.":
    "Los informes enviados se guardan en la plataforma. Los borradores solo permanecen en este dispositivo.",

  "d ago": "d atrás",

  // Branding / hub
  "MASCI Safety Hub": "Centro MASCI",
  // iter239 — Legacy "MASCI Hub" platform-identity strings retired
  // from the live UI; their dead i18n entries were pruned to avoid
  // future translation drift. "Hub" remains a normal operational
  // section label (Dispatch Hub, Field Leadership Hub, etc.).
  // "One place for every MASCI job." is now rendered directly in Hub.jsx
  // with a per-language branch (since the trailing " job" doesn't appear in
  // the Spanish version) — no t() call to translate.
  "Field reports, safety records, mechanic sign-offs, project workspaces, training, and the back-office console — every MASCI workflow in one place.":
    "Reportes de campo, registros de seguridad, firmas del taller, espacios de proyecto, capacitación y la consola de oficina — cada flujo de MASCI en un solo lugar.",
  "Safety forms, field reports, project workspaces, and the office console — all under one roof.":
    "Formularios de seguridad, reportes de campo, espacios de proyecto y la consola de oficina — todo bajo un techo.",
  "Safety": "Seguridad",
  "Field": "Campo",
  "Projects": "Proyectos",
  "Admin": "Admin",
  "Compliance": "Cumplimiento",
  "Quality Assurance": "Aseguramiento de Calidad",
  "Quality Assurance · Quality Control": "Aseguramiento de Calidad · Control de Calidad",
  "Daily Ops": "Operaciones diarias",
  "Project Workspaces": "Espacios de proyecto",
  "Office Console": "Consola de oficina",
  "Safety · Compliance": "Seguridad · Cumplimiento",
  "Field · Daily Ops": "Campo · Operaciones diarias",
  "Every form your crews need to stay OSHA-compliant and keep the company defensible.":
    "Cada formulario que tu cuadrilla necesita para cumplir con OSHA y mantener a la empresa defendible.",
  "What the crew fills out every day, before and after the shift.":
    "Lo que la cuadrilla llena cada día, antes y después del turno.",
  "Site Inspections · Safety Meetings": "Inspecciones · Juntas de Seguridad",
  "Incident Reports · JHP Plans · Trench Box Data": "Incidentes · Planes JHP · Trinchera",
  "Daily Reports — crews, subs, visitors, equipment, materials":
    "Reportes Diarios — cuadrillas, subcontratistas, visitantes, equipo, materiales",
  "Equipment Pre-Op — OSHA walk-arounds with pass/fail":
    "Pre-Op de Equipo — recorridos OSHA con aprobado/fallado",
  "Crew Hub — Basecamp-style per-job collaboration":
    "Crew Hub — colaboración por trabajo estilo Basecamp",
  "@mentions · My Stuff inbox · Activity feed":
    "@menciones · Bandeja Mi Trabajo · Actividad",
  // Basecamp + OnStation external links (replaced Crew Hub 2026-04-28)
  "Open the live MASCI Basecamp account in a new tab. All project messages, to-dos, schedules, and docs live there.":
    "Abre la cuenta de Basecamp de MASCI en una nueva pestaña. Mensajes, tareas, calendarios y documentos viven ahí.",
  "Opens 3.basecamp.com/5958093 in a new tab":
    "Abre 3.basecamp.com/5958093 en una nueva pestaña",
  "Sign in with your Basecamp credentials":
    "Inicia sesión con tus credenciales de Basecamp",
  "Open OnStation for live job staking, station mapping, and field GPS coordination.":
    "Abre OnStation para estacas de obra, mapeo de estaciones y coordinación GPS en campo.",
  "Opens app.onstation.us in a new tab":
    "Abre app.onstation.us en una nueva pestaña",
  "Sign in with your OnStation credentials":
    "Inicia sesión con tus credenciales de OnStation",
  "Project messages, to-dos, schedules, docs, and field staking all live in our two external apps. Pick one:":
    "Mensajes, tareas, calendarios, documentos y estacas de obra viven en nuestras dos aplicaciones externas. Elige una:",
  "Messages · To-dos · Schedule · Docs":
    "Mensajes · Tareas · Calendario · Documentos",
  "Field staking · Station mapping · GPS":
    "Estacas · Mapeo de estaciones · GPS",
  "Both open in a new tab. Sign in with your Basecamp / OnStation credentials.":
    "Ambas se abren en una nueva pestaña. Inicia sesión con tus credenciales de Basecamp / OnStation.",
  "Project Workspaces":
    "Espacios de Proyecto",
  // Combo dropdowns (employee/supplier/equipment) — added 2026-04-29 in the
  // big rewrite that fixed the focus-stealing bug. The combos no longer have
  // a separate search input; the main input filters the list directly.
  "Type or pick an employee…": "Escribe o elige un empleado…",
  "Type or pick a supplier…": "Escribe o elige un proveedor…",
  "Type or pick equipment…": "Escribe o elige equipo…",
  "Browse roster": "Ver lista",
  "Browse supplier list": "Ver lista de proveedores",
  "Browse fleet": "Ver flota",
  "Roster not uploaded yet — type the name freely.":
    "Lista no cargada — escribe el nombre libremente.",
  "Supplier list not uploaded yet — type freely.":
    "Lista de proveedores no cargada — escribe libremente.",
  "Equipment list not loaded yet.":
    "Lista de equipo no cargada todavía.",
  "No matches — your typed name will be saved.":
    "Sin coincidencias — el nombre que escribiste se guardará.",
  "No matches — your typed value will be saved.":
    "Sin coincidencias — el valor que escribiste se guardará.",
  "Will save as new entry:": "Se guardará como nueva entrada:",
  "Open in new tab ↗":
    "Abrir en nueva pestaña ↗",
  "Basecamp": "Basecamp",
  "OnStation": "OnStation",
  "Password-gated · view / print / delete any record":
    "Protegido con contraseña · ver / imprimir / eliminar registros",
  "Backup · Restore · Auto-email routing · Posters":
    "Respaldo · Restaurar · Ruteo de correos · Carteles",
  "MASCI Operations Platform": "MASCI · Plataforma de Operaciones",
  "MASCI · Safety · No Shortcuts · No Exceptions":
    "MASCI · Seguridad · Sin Atajos · Sin Excepciones",
  "MASCI · Field · No Shortcuts · No Exceptions":
    "MASCI · Campo · Sin Atajos · Sin Excepciones",
  "One front door for every safety form.": "Una puerta de entrada para cada formulario de seguridad.",
  "Inspections. Meetings. Hazards. Incidents. Handled.":
    "Inspecciones. Reuniones. Peligros. Incidentes. Resueltos.",
  "Every field-safety form. One digital home.":
    "Cada formulario de seguridad de campo. Un hogar digital.",

  // ============================================================
  // Daily Report
  // ============================================================
  "Daily Reports": "Reportes Diarios",
  // Section 04 — MASCI Crews on Site (rebuilt 2026-04-28)
  "Crew Member": "Miembro de Cuadrilla",
  "Add Crew Member": "Agregar Miembro de Cuadrilla",
  "Employee Name": "Nombre del Empleado",
  "Trade / Role": "Oficio / Rol",
  "Hours": "Horas",
  "Start Time": "Hora de Inicio",
  "Stop Time": "Hora de Fin",
  "Lunch": "Almuerzo",
  "auto": "auto",
  "Total crew hours today": "Horas Totales de la Cuadrilla Hoy",
  "Type or pick from roster…": "Escriba o elija de la lista…",
  // Photo picker (used everywhere)
  "From gallery": "De la galería",
  "Take photo": "Tomar foto",
  "Pick existing photos": "Elija fotos existentes",
  "Open camera": "Abrir cámara",
  // Equipment combo
  "Type or pick a unit…": "Escriba o elija una unidad…",
  "Browse fleet": "Ver flota",
  "Tip: type freely for custom equipment not in fleet.":
    "Consejo: escriba libremente para equipo no listado en la flota.",
  "No matches — your typed value will be saved as custom.":
    "Sin coincidencias — el valor escrito se guardará tal cual.",
  "Equipment list not loaded yet.": "Lista de equipo aún no cargada.",
  "Search unit #, make, model, VIN…": "Buscar # de unidad, marca, modelo, VIN…",
  // Equipment Pre-Op — out-of-service modal
  "Stop — Major Safety Failure": "Alto — Falla de Seguridad Mayor",
  "Stop — Critical Fluid Failure": "Alto — Falla Crítica de Fluido",
  "Unit is OUT OF SERVICE": "Unidad FUERA DE SERVICIO",
  "Major safety items failing:": "Fallas de seguridad mayor:",
  "Critical fluid failure:": "Falla crítica de fluido:",
  "is marked FAIL.": "está marcado como FALLO.",
  "Do NOT operate this machine. Get with your supervisor immediately and advise that the unit is unsafe. Shop must be notified so the issue can be repaired before the unit goes back in service.":
    "NO opere esta máquina. Avise a su supervisor de inmediato — la unidad no es segura. El taller debe ser notificado para que el problema se repare antes de que la unidad regrese al servicio.",
  "Get with your supervisor immediately to refill the fluid before continuing this inspection. The inspection cannot be submitted while a critical fluid level is failing — running this unit could cause severe damage or injury.":
    "Avise a su supervisor de inmediato para rellenar el fluido antes de continuar con esta inspección. La inspección no puede enviarse mientras un nivel de fluido crítico esté fallando — operar esta unidad podría causar daños severos o lesiones.",
  "Required actions:": "Acciones requeridas:",
  "Tell your supervisor — do not operate.": "Avise a su supervisor — no opere.",
  "Notify shop so unit can be repaired.": "Notifique al taller para que la unidad sea reparada.",
  "Tag-out the machine.": "Coloque tarjeta de bloqueo en la máquina.",
  "Once the fluid is filled:": "Una vez rellenado el fluido:",
  "change the item from FAIL to PASS, then continue the inspection.":
    "cambie el ítem de FALLO a APROBADO y continúe con la inspección.",
  "I'll get my supervisor": "Voy por mi supervisor",
  "Out of Service": "Fuera de Servicio",
  "Needs Attention": "Requiere Atención",

  "Type or pick a supplier…": "Escriba o elija un proveedor…",
  "Browse supplier list": "Ver lista de proveedores",
  "Search by company name…": "Buscar por nombre de la compañía…",
  "Supplier list not uploaded yet — type freely.":
    "Lista de proveedores aún no cargada — escriba libremente.",
  "Tip: type freely for one-off vendors not in the list.":
    "Consejo: escriba libremente para proveedores no listados.",
  // Employee combo
  "Type or pick an employee…": "Escriba o elija un empleado…",
  "Browse roster": "Ver lista de empleados",
  "Search by name, ID, trade…": "Buscar por nombre, ID, oficio…",
  "Roster not uploaded yet — type the name freely.":
    "Lista de empleados aún no cargada — escriba el nombre libremente.",
  "Tip: type freely for anyone not in the roster.":
    "Consejo: escriba libremente para alguien fuera de la lista.",
  "Daily Job Report": "Reporte Diario del Trabajo",
  "Today's site activity, captured.": "La actividad del sitio de hoy, registrada.",
  "Crews · subs · visitors · equipment · materials · weather · photos. One record per crew, per day.":
    "Cuadrillas · subcontratistas · visitantes · equipo · materiales · clima · fotos. Un registro por cuadrilla, por día.",
  "End-of-day site log: crews, subs, visitors, equipment, materials, weather, photos. Replaces Fieldwire.":
    "Registro de fin de día: cuadrillas, subcontratistas, visitantes, equipo, materiales, clima, fotos.",
  "No daily reports yet": "Aún no hay reportes diarios",
  "File one before the crew leaves the site at end of day.":
    "Archive uno antes de que la cuadrilla se vaya al final del día.",
  "File First Report": "Archivar Primer Reporte",
  "Recent Reports": "Reportes Recientes",
  "on file": "en archivo",
  "Prepared by": "Preparado por",
  "Prepared By *": "Preparado Por *",
  "Prepared By Signature": "Firma de Preparado Por",
  "Prepared By": "Preparado Por",
  "Foreman / Superintendent": "Capataz / Superintendente",
  "Superintendent": "Superintendente",
  "Superintendent Signature": "Firma del Superintendente",
  "Report #": "Reporte #",
  "View": "Ver",
  "crew": "cuadrilla",
  "subs": "subs",
  "visitors": "visitantes",
  "Weather": "Clima",
  "Refresh Weather": "Actualizar Clima",
  "Capture GPS to auto-load today's weather. Refresh anytime.":
    "Capture GPS para cargar el clima de hoy automáticamente. Actualice cuando sea necesario.",
  "No weather data yet — tap Use GPS above.":
    "Aún no hay datos de clima — toque Usar GPS arriba.",
  "General Information": "Información General",
  "Schedule Delays Today?": "¿Retrasos de Cronograma Hoy?",
  "Weather Impact?": "¿Impacto del Clima?",
  "Any Accidents on Site?": "¿Algún Accidente en el Sitio?",
  "Any Injuries Reported?": "¿Lesiones Reportadas?",
  "Detail any 'Yes' answers": "Detalle cualquier respuesta 'Sí'",
  "Describe delays, weather impact, accidents, injuries...":
    "Describa retrasos, impacto del clima, accidentes, lesiones...",
  "General Notes": "Notas Generales",
  "Anything else worth noting from today...":
    "Cualquier otra cosa que valga la pena anotar de hoy...",
  // Safety escalation gate
  "Safety Escalation Required": "Escalación de Seguridad Requerida",
  "An accident or injury was reported today. Complete the safety escalation steps before submitting this report.":
    "Se reportó un accidente o lesión hoy. Complete los pasos de escalación de seguridad antes de enviar este reporte.",
  "Was Safety notified? *": "¿Se notificó a Seguridad? *",
  "STOP — Contact Safety immediately.": "ALTO — Contacte a Seguridad inmediatamente.",
  "You cannot submit this Daily Report until Safety has been notified. Call your Safety Manager now, then return and mark Yes above.":
    "No puede enviar este Reporte Diario hasta que se haya notificado a Seguridad. Llame al Gerente de Seguridad ahora, luego regrese y marque Sí arriba.",
  "Who Was Contacted? *": "¿A Quién se Contactó? *",
  "Name + role (e.g. Jaymn Judd, Safety Mgr)":
    "Nombre + cargo (ej. Jaymn Judd, Gerente de Seguridad)",
  "Time of Contact *": "Hora de Contacto *",
  "Has the Accident/Incident Report been filled out? *":
    "¿Se ha completado el Reporte de Accidente/Incidente? *",
  "STOP — File the Incident Report first.":
    "ALTO — Presente primero el Reporte de Incidente.",
  "An Accident/Incident Report MUST be filed before this Daily Report can be submitted.":
    "DEBE presentarse un Reporte de Accidente/Incidente antes de poder enviar este Reporte Diario.",
  "Open Incident Report Form": "Abrir Formulario de Reporte de Incidente",
  "Time Incident Report Was Filed *":
    "Hora en que se Presentó el Reporte de Incidente *",
  "MASCI Crews on Site": "Cuadrillas MASCI en Sitio",
  "Subcontractors on Site": "Subcontratistas en Sitio",
  "Site Visitors": "Visitantes del Sitio",
  "Equipment Log": "Registro de Equipo",
  "Material Deliveries": "Entregas de Materiales",
  "Activity / Production Log": "Registro de Actividad / Producción",
  "Crew": "Cuadrilla",
  "Subcontractor": "Subcontratista",
  "Visitor": "Visitante",
  "Equipment": "Equipo",
  "Material": "Material",
  "Activity": "Actividad",
  "Trade": "Oficio",
  "Foreman": "Capataz",
  "# of Workers": "# de Trabajadores",
  "Hours Worked": "Horas Trabajadas",
  "Work Performed": "Trabajo Realizado",
  "Company": "Compañía",
  "Foreman / Lead": "Capataz / Líder",
  "Company / Agency": "Compañía / Agencia",
  "Time In": "Hora de Entrada",
  "Time Out": "Hora de Salida",
  "Purpose / Notes": "Propósito / Notas",
  "Description / ID": "Descripción / ID",
  "Hours Used": "Horas Usadas",
  "Time Delivered": "Hora de Entrega",
  "Time Removed": "Hora de Retiro",
  "Notes": "Notas",
  "Description": "Descripción",
  "Quantity": "Cantidad",
  "Unit": "Unidad",
  "Supplier": "Proveedor",
  "Ticket #": "Ticket #",
  "% Complete": "% Completo",
  "Station / Loc From": "Estación / Loc Desde",
  "Station / Loc To": "Estación / Loc Hasta",
  "Photo minimum met. Add more if helpful.":
    "Mínimo de fotos cumplido. Agregue más si es útil.",
  "Add at least": "Agregue al menos",
  "more photo(s)": "foto(s) más",
  "Sign-Off": "Firma de Cierre",
  "Submit Daily Report": "Enviar Reporte Diario",
  "Document compliance, run toolbox talks, and analyze hazards before every task. Print or save any record as a branded PDF — works from any device.":
    "Documente el cumplimiento, dirija charlas de seguridad y analice los peligros antes de cada tarea. Imprima o guarde cualquier registro como PDF — funciona en cualquier dispositivo.",
  "No Shortcuts": "Sin Atajos",
  "No Exceptions": "Sin Excepciones",
  // === Tagline (2026-05 rebrand) ===
  // Replaces "Accountability · Adapt · Overcome" everywhere.
  "No Guesswork.": "Sin Adivinanzas.",
  "No Missed Steps.": "Sin Pasos Omitidos.",
  "No Excuses.": "Sin Excusas.",
  "No Guesswork. No Missed Steps. No Excuses.":
    "Sin Adivinanzas. Sin Pasos Omitidos. Sin Excusas.",
  "MASCI · No Guesswork. No Missed Steps. No Excuses.":
    "MASCI · Sin Adivinanzas. Sin Pasos Omitidos. Sin Excusas.",
  "MASCI · Safety · No Guesswork. No Missed Steps. No Excuses.":
    "MASCI · Seguridad · Sin Adivinanzas. Sin Pasos Omitidos. Sin Excusas.",
  "MASCI · Field · No Guesswork. No Missed Steps. No Excuses.":
    "MASCI · Campo · Sin Adivinanzas. Sin Pasos Omitidos. Sin Excusas.",
  // Hub homepage subtext (2026-05 rebrand)
  "Daily reports, safety enforcement, equipment tracking, training, and complete documentation — automatically captured, routed, and stored in one system.":
    "Reportes diarios, seguridad, seguimiento de equipos, capacitación y documentación completa — capturados, enrutados y almacenados automáticamente en un solo sistema.",
  // Hub "New here?" Day-1 entry banner (iter218 · localized iter236)
  "New here?": "¿Nuevo aquí?",
  "First week on the platform — start here":
    "Primera semana en la plataforma — comience aquí",
  "A 5-minute walkthrough for new hires: what to fill out, where, and why.":
    "Un recorrido de 5 minutos para nuevos empleados: qué llenar, dónde y por qué.",
  "Quality assurance and quality control inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.":
    "Inspecciones de aseguramiento y control de calidad para concreto, varilla y trabajo de subcontratistas — documentadas, firmadas, fotografiadas, enrutadas y almacenadas.",
  "Site Inspections": "Inspecciones de Obra",
  "Safety Meetings": "Reuniones de Seguridad",
  "Job Hazard Plan": "Plan de Peligros del Trabajo",
  "Start Form": "Iniciar Formulario",
  "Open Library": "Abrir Biblioteca",
  "Open Plans": "Abrir Planes",
  "Open Cards": "Abrir Tarjetas",
  "Incident Reports": "Reportes de Incidentes",
  "Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.":
    "Inspecciones diarias y semanales del sitio. EPP, control de tránsito, protección contra caídas, eléctrico y más — calificadas automáticamente.",
  "Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.":
    "Charlas de seguridad y reuniones diarias. Más de 80 temas con peligros prellenados — cada miembro de la cuadrilla firma.",
  "Pre-built by Safety, PMs, and leadership before work begins. Crews review and follow — they don't fill it out.":
    "Preparado por Seguridad, PMs y el liderazgo antes de comenzar el trabajo. Las cuadrillas revisan y siguen — no lo llenan.",
  "Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.":
    "Documente cuasi-accidentes, lesiones y daños. Niveles de severidad, causa raíz, testigos y seguimiento — todo en un registro.",

  // Equipment Pre-Op
  "Equipment Pre-Op": "Inspección de Equipo",
  "Equipment Pre-Op Inspection": "Inspección Pre-Operación de Equipo",
  "Daily OSHA walk-around inspections for Heavy Equipment. PASS / FAIL each item — fail tags the unit out of service.":
    "Recorrido diario OSHA para Equipo Pesado. APROBADO / FALLA por cada punto — una falla deja la máquina fuera de servicio.",
  "OSHA daily walk-around for the unit you're operating. Mark every item — anything FAIL tags the machine OUT OF SERVICE until shop verifies.":
    "Recorrido diario OSHA del equipo que está operando. Marque cada punto — cualquier FALLA deja la máquina FUERA DE SERVICIO hasta que el taller la verifique.",
  "FAIL — DO NOT OPERATE": "FALLA — NO OPERAR",
  "item(s) failed inspection. This unit will be tagged OUT OF SERVICE on the report.":
    "punto(s) fallaron. Esta unidad quedará marcada FUERA DE SERVICIO en el reporte.",
  "Project & Operator": "Proyecto y Operador",
  "Equipment": "Equipo",
  "Equipment Type *": "Tipo de Equipo *",
  "Select equipment type": "Seleccione tipo de equipo",
  "Loading…": "Cargando…",
  "Saved units": "Unidades guardadas",
  "Search saved units…": "Buscar unidades guardadas…",
  "No matches.": "Sin resultados.",
  "Unit # / Label *": "Unidad # / Etiqueta *",
  "Make": "Marca",
  "Model": "Modelo",
  "Serial #": "Número de Serie",
  "Hour Meter": "Horómetro",
  "Odometer": "Odómetro",
  "Hour Meter / Odometer": "Horómetro / Odómetro",
  "Hour Meter / Odometer *": "Horómetro / Odómetro *",
  "Required — enter hours OR miles.": "Requerido — ingrese horas O millas.",
  "Leave blank if no hour meter.": "Deje en blanco si no hay horómetro.",
  "Leave blank if no odometer.": "Deje en blanco si no hay odómetro.",
  "Operator Name *": "Nombre del Operador *",
  "Your full name": "Su nombre completo",
  "Pass": "Cumple",
  "Fail": "No Cumple",
  "PASS": "CUMPLE",
  "N/A": "N/A",
  "Describe the issue (required for FAIL — min 10 characters)":
    "Describa el problema (requerido para NO CUMPLE — mínimo 10 caracteres)",
  "Description required for FAIL": "Descripción requerida para NO CUMPLE",
  "At least 10 characters required": "Mínimo 10 caracteres requeridos",
  "Description": "Descripción",
  "Replace photo": "Reemplazar foto",
  "Add photo (required for FAIL)": "Agregar foto (requerida para NO CUMPLE)",
  "Tally": "Resumen",
  "Hide tally": "Ocultar resumen",
  "Notes & Photos": "Notas y Fotos",
  "Deficiency notes": "Notas de deficiencias",
  "What's wrong — be specific": "Qué está mal — sea específico",
  "Corrective actions": "Acciones correctivas",
  "What's being done about it": "Qué se está haciendo al respecto",
  "Equipment Photos": "Fotos del Equipo",
  "Operator Sign-Off": "Firma del Operador",
  "I certify that I performed this pre-shift inspection of the listed equipment and that the conditions noted above are true and accurate. I will not operate this unit if any item is marked FAIL.":
    "Certifico que realicé esta inspección pre-turno del equipo listado y que las condiciones anotadas son verdaderas y precisas. No operaré esta unidad si algún punto está marcado FALLA.",
  "Operator Signature *": "Firma del Operador *",
  "Submit Inspection": "Enviar Inspección",
  "New": "Nuevo",
  "Good": "Bueno",
  "Fair": "Regular",
  "Condition": "Condición",
  "Initial Training": "Capacitación Inicial",
  "Refresher": "Repaso",
  "Retraining": "Reentrenamiento",
  "Open": "Abrir",
  "report on file": "reporte en archivo",
  "reports on file": "reportes en archivo",
  "meeting logged": "reunión registrada",
  "meetings logged": "reuniones registradas",
  "analysis on file": "análisis en archivo",
  "analyses on file": "análisis en archivo",
  "Recent Activity": "Actividad Reciente",
  "Loading...": "Cargando...",
  "MASCI · Job Site Safety Program": "MASCI · Programa de Seguridad del Sitio",
  "MASCI · Field Safety Reporting Portal":
    "MASCI · Portal de Reportes de Seguridad de Campo",
  // iter241 — Localization continuity completion pass. The platform
  // was already strongly bilingual; the remaining English fragments
  // (footer link labels, guidance-hub section titles, portal-track
  // labels, training-hub banner) now have their ES counterparts so
  // Spanish-speaking field crews don't encounter random English on
  // shared/common surfaces.
  //
  // Footer link primitives (rendered uppercase via CSS).
  "Terms": "Términos",
  "Privacy": "Privacidad",
  //
  // Operational Guidance Center — SECTIONS (backend-driven, frontend
  // now wraps `s.title` in t()).
  "Role-Based Training": "Capacitación por Rol",
  "Task-Based Quick Help": "Ayuda Rápida por Tarea",
  "Portal Guides": "Guías de Portal",
  "Troubleshooting": "Solución de Problemas",
  "Why It Matters": "Por Qué Importa",
  "Backups & Data Portability": "Respaldos y Portabilidad de Datos",
  "New User Onboarding": "Orientación para Usuarios Nuevos",
  //
  // Operational Guidance Center — PORTAL_TRACKS labels.
  "HR Portal": "Portal de RH",
  "Safety Portal": "Portal de Seguridad",
  "Shop / Fleet Portal": "Portal de Taller / Flota",
  "Dispatch Portal": "Portal de Despacho",
  "PM Portal": "Portal de PM",
  "Field Leadership Portal": "Portal de Liderazgo de Campo",
  "Admin Console": "Consola de Administración",
  //
  // Training Hub — operational-guidance banner that links from
  // /training → /guidance.
  "New · Operational Guidance Center": "Nuevo · Centro de Guía Operacional",
  "How and why to run MASCI operations":
    "Cómo y por qué operar MASCI",
  "Role-based training · task-based help · troubleshooting · why each workflow matters. Filtered to your portal access.":
    "Capacitación por rol · ayuda por tarea · solución de problemas · por qué importa cada flujo. Filtrado por su acceso al portal.",
  //
  // ── End iter241 entries ──

  // ────────────────────────────────────────────────────────────────────
  // iter241b — Operator-surfaced second pass: 146 missing translations
  // on the explicit user journey (Hub → guidance → training → portal
  // login → password flows). All strings were already wrapped in t();
  // they were silently falling back to English because the ES
  // dictionary had no entry. Translated as a single batch so
  // Spanish-speaking crews don't keep encountering random English
  // fragments while moving through the system.
  // ────────────────────────────────────────────────────────────────────

  // Hub homepage — additional surfaces beyond iter241a
  "Welcome back": "Bienvenido de nuevo",
  "Signed in": "Sesión iniciada",
  "Tap to jump back into your": "Toque para volver a su",
  "Open Portal": "Abrir Portal",
  "Open Console": "Abrir Consola",
  "Your Portals": "Sus Portales",
  "Other Portals": "Otros Portales",
  "Sign-in required. Showing portals you're authorized for.":
    "Inicio de sesión requerido. Mostrando los portales para los que está autorizado.",
  "Sign-in required. For office staff, mechanics, HR, Safety, and Dispatch.":
    "Inicio de sesión requerido. Para personal de oficina, mecánicos, RH, Seguridad y Despacho.",
  "Sign-in required. Office staff, mechanics, HR.":
    "Inicio de sesión requerido. Personal de oficina, mecánicos, RH.",
  "not in your access set": "no en su conjunto de acceso",
  "Operational Guidance Center": "Centro de Guía Operacional",
  "RBAC-aware portal training, role-based help, and operator guides.":
    "Capacitación de portal por rol, ayuda basada en tareas y guías para operadores.",
  "Step into the Hub": "Entrar al Centro",
  "Submit on Site": "Enviar en la Obra",
  "Run every job. Control every detail.":
    "Dirija cada trabajo. Controle cada detalle.",
  "Safety command center — incidents, audits, corrective actions, training.":
    "Centro de mando de seguridad — incidentes, auditorías, acciones correctivas, capacitación.",
  "Equipment movement, availability, transfers, and utilization.":
    "Movimiento, disponibilidad, transferencias y utilización de equipos.",
  "Mechanics · out-of-service queue · Pre-Op FAILs · sign-offs.":
    "Mecánicos · cola fuera de servicio · FALLOS Pre-Op · aprobaciones.",
  "Project managers · active jobs · routing · fleet · staff.":
    "Gerentes de proyecto · trabajos activos · enrutamiento · flota · personal.",
  "Employee accountability · time verification · payroll cross-check.":
    "Responsabilidad del empleado · verificación de tiempo · cruce de nómina.",
  "Supervisor forms · crew accountability · equipment checkout.":
    "Formularios de supervisor · responsabilidad de cuadrilla · entrega de equipos.",
  "Dispatch": "Despacho",
  "Quality & Compliance": "Calidad y Cumplimiento",
  "Public · no sign-in required.": "Público · sin inicio de sesión.",
  "Concrete · Rebar · Subcontractor Inspections. Sign on screen, submit, instant PDF + record.":
    "Inspecciones de Concreto · Acero · Subcontratista. Firme en pantalla, envíe, PDF + registro al instante.",
  "Daily Reports · Equipment Pre-Op walk-arounds. GPS auto-fills location, weather auto-loads, photos attach instantly.":
    "Reportes Diarios · Inspecciones Pre-Op de equipos. GPS llena ubicación, clima se carga automáticamente, fotos se adjuntan al instante.",
  "Inspections · Toolbox Talks · Incidents · JHPs · Trench Box reference. Routed to the office in 60 seconds.":
    "Inspecciones · Charlas de Caja de Herramientas · Incidentes · Planes JHP · Referencia de Caja de Zanja. Enrutado a la oficina en 60 segundos.",

  // Sign-in master entry
  "MASCI Operations Platform · Master Sign-In":
    "Plataforma de Operaciones MASCI · Inicio de Sesión Principal",
  "Single-Portal Sign-In": "Inicio de Sesión de Portal Único",
  "Multi-portal sign-in for accounts with access to more than one portal. Single-portal employees, use your portal":
    "Inicio de sesión multi-portal para cuentas con acceso a más de un portal. Empleados de un solo portal, use su portal",
  "Operations Platform": "Plataforma de Operaciones",
  "Master Password": "Contraseña Principal",
  "Enter your work email and master password":
    "Ingrese su correo de trabajo y contraseña principal",
  "Signing in…": "Iniciando sesión…",
  "Sign-in failed": "Falló el inicio de sesión",
  "Sign-in failed — try again": "Falló el inicio de sesión — intente de nuevo",
  "Invalid email or password": "Correo o contraseña inválidos",
  "Welcome": "Bienvenido",
  "Signed in to": "Sesión iniciada en",
  "Signed in as": "Sesión iniciada como",

  // Universal login form primitives (used across every portal)
  "Work Email": "Correo de Trabajo",
  "Work email": "Correo de trabajo",
  "Remember me on this device": "Recordarme en este dispositivo",
  "Forgot password?": "¿Olvidó su contraseña?",
  "Forgot password": "Olvidó su contraseña",
  "Enter your work email": "Ingrese su correo de trabajo",
  "Enter your password": "Ingrese su contraseña",
  "Enter your work email and password":
    "Ingrese su correo de trabajo y contraseña",
  "Sending…": "Enviando…",
  "Saving…": "Guardando…",
  "Wrong email or password": "Correo o contraseña incorrectos",
  "Too many requests — wait a minute and try again":
    "Demasiadas solicitudes — espere un minuto e intente de nuevo",
  "Account locked — contact admin": "Cuenta bloqueada — contacte al administrador",
  "Access blocked": "Acceso bloqueado",
  "Call the office immediately": "Llame a la oficina de inmediato",
  "Back to sign in": "Volver al inicio de sesión",

  // Forgot / Reset / Change Password flows
  "Reset your password": "Restablecer su contraseña",
  "Self-service reset": "Restablecimiento de autoservicio",
  "Send reset link": "Enviar enlace de restablecimiento",
  "Email reset link": "Enviar enlace por correo",
  "If that email is on file, a reset link is on its way.":
    "Si ese correo está en nuestros registros, un enlace de restablecimiento está en camino.",
  "If this email belongs to a Dispatch user, a reset link is on its way. The link expires in 30 minutes.":
    "Si este correo pertenece a un usuario de Despacho, un enlace de restablecimiento está en camino. El enlace expira en 30 minutos.",
  "If this email belongs to a Safety user, a reset link is on its way. The link expires in 30 minutes.":
    "Si este correo pertenece a un usuario de Seguridad, un enlace de restablecimiento está en camino. El enlace expira en 30 minutos.",
  "Enter your work email. If we have you on file with an active account, we'll email you a one-time link to set a new password.":
    "Ingrese su correo de trabajo. Si lo tenemos en nuestros registros con una cuenta activa, le enviaremos un enlace de un solo uso para establecer una nueva contraseña.",
  "Enter your Dispatch Portal email. We'll send you a link to choose a new password.":
    "Ingrese su correo del Portal de Despacho. Le enviaremos un enlace para elegir una nueva contraseña.",
  "Enter your Safety Portal email. We'll send you a link to choose a new password.":
    "Ingrese su correo del Portal de Seguridad. Le enviaremos un enlace para elegir una nueva contraseña.",
  "Couldn't send reset email — try again or call the office":
    "No se pudo enviar el correo de restablecimiento — intente de nuevo o llame a la oficina",
  "This reset link is invalid or has expired.":
    "Este enlace de restablecimiento es inválido o ha expirado.",
  "This reset link is invalid or has expired. Request a new one from the HR login page.":
    "Este enlace de restablecimiento es inválido o ha expirado. Solicite uno nuevo desde la página de inicio de sesión de RH.",
  "Reset failed": "Falló el restablecimiento",
  "Reset failed — request a fresh link from /pm/login":
    "Falló el restablecimiento — solicite un nuevo enlace desde /pm/login",
  "Reset failed — request a fresh link from /shop/login":
    "Falló el restablecimiento — solicite un nuevo enlace desde /shop/login",
  "Password reset successful": "Contraseña restablecida correctamente",
  "Choose a new password": "Elija una nueva contraseña",
  "Choose your password": "Elija su contraseña",
  "Current (or temporary) password": "Contraseña actual (o temporal)",
  "Current password is incorrect": "La contraseña actual es incorrecta",
  "Enter the password": "Ingrese la contraseña",
  "Confirm new password": "Confirme la nueva contraseña",
  "New password (6+ characters)": "Nueva contraseña (6+ caracteres)",
  "New password (8+ characters)": "Nueva contraseña (8+ caracteres)",
  "New password must be at least 6 characters":
    "La nueva contraseña debe tener al menos 6 caracteres",
  "New password must be at least 8 characters":
    "La nueva contraseña debe tener al menos 8 caracteres",
  "New password must be different from the old one":
    "La nueva contraseña debe ser diferente de la anterior",
  "Password must be at least 6 characters":
    "La contraseña debe tener al menos 6 caracteres",
  "Password must be at least 8 characters":
    "La contraseña debe tener al menos 8 caracteres",
  "Passwords don't match": "Las contraseñas no coinciden",
  "Save new password": "Guardar nueva contraseña",
  "Save password & sign in": "Guardar contraseña e iniciar sesión",
  "Save password &amp; sign in": "Guardar contraseña e iniciar sesión",
  "Password updated": "Contraseña actualizada",
  "Password updated — welcome back!": "Contraseña actualizada — ¡bienvenido de nuevo!",
  "Update failed": "Falló la actualización",
  "Password rotation required — pick a new one":
    "Se requiere rotación de contraseña — elija una nueva",
  "Welcome — please choose a new password":
    "Bienvenido — por favor elija una nueva contraseña",
  "Welcome, HR": "Bienvenido, RH",
  "Welcome to Dispatch": "Bienvenido a Despacho",
  "Welcome to the Safety Portal": "Bienvenido al Portal de Seguridad",
  "Pick a new password to finish signing in.":
    "Elija una nueva contraseña para terminar de iniciar sesión.",
  "Pick a new password to finish signing in. You'll be dropped straight into the HR portal once saved.":
    "Elija una nueva contraseña para terminar de iniciar sesión. Será llevado directamente al portal de RH una vez guardada.",
  "Pick something at least 6 characters. The reset link in your email stops working as soon as you save.":
    "Elija algo de al menos 6 caracteres. El enlace de restablecimiento en su correo deja de funcionar tan pronto como guarde.",
  "Pick something at least 6 characters. The temporary password the admin issued will stop working as soon as you save.":
    "Elija algo de al menos 6 caracteres. La contraseña temporal que emitió el administrador dejará de funcionar tan pronto como guarde.",
  "Pick something at least 8 characters. The temporary password the admin issued will stop working as soon as you save.":
    "Elija algo de al menos 8 caracteres. La contraseña temporal que emitió el administrador dejará de funcionar tan pronto como guarde.",
  "Only per-PM accounts can change password here":
    "Solo las cuentas por PM pueden cambiar la contraseña aquí",
  "Only per-user accounts can change password here":
    "Solo las cuentas por usuario pueden cambiar la contraseña aquí",
  "New to this portal?": "¿Nuevo en este portal?",
  "What does this portal do?": "¿Qué hace este portal?",

  // Portal-login headings + chrome
  "PM Login": "Inicio de Sesión PM",
  "HR Login": "Inicio de Sesión RH",
  "HR Portal Sign In": "Inicio de Sesión Portal RH",
  "Human Resources": "Recursos Humanos",
  "MASCI · Human Resources Portal": "MASCI · Portal de Recursos Humanos",
  "Safety Login": "Inicio de Sesión de Seguridad",
  "Safety Portal Sign In": "Inicio de Sesión Portal de Seguridad",
  "Safety Manager, Coordinator, and Officer access. Use the credentials issued by Admin.":
    "Acceso para Gerente de Seguridad, Coordinador y Oficial. Use las credenciales emitidas por el administrador.",
  "Safety Operations": "Operaciones de Seguridad",
  "MASCI · Safety Portal": "MASCI · Portal de Seguridad",
  "Shop Login": "Inicio de Sesión Taller",
  "Dispatch Login": "Inicio de Sesión Despacho",
  "Dispatch Portal Sign In": "Inicio de Sesión Portal de Despacho",
  "Dispatcher access. Use the credentials issued by Admin.":
    "Acceso de despachador. Use las credenciales emitidas por el administrador.",
  "Operations · Fleet Movement": "Operaciones · Movimiento de Flota",
  "MASCI · Dispatch Portal": "MASCI · Portal de Despacho",
  "Sign in with the account the admin issued you. First-time users will be prompted to set their own password after entering the temporary one.":
    "Inicie sesión con la cuenta que el administrador le emitió. A los usuarios por primera vez se les pedirá establecer su propia contraseña después de ingresar la temporal.",
  "Sign in with your MASCI work email. If this is your first time, the admin will give you a temporary password — you'll change it on first sign-in.":
    "Inicie sesión con su correo de trabajo MASCI. Si es su primera vez, el administrador le dará una contraseña temporal — la cambiará en el primer inicio de sesión.",
  "Forgot password? Click the link above and we'll email you a reset. Or call the office — admin can issue a fresh temp password.":
    "¿Olvidó su contraseña? Haga clic en el enlace de arriba y le enviaremos un restablecimiento. O llame a la oficina — el administrador puede emitir una nueva contraseña temporal.",

  // Cheat Sheet card + reference
  "MASCI Operations Platform · Field Card":
    "Plataforma de Operaciones MASCI · Tarjeta de Campo",
  "Print and post inside every site trailer.":
    "Imprima y publique dentro de cada tráiler de obra.",
  "Memorize these.": "Memorice esto.",
  "Tips for Everyone": "Consejos para Todos",
  "Field Tips & Emergency Steps": "Consejos de Campo y Pasos de Emergencia",
  "Safety & Stop-the-Line": "Seguridad y Detener la Línea",
  "Office": "Oficina",
  "Pre-Op FAILs": "FALLOS Pre-Op",
  "Open the": "Abra el",
  "Open your camera, point it at the QR code, tap the link. MASCI Operations Platform opens in your browser. No login. No app. Add it to your home screen and you're set.":
    "Abra la cámara, apúntela al código QR, toque el enlace. La Plataforma de Operaciones MASCI se abre en su navegador. Sin inicio de sesión. Sin app. Agréguela a su pantalla de inicio y listo.",
  "Powered by ForgedOps™": "Impulsado por ForgedOps™",
  "Use the ES button to switch any form to Spanish — it submits in English automatically.":
    "Use el botón ES para cambiar cualquier formulario a español — se envía en inglés automáticamente.",
  "Short bilingual lessons for every role — open mascidocs.com/training.":
    "Lecciones bilingües cortas para cada rol — abra mascidocs.com/training.",
  "Tap the Need Help tile on the Hub — office phone, address, and after-hours contact.":
    "Toque la tarjeta ¿Necesita Ayuda? en el centro — teléfono de la oficina, dirección y contacto fuera de horario.",
  "Every submission gets a unique tracking number printed on the PDF (e.g. DR-2026-00042). Read it back to the office when calling about a job.":
    "Cada envío recibe un número de seguimiento único impreso en el PDF (ej. DR-2026-00042). Léalo a la oficina cuando llame sobre un trabajo.",
  "auto-email every active mechanic and the parts office in 60 seconds. No need to call separately.":
    "se envía por correo automáticamente a cada mecánico activo y a la oficina de partes en 60 segundos. No es necesario llamar por separado.",
  "— it will prompt you to confirm the office was notified and the Incident Report was filed before the truck moves.":
    "— le pedirá confirmar que se notificó a la oficina y que se presentó el Reporte de Incidente antes de que el camión se mueva.",
  "Doc ID:": "ID Doc:",
  "Field Crew is public — share with insurance, auditors, or new-hire onboarding. Internal Shop, PM, and Admin packets are sign-in required.":
    "Cuadrilla de Campo es público — compártalo con seguros, auditores u orientación de nuevos empleados. Los paquetes internos de Taller, PM y Admin requieren inicio de sesión.",
  // ── End iter241b entries ──

  // iter241c — 10 exact-wording corrections (operator-sourced strings
  // that had slightly different wording than the iter241b batch
  // translated; the source-of-truth strings now have matching ES
  // entries verbatim).
  "Daily Reports · Equipment Pre-Op walk-arounds. GPS auto-fills location, weather auto-loads, photos in two taps.":
    "Reportes Diarios · Inspecciones Pre-Op de equipos. GPS llena ubicación, clima se carga automáticamente, fotos en dos toques.",
  "Enter your work email. If we have you on file with an active account, we'll email you a one-time link to set a new password. Link expires in 30 minutes.":
    "Ingrese su correo de trabajo. Si lo tenemos en nuestros registros con una cuenta activa, le enviaremos un enlace de un solo uso para establecer una nueva contraseña. El enlace expira en 30 minutos.",
  "Every submission gets a unique tracking number printed on the PDF (e.g. DR-2026-00042). Read it back when the office calls — they find it instantly.":
    "Cada envío recibe un número de seguimiento único impreso en el PDF (ej. DR-2026-00042). Léalo cuando la oficina llame — lo encuentran al instante.",
  "Field Crew is public — share with insurance, auditors, or new-hire onboarding. Internal Shop, PM, and Admin packets are managed in the Admin Console.":
    "Cuadrilla de Campo es público — compártalo con seguros, auditores u orientación de nuevos empleados. Los paquetes internos de Taller, PM y Admin se gestionan en la Consola de Administración.",
  "Forgot password? Click the link above and we'll email you a reset. Or call the office — admin can issue a fresh temp password from the console.":
    "¿Olvidó su contraseña? Haga clic en el enlace de arriba y le enviaremos un restablecimiento. O llame a la oficina — el administrador puede emitir una nueva contraseña temporal desde la consola.",
  "Multi-portal sign-in for accounts with access to more than one portal. Single-portal employees, use your portal's direct sign-in page (linked below).":
    "Inicio de sesión multi-portal para cuentas con acceso a más de un portal. Empleados de un solo portal, use la página de inicio de sesión directo de su portal (enlace abajo).",
  "Open your camera, point it at the QR code, tap the link. MASCI Operations Platform opens in your browser. No login for field forms. No app to install. Add it to your home screen and you're set.":
    "Abra la cámara, apúntela al código QR, toque el enlace. La Plataforma de Operaciones MASCI se abre en su navegador. Sin inicio de sesión para formularios de campo. Sin app que instalar. Agréguela a su pantalla de inicio y listo.",
  "Sign in with the account the admin issued you. First-time users will be prompted to set their own password after entering the temporary one from their welcome email.":
    "Inicie sesión con la cuenta que el administrador le emitió. A los usuarios por primera vez se les pedirá establecer su propia contraseña después de ingresar la temporal de su correo de bienvenida.",
  "Sign in with your MASCI work email. If this is your first time, the admin will give you a temporary password — you'll choose your own on first login.":
    "Inicie sesión con su correo de trabajo MASCI. Si es su primera vez, el administrador le dará una contraseña temporal — elegirá la suya en el primer inicio de sesión.",
  "— it will prompt you to confirm the office was notified and the Incident Report was filed before you can submit.":
    "— le pedirá confirmar que se notificó a la oficina y que se presentó el Reporte de Incidente antes de poder enviar.",
  // ── End iter241c entries ──

  // iter245 — Request PO workflow refinement (2026-05-19).
  // Field Leadership submits PO requests using searchable dropdowns for
  // Active Jobs and the shared Vendor / Subcontractor master list.
  // (Keys already present elsewhere in this dict — Job, Description,
  // Urgency, Category, Notes, Estimated amount, Needed by, Your name —
  // are NOT duplicated here; they resolve via their existing entries.)
  "Request PO": "Solicitar OC",
  "PO requested": "OC solicitada",
  "Could not request PO": "No se pudo solicitar la OC",
  "Please select a job, choose a vendor, and add a description.":
    "Seleccione una obra, elija un proveedor y agregue una descripción.",
  "Select Job": "Seleccionar obra",
  "Active jobs only · maintained by PM / Admin.":
    "Solo obras activas · administradas por PM / Admin.",
  "I don't see this job — contact PM to add it.":
    "No veo esta obra — contacte al PM para agregarla.",
  "Vendor / Subcontractor": "Proveedor / Subcontratista",
  "Search vendors or add a new one…":
    "Buscar proveedores o agregar uno nuevo…",
  "Type to search the shared vendor list. New names are added to the master list for everyone.":
    "Escriba para buscar en la lista compartida de proveedores. Los nombres nuevos se agregan a la lista maestra para todos.",
  "Supervisor signature": "Firma del supervisor",
  // ── End iter245 entries ──

  // iter247 P1-B · AccessDenied page localization (operator-approved audit follow-up)
  "that section": "esa sección",
  "403 · Access Restricted": "403 · Acceso Restringido",
  "You don't have access to": "No tiene acceso a",
  "This section belongs to a different portal scope. Your current session can't open it, but you can jump back to a portal you do have access to below. If this is unexpected, contact your administrator.":
    "Esta sección pertenece a otro portal. Su sesión actual no puede abrirla, pero puede regresar a un portal al que sí tiene acceso a continuación. Si esto no es lo esperado, contacte a su administrador.",
  "You need to sign in to view this section. Pick the right portal sign-in below — or head back to the public home.":
    "Debe iniciar sesión para ver esta sección. Elija el inicio de sesión del portal correcto a continuación — o regrese a la página pública.",
  "Back to": "Regresar a",
  "Sign in": "Iniciar sesión",
  "Public Home": "Página Pública",
  "Other portals you can access": "Otros portales a los que tiene acceso",
  "Path:": "Ruta:",
  // ── End iter247 P1-B entries ──

  // iter246 · F1 — /admin/login ES polish (final localization continuity)
  "Admin Sign In": "Inicio de Sesión de Administrador",
  "Forgot password? Call the office.":
    "¿Olvidó su contraseña? Llame a la oficina.",
  "Office sign-in for managers and supervisors. Field crews don't need to sign in to fill out forms — they can start a new one straight from the":
    "Inicio de sesión de oficina para gerentes y supervisores. Las cuadrillas de campo no necesitan iniciar sesión para llenar formularios — pueden comenzar uno nuevo directamente desde el",
  "Access multiple portals?": "¿Tiene acceso a varios portales?",
  "Use the master sign-in": "Use el inicio de sesión maestro",
  "to land on any portal in one step.":
    "para acceder a cualquier portal en un solo paso.",
  // ── End iter246 F1 entries ──

  // Crew Cheat Sheet
  "Cheat Sheet": "Hoja de Referencia",
  "Crew Cheat Sheet": "Hoja de Referencia de Cuadrilla",
  "Crew Cheat Sheet · Field Safety Reporting Portal":
    "Hoja de Referencia · Portal de Reportes de Seguridad de Campo",
  Office: "Oficina",
  Print: "Imprimir",
  "Scan to start": "Escanee para comenzar",
  "One front door for every safety form.":
    "Una puerta de entrada para cada formulario de seguridad.",
  "Open your camera, point it at the QR code, and tap the link. The MASCI Operations Platform opens in your browser. No login. No app to install. Add it to your home screen and you're set.":
    "Abra la cámara, apúntela al código QR y toque el enlace. La Plataforma de Operaciones MASCI se abre en su navegador. Sin inicio de sesión. Sin aplicación que instalar. Agréguela a su pantalla de inicio y listo.",
  "Step 01": "Paso 01",
  "Step 02": "Paso 02",
  "Step 03": "Paso 03",
  "Step 04": "Paso 04",
  "Pick the form": "Elija el formulario",
  "Daily Report, Site Inspection, Safety Meeting, JHP, or Incident — tap the tile.":
    "Reporte Diario, Inspección, Reunión de Seguridad, JHP o Incidente — toque la tarjeta.",
  "Fill it on site": "Llénelo en el sitio",
  "GPS auto-fills location, weather auto-loads, your job is in the picker. Tap to add photos.":
    "El GPS rellena la ubicación, el clima se carga solo, su obra está en el selector. Toque para agregar fotos.",
  "Sign + Submit": "Firme + Envíe",
  "Sign with your finger. Hit Submit. Translates Spanish to English automatically before saving.":
    "Firme con el dedo. Toque Enviar. Traduce del español al inglés automáticamente antes de guardar.",
  Done: "Listo",
  "Office gets the report instantly. You'll see a Thank You screen with the option to file another.":
    "La oficina recibe el reporte al instante. Verá una pantalla de Gracias con la opción de archivar otro.",
  "Tips for Foremen": "Consejos para Capataces",
  "Tips for Supervisors": "Consejos para Supervisores",
  "Use the ES button to switch the form to Spanish — it submits in English automatically.":
    "Use el botón ES para cambiar el formulario a español — se envía en inglés automáticamente.",
  "Daily Reports require": "Los Reportes Diarios requieren",
  "at least 6 photos": "al menos 6 fotos",
  ". Take them as you walk the site.":
    ". Tómelas mientras camina por el sitio.",
  "Add the Hub to your home screen so it opens with one tap.":
    "Agregue el Hub a su pantalla de inicio para abrirlo con un toque.",
  "If GPS doesn't grab, type the address in the Location field — same result.":
    "Si el GPS no funciona, escriba la dirección en Ubicación — mismo resultado.",
  "Stop-the-line · Accidents & Injuries":
    "Pare la Línea · Accidentes y Lesiones",
  "Make the scene safe": "Asegure la escena",
  "and get any injured worker medical attention.":
    "y consiga atención médica a cualquier trabajador lesionado.",
  "Call Safety immediately": "Llame a Seguridad inmediatamente",
  Open: "Abra",
  "Incident Report": "Reporte de Incidente",
  "form on the Hub and fill it out as soon as the scene is stable.":
    "en el Hub y complételo tan pronto como la escena sea estable.",
  "Then complete your": "Luego complete su",
  "Daily Report": "Reporte Diario",
  "— it will prompt you to confirm Safety was notified and the Incident Report was filed before you can submit.":
    "— le pedirá confirmar que se notificó a Seguridad y que se presentó el Reporte de Incidente antes de poder enviar.",
  "No Shortcuts · No Exceptions": "Sin Atajos · Sin Excepciones",

  // Common form chrome
  "New Report": "Nuevo Reporte",
  "Submit": "Enviar",
  "Save": "Guardar",
  "Saving...": "Guardando...",
  "Cancel": "Cancelar",
  "Required": "Requerido",
  "Optional": "Opcional",
  "Yes": "Sí",
  "No": "No",
  "N/A": "N/A",
  "Unsure": "No estoy seguro",
  "Remove": "Quitar",
  "Add": "Agregar",
  "Add Attendee": "Agregar Asistente",
  "Add Witness": "Agregar Testigo",
  "Add Crew Member": "Agregar Miembro de Cuadrilla",
  "Add Task Step": "Agregar Paso de Tarea",
  "Print / PDF": "Imprimir / PDF",

  // MASCI Job picker
  "MASCI Job": "Trabajo MASCI",
  "Pick a current job to auto-fill name + number — or choose Custom Job to type your own.":
    "Elija un trabajo actual para autocompletar nombre + número — o elija Trabajo Personalizado para escribir el suyo.",
  "Pick a MASCI job — or choose Custom": "Elija un trabajo MASCI — o elija Personalizado",
  "Search by job #, name, route, or city...":
    "Buscar por # de trabajo, nombre, ruta o ciudad...",
  "No job matches that search.": "Ningún trabajo coincide con esa búsqueda.",
  "Custom": "Personalizado",
  "Custom Job": "Trabajo Personalizado",
  "Type the project name and number manually":
    "Escriba el nombre y número del proyecto manualmente",

  // Project / location fields
  "Project Name *": "Nombre del Proyecto *",
  "Project Number": "Número de Proyecto",
  "Location *": "Ubicación *",
  "Location": "Ubicación",
  "Use GPS": "Usar GPS",
  "Date *": "Fecha *",
  "Time *": "Hora *",
  "Date": "Fecha",
  "Time": "Hora",

  // ============================================================
  // Site Inspection
  // ============================================================
  "Job Site Safety Inspection": "Inspección de Seguridad del Sitio",
  "Project / Inspection Information": "Información del Proyecto / Inspección",
  "Operation *": "Turno *",
  "Day": "Día",
  "Night": "Noche",
  "Inspector Name *": "Nombre del Inspector *",
  "Foreman / Supervisor *": "Capataz / Supervisor *",
  "Crew / MASCI Personnel Onsite": "Cuadrilla / Personal MASCI en Sitio",
  "List crew members or crew lead": "Liste los miembros de la cuadrilla o líder",
  "Subcontractors Onsite": "Subcontratistas en Sitio",
  "Weather Conditions": "Condiciones Climáticas",
  "Work Activity *": "Actividad de Trabajo *",
  "What is the crew working on?": "¿En qué está trabajando la cuadrilla?",
  "PPE Compliance": "Cumplimiento de EPP",
  "Site Hazards": "Peligros del Sitio",
  "Corrective Actions": "Acciones Correctivas",
  "Photos": "Fotos",
  "Hazards Observed": "Peligros Observados",
  "Stop Work Issued": "Suspensión del Trabajo Emitida",
  "Corrected On Site": "Corregido en el Sitio",
  "Responsible Party": "Parte Responsable",
  "Corrective Action Notes": "Notas de Acción Correctiva",
  "Inspector Signature": "Firma del Inspector",
  "Foreman Signature": "Firma del Capataz",
  "Live Grade": "Calificación en Vivo",
  "Submit Inspection": "Enviar Inspección",
  "Saving Inspection...": "Guardando Inspección...",

  // ============================================================
  // Safety Meeting
  // ============================================================
  "Site Safety Meeting": "Reunión de Seguridad del Sitio",
  "Meeting Information": "Información de la Reunión",
  "Conducted By *": "Conducida Por *",
  "Conducted By": "Conducida Por",
  "— enter in Section 01 —": "— ingresar en Sección 01 —",
  "Crew Size": "Tamaño de Cuadrilla",
  "Total on crew today": "Total de la cuadrilla hoy",
  "Shift": "Turno",
  "Select shift": "Seleccionar turno",
  "High-risk activity today": "Actividad de alto riesgo hoy",
  /* iter269 · Sprint 2 · K4 · K6 · K7 · philosophy linkage strings */
  "After you pick a topic, read the WHAT HAPPENS paragraph to the crew first — that's the real-world pattern. Then walk through the bullets. That's the operational drill.":
    "Después de elegir un tema, lea primero el párrafo PATRÓN REAL a la cuadrilla — ese es el patrón del mundo real. Luego repase los puntos. Esa es la disciplina operacional.",
  "Domain": "Dominio",
  "Context for the crew · the bullets below are the action drill":
    "Contexto para la cuadrilla · los puntos de abajo son la disciplina de acción",

  "Auto-fills when you pick a topic below": "Se autocompleta al elegir un tema abajo",

  /* iter268 · Sprint 1 · K1·K2·K3·K9 · ViewMeeting + NewMeeting bilingual alignment */
  "Topic": "Tema",
  "Pick a topic — Category & all fields below auto-fill":
    "Elija un tema — Categoría y los campos de abajo se autocompletan",
  "Add every person who attended":
    "Añada a todas las personas que asistieron",

  /* Weather chip values (used in ViewMeeting summary AND PDF) */
  "Clear": "Despejado",
  "Hot": "Calor",
  "Cold": "Frío",
  "Rain": "Lluvia",
  "Wind": "Viento",
  "Storm Risk": "Riesgo de Tormenta",

  /* ViewMeeting header + chrome */
  "Site Safety Meeting Record": "Registro de Reunión de Seguridad del Sitio",
  "Doc ID": "ID de Doc.",
  "Report ID": "ID de Reporte",
  "Meetings": "Reuniones",
  "Print / PDF": "Imprimir / PDF",
  "Email": "Correo",
  "Loading…": "Cargando…",

  /* ViewMeeting field labels not already covered */
  "Topic / Subject": "Tema / Asunto",
  "Discussion Notes": "Notas de Discusión",
  "Open in Maps": "Abrir en Mapas",
  "Yes (unnamed)": "Sí (sin nombre)",
  "No attendees listed.": "No hay asistentes registrados.",
  "Attendee": "Asistente",
  "No signature": "Sin firma",
  "Safety Meeting": "Reunión de Seguridad",
  "Generated": "Generado",

  /* ViewMeeting toasts / confirm dialogs */
  "Meeting not found": "Reunión no encontrada",
  "Delete this meeting? This cannot be undone.":
    "¿Eliminar esta reunión? Esto no se puede deshacer.",
  "Delete failed": "Error al eliminar",

  /* NewMeeting toasts (K3) */
  "Job loaded: #{n}": "Trabajo cargado: #{n}",
  "Location captured from GPS": "Ubicación capturada por GPS",
  "Got GPS coordinates, but couldn't look up address":
    "Se obtuvieron coordenadas GPS, pero no se pudo buscar la dirección",
  "Could not get GPS location": "No se pudo obtener la ubicación GPS",
  "{field} is required": "{field} es obligatorio",
  "Conductor signature is required": "La firma del conductor es obligatoria",
  "Add at least one attendee": "Añada al menos un asistente",
  "Translating to English…": "Traduciendo al inglés…",
  "Meeting saved": "Reunión guardada",
  "Could not save meeting": "No se pudo guardar la reunión",
  "Weather": "Clima",
  "Subcontractor crew present": "Cuadrilla subcontratista presente",
  "Subcontractor name (optional)": "Nombre del subcontratista (opcional)",
  "The person who ran the meeting signs to confirm the record is accurate.":
    "La persona que dirigió la reunión firma para confirmar que el registro es preciso.",
  "Foreman / Supervisor": "Capataz / Supervisor",
  "Topic Category *": "Categoría del Tema *",
  "Topic & Discussion": "Tema y Discusión",
  "Topic Library — Pick a topic to prefill":
    "Biblioteca de Temas — Elija un tema para prellenar",
  "Search topics (e.g. trench, silica, heat)...":
    "Buscar temas (ej. zanja, sílice, calor)...",
  "No topic matches that search.": "Ningún tema coincide con esa búsqueda.",
  "Custom Topic": "Tema Personalizado",
  "Custom Topic — write your own": "Tema Personalizado — escriba el suyo",
  "Clear all fields and write your own": "Borrar todos los campos y escribir el suyo",
  "Search or pick a topic...": "Busque o elija un tema...",
  "Topic / Subject *": "Tema / Asunto *",
  "Hazards Reviewed": "Peligros Revisados",
  "Discussion Notes / Minutes": "Notas de Discusión / Minutas",
  "References Cited": "Referencias Citadas",
  "Action Items / Follow-Up": "Acciones / Seguimiento",
  "What specific hazards were discussed?": "¿Qué peligros específicos se discutieron?",
  "Key points, questions, lessons learned...":
    "Puntos clave, preguntas, lecciones aprendidas...",
  "OSHA standards, SDS reviewed, MASCI procedures...":
    "Estándares OSHA, SDS revisados, procedimientos MASCI...",
  "What needs to happen next? Who owns it?":
    "¿Qué debe pasar después? ¿Quién es responsable?",
  "Attendees": "Asistentes",
  "Add every person who attended. Each attendee signs to confirm they were present and understood the topic.":
    "Agregue a cada persona que asistió. Cada asistente firma para confirmar que estuvo presente y entendió el tema.",
  "Attendee": "Asistente",
  "Typed name": "Nombre escrito",
  "Signature": "Firma",
  "Conductor Signature": "Firma del Conductor",
  "The person who ran the meeting signs to confirm the record is accurate.":
    "La persona que dirigió la reunión firma para confirmar que el registro es exacto.",
  "Conducted By (Typed) *": "Conducida Por (Escrito) *",
  "Submit Meeting": "Enviar Reunión",
  "Saving Meeting...": "Guardando Reunión...",

  // ============================================================
  // JHP
  // ============================================================
  "Job / Task Information": "Información del Trabajo / Tarea",
  "Crew Lead / Foreman *": "Líder de Cuadrilla / Capataz *",
  "Job / Task Title *": "Título del Trabajo / Tarea *",
  "Job Description": "Descripción del Trabajo",
  "Crew Members": "Miembros de la Cuadrilla",
  "List all crew members performing the task":
    "Liste todos los miembros que realizarán la tarea",
  "Required PPE": "EPP Requerido",
  "Check every PPE item required for this task.":
    "Marque cada artículo de EPP requerido para esta tarea.",
  "Required Permits": "Permisos Requeridos",
  "Check any permits required before this work begins.":
    "Marque los permisos requeridos antes de comenzar este trabajo.",
  "Tools & Equipment": "Herramientas y Equipo",
  "List tools, equipment, and machinery needed":
    "Liste herramientas, equipo y maquinaria necesaria",
  "Hazard Plan": "Plan de Peligros",
  "Walk through each step of the task. For every step, list the potential hazards and the controls / safe practices to mitigate them.":
    "Recorra cada paso de la tarea. Para cada paso, liste los peligros potenciales y los controles / prácticas seguras para mitigarlos.",
  "Step": "Paso",
  "Step Description": "Descripción del Paso",
  "What is the crew doing in this step?":
    "¿Qué está haciendo la cuadrilla en este paso?",
  "Potential Hazards": "Peligros Potenciales",
  "What could go wrong? What hazards are present?":
    "¿Qué podría salir mal? ¿Qué peligros hay?",
  "Controls / Safe Practices": "Controles / Prácticas Seguras",
  "What are we doing to eliminate or control the hazard?":
    "¿Qué estamos haciendo para eliminar o controlar el peligro?",
  "Emergency & Stop Work": "Emergencia y Suspensión del Trabajo",
  "Stop Work Authority Acknowledged *": "Autoridad para Suspender el Trabajo Reconocida *",
  "Every crew member has the authority and responsibility to stop work for any safety concern, no questions asked.":
    "Cada miembro de la cuadrilla tiene la autoridad y responsabilidad de suspender el trabajo por cualquier preocupación de seguridad, sin preguntas.",
  "Nearest Hospital / ER": "Hospital / Sala de Emergencias más Cercano",
  "Emergency Contact #": "# de Contacto de Emergencia",
  "Crew Sign-Off": "Firma de la Cuadrilla",
  "Each crew member signs to confirm they understand the hazards and the safe work plan.":
    "Cada miembro firma para confirmar que entiende los peligros y el plan de trabajo seguro.",
  "Crew Member": "Miembro de Cuadrilla",
  "Foreman Approval": "Aprobación del Capataz",
  "Foreman / Crew Lead (Typed)": "Capataz / Líder de Cuadrilla (Escrito)",
  "Foreman Approval Signature *": "Firma de Aprobación del Capataz *",
  "Submit JHP": "Enviar JHP",
  "Saving JHP...": "Guardando JHP...",

  // ============================================================
  // Incident
  // ============================================================
  "Accident / Incident Report": "Reporte de Accidente / Incidente",
  "First, secure the scene and the injured.":
    "Primero, asegure la escena y a los heridos.",
  "Call 911 if anyone is seriously hurt. Document this report once the immediate response is complete.":
    "Llame al 911 si alguien está gravemente herido. Documente este reporte una vez completada la respuesta inmediata.",
  "Report Information": "Información del Reporte",
  "Specific location on site (station, lane, structure...)":
    "Ubicación específica en el sitio (estación, carril, estructura...)",
  "Incident Date *": "Fecha del Incidente *",
  "Incident Time *": "Hora del Incidente *",
  "Date Reported": "Fecha Reportada",
  "Reported By *": "Reportado Por *",
  "Your name": "Su nombre",
  "Supervisor / Foreman On-Site": "Supervisor / Capataz en el Sitio",
  "Classification & Severity": "Clasificación y Severidad",
  "Incident Type *": "Tipo de Incidente *",
  "Severity Tier *": "Nivel de Severidad *",
  "Pick the actual outcome. For a near miss, choose Near Miss even if the potential was severe — note the potential in the description.":
    "Elija el resultado real. Para un cuasi-accidente, elija Cuasi-Accidente aunque el potencial haya sido severo — anote el potencial en la descripción.",
  "Selected": "Seleccionado",
  "OSHA Recordable?": "¿Registrable por OSHA?",
  "Was Work Stopped?": "¿Se Suspendió el Trabajo?",
  // Severity labels & descriptions
  "Near Miss": "Cuasi-Accidente",
  "First Aid": "Primeros Auxilios",
  "Medical Treatment": "Tratamiento Médico",
  "Restricted / Light Duty": "Trabajo Restringido / Liviano",
  "Lost Time (DART)": "Tiempo Perdido (DART)",
  "Fatality / Catastrophic": "Fatalidad / Catastrófico",
  "No injury, no damage — but could have happened.":
    "Sin lesión, sin daño — pero pudo haber ocurrido.",
  "Minor — treated on-site, no further care.":
    "Menor — tratado en el sitio, sin más atención.",
  "Required clinic / urgent-care treatment beyond first aid.":
    "Requirió tratamiento de clínica / urgencias más allá de primeros auxilios.",
  "Worker on restricted duty after the event.":
    "Trabajador con trabajo restringido después del evento.",
  "Days away or restricted — OSHA recordable.":
    "Días ausentes o restringido — registrable por OSHA.",
  "Fatality, hospitalization, amputation, loss of eye.":
    "Fatalidad, hospitalización, amputación, pérdida de ojo.",
  // Incident type options
  "Injury / Illness": "Lesión / Enfermedad",
  "Property / Equipment Damage": "Daño a Propiedad / Equipo",
  "Vehicle / Mobile Equipment": "Vehículo / Equipo Móvil",
  "Environmental Release / Spill": "Derrame / Liberación Ambiental",
  "Utility Strike": "Golpe a Servicio Subterráneo",
  "Public / Third Party": "Público / Tercero",
  "Security": "Seguridad (Robo)",
  "Other": "Otro",

  "Person Involved": "Persona Involucrada",
  "Name": "Nombre",
  "Role / Trade": "Rol / Oficio",
  "Laborer, Operator, Foreman...": "Obrero, Operador, Capataz...",
  "Employer": "Empleador",
  "MASCI / subcontractor name": "MASCI / nombre del subcontratista",
  "Years Experience": "Años de Experiencia",
  "Body Part Affected": "Parte del Cuerpo Afectada",
  "Select body part...": "Elija parte del cuerpo...",
  "Nature of Injury / Illness": "Naturaleza de la Lesión / Enfermedad",
  "Select...": "Elija...",
  "Treatment Provided": "Tratamiento Proporcionado",
  "First aid given, EMS called, transported by...":
    "Primeros auxilios dados, EMS llamado, transportado por...",
  "Medical Facility": "Centro Médico",
  "Clinic / hospital, if applicable": "Clínica / hospital, si aplica",
  "Sent Home / Off Site?": "¿Enviado a Casa / Fuera del Sitio?",

  "What Happened": "Qué Sucedió",
  "Description of Incident *": "Descripción del Incidente *",
  "Describe in detail what was happening, what changed, what occurred. Include sequence of events.":
    "Describa en detalle qué estaba pasando, qué cambió, qué ocurrió. Incluya la secuencia de eventos.",
  "Immediate Cause": "Causa Inmediata",
  "What was the unsafe act or condition that triggered the event?":
    "¿Cuál fue el acto o condición insegura que provocó el evento?",
  "Contributing Factors": "Factores Contribuyentes",
  "Weather, fatigue, training, equipment condition, schedule pressure...":
    "Clima, fatiga, capacitación, condición del equipo, presión de horario...",

  "Root Cause Analysis": "Análisis de Causa Raíz",
  "Check every category that contributed. Pick all that apply.":
    "Marque cada categoría que contribuyó. Elija todas las que apliquen.",
  "PPE not used / inadequate": "EPP no usado / inadecuado",
  "Inadequate training / knowledge": "Capacitación / conocimiento inadecuado",
  "Procedure not followed": "Procedimiento no seguido",
  "Inadequate supervision": "Supervisión inadecuada",
  "Equipment / tool failure": "Falla de equipo / herramienta",
  "Design / engineering": "Diseño / ingeniería",
  "Communication breakdown": "Falla de comunicación",
  "Fatigue / human factors": "Fatiga / factores humanos",
  "Housekeeping / site conditions": "Orden / condiciones del sitio",
  "Weather / environment": "Clima / ambiente",
  "Notes / Additional Detail": "Notas / Detalles Adicionales",

  "Witnesses": "Testigos",
  "Add anyone who saw the event. Capture short statements while it's fresh.":
    "Agregue a cualquiera que vio el evento. Capture declaraciones cortas mientras está fresco.",
  "Witness": "Testigo",
  "What they saw, in their words.": "Lo que vieron, en sus palabras.",

  "Corrective Actions & Follow-Up": "Acciones Correctivas y Seguimiento",
  "Immediate Actions Taken (on-site, today)":
    "Acciones Inmediatas Tomadas (en sitio, hoy)",
  "What was done immediately to make the area safe?":
    "¿Qué se hizo inmediatamente para hacer segura el área?",
  "Long-Term Corrective Actions": "Acciones Correctivas a Largo Plazo",
  "Training, procedure changes, engineering controls...":
    "Capacitación, cambios de procedimiento, controles de ingeniería...",
  "Who owns the follow-up?": "¿Quién es responsable del seguimiento?",
  "Target Completion Date": "Fecha Meta de Finalización",

  "Notifications Made": "Notificaciones Realizadas",
  "Confirm who was notified about this incident.":
    "Confirme a quién se notificó sobre este incidente.",
  "Safety Manager": "Gerente de Seguridad",
  "Project Manager": "Gerente de Proyecto",
  "General Contractor": "Contratista General",
  "Owner / Agency": "Dueño / Agencia",
  "OSHA (if catastrophic)": "OSHA (si es catastrófico)",
  "Other (free text)": "Otro (texto libre)",
  "Insurance, EAP, family...": "Seguro, EAP, familia...",

  "Photos / Evidence": "Fotos / Evidencia",
  "Signatures": "Firmas",
  "Reporter Signature *": "Firma del Reportero *",
  "Supervisor Signature": "Firma del Supervisor",
  "Reporter": "Reportero",
  "Supervisor": "Supervisor",
  "Submit Incident Report": "Enviar Reporte de Incidente",
  "Saving Report...": "Guardando Reporte...",

  // Lang toggle copy
  "Language": "Idioma",
  "English": "Inglés",
  "Español": "Español",
  "Forms can be filled in Spanish — submitted record stays in English.":
    "Los formularios se pueden llenar en español — el registro enviado se mantiene en inglés.",
  "heavy civil / highway topics with prefilled hazards, key points, references, and action items. Type to search — or choose":
    "temas de obra civil pesada / carretera con peligros, puntos clave, referencias y acciones prellenadas. Escriba para buscar — o elija",
  "to write your own.": "para escribir el suyo.",
  "Custom topic — all topic fields cleared.":
    "Tema personalizado — todos los campos limpiados.",

  // ============================================================
  // Job Hazard Plans (file-sharing hub)
  // ============================================================
  "Job Hazard Plans": "Planes de Peligros del Trabajo",
  "Read your job's Hazard Plan PDF before crew breaks ground. One plan per active MASCI job — uploaded by the office.":
    "Lea el PDF del Plan de Peligros de su trabajo antes de que la cuadrilla comience. Un plan por cada trabajo MASCI activo — subido por la oficina.",
  "Pick your job to view its Hazard Plan":
    "Elija su trabajo para ver su Plan de Peligros",
  "Each MASCI job has its own Job Hazard Plan PDF. Open your job and read it before crew breaks ground. If your job has no plan yet, get with your PM.":
    "Cada trabajo MASCI tiene su propio PDF del Plan de Peligros. Abra su trabajo y léalo antes de que la cuadrilla comience. Si su trabajo aún no tiene plan, consulte con su Gerente de Proyecto.",
  "Search by job number, name, or location…":
    "Buscar por número de trabajo, nombre o ubicación…",
  "Uploaded": "Subido",
  "View Plan": "Ver Plan",
  "Not uploaded yet": "Aún no subido",
  "No job matches your search.": "Ningún trabajo coincide con su búsqueda.",
  "Download for offline use": "Descargar para uso sin conexión",
  "On your phone, hold": "En su teléfono, mantenga presionado",
  "Save to Files / Downloads": "Guardar en Archivos / Descargas",
  "to read it where there's no service.":
    "para leerlo donde no haya señal.",
  "Hub": "Inicio",

  // ============================================================
  // FOCP Release 2 · TR-0001 — JHP Acknowledgement Ledger strings
  // ============================================================
  "Acknowledge": "Confirmar Recibido",
  "Acknowledged": "Confirmado",
  "Acknowledge Job Hazard Plan": "Confirmar Plan de Peligros del Trabajo",
  "I have read this Hazard Plan and understand the site hazards, PPE requirements, and emergency response.":
    "He leído este Plan de Peligros y entiendo los peligros del sitio, los requisitos de EPP y la respuesta de emergencia.",
  "Work email": "Correo de trabajo",
  "Signature (type your full name)":
    "Firma (escriba su nombre completo)",
  "Full name": "Nombre completo",
  "Your acknowledgement is permanent and visible to your supervisor.":
    "Su confirmación es permanente y visible para su supervisor.",
  "Sign and Acknowledge": "Firmar y Confirmar",
  "You have acknowledged this Hazard Plan.":
    "Usted ha confirmado este Plan de Peligros.",
  "Enter your work email.": "Ingrese su correo de trabajo.",
  "Type your full name as your signature.":
    "Escriba su nombre completo como firma.",
  "Acknowledgement recorded.": "Confirmación registrada.",
  "Acknowledgement failed. Try again.":
    "La confirmación falló. Intente de nuevo.",
  "No employee on file matches that email. Get with your PM.":
    "Ningún empleado en archivo coincide con ese correo. Consulte con su Gerente de Proyecto.",
  "That email format isn't valid.":
    "El formato del correo no es válido.",
  "Signing as": "Firmando como",
  "plans acknowledged": "planes confirmados",
  "Not me — clear": "No soy yo — borrar",
  "Acknowledge any plan below to begin — your work email is your signature key.":
    "Confirme cualquier plan abajo para comenzar — su correo de trabajo es su llave de firma.",

  // ============================================================
  // Trench Box Tabulated Data
  // ============================================================
  "Trench Box Data": "Datos de Cajas de Zanja",
  "MASCI trench-shield fleet. Size, weight, OSHA max-depth by soil type, and manufacturer tabulated-data PDFs.":
    "Flota de escudos de zanja MASCI. Tamaño, peso, profundidad máxima OSHA por tipo de suelo, y PDFs de datos tabulados del fabricante.",
  "Trench Box Tabulated Data": "Datos Tabulados de Cajas de Zanja",

  // ============================================================
  // Trench Safety Operations System — Phase 3 UI
  // ============================================================
  "Trench Safety": "Seguridad de Zanjas",
  "Back to Trench Safety": "Volver a Seguridad de Zanjas",
  "Back to Safety": "Volver a Seguridad",
  "Cancel · Back to Trench Safety": "Cancelar · Volver a Seguridad de Zanjas",
  // Phase 10A-B · OMEGA Correction Directive · ES keys
  "Excavation Activity Today?": "¿Excavación hoy?",
  "If your crew opened or worked in any trench, hole, or excavation today, select YES and link the excavation record.":
    "Si su cuadrilla abrió o trabajó en cualquier zanja, hoyo o excavación hoy, seleccione SÍ y vincule el registro de excavación.",
  "Create New Excavation Record": "Crear Nuevo Registro de Excavación",
  "Link Existing Excavation Record": "Vincular Registro de Excavación Existente",
  "Linked Excavation Records": "Registros de Excavación Vinculados",
  "Suggestions for project": "Sugerencias para el proyecto",
  "(set project to load)": "(elige el proyecto para cargar)",
  "No existing excavation records for this project.": "No hay registros de excavación para este proyecto.",
  "Excavation Activity Today is YES — create or link at least one Excavation Record before submitting the Daily Report.":
    "Excavación Hoy es SÍ — cree o vincule al menos un Registro de Excavación antes de enviar el Reporte Diario.",
  "Action Required.": "Acción Requerida.",
  "MASCI Job · Project Information": "Trabajo MASCI · Información del Proyecto",
  "Same job source as Daily Reports.": "Mismo origen de trabajos que los Reportes Diarios.",
  "Field Leadership Roster": "Lista del Liderazgo de Campo",
  "Pull from the certified MASCI roster — no manual typing.": "Tomado de la lista oficial MASCI — sin tipeo manual.",
  "Foreman / Supervisor": "Capataz / Supervisor",
  "Leadman": "Jefe de Cuadrilla",
  "Superintendent": "Superintendente",
  "Prepared By": "Preparado Por",
  "Multi-select from the certified MASCI trench registry. Status / serial / open holds shown.":
    "Selección múltiple del registro oficial de zanjas MASCI. Estado / serie / retenciones visibles.",
  "Road Plates Used?": "¿Se usan Placas de Camino?",
  "Pull from the certified Road Plate registry.": "Tomado del registro oficial de Placas de Camino.",
  "Smart Trigger": "Disparador Inteligente",
  "OSHA Coaching": "Coaching OSHA",
  "Why This Matters:": "Por Qué Importa:",
  "OSHA Requirement:": "Requisito OSHA:",
  "Example:": "Ejemplo:",
  "Common Mistakes:": "Errores Comunes:",
  "When To Escalate:": "Cuándo Escalar:",
  "If Unsure:": "Si No Está Seguro:",
  "Trigger Reinspection": "Disparar Reinspección",
  "Reinspection triggered": "Reinspección disparada",
  "Reinspection Queue": "Cola de Reinspección",
  "All Records": "Todos los Registros",
  "no open reinspections": "sin reinspecciones abiertas",
  "Rain": "Lluvia",
  "Soil Change": "Cambio de Suelo",
  "Water Intrusion": "Intrusión de Agua",
  "Utility Strike": "Golpe de Servicio",
  "Protective System Change": "Cambio de Sistema Protector",
  "Excavation Expansion": "Expansión de Excavación",
  "Manual": "Manual",
  "Show Original": "Ver Original",
  "Show Translated": "Ver Traducido",
  "Add / Update English Translation": "Agregar / Actualizar Traducción al Inglés",
  "English translation (original Spanish is preserved)": "Traducción al inglés (el español original se conserva)",
  "Save Translation": "Guardar Traducción",
  "Translation saved": "Traducción guardada",
  "Original Language": "Idioma Original",
  "The platform does the work. You verify. Pick the MASCI Job and the field roster — project number, customer, PM, and assets auto-populate from the certified registries.":
    "La plataforma hace el trabajo. Tú verificas. Elige el Trabajo MASCI y la lista de campo — número de proyecto, cliente, PM y activos se completan automáticamente desde los registros certificados.",
  "Trench boxes, end panels, spreaders, hydraulic shores · tabulated data, inspections, holds, repairs, QR field view.":
    "Cajas de zanja, paneles, separadores, apuntalamientos hidráulicos · datos tabulados, inspecciones, retenciones, reparaciones, vista QR en campo.",
  "Operational hub for every MASCI trench safety asset — inspections, holds, repairs, tabulated data, and field QR access. Real counts from the platform — no static numbers.":
    "Centro operativo para cada activo de seguridad de zanjas de MASCI — inspecciones, retenciones, reparaciones, datos tabulados y acceso QR en campo. Conteos reales de la plataforma — sin números estáticos.",
  "Coaching:": "Recomendación:",
  "Match the box to the correct tabulated data before use. If the serial plate or tabulated data is missing, stop and contact Safety. A box on Inspection Hold is not available for use.":
  // Phase 10D · Daily Report Field-First (ES)
  "Live Submit Status": "Estado de Envío en Vivo",
  "Ready to Submit": "Listo para Enviar",
  "Every required item is in. Sign and submit.": "Todos los requisitos están listos. Firme y envíe.",
  "One or more required items need attention before this report can be submitted.": "Uno o más requisitos necesitan atención antes de enviar este reporte.",
  "You can submit — Safety/PM may follow up on the items below.": "Puede enviar — Seguridad/PM puede dar seguimiento a los puntos siguientes.",
  "Project not selected": "Proyecto no seleccionado",
  "Pick a MASCI Job (or Custom) so the report ties to a project number.": "Elige un Trabajo MASCI (o Personalizado) para que el reporte tenga un número de proyecto.",
  "Use the Job picker at the top of the form.": "Usa el selector de Trabajo en la parte superior del formulario.",
  "Prepared By is empty": "Preparado Por está vacío",
  "Every Daily Report must name the person submitting it.": "Cada Reporte Diario debe identificar a quién lo envía.",
  "Pick yourself from the roster or type your name.": "Elige tu nombre del listado o escríbelo.",
  "Location not entered": "Ubicación no ingresada",
  "Owners and the GC look at location for context.": "Los dueños y el GC necesitan la ubicación para entender el contexto.",
  "Add the work area / street / station.": "Agrega el área de trabajo / calle / estación.",
  "Excavation Activity is YES — link a record": "Excavación Hoy es SÍ — vincule un registro",
  "Daily Reports cannot be submitted without an Excavation Record when crews worked in a trench today.": "El Reporte Diario no se puede enviar sin un Registro de Excavación cuando las cuadrillas trabajaron en una zanja hoy.",
  "Create New or Link Existing in the Excavation Activity panel below.": "Crear Nuevo o Vincular Existente en el panel de Actividad de Excavación abajo.",
  "Weather Impact = YES — add a Weather row": "Impacto del Clima = SÍ — agregue una fila de Clima",
  "When weather impacted production, add a Delay/Extra Work row tagged Weather so the schedule team can see it.": "Cuando el clima afectó la producción, agregue una fila de Demora / Trabajo Extra etiquetada Clima.",
  "Open the Delays / Extra Work section and add a Weather row.": "Abra Demoras / Trabajo Extra y agregue una fila de Clima.",
  "Delays / Extra Work = YES — add a row": "Demoras / Trabajo Extra = SÍ — agregue una fila",
  "Pick the cause and a short note so the PM can act on it.": "Elija la causa y agregue una nota corta para que el PM pueda actuar.",
  "Open Delays / Extra Work and add one row.": "Abra Demoras / Trabajo Extra y agregue una fila.",
  "Safety must be notified": "Se debe notificar a Seguridad",
  "When an incident or injury is reported, Safety must be contacted before this Daily Report can be submitted.": "Cuando se reporta un incidente o lesión, Seguridad debe ser contactado antes de enviar este Reporte Diario.",
  "Mark Safety Notified = Yes after calling.": "Marca Seguridad Notificada = Sí después de llamar.",
  "Incident/Injury Report missing": "Reporte de Incidente/Lesión faltante",
  "An incident or injury also requires a separate Incident Report.": "Un incidente o lesión también requiere un Reporte de Incidente separado.",
  "File the Incident Report, then return here.": "Presenta el Reporte de Incidente y regresa aquí.",
  "No crew or subs on the report yet": "Aún no hay cuadrilla ni subcontratistas en el reporte",
  "Most Daily Reports list at least one crew or sub on site.": "La mayoría de Reportes Diarios incluyen al menos una cuadrilla o subcontratista en sitio.",
  "Add MASCI crew rows, or use the 'Use yesterday's crew' button if available.": "Agrega filas de cuadrilla MASCI, o usa el botón 'Usar la cuadrilla de ayer' si está disponible.",
  "Need {n} more photos": "Faltan {n} fotos",
  "Daily Reports need at least 6 photos showing the day's work.": "Los Reportes Diarios necesitan al menos 6 fotos del trabajo del día.",
  "Open the Photos section and capture the missing shots.": "Abre la sección de Fotos y captura las fotos faltantes.",
  "Signature missing": "Firma faltante",
  "Foremen sign off on the day's data so HR and PM trust the record.": "Los capataces firman los datos del día para que RH y PM confíen en el reporte.",
  "Sign at the bottom of the form.": "Firma al final del formulario.",
  "Previous Daily Report Found": "Reporte Diario Anterior Encontrado",
  "Last foreman": "Último capataz",
  "crew members": "miembros de cuadrilla",
  "equipment items": "elementos de equipo",
  "work-performed text available": "texto de trabajo realizado disponible",
  "Use Everything from Yesterday": "Usar Todo de Ayer",
  "Use Crew": "Usar Cuadrilla",
  "Use Equipment": "Usar Equipo",
  "Copy Last Activity": "Copiar Última Actividad",
  "Compliance view requires Safety/Admin sign-in.": "La vista de cumplimiento requiere acceso de Seguridad/Admin.",
  "more in the excavation record": "más en el registro de excavación",
  "action": "acción",
  "review": "revisión",
  "info": "info",

    "Verifique que la caja coincida con sus datos tabulados antes de usarla. Si falta la placa de serie o los datos tabulados, deténgase y contacte a Seguridad. Una caja en Retención de Inspección no está disponible para uso.",
  "Loading dashboard…": "Cargando panel…",
  "Unable to load dashboard.": "No se pudo cargar el panel.",
  "Active Assets": "Activos Activos",
  "Available": "Disponible",
  "Inspection Hold": "Retención de Inspección",
  "Open Repairs": "Reparaciones Abiertas",
  "By Type": "Por Tipo",
  "By Status": "Por Estado",
  "By Condition": "Por Condición",
  "Alerts": "Alertas",
  "Missing Serial Number": "Falta Número de Serie",
  "Missing Manufacturer": "Falta Fabricante",
  "Needs Review": "Necesita Revisión",
  "Inspections Due": "Inspecciones Pendientes",
  "Missing Tabulated Data": "Faltan Datos Tabulados",
  "Trench Equipment": "Equipo de Zanjas",
  "Filterable list of every MASCI trench safety asset.":
    "Lista filtrable de cada activo de seguridad de zanjas de MASCI.",
  "Tabulated Data": "Datos Tabulados",
  "OSHA tabulated data PDFs · per-box folders + general library.":
    "PDFs de datos tabulados OSHA · carpetas por caja + biblioteca general.",
  "Coming in later certified phases:": "Próximamente en fases certificadas posteriores:",
  "Inspections workflow · Repairs workflow · Certifications · Deployments history · Reports · QR PNG label generator · OCR for serial plates.":
    "Flujo de inspecciones · Flujo de reparaciones · Certificaciones · Historial de despliegues · Reportes · Generador de etiquetas QR PNG · OCR para placas de serie.",

  // ============================================================
  // Trench Safety · Phase 7.5A Command Center
  // ============================================================
  "New Asset": "Nuevo Activo",
  "Asset IDs (TB-01, EP-001…) are permanent once created. Safety and Admin can both create, edit, and retire.":
    "Los IDs de activos (TB-01, EP-001…) son permanentes una vez creados. Seguridad y Admin pueden crear, editar y retirar.",
  "Create Trench Safety Asset": "Crear Activo de Seguridad de Zanjas",
  "Asset ID is permanent. Choose deliberately — TB-01, EP-001, SP-001, etc.":
    "El ID del activo es permanente. Elija deliberadamente — TB-01, EP-001, SP-001, etc.",
  "Asset Type": "Tipo de Activo",
  "Manufacturer": "Fabricante",
  "Model": "Modelo",
  "Serial Number": "Número de Serie",
  "Size": "Tamaño",
  "Color": "Color",
  "Weight (lb)": "Peso (lb)",
  "Rated Depth (ft)": "Profundidad Nominal (ft)",
  "Rated Soil Type": "Tipo de Suelo Nominal",
  "Condition": "Condición",
  "Yard / Location": "Patio / Ubicación",
  "Notes": "Notas",
  "This asset requires a certification (engineered shore, slide rail, etc.)":
    "Este activo requiere certificación (apuntalamiento de ingeniería, riel deslizante, etc.)",
  "Asset ID and Asset Type are required.": "El ID y el Tipo de Activo son obligatorios.",
  "Asset created.": "Activo creado.",
  "Create failed.": "Creación fallida.",
  "Create Asset": "Crear Activo",
  "Cancel": "Cancelar",
  "Edit Asset": "Editar Activo",
  "Immutable": "Inmutable",
  "Save Changes": "Guardar Cambios",
  "Asset updated.": "Activo actualizado.",
  "Save failed.": "Guardado fallido.",
  "Retire Asset": "Retirar Activo",
  "Retirement is terminal.": "El retiro es definitivo.",
  "The asset will be removed from active service. Reactivation requires an admin edit.":
    "El activo se eliminará del servicio activo. La reactivación requiere edición de administrador.",
  "Reason": "Motivo",
  "Asset retired.": "Activo retirado.",
  "Retire failed.": "Retiro fallido.",
  "Change Status": "Cambiar Estado",
  "Current status:": "Estado actual:",
  "Status changes are validated against the lifecycle engine — holds cannot be cleared directly through status changes.":
    "Los cambios de estado se validan contra el motor de ciclo de vida — las retenciones no se pueden liberar directamente mediante cambios de estado.",
  "New Status": "Nuevo Estado",
  "Apply Status": "Aplicar Estado",
  "Status updated.": "Estado actualizado.",
  "Status change failed.": "Cambio de estado fallido.",
  "Holds": "Retenciones",
  "Open Hold": "Abrir Retención",
  "No active holds.": "Sin retenciones activas.",
  "Loading holds…": "Cargando retenciones…",
  "Hold Type": "Tipo de Retención",
  "Hold opened.": "Retención abierta.",
  "Open hold failed.": "Apertura de retención fallida.",
  "Clear Hold": "Liberar Retención",
  "Release": "Liberar",
  "Release Hold": "Liberar Retención",
  "Opened:": "Abierta:",
  "Original reason:": "Motivo original:",
  "Release reason": "Motivo de liberación",
  "Hold cleared.": "Retención liberada.",
  "Clear hold failed.": "Liberación de retención fallida.",
  "Safety Hold": "Retención de Seguridad",
  "Maintenance Hold": "Retención de Mantenimiento",
  "Certification Hold": "Retención de Certificación",
  "Inspections": "Inspecciones",
  "Record Inspection": "Registrar Inspección",
  "No inspections yet.": "Aún no hay inspecciones.",
  "Loading…": "Cargando…",
  "Type": "Tipo",
  "Result": "Resultado",
  "Severity": "Severidad",
  "Inspector Name": "Nombre del Inspector",
  "Inspector name is required.": "Se requiere el nombre del inspector.",
  "Inspection recorded.": "Inspección registrada.",
  "Daily Visual": "Visual Diaria",
  "Monthly Competent Person": "Persona Competente Mensual",
  "Annual Review": "Revisión Anual",
  "Special Inspection": "Inspección Especial",
  "Damage Inspection": "Inspección por Daño",
  "Return Inspection": "Inspección de Devolución",

  "Issuer is required.": "El emisor es obligatorio.",
  "Manufacturer": "Fabricante",
  "Annual Inspection": "Inspección Anual",
  "Engineering Letter": "Carta de Ingeniería",
  "Repair Certification": "Certificación de Reparación",
  "Special": "Especial",

  // ============================================================
  // Trench Safety · Phase 7.5C Notification strings
  // ============================================================
  // Bell titles
  "Safety Hold opened": "Retención de Seguridad abierta",
  "Inspection Hold opened": "Retención de Inspección abierta",
  "Maintenance Hold opened": "Retención de Mantenimiento abierta",
  "Certification Hold opened": "Retención de Certificación abierta",
  "Hold released": "Retención liberada",
  "Critical Inspection Failure": "Fallo Crítico de Inspección",
  "Major Inspection Failure": "Fallo Mayor de Inspección",
  "Damage reported": "Daño reportado",
  "Unsafe Condition reported": "Condición Insegura reportada",
  "Certification due ≤ 30 days": "Certificación vence ≤ 30 días",
  "Certification due ≤ 14 days": "Certificación vence ≤ 14 días",
  "Certification due ≤ 7 days": "Certificación vence ≤ 7 días",
  "Certification EXPIRED": "Certificación EXPIRADA",
  "Repair complete · awaiting Safety verification": "Reparación completa · esperando verificación de Seguridad",
  "Asset returned to service": "Activo devuelto al servicio",
  // Coaching template fragments
  "What happened:": "Qué ocurrió:",
  "Why it matters:": "Por qué importa:",
  "What to do next:": "Qué hacer a continuación:",
  "Open Asset": "Abrir Activo",
  "Review Inspection": "Revisar Inspección",
  // Digest section
  "Open Safety Holds": "Retenciones de Seguridad Abiertas",
  "Open Certification Holds": "Retenciones de Certificación Abiertas",
  "Open Inspection Holds": "Retenciones de Inspección Abiertas",
  "Open Maintenance Holds": "Retenciones de Mantenimiento Abiertas",
  "Repairs Awaiting Verification": "Reparaciones Esperando Verificación",
  "Expiring Certifications (30d)": "Certificaciones por Expirar (30d)",
  "New Damage Reports (7d)": "Nuevos Reportes de Daño (7d)",
  "Failed Inspections (7d)": "Inspecciones Fallidas (7d)",



  // ============================================================
  // Trench Safety · Phase 7.5B + Phase 7 (Repair Review · Field Reports · QR · Photos · Posture)
  // ============================================================
  "Repair Review": "Revisión de Reparaciones",
  "Safety verifies every Shop repair before the asset returns to service.": "Seguridad verifica cada reparación del Taller antes de que el activo vuelva al servicio.",
  "Field Reports": "Reportes de Campo",
  "Damage, unsafe conditions, missing pins, missing labels — every public report lands here for triage.": "Daño, condiciones inseguras, pasadores faltantes, etiquetas faltantes — cada reporte público llega aquí para triaje.",
  "Daily Posture": "Postura Diaria",
  "Loading posture…": "Cargando postura…",
  "Posture load failed.": "Carga de postura fallida.",
  "Refresh": "Actualizar",
  // Repair Review filters
  "All Open": "Todas Abiertas",
  "Awaiting Verification": "Esperando Verificación",
  "Vendor Repairs": "Reparaciones de Proveedor",
  "Verify Repair": "Verificar Reparación",
  "Verify": "Verificar",
  "Decision": "Decisión",
  "Approve · Release Inspection Hold": "Aprobar · Liberar Retención de Inspección",
  "Reject · Return to Shop": "Rechazar · Devolver al Taller",
  "Approve Repair": "Aprobar Reparación",
  "Return to Shop": "Devolver al Taller",
  "Repair verified — Inspection Hold released.": "Reparación verificada — Retención de Inspección liberada.",
  "Returned to Shop for additional repair.": "Devuelto al Taller para reparación adicional.",
  "Verification failed.": "Verificación fallida.",
  "Repair Complete does not mean Safe To Use. Verification is what releases the Inspection Hold. Safety Holds and Certification Holds are never auto-cleared.":
    "Reparación Completa no significa Seguro Para Usar. La verificación es lo que libera la Retención de Inspección. Las Retenciones de Seguridad y Certificación nunca se liberan automáticamente.",
  "Issue:": "Problema:",
  "Vendor:": "Proveedor:",
  "Severity:": "Severidad:",
  "Repair queue load failed.": "Carga de cola de reparaciones fallida.",
  "No repairs in this view.": "No hay reparaciones en esta vista.",
  // Field Reports
  "Close this report with what note?": "¿Cerrar este reporte con qué nota?",
  "Field report closed.": "Reporte de campo cerrado.",
  "Close failed.": "Cierre fallido.",
  "Field reports load failed.": "Carga de reportes de campo fallida.",
  "All Report Types": "Todos los Tipos de Reporte",
  "No field reports in this view.": "No hay reportes de campo en esta vista.",
  "Open Asset": "Abrir Activo",
  "Damage": "Daño",
  "Unsafe Condition": "Condición Insegura",
  "Missing Pins": "Pasadores Faltantes",
  "Missing Labels": "Etiquetas Faltantes",
  "Certification Concern": "Preocupación de Certificación",
  "Purpose: review every repair Shop completes before releasing the Inspection Hold. Why it matters: a finished repair is not a safe asset until Safety verifies. What happens next: Approve releases the Inspection Hold; Reject sends the repair back to Shop with a note.":
    "Propósito: revisar cada reparación que el Taller completa antes de liberar la Retención de Inspección. Por qué importa: una reparación terminada no es un activo seguro hasta que Seguridad verifique. Qué hacer a continuación: Aprobar libera la Retención de Inspección; Rechazar envía la reparación de vuelta al Taller con una nota.",
  "Purpose: review every report a crew member submits from the field. Why it matters: reports are the leading indicator of unsafe conditions. What happens next: open the asset, convert to inspection or repair, or close with a note.":
    "Propósito: revisar cada reporte que un miembro de la cuadrilla envía desde el campo. Por qué importa: los reportes son el indicador principal de condiciones inseguras. Qué hacer a continuación: abrir el activo, convertir a inspección o reparación, o cerrar con una nota.",
  // QR Management
  "QR Management": "Gestión de QR",
  "Download": "Descargar",
  "Print": "Imprimir",
  "Log Reprint": "Registrar Reimpresión",
  "Reprint logged.": "Reimpresión registrada.",
  "Reprint log failed.": "Registro de reimpresión fallido.",
  "QR History": "Historial de QR",
  "No QR activity yet.": "Sin actividad de QR aún.",
  "QR label is MASCI-branded and embeds the asset ID, serial, last inspection, and current status.":
    "La etiqueta QR tiene marca MASCI e incluye ID del activo, serie, última inspección y estado actual.",
  // Photo Management
  "Photos": "Fotos",
  "Upload Photo": "Subir Foto",
  "Choose a photo first.": "Elija una foto primero.",
  "File": "Archivo",
  "Category": "Categoría",
  "Visibility": "Visibilidad",
  "Caption": "Leyenda",
  "Internal Only": "Solo Interna",
  "Field Safe": "Apta para Campo",
  "Public": "Pública",
  "Photo uploaded.": "Foto subida.",
  "No photos yet.": "Sin fotos aún.",
  "Loading photos…": "Cargando fotos…",
  "Delete this photo?": "¿Eliminar esta foto?",
  "Photo deleted.": "Foto eliminada.",
  "Delete failed.": "Eliminación fallida.",
  "Internal Only stays inside the Safety Portal. Field Safe + Public are surfaced on the public QR view.":
    "Solo Interna permanece dentro del Portal de Seguridad. Apta para Campo + Pública aparecen en la vista pública de QR.",
  "Front": "Frente",
  "Rear": "Atrás",
  "Left": "Izquierda",
  "Right": "Derecha",
  "Serial Plate": "Placa de Serie",
  "Manufacturer Plate": "Placa de Fabricante",
  "Inspection": "Inspección",
  "Repair": "Reparación",
  "Certification": "Certificación",
  "Other": "Otro",
  // Daily Posture tiles
  "Safety Holds": "Retenciones de Seguridad",
  "Inspection Holds": "Retenciones de Inspección",
  "Certification Holds": "Retenciones de Certificación",
  "Critical Repairs": "Reparaciones Críticas",
  "Failed Insp. 7d": "Inspecciones Fallidas 7d",
  "Damage Reports": "Reportes de Daño",
  "Cert Exp. 30d": "Cert por Expirar 30d",

  "Inspection failed.": "Inspección fallida.",
  "A Fail with Major or Critical severity automatically opens an Inspection Hold and stubs a repair recommendation.":
    "Un Fallo con severidad Mayor o Crítica abre automáticamente una Retención de Inspección y crea una recomendación de reparación.",
  "Daily": "Diaria",
  "Monthly": "Mensual",
  "Annual": "Anual",
  "Pass": "Aprobado",
  "Fail": "Fallido",
  "Minor": "Menor",
  "Major": "Mayor",
  "Critical": "Crítica",
  "Certifications": "Certificaciones",
  "Upload Certification": "Subir Certificación",
  "Upload": "Subir",
  "No certifications on file.": "Sin certificaciones registradas.",
  "Certification Type": "Tipo de Certificación",
  "Issued At": "Emitida el",
  "Expires At": "Expira el",
  "Issuer": "Emisor",
  "Expires date is required.": "La fecha de expiración es obligatoria.",
  "Certification uploaded.": "Certificación subida.",
  "Upload failed.": "Subida fallida.",
  "Expires": "Expira",
  "Revoke": "Revocar",
  "Reason for revoking this certification?": "¿Motivo para revocar esta certificación?",
  "Certification revoked.": "Certificación revocada.",
  "Revoke failed.": "Revocación fallida.",
  "Due Soon": "Vence Pronto",
  "Expired": "Expirada",
  "Revoked": "Revocada",
  "OK": "OK",
  "Audit Timeline": "Línea de Tiempo de Auditoría",
  "Loading timeline…": "Cargando línea de tiempo…",
  "No audit events on file.": "Sin eventos de auditoría registrados.",
  "details": "detalles",
  "Excellent": "Excelente",
  "Good": "Bueno",
  "Fair": "Regular",
  "Poor": "Pobre",
  "Out Of Service": "Fuera de Servicio",


  // Asset list
  "Live roster of every MASCI trench safety asset. Tap an asset to see its full record.":
    "Lista en vivo de cada activo de seguridad de zanjas de MASCI. Toque un activo para ver su registro completo.",
  "asset(s)": "activo(s)",
  "Search by ID, serial, size, location…": "Buscar por ID, serie, tamaño, ubicación…",
  "Asset Type": "Tipo de Activo",
  "All Types": "Todos los Tipos",
  "Status": "Estado",
  "All Statuses": "Todos los Estados",
  "Condition": "Condición",
  "All Conditions": "Todas las Condiciones",
  "All": "Todas",
  "Yes": "Sí",
  "No": "No",
  "Loading assets…": "Cargando activos…",
  "No trench safety assets match the current filters.":
    "Ningún activo de seguridad de zanjas coincide con los filtros actuales.",
  "Asset ID": "ID de Activo",
  "Size": "Tamaño",
  "Serial #": "N° Serie",
  "Color": "Color",
  "Location": "Ubicación",
  "Last Inspection": "Última Inspección",
  "missing": "faltante",
  "never": "nunca",

  // Asset types / statuses / conditions  (already translatable above)
  "Trench Box": "Caja de Zanja",
  "End Panel": "Panel Lateral",
  "Spreader Bar": "Barra Separadora",
  "Hydraulic Shore": "Apuntalamiento Hidráulico",
  "Slide Rail System": "Sistema de Riel Deslizante",
  "Trench Jack": "Gato de Zanja",
  "Ladder": "Escalera",
  "Accessory": "Accesorio",
  // Phase 8A — Road Plate i18n
  "Road Plate": "Placa de Acero",
  "Road Plates": "Placas de Acero",
  "Road Plate · Physical Specs": "Placa de Acero · Especificaciones Físicas",
  "Road Plate · Condition Detail": "Placa de Acero · Detalle de Condición",
  "Road Plate · Specs": "Placa de Acero · Especificaciones",
  "Road Plate · Specs & Condition": "Placa de Acero · Especificaciones y Condición",
  "Road Plate · Inspection Checklist": "Placa de Acero · Lista de Inspección",
  "Length (in)": "Largo (pulg)",
  "Width (in)": "Ancho (pulg)",
  "Thickness (in)": "Espesor (pulg)",
  "Rated Capacity (lb)": "Capacidad Nominal (lb)",
  "Material": "Material",
  "Markings": "Marcas",
  "Color / Markings": "Color / Marcas",
  "Surface Condition": "Condición de Superficie",
  "Edge Condition": "Condición de Borde",
  "Lifting Point Condition": "Condición de Punto de Izaje",
  "Anti-Skid Status": "Estado Antideslizante",
  "Present": "Presente",
  "Worn": "Desgastado",
  "Missing": "Faltante",
  "N/A": "N/A",
  "e.g., Yellow paint, MASCI stencil": "p. ej., Pintura amarilla, plantilla MASCI",
  // Road Plate checklist items
  "Bent Plate": "Placa Doblada",
  "Warped Plate": "Placa Deformada",
  "Cracks": "Grietas",
  "Unsafe Deformation": "Deformación Insegura",
  "Slick Surface": "Superficie Resbalosa",
  "Missing Anti-Skid": "Antideslizante Faltante",
  "Surface Damage": "Daño en Superficie",
  "Rust": "Óxido",
  "Corrosion": "Corrosión",
  "Sharp Edge": "Borde Filoso",
  "Damaged Edge": "Borde Dañado",
  "Damaged Lift Hole": "Orificio de Izaje Dañado",
  "Damaged Lifting Point": "Punto de Izaje Dañado",
  "Proper Bearing": "Apoyo Correcto",
  "Proper Overlap": "Traslape Correcto",
  "Proper Anchoring": "Anclaje Correcto",
  "Proper Pinning": "Pasadores Correctos",
  "Traffic Safe": "Seguro para Tránsito",
  "Pedestrian Safe": "Seguro para Peatones",
  "Markings Visible": "Marcas Visibles",
  // Road Plate repair kinds
  "Weld Repair": "Reparación de Soldadura",
  "Structural Repair": "Reparación Estructural",
  "Surface Repair": "Reparación de Superficie",
  "Edge Repair": "Reparación de Borde",
  "Anti-Skid Restoration": "Restauración Antideslizante",
  // Road Plate dialog helpers
  "Asset ID is permanent. Suggested IDs follow the certified registry — TB-XX, RP-001, EP-001, etc.": "El ID del activo es permanente. Los IDs sugeridos siguen el registro certificado — TB-XX, RP-001, EP-001, etc.",
  "Findings": "Hallazgos",
  "Corrective Actions": "Acciones Correctivas",
  "I am the designated competent person for this inspection.": "Soy la persona competente designada para esta inspección.",
  "Competent person confirmation is required for this inspection type.": "Se requiere confirmación de persona competente para este tipo de inspección.",
  // Phase 8B — Operational Polish i18n
  "Quick Add Asset": "Agregar Activo Rápido",
  "Quick Add": "Agregar Rápido",
  "New Asset (Full)": "Nuevo Activo (Completo)",
  "Import CSV": "Importar CSV",
  "Import Assets · CSV": "Importar Activos · CSV",
  "Pick a type — the system suggests the next permanent ID. Fill the essentials, save, and refine later.": "Elige un tipo — el sistema sugiere el próximo ID permanente. Completa lo esencial, guarda y refina después.",
  "Suggested": "Sugerido",
  "Asset ID is required.": "Se requiere el ID del activo.",
  "Executive Summary": "Resumen Ejecutivo",
  "Total Assets": "Activos Totales",
  "On Hold": "En Espera",
  "Open Repairs": "Reparaciones Abiertas",
  "Inspections Due": "Inspecciones Pendientes",
  "Recent Activity · 7d": "Actividad Reciente · 7d",
  "Count by Status": "Conteo por Estado",
  "Count by Type": "Conteo por Tipo",
  "Operational Alerts": "Alertas Operativas",
  "Missing Photos": "Fotos Faltantes",
  "Missing Serial Number": "Número de Serie Faltante",
  "No Project Assignment": "Sin Asignación de Proyecto",
  "Needs Review": "Necesita Revisión",
  "Road Plates Missing Capacity": "Placas Sin Capacidad",
  "Tabulated Data Missing": "Datos Tabulados Faltantes",
  "Open Asset Roster": "Abrir Lista de Activos",
  "Transport": "Transporte",
  "Safety": "Seguridad",
  "Inspection": "Inspección",
  "Maint": "Mantenim.",
  "Cert": "Cert.",
  "All Types": "Todos los Tipos",
  // CSV import
  "Upload a CSV or paste rows below. Preview validates every row against the certified registry — duplicates and bad rows are blocked.": "Sube un CSV o pega filas. La vista previa valida cada fila contra el registro certificado — los duplicados y filas inválidas se bloquean.",
  "Choose CSV File": "Elegir Archivo CSV",
  "Load sample": "Cargar muestra",
  "Limit 500 rows per file": "Límite 500 filas por archivo",
  "Preview": "Vista Previa",
  "Commit Import": "Confirmar Importación",
  "Paste or upload a CSV first.": "Pega o sube un CSV primero.",
  "Preview failed.": "La vista previa falló.",
  "Nothing to import. Preview shows zero valid rows.": "Nada que importar. La vista previa muestra cero filas válidas.",
  "Import failed.": "La importación falló.",
  "Imported": "Importados",
  "Skipped": "Omitidos",
  "will insert": "se insertará",
  "duplicate": "duplicado",
  "error": "error",
  "Row": "Fila",
  "Errors": "Errores",
  "Close": "Cerrar",
  // Phase 8C — Operational Intelligence / Pulse
  "Operational Intelligence": "Inteligencia Operativa",
  "Trench Safety Pulse": "Pulso de Seguridad de Zanjas",
  "Week of": "Semana del",
  "Last generated": "Última generación",
  "Delivered": "Entregado",
  "View Current Pulse": "Ver Pulso Actual",
  "Generate Snapshot": "Generar Instantánea",
  "Generate + Send": "Generar + Enviar",
  "Generate failed.": "La generación falló.",
  "Pulse generated.": "Pulso generado.",
  "Pulse generated and dispatched": "Pulso generado y enviado",
  "recipient(s)": "destinatario(s)",
  "History": "Historial",
  "Pulse History": "Historial de Pulsos",
  "No pulses generated yet. Press Generate Snapshot to create the first.": "Aún no se han generado pulsos. Presiona Generar Instantánea para crear el primero.",
  "Rendering pulse…": "Renderizando pulso…",
  "items requiring attention": "elementos requieren atención",
  "Needs Attention": "Necesita Atención",
  "Critical": "Crítico",
  "sent": "enviado",
  "not_sent": "no enviado",
  "live_preview": "vista previa",
  "no_recipients": "sin destinatarios",
  "email_disabled": "email deshabilitado",
  "Recent · 7d": "Reciente · 7d",
  // Phase 9A — Reports
  "Trench Safety Reports": "Reportes de Seguridad de Zanjas",
  "Operational reporting on certified data": "Reportes operativos sobre datos certificados",
  "Reports": "Reportes",
  "Nine read-only operational reports computed from the certified asset registry. Apply filters once — they cascade across every report. CSV export available on each section.": "Nueve reportes operativos de solo lectura calculados desde el registro certificado de activos. Aplica filtros una vez — se propagan a todos los reportes. Exportación CSV disponible en cada sección.",
  "All figures are read directly from the certified Trench Safety registry, audit log, inspection/repair/hold collections, and the latest stored Pulse snapshot. No analytics engine, no separate data store.": "Todas las cifras se leen directamente del registro certificado, bitácora de auditoría, colecciones de inspección/reparación/retención y la última instantánea de Pulso. Sin motor analítico, sin almacén de datos separado.",
  "Global Filters": "Filtros Globales",
  "Date From": "Desde",
  "Date To": "Hasta",
  "Reset Filters": "Restablecer Filtros",
  "CSV": "CSV",
  "Loading…": "Cargando…",
  "Executive Asset Health": "Salud Ejecutiva de Activos",
  "Road Plate Command": "Mando de Placas",
  "Inspection Compliance": "Cumplimiento de Inspección",
  "Repair Backlog": "Backlog de Reparaciones",
  "Hold Management": "Gestión de Retenciones",
  "Asset Utilization": "Utilización de Activos",
  "Missing Data": "Datos Faltantes",
  "Project Asset": "Activo por Proyecto",
  "Activity & Audit": "Actividad y Auditoría",
  "Asset Availability": "Disponibilidad",
  "Operational Health": "Salud Operativa",
  "Window": "Ventana",
  "Activity Count": "Eventos",
  "Compliance Score": "Puntaje de Cumplimiento",
  "Due Soon": "Próximo a Vencer",
  "Overdue": "Vencido",
  "Failed · 30d": "Fallidas · 30d",
  "Yard / Location": "Yarda / Ubicación",
  "Compliance %": "Cumplimiento %",
  "Completed": "Completadas",
  "Avg Days Open": "Días Abiertos · Prom",
  "Avg Days to Close": "Días al Cierre · Prom",
  "Kind": "Tipo",
  "Repair Count": "Reparaciones",
  "Active": "Activos",
  "Released": "Liberados",
  "Maintenance": "Mantenim.",
  "Certification": "Cert",
  "Hold Count": "Retenciones",
  "Active Holds": "Retenciones Activas",
  "Idle": "Inactivos",
  "Total": "Total",
  "In Use": "En Uso",
  "Util %": "Util %",
  "Assets Deployed": "Activos Desplegados",
  "Capacity Bucket": "Categoría de Capacidad",
  "Unknown": "Desconocido",
  "Trend · 30 Days": "Tendencia · 30 Días",
  "Repair Activity": "Actividad de Reparación",
  "Deployment Events": "Eventos de Despliegue",
  "Utilization": "Utilización",
  "Missing Capacity Data": "Datos de Capacidad Faltantes",
  "Missing Manufacturer": "Fabricante Faltante",
  "Missing Inspection": "Inspección Faltante",
  "Missing Project Assignment": "Asignación de Proyecto Faltante",
  "Missing Location": "Ubicación Faltante",
  "Missing Tabulated Data": "Datos Tabulados Faltantes",
  "Missing Capacity": "Capacidad Faltante",
  "Missing Serial": "Serie Faltante",
  "affected assets": "activos afectados",
  "Projects with Assets": "Proyectos con Activos",
  "Total Rows": "Filas Totales",
  "Assets": "Activos",
  "Trench Boxes": "Cajas de Zanja",
  "Insp Due": "Insp Pend.",
  "Holds": "Retenciones",
  "Health": "Salud",
  "Risk": "Riesgo",
  "Event Kind": "Tipo de Evento",
  "Repairs Opened": "Reparaciones Abiertas",
  "Holds Opened": "Retenciones Abiertas",
  "Assets Deployed": "Activos Desplegados",
  "Active Assets": "Activos Activos",
  // Phase 9B — Report Automation & Distribution
  "Subscriptions": "Suscripciones",
  "Report Subscriptions": "Suscripciones de Reportes",
  "Active Subscriptions": "Suscripciones Activas",
  "Install Road Plate Leadership Package": "Instalar Paquete de Liderazgo de Placas",
  "Road Plate Leadership Package": "Paquete de Liderazgo de Placas",
  "installed": "instalados",
  "already present": "ya presentes",
  "Install failed.": "La instalación falló.",
  "Create Subscription": "Crear Suscripción",
  "Subscription created.": "Suscripción creada.",
  "Subscription deleted.": "Suscripción eliminada.",
  "Subscription name is required.": "Se requiere el nombre de la suscripción.",
  "Update failed.": "La actualización falló.",
  "Delete failed.": "La eliminación falló.",
  "Run Now": "Ejecutar Ahora",
  "Run complete": "Ejecución completa",
  "Run failed.": "La ejecución falló.",
  "Disable": "Deshabilitar",
  "Enable": "Habilitar",
  "Last run": "Última ejecución",
  "Next due": "Próxima",
  "Recipients (comma)": "Destinatarios (coma)",
  "Weekly": "Semanal",
  "Monthly": "Mensual",
  "Format": "Formato",
  "Frequency": "Frecuencia",
  "Report": "Reporte",
  "Weekly Executive · Safety": "Ejecutivo Semanal · Seguridad",
  "no subscriptions yet": "aún no hay suscripciones",
  "Leadership Digest": "Resumen de Liderazgo",
  "Trench Safety Leadership Digest": "Resumen de Liderazgo de Seguridad de Zanjas",
  "Digest dispatched": "Resumen enviado",
  "Send failed.": "El envío falló.",
  // Phase 10A — Public Excavation Workflow
  "Excavation Operations": "Operaciones de Excavación",
  "Operaciones de Excavación": "Operaciones de Excavación",
  "Excavation Operations Record": "Registro de Operaciones de Excavación",
  "Excavation Record Submitted": "Registro de Excavación Enviado",
  "Submit Excavation Record": "Enviar Registro",
  "Submit a field excavation record. Coaching first. EN / ES.": "Envía un registro de excavación de campo. Enfoque de coaching. EN / ES.",
  "Coaching first — if unsure on any field, select 'Needs Review' and Safety will follow up.": "Coaching primero — si tienes dudas, selecciona 'Necesita Revisión' y Seguridad dará seguimiento.",
  "Excavation Oversight": "Supervisión de Excavaciones",
  "Public field submissions · review and close": "Envíos públicos del campo · revisar y cerrar",
  "Field crews submit excavation records from the Public Safety Tile. Coaching language. No punitive vocabulary.": "Las cuadrillas envían registros desde el Panel Público de Seguridad. Lenguaje de coaching. Sin vocabulario punitivo.",
  "Excavations": "Excavaciones",
  "Project / Job Information": "Proyecto / Información del Trabajo",
  "Excavation Dimensions": "Dimensiones de Excavación",
  "Length (ft)": "Largo (ft)",
  "Width (ft)": "Ancho (ft)",
  "Depth (ft)": "Profundidad (ft)",
  "Is excavation 4 feet or deeper?": "¿Excavación de 4 pies o más?",
  "Is excavation 5 feet or deeper?": "¿Excavación de 5 pies o más?",
  "Cave-in hazard under 5 ft?": "¿Peligro de derrumbe bajo 5 pies?",
  "Work Type": "Tipo de Trabajo",
  "Soil / Ground Conditions": "Condiciones del Suelo",
  "If unsure, select Unknown / Needs Review — Safety will follow up.": "Si tienes dudas, selecciona Desconocido / Necesita Revisión.",
  "Protective System": "Sistema de Protección",
  "Explain (required when 5 ft+ and Not Required)": "Explica (requerido cuando 5 ft+ y No Requerido)",
  "Assigned Trench Safety Assets": "Activos Asignados",
  "Enter asset IDs (TB-XX, RP-XXX, EP-XXX...). Comma-separated.": "Ingresa IDs de activos (TB-XX, RP-XXX, EP-XXX...). Separados por comas.",
  "Access / Egress": "Acceso / Egreso",
  "Access/egress required?": "¿Acceso/egreso requerido?",
  "Access/egress installed?": "¿Acceso/egreso instalado?",
  "Within 25 ft lateral travel?": "¿Dentro de 25 ft de recorrido lateral?",
  "Ladder extends above landing?": "¿Escalera se extiende sobre el descanso?",
  "Access/egress secure?": "¿Acceso/egreso seguro?",
  "Utility Locate": "Localización de Servicios",
  "Utility locate required?": "¿Se requiere localización?",
  "Ticket Number": "Número de Boleto",
  "Locate Status": "Estado de Localización",
  "Utility conflicts observed?": "¿Conflictos de servicios observados?",
  "Utility Notes": "Notas de Servicios",
  "Spoils / Edge Protection": "Despojos / Protección de Borde",
  "Spoils ≥ 2 ft from edge?": "¿Despojos ≥ 2 ft del borde?",
  "Equipment / materials near edge?": "¿Equipo / materiales cerca del borde?",
  "Barricades in place?": "¿Barricadas en su lugar?",
  "Stop logs / warning system?": "¿Topes / sistema de advertencia?",
  "Water Conditions": "Condiciones de Agua",
  "Water present?": "¿Agua presente?",
  "Seepage present?": "¿Filtración presente?",
  "Dewatering required?": "¿Achique requerido?",
  "Dewatering active?": "¿Achique activo?",
  "Needs Safety review?": "¿Necesita revisión de Seguridad?",
  "Atmosphere / Hazard Conditions": "Atmósfera / Peligros",
  "Deep / confined hazard concern?": "¿Preocupación profunda / confinada?",
  "Hazardous atmosphere concern?": "¿Atmósfera peligrosa?",
  "Atmospheric testing required?": "¿Pruebas atmosféricas requeridas?",
  "Atmospheric testing completed?": "¿Pruebas atmosféricas completadas?",
  "Competent Person Name": "Nombre de Persona Competente",
  "I confirm CP role for this excavation": "Confirmo el rol de PC para esta excavación",
  "Pre-entry inspection completed?": "¿Inspección previa completada?",
  "Reinspection required (rain / change)?": "¿Reinspección requerida (lluvia / cambio)?",
  "Reinspection completed?": "¿Reinspección completada?",
  "Photos can be uploaded after submission via the asset photo workflow. (Phase 10A.2)": "Las fotos pueden subirse después del envío. (Fase 10A.2)",
  "Field Notes": "Notas de Campo",
  "Notes can be English or Spanish — both are preserved.": "Las notas pueden ser en inglés o español — ambas se conservan.",
  "Yes": "Sí", "No": "No",
  "Project, Supervisor, and Submitted By are required.": "Proyecto, Supervisor y Enviado Por son obligatorios.",
  "Submission failed.": "El envío falló.",
  "Coaching Flags": "Banderas de Coaching",
  "Back to Public Safety Tile": "Volver al Panel Público",
  "Project Number": "Número de Proyecto",
  "Location": "Ubicación",
  "Work Area": "Área de Trabajo",
  "Date of Work": "Fecha del Trabajo",
  "Supervisor / Foreman": "Supervisor / Capataz",
  "Crew": "Cuadrilla",
  "Submitted By": "Enviado Por",
  "Contact Phone": "Teléfono de Contacto",
  "Project": "Proyecto",
  "Submitted": "Enviado",
  "Needs Review": "Necesita Revisión",
  "Action Required": "Acción Requerida",
  "Pending Verification": "Pendiente Verificación",
  "Reviewed": "Revisado",
  "Closed": "Cerrado",
  "Reopened": "Reabierto",
  "All Statuses": "Todos los Estados",
  "Project name": "Nombre del Proyecto",
  "Supervisor": "Supervisor",
  "Min depth ft": "Profundidad mín ft",
  "no excavation records": "sin registros de excavación",
  "Coaching note (optional)": "Nota de coaching (opcional)",
  "Request Clarification": "Solicitar Aclaración",
  "Mark Reviewed": "Marcar Revisado",
  "Review": "Revisar",
  "Saved": "Guardado",
  "Depth": "Profundidad",
  "Protective": "Protección",
  "Soil": "Suelo",
  "N/A": "N/A",
  "Type A": "Tipo A", "Type B": "Tipo B", "Type C": "Tipo C",
  "Stable Rock": "Roca Estable",
  "Unknown / Needs Review": "Desconocido / Necesita Revisión",
  "Trench Box / Shielding": "Caja de Zanja / Blindaje",
  "Shoring": "Apuntalamiento",
  "Sloping": "Talud",
  "Benching": "Bancada",
  "Combination": "Combinación",
  "Not Required": "No Requerido",
  "Needs Safety Review": "Necesita Revisión de Seguridad",
  "Complete": "Completo",
  "Pending": "Pendiente",
  "Conflict / Needs Review": "Conflicto / Necesita Revisión",
  "Assigned": "Asignado",
  "In Transport": "En Tránsito",
  "Repair": "Reparación",
  "Retired": "Retirado",
  "Excellent": "Excelente",
  "Good": "Bueno",
  "Fair": "Regular",
  "Poor": "Malo",
  "Out Of Service": "Fuera de Servicio",

  // Asset detail
  "Back to Trench Equipment": "Volver al Equipo de Zanjas",
  "Loading asset…": "Cargando activo…",
  "Asset not found.": "Activo no encontrado.",
  "Physical plate verification required before use.":
    "Se requiere verificación de la placa física antes de usar.",
  "Manufacturer or model data not yet verified.":
    "Datos del fabricante o modelo aún no verificados.",
  "Tabulated Data Missing": "Faltan Datos Tabulados",
  "No manufacturer PDF linked to this asset yet. ":
    "Aún no se ha vinculado un PDF del fabricante a este activo. ",
  "Browse library": "Explorar biblioteca",
  "Identification": "Identificación",
  "Manufacturer": "Fabricante",
  "Model": "Modelo",
  "Operational": "Operativo",
  "Current Location": "Ubicación Actual",
  "Current Project": "Proyecto Actual",
  "Yard": "Patio",
  "Next Inspection Due": "Próxima Inspección",
  "Certification Expires": "Vence Certificación",
  "Last Repair": "Última Reparación",
  "Field View": "Vista de Campo",
  "Open QR Field View": "Abrir Vista QR de Campo",
  "Mobile-first read-only crew view. Safe to scan in the field.":
    "Vista de solo lectura optimizada para móvil. Segura para escanear en campo.",
  "Reference": "Referencia",
  "Browse Tabulated Data Library": "Explorar Biblioteca de Datos Tabulados",
  "Manufacturer-engineered OSHA tabulated PDFs.":
    "PDFs de datos tabulados OSHA diseñados por el fabricante.",
  "Recent Inspections": "Inspecciones Recientes",
  "Recent Repairs": "Reparaciones Recientes",
  "Recent Deployments": "Despliegues Recientes",
  "No inspections yet.": "Aún no hay inspecciones.",
  "No repairs on file.": "Sin reparaciones registradas.",
  "No deployments recorded.": "Sin despliegues registrados.",
  "Pass": "Aprobado",
  "Fail": "Rechazado",
  "Pending Review": "Revisión Pendiente",
  "active": "activo",
  "Report damage before the box goes into the trench. A box on Inspection Hold is not available for use.":
    "Reporte daños antes de que la caja entre a la zanja. Una caja en Retención de Inspección no está disponible para uso.",
  "Inspection, repair, assign/return and edit actions land in later certified phases. This Phase 3 view is read-only.":
    "Las acciones de inspección, reparación, asignar/devolver y editar llegarán en fases certificadas posteriores. Esta vista de Fase 3 es de solo lectura.",
  "Open": "Abrir",

  // Phase 4A — Equipment Inventory + Operations Integration
  "Assign to Project": "Asignar a Proyecto",
  "Return from Project": "Devolver del Proyecto",
  "Return to Yard": "Devolver al Patio",
  "Returned to yard": "Devuelto al patio",
  "Assigned to ": "Asignado a ",
  "Assigned By": "Asignado Por",
  "Returned By": "Devuelto Por",
  "Condition at Assignment": "Condición al Asignar",
  "Condition at Return": "Condición al Devolver",
  "Source": "Origen",
  "Project Number": "Número de Proyecto",
  "Project Name": "Nombre del Proyecto",
  "Project #": "Proyecto #",
  "Superintendent": "Superintendente",
  "Foreman": "Capataz",
  "Notes": "Notas",
  "Project": "Proyecto",
  "Assigned": "Asignado",
  "Returned": "Devuelto",
  "Active": "Activo",
  "Your name": "Su nombre",
  "Project Name is required": "El nombre del proyecto es obligatorio",
  "Assign failed": "Falló la asignación",
  "Return failed": "Falló la devolución",
  "Records a real deployment. The asset becomes Assigned and appears on the project dashboard.":
    "Registra un despliegue real. El activo pasa a Asignado y aparece en el panel del proyecto.",
  "Closes the active deployment and moves the asset back to Available.":
    "Cierra el despliegue activo y devuelve el activo a Disponible.",
  "Deployment History": "Historial de Despliegues",
  "Assign": "Asignar",
  "Cancel": "Cancelar",
  "Asset is": "El activo está",
  "clear before assigning": "libérelo antes de asignar",
  "Manual Assignment": "Asignación Manual",
  "Daily Report": "Reporte Diario",
  "Project Equipment List": "Lista de Equipos del Proyecto",
  "Dispatch / Transport Log": "Registro de Despacho / Transporte",
  "Admin Adjustment": "Ajuste Administrativo",
  "Excellent": "Excelente",
  "Out Of Service": "Fuera de Servicio",

  // Phase 4B — Holds / Certifications / Alerts
  "Maintenance Hold":   "Retención de Mantenimiento",
  "Certification Hold": "Retención de Certificación",
  "Safety Hold":        "Retención de Seguridad",
  "This asset is under Maintenance. It is not available for the field.":
    "Este activo está en Mantenimiento. No está disponible para uso en campo.",
  "This asset's required certification is missing or expired. DO NOT USE.":
    "Falta la certificación requerida o ha expirado. NO USAR.",
  "SAFETY HOLD — critical condition reported. DO NOT USE. Contact Safety immediately.":
    "RETENCIÓN DE SEGURIDAD — condición crítica reportada. NO USAR. Contacte a Seguridad inmediatamente.",
  "This asset is on hold. DO NOT USE.": "Este activo está retenido. NO USAR.",

  // Phase 5 — Transport / Dispatch Integration
  "In Transport": "En Transporte",
  "Transfer Cancelled": "Transferencia Cancelada",
  "Hold Preserved": "Retención Preservada",
  "From": "Desde",
  "To": "Hasta",
  "Delivered": "Entregado",
  "Received": "Recibido",
  "Moving a box does not clear a hold.": "Mover una caja no elimina una retención.",
  "A trench box on hold may be transported, but it is not available for use.":
    "Una caja de zanja retenida puede ser transportada, pero no está disponible para uso.",
  "Location updates when Dispatch/Transport completes the move.":
    "La ubicación se actualiza cuando Despacho/Transporte completa el movimiento.",
  "Scan the QR to verify the box before it goes in the trench.":
    "Escanee el QR para verificar la caja antes de bajarla a la zanja.",

  // Public Safety Tile — corrected to surface the full Trench Safety field portal
  "OPEN TRENCH SAFETY": "ABRIR SEGURIDAD DE ZANJA",

  // Phase 6 — Shop Repair Workflow
  "Trench Safety Repairs": "Reparaciones de Seguridad de Zanja",
  "Waiting on Parts": "Esperando Repuestos",
  "Vendor Repair": "Reparación por Proveedor",
  "Closed After Verification": "Cerrado tras Verificación",
  "Pending Safety Verification": "Pendiente de Verificación de Seguridad",
  "Reinspection Required": "Reinspección Requerida",
  "Repair Notes": "Notas de Reparación",
  "Repair Cost": "Costo de Reparación",
  "Repair Vendor": "Proveedor de Reparación",
  "Mark Repair Completed": "Marcar Reparación Completada",
  "Do Not Use": "No Usar",
  "Under Repair": "En Reparación",
  "Awaiting Verification": "Esperando Verificación",
  "Verify Repair": "Verificar Reparación",
  "Verification Notes": "Notas de Verificación",
  "Start Repair": "Iniciar Reparación",
  "Add Note": "Agregar Nota",

  // Phase 7 — QR Labels + Photo Management
  "QR Label": "Etiqueta QR",
  "Generate QR Label": "Generar Etiqueta QR",
  "Print Label": "Imprimir Etiqueta",
  "Download PNG": "Descargar PNG",
  "Reprint Label": "Reimprimir Etiqueta",
  "Photo Gallery": "Galería de Fotos",
  "Upload Photo": "Subir Foto",
  "Category": "Categoría",
  "Caption": "Leyenda",
  "Front": "Frente",
  "Rear": "Atrás",
  "Side": "Lado",
  "Serial Number": "Número de Serie",
  "Manufacturer Plate": "Placa del Fabricante",
  "Inspection Photo": "Foto de Inspección",
  "Damage Photo": "Foto de Daño",
  "Repair Photo": "Foto de Reparación",
  "Deployment Photo": "Foto de Despliegue",
  "Field Safe": "Seguro para Campo",
  "Internal Only": "Solo Interno",
  "Upload Failed": "Subida Fallida",
  "Upload Complete": "Subida Completa",
  "Field-facing entry point for the MASCI Trench Safety system — asset lookup, QR scan landing, tabulated data, safety reference, and damage / unsafe / missing-pin / missing-label reporting. Bilingual.":
    "Punto de entrada en campo para el sistema de Seguridad de Zanja de MASCI — búsqueda de activos, escaneo QR, datos tabulados, referencia de seguridad y reportes de daños / inseguro / pasadores faltantes / etiquetas faltantes. Bilingüe.",

  // QR landing
  "MASCI Trench Safety": "Seguridad de Zanjas MASCI",
  "This QR is not linked to a known MASCI trench safety asset. Contact Safety.":
    "Este QR no está vinculado a un activo de seguridad de zanjas conocido de MASCI. Contacte a Seguridad.",
  "Do not use": "No usar",
  "This asset is on Inspection Hold. A competent person must clear it before use.":
    "Este activo está en Retención de Inspección. Una persona competente debe liberarlo antes de usar.",
  "This asset is under Repair. It is not available for the field.":
    "Este activo está en Reparación. No está disponible para uso en campo.",
  "Serial number not on file — verify the physical plate before use.":
    "Número de serie no registrado — verifique la placa física antes de usar.",
  "This asset is flagged for Safety review.":
    "Este activo está marcado para revisión por Seguridad.",
  "Asset Details": "Detalles del Activo",
  "Current Use": "Uso Actual",
  "on file": "registrado",
  "Open Tabulated Data": "Abrir Datos Tabulados",
  "Scanning confirms the asset record — it does not move the asset. Location updates when the asset is assigned, transported, or returned. Report damage before the box goes into the trench.":
    "El escaneo confirma el registro del activo — no mueve el activo. La ubicación se actualiza cuando el activo se asigna, transporta o devuelve. Reporte daños antes de que la caja entre a la zanja.",
  "MASCI Operations Platform": "Plataforma de Operaciones MASCI",
  "Field-safe view": "Vista segura de campo",
  "Asset not found": "Activo no encontrado",
  "Safety": "Seguridad",
  "Dashboard": "Panel",

  // ============================================================
  // Phase 3.5 — Public Trench Safety Dashboard / Lookup / Report
  // ============================================================
  "Field reference for every MASCI trench safety asset. Look up a box, open its tabulated data, or report a problem.":
    "Referencia de campo para cada activo de seguridad de zanjas MASCI. Busque una caja, abra sus datos tabulados o reporte un problema.",
  "Fleet Overview": "Resumen de Flota",
  "Loading overview…": "Cargando resumen…",
  "Could not load overview.": "No se pudo cargar el resumen.",
  "Asset Lookup": "Búsqueda de Activo",
  "Type an Asset ID printed on the box (TB-07, EP-001, SP-001…) to see its status, last inspection, and tabulated data.":
    "Escriba el ID de Activo impreso en la caja (TB-07, EP-001, SP-001…) para ver su estado, última inspección y datos tabulados.",
  "Enter Asset ID (e.g. TB-07)": "Ingrese ID de Activo (ej. TB-07)",
  "Look Up": "Buscar",
  "Safety References": "Referencias de Seguridad",
  "Plain-English / Spanish primer · what tabulated data is and how to read it in the field.":
    "Manual claro · qué son los datos tabulados y cómo leerlos en el campo.",
  "Report a Problem": "Reportar un Problema",
  "Damage · Unsafe Condition · Missing Pins · Missing Labels. Goes straight to Safety.":
    "Daño · Condición Insegura · Pines Faltantes · Etiquetas Faltantes. Va directo a Seguridad.",
  "QR Scan:": "Escaneo QR:",
  "Scan the QR label on any MASCI trench box to open its asset record. Scanning does not move the asset — location updates when the asset is assigned, transported, or returned.":
    "Escanee la etiqueta QR de cualquier caja de zanja MASCI para abrir su registro. El escaneo no mueve el activo — la ubicación se actualiza cuando el activo se asigna, transporta o devuelve.",

  // Report modal
  "What's wrong?": "¿Qué pasó?",
  "Damage": "Daño",
  "Unsafe Condition": "Condición Insegura",
  "Missing Pins": "Pines Faltantes",
  "Missing Labels": "Etiquetas Faltantes",
  "What did you see? (5+ characters)": "¿Qué observó? (5+ caracteres)",
  "e.g. crack near top rail on the east side; missing R-pin on spreader…":
    "ej. grieta cerca del riel superior en el lado este; pin R faltante en el separador…",
  "Your name (optional)": "Su nombre (opcional)",
  "Contact (optional)": "Contacto (opcional)",
  "phone or email": "teléfono o email",
  "Your report goes to MASCI Safety for review. Submitting does not change the asset's status — Shop and Safety decide next steps.":
    "Su reporte va a Seguridad MASCI para revisión. Enviar no cambia el estado del activo — Taller y Seguridad deciden los siguientes pasos.",
  "Submit Report": "Enviar Reporte",
  "Could not submit report. Please try again.": "No se pudo enviar el reporte. Intente de nuevo.",
  "Could not submit report.": "No se pudo enviar el reporte.",
  "Report Received": "Reporte Recibido",
  "Safety has been notified. The asset has NOT been moved or changed — Shop and Safety will review and take it from here.":
    "Seguridad ha sido notificada. El activo NO ha sido movido ni cambiado — Taller y Seguridad revisarán y se encargarán a partir de aquí.",
  "Close": "Cerrar",
  "Home": "Inicio",
  "Know Before You Dig": "Conozca Antes de Excavar",
  "This is where your trench shield's life-safety data lives. Every box in the MASCI fleet has a manufacturer-engineered data sheet that tells you exactly how deep you can dig, in what soil, with what spreaders, and under what conditions. Read it. Understand it. It's the difference between a safe shift and a collapse.":
    "Aquí viven los datos de seguridad de su escudo de zanja. Cada caja en la flota MASCI tiene una hoja de datos diseñada por el fabricante que le dice exactamente qué tan profundo puede excavar, en qué tipo de suelo, con qué separadores y bajo qué condiciones. Léala. Entiéndala. Es la diferencia entre un turno seguro y un colapso.",
  "Start with the primer below": "Comience con la guía a continuación",
  "— a plain-English / Spanish walkthrough of what tabulated data is, why OSHA requires it, and how to read it in the field. Then open the":
    " — un recorrido en inglés sencillo / español de qué son los datos tabulados, por qué OSHA los requiere y cómo leerlos en el campo. Luego abra la",
  "to grab the exact PDF for the shield you're using.":
    "para obtener el PDF exacto del escudo que está usando.",
  "OSHA-compliant trench shields in MASCI fleet":
    "Escudos de zanja conformes a OSHA en la flota MASCI",
  "Tap any box to see its size, weight, and maximum allowable depth by soil type (OSHA 1926 Subpart P).":
    "Toque cualquier caja para ver su tamaño, peso y profundidad máxima permitida por tipo de suelo (OSHA 1926 Subparte P).",
  "Search by manufacturer, model, serial…":
    "Buscar por fabricante, modelo, número de serie…",
  "No trench boxes have been added yet":
    "Aún no se han agregado cajas de zanja",
  "An admin will add MASCI's trench-box fleet here. Once added, the data will be searchable on every device.":
    "Un administrador agregará la flota de cajas de zanja de MASCI aquí. Una vez agregadas, los datos se podrán buscar en cualquier dispositivo.",
  "Type": "Tipo",
  "Length (ft)": "Largo (ft)",
  "Width Min/Max (ft)": "Ancho Mín/Máx (ft)",
  "Sidewall H × Thickness": "Altura × Espesor de Pared",
  "Weight (lbs)": "Peso (lbs)",
  "Spreaders": "Separadores",
  "Stacking": "Apilable",
  "Maximum Allowable Depth (OSHA 1926.652)":
    "Profundidad Máxima Permitida (OSHA 1926.652)",
  "View Manufacturer Tabulated Data PDF":
    "Ver PDF de Datos Tabulados del Fabricante",
  // Tabulated Data Library — public crew-facing labels
  "Field Reference": "Referencia de Campo",
  "Tabulated Data Library": "Biblioteca de Datos Tabulados",
  "Manufacturer tabulated-data PDFs, technical data sheets, and educational resources — one folder per trench box plus a shared":
    "PDFs de datos tabulados del fabricante, hojas técnicas y recursos educativos — una carpeta por cada caja de zanja más una compartida",
  "General / Educational": "General / Educativo",
  "folder. Total:": "carpeta. Total:",
  "files across": "archivos en",
  "folders.": "carpetas.",
  "Start Here": "Comience Aquí",
  "Box": "Caja",
  "No files for this box yet. Ask the office to upload the manufacturer data sheet.":
    "Aún no hay archivos para esta caja. Pídale a la oficina que suba la hoja de datos del fabricante.",
  "General / Educational — United Rentals explainers, OSHA references":
    "General / Educativo — explicaciones de United Rentals, referencias OSHA",

  // ============================================================
  // Trench Box Poster (printable QR poster)
  // ============================================================
  "Trench Box QR Poster": "Cartel QR de Cajas de Zanja",
  "Scan before you dig.": "Escanee antes de excavar.",
  "Every MASCI trench shield. OSHA max-depth by soil type. One scan, one tap, one answer.":
    "Cada escudo de zanja MASCI. Profundidad máxima OSHA por tipo de suelo. Un escaneo, un toque, una respuesta.",
  "Open your phone camera. Point it at the QR. Tap the link. Find your shield. Read its Type-C max depth before the bucket touches dirt.":
    "Abra la cámara del teléfono. Apunte al QR. Toque el enlace. Encuentre su escudo. Lea la profundidad máxima Tipo C antes de que el balde toque tierra.",
  "Soil Type Quick Reference": "Referencia Rápida de Tipo de Suelo",
  "Type A — Cohesive (clay)": "Tipo A — Cohesivo (arcilla)",
  "Most stable. Compact, fine-grained.": "Más estable. Compacto, grano fino.",
  "Type B — Cohesive or granular": "Tipo B — Cohesivo o granular",
  "Average. Silty clay, dry rock.": "Promedio. Arcilla limosa, roca seca.",
  "Type C — Granular / submerged":
    "Tipo C — Granular / sumergido",
  "Least stable. Sand, gravel, water.":
    "Menos estable. Arena, grava, agua.",
  "When in doubt — call it Type C and get a Competent Person on site before the next bucket.":
    "Cuando tenga duda — clasifíquelo como Tipo C y traiga a una Persona Competente antes del siguiente balde.",
  "Fleet on file": "Flota registrada",
  "MASCI Trench Box Fleet at a Glance":
    "Flota MASCI de Cajas de Zanja de un Vistazo",
  "Manufacturer · Model": "Fabricante · Modelo",
  "Length": "Largo",
  "Type C-60 Max": "Máx Tipo C-60",
  "All depths per OSHA 1926.652. Verify against the manufacturer's tabulated data on every job.":
    "Todas las profundidades según OSHA 1926.652. Verifique con los datos tabulados del fabricante en cada trabajo.",
  "OSHA 1926 Subpart P · Excavations":
    "OSHA 1926 Subparte P · Excavaciones",
  "Post inside every excavation kit toolbox.":
    "Coloque dentro de cada caja de herramientas de excavación.",
  "Scan to open MASCI Trench Box Data on any phone.":
    "Escanee para abrir los Datos de Cajas de Zanja MASCI en cualquier teléfono.",
  "Open Trench Box Poster": "Abrir Cartel de Caja de Zanja",
  "Print Poster": "Imprimir Cartel",

  // ============================================================
  // JHP Plans Poster (printable QR poster)
  // ============================================================
  "Job Hazard Plans QR Poster": "Cartel QR de Planes de Peligros del Trabajo",
  "Job Hazard Plans · One per active job":
    "Planes de Peligros del Trabajo · Uno por trabajo activo",
  "Read the plan before crew breaks ground.":
    "Lea el plan antes de que la cuadrilla comience.",
  "Every active MASCI job. Its own Hazard Plan PDF. One scan.":
    "Cada trabajo MASCI activo. Su propio PDF del Plan de Peligros. Un escaneo.",
  "Open your phone camera. Point at the QR. Pick your job. Read the Hazard Plan before the first shovel moves. No service? Save the PDF to your phone and read it offline.":
    "Abra la cámara del teléfono. Apunte al QR. Elija su trabajo. Lea el Plan de Peligros antes de que la primera pala se mueva. ¿Sin señal? Guarde el PDF en su teléfono y léalo sin conexión.",
  "What's in a Hazard Plan": "Qué hay en un Plan de Peligros",
  "Site-specific hazards": "Peligros específicos del sitio",
  "Traffic, utilities, deep cuts, water, overhead lines.":
    "Tráfico, servicios subterráneos, cortes profundos, agua, líneas aéreas.",
  "PPE & permits": "EPP y permisos",
  "What gets worn, what gets pulled before the crew steps in.":
    "Qué se usa, qué se obtiene antes de que entre la cuadrilla.",
  "Emergency response": "Respuesta de emergencia",
  "Nearest hospital, muster point, who calls 911 first.":
    "Hospital más cercano, punto de reunión, quién llama al 911 primero.",
  "If you can't find your job's plan in the list — STOP and call your PM. Don't break ground without one.":
    "Si no encuentra el plan de su trabajo en la lista — DETÉNGASE y llame a su Gerente de Proyecto. No comience sin uno.",
  "Plans currently uploaded": "Planes cargados actualmente",
  "Active MASCI jobs": "Trabajos MASCI activos",
  "jobs covered": "trabajos cubiertos",
  "Project #": "# de Proyecto",
  "Project Name": "Nombre del Proyecto",
  "List shows only jobs that have a plan uploaded. Scan the QR for the live, complete list.":
    "La lista muestra solo trabajos con un plan cargado. Escanee el QR para la lista completa en vivo.",
  "Sample of MASCI active jobs. Scan the QR for the live, complete list with download links.":
    "Muestra de trabajos MASCI activos. Escanee el QR para la lista completa en vivo con enlaces de descarga.",
  "Post inside every job trailer.": "Coloque dentro de cada tráiler de trabajo.",

  // ============================================================
  // Site Posters (Admin Hub panel)
  // ============================================================
  "Site Posters": "Carteles del Sitio",
  "Printable handouts for every job trailer":
    "Folletos imprimibles para cada tráiler de trabajo",
  "QR-coded posters foremen scan from any phone. One sheet each. Print before every quarterly safety refresh.":
    "Carteles con código QR que los capataces escanean desde cualquier teléfono. Una hoja cada uno. Imprima antes de cada actualización trimestral de seguridad.",
  "Print All Posters": "Imprimir Todos los Carteles",
  "All Site Posters · Print 3 sheets":
    "Todos los Carteles · Imprimir 3 hojas",
  "Foreman handout. QR to the Hub + 4-step submit flow + stop-the-line rules.":
    "Folleto del capataz. QR al Hub + flujo de 4 pasos + reglas para detener la línea.",
  "Post inside every site trailer.": "Coloque dentro de cada tráiler del sitio.",
  "OSHA 1926 Subpart P. QR to live trench-shield specs + soil-type quick reference.":
    "OSHA 1926 Subparte P. QR a especificaciones de escudos en vivo + referencia rápida de tipo de suelo.",
  "QR to Job Hazard Plans hub + job list + what-to-look-for cheat card.":
    "QR al Hub de Planes de Peligros + lista de trabajos + tarjeta de qué buscar.",
  "Preview": "Vista Previa",
  "Print": "Imprimir",
  "Admin": "Admin",
  "Crew Hub": "Hub de Cuadrilla",
  "Loading…": "Cargando…",

  // ============================================================
  // Shop Console (mechanics) — 2026-04-28
  // ============================================================
  "Shop": "Taller",
  "Mechanics & Shop": "Mecánicos y Taller",
  "Shop Console": "Consola del Taller",
  "Shop Sign In": "Iniciar Sesión Taller",
  "Shop Password": "Contraseña del Taller",
  "Enter the shop password": "Ingrese la contraseña del taller",
  "Welcome to the Shop": "Bienvenido al Taller",
  "Shop Use Only": "Solo Uso del Taller",
  "Sign in to review every Pre-Op inspection, sign off on Out-of-Service and Needs-Attention items, and keep the fleet running.":
    "Inicie sesión para revisar cada inspección Pre-Op, firmar los artículos Fuera de Servicio y de Atención Requerida, y mantener la flota funcionando.",
  "Pre-Op trends, open Out-of-Service / Needs-Attention items, and the full equipment list. Sign-off in one tap.":
    "Tendencias Pre-Op, artículos abiertos Fuera de Servicio / Atención Requerida y la lista completa de equipo. Firme con un solo toque.",
  "Password-gated · sign off on FAILs · clear units back to operate":
    "Protegido con contraseña · firme las fallas · libere unidades para operar",
  "Trends · Open Items · Equipment List · Recent Inspections":
    "Tendencias · Artículos Abiertos · Lista de Equipo · Inspecciones Recientes",
  "Pre-Op & Equipment": "Pre-Op y Equipo",
  "Every Pre-Op inspection. Sign off on Out-of-Service and Needs-Attention items so jobs can keep moving.":
    "Cada inspección Pre-Op. Firme los artículos Fuera de Servicio y de Atención Requerida para que los trabajos sigan adelante.",
  "Inspections on file": "Inspecciones registradas",
  "Units flagged FAIL": "Unidades marcadas FALLA",
  "Shop sign-offs": "Firmas del taller",
  "Equipment in fleet": "Equipo en la flota",
  "Open Items": "Artículos Abiertos",
  "Trends": "Tendencias",
  "Recent Inspections": "Inspecciones Recientes",
  "Equipment List": "Lista de Equipo",
  "Recent Pre-Op Inspections": "Inspecciones Pre-Op Recientes",
  "No equipment inspections yet.": "Aún no hay inspecciones de equipo.",
  "MASCI Fleet": "Flota MASCI",
  "units": "unidades",
  "Search unit, make, model…": "Buscar unidad, marca, modelo…",
  "All categories": "Todas las categorías",
  "No matching equipment.": "No hay equipo que coincida.",
  "Unit #": "# de Unidad",
  "Make": "Marca",
  "Model": "Modelo",
  "Category": "Categoría",
  "Could not load shop data": "No se pudo cargar los datos del taller",
  "Sign out": "Cerrar sesión",
  "Hub": "Hub",

  // Open Items panel
  "Open Shop Items": "Artículos Abiertos del Taller",
  "All severities": "Todas las severidades",
  "Out of Service only": "Solo Fuera de Servicio",
  "Needs Attention only": "Solo Atención Requerida",
  "Refresh": "Actualizar",
  "All clear.": "Todo en orden.",
  "Every Pre-Op fail has been signed off by the shop.":
    "Toda falla Pre-Op ha sido firmada por el taller.",
  "Severity": "Severidad",
  "Unit": "Unidad",
  "Failed item": "Artículo fallido",
  "Operator": "Operador",
  "Date": "Fecha",
  "Action": "Acción",
  "OUT OF SERVICE": "FUERA DE SERVICIO",
  "NEEDS ATTENTION": "ATENCIÓN REQUERIDA",
  "OOS": "FDS",
  "ATTN": "ATN",
  "Sign Off": "Firmar",
  "signed": "firmado",
  "FAIL": "NO CUMPLE",

  // Sign-off card
  "Shop Sign-Off": "Firma del Taller",
  "Your name (mechanic / shop)": "Su nombre (mecánico / taller)",
  "Optional notes (parts replaced, follow-up needed, etc.)":
    "Notas opcionales (partes reemplazadas, seguimiento necesario, etc.)",
  "Repaired": "Reparado",
  "Tagged out of service": "Etiquetado fuera de servicio",
  "Parts ordered": "Partes ordenadas",
  "No action needed": "No requiere acción",
  "Enter your name to sign off.": "Ingrese su nombre para firmar.",
  "Signed off.": "Firmado.",
  "Could not save sign-off.": "No se pudo guardar la firma.",
  "Reopen this item? The shop sign-off stamp will be removed.":
    "¿Reabrir este artículo? El sello de firma del taller será removido.",
  "Reopened.": "Reabierto.",
  "Could not reopen.": "No se pudo reabrir.",
  "Shop signed off": "Taller firmó",
  "By": "Por",
  "Reopen": "Reabrir",

  // ViewEquipmentInspection
  "Inspection not found": "Inspección no encontrada",
  "Permanently delete this equipment inspection?":
    "¿Eliminar permanentemente esta inspección de equipo?",
  "Deleted": "Eliminado",
  "Could not delete": "No se pudo eliminar",
  "All Inspections": "Todas las Inspecciones",
  "Email": "Correo",
  "View": "Ver",

  // Auth shared
  "Login failed": "Inicio de sesión fallido",
  "Wrong password": "Contraseña incorrecta",
  "Login failed — check connection":
    "Inicio de sesión fallido — verifique la conexión",
  "Login failed — server didn't return a token":
    "Inicio de sesión fallido — el servidor no devolvió un token",
  "Server is waking up — give it ~60 seconds and try again":
    "El servidor está despertando — espere ~60 segundos e intente de nuevo",
  "Server error": "Error del servidor",
  "try again in a moment": "intente de nuevo en un momento",
  "Request timed out — server is cold-starting, try again":
    "Tiempo de espera agotado — el servidor está iniciando, intente de nuevo",
  "Can't reach server — check your internet":
    "No se puede conectar al servidor — verifique su internet",
  "Verifying…": "Verificando…",
  "Sign In": "Iniciar Sesión",

  // Activity Feed + Parts Catalog (2026-04-28)
  "Activity Feed": "Bitácora de Actividad",
  "Shop Activity Feed": "Bitácora del Taller",
  "No sign-offs recorded yet. Once the shop closes out a FAIL it will appear here.":
    "Aún no hay firmas registradas. Cuando el taller cierre una FALLA aparecerá aquí.",
  "Open": "Abrir",
  "Signed off": "Firmado",
  "Parts Catalog": "Catálogo de Partes",
  "Pick a Unit": "Elija una Unidad",
  "Search unit, make, model, category…": "Buscar unidad, marca, modelo, categoría…",
  "No matching units.": "No hay unidades que coincidan.",
  "Pick a unit to view its parts catalog": "Elija una unidad para ver su catálogo de partes",
  "Search the 589-unit fleet above. Each unit has filters, cutting edges, wiper blades, tires, and other wear items.":
    "Busque la flota de 589 unidades. Cada unidad tiene filtros, cuchillas, plumas, llantas y otros artículos de desgaste.",
  "Last updated": "Última actualización",
  "by": "por",
  "Your name": "Su nombre",
  "Save Catalog": "Guardar Catálogo",
  "Catalog saved.": "Catálogo guardado.",
  "Could not save catalog.": "No se pudo guardar el catálogo.",
  "Could not load fleet list": "No se pudo cargar la lista de flota",
  "Enter your name before saving.": "Ingrese su nombre antes de guardar.",
  "Filters": "Filtros",
  "Cutting Edges": "Cuchillas",
  "Wiper Blades": "Plumas Limpiaparabrisas",
  "Tires": "Llantas",
  "Other Wear Items": "Otros Artículos de Desgaste",
  "Add Part": "Agregar Parte",
  "No parts on file. Click Add Part.": "No hay partes registradas. Haga clic en Agregar Parte.",
  "Part name": "Nombre de la parte",
  "Part #": "# de Parte",
  "Qty": "Cant.",
  "Notes": "Notas",
  "Size": "Tamaño",
  "Position": "Posición",
  "Ply": "Capas",
  "Brand": "Marca",
  "Add to order list": "Agregar a la lista de pedido",
  "Remove part": "Eliminar parte",
  "Already in order list": "Ya está en la lista de pedido",
  "Added to order list": "Agregado a la lista de pedido",

  // Order cart
  "Order List": "Lista de Pedido",
  "Tap the cart icon next to a part to add it. Then send the list to the parts office.":
    "Toque el ícono del carrito al lado de una parte para agregarla. Luego envíe la lista a la oficina de partes.",
  "Name": "Nombre",
  "Your name (mechanic)": "Su nombre (mecánico)",
  "Send to email(s) — comma-separated": "Enviar a correo(s) — separados por coma",
  "CC (optional)": "CC (opcional)",
  "Additional notes (e.g. needed by Friday for PM service)":
    "Notas adicionales (ej. se necesita el viernes para servicio PM)",
  "Email Order to Parts Office": "Enviar Pedido a Oficina de Partes",
  "Order list is empty.": "La lista de pedido está vacía.",
  "Enter your name.": "Ingrese su nombre.",
  "Enter at least one email address to send to.": "Ingrese al menos un correo de destino.",
  "Parts order emailed.": "Pedido de partes enviado.",
  "Could not send order email.": "No se pudo enviar el correo del pedido.",
  "CLEARED TO OPERATE": "LIBERADO PARA OPERAR",

  // QC tile (coming soon, 2026-04-28)
  "QC": "Control de Calidad",
  "Coming Soon": "Próximamente",
  "In development": "En desarrollo",
  "Quality Control workflows for the asphalt & roadway field team — daily roadway reports, testing reports, and other fillable QC documents to turn in. Coming soon.":
    "Flujos de Control de Calidad para el equipo de campo de asfalto y vialidades — reportes diarios de vialidad, reportes de pruebas y otros documentos QC para llenar y entregar. Próximamente.",
  "Roadway reports · density logs · core sample logs":
    "Reportes de vialidad · registros de densidad · registros de núcleos",
  "Testing reports · fillable QC docs · field-team submittals":
    "Reportes de pruebas · documentos QC para llenar · entregas del equipo de campo",

  // ============================================================
  // Persistence + Backup admin panels (2026-04-28)
  // ============================================================
  "Persistent database connected": "Base de datos persistente conectada",
  "Mongo host:": "Host de Mongo:",
  "Redeploys will not wipe your data.": "Los redespliegues no borrarán sus datos.",
  "Your data will be deleted on the next redeploy":
    "Sus datos se borrarán en el próximo redespliegue",
  "MongoDB is running": "MongoDB se está ejecutando",
  "inside this container": "dentro de este contenedor",
  "which means every new deploy destroys your database.":
    "lo que significa que cada nuevo despliegue destruye su base de datos.",
  "Before you redeploy next time, always click the button below to grab + email a full backup":
    "Antes de redesplegar, haga clic en el botón a continuación para obtener y enviar por correo una copia de seguridad completa",
  ", or you will lose everything created since the last nightly backup.":
    ", o perderá todo lo creado desde la última copia de seguridad nocturna.",
  "Permanent fix:": "Solución permanente:",
  "switch the production app to": "cambie la aplicación de producción a",
  "(free tier, 15-min setup) — see the instructions your developer sent. Once the Atlas connection string is in your production env vars, this banner will turn green and redeploys become safe forever.":
    "(plan gratuito, configuración en 15 minutos) — vea las instrucciones que su desarrollador envió. Una vez que la cadena de conexión Atlas esté en sus variables de entorno de producción, este aviso se pondrá verde y los redespliegues serán seguros para siempre.",
  "Building backup + emailing to {dest}…": "Creando copia + enviando por correo a {dest}…",
  "you": "usted",
  "Backup saved + emailed to {dest} + downloaded.":
    "Copia guardada + enviada a {dest} + descargada.",
  "Backup saved + downloaded.": "Copia guardada + descargada.",
  "Email step skipped — check BACKUP_EMAIL_TO + RESEND_API_KEY.":
    "Paso de correo omitido — verifique BACKUP_EMAIL_TO + RESEND_API_KEY.",
  "Backup failed": "La copia de seguridad falló",
  "Building + sending…": "Creando + enviando…",
  "Backup + email + download NOW": "Copia + correo + descargar AHORA",
  "Emails to": "Correos a",
  "BACKUP_EMAIL_TO not set": "BACKUP_EMAIL_TO no configurado",
  "Sign up for MongoDB Atlas": "Regístrese en MongoDB Atlas",
  "Last on-server backup:": "Última copia en servidor:",

  // BackupHeroPanel
  "Building your complete backup… ~30 seconds": "Creando su copia de seguridad completa… ~30 segundos",
  "Backed up": "Respaldados",
  "records": "registros",
  "emailed to": "enviado a",
  "downloaded": "descargado",
  "Backup failed — please try again": "La copia falló — intente de nuevo",
  "Please pick a .zip backup file": "Elija un archivo .zip de copia de seguridad",
  "File exceeds 500 MB limit": "El archivo excede el límite de 500 MB",
  "Restoring backup… ~30 seconds": "Restaurando copia… ~30 segundos",
  "Restored": "Restaurados",
  "records across": "registros en",
  "collections": "colecciones",
  "Restore failed": "La restauración falló",
  "Restore failed — see console": "La restauración falló — vea la consola",
  "Backup & Restore Everything": "Copia y Restauración de Todo",
  "Two buttons. Your whole MASCI Operations Platform — every form, every photo, every Crew Hub message.":
    "Dos botones. Toda su Plataforma de Operaciones MASCI — cada formulario, cada foto, cada mensaje del Hub de Cuadrilla.",
  "Building backup…": "Creando copia…",
  "Backup Everything": "Copia de Todo",
  "Step 1 · Do this before any redeploy": "Paso 1 · Haga esto antes de cualquier redespliegue",
  "Downloads a single .zip containing every safety record, photo, signature, PDF, Crew Hub message, to-do, schedule, and doc. Also emails a copy to your inbox.":
    "Descarga un solo .zip que contiene cada registro de seguridad, foto, firma, PDF, mensaje del Hub de Cuadrilla, tarea, horario y documento. También envía una copia a su correo.",
  "Restoring…": "Restaurando…",
  "Restore From File": "Restaurar Desde Archivo",
  "Step 2 · Use after a redeploy to get data back": "Paso 2 · Use después de un redespliegue para recuperar datos",
  "Pick a MASCI backup .zip from your computer. Every record inside is merged into the live system. Safe — existing data isn't wiped.":
    "Elija un archivo .zip de copia MASCI de su computadora. Cada registro adentro se fusiona al sistema en vivo. Seguro — los datos existentes no se borran.",
  "The .zip is a normal file": "El .zip es un archivo normal",
  "you can open it in Windows Explorer or Mac Finder with no password, no special tool. Each safety record is inside as both a raw .json and a printable .pdf. Photos and signatures are embedded in the JSON. Safe to archive forever.":
    "puede abrirlo en el Explorador de Windows o el Finder de Mac sin contraseña ni herramienta especial. Cada registro de seguridad está adentro como un .json crudo y un .pdf imprimible. Las fotos y firmas están embebidas en el JSON. Seguro para archivar para siempre.",
  "Restore from": "Restaurar desde",
  "Every record inside this .zip will be merged into the live system — existing rows are overwritten with the backup's copy, new rows are added. Anything in the DB that isn't in the backup is left alone. This is safe to run.":
    "Cada registro adentro de este .zip se fusionará al sistema en vivo — las filas existentes se sobrescriben con la copia de seguridad, se agregan nuevas filas. Lo que no esté en la copia se deja intacto. Es seguro ejecutarlo.",
  "Cancel": "Cancelar",
  "Yes, restore it": "Sí, restaurar",

  // ============================================================
  // Crew Hub Login + AppHome (2026-04-28)
  // ============================================================
  "Welcome back,": "Bienvenido de nuevo,",
  "there": "ahí",
  "What are you working on today?": "¿En qué está trabajando hoy?",
  "Every MASCI job has its own workspace here — message board, to-dos, schedule, docs, and progress tracking. Pick a project to jump in.":
    "Cada trabajo MASCI tiene su propio espacio aquí — tablero de mensajes, tareas, horario, documentos y seguimiento de progreso. Elija un proyecto para entrar.",
  "Loading projects…": "Cargando proyectos…",
  "No projects yet": "Aún no hay proyectos",
  "An owner will add you to projects shortly. You still have MASCI HQ below for company-wide announcements.":
    "Un propietario lo agregará a los proyectos pronto. Aún tiene MASCI HQ abajo para anuncios de toda la compañía.",
  "Crew Hub · Sign in": "Hub de Cuadrilla · Iniciar sesión",
  "Welcome back.": "Bienvenido de nuevo.",
  "Use the email address MASCI issued you.": "Use el correo electrónico que MASCI le emitió.",
  "Password": "Contraseña",
  "Sign in": "Iniciar sesión",
  "First time?": "¿Primera vez?",
  "Your login is the @mascigc.com email MASCI issued you — not 'admin'. Temp password is Welcome2MASCI! — you'll be asked to change it right after sign-in. Forgot your password? An owner can reset it from the Users panel.":
    "Su inicio de sesión es el correo @mascigc.com que MASCI le emitió — no 'admin'. La contraseña temporal es Welcome2MASCI! — se le pedirá cambiarla justo después de iniciar sesión. ¿Olvidó su contraseña? Un propietario puede restablecerla desde el panel de Usuarios.",
  "Looking for the Safety Admin console (inspections, equipment, JHP plans)? Use":
    "¿Busca la consola de Admin de Seguridad (inspecciones, equipo, planes JHP)? Use",
  "that's a different system.": "ese es un sistema diferente.",
  "Back to MASCI Operations Platform": "Volver a la Plataforma de Operaciones MASCI",

  // ============================================================
  // Hub tile rewrite (2026-04-30) + ThankYou page (2026-05-01)
  // ============================================================
  "Enter section →": "Entrar a la sección →",
  "Open →": "Abrir →",
  "End-of-day reports and equipment walk-arounds for the crew on the ground.":
    "Reportes de fin de día y recorridos de equipo para la cuadrilla en campo.",
  "Daily Reports — what the crew did today":
    "Reportes Diarios — lo que la cuadrilla hizo hoy",
  "Equipment Pre-Op — OSHA walk-around with pass / fail":
    "Pre-Op de Equipo — recorrido OSHA con aprobado / fallado",
  "Inspections, toolbox talks, incident reports, JHPs, and trench-box guidance — if safety is on your mind, it lives here.":
    "Inspecciones, charlas de seguridad, reportes de incidentes, JHPs y guía de cajas de zanja — si la seguridad está en mente, aquí vive.",
  "Site Inspections · Safety Meetings · Incidents":
    "Inspecciones · Juntas de Seguridad · Incidentes",
  "Job Hazard Plans · Trench Box Reference":
    "Planes de Peligros · Referencia de Cajas de Zanja",
  "QA / QC": "QA / QC",
  "Quality Assurance and Quality Control workflows for the field team — pour cards, density logs, and inspection forms ready to fill out and turn in. More forms rolling out soon.":
    "Flujos de Aseguramiento y Control de Calidad para el equipo de campo — tarjetas de vaciado, registros de densidad y formularios de inspección listos para llenar y entregar. Más formularios próximamente.",
  "Asphalt density · core samples · roadway reports":
    "Densidad de asfalto · núcleos · reportes de vialidad",
  "Rebar inspections · concrete form inspections":
    "Inspecciones de varilla · inspecciones de formaletas de concreto",
  "Daily QA / QC submittals · field-team turn-ins":
    "Entregas QA/QC diarias · entregas del equipo de campo",
  "Project Management": "Gestión de Proyectos",
  "PM Portal": "Portal de Gestión",
  "The day-to-day project-management workspace — every job, every record, every master list, in one place.":
    "El espacio diario de gestión de proyectos — cada trabajo, cada registro, cada lista maestra, en un solo lugar.",
  "Active jobs · email routing · site posters":
    "Trabajos activos · ruteo de correos · carteles del sitio",
  "Equipment fleet · employees · suppliers":
    "Flota de equipo · empleados · proveedores",
  "The mechanic's console for the MASCI equipment fleet. Sign off failed Pre-Ops, clear units back to service, and stay on top of open items.":
    "La consola del mecánico para la flota de equipo MASCI. Firme Pre-Ops fallidos, libere unidades para volver al servicio y esté al día con los pendientes.",
  "Open Out-of-Service · Needs-Attention queue":
    "Cola Fuera de Servicio · Requiere Atención",
  "Recent inspections · full equipment list":
    "Inspecciones recientes · lista completa de equipo",
  "The full office console. Dashboards, master records, and the back-office tools for the whole platform.":
    "La consola de oficina completa. Tableros, registros maestros y herramientas de respaldo para toda la plataforma.",
  "Records · master lists · compliance exports":
    "Registros · listas maestras · exportes de cumplimiento",
  "Office staff only": "Solo personal de oficina",

  // ThankYou
  "Submitted": "Enviado",
  "Thank you.": "Gracias.",
  "The MASCI safety team has been notified. Stay safe out there.":
    "El equipo de seguridad de MASCI fue notificado. Cuídese allá afuera.",
  "Submit Another": "Enviar Otro",
  "Close Window": "Cerrar Ventana",
  "Inspection": "Inspección",
  "Meeting": "Reunión",
  "JHP": "JHP",
  "Incident": "Incidente",
  "Daily Report": "Reporte Diario",
  "Equipment Inspection": "Inspección de Equipo",

  // PmLogin (2026-05-01)
  "Enter the PM password": "Ingrese la contraseña PM",
  "Welcome, PM": "Bienvenido, PM",
  "PM Portal Sign In": "Portal de Gestión — Iniciar Sesión",
  "Project-manager workspace — every record, every form, every master list. Backup / restore controls live in the Admin Console only.":
    "Espacio del gerente de proyectos — cada registro, cada formulario, cada lista maestra. Los controles de respaldo / restauración viven solo en la Consola de Admin.",
  "PM Password": "Contraseña PM",
  "MASCI · Project Management Portal": "MASCI · Portal de Gestión de Proyectos",

  // ============================================================
  // Training Hub (2026-05-01)
  // ============================================================
  "Training": "Capacitación",
  "Training Hub": "Centro de Capacitación",
  "MASCI Training": "Capacitación MASCI",
  "Short lessons, printable cheat sheets, and video walk-throughs for Field, Shop, PMs, and Admins. New hires up to speed in an afternoon.":
    "Lecciones cortas, hojas imprimibles y videos tutoriales para Campo, Taller, Gerentes y Admins. Nuevos empleados al día en una tarde.",
  "Field Crew · Shop · PM · Admin tracks":
    "Tracks de Campo · Taller · Gerente · Admin",
  "Written guides + video slots + print-friendly":
    "Guías escritas + videos + listo para imprimir",
  "Short, focused lessons for every role — Field Crews, Shop, Project Managers, and Admins. Written walk-throughs, printable cheat sheets, and video tutorials. Pick your track.":
    "Lecciones cortas y enfocadas para cada rol — Cuadrillas de Campo, Taller, Gerentes y Admins. Guías escritas, hojas imprimibles y videos tutoriales. Elija su track.",
  "lessons": "lecciones",
  "more…": "más…",
  "Open track →": "Abrir track →",
  "Admin note": "Nota para admins",
  "Shop / PM / Admin tracks require their respective passwords. The Field Crew track is public — no login needed. Each lesson has a video slot; admins can paste YouTube / Loom / Vimeo URLs via the Admin console → Training Videos panel.":
    "Los tracks de Taller / Gerente / Admin requieren sus contraseñas. El track de Campo es público — sin inicio de sesión. Cada lección tiene un espacio para video; los admins pueden pegar URLs de YouTube / Loom / Vimeo desde la consola de Admin → panel de Videos de Capacitación.",
  "All Tracks": "Todos los Tracks",
  "Training Track": "Track de Capacitación",
  "Print all cheat sheets": "Imprimir todas las hojas",
  "Why this matters": "Por qué importa",
  "What happens next": "Qué pasa después",
  "Common mistakes": "Errores comunes",
  // iter202 — Operational Guidance Center landing translation
  "MASCI Operations Platform · Operational Guidance Center": "Plataforma de Operaciones MASCI · Centro de Guía Operacional",
  // iter203/iter204 — Portal Training Directory inside Guidance
  // (iter204 reframed cards from production-launchers → training-first)
  "Training & Onboarding · By Portal": "Capacitación y Orientación · Por Portal",
  "Portal Training": "Capacitación de Portal",
  "Open each portal's training to learn what it does, who uses it, and how to operate it. Sign-in links are available if you already know your portal.": "Abra la capacitación de cada portal para aprender qué hace, quién lo usa y cómo operarlo. Los enlaces de inicio de sesión están disponibles si ya conoce su portal.",
  "Open Training": "Abrir Capacitación",
  "Go to portal sign-in": "Ir al inicio de sesión del portal",
  "Sign in": "Iniciar sesión",
  "Portal-specific training, role-based help, troubleshooting, and operational knowledge. Filtered by your portal access.": "Capacitación específica del portal, ayuda por rol, solución de problemas y conocimiento operacional. Filtrado por su acceso al portal.",
  "Public field-crew training is open below. Portal-specific training (HR · Safety · Shop · Dispatch · PM · Field Leadership · Admin) appears when you sign in.": "La capacitación pública de cuadrilla está abierta abajo. La capacitación específica del portal (RH · Seguridad · Taller · Despacho · PM · Liderazgo de Campo · Admin) aparece cuando inicia sesión.",
  "Sign in for portal training": "Iniciar sesión para capacitación del portal",
  "Search guidance — by role, task, or keyword": "Buscar guía — por rol, tarea o palabra clave",
  "Public · No Sign-In Required": "Público · Sin Inicio de Sesión",
  "Field Crew Training": "Capacitación de Cuadrilla de Campo",
  "Sign-In Required · Your Portals": "Inicio de Sesión Requerido · Sus Portales",
  "Portal Training": "Capacitación de Portal",
  "All portal articles": "Todos los artículos del portal",
  "article": "artículo",
  "articles": "artículos",
  "By Topic": "Por Tema",
  "Browse all guidance": "Explorar toda la guía",
  "No guidance is available for your access level yet.": "Aún no hay guía disponible para su nivel de acceso.",
  // iter200 — LeadershipLogin
  "Field Leadership Portal": "Portal de Liderazgo de Campo",
  "Field Leadership is the operational portal for Superintendents, Foremen, Field Leaders, and Operations Oversight — the people running crews on the ground.": "El Liderazgo de Campo es el portal operacional para Superintendentes, Capataces, Líderes de Campo y Supervisión de Operaciones — la gente que dirige las cuadrillas en el suelo.",
  "Uses a shared leadership password — every record you submit is individually signed inside the form (your name, your signature). Accountability is at the record, not the door.": "Usa una contraseña compartida de liderazgo — todo registro que envía se firma individualmente dentro del formulario (su nombre, su firma). La rendición de cuentas pasa al nivel del registro, no en la puerta.",
  "Leadership Password": "Contraseña de Liderazgo",
  "Verifying…": "Verificando…",
  "New to Field Leadership?": "¿Nuevo en Liderazgo de Campo?",
  "First-Week Onboarding": "Orientación de Primera Semana",
  "What does Field Leadership do?": "¿Qué hace el Liderazgo de Campo?",
  "Can't sign in?": "¿No puede iniciar sesión?",
  "Admin tokens and PM tokens also satisfy the Field Leadership gate — Operations Managers and PMs can read leadership records without re-signing in.": "Los tokens de Admin y PM también satisfacen la puerta de Liderazgo de Campo — los Gerentes de Operaciones y PMs pueden leer registros de liderazgo sin volver a iniciar sesión.",
  "MASCI · Field Leadership Portal": "MASCI · Portal de Liderazgo de Campo",
  "Access granted": "Acceso concedido",
  "Incorrect password": "Contraseña incorrecta",
  "Step-by-step": "Paso a paso",
  "Tips": "Consejos",
  "Cheat Sheet": "Hoja de Referencia",
  "Video tutorial coming soon": "Video tutorial próximamente",
  "Open video": "Abrir video",
  "Video unavailable": "Video no disponible",
  "Spanish version not available for this lesson":
    "Versión en español no disponible para esta lección",
  "Training video unavailable. Please contact your MASCI administrator.":
    "Video de capacitación no disponible. Comuníquese con su administrador de MASCI.",
  "Open video in new tab": "Abrir video en nueva pestaña",
  "This track is password-protected": "Este track requiere contraseña",
  "Back to Training Hub": "Volver al Centro de Capacitación",
  "Downloadable packets": "Paquetes descargables",
  "PDF training packets · no login required": "Paquetes PDF de capacitación · sin inicio de sesión",
  "PDF training packets": "Paquetes PDF de capacitación",
  "Field Crew is public — share with insurance, auditors, or new-hire onboarding. Shop, PM, and Admin packets require their respective passwords (back-office workflows aren't shared outside the company).":
    "Cuadrilla de Campo es público — compártalo con aseguradoras, auditores o nuevos empleados. Los paquetes de Taller, PM y Admin requieren sus contraseñas (los flujos internos no se comparten fuera de la empresa).",
  "Public": "Público",
  "Shop sign-in": "Acceso Taller",
  "PM sign-in": "Acceso PM",
  "Admin sign-in": "Acceso Admin",
  "Share these links with insurance, auditors, or new-hire onboarding. Cover, table of contents, and every lesson in one file — in English or Spanish.":
    "Comparta estos enlaces con seguros, auditores o nuevos empleados. Portada, contenido y cada lección en un archivo — en inglés o español.",

  // Training Scan-&-Go + New Hire Onboarding (2026-05-01)
  "Scan-&-Go Posters": "Carteles Escanee y Vaya",
  "1-page QR poster per track · tape in every trailer":
    "Cartel QR de 1 página por track · pegue en cada tráiler",
  "Three QR codes per poster — EN, ES, and EN+ES side-by-side. Print, tape, done. No typing URLs on phones.":
    "Tres códigos QR por cartel — EN, ES y EN+ES lado a lado. Imprima, pegue, listo. Sin escribir URLs en teléfonos.",
  "View": "Ver",
  "Print": "Imprimir",
  "Coming soon": "Próximamente",
  "New Hire Onboarding": "Orientación de Nuevos Empleados",
  "A guided first-day checklist for every new MASCI hire: watch the core Field lessons, take a short quiz, sign an acknowledgement, and you're cleared for the site. HR gets a paper trail, the new hire gets confidence, insurance gets peace of mind.":
    "Una lista guiada del primer día para cada nuevo empleado MASCI: vea las lecciones de Campo, responda un breve examen, firme un acuerdo, y queda listo para el sitio. RH obtiene registro, el empleado obtiene confianza, seguros obtienen tranquilidad.",
  "Required lesson tracking per employee":
    "Seguimiento de lecciones requeridas por empleado",
  "5-question quiz + pass/fail threshold":
    "Examen de 5 preguntas + umbral aprobado/reprobado",
  "Digital signed acknowledgement stored on the employee record":
    "Acuse digital firmado guardado en el registro del empleado",
  "Admin dashboard: who's onboarded, who's outstanding, who's expired":
    "Tablero de admin: quién está orientado, pendiente, vencido",

  // SitePostersPanel — training rows
  "Training Scan-&-Go · Field Crew": "Escanee y Vaya · Cuadrilla de Campo",
  "Training Scan-&-Go · Shop": "Escanee y Vaya · Taller",
  "Training Scan-&-Go · PM": "Escanee y Vaya · Gerente",
  "Training Scan-&-Go · Admin": "Escanee y Vaya · Admin",
  "3 QR codes (EN / ES / EN+ES) → the full Field Crew training packet. Bilingual poster.":
    "3 códigos QR (EN / ES / EN+ES) → paquete completo de Cuadrilla de Campo. Cartel bilingüe.",
  "3 QR codes (EN / ES / EN+ES) → the Shop / Mechanic training packet.":
    "3 códigos QR (EN / ES / EN+ES) → paquete del Taller / Mecánico.",
  "3 QR codes (EN / ES / EN+ES) → the PM / Project Management training packet.":
    "3 códigos QR (EN / ES / EN+ES) → paquete del Gerente de Proyecto.",
  "3 QR codes → the Admin / Owner training packet incl. backup, restore, and security.":
    "3 códigos QR → paquete del Admin / Dueño incl. respaldo, restauración y seguridad.",
  "Post inside the shop office and parts room.":
    "Pegue dentro de la oficina del taller y cuarto de partes.",
  "Post on the wall behind the PM's desk.":
    "Pegue en la pared detrás del escritorio del Gerente.",
  "Keep in the admin / owner's office binder.":
    "Guarde en la carpeta de la oficina del Admin / Dueño.",

  // TrainingStatsStripe (2026-05-01)
  "Training scans · last 7 days": "Escaneos de capacitación · últimos 7 días",
  "vs prior week": "vs semana anterior",
  "By track": "Por track",
  "By language": "Por idioma",
  "All-time total": "Total histórico",
  "14-day trend": "Tendencia 14 días",
  "today": "hoy",

  // Track gating (2026-05-01)
  "Password required": "Contraseña requerida",
  "Internal track — covers back-office workflows. Sign in as":
    "Track interno — cubre flujos de oficina. Inicie sesión como",
  "to see the lessons and packets.": "para ver las lecciones y paquetes.",
  "Sign in →": "Iniciar sesión →",
  "Internal training · password required":
    "Capacitación interna · contraseña requerida",
  "This packet covers internal MASCI workflows and is only shared with office staff.":
    "Este paquete cubre flujos internos de MASCI y solo se comparte con personal de oficina.",
  "Opening packet…": "Abriendo paquete…",
  "Your packet is ready": "Su paquete está listo",
  "If it didn't open in a new tab, your browser may have blocked the pop-up — check your downloads folder.":
    "Si no abrió en una nueva pestaña, el navegador puede haber bloqueado el pop-up — revise la carpeta de descargas.",
  "Back to track": "Volver al track",
  "Couldn't open the packet": "No se pudo abrir el paquete",

  // ===== Material Calculators =====
  "Material Calculators": "Calculadoras de Materiales",
  "Quickly estimate aggregate, asphalt, concrete, truck loads, yield, waste, and tons-to-cubic-yard conversions from the field.":
    "Estime rápidamente agregado, asfalto, concreto, cargas de camión, rendimiento, desperdicio y conversiones de toneladas a yardas cúbicas desde el campo.",
  "Field · Estimate Quantities": "Campo · Estimar Cantidades",
  "Fast field math for aggregate, asphalt, concrete, truck loads, yield, waste, and tons↔CY conversions.":
    "Matemáticas rápidas de campo para agregado, asfalto, concreto, cargas de camión, rendimiento, desperdicio y conversiones ton↔yd³.",

  // Tabs
  "Aggregate": "Agregado",
  "Asphalt": "Asfalto",
  "Concrete": "Concreto",
  "Truck Load": "Carga de Camión",
  "Yield / Waste": "Rendimiento / Desperdicio",
  "Tons ↔ CY": "Ton ↔ YD³",

  // Panel titles
  "Aggregate Calculator": "Calculadora de Agregado",
  "Asphalt Calculator": "Calculadora de Asfalto",
  "Concrete Calculator": "Calculadora de Concreto",
  "Truck Load Calculator": "Calculadora de Carga de Camión",
  "Yield / Waste Factor": "Factor de Rendimiento / Desperdicio",
  "Tons ↔ Cubic Yards Conversion": "Conversión Toneladas ↔ Yardas Cúbicas",

  // Inputs
  "Length (ft)": "Largo (pies)",
  "Width (ft)": "Ancho (pies)",
  "Thickness": "Espesor",
  "Unit": "Unidad",
  "inches": "pulgadas",
  "feet": "pies",
  "Material": "Material",
  "Density (lb/ft³)": "Densidad (lb/pie³)",
  "Override if mix/lab report differs.": "Sobrescriba si el reporte del laboratorio/mezcla difiere.",
  "Waste %": "Desperdicio %",
  "Truck capacity (tons)": "Capacidad del camión (toneladas)",
  "Total material needed": "Material total necesario",
  "Truck capacity": "Capacidad del camión",
  "Truck capacity unit": "Unidad de capacidad del camión",
  "Density (lb/ft³) for conversion": "Densidad (lb/pie³) para la conversión",
  "Planned quantity": "Cantidad planeada",
  "Actual installed quantity": "Cantidad realmente instalada",
  "Target waste % (optional override)": "Desperdicio objetivo % (anulación opcional)",
  "Direction": "Dirección",
  "Tons → Cubic Yards": "Toneladas → Yardas Cúbicas",
  "Cubic Yards → Tons": "Yardas Cúbicas → Toneladas",
  "Quantity": "Cantidad",
  "Mixer capacity (cy)": "Capacidad del mezclador (yd³)",
  "Typical ready-mix truck ≈ 10 cy.": "Camión típico de concreto premezclado ≈ 10 yd³.",
  "Coarse aggregate % (optional)": "Agregado grueso % (opcional)",
  "Fine aggregate % (optional)": "Agregado fino % (opcional)",
  "Asphalt binder %": "Porcentaje de asfalto (ligante) %",
  "Standard HMA ≈ 145 lb/ft³.": "HMA estándar ≈ 145 lb/pie³.",

  // Material labels
  "Lime Rock Base": "Base de Roca Caliza",
  "Crushed Stone": "Piedra Triturada",
  "57 Stone": "Piedra 57",
  "Washed Shell": "Concha Lavada",
  "Sand": "Arena",
  "Base Material": "Material de Base",
  "RAP (Recycled Asphalt)": "RAP (Asfalto Reciclado)",
  "Custom": "Personalizado",

  // Units in results
  "tons": "toneladas",
  "cy": "yd³",
  "cf": "pie³",
  "cubic yards": "yardas cúbicas",
  "cubic feet": "pies cúbicos",
  "loads": "cargas",

  // Result labels
  "Cubic Feet": "Pies Cúbicos",
  "Cubic Yards": "Yardas Cúbicas",
  "Tons": "Toneladas",
  "Tons + Waste": "Toneladas + Desperdicio",
  "Truck Loads": "Cargas de Camión",
  "Total Asphalt": "Asfalto Total",
  "Binder": "Ligante",
  "Aggregate in Mix": "Agregado en la Mezcla",
  "Base Tons (no waste)": "Toneladas Base (sin desperdicio)",
  "CY + Waste": "YD³ + Desperdicio",
  "Mixer Loads": "Cargas del Mezclador",
  "Coarse Aggregate": "Agregado Grueso",
  "Fine Aggregate": "Agregado Fino",
  "Adjusted Qty": "Cant. Ajustada",
  "Qty in Truck Unit": "Cant. en Unidad del Camión",
  "Partial Remaining": "Remanente Parcial",
  "Difference": "Diferencia",
  "Yield %": "Rendimiento %",
  "Overrun": "Exceso",
  "Underrun": "Faltante",
  "Recommended Order": "Orden Recomendada",
  "Result": "Resultado",
  "Formula": "Fórmula",
  "Density used": "Densidad usada",

  // Actions
  "Calculate": "Calcular",
  "Reset": "Restablecer",
  "Save Calculation": "Guardar Cálculo",
  "Saved": "Guardado",
  "Saved.": "Guardado.",
  "Calculate first, then save.": "Calcule primero, luego guarde.",
  "Could not save. Try again.": "No se pudo guardar. Intente de nuevo.",

  // Validation
  "Check your inputs — required values must be greater than 0.":
    "Revise los valores — los campos obligatorios deben ser mayores que 0.",
  "Length must be greater than 0.": "El largo debe ser mayor que 0.",
  "Width must be greater than 0.": "El ancho debe ser mayor que 0.",
  "Thickness must be greater than 0.": "El espesor debe ser mayor que 0.",
  "Density must be greater than 0.": "La densidad debe ser mayor que 0.",
  "Truck capacity must be greater than 0.": "La capacidad del camión debe ser mayor que 0.",
  "Quantity must be greater than 0.": "La cantidad debe ser mayor que 0.",
  "Enter a quantity greater than 0.": "Ingrese una cantidad mayor que 0.",
  "Density required for unit conversion.": "Se requiere densidad para la conversión de unidades.",
  "Planned must be greater than 0.": "El valor planeado debe ser mayor que 0.",
  "Actual must be 0 or greater.": "El valor real debe ser 0 o mayor.",

  // Disclaimer
  "Calculations are estimates for planning purposes only. Actual quantities may vary based on field conditions, material density, moisture, compaction, yield, mix design, waste, and project specifications.":
    "Los cálculos son estimaciones para fines de planificación únicamente. Las cantidades reales pueden variar según las condiciones del terreno, la densidad del material, humedad, compactación, rendimiento, diseño de mezcla, desperdicio y especificaciones del proyecto.",

  // ============================================================
  // QA/QC INSPECTIONS — checklist labels, section titles, helper text,
  // validation messages, button labels.  Added 2026-05-03 to fix the
  // "85% translates" bug where checklist rows + Pass/Fail/N/A buttons
  // stayed in English on ES. All three forms (concrete-form, rebar,
  // subcontractor-work) draw from this dict via t(item.label).
  // ============================================================

  // Section titles
  "Job": "Obra",
  "Subcontractor / Crew": "Subcontratista / Cuadrilla",
  "Inspection": "Inspección",
  "Concrete Placement": "Vaciado de Concreto",
  "Required for every concrete-form inspection.":
    "Requerido en cada inspección de formaleta de concreto.",
  "Checklist": "Lista de Verificación",
  "Notes & Corrective Action": "Notas y Acción Correctiva",
  "Photos": "Fotos",
  "Sign-Off": "Firma",

  // Field labels
  "Location": "Ubicación",
  "Project Manager": "Gerente de Proyecto",
  "Auto-filled from job": "Llenado automático desde la obra",
  "Subcontractor": "Subcontratista",
  "Search or add a subcontractor / vendor…":
    "Buscar o agregar un subcontratista / proveedor…",
  "Crew / Company": "Cuadrilla / Empresa",
  "Date": "Fecha",
  "Time": "Hora",
  "Inspector Name": "Nombre del Inspector",
  "Work Area / Station": "Área de Trabajo / Estación",
  "Work Activity": "Actividad de Trabajo",
  "Weather / Site Conditions": "Clima / Condiciones del Sitio",
  "e.g. 78°F, clear, light wind": "ej. 78°F, despejado, viento ligero",
  "Mix Design": "Diseño de Mezcla",
  "e.g. 4000 PSI Class IV": "ej. 4000 PSI Clase IV",
  "Yards Ordered (CY)": "Yardas Pedidas (CY)",
  "Concrete Vendor": "Proveedor de Concreto",
  "Search or add the concrete supplier…":
    "Buscar o agregar el proveedor de concreto…",
  "Inspection Notes / Description": "Notas de Inspección / Descripción",
  "Deficiencies": "Deficiencias",
  "Corrective Actions Required": "Acciones Correctivas Requeridas",
  "Upload at least 4 photos of the work area.":
    "Suba al menos 4 fotos del área de trabajo.",
  "Uploaded:": "Subidas:",
  "min 4 required": "mín. 4 requeridas",
  "Need 4 photos to submit": "Necesita 4 fotos para enviar",
  "Need": "Necesita",
  "photos to submit": "fotos para enviar",
  "Photo required": "Foto requerida",
  "Add at least 1 photo to submit": "Agregue al menos 1 foto para enviar",
  "Search jobs…": "Buscar trabajos…",
  "Job Photos": "Fotos de Trabajo",
  "All photos by job & week": "Todas las fotos por trabajo y semana",
  "Failed to load photos": "Error al cargar fotos",
  "Search jobs / submitter…": "Buscar trabajos / autor…",
  "All sources": "Todas las fuentes",
  "Daily Reports": "Reportes Diarios",
  "Site Inspections": "Inspecciones de Sitio",
  "QA/QC": "QA/QC",
  "Total": "Total",
  "No photos yet — submit a Daily Report, Site Inspection, or QA/QC to populate.":
    "Aún no hay fotos — envíe un Reporte Diario, Inspección de Sitio o QA/QC.",
  "No photos match your filter.": "Ninguna foto coincide con su filtro.",
  "Week of": "Semana de",
  "photos": "fotos",
  "Select all week": "Seleccionar toda la semana",
  "Deselect week": "Deseleccionar semana",
  "Selected": "Seleccionadas",
  "Clear": "Limpiar",
  "Email": "Correo",
  "Download ZIP": "Descargar ZIP",
  "Re-index": "Re-indexar",
  "Re-indexed {n} photos.": "Re-indexadas {n} fotos.",
  "Re-index failed": "Re-indexar falló",
  "Downloaded {n} photos.": "Descargadas {n} fotos.",
  "Download failed": "Descarga falló",
  "Emailed {n} photos.": "Enviadas {n} fotos por correo.",
  "Email failed": "Envío de correo falló",
  "Enter a valid email": "Ingrese un correo válido",
  "Recipient email": "Correo del destinatario",
  "Subject (optional)": "Asunto (opcional)",
  "Note (optional)": "Nota (opcional)",
  "Note: emails capped at 25MB. For larger packets use Download ZIP.":
    "Nota: los correos están limitados a 25MB. Para paquetes más grandes use Descargar ZIP.",
  "Cancel": "Cancelar",
  "Send": "Enviar",
  "PM Portal": "Portal PM",
  "Admin": "Admin",
  "Clear search": "Borrar búsqueda",
  "Expand All": "Expandir Todo",
  "Collapse All": "Colapsar Todo",
  "Last activity:": "Última actividad:",
  "No jobs match": "Ningún trabajo coincide",
  "No records yet.": "Aún no hay registros.",
  "(No Job)": "(Sin Trabajo)",
  "FAIL needs photo": "FALLA necesita foto",
  "FAILs need photos": "FALLAS necesitan fotos",
  "FAIL needs description": "FALLA necesita descripción",
  "FAILs need descriptions": "FALLAS necesitan descripciones",
  "Complete FAIL items to submit": "Complete las FALLAS para enviar",
  "Fix FAILs": "Arreglar FALLAS",
  "Photo Documentation": "Documentación Fotográfica",
  "Add": "Agregue",
  "more photo to submit": "foto más para enviar",
  "more photos to submit": "fotos más para enviar",
  "Inspector Signature": "Firma del Inspector",
  "Sub. Rep. Name (optional)": "Nombre del Rep. del Sub. (opcional)",
  "Sub. Rep. Signature (optional)": "Firma del Rep. del Sub. (opcional)",

  // Helper text + validation
  "Mark each item Pass, Fail, or N/A. Fails require a note.":
    "Marque cada punto Cumple, No Cumple, o N/A. Los No Cumple requieren una nota.",
  "Deficiency note (required for Fail)":
    "Nota de deficiencia (requerida para No Cumple)",
  "One or more items failed. Document deficiencies and corrective actions before submitting.":
    "Uno o más puntos no cumplen. Documente las deficiencias y acciones correctivas antes de enviar.",
  "Select a job.": "Seleccione una obra.",
  "Enter the work location.": "Ingrese la ubicación del trabajo.",
  "Work Area / Station required.": "Área de Trabajo / Estación requerida.",
  "Inspector name required.": "Nombre del Inspector requerido.",
  "Inspection notes required.": "Notas de Inspección requeridas.",
  "Minimum 4 photos required.": "Se requieren mínimo 4 fotos.",
  "Inspector signature required.": "Firma del Inspector requerida.",
  "Every Fail item needs a deficiency note.":
    "Cada punto No Cumple necesita una nota de deficiencia.",
  "Mix Design required.": "Diseño de Mezcla requerido.",
  "Yards Ordered required.": "Yardas Pedidas requeridas.",
  "Concrete Vendor required.": "Proveedor de Concreto requerido.",
  "Translating to English…": "Traduciendo al inglés…",
  "Submitted. Routing to assigned PM…":
    "Enviado. Enviando al Gerente de Proyecto asignado…",
  "Could not submit. Try again.":
    "No se pudo enviar. Intente de nuevo.",
  "Submit Inspection": "Enviar Inspección",
  "Submitting…": "Enviando…",
  "Use GPS": "Usar GPS",
  "Location captured from GPS": "Ubicación capturada por GPS",
  "Got GPS coordinates, but couldn't look up address":
    "Coordenadas GPS obtenidas, pero no se pudo encontrar la dirección",
  "Could not get GPS location": "No se pudo obtener la ubicación GPS",

  // ----------------------------------------------------------------
  // Concrete-Form inspection checklist labels
  // ----------------------------------------------------------------
  "Correct job selected": "Obra correcta seleccionada",
  "Correct location / station": "Ubicación / estación correcta",
  "Formwork installed per plans": "Encofrado instalado según planos",
  "Line and grade checked": "Línea y nivel verificados",
  "Dimensions verified": "Dimensiones verificadas",
  "Elevation checked": "Elevación verificada",
  "Forms braced and secured": "Formaletas arriostradas y aseguradas",
  "Forms clean and free of debris":
    "Formaletas limpias y libres de escombros",
  "Chamfer / keyway / blockouts installed where required":
    "Chaflán / llave / huecos instalados donde se requiere",
  "Expansion / construction joints installed where required":
    "Juntas de expansión / construcción instaladas donde se requiere",
  "Embedded items / sleeves / inserts verified":
    "Embebidos / camisas / insertos verificados",
  "Access and pour area ready": "Acceso y área de vaciado listos",
  "Safety / access around formwork acceptable":
    "Seguridad / acceso alrededor del encofrado aceptable",

  // ----------------------------------------------------------------
  // Rebar inspection checklist labels
  // ----------------------------------------------------------------
  "Rebar installed per plans": "Acero de refuerzo instalado según planos",
  "Bar size verified": "Diámetro de barra verificado",
  "Bar spacing verified": "Separación de barras verificada",
  "Bar quantity verified": "Cantidad de barras verificada",
  "Bar lap lengths verified": "Longitud de traslape verificada",
  "Tie spacing acceptable": "Separación de amarres aceptable",
  "Chairs / supports installed": "Sillas / soportes instalados",
  "Required concrete cover verified":
    "Recubrimiento de concreto requerido verificado",
  "Dowels / embeds / anchor bolts checked":
    "Pasadores / embebidos / pernos de anclaje verificados",
  "Rebar clean and free of mud, oil, or debris":
    "Acero limpio y libre de lodo, aceite o escombros",
  "Openings / blockouts verified": "Aberturas / huecos verificados",
  "Inspection ready for concrete placement":
    "Inspección lista para vaciado de concreto",

  // ----------------------------------------------------------------
  // Subcontractor work inspection checklist labels
  // ----------------------------------------------------------------
  "Work matches plans/specifications":
    "El trabajo coincide con planos / especificaciones",
  "Work area safe and accessible": "Área de trabajo segura y accesible",
  "Subcontractor manpower adequate":
    "Personal del subcontratista adecuado",
  "Equipment / materials appropriate": "Equipo / materiales apropiados",
  "Quality of workmanship acceptable":
    "Calidad de la mano de obra aceptable",
  "Layout / line / grade acceptable if applicable":
    "Trazo / línea / nivel aceptables si aplica",
  "Materials appear correct": "Los materiales parecen correctos",
  "Required permits / approvals in place if applicable":
    "Permisos / aprobaciones requeridos vigentes si aplica",
  "Work area cleaned up": "Área de trabajo limpia",
  "Rework required": "Se requiere re-trabajo",
  "Follow-up inspection required": "Se requiere inspección de seguimiento",

  // QA/QC navigation labels
  "QA / QC": "QA / QC",

  // QA/QC view-page extras (read-only inspection summary + KV labels)
  "Inspection Summary": "Resumen de Inspección",
  "Pass Items": "Cumple",
  "Fail Items": "No Cumple",
  "N/A Items": "N/A",
  "Project Number": "Número de Proyecto",
  "Client": "Cliente",
  "Weather": "Clima",
  "item(s) failed inspection": "elemento(s) no cumplen",
  "See deficiencies below.": "Vea las deficiencias abajo.",
  "Subcontractor Rep": "Rep. del Subcontratista",

  // ── Safety Forms (Issuance + Use & Care Training + Check-In) ─────
  "Safety Forms": "Formularios de Seguridad",
  "Safety Department": "Departamento de Seguridad",
  "Welcome to Safety Forms": "Bienvenido a Formularios de Seguridad",
  "Equipment Issuance and Use & Care Training. Password-gated for the Safety Department.":
    "Emisión de Equipo y Capacitación de Uso y Cuidado. Acceso por contraseña para el Departamento de Seguridad.",

  // ── iter322 / 323 / 324 · Safety Portal Ownership + Accountability ─────
  // Strings added when the Safety Portal absorbed Safety Forms ownership
  // and gained the Equipment & PPE Accountability review surface. Keys
  // are exact English UI strings — translations follow the platform's
  // operational, field-readable voice (concise, direct, non-corporate).
  "Equipment & PPE Accountability":
    "Responsabilidad de Equipo y PPE",
  "Equipment Issuance & Accountability + Use & Care Training documentation — open from the Safety Portal.":
    "Emisión y Responsabilidad de Equipo + Capacitación de Uso y Cuidado — disponible desde el Portal de Seguridad.",
  "Review every Equipment Issuance and Use & Care Training submission — per-employee chain of custody, returns, damages, and chargebacks.":
    "Revise cada emisión de equipo y capacitación — cadena de custodia por empleado, devoluciones, daños y cargos.",
  "Every Equipment Issuance and Use & Care Training record filed through Safety Forms. Filter by employee, project, or date — drill in for the full PDF and check-in/return status.":
    "Cada registro de Emisión de Equipo y Capacitación filtrado por empleado, proyecto o fecha — abra para ver el PDF y el estado de devolución.",
  "Safety Review": "Revisión de Seguridad",
  "Safety Portal": "Portal de Seguridad",
  "Safety Portal Ownership": "Propiedad del Portal de Seguridad",
  "Safety Forms are now owned by the Safety Portal. Sign in there for the full review experience.":
    "Los Formularios de Seguridad ahora pertenecen al Portal de Seguridad. Inicie sesión allí para la experiencia completa de revisión.",
  "Go to Safety Portal sign-in →": "Ir al inicio de sesión del Portal de Seguridad →",
  "Currently Issued": "Actualmente Emitido",
  "Aging (>90d)": "Vencido (>90d)",
  "Serialized PPE — consumables excluded":
    "PPE Serializado — consumibles excluidos",
  "Search employee, project, instructor…":
    "Buscar empleado, proyecto, instructor…",
  "Employee filter": "Filtro de Empleado",
  "Instructor": "Instructor",
  "Training Type": "Tipo de Capacitación",
  "No records match these filters.":
    "Ningún registro coincide con estos filtros.",
  "records shown": "registros mostrados",
  "Failed to load Safety Forms records":
    "No se pudieron cargar los registros de Formularios de Seguridad",
  "issued": "emitido",
  "returned": "devuelto",
  "damaged": "dañado",
  "lost": "perdido",
  "Aging accountability item": "Equipo de responsabilidad vencido",
  "90d+": "90d+",
  "aging": "vencido",
  "NEW SITE INSPECTION": "NUEVA INSPECCIÓN DE SITIO",
  // iter322 — auth continuity banner copy
  "Safety, Admin, or PM login required":
    "Se requiere inicio de sesión de Seguridad, Admin o PM",

  // ── iter327 · Hub capability-forward voice (Homepage Phase D) ─────
  // Capability-forward tile copy that communicates operational power
  // instead of generic department names. Field-readable Spanish.
  "End-of-day reports, safety enforcement, equipment tracking, quality control, and complete documentation — captured in the field, routed automatically, and stored in one operational system.":
    "Reportes de fin de día, cumplimiento de seguridad, control de equipo, control de calidad y documentación completa — capturado en campo, ruteado automáticamente y archivado en un solo sistema operativo.",
  "What every crew on site does today.":
    "Lo que cada cuadrilla en el sitio hace hoy.",
  "File end-of-day reports, log equipment walk-arounds, and capture crew, weather, and production from the job site.":
    "Presente reportes de fin de día, registre revisiones de equipo, y capture cuadrilla, clima y producción desde la obra.",
  "Run quality inspections on concrete, asphalt, rebar, and subcontractor work — signed, photographed, routed, and archived.":
    "Ejecute inspecciones de calidad en concreto, asfalto, refuerzo y trabajo de subcontratistas — firmadas, fotografiadas, ruteadas y archivadas.",
  "File toolbox talks, JHAs, incident reports, and trench-box plans — directly from the truck or trailer.":
    "Presente charlas de seguridad, JHAs, reportes de incidentes y planes de trincheras — directamente desde la camioneta o el remolque.",
  "For foremen, supervisors, and superintendents running the work.":
    "Para capataces, supervisores y superintendentes que dirigen el trabajo.",
  "Track crew accountability, employee documentation, equipment custody, recognition, and workforce decisions.":
    "Registre responsabilidad de cuadrilla, documentación de empleados, custodia de equipo, reconocimiento y decisiones de personal.",
  "Manage jobs, PO requests, daily reports, inspections, photos, and project compliance.":
    "Administre obras, solicitudes de OC, reportes diarios, inspecciones, fotos y cumplimiento del proyecto.",
  "Run the mechanic queue — repairs, parts, PMs, and fleet readiness.":
    "Maneje la cola del taller — reparaciones, refacciones, mantenimientos preventivos y disponibilidad de flota.",
  "Employee records, onboarding, payroll cross-checks, and workforce documentation.":
    "Expedientes de empleados, inducción, verificación de nómina y documentación de personal.",
  "Incidents, audits, inspections, PPE accountability, training, and corrective actions.":
    "Incidentes, auditorías, inspecciones, responsabilidad de PPE, capacitación y acciones correctivas.",
  "Equipment movement, DVIRs, transfers, utilization, and operational readiness.":
    "Movimiento de equipo, DVIRs, transferencias, utilización y disponibilidad operativa.",
  "System administration — users, roles, integrations, audit logs, and exports.":
    "Administración del sistema — usuarios, roles, integraciones, registros de auditoría y exportaciones.",
  "Sign-in required. Showing the portals you're authorized for.":
    "Inicio de sesión requerido. Mostrando los portales para los que está autorizado.",
  "Sign-in required. Office, mechanic, HR, Safety, Dispatch, and Admin operations.":
    "Inicio de sesión requerido. Operaciones de oficina, taller, RR.HH., Seguridad, Despacho y Administración.",
  "Operator guides, training, and contact info — always available, no sign-in required.":
    "Guías para operadores, capacitación e información de contacto — siempre disponibles, sin inicio de sesión.",
  "Office phone, address, and after-hours operations contact.":
    "Teléfono de oficina, dirección y contacto operativo después de horas.",
  "Role-based operator playbooks, portal walk-throughs, and field cheat references.":
    "Guías por rol, recorridos de portales y referencias rápidas de campo.",
  "The one-page operations summary pinned in every site trailer.":
    "El resumen operativo de una página fijado en cada remolque de obra.",

  "Open Forms": "Abrir Formularios",
  "Equipment Issuance": "Emisión de Equipo",
  "Use & Care Training": "Capacitación de Uso y Cuidado",
  "Issue safety equipment to employees with full chain of custody — itemized inventory, condition, photos, and dual signatures.":
    "Emita equipo de seguridad con cadena de custodia completa — inventario detallado, condición, fotos y firmas duales.",
  "Document equipment training — initial, refresher, or retraining — with topics covered and instructor sign-off.":
    "Documente capacitación — inicial, repaso o reentrenamiento — con temas cubiertos y firma del instructor.",
  "Issue equipment with full accountability and document use & care training — every submission emails a clean PDF to safety@mascigc.com.":
    "Emita equipo con responsabilidad total y documente la capacitación — cada envío envía un PDF al correo safety@mascigc.com.",
  "MASCI · Safety Department": "MASCI · Departamento de Seguridad",
  "Start Form": "Iniciar Formulario",
  "Safety Equipment Issuance & Accountability":
    "Emisión y Responsabilidad de Equipo de Seguridad",
  "Employee": "Empleado",
  "Employee Name": "Nombre del Empleado",
  "Employee ID (optional)": "ID del Empleado (opcional)",
  "Issued By": "Emitido Por",
  "Project / Location": "Proyecto / Ubicación",
  "Date Issued": "Fecha de Emisión",
  "Equipment": "Equipo",
  "Add every item being issued. Other allows a write-in description.":
    "Agregue cada artículo emitido. La opción 'Otro' permite escribir una descripción.",
  "Item Type": "Tipo de Artículo",
  "Specify Other": "Especificar Otro",
  "Qty": "Cant.",
  "Unit $": "$ Unitario",
  "auto": "auto",
  "Asset / Serial #": "Activo / Serial #",
  "Line total": "Total de línea",
  "Add Item": "Agregar Artículo",
  "Total Issued Value": "Valor Total Emitido",
  "Condition at Issuance": "Condición al Emitir",
  "New / Good auto-prices from the catalog. Fair / Damaged unlocks Unit $ so you can enter a depreciated value.":
    "Nuevo / Bueno se cotiza automáticamente desde el catálogo. Regular / Dañado desbloquea $ Unitario para ingresar un valor depreciado.",
  "Damage Note": "Nota de Daño",
  "Describe the damage": "Describa el daño",
  "Photos": "Fotos",
  "Required — capture serial number and/or condition.":
    "Requerido — capture el número de serie y/o la condición.",
  "Uploaded:": "Subidas:",
  "min 1 required": "mín. 1 requerida",
  "Acknowledgment & Legal": "Reconocimiento y Términos Legales",
  "I acknowledge that all issued equipment remains the property of MASCI General Contractors Inc. I agree to use all equipment in accordance with manufacturer guidelines, company policy, and applicable OSHA safety requirements.":
    "Reconozco que todo el equipo emitido sigue siendo propiedad de MASCI General Contractors Inc. Acepto utilizar todo el equipo conforme a las directrices del fabricante, las políticas de la empresa y los requisitos de seguridad de OSHA aplicables.",
  "I understand that I am responsible for the proper use, care, maintenance, and return of all issued equipment. I further understand that I am responsible for promptly reporting any loss, damage, or malfunction.\n\nEquipment that is lost, stolen, misplaced, or damaged due to negligence, misuse, or failure to follow manufacturer guidelines, company policy, or OSHA requirements may result in financial responsibility for the reasonable replacement cost or fair market value of the equipment, to the extent permitted by law.\n\nI understand that I will not be held responsible for normal wear and tear resulting from proper use.\n\nAny reimbursement or payroll deduction will be handled in accordance with applicable Florida law and the Fair Labor Standards Act (FLSA), and will only occur with proper written authorization where required.\n\nI understand that failure to follow these requirements may also result in disciplinary action, up to and including termination, in accordance with company policy.":
    "Entiendo que soy responsable del uso adecuado, cuidado, mantenimiento y devolución de todo el equipo emitido. Además, entiendo que soy responsable de reportar de manera oportuna cualquier pérdida, daño o mal funcionamiento.\n\nEl equipo que sea perdido, robado, extraviado o dañado debido a negligencia, mal uso, o por no seguir las directrices del fabricante, las políticas de la empresa o los requisitos de OSHA, puede resultar en responsabilidad financiera por el costo razonable de reemplazo o el valor justo de mercado del equipo, en la medida en que lo permita la ley.\n\nEntiendo que no se me responsabilizará por el desgaste normal resultante del uso adecuado.\n\nCualquier reembolso o deducción de nómina se manejará de acuerdo con la ley aplicable de Florida y la Ley de Normas Razonables de Trabajo (FLSA), y solo ocurrirá con la autorización escrita correspondiente cuando sea requerida.\n\nEntiendo que el incumplimiento de estos requisitos también puede resultar en acción disciplinaria, hasta e incluyendo la terminación del empleo, conforme a las políticas de la empresa.",
  "I acknowledge receipt of the listed equipment and accept responsibility.":
    "Reconozco la recepción del equipo listado y acepto la responsabilidad.",
  "Email a Copy to Employee (optional)": "Enviar Copia al Empleado (opcional)",
  "If provided, the employee will receive a copy of the signed PDF along with the Safety Department.":
    "Si se proporciona, el empleado recibirá una copia del PDF firmado junto con el Departamento de Seguridad.",
  "Employee Email": "Correo del Empleado",
  "Signatures": "Firmas",
  "Employee Signature": "Firma del Empleado",
  "Supervisor Signature": "Firma del Supervisor",
  "Auto-emails Safety dept on submit":
    "Envía correo automáticamente al Dept. de Seguridad",
  "Submitting…": "Enviando…",
  "Submit & Email PDF": "Enviar y Mandar PDF",
  "Submitted — PDF emailed to Safety": "Enviado — PDF enviado a Seguridad",
  "Could not submit": "No se pudo enviar",
  "Translating to English…": "Traduciendo al inglés…",
  "Type to filter…": "Escriba para filtrar…",
  "Select item": "Seleccione artículo",
  "Select equipment": "Seleccione equipo",
  "Employee name required": "Nombre del empleado requerido",
  "Issued By required": "Emitido Por requerido",
  "Add at least one item": "Agregue al menos un artículo",
  "Each item needs a type": "Cada artículo necesita un tipo",
  "Specify the 'Other' item": "Especifique el artículo 'Otro'",
  "Quantity must be > 0": "La cantidad debe ser mayor que 0",
  "Damage note required when condition is Damaged":
    "Se requiere nota cuando la condición es Dañado",
  "At least 1 photo required": "Se requiere al menos 1 foto",
  "You must acknowledge the terms": "Debe reconocer los términos",
  "Employee signature required": "Firma del empleado requerida",
  "Supervisor signature required": "Firma del supervisor requerida",
  "Could not get GPS location": "No se pudo obtener la ubicación GPS",
  "Equipment Use & Care Training Documentation":
    "Documentación de Capacitación de Uso y Cuidado de Equipo",
  "Training Information": "Información de Capacitación",
  "Training Date": "Fecha de Capacitación",
  "Instructor Name": "Nombre del Instructor",
  "Training Location": "Ubicación de Capacitación",
  "Equipment Trained": "Equipo Entrenado",
  "Add every piece of equipment covered in this session.":
    "Agregue cada equipo cubierto en esta sesión.",
  "Training Type": "Tipo de Capacitación",
  "Mfr / Model": "Fabricante / Modelo",
  "Notes": "Notas",
  "Add Equipment": "Agregar Equipo",
  "Topics Covered": "Temas Cubiertos",
  "Select every topic discussed during training.":
    "Seleccione cada tema discutido durante la capacitación.",
  "Proper Use": "Uso Adecuado",
  "Inspection Requirements": "Requisitos de Inspección",
  "Maintenance": "Mantenimiento",
  "Storage": "Almacenamiento",
  "Limitations of Equipment": "Limitaciones del Equipo",
  "OSHA Compliance": "Cumplimiento de OSHA",
  "Other": "Otro",
  "Specify Other Topic": "Especificar Otro Tema",
  "Acknowledgment": "Reconocimiento",
  "I acknowledge that I have received training on the equipment listed above and understand proper use, inspection, and safety requirements.":
    "Reconozco haber recibido capacitación sobre el equipo listado y entiendo el uso adecuado, la inspección y los requisitos de seguridad.",
  "Instructor Signature": "Firma del Instructor",
  "Instructor name required": "Nombre del instructor requerido",
  "Training date required": "Fecha de capacitación requerida",
  "Add at least one equipment item": "Agregue al menos un artículo de equipo",
  "Each item needs equipment type": "Cada artículo necesita un tipo de equipo",
  "Specify the 'Other' equipment": "Especifique el equipo 'Otro'",
  "Each item needs training type": "Cada artículo necesita un tipo de capacitación",
  "Select at least one topic covered": "Seleccione al menos un tema cubierto",
  "Specify 'Other' topic": "Especifique el tema 'Otro'",
  "Acknowledgment required": "Reconocimiento requerido",
  "Safety Forms · Check-In": "Formularios de Seguridad · Recepción",
  "Equipment Check-In & Return": "Recepción y Devolución de Equipo",
  "Reviewing": "Revisando",
  "issued": "emitido",
  "Check-In": "Recepción",
  "Date Returned": "Fecha de Devolución",
  "Received By": "Recibido Por",
  "Notes (optional)": "Notas (opcional)",
  "Per-Item Return": "Devolución por Artículo",
  "Tap a status pill for each item. Notes required for Damaged or Lost.":
    "Toque un estado para cada artículo. Notas requeridas para Dañado o Perdido.",
  "Issued": "Emitido",
  "Chargeback": "Cargo",
  "Returned OK": "Devuelto OK",
  "Damaged": "Dañado",
  "Lost / Not Returned": "Perdido / No Devuelto",
  "Qty Returned (of {n})": "Cant. Devuelta (de {n})",
  "Any not-returned units will be billed as Lost.":
    "Las unidades no devueltas se cobrarán como Perdidas.",
  "Damage description": "Descripción del daño",
  "Lost / not-returned reason": "Razón de pérdida / no devolución",
  "Describe what happened": "Describa lo que pasó",
  "Total Chargeback": "Cargo Total",
  "Lost": "Perdido",
  "Both parties confirm the above return outcome is accurate and complete.":
    "Ambas partes confirman que el resultado de la devolución es preciso y completo.",
  "Save Check-In & Email PDF": "Guardar Recepción y Mandar PDF",
  "Check-in saved — PDF emailed to Safety":
    "Recepción guardada — PDF enviado a Seguridad",
  "This issuance has already been checked in.":
    "Esta emisión ya ha sido recibida.",
  "Each item needs a status": "Cada artículo necesita un estado",
  "Note required for Damaged or Lost items":
    "Nota requerida para artículos Dañados o Perdidos",
  "Returned qty must be between 0 and issued qty":
    "La cantidad devuelta debe estar entre 0 y la cantidad emitida",
  "Pre-filled from the original issuance. Edit or clear to change.":
    "Pre-llenado desde la emisión original. Edite o borre para cambiar.",
  "If provided, the employee will receive a copy of the signed receipt along with the Safety Department.":
    "Si se proporciona, el empleado recibirá una copia del recibo firmado junto con el Departamento de Seguridad.",
  "Submitted": "Enviado",
  "Equipment Out": "Equipo Fuera",
  "When this gear comes back, log the check-in to close the loop.":
    "Cuando este equipo regrese, registre la recepción para cerrar el ciclo.",
  "Start Check-In / Return": "Iniciar Recepción / Devolución",
  "Check-In Receipt": "Recibo de Recepción",
  "Received by": "Recibido por",
  "Returned": "Devuelto",
  "Item": "Artículo",
  "Mfr/Model": "Fabricante/Modelo",
  "Asset/Serial": "Activo/Serial",
  "Line $": "Línea $",
  "Form Ref": "Ref. Formulario",
  "Download Return PDF": "Descargar PDF de Devolución",
  "Could not download PDF": "No se pudo descargar el PDF",
  "Confidential": "Confidencial",
  "Generated": "Generado",
  "Not found": "No encontrado",
  "Use GPS": "Usar GPS",
  "Issuance": "Emisión",
  "Equipment Trained On": "Equipo Entrenado",

  // ---- Field Leadership module ------------------------------------------
  "Field Leadership": "Liderazgo de Campo",
  "Restricted": "Restringido",
  "Restricted · Crew Documentation": "Restringido · Documentación de Cuadrilla",
  "Restricted Form": "Formulario Restringido",
  "This section is restricted to MASCI field supervisors, foremen, superintendents, PMs, Safety, and Admin. Enter the leadership password to continue.":
    "Esta sección está restringida a supervisores de campo, capataces, superintendentes, PMs, Seguridad y Administración de MASCI. Ingrese la contraseña de liderazgo para continuar.",
  "Leadership password": "Contraseña de Liderazgo",
  "Enter Field Leadership": "Entrar a Liderazgo de Campo",
  "Verifying…": "Verificando…",
  "Access granted": "Acceso concedido",
  "Incorrect password": "Contraseña incorrecta",
  "Back to Hub": "Volver al Hub",
  "Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management tools for MASCI field leadership.":
    "Responsabilidad de cuadrilla, documentación de empleados, responsabilidad de equipo, reconocimiento y herramientas de gestión de personal para el liderazgo de campo de MASCI.",
  "All forms must be factual, professional, and compliant with employment-documentation best practices.":
    "Todos los formularios deben ser objetivos, profesionales y cumplir con las mejores prácticas de documentación laboral.",
  "Records": "Registros",
  "Records & Submissions": "Registros y Envíos",
  "All Field Leadership submissions across every job.": "Todos los envíos de Liderazgo de Campo en cada trabajo.",
  "Submissions for jobs assigned to you.": "Envíos para los trabajos asignados a usted.",
  "Field Leadership · Records": "Liderazgo de Campo · Registros",
  "Sign Out": "Cerrar Sesión",
  "Existing Form": "Formulario Existente",
  "Open form →": "Abrir formulario →",
  "New entry →": "Nueva entrada →",
  "Admin Only": "Solo Admin",
  "Sign in as Admin to unlock": "Inicie sesión como Admin para desbloquear",
  "Admin Login Required": "Se Requiere Inicio de Sesión de Admin",
  "Supervisor Notes are restricted. Sign in as an Admin from the Hub.":
    "Las Notas del Supervisor están restringidas. Inicie sesión como Admin desde el Hub.",
  "Admin Login": "Iniciar Sesión como Admin",
  "← Back to Field Leadership": "← Volver a Liderazgo de Campo",

  // Form labels (10 forms + 1 link)
  "Employee Write-Up": "Amonestación de Empleado",
  "Verbal Coaching": "Asesoría Verbal",
  "Attendance / Tardy": "Asistencia / Tardanza",
  "Recognition / Reward": "Reconocimiento / Premio",
  "Equipment Checkout & Accountability": "Entrega de Equipo y Responsabilidad",
  "New Employee Evaluation": "Evaluación de Empleado Nuevo",
  "Crew Evaluation": "Evaluación de Cuadrilla",
  "Promotion Recommendation": "Recomendación de Ascenso",
  "Training Deficiency / Retraining": "Deficiencia de Capacitación / Recapacitación",
  "Supervisor Notes Log": "Registro de Notas del Supervisor",
  "Safety Equipment Issuance & Accountability": "Entrega de Equipo de Seguridad y Responsabilidad",

  // Form descriptions
  "Document formal disciplinary or corrective action.": "Documente acción disciplinaria o correctiva formal.",
  "Document a coaching conversation that is not a formal write-up.": "Documente una conversación de asesoría que no sea una amonestación formal.",
  "Document attendance-related issues factually.": "Documente problemas de asistencia de manera objetiva.",
  "Recognize an employee for safety, quality, teamwork, or leadership.": "Reconozca a un empleado por seguridad, calidad, trabajo en equipo o liderazgo.",
  "Track tools, vehicles, and equipment assigned to an employee.": "Rastree herramientas, vehículos y equipo asignado a un empleado.",
  "30 / 60 / 90-day evaluation for a new hire.": "Evaluación de 30 / 60 / 90 días para un nuevo empleado.",
  "Evaluate the entire crew on safety, production, quality, and communication.": "Evalúe a toda la cuadrilla en seguridad, producción, calidad y comunicación.",
  "Recommend an employee for promotion, raise, or leadership development.": "Recomiende a un empleado para ascenso, aumento o desarrollo de liderazgo.",
  "Document a training deficiency and assigned retraining.": "Documente una deficiencia de capacitación y la recapacitación asignada.",
  "Internal leadership documentation log — admin-restricted.": "Registro interno de documentación de liderazgo — restringido a administradores.",
  "Issue safety equipment to crew members and track accountability.": "Entregue equipo de seguridad a los miembros de la cuadrilla y rastree la responsabilidad.",

  // Form fields / common labels
  "Active Job": "Trabajo Activo",
  "Select a job…": "Seleccione un trabajo…",
  "Select an employee…": "Seleccione un empleado…",
  "Select…": "Seleccione…",
  "Employee": "Empleado",
  "Search employee by name…": "Buscar empleado por nombre…",
  "Add new employee": "Agregar nuevo empleado",
  "New employee name": "Nombre del nuevo empleado",
  "Employee added": "Empleado agregado",
  "Could not add employee": "No se pudo agregar empleado",
  "Add": "Agregar",
  "Cancel": "Cancelar",
  "Or type employee name (not in system)": "O escriba el nombre del empleado (no está en el sistema)",
  "Manual employee name": "Nombre manual del empleado",
  "Position": "Puesto",
  "Supervisor / Foreman / Superintendent": "Supervisor / Capataz / Superintendente",
  "Date / Time": "Fecha / Hora",
  "Location / Work Area": "Ubicación / Área de Trabajo",
  "Photos / Documents": "Fotos / Documentos",
  "(required if condition is Fair or Damaged)": "(requerido si la condición es Aceptable o Dañado)",
  "Employee signature acknowledges receipt of this document and does not necessarily indicate agreement with its contents.":
    "La firma del empleado reconoce la recepción de este documento y no necesariamente indica acuerdo con su contenido.",
  "Supervisor Signature": "Firma del Supervisor",
  "Employee Signature": "Firma del Empleado",
  "Employee Signature (Optional)": "Firma del Empleado (Opcional)",
  "Witness Signature": "Firma del Testigo",
  "Witness Name": "Nombre del Testigo",
  "Employee refused to sign": "El empleado se negó a firmar",
  "Submitting…": "Enviando…",
  "Submitted — assigned PM, jaymn, and safety have been notified.":
    "Enviado — el PM asignado, jaymn y seguridad han sido notificados.",
  "Submit failed": "El envío falló",
  "Supervisor name required": "Se requiere el nombre del supervisor",
  "Employee name required": "Se requiere el nombre del empleado",
  "is required": "es requerido",
  "Photos are required for the selected condition.": "Se requieren fotos para la condición seleccionada.",
  "Supervisor signature required": "Se requiere la firma del supervisor",
  "Employee signature OR refusal required": "Se requiere la firma del empleado O su negativa",
  "Witness name and signature required when employee refuses to sign":
    "Se requiere nombre y firma del testigo cuando el empleado se niega a firmar",

  // Records dashboard
  "Total": "Total",
  "Job # or Name": "Trabajo # o Nombre",
  "Search": "Buscar",
  "Search…": "Buscar…",
  "Clear": "Limpiar",
  "Export CSV": "Exportar CSV",
  "Could not load records": "No se pudieron cargar los registros",
  "Could not export CSV": "No se pudo exportar el CSV",
  "Form": "Formulario",
  "Job": "Trabajo",
  "Date": "Fecha",
  "Supervisor": "Supervisor",
  "Actions": "Acciones",
  "Loading…": "Cargando…",
  "No records yet for the current filters.": "Aún no hay registros para los filtros actuales.",
  "Permanently archive this record?": "¿Archivar permanentemente este registro?",
  "Archived": "Archivado",
  "Could not archive": "No se pudo archivar",

  // View page
  "Form Type": "Tipo de Formulario",
  "Assigned PM": "PM Asignado",
  "Submitted via": "Enviado por",
  "Language": "Idioma",
  "Summary": "Resumen",
  "Details": "Detalles",
  "Photos": "Fotos",
  "Signatures": "Firmas",
  "Employee Refused": "El Empleado se Negó",
  "Witness": "Testigo",
  "Download PDF": "Descargar PDF",
  "Could not load record": "No se pudo cargar el registro",
  "Could not open PDF": "No se pudo abrir el PDF",
  "Quality Assurance · Quality Control": "Aseguramiento de Calidad · Control de Calidad",
  "QA / QC": "QA / QC",
  "QA / QC Inspections": "Inspecciones de QA / QC",
  "MASCI · QA/QC": "MASCI · QA/QC",
  "Open Form": "Abrir Formulario",
  "None": "Ninguno",
  "Location": "Ubicación",
  "Client": "Cliente",
  "Concrete Form Inspection": "Inspección de Formaleta de Concreto",
  "Rebar Inspection": "Inspección de Acero de Refuerzo",
  "Subcontractor Work Inspection": "Inspección de Trabajo de Subcontratista",
  "Document inspection of concrete formwork before placement.": "Documente la inspección de la formaleta de concreto antes de la colocación.",
  "Document reinforcing steel inspection before concrete placement.": "Documente la inspección del acero de refuerzo antes de la colocación del concreto.",
  "General QA/QC inspection form for any subcontractor work onsite.": "Formulario general de inspección de QA/QC para cualquier trabajo de subcontratista en el sitio.",

  // ---- CompanyInfoDialog ------------------------------------------------
  "Company Info": "Información de la Empresa",
  "Info": "Info",
  "Appears on the print/PDF footer of every safety report. Stored only on this device.":
    "Aparece en el pie de página impreso/PDF de cada informe de seguridad. Se guarda solo en este dispositivo.",
  "Appears on every printed report. Admin only — sign in as admin to make changes.":
    "Aparece en cada informe impreso. Solo Admin — inicie sesión como admin para hacer cambios.",
  "View only · Admin login required to edit": "Solo lectura · Inicio de sesión de Admin requerido para editar",
  "Call Office": "Llamar a la Oficina",
  "Company Name": "Nombre de la Empresa",
  "Street Address": "Dirección",
  "City, State, ZIP": "Ciudad, Estado, Código Postal",
  "Office Phone": "Teléfono de Oficina",
  "Email": "Correo Electrónico",
  "Website": "Sitio Web",
  "Close": "Cerrar",
  "Save": "Guardar",
  "Company info saved — appears on every printed report": "Información de la empresa guardada — aparece en cada informe impreso",

  // ---- Hub eyebrow / training hub additions -----------------------------
  "Hub": "Hub",
  "lessons": "lecciones",
  "Password required": "Contraseña requerida",
  "more…": "más…",
  "Open track →": "Abrir pista →",
  "Sign in →": "Iniciar sesión →",
  "Internal track — covers back-office workflows. Sign in as": "Pista interna — cubre flujos de trabajo internos. Inicie sesión como",
  "to see the lessons and packets.": "para ver las lecciones y paquetes.",
  "MASCI Training": "Capacitación MASCI",
  "Short, focused lessons for every role — Field Crews, Shop, Project Managers, and Admins. Written walk-throughs, printable cheat sheets, and video tutorials. Pick your track.":
    "Lecciones cortas y enfocadas para cada rol — Cuadrillas de Campo, Taller, Gerentes de Proyecto y Administradores. Guías escritas, hojas de referencia imprimibles y tutoriales en video. Elija su pista.",
  "Field Leadership Training": "Capacitación de Liderazgo de Campo",
  "Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management forms. For supervisors, foremen, and superintendents.":
    "Responsabilidad de cuadrilla, documentación de empleados, responsabilidad de equipo, reconocimiento y formularios de gestión de personal. Para supervisores, capataces y superintendentes.",

  // ---- Equipment Checkout / Catalog -------------------------------------
  "Equipment Issued": "Equipo Entregado",
  "Add each tool, vehicle, or asset issued. Search the catalog or add a custom item.":
    "Agregue cada herramienta, vehículo o activo entregado. Busque en el catálogo o agregue un artículo personalizado.",
  "Add Equipment": "Agregar Equipo",
  "Add Custom": "Agregar Personalizado",
  "No equipment added yet. Tap \"Add Equipment\" to issue the first item.":
    "Aún no se ha agregado equipo. Toque \"Agregar Equipo\" para entregar el primer artículo.",
  "Item": "Artículo",
  "Remove": "Quitar",
  "Equipment / Tool": "Equipo / Herramienta",
  "Search catalog or type custom name…": "Busque en el catálogo o escriba un nombre personalizado…",
  "Search equipment…": "Buscar equipo…",
  "No matches.": "Sin coincidencias.",
  "Or type custom equipment name": "O escriba un nombre personalizado de equipo",
  "Manufacturer / Make": "Fabricante / Marca",
  "Select manufacturer…": "Seleccione fabricante…",
  "Other / Custom": "Otro / Personalizado",
  "Custom manufacturer": "Fabricante personalizado",
  "Model": "Modelo",
  "Serial / Asset ID": "Serie / ID de Activo",
  "Quantity": "Cantidad",
  "Replacement $": "Reemplazo $",
  "Condition": "Condición",
  "Line Total": "Total de Línea",
  "Notes": "Notas",
  "Photos (optional)": "Fotos (opcional)",
  "Total Replacement Value Issued": "Valor Total de Reemplazo Entregado",
  "item": "artículo",
  "items": "artículos",
  "Add at least one equipment item": "Agregue al menos un artículo de equipo",
  "Every equipment item needs a name": "Cada artículo de equipo necesita un nombre",
  "Every equipment item needs a replacement value greater than zero": "Cada artículo necesita un valor de reemplazo mayor a cero",
  "Every equipment item needs a quantity": "Cada artículo necesita una cantidad",

  // Admin equipment catalog page
  "Admin": "Admin",
  "Field Leadership · Admin": "Liderazgo de Campo · Admin",
  "Equipment Catalog & Manufacturers": "Catálogo de Equipo y Fabricantes",
  "Manage the searchable equipment list and manufacturer dropdown used by the Equipment Checkout & Accountability form. Disable old items instead of deleting to preserve historical record references.":
    "Gestione la lista de equipo y el desplegable de fabricantes usado por el formulario de Entrega de Equipo y Responsabilidad. Deshabilite artículos antiguos en lugar de eliminarlos para preservar las referencias históricas.",
  "Equipment Catalog": "Catálogo de Equipo",
  "Refresh": "Actualizar",
  "Export Checkout CSV": "Exportar CSV de Entregas",
  "Add Item": "Agregar Artículo",
  "Search by name, make, or category…": "Buscar por nombre, marca o categoría…",
  "Default Make": "Marca Predeterminada",
  "Category": "Categoría",
  "Active": "Activo",
  "No items.": "Sin artículos.",
  "Disabled": "Deshabilitado",
  "Manufacturers": "Fabricantes",
  "Add Make": "Agregar Marca",
  "Disable": "Deshabilitar",
  "Enable": "Habilitar",
  "Edit": "Editar",
  "Edit Equipment": "Editar Equipo",
  "Add Equipment Item": "Agregar Artículo de Equipo",
  "Category (optional)": "Categoría (opcional)",
  "Active (visible in dropdown)": "Activo (visible en desplegable)",
  "Edit Manufacturer": "Editar Fabricante",
  "Add Manufacturer": "Agregar Fabricante",
  "Saved": "Guardado",
  "Save failed": "Error al guardar",
  "Could not load equipment catalog": "No se pudo cargar el catálogo de equipo",
  "Could not update": "No se pudo actualizar",
  "Name required": "Se requiere nombre",
  "Name": "Nombre",

  // ---- Stricter Equipment Checkout validation messages ----------------
  "Employee position is required": "Se requiere el puesto del empleado",
  "equipment name is required": "se requiere el nombre del equipo",
  "manufacturer is required": "se requiere el fabricante",
  "model is required": "se requiere el modelo",
  "serial / asset ID is required": "se requiere la serie / ID de activo",
  "quantity is required": "se requiere la cantidad",
  "replacement value is required": "se requiere el valor de reemplazo",
  "condition is required": "se requiere la condición",
  "at least 2 photos are required per item": "se requieren al menos 2 fotos por artículo",
  "Photos": "Fotos",
  "(Minimum 2 photos required)": "(Mínimo 2 fotos requeridas)",
  "Need": "Faltan",
  "more photo(s)": "foto(s) más",

  // ---- Equipment Return form ------------------------------------------
  "Equipment Return & Reconciliation": "Devolución y Reconciliación de Equipo",
  "Close the loop on issued equipment — scan or look up by serial/asset ID, document return condition with photos, auto-flag damage or loss against the original replacement value.":
    "Cierre el ciclo del equipo entregado — busque por serie/ID de activo, documente la condición de devolución con fotos, marque daños o pérdidas contra el valor de reemplazo original.",
  "Look Up by Serial / Asset ID": "Buscar por Serie / ID de Activo",
  "Scan or type the serial / asset ID stamped on the equipment to pull the original checkout record.":
    "Escanee o escriba la serie / ID de activo del equipo para abrir el registro original de entrega.",
  "e.g. RL200-789": "ej. RL200-789",
  "Searching…": "Buscando…",
  "Look Up": "Buscar",
  "Add Manual Entry": "Agregar Entrada Manual",
  "No items yet. Look up a serial or add a manual entry.": "Aún no hay artículos. Busque una serie o agregue una entrada manual.",
  "Loaded original checkout — record return condition + photos": "Entrega original cargada — registre la condición de devolución y fotos",
  "Lookup failed": "Búsqueda fallida",
  "No open checkout found for that serial": "No se encontró una entrega abierta para esa serie",
  "Enter a serial / asset ID to look up": "Ingrese una serie / ID de activo para buscar",
  "Look up at least one item by serial or add it manually": "Busque al menos un artículo por serie o agréguelo manualmente",
  "return condition is required": "se requiere la condición de devolución",
  "at least 2 return photos are required per item": "se requieren al menos 2 fotos de devolución por artículo",
  "Matched checkout": "Entrega coincidente",
  "Damage flagged": "Daño marcado",
  "Equipment": "Equipo",
  "Manufacturer": "Fabricante",
  "Qty": "Cant.",
  "Issued Cond.": "Cond. Entregada",
  "Return Condition": "Condición de Devolución",
  "Loss / Damage Amount": "Monto de Pérdida / Daño",
  "Defaults to full replacement": "Por defecto al reemplazo total",
  "Auto-zero unless damaged/lost": "Cero automático salvo dañado/perdido",
  "Return Notes": "Notas de Devolución",
  "Return Photos": "Fotos de Devolución",
  "Total Replacement Value": "Valor Total de Reemplazo",
  "Total Loss / Damage": "Pérdida / Daño Total",
  "Auto-flagged on return": "Marcado automáticamente al devolver",
  "Clean return — no damage": "Devolución limpia — sin daños",

  // ---- Field Leadership login screen (matches Admin/PM/Shop chrome) ----
  "Restricted Area": "Área Restringida",
  "Field Leadership Sign In": "Inicio de Sesión · Liderazgo de Campo",
  "Leadership Password": "Contraseña de Liderazgo",
  "Sign In": "Iniciar Sesión",
  "MASCI · Field Leadership · Restricted": "MASCI · Liderazgo de Campo · Restringido",

  // ---- Sub-hub + Field Leadership tile CTAs (iter106–iter108) ----------
  "Home": "Inicio",
  "New entry": "Nueva entrada",
  "Open form": "Abrir formulario",
  "Open Tools": "Abrir Herramientas",

  // ---- Public Time Off form (iter102 + iter110 bilingual) --------------
  "Public Form": "Formulario Público",
  "Link unavailable": "Enlace no disponible",
  "Contact HR for a fresh link.": "Contacte a RRHH para un nuevo enlace.",
  "Loading form…": "Cargando formulario…",
  "Submitted!": "¡Enviado!",
  "HR has been notified. You'll get an email when your request is reviewed.":
    "Se notificó a RRHH. Recibirá un correo cuando su solicitud sea revisada.",
  "Reference:": "Referencia:",
  "MASCI · Time Off Request": "MASCI · Solicitud de Tiempo Libre",
  "Hello,": "Hola,",
  "Fill out this form to request time off. HR will review and email you a decision.":
    "Llene este formulario para solicitar tiempo libre. RRHH lo revisará y le enviará una decisión por correo.",
  "Position": "Puesto",
  "Department": "Departamento",
  "Reason *": "Motivo *",
  "Pick a reason…": "Elija un motivo…",
  "If Other, please explain *": "Si es Otro, por favor explique *",
  "Pay Type": "Tipo de Pago",
  "Paid": "Pagado",
  "Unpaid": "Sin Pago",
  "Half day on start": "Medio día al inicio",
  "Half day on end": "Medio día al final",
  "Total Days Requested:": "Días Totales Solicitados:",
  "Contact Phone During Leave": "Teléfono de Contacto Durante la Ausencia",
  "Coverage Plan / Who's Covering": "Plan de Cobertura / Quién Cubre",
  "Employee Signature": "Firma del Empleado",
  "Submit Time Off Request": "Enviar Solicitud de Tiempo Libre",
  "Submitting…": "Enviando…",
  // Time Off reason options
  "Vacation": "Vacaciones",
  "Sick Leave": "Permiso por Enfermedad",
  "Medical Appointment": "Cita Médica",
  "Family Emergency": "Emergencia Familiar",
  "Bereavement": "Duelo",
  "Jury Duty": "Jurado",
  "Military Leave": "Permiso Militar",
  "Personal": "Personal",
  "Other": "Otro",

  // ---- Hub.jsx section headers + tile descriptions (iter110) ----------
  "Today in the Field": "Hoy en el Campo",
  "Submissions every crew on site needs today.": "Envíos que cada cuadrilla en la obra necesita hoy.",
  "Leadership Tools": "Herramientas de Liderazgo",
  "For foremen, supervisors, and superintendents in the field.": "Para capataces, supervisores y superintendentes en campo.",
  "Office Portals": "Portales de Oficina",
  "Sign-in required. For office staff, mechanics, and HR.": "Inicio de sesión requerido. Para personal de oficina, mecánicos y RRHH.",
  "Reference": "Referencia",
  "Always available — no sign-in needed.": "Siempre disponible — sin necesidad de iniciar sesión.",
  "Enter →": "Entrar →",
  "The project-management workspace for MASCI office staff.": "El espacio de gestión de proyectos para personal de oficina de MASCI.",
  "The mechanic's console for the MASCI equipment fleet.": "La consola del mecánico para la flota de equipos de MASCI.",
  "Employee records and payroll cross-check for MASCI HR.": "Registros de empleados y verificación de nómina para RRHH de MASCI.",
  "The MASCI office console.": "La consola de oficina de MASCI.",
  "Need Help?": "¿Necesita Ayuda?",
  "Office phone, address, and after-hours contact.": "Teléfono de oficina, dirección y contacto fuera de horario.",
  "Short bilingual lessons for every role.": "Lecciones bilingües cortas para cada rol.",
  "The one-pager pinned in every site trailer.": "La hoja de referencia colgada en cada remolque de obra.",
  "Quality inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.":
    "Inspecciones de calidad para concreto, varilla y trabajo de subcontratistas — documentadas, firmadas, fotografiadas, enrutadas y archivadas.",
  "MASCI Field Leadership": "Liderazgo de Campo MASCI",
  "Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management forms.":
    "Responsabilidad de cuadrilla, documentación de empleados, responsabilidad de equipo, reconocimiento y formularios de gestión de personal.",
  "Project Spaces": "Espacios de Proyecto",
  "Projects": "Proyectos",
  "Messages, to-dos, schedules, docs, and field staking.":
    "Mensajes, tareas, horarios, documentos y replanteo en campo.",

  // ---- Photo upload (iter111) ------------------------------------------
  "Minimum 2 photos required.": "Mínimo 2 fotos requeridas.",
  "Minimum 4 photos required.": "Mínimo 4 fotos requeridas.",
  "Photos: ": "Fotos: ",
  "min 2 required": "mín 2 requeridas",
  "more photo(s) before you can submit": "foto(s) más antes de enviar",
  "photos added": "fotos agregadas",
  "No photos could be added": "No se pudieron agregar fotos",
  "Compressing": "Comprimiendo",
  "of": "de",
  "jobs have plans uploaded": "trabajos tienen planes cargados",
  "file uploaded": "archivo cargado",
  "files uploaded": "archivos cargados",
  "View Plans": "Ver Planes",
  "Not uploaded yet": "Aún no cargado",
  "Pick your job to view its Hazard Plan": "Elija su trabajo para ver su Plan de Peligros",
  "Each MASCI job has its own Job Hazard Plan PDF. Open your job and read it before crew breaks ground. If your job has no plan yet, get with your PM.":
    "Cada trabajo de MASCI tiene su propio PDF del Plan de Peligros. Abra el suyo y léalo antes de que la cuadrilla rompa terreno. Si su trabajo aún no tiene plan, hable con su PM.",
  "Search by job number, name, or location…": "Buscar por número de trabajo, nombre o ubicación…",
  "Download for offline use": "Descargar para uso fuera de línea",
  "On your phone, hold": "En su teléfono, mantenga presionado",
  "Save to Files / Downloads": "Guardar en Archivos / Descargas",
  "to read it where there's no service.": "para leerlo donde no hay señal.",
  "No job matches your search.": "Ningún trabajo coincide con su búsqueda.",
  "Download": "Descargar",

  // ─── iter251 Phase 2 · Trucking / DVIR ──────────────────────────
  "Trucking · Daily DVIR": "Camiones · DVIR Diario",
  "Daily Vehicle Inspection for trucks and trailers. Walk-around · PASS / FAIL each item · Shop sees defects automatically.": "Inspección Diaria del Vehículo para camiones y remolques. Recorrido · APROBADO / FALLA en cada elemento · el Taller ve los defectos automáticamente.",
  "Start DVIR": "Iniciar DVIR",
  "Daily Vehicle Inspection": "Inspección Diaria del Vehículo",
  "Walk around your truck before you roll. Mark every item. Anything FAIL gets logged so Shop can keep us on the road.": "Camine alrededor de su camión antes de salir. Marque cada elemento. Cualquier FALLA se registra para que el Taller nos mantenga en la ruta.",
  "Driver & Truck": "Conductor y Camión",
  "Why we ask for your name": "Por qué pedimos su nombre",
  "Accountability — Shop and Dispatch need to know who walked this truck. Drivers who report defects honestly keep the whole crew safe.": "Responsabilidad — el Taller y Despacho necesitan saber quién revisó este camión. Los conductores que reportan defectos honestamente mantienen a toda la cuadrilla segura.",
  "Driver name": "Nombre del conductor",
  "First and last name": "Nombre y apellido",
  "Date": "Fecha",
  "Time": "Hora",
  "Truck unit": "Unidad de camión",
  "— Pick your truck —": "— Elija su camión —",
  "Plate": "Placa",
  "VIN": "VIN",
  "Odometer": "Odómetro",
  "Hour meter": "Horómetro",
  "Truck Walk-Around": "Recorrido del Camión",
  "How to walk a truck": "Cómo recorrer un camión",
  "Front · driver side · rear · passenger side. Look for leaks under the engine, listen for air, check lights with the 4-ways on, look at every tire's tread.": "Frente · lado del conductor · trasera · lado del pasajero. Busque fugas debajo del motor, escuche el aire, revise las luces con las intermitentes encendidas, mire la banda de cada llanta.",
  "Progress": "Progreso",
  "PASS": "APROBADO",
  "FAIL": "FALLA",
  "N/A": "N/D",
  "Describe the defect — what you saw / heard / felt (10+ chars)": "Describa el defecto — qué vio / oyó / sintió (10+ caracteres)",
  "Photos (optional but helpful)": "Fotos (opcional pero útil)",
  "Why this matters": "Por qué importa",
  "Out of Service if failed": "Fuera de Servicio si falla",
  "Monitor — shop will see this": "Monitor — el taller lo verá",
  "Safety-critical for road operation or worker protection. Shop will be notified and the truck will be tagged Out of Service for this defect.": "Crítico para la operación vial o la protección del trabajador. El Taller será notificado y el camión será etiquetado como Fuera de Servicio por este defecto.",
  "Shop will see this on their queue and schedule a repair window. Truck stays available.": "El Taller lo verá en su cola y programará una ventana de reparación. El camión permanece disponible.",
  "Reference": "Referencia",
  "Trailer Walk-Around": "Recorrido del Remolque",
  "Add trailer": "Agregar remolque",
  "No trailer today? Skip this section.": "¿Sin remolque hoy? Omita esta sección.",
  "Trailer": "Remolque",
  "— Pick trailer —": "— Elija remolque —",
  "Sign & Submit": "Firmar y Enviar",
  "What happens next": "Qué pasa después",
  "Submit and you'll see your truck's status. If anything is Out of Service, Shop is notified automatically and Dispatch will reassign. If it's a Monitor item, Shop sees it and schedules a repair window.": "Envíe y verá el estado de su camión. Si algo está Fuera de Servicio, el Taller es notificado automáticamente y Despacho reasignará. Si es un elemento Monitor, el Taller lo ve y programa una ventana de reparación.",
  "Notes for Shop / Dispatch (optional)": "Notas para Taller / Despacho (opcional)",
  "Anything else worth flagging — sound, smell, vibration, recent fix?": "¿Algo más que valga la pena reportar — sonido, olor, vibración, reparación reciente?",
  "Driver signature": "Firma del conductor",
  "Submit DVIR": "Enviar DVIR",
  "Submitting…": "Enviando…",
  "Loading DVIR form…": "Cargando formulario DVIR…",
  "DVIR form unavailable": "Formulario DVIR no disponible",
  "Back to Field": "Volver a Campo",
  "Please reload.": "Por favor recargue.",
  "Please enter your name.": "Por favor ingrese su nombre.",
  "Please pick your truck.": "Por favor elija su camión.",
  "Please sign before submitting.": "Por favor firme antes de enviar.",
  "Mark every truck item PASS, FAIL, or N/A.": "Marque cada elemento del camión APROBADO, FALLA o N/D.",
  "Mark every trailer item PASS, FAIL, or N/A.": "Marque cada elemento del remolque APROBADO, FALLA o N/D.",
  "Each FAIL needs a short note (10+ characters).": "Cada FALLA necesita una nota corta (10+ caracteres).",
  "Submission failed — please try again.": "Envío fallido — intente de nuevo por favor.",
  "Offline": "Sin conexión",
  "Online": "En línea",
  "Loaded from cache · live data unavailable. Submit when signal returns.": "Cargado desde caché · datos en vivo no disponibles. Envíe cuando regrese la señal.",
  "Could not load truck list. Check your signal and reload.": "No se pudo cargar la lista de camiones. Verifique su señal y recargue.",
  "Severity table version": "Versión de la tabla de severidad",

  // ─── DVIR confirmation page ─────────────────────────────────────
  "Out of Service": "Fuera de Servicio",
  "Repair required before return to service.": "Reparación requerida antes del regreso al servicio.",
  "Shop has been notified automatically. Dispatch will reassign as needed. Thank you for catching this before rolling.": "El Taller ha sido notificado automáticamente. Despacho reasignará según sea necesario. Gracias por detectar esto antes de salir.",
  "Defect Logged · Truck Still Available": "Defecto Registrado · Camión Aún Disponible",
  "Shop has been notified · they'll schedule a repair window.": "El Taller ha sido notificado · programarán una ventana de reparación.",
  "This truck stays available for your shift. Keep an eye on the item you flagged · if anything changes, log another DVIR.": "Este camión permanece disponible para su turno. Esté atento al elemento que reportó · si algo cambia, registre otro DVIR.",
  "All Clear · Ready to Roll": "Todo Despejado · Listo para Rodar",
  "Thanks for the walk-around. Drive safe.": "Gracias por el recorrido. Conduzca con seguridad.",
  "Nothing flagged. Truck status is Available. Have a good shift.": "Nada reportado. El estado del camión es Disponible. Tenga un buen turno.",
  "DVIR submitted": "DVIR enviado",
  "Your inspection was received. This confirmation page only shows details right after submission · please start a fresh DVIR if you need to log another.": "Su inspección fue recibida. Esta página de confirmación solo muestra detalles justo después del envío · por favor inicie un DVIR nuevo si necesita registrar otro.",
  "Submitted": "Enviado",
  "Truck": "Camión",
  "Defects": "Defectos",
  "Status": "Estado",
  "Driver": "Conductor",
  "Available": "Disponible",
  "Defect Logged": "Defecto Registrado",
  "Unknown": "Desconocido",
  "Logged for Shop": "Registrado para el Taller",

  // v1.1 · driver dropdown + denser helptips
  "Type or pick driver name…": "Escriba o elija el nombre del conductor…",
  "If you're new to MASCI, type your full name and tap '+ Add to roster'. Future DVIRs will autocomplete.": "Si es nuevo en MASCI, escriba su nombre completo y toque '+ Agregar al roster'. Los próximos DVIR se autocompletarán.",
  "Air brakes · what to listen for": "Frenos de aire · qué escuchar",
  "Build to 95 psi · listen for leaks at gladhands and chambers · then engine off and watch the gauge for 2 minutes · should not drop more than ~4 psi/min. If it bleeds faster, it's a real defect — not driver error.": "Cargue hasta 95 psi · escuche fugas en las conexiones y cámaras · luego apague el motor y observe el manómetro durante 2 minutos · no debería caer más de ~4 psi/min. Si pierde más rápido, es un defecto real — no es error del conductor.",
  "Tires · quick check": "Llantas · revisión rápida",
  "Tread depth gauge if you have one · otherwise eyeball the wear bars. Walk every tire and run your hand along the sidewall — bulges and cuts feel obvious. Note any audible hiss.": "Use un medidor de profundidad si tiene uno · si no, observe las barras de desgaste. Camine cada llanta y pase la mano por el costado — los bultos y cortes se sienten obvios. Anote cualquier silbido audible.",
  "Coupling · the most common roadside finding": "Acoplamiento · el hallazgo más común en carretera",
  "Confirm the kingpin is fully seated in the fifth wheel · jaws closed · safety pin in place. Tug-test forward in low gear. A bad coupling will drop the trailer · always worth the extra 10 seconds.": "Confirme que el pivote esté completamente asentado en la quinta rueda · mordazas cerradas · pasador de seguridad en su lugar. Pruebe tirando hacia adelante en marcha baja. Un acoplamiento defectuoso dejará caer el remolque · siempre vale los 10 segundos extra.",
  "Shop sees this truck in their queue right now. Once they repair and sign off, Dispatch re-clears the unit for service. You'll see status update on the next DVIR.": "El Taller ve este camión en su cola ahora mismo. Una vez que reparen y aprueben, Despacho autoriza nuevamente la unidad para servicio. Verá la actualización del estado en el próximo DVIR.",
  "Shop sees the defect on their queue. Repair gets scheduled within the operational window for the item. Drive normally until then.": "El Taller ve el defecto en su cola. La reparación se programa dentro de la ventana operacional del elemento. Conduzca normalmente hasta entonces.",
  "You're good to go. Submit another DVIR at the start of your next shift.": "Está listo para irse. Envíe otro DVIR al inicio de su próximo turno.",
  "Start another DVIR": "Iniciar otro DVIR",
  "Home": "Inicio",
  "MASCI · Trucking · DVIR": "MASCI · Camiones · DVIR",

  // ─── Phase 3 · Fleet Visibility (Dispatch / Shop / Safety) ──────
  "Shop · Fleet Repair Queue": "Taller · Cola de Reparación de Flota",
  "Trucks needing attention": "Camiones que requieren atención",
  "Dispatch · Fleet Availability": "Despacho · Disponibilidad de Flota",
  "Fleet operational status": "Estado operacional de la flota",
  "Safety · Fleet Governance": "Seguridad · Gobernanza de Flota",
  "Open defects across fleet": "Defectos abiertos en toda la flota",
  "Repair Required": "Reparación Requerida",
  "Repair In Progress": "Reparación en Progreso",
  "Returned to Service": "Regresado al Servicio",
  "Monitor": "Monitor",
  "OOS": "FDS",
  "Latest DVIR": "Último DVIR",
  "Open OOS units": "Unidades con FDS",
  "Monitor-only units": "Unidades solo en monitoreo",
  "Total units with defects": "Total de unidades con defectos",
  "Total open defects": "Total de defectos abiertos",
  "Severity table approved": "Tabla de severidad aprobada",
  "Download printable reference": "Descargar referencia imprimible",
  "Units": "Unidades",
  "Refresh": "Actualizar",
  "Loading…": "Cargando…",
  "Could not load fleet status.": "No se pudo cargar el estado de la flota.",
  "All clear": "Todo despejado",
  "No open defects across the fleet right now. Great job out there.": "No hay defectos abiertos en la flota en este momento. Excelente trabajo.",
  "Fleet unit": "Unidad de flota",
  "(no item)": "(sin elemento)",
  "photo(s)": "foto(s)",
  "Trucking · Fleet": "Camiones · Flota",
  "See defects grouped by truck · driver notes · current status · severity context. Mobile-friendly · operational clarity only.": "Ver defectos agrupados por camión · notas del conductor · estado actual · contexto de severidad. Compatible con móvil · solo claridad operacional.",
  "Open Fleet View": "Abrir vista de flota",

  // ─── Phase 4 · Repair Lifecycle (Shop · Dispatch · Safety) ──────
  "Awaiting RTS": "Esperando RTS",
  "Mark Repaired": "Marcar Reparado",
  "Return to Service": "Regresar al Servicio",
  "Awaiting Dispatch Return-to-Service": "Esperando confirmación de Despacho",
  "Log Repair": "Registrar Reparación",
  "Shop · Repair Lifecycle": "Taller · Ciclo de Reparación",
  "Confirm Return to Service": "Confirmar Regreso al Servicio",
  "Dispatch · Return-to-Service": "Despacho · Regreso al Servicio",
  "Mechanic / Repair owner": "Mecánico / Responsable de Reparación",
  "Name of the person performing the repair": "Nombre de la persona que realiza la reparación",
  "Repair notes": "Notas de reparación",
  "What was inspected and what was done (parts, adjustments, retorques, etc.)": "Qué se inspeccionó y qué se hizo (piezas, ajustes, reaprietes, etc.)",
  "≥ 5 characters": "≥ 5 caracteres",
  "characters": "caracteres",
  "Repair photos (optional)": "Fotos de reparación (opcional)",
  "Cancel": "Cancelar",
  "Saving…": "Guardando…",
  "Logging the repair flags the defect as awaiting Dispatch Return-to-Service. The unit will not roll until Dispatch confirms.": "Registrar la reparación marca el defecto como pendiente de confirmación de Despacho. La unidad no rodará hasta que Despacho confirme.",
  "Shop repair note": "Nota de reparación del Taller",
  "by": "por",
  "Dispatcher confirming": "Despachador que confirma",
  "Your name": "Su nombre",
  "Dispatch note (optional)": "Nota de Despacho (opcional)",
  "Anything Dispatch should record alongside the return-to-service": "Cualquier cosa que Despacho deba registrar junto con el regreso al servicio",
  "I have reviewed the Shop repair record and confirm this unit is safe to return to service.": "He revisado el registro de reparación del Taller y confirmo que esta unidad es segura para regresar al servicio.",
  "Shop repair logged": "Reparación del Taller registrada",
  "Mechanic": "Mecánico",
  "Open": "Abierto",
  "Shop acknowledged": "Taller reconocido",
  "Returned to service": "Regresado al servicio",
  "View audit trail": "Ver registro de auditoría",
  "Hide audit trail": "Ocultar registro de auditoría",
  "Loading audit trail…": "Cargando registro de auditoría…",
  "No audit events yet.": "Aún no hay eventos de auditoría.",
  "Driver submitted": "Conductor envió",
  "Shop marked repaired": "Taller marcó como reparado",
  "Dispatch returned to service": "Despacho regresó al servicio",
  "Manual OOS by Dispatch": "FDS manual por Despacho",
  "Driver": "Conductor",
  "Trailer": "Remolque",

  // ─── Phase 5 · Weekly Lead + Emergency Equipment ──────────────
  "Weekly · Lead Inspection": "Semanal · Inspección del Líder",
  "Quick weekly check by the lead — operational hygiene, recurring issues, key safety items. Reuses the DVIR flow.": "Revisión semanal rápida por el líder — higiene operativa, problemas recurrentes, elementos clave de seguridad. Reutiliza el flujo DVIR.",
  "Start Lead Inspection": "Iniciar Inspección del Líder",
  "Weekly · Emergency Equipment": "Semanal · Equipo de Emergencia",
  "Fire extinguishers, triangles, first aid, PPE, alarms. Present · charged · within date.": "Extintores, triángulos, botiquín, EPP, alarmas. Presentes · cargados · dentro de fecha.",
  "Start Emergency Check": "Iniciar Revisión de Emergencia",
  "Fleet · Weekly Lead Inspection": "Flota · Inspección Semanal del Líder",
  "Fleet · Weekly Emergency Equipment": "Flota · Equipo de Emergencia Semanal",
  "Fleet · Driver Vehicle Inspection": "Flota · Inspección Vehicular del Conductor",
  "Weekly Lead Inspection": "Inspección Semanal del Líder",
  "Weekly Emergency Equipment": "Equipo de Emergencia Semanal",
  "Daily Vehicle Inspection": "Inspección Vehicular Diaria",
  "Lead inspector": "Inspector Líder",
  "Inspector": "Inspector",
  "Lead inspector signature": "Firma del inspector líder",
  "Inspector signature": "Firma del inspector",
  "Submit Lead Inspection": "Enviar Inspección del Líder",
  "Submit Emergency Check": "Enviar Revisión de Emergencia",
  "Quick weekly check by the lead. High-signal items only — operational hygiene, recurring issues, critical safety items the daily DVIR also covers.": "Revisión semanal rápida por el líder. Solo elementos de alta señal — higiene operativa, problemas recurrentes, elementos críticos de seguridad que la DVIR diaria también cubre.",
  "Emergency equipment & safety systems check. Verify each item is present, charged, and within date.": "Revisión de equipo de emergencia y sistemas de seguridad. Verifique que cada elemento esté presente, cargado y dentro de fecha.",
  "Type or pick name…": "Escriba o seleccione nombre…",
  "If you're new to MASCI, type your full name and tap '+ Add to roster'. Future inspections will autocomplete.": "Si es nuevo en MASCI, escriba su nombre completo y toque '+ Agregar a la lista'. Las futuras inspecciones se autocompletarán.",
  "Lead Walk-Around": "Recorrido del Líder",
  "Emergency Equipment Check": "Revisión de Equipo de Emergencia",

  // ─── iter272 · Legacy View-Surface i18n Closure Cluster ─────────
  // ViewIncident · ViewInspection · ViewDailyReport — translation parity
  // closure. Mirrors the ViewMeeting Sprint 1 (iter268) pattern.

  /* shared chrome */
  "Reports": "Reportes",
  "Incidents": "Incidentes",

  /* delete confirmations + toasts */
  "Incident not found": "Incidente no encontrado",
  "Delete this incident report? This cannot be undone.":
    "¿Eliminar este reporte de incidente? Esto no se puede deshacer.",
  "Delete this inspection? This cannot be undone.":
    "¿Eliminar esta inspección? Esto no se puede deshacer.",
  "Delete this daily report? This cannot be undone.":
    "¿Eliminar este reporte diario? Esto no se puede deshacer.",

  /* ViewIncident — header + sections */
  "Job Site Safety Inspection Report": "Reporte de Inspección de Seguridad del Sitio",
  "Job Site Safety": "Seguridad del Sitio",
  "OSHA Recordable": "Registrable por OSHA",
  "OSHA": "OSHA",
  "Stop Work": "Paro de Trabajo",
  "Hazard Found": "Peligro Encontrado",
  "Classification": "Clasificación",
  "Incident Type": "Tipo de Incidente",
  "Incident Date": "Fecha del Incidente",
  "Incident Time": "Hora del Incidente",
  "Reported Date": "Fecha de Reporte",
  "Reported By": "Reportado Por",
  "Work Stopped": "Trabajo Detenido",
  "Body Part": "Parte del Cuerpo",
  "Injury Nature": "Naturaleza de la Lesión",
  "Sent Home / Off Site": "Enviado a Casa / Fuera del Sitio",
  "No root cause categories selected.": "No se seleccionaron categorías de causa raíz.",
  "No witnesses listed.": "No hay testigos registrados.",
  "Notifications": "Notificaciones",
  "Immediate Actions Taken": "Acciones Inmediatas Tomadas",
  "Target Completion": "Finalización Objetivo",

  /* ViewInspection — sections + labels */
  "Work Activity Taking Place Onsite": "Actividad de Trabajo en el Sitio",
  "General Site Hazards & Housekeeping": "Peligros Generales del Sitio y Orden y Limpieza",
  "Safety Issues / Corrective Actions": "Asuntos de Seguridad / Acciones Correctivas",
  "Description / Corrective Action Notes": "Descripción / Notas de Acción Correctiva",
  "Operation": "Operación",
  "Crew / MASCI Personnel": "Cuadrilla / Personal de MASCI",

  /* ViewDailyReport — sections + tables */
  "Schedule Delays": "Retrasos de Programación",
  "Weather Impact": "Impacto del Clima",
  "Accidents on Site": "Accidentes en el Sitio",
  "Injuries Reported": "Lesiones Reportadas",
  "Detail": "Detalle",
  "Safety Escalation": "Escalación de Seguridad",
  "Safety Notified": "Seguridad Notificada",
  "Contacted": "Contactado",
  "Time of Contact": "Hora del Contacto",
  "Incident Report Filed": "Reporte de Incidente Presentado",
  "Incident Report Time": "Hora del Reporte de Incidente",
  "MASCI Crews": "Cuadrillas de MASCI",
  "Subcontractors": "Subcontratistas",
  "Subcontractor": "Subcontratista",
  "Visitors": "Visitantes",
  "Materials": "Materiales",
  "Activity Log": "Bitácora de Actividades",
  "No MASCI crews on site.": "No hay cuadrillas de MASCI en el sitio.",
  "No subcontractors on site.": "No hay subcontratistas en el sitio.",
  "No site visitors.": "No hay visitantes en el sitio.",
  "No equipment logged.": "No hay equipo registrado.",
  "No material deliveries.": "No hay entregas de materiales.",
  "No activities logged.": "No hay actividades registradas.",
  "No weather captured.": "No se capturó el clima.",
  "Total Hours": "Horas Totales",
  "Trade / Role": "Oficio / Rol",
  "Trade": "Oficio",
  "Lead": "Líder",
  "Start": "Inicio",
  "Stop": "Fin",
  "Hrs": "Hrs",
  "Work Performed": "Trabajo Realizado",
  "In": "Entrada",
  "Out": "Salida",
  "Purpose": "Propósito",
  "Delivered": "Entregado",
  "Removed": "Retirado",
  "Qty": "Cant.",
  "Unit": "Unidad",
  "Supplier": "Proveedor",
  "Ticket #": "Ticket #",
  "% Done": "% Hecho",
  "From": "Desde",
  "To": "Hasta",
  "#": "#",
  "Activity": "Actividad",
  "Sign-Off": "Firma de Cierre",
  "Daily Report": "Reporte Diario",

  // ─── Document Expirations (iter276 · Sequence #7) ────────────────
  "Document Expirations": "Vencimientos de Documentos",
  "Compliance Tracker": "Rastreador de Cumplimiento",
  "Back": "Atrás",
  "Current": "Vigente",
  "Expiring Soon": "Por Vencer",
  "Expired": "Vencido",
  "All statuses": "Todos los estados",
  "All categories": "Todas las categorías",
  "Employee documents": "Documentos del empleado",
  "Training certifications": "Certificaciones de capacitación",
  "Safety compliance": "Cumplimiento de seguridad",
  "Equipment / asset": "Equipo / activo",
  "Company / admin": "Compañía / administración",
  "Project / job": "Proyecto / obra",
  "Search document type or title…": "Buscar tipo o título de documento…",
  "Preview Scan": "Vista previa de escaneo",
  "Run Scan": "Ejecutar escaneo",
  "Could not load expirations": "No se pudieron cargar los vencimientos",
  "Expiration record added": "Registro de vencimiento agregado",
  "Could not save expiration": "No se pudo guardar el vencimiento",
  "Scan failed": "El escaneo falló",
  "Document type and expiration date are required": "El tipo de documento y la fecha de vencimiento son obligatorios",
  "No expiration records": "No hay registros de vencimiento",
  "Documents you upload with an expiration date will appear here. Try clearing filters.": "Los documentos que suba con una fecha de vencimiento aparecerán aquí. Intente borrar los filtros.",
  "Document": "Documento",
  "Linked To": "Vinculado a",
  "Expires": "Vence",
  "Days": "Días",
  "Add Expiration Record": "Agregar Registro de Vencimiento",
  "Document type *": "Tipo de documento *",
  "e.g. OSHA 30, TWIC, CDL Medical": "p. ej. OSHA 30, TWIC, Médico CDL",
  "Category *": "Categoría *",
  "Title / Reference": "Título / Referencia",
  "e.g. John Doe — Driver License": "p. ej. Juan Pérez — Licencia de Conducir",
  "Issue date": "Fecha de emisión",
  "Expiration date *": "Fecha de vencimiento *",
  "Linked employee ID": "ID de empleado vinculado",
  "Linked equipment ID": "ID de equipo vinculado",
  "Preview": "Vista previa",
  "threshold(s) would fire": "umbral(es) se dispararían",
  "Scan complete": "Escaneo completo",
  "threshold(s) fired": "umbral(es) disparados",

  // ─── HR Payroll Variance (iter283 · UI key parity) ────────────
  "Could not load recent batches": "No se pudieron cargar los lotes recientes",
  "Paste your Exact CSV first": "Pegue primero su CSV de Exact",
  "Variance batch created": "Lote de variación creado",
  "Upload failed": "Falló la carga",
  "Could not load batch": "No se pudo cargar el lote",
  "Could not save decision": "No se pudo guardar la decisión",
  "CSV download failed": "Falló la descarga del CSV",
  "Paste your Exact payroll export": "Pegue su exportación de nómina de Exact",
  "Paste the CSV from Exact for the week — the system matches each row to MASCI supervisor-reported hours and flags every variance above the threshold.": "Pegue el CSV de Exact para la semana — el sistema empareja cada fila con las horas reportadas por el supervisor de MASCI y marca cada variación por encima del umbral.",
  "Week Ending": "Semana Terminada",
  "Threshold (minutes)": "Umbral (minutos)",
  "Run Variance": "Correr Variación",
  "Employee Name,Employee ID,Regular Hours,Overtime Hours,Total Hours\nJohn Smith,E1001,40,2.5,42.5\n...": "Nombre del Empleado,ID del Empleado,Horas Regulares,Horas Extra,Horas Totales\nJuan Pérez,E1001,40,2.5,42.5\n...",
  "Accepted columns: Employee Name (required), Regular Hours OR Total Hours (required), Overtime Hours, Employee ID, Week Ending. Comma, tab, or pipe-delimited.": "Columnas aceptadas: Nombre del Empleado (obligatorio), Horas Regulares O Horas Totales (obligatorio), Horas Extra, ID del Empleado, Semana Terminada. Separadas por coma, tab o pipe.",
  "Recent Variance Batches": "Lotes Recientes de Variación",
  "No variance batches yet. Paste a CSV above to create the first one.": "Todavía no hay lotes de variación. Pegue un CSV arriba para crear el primero.",
  "Created": "Creado",
  "Matched": "Coincidente",
  "Flagged": "Marcado",
  "Active Batch · Week Ending": "Lote Activo · Semana Terminada",
  "Download CSV": "Descargar CSV",
  "Pending Review": "Pendiente de Revisión",
  "Exact Reg": "Exact Reg.",
  "Exact OT": "Exact T.E.",
  "Exact Total": "Exact Total",
  "MASCI Total": "MASCI Total",
  "Diff": "Dif",
  "Flag": "Marca",
  "Decision": "Decisión",
  "Approve": "Aprobar",
  "Dispute": "Disputar",

  // ─── HR Employee Lifecycle Dates (iter285) ────────────────────
  "Original Hire Date": "Fecha Original de Contratación",
  "write-once · already set": "una sola escritura · ya fijada",
  "Tenure": "Antigüedad",
  "days": "días",
  "yr": "año",
  "Last Day Worked": "Último Día Trabajado",
  "Termination Date": "Fecha de Terminación",
  "Leave Start Date": "Inicio de Permiso",
  "Expected Return Date": "Fecha Esperada de Regreso",
  "Separation Type": "Tipo de Separación",
  "voluntary": "voluntaria",
  "involuntary": "involuntaria",
  "layoff": "despido",
  "New status": "Nuevo estatus",
  "Pick a type": "Escoja un tipo",
  "Reason / note": "Razón / nota",
  "Optional context recorded in status history": "Contexto opcional registrado en el historial de estatus",
  "Pick a separation type — voluntary, involuntary, or layoff": "Escoja un tipo de separación — voluntaria, involuntaria o despido",
  "Status updated": "Estatus actualizado",
  "offboarding tasks created": "tareas de desvínculo creadas",
  "Status change failed": "Falló el cambio de estatus",
  "Employee updated": "Empleado actualizado",
  "Update failed": "Falló la actualización",

  // ─── HR Driver Qualification (iter286) ────────────────────────
  "Driver Qualification": "Calificación del Conductor",
  "CDL Holder": "Titular de CDL",
  "Approved Company Driver": "Conductor Aprobado por la Compañía",
  // ─── iter353c · Employee Accountability Timeline ─────────────
  "Approved Driver": "Conductor Aprobado",
  "CDL Expires": "CDL Vence",
  "Medical Card": "Tarjeta Médica",
  "Expiring ≤90d": "Vence ≤90d",
  "Compliance Brief PDF": "PDF de Resumen de Cumplimiento",
  "Compliance brief downloaded": "PDF de cumplimiento descargado",
  "Could not download PDF.": "No se pudo descargar el PDF.",
  "Could not load accountability timeline.": "No se pudo cargar el historial de responsabilidad.",
  "Employee Accountability Timeline.": "Línea de Tiempo de Responsabilidad del Empleado.",
  "Aggregated read-only view of training, PPE, incidents, CDL/medical, Field Leadership, and HR lifecycle events. Source records remain authoritative — corrections are made in their original portal.": "Vista agregada de solo lectura: capacitación, EPP, incidentes, CDL/médico, Liderazgo de Campo y ciclo de vida de RR. HH. Los registros fuente siguen siendo autoritativos — las correcciones se hacen en su portal original.",
  "Loading employee accountability…": "Cargando responsabilidad del empleado…",
  "PPE": "EPP",
  "FL Records": "Registros de Liderazgo",
  "Driver Qual": "Calif. Conductor",
  "HR Lifecycle": "Ciclo de RR. HH.",
  "Expiration Watch": "Vigilancia de Vencimientos",
  "No events in this category yet.": "Aún no hay eventos en esta categoría.",
  "Event": "Evento",
  "Source": "Fuente",
  "By": "Por",
  "exp": "vence",
  "Aggregated view · source records remain authoritative · generated": "Vista agregada · registros fuente autoritativos · generado",
  "Employee Accountability Timeline": "Línea de Tiempo de Responsabilidad",
  "View Accountability Timeline": "Ver Línea de Tiempo de Responsabilidad",
  "Accountability": "Responsabilidad",
  "Driver Status": "Estatus del Conductor",
  // ─── iter353b-availability · Drivers Available Right Now ─────
  "Drivers Available Right Now": "Conductores Disponibles Ahora",
  "non-CDL approved": "no-CDL aprobado",
  "Active · approved · CDL valid · medical valid": "Activo · aprobado · CDL vigente · médico vigente",
  "Click to filter": "Clic para filtrar",
  "Showing dispatchable only — click to clear": "Mostrando solo disponibles — clic para limpiar",
  "Could not load driver qualification.": "No se pudo cargar la calificación del conductor.",
  "Read-only · Driver Qualification": "Solo lectura · Calificación del Conductor",
  "Verify approved-driver and CDL readiness before sending or assigning someone to work. Editing happens in HR — corrections are made there.": "Verifique conductor aprobado y CDL antes de enviar o asignar a alguien al trabajo. La edición ocurre en RR. HH. — las correcciones se hacen ahí.",
  "Drivers in scope": "Conductores en alcance",
  "CDL expiring ≤30d": "CDL vence ≤30d",
  "Medical ≤30d": "Médico ≤30d",
  "Restricted": "Restringido",
  "Suspended": "Suspendido",
  "Name · employee ID · CDL #": "Nombre · ID empleado · CDL #",
  "Any": "Cualquiera",
  "CDL holders only": "Solo titulares de CDL",
  "Non-CDL": "No-CDL",
  "Approved only": "Solo aprobados",
  "Not approved": "No aprobados",
  "Inactive": "Inactivo",
  "≤30d": "≤30d",
  "Approved": "Aprobado",
  "Endorsements": "Endosos",
  "Medical": "Médico",
  "No driver-qualified employees match the current filter.": "Ningún empleado calificado coincide con el filtro actual.",
  "Read-only · source roster owned by HR · last verified": "Solo lectura · roster fuente propiedad de RR. HH. · última verificación",
  "Dispatch · Approved Drivers / CDL Readiness": "Despacho · Conductores Aprobados / CDL",
  "Field Leadership · Driver Readiness": "Liderazgo de Campo · Disponibilidad de Conductores",
  "Pick a status": "Escoja un estatus",
  "active": "activo",
  "suspended": "suspendido",
  "restricted": "restringido",
  "inactive": "inactivo",
  "CDL License Number": "Número de Licencia CDL",
  "CDL State": "Estado de CDL",
  "CDL Expiration Date": "Fecha de Vencimiento de CDL",
  "Medical Card Expiration Date": "Fecha de Vencimiento de Tarjeta Médica",

  // ─── HR CDL Endorsements + Restrictions (iter287) ─────────────
  "CDL Endorsements": "Endosos de CDL",
  "CDL Restrictions": "Restricciones de CDL",
  "Tanker (N)": "Tanque (N)",
  "Hazmat (H)": "Hazmat (H)",
  "Tanker + Hazmat (X)": "Tanque + Hazmat (X)",
  "Doubles/Triples (T)": "Dobles/Triples (T)",
  "Passenger (P)": "Pasajeros (P)",
  "School Bus (S)": "Autobús Escolar (S)",
  "Air Brake Restriction": "Restricción de Freno de Aire",
  "Manual Transmission Restriction": "Restricción de Transmisión Manual",

  // ─── HR Driver Qualification Dashboard (iter288) ──────────────
  "Driver Qualification Dashboard": "Tablero de Calificación de Conductores",
  "HR · Operational Visibility": "RH · Visibilidad Operacional",
  "CDL Expiring 30d": "CDL Vence 30d",
  "Medical Card Expiring 30d": "Tarjeta Médica Vence 30d",
  "Restricted": "Restringido",
  "Suspended": "Suspendido",
  "Tanker-Capable": "Capaz de Tanque",
  "Export Current View → CSV": "Exportar Vista Actual → CSV",
  "Export the current filtered view to CSV": "Exportar la vista filtrada actual a CSV",
  "Driver qualification CSV downloaded": "CSV de calificación de conductores descargado",
  "Could not export driver qualification CSV": "No se pudo exportar el CSV de calificación de conductores",
  "Read-only operational visibility · CDL holders · approved drivers · endorsements · expirations · tanker-capable list":
    "Visibilidad operacional de solo lectura · titulares de CDL · conductores aprobados · endosos · vencimientos · lista capaz de tanque",
  "Name · ID · CDL #": "Nombre · ID · # de CDL",
  "Any": "Cualquiera",
  "Yes": "Sí",
  "No": "No",
  "Endorsement": "Endoso",
  "No matching drivers": "No hay conductores que coincidan",
  "Adjust filters above, or add driver qualification data on an employee record in the HR portal.":
    "Ajuste los filtros arriba, o agregue datos de calificación de conductor en el registro de un empleado en el portal de RH.",
  "Driver": "Conductor",
  "CDL": "CDL",
  "Approved": "Aprobado",
  "Endorsements": "Endosos",
  "Restrictions": "Restricciones",
  "CDL Exp": "Venc. CDL",
  "Medical Exp": "Venc. Médica",
  "Drivers": "Conductores",
  "Air Brake": "Freno de Aire",
  "Manual": "Manual",
  "Expired": "Vencido",
  "Expiring soon": "Vence pronto",
  "Could not load driver qualification dashboard": "No se pudo cargar el tablero de calificación de conductor",

  // ─── Fire Extinguishers (iter293) ──────────────────────────────
  // Keys NOT duplicated below already exist with established
  // translations (Pass="Cumple" · Fail="No Cumple" · Status="Estado" ·
  // Notes="Notas" · Cancel · Save · Loading… · Type · Size · Unit ID ·
  // Inspection date · Inspector name · Last status · Last inspection
  // date · Next due date · Next due date (optional) · How is next-due
  // calculated? · Leave blank … · Defaults to signed-in safety user ·
  // Linked equipment (optional) · etc). iter293 adds ONLY the labels
  // that were genuinely missing from the registry.
  "Fire Extinguishers": "Extintores",
  "SAFETY · FIRE EXTINGUISHER REGISTER": "SEGURIDAD · REGISTRO DE EXTINTORES",
  "Track every fire extinguisher unit across trucks, jobsites, and facilities. Monthly inspections push status + next-due date + the inspection log automatically.":
    "Lleve el control de cada extintor en camiones, obras e instalaciones. Las inspecciones mensuales actualizan estatus, próxima fecha y bitácora automáticamente.",
  "Bulk Import": "Importación Masiva",
  "Add Extinguisher": "Agregar Extintor",
  "Add fire extinguisher": "Agregar extintor",
  "Edit extinguisher": "Editar extintor",
  "One record per physical unit. Logging inspections later updates this row + adds to history.":
    "Un registro por unidad física. Registrar inspecciones después actualiza esta fila y agrega al historial.",
  "Filter by unit, location, type…": "Filtrar por unidad, ubicación, tipo…",
  "No extinguishers": "No hay extintores",
  "Add the first one above.": "Agregue el primero arriba.",
  "Try a different filter.": "Pruebe un filtro diferente.",
  // Tabs (Pass / Fail / Status already translated — Cumple / No Cumple / Estado)
  "All": "Todos",
  "Needs Service": "Necesita Servicio",
  "Overdue": "Vencido",
  // Table headers
  "Unit": "Unidad",
  "Location": "Ubicación",
  "Type / Size": "Tipo / Tamaño",
  "Last Inspect": "Última Inspección",
  "Next Due": "Próximo Vence",
  "Actions": "Acciones",
  // Row chip — location_kind values
  "truck": "camión",
  "job": "obra",
  "facility": "instalación",
  // Form Select labels for location-kind
  "Location kind": "Tipo de ubicación",
  "Location value": "Ubicación",
  "Truck #": "Camión #",
  "Job # / Project": "Obra # / Proyecto",
  "Facility": "Instalación",
  // Inspect dialog
  "Log inspection": "Registrar inspección",
  "Saves the result + auto-stamps next due date (defaults to +30 days).":
    "Guarda el resultado y auto-marca la próxima fecha (por defecto +30 días).",
  "Attachments & PDF history": "Adjuntos e historial PDF",
  "Delete failed": "Falló al borrar",
  "e.g. Truck 12 / Job 220 / Shop": "ej. Camión 12 / Obra 220 / Taller",

  // iter296 · Operational Guidance Center shell-chrome i18n closure
  "Search results": "Resultados de búsqueda",
  "All guidance": "Toda la guía",
  "No matching guidance available for your access level.": "No hay guía coincidente disponible para su nivel de acceso.",
  "Not available": "No disponible",
  "This guidance isn't available for your access level.": "Esta guía no está disponible para su nivel de acceso.",
  "Back to Guidance": "Regresar a la Guía",
  "Section": "Sección",
  "No articles in this section for your access level.": "No hay artículos en esta sección para su nivel de acceso.",
  "Related guidance": "Guía relacionada",

  // iter300 · Bilingual continuity ES dictionary closure (Lane A clusters A+B+C+D+G+I+J)
  // 162 keys · pure dictionary additions · NO JSX changes · operator-approved.
  // Tone discipline: calm, operational, field-readable. Reuses canonical
  // terminology already established earlier in this file (Cumple/No Cumple,
  // Acción Correctiva, Reporte Diario, Cuadrilla, Capacitación, Extintor, FDS).

  // A · SafetyHub.jsx
  "All time": "Todo el tiempo",
  "Audits & Inspections": "Auditorías e Inspecciones",
  "Awaiting close-out": "En espera de cierre",
  "CA · Open": "AC · Abierta",
  "CA · Overdue": "AC · Vencida",
  "Change Password": "Cambiar Contraseña",
  "Could not load metrics. Sign out and back in.": "No se pudieron cargar las métricas. Cierre sesión y vuelva a entrar.",
  "Cross-portal accountability engine. Track corrective actions, follow-ups, deficiencies, and approvals to closure.": "Motor de rendición de cuentas entre portales. Rastree acciones correctivas, seguimientos, deficiencias y aprobaciones hasta el cierre.",
  "Employee Safety Profiles": "Perfiles de Seguridad del Empleado",
  "Employee certifications, training records, expiration tracking, sign-in sheets, and renewal alerts.": "Certificaciones del empleado, registros de capacitación, seguimiento de vencimientos, listas de firmas y alertas de renovación.",
  "Equipment Accountability": "Rendición de Cuentas del Equipo",
  "Field Leadership records": "Registros de Liderazgo de Campo",
  "Filter the 136-topic safety library by severity and domain · build a multi-topic PDF pack for kickoffs, mobilizations, and high-risk job prep. Internal use only.": "Filtre la biblioteca de 136 temas de seguridad por severidad y dominio · arme un paquete PDF de varios temas para arranques, movilizaciones y trabajos de alto riesgo. Uso interno solamente.",
  "Incidents & Near Misses": "Incidentes y Casi-Accidentes",
  "Incidents (Total)": "Incidentes (Total)",
  "Incidents · 7d": "Incidentes · 7d",
  "Inspections · 30d": "Inspecciones · 30d",
  "Last 30 days": "Últimos 30 días",
  "Last 7 days": "Últimos 7 días",
  "Loading metrics…": "Cargando métricas…",
  "Meetings · 7d": "Reuniones · 7d",
  "Modules": "Módulos",
  "Monday-morning email digest of open CAs, overdue items, 7-day incidents, and 30-day training expirations. Preview anytime or send on demand.": "Resumen por correo cada lunes en la mañana: ACs abiertas, vencidas, incidentes de 7 días y vencimientos de capacitación a 30 días. Vista previa en cualquier momento o envíelo a pedido.",
  "Monthly inspections, due-date tracking, pass/fail records, and unit-level history per truck / job / facility.": "Inspecciones mensuales, seguimiento de fechas de vencimiento, registros de Cumple/No Cumple e historial por unidad para cada camión / obra / instalación.",
  "OSHA 300, insurance summaries, trend reports, executive roll-ups, and project safety flags.": "OSHA 300, resúmenes de seguro, reportes de tendencia, resúmenes ejecutivos y banderas de seguridad por proyecto.",
  "OSHA records, SDS, emergency action plans, competent-person docs, fall-protection training, sign-in sheets, and more.": "Registros OSHA, SDS, planes de acción de emergencia, documentos de persona competente, capacitación de protección contra caídas, listas de firmas y más.",
  "Open → In Progress → Pending Review → Closed. Track every safety deficiency to resolution. Auto-link to incidents, audits, inspections, and training records.": "Abierta → En Progreso → Pendiente de Revisión → Cerrada. Rastree cada deficiencia de seguridad hasta su resolución. Vinculación automática con incidentes, auditorías, inspecciones y registros de capacitación.",
  "PPE Issuances": "Entregas de EPP",
  "Past due date": "Pasada la fecha de vencimiento",
  "Per-employee roll-up: trainings, certs, meeting attendance, incident involvement, retraining, and PPE issuance.": "Resumen por empleado: capacitaciones, certificaciones, asistencia a reuniones, participación en incidentes, recapacitación y entrega de EPP.",
  "Read-only roll-up of every incident report filed from the field. Filter by severity, project, employee, and date.": "Resumen de solo lectura de cada incidente enviado desde el campo. Filtre por severidad, proyecto, empleado y fecha.",
  "Reports & Exports": "Reportes y Exportes",
  "Safety Document Library": "Biblioteca de Documentos de Seguridad",
  "Site safety audits and jobsite inspections — same records the field submits, organized for Safety review and close-out.": "Auditorías de seguridad de la obra e inspecciones de campo — los mismos registros que envía el campo, organizados para revisión y cierre por Seguridad.",
  "Step-by-step operator guides for Safety Portal workflows — Corrective Actions, Incidents, Fire Extinguisher Bulk Import, Weekly Digest. Download any guide as PDF.": "Guías paso a paso para los flujos del Portal de Seguridad — Acciones Correctivas, Incidentes, Importación Masiva de Extintores, Resumen Semanal. Descargue cualquier guía en PDF.",
  "Tasks & Actions": "Tareas y Acciones",
  "Toolbox + huddles": "Reuniones de seguridad + huddles",
  "Topic Library · Operational Prep": "Biblioteca de Temas · Preparación Operacional",
  "Training & Certifications": "Capacitación y Certificaciones",
  "Training Center & Guides": "Centro de Capacitación y Guías",
  "Training Deficiencies": "Deficiencias de Capacitación",
  "Training certifications, competent-person docs, fall protection, CPR/First Aid — visibility before they lapse.": "Certificaciones de capacitación, documentos de persona competente, protección contra caídas, CPR/Primeros Auxilios — visibilidad antes de que venzan.",
  "Update your Safety Portal password. Required for first login after Admin issues a temp password.": "Actualice su contraseña del Portal de Seguridad. Requerido en el primer inicio de sesión después de que Admin le emita una contraseña temporal.",
  "Weekly Digest": "Resumen Semanal",

  // B · SafetyCorrectiveActions.jsx
  "Any employee": "Cualquier empleado",
  "Any equipment": "Cualquier equipo",
  "Assigned": "Asignado",
  "Assigned to (email)": "Asignado a (correo)",
  "Assigned to (name)": "Asignado a (nombre)",
  "Completion notes": "Notas de cierre",
  "Corrective actions track findings from inspections, incidents, and audits through to closure. Tap the New button above to create your first one.": "Las acciones correctivas rastrean los hallazgos de inspecciones, incidentes y auditorías hasta su cierre. Toque el botón Nueva arriba para crear la primera.",
  "Due date": "Fecha de vencimiento",
  "Edit corrective action": "Editar acción correctiva",
  "Employee acknowledgment": "Reconocimiento del empleado",
  "Filter by linked employee": "Filtrar por empleado vinculado",
  "Filter by linked equipment": "Filtrar por equipo vinculado",
  "Filter by title, project, assignee, description…": "Filtrar por título, proyecto, asignado, descripción…",
  "Link to a source record (incident, audit, inspection, training, meeting) and assign a responsible party.": "Vincule a un registro de origen (incidente, auditoría, inspección, capacitación, reunión) y asigne un responsable.",
  "Linked employee": "Empleado vinculado",
  "Linked equipment": "Equipo vinculado",
  "New Corrective Action": "Nueva Acción Correctiva",
  "New corrective action": "Nueva acción correctiva",
  "No corrective actions": "Sin acciones correctivas",
  "Nothing matches this filter yet. Try the 'All' tab to see every record.": "Nada coincide con este filtro todavía. Pruebe la pestaña 'Todas' para ver todos los registros.",
  "Open → In Progress → Pending Review → Closed": "Abierta → En Progreso → Pendiente de Revisión → Cerrada",
  "Optional — paste record ID": "Opcional — pegue el ID del registro",
  "Priority": "Prioridad",
  "Priority drives WHEN we act — it controls the Open-queue ordering. Severity (set on the source incident or audit) describes the risk of the underlying finding itself.": "La prioridad determina CUÁNDO actuamos — controla el orden de la cola de abiertas. La severidad (fijada en el incidente o auditoría de origen) describe el riesgo del hallazgo en sí.",
  "Priority vs. Severity": "Prioridad vs. Severidad",
  "Project": "Proyecto",
  "Project number": "Número de proyecto",
  "Required to mark as Closed — what was done and when?": "Requerido para marcar como Cerrada — ¿qué se hizo y cuándo?",
  "Search by name / email / employee ID…": "Buscar por nombre / correo / ID de empleado…",
  "Search by unit / make / VIN…": "Buscar por unidad / marca / VIN…",
  "Short summary — e.g. Install missing fire extinguisher at job 220": "Resumen corto — ej. Instalar extintor faltante en obra 220",
  "Source": "Origen",
  "Source record ID": "ID del registro de origen",
  "Submit for Review": "Enviar para Revisión",
  "Track every safety deficiency to resolution. Auto-link CAs to incidents, audits, inspections, training records, and meetings. The pipeline is": "Rastree cada deficiencia de seguridad hasta su resolución. Vinculación automática de las AC con incidentes, auditorías, inspecciones, registros de capacitación y reuniones. La secuencia es",
  "What needs to happen and why?": "¿Qué tiene que pasar y por qué?",

  // C · SafetyTopicLibrary.jsx
  "Both languages (EN page · ES page · per topic)": "Ambos idiomas (página EN · página ES · por tema)",
  "Choose the language for the generated pack.": "Elija el idioma del paquete generado.",
  "Clear selection": "Limpiar selección",
  "English only": "Solo inglés",
  "Filter the 136-topic safety library by severity and domain. Pick the topics you need, choose the language, and generate a PDF pack. For kickoffs, mobilizations, and high-risk job prep — not for distribution outside MASCI Safety/Admin.": "Filtre la biblioteca de 136 temas de seguridad por severidad y dominio. Escoja los temas que necesita, elija el idioma y genere un paquete PDF. Para arranques, movilizaciones y trabajos de alto riesgo — no para distribución fuera de MASCI Seguridad/Admin.",
  "Generate": "Generar",
  "Generate PDF Pack": "Generar Paquete PDF",
  "Generating…": "Generando…",
  "No topics match the current filters.": "Ningún tema coincide con los filtros actuales.",
  "PDF generation failed: ": "Falló la generación del PDF: ",
  "PDF pack generated · {n} topic(s)": "Paquete PDF generado · {n} tema(s)",
  "Safety / Admin · Internal Use": "Seguridad / Admin · Uso Interno",
  "Safety/Admin operational metadata · not for field display": "Metadatos operacionales de Seguridad/Admin · no para vista en campo",
  "Search by title (EN or ES)…": "Buscar por título (EN o ES)…",
  "Select all visible": "Seleccionar todos los visibles",
  "Select at least one topic before generating a pack.": "Seleccione al menos un tema antes de generar un paquete.",
  "Spanish only": "Solo español",
  "Topic Library · MASCI Safety": "Biblioteca de Temas · MASCI Seguridad",
  "Try clearing severity, domain, or search.": "Pruebe limpiar severidad, dominio o búsqueda.",
  "topics selected": "tema(s) seleccionado(s)",

  // D1 · SafetyTrainingRecords.jsx
  "Add Record": "Agregar Registro",
  "Add training record": "Agregar registro de capacitación",
  "Certification type": "Tipo de certificación",
  "Completed date": "Fecha de finalización",
  "Edit training record": "Editar registro de capacitación",
  "Expiration date": "Fecha de vencimiento",
  "Filter by employee, training, cert type…": "Filtrar por empleado, capacitación, tipo de certificación…",
  "Issued by": "Emitido por",
  "Leave blank for certifications that don't expire (e.g. orientation). For OSHA-10/30, MSHA, CPR/First Aid, and other annual or biennial certs, set this to the date the credential lapses.": "Deje en blanco para certificaciones que no vencen (ej. orientación). Para OSHA-10/30, MSHA, CPR/Primeros Auxilios y otras certificaciones anuales o bianuales, ponga la fecha en que la credencial caduca.",
  "No training records": "Sin registros de capacitación",
  "Nothing matches this filter.": "Nada coincide con este filtro.",
  "Or search by name / email / employee ID…": "O buscar por nombre / correo / ID de empleado…",
  "Per-employee training records tied to the MASCI employee roster. Expiration tracking flags certs about to lapse so they're renewed before the field crew is non-compliant.": "Registros de capacitación por empleado ligados a la lista de empleados de MASCI. El seguimiento de vencimientos marca las certificaciones por caducar para renovarlas antes de que la cuadrilla quede fuera de cumplimiento.",
  "Pick employee": "Escoger empleado",
  "Tied to the MASCI employee roster. Leave expiration blank for trainings that don't expire.": "Ligado a la lista de empleados de MASCI. Deje el vencimiento en blanco para capacitaciones que no vencen.",
  "Training name": "Nombre de la capacitación",
  "When does a training expire?": "¿Cuándo vence una capacitación?",

  // D2 · SafetyDocuments.jsx
  "Centralized storage for OSHA records, SDS, emergency action plans, training certificates, sign-in sheets, and policies. Visible to Safety, HR, and Admin.": "Almacenamiento central para registros OSHA, SDS, planes de acción de emergencia, certificados de capacitación, listas de firmas y políticas. Visible para Seguridad, RH y Admin.",
  "Comma-separated — e.g. confined-space, 2026": "Separado por comas — ej. espacio-confinado, 2026",
  "Defaults to filename": "Por defecto, el nombre del archivo",
  "Max 15 MB. Visible to Safety, HR, and Admin once uploaded.": "Máximo 15 MB. Visible para Seguridad, RH y Admin una vez subido.",
  "No documents": "Sin documentos",
  "Search title, filename, tags…": "Buscar título, nombre de archivo, etiquetas…",
  "Upload": "Subir",
  "Upload Document": "Subir Documento",
  "Upload one with the button above.": "Suba uno con el botón de arriba.",
  "Upload safety document": "Subir documento de seguridad",

  // D3 · SafetyFireExtinguishers.jsx
  "Defaults to signed-in safety user": "Por defecto, el usuario de seguridad con sesión iniciada",
  "How is next-due calculated?": "¿Cómo se calcula la próxima fecha?",
  "Inspection date": "Fecha de inspección",
  "Inspector name": "Nombre del inspector",
  "Last inspection date": "Fecha de la última inspección",
  "Last status": "Último estado",
  "Leave blank and the system auto-sets +30 days from today (monthly cadence per NFPA 10). Override only when the unit is on a custom inspection interval (e.g. quarterly).": "Déjelo en blanco y el sistema fija automáticamente +30 días desde hoy (cadencia mensual según NFPA 10). Cámbielo solamente cuando la unidad tenga un intervalo de inspección personalizado (ej. trimestral).",
  "Leave blank to auto-set +30 days.": "Deje en blanco para que se fije automáticamente +30 días.",
  "Linked equipment (optional)": "Equipo vinculado (opcional)",
  "Next due date": "Próxima fecha de vencimiento",
  "Next due date (optional)": "Próxima fecha de vencimiento (opcional)",
  "Truck or yard unit this extinguisher is assigned to": "Camión o unidad de patio al que se asignó este extintor",
  "Unit ID": "ID de unidad",

  // G · SafetyIncidents.jsx
  "Failed to load incidents": "Falló al cargar los incidentes",
  "No incidents match these filters.": "Ningún incidente coincide con estos filtros.",
  "Project / Job": "Proyecto / Obra",
  "Read-only review of every incident and near-miss filed from the field. Use the filters to focus on critical events, open investigations, or a specific job/employee. New incidents are submitted from the field at ": "Revisión de solo lectura de cada incidente y casi-accidente enviado desde el campo. Use los filtros para concentrarse en eventos críticos, investigaciones abiertas o un empleado/obra específico. Los nuevos incidentes se envían desde el campo en ",
  "Safety Review": "Revisión de Seguridad",
  "Search title, employee, supervisor, job…": "Buscar título, empleado, supervisor, obra…",
  "incidents shown": "incidentes mostrados",

  // I1 · HrHub.jsx
  "Driver Safety Events (HR Review)": "Eventos de Seguridad del Conductor (Revisión RH)",
  "Employee Records & Accountability": "Registros del Empleado y Rendición de Cuentas",
  "OPEN →": "ABRIR →",
  "Read-only HR access · field leadership records · accountability · payroll-time verification · training compliance.": "Acceso de solo lectura para RH · registros de liderazgo de campo · rendición de cuentas · verificación de tiempo para nómina · cumplimiento de capacitación.",

  // I2 · ShopHub.jsx
  "Change password": "Cambiar contraseña",
  "Fleet Repair Queue · grouped by truck": "Cola de Reparación de Flota · agrupada por camión",
  "Guides": "Guías",
  "Integrations": "Integraciones",

  // iter317-C Part 2 · HR Hub grouped-card refinement
  "Primary HR Actions": "Acciones Principales de RH",
  "Day-to-day employee operations": "Operaciones diarias del personal",
  "Compliance & Accountability": "Cumplimiento y Rendición de Cuentas",
  "Field leadership · accountability · safety · driver qualification": "Liderazgo de campo · rendición de cuentas · seguridad · calificación de conductor",
  "Payroll / Time": "Nómina / Tiempo",
  "Time, payroll variance, expense tracking, training compliance": "Tiempo, variación de nómina, seguimiento de gastos, cumplimiento de capacitación",
  "Integrations & Systems": "Integraciones y Sistemas",
  "Supporting tools · guides · cross-portal integration visibility": "Herramientas de apoyo · guías · visibilidad de integraciones entre portales",

  // iter318 · Safety Hub Calm Pass (grouped sections)
  "Primary Safety Operations": "Operaciones Principales de Seguridad",
  "Day-to-day safety workflows": "Flujos diarios de seguridad",
  "Compliance & Records": "Cumplimiento y Registros",
  "Training, certifications, documents, expirations": "Capacitación, certificaciones, documentos, vencimientos",
  "Operational Output": "Producción Operacional",
  "Digests, reports, topic prep, fleet visibility": "Resúmenes, reportes, preparación de temas, visibilidad de flota",
  "Guidance & Systems": "Guía y Sistemas",
  "Supporting tools · operator guides · cross-portal integration visibility": "Herramientas de apoyo · guías para operadores · visibilidad de integraciones entre portales",

  // iter319 · Field Hub Calm Pass (grouped sections + new CTAs)
  "Daily Operations": "Operaciones Diarias",
  "Start-of-shift and end-of-shift submissions": "Envíos al inicio y al final del turno",
  "Weekly Checks": "Inspecciones Semanales",
  "Lead-driven recurring inspections": "Inspecciones recurrentes dirigidas por el líder",
  "Calculators & Tools": "Calculadoras y Herramientas",
  "Supporting field calculators": "Calculadoras de apoyo para el campo",
  "START FORM": "INICIAR FORMULARIO",
  "START DVIR": "INICIAR DVIR",
  "START SHIFT": "INICIAR TURNO",
  "Driver Shift Start": "Inicio de Turno del Conductor",
  "Truck drivers check in here at the start of every shift. Pick your name and truck — no password, no app.": "Los camioneros se registran aquí al inicio de cada turno. Selecciona tu nombre y tu camión — sin contraseña, sin aplicación.",
  "Field Reporting": "Reportes de Campo",
  "End-of-day operational memory": "Memoria operativa de fin de día",
  "Equipment Operations": "Operaciones de Equipo",
  "Daily OSHA equipment readiness": "Preparación diaria OSHA del equipo",
  "Trucking Operations": "Operaciones de Camiones",
  "Shift activation · daily readiness · recurring continuity": "Activación de turno · preparación diaria · continuidad recurrente",

  // ─── iter405 · Phase 13.2 · DLS targeted i18n sweep ────────────
  // ShiftStart driver-facing chrome
  "Operational check-in": "Registro operativo",
  "Start your shift": "Inicia tu turno",
  "Pick who's driving and which truck. Subs and rentals aren't in the system yet — tap": "Selecciona quién conduce y qué camión. Los subcontratistas y rentas aún no están en el sistema — toca",
  "Add temporary": "Agregar temporal",
  "if needed.": "si es necesario.",
  "Driver name": "Nombre del conductor",
  "Type a name to search": "Escribe un nombre para buscar",
  "Truck number": "Número de camión",
  "Pick a truck or type unit number": "Selecciona un camión o escribe el número",
  "Trailer number": "Número de remolque",
  "optional": "opcional",
  "If you're pulling one": "Si llevas uno",
  "Company / Hauler": "Compañía / Transportista",
  "Search or add": "Buscar o agregar",
  "Starting…": "Iniciando…",
  "Start shift": "Iniciar turno",
  "No password. No app. Just check in.": "Sin contraseña. Sin aplicación. Solo registra tu llegada.",
  "Could not start shift. Try again.": "No se pudo iniciar el turno. Intenta de nuevo.",
  // Searchable select chrome
  "temp": "temp",
  "change": "cambiar",
  "Looking…": "Buscando…",
  "Type at least 2 letters to search.": "Escribe al menos 2 letras para buscar.",
  "No matches yet.": "Sin coincidencias todavía.",
  "Add temporary:": "Agregar temporal:",
  "Add temporary driver:": "Agregar conductor temporal:",
  "Add temporary truck:": "Agregar camión temporal:",
  "Add temporary trailer:": "Agregar remolque temporal:",
  "Add carrier / hauler:": "Agregar transportista:",
  // DriverShift current-state labels
  "Current state": "Estado actual",
  "Assigned · ready to roll": "Asignado · listo para salir",
  "En route to load": "En ruta a cargar",
  "At load site": "En el sitio de carga",
  "Loading": "Cargando",
  "Loaded · secure your ticket": "Cargado · asegura tu boleta",
  "En route to job": "En ruta al trabajo",
  "Arrived at job": "Llegada al trabajo",
  "Dumping": "Descargando",
  "Complete — start next cycle when dispatched": "Completo — inicia el siguiente ciclo cuando se asigne",
  "Waiting": "Esperando",
  "On hold": "En espera",
  "Breakdown": "Avería",
  "Off shift": "Fuera de turno",
  // DriverShift body
  "Connection failed — retrying…": "Falló la conexión — reintentando…",
  "Could not record that. Try again.": "No se pudo registrar. Intenta de nuevo.",
  "Connection failed — try again.": "Falló la conexión — intenta de nuevo.",
  "Loading your shift…": "Cargando tu turno…",
  "No active haul right now": "Sin acarreo activo ahora mismo",
  "Dispatch will assign your next cycle. This screen will update on its own — keep it open in your phone.": "Despacho asignará tu siguiente ciclo. Esta pantalla se actualizará sola — mantenla abierta en tu teléfono.",
  "Sign out": "Cerrar sesión",
  "Driver shift": "Turno del conductor",
  "Truck": "Camión",
  "Reason": "Motivo",
  "Job": "Trabajo",
  "No next step — dispatch will pick this up.": "Sin siguiente paso — despacho lo retomará.",
  "Waiting…": "Esperando…",
  "Hold": "Espera",
  "End shift": "Terminar turno",
  "What are you waiting on?": "¿Qué estás esperando?",
  "Cancel": "Cancelar",
  // Wait reasons (short labels)
  "Plant": "Planta",
  "Loader": "Cargador",
  "Dump": "Descarga",
  "Paver": "Pavimentadora",
  "Traffic": "Tráfico",
  "Lane closure": "Cierre de carril",
  "Next dispatch": "Próximo despacho",
  "Staging": "Preparación",
  // DispatchBoard chrome
  "Operational signals": "Señales operativas",
  "finding requires operational attention.": "hallazgo requiere atención operativa.",
  "findings require operational attention.": "hallazgos requieren atención operativa.",
  "No active findings.": "Sin hallazgos activos.",
  "breakdown": "avería",
  "breakdowns": "averías",
  "stuck": "atorado",
  "long wait": "espera larga",
  "long waits": "esperas largas",
  "pattern": "patrón",
  "patterns": "patrones",
  // DispatchBoard summary tiles
  "Active hauls": "Acarreos activos",
  "Stuck": "Atorado",
  // DispatchBoard state chips (short)
  "Assigned": "Asignado",
  "En route · load": "En ruta · carga",
  "At load": "En carga",
  "En route · job": "En ruta · trabajo",
  "At job": "En trabajo",
  "Complete": "Completo",
  // DispatchBoard exports
  "Operational exports (CSV)": "Exportaciones operativas (CSV)",
  "Assignments": "Asignaciones",
  "State events": "Eventos de estado",
  "Haul cycles": "Ciclos de acarreo",
  "Export failed": "Falló la exportación",
  "Export failed — check connection.": "Falló la exportación — revisa la conexión.",
  "Export downloaded": "Exportación descargada",
  "Truck-level finding — open the row directly to act.": "Hallazgo a nivel de camión — abre la fila directamente para actuar.",
  "Removed from active board": "Removido del tablero activo",
  "Assignment not on active board — likely already cleared.": "La asignación no está en el tablero activo — probablemente ya fue limpiada.",
  // DispatchBoard rows
  "Unassigned project": "Proyecto sin asignar",
  "m in state": "m en estado",
  "tap for actions": "toca para acciones",
  // DispatchBoard header + title card
  "Dispatch Hub": "Centro de Despacho",
  "Operational Board": "Tablero Operativo",
  "Dispatch Lifecycle System": "Sistema de Ciclo de Vida del Despacho",
  "Live operational flow": "Flujo operativo en vivo",
  "Every active haul, one card. Tap a row to see history, issue a driver magic link, cancel, reassign, or revoke a session. Refreshes every": "Cada acarreo activo, una tarjeta. Toca una fila para ver el historial, emitir un enlace mágico, cancelar, reasignar o revocar una sesión. Se actualiza cada",
  "seconds.": "segundos.",
  "Refresh": "Actualizar",
  // LifecycleGuide section labels + bodies
  "What this board is telling you": "Lo que este tablero te está diciendo",
  "Calm operational truth · forgiving transitions · governance signals": "Verdad operativa calmada · transiciones tolerantes · señales de gobernanza",
  "Lifecycle": "Ciclo de vida",
  "Every truck moves through 13 canonical states. Non-standard transitions are accepted but tagged so operations are never blocked. See the glossary for full definitions.": "Cada camión pasa por 13 estados canónicos. Las transiciones no estándar se aceptan pero se etiquetan, las operaciones nunca se bloquean. Consulta el glosario para definiciones completas.",
  "Findings": "Hallazgos",
  "Four signals only — BREAKDOWN_ACTIVE (critical), ASSIGNMENT_STUCK (≥30 min in non-terminal state), WAIT_THRESHOLD_EXCEEDED (≥20 min in WAITING), NON_STANDARD_TRANSITION_PATTERN (≥3 non-standard transitions in 2h per truck). Nothing else fires.": "Solo cuatro señales — BREAKDOWN_ACTIVE (crítica), ASSIGNMENT_STUCK (≥30 min en estado no terminal), WAIT_THRESHOLD_EXCEEDED (≥20 min en WAITING), NON_STANDARD_TRANSITION_PATTERN (≥3 transiciones no estándar en 2h por camión). Nada más se dispara.",
  "Roles": "Roles",
  "Dispatch and Admin act here. Drivers act on the magic-link mobile screen. PM and Shop see project- and breakdown-scoped signals on their own hubs. Safety, FL, and HR remain operationally quiet on DLS by design — restraint until live operations tell us where signal-surfacing actually helps.": "Despacho y Admin actúan aquí. Los conductores actúan en la pantalla móvil del enlace mágico. PM y Taller ven señales con alcance por proyecto y por avería en sus propios centros. Seguridad, FL y RH permanecen silenciosos en DLS por diseño — moderación hasta que las operaciones en vivo nos digan dónde la visibilidad realmente ayuda.",
  "Restraint": "Moderación",
  "Read-only · refreshes every 5 seconds · no chat, no maps, no analytics. The lifecycle engine is the single source of operational truth — every action here delegates to it so nothing gets out of sync.": "Solo lectura · se actualiza cada 5 segundos · sin chat, sin mapas, sin analítica. El motor de ciclo de vida es la única fuente de verdad operativa — cada acción aquí delega en él para que nada se desincronice.",
  // DispatchBoard error / empty / loading
  "Viewing tenant override:": "Viendo invalidación de inquilino:",
  "dev mode": "modo dev",
  "Loading operational board…": "Cargando tablero operativo…",
  "No active hauls right now.": "Sin acarreos activos ahora mismo.",
  "Trucks will appear here the moment dispatch creates an assignment.": "Los camiones aparecerán aquí en el momento en que despacho cree una asignación.",
  // DispatchLifecycleTile (PM / Shop / FL scopes)
  "Haul activity on your projects": "Actividad de acarreo en tus proyectos",
  "live dispatch signal · project-scoped": "señal de despacho en vivo · alcance por proyecto",
  "No haul activity currently affecting your projects.": "Sin actividad de acarreo afectando tus proyectos actualmente.",
  "Trucks in breakdown right now": "Camiones en avería ahora mismo",
  "operational downtime signal": "señal de tiempo inactivo operativo",
  "No trucks in BREAKDOWN — fleet operating cleanly.": "Sin camiones en AVERÍA — la flota opera limpiamente.",
  "Production-impacting haul signals": "Señales de acarreo que impactan producción",
  "starvation + extended wait": "desabasto + espera extendida",
  "No paving-impacting haul signals right now.": "Sin señales de acarreo que impacten pavimentación ahora.",
  "signal": "señal",
  "signals": "señales",
  "Read-only · refreshes every minute · dispatch owns these states.": "Solo lectura · se actualiza cada minuto · despacho es dueño de estos estados.",
  // AssignmentDrawer (high-visibility labels only)
  "Assignment": "Asignación",
  "No driver": "Sin conductor",
  "Close": "Cerrar",
  "Project": "Proyecto",
  "Material": "Material",
  "Assigned at": "Asignado en",
  "START LEAD INSPECTION": "INICIAR INSPECCIÓN DEL LÍDER",
  "START EMERGENCY CHECK": "INICIAR CHEQUEO DE EMERGENCIA",
  "OPEN TOOLS": "ABRIR HERRAMIENTAS",
  "OPEN": "ABRIR",
  "OPEN FORM": "ABRIR FORMULARIO",
  "NEW ENTRY": "NUEVO REGISTRO",
  "OPEN LIBRARY": "ABRIR BIBLIOTECA",
  "OPEN FLEET VIEW": "VER FLOTA",

  // iter320 · Shop + QA/QC Calm Pass
  "DVIR defects per truck · driver notes · current status · severity context.": "Defectos DVIR por camión · notas del conductor · estado actual · contexto de severidad.",
  "Inspection Forms": "Formularios de Inspección",
  "Routed, signed, photographed, and stored": "Enrutado, firmado, fotografiado y almacenado",

  // iter321 · Safety Section Calm Pass (Safety tile governance closure)
  "Compliance Forms & References": "Formularios y Referencias de Cumplimiento",
  "Crew-facing OSHA forms · job hazard plans · field references": "Formularios OSHA para la cuadrilla · planes de riesgo del trabajo · referencias de campo",
  "OPEN PLANS": "ABRIR PLANES",
  "OPEN CARDS": "ABRIR TARJETAS",
  "OPEN FORMS": "ABRIR FORMULARIOS",

  // iter322 · Portal continuity banner + auth-required banner
  "Back to": "Volver a",
  "You are viewing platform Guidance": "Estás viendo la Guía de la plataforma",
  "You are viewing Safety Forms": "Estás viendo Formularios de Seguridad",
  "Safety Forms · Sign-in required": "Formularios de Seguridad · Se requiere inicio de sesión",
  "Higher access required": "Se requiere mayor acceso",
  "{workflow} requires {role} sign-in.": "{workflow} requiere acceso de {role}.",
  "If you believe you should have access, contact your portal lead.": "Si crees que deberías tener acceso, contacta al líder de tu portal.",
  "This workflow": "Este flujo de trabajo",
  "elevated access": "acceso elevado",
  "Safety Portal": "Portal de Seguridad",
  "HR Portal": "Portal de RH",
  "Field Leadership": "Liderazgo de Campo",
  "Shop Portal": "Portal del Taller",
  "Dispatch Portal": "Portal de Despacho",

  // iter322-B · enriched AuthRequiredBanner copy + workflow labels
  "Sign-in required": "Se requiere iniciar sesión",
  "You selected {workflow} from {origin}.": "Seleccionaste {workflow} desde {origin}.",
  "This workflow requires {role} access.": "Este flujo requiere acceso de {role}.",
  "After sign-in, you'll continue to {workflow}.": "Después de iniciar sesión, continuarás a {workflow}.",

  // iter322-C · Job Site Safety Inspection surfacing
  "New Site Inspection": "Nueva Inspección de Sitio",
  "Every site safety audit and Job Site Safety Inspection — the records the field submits through": "Cada auditoría de seguridad de sitio e Inspección de Seguridad del Sitio de Trabajo — los registros que el campo envía a través de",
  "— organized for Safety review and corrective-action close-out.": "— organizados para revisión de Seguridad y cierre de acciones correctivas.",
  "Review every Job Site Safety Inspection submitted from the field · filter, search, drill in · start a new inspection from the same page.": "Revisa cada Inspección de Seguridad del Sitio enviada desde el campo · filtra, busca, profundiza · comienza una nueva inspección desde la misma página.",
  // Workflow labels (i18n keys = English label; t() falls back to EN
  // when an entry isn't present so this only needs the most-hit names).
  "Incident Reports": "Reportes de Incidentes",
  "Audits & Inspections": "Auditorías e Inspecciones",
  "Corrective Actions": "Acciones Correctivas",
  "Training & Certifications": "Capacitación y Certificaciones",
  "Employee Safety Profiles": "Perfiles de Seguridad del Empleado",
  "Fire Extinguishers": "Extintores",
  "Safety Document Library": "Biblioteca de Documentos de Seguridad",
  "Weekly Digest": "Resumen Semanal",
  "Reports & Exports": "Reportes y Exportaciones",
  "Trucking · Fleet": "Transporte · Flota",
  "Topic Library": "Biblioteca de Temas",
  "Change Password": "Cambiar Contraseña",
  "Employee Lifecycle": "Ciclo de Vida del Empleado",
  "Field Leadership Records": "Registros de Liderazgo de Campo",
  "Field Leadership Accounts": "Cuentas de Liderazgo de Campo",
  "Time Off Requests": "Solicitudes de Tiempo Libre",
  "Employee Accountability": "Responsabilidad del Empleado",
  "Time Verification": "Verificación de Tiempo",
  "Payroll Variance": "Variación de Nómina",
  "Training Records": "Registros de Capacitación",
  "Driver Qualification": "Calificación del Conductor",
  "Safety Records": "Registros de Seguridad",
  "Fleet Repair Queue": "Cola de Reparación de Flota",
  "Admin Console": "Consola de Administración",
  "Admin Portal": "Portal de Administración",
  "PM Portal": "Portal de PM",

  // iter332 · HR Daily Reports Review + Safety Forms entry CTAs
  "NEW EQUIPMENT ISSUANCE": "NUEVA ENTREGA DE EQUIPO",
  "NEW USE & CARE TRAINING": "NUEVA CAPACITACIÓN DE USO Y CUIDADO",
  "Back to Review": "Volver a Revisión",
  "Daily Reports Review": "Revisión de Reportes Diarios",
  "Read-only daily report visibility for payroll cross-checks · labor crews · subcontractors · vendors · attendance context. No edit or approval.": "Visibilidad de solo lectura para verificación de nómina · cuadrillas · subcontratistas · vendedores · contexto de asistencia. Sin edición ni aprobación.",
  "Read-only": "Solo lectura",
  "Back to HR": "Volver a RH",
  "Back to list": "Volver a la lista",
  "Read-only visibility into daily reports — labor crews, subcontractors, vendors, weather, location, and photo counts. No edit, no delete, no email, no approval.": "Visibilidad de solo lectura de reportes diarios — cuadrillas, subcontratistas, vendedores, clima, ubicación y conteo de fotos. Sin editar, sin eliminar, sin correo, sin aprobar.",
  "Reports": "Reportes",
  "Crews": "Cuadrillas",
  "Subs": "Subs",
  "Visitors": "Visitantes",
  "Date from": "Fecha desde",
  "Date to": "Fecha hasta",
  "Project": "Proyecto",
  "Report number": "Número de reporte",
  "Project name or number": "Nombre o número de proyecto",
  "Crew member name": "Nombre del miembro de cuadrilla",
  "Subcontractor": "Subcontratista",
  "Sub company name": "Nombre de la empresa sub",
  "Vendor / Visitor": "Vendedor / Visitante",
  "Vendor name": "Nombre del vendedor",
  "Apply": "Aplicar",
  "No daily reports match these filters.": "Ningún reporte diario coincide con estos filtros.",
  "Report #": "Reporte #",
  "Prepared by": "Preparado por",
  "Failed to load daily reports": "No se pudieron cargar los reportes diarios",
  "Failed to load report": "No se pudo cargar el reporte",
  "Report not found.": "Reporte no encontrado.",
  "Daily Report": "Reporte Diario",
  "Weather": "Clima",
  "MASCI Crews": "Cuadrillas MASCI",
  "Subcontractors": "Subcontratistas",
  "Crew size": "Tamaño de cuadrilla",
  "Visitors / Vendors": "Visitantes / Vendedores",
  "Narrative": "Narrativa",
  "Photos": "Fotos",
  "Crew": "Cuadrilla",
  "This is a read-only HR view. To edit or send this report, the PM must use the PM Portal.": "Esta es una vista de solo lectura para RH. Para editar o enviar este reporte, el PM debe usar el Portal de PM.",

  // iter333 · Final Operational Coaching Convergence · iter327 voice
  // ─ Submit-success continuity toasts ─
  "Incident report filed · Safety + PM notified · visible under Incidents": "Reporte de accidente archivado · Seguridad + PM notificados · visible en Incidentes",
  "Daily report filed · PM distribution sent · visible under Daily Reports": "Reporte diario archivado · distribución de PM enviada · visible en Reportes Diarios",
  "Inspection filed · graded · visible under Audits & Inspections": "Inspección archivada · calificada · visible en Auditorías e Inspecciones",
  "Issuance filed · PDF emailed to Safety · visible in Safety Forms Records": "Entrega archivada · PDF enviado a Seguridad · visible en Registros de Formularios",
  "Training filed · PDF emailed to Safety · visible in Safety Forms Records": "Capacitación archivada · PDF enviado a Seguridad · visible en Registros de Formularios",
  // ─ Tier-1 form intros ─
  "Every detail filed here protects the crew, the project, and the company. Write it the way you'd want to read it six months from now.": "Cada detalle archivado aquí protege a la cuadrilla, al proyecto y a la empresa. Escríbelo como te gustaría leerlo dentro de seis meses.",
  "One report per crew, per day. Capture labor, subs, materials, weather, and photos so payroll and PM coordination run clean tomorrow.": "Un reporte por cuadrilla, por día. Captura mano de obra, subs, materiales, clima y fotos para que la nómina y la coordinación del PM corran limpias mañana.",
  "A walking record of what's safe, what isn't, and what was fixed today. Honest grades drive better jobs.": "Un registro caminado de lo que es seguro, lo que no, y lo que se corrigió hoy. Las calificaciones honestas hacen mejores trabajos.",
  "Walk it before you roll it. Mark every item honestly. A FAIL today is a downed truck — and a tomorrow you can plan for, not one that surprises you.": "Camínalo antes de moverlo. Marca cada ítem honestamente. Un FALLO hoy es un camión fuera — y un mañana que puedes planear, no uno que te sorprenda.",
  // ─ "What good looks like" placeholders ─
  "What happened, who was involved, what equipment or materials were present, and what was done in the moment. Write it like you'd brief the Safety Manager on a phone call.": "Qué pasó, quién estuvo involucrado, qué equipo o materiales estaban presentes, y qué se hizo en el momento. Escríbelo como si le informaras al Gerente de Seguridad por teléfono.",
  "Specific changes that prevent this from happening again — training, procedure updates, equipment fixes, supervision changes.": "Cambios específicos que previenen que esto vuelva a pasar — capacitación, actualizaciones de procedimiento, reparaciones de equipo, cambios de supervisión.",
  "What was the issue, where on site, what was done about it, and who owns the follow-up. Specific beats general — name the location, the trade, the action.": "Cuál fue el problema, dónde en el sitio, qué se hizo al respecto, y quién dirige el seguimiento. Específico le gana a general — nombra el lugar, el oficio, la acción.",
  "Describe the defect — what you saw, heard, or felt. Where on the unit. When it started. Be specific so Shop knows what to grab.": "Describe el defecto — qué viste, escuchaste o sentiste. Dónde en la unidad. Cuándo empezó. Sé específico para que el Taller sepa qué traer.",
  // ─ Empty-state guidance ─
  "No daily reports match these filters. Try a wider date range or clear all filters to see everything on file.": "Ningún reporte diario coincide con estos filtros. Prueba un rango de fechas más amplio o limpia todos los filtros para ver todo en archivo.",

  // iter334 · Public Submission Thank-You Continuity · iter327 voice
  "Filed.": "Archivado.",
  "On file": "En archivo",
  "File Another": "Archivar Otro",
  "Safety has it. If additional information is needed, the team will follow up.": "Seguridad lo tiene. Si se necesita información adicional, el equipo dará seguimiento.",
  "Operations, payroll, and project leadership can now review today's activity.": "Operaciones, nómina y liderazgo del proyecto ya pueden revisar la actividad de hoy.",
  "Findings and corrective actions are now visible in Safety Review.": "Los hallazgos y las acciones correctivas ya están visibles en Revisión de Seguridad.",
  "Issuance recorded. Equipment accountability and return status are now tracked.": "Entrega registrada. La responsabilidad del equipo y el estado de devolución ya están en seguimiento.",
  "Training recorded. Use and care accountability is now tracked.": "Capacitación registrada. La responsabilidad de uso y cuidado ya está en seguimiento.",
  "Defect log filed. Shop has visibility for tomorrow's planning.": "Registro de defecto archivado. El Taller tiene visibilidad para la planeación de mañana.",
  "Meeting recorded. Attendance and topics are now on file.": "Reunión registrada. La asistencia y los temas ya están en archivo.",
  "JHA filed. The plan is available for the crew and Safety review.": "JHA archivada. El plan está disponible para la cuadrilla y la revisión de Seguridad.",
  "Pre-op log filed. Shop and supervision have visibility for the day's run.": "Inspección pre-operacional archivada. El Taller y la supervisión tienen visibilidad para la jornada.",
  "The right people have visibility. You're done unless contacted.": "Las personas correctas tienen visibilidad. Has terminado a menos que te contacten.",
  // formType label translations (used by t(formType) in the kicker)
  "Incident Report": "Reporte de Accidente",
  "Daily Report": "Reporte Diario",
  "Equipment Issuance": "Entrega de Equipo",
  "Equipment Training": "Capacitación de Equipo",
  "Toolbox Meeting": "Reunión de Caja de Herramientas",
  // iter335 · Submission tracking reference label
  "Ref": "Ref.",

  // iter338 · Admin Reference Lookup
  "Admin Utility": "Utilidad de Admin",
  "Find Record by Ref": "Buscar Registro por Ref.",
  "Paste a canonical reference to jump straight to the record.": "Pega una referencia canónica para ir directo al registro.",
  "Paste Ref · INC-2026-0517-002": "Pega Ref. · INC-2026-0517-002",
  "Find": "Buscar",
  "No active record matches Ref": "Ningún registro activo coincide con Ref.",
  "Lookup unavailable. Try again in a moment.": "Búsqueda no disponible. Intenta de nuevo en un momento.",

  // iter339 · HR Daily Reports calm error sanitization (no raw "Not Found" leak)
  "Daily Reports temporarily unavailable. Try again in a moment.": "Los Reportes Diarios no están disponibles temporalmente. Intenta de nuevo en un momento.",
  "That report is temporarily unavailable. Try again in a moment.": "Ese reporte no está disponible temporalmente. Intenta de nuevo en un momento.",
  "Your HR session expired. Please sign in again.": "Tu sesión de RH expiró. Por favor, inicia sesión de nuevo.",

  // iter342 · FL login convergence — modern per-user login is now primary
  "Crew using a shared leadership code? Use the legacy gate →": "¿Tu cuadrilla usa un código compartido? Usa el acceso heredado →",

  // iter343 · FL login chrome rebuild — full platform-family parity with HR
  "Field Leadership": "Liderazgo de Campo",
  "Field Leadership Sign In": "Inicio de Sesión · Liderazgo de Campo",
  "Sign in with your MASCI work email. For approved Field Leadership personnel — Superintendents, Foremen, Truck Bosses, and Working Supervisors. If this is your first time, the admin or HR will give you a temporary password — you'll choose your own on first login.":
    "Inicia sesión con tu correo de trabajo de MASCI. Solo para personal aprobado de Liderazgo de Campo — Superintendentes, Capataces, Jefes de Camión y Supervisores Operativos. Si es tu primera vez, el admin o RH te darán una contraseña temporal — eligirás la tuya al iniciar sesión por primera vez.",
  "Enter your work email and password": "Ingresa tu correo de trabajo y contraseña",
  "Invalid email or password": "Correo o contraseña incorrectos",
  "Account is disabled — call the office to reactivate": "Cuenta deshabilitada — llama a la oficina para reactivarla",
  "Too many attempts — wait a minute and try again": "Demasiados intentos — espera un minuto e intenta de nuevo",
  "Request timed out — server is cold-starting, try again": "Se agotó el tiempo de espera — el servidor está iniciando, intenta de nuevo",
  "Can't reach server — check your internet": "No se puede conectar al servidor — revisa tu internet",
  "Sign in failed — try again or call the office": "Inicio de sesión fallido — intenta de nuevo o llama a la oficina",
  "Your session expired. Please sign in again.": "Tu sesión expiró. Por favor, inicia sesión de nuevo.",
  "Welcome,": "Bienvenido,",
  "Field Leader": "Líder de Campo",
  "Forgot password? Click the link above and we'll email you a reset. Or call the office — admin or HR can issue a fresh temp password from the console.":
    "¿Olvidaste tu contraseña? Haz clic en el enlace arriba y te enviaremos un correo para restablecerla. O llama a la oficina — el admin o RH pueden emitir una contraseña temporal nueva desde la consola.",
  "Enter your work email. If we have you on file with an active Field Leadership account, we'll email you a one-time link to set a new password. Link expires in 30 minutes.":
    "Ingresa tu correo de trabajo. Si te tenemos en archivo con una cuenta activa de Liderazgo de Campo, te enviaremos un enlace de un solo uso para establecer una nueva contraseña. El enlace expira en 30 minutos.",
  "Couldn't send reset email — try again or call the office": "No se pudo enviar el correo de restablecimiento — intenta de nuevo o llama a la oficina",
  "If that email is on file, a reset link is on its way.": "Si ese correo está en archivo, un enlace de restablecimiento está en camino.",
  "MASCI · Field Leadership Portal": "MASCI · Portal de Liderazgo de Campo",
  "You're already signed in as Admin": "Ya iniciaste sesión como Admin",
  "Admin tokens already satisfy the Field Leadership Hub gate — you do not need to sign in here.":
    "Los tokens de Admin ya cumplen con el acceso al Centro de Liderazgo de Campo — no necesitas iniciar sesión aquí.",
  "Continue to Field Leadership Hub": "Continuar al Centro de Liderazgo de Campo",

  // J · NewDailyReport.jsx (composite size-warning sentence)
  " estimated).": " estimado).",
  "Still submittable. For very large evidence sets consider splitting into multiple reports so each stays well under the size limit.": "Aún se puede enviar. Para conjuntos de evidencia muy grandes, considere dividir en varios reportes para que cada uno quede bien por debajo del límite de tamaño.",
  "This report has": "Este reporte tiene",
  "photo(s) attached (≈": "foto(s) adjunta(s) (≈",

  // iter346-A · EditProjectDialog i18n closure (English leak fix)
  "Edit Project": "Editar Proyecto",
  "Re-tag this report": "Re-etiquetar este reporte",
  "Change the project this record is filed under. Signatures, photos, narrative, and checklist data stay untouched.": "Cambia el proyecto bajo el cual está archivado este registro. Las firmas, fotos, narrativa y datos de la lista de verificación permanecen intactos.",
  "Currently filed under": "Actualmente archivado bajo",
  "Move to": "Mover a",
  "Project name is required": "Se requiere el nombre del proyecto",
  "Project updated": "Proyecto actualizado",
  "Failed to update project — try again": "No se pudo actualizar el proyecto — intenta de nuevo",

  // iter346-A · AdminAccessStatsTile (admin-only quick visibility)
  "Access Control · Quick Stats": "Control de Acceso · Estadísticas Rápidas",
  "Total Users": "Usuarios Totales",
  "Total Grants": "Permisos Totales",
  "Cross-Portal": "Multi-Portal",
  "Disabled": "Deshabilitados",
  "Access stats temporarily unavailable.": "Estadísticas de acceso no disponibles temporalmente.",

  // iter346-B · universal super-admin login fallback (welcome toast
  // when super-admin signs in via any portal login).
  "Welcome, Admin": "Bienvenido, Administrador",

  // iter353e-UI · PM Crew Compliance surface (read-only operational awareness).
  "My Crew Compliance": "Cumplimiento de Mi Cuadrilla",
  "Read-only operational awareness for the crews on your projects. Scope: every employee on a daily report under your projects in the last 180 days. For corrections, contact HR or Safety — this view is read-only.": "Visibilidad operativa de solo lectura para las cuadrillas en tus proyectos. Alcance: cada empleado en un reporte diario bajo tus proyectos en los últimos 180 días. Para correcciones, contacta a Recursos Humanos o Seguridad — esta vista es de solo lectura.",
  "Crew size (180d)": "Tamaño de cuadrilla (180d)",
  "Training expiring ≤30d": "Capacitación venciendo ≤30d",
  "Training expired": "Capacitación vencida",
  "Open CAPAs": "CAPAs Abiertas",
  "PPE records": "Registros de EPP",
  "Read-only PM operational awareness.": "Visibilidad operativa de PM (solo lectura).",
  "My crew · 180d": "Mi cuadrilla · 180d",
  "Admin all": "Admin total",
  "Updated": "Actualizado",
  "Could not load crew compliance.": "No se pudo cargar el cumplimiento de la cuadrilla.",
  "Employee · training · equipment · CAPA": "Empleado · capacitación · equipo · CAPA",
  "Refresh": "Actualizar",
  "Training": "Capacitación",
  "PPE": "EPP",
  "CAPAs": "CAPAs",
  "Showing expired only": "Mostrando solo vencidas",
  "Showing expiring ≤30d": "Mostrando venciendo ≤30d",
  "Clear filter": "Limpiar filtro",
  "No training records match the current filter.": "Ningún registro de capacitación coincide con el filtro actual.",
  "No PPE issuance records yet.": "Aún no hay registros de entrega de EPP.",
  "No open CAPAs involving crew.": "No hay CAPAs abiertas que involucren a la cuadrilla.",
  "Employee": "Empleado",
  "Completed": "Completado",
  "Expires": "Vence",
  "Severity": "Severidad",
  "Equipment": "Equipo",
  "Issued": "Entregado",
  "Condition": "Condición",
  "CAPA": "CAPA",
  "Status": "Estado",
  "Due": "Vence",
  "Done": "Listo",
  "Exp": "Vence",
  "Current": "Vigente",
  "Expired": "Vencido",
  "≤30d": "≤30d",
  "Search": "Buscar",

  // iter356 · Operational coaching standard (LifecycleGuide + CAPA lifecycle).
  "Lifecycle Guide": "Guía de Ciclo de Vida",
  "Don't show this again": "No mostrar de nuevo",
  "CAPA Lifecycle": "Ciclo de vida de la CAPA",
  "Open → In Progress → Pending Review → Verified → Closed (illegal jumps are blocked)": "Abierto → En Progreso → Revisión Pendiente → Verificada → Cerrada (los saltos ilegales se bloquean)",
  "Open → In Progress → Pending Review → Verified → Closed": "Abierto → En Progreso → Revisión Pendiente → Verificada → Cerrada",
  "Roles": "Roles",
  "Safety owns CAPA governance — create, edit, advance, verify, close. HR adds labor/accountability notes only (no Safety override). PM and FL get read-only visibility on records affecting their crews. Admin keeps supervisory authority.": "Seguridad gobierna las CAPAs — crear, editar, avanzar, verificar, cerrar. RRHH solo añade notas laborales/de responsabilidad (sin anular a Seguridad). PM y FL tienen visibilidad de solo lectura sobre los registros que afectan a sus cuadrillas. Admin mantiene autoridad supervisora.",
  "Lifecycle gate": "Compuerta del ciclo de vida",
  "A CAPA cannot move directly from Pending Review to Closed. It must pass through Verified — a separate review step that confirms the corrective work actually happened. The verifier is stamped onto the record.": "Una CAPA no puede pasar directamente de Revisión Pendiente a Cerrada. Debe pasar por Verificada — un paso de revisión separado que confirma que el trabajo correctivo realmente ocurrió. El verificador queda registrado.",
  "Downstream visibility": "Visibilidad descendente",
  "Open and Verified CAPAs surface on the PM Crew Compliance lens, HR Accountability Timeline, Governance Health dashboard, and Compliance Findings. Closed CAPAs remain in the audit trail forever.": "Las CAPAs Abiertas y Verificadas aparecen en el Cumplimiento de Cuadrilla del PM, la Línea de Tiempo de Responsabilidad de RRHH, el panel de Salud de Gobernanza y los Hallazgos de Cumplimiento. Las CAPAs Cerradas permanecen en el registro de auditoría para siempre.",
  "Why this matters": "Por qué importa",
  "Open CAPAs that never close are silent operational debt. Severe incidents without a CAPA are a governance failure surfaced by Governance Health. Every status change is appended to the CAPA's status_history for OSHA / DOT / insurance review.": "Las CAPAs Abiertas que nunca cierran son deuda operativa silenciosa. Los incidentes graves sin CAPA son una falla de gobernanza expuesta por Salud de Gobernanza. Cada cambio de estado se añade al status_history de la CAPA para revisión OSHA / DOT / aseguradora.",
  "Track every safety deficiency to resolution. Auto-link CAs to incidents, audits, inspections, training records, and meetings. The pipeline is": "Lleva cada deficiencia de seguridad hasta la resolución. Vincula automáticamente las CAs a incidentes, auditorías, inspecciones, registros de capacitación y reuniones. La canalización es",

  // iter357 · Operational Intelligence Notifications (Phase 2 P1).
  "Today's intelligence": "Inteligencia de hoy",
  "Operational digest": "Resumen operativo",
  "Generated": "Generado",
  "Sign in to see today's intelligence": "Inicia sesión para ver la inteligencia de hoy",
  "Each portal has a role-scoped digest. Sign into Safety or Admin to view yours.": "Cada portal tiene un resumen según el rol. Inicia sesión en Seguridad o Admin para ver el tuyo.",
  "How notifications work": "Cómo funcionan las notificaciones",
  "Role-scoped · severity-aware · sourced from the live detection engine · in-platform first, email follows.": "Por rol · por severidad · alimentadas desde el motor de detección en vivo · primero dentro de la plataforma, luego por correo.",
  "What this is": "Qué es esto",
  "Your daily operational priorities. Generated from the live compliance findings + lifecycle state — no hand-curated lists, no spam. Each item points at a workflow you can resolve right now.": "Tus prioridades operativas diarias. Generado desde los hallazgos de cumplimiento y el estado de ciclo de vida en vivo — sin listas curadas a mano, sin spam. Cada elemento apunta a un flujo que puedes resolver ahora.",
  "How items are chosen": "Cómo se eligen los elementos",
  "Every section maps to a detector rule from Governance Health. If a rule has zero open findings for you, it doesn't appear here. Items disappear automatically once the underlying condition is fixed or acknowledged.": "Cada sección mapea a una regla detectora de Salud de Gobernanza. Si una regla tiene cero hallazgos abiertos para ti, no aparece aquí. Los elementos desaparecen automáticamente cuando la condición subyacente se corrige o se reconoce.",
  "What to do": "Qué hacer",
  "Open the View link on any section to act inside the relevant portal. Acknowledge or resolve from Compliance Findings; advance CAPAs from Safety Corrective Actions. Every action is audit-trailed.": "Abre el enlace Ver en cualquier sección para actuar dentro del portal correspondiente. Reconoce o resuelve desde Hallazgos de Cumplimiento; avanza las CAPAs desde Acciones Correctivas de Seguridad. Cada acción queda registrada en auditoría.",
  "Operational risk surfaces here before it becomes a meeting, a citation, or an injury. Treating this digest as the start of every day is the cheapest insurance the platform offers.": "El riesgo operativo aparece aquí antes de convertirse en una reunión, una citación o una lesión. Tratar este resumen como el inicio de cada día es el seguro más barato que la plataforma ofrece.",
  "Convergence score": "Puntuación de convergencia",
  "Overdue CAPAs": "CAPAs vencidas",
  "Need a CAPA": "Necesitan CAPA",
  "Pending verification": "Verificación pendiente",
  "No owner": "Sin responsable",
  "Closed w/ open CAPA": "Cerrado con CAPA abierta",
  "Expired training": "Capacitación vencida",
  "No operational signal today.": "No hay señal operativa hoy.",
  "Every monitored rule is clean for your role. Detection runs continuously — this surface refreshes the moment something changes.": "Cada regla monitoreada está limpia para tu rol. La detección corre de forma continua — esta vista se actualiza en cuanto algo cambia.",

  // iter358 · digest expansion (HR / PM / Dispatch / FL summary tile labels).
  "Linkage failures": "Fallas de vinculación",
  "Driver creds expired": "Credenciales de conductor vencidas",
  "Expiring ≤30d": "Vence en ≤30d",
  "Archived but active": "Archivado pero activo",
  "CAPAs past due": "CAPAs vencidas",
  "No PPE": "Sin EPP",
  "Drivers unavailable": "Conductores no disponibles",
  "Med card expired": "Tarjeta médica vencida",
  "CDL expired": "CDL vencido",
  "Incidents need CAPA": "Incidentes necesitan CAPA",

  // iter358 · Operational Language glossary.
  "Operational meaning": "Significado operativo",
  "Lifecycle meaning": "Significado en el ciclo de vida",
  "Accountability": "Responsabilidad",
  "Search any term, definition, or workflow concept": "Busca cualquier término, definición o concepto de flujo de trabajo",
  "No glossary entries match. Try a broader term.": "Ningún término del glosario coincide. Intenta con un término más amplio.",
  "One vocabulary across the platform. \"Archive\" means the same thing in HR as in Safety; \"Closeout\" means the same thing on a CAPA as on an incident; \"Driver Qualified\" means the same thing in Dispatch as in FL. This page is the canonical reference — every LifecycleGuide should link to the relevant entry here.": "Un vocabulario en toda la plataforma. \"Archivar\" significa lo mismo en RRHH que en Seguridad; \"Cierre\" significa lo mismo en una CAPA que en un incidente; \"Conductor Cualificado\" significa lo mismo en Despacho que en FL. Esta página es la referencia canónica — cada Guía de Ciclo de Vida debería enlazar a la entrada relevante aquí.",
  "Why this glossary exists": "Por qué existe este glosario",
  "Single source of operational truth · EN + ES parity · versioned in code.": "Fuente única de verdad operativa · paridad EN + ES · versionado en código.",
  "Every operational term the platform uses, with the same meaning in every portal. When in doubt, link here from a LifecycleGuide, an internal Slack thread, or a meeting deck.": "Cada término operativo que usa la plataforma, con el mismo significado en cada portal. En caso de duda, enlaza aquí desde una Guía de Ciclo de Vida, un hilo interno de Slack o una presentación de reunión.",
  "How it's maintained": "Cómo se mantiene",
  "Entries live in the codebase, not a CMS. Adding or changing a definition is a Git commit — the commit history IS the audit trail. ES parity is required for every entry.": "Las entradas viven en el código fuente, no en un CMS. Añadir o cambiar una definición es un commit de Git — el historial de commits ES el registro de auditoría. La paridad ES es obligatoria para cada entrada.",
  "How to use it": "Cómo usarlo",
  "Search the bar below. Or deep-link to a specific entry — every entry has an anchor like /admin/operational-language#capa.": "Busca en la barra de abajo. O usa un enlace directo a una entrada específica — cada entrada tiene un ancla como /admin/operational-language#capa.",
  "Vocabulary drift between departments is the cheapest source of operational chaos in a multi-portal platform. One word, one meaning, everywhere — every time.": "La deriva de vocabulario entre departamentos es la fuente más barata de caos operativo en una plataforma multi-portal. Una palabra, un significado, en todas partes — cada vez.",

  // iter359 · UI-level Employee Linkage Enforcement (EmployeeRosterField).
  "Linked to employee master": "Vinculado al maestro de empleados",
  "Type name to search roster": "Escribe un nombre para buscar en el roster",
  "Searching…": "Buscando…",
  "No roster match.": "Sin coincidencia en el roster.",
  "Linked to roster": "Vinculado al roster",
  "Not in roster": "No está en el roster",
  "Saved as free-text. This will appear as an EMP_LINK_UNRESOLVABLE finding in Governance Health until you either pick from the roster or add this person to the employee master.": "Guardado como texto libre. Esto aparecerá como un hallazgo EMP_LINK_UNRESOLVABLE en Salud de Gobernanza hasta que selecciones del roster o agregues a esta persona al maestro de empleados.",
  "What does this mean?": "¿Qué significa esto?",

  // iter360 · Daily Report crew linkage.
  "Not in roster — will create governance finding": "No está en el roster — creará un hallazgo de gobernanza",
  "Crew identity linkage": "Vinculación de identidad de la cuadrilla",
  "Pick each crew member from the roster suggestions when possible — linked names propagate accountability automatically.": "Selecciona cada miembro de la cuadrilla desde las sugerencias del roster cuando sea posible — los nombres vinculados propagan la responsabilidad automáticamente.",
  "PMs and field leadership own daily-report submission. The crew names captured here feed every downstream surface that tracks who-was-where: HR accountability timelines, PM crew compliance, payroll reconciliation, and OSHA recordkeeping if an incident is later linked to today's date.": "Los PM y el liderazgo de campo son responsables del envío del reporte diario. Los nombres de la cuadrilla capturados aquí alimentan cada vista descendente que rastrea quién estuvo dónde: líneas de tiempo de responsabilidad de RRHH, cumplimiento de cuadrilla del PM, conciliación de nómina, y registros OSHA si un incidente se vincula después a la fecha de hoy.",
  "Why linkage matters": "Por qué importa la vinculación",
  "Names typed without picking from the roster become EMP_LINK_UNRESOLVABLE findings in Governance Health. Names picked from the roster carry the canonical employee_id, which makes accountability propagate to the right person automatically across every portal.": "Los nombres escritos sin seleccionar del roster se convierten en hallazgos EMP_LINK_UNRESOLVABLE en Salud de Gobernanza. Los nombres seleccionados del roster llevan el employee_id canónico, lo que hace que la responsabilidad se propague automáticamente a la persona correcta en todos los portales.",
  "Subcontractors": "Subcontratistas",
  "Free-text is allowed and intentionally never blocked — subcontractors aren't in the employee master. The amber indicator below the name just tells you the linkage state so the daily report still ships fast.": "El texto libre está permitido y nunca se bloquea intencionalmente — los subcontratistas no están en el maestro de empleados. El indicador ámbar debajo del nombre solo te dice el estado de vinculación para que el reporte diario siga saliendo rápido.",
  "Linked crew rows appear inside that employee's Accountability Timeline, on the PM Crew Compliance lens for the project, and (if relevant) inside any incident investigation that references today's date.": "Las filas de cuadrilla vinculadas aparecen dentro de la Línea de Tiempo de Responsabilidad de ese empleado, en el lente de Cumplimiento de Cuadrilla del PM para el proyecto, y (si aplica) dentro de cualquier investigación de incidente que haga referencia a la fecha de hoy.",

  // iter365 · LifecycleGuide retrofits (Incident Detail, Accountability Timeline, PM Crew Compliance, Driver Qualification / Dispatch Readiness).
  "Incident lifecycle": "Ciclo de vida del incidente",
  "Reported → Linked CAPA(s) → Verified → Closed. Closing without a verified CAPA is blocked.": "Reportado → CAPA(s) vinculada(s) → Verificada → Cerrada. No se permite cerrar sin una CAPA verificada.",
  "Every incident is tied to corrective actions. Closing the loop is how the crew learns and the next shift stays safe.": "Cada incidente está vinculado a acciones correctivas. Cerrar el ciclo es como la cuadrilla aprende y el próximo turno se mantiene seguro.",
  "Downstream": "Aguas abajo",
  "Safety, the PM, HR (for OSHA recordables), and the involved employee's accountability timeline all see this record.": "Seguridad, el PM, RRHH (para registros OSHA) y la línea de tiempo de responsabilidad del empleado involucrado ven este registro.",
  "How this timeline works": "Cómo funciona esta línea de tiempo",
  "One employee · every operational record from every portal · read-only.": "Un empleado · cada registro operativo de cada portal · solo lectura.",
  "If a CAPA, training, PPE, incident, or CDL/medical event touches this person, it shows up here. This is how the platform builds trust in the roster.": "Si una CAPA, capacitación, EPP, incidente o evento de CDL/médico afecta a esta persona, aparece aquí. Así es como la plataforma construye confianza en el roster.",
  "Source of truth": "Fuente de la verdad",
  "Corrections happen in the original portal — this view aggregates, it doesn't edit. The role pill on each row shows where the record was written.": "Las correcciones ocurren en el portal original — esta vista agrega, no edita. La etiqueta de rol en cada fila muestra dónde se escribió el registro.",
  "How your crew compliance view works": "Cómo funciona tu vista de cumplimiento de cuadrilla",
  "Read-only roll-up of everyone on your projects' daily reports in the last 180 days.": "Resumen de solo lectura de todos los que están en los reportes diarios de tus proyectos en los últimos 180 días.",
  "If someone on your crew has an expired training or missing PPE, you see it before the field does. Corrections happen in HR / Safety — not here.": "Si alguien en tu cuadrilla tiene una capacitación vencida o le falta EPP, lo ves antes que el campo. Las correcciones ocurren en RRHH / Seguridad — no aquí.",
  "How driver readiness works": "Cómo funciona la disponibilidad del conductor",
  "A driver is dispatchable only when active, approved, CDL valid (if CDL holder), and medical card valid.": "Un conductor está disponible para despacho solo cuando está activo, aprobado, con CDL vigente (si tiene CDL) y con tarjeta médica vigente.",
  "Sending an unqualified driver creates legal and safety exposure. The emerald tile above is your one-click 'who can I send right now' answer.": "Enviar a un conductor no calificado crea exposición legal y de seguridad. La tarjeta verde arriba es tu respuesta de un clic a '¿a quién puedo enviar ahora mismo?'.",
  "Status, CDL, and medical-card data are owned by HR. To correct anything, contact HR — this view never edits the source.": "Los datos de estado, CDL y tarjeta médica son propiedad de RRHH. Para corregir algo, contacta a RRHH — esta vista nunca edita la fuente.",

  // iter364 · FL records linkage indicator strings.
  "Saved as free-text. This will appear as an EMP_LINK_UNRESOLVABLE finding in Governance Health until you either pick from the roster or add this person to the employee master.": "Guardado como texto libre. Aparecerá como hallazgo EMP_LINK_UNRESOLVABLE en Salud de Gobernanza hasta que selecciones del roster o agregues a esta persona al maestro de empleados.",

  // iter367 · LifecycleGuide retrofit · HR Incidents.
  "HR · OSHA & Labor": "RR. HH. · OSHA y Laboral",
  "How HR sees incidents": "Cómo ve RR. HH. los incidentes",
  "Read-only view across the OSHA window. Closeout and CAPA action happen in the Safety portal.": "Vista de solo lectura sobre la ventana de OSHA. El cierre y la acción CAPA ocurren en el portal de Seguridad.",
  "HR owns OSHA recordkeeping and labor-side accountability. Spotting a recordable here triggers the 300/301 workflow even though the incident itself is owned by Safety.": "RR. HH. es responsable del registro OSHA y la rendición de cuentas laboral. Detectar un caso registrable aquí dispara el flujo 300/301 aunque el incidente sea propiedad de Seguridad.",
  "Every row links straight to the original Safety incident. If something looks wrong, fix it in Safety — this view aggregates and never edits.": "Cada fila enlaza directamente con el incidente original en Seguridad. Si algo se ve incorrecto, corrígelo en Seguridad — esta vista agrega y nunca edita.",

  // iter368 · ViewIncident · "Linked CAPAs" reverse-link section.
  "Linked CAPAs": "CAPAs vinculadas",
  "Owner": "Responsable",
  "Due": "Vence",

  // Phase 5D · P1 · ViewIncident follow-up awareness banner (rose/amber/emerald).
  "Follow-Up Required": "Requiere Seguimiento",
  "Investigation Open": "Investigación Abierta",
  "Operationally Complete": "Operativamente Completo",
  "What this means": "Qué significa",
  "Open Follow-Up CAPA": "Abrir CAPA de Seguimiento",
  "Tier-1 report is in. No CAPA has been opened yet. Open one to track the corrective work.": "El reporte inicial está registrado. Aún no se ha abierto una CAPA. Abre una para rastrear el trabajo correctivo.",
  "of": "de",
  "CAPA(s) verified ·": "CAPA(s) verificada(s) ·",
  "still in motion.": "aún en curso.",
  "All": "Todas",
  "linked CAPA(s) verified or closed. Audit trail preserved.": "las CAPAs vinculadas verificadas o cerradas. Pista de auditoría preservada.",

  // Phase 6 · WS3 · operational completion indicators on NewIncident + NewDailyReport.
  "Operationally complete": "Operativamente completo",
  "Operationally complete · ready to submit": "Operativamente completo · listo para enviar",
  "section(s) need attention": "sección(es) requieren atención",
  "Complete the highlighted section or mark it not used today.": "Completa la sección resaltada o márcala como no aplica hoy.",
  "Optional sections completed": "Secciones opcionales completadas",
  "Ready to submit · follow-up optional for this severity": "Listo para enviar · seguimiento opcional para esta severidad",
  "Optional sections available · add only what applies": "Secciones opcionales disponibles · agrega solo lo que aplique",
  "sections filled today": "secciones completadas hoy",
  "Delay details": "Detalles de demora",
  "Safety escalation": "Escalamiento de seguridad",
  "Attention": "Atención",
  "Status": "Estado",

  // ─── iter406 · Phase 14 · QR Shift Start Generator ──────────────
  "Physical Deployment": "Despliegue Físico",
  "Shift Start QR Generator": "Generador de QR · Inicio de Turno",
  "Print a QR sticker for the truck cab. Drivers scan, land on the public shift entry, pick their identity and start the shift. No password, no app install.":
    "Imprime una etiqueta QR para la cabina del camión. Los conductores escanean, llegan al inicio público de turno, eligen su identidad e inician el turno. Sin contraseña, sin aplicación.",
  "How operations uses this": "Cómo lo usa operaciones",
  "One QR per truck cab · scan · start shift · operate lifecycle":
    "Un QR por cabina · escanea · inicia turno · opera el ciclo",
  "Print": "Imprimir",
  "Fill the optional truck and carrier labels so operations can tell stickers apart. Tap Print, then choose 'Save as PDF' or send to your printer.":
    "Completa las etiquetas opcionales de camión y transportista para que operaciones pueda distinguir las etiquetas. Toca Imprimir y luego elige 'Guardar como PDF' o envíalo a la impresora.",
  "Place": "Colocar",
  "Stick the printed card on the inside of the driver's door, the visor, or the dash. Anywhere the driver can reach with their phone camera before they roll.":
    "Pega la tarjeta impresa en el interior de la puerta del conductor, en la visera o en el tablero. Cualquier lugar al que el conductor pueda apuntar la cámara antes de arrancar.",
  "Scan": "Escanear",
  "The driver opens their phone camera, points at the QR, taps the link. They land on the public shift entry and pick their identity from the platform's existing records — no enrollment, no app install.":
    "El conductor abre la cámara, apunta al QR y toca el enlace. Llega al inicio público de turno y elige su identidad de los registros existentes — sin inscripción, sin instalar nada.",
  "The QR is not tracked. There is no per-card audit log. This screen is a printer, not a system. If a sticker is damaged, print a new one — the QR target is the same public URL for every truck.":
    "El QR no se rastrea. No hay registro de auditoría por tarjeta. Esta pantalla es una impresora, no un sistema. Si una etiqueta se daña, imprime una nueva — el destino del QR es la misma URL pública para todos los camiones.",
  "Card details": "Detalles de la tarjeta",
  "Truck label": "Etiqueta del camión",
  "optional": "opcional",
  "e.g. T-21": "ej. T-21",
  "Printed at the top of the card so operations knows which truck this sticker belongs to.":
    "Se imprime en la parte superior de la tarjeta para que operaciones sepa a qué camión pertenece.",
  "Carrier": "Transportista",
  "Useful when printing sticker packs for subhauler fleets.":
    "Útil al imprimir paquetes de etiquetas para flotas subcontratadas.",
  "Tenant": "Inquilino",
  "dev only": "solo dev",
  "Leave blank for production": "Déjalo en blanco para producción",
  "Only set this when generating stickers for a non-default tenant (dev or pilot).":
    "Solo configúralo al generar etiquetas para un inquilino distinto al predeterminado (dev o piloto).",
  "Print card": "Imprimir tarjeta",
  "Open shift URL": "Abrir URL de turno",
  "DRIVER SHIFT START": "INICIO DE TURNO",
  "Truck cab": "Cabina del camión",
  "Scan to start your shift": "Escanea para iniciar tu turno",
  "Open camera · point at QR · tap link": "Abre la cámara · apunta al QR · toca el enlace",
  "No password · No app · Just tap": "Sin contraseña · Sin app · Solo toca",
  "Shift Start QR": "QR · Inicio de Turno",

  // ─── iter407 · Phase 14 · Dispatch Assignment Issuance ──────────
  "Create assignment": "Crear asignación",
  "Dispatch issuance": "Emisión de despacho",
  "Truck is required. Driver is optional — self-start can claim later. Pick a project and source so operational memory stays accurate. Wait reasons stay canonical (set later via the driver lifecycle).":
    "El camión es obligatorio. El conductor es opcional — el auto-inicio puede reclamarlo después. Elige un proyecto y origen para que la memoria operativa siga siendo precisa. Las razones de espera siguen siendo canónicas (se asignan después en el ciclo del conductor).",
  "Truck": "Camión",
  "Type a truck number": "Escribe un número de camión",
  "Add temporary truck:": "Agregar camión temporal:",
  "No matching truck. Type the unit number to add a temporary one.":
    "Sin coincidencias. Escribe el número de unidad para agregar uno temporal.",
  "Driver": "Conductor",
  "Type a driver name": "Escribe el nombre del conductor",
  "Add temporary driver:": "Agregar conductor temporal:",
  "No matching driver. Leave blank for self-start.":
    "Sin coincidencias. Déjalo vacío para auto-inicio.",
  "Trailer": "Tráiler",
  "Type a trailer number": "Escribe un número de tráiler",
  "Add temporary trailer:": "Agregar tráiler temporal:",
  "No matching trailer.": "Sin coincidencias.",
  "Add temporary carrier:": "Agregar transportista temporal:",
  "Add a one-time carrier.": "Agrega un transportista de una sola vez.",
  "Project": "Proyecto",
  "Project number": "Número de proyecto",
  "Add temporary project:": "Agregar proyecto temporal:",
  "Recent projects appear here as operations build memory.":
    "Los proyectos recientes aparecen aquí conforme operaciones acumula memoria.",
  "Source / load point": "Origen / punto de carga",
  "e.g. Plant 04, Pit 12": "ej. Planta 04, Pozo 12",
  "Add temporary source:": "Agregar origen temporal:",
  "Recent load points appear here as operations build memory.":
    "Los puntos de carga recientes aparecen aquí conforme operaciones acumula memoria.",
  "Destination": "Destino",
  "Job site or stockpile": "Sitio del trabajo o acopio",
  "Add temporary destination:": "Agregar destino temporal:",
  "Recent destinations appear here as operations build memory.":
    "Los destinos recientes aparecen aquí conforme operaciones acumula memoria.",
  "Material": "Material",
  "e.g. Base Rock, RAP, Hot Mix": "ej. Base, RAP, Mezcla Caliente",
  "Add temporary material:": "Agregar material temporal:",
  "Recent materials appear here as operations build memory.":
    "Los materiales recientes aparecen aquí conforme operaciones acumula memoria.",
  "Note": "Nota",
  "Anything the driver needs to know before they roll.":
    "Cualquier cosa que el conductor necesite saber antes de arrancar.",
  "Truck is required to issue an assignment.":
    "El camión es obligatorio para emitir una asignación.",
  "Issuance failed": "La emisión falló",
  "Assignment issued · truck on the board": "Asignación emitida · camión en el tablero",
  "Issuing…": "Emitiendo…",
  "Issue assignment": "Emitir asignación",
  "Truck appears on the board immediately. Driver lifecycle stays the source of operational truth.":
    "El camión aparece en el tablero de inmediato. El ciclo del conductor sigue siendo la fuente de verdad operativa.",
  "Close": "Cerrar",
  "Connection failed — try again.": "Conexión fallida — intenta de nuevo.",
  "No matches yet.": "Aún no hay coincidencias.",

  // ─── iter408 · Phase 14.1 + 14.2 · Haul Type + searchable rosters ──
  "Haul type": "Tipo de viaje",
  "Material": "Material",
  "Equipment Move": "Mover Equipo",
  "Spoils / Dump": "Escombros / Vertedero",
  "Support / Misc": "Apoyo / Varios",
  "Lowboy / Trailer": "Lowboy / Tráiler",
  "Receiving job / project": "Trabajo / proyecto receptor",
  "Equipment being hauled": "Equipo a transportar",
  "from equipment master": "del maestro de equipo",
  "Type or pick equipment (e.g. EX-12)": "Escribe o elige equipo (ej. EX-12)",
  "Add temporary equipment:": "Agregar equipo temporal:",
  "No matching equipment. Type a label to add a temporary one.":
    "Sin coincidencias. Escribe una etiqueta para agregar uno temporal.",
  "Pickup location": "Ubicación de recogida",
  "Drop-off location": "Ubicación de entrega",
  "e.g. 415 Yard, Vendor": "ej. 415 Yard, Proveedor",
  "e.g. Job Site, Shop": "ej. Sitio, Taller",
  "e.g. MASCI Hot Plant 1, 415 Yard": "ej. MASCI Hot Plant 1, 415 Yard",
  "e.g. Job Site, Dump": "ej. Sitio, Vertedero",
  "Add pickup location:": "Agregar ubicación de recogida:",
  "Add drop-off location:": "Agregar ubicación de entrega:",
  "Add source:": "Agregar origen:",
  "Add destination:": "Agregar destino:",
  "Add material:": "Agregar material:",
  "Add carrier:": "Agregar transportista:",
  "Pick from seeded or recent locations.": "Elige de las ubicaciones predefinidas o recientes.",
  "Pick from seeded or recent load points.": "Elige de los puntos de carga predefinidos o recientes.",
  "Pick from seeded or recent destinations.": "Elige de los destinos predefinidos o recientes.",
  "Pick from the seeded material catalog or recent values.":
    "Elige del catálogo de materiales o valores recientes.",
  "Type or pick a truck number": "Escribe o elige un número de camión",
  "Type or pick a driver": "Escribe o elige un conductor",
  "Type or pick a trailer": "Escribe o elige un tráiler",
  "Type or pick a material": "Escribe o elige un material",
  "Equipment Move: dispatch picks the truck/lowboy, the piece of equipment being hauled, pickup, drop-off. Same lifecycle, same board — completed counts as an Equipment Move on operational memory.":
    "Mover Equipo: despacho elige el camión/lowboy, la pieza de equipo a transportar, recogida y entrega. Mismo ciclo, mismo tablero — al completarse cuenta como Mover Equipo en la memoria operativa.",
  "Truck is required. Driver is optional — self-start can claim later. Pick a project, source, and material so operational memory stays accurate. Wait reasons stay canonical (set later via the driver lifecycle).":
    "El camión es obligatorio. El conductor es opcional — el auto-inicio puede reclamarlo después. Elige proyecto, origen y material para que la memoria operativa se mantenga precisa. Las razones de espera siguen siendo canónicas (se asignan después en el ciclo del conductor).",
  "Issue equipment move": "Emitir mover equipo",
  "Equipment move issued · truck on the board": "Mover equipo emitido · camión en el tablero",

  // ─── iter409 · Phase 14.3 · PM Haul Activity Tile ───────────────
  "Haul activity": "Actividad de viajes",
  "loading": "cargando",
  "Haul activity on your projects": "Actividad de viajes en tus proyectos",
  "production awareness · read-only": "conciencia de producción · solo lectura",
  "What's moving on your jobs today. PM never operates dispatch — this is glanceable awareness only.":
    "Lo que se mueve hoy en tus trabajos. El PM no opera despacho — esto es conciencia operativa solamente.",
  "Nothing to report — your jobs are quiet right now.":
    "Nada que reportar — tus trabajos están tranquilos en este momento.",
  "Loads today": "Viajes hoy",
  "eq": "eq",
  "Active hauls": "Viajes activos",
  "Equipment moves": "Mover equipo",
  "inbound + active": "entrante + activo",
  "Waiting on plant": "Esperando planta",
  "Waiting on site": "Esperando sitio",
  "Breakdown impacts": "Impactos por avería",
  "Top materials today": "Materiales principales hoy",

  // ─── iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity ──
  "Tanker / Liquid Asphalt": "Cisterna / Asfalto Líquido",
  "Tanker / Liquid Asphalt: dispatch picks the truck, tanker trailer, terminal/source, destination plant or tank, and the liquid product. Same lifecycle, same board — feeds plant continuity and supply truth.":
    "Cisterna / Asfalto Líquido: despacho elige camión, tráiler cisterna, terminal/origen, planta o tanque de destino y el producto líquido. Mismo ciclo, mismo tablero — alimenta la continuidad de planta y la verdad de suministro.",
  "Tanker trailer": "Tráiler cisterna",
  "Plant / job / project": "Planta / trabajo / proyecto",
  "Terminal / source": "Terminal / origen",
  "Destination plant / tank": "Planta / tanque de destino",
  "Liquid product": "Producto líquido",
  "e.g. Asphalt Terminal, Port": "ej. Terminal de asfalto, Puerto",
  "e.g. MASCI Hot Plant 1, Storage Tank": "ej. MASCI Hot Plant 1, Tanque de almacenamiento",
  "e.g. PG 64-22, CRS-2, Diesel": "ej. PG 64-22, CRS-2, Diésel",
  "Add terminal / source:": "Agregar terminal / origen:",
  "Add destination plant / tank:": "Agregar planta / tanque de destino:",
  "Add liquid product:": "Agregar producto líquido:",
  "Pick from seeded terminals or recent values.": "Elige de las terminales predefinidas o valores recientes.",
  "Pick from seeded plants/tanks or recent values.": "Elige de las plantas/tanques predefinidos o valores recientes.",
  "Pick from the seeded liquid catalog or recent values.":
    "Elige del catálogo de líquidos predefinidos o valores recientes.",
  "Issue tanker haul": "Emitir viaje de cisterna",
  "Tanker haul issued · truck on the board": "Viaje de cisterna emitido · camión en el tablero",

  // ─── iter411 · Phase 16 · Dispatch Command Portal ───────────────
  "Dispatcher": "Despachador",
  "Dispatch Command": "Mando de Despacho",
  "Issue work, watch movement, resolve delays, and keep trucks flowing.":
    "Emite trabajo, observa el movimiento, resuelve demoras y mantén los camiones fluyendo.",
  "Start with anything needing attention.": "Comienza con lo que requiere atención.",
  "Issue assignments before reviewing history.": "Emite asignaciones antes de revisar el historial.",
  "Driver taps are the source of operational truth.":
    "Los toques del conductor son la fuente de la verdad operativa.",
  "PMs see production awareness only.": "Los PMs solo ven conciencia de producción.",
  "Shop sees breakdown continuity only.": "El taller solo ve continuidad de averías.",
  "Motive will validate later — it does not replace the driver.":
    "Motive validará más adelante — no reemplaza al conductor.",
  "Start here": "Empieza aquí",
  "Operational Attention": "Atención operativa",
  "These are the items most likely to slow work today.":
    "Estos son los elementos con mayor probabilidad de retrasar el trabajo hoy.",
  "Reading signals…": "Leyendo señales…",
  "All hauls are flowing. Nothing requires dispatch attention right now.":
    "Todos los viajes están fluyendo. Nada requiere atención de despacho ahora mismo.",
  "Trucks in breakdown": "Camiones en avería",
  "Shop sees these too. Decide reassign vs hold.":
    "El taller también ve esto. Decide reasignar o detener.",
  "Stuck > 30 min": "Detenido > 30 min",
  "Lifecycle stalled. Tap the row on the board for context.":
    "Ciclo detenido. Toca la fila en el tablero para más contexto.",
  "Extended wait": "Espera prolongada",
  "Driver is waiting too long. Confirm the wait reason still applies.":
    "El conductor está esperando demasiado. Confirma que la razón de espera sigue aplicando.",
  "Open the operational board": "Abrir el tablero operativo",
  "Primary actions": "Acciones principales",
  "Issue Work": "Emitir trabajo",
  "Create the assignment once. Drivers and PMs see the right operational signal downstream.":
    "Crea la asignación una vez. Conductores y PMs verán la señal operativa correcta aguas abajo.",
  "Create Assignment": "Crear asignación",
  "Material haul": "Viaje de material",
  "Start Equipment Move": "Iniciar movimiento de equipo",
  "Lowboy / equipment haul": "Lowboy / movimiento de equipo",
  "Asphalt oil · binder · fuel": "Aceite asfáltico · ligante · combustible",
  "Support / Misc Haul": "Apoyo / Misc",
  "Spoils · support · misc": "Escombros · apoyo · varios",
  "Watch movement": "Observar movimiento",
  "Live Operational Flow": "Flujo operativo en vivo",
  "Active assignments, waiting trucks, breakdowns, and haul movement.":
    "Asignaciones activas, camiones en espera, averías y movimiento de viajes.",
  "Driver lifecycle taps keep the board current. Motive will validate later; it does not replace the driver.":
    "Los toques del ciclo del conductor mantienen el tablero al día. Motive validará después; no reemplaza al conductor.",
  "Open Operational Board": "Abrir tablero operativo",
  "Resolve before tomorrow": "Resolver antes de mañana",
  "Follow-Through": "Seguimiento",
  "These items need a decision, handoff, or correction before they become tomorrow's problem.":
    "Estos elementos necesitan una decisión, entrega o corrección antes de que se conviertan en el problema de mañana.",
  "Holds": "Retenciones",
  "Secondary operations": "Operaciones secundarias",
  "Fleet, utilization, and integrations": "Flota, utilización e integraciones",
  "Lower-priority context. Open only when needed.":
    "Contexto de menor prioridad. Ábrelo solo cuando lo necesites.",
  "Overview": "Resumen",
  "What's moving vs sitting": "Qué se mueve vs qué está detenido",
  "Trucks sitting too long": "Camiones detenidos demasiado tiempo",
  "Systems that validate operations": "Sistemas que validan las operaciones",
  "Fleet": "Flota",
  "Approved drivers": "Conductores aprobados",
  "Equipment moves (all-time)": "Movimientos de equipo (histórico)",
  "Coaching": "Coaching",
  "Guides & Coaching": "Guías y Coaching",
  "Use these when a dispatcher or truck boss is unsure what a state means.":
    "Úsalas cuando un despachador o jefe de camiones no sepa qué significa un estado.",
  "What dispatch owns": "Qué le pertenece a despacho",
  "Issuance, reassignment, breakdown response, and the operational board.":
    "Emisión, reasignación, respuesta a averías y tablero operativo.",
  "How assignment issuance works": "Cómo funciona la emisión de asignaciones",
  "One drawer · five haul types · seeded + historical rosters · add-temp anywhere.":
    "Un cajón · cinco tipos de viaje · listas predefinidas + históricas · agregar temporal en cualquier campo.",
  "What wait states mean": "Qué significan los estados de espera",
  "Canonical operational intelligence — never free text. Plant, dump, breakdown, etc.":
    "Inteligencia operativa canónica — nunca texto libre. Planta, vertedero, avería, etc.",
  "Downstream signals": "Señales aguas abajo",
  "PM sees production awareness only. Shop sees breakdown continuity only. Safety / FL / HR stay quiet on DLS.":
    "PM solo ve conciencia de producción. Taller solo ve continuidad de averías. Safety / FL / HR permanecen silenciosos en DLS.",
  "Why Motive validates later, not surveils": "Por qué Motive valida después, no vigila",
  "Motive answers questions about movement, arrival, and wait truth — it does not give orders.":
    "Motive responde preguntas sobre movimiento, llegada y verdad de espera — no da órdenes.",
  "Open all guides": "Abrir todas las guías",
  "Home": "Inicio",
  "Back": "Atrás",
  "Dispatch": "Despacho",
  "Sign out": "Cerrar sesión",
  "Equipment moves": "Movimientos de equipo",
  // iter414 · Phase 18.1 · in-flow coaching links — EN→ES
  "What requires dispatch attention": "Qué requiere atención de despacho",
  "How the 5 haul types flow": "Cómo fluyen los 5 tipos de acarreo",
  "What PM haul activity means": "Qué significa la actividad de acarreos del PM",
  "How shift start works": "Cómo funciona el inicio de turno",
  // iter416 · Phase 19.1 · Day-1 Live Ops Debrief — EN→ES
  "Day-1 review": "Revisión del Día-1",
  "Day-1 Live Ops Debrief": "Informe de Operaciones en Vivo · Día-1",
  "Capture real operational friction while it is still fresh. Only document repeated hesitation, confusion, downstream continuity problems, or operational slowdowns.": "Capture la fricción operacional real mientras aún está fresca. Solo documente vacilación repetida, confusión, problemas de continuidad río abajo o lentitud operacional.",
  "Today": "Hoy",
  "Where did dispatch hesitate?": "¿Dónde vaciló despacho?",
  "What was difficult to find?": "¿Qué fue difícil de encontrar?",
  "Did drivers understand shift start?": "¿Entendieron los conductores el inicio de turno?",
  "Did drivers understand assignment flow?": "¿Entendieron los conductores el flujo de asignaciones?",
  "Was assignment issuance fast enough?": "¿Fue la emisión de asignaciones suficientemente rápida?",
  "Did PM haul visibility help production awareness?": "¿La visibilidad de acarreos del PM ayudó a la conciencia de producción?",
  "Did Shop breakdown continuity make sense?": "¿Tuvo sentido la continuidad de avería del Taller?",
  "Were any dropdowns confusing?": "¿Algún menú desplegable fue confuso?",
  "Were any wait states missing or unclear?": "¿Faltó algún estado de espera o no quedó claro?",
  "Where did users pause too long or become uncertain?": "¿Dónde se detuvieron demasiado los usuarios o quedaron inseguros?",
  "What felt unnecessary or overly complicated?": "¿Qué se sintió innecesario o demasiado complicado?",
  "What should remain simple and untouched?": "¿Qué debe permanecer simple e intacto?",
  "Brief operational observation…": "Observación operacional breve…",
  "Operational notes": "Notas operacionales",
  "Anything else from the field…": "Cualquier otra cosa del campo…",
  "Doctrine observations": "Observaciones de doctrina",
  "Did doctrine hold? Any restraint pressure points?": "¿Se mantuvo la doctrina? ¿Algún punto de presión sobre la restricción?",
  "Save Day-1 debrief": "Guardar informe Día-1",
  "Saving…": "Guardando…",
  "Submission failed.": "Falló el envío.",
  "Admin sign-in required.": "Se requiere inicio de sesión de administrador.",
  "Debrief saved.": "Informe guardado.",
  "Written to": "Escrito en",
  "Re-submitting same day will overwrite this file with your latest version.": "Reenviar el mismo día sobrescribirá este archivo con su última versión.",
  "Capture operational hesitation and continuity gaps — not feature wishlists. Build from repeated operational patterns, not isolated requests.": "Capture vacilación operacional y vacíos de continuidad — no listas de deseos de funcionalidades. Construya a partir de patrones operacionales repetidos, no de solicitudes aisladas.",
  "Back to Admin": "Regresar al Admin",
  // iter417 · Phase 20.0 · Operational Attachments — EN→ES
  "Operational proof": "Prueba operacional",
  "Tickets · photos · receipts": "Boletos · fotos · recibos",
  "How load proof works": "Cómo funciona la prueba de carga",
  "Attachment type": "Tipo de adjunto",
  "Note (optional)": "Nota (opcional)",
  "Plant A scale · ticket #1421": "Báscula Planta A · boleto #1421",
  "Capture / Upload": "Capturar / Subir",
  "Uploading…": "Subiendo…",
  "Images up to 5 MB · camera-first on phones.": "Imágenes hasta 5 MB · cámara primero en teléfonos.",
  "Loading attachments…": "Cargando adjuntos…",
  "No operational proof attached yet.": "Aún no hay prueba operacional adjunta.",
  "Open original": "Abrir original",
  "Attached.": "Adjuntado.",
  "Removed.": "Eliminado.",
  "Upload failed.": "Falló la subida.",
  "Delete failed.": "Falló la eliminación.",
  "File too large (5 MB max).": "Archivo demasiado grande (5 MB máx).",
  "Only image files are supported.": "Solo se admiten archivos de imagen.",
  "Delete this attachment? (5 minutes after upload only)": "¿Eliminar este adjunto? (Solo 5 minutos después de subirlo)",
  "Delete (5 min mistake-recovery window)": "Eliminar (ventana de recuperación de 5 min)",
  "Asphalt ticket": "Boleto de asfalto",
  "Scale ticket": "Boleto de báscula",
  "Tanker BOL": "Carta de Porte de Cisterna (BOL)",
  "Fuel receipt": "Recibo de combustible",
  "Delivery receipt": "Recibo de entrega",
  "Load photo": "Foto de carga",
  "Damage photo": "Foto de daño",
  "Breakdown photo": "Foto de avería",
  "Inspection photo": "Foto de inspección",
  "Transfer document": "Documento de transferencia",
  "Dump receipt": "Recibo de descarga",
  "Other photo": "Otra foto",
  // iter418 · Phase 20.1 · Driver breakdown-proof prompt
  "Operational proof · optional": "Prueba operacional · opcional",
  "Add a breakdown photo? Helps Shop see what's wrong.": "¿Agregar foto de avería? Ayuda al Taller a ver qué está mal.",
  "Take Photo": "Tomar foto",
  "Skip": "Omitir",
  // iter421 · Phase 23.0 · Offline continuity (invisible language)
  "1 update waiting to sync": "1 actualización esperando sincronizar",
  "{n} updates waiting to sync": "{n} actualizaciones esperando sincronizar",
  "Operational update pending": "Actualización operacional pendiente",
  // iter418/421 · errors stay operational, not technical
  "Could not record that. Try again.": "No se pudo registrar. Intente de nuevo.",
  "Connection failed — try again.": "Falló la conexión — intente de nuevo.",
  "Connection failed — retrying…": "Falló la conexión — reintentando…",
  // iter422 · Phase 24 · Passkey / device sign-in continuity
  "Use device sign-in": "Usar inicio con dispositivo",
  "Use passkey": "Usar clave de acceso",
  "Use password instead": "Usar contraseña en su lugar",
  "Sign in with Face ID": "Iniciar sesión con Face ID",
  "Verifying device…": "Verificando dispositivo…",
  "Enter your work email first": "Ingrese su correo de trabajo primero",
  "Device sign-in failed": "Falló el inicio con dispositivo",
  "Device sign-in cancelled": "Inicio con dispositivo cancelado",
  "Your device handles Face ID / Touch ID securely. MASCI never stores biometric information.": "Su dispositivo maneja Face ID / Touch ID de forma segura. MASCI nunca almacena información biométrica.",
  "Enable faster sign-in on this device?": "¿Activar inicio de sesión más rápido en este dispositivo?",
  "Your device's secure unlock will sign you in next time.": "El desbloqueo seguro de su dispositivo le iniciará sesión la próxima vez.",
  "Enable device sign-in": "Activar inicio con dispositivo",
  "Not now": "Ahora no",
  "Device sign-in enabled.": "Inicio con dispositivo activado.",
  "No device passkey is registered for this account": "No hay clave de dispositivo registrada para esta cuenta",
  "Please sign in with your password first": "Inicie sesión con su contraseña primero",
  "Device sign-in is not available in this browser": "El inicio con dispositivo no está disponible en este navegador",
  "Continue sign-in at the master page.": "Continúe el inicio de sesión en la página principal.",
  // iter423 · Phase 25 · Shop Recovery convergence (operational language only)
  "Shop Console": "Consola de Taller",
  "Shop Recovery": "Recuperación Operacional",
  "Operational Recovery": "Recuperación Operacional",
  "Equipment Needing Attention": "Equipo que Necesita Atención",
  "Active Recovery Work": "Trabajo de Recuperación Activo",
  "Waiting / Delays": "Esperando / Demoras",
  "Returned to Service": "Devuelto al Servicio",
  "Operational Continuity History": "Historial de Continuidad Operacional",
  "Loading operational recovery…": "Cargando recuperación operacional…",
  "No equipment in operational recovery right now.": "Ningún equipo en recuperación operacional ahora mismo.",
  "{n} pieces of equipment currently in operational recovery.": "{n} equipos actualmente en recuperación operacional.",
  "{n} operational interruption waiting on parts.": "{n} interrupción operacional esperando piezas.",
  "{n} pieces of equipment returned to service today.": "{n} equipos devueltos al servicio hoy.",
  "Operational interruptions that need Shop awareness right now. Sign off when the unit is back in field service.": "Interrupciones operacionales que necesitan atención del Taller ahora mismo. Firme cuando la unidad regrese al servicio de campo.",
  "Active recovery work means equipment is being restored to field service.": "El trabajo de recuperación activo significa que el equipo está siendo restaurado al servicio de campo.",
  "Waiting on parts pauses operational recovery until components arrive.": "Esperando piezas pausa la recuperación operacional hasta que lleguen los componentes.",
  "Returned to service means the equipment is operationally ready for field continuity again.": "Devuelto al servicio significa que el equipo está operacionalmente listo para la continuidad de campo de nuevo.",
  "Operational chronology · breakdown continuity, reassignments, and recovery moments across the platform.": "Cronología operacional · continuidad de averías, reasignaciones y momentos de recuperación en la plataforma.",
  "Operational continuity restored.": "Continuidad operacional restaurada.",
  "No active recovery work right now. Equipment is in field service or waiting on parts.": "Sin trabajo de recuperación activo ahora. El equipo está en servicio de campo o esperando piezas.",
  "No equipment is currently held by an operational interruption.": "Ningún equipo está actualmente retenido por una interrupción operacional.",
  "No equipment has been returned to service in the last 7 days.": "Ningún equipo ha sido devuelto al servicio en los últimos 7 días.",
  "No operational continuity events recorded yet. Recent breakdowns, reassignments, and recovery moments will appear here as they happen.": "No hay eventos de continuidad operacional registrados todavía. Las averías, reasignaciones y momentos de recuperación recientes aparecerán aquí cuando ocurran.",
  "Acknowledged": "Reconocido",
  "Diagnosing": "Diagnosticando",
  "Repair Active": "Reparación Activa",
  "Operational Test": "Prueba Operacional",
  "Waiting on parts": "Esperando piezas",
  "Truck": "Camión",
  "Driver": "Conductor",
  "Equipment": "Equipo",
  "Event": "Evento",
  "None.": "Ninguno.",
  "More": "Más",
  "Trends · Equipment · Parts · Integrations · Activity": "Tendencias · Equipo · Piezas · Integraciones · Actividad",
  "These views remain accessible but stay out of first-screen cognition.": "Estas vistas permanecen accesibles pero se mantienen fuera de la cognición de pantalla inicial.",
  "MASCI Fleet · DVIR queue": "Flota MASCI · cola DVIR",
  "Recent Pre-Op Inspections": "Inspecciones Pre-Operativas Recientes",
  "Equipment Trends": "Tendencias de Equipo",
  "Shop Activity": "Actividad del Taller",
  "Equipment List": "Lista de Equipo",
  "Parts Catalog": "Catálogo de Piezas",
  "Reachable via direct URL · kept out of first-screen cognition": "Accesible vía URL directa · mantenido fuera de la cognición de pantalla inicial",
  // iter424 · Phase 25.1 · Inline Recovery Continuity Actions
  "Set recovery state": "Establecer estado de recuperación",
  "Note (optional)": "Nota (opcional)",
  "Save": "Guardar",
  "Saving…": "Guardando…",
  "Recovery state updated.": "Estado de recuperación actualizado.",
  "Already in that recovery state.": "Ya está en ese estado de recuperación.",
  "Could not update recovery state. Try again.": "No se pudo actualizar el estado de recuperación. Intente de nuevo.",
  "Returned to service means equipment is operationally ready for field continuity.": "Devuelto al servicio significa que el equipo está operacionalmente listo para la continuidad de campo.",
  "Operational test confirms field readiness before return.": "La prueba operacional confirma la disponibilidad de campo antes del retorno.",
  // Note placeholder examples (rotated · teach operational language)
  "Waiting on hydraulic hose": "Esperando manguera hidráulica",
  "Operational test complete": "Prueba operacional completa",
  "Back running": "De vuelta en operación",
  "Parts arriving tomorrow": "Piezas llegan mañana",
  "Sensor swapped · running clean": "Sensor cambiado · operando limpio",
};

const DICTS = { es: ES, en: {} };

export function tStr(key) {
  if (_current === "en" || !key) return key;
  return DICTS[_current][key] || key;
}

/**
 * React hook — re-renders when the language changes.
 * Returns { t, lang, setLang }.
 */
export function useT() {
  const lang = useSyncExternalStore(subscribe, getLang, getLang);
  return { t: tStr, lang, setLang };
}
