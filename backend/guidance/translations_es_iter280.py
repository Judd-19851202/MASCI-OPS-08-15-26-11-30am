"""
iter280 · Sequence #8 knowledge i18n closure.

ES translations for the 19 `knowledge`-section guidance articles flagged
by the iter277 pre-audit as "minor (i18n only)".

Style discipline (per user directive · iter278/iter279 reaffirmed):
  - Operational, concise, field-readable Spanish.
  - Block structure mirrors EN source exactly (same block count, same
    block types per index).
  - Established platform terminology only.

Merged into TRANSLATIONS_ES at import time at the bottom of
`translations_es.py` alongside the iter279 entries.
"""

EXTRA_ES: dict[str, dict] = {
    "field-project-scope": {
        "title_es": "Campo · Lo que Usted Ve en Otros Proyectos",
        "summary_es": "Asignación de proyecto, alcance del PM y por qué podría no ver algo.",
        "body_es": [
            {"type": "p", "text": "Liderazgo de Campo ve los registros ligados a los proyectos que tiene asignados. Los PMs ven los registros ligados a los proyectos que manejan. Admin lo ve todo."},
            {"type": "bullets", "items": [
                "Si falta un registro, la causa más probable es la asignación del proyecto",
                "Si un proyecto cambió de PM, los registros viejos siguen perteneciendo al alcance del PM anterior",
                "El reporteo entre proyectos (cuando se necesita) pasa por Admin",
            ]},
            {"type": "why", "text": "La visibilidad por alcance mantiene la pantalla de inicio de cada supervisor enfocada en el trabajo que de verdad le toca. No es una pared de seguridad — es un filtro de ruido."},
        ],
    },
    "pm-coordination": {
        "title_es": "PM · Coordinación entre Cuadrillas y Oficios",
        "summary_es": "Cómo los PMs usan la plataforma para mantener varias cuadrillas alineadas.",
        "body_es": [
            {"type": "p", "text": "Los proyectos con varias cuadrillas viven o mueren por coordinación. La plataforma no hace la coordinación — la hacen los humanos — pero la plataforma crea el registro compartido que mantiene a cada cuadrilla trabajando con los mismos hechos."},
            {"type": "bullets", "items": [
                "Los reportes diarios de varias cuadrillas cuentan una sola historia del proyecto",
                "El coaching / amonestaciones de liderazgo de campo expone la fricción a tiempo",
                "Las asignaciones de equipo por cuadrilla son visibles a través del proyecto",
                "La escalación de incidentes involucra al PM el mismo día para eventos graves",
            ]},
            {"type": "why", "text": "Sin registros compartidos, la coordinación depende de la memoria y de llamadas — las dos fallan cuando algo se disputa. Con registros compartidos, la conversación arranca desde una base común."},
        ],
    },
    "hr-audit-trail": {
        "title_es": "RH · Registro de Auditoría — Qué Queda Registrado",
        "summary_es": "Qué acciones de RH se guardan y dónde encontrarlas.",
        "body_es": [
            {"type": "p", "text": "Cada acción de RH que toca una cuenta o un registro queda en el registro de auditoría. La bitácora contesta 'quién hizo qué, y cuándo' para acciones de relevancia para RH."},
            {"type": "bullets", "items": [
                "Eventos de inicio / cierre de sesión (con IP)",
                "Crear / deshabilitar cuenta / restablecer contraseña (acciones admin)",
                "Exportes CSV de Verificación de Tiempo",
                "Las vistas de registros entre portales NO se registran individualmente (el volumen es muy alto) — pero el alcance del acceso se aplica del lado del servidor",
            ]},
            {"type": "p", "text": "Los admins pueden revisar la bitácora completa en Admin → Registro de Auditoría. Los usuarios de RH ven su propio historial de acciones a través de las superficies de revisión de RH."},
            {"type": "why", "text": "El registro de auditoría es un detector de regresión. Si un registro se ve mal, la bitácora muestra si siempre estuvo mal o si alguien lo cambió."},
        ],
    },
    "dispatch-accuracy-why": {
        "title_es": "Despacho · Por Qué la Exactitud Importa",
        "summary_es": "Cada reporte aguas abajo depende de que el registro de despacho esté bien.",
        "body_es": [
            {"type": "p", "text": "Despacho está aguas arriba de todo: reportes de utilización del proyecto, la vista del Taller de quién tiene qué, la lista de activos disponibles del campo, las decisiones ejecutivas de flota. Cuando Despacho está mal, cada vista aguas abajo está mal — pero la gente que depende de ellas a menudo no lo sabe."},
            {"type": "bullets", "items": [
                "El campo ve una lista de 'disponibles' vieja → vueltas desperdiciadas",
                "El Taller programa servicio en activos que se movieron → tiempo de técnico desperdiciado",
                "Los PMs ven utilización equivocada → estimaciones de costo de proyecto equivocadas",
                "Los ejecutivos ven utilización de flota equivocada → decisiones de compra / venta equivocadas",
            ]},
            {"type": "why", "text": "La exactitud de Despacho no es preocupación solo del equipo de Despacho — es preocupación operacional de cada equipo aguas abajo. Trate cada entrada como el reporte en el que se va a citar, porque sí se va a citar."},
        ],
    },
    "connect-incident-to-audit": {
        "title_es": "Cómo un Incidente se Vuelve una Acción Correctiva",
        "summary_es": "Incidente de campo → Revisión de Seguridad → Acción Correctiva → Registro de auditoría.",
        "body_es": [
            {"type": "p", "text": "Un incidente enviado en el campo no termina con el envío. Abre una cadena de revisión que puede producir una Acción Correctiva — el registro de seguimiento que prueba que el problema realmente se atendió."},
            {"type": "steps", "items": [
                "Incidente enviado (campo, supervisor o Seguridad)",
                "Seguridad revisa el reporte y decide si se necesita una Acción Correctiva",
                "Se abre la Acción Correctiva con un dueño y un plazo",
                "El dueño completa la acción y registra qué cambió",
                "Seguridad cierra la acción — el registro de auditoría ahora muestra el ciclo de vida completo",
            ]},
            {"type": "why", "text": "La Acción Correctiva es lo que convierte un incidente de un registro de un problema en un registro de una solución. Sin ella, el mismo casi-incidente puede volver a pasar y nadie puede decir qué se hizo al respecto la vez anterior."},
        ],
    },
    "connect-admin-controls": {
        "title_es": "Cómo los Controles de Admin Protegen Cada Portal",
        "summary_es": "RBAC, auditoría, límites de sesión — qué hereda cada portal.",
        "body_es": [
            {"type": "p", "text": "Cada portal se beneficia de controles de nivel admin que no ve directamente. Entender la postura heredada ayuda al diseñar funciones nuevas o al decidir si una petición requiere step-up."},
            {"type": "bullets", "items": [
                "Cada portal hereda el registro de auditoría (inicio de sesión, cierre, acciones sensibles)",
                "Cada portal hereda los timeouts de sesión (específicos por nivel)",
                "Cada portal hereda los límites de tasa en superficies POST públicas",
                "Cada portal hereda RBAC por alcance en la puerta de la API",
                "La autenticación step-up (controlada por env) aplica solo a mutaciones admin-sensibles",
            ]},
            {"type": "why", "text": "Los controles de admin no son protecciones solo de admin — son protecciones a nivel plataforma que hacen que cada portal sea más seguro. Los portales no tienen que implementarlas por su cuenta; admin es dueño de la postura para todos."},
        ],
    },
    "shop-operator-responsibilities": {
        "title_es": "Taller · Responsabilidades del Operador",
        "summary_es": "Qué le toca al operador — y qué le toca al Taller.",
        "body_es": [
            {"type": "p", "text": "El operador y el Taller se reparten la responsabilidad del equipo. Entender el reparto previene el conflicto más común ('el Taller lo debió haber detectado' / 'el operador lo debió haber marcado')."},
            {"type": "bullets", "items": [
                "Al operador le toca: Pre-Op diario, revisiones en turno, reporte inmediato de daño / falla, nota de condición al fin de turno",
                "Al Taller le toca: servicio programado, reparación después de una falla documentada, condición de la flota en el tiempo, firma de regreso a servicio",
                "Compartido: descubrimiento de daño (quien lo encuentre lo documenta), cumplimiento de capacitación (registro del operador pero el Taller verifica antes de entregar)",
            ]},
            {"type": "why", "text": "Una división clara previene la grieta de 'alguien más se suponía que iba a atrapar eso'. Las dos mitades pesan — el sistema solo sirve cuando ambos lados son dueños de su mitad."},
        ],
    },
    "hr-cross-portal-reads": {
        "title_es": "RH · Lo que Puede Leer en Otros Portales",
        "summary_es": "Alcance de lectura entre portales de RH — qué es y qué no es visible.",
        "body_es": [
            {"type": "p", "text": "RH tiene acceso de lectura a portales adyacentes cuando los datos se atan a un empleado. Esa visibilidad es intencionalmente estrecha — RH revisa, no edita otros portales."},
            {"type": "bullets", "items": [
                "Registros de Seguridad (incidentes ligados a un empleado) — solo lectura",
                "Salida de Equipo / registros de capacitación — solo lectura",
                "Amonestaciones y coaching de Liderazgo de Campo — revisión solo lectura",
                "Verificación de Tiempo para cualquier proyecto donde el supervisor capture horas",
            ]},
            {"type": "warn", "text": "RH NO ve los registros de auditoría de admin, la salud del sistema, los respaldos ni los restablecimientos de contraseña de otros usuarios de RH. Eso se queda con Admin."},
            {"type": "why", "text": "Las lecturas entre portales le dejan a RH construir una imagen completa de un empleado sin necesitar escalación a admin para trabajo de revisión rutinario. Las escrituras se quedan amarradas al portal de origen — eso preserva la cadena de custodia."},
        ],
    },
    "dispatch-field-coordination": {
        "title_es": "Despacho · Cómo Despacho y Campo se Mantienen Sincronizados",
        "summary_es": "El traspaso que previene 'el activo no está donde dice el sistema'.",
        "body_es": [
            {"type": "p", "text": "Despacho ve la vista del sistema; el campo ve la vista física. Cuando se desfasan, el campo desperdicia las horas de la mañana buscando equipo. El traspaso es lo que mantiene las dos vistas alineadas."},
            {"type": "bullets", "items": [
                "La salida de equipo de liderazgo de campo registra QUIÉN tiene QUÉ (nivel operador)",
                "Despacho registra DÓNDE está ese QUÉ (nivel proyecto)",
                "Las dos se actualizan en eventos de movimiento; las dos llegan al PM",
            ]},
            {"type": "why", "text": "Despacho solo no puede ver la realidad nivel operador; el campo solo no puede ver la asignación nivel proyecto. El traspaso es el único lugar donde las dos vistas se encuentran."},
            {"type": "tip", "text": "Si un supervisor encuentra equipo en el campo que Despacho no muestra ahí, el supervisor registra la discrepancia — Despacho reconcilia, no discute. El registro vale más que la pregunta de quién tenía razón."},
        ],
    },
    "shop-downtime-logic": {
        "title_es": "Taller · Lógica de Tiempo Muerto y Escalación",
        "summary_es": "Cuándo el tiempo muerto se vuelve una escalación, no solo una reparación.",
        "body_es": [
            {"type": "p", "text": "No toda reparación es una escalación. Pero ciertos patrones de tiempo muerto sí lo son — y necesitan involucrar a Despacho, PM y a veces a Admin para que el campo no se entere de los huecos de disponibilidad el día que necesita el activo."},
            {"type": "bullets", "items": [
                "Rutinaria — reparación el mismo día o el siguiente, sin impacto al campo",
                "Significativa — reparación de varios días O activo crítico; Despacho debe saber",
                "Escalación — la reparación saca un activo crítico del proyecto; PM + Despacho + Admin se involucran",
                "Decisión de reemplazo — fallas repetidas o costo de reparación arriba del umbral; se requiere decisión de Admin",
            ]},
            {"type": "why", "text": "El campo puede absorber una reparación rutinaria sin aviso. No puede absorber que un activo crítico de proyecto desaparezca sin coordinación. Las reglas de escalación no son burocracia — son cómo Despacho / PM / Admin obtienen el contexto que necesitan para mantener al campo trabajando."},
        ],
    },
    "pm-cross-project-visibility": {
        "title_es": "PM · Lo que Puede y No Puede Ver",
        "summary_es": "Asignación de proyecto, filtrado por alcance, cuándo preguntarle a Admin.",
        "body_es": [
            {"type": "p", "text": "La visibilidad del PM está limitada por proyecto. Los registros ligados a proyectos que usted maneja son totalmente visibles; los registros de otros proyectos están intencionalmente ocultos. No es una limitación de permisos — es un filtro de ruido."},
            {"type": "bullets", "items": [
                "Visible: reportes diarios, inspecciones, JHAs, incidentes, registros de Liderazgo de Campo de sus proyectos",
                "Visible: asignaciones de equipo en sus proyectos",
                "Oculto: cualquier registro ligado a un proyecto que no maneja",
                "Reporteo entre proyectos: enrutado por Admin",
            ]},
            {"type": "warn", "text": "Si un registro que espera ver está faltando, primero revise la asignación del proyecto. La causa más común es el proyecto equivocado en el registro original — corríjalo en la fuente, no le dé la vuelta."},
            {"type": "why", "text": "La visibilidad por alcance mantiene la vista de cada PM enfocada en el trabajo que de verdad le toca. Admin ve todo; por eso las preguntas entre proyectos se enrutan por Admin, no por compartir datos PM-a-PM."},
        ],
    },
    "connect-pm-field-review": {
        "title_es": "Cómo los Reportes de Campo Llegan a la Revisión del PM",
        "summary_es": "Envío de campo → alcance del PM → revisión → acción.",
        "body_es": [
            {"type": "p", "text": "Un reporte de campo no solo se queda en el almacén de registros del campo. Sale automáticamente a los PMs asignados al proyecto, que lo usan como su sistema de alerta temprana."},
            {"type": "steps", "items": [
                "El supervisor envía un reporte diario / inspección / incidente con el proyecto correcto",
                "El registro entra a la vista por alcance del proyecto del PM al siguiente cargado de página",
                "El PM revisa en su cadencia (diaria / semanal / mensual)",
                "Los problemas se vuelven seguimientos; los temas graves escalan el mismo día",
                "El registro de auditoría guarda quién revisó qué, cuándo",
            ]},
            {"type": "why", "text": "Sin este ciclo, el PM solo se entera de los problemas del campo cuando escalan de palabra. Con él, el PM tiene la oportunidad de atrapar un problema chico mientras todavía está chico — que también es cuando es más barato arreglarlo."},
            {"type": "tip", "text": "Proyecto equivocado en el registro de campo = el registro nunca llega a la revisión del PM. De todos los problemas de calidad de datos del sistema, este es el de mayor costo si se deja sin corregir."},
        ],
    },
    "admin-governance-why": {
        "title_es": "Admin · Por Qué Existen los Controles y Restricciones",
        "summary_es": "El razonamiento detrás de RBAC, auditoría, lockouts y límites de tasa.",
        "body_es": [
            {"type": "p", "text": "Los controles de admin no son un impuesto a la velocidad — son cómo la plataforma sobrevive el día eventual en que algo sale mal. Cada control contesta a un riesgo real específico."},
            {"type": "bullets", "items": [
                "RBAC: previene que el error de un portal se extienda a otros portales",
                "Registro de auditoría: contesta 'quién hizo qué' cuando un registro se disputa",
                "Timeouts de sesión: limitan el costo de un dispositivo perdido / sin atender",
                "Límites de tasa: previenen que un solo cliente con bugs (o un atacante) sature la API",
                "Respaldo + simulacro de restauración: aseguran que la recuperación es posible cuando se necesita",
                "Step-up auth (cuando está habilitado): reconfirma la identidad para acciones sensibles",
            ]},
            {"type": "why", "text": "Cada control es chico; juntos forman la diferencia entre una plataforma que aguanta bajo fricción del mundo real y una que falla en silencio cuando importa. Ninguno es paranoia — todos son respuestas a eventos que les han pasado a otras plataformas."},
        ],
    },
    "safety-escalation-chain": {
        "title_es": "Seguridad · Cadena de Escalación y Quién Ve Qué",
        "summary_es": "Campo → Seguridad → Admin → Aseguradora: cuándo se involucra cada paso.",
        "body_es": [
            {"type": "p", "text": "Diferentes severidades disparan respuestas diferentes. Saber qué nivel se involucra cuándo previene tanto la sobre-escalación (todos llamados por una cortada) como la sub-escalación (admin se entera de un evento serio por rumor)."},
            {"type": "bullets", "items": [
                "Rutinaria — Seguridad revisa y cierra por la cadencia normal",
                "Significativa — Seguridad + el PM asignado son notificados; Acción Correctiva probable",
                "Grave (lesión, daño a propiedad, exposición pública) — Admin + Seguridad + PM el mismo día",
                "Catastrófica — Admin + involucramiento de aseguradora; postura de retención legal",
            ]},
            {"type": "warn", "text": "Si tiene duda, escale. El costo de sobre-involucrar a Admin una vez es mucho menor que el costo de sub-involucrarlos cuando sí importaba."},
            {"type": "why", "text": "La cadena protege a todos: el lesionado tiene respuesta rápida, el supervisor no se queda solo con una decisión seria y Admin tiene el contexto para involucrar a aseguradora / legal cuando de verdad se necesita."},
        ],
    },
    "connect-field-to-payroll": {
        "title_es": "Cómo los Reportes de Campo se Vuelven Nómina",
        "summary_es": "Reporte Diario → Verificación de Tiempo de RH → cruce con nómina.",
        "body_es": [
            {"type": "p", "text": "Un reporte diario no se queda en un solo portal. Una vez enviado, las entradas de tiempo alimentan la Verificación de Tiempo de RH, donde se resumen semanalmente en Regular / Tiempo Extra / Lunch y se cruzan contra nómina."},
            {"type": "steps", "items": [
                "El supervisor envía un Reporte Diario desde el campo",
                "Las horas por empleado aterrizan en la Verificación de Tiempo de RH bajo el período de pago correspondiente",
                "RH resume la semana y marca discrepancias",
                "Los totales verificados apoyan el cruce con nómina",
                "El registro de auditoría preserva cada paso — entrada del supervisor, revisión de RH, exporte",
            ]},
            {"type": "why", "text": "Entender esta conexión es lo que hace que un supervisor de campo sea cuidadoso con las horas y los proyectos en el reporte diario. El número de un cheque dos semanas después arrancó su vida en su teléfono en la obra."},
            {"type": "tip", "text": "Proyecto equivocado en el reporte diario = proyecto equivocado en el código de costo del cheque. Es el error más barato de cometer y el más caro de desenredar."},
        ],
    },
    "connect-equipment-lifecycle": {
        "title_es": "Ciclo de Vida del Equipo — de Punta a Punta",
        "summary_es": "Entrega → Uso → Daño → Devolución → Desvínculo.",
        "body_es": [
            {"type": "p", "text": "La vida de un activo en el sistema abarca varios portales. Conocer el ciclo de vida ayuda a cada portal a reconocer su pieza — y ayuda a todos a detectar dónde falta un registro."},
            {"type": "steps", "items": [
                "Activo creado / recibido — el Taller o Admin registra el maestro",
                "Entregado a un empleado — forma de Salida de Equipo de Liderazgo de Campo o Formas de Seguridad",
                "En uso — Pre-Op diario, revisiones en turno, nota de condición al fin de turno",
                "Daño / falla (si la hay) — el operador o el Taller lo registra",
                "Devuelto — el Taller inspecciona, actualiza el estado, ata al registro de salida",
                "Desvínculo (cuando aplica) — RH confirma que cada activo asignado regresó, se transfirió o se dio de baja",
                "Retirado / vendido — Admin registra la disposición final",
            ]},
            {"type": "why", "text": "Cada hueco en esta cadena es una disputa futura esperando pasar — '¿esto se devolvió?', '¿quién lo dañó?', '¿por qué la lista de RH no coincide con la del Taller?'. La vista de ciclo de vida es la hoja de respuestas."},
        ],
    },
    "safety-photo-quality": {
        "title_es": "Seguridad · Estándares de Calidad de Foto y Documentación",
        "summary_es": "Qué hace que una fotografía sea evidencia en lugar de ruido.",
        "body_es": [
            {"type": "p", "text": "Una foto convierte una nota en evidencia. Una mala foto la regresa a una nota. La diferencia es qué está en el cuadro, qué está en foco y si alguien seis meses después puede decir qué está viendo."},
            {"type": "bullets", "items": [
                "Capture contexto primero (toma amplia mostrando los alrededores)",
                "Después capture el detalle (acercamiento al artículo / daño / peligro específico)",
                "Incluya una referencia de tamaño donde importe (una mano, una cinta, cualquier cosa conocida)",
                "Evite el borroso — vuelva a tomar si el movimiento o el enfoque está mal",
                "Tome más de las que piensa que necesita; borrar es barato, regresar a la escena no",
            ]},
            {"type": "why", "text": "Las fotos son lo primero a lo que llegan los revisores. Sobreviven a la memoria, los cambios de personal y las disputas. Un set claro de fotos vale más que una descripción larga por escrito."},
            {"type": "mistakes", "items": [
                "Una sola foto de una escena compleja",
                "Acercamiento sin contexto (¿dónde está esto?)",
                "Toma amplia sin detalle (¿cuál es el problema?)",
                "Olvidar fotografiar los alrededores (testigos, equipo, condiciones)",
            ]},
        ],
    },
    "safety-near-miss-importance": {
        "title_es": "Seguridad · Por Qué los Casi-Incidentes son las Lecciones Más Baratas",
        "summary_es": "Qué es un casi-incidente, por qué importa más de lo que la gente piensa.",
        "body_es": [
            {"type": "p", "text": "Un casi-incidente es un evento que pudo haber causado daño pero no lo hizo — el tropiezo que no se volvió caída, el golpe que no conectó, la cadena suelta que se atrapó a tiempo. La mayoría de las empresas sub-documentan los casi-incidentes porque 'no pasó nada'. Eso es exactamente al revés."},
            {"type": "why", "text": "Los casi-incidentes son las lecciones más baratas posibles. Le dicen del riesgo sin el costo de una lesión. Un campo que documenta bien los casi-incidentes produce menos incidentes reales con el tiempo — porque los factores contribuyentes se atraparon temprano."},
            {"type": "bullets", "items": [
                "Documente con hechos — qué casi pasó, qué lo detuvo",
                "Fotografíe el escenario si todavía existe",
                "Envíe por la misma forma de incidente (marque como casi-incidente)",
                "Seguridad revisa como cualquier otro incidente",
            ]},
            {"type": "tip", "text": "Las cuadrillas que envían casi-incidentes no son cuadrillas malas — son cuadrillas honestas. Las cuadrillas que envían cero casi-incidentes durante un año no están más seguras; están más calladas. Trate el volumen de casi-incidentes como una señal, no como un estigma."},
        ],
    },
    "connect-shop-to-dispatch": {
        "title_es": "Cómo el Taller y Despacho se Mantienen Sincronizados",
        "summary_es": "Pre-Op fallido → Taller → retención de Despacho → disponibilidad en campo.",
        "body_es": [
            {"type": "p", "text": "La disponibilidad del equipo le concierne a Despacho. La salud del equipo le concierne al Taller. Tienen que estar sincronizados o al campo le entregan activos que no deberían estar en servicio — o no puede encontrar activos que sí están."},
            {"type": "steps", "items": [
                "Una falla de Pre-Op / daño / servicio programado saca un activo de servicio",
                "El Taller registra el estado — esa actualización fluye a la vista de disponibilidad de Despacho",
                "Despacho retiene el activo; deja de aparecer en las listas de asignación de campo",
                "El Taller completa el trabajo y firma — Despacho recoge el nuevo estado",
                "El activo regresa a la rotación de campo — con un registro limpio del hueco",
            ]},
            {"type": "why", "text": "Cuando este ciclo está limpio, el campo ve solo los activos que de verdad están listos. Cuando se rompe, los supervisores desperdician una mañana persiguiendo equipo que no está donde dice el sistema. La integridad de cada lista de activos aguas abajo depende de este ciclo."},
            {"type": "tip", "text": "Si Despacho ve un activo listado como disponible pero el Taller lo tiene en la mesa, es un bug de sincronización — usualmente una actualización de estado faltante. Márquelo; no le dé la vuelta."},
        ],
    },
}
