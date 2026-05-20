// Domain ES: utilities · iter261 Phase H Batch 3 · 2 ES translations con incident_pattern

export const TOPICS_UTILITIES_ES = {
  underground_utilities: {
    title: "Servicios Subterráneos / Localización 811",
    incident_pattern:
      "Las fatalidades por golpe a servicio se agrupan en tres patrones: golpe a línea de gas con ignición retrasada, golpe a fibra sin lesión pero con responsabilidad masiva, y golpe a eléctrico subterráneo con electrocución del operador. El patrón de gas es el asesino — el cucharón muerde una línea de gas de 2 pulgadas, sin fuego inmediato, el gas se acumula en la zanja mientras la cuadrilla sigue trabajando, una fuente de ignición (celular, interruptor, arranque de vehículo) lo enciende, y la zanja se convierte en un incendio relámpago. Fatalidades múltiples son comunes. El patrón eléctrico es más rápido pero con menor cuerpo de víctimas — los dientes del cucharón muerden un primario, el voltaje transfiere a la excavadora, el operador recibe el golpe, la cuadrilla en tierra recibe potencial de paso. Cada fatalidad en esta categoría regresa a la misma raíz: un servicio no marcado o mal marcado, O una cuadrilla que excavó mecánicamente dentro de la zona de tolerancia de 24 pulgadas de un servicio marcado. El arreglo no es negociable: excavación a mano dentro de la zona de tolerancia. Sin excepciones.",
    hazards_reviewed:
      "Golpe a servicio (gas, eléctrico, fibra, agua, alcantarilla) · Explosión / incendio · Electrocución · Corte de servicio · Lesión por línea energizada",
    discussion_notes:
      "• Llame al 811 (o equivalente estatal) mínimo 2-3 días hábiles antes de excavar.\n• Verificar ticket vigente y NO vencido antes de excavar.\n• Verificar visualmente TODAS las marcas antes de romper terreno; marcas faltantes = parar y volver a llamar.\n• Excavación manual a 24 pulgadas de cualquier servicio marcado (zona de tolerancia).\n• Tratar toda línea no marcada como viva hasta probar lo contrario.\n• Golpe de línea: despejar el área, evacuar viento arriba para gas, sin interruptores/teléfonos cerca de gas, llamar al servicio Y al 911.\n• Daylight (vacío/manual) servicios críticos antes de excavar mecánicamente cerca.",
    references_cited: "OSHA 1926.651(b) · Mejores Prácticas CGA · Programa estatal 811",
    action_items:
      "Tickets 811 verificados · Marcas fotografiadas · Tolerancia manual aplicada · Spotter para excavación mecánica",
  },
  overhead_power: {
    title: "Trabajo Cerca de Líneas Eléctricas Aéreas",
    incident_pattern:
      "Las fatalidades por línea aérea son catastróficas, frecuentemente de múltiples víctimas, y siguen un patrón firma: el equipo con boom contacta un primario, el equipo se energiza, el operador queda bien dentro de la cabina (efecto jaula de Faraday), pero un trabajador en tierra tocando el equipo o cerca recibe la transferencia completa. Escenarios comunes — boom de grúa contacta durante un levantamiento, caja de volteo levantada bajo una línea, escalera resbalada contra un cable de servicio, hasta el brazo de excavadora girando contra un primario bajo. El paso asesino es el trabajador servicial que corre al equipo a ver qué pasa — toca el metal y se convierte en la ruta a tierra. Las lesiones por quemadura son catastróficas. El arreglo es distancia de 10 pies mínimo (más para mayor voltaje), spotter dedicado a la distancia, y si el equipo contacta una línea: PERMANEZCA EN LA CABINA. Salga del contacto si puede, si no salte limpio y arrastre los pies 30 pies de distancia.",
    hazards_reviewed:
      "Electrocución por contacto · Arco por aproximación · Movimiento de equipo (boom, caja, escalera) en zona libre · Voltaje inducido en objetos paralelos",
    discussion_notes:
      "• Distancia mínima de 10 pies para líneas hasta 50 kV; más para mayor voltaje.\n• Donde no se puedan mantener 10 pies: de-energizar + aterrizar O instalar cubiertas O usar spotter dedicado.\n• Equipo con boom cerca de líneas — alarmas de proximidad, spotter dedicado, distancias Tabla A.\n• Cajas de volteo / escaleras — bajas hasta despejar.\n• Si el equipo contacta una línea: PERMANEZCA EN LA CABINA. Operador sale del contacto si es posible. Si no, salte limpio y arrastre los pies a 30+ pies.",
    references_cited: "OSHA 1926.1408 · OSHA 1926.952 · OSHA 1926.405",
    action_items:
      "Líneas identificadas · Distancia verificada · Spotter asignado · Respuesta a contacto",
  },
};
