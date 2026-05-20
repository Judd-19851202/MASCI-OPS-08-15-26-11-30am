// Domain ES: paving · iter261 Phase H Batch 2 · 8 entries (3 uplift + 5 new)

export const TOPICS_PAVING_ES = {
  asphalt_paving: {
    title: "Operaciones de Asfalto Caliente y Pavimentación",
    incident_pattern:
      "Los incidentes de pavimentación se concentran en la parte trasera del camión — el lugar donde el hot mix transfiere de la caja al hopper a 300–325°F. El chofer abre la compuerta, el peón rastrillando la junta se acerca demasiado, y un derrame o una liberación súbita pone hot mix sobre su bota o su pierna. El asfalto se pega. La ropa de algodón conduce el calor a través. La quemadura es de grosor completo en segundos y el trabajador trata de quitarse la bota — llevándose la piel con ella. Patrón complicado: trabajadores en shorts, playeras o zapatos bajos en días de 95°F porque 'estaba muy caliente para pantalones.' Pantalones y botas de cuero son el seguro más barato en el tren de pavimentación. La incomodidad de mangas largas en un día caliente no es nada comparada con un injerto.",
    hazards_reviewed:
      "Quemaduras severas por hot mix (300°F+) · Quemaduras por tack/aceite/combustible · Inhalación de humos · Golpe-por paver, roller, camión · Atrapado entre roller y borde de pavimento · Estrés por calor",
    discussion_notes:
      "• Mangas largas, pantalones largos, guantes calificados para asfalto caliente, botas de cuero — aun con calor.\n• Sin contacto de piel con hot mix; trabajo de rastrillo upwind del penacho de humo.\n• Zonas no-go del paver y roller marcadas; spotters donde trabajadores se acercan a equipo.\n• Chofer reconoce a la cuadrilla antes de descargar; comunicación positiva con operador de screed.\n• Manejo de combustible y tack: contenedores con bonding, no fumar, extintor a 50 pies.\n• Programa de estrés por calor — agua, descanso, rotación de sombra. Foreman vigilando síntomas.\n• Si hot mix contacta piel: NO trate de quitarlo. Cubra con paño limpio y seco. ER inmediatamente.",
    references_cited: "OSHA 1926.95 PPE · Boletín NIOSH Asfalto · Seguridad NAPA",
    action_items:
      "PPE calificado para quemadura emitido · Zonas no-go marcadas · Monitoreo de estrés por calor activo · Extintor en sitio · Respuesta a quemadura revisada",
  },
  tack_prime_coat: {
    title: "Aplicación de Tack Coat / Prime Coat",
    incident_pattern:
      "Los incidentes de tack-coat casi siempre vienen de spray-back, no del camión rociando como se planea. El patrón: una boquilla tapada que el operador despeja a mano sin despresurizar la barra, una manguera doblada que se libera cuando un trabajador mueve un tambo, o un trabajador caminando a través del abanico porque no lo vio desde el ángulo equivocado. Tack a 140–160°F no mata, pero come piel y termina en ojos y bocas. Materiales cortados / emulsionados añaden riesgo de fuego cuando el camión está junto a un generador o un soplete. El arreglo más probado en campo: nadie en el sobre del abanico, nunca — aun cuando el operador dice 'está apagado.'",
    hazards_reviewed:
      "Quemaduras por tack caliente (140°F+) · Inhalación de humos · Resbalón en pavimento tackeado · Spray-back al operador/trabajador · Fuego / explosión de materiales cortados",
    discussion_notes:
      "• Mangas largas, guantes, protección ocular — sin piel expuesta durante el spray.\n• Materiales cortados son inflamables — sin fuentes de ignición, extintor armado.\n• Párese viento-arriba de la barra; boquilla probada a baja presión ANTES de aplicar.\n• Nunca despeje una boquilla tapada sin despresurizar la barra primero.\n• Tiempo libre-de-huella observado antes del tráfico — bandera si peatones o vehículos se acercan.\n• Equipo limpiado con solvente aprobado; kits de derrame listos.\n• Comunicación operador-cuadrilla verificada antes de mover el camión.",
    references_cited: "OSHA 1926.59 (HazCom) · Mejores Prácticas Tack NAPA",
    action_items:
      "PPE de quemadura · Extintor armado · Comunicaciones probadas · Kit de derrames listo · Regla de despresurizar-antes-de-despejar reforzada",
  },
  joint_sealing: {
    title: "Sellado de Juntas — Vertido Caliente y Frío",
    incident_pattern:
      "Las quemaduras por sellado de juntas pasan en dos momentos predecibles: vertiendo de la caldera cuando la varilla es muy corta y el trabajador se asoma para dirigir el vertido, y rellenando la caldera de un melt pot cuando la tapa está parcialmente abierta y un salpicón llega a la cara. El sellador caliente corre a 380–400°F. Una gota en un antebrazo es una quemadura seria de segundo grado antes de que pueda sacudírsela. El otro incidente recurrente es el calentador de propano de mochila usado dentro de una carpa o granero — acumulación de CO en minutos, trabajador desmayado, caldera todavía corriendo. El arreglo son los básicos — varillas largas, careta completa sobre goggles, propano solo afuera, y nunca trabajar una caldera solo.",
    hazards_reviewed:
      "Quemaduras de sellador caliente 380°F+ · Inhalación de humos / vapor · Resbalón en junta recién sellada · Ruptura por presión de quemador de mochila / caldera · Fuego por solvente (vertido frío) · Envenenamiento por CO de propano adentro",
    discussion_notes:
      "• Vertido caliente: guantes térmicos, mangas largas, careta sobre lentes de seguridad al verter.\n• Pistola de vertido de varilla larga — NO se asome sobre la caldera para dirigir flujo.\n• Liberación de presión de caldera verificada antes de cada turno; nunca modifique dispositivos de seguridad.\n• Calentador de mochila de propano solo afuera — nunca en granero, carpa o trailer.\n• Control de humos — trabaje viento-arriba; protección respiratoria si los humos irritan.\n• Solvente de vertido frío: revise SDS, no fumar, contenedores aterrizados.\n• Sellador fresco abanderado hasta curarse.\n• Regla de dos personas en la caldera. Nunca solo.",
    references_cited:
      "OSHA 1926.59 · Manual de Operación del Fabricante · NFPA 58 (Propano)",
    action_items:
      "PPE térmico emitido · Caldera inspeccionada · SDS revisado · Señalización zona-curada · Regla de dos-en-la-caldera reforzada",
  },
  paving_paver_blind_spots: {
    title: "Puntos Ciegos del Paver — Interfaz Cuadrilla del Screed y Operador",
    incident_pattern:
      "Las fatalidades del paver casi siempre pasan en la misma zona de 4 pies — entre la parte trasera del camión descargando y el frente del hopper del paver. El chofer del camión está viendo el hopper, el operador del paver está viendo el screed, y un peón se mete a lutear una esquina o arreglar una junta. Nadie lo ve. El chofer suelta el freno para avanzar a la posición de siguiente carga, el paver avanza para mantener la junta, y el peón queda atrapado entre las dos máquinas. La otra variante es la cuadrilla de rake/lute trabajando alrededor de las alas del screed cuando el paver gira para ensanchar — pisan atrás al punto ciego del operador en el filo exterior del ala. El arreglo es protocolo de grito: cualquier trabajador dentro de 6 pies de las alas del paver o la zona de transferencia camión-hopper grita su posición EN VOZ ALTA al operador antes de entrar, y el operador reconoce EN VOZ ALTA.",
    hazards_reviewed:
      "Pellizco entre camión y paver durante avance · Golpeado por ala del screed extendiéndose · Atropello por camión en reversa a posición · Aplastado en ciclo de pliegue del hopper · Trabajador en zona de rake invisible detrás de ala extendiéndose",
    discussion_notes:
      "• Protocolo de aviso verbal — peón entrando a zona delantera del paver grita 'AL FRENTE' antes de entrar. Operador responde 'LIBRE.' Sin entradas silenciosas.\n• Las alas del paver son peligros de cámara lenta. Cuando el ala se extiende, todo ese arco es no-go para trabajadores en tierra.\n• Interfaz camión-paver: solo el foreman o spotter designado señala al camión para abrir la compuerta. Sin señales libres del peón.\n• Operador de screed para el screed antes de que cualquier trabajador se asome a lutear la junta. Punto. No 'la mayoría.' Cada vez.\n• Cinta reflectiva en mangos de rake ayuda al operador a atraparlos en visión periférica.\n• Peones nuevos caminan el tren con el foreman antes de tocar un lute. Cada punto de pellizco mostrado.\n• Contacto visual a través del vidrio de cabina antes de meterse al marco del operador.\n• Radio para trabajo de noche y ruido — las llamadas de voz no se llevan sobre un paver a tope.",
    references_cited:
      "OSHA 1926.602 · Seguridad de Tren de Pavimentación NAPA · SOP de Pavimentación MASCI",
    action_items:
      "Protocolo de aviso verbal reforzado · Zona no-go de arco de ala marcada · Hábito de parar-screed-antes-de-lutear verificado · Recorrido del paver para nuevo programado",
  },
  paving_roller_pinch_zones: {
    title: "Zonas de Pellizco del Roller — Retroceso y Aplastamiento en Borde de Mat",
    incident_pattern:
      "Las fatalidades por aplastamiento de roller son algunos de los incidentes más prevenibles y más repetidos en pavimentación. El operador va y viene en el mat, la visibilidad desde la cabina es limitada hacia atrás (especialmente en rollers más viejos de tambor liso sin cámara), y un peón pisa al mat para hacer un toque rápido. El operador retrocede, el peón está de espaldas, la velocidad de cierre es 3 mph — y un tambor de 10 toneladas no se detiene. La mayoría de las fatalidades no involucran al trabajador siendo atropellado de frente; es el golpe de reversa. Factor complicado: rollers corriendo cerca del borde del mat, donde el operador se enfoca en la línea y no en el peón a 8 pies adelante. El arreglo es rígido — nadie en el mat detrás de un roller en movimiento, nunca, y cada roller retrocede solo con la cabeza del operador volteada 180°.",
    hazards_reviewed:
      "Trabajador atropellado por roller en reversa · Aplastamiento entre dos rollers en patrón escalonado · Atrapado entre tambor del roller y drop-off del borde · Pellizco en toggle de vibración / pivote · Caídas del roller durante subir/bajar",
    discussion_notes:
      "• NADIE en el mat detrás de un roller en movimiento. Punto. Toques pasan entre pasadas, no durante.\n• Operador mira 180° atrás ANTES de meter reversa. Alarma de reversa funcional cada turno.\n• Operaciones escalonadas (multi-roller) — operadores coordinan verbalmente por radio, NO solo por espejos.\n• Borde del mat: el roller queda 6 pulgadas del drop hasta que la junta esté armada. Un tambor colgando sobre el borde puede tirar al operador por un cordón.\n• Toggle de vibración es solo del operador — ningún peón sube a la cabina a moverlo.\n• Subir/bajar solo en parada total, freno de mano engranado, nunca con motor corriendo y freno suelto.\n• Radio para noche y trabajo ruidoso — señales visuales fallan a distancia.\n• Regla operador-a-cuadrilla: si no los puede ver, no se mueve. Haga contacto visual primero.",
    references_cited:
      "OSHA 1926.602 · Operaciones de Roller NAPA · SOP de Pavimentación MASCI",
    action_items:
      "Regla de nadie-en-mat-detrás-de-roller reforzada · Verificación de alarma de reversa por turno verificada · Protocolo de radio escalonado establecido · Disciplina de subir/bajar revisada",
  },
  paving_asphalt_transfer_burn: {
    title: "Quemaduras en Transferencia de Asfalto — Camión a Hopper del Paver",
    incident_pattern:
      "Las quemaduras de transferencia al hopper son lo suficientemente comunes que la mayoría de foremen de pavimentación han visto una. El chofer retrocede al paver, el peón guía con señales de mano, y durante el descargue la compuerta abre muy rápido o el camión rueda ligeramente adelante para aliviar peso. El hot mix a 310°F+ se sale, salpica del delantal, y golpea a quien esté más cerca — usualmente las piernas del operador de screed o las botas del peón. Menos común pero peor: un peón al frente del paver durante un descargue es golpeado por una ola de derrame cuando el hopper se llena pasando el borde. La ropa de algodón conduce el calor. Las botas de cuero o resisten o se quitan rápido; los tenis se derriten. El arreglo es no glamoroso — descargas lentas, nadie en la zona de salpicón, y PPE completo en cada transferencia.",
    hazards_reviewed:
      "Quemadura por salpicón de derrame al llenar hopper · Avance del camión durante descargue · Quemadura de pie/pierna por calzado bajo · Quemadura de piel por ropa de algodón · Salpicón ocular por rebote del delantal",
    discussion_notes:
      "• Tasa de descargue LENTA. El chofer controla la compuerta. Operador del paver también controla tiempo de pliegue del hopper.\n• Ningún peón dentro de 6 pies del delantal del hopper durante un descargue. Punto.\n• Pantalones largos, botas de cuero — aun en el día más caliente. Tenis y shorts no tienen lugar en un tren de pavimentación.\n• Protección ocular (lentes de seguridad mínimo, careta preferida para operador de screed).\n• Chofer verifica freno de mano Y cuñas si la pendiente es más que unos grados. Un camión rodando durante descargue es riesgo de fatalidad.\n• Spotter señala al camión PARAR antes del descargue, no durante. Una vez fluyendo, sin más señales — deje que el descargue termine.\n• Si hot mix golpea piel: cubra con paño limpio y seco. NO trate de removerlo. ER inmediatamente.\n• Barra el delantal entre camiones — material apelmazado en el delantal desvía el siguiente salpicón.",
    references_cited:
      "OSHA 1926.95 · SOP de Tren de Pavimentación NAPA · Manejo de Hot Mix MASCI",
    action_items:
      "PPE para trabajadores de transferencia verificado · Zona de salpicón de 6 ft reforzada · Política de cuñas revisada · Respuesta a quemadura ensayada",
  },
  paving_night_fatigue: {
    title: "Pavimentación Nocturna — Fatiga, Iluminación y Calidad de Decisión",
    incident_pattern:
      "Los incidentes de pavimentación nocturna no son aleatorios — se concentran entre 2 a.m. y 4 a.m. La cuadrilla ha estado de pie 8 horas, comió a las 11 p.m., y su calidad de decisión está medibalmente impedida para entonces. El operador juzga mal una reversa de roller. El peón pisa la zona equivocada. El chofer retrocede a un objeto fijo. Complicando la fatiga está el problema del cono de luz: las luces de globo en el paver lanzan 30 pies de brillo, y el público en el siguiente carril ve solo un halo. Los trabajadores caminando fuera de la zona iluminada son invisibles. Añada lluvia fría a las 3 a.m. y la tasa de falla se duplica. El patrón se previene con rotación disciplinada de descansos, iluminación distribuida, y una hora de paro duro a las 5 a.m. para cualquier trabajo no urgente.",
    hazards_reviewed:
      "Error de operador inducido por fatiga · Trabajador en zona sin luz golpeado por equipo o vehículo · Choque en el camino a casa · Exposición fría/mojada compuesta con fatiga · Impedimento por sobre-uso de estimulantes (energy drinks, cafeína) · Inatención de chofer público en la noche",
    discussion_notes:
      "• Rotación obligatoria de descansos cada 2 horas. Siéntese, hidrátese, coma. Foreman aplica.\n• Iluminación distribuida — no solo en el paver. Ilumine la zona de rake, la zona de entrada de camión, la posición del cono-tender.\n• Hi-vis Clase 3 (no Clase 2) para la noche. Cinta reflectiva en piernas y brazos.\n• No más de UN energy drink por noche. El bajón de estimulante a las 4 a.m. es peor que sin estimulante.\n• Foreman vigila a cada miembro por reacciones lentas, irritabilidad, ojos vidriosos — señales de fatiga peligrosa. Mándelo al camión si necesario.\n• El riesgo del camino a casa es real. Si alguien está arrastrándose, no maneja a casa. Consígale aventón, hotel, o un sofá.\n• Hora de paro duro. Si el trabajo no termina para entonces, no termina. Calidad y vidas ambos degradan después de 12 horas.\n• Frío/mojado añade 30% a la carga de fatiga. Planee para ello.\n• Tráfico público nocturno maneja PEOR que de día. Trate cada intrusión como inminente.",
    references_cited:
      "NIOSH Total Worker Health · Estudios CDC de Fatiga · MUTCD Parte 6 Noche · SOP Pavimentación Nocturna MASCI",
    action_items:
      "Rotación de descansos aplicada · Iluminación distribuida verificada · Hi-vis Clase 3 requerida · Contingencia de camino a casa discutida · Hora de paro duro fijada",
  },
  paving_stringline_trip: {
    title: "Tropezones de Stringline y Estacas de Cimbra",
    incident_pattern:
      "Los tropezones de stringline son la lesión de tiempo-perdido más común en pavimentación y la más fácil de descartar. El patrón: un peón caminando entre el paver y el camión pasa sobre la stringline una vez, dos, luego falla a la tercera — atrapa la punta del pie y cae duro. Estacas de cimbra puestas a 18 pulgadas en un vertido de cordón-cuneta se vuelven un bosque de peligros una vez oscurece o una vez el trabajador está fatigado. La lesión usualmente es tobillo, rodilla o muñeca cuando se atrapan. Las caídas al mismo nivel son el tipo de lesión más frecuente en obra civil pesada en general, y las stringlines específicamente generan una parte desproporcionada. El arreglo es pequeño pero real — bandera de color en cada línea, ilumine cada estaca, rute trayectos alrededor del layout, no a través.",
    hazards_reviewed:
      "Tropezón con stringline a nivel de suelo · Tropezón con estaca de cimbra en layout cordón-cuneta · Tobillo / rodilla torcida · Fractura de muñeca al atrapar caída · Caída de herramienta sobre pavimento durante caída · Resbalón en mat recién puesto durante el tropezón",
    discussion_notes:
      "• Stringline lleva bandera hi-vis cada 10 pies. No opcional.\n• Estacas de cimbra llevan tapa o cinta fluorescente — visible de noche y en polvo.\n• Defina trayecto de caminata alrededor del layout, no a través. Marque con cinta si necesario.\n• Cinturones de herramientas y bolsas aseguradas — una herramienta colgando atrapa líneas también.\n• No cargue material Y camine por el layout. Dos viajes es mejor que una caída.\n• Trabajo de noche complica esto — añada conos con luz o tiras LED a lo largo del layout.\n• Si tropieza y se atrapa, repórtelo — aun si 'se siente bien.' Esguinces y dolores se vuelven lesiones 12 horas después.\n• Cuadrilla de layout camina el área al final del turno y jala lo no necesario. No deje bosques de estacas durante la noche.",
    references_cited:
      "OSHA 1926.500 (resbalones/tropezones) · Seguridad de Layout NAPA · SOP de Pavimentación MASCI",
    action_items:
      "Banderillado de stringline verificado · Tapas para estacas emitidas · Trayecto de caminata definido · Cultura de reporte de casi-accidente reforzada",
  },
};
