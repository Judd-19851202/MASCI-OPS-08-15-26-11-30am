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
}
