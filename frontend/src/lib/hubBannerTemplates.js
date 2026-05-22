/**
 * HUB_BANNER_TEMPLATES — preloaded message templates the admin can
 * pick from when composing a banner.
 *
 * iter328 · Banner Governance V2:
 *   • Operational copy refined to calm, mature, field-experienced tone.
 *     No exclamation marks. No alarmism. Direct verbs, short sentences.
 *   • New severity tier: `cultural` — slate-grounded calm chrome, used
 *     ONLY for holiday / remembrance / civic-culture banners. Cultural
 *     banners sort BELOW every operational severity (see SEVERITY_META
 *     priority) so they can never visually compete with hurricanes,
 *     heat emergencies, or active danger.
 *   • Each template ships with English + Spanish copy at the source.
 *     The frontend renders BOTH simultaneously (bilingual broadcast)
 *     so morning-briefing messaging reaches the entire workforce.
 *   • Adding a template?
 *       - Pick a stable `id` (snake_case).
 *       - Provide title_en / title_es and body_en / body_es.
 *       - Severity must be one of:
 *           cultural | info | advisory | warning | critical.
 *       - `default_expires_hours` prefills expires_at on compose.
 *
 * Order in this list = order the picker renders them.
 */
export const HUB_BANNER_TEMPLATES = [
  // ─── Operational safety advisories ────────────────────────────────

  {
    id: "heat_advisory",
    label: "Heat Advisory",
    icon: "thermometer-sun",
    severity: "advisory",
    require_ack: false,
    default_expires_hours: 10,
    title_en: "Heat Advisory in Effect",
    title_es: "Aviso de Calor en Vigor",
    body_en:
      "Temperatures will exceed 95°F today. Take a 10-minute shaded break every hour. Drink water every 15 minutes. Watch your crew for cramps, dizziness, or confusion — stop work and call your foreman if anyone shows symptoms.",
    body_es:
      "Las temperaturas superarán los 95°F hoy. Tome un descanso de 10 minutos en la sombra cada hora. Beba agua cada 15 minutos. Observe a su cuadrilla por calambres, mareos o confusión — detenga el trabajo y llame a su capataz si alguien presenta síntomas.",
  },
  {
    id: "heat_warning",
    label: "Excessive Heat Warning",
    icon: "thermometer-sun",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 10,
    title_en: "Excessive Heat Warning — Mandatory Cooling Cycle",
    title_es: "Advertencia de Calor Excesivo — Ciclo de Enfriamiento Obligatorio",
    body_en:
      "Heat index will exceed 108°F. OSHA-mandatory 15-minute shaded break every 45 minutes of work. Buddy-check your crew every 30 minutes. Any sign of heat illness — stop work and call 911. No outdoor work between 12 PM and 3 PM.",
    body_es:
      "El índice de calor superará los 108°F. Descanso obligatorio OSHA de 15 minutos en la sombra cada 45 minutos de trabajo. Revise a su compañero cada 30 minutos. Cualquier señal de enfermedad por calor — detenga el trabajo y llame al 911. Sin trabajo al aire libre entre 12 PM y 3 PM.",
  },
  {
    id: "hurricane_watch",
    label: "Hurricane Watch (48–72h)",
    icon: "cloud-rain-wind",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 48,
    title_en: "Hurricane Watch Issued",
    title_es: "Vigilancia de Huracán Emitida",
    body_en:
      "A hurricane is possible in our area within 48–72 hours. Foremen begin securing loose tools, signage, and fuel. PMs confirm everyone has reviewed the Storm Plan. Monitor updates — Warning status is next. No new excavations until the storm passes.",
    body_es:
      "Es posible un huracán en nuestra área dentro de 48–72 horas. Capataces comienzan a asegurar herramientas, señalización y combustible. PMs confirman que todos han revisado el Plan de Tormenta. Vigile las actualizaciones — el siguiente estado es Advertencia. Sin nuevas excavaciones hasta que pase la tormenta.",
  },
  {
    id: "hurricane_warning",
    label: "Hurricane Warning (within 36h)",
    icon: "cloud-rain-wind",
    severity: "critical",
    require_ack: true,
    default_expires_hours: 36,
    title_en: "Hurricane Warning — Stand Down",
    title_es: "Advertencia de Huracán — Cese de Operaciones",
    body_en:
      "A hurricane will impact our area within 36 hours. Stop all field operations by end of shift. Secure every site: tools, trench boxes, MOT signage, fuel, and generators. All crews report storm prep complete to your PM before leaving. The office will email when it is safe to return.",
    body_es:
      "Un huracán impactará nuestra área dentro de 36 horas. Detenga todas las operaciones de campo al final del turno. Asegure cada sitio: herramientas, cajas de trinchera, señalización MOT, combustible y generadores. Toda cuadrilla reporta preparación de tormenta completa a su PM antes de salir. La oficina enviará correo cuando sea seguro regresar.",
  },
  {
    id: "lightning",
    label: "Severe Thunderstorm / Lightning",
    icon: "cloud-lightning",
    severity: "warning",
    require_ack: false,
    default_expires_hours: 4,
    title_en: "Lightning in Area — Pause Work",
    title_es: "Rayos en el Área — Pause el Trabajo",
    body_en:
      "Lightning has been detected within 10 miles. Apply the 30-minute rule: wait 30 minutes after the last strike before returning to open work. Get crews off lifts, off rebar, out of trenches, and into vehicles or hard-roofed structures.",
    body_es:
      "Se han detectado rayos dentro de 10 millas. Aplique la regla de los 30 minutos: espere 30 minutos después del último rayo antes de regresar al trabajo abierto. Saque a las cuadrillas de elevadores, refuerzo, trincheras, y llévelos a vehículos o estructuras con techo sólido.",
  },
  {
    id: "flood_watch",
    label: "Flood Watch",
    icon: "waves",
    severity: "advisory",
    require_ack: false,
    default_expires_hours: 24,
    title_en: "Flood Watch in Effect",
    title_es: "Vigilancia de Inundación en Vigor",
    body_en:
      "Heavy rain is expected. Check trench-box drainage and pump readiness before the rain starts. Do not enter any trench with standing water until inspected by the Competent Person. Report site flooding to your PM immediately.",
    body_es:
      "Se espera lluvia fuerte. Revise el drenaje de las cajas de trinchera y la disponibilidad de bombas antes de que comience la lluvia. No entre a ninguna trinchera con agua estancada hasta que sea inspeccionada por la Persona Competente. Reporte inundaciones al PM de inmediato.",
  },
  {
    id: "air_quality",
    label: "Air Quality / Smoke Advisory",
    icon: "wind",
    severity: "advisory",
    require_ack: false,
    default_expires_hours: 12,
    title_en: "Air Quality Advisory — Reduce Exposure",
    title_es: "Aviso de Calidad de Aire — Reduzca la Exposición",
    body_en:
      "Particulate levels are elevated. Workers with asthma or respiratory conditions report to your foreman before starting. Shorten time on heavy exertion tasks. N95 or better is required for any cutting, grinding, or sweeping today.",
    body_es:
      "Los niveles de partículas están elevados. Trabajadores con asma o condiciones respiratorias repórtense con su capataz antes de comenzar. Acorte el tiempo en tareas de esfuerzo intenso. Se requiere N95 o mejor para cualquier corte, esmerilado, o barrido hoy.",
  },
  {
    id: "faa_fod",
    label: "FAA / FOD Alert",
    icon: "plane",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 12,
    title_en: "FAA / FOD Alert — Airfield Discipline",
    title_es: "Alerta FAA / FOD — Disciplina de Aeródromo",
    body_en:
      "Active FOD risk on the airfield. Walk every work zone before crew arrival. Pocket every loose item — tape, fasteners, cuttings, water bottles. Any equipment leaving the airside undergoes a FOD walk before exit. Report any incident to ATC and your PM immediately.",
    body_es:
      "Riesgo activo de FOD en el aeródromo. Camine cada zona de trabajo antes de la llegada de la cuadrilla. Guarde en bolsillos cada objeto suelto — cinta, sujetadores, recortes, botellas de agua. Todo equipo que sale del lado aéreo pasa por una caminata FOD antes de salir. Reporte cualquier incidente a ATC y a su PM de inmediato.",
  },
  {
    id: "osha_visit",
    label: "OSHA Site Visit Today",
    icon: "shield-check",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 12,
    title_en: "OSHA Compliance Officer On Site Today",
    title_es: "Oficial de Cumplimiento OSHA en el Sitio Hoy",
    body_en:
      "An OSHA Compliance Officer is visiting MASCI job sites today. Full PPE — hard hat, hi-vis, safety glasses, gloves, and boots. All daily reports, JHAs, and Competent Person logs current and on site. Direct any officer to your PM before answering questions. Be polite, be brief.",
    body_es:
      "Un Oficial de Cumplimiento OSHA visitará las obras MASCI hoy. PPE completo — casco, alta visibilidad, gafas de seguridad, guantes y botas. Todos los reportes diarios, JHAs, y bitácoras de Persona Competente al día y en sitio. Dirija a cualquier oficial a su PM antes de contestar preguntas. Sea cortés, sea breve.",
  },
  {
    id: "stand_down",
    label: "Major Incident — Stand Down",
    icon: "octagon-alert",
    severity: "critical",
    require_ack: true,
    default_expires_hours: 8,
    title_en: "Safety Stand-Down in Effect",
    title_es: "Cese de Seguridad en Vigor",
    body_en:
      "A serious incident has occurred on a MASCI project. All crews stop work immediately and meet with your foreman for a safety briefing before resuming any task. Foremen call your PM for details. Do not discuss the incident on social media or with anyone outside the company.",
    body_es:
      "Ha ocurrido un incidente grave en un proyecto MASCI. Todas las cuadrillas detienen el trabajo de inmediato y se reúnen con su capataz para una reunión de seguridad antes de reanudar cualquier tarea. Capataces llamen a su PM por detalles. No discutan el incidente en redes sociales ni con nadie fuera de la compañía.",
  },
  {
    id: "illness_reporting",
    label: "Illness Reporting Reminder",
    icon: "thermometer",
    severity: "info",
    require_ack: false,
    default_expires_hours: 168,
    title_en: "Illness Reporting Reminder",
    title_es: "Recordatorio de Reporte de Enfermedad",
    body_en:
      "If you have a fever, cough, or any contagious symptoms, do not report to the job site. Call your foreman or PM to report off. Sick days are protected — your job is not at risk for staying home when you're contagious. Protect your crew.",
    body_es:
      "Si tiene fiebre, tos o cualquier síntoma contagioso, no se presente a la obra. Llame a su capataz o PM para reportarse enfermo. Los días por enfermedad están protegidos — su trabajo no está en riesgo por quedarse en casa cuando es contagioso. Proteja a su cuadrilla.",
  },
  {
    id: "operational_notice",
    label: "Operational Notice",
    icon: "info",
    severity: "info",
    require_ack: false,
    default_expires_hours: 48,
    title_en: "Operational Notice",
    title_es: "Aviso Operativo",
    body_en:
      "Standing operational notice — see your PM or foreman for site-specific direction.",
    body_es:
      "Aviso operativo en vigor — consulte con su PM o capataz para indicaciones específicas del sitio.",
  },
  {
    id: "holiday_closure",
    label: "Company Holiday / Shutdown",
    icon: "calendar-x",
    severity: "info",
    require_ack: false,
    default_expires_hours: 168,
    title_en: "Office Closed for Holiday",
    title_es: "Oficina Cerrada por Día Festivo",
    body_en:
      "The MASCI office will be closed for the holiday. Field crews — check with your foreman for your specific schedule. For emergencies (incidents, equipment failure that stops the job, or any safety concern), call the on-call PM. Otherwise, see you on the next business day.",
    body_es:
      "La oficina MASCI estará cerrada por el día festivo. Cuadrillas de campo — consulten con su capataz por su horario específico. Para emergencias (incidentes, falla de equipo que detiene la obra, o cualquier preocupación de seguridad), llamen al PM de guardia. Si no, nos vemos el siguiente día hábil.",
  },

  // ─── iter328 · Holiday / cultural banners (calm slate chrome) ─────
  //
  // These run as severity: "cultural" — sorted below every operational
  // severity and rendered in calm slate chrome so they NEVER visually
  // compete with active safety alerts. Tone is grounded, respectful,
  // operational — no exclamation marks, no flag emoji, no clichés.

  {
    id: "memorial_day",
    label: "Memorial Day",
    icon: "flag",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 72,
    title_en: "Memorial Day — In Remembrance",
    title_es: "Día de los Caídos — En Memoria",
    body_en:
      "Memorial Day reminds us that freedom and opportunity were secured through sacrifice. We honor the men and women who gave their lives in service to our nation. Have a safe weekend, and look out for one another.",
    body_es:
      "El Día de los Caídos nos recuerda que la libertad y la oportunidad se aseguraron mediante el sacrificio. Honramos a los hombres y mujeres que dieron su vida en servicio a nuestra nación. Tengan un fin de semana seguro, y cuídense unos a otros.",
  },
  {
    id: "independence_day",
    label: "Independence Day",
    icon: "flag",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 48,
    title_en: "Independence Day",
    title_es: "Día de la Independencia",
    body_en:
      "Independence Day is a moment to recognize the country that gives MASCI the opportunity to build, employ, and contribute. Thank you for the work you do. Travel safe, stay hydrated, and look out for your crew.",
    body_es:
      "El Día de la Independencia es un momento para reconocer al país que da a MASCI la oportunidad de construir, emplear y contribuir. Gracias por el trabajo que hacen. Viajen seguros, manténganse hidratados, y cuiden a su cuadrilla.",
  },
  {
    id: "labor_day",
    label: "Labor Day",
    icon: "hard-hat",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 72,
    title_en: "Labor Day — In Recognition of the Trade",
    title_es: "Día del Trabajo — Reconocimiento al Oficio",
    body_en:
      "Labor Day recognizes the people who build the country with their hands. That is every operator, laborer, foreman, mechanic, and superintendent at MASCI. Thank you for the standards you hold and the work you deliver.",
    body_es:
      "El Día del Trabajo reconoce a las personas que construyen el país con sus manos. Eso es cada operador, obrero, capataz, mecánico y superintendente en MASCI. Gracias por los estándares que mantienen y el trabajo que entregan.",
  },
  {
    id: "veterans_day",
    label: "Veterans Day",
    icon: "shield-check",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 48,
    title_en: "Veterans Day — Thank You for Your Service",
    title_es: "Día del Veterano — Gracias por su Servicio",
    body_en:
      "To every veteran on our crews and to every veteran in our families — thank you. The discipline, professionalism, and accountability you carry into this work makes MASCI better. We are proud you are with us.",
    body_es:
      "A cada veterano en nuestras cuadrillas y a cada veterano en nuestras familias — gracias. La disciplina, profesionalismo y responsabilidad que traen a este trabajo hace mejor a MASCI. Estamos orgullosos de tenerlos con nosotros.",
  },
  {
    id: "thanksgiving",
    label: "Thanksgiving",
    icon: "calendar-heart",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 72,
    title_en: "Thanksgiving — From the MASCI Family",
    title_es: "Día de Acción de Gracias — De la Familia MASCI",
    body_en:
      "Thanksgiving is a moment to recognize what we have built together. Whatever your tradition, take the time to be with the people who matter to you. Travel safe, drive rested, and we will see you back on the work.",
    body_es:
      "El Día de Acción de Gracias es un momento para reconocer lo que hemos construido juntos. Sea cual sea su tradición, tomen el tiempo de estar con las personas que les importan. Viajen seguros, conduzcan descansados, y nos veremos de regreso en el trabajo.",
  },
  {
    id: "christmas",
    label: "Christmas / Holiday Season",
    icon: "calendar-heart",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 96,
    title_en: "Christmas — From the MASCI Family",
    title_es: "Navidad — De la Familia MASCI",
    body_en:
      "From every superintendent, PM, mechanic, foreman, and crew at MASCI — Merry Christmas to you and your family. Drive carefully through the holiday traffic. We will see you back on the work in the new year.",
    body_es:
      "De cada superintendente, PM, mecánico, capataz, y cuadrilla en MASCI — Feliz Navidad a ustedes y a sus familias. Conduzcan con cuidado durante el tráfico de las fiestas. Nos veremos de regreso en el trabajo en el año nuevo.",
  },
  {
    id: "new_year",
    label: "New Year",
    icon: "calendar-heart",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 72,
    title_en: "New Year — Forward Together",
    title_es: "Año Nuevo — Adelante Juntos",
    body_en:
      "Another year of work behind us. Another year of opportunity ahead. Thank you for the standards you held in the past year, and for the standards we will hold together in the next one.",
    body_es:
      "Otro año de trabajo detrás de nosotros. Otro año de oportunidad por delante. Gracias por los estándares que mantuvieron en el año pasado, y por los estándares que mantendremos juntos en el próximo.",
  },
  {
    id: "work_zone_awareness",
    label: "National Work Zone Awareness Week",
    icon: "hard-hat",
    severity: "cultural",
    require_ack: false,
    default_expires_hours: 168,
    title_en: "National Work Zone Awareness Week",
    title_es: "Semana Nacional de Conciencia de Zonas de Trabajo",
    body_en:
      "Every cone we set up is the last line of defense between a driver who is not paying attention and a worker on our crew. Watch your MOT. Wear your hi-vis. Take care of the operator behind the operator.",
    body_es:
      "Cada cono que colocamos es la última línea de defensa entre un conductor distraído y un trabajador en nuestra cuadrilla. Vigile su MOT. Use su alta visibilidad. Cuide al operador detrás del operador.",
  },
];

/**
 * Severity → UI color + icon hint. Keep in sync with BannerStrip.jsx
 * and AdminBannersPanel.jsx (they import from here so we never drift).
 *
 * iter328 — calm chrome conversion: every severity now uses the same
 * `border border-l-4` + soft fill pattern as the platform family
 * contract, with severity driven by the LEFT-EDGE STRIPE color. No
 * more `border-b-2` slabs or full-bleed bright fills — banners now
 * sit calmly inside the platform's visual rhythm.
 *
 * `priority` enforces sort order in the picker / aggregator. Lower
 * number = higher priority. Cultural banners are intentionally last
 * so a Memorial Day banner can NEVER win over an active hurricane.
 */
export const SEVERITY_META = {
  // ── OPERATIONAL TIERS (always win over cultural) ───────────────
  critical: {
    label: "Critical",
    priority: 1,
    cls_bar: "bg-red-50 text-red-950 border-red-300 border-l-4 border-l-red-800",
    cls_chip: "bg-red-100 text-red-900 border-red-400",
    cls_btn: "bg-red-800 text-white hover:bg-red-900",
    icon: "octagon-alert",
    pulse: true,
  },
  warning: {
    label: "Warning",
    priority: 2,
    cls_bar: "bg-red-50 text-red-900 border-red-200 border-l-4 border-l-red-700",
    cls_chip: "bg-red-100 text-red-900 border-red-400",
    cls_btn: "bg-red-700 text-white hover:bg-red-800",
    icon: "alert-octagon",
    pulse: false,
  },
  advisory: {
    label: "Advisory",
    priority: 3,
    cls_bar: "bg-amber-50 text-amber-950 border-amber-200 border-l-4 border-l-amber-600",
    cls_chip: "bg-amber-100 text-amber-900 border-amber-400",
    cls_btn: "bg-amber-600 text-white hover:bg-amber-700",
    icon: "alert-triangle",
    pulse: false,
  },
  info: {
    label: "Notice",
    priority: 4,
    cls_bar: "bg-blue-50 text-blue-950 border-blue-200 border-l-4 border-l-blue-700",
    cls_chip: "bg-blue-100 text-blue-900 border-blue-300",
    cls_btn: "bg-blue-700 text-white hover:bg-blue-800",
    icon: "info",
    pulse: false,
  },
  // ── CULTURAL TIER (always loses to operational) ────────────────
  cultural: {
    label: "Remembrance",
    priority: 9,
    cls_bar: "bg-slate-50 text-slate-900 border-slate-200 border-l-4 border-l-slate-700",
    cls_chip: "bg-slate-100 text-slate-800 border-slate-300",
    cls_btn: "bg-slate-800 text-white hover:bg-slate-900",
    icon: "flag",
    pulse: false,
  },
};
