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
if (typeof window !== "undefined") {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored && VALID.has(stored)) _current = stored;
  } catch {
    /* localStorage unavailable */
  }
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
  "MASCI Safety Hub": "Centro de Seguridad MASCI",
  "One front door for every safety form.": "Una puerta de entrada para cada formulario de seguridad.",
  "Document compliance, run toolbox talks, and analyze hazards before every task. Print or save any record as a branded PDF — works from any device.":
    "Documente el cumplimiento, dirija charlas de seguridad y analice los peligros antes de cada tarea. Imprima o guarde cualquier registro como PDF — funciona en cualquier dispositivo.",
  "No Shortcuts": "Sin Atajos",
  "No Exceptions": "Sin Excepciones",
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
