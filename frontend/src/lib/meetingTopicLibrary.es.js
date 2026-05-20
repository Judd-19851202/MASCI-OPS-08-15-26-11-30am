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
    incident_pattern:
      "Las fatalidades por colapso de zanja siguen el mismo patrón casi siempre: una zanja de 4 a 6 pies, un trabajador baja 'nomás un minuto' a revisar grado o jalar un tubo atorado, y la pared falla. La zanja está apenas debajo de 5 pies, la cuadrilla no jaló la caja por un tramo tan corto, y la pila de spoil queda a un pie del borde. La pared entra como una sola losa — no como un hundimiento lento. El trabajador queda enterrado hasta el pecho en 2 segundos, y una yarda cúbica de tierra pesa ~3,000 lb. Aun si la cabeza queda libre, la compresión del pecho mata en menos de 5 minutos. Hemos perdido trabajadores en este mismo patrón en nuestra región. Cinco pies no es un número mágico — profundidad, suelo, agua y tráfico todos importan.",
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
    incident_pattern:
      "La mala clasificación del suelo mata más seguido que ninguna clasificación — porque la caja o el talud se eligió con confianza para el tipo EQUIVOCADO. Una zanja se clasifica como 'arcilla Tipo A' en la junta matutina, la caja coincide con eso, y la pared falla porque la lluvia de la semana pasada saturó las 18 pulgadas superiores a Tipo C efectivo. La persona competente lo caminó seco, hizo la prueba manual con material de un día, y la cuenta cambió de la noche a la mañana. El arreglo es reclasificación recurrente — después de lluvia, después de congelación-deshielo, después de vibración, después de cualquier disturbio. Cuando hay duda, clasifique HACIA ABAJO, no hacia arriba. El costo de un talud extra son unas yardas cúbicas; el costo de equivocarse es una fatalidad.",
    hazards_reviewed:
      "Sistema de protección equivocado · Colapso por debilidad no detectada · Suelos en capas comportándose como el más débil · Suelo saturado reclasificado tras lluvia",
    discussion_notes:
      "• Tipo A: más estable (arcilla, terreno duro) — talud 3/4:1.\n• Tipo B: medio (suelos limosos) — talud 1:1.\n• Tipo C: menos estable (grava, arena, sumergido) — talud 1.5:1.\n• Suelo en capas = clasificar como la capa más débil.\n• Suelo previamente alterado es automáticamente Tipo C.\n• Pruebas visuales + manuales por persona competente; reclasificar tras lluvia o congelación.\n• En caso de duda, clasificar más bajo (más conservador).",
    references_cited:
      "OSHA 1926 Subparte P Apéndice A · OSHA Tabla de Clasificación de Suelos",
    action_items:
      "Tipo de suelo registrado diariamente · Persona competente realiza prueba · Sistema ajustado tras cambio de clima",
  },
  excavation_potholing_daylight: {
    title: "Potholing y Daylight Antes de Excavación Mecánica",
    incident_pattern:
      "Los golpes a servicios subterráneos que el ticket 811 NO previno casi siempre se rastrean al mismo atajo: la cuadrilla obtuvo un locate, las marcas estaban imperfectas, y el operador golpeó algo con el cucharón tratando de 'encontrarlo.' Las marcas son orientativas — la zona de tolerancia alrededor de ellas es 18-24 pulgadas en la mayoría de los estados, y dentro de esa zona, la excavación mecánica debe PARAR y comienza el daylight. Una línea de fibra de 14 pulgadas, un main de gas de 6 pulgadas, un alimentador de alto voltaje — todos viven a una o dos pulgadas de donde el cucharón está excavando. El arreglo es potholing con aire o vacío antes de que el cucharón entre a la zona de tolerancia de cualquier marca. Cuesta una hora. La alternativa cuesta una vida o una cuadra entera de servicio.",
    hazards_reviewed:
      "Golpe a energía energizada · Ruptura de main de gas / explosión · Golpe a fibra / comm con impacto de servicio · Reventón de main de agua · Operador atrapado en flash por golpe eléctrico · Exposición de cuadrilla durante búsqueda-con-cucharón",
    discussion_notes:
      "• Ticket 811 válido Y vigente. Vuelva a llamar antes de que el cucharón empiece si el ticket pasó la ventana de expiración estatal.\n• Camine las marcas ANTES de que el operador se suba. Coteje marcas con el ticket. Cualquier cosa faltante o contradictoria — pare, vuelva a llamar.\n• Zona de tolerancia es típicamente 18-24 pulgadas a cada lado de la marca. Dentro de esa zona, no excavación mecánica. Punto.\n• Daylight con air-knife, excavador de vacío, o pala hasta que el servicio esté expuesto y confirmado. Luego mecánica puede reanudar.\n• Excavador de vacío: mantenga la varilla en movimiento, vigile la fuerza de succión, protección ocular contra rebote.\n• Operador y cuadrilla acuerdan señales ANTES de excavar. Movimiento del cucharón por la zona de tolerancia necesita reconocimiento explícito de la cuadrilla.\n• Si pega algo inesperado — PARE. No trate de despejarlo. Identifique qué es desde distancia segura.\n• Golpe de gas: despeje viento arriba, sin fuentes de ignición, llame al 911 y al servicio. No trate de tapar o detener la fuga usted mismo.\n• Golpe de energía: manténgase atrás. Trate cualquier cosa metálica en la zanja como energizada. Llame al 911 y al servicio. No entre a la zanja hasta que el servicio confirme desenergización.",
    references_cited:
      "Mejores Prácticas CGA · OSHA 1926.651(b) · Estatutos estatales 811 / One-Call · SOP de Locate MASCI",
    action_items:
      "Ticket 811 verificado vigente · Zona de tolerancia explicada al operador · Herramientas de daylight en sitio · Procedimiento de respuesta a golpe revisado",
  },
  excavation_spoil_placement: {
    title: "Colocación de Pila de Spoil Alrededor de Zanjas Abiertas",
    incident_pattern:
      "Los colapsos de zanja relacionados con spoil son predecibles y prevenibles. La pila de spoil queda a 18 pulgadas del borde porque el espacio disponible es apretado, el excavador corre paralelo a la zanja porque el trabajo lo demanda, y el suelo ha estado en el sol perdiendo humedad toda la mañana. Para las 2 p.m. la carga de sobrepeso en el borde de la zanja más la vibración del equipo corriendo más el asentamiento natural del terreno original saturado mina la pared. La pared se desliza adentro. Un trabajador en el fondo revisando grado queda enterrado. Mismo patrón que las zanjas de wellpoint, pero en trabajo diario de tubería y servicios pasa más seguido porque las cuadrillas están menos alerta.",
    hazards_reviewed:
      "Colapso de zanja por sobrecarga de spoil · Vibración de equipo aflojando pared · Engullimiento de trabajador · Avalancha de material de spoil sobre cuadrilla · Tropezón con pila en el borde",
    discussion_notes:
      "• Spoil mínimo 2 pies del borde de la zanja. Para zanjas más profundas que 5 pies, empújela atrás a una profundidad-de-zanja o más. Si no puede, la caja se llama inmediatamente.\n• Trayectos de equipo a una profundidad-de-zanja atrás del borde. Excavadores corriendo paralelos a una zanja transmiten vibración a través del spoil hacia la pared.\n• Si el spoil TIENE que quedarse cerca, instale plywood o placas de acero en el borde para distribuir la carga.\n• Vigile la pila a través del día. Una pila firme a las 7 a.m. puede estar suelta-flujo a las 2 p.m. al secarse — o saturada y más pesada después de lluvia.\n• Grietas de tensión en el borde son su última advertencia. Si ve una, saque trabajadores AHORA y reinstale protección antes de re-entrar.\n• Caras de pila de spoil — si una pila está amontonada en el borde, el lado que ve a la zanja puede avalanzar al fondo por sí solo. Mantenga pilas extendidas, no amontonadas.\n• Trabajadores pasando el borde sobre una pila — riesgo de tropezón, torcedura de tobillo. Mantenga ruta de acceso limpia en cada escalera.\n• Hablen cada mañana. La pila cambia diariamente — el plan de ayer no es el plan de hoy.",
    references_cited:
      "OSHA 29 CFR 1926.651(j) · OSHA 1926.652 · NIOSH Trinchera · SOP de Zanja MASCI",
    action_items:
      "Setback de spoil verificado · Trayecto de equipo movido del borde · Inspección diaria de borde asignada · Respuesta a grieta de tensión revisada",
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
    incident_pattern:
      "Las fatalidades por golpe-por en zona de trabajo se concentran en dos momentos: MONTAJE y DESMONTAJE. Las cuadrillas suelen estar más seguras a media tarde con la zona totalmente instalada. Pero a las 6 a.m. cuando los conos se ponen, y a las 8 p.m. cuando se levantan, los trabajadores están dentro del carril vivo, el buffer no está armado, y el público no se ha condicionado a reducir velocidad. El patrón es un solo chofer distraído, un trabajador de 6 pies colocando un cono, y una velocidad de cierre de 65+. El arreglo es montaje upstream-a-downstream, desmontaje downstream-a-upstream — y tratar el PRIMER cono y el ÚLTIMO cono como los objetos más mortales del trabajo.",
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
    incident_pattern:
      "Las fatalidades de banderilleros se recuerdan por nombre en esta industria, y el patrón casi siempre es el mismo: posición solitaria, sin camión sombra detrás, un solo chofer distraído o impedido cruzando el taper a velocidad. El banderillero no ve el camión a tiempo para hacerse a un lado — o se congela. Brillo del sol en el paddle, uniformes oscuros al atardecer, y un turno largo sin rotación lo amplifican. El arreglo es posicionar al banderillero para que tenga RUTA DE ESCAPE — nunca atrapado entre barrera y tráfico — y un camión sombra detrás en cualquier zona con velocidad o volumen. Un banderillero es la posición de mayor exposición de toda la cuadrilla.",
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
    incident_pattern:
      "El atropello en carretera es la causa principal de fatalidades de construcción, y el trabajador rara vez lo ve venir. El patrón: un trabajador está cabeza-abajo en una tarea — barriendo, marcando, sosteniendo una cinta — y un solo vehículo se desvía por el taper. Para cuando el trabajador escucha las llantas, tiene menos de 1 segundo de reacción. La mayoría de intrusiones fatales pasan en el BUFFER, no en el área de trabajo, porque el buffer está vacío y los choferes lo cortan. El arreglo es posicionar trabajadores en el lado PROTEGIDO de cualquier barrera o equipo, nunca pararse en un carril abierto, y tratar el buffer como si un vehículo ya estuviera entrando — porque eventualmente uno lo hará.",
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
    incident_pattern:
      "Las caídas y eyecciones desde camiones de colocación MOT pasan en un momento muy específico: el camión pega un bache inesperado, el trabajador en la caja pierde pisada, y el tie-off o falla o no estaba en un anclaje calificado. Las cuadrillas que han perdido trabajadores a esto universalmente describen lo mismo — habían estado haciéndolo igual por años, el anclaje era 'suficiente,' y un mal bache a 8 mph lo convirtió en fatalidad. El camión no tiene que ir rápido. El trabajador no tiene que ser descuidado. El arreglo es solo anclajes diseñados, tope duro de 5 mph, y cero subir/bajar mientras el camión está en movimiento.",
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
    incident_pattern:
      "Las intrusiones en cierres de carril siguen una curva predecible: la primera hora después del montaje, el público no se ha acondicionado al nuevo patrón, y 3-5 choferes van a pasar por encima de los conos antes de que se asiente. Esa primera hora es donde pasan las fatalidades por intrusión. Los cierres multi-carril añaden un segundo patrón — choferes que se dan cuenta tarde de que están en el carril equivocado, se barren al carril cerrado, y rozan un trabajador o equipo. El arreglo es un camión sombra con TMA durante la primera hora como mínimo, respuesta a derribos (reemplace el cono, camine la línea), y nunca dejar que el hueco de un cono derribado quede abierto más de un minuto.",
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
    incident_pattern:
      "Las cuadrillas tratan el trabajo en acotamiento como 'más seguro' que el trabajo en carril. No lo es. Los choferes errantes dejan el carril a velocidad por exactamente las razones por las que existen los acotamientos — distracción, somnolencia, problema mecánico, evasión de un peligro adelante. El acotamiento es a donde apuntan cuando dejan el carril. Un trabajador en cierre de acotamiento sin barrera positiva está tomando exposición de carril abierto. Combine con drop-offs de borde por milling o trinchera y un solo vehículo errante se vuelve multi-fatalidad. El arreglo es tratar el trabajo en acotamiento como exposición de tráfico vivo: camión sombra con TMA a alta velocidad, barrera positiva del lado del carril vivo, y trabajadores protegidos por equipo cuando se pueda.",
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
    incident_pattern:
      "Las fallas de desvío rara vez causan un solo incidente grande — causan docenas de pequeños. El patrón: una flecha faltante en una intersección, un trailblazer vandalizado, o señalización contradictoria manda choferes hacia el cierre o a una calle residencial que no fue diseñada para el volumen. Los automovilistas frustrados luego ignoran la siguiente ronda de señales, pasan conos, y crean exposición para la siguiente cuadrilla. La respuesta de emergencia es el modo de falla de mayor riesgo — un camión de bomberos o ambulancia pega el cierre a velocidad porque el desvío no se comunicó al dispatch. El arreglo es caminatas diarias de letreros, coordinación previa con PD/Bomberos/EMS locales, y tratar el robo / vandalismo de letreros como reparación del mismo día.",
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
    incident_pattern:
      "Las cuadrillas de striping son la zona de trabajo rodante más lenta en la carretera, y el público está condicionado a tráfico más rápido. El patrón de incidentes: un camión de termoplástico rodando a 3-5 mph, un operador de pintura caminando atrás, y un automovilista que cierra desde 70 mph en segundos sin registrar la diferencia de velocidad. El golpe pasa al trabajador trasero — el que ve la línea, no el tráfico. El patrón secundario es quemaduras de termoplástico caliente en piernas y pies del operador cuando el material salpica o una línea se rompe. El arreglo son múltiples camiones sombra con TMA, un spotter trasero vigilando solo el tráfico, y PPE calificado para quemadura que cubra de los tobillos hacia arriba.",
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
    incident_pattern:
      "Los incidentes de instalación de letreros se dividen entre dos patrones: golpes a servicios subterráneos al taladrar postes, y caídas desde plataformas aéreas en instalaciones de truss aéreo. El primero pasa cuando se salta un ticket 811 o las marcas se malinterpretan — una línea de fibra, gas o energía vive a 18 pulgadas debajo de donde se pone el auger, y el golpe cuesta la vista de un trabajador o inicia un fuego. El segundo pasa cuando un miembro de la cuadrilla se sale del bucket para alcanzar 'un poquito más' en una instalación de letrero guía. Los buckets existen porque el salirse es lo que mata gente. El arreglo es 811 sin excepciones + spotter en cada taladrado, y no subirse al truss — reposicione el bucket.",
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
    incident_pattern:
      "Los atenuadores de impacto existen para absorber un vehículo errante de modo que el trabajador detrás de ellos viva. El patrón de falla en instalación es apurarlo — módulos colocados en patrón de anclaje equivocado, pernos clavados antes de que se libere un locate, o un módulo dañado de un golpe previo redesplegado porque 'se ve bien.' Un atenuador usado con daño interno dejará pasar un vehículo a la mitad de la velocidad de diseño. La cuadrilla de instalación también está expuesta durante el montaje — están trabajando al filo de la zona de trabajo sin atenuador aún protegiéndolos. Trate el montaje mismo como la tarea de mayor exposición del día, y no redespliegue un módulo dañado — jamás.",
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
    incident_pattern:
      "Los incidentes de VMS caen en dos patrones: volcaduras del trailer al subir el mástil, y golpes a líneas aéreas cuando el mástil atrapa lo que nadie miró arriba primero. Las volcaduras pasan cuando los outriggers no están totalmente extendidos o el terreno cede — un trailer de 4,000 lb con mástil extendido atrapa una ráfaga, el outrigger delantero se hunde 4 pulgadas en asfalto blando, y el trailer se voltea con el mástil arriba. El patrón de golpe aéreo es idéntico al de cajas volcadoras: alguien sube un mástil sin mirar arriba porque el cielo 'se veía despejado.' El arreglo es el mismo: camínelo, mire arriba, confirme distancia antes de cualquier movimiento vertical.",
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
    incident_pattern:
      "Los incidentes de colocación de barrera siguen dos patrones. Primero — golpe-por durante instalación, porque la barrera no está ahí todavía para proteger a los instaladores del carril vivo. La cuadrilla está en máxima exposición por los 30-60 minutos que toma colocar un tramo. Segundo — aplastamiento por barrera suspendida cuando un pasador no está totalmente asentado o un sling se suelta. Un segmento de concreto de 6,000 lb cayendo 18 pulgadas matará a cualquiera debajo. El arreglo es la cuadrilla del lado OPUESTO del equipo de colocación (nunca entre barrera y tráfico vivo), enganche de pasador verificado antes del siguiente levante, y regla dura de que nadie se para bajo una carga suspendida — sin excepciones.",
    hazards_reviewed:
      "Golpe por tráfico durante colocación · Aplastamiento por barrera suspendida · Pellizcos al conectar segmentos · Esfuerzo al levantar barrera con agua · Falla por conexión incorrecta",
    discussion_notes:
      "• Cuadrilla del lado opuesto al equipo, nunca entre barrera y tráfico vivo.\n• Eslingas certificadas; puntos de levantamiento marcados.\n• Pasadores de conexión completamente asentados antes del siguiente levantamiento; sin conexiones improvisadas.\n• Barrera con agua requiere fuente — permiso de hidrante, manguera asegurada.\n• Distancia de deflexión considerada en diseño — trabajadores detrás fuera de zona.\n• Delineadores reflectivos en cada segmento para visibilidad nocturna.",
    references_cited: "Niveles de Prueba MASH · MUTCD Parte 6 · OSHA 1926.251",
    action_items:
      "Eslingas certificadas · Pasadores verificados · Zona de deflexión marcada · Delineadores",
  },
  mot_survey_crew_exposure: {
    title: "Exposición de Cuadrilla de Topografía a Tráfico Vivo",
    incident_pattern:
      "Los incidentes de golpe-por a cuadrillas de topografía tienen una forma reconocible: una cuadrilla de dos personas corriendo secciones transversales o estacando línea central, sin cierre instalado porque 'nomás venimos por una hora,' el rodman en el carril leyendo el prisma, el operador de instrumento enfocado en la estación. La cuadrilla está cabeza-abajo en el trabajo y condiciona al público a esperar que se quiten del camino. Un chofer distraído — celular, radio, sol — cierra la distancia en 3 segundos. La mayoría de golpes fatales son al rodman, no al operador, porque el rodman es el que está en o cerca del carril. El arreglo es tratar CUALQUIER trabajo de topografía en el acotamiento o carril vivo como exposición nivel-cierre: conos, hi-vis Clase 3, un spotter trasero, y una desviación legal siempre que sea posible.",
    hazards_reviewed:
      "Rodman golpeado por automovilista · Operador de instrumento golpeado en acotamiento · Chofer distraído cruzando la línea · Cegado por brillo del sol · Vehículo de topografía estacionado parcialmente en carril",
    discussion_notes:
      "• Cualquier shot en o cerca de un carril vivo lleva un cierre real — conos a espaciado MUTCD, letrero de aviso previo upstream, y un spotter trasero vigilando solo tráfico.\n• Hi-vis Clase 3 en ambos miembros. Rodman con cinta reflectiva en piernas y brazos — ahí es donde los faros atrapan el ojo.\n• Spotter trasero tiene radio Y silbato. Si ven un vehículo cerrando, llaman Y soplan — la señal auditiva es más rápida que el reconocimiento visual.\n• Vehículo de topografía estacionado FUERA del pavimento cuando sea posible. Si tiene que estar en acotamiento, intermitentes puestas y ruedas en ángulo lejos del tráfico para que un golpe no empuje el vehículo hacia la cuadrilla.\n• El brillo del sol importa. Si el sol está detrás de su zona en la mañana o tarde, agende esos shots cuando el sol esté arriba. Los carros literalmente no pueden verlo con sol en los ojos.\n• Sin 'nomás un shot más' si un cierre se empieza a romper. Pare, reinicie, luego continúe.\n• Topografía solitaria en tráfico vivo — no. Mínimo dos personas en cualquier exposición vial.\n• En ausencia de protección positiva verdadera, su SPOTTER TRASERO es la protección. Tome esa posición en serio.",
    references_cited:
      "MUTCD Parte 6 · Seguridad de Zona de Trabajo FHWA · Mejores Prácticas ATSSA · SOP de Topografía MASCI",
    action_items:
      "Conos / aviso previo verificados para ventana de topografía · Spotter trasero asignado · Hi-vis Clase 3 confirmado · Tiempo por brillo del sol revisado · Prohibición de trabajo solo reforzada",
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
      "• CADA nuevo contratado y CADA persona nueva en el sitio recibe orientación específica del sitio.\n• Recorrer el sitio, señalar peligros, rutas de evacuación, botiquín, extintores.\n• Revisar TCP específico, JHP de su cuadrilla y permisos activos.\n• Reforzar Autoridad para Suspender Trabajo — la tienen desde el minuto uno.\n• Emparejar con compañero experimentado por 1-3 días.\n• Confirmar certificaciones / capacitación vigentes antes de iniciar.",
    references_cited: "OSHA 1926.21 · Procedimiento MASCI Nuevo Contratado",
    action_items:
      "Orientación completada · Compañero asignado · Registros de capacitación · Stop Work informado",
  },
  subcontractor_coordination: {
    title: "Coordinación con Subcontratistas",
    hazards_reviewed:
      "Actividades en conflicto · Desconocimiento mutuo de peligros · Diferentes estándares de seguridad · Falla de comunicación · Presión de horario sobre secuencia",
    discussion_notes:
      "• Cada sub en sitio ha tenido revisión pre-mob de seguridad con MASCI.\n• Reunión diaria de coordinación — quién está dónde, qué actividades, conflictos identificados.\n• Subs siguen estándares MASCI o más altos — nunca más bajos.\n• Autoridad MASCI para Suspender Trabajo se extiende a TODOS los trabajadores sin importar empleador.\n• JHP / plan pre-tarea compartido entre oficios en conflicto.\n• Incidentes reportados a MASCI mismo día.",
    references_cited:
      "Política OSHA Multi-Empleador · Pre-Cualificación MASCI",
    action_items:
      "Reps de seguridad sub identificados · Coordinación diaria · Stop Work extendido · JHPs compartidos",
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

  // ============================================================
  // TRUCKING / FLEET · FAMILIA DE GOLPES DE CAJA · iter251 Fase B
  // ------------------------------------------------------------
  // Traducciones espejo de las 5 cápsulas en inglés. Voz de
  // patrón-real. Hechas para choferes y líderes de patio, no para
  // foremen leyendo diapositivas.
  // ============================================================
  dump_bed_overhead_strike: {
    title: "Golpes de Caja Volcadora — Líneas Aéreas, Puentes, Letreros, Bandas",
    incident_pattern:
      "La mayoría de los golpes aéreos suceden en el sitio de descarga mismo — no en tránsito. El chofer termina una carga, la caja sigue parcialmente levantada y el camión avanza para despejar la pila. En tres o cuatro pies de avance, la caja levantada engancha una línea aérea, un puente bajo, un letrero o una banda transportadora de planta. Para cuando el chofer se da cuenta de lo que pasó, la línea está en el suelo o la banda está doblada. Muchos de estos golpes son fatales cuando la línea está energizada.",
    hazards_reviewed:
      "Electrocución por línea aérea energizada · Golpe contra puente / letrero / estructura · Golpe contra banda transportadora de planta · Corte de servicio público · Volcadura por frenada con caja levantada",
    discussion_notes:
      "• Antes de levantar la caja — mire arriba. Líneas · puentes · letreros · bandas transportadoras de planta · estructuras aéreas.\n• Mantenga 20 pies de espacio libre de cualquier línea energizada. Si no puede confirmar que está desenergizada, trátela como viva.\n• Ponga el freno de estacionamiento antes de levantar. El camión NO debe rodar mientras la caja se mueve.\n• No mueva el camión hasta que la caja esté totalmente abajo. Mire el indicador en cabina o el espejo — no asuma.\n• En sitios desconocidos (plantas de asfalto, patios MOT, sitios de cliente), camine el área primero. Conozca el panorama aéreo.\n• Si toca una línea energizada: QUÉDESE EN LA CABINA. Llame al 911. Espere a que el servicio público confirme que la línea está desenergizada antes de bajarse. Bajarse con el camión energizado ha matado choferes.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.1408 (distancia a líneas eléctricas) · DOT FMCSA · Concientización de golpe a servicios",
    action_items:
      "Caminata aérea discutida · Indicador de caja arriba revisado · Procedimiento ante línea energizada revisado · Regla de 20 pies reforzada",
  },
  dump_bed_traveling_raised: {
    title: "Viajar Con la Caja Arriba — El Asesino Silencioso",
    incident_pattern:
      "Después de descargar, el chofer se enfoca en salir del área — checando espejos, buscando la siguiente carga, vigilando spotters en tierra. La caja sigue parcialmente arriba. El camión avanza, el chofer cambia su atención al camino, y la caja ahora va 6, 8, a veces 14 pies en el aire por todo el trayecto de salida. El golpe sucede en la primera obstrucción aérea — usualmente dentro de 50 pies de la pila. Los choferes lo describen igual cada vez: 'Se me olvidó que la caja estaba arriba.'",
    hazards_reviewed:
      "Golpe aéreo catastrófico · Contacto con línea eléctrica · Volcadura por centro de gravedad elevado a velocidad de carretera · Impacto contra puente / letrero · Incidente que cuesta la licencia",
    discussion_notes:
      "• La verificación de caja-abajo es LO PRIMERO después de descargar — no lo último. Antes que los espejos. Antes que la radio. Antes del siguiente movimiento.\n• Vigile el indicador en cabina de caja arriba. Si su camión no tiene uno, revise el espejo lateral ANTES de rodar adelante. Punto.\n• Las alarmas de caja arriba no son opcionales — si la suya está rota, ese camión no acarrea hasta que se arregle. Avise al Taller.\n• Las salidas de planta, de patio y de obra son los puntos de golpe más comunes. Reduzca velocidad en la salida y vuelva a revisar.\n• Velocidad de carretera con la caja levantada aunque sea parcialmente eleva su centro de gravedad peligrosamente — una curva a 55 mph puede volverse una volcadura.\n• Si nota a media ruta que la caja está arriba: NO frene fuerte. Reduzca de manera constante. Encuentre un costado seguro. Baje la caja allí.",
    references_cited:
      "OSHA 1926.601 · Pre-Viaje DOT FMCSA · Manual del fabricante · Especificación de alarma de caja arriba",
    action_items:
      "Hábito de caja-abajo-primero reforzado · Función de alarma de caja arriba verificada · Conciencia en salida de planta/patio revisada",
  },
  dump_bed_pto_habits: {
    title: "Desconexión del PTO y Hábitos de Bajar la Caja",
    incident_pattern:
      "Los incidentes de caja arriba relacionados con el PTO casi siempre se rastrean al hábito, no al equipo. El chofer entra en ritmo — descargar, revisar espejos, rodar. El paso de bajar la caja se comprime o se salta. En días calurosos, choferes fatigados, plantas ocupadas con varios camiones haciendo fila, la memoria muscular toma el control. El camión se mueve antes de que el PTO esté desconectado y antes de que la caja esté totalmente asentada. La siguiente operación — retroceder bajo una banda, entrar a un patio, entrar a la báscula de planta — es cuando ocurre el golpe.",
    hazards_reviewed:
      "Viaje con caja arriba por saltarse el paso de bajar PTO · Daño hidráulico · Golpe aéreo · Falla mecánica por traslado con PTO conectado · Incidente que cuesta la licencia",
    discussion_notes:
      "• PTO desconectado antes de rodar el camión. Cada descarga. Cada vez. Sin excepciones.\n• Secuencia: descargar → caja abajo → desconectar PTO → confirmar indicador → revisar espejos → rodar.\n• Si una planta llena o un sitio de cliente ocupado lo está apresurando, baje el ritmo. La planta esperará. La línea aérea no.\n• Si su camión tiene interlock (PTO conectado impide engranar la transmisión), no lo brinque. El interlock es la última defensa.\n• Capacite a choferes nuevos en esta secuencia el Día 1. Haga el paso de caja abajo explícito y verbal.\n• Después de cada descarga, antes de moverse — dígalo en voz alta o para usted: 'Caja abajo. PTO afuera. Espejos.' El hábito le gana a la prisa.",
    references_cited:
      "OSHA 1926.601 · DOT FMCSA · Especificación PTO del fabricante · SOP de fila en planta",
    action_items:
      "Secuencia de descarga verbalizada · Función de interlock PTO verificada · Refuerzo de hábito del chofer discutido",
  },
  dump_bed_soft_ground_tipover: {
    title: "Volcaduras en Terreno Blando — La Volcadura Con Caja Arriba",
    incident_pattern:
      "Una caja volcadora levantada hace al camión pesado de arriba. Una caja cargada y levantada lo hace peligrosamente pesado de arriba. El riesgo es mayor en el momento en que el material empieza a soltarse disparejo — asfalto pegajoso, material congelado, media carga atascada. El chofer siente que el camión se inclina, lo malinterpreta como la caja liberándose, y la sube más. El centro de gravedad se mueve hacia afuera, el lado blando se compacta, y el camión se voltea. La mayoría de las volcaduras en terreno blando suceden en la segunda o tercera descarga de la mañana cuando el terreno aún no se ha trabajado.",
    hazards_reviewed:
      "Volcadura con caja arriba · Aplastamiento del chofer en cabina al volcarse · Avalancha de material sobre la cuadrilla · Equipo adyacente / spotter golpeado · Volcadura en relleno blando / mojado / recién movido",
    discussion_notes:
      "• Descargue en terreno nivelado y firme. Si el suelo cede bajo el pie, va a ceder bajo 80,000 lb con la caja arriba.\n• Cargas que no se sueltan parejo — DEJE DE SUBIR. Baje la caja. Investigue. Asfalto caliente, material congelado y cargas atascadas son las señales de aviso.\n• Si siente que el camión se inclina hacia un lado mientras sube la caja — eso no es liberación normal. Baje la caja de inmediato. Bájese y revise.\n• Relleno recién puesto, lluvia reciente, días de hielo-deshielo — asuma que el terreno está blando hasta probar lo contrario. Camínelo antes de retroceder.\n• Nunca permanezca en la cabina con el cinturón sin abrochar durante una descarga. Si el camión se voltea, el cinturón es lo que lo mantiene vivo.\n• Los spotters se quedan fuera de la línea de caída — incluyendo los LADOS, no solo la parte trasera. Una volcadura con caja arriba lanza material 30+ pies de lado.",
    references_cited:
      "OSHA 1926.601 · Protección OSHA contra volcaduras · Manual del fabricante",
    action_items:
      "Revisión de firmeza del terreno discutida · Respuesta ante liberación dispareja revisada · Política de cinturón durante descarga reforzada · Línea de caída de spotter revisada",
  },
  dump_bed_wind_raised: {
    title: "Operación con Caja Arriba en Viento Fuerte",
    incident_pattern:
      "Una caja volcadora levantada es una vela. A 30 mph de viento sostenido, una caja vacía levantada atrapa suficiente fuerza para empujar el camión de lado o acelerar una volcadura que ya iba marginal. Los peores incidentes pasan cuando las cuadrillas tienen prisa por terminar antes de que llegue un frente — caja arriba, ráfaga golpea, camión en tres ruedas antes de que el chofer reaccione. El patrón se repite más en sitios expuestos: losas de puente, terraplenes, taludes, patios de planta con exposición al viento predominante.",
    hazards_reviewed:
      "Volcadura inducida por viento con caja arriba · Carga lateral por viento sostenido · Carga repentina de ráfaga · Cuadrilla golpeada por volcadura sin control · Liberación de material por viento",
    discussion_notes:
      "• Si los vientos sostenidos pasan de 25–30 mph, considere si la descarga puede esperar. Cajas vacías levantadas a velocidad con viento lateral han volteado camiones.\n• Las ráfagas son peores que el viento sostenido — una ráfaga de 50 mph contra una caja levantada son varios miles de libras de carga lateral instantánea.\n• Posicione el camión para que la caja suba HACIA el viento, no atravesada. Reduce el efecto vela.\n• Vigile el cielo y el radar. Frentes que entran rápido (líneas de tormenta, tormentas de verano) traen ráfagas de 50–70 mph antes de la lluvia.\n• Si una ráfaga golpea con la caja arriba: mantenga los controles firmes. NO haga movimientos bruscos. La mayoría de las volcaduras por viento se agravan con dirección de pánico.\n• En sitios expuestos — losas de puente, terraplenes, patios de planta con exposición abierta — fije un umbral de viento para la cuadrilla y llámelo antes de que se ponga feo.",
    references_cited:
      "OSHA 1926.601 · Límites de operación del fabricante en viento · Concientización NWS sobre frentes de ráfaga",
    action_items:
      "Umbral de viento de la cuadrilla discutido · Orientación caja-hacia-viento revisada · Responsable de vigilancia del clima asignado",
  },

  // ============================================================
  // TRUCKING / FLEET · FASE C EXPANSIÓN · iter251
  // ------------------------------------------------------------
  // 6 temas adicionales para choferes, dispatchers y líderes de
  // patio. Misma voz de patrón-real. Plain-spoken. Field-facing.
  // ============================================================
  trucking_backing_struck_by: {
    title: "Accidentes al Retroceder — Uso de Spotter y los Últimos 10 Pies",
    incident_pattern:
      "Los incidentes al retroceder son el tipo más común de accidente de camión en obra civil pesada — y casi cada fatalidad ocurre en los últimos 10 pies de la maniobra. El chofer ya pasó el giro amplio, va arrastrándose para posicionarse, y deja de checar espejos con la atención que debería. Un peón se mete atrás a recoger una herramienta. Un cucharón se deja donde el chofer no lo ve. Un spotter sale del marco visual para tomar una llamada. El camión toca algo — una persona, un equipo, una pared — a 1 o 3 mph. Eso es suficiente para matar a alguien, destruir una pickup, o arrancar una pierna.",
    hazards_reviewed:
      "Golpe / atropello a trabajadores en tierra · Aplastamiento contra equipo adyacente · Daño a propiedad en la pila / plataforma de carga · Spotter golpeado mientras señaliza · Trabajador peatón en el lado ciego",
    discussion_notes:
      "• Use un spotter siempre que retroceda en área congestionada, alrededor de personal, o en cualquier muelle / pila / báscula donde no vea con claridad su trayecto.\n• G-O-A-L: Get Out And Look · Bájese, Camine y Mire. Antes de retroceder a un espacio estrecho, bájese, camine el trayecto, mire arriba y abajo. Luego retroceda.\n• Acuerde las señales de mano ANTES de retroceder — el spotter debe conocer SUS señales y USTED debe conocer cómo se ve su señal de alto.\n• Si pierde de vista al spotter por CUALQUIER razón — pare. No adivine. No siga rodando. Espere hasta verlo de nuevo.\n• Use el claxon — un toque antes de moverse, dos toques para reversa. Despierta a cualquiera en el área antes de que las ruedas se muevan.\n• Los últimos 10 pies es cuando se reduce la velocidad, no cuando se acelera para terminar. Ahí es donde ocurre el golpe.\n• Spotters: manténganse fuera del radio de giro y de la línea de atropello. Nunca paren directamente detrás de las ruedas. Manténganse donde el chofer pueda VERLOS en el espejo.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.602 · SOP de retroceso FMCSA · Tarjeta de Spotter MASCI",
    action_items:
      "Hábito G-O-A-L discutido · Señales de mano de spotter revisadas · Regla de pérdida-de-vista reforzada · Reducción de velocidad en los últimos 10 pies reforzada",
  },
  trucking_shoulder_pulloff_struck_by: {
    title: "Estacionamiento en el Acotamiento y Posicionamiento en el Hombro",
    incident_pattern:
      "La mayoría de las fatalidades de choferes profesionales por ser golpeados no suceden en tránsito — suceden después de que el camión ya está parado en el acotamiento. El chofer se hace a un lado para revisar una llanta, ajustar la carga, una llamada, o un problema mecánico. Se baja, camina alrededor de la cabina, y un automovilista que se desvió al acotamiento lo golpea. La combinación de un acotamiento iluminado, un automovilista distraído con el celular, y un chofer con uniforme oscuro hace este patrón terrible y predecible. Pasa más de noche que de día, y en carreteras rurales de dos carriles más que en autopistas.",
    hazards_reviewed:
      "Golpeado por automovilista en el acotamiento · Puerta del lado del chofer abre hacia tráfico vivo · Escombros de llanta reventada de vehículo en marcha · Atrapado entre camión y barrera · Caída desde la cabina al acotamiento suelto",
    discussion_notes:
      "• Hágase a un lado lo más a la derecha que el acotamiento permita. Si el acotamiento es estrecho, busque la siguiente salida, marcador de milla o lugar amplio — no pare en un acotamiento de 6 pies si puede evitarlo.\n• Intermitentes desde el momento que para. Triángulos o bengalas conforme FMCSA (10 pies atrás · 100 pies atrás · 100 pies adelante dentro de 10 minutos). En carretera dividida, los tres atrás.\n• Salga por el lado del PASAJERO siempre que sea posible. Nunca salga de la cabina hacia un carril vivo.\n• Chaleco reflectivo PUESTO antes de abrir la puerta — Tipo II Clase 2 mínimo, Tipo III Clase 3 de noche. Chaleco en la cabina, no debajo del asiento.\n• De noche: luz de domo encendida, intermitentes de 4 puestos, faros ajustados para no encandilar al tráfico. No pare entre su camión y los faros que vienen — los choferes literalmente no pueden verlo en esa silueta.\n• Llamada telefónica, papeleo, GPS, comida — ninguno vale la pena hacerlo en el acotamiento. Tome la próxima salida.\n• Si una llanta reventó y tiene que estar cerca del rin — párese del lado de la BARRERA, nunca del lado del tráfico. Una segunda reventada lanza escombros muy lejos.",
    references_cited:
      "FMCSA 49 CFR 392.22 (dispositivos de aviso) · FMCSA 392.71 · OSHA 1926.201 · ANSI/ISEA 107 (PPE)",
    action_items:
      "Preferencia de posición en acotamiento reforzada · Colocación de triángulos / bengalas revisada · Hábito de salida por lado pasajero discutido · Regla de chaleco-en-la-puerta reforzada",
  },
  trucking_tarp_load_securement: {
    title: "Lona y Aseguramiento de Carga en la Carretera",
    incident_pattern:
      "Los incidentes de pérdida de carga y pérdida de lona siguen un patrón apretado: el chofer hace una revisión cuidadosa en el patio, luego corre las primeras 5–10 millas en camino lento. Una vez que pega la carretera y la carga de viento sube, cualquier cosa que no quedó bien apretada empieza a moverse. Una lona suelta se levanta, suelta una cincha, y se convierte en paracaídas para el siguiente vehículo o libera material a través de dos carriles. Agregado, millings de asfalto, escombros de demolición — una vez que un pedazo le pega a un carro a 70 mph es un pleito legal en el mejor caso y una fatalidad en el peor. La mayoría de estas fallas se rastrean a una sola cincha saltada o un clip de lona que ya estaba agrietado.",
    hazards_reviewed:
      "Material liberado hacia tráfico vivo · Lona arrancada — golpe al parabrisas de vehículo trasero · Desplazamiento de carga causando volcadura o salida de carril · Falla de cincha por roce o daño previo · Material de retorno en la caja liberándose con los baches",
    discussion_notes:
      "• Pre-trip la carga Y la lona. Camine los cuatro lados. Mire cada cincha, cada tensor, cada clip. Reemplace cualquier cosa agrietada, deshilachada o desgastada — no espere a que falle en la carretera.\n• La cobertura con lona es requerida para cualquier acarreo que pueda perder material — agregado, millings, tierra, arena, demolición. Las cajas 'vacías' aún guardan polvo y escombros pequeños que vuelan a velocidad.\n• Patrón de cinchas: conforme FMCSA, mínimo una sujeción para los primeros 5 pies de carga y otra cada 10 pies después. Cargas pesadas / asimétricas requieren más, no menos.\n• Re-revise en la primera parada. Las primeras 5–10 millas de carretera son donde todo se asienta. Hágase a un lado (legalmente), camine, vuelva a apretar lo que se aflojó.\n• Clips de lona y amarres de esquina — son el punto de falla más común. Inspecciónelos como si importaran. Sí importan.\n• Si pierde una lona a velocidad: hágase a un lado de manera segura, intermitentes, NO persiga la lona a pie hacia el tráfico. Llame al dispatch. Llame a la patrulla. Pida respaldo antes de recuperar.\n• Tip de retorno: un camión 'limpio' no está limpio. Barra la caja y revise las esquinas antes de salir de la pila de descarga. Un puñado de millings a 70 mph es un golpe al parabrisas.",
    references_cited:
      "FMCSA 49 CFR 393 Subparte I (aseguramiento de carga) · Manual del Chofer FMCSA · Inspección de Lona NACS · SOP de Lona MASCI",
    action_items:
      "Pre-trip de lona y cinchas discutido · Hábito de re-revisión en primera parada reforzado · Barrido de retorno reforzado · Umbral de reemplazo de clip de lona revisado",
  },
  trucking_kingpin_coupling_failure: {
    title: "Fallas de Kingpin y Acoplamiento del Trailer",
    incident_pattern:
      "Las caídas de trailer siguen una secuencia reconocible: el chofer acopla con prisa — solo inspección visual, sin tug-test, las mordazas se ven cerradas, el pasador de seguridad se mira por encima. Los primeros 100 pies de movimiento van bien porque el trailer está sentado sobre la quinta rueda por gravedad. Luego un leve declive, un bache, un giro, y el kingpin se desliza fuera de mordazas que no sellaron. El trailer cae sobre la placa de cubierta o sobre el pavimento. Si alguien está entre la cabina y el trailer en ese momento — un trabajador de patio, otro chofer haciendo walk-around, un mecánico — el resultado es catastrófico. El patrón es más viejo que la mayoría de los choferes al volante, y sigue matando gente cada año.",
    hazards_reviewed:
      "Caída de trailer / desacoplamiento accidental · Aplastamiento entre trailer caído y cabina · Colapso de patas de aterrizaje con carga que se desplaza · Falso bloqueo del kingpin · Desconexión de glad-hands y eléctrico en ruta",
    discussion_notes:
      "• La revisión de acoplamiento son TRES revisiones, no una: visual (mordazas cerradas sobre el kingpin) · seguro / pasador de bloqueo enganchado · TUG-TEST en marcha baja contra frenos del trailer.\n• Tug-test significa: frenos del trailer puestos, marcha baja, jalar suavemente hacia adelante. El pin agarra las mordazas. SIN movimiento = bien. CUALQUIER movimiento = re-acoplar inmediatamente.\n• Inspección visual: métase BAJO la quinta rueda con una linterna. Quiere VER las mordazas cerradas alrededor del kingpin, no solo la palanca de bloqueo 'adentro.' Las palancas pueden estar 'adentro' en un falso bloqueo.\n• Patas de aterrizaje totalmente arriba y manivela guardada. Una pata aunque sea ligeramente abajo puede engancharse en pavimento rugoso y arrancarse.\n• Glad-hands asentadas · cadenas o aparejo de seguridad donde se requieran · pigtail eléctrico enganchado. Estos son ítems de walk-around, no de 'reviso después del almuerzo.'\n• Nunca se pare entre la cabina y el trailer durante acoplamiento / desacoplamiento. Comuníquese con cualquiera en el área — asegúrese que estén despejados. Las fatalidades en patio casi siempre involucran a una persona en este espacio.\n• Si siente algo raro en la carretera — vibración, golpe seco, movimiento súbito — hágase a un lado YA. No siga otras cinco millas a la próxima salida. Los desacoplamientos han ocurrido en autopista.",
    references_cited:
      "FMCSA 49 CFR 393.70 (dispositivos de acoplamiento) · Criterios OOS de CVSA · Manual OEM de quinta rueda · Tarjeta de Acoplamiento MASCI",
    action_items:
      "Revisión de acoplamiento de tres pasos reforzada · Método de tug-test revisado · Hábito visual bajo el trailer reforzado · Regla de mantenerse-fuera-de-la-zona-pinch discutida",
  },
  trucking_overweight_axle_law: {
    title: "Sobrepeso, Carga por Eje y Ley de Puentes",
    incident_pattern:
      "Las multas por sobrepeso y violaciones de eje casi nunca vienen de un chofer que DECIDIÓ correr pesado. Vienen de un chofer al que el operador de planta le cargó, no revisó el ticket, no se pesó al salir, y pasó frente a un equipo portátil de pesaje. El patrón se repite más en dos escenarios: hot-mix saliendo de planta ocupada donde los operadores de loader llevan días largos y sobre-cargan 'un poquito,' y acarreos de agregado donde el cliente paga por tonelada y el proveedor carga al ras. El chofer come la multa, la compañía come los puntos en su DOT score, y una violación de Bridge Law a nivel estatal puede detener un trabajo.",
    hazards_reviewed:
      "Pérdida de frenos / fuego de frenos en bajadas por sobrecarga · Reventón de llanta por sobrecarga de eje · Daño estructural a puente / alcantarilla · Puntos DOT en autorización operativa · Citaciones que afectan la licencia · Pérdida de dirección por sobrecarga del eje delantero",
    discussion_notes:
      "• Conozca la tara de su camión, las clasificaciones de eje y el bruto. Téngalo escrito en la cabina — no en su cabeza, no 'aproximado,' sino exacto.\n• Revise el ticket en la planta ANTES de salir de la báscula. Si los números no cuadran o el camión se siente pesado en la suspensión, pídale al loader que quite una pala.\n• La ley federal de puentes no es solo peso bruto — es cómo se distribuye el peso. Un camión legal en bruto puede ser ilegal en el tándem o en el eje delantero. Distribuya cargas, deslice la quinta rueda, deslice el eje del trailer.\n• Si pasa por una báscula CAT o una portátil estatal en la ruta, ÚSELA. Mejor saber que va 800 lb arriba y deslizar el eje, que descubrirlo en el chicken coop.\n• Sobrecarga en el eje de dirección es la más peligrosa — ahí vive la autoridad de dirección. Un eje de dirección sobrecargado en una curva puede irse de largo y volverse volcadura.\n• Hot mix de planta: la temperatura afecta cómo se asienta la carga. Una báscula perfecta en la planta puede correrse en la carretera. Maneje en consecuencia — frenado más suave, mayor distancia de seguimiento.\n• Tip de dispatch: si un cliente pide consistentemente acarreos sobre eje, documéntelo y escálelo. No deje que se vuelva 'así corremos a ese cliente.'",
    references_cited:
      "FMCSA 49 CFR 393 · Fórmula Federal de Puentes (23 USC 127) · Tablas de eje del DOT estatal · SOP de Carga en Planta MASCI",
    action_items:
      "Tara / clasificación / bruto verificados en cabina · Hábito de báscula-de-salida reforzado · Conciencia del eje de dirección discutida · Ruta de escalación de sobrecarga discutida",
  },
  trucking_blind_spots_pedestrian: {
    title: "Puntos Ciegos y Trabajadores Peatones Alrededor de Camiones",
    incident_pattern:
      "Las fatalidades por golpe a peatón en obras de civil pesada casi siempre ocurren en una zona específica — el cuarto delantero del lado pasajero, o el área inmediata frente a la cabina — y casi siempre pasan durante los primeros 2 segundos de movimiento del vehículo. Un peón está revisando una llanta, levantando una herramienta, señalando a otro equipo, o simplemente parado en el lugar equivocado. El chofer mira los espejos, no ve nada, y arranca. El camión avanza 5 a 10 pies antes de que el chofer vea un chaleco hi-vis caer al suelo. El arreglo no son mejores espejos — es un hábito fuerte de pre-movimiento y una cultura de sitio donde los trabajadores de tierra saben no pararse en esas zonas.",
    hazards_reviewed:
      "Peatón golpeado / atropellado desde el punto ciego de la cabina · Brecha del espejo lateral derecho en cabinas anchas · Peatón detrás del camión durante reversa · Trabajador en zona de pinch durante un giro · Falta de familiaridad de chofer nuevo con cobertura de espejos",
    discussion_notes:
      "• Antes de cualquier movimiento — el chofer hace un walk-around de 360 o un barrido completo de espejos + por encima del hombro. Contacto visual con cualquiera que sea visible.\n• Use el claxon. Un toque antes del movimiento adelante, dos toques para reversa. Si alguien está cerca, baje el vidrio y avise antes de moverse.\n• Los puntos ciegos: directamente al frente del bumper (la 'zona de muerte'), el cuarto delantero derecho, el área inmediatamente detrás del trailer, y la zona de pinch al girar a la derecha. Los trabajadores en tierra NUNCA deben pararse ahí.\n• El chaleco hi-vis es una herramienta, no un permiso. Un chaleco no le permite pararse en un punto ciego.\n• En sitio ocupado — patios de planta, trenes de pavimento, pilas de descarga — haga contacto visual con el chofer antes de caminar cerca del camión. Si no recibe reconocimiento, no entre a la zona.\n• Choferes nuevos: tomen 15 minutos con cada camión y SEPAN qué cubre cada espejo y qué no. Los espejos del lado derecho en cabinas día vs sleeper vs cab-over son diferentes — no asuman.\n• Supervisores de sitio y personal de oficina visitando el campo: misma regla. Manténganse fuera de los puntos ciegos de la cabina, especialmente alrededor de equipo en marcha.\n• Si usted es el spotter o trabajador en tierra, póngase donde el CHOFER pueda VERLO a USTED en el espejo — no donde usted pueda ver el camión. Son cosas diferentes.",
    references_cited:
      "OSHA 1926.601 · OSHA 1926.602 · Control Interno de Tráfico NIOSH · SOP de Peatones en Sitio MASCI",
    action_items:
      "Hábito de walk-around pre-movimiento reforzado · Conciencia de zona-de-muerte para cuadrilla en tierra revisada · Revisión de cobertura de espejos para chofer nuevo asignada · Regla de punto-ciego para visitantes de oficina discutida",
  },

  // ============================================================
  // DESAGÜE / WELLPOINT · FASE D · iter251
  // ------------------------------------------------------------
  // Lecciones operativas de riesgo catastrófico para cuadrillas
  // de desagüe. Voz de superintendente con experiencia.
  // ============================================================
  dewatering_jetting_rig_overhead_strike: {
    title: "Golpes de Equipo Jet a Líneas Eléctricas Aéreas",
    incident_pattern:
      "Los contactos con líneas eléctricas en equipos jet casi nunca pasan durante el jetting constante — pasan durante el reposicionamiento. El equipo está puesto, el operador termina un header, y ahora necesita moverse al siguiente stab. Retrae un poco, gira el brazo, y el mástil — usualmente totalmente extendido del último header — barre hacia la línea aérea. El operador está enfocado en la cuadrilla y el siguiente stab, no en lo que está 30 pies arriba. Alrededor de patios de servicio, detrás de tiendas, en la parte trasera de estaciones de bombeo — las líneas aéreas están en todas partes y los mástiles en equipos jet son suficientemente altos para encontrarlas.",
    hazards_reviewed:
      "Electrocución del operador o cuadrilla en tierra · Contacto del mástil con línea energizada durante reposicionamiento · Potencial de paso alrededor del equipo energizado · Corte de servicio / incendio por daño a línea · Quemaduras por arco eléctrico",
    discussion_notes:
      "• Antes de bajar el equipo del trailer — camine el sitio. Mire arriba. Identifique CADA línea aérea dentro de 50 pies de cualquier lugar por donde el mástil viajará.\n• Distancia mínima 20 pies de líneas energizadas bajo OSHA 1926.1408. Si la línea es menor a 50 kV. Voltaje mayor = distancia mayor.\n• Baje el mástil ANTES de reposicionarse. Cada vez. Los 30 segundos que cuesta es el seguro más barato que comprará.\n• Asigne un spotter cuya ÚNICA tarea sea vigilar el mástil y las líneas durante cualquier reposicionamiento. No multitarea. No también señalar a la cuadrilla. Solo el mástil y las líneas.\n• Si no sabe si una línea está energizada, trátela como viva. Llame al servicio. Obtenga una desenergización confirmada y conexión a tierra ANTES de trabajar cerca.\n• Sucede contacto: QUÉDESE EN EL EQUIPO. Mantenga la cuadrilla atrás al menos un largo de equipo más la línea. Llame al 911 y al servicio. El potencial de paso ha matado más gente que el contacto inicial.\n• Si TIENE que salir: salte con los pies juntos. Nunca tenga dos partes del cuerpo en el suelo al mismo tiempo hasta estar a 30 pies de distancia.",
    references_cited:
      "OSHA 29 CFR 1926.1408 · OSHA 1926.416 · Distancias NESC · SOP de Equipo Jet MASCI",
    action_items:
      "Walk-around aéreo hecho · Hábito de mástil-abajo-antes-de-reposicionar reforzado · Spotter de mástil designado · Procedimiento de respuesta a contacto revisado",
  },
  dewatering_suction_line_entrapment: {
    title: "Atrapamiento y Engullimiento por Línea de Succión",
    incident_pattern:
      "El engullimiento por línea de succión es una de las fatalidades menos discutidas en desagüe, y una de las más prevenibles. Un header de wellpoint se tapa, el operador jala un stinger para revisar la criba, y el agua corre por la línea abierta. Cualquiera dentro de unos pies — botas en el fondo de la zanja, mano alcanzando la criba, arrodillado junto a la línea — puede ser jalado a la succión por acción hidráulica. Aun una succión de 6 pulgadas a vacío total sostendrá una mano o una bota al inlet con tanta fuerza que el trabajador no puede liberarse. Varias fatalidades documentadas en nuestra región se rastrean a una sola acción de 'nomás voy a revisar la criba.'",
    hazards_reviewed:
      "Mano o brazo jalado al inlet de succión · Engullimiento en zanja wellpoint colapsada · Ahogamiento en sump sin criba · Lesión por latigazo de manguera · Pellizco / amputación en strainer",
    discussion_notes:
      "• Vacío APAGADO antes de que alguien toque línea de succión, header, stinger, criba o strainer. Punto. Sin excepciones. Sin 'voy a ser rápido.'\n• Lockout de la bomba en los controles Y verificar cero presión en el manómetro antes de que alguien se acerque al inlet.\n• Si debe trabajar cerca de una línea con flujo, use herramienta de mango largo. Nunca meta una mano o brazo en la zona de succión.\n• Las cribas previenen atrapamiento Y previenen fallas de criba — inspecciónelas diariamente, reemplace cualquier agrietada o desgastada.\n• Zanjas de wellpoint deben estar bien apuntaladas o con talud. El riesgo de engullimiento es real si la pared falla mientras alguien está al fondo dando servicio a un header.\n• Pozos sump con inlets de succión abiertos necesitan barreras o rejillas. Un niño, un trabajador, un perro — cualquier cosa que caiga ahí está en problemas inmediatos.\n• Capacite a cuadrilla nueva sobre física de succión — explique por qué una manguera de 6 pulgadas a 25 inHg no soltará una mano. Hágalo real, no teórico.",
    references_cited:
      "OSHA 29 CFR 1926 Subparte P · OSHA 1910.147 (LOTO) · Manual del fabricante de la bomba · SOP de Desagüe MASCI",
    action_items:
      "Regla de vacío-apagado-antes-de-tocar reforzada · Lockout en controles de bomba verificado · Inspección de cribas asignada · Charla de física de succión para cuadrilla nueva programada",
  },
  dewatering_diesel_pump_fueling_fires: {
    title: "Incendios al Recargar Bombas Diésel",
    incident_pattern:
      "Los incendios de bomba diésel casi nunca pasan en la gasolinera — pasan en sitio durante la recarga de equipo corriendo o recién apagado. La bomba ha corrido 12 horas, el mofle y el turbo están a 800–1000°F, el operador tiene prisa por recargar antes de la siguiente tormenta, y un salpicón de combustible toca metal caliente. El fuego es instantáneo y amenaza de inmediato al operador parado a 18 pulgadas del tubo de llenado. La mayoría de estos fuegos se convierten en quemaduras, no fatalidades — pero arruinan la vida del trabajador y paran un trabajo. El patrón se previene con una disciplina simple: tiempo de enfriamiento y recarga limpia.",
    hazards_reviewed:
      "Salpicón de combustible sobre escape / turbo caliente · Ignición por descarga estática durante transferencia · Derrame creando riesgo de resbalón + incendio · Quemadura al que recarga · Pérdida del equipo · Liberación ambiental",
    discussion_notes:
      "• Apague la bomba ANTES de recargar. Permita 5–10 minutos de enfriamiento si el motor ha corrido fuerte. El múltiple de escape y el turbo siguen calientes mucho después del apagado.\n• No fumar · sin llamadas de celular · sin llamas abiertas dentro de 25 pies del punto de recarga. Esto no es opcional.\n• Mantenga el bonding entre el contenedor o manguera y el chasis de la bomba durante transferencia. La estática es una fuente real de ignición.\n• No llene de más. La expansión cuando el combustible se calienta puede empujar combustible por el venteo sobre el motor.\n• Transferir combustible de noche con linterna — no con una lámpara de trabajo caliente apoyada en la bomba. Las luces se calientan.\n• Kit de derrames en cada sitio de desagüe. Almohadillas absorbentes, calcetín, tapete de drenaje. El tapete va DEBAJO del punto de llenado cada vez.\n• Si arranca un fuego: extintor ABC al alcance (dentro de 10 pies del punto de recarga). Saque al operador PRIMERO. Luego combata el fuego. Nunca combata un fuego solo.\n• Sumergibles eléctricos: GFCI en cada bomba eléctrica, cables inspeccionados diariamente por daño, bonding + conexión a tierra verificados en el chasis. Un sello que falla convierte toda la zanja en peligro de descarga para cualquiera trabajando en el agua.",
    references_cited:
      "NFPA 30 · OSHA 1926.152 · EPA SPCC · DOT 49 CFR 173 · SOP de Recarga MASCI",
    action_items:
      "Hábito de enfriamiento-antes-de-recargar discutido · Extintor dentro de 10 ft verificado · Kit de derrames + tapete en cada bomba · Bonding-durante-transferencia revisado",
  },
  dewatering_wellpoint_trench_collapse: {
    title: "Colapso de Zanja Wellpoint Alrededor de Headers",
    incident_pattern:
      "Los colapsos de zanja wellpoint siguen un patrón apretado: la zanja se cava a profundidad moderada (4–8 pies), se pone el header, se jetting los wellpoints. Tres días después de bombear, el suelo entre puntos ha sido jalado más apretado y las paredes lucen estables. Un trabajador baja a la zanja para dar servicio a un punto tapado o reparar una fuga. El desagüe en realidad ha cambiado la estructura del suelo — material saturado encima de una sección ya seca crea un plano de deslizamiento. La pared falla hacia adentro sin aviso. El trabajador, aun si vive, está enterrado al pecho en segundos. Zanjas antes estables no son estables para siempre cuando el contenido de agua cambia.",
    hazards_reviewed:
      "Enterramiento / asfixia por pared de zanja colapsada · Lesión por aplastamiento al fallar la pared · Ahogamiento en fondo de zanja por entrada súbita · Golpe por header / equipo cayendo · Hipotermia en enterramiento prolongado",
    discussion_notes:
      "• La protección de zanja a 5 pies+ no es opcional — talud, banco, apuntalamiento o trench box. El desagüe NO reemplaza el apuntalamiento.\n• Zanjas mayores a 4 pies necesitan escalera o rampa dentro de 25 pies de cualquier trabajador.\n• Reclasifique el suelo después de que el desagüe ha estado corriendo. Las transiciones saturado-a-seco crean capas inestables. Hable con su persona competente.\n• Pila de spoil al menos a 2 pies del borde. Trayectos de equipo al menos a una profundidad-de-zanja atrás. La vibración de bombas corriendo afloja material del borde durante horas.\n• Dé servicio a un wellpoint desde ARRIBA de la zanja siempre que sea posible. El riesgo de estar en la zanja para arreglar un punto no vale el tiempo ahorrado.\n• Nunca trabaje solo en una zanja wellpoint. Los primeros 60 segundos después de un colapso es cuando ocurre la supervivencia — solo si alguien arriba lo ve.\n• Inspección diaria por persona competente — y después de cualquier lluvia, congelación-deshielo o evento de vibración.",
    references_cited:
      "OSHA 29 CFR 1926 Subparte P · OSHA 1926.651 · OSHA 1926.652 · SOP de Zanja de Desagüe MASCI",
    action_items:
      "Protección de zanja revisada para profundidad actual · Reclasificación de suelo hecha después de iniciar bombeo · Hábito de servicio sobre-zanja reforzado · Inspección diaria de persona competente asignada",
  },
  dewatering_rotating_shaft_belt: {
    title: "Enredamiento en Eje Rotatorio y Banda",
    incident_pattern:
      "Las lesiones por enredamiento en banda y eje en bombas de desagüe usualmente pasan cuando una guarda está fuera por una tarea de servicio y alguien que no sabía que un compañero estaba trabajando golpea o vuelve a arrancar el motor. Un guante, una manga, un faldón de camisa, un cordón de capucha agarra una banda en V o un cople. El motor de la bomba va a 1800 RPM en el cople — el brazo entero está adentro antes de que el trabajador reaccione. Sudaderas, mangas sueltas y puños desabrochados son el factor principal en casi cada incidente documentado. El segundo factor es falta de LOTO cuando una guarda está fuera.",
    hazards_reviewed:
      "Brazo / mano jalado a banda en V o cople · Aplastamiento / amputación por eje rotatorio · Muerte por ropa atrapada en PTO · Quemadura por fricción de banda · Lesión ocular por falla de banda",
    discussion_notes:
      "• Guardas puestas CUALQUIER vez que el motor corre. Sin excepciones. Si la guarda está rota, la bomba no corre hasta que se arregle.\n• Lockout del motor en el interruptor Y quitar la llave antes de que cualquier guarda salga. Verifique con intento de arranque antes de meter la mano.\n• Mangas abrochadas · camisas fajadas · SIN cordones de capucha · SIN joyas sueltas cerca de equipo rotatorio.\n• Solo guantes ajustados — y considere guantes FUERA al trabajar cerca de ejes rotatorios. Dedos sueltos de guante agarran bandas.\n• Capacite a operadores nuevos para identificar CADA punto de pellizco en la bomba antes de tocarla corriendo. Camínenlo. Apunten a cada uno.\n• Servicio de banda es servicio con motor APAGADO. Tensión, alineación, reemplazo — todo motor-apagado, con la llave en su bolsillo.\n• Si una guarda está fuera por inspección — asigne una persona como dueño del candado. Su llave se queda en su bolsillo. Nadie más puede arrancar.",
    references_cited:
      "OSHA 29 CFR 1910.147 (LOTO) · OSHA 1910.219 · ANSI B11 · Manual del fabricante de la bomba",
    action_items:
      "Regla de guardas-puestas reforzada · LOTO antes de quitar guarda verificado · Estándares de ropa (sin cordones) discutidos · Recorrido de puntos de pellizco para operador nuevo asignado",
  },
  dewatering_discharge_hose_whip: {
    title: "Latigazo de Manguera de Descarga y Liberación de Presión",
    incident_pattern:
      "Los incidentes de latigazo de manguera de descarga pasan porque una conexión falla o una sección se suelta bajo presión. Una manguera de descarga de 6 u 8 pulgadas a 60–80 psi carga energía almacenada enorme. Cuando un cople se suelta, el extremo de la manguera se vuelve un látigo — moviéndose lo suficientemente rápido para romper huesos, lanzar trabajadores o tirar a alguien del talud de una zanja. El patrón usualmente es un cam-lock o quick-connect desgastado, un pasador o clip de seguridad faltante, o una manguera que no estaba restringida donde debía. El látigo viaja por el camino de menor resistencia — usualmente hacia quien esté más cerca.",
    hazards_reviewed:
      "Latigazo de manguera a cabeza / pecho · Liberación de presión tirando trabajador a la zanja · Lesión por resbalón por liberación súbita de agua · Proyectil por falla de cople · Quemaduras por descarga caliente (bombas de aceite caliente)",
    discussion_notes:
      "• Inspeccione cada cam-lock y cople en cada turno. Busque levas desgastadas, clips de seguridad faltantes, empaques deformados. Reemplace cualquier cosa dudosa.\n• Pasadores / clips de seguridad en cada cople. No son opcionales. Son lo que mantiene la manguera conectada cuando una leva se fatiga.\n• Restrinja las mangueras de descarga donde cambian de dirección, donde cruzan un trayecto, donde pasan por un talud. Use amarres de cuerda, sacos de arena, o restricciones apropiadas — no piedras apiladas.\n• Al presurizar una línea, nadie se para en línea con la manguera. Todos se hacen fuera-de-eje ANTES de que la bomba arranque.\n• Si una manguera se suelta: APAGUE LA BOMBA desde el lado de control primero. No intente agarrar la manguera. Los extremos de manguera pesan suficiente para romper una mano a 60 psi.\n• Whip-checks (cables de seguridad trenzados) en cada cople en corridas largas de descarga. Equipo estándar, no opcional.\n• Caminata diaria de toda la corrida de descarga — busque puntos de estrés, dobleces, abrasión, restricción expuesta, fugas. Atrape la falla ANTES del latigazo.",
    references_cited:
      "OSHA 29 CFR 1926.302 · ASME B31.3 · Capacidades de manguera / cople del fabricante · SOP de Descarga MASCI",
    action_items:
      "Inspección de coples asignada a cada turno · Pasadores de seguridad verificados en todos los coples · Whip-checks desplegados en corridas largas · Bomba-apagada-antes-de-tocar reforzada",
  },
  dewatering_spoil_edge_instability: {
    title: "Colocación de Spoil en Bordes de Zanja Wellpoint",
    incident_pattern:
      "La mayoría de fallas de borde en zanjas wellpoint no empiezan con la pared — empiezan con la pila de spoil. Spoil colocado muy cerca del borde añade carga de sobrepeso. Equipo corriendo paralelo a la zanja transmite vibración a través del spoil hacia la pared. Tres días de bombeo más la carga estática de una pila de spoil de 4 pies más la carga dinámica de un excavador pasando equivale a una sección de pared que se desliza a la zanja sin aviso. El trabajador dando servicio a un header al fondo nunca lo ve venir. El arreglo no es glamoroso y se conoce: mantenga el spoil atrás, mantenga el equipo atrás, inspeccione diariamente.",
    hazards_reviewed:
      "Colapso de zanja por sobrecarga de spoil · Engullimiento de trabajador en fondo de zanja · Deslizamiento de equipo a la zanja · Golpe por avalancha de spoil · Daño a manguera / header por pared colapsada",
    discussion_notes:
      "• Pila de spoil mínimo 2 pies del borde de la zanja. Para zanjas más profundas, empújela más — 1 profundidad-de-zanja atrás es el referente más seguro.\n• Sin trayectos de equipo dentro de una profundidad-de-zanja del borde. Excavadores, cargadores, dump trucks — todos atrás del filo.\n• Use plywood o placas de acero si debe cruzar o trabajar cerca del borde. Distribuye carga y reduce estrés local.\n• Equipo corriendo paralelo a una zanja wellpoint transmite vibración. La vibración afloja el suelo del borde. Mueva el trayecto del equipo o pare de correrlo por la duración.\n• Efecto compuesto: el bombeo jala agua de la pared. La pérdida de presión de poros hace que el suelo húmedo se asiente y el suelo seco se agriete. La pared que armó ayer no es la pared que tiene hoy.\n• Inspección diaria de persona competente del spoil y el borde, no solo el fondo de la zanja. El borde le dice el futuro.\n• Si ve CUALQUIER grieta de tensión, fisura o hundimiento en el borde — saque a los trabajadores YA. Re-inspeccione antes de dejar que alguien vuelva a entrar.",
    references_cited:
      "OSHA 29 CFR 1926.651(j) · OSHA 1926.652 Apéndice B · SOP de Borde de Zanja MASCI",
    action_items:
      "Setback de spoil verificado · Trayecto de equipo movido atrás · Inspección diaria de borde asignada · Respuesta a grieta de tensión revisada",
  },
  dewatering_night_work_struck_by: {
    title: "Visibilidad y Golpe-por en Trabajo Nocturno de Desagüe",
    incident_pattern:
      "El trabajo nocturno de desagüe es más peligroso que el de día por una razón específica: conos de visibilidad. Los operadores ven el área iluminada por sus luces de trabajo y asumen que todos los demás también. El chofer del camión entrando al sitio ve un halo de brillo y un campo negro más allá. El trabajador en tierra dando servicio a un header en la zona sin luz es invisible. La mayoría de los incidentes nocturnos de golpe-por en obras de desagüe pasan cuando un camión de entrega, un equipo de transferencia, o un vehículo de cliente entra a una zona iluminada y el chofer no ve a un trabajador afuera del cono iluminado. El patrón se repite porque la iluminación se instala para el TRABAJO, no para la visibilidad de los trabajadores.",
    hazards_reviewed:
      "Golpe-por de vehículo entrando al sitio de noche · Trabajador en zona sin luz invisible al chofer · Tropezón / caída en área sin luz · Contacto de equipo con obstrucciones mal iluminadas · Fatiga + tiempo de reacción reducido",
    discussion_notes:
      "• Ilumine el trabajo Y los trayectos de los trabajadores. Una sola torre de luz en la bomba no es suficiente. Ilumine las rutas entre el trailer, las bombas y la zanja.\n• Hi-vis reflectivo Clase 3 de noche — no Clase 2. Mangas, chaleco, pantalón. La cinta reflectiva es lo que lo hace visible en un haz de faros.\n• Cada trabajador tiene una luz personal — frontal o pectoral — que voltea hacia vehículos entrantes. El seguimiento de ojo del chofer va al movimiento de luz. Use eso.\n• Carril designado de entrada / salida para vehículos. Marcado con conos o barricadas. Ningún chofer entra libremente por un área de trabajo de desagüe de noche.\n• Chofer de cualquier vehículo entrante: pare en el borde del sitio. Haga contacto por radio o visual con el líder antes de entrar. NUNCA asuma que el área está libre.\n• La fatiga es real. Turnos de noche después de días largos producen tiempos de reacción como alcohol en sangre arriba del límite legal. Cuídense unos a otros. Forcen descansos. Manden gente a casa.\n• Clima severo de noche — llámelo antes de lo que lo haría de día. No puede ver lo que viene.",
    references_cited:
      "OSHA 29 CFR 1926.56 · ANSI/ISEA 107 (Clase 3) · MUTCD zonas de trabajo nocturno · SOP de Trabajo Nocturno MASCI",
    action_items:
      "Iluminación de trayectos de trabajadores revisada · Hi-vis Clase 3 requerida para turno noche · Luces personales distribuidas · Carril de entrada definido y marcado · Hora de check-in de fatiga fijada",
  },

  // ============================================================
  // TALLER / MECÁNICO · FASE E · iter251
  // ------------------------------------------------------------
  // Patrones de incidentes en piso de taller. Voz de mecánico
  // experimentado hablando con los más nuevos.
  // ============================================================
  shop_jack_stand_failure: {
    title: "Fallas de Caballetes — Fatalidades Bajo el Camión",
    incident_pattern:
      "Casi cada fatalidad de caballete sigue la misma secuencia: un mecánico levanta un camión o trailer pesado con el gato de piso, pone dos caballetes, se mete a empezar el trabajo, y el camión se mueve. A veces es porque los caballetes se pusieron en un miembro de chasis oxidado, a veces porque el piso tenía pendiente, a veces porque eran de capacidad menor a la carga. El camión no cae todo lo que puede — solo se asienta 2 pulgadas. Eso es suficiente para aplastar un pecho. No hay aviso. El mecánico está solo, frecuentemente al final del turno, y nadie lo encuentra por una hora. Hemos perdido mecánicos en esta industria a este patrón más veces de las que nadie quiere contar.",
    hazards_reviewed:
      "Aplastamiento fatal por caída de vehículo · Caballete hundiéndose en piso blando · Capacidad de caballete equivocada para la carga · Un solo caballete en vez de par · Trabajar solo bajo carga · Deslizamiento / falla de gato hidráulico",
    discussion_notes:
      "• Gato de piso es para LEVANTAR, nunca para SOSTENER. En el momento que la carga está arriba, caballetes de la capacidad de la carga van bajo PUNTOS DE LEVANTE APROPIADOS.\n• Caballetes con capacidad AL MENOS al peso de la carga, con margen. Un camión de 40,000 lb no va en caballetes de 6 toneladas. Lea la capacidad, haga las cuentas.\n• Ambos caballetes enganchados — no solo uno con el gato todavía debajo como segundo sostén. Un mango golpeado tira el camión.\n• Cuñas en las ruedas del EXTREMO OPUESTO. Trans en velocidad o parking. Freno de mano PUESTO. Cinturón y tirantes.\n• Coloque caballetes en el CHASIS, no en faldones de plástico, no en paneles de carrocería, no en estructura oxidada. Toque y mire antes de poner.\n• Solo piso de concreto. Puntos blandos de asfalto pueden fallar bajo un solo caballete. Si debe trabajar sobre asfalto, use una placa de acero para distribuir la carga.\n• Tug-test ANTES de meterse abajo. Empuje el camión, sacúdalo. Si algo se mueve más que la oscilación de la suspensión, rehaga el levante.\n• No trabaje solo bajo un vehículo. Si debe, fije una hora de check-in con alguien que lo busque si no contesta el mensaje.",
    references_cited:
      "OSHA 29 CFR 1910.244 · ANSI/PASE 5/MH29 (caballetes) · Manuales OEM de puntos de levante · SOP de Levante en Taller MASCI",
    action_items:
      "Mapa de puntos de levante para unidades comunes publicado · Verificación de capacidad de caballete asignada · Hábito de tug-test reforzado · Protocolo de check-in solo-bajo-vehículo fijado",
  },
  shop_lockout_tagout_bypass: {
    title: "Lockout / Tagout — El Bypass Que Mata",
    incident_pattern:
      "Las fallas de LOTO no matan al trabajador que puso el lockout — matan al trabajador que NO lo puso. El patrón: una pieza de equipo está en el taller para servicio hidráulico. El mecánico líder hace lockout correctamente. Un segundo mecánico, ayudando, no tiene su candado personal en él. Un tercer mecánico, terminando su turno, ve el equipo y decide 'nomás picar' los controles para revisar algo. El segundo mecánico, con la mano dentro del área del cilindro, queda aplastado. El candado del primer mecánico estaba correcto. El sistema falló porque no cada persona bajo el equipo tenía su propio candado.",
    hazards_reviewed:
      "Liberación de energía hidráulica almacenada · Aplastamiento por colapso de cilindro · Re-energización eléctrica durante servicio · Arranque de banda durante alineación · Liberación neumática de aire almacenado · Caída de contrapeso",
    discussion_notes:
      "• Un trabajador, un candado. CADA persona que tenga cualquier parte del cuerpo en o cerca de la zona de peligro pone SU PROPIO candado. Sin atajos de 'comparto candado.'\n• Etiquete el candado con quién lo puso y cuándo. Así el tercer mecánico que llega sabe de quién es este lockout y no lo quita.\n• Verifique energía cero: ciclar los controles, revisar los manómetros, bajar presión hidráulica a cero, drenar aire almacenado. CADA servicio.\n• Bloquee cilindros hidráulicos mecánicamente. Un soporte de cilindro, un bloque de madera, una cadena — algo que sostenga la carga si el sello falla.\n• No confíe en 'el jefe dijo que está bloqueado.' Verifique con sus propios ojos. Ponga su propio candado. Trate de arrancar.\n• Quitar un lockout: SOLO el trabajador que lo puso. Si no está en sitio, siga el procedimiento de retiro — usualmente requiere autorización del supervisor e intento documentado de localizar al dueño original.\n• Mecánicos nuevos: caminen un procedimiento LOTO con el líder el Día 1. Cada. Sola. Vez.",
    references_cited:
      "OSHA 29 CFR 1910.147 · Manuales de servicio OEM · Estándar LOTO de Taller MASCI",
    action_items:
      "Regla de un-trabajador-un-candado reforzada · Etiquetado de candado discutido · Verificación de energía cero revisada · Práctica de bloqueo de cilindro asignada · Recorrido LOTO para mecánico nuevo programado",
  },
  shop_brake_spring_energy: {
    title: "Liberación de Energía Almacenada en Resorte de Freno",
    incident_pattern:
      "Las liberaciones de cámara de freno han matado y cegado mecánicos por décadas, y siguen haciéndolo. El patrón es siempre el mismo: un mecánico reemplaza una cámara de freno o trabaja un ajustador de holgura en una unidad sin resorte enjaulado. Golpean un pasador atascado con martillo, o desatornillan una cámara que todavía sostiene la fuerza del resorte, y la cámara se desarma con la energía de una pequeña explosión. El resorte interno tiene capacidad de 2,000 lb de fuerza. Cuando eso se libera a seis pulgadas de una cara, es un impacto facial fatal. Enjaular el resorte no es opcional y nunca lo ha sido.",
    hazards_reviewed:
      "Proyectil de liberación de cámara de freno · Trauma facial / pectoral por componente de cámara · Pérdida de ojo por metralla de resorte · Daño auditivo por liberación · Pellizco durante enjaulamiento",
    discussion_notes:
      "• SIEMPRE enjaule el resorte antes de tocar un perno de servicio de cámara de freno, ajustador de holgura, o vástago. Las herramientas de enjaular son baratas. Los mecánicos nuevos cuestan más.\n• Use el puerto de enjaular de la cámara — deslice la herramienta, gírela 90°, jale apretado. Verifique que la jaula esté enganchada antes de quitar cualquier perno de servicio.\n• Párese al LADO durante la verificación de liberación. No al frente, no atrás — al lado. La trayectoria de liberación es derecho hacia afuera.\n• Protección ocular es no-negociable. No solo lentes de seguridad — careta completa sobre lentes para trabajo de freno.\n• Si no puede enjaular porque el puerto está oxidado, considere la unidad fuera-de-servicio para trabajo de taller. Corte la cámara como unidad y reemplácela con el resorte todavía enjaulado en la cámara VIEJA.\n• Tapones pop-off en el extremo del vástago — nunca los manipule. Son calificados para PRESIÓN, no para servicio.\n• Capacite a cada mecánico nuevo en instalación de jaula la primera semana. Hágalos hacerlo con una cámara en sus manos.",
    references_cited:
      "Servicio de Frenos FMCSA · Manuales OEM de cámara de freno · OSHA 1910.132 (PPE) · SOP de Taller de Frenos MASCI",
    action_items:
      "Inventario de herramienta de jaula verificado · Hábito de enjaular-antes-de-servicio reforzado · Requisito de careta revisado · Capacitación para mecánico nuevo programada",
  },
  shop_tire_cage_explosion: {
    title: "Explosiones de Jaula de Llanta y Rines de Múltiples Piezas",
    incident_pattern:
      "Los incidentes de jaula de llanta no son lo que la gente piensa. Las famosas fatalidades viejas — rines de múltiples piezas separándose durante inflado — siguen pasando porque algún equipo todavía corre en esos rines. Un rin de cargador, un rin de motoconformadora, un rin viejo de carretera. El mecánico desinfla, desmonta, vuelve a armar, infla sin jaula, y el anillo de cierre se separa a 80 psi. La energía es equivalente a una pequeña carga explosiva. Hay video. Todos lo hemos visto. El arreglo es más viejo que la mayoría de la gente en talleres hoy — y la gente sigue muriendo porque la jaula 'nada más por un segundo' se dejó a un lado.",
    hazards_reviewed:
      "Proyectil de separación de anillo de cierre durante inflado · Mecánico en línea de fuego · Falla de rin múltiple por corrosión · Agrietamiento de rin de una pieza · Recogida de manguera de inflado · Explosión de talón de llanta",
    discussion_notes:
      "• Jaula de llanta para CADA inflado, cada vez. Incluidos rines de una pieza — las fallas de talón pasan ahí también.\n• Párese al LADO durante el inflado. Nunca al frente del rin. Manguera de inflado larga con manómetro en línea para que esté afuera de la trayectoria.\n• Inspeccione rines ANTES de montar. Anillos de cierre, anillos laterales, canales — busque grietas, corrosión, deformación. Si el anillo no asienta limpio, el rin no vuelve a servicio.\n• Rines de múltiples piezas deben coincidir. Mezclar fabricantes o tamaños es lo que causa la mayoría de las separaciones. Si no está seguro que coincide, dispóngalo.\n• Infle en etapas. Asiente el talón a menor presión, verifique asentado, luego suba a presión de operación.\n• Lubricante de talón — solo agua y jabón. NUNCA use lubricantes con solvente. Pueden inflamarse bajo alta temperatura.\n• Los veteranos a veces saltan la jaula porque 'conocen' el rin. El rin no los conoce a ellos. Use la jaula.",
    references_cited:
      "OSHA 29 CFR 1910.177 · Manuales OEM de servicio de rin · Estándares de servicio de llanta TIA · SOP de Taller de Llantas MASCI",
    action_items:
      "Regla de jaula-cada-inflado reforzada · Paso de inspección de rin verificado · Política de lubricante de talón revisada · Política de rin de múltiples piezas discutida",
  },
  shop_welding_fire_watch: {
    title: "Fire Watch de Soldadura y Limpieza Post-Trabajo en Caliente",
    incident_pattern:
      "Los incendios de taller por soldadura casi nunca pasan durante la soldadura — pasan 20 a 60 minutos DESPUÉS. El soldador corta un soporte, esmerila el cordón, sopla la escoria, y se va. Una chispa que cayó en trapos aceitosos en una repisa, atrás de un tambo de 55 galones, o en cartón empaque arde lento. El taller está vacío para entonces. El detector de humo se dispara a la 1:30 a.m. y los bomberos llegan a un edificio totalmente envuelto. El arreglo es de décadas: limpieza, fire watch, inspección post-soldadura. Lo sabemos. Seguimos perdiendo edificios a fire watches saltadas.",
    hazards_reviewed:
      "Fuego de arder-lento en materiales aceitosos / con polvo · Fuego escondido tras / bajo equipo · Lesión por quemadura / humo · Incendio total del edificio · Ignición por chispa de líquido inflamable · Ignición de vapor durante corte",
    discussion_notes:
      "• Permiso de trabajo en caliente para cada trabajo de soldadura / corte / esmerilado. Hábito viejo, todavía correcto. El permiso nombra al soldador, la ubicación, el fire watch, y la hora de fin.\n• Despeje un radio de 35 pies antes de que vuelen chispas. Mueva trapos aceitosos, contenedores de combustible, cartón, aserrín, tambos de aceite hidráulico. TODO lo combustible.\n• Moje lo que no pueda mover. Cobijas de soldadura sobre lo que sí. Escudos de acero sobre aberturas a cuartos adyacentes.\n• El fire watch SE QUEDA por 30 minutos después de la última chispa. Teléfono en mano. Ojos en cada lugar donde pudo haber caído una chispa.\n• Revise ARRIBA y ABAJO de rejillas, en drenajes de piso, atrás de cualquier equipo dentro del radio de 35 ft. Las chispas viajan.\n• Extintor cargado al alcance del brazo durante Y después. Confirme que no es el vacío del último simulacro.\n• Último soldador al cierre de turno: camine todo el taller. Toque superficies, huela el aire. El humo y calor dicen lo que los ojos no.",
    references_cited:
      "NFPA 51B · OSHA 29 CFR 1910.252 · NFPA 241 · SOP de Permiso de Trabajo en Caliente MASCI",
    action_items:
      "Permisos de trabajo en caliente requeridos + publicados · Zona-libre de 35 ft aplicada · Duración del fire watch verificada · Caminata de fin de turno discutida",
  },
  shop_hydraulic_stored_energy: {
    title: "Energía Hidráulica Almacenada en Cilindros, Mangueras y Acumuladores",
    incident_pattern:
      "Las lesiones por inyección hidráulica se ven menores y matan gente. Un agujero pinhole en una manguera a 2,500 psi atomiza aceite a través de la piel como aguja hipodérmica. El mecánico ve un piquete diminuto en su mano, lo lava, lo venda, se va a casa. Dentro de 24 horas la mano está hinchada, el tejido se está muriendo por contaminación de aceite, y la sala de emergencias está amputando. Compuesto con la liberación de presión cruda de cilindro — un acople se afloja y el cilindro descarga a través del taller — y un acople se vuelve proyectil. La energía hidráulica almacenada es invisible. Mata mecánicos que no la respetan.",
    hazards_reviewed:
      "Lesión por inyección hidráulica a través de piel · Proyectil de acople / manguera · Extensión sin control de cilindro al liberar energía · Aplastamiento por caída de carga al despresurizar · Quemadura por aceite caliente · Lesión ocular por aceite atomizado",
    discussion_notes:
      "• Nunca busque una fuga hidráulica con la mano. Use cartón, papel o un pedazo de madera. Si encuentra una fuga, reemplace la manguera — no la parche.\n• Baje la presión a cero ANTES de desconectar cualquier acople. Cicle los controles con el motor apagado. Mire el manómetro. Verifique CERO.\n• Los acumuladores hidráulicos quedan presurizados DESPUÉS de cero en el manómetro del sistema. Descárguelos por el procedimiento OEM antes de tocar cualquier línea conectada.\n• Si aceite contacta piel bajo presión — ER YA. Aun si 'se ve como nada.' Dígales que fue inyección hidráulica. El reloj de cirugía empieza inmediato.\n• Herramientas de mango largo al trabajar cerca de una manguera presurizada. Párese fuera-de-eje al aflojar un acople.\n• Inspecciones de manguera semanales. Grietas, abrasión, bultos, fugas. Reemplace antes de la falla.\n• Protección ocular Y careta para cualquier trabajo hidráulico abierto. Sistema cerrado es regla distinta — sistema abierto es PPE completo.\n• Bloquee cilindros mecánicamente antes de trabajar en ellos. La presión hidráulica puede desaparecer y la carga puede caer si un sello falla.",
    references_cited:
      "OSHA 29 CFR 1910.147 · Seguridad de Fluid Power Society · Manuales de servicio OEM · SOP de Servicio Hidráulico MASCI",
    action_items:
      "Regla de buscar-pinhole-con-cartón discutida · Procedimiento de descarga de acumulador revisado · Política de ER-inmediato-para-inyección reforzada · Bloqueo de cilindro verificado",
  },
  shop_under_bed_crush_zone: {
    title: "Zonas de Aplastamiento Bajo Cajas, Brazos y Equipo",
    incident_pattern:
      "El pasador de body-prop en una caja volcadora existe por una razón: mantener vivos a los mecánicos cuando la caja baja inesperadamente. La mayoría de fatalidades bajo cajas pasan porque el prop se 'nomás por un minuto' dejó a un lado mientras el mecánico alcanzaba para liberar un pasador atorado o engrasar un pivote. Un sello hidráulico falla. Un interruptor de control se golpea. Una fuga que ha sido menor finalmente cede. La caja baja. El mecánico, manos arriba, queda atrapado entre caja y chasis. No hay escape de ese pellizco — se mide en fracciones de segundo, no segundos.",
    hazards_reviewed:
      "Aplastamiento entre caja y chasis en dump trucks · Aplastamiento bajo brazo en excavadores / grúas · Pellizco en rotación de contrapeso · Aplastamiento bajo attachment sin apoyo · Caída de cucharón / cuchilla con motor apagado",
    discussion_notes:
      "• Pasador de body-prop enganchado CUALQUIER vez que un mecánico esté bajo una caja levantada. No 'la mayoría del tiempo.' CADA vez. Aun por 30 segundos de engrase.\n• Brazo o pluma: BÁJELO HASTA EL FONDO antes de cualquier servicio. Si debe trabajar bajo uno levantado, bloquéelo con cribbing calificado para la carga.\n• Pasadores de stinger en stinger steer / tag-axles — póngalos adentro o afuera, no trabaje bajo ellos en posición media. El amortiguamiento hidráulico no sostendrá.\n• Rotación de contrapeso en excavadores — despeje el radio de giro antes de servicio. Aun con motor apagado, los hidráulicos pueden deslizar.\n• Cucharón / cuchilla — baje al suelo o bloquee antes de servicio. Las fallas de sello hidráulico tiran cargas. Los bloques mecánicos no.\n• Comuníquense en cambio de turno. El mecánico nuevo que toma un trabajo necesita saber qué está bloqueado, qué está pasador, qué está presurizado.\n• Si un body prop no engancha limpio, el camión no entra a trabajo. Arregle el prop primero.",
    references_cited:
      "OSHA 29 CFR 1910.147 · Manuales OEM de body prop · Estándares ANSI / SAE de bloqueo · SOP de Taller MASCI",
    action_items:
      "Regla de pasador-de-prop-siempre reforzada · Inventario de cribbing verificado · Zona-libre de contrapeso revisada · Comunicación de cambio de turno discutida",
  },
  shop_battery_explosion: {
    title: "Carga, Boost y Explosión de Hidrógeno de Batería",
    incident_pattern:
      "Las explosiones de batería se ven como efecto de película y pasan en la vida real. Un mecánico está dando boost a un camión muerto, la batería muerta ha estado descargada por semanas, y las celdas han desgasificado hidrógeno al gabinete. La pinza de boost arquea al borne, la chispa enciende el hidrógeno, y el gabinete revienta. Ácido y fragmentos de plástico vuelan en cada dirección — a la cara, ojos, brazos del mecánico. Las lesiones son a veces cegadoras y siempre con quemaduras. El arreglo es más viejo que el camión: conecte último a tierra, no a la batería, y revise abultamiento de gabinete o desgasificación antes de tocarla.",
    hazards_reviewed:
      "Explosión de hidrógeno durante boost / carga · Quemadura por ácido en ojos / piel · Salpicón de ácido por gabinete agrietado · Arco / fuego de cable de boost · Ruptura de gabinete por corto interno · Lesión por levantar baterías comerciales pesadas",
    discussion_notes:
      "• Mire la batería ANTES de conectar. Gabinete abultado = FUERA DE SERVICIO. Reemplace, no boostee.\n• Secuencia de conexión de boost: rojo-positivo a positivo-muerto · rojo-positivo a positivo-vivo · negro-negativo a negativo-vivo · negro-negativo a TIERRA DE VEHÍCULO MUERTO (chasis), NO al borne de batería muerta.\n• Esa última conexión es donde sucede el arco. Ponerlo en una tierra de chasis mantiene el arco LEJOS del hidrógeno en las celdas.\n• Protección ocular puesta. El ácido no es sobrevivible en los ojos sin enjuague inmediato — 15+ minutos en la estación de lavaojos.\n• Ventilación durante carga. Abra el cofre. No cargue un camión sellado en una bahía cerrada sin ventilación.\n• Desconecte el negativo PRIMERO al quitar una batería. Conecte negativo ÚLTIMO al instalar. Reduce riesgo de arco en la celda.\n• Las baterías comerciales son PESADAS — 70+ lbs. Cargar entre dos o levantador apropiado. Espaldas y dedos del pie son lesiones típicas.\n• Kit de derrames de ácido y estación de lavaojos probados cada mes. Lavaojos sin probar es lavaojos inútil.",
    references_cited:
      "OSHA 29 CFR 1910.151 · OSHA 1910.305 · Manuales OEM de servicio de batería · SOP de Servicio de Batería MASCI",
    action_items:
      "Paso de inspección visual de batería agregado · Secuencia de boost-a-tierra-no-batería reforzada · Prueba mensual de lavaojos programada · Política de levante entre dos revisada",
  },

  // ============================================================
  // PLANTA / TRITURADOR / LAB / AEROPUERTO · FASE F · iter251
  // ------------------------------------------------------------
  plant_conveyor_entanglement: {
    title: "Enredamiento en Banda Transportadora — Poleas de Cola y Puntos de Pellizco",
    incident_pattern:
      "Las fatalidades por enredamiento en banda en plantas de agregado y asfalto siguen un patrón terriblemente predecible. Un peón se acerca a una polea de cola corriendo para limpiar acumulación de finos o un pedazo de metal extraño. Mete una pala, la pala agarra la banda, y es jalado al punto de pellizco entre banda y polea. La banda no para sola. Para cuando el operador pega al paro de emergencia desde la caseta, el trabajador ya se fue. CADA reporte de incidente de banda que hemos leído incluye la línea 'la guarda estaba quitada' o 'iba a agarrarlo nomás rapidito.'",
    hazards_reviewed:
      "Enredamiento en polea de cola / cabeza / take-up · Pellizco en rodillos idler · Ropa suelta atrapada por banda · Subirse a banda corriendo · Limpiar bajo banda corriendo · Aplastamiento por arranque/paro durante servicio",
    discussion_notes:
      "• NADIE cerca de una polea de cola o cabeza corriendo. Punto. La acumulación se limpia con la banda BLOQUEADA, no corriendo.\n• Guardas en todos los puntos de pellizco cuando la banda corre. Si una guarda está fuera por servicio, la banda está BLOQUEADA.\n• Metal extraño removido con la banda apagada, no 'lo agarro antes de la siguiente descarga.' Los imanes y detectores están para prevenir esa situación.\n• Sin meter mano a banda corriendo con pala, escoba, barra, mano. Sin excepciones.\n• Cuerdas de paro de emergencia a lo largo de toda la longitud, probadas semanalmente. Los operadores deben saber exactamente dónde está la cuerda más cercana.\n• Caminar bajo una banda — casco puesto, vigilar caída de material, nunca pararse bajo una banda que está siendo limpiada río arriba.\n• Subirse a una banda — solo con banda bloqueada y etiquetada. Nunca en banda corriendo.\n• Trabajadores nuevos de planta: caminen el sistema de bandas el Día 1 con el líder. Apunten a cada punto de pellizco. Muestren cada paro de emergencia.",
    references_cited:
      "OSHA 29 CFR 1910.147 · MSHA 30 CFR Parte 56 · Seguridad de bandas NSSGA · SOP de Planta MASCI",
    action_items:
      "Regla de no-tocar-banda-corriendo reforzada · Inspección de guardas asignada · Función de cuerdas de paro probada · Recorrido de bandas para trabajador nuevo programado",
  },
  plant_baghouse_silo_hazards: {
    title: "Limpieza de Baghouse y Riesgos de Entrada a Silos",
    incident_pattern:
      "Las fatalidades en silos y baghouse casi siempre involucran a alguien entrando sin permiso de espacio confinado. El patrón: un baghouse se está tapando, la producción cae, y alguien se sube al gabinete para romper el puente de material. No le dicen a nadie exactamente dónde están. El puente cede, el material cae en avalancha, y quedan engullidos. Los silos de asfalto añaden vapores de bitumen caliente y el riesgo de caer en material caliente. Los silos de agregado añaden polvo fino a densidades de asfixia. Ambos han matado trabajadores de planta en los últimos 5 años en esta industria. El arreglo es el mismo que siempre ha sido: permiso de espacio confinado, prueba atmosférica, asistente, línea de recuperación.",
    hazards_reviewed:
      "Engullimiento en material fluyente · Asfixia por bajo O2 en atmósfera de silo · Quemadura por contacto con bitumen caliente · Colapso de puente sobre trabajadores · Aplastamiento por equipo de limpieza rotatorio · Caídas desde plataformas de baghouse",
    discussion_notes:
      "• Permiso de entrada a espacio confinado ANTES de que alguien entre a silo, baghouse o tanque de almacenamiento. Sin 'nomás voy a meterme rápido.'\n• Prueba atmosférica — O2, LEL, CO, H2S mínimo. Monitoreo continuo mientras esté ocupado. Silos de asfalto: también probar VOCs.\n• Asistente afuera todo el tiempo. NO entran a rescatar. Llaman al rescate. Mantienen comunicación.\n• Línea de recuperación y arnés completo para el entrante. Silos de asfalto añaden PPE resistente al calor.\n• Aislamiento de material ANTES de entrada. Lockout de alimentación. Lockout de descarga. Verifique que el puente esté roto desde AFUERA si es posible.\n• Romper puente desde afuera siempre que sea posible — barras largas, lanzas de aire, vibradores. Entrar debe ser la última opción, no la primera.\n• Plataformas de acceso de baghouse — barandales completos, protección contra caídas arriba de 6 ft, nunca confíe en una plataforma con rejilla corroída.\n• Emergencias en silo de asfalto: el trabajador está del lado caliente. Sáquenlo RÁPIDO. Tengan plan de rescate escrito y ensayado.",
    references_cited:
      "OSHA 29 CFR 1926 Subparte AA · OSHA 1910.146 · NIOSH entrada a silos · SOP de Espacio Confinado MASCI",
    action_items:
      "Política de permiso de espacio confinado reforzada · Monitor atmosférico calibrado · Herramientas para romper desde afuera disponibles · Plan de rescate revisado",
  },
  plant_asphalt_burns_oil_exposure: {
    title: "Quemaduras de Asfalto Caliente y Exposición a Vapor de Bitumen",
    incident_pattern:
      "Las quemaduras de asfalto no son como quemaduras normales. El material está a 300–350°F cuando toca la piel y SE PEGA — no escurre como agua caliente. El trabajador no puede quitárselo a tiempo para prevenir quemaduras de tercer grado. El escenario más común es un muestreador en el load-out, un chofer subiéndose al camión, o un técnico de lab en la caldera. Un salpicón, un contacto con una línea caliente, una liberación súbita de material atrapado — y lo que habría sido un susto ahora es un viaje al hospital con injertos de piel. Los vapores de bitumen en la planta complican el asunto con irritación respiratoria y preocupaciones de exposición a largo plazo.",
    hazards_reviewed:
      "Quemadura de tercer grado por contacto con asfalto caliente · Quemadura por liberación de vapor en load-out · Inhalación de vapor (exposición PAH) · Quemadura ocular por salpicón · Resbalón en binder derramado y frío · Quemadura a través de ropa",
    discussion_notes:
      "• Mangas largas, pantalones largos, guantes con puños. Botas calificadas para asfalto — cuero, no sintéticas. Las botas sintéticas se derriten DENTRO del pie.\n• Careta sobre lentes de seguridad para cualquier trabajo de load-out, muestreo o caldera. Los salpicones van a la cara.\n• Párese A FAVOR DEL VIENTO del tubo al cargar. Choferes: quédense en la cabina durante el load-out donde se permita. Si debe estar afuera, protección ocular.\n• Nunca use agua para lavar asfalto caliente de la piel. Enfríe con compresas frías si es posible, luego al ER. El agua puede meter el calor más profundo.\n• Muestreo: muestreadores de mango largo. Nunca alcance dentro de una caldera o chute de load-out con herramienta corta. La distancia de salpicón es real.\n• Vapores de bitumen — trabaje a favor del viento, tome descansos, reporte síntomas (dolor de cabeza, ardor de ojos, irritación de garganta). El monitoreo a largo plazo importa.\n• Lavaojos y ducha de emergencia dentro de 25 pies de operaciones de asfalto. Probadas mensualmente.\n• Si un trabajador se quema: cubra la quemadura con paño limpio y seco (NO trate de quitar el asfalto de la piel). Al ER inmediatamente.",
    references_cited:
      "OSHA 29 CFR 1910.132 · TLV ACGIH para bitumen · Guía NIOSH para humos de asfalto · SOP de Quemadura en Planta MASCI",
    action_items:
      "PPE para trabajo en planta verificado · Uso de muestreador de mango largo discutido · Lavaojos / ducha probados · Procedimiento de respuesta a quemadura revisado",
  },
  plant_burner_systems: {
    title: "Sistemas de Quemador — Riesgos de Encendido y Apagado de Flama",
    incident_pattern:
      "Los incidentes relacionados con el quemador en plantas de hot-mix siguen dos patrones. El primero es explosión de encendido: el quemador cicla por ignición, no enciende, pero el combustible sigue alimentándose. El combustible sin quemar se acumula en el tambor. Cuando la ignición finalmente prende, el combustible acumulado explota — volando el extremo del tambor, lanzando flama a través del patio de planta, y lesionando a cualquiera cerca. El segundo es apagón durante operación: la flama se va, el combustible continúa, y el siguiente encendido se comporta igual. Ambos son causados por ciclos de purga saltados, fuentes de ignición débiles, u operación fuera del sobre de control. Los sistemas modernos de flame-safeguard previenen esto — SI están mantenidos y no son bypaseados.",
    hazards_reviewed:
      "Explosión de encendido en tambor · Flashback a línea de combustible · Quemadura por blowout de extremo del tambor · Daño auditivo por explosión · Acumulación de CO en área de operación de planta · Ignición de fuga de combustible",
    discussion_notes:
      "• Ciclo de purga CADA encendido. No 'cuando me acuerde.' CADA vez. La purga limpia cualquier combustible sin quemar de intentos previos.\n• No bypasee el sistema de flame-safeguard. Si está disparándose repetidamente, ARREGLE la causa — no lo brinquee.\n• Secuencia de encendido: purga → ignición piloto → ignición de quemador principal → flama detectada → fuego completo. Cada paso verificado antes del siguiente.\n• Si la flama se va durante operación: corte combustible INMEDIATAMENTE, complete un ciclo de purga, luego re-encienda. No solo siga alimentando.\n• Área del quemador libre de personal durante encendido. Fije la regla, hágala cumplir. Si algo falla, no quiere a nadie en línea de fuego.\n• Inspección diaria de líneas de combustible, válvulas, piloto, escaneador de flama. Las fugas en el quemador son catastróficas si se acumulan y encuentran ignición.\n• Monitoreo de CO en el área del patio de planta. Inversiones y condiciones de viento apretadas atrapan el escape. Los trabajadores necesitan saber si se está acumulando.\n• Si huele a combustible sin quemar cerca del quemador — PARE. Apague. Investigue antes de re-encender.",
    references_cited:
      "NFPA 86 · OSHA 29 CFR 1910.106 · Manuales OEM del quemador · SOP del Quemador de Planta MASCI",
    action_items:
      "Protocolo de ciclo de purga reforzado · Política de manipular flame-safeguard discutida · Inspección diaria de línea de combustible asignada · Monitor de CO verificado",
  },
  plant_loader_blind_spots_haul_road: {
    title: "Puntos Ciegos de Cargador y Interacciones en el Haul Road",
    incident_pattern:
      "Los incidentes en el patio de planta y haul road casi siempre involucran un cargador y un camión de acarreo o una pickup. El operador de cargador tiene buena visibilidad en la dirección que apunta el cucharón — y mala visibilidad ATRÁS y a la derecha. Un chofer entra a posición, un foreman camina el patio a inspeccionar material, o un vendedor sale de la oficina. El cargador retrocede para reposicionarse a la siguiente descarga, y el espacio entre el cucharón y el camión se cierra. El patrón es tráfico constante, movimiento constante, y un operador de cargador que no puede ver a todos todo el tiempo. La supervisión del patio y la disciplina de tráfico son lo que previene esto.",
    hazards_reviewed:
      "Golpe-por de cargador retrocediendo · Chofer de pickup en punto ciego del cargador · Aplastado entre cargador y pila · Vendedor / visitante en área activa de patio · Avalancha de material durante operación del cargador",
    discussion_notes:
      "• Operadores de cargador: alarma de reversa funcional, CADA turno. Si está rota, el cargador no corre.\n• Carril de entrada/salida para camiones de acarreo — definido y señalizado. Los choferes se quedan en cabina durante carga siempre que sea posible.\n• Visitantes / ventas / gerencia en el patio: chaleco hi-vis + casco, escoltados, nunca en la trayectoria activa del cargador. Si no está cargando, está en otro lado.\n• El operador NO carga si alguien está en la zona de retroceso. Pause, indíqueles que despejen, luego opere.\n• El haul road tiene límite de velocidad publicado y patrón de un solo sentido. Háganlo cumplir. Tráfico lado-a-lado en un haul road es un choque frontal esperando suceder.\n• Vigile la cara de la pila. Un cargador socavando una cara crea un voladizo que puede colapsar sin aviso. Mantenga las caras al ángulo de reposo.\n• Foremen en el patio: párese donde pueda ver los ojos del operador a través del vidrio de cabina. Si no puede, el operador no lo puede ver a usted tampoco.\n• Operaciones nocturnas de planta: operador con luz de cabina apagada, choferes con faros apuntando lejos del operador. El brillo ciega al cargador hacia trabajadores en tierra.",
    references_cited:
      "OSHA 29 CFR 1926.602 · MSHA 30 CFR Parte 56 · Seguridad de Planta NSSGA · SOP de Tráfico de Patio MASCI",
    action_items:
      "Verificación de alarma de reversa por turno verificada · Política de escolta de visitantes revisada · Pendiente de cara de pila inspeccionada · Procedimiento de brillo nocturno discutido",
  },
  plant_crusher_clearing_jams: {
    title: "Atascos de Triturador — Cómo Liberar Trituradores Bloqueados con Seguridad",
    incident_pattern:
      "Los incidentes al liberar trituradores son algunas de las peores lesiones en la industria del agregado. Un pedazo de metal extraño o alimentación de tamaño excesivo atasca el triturador. El operador se sube a la banda de alimentación o entra a la boca del triturador con una barra para liberar el material. El triturador sigue energizado, el operador está en un espacio apretado con energía hidráulica / mecánica almacenada, y o el atasco se libera violentamente (lanzando el material y al trabajador) o alguien golpea un control y el triturador arranca. Se pierden extremidades. Los trabajadores mueren. El patrón es el mismo que la gente de taller ve con LOTO — pero peor, porque los trituradores tienen energía almacenada enorme.",
    hazards_reviewed:
      "Arranque de triturador mientras está ocupado · Proyectil por liberación súbita de atasco · Aplastamiento en la garganta de alimentación · Caídas de banda de alimentación · Liberación de energía hidráulica / de resorte almacenada · Proyectil de metal extraño",
    discussion_notes:
      "• LOTO el triturador antes de CUALQUIER trabajo de liberación. Desconexión del motor principal. Aislamiento hidráulico. Candado personal por cada trabajador involucrado.\n• Verifique energía cero. Try-start en el control. Baje presión hidráulica. Bloquee cualquier componente móvil mecánicamente.\n• Nunca libere un atasco con la mano desde la garganta de alimentación. Use herramientas de mango largo desde AFUERA de la zona de trituración.\n• Si debe entrar — trato de espacio confinado. Asistente. Recuperación. Comunicación.\n• Manejo de metal extraño — imán, detector de metal, scalper. PREVENGA el atasco antes de que pase.\n• Material sobre-tamaño — sacado en el scalper, no permitido llegar a la boca del triturador.\n• Al liberar un atasco, párese fuera-de-eje de la garganta. El material liberado puede salir disparado rápido.\n• Operadores de triturador: capaciten a los nuevos en procedimiento de liberación con el triturador bloqueado, caminando cada paso ANTES de que encuentren un atasco real.",
    references_cited:
      "OSHA 29 CFR 1910.147 · MSHA 30 CFR Parte 56 · Seguridad de Triturador NSSGA · Manual OEM del triturador",
    action_items:
      "Procedimiento LOTO de triturador revisado · Herramientas de mango largo disponibles · Manejo de metal extraño discutido · Capacitación de liberación para nuevo asignada",
  },
  plant_lab_solvents_ignition: {
    title: "Lab de Asfalto — Solventes, Hornos y Riesgo de Ignición",
    incident_pattern:
      "Los incendios en lab de asfalto usualmente involucran solventes y hornos. Un técnico corre una extracción usando tricloroetileno o percloroetileno, ventila a la campana, pone el rotovap, y se va. Un reflujo al horno, un punto caliente en el elemento, un motor que arquea — y el vapor de solvente encuentra ignición. El fuego es rápido y el humo es tóxico. Los técnicos de lab trabajando solos están en el mayor riesgo porque nadie ve los avisos tempranos. El otro patrón es el aparato de punto de ignición durante prueba de pérdida por ignición — flama abierta, sólidos calientes, cerca de combustibles. Estos labs son más apretados de lo que la gente piensa.",
    hazards_reviewed:
      "Ignición de vapor de solvente · Quemadura por aparato calentado · Inhalación de TCE / perc / humos · Rotura de vidrio con aceite caliente · Salpicón ocular de binder extraído · Resbalón en derrame de solvente",
    discussion_notes:
      "• Campana de ventilación operativa y probada. CADA corrida de extracción usa la campana. Si la campana está abajo, la prueba espera.\n• Contenedores de solvente etiquetados, tapados, almacenados en gabinete inflamable entre usos.\n• Trabajo caliente — hornos, aparato de punto de ignición, calderas — mantenido físicamente separado del trabajo de solvente. Disciplina de lado caliente / lado frío.\n• PPE: guantes de nitrilo, protección ocular, bata de lab. Sin cabello suelto, sin bufandas, sin batas con cordones o lazos.\n• Lavaojos y ducha de emergencia dentro de 10 segundos de cualquier aparato. Probados semanalmente.\n• Contenedores de desecho de solvente metálicos, tapados, conectados a tierra. No vidrio, no jarras abiertas en repisa.\n• Sin comer, beber o guardar comida en el lab. El bitumen y los solventes se transfieren a las manos y a las bocas.\n• Técnico de lab trabajando solo fuera de horas — protocolo de llamada. Alguien sabe que está adentro. Revisan si no envía mensaje de salida.",
    references_cited:
      "OSHA 29 CFR 1910.1450 (Estándar de Lab) · NFPA 45 · TLVs ACGIH · SOP de Lab MASCI",
    action_items:
      "Prueba de función de campana verificada · Auditoría de almacenamiento de solventes hecha · Layout lado-caliente / lado-frío discutido · Protocolo de check-in fuera de horas fijado",
  },
  plant_silo_burn_avalanche: {
    title: "Drag Slat de Silo de Asfalto y Avalancha de Material",
    incident_pattern:
      "El load-out de silo de asfalto es una interfaz peligrosa — material caliente a 300°F+ sentado en un silo, liberado por una compuerta, cayendo 8–15 pies a la caja de un camión abajo. El patrón de lesiones es doble: los choferes bajo el silo durante una caída se queman por salpicón o derrame, y los drag-slat sobre el silo pueden lanzar material si una acumulación se libera inesperadamente. El incidente clásico es un chofer subiendo a la plataforma del silo para revisar el nivel de carga, asomándose, y siendo golpeado por una liberación súbita de material cuando la compuerta abre. O un trabajador de mantenimiento en la plataforma del drag-slat cuando un atasco río arriba se libera.",
    hazards_reviewed:
      "Quemadura por liberación súbita de material en compuerta · Caída desde plataforma de silo · Aplastamiento por cadena de drag-slat · Quemadura por fuga de aceite de drag-slat · Inhalación de vapor tóxico en parte alta del silo · Chofer atorado bajo silo caliente",
    discussion_notes:
      "• Chofer bajo el silo: en la cabina durante carga. Siempre. Suba solo después de que la compuerta cerró y el chute drenó.\n• Acceso a parte alta del silo: arnés y atado arriba de 6 ft. Aun en plataforma con barandal, protección contra caídas durante cualquier tarea que involucre asomarse.\n• Los drag-slat son LOTO siempre que un trabajador esté en la plataforma para servicio o inspección. Pasar caminando para revisión visual desde distancia segura es una cosa — trabajo de servicio necesita LOTO completo.\n• Comunicación entre operador de load-out y chofer — radio o señal de claxon. El chofer sabe cuándo la compuerta está por abrir.\n• Fallas de compuerta de silo — si una compuerta no sella, ponga el silo FUERA DE SERVICIO para reparar. No trabaje alrededor de una compuerta con falla.\n• Vapores en parte alta del silo — los vapores de bitumen se acumulan en el espacio superior. No abra la escotilla de inspección en viento calmo sin ventilación. Tome descanso a favor del viento después de exposición.\n• Caja del camión bajo el silo: confirmación visual antes de abrir la compuerta. Caja vacía, posicionada apropiadamente. El foreman da el OK.",
    references_cited:
      "OSHA 29 CFR 1926.501 · MSHA Seguridad de Silos · Manuales OEM de silo / drag-slat · SOP de Load-out MASCI",
    action_items:
      "Regla de chofer-en-cabina-en-load-out reforzada · Protección contra caídas en parte alta verificada · Procedimiento LOTO de drag-slat revisado · Regla OOS por falla de compuerta discutida",
  },
  airport_movement_area_awareness: {
    title: "Áreas de Movimiento de Aeropuerto — Disciplina de Pista, Taxiway y ATC",
    incident_pattern:
      "Los incidentes en trabajos de aeropuerto involucran aeronaves, no solo equipo de tierra. El patrón se repite: una cuadrilla está pavimentando o reparando pavimento al borde de una pista o taxiway. El líder ha despejado la zona de trabajo con ATC. La autorización era por una hora. La cuadrilla se pasa de la autorización porque un equipo se descompuso. ATC, asumiendo que la zona está despejada en el tiempo acordado, libera la pista. Una aeronave está rodando en 90 segundos. El trabajador sacando un equipo no sabe que la autorización venció. El hallazgo más consistente en fatalidades relacionadas con aeropuerto es ruptura de comunicación — entre ATC, el líder, y los trabajadores en tierra.",
    hazards_reviewed:
      "Golpe de aeronave a trabajador o equipo en área de movimiento activa · Jet blast / prop wash · FOD creado por escombros del sitio · Incursión de equipo a pista activa · Ruptura de comunicación con ATC · Confusión en operaciones de baja visibilidad o noche",
    discussion_notes:
      "• El trabajo en área de movimiento requiere autorización de ATC y ventana CONFIRMADA. El líder tiene la radio. El líder está en ello.\n• Si la ventana de trabajo está por expirar — PARE. Saque a todos y todo. NO empuje el tiempo. ATC va a re-autorizar; las aeronaves no pueden aterrizar dos veces.\n• Los trabajadores todos cargan radios en la frecuencia de operaciones que la autoridad del aeropuerto asigna. Escuchen primero, hablen segundo.\n• Disciplina de FOD — cada llave, cada cono, cada escombro contado antes de despejar el área. Un perno suelto destruye un motor de jet.\n• Hi-vis a especificación de aeropuerto — no igual que hi-vis de construcción. ANSI 207 colores de Seguridad Pública donde se requiera. Lea la especificación del contrato.\n• Equipo en zona activa — escoltado, marcado, y en radio ATC. Pickups también. Nadie freelancea sobre un taxiway.\n• Zonas de jet blast / prop wash — aun aeronaves pequeñas crean viento que puede lanzar a una persona o un cono. Manténgase lejos de aeronaves en espera.\n• Operaciones de noche / baja visibilidad — coordinación extra, iluminación extra, check-ins extra. No empuje a través de mala visibilidad sin alineación con autoridad.",
    references_cited:
      "FAA AC 150/5210-5 · FAA AC 150/5370-2 · Procedimientos TSA / específicos del aeropuerto · SOP de Operaciones de Aeropuerto MASCI",
    action_items:
      "Protocolo de autorización ATC reforzado · Responsabilidad de FOD revisada · Disciplina de radio discutida · Simulacro de retirada por expiración de ventana asignado",
  },
  airport_jet_blast_fueling: {
    title: "Jet Blast, Prop Wash y Conciencia de Recarga en Aeropuerto",
    incident_pattern:
      "Los trabajadores subestiman el jet blast y prop wash. Un turbohélice regional encendiendo genera 100+ mph de viento atrás. Un jet comercial en thrust de ralenti genera vientos capaces de voltear una pickup. El patrón: una cuadrilla está posicionando equipo cerca de una aeronave en espera, el piloto sube thrust para empezar a taxiar, y un trabajador, un cono, o un equipo es lanzado. Combine eso con el ambiente de recarga de aeropuerto — Jet-A está en todas partes, las fuentes de ignición deben controlarse, y una chispa estática es un fuego Clase B instantáneo. El trabajo en aeropuerto tiene sus propios riesgos que no existen en ningún otro lado.",
    hazards_reviewed:
      "Trabajador / equipo lanzado por jet blast · Lesión por prop wash a cuadrilla en tierra · Ignición estática de Jet-A · Ignición de nube de vapor cerca de operaciones de combustible · Daño auditivo por ruido de aeronave · FOD por escombros lanzados",
    discussion_notes:
      "• Manténgase lejos de aeronaves en espera. Una distancia de 100 pies es un punto de partida, no un máximo. Si puede ver el motor, el motor lo puede golpear con blast.\n• Protección auditiva en cualquier área de movimiento activa. El ruido de aeronaves daña la audición en minutos de exposición.\n• Áreas de recarga Jet-A — sin fuentes de chispa dentro de 50 pies. Sin celulares, sin linternas sin clasificación intrínseca, sin metal-contra-metal.\n• Amarre o ponga peso a TODO cerca de un taxiway. Conos, caballetes, equipo. Lo que se queda en viento normal se vuela en prop wash.\n• Las operaciones de recarga tienen su propia cuadrilla. Las cuadrillas de construcción no intersectan con ops de recarga. Manténgase lejos de camiones de combustible y aeronaves recargando.\n• Conexión a tierra estática para cualquier trabajo adyacente a recarga. Cables de bonding, varillas de tierra. La estática es la fuente de ignición silenciosa.\n• Si siente viento de repente — mire alrededor. Una aeronave se está moviendo en un lugar que no esperaba. Verifique posición antes de continuar.\n• Protección ocular — escombros en trabajo de aeropuerto están en todas partes. Caretas abiertas no son suficiente en aeropuertos ocupados.",
    references_cited:
      "FAA AC 150/5230-4 · NFPA 407 (servicio de combustible de aeronaves) · OSHA 1926.101 (audición) · SOP de Aeropuerto MASCI",
    action_items:
      "Distancia de despeje de aeronave reforzada · Protección auditiva verificada · Control de ignición adyacente a recarga discutido · Política de amarre para conos / equipo revisada",
  },

  // ============================================================
  // OFICINA / ADMIN · FASE G · iter251
  // ------------------------------------------------------------
  office_distracted_driving: {
    title: "Manejar Distraído — Teléfonos, Café y el Trayecto",
    incident_pattern:
      "Los choques por manejo distraído golpean al personal de oficina a una tasa que el campo no ve, porque el personal de oficina maneja MÁS — entre obras, entre juntas, a comidas y de regreso. El patrón es benigno individualmente: un texto rápido de un PM, un vistazo a la navegación, un sorbo de café mientras te incorporas. Apila tres de esas cosas pequeñas en 10 segundos y cruzaste una línea central a 65 mph. El factor más consistente en choques de personal de oficina no es estado de embriaguez — es la inatención acumulada de una persona ocupada haciendo seis cosas mientras maneja. El arreglo es política y hábito, no tecnología.",
    hazards_reviewed:
      "Choque frontal / fuera de camino por inatención · Choque trasero en cambio de semáforo · Multa por uso de celular · Velocidad en zona escolar / construcción · Fatiga por días sobre-agendados · Comer / beber mientras maneja",
    discussion_notes:
      "• Teléfono boca abajo o en holder, en modo NO MOLESTAR. Las llamadas van al buzón. Los textos esperan.\n• Manos-libres sigue siendo distraído. La carga cognitiva importa, no solo la posición de las manos. Guarde la llamada para el estacionamiento.\n• Navegación fijada ANTES de poner el camión en marcha. Re-rutear mientras maneja es causa principal de choques relacionados con oficina.\n• Café, comida, papeleo — hágase a un lado. Los 90 segundos que cuesta es el seguro más barato que comprará.\n• Margen de horario. Si su día tiene cero margen, cada junta tarde se vuelve un viaje con exceso de velocidad. Construya holgura en su calendario.\n• Zonas de construcción — en ambas direcciones. Baje velocidad por las zonas PROPIAS de MASCI primero. Lidere la cultura.\n• Clima severo — hágase a un lado y espere. Lluvia a 70 mph no es manejar, es apostar.\n• Si está cansado, está manejando impedido. Hágase a un lado por 20 minutos. La junta esperará.",
    references_cited:
      "NHTSA Manejo Distraído · Leyes estatales de manos-libres · Política de Vehículo de Flota MASCI",
    action_items:
      "Política de NO-MOLESTAR-al-manejar reforzada · Mensaje de manos-libres-sigue-siendo-riesgoso discutido · Disciplina de margen de horario revisada · Regla de hacerse-a-un-lado por clima severo discutida",
  },
  office_site_visit_ppe: {
    title: "PPE de Visita a Obra y Expectativas para Visitantes",
    incident_pattern:
      "La mayoría de las lesiones a personal de oficina en sitios pasan en los primeros 5 minutos de llegar al jobsite. El patrón: llegar con ropa de oficina, sin hi-vis, sin casco, caminar hacia el foreman para encontrarlo, y meterse al radio de giro de un excavador o a la trayectoria de un dump truck retrocediendo. El visitante no conoce el sitio, los operadores no saben que el visitante viene, y el foreman está a 200 pies. El personal de oficina frecuentemente piensa que 'nomás vengo 5 minutos' justifica saltarse el PPE. La cuadrilla ha trabajado toda la mañana construyendo una cultura de PPE y el visitante la mina instantáneamente. El arreglo es PPE en el vehículo, sin excepciones.",
    hazards_reviewed:
      "Golpe-por de equipo en primera llegada · Tropezón / caída en terreno rugoso · Lesión ocular por escombros lanzados · Lesión de cabeza por bajo aéreo · Estrés por calor sin agua / sombra · Visitante minando la cultura de PPE de la cuadrilla",
    discussion_notes:
      "• Kit de PPE en cada vehículo de oficina: casco, chaleco hi-vis Clase 2, lentes de seguridad, guantes de cuero, botas de seguridad (o cubre-zapatos como respaldo para UNA visita).\n• Póngase el PPE ANTES de salir del vehículo. No después de caminar 50 pies por el estacionamiento. Antes.\n• Encuentre al foreman por RADIO o TELÉFONO antes de caminar. El foreman viene a USTED a un punto de encuentro seguro — no al revés.\n• Quédese en trayectos marcados. No corte por zonas de trabajo activas, aunque agregue 100 pies.\n• Firme en la caja de herramientas / hoja de firma. El sitio sabe quién está en sitio.\n• No aparezca a la hora de comida sin anuncio. Agende la visita. Deje que el foreman le avise a la cuadrilla.\n• Calor / frío — traiga agua, vístase para el clima, sepa dónde está el trailer de descanso.\n• Dé el ejemplo. La cuadrilla ve si SU PPE está bien. Siguen esa señal.",
    references_cited:
      "OSHA 1926.95 / .96 / .100 / .102 (PPE) · ANSI/ISEA 107 · SOP de Visitante MASCI",
    action_items:
      "Kit de PPE en cada vehículo de oficina verificado · Hábito de encontrar-al-foreman-primero reforzado · Política de visita-agendada revisada · Firma de visitante aplicada",
  },
  office_parking_lot_struck_by: {
    title: "Estacionamientos, Reversa y Conciencia Peatonal",
    incident_pattern:
      "Los incidentes de estacionamiento en sitios MASCI y oficinas de clientes pasan a las velocidades más lentas y aun así producen las lesiones de tobillo, rodilla y espalda más comunes del lado administrativo. El patrón: un admin o PM camina del vehículo a la puerta de oficina, mirando su teléfono por la confirmación de junta. Un chofer de pickup retrocediendo, también distraído, nunca lo ve. El contacto es a 3–5 mph. El peatón no cae duro pero se tuerce al esquivar — rodilla, tobillo, espalda. Otra variante: salir de una cabina hacia un vehículo estacionado junto al suyo. El filo de la puerta toca la siguiente puerta, el dueño se molesta, reclamo presentado. Velocidades lentas, grandes resultados.",
    hazards_reviewed:
      "Vehículo retrocediendo golpea-por · Resbalón en estacionamiento mojado / con hielo · Bajarse de banqueta a trayectoria de vehículo · Golpe de puerta a vehículo adyacente · Tropezón con topes · Problemas de visibilidad en invierno / poca luz",
    discussion_notes:
      "• Teléfono ABAJO al caminar. Ojos en el estacionamiento, en luces de reversa, en movimiento. El texto espera.\n• Camine en cruces marcados donde existan. Donde no, escoja la trayectoria más segura y manténgala.\n• Al retroceder — retroceda ANTES de que salgan los niños y peatones. O pase de paso si está disponible. O cámara de reversa, barrido de espejos, Y vistazo rápido sobre el hombro. Las cámaras solas no son suficiente.\n• Salga de su vehículo a un espacio LIBRE — no abra la puerta a ciegas al carril siguiente.\n• Invierno / mojado — botas con agarre en la suela, no zapatos de vestir. Un resbalón en el estacionamiento sí pasa a edad MASCI.\n• Estaciónese en espacios iluminados de noche. La visibilidad de SU vehículo importa tanto como la visibilidad desde SU vehículo.\n• Cuidado con personal de oficina y visitantes en sitios de cliente — no están acostumbrados a la escala de vehículos de construcción. Reduzca velocidad extra en estacionamientos de cliente.",
    references_cited:
      "OSHA Deber General · NHTSA Seguridad Peatonal · Política de Flota MASCI",
    action_items:
      "Hábito de teléfono-abajo-al-caminar discutido · Regla de cámara-más-espejo revisada · Discusión de calzado de invierno · Precaución-extra en estacionamiento de cliente reforzada",
  },
  office_heat_stress_visits: {
    title: "Estrés por Calor en Visitas de Verano a Obra",
    incident_pattern:
      "Las lesiones por calor a personal de oficina durante visitas de verano siguen un patrón específico. El visitante llega en ropa de oficina-casual, sin agua, camina el sitio por 30–45 minutos en calor de 95°F+, y solo se da cuenta que está en problemas cuando ya está sintomático — dolor de cabeza, mareo, náusea. Manejaron solos al sitio, y ahora tienen que manejar solos a casa mientras están sintomáticos por calor, lo cual es su propio riesgo de choque. El personal de oficina tiene menor tolerancia al calor que la cuadrilla de campo porque no están aclimatados al calor. Una caminata de 20 minutos para un trabajador de campo es un riesgo serio de salud para alguien que estuvo en AC toda la mañana.",
    hazards_reviewed:
      "Agotamiento por calor progresando a golpe de calor · Choque por manejar con síntomas de calor · Deshidratación · Quemadura solar / daño ocular por exposición prolongada · Subestimar el calor sin aclimatación",
    discussion_notes:
      "• Botella de agua en el vehículo, cada visita a obra, mayo a octubre. Beba antes, durante y después.\n• Agende visitas de verano en la mañana o tarde noche. Evite el pico de calor de 11 a.m. a 3 p.m.\n• Sombrero que sombree cara y cuello. Bloqueador solar. Las mangas largas son más frescas que la piel descubierta al sol directo.\n• Tome descansos en el trailer o en su vehículo con AC. No 'aguante.'\n• Vigile síntomas en usted y otros: dolor de cabeza, náusea, irritabilidad, mareo, silencio súbito. El agotamiento por calor progresa a golpe de calor RÁPIDO.\n• Si aparecen síntomas: a sombra o AC, beba agua con electrolitos, enfríe el cuerpo. Si los síntomas no resuelven en 15 minutos — ER.\n• Manejar con síntomas de calor es manejar impedido. Que alguien lo lleve. Llame a dispatch. Espere en el trailer.\n• Los nuevos contratados y visitantes NO están aclimatados. Trátelos más conservadoramente que la cuadrilla de campo.",
    references_cited:
      "OSHA Estrés por Calor · NIOSH Estrés por Calor · CDC Enfermedad por Calor · Política de Calor MASCI",
    action_items:
      "Hábito de agua-en-vehículo reforzado · Agendar visitas matutinas revisado · Conciencia de síntomas discutida · Regla de no-manejar-impedido reforzada",
  },
  office_lone_worker_checkin: {
    title: "Trabajador Solo / Realidades de Check-In en Obra",
    incident_pattern:
      "Los incidentes de trabajador solo en MASCI típicamente involucran un PM, un estimador o un vendedor que manejó a un jobsite remoto, se estacionó, caminó el proyecto solo, y o tuvo un evento médico (corazón, derrame, caída) o entró en interacción tensa con un cliente o un intruso. Nadie sabía exactamente dónde estaban. El teléfono no se había movido por 45 minutos. Para cuando alguien dio seguimiento, la situación se había vuelto seria. El arreglo no es glamoroso: dígale a alguien adónde va, fije una hora de check-in, y cumpla. No hemos tenido una fatalidad de esto — pero hemos tenido casi-accidentes que han cambiado qué tan seriamente tomamos los check-ins.",
    hazards_reviewed:
      "Evento médico sin nadie que responda · Resbalón / caída sin observador · Interacción tensa con intruso · Falla de vehículo en área de baja señal · Cliente hostil / escalada de disputa · Perdido / desorientado en área desconocida",
    discussion_notes:
      "• Dígale a alguien — dispatch, un admin, su gerente — adónde va y cuándo espera regresar. Texto funciona.\n• Fije una HORA de check-in, no solo intención. 'Mando texto para las 2:30.' Si pasa 2:30 sin texto, esa persona le llama.\n• Teléfono cargado antes de salir de oficina. Traiga cargador y power bank cargado para viajes más largos.\n• No entre a una situación hostil solo. ¿Disputa con cliente escalando? Retírese, llame a su gerente, regrese con compañero.\n• Intrusos / personas desconocidas en el sitio — no se enfrente solo. Llame a seguridad del sitio o policía local. Usted no es guardia de seguridad.\n• Falla de vehículo en área remota — quédese con el vehículo si es seguro. Salir caminando lo puede meter en peor problema.\n• Historial médico — si tiene cualquier condición que pueda dejarlo sin respuesta, el protocolo de check-in es doblemente importante.\n• Al final de la visita, mande texto 'libre' a la misma persona. Cierra el loop.",
    references_cited:
      "OSHA Trabajador Solo · ANSI/ASSP Z490 · Política de Visita de Campo MASCI",
    action_items:
      "Disciplina de hora de check-in reforzada · Hábito de cargar teléfono discutido · Política de des-escalación de interacción hostil revisada · Hábito de texto 'libre' al final fijado",
  },
  office_severe_weather_accountability: {
    title: "Responsabilidad por Clima Severo para Cuadrillas y Visitantes",
    incident_pattern:
      "Los eventos de clima severo agarran al personal de oficina en el peor momento — manejando de regreso de una visita, a media junta con cliente, o mientras la oficina cierra al final del día. El patrón de falla es contabilidad: la oficina asume que todas las cuadrillas están adentro, pero dos camiones siguen afuera. El campo asume que la oficina ha llamado a todos, pero tres visitantes siguen en sitio. Cuando un aviso de tornado llega o una tormenta eléctrica entra, nadie sabe con certeza quién está dónde. El arreglo es una persona — usualmente dispatch o admin — siendo dueña del proceso de revisar la lista durante eventos de clima.",
    hazards_reviewed:
      "Trabajador / visitante atrapado en tornado / tormenta severa · Golpe de rayo en sitio · Inundación súbita de sitios bajos · Daño por granizo a cuadrilla y equipo · Hipotermia / calor por exposición prolongada durante tormenta",
    discussion_notes:
      "• Una persona es el POC de clima durante un evento de clima severo. Usualmente dispatch o admin. Tienen la lista. Hacen las llamadas.\n• Revise el radar ANTES de salir de oficina en temporada de tormentas. Vigile frentes que se mueven rápido.\n• Regla de rayo: cuando VEA un rayo o ESCUCHE trueno, la cuadrilla de campo se mete. Regla 30/30 — 30 minutos después del último rayo antes de reanudar.\n• Aviso de tornado: a la estructura más segura disponible. Cuadrilla de campo a la oficina o edificio sólido, NO en vehículo, NO en trailer.\n• Lluvia severa / inundación súbita: evite sitios bajos hasta que las condiciones despejen. Muchos sitios de obra civil pesada están diseñados para inundarse — son canales.\n• Granizo: ponga vehículos bajo techo donde se pueda. Personas lejos de ventanas.\n• Contabilice TODO el personal durante un evento severo. Oficina, campo, choferes, visitantes. El POC revisa cada nombre en la lista.\n• Visitantes en sitio: avísenles antes de que salgan de la oficina que viene clima. Díganles que regresen directo cuando las condiciones se degraden.",
    references_cited:
      "NWS Conciencia de Clima Severo · OSHA Seguridad de Rayo · SOP de Clima Severo MASCI",
    action_items:
      "POC de clima designado · Regla 30/30 de rayo revisada · Mapeo de refugio de tornado verificado · Hábito de avisar a visitante sobre clima discutido",
  },
  office_slips_trips_falls: {
    title: "Resbalones, Tropezones y Caídas en el Ambiente de Oficina",
    incident_pattern:
      "Los incidentes de resbalón y caída en oficina son nada glamorosos y muy reales. El patrón: café derramado en la cocineta queda sin limpiar por una hora, alguien lo pisa con zapatos de vestir, y se cae. O un cable de poder cruzando una puerta durante un setup temporal, nunca recogido. O una escalera con un foco fundido, y alguien falla el último escalón en la esquina oscura. Ninguno de estos es dramático — pero juntos suman más lesiones de tiempo perdido de oficina que cualquier otra causa. Rodillas, tobillos, caderas, muñecas. La gente trabaja lesionada por semanas porque les da vergüenza una caída en el pasillo.",
    hazards_reviewed:
      "Resbalón en líquido derramado · Tropezón con cable de poder / orilla de tapete · Caída en escalera con poca luz · Resbalón en entrada con hielo · Caída de silla / banquito usado como escalera · Resbalón en baño",
    discussion_notes:
      "• Limpie derrames inmediatamente. No espere a alguien más. La siguiente persona que pase puede ser usted.\n• Señales de piso mojado cuando algo no puede limpiarse de inmediato. De verdad funcionan.\n• Cables de poder en setups temporales — pegados con cinta o ruteados alrededor del paso. Sin cables atravesando superficies de caminata.\n• Iluminación de escalera — reporte focos fundidos el mismo día. Facilidades los reemplaza.\n• Tapetes de entrada de invierno — mantenidos en su lugar, reemplazados cuando gastados. Los primeros 6 pies dentro de la puerta son donde pasan la mayoría de resbalones de invierno.\n• Banquito, no silla, para alcanzar algo alto. Tenemos banquitos. Úsenlos.\n• Limpieza del piso de baño — reporte pisos mojados a facilidades. La persona que se resbaló ahí el mes pasado fue usted.\n• ¿Cargando 4 cosas y caminando? Va a tirar una o caerse por una. Dos viajes es mejor que una caída.",
    references_cited:
      "OSHA 1910.22 · Guía NSC de resbalones/tropezones · Política de Seguridad de Oficina MASCI",
    action_items:
      "Hábito de limpiar-derrame-ya reforzado · Reporte de iluminación de escalera revisado · Manejo de cables en setups temporales discutido · Regla de banquito-no-silla reforzada",
  },
  office_fatigue_mental_load: {
    title: "Fatiga y Carga Mental — Cuando Está Cansado, Está Impedido",
    incident_pattern:
      "La fatiga mental es el equivalente de oficina al estrés por calor en campo — más lenta para desarrollarse, más fácil de ignorar, igual de peligrosa. El patrón: un PM trabaja días de 11 horas por dos semanas durante temporada ocupada, duerme mal, vive de café. Los errores se cuelan — un número de obra invertido, una cotización que le falta un renglón, un correo crítico que no se manda. El PM se culpa de no estar agudo. La causa real es deuda sostenida de sueño y fatiga de decisión. A largo plazo, este patrón lleva a depresión, estrés familiar y enfermedad física. Hemos perdido buena gente al burnout que empezó exactamente así.",
    hazards_reviewed:
      "Errores de decisión por privación de sueño · Choque por manejar fatigado · Errores en correo / contrato con impacto río abajo · Burnout / decline de salud mental · Estrés familiar · Enfermedad física por deuda sostenida de sueño",
    discussion_notes:
      "• El sueño no es opcional. Siete horas mínimo. Menos de eso por una semana es impacto cognitivo nivel manejar-impedido.\n• Tome sus vacaciones. Vacaciones acumuladas no ayudan a nadie — vacaciones usadas sí.\n• La fatiga de decisión es real. Las decisiones que toma a las 5 p.m. después de 10 horas de juntas no son sus mejores decisiones. Junte llamadas importantes más temprano en el día.\n• Cuando se cache cometiendo errores, no empuje más — pare. Camine. Hidrátese. Coma. Vuelva.\n• La salud mental no es debilidad. Hable con alguien. EAP es confidencial y útil. Los compañeros son útiles. La familia es útil.\n• Vigile a sus compañeros. Retirados, irritables, propensos a error — son las señales tempranas. Pregúntense unos a otros.\n• Teléfono apagado después de horas cuando se pueda. El trabajo estará ahí mañana. Sus reservas mentales no si no las reconstruye.\n• 988 — Línea de Crisis y Suicidio (llamar o textear). EAP MASCI para ayuda confidencial. La construcción tiene una de las tasas de suicidio más altas de cualquier industria. Esto importa.",
    references_cited:
      "CDC Fatiga · NIOSH Total Worker Health · 988 Línea de Suicidio y Crisis · EAP MASCI",
    action_items:
      "Prioridad de sueño discutida · Política de uso de vacaciones revisada · Conciencia de fatiga de decisión levantada · Info 988 / EAP compartida",
  },
};
