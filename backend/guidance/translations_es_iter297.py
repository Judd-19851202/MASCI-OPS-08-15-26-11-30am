"""
iter297 · Operational `why-*` knowledge articles · ES translation pass.

ES translations for the 7 `why-*` knowledge articles previously classified
as "explicit-leave" terse stubs in iter277, now re-classified per operator
direction (iter296+iter297 bundle) as operational-philosophy surfaces that
Spanish-speaking crews will reach via search.

Style discipline:
  - Calm, operational, practical tone — NOT corporate / NOT LMS / NOT
    machine-translated boilerplate.
  - Block structure mirrors the EN article exactly (same types, same
    item counts).
  - Canonical platform terminology only: Reporte Diario · Incidente ·
    Acción Correctiva · Tiempo Verificado · Registro de Auditoría.
  - No new content added in the ES side — same operational anchor,
    same length envelope, different language.
"""

EXTRA_ES: dict[str, dict] = {
    "why-daily-reports": {
        "title_es": "Por Qué Importan los Reportes Diarios",
        "summary_es": "La columna vertebral de la documentación de campo.",
        "body_es": [
            {"type": "p", "text": "El Reporte Diario es el registro operacional más consultado que tenemos. Apoya el cruce con nómina, la revisión del proyecto, la resolución de disputas y las investigaciones posteriores."},
            {"type": "why", "text": "Un Reporte Diario completo protege a la cuadrilla y a la empresa. Mejora la comunicación entre el campo y la oficina, ayuda a detectar problemas a tiempo y crea un registro defendible de lo que de verdad pasó en la obra."},
        ],
    },
    "why-photos": {
        "title_es": "Por Qué Importan las Fotos",
        "summary_es": "Las fotos convierten las notas en evidencia.",
        "body_es": [
            {"type": "p", "text": "Las fotos convierten una nota escrita en un registro verificable. Apoyan investigaciones, reclamos de seguro o garantía, el estado del equipo y la documentación del proyecto."},
        ],
    },
    "why-incidents": {
        "title_es": "Por Qué Hay Que Documentar los Incidentes de Seguridad",
        "summary_es": "La documentación apoya la investigación y protege a todos.",
        "body_es": [
            {"type": "p", "text": "Los incidentes documentados apoyan la investigación, ayudan a evitar que se repitan y protegen tanto a la empresa como a las personas involucradas."},
            {"type": "tip", "text": "Documente también los casi-accidentes — son las lecciones más baratas que recibimos."},
        ],
    },
    "why-corrective-actions": {
        "title_es": "Por Qué Importan las Acciones Correctivas",
        "summary_es": "Cierran el ciclo de un problema reportado.",
        "body_es": [
            {"type": "p", "text": "Una Acción Correctiva convierte un incidente o un hallazgo en un seguimiento rastreado. Hace visible si el problema de verdad se atendió."},
        ],
    },
    "why-equipment-accountability": {
        "title_es": "Por Qué Importa la Rendición de Cuentas del Equipo",
        "summary_es": "El equipo asignado tiene costo y responsabilidad.",
        "body_es": [
            {"type": "p", "text": "El equipo asignado lleva costo y responsabilidad. Los registros limpios de salida y devolución ayudan a evitar pérdidas y apoyan la revisión de desvínculo."},
        ],
    },
    "why-time-verification": {
        "title_es": "Por Qué Importa la Verificación de Tiempo",
        "summary_es": "Apoya la exactitud de la nómina y el rastro de auditoría.",
        "body_es": [
            {"type": "p", "text": "El tiempo verificado apoya la exactitud de la nómina y deja un rastro de auditoría limpio si alguna vez se cuestiona un cheque."},
            {"type": "tip", "text": "Regular / Tiempo Extra / Almuerzo se rastrean por separado. Total de horas pagadas = Regular + Tiempo Extra. El almuerzo es tiempo no pagado, rastreado aparte."},
        ],
    },
    "why-audit-logs": {
        "title_es": "Por Qué Importan los Registros de Auditoría",
        "summary_es": "Quién hizo qué, y cuándo.",
        "body_es": [
            {"type": "p", "text": "Los registros de auditoría responden \"quién hizo qué, y cuándo\" — para acciones sensibles de admin, para descargas de respaldo, para cambios de permisos. Así reconstruimos los eventos después del hecho."},
        ],
    },
}
