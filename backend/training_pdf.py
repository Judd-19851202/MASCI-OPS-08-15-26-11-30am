"""Render the Training Hub as downloadable PDF packets.

Used by `GET /api/training/packet.pdf?track={track}&lang={en|es}` (public,
no auth). Returns a single-file PDF that contains every lesson for the
requested track with cover page, table of contents, and per-lesson pages
(title + "Why this matters" + numbered steps + tips + cheat sheet).

Lesson content lives in this module as a Python mirror of
`frontend/src/data/training.js` + `training_es.js`. Kept in sync by hand —
the frontend is the source of truth, this file is a serialized snapshot
rendered into PDFs for offline/email distribution.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).parent
LOGO_PATH = ROOT.parent / "frontend" / "public" / "masci-full-lockup-onlight.png"


def _logo_uri() -> str:
    try:
        b = LOGO_PATH.read_bytes()
        return f"data:image/png;base64,{base64.b64encode(b).decode()}"
    except Exception:
        return ""


# ----------------------------------------------------------------------------
# Lesson catalog (mirror of frontend/src/data/training.js)
# ----------------------------------------------------------------------------

TRACKS = {
    "field": {
        "title": "Field Crew Training",
        "title_es": "Capacitación de Cuadrilla de Campo",
        "blurb": "Everything the crew on the ground needs — from scanning the QR at the trailer to submitting a Daily Report after the shift.",
        "blurb_es": "Todo lo que la cuadrilla en campo necesita — desde escanear el QR en el tráiler hasta enviar el Reporte Diario después del turno.",
        "accent": "#B91C1C",
    },
    "shop": {
        "title": "Shop / Mechanic Training",
        "title_es": "Capacitación del Taller / Mecánico",
        "blurb": "How the shop clears failed Pre-Ops, tracks parts, and keeps the fleet running.",
        "blurb_es": "Cómo el taller libera Pre-Ops fallados, rastrea partes y mantiene la flota funcionando.",
        "accent": "#0F172A",
    },
    "pm": {
        "title": "PM / Project Management Training",
        "title_es": "Capacitación del Gerente de Proyectos",
        "blurb": "Day-to-day management: master lists, email routing, import/export, archive recovery.",
        "blurb_es": "Gestión diaria: listas maestras, ruteo de correos, importar/exportar, archivo.",
        "accent": "#D97706",
    },
    "admin": {
        "title": "Admin / Owner Training",
        "title_es": "Capacitación del Administrador / Dueño",
        "blurb": "Full platform overview, system-recovery tools, and the exact backup workflow that protects every record.",
        "blurb_es": "Panorama completo de la plataforma, herramientas de recuperación y el flujo exacto de respaldo.",
        "accent": "#B91C1C",
    },
}


# --- Field (7) ---
FIELD_LESSONS = [
    {
        "slug": "field-01-hub-navigation",
        "order": 1,
        "title": "Lesson 1 — Navigating the MASCI Hub",
        "title_es": "Lección 1 — Navegando el Hub MASCI",
        "why": "Everything starts here. If you can find the Hub on your phone, you can file any form the company needs in under 2 minutes.",
        "why_es": "Todo empieza aquí. Si encuentra el Hub en su teléfono, puede llenar cualquier formulario que la compañía necesite en menos de 2 minutos.",
        "steps": [
            "Point your phone camera at the QR code posted inside the site trailer — the MASCI Hub opens in your browser automatically. No app to install, no login for Field forms.",
            "On the Hub home page you'll see 8 tiles: Field, QA/QC, Safety, Projects, PM Portal, Shop, Training Hub, and Admin. Field, QA/QC, and Safety are the three you'll use every day.",
            "Tap the language toggle in the top-right to switch between EN and ES — your choice is remembered on this phone.",
            "Tap 'Company Info' in the top-right to see MASCI's office address and phone numbers if you need to call HQ from the field.",
            "Tap 'Add to Home Screen' in your browser menu once — after that the Hub opens like a real app with one tap.",
        ],
        "steps_es": [
            "Apunte la cámara de su teléfono al código QR dentro del tráiler — el Hub MASCI se abre en su navegador automáticamente. Sin aplicación que instalar, sin inicio de sesión para los formularios de Campo.",
            "En la página principal verá 8 mosaicos: Campo, QA/QC, Seguridad, Proyectos, Portal del PM, Taller, Centro de Capacitación y Admin. Campo, QA/QC y Seguridad son los tres que usará todos los días.",
            "Toque el botón EN/ES en la esquina superior derecha para cambiar el idioma — su elección se recuerda en este teléfono.",
            "Toque 'Company Info' en la esquina superior derecha para ver la dirección y teléfonos de MASCI si necesita llamar a la oficina desde el campo.",
            "Toque 'Agregar a pantalla de inicio' en el menú del navegador una vez — después el Hub se abre como una aplicación real con un toque.",
        ],
        "tips": [
            "If GPS doesn't grab on the first try, type the address in the Location field instead — same result.",
            "The Hub works offline for reading, but submitting a form needs a signal — save and retry when you get bars.",
        ],
        "tips_es": [
            "Si el GPS no funciona al primer intento, escriba la dirección en el campo Ubicación — mismo resultado.",
            "El Hub funciona sin conexión para leer, pero enviar un formulario necesita señal — guarde y reintente cuando tenga barras.",
        ],
        "cheatSheet": [
            "Scan the QR → Hub opens → Pick Field or Safety → Fill → Sign → Submit.",
            "Language toggle is top-right. Company Info is next to it.",
        ],
        "cheatSheet_es": [
            "Escanee QR → Hub abre → Elija Campo o Seguridad → Llene → Firme → Envíe.",
            "Idioma arriba a la derecha. Company Info al lado.",
        ],
    },
    {
        "slug": "field-02-daily-report",
        "order": 2,
        "title": "Lesson 2 — Daily Reports",
        "title_es": "Lección 2 — Reportes Diarios",
        "why": "The Daily Report is the company's memory for what happened today. No Daily Report = no proof of crew time, material deliveries, subs on site, equipment used, or progress made.",
        "why_es": "El Reporte Diario es la memoria de la compañía sobre lo que pasó hoy. Sin Reporte Diario no hay prueba de horas de cuadrilla, entregas de material, subs en sitio, equipo usado, ni progreso.",
        "steps": [
            "From the Hub, tap Field → Daily Reports → 'File First Report' (or 'New Report').",
            "Pick your MASCI Job from the picker — project number, name, location, and client auto-fill.",
            "Tap 'Use GPS' to auto-fill Location. Weather auto-loads from today's forecast.",
            "General Info: Yes/No on Schedule Delays, Weather, Accidents, Injuries. Any Yes → red Safety Escalation box appears.",
            "MASCI Crews: tap 'Add Crew Member', pick name, Start/Stop times. Lunch auto-deducts 30 min.",
            "Subcontractors on Site: same pattern — who, how many, how many hours, what they did.",
            "Site Visitors, Equipment Log, Material Deliveries, Activity Log: fill what applies.",
            "Photos: minimum 6 required. Start / progress / issues / end.",
            "Prepared By + Superintendent sign at the bottom. Submit.",
        ],
        "steps_es": [
            "Desde el Hub, toque Campo → Reportes Diarios → 'Archivar Primer Reporte' (o 'Nuevo Reporte').",
            "Elija su Trabajo MASCI del selector — el número de proyecto, nombre, ubicación y cliente se autocompletan.",
            "Toque 'Usar GPS' para autocompletar Ubicación. El clima se carga automáticamente del pronóstico de hoy.",
            "Información General: responda Sí/No sobre Retrasos, Clima, Accidentes, Lesiones. Cualquier Sí → aparece caja roja de Escalación de Seguridad.",
            "Cuadrillas MASCI: toque 'Agregar Miembro', elija nombre, horas Inicio/Fin. El almuerzo resta 30 min automáticamente.",
            "Subcontratistas en Sitio: mismo patrón — quién, cuántos, cuántas horas, qué hicieron.",
            "Visitantes, Registro de Equipo, Entregas de Materiales, Registro de Actividad: llene lo que aplique.",
            "Fotos: mínimo 6 requeridas. Inicio / progreso / problemas / final.",
            "Preparado Por + Superintendente firman abajo. Envíe.",
        ],
        "tips": [
            "If an accident or injury was reported, the app BLOCKS submission until an Incident Report is filed first.",
            "Hit 'Save Draft' any time — progress persists on this phone.",
        ],
        "tips_es": [
            "Si se reportó un accidente o lesión, la app BLOQUEA el envío hasta que se presente un Reporte de Incidente primero.",
            "Toque 'Guardar Borrador' en cualquier momento — el progreso persiste en este teléfono.",
        ],
        "cheatSheet": [
            "6 photos minimum. GPS + weather are automatic.",
            "If Yes on Accident/Injury → Incident Report FIRST.",
            "Prepared By + Superintendent both sign.",
        ],
        "cheatSheet_es": [
            "Mínimo 6 fotos. GPS + clima automáticos.",
            "Si Sí en Accidente/Lesión → Reporte de Incidente PRIMERO.",
            "Preparado Por + Superintendente firman ambos.",
        ],
    },
    {
        "slug": "field-03-equipment-preop",
        "order": 3,
        "title": "Lesson 3 — Equipment Pre-Op Inspection",
        "title_es": "Lección 3 — Inspección Pre-Operación de Equipo",
        "why": "OSHA 1926 requires a daily walk-around before you operate heavy equipment. A FAIL here tags the unit OUT OF SERVICE until the shop clears it.",
        "why_es": "OSHA 1926 requiere un recorrido diario antes de operar equipo pesado. Un FALLO aquí marca la unidad FUERA DE SERVICIO hasta que el taller la libere.",
        "steps": [
            "Hub → Field → Equipment Pre-Op.",
            "Pick Job and Equipment Type. Search the saved units list — make/model/serial auto-fill.",
            "Enter Hour Meter OR Odometer. Enter your full name.",
            "Walk the unit. For each item, tap Pass / Fail / N/A. FAIL requires 10-char description AND photo.",
            "Major-safety failures (brakes, steering, seat belt, ROPS, horn) → STOP modal. Unit marked OUT OF SERVICE.",
            "Critical-fluid failures block submission until refilled and flipped back to Pass.",
            "Add deficiency notes, corrective actions, and equipment photos.",
            "Operator Sign-Off: sign, tap Submit.",
        ],
        "steps_es": [
            "Hub → Campo → Pre-Op de Equipo.",
            "Elija Trabajo y Tipo de Equipo. Busque en las unidades guardadas — marca/modelo/serie se autocompletan.",
            "Ingrese Horómetro U Odómetro. Ingrese su nombre completo.",
            "Recorra la unidad. Para cada punto, toque Aprobado / Falla / N/A. FALLO requiere descripción de 10 caracteres Y foto.",
            "Fallas de seguridad mayor (frenos, dirección, cinturón, ROPS, bocina) → modal ALTO. Unidad FUERA DE SERVICIO.",
            "Fallas críticas de fluido bloquean el envío hasta rellenar y cambiar a Aprobado.",
            "Agregue notas de deficiencias, acciones correctivas y fotos del equipo.",
            "Firma del Operador: firme, toque Enviar.",
        ],
        "tips": [
            "Engine off first (visual), then on (gauges/brakes/hydraulics).",
            "Don't lie on a Pass. The shop sees every FAIL and will notice a pattern.",
            "FAIL or out-of-service auto-emails EVERY active mechanic in Shop Users panel within 60 seconds.",
            "Your Pre-Op gets a Doc ID like PRE-2026-00042 — printed on the PDF, in the email subject. Office calls? Give them that number.",
        ],
        "tips_es": [
            "Motor apagado primero (visual), luego encendido (medidores/frenos/hidráulicos).",
            "No mienta en un Aprobado. El taller ve cada FALLO y notará un patrón.",
            "FALLO o fuera de servicio envía correo a CADA mecánico activo del panel de Shop Users en 60 segundos.",
            "Su Pre-Op recibe un Doc ID como PRE-2026-00042 — en el PDF y en el asunto del correo. ¿Llaman de la oficina? Deles ese número.",
        ],
        "cheatSheet": [
            "Engine off → walk around → engine on → check fluids & gauges.",
            "FAIL = unit out of service + photo required.",
            "Major safety items = STOP, do not operate.",
        ],
        "cheatSheet_es": [
            "Motor apagado → recorrido → motor encendido → revise fluidos y medidores.",
            "FALLO = unidad fuera de servicio + foto requerida.",
            "Puntos de seguridad mayor = ALTO, no opere.",
        ],
    },
    {
        "slug": "field-material-calculators",
        "order": 4,
        "title": "Lesson 4 — Material Calculators",
        "title_es": "Lección 4 — Calculadoras de Materiales",
        "why": "Quantity guesses cost money. Order short → second-day delivery, idle crew. Order over → wasted yards billed against the job. The Material Calculators give field estimates with the same formulas the office uses.",
        "why_es": "Las cantidades adivinadas cuestan dinero. Pedir de menos → entrega al día siguiente, cuadrilla parada. Pedir de más → yardas desperdiciadas. Las Calculadoras de Materiales dan estimaciones con las mismas fórmulas que usa la oficina.",
        "steps": [
            "Hub → Field → Material Calculators. Six cards: Aggregate, Asphalt, Concrete, Truck Load, Yield/Waste, Tons↔CY.",
            "Pick the right calculator. Enter dimensions in feet & inches as the field reads them — app handles the math.",
            "Always ROUND UP for ordering. The 'Order This Much' line already includes a small over-order buffer.",
            "Tap 'Save / Log Use' so the PM and Admin see who calculated what — drives waste/yield tracking.",
            "EN/ES toggle works on every calculator — labels, formulas, and result lines all bilingual.",
        ],
        "steps_es": [
            "Hub → Campo → Calculadoras de Materiales. Seis tarjetas: Agregado, Asfalto, Concreto, Carga de Camión, Rendimiento/Desperdicio, Toneladas↔CY.",
            "Elija la calculadora correcta. Ingrese dimensiones en pies y pulgadas como las lee el campo — la app hace los cálculos.",
            "SIEMPRE REDONDEE HACIA ARRIBA. La línea 'Pedir esta cantidad' ya incluye margen de desperdicio.",
            "Toque 'Guardar / Registrar Uso' para que el PM y el Admin vean quién calculó qué — alimenta el seguimiento.",
            "El botón EN/ES funciona en cada calculadora — etiquetas, fórmulas y resultados son bilingües.",
        ],
        "tips": [
            "When in doubt, ROUND UP — being short on a pour costs 10× more than being slightly over.",
            "The calculator is a field check, not the official take-off quantity.",
        ],
        "tips_es": [
            "En caso de duda, REDONDEE HACIA ARRIBA — quedar corto cuesta 10× más que estar un poco sobre.",
            "La calculadora es una verificación de campo, no la cantidad oficial.",
        ],
        "cheatSheet": [
            "Six calculators. Feet & inches in. App does the math.",
            "Round UP. 'Save / Log Use' so the office sees the estimate.",
        ],
        "cheatSheet_es": [
            "Seis calculadoras. Pies y pulgadas. La app hace los cálculos.",
            "Redondee hacia ARRIBA. 'Guardar / Registrar Uso' para que la oficina vea la estimación.",
        ],
    },
    {
        "slug": "field-qaqc-inspections",
        "order": 5,
        "title": "Lesson 5 — QA / QC Inspections",
        "title_es": "Lección 5 — Inspecciones de QA / QC",
        "why": "Quality issues caught before the pour or before the sub leaves the site cost a fraction of fixing them later. The QA/QC module documents the inspection, captures photos and signatures, generates a PDF, and routes it to the assigned PM.",
        "why_es": "Los problemas de calidad detectados antes de la colada o antes de que el sub deje el sitio cuestan una fracción de arreglarlos después. El módulo QA/QC documenta la inspección, captura fotos y firmas, genera un PDF y lo envía al PM asignado.",
        "steps": [
            "Hub → QA / QC. Three forms today: Concrete Form Inspection, Rebar Inspection, Subcontractor Work Inspection. More to come.",
            "Pick the MASCI Job — project number, name, location, client, and assigned PM all auto-fill. PM email captured automatically.",
            "GPS button next to Location auto-fills the address. Subcontractor / Crew = searchable dropdown with add-new.",
            "Work Area / Station is REQUIRED — be specific (e.g. 'Bridge deck north abutment STA 100+05').",
            "Concrete Form only: Mix Design + Yards Ordered + Concrete Vendor (searchable, add-new).",
            "Checklist: Pass / Fail / N/A. Every FAIL needs a deficiency note.",
            "Min 3 photos. Inspection notes, deficiencies, corrective actions. Inspector signs. Sub Rep signature optional.",
            "Submit. PDF emails to assigned PM automatically. Record visible in PM Portal + Admin Console.",
        ],
        "steps_es": [
            "Hub → QA / QC. Tres formularios hoy: Inspección de Formaleta de Concreto, Inspección de Acero, Inspección de Trabajo del Subcontratista. Más por venir.",
            "Elija el Trabajo MASCI — número, nombre, ubicación, cliente y PM asignado se llenan automáticamente. Correo del PM capturado automáticamente.",
            "Botón GPS al lado de Ubicación autollena la dirección. Subcontratista / Cuadrilla = lista buscable con agregar-nuevo.",
            "Área de Trabajo / Estación REQUERIDO — sea específico (ej. 'Tablero, estribo norte EST 100+05').",
            "Solo Formaleta de Concreto: Diseño de Mezcla + Yardas Pedidas + Vendedor de Concreto (buscable, agregar-nuevo).",
            "Lista de verificación: Aprobado / Falla / N/A. Cada FALLA necesita una nota de deficiencia.",
            "Mín. 3 fotos. Notas, deficiencias, acciones correctivas. El Inspector firma. Firma del Rep del Sub opcional.",
            "Envíe. El PDF se envía al PM asignado automáticamente. Registro visible en el Portal del PM + Consola del Admin.",
        ],
        "tips": [
            "Photo a Fail with a tape measure or reference in frame — 'Slump too high' is hard to defend; '7-inch slump on 4-inch spec' is bulletproof.",
            "PM only sees records on jobs they're assigned to. Pick the right job — wrong job = wrong PM gets the email.",
        ],
        "tips_es": [
            "Fotografíe una Falla con cinta métrica o referencia en el cuadro — 'Asentamiento alto' es difícil de defender; 'Asentamiento de 7 in en especificación de 4 in' es a prueba de balas.",
            "El PM solo ve registros en sus trabajos asignados. Elija el trabajo correcto — trabajo equivocado = PM equivocado.",
        ],
        "cheatSheet": [
            "3 inspection types today. Pick job → PM auto-fills. GPS for location. Work Area required.",
            "Min 3 photos. Every FAIL needs a note. Inspector signs. PM emailed automatically.",
        ],
        "cheatSheet_es": [
            "3 tipos hoy. Elija el trabajo → el PM se autollena. GPS para ubicación. Área de Trabajo requerida.",
            "Mín. 3 fotos. Cada FALLA necesita una nota. Inspector firma. PM recibe correo automático.",
        ],
    },
    {
        "slug": "field-04-safety-meeting",
        "order": 6,
        "title": "Lesson 6 — Safety Meetings (Toolbox Talks)",
        "title_es": "Lección 6 — Reuniones de Seguridad (Charlas de Caja)",
        "why": "Required daily huddle before work starts. Documents that the crew was briefed on today's hazards.",
        "why_es": "Junta diaria requerida antes de comenzar el trabajo. Documenta que la cuadrilla fue informada sobre los peligros de hoy.",
        "steps": [
            "Hub → Safety → Safety Meetings → New Meeting.",
            "Project, date/time, Conducted By, Topic Category.",
            "Tap 'Topic Library', search (trench, silica, heat). 80+ prefilled topics. Or Custom Topic.",
            "Review / edit Hazards, Notes, References, Actions.",
            "Add every attendee — each signs.",
            "Conductor signs. Submit.",
        ],
        "steps_es": [
            "Hub → Seguridad → Reuniones de Seguridad → Nueva Reunión.",
            "Proyecto, fecha/hora, Conducida Por, Categoría del Tema.",
            "Toque 'Biblioteca de Temas', busque (zanja, sílice, calor). Más de 80 temas prellenados. O Tema Personalizado.",
            "Revise / edite Peligros, Notas, Referencias, Acciones.",
            "Agregue cada asistente — cada uno firma.",
            "Conductor firma. Envíe.",
        ],
        "tips": ["Do this BEFORE the crew picks up a shovel.", "Rotate who conducts each week — builds ownership."],
        "tips_es": ["Haga esto ANTES de que la cuadrilla levante una pala.", "Rote quién dirige cada semana — construye pertenencia."],
        "cheatSheet": ["80+ prefilled topics. Pick, edit, get signatures.", "Every attendee signs. Conductor signs. Submit."],
        "cheatSheet_es": ["Más de 80 temas prellenados. Elija, edite, obtenga firmas.", "Cada asistente firma. Conductor firma. Envíe."],
    },
    {
        "slug": "field-05-jhp",
        "order": 7,
        "title": "Lesson 7 — Job Hazard Plan (JHP)",
        "title_es": "Lección 7 — Plan de Peligros del Trabajo (JHP)",
        "why": "MASCI Job Hazard Plans are built before work begins by the Safety Department, Project Managers, and leadership — based on scope of work, site conditions, traffic control (MOT), environmental factors, and known project hazards. Hazards are identified and controlled BEFORE crews step onto the job. A properly built JHP is one of the strongest tools we have to prevent incidents.",
        "why_es": "Los JHPs de MASCI se preparan antes de que comience el trabajo, por el Departamento de Seguridad, los Gerentes de Proyecto y el liderazgo — basados en el alcance, condiciones del sitio, control de tráfico (MOT), factores ambientales y peligros conocidos del proyecto. Los peligros se identifican y controlan ANTES de que la cuadrilla pise el sitio. Un JHP bien hecho es una de las mejores herramientas para prevenir incidentes.",
        "steps": [
            "Crews do NOT build JHPs. JHPs are job-specific documents prepared in advance by Safety, PMs, and senior leadership.",
            "Each JHP covers project-wide hazards, locations by station number, required controls, environmental + site-specific risks, MOT hazards, and equipment/operational hazards.",
            "Every JHP package includes two documents: (1) JHP Document — full list of hazards, locations by station, required controls and safe practices; (2) Hazard Worksheet — hazard type, threat level, exact location, required controls, additional notes.",
            "Before starting work: review the JHP, understand the hazards in your work area, and follow every listed control.",
            "If anything is unclear or conditions don't match the plan: ask questions, and use Stop Work Authority. Do not improvise.",
            "This is NOT a form completed in the field. It is a pre-built safety system designed to protect the crew before work begins.",
        ],
        "steps_es": [
            "Las cuadrillas NO crean JHPs. Los JHPs son documentos del proyecto preparados con anticipación por Seguridad, PMs y el liderazgo.",
            "Cada JHP cubre los peligros del proyecto, ubicaciones por número de estación, controles requeridos, riesgos ambientales y del sitio, peligros de MOT y peligros del equipo/operación.",
            "Cada paquete JHP incluye dos documentos: (1) Documento JHP — lista completa de peligros, ubicaciones por estación, controles requeridos y prácticas seguras; (2) Hoja de Peligros — tipo de peligro, nivel de amenaza, ubicación exacta, controles requeridos, notas adicionales.",
            "Antes de comenzar: revise el JHP, entienda los peligros de su área, y siga cada control listado.",
            "Si algo no está claro o las condiciones no coinciden con el plan: pregunte, y use la Autoridad para Suspender el Trabajo. No improvise.",
            "Esto NO es un formulario que se llena en el campo. Es un sistema de seguridad pre-construido para proteger a la cuadrilla antes de comenzar el trabajo.",
        ],
        "tips": [
            "The JHP exists so every crew member understands the risks BEFORE they encounter them. Use it, follow it, and speak up if something doesn't match.",
            "Stop Work Authority: every crew member has it. No questions, no discipline — if conditions on the ground don't match the JHP, stop.",
        ],
        "tips_es": [
            "El JHP existe para que cada miembro entienda los riesgos ANTES de encontrarlos. Úselo, sígalo, y hable si algo no coincide.",
            "Autoridad para Suspender el Trabajo: cada miembro la tiene. Sin preguntas, sin disciplina — si las condiciones no coinciden con el JHP, pare.",
        ],
        "cheatSheet": [
            "JHPs are pre-built by Safety / PM / Leadership — not the crew.",
            "Two docs per job: JHP + Hazard Worksheet (with station numbers).",
            "Review before work. Follow controls. Stop Work if conditions change.",
        ],
        "cheatSheet_es": [
            "Los JHPs los prepara Seguridad / PM / Liderazgo — no la cuadrilla.",
            "Dos documentos por trabajo: JHP + Hoja de Peligros (con números de estación).",
            "Revise antes del trabajo. Siga los controles. Pare el Trabajo si cambian las condiciones.",
        ],
    },
    {
        "slug": "field-06-incident",
        "order": 8,
        "title": "Lesson 8 — Accident / Incident Reports",
        "title_es": "Lección 8 — Reportes de Accidente / Incidente",
        "why": "The moment something goes wrong, this is the form. Near miss → fatality — every level gets documented.",
        "why_es": "El momento que algo sale mal, este es el formulario. Cuasi-accidente → fatalidad — cada nivel se documenta.",
        "steps": [
            "SECURE THE SCENE FIRST. Medical for injured. 911 if serious. THEN open the app.",
            "Hub → Safety → Incident Reports → New Report.",
            "Date, time, location, Reported By, Supervisor.",
            "Incident Type + Severity Tier (drives OSHA reporting).",
            "Person Involved: name, role, employer, body part, nature, treatment, sent home.",
            "Description: sequence of events. Factual, specific.",
            "Root Cause: PPE, training, procedure, supervision, equipment, comms, fatigue, housekeeping, weather.",
            "Witnesses with short statements while fresh.",
            "Immediate + Long-Term Corrective Actions, owner, deadline.",
            "Notifications: Safety Manager, PM, GC, Owner, OSHA if catastrophic.",
            "Photos of scene, equipment, environment.",
            "Reporter + Supervisor sign. Submit.",
        ],
        "steps_es": [
            "ASEGURE LA ESCENA PRIMERO. Médica para lesionados. 911 si es grave. LUEGO abra la app.",
            "Hub → Seguridad → Reportes de Incidentes → Nuevo Reporte.",
            "Fecha, hora, ubicación, Reportado Por, Supervisor.",
            "Tipo + Nivel de Severidad (determina reporte OSHA).",
            "Persona Involucrada: nombre, rol, empleador, parte del cuerpo, naturaleza, tratamiento, enviado a casa.",
            "Descripción: secuencia de eventos. Factual, específico.",
            "Causa Raíz: EPP, capacitación, procedimiento, supervisión, equipo, comunicación, fatiga, orden, clima.",
            "Testigos con declaraciones cortas mientras está fresco.",
            "Acciones Inmediatas + Largo Plazo, responsable, fecha límite.",
            "Notificaciones: Gerente de Seguridad, Gerente de Proyecto, Contratista General, Dueño, OSHA si catastrófico.",
            "Fotos de la escena, equipo, ambiente.",
            "Reportero + Supervisor firman. Envíe.",
        ],
        "tips": ["Near Miss with severe potential stays 'Near Miss' — describe the potential.", "Safety is emailed automatically within seconds of submit."],
        "tips_es": ["Cuasi-Accidente con potencial severo queda 'Cuasi-Accidente' — describa el potencial.", "Seguridad recibe correo automático en segundos del envío."],
        "cheatSheet": ["Scene safe → medical first → app second.", "Type + Severity → Person → Story → Root Cause → Witnesses → Fixes → Photos.", "Reporter + Supervisor sign."],
        "cheatSheet_es": ["Escena segura → médica primero → app después.", "Tipo + Severidad → Persona → Historia → Causa Raíz → Testigos → Correcciones → Fotos.", "Reportero + Supervisor firman."],
    },
    {
        "slug": "field-07-site-inspection",
        "order": 9,
        "title": "Lesson 9 — Site Safety Inspection",
        "title_es": "Lección 9 — Inspección de Seguridad del Sitio",
        "why": "Daily and weekly walk-throughs to catch hazards before they hurt someone. Graded automatically so you can see if your site is passing OSHA.",
        "why_es": "Recorridos diarios y semanales para atrapar peligros antes de que lastimen a alguien. Calificado automáticamente para ver si su sitio pasa OSHA.",
        "steps": [
            "Hub → Safety → Site Inspections → New Inspection.",
            "Fill project, Day or Night, Inspector + Foreman names.",
            "List crew and subs onsite. Weather + activity.",
            "Grade PPE, Hazards, MOT, Fall Protection, Electrical, Housekeeping, Fire, Heat/Cold: Pass/Fail/N/A. Live Grade % updates.",
            "Photo any Fail. Note Stop Work, Corrected on Site, Responsible Party.",
            "Inspector + Foreman sign. Submit.",
        ],
        "steps_es": [
            "Hub → Seguridad → Inspecciones → Nueva Inspección.",
            "Llene proyecto, Día o Noche, nombres de Inspector + Capataz.",
            "Liste cuadrilla y subs en sitio. Clima + actividad.",
            "Califique EPP, Peligros, MOT, Caídas, Eléctrico, Orden, Fuego, Calor/Frío: Aprobado/Falla/N/A. % en vivo se actualiza.",
            "Foto a cada Falla. Anote Suspensión, Corregido en Sitio, Responsable.",
            "Inspector + Capataz firman. Envíe.",
        ],
        "tips": ["Weekly inspections are more thorough than daily.", "Live Grade below 80% should trigger a stand-down."],
        "tips_es": ["Las inspecciones semanales son más completas que las diarias.", "Calificación en Vivo bajo 80% debe activar una parada."],
        "cheatSheet": ["Pass/Fail each category. Photo every Fail.", "Live Grade shows where you stand. <80% = stand-down."],
        "cheatSheet_es": ["Aprobado/Falla por cada categoría. Foto a cada Falla.", "Calificación en Vivo muestra dónde está. <80% = parada."],
    },
    {
        "slug": "field-08-doc-ids",
        "order": 8,
        "title": "Lesson 8 — Doc IDs (every form's tracking number)",
        "title_es": "Lección 8 — Doc IDs (número de seguimiento de cada formulario)",
        "why": "Every form, report, inspection, and check-in is now stamped with a unique Doc ID (DR-2026-00042 etc.). It prints on the PDF, shows on screen, and goes in the email subject. When the office calls about a record, give them the Doc ID — they find it instantly.",
        "why_es": "Cada formulario, reporte e inspección lleva un Doc ID único (DR-2026-00042 etc.). Imprime en el PDF, aparece en pantalla, va en el asunto del correo. Cuando la oficina llame por un registro, deles el Doc ID — lo encuentran instantáneo.",
        "steps": [
            "After submit, the Thank-You screen shows the Doc ID at the top in big red text.",
            "PDF prints the Doc ID top-right in red on every page.",
            "Format: <KIND>-<YEAR>-<5digits>. DR=Daily, PRE=Pre-Op, INSP=Site Inspection, MTG=Toolbox, JHA=Job Hazard, INC=Incident, QC=QA/QC, EQC=Checkout, EQR=Return.",
            "Numbers reset every Jan 1. DR-2026-00001 was the first Daily Report of 2026.",
            "Office calls about a record → give them the Doc ID → they punch it into the Admin search bar and land instantly.",
        ],
        "steps_es": [
            "Después de enviar, la pantalla de Gracias muestra el Doc ID arriba en rojo grande.",
            "El PDF imprime el Doc ID arriba a la derecha en rojo en cada página.",
            "Formato: <TIPO>-<AÑO>-<5dígitos>. DR=Diario, PRE=Pre-Op, INC=Incidente, EQC=Checkout, EQR=Devolución.",
            "Los números reinician cada 1 de enero. DR-2026-00001 fue el primer Reporte Diario de 2026.",
            "Oficina llama por un registro → deles el Doc ID → lo meten en la barra de Admin y aterriza instantáneo.",
        ],
        "tips": ["Two Doc IDs on a Return form = parent Checkout reference (linked).", "Doc IDs never change — once stamped, that number belongs to that record forever."],
        "tips_es": ["Dos Doc IDs en un formulario de Devolución = referencia al Checkout padre (ligados).", "Los Doc IDs nunca cambian — una vez sellados, ese número es del registro para siempre."],
        "cheatSheet": ["Doc ID = <KIND>-<YEAR>-<5digit>. Top-right of every PDF.", "Office calls → give them the Doc ID → instant find."],
        "cheatSheet_es": ["Doc ID = <TIPO>-<AÑO>-<5dígitos>. Arriba a la derecha de cada PDF.", "Oficina llama → deles el Doc ID → encuentro instantáneo."],
    },
]


# --- Shop (3) ---
SHOP_LESSONS = [
    {
        "slug": "shop-01-portal-intro",
        "order": 1,
        "title": "Lesson 1 — Shop Portal Overview",
        "title_es": "Lección 1 — Panorama del Portal del Taller",
        "why": "The shop console is where mechanics see every Pre-Op submitted, what's flagged, and what needs attention. Each mechanic now has their OWN login (email + password) — the old shared password is retired. Per-user accounts mean every sign-off carries the mechanic's name automatically.",
        "why_es": "La consola del taller es donde los mecánicos ven cada Pre-Op enviado. Cada mecánico ahora tiene su PROPIO inicio de sesión (correo + contraseña) — la contraseña compartida está retirada. Cuentas individuales significan que cada firma lleva el nombre del mecánico automáticamente.",
        "steps": [
            "/shop/login → enter your work email AND your personal password.",
            "First-time login auto-redirects to /shop/change-password. Pick a new 6+ char password and confirm.",
            "Forgot password? Tap 'Forgot password?' on /shop/login → email link arrives within seconds (good for 30 min).",
            "4 stats: Inspections on file, Units flagged FAIL, Shop sign-offs, Equipment in fleet.",
            "Left: Open Items queue (every unsigned FAIL). Right: Trends.",
            "Below: Recent Pre-Op Inspections, Equipment List, Parts Catalog.",
            "Rotate password any time via 'CHANGE PASSWORD' button in the Hub header.",
            "Sign out top-right on shared computers.",
        ],
        "steps_es": [
            "/shop/login → ingrese correo + contraseña personal.",
            "Primer inicio redirige a /shop/change-password. Elija nueva contraseña 6+ caracteres y confirme.",
            "¿Olvidó contraseña? Toque 'Forgot password?' → enlace por correo (válido 30 min).",
            "4 estadísticas: Inspecciones, Unidades FALLA, Firmas del taller, Equipo en flota.",
            "Izquierda: cola de Artículos Abiertos. Derecha: Tendencias.",
            "Abajo: Inspecciones Recientes, Lista de Equipo, Catálogo de Partes.",
            "Rote contraseña con botón 'CHANGE PASSWORD' en el encabezado del Hub.",
            "Cierre sesión arriba a la derecha en computadoras compartidas.",
        ],
        "tips": [
            "Admin sees everything. PMs see trends but can't sign off.",
            "FAIL/out-of-service Pre-Ops auto-email every active mechanic.",
            "Locked out? Admin unlocks from /admin → Shop Users panel.",
        ],
        "tips_es": [
            "Admin ve todo. Gerentes ven tendencias pero no firman.",
            "Pre-Ops con FALLA o fuera de servicio envían correo a cada mecánico activo.",
            "¿Bloqueado? Admin desbloquea desde /admin → panel de Shop Users.",
        ],
        "cheatSheet": [
            "Email + password (both required). Forgot password works.",
            "First login forces password change.",
            "FAILs auto-email every active mechanic.",
            "Change Password in Hub header.",
        ],
        "cheatSheet_es": [
            "Correo + contraseña (ambos requeridos). Forgot password funciona.",
            "Primer inicio fuerza cambio de contraseña.",
            "Las FALLAS notifican a cada mecánico activo.",
            "Change Password en el encabezado del Hub.",
        ],
    },
    {
        "slug": "shop-02-signing-off",
        "order": 2,
        "title": "Lesson 2 — Signing Off a Failed Pre-Op",
        "title_es": "Lección 2 — Firmando un Pre-Op Fallido",
        "why": "A FAIL keeps the unit OUT OF SERVICE until the shop clears it. Your sign-off is the audit trail.",
        "why_es": "Un FALLO mantiene la unidad FUERA DE SERVICIO hasta que el taller la libere. Su firma es la bitácora.",
        "steps": [
            "Open Items → pick severity filter → 'Sign Off' on the row.",
            "Name + optional notes (parts replaced, follow-up).",
            "Outcome: Repaired / Tagged OOS / Parts ordered / No action.",
            "Sign Off → unit CLEARED (or stays OOS).",
            "Reopen undoes the stamp.",
        ],
        "steps_es": [
            "Artículos Abiertos → elija filtro → 'Firmar' en la fila.",
            "Nombre + notas opcionales (partes, seguimiento).",
            "Resultado: Reparado / Fuera de Servicio / Partes ordenadas / Sin acción.",
            "Firmar → unidad LIBERADA (o sigue FDS).",
            "Reabrir deshace el sello.",
        ],
        "tips": ["'Parts ordered' keeps unit OOS but shows progress.", "'Repaired' is the only outcome that returns unit to service."],
        "tips_es": ["'Partes ordenadas' mantiene FDS pero muestra progreso.", "'Reparado' es el único resultado que regresa la unidad al servicio."],
        "cheatSheet": ["Name → notes → outcome → Sign Off.", "Repaired = cleared. Parts ordered = still OOS but tracked.", "Reopen if you signed off too early."],
        "cheatSheet_es": ["Nombre → notas → resultado → Firmar.", "Reparado = liberada. Partes ordenadas = sigue FDS pero registrada.", "Reabra si firmó muy temprano."],
    },
    {
        "slug": "shop-03-parts-catalog",
        "order": 3,
        "title": "Lesson 3 — Parts Catalog + Order List",
        "title_es": "Lección 3 — Catálogo de Partes + Lista de Pedido",
        "why": "Every unit has its own parts list. Build the order in one tap per part, email the parts office in one tap at the end.",
        "why_es": "Cada unidad tiene su propia lista de partes. Arme el pedido con un toque por parte, envíelo a la oficina con un toque al final.",
        "steps": [
            "Shop Console → Parts Catalog → Pick Unit.",
            "5 categories. 'Add Part' → name, part #, qty, notes.",
            "'Save Catalog' to persist.",
            "Cart icon adds part to Order List panel.",
            "Order List: your name, parts-office email(s), CC, notes.",
            "'Email Order to Parts Office'. Done.",
        ],
        "steps_es": [
            "Consola del Taller → Catálogo → Elija Unidad.",
            "5 categorías. 'Agregar Parte' → nombre, #, cantidad, notas.",
            "'Guardar Catálogo' para persistir.",
            "Ícono de carrito agrega parte a la Lista de Pedido.",
            "Lista de Pedido: su nombre, correo(s), CC, notas.",
            "'Enviar Pedido a Oficina'. Listo.",
        ],
        "tips": ["Catalog persists — every mechanic benefits from building it once per unit.", "Common parts: add per-unit so quantities stack."],
        "tips_es": ["El catálogo persiste — cada mecánico se beneficia de armarlo una vez por unidad.", "Partes comunes: agregue por unidad para que se sumen cantidades."],
        "cheatSheet": ["Pick unit → Add Part → Save.", "Cart icon → Order List. Email at the end."],
        "cheatSheet_es": ["Elija unidad → Agregar Parte → Guardar.", "Carrito → Lista de Pedido. Correo al final."],
    },
    {
        "slug": "shop-04-account-and-password",
        "order": 4,
        "title": "Lesson 4 — Your Account, Login & Password",
        "title_es": "Lección 4 — Su Cuenta, Inicio de Sesión y Contraseña",
        "why": "Each mechanic has their own MASCI account so every Pre-Op sign-off, parts order, and fleet edit is traceable to the person who made it. Shared passwords are gone.",
        "why_es": "Cada mecánico tiene su propia cuenta MASCI para que cada firma, orden de partes y edición de flota sea trazable. Las contraseñas compartidas se acabaron.",
        "steps": [
            "Admin issues your account from /admin → Shop Users panel. Two delivery options: 'Show on Screen' or 'Email to User'.",
            "First login: /shop/login → email + temp password → auto-redirected to /shop/change-password. Pick 6+ char password.",
            "Change password any time: 'CHANGE PASSWORD' button in Shop Hub header → old + new + confirm.",
            "Forgot password: /shop/login → 'Forgot password?' → email link (good for 30 min) → pick new password → in.",
            "Teammate leaves: Admin disables their account from /admin → Shop Users → lock icon. Their token stops immediately.",
        ],
        "steps_es": [
            "Admin emite cuenta desde /admin → panel Shop Users. Dos opciones: 'Mostrar en Pantalla' o 'Enviar por Correo'.",
            "Primer inicio: /shop/login → correo + contraseña temp → redirigido a /shop/change-password. Elija 6+ caracteres.",
            "Cambie contraseña cuando quiera: botón 'CHANGE PASSWORD' en encabezado del Hub → vieja + nueva + confirmar.",
            "Olvidó contraseña: /shop/login → 'Forgot password?' → enlace por correo (válido 30 min) → nueva contraseña → adentro.",
            "Compañero se va: Admin desactiva desde /admin → Shop Users → ícono candado. Su token deja de funcionar inmediato.",
        ],
        "tips": ["Reset links good for 30 min only — request another if expired.", "Don't share password — your name stays on YOUR sign-offs."],
        "tips_es": ["Enlaces de reset válidos 30 min — pida otro si expiró.", "No comparta contraseña — su nombre queda en SUS firmas."],
        "cheatSheet": ["Email + password. Forgot link emails 30-min reset.", "Change Password button in Hub header any time.", "Don't share login = your name on your sign-offs."],
        "cheatSheet_es": ["Correo + contraseña. Forgot link envía reset 30 min.", "Botón Change Password en encabezado del Hub.", "No comparta login = su nombre en sus firmas."],
    },
]


# --- PM (6) ---
PM_LESSONS = [
    {
        "slug": "pm-01-portal-intro",
        "order": 1,
        "title": "Lesson 1 — PM Portal Overview",
        "title_es": "Lección 1 — Panorama del Portal de Gestión",
        "why": "Same surface as Admin for day-to-day work. Backup / restore / force-reseed are hidden from PMs — that's the Admin's job.",
        "why_es": "La misma superficie que Admin para el trabajo diario. Respaldo / restauración / force-reseed están ocultos de Gerentes — ese es trabajo del Admin.",
        "steps": [
            "/pm/login → enter PM password (ask supervisor) → Records & Forms.",
            "Tiles: P&L, Daily Reports, Inspections, Safety Meetings, JHP, Trench Box, Incidents, Pre-Op.",
            "Scroll to master lists: Jobs, Employees, Suppliers, Equipment, Parts.",
            "Top bar: ALL OK badge, Guide, Company Info, Sign Out.",
            "Backup / restore controls DO NOT appear in PM Portal.",
        ],
        "steps_es": [
            "/pm/login → ingrese la contraseña PM (pregunte al supervisor) → Registros y Formularios.",
            "Tarjetas: P&L, Reportes Diarios, Inspecciones, Reuniones, JHP, Caja de Zanja, Incidentes, Pre-Op.",
            "Baje a listas maestras: Trabajos, Empleados, Proveedores, Equipo, Partes.",
            "Barra superior: bandera ALL OK, Guía, Company Info, Cerrar Sesión.",
            "Controles de respaldo / restauración NO aparecen en Portal de Gestión.",
        ],
        "tips": ["PM token lasts until you sign out.", "Admin sees everything you see (and more). PMs cannot see what Admin sees."],
        "tips_es": ["Token PM dura hasta que cierre sesión.", "Admin ve todo lo que ve usted (y más). Gerentes no ven lo que ve Admin."],
        "cheatSheet": ["Records & Forms on top → master lists below.", "No backup/restore in PM. That's Admin only."],
        "cheatSheet_es": ["Registros arriba → listas maestras abajo.", "Sin respaldo/restauración en PM. Solo Admin."],
    },
    {
        "slug": "pm-02-master-lists",
        "order": 2,
        "title": "Lesson 2 — Master Lists (Jobs / Employees / Suppliers / Equipment / Parts)",
        "title_es": "Lección 2 — Listas Maestras",
        "why": "These 5 lists power every dropdown in the field app. Keeping them clean = the whole app stays clean.",
        "why_es": "Estas 5 listas alimentan cada menú del app. Mantenerlas limpias = toda la app se mantiene limpia.",
        "steps": [
            "'Add New' for inline type. Click cell to edit. Changes save on blur.",
            "Bulk Replace: paste spreadsheet → list wiped and rebuilt. Old data soft-deleted (14-day undo).",
            "Red 🗑️ → row moves to Archive tab (NOT permanently deleted).",
            "Archive tab: see deleted rows, 'Restore' pulls them back. After 14 days → permanent.",
            "Export: downloads XLSX. Round-trips cleanly into Bulk Replace.",
        ],
        "steps_es": [
            "'Agregar Nuevo' para escribir en línea. Clic en celda para editar. Guarda al salir.",
            "Reemplazo Masivo: pegue hoja → lista borrada y reconstruida. Datos viejos con borrado suave (undo 14 días).",
            "🗑️ rojo → fila al Archivo (NO borrada permanentemente).",
            "Pestaña Archivo: vea filas borradas, 'Restaurar' las regresa. Después de 14 días → permanente.",
            "Exportar: descarga XLSX. Round-trip limpio a Reemplazo Masivo.",
        ],
        "tips": ["14-day soft-delete is your safety net.", "Bulk-replaced by mistake? Every old row is in Archive."],
        "tips_es": ["Borrado suave de 14 días es su red de seguridad.", "¿Reemplazo masivo por error? Cada fila vieja está en Archivo."],
        "cheatSheet": ["Add New → inline. Click cell → edit.", "🗑️ = soft delete. Archive tab = 14-day undo.", "Bulk Replace = wipe + seed. Export = XLSX."],
        "cheatSheet_es": ["Agregar Nuevo → en línea. Clic en celda → editar.", "🗑️ = borrado suave. Archivo = undo 14 días.", "Reemplazo Masivo = borrar + sembrar. Exportar = XLSX."],
    },
    {
        "slug": "pm-03-import-export",
        "order": 3,
        "title": "Lesson 3 — Import / Export Round-Trips",
        "title_es": "Lección 3 — Round-Trips de Importar / Exportar",
        "why": "Your master lists may be the cleanest copy of this data the company has. Export regularly so finance, insurance, and auditors can pull fresh data.",
        "why_es": "Sus listas maestras pueden ser la copia más limpia de estos datos. Exporte regularmente para finanzas, seguros y auditores.",
        "steps": [
            "'Export' (green) → timestamped XLSX downloads.",
            "Edit offline in Excel/Sheets.",
            "'Bulk Replace' → drop the workbook. List rebuilt.",
            "Verify: re-export and diff. Should match byte-for-byte.",
        ],
        "steps_es": [
            "'Exportar' (verde) → descarga XLSX con marca de tiempo.",
            "Edite fuera de línea en Excel/Sheets.",
            "'Reemplazo Masivo' → suelte el libro. Lista reconstruida.",
            "Verifique: re-exporte y compare. Debe coincidir byte por byte.",
        ],
        "tips": ["Stage big imports against a 5-row copy first.", "Archive tab holds the replaced rows for 14 days."],
        "tips_es": ["Pruebe importaciones grandes con copia de 5 filas primero.", "Pestaña Archivo guarda las filas reemplazadas por 14 días."],
        "cheatSheet": ["Export → edit offline → Bulk Replace back in.", "Round-trip matches byte-for-byte."],
        "cheatSheet_es": ["Exportar → editar fuera de línea → Reemplazo Masivo.", "Round-trip coincide byte por byte."],
    },
    {
        "slug": "pm-04-archive",
        "order": 4,
        "title": "Lesson 4 — Archive & 14-Day Undo",
        "title_es": "Lección 4 — Archivo y Undo de 14 Días",
        "why": "Every delete is soft. Rows aren't gone — they sit in Archive for 14 days, then get purged. Safety net for a bad Friday click.",
        "why_es": "Cada borrado es suave. Las filas no se van — están en Archivo por 14 días, luego se purgan. Red para un mal clic de viernes.",
        "steps": [
            "Any master list → 'Archive' tab at top.",
            "See each deleted row: what, who, when, days until purge.",
            "'Restore' pulls it back into live list instantly.",
            "Rows >14 days old auto-purged by background job.",
            "Admin only: 'Purge Now' button for compliance sweeps.",
        ],
        "steps_es": [
            "Cualquier lista maestra → pestaña 'Archivo' arriba.",
            "Vea cada fila borrada: qué, quién, cuándo, días hasta purga.",
            "'Restaurar' la regresa a lista en vivo al instante.",
            "Filas >14 días auto-purgadas por trabajo en segundo plano.",
            "Solo Admin: botón 'Purgar Ahora' para barridas de cumplimiento.",
        ],
        "tips": ["Unfamiliar row in Archive? Check with Admin before restoring.", "14-day window is a HARD cap."],
        "tips_es": ["¿Fila desconocida en Archivo? Consulte con Admin antes de restaurar.", "Ventana de 14 días es un límite DURO."],
        "cheatSheet": ["Archive tab = soft-deleted rows.", "Restore → back in live list.", "Purged after 14 days. Then only a backup saves it."],
        "cheatSheet_es": ["Pestaña Archivo = filas con borrado suave.", "Restaurar → de vuelta en la lista.", "Purgado después de 14 días. Luego solo un respaldo salva."],
    },
    {
        "slug": "pm-05-email-routing",
        "order": 5,
        "title": "Lesson 5 — Email Routing (PM & Safety)",
        "title_es": "Lección 5 — Ruteo de Correos",
        "why": "Every form is auto-emailed to the PM and (for compliance kinds) the office always-CC. Admin can now change WHO gets what email straight from /admin → Email Routing — no redeploy.",
        "why_es": "Cada formulario va al Gerente y (para tipos de cumplimiento) la lista always-CC de oficina. Admin ahora cambia QUIÉN recibe qué desde /admin → Email Routing — sin redespliegue.",
        "steps": [
            "PM Portal → Project Manager roster + Jobs master.",
            "Each Job: Primary PM + up to 4 co-PMs. Email auto-fills, all CC'd on every report.",
            "Compliance kinds (Site Inspection, Toolbox, JHA, Incident, QA/QC) ALSO get office always-CC. Daily/Pre-Op do NOT — PM only.",
            "Pre-Op FAIL emails fan out to every active mechanic.",
            "Admin overrides every list (compliance always-CC, Safety Forms, Leadership CC, Severe Incident extras, Shop fallback, Daily backup) in /admin → Email Routing.",
        ],
        "steps_es": [
            "Portal del PM → roster de Gerentes + maestro de Trabajos.",
            "Cada Trabajo: Gerente Primario + hasta 4 co-Gerentes. Correo autocompleta, todos CC en cada reporte.",
            "Tipos de cumplimiento (Inspección, Junta, JHA, Incidente, QA/QC) TAMBIÉN reciben always-CC de oficina. Diario/Pre-Op NO — solo PM.",
            "Correos de FALLA de Pre-Op se envían a cada mecánico activo.",
            "Admin sobrescribe cada lista en /admin → Email Routing.",
        ],
        "tips": ["AUTO_EMAIL_REPORTS env flag: ON in prod, OFF in preview.", "Not receiving: check active toggle, job assignment, spam, then /admin → Email Routing → 'Send test email'.", "Adding a co-PM auto-CCs them on every record for that job."],
        "tips_es": ["Bandera AUTO_EMAIL_REPORTS: ON en prod, OFF en preview.", "No recibe: revise activo, asignación, spam, luego /admin → Email Routing → 'Send test email'.", "Agregar co-Gerente auto-CC en cada registro de ese trabajo."],
        "cheatSheet": ["Job → Primary PM + Co-PMs → email + CCs automatically.", "Compliance = office CC. Operational = PM only.", "Admin → Email Routing for every override."],
        "cheatSheet_es": ["Trabajo → Gerente Primario + Co-Gerentes → correo automático.", "Cumplimiento = CC oficina. Operacional = solo PM.", "Admin → Email Routing para overrides."],
    },
    {
        "slug": "pm-06-posters-jha",
        "order": 6,
        "title": "Lesson 6 — Site Posters + JHP Plans",
        "title_es": "Lección 6 — Carteles + Planes JHP",
        "why": "Site Posters are printable handouts you tape inside trailers. JHP Plans are per-job PDFs for foremen to read before breaking ground.",
        "why_es": "Carteles del Sitio son folletos que pega en tráileres. Planes JHP son PDFs por trabajo para capataces antes de comenzar.",
        "steps": [
            "PM Portal → Site Posters. Three posters (Cheat Sheet, Trench Box, JHP Plans).",
            "Preview → Print → Tape in every active trailer.",
            "JHP Plans Admin: upload PDF per active job. Max 10 MB.",
            "Crews: Safety → JHP Plans → pick job → read PDF. No login.",
            "Offline: tap PDF → share menu → save to Files.",
        ],
        "steps_es": [
            "Portal de Gestión → Carteles. Tres carteles (Referencia, Caja de Zanja, JHP).",
            "Vista previa → Imprimir → Pegar en tráileres activos.",
            "Admin JHP: suba PDF por trabajo activo. Máximo 10 MB.",
            "Cuadrillas: Seguridad → Planes JHP → elija trabajo → lea PDF. Sin login.",
            "Sin conexión: toque PDF → compartir → guardar en Archivos.",
        ],
        "tips": ["Reprint quarterly — QRs don't change, paper fades.", "Upload JHP before Day 1 of every new job."],
        "tips_es": ["Reimprima trimestralmente — QRs no cambian, papel se desgasta.", "Suba JHP antes del Día 1 de cada trabajo."],
        "cheatSheet": ["Posters → print → tape in trailer.", "JHP PDF per job → readable offline on phones."],
        "cheatSheet_es": ["Carteles → imprimir → pegar en tráiler.", "PDF JHP por trabajo → legible sin conexión."],
    },
    {
        "slug": "pm-07-field-leadership",
        "order": 7,
        "title": "Lesson 7 — Field Leadership Hub (PM perspective)",
        "title_es": "Lección 7 — Hub de Field Leadership (perspectiva del PM)",
        "why": "Field Leadership is the supervisor toolkit (10 forms — write-ups, coaching, equipment checkout/return, evaluations, supervisor notes). PM is the routing destination for every leadership record on their jobs.",
        "why_es": "Field Leadership es el kit del supervisor (10 formularios). El PM es el destino de ruteo para cada registro en sus trabajos.",
        "steps": [
            "Every Field Leadership record auto-emails to assigned PM, jaymn.judd@mascigc.com, and safety@mascigc.com. PDF attached.",
            "Browse: /pm → Field Leadership records (or /leadership/records). Filter by kind, date, employee, project. PMs see only their job records — admin sees all.",
            "Tap any record → detail page → Doc ID badge (e.g. EQR-2026-00012), full form data, signatures, photos.",
            "Equipment Checkout: per-item photos in page + PDF. EVERY item has Mfg/Name/Model/SN/qty/replacement value/2+ photos.",
            "Equipment Return: side-by-side 'Original at Checkout' (emerald) vs. 'Returned Condition' (amber/red) photo comparison. Damage Owed pill turns red when items Damaged/Missing/Lost.",
            "Export: 'CSV' button on records page pulls filtered list with all metadata.",
        ],
        "steps_es": [
            "Cada registro envía correo al PM asignado, jaymn.judd@mascigc.com, y safety@mascigc.com. PDF adjunto.",
            "Navegar: /pm → registros de Field Leadership (o /leadership/records). Filtre por tipo, fecha, empleado, proyecto.",
            "Toque cualquier registro → página detalle → badge Doc ID, datos del formulario, firmas, fotos.",
            "Equipment Checkout: fotos por artículo en página + PDF. CADA artículo: Marca/Nombre/Modelo/Serie/cant/valor/2+ fotos.",
            "Equipment Return: comparación lado-a-lado Original vs. Devolución. Damage Owed se pone rojo si Dañado/Perdido.",
            "Exportar: botón 'CSV' en página de registros descarga lista filtrada con metadatos.",
        ],
        "tips": ["Supervisor Notes are admin-strict to file (Foremen don't access).", "Equipment Return uses Doc ID of original Checkout for the side-by-side.", "Use Doc ID search bar in /admin to jump to a leadership record by its ID."],
        "tips_es": ["Notas del Supervisor son admin-estricto para presentar (Capataces no acceden).", "Return usa Doc ID del Checkout original para lado-a-lado.", "Use búsqueda Doc ID en /admin para saltar a un registro."],
        "cheatSheet": ["PM auto-CC'd on every Field Leadership record on their jobs.", "/leadership/records → filter, search, open, export.", "Equipment Return shows side-by-side photo comparison + Damage Owed pill."],
        "cheatSheet_es": ["PM auto-CC en cada registro en sus trabajos.", "/leadership/records → filtrar, buscar, abrir, exportar.", "Return muestra comparación lado-a-lado + badge Damage Owed."],
    },
    {
        "slug": "pm-08-job-photos",
        "order": 8,
        "title": "Lesson 8 — Job Photos Library",
        "title_es": "Lección 8 — Biblioteca de Fotos del Trabajo",
        "why": "Every photo crews submit on Daily Reports, Site Inspections, QA/QC inspections is mirrored to a single browsable gallery — Job → Week. Multi-select to download ZIP or email a packet to a GC, insurance adjuster, or attorney.",
        "why_es": "Cada foto que las cuadrillas envían se replica a una galería buscable única — Trabajo → Semana. Selección múltiple para ZIP o correo a GC, ajustador de seguros, abogado.",
        "steps": [
            "PM Portal → Job Photos (or /pm/photos). Scoped to assigned jobs (admin sees all).",
            "Folder accordion: Job (with Doc ID) → Weeks → photos with source badge (DR=red, INSP=amber, QC=green) and date.",
            "Search bar: project number, employee name, partial job name. Source filter narrows by kind.",
            "Click photo → lightbox (full-resolution). Esc to close.",
            "Multi-select: tap checkbox top-right of tile. Action bar: Selected count + Email + Download ZIP.",
            "Download ZIP: <Job>/<Week>/<source>__<date>__N.<ext>. Cap 1000 photos.",
            "Email packet: type recipient(s), subject, optional note. ZIP attached. Cap 200 photos / 25 MB.",
            "iPhone HEIC photos render correctly (backend converts HEIC → WebP/AVIF/JPEG). Pre-Op photos NOT in library — diagnostic, not progress documentation.",
        ],
        "steps_es": [
            "Portal del PM → Job Photos (o /pm/photos). Limitado a trabajos asignados (admin ve todo).",
            "Acordeón de carpetas: Trabajo (con Doc ID) → Semanas → fotos con badge de fuente (DR=rojo, INSP=ámbar, QC=verde) y fecha.",
            "Búsqueda: número de proyecto, empleado, nombre parcial. Filtro de fuente reduce a un tipo.",
            "Clic foto → lightbox (resolución completa). Esc cierra.",
            "Selección múltiple: casilla arriba-derecha del mosaico. Barra: cuenta + Email + Download ZIP.",
            "ZIP: <Trabajo>/<Semana>/<fuente>__<fecha>__N.<ext>. Tope 1000 fotos.",
            "Email packet: destinatario(s), asunto, nota opcional. ZIP adjunto. Tope 200 fotos / 25 MB.",
            "Fotos HEIC del iPhone renderizan bien (backend convierte). Fotos Pre-Op NO en biblioteca — son diagnóstico.",
        ],
        "tips": ["Photos NOT duplicated — library reads from original record. Delete photo on Daily = library entry vanishes.", "Email packet = fastest way to send insurance/legal documentation.", "Galleries load instant the second time (7-day thumbnail cache). New photos warm in background within 10 min."],
        "tips_es": ["Fotos NO duplicadas — biblioteca lee del original. Borre en Diario = entrada desaparece.", "Email packet = forma más rápida de enviar documentación seguro/legal.", "Galerías cargan instantáneo segunda vez (caché 7 días). Nuevas fotos calientan en background en 10 min."],
        "cheatSheet": ["PM Portal → Job Photos. Folders by Job → Week.", "Multi-select → Download ZIP or Email packet.", "Caps: 1000 photos/ZIP, 200 photos / 25 MB per email."],
        "cheatSheet_es": ["Portal PM → Job Photos. Carpetas Trabajo → Semana.", "Selección múltiple → ZIP o Email packet.", "Topes: 1000 fotos/ZIP, 200 / 25 MB por correo."],
    },
]


# --- Admin (7) ---
ADMIN_LESSONS = [
    {
        "slug": "admin-01-platform-overview",
        "order": 1,
        "title": "Lesson 1 — Platform Overview",
        "title_es": "Lección 1 — Panorama de la Plataforma",
        "why": "You hold the admin password. Everything a PM can do, plus controls that keep the platform safe — backups, restores, force-reseed, audits.",
        "why_es": "Usted tiene la contraseña admin. Todo lo de Gerente, más controles para mantener la plataforma segura — respaldos, restauraciones, force-reseed, auditorías.",
        "steps": [
            "React (frontend) + FastAPI (backend) + MongoDB. Deployed at mascidocs.com.",
            "3 access tiers: Admin, PM, Shop — each has its own password, issued offline by Safety Department leadership.",
            "/admin/login. Lands on Records & Forms + System Recovery at bottom.",
            "Top panels: Dashboards, Master Lists, Forms, Email Routing, Posters, JHP, Trench Boxes, PMs, System Recovery.",
            "System Recovery (admin-strict): Backup, Integrity Check, On-Server Backups, Crew Recovery, Force-Reseed.",
            "Scheduled backups: 02:00 + 18:00 UTC daily. 14-day retention. Auto-pruned.",
        ],
        "steps_es": [
            "React + FastAPI + MongoDB. Desplegado en mascidocs.com.",
            "3 niveles de acceso: Admin, PM, Taller — cada uno tiene su propia contraseña, emitida fuera de línea por el liderazgo del Departamento de Seguridad.",
            "/admin/login. Aterriza en Registros + Recuperación del Sistema abajo.",
            "Paneles: Tableros, Listas Maestras, Formularios, Ruteo, Carteles, JHP, Cajas de Zanja, Gerentes, Recuperación.",
            "Recuperación (admin-estricto): Respaldo, Verificación de Integridad, Respaldos, Recuperación de Cuadrilla, Force-Reseed.",
            "Respaldos programados: 02:00 + 18:00 UTC diarios. 14 días de retención. Auto-podados.",
        ],
        "tips": ["Never share admin password. Rotate via ADMIN_PASSWORD env var.", "No reason to 'be a PM' as admin."],
        "tips_es": ["Nunca comparta contraseña admin. Rote vía variable env ADMIN_PASSWORD.", "Sin razón para 'ser Gerente' siendo admin."],
        "cheatSheet": ["Admin = PM + System Recovery.", "3 password tiers: Admin > PM > Shop.", "Backups run 02:00 + 18:00 UTC. 14-day retention. Automatic."],
        "cheatSheet_es": ["Admin = Gerente + Recuperación del Sistema.", "3 niveles: Admin > Gerente > Taller.", "Respaldos 02:00 + 18:00 UTC. 14 días retención. Automático."],
    },
    {
        "slug": "admin-02-backups-how",
        "order": 2,
        "title": "Lesson 2 — How Backups Work (Automatic + Manual)",
        "title_es": "Lección 2 — Cómo Funcionan los Respaldos",
        "why": "If mascidocs.com's DB disappeared right now, backups are the only thing that bring MASCI's records back. Know EXACTLY how they run.",
        "why_es": "Si la DB de mascidocs.com desapareciera ahora, los respaldos son lo único que trae los registros de vuelta. Sepa EXACTAMENTE cómo corren.",
        "steps": [
            "Scheduled: 02:00 UTC (~10pm Eastern) and 18:00 UTC (~2pm Eastern). BACKUP_HOURS_UTC env var.",
            "Content: ONE zip per run — MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip. Every collection as JSON + all uploaded files.",
            "Storage: /app/backend/backups/. Listed via Admin → On-Server Backups.",
            "Retention: 14 days. Auto-pruned on every run (pre-flight).",
            "Manual: Admin → System Recovery → 'Backup + email + download NOW'. ~30 sec. Download + email to BACKUP_EMAIL_TO.",
            "Inside the .zip: normal file. Unzip in Explorer/Finder. JSON per collection. PDFs. Base64 photos. Not encrypted — store safely.",
            "Integrity Check: compares live DB vs last backup manifest. Run before every deploy.",
            "Scheduled backup failed? Check /app/backend logs (grep 'scheduled-backup'). Usually disk space.",
        ],
        "steps_es": [
            "Programados: 02:00 UTC (~10pm Este) y 18:00 UTC (~2pm Este). Variable BACKUP_HOURS_UTC.",
            "Contenido: UN zip por corrida — MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip. Cada colección en JSON + archivos subidos.",
            "Almacenamiento: /app/backend/backups/. Listado vía Admin → Respaldos en Servidor.",
            "Retención: 14 días. Auto-podados en cada corrida (pre-flight).",
            "Manual: Admin → Recuperación → 'Respaldo + correo + descargar AHORA'. ~30 seg. Descarga + correo a BACKUP_EMAIL_TO.",
            "Dentro del .zip: archivo normal. Descomprima en Explorador/Finder. JSON por colección. PDFs. Fotos base64. No encriptado — guarde seguro.",
            "Verificación de Integridad: compara DB en vivo vs último manifiesto. Corra antes de cada despliegue.",
            "¿Respaldo programado falló? Revise logs /app/backend (grep 'scheduled-backup'). Usualmente espacio en disco.",
        ],
        "tips": ["Manual backup before any redeploy. 30 sec. Saves you from hidden env var flips.", "BACKUP_EMAIL_TO must be right in prod env.", "DON'T delete .zips unless you have another copy."],
        "tips_es": ["Respaldo manual antes de cualquier redespliegue. 30 seg. Lo salva de cambios env ocultos.", "BACKUP_EMAIL_TO debe estar correcto en env de prod.", "NO borre .zips a menos que tenga otra copia."],
        "cheatSheet": ["Auto: 02:00 + 18:00 UTC. 14-day retention.", "Manual: Admin → Backup + email + download NOW.", "Integrity Check before every deploy.", "BACKUP_EMAIL_TO must be set in prod env."],
        "cheatSheet_es": ["Auto: 02:00 + 18:00 UTC. 14 días retención.", "Manual: Admin → Respaldo + correo + descargar.", "Verificación de Integridad antes de cada despliegue.", "BACKUP_EMAIL_TO configurado en env de prod."],
    },
    {
        "slug": "admin-03-restore",
        "order": 3,
        "title": "Lesson 3 — How to Restore from a Backup",
        "title_es": "Lección 3 — Cómo Restaurar desde un Respaldo",
        "why": "You have a .zip. Something went wrong. You need data back. This is the exact flow.",
        "why_es": "Tiene un .zip. Algo salió mal. Necesita datos de vuelta. Este es el flujo exacto.",
        "steps": [
            "Single soft-deleted row? Use Archive tab — faster and safer than full restore.",
            "Grab a .zip from Admin → On-Server Backups, or your email inbox.",
            "Admin → System Recovery → 'Restore From File' → pick .zip. Max 500 MB.",
            "Restore MERGES: existing rows overwritten with backup copy. New rows added. Rows not in backup LEFT ALONE.",
            "Confirmation modal → 'Yes, restore it'.",
            "Watch progress. 'Restored X records across Y collections.'",
            "Sanity-check dashboards.",
        ],
        "steps_es": [
            "¿Una sola fila borrada suave? Use pestaña Archivo — más rápido y seguro que restauración completa.",
            "Obtenga .zip de Admin → Respaldos en Servidor, o su correo.",
            "Admin → Recuperación → 'Restaurar Desde Archivo' → elija .zip. Máximo 500 MB.",
            "Restaurar FUSIONA: filas existentes sobrescritas con copia del respaldo. Filas nuevas agregadas. Filas no en respaldo DEJADAS INTACTAS.",
            "Modal → 'Sí, restaurar'.",
            "Vea progreso. 'Restaurados X registros en Y colecciones.'",
            "Revise tableros.",
        ],
        "tips": ["Restores NEVER wipe. To rollback bad change: restore + manually delete new bad rows.", "Older .zip than live data = you'll overwrite fresh with stale. Think first."],
        "tips_es": ["Restauraciones NUNCA borran. Para revertir: restaurar + borrar manualmente filas nuevas malas.", ".zip más viejo que datos en vivo = sobrescribirá fresco con viejo. Piense primero."],
        "cheatSheet": ["Restore = merge. Never wipes. Old rows restored + new rows ADDED.", "True rollback: restore + manually delete new bad rows.", "Soft-delete tab is faster for single-row mistakes."],
        "cheatSheet_es": ["Restaurar = fusionar. Nunca borra. Filas viejas restauradas + nuevas AGREGADAS.", "Rollback real: restaurar + borrar manualmente filas nuevas.", "Pestaña de borrado suave es más rápida para errores de una fila."],
    },
    {
        "slug": "admin-04-integrity-check",
        "order": 4,
        "title": "Lesson 4 — Integrity Check & Audit Trail",
        "title_es": "Lección 4 — Verificación de Integridad y Auditoría",
        "why": "Trust but verify. Integrity Check proves every live collection is captured in the most recent backup.",
        "why_es": "Confíe pero verifique. Verificación de Integridad prueba que cada colección en vivo está capturada en el respaldo más reciente.",
        "steps": [
            "Admin → System Recovery → Integrity Check.",
            "Output: last_backup_filename, last_backup_at, live_collections, captured_collections, missing_from_backup, ok.",
            "ok=false? Run manual backup immediately. If still missing next scheduled, backup code needs patch.",
            "Run: after feature releases adding collections, before prod deploys, monthly sweeps.",
        ],
        "steps_es": [
            "Admin → Recuperación → Verificación de Integridad.",
            "Salida: last_backup_filename, last_backup_at, live_collections, captured_collections, missing_from_backup, ok.",
            "¿ok=false? Corra respaldo manual. Si sigue faltando, código de respaldo necesita parche.",
            "Corra: después de features con colecciones nuevas, antes de despliegues, barridas mensuales.",
        ],
        "tips": ["Current audit: all 23 collections captured.", "Integrity check is cheap (<1 sec). Run it often."],
        "tips_es": ["Auditoría actual: las 23 colecciones capturadas.", "Verificación es barata (<1 seg). Córrala frecuentemente."],
        "cheatSheet": ["Integrity Check = do live collections match last backup's manifest?", "ok=true → all good. ok=false → run manual backup now."],
        "cheatSheet_es": ["Verificación = ¿coinciden colecciones en vivo con manifiesto?", "ok=true → bien. ok=false → respaldo manual ahora."],
    },
    {
        "slug": "admin-05-crew-recovery",
        "order": 5,
        "title": "Lesson 5 — Crew Recovery Tools (Force-Reseed, Password Reset)",
        "title_es": "Lección 5 — Herramientas de Recuperación",
        "why": "Rare-use tools for when seed data drifts or a redeploy loses seed. Admin-only. Most admins never touch these.",
        "why_es": "Herramientas de uso raro cuando datos sembrados se corrompen o redespliegue pierde semilla. Solo Admin. La mayoría nunca las toca.",
        "steps": [
            "Status: /api/admin/crew-recovery/status. Shows live DB vs seed counts.",
            "Reset Password: /api/admin/crew-recovery/reset-password. Rare.",
            "Force-Reseed: WIPES + rebuilds jobs_master, employees, suppliers from hard-coded JOB_LIBRARY. All edits LOST.",
            "Before force-reseed: manual backup. Confirm you want to lose edits. Then click.",
            "Scrap-Crew-Hub: already run historically. Don't re-run.",
        ],
        "steps_es": [
            "Estado: /api/admin/crew-recovery/status. Muestra DB en vivo vs semilla.",
            "Reiniciar Contraseña: /api/admin/crew-recovery/reset-password. Raro.",
            "Force-Reseed: BORRA + reconstruye jobs_master, employees, suppliers desde JOB_LIBRARY. Todas las ediciones PERDIDAS.",
            "Antes: respaldo manual. Confirme que quiere perder ediciones. Luego clic.",
            "Scrap-Crew-Hub: ya corrido. No re-correr.",
        ],
        "tips": ["PM replaced all employees with 2 test rows? DON'T force-reseed — restore from Archive.", "All recovery routes require_admin_strict. PM/Shop tokens return 401."],
        "tips_es": ["¿Gerente reemplazó todos los empleados con 2 filas? NO force-reseed — restaure desde Archivo.", "Todas las rutas require_admin_strict. Tokens PM/Taller regresan 401."],
        "cheatSheet": ["Force-reseed = wipe + seed from JOB_LIBRARY. Last resort.", "Always manual-backup FIRST.", "Prefer Archive restore for single-row mistakes."],
        "cheatSheet_es": ["Force-reseed = borrar + sembrar desde JOB_LIBRARY. Último recurso.", "Siempre respaldo manual PRIMERO.", "Prefiera Archivo para errores de una fila."],
    },
    {
        "slug": "admin-06-deploy-redeploy",
        "order": 6,
        "title": "Lesson 6 — Safe Deploy / Redeploy Workflow",
        "title_es": "Lección 6 — Flujo de Despliegue Seguro",
        "why": "Every redeploy is a chance for something to break. The routine below has shipped 20+ deploys without data loss.",
        "why_es": "Cada redespliegue es oportunidad de romper algo. La rutina abajo ha enviado más de 20 despliegues sin pérdida.",
        "steps": [
            "1 — BACKUP. Admin → 'Backup + email + download NOW'. Green check.",
            "2 — Integrity Check. Confirm ok: true.",
            "3 — Save-to-GitHub in deploy chat input.",
            "4 — Verify production env vars: ADMIN/PM/SHOP_PASSWORD, HMAC_SECRET, CORS, MONGO, BACKUP_EMAIL_TO, RESEND_API_KEY, AUTO_EMAIL_REPORTS, RATE_LIMITING.",
            "5 — Deploy. Wait for build.",
            "6 — Smoke: curl /api/health, login all 3 tiers, spot-check dashboards, Backup panel.",
            "7 — Post-deploy Integrity Check.",
            "Issues? Rollback in deployment dashboard. Data drift? Restore Step-1 backup.",
        ],
        "steps_es": [
            "1 — RESPALDO. Admin → 'Respaldo + correo + descargar AHORA'. Palomita verde.",
            "2 — Verificación de Integridad. Confirme ok: true.",
            "3 — Save-to-GitHub en input de chat del despliegue.",
            "4 — Verifique env: ADMIN/PM/SHOP_PASSWORD, HMAC_SECRET, CORS, MONGO, BACKUP_EMAIL_TO, RESEND_API_KEY, AUTO_EMAIL_REPORTS, RATE_LIMITING.",
            "5 — Desplegar. Espere compilación.",
            "6 — Prueba: curl /api/health, login en 3 niveles, tableros, panel Respaldo.",
            "7 — Verificación de Integridad post-despliegue.",
            "¿Problemas? Rollback en tablero de despliegue. ¿Datos cambiaron? Restaure del Paso 1.",
        ],
        "tips": ["Rollback is free and fast. Don't hesitate.", "Keep pre-deploy backup for a week after deploy."],
        "tips_es": ["Rollback es gratis y rápido. No dude.", "Guarde respaldo pre-despliegue por una semana."],
        "cheatSheet": ["Backup → Integrity Check → GitHub → Deploy → Smoke → Integrity Check.", "Rollback if anything's off. Debug later."],
        "cheatSheet_es": ["Respaldo → Integridad → GitHub → Desplegar → Prueba → Integridad.", "Rollback si algo no está bien. Debugee después."],
    },
    {
        "slug": "admin-07-security-passwords",
        "order": 7,
        "title": "Lesson 7 — Passwords, Access, and Security",
        "title_es": "Lección 7 — Contraseñas, Acceso y Seguridad",
        "why": "Weakest link is the password. Here's the token model and what to do when a password leaks or someone leaves.",
        "why_es": "Eslabón más débil es la contraseña. Aquí está el modelo de token y qué hacer cuando se filtra o alguien se va.",
        "steps": [
            "Passwords in env vars: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD.",
            "POST /api/{admin|pm|shop}/login → 64-char HMAC token → localStorage → X-{Admin|PM|Shop}-Token header.",
            "No token expiry. Rotating password invalidates every session instantly.",
            "Rotate: change env var → redeploy → all old tokens die.",
            "Rate limit: LOGIN_MAX_FAILS=10, LOGIN_LOCKOUT_SECONDS=900 (15 min IP block).",
            "CORS: only mascidocs.com + www origin. Preview via CORS_ORIGIN_REGEX.",
            "Someone leaves → rotate their tier's password. Inform out-of-band (Signal/phone). NOT email.",
        ],
        "steps_es": [
            "Contraseñas en env: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD.",
            "POST /api/{admin|pm|shop}/login → token HMAC 64 chars → localStorage → header X-{Admin|PM|Shop}-Token.",
            "Token sin expiración. Rotar contraseña invalida cada sesión al instante.",
            "Rotar: cambie variable env → redespliegue → todos los tokens viejos mueren.",
            "Límite: LOGIN_MAX_FAILS=10, LOGIN_LOCKOUT_SECONDS=900 (bloqueo IP 15 min).",
            "CORS: solo mascidocs.com + origen www. Preview vía CORS_ORIGIN_REGEX.",
            "Alguien se va → rote contraseña de su nivel. Informe fuera de banda (Signal/teléfono). NO correo.",
        ],
        "tips": ["Admin leaked? Rotate immediately. Audit activity_log last 72hrs.", "ADMIN_HMAC_SECRET leak = rotate that too → every admin session dies system-wide."],
        "tips_es": ["¿Admin filtrado? Rote inmediatamente. Audite activity_log últimas 72hrs.", "¿ADMIN_HMAC_SECRET filtrado? Rótelo → cada sesión admin muere en todo el sistema."],
        "cheatSheet": ["Passwords = env vars. Rotate = redeploy = all old tokens invalidated.", "Rate limit: 10 fails → 15-min IP lockout.", "When someone leaves → rotate their tier's password."],
        "cheatSheet_es": ["Contraseñas = variables env. Rotar = redesplegar = todos los tokens invalidados.", "Límite: 10 fallos → bloqueo IP 15 min.", "Alguien se va → rote contraseña de su nivel."],
    },
    {
        "slug": "admin-08-email-routing",
        "order": 8,
        "title": "Lesson 8 — Email Routing Console (no-redeploy overrides)",
        "title_es": "Lección 8 — Consola de Email Routing (sin redespliegue)",
        "why": "Six routable email lists used to require env-var change + redeploy. Now you edit them in /admin → Email Routing. Changes live within 60 seconds.",
        "why_es": "Seis listas ruteables antes requerían cambio env + redespliegue. Ahora se editan en /admin → Email Routing. Vivos en 60 segundos.",
        "steps": [
            "Admin Hub → Email Routing panel (between PM Routing Table and Site Posters).",
            "Each row: label, live value, env default, OVERRIDE badge if customized, Default + Save buttons.",
            "Edit any list: comma/semicolon/newline-separate addresses → Save → toast confirms.",
            "Reset: Default button → loads env value → Save to persist (or walk away to discard).",
            "Empty list = silence the route (e.g. set Severe Incident extra-CC to empty for zero extras).",
            "Send test email: type address → Send test → Resend delivers in 3 seconds. Verify before adding to a routing list.",
            "Source pill top-right: 'Defaults (env)' or 'Custom (DB)' (amber).",
            "Audit line: timestamp + who changed it.",
        ],
        "steps_es": [
            "Hub Admin → panel Email Routing (entre PM Routing y Site Posters).",
            "Cada fila: etiqueta, valor vivo, default env, badge OVERRIDE si personalizada, botones Default + Save.",
            "Edite lista: separe direcciones con coma/punto-coma/saltos → Save → toast confirma.",
            "Reset: botón Default → carga valor env → Save persiste (o aléjese para descartar).",
            "Lista vacía = silenciar ruta (ej. Severe Incident extra-CC vacío para cero extras).",
            "Send test email: escriba dirección → Send test → Resend entrega en 3 seg. Verifique antes de agregar.",
            "Badge fuente arriba-derecha: 'Defaults (env)' o 'Custom (DB)' (ámbar).",
            "Línea de auditoría: timestamp + quién cambió.",
        ],
        "tips": ["Save forces immediate cache invalidation — next email uses new list.", "Env vars stay as fallbacks — clear DB override and route reverts to env.", "Test new GC's address BEFORE adding to a routing list."],
        "tips_es": ["Save fuerza invalidación inmediata — siguiente correo usa nueva lista.", "Variables env quedan como respaldo — borrar override DB y ruta vuelve a env.", "Pruebe correo nuevo GC ANTES de agregar a lista."],
        "cheatSheet": ["Admin → Email Routing. 6 lists + 1 single email + Send test.", "Empty list = silence. OVERRIDE badge = customized.", "Effect within 60 seconds. No redeploy needed."],
        "cheatSheet_es": ["Admin → Email Routing. 6 listas + 1 correo + Send test.", "Lista vacía = silenciar. Badge OVERRIDE = personalizada.", "Efecto en 60 seg. Sin redespliegue."],
    },
    {
        "slug": "admin-09-doc-id-search",
        "order": 9,
        "title": "Lesson 9 — Doc ID Global Search Bar",
        "title_es": "Lección 9 — Barra de Búsqueda Global de Doc ID",
        "why": "Every form/report/inspection carries a unique Doc ID. The amber search bar at top of /admin lets you punch any Doc ID and land on the matching record's detail page in one keystroke.",
        "why_es": "Cada formulario lleva un Doc ID único. La barra ámbar arriba de /admin lo lleva al registro coincidente con una pulsación.",
        "steps": [
            "Admin Hub → top → amber-bordered search bar with magnifying-glass icon.",
            "Placeholder shows format: PRE-2026-00042, DR-2026-00007, EQR-2026-00012, JHA-2026-00001…",
            "Type Doc ID (case auto-uppercases) → Enter or tap Find.",
            "Match → routes to detail page with Doc ID badge highlighted.",
            "No match → red 'NO RECORD FOUND FOR \"<id>\"' inline (no toast).",
            "Doc ID searched across all 10 source collections in one round-trip (~50ms).",
        ],
        "steps_es": [
            "Hub Admin → arriba → barra borde ámbar con ícono lupa.",
            "Placeholder muestra formato: PRE-2026-00042, DR-2026-00007, EQR-2026-00012, JHA-2026-00001…",
            "Escriba Doc ID (auto-mayúsculas) → Enter o Find.",
            "Coincidencia → rutea al detalle con badge resaltado.",
            "Sin coincidencia → mensaje rojo 'NO RECORD FOUND' inline (sin toast).",
            "Doc ID busca en 10 colecciones en un round-trip (~50ms).",
        ],
        "tips": ["Case-insensitive but exact-match — 'DR-2026-42' won't match DR-2026-00042 (zero-padding matters).", "Admin token preserved through routing even to /pm/* or /shop/* paths."],
        "tips_es": ["Insensible a mayúsculas pero exacto — 'DR-2026-42' no coincide con DR-2026-00042 (padding cero importa).", "Token admin se preserva al rutear a paths /pm/* o /shop/*."],
        "cheatSheet": ["Top of /admin. Type Doc ID → Enter → land on record.", "10 collections in one round-trip.", "Case-insensitive but exact-match."],
        "cheatSheet_es": ["Arriba de /admin. Escriba Doc ID → Enter → registro.", "10 colecciones en un round-trip.", "Insensible a mayúsculas pero exacto."],
    },
    {
        "slug": "admin-10-job-photos-perf",
        "order": 10,
        "title": "Lesson 10 — Job Photos performance (HEIC, warm-cache, Re-index)",
        "title_es": "Lección 10 — Rendimiento Job Photos (HEIC, warm-cache, Re-index)",
        "why": "iPhone HEIC photos are decoded server-side, thumbnails cached in MongoDB for 7 days, and new submissions auto-warmed in background. Two admin emergency buttons exist when needed.",
        "why_es": "Fotos HEIC del iPhone se decodifican server-side, miniaturas caché en MongoDB 7 días, envíos nuevos se calientan en background. Dos botones de emergencia para admin.",
        "steps": [
            "Pipeline: photo → indexer mirrors to job_photos → frontend requests /thumb-signed?t=<token> → backend checks cache → if miss, decodes (Pillow + pillow-heif) → encodes WebP/AVIF/JPEG in one pass → stores all 3 → serves right format per Accept header.",
            "Render concurrency capped at 2 in-flight Pillow decodes (env: JOB_PHOTO_RENDER_CONCURRENCY). Bounds memory; 30-photo gallery doesn't OOM. Cache hits skip the lock.",
            "Frontend cap: 6 thumb requests in flight, gated by IntersectionObserver (300px rootMargin).",
            "Auto-warm scheduler: every 10 min, background loop pre-renders any photo missing JPEG cache. Up to 200 photos/tick. New Daily Report's photos warm within 10 min.",
            "Re-index button (top-right of /admin/photos): wipes index + cache, rebuilds from source. Use after deploy or when a known photo isn't appearing.",
            "Manual warm-cache: POST /api/job-photos/admin/warm-cache (admin token) → pre-renders every photo. Returns {warmed, skipped, failed, elapsed_seconds}.",
            "Cache TTL 7 days. Cold photos drop out automatically; re-rendered on next request.",
        ],
        "steps_es": [
            "Pipeline: foto → indexer → job_photos → frontend pide /thumb-signed → backend revisa caché → si miss, decodifica (Pillow + pillow-heif) → encodea WebP/AVIF/JPEG en una pasada → guarda los 3 → sirve formato según Accept.",
            "Concurrencia render topada en 2 (env: JOB_PHOTO_RENDER_CONCURRENCY). Acota memoria; 30 fotos no le hace OOM. Hits de caché saltan el lock.",
            "Tope frontend: 6 peticiones en vuelo, gateadas por IntersectionObserver (300px rootMargin).",
            "Scheduler auto-warm: cada 10 min, loop background pre-renderiza fotos sin caché JPEG. Hasta 200/tick. Reportes Diarios nuevos calientan en 10 min.",
            "Botón Re-index (arriba-derecha de /admin/photos): limpia índice + caché, reconstruye. Use después de despliegue o cuando una foto conocida no aparece.",
            "Warm-cache manual: POST /api/job-photos/admin/warm-cache → pre-renderiza todo. Devuelve {warmed, skipped, failed, elapsed_seconds}.",
            "TTL caché 7 días. Fotos frías caen automático; re-renderizadas en siguiente petición.",
        ],
        "tips": ["After every prod deploy: /admin → Job Photos → Re-index. Wipes pre-pillow-heif broken iPhone photos.", "Broken thumbs? Network tab → /thumb-signed status. 5xx=worker. 404=source missing. 200<1KB=corrupt cache → Re-index.", "Cloudflare 520 storms = worker OOM-killed. Check JOB_PHOTO_RENDER_CONCURRENCY (default 2) + container memory."],
        "tips_es": ["Después de cada despliegue: /admin → Job Photos → Re-index. Limpia HEIC roto pre-pillow-heif.", "¿Miniaturas rotas? Network tab → estado /thumb-signed. 5xx=worker. 404=fuente faltante. 200<1KB=caché corrupto → Re-index.", "Tormentas Cloudflare 520 = worker OOM. Revise JOB_PHOTO_RENDER_CONCURRENCY (default 2) + memoria contenedor."],
        "cheatSheet": ["Auto-warm every 10 min. Cache TTL 7 days. HEIC supported.", "After deploy → click Re-index once. Done.", "Render concurrency 2 (semaphore). Frontend 6 in-flight tiles."],
        "cheatSheet_es": ["Auto-warm cada 10 min. TTL caché 7 días. HEIC soportado.", "Después de despliegue → Re-index una vez. Listo.", "Concurrencia 2 (semáforo). Frontend 6 mosaicos en vuelo."],
    },
]


LESSONS = FIELD_LESSONS + SHOP_LESSONS + PM_LESSONS + ADMIN_LESSONS


def _lessons_for(track: str) -> list:
    prefix = track + "-"
    return [l for l in LESSONS if l["slug"].startswith(prefix)]


# ----------------------------------------------------------------------------
# Renderer
# ----------------------------------------------------------------------------

_STRINGS = {
    "en": {
        "header_brand": "MASCI Hub Training",
        "packet": "Training Packet",
        "cover_subtitle": "Step-by-step walk-throughs, printable cheat sheets, and\u00a0reference\u00a0guides for every role.",
        "toc": "Contents",
        "lesson": "Lesson",
        "why": "Why this matters",
        "steps": "Step-by-step",
        "tips": "Tips",
        "cheat": "Cheat sheet",
        "prepared": "Prepared for MASCI Safety &\u00a0Operations",
        "generated": "Generated",
        "page": "Page",
        "of": "of",
        "footer_legal": "Generated through MASCI HUB \u2014 Powered by ForgedOps LLC | \u00a9 2026 ForgedOps LLC",
        "ownership_note": "mascidocs.com is a customer-branded deployment of an enterprise operational platform owned and operated by ForgedOps LLC.",
        "disclaimer": "This platform and training material are provided as a documentation and support tool only and do not replace required safety supervision, inspections, or regulatory compliance responsibilities.",
    },
    "es": {
        "header_brand": "Capacitación Hub MASCI",
        "packet": "Paquete de Capacitación",
        "cover_subtitle": "Guías paso a paso, hojas imprimibles y referencias para cada rol.",
        "toc": "Contenido",
        "lesson": "Lección",
        "why": "Por qué importa",
        "steps": "Paso a paso",
        "tips": "Consejos",
        "cheat": "Hoja de referencia",
        "prepared": "Preparado para MASCI Seguridad &\u00a0Operaciones",
        "generated": "Generado",
        "page": "Página",
        "of": "de",
        "footer_legal": "Generado a trav\u00e9s de MASCI HUB \u2014 Desarrollado por ForgedOps LLC | \u00a9 2026 ForgedOps LLC",
        "ownership_note": "mascidocs.com es una implementaci\u00f3n con marca del cliente de una plataforma operativa empresarial propiedad de y operada por ForgedOps LLC.",
        "disclaimer": "Esta plataforma y el material de capacitaci\u00f3n se proporcionan \u00fanicamente como herramienta de documentaci\u00f3n y apoyo, y no reemplazan la supervisi\u00f3n de seguridad, inspecciones o responsabilidades de cumplimiento regulatorio requeridas.",
    },
}


def _pick(obj: dict, key: str, lang: str):
    if lang == "es":
        v = obj.get(f"{key}_es")
        if v is not None:
            return v
    return obj.get(key)


def _normalize_lang(raw: str) -> str:
    """Return one of 'en', 'es', 'bi'."""
    s = str(raw or "").strip().lower()
    # "bilingual", "es-en", "en-es", "both"
    if s in {"bi", "bilingual", "both", "es-en", "en-es", "dual", "en+es"}:
        return "bi"
    if s.startswith("es"):
        return "es"
    return "en"


_CSS_TEMPLATE = """
@page {
  size: Letter;
  margin: 0.55in 0.55in 0.7in 0.55in;
  @bottom-left {
    content: "{FOOTER_TEXT}";
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 8pt;
    color: #64748B;
  }
  @bottom-right {
    content: counter(page) "  /  " counter(pages);
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 8pt;
    color: #64748B;
  }
}
@page :first {
  margin: 0.9in 0.6in 0.9in 0.6in;
  @bottom-left   { content: ""; }
  @bottom-right  { content: ""; }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; color: #0F172A; }
body { font-size: 10.5pt; line-height: 1.45; }

.stripe { height: 10px; background: repeating-linear-gradient(45deg, #B91C1C 0 14px, #FACC15 14px 28px); margin-bottom: 16pt; }

.cover { page-break-after: always; }
.cover .eyebrow { font-family: 'Courier New', monospace; font-size: 8.5pt; letter-spacing: 3pt; color: #B91C1C; text-transform: uppercase; font-weight: 800; }
.cover h1 { font-size: 42pt; font-weight: 900; letter-spacing: -0.5pt; line-height: 1.02; margin: 10pt 0 6pt 0; color: #0F172A; }
.cover h1 .accent { color: var(--accent); }
.cover .blurb { font-size: 13pt; color: #334155; max-width: 520pt; margin-top: 6pt; }
.cover .grid { display: flex; gap: 18pt; margin-top: 28pt; }
.cover .stat { background: #F1F5F9; border-left: 3pt solid var(--accent); padding: 12pt 14pt; min-width: 120pt; }
.cover .stat .n { font-size: 22pt; font-weight: 900; color: #0F172A; }
.cover .stat .l { font-size: 8pt; letter-spacing: 2pt; color: #64748B; text-transform: uppercase; }
.cover .meta { margin-top: 60pt; font-size: 9pt; color: #64748B; letter-spacing: 1pt; }

.toc { page-break-after: always; }
.toc h2 { font-size: 20pt; font-weight: 900; border-bottom: 2pt solid var(--accent); padding-bottom: 6pt; margin: 0 0 14pt 0; }
.toc ol { list-style: none; padding: 0; margin: 0; counter-reset: lessonNum; }
.toc li { counter-increment: lessonNum; display: flex; gap: 10pt; padding: 7pt 0; border-bottom: 1px dotted #E2E8F0; font-size: 11pt; }
.toc li::before { content: counter(lessonNum, decimal-leading-zero); color: var(--accent); font-weight: 800; min-width: 28pt; }

.lesson { page-break-before: always; }
.lesson .eyebrow { font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 2.5pt; color: var(--accent); text-transform: uppercase; font-weight: 800; }
.lesson h2 { font-size: 22pt; font-weight: 900; margin: 4pt 0 14pt 0; line-height: 1.12; }
.lesson .why { border-left: 3pt solid #B91C1C; background: #FEF2F2; padding: 10pt 12pt; margin: 0 0 14pt 0; }
.lesson .why .l { font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 2pt; color: #B91C1C; font-weight: 800; text-transform: uppercase; margin-bottom: 3pt; }
.lesson .why .b { font-size: 10.5pt; color: #0F172A; }

.lesson h3 { font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 2.5pt; color: #64748B; font-weight: 800; text-transform: uppercase; margin: 14pt 0 6pt 0; }

.lesson ol.steps { list-style: none; padding: 0; margin: 0; counter-reset: s; }
.lesson ol.steps > li { counter-increment: s; display: flex; gap: 9pt; padding: 4pt 0; }
.lesson ol.steps > li::before { content: counter(s); display: inline-block; min-width: 17pt; height: 17pt; border-radius: 17pt; background: #0F172A; color: #FFF; font-weight: 800; font-size: 9pt; text-align: center; line-height: 17pt; font-family: 'Courier New', monospace; flex-shrink: 0; }
.lesson ul.tips { list-style: none; padding: 0; margin: 0; }
.lesson ul.tips > li { padding: 3pt 0 3pt 14pt; position: relative; font-size: 10pt; color: #334155; }
.lesson ul.tips > li::before { content: "\\2713"; position: absolute; left: 0; color: #047857; font-weight: 800; }

.lesson .cheat { margin-top: 14pt; background: #0F172A; color: #F8FAFC; padding: 12pt 14pt; border-radius: 3pt; }
.lesson .cheat .l { font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 2.5pt; color: #FBBF24; font-weight: 800; text-transform: uppercase; margin-bottom: 5pt; }
.lesson .cheat ul { list-style: none; padding: 0; margin: 0; }
.lesson .cheat li { padding: 2.5pt 0; font-size: 10pt; }
.lesson .cheat li::before { content: "\\2714 "; color: #FBBF24; font-weight: 900; margin-right: 5pt; }

.endnote { page-break-before: always; padding-top: 40pt; font-size: 9pt; color: #64748B; text-align: center; }
.endnote .big { font-size: 14pt; color: #0F172A; font-weight: 700; margin-bottom: 8pt; }

/* -------- Bilingual (side-by-side) layout -------- */
/* Uses CSS tables instead of flexbox/grid so WeasyPrint paginates the
   rows correctly when a lesson spans multiple pages. */
.bi-row { display: table; width: 100%; border-collapse: collapse; margin: 0; }
.bi-row > .bi-cell { display: table-cell; width: 50%; vertical-align: top; padding: 0; }
.bi-row > .bi-cell.en { padding-right: 10pt; border-right: 1pt solid #E2E8F0; }
.bi-row > .bi-cell.es { padding-left: 10pt; }
.bi-row .bi-cell-inner { padding: 0; }

.bi-langhdr { display: table; width: 100%; margin: 0 0 6pt 0; }
.bi-langhdr > div { display: table-cell; width: 50%; padding: 4pt 8pt; font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 2pt; text-transform: uppercase; font-weight: 800; color: #FFF; }
.bi-langhdr .h-en { background: #0F172A; border-right: 2pt solid #FFF; }
.bi-langhdr .h-es { background: var(--accent); }

.bi-step { display: table; width: 100%; margin: 5pt 0; border-bottom: 1px dotted #E2E8F0; padding-bottom: 5pt; }
.bi-step > .num { display: table-cell; width: 22pt; vertical-align: top; padding-top: 1pt; }
.bi-step > .num span { display: inline-block; width: 16pt; height: 16pt; border-radius: 16pt; background: #0F172A; color: #FFF; font-weight: 800; font-size: 8.5pt; text-align: center; line-height: 16pt; font-family: 'Courier New', monospace; }
.bi-step > .en, .bi-step > .es { display: table-cell; vertical-align: top; font-size: 9.5pt; line-height: 1.4; }
.bi-step > .en { padding-right: 10pt; border-right: 1pt solid #E2E8F0; padding-left: 0; }
.bi-step > .es { padding-left: 10pt; color: #334155; }

.bi-tipline, .bi-cheatline { display: table; width: 100%; margin: 3pt 0; }
.bi-tipline > div, .bi-cheatline > div { display: table-cell; width: 50%; vertical-align: top; padding: 2pt 10pt; font-size: 9.5pt; line-height: 1.4; }
.bi-tipline > .en { padding-left: 14pt; position: relative; border-right: 1pt solid #E2E8F0; }
.bi-tipline > .en::before, .bi-tipline > .es::before { content: "\\2713"; color: #047857; font-weight: 800; position: absolute; left: 0; margin-left: 0; }
.bi-tipline > .es { padding-left: 24pt; position: relative; color: #334155; }
.bi-tipline > .es::before { left: 10pt; }

.bi-cheatbox { background: #0F172A; color: #F8FAFC; padding: 10pt 0; border-radius: 3pt; margin-top: 12pt; }
.bi-cheatbox .l { display: table; width: 100%; margin-bottom: 4pt; }
.bi-cheatbox .l div { display: table-cell; width: 50%; padding: 0 14pt; font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 2.5pt; font-weight: 800; text-transform: uppercase; color: #FBBF24; }
.bi-cheatbox .bi-cheatline > div { color: #F8FAFC; padding: 2pt 14pt; font-size: 9.5pt; }
.bi-cheatbox .bi-cheatline > div::before { content: "\\2714 "; color: #FBBF24; font-weight: 900; margin-right: 5pt; }
.bi-cheatbox .bi-cheatline > .en { border-right: 1pt solid #334155; }
"""


def _css_for_lang(lang: str) -> str:
    """Render the packet CSS with a language-appropriate footer string
    in the @page @bottom-left margin box. The footer text MUST match
    the `footer_legal` string in the i18n table (see `_strings_for`)
    so every page of the packet shows the same language as the body.
    """
    footer_en = "Generated through MASCI HUB \u2014 Powered by ForgedOps LLC | \\00A9  2026 ForgedOps LLC"
    footer_es = "Generado a trav\u00e9s de MASCI HUB \u2014 Desarrollado por ForgedOps LLC | \\00A9  2026 ForgedOps LLC"
    footer = footer_es if lang == "es" else footer_en
    return _CSS_TEMPLATE.replace("{FOOTER_TEXT}", footer)


# ----------------------------------------------------------------------------
# Bilingual renderer
# ----------------------------------------------------------------------------


def _render_bilingual(track: str, meta: dict, lessons: list) -> bytes:
    """Side-by-side EN / ES packet — English on the left, Spanish on the right.
    Shares the base CSS and cover/TOC/endnote styling with the single-language
    renderer but replaces each lesson body with a 2-column layout so readers
    can map English technical terms to their Spanish equivalents at a glance."""
    accent = meta["accent"]
    logo = _logo_uri()
    now_en = datetime.now(timezone.utc).strftime("%b %d, %Y")
    now_es = datetime.now(timezone.utc).strftime("%d de %b, %Y")

    parts = []
    # Bilingual packet uses the English footer by default — body already
    # covers both languages side-by-side.
    parts.append(f"<style>{_css_for_lang('en')}</style>")
    parts.append(f"<div style='--accent: {accent};'>")

    # Cover
    parts.append("<section class='cover'>")
    parts.append("<div class='stripe'></div>")
    if logo:
        parts.append(f"<img src='{logo}' style='height:40pt; margin-bottom:22pt;' alt='MASCI'/>")
    parts.append("<div class='eyebrow'>MASCI Hub Training \u00b7 Bilingual Packet / Paquete Bilingüe</div>")
    parts.append(f"<h1>{escape(meta['title'])}<br/><span style='color:{accent};font-size:28pt'>{escape(meta['title_es'])}</span></h1>")
    parts.append("<div class='blurb'>")
    parts.append(f"<strong>EN:</strong> {escape(meta['blurb'])}<br/>")
    parts.append(f"<strong>ES:</strong> {escape(meta['blurb_es'])}")
    parts.append("</div>")
    parts.append("<div class='grid'>")
    parts.append(f"<div class='stat'><div class='n'>{len(lessons)}</div><div class='l'>Lessons / Lecciones</div></div>")
    parts.append("<div class='stat'><div class='n'>EN+ES</div><div class='l'>Side-by-side / Lado a lado</div></div>")
    parts.append("</div>")
    parts.append(f"<div class='meta'>Prepared for MASCI Safety &amp; Operations \u00b7 Preparado para MASCI \u00b7 Generated / Generado: {now_en} ({now_es})</div>")
    parts.append("</section>")

    # TOC — bilingual side-by-side
    parts.append("<section class='toc'>")
    parts.append("<h2>Contents / Contenido</h2>")
    parts.append("<ol>")
    for lesson in lessons:
        parts.append(
            "<li><div style='display:table;width:100%'>"
            f"<div style='display:table-cell;width:50%;padding-right:10pt'>{escape(lesson['title'])}</div>"
            f"<div style='display:table-cell;width:50%;padding-left:10pt;color:{accent}'>{escape(lesson['title_es'])}</div>"
            "</div></li>"
        )
    parts.append("</ol>")
    parts.append("</section>")

    # Lessons
    for lesson in lessons:
        parts.append("<section class='lesson'>")
        parts.append(
            f"<div class='eyebrow'>{escape(meta['title'])} \u00b7 Lesson {lesson['order']} / Lección {lesson['order']}</div>"
        )
        parts.append(
            f"<h2>{escape(lesson['title'])}<br/>"
            f"<span style='font-size:14pt;color:{accent};font-weight:700'>{escape(lesson['title_es'])}</span></h2>"
        )

        # Language headers
        parts.append(
            "<div class='bi-langhdr'>"
            "<div class='h-en'>English</div>"
            "<div class='h-es'>Español</div>"
            "</div>"
        )

        # Why — two boxes side-by-side
        parts.append("<h3>Why this matters / Por qué importa</h3>")
        parts.append(
            "<div class='bi-row'>"
            f"<div class='bi-cell en'><div style='border-left:3pt solid #B91C1C;background:#FEF2F2;padding:8pt 10pt;font-size:10pt'>{escape(lesson['why'])}</div></div>"
            f"<div class='bi-cell es'><div style='border-left:3pt solid {accent};background:#F8FAFC;padding:8pt 10pt;font-size:10pt'>{escape(lesson['why_es'])}</div></div>"
            "</div>"
        )

        # Steps — pair EN[i] with ES[i]
        steps_en = lesson.get("steps") or []
        steps_es = lesson.get("steps_es") or []
        max_steps = max(len(steps_en), len(steps_es))
        if max_steps:
            parts.append("<h3>Step-by-step / Paso a paso</h3>")
            for i in range(max_steps):
                en_txt = steps_en[i] if i < len(steps_en) else ""
                es_txt = steps_es[i] if i < len(steps_es) else ""
                parts.append(
                    f"<div class='bi-step'>"
                    f"<div class='num'><span>{i + 1}</span></div>"
                    f"<div class='en'>{escape(en_txt)}</div>"
                    f"<div class='es'>{escape(es_txt)}</div>"
                    f"</div>"
                )

        # Tips — pair EN[i] with ES[i]
        tips_en = lesson.get("tips") or []
        tips_es = lesson.get("tips_es") or []
        max_tips = max(len(tips_en), len(tips_es))
        if max_tips:
            parts.append("<h3>Tips / Consejos</h3>")
            for i in range(max_tips):
                en_txt = tips_en[i] if i < len(tips_en) else ""
                es_txt = tips_es[i] if i < len(tips_es) else ""
                parts.append(
                    f"<div class='bi-tipline'>"
                    f"<div class='en'>{escape(en_txt)}</div>"
                    f"<div class='es'>{escape(es_txt)}</div>"
                    f"</div>"
                )

        # Cheat sheet — dark box, two columns
        cheat_en = lesson.get("cheatSheet") or []
        cheat_es = lesson.get("cheatSheet_es") or []
        max_cheat = max(len(cheat_en), len(cheat_es))
        if max_cheat:
            parts.append("<div class='bi-cheatbox'>")
            parts.append("<div class='l'><div>Cheat Sheet</div><div>Hoja de Referencia</div></div>")
            for i in range(max_cheat):
                en_txt = cheat_en[i] if i < len(cheat_en) else ""
                es_txt = cheat_es[i] if i < len(cheat_es) else ""
                parts.append(
                    f"<div class='bi-cheatline'>"
                    f"<div class='en'>{escape(en_txt)}</div>"
                    f"<div class='es'>{escape(es_txt)}</div>"
                    f"</div>"
                )
            parts.append("</div>")

        parts.append("</section>")

    # End note — final page ownership clarification + platform attribution.
    # NOTE: The footer text is ALREADY on every page via the @page
    # @bottom-left margin box — do NOT repeat it in the endnote body.
    parts.append("<section class='endnote'>")
    parts.append("<div class='big'>mascidocs.com</div>")
    parts.append(
        "<div style='margin-top:10pt;font-size:9pt;color:#64748B;'>"
        "mascidocs.com is a customer-branded deployment of a platform developed by "
        "ForgedOps LLC."
        "</div>"
        "<div style='margin-top:10pt;font-size:8.5pt;color:#94A3B8;font-style:italic;max-width:5in;margin-left:auto;margin-right:auto;'>"
        "This platform and training material are provided as a documentation and "
        "support tool only and do not replace required safety supervision, "
        "inspections, or regulatory compliance responsibilities."
        "</div>"
    )
    parts.append("</section>")

    parts.append("</div>")
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body>" + "".join(parts) + "</body></html>"
    return HTML(string=html).write_pdf()


def render_packet(track: str, lang: str = "en") -> bytes:
    """Render the training packet for `track` in `lang` ('en', 'es', or
    'bi' / 'bilingual' / 'es-en')."""
    track = track.lower()
    lang = _normalize_lang(lang)
    meta = TRACKS.get(track)
    if not meta:
        raise ValueError(f"Unknown track: {track}")
    lessons = _lessons_for(track)

    if lang == "bi":
        return _render_bilingual(track, meta, lessons)

    t = _STRINGS[lang]
    accent = meta["accent"]
    title = _pick(meta, "title", lang)
    blurb = _pick(meta, "blurb", lang)
    logo = _logo_uri()
    now = datetime.now(timezone.utc).strftime("%b %d, %Y") if lang == "en" else datetime.now(timezone.utc).strftime("%d de %b, %Y")

    parts = []
    parts.append(f"<style>{_css_for_lang(lang)}</style>")
    parts.append(f"<div style='--accent: {accent};'>")

    # Cover
    parts.append("<section class='cover'>")
    parts.append("<div class='stripe'></div>")
    if logo:
        parts.append(f"<img src='{logo}' style='height:40pt; margin-bottom:22pt;' alt='MASCI'/>")
    parts.append(f"<div class='eyebrow'>{escape(t['header_brand'])} \u00b7 {escape(t['packet'])}</div>")
    parts.append(f"<h1>{escape(title)}</h1>")
    parts.append(f"<div class='blurb'>{escape(blurb)}</div>")
    parts.append("<div class='grid'>")
    parts.append(f"<div class='stat'><div class='n'>{len(lessons)}</div><div class='l'>{escape(t['lesson'])}S</div></div>")
    parts.append(f"<div class='stat'><div class='n'>{lang.upper()}</div><div class='l'>Idioma / Language</div></div>")
    parts.append("</div>")
    parts.append(f"<div class='meta'>{escape(t['prepared'])} \u00b7 {escape(t['generated'])}: {now}</div>")
    parts.append("</section>")

    # TOC
    parts.append("<section class='toc'>")
    parts.append(f"<h2>{escape(t['toc'])}</h2>")
    parts.append("<ol>")
    for l in lessons:
        parts.append(f"<li>{escape(_pick(l, 'title', lang))}</li>")
    parts.append("</ol>")
    parts.append("</section>")

    # Lessons
    for l in lessons:
        parts.append("<section class='lesson'>")
        parts.append(f"<div class='eyebrow'>{escape(title)} \u00b7 {escape(t['lesson'])} {l['order']}</div>")
        parts.append(f"<h2>{escape(_pick(l, 'title', lang))}</h2>")
        parts.append("<div class='why'>")
        parts.append(f"<div class='l'>{escape(t['why'])}</div>")
        parts.append(f"<div class='b'>{escape(_pick(l, 'why', lang))}</div>")
        parts.append("</div>")
        steps = _pick(l, "steps", lang) or []
        if steps:
            parts.append(f"<h3>{escape(t['steps'])}</h3>")
            parts.append("<ol class='steps'>")
            for s in steps:
                parts.append(f"<li><span>{escape(s)}</span></li>")
            parts.append("</ol>")
        tips = _pick(l, "tips", lang) or []
        if tips:
            parts.append(f"<h3>{escape(t['tips'])}</h3>")
            parts.append("<ul class='tips'>")
            for tip in tips:
                parts.append(f"<li>{escape(tip)}</li>")
            parts.append("</ul>")
        cheat = _pick(l, "cheatSheet", lang) or []
        if cheat:
            parts.append("<div class='cheat'>")
            parts.append(f"<div class='l'>{escape(t['cheat'])}</div>")
            parts.append("<ul>")
            for c in cheat:
                parts.append(f"<li>{escape(c)}</li>")
            parts.append("</ul>")
            parts.append("</div>")
        parts.append("</section>")

    # End note — final page ownership clarification + safety disclaimer.
    # NOTE: The footer text `t['footer_legal']` is ALREADY rendered on
    # every page (including this one) by the @page @bottom-left margin
    # box — do NOT repeat it here or it prints twice on the last page.
    parts.append("<section class='endnote'>")
    parts.append("<div class='big'>mascidocs.com</div>")
    parts.append(
        f"<div style='margin-top:10pt;font-size:9pt;color:#64748B;'>"
        f"{escape(t['ownership_note'])}"
        f"</div>"
        f"<div style='margin-top:10pt;font-size:8.5pt;color:#94A3B8;font-style:italic;max-width:5in;margin-left:auto;margin-right:auto;'>"
        f"{escape(t['disclaimer'])}"
        f"</div>"
    )
    parts.append("</section>")

    parts.append("</div>")
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body>" + "".join(parts) + "</body></html>"
    return HTML(string=html).write_pdf()
