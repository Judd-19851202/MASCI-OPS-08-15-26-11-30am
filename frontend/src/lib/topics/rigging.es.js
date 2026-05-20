// Domain ES: rigging · iter261 Phase H Batch 3 · 2 ES translations con incident_pattern

export const TOPICS_RIGGING_ES = {
  cranes_hoisting: {
    title: "Operaciones de Levantamiento con Grúa",
    incident_pattern:
      "Las fatalidades de grúa se agrupan en cuatro patrones predecibles. Uno — el boom contacta un primario aéreo, el operador sobrevive en cabina (Faraday), la cuadrilla en tierra tocando la grúa muere por transferencia. Dos — la carga cae porque el aparejo estaba mal: eslinga sobrecargada para el ángulo de hitch, pasador de grillete saliéndose, choker resbalando. Los trabajadores debajo de la carga mueren al instante. Tres — la grúa se vuelca porque los outriggers estaban sobre tierra en vez de zoquetes, o el radio de levantamiento excedió la tabla de carga, o el operador extendió el boom más allá del límite de ingeniería para hacer un 'alcance corto.' La grúa entera se va. Cuatro — two-blocking, donde el bloque del gancho golpea la punta del boom y o rompe la línea de carga o destroza el boom. El arreglo es el plan de levantamiento, tratado como contrato: peso verificado, radio verificado, capacidad del suelo de ingeniería, outriggers totalmente sobre zoquetes, señalero calificado, y nadie debajo de la carga. Nunca.",
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
    incident_pattern:
      "Las fatalidades por falla de aparejo tienen una repetición deprimente: alguien usó una eslinga que estaba claramente dañada porque 'aguanta un levantamiento más,' o el rigger ajustó mal por el ángulo de hitch y la eslinga rompió al 60% de capacidad nominal. Una carga de 2 toneladas cayendo 6 pies sobre un trabajador es insobrevivible. Patrón dos — grilletes cargados de lado durante un basket hitch, el pasador de tornillo se sale por vibración, la carga se libera. Patrón tres — cadenas y binders en un flatbed no torqueados suficiente; la carga se mueve en tránsito, saca a un trabajador en la siguiente curva. El arreglo es mecánico y aburrido: inspeccionar cada eslinga, grillete, gancho antes de CADA levantamiento; remover equipo dañado de servicio inmediatamente; nunca cargar lateralmente un grillete; igualar capacidad al tipo de hitch Y al ángulo. Trabajadores nunca bajo carga suspendida — las líneas guía dirigen desde fuera de la zona de muerte.",
    hazards_reviewed:
      "Falla de eslinga · Carga moviéndose en tránsito · Hitch / conexión incorrecta · Aparejo dañado · Pellizcos · Material cayendo por chock o correa incorrecta",
    discussion_notes:
      "• Inspeccionar cada eslinga, grillete, gancho antes de uso; remover dañados de servicio.\n• Igualar capacidad de eslinga a la carga — ajustar por tipo de hitch y ángulo.\n• Grilletes screw-pin o de perno para levantamientos elevados; nunca cargados de lado.\n• Etiquetas WLL legibles; equipo etiquetado fuera de servicio.\n• Trabajadores nunca bajo carga suspendida; líneas guía para control.\n• Cargas de camión: chocks, correas según FMCSA.",
    references_cited: "OSHA 1926.251 · ASME B30.9 · FMCSA 49 CFR 393",
    action_items:
      "Aparejos inspeccionados · Capacidades verificadas · Líneas guía · Aseguramiento de carga revisado",
  },
};
