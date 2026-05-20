"""
iter281 · Sequence #8 roles + reliability i18n closure (final cluster).

ES translations for the remaining 4 articles flagged by the iter277
pre-audit as "minor (i18n only)":
  - 3 roles-section: role-foreman, role-hr, role-superintendent
  - 1 reliability-section: why-backups

Style discipline (per iter278/iter279/iter280): operational, concise,
field-readable Spanish · block structure mirrors EN exactly · canonical
platform terminology only.
"""

EXTRA_ES: dict[str, dict] = {
    "why-backups": {
        "title_es": "Cómo Funcionan los Respaldos de MASCI",
        "summary_es": "Respaldos técnicos, exportes legibles, simulacros de restauración.",
        "body_es": [
            {"type": "p", "text": "MASCI mantiene dos sistemas de preservación en paralelo."},
            {"type": "bullets", "items": [
                "Respaldos técnicos: snapshots nocturnos + por hora guardados en Cloudflare R2. Se usan para restaurar la base de datos en vivo si algo falla.",
                "Exportes legibles: archivos por registro en PDF + CSV. Se usan cuando un lector no técnico necesita ver lo que estaba en el archivo.",
            ]},
            {"type": "p", "text": "Los simulacros de restauración prueban periódicamente que los respaldos técnicos sí se pueden usar — un respaldo que nunca se ha restaurado todavía no es un respaldo."},
            {"type": "why", "text": "Juntos apoyan la recuperación ante desastres, las peticiones de registros de cliente / auditor y la continuidad operacional."},
        ],
    },
    "role-foreman": {
        "title_es": "Capataz",
        "summary_es": "Liderazgo de cuadrilla y documentación diaria del campo.",
        "body_es": [
            {"type": "p", "text": "Los capataces dirigen las cuadrillas en el campo y son dueños de la mayoría de la documentación del día a día: reportes diarios, fotos, estado del equipo, entradas de tiempo."},
            {"type": "why", "text": "La documentación del capataz es el registro operacional más exacto que tenemos. Mejora la exactitud de la nómina y apoya las decisiones del campo."},
            {"type": "bullets", "items": [
                "Envíe un Reporte Diario cada día de trabajo",
                "Documente problemas de equipo de inmediato",
                "Dé coaching a los empleados y registre las conversaciones importantes",
                "Escale los incidentes rápido",
            ]},
        ],
    },
    "role-hr": {
        "title_es": "RH",
        "summary_es": "Tiempo, empleados, amonestaciones, desvínculo.",
        "body_es": [
            {"type": "p", "text": "RH usa la plataforma para verificar tiempo, gestionar registros de empleados, revisar amonestaciones, rastrear la salida de equipo para el desvínculo y documentar acciones de personal."},
            {"type": "why", "text": "La documentación de RH apoya la exactitud de la nómina, ayuda a proteger tanto a MASCI como a los empleados y crea un rastro documental claro para las decisiones de personal."},
            {"type": "bullets", "items": [
                "Verificación de Tiempo",
                "Registros de Empleados",
                "Amonestaciones / Seguimiento de Acciones Correctivas",
                "Desvínculo (devolución de equipo, pago final)",
            ]},
            {"type": "next", "items": [
                "El tiempo verificado va al cruce con nómina",
                "Las amonestaciones son visibles para RH, Admin y liderazgo de campo",
                "El registro de auditoría guarda quién revisó qué",
            ]},
        ],
    },
    "role-superintendent": {
        "title_es": "Superintendente",
        "summary_es": "Operaciones diarias, cuadrilla, equipo, incidentes, coaching.",
        "body_es": [
            {"type": "p", "text": "Los superintendentes documentan las operaciones diarias, la actividad de la cuadrilla, el uso del equipo, los incidentes, el coaching y las condiciones del proyecto."},
            {"type": "why", "text": "La documentación limpia del campo apoya a MASCI, ayuda a la nómina y a la revisión del proyecto, mejora la rendición de cuentas y le da al liderazgo visibilidad en tiempo real."},
            {"type": "bullets", "items": [
                "Reportes Diarios",
                "Reporte de Incidentes",
                "Salida de Equipo",
                "Coaching del Empleado",
                "Acciones Correctivas",
                "Documentación de Seguridad",
            ]},
            {"type": "mistakes", "items": [
                "Fotos faltantes",
                "Notas incompletas",
                "Proyecto equivocado seleccionado",
                "No enviar antes de fin del día",
                "No documentar los problemas de equipo",
            ]},
            {"type": "next", "items": [
                "Los registros se vuelven visibles para el liderazgo autorizado",
                "RH / Seguridad / Admin pueden revisar según el flujo",
                "Los rastros de auditoría preservan el historial de envíos",
            ]},
        ],
    },
}
