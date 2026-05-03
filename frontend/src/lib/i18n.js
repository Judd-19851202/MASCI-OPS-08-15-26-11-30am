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
  // Branding / hub
  "MASCI Safety Hub": "Centro MASCI",
  "MASCI Hub": "Centro MASCI",
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
  "MASCI · Operations Platform": "MASCI · Plataforma de Operaciones",
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
  "Accountability": "Responsabilidad",
  "Adapt": "Adaptarse",
  "Overcome": "Superar",
  "Accountability · Adapt · Overcome": "Responsabilidad · Adaptarse · Superar",
  "MASCI · Safety · Accountability · Adapt · Overcome":
    "MASCI · Seguridad · Responsabilidad · Adaptarse · Superar",
  "MASCI · Field · Accountability · Adapt · Overcome":
    "MASCI · Campo · Responsabilidad · Adaptarse · Superar",
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
  "Pass": "Aprobado",
  "Fail": "Falla",
  "N/A": "N/A",
  "Describe the issue (required for FAIL — min 10 characters)":
    "Describa el problema (requerido para FALLA — mínimo 10 caracteres)",
  "Description required for FAIL": "Descripción requerida para FALLA",
  "At least 10 characters required": "Mínimo 10 caracteres requeridos",
  "Description": "Descripción",
  "Replace photo": "Reemplazar foto",
  "Add photo (required for FAIL)": "Agregar foto (requerida para FALLA)",
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
  "Open your camera, point it at the QR code, and tap the link. The MASCI Hub opens in your browser. No login. No app to install. Add it to your home screen and you're set.":
    "Abra la cámara, apúntela al código QR y toque el enlace. El MASCI Hub se abre en su navegador. Sin inicio de sesión. Sin aplicación que instalar. Agréguelo a su pantalla de inicio y listo.",
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
  // Trench Box Tabulated Data
  // ============================================================
  "Trench Box Data": "Datos de Cajas de Zanja",
  "MASCI trench-shield fleet. Size, weight, OSHA max-depth by soil type, and manufacturer tabulated-data PDFs.":
    "Flota de escudos de zanja MASCI. Tamaño, peso, profundidad máxima OSHA por tipo de suelo, y PDFs de datos tabulados del fabricante.",
  "Trench Box Tabulated Data": "Datos Tabulados de Cajas de Zanja",
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
  "FAIL": "FALLA",

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
  "Two buttons. Your whole MASCI Hub — every form, every photo, every Crew Hub message.":
    "Dos botones. Todo su MASCI Hub — cada formulario, cada foto, cada mensaje del Hub de Cuadrilla.",
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
  "Back to MASCI Hub": "Volver al Hub MASCI",

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
