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
}
