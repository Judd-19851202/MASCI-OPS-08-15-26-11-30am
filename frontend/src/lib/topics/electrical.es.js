// Auto-split from monolithic meetingTopicLibrary.es.js · iter260
// Domain: electrical · 4 ES translations

export const TOPICS_ELECTRICAL_ES = {
  electrical_safety: {
    title: "Seguridad Eléctrica y Equipo Energizado",
    hazards_reviewed: "Electrocución · Arco eléctrico / explosión · Quemaduras · Caída por choque · Incendio por cables dañados · Arranque inesperado",
    discussion_notes: "• GFCI en cada circuito de 120V — energía temporal, generadores, extensiones.\n• Inspeccionar cables diariamente — sin chaquetas dañadas, conductores expuestos, pines de tierra faltantes.\n• LOTO para cualquier trabajo en sistemas eléctricos — verificado de-energizado con tester.\n• Mantener mínimo 10 pies de líneas aéreas (más para mayor voltaje).\n• Paneles y desconectadores cubiertos y etiquetados.\n• Solo personas calificadas trabajan en equipo energizado, y solo cuando de-energizar no sea factible.",
    references_cited: "OSHA 1926 Subparte K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items: "GFCI verificado · Cables inspeccionados · LOTO seguido · Distancia de altura libre",
  },
  loto: {
    title: "Bloqueo / Etiquetado (LOTO)",
    hazards_reviewed: "Arranque inesperado · Liberación de energía almacenada (hidráulica, neumática, gravedad, resortes) · Múltiples fuentes de energía · Burlando controles · Quitando candado de otra persona",
    discussion_notes: "• Identificar TODA fuente de energía — eléctrica, hidráulica, neumática, gravedad, térmica, química.\n• Notificar a empleados afectados, apagar normalmente, aislar, candado + etiqueta, verificar energía cero.\n• Cada trabajador autorizado aplica su propio candado personal — sin candados compartidos.\n• Probar energía cero: interruptor de arranque, manómetros, operación manual según corresponda.\n• Quitar tu propio candado = tu responsabilidad. Quitar el de otro requiere procedimiento de empleado ausente.\n• LOTO grupal usa lockbox + etiqueta maestra; todos firman entrada y salida.",
    references_cited: "OSHA 1910.147 · OSHA 1926 Subparte K · ANSI Z244.1",
    action_items: "Procedimiento LOTO en sitio · Candados personales · Fuentes de energía · Paso de verificación capacitado",
  },
  generator_temp_power: {
    title: "Generador / Energía Temporal",
    hazards_reviewed: "Envenenamiento por CO · Choque eléctrico · Incendio / derrame · Backfeed a líneas de servicio · Sobrecarga del generador",
    discussion_notes: "• NUNCA operar generador a combustión adentro o en espacio cerrado — el CO mata.\n• 20 pies mínimo de edificios, ventilas, tomas de aire.\n• Aterrizar marco del generador a varilla de tierra donde se requiera.\n• GFCI en cada salida de 120V — muchos generadores no tienen GFCI interno.\n• Dimensionar circuitos para la carga; distribuir en fases.\n• Si alimenta panel, usar interruptor de transferencia (no backfeed por salidas).\n• Recargar combustible solo en frío; contenedores con bonding; no fumar.",
    references_cited: "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO",
    action_items: "Ubicación verificada · Bonding/aterrizaje · GFCI · Área de combustible",
  },
  light_tower: {
    title: "Operaciones de Torre de Iluminación",
    hazards_reviewed: "Volcadura al subir/bajar · Contacto con altura libre · Quemaduras por luces calientes · CO de sección de generador · Choque eléctrico por cables dañados",
    discussion_notes: "• Colocar en suelo nivelado y estable; outriggers totalmente extendidos.\n• Verificar altura libre antes de subir mástil.\n• Bloquear mástil a altura completa antes de alejarse.\n• Generador: recarga en frío, contenedor con bonding, no fumar, 20 pies de edificios.\n• Luces calientes — dejar enfriar antes de servicio o reubicación.\n• Inspeccionar cables a diario; torre dañada fuera de servicio.",
    references_cited: "OSHA 1926.405 · Manual del Fabricante",
    action_items: "Outriggers · Altura libre · Mástil bloqueado · Procedimiento de recarga",
  },
};
