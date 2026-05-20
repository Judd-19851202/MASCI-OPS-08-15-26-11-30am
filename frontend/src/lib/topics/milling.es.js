// Domain ES: milling · iter261 Phase H Batch 2 · 2 entries

export const TOPICS_MILLING_ES = {
  milling_operations: {
    title: "Operaciones de Milling (Cold Planing)",
    incident_pattern:
      "Las fatalidades de milling se dividen entre dos patrones. Primero — un trabajador alcanza cerca o adentro del tambor para liberar una piedra atorada, quitar metal extraño, o cambiar un diente, con la máquina corriendo o con energía hidráulica almacenada en el levante del tambor. El tambor cae o gira 6 pulgadas y se lleva un brazo. Segundo — un peón camina detrás del conveyor mientras gira para descargar en el camión, y la cola del conveyor lo atrapa. El tambor para rápido cuando se apaga, pero la energía almacenada en los cilindros de levante no. El lockout es el arreglo universal y el paso universalmente saltado en toques pequeños. 'Solo un diente' ha costado manos.",
    hazards_reviewed:
      "Golpe-por tambor / conveyor · Polvo de sílice / asfalto · Atrapamiento en puntos de pellizco del conveyor · Contacto con dientes calientes · Ruido arriba de 95 dBA · Tropezón en transiciones de grado · Energía hidráulica almacenada en levante de tambor",
    discussion_notes:
      "• Trabajadores se quedan fuera de zonas no-go del tambor y conveyor durante operación. Marcadas con conos hi-vis.\n• Sistema de spray de agua en el tambor — control primario de sílice/polvo. Confirme flujo en cada turno.\n• Respirador si el control de agua es insuficiente (mills viejos, condiciones secas, cortes interiores).\n• Cambios de dientes: máquina totalmente apagada, BLOQUEADA, tambor enfriado, levante del tambor BLOQUEADO con cribbing calificado.\n• 'Solo un diente' aún requiere LOTO completo. El patrón es atajo → lesión.\n• Protección auditiva obligatoria.\n• Cuadrilla en tierra consciente de transiciones de grado; comunicación positiva con operador.\n• Zona de giro del conveyor — trabajadores en tierra se mantienen libres. El giro es más rápido de lo que la gente espera.",
    references_cited:
      "OSHA 1926.1153 · Boletín NIOSH Milling de Asfalto · OSHA 1910.147",
    action_items:
      "Zonas no-go marcadas · Spray de agua verificado · Protección auditiva requerida · LOTO para cambios de diente · Cribbing de levante de tambor en sitio",
  },
  milling_silica_exposure: {
    title: "Exposición a Sílice en Milling y Disciplina de Spray de Agua",
    incident_pattern:
      "La exposición a sílice en milling es una catástrofe LENTA — no del tipo que aparece en un log de fatalidades este año. El trabajador respira polvo por 5–10 temporadas de pavimentación. La silicosis se construye en tejido pulmonar a niveles de exposición que el trabajador nunca se dio cuenta que eran peligrosos. El trabajo se siente normal. La tos a los 50 no. El patrón de falla es consistente: boquillas de spray tapadas o parcialmente tapadas, el operador no las ve desde la cabina, y el penacho de polvo sube del tambor invisiblemente. O el spray se acaba a media jornada y el operador sigue cortando porque el camión está esperando. La regla OSHA de sílice de 50 µg/m³ (8 horas) se excede fácilmente en un mill seco con mal spray. El arreglo es inspección diaria de boquillas, un tanque de agua de respaldo, y protección respiratoria como segunda línea de defensa — no la primera.",
    hazards_reviewed:
      "Silicosis a largo plazo por cortar concreto/asfalto con contenido de sílice · Irritación respiratoria aguda · Irritación ocular por partículas aerotransportadas · Pérdida de visibilidad por penacho de polvo ocultando peligros · Acumulación de polvo en cabina del operador",
    discussion_notes:
      "• El spray de agua es el control PRIMARIO de sílice. Revise cada boquilla ANTES de empezar a cortar.\n• Tanque de agua de respaldo o plan de recarga — nunca se quede seco a media jornada para 'terminar este.'\n• Penacho de polvo visible = falla de control. Pare de cortar. Diagnostique. Arregle las boquillas.\n• Protección respiratoria (P100 o aire suministrado) para condiciones de mill seco, cortes interiores, o cuando el agua falla.\n• No se pare viento-abajo del corte. Posicione equipo de apoyo viento-arriba también.\n• Sistema de filtro de cabina en el mill — cambie según OEM, no 'cuando me acuerde.'\n• Regla OSHA de sílice dice 50 µg/m³ 8 horas. Muestreo de aire requerido en trabajos de alta exposición.\n• Ropa de trabajo de manga larga — la sílice se adhiere a la piel y se lleva a casa a las familias.\n• Ducha / cambio antes de salir si expuesto. No le ayuda a USTED, ayuda a su familia.",
    references_cited:
      "OSHA 29 CFR 1926.1153 (Sílice) · Boletín NIOSH Milling de Asfalto · TLV ACGIH",
    action_items:
      "Inspección de boquillas asignada a cada turno · Plan de agua de respaldo revisado · Respirador con prueba de ajuste para trabajadores expuestos · Cambio de filtro de cabina programado · Hábito de contaminación que-se-va-a-casa discutido",
  },
};
