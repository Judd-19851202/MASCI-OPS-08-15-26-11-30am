"""Spanish translations for the HelpTip registry.

Keyed by (form_key, kind) tuples for exact matching with tips.py.
Merged at import-time via tips._merge_es().
"""

from __future__ import annotations

TIPS_ES: dict[tuple[str, str], dict] = {
    # ── daily-report (top-level) ─────────────────────────────────────
    ("daily-report", "why"): {
        "title_es": "Por qué importan los Reportes Diarios",
        "body_es":
            "Un Reporte Diario se vuelve el registro oficial del día de trabajo. "
            "RH lo usa para tiempo, PM para estado de proyecto, Seguridad para "
            "contexto de incidentes. Constrúyalo como si alguien lo fuera a leer "
            "en seis meses — porque alguien lo hará.",
    },
    ("daily-report", "who"): {
        "title_es": "Quién lo ve",
        "body_es":
            "Su PM, RH, Seguridad y admin. Dueños en una revisión de proyecto "
            "también pueden consultarlo. Personal de campo fuera del proyecto "
            "usualmente no puede.",
    },
    ("daily-report", "next"): {
        "title_es": "Qué pasa después de enviar",
        "body_es":
            "Las horas fluyen a RH para verificación de tiempo. Materiales y "
            "equipo fluyen a la codificación de costo de PM. Las fotos y notas "
            "se adjuntan al registro del proyecto. Las ediciones después del "
            "envío se rastrean.",
    },
    ("daily-report", "escalate"): {
        "title_es": "Cuándo escalar",
        "body_es":
            "Si pasó algo en el sitio que necesita atención de Seguridad — "
            "lesión, casi-incidente, tercero — llene también el formulario de "
            "Incidente de Seguridad. El Reporte Diario solo no es suficiente.",
    },

    # ── daily-report.crew ────────────────────────────────────────────
    ("daily-report.crew", "why"): {
        "title_es": "Por qué importa la cuadrilla",
        "body_es":
            "Esta es la fuente de verdad del campo para horas trabajadas. RH "
            "reconcilia nómina contra esto. Si un nombre o conteo de horas "
            "está mal aquí, el cheque de alguien está mal el viernes.",
    },
    ("daily-report.crew", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Listar un trabajador que no se presentó. Listar horas 'a ojo' en "
            "vez de por el tiempo real en sitio. Olvidar quitar a alguien que "
            "se fue temprano. Redondee al cuarto de hora, no a la hora completa.",
    },
    ("daily-report.crew", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Smith, J — 6:00 a 14:30 (8.0h reg, 0.5h almuerzo)' es bueno. "
            "'Smith — día completo' no — nómina no puede verificarlo.",
    },

    # ── daily-report.equipment ───────────────────────────────────────
    ("daily-report.equipment", "why"): {
        "title_es": "Por qué importa el equipo",
        "body_es":
            "Esto alimenta los reportes de utilización del proyecto y de "
            "asignación de equipo. Si una unidad no está listada aquí, "
            "finanzas no puede facturarla al proyecto.",
    },
    ("daily-report.equipment", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Listar equipo que no se usó. Saltarse horas inactivas (inactividad "
            "todavía cuenta contra utilización). Listar el ID de unidad "
            "equivocado — siempre confirme desde el costado de la unidad, no "
            "de memoria.",
    },

    # ── daily-report.materials ───────────────────────────────────────
    ("daily-report.materials", "why"): {
        "title_es": "Por qué importan los materiales",
        "body_es":
            "Los materiales impulsan la asignación de código de costo. El "
            "margen de proyecto del PM se calcula contra lo que se registra "
            "aquí. Aproximado está bien — adivinar al azar no.",
    },
    ("daily-report.materials", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Piedra, base 3/4\" — 18 toneladas colocadas en la plataforma "
            "norte' es bueno. 'Algo de piedra' no — finanzas no puede "
            "asignarle código de costo.",
    },

    # ── daily-report.photos ──────────────────────────────────────────
    ("daily-report.photos", "why"): {
        "title_es": "Por qué importan las fotos",
        "body_es":
            "Las fotos protegen a todos. Una foto del trabajo terminado hoy es "
            "evidencia incontestable meses después cuando llega una disputa. "
            "Son baratas de tomar e imposibles de recrear después del hecho.",
    },
    ("daily-report.photos", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Tomar fotos desde muy lejos (sin escala). Fotografiar solo el "
            "trabajo terminado y no fotos de progreso. Olvidar una foto de "
            "cualquier daño que encontró al inicio del día — así evita ser "
            "culpado por él.",
    },

    # ── daily-report.narrative ───────────────────────────────────────
    ("daily-report.narrative", "why"): {
        "title_es": "Por qué importa la narrativa",
        "body_es":
            "La narrativa es lo que un PM o admin lee primero cuando algo se "
            "ve fuera de lugar. Dos oraciones de contexto ahora ahorran veinte "
            "minutos de llamadas en una semana.",
    },
    ("daily-report.narrative", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Escribir 'todo normal' cuando no lo fue. Escribir solo lo que "
            "salió bien. Olvidar el clima/condiciones que retrasaron la "
            "cuadrilla — ese contexto es exactamente lo que defiende contra "
            "una pregunta de '¿por qué fue baja la producción?' después.",
    },
    ("daily-report.narrative", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Viento 25+ mph toda la mañana; trabajo de grúa retrasado 2.5h. "
            "Reanudado 11:00, vaciado completado 15:30. Sin incidentes.' es "
            "excelente. Explica por qué la producción fue baja Y que nada más "
            "salió mal.",
    },

    # ── iter210 · Safety Incidents ───────────────────────────────────
    ("incident", "why"): {
        "title_es": "Por qué importa este reporte",
        "body_es":
            "Un reporte de incidente es un documento legal en el momento que lo "
            "envía. OSHA, seguros y cualquier investigación futura lo leen. "
            "Calmado, específico y factual ahora le gana a apologético y vago después.",
    },
    ("incident", "who"): {
        "title_es": "Quién lo ve",
        "body_es":
            "Personal de Seguridad (inmediatamente), PM y RH (dentro de 24h), "
            "Admin, y cualquier parte externa formalmente involucrada en la "
            "respuesta. Trate cada campo como si un abogado lo fuera a leer mañana.",
    },
    ("incident", "next"): {
        "title_es": "Qué pasa después de enviar",
        "body_es":
            "Seguridad abre una investigación. Las acciones correctivas se "
            "asignan y rastrean hasta el cierre. El incidente se adjunta al "
            "proyecto y al equipo involucrado. Puede que le pidan más detalle — "
            "es normal.",
    },
    ("incident", "escalate"): {
        "title_es": "Cuándo llamar antes de reportar",
        "body_es":
            "Lesión grave, hospitalización, fatalidad o cualquier involucramiento "
            "de un tercero: llame a su supervisor Y a Seguridad por teléfono "
            "primero. No espere a que cargue el formulario. El formulario es el "
            "registro; la llamada telefónica es la respuesta.",
    },

    ("incident.location", "why"): {
        "title_es": "Por qué la ubicación debe ser específica",
        "body_es":
            "'En el sitio' no es suficiente. La ubicación exacta decide qué "
            "supervisor responde, a qué jurisdicción van los reportes, y si un "
            "peligro recurrente surge en una revisión de patrones.",
    },
    ("incident.location", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Estación 12+50 carril norte, cerca de la entrada de drenaje este' "
            "es bueno. 'Carretera 30' no — el proyecto tiene 8 millas de largo.",
    },
    ("incident.location", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Escribir una ubicación vaga para ahorrar 30 segundos, y luego "
            "tener que corregirla bajo presión cuando Seguridad llama de vuelta. "
            "Use GPS si puede — los teléfonos son lo suficientemente precisos "
            "para documentar incidentes.",
    },

    ("incident.narrative", "why"): {
        "title_es": "Por qué la narrativa es el corazón del reporte",
        "body_es":
            "Los investigadores reconstruyen el evento desde este párrafo. La "
            "especulación debilita el registro; los hechos observados lo "
            "fortalecen. Escriba lo que vio, escuchó e hizo — en ese orden.",
    },
    ("incident.narrative", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Adivinar sobre causas ('él debió...'). Asignar culpa en la "
            "narrativa. Saltarse la línea de tiempo. Usar lenguaje emocional. "
            "Cada uno de esos debilita el reporte cuando más importa.",
    },
    ("incident.narrative", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'14:22 — operador se bajó de la excavadora. Pisó terreno disparejo "
            "cerca de la oruga. Perdió balance, cayó sobre rodilla derecha. "
            "Reportó dolor. La cuadrilla detuvo trabajo. Primeros auxilios "
            "aplicados. 14:35 — supervisor notificado.' es exactamente la forma correcta.",
    },

    ("incident.severity", "why"): {
        "title_es": "Por qué la severidad es difícil pero importante",
        "body_es":
            "La severidad impulsa el cronograma de respuesta. 'Menor' que "
            "realmente es moderado retrasa la atención de Seguridad; 'Grave' "
            "que realmente es menor crea un patrón de falsas alarmas. Si tiene "
            "dudas, suba un nivel y deje que Seguridad lo baje.",
    },
    ("incident.severity", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Minimizar la severidad para evitar molestias. Marcar 'Casi-Incidente' "
            "para algo con respuesta de primeros auxilios. Llamar a cualquier "
            "cosa con ambulancia 'Menor'. La severidad es un juicio de "
            "Seguridad, no una escala de vergüenza personal.",
    },

    ("incident.witnesses", "why"): {
        "title_es": "Por qué los testigos importan incluso si usted lo vio",
        "body_es":
            "La memoria se desvanece rápido y las historias derivan. Una "
            "declaración de testigo capturada en horas vale más que diez "
            "capturadas la próxima semana. Incluso una línea de 'vi X' de un "
            "compañero le gana a no tener registro.",
    },
    ("incident.witnesses", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Aconsejar a un testigo sobre qué escribir. Combinar dos testigos "
            "en una entrada. Saltarse un testigo porque 'solo vio el final'. "
            "Cada testigo tiene su propia fila, sus propias palabras, en su orden.",
    },
    ("incident.witnesses", "escalate"): {
        "title_es": "Cuándo un testigo rehúsa dar declaración",
        "body_es":
            "Documente que estuvo presente, que usted preguntó, y que él "
            "declinó. No lo presione. Anote la negativa en la narrativa y "
            "dígaselo a Seguridad verbalmente. Ellos manejan desde ahí.",
    },

    ("incident.corrective", "why"): {
        "title_es": "Por qué las acciones correctivas cierran el ciclo",
        "body_es":
            "Un incidente sin acción correctiva es un incidente recurrente. "
            "Incluso una nota pequeña — 'conos agregados en el escalón "
            "disparejo', 'cuadrilla informada' — previene el mismo evento el "
            "próximo mes.",
    },
    ("incident.corrective", "next"): {
        "title_es": "Qué pasa después de listar acciones",
        "body_es":
            "Seguridad revisa y puede agregar más. Cada acción tiene un dueño "
            "y una fecha. El incidente no se cierra hasta que cada acción se "
            "verifica completa y se firma — esa es la pista de auditoría.",
    },
    ("incident.corrective", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Escribir 'tener más cuidado' como acción correctiva. No es "
            "accionable, ni verificable, ni auditable. Indique un cambio "
            "concreto: nueva señalización, nuevo procedimiento, recapacitación, "
            "reparación de equipo.",
    },

    # ── iter211 · Pre-Op Equipment Inspection ────────────────────────
    ("preop", "why"): {
        "title_es": "Por qué importa este Pre-Op",
        "body_es":
            "Los Pre-Ops no son papeleo. El operador antes de usted confió en "
            "el suyo; el operador después de usted confía en el suyo. Marque "
            "solo lo que ha revisado físicamente.",
    },
    ("preop", "who"): {
        "title_es": "Quién lo ve",
        "body_es":
            "Su capataz de Taller, Despacho, su supervisor, y el siguiente "
            "operador que use esta unidad. Si algo falla en esta máquina hoy, "
            "este es el primer registro que cualquiera lee.",
    },
    ("preop", "next"): {
        "title_es": "Qué pasa después de enviar",
        "body_es":
            "Pasa → la unidad queda operativa. Falla → va al Taller. Falla "
            "mayor (frenos, dirección, ROPS, fuga de manguera) → Fuera de "
            "Servicio hasta que se libere. Su firma es la liberación de esta "
            "unidad del día.",
    },
    ("preop", "escalate"): {
        "title_es": "Cuándo detenerse y llamar",
        "body_es":
            "Elementos críticos de seguridad fallando — frenos, dirección, "
            "hidráulicos con fuga activa, ROPS faltante o dañado — deténgase. "
            "Llame a su supervisor antes de firmar nada. No trate de "
            "manejarla 'solo por hoy'.",
    },

    ("preop.fluids", "why"): {
        "title_es": "Por qué importan las revisiones de fluidos",
        "body_es":
            "Las fugas de hoy son las reparaciones de mañana y las descomposturas "
            "de la próxima semana. Atrapar un sudor en el cilindro mientras es "
            "una mancha húmeda es la reparación más barata que esta máquina "
            "tendrá.",
    },
    ("preop.fluids", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Marcar 'bien' porque la varilla salió bien. Las revisiones de "
            "fluido son visuales Y un vistazo al suelo bajo la unidad. Suelo "
            "mojado bajo una máquina estacionada casi nunca significa lluvia.",
    },
    ("preop.fluids", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Sudor hidráulico en cilindro de inclinación izquierdo — "
            "operativo, monitorear diariamente.' es bueno. 'OK' no — no hay "
            "nada ahí con lo que el mecánico pueda actuar.",
    },

    ("preop.tires-tracks", "why"): {
        "title_es": "Por qué importan llantas y orugas",
        "body_es":
            "Las llantas y orugas son lo único entre la máquina y el suelo. "
            "Una garra desgastada o PSI baja aparece primero como un día que "
            "'se siente raro' — regístrelo antes de que aparezca como una "
            "llamada de recuperación.",
    },
    ("preop.tires-tracks", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Pasar por un solo lado. Los operadores favorecen el mismo lado "
            "cada día. Camine las cuatro esquinas en cada Pre-Op — así es "
            "como atrapa lo que la rutina deja pasar.",
    },

    ("preop.controls", "why"): {
        "title_es": "Por qué importan los controles",
        "body_es":
            "Cada control que se salta de revisar es algo que descubrirá en el "
            "momento equivocado. Dos minutos en el asiento ahora le ganan a "
            "dos horas esperando un mecánico después.",
    },
    ("preop.controls", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Alarma de reversa intermitente — funciona en frío, silenciosa "
            "después de calentar.' es exactamente lo que el Taller necesita. "
            "'Alarma de reversa rota' no le dice al Taller cuándo ni cómo.",
    },

    ("preop.defects", "why"): {
        "title_es": "Por qué importa el registro honesto de defectos",
        "body_es":
            "Un defecto registrado honestamente es un defecto que se arregla. "
            "Un defecto escondido se vuelve el incidente del siguiente "
            "operador. Los Pre-Ops son el registro de seguridad más leído de "
            "la plataforma.",
    },
    ("preop.defects", "next"): {
        "title_es": "Qué pasa después de un Falla",
        "body_es":
            "Los elementos fallidos van al Taller/Flota dentro de la hora. "
            "Foto + nota específica acelera la respuesta por horas. Notas "
            "vagas la frenan — el Taller no puede despachar una pieza con "
            "'algo está mal'.",
    },
    ("preop.defects", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Marcar 'falla' sin foto. Saltarse la nota porque 'ya lo verán'. "
            "No verán lo que usted no les muestra. Foto + una oración es la "
            "regla.",
    },

    ("preop.signoff", "why"): {
        "title_es": "Por qué la firma es su palabra",
        "body_es":
            "Su firma en un Pre-Op es su palabra. El operador antes de usted "
            "firmó de buena fe — devuelva el favor. Si no lo revisó "
            "físicamente, no firme por él.",
    },
    ("preop.signoff", "escalate"): {
        "title_es": "Cuándo la presión para firmar se siente mal",
        "body_es":
            "Si su supervisor lo presiona para firmar por algo que no revisó, "
            "o para marcar un elemento fallido como aprobado, dígale a "
            "Seguridad. Eso no es un problema de personalidad — es un problema "
            "de cultura de seguridad, y Seguridad quiere saberlo.",
    },

    # ── iter212 · Equipment Checkout ─────────────────────────────────
    ("checkout", "why"): {
        "title_es": "Por qué importa el Checkout de Equipo",
        "body_es":
            "El Checkout es la promesa: usted dice 'tengo esto', el sistema "
            "dice 'lo tiene'. Cuando algo se pierde o se daña, el Checkout "
            "es el primer registro que alguien lee. Su nombre está en él.",
    },
    ("checkout", "who"): {
        "title_es": "Quién lo ve",
        "body_es":
            "Su capataz, Taller (rastrear estado del activo), Despacho "
            "(disponibilidad), RH (rendición de cuentas del empleado), y "
            "Admin. Su supervisor lo ve dentro del minuto que usted firma.",
    },
    ("checkout", "next"): {
        "title_es": "Qué pasa después de firmar",
        "body_es":
            "La unidad sale de la disponibilidad de Despacho y entra en su "
            "registro personal de rendición de cuentas. Permanece ahí hasta "
            "que la devuelva o la transfiera oficialmente — sin firma de "
            "devolución, sigue siendo su responsabilidad.",
    },
    ("checkout", "escalate"): {
        "title_es": "Cuándo no firmar todavía",
        "body_es":
            "Si la unidad le llega con daño no documentado, deténgase y "
            "documéntelo antes de firmar. Una vez que firma, ese daño es "
            "operacionalmente suyo a menos que pueda demostrar que estaba "
            "ahí antes.",
    },

    ("checkout.condition", "why"): {
        "title_es": "Por qué la condición al recibir importa",
        "body_es":
            "El registro de condición al checkout es lo único que separa el "
            "'lo recibí así' de 'yo lo hice'. Treinta segundos de notas y "
            "fotos ahora le ahorran horas de explicación cuando ocurre una "
            "disputa.",
    },
    ("checkout.condition", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Marcar 'bueno' sin caminar la unidad. Saltarse las fotos porque "
            "'se ve bien'. Aceptar la palabra del operador anterior sin "
            "verificar. Confíe en la unidad por sí mismo — el operador antes "
            "de usted firmó de buena fe, pero ahora es su turno.",
    },
    ("checkout.condition", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Rasguño existente — guardabarros trasero izquierdo, ~6 pulgadas. "
            "Foto adjunta. Espejo lateral derecho lleno de polvo pero "
            "intacto.' es bueno. 'Condición OK' no — no hay registro para "
            "regresar.",
    },

    ("checkout.signature", "why"): {
        "title_es": "Por qué la firma es rendición de cuentas, no formalidad",
        "body_es":
            "Su firma es el momento en que el sistema le pasa la "
            "responsabilidad operacional. No es un campo más. Es el "
            "compromiso de cuidar este equipo como si fuera suyo — porque "
            "para todos los efectos prácticos, lo es ahora.",
    },
    ("checkout.signature", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Firmar primero, revisar después. Firmar con un nombre garabateado "
            "que no es claramente el suyo. Firmar por alguien más 'porque "
            "está manejando ahora mismo'. Todos esos rompen la pista de "
            "auditoría cuando importa.",
    },
    ("checkout.signature", "escalate"): {
        "title_es": "Cuándo NO firmar",
        "body_es":
            "Si Taller o Despacho insiste en que firme por equipo que aún no "
            "ha visto físicamente o caminado, no lo haga. Eso no es un "
            "atajo — es transferir la culpa antes de tiempo. Llame a su "
            "supervisor.",
    },

    ("checkout.return-expectations", "why"): {
        "title_es": "Por qué importan las expectativas de devolución",
        "body_es":
            "El Checkout es la mitad delantera de un par. El Return cierra "
            "el ciclo. Saber qué se espera al devolver — limpieza, "
            "documentación de fluidos, fotos — convierte el día final en "
            "30 segundos en vez de una semana de disputas.",
    },
    ("checkout.return-expectations", "next"): {
        "title_es": "Lo que viene cuando devuelve",
        "body_es":
            "Una firma de Return + foto cierran el Checkout. Daño descubierto "
            "en el Return abre un caso de daño — su nota original de "
            "condición al checkout es lo que decide si es suyo o no. "
            "Documente bien al inicio para evitar disputas al final.",
    },

    ("checkout.photos", "why"): {
        "title_es": "Por qué importan las fotos al checkout",
        "body_es":
            "Las fotos no son opcionales — son el único registro objetivo. "
            "La memoria se desvanece; las palabras se interpretan; las "
            "fotos no. Una foto rápida ahora le ahorra una conversación "
            "complicada después.",
    },
    ("checkout.photos", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Una sola foto desde lejos. Saltarse las áreas que importan "
            "(ruedas/llantas, parabrisas, cubiertas, espejos). Tomar fotos "
            "con el sol detrás del equipo y obtener solo siluetas. Cuatro "
            "lados + cabina + cualquier daño existente es el mínimo.",
    },

    # ── iter213 · Time Verification (Tier 2 · RH) ────────────────────
    ("time-verification", "why"): {
        "title_es": "Por qué importa la Verificación de Tiempo",
        "body_es":
            "Aquí es donde las horas de campo se vuelven cheques de pago. "
            "Hágalo bien y los supervisores dejan de oír 'mi cheque está "
            "corto' el lunes por la mañana. Hágalo mal — calladamente — y "
            "la confianza con la cuadrilla tarda meses en reconstruirse. "
            "Su trabajo es el puente entre el campo y el cheque.",
    },
    ("time-verification", "who"): {
        "title_es": "Quién depende de esto",
        "body_es":
            "La cuadrilla primero — su pago depende de estos números. "
            "Después el supervisor que reportó las horas, luego PM (costo "
            "de proyecto), y luego nómina (Exact). Los dueños ven los "
            "totales semanales de OT. Si un número está mal aquí, cada "
            "registro corriente abajo está mal.",
    },
    ("time-verification", "next"): {
        "title_es": "Qué pasa después de verificar",
        "body_es":
            "Las horas verificadas fluyen al export de nómina de Exact. "
            "Cualquier anomalía marcada queda en la lista del lunes del "
            "supervisor. Las correcciones se hacen en la fuente — el "
            "Reporte Diario — no sobrescribiendo números aquí en "
            "silencio.",
    },
    ("time-verification", "escalate"): {
        "title_es": "Cuándo escalar, no corregir",
        "body_es":
            "Si un número se ve mal, llame al supervisor antes de cambiar "
            "nada. Las ediciones silenciosas son cómo una discrepancia de "
            "$40 se vuelve una queja formal. El supervisor edita el "
            "Reporte Diario; usted verifica el resultado. Ese orden "
            "importa.",
    },

    ("time-verification.overtime", "why"): {
        "title_es": "Por qué el OT es semanal, no diario",
        "body_es":
            "El tiempo extra es lo que pasa de 40 horas en la semana "
            "laboral — no 'más de 8 en un día'. Un martes de 10 horas no "
            "es OT si el viernes la semana llega a 38. El OT aparece aquí "
            "una vez que el total semanal cruza las 40; la columna diaria "
            "se queda como regular.",
    },
    ("time-verification.overtime", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Marcar un martes largo como OT antes de cerrar la semana. "
            "Dividir el OT entre trabajos sin preguntarle al supervisor "
            "qué proyecto lo carga. Leer la columna de OT en el día 3 y "
            "asumir que es final — la semana no terminó.",
    },

    ("time-verification.lunch", "why"): {
        "title_es": "Por qué el almuerzo se rastrea pero no se paga",
        "body_es":
            "El almuerzo son los 30 minutos que la cuadrilla se debe a sí "
            "misma y a la empresa. No se paga, pero tiene que estar en el "
            "registro — tanto por cumplimiento como para que las cuentas "
            "del supervisor cuadren. Saltarse el almuerzo no es un atajo "
            "de captura; es un descanso perdido que vale preguntar.",
    },
    ("time-verification.lunch", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Llenar calladamente 0.5 de almuerzo en cada renglón porque "
            "'siempre lo toman'. Eso esconde los días en que no lo "
            "tomaron, que es exactamente la información que el supervisor "
            "y Seguridad necesitan. Si falta el almuerzo, pregunte — no "
            "rellene.",
    },

    ("time-verification.discrepancy", "why"): {
        "title_es": "Por qué las discrepancias son conversaciones, no correcciones",
        "body_es":
            "Cada desajuste entre Reporte Diario y nómina es una historia "
            "que el supervisor conoce y usted aún no. El número no está "
            "mal porque alguien fue flojo — está mal porque el día fue "
            "largo, la hoja se llenó apurado, o la cuadrilla cambió de "
            "trabajo a media jornada. Pregunte primero.",
    },
    ("time-verification.discrepancy", "next"): {
        "title_es": "Cómo se ve la corrección correcta",
        "body_es":
            "Llame al supervisor, escuche la historia, acuerden el número "
            "correcto, y haga que él corrija el Reporte Diario en la "
            "fuente. Luego vuelva a correr la verificación — el número "
            "corregido fluye de regreso aquí y la pista de auditoría "
            "muestra quién cambió qué y por qué.",
    },
    ("time-verification.discrepancy", "escalate"): {
        "title_es": "Cuándo el patrón es el problema",
        "body_es":
            "Una discrepancia aislada pasa. Una cuadrilla que registra "
            "8.00 todos los días por dos semanas seguidas — incluyendo "
            "un día de lluvia conocido — es un patrón de redondeo, no un "
            "error de matemáticas. Eso es una conversación de RH con el "
            "supervisor, no una corrección silenciosa aquí.",
    },

    # ── iter214 · Write-Ups (FL disciplinary documentation) ──────────
    ("writeup", "why"): {
        "title_es": "Por qué importa un Write-Up",
        "body_es":
            "Un write-up es el registro de una conversación que ya "
            "ocurrió — nunca un sustituto de ella. Si el empleado se "
            "entera del write-up antes de que usted hable con él, se "
            "saltó la parte que realmente cambia el comportamiento. El "
            "papel es la evidencia; la conversación es el trabajo.",
    },
    ("writeup", "who"): {
        "title_es": "Quién lo lee después",
        "body_es":
            "RH, el empleado, el supervisor (usted), y — si el patrón "
            "continúa — un futuro gerente decidiendo el siguiente paso. "
            "Meses después, cualquiera que lo lea debe poder imaginarse "
            "el incidente solo con sus palabras. Escriba para ese lector.",
    },
    ("writeup", "next"): {
        "title_es": "Qué pasa después de enviar",
        "body_es":
            "RH lo revisa y lo archiva. El empleado recibe una copia. Si "
            "es un patrón repetido, se une a los registros previos y "
            "puede generar una conversación con RH. Si es la primera "
            "vez, queda en archivo como base para cualquier patrón "
            "futuro.",
    },
    ("writeup", "escalate"): {
        "title_es": "Cuándo llamar a RH antes de enviar",
        "body_es":
            "Violación de seguridad que puso a la cuadrilla en riesgo. "
            "Robo, acoso, o cualquier cosa que toque una clase protegida. "
            "Cualquier caso donde usted no esté seguro si es write-up o "
            "terminación. Llame a RH primero — prefieren acompañarlo a "
            "leerlo el lunes por la mañana.",
    },

    ("writeup.facts", "why"): {
        "title_es": "Por qué hechos, no sentimientos",
        "body_es":
            "'Llegó 22 minutos tarde, 3ra vez este mes, sin llamar' es un "
            "hecho. 'Tiene problema de actitud' es un sentimiento. Los "
            "hechos sostienen; los sentimientos no. El mismo write-up "
            "leído por otra persona debe llegar a la misma conclusión — "
            "eso solo es posible con hechos.",
    },
    ("writeup.facts", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Lenguaje cargado ('flojo', 'no le importa', 'se cree el "
            "dueño'). Tiempos vagos ('últimamente', 'siempre', 'nunca'). "
            "Saltarse los nombres de los testigos. Editorializar lo que "
            "el empleado 'debió estar pensando'. Nada de eso ayuda a la "
            "siguiente persona que lea el archivo.",
    },
    ("writeup.facts", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'2026-05-12, 6:38am — El empleado llegó al patio a las 6:38, "
            "inicio programado 6:15. Sin llamar, sin mensaje. Es la 3ra "
            "llegada tarde en 14 días laborales (2026-04-29, 2026-05-06, "
            "2026-05-12). El capataz Davis estaba en sitio a la hora de "
            "inicio. Conversación sostenida a las 6:40am.' es bueno. "
            "'Tarde otra vez' no lo es.",
    },

    ("writeup.conversation", "why"): {
        "title_es": "Por qué la conversación va primero",
        "body_es":
            "Sorprender a alguien con un write-up que no vio venir "
            "termina la relación. La conversación le da al empleado una "
            "oportunidad justa de explicar, acordar lo que se espera, y "
            "asumir el arreglo. El write-up solo registra lo que ya se "
            "dijo y se acordó.",
    },
    ("writeup.conversation", "next"): {
        "title_es": "Cómo se ve un 'próximo paso acordado'",
        "body_es":
            "Específico, con tiempo, y verificable. 'Llegar a tiempo' no "
            "es acordado — 'llegar al patio a las 6:15 o antes los "
            "próximos 30 días, con llamada antes de las 5:45 si algo lo "
            "va a hacer tarde' sí es acordado. El empleado debe poder "
            "repetirlo.",
    },

    ("writeup.due-process", "why"): {
        "title_es": "Por qué el debido proceso protege a ambos lados",
        "body_es":
            "Un empleado que lee un write-up y no está de acuerdo tiene "
            "derecho a agregar su versión. Eso no es una pérdida para el "
            "supervisor — es el archivo contando toda la verdad en lugar "
            "de la mitad. Un write-up donde solo hay una voz en la "
            "página es más débil, no más fuerte.",
    },
    ("writeup.due-process", "escalate"): {
        "title_es": "Cuándo el empleado no firma",
        "body_es":
            "Documente que usted le ofreció, que rehusó, y que le "
            "explicó que firmar significa 'lo recibí', no 'estoy de "
            "acuerdo'. Luego envíelo de todos modos — el rechazo no "
            "anula el registro. Avise a RH verbalmente para que no se "
            "sorprendan.",
    },
}
