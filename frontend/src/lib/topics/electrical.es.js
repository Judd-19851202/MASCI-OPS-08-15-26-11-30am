// Domain ES: electrical · iter261 Phase H Batch 4 · 4 ES translations con incident_pattern

export const TOPICS_ELECTRICAL_ES = {
  electrical_safety: {
    title: "Seguridad Eléctrica y Equipo Energizado",
    incident_pattern:
      "Las fatalidades eléctricas en obras se agrupan alrededor de tres atajos recurrentes. Primero — la extensión con el pin de tierra faltante usada en un área mojada porque 'solo es por una hora.' El trabajador agarra una herramienta metálica, se convierte en ruta a tierra, muere en un escalón de tráiler. Segundo — el trabajo en panel hecho 'vivo' porque apagar inconvenienciaría a otra contrata. El arco salta cuando un desarmador puentea dos fases; el trabajador muere de lesiones térmicas en las próximas 72 horas. Tercero — el circuito asumido como muerto. El trabajador llega, no prueba, toca un bus que alguien más energizó en el breaker. Cada uno de estos es prevenible con los mismos controles: GFCI en cada cordón de 120V, sin trabajo vivo sin excepción documentada, y probar-antes-de-tocar con un medidor en el que el trabajador personalmente confíe.",
    hazards_reviewed:
      "Electrocución · Arco eléctrico / explosión · Quemaduras · Caída por choque · Incendio por cables dañados · Arranque inesperado",
    discussion_notes:
      "• GFCI en cada circuito de 120V — energía temporal, generadores, extensiones.\n• Inspeccionar cables diariamente — sin chaquetas dañadas, conductores expuestos, pines de tierra faltantes.\n• LOTO para cualquier trabajo en sistemas eléctricos — verificado de-energizado con tester.\n• Mantener mínimo 10 pies de líneas aéreas (más para mayor voltaje).\n• Paneles y desconectadores cubiertos y etiquetados.\n• Solo personas calificadas trabajan en equipo energizado, y solo cuando de-energizar no sea factible.",
    references_cited: "OSHA 1926 Subparte K · OSHA 1926.404 · NFPA 70E · OSHA LOTO 1910.147",
    action_items:
      "GFCI verificado · Cables inspeccionados · LOTO seguido · Distancia de altura libre",
  },
  loto: {
    title: "Bloqueo / Etiquetado (LOTO)",
    incident_pattern:
      "Las fallas de LOTO matan trabajadores en un patrón firma: estado de energía asumido. Patrón uno — un mecánico bloquea el desconectador eléctrico pero no toma en cuenta el acumulador hidráulico, la presión almacenada se libera cuando se abre la línea, y el boom cae sobre el trabajador debajo. Patrón dos — una cuadrilla comparte un candado o usa un enfoque de 'un-candado-para-el-equipo.' Un trabajador termina su tarea, quita el candado, el equipo se energiza, el siguiente trabajador sigue dentro de la máquina. Patrón tres — alguien quita un candado que no es suyo porque el dueño original se fue a casa. El equipo se energiza con el trabajador del segundo turno todavía en la zona de peligro. El arreglo no es negociable: cada trabajador autorizado aplica su candado personal, cada fuente de energía aislada (eléctrica Y hidráulica Y neumática Y gravedad Y resortes), y verificación de energía cero con un tester antes de tocar nada.",
    hazards_reviewed:
      "Arranque inesperado · Liberación de energía almacenada (hidráulica, neumática, gravedad, resortes) · Múltiples fuentes de energía · Burlando controles · Quitando candado de otra persona",
    discussion_notes:
      "• Identificar TODA fuente de energía — eléctrica, hidráulica, neumática, gravedad, térmica, química.\n• Notificar a empleados afectados, apagar normalmente, aislar, candado + etiqueta, verificar energía cero.\n• Cada trabajador autorizado aplica su propio candado personal — sin candados compartidos.\n• Probar energía cero: interruptor de arranque, manómetros, operación manual según corresponda.\n• Quitar tu propio candado = tu responsabilidad. Quitar el de otro requiere procedimiento de empleado ausente.\n• LOTO grupal usa lockbox + etiqueta maestra; todos firman entrada y salida.",
    references_cited: "OSHA 1910.147 · OSHA 1926 Subparte K · ANSI Z244.1",
    action_items:
      "Procedimiento LOTO en sitio · Candados personales · Fuentes de energía · Paso de verificación capacitado",
  },
  generator_temp_power: {
    title: "Generador / Energía Temporal",
    incident_pattern:
      "Las fatalidades de generador tienen dos perfiles distintos. Perfil uno es envenenamiento por CO — generador colocado muy cerca de una carpa, una puerta de garage abierta, un tráiler parcialmente cerrado, o bajo el alero de un edificio. El escape se acumula, la cuadrilla trabajando cerca pasa de dolor de cabeza a náusea a inconsciencia sin darse cuenta de lo que está pasando. Muertes de múltiples víctimas por este patrón exacto pasan cada temporada de limpieza de tormenta. Perfil dos es backfeed a la utility — generador conectado a un panel sin interruptor de transferencia, el liniero trabajando en lo que cree es una línea de-energizada muere porque el generador empujó voltaje de regreso por el servicio. El arreglo para ambos: mínimo 20 pies de cualquier abertura, nunca adentro ni bajo techo, interruptor de transferencia obligatorio cuando se alimente un panel, y GFCI en cada salida porque la mayoría de generadores comerciales no tienen GFCI interno.",
    hazards_reviewed:
      "Envenenamiento por CO · Choque eléctrico · Incendio / derrame · Backfeed a líneas de servicio · Sobrecarga del generador",
    discussion_notes:
      "• NUNCA operar generador a combustión adentro o en espacio cerrado — el CO mata.\n• 20 pies mínimo de edificios, ventilas, tomas de aire.\n• Aterrizar marco del generador a varilla de tierra donde se requiera.\n• GFCI en cada salida de 120V — muchos generadores no tienen GFCI interno.\n• Dimensionar circuitos para la carga; distribuir en fases.\n• Si alimenta panel, usar interruptor de transferencia (no backfeed por salidas).\n• Recargar combustible solo en frío; contenedores con bonding; no fumar.",
    references_cited: "OSHA 1926.405 · NFPA 70 (NEC) · NIOSH CO",
    action_items: "Ubicación verificada · Bonding/aterrizaje · GFCI · Área de combustible",
  },
  light_tower: {
    title: "Operaciones de Torre de Iluminación",
    incident_pattern:
      "Los incidentes de torre de iluminación siguen guiones predecibles. El guión del mástil-a-la-línea: torre colocada en una obra de pavimentación al atardecer, el operador sube el mástil sin escanear arriba, el mástil pega un cable de servicio, el marco de la torre se energiza, el trabajador en tierra recargado en ella recibe la transferencia. El otro guión es la volcadura por viento — torre colocada en grava blanda con outriggers extendidos pero sin zoquetes, ráfaga de viento a las 3 a.m. la tira de lado, el mástil cae sobre un carril o sobre un vehículo estacionado. El CO de la sección del generador es un tercer patrón — torre estacionada bajo un paso elevado para trabajo nocturno, los gases se acumulan bajo el deck, la cuadrilla viento abajo aparece con síntomas. El arreglo es la rutina que a nadie le gusta pero funciona: outriggers sobre zoquetes, escanear arriba antes de subir el mástil, colocar 20 pies de cualquier cerrado.",
    hazards_reviewed:
      "Volcadura al subir/bajar · Contacto con altura libre · Quemaduras por luces calientes · CO de sección de generador · Choque eléctrico por cables dañados",
    discussion_notes:
      "• Colocar en suelo nivelado y estable; outriggers totalmente extendidos.\n• Verificar altura libre antes de subir mástil.\n• Bloquear mástil a altura completa antes de alejarse.\n• Generador: recarga en frío, contenedor con bonding, no fumar, 20 pies de edificios.\n• Luces calientes — dejar enfriar antes de servicio o reubicación.\n• Inspeccionar cables a diario; torre dañada fuera de servicio.",
    references_cited: "OSHA 1926.405 · Manual del Fabricante",
    action_items: "Outriggers · Altura libre · Mástil bloqueado · Procedimiento de recarga",
  },
};
