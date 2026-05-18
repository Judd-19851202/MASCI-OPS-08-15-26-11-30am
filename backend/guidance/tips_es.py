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
}
