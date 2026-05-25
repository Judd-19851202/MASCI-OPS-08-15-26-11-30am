"""guidance/translations_es_iter423.py · Phase 25 · Shop convergence ES strings.

ES mirrors for the four new walking-skeleton Shop coaching articles:
  dls-equipment-needing-attention
  dls-active-recovery-work
  dls-waiting-on-parts
  dls-returned-to-service

Doctrine: operational continuity meaning is preserved · NOT literal
robotic translation. Field-driven Spanish that mechanics in Texas and
SW operations will read calmly.
"""

EXTRA_ES = {
    # ─────────────────────────────────────────────────────────────
    # dls-equipment-needing-attention
    # ─────────────────────────────────────────────────────────────
    "dls-equipment-needing-attention": {
        "title": "Taller · Equipo que Necesita Atención",
        "summary": "Qué significa esta sección y por qué encabeza la Consola de Taller.",
        "body": [
            {"type": "p", "text":
                "'Equipo que Necesita Atención' es lo primero que ve el Taller "
                "porque responde UNA pregunta operacional: ¿qué está interrumpiendo "
                "el servicio de campo ahora mismo? Dos fuentes lo alimentan — "
                "inspecciones DVIR con FALLA recientes de los conductores, y "
                "señales de AVERÍA del ciclo de vida desde el tablero de despacho."},
            {"type": "why", "text":
                "El trabajo de campo se detiene mientras el equipo no está sano. "
                "Mostrar esas interrupciones en lenguaje operacional (no un "
                "tablero de control) ayuda al Taller a liderar con recuperación — "
                "no con reportes."},
            {"type": "next", "items": [
                "Reconozca la avería para moverla a Trabajo de Recuperación Activo",
                "Firme las fallas DVIR cuando la unidad esté de regreso al servicio",
                "Use Historial de Continuidad Operacional para ver la narrativa",
            ]},
        ],
    },
    # ─────────────────────────────────────────────────────────────
    # dls-active-recovery-work
    # ─────────────────────────────────────────────────────────────
    "dls-active-recovery-work": {
        "title": "Taller · Trabajo de Recuperación Activo",
        "summary": "Qué significan los cuatro sub-estados de recuperación y cómo los mecánicos mueven el equipo a través de ellos.",
        "body": [
            {"type": "p", "text":
                "El trabajo de recuperación activo significa que el equipo está "
                "siendo restaurado al servicio de campo. Cuatro sub-estados "
                "llevan una unidad desde la conciencia hasta la disponibilidad: "
                "Reconocido → Diagnosticando → Reparación Activa → Prueba "
                "Operacional."},
            {"type": "why", "text":
                "Cada paso es un momento operacional real. El Taller sabe dónde "
                "está cada unidad averiada. Despacho y PM ven el impacto en "
                "texto secundario calmo — nunca comportamiento de alerta."},
            {"type": "next", "items": [
                "Reconocido · el Taller ha visto la avería",
                "Diagnosticando · el mecánico está investigando",
                "Reparación Activa · piezas en mano, trabajo en progreso",
                "Prueba Operacional · verificando antes de devolver al servicio",
            ]},
            {"type": "tip", "text":
                "Si falta una pieza, transicione a Esperando Piezas en lugar de "
                "dejar la reparación detenida. Eso hace visible la interrupción "
                "operacional para PM y despacho sin confundirlos con una "
                "reparación estancada."},
        ],
    },
    # ─────────────────────────────────────────────────────────────
    # dls-waiting-on-parts
    # ─────────────────────────────────────────────────────────────
    "dls-waiting-on-parts": {
        "title": "Taller · Esperando Piezas",
        "summary": "Por qué el estado Esperando es calmo, no urgente — y qué ven las operaciones aguas abajo.",
        "body": [
            {"type": "p", "text":
                "'Esperando Piezas' pausa la recuperación operacional hasta que "
                "lleguen los componentes. Es una interrupción operacional — un "
                "momento de espera visible y calmo — no una emergencia."},
            {"type": "why", "text":
                "PM y Despacho ven la misma señal de espera. Las plantas pueden "
                "planear. Los capataces pueden rebalancear. Nadie asume que la "
                "unidad volverá hoy. La visibilidad reduce la cognición bajo "
                "presión de campo."},
            {"type": "next", "items": [
                "Anote el proveedor y la fecha estimada en la nota de recuperación",
                "Transicione de vuelta a Reparación Activa cuando lleguen las piezas",
                "Use Historial de Continuidad Operacional para mantener la narrativa",
            ]},
            {"type": "warn", "text":
                "No deje una tarjeta de Espera en silencio. Una breve nota de "
                "recuperación (ej. 'sensor ordenado, llega jueves') es la "
                "cortesía operacional que mantiene calmo lo de aguas abajo."},
        ],
    },
    # ─────────────────────────────────────────────────────────────
    # dls-returned-to-service
    # ─────────────────────────────────────────────────────────────
    "dls-returned-to-service": {
        "title": "Taller · Devuelto al Servicio",
        "summary": "Qué significa 'Devuelto al Servicio' y por qué se lee como confianza de finalización operacional.",
        "body": [
            {"type": "p", "text":
                "Devuelto al Servicio significa que el equipo está operacionalmente "
                "listo para la continuidad de campo de nuevo. La tarjeta del "
                "Taller dice 'Continuidad operacional restaurada.' — una señal "
                "pequeña y calma de confianza de que el ciclo se cerró "
                "limpiamente."},
            {"type": "why", "text":
                "El trabajo de recuperación que termina en silencio no enseña "
                "nada. Mostrar la finalización da a mecánicos, PM y despacho "
                "conciencia compartida de que la unidad está operacional — y da "
                "a la memoria operacional algo de qué aprender."},
            {"type": "next", "items": [
                "Los últimos 7 días de equipo restaurado aparecen automáticamente",
                "La transición terminal se preserva en el historial de recuperación",
                "El Historial de Continuidad Operacional registra la narrativa completa",
            ]},
        ],
    },
}
