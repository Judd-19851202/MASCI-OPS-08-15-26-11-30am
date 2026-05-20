// Domain ES: grading · iter261 Phase H Batch 3 · 5 ES translations con incident_pattern

export const TOPICS_GRADING_ES = {
  earthmoving_equipment: {
    title: "Equipo de Movimiento de Tierra y Maquinaria Pesada",
    incident_pattern:
      "Las fatalidades de golpe-por y atropello con equipo de movimiento de tierra siguen uno de dos patrones. Patrón uno — el operador no puede ver a un trabajador a pie cerca de la esquina de la cabina. Bulldozers, cargadores, motoniveladoras tienen puntos ciegos que crecen con el tamaño de la maquinaria. El trabajador camina detrás del cargador para una medición rápida, el operador gira para reposicionar, la parte trasera de la cabina barre hacia donde está parado el trabajador. Patrón dos — trabajadores en la línea de fuego del cucharón o la hoja durante la carga. El chofer del camión se baja a saludar al operador del cargador, camina dentro del radio de giro, lo golpea el siguiente pivote. El arreglo no es negociable: sin tráfico a pie en zonas de carga activa, contacto visual + pulgar arriba antes de cualquier movimiento cerca de personal, hi-vis siempre puesto. El operador es responsable de negarse a moverse hasta que PUEDA ver a la cuadrilla en tierra.",
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
    incident_pattern:
      "Las fatalidades por atropello en reversa son una de las categorías más prevenibles en obra civil pesada — y una de las más repetidas. El patrón: un camión de volteo o equipo pesado retrocede sobre un trabajador a pie en una zona de logística congestionada. El chofer estaba viendo los espejos, el trabajador estaba viendo su teléfono o caminando de espaldas al equipo, la alarma de reversa pitó en un mar de otras alarmas y se ignoró. Spotter ausente, o el spotter estaba hablando con alguien más y rompió contacto visual por 4 segundos. El arreglo es rígido: alarmas de reversa en cada retroceso, spotter dedicado para cualquier reversa en zona de trabajo, y perder de vista al spotter = parar. El único trabajo del spotter durante una reversa es la reversa. Nada de radio, nada de teléfono, nada de plática.",
    hazards_reviewed:
      "Atropello al retroceder · Golpe por equipo en reversa · Spotter golpeado por otro vehículo · Falla de comunicación · Puntos ciegos",
    discussion_notes:
      "• Alarmas de reversa operativas en cada equipo móvil / camión de volteo.\n• Spotter requerido al retroceder en áreas congestionadas o cerca de personal.\n• Spotter se ubica fuera del trayecto, en línea de visión del operador.\n• Perder de vista al spotter = PARAR. El operador nunca retrocede a ciegas.\n• Señales de bocina: 1 parar, 2 adelante, 3 reversa.\n• Vestimenta hi-vis obligatoria para spotters todo el tiempo.",
    references_cited: "OSHA 1926.601(b)(4) · Boletín OSHA Atropello en Reversa",
    action_items:
      "Spotters designados · EPP del spotter verificado · Señales revisadas · Plan de comunicación en marcha",
  },
  compaction: {
    title: "Operaciones de Compactación",
    incident_pattern:
      "Las lesiones por compactación se dividen en dos patrones. Patrón agudo — operador de rodillo retrocede sobre un trabajador a pie que se metió a arreglar un punto bajo. Los rodillos de pata de cabra y tambor liso son de los equipos más pesados en una obra de grading y no se detienen en los últimos 6 pies. El operador estaba mirando hacia adelante, la alarma de reversa pitó, el trabajador traía audífonos o estaba distraído, y el cierre fue muy rápido para reaccionar. Patrón crónico — síndrome de vibración mano-brazo por años de operar compactadores manuales sin guantes anti-vibración y sin descansos. Las manos del operador pierden fuerza de agarre, control motor fino, y circulación. Acorta carreras pero es invisible a los 30 años. El arreglo es sin tráfico a pie detrás de un rodillo en movimiento, guantes anti-vibración en cada compactador manual, y 10 minutos de rotación fuera del equipo cada hora.",
    hazards_reviewed:
      "Síndrome de vibración mano-brazo · Vibración de cuerpo entero en rodillos · Golpe por compactador · Volcadura en pendiente · Ruido sobre 85 dBA · Atropello por rodillo en reversa",
    discussion_notes:
      "• Compactadores manuales: agarre firme, guantes anti-vibración, sin ropa suelta.\n• Rodillos vibratorios: nunca operar en pendientes mayores al máximo del fabricante.\n• Zonas prohibidas marcadas; spotters en bordes y conicidades.\n• Alarmas de reversa requeridas; reversa en pendiente solo con spotter.\n• 10 minutos de descanso por hora con equipo vibratorio para mitigar HAVS.\n• Protección auditiva requerida — la mayoría de compactadores supera 85 dBA.",
    references_cited:
      "OSHA 1926.95 · NIOSH Vibración Mano-Brazo · ACGIH TLV para vibración",
    action_items:
      "Guantes anti-vibración · Zonas prohibidas marcadas · Protección auditiva · Rotación de operadores",
  },
  excavator_safety: {
    title: "Seguridad de Excavadora",
    incident_pattern:
      "Las fatalidades de excavadora son usualmente eventos de aplastamiento por radio de giro. El cucharón y el contrapeso juntos crean una zona asesina de 360°, y el trabajador en la zona asesina usualmente tiene una razón para estar ahí — midiendo grado, sloping una pared, sosteniendo una mira para topografía. El operador pivota para cargar el camión o reposicionar, el contrapeso trasero gira hacia el trabajador, y el trabajador queda atrapado contra un talud o equipo adyacente. Patrón secundario es la liberación del cucharón por quick-coupler — el operador levanta el cucharón y el coupler no estaba completamente enganchado, el cucharón cae sobre el peón debajo. Las fallas de quick-coupler mataron a docenas de trabajadores antes de que entrara el estándar de enganche audible. El arreglo son barricadas duras en el radio de giro, sin trabajadores entre la excavadora y cualquier objeto fijo, y enganche de quick-coupler verificado antes de cualquier levantamiento.",
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
    incident_pattern:
      "Las fatalidades de skid-steer tienen un patrón firma brutal: el operador entra o sale de la cabina con los brazos elevados, y los brazos caen. El pasador de soporte de brazo no estaba instalado, el sello hidráulico falló, o el operador golpeó una palanca al bajarse. Los brazos caen en menos de un segundo y aplastan al operador a nivel del pecho. OSHA ha sido claro en esto por 20 años: entrar y salir SOLO con brazos ABAJO y cucharón plano. El otro patrón recurrente es el atropello a espectador — los skid steers y CTLs tienen cero visibilidad trasera, el operador retrocede en una plataforma estrecha, y un trabajador en tierra que pasa queda atrapado. Alarma de reversa, spotter para reversa en congestionado, y nunca entrar bajo brazos elevados — esos tres controles eliminan el 90% de las fatalidades.",
    hazards_reviewed:
      "Aplastamiento por brazos (al entrar/salir) · Volcadura en pendiente · Golpe por accesorios · Atropello por máquina en reversa · Quemaduras por escape/turbo · Desenganche de quick attach",
    discussion_notes:
      "• Entrar/salir SOLO con brazos abajo y cucharón plano — nunca bajo brazos elevados.\n• Cinturón y barra de asiento abajo antes de arrancar.\n• Pasadores de quick attach completamente enganchados — verificar antes de levantar.\n• Sin pasajeros. Sin pararse en accesorios.\n• Reversa en áreas congestionadas requiere spotter.\n• Estacionar nivelado, brazos abajo, cucharón al suelo.",
    references_cited: "OSHA 1926.602 · Manual del Fabricante · NIOSH Skid Steer",
    action_items: "Cinturón · Quick attach verificado · Spotter · Sin pasajeros",
  },
};
