"""
iter279 · Sequence #8 portals i18n closure.

ES translations for the 33 `portals`-section guidance articles flagged
by the iter277 pre-audit as "minor (i18n only)" / "moderate (i18n only)".

Style discipline (per user directive · iter278 reaffirmed):
  - Operational, concise, field-readable Spanish.
  - Block structure mirrors EN source exactly.
  - Canonical platform terminology only — no regional slang, no
    consultant phrasing, no inflation.
  - Established platform terms used:
      "Reporte Diario" · "Reunión de Seguridad" · "Pre-Op" · "JHA" ·
      "Acción Correctiva" · "Despacho" · "Taller" · "amonestación" ·
      "registro de auditoría" · "rendición de cuentas" · "cuadrilla" ·
      "capataz" · "superintendente" · "permisos" · "respaldo".

Merged into TRANSLATIONS_ES at import time at the bottom of
`translations_es.py`.
"""

EXTRA_ES: dict[str, dict] = {
    "portal-leadership": {
        "title_es": "Inicio Rápido del Portal de Liderazgo de Campo",
        "summary_es": "Superficie de operaciones diarias para supers, capataces y líderes de cuadrilla.",
        "body_es": [
            {"type": "p", "text": "Liderazgo de Campo es la superficie de operaciones diarias para superintendentes, capataces y líderes de cuadrilla. Todo lo que documenta aquí fluye a RH, Seguridad y revisión de PM."},
            {"type": "bullets", "items": [
                "Reportes Diarios",
                "Amonestaciones / Coaching Verbal / Asistencia",
                "Reconocimientos",
                "Salida de Equipo",
                "Evaluaciones de Empleado Nuevo / Cuadrilla",
                "Notas de Deficiencia de Capacitación",
            ]},
            {"type": "tip", "text": "Use el acceso directo del portal en la pantalla de inicio del teléfono. El portal está hecho mobile-first porque la mayoría de la documentación pasa en el campo con el teléfono."},
        ],
    },
    "pm-reporting-workflows": {
        "title_es": "PM · Flujos de Reportes",
        "summary_es": "Vistas de superficie, desgloses y qué exportar.",
        "body_es": [
            {"type": "p", "text": "El reporteo del PM es por capas. El tablero de PM es el escaneo de superficie; los desgloses contestan preguntas específicas; los exportes apoyan conversaciones fuera de la plataforma."},
            {"type": "bullets", "items": [
                "Tablero: resumen por proyecto de actividad reciente, pendientes, alertas",
                "Desglose: detalle por registro (reporte diario, inspección, etc.)",
                "Exporte: CSV / PDF para revisión de dueño / cliente / ejecutivo",
            ]},
            {"type": "why", "text": "El reporteo por capas se ajusta al tipo de pregunta que se está haciendo. El tablero contesta '¿cómo va el proyecto?'; los desgloses contestan '¿qué pasó específicamente?'; los exportes contestan 'muéstreme el registro'. Cada uno tiene su lugar."},
            {"type": "next", "items": [
                "El registro de auditoría guarda quién exportó qué y cuándo",
                "Desgloses repetidos en la misma área salen como patrones del PM",
            ]},
        ],
    },
    "field-coaching-documentation": {
        "title_es": "Campo · Documentar Coaching y Conversaciones Verbales",
        "summary_es": "Por qué una conversación de 5 minutos merece un registro de 30 segundos.",
        "body_es": [
            {"type": "p", "text": "El coaching verbal es la forma más común de liderazgo y la más sub-documentada. Registrarlo brevemente crea el patrón que RH necesita si la misma conversación se sigue dando."},
            {"type": "bullets", "items": [
                "Fecha, empleado, qué se discutió, qué se acordó",
                "Manténgalo factual — sin opiniones, sin etiquetas",
                "Anote cualquier acción de seguimiento (capacitación, re-checar la próxima semana, etc.)",
            ]},
            {"type": "why", "text": "Un registro de coaching es algo pequeño la primera vez. La cuarta vez se vuelve la base para una amonestación. La décima vez se vuelve la base para una acción correctiva. Nada de eso es posible sin el registro #1."},
            {"type": "mistakes", "items": [
                "Esperar a que la conversación 'se sienta lo suficientemente formal' para documentarla",
                "Registrar opiniones en lugar de hechos",
                "Saltarse la nota de seguimiento (lo que se acordó)",
            ]},
        ],
    },
    "field-equipment-checkout": {
        "title_es": "Campo · Salida y Devolución de Equipo",
        "summary_es": "El traspaso entre supervisor, Taller y RH.",
        "body_es": [
            {"type": "p", "text": "La Salida de Equipo es cómo el liderazgo de campo registra quién tiene qué. Es la fuente tanto para la rendición de cuentas del Taller (dónde está el activo) como de RH (la responsabilidad del empleado)."},
            {"type": "steps", "items": [
                "Abra Liderazgo de Campo → Salida de Equipo",
                "Escoja al empleado y el / los activo(s)",
                "Anote la condición al entregar (las fotos cuentan)",
                "Envíe",
            ]},
            {"type": "why", "text": "Si el equipo se pierde, se daña o no se devuelve al desvincular, el registro de salida contesta quién lo tenía al último. Sin registro de salida = sin rendición de cuentas."},
            {"type": "next", "items": [
                "El Taller ve que el activo ya está asignado (ya no aparece como 'disponible')",
                "RH ve crecer la lista de responsabilidad del empleado",
                "Al desvincular, RH recorre la lista y confirma cada artículo de regreso",
            ]},
            {"type": "tip", "text": "Fotografíe la condición del activo al salir Y al regresar. Las dos fotos son el registro más limpio posible de daño."},
        ],
    },
    "shop-maintenance-coordination": {
        "title_es": "Taller · Coordinación de Mantenimiento",
        "summary_es": "Servicio programado, historial del activo y el traspaso con Despacho.",
        "body_es": [
            {"type": "p", "text": "El trabajo de mantenimiento — programado o reactivo — fluye por el Taller. El punto es mantener el equipo trabajando mientras se preserva un historial de servicio limpio por activo."},
            {"type": "bullets", "items": [
                "Servicio programado: basado en horas / millaje / calendario por activo",
                "Servicio reactivo: de un Pre-Op fallido, reporte de daño o nota del operador",
                "Registro de servicio: qué se hizo, por quién, partes usadas, horas en el activo",
                "Traspaso con Despacho: el activo está no-disponible durante el servicio, disponible otra vez al firmar el cierre",
            ]},
            {"type": "why", "text": "Un historial limpio de mantenimiento reduce el tiempo muerto inesperado, apoya el valor de garantía / reventa y contesta preguntas cuando un activo falla ('¿se le dio servicio a tiempo?')."},
            {"type": "next", "items": [
                "El registro de servicio es buscable por activo",
                "Despacho se actualiza cuando un activo entra / sale de servicio",
                "Patrones de servicio recurrente marcan candidatos para reemplazo",
            ]},
        ],
    },
    "admin-system-health": {
        "title_es": "Admin · Salud del Sistema y Sesiones",
        "summary_es": "Cómo se ve 'saludable' y cómo notar cuando no lo es.",
        "body_es": [
            {"type": "p", "text": "Admin → Sistema expone los signos vitales de la plataforma: salud de Mongo, programador, respaldos recientes, sesiones activas. La mayoría del tiempo esta página es aburrida — ese es el punto. Ponga atención cuando no lo es."},
            {"type": "bullets", "items": [
                "Mongo + programador = los dos en verde en todo momento",
                "Frescura del respaldo: la marca de tiempo del respaldo más reciente debe estar dentro de la cadencia automática",
                "Panel de las últimas 5 sesiones: detecte sesiones activas viejas o anómalas",
                "/api/health/full: prueba profunda de salud (usada por UptimeRobot)",
            ]},
            {"type": "why", "text": "Aburrido es la meta. La mayoría de los días la página de salud del sistema no le dice nada nuevo. La disciplina está en revisarla de todos modos — porque el día que tenga algo que decir, usted quiere enterarse desde esta página, no por un usuario."},
            {"type": "next", "items": [
                "Falla de frescura del respaldo → revise el log del programador; usualmente transitorio",
                "Anomalía de sesión → cruce con el registro de auditoría",
            ]},
        ],
    },
    "admin-audit-forensics": {
        "title_es": "Admin · Forense del Registro de Auditoría",
        "summary_es": "Leer la bitácora de auditoría para reconstruir qué pasó en realidad.",
        "body_es": [
            {"type": "p", "text": "El registro de auditoría es la memoria de la plataforma. Cuando surge una pregunta — '¿quién deshabilitó esa cuenta?', '¿quién exportó el respaldo?', '¿cuándo cambió este permiso?' — el registro de auditoría es donde se obtiene una respuesta defendible."},
            {"type": "bullets", "items": [
                "Eventos de inicio / cierre de sesión con IP",
                "Crear / deshabilitar cuenta / reset de contraseña",
                "Descargas de respaldos (cadena de custodia)",
                "Cambios de permisos y plantillas de rol",
                "Acciones admin sensibles (denegaciones registradas para verificación de step-up)",
            ]},
            {"type": "steps", "items": [
                "Filtre por actor (correo) o por tipo de acción",
                "Acote por ventana de tiempo",
                "Lea la cadena de extremo a extremo antes de concluir — filas sueltas engañan",
                "Exporte las filas relevantes para el registro de la investigación",
            ]},
            {"type": "why", "text": "El registro de auditoría es la respuesta a preguntas de confianza. Sin él, cada disputa es la memoria de una persona contra la de otra. Con él, el sistema habla por sí mismo."},
        ],
    },
    "pm-labor-documentation": {
        "title_es": "PM · Relación entre Mano de Obra y Documentación",
        "summary_es": "Cómo las entradas de mano de obra de campo se vuelven costo real del proyecto.",
        "body_es": [
            {"type": "p", "text": "Las horas registradas en reportes de campo se vuelven el costo de mano de obra del proyecto. El PM es la persona que sabe si esas horas tienen sentido para el trabajo realizado — nadie más tiene la vista de campo y la vista de costo al mismo tiempo."},
            {"type": "bullets", "items": [
                "Horas del reporte diario → verificación de tiempo de RH → código de costo de nómina",
                "Proyecto equivocado en un reporte diario = código de costo equivocado en nómina",
                "Las discrepancias de tiempo usualmente se atrapan en la revisión semanal de PM",
            ]},
            {"type": "why", "text": "La mano de obra usualmente es la línea más grande del proyecto. Datos malos de mano de obra no es un problema chico — es un problema de miles de dólares repetido cada semana. La revisión de PM es donde se atrapa antes de que se acumule."},
            {"type": "mistakes", "items": [
                "Asumir que RH va a atrapar los códigos de proyecto equivocados (RH atrapa totales, PM atrapa proyectos)",
                "Revisar la mano de obra solo a fin de mes (el error se compone por 4 semanas)",
                "No pedir una re-entrada cuando el reporte tiene un error material",
            ]},
        ],
    },
    "pm-project-review-cadence": {
        "title_es": "PM · Cadencia de Revisión del Proyecto",
        "summary_es": "Qué revisar, con qué frecuencia, qué escalar.",
        "body_es": [
            {"type": "p", "text": "La revisión del PM es el sistema de alerta temprana del proyecto. Las revisiones diarias atrapan problemas pequeños; los resúmenes semanales atrapan tendencias; las revisiones mensuales marcan la dirección. Saltarse un nivel rompe el sistema de alerta."},
            {"type": "steps", "items": [
                "Diario: revise reportes diarios buscando problemas, entradas faltantes, atraso de programa",
                "Semanal: resumen de horas, conteo de incidentes, estado de equipo, pendientes abiertos",
                "Mensual: revisión de tendencia del proyecto con liderazgo, alineación de alcance",
                "Trimestral: lecciones aprendidas entre proyectos",
            ]},
            {"type": "why", "text": "La mayoría de los problemas de proyecto aparecen en la ventana diaria / semanal como señales chicas. El costo de atraparlos ahí es horas; el costo de atraparlos en la revisión mensual es semanas; el costo de atraparlos al cierre es la orden de cambio."},
            {"type": "next", "items": [
                "Los problemas marcados en revisión se vuelven pendientes de seguimiento del PM",
                "Los patrones informan el coaching del supervisor",
                "Las tendencias entre proyectos suben a admin y liderazgo",
            ]},
        ],
    },
    "dispatch-availability-management": {
        "title_es": "Despacho · Disponibilidad y Utilización",
        "summary_es": "Qué significa 'disponible' en realidad, y el costo de los datos viejos.",
        "body_es": [
            {"type": "p", "text": "'Disponible' tiene un significado preciso: sin asignar a un proyecto, sin retención, fuera de servicio del Taller, condición verificada. Cualquier cosa menos es algo más — y el sistema registra la diferencia para que Despacho pueda decidir con exactitud."},
            {"type": "bullets", "items": [
                "Disponible — listo para ser asignado",
                "Asignado — actualmente en un proyecto",
                "En tránsito — moviéndose entre obras",
                "En retención — temporalmente restringido (certificación del operador, pausa de proyecto, etc.)",
                "En servicio — el Taller tiene el activo",
                "Fuera de servicio — Pre-Op fallido o daño pendiente de reparación",
            ]},
            {"type": "why", "text": "La disponibilidad vieja es la fuente de más esfuerzo desperdiciado al día que cualquier otro tipo de dato malo. Un capataz manejando hasta un patio por un activo que no está ahí son los cinco minutos más caros de despacho."},
            {"type": "next", "items": [
                "Los cambios de disponibilidad fluyen a las listas de asignación de campo en tiempo real",
                "Los reportes de utilización detectan activos sobre- o sub-utilizados",
                "Los patrones informan decisiones de tamaño de flota",
            ]},
        ],
    },
    "field-incident-escalation": {
        "title_es": "Campo · Cadena de Escalación de Incidentes",
        "summary_es": "Campo → Seguridad → Admin: quién ve qué, cuándo.",
        "body_es": [
            {"type": "p", "text": "Un incidente en el campo viaja por una cadena definida. Conocer la cadena ayuda a que las personas correctas respondan a tiempo."},
            {"type": "steps", "items": [
                "Haga la escena segura — eso siempre es el paso uno",
                "Documente el incidente con fotos y un relato escrito",
                "Envíe a través del portal de Campo o Seguridad antes de dejar el sitio",
                "Seguridad revisa y puede abrir una Acción Correctiva",
                "Los incidentes graves escalan a Admin y al PM asignado",
            ]},
            {"type": "why", "text": "La documentación rápida y factual del incidente apoya la investigación, protege a las personas involucradas y previene eventos repetidos. La documentación tarde o vaga hace lo contrario."},
            {"type": "warn", "text": "No especule sobre la causa en el reporte de incidente. Registre lo que observó. El análisis de causa es trabajo de la investigación, no del reporte de campo."},
            {"type": "next", "items": [
                "Seguridad revisa dentro de su cadencia normal",
                "Las Acciones Correctivas (si las hay) se siguen aparte",
                "El registro de auditoría preserva la cadena de envío",
                "Los incidentes graves disparan notificación a admin",
            ]},
        ],
    },
    "safety-training-compliance": {
        "title_es": "Seguridad · Capacitación y Seguimiento de Cumplimiento",
        "summary_es": "Quién está capacitado en qué, cuándo vence, qué hacer cuando vence.",
        "body_es": [
            {"type": "p", "text": "Los registros de capacitación prueban quién está calificado para operar qué. También son lo que protege a la compañía cuando surge la pregunta de si alguien debería haber estado operando equipo para el que no estaba capacitado."},
            {"type": "bullets", "items": [
                "Cada registro de capacitación liga a un empleado + una competencia + una fecha",
                "Las competencias con vencimiento cargan una fecha de renovación",
                "La Salida de Equipo se puede cruzar contra los registros de capacitación",
                "La capacitación vencida o faltante aparece en el tablero de Seguridad",
            ]},
            {"type": "why", "text": "Los registros de capacitación son la respuesta documentada a '¿debió haber estado haciendo eso?'. La capacitación sin registrar es capacitación indefendible."},
            {"type": "mistakes", "items": [
                "Entregar equipo a alguien cuya capacitación venció",
                "Archivar los certificados de capacitación fuera de la plataforma ('lo agrego después')",
                "Tratar las fechas de renovación como sugerencias",
            ]},
            {"type": "next", "items": [
                "Los registros fluyen a la vista de responsabilidad del empleado en RH",
                "La capacitación por vencer sale en el resumen semanal",
                "El registro de auditoría guarda quién registró la capacitación y cuándo",
            ]},
        ],
    },
    "safety-fire-extinguishers": {
        "title_es": "Seguridad · Inspecciones de Extintores",
        "summary_es": "Cadencia mensual de inspección, historial de la unidad, deficiencias, reemplazo.",
        "body_es": [
            {"type": "p", "text": "Los extintores cargan una cadencia explícita de inspección — por código y por política de la compañía. Cada unidad tiene un historial: inspecciones, deficiencias, recargas, reemplazos."},
            {"type": "steps", "items": [
                "Abra Seguridad → Extintores",
                "Escoja la unidad (por serie o etiqueta)",
                "Registre la inspección: presión / sello / pin / manguera / señalización / despeje",
                "Anote cualquier deficiencia — abra un seguimiento para reparación o reemplazo",
                "Envíe — el historial de la unidad se actualiza con la marca de tiempo + inspector",
            ]},
            {"type": "why", "text": "Los registros de extintores los inspeccionan autoridades de código y aseguradoras. Un mes faltante es un hallazgo; un año faltante es un problema. El historial es la defensa de la unidad."},
            {"type": "warn", "text": "Un extintor fallado está fuera de servicio hasta que se reemplace — no lo regrese a su soporte con una deficiencia abierta."},
            {"type": "next", "items": [
                "El historial de la unidad es buscable por serie / proyecto / inspector",
                "Las unidades deficientes se marcan en el tablero de Seguridad hasta resolverse",
                "Los ciclos anuales de recarga / reemplazo se siguen desde el mismo registro",
            ]},
        ],
    },
    "admin-data-portability": {
        "title_es": "Admin · Portabilidad de Datos y Exportes Legibles",
        "summary_es": "Cuando clientes, auditores o abogados necesitan registros legibles.",
        "body_es": [
            {"type": "p", "text": "Los exportes legibles convierten la base de datos en algo que un lector no técnico puede abrir. Se usan para escenarios de cliente que se va de la plataforma, peticiones de auditor / abogado, o simplemente pulls internos de registros."},
            {"type": "bullets", "items": [
                "PDF por registro (formato de plataforma cuando está disponible, fallback en otros casos)",
                "CSV / JSON / RAW por registro",
                "Fotos resueltas offline (sin dependencia de R2 al leer)",
                "Manifiesto + reporte de verificación incluido en cada exporte",
            ]},
            {"type": "why", "text": "La portabilidad de datos no es una función de marketing — es una obligación operacional. Cuando un cliente, auditor o abogado necesita registros, los exportes legibles son la respuesta que no requiere un desarrollador ni un inicio de sesión en la plataforma."},
            {"type": "tip", "text": "Los exportes son neutrales en almacenamiento por diseño. La herramienta de exporte nunca sube automáticamente a R2 — esa decisión le pertenece a quien corre el exporte, para el caso por el que lo corre."},
            {"type": "next", "items": [
                "Exporte registrado en auditoría con actor, alcance, marca de tiempo",
                "El zip / carpeta de salida se entrega por el canal escogido (manual, por diseño)",
            ]},
        ],
    },
    "safety-audits-workflow": {
        "title_es": "Seguridad · Conducir una Auditoría",
        "summary_es": "Cadencia, alcance, hallazgos, acciones correctivas, documentación.",
        "body_es": [
            {"type": "p", "text": "Las auditorías de Seguridad son revisiones programadas y con alcance limitado de un área, cuadrilla o proceso. La salida es una lista de hallazgos — cada uno se vuelve una observación cerrada o una Acción Correctiva abierta."},
            {"type": "bullets", "items": [
                "Alcance: proyecto, cuadrilla, clase de equipo o proceso",
                "Cadencia: como la establezca el liderazgo de Seguridad — típicamente mensual por proyecto activo",
                "Salida: lista de hallazgos con severidad, dueño y seguimiento",
                "Seguimiento: cada hallazgo no trivial se vuelve una Acción Correctiva",
            ]},
            {"type": "why", "text": "Las auditorías atrapan problemas antes de que se vuelvan incidentes. Una auditoría limpia no es la meta — una auditoría a fondo sí lo es. Los hallazgos son el valor de la auditoría, no su falla."},
            {"type": "mistakes", "items": [
                "Auditar solo cuando algo está mal — la cadencia es el punto",
                "Listar hallazgos sin dueños ni plazos",
                "Registrar 'todo limpio' sin describir qué se inspeccionó en realidad",
            ]},
            {"type": "next", "items": [
                "Los hallazgos fluyen a Acciones Correctivas cuando aplica",
                "El historial de auditoría es buscable por proyecto, cuadrilla y fecha",
                "Los patrones de auditoría informan las prioridades de capacitación de seguridad",
            ]},
        ],
    },
    "field-writeup-authoring": {
        "title_es": "Campo · Redactar una Amonestación Defendible",
        "summary_es": "Hechos, conversación, próximo paso acordado.",
        "body_es": [
            {"type": "p", "text": "Una amonestación registra que una conversación ocurrió, qué se acordó y cuál es el próximo paso. No es una forma de queja — es una estructura de seguimiento."},
            {"type": "bullets", "items": [
                "Qué pasó (hechos, sin etiquetas)",
                "Qué se discutió (resumen de la conversación)",
                "Qué se acordó (próximo paso, plazo, revisión)",
                "Reconocimiento del empleado (donde aplique)",
            ]},
            {"type": "why", "text": "Las amonestaciones defendibles protegen a todos en la cadena — al empleado de acusaciones vagas, al supervisor de memoria selectiva, a la compañía de disputas. El patrón importa más que la dureza de las palabras."},
            {"type": "mistakes", "items": [
                "Escribir solo sobre el incidente, sin próximo paso acordado",
                "Usar palabras de opinión ('flojo', 'descuidado') en lugar de describir conducta",
                "Redactar sin haber tenido la conversación primero",
                "Archivar y olvidar — la revisión es el punto",
            ]},
            {"type": "next", "items": [
                "RH revisa en RH → Registros de Liderazgo de Campo",
                "Amonestaciones repetidas para el mismo empleado salen en revisión",
                "Si se necesita escalar, Seguridad / RH / Admin lo recoge desde ahí",
            ]},
        ],
    },
    "admin-role-templates": {
        "title_es": "Admin · Plantillas de Rol",
        "summary_es": "Por qué existen las plantillas, cómo asignarlas y qué sigue siendo a mano.",
        "body_es": [
            {"type": "p", "text": "Las plantillas de rol capturan los permisos estándar para cada combinación portal-rol (Gerente de RH, Mecánico, Capataz, Superintendente, etc.). Existen para que cada cuenta no tenga que permisionarse desde cero."},
            {"type": "bullets", "items": [
                "31 plantillas integradas a través de los 7 portales (Fase K3)",
                "Jerarquía soportada (PM Solo-Lectura ⊆ Coordinador ⊆ PM)",
                "Las plantillas personalizadas sobreviven al seed del sistema (bandera system != True)",
                "La aplicación se difiere a la Fase K6 — las plantillas existen, hoy se muestran solo lectura",
            ]},
            {"type": "why", "text": "Las plantillas de rol son el área de preparación para reemplazar las revisiones dispersas de `role == \"...\"` con un catálogo único de permisos. Mostrarlas como solo lectura primero deja que el equipo verifique el catálogo antes de activar la aplicación — un despliegue lento deliberado para evitar romper usuarios válidos."},
            {"type": "warn", "text": "Hoy, las plantillas de rol son visibles en el Directorio Unificado pero todavía no las aplican las puertas de autenticación. Las rutas siguen usando verificaciones de token por portal. La transición de aplicación está escalonada (Fase K6) e intencionalmente gradual."},
        ],
    },
    "shop-equipment-return": {
        "title_es": "Taller · Devolución y Reconciliación de Equipo",
        "summary_es": "Recibir equipo de regreso — revisión de condición, historial, rendición de cuentas.",
        "body_es": [
            {"type": "p", "text": "Las devoluciones de equipo son donde aterriza la rendición de cuentas. Sea la devolución rutinaria (fin de obra) o parte de un desvínculo, el trabajo del Taller es verificar qué regresó, en qué condición, con qué historial."},
            {"type": "steps", "items": [
                "Inspeccione al regreso — fotografíe la condición (que empate con las fotos de salida cuando estén disponibles)",
                "Anote cualquier daño descubierto al regreso que no se haya registrado antes",
                "Actualice el estado del activo: disponible / en servicio / dañado / perdido",
                "Ate al registro de Salida de Liderazgo de Campo si aplica",
                "Si está asociado con un desvínculo, confirme que RH ve el activo como devuelto",
            ]},
            {"type": "why", "text": "Las devoluciones cierran el ciclo de rendición de cuentas abierto en la salida. Sin un registro limpio de devolución, un activo puede 'devolverse' de palabra pero seguir marcado como asignado en el sistema — el tipo de inconsistencia que aparece hasta fin de año."},
            {"type": "mistakes", "items": [
                "Aceptar una devolución sin inspeccionar la condición",
                "Saltarse la foto al regreso ('se ve bien')",
                "No actualizar el estado del activo — el registro lo muestra todavía asignado",
                "Devolver equipo desvinculado sin notificar a RH",
            ]},
        ],
    },
    "admin-sentry-observability": {
        "title_es": "Admin · Postura de Sentry y Observabilidad",
        "summary_es": "Errores, releases y disciplina con PII.",
        "body_es": [
            {"type": "p", "text": "Sentry está activo en preview y producción para backend y frontend. Su trabajo es exponer los errores que el equipo no vio — peticiones que fallan en silencio, frontends rotos en ambientes que no se están usando activamente."},
            {"type": "bullets", "items": [
                "Identificador de release = hash del código fuente (BE + FE comparten la misma etiqueta de release)",
                "El sanitizador de PII quita password*/token*/secret*/api_key* + headers de auth + blobs hex",
                "Auto-seguimiento de sesiones habilitado para release-health",
                "El init es no-op si el DSN no está configurado — la app está segura sin Sentry configurado",
            ]},
            {"type": "why", "text": "La mayoría de los bugs de producción no los reportan los usuarios — son fallas en silencio que el equipo no sabe que tiene que buscar. El trabajo de Sentry es exponerlas automáticamente, con suficiente contexto de release para saber qué deploy las introdujo y cuál las arregló."},
            {"type": "warn", "text": "NO registre cuerpos crudos de peticiones ni payloads de respuesta a Sentry. El sanitizador atrapa las llaves comunes; asuma que cualquier superficie no sanitizada se registra en claro."},
            {"type": "next", "items": [
                "Los errores nuevos salen en issues de Sentry — triaje el mismo día",
                "La salud de release baja después de un deploy → haga rollback rápido, investigue después",
            ]},
        ],
    },
    "dispatch-holds-transfers": {
        "title_es": "Despacho · Retenciones y Transferencias",
        "summary_es": "Pausar, liberar y ruteo de activos sin perder rendición de cuentas.",
        "body_es": [
            {"type": "p", "text": "Una retención es una restricción temporal. Una transferencia es un cambio permanente de asignación. Son operaciones distintas porque tienen efectos diferentes aguas abajo — una retención es reversible sin rehacer la rendición de cuentas; una transferencia no."},
            {"type": "bullets", "items": [
                "Razones de retención: certificación del operador, pausa de proyecto, clima, inspección",
                "Razones de transferencia: terminación de proyecto, reasignación, devolución de renta",
                "Cada una lleva un código de razón que sale en el historial del activo",
            ]},
            {"type": "why", "text": "Retención vs transferencia es una de las operaciones más confundidas en despacho — y una donde la elección equivocada envenena en silencio los reportes aguas abajo. Escoger la correcta es como los números de utilización del proyecto se mantienen honestos."},
            {"type": "warn", "text": "No use una retención cuando una transferencia es la operación correcta, o al revés. Un activo retenido sigue contando contra la utilización del proyecto original; un activo transferido no. El reporteo aguas abajo depende de la elección correcta."},
            {"type": "next", "items": [
                "Los activos retenidos reaparecen cuando se libera la retención",
                "Los activos transferidos cierran el registro del proyecto original",
                "Las vistas del PM se actualizan con el cambio",
            ]},
        ],
    },
    "shop-damage-reporting": {
        "title_es": "Taller · Reporte de Daños",
        "summary_es": "Del descubrimiento a la recuperación de costo — el rastro completo del daño.",
        "body_es": [
            {"type": "p", "text": "Los reportes de daño documentan el daño al equipo con suficiente detalle para apoyar la planeación de la reparación, los reclamos de garantía / seguro y (cuando aplique) las conversaciones de rendición de cuentas con el operador."},
            {"type": "steps", "items": [
                "Fotografíe el daño — toma amplia para contexto, acercamientos para detalle",
                "Registre el activo (serie / etiqueta), la fecha, quién lo descubrió",
                "Describa qué pasó de manera factual — cuando se sabe, por quién; cuando no, dígalo",
                "Ate al nombre del operador si el daño está asociado a un uso específico",
                "Envíe — el Taller, Admin y (donde aplique) RH pueden revisar",
            ]},
            {"type": "why", "text": "Los registros de daño apoyan tres conversaciones aguas abajo: cuánto reparar / reemplazar, si aplica el seguro o la garantía, y si el daño apunta a un problema de capacitación o proceso."},
            {"type": "warn", "text": "Los reportes de daño son registros factuales, no atribuciones de culpa. Describa lo que observó; deje que RH / Seguridad maneje las discusiones de rendición de cuentas por separado."},
            {"type": "next", "items": [
                "El Taller programa la reparación o la baja",
                "Si está asociado con un operador, el registro es visible para RH para revisión",
                "El historial del activo crece — los patrones salen (algunos activos / operadores se repiten)",
            ]},
        ],
    },
    "admin-backup-restore": {
        "title_es": "Admin · Postura de Respaldos y Restauración",
        "summary_es": "Qué se respalda, cuándo, dónde vive y cómo probar que funciona.",
        "body_es": [
            {"type": "p", "text": "MASCI mantiene dos sistemas de preservación en paralelo: respaldos técnicos (usados para restaurar la base de datos en vivo) y exportes legibles (usados para leer registros fuera de la plataforma). Un respaldo que nunca se ha restaurado todavía no es un respaldo — es una suposición."},
            {"type": "bullets", "items": [
                "Snapshots por hora + nocturnos → Cloudflare R2 → expiración por ciclo de vida a 90 días",
                "Simulacro de restauración a DB lateral: valida que un respaldo realmente se puede leer en Mongo",
                "Cadencia trimestral del simulacro; registrada en `RESTORE_DRILL.md`",
                "Exporte legible: herramienta separada, neutral en almacenamiento, bajo demanda",
            ]},
            {"type": "why", "text": "Un respaldo que nunca se ha restaurado es una suposición, no un respaldo. La cadencia del simulacro convierte esa suposición en una capacidad verificada — y el blanco de DB lateral asegura que la verificación nunca arriesga la base de datos en vivo."},
            {"type": "warn", "text": "Nunca restaure un respaldo sobre la DB en vivo. El script del simulacro rechaza cualquier target_db que no empiece con `masci_restore_drill_`. Ese rechazo es intencional."},
            {"type": "next", "items": [
                "Simulacro fallido = el respaldo está sospechoso; investigue de inmediato",
                "Simulacro exitoso = se agrega la fila del simulacro al runbook",
                "Las decisiones de restauración sobre datos en vivo involucran a Admin + seguros / legal según aplique",
            ]},
        ],
    },
    "hr-writeups-correctives": {
        "title_es": "RH · Amonestaciones y Seguimiento de Acciones Correctivas",
        "summary_es": "Qué hace defendible a una amonestación de RH y cómo viaja por la plataforma.",
        "body_es": [
            {"type": "p", "text": "Las amonestaciones se originan en Liderazgo de Campo (el supervisor las redacta). RH revisa, archiva y le da seguimiento. Una amonestación es documentación operacional, no un castigo — su trabajo es registrar que una conversación pasó, qué se acordó y cuál es el próximo paso."},
            {"type": "bullets", "items": [
                "El supervisor redacta la amonestación en Liderazgo de Campo",
                "RH revisa en RH → Registros de Liderazgo de Campo",
                "Las Acciones Correctivas (si las hay) las sigue Seguridad por separado",
                "Cada amonestación tiene marca de tiempo, atribución y queda en el registro de auditoría",
            ]},
            {"type": "why", "text": "Una amonestación defendible protege a todos. Protege al empleado de acusaciones vagas, al supervisor de memoria selectiva y a la compañía de disputas. Las amonestaciones vagas no protegen a nadie."},
            {"type": "mistakes", "items": [
                "Editar el registro original del supervisor — RH revisa, no reescribe",
                "Cerrar el ciclo de palabra sin registrarlo",
                "Tratar una amonestación como el final de la historia — usualmente es el inicio de una",
                "Saltarse la conversación y solo archivar el formato",
            ]},
            {"type": "next", "items": [
                "La amonestación se vuelve visible para RH, Admin y el supervisor que la redactó",
                "Si se abre una Acción Correctiva, Seguridad es dueña del seguimiento",
                "Las amonestaciones repetidas para el mismo empleado salen como patrones en la revisión de RH",
            ]},
        ],
    },
    "admin-user-management": {
        "title_es": "Admin · Gestión de Usuarios",
        "summary_es": "Crear, deshabilitar, transferir, restablecer — el día a día del directorio.",
        "body_es": [
            {"type": "p", "text": "La gestión de usuarios es el corazón diario del trabajo de admin. La mayoría es crear y deshabilitar cuentas, restablecer contraseñas y asignar plantillas de rol. Cada una es pequeña; la disciplina está en hacerla con consistencia."},
            {"type": "steps", "items": [
                "Crear: ingrese correo + portal(es) + plantilla de rol; ponga must_change_password=true",
                "Deshabilitar (preferido sobre borrar): preserva el historial de auditoría",
                "Restablecer contraseña: credencial temporal emitida por admin, cambio forzado en el siguiente inicio de sesión",
                "Convertir espejo → gestionado (K4b, cuando esté conectado): traspaso explícito de contraseña",
            ]},
            {"type": "why", "text": "La gestión de usuarios es el perímetro de acceso de la plataforma. Una cuenta deshabilitada-no-borrada preserva la cadena de auditoría; un cambio forzado de contraseña al primer inicio preserva el secreto. Las dos disciplinas chicas suman a la respuesta de la plataforma cuando después se cuestiona el acceso."},
            {"type": "warn", "text": "Nunca borre una cuenta que tenga historial de auditoría — deshabilítela. Borrar rompe toda referencia del rastro de auditoría que apunta a ese usuario. Deshabilitar preserva el historial; borrar borra la cadena de custodia."},
            {"type": "next", "items": [
                "Los usuarios creados aparecen en el directorio al siguiente cargado de página",
                "Las cuentas deshabilitadas dejan de funcionar de inmediato en la siguiente petición",
                "El registro de auditoría guarda cada acción de crear / deshabilitar / restablecer contraseña",
            ]},
        ],
    },
    "dispatch-equipment-movement": {
        "title_es": "Despacho · Ciclo de Vida del Movimiento de Equipo",
        "summary_es": "Transferencias entre obras, estado en tránsito, confirmación de llegada.",
        "body_es": [
            {"type": "p", "text": "El equipo no se teletransporta entre obras. El movimiento es un evento rastreado con un origen, un destino, un estado en tránsito y una confirmación de llegada. Cada uno de esos estados es visible para quien lo necesita."},
            {"type": "steps", "items": [
                "El PM / supervisor de origen libera el activo (o Despacho lo recupera)",
                "Despacho crea el evento de movimiento con origen / destino / tiempos",
                "El activo entra a `en tránsito` — invisible a la lista de activos activos de cualquiera de las dos obras",
                "El proyecto receptor confirma la llegada; el activo reentra a `asignado` en la nueva obra",
                "El evento de movimiento se cierra — visible en el historial del activo",
            ]},
            {"type": "why", "text": "Sin un movimiento rastreado, el equipo puede aparecer como 'todavía en la obra A' cuando físicamente está en la obra B. Eso rompe tanto los reportes de activos del proyecto como la capacidad del Taller de saber a dónde enviar un técnico para servicio."},
            {"type": "mistakes", "items": [
                "Reasignar al nuevo proyecto sin liberar del anterior",
                "Saltarse el estado en tránsito (salta de A a B sin gap, esconde retrasos)",
                "Olvidar confirmar la llegada (el activo aparece en tránsito indefinidamente)",
            ]},
            {"type": "next", "items": [
                "Las listas de activos de los dos proyectos se actualizan automáticamente",
                "El historial del activo muestra la ruta completa — útil para análisis de utilización",
                "Los PMs ven los cambios a nivel proyecto en su tablero",
            ]},
        ],
    },
    "shop-failed-preop-workflow": {
        "title_es": "Taller · Flujo de Pre-Op Fallido",
        "summary_es": "Qué pasa después de un Pre-Op fallido — y quién está involucrado.",
        "body_es": [
            {"type": "p", "text": "Cuando un Pre-Op falla — o el operador marca una condición de Fuera de Servicio — una cadena definida se activa. El activo se etiqueta, el Taller es notificado, Despacho sabe que está no-disponible y el campo tiene por qué documentado."},
            {"type": "steps", "items": [
                "El operador marca el Pre-Op como fallido (o fuera de servicio) y documenta qué",
                "Auto-correo se reparte a cada usuario activo del Taller + al supervisor",
                "El Taller revisa, programa reparación o saca el activo",
                "Se actualiza Despacho — el activo deja de aparecer como disponible",
                "Cuando se repara, el Taller firma — el activo reentra a disponibilidad",
            ]},
            {"type": "why", "text": "Sin esta cadena, un activo fallado puede seguirse entregando al siguiente operador. El registro de falla + la retención de despacho son las dos cosas que paran el ciclo. Las dos tienen que aterrizar o el sistema se rompe."},
            {"type": "mistakes", "items": [
                "Marcar 'falla' sin describir la falla",
                "Traspaso verbal al Taller sin archivar la forma (no existe registro)",
                "Regresar a servicio sin la firma del Taller",
                "Saltarse la actualización de Despacho — el activo aparece disponible pero no lo está",
            ]},
            {"type": "next", "items": [
                "El Taller recibe el correo de alerta y abre el registro de inspección",
                "Despacho ve el activo en la lista de Fuera de Servicio",
                "La firma del Taller cierra el ciclo y libera el activo",
                "El registro de auditoría preserva el ciclo de vida completo de la falla",
            ]},
        ],
    },
    "hr-offboarding": {
        "title_es": "RH · Desvínculo del Empleado",
        "summary_es": "Devolución de equipo, deshabilitar cuenta, pago final, cierre de auditoría.",
        "body_es": [
            {"type": "p", "text": "El desvínculo es el reverso de la integración — y igual de importante. La meta es sin cabos sueltos: cada artículo asignado está devuelto o contabilizado, cada cuenta está deshabilitada y el último cheque refleja horas verificadas."},
            {"type": "steps", "items": [
                "Saque el historial de salidas de equipo del empleado (RH → Rendición de Cuentas del Empleado)",
                "Confirme que cada artículo está devuelto, transferido o dado de baja — registre cuál",
                "Corra una Verificación de Tiempo final hasta su último día de trabajo",
                "Deshabilite la cuenta del portal del empleado en Admin → Personas y Acceso (NO la borre)",
                "Anote la fecha del desvínculo en su registro",
                "Informe a nómina la ventana de pago final (fuera de la plataforma)",
            ]},
            {"type": "why", "text": "La documentación del desvínculo contesta dos preguntas que vuelven después: '¿Recuperamos nuestras cosas?' y '¿El último cheque estuvo bien?'. Un desvínculo limpio cierra las dos antes de que se vuelvan disputa."},
            {"type": "warn", "text": "Deshabilite las cuentas, NO las borre. Borrar una cuenta rompe todo rastro de auditoría que la referencia. Deshabilitar preserva el historial; borrar lo borra."},
            {"type": "next", "items": [
                "La cuenta deshabilitada deja de funcionar de inmediato al siguiente cargado de página",
                "Los registros de equipo muestran el activo como sin asignar (el Taller / Despacho pueden re-emitir)",
                "El CSV de la Verificación de Tiempo final es el registro auditable del último cheque",
                "El registro de auditoría preserva la acción de deshabilitar con el actor y la marca de tiempo",
            ]},
        ],
    },
    "safety-corrective-actions-workflow": {
        "title_es": "Seguridad · Flujo Profundo de Acciones Correctivas",
        "summary_es": "Dueño, plazo, seguimiento, cierre, verificación.",
        "body_es": [
            {"type": "p", "text": "Una Acción Correctiva es un seguimiento rastreado a un incidente, hallazgo de auditoría o casi-incidente. Su trabajo es asegurar que el problema realmente se arregló — no solo se discutió."},
            {"type": "steps", "items": [
                "Abra la Acción Correctiva desde el registro fuente (incidente, auditoría o casi-incidente)",
                "Asigne un dueño — debe ser una persona específica, no un departamento",
                "Ponga un plazo — corto suficiente para mantener impulso, realista suficiente para cumplir",
                "Defina cómo se ve 'hecho' (capacitación completada, equipo reemplazado, procedimiento actualizado, etc.)",
                "El dueño ejecuta y registra qué cambió (fotos, reconocimientos firmados, registros de capacitación)",
                "Seguridad verifica y cierra — nunca cierre sin verificar",
            ]},
            {"type": "why", "text": "Sin Acciones Correctivas, el mismo problema pasa otra vez y nadie puede decir qué se hizo la vez pasada. Las Acciones Correctivas son la diferencia entre documentar el fracaso y documentar la mejora."},
            {"type": "mistakes", "items": [
                "Asignar a un departamento ('el Taller se encarga') — asigne a una persona",
                "Criterio de 'hecho' vago ('mejorar la capacitación') — sea específico",
                "Cerrar solo con la palabra del dueño — verifique con el artefacto",
                "Dejar que las acciones envejezcan pasado el plazo sin re-enganchar al dueño",
            ]},
            {"type": "next", "items": [
                "La acción cerrada sale en el registro de auditoría del incidente fuente",
                "Las acciones abiertas salen en el resumen semanal de Seguridad",
                "Las acciones repetidas para la misma causa raíz marcan un problema sistémico",
            ]},
        ],
    },
    "shop-preop-deep": {
        "title_es": "Taller · Inspecciones Pre-Op a Fondo",
        "summary_es": "Qué debe atrapar cada Pre-Op, qué significa 'pasa' en realidad.",
        "body_es": [
            {"type": "p", "text": "Un Pre-Op es la revisión del operador antes de usar el equipo. Es una promesa diaria de que el equipo es seguro para operar — y una protección diaria si resulta que no lo era."},
            {"type": "bullets", "items": [
                "Fluidos — niveles y fugas de motor, hidráulico, refrigerante",
                "Llantas / orugas — presión, desgaste, daño",
                "Luces y señales — direccionales / freno / reversa / estrobo",
                "Dispositivos de seguridad — cinturón, claxon, alarmas, guardas",
                "Controles de operación — rango completo, sin atorones",
                "Daño visible — fisuras de chasis, componentes doblados, tornillería faltante",
            ]},
            {"type": "why", "text": "Los registros de Pre-Op protegen al operador de que lo culpen por un defecto que ya estaba antes de que empezara, y protegen a la compañía de operar equipo que se debió haber sacado de servicio. Un Pre-Op firmado es un registro de rendición de cuentas operacional."},
            {"type": "warn", "text": "El Pre-Op no es papeleo. Si se salta la inspección y 'solo palomea la casilla', firmó un documento diciendo que el equipo estaba seguro cuando en realidad no lo miró."},
            {"type": "mistakes", "items": [
                "Palomear casillas sin caminar el activo",
                "Faltar la parte inferior / lados ciegos (donde se esconde la mayoría del daño)",
                "Saltarse los frenos / dispositivos de seguridad porque 'sirvieron ayer'",
                "Registrar 'pasa' en un problema que pensaba marcar de palabra",
            ]},
            {"type": "next", "items": [
                "El Pre-Op enviado se vuelve parte del registro diario del activo",
                "Un Pre-Op fallido activa el flujo de pre-op fallido (Taller + Despacho alertados)",
                "Un patrón de fallas en el mismo activo sale en las tendencias del Taller",
            ]},
        ],
    },
    "hr-time-verification-deep": {
        "title_es": "RH · Verificación de Tiempo a Fondo",
        "summary_es": "Invariante de Regular / Tiempo Extra / Lunch, cruce con nómina, registro defendible.",
        "body_es": [
            {"type": "p", "text": "La Verificación de Tiempo compara las horas que el supervisor ingresó contra el sistema de nómina. La plataforma hace la división Regular/Tiempo Extra de FLSA en el resumen semanal, no por día. El lunch no se paga y se rastrea aparte."},
            {"type": "bullets", "items": [
                "Total de horas pagadas = Regular + Tiempo Extra (invariante — nunca se rompe)",
                "El lunch se rastrea pero NO se incluye en los totales pagados",
                "El TE es la porción semanal arriba de las 40 horas de trabajo regular",
                "Las filas diarias muestran 0.00 para Reg/TE — eso es por diseño; el resumen es semanal",
            ]},
            {"type": "steps", "items": [
                "Abra RH → Verificación de Tiempo",
                "Escoja el período de pago (semana terminada)",
                "Escanee las tarjetas de resumen: Horas Totales / Regular / Tiempo Extra / Lunch",
                "Entre al detalle de cualquier empleado cuyos totales se vean mal",
                "Marque las discrepancias al supervisor — NO edite en silencio",
                "Exporte CSV con la sección de RESUMEN SEMANAL para cruzar con nómina",
            ]},
            {"type": "why", "text": "La Verificación de Tiempo es el registro más cuestionado que llevamos. Si alguna vez se disputa un cheque, este es el registro que contesta. Un resumen semanal limpio con CSV firmado es un registro defendible. Una entrada adivinada o rellenada después no lo es."},
            {"type": "next", "items": [
                "Los totales verificados alimentan el cruce con nómina (fuera de la plataforma)",
                "El CSV con totales de RESUMEN SEMANAL se puede archivar por período de pago",
                "Las discrepancias se vuelven seguimientos de Liderazgo de Campo — el supervisor edita la fuente, no RH",
            ]},
            {"type": "warn", "text": "RH no edita las horas ingresadas por el supervisor. Si un número está mal, el supervisor lo arregla en el registro fuente — eso preserva la cadena de custodia."},
        ],
    },
    "field-daily-report-howto": {
        "title_es": "Campo · Enviar un Reporte Diario Defendible",
        "summary_es": "Qué va, qué saltarse, por qué importa.",
        "body_es": [
            {"type": "p", "text": "Un Reporte Diario es el registro operacional del día de trabajo. RH lo referencia para tiempo, PM para estado del proyecto, Seguridad para incidentes y liderazgo para revisiones a posteriori. Constrúyalo como si alguien lo fuera a leer en seis meses — porque alguien lo va a leer."},
            {"type": "steps", "items": [
                "Escoja el proyecto correcto (el error más común es el proyecto equivocado)",
                "Ingrese la cuadrilla en sitio, horas trabajadas, lunch",
                "Documente el trabajo realizado en lenguaje sencillo — qué se construyó / completó / bloqueó",
                "Fotografíe el avance, las entregas, las condiciones y cualquier problema",
                "Registre el equipo usado y cualquier falla",
                "Anote las condiciones: clima, retrasos, preocupaciones de seguridad",
                "Envíe ANTES de dejar el sitio",
            ]},
            {"type": "why", "text": "El reporte diario es el documento que más se cita de los que llevamos. Apoya la nómina, disputas de programa del proyecto, órdenes de cambio, reclamos de seguro e investigaciones de seguridad. El liderazgo de campo es el único rol que lo puede producir."},
            {"type": "mistakes", "items": [
                "Proyecto equivocado seleccionado (todo aguas abajo queda mal)",
                "Sin fotos (una nota sin foto es más difícil de defender)",
                "Enviar desde casa al día siguiente (la marca de tiempo está mal; los detalles ya están fríos)",
                "Saltarse el campo de 'problemas' porque nada se sintió tan grande para mencionarse",
                "Copiar-pegar la narrativa de ayer",
            ]},
            {"type": "next", "items": [
                "El reporte se vuelve visible para PM, RH, Admin y liderazgo autorizado",
                "Las entradas de tiempo del reporte alimentan la Verificación de Tiempo de RH",
                "Las fotos se vuelven parte del archivo del proyecto — buscables por fecha",
                "Los problemas marcados se vuelven seguimientos del PM",
            ]},
        ],
    },
    "safety-incident-investigation": {
        "title_es": "Seguridad · Investigar un Incidente Después del Envío",
        "summary_es": "Triaje, causa raíz, evidencia fotográfica, declaraciones de testigos.",
        "body_es": [
            {"type": "p", "text": "Una vez que un incidente de campo se envía, Seguridad es dueña de la investigación. El trabajo de la investigación no es asignar culpa — es reconstruir lo que pasó con suficientes hechos como para que el mismo evento se pueda prevenir la próxima vez."},
            {"type": "steps", "items": [
                "Lea el reporte de campo completo — no lo escanee",
                "Verifique que la escena se hizo segura (el reporte lo debe decir explícitamente)",
                "Revise cada foto; pida fotos adicionales si la escena no se capturó",
                "Reúna declaraciones de testigos mientras la memoria está fresca — idealmente dentro de 24h",
                "Identifique factores contribuyentes (equipo, capacitación, procedimiento, ambiente)",
                "Decida si una Acción Correctiva está justificada",
                "Documente los hallazgos de la investigación en el registro del incidente",
            ]},
            {"type": "why", "text": "Una investigación a fondo protege a todos — al lesionado, a los testigos, al supervisor y a la compañía. Una investigación apurada o saltada crea un registro que no prueba nada, lo cual es peor que no tener registro."},
            {"type": "mistakes", "items": [
                "Especular sobre la causa antes de tener los hechos",
                "Dejar que la investigación se pase de 72h (la memoria se degrada rápido)",
                "Cerrar sin un hallazgo escrito — incluso 'no se requiere acción adicional' es un hallazgo",
                "Saltarse la entrevista del testigo porque 'parece menor'",
            ]},
            {"type": "next", "items": [
                "Acción Correctiva abierta (si aplica) — vea safety-corrective-actions-workflow",
                "Los incidentes graves escalan a Admin + revisión de seguros",
                "El registro de auditoría guarda cada paso de la investigación",
                "Los patrones salen en la revisión mensual de Seguridad (varios incidentes similares = sistémico)",
            ]},
        ],
    },
    "hr-onboarding-new-hire": {
        "title_es": "RH · Integración de Nuevo Empleado",
        "summary_es": "Configuración de cuenta, salida de equipo, asignación de capacitación, rastro documental.",
        "body_es": [
            {"type": "p", "text": "Integrar un nuevo empleado crea el registro operacional que lo sigue por toda su estancia. La meta es un rastro limpio: la cuenta existe, el equipo está firmado, la capacitación está asignada, el supervisor sabe."},
            {"type": "steps", "items": [
                "Confirme que el paquete de contratación está completo (oferta aceptada, I-9, W-4) — fuera de la plataforma",
                "En Admin → Personas y Acceso, cree la cuenta del portal del empleado (campo / taller / despacho según aplique)",
                "Ponga must_change_password=true y entregue las credenciales temporales por el canal que RH usa (correo / en persona)",
                "Abra Formas de Seguridad → Salida de Equipo para cualquier EPP / herramientas / teléfono / tableta asignados el día uno",
                "Abra Formas de Seguridad → Capacitación de Equipo para la capacitación requerida del primer día (extintor, plataforma, etc.)",
                "Avise al supervisor por escrito — el registro de auditoría guarda que lo hizo",
            ]},
            {"type": "why", "text": "La documentación del día uno previene los dos problemas de RH más caros: un empleado disputando lo que se le dio, y un empleado usando equipo para el que no estaba capacitado. Los dos regresan a si el rastro documental existe."},
            {"type": "next", "items": [
                "La salida de equipo auto-correa a Seguridad + RH (rastreado en auditoría)",
                "El supervisor ve al nuevo empleado en el roster de su cuadrilla la siguiente vez que abra Liderazgo de Campo",
                "Los registros de capacitación son buscables por Seguridad para auditorías",
                "Las entradas de tiempo son posibles desde el primer día de trabajo",
            ]},
            {"type": "mistakes", "items": [
                "Saltarse la forma de salida de equipo porque 'es solo un casco'",
                "No poner must_change_password — las credenciales temporales viven para siempre",
                "Entregar equipo sin registrar la capacitación que autoriza su uso",
                "Olvidar avisarle al supervisor (no van a saber que la persona está empezando)",
            ]},
        ],
    },
}
