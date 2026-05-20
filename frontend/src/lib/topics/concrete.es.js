// Domain ES: concrete · iter261 Phase H Batch 2 · 12 ES translations (con incident_pattern)

export const TOPICS_CONCRETE_ES = {
  drilled_shaft: {
    title: "Operaciones de Perforación / Cajones",
    incident_pattern:
      "Las fatalidades en perforación de pilotes se dividen en dos patrones. Primero — un pozo abierto se deja sin cubrir mientras la cuadrilla sale a comer, o queda barricado solo con cinta de precaución, y un trabajador camina por encima y cae adentro. Una caída de 20 pies a lodo húmedo es insobrevivible sin rescate inmediato. Segundo — la barra Kelly o la jaula de varilla balanceándose hacia la cuadrilla en tierra durante la colocación. El operador del rig se enfoca en el pozo, la cuadrilla se enfoca en la jaula, y alguien se mete al arco de giro para hacer un amarre final. El arreglo es rígido: pozos cubiertos o barricados rígidos en el momento que la broca sale, radio de giro marcado en el suelo, y un solo señalero en el rig.",
    hazards_reviewed: "Caídas a pozo abierto · Colapso de pared · Golpe por barra Kelly · Sepultamiento por colapso de lodo/casing · Volcadura de grúa/perforadora · Oscilación de carga suspendida",
    discussion_notes: "• Pozos abiertos SIEMPRE cubiertos o barricadas; nunca dejar abiertos sin atender.\n• Cuadrilla en tierra fuera del radio de giro de la perforadora.\n• Trabajadores fuera del alcance de barra y casing suspendidos.\n• Manejo de lodo — EPP químico, protección contra salpicaduras, lavaojos a 25 pies.\n• Señalero capacitado para apoyo de grúa; aparejador certificado para jaulas y casings.\n• Riesgos de tropiezo (varilla, mangueras, líneas de lodo) controlados.",
    references_cited: "OSHA 1926 Subparte P · OSHA 1926 Subparte CC · DFI Drilled Shaft Safety",
    action_items: "Pozos cubiertos/barricadas · Radio de giro marcado · Señalero designado · EPP para lodo listo",
  },
  saw_cutting: {
    title: "Corte de Pavimento con Sierra",
    incident_pattern:
      "Los incidentes de corte con sierra están dominados por dos problemas: exposición a sílice que no duele hasta dentro de 10 años, y retroceso del disco en tiempo real. El patrón de retroceso es consistente — el operador empuja la sierra en un punto duro demasiado rápido, el disco se atasca, la sierra salta hacia atrás a las piernas. Las botas de punta de acero detienen el cuerpo de la sierra; nada detiene un disco mojado de 14 pulgadas atrapando un muslo. El segundo más común es operar viento-abajo del corte sin protección respiratoria 'porque el rociador de agua estaba prendido' — pero si las boquillas están tapadas o el tanque de agua está bajo, el penacho de sílice es invisible a la cara del operador. El arreglo es marcar la línea en seco, agarre con dos manos, y protección respiratoria como respaldo siempre que el agua sea el control primario.",
    hazards_reviewed: "Sílice respirable · Cortes / amputaciones por disco · Retroceso (kickback) · Ruido · Calor / disco caliente · Golpe por tráfico · Contaminación por lechada",
    discussion_notes: "• Corte mojado siempre que sea posible — supresión con agua es control de Tabla 1 de OSHA.\n• Cuando el corte seco sea necesario: aspiradora HEPA Y protección respiratoria.\n• Inspeccionar disco antes de cada uso; descartar discos agrietados.\n• Agarre con dos manos; sin extender brazos; pie firme.\n• Protección auditiva — sierras de pavimento exceden 100 dBA.\n• Lechada: contenerla; no dejar correr a drenaje (violación NPDES).\n• Protección de ojos + cara contra astillas.",
    references_cited: "OSHA 1926.1153 (Sílice Tabla 1) · OSHA 1926.300 · OSHA 1926.95",
    action_items: "Equipo de corte mojado · Respirador si seco · Contención de lechada · EPP auditiva y facial · Disco inspeccionado",
  },
  curb_gutter: {
    title: "Operaciones de Cordones y Cunetas",
    incident_pattern:
      "Las lesiones de cordón y cuneta son usualmente espalda, rodilla y mano — el tipo de daño lento que termina carreras sin nunca aparecer en un reporte de incidente. Los acabadores a mano pasan 6-8 horas inclinados sobre concreto fresco, las quemaduras químicas se acumulan por contacto con concreto húmedo a través de guantes de algodón, y a la mañana siguiente las manos están agrietadas y sangrando. El riesgo de fatalidad por patrón es más bajo que en otros dominios de concreto pero el costo de lesión de por vida es el más alto. El patrón de golpe-por que SÍ mata cuadrillas de cordón es la máquina slip-form — el operador juzga mal la zona de pellizco alrededor del tornillo sin fin o la regla y un acabador mete la mano para arreglar un defecto con la máquina todavía moviéndose. El arreglo es guantes y botas impermeables, no meter mano a un slip-form corriendo, y rotar la cuadrilla cada par de horas para reducir el sobreuso de inclinarse y acabar.",
    hazards_reviewed: "Pellizcos en máquina slip-form · Contacto con concreto caliente/húmedo · Doblar y levantar repetitivo · Golpe por tráfico · Sílice de cortar concreto · Quemaduras químicas",
    discussion_notes: "• Trabajadores fuera de zona prohibida de slip-form — buffer típico de 6 pies.\n• Cuadrilla de acabado con guantes y botas impermeables; enjuagar contacto con piel inmediatamente.\n• Levantar / mover formas con mecánica adecuada — carga cerca, rodillas dobladas.\n• Trabajo de borde cerca de tráfico = protección positiva (mínimo línea de tambores, barrera preferida).\n• Corte de juntas sigue controles de sílice (Tabla 1).\n• Disponer concreto residual correctamente; no a drenajes.",
    references_cited: "OSHA 1926 Subparte Q · OSHA 1926.1153 · NIOSH Boletín de Trabajadores de Concreto",
    action_items: "EPP impermeable · Zona prohibida marcada · Plan de levantamiento · Controles Tabla 1 de sílice",
  },
  mse_wall: {
    title: "Construcción de Muro MSE / de Retención",
    incident_pattern:
      "Las fatalidades de muro MSE vienen de dos fuentes: caída de paneles durante la colocación y colapso del pie del muro por setback inadecuado de compactación. El patrón de caída de panel — un panel precolado de 2 toneladas suspendido de la grúa, líneas guía parcialmente desplegadas, un trabajador se mete a guiarlo a casa, el viento agarra la cara. El panel oscila 4 pies, atrapa al trabajador contra el pilote soldado. El patrón de colapso de pie del muro — el equipo de compactación corriendo muy cerca de un muro verde (relleno suelto, paneles aún no cosidos al refuerzo del suelo), el pie se desplaza hacia afuera, y el muro empieza a fallar hacia arriba. La cuadrilla encima es la población en riesgo. El arreglo son los planos del ingeniero, tratados como evangelio: setbacks de compactación, alturas de capas, secuencia de cosido de paneles.",
    hazards_reviewed: "Caídas desde paneles · Golpe por panel · Pellizco/aplastamiento al instalar tiras · Inestabilidad de borde de relleno · Lesiones por manejo de material",
    discussion_notes: "• Líneas guía controlan rotación de paneles.\n• Trabajadores tras paneles protegidos; fuera del radio de giro.\n• Tie-off al trabajar en bordes de 6 pies+; barandillas conforme crece el muro.\n• Equipo de compactación a distancia del frente según diseño.\n• Tiras de refuerzo desenrolladas con herramientas, no a mano.\n• Pie del muro estable antes de la siguiente capa.",
    references_cited: "OSHA 1926 Subparte M · AASHTO LRFD · NCMA Design Manual",
    action_items: "Líneas guía listas · Protección contra caídas 6 pies+ · Setbacks de compactación · Plan de levantamiento",
  },
  concrete_silica: {
    title: "Operaciones de Concreto y Sílice Respirable",
    incident_pattern:
      "El sílice es el asesino lento de las cuadrillas de concreto. Los trabajadores pasan carreras cortando, esmerilando, picando, martillando — nada de lo cual se siente peligroso en el momento. El polvo parece polvo normal de obra. El daño pulmonar se acumula durante décadas. Cuando aparece la silicosis o cáncer de pulmón, el trabajador tiene 50 y pico y la exposición fue en los 80s y 90s. Patrón compuesto: la boquilla de corte mojado estuvo 'casi funcionando' todo el verano; la manguera de aspiradora HEPA estuvo desconectada por una semana; el respirador estaba colgado en el gancho pero no puesto porque 'da sudor.' La Tabla 1 de OSHA detalla los controles para cada tarea. El atajo es la silicosis. Mojar, aspirar, respirar — en ese orden.",
    hazards_reviewed: "Sílice cristalina respirable (silicosis, cáncer de pulmón) · Quemaduras cáusticas por concreto húmedo · Irritación de piel/ojos · Empalamiento por varilla · Colapso de cimbras · Lesiones por levantar",
    discussion_notes: "• Tabla 1 de OSHA — emparejar cada tarea generadora de polvo con su control de ingeniería (agua O vacío).\n• Protección respiratoria (P100 o aire suministrado) cuando los controles sean insuficientes.\n• Guantes, botas, mangas impermeables con concreto húmedo; enjuagar contacto con piel inmediatamente.\n• Tapas de varilla en cada extremo expuesto a altura de tropiezo o menos.\n• Cimbras inspeccionadas y arriostradas antes de la colada.\n• Protección ocular obligatoria al cortar, esmerilar, aserrar, picar.",
    references_cited: "OSHA 1926.1153 · OSHA 1926 Subparte Q · NIOSH Boletín de Sílice",
    action_items: "Controles Tabla 1 · Sistemas de agua/vacío revisados · Respiradores ajustados · Tapas de varilla",
  },
  concrete_pumping: {
    title: "Bombeo de Concreto",
    incident_pattern:
      "Las fatalidades por bomba de concreto vienen del contacto del brazo con líneas aéreas y del latigazo de línea después de que una obstrucción se libera violentamente. El patrón aéreo: el operador extiende el brazo en un trabajo residencial, no revisa completamente arriba, contacta un servicio de 13kV. La electrocución viaja por el camión bomba. Toda la cuadrilla dentro de 30 pies está en riesgo por potencial de paso. El patrón de latigazo de línea: una obstrucción se acumula, el operador invierte para limpiar, luego avanza muy agresivo. El tapón sale disparado, todo el brazo latiga hacia abajo en un arco de retroceso, y el trabajador en el extremo de la manguera está en la zona del balanceo. El 100% de estas fatalidades son prevenibles a través de verificación de espacio libre + limpieza lenta de obstrucción + nadie en el arco de giro del brazo.",
    hazards_reviewed: "Latigazo / falla de línea · Golpe por manguera · Quemaduras cáusticas por aerosol · Volcadura de bomba · Contacto con línea aérea · Tapón causando falla",
    discussion_notes: "• Outriggers totalmente extendidos sobre zoquetes; capacidad del suelo confirmada.\n• Mantener distancia de líneas aéreas — mínimo 10 pies (más para alto voltaje).\n• Manguero fuera de zona de latigazo potencial; comunicaciones con operador.\n• Protección de ojos/cara obligatoria — fittings rotos rocían cemento a presión.\n• Despejar tapones invirtiendo, nunca desconectando bajo presión.\n• Cadenas de seguridad en todas las conexiones de abrazadera.",
    references_cited: "ACPA Concrete Pump Safety · OSHA 1926.701 · OSHA 1926.405",
    action_items: "Outriggers · Altura libre · EPP facial · Comunicaciones probadas · Cadenas de seguridad",
  },
  formwork: {
    title: "Seguridad en Cimbra",
    incident_pattern:
      "Las fatalidades por colapso de cimbra son catastróficas y de múltiples víctimas. El patrón: una cimbra de viga profunda o una cimbra de losa se sobre-prepara por conveniencia de la cuadrilla, las cargas de diseño no se verificaron para la cabeza real de concreto, y la colada comienza. En el momento que el concreto fresco alcanza una profundidad crítica, el arriostre falla — usualmente un puntal o un tirante cediendo y el resto cascada. La colada está pasando, los trabajadores están en el deck o debajo del deck, y el colapso se lleva la cimbra, el concreto y los trabajadores juntos. En toda la industria, el colapso de cimbra es uno de los eventos individuales con más fatalidades porque no hay tiempo de escape. El arreglo son los planos del ingeniero, tratados como inviolables, inspección de persona competente pre-colada de cada arriostre y tirante, y sin desviaciones sin re-ingeniería.",
    hazards_reviewed: "Colapso de cimbra · Caídas desde cimbra · Golpe por cimbra cayendo · Pellizco/aplastamiento al desencofrar · Empalamiento por varilla · Falla de hardware bajo carga",
    discussion_notes: "• Cimbra diseñada por persona calificada para la carga (concreto + trabajadores + equipo).\n• Sin desviaciones del plano sin aprobación del ingeniero.\n• Inspeccionar cimbra antes de la colada — cada arriostre, tirante, puntal.\n• Trabajadores con tie-off al trabajar a 6 pies+.\n• Desencofrado: solo después de que el concreto alcance la resistencia requerida; zonas de caída controladas.\n• Tapas de varilla en todos los extremos expuestos; sin caminar sobre la malla superior sin tablones.",
    references_cited: "OSHA 1926.703 · ACI 347 Cimbra · OSHA 1926.703(b)",
    action_items: "Planos en sitio · Inspección pre-colada · Resistencia para descimbrar · Tapas de varilla",
  },
  bridge_deck_pour: {
    title: "Coladas de Tablero de Puente",
    incident_pattern:
      "Las fatalidades en tableros de puente están dominadas por caídas de borde. Una colada de tablero involucra horas largas, fatiga, calor, y un perímetro alrededor del cual la cuadrilla ha estado trabajando todo el día. Para la hora 8, la conciencia del borde se resbala, un trabajador pisa muy cerca de la fascia, y la caída es de 40+ pies sobre rocas, equipo, o tráfico en movimiento abajo. El otro patrón fatal son caídas A TRAVÉS del deck — aberturas de cimbra para penetraciones de servicios o juntas de expansión dejadas sin cubrir durante la colada. Un trabajador caminando el deck mojado pisa donde no hay cimbra. Ambos patrones comparten un arreglo: barandilla perimetral o sistema personal completo de detención de caídas antes de cualquier trabajo en deck, cada abertura cubierta o barricada, y rotación para manejar la fatiga en coladas de múltiples horas.",
    hazards_reviewed: "Caídas por borde · Caídas por aberturas · Golpe por máquina de acabado · Aerosol de concreto · Tropiezo/empalamiento por varilla · Estrés térmico en coladas largas",
    discussion_notes: "• Barandilla perimetral o PFAS completo antes de cualquier trabajo en tablero.\n• Cubrir o barricadas todas las aberturas.\n• Zonas prohibidas de máquina de acabado marcadas; comunicaciones operador-cuadrilla.\n• Plan de estrés térmico activo — agua, hielo, sombra, rotación.\n• Briefing de cuadrilla: secuencia de colada, ubicación de descarga, comunicación con conductores de mezcladora.\n• Protección de borde en fascia hasta colar parapeto.",
    references_cited: "OSHA 1926 Subparte M · OSHA 1926.502 · AASHTO Construcción de Puentes",
    action_items: "Protección de borde · Aberturas cubiertas · Plan de calor · Secuencia informada",
  },
  curing_sealing: {
    title: "Curado y Sellado",
    incident_pattern:
      "Los incidentes de curado y sellado son mayormente exposición química y peligros de resbalón. El patrón es un trabajador rociando un curado a base de solvente en un día caliente, sin respirador, la deriva del aplicador con el viento, dolor de cabeza para el almuerzo, mareo para las 2 p.m. La exposición no es fatal pero la cuadrilla con dolor de cabeza se va a casa impedida y el viaje a casa se vuelve peligroso. El segundo patrón es incendio por solvente — un trabajador en el paso de enjuague usa un limpiador a base de solvente cerca de un escape caliente o un soplete en el siguiente deck, los vapores encuentran ignición, incendio relámpago. El arreglo es la SDS — léala, siga el EPP, y respete el viento. Los curados a base de solvente no son para clima de shorts y playera.",
    hazards_reviewed: "Inhalación de vapores · Irritación de piel/ojos · Incendio / explosión por curados inflamables · Resbalón por curado húmedo · Salpicadura a la cara",
    discussion_notes: "• Leer SDS antes de cualquier uso; verificar EPP requerido.\n• Productos a base de solvente: protección respiratoria, no fumar, sin fuentes de ignición, aterrizar rociadores.\n• Rociar con el viento; apagar si cambia el viento.\n• Protección de ojos / cara obligatoria.\n• Riesgo de resbalón — banderear áreas húmedas, no caminar sobre superficies recién curadas.\n• Kits de derrame en sitio; cumplimiento ambiental ante cualquier derrame.",
    references_cited: "OSHA 1926.59 (HazCom) · SDS · NFPA 30 (Inflamables)",
    action_items: "SDS revisada · Respiradores listos · Zonas húmedas señaladas · Kits de derrame",
  },
  cold_weather_concrete: {
    title: "Operaciones de Concreto en Clima Frío",
    incident_pattern:
      "Las operaciones de concreto en clima frío mueven el envenenamiento por CO de 'teórico' a 'este invierno.' El patrón: una cuadrilla monta encerramientos calentados alrededor de una colada para proteger al concreto de congelarse, los calentadores son de propano de fuego directo sin monitoreo continuo de CO, y dentro de 2-3 horas el CO adentro del encerramiento sube a niveles peligrosos. La cuadrilla trabajando adentro no se da cuenta — el CO no tiene olor — y los primeros síntomas son dolor de cabeza y confusión. Para cuando alguien sale a un descanso, ya está impedido. Fatalidades de múltiples personas han pasado por este patrón exacto. El arreglo es obligatorio: calentadores de fuego indirecto venteando combustión afuera del encerramiento, O monitoreo continuo de CO en cada montaje de fuego directo, O el encerramiento se queda abierto.",
    hazards_reviewed: "Estrés por frío / hipotermia · Quemaduras por agua caliente / vapor · CO de calentadores en encerramientos · Resbalones en hielo · Retroceso de agregado congelado",
    discussion_notes: "• Ropa en capas, guantes y botas impermeables aislantes; cubrir cabeza y cuello.\n• Encerramientos calentados: SOLO calentadores directos con monitoreo continuo de CO; O calentadores indirectos venteados al exterior.\n• Áreas de calentamiento (trailer / caseta) a 100 pies de la cuadrilla.\n• Sal / arena en superficies; señalar áreas con hielo.\n• Agua caliente para mezcla: 140°F máx en punto de uso; guantes requeridos.\n• Sistema de compañero — los primeros signos de congelación son sutiles.",
    references_cited: "Boletín OSHA Estrés por Frío · ACI 306 Concretado en Frío",
    action_items: "EPP de frío · Monitoreo de CO · Superficies sin hielo · Área de calentamiento",
  },
  diamond_grinding: {
    title: "Diamond Grinding y Grooving",
    incident_pattern:
      "Los incidentes de diamond grinding comparten perfil con el milling — exposición a sílice de largo plazo domina, con lesiones agudas por aerosol y contacto con disco como secundarias. El esmeril corre agua en el disco, pero en turnos largos el tanque de agua se vacía o una boquilla se tapa y el penacho de sílice sube. El operador en el rig no lo ve desde la cabina. El vehículo de seguimiento y el spotter detrás del rig se llevan lo peor porque están a la altura del penacho. El patrón complicante es el resbalón de lechada — trabajadores con botas de vestir no calificadas para concreto húmedo caminan por la lechada, pierden el pie, terminan debajo o al lado del rig. El arreglo son revisiones horarias de boquillas, un encargado de agua dedicado, y aspiradora de lechada para mantener las superficies de caminar limpias.",
    hazards_reviewed: "Sílice respirable · Resbalones en lechada · Contacto con disco caliente · Ruido · Golpe por tráfico · Lesión ocular por astilla / aerosol",
    discussion_notes: "• Esmerilado mojado para control de sílice (Tabla 1) — agua continua en el disco.\n• Aspirar lechada para evitar contaminación de drenaje.\n• Protección auditiva — el proceso supera 95 dBA.\n• Protección de ojos / cara contra astillas y aerosol.\n• Operador lejos del disco; enfriar disco antes de mantenimiento.\n• Lechada dispuesta en ubicación aprobada.",
    references_cited: "OSHA 1926.1153 (Sílice Tabla 1) · ACPA Grinding Best Practices",
    action_items: "Aspersión verificada · Contención de lechada · EPP auditiva y ocular · Disposición aprobada",
  },
  sound_wall: {
    title: "Construcción de Muro Acústico",
    incident_pattern:
      "Los incidentes de muro acústico vienen del viento agarrando paneles durante la colocación. Un panel precolado de muro acústico mide 18-25 pies de alto y actúa como una vela. El viento sube, el panel oscila la carga mucho más lejos de la expectativa del operador, y la cuadrilla en tierra queda atrapada entre el panel y una columna o barrera. El otro patrón recurrente es la interfaz con tráfico vivo — los muros acústicos por definición se construyen justo al lado de carreteras, y la cuadrilla en tierra se posiciona entre el muro y el carril. Un vehículo saliéndose del carril no tiene a dónde ir más que dentro de la zona de trabajo. El arreglo es monitoreo de velocidad de viento con un umbral duro, líneas guía desplegadas correctamente, y protección positiva entre el trabajo y el carril de viaje.",
    hazards_reviewed: "Caídas · Golpe por panel · Aplastamiento durante erección de columna · Viento atrapando paneles · Volcadura de grúa · Tráfico vivo adyacente",
    discussion_notes: "• Líneas guía controlan rotación; trabajadores fuera del radio de giro.\n• Monitoreo de velocidad de viento — parar colocación al umbral del fabricante.\n• Tie-off sobre 6 pies; barandilla perimetral / sistema de captura conforme crece el muro.\n• Señalero de grúa designado y certificado.\n• Lado de tráfico vivo: protección positiva (barrera) entre trabajo y carril.\n• Cimentaciones curadas a resistencia de diseño antes de colocar columna / panel.",
    references_cited: "OSHA 1926 Subparte M · OSHA 1926 Subparte CC · AASHTO LRFD",
    action_items: "Líneas guía · Monitor de viento · Protección 6 pies+ · Señalero designado",
  },
};
