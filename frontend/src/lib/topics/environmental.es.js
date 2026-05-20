// Domain ES: environmental · iter261 Phase H Batch 4 · 3 ES translations con incident_pattern

export const TOPICS_ENVIRONMENTAL_ES = {
  lightning: {
    title: "Rayos y Tormentas Severas",
    incident_pattern:
      "Las fatalidades por rayo en obras vienen de un patrón terco: 'una colada más' o 'una carga más.' La cuadrilla ve relámpagos a lo lejos, el foreman cuenta truenos, decide que la tormenta sigue a 5 millas, sigue trabajando. El radio de impacto está más cerca de lo que el ojo lee — un rayo puede pegar 10 millas adelante de la lluvia. Trabajador sosteniendo un rastrillo metálico en un deck de pavimentación, trabajador en una grúa, trabajador encima de un camión de combustible, trabajador sosteniendo un alambre de amarre de varilla — cualquiera se vuelve el pararrayos. Patrón dos es el refugio asumido como seguro — trabajadores se agrupan bajo un kiosco abierto o bajo una pieza de equipo creyendo que están protegidos. El flash lateral y la corriente de tierra los encuentran de todos modos. El arreglo es la regla 30/30, tratada como inviolable: trueno dentro de 30 segundos del rayo = parar trabajo, a refugio duro, 30 minutos de silencio antes de reanudar. Sin excepciones por el último camión de asfalto.",
    hazards_reviewed:
      "Impacto directo · Flash lateral · Corriente de tierra · Energización de equipo · Daño por viento · Inundación súbita",
    discussion_notes:
      "• Regla 30/30 — cuando el trueno sigue al rayo en 30 segundos o menos, parar y refugiarse. Esperar 30 minutos tras el último trueno.\n• Sin refugio bajo árboles aislados, cabinas abiertas o andamios.\n• Mejor refugio: edificio cerrado, vehículo con techo duro (ventanas arriba).\n• Desconectar grúas, equipo y herramientas antes de la tormenta.\n• Vigilar inundación súbita en zonas bajas.",
    references_cited: "NWS Lightning Safety · OSHA Boletín de Rayos · NFPA 780",
    action_items: "App de clima · Ubicación de refugio · Regla 30/30 informada · Plan de apagado",
  },
  wildlife_insects: {
    title: "Vida Silvestre / Picaduras de Insectos",
    incident_pattern:
      "Los incidentes de vida silvestre e insectos se ven menores en lo abstracto y se vuelven fatales en la vida real cuando el trabajador es alérgico y la respuesta es lenta. El patrón: peón mete la mano a una caja de medidor o se baja de equipo a un montículo de hormigas rojas, recibe 15-30 piquetes en segundos, tiene una alergia conocida a abejas, desarrolla anafilaxia en el campo. El EpiPen está en la troca a un cuarto de milla. Para cuando alguien corre y regresa, la garganta se está cerrando. Segundo patrón es la mordedura de serpiente que el trabajador no toma en serio — punción pequeña, no vio qué fue, sigue trabajando hasta que la pierna empieza a hincharse 90 minutos después. La ventana de tratamiento se está cerrando. El trabajo de campo en Florida y Texas tiene la mayor concentración de estos incidentes. El arreglo es pequeño pero real: pregunte a la cuadrilla sobre alergias en la orientación, mantenga EpiPens en cada proyecto donde haya trabajadores alérgicos a abejas, y trate cada mordedura de serpiente como venenosa hasta que la ER diga lo contrario.",
    hazards_reviewed:
      "Picaduras de abeja / avispa (anafilaxia) · Mordidas de serpiente · Ataques de hormigas rojas · Garrapatas / mosquitos · Encuentros con caimán / vida silvestre · Mordidas de araña · Atropellos animal-vehículo",
    discussion_notes:
      "• Caminos despejados; ojos al suelo en pasto alto.\n• Botas pesadas y pantalones largos en áreas de matorral.\n• Repelente con DEET 20-30%.\n• Alergia a abejas/avispas — EpiPen en sitio, ubicación conocida por la cuadrilla.\n• Mordedura de serpiente: víctima calmada, inmovilizar área mordida, 911 — SIN hielo, SIN torniquete, SIN succión.\n• Hormigas rojas: salir del área, sacudir, tratar; reacción alérgica = 911.\n• Caimanes en aguas de FL — nunca acercarse, nunca alimentar, mínimo 30 pies.",
    references_cited: "CDC Enfermedades Vectoriales · OSHA Quick Card · Agencia Estatal de Vida Silvestre",
    action_items: "Botiquín con suministros · EpiPen ubicado · Repelente surtido",
  },
  spill_response: {
    title: "Respuesta a Derrames y Cumplimiento Ambiental",
    incident_pattern:
      "Los incidentes de derrame rara vez matan trabajadores directamente pero generan dos resultados del mundo real que dañan a las cuadrillas: la liberación al drenaje pluvial que se convierte en una multa de seis cifras más una orden de paro, y el charco de combustible que se enciende y saca equipo, vehículos y a veces operadores. El patrón: la boquilla de la manguera gotea durante el reabastecimiento sobre una superficie inclinada del paver, el combustible corre 40 pies a una rejilla de drenaje antes de que alguien se dé cuenta. El inspector ve el brillo en el siguiente desfogue y lo conecta al número de proyecto en el camión de volteo al otro lado de la calle. El arreglo son las cosas sin gloria: kits de derrame dentro de 50 pies de cada punto de combustible, tapetes de drenaje pluvial durante TODO el reabastecimiento (no solo cuando parece riesgoso), y una regla absoluta de que 'parar la fuente' es paso uno. No trate de empujar un charco extendiéndose de regreso aguas arriba — cierre la válvula, luego lidie con lo que ya salió. Umbral de reporte conocido por cada foreman ANTES del derrame, no después.",
    hazards_reviewed:
      "Liberación de combustible / aceite a suelo o drenaje · Derrame químico · Multas ambientales · Resbalón en material derramado · Inhalación de vapor",
    discussion_notes:
      "• Kit de derrame disponible donde sea que se use o almacene combustible, aceite, hidráulico, químicos.\n• Detener la fuente primero — cerrar válvulas, contenedores.\n• Contener el derrame — boom absorbente, calcetines, almohadillas.\n• Limpiar y disponer adecuadamente — materiales contaminados son residuos peligrosos.\n• Reportar derrames según umbral estatal/EPA — derrames menores rastreados, reportables llamados en tiempo requerido.\n• Tapetes de protección de drenaje durante reabastecimiento.",
    references_cited: "EPA SPCC · Requisitos FDEP / estatal · NFPA 30",
    action_items: "Kits en sitio · SDS de químicos · Umbral de reporte · Tapetes desplegados",
  },
};
