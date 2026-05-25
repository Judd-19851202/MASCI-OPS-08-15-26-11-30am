"""guidance.translations_es — Spanish translations for guidance articles.

Pass 3 of the Operational Inventory initiative.

Architecture
------------
English content lives in ``guidance/content.py`` and remains canonical.
This module provides Spanish translations as a side-companion map:

    TRANSLATIONS_ES = {
        "<article_id>": {
            "title_es":   "Título en español",
            "summary_es": "Resumen en español",
            "body_es":    [<list of block dicts, same shape as body>],
        },
        ...
    }

At import time, ``guidance.__init__`` merges each entry into the
matching article dict in ``_ARTICLES``. Missing translations →
graceful fallback to English (no warning, no 404).

Translation policy
------------------
1. English is the source of truth. Always.
2. Article IDs, slugs, scopes, tags stay English.
3. Block ``type`` values stay English; only the human-readable strings
   (``text``, ``items``) get translated.
4. Translations target field-crew comprehension, not literal accuracy.
5. OSHA citations, equipment model numbers, and acronyms stay English
   inside the Spanish text (industry convention; matches the existing
   ``/app/frontend/src/lib/i18n.js`` dictionary).

Tier 1 — Public scope articles (this file)
------------------------------------------
The 17 articles tagged ``public`` are the highest operational priority
because mixed-language field crews read them without logging in.
"""
from __future__ import annotations

# Tier 1 — Public scope (17 articles)
TRANSLATIONS_ES: dict[str, dict] = {
    # ── role-new-employee ────────────────────────────────────────────
    "role-new-employee": {
        "title_es": "Empleado Nuevo",
        "summary_es": "Lo básico de la primera semana — sin importar el rol.",
        "body_es": [
            {"type": "p", "text": "Bienvenido a MASCI. Esto es lo que pasa la primera semana sin importar el oficio."},
            {"type": "steps", "items": [
                "Reciba sus credenciales de inicio de sesión de RH (correo y contraseña).",
                "Asista a la orientación de seguridad antes de pisar el sitio de trabajo.",
                "Reciba su EPP — botas, casco, chaleco, gafas, audífonos.",
                "Conozca a su supervisor y al capataz de su cuadrilla.",
                "Aprenda a llenar Reportes Diarios y Pre-Op (si opera equipo).",
            ]},
            {"type": "why", "text": "La primera semana define cómo trabajará el resto del tiempo. Si algo no le quedó claro — pregunte. Es más fácil aprender bien la primera vez que corregir después."},
            {"type": "tip", "text": "Guarde el número de su supervisor en su teléfono el primer día."},
        ],
    },

    # ── Pass 4 — Field Leadership Operational Identity (public articles) ──
    # iter317-B · two-doors disambiguation added to all three articles
    # so EN/ES parity reflects the live per-user portal alongside the
    # legacy shared-password gate.
    "onboard-leadership-first-week": {
        "title_es": "Liderazgo de Campo — Primera Semana",
        "summary_es": "Qué hace un nuevo Superintendente o Capataz en su primera semana en MASCI.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido al Liderazgo de Campo. Este portal es la superficie de operaciones diarias "
                "para Superintendentes, Capataces, Líderes de Campo y Supervisión de Operaciones. "
                "Esto es lo que debe hacer su primera semana."},
            {"type": "tip", "text":
                "¿Cuál puerta uso? Existen dos puertas válidas. La "
                "operacional — donde viven sus Reportes Diarios, "
                "amonestaciones, salidas de equipo y evaluaciones "
                "de cuadrilla — es /field-leadership/portal/login "
                "(su correo de la empresa + contraseña individual, "
                "emitida por RH o Admin). La puerta legacy con "
                "contraseña compartida en /field-leadership/login "
                "es solo lectura para documentos de cuadrilla. Si "
                "RH o Admin le dio una cuenta por usuario, esa es "
                "la puerta que usa día a día."},
            {"type": "steps", "items": [
                "Día 1 — Averigüe qué puerta le configuró RH/Admin. Si tiene cuenta por usuario, inicie sesión en /field-leadership/portal/login con su correo de empresa y la contraseña temporal que le dieron; el portal le obliga a cambiarla en el primer inicio. Si solo tiene la contraseña compartida de la cuadrilla, la oficina puede emitirle una cuenta por usuario en pocos minutos.",
                "Día 1 — Lea el artículo '¿Qué hace el Liderazgo de Campo?' (enlace en la parte inferior de la página de inicio de sesión).",
                "Día 2 — Envíe su primer Reporte Diario en un trabajo real (no de prueba). Fotos. Cuadrillas. Horas. Condiciones.",
                "Día 2-3 — Recorra el ciclo completo de un Pre-Op de equipo desde el operador → taller → de vuelta al campo. Entienda qué pasa cuando usted firma.",
                "Día 3-4 — Entregue una pieza de EPP / equipo usando Equipment Checkout. El registro es la prueba.",
                "Día 4-5 — Dirija una Reunión de Seguridad y envíe el formulario de asistencia.",
                "Fin de Semana 1 — Si tuvo cualquier evento de documentación (amonestación verbal, escrita, reconocimiento), regístrelo el mismo día. La documentación tardía es documentación débil.",
            ]},
            {"type": "why", "text":
                "El Liderazgo de Campo es el portal más conectado operacionalmente en MASCI — sus "
                "Reportes Diarios alimentan la nómina (RH), sus amonestaciones alimentan la "
                "rendición de cuentas (RH + Seguridad), sus salidas de equipo alimentan Taller + "
                "Despacho, y sus notas de proyecto alimentan al PM. La primera semana se trata "
                "de entender que todo lo que documenta afecta a otro equipo. Si toma el ritmo "
                "correcto, el resto de la plataforma trabaja a su favor."},
            {"type": "tip", "text":
                "Agregue el portal por usuario a la pantalla de inicio de su teléfono el Día 1. "
                "Casi toda tarea de Liderazgo de Campo se hace en un teléfono en el sitio — "
                "instalar el atajo temprano le ahorra 5-10 toques por envío el resto de su "
                "carrera aquí."},
            {"type": "warn", "text":
                "Su contraseña del portal por usuario es suya — no "
                "de la cuadrilla. Cada acción que envía queda "
                "firmada con su nombre en el rastro de auditoría. "
                "No le mande la contraseña por mensaje a un "
                "capataz ni la comparta 'nada más para que jale un "
                "reporte.' Si un compañero necesita acceso, eso es "
                "una conversación de RH/Admin para emitir una "
                "cuenta, no un atajo de compartir contraseña."},
            {"type": "next", "items": [
                "Marque este artículo — también es la respuesta a 'qué hago después' durante el primer mes",
                "Lea 'Enviando un Reporte Diario Defendible' — el más referenciado de todos",
                "Lea 'Cuentas del Portal de Liderazgo de Campo' (resumen de identidad por usuario)",
                "Hable con su PM sobre los proyectos a los que será asignado",
            ]},
        ],
    },

    "tshoot-leadership-login": {
        "title_es": "No puedo iniciar sesión en Liderazgo de Campo",
        "summary_es": "Soluciones rápidas para las dos puertas de Liderazgo de Campo — el portal por usuario y la puerta legacy con contraseña compartida.",
        "body_es": [
            {"type": "p", "text":
                "Existen dos puertas de Liderazgo de Campo y "
                "necesitan cosas distintas al iniciar sesión. "
                "Averigüe en cuál está y siga la lista que "
                "corresponde."},
            {"type": "tip", "text":
                "¿En cuál puerta estoy? Si el formulario le pide un "
                "CORREO y una contraseña, está en el portal por "
                "usuario (/field-leadership/portal/login). Si pide "
                "solo una contraseña, está en la puerta legacy con "
                "contraseña compartida (/field-leadership/login)."},
            {"type": "p", "text":
                "Portal por usuario — /field-leadership/portal/login "
                "(su correo de empresa + su contraseña individual):"},
            {"type": "steps", "items": [
                "Confirme que está en /field-leadership/portal/login (no /field-leadership/login).",
                "Use el correo de empresa que RH o Admin le asignó — no el de un compañero, no un correo personal.",
                "Si le dieron una contraseña temporal y nunca inició sesión, el portal le obligará a cambiarla en el primer inicio.",
                "¿Olvidó la contraseña? Use el enlace de Olvidé Mi Contraseña en la página de inicio, o pida a RH/Admin que la reinicie. Ambos caminos emiten una nueva contraseña temporal e invalidan la anterior de inmediato.",
                "¿Sigue rechazado? Pida a RH/Admin que confirme que su cuenta está activa. Las cuentas desactivadas no pueden iniciar sesión.",
            ]},
            {"type": "p", "text":
                "Puerta Legacy con Contraseña Compartida — "
                "/field-leadership/login (contraseña de cuadrilla "
                "para documentos de solo lectura solamente):"},
            {"type": "steps", "items": [
                "Confirme que está en /field-leadership/login (la puerta con contraseña compartida).",
                "Verifique la ortografía y el estado de mayúsculas — la contraseña compartida distingue mayúsculas.",
                "Si ya tiene un token Admin o PM (inició sesión en /admin/login o /pm/login antes en esta sesión), la puerta legacy los acepta automáticamente.",
                "Cierre la pestaña del navegador y vuelva a abrir si un token previo está interfiriendo.",
                "Pida la contraseña compartida actual a su supervisor directo o a la oficina si la rotaron.",
            ]},
            {"type": "why", "text":
                "Las dos puertas existen a propósito. El portal por "
                "usuario carga la rendición de cuentas operacional "
                "— cada acción queda firmada con su nombre. La "
                "puerta con contraseña compartida existe para "
                "acceso de solo lectura a documentos de cuadrilla "
                "donde no se necesita identidad individual. La "
                "mayor parte del trabajo operacional va en la "
                "puerta por usuario."},
            {"type": "warn", "text":
                "NO escriba la contraseña compartida de cuadrilla "
                "en el portal por usuario (ni al revés). Puerta "
                "equivocada + contraseña equivocada es lo que "
                "causa la mayoría de los fallos repetidos. Vea el "
                "formulario primero; si pide correo, necesita sus "
                "credenciales por usuario."},
            {"type": "tip", "text":
                "Una vez que inicie sesión en cualquiera de las "
                "dos puertas, su navegador guarda un token de "
                "sesión. No necesita volver a escribir las "
                "credenciales ese mismo turno a menos que cierre "
                "la pestaña o expire la sesión."},
        ],
    },

    "portal-leadership-identity": {
        "title_es": "Portal de Liderazgo de Campo — Resumen",
        "summary_es": "Para qué es el Liderazgo de Campo, quién lo usa, y cuál de las dos puertas usar.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de Liderazgo de Campo es la superficie de operaciones diarias para "
                "Superintendentes, Capataces, Líderes de Campo y Supervisión de Operaciones — "
                "la gente que dirige las cuadrillas en el campo."},
            {"type": "p", "text":
                "Quién lo usa: Superintendentes, Capataces, Truck "
                "Bosses, Working Supervisors, Field Supervisors. La "
                "Supervisión de Operaciones (RH/Admin) emite y "
                "gestiona las cuentas pero trabaja dentro de sus "
                "propios portales."},
            {"type": "tip", "text":
                "¿Cuál puerta uso? Existen dos puertas válidas. "
                "(1) /field-leadership/portal/login — cuentas por "
                "usuario (su correo de empresa + contraseña "
                "individual). Esta es la puerta operacional; todo "
                "lo que envía queda firmado con su nombre. "
                "(2) /field-leadership/login — puerta legacy con "
                "contraseña compartida para documentos de cuadrilla "
                "de solo lectura. Las dos funcionan; hacen trabajos "
                "diferentes."},
            {"type": "p", "text":
                "Cómo conseguir una cuenta por usuario: RH o Admin "
                "emite cuentas del Portal de Liderazgo de Campo. "
                "Recibe un correo de empresa y una contraseña "
                "temporal; el portal le obliga a cambiarla en el "
                "primer inicio de sesión. Después de eso, su correo "
                "y su contraseña individual le hacen entrar."},
            {"type": "warn", "text":
                "La capacitación operacional de Liderazgo de Campo (procedimientos, flujos, "
                "SOPs internos) está restringida a usuarios autenticados de liderazgo. El "
                "contenido a nivel de flujo no es visible para usuarios anónimos."},
            {"type": "next", "items": [
                "Lea 'Cuentas del Portal de Liderazgo de Campo' para el recorrido completo de identidad por usuario",
                "Si no puede iniciar sesión — lea 'No puedo iniciar sesión en Liderazgo de Campo' (público)",
            ]},
        ],
    },

    # iter317-B · NEW per-user FL Portal accounts article (ES parity).
    "portal-field-leadership-portal-accounts": {
        "title_es": "Cuentas del Portal de Liderazgo de Campo (por usuario)",
        "summary_es": "Cuentas por usuario del Portal de Liderazgo de Campo — qué son, quién las emite, y cuándo aplica todavía la puerta legacy con contraseña compartida.",
        "body_es": [
            {"type": "p", "text":
                "Una cuenta del Portal de Liderazgo de Campo es su "
                "identidad operacional individual dentro de MASCI. "
                "Es un correo de empresa + una contraseña "
                "individual — no un código compartido de cuadrilla. "
                "Cada Reporte Diario, amonestación, salida de "
                "equipo y evaluación de cuadrilla que envíe queda "
                "firmado con su nombre en el rastro de auditoría."},
            {"type": "tip", "text":
                "¿Cuál puerta uso? Existen dos puertas válidas. El "
                "portal por usuario en /field-leadership/portal/"
                "login es la puerta operacional — sus flujos día a "
                "día viven ahí. La puerta legacy con contraseña "
                "compartida en /field-leadership/login sigue "
                "existiendo para documentos de cuadrilla de solo "
                "lectura; no desbloquea flujos operacionales. La "
                "mayor parte del trabajo de liderazgo va en la "
                "puerta por usuario."},
            {"type": "p", "text":
                "Quién emite las cuentas: RH o Admin. Le crean la "
                "cuenta, ponen una contraseña temporal, y se la "
                "entregan por el canal que RH usa para "
                "credenciales. El portal le obliga a cambiar la "
                "contraseña temporal en el primer inicio de sesión "
                "— ese es el traspaso de 'emitida' a 'en uso.'"},
            {"type": "p", "text":
                "Quién recibe cuentas: Superintendentes, Capataces, "
                "Truck Bosses, Working Supervisors, Field "
                "Supervisors. Las cuentas se emiten a personas que "
                "realmente las necesitan — no cuentas 'por si "
                "acaso', no cuentas de capacitación que nunca se "
                "limpian."},
            {"type": "p", "text":
                "Reinicios de contraseña: RH o Admin reinicia la "
                "contraseña si la olvida, o puede usar el enlace "
                "Olvidé Mi Contraseña en la página de inicio. "
                "Ambos caminos emiten una contraseña temporal "
                "nueva e invalidan la anterior de inmediato. Las "
                "sesiones viejas mueren en el mismo momento."},
            {"type": "why", "text":
                "Las cuentas por usuario existen porque las "
                "acciones operacionales necesitan rendición de "
                "cuentas operacional. Un Reporte Diario firmado "
                "carga su nombre a nómina y a la revisión de "
                "Seguridad; una amonestación carga su nombre al "
                "registro del empleado que mantiene RH. Una "
                "contraseña compartida de cuadrilla no puede "
                "hacer eso — todos los que entran se ven iguales. "
                "El portal por usuario es como la plataforma "
                "conecta lo que pasa en el campo con quién "
                "realmente lo hizo."},
            {"type": "warn", "text":
                "Su contraseña es suya — no de la cuadrilla. No la "
                "mande por mensaje a un capataz, no la escriba en "
                "un portapapeles, no la comparta 'nada más para "
                "que jale un reporte.' Cada acción firmada con su "
                "nombre es suya operacionalmente — incluyendo las "
                "que no hizo porque alguien le pidió prestado su "
                "inicio. Si un compañero necesita acceso, eso es "
                "una conversación de RH/Admin para emitir una "
                "cuenta."},
            {"type": "p", "text":
                "¿Cuándo aplica todavía la puerta legacy con "
                "contraseña compartida? Acceso de solo lectura a "
                "documentos de cuadrilla en /field-leadership/"
                "login — planos, juegos de planos y documentos "
                "similares que toda la cuadrilla necesita ver. La "
                "puerta compartida NO desbloquea Reportes Diarios, "
                "amonestaciones, salidas de equipo, evaluaciones "
                "ni ningún otro flujo por usuario. Las dos puertas "
                "son a propósito; hacen trabajos diferentes."},
            {"type": "next", "items": [
                "¿No tiene cuenta todavía? Pídala a RH o Admin — ellos emiten cuentas del Portal de Liderazgo de Campo.",
                "¿Le dieron una contraseña temporal? Inicie sesión en /field-leadership/portal/login y cámbiela en el primer inicio.",
                "¿No puede iniciar sesión? Lea 'No puedo iniciar sesión en Liderazgo de Campo' (público).",
                "¿Ya entró? Lea 'Liderazgo de Campo — Primera Semana' para el ritmo operacional.",
                "¿No está seguro de cuál puerta debería usar? Pregunte a RH o Admin. La respuesta es rápida (normalmente 'la cuenta que le configuramos'). No ande rebotando entre las dos puertas resolviendo solo.",
            ]},
        ],
    },

    # ═════════════════════════════════════════════════════════════════
    # iter317-C · ES parity for the 5 Driver Qualification articles.
    # ═════════════════════════════════════════════════════════════════
    "driver-cdl-vs-approved-company-driver": {
        "title_es": "Titular de CDL vs Chofer Aprobado por la Empresa",
        "summary_es": "Por qué MASCI rastrea las dos banderas por separado y por qué un CDL solo no sube a un chofer a un camión MASCI.",
        "body_es": [
            {"type": "p", "text":
                "Dos banderas. Dos decisiones separadas. CDL "
                "Holder significa que el estado licenció al chofer "
                "para operar un vehículo comercial en esa clase. "
                "Chofer Aprobado por la Empresa significa que la "
                "lista de seguros de MASCI, la revisión de MVR, el "
                "escaneo de tarjeta médica, los resultados del "
                "antidoping y la firma del supervisor están todos "
                "en archivo y el chofer está autorizado para "
                "operar un camión MASCI. Las dos respuestas casi "
                "nunca caen el mismo día."},
            {"type": "why", "text":
                "Confundirlas es el error de despacho más común en "
                "este espacio. 'Tiene CDL' no es lo mismo que "
                "'puede manejar hoy.' El tablero muestra las dos "
                "como columnas separadas para que la respuesta sea "
                "inequívoca antes de que el camión se mueva."},
            {"type": "bullets", "items": [
                "CDL Holder — licencia emitida por el estado, clase + endosos + restricciones en archivo",
                "Chofer Aprobado por la Empresa — proceso MASCI completo (seguros · MVR · médico · antidoping · supervisor)",
                "Driver Status — resumen operacional (Activo · Pendiente · Suspendido · Fuera de roster)",
                "Filtro Tanker-Capable — filtro operacional separado para cargas de dewatering",
            ]},
            {"type": "tip", "text":
                "Cuando un titular de CDL está sentado en "
                "pendiente-de-aprobación, casi siempre falta una "
                "pieza del proceso. Abra el panel del chofer; el "
                "campo faltante está ahí."},
            {"type": "warn", "text":
                "Nunca asigne una carga solo con CDL. El CDL "
                "satisface la ley estatal. La bandera de "
                "chofer-aprobado satisface el seguro y el proceso "
                "de MASCI. Las dos tienen que estar en verde "
                "antes del despacho."},
            {"type": "next", "items": [
                "Lea 'Cadencia y Vencimientos de la Tarjeta Médica' — la fecha que se vence más en silencio",
                "Lea 'Restricciones del Chofer y Escalación' — cuando las restricciones de licencia estatal cambian las opciones de despacho",
            ]},
        ],
    },

    "driver-medical-card-and-expirations": {
        "title_es": "Cadencia y Vencimientos de la Tarjeta Médica",
        "summary_es": "Tarjeta médica vencida significa que el chofer no opera un CMV ese día. Cómo el tablero muestra la fecha y cómo Seguridad, RH y Despacho escalan cuando se atrasa.",
        "body_es": [
            {"type": "p", "text":
                "La tarjeta médica del DOT (FMCSA 391.45) corre en "
                "su propio reloj — típicamente 24 meses, a veces "
                "más corto si el examinador marcó una condición. "
                "NO está atada al vencimiento del CDL. Un chofer "
                "puede tener tres años de CDL y una tarjeta médica "
                "que vence mañana. El día que la tarjeta vence, "
                "ese chofer legalmente no puede operar un CMV en "
                "comercio interestatal."},
            {"type": "why", "text":
                "Las dos fechas casi nunca empalman. Tratar la "
                "tarjeta médica y el CDL como una sola ventana de "
                "renovación es la forma más común de que una "
                "tarjeta venza en silencio. El tablero las muestra "
                "en dos columnas separadas por esa razón."},
            {"type": "tip", "text":
                "Use la vista de vencimiento a 60 días, no la del "
                "día del despacho. La mayoría de las renovaciones "
                "tardan 1–2 semanas una vez que el examen DOT está "
                "agendado — y agendar el examen toma su propio "
                "tiempo."},
            {"type": "warn", "text":
                "Tarjeta vencida = chofer no opera un CMV ese día. "
                "Notifique a Seguridad + RH + Despacho el mismo "
                "turno. El camino de renovación es un examinador "
                "médico certificado DOT, examen vigente, "
                "certificado en archivo con MASCI. Hasta que las "
                "tres cosas sean verdad, el chofer hace solo "
                "trabajo de apoyo — este no es un campo de "
                "'excepción por un día.'"},
            {"type": "next", "items": [
                "Si la tarjeta ya venció: saque al chofer de la ruta, agende el examen DOT, documente la conversación.",
                "Si faltan 30 días: pre-agende el examen ahora — las renovaciones toman tiempo.",
                "Lea 'Titular de CDL vs Chofer Aprobado por la Empresa' para ver cómo encaja la tarjeta médica en el proceso de aprobación.",
            ]},
        ],
    },

    "driver-tanker-and-endorsements": {
        "title_es": "Endoso de Tanque y Códigos de Endoso en MASCI",
        "summary_es": "Por qué el endoso de tanque (N) importa para el trabajo de dewatering de MASCI, y cómo las combinaciones X / H abren las rutas que el CDL básico no.",
        "body_es": [
            {"type": "p", "text":
                "El trabajo de dewatering de MASCI mueve volúmenes "
                "reales de líquido. El endoso de tanque (N) no es "
                "una casilla de papeleo — cubre la física de "
                "transportar un remolque líquido parcialmente "
                "cargado: oleaje, riesgo de volcadura en una "
                "curva, desvanecimiento de frenos en bajada. Los "
                "choferes sin N no corren cargas de dewatering. "
                "Punto."},
            {"type": "bullets", "items": [
                "N — Tanque. Requerido para cualquier carga líquida en bulto por encima del umbral; central a las rutas de dewatering de MASCI.",
                "H — Hazmat. Requerido para carga peligrosa con cartel. Lleva su propia revisión de TSA.",
                "X — Tanque Y Hazmat combinados. Requerido cuando líquido peligroso se mueve en un tanque — el único endoso individual que pasa la inspección.",
                "T — Remolques dobles/triples. Uso específico de equipo, menos común en MASCI.",
                "P — Pasajero. Rara vez aplicable al trabajo de MASCI.",
                "S — Autobús escolar. No aplica.",
            ]},
            {"type": "tip", "text":
                "Cuando despacho está emparejando un chofer con "
                "una carga líquida hazmat (camiones vac jalando "
                "agua contaminada es el caso común), vea la "
                "columna de endosos. La respuesta es: o está "
                "presente la X o la carga va a otro chofer."},
            {"type": "why", "text":
                "El tablero muestra los choferes capacitados para "
                "tanque como un filtro separado porque ese filtro "
                "realmente importa para la asignación. 'Tiene "
                "CDL' no alcanza; 'tiene N' es la respuesta "
                "operacional para dewatering."},
            {"type": "next", "items": [
                "Lea 'Restricciones del Chofer y Escalación' — las restricciones pueden descalificar choferes aunque los endosos se vean bien",
                "Lea 'Titular de CDL vs Chofer Aprobado por la Empresa' — los endosos viven dentro del CDL; la aprobación es un proceso separado",
            ]},
        ],
    },

    "driver-qualification-dashboard-understanding": {
        "title_es": "Leyendo el Tablero de Calificación del Chofer",
        "summary_es": "Qué significa cada columna del tablero de Calificación del Chofer, cuándo actuar y qué deliberadamente no hace.",
        "body_es": [
            {"type": "p", "text":
                "El tablero de Calificación del Chofer es el "
                "resumen operacional de cada campo relevante del "
                "registro del empleado — CDL holder, chofer "
                "aprobado, driver status, vencimiento del CDL, "
                "vencimiento de la tarjeta médica, endosos, "
                "restricciones, capacitado para tanque. Es la "
                "superficie que Despacho, Seguridad y RH miran "
                "antes de que una carga se mueva."},
            {"type": "bullets", "items": [
                "Nombre + ID del Empleado — ordenable, buscable",
                "CDL Holder — bandera sí/no del registro del empleado",
                "Chofer Aprobado por la Empresa — bandera sí/no, separada del CDL",
                "Driver Status — resumen operacional (Activo · Pendiente · Suspendido · Fuera de roster)",
                "Vencimiento del CDL — fecha de renovación estatal",
                "Vencimiento de Tarjeta Médica — cadencia FMCSA 391.45, INDEPENDIENTE del CDL",
                "Endosos — códigos N · H · X · T · P · S en el CDL",
                "Restricciones — códigos L · E · Z en el CDL que limitan el equipo",
            ]},
            {"type": "tip", "text":
                "Vistas de filtro — use los filtros de vencimiento "
                "a 30 / 60 / 90 días para planear con tiempo. Use "
                "el filtro de tanker-capable para emparejar cargas "
                "de dewatering. El tablero es una superficie de "
                "planeación, no una superficie de rechazo el día "
                "del despacho."},
            {"type": "warn", "text":
                "Lo que este tablero NO es. No es un sistema de "
                "despacho. No asigna cargas. No revoca "
                "automáticamente el estatus de chofer-aprobado "
                "cuando algo vence — esa decisión se queda humana "
                "a propósito. No hace cumplir la calificación al "
                "momento de la asignación. Construir cualquiera de "
                "esas cosas significaría que MASCI ahora es dueño "
                "de un producto de gestión de transporte, que es "
                "exactamente a lo que dijimos no."},
            {"type": "next", "items": [
                "Export Current View — exporta la lista filtrada como CSV para revisión offline",
                "Lea el artículo profundo de cada columna: CDL vs Aprobado · Tarjeta Médica · Tanque · Restricciones",
            ]},
        ],
    },

    "driver-restrictions-and-escalation": {
        "title_es": "Restricciones del Chofer y Escalación",
        "summary_es": "Qué significan los códigos de restricción del CDL para despacho en MASCI y cómo Seguridad + RH manejan a un chofer que llega a operar equipo que su CDL restringe.",
        "body_es": [
            {"type": "p", "text":
                "Los códigos de restricción del CDL son decisiones "
                "estatales de licencia — escritos en el CDL porque "
                "el chofer demostró habilidad en una clase más "
                "estrecha de equipo que la que la clase completa "
                "permite. MASCI no las anula con una firma de "
                "supervisor dispuesto; no son información "
                "opcional."},
            {"type": "bullets", "items": [
                "L — Sin CMV equipado con frenos de aire (la más consecuente operacionalmente en MASCI; la mayor parte de la flota pesada tiene frenos de aire)",
                "E — Sin transmisión manual (elimina asignaciones de palanca)",
                "Z — Sin sistema completo de frenos de aire (impacto operacional similar a L; trátese igual)",
                "K — Solo intraestatal (no puede cruzar líneas estatales)",
                "M — Sin vehículo de pasajeros Clase A",
                "N — Sin vehículo de pasajeros Clase A o B",
                "O — Sin tractor-remolque",
            ]},
            {"type": "tip", "text":
                "Despacho lee la columna de restricciones antes "
                "de asignar. Es el mismo flujo que leer endosos — "
                "la columna le dice qué puede y qué no puede "
                "operar legalmente el chofer, no lo que la "
                "oficina quisiera que pudiera."},
            {"type": "warn", "text":
                "Si un chofer se presenta a operar un equipo que "
                "su CDL restringe, eso es una parada de Seguridad "
                "— no una redirección de despacho. Sáquelo del "
                "camión, documente el desajuste, llévelo a "
                "RH/Seguridad el mismo día. Dos caminos hacia "
                "adelante: (1) el chofer pasa por el DMV a quitar "
                "la restricción, (2) despacho lo emparejea con un "
                "camión para el que realmente está licenciado. "
                "Los atajos no son un tercer camino."},
            {"type": "next", "items": [
                "Lea 'Titular de CDL vs Chofer Aprobado por la Empresa' — las restricciones viven dentro del CDL; la aprobación es separada",
                "Lea 'Endoso de Tanque' — endosos + restricciones juntos definen el emparejamiento de equipo",
            ]},
        ],
    },



    # ── Pass 5a · HR + Safety + PM onboarding + login troubleshoot ───
    "onboard-hr-first-week": {
        "title_es": "Personal de RH — Primera Semana",
        "summary_es": "Qué hace un nuevo miembro del personal de RH o Gerente de RH en su primera semana en MASCI.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido a RH. El portal de RH es personas-y-tiempo en MASCI. Su primera "
                "semana es principalmente configuración, observación y lectura — no trabajo "
                "solo. Tómese el tiempo. Los registros de RH son referenciados por nómina, "
                "auditorías y revisiones de proyecto durante años."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de RH de un administrador. Inicie sesión en /hr/login y complete su cambio de contraseña forzado.",
                "Día 1 — Lea la página principal pública del Centro de Orientación de principio a fin (15 minutos). Verá lo que hace cada portal.",
                "Día 2 — Siéntese con su Gerente de RH por una hora. Pídale que le muestre su bandeja de entrada: qué llega diariamente, qué llega semanalmente, qué es estacional.",
                "Día 2-3 — Observe un ciclo completo con su gerente antes de hacer uno usted mismo. La cadencia importa más que la pantalla.",
                "Día 3-4 — Observe una orientación completa de nuevo empleado, papeleo hasta el primer día. Tome notas de lo que se siente lento — ahí es donde ocurren los errores.",
                "Día 4-5 — Lea los artículos profundos de capacitación de RH una vez. Son largos a propósito; revise, marque, regrese cuando lo necesite.",
                "Fin de la semana 1 — Haga una lista de cada pregunta que aún no hizo. Hágalas. RH es perdonador con 'demasiadas preguntas temprano' — mucho menos con 'fingí saber'.",
            ]},
            {"type": "why", "text":
                "Los registros de RH fluyen a nómina la misma semana que se crean. Un error "
                "de primera semana en una entrada de tiempo se corrige con una conversación de "
                "30 segundos; el mismo error descubierto tres meses después requiere un ajuste "
                "de cheque, una nota de auditoría y una conversación difícil. Los errores son "
                "baratos en la semana uno. Se vuelven caros rápido."},
            {"type": "tip", "text":
                "Mantenga un cuaderno (papel o app) durante el primer mes. Escriba cada "
                "término, cada acrónimo, cada flujo que encuentre. Re-léalo semanalmente. "
                "Para la semana cuatro habrá creado su propia hoja de referencia de RH — y "
                "eso vale más que cualquier documento que podamos escribirle."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar haciendo verificación de tiempo independientemente con revisiones puntuales del gerente",
                "Para la semana 4 debería ser dueño de un ciclo de orientación de principio a fin",
                "Marque '¿No puede iniciar sesión?' (público) — lo necesitará para apuntar a nuevos miembros del personal",
            ]},
        ],
    },
    "tshoot-hr-login": {
        "title_es": "No puedo iniciar sesión en RH",
        "summary_es": "Soluciones rápidas cuando /hr/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "RH usa correo + contraseña por usuario. Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /hr/login (NO en /admin/login, NO en /pm/login — esos esperan cuentas diferentes y lo bloquearán después de varios intentos).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio un administrador. Será forzado a cambiarla.",
                "Si olvidó su contraseña, haga clic en '¿Olvidó su contraseña?' en /hr/login. Recibirá un enlace de restablecimiento por correo — de un solo uso, expiración de 30 minutos.",
                "Si el correo de restablecimiento nunca llega, revise spam. Si todavía falta después de 10 minutos, el correo registrado puede estar equivocado — contacte a su administrador.",
                "Si ve 'cuenta deshabilitada', un administrador ha bloqueado su cuenta. Contacte a su operador.",
            ]},
            {"type": "why", "text":
                "RH es su propio ámbito aislado — los tokens de administrador NO satisfacen "
                "los endpoints de RH. Es intencional: los registros de RH (personal, "
                "variación de nómina, amonestaciones) son lo suficientemente sensibles como "
                "para que 'admin puede ver todo' no sea la postura correcta para lecturas de RH."},
            {"type": "warn", "text":
                "NO escriba su contraseña de RH en el formulario de inicio de sesión de otro "
                "portal (Seguridad, PM, Taller, Despacho, Admin). Cada portal tiene su propio "
                "inicio de sesión. Pegar la contraseña equivocada en otro puede bloquear esa "
                "cuenta temporalmente después de varios intentos."},
            {"type": "tip", "text":
                "Si está bloqueado después de múltiples intentos malos, espere 15 minutos — "
                "el bloqueo es por IP y se auto-limpia. O contacte a su operador para "
                "limpiarlo antes."},
        ],
    },
    "onboard-safety-first-week": {
        "title_es": "Personal de Seguridad — Primera Semana",
        "summary_es": "Qué hace un nuevo Gerente, Coordinador u Oficial de Seguridad en su primera semana.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido a Seguridad. El portal de Seguridad es cómo MASCI prueba "
                "cumplimiento, documenta incidentes y defiende operaciones durante una visita "
                "de OSHA. Su primera semana es principalmente visitas a sitios, observación y "
                "lectura. La profundidad importa más que la velocidad."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de Seguridad de un administrador. Inicie sesión en /safety-portal/login y complete su cambio de contraseña forzado.",
                "Día 1 — Camine un sitio de trabajo activo con un miembro actual del personal de Seguridad. No tome notas de cumplimiento todavía — solo observe lo que ellos observan.",
                "Día 2 — Siéntese con su gerente y revise los últimos 30 días de incidentes, casi-incidentes y acciones correctivas. Los patrones importan más que los eventos individuales.",
                "Día 2-3 — Observe un incidente completo desde reporte → investigación → acción correctiva → cierre. No lo dirija. Observe la cadencia.",
                "Día 3-4 — Lea los artículos profundos de capacitación de Seguridad una vez. Márquelos. Están escritos para releerse cada trimestre.",
                "Día 4-5 — Dirija una Reunión de Seguridad bajo la supervisión de su gerente. Acostúmbrese al ritmo de dirigir una reunión.",
                "Fin de la semana 1 — Identifique el proyecto que más le preocupa. Ahí pertenece su atención en la semana 2.",
            ]},
            {"type": "why", "text":
                "Seguridad es el portal que se cita más a menudo en disputas — visitas de "
                "OSHA, reclamos de seguros, revisiones después de la acción. Los errores de "
                "primera semana se perdonan; la meta es construir la memoria muscular de "
                "'documentar específicamente, cerrar completamente, hacer seguimiento "
                "siempre' antes de operar solo."},
            {"type": "tip", "text":
                "Las cuadrillas de campo responden al personal de seguridad que ESCUCHA antes "
                "de corregir. Pase su primera semana preguntando '¿qué le ha estado "
                "frustrando?' en vez de '¿está siguiendo el procedimiento?'. La confianza "
                "que construya temprano se multiplica por años."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar redactando reportes rutinarios de incidentes independientemente",
                "Para la semana 4 debería ser dueño de la supervisión de seguridad de un proyecto de principio a fin",
                "Marque 'Si pasa algo en el sitio' (público) — esa es la superficie de campo que estará apoyando",
            ]},
        ],
    },
    "tshoot-safety-login": {
        "title_es": "No puedo iniciar sesión en Seguridad",
        "summary_es": "Soluciones rápidas cuando /safety-portal/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "Seguridad usa correo + contraseña por usuario. Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /safety-portal/login (NO en /admin/login ni en ninguna otra puerta de portal).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio un administrador. Será forzado a cambiarla.",
                "Use '¿Olvidó su contraseña?' para un enlace de restablecimiento por correo (un solo uso, expiración de 30 minutos).",
                "Revise spam si el correo de restablecimiento no llega. Si todavía falta, su operador puede tener el correo equivocado registrado.",
                "Si ve 'cuenta deshabilitada', contacte a su operador.",
            ]},
            {"type": "why", "text":
                "Seguridad es su propio ámbito aislado. Los tokens de administrador NO "
                "satisfacen los endpoints de Seguridad automáticamente — es intencional, "
                "porque los registros de Seguridad se referencian durante conversaciones con "
                "OSHA y necesitan una pista de auditoría limpia de 'quién leyó qué cuándo'."},
            {"type": "warn", "text":
                "NO escriba su contraseña de Seguridad en el formulario de inicio de sesión "
                "de otro portal. Cada portal tiene su propio inicio de sesión. Intentos malos "
                "repetidos en el portal equivocado pueden bloquear esa cuenta temporalmente."},
            {"type": "tip", "text":
                "Si está bloqueado, espere 15 minutos — el bloqueo se auto-limpia — o "
                "contacte a su operador. Los bloqueos de Seguridad son raros; si pasa dos "
                "veces en una semana, el problema probablemente es la URL de inicio de "
                "sesión equivocada, no la contraseña."},
        ],
    },
    "onboard-pm-first-week": {
        "title_es": "PM — Primera Semana",
        "summary_es": "Qué hace un nuevo Gerente de Proyecto o Co-PM en su primera semana en MASCI.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido a PM. El portal de PM es la lente a nivel de proyecto en MASCI. "
                "Su primera semana es principalmente escuchar, leer la historia del proyecto "
                "y construir relación con el campo. Los PMs que intentan empezar cambiando "
                "cosas en la semana uno casi siempre lo lamentan."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de PM de un administrador. Inicie sesión en /pm/login y complete su cambio de contraseña forzado.",
                "Día 1 — Lea cada proyecto que se le asignará. Últimos 30 días de Reportes Diarios, últimos 90 días de incidentes, últimos totales laborales del trimestre. No actúe todavía. Solo lea.",
                "Día 2 — Visite al menos un sitio de trabajo activo de cada proyecto asignado. Conozca al capataz en persona. Es su relación más importante.",
                "Día 2-3 — Siéntese con su PM saliente (si lo hay) por medio día de entrega. Pregunte: '¿Qué es frágil aquí? ¿Qué no escribió el último PM?'",
                "Día 3-4 — Recorra un ciclo de revisión semanal con otro PM. No lo dirija — solo observe qué mira y en qué orden.",
                "Día 4-5 — Lea los artículos profundos de capacitación de PM una vez. Son largos; revise y marque.",
                "Fin de la semana 1 — Identifique el proyecto que necesita más atención. Programe una visita al sitio para la semana 2.",
            ]},
            {"type": "why", "text":
                "Los PMs son el puente entre las operaciones de campo y las finanzas del "
                "proyecto. El trabajo de la primera semana no es demostrar mando — es "
                "construir un modelo mental claro de dónde está el campo, qué está "
                "funcionando, y qué le preocupaba al PM anterior. Ese modelo es de lo que "
                "depende cada decisión posterior."},
            {"type": "tip", "text":
                "Envíe una nota corta a cada capataz en su primera semana: 'Soy su nuevo PM, "
                "mi teléfono es X, mi correo es Y, llámeme antes del mediodía para respuesta "
                "más rápida.' La mayor parte de la fricción de comunicación en el trabajo de "
                "PM viene del campo no sabiendo cómo contactarlo. Cierre esa brecha el día tres."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar dirigiendo revisiones semanales de proyecto independientemente",
                "Para la semana 4 debería estar reconciliando mano de obra y respondiendo preguntas de dueños por su cuenta",
                "Marque 'Fundamentos de Reporte Diario' (público) — esa es la superficie de campo que alimenta su tablero",
            ]},
        ],
    },
    "tshoot-pm-login": {
        "title_es": "No puedo iniciar sesión en PM",
        "summary_es": "Soluciones rápidas cuando /pm/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "PM usa correo + contraseña por usuario. Cada PM tiene su propia cuenta "
                "acotada a los proyectos que administra. Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /pm/login (NO en /admin/login ni en ninguna otra puerta de portal).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio un administrador. Será forzado a cambiarla.",
                "Use '¿Olvidó su contraseña?' para un enlace de restablecimiento por correo (un solo uso, expiración de 30 minutos).",
                "Revise spam si el correo de restablecimiento no llega. Si todavía falta, su operador puede tener el correo equivocado registrado.",
                "Si ve 'cuenta deshabilitada' o 'bloqueada', contacte a su operador.",
            ]},
            {"type": "why", "text":
                "El alcance de PM es basado-en-proyecto, no basado-en-portal. Cada PM inicia "
                "sesión con su propia cuenta para que el registro de auditoría pueda atribuir "
                "cada acción a la persona correcta. Compartir credenciales de PM rompe la "
                "pista de auditoría y hace que las disputas sean más difíciles de resolver."},
            {"type": "warn", "text":
                "NO use las credenciales de otro PM, ni siquiera temporalmente. El registro "
                "de auditoría atribuirá cada acción a ellos — incluyendo cualquier "
                "aprobación, edición o cierre que realice. Si necesita acceso entre PMs, "
                "pídale a su operador la delegación apropiada."},
            {"type": "tip", "text":
                "Los bloqueos de PM se auto-limpian después de 15 minutos. Si está bloqueado "
                "dos veces en una semana, el problema casi siempre es la puerta de portal "
                "equivocada, no la contraseña."},
        ],
    },

    # ── Pass 5b · Shop + Dispatch onboarding + login troubleshoot ────
    "onboard-shop-first-week": {
        "title_es": "Personal de Taller / Flota — Primera Semana",
        "summary_es": "Qué hace un nuevo Mecánico, Capataz de Taller o Coordinador de Flota en su primera semana.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido al Taller. El portal de Taller / Flota es cómo MASCI mantiene el "
                "equipo operativo y documentado. Su primera semana es principalmente tiempo "
                "práctico en el patio, observando a quienes ya hacen el trabajo, y aprendiendo "
                "el ritmo de cómo el campo le habla al taller."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de Taller de un administrador. Inicie sesión en /shop/login y complete su cambio de contraseña forzado.",
                "Día 1 — Camine el patio con el Capataz de Taller. Toque cada pieza activa de equipo. Los nombres en la plataforma no significan nada hasta que haya puesto las manos en la unidad real.",
                "Día 2 — Siéntese con el Coordinador de Flota por una hora. Pídale que le muestre su día: qué llega primero, qué es de medio día, qué es reconciliación de fin de día.",
                "Día 2-3 — Observe un ciclo completo de revisión de Pre-Op desde el envío entrante hasta la llamada de seguimiento con el campo. No actúe todavía — observe la cadencia.",
                "Día 3-4 — Observe un triaje completo de daño desde el reporte de campo hasta la firma de reparación. Note dónde el operador de campo estaba equivocado, dónde tenía razón, y cómo fue la conversación.",
                "Día 4-5 — Lea los artículos profundos de capacitación de Taller una vez. Márquelos; están construidos para releerse cada trimestre.",
                "Fin de la semana 1 — Identifique la pieza de equipo que más preocupa a todos en el patio. Ahí pertenece su atención en la semana 2.",
            ]},
            {"type": "why", "text":
                "El Taller se sienta en la intersección de seguridad, dinero y moral del "
                "campo. Una unidad liberada muy temprano causa un incidente; una unidad "
                "retenida muy tarde paraliza un proyecto. La documentación del taller es lo "
                "único que prueba qué decisión se tomó y por qué. Los errores de primera "
                "semana se esperan — los atajos de documentación de primera semana, no."},
            {"type": "tip", "text":
                "Los operadores de campo confían en mecánicos que ESCUCHAN. Pase su primera "
                "semana preguntando a los operadores '¿qué le ha estado dando problemas?' en "
                "vez de decirles que su Pre-Op estaba mal. La confianza que construya temprano "
                "se muestra como reportes honestos de daño durante años."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar revisando Pre-Ops rutinarios independientemente",
                "Para la semana 4 debería ser dueño de una firma conjunta de devolución de equipo con Seguridad",
                "Marque 'Inspección Pre-Operación (Básico de Campo)' (público) — esa es la superficie de campo que estará apoyando",
            ]},
        ],
    },
    "tshoot-shop-login": {
        "title_es": "No puedo iniciar sesión en el Taller",
        "summary_es": "Soluciones rápidas cuando /shop/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "El Taller usa correo + contraseña por usuario. Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /shop/login (NO en /admin/login ni en ninguna otra puerta de portal).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio un administrador. Será forzado a cambiarla.",
                "Use '¿Olvidó su contraseña?' para un enlace de restablecimiento por correo (un solo uso, expiración de 30 minutos).",
                "Revise spam si el correo de restablecimiento no llega. Si todavía falta, su operador puede tener el correo equivocado registrado.",
                "Si ve 'cuenta deshabilitada' o 'bloqueada', contacte a su operador.",
            ]},
            {"type": "why", "text":
                "El Taller es su propio ámbito aislado. Los tokens de administrador NO "
                "satisfacen los endpoints de Taller automáticamente — es intencional, porque "
                "las firmas del taller se referencian durante disputas de seguros y "
                "necesitan una pista de auditoría limpia por usuario."},
            {"type": "warn", "text":
                "NO escriba su contraseña del Taller en el formulario de inicio de sesión "
                "de otro portal (Seguridad, RH, PM, Despacho, Admin). Cada portal tiene su "
                "propio inicio de sesión. Intentos malos repetidos en el portal equivocado "
                "pueden bloquear esa cuenta temporalmente."},
            {"type": "tip", "text":
                "Si está bloqueado, espere 15 minutos — el bloqueo se auto-limpia — o "
                "contacte a su operador. Los bloqueos del Taller usualmente significan la "
                "URL equivocada, no la contraseña equivocada. Marque /shop/login el día uno "
                "para evitar el problema."},
        ],
    },
    "onboard-dispatch-first-week": {
        "title_es": "Personal de Despacho — Primera Semana",
        "summary_es": "Qué hace un nuevo Despachador, Coordinador de Flota o miembro de Supervisión de Operaciones en su primera semana.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido a Despacho. El portal de Despacho es cómo MASCI coordina equipo a "
                "través de proyectos activos. Su primera semana es principalmente escuchar, "
                "mapear modelos mentales a unidades físicas, y aprender el ritmo de cómo el "
                "campo, el taller y la oficina no están de acuerdo sobre dónde está el equipo."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de Despacho de un administrador. Inicie sesión en /dispatch-portal/login y complete su cambio de contraseña forzado.",
                "Día 1 — Siéntese al lado del despachador actual durante el empuje matutino. No hable. Solo observe cómo decide qué llamada tomar primero.",
                "Día 2 — Visite al menos dos sitios de trabajo activos. Vea el equipo con sus propios ojos antes de confiar en cualquier reporte del sistema. La memoria de las unidades físicas paga durante meses.",
                "Día 2-3 — Observe un evento completo de movimiento trabajo-a-trabajo desde la liberación hasta la llegada. Note dónde la vista del sistema y la realidad divergieron.",
                "Día 3-4 — Lea los últimos 30 días de reportes de discrepancia entre campo y despacho. Los patrones importan más que los incidentes individuales.",
                "Día 4-5 — Lea los artículos profundos de capacitación de Despacho una vez. Son largos; revise y marque.",
                "Fin de la semana 1 — Identifique el proyecto que sigue generando problemas de reconciliación. Planifique una visita al sitio para la semana 2.",
            ]},
            {"type": "why", "text":
                "Despacho está aguas arriba de cada decisión de activos que toma el resto de "
                "la plataforma. Un despachador de primera semana que reconcilia honestamente "
                "vale más que un veterano de diez años que esconde discrepancias para "
                "mantener limpios los números. Construya el hábito temprano: escriba lo que "
                "es verdad, incluso cuando es desordenado."},
            {"type": "tip", "text":
                "Las cuadrillas de campo confían en despachadores que contestan el teléfono. "
                "Pase su primera semana contestando cada llamada en dos timbrazos, incluso "
                "si no puede resolverla todavía. 'No sé, déjeme averiguar' le gana a 'le "
                "llamo de vuelta' cada vez."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar dirigiendo eventos de movimiento rutinarios independientemente",
                "Para la semana 4 debería estar reconciliando discrepancias de campo por su cuenta",
                "Marque 'Fundamentos de Reporte Diario' (público) — esa es la superficie de campo que alimenta lo que ve",
            ]},
        ],
    },
    "tshoot-dispatch-login": {
        "title_es": "No puedo iniciar sesión en Despacho",
        "summary_es": "Soluciones rápidas cuando /dispatch-portal/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "Despacho usa correo + contraseña por usuario. Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /dispatch-portal/login (NO en /admin/login ni en ninguna otra puerta de portal — la URL de Despacho es más larga que la mayoría).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio un administrador. Será forzado a cambiarla.",
                "Use '¿Olvidó su contraseña?' para un enlace de restablecimiento por correo (un solo uso, expiración de 30 minutos).",
                "Revise spam si el correo de restablecimiento no llega. Si todavía falta, su operador puede tener el correo equivocado registrado.",
                "Si ve 'cuenta deshabilitada' o 'bloqueada', contacte a su operador.",
            ]},
            {"type": "why", "text":
                "Despacho es su propio ámbito aislado. Los tokens de administrador NO "
                "satisfacen los endpoints de Despacho automáticamente — es intencional, "
                "porque los registros de despacho se referencian durante revisiones de "
                "utilización y necesitan atribución limpia por usuario."},
            {"type": "warn", "text":
                "NO escriba su contraseña de Despacho en el formulario de inicio de sesión "
                "de otro portal. Cada portal tiene su propio inicio de sesión. La URL de "
                "Despacho es /dispatch-portal/login — más larga que la de RH o Taller — y "
                "confundirla con otra puerta de portal es el error de inicio de sesión más "
                "común de primera semana."},
            {"type": "tip", "text":
                "Marque /dispatch-portal/login el día uno. Es la URL de portal más larga "
                "y la más fácil de recordar mal. Los bloqueos se auto-limpian en 15 "
                "minutos si llega a tener uno."},
        ],
    },

    # ── Pass 5c · Admin onboarding + login troubleshoot ──────────────
    "onboard-admin-first-week": {
        "title_es": "Admin / Operador — Primera Semana",
        "summary_es": "Qué hace un nuevo Operador de plataforma en su primera semana. Deliberado, lento, auditoría-primero.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido. Operador es el rol de más confianza en la plataforma — y el "
                "de mayor radio de impacto. Su primera semana es deliberadamente lenta. "
                "Lea, observe, pregunte y resista el impulso de cambiar cosas. Cada operador "
                "que se equivocó seriamente llegó ahí actuando rápido en la semana uno."},
            {"type": "steps", "items": [
                "Día 1 — Reciba sus credenciales de operador directamente del Dueño de la plataforma. Inicie sesión en /admin/login y complete su cambio de contraseña forzado. Cámbiela otra vez al final de la semana 1 — para entonces habrá aprendido cómo se siente una contraseña fuerte en este entorno.",
                "Día 1 — Lea la guía profunda de la Consola de Admin una vez, de principio a fin. No actúe sobre nada todavía.",
                "Día 2 — Siéntese al lado del operador actual durante el día completo. Observe lo que hace, no lo que dice que hace. La brecha entre esos dos es donde se esconden la mayoría de los errores.",
                "Día 2-3 — Lea cada entrada del registro de auditoría de los últimos 30 días. Los patrones importan más que los eventos individuales. Si algo se ve raro, pregunte antes de asumir.",
                "Día 3-4 — Elija una tarea de mantenimiento de bajo riesgo (por ejemplo, revisar el tablero de desviación de inventario operacional) y recórrala bajo supervisión. No realice ninguna operación de gestión de usuarios o respaldo solo todavía.",
                "Día 4-5 — Lea los últimos dos post-mortems de incidentes de la plataforma si existen. El trabajo de operador se juzga por lo que no pasó — conocer los casi-incidentes pasados es cómo se mantiene ahí.",
                "Fin de la semana 1 — Haga una lista de cada superficie del sistema que aún no entiende. Llévela a su reunión semanal con el Dueño.",
            ]},
            {"type": "why", "text":
                "El trabajo de Admin es de alta confianza y alto impacto. Un error de "
                "primera semana en un registro de usuario crea una pista de papel. Un "
                "error de primera semana en una plantilla de rol crea una brecha de "
                "seguridad. Un error de primera semana en un respaldo crea un problema de "
                "recuperación. El costo de ir lento en la semana uno es cero; el costo de "
                "ir rápido puede ser permanente."},
            {"type": "tip", "text":
                "El trabajo de operador es una relación con el Dueño, no solo un trabajo "
                "técnico. En su primera semana, envíe un resumen corto de fin del día cada "
                "día: 'hoy hice X, Y, Z; mañana planeo hacer A, B, C; mis preguntas son "
                "1, 2.' La mayor parte de la fricción de orientación de operador viene de "
                "brechas en comunicación, no en habilidad."},
            {"type": "next", "items": [
                "Para la semana 2 debería estar realizando operaciones rutinarias de solo lectura independientemente",
                "Para la semana 4 debería ser dueño de un ciclo de gestión de usuarios de principio a fin con la aprobación del Dueño",
                "Marque el registro de auditoría — vivirá en él",
            ]},
        ],
    },
    "tshoot-admin-login": {
        "title_es": "No puedo iniciar sesión en Admin",
        "summary_es": "Soluciones rápidas cuando /admin/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "Admin usa una contraseña emitida directamente por el Dueño de la plataforma. "
                "Si no puede entrar, recorra estos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /admin/login (NO en /hr/login ni en ninguna otra puerta de portal — admin tiene su propia superficie).",
                "Revise mayúsculas y ortografía. Las contraseñas distinguen mayúsculas y minúsculas.",
                "Si es su primer inicio de sesión, use la contraseña temporal que le dio el Dueño. Será forzado a cambiarla.",
                "Si olvidó su contraseña, contacte al Dueño de la plataforma directamente. Los restablecimientos de contraseña de admin no son auto-servicio por diseño.",
                "Si ve 'cuenta deshabilitada' o 'bloqueada', contacte al Dueño. Los bloqueos de admin son raros e intencionales.",
                "No solicite un restablecimiento de contraseña de admin por ningún otro canal (chat, reenvío de correo, capturas de pantalla). El Dueño es la única ruta de restablecimiento autorizada.",
            ]},
            {"type": "why", "text":
                "Los restablecimientos de contraseña de admin deliberadamente no están "
                "automatizados. Un restablecimiento de auto-servicio para la cuenta más "
                "privilegiada de la plataforma sería una debilidad estructural. La ruta "
                "de restablecimiento solo-Dueño es una característica, no una fricción — "
                "hace que un ataque de phishing a una cuenta de operador sea "
                "significativamente más difícil."},
            {"type": "warn", "text":
                "Nunca pegue su contraseña de admin en el formulario de inicio de sesión "
                "de otro portal. Nunca comparta una contraseña de admin — ni con otro "
                "operador, ni con el Dueño por chat, nunca. Si sospecha que su contraseña "
                "de admin ha sido vista por alguien, solicite una rotación a través del "
                "Dueño inmediatamente."},
            {"type": "tip", "text":
                "Los bloqueos de admin se auto-limpian en 15 minutos para bloqueos basados "
                "en IP. Los bloqueos a nivel de cuenta requieren acción del Dueño. Marque "
                "/admin/login y úselo desde un dispositivo conocido — la falla más común "
                "de inicio de sesión de admin es escribir /admin en un navegador de "
                "teléfono que auto-completa a una URL de portal previa."},
        ],
    },

    # ── tshoot-session-timeout ───────────────────────────────────────
    "tshoot-session-timeout": {
        "title_es": "Mi sesión se cerró",
        "summary_es": "Por qué pasa y qué hacer.",
        "body_es": [
            {"type": "p", "text": "Las sesiones de MASCI expiran por seguridad — generalmente después de varias horas inactivo o 12 horas en total."},
            {"type": "steps", "items": [
                "Vuelva a iniciar sesión con su correo y contraseña.",
                "Si estaba llenando un formulario, MASCI guarda borradores localmente — abra el formulario otra vez para recuperarlo.",
                "Si no se acuerda de la contraseña, use 'Olvidé mi contraseña' o llame a la oficina.",
            ]},
            {"type": "why", "text": "Cerrar sesión automáticamente protege la información si pierde el teléfono o lo deja prestado."},
        ],
    },

    # ── why-session-timeouts ─────────────────────────────────────────
    "why-session-timeouts": {
        "title_es": "Por qué expiran las sesiones",
        "summary_es": "Es un control de seguridad — no un error.",
        "body_es": [
            {"type": "p", "text": "Cada portal de MASCI cierra sesión solo después de inactividad o de un máximo de 12 horas continuas. No es una falla del sistema."},
            {"type": "why", "text": "Si su teléfono se pierde o queda desatendido, la sesión expirada evita que un extraño vea reportes, datos de empleados o registros de cumplimiento. Es la misma razón por la que su banco también cierra sesión automáticamente."},
            {"type": "tip", "text": "Si su sesión se cierra mientras llena un formulario, los datos quedan guardados localmente — abra el formulario de nuevo y siga llenando."},
        ],
    },

    # ── onboard-login ────────────────────────────────────────────────
    "onboard-login": {
        "title_es": "Cómo iniciar sesión",
        "summary_es": "Lo básico de la primera vez que entra.",
        "body_es": [
            {"type": "p", "text": "Casi todos los formularios de campo en MASCI se pueden llenar sin iniciar sesión — basta con escanear el código QR del cartel o usar el enlace público. Solo necesita inicio de sesión para los portales (RH, Seguridad, Taller, Despacho, PM, Admin, Liderazgo de Campo)."},
            {"type": "steps", "items": [
                "Abra https://safety-audit-mobile-1.preview.emergentagent.com en su teléfono o computadora.",
                "Toque 'Iniciar sesión' arriba a la derecha.",
                "Escriba su correo de trabajo y su contraseña.",
                "Si es la primera vez, le pedirá cambiar la contraseña.",
            ]},
            {"type": "tip", "text": "Si no tiene credenciales aún, llame a la oficina o pregúntele a RH."},
        ],
    },

    # ── onboard-mobile ───────────────────────────────────────────────
    "onboard-mobile": {
        "title_es": "Usando MASCI en el teléfono o tableta",
        "summary_es": "Consejos para que su trabajo no se pierda.",
        "body_es": [
            {"type": "p", "text": "MASCI funciona en cualquier teléfono o tableta con cámara y navegador. No hay que descargar nada."},
            {"type": "steps", "items": [
                "Abra el navegador (Chrome o Safari).",
                "Vaya a la dirección del Hub MASCI o escanee un código QR del sitio.",
                "Agregue el sitio a la pantalla de inicio — toque el menú del navegador y elija 'Agregar a la pantalla de inicio'.",
                "Llene formularios normalmente — MASCI guarda lo que escribe aunque pierda señal.",
            ]},
            {"type": "tip", "text": "Si pierde señal en medio de un formulario, siga llenándolo — al recuperar señal se envía automáticamente."},
            {"type": "warn", "text": "No cierre la pestaña del navegador hasta ver la pantalla de 'Gracias' — eso confirma que se envió."},
        ],
    },

    # ── public-mobile-qr ─────────────────────────────────────────────
    "public-mobile-qr": {
        "title_es": "Escanear-y-listo: Usando el código QR del sitio",
        "summary_es": "Abra MASCI en su teléfono en segundos.",
        "body_es": [
            {"type": "p", "text": "Cada sitio de trabajo MASCI tiene carteles con códigos QR. Estos son los atajos más rápidos a los formularios."},
            {"type": "steps", "items": [
                "Abra la cámara del teléfono.",
                "Apúntela al código QR — no necesita tomar la foto, solo apuntar.",
                "Toque el enlace que aparece arriba en la pantalla.",
                "Se abre el formulario correcto en su navegador. Listo.",
            ]},
            {"type": "why", "text": "Los QR brincan el menú — abren directo el formulario que necesita. No hay que iniciar sesión, no hay que instalar nada."},
            {"type": "tip", "text": "Después de la primera vez, agregue el sitio a la pantalla de inicio del teléfono y será un solo toque la próxima vez."},
        ],
    },

    # ── public-photos ────────────────────────────────────────────────
    "public-photos": {
        "title_es": "Fotos que realmente sirven",
        "summary_es": "Toma amplia · acercamiento · claras.",
        "body_es": [
            {"type": "p", "text": "Una foto buena cuenta toda la historia. Una foto mala obliga a explicar con palabras lo que la foto debió mostrar."},
            {"type": "steps", "items": [
                "Toma amplia: muestre todo el contexto del área — la cuadrilla, el equipo, dónde está el problema.",
                "Acercamiento: muestre el detalle exacto del problema — la fuga, la grieta, el daño.",
                "Limpie el lente antes de tomar la foto (los teléfonos de campo están sucios — la foto sale borrosa).",
                "Buena luz — si está oscuro, encienda el flash o use linterna.",
            ]},
            {"type": "why", "text": "Las fotos son evidencia. La oficina, Seguridad y el cliente confían en ellas para decisiones. Una foto borrosa o lejana retrasa todo porque alguien tiene que volver a tomar la foto bien."},
            {"type": "mistakes", "items": [
                "Una sola foto de lejos — sin acercamiento del problema",
                "Lente sucio o dedo cubriendo parte del lente",
                "Foto tomada en oscuridad sin flash",
                "Foto tomada del seat del equipo en lugar de caminar al problema",
            ]},
        ],
    },

    # ── public-daily-report-basics ───────────────────────────────────
    "public-daily-report-basics": {
        "title_es": "Qué es un Reporte Diario (y por qué el suyo importa)",
        "summary_es": "Un registro por cuadrilla, por día — todo lo que pasó.",
        "body_es": [
            {"type": "p", "text": "El Reporte Diario es el registro oficial del día: quién trabajó, qué se hizo, qué equipo se usó, qué materiales llegaron, el clima, fotos. Se llena al final del turno."},
            {"type": "bullets", "items": [
                "Cuadrillas — quién, cuántas horas, qué hicieron",
                "Subcontratistas — qué empresa, cuántos trabajadores",
                "Visitantes — inspectores, dueños, terceros que llegaron",
                "Equipo — qué unidades trabajaron, cuántas horas",
                "Materiales — qué llegó, de quién, cuánto",
                "Clima — temperatura, lluvia, viento si afectó",
                "Fotos — al menos 6 — caminando por el sitio",
            ]},
            {"type": "why", "text": "El Reporte Diario es la prueba de lo que se hizo. Sin él, no hay nóminas correctas, no hay pago al cliente, no hay defensa si algo se reclama después."},
            {"type": "tip", "text": "Llene el reporte en el sitio — no al regresar a casa. Los detalles se olvidan rápido."},
        ],
    },

    # ── public-incident-basics ───────────────────────────────────────
    "public-incident-basics": {
        "title_es": "Si pasa algo en el sitio",
        "summary_es": "Primeros pasos después de una lesión, cuasi-accidente o daño.",
        "body_es": [
            {"type": "p", "text": "Las cosas pasan. Lo que importa es qué hace en los próximos minutos."},
            {"type": "steps", "items": [
                "Asegure el área primero — eso siempre va antes del papeleo.",
                "Avise al supervisor o capataz de inmediato — en persona, no por mensaje.",
                "Si hay un herido, consiga atención médica — llame al 911 si es grave.",
                "Tome fotos de la escena si es seguro hacerlo.",
                "No mueva equipo ni limpie hasta que se lo indiquen (preserva la evidencia).",
            ]},
            {"type": "why", "text": "Reportar rápido y honestamente protege a todos — al herido, a la cuadrilla, al supervisor y a la empresa. Reportar tarde o vago protege a nadie."},
            {"type": "warn", "text": "No adivine sobre la causa ni asigne culpas. Solo describa lo que vio. Seguridad investiga desde ahí."},
            {"type": "tip", "text": "Un cuasi-accidente (algo que casi pasó — casi se cayó, casi golpeó) vale la pena reportarlo igual. Los cuasi-accidentes son las lecciones más baratas que la cuadrilla recibe — hable y puede que acabe de prevenir el accidente real."},
        ],
    },

    # ── public-cant-login ────────────────────────────────────────────
    "public-cant-login": {
        "title_es": "No puedo iniciar sesión",
        "summary_es": "Problemas comunes y soluciones.",
        "body_es": [
            {"type": "p", "text": "Primero — recuerde que la mayoría de formularios de campo NO necesitan inicio de sesión. Si escaneó un código QR del sitio o usa un enlace público, simplemente llene el formulario."},
            {"type": "p", "text": "Si necesita entrar a un portal (RH, Seguridad, Taller, Despacho, PM, Admin, Liderazgo de Campo):"},
            {"type": "steps", "items": [
                "Verifique que está escribiendo el correo de trabajo correcto (no el personal).",
                "Verifique que la contraseña está bien escrita — mayúsculas y minúsculas cuentan.",
                "Pruebe 'Olvidé mi contraseña' si está disponible para su portal.",
                "Si sigue sin entrar, llame a la oficina o pregunte a RH.",
            ]},
            {"type": "tip", "text": "Si comparte un teléfono o computadora con otro compañero, asegúrese de cerrar sesión cuando termine para que él pueda entrar con su propia cuenta."},
        ],
    },

    # ── public-who-to-ask ────────────────────────────────────────────
    "public-who-to-ask": {
        "title_es": "¿A quién le pregunto cuando necesito ayuda?",
        "summary_es": "Un mapa rápido de quién maneja qué.",
        "body_es": [
            {"type": "p", "text": "Si está en la cuadrilla y no sabe con quién hablar — esta es la guía rápida."},
            {"type": "bullets", "items": [
                "Problema de seguridad o casi-accidente → Capataz primero, luego Gerente de Seguridad",
                "Equipo dañado o que falla en Pre-Op → Capataz primero, luego Taller",
                "Pago, horas o cheques → RH",
                "Llegada de materiales o cambios en el cronograma → PM (Gerente de Proyecto)",
                "Lesión → Capataz INMEDIATAMENTE — y llame al 911 si es grave",
                "No puedo iniciar sesión en MASCI → Oficina o RH",
                "Otro asunto del trabajo (qué hago hoy, dónde voy, etc.) → Su capataz",
            ]},
            {"type": "tip", "text": "Cuando tenga duda, su capataz es el primer contacto. Él o ella sabe a quién más involucrar."},
        ],
    },

    # ── public-why-documentation ─────────────────────────────────────
    "public-why-documentation": {
        "title_es": "Por qué importa este papeleo",
        "summary_es": "La versión de la cuadrilla.",
        "body_es": [
            {"type": "p", "text": "Llenar formularios puede parecer extra trabajo. Pero todo formulario en MASCI existe por una razón muy específica."},
            {"type": "bullets", "items": [
                "Reportes Diarios → su nómina sale correcta · el cliente paga al tiempo",
                "Pre-Op del equipo → usted no opera una máquina insegura · si algo se rompió antes, no se lo cobran a usted",
                "Reuniones de Seguridad → su firma es la prueba de que escuchó el tema · lo protege a usted y al equipo",
                "Reportes de Incidentes → la verdad queda registrada · seguro y abogados ven el lado de la cuadrilla, no solo el del cliente",
                "QA/QC → el trabajo se hace bien la primera vez · sin re-trabajo no remunerado",
            ]},
            {"type": "why", "text": "Cada papeleo lo protege a usted, a la cuadrilla y a la empresa. Si algo sale mal en el futuro — la documentación es la diferencia entre 'lo hicimos bien' y 'no podemos probarlo'."},
            {"type": "tip", "text": "Pregunte por qué cualquier formulario existe. Toda persona en MASCI debería poder explicárselo."},
        ],
    },

    # ── public-preop-basics ──────────────────────────────────────────
    "public-preop-basics": {
        "title_es": "Inspección Pre-Operación (Básico de Campo)",
        "summary_es": "Revisión diaria antes de operar. Firme su nombre. Marque lo que esté roto.",
        "body_es": [
            {"type": "p", "text": "Antes de operar cualquier equipo, hay que caminarlo. El Pre-Op es el registro de ese recorrido: fluidos, llantas, luces, dispositivos de seguridad, daños evidentes. Usted firma y lo envía antes de empezar a trabajar."},
            {"type": "steps", "items": [
                "Abra el formulario Pre-Op (escanee el QR del equipo o use el enlace público).",
                "Camine la máquina — realmente camínela, no marque sentado en el asiento.",
                "Revise fluidos, llantas/orugas, luces, alarmas, cinturón, guardas, controles.",
                "Tome fotos de cualquier cosa que esté mal antes de enviar.",
                "Envíe. El formulario registra la hora y su nombre.",
            ]},
            {"type": "why", "text": "El Pre-Op lo protege a usted. Si la máquina estaba dañada antes de que la usara, su Pre-Op firmado muestra que usted lo señaló. Si no firmó, la pregunta se vuelve si usted causó el daño. Cinco minutos de caminar la máquina es el seguro más barato del trabajo."},
            {"type": "warn", "text": "Si algo falla la inspección, NO opere el equipo. Avise al supervisor. El taller tiene que liberarlo antes de que la unidad regrese al servicio."},
            {"type": "bullets", "items": [
                "Frenos flojos → pare, no opere",
                "Fuga hidráulica → pare, no opere",
                "Guardas faltantes o agrietadas → pare, no opere",
                "Cualquier cosa donde no metería a su hijo → pare",
            ]},
        ],
    },

    # ── public-toolbox-talks ─────────────────────────────────────────
    "public-toolbox-talks": {
        "title_es": "Reuniones de Seguridad",
        "summary_es": "Firme. Escuche. El registro es su firma.",
        "body_es": [
            {"type": "p", "text": "Una reunión de seguridad es una junta corta al inicio del día o turno. Tema del día, peligros, cualquier cosa nueva. Usted firma la lista — así queda registrado que asistió y entendió."},
            {"type": "steps", "items": [
                "Llegue a tiempo — usualmente son 5 a 15 minutos.",
                "Escuche el tema. Pregunte si algo no le quedó claro.",
                "Firme la lista de asistencia cuando le llegue (o escanee el QR / envíe por el formulario público).",
                "Si vio un peligro durante la reunión, hable antes de que la cuadrilla se separe.",
            ]},
            {"type": "why", "text": "Su firma es el registro de que escuchó el tema de seguridad. Si después pasa algo que se cubrió en la reunión, esa firma protege a todos — usted supo, la cuadrilla supo, la empresa puede demostrarlo. Saltarse la firma hace lo contrario."},
            {"type": "tip", "text": "Si no puede llegar (médico, cambio de turno), avise al supervisor. A veces le dejan reconocer aparte."},
        ],
    },

    # ── public-qaqc-basics ───────────────────────────────────────────
    "public-qaqc-basics": {
        "title_es": "QA/QC para Cuadrillas de Campo",
        "summary_es": "Revisiones de calidad mientras trabaja — fotos, medidas, firmas.",
        "body_es": [
            {"type": "p", "text": "QA/QC significa Aseguramiento de Calidad / Control de Calidad. En el campo son los registros que crea usted que prueban que el trabajo se hizo según especificación — fotos del refuerzo antes de la colada, dimensiones, materiales usados, firmas en cada etapa."},
            {"type": "bullets", "items": [
                "Foto ANTES de cubrir (colada de concreto, relleno, tablaroca, etc.)",
                "Foto DESPUÉS si la condición importa",
                "Registre medidas / conteos cuando se le pida — adivinanzas no ayudan a nadie",
                "Anote quién inspeccionó y cuándo, si usted es el que lo hace",
            ]},
            {"type": "why", "text": "La documentación QA/QC protege al proyecto. Si el dueño o inspector pregunta '¿esto va con la especificación?', la respuesta es lo que digan las fotos y registros. Buenos registros = sin discusiones de re-trabajo. Registros faltantes = re-trabajo o peor."},
            {"type": "warn", "text": "No cuele, no cubra, no cierre trabajo que se supone tenía que inspeccionarse primero. Espere la firma o capture el registro de inspección en el momento."},
        ],
    },

    # ── public-material-calculator ───────────────────────────────────
    "public-material-calculator": {
        "title_es": "Calculadora de Materiales y Herramientas de Campo",
        "summary_es": "Matemáticas rápidas para concreto, grava, asfalto y más.",
        "body_es": [
            {"type": "p", "text": "La Calculadora de Materiales es una herramienta sin inicio de sesión en la plataforma MASCI que estima cantidades para materiales comunes — concreto (yardas), grava (toneladas), asfalto (toneladas), relleno de zanjas de tubería y similares. Es aproximado: sirve para pedir y para verificar dos veces, NO sustituye los planos de ingeniería."},
            {"type": "steps", "items": [
                "Elija el tipo de material.",
                "Ingrese las dimensiones (largo × ancho × profundo, o lo que la herramienta pida).",
                "Revise la cantidad calculada.",
                "Compare con su plano o con el número del supervisor — si no coinciden, pregunte antes de pedir.",
            ]},
            {"type": "why", "text": "Pedir de más desperdicia dinero; pedir de menos detiene a la cuadrilla. La calculadora atrapa errores evidentes antes de que llegue el camión. Una revisión de 30 segundos es más barata que medio día de espera."},
            {"type": "mistakes", "items": [
                "Mezclar unidades (pies vs pulgadas, yardas vs toneladas) — lea las etiquetas con cuidado",
                "Olvidar factores de desperdicio / compactación — el supervisor sabe el multiplicador correcto",
                "Confiar en la calculadora sobre el plano cuando no coinciden — verifique",
            ]},
            {"type": "tip", "text": "Cuando tenga duda, mándele al supervisor una captura de pantalla del resultado antes de hacer el pedido. Confirmación de dos minutos, cero re-pedidos."},
        ],
    },

    # ── public-tools-map ─────────────────────────────────────────────
    "public-tools-map": {
        "title_es": "Herramientas Públicas de Campo — Lo que está disponible sin iniciar sesión",
        "summary_es": "Índice de todas las herramientas sin inicio de sesión en la plataforma.",
        "body_es": [
            {"type": "p", "text": "Estas son todas las herramientas que cualquier persona en la cuadrilla puede usar SIN iniciar sesión. Escanee un código QR del sitio o use el enlace directo."},
            {"type": "bullets", "items": [
                "Reporte Diario — Lo que pasó hoy en el sitio (cuadrillas, equipo, materiales, fotos)",
                "Inspección Pre-Op de Equipo — Recorrido OSHA diario por unidad",
                "Reunión de Seguridad — Firma + lista de asistencia",
                "Reporte de Accidente / Incidente — Si pasa algo, pequeño o grande",
                "Inspección del Sitio — Revisión general de seguridad en el lugar",
                "QA/QC — Inspecciones de calidad por etapa",
                "Calculadora de Materiales — Concreto, grava, asfalto",
                "Hoja de Referencia / Cheat Sheet — Tarjeta imprimible con los pasos básicos",
            ]},
            {"type": "why", "text": "Estas herramientas no requieren inicio de sesión a propósito — para que cualquier persona en la cuadrilla pueda llenarlas sin pedir credenciales a la oficina. La cuenta queda registrada por nombre escrito + firma + GPS + foto."},
            {"type": "tip", "text": "Si solo usa una herramienta — que sea el Reporte Diario. Es la columna vertebral de cómo se documenta el día."},
        ],
    },

    # ── iter205 · Tiered Guidance RBAC · public identity articles ────
    # Operator directive: identity articles must NOT expose internal workflows.
    "portal-hr-identity": {
        "title_es": "Portal de RH — Resumen",
        "summary_es": "Para qué es el Portal de RH y cómo accederlo. La capacitación operacional de RH requiere inicio de sesión.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de RH es el portal de personas y tiempo de MASCI. Existe para que "
                "el personal de RH tenga un solo lugar para administrar registros de empleados y tiempo."},
            {"type": "p", "text":
                "Quién lo usa: Personal de RH y Gerentes de RH."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /hr/login con el correo y la contraseña que "
                "le emitió un administrador. Si no tiene una cuenta, contacte a su operador."},
            {"type": "warn", "text":
                "La capacitación operacional de RH (procedimientos, flujos, SOPs internos) "
                "está restringida al personal de RH. El Centro de Orientación público no "
                "muestra esos artículos. Si es personal de RH, inicie sesión para leerlos. "
                "Si no lo es, este material no es visible para usted intencionalmente."},
        ],
    },
    "portal-safety-identity": {
        "title_es": "Portal de Seguridad — Resumen",
        "summary_es": "Para qué es el Portal de Seguridad y cómo accederlo. La capacitación operacional requiere inicio de sesión.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de Seguridad es el sistema que usa el personal de Seguridad para "
                "administrar el cumplimiento, los incidentes y las auditorías en MASCI."},
            {"type": "p", "text":
                "Quién lo usa: Gerentes, Coordinadores y Oficiales de Seguridad."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /safety-portal/login con el correo y la "
                "contraseña que le emitió un administrador. Si no tiene una cuenta, contacte "
                "a su operador."},
            {"type": "warn", "text":
                "La capacitación operacional de Seguridad (procedimientos, flujos, SOPs "
                "internos) está restringida al personal de Seguridad. Las cuadrillas de campo "
                "pueden leer orientación básica de seguridad (pública) en otra parte del "
                "Centro de Orientación. El contenido a nivel de flujo no es visible para "
                "usuarios anónimos."},
            {"type": "next", "items": [
                "Si es cuadrilla de campo — lea 'Si pasa algo en el sitio' (público)",
                "Si no puede iniciar sesión — lea '¿No puede iniciar sesión?' (público)",
            ]},
        ],
    },
    "portal-shop-identity": {
        "title_es": "Portal de Taller / Flota — Resumen",
        "summary_es": "Para qué es el Portal del Taller y cómo accederlo. La capacitación operacional requiere inicio de sesión.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de Taller / Flota es el sistema que usa el personal del Taller para "
                "mantener la flota de MASCI funcionando. Existe para que mecánicos y "
                "coordinadores de flota tengan un solo lugar para administrar la salud del equipo."},
            {"type": "p", "text":
                "Quién lo usa: Mecánicos, Capataz de Taller, Coordinador de Flota."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /shop/login con el correo y la contraseña "
                "que le emitió un administrador. Si no tiene una cuenta, contacte a su operador."},
            {"type": "warn", "text":
                "La capacitación operacional del Taller (procedimientos, flujos, SOPs "
                "internos) está restringida al personal del Taller. Los operadores de campo "
                "pueden leer 'Inspección Pre-Operación (Básico de Campo)' (pública) para la "
                "superficie de campo. El contenido a nivel de flujo no es visible para "
                "usuarios anónimos."},
            {"type": "next", "items": [
                "Si es operador de campo — lea 'Inspección Pre-Operación (Básico de Campo)' (público)",
                "Si no puede iniciar sesión — lea '¿No puede iniciar sesión?' (público)",
            ]},
        ],
    },
    "portal-dispatch-identity": {
        "title_es": "Portal de Despacho — Resumen",
        "summary_es": "Para qué es el Portal de Despacho y cómo accederlo. La capacitación operacional requiere inicio de sesión.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de Despacho es el sistema que usa el personal de Despacho para "
                "coordinar equipo a través de los proyectos de MASCI. Existe para que "
                "despachadores y coordinadores de flota tengan un solo lugar para saber "
                "dónde están los activos."},
            {"type": "p", "text":
                "Quién lo usa: Despachadores, Coordinadores de Flota, Supervisión de Operaciones."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /dispatch-portal/login con el correo y la "
                "contraseña que le emitió un administrador. Si no tiene una cuenta, contacte "
                "a su operador."},
            {"type": "warn", "text":
                "La capacitación operacional de Despacho (procedimientos, flujos, SOPs "
                "internos) está restringida al personal de Despacho. El contenido a nivel de "
                "flujo no es visible para usuarios anónimos."},
            {"type": "next", "items": [
                "Si no puede iniciar sesión — lea '¿No puede iniciar sesión?' (público)",
            ]},
        ],
    },
    "portal-pm-identity": {
        "title_es": "Portal de PM — Resumen",
        "summary_es": "Para qué es el Portal de PM y cómo accederlo. La capacitación operacional de PM requiere inicio de sesión.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de PM (Gestión de Proyectos) es el sistema que usan los Gerentes de "
                "Proyecto para supervisar sus proyectos asignados. Existe para que cada PM "
                "tenga un solo lugar acotado a los proyectos que administra."},
            {"type": "p", "text":
                "Quién lo usa: Gerentes de Proyecto y Co-PMs."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /pm/login con el correo y la contraseña que "
                "le emitió un administrador. Si no tiene una cuenta, contacte a su operador."},
            {"type": "warn", "text":
                "La capacitación operacional de PM (procedimientos, flujos, SOPs internos) "
                "está restringida a los PMs. Las cuadrillas de campo pueden leer orientación "
                "pública sobre Reportes Diarios. El contenido a nivel de gestión de PM no es "
                "visible para usuarios anónimos."},
            {"type": "next", "items": [
                "Si es cuadrilla de campo — lea 'Fundamentos de Reporte Diario' (público)",
                "Si no puede iniciar sesión — lea '¿No puede iniciar sesión?' (público)",
            ]},
        ],
    },
    "portal-admin-identity": {
        "title_es": "Consola de Admin — Resumen",
        "summary_es": "Para qué es la Consola de Admin y cómo accederla. La capacitación operacional es solo para admin.",
        "body_es": [
            {"type": "p", "text":
                "La Consola de Admin es la superficie de control a nivel de operador de la "
                "plataforma. Existe para que el dueño de la plataforma y los operadores de "
                "confianza tengan un solo lugar para administrar el sistema."},
            {"type": "p", "text":
                "Quién la usa: el Dueño de la plataforma y Operador(es) designado(s). No "
                "para personal general."},
            {"type": "p", "text":
                "Cómo accederla: inicie sesión en /admin/login. Las cuentas de admin las "
                "emite directamente el Dueño de la plataforma."},
            {"type": "warn", "text":
                "La capacitación operacional de Admin es el nivel más restringido de la "
                "plataforma. Sus procedimientos, flujos y SOPs internos no se exponen "
                "deliberadamente a usuarios anónimos. Si no tiene una cuenta de admin, este "
                "material no es para usted intencionalmente — es por diseño."},
            {"type": "next", "items": [
                "Si necesita que un admin realice una acción — contacte a su operador directamente",
                "Si no puede iniciar sesión — lea '¿No puede iniciar sesión?' (público)",
            ]},
        ],
    },

    # ── iter205 · Tier 2 · Deep portal-scoped operational training ───
    # Spanish for the deep portal articles. Only visible to authenticated
    # portal-scoped readers (HR/Safety/Shop/Dispatch/PM/Admin).
    "portal-hr": {
        "title_es": "Capacitación del Portal de RH",
        "summary_es": "Lo que RH posee, quién lo usa, y cómo el trabajo conecta con todos los demás portales.",
        "body_es": [
            {"type": "p", "text":
                "RH es el portal de personas-y-tiempo. Es dueño de los registros que prueban "
                "quién trabajó, qué horas se pagaron, quién fue contratado, quién se fue, y "
                "qué capacitación está vigente. Es uno de los portales más interconectados — "
                "todos los demás portales le envían datos, y RH alimenta nómina + cumplimiento "
                "+ cada conversación de auditoría."},
            {"type": "p", "text":
                "Quién lo usa: Personal de RH, Gerentes de RH, roles de soporte de Operaciones. "
                "Lecturas entre portales desde PM (mano de obra de proyecto) y Liderazgo de "
                "Campo (amonestaciones, reconocimientos)."},
            {"type": "bullets", "items": [
                "Verificación de tiempo — comparar Reportes Diarios contra nómina",
                "Orientación de nuevos empleados — papeleo, credenciales, equipo, capacitación",
                "Rendición de cuentas — amonestaciones, coaching, reconocimientos",
                "Registros de capacitación — OSHA, certificación de equipo, cursos internos",
                "Vencimientos de documentos — licencias, tarjetas médicas, certificaciones",
                "Solicitudes de tiempo libre — vacaciones, enfermedad, PTO",
                "Variación de nómina — cuando las horas reportadas no coinciden con el campo",
                "Salida / terminación — pagos finales, devolución de activos",
            ]},
            {"type": "why", "text":
                "RH es donde la documentación del campo se convierte en la fuente de verdad de "
                "la compañía. Un Reporte Diario de un capataz se vuelve un total de horas en "
                "RH. Una amonestación de un superintendente en Liderazgo de Campo se vuelve un "
                "registro de rendición de cuentas en RH. Una inspección QA/QC firmada en PM se "
                "vuelve una señal de patrón de capacitación para RH. Si los registros de RH "
                "están equivocados, la nómina está equivocada — y nómina equivocada es la "
                "forma más rápida de perder una cuadrilla."},
            {"type": "next", "items": [
                "Si es nuevo — lea la guía de rol para personal de RH",
                "Primera tarea usualmente: verificación de tiempo del período actual",
                "Recorra un onboarding de nuevo empleado de principio a fin antes de hacer uno solo",
                "Marque Vencimientos de Documentos — nunca deja de necesitar atención",
            ]},
            {"type": "mistakes", "items": [
                "Aprobar tiempo sin comparar el Reporte Diario (el campo es la verdad)",
                "Cerrar un onboarding antes de que se firme la entrega de equipo",
                "Archivar una amonestación sin la firma del supervisor",
                "Dejar que un vencimiento de licencia/médico/certificación pase de fecha",
            ]},
            {"type": "tip", "text":
                "Los registros de RH son leídos constantemente por PM y Liderazgo de Campo. "
                "Trate cada registro de RH como si el gerente de proyecto y el superintendente "
                "lo leyeran mañana — porque lo harán."},
            {"type": "warn", "text":
                "Si no puede iniciar sesión en RH, no escriba su contraseña de RH en el "
                "formulario de inicio de sesión de otro portal (Seguridad, Taller, etc.). "
                "Cada portal tiene su propio inicio de sesión — pegar la contraseña "
                "equivocada en otro puede bloquear su cuenta temporalmente."},
        ],
    },
    "portal-safety": {
        "title_es": "Capacitación del Portal de Seguridad",
        "summary_es": "Incidentes, acciones correctivas, auditorías, cumplimiento de capacitación — y por qué nada de esto es papeleo.",
        "body_es": [
            {"type": "p", "text":
                "Seguridad es el portal que convierte eventos en rendición de cuentas. Cada "
                "incidente, casi-incidente, acción correctiva, hallazgo de auditoría, "
                "inspección de extintor y revisión de cumplimiento de capacitación vive aquí. "
                "No es un portal de papeleo — cada registro en Seguridad o previno una lesión, "
                "se recuperó de una, o construyó la defensa para una conversación con OSHA "
                "que aún no ha ocurrido."},
            {"type": "p", "text":
                "Quién lo usa: Gerentes de Seguridad, Coordinadores y Oficiales de Seguridad. "
                "Lecturas entre portales desde Liderazgo de Campo (contexto de incidentes), RH "
                "(registros de capacitación) y Admin."},
            {"type": "bullets", "items": [
                "Incidentes — lesiones, daños a propiedad, casi-incidentes, eventos de terceros",
                "Acciones correctivas — qué se arregla, por quién, para cuándo, firmado",
                "Auditorías — recorridos de sitio, auditorías de obra, de subcontratistas",
                "Extintores — inventario, inspecciones mensuales, recarga",
                "Cumplimiento de capacitación — OSHA-10, OSHA-30, equipo, primeros auxilios",
                "Reuniones de seguridad — temas, asistencia, firmas",
                "Planes JHA — Análisis de Riesgo de Trabajo autorizados",
            ]},
            {"type": "why", "text":
                "Los registros de Seguridad son la documentación defensiva más importante que "
                "MASCI produce. Un inspector de OSHA mañana hace dos preguntas: 'Muéstreme su "
                "cumplimiento de capacitación' y 'Muéstreme su último incidente.' Seguridad "
                "es donde viven las respuestas."},
            {"type": "next", "items": [
                "Si es nuevo — lea la guía de rol para Gerente de Seguridad",
                "Recorra un incidente abierto de principio a fin (reporte → investigación → correctivo → cierre)",
                "Saque el reporte actual de cumplimiento de capacitación de su proyecto más activo",
                "Marque Extintores — la cadencia mensual se le adelanta rápido",
            ]},
            {"type": "mistakes", "items": [
                "Cerrar un incidente sin una causa raíz documentada + acción correctiva",
                "Registrar una acción correctiva sin fecha de cierre firmada",
                "Dejar que vencimientos de OSHA-10 pasen en la cuadrilla activa (riesgo de cierre)",
                "Archivar una reunión de seguridad sin las firmas de asistencia",
                "Especular sobre la causa en un reporte de incidente — registre solo hechos observados",
            ]},
            {"type": "tip", "text":
                "Los casi-incidentes son las lecciones más baratas que MASCI obtiene. Anime "
                "a las cuadrillas a reportarlos y documentarlos igual que las lesiones — son "
                "el sistema de alerta temprana."},
            {"type": "warn", "text":
                "Nunca cierre un incidente antes de que la acción correctiva esté verificada "
                "completa. Un registro 'incidente cerrado' con acción correctiva abierta es "
                "la peor pista de auditoría posible."},
        ],
    },
    "portal-shop": {
        "title_es": "Capacitación del Portal de Taller / Flota",
        "summary_es": "Salud del equipo, revisión Pre-Op, flujo de daños, coordinación de mantenimiento — el back-end de operaciones de flota.",
        "body_es": [
            {"type": "p", "text":
                "El Taller es el portal que mantiene la flota funcionando. Cada Pre-Op que un "
                "operador de campo envía fluye aquí. Cada reporte de daño, cada tarea de "
                "mantenimiento, cada pedido de repuestos, cada devolución de equipo — todo "
                "vive en el Taller. El portal existe para asegurar que el equipo correcto esté "
                "operativo en el trabajo correcto a la hora correcta."},
            {"type": "p", "text":
                "Quién lo usa: Mecánicos, Capataz de Taller, Coordinador de Flota. Lecturas "
                "entre portales desde Despacho (a dónde va el equipo) y Liderazgo de Campo "
                "(quién lo tiene ahora)."},
            {"type": "bullets", "items": [
                "Revisión de Pre-Op — cada Pre-Op llega aquí; los fallidos necesitan acción",
                "Reporte de daños — qué se dobló, raspó, rompió, por quién, cuándo",
                "Coordinación de mantenimiento — programado, preventivo, emergencia",
                "Catálogo y pedidos de repuestos — qué hay, qué está pedido, tiempos de entrega",
                "Entrega y devolución de equipo — firmas conjuntas Seguridad + Taller",
                "Firmas — liberar equipo al campo después de reparación",
            ]},
            {"type": "why", "text":
                "Los registros del Taller protegen a todos. La firma de Pre-Op de un operador "
                "muestra que hizo el recorrido; el registro de reparación muestra qué se "
                "encontró y arregló; la firma de devolución muestra que la unidad está "
                "liberada. Si una pieza de equipo causa un incidente, la cadena Pre-Op → Daño "
                "→ Reparación → Firma es toda la defensa."},
            {"type": "next", "items": [
                "Si es nuevo — lea la guía de rol para Taller / Mecánico",
                "Recorra un Pre-Op fallido de principio a fin (reporte de campo → firma de taller)",
                "Abra el Catálogo de Repuestos y aprenda los tiempos de pedido por categoría",
                "Marque el formulario de devolución de equipo — es conjunto con Seguridad",
            ]},
            {"type": "mistakes", "items": [
                "Firmar una unidad de vuelta al servicio antes de verificar la acción correctiva",
                "Pedir repuestos sin confirmar ID de equipo + número de serie",
                "Cerrar reportes de daño sin fotos antes Y después de la reparación",
                "Saltarse la firma conjunta de Seguridad en la devolución de equipo",
            ]},
            {"type": "tip", "text":
                "Cuando llega un Pre-Op fallido, la meta no es ganarle al campo — es "
                "determinar si la unidad es operacionalmente segura ahora. Operadores de "
                "campo que se sienten escuchados reportan problemas más rápido la próxima vez."},
        ],
    },
    "portal-dispatch": {
        "title_es": "Capacitación del Portal de Despacho",
        "summary_es": "Movimiento de equipo, disponibilidad, retenciones, transferencias y coordinación con el campo — aguas arriba de cada decisión sobre activos.",
        "body_es": [
            {"type": "p", "text":
                "Despacho es el portal que coordina el equipo a través de la flota. Su trabajo "
                "es asegurar que el activo correcto esté en el lugar correcto, en el trabajo "
                "correcto, en un estado conocido — y que todos aguas abajo (Taller, Liderazgo "
                "de Campo, PM) vean la misma verdad."},
            {"type": "p", "text":
                "Quién lo usa: Despachadores, Coordinadores de Flota, Supervisión de "
                "Operaciones. Lecturas entre portales desde Taller (salud del equipo), "
                "Liderazgo de Campo (entrega a operador) y PM (asignaciones)."},
            {"type": "bullets", "items": [
                "Disponibilidad — Disponible / Asignado / En-Tránsito / Retenido / En Servicio / Fuera",
                "Eventos de movimiento — transferencias trabajo-a-trabajo con origen · destino · llegada",
                "Retenciones y transferencias — restricción temporal vs reasignación permanente",
                "Reportes de utilización — activos sobre- y sub-desplegados",
                "Registro de eventos operacionales — asignaciones, retenciones, devoluciones",
                "Coordinación de campo — reconciliar vista del sistema con realidad física",
                "Difusión de estado entre portales — sincronización Taller / Campo / PM",
            ]},
            {"type": "why", "text":
                "Despacho está aguas arriba de cada decisión sobre activos que toma el resto "
                "de la plataforma. Cuando Despacho es preciso, el campo no pierde mañanas "
                "buscando equipo, el Taller programa servicio contra el proyecto correcto, "
                "los PMs ven utilización real, y los ejecutivos toman decisiones de flota con "
                "datos honestos."},
            {"type": "next", "items": [
                "Si es nuevo — lea la guía de rol para Despacho",
                "Recorra un evento de movimiento trabajo-a-trabajo (liberar → en-tránsito → llegada)",
                "Aprenda la diferencia entre RETENCIÓN y TRANSFERENCIA — la elección equivocada corrompe la utilización",
                "Marque Disponibilidad — su superficie más referenciada",
            ]},
            {"type": "mistakes", "items": [
                "Reasignar a un nuevo proyecto sin liberar del anterior",
                "Saltarse el estado en-tránsito (salto A→B sin brecha, esconde retrasos)",
                "Usar RETENCIÓN cuando TRANSFERENCIA es correcta (o viceversa) — corrompe la utilización",
                "Olvidar confirmar llegada (activo muestra en-tránsito indefinidamente)",
                "Discutir con reportes de discrepancia de campo en vez de registrar la reconciliación",
            ]},
            {"type": "tip", "text":
                "La mayoría de disputas sobre 'dónde está el equipo X?' terminan en Despacho. "
                "Mientras más limpio el registro de Despacho, más corta la conversación."},
            {"type": "warn", "text":
                "Un activo retenido todavía cuenta contra la utilización del proyecto original; "
                "un activo transferido no. Escoger la operación correcta es cómo se mantiene "
                "honesto el reporte aguas abajo."},
        ],
    },
    "portal-pm": {
        "title_es": "Capacitación del Portal de PM",
        "summary_es": "Supervisión de proyecto, revisión de reportes, documentación laboral, coordinación entre portales — la lente a nivel de proyecto.",
        "body_es": [
            {"type": "p", "text":
                "El portal de PM es la lente a nivel de proyecto. Los PMs ven solo los "
                "registros vinculados a los proyectos que administran — Reportes Diarios, "
                "inspecciones, JHAs, incidentes, registros de Liderazgo de Campo, asignaciones "
                "de equipo, documentación laboral y estado entre portales. Es intencionalmente "
                "filtrado por alcance: cada PM se enfoca en sus propios proyectos."},
            {"type": "p", "text":
                "Quién lo usa: Gerentes de Proyecto y Co-PMs. Lecturas entre portales desde "
                "Liderazgo de Campo (Reportes Diarios), RH (totales de mano de obra), Seguridad "
                "(incidentes), Taller (salud del equipo) y Despacho (asignaciones)."},
            {"type": "bullets", "items": [
                "Tablero del proyecto — filtrado a los proyectos del PM",
                "Revisión de Reportes Diarios — verdad operacional del día",
                "Inspecciones / reuniones / JHAs — registros de seguridad y calidad",
                "Incidentes — cualquier cosa que pasó en el proyecto, cadena completa",
                "Registros de Liderazgo de Campo — amonestaciones, reconocimientos, asistencia",
                "Visibilidad de asignación de equipo — qué está en el proyecto y en qué estado",
                "Documentación laboral — horas → código de costo → conexión con nómina",
                "Visibilidad entre proyectos — solo lo que el alcance permite; admin ve todo",
                "Flujos de reportes — tableros, exploraciones, exportes para dueños",
                "Revisiones de cadencia — ciclos diarios / semanales / mensuales",
            ]},
            {"type": "why", "text":
                "El trabajo de PM es el puente entre operaciones de campo y finanzas de "
                "proyecto. Un Reporte Diario del campo se vuelve un costo de mano de obra en "
                "el tablero de PM. Un incidente se vuelve un riesgo del proyecto. Los PMs son "
                "el único rol con una vista de proyecto lo suficientemente amplia para "
                "detectar desviación y lo suficientemente estrecha para actuar."},
            {"type": "next", "items": [
                "Si es nuevo — lea la guía de rol para PM",
                "Recorra los últimos 7 días de Reportes Diarios de un proyecto (el anclaje de cadencia)",
                "Abra el reporte de documentación laboral y reconcilie contra una nómina semanal",
                "Marque Visibilidad Entre Proyectos — entienda qué muestra y qué no su alcance",
            ]},
            {"type": "mistakes", "items": [
                "Aprobar un Reporte Diario sin verificar que los totales de mano de obra coincidan con el campo",
                "Dejar que un incidente se cierre sin confirmar que la acción correctiva fue verificada",
                "Saltarse la cadencia semanal de revisión (la desviación compone cuando nadie está mirando)",
                "Asumir que admin ve la misma vista filtrada por alcance (admin ve todo)",
                "Revisar reportes una semana tarde — el campo necesita retroalimentación mientras los detalles están calientes",
            ]},
            {"type": "tip", "text":
                "El alcance de PM es basado-en-proyecto, no basado-en-portal. Los registros de "
                "proyectos que no administra están intencionalmente ocultos — eso es un filtro "
                "de ruido, no una pared de seguridad. Si necesita ver el proyecto de otro PM, "
                "pida acceso de lectura a admin."},
            {"type": "warn", "text":
                "No inicie sesión en /pm/login con el correo de otra persona. El alcance "
                "por-PM se aplica por token — usar la cuenta de otro PM hace que el registro "
                "de auditoría apunte a ellos por cada acción que tome."},
        ],
    },
    "portal-admin": {
        "title_es": "Guía de Consola de Admin",
        "summary_es": "El plano de control — personas, roles, salud del sistema, respaldos, gobernanza.",
        "body_es": [
            {"type": "p", "text":
                "Admin es el plano de control a nivel de operador de la plataforma. Es "
                "intencionalmente estrecho en audiencia — típicamente el dueño de la "
                "plataforma y uno o dos operadores de confianza. Admin es dueño de las "
                "superficies que ningún otro portal puede ver: cada usuario, cada plantilla "
                "de rol, cada entrada de auditoría, cada sesión activa, cada respaldo, y las "
                "señales de gobernanza que indican cuándo algo está desviándose."},
            {"type": "p", "text":
                "Quién lo usa: el Dueño de la plataforma y Operador(es) designado(s). No para personal general."},
            {"type": "bullets", "items": [
                "Gestión de usuarios — invitar, asignar rol, suspender, restaurar",
                "Plantillas de rol — definir lo que otorga cada token de portal",
                "Registro de auditoría — cada acción privilegiada, quién/cuándo/qué",
                "Salud del sistema — métricas del backend, profundidad de colas, tasas de error",
                "Sesiones — quién está conectado ahora, revocar si es necesario",
                "Respaldos y restauración — disparadores manuales, programa, punto-en-tiempo",
                "Portabilidad de datos — exportes de grado de cumplimiento por familia de registro",
                "Inventario operacional y gobernanza — detección de desviación entre portales",
                "Observabilidad Sentry — seguimiento de errores, etiquetado de release",
            ]},
            {"type": "why", "text":
                "El trabajo de Admin tiene el radio de impacto más profundo de la plataforma. "
                "Un solo cambio de plantilla de rol se propaga a cada usuario con ese rol. Una "
                "sesión revocada por la fuerza bloquea a alguien en medio de su tarea. El "
                "registro de auditoría es el único lugar donde 'quién cambió qué cuándo' se "
                "registra permanentemente. Admin es intencionalmente solo en inglés porque "
                "los operadores necesitan terminología precisa, no aproximaciones traducidas."},
            {"type": "next", "items": [
                "Si es nuevo en el rol de operador — primero lea Gestión de Usuarios de Admin",
                "Ejecute un respaldo manual y recorra el proceso de restauración en un contexto seguro",
                "Abra el tablero de Inventario Operacional y lea cada elemento de desviación",
                "Marque el Registro de Auditoría — cada acción de operador que tome llega ahí",
            ]},
            {"type": "mistakes", "items": [
                "Modificar una plantilla de rol sin revisar quién tiene ese rol actualmente",
                "Revocar por la fuerza una sesión sin avisarle primero al usuario",
                "Editar registros de usuario sin una razón amigable al registro de auditoría en las notas",
                "Saltarse la revisión de desviación de inventario operacional durante las revisiones semanales",
            ]},
            {"type": "tip", "text":
                "Cuando el trabajo de Admin toca múltiples usuarios (cambios de rol, suspensión "
                "masiva), combínelo con un aviso por Slack/correo. El registro de auditoría "
                "registra la acción; la comunicación registra la intención operacional."},
            {"type": "warn", "text":
                "Los tokens de admin otorgan acceso a cada otro portal automáticamente. Nunca "
                "comparta un token de admin. Si una contraseña de admin necesita rotación, "
                "rote también las concesiones de token de rol."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # FLEET / TRUCKING DVIR · iter251 · Phase 1-5 (ES)
    # ─────────────────────────────────────────────────────────────────
    "fleet-daily-dvir": {
        "title_es": "Inspección Vehicular Diaria del Conductor (DVIR)",
        "summary_es": "Recorra el camión antes de rodar. Marque APROBADO / FALLA / N/D. El sistema asigna la severidad.",
        "body_es": [
            {"type": "p", "text":
                "La DVIR diaria es el recorrido pre-viaje del conductor. Existe para que el conductor, "
                "el Taller y Despacho trabajen con la misma imagen del camión antes de salir del patio. "
                "No es papeleo — es el momento en el que el conductor dice 'esto es lo que veo' y el "
                "Taller lo escucha en el mismo minuto."},
            {"type": "steps", "items": [
                "Abra Campo · toque 'Camionería · DVIR Diaria'",
                "Escriba o seleccione su nombre · la lista se autocompleta tras la primera inspección",
                "Seleccione su unidad de camión · placa / VIN / odómetro / horómetro se prellenan",
                "Recorra el camión — frente, lado del conductor, parte trasera, lado del pasajero. Marque cada elemento APROBADO, FALLA o N/D",
                "Si lleva remolque, toque 'Agregar remolque' y recórralo también",
                "Cualquier elemento marcado FALLA necesita una nota breve (10+ caracteres) y una foto si la tiene",
                "Firme y envíe",
            ]},
            {"type": "why", "text":
                "Una DVIR honesta mantiene segura a la cuadrilla y al camión en la ruta. Un defecto "
                "real detectado a las 6:30 a.m. es un ticket de Taller. El mismo defecto detectado a "
                "80 km/h es una factura de grúa, un día perdido — o peor."},
            {"type": "next", "items": [
                "El Taller ve sus defectos agrupados por camión en segundos",
                "La severidad se asigna automáticamente — los conductores no clasifican · el sistema lo hace",
                "Si algo está Fuera de Servicio, Despacho reasigna la carga",
                "Si es un elemento de Monitoreo, el Taller programa una ventana de reparación",
                "Su nombre queda en la inspección · responsabilidad, no culpa",
            ]},
            {"type": "mistakes", "items": [
                "Marcar N/D en elementos que el camión sí tiene (eje sin refacción, triángulo faltante)",
                "Saltar el recorrido del remolque cuando lleva uno",
                "FALLA sin nota · el Taller no puede actuar sobre 'algo está mal'",
                "Esperar a hacer la inspección cuando ya está en la ruta",
            ]},
            {"type": "tip", "text":
                "Use el consejo 'Por qué importa' dentro del formulario en cada sección — coaching breve, "
                "sin lenguaje de cumplimiento."},
        ],
    },
    "fleet-weekly-lead": {
        "title_es": "Inspección Semanal del Líder",
        "summary_es": "Revisión semanal rápida por el conductor líder, líder de flota o superintendente. Solo elementos de alta señal.",
        "body_es": [
            {"type": "p", "text":
                "La Inspección Semanal del Líder es un segundo par de ojos rápido a cargo de un "
                "conductor líder, líder de flota o superintendente. No es una repetición de la DVIR "
                "diaria. Es la revisión de higiene operacional — quejas recurrentes, elementos que "
                "el líder quiere que el Taller revise, las cosas que un conductor que opera el mismo "
                "camión todos los días deja de notar."},
            {"type": "steps", "items": [
                "Abra Campo · toque 'Semanal · Inspección del Líder'",
                "Seleccione el camión e ingrese su nombre como inspector líder",
                "Recórralo · 9 elementos de alta señal (frenos, espejos, luces, fluidos, cinturones, kit de emergencia, extintor, triángulos, carrocería / pintura)",
                "Firme y envíe",
            ]},
            {"type": "why", "text":
                "Los líderes ven patrones que los conductores no notan porque cambian de camión. Un "
                "recorrido semanal del líder detecta la fuga lenta, la grieta progresiva del espejo, "
                "el sello de puerta que ha estado dejando entrar polvo por tres semanas. Problemas "
                "pequeños · antes de que sean Fuera de Servicio."},
            {"type": "next", "items": [
                "Los defectos pasan por la misma cola del Taller que la DVIR diaria",
                "La gobernanza de severidad es idéntica · FDS / Monitoreo lo decide el sistema",
                "El Taller ve la nota del líder junto a la nota del conductor de la misma mañana",
            ]},
            {"type": "mistakes", "items": [
                "Tratar la inspección semanal del líder como una 'trampa' al conductor — es una alianza",
                "Saltar la semana porque 'nada ha cambiado'",
                "Reutilizar la firma de la semana pasada en vez de firmar nueva",
            ]},
        ],
    },
    "fleet-weekly-emergency": {
        "title_es": "Revisión Semanal de Equipo de Emergencia",
        "summary_es": "Extintor · triángulos · botiquín · EPP · alarma de retroceso. Presente · cargado · dentro de fecha.",
        "body_es": [
            {"type": "p", "text":
                "La Revisión Semanal de Equipo de Emergencia es la confirmación del inspector de que "
                "todo lo que el camión lleva para una emergencia en carretera está realmente ahí, "
                "cargado y no vencido. Es rápida — 17 elementos — y importa más de lo que su tamaño "
                "sugiere. El extintor que no nota faltante en el patio es el que busca a las 2 a.m. "
                "en una zona de trabajo."},
            {"type": "steps", "items": [
                "Abra Campo · toque 'Semanal · Equipo de Emergencia'",
                "Seleccione el camión",
                "Verifique cada elemento: extintor (cargado · sellado · etiqueta vigente) · triángulos reflectivos · botiquín · kit de derrames · alarma de retroceso · luces de emergencia · EPP a bordo",
                "Marque cada uno APROBADO / FALLA / N/D",
                "Los elementos en FALLA necesitan una nota breve · el elemento se enruta al Taller igual que un defecto de DVIR",
                "Firme y envíe",
            ]},
            {"type": "why", "text":
                "Esta es una de las pocas revisiones donde equipo faltante se clasifica automáticamente "
                "como Fuera de Servicio — no puede operar un camión de sitio sin un extintor funcional "
                "o triángulos. La revisión protege a la cuadrilla, al público y la capacidad de la "
                "empresa de responder a un incidente profesionalmente."},
            {"type": "next", "items": [
                "Los elementos fallidos aparecen en la cola del Taller con la severidad correcta ya adjunta",
                "Despacho ve la actualización de estado de la unidad al instante",
                "Seguridad puede revisar el registro de auditoría para cualquier documentación DOT o de zona de trabajo",
            ]},
            {"type": "mistakes", "items": [
                "Marcar 'presente' sin verificar realmente la fecha de la etiqueta del extintor",
                "Saltar el kit de derrames en un camión que transporta equipo hidráulico",
                "Tratar una etiqueta vencida como Monitoreo — el sistema clasifica correctamente automáticamente",
            ]},
        ],
    },
    "fleet-severity-oos-vs-monitor": {
        "title_es": "Fuera de Servicio vs Monitoreo · cómo funciona la severidad",
        "summary_es": "Los conductores no asignan severidad. El sistema lo hace. Lo que importa es reportar con honestidad.",
        "body_es": [
            {"type": "p", "text":
                "Cada defecto en una DVIR, Inspección Semanal del Líder o Revisión de Equipo de "
                "Emergencia se clasifica automáticamente como Fuera de Servicio o Monitoreo. Los "
                "conductores e inspectores no toman esa decisión — solo reportan lo que vieron. La "
                "clasificación viene de una tabla de severidad fija revisada contra los lineamientos "
                "comerciales de FMCSA y DOT, y aprobada por el liderazgo de operaciones."},
            {"type": "p", "text":
                "Fuera de Servicio significa que el camión no rueda hasta que el Taller verifique la "
                "reparación y Despacho confirme el Regreso al Servicio. Monitoreo significa que el "
                "camión es seguro para operar pero el Taller es dueño de la reparación en un ritmo "
                "planificado — sin prisa, sin pánico, pero está siendo rastreado."},
            {"type": "why", "text":
                "Separar el reporte de la severidad es intencional. Quita la presión sobre el conductor "
                "de subreportar ('probablemente está bien') o sobre-reportar ('mejor prevenir…') y quita "
                "la tentación de cualquiera en la cadena de discutir severidad después del hecho. El "
                "conductor reporta. El sistema clasifica. El Taller actúa."},
            {"type": "bullets", "items": [
                "Conductores y líderes · reporte honesto · nota breve · foto si la tiene",
                "Sistema · severidad según el elemento y la descripción · tabla publicada",
                "Taller · ve el camión agrupado por unidad · nota del conductor + foto + severidad en un solo lugar",
                "Despacho · ve la disponibilidad (FDS / Reparación en curso / Disponible)",
                "Seguridad · lee el registro de auditoría · registro de reparación · referencia regulatoria cuando aplica",
            ]},
            {"type": "tip", "text":
                "Monitoreo no es castigo. Monitoreo es 'lo sabemos · está rastreado · está programado'. "
                "Un camión con tres elementos de Monitoreo puede rodar todo el día. Un camión con un "
                "elemento FDS se queda estacionado hasta que el Taller diga lo contrario."},
            {"type": "mistakes", "items": [
                "Llamar a un defecto Monitoreo 'porque necesitamos el camión hoy' · el sistema clasifica, no el operador",
                "Ocultar un defecto para evitar FDS · pone en riesgo a la cuadrilla y aparece después como una reparación mayor",
                "Discutir severidad con el Taller · la severidad es una tabla publicada · la conversación es sobre la reparación, no la clasificación",
            ]},
        ],
    },
    "fleet-repair-lifecycle": {
        "title_es": "Ciclo de Reparación de Flota · Taller · Despacho · Seguridad",
        "summary_es": "Defecto → Taller reconocido → Reparado → Regreso al Servicio por Despacho. Un registro · tres ámbitos.",
        "body_es": [
            {"type": "p", "text":
                "Cada defecto de Flota — DVIR, Inspección Semanal del Líder o Equipo de Emergencia — "
                "fluye por el mismo ciclo de cuatro pasos. Taller, Despacho y Seguridad ven el mismo "
                "registro en cada paso, con el alcance que cada rol realmente ejerce."},
            {"type": "steps", "items": [
                "Abierto · el defecto está recién del conductor/inspector. El Taller lo ve en la cola de la unidad.",
                "Taller reconocido · el mecánico abrió la tarjeta. Opcional — la mayoría de los talleres se saltan esto y van directo a la reparación.",
                "Reparado · el Taller registró el panel de reparación (nombre del mecánico · notas · fotos si aplica · marca de tiempo).",
                "Regresado al servicio · Despacho confirmó que la unidad es segura para rodar. Intencional · confirmado con casilla de verificación.",
            ]},
            {"type": "why", "text":
                "Los cuatro pasos son deliberados. El Taller es dueño de la llave inglesa. Despacho es "
                "dueño de la decisión operacional de poner el camión de vuelta en rotación. Seguridad "
                "lee el registro. Ninguna persona cierra el ciclo sola."},
            {"type": "bullets", "items": [
                "Taller · usa la nota y la foto del conductor para saber exactamente qué revisar",
                "Despacho · ve Disponible / FDS / Reparación-en-curso sin escanear una lista",
                "Seguridad · lee el registro de auditoría completo · quién · cuándo · qué cambió · estado anterior/nuevo",
            ]},
            {"type": "next", "items": [
                "Después de que el Taller marque reparado · el estado de la unidad pasa a 'Reparación en curso' (esperando RTS)",
                "Despacho ve la unidad en su página de visibilidad con un botón 'Regresar al Servicio'",
                "Después del RTS · el estado de la unidad regresa a Disponible · el registro de auditoría queda sellado con ambos nombres",
            ]},
            {"type": "mistakes", "items": [
                "El Taller marca reparado pero Despacho nunca confirma — la unidad se queda en 'esperando RTS' indefinidamente",
                "Nota de reparación más corta que 'cambié la pieza' — Seguridad no tiene registro de qué se inspeccionó",
                "Saltar el panel del Taller y editar el defecto directamente · rompe el registro de auditoría",
            ]},
        ],
    },
    "fleet-return-to-service": {
        "title_es": "Regreso al Servicio · confirmación de Despacho",
        "summary_es": "El Taller arregló el camión. Despacho confirma que puede rodar. Intencional · con marca de tiempo · auditado.",
        "body_es": [
            {"type": "p", "text":
                "El Regreso al Servicio es el momento en que Despacho le dice al sistema 'este camión "
                "está de vuelta en rotación'. Sucede solo después de que el Taller haya registrado una "
                "reparación · nunca automáticamente · nunca como efecto secundario de cerrar algo más."},
            {"type": "steps", "items": [
                "Abra la vista de Flota desde el portal de Despacho",
                "Encuentre la unidad · muestra 'Esperando RTS' junto con el registro de reparación del Taller",
                "Toque 'Regresar al Servicio' en el defecto",
                "Revise la nota de reparación del Taller (y las fotos, si el Taller las adjuntó)",
                "Ingrese su nombre · agregue una nota opcional de Despacho",
                "Marque la casilla de confirmación — 'He revisado el registro de reparación del Taller y confirmo que esta unidad es segura para regresar al servicio'",
                "Toque Regresar al Servicio",
            ]},
            {"type": "why", "text":
                "El Taller es dueño de la llave inglesa pero Despacho es dueño de la decisión operacional. "
                "Despacho es el rol que sabe si la carga es realista, si la ruta tiene sentido para una "
                "unidad recién reparada, y si alguien necesita un aviso. La casilla de confirmación "
                "intencional no es burocracia · es el momento en el que la plataforma registra que un "
                "humano tomó una decisión, no que un botón se tocó camino a otro lugar."},
            {"type": "next", "items": [
                "El estado de la unidad pasa a Disponible · los conductores pueden tomarla",
                "El registro de auditoría captura: quién · cuándo · estado_anterior · estado_nuevo · nota del Taller · nota de Despacho",
                "Seguridad puede leer el registro completo · DVIR → reparación del Taller → RTS de Despacho",
            ]},
            {"type": "mistakes", "items": [
                "Confirmar RTS sin leer la nota del Taller · pierde el contexto operacional",
                "Saltar la nota de confirmación cuando algo es inusual · el contexto breve ayuda a Seguridad después",
                "Intentar RTS en una unidad que el Taller aún no ha reparado · el sistema bloquea esto · por una buena razón",
            ]},
        ],
    },
}


# iter279 · Sequence #8 portals i18n closure — merge the 33 ES portal
# entries authored in `translations_es_iter279.py`. Kept in a separate
# module to keep this file manageable; same load-time effect.
from .translations_es_iter279 import EXTRA_ES as _EXTRA_ES_ITER279  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER279)

# iter280 · Sequence #8 knowledge i18n closure — merge the 19 ES
# knowledge-section entries.
from .translations_es_iter280 import EXTRA_ES as _EXTRA_ES_ITER280  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER280)

# iter281 · Sequence #8 roles + reliability i18n closure (final cluster) —
# merge the 4 ES entries: 3 roles + 1 reliability.
from .translations_es_iter281 import EXTRA_ES as _EXTRA_ES_ITER281  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER281)

# iter297 · Operational `why-*` knowledge ES translation pass — merge the
# 7 `why-*` knowledge-section entries (operational philosophy surfaces
# re-classified from "explicit-leave" to "translated" per operator
# direction in the iter296+iter297 bundle).
from .translations_es_iter297 import EXTRA_ES as _EXTRA_ES_ITER297  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER297)

# iter414 · Phase 18 · DLS operational unification — Help-Search closure.
# 7 new DLS-era articles (driver shift start · assignment issuance ·
# haul types · lifecycle states · PM haul activity · operational
# attention · health summary) with field-accurate operational Spanish.
from .translations_es_iter414 import EXTRA_ES as _EXTRA_ES_ITER414  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER414)

# iter417 · Phase 20.0 · Operational Attachments Foundation —
# coaching shipped at the same time as the primitive.
from .translations_es_iter417 import EXTRA_ES as _EXTRA_ES_ITER417  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER417)

# iter418-421 · Phases 20.1/21.0/22.0/23.0 · Continuity expansion —
# breakdown proof · operational exceptions · shop recovery · offline.
from .translations_es_iter418 import EXTRA_ES as _EXTRA_ES_ITER418  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER418)

# iter423 · Phase 25 · Shop Operational Cognition Convergence —
# four new bilingual coaching articles surfaced by the Shop Hub sections.
from .translations_es_iter423 import EXTRA_ES as _EXTRA_ES_ITER423  # noqa: E402
TRANSLATIONS_ES.update(_EXTRA_ES_ITER423)
