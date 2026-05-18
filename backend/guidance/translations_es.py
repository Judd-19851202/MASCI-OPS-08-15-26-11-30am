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
    "onboard-leadership-first-week": {
        "title_es": "Liderazgo de Campo — Primera Semana",
        "summary_es": "Qué hace un nuevo Superintendente o Capataz en su primera semana en MASCI.",
        "body_es": [
            {"type": "p", "text":
                "Bienvenido al Liderazgo de Campo. Este portal es la superficie de operaciones diarias "
                "para Superintendentes, Capataces, Líderes de Campo y Supervisión de Operaciones. "
                "Esto es lo que debe hacer su primera semana."},
            {"type": "steps", "items": [
                "Día 1 — Visite /leadership/login y pida la contraseña de liderazgo a la oficina o a su supervisor directo.",
                "Día 1 — Lea el artículo '¿Qué hace el Liderazgo de Campo?' (enlace en la parte inferior de la página de inicio de sesión).",
                "Día 2 — Envíe su primer Reporte Diario en un trabajo real (no de prueba). Fotos. Cuadrillas. Horas. Condiciones.",
                "Día 2-3 — Recorra el ciclo completo de un Pre-Op de equipo desde el operador → taller → de vuelta al campo. Entienda qué pasa cuando usted firma.",
                "Día 3-4 — Entregue una pieza de EPP / equipo usando Equipment Checkout. El registro es la prueba.",
                "Día 4-5 — Dirija una Charla de Seguridad / Toolbox Talk y envíe el formulario de asistencia.",
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
                "Agregue /leadership a la pantalla de inicio de su teléfono el Día 1. Casi toda "
                "tarea de Liderazgo de Campo se hace en un teléfono en el sitio — instalar el "
                "atajo temprano le ahorra 5-10 toques por envío el resto de su carrera aquí."},
            {"type": "warn", "text":
                "El Liderazgo de Campo usa una CONTRASEÑA COMPARTIDA — igual que un código de "
                "despacho de cuadrilla. No comparta la contraseña fuera del equipo de liderazgo. "
                "La rendición de cuentas por cada registro pasa al nivel del registro (su firma "
                "en el formulario), no en la puerta."},
            {"type": "next", "items": [
                "Marque este artículo — también es la respuesta a 'qué hago después' durante el primer mes",
                "Lea 'Enviando un Reporte Diario Defendible' — el más referenciado de todos",
                "Hable con su PM sobre los proyectos a los que será asignado",
            ]},
        ],
    },

    "tshoot-leadership-login": {
        "title_es": "No puedo iniciar sesión en Liderazgo de Campo",
        "summary_es": "Soluciones rápidas cuando /leadership/login no funciona.",
        "body_es": [
            {"type": "p", "text":
                "El Liderazgo de Campo usa una contraseña compartida (no su correo + contraseña "
                "individual). Si no puede entrar, siga estos pasos en orden."},
            {"type": "steps", "items": [
                "Confirme que está en /leadership/login (la puerta dedicada del portal). La contraseña compartida funciona ahí.",
                "Verifique la ortografía y el estado de mayúsculas — las contraseñas de liderazgo distinguen mayúsculas.",
                "Si ya tiene un token Admin o PM (inició sesión en /admin/login o /pm/login antes en esta sesión), la puerta de liderazgo los acepta automáticamente — no necesita la contraseña de liderazgo.",
                "Borre sessionStorage y recargue la página si un token previo está interfiriendo — cierre la pestaña del navegador y vuelva a abrir /leadership/login.",
                "Pida la contraseña de liderazgo actual a su supervisor directo o a la oficina. La contraseña puede haber rotado.",
            ]},
            {"type": "why", "text":
                "La contraseña compartida de liderazgo es el modelo correcto para cuadrillas "
                "porque funciona igual que un código de despacho o una llave del taller — todo "
                "líder necesita entrar, y la identidad individual queda capturada al nivel de "
                "firma del formulario. Si perdió la contraseña, casi siempre la oficina puede "
                "dársela en 30 segundos."},
            {"type": "warn", "text":
                "NO escriba la contraseña de liderazgo en el formulario de inicio de sesión de "
                "otro portal (/hr/login, /pm/login, etc.) — esos esperan correo + contraseña "
                "individual, y pegar la contraseña compartida ahí puede bloquear su cuenta "
                "individual temporalmente después de varios intentos."},
            {"type": "tip", "text":
                "Una vez que inicie sesión correctamente, su pestaña del navegador guarda un "
                "token de 12 horas. No necesita volver a escribir la contraseña ese mismo "
                "turno a menos que cierre la pestaña."},
        ],
    },

    "portal-leadership-identity": {
        "title_es": "Portal de Liderazgo de Campo — Resumen",
        "summary_es": "Para qué es el Liderazgo de Campo y cómo accederlo. La capacitación operacional requiere inicio de sesión de liderazgo.",
        "body_es": [
            {"type": "p", "text":
                "El Portal de Liderazgo de Campo es la superficie de operaciones diarias para "
                "Superintendentes, Capataces, Líderes de Campo y Supervisión de Operaciones — "
                "la gente que dirige las cuadrillas en el campo."},
            {"type": "p", "text":
                "Quién lo usa: Superintendentes, Capataces, Líderes de Campo, Supervisión de Operaciones."},
            {"type": "p", "text":
                "Cómo accederlo: inicie sesión en /leadership/login con la contraseña de "
                "liderazgo compartida que le da la oficina o su supervisor directo. Los "
                "tokens de Admin y PM también satisfacen la puerta de liderazgo."},
            {"type": "warn", "text":
                "La capacitación operacional de Liderazgo de Campo (procedimientos, flujos, "
                "SOPs internos) está restringida a usuarios autenticados de liderazgo. El "
                "contenido a nivel de flujo no es visible para usuarios anónimos."},
            {"type": "next", "items": [
                "Si no puede iniciar sesión — lea 'No puedo iniciar sesión en Liderazgo de Campo' (público)",
            ]},
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
        "title_es": "Reuniones de Seguridad y Charlas",
        "summary_es": "Firme. Escuche. El registro es su firma.",
        "body_es": [
            {"type": "p", "text": "Una charla de seguridad (o reunión de seguridad) es una junta corta al inicio del día o turno. Tema del día, peligros, cualquier cosa nueva. Usted firma la lista — así queda registrado que asistió y entendió."},
            {"type": "steps", "items": [
                "Llegue a tiempo — usualmente son 5 a 15 minutos.",
                "Escuche el tema. Pregunte si algo no le quedó claro.",
                "Firme la lista de asistencia cuando le llegue (o escanee el QR / envíe por el formulario público).",
                "Si vio un peligro durante la charla, hable antes de que la cuadrilla se separe.",
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
                "Reunión de Seguridad / Charla — Firma + lista de asistencia",
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
                "Charlas de seguridad — temas, asistencia, firmas",
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
                "Archivar una charla sin las firmas de asistencia",
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
}
