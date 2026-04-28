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
  "One place for every MASCI job.": "Un solo lugar para cada trabajo de MASCI.",
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
  "Incident Reports · JHA Plans · Trench Box Data": "Incidentes · Planes JHA · Trinchera",
  "Daily Reports — crews, subs, visitors, equipment, materials":
    "Reportes Diarios — cuadrillas, subcontratistas, visitantes, equipo, materiales",
  "Equipment Pre-Op — OSHA walk-arounds with pass/fail":
    "Pre-Op de Equipo — recorridos OSHA con aprobado/fallado",
  "Crew Hub — Basecamp-style per-job collaboration":
    "Crew Hub — colaboración por trabajo estilo Basecamp",
  "@mentions · My Stuff inbox · Activity feed":
    "@menciones · Bandeja Mi Trabajo · Actividad",
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
  "Job Hazard Analysis": "Análisis de Peligros del Trabajo",
  "Incident Reports": "Reportes de Incidentes",
  "Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.":
    "Inspecciones diarias y semanales del sitio. EPP, control de tránsito, protección contra caídas, eléctrico y más — calificadas automáticamente.",
  "Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.":
    "Charlas de seguridad y reuniones diarias. Más de 80 temas con peligros prellenados — cada miembro de la cuadrilla firma.",
  "Pre-task JHA / JSA. Walk every step, list hazards, document controls, and get the crew sign-off before work starts.":
    "JHA / JSA previo a la tarea. Recorra cada paso, liste los peligros, documente los controles y obtenga la firma de la cuadrilla antes de comenzar.",
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
  "Daily Report, Site Inspection, Safety Meeting, JHA, or Incident — tap the tile.":
    "Reporte Diario, Inspección, Reunión de Seguridad, JHA o Incidente — toque la tarjeta.",
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
  // JHA
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
  "Hazard Analysis": "Análisis de Peligros",
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
  "Submit JHA": "Enviar JHA",
  "Saving JHA...": "Guardando JHA...",

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
  // JHA Plans Poster (printable QR poster)
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
