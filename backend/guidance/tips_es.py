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

    # ── iter215 · deepening daily-report.materials ───────────────────
    ("daily-report.materials", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Entradas vagas tipo 'una tarima de conexiones' (¿cuáles "
            "conexiones, cuántas?). Redondear salvajemente a un número "
            "limpio ('como 20 toneladas') cuando el boleto dice 18.4. "
            "Olvidarse de registrar el material que llegó corto — esa es "
            "la conversación que PM necesita tener con el proveedor, no "
            "la sorpresa de la próxima semana.",
    },
    ("daily-report.materials", "next"): {
        "title_es": "Qué pasa después de que PM lo ve",
        "body_es":
            "Las cantidades se cargan al código de costo del proyecto. "
            "Si el uso registrado está muy por encima del plan, PM recibe "
            "una alerta de margen. Si está muy por debajo, inventario "
            "recibe una pregunta de '¿dónde quedó el resto?'. De "
            "cualquier modo, su nota es la primera explicación que se "
            "lee.",
    },
    ("daily-report.materials", "escalate"): {
        "title_es": "Cuándo marcar un cambio ANTES de que sea disputa",
        "body_es":
            "Si el campo usó algo distinto al plan — sustituido, cambió "
            "una especificación, se acabó y tomó de otro trabajo — "
            "escríbalo en palabras claras aquí Y avise a PM verbalmente "
            "el mismo día. Las sustituciones silenciosas son cómo un "
            "trabajo termina en disputa de facturación seis semanas "
            "después.",
    },

    # ── iter216 · deepening daily-report.equipment ───────────────────
    ("daily-report.equipment", "next"): {
        "title_es": "Qué lee Despacho mañana",
        "body_es":
            "Despacho saca todos los Reportes Diarios a las 5pm para "
            "armar los movimientos de mañana. Una nota aquí que diga "
            "'necesitamos el mini de regreso el martes' es lo que hace "
            "que el martes sea suave. Un Reporte Diario sin notas hace "
            "del mañana un arrebato de llamadas para todos.",
    },
    ("daily-report.equipment", "escalate"): {
        "title_es": "Cuándo la unidad está fallando o va a fallar",
        "body_es":
            "Si una unidad se rompió hoy, o vio algo hoy que dice que SE "
            "VA a romper mañana, dígalo aquí Y avise a Taller "
            "directamente. El Reporte Diario alerta a todos pasivamente; "
            "un aviso verbal a Taller pone a un mecánico en marcha antes "
            "del amanecer.",
    },

    # ── iter215 · Material Calculator ────────────────────────────────
    ("material-calculator", "why"): {
        "title_es": "Por qué importa este cálculo",
        "body_es":
            "Este número guía la orden. Pida corto y la cuadrilla se "
            "detiene a las 2pm esperando una segunda entrega; pida de "
            "más y el sobrante se le carga al trabajo por yardas que "
            "nadie colocó. Los cinco minutos aquí ahorran un día de "
            "carreras.",
    },
    ("material-calculator", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Tratar el número del calculador como final — es una "
            "estimación de planeación, no una medición. Poner el "
            "desperdicio en 0% porque 'esta cuadrilla es limpia'. "
            "Olvidar que el calculador no sabe que su subbase está "
            "blanda, que su zanja se ensanchó, o que el proveedor solo "
            "vende tarima completa.",
    },
    ("material-calculator", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "'Plataforma 24×40, 6\" de roca caliza, densidad 1.45, 10% "
            "de desperdicio → 14.5 toneladas → ordene 15 toneladas' es "
            "un número real. Después verifique contra el mínimo de "
            "tarima/camión del proveedor y la medición de campo del "
            "capataz antes de firmar la PO.",
    },

    ("material-calculator.waste", "why"): {
        "title_es": "Por qué el factor de desperdicio no es opcional",
        "body_es":
            "Pérdida por corte, derrame, orilla, asentamiento por "
            "compactación, y faltantes del proveedor son reales en cada "
            "trabajo. Un estimado de 0% de desperdicio es un 0% honesto. "
            "Use el histórico del trabajo — si el último trimestre fue "
            "12%, planee 12%, no 5%.",
    },
    ("material-calculator.waste", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Escoger un porcentaje de desperdicio que 'se siente bien' "
            "en vez de usar el histórico del tipo de trabajo. Subirlo "
            "para acolchonar la orden (ahora PM cree que el proyecto "
            "está sangrando margen). Bajarlo para ganar la propuesta "
            "(ahora el capataz está corto el martes).",
    },

    ("material-calculator.lead-time", "why"): {
        "title_es": "Por qué el tiempo de entrega es parte del cálculo",
        "body_es":
            "El calculador resuelve cantidad. El tiempo de entrega "
            "resuelve CUÁNDO. Un número perfecto de 14.5 toneladas no "
            "vale nada si lo ordena viernes en la tarde para una colada "
            "del lunes y la planta del proveedor está cerrada el "
            "domingo. Revise el calendario del proveedor antes de "
            "comprometer una fecha.",
    },
    ("material-calculator.lead-time", "escalate"): {
        "title_es": "Cuándo llamar al proveedor primero",
        "body_es":
            "Mezclas especiales, cargas de sobretamaño, cualquier cosa "
            "que venga de fuera de la planta regional, y cualquier orden "
            "puesta dentro de 24h de la necesidad. Llame antes de "
            "comprometer una fecha de entrega en un Reporte Diario o "
            "schedule. El 'sí' del proveedor por teléfono le gana a la "
            "confianza del calculador todas las veces.",
    },

    ("material-calculator.field-verify", "why"): {
        "title_es": "Por qué ningún calculador reemplaza una medición de campo",
        "body_es":
            "El plano decía que la zanja es de 80 pies a 24 pulgadas. "
            "El campo encontró roca a los 50 pies y la zanja se ensanchó "
            "a 36 para librarla. El calculador no puede saber eso. "
            "Camine el trabajo, mida lo que de verdad está ahí, y "
            "después calcule — no al revés.",
    },
    ("material-calculator.field-verify", "next"): {
        "title_es": "Qué hacer con el número calculado",
        "body_es":
            "Contrástelo con la intuición del capataz. Confirme que el "
            "proveedor lo puede entregar a tiempo. Después el día del "
            "Reporte Diario, registre lo que SE COLOCÓ (no lo que se "
            "ordenó). El calculador es para planear; el Reporte Diario "
            "es para la verdad.",
    },

    # ── iter216 · Dispatch Transfers (Tier 2) ────────────────────────
    ("dispatch.transfers", "why"): {
        "title_es": "Por qué las transferencias son el apalancamiento del despachador",
        "body_es":
            "Cada transferencia o le ahorra un día al trabajo o le "
            "cuesta uno. Un movimiento bien ruteado convierte un camión "
            "en tres paradas productivas; un movimiento apurado "
            "desperdicia el camión y frustra a dos capataces. Despacho "
            "es el árbitro operacional — proteja el schedule, el "
            "equipo, y el día de la cuadrilla.",
    },
    ("dispatch.transfers", "who"): {
        "title_es": "Quién se ve afectado por este movimiento",
        "body_es":
            "El capataz que envía (perdió la unidad), el capataz que "
            "recibe (la consiguió — o no, a tiempo), el operador (ruta "
            "y carga), Taller (cualquier defecto en camino), PM (código "
            "de costo), y Seguridad (cualquier movimiento que toque "
            "DOT). Una tarjeta de transferencia aterriza en el radar de "
            "seis personas.",
    },
    ("dispatch.transfers", "next"): {
        "title_es": "Qué pasa después de que la pone en cola",
        "body_es":
            "El capataz que recibe ve la disponibilidad de mañana. El "
            "operador recibe la hoja de carga. Taller ve la última "
            "ubicación conocida de la unidad para partes/PM. Si el "
            "movimiento se atrasa, todos los que dependen necesitan "
            "saberlo en la hora — no al inicio del turno del día "
            "siguiente.",
    },
    ("dispatch.transfers", "escalate"): {
        "title_es": "Cuándo la solicitud no cuadra",
        "body_es":
            "El capataz pide una unidad que usted no tiene. El "
            "movimiento requiere un permiso, escolta, o ventana fuera "
            "de horario. Le piden a una unidad que deje un trabajo que "
            "sigue activo según el Reporte Diario. No diga simplemente "
            "'no' — llame al capataz que pidió Y al PM, hablen, y "
            "documente la decisión.",
    },

    ("dispatch.transfers.lead-time", "why"): {
        "title_es": "Por qué el tiempo de aviso es todo el juego",
        "body_es":
            "24 horas de aviso = puede rutear eficiente y evitar millas "
            "muertas. 4 horas de aviso = un camión apurado y un "
            "operador frustrado. 30 minutos de aviso = se quema el día "
            "de alguien. Enseñe a los capataces a pensar un día de "
            "trabajo adelante, no un descanso adelante.",
    },
    ("dispatch.transfers.lead-time", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Aceptar 'lo necesito ya' como el tiempo de respuesta por "
            "default. No preguntar al que pide CUÁNDO de verdad lo "
            "necesita — la mayoría de los 'ya' tienen un deadline real "
            "de 4-6 horas. Cotizar un tiempo aspiracional que no puede "
            "cumplir. Mejor comprometer tarde y entregar temprano que "
            "al revés.",
    },

    ("dispatch.transfers.access", "why"): {
        "title_es": "Por qué los detalles de acceso al sitio importan",
        "body_es":
            "Un operador que llega a una reja sin código, un lote "
            "blando que no aguanta un lowboy, o un techo bajo que el "
            "camión no pasa — esos no son errores del operador, son "
            "fallas de información de Despacho. Pídale al capataz los "
            "detalles de acceso antes de comprometer el horario de "
            "entrega.",
    },
    ("dispatch.transfers.access", "example"): {
        "title_es": "Ejemplo",
        "body_es":
            "Nota de acceso buena: 'Sitio en 1450 Industrial Pkwy, "
            "código de reja 8842, capataz Díaz al 555-0117, lote de "
            "grava al este del tráiler, 11'6\" techo bajo en la reja "
            "(nada de cubiertas altas).' Mala: 'Industrial Parkway, "
            "pregunte por Díaz.' — la segunda genera la llamada.",
    },

    ("dispatch.transfers.load-specs", "why"): {
        "title_es": "Por qué las especificaciones de carga nos protegen a todos",
        "body_es":
            "Peso, altura, largo, accesorios montados/desmontados, "
            "fluidos llenos o vaciados — esos deciden qué tráiler va, "
            "si se necesita permiso, y si el DOT puede ser problema. "
            "El operador y el capataz los necesitan correctos a la "
            "primera.",
    },
    ("dispatch.transfers.load-specs", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Confiar en las hojas de especificación del equipment-"
            "master sin verificar con el capataz que envía ('le "
            "dejamos el bote'). Saltarse las notas de fluidos/"
            "combustible (un tanque lleno puede ser la diferencia "
            "entre legal y sobrepeso). Olvidar los accesorios — van "
            "separados si no se cuentan.",
    },

    ("dispatch.transfers.utilization", "why"): {
        "title_es": "Por qué la utilización es el marcador del juego largo",
        "body_es":
            "Cada unidad parada en un patio es dinero quieto. Cada "
            "unidad doble-asignada es un pleito. La utilización no es "
            "un reporte administrativo que lee una vez al mes — es el "
            "marcador diario por el que está jugando. Una buena "
            "transferencia empuja la utilización para arriba; una "
            "apurada la empuja para abajo.",
    },
    ("dispatch.transfers.utilization", "next"): {
        "title_es": "Qué le dice el tablero de utilización",
        "body_es":
            "Una unidad parada en un patio mientras otro trabajo pide "
            "el mismo modelo es una oportunidad de ruteo. Múltiples "
            "intercambios de la misma unidad entre dos trabajos en una "
            "semana dice que los proyectos no se planearon juntos. "
            "Lleve ambos a PM — prefieren oírlo de Despacho que de "
            "finanzas.",
    },

    # ── iter218 · field-leadership.records (reviewer-side) ───────────
    ("field-leadership.records", "why"): {
        "title_es": "Por qué revisar los registros, no solo archivarlos",
        "body_es":
            "Un reporte diario que solo le da una hojeada es un reporte "
            "que nadie leyó. La cuadrilla nota cuáles supers de verdad "
            "leen lo que se entrega — lo oyen la siguiente mañana "
            "cuando usted les pregunta sobre la nota específica que "
            "importó. Revisar no es auditar; es la lectura del "
            "supervisor del trabajo de su cuadrilla.",
    },
    ("field-leadership.records", "who"): {
        "title_es": "Quién más lee este mismo registro",
        "body_es":
            "PM (margen de proyecto), RH (cualquier nota de personal), "
            "Seguridad (cualquier referencia a incidente), Despacho "
            "(notas de equipo), y los dueños (el resumen semanal). "
            "Cuando rechaza una entrada vaga, no está siendo "
            "exigente — está protegiendo a los cinco lectores que "
            "vienen después.",
    },
    ("field-leadership.records", "next"): {
        "title_es": "Qué hacer cuando algo no cuadra",
        "body_es":
            "Abra el registro. Lea la narrativa del capataz. Si las "
            "cuentas entre horas de cuadrilla, horas de equipo, y "
            "notas de material no cuentan una historia coherente del "
            "día — esa es una conversación con el capataz, no una "
            "edición silenciosa. Mismo principio que Verificación de "
            "Tiempo: arregle en la fuente.",
    },
    ("field-leadership.records", "escalate"): {
        "title_es": "Cuándo empujar de regreso, cuándo escalar",
        "body_es":
            "Un patrón en varios registros del mismo capataz — entradas "
            "vagas, sin notas de despacho, equipo fantasma — es una "
            "conversación de coaching con RH, no un arreglo de un solo "
            "registro. Una referencia de seguridad enterrada en un "
            "Reporte Diario en vez de un Incidente es una llamada "
            "inmediata a Seguridad. No se quede con ninguno.",
    },
    ("field-leadership.records.review-tone", "why"): {
        "title_es": "Por qué importa CÓMO se empuja de regreso",
        "body_es":
            "El primer capataz al que le 'corrigieron' su reporte "
            "diario sin una llamada es el mismo capataz que deja de "
            "escribir notas detalladas al mes siguiente. Los "
            "revisores protegen la cultura del reporte llamando, no "
            "editando. Una llamada de 30 segundos compra seis meses "
            "de reportes honestos.",
    },
    ("field-leadership.records.review-tone", "mistake"): {
        "title_es": "Errores comunes del revisor",
        "body_es":
            "Corregir silenciosamente la narrativa del capataz porque "
            "'es más fácil'. Preguntar '¿por qué no escribió XYZ?' "
            "en vez de 'cuénteme de la mañana para que arregle el "
            "reporte'. Tratar el registro como LA verdad en vez de "
            "como el RELATO del capataz de la verdad.",
    },

    # ── iter218 · crew_eval (migrated from legacy WhyItMattersPanel) ─
    ("crew_eval", "why"): {
        "title_es": "Por qué importa esta evaluación",
        "body_es":
            "Una evaluación de cuadrilla honesta es el único momento "
            "formal en que los últimos 6 meses de un operador quedan "
            "en el registro. Las evaluaciones vagas hacen que después "
            "los aumentos, ascensos, y (raramente) la disciplina sean "
            "indefendibles. El super que escribe evaluaciones en las "
            "que la cuadrilla puede confiar es el super al que la "
            "cuadrilla de verdad escucha.",
    },
    ("crew_eval", "who"): {
        "title_es": "Quién lo lee 6 meses después",
        "body_es":
            "RH (ascensos, aumentos), el siguiente super que herede al "
            "operador, PM (decisiones de staffing de proyecto), y el "
            "operador mismo (cuando pregunte por qué no recibió el "
            "aumento). Escríbalo de modo que la respuesta esté en el "
            "archivo, no en su memoria.",
    },
    ("crew_eval", "next"): {
        "title_es": "Qué pasa después de enviarlo",
        "body_es":
            "RH lo archiva. El operador recibe una copia. Se une al "
            "expediente del operador junto a las evaluaciones previas — "
            "los patrones se vuelven visibles con el tiempo. Si esta "
            "es la tercera 'cumple expectativas' consecutiva de "
            "alguien que ha estado considerando para capataz, el "
            "expediente dice que en realidad no lo ha movido.",
    },
    ("crew_eval", "escalate"): {
        "title_es": "Cuándo escribir menos, hablar más",
        "body_es":
            "Si la evaluación honesta sería 'necesitamos separarnos', "
            "no escriba nada aquí todavía — llame a RH. Lo mismo para "
            "cualquier patrón de acoso o seguridad. La evaluación es "
            "para el operador en estado estable de su cuadrilla, no "
            "para la conversación que está a punto de cambiar el "
            "empleo de alguien.",
    },
    ("crew_eval.calibration", "why"): {
        "title_es": "Por qué la calibración le gana a las calificaciones",
        "body_es":
            "Si cada operador de su cuadrilla es un 4 de 5, la "
            "evaluación no le dice nada a RH. Calibrar es preguntar: "
            "comparado con el operador promedio en trabajo similar, "
            "¿dónde cae esta persona? Abajo, igual, o arriba. Esa es "
            "la pregunta real de la evaluación.",
    },
    ("crew_eval.calibration", "mistake"): {
        "title_es": "Errores comunes de calibración",
        "body_es":
            "Calificar a todos igual para evitar conflicto. Dejar que "
            "un buen día infle los 6 meses completos. Dejar que un "
            "mal día los hunda. Comparar a su operador de banca-B "
            "con su líder de banca-A en vez de con el promedio. "
            "Califique contra el promedio real, no contra su favorito "
            "ni contra su frustración.",
    },
    ("crew_eval.evidence", "why"): {
        "title_es": "Por qué los ejemplos específicos le ganan a las generalidades",
        "body_es":
            "'Buena actitud' es un sentimiento. 'Se quedó tarde tres "
            "viernes en mayo para ayudar a terminar la plataforma "
            "McCray' es evidencia. El operador puede pelear con un "
            "sentimiento; no puede pelear con un día específico. Y "
            "RH puede actuar con evidencia; no puede actuar con "
            "buena vibra.",
    },
    ("crew_eval.evidence", "example"): {
        "title_es": "Ejemplo de evidencia",
        "body_es":
            "Bueno: 'Detectó una fuga hidráulica en la Unidad 217 "
            "durante el pre-op 2026-03-14 — avisó al Taller antes "
            "del amanecer, previno una línea reventada en la colada "
            "de McCray.' Malo: 'Le pone atención a su equipo.' Lo "
            "primero es la evaluación; lo segundo es el papel tapiz.",
    },

    # ── iter218 · dispatch.idle-alerts ───────────────────────────────
    ("dispatch.idle-alerts", "why"): {
        "title_es": "Por qué las alertas de inactividad son oportunidad, no culpa",
        "body_es":
            "Una alerta de inactividad no es 'este capataz está "
            "desperdiciando equipo'. Es 'esta unidad no ha generado "
            "un evento operacional en N días — ¿es a propósito o se "
            "le olvidó a todos?'. Trátelo como descubrimiento, no "
            "como trampa — la mayoría de las unidades inactivas "
            "tienen una historia; la alerta solo le hace preguntar.",
    },
    ("dispatch.idle-alerts", "who"): {
        "title_es": "A quién llama antes de mover",
        "body_es":
            "Al capataz asignado primero — él sabe si la unidad está "
            "lista para la colada de la próxima semana, descompuesta "
            "esperando una parte, o genuinamente olvidada. Después al "
            "PM si la respuesta es 'todavía la necesitamos' para "
            "revisar la utilización a nivel proyecto. Nunca "
            "auto-retire.",
    },
    ("dispatch.idle-alerts", "next"): {
        "title_es": "Qué convierte una alerta en un movimiento",
        "body_es":
            "El capataz confirma que la unidad está genuinamente "
            "disponible. Otro trabajo tiene una necesidad confirmada "
            "del mismo modelo. El tiempo de aviso alcanza para la "
            "transferencia. El PM se entera antes del movimiento, no "
            "después. Si falta cualquiera de los cuatro, la alerta es "
            "información — aún no es una acción.",
    },
    ("dispatch.idle-alerts", "escalate"): {
        "title_es": "Cuándo el patrón es la historia",
        "body_es":
            "Una unidad inactiva en un trabajo es normal. El equipo "
            "entero de un trabajo tendiendo a inactividad por tres "
            "semanas es una conversación de estatus de proyecto con "
            "el PM — el trabajo puede estar cerrando, parado, o "
            "perdiendo alcance calladamente. Llévelo al PM como una "
            "pregunta, no como una queja.",
    },
    ("dispatch.idle-alerts.thresholds", "why"): {
        "title_es": "Por qué 7 / 14 / 30 días, no un solo número",
        "body_es":
            "7 días atrapa el olvido reciente genuino. 14 días atrapa "
            "el patrón de unidad-lista-para-la-próxima-semana. 30 "
            "días atrapa el ciclo de equipo de temporada-sí, "
            "temporada-no. Un solo umbral lo inundaría de falsas "
            "alertas o le escondería las reales.",
    },
    ("dispatch.idle-alerts.thresholds", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Subir el umbral a 30 porque es más tranquilo — ahora "
            "pierde la inactividad de 10 días que otro capataz está "
            "pidiendo activamente. Tratar el conteo de 7 días como "
            "'unidades a retirar' en vez de 'unidades a preguntar'. "
            "El umbral es un iniciador de conversación, no un "
            "veredicto.",
    },

    # ── iter218 · dispatch.holds ─────────────────────────────────────
    ("dispatch.holds", "why"): {
        "title_es": "Por qué existen los retenes (y por qué Despacho no los libera)",
        "body_es":
            "Un retén significa que Seguridad o Taller decidió que "
            "esta unidad no está apta para campo ahora mismo. El "
            "trabajo de Despacho es VER el retén y rutear alrededor — "
            "no cuestionar la decisión. Si el retén parece equivocado, "
            "la conversación es con el equipo que lo puso, no un "
            "rodeo.",
    },
    ("dispatch.holds", "who"): {
        "title_es": "Quién puso qué tipo de retén",
        "body_es":
            "Retenes de Seguridad = Seguridad lo puso (usualmente "
            "post-incidente o hallazgo de auditoría). Retenes de "
            "Mantenimiento = Taller lo puso (usualmente un PM "
            "fallido, parte rota, o defecto reportado por el "
            "operador). Retenes pendientes = alguien solicitó uno y "
            "necesita aprobación. Despacho lee los tres; libera "
            "ninguno.",
    },
    ("dispatch.holds", "next"): {
        "title_es": "Qué hace Despacho mientras una unidad está retenida",
        "body_es":
            "No ponga la unidad en cola para ninguna transferencia. "
            "Dígale al capataz que pide que la unidad no está "
            "disponible Y la clase de razón (Seguridad / "
            "Mantenimiento) — necesita saber a qué equipo perseguir "
            "si cree que el retén está mal. Vigile la cola para el "
            "evento de liberación; ahí es cuando reanuda el ruteo.",
    },
    ("dispatch.holds", "escalate"): {
        "title_es": "Cuándo surface un patrón de retenes",
        "body_es":
            "La misma unidad retenida tres veces en un trimestre es "
            "una conversación con Taller sobre retiro. El equipo "
            "entero de un trabajo tendiendo a retenes es una "
            "conversación de camínale-el-trabajo con Seguridad. "
            "Despacho no arregla ninguno — Despacho es el equipo "
            "que NOTA primero porque la cola de ruteo muestra el "
            "patrón.",
    },
    ("dispatch.holds.pending", "why"): {
        "title_es": "Por qué los retenes pendientes necesitan revisión rápida",
        "body_es":
            "Un retén pendiente es una solicitud que no se ha "
            "aprobado todavía — la unidad todavía es ruteable, pero "
            "alguien del equipo cree que no debería serlo. Si lo "
            "deja mucho, la unidad sale por la reja a la mañana "
            "siguiente antes de que aterrice la aprobación. Trabajo "
            "de Despacho: ponerle ojos a pendiente el mismo día.",
    },
    ("dispatch.holds.pending", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Descartar un retén pendiente sin leer el contexto de la "
            "solicitud. Aprobar sin preguntarle al solicitante si "
            "debe ser clase-Seguridad o clase-Mantenimiento — esas "
            "se enrutan a distintas autoridades de liberación. "
            "Tratar pendiente como una cola de 'revisar cuando haya "
            "tiempo' en vez de una cola de acción del día.",
    },

    # ── iter222 · time-off-review (Tier-2 HR) ────────────────────────
    ("time-off-review", "why"): {
        "title_es": "Por qué importa esta revisión",
        "body_es":
            "El tiempo libre es donde aparece el carácter de la "
            "empresa. La cuadrilla mira cómo RH maneja estas "
            "solicitudes — con justicia, con humanidad, a tiempo — y "
            "decide si vale la pena trabajar aquí. La mayoría son "
            "decisiones de juicio, no de política. Lea la solicitud, "
            "haga las preguntas, luego decida.",
    },
    ("time-off-review", "who"): {
        "title_es": "A quién afecta su decisión",
        "body_es":
            "Al empleado primero (su día libre, su familia, su "
            "confianza en la empresa). A su supervisor (que tiene "
            "que cubrir el trabajo). A la cuadrilla (que ve si la "
            "decisión cuadra con las últimas 10 iguales). Al PM si "
            "afecta el staffing de proyecto. A nómina si cambia los "
            "totales de la semana.",
    },
    ("time-off-review", "next"): {
        "title_es": "Qué pasa después de que decide",
        "body_es":
            "El empleado recibe la respuesta — el mismo día si es "
            "posible. El supervisor recibe visibilidad para planear "
            "la cobertura. El tiempo aprobado entra a la cola de "
            "verificación de tiempo automáticamente. Si necesitó más "
            "información, la solicitud queda abierta con una nota "
            "explicando qué pidió y cuándo.",
    },
    ("time-off-review", "escalate"): {
        "title_es": "Cuándo llamar antes de decidir",
        "body_es":
            "Cualquier cosa que pudiera ser una pregunta de "
            "discapacidad médica, cualquier cosa que toque una clase "
            "protegida, cualquier caso donde el mismo empleado tenga "
            "3+ solicitudes abiertas este trimestre, o cualquier "
            "caso donde el supervisor empuje fuerte contra la "
            "aprobación. Llame antes de decidir — el Director de RH "
            "se entera el lunes de cualquier modo.",
    },

    ("time-off-review.bereavement", "why"): {
        "title_es": "El duelo se concede, nunca se debate",
        "body_es":
            "Alguien murió. Apruebe el tiempo. La conversación "
            "después es sobre la fecha de regreso y qué necesita "
            "cuando regrese — no sobre si 'de verdad' necesita "
            "estar fuera. El estándar de 3 días es el piso, no el "
            "techo; extiéndalo si lo piden, en el momento.",
    },
    ("time-off-review.bereavement", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Pedir certificado de defunción antes de aprobar. Llamar "
            "al supervisor 'solo para chequear' antes de conceder. "
            "Empujar de regreso sobre cuál familiar 'cuenta' — el "
            "empleado decide quién es familia. Tratar la solicitud "
            "como un rompecabezas de política en vez de una persona "
            "de duelo.",
    },
    ("time-off-review.bereavement", "escalate"): {
        "title_es": "Cuándo algo se ve raro",
        "body_es":
            "Si se forma un patrón (varias solicitudes de duelo por "
            "la misma persona · nombres claramente inventados · "
            "tiempos que cuadran con turnos esquivados conocidos), "
            "eso es una conversación con el Director de RH DESPUÉS "
            "de que el tiempo ya está aprobado. No le niega el duelo "
            "a alguien para investigarlo. Aprueba, luego habla.",
    },

    ("time-off-review.pattern", "why"): {
        "title_es": "Un patrón es una conversación, no una negativa",
        "body_es":
            "Un día de enfermedad es un día de enfermedad. Tres "
            "lunes seguidos es un patrón. El patrón no cambia si "
            "se aprueba la solicitud actual — cambia si la "
            "conversación que debería estar pasando, está pasando. "
            "Negar la solicitud para 'mandar un mensaje' solo le "
            "enseña a la cuadrilla que RH juega juegos.",
    },
    ("time-off-review.pattern", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Negar la solicitud como sustituto de la conversación "
            "que no quiere tener. Aprobar por trigésima vez sin "
            "nunca avisarle al supervisor del patrón. Dejar que el "
            "patrón se vuelva 'reputación' antes de que alguien le "
            "haya dicho las palabras al empleado.",
    },
    ("time-off-review.pattern", "next"): {
        "title_es": "Cómo se ve la conversación correcta",
        "body_es":
            "Apruebe la solicitud actual. Después, por separado, "
            "usted o el supervisor se sienta con el empleado y le "
            "dice lo observado — fechas específicas, sin "
            "editorializar. Pregunte si está pasando algo. "
            "Escúchelo. La mayoría de los 'patrones' tienen una "
            "historia real atrás; algunos no. La conversación "
            "averigua.",
    },

    ("time-off-review.vacation", "why"): {
        "title_es": "Las vacaciones son un sí con tiempo",
        "body_es":
            "Las vacaciones planeadas no son un privilegio que RH "
            "concede — son tiempo ganado del empleado. La pregunta "
            "rara vez es 'sí o no' — es 'esta semana o esa semana'. "
            "Revise el calendario del proyecto, hable con el "
            "supervisor sobre cobertura, y confirme una ventana que "
            "funcione. Decir 'no' de plano casi siempre es la "
            "respuesta equivocada.",
    },
    ("time-off-review.vacation", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Decir 'no' en vez de 'esa semana no'. No revisar el "
            "calendario del proyecto antes de decidir. Aprobar sin "
            "avisarle al supervisor — la cobertura se descubre la "
            "mañana del primer día, no la semana antes. Dejar "
            "solicitudes pendientes 5 días mientras el empleado se "
            "pregunta si cuenta como 'no'.",
    },

    ("time-off-review.medical", "why"): {
        "title_es": "Permiso médico: planee alrededor, no escarbe en él",
        "body_es":
            "Cirugía, citas, recuperación — el empleado le dice "
            "cuándo, usted planea alrededor. El diagnóstico no es "
            "asunto suyo a menos que el empleado decida compartirlo. "
            "Coordine el calendario, confirme la cobertura, y "
            "respete la privacidad. '¿Qué tiene?' no es una "
            "pregunta que RH haga aquí.",
    },
    ("time-off-review.medical", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Preguntar para qué es la cita. Empujar de regreso "
            "sobre los tiempos porque 'tenemos una semana ocupada' — "
            "ellos no programaron la cirugía alrededor de su "
            "calendario de coladas. Decirle al supervisor cuál es "
            "el asunto médico. Tratar una nota médica como un "
            "permiso que usted puede evaluar.",
    },

    # ── iter223 · employee-accountability (Tier-2 HR) ────────────────
    ("employee-accountability", "why"): {
        "title_es": "Por qué importa esta conversación",
        "body_es":
            "Cuando un empleado pregunta sobre su pago, su talón, o "
            "un bono que falta, no está buscando pelea — le está "
            "extendiendo confianza a RH para que arregle las cosas. "
            "Cómo responda en los próximos 90 segundos decide si "
            "se va del mostrador creyendo que la empresa lo "
            "respalda, o creyendo que está por su cuenta.",
    },
    ("employee-accountability", "who"): {
        "title_es": "Quién está escuchando su respuesta",
        "body_es":
            "El empleado enfrente de usted. Los dos compañeros en "
            "la sala de descanso que se enterarán en una hora. El "
            "supervisor (si resulta ser un arreglo de Reporte "
            "Diario). Nómina (si es un problema del sistema). La "
            "cuadrilla — porque las historias de justicia viajan "
            "más rápido que cualquier comunicación corporativa.",
    },
    ("employee-accountability", "next"): {
        "title_es": "Qué pasa después de que leyó el registro",
        "body_es":
            "Dígale al empleado lo que encontró en palabras "
            "claras. Si tiene razón, arréglelo hoy y dígale cuándo "
            "llega el cheque corregido. Si no tiene razón, "
            "explíquele los números para que entienda. Si necesita "
            "más tiempo, dele una hora específica para devolverle "
            "la llamada — y cúmplala.",
    },
    ("employee-accountability", "escalate"): {
        "title_es": "Cuándo llamar al Director de RH antes de responder",
        "body_es":
            "Cualquier cosa que suene a queja más allá del pago "
            "(acoso, discriminación, represalia). Cualquier caso "
            "donde varios empleados estén haciendo la misma "
            "pregunta esta semana (problema del sistema, no del "
            "empleado). Cualquier caso donde ya se sienta usted "
            "poniéndose a la defensiva — ese es el momento de "
            "pausar y llamar arriba.",
    },

    ("employee-accountability.read-first", "why"): {
        "title_es": "La respuesta vive en el registro — lea primero, responda después",
        "body_es":
            "Resista el reflejo de responder de memoria o de lo "
            "que se siente correcto. Abra el registro de "
            "verificación de tiempo. Abra el Reporte Diario. Abra "
            "el talón anterior. La respuesta está en esos "
            "documentos. Leer primero le cuesta 60 segundos y le "
            "compra una respuesta que el empleado de verdad puede "
            "verificar.",
    },
    ("employee-accountability.read-first", "mistake"): {
        "title_es": "Errores comunes",
        "body_es":
            "Responder 'eso no puede estar bien' antes de abrir "
            "nada. Citar números de política en vez de mostrar el "
            "registro real. Decir 'lo voy a revisar' y luego "
            "olvidarse por dos días. Mirar la pantalla pero no "
            "leer en serio lo que dice.",
    },
    ("employee-accountability.read-first", "example"): {
        "title_es": "Cómo se ve 'leer primero'",
        "body_es":
            "Empleado: 'Mi cheque está corto como $80.' Usted: "
            "'Déjeme sacar su semana pasada — un minuto.' [Abre "
            "Reportes Diarios, verificación de tiempo, talón.] "
            "Usted: 'Registró 42.5 horas, le pagaron 40 — parece "
            "que 2.5 de OT no entró. Veo qué pasó. Lo arreglo y "
            "tiene la corrección el viernes.' Esa es toda la "
            "interacción.",
    },

    ("employee-accountability.tone", "why"): {
        "title_es": "Por qué la respuesta calmada gana",
        "body_es":
            "El empleado vino con usted porque confió en RH antes "
            "que en el supervisor, los rumores, o irse frustrado a "
            "casa. La actitud defensiva termina esa confianza. "
            "Calmado, específico, basado en evidencia — ese es el "
            "tono que deja que la conversación resuelva algo. La "
            "frustración rara vez es contra usted; no se la tome.",
    },
    ("employee-accountability.tone", "mistake"): {
        "title_es": "Errores comunes de actitud defensiva",
        "body_es":
            "Empatar la frustración del empleado con la suya. "
            "Decir 'así no funciona' antes de escuchar. Alcanzar "
            "el manual antes de alcanzar el registro real. Tratar "
            "la pregunta como una acusación. Leer 'creo que hay "
            "un error' como 'creo que usted cometió un error' — "
            "no son la misma frase.",
    },

    ("employee-accountability.verify", "why"): {
        "title_es": "Verificar sin que se sienta como interrogatorio",
        "body_es":
            "Necesita hechos para responder: qué semana, qué "
            "trabajo, qué horas. El empleado necesita sentir que "
            "está investigando CON él, no investigándolo. Haga "
            "preguntas abiertas ('cuénteme de esa semana') en vez "
            "de cerradas ('¿tiene prueba de esas horas?'). La "
            "misma recolección de hechos, la mitad de fricción.",
    },
    ("employee-accountability.verify", "next"): {
        "title_es": "Cómo se ve una 'buena verificación'",
        "body_es":
            "Una nota corta en el registro: 'El empleado preguntó "
            "por faltante en el periodo de pago 2026-05-12, "
            "reclamó 42.5 hrs. Contrastado contra Reportes Diarios "
            "+ verificación: 42.5 confirmado. Corrección emitida "
            "2026-05-19, empleado notificado verbalmente.' "
            "Cualquiera que lea esa nota tres meses después "
            "entiende exactamente qué pasó y por qué.",
    },

    ("employee-accountability.followup", "why"): {
        "title_es": "Por qué cerrar el ciclo importa más que la solución",
        "body_es":
            "Una corrección de la que el empleado nunca se entera "
            "es lo mismo que ninguna corrección. Después de que "
            "corra nómina, mande una confirmación rápida — 'su "
            "cheque debería reflejar el arreglo el viernes, "
            "avíseme si no' — y signifique las últimas cinco "
            "palabras. El seguimiento es la parte que la "
            "cuadrilla recuerda, no la conversación original.",
    },

    # ── iter224 · employee-lifecycle (Tier-2 HR onboarding) ──────────
    # Operator-stated anchor (verbatim · test-enforced):
    #   "Get it right and they hear about the company; get it wrong
    #    and they hear about the bureaucracy."
    ("employee-lifecycle", "why"): {
        "title_es": "Por qué el primer día importa más que el papeleo",
        "body_es":
            "Dentro de años, el empleado no se acordará de qué "
            "formulario firmó primero. Se acordará de si el lugar "
            "se sintió organizado, acogedor, y serio con su gente. "
            "La inducción no es una lista de tareas — es el primer "
            "mensaje que la empresa manda sobre cómo trata a la "
            "cuadrilla.",
    },
    ("employee-lifecycle", "who"): {
        "title_es": "Quién más hace que el Día 1 funcione",
        "body_es":
            "El supervisor que lo contrata (necesita saber que "
            "viene, con el nombre y la hora correctos). La cuadrilla "
            "donde va a entrar (un aviso vale más que una sorpresa). "
            "Nómina (datos bancarios, deducciones). Taller o "
            "Despacho si hay equipo que asignar. Los dueños no ven "
            "esto — pero se enteran si sale mal.",
    },
    ("employee-lifecycle", "next"): {
        "title_es": "Qué pasa después de terminar la inducción",
        "body_es":
            "Mándele al supervisor la confirmación de hora de "
            "entrada el mismo día. Asegúrese de que el nuevo "
            "empleado sepa dónde estacionarse, dónde encontrarlo a "
            "usted, y a quién va a buscar mañana. Agende un "
            "seguimiento a los 14 días en su calendario antes de "
            "dejarlo salir por la puerta — ahí es cuando empiezan "
            "las preguntas reales.",
    },
    ("employee-lifecycle", "escalate"): {
        "title_es": "Cuándo llamar al Director de RH antes de terminar",
        "body_es":
            "Documentos I-9 que faltan o están vencidos y no se "
            "van a resolver antes de la fecha de inicio. Banderas "
            "del background check que no eran esperadas. Descubrir "
            "que esta persona ya había trabajado aquí y se fue en "
            "condiciones que vale la pena saber. Cualquier cosa "
            "donde usted se siente incómodo pero el formulario le "
            "pide que apriete Enviar de todos modos.",
    },

    # ── iter224 · employee-lifecycle.first-impression ────────────────
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    #   "Get it right and they hear about the company; get it wrong
    #    and they hear about the bureaucracy."
    ("employee-lifecycle.first-impression", "why"): {
        "title_es": "Si lo hace bien hablan de la empresa; si lo hace mal hablan de la burocracia",
        "body_es":
            "El nuevo empleado le va a contar a alguien esta noche "
            "cómo le fue en su primer día. Va a describir un lugar "
            "que tenía las cosas en orden y lo trató como persona, "
            "o un lugar que le entregó un montón de formularios y "
            "le señaló una silla. Usted decide cuál de las dos "
            "historias se cuenta.",
    },
    ("employee-lifecycle.first-impression", "mistake"): {
        "title_es": "Errores comunes de primera impresión",
        "body_es":
            "Dejarlo esperando en recepción 20 minutos porque "
            "nadie sabía que venía. Arrancar con el I-9 en vez de "
            "con un apretón de manos y su nombre. Tratar la "
            "inducción como captura de datos. Mandarlo al campo "
            "sin avisarle al supervisor que existe.",
    },
    ("employee-lifecycle.first-impression", "example"): {
        "title_es": "Cómo se ve una buena primera impresión",
        "body_es":
            "Lo recibe en la puerta por su nombre. El café o el "
            "agua ya están afuera. La cara del supervisor está en "
            "un papelito para que sepa a quién buscar. El papeleo "
            "viene DESPUÉS de la conversación de bienvenida, no "
            "antes. Se va sabiendo dónde estacionarse mañana, qué "
            "traer, y que usted es la persona a quien llamar si "
            "algo no está claro.",
    },

    # ── iter224 · employee-lifecycle.welcome ─────────────────────────
    ("employee-lifecycle.welcome", "why"): {
        "title_es": "Por qué la bienvenida va antes que los formularios",
        "body_es":
            "Si los primeros 60 segundos de la conversación son "
            "'necesito su seguro social y una copia de su licencia,' "
            "el empleado ya sabe qué clase de lugar es este. "
            "Arranque con su nombre, de dónde es, qué turno empieza. "
            "El papeleo toma los mismos cinco minutos en el minuto "
            "uno o en el minuto diez — el minuto diez se siente "
            "mejor.",
    },
    ("employee-lifecycle.welcome", "mistake"): {
        "title_es": "Errores comunes en la bienvenida",
        "body_es":
            "Pedir documentos antes de presentarse usted mismo. "
            "Leerle la lista de políticas en vez de explicarle "
            "cómo se ve el día. Hablarle a la pantalla en vez de "
            "a él. Tratarlo como una transacción en vez del "
            "comienzo de una relación de trabajo.",
    },

    # ── iter224 · employee-lifecycle.documents ───────────────────────
    ("employee-lifecycle.documents", "why"): {
        "title_es": "Recoger documentos sin que se sienta como interrogatorio",
        "body_es":
            "Usted necesita el I-9, los datos del banco, el "
            "contacto de emergencia. Él necesita sentir que usted "
            "lo está ayudando a entrar a la empresa, no que lo "
            "está revisando en una frontera. Explique POR QUÉ se "
            "necesita cada uno en palabras simples, acepte lo que "
            "trae, y resuelva lo que falta con una cita de "
            "seguimiento — nunca con actitud.",
    },
    ("employee-lifecycle.documents", "mistake"): {
        "title_es": "Errores comunes recogiendo documentos",
        "body_es":
            "Recitar la lista sin explicar por qué se necesita "
            "cada cosa. Suspirar cuando le falta algo. Hacerle "
            "sentir que el documento que falta es culpa suya, en "
            "vez de un momento de 'no hay problema, busquemos el "
            "camino más rápido.' Tratar la lista como un examen "
            "que está pasando o reprobando.",
    },

    # ── iter224 · employee-lifecycle.day-one ─────────────────────────
    ("employee-lifecycle.day-one", "next"): {
        "title_es": "Cómo se ve un buen traspaso de Día 1",
        "body_es":
            "Confirme con el supervisor por teléfono (no solo por "
            "mensaje) que el nuevo empleado ya va en camino y a "
            "qué hora lo espera. Si puede, acompáñelo personalmente "
            "a la salida, o al menos señálele la entrada correcta. "
            "Asegúrese de que tenga su número para la inevitable "
            "llamada de 'ya estoy aquí — ¿a dónde voy?' la mañana "
            "del primer día.",
    },

    # ── iter225 · document-expirations (Tier-2 hr+safety+admin) ──────
    # Operator-stated anchor (verbatim · test-enforced):
    #   "Phone call beats email blast."
    ("document-expirations", "why"): {
        "title_es": "Por qué esta lista es de personas, no de papeleo",
        "body_es":
            "Cada renglón en esta página es la CDL de alguien, su "
            "tarjeta médica, su OSHA-10, o su certificado de "
            "primeros auxilios — lo que necesitan para seguir "
            "trabajando. Cómo la empresa los busca antes del "
            "vencimiento es cómo la empresa les dice si importan. "
            "Una llamada dice 'sabemos tu nombre.' Un correo "
            "masivo dice 'estás en una lista.'",
    },
    ("document-expirations", "who"): {
        "title_es": "Quién más depende de que esto se resuelva",
        "body_es":
            "El empleado (su cheque se para si el certificado "
            "vence). Su supervisor (que tiene que reacomodar a la "
            "cuadrilla). Despacho (si se cae una CDL, el camión no "
            "sale). Seguridad (si vence la tarjeta de OSHA, el "
            "sitio no lo puede usar). Los dueños se enteran cuando "
            "un trabajo se atrasa porque nadie renovó una tarjeta "
            "a tiempo.",
    },
    ("document-expirations", "next"): {
        "title_es": "Qué pasa después de terminar el contacto del día",
        "body_es":
            "La renovación no está terminada hasta que habló con "
            "una persona y le dijo cuándo va a ir a la clínica, al "
            "DOL, al centro de pruebas. Apunte la fecha en el "
            "registro. Marque un seguimiento para el día siguiente "
            "a su cita para confirmar la tarjeta nueva. No cierre "
            "el renglón solo porque 'mandó el recordatorio.'",
    },
    ("document-expirations", "escalate"): {
        "title_es": "Cuándo llamar arriba antes de que venza",
        "body_es":
            "Cuando el empleado no responde después de dos intentos "
            "y la fecha está adentro de 14 días. Cuando la "
            "renovación requiere dinero que el empleado no puede "
            "adelantar y la empresa no ha decidido si lo cubre. "
            "Cuando la misma persona se ha vencido tres trimestres "
            "seguidos — ese es un problema del sistema, no un "
            "problema de recordatorio.",
    },

    # ── iter225 · document-expirations.outreach (ANCHOR SURFACE) ─────
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    #   "Llamada por teléfono le gana al correo masivo." (ES anchor)
    ("document-expirations.outreach", "why"): {
        "title_es": "Llamada por teléfono le gana al correo masivo",
        "body_es":
            "Un correo masivo sobre CDLs por vencer se abre, se "
            "mira por encima, y se olvida entre otras tres "
            "notificaciones. Una llamada — aunque sea de 90 "
            "segundos — pone la renovación en su calendario. La "
            "llamada dice 'esto es entre tú y yo, y no voy a "
            "dejar que se venza.' El correo dice 'esto es un "
            "evento del sistema.' Escoja el que renueva la "
            "tarjeta.",
    },
    ("document-expirations.outreach", "mistake"): {
        "title_es": "Errores comunes al hacer el contacto",
        "body_es":
            "Mandar el mismo correo automático tres semanas "
            "seguidas y contarlo como 'estoy dando seguimiento.' "
            "Poner al supervisor en copia en vez de llamarle al "
            "empleado. Tratar la renovación como problema solo "
            "del empleado. Marcar el renglón 'notificado' cuando "
            "nadie confirmó que recibió el mensaje — mucho menos "
            "que tiene un plan.",
    },
    ("document-expirations.outreach", "example"): {
        "title_es": "Cómo suena una buena llamada de contacto",
        "body_es":
            "'Oye Mike, tu renovación de CDL es el 30 de mayo — "
            "tres semanas. ¿Ya tienes cita? … Ok, te bloqueo la "
            "mañana del 24 en tu horario para que tengas tiempo "
            "para la clínica. Tráeme la tarjeta nueva antes del "
            "31. Llámame si algo se complica en medio.' Noventa "
            "segundos. El certificado se renueva a tiempo.",
    },

    # ── iter225 · document-expirations.cdl ───────────────────────────
    ("document-expirations.cdl", "why"): {
        "title_es": "Por qué la renovación de la CDL merece su propio plan",
        "body_es":
            "Una CDL vencida no solo incomoda al chofer — para el "
            "camión. La cuadrilla entera pierde un día, despacho "
            "corre a reasignar, y el cliente se entera. Construya "
            "la secuencia de renovación de la CDL como un momento "
            "operativo de primera, no como un recordatorio en el "
            "calendario. El sustento del chofer está sentado "
            "encima de esta fecha.",
    },
    ("document-expirations.cdl", "mistake"): {
        "title_es": "Errores comunes en la renovación de la CDL",
        "body_es":
            "Esperar hasta 14 días antes para empezar la "
            "conversación — la tarjeta médica sola puede tomar más "
            "que eso para conseguir cita. No avisarle a Despacho "
            "de la renovación con tiempo, para que no los agarre "
            "por sorpresa cuando el camión no sale. Olvidar que la "
            "tarjeta médica del DOT vence aparte de la CDL en sí.",
    },

    # ── iter225 · document-expirations.triage ────────────────────────
    ("document-expirations.triage", "why"): {
        "title_es": "No todo vencimiento es problema de esta semana",
        "body_es":
            "Un certificado de primeros auxilios que vence en 90 "
            "días no es lo mismo que una tarjeta médica que vence "
            "en 8 días. Lea la lista con criterio: ¿qué persona "
            "está en un trabajo que requiere el certificado hoy? "
            "¿Quién puede seguir trabajando hasta el mes que viene "
            "sin él? ¿Qué chofer está a punto de salir con un "
            "camión donde una tarjeta vencida es un paro real? "
            "Ordene la página por qué para el trabajo primero, no "
            "por fecha.",
    },
    ("document-expirations.triage", "mistake"): {
        "title_es": "Errores comunes al priorizar",
        "body_es":
            "Tratar el filtro de 30 días como el único filtro. "
            "Perseguir un certificado de bajo impacto con la misma "
            "energía que una CDL porque las fechas se parecen. "
            "Saltarse la pestaña de Por Vencer y solo trabajar la "
            "de Vencidos — para entonces alguien ya está fuera "
            "del trabajo.",
    },

    # ── iter225 · document-expirations.cadence ───────────────────────
    ("document-expirations.cadence", "next"): {
        "title_es": "Construyendo el ritmo semanal que lo agarra a tiempo",
        "body_es":
            "Escoja un horario fijo cada semana — el lunes en la "
            "mañana le funciona a la mayoría de coordinadores de "
            "RH — y revise la lista de Por Vencer antes de "
            "cualquier otra cosa. Una llamada por teléfono a cada "
            "persona de la lista, bloque de calendario, fecha de "
            "seguimiento. Mismo horario, misma secuencia, cada "
            "semana. El ritmo es lo que evita que la lista se "
            "vuelva un incendio dos veces al año.",
    },

    # ── iter226 · dispatch.utilization ───────────────────────────────
    # Operator-stated anchor (verbatim · test-enforced):
    #   "La utilización es una herramienta de decisión, no un tablero."
    ("dispatch.utilization", "why"): {
        "title_es": "Por qué esta página es una herramienta de decisión, no un tablero",
        "body_es":
            "La utilización es una herramienta de decisión, no un "
            "tablero. Lea la página para encontrar el próximo "
            "movimiento, la próxima rotación, el próximo servicio "
            "— no para calificar operadores. Un 38% en una unidad "
            "no significa que el operador es flojo. Significa que "
            "la unidad está disponible para otro trabajo, o que va "
            "rumbo a una falla y el taller debería saberlo ya.",
    },
    ("dispatch.utilization", "who"): {
        "title_es": "Quién más lee lo que usted decide aquí",
        "body_es":
            "El foreman cuya cuadrilla pierde o gana una pieza de "
            "equipo mañana. El taller, si la rotación destapa un "
            "intervalo de servicio. El PM, cuando una unidad "
            "reubicada aparece en el código de costo de otro "
            "trabajo. No tome la decisión en silencio — la gente "
            "del otro lado se entera más rápido de lo que cree y "
            "se acuerda si usted les avisó primero.",
    },
    ("dispatch.utilization", "next"): {
        "title_es": "Qué pasa después de decidir reubicar",
        "body_es":
            "Abra una Transferencia desde esta página (no mueva "
            "la unidad por mensaje). Confirme con el foreman que "
            "recibe que la espera antes de que salga el camión. "
            "Apunte la razón operativa — 'subutilizada en Sitio "
            "23, Cuadrilla 12 necesita un respaldo' — para que "
            "el próximo despachador que lea esto en tres meses "
            "entienda por qué se movió la unidad.",
    },
    ("dispatch.utilization", "escalate"): {
        "title_es": "Cuando el número le está diciendo algo más grande",
        "body_es":
            "Una cuadrilla entera con todas sus unidades en 25% "
            "— ese es un problema de programación de trabajo, no "
            "de reubicación. Hable con el super. Una unidad "
            "siempre en 100%+ — es una falla esperando pasar. "
            "Hable con el taller. Cuando la página dice lo mismo "
            "tres semanas seguidas y usted persigue renglones "
            "sueltos, está perdiéndose el patrón.",
    },

    # ── iter226 · dispatch.utilization.scoreboard ────────────────────
    ("dispatch.utilization.scoreboard", "why"): {
        "title_es": "Por qué la utilización no es una calificación",
        "body_es":
            "Una unidad en 40% no es una unidad reprobada. Puede "
            "ser el respaldo del tamaño correcto para una "
            "cuadrilla que va adelantada, o la de repuesto que "
            "tiene en un trabajo porque la principal se descompone. "
            "Leer el número como calificación lleva a malas "
            "decisiones — saca respaldos que funcionan y deja a "
            "las cuadrillas atascadas la próxima vez que la "
            "principal se cae.",
    },
    ("dispatch.utilization.scoreboard", "mistake"): {
        "title_es": "Errores comunes de tablero",
        "body_es":
            "Llamar la atención de operadores por número de "
            "utilización enfrente de supers. Reasignar unidades "
            "basándose solo en el número sin preguntarle al "
            "foreman por qué está bajo. Tratar la pestaña de "
            "utilización como evaluación de desempeño. Repetirle "
            "el porcentaje de la semana pasada al operador de esta "
            "semana sin revisar si cambió el trabajo.",
    },

    # ── iter226 · dispatch.utilization.redeploy ──────────────────────
    ("dispatch.utilization.redeploy", "why"): {
        "title_es": "Por qué las reubicaciones aterrizan mejor cuando llama primero",
        "body_es":
            "El foreman que recibe no quiere una unidad que no "
            "pidió, y el foreman que la entrega no quiere que se "
            "la jalen a medio trabajo sin avisar. Levante el "
            "teléfono antes de abrir la Transferencia. Noventa "
            "segundos de conversación cambian una llamada de "
            "'¿por qué se llevaron mi equipo?' por una de "
            "'gracias por el respaldo.'",
    },
    ("dispatch.utilization.redeploy", "example"): {
        "title_es": "Cómo se ve una decisión de reubicación limpia",
        "body_es":
            "Ve la Unidad 247 en 32% en Sitio 14 por segunda "
            "semana. Le llama a Mike en Sitio 14: 'Oye, la mini "
            "ha estado tranquila — ¿estás bien si la muevo a la "
            "Cuadrilla 8?' Mike dice sí. Le llama al foreman de "
            "la Cuadrilla 8: 'Te llega la mini mañana.' DESPUÉS "
            "abre la Transferencia. Tres llamadas, dos minutos "
            "en total, y mañana en la mañana nadie se sorprende.",
    },

    # ── iter226 · dispatch.daily-report-read ─────────────────────────
    # Operator-stated anchor (verbatim · test-enforced):
    #   "El Reporte Diario es la inteligencia de ruta del despachador
    #    — léalo para movimiento, no para culpa."
    ("dispatch.daily-report-read", "why"): {
        "title_es": "Por qué el Reporte Diario es su inteligencia de ruta",
        "body_es":
            "El Reporte Diario es la inteligencia de ruta del "
            "despachador — léalo para movimiento, no para culpa. "
            "Las notas sobre qué equipo se usó, qué quedó parado, "
            "qué regresó dañado, qué se necesita mañana — esa es "
            "la entrada para las reubicaciones de hoy. Léalo como "
            "lo lee un despachador en la mañana, no como un "
            "auditor revisando una tarjeta de tiempo.",
    },
    ("dispatch.daily-report-read", "who"): {
        "title_es": "Quién más lee el mismo reporte distinto",
        "body_es":
            "RH lo lee por horas. El PM lo lee por códigos de "
            "costo. Seguridad lo lee por incidentes. Usted es el "
            "único leyéndolo para saber dónde acabó el equipo. "
            "Ese es el trabajo del despachador — traducir lo que "
            "escribió el foreman a 'qué muevo mañana.'",
    },
    ("dispatch.daily-report-read", "next"): {
        "title_es": "Qué pasa después de leer los reportes de hoy",
        "body_es":
            "Marque las unidades señaladas para regreso o "
            "servicio antes de salir de la página. Abra una "
            "Transferencia o una Retención para las obvias. "
            "Apunte el nombre del foreman en cualquier reporte "
            "donde las notas de equipo estaban flojas — esa es "
            "una conversación de coaching, no un regaño, para "
            "mañana.",
    },
    ("dispatch.daily-report-read", "escalate"): {
        "title_es": "Cuándo dejar de leer y llamar",
        "body_es":
            "Un reporte describiendo una unidad cayéndose duro a "
            "media jornada y el foreman todavía la tiene en el "
            "trabajo — llame al super, no al foreman. Un reporte "
            "sin la sección de equipo dos días seguidos de la "
            "misma cuadrilla — llame al foreman ya, no después "
            "del tercero. Un reporte que contradice el registro "
            "de checkout — llame a RH antes de reubicar nada de "
            "esa cuadrilla.",
    },

    # ── iter226 · dispatch.daily-report-read.routing-intel ───────────
    ("dispatch.daily-report-read.routing-intel", "why"): {
        "title_es": "Léalo para movimiento, no para culpa",
        "body_es":
            "La nota del foreman 'la mini sonó mal casi todo el "
            "día' es oro para el despachador — eso es un servicio "
            "para mañana, no una conversación de culpa hoy. La "
            "nota 'no usamos el segundo rodillo, se quedó parado' "
            "es candidato a reubicación, no a regaño. Traduzca el "
            "lenguaje operativo a decisiones de ruta. La culpa es "
            "trabajo de otro, no suyo.",
    },
    ("dispatch.daily-report-read.routing-intel", "example"): {
        "title_es": "Cómo se ve una buena lectura de inteligencia",
        "body_es":
            "Reporte Diario de Cuadrilla 12: 'Usamos las dos "
            "excavadoras, rodillo parado 60% del turno, generador "
            "se apagó dos veces.' Decisiones de ruta en 90 "
            "segundos: deje las excavadoras, marque el rodillo "
            "como candidato a reubicación (llame a Cuadrilla 8 "
            "en la mañana), abra una Retención de mantenimiento "
            "en el generador con una nota para el Taller. Un "
            "reporte, tres decisiones, nadie culpó a nadie.",
    },

    # ── iter226 · dispatch.daily-report-read.return-drift ────────────
    ("dispatch.daily-report-read.return-drift", "why"): {
        "title_es": "Cómo agarrar la deriva entre checkout y regreso",
        "body_es":
            "Una unidad está en la lista de checkout pero el "
            "Reporte Diario no la menciona tres días seguidos — "
            "esa es una renta fantasma. O regresó y nadie cerró "
            "el checkout, o está sentada en un trabajo donde el "
            "foreman no la está registrando. Cruzar las dos "
            "listas es el trabajo del despachador; nadie más lo "
            "hace.",
    },
    ("dispatch.daily-report-read.return-drift", "mistake"): {
        "title_es": "Errores comunes con rentas fantasma",
        "body_es":
            "Asumir que una unidad sigue en el campo porque el "
            "checkout lo dice. Asumir que una unidad regresó "
            "porque el foreman no la mencionó. Tratar un reporte "
            "que falta como 'nada de qué preocuparse' en vez de "
            "como un hueco de datos que merece una llamada. "
            "Dejar que la lista de checkout y la realidad del "
            "campo se separen una semana antes de cuadrarlas.",
    },

    # ── iter226 · dispatch.handoff ───────────────────────────────────
    # Operator-stated anchor (verbatim · test-enforced):
    #   "El traspaso es una conversación, no una invitación de calendario."
    ("dispatch.handoff", "why"): {
        "title_es": "Por qué el traspaso de esta noche evita el caos de mañana",
        "body_es":
            "El traspaso es una conversación, no una invitación "
            "de calendario. Si cambió el plan de mañana, el "
            "foreman se entera de usted esta noche — no del "
            "guardia de la entrada a las 06:00. Cada minuto en "
            "la llamada de confirmación de las 16:30 ahorra tres "
            "minutos de confusión en la mañana, dos camiones "
            "apuntados al patio equivocado, y un foreman que "
            "empieza el día frustrado.",
    },
    ("dispatch.handoff", "who"): {
        "title_es": "Quién depende de que salga la llamada",
        "body_es":
            "Cada foreman con una cuadrilla saliendo en la "
            "mañana. Operadores que ponen su despertador según "
            "a qué patio reportan. El Taller, si el plan de "
            "mañana incluye una ventana de servicio. El siguiente "
            "despachador de turno, que lee el plan de mañana de "
            "sus notas y hereda lo que usted dejó sin decir.",
    },
    ("dispatch.handoff", "next"): {
        "title_es": "Qué deja atrás un buen traspaso",
        "body_es":
            "El plan de mañana escrito, no solo recordado. Cada "
            "foreman afectado confirmado por voz (solo texto no "
            "cuenta como confirmado). Transferencias abiertas "
            "cerradas por el día, o anotadas con qué queda "
            "pendiente y por qué. Una nota corta para el "
            "siguiente despachador sobre cualquier cosa que no "
            "vaya a ser obvia en las pantallas.",
    },
    ("dispatch.handoff", "escalate"): {
        "title_es": "Cuando el traspaso tiene que subir, no salir",
        "body_es":
            "Una unidad caída y no regresa mañana — el super "
            "necesita saber antes que el foreman llame. Un "
            "foreman no contesta y cambió el plan de mañana — "
            "llame al super para respaldar el mensaje. Un hueco "
            "de personal que no puede arreglar solo desde la "
            "silla del despachador — esa es una llamada de las "
            "17:00 a supervisión de operaciones, no un problema "
            "para mañana en la mañana.",
    },

    # ── iter226 · dispatch.handoff.communication ─────────────────────
    ("dispatch.handoff.communication", "why"): {
        "title_es": "Por qué una llamada le gana al texto y el texto al silencio",
        "body_es":
            "Las llamadas confirman recepción; los textos se "
            "pasan de largo; los planes silenciosos se descubren "
            "a las 06:00. La llamada de 90 segundos a cada "
            "foreman es la disciplina que mantiene la mañana "
            "tranquila. Mande texto después de la llamada si "
            "necesita registro escrito — pero la conversación es "
            "donde de verdad se acuerda algo.",
    },
    ("dispatch.handoff.communication", "mistake"): {
        "title_es": "Errores comunes de comunicación",
        "body_es":
            "Mandar el plan de despacho por chat grupal y llamarle "
            "a eso el traspaso. Asumir que la invitación del "
            "calendario cuenta. Saltarse al foreman cuyo plan no "
            "cambió (igual quiere saber qué hacen los demás). "
            "Llamar a las 17:45 cuando el foreman ya va manejando "
            "a su casa — muy tarde para planear nada.",
    },
    ("dispatch.handoff.communication", "example"): {
        "title_es": "Cómo suena una llamada de traspaso de 90 segundos",
        "body_es":
            "'Oye Tony, rapidito — mañana sigues en Sitio 23 "
            "con la misma cuadrilla. Dos cambios respecto a hoy: "
            "el segundo rodillo regresa al patio en la noche "
            "para servicio, y el operador nuevo Alex te reporta "
            "a las 07:00 en vez de las 06:30. ¿Algo más que "
            "necesites de mí antes de mañana? Bien — llámame si "
            "algo se complica en la noche.' Listo.",
    },

    # ── iter226 · dispatch.handoff.changes ───────────────────────────
    ("dispatch.handoff.changes", "why"): {
        "title_es": "Por qué la llamada de cambio sale primero",
        "body_es":
            "El foreman cuyo plan se movió entre las 14:00 y las "
            "16:30 es el que más probable arranca mañana con el "
            "pie equivocado. Llámele a ESOS foreman PRIMERO en "
            "la secuencia de traspaso — no a los cuyo día no "
            "cambió. Un cambio no dicho a las 16:30 se vuelve "
            "una cuadrilla parada a las 06:30, pagada por "
            "esperar respuesta.",
    },
    ("dispatch.handoff.changes", "mistake"): {
        "title_es": "Errores comunes al comunicar cambios",
        "body_es":
            "Secuenciar el traspaso por nombre de foreman en vez "
            "de por qué cambió. Esconder el cambio dentro de un "
            "resumen largo de planes que no cambiaron. Decirle "
            "al operador pero no al foreman, o al foreman pero "
            "no al super. Mandar el cambio como 'FYI' cuando en "
            "realidad requiere una decisión en la que el foreman "
            "debería opinar.",
    },

    # ── FLEET / TRUCKING DVIR · iter251 · Phase 1-5 (ES) ─────────────
    ("fleet.dvir", "why"): {
        "title_es": "Por qué importa la DVIR",
        "body_es":
            "Una DVIR honesta es el momento en que el conductor, el "
            "Taller y Despacho miran el mismo camión. Detectado a "
            "las 6:30 a.m. es un ticket de Taller. Detectado a 80 "
            "km/h es una factura de grúa.",
    },
    ("fleet.dvir", "who"): {
        "title_es": "Quién ve lo que usted envía",
        "body_es":
            "El Taller ve cada defecto agrupado por su camión en "
            "segundos. Despacho ve el estado de la unidad (FDS / "
            "Disponible). Seguridad lee el registro de auditoría. "
            "Su nombre queda en la inspección · responsabilidad, "
            "no culpa.",
    },
    ("fleet.dvir", "mistake"): {
        "title_es": "Errores fáciles de evitar",
        "body_es":
            "Marcar N/D en elementos que el camión sí tiene. FALLA "
            "sin nota (el Taller no puede actuar sobre 'algo está "
            "mal'). Saltar el recorrido del remolque cuando lleva "
            "uno. Esperar a hacer la inspección cuando ya está en "
            "la ruta.",
    },
    ("fleet.weekly-lead", "why"): {
        "title_es": "Por qué el recorrido semanal del líder",
        "body_es":
            "Los líderes ven patrones que los conductores dejan de "
            "notar porque cambian de camión. La fuga lenta, la "
            "grieta progresiva del espejo, el sello de puerta que "
            "ha estado dejando entrar polvo por tres semanas. "
            "Problemas pequeños · antes de que sean Fuera de Servicio.",
    },
    ("fleet.weekly-lead", "when"): {
        "title_es": "Cuándo completarlo",
        "body_es":
            "Una vez por semana por cada unidad activa · "
            "idealmente un día que el camión esté en el patio. "
            "No reemplaza la DVIR diaria · la complementa.",
    },
    ("fleet.weekly-emergency", "why"): {
        "title_es": "Por qué importa el equipo de emergencia",
        "body_es":
            "El extintor que no nota faltante en el patio es el "
            "que busca a las 2 a.m. en una zona de trabajo. El "
            "equipo de emergencia faltante o vencido se clasifica "
            "automáticamente como Fuera de Servicio · esto no es "
            "papeleo, es preparación.",
    },
    ("fleet.weekly-emergency", "mistake"): {
        "title_es": "Errores fáciles de evitar",
        "body_es":
            "Marcar 'presente' sin verificar la fecha de la "
            "etiqueta del extintor. Saltar el kit de derrames en "
            "un camión que transporta equipo hidráulico. Tratar "
            "una etiqueta vencida como Monitoreo · el sistema "
            "clasifica correctamente automáticamente.",
    },
    ("fleet.repair", "why"): {
        "title_es": "Por qué registrar la reparación aquí",
        "body_es":
            "Marcar el defecto como reparado pasa la unidad a "
            "'Reparación en curso · esperando RTS'. El camión no "
            "rueda hasta que Despacho confirme el Regreso al "
            "Servicio. Su nota y marca de tiempo son el registro "
            "de auditoría que lee Seguridad.",
    },
    ("fleet.repair", "next"): {
        "title_es": "Qué pasa después de registrar una reparación",
        "body_es":
            "Despacho ve la unidad aparecer en su cola de "
            "Esperando-RTS. Cuando confirman, la unidad regresa a "
            "Disponible y el registro de auditoría queda sellado "
            "con ambos nombres — el suyo y el del despachador.",
    },
    ("fleet.rts", "why"): {
        "title_es": "Por qué esta confirmación es intencional",
        "body_es":
            "El Taller es dueño de la llave inglesa, pero Despacho "
            "es dueño de la decisión operacional de poner el "
            "camión de vuelta en rotación. La casilla intencional "
            "es el momento en el que la plataforma registra que "
            "un humano tomó una decisión · no que un botón se "
            "tocó camino a otro lugar.",
    },
    ("fleet.rts", "mistake"): {
        "title_es": "Errores fáciles de evitar",
        "body_es":
            "Confirmar RTS sin leer la nota del Taller · pierde "
            "el contexto operacional. Saltar la nota de Despacho "
            "cuando algo es inusual · el contexto breve ayuda a "
            "Seguridad después.",
    },
    ("fleet.visibility", "why"): {
        "title_es": "Cómo funciona la severidad en estas tarjetas",
        "body_es":
            "Los conductores no clasifican severidad · el sistema "
            "lo hace, desde una tabla publicada revisada contra "
            "los lineamientos de FMCSA y DOT. Fuera de Servicio "
            "significa que la unidad no rueda. Monitoreo significa "
            "que el Taller es dueño de la reparación en un ritmo "
            "planificado · la unidad puede operar con seguridad "
            "hasta entonces.",
    },
    ("fleet.visibility", "who"): {
        "title_es": "Qué ve cada ámbito aquí",
        "body_es":
            "El Taller ve la unidad agrupada con la nota del "
            "conductor, las fotos y la severidad · actúa en la "
            "reparación. Despacho ve la disponibilidad y confirma "
            "el RTS. Seguridad lee el registro de auditoría "
            "completo con la referencia regulatoria cuando aplica.",
    },
}
