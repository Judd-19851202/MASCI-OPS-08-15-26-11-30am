// Domain ES: fall_protection · iter261 Phase H Batch 3 · 5 ES translations con incident_pattern

export const TOPICS_FALL_PROTECTION_ES = {
  fall_protection: {
    title: "Protección Contra Caídas — General",
    incident_pattern:
      "Las caídas son la causa #1 de fatalidades en construcción, año tras año. El patrón que más se repite no es el trabajador que trató de hacer lo correcto — es el trabajador que se amarró a algo que no era un anclaje de ingeniería. Un poste de barandilla. Una pieza de conduit. Un ángulo pequeño. El anclaje falla a 200 lb en vez de aguantar 5,000 lb, y el trabajador cae con el equipo todavía puesto. El segundo patrón es el lanyard desplegado-pero-muy-largo — trabajador tiene el arnés puesto, pero el lanyard de 6 pies sin SRL significa que el arresto de caída no engancha hasta después de pegar el deck abajo. No se hizo la matemática de distancia libre. Patrón tres es el trabajador suspendido no rescatado que desarrolla trauma por suspensión dentro de 15 minutos — el equipo funcionó, pero no había plan de rescate, y el trabajador muere colgado del arnés. El arreglo son anclajes de ingeniería, matemática de distancia libre hecha antes de empezar el trabajo, y un plan de rescate que nombra quién baja al trabajador suspendido en menos de 15 minutos.",
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
    incident_pattern:
      "Las lesiones por escalera son de las lesiones de tiempo-perdido más comunes en construcción y las más fáciles de descartar como 'fue torpeza.' No es torpeza — es predecible. Patrón uno es la sobre-extensión — trabajador en escalera de extensión se inclina hacia un lado para alcanzar un perno más en vez de bajarse y mover la escalera. El centro de gravedad pasa fuera de los rieles y la escalera patea lateralmente. El trabajador cae 12 pies sobre cadera u hombro. Patrón dos es el deslizamiento de la base — base puesta en una losa lisa sin pies antideslizantes, la escalera patea al bajar el trabajador, la caída es directo al piso. Patrón tres es electrocución — escalera de extensión de aluminio recargada contra un edificio, la cabeza contacta un cable de servicio aéreo al subir. El trabajador se convierte en ruta a tierra. Arreglo: ángulo 4:1, tres puntos de contacto, amarrada arriba, fibra de vidrio cerca de eléctrico, y la regla simple — si tiene que inclinarse, bájese.",
    hazards_reviewed:
      "Caídas · Deslizamiento de escalera · Volcadura · Electrocución por línea aérea · Sobre-extensión · Peldaños / rieles dañados",
    discussion_notes:
      "• Inspeccionar cada escalera antes de uso — sin grietas, rieles doblados, pies faltantes.\n• Regla 4:1 para escaleras de extensión.\n• Tres puntos de contacto; nunca cargar herramientas al subir.\n• Extender 3 pies sobre el punto de aterrizaje, asegurada arriba.\n• Nunca los dos peldaños superiores de tijera; nunca el tope de extensión.\n• No conductora (fibra de vidrio) cerca de eléctrico.\n• No alcanzar más allá de los rieles — bajar y mover la escalera.",
    references_cited: "OSHA 1926 Subparte X · OSHA 1926.1053 · ANSI A14",
    action_items:
      "Escaleras inspeccionadas · Defectuosas etiquetadas · Tie-off donde sea 6 pies+ · Fibra de vidrio para eléctrico",
  },
  aerial_lift: {
    title: "Plataforma Aérea / Boom Lift",
    incident_pattern:
      "Las fatalidades de plataforma aérea se dividen en dos patrones. Patrón uno es la eyección / catapulta — el operador maneja el boom sobre terreno desigual, la plataforma se sacude arriba, y el trabajador sale lanzado de la canasta. El tie-off habría detenido la caída pero el lanyard no estaba anclado al punto duro del fabricante — estaba enganchado a una baranda lateral. Patrón dos es el aplastamiento contra una estructura aérea — el operador eleva la canasta hacia una viga o debajo de un deck, no se da cuenta que el espacio se cierra, queda atrapado a nivel del pecho entre el riel de la canasta y la estructura. El trabajador no puede alcanzar los controles de pie para retroceder. En toda la industria, ambos patrones se eliminan con dos controles: tie-off anclado al punto del fabricante, y un segundo trabajador en tierra vigilando espacio libre que pueda activar el descenso de emergencia desde abajo. El operador nunca trabaja solo en la canasta.",
    hazards_reviewed:
      "Caídas desde plataforma · Volcadura por sobrecarga o terreno desigual · Golpe por obstáculo aéreo · Electrocución · Aplastamiento entre plataforma y estructura",
    discussion_notes:
      "• Operador certificado y autorizado; inspección pre-turno.\n• Tie-off en canasta — arnés cuerpo entero, lanyard al anclaje del fabricante.\n• Outriggers (donde aplique) totalmente extendidos en terreno nivelado.\n• Mantener mínimo 10 pies de líneas energizadas; más para mayor voltaje.\n• No trepar barandillas ni salir de canasta — la canasta es la única posición de trabajo.\n• Bocina antes de mover; spotter al viajar cerca de personal.",
    references_cited: "OSHA 1926.453 · ANSI A92 · Manual del Fabricante",
    action_items:
      "Inspección pre-turno · Operador certificado · Tie-off en canasta · Altura libre",
  },
  scaffold: {
    title: "Seguridad de Andamios",
    incident_pattern:
      "Las fatalidades de andamio tienen un patrón clásico que se sigue repitiendo: el andamio lo erige una cuadrilla no calificada, la placa base se asienta sobre suelo blando sin tablones, la altura crece más allá de la relación altura-base, el viento atrapa la plataforma al tercer día, y toda la estructura se vuelca. Los trabajadores en la plataforma superior caen con el andamio. Segundo patrón es la barandilla faltante — el andamio se erigió correctamente, pero una sección se modificó después para acomodar una característica de pared y la barandilla se quitó y nunca regresó. El trabajador pisa el borde abierto durante una tarea rutinaria. Tercero es la sobrecarga — escombros y material apilados en la plataforma exceden la capacidad calificada, los tablones flexionan o quiebran. El arreglo es la inspección de persona competente ANTES de cada turno — base de ingeniería, barandillas completas, capacidad calificada no excedida, y solo erectores calificados.",
    hazards_reviewed:
      "Caídas · Colapso por erección incorrecta · Golpe por material cayendo · Electrocución cerca de líneas · Volcadura por base inadecuada",
    discussion_notes:
      "• Erigido, modificado o desmantelado solo por personas calificadas bajo supervisión de persona competente.\n• Inspección diaria por persona competente antes de cada turno.\n• Barandillas en todos los lados abiertos sobre 10 pies.\n• Toe boards, pantallas o redes para prevenir caída de materiales.\n• Base sobre tablones o placas en suelo sólido; relación altura-base por fabricante.\n• Mantener 10 pies+ de líneas aéreas.\n• Acceso por escalera, torre o escalera incorporada — no trepar arriostres.",
    references_cited: "OSHA 1926 Subparte L · OSHA 1926.451",
    action_items: "Inspección diaria · Barandillas / toe boards · Base verificada · Ruta de acceso",
  },
  bridge_overpass: {
    title: "Trabajo en Puente / Paso Elevado",
    incident_pattern:
      "Las caídas en puente y paso elevado tienen dos firmas asesinas. Primero — el trabajador que se va por el borde de un deck abierto durante una colada larga o una tarea de inspección larga. Para la hora 8 la conciencia del perímetro se desvanece, un trabajador pisa muy cerca de la fascia ajustando una cimbra, y la caída es de 40+ pies sobre tráfico, agua o rocas. La tasa de sobrevivencia es casi cero. Segundo patrón — objetos cayendo a tráfico vivo abajo. El trabajador deja caer una llave o un pedazo de concreto del deck. Pega en un parabrisas a velocidad de carretera. El conductor muere, el proyecto sale en primera plana, vienen demandas. Ambos patrones mueren bajo el mismo conjunto de controles: PFAS perimetral o barandilla antes de cualquier trabajo en deck, plataformas de captura / redes para proteger carriles abajo, cada herramienta amarrada, y cierre de carriles coordinado para cualquier operación que pueda dejar caer material.",
    hazards_reviewed:
      "Caídas por borde · Caídas por aberturas · Tráfico vivo abajo o adyacente · Objetos cayendo a carriles · Golpe por tráfico viajante",
    discussion_notes:
      "• Protección perimetral ANTES de cualquier trabajo en tablero.\n• Plataformas de captura / redes para proteger carriles abajo.\n• Herramientas amarradas; partes pequeñas en bolsas con cierre.\n• Coordinar cierre de tráfico vivo abajo para operaciones de alto riesgo.\n• Trabajo de borde: anclaje positivo y PFAS — sin tareas de borde por trabajador solo.\n• Monitoreo de viento para operaciones de mástil alto.",
    references_cited:
      "OSHA 1926 Subparte M · AASHTO Construcción de Puentes · ANSI Z359",
    action_items:
      "PFAS perimetral · Plataforma de captura · Herramientas amarradas · Cierre coordinado",
  },
};
