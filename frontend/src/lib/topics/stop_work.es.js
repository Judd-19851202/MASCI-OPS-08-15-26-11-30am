// Domain ES: stop_work · TRACK 15.47
// Voz directa de campo. La prueba de 60 segundos del laborer.

export const TOPICS_STOP_WORK_ES = {
  stop_work_authority: {
    title: "Autoridad de Parar el Trabajo — Cuándo y Cómo Parar",
    incident_pattern:
      "Cada incidente fatal que MASCI ha investigado tiene el mismo dato en la cadena: un momento, a veces de segundos, donde ALGUIEN sabía que estaba mal y no lo dijo. No porque no le importara. Porque no creyó tener la autoridad. No creyó que producción lo perdonaría. No creyó que el foreman lo respaldaría. La Autoridad de Parar el Trabajo significa que CADA persona — laborer, operador, foreman, super, PM — tiene la posición, el deber, y la protección para detener el trabajo en el segundo en que se vuelve inseguro. No 'después del próximo vaciado.' No 'después del almuerzo.' Ahora. Ejemplos reales: un residente agresivo al borde de la zanja (caso 15.47), un hydro-vac que sale vacío donde debía haber gas, un operador en su tercer día de 12 horas, una tormenta a las 3 PM, un cuasi-accidente en los últimos 60 minutos que no paró la operación. Cada uno es un PARA. Para ahora, hablen en la cabina, reinicien sólo cuando la condición inseguro ya no esté.",
    hazards_reviewed:
      "Fatalidad · Daño catastrófico de equipo · Escalación de violencia laboral · Strike de utilidad · Liberación ambiental · Colapso de zanja · Lesión de cuadrilla · Consecuencias reputacionales + legales",
    warning_signs:
      "Un miembro dijo que algo está mal y lo ignoraron\nUn ítem pre-turno fue chequeado en 10 segundos sin inspección\n'Después de este vaciado' / 'después de esta carga' / 'después del almuerzo'\nUn equipo opera con alarma activa\nLa calcomanía de utility one-call está vieja o no está\nUn miembro está en su tercer día de 12 horas\nEl clima entró y nadie lo mencionó\nUn miembro del público está en la barricada y el trabajo no paró",
    when_to_stop:
      "PARA INMEDIATAMENTE cuando CUALQUIERA de estos es verdadero:\n• Un miembro del público se vuelve agresivo al alcance de la cuadrilla o equipo\n• Ves, oyes, o te dicen que hay amenaza creíble o arma\n• El riesgo de strike de utilidad cambió (calcomanía vieja, excavación a mano no encontró utilidad conocida, hydro-vac seco)\n• Una excavación tiene grietas, deslizamiento, agua, o un trabajador expresó duda\n• Equipo con alarma de seguridad (sobrecalentamiento, aceite bajo, falla hidráulica, freno)\n• Un cuasi-accidente en los últimos 60 minutos sin revisión formal\n• Un trabajador visiblemente impedido (fatiga, medicación, alcohol, emocional)\n• Una celda de tormenta a 10 millas y acercándose\n• Una utilidad aérea, dron, o aeronave más cerca de lo planeado",
    who_can_stop:
      "CADA persona en el trabajo. Sin excepción.\n• Laborer — sí, en el día uno\n• Operador — sí, cualquier pieza, cualquier clase\n• Foreman — sí, en cualquier fase\n• Superintendente — sí, en cualquier proyecto\n• Safety — sí, sobre cualquier sub, cualquier nivel\n• Project Manager — sí, incluyendo sobre la protesta del GC\nSi el GC, Owner, o DOT presiona continuar: SIGUE siendo PARA. Documenta la presión por separado. La presión no cambia la decisión.",
    how_to_stop:
      "1. Dilo en voz alta. Las palabras no importan. 'Para. Quiero un reset de 2 minutos.' / 'Para, esto no está bien.' / 'Estoy llamando un Stop Work.'\n2. Señal de mano: palma abierta arriba, luego puño cerrado para mantener.\n3. Sacar a todos de la línea de fuego — retroceder excavador de la zanja, bajar la carga, apagar el motor.\n4. La cuadrilla se reúne en punto seguro (típicamente la camioneta del foreman).\n5. Indica la razón. Palabras simples.\n6. Decidan juntos: ¿qué cambia antes de reiniciar? ¿Quién confirma?\n7. Documenta — hoja pre-turno con nota + iniciales. Foreman llama al super.",
    escalation_chain:
      "Si el foreman no respeta el Stop Work:\n  → Llama al Superintendente.\nSi el Super no respeta:\n  → Llama al Safety Manager.\nSi Safety no respeta (esto nunca debe pasar):\n  → Llama al Operations Manager.\nEscalación final: Owner (Robert / Eric).\nRepresalia por una llamada de Stop Work es motivo de terminación del que toma represalia — laborer, foreman, super, o PM.\nReporte de represalia por escrito: HR + Operaciones.",
    restart_requirements:
      "Reinicia SOLAMENTE cuando TODO esto es verdadero:\n1. La condición que disparó la parada está corregida.\n2. La persona que llamó el Stop Work está de acuerdo en que está corregida.\n3. El foreman firmó en el pre-turno / JHA.\n4. La cuadrilla recibió nuevo briefing sobre lo que cambió.\n5. Si un cuasi-accidente disparó la parada: incidente abierto en ForgedOps.\nDocumenta hora de reinicio en el pre-turno.",
    what_to_do:
      "1. Reconoce el disparador de la lista 'When to Stop'.\n2. Llámalo — palabras, señal de mano, ambos.\n3. Lleva a todos a punto seguro.\n4. Hablen. ¿Qué cambia?\n5. Reinicia sólo después del checklist de reinicio.\n6. Documenta.",
    what_not_to_do:
      "No 'sólo termina esta carga' / 'sólo este vaciado' / 'sólo esta sección.'\nNo uses Stop Work como táctica para bajar producción por razones ajenas — quema la llamada para todos.\nNo discutan de quién es la culpa durante la parada — eso es para revisión post-evento.\nNo dejes que el GC, Owner, o DOT anule la llamada — documenta presión, mantén parada.\nNo te saltes la firma de reinicio — eso hace defensible el Stop Work después.",
    supervisor_actions:
      "Respalda la llamada públicamente. La primera vez que NO respaldes una llamada Stop Work, mataste el programa. Documenta en pre-turno, en la reunión, y en cualquier incidente que fluya de ella. Si la llamada fue innecesaria, ANTE TODO respáldala públicamente — coach al que llamó en privado. Castigar al que llama es el camino más rápido a una fatalidad.",
    documentation:
      "Hoja pre-turno: Stop Work llamado a HH:MM por [Nombre]. Razón: [una línea]. Reinicio a HH:MM tras [qué cambió].\nSi el disparador fue cuasi-accidente, acoso, confrontación pública, problema de utilidad, o violencia: abre incidente en ForgedOps con clasificación correcta.\nSi fue equipo: Pre-Op + orden de mantenimiento.\nSi fue clima: log en el daily report.",
    corrective_actions:
      "Cuenta # de Stop Work por proyecto por mes — SUBIR es bueno (captura cosas), BAJAR es sospechoso.\nSi hubo represalia: investigación HR en 48 horas; terminación está sobre la mesa.\nSi el mismo disparador causó Stop Work dos veces en el mismo proyecto: PM convoca revisión estructural.",
    read_aloud:
      "Escuchen — sesenta segundos. Si ven algo que está a punto de salir mal, digan PARA. En voz alta. Palma abierta en el aire. No importa si llevan un día o veinte años. No importa si yo estoy aquí, o si el GC está aquí, o si el dueño está aquí. Pueden parar el trabajo. Los vamos a respaldar. Cada vez. Si se arregla, reiniciamos. Si no se arregla, no reiniciamos. Hemos perdido gente porque alguien sabía que estaba mal y no lo dijo. No vamos a perder a otro. Stop Work es su trabajo. No es opcional. No es sólo para emergencias. Es para el momento en que piensan 'esto no está bien.' Confíen en ese momento.",
    references_cited:
      "OSHA Stop Work Authority · ANSI/ASSP Z10 Sección 5.1.4 · Política de Stop Work de MASCI · MASCI Flujo de Violencia Laboral",
    action_items:
      "Cada cuadrilla informada pre-turno · Hoja pre-turno con línea Stop Work · Foreman modela la llamada al menos una vez por proyecto · Cero tolerancia a represalia",
  },
};
