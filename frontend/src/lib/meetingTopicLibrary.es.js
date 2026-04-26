// Spanish translations for the MASCI Safety Meeting topic library.
// Keyed by the topic's `key` from meetingTopicLibrary.js.
//
// IMPORTANT: When a user fills the form in Spanish and submits, the app
// auto-swaps unedited template content BACK to the English canonical from
// meetingTopicLibrary.js so the database / printed PDF stays English.
// If the user EDITED a field, their typed value (Spanish or otherwise)
// is what gets saved.

export const TOPIC_LIBRARY_ES = {
  // EARTHWORK / EXCAVATION / UNDERGROUND
  trenching_shoring: {
    title: "Seguridad en Zanjas, Apuntalamiento y Excavación",
    hazards_reviewed:
      "Derrumbe / colapso · Sepultamiento · Caídas a la excavación · Golpe por material o tierra apilada · Atmósferas peligrosas · Acumulación de agua · Servicios subterráneos · Equipo cayendo a la zanja",
    discussion_notes:
      "• Persona competente inspecciona toda excavación diariamente, después de lluvia y tras cualquier cambio de condiciones.\n• Sistema de protección obligatorio a 5 pies+: talud, apuntalamiento, escudo o banco.\n• Tierra apilada y equipo a ≥2 pies del borde.\n• Escalera/rampa/escalones requeridos a 25 pies de cualquier trabajador en zanja de 4 pies+.\n• Prueba atmosférica donde se sospeche atmósfera peligrosa.\n• Cuadrillas fuera del radio de giro del equipo y nunca bajo cargas suspendidas.\n• Nadie entra a una zanja sin sistema de protección — punto.",
    references_cited:
      "OSHA 29 CFR 1926 Subparte P · OSHA 1926.651 · OSHA 1926.652 · OSHA Trenching Quick Card",
    action_items:
      "Confirmar persona competente · Verificar sistema según tipo de suelo · Ticket 811 vigente · Inspección diaria registrada · Plan de rescate revisado",
  },
  soil_classification: {
    title: "Clasificación de Suelos (Tipo A / B / C)",
    hazards_reviewed:
      "Sistema de protección equivocado · Colapso por debilidad no detectada · Suelos en capas comportándose como el más débil · Suelo saturado reclasificado tras lluvia",
    discussion_notes:
      "• Tipo A: más estable (arcilla, terreno duro) — talud 3/4:1.\n• Tipo B: medio (suelos limosos) — talud 1:1.\n• Tipo C: menos estable (grava, arena, sumergido) — talud 1.5:1.\n• Suelo en capas = clasificar como la capa más débil.\n• Suelo previamente alterado es automáticamente Tipo C.\n• Pruebas visuales + manuales por persona competente; reclasificar tras lluvia o congelación.\n• En caso de duda, clasificar más bajo (más conservador).",
    references_cited:
      "OSHA 1926 Subparte P Apéndice A · OSHA Tabla de Clasificación de Suelos",
    action_items:
      "Tipo de suelo registrado diariamente · Persona competente realiza prueba · Sistema ajustado tras cambio de clima",
  },
  underground_utilities: {
    title: "Servicios Subterráneos / Localización 811",
    hazards_reviewed:
      "Golpe a servicio (gas, eléctrico, fibra, agua, alcantarilla) · Explosión / incendio · Electrocución · Corte de servicio · Lesión por línea energizada",
    discussion_notes:
      "• Llame al 811 (o equivalente estatal) mínimo 2-3 días hábiles antes de excavar.\n• Verificar ticket vigente y NO vencido antes de excavar.\n• Verificar visualmente TODAS las marcas antes de romper terreno; marcas faltantes = parar y volver a llamar.\n• Excavación manual a 24 pulgadas de cualquier servicio marcado (zona de tolerancia).\n• Tratar toda línea no marcada como viva hasta probar lo contrario.\n• Golpe de línea: despejar el área, evacuar viento arriba para gas, sin interruptores/teléfonos cerca de gas, llamar al servicio Y al 911.\n• Daylight (vacío/manual) servicios críticos antes de excavar mecánicamente cerca.",
    references_cited:
      "OSHA 1926.651(b) · Mejores Prácticas CGA · Programa estatal 811",
    action_items:
      "Tickets 811 verificados · Marcas fotografiadas · Tolerancia manual aplicada · Spotter para excavación mecánica",
  },
  confined_space: {
    title: "Entrada a Espacios Confinados — Pozos, Bóvedas, Estaciones de Bombeo",
    hazards_reviewed:
      "Atmósfera peligrosa (bajo O2, H2S, metano, CO) · Sepultamiento · Atrapamiento · Caídas al espacio · Golpe por tapa levantada · Estrés térmico en espacio cerrado",
    discussion_notes:
      "• Programa de Permiso de Entrada antes de CUALQUIER ingreso.\n• Prueba atmosférica antes Y de manera continua: O2 19.5–23.5%, LEL <10%, H2S <10 ppm, CO <25 ppm.\n• Ventilación mecánica casi siempre requerida en alcantarillas/drenajes.\n• Asistente afuera todo el tiempo — nunca abandona el puesto.\n• Entrante con cuerda de recuperación + arnés; rescate sin entrada es la meta.\n• Comunicación continua (voz, radio, señales).\n• Rescate: nunca entrar tras un trabajador caído sin sistema de recuperación + SCBA.",
    references_cited: "OSHA 1926 Subparte AA · OSHA 1926.1203 · OSHA 1910.146",
    action_items:
      "Permiso firmado · Monitor de gas calibrado · Asistente asignado · Ventilación instalada · Plan de rescate informado",
  },
  earthmoving_equipment: {
    title: "Equipo de Movimiento de Tierra y Maquinaria Pesada",
    hazards_reviewed:
      "Golpe por equipo · Atropello al hacer de spotter · Atrapado entre equipo y objeto fijo · Volcadura · Accidentes al retroceder · Incidentes en radio de giro",
    discussion_notes:
      "• Inspección pre-turno en cada máquina — fluidos, llantas, luces, alarmas, extintor.\n• Cinturones de seguridad siempre puestos — sin excepciones.\n• Alarmas de retroceso operativas; spotters en áreas congestionadas o visibilidad limitada.\n• Establecer y hacer cumplir zonas prohibidas alrededor del radio de giro.\n• Trabajadores en tierra con chaleco hi-vis y dentro de la línea de visión del operador.\n• Contacto visual + pulgar arriba antes de mover equipo cerca de personal.\n• Estacionar en terreno nivelado, cuchilla/cucharón abajo, freno puesto, llave fuera al salir.",
    references_cited:
      "OSHA 29 CFR 1926 Subparte O · OSHA 1926.601 · OSHA 1926.602 · MUTCD Parte 6",
    action_items:
      "Inspecciones pre-op registradas · Spotters asignados · Zonas prohibidas marcadas · Equipo estacionado seguro al final del turno",
  },
  backing_spotters: {
    title: "Operaciones de Retroceso y Spotters",
    hazards_reviewed:
      "Atropello al retroceder · Golpe por equipo en reversa · Spotter golpeado por otro vehículo · Falla de comunicación · Puntos ciegos",
    discussion_notes:
      "• Alarmas de reversa operativas en cada equipo móvil / camión de volteo.\n• Spotter requerido al retroceder en áreas congestionadas o cerca de personal.\n• Spotter se ubica fuera del trayecto, en línea de visión del operador.\n• Perder de vista al spotter = PARAR. El operador nunca retrocede a ciegas.\n• Señales de bocina: 1 parar, 2 adelante, 3 reversa.\n• Vestimenta hi-vis obligatoria para spotters todo el tiempo.",
    references_cited: "OSHA 1926.601(b)(4) · Boletín OSHA Atropello en Reversa",
    action_items:
      "Spotters designados · EPP del spotter verificado · Señales revisadas · Plan de comunicación en marcha",
  },
  drilled_shaft: {
    title: "Operaciones de Perforación / Cajones",
    hazards_reviewed:
      "Caídas a pozo abierto · Colapso de pared · Golpe por barra Kelly · Sepultamiento por colapso de lodo/casing · Volcadura de grúa/perforadora · Oscilación de carga suspendida",
    discussion_notes:
      "• Pozos abiertos SIEMPRE cubiertos o barricadas; nunca dejar abiertos sin atender.\n• Cuadrilla en tierra fuera del radio de giro de la perforadora.\n• Trabajadores fuera del alcance de barra y casing suspendidos.\n• Manejo de lodo — EPP químico, protección contra salpicaduras, lavaojos a 25 pies.\n• Señalero capacitado para apoyo de grúa; aparejador certificado para jaulas y casings.\n• Riesgos de tropiezo (varilla, mangueras, líneas de lodo) controlados.",
    references_cited:
      "OSHA 1926 Subparte P · OSHA 1926 Subparte CC · DFI Drilled Shaft Safety",
    action_items:
      "Pozos cubiertos/barricadas · Radio de giro marcado · Señalero designado · EPP para lodo listo",
  },
  pipe_installation: {
    title: "Instalación de Tubería — RCP / DI / HDPE",
    hazards_reviewed:
      "Golpe por tubería suspendida · Aplastamiento / pellizco al unir · Trabajador en zanja bajo carga suspendida · Colapso de zanja · Resbalones en cama mojada · Lesión de espalda por manejo manual",
    discussion_notes:
      "• Trabajadores FUERA de la zanja mientras se baja la tubería. Reentrar solo después de asentar y liberar la carga.\n• Usar tenazas, eslingas o levantadores — nunca improvisado.\n• Señalero designado para grúa / excavadora colocando tubería.\n• Asentar uniones con medio mecánico — no a mano.\n• Líneas guía controlan rotación; trabajadores fuera del 'pinch'.\n• Sistema de protección de zanja en su lugar durante instalación.",
    references_cited:
      "OSHA 1926 Subparte P · OSHA 1926.251 (Aparejos) · ACPA Concrete Pipe Handbook",
    action_items:
      "Aparejadores certificados · Señalero designado · Líneas guía usadas · Escudo de zanja en su lugar",
  },
  compaction: {
    title: "Operaciones de Compactación",
    hazards_reviewed:
      "Síndrome de vibración mano-brazo · Vibración de cuerpo entero en rodillos · Golpe por compactador · Volcadura en pendiente · Ruido sobre 85 dBA · Atropello por rodillo en reversa",
    discussion_notes:
      "• Compactadores manuales: agarre firme, guantes anti-vibración, sin ropa suelta.\n• Rodillos vibratorios: nunca operar en pendientes mayores al máximo del fabricante.\n• Zonas prohibidas marcadas; spotters en bordes y conicidades.\n• Alarmas de reversa requeridas; reversa en pendiente solo con spotter.\n• 10 minutos de descanso por hora con equipo vibratorio para mitigar HAVS.\n• Protección auditiva requerida — la mayoría de compactadores supera 85 dBA.",
    references_cited:
      "OSHA 1926.95 · NIOSH Vibración Mano-Brazo · ACGIH TLV para vibración",
    action_items:
      "Guantes anti-vibración · Zonas prohibidas marcadas · Protección auditiva · Rotación de operadores",
  },
  dewatering: {
    title: "Desagüe / Wellpoint",
    hazards_reviewed:
      "Riesgo eléctrico de bombas en agua · Inestabilidad de zanja por bombeo excesivo o insuficiente · Latigazo de manguera · Resbalones · Violación ambiental por descarga inadecuada",
    discussion_notes:
      "• GFCI obligatorio en bombas eléctricas; cables inspeccionados a diario.\n• Bonding y aterrizaje de bombas sumergibles para prevenir choque.\n• Tasa de bombeo fijada para mantener zanja estable.\n• Descarga dirigida a ubicación aprobada — nunca a humedales o pendientes sin permiso.\n• Asegurar mangueras de descarga para evitar latigazo.\n• Manejo de combustible: contenedores con bonding, no fumar, extintor a 50 pies.",
    references_cited:
      "OSHA 1926.405 · Regulaciones EPA / FDEP · Permiso NPDES",
    action_items:
      "GFCI verificado · Bomba con bonding · Descarga aprobada · Área de combustible · SDS disponible",
  },
  manhole_work: {
    title: "Trabajo en Pozos de Inspección y Estaciones de Bombeo",
    hazards_reviewed:
      "Atmósfera peligrosa (H2S, metano, bajo O2) · Caídas a estructura abierta · Golpe por tapa · Sepultamiento por flujo súbito · Riesgo biológico por aguas residuales",
    discussion_notes:
      "• Tratar todo pozo como espacio confinado con permiso hasta probar lo contrario.\n• Prueba atmosférica antes y monitoreo continuo.\n• Ventilación con ventilador para alcantarillas activas.\n• Usar gancho de pozo correcto — nunca dedos en ranuras.\n• Barricadas / cubrir toda estructura abierta; nunca dejar sin atender.\n• Exposición a aguas residuales: protección de piel/ojos, descontaminación inmediata, higiene de manos.",
    references_cited:
      "OSHA 1926 Subparte AA · OSHA 1910.1030 (Patógenos Sanguíneos)",
    action_items:
      "Permiso firmado · Monitor calibrado · Ventilación · Suministros de descontaminación",
  },
  saw_cutting: {
    title: "Corte de Pavimento con Sierra",
    hazards_reviewed:
      "Sílice respirable · Cortes / amputaciones por disco · Retroceso (kickback) · Ruido · Calor / disco caliente · Golpe por tráfico · Contaminación por lechada",
    discussion_notes:
      "• Corte mojado siempre que sea posible — supresión con agua es control de Tabla 1 de OSHA.\n• Cuando el corte seco sea necesario: aspiradora HEPA Y protección respiratoria.\n• Inspeccionar disco antes de cada uso; descartar discos agrietados.\n• Agarre con dos manos; sin extender brazos; pie firme.\n• Protección auditiva — sierras de pavimento exceden 100 dBA.\n• Lechada: contenerla; no dejar correr a drenaje (violación NPDES).\n• Protección de ojos + cara contra astillas.",
    references_cited:
      "OSHA 1926.1153 (Sílice Tabla 1) · OSHA 1926.300 · OSHA 1926.95",
    action_items:
      "Equipo de corte mojado · Respirador si seco · Contención de lechada · EPP auditiva y facial · Disco inspeccionado",
  },
  curb_gutter: {
    title: "Operaciones de Cordones y Cunetas",
    hazards_reviewed:
      "Pellizcos en máquina slip-form · Contacto con concreto caliente/húmedo · Doblar y levantar repetitivo · Golpe por tráfico · Sílice de cortar concreto · Quemaduras químicas",
    discussion_notes:
      "• Trabajadores fuera de zona prohibida de slip-form — buffer típico de 6 pies.\n• Cuadrilla de acabado con guantes y botas impermeables; enjuagar contacto con piel inmediatamente.\n• Levantar / mover formas con mecánica adecuada — carga cerca, rodillas dobladas.\n• Trabajo de borde cerca de tráfico = protección positiva (mínimo línea de tambores, barrera preferida).\n• Corte de juntas sigue controles de sílice (Tabla 1).\n• Disponer concreto residual correctamente; no a drenajes.",
    references_cited:
      "OSHA 1926 Subparte Q · OSHA 1926.1153 · NIOSH Boletín de Trabajadores de Concreto",
    action_items:
      "EPP impermeable · Zona prohibida marcada · Plan de levantamiento · Controles Tabla 1 de sílice",
  },
  mse_wall: {
    title: "Construcción de Muro MSE / de Retención",
    hazards_reviewed:
      "Caídas desde paneles · Golpe por panel · Pellizco/aplastamiento al instalar tiras · Inestabilidad de borde de relleno · Lesiones por manejo de material",
    discussion_notes:
      "• Líneas guía controlan rotación de paneles.\n• Trabajadores tras paneles protegidos; fuera del radio de giro.\n• Tie-off al trabajar en bordes de 6 pies+; barandillas conforme crece el muro.\n• Equipo de compactación a distancia del frente según diseño.\n• Tiras de refuerzo desenrolladas con herramientas, no a mano.\n• Pie del muro estable antes de la siguiente capa.",
    references_cited:
      "OSHA 1926 Subparte M · AASHTO LRFD · NCMA Design Manual",
    action_items:
      "Líneas guía listas · Protección contra caídas 6 pies+ · Setbacks de compactación · Plan de levantamiento",
  },
  boring_drilling: {
    title: "Perforación / Perforación Direccional (HDD)",
    hazards_reviewed:
      "Golpe inadvertido a servicio · Estallido de lodo a alta presión · Pellizcos en manipulador de varilla · Resbalones en suelo con lodo · Frac-out · Atrapamiento en sarta de perforación",
    discussion_notes:
      "• Pothole / daylight todos los cruces antes de perforar.\n• Localización es obligatoria — verificar con dueño del servicio donde sea crítico.\n• Nunca tocar la sarta giratoria.\n• Plan de frac-out por escrito; kits de derrame en sitio.\n• Chorros de alta presión pueden cortar piel — manos lejos del chorro.\n• Fuerzas de retracción son altas — trabajadores fuera de la línea de tensión.",
    references_cited:
      "OSHA 1926.601 · Mejores Prácticas DCA para HDD · CGA Best Practices",
    action_items:
      "Cruces daylightados · Plan de frac-out · Kit de derrame listo · Zona de tensión despejada",
  },
  demolition: {
    title: "Operaciones de Demolición",
    hazards_reviewed:
      "Caídas · Golpe por escombros · Colapso prematuro · Exposición a asbesto / plomo · Polvo de sílice · Incendio de corte/trabajo en caliente · Golpe a servicios remanentes",
    discussion_notes:
      "• Estudio de ingeniería antes de demoler — pisos, muros, materiales, servicios.\n• Estudio de materiales peligrosos — asbesto, plomo, PCBs identificados y abatidos.\n• Servicios cortados, capeados, bloqueados antes de demoler.\n• Zonas de caída barricadas; spotters en perímetro.\n• Controles de polvo — supresión con agua y EPP respiratorio.\n• Permisos de trabajo en caliente para corte/soldadura/quema.\n• Inspección diaria de estructura remanente.",
    references_cited:
      "OSHA 1926 Subparte T · OSHA 1926.850 · OSHA 1926.1101 (Asbesto) · OSHA 1926.62 (Plomo)",
    action_items:
      "Estudio ingeniería · Estudio MatPel · Servicios LOTO · Zonas de caída · Permisos de hot work",
  },
  // TRAFFIC / MOT
  mot_setup: {
    title: "Configuración MOT y Control de Tráfico en Zona de Trabajo",
    hazards_reviewed:
      "Golpe por vehículos · Conductor distraído / impedido · Buffer / conicidad inadecuados · Exposición durante montaje y desmontaje · Visibilidad nocturna · Interfase equipo / vehículo dentro de zona",
    discussion_notes:
      "• Plan de Control de Tráfico (TCP) aprobado en sitio y coincidiendo con campo.\n• Montaje aguas arriba a aguas abajo; desmontaje al revés — nunca de cara al tráfico.\n• Longitudes de buffer / conicidad acordes a velocidad.\n• Dispositivos limpios, retroreflectivos, espaciados correctamente.\n• Plan interno de tráfico separa trabajadores de equipo dentro de la zona.\n• Trabajo nocturno: iluminación min 5 fc, todos en hi-vis Clase 3 con bandas retro.\n• Exposición pública controlada con protección positiva donde velocidad/volumen lo justifiquen.",
    references_cited:
      "MUTCD Parte 6 · FHWA Work Zone Safety · OSHA 1926 Subparte G · ATSSA",
    action_items:
      "TCP firmado · Dispositivos coinciden · Plan interno informado · Iluminación nocturna · Hi-vis Clase 3",
  },
  flaggers: {
    title: "Banderilleros y Exposición a Tráfico Público",
    hazards_reviewed:
      "Golpe por motorista · Conductor distraído / impedido · Conductor ignorando paleta · Trabajador solo · Deslumbramiento solar · Estrés por calor / frío",
    discussion_notes:
      "• Banderillero es posición certificada — tarjeta vigente.\n• Paleta de stop, no bandera, en todo trabajo pagado.\n• Estación con ruta de escape clara — nunca atrapado entre barrera y tráfico.\n• Hi-vis Clase 3 día, hi-vis con retro de noche.\n• Comunicación por radio de dos vías con cuadrilla y otros banderilleros.\n• Rotar banderilleros cada 2 horas con calor; agua, sombra, asiento entre rotaciones.\n• Posicionarse para distancia completa de visibilidad de frenado.",
    references_cited: "MUTCD Parte 6E · ATSSA Flagger Cert · Requisitos estatales",
    action_items:
      "Certificaciones verificadas · Paletas en buen estado · Ruta de escape · Horario de rotación · Comunicaciones probadas",
  },
  live_traffic: {
    title: "Exposición a Tráfico Vivo / Atropello",
    hazards_reviewed:
      "Trabajador atropellado · Conductor distraído · Exceso de velocidad · Intrusión por conicidades · Tiempo limitado de reacción de noche · Trabajador solo",
    discussion_notes:
      "• Causa #1 de muerte en nuestra industria — tratar todo vehículo como intrusión potencial.\n• Mantener conciencia situacional — un ojo en el tráfico cerca de carriles abiertos.\n• Pararse del lado protegido de barrera o equipo cuando sea posible.\n• Nunca cruzar carriles abiertos a pie — usar puntos de cruce aprobados.\n• Alarmas de intrusión / vehículo sombra donde la velocidad/volumen lo justifiquen.\n• Parar, ponerse tras protección, llamar dispatch si vehículo penetra el buffer.",
    references_cited:
      "FHWA Work Zone Safety · OSHA 1926.201 · MUTCD Parte 6 · NIOSH",
    action_items:
      "Buffer verificado · Vehículo sombra · Cuadrilla informada de rutas de escape · Respuesta a intrusión",
  },
  mot_moving_trucks: {
    title: "Colocación MOT desde Camiones en Movimiento",
    hazards_reviewed:
      "Caídas desde camión en movimiento · Golpe por vehículo · Pérdida de agarre · Anclaje inadecuado · Falla de comunicación · Calor / fatiga",
    discussion_notes:
      "• Trabajadores en parte trasera de camión MOT en movimiento DEBEN estar 100% atados a anclaje certificado.\n• No improvisar tie-off — barandillas y cajas NO son anclajes.\n• Velocidad del camión: 5 mph o menos.\n• Conductor y trabajadores con comunicación constante por radio o señales.\n• No subir/bajar mientras el camión se mueve.\n• Trabajadores nunca viajan en equipo a menos que haya plataforma designada.",
    references_cited: "OSHA 1926.501(b) · OSHA 1926.502 · MUTCD Parte 6",
    action_items:
      "Arneses inspeccionados · Anclajes verificados · Comunicación probada · Límite de velocidad",
  },
  lane_closures: {
    title: "Cierres de Carril — Únicos y Múltiples",
    hazards_reviewed:
      "Conductor atravesando cierre · Cuadrilla expuesta durante montaje · Conicidad inadecuada · Letreros confusos · Tumbado de conos por viento / estela",
    discussion_notes:
      "• Montaje SIEMPRE aguas arriba a aguas abajo; desmontaje al revés.\n• Primer camión = camión sombra con TMA donde se requiera.\n• Conos / tambores reemplazados si son tumbados — reponer inmediatamente.\n• Letreros 'Lane Closed' / merge visibles a distancia completa de visibilidad.\n• Punto de cruce delineado claramente; flechas apuntadas correctamente.\n• Verificar letreros de reducción de velocidad temporal.",
    references_cited:
      "MUTCD Parte 6 · Estándares DOT estatal · ATSSA Best Practices",
    action_items:
      "Dispositivos coinciden · Vehículo sombra · Letreros de velocidad · Plan de respuesta a tumbados",
  },
  shoulder_closures: {
    title: "Cierres de Acotamiento",
    hazards_reviewed:
      "Vehículo errante golpeando trabajadores · Área estrecha · Vehículos usando acotamiento como escape · Riesgos de borde",
    discussion_notes:
      "• Tratar acotamiento como exposición a tráfico vivo — EPP completo, TCP completo.\n• Vehículo sombra / TMA recomendado incluso en cierres de acotamiento a alta velocidad.\n• Vigilar bordes de caída — barricadas donde aplique.\n• Operaciones de zanja en acotamiento requieren barrera positiva del lado del carril.\n• Trabajadores protegidos por equipo / vehículo cuando sea factible.",
    references_cited:
      "MUTCD Parte 6 · FHWA Shoulder Operations · DOT estatal",
    action_items:
      "Vehículo sombra · Bordes de caída barricadas · Hi-vis Clase 3 · Posición de protección identificada",
  },
  detour_routing: {
    title: "Rutas de Desvío y Cierres de Carretera",
    hazards_reviewed:
      "Conductores ignorando letreros · Aviso anticipado inadecuado · Letreros confusos · Acceso de emergencia bloqueado · Frustración de residentes",
    discussion_notes:
      "• Letreros de aviso anticipado en todas las intersecciones — espaciado mínimo MUTCD.\n• Letreros 'DETOUR' con flecha en cada vuelta — sin flechas faltantes.\n• Letreros guía a lo largo de la ruta confirman que motoristas siguen el camino.\n• Coordinar con bomberos / EMS / policía local.\n• Comunicar a residentes / negocios locales con anticipación.\n• Confirmar letreros diariamente — vandalismo y robo son comunes.",
    references_cited:
      "MUTCD Parte 6F · Planes Estándar DOT · Coordinación con PD local",
    action_items:
      "Inventario de letreros caminado diariamente · Servicios de emergencia notificados · Difusión local",
  },
  pavement_marking: {
    title: "Operaciones de Marcado de Pavimento (Striping)",
    hazards_reviewed:
      "Golpe por tráfico a baja velocidad · Exposición a cloruro de metileno / MMA · Quemaduras por termoplástico caliente · Salpicaduras de cuentas de vidrio · Resbalones en pintura · Incendio / explosión (MMA)",
    discussion_notes:
      "• Cuadrillas de striping trabajan a baja velocidad — asegurar visibilidad extra (vehículos sombra adicionales, flechas grandes).\n• Termoplástico caliente 400°F+ — mangas largas, guantes térmicos, sin piel expuesta.\n• Epoxi MMA: protección respiratoria, no fumar, sin fuentes de ignición.\n• Cuentas de vidrio causan lesión ocular — protección facial completa.\n• Trabajadores aguas abajo del kettle fuera de la pluma de humos.\n• Recorrer ruta del camión antes para verificar obstáculos.",
    references_cited:
      "OSHA 1926.59 (HazCom) · MUTCD Parte 6 · SDS del material",
    action_items:
      "Vehículos sombra · EPP resistente a quemaduras · SDS de MMA revisada · Extintor listo",
  },
  sign_installation: {
    title: "Instalación y Remoción de Letreros",
    hazards_reviewed:
      "Golpe por tráfico durante instalación · Esfuerzo al levantar · Caídas desde plataforma aérea · Atrapado entre auger y obstáculos · Golpe a servicio subterráneo al perforar",
    discussion_notes:
      "• Ticket 811 antes de cualquier perforación de poste.\n• Levantamiento de dos personas para letreros >50 lb o sobredimensionados.\n• Trabajo aéreo para letreros suspendidos: tie-off en canasta, no trepar el truss.\n• Eslingas para paneles certificadas para la carga.\n• Zonas prohibidas del auger marcadas; spotter en cercas y cunetas.\n• Re-pintar marcas tras letreros temporales removidos.",
    references_cited:
      "MUTCD Parte 6 · OSHA 1926.453 (Plataformas) · OSHA 1926.251",
    action_items:
      "Ticket 811 vigente · Plan de levantamiento · Protección contra caídas en aérea · Eslingas inspeccionadas",
  },
  crash_cushion: {
    title: "Instalación de Atenuador de Impacto",
    hazards_reviewed:
      "Golpe por tráfico · Pellizcos entre módulos · Golpe por tornillo de anclaje · Levantamientos pesados · Daño oculto en atenuadores usados",
    discussion_notes:
      "• Tornillos de anclaje solo después de ticket de localización.\n• Levantamientos de módulos — eslingas certificadas, señalero, zona de caída designada.\n• Trabajadores fuera de la línea de tensión durante levantamiento.\n• Inspeccionar cada módulo — los dañados se retiran de servicio.\n• Lámina reflectiva limpia antes de colocar.\n• Atenuador montado en camión (TMA) en vehículo sombra confirmado operacional.",
    references_cited: "Estándares MASH · MUTCD Parte 6 · DOT estatal",
    action_items:
      "Ticket de localización · Eslingas inspeccionadas · Módulos inspeccionados · TMA operacional",
  },
  vms_signs: {
    title: "Letreros de Mensaje Variable (VMS / DMS)",
    hazards_reviewed:
      "Golpe por tráfico durante colocación · Volcadura del trailer · Choque eléctrico de sistema solar/batería · Pellizcos al subir mástil · Contacto con altura libre",
    discussion_notes:
      "• Colocar VMS en terreno estable y nivelado — outriggers totalmente extendidos.\n• Verificar altura libre antes de subir mástil — líneas eléctricas, árboles.\n• Sistema de batería y solar — lejos de chispas, no fumar cerca.\n• Bloquear mástil a altura completa antes de alejarse.\n• Mensaje claro, legible, frase aprobada por MUTCD.\n• Asegurar trailer con candado cuando esté desatendido.",
    references_cited: "MUTCD Parte 6F · Manual del fabricante · OSHA 1926.405",
    action_items:
      "Outriggers puestos · Altura libre verificada · Mástil bloqueado · Candado de hitch",
  },
  barrier_placement: {
    title: "Colocación de Barrera de Concreto / Llena de Agua",
    hazards_reviewed:
      "Golpe por tráfico durante colocación · Aplastamiento por barrera suspendida · Pellizcos al conectar segmentos · Esfuerzo al levantar barrera con agua · Falla por conexión incorrecta",
    discussion_notes:
      "• Cuadrilla del lado opuesto al equipo, nunca entre barrera y tráfico vivo.\n• Eslingas certificadas; puntos de levantamiento marcados.\n• Pasadores de conexión completamente asentados antes del siguiente levantamiento; sin conexiones improvisadas.\n• Barrera con agua requiere fuente — permiso de hidrante, manguera asegurada.\n• Distancia de deflexión considerada en diseño — trabajadores detrás fuera de zona.\n• Delineadores reflectivos en cada segmento para visibilidad nocturna.",
    references_cited: "Niveles de Prueba MASH · MUTCD Parte 6 · OSHA 1926.251",
    action_items:
      "Eslingas certificadas · Pasadores verificados · Zona de deflexión marcada · Delineadores",
  },
  // CONCRETE / PAVING
  concrete_silica: {
    title: "Operaciones de Concreto y Sílice Respirable",
    hazards_reviewed:
      "Sílice cristalina respirable (silicosis, cáncer de pulmón) · Quemaduras cáusticas por concreto húmedo · Irritación de piel/ojos · Empalamiento por varilla · Colapso de cimbras · Lesiones por levantar",
    discussion_notes:
      "• Tabla 1 de OSHA — emparejar cada tarea generadora de polvo con su control de ingeniería (agua O vacío).\n• Protección respiratoria (P100 o aire suministrado) cuando los controles sean insuficientes.\n• Guantes, botas, mangas impermeables con concreto húmedo; enjuagar contacto con piel inmediatamente.\n• Tapas de varilla en cada extremo expuesto a altura de tropiezo o menos.\n• Cimbras inspeccionadas y arriostradas antes de la colada.\n• Protección ocular obligatoria al cortar, esmerilar, aserrar, picar.",
    references_cited:
      "OSHA 1926.1153 · OSHA 1926 Subparte Q · NIOSH Boletín de Sílice",
    action_items:
      "Controles Tabla 1 · Sistemas de agua/vacío revisados · Respiradores ajustados · Tapas de varilla",
  },
  concrete_pumping: {
    title: "Bombeo de Concreto",
    hazards_reviewed:
      "Latigazo / falla de línea · Golpe por manguera · Quemaduras cáusticas por aerosol · Volcadura de bomba · Contacto con línea aérea · Tapón causando falla",
    discussion_notes:
      "• Outriggers totalmente extendidos sobre zoquetes; capacidad del suelo confirmada.\n• Mantener distancia de líneas aéreas — mínimo 10 pies (más para alto voltaje).\n• Manguero fuera de zona de latigazo potencial; comunicaciones con operador.\n• Protección de ojos/cara obligatoria — fittings rotos rocían cemento a presión.\n• Despejar tapones invirtiendo, nunca desconectando bajo presión.\n• Cadenas de seguridad en todas las conexiones de abrazadera.",
    references_cited: "ACPA Concrete Pump Safety · OSHA 1926.701 · OSHA 1926.405",
    action_items:
      "Outriggers · Altura libre · EPP facial · Comunicaciones probadas · Cadenas de seguridad",
  },
  formwork: {
    title: "Seguridad en Cimbra",
    hazards_reviewed:
      "Colapso de cimbra · Caídas desde cimbra · Golpe por cimbra cayendo · Pellizco/aplastamiento al desencofrar · Empalamiento por varilla · Falla de hardware bajo carga",
    discussion_notes:
      "• Cimbra diseñada por persona calificada para la carga (concreto + trabajadores + equipo).\n• Sin desviaciones del plano sin aprobación del ingeniero.\n• Inspeccionar cimbra antes de la colada — cada arriostre, tirante, puntal.\n• Trabajadores con tie-off al trabajar a 6 pies+.\n• Desencofrado: solo después de que el concreto alcance la resistencia requerida; zonas de caída controladas.\n• Tapas de varilla en todos los extremos expuestos; sin caminar sobre la malla superior sin tablones.",
    references_cited: "OSHA 1926.703 · ACI 347 Cimbra · OSHA 1926.703(b)",
    action_items:
      "Planos en sitio · Inspección pre-colada · Resistencia para descimbrar · Tapas de varilla",
  },
  bridge_deck_pour: {
    title: "Coladas de Tablero de Puente",
    hazards_reviewed:
      "Caídas por borde · Caídas por aberturas · Golpe por máquina de acabado · Aerosol de concreto · Tropiezo/empalamiento por varilla · Estrés térmico en coladas largas",
    discussion_notes:
      "• Barandilla perimetral o PFAS completo antes de cualquier trabajo en tablero.\n• Cubrir o barricadas todas las aberturas.\n• Zonas prohibidas de máquina de acabado marcadas; comunicaciones operador-cuadrilla.\n• Plan de estrés térmico activo — agua, hielo, sombra, rotación.\n• Briefing de cuadrilla: secuencia de colada, ubicación de descarga, comunicación con conductores de mezcladora.\n• Protección de borde en fascia hasta colar parapeto.",
    references_cited:
      "OSHA 1926 Subparte M · OSHA 1926.502 · AASHTO Construcción de Puentes",
    action_items:
      "Protección de borde · Aberturas cubiertas · Plan de calor · Secuencia informada",
  },
  curing_sealing: {
    title: "Curado y Sellado",
    hazards_reviewed:
      "Inhalación de vapores · Irritación de piel/ojos · Incendio / explosión por curados inflamables · Resbalón por curado húmedo · Salpicadura a la cara",
    discussion_notes:
      "• Leer SDS antes de cualquier uso; verificar EPP requerido.\n• Productos a base de solvente: protección respiratoria, no fumar, sin fuentes de ignición, aterrizar rociadores.\n• Rociar con el viento; apagar si cambia el viento.\n• Protección de ojos / cara obligatoria.\n• Riesgo de resbalón — banderear áreas húmedas, no caminar sobre superficies recién curadas.\n• Kits de derrame en sitio; cumplimiento ambiental ante cualquier derrame.",
    references_cited: "OSHA 1926.59 (HazCom) · SDS · NFPA 30 (Inflamables)",
    action_items:
      "SDS revisada · Respiradores listos · Zonas húmedas señaladas · Kits de derrame",
  },
  cold_weather_concrete: {
    title: "Operaciones de Concreto en Clima Frío",
    hazards_reviewed:
      "Estrés por frío / hipotermia · Quemaduras por agua caliente / vapor · CO de calentadores en encerramientos · Resbalones en hielo · Retroceso de agregado congelado",
    discussion_notes:
      "• Ropa en capas, guantes y botas impermeables aislantes; cubrir cabeza y cuello.\n• Encerramientos calentados: SOLO calentadores directos con monitoreo continuo de CO; O calentadores indirectos venteados al exterior.\n• Áreas de calentamiento (trailer / caseta) a 100 pies de la cuadrilla.\n• Sal / arena en superficies; señalar áreas con hielo.\n• Agua caliente para mezcla: 140°F máx en punto de uso; guantes requeridos.\n• Sistema de compañero — los primeros signos de congelación son sutiles.",
    references_cited:
      "Boletín OSHA Estrés por Frío · ACI 306 Concretado en Frío",
    action_items:
      "EPP de frío · Monitoreo de CO · Superficies sin hielo · Área de calentamiento",
  },
  asphalt_paving: {
    title: "Asfalto Caliente y Pavimentación",
    hazards_reviewed:
      "Quemaduras severas por mezcla caliente (300°F+) · Quemaduras por tack/aceite/combustible · Inhalación de humos · Golpe por pavimentadora, rodillo, camión · Atrapado entre rodillo y borde · Estrés térmico",
    discussion_notes:
      "• Mangas largas, pantalones largos, guantes para asfalto caliente, botas de cuero — incluso en calor.\n• Sin contacto de piel con mezcla caliente; rastrillado/lute con viento favorable.\n• Zonas prohibidas de pavimentadora y rodillo marcadas; spotters donde trabajadores se acerquen.\n• Conductor reconoce a la cuadrilla antes de descargar; comunicaciones con operador del screed.\n• Manejo de combustible y tack: contenedores con bonding, no fumar, extintor a 50 pies.\n• Programa de estrés térmico — agua, descanso, rotación de sombra.",
    references_cited:
      "OSHA 1926.95 EPP · NIOSH Boletín de Asfalto · NAPA Worker Safety",
    action_items:
      "EPP contra quemaduras · Zonas prohibidas · Monitoreo de calor · Extintor en sitio",
  },
  milling_operations: {
    title: "Operaciones de Milling (Cold Planing)",
    hazards_reviewed:
      "Golpe por tambor / banda transportadora · Polvo de sílice / asfalto · Pellizco en banda · Contacto con dientes calientes · Ruido sobre 95 dBA · Tropiezo en transiciones",
    discussion_notes:
      "• Trabajadores fuera de zonas prohibidas de tambor y banda durante operación.\n• Sistema de aspersión de agua en el tambor — control primario de sílice/polvo.\n• Respirador si el control de agua es insuficiente (milling viejo, condiciones secas).\n• Cambio de dientes: máquina apagada, bloqueada (LOTO), tambor frío.\n• Protección auditiva obligatoria.\n• Cuadrilla en tierra consciente de transiciones de grado; comunicaciones con operador.",
    references_cited:
      "OSHA 1926.1153 · NIOSH Asphalt Milling · OSHA 1910.147",
    action_items:
      "Zonas prohibidas · Aspersión verificada · Protección auditiva · LOTO para cambio de dientes",
  },
  tack_prime_coat: {
    title: "Aplicación de Tack Coat / Prime Coat",
    hazards_reviewed:
      "Quemaduras por tack caliente (140°F+) · Inhalación de humos · Resbalón en pavimento con tack · Salpicadura · Incendio / explosión de cutbacks",
    discussion_notes:
      "• Mangas largas, guantes, protección ocular — sin piel expuesta durante rociado.\n• Cutbacks son inflamables — sin fuentes de ignición, extintor listo.\n• Pararse contra el viento de la barra rociadora; probar boquillas antes.\n• Tiempo libre de pegajosidad observado antes de tráfico — banderear si peatones o vehículos se acercan.\n• Equipo limpiado con solvente aprobado; kits de derrame listos.\n• Comunicación operador-cuadrilla verificada.",
    references_cited: "OSHA 1926.59 (HazCom) · NAPA Tack Coat Best Practices",
    action_items:
      "EPP contra quemaduras · Extintor · Comunicación · Kit de derrame",
  },
  joint_sealing: {
    title: "Sellado de Juntas — Vertido Caliente y Frío",
    hazards_reviewed:
      "Quemaduras por sellador caliente 380°F+ · Inhalación de humos · Resbalón en junta sellada · Ruptura del kettle por presión · Incendio de solvente (frío)",
    discussion_notes:
      "• Vertido caliente: guantes térmicos, mangas largas, careta al verter.\n• Alivio de presión del kettle verificado al inicio del turno; nunca modificar dispositivos.\n• Control de humos — trabajar contra el viento; respiratorio si los humos irritan.\n• Solvente de vertido frío: revisar SDS, no fumar, contenedores aterrizados.\n• Sellador fresco señalado hasta curado.\n• Lanzallamas de mochila (calentador de junta) — solo al aire libre, sin fuentes de ignición cerca del cilindro.",
    references_cited: "OSHA 1926.59 · Manual del fabricante · NFPA 58 (Propano)",
    action_items:
      "EPP térmico · Kettle inspeccionado · SDS revisada · Señalización de zona curada",
  },
  diamond_grinding: {
    title: "Diamond Grinding y Grooving",
    hazards_reviewed:
      "Sílice respirable · Resbalones en lechada · Contacto con disco caliente · Ruido · Golpe por tráfico · Lesión ocular por astilla / aerosol",
    discussion_notes:
      "• Esmerilado mojado para control de sílice (Tabla 1) — agua continua en el disco.\n• Aspirar lechada para evitar contaminación de drenaje.\n• Protección auditiva — el proceso supera 95 dBA.\n• Protección de ojos / cara contra astillas y aerosol.\n• Operador lejos del disco; enfriar disco antes de mantenimiento.\n• Lechada dispuesta en ubicación aprobada.",
    references_cited:
      "OSHA 1926.1153 (Sílice Tabla 1) · ACPA Grinding Best Practices",
    action_items:
      "Aspersión verificada · Contención de lechada · EPP auditiva y ocular · Disposición aprobada",
  },
  sound_wall: {
    title: "Construcción de Muro Acústico",
    hazards_reviewed:
      "Caídas · Golpe por panel · Aplastamiento durante erección de columna · Viento atrapando paneles · Volcadura de grúa · Tráfico vivo adyacente",
    discussion_notes:
      "• Líneas guía controlan rotación; trabajadores fuera del radio de giro.\n• Monitoreo de velocidad de viento — parar colocación al umbral del fabricante.\n• Tie-off sobre 6 pies; barandilla perimetral / sistema de captura conforme crece el muro.\n• Señalero de grúa designado y certificado.\n• Lado de tráfico vivo: protección positiva (barrera) entre trabajo y carril.\n• Cimentaciones curadas a resistencia de diseño antes de colocar columna / panel.",
    references_cited:
      "OSHA 1926 Subparte M · OSHA 1926 Subparte CC · AASHTO LRFD",
    action_items:
      "Líneas guía · Monitor de viento · Protección 6 pies+ · Señalero designado",
  },
  hot_work: {
    title: "Trabajo en Caliente — Soldadura, Corte, Esmerilado",
    hazards_reviewed:
      "Incendio / explosión · Quemaduras · Exposición UV / IR (arco) · Inhalación de humos de soldadura · Escoria caliente igniciendo combustibles · Ruptura de cilindro de gas",
    discussion_notes:
      "• Permiso de Trabajo en Caliente requerido y en sitio para cualquier corte/soldadura/esmerilado fuera del taller.\n• Vigilante de fuego con extintor durante Y 30 min después.\n• Combustibles a 35 pies removidos o protegidos con mantas de soldadura.\n• Cilindros encadenados verticalmente, tapas puestas, oxígeno y combustible separados por 20 pies o barrera no combustible de 5 pies.\n• Protección ocular — sombra acorde al amperaje; protección de espectadores.\n• Ventilación o aire suministrado para galvanizado, cadmio o metal recubierto.",
    references_cited:
      "OSHA 1926 Subparte J · OSHA 1926.352 · NFPA 51B · ANSI Z49.1",
    action_items:
      "Permiso firmado · Vigilante de fuego · Combustibles despejados · Extintor listo · Cilindros asegurados",
  },
  // FALL PROTECTION
  fall_protection: {
    title: "Protección Contra Caídas — General",
    hazards_reviewed:
      "Caídas desde altura · Caídas a excavaciones · Caídas por aberturas · Falla de anclaje · Golpe por herramientas cayendo · Trauma por suspensión",
    discussion_notes:
      "• Tie-off 100% sobre 6 pies en construcción.\n• Anclajes calificados a 5,000 lb mínimo o sistema de ingeniería.\n• Inspeccionar arnés / lanyard / SRL antes de CADA uso — sin abrasión, cortes, indicadores desplegados, corrosión.\n• Calcular distancia de caída — anclaje + lanyard + caída libre + desaceleración + factor de seguridad.\n• Plan de rescate listo; trabajador suspendido requiere rescate en 15 minutos.\n• Herramientas amarradas o en bolsas con cierre en altura.\n• Barandillas, cubiertas, barricadas en cada hueco y borde.",
    references_cited: "OSHA 1926 Subparte M · OSHA 1926.501 · ANSI Z359",
    action_items:
      "Arneses inspeccionados · Anclajes identificados · Plan de rescate informado · Huecos cubiertos · Herramientas amarradas",
  },
  ladder_safety: {
    title: "Seguridad de Escaleras",
    hazards_reviewed:
      "Caídas · Deslizamiento de escalera · Volcadura · Electrocución por línea aérea · Sobre-extensión · Peldaños / rieles dañados",
    discussion_notes:
      "• Inspeccionar cada escalera antes de uso — sin grietas, rieles doblados, pies faltantes.\n• Regla 4:1 para escaleras de extensión.\n• Tres puntos de contacto; nunca cargar herramientas al subir.\n• Extender 3 pies sobre el punto de aterrizaje, asegurada arriba.\n• Nunca los dos peldaños superiores de tijera; nunca el tope de extensión.\n• No conductora (fibra de vidrio) cerca de eléctrico.\n• No alcanzar más allá de los rieles — bajar y mover la escalera.",
    references_cited:
      "OSHA 1926 Subparte X · OSHA 1926.1053 · ANSI A14",
    action_items:
      "Escaleras inspeccionadas · Defectuosas etiquetadas · Tie-off donde sea 6 pies+ · Fibra de vidrio para eléctrico",
  },
  aerial_lift: {
    title: "Plataforma Aérea / Boom Lift",
    hazards_reviewed:
      "Caídas desde plataforma · Volcadura por sobrecarga o terreno desigual · Golpe por obstáculo aéreo · Electrocución · Aplastamiento entre plataforma y estructura",
    discussion_notes:
      "• Operador certificado y autorizado; inspección pre-turno.\n• Tie-off en canasta — arnés cuerpo entero, lanyard al anclaje del fabricante.\n• Outriggers (donde aplique) totalmente extendidos en terreno nivelado.\n• Mantener mínimo 10 pies de líneas energizadas; más para mayor voltaje.\n• No trepar barandillas ni salir de canasta — la canasta es la única posición de trabajo.\n• Bocina antes de mover; spotter al viajar cerca de personal.",
    references_cited:
      "OSHA 1926.453 · ANSI A92 · Manual del Fabricante",
    action_items:
      "Inspección pre-turno · Operador certificado · Tie-off en canasta · Altura libre",
  },
  scaffold: {
    title: "Seguridad de Andamios",
    hazards_reviewed:
      "Caídas · Colapso por erección incorrecta · Golpe por material cayendo · Electrocución cerca de líneas · Volcadura por base inadecuada",
    discussion_notes:
      "• Erigido, modificado o desmantelado solo por personas calificadas bajo supervisión de persona competente.\n• Inspección diaria por persona competente antes de cada turno.\n• Barandillas en todos los lados abiertos sobre 10 pies.\n• Toe boards, pantallas o redes para prevenir caída de materiales.\n• Base sobre tablones o placas en suelo sólido; relación altura-base por fabricante.\n• Mantener 10 pies+ de líneas aéreas.\n• Acceso por escalera, torre o escalera incorporada — no trepar arriostres.",
    references_cited: "OSHA 1926 Subparte L · OSHA 1926.451",
    action_items:
      "Inspección diaria · Barandillas / toe boards · Base verificada · Ruta de acceso",
  },
  bridge_overpass: {
    title: "Trabajo en Puente / Paso Elevado",
    hazards_reviewed:
      "Caídas por borde · Caídas por aberturas · Tráfico vivo abajo o adyacente · Objetos cayendo a carriles · Golpe por tráfico viajante",
    discussion_notes:
      "• Protección perimetral ANTES de cualquier trabajo en tablero.\n• Plataformas de captura / redes para proteger carriles abajo.\n• Herramientas amarradas; partes pequeñas en bolsas con cierre.\n• Coordinar cierre de tráfico vivo abajo para operaciones de alto riesgo.\n• Trabajo de borde: anclaje positivo y PFAS — sin tareas de borde por trabajador solo.\n• Monitoreo de viento para operaciones de mástil alto.",
    references_cited:
      "OSHA 1926 Subparte M · AASHTO Construcción de Puentes · ANSI Z359",
    action_items:
      "PFAS perimetral · Plataforma de captura · Herramientas amarradas · Cierre coordinado",
  },
  cranes_hoisting: {
    title: "Operaciones de Levantamiento con Grúa",
    hazards_reviewed:
      "Volcadura · Golpe por carga suspendida · Aplastamiento · Two-blocking · Contacto con línea aérea · Falla de aparejo · Operador / señalero no certificado",
    discussion_notes:
      "• Operador Y señalero certificados.\n• Plan de levantamiento previo: peso, radio, aparejo, capacidad del suelo, trayectoria de giro.\n• Outriggers totalmente extendidos sobre zoquetes; capacidad del suelo confirmada.\n• Mantener distancia de líneas eléctricas (Tabla A).\n• Líneas guía controlan rotación; sin trabajadores bajo carga suspendida.\n• Dispositivo anti-two-block funcional; LMI calibrado.\n• Velocidad del viento monitoreada — parar al umbral del fabricante.",
    references_cited: "OSHA 1926 Subparte CC · ASME B30 · OSHA 1926.1408",
    action_items:
      "Plan firmado · Operador/señalero certificados · Zoquetes · Líneas guía · Monitor de viento",
  },
  rigging_load_securement: {
    title: "Aparejos y Aseguramiento de Carga",
    hazards_reviewed:
      "Falla de eslinga · Carga moviéndose en tránsito · Hitch / conexión incorrecta · Aparejo dañado · Pellizcos · Material cayendo por chock o correa incorrecta",
    discussion_notes:
      "• Inspeccionar cada eslinga, grillete, gancho antes de uso; remover dañados de servicio.\n• Igualar capacidad de eslinga a la carga — ajustar por tipo de hitch y ángulo.\n• Grilletes screw-pin o de perno para levantamientos elevados; nunca cargados de lado.\n• Etiquetas WLL legibles; equipo etiquetado fuera de servicio.\n• Trabajadores nunca bajo carga suspendida; líneas guía para control.\n• Cargas de camión: chocks, correas según FMCSA.",
    references_cited:
      "OSHA 1926.251 · ASME B30.9 · FMCSA 49 CFR 393",
    action_items:
      "Aparejos inspeccionados · Capacidades verificadas · Líneas guía · Aseguramiento de carga revisado",
  },
  // ELECTRICAL
  electrical_safety: {
    title: "Seguridad Eléctrica y Equipo Energizado",
    hazards_reviewed:
      "Electrocución · Arco eléctrico / explosión · Quemaduras · Caída por choque · Incendio por cables dañados · Arranque inesperado",
    discussion_notes:
      "• GFCI en cada circuito de 120V — energía temporal, generadores, extensiones.\n• Inspeccionar cables diariamente — sin chaquetas dañadas, conductores expuestos, pines de tierra faltantes.\n• LOTO para cualquier trabajo en sistemas eléctricos — verificado de-energizado con tester.\n• Mantener mínimo 10 pies de líneas aéreas (más para mayor voltaje).\n• Paneles y desconectadores cubiertos y etiquetados.\n• Solo personas calificadas trabajan en equipo energizado, y solo cuando de-energizar no sea factible.",
    references_cited:
      "OSHA 1926 Subparte K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items:
      "GFCI verificado · Cables inspeccionados · LOTO seguido · Distancia de altura libre",
  },
  loto: {
    title: "Bloqueo / Etiquetado (LOTO)",
    hazards_reviewed:
      "Arranque inesperado · Liberación de energía almacenada (hidráulica, neumática, gravedad, resortes) · Múltiples fuentes de energía · Burlando controles · Quitando candado de otra persona",
    discussion_notes:
      "• Identificar TODA fuente de energía — eléctrica, hidráulica, neumática, gravedad, térmica, química.\n• Notificar a empleados afectados, apagar normalmente, aislar, candado + etiqueta, verificar energía cero.\n• Cada trabajador autorizado aplica su propio candado personal — sin candados compartidos.\n• Probar energía cero: interruptor de arranque, manómetros, operación manual según corresponda.\n• Quitar tu propio candado = tu responsabilidad. Quitar el de otro requiere procedimiento de empleado ausente.\n• LOTO grupal usa lockbox + etiqueta maestra; todos firman entrada y salida.",
    references_cited: "OSHA 1910.147 · OSHA 1926 Subparte K · ANSI Z244.1",
    action_items:
      "Procedimiento LOTO en sitio · Candados personales · Fuentes de energía · Paso de verificación capacitado",
  },
  overhead_power: {
    title: "Trabajo Cerca de Líneas Eléctricas Aéreas",
    hazards_reviewed:
      "Electrocución por contacto · Arco por aproximación · Movimiento de equipo (boom, caja, escalera) en zona libre · Voltaje inducido en objetos paralelos",
    discussion_notes:
      "• Distancia mínima de 10 pies para líneas hasta 50 kV; más para mayor voltaje.\n• Donde no se puedan mantener 10 pies: de-energizar + aterrizar O instalar cubiertas O usar spotter dedicado.\n• Equipo con boom cerca de líneas — alarmas de proximidad, spotter dedicado, distancias Tabla A.\n• Cajas de volteo / escaleras — bajas hasta despejar.\n• Si el equipo contacta una línea: PERMANEZCA EN LA CABINA. Operador sale del contacto si es posible. Si no, salte limpio y arrastre los pies a 30+ pies.",
    references_cited:
      "OSHA 1926.1408 · OSHA 1926.952 · OSHA 1926.405",
    action_items:
      "Líneas identificadas · Distancia verificada · Spotter asignado · Respuesta a contacto",
  },
  generator_temp_power: {
    title: "Generador / Energía Temporal",
    hazards_reviewed:
      "Envenenamiento por CO · Choque eléctrico · Incendio / derrame · Backfeed a líneas de servicio · Sobrecarga del generador",
    discussion_notes:
      "• NUNCA operar generador a combustión adentro o en espacio cerrado — el CO mata.\n• 20 pies mínimo de edificios, ventilas, tomas de aire.\n• Aterrizar marco del generador a varilla de tierra donde se requiera.\n• GFCI en cada salida de 120V — muchos generadores no tienen GFCI interno.\n• Dimensionar circuitos para la carga; distribuir en fases.\n• Si alimenta panel, usar interruptor de transferencia (no backfeed por salidas).\n• Recargar combustible solo en frío; contenedores con bonding; no fumar.",
    references_cited: "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO",
    action_items:
      "Ubicación verificada · Bonding/aterrizaje · GFCI · Área de combustible",
  },
  light_tower: {
    title: "Operaciones de Torre de Iluminación",
    hazards_reviewed:
      "Volcadura al subir/bajar · Contacto con altura libre · Quemaduras por luces calientes · CO de sección de generador · Choque eléctrico por cables dañados",
    discussion_notes:
      "• Colocar en suelo nivelado y estable; outriggers totalmente extendidos.\n• Verificar altura libre antes de subir mástil.\n• Bloquear mástil a altura completa antes de alejarse.\n• Generador: recarga en frío, contenedor con bonding, no fumar, 20 pies de edificios.\n• Luces calientes — dejar enfriar antes de servicio o reubicación.\n• Inspeccionar cables a diario; torre dañada fuera de servicio.",
    references_cited: "OSHA 1926.405 · Manual del Fabricante",
    action_items:
      "Outriggers · Altura libre · Mástil bloqueado · Procedimiento de recarga",
  },
  lightning: {
    title: "Rayos y Tormentas Severas",
    hazards_reviewed:
      "Impacto directo · Flash lateral · Corriente de tierra · Energización de equipo · Daño por viento · Inundación súbita",
    discussion_notes:
      "• Regla 30/30 — cuando el trueno sigue al rayo en 30 segundos o menos, parar y refugiarse. Esperar 30 minutos tras el último trueno.\n• Sin refugio bajo árboles aislados, cabinas abiertas o andamios.\n• Mejor refugio: edificio cerrado, vehículo con techo duro (ventanas arriba).\n• Desconectar grúas, equipo y herramientas antes de la tormenta.\n• Vigilar inundación súbita en zonas bajas.",
    references_cited:
      "NWS Lightning Safety · OSHA Boletín de Rayos · NFPA 780",
    action_items:
      "App de clima · Ubicación de refugio · Regla 30/30 informada · Plan de apagado",
  },
  // EQUIPMENT-SPECIFIC
  excavator_safety: {
    title: "Seguridad de Excavadora",
    hazards_reviewed:
      "Volcadura en pendientes · Golpe por cucharón / contrapeso · Aplastamiento en radio de giro · Caída de cabina en pendiente · Falla de línea hidráulica · Desconexión de quick coupler",
    discussion_notes:
      "• Recorrido pre-turno; revisar tracks, suspensión, hidráulicos, fluidos, accesorios de cabina.\n• Operador se abrocha cinturón antes de arrancar.\n• Radio de giro marcado / barricadas — trabajadores fuera.\n• Cucharón al suelo al cargar camiones; nunca girar sobre la cabina del operador.\n• Quick coupler: enganche positivo verificado antes de levantar.\n• Estacionar nivelado, cucharón abajo, llave fuera, freno puesto.",
    references_cited: "OSHA 1926.602 · Manual del Fabricante",
    action_items:
      "Inspección pre-op · Radio de giro · Quick coupler verificado · Rutina de estacionamiento",
  },
  skid_steer: {
    title: "Seguridad de Skid Steer / CTL",
    hazards_reviewed:
      "Aplastamiento por brazos (al entrar/salir) · Volcadura en pendiente · Golpe por accesorios · Atropello por máquina en reversa · Quemaduras por escape/turbo · Desenganche de quick attach",
    discussion_notes:
      "• Entrar/salir SOLO con brazos abajo y cucharón plano — nunca bajo brazos elevados.\n• Cinturón y barra de asiento abajo antes de arrancar.\n• Pasadores de quick attach completamente enganchados — verificar antes de levantar.\n• Sin pasajeros. Sin pararse en accesorios.\n• Reversa en áreas congestionadas requiere spotter.\n• Estacionar nivelado, brazos abajo, cucharón al suelo.",
    references_cited:
      "OSHA 1926.602 · Manual del Fabricante · NIOSH Skid Steer",
    action_items:
      "Cinturón · Quick attach verificado · Spotter · Sin pasajeros",
  },
  forklift_telehandler: {
    title: "Operaciones de Montacargas / Telehandler",
    hazards_reviewed:
      "Volcadura · Golpe por carga · Atropello de peatones · Caídas desde horquillas (sin pasajeros) · Contacto con altura libre · Carga muy alta para ver",
    discussion_notes:
      "• Operador certificado (cert de 3 años + evaluación).\n• Inspección pre-turno registrada.\n• Capacidad con boom extendido es MENOR que retraído — leer la tabla.\n• Carga detrás del talón de horquillas; inclinar hacia atrás al viajar.\n• Viajar con horquillas bajas, ~6 pulgadas sobre el suelo.\n• Reversa en rampas con carga cuesta arriba; sin pasajeros nunca.\n• Outriggers requeridos para telehandler con alcance completo.",
    references_cited:
      "OSHA 1926.602 · OSHA 1910.178 · ANSI/ITSDF B56.6 · ANSI/ITSDF B56.1",
    action_items:
      "Cert vigente · Tabla de capacidad · Procedimiento de outriggers · Sin pasajeros",
  },
  dump_truck: {
    title: "Operaciones de Camión de Volteo",
    hazards_reviewed:
      "Volcadura al descargar (suelo desigual / suave) · Golpe por caja levantada o portón · Contacto con línea aérea al descargar · Atropello al hacer spotter · Quemaduras por motor / escape",
    discussion_notes:
      "• Descargar solo en suelo nivelado y firme.\n• Verificar SIN obstáculos aéreos (líneas, ramas, estructuras) antes de levantar caja.\n• Conductor permanece en cabina al descargar; spotter fuera de la línea de caída.\n• Portón despejado de obstrucciones antes de levantar.\n• Nadie entre el camión y el equipo cargándolo.\n• Inspección pre-viaje diaria.",
    references_cited:
      "OSHA 1926.601 · DOT FMCSA Pre-Trip · Manual del Fabricante",
    action_items:
      "Pre-viaje completado · Sitio nivelado · Altura libre · Posición del spotter",
  },
  // GENERAL / PERSONAL SAFETY
  ppe_general: {
    title: "EPP — Revisión Diaria de Cumplimiento",
    hazards_reviewed:
      "Lesión en cabeza · Lesión ocular · Pérdida auditiva · Lesión en pie · Laceración de mano · Lesión por aplastamiento · Falta de hi-vis llevando a atropello",
    discussion_notes:
      "• Casco — Tipo II para zonas de tráfico / impacto; reemplazar cada 5 años o tras impacto.\n• Lentes de seguridad con protectores laterales — ANSI Z87 mínimo.\n• Hi-vis Clase 2 día / Clase 3 noche para todo trabajo de carretera.\n• Botas con punta de acero o composite — sin tenis.\n• Guantes resistentes a cortes para trabajo afilado / abrasivo.\n• Protección auditiva donde el ruido > 85 dBA TWA.\n• EPP inspeccionado antes de uso; EPP dañado fuera de servicio.",
    references_cited:
      "OSHA 1926 Subparte E · OSHA 1926.95 · ANSI Z87 / Z89 / Z41",
    action_items:
      "Inventario EPP · EPP dañado reemplazado · Clase de hi-vis · Protección auditiva disponible",
  },
  stop_work: {
    title: "Autoridad para Suspender el Trabajo",
    hazards_reviewed:
      "Peligro inminente ignorado · Presión de producción sobre seguridad · Condición peligrosa escalando · Cuasi-accidente no reportado",
    discussion_notes:
      "• CADA miembro de la cuadrilla tiene la autoridad y responsabilidad de suspender el trabajo por cualquier preocupación de seguridad.\n• Nadie será represaliado, nunca, por suspender de buena fe.\n• Proceso: Parar. Notificar. Corregir. Reanudar. — los cuatro pasos.\n• Documentar el evento de Stop Work para aprender.\n• Stop Work cubre tu trabajo, tu cuadrilla, el público — cualquiera expuesto.\n• Si no estás seguro, para. Mejor perder 5 minutos que un compañero.",
    references_cited:
      "Cláusula General de OSHA 5(a)(1) · Política Stop Work MASCI",
    action_items:
      "Cartel Stop Work visible · Cuadrilla reconoce autoridad · Eventos recientes revisados",
  },
  heat_stress: {
    title: "Estrés Térmico / Hidratación",
    hazards_reviewed:
      "Agotamiento por calor · Insolación (emergencia médica) · Deshidratación · Tiempo de reacción reducido · Quemadura solar / UV",
    discussion_notes:
      "• Agua, descanso, sombra — protocolo OSHA-NIOSH.\n• 1 vaso de agua cada 15-20 minutos en trabajo pesado en calor.\n• Aclimatar trabajadores nuevos y de regreso — 20% de carga día 1, aumentar 20% por día.\n• Sistema de compañero — vigilar a tu pareja: confusión, habla arrastrada, piel caliente seca = insolación = 911.\n• Programar trabajo más pesado en horas frescas cuando sea posible.\n• Índice de calor publicado diariamente; protocolo activa a 80°F+.\n• Descansos en sombra o AC cada hora en días de alto calor.",
    references_cited:
      "Campaña OSHA Calor · Criterio NIOSH · Herramienta OSHA-NIOSH",
    action_items:
      "Agua y hielo · Estructura de sombra · Protocolo publicado · Plan de aclimatación",
  },
  cold_stress: {
    title: "Estrés por Frío / Hipotermia",
    hazards_reviewed:
      "Hipotermia · Congelación · Destreza manual reducida · Resbalones en hielo · Choque por contacto con agua helada · Sepultado por colapso de nieve",
    discussion_notes:
      "• Ropa en capas: base que absorba humedad, capa aislante, exterior resistente al viento/agua.\n• Cubrir cabeza, cuello, manos, pies — la mayor pérdida de calor es por extremidades.\n• Sistema de compañero — primeros signos de congelación son sutiles (entumecimiento, piel blanca).\n• Área de calentamiento a 100 pies, bebidas calientes (sin alcohol, limitar cafeína).\n• Intervalos más cortos a temperaturas más bajas; rotar cuadrilla.\n• Vigilar hipotermia: confusión, habla arrastrada, escalofríos — 911 + caliente + estable.\n• Quitar hielo de superficies antes del turno.",
    references_cited:
      "Boletín OSHA Frío · NIOSH Frío · CDC Hipotermia",
    action_items:
      "EPP de frío · Área de calentamiento · Sistema de compañero · Suministros de des-helar",
  },
  near_miss: {
    title: "Reporte de Cuasi-Accidentes",
    hazards_reviewed:
      "Cuasi-accidentes recurrentes llevando a lesión real · Peligros no reportados · Datos de tendencia perdidos · Cultura de silencio",
    discussion_notes:
      "• Un cuasi-accidente es una lección gratis. Trátalo como una lesión que tuviste suerte de evitar.\n• Reporta cualquier acto inseguro, condición insegura o cercana — mismo turno.\n• Reporte anónimo disponible; sin represalias.\n• MASCI rastrea cuasi-accidentes para tendencias — así prevenimos el siguiente incidente.\n• No culpar al trabajador; corregir condición o proceso.\n• Ejemplos: herramienta cayó de altura, intrusión de vehículo, oscilación amplia de carga, casi tropiezo.",
    references_cited:
      "OSHA VPP · ANSI Z10 · Procedimiento Cuasi-Accidente MASCI",
    action_items:
      "Formulario disponible · Reporte revisado · Reportes recientes discutidos · Acciones correctivas rastreadas",
  },
  stretch_flex: {
    title: "Estiramiento y Calentamiento / Reunión Diaria",
    hazards_reviewed:
      "Esguinces y torceduras · Lesiones de tejido blando · Lesión muscular en frío · Movimiento repetitivo · Resbalones/tropiezos/caídas en la primera hora del turno",
    discussion_notes:
      "• Rutina de 5 minutos antes del trabajo — cuello, hombros, espalda, caderas, isquiotibiales.\n• Recorrer la lista de tareas e identificar algo nuevo o inusual.\n• Confirmar asignaciones de cuadrilla y equipo del turno.\n• Identificar preocupaciones del clima (calor, frío, rayos, viento, lluvia).\n• Confirmar todos aptos para el deber — sin discapacidad, enfermedad o fatiga.\n• Recordatorio rápido de seguridad relevante al trabajo de hoy.",
    references_cited: "MASCI Daily Huddle SOP · NIOSH Ergonomía",
    action_items:
      "Rutina de estiramiento completada · Tareas informadas · Revisión de clima · Aptos confirmados",
  },
  slips_trips: {
    title: "Resbalones, Tropiezos y Caídas (Mismo Nivel)",
    hazards_reviewed:
      "Resbalón en superficies húmedas/aceitosas/heladas · Tropiezo con mangueras, varilla, escombros · Caída en terreno desigual · Tobillo torcido por agujeros / suaves · Cargando con carga al caminar",
    discussion_notes:
      "• Causa #1 de lesiones en obra civil pesada — y la más prevenible.\n• Superficies despejadas de mangueras, cables, varilla — enrollar y apilar.\n• Caminos definidos y marcados a través de la obra.\n• Botas con suela agresiva; reemplazar cuando estén desgastadas.\n• No cargar cargas que bloqueen la vista de los pies.\n• Sal/arena o barrer hielo y escombros.\n• Agujeros cubiertos o barricadas — banderear terreno desigual.",
    references_cited: "OSHA 1926.25 · OSHA 1926.501 · NIOSH STF",
    action_items:
      "Caminos marcados · Cables/mangueras manejados · Agujeros cubiertos · Superficies mantenidas",
  },
  hand_injury: {
    title: "Prevención de Lesiones de Mano",
    hazards_reviewed:
      "Laceraciones · Lesiones por aplastamiento (pellizcos) · Punciones · Quemaduras · Amputaciones por equipo giratorio · Esfuerzo repetitivo",
    discussion_notes:
      "• Igualar el guante al peligro — resistente a cortes para afilado, químico para químico, impacto para impacto.\n• Identificar pellizcos antes de alcanzar — usar herramientas para posicionar, no manos.\n• Empujar, no jalar — cuando jalar falla, tu mano va contra lo que jalas.\n• Nunca tocar disco, tambor o banda en movimiento — LOTO antes de servicio.\n• Inspeccionar herramientas a diario; remover dañadas de servicio.\n• Arrodillarse o usar plataforma estable para trabajo fino.",
    references_cited:
      "OSHA 1926.95 · Estadísticas BLS · Política de Seguridad de Manos MASCI",
    action_items:
      "Guantes apropiados · Pellizcos identificados · Herramientas inspeccionadas · LOTO informado",
  },
  hearing_conservation: {
    title: "Conservación Auditiva",
    hazards_reviewed:
      "Pérdida auditiva permanente inducida por ruido · Tinnitus · Dificultad de comunicación enmascarando otros peligros · Daño acumulativo de carrera",
    discussion_notes:
      "• Nivel de acción OSHA 85 dBA TWA — la mayoría de maquinaria pesada lo excede.\n• Tapones O orejeras — ambos para ruido de impacto (martillo, tambor de milling, demolición).\n• Reemplazar tapones de espuma diariamente; limpiar reusables a diario.\n• Audiograma anual por programa de conservación auditiva.\n• Vigilar señales tempranas: zumbido, subir TV, perder conversaciones.\n• Señales de mano silenciosas durante trabajo ruidoso; pre-arreglar comunicación.",
    references_cited: "OSHA 1926.101 · OSHA 1910.95 · NIOSH REL",
    action_items:
      "Protección disponible · Usada en ruido alto · Audiograma anual",
  },
  respiratory_protection: {
    title: "Protección Respiratoria",
    hazards_reviewed:
      "Sílice · Asbesto · Humos de soldadura · Solventes de asfalto/pintura · Diésel · CO · Moho / polvo · Ajuste inadecuado permitiendo exposición",
    discussion_notes:
      "• Respirador requerido cuando los controles de ingeniería sean insuficientes.\n• Prueba de ajuste anual — cuantitativa o cualitativa — registrada.\n• Autorización médica antes de uso de respirador.\n• Igualar cartucho al contaminante — P100 para partículas, OV para vapores orgánicos.\n• Inspeccionar antes de cada uso; verificación de sello en cada colocación.\n• Barba / vello facial rompe el sello — afeitado en superficie de sello.\n• Cartuchos tienen vida útil — cambiar según horario.",
    references_cited:
      "OSHA 1910.134 · OSHA 1926.103 · Certificación NIOSH",
    action_items:
      "Pruebas de ajuste · Cartuchos en stock · Procedimiento de sello · Horario de cambio",
  },
  fatigue: {
    title: "Fatiga y Conducción Somnolienta",
    hazards_reviewed:
      "Conducción somnolienta (commute) · Tiempo de reacción reducido · Errores de toma de decisiones · Microsueño · Mayor lesión al final de turnos largos",
    discussion_notes:
      "• La causa #1 de muerte en nuestra industria no es en sitio — es el viaje a casa.\n• 7-9 horas de sueño es no negociable para operación segura.\n• Turnos largos, nocturnos y 10s/12s consecutivos elevan el riesgo significativamente.\n• Sistema de compañero — di algo si un compañero muestra señales de fatiga.\n• Para y duerme una siesta si tienes sueño en el camino — café + AC frío es un mito.\n• Reportar fatiga al capataz — mejor que un choque.",
    references_cited:
      "NIOSH Fatiga · NHTSA Conducción Somnolienta · NSC",
    action_items:
      "Cuadrilla informada de señales · Verificación al final del turno · Sueño antes de turnos largos",
  },
  drug_alcohol: {
    title: "Política de Drogas y Alcohol / Apto para el Deber",
    hazards_reviewed:
      "Operación impedida de equipo / vehículo · Tiempo de reacción reducido · Mala toma de decisiones · Mayor lesión · Violaciones legales / DOT",
    discussion_notes:
      "• Cero tolerancia a alcohol o drogas (incluyendo marihuana) en horario de la empresa o roles cubiertos por DOT.\n• Medicamentos recetados — informar al supervisor si pueden afectar operación.\n• Pruebas aleatorias por política DOT y MASCI.\n• 'Apto para el deber' = mente clara, bien descansado, sano para hacer el trabajo.\n• Pruebas por sospecha razonable si comportamiento, olor u ojos sugieren impedimento.\n• Auto-reporte y referencia EAP protegidos — busca ayuda, no escondas.",
    references_cited:
      "DOT 49 CFR Parte 40 · Política MASCI · OSHA Drug-Free Workplace",
    action_items:
      "Política publicada · Horario de pruebas · Info de EAP",
  },
  bloodborne: {
    title: "Patógenos Sanguíneos y Respuesta de Primeros Auxilios",
    hazards_reviewed:
      "Exposición a sangre / OPIM · VIH / Hep B / Hep C · EPP inadecuado en respuesta · Manejo inadecuado de objetos punzantes · Falla de reportar exposición",
    discussion_notes:
      "• Tratar TODA sangre y fluidos como potencialmente infecciosos — precauciones universales.\n• Guantes desechables, protección ocular, máscara si hay riesgo de salpicadura.\n• Limpiar derrame con desinfectante aprobado; objetos punzantes en contenedor resistente a punciones.\n• Lavar manos completamente después de cualquier respuesta, con o sin guante.\n• Reportar exposición inmediatamente — vacuna Hep B y seguimiento disponibles.\n• Botiquín surtido, ubicación conocida, respondedores entrenados identificados.",
    references_cited:
      "OSHA 1910.1030 · OSHA 1926.50 · CDC BBP",
    action_items:
      "Botiquín revisado · Respondedores identificados · Kit de derrame · Procedimiento de reporte",
  },
  hazcom_sds: {
    title: "Comunicación de Peligros / SDS",
    hazards_reviewed:
      "Exposición química a producto desconocido · EPP equivocado · Incompatibilidades de almacenamiento · Disposición inadecuada · Pictogramas mal interpretados",
    discussion_notes:
      "• Cada químico en sitio tiene SDS — accesible.\n• Leer SDS antes del primer uso: peligros, EPP, almacenamiento, primeros auxilios, respuesta a derrame.\n• Etiquetas intactas y legibles — sin contenedores de transferencia sin marcar.\n• 9 pictogramas GHS — saber qué significa cada uno.\n• Segregación: inflamables aparte de oxidantes, ácidos aparte de bases.\n• Disposición según SDS y EPA / requisitos estatales — no a drenajes.",
    references_cited: "OSHA 1926.59 · OSHA 1910.1200 · GHS",
    action_items:
      "Carpeta SDS vigente · Etiquetas revisadas · Segregación · Disposición identificada",
  },
  wildlife_insects: {
    title: "Vida Silvestre / Picaduras de Insectos",
    hazards_reviewed:
      "Picaduras de abeja / avispa (anafilaxia) · Mordidas de serpiente · Ataques de hormigas rojas · Garrapatas / mosquitos · Encuentros con caimán / vida silvestre · Mordidas de araña · Atropellos animal-vehículo",
    discussion_notes:
      "• Caminos despejados; ojos al suelo en pasto alto.\n• Botas pesadas y pantalones largos en áreas de matorral.\n• Repelente con DEET 20-30%.\n• Alergia a abejas/avispas — EpiPen en sitio, ubicación conocida por la cuadrilla.\n• Mordedura de serpiente: víctima calmada, inmovilizar área mordida, 911 — SIN hielo, SIN torniquete, SIN succión.\n• Hormigas rojas: salir del área, sacudir, tratar; reacción alérgica = 911.\n• Caimanes en aguas de FL — nunca acercarse, nunca alimentar, mínimo 30 pies.",
    references_cited:
      "CDC Enfermedades Vectoriales · OSHA Quick Card · Agencia Estatal de Vida Silvestre",
    action_items:
      "Botiquín con suministros · EpiPen ubicado · Repelente surtido",
  },
  site_walk: {
    title: "Recorrido Diario del Sitio / Evaluación de Peligros",
    hazards_reviewed:
      "Nuevos peligros del trabajo de ayer · Cambios por clima (agua, escarcha, daño por viento) · Equipo / material movido · Invasión pública · Trabajo de servicios desde último turno",
    discussion_notes:
      "• Capataz recorre toda la zona de trabajo antes de que las cuadrillas inicien.\n• Buscar algo nuevo o diferente de ayer: agua en zanja, barricadas desplazadas, tumbados, robo, vandalismo.\n• Verificar que sistemas de protección sigan en lugar.\n• Verificar tropiezos por movimiento nocturno de equipo / material.\n• Reponer / reemplazar lo faltante o dañado antes de que las cuadrillas entren.\n• Documentar e informar hallazgos en la reunión.",
    references_cited: "MASCI Site Walk SOP · OSHA Persona Competente",
    action_items:
      "Recorrido completado · Hallazgos informados · Correcciones registradas",
  },
  housekeeping_cleanup: {
    title: "Limpieza y Orden al Final del Turno",
    hazards_reviewed:
      "Tropiezos por material dejado · Robo de herramientas / equipo no asegurado · Lesión pública por peligros abiertos · Contaminación de drenaje por derrames · Vandalismo / invasión",
    discussion_notes:
      "• 15 minutos de orden al final de cada turno — no negociable.\n• Herramientas y equipo pequeño bajo llave; equipo grande estacionado seguro.\n• Zanjas / estructuras abiertas cubiertas, barricadas, iluminadas.\n• Dispositivos MOT restaurados a configuración nocturna; luces revisadas.\n• Basura y escombros recogidos; sin plástico / desperdicio que pueda volar a drenajes.\n• Recorrer el sitio una última vez antes de salir.",
    references_cited: "OSHA 1926.25 · Estándar de Orden MASCI",
    action_items:
      "Herramientas aseguradas · Excavaciones cubiertas/iluminadas · MOT verificado · Recorrido completado",
  },
  new_hire_orientation: {
    title: "Orientación para Nuevos Contratados / Nuevos al Sitio",
    hazards_reviewed:
      "Desconocimiento de peligros del sitio · Equipo / procedimientos desconocidos · Mayor tasa de lesiones en primeros 30 días · EPP / capacitación faltante · Cultura desalineada en Stop Work",
    discussion_notes:
      "• CADA nuevo contratado y CADA persona nueva en el sitio recibe orientación específica del sitio.\n• Recorrer el sitio, señalar peligros, rutas de evacuación, botiquín, extintores.\n• Revisar TCP específico, JHA de su cuadrilla y permisos activos.\n• Reforzar Autoridad para Suspender Trabajo — la tienen desde el minuto uno.\n• Emparejar con compañero experimentado por 1-3 días.\n• Confirmar certificaciones / capacitación vigentes antes de iniciar.",
    references_cited: "OSHA 1926.21 · Procedimiento MASCI Nuevo Contratado",
    action_items:
      "Orientación completada · Compañero asignado · Registros de capacitación · Stop Work informado",
  },
  subcontractor_coordination: {
    title: "Coordinación con Subcontratistas",
    hazards_reviewed:
      "Actividades en conflicto · Desconocimiento mutuo de peligros · Diferentes estándares de seguridad · Falla de comunicación · Presión de horario sobre secuencia",
    discussion_notes:
      "• Cada sub en sitio ha tenido revisión pre-mob de seguridad con MASCI.\n• Reunión diaria de coordinación — quién está dónde, qué actividades, conflictos identificados.\n• Subs siguen estándares MASCI o más altos — nunca más bajos.\n• Autoridad MASCI para Suspender Trabajo se extiende a TODOS los trabajadores sin importar empleador.\n• JHA / plan pre-tarea compartido entre oficios en conflicto.\n• Incidentes reportados a MASCI mismo día.",
    references_cited:
      "Política OSHA Multi-Empleador · Pre-Cualificación MASCI",
    action_items:
      "Reps de seguridad sub identificados · Coordinación diaria · Stop Work extendido · JHAs compartidos",
  },
  emergency_action_plan: {
    title: "Plan de Acción de Emergencia / Evacuación",
    hazards_reviewed:
      "Emergencias del sitio (incendio, fuga de gas, clima severo, amenaza activa) · Evacuación inadecuada · Falla de contar personal · Salida bloqueada · Respuesta 911 demorada",
    discussion_notes:
      "• Cada sitio tiene un EAP publicado — punto de reunión, rutas primaria y secundaria, indicaciones 911, contactos en sitio.\n• Contar TODO el personal en el punto de reunión — sistema de compañero o registro.\n• Nunca re-entrar por herramientas, vehículos o material.\n• Quien llama al 911 permanece en línea; provee dirección del sitio e info de acceso.\n• Operadores apagan equipo seguramente si hay tiempo; si no, evacuar inmediatamente.\n• Ensayar el EAP cada 90 días o tras cambios mayores del sitio.",
    references_cited:
      "OSHA 1926.35 · NFPA 101 · Manejo Estatal / Local de Emergencias",
    action_items:
      "EAP publicado · Punto de reunión · Dirección 911 verificada · Ensayo programado",
  },
  fire_prevention: {
    title: "Prevención de Incendios y Uso de Extintores",
    hazards_reviewed:
      "Ignición de hot work · Derrame de combustible / vapor · Fumar cerca de inflamables · Selección equivocada de extintor · Trabajador no entrenado peleando incendio · Incendio de vehículo/equipo",
    discussion_notes:
      "• Combustibles a 35 pies+ de hot work; extintor listo.\n• Polvo químico ABC para la mayoría de incendios; CO2 para eléctrico; espuma para combustibles.\n• PASS: Pull, Aim, Squeeze, Sweep — solo combatir incendio menor a un cesto y solo con ruta de escape clara.\n• En duda — sal y llama al 911.\n• No fumar cerca de combustible, grasa, solventes — solo áreas designadas.\n• Inspeccionar extintores mensualmente; recargar tras uso.",
    references_cited: "OSHA 1926 Subparte F · NFPA 10 · NFPA 51B",
    action_items:
      "Extintores inspeccionados · Técnica PASS · Áreas designadas · Permisos hot work",
  },
  spill_response: {
    title: "Respuesta a Derrames y Cumplimiento Ambiental",
    hazards_reviewed:
      "Liberación de combustible / aceite a suelo o drenaje · Derrame químico · Multas ambientales · Resbalón en material derramado · Inhalación de vapor",
    discussion_notes:
      "• Kit de derrame disponible donde sea que se use o almacene combustible, aceite, hidráulico, químicos.\n• Detener la fuente primero — cerrar válvulas, contenedores.\n• Contener el derrame — boom absorbente, calcetines, almohadillas.\n• Limpiar y disponer adecuadamente — materiales contaminados son residuos peligrosos.\n• Reportar derrames según umbral estatal/EPA — derrames menores rastreados, reportables llamados en tiempo requerido.\n• Tapetes de protección de drenaje durante reabastecimiento.",
    references_cited: "EPA SPCC · Requisitos FDEP / estatal · NFPA 30",
    action_items:
      "Kits en sitio · SDS de químicos · Umbral de reporte · Tapetes desplegados",
  },
  mental_health: {
    title: "Salud Mental y Prevención del Suicidio",
    hazards_reviewed:
      "Industria de construcción tiene tasa elevada de suicidio · Estigma previene buscar ayuda · Abuso de sustancias · Estrés familiar / financiero · Duelo por compañero",
    discussion_notes:
      "• Los trabajadores de construcción tienen una de las tasas de suicidio más altas de cualquier industria — esto importa.\n• Cuídense unos a otros: cambios de ánimo, retraimiento, mayor uso de sustancias, hablar de desesperanza.\n• Está bien preguntar: '¿Estás bien? ¿Estás pensando en lastimarte?' Preguntar NO planta la idea — puede salvar una vida.\n• 988 — Línea de Suicidio y Crisis (llamar o textear). EAP MASCI para ayuda confidencial.\n• Reducir estigma — hablar de salud mental es fortaleza, no debilidad.\n• Fomentar afrontamiento sano: dormir, ejercicio, tiempo libre, apoyo de pares.",
    references_cited:
      "Datos CDC Suicidio Construcción · Línea 988 · EAP MASCI · CIASP",
    action_items:
      "Info 988 / EAP publicada · Check-in de cuadrilla · Reducción de estigma discutida",
  },
};
