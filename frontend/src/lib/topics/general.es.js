// Domain ES: general · iter261 Phase H Batch 5 · 20 ES translations (18 uplifted + 2 new)

export const TOPICS_GENERAL_ES = {
  demolition: {
    title: "Operaciones de Demolición",
    incident_pattern:
      "Las fatalidades de demolición se agrupan alrededor del colapso prematuro y materiales peligrosos ocultos. El patrón de colapso — un trabajador jala un miembro estructural que el estudio de ingeniería no marcó como portante, un piso superior o muro cae en segundos, y la cuadrilla abajo no tiene tiempo de despejar. El patrón de materiales peligrosos — asbesto o pintura con plomo no estudiados antes de demoler, polvo liberado en la zona de trabajo, la exposición aparece como cáncer respiratorio 20 años después. Sumando golpes a servicios aéreos del cucharón e incendios por sopletes en líneas de combustible, tienes una tasa de fatalidad de las más altas en construcción. El arreglo es el estudio de ingeniería tratado como contrato, abatimiento de materiales peligrosos antes de demoler mecánicamente, y una inspección estructural de lo remanente cada día.",
    hazards_reviewed:
      "Caídas · Golpe por escombros · Colapso prematuro · Exposición a asbesto / plomo · Polvo de sílice · Incendio de corte/trabajo en caliente · Golpe a servicios remanentes",
    discussion_notes:
      "• Estudio de ingeniería antes de demoler — pisos, muros, materiales, servicios.\n• Estudio de materiales peligrosos — asbesto, plomo, PCBs identificados y abatidos.\n• Servicios cortados, capeados, bloqueados antes de demoler.\n• Zonas de caída barricadas; spotters en perímetro.\n• Controles de polvo — supresión con agua y EPP respiratorio.\n• Permisos de trabajo en caliente para corte/soldadura/quema.\n• Inspección diaria de estructura remanente.",
    references_cited:
      "OSHA 1926 Subparte T · OSHA 1926.850 · OSHA 1926.1101 (Asbesto) · OSHA 1926.62 (Plomo)",
    action_items: "Estudio ingeniería · Estudio MatPel · Servicios LOTO · Zonas de caída · Permisos de hot work",
  },
  hot_work: {
    title: "Trabajo en Caliente — Soldadura, Corte, Esmerilado",
    incident_pattern:
      "Los incendios de hot work casi nunca empiezan durante el trabajo. Empiezan 20-45 minutos después de que el trabajo paró, cuando el vigilante de fuego se fue, la cuadrilla se fue, y una brasa humeante finalmente alcanza inflamables. El patrón: chispa de esmerilado cae en una pila de lonas o un bote de trapos aceitosos, humea silenciosamente mientras la cuadrilla sale a comer, se enciende 30 minutos después de que se van, y el edificio o el tanque de combustible arden. NFPA ha rastreado esto por décadas — la vigilancia post-trabajo es cuando realmente brotan los incendios. El otro patrón recurrente es la ruptura de cilindro por almacenamiento inadecuado — oxígeno y acetileno juntos, el cilindro se inclina y se le rompe el regulador, se convierte en un cohete. El arreglo es el permiso de hot work, vigilante de fuego DURANTE y 30 minutos DESPUÉS, combustibles despejados o protegidos, y cilindros encadenados verticalmente con 20 pies entre oxígeno y combustible.",
    hazards_reviewed:
      "Incendio / explosión · Quemaduras · Exposición UV / IR (arco) · Inhalación de humos de soldadura · Escoria caliente igniciendo combustibles · Ruptura de cilindro de gas",
    discussion_notes:
      "• Permiso de Trabajo en Caliente requerido y en sitio para cualquier corte/soldadura/esmerilado fuera del taller.\n• Vigilante de fuego con extintor durante Y 30 min después.\n• Combustibles a 35 pies removidos o protegidos con mantas de soldadura.\n• Cilindros encadenados verticalmente, tapas puestas, oxígeno y combustible separados por 20 pies o barrera no combustible de 5 pies.\n• Protección ocular — sombra acorde al amperaje; protección de espectadores.\n• Ventilación o aire suministrado para galvanizado, cadmio o metal recubierto.",
    references_cited: "OSHA 1926 Subparte J · OSHA 1926.352 · NFPA 51B · ANSI Z49.1",
    action_items: "Permiso firmado · Vigilante de fuego · Combustibles despejados · Extintor listo · Cilindros asegurados",
  },
  forklift_telehandler: {
    title: "Operaciones de Montacargas / Telehandler",
    incident_pattern:
      "Las fatalidades de montacargas y telehandler siguen dos guiones. Guión uno — la volcadura. El operador levanta una carga cerca de la capacidad nominal con boom retraído, luego extiende el boom para colocar la carga alta; la capacidad con extensión es 30-50% de la capacidad retraída, la tabla de carga lo muestra, el operador no la verificó, la máquina se va de lado. El operador queda aplastado porque el cinturón no estaba puesto. Guión dos — atropello peatonal. El operador retrocede en un patio congestionado, el punto ciego cubre al trabajador caminando al lado, la alarma pita pero el trabajador trae audífonos. Ambos mueren bajo los mismos controles: operador certificado, tabla de carga consultada, outriggers extendidos con boom completo, cinturón puesto, spotter para cualquier movimiento cerca de peatones.",
    hazards_reviewed:
      "Volcadura · Golpe por carga · Atropello de peatones · Caídas desde horquillas (sin pasajeros) · Contacto con altura libre · Carga muy alta para ver",
    discussion_notes:
      "• Operador certificado (cert de 3 años + evaluación).\n• Inspección pre-turno registrada.\n• Capacidad con boom extendido es MENOR que retraído — leer la tabla.\n• Carga detrás del talón de horquillas; inclinar hacia atrás al viajar.\n• Viajar con horquillas bajas, ~6 pulgadas sobre el suelo.\n• Reversa en rampas con carga cuesta arriba; sin pasajeros nunca.\n• Outriggers requeridos para telehandler con alcance completo.",
    references_cited: "OSHA 1926.602 · OSHA 1910.178 · ANSI/ITSDF B56.6 · ANSI/ITSDF B56.1",
    action_items: "Cert vigente · Tabla de capacidad · Procedimiento de outriggers · Sin pasajeros",
  },
  ppe_general: {
    title: "EPP — Revisión Diaria de Cumplimiento",
    incident_pattern:
      "Los incidentes de falla de EPP casi nunca pasan porque el trabajador no conocía el requisito. Pasan porque el EPP estaba quitado por 'solo un minuto' — casco quitado porque la cabina tiene aire acondicionado, lentes quitados porque se empañaron, hi-vis quitada porque hacía calor, guantes quitados para sentir una conexión. Ese es el minuto en que pasa el incidente. Patrón dos — EPP equivocado para el peligro. Hi-vis Clase 2 usada en trabajo nocturno donde se requiere Clase 3, lentes básicos usados al esmerilar donde se necesita careta, guantes de cuero usados cerca de químicos donde se requiere nitrilo. El arreglo es el foreman que trata el EPP como el piso, no la meta — y una cultura donde 'ya regreso' no es pase libre para quitarse el equipo.",
    hazards_reviewed:
      "Lesión en cabeza · Lesión ocular · Pérdida auditiva · Lesión en pie · Laceración de mano · Lesión por aplastamiento · Falta de hi-vis llevando a atropello",
    discussion_notes:
      "• Casco — Tipo II para zonas de tráfico / impacto; reemplazar cada 5 años o tras impacto.\n• Lentes de seguridad con protectores laterales — ANSI Z87 mínimo.\n• Hi-vis Clase 2 día / Clase 3 noche para todo trabajo de carretera.\n• Botas con punta de acero o composite — sin tenis.\n• Guantes resistentes a cortes para trabajo afilado / abrasivo.\n• Protección auditiva donde el ruido > 85 dBA TWA.\n• EPP inspeccionado antes de uso; EPP dañado fuera de servicio.",
    references_cited: "OSHA 1926 Subparte E · OSHA 1926.95 · ANSI Z87 / Z89 / Z41",
    action_items: "Inventario EPP · EPP dañado reemplazado · Clase de hi-vis · Protección auditiva disponible",
  },
  stop_work: {
    title: "Autoridad para Suspender el Trabajo",
    incident_pattern:
      "El patrón fatal que la Autoridad para Suspender Trabajo está diseñada para romper es el momento de 'tuve un mal presentimiento pero seguí adelante.' Cada revisión post-incidente de un evento serio en esta industria tiene la misma línea en algún lado: alguien en la cuadrilla pensó que algo estaba mal, no dijo nada, y el trabajador murió. El arreglo no es un cartel — es un foreman que ha respaldado demostrablemente a un miembro de cuadrilla que paró el trabajo en el pasado, así el resto de la cuadrilla cree que realmente puede. Stop Work es memoria muscular cultural. Las cuadrillas que la tienen en los huesos tienen menos fatalidades; las cuadrillas que la tienen en papel pero no en práctica son las que siguen apareciendo en los reportes de OSHA.",
    hazards_reviewed:
      "Peligro inminente ignorado · Presión de producción sobre seguridad · Condición peligrosa escalando · Cuasi-accidente no reportado",
    discussion_notes:
      "• CADA miembro de la cuadrilla tiene la autoridad y responsabilidad de suspender el trabajo por cualquier preocupación de seguridad.\n• Nadie será represaliado, nunca, por suspender de buena fe.\n• Proceso: Parar. Notificar. Corregir. Reanudar. — los cuatro pasos.\n• Documentar el evento de Stop Work para aprender.\n• Stop Work cubre tu trabajo, tu cuadrilla, el público — cualquiera expuesto.\n• Si no estás seguro, para. Mejor perder 5 minutos que un compañero.",
    references_cited: "Cláusula General de OSHA 5(a)(1) · Política Stop Work MASCI",
    action_items: "Cartel Stop Work visible · Cuadrilla reconoce autoridad · Eventos recientes revisados",
  },
  near_miss: {
    title: "Reporte de Cuasi-Accidentes",
    incident_pattern:
      "El mismo cuasi-accidente pasa 3-10 veces antes de convertirse en una lesión real. Eso no es estadística abstracta — es el patrón de las propias revisiones de incidentes de MASCI y de cada estudio de seguridad de los últimos 50 años. Trabajador suelta una llave del deck, cae 4 pies de un compañero, nadie reporta, dos semanas después la misma caída pega en un casco, luego un mes después la misma situación mata a un trabajador. El arreglo es reportar las lecciones GRATIS — los acercamientos donde nadie se lastimó. Se rastrean, las tendencias se arreglan, la lesión real nunca pasa. Las cuadrillas que reportan cuasi-accidentes honestamente tienen menos lesiones reales; las que los suprimen son las que generan el siguiente registro de OSHA.",
    hazards_reviewed:
      "Cuasi-accidentes recurrentes llevando a lesión real · Peligros no reportados · Datos de tendencia perdidos · Cultura de silencio",
    discussion_notes:
      "• Un cuasi-accidente es una lección gratis. Trátalo como una lesión que tuviste suerte de evitar.\n• Reporta cualquier acto inseguro, condición insegura o cercana — mismo turno.\n• Reporte anónimo disponible; sin represalias.\n• MASCI rastrea cuasi-accidentes para tendencias — así prevenimos el siguiente incidente.\n• No culpar al trabajador; corregir condición o proceso.\n• Ejemplos: herramienta cayó de altura, intrusión de vehículo, oscilación amplia de carga, casi tropiezo.",
    references_cited: "OSHA VPP · ANSI Z10 · Procedimiento Cuasi-Accidente MASCI",
    action_items: "Formulario disponible · Reporte revisado · Reportes recientes discutidos · Acciones correctivas rastreadas",
  },
  stretch_flex: {
    title: "Estiramiento y Calentamiento / Reunión Diaria",
    incident_pattern:
      "La mayoría de las lesiones de tejido blando en construcción pasan en los primeros 90 minutos del turno. El trabajador se baja del camión frío y tieso, salta directo a palear o cargar, y la espalda o el hombro ceden a las 7:30 a.m. Los registros de lesiones en MASCI y en toda la industria muestran la misma concentración matutina. El estiramiento no es sobre flexibilidad — es sobre meter sangre a músculos fríos antes de pedirles que hagan el trabajo. Cinco minutos salvan una lesión de espalda que termina una carrera. Las cuadrillas que lo saltan tienen reclamos de espalda/hombro/rodilla medibalmente más altos. La parte de la reunión también importa — el breve donde clima, apto-para-el-deber, y los peligros del día se nombran antes de que alguien toque una herramienta.",
    hazards_reviewed:
      "Esguinces y torceduras · Lesiones de tejido blando · Lesión muscular en frío · Movimiento repetitivo · Resbalones/tropiezos/caídas en la primera hora del turno",
    discussion_notes:
      "• Rutina de 5 minutos antes del trabajo — cuello, hombros, espalda, caderas, isquiotibiales.\n• Recorrer la lista de tareas e identificar algo nuevo o inusual.\n• Confirmar asignaciones de cuadrilla y equipo del turno.\n• Identificar preocupaciones del clima (calor, frío, rayos, viento, lluvia).\n• Confirmar todos aptos para el deber — sin discapacidad, enfermedad o fatiga.\n• Recordatorio rápido de seguridad relevante al trabajo de hoy.",
    references_cited: "MASCI Daily Huddle SOP · NIOSH Ergonomía",
    action_items: "Rutina de estiramiento completada · Tareas informadas · Revisión de clima · Aptos confirmados",
  },
  slips_trips: {
    title: "Resbalones, Tropiezos y Caídas (Mismo Nivel)",
    incident_pattern:
      "Las caídas al mismo nivel son el tipo de lesión más común en obra civil pesada — usualmente las que nadie comenta porque no llegan a reportes de OSHA. El trabajador atrapa una stringline con la punta del pie, cae mal sobre una muñeca, seis semanas de servicio ligero. El trabajador se baja de un talud sobre piedra suelta, el tobillo se rueda, seis meses de terapia. La versión fatal también existe — trabajador cargando un pedazo de tubería tropieza con una manguera, cae sobre una tapa de varilla, empalamiento. Las lesiones son predecibles: varilla, mangueras, stringlines, puntos suaves, hielo, mancha de aceite, pilas de escombros. El arreglo es orden rotado durante el día, no solo al final del turno — y botas con suela agresiva reemplazadas cuando se pulen lisas.",
    hazards_reviewed:
      "Resbalón en superficies húmedas/aceitosas/heladas · Tropiezo con mangueras, varilla, escombros · Caída en terreno desigual · Tobillo torcido por agujeros / suaves · Cargando con carga al caminar",
    discussion_notes:
      "• Causa #1 de lesiones en obra civil pesada — y la más prevenible.\n• Superficies despejadas de mangueras, cables, varilla — enrollar y apilar.\n• Caminos definidos y marcados a través de la obra.\n• Botas con suela agresiva; reemplazar cuando estén desgastadas.\n• No cargar cargas que bloqueen la vista de los pies.\n• Sal/arena o barrer hielo y escombros.\n• Agujeros cubiertos o barricadas — banderear terreno desigual.",
    references_cited: "OSHA 1926.25 · OSHA 1926.501 · NIOSH STF",
    action_items: "Caminos marcados · Cables/mangueras manejados · Agujeros cubiertos · Superficies mantenidas",
  },
  hand_injury: {
    title: "Prevención de Lesiones de Mano",
    incident_pattern:
      "Las manos son la parte del cuerpo más lesionada en construcción. El patrón que recurre es meter las manos sin guantes a un punto de pellizco porque los guantes 'estorbaban' — jalando una cinta métrica a una conexión, guiando un manojo de varilla, liberando un perno atorado. La mano va donde está la energía, y el resultado es una lesión por aplastamiento o desollamiento. Las amputaciones por equipo giratorio son menores en conteo pero cambian vidas — el trabajador mete la mano a una banda o sierra en movimiento para limpiar un atasco sin LOTO. El arreglo son guantes igualados al peligro (resistentes a cortes para afilado, con clasificación de impacto para material pesado), herramientas usadas para posicionar en vez de manos, y LOTO antes de cualquier servicio de equipo giratorio. 'Solo por un segundo' es la frase que cuesta dedos.",
    hazards_reviewed:
      "Laceraciones · Lesiones por aplastamiento (pellizcos) · Punciones · Quemaduras · Amputaciones por equipo giratorio · Esfuerzo repetitivo",
    discussion_notes:
      "• Igualar el guante al peligro — resistente a cortes para afilado, químico para químico, impacto para impacto.\n• Identificar pellizcos antes de alcanzar — usar herramientas para posicionar, no manos.\n• Empujar, no jalar — cuando jalar falla, tu mano va contra lo que jalas.\n• Nunca tocar disco, tambor o banda en movimiento — LOTO antes de servicio.\n• Inspeccionar herramientas a diario; remover dañadas de servicio.\n• Arrodillarse o usar plataforma estable para trabajo fino.",
    references_cited: "OSHA 1926.95 · Estadísticas BLS · Política de Seguridad de Manos MASCI",
    action_items: "Guantes apropiados · Pellizcos identificados · Herramientas inspeccionadas · LOTO informado",
  },
  hearing_conservation: {
    title: "Conservación Auditiva",
    incident_pattern:
      "La pérdida auditiva inducida por ruido es la lesión ocupacional más subcontada en construcción. Pasa gradualmente, sin dolor, y para cuando un trabajador nota que la TV necesita estar más alta y se está perdiendo el remate de los chistes, la audición de alta frecuencia ya se fue — permanentemente. La mayoría de la maquinaria pesada y la mayoría de operaciones de corte/esmerilado exceden 85 dBA TWA. El patrón es el trabajador que usaba tapones en sus 20s, perdió el hábito en sus 30s 'porque no parecía tan ruidoso,' y a los 50 necesita audífonos. Acorta carreras pero es invisible hasta que es irreversible. El arreglo son tapones O orejeras (AMBOS para martillo, tambor de milling, demolición), usados cuando el ruido cruza el umbral, y el audiograma anual que atrapa el cambio temprano antes de que sea pérdida.",
    hazards_reviewed:
      "Pérdida auditiva permanente inducida por ruido · Tinnitus · Dificultad de comunicación enmascarando otros peligros · Daño acumulativo de carrera",
    discussion_notes:
      "• Nivel de acción OSHA 85 dBA TWA — la mayoría de maquinaria pesada lo excede.\n• Tapones O orejeras — ambos para ruido de impacto (martillo, tambor de milling, demolición).\n• Reemplazar tapones de espuma diariamente; limpiar reusables a diario.\n• Audiograma anual por programa de conservación auditiva.\n• Vigilar señales tempranas: zumbido, subir TV, perder conversaciones.\n• Señales de mano silenciosas durante trabajo ruidoso; pre-arreglar comunicación.",
    references_cited: "OSHA 1926.101 · OSHA 1910.95 · NIOSH REL",
    action_items: "Protección disponible · Usada en ruido alto · Audiograma anual",
  },
  respiratory_protection: {
    title: "Protección Respiratoria",
    incident_pattern:
      "Los incidentes de exposición respiratoria tienen el retraso más largo entre causa y efecto de cualquier peligro de seguridad en construcción. El trabajador esmerila concreto o respira humo de asfalto en días calientes durante sus 20s y 30s, no usa el respirador porque está sudoroso y 'el polvo no está tan mal.' Silicosis o cáncer de pulmón aparecen en sus 50s. Para entonces la exposición fue hace 20 años y el trabajador no tiene recurso. Patrón dos — el cartucho equivocado. El trabajador agarra un P100 pensando que manejará vapores de solvente; no lo hará, vapor orgánico necesita un cartucho OV. Huele el solvente a través de la máscara, piensa que es problema de ajuste, cambia a otra máscara pero todavía con cartucho equivocado. El arreglo es ajuste vigente, cartucho igualado al contaminante vía SDS, superficie de sello bien afeitada, y la disciplina de realmente usarlo.",
    hazards_reviewed:
      "Sílice · Asbesto · Humos de soldadura · Solventes de asfalto/pintura · Diésel · CO · Moho / polvo · Ajuste inadecuado permitiendo exposición",
    discussion_notes:
      "• Respirador requerido cuando los controles de ingeniería sean insuficientes.\n• Prueba de ajuste anual — cuantitativa o cualitativa — registrada.\n• Autorización médica antes de uso de respirador.\n• Igualar cartucho al contaminante — P100 para partículas, OV para vapores orgánicos.\n• Inspeccionar antes de cada uso; verificación de sello en cada colocación.\n• Barba / vello facial rompe el sello — afeitado en superficie de sello.\n• Cartuchos tienen vida útil — cambiar según horario.",
    references_cited: "OSHA 1910.134 · OSHA 1926.103 · Certificación NIOSH",
    action_items: "Pruebas de ajuste · Cartuchos en stock · Procedimiento de sello · Horario de cambio",
  },
  hazcom_sds: {
    title: "Comunicación de Peligros / SDS",
    incident_pattern:
      "Los incidentes de HazCom pasan cuando un trabajador agarra un contenedor sin etiqueta pensando que es una cosa y es otra. Patrón uno — el contenedor de transferencia. El foreman decantó gasolina a una garrafa de líquido limpiaparabrisas la semana pasada para ahorrarse un viaje, no la etiquetó; trabajador nuevo la agarra pensando que es limpiaparabrisas, rocía a un compartimento de motor caliente, fuego. Patrón dos — la incompatibilidad de almacenamiento. Cloro de blanqueador y limpiador a base de amoniaco almacenados uno junto al otro en un tráiler de almacenamiento, un derrame los mezcla, gas cloramina en un espacio confinado. El arreglo no es glamoroso: cada contenedor etiquetado, cada químico con una SDS dentro de 30 segundos de donde se usa, y almacenamiento segregado que respeta las advertencias de la SDS (inflamables aparte de oxidantes, ácidos aparte de bases).",
    hazards_reviewed:
      "Exposición química a producto desconocido · EPP equivocado · Incompatibilidades de almacenamiento · Disposición inadecuada · Pictogramas mal interpretados",
    discussion_notes:
      "• Cada químico en sitio tiene SDS — accesible.\n• Leer SDS antes del primer uso: peligros, EPP, almacenamiento, primeros auxilios, respuesta a derrame.\n• Etiquetas intactas y legibles — sin contenedores de transferencia sin marcar.\n• 9 pictogramas GHS — saber qué significa cada uno.\n• Segregación: inflamables aparte de oxidantes, ácidos aparte de bases.\n• Disposición según SDS y EPA / requisitos estatales — no a drenajes.",
    references_cited: "OSHA 1926.59 · OSHA 1910.1200 · GHS",
    action_items: "Carpeta SDS vigente · Etiquetas revisadas · Segregación · Disposición identificada",
  },
  site_walk: {
    title: "Recorrido Diario del Sitio / Evaluación de Peligros",
    incident_pattern:
      "Las condiciones cambian de la noche a la mañana. La lluvia llena una zanja, la tormenta tira una barricada, un transeúnte jala conos por diversión, un subcontratista reubica una pieza de equipo sin avisar, un vehículo clipeó un letrero a las 2 a.m. El foreman que recorre el sitio ANTES de que llegue la cuadrilla atrapa todo eso; el foreman que se salta el recorrido se entera por las malas cuando un trabajador pisa donde no debía. El patrón que recurre — agua en una excavación que la cuadrilla asume está bien, suelos cediendo, colapso durante el día porque la saturación cambió la fuerza durante la noche. Lo mismo con escarcha en invierno — lo que estaba estable ayer está suelto hoy. El arreglo es el recorrido de 15 minutos antes de que cualquier cuadrilla toque una herramienta, con correcciones hechas e informadas en la reunión.",
    hazards_reviewed:
      "Nuevos peligros del trabajo de ayer · Cambios por clima (agua, escarcha, daño por viento) · Equipo / material movido · Invasión pública · Trabajo de servicios desde último turno",
    discussion_notes:
      "• Capataz recorre toda la zona de trabajo antes de que las cuadrillas inicien.\n• Buscar algo nuevo o diferente de ayer: agua en zanja, barricadas desplazadas, tumbados, robo, vandalismo.\n• Verificar que sistemas de protección sigan en lugar.\n• Verificar tropiezos por movimiento nocturno de equipo / material.\n• Reponer / reemplazar lo faltante o dañado antes de que las cuadrillas entren.\n• Documentar e informar hallazgos en la reunión.",
    references_cited: "MASCI Site Walk SOP · OSHA Persona Competente",
    action_items: "Recorrido completado · Hallazgos informados · Correcciones registradas",
  },
  housekeeping_cleanup: {
    title: "Limpieza y Orden al Final del Turno",
    incident_pattern:
      "El atajo de limpieza al final del turno crea tres problemas predecibles al día siguiente. Uno — los tropiezos dejados afuera se vuelven resbalones matutinos cuando la cuadrilla llega con poca luz. Dos — excavaciones abiertas o bordes sin guardar con mala barricada se vuelven una lesión pública durante la noche (los niños encuentran obras, los conductores ebrios encuentran obras). Tres — las herramientas y equipo pequeño dejado afuera se roban, y el trabajo del día siguiente se detiene por 90 minutos mientras llegan reemplazos. El arreglo es la disciplina de 15 minutos al final de cada turno — no negociable. Herramientas bajo llave, aberturas cubiertas o barricadas con luces, MOT verificado para configuración nocturna, y un recorrido final del sitio por el foreman.",
    hazards_reviewed:
      "Tropiezos por material dejado · Robo de herramientas / equipo no asegurado · Lesión pública por peligros abiertos · Contaminación de drenaje por derrames · Vandalismo / invasión",
    discussion_notes:
      "• 15 minutos de orden al final de cada turno — no negociable.\n• Herramientas y equipo pequeño bajo llave; equipo grande estacionado seguro.\n• Zanjas / estructuras abiertas cubiertas, barricadas, iluminadas.\n• Dispositivos MOT restaurados a configuración nocturna; luces revisadas.\n• Basura y escombros recogidos; sin plástico / desperdicio que pueda volar a drenajes.\n• Recorrer el sitio una última vez antes de salir.",
    references_cited: "OSHA 1926.25 · Estándar de Orden MASCI",
    action_items: "Herramientas aseguradas · Excavaciones cubiertas/iluminadas · MOT verificado · Recorrido completado",
  },
  new_hire_orientation: {
    title: "Orientación para Nuevos Contratados / Nuevos al Sitio",
    incident_pattern:
      "Los nuevos contratados y trabajadores nuevos en un sitio tienen tasas de lesión 3-5x más altas en los primeros 30 días que los trabajadores experimentados. El patrón es consistente en toda la industria: el trabajador nuevo no sabe cuál zanja ha sido perfilada, no sabe cuál puerta usan los camiones, no sabe que el extremo sur del sitio tiene una línea aérea activa, no sabe que el radio de giro de la excavadora en la esquina es la zona asesina. Caminan a algo que un trabajador experimentado habría rodeado. Patrón dos — el nuevo contratado que tiene miedo de usar la Autoridad para Suspender Trabajo porque es nuevo. Ven algo mal, no hablan porque no quieren parecer tontos en el día tres. El arreglo es la orientación formal con un recorrido del sitio, la asignación de compañero por 1-3 días, y el refuerzo explícito de que Stop Work les pertenece desde el minuto uno.",
    hazards_reviewed:
      "Desconocimiento de peligros del sitio · Equipo / procedimientos desconocidos · Mayor tasa de lesiones en primeros 30 días · EPP / capacitación faltante · Cultura desalineada en Stop Work",
    discussion_notes:
      "• CADA nuevo contratado y CADA persona nueva en el sitio recibe orientación específica del sitio.\n• Recorrer el sitio, señalar peligros, rutas de evacuación, botiquín, extintores.\n• Revisar TCP específico, JHP de su cuadrilla y permisos activos.\n• Reforzar Autoridad para Suspender Trabajo — la tienen desde el minuto uno.\n• Emparejar con compañero experimentado por 1-3 días.\n• Confirmar certificaciones / capacitación vigentes antes de iniciar.",
    references_cited: "OSHA 1926.21 · Procedimiento MASCI Nuevo Contratado",
    action_items: "Orientación completada · Compañero asignado · Registros de capacitación · Stop Work informado",
  },
  subcontractor_coordination: {
    title: "Coordinación con Subcontratistas",
    incident_pattern:
      "Las fatalidades multi-empleador siguen un patrón firma: cada contratista conoce sus propios peligros pero no sabe qué están haciendo los otros contratistas. Sub A está excavando; Sub B está haciendo trabajo de servicios aéreos arriba de la misma área. Sub A no sabe que Sub B está arriba hasta que algo cae. O — Sub C está haciendo hot work en una esquina, Sub D está reabasteciendo equipo en la siguiente esquina, los vapores encuentran la chispa. La política multi-empleador de OSHA responsabiliza al GC por lo que hacen los subs porque el GC es la única entidad que ve el cuadro completo. El arreglo es la reunión diaria de coordinación — quién está dónde, qué actividades, qué conflictos. Los subs siguen estándares de MASCI o más altos, nunca más bajos; la Autoridad para Suspender Trabajo se extiende a cada trabajador sin importar el gafete.",
    hazards_reviewed:
      "Actividades en conflicto · Desconocimiento mutuo de peligros · Diferentes estándares de seguridad · Falla de comunicación · Presión de horario sobre secuencia",
    discussion_notes:
      "• Cada sub en sitio ha tenido revisión pre-mob de seguridad con MASCI.\n• Reunión diaria de coordinación — quién está dónde, qué actividades, conflictos identificados.\n• Subs siguen estándares MASCI o más altos — nunca más bajos.\n• Autoridad MASCI para Suspender Trabajo se extiende a TODOS los trabajadores sin importar empleador.\n• JHP / plan pre-tarea compartido entre oficios en conflicto.\n• Incidentes reportados a MASCI mismo día.",
    references_cited: "Política OSHA Multi-Empleador · Pre-Cualificación MASCI",
    action_items: "Reps de seguridad sub identificados · Coordinación diaria · Stop Work extendido · JHPs compartidos",
  },
  emergency_action_plan: {
    title: "Plan de Acción de Emergencia / Evacuación",
    incident_pattern:
      "Las fallas de acción de emergencia durante eventos reales siguen guiones predecibles. Trabajador colapsa por insolación; la cuadrilla llama al 911 pero no le puede dar al despachador la dirección real porque el número de proyecto no es la misma dirección de la calle. La ambulancia pierde 8 minutos encontrando la puerta. Para cuando llegan, el trabajador se fue. O — incendio brota cerca de un camión de combustible; la cuadrilla evacúa pero nadie hace el conteo en el punto de reunión. Dos trabajadores que se creían evacuados están en realidad dentro del tráiler. El arreglo es el EAP publicado en cada sitio con la dirección 911, la info de acceso de puerta, el punto de reunión, y el sistema de compañero o registro que confirma cada trabajador contado. Ensáyenlo cada 90 días porque nadie recuerda un plan que nunca practicaron.",
    hazards_reviewed:
      "Emergencias del sitio (incendio, fuga de gas, clima severo, amenaza activa) · Evacuación inadecuada · Falla de contar personal · Salida bloqueada · Respuesta 911 demorada",
    discussion_notes:
      "• Cada sitio tiene un EAP publicado — punto de reunión, rutas primaria y secundaria, indicaciones 911, contactos en sitio.\n• Contar TODO el personal en el punto de reunión — sistema de compañero o registro.\n• Nunca re-entrar por herramientas, vehículos o material.\n• Quien llama al 911 permanece en línea; provee dirección del sitio e info de acceso.\n• Operadores apagan equipo seguramente si hay tiempo; si no, evacuar inmediatamente.\n• Ensayar el EAP cada 90 días o tras cambios mayores del sitio.",
    references_cited: "OSHA 1926.35 · NFPA 101 · Manejo Estatal / Local de Emergencias",
    action_items: "EAP publicado · Punto de reunión · Dirección 911 verificada · Ensayo programado",
  },
  fire_prevention: {
    title: "Prevención de Incendios y Uso de Extintores",
    incident_pattern:
      "Los incendios en obras usualmente empiezan pequeños y se hacen grandes rápido. La mayoría empieza en uno de tres lugares: un punto de combustible donde el vapor encuentra una fuente de ignición, una zona de hot work donde el vigilante de fuego se fue muy temprano, o una pieza de equipo donde una línea hidráulica falló y roció sobre un turbo. El patrón que mata trabajadores es la respuesta sin entrenamiento al extintor — el trabajador agarra un extintor por un fuego que ya es muy grande, agota la botella en 8 segundos, queda acorralado. Los extintores son para incendios del tamaño de un cesto con ruta de escape clara. Más grande que eso, salga y llame al 911. El otro patrón es el extintor equivocado — polvo químico ABC en un incendio de grasa no funciona, agua en un incendio eléctrico mata al trabajador. Sepa qué está en riesgo donde está el extintor, y sepa cuándo retirarse.",
    hazards_reviewed:
      "Ignición de hot work · Derrame de combustible / vapor · Fumar cerca de inflamables · Selección equivocada de extintor · Trabajador no entrenado peleando incendio · Incendio de vehículo/equipo",
    discussion_notes:
      "• Combustibles a 35 pies+ de hot work; extintor listo.\n• Polvo químico ABC para la mayoría de incendios; CO2 para eléctrico; espuma para combustibles.\n• PASS: Pull, Aim, Squeeze, Sweep — solo combatir incendio menor a un cesto y solo con ruta de escape clara.\n• En duda — sal y llama al 911.\n• No fumar cerca de combustible, grasa, solventes — solo áreas designadas.\n• Inspeccionar extintores mensualmente; recargar tras uso.",
    references_cited: "OSHA 1926 Subparte F · NFPA 10 · NFPA 51B",
    action_items: "Extintores inspeccionados · Técnica PASS · Áreas designadas · Permisos hot work",
  },
  general_lone_worker_field: {
    title: "Trabajador Solo / Operaciones en Campo Solo",
    incident_pattern:
      "Las fatalidades de trabajador solo tienen el patrón más cruel en construcción: pasa un incidente y nadie sabe por horas. El chofer se orilla en el acotamiento para lo que debe ser una revisión de 5 minutos, se resbala y cae a una alcantarilla o tiene un evento cardíaco, el vehículo se queda estacionado con intermitentes prendidas por medio día antes de que alguien note. El topógrafo camina un alineamiento solo, lo muerde algo venenoso, no tiene señal, se sienta en el matorral y no lo encuentran hasta la mañana siguiente. El estimador hace una visita a un proyecto cerrado, cae a una estructura parcialmente colapsada, tiene una pierna fracturada y una batería de celular muerta. El arreglo son protocolos obligatorios de check-in — tiempos designados, contactos designados, procedimiento de escalación cuando el check-in se pierde. El trabajo solo sin plan de check-in es lo que mata a estos trabajadores, no el incidente original.",
    hazards_reviewed:
      "Evento médico sin testigos · Resbalón/caída sin testigos en área remota · Zona sin señal de celular · Encuentro con vida silvestre solo · Falla de vehículo en área remota · Trabajo solo después del oscurecer · Check-in perdido",
    discussion_notes:
      "• Cada asignación de trabajador solo tiene horario designado de check-in: ej., 'envío texto a las 10:00, 12:00, 2:00, y cuando salga del sitio.'\n• Contacto designado del otro lado — supervisor, despachador o pareja. No solo 'alguien.'\n• Escalación si se pierde check-in: intentos de contacto, luego 911 si no responde en 30 minutos.\n• Cobertura celular verificada antes de salir de la oficina. Anotar zonas muertas.\n• Vehículo accesible — llaves en bolsillo, combustible arriba de la mitad, agua en cabina.\n• Hi-vis puesta aun para exposiciones cortas fuera del vehículo cerca de carretera.\n• 'Revisión rápida' que se vuelve tarea de 45 minutos es el patrón más peligroso. Actualice el check-in si cambia el alcance.\n• Conciencia de vida silvestre — serpientes, caimanes, perros — al trabajar solo.",
    references_cited: "Cláusula General de OSHA 5(a)(1) · MASCI Lone Worker SOP · ANSI/ISEA Z308",
    action_items: "Horario de check-in · Contacto designado · Procedimiento de escalación · Cobertura verificada",
  },
  general_line_of_fire: {
    title: "Conciencia de Línea de Fuego",
    incident_pattern:
      "La línea de fuego es el patrón universal bajo casi cada fatalidad de golpe-por y atrapamiento en construcción. El trabajador está en el lugar equivocado en el momento equivocado — entre el giro de una excavadora y un objeto fijo, detrás de un camión en reversa, bajo una carga suspendida, en el lado descendente de material almacenado que se mueve, en la trayectoria de una línea tensionada que rompe. La mayoría de las fatalidades no son porque el trabajador no sabía que era peligroso; son porque el trabajador no pensó que la línea de fuego le aplicaba a él en ese momento. 'Solo me meto dos segundos a amarrar esto.' El arreglo es disciplina mental: antes de pisar cualquier posición, pregunte 'si la energía se libera ahorita — el cucharón gira, la línea rompe, la carga cae, el material se mueve, la máquina se mueve — ¿a dónde va?' Si usted está en esa trayectoria, cambie de posición. Foremen y líderes de cuadrilla refuerzan el hábito hasta que es automático.",
    hazards_reviewed:
      "Entre equipo y objeto fijo · Bajo carga suspendida · Detrás de equipo en reversa · Dentro de radio de giro · Zona de retroceso de línea tensionada · Cuesta abajo de material almacenado · Dentro de zona de latigazo de manguera presurizada",
    discussion_notes:
      "• Antes de pisar en cualquier lado, pregunte: 'Si la energía se libera ahorita — la carga cae, el cucharón gira, la línea rompe, el material se mueve — ¿a dónde va?'\n• Si usted está en esa trayectoria, MUÉVASE antes de hacer la tarea.\n• Cargas suspendidas: nunca debajo, nunca en el arco de giro.\n• Equipo en reversa: nunca detrás sin contacto de spotter Y alarma.\n• Líneas tensionadas (aparejo, correas de remolque, fleje): párese fuera de la zona de retroceso (~1.5x el largo de la línea a cada lado).\n• Material almacenado en pendientes: párese cuesta arriba, no cuesta abajo, aun para 'solo ver.'\n• Mangueras presurizadas (bomba de concreto, hidráulica, agua a presión): fuera de la zona de latigazo, siempre.\n• Líder de cuadrilla refuerza el hábito en la reunión — '¿dónde está la línea de fuego?' en cada tarea.",
    references_cited:
      "Boletín OSHA Golpe-Por · Boletín OSHA Atrapamiento · MASCI Línea de Fuego SOP",
    action_items: "Hábito de pregunta de línea de fuego · Tareas revisadas · Zonas no-go marcadas · Refuerzo durante turno",
  },
};
