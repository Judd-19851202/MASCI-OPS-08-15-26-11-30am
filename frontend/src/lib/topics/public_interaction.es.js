// Domain ES: public_interaction · TRACK 15.46 + 15.47
// Voz: directa, de campo. Mismas reglas del 5:30 AM. Los foremen
// leen estos en voz alta a la cuadrilla — corto y honesto.
//
// Schema ES extendido (TRACK 15.47): cada tópico ahora carga
// warning_signs, what_to_do, what_not_to_do, supervisor_actions,
// documentation, corrective_actions, read_aloud. Campos antiguos
// preservados.

export const TOPICS_PUBLIC_INTERACTION_ES = {
  angry_public_de_escalation: {
    title: "Tratar Con Miembros del Público Enojados",
    incident_pattern:
      "El trabajo pesado-civil ocurre frente al público. Vecinos, conductores desviados, dueños de negocios con la entrada bloqueada. Cuando sale mal: un residente molesto llega al foreman a las 7 AM, el foreman responde mal, sube la voz, terceros graban con el celular. En casos graves: objetos lanzados, empujones, armas. Lección: el miembro de la cuadrilla que responde con paciencia y llama al superintendente previene un video viral, un reporte de violencia laboral, y en los peores casos una lesión.",
    hazards_reviewed:
      "Confrontación verbal · Comportamiento agresivo · Amenaza física · Armas · Daño reputacional · Incidente de violencia laboral · Lesión personal",
    warning_signs:
      "Acercamiento sin contacto visual + contacto visual súbito · dedo apuntando · paso adentro de la barricada · voz que sube MÁS y no baja · puños cerrados · celular grabando · 'tú sabes quién soy yo' · referencias a un arma",
    what_to_do:
      "1. Baja tu voz. La de ellos sube — la tuya baja. Funciona.\n2. Manos visibles, palmas afuera, sin apuntar, medio giro.\n3. Reconoce: 'Te escucho. Esto está afectando tu día.'\n4. Enruta: 'Déjame llamar al superintendente — él te puede dar las respuestas.'\n5. Si no se retiran: regresa detrás de la barricada o al vehículo.\n6. Si muestran arma, amenazan, o te tocan: PARA. Retírate. Llama al 911. Luego al superintendente.\n7. Documenta enseguida por escrito: hora, lugar, palabras, testigos.",
    what_not_to_do:
      "No discutas. Tú no decides.\nNo los grabes — la compañía documenta.\nNo publiques en redes sociales.\nNo los toques, ni para guiarlos.\nNo digas 'cálmate' — nunca funciona.\nNo prometas nada (horario, dinero, acceso) que no puedas cumplir.",
    supervisor_actions:
      "Al teléfono en 2 minutos. Si fue verbal: incidente mismo día, clasificación 'Trato con Público · Confrontación Verbal'. Si hubo contacto físico: 911 + clasificación 'Contacto Físico' o 'Asalto Físico'. Notifica Operaciones y Seguridad directamente.",
    documentation:
      "Incidente tipo 'Public / Third Party'.\nClasificaciones: Public Interaction + Verbal Confrontation (+ Threat / Physical Contact / Workplace Violence si aplica).\nTestigos: nombre + rol + teléfono + correo + declaración por cada miembro.\nSi hubo policía: agencia, oficial, placa, número de caso.\nFotos: posición de barricada, dirección de la residencia.",
    corrective_actions:
      "Repetir este tópico pre-turno con la cuadrilla.\nNúmero del superintendente en cada cabina.\nSi la misma dirección genera 2 incidentes: briefing completo con cuadrilla + safety + PM.",
    read_aloud:
      "Escuchen — 60 segundos. Si alguien del público se acerca enojado, esto es lo que haces. UNO: baja la voz. DOS: manos abiertas, no apuntes. TRES: di 'te escucho' — eso no es estar de acuerdo, es reconocer. CUATRO: di 'déjame llamar a mi supervisor.' CINCO: si te tocan, muestran un arma, o dicen que te van a lastimar — PARA, retrocede, llama al 911, luego llámame a mí. No te pagan por discutir. Te pagan por llegar a casa hoy. Documentamos TODA interacción, hasta las pequeñas, porque las pequeñas se vuelven las grandes.",
    references_cited:
      "Guía OSHA · Política de Violencia Laboral de MASCI · SOP de Incidentes",
    action_items:
      "Número del superintendente en cabina · Formulario de violencia laboral conocido · 'Retirarse' ensayado en pre-turno",
  },

  public_near_children: {
    title: "Miembros del Público Cerca de Niños",
    incident_pattern:
      "Zonas escolares, líneas de recogida, parques, banquetas. Cuando el trabajo está cerca de niños, el público mira distinto. Los padres proyectan a su hijo en cada miembro de la cuadrilla. La misma plancha que cayó dentro de la barricada es ahora una amenaza pública. Peor: un niño cruza al zona de trabajo. Aunque haya barricada, aunque el padre esté visible. El patrón: operador retrocede, niño a 10 pies, padre pierde el control, ahora el operador es defendido en redes que no puede ganar.",
    hazards_reviewed:
      "Niño entra al zona · Escalación del padre · Exposición en redes · Equipo retrocediendo cerca de peatones · Acusaciones falsas · Operador distraído",
    warning_signs:
      "Padre mirando con celular afuera · niño más cerca de la barricada que el padre · hora de salida de escuela · '¿esto es seguro?' del padre · padre llamando a la escuela mientras mira",
    what_to_do:
      "1. Antes de retroceder/girar: ojos en cada peatón a 50 pies, INCLUYENDO niños.\n2. Spotter para CADA retroceso cuando la escuela está a 500 pies.\n3. Ventana de salida (2:45-3:30 PM): no retroceso, no giro, no carga aérea.\n4. Si un padre se acerca: para, guantes afuera, baja la voz, reconoce.\n5. Todas las preguntas al foreman o PM. Operador no negocia.\n6. Si un niño cruza la barricada: PARA todo. Reset barricada. Incidente — 'Public / Third Party · Near-Miss'.",
    what_not_to_do:
      "No digas 'esto es seguro, señora' — no puedes garantizarlo.\nNo retrocedas sin spotter en ventana escolar.\nNo bromees cerca de zona escolar — padres asumen lo peor.\nNo discutas con el celular grabando. Reconoce que graban, mantente calmado, enruta al supervisor.",
    supervisor_actions:
      "Pre-plan ventanas escolares en cada proyecto a 500 pies de escuela. Coordina con el oficial de recursos escolares antes de mobilización. Si un padre escala: en persona, no por teléfono.",
    documentation:
      "Tipo 'Public / Third Party'. Clasificaciones: Public Interaction + Verbal Confrontation si aplica + Near-Miss si el niño cruzó. Nota la escuela por nombre. Foto de barricada ANTES y DESPUÉS.",
    corrective_actions:
      "Verificar barricada < 30 pulgadas cerca de escuela.\nSpotter asignado para cada retroceso en ventana.\nOficial de recursos escolares notificado en 24 horas.",
    read_aloud:
      "Los niños son distintos. Los adultos se quedan afuera de la barricada. Los niños no. Corren, persiguen una pelota, no ven la excavadora. Si trabajan cerca de una escuela o parque: nada de retroceso sin spotter — nada. Entre 2:45 y 3:30, no se gira el brazo, no se carga aéreo. Si un padre se acerca — aunque esté enojado — para, respira, llama al supervisor. No discutas con un padre. No vas a ganar.",
    references_cited:
      "OSHA 1926 Subpart G · MOT de FDOT zona escolar · Política de Trato Público de MASCI",
    action_items:
      "Ventana escolar en el JHA · Spotter asignado · Contacto del oficial escolar en archivo",
  },

  verbal_threats_harassment: {
    title: "Amenazas Verbales y Acoso",
    incident_pattern:
      "Una amenaza verbal parece nada — hasta que es la pieza sobre la que se construye una declaración. Patrón real: alguien grita 'te agarro afuera en el estacionamiento.' Cuadrilla se ríe. Tres días después, esa persona está esperando en el mismo estacionamiento. La amenaza que no se documentó es la amenaza que la compañía no puede probar. El acoso: el mismo residente, todas las mañanas, en la ventana del foreman, por una semana. El jueves el foreman está corto. El viernes explota. El sábado está en la portada del grupo de Facebook local. TODA amenaza verbal o acoso se reporta, incluso las 'menores'.",
    hazards_reviewed:
      "Amenaza verbal directa · Amenaza implícita · Acoso repetido · Patrón de stalking · Represalia de cuadrilla · Daño reputacional",
    warning_signs:
      "Misma persona, varios días, misma cuadrilla\n'Amenaza desde la calle'\nAmenaza con nombre ('te agarro a TI')\nReferencias a armas, vehículos, 'después del turno'\nConocer datos personales (tu camión, tu calle, tu esposa)\nUn miembro de cuadrilla que 'ya no dice nada al respecto'",
    what_to_do:
      "1. Documenta la PRIMERA. Hora, lugar, quién dijo, quién oyó, palabras exactas.\n2. Dile al supervisor ANTES del fin de turno. No la próxima semana.\n3. Si la amenaza es específica (nombre, hora, lugar, arma) — llama al 911. Específico = creíble.\n4. Si la misma persona lo hizo dos veces — llama al 911. Patrón = stalker.\n5. Varía tu ruta de salida. No estaciones en el mismo lugar dos días seguidos.\n6. Sal en parejas si hay amenaza creíble.",
    what_not_to_do:
      "No lo manejes 'como cuadrilla.' Para eso está la compañía.\nNo confrontes al agresor 'después del trabajo.' Es exactamente lo que la amenaza quiere.\nNo minimices ('estaba hablando por hablar').\nNo compartas información personal — nunca confirmes tu calle, el nombre de tu esposa, la placa de tu camión.",
    supervisor_actions:
      "Incidente el MISMO día. Clasificación 'Public Interaction + Threat' mínimo; '+ Harassment' si hay patrón. Si es creíble, escala a Operaciones y Seguridad ese día. Coordina con HR y Legal si la amenaza nombra a un empleado específico. Verifica el bienestar del empleado señalado.",
    documentation:
      "Cita textual de la amenaza.\nFila por testigo (teléfono, correo, empleador) por cada persona que la oyó.\nSi hubo policía: agencia, oficial, número de caso.\nRevisa redes sociales: ¿la amenaza se repitió en línea? (Sí → media_filmed = true.)",
    corrective_actions:
      "Ruta del empleado señalado variada por 2 semanas.\nSi patrón de acoso: re-evaluación de barricadas + coordinación con el sheriff.\nVerificación de bienestar en 24 horas.",
    read_aloud:
      "Si alguien te grita una amenaza — aunque parezca nada — me lo dices antes de irte a casa. No mañana. Hoy. Si usó tu nombre, dijo dónde te encontraría, o habló de un arma: eso no es nada. Eso es una llamada al 911. No lo manejas 'como cuadrilla.' No vas a buscarlo. Eso es lo que la amenaza quiere. Documentamos TODAS porque los patrones sólo se ven cuando los contamos.",
    references_cited:
      "Guía OSHA · Política de Violencia Laboral de MASCI · § 836.10 Florida Amenazas Escritas",
    action_items:
      "Amenazas documentadas mismo día · Bienestar del empleado verificado · Ruta variada si hay patrón",
  },

  physical_confrontations: {
    title: "Confrontaciones Físicas",
    incident_pattern:
      "Empujones, una mano abierta al pecho, un intento de golpe, un objeto lanzado. Una vez que hay contacto, la 'de-escalación' ya no aplica. El patrón malo: un miembro de la cuadrilla 'no quiere parecer débil' y deja pasar el empujón sin reporte. Dos semanas después, en una discusión sin relación, el mismo agresor da un golpe — y la compañía no tiene registro del primer incidente. Otro patrón: el miembro de la cuadrilla responde con un empujón. Ahora ambos son acusados de agresión. La defensa de la compañía desaparece. Regla: una vez que te tocan, paras, retrocedes, llamas al 911. No respondes. No persigues. No 'arreglas las cosas.' Tu trabajo es ser la señal más limpia en el video que va a las noticias.",
    hazards_reviewed:
      "Empujón con mano abierta · Objeto lanzado · Golpe con puño cerrado · Toma de EPP / ropa · Vehículo usado como arma · Cargos por combate mutuo · Lesión por represalia · Daño reputacional",
    warning_signs:
      "Miembro de cuadrilla ya al alcance del agresor · cuerpo del agresor se ajusta (peso adelante, hombros cuadrados) · agresor se prepara como para golpear · objeto lanzado que falla · una 'segunda persona' uniéndose al agresor",
    what_to_do:
      "1. EN EL MOMENTO en que te tocan: para. Manos visibles. Retrocede, no avances.\n2. Llama al 911. Luego al supervisor.\n3. Si otros de la cuadrilla están al alcance, ponte entre ELLOS y el agresor — defensivo, sin contacto.\n4. Si te derriban: quédate abajo hasta que el agresor se aleje.\n5. Foto del lugar, barricada, EPP, lesión visible en 5 minutos.\n6. Busca evaluación médica aunque te sientas bien — las conmociones se manifiestan después.",
    what_not_to_do:
      "No empujes de vuelta. No persigas. No 'pongas las cosas en orden.'\nNo amenaces de regreso — te vuelves el agresor en el video.\nNo te vayas del lugar antes de que llegue el sheriff.\nNo borres fotos / videos / dashcam.\nNo hables con la prensa, con la familia del agresor, ni publiques en redes.",
    supervisor_actions:
      "Incidente mismo día — Public Interaction + Physical Contact + Physical Assault + Workplace Violence si hay patrón. 911 si no se ha llamado. Operaciones, Safety, HR, Legal INMEDIATAMENTE. Verificación de bienestar del empleado golpeado — físico Y psicológico. Coordina con el oficial sobre el número de caso. Captura contacto de testigos ANTES de que se vayan.",
    documentation:
      "Clasificaciones: Physical Contact = TRUE; Physical Assault = TRUE.\nThreat description: cita textual si hubo amenaza antes.\nFila por testigo con teléfono, correo, empleador — mínimo 2.\nCampos de policía: agencia, oficial, placa, número de caso, número de reporte.\nCampos médicos: tratamiento, instalación, sent_home.\nAdjuntos: police_report, medical, witness_statement, photo, video.",
    corrective_actions:
      "Verificación de bienestar en 24 horas (físico + mental).\nRe-evaluación de barreras del proyecto.\nReporte policial obtenido y adjunto.\nLegal / seguros notificados en 24 horas.\nRevisión ejecutiva en 72 horas.",
    read_aloud:
      "Si alguien te toca — te empuja, intenta golpearte, te lanza algo — PARA. Manos abiertas. Retrocede, no avances. No empujes de vuelta. En el momento en que respondes, deja de ser un video de ELLOS atacándote y se convierte en un video de DOS personas peleando. La compañía pierde el caso. Tú pierdes el caso. Paras. Retrocedes. Llamas al 911. Luego me llamas a mí. Luego tomas fotos del lugar, la barricada, tus manos, tu camisa. Aunque te sientas bien — te revisan. Las conmociones aparecen una hora después.",
    references_cited:
      "29 CFR 1904 (OSHA Recordkeeping) · Política de Violencia Laboral de MASCI · § 784.03 Florida Agresión",
    action_items:
      "Incidente mismo día · 911 llamado · Contacto de testigos capturado · Bienestar verificado · Caso # registrado",
  },

  recording_employees_social_media: {
    title: "Grabación de Empleados / Redes Sociales",
    incident_pattern:
      "Los celulares están afuera para todo. Un transeúnte filma a una cuadrilla en su descanso, publica 'por qué estos tipos están sentados cuando mis impuestos los pagan.' Para el almuerzo tiene 40,000 vistas. Para la cena el PM está al teléfono con el dueño. El patrón malo: un miembro de la cuadrilla ve el celular, dice algo cortante ('ocúpate de tus asuntos'), y ahora el mismo transeúnte tiene un clip de un empleado de MASCI siendo grosero. El clip es lo único que el público ve. La verdad no importa. El tono importa.",
    hazards_reviewed:
      "Video fuera de contexto · Daño reputacional · Represalia de cuadrilla grabada · Doxxing · Reacción del Owner / GC · Retrasos en proyecto",
    warning_signs:
      "Celular al pecho (postura de grabar)\nCámara trasera apuntando a la cuadrilla\nTranseúnte narrando ('Miren a estos tipos…')\nTranseúnte conduciendo LENTO con celular visible\nPregunta tu nombre, el nombre de tu jefe, el dueño del proyecto",
    what_to_do:
      "1. Asume que estás en cámara cuando un extraño está a 30 pies. Actúa así.\n2. Si te abordan: corto y educado. 'Señor/Señora, el project manager puede darle esa información. Déjame llamarlo.'\n3. No respondas a provocaciones. Camina a la barricada o vehículo.\n4. Nota la hora, la descripción, y dile al foreman.\n5. Si tu cara o placa aparece pública: supervisor + HR. NO respondas tú al post.",
    what_not_to_do:
      "No digas 'apaga eso' — Florida es de un solo consentimiento, los espacios públicos son filmables.\nNo apuntes a la cámara.\nNo des tu apellido, ciudad, ni el nombre de tu jefe en cámara.\nNo publiques un contra-video.\nNo comentes en el post original.\nNo dejes que la cuadrilla comparta el link en el chat grupal.",
    supervisor_actions:
      "Si aparece clip viral: PM, Operaciones, HR ese MISMO día. No participes en el post. Documenta URL + screenshots antes de que se borre. Marca social_media_posted en cualquier incidente relacionado. Comunica al Owner / GC antes de que se enteren por terceros.",
    documentation:
      "Incidente tipo 'Public / Third Party' aunque no hubo interacción — exposición viral ES un incidente.\nClasificaciones: Public Interaction + Verbal Confrontation si aplica.\nMedia filmed = TRUE.\nSocial media posted = TRUE si hay post público.\nAdjunto: foto del dispositivo si grabaron abierto, screenshot del post con URL.",
    corrective_actions:
      "Briefing 'asume cámara encendida.'\nRevisión de cumplimiento de política de redes.\nSi hay doxxing: HR + Legal + IT.",
    read_aloud:
      "Cuando están en el trabajo, asuman que el celular está grabando. Siempre. Si alguien se acerca con cámara — educado. Corto. Dile 'el project manager puede contestar, déjame llamarlo.' No discutas con la cámara. No apuntes a la cámara. No digas algo que no quieras que tu hijo vea. Somos invitados en esta calle. La manera en que actúas en cámara es la manera en que el público recordará a MASCI.",
    references_cited:
      "§ 934 Florida (Espacios públicos exentos) · Política de Redes Sociales de MASCI",
    action_items:
      "Cuadrilla informada · Foreman conoce clasificación · URL capturada si viral",
  },

  media_public_questions: {
    title: "Medios y Preguntas del Público",
    incident_pattern:
      "Una camioneta de noticias se estaciona. Un reportero baja con micrófono, camarógrafo a 10 pies. Caminan hacia el foreman con 'sólo unas preguntas sobre el proyecto.' El foreman trata de ayudar, dice algo inexacto sobre el cronograma, el reportero lo acepta, y ahora el GC + Owner + DOT están al teléfono al mediodía. El patrón malo NO es ser maleducado — es ser servicial. Los miembros de cuadrilla no tienen contexto para hablar por el proyecto. Las preguntas de medios van a UNA persona: el vocero designado (PM u Operaciones).",
    hazards_reviewed:
      "Cita errónea de medios · Declaración de cronograma/alcance inexacta · Miembro de cuadrilla convertido en cara pública · Daño de confianza con Owner / GC · Retrasos políticos",
    warning_signs:
      "Cámara y micrófono caminando hacia ti\nUn carro estacionado al otro lado con alguien con libreta\n'Sólo una pregunta rápida'\nUna pregunta que comienza con 'por qué se está tomando tanto tiempo'\nUna pregunta que menciona a un concejal por nombre",
    what_to_do:
      "1. Educado, corto. 'Aprecio la pregunta, pero el project manager maneja las preguntas de medios. Déjame conseguir su contacto.'\n2. Foreman guarda la tarjeta del PM en la cabina.\n3. No digas 'sin comentarios' — di 'el project manager maneja esas preguntas y puede contestar completamente.'\n4. Notifica al PM en 5 minutos.\n5. Documenta: medio, reportero, hora, qué preguntó.",
    what_not_to_do:
      "No estimes el cronograma.\nNo estimes el costo.\nNo digas el nombre del Owner ni del GC a menos que ya sea público.\nNo digas 'el GC nos obligó' o 'el DOT nos obligó.'\nNo digas 'sin comentarios' — suena culpable.\nNo dejes que la cámara filme dentro de la zona sin aprobación del PM.",
    supervisor_actions:
      "Foreman tiene tarjeta de protocolo en cada cabina — PM primero, Operaciones segundo. Si medios aparecen sin anunciar, el PM se entera en 5 minutos. Si hay una historia controversial, el PM coordina una respuesta unificada con Owner + GC antes de cualquier compromiso de la cuadrilla.",
    documentation:
      "Nota: medio, reportero, estación/periódico, hora, lugar, preguntas.\nNo siempre requiere incidente — pero si fue contencioso: clasificación 'Public Interaction'.\nSi fue filmado: media filmed = TRUE.",
    corrective_actions:
      "Tarjeta de contacto del PM actualizada en cada cabina.\nSi el mismo medio regresa varias veces: PM coordina respuesta única en cámara con aprobación del Owner.",
    read_aloud:
      "Si un reportero se acerca, sonríe, sé educado, entrégale la tarjeta del PM y dile 'el project manager maneja esas preguntas y puede contestar completamente.' No estimes el cronograma. No digas el costo. No culpes al GC ni al DOT. No digas 'sin comentarios' — suena mal. La línea es: 'el project manager maneja eso.' Luego me llamas a mí.",
    references_cited:
      "SOP de Relaciones con Medios de MASCI · Cláusulas de medios del contrato del Owner",
    action_items:
      "Tarjeta del PM en cada cabina · Foreman entrenado en 'respuesta de una línea' · Encuentro con medios registrado",
  },

  trespassing_into_work_zones: {
    title: "Intrusión en Zonas de Trabajo",
    incident_pattern:
      "Ciudadanos cortan camino. Lo han hecho cada día por cinco años y ahora estamos en el medio. Peatones se meten detrás de la barricada porque el desvío es 200 pies más largo. Niños en bici cruzan derecho. Personas con perros cruzan en la apertura. El peor patrón: alguien pisa una zanja mientras el operador está girando. La lección de los cuasi-accidentes dice una cosa — cada intrusión es un golpe potencial. El otro patrón: el intruso es hostil. Se niega a salir. Saca el celular. El miembro de la cuadrilla que trata de removerlo físicamente se convierte en la historia. Regla: los intrusos se escoltan verbalmente. Si se niegan, paras el trabajo, llamas al sheriff, y documentas. No les pones las manos encima.",
    hazards_reviewed:
      "Peatón golpeado por equipo · Peatón cae en excavación · Intruso hostil · Contacto iniciado por cuadrilla (agresión) · Daño reputacional · Responsabilidad de Owner / ciudad",
    warning_signs:
      "Sendero de tierra a través de la apertura (la gente ha estado cortando)\nUna bicicleta o paseador de perros que reduce velocidad cerca\nUn ciclista con audífonos — no oye la alarma de retroceso\nUna persona en audífonos hacia operación activa\nUna persona sentada en el equipo / apoyada en barricadas",
    what_to_do:
      "1. PARA la operación activa si alguien está dentro de la zona. Señal de mano. Voz. Bocina.\n2. Camina hacia ellos con manos visibles. 'Señor/Señora — hay una excavación activa, necesito que regrese a la banqueta por su seguridad.'\n3. Si cumplen: gracias, escoltar, reset barricada detrás.\n4. Si se niegan: para el trabajo. 911 no-emergencia. Documenta con foto.\n5. Si muestran hostilidad o sacan el celular: igual — para trabajo, llama sheriff, documenta.\n6. NUNCA pongas las manos sobre un intruso. Nunca. Ni una mano guía en el hombro es agresión.",
    what_not_to_do:
      "No persigas. No acorrales.\nNo pongas las manos, ni para 'guiar.'\nNo grites — voz arriba = intrusión escala.\nNo asumas que entienden inglés. Señales de mano + habla lenta.\nNo dejes que se sienten en el equipo 'por un minuto' — si se lastiman, es nuestra responsabilidad.",
    supervisor_actions:
      "Verificar integridad de barricada pre-turno — apertura < 30 pulgadas → recommit. Si la misma dirección / esquina muestra sendero de desgaste: rediseñar barricada. Si la intrusión fue hostil o repetida, incidente con clasificación 'Public Interaction + Trespass'.",
    documentation:
      "Incidente tipo 'Public / Third Party' para intrusiones hostiles/repetidas.\nClasificaciones: Public Interaction + Trespass (texto libre).\nSi el intruso fue golpeado: tipo cambia a 'Injury / Illness' co-clasificado 'Public Interaction'.\nFotos de barricada ANTES y DESPUÉS.",
    corrective_actions:
      "Re-diseño de barricada en 24 horas si sendero confirmado.\nSeñalización MOT adicional vía PM.\nSi intrusión en escuela: oficial escolar notificado.",
    read_aloud:
      "Si alguien está dentro de la barricada — PARA. Señal de mano, bocina, lo que sea. Camina hacia ellos con manos visibles. Dile 'hay una excavación activa, por favor regrese a la banqueta por su seguridad.' Si escuchan — gracias y reset barricada detrás. Si no escuchan — PARA el trabajo, 911 no-emergencia, toma una foto. No le pones las manos a nadie. Nunca. Ni guiándolos del codo es agresión. No ganamos esa pelea.",
    references_cited:
      "OSHA 1926 Subpart G · § 810.09 Florida Intrusión · SOP de Trato Público de MASCI",
    action_items:
      "Chequeo de barricada pre-turno · Sendero identificado y mitigado · Regla 'no tocar' reforzada",
  },

  drone_overhead_survey_ops: {
    title: "Operaciones de Dron y Levantamiento Aéreo",
    incident_pattern:
      "Los drones son ahora parte del levantamiento, documentación de avance, dashboards del Owner. La cuadrilla se acostumbra a la actividad aérea. El público no. Un dron sobre un vecindario a las 8 AM genera un post en Nextdoor a las 8:15 con acusación de vigilancia. Para el mediodía hay una llamada a la ciudad. Para la mañana siguiente el mismo vecino está con el foreman con 'por qué me espían.' El otro patrón es la seguridad real: un dron amateur cruza la zona. El brazo del excavador y las hélices en el mismo espacio = dron perdido en la cuchara o un operador en pánico. Regla: cada operación aérea se anuncia, se publica, y se informa a la cuadrilla; cada pregunta del público recibe el trato de vocero PM.",
    hazards_reviewed:
      "Preocupación de privacidad · Colisión de dron con equipo · Incumplimiento FAA · Distracción de cuadrilla · Daño reputacional",
    warning_signs:
      "Un vecino afuera mirando el dron\nUn dron amateur visible durante nuestra operación\nUn vecino acercándose con celular y '¿por qué vuela sobre mi alberca?'\nUn funcionario de la ciudad pidiendo el papeleo Part 107\nUn miembro de cuadrilla mirando arriba en lugar de la zanja mientras el equipo se mueve",
    what_to_do:
      "1. Publica operaciones de dron 24 horas antes en la señalización del proyecto Y en el cronograma público.\n2. Piloto al mando (PiC) en sitio con Part 107 en mano.\n3. Briefing pre-vuelo — equipo apaga durante el paso del levantamiento.\n4. Si pregunta del público durante el vuelo: piloto mantiene línea de vista; foreman maneja con la línea PM-vocero.\n5. Si un dron amateur entra a nuestro espacio: piloto baja el nuestro inmediato. Foreman nota hora y dirección.",
    what_not_to_do:
      "No vueles sin un PiC Part 107.\nNo vueles sin briefing.\nNo vueles sobre excavación activa con gente en la zanja.\nNo discutas la pregunta de privacidad en cámara — enruta al PM.\nNo 'reposiciones' el dron más cerca de la propiedad del vecino para mejor toma.",
    supervisor_actions:
      "Verificar papeleo Part 107 antes de cada vuelo. Coordinar con ciudad / FAA si requiere autorización. Briefing de cuadrilla. Publicar cronograma. Si hay queja de privacidad: PM responde por escrito con razón del levantamiento y confirmación de que propiedad residencial no es el objetivo.",
    documentation:
      "Bitácora de vuelo: piloto, hora, duración, propósito, ref papeleo.\nInteracción pública durante vuelo: tipo 'Public / Third Party' si contencioso; clasificación 'Public Interaction'.\nSi dron amateur entró: tipo 'Public / Third Party' + 'Near-Miss' + describir trayectoria.",
    corrective_actions:
      "Operaciones publicadas en cronograma público.\nPart 107 en sitio cada vuelo.\nSi dron amateur entró: notificación FAA + PM notifica al Owner.",
    read_aloud:
      "Cuando el dron está arriba, dos cosas importan. UNO — no volamos sobre la zanja con gente adentro. El equipo para, la cuadrilla recibe briefing, luego volamos. DOS — si un vecino se acerca preguntando por qué volamos sobre su alberca, somos educados y cortos. 'El project manager maneja esas preguntas, déjame conseguir su tarjeta.' No te metas en 'no te estoy espiando' en cámara. Vas a perder. El PM maneja las preguntas de privacidad. Nosotros sólo volamos seguro.",
    references_cited:
      "14 CFR Part 107 · Autorización FAA LAANC · SOP de Drones de MASCI · Política de Trato Público de MASCI",
    action_items:
      "Part 107 en sitio · Cronograma publicado · Cuadrilla informada pre-vuelo · Preguntas de privacidad enrutadas al PM",
  },
};
