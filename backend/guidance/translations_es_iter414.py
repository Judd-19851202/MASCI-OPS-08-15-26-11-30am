"""iter414 · Phase 18 · DLS operational unification — ES translations.

Spanish translations for the 7 DLS-era guidance articles introduced in
iter414 to close the Phase 18 help-search gap surfaced by the Phase 17
audit. Style discipline mirrors translations_es.py:

- Field-accurate operational Spanish (NOT robotic translation)
- Same block structure as EN
- Canonical platform terms preserved in Spanish form:
    Cisterna / Asfalto Líquido · Movimiento de equipo ·
    Conductores aprobados · Avería · Esperando en planta · Emitir trabajo
- Acronyms (DLS, QR, CDL, PM) stay English
- ENTRY POINT: imported and merged in translations_es.py at module load
"""
from __future__ import annotations

EXTRA_ES: dict[str, dict] = {
    "dls-driver-shift-start": {
        "title_es": "DLS · Inicio de Turno del Conductor (Calcomanía QR → /shift)",
        "summary_es": "Cómo un conductor inicia su turno en segundos — sin contraseña, sin app, sin enrolamiento.",
        "body_es": [
            {"type": "p", "text":
                "Cada camión lleva una calcomanía QR impresa. El conductor la escanea con la "
                "cámara del teléfono, aterriza en /shift, escoge su nombre + el camión + "
                "(opcional) tráiler y empresa, toca INICIAR TURNO, y queda operacionalmente "
                "activo. Sin contraseña, sin app, sin enrolamiento. La plataforma sigue al "
                "camión, no a la cuenta de usuario."},
            {"type": "steps", "items": [
                "El conductor abre la cámara del teléfono y escanea la calcomanía en la puerta del camión",
                "El teléfono abre /shift en el navegador — ya en el tenant correcto",
                "Escoge su nombre (o lo escribe si es subcontratista), escoge el camión, tráiler y empresa opcionales",
                "Toca INICIAR TURNO",
                "El camión aparece en el tablero de despacho · puede recibir taps de ciclo",
            ]},
            {"type": "why", "text":
                "La identidad del camión es la llave de continuidad operacional, no la cuenta "
                "de usuario. La plataforma no debe pedir autenticación corporativa a un "
                "conductor que está a punto de ponerse guantes. El QR es el puente físico "
                "entre un camión estacionado y operaciones en vivo."},
            {"type": "next", "items": [
                "Maneje la asignación — toque EN_RUTA_A_CARGA al salir",
                "Si despacho aún no ha emitido una, el camión simplemente queda listo",
                "Fin del día · toque Cerrar sesión — deja el camión limpio para el siguiente conductor",
            ]},
            {"type": "tip", "text":
                "Los administradores imprimen la calcomanía en /admin/dls/shift-qr — un "
                "tenant, una URL, un QR. Las calcomanías van en la puerta de la cabina. Una "
                "calcomanía gastada se reimprime en 30 segundos."},
        ],
    },
    "dls-assignment-issuance": {
        "title_es": "DLS · Emisión de Asignaciones (Gaveta de Emitir Trabajo)",
        "summary_es": "Cómo despacho emite un acarreo a un camión — Material · Movimiento de equipo · Cisterna · Material de excavación · Apoyo — a través de una sola gaveta calmada.",
        "body_es": [
            {"type": "p", "text":
                "Despacho abre la gaveta de Emitir Trabajo desde el portal de Comando de "
                "Despacho y la sección de Emitir Trabajo preselecciona el tipo de acarreo. "
                "La gaveta pide el camión (requerido), conductor (opcional · el inicio "
                "propio puede reclamarlo después), y 4-6 campos condicionales según el tipo "
                "de acarreo. Enviar coloca la asignación en el tablero inmediatamente."},
            {"type": "bullets", "items": [
                "Material — fuente / punto de carga · destino · material (catálogo)",
                "Movimiento de equipo — equipo · lugar de recogida · lugar de entrega",
                "Cisterna / Asfalto Líquido — fuente cisterna · planta destino · producto líquido (catálogo de 27)",
                "Material de excavación / Volteo — usa los campos de Material con valores típicos",
                "Apoyo / Varios — campos mínimos · texto libre en el espacio del material",
            ]},
            {"type": "why", "text":
                "UNA gaveta · UN Sistema de Ciclo de Despacho · cinco tipos de acarreo. Los "
                "lowboys corren en el mismo DLS que los camiones de material. Las cisternas "
                "corren en el mismo DLS que los lowboys. La plataforma es UN sistema "
                "operacional, no cinco módulos de despacho separados."},
            {"type": "next", "items": [
                "El camión aparece en el tablero como ASIGNADO",
                "Los taps del conductor mueven el estado adelante (EN_RUTA → EN_CARGA → EN_RUTA_A_DESCARGA → COMPLETO)",
                "Al COMPLETAR, se materializa un ciclo · el tile del PM se actualiza · los chips de materiales superiores se actualizan",
            ]},
            {"type": "tip", "text":
                "Cada valor escrito-una-vez como 'Agregar temporal' (empresa, material, "
                "fuente, destino) aparece en la siguiente gaveta como opción 'historial'. "
                "La memoria operacional se alimenta sola."},
        ],
    },
    "dls-haul-types": {
        "title_es": "DLS · Cinco Tipos de Acarreo (Material · Movimiento de equipo · Cisterna · Material de excavación · Apoyo)",
        "summary_es": "Cómo el DLS maneja todo tipo de trabajo de camión a través de UN solo ciclo.",
        "body_es": [
            {"type": "p", "text":
                "El despacho de MASCI maneja cinco tipos de acarreo a través del MISMO "
                "ciclo. Mismo tablero. Misma gobernanza. Misma materialización de ciclo. "
                "Sin portales separados, sin módulos separados — solo diferentes campos "
                "condicionales en la gaveta de asignaciones."},
            {"type": "bullets", "items": [
                "Material — asfalto, agregado, concreto, terracería, utilidad, apoyo de obra (catálogo de 66)",
                "Movimiento de equipo — acarreos con lowboy con recogida/entrega + registro maestro de equipo",
                "Cisterna / Asfalto Líquido — catálogo de 27 productos (ligantes · emulsiones · combustible) · 9 terminales · 9 destinos en planta",
                "Material de excavación / Volteo — material de excavación a un destino de volteo",
                "Apoyo / Varios — cualquier otro acarreo operacionalmente válido",
            ]},
            {"type": "why", "text":
                "Operaciones piensa en camiones moviendo cosas, no en módulos de software. "
                "Forzar al sistema a reflejar el lenguaje operacional (en lugar de forzar a "
                "operaciones a reflejar la taxonomía del software) es lo que hace que esta "
                "plataforma se sienta calmada en lugar de corporativa."},
            {"type": "next", "items": [
                "El tile del PM separa cargas de material y movimientos de equipo en el conteo",
                "El resumen de salud lista los 5 tipos en `haul_types_today`",
                "El trabajo futuro de continuidad de planta ya tiene `liquid_product` en el cable",
            ]},
        ],
    },
    "dls-lifecycle-states": {
        "title_es": "DLS · Estados del Ciclo y Razones de Espera",
        "summary_es": "ASIGNADO → EN_RUTA → EN_CARGA → ESPERANDO → EN_RUTA_A_DESCARGA → COMPLETO — y qué señala cada transición río abajo.",
        "body_es": [
            {"type": "p", "text":
                "Cada asignación se mueve a través de una máquina de estados canónica "
                "manejada por los taps del conductor. No hay auto-estado — los conductores "
                "son los únicos autores de cada transición. Esto preserva la honestidad "
                "operacional (la plataforma nunca inventa actividad que no pasó) y protege "
                "contra cambios de estado falsos por GPS."},
            {"type": "bullets", "items": [
                "ASIGNADO — emitido por despacho · esperando el reclamo del conductor",
                "EN_RUTA_A_CARGA — el conductor se mueve hacia la fuente",
                "EN_CARGA — el conductor llegó a la fuente",
                "ESPERANDO — el conductor tocó una razón canónica (WAIT_ON_PLANT / WAIT_ON_DUMP / BREAKDOWN / WAITING_OTHER)",
                "EN_RUTA_A_DESCARGA — el conductor cargó y va al destino",
                "EN_DESCARGA — el conductor llegó al destino",
                "COMPLETO — el conductor terminó el acarreo · ciclo materializado",
            ]},
            {"type": "why", "text":
                "Estados canónicos + razones de espera canónicas (no texto libre) mantienen "
                "los datos operacionales limpios para gobernanza, reportes de PM y revisión "
                "post-despliegue. Esperando en planta significa LO MISMO cada vez, en cada "
                "reporte, sin importar qué conductor lo tocó."},
            {"type": "next", "items": [
                "Gobernanza emite hallazgos en parado > 30 min o espera > 45 min",
                "El Taller ve AVERÍA inmediatamente vía el tile cruzado de portales",
                "El PM ve conteos de esperando_en_planta / esperando_en_descarga en el tile de actividad",
            ]},
            {"type": "warn", "text":
                "Los conductores NO usan razones de espera en texto libre. El texto libre "
                "destruye la inteligencia operacional. El selector WAITING_OTHER (diferido "
                "hasta que operaciones en vivo identifique patrones reales) será una lista "
                "canónica de sub-categorías, no una caja de notas."},
        ],
    },
    "dls-haul-activity-tile": {
        "title_es": "DLS · Tile de Actividad de Acarreos del PM (Conciencia de Producción)",
        "summary_es": "Cómo los PMs ven actividad de acarreos en vivo para sus proyectos — sin volverse despachadores.",
        "body_es": [
            {"type": "p", "text":
                "El tile de Actividad de Acarreos del PM vive en el hub del PM y se "
                "refresca cada 60 segundos. Muestra conciencia de producción — cargas "
                "completadas hoy, acarreos activos, movimientos de equipo, esperas en "
                "planta/sitio, impactos por avería — limitado a los proyectos asignados al "
                "PM. Es solo de lectura por diseño. Los PMs no pueden emitir, cancelar ni "
                "transicionar."},
            {"type": "bullets", "items": [
                "Cargas completadas hoy — separadas en cargas de material y movimientos de equipo",
                "Acarreos activos — todo lo que aún no está COMPLETO",
                "Movimientos de equipo activos — lowboys en camino hacia o desde una obra",
                "Esperando en planta / Esperando en descarga — conteos de excepciones",
                "Impactos por avería — camiones caídos en los proyectos del PM",
                "Materiales superiores — los 5 con más cargas hoy (Movimiento de equipo filtrado)",
            ]},
            {"type": "why", "text":
                "Los PMs necesitan conciencia de producción, no controles de despacho. "
                "Saber cuánto trabajo se completó hoy y qué está esperando es suficiente — "
                "el despachador sigue siendo el único decisor de cada reasignación. Esta "
                "restricción es lo que evita que operaciones acumule cinco coordinadores "
                "superpuestos."},
            {"type": "next", "items": [
                "El tile se refresca cada 60 segundos automáticamente",
                "Estado vacío explícito: 'Nada que reportar — sus obras están tranquilas ahora'",
                "Si ocurre una avería, el tile la refleja en un minuto · el Taller la ve al instante",
            ]},
        ],
    },
    "dls-operational-attention": {
        "title_es": "DLS · Atención Operacional (Qué Importa AHORA)",
        "summary_es": "La superficie del Comando de Despacho que surfacea camiones parados, esperas largas y averías — sin convertirse en un dashboard.",
        "body_es": [
            {"type": "p", "text":
                "Atención Operacional es la sección rosa-acentuada en la parte superior "
                "del portal de Comando de Despacho. Lee de /api/dispatch/governance/"
                "findings y surfacea tres familias de excepción: averías, camiones parados "
                "más de 30 minutos, y esperas extendidas. Cada tarjeta lleva texto guía "
                "orientado a la acción — no una métrica."},
            {"type": "bullets", "items": [
                "Avería — El Taller también las ve. Decida reasignar contra suspender.",
                "Parado > 30 min — el conductor no ha tocado en un rato. Llámelo.",
                "Espera extendida — cuello de botella en planta o descarga. Reasigne o absorba.",
            ]},
            {"type": "why", "text":
                "Las operaciones calmadas requieren UN solo lugar donde surfacean las "
                "excepciones. Los dashboards dividen la atención entre gráficos; Atención "
                "Operacional la concentra en 3 tarjetas con una próxima acción clara. "
                "Cuando las tarjetas están vacías, despacho puede respirar — la plataforma "
                "está señalando 'nada necesita sus ojos en este momento'."},
            {"type": "next", "items": [
                "Cada tarjeta lleva una guía de acción, no un número",
                "El estado vacío dice exactamente eso — vacío",
                "Los hallazgos se actualizan en vivo vía polling de /api/dispatch/governance/findings",
            ]},
        ],
    },
    "dls-health-summary": {
        "title_es": "DLS · Resumen de Salud Día-1 (Tranquilo · Fluyendo · Atención)",
        "summary_es": "El endpoint admin de solo lectura que da a liderazgo operacional una señal calmada de salud de plataforma.",
        "body_es": [
            {"type": "p", "text":
                "GET /api/admin/dls/health-summary es toda la historia de monitoreo de "
                "Día-1. Tres llamadas calmadas — mañana, media mañana, fin del día — "
                "responden '¿la plataforma está saludable?' Tres palabras operacionales, "
                "sin puntajes, sin gráficos."},
            {"type": "bullets", "items": [
                "tranquilo — cero asignaciones activas · cero turnos · cero excepciones",
                "fluyendo — trabajo activo presente · sin excepciones",
                "atención — avería presente · O espera más larga ≥ 45 min · O parado más viejo ≥ 60 min · O hallazgos > 0",
            ]},
            {"type": "why", "text":
                "La observabilidad mínima le gana a las suites de monitoreo para liderazgo "
                "operacional. Un solo endpoint, llamado tres veces al día, es toda la "
                "historia de salud de plataforma para Día-1. Las notas llevan hasta 3 "
                "razones operacionales pequeñas. No hay KPI, ni puntaje, ni gráfico. Solo "
                "una palabra y una razón honesta."},
            {"type": "next", "items": [
                "Pre-vuelo (30 min antes de que lleguen los conductores) — esperar status: tranquilo",
                "Media mañana (~11 AM) — esperar status: fluyendo · transitions_today > 0",
                "Fin del día — capturar completed_cycles_today · transitions_today como números de cierre",
            ]},
            {"type": "tip", "text":
                "Presente el informe Día-1 el mismo día en /app/memory/"
                "DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md. La memoria operacional se "
                "desvanece rápido — y el informe es lo que le dice a la siguiente "
                "iteración qué construir versus qué dejar tranquilo."},
        ],
    },
}
