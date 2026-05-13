// Spanish translations for every Training Hub lesson body.
// Structure is {slug: {title_es, why_es, steps_es[], tips_es[], cheatSheet_es[]}}.
// Merged into the main LESSONS array by training.js so TrainingTrack.jsx can
// call `pick(lesson, 'title')` and get the *_es variant when lang === "es".

export const LESSON_TRANSLATIONS_ES = {
  // ============================================================
  // FIELD
  // ============================================================
  "field-01-hub-navigation": {
    title_es: "Lección 1 — Navegando el Hub MASCI",
    why_es: "Todo empieza aquí. Si encuentra el Hub en su teléfono, puede llenar cualquier formulario que la compañía necesite en menos de 2 minutos.",
    steps_es: [
      "Apunte la cámara de su teléfono al código QR dentro del tráiler — el Hub MASCI se abre en su navegador automáticamente. Sin aplicación que instalar, sin inicio de sesión para los formularios de Campo.",
      "En la página principal verá 8 mosaicos: Campo, QA/QC, Seguridad, Proyectos, Portal del PM, Taller, Centro de Capacitación y Admin. Campo, QA/QC y Seguridad son los tres que usará todos los días.",
      "Toque el botón EN/ES en la esquina superior derecha para cambiar el idioma — su elección se recuerda en este teléfono.",
      "Toque 'Company Info' en la esquina superior derecha para ver la dirección y teléfonos de MASCI si necesita llamar a la oficina desde el campo.",
      "Toque 'Agregar a pantalla de inicio' en el menú del navegador una vez — después el Hub se abre como una aplicación real con un toque.",
    ],
    tips_es: [
      "Si el GPS no funciona al primer intento, escriba la dirección en el campo Ubicación — mismo resultado.",
      "El Hub funciona sin conexión para leer, pero enviar un formulario necesita señal — guarde y reintente cuando tenga barras.",
    ],
    cheatSheet_es: [
      "Escanee QR → Hub abre → Elija Campo o Seguridad → Llene → Firme → Envíe.",
      "Idioma arriba a la derecha. Company Info al lado.",
    ],
  },
  "field-02-daily-report": {
    title_es: "Lección 2 — Reportes Diarios",
    why_es: "El Reporte Diario es la memoria de la compañía sobre lo que pasó hoy. Sin Reporte Diario no hay prueba de horas de cuadrilla, entregas de material, subs en sitio, equipo usado, ni progreso. Lo protege a usted y a la compañía en una disputa.",
    steps_es: [
      "Desde el Hub, toque Campo → Reportes Diarios → 'Archivar Primer Reporte' (o 'Nuevo Reporte').",
      "Elija su Trabajo MASCI del selector — el número de proyecto, nombre, ubicación y cliente se autocompletan. Elija 'Trabajo Personalizado' solo si su trabajo aún no está en la lista (raro).",
      "Toque 'Usar GPS' para autocompletar Ubicación. El clima se carga automáticamente del pronóstico de hoy. Si el GPS falla, escriba la dirección.",
      "Información General: responda Sí/No sobre Retrasos, Clima, Accidentes, Lesiones. Si CUALQUIER respuesta es Sí, aparece una caja roja de Escalación de Seguridad — llénela completamente o no podrá enviar.",
      "Cuadrillas MASCI en Sitio: toque 'Agregar Miembro de Cuadrilla'. La lista está precargada — escriba un nombre y elija. Ingrese Hora de Inicio / Fin. El almuerzo resta 30 min automáticamente. Las horas se calculan solas.",
      "Subcontratistas en Sitio: mismo patrón — quién, cuántos trabajadores, cuántas horas, qué hicieron.",
      "Visitantes del Sitio, Registro de Equipo, Entregas de Materiales, Registro de Actividad / Producción: llene lo que aplique hoy. Omita secciones que no apliquen.",
      "Fotos: mínimo 6 requeridas. Tómelas mientras camina por el sitio — inicio, progreso, cualquier problema, final.",
      "Preparado Por + Superintendente firman abajo. Toque 'Enviar Reporte Diario'. Verá la pantalla de Gracias.",
    ],
    tips_es: [
      "Si se reportó un accidente o lesión, la app BLOQUEA el envío hasta que (1) Seguridad fue notificada Y (2) se presentó un Reporte de Incidente. No intente atajos — llene primero el Reporte de Incidente, luego regrese.",
      "Toque 'Guardar Borrador' en cualquier momento si una junta lo interrumpe — su progreso persiste en este teléfono.",
      "Cuadrillas de habla hispana: ponga el idioma en ES, llene en español. La app traduce al inglés automáticamente antes de guardar a la oficina.",
    ],
    cheatSheet_es: [
      "Mínimo 6 fotos. GPS + clima automáticos.",
      "Si Sí en Accidente/Lesión → Reporte de Incidente PRIMERO, luego Reporte Diario.",
      "Preparado Por + Superintendente firman ambos.",
    ],
  },
  "field-03-equipment-preop": {
    title_es: "Lección 3 — Inspección Pre-Operación de Equipo",
    why_es: "OSHA 1926 requiere un recorrido diario antes de operar equipo pesado. El Pre-Op lo protege de lesionarse con una máquina mala conocida y protege a la compañía de operar una unidad hasta destruirla. Un FALLO aquí marca la unidad FUERA DE SERVICIO hasta que el taller la libere.",
    steps_es: [
      "Hub → Campo → Pre-Op de Equipo.",
      "Elija su Trabajo y Tipo de Equipo. Busque en 'Unidades guardadas' la unidad que está operando — marca, modelo y serie se autocompletan.",
      "Ingrese Horómetro U Odómetro (uno requerido). Ingrese su nombre completo.",
      "Recorra la unidad. Para cada punto del checklist, toque Aprobado, Falla o N/A. Un FALLO requiere descripción (mín 10 caracteres) Y foto del defecto.",
      "Fallas de seguridad mayor (frenos, dirección, cinturón, ROPS, bocina) activan el modal rojo 'ALTO — Falla de Seguridad Mayor'. La unidad queda FUERA DE SERVICIO — NO la opere. Avise al supervisor, notifique al taller, ponga tarjeta de bloqueo.",
      "Fallas críticas de fluido (sin aceite, sin refrigerante, fuga de hidráulico) bloquean el envío hasta que se rellene el fluido y el punto cambie de Falla a Aprobado.",
      "Agregue notas de deficiencias, acciones correctivas y fotos del equipo abajo.",
      "Firma del Operador: lea la certificación, firme, toque 'Enviar Inspección'.",
    ],
    tips_es: [
      "Haga el Pre-Op con el motor apagado primero (recorrido visual), luego enciéndalo y revise medidores, frenos e hidráulicos.",
      "Si omite un punto como N/A, la app lo acepta — no mienta en un Aprobado. El taller revisa cada FALLO y verá un patrón.",
      "Una vez que el taller firma un FALLO, la unidad queda LIBERADA PARA OPERAR y la verá en el tablero de equipo.",
      "Cada FALLO o Pre-Op fuera de servicio envía correo automático a CADA mecánico activo del panel de Shop Users — en menos de 60 segundos la oficina de partes lo sabe. El asunto lleva 'EQUIPMENT FAIL · …' al frente para que sea difícil de ignorar.",
      "Su Pre-Op recibe un Doc ID como PRE-2026-00042 — impreso en el PDF y en el asunto del correo. Si el taller le llama, dele ese número.",
    ],
    cheatSheet_es: [
      "Motor apagado → recorrido → motor encendido → revise fluidos y medidores.",
      "FALLO = unidad fuera de servicio + foto requerida.",
      "Puntos de seguridad mayor = ALTO, no opere.",
    ],
  },
  "field-material-calculators": {
    title_es: "Lección 4 — Calculadoras de Materiales",
    why_es: "Las cantidades adivinadas cuestan dinero. Pedir de menos → entrega al día siguiente, cuadrilla parada, cronograma roto. Pedir de más → yardas desperdiciadas que se le cobran al trabajo. Las Calculadoras de Materiales le dan estimaciones precisas en segundos, con las mismas fórmulas que usa la oficina, para que el número que pide coincida con el número de la factura.",
    steps_es: [
      "Hub → Campo → Calculadoras de Materiales. Verá seis tarjetas, una por calculadora: Agregado, Asfalto, Concreto, Carga de Camión, Rendimiento / Desperdicio y Conversión Toneladas ↔ CY.",
      "Elija la calculadora correcta para el trabajo. Agregado (base, #57, riprap) → toneladas por área + profundidad. Asfalto → toneladas de HMA por área + profundidad + densidad de mezcla. Concreto → yardas cúbicas para losas, zapatas, columnas, muros. Carga de Camión → cuántas cargas pedir según tamaño del camión. Rendimiento / Desperdicio → ajusta el número limpio para derrames y sobre-vertido reales. Toneladas ↔ CY → conversión rápida de unidades.",
      "Ingrese dimensiones en pies y pulgadas como las lee el campo. La calculadora hace los cálculos — no necesita convertir a decimales primero.",
      "Lea el resultado y SIEMPRE REDONDEE HACIA ARRIBA al pedir. La línea 'Pedir esta cantidad' en cada calculadora ya incluye un pequeño margen de desperdicio; trátela como la cantidad mínima a pedir.",
      "Toque 'Guardar / Registrar Uso' para registrar la estimación contra el trabajo. El PM y el Admin ven quién calculó qué y cuándo — esto alimenta el seguimiento de desperdicio y rendimiento de la oficina.",
      "Cambie el idioma con el botón EN/ES arriba. Cada etiqueta, fórmula y línea de resultado es bilingüe.",
    ],
    tips_es: [
      "En caso de duda, REDONDEE HACIA ARRIBA — quedar corto en una colada cuesta 10× más que estar un poco sobre.",
      "La calculadora NO reemplaza el diseño de mezcla del proyecto ni el take-off oficial. Es una verificación de campo, no la cantidad oficial.",
      "Guarde / Registre Uso cada vez. El patrón de los registros es cómo los PMs detectan qué cuadrillas piden de menos o de más constantemente.",
    ],
    cheatSheet_es: [
      "Seis calculadoras: Agregado · Asfalto · Concreto · Carga de Camión · Rendimiento/Desperdicio · Toneladas↔CY.",
      "Ingrese pies y pulgadas como las lee el campo. La app hace los cálculos.",
      "REDONDEE HACIA ARRIBA al pedir. Toque 'Guardar / Registrar Uso' para que la oficina vea la estimación.",
    ],
  },
  "field-qaqc-inspections": {
    title_es: "Lección 5 — Inspecciones de QA / QC",
    why_es: "Los problemas de calidad detectados ANTES de la colada o ANTES de que el subcontratista deje el sitio cuestan una fracción de lo que cuesta arreglarlos después. El módulo QA/QC documenta la inspección, captura fotos y firmas, genera un PDF, y lo envía directamente al Gerente de Proyecto asignado — cada registro vinculado a un trabajo, una estación, y un inspector. Esta es su evidencia para auditorías del dueño, disputas con subs y reclamos de garantía.",
    steps_es: [
      "Hub → QA / QC. Verá los tipos de inspección disponibles — actualmente tres: Inspección de Formaleta de Concreto, Inspección de Acero de Refuerzo, e Inspección de Trabajo del Subcontratista. Más formularios se agregan a medida que el sistema crece.",
      "Toque la inspección que necesita. Elija su Trabajo MASCI del selector — número de proyecto, nombre, ubicación, cliente, Y el Gerente de Proyecto asignado se llenan automáticamente. El correo del PM se captura automáticamente para que el reporte se envíe a la persona correcta.",
      "Toque el botón GPS al lado de Ubicación para autollenar la dirección del área de trabajo desde el GPS de su teléfono.",
      "Subcontratista / Cuadrilla: lista buscable con todos los subs y vendedores en el sistema. Si el suyo no está, toque 'Agregar nuevo' y créelo en el momento.",
      "Área de Trabajo / Estación es REQUERIDO en cada formulario QA/QC — sea específico: 'Tablero del puente, estribo norte EST 100+05', no 'en el puente'.",
      "Solo Inspecciones de Formaleta de Concreto: ingrese Diseño de Mezcla (ej. 4000 PSI Clase IV), Yardas Pedidas (CY), y Vendedor de Concreto (lista buscable — misma lista de vendedores, agregue nuevo si necesario).",
      "Recorra la lista de verificación. Cada punto recibe Aprobado, Falla o N/A. Cada FALLA requiere una nota de deficiencia describiendo qué está mal.",
      "Fotos: mínimo 3 requeridas. Capture el área de trabajo, cualquier deficiencia y la condición general.",
      "Notas de Inspección / Descripción, Deficiencias, Acciones Correctivas Requeridas — llene con detalle. La firma del Representante del Sub es opcional pero recomendada cuando el trabajo es rechazado.",
      "El Inspector firma. Envíe. El PDF se genera y se envía por correo al PM asignado automáticamente; el registro aparece en el Portal del PM y en la Consola del Admin.",
    ],
    tips_es: [
      "Si tiene una Falla, tome una foto del defecto con una cinta métrica u otra referencia en el cuadro. 'Asentamiento muy alto' por sí solo es difícil de defender; 'Asentamiento de 7 pulgadas en una especificación de 4 pulgadas, foto adjunta' es a prueba de balas.",
      "El PM solo ve los registros QA/QC en trabajos donde está asignado. Elija el trabajo correcto — trabajo equivocado = el PM equivocado recibe el correo.",
      "Use el formulario incluso cuando el trabajo pase limpiamente. Un registro de aprobación limpia del trabajo de un sub lo protege cuando el sub luego dice 'no lo hicimos así'.",
    ],
    cheatSheet_es: [
      "Tres tipos de inspección hoy (más por venir): Formaleta de Concreto · Acero · Trabajo del Subcontratista.",
      "Elija el trabajo → el PM se autollena. Use GPS para ubicación. Área de Trabajo requerida.",
      "Mín. 3 fotos. Cada FALLA necesita una nota. El Inspector firma. El PM recibe el PDF automáticamente.",
    ],
  },
  "field-04-safety-meeting": {
    title_es: "Lección 6 — Reuniones de Seguridad (Charlas de Caja)",
    why_es: "Junta diaria requerida antes de comenzar el trabajo. Documenta que la cuadrilla fue informada sobre los peligros de hoy — crítico si OSHA aparece o pasa un incidente después.",
    steps_es: [
      "Hub → Seguridad → Reuniones de Seguridad → Nueva Reunión.",
      "Llene proyecto, fecha/hora, Conducida Por, Categoría del Tema.",
      "Toque 'Biblioteca de Temas — Elija un tema para prellenar' y busque (ej. 'zanja', 'sílice', 'calor'). Más de 80 temas prellenados con peligros, puntos clave, referencias y acciones. O toque 'Tema Personalizado' para escribir el suyo.",
      "Revise / edite los Peligros, Notas de Discusión, Referencias y Acciones.",
      "Agregue a cada asistente — cada uno firma para confirmar que estuvo.",
      "El Conductor firma abajo. Envíe.",
    ],
    tips_es: [
      "Haga esto ANTES de que la cuadrilla levante una pala — no después. La documentación vence a la memoria.",
      "Rote quién dirige la reunión cada semana — construye pertenencia en la cuadrilla.",
    ],
    cheatSheet_es: [
      "Más de 80 temas prellenados. Elija uno, edite, obtenga firmas.",
      "Cada asistente firma. Conductor firma. Envíe.",
    ],
  },
  "field-05-jhp": {
    title_es: "Lección 7 — Plan de Peligros del Trabajo (JHP)",
    why_es: "Los JHPs de MASCI se preparan antes de que comience el trabajo, por el Departamento de Seguridad, los Gerentes de Proyecto y el liderazgo — basados en el alcance del trabajo, condiciones del sitio, control de tráfico (MOT), factores ambientales y peligros conocidos del proyecto. Así los peligros se identifican y controlan ANTES de que la cuadrilla pise el sitio. Un JHP bien hecho es una de las mejores herramientas que tenemos para prevenir incidentes y eliminar la improvisación en el campo.",
    steps_es: [
      "Las cuadrillas NO crean JHPs. Los JHPs son documentos específicos del proyecto, preparados con anticipación por Seguridad, los Gerentes de Proyecto y el liderazgo, antes de que llegue cualquier cuadrilla.",
      "Cada JHP cubre: peligros identificados en todo el proyecto, ubicaciones de peligros por número de estación, controles requeridos para cada peligro, riesgos ambientales y específicos del sitio, peligros de MOT (control de tráfico), y peligros del equipo y de la operación.",
      "Cada paquete JHP viene con dos documentos: (1) el DOCUMENTO JHP — lista completa de peligros, ubicaciones por estación, controles requeridos y prácticas seguras; (2) la HOJA DE PELIGROS — tipo de peligro y nivel de amenaza, ubicación exacta, controles requeridos y notas adicionales donde se necesiten.",
      "Antes de comenzar el trabajo: revise el JHP, entienda los peligros específicos de su área de trabajo, y siga cada control listado.",
      "Si algo no está claro o las condiciones NO coinciden con el plan: pregunte, y use la Autoridad para Suspender el Trabajo. No improvise.",
      "Esto NO es un formulario que se llena en el campo. Es un sistema de seguridad pre-construido para protegerlo antes de que comience el trabajo.",
    ],
    tips_es: [
      "El JHP existe para que cada miembro de la cuadrilla entienda los riesgos ANTES de encontrarlos. Úselo, sígalo, y hable si algo no coincide con lo documentado.",
      "Autoridad para Suspender el Trabajo: cada miembro la tiene. Sin preguntas, sin disciplina — si las condiciones en el sitio no coinciden con el JHP, pare.",
    ],
    cheatSheet_es: [
      "Los JHPs los prepara Seguridad / PM / Liderazgo — no la cuadrilla.",
      "Dos documentos por trabajo: JHP + Hoja de Peligros (con números de estación).",
      "Revise antes del trabajo. Siga los controles. Pare el Trabajo si las condiciones cambian.",
    ],
  },
  "field-06-incident": {
    title_es: "Lección 8 — Reportes de Accidente / Incidente",
    why_es: "El momento que algo sale mal, este es el formulario. Cuasi-accidente, primeros auxilios, médico, DART, fatalidad — cada nivel se documenta. Causa raíz, testigos, acciones correctivas — todo en un registro.",
    steps_es: [
      "ASEGURE LA ESCENA PRIMERO. Consiga atención médica a los trabajadores lesionados. Llame al 911 si es grave. LUEGO abra la app.",
      "Hub → Seguridad → Reportes de Incidentes → Nuevo Reporte.",
      "Llene fecha, hora, ubicación, Reportado Por, Supervisor.",
      "Elija Tipo de Incidente (Lesión, Daño a Propiedad, Vehículo, Golpe a Servicio, Ambiental, Público, Otro) y Nivel de Severidad (Cuasi-Accidente → Fatalidad). El nivel determina el reporte a OSHA.",
      "Sección Persona Involucrada: nombre, rol, empleador, años de experiencia, parte del cuerpo afectada, naturaleza de la lesión, tratamiento, centro médico, si fue enviado a casa.",
      "Descripción: secuencia de eventos, qué cambió, qué pasó. Sea factual, sea específico.",
      "Análisis de Causa Raíz: marque cada categoría contribuyente (EPP, capacitación, procedimiento, supervisión, equipo, comunicación, fatiga, orden, clima).",
      "Agregue a cada testigo con una declaración corta mientras está fresco.",
      "Acciones Inmediatas + Acciones Correctivas a Largo Plazo. Quién es responsable del seguimiento, para cuándo.",
      "Notificaciones Realizadas: Gerente de Seguridad, Gerente de Proyecto, Contratista General, Dueño, OSHA si catastrófico.",
      "Agregue fotos de la escena, equipo, ambiente.",
      "Reportero + Supervisor firman. Envíe.",
    ],
    tips_es: [
      "Un 'Cuasi-Accidente' con potencial severo se marca nivel 'Cuasi-Accidente' + describa el potencial en la descripción. No suba el nivel.",
      "Una vez que envía, el Gerente de Seguridad recibe correo automáticamente en segundos.",
    ],
    cheatSheet_es: [
      "Escena segura → médica primero → app después.",
      "Tipo + Severidad → Persona → Historia → Causa Raíz → Testigos → Correcciones → Notificaciones → Fotos.",
      "Reportero + Supervisor firman. Seguridad recibe correo automático.",
    ],
  },
  "field-07-site-inspection": {
    title_es: "Lección 9 — Inspección de Seguridad del Sitio",
    why_es: "Recorridos diarios y semanales para atrapar peligros antes de que lastimen a alguien. Calificados automáticamente para ver de un vistazo si su sitio está pasando OSHA.",
    steps_es: [
      "Hub → Seguridad → Inspecciones → Nueva Inspección.",
      "Llene información del proyecto, elija Día o Noche, ingrese nombres de Inspector + Capataz.",
      "Liste la cuadrilla y cualquier sub en sitio. Anote clima y en qué trabaja la cuadrilla hoy.",
      "Recorra el sitio. Califique Cumplimiento de EPP, Peligros del Sitio, MOT, Protección contra Caídas, Eléctrico, Orden, Fuego, Estrés por Calor/Frío como Aprobado / Falla / N/A. El % en vivo se actualiza conforme avanza.",
      "Fotografíe cada Falla. Anote Suspensión de Trabajo emitida, Corregido en Sitio, Parte Responsable.",
      "Inspector + Capataz firman. Envíe.",
    ],
    tips_es: [
      "Las inspecciones semanales son más completas que las diarias. Use el mismo formulario — solo marque más puntos.",
      "Una Calificación en Vivo bajo 80% debe activar una parada con la cuadrilla.",
    ],
    cheatSheet_es: [
      "Aprobado/Falla por cada categoría. Foto a cada Falla.",
      "Calificación en Vivo muestra dónde está. <80% = parada.",
    ],
  },

  // ============================================================
  // SHOP
  // ============================================================
  "shop-01-portal-intro": {
    title_es: "Lección 1 — Panorama del Portal del Taller",
    why_es: "La consola del taller es donde los mecánicos ven cada Pre-Op enviado por el campo, qué unidades están marcadas y qué requiere atención. Cada mecánico ahora tiene su PROPIO inicio de sesión (correo + contraseña) — la contraseña compartida 'Nothappy123' está retirada. Cuentas individuales significan que cada firma lleva el nombre del mecánico automáticamente.",
    duration: "~5 min",
    steps_es: [
      "Vaya a /shop/login → ingrese su correo de trabajo Y su contraseña personal (ambos requeridos — el correo ya no es opcional).",
      "Primer inicio de sesión: será redirigido automáticamente a /shop/change-password. Elija una nueva contraseña de 6+ caracteres y confirme. Después entra directo a la Consola del Taller.",
      "¿Olvidó su contraseña? Toque 'Forgot password?' en /shop/login → escriba su correo → revise su bandeja por el enlace de restablecimiento (válido por 30 minutos). Elija una nueva contraseña, está adentro.",
      "La barra superior muestra 4 estadísticas: Inspecciones registradas, Unidades marcadas FALLA, Firmas del taller, Equipo en la flota.",
      "Panel izquierdo: cola de Artículos Abiertos (cada FALLA sin firmar). Panel derecho: Tendencias (tasa de aprobados por unidad/categoría).",
      "Más abajo: Inspecciones Pre-Op Recientes (lista completa), Lista de Equipo (flota buscable), Catálogo de Partes.",
      "Para rotar su propia contraseña en cualquier momento, toque el botón ámbar 'CHANGE PASSWORD' en el encabezado del Hub del Taller.",
      "Cierre sesión arriba a la derecha cuando termine en una computadora compartida.",
    ],
    tips_es: [
      "Admin también ve todo lo que ve el taller. Los Gerentes ven tendencias pero no pueden firmar artículos.",
      "Cuando se envía un Pre-Op con FALLA o artículo fuera de servicio, CADA mecánico activo recibe un correo automático para que la oficina de partes pueda planear.",
      "Si su cuenta queda bloqueada después de varios intentos fallidos, pida a Admin que la desbloquee desde /admin → panel de Shop Users.",
    ],
    cheatSheet_es: [
      "Correo + contraseña (ambos requeridos). Enlace de Forgot password funciona.",
      "Primer inicio fuerza un cambio de contraseña.",
      "Las FALLAS notifican por correo a cada mecánico activo.",
      "Botón Change Password en el encabezado del Hub.",
    ],
  },
  "shop-02-signing-off": {
    title_es: "Lección 2 — Firmando un Pre-Op Fallido",
    why_es: "Un FALLO mantiene la unidad FUERA DE SERVICIO hasta que el taller la libere. Su firma es la bitácora — quién lo arregló, qué partes entraron, si se necesita seguimiento.",
    steps_es: [
      "Panel de Artículos Abiertos → elija un filtro de severidad (Todas / Solo Fuera de Servicio / Solo Requiere Atención) → toque 'Firmar' en la fila que está trabajando.",
      "Se abre la tarjeta de Firma del Taller. Ingrese su nombre. Escriba notas opcionales (partes reemplazadas, seguimiento necesario, etc.).",
      "Elija un resultado: Reparado, Etiquetado fuera de servicio, Partes ordenadas, No requiere acción.",
      "Toque 'Firmar'. La unidad queda LIBERADA PARA OPERAR (o sigue FDS si la etiquetó así).",
      "Para deshacer: toque 'Reabrir' en cualquier artículo firmado. El sello se elimina y el artículo regresa a la cola.",
    ],
    tips_es: [
      "Si ordenó partes y la unidad aún espera, elija 'Partes ordenadas' — la unidad sigue FDS pero la cola muestra que está atendiendo.",
      "'Reparado' es el único resultado que regresa la unidad al servicio.",
    ],
    cheatSheet_es: [
      "Nombre → notas → resultado → Firmar.",
      "Reparado = liberada. Partes ordenadas = sigue FDS pero registrada.",
      "Reabra si firmó muy temprano.",
    ],
  },
  "shop-03-parts-catalog": {
    title_es: "Lección 3 — Catálogo de Partes + Lista de Pedido",
    why_es: "Cada unidad tiene su propia lista de partes — filtros, cuchillas, plumas, llantas, otros artículos de desgaste. Arme la lista de pedido con un toque por parte, envíela por correo a la oficina de partes con un toque al final.",
    steps_es: [
      "Consola del Taller → Catálogo de Partes → Elija una Unidad de la flota buscable.",
      "Se abre el catálogo de la unidad con 5 categorías (Filtros, Cuchillas, Plumas, Llantas, Otros Artículos de Desgaste). Cada categoría tiene filas por cada parte.",
      "Toque 'Agregar Parte' en una categoría → ingrese nombre, # de parte, cantidad, notas / tamaño / posición / capas / marca según aplique.",
      "Toque 'Guardar Catálogo' cuando haya agregado o editado partes — registrado con su nombre + marca de tiempo.",
      "Para ordenar: toque el ícono del carrito al lado de cualquier parte. Se agrega al panel de Lista de Pedido abajo.",
      "En la Lista de Pedido: ingrese su nombre, correo(s) de la oficina de partes (separados por coma), CC opcional, notas opcionales.",
      "Toque 'Enviar Pedido a Oficina de Partes'. Listo — la oficina recibe una lista formateada que pueden actuar.",
    ],
    tips_es: [
      "El catálogo persiste — una vez que arma la lista de una unidad, cada mecánico se beneficia.",
      "Si la misma parte aparece en varias unidades (ej. un filtro común), agréguela por cada unidad para que las cantidades se sumen correctamente en los pedidos.",
    ],
    cheatSheet_es: [
      "Elija unidad → Agregar Parte en la categoría correcta → Guardar.",
      "Ícono de carrito agrega a la lista de pedido. Envíe correo al final.",
    ],
  },

  // ============================================================
  // PM
  // ============================================================
  "pm-01-portal-intro": {
    title_es: "Lección 1 — Panorama del Portal de Gestión",
    why_es: "La misma superficie que la consola de Admin para el trabajo diario. Respaldo / restauración / force-reseed están ocultos de los Gerentes a propósito — ese es trabajo del Admin. Todo lo demás es idéntico.",
    steps_es: [
      "Vaya a /pm/login → ingrese la contraseña PM (pregunte a su supervisor — las credenciales se entregan fuera de línea, no se publican en ningún documento). Aterriza en Registros y Formularios.",
      "Tarjetas del tablero: Snapshot de P&L, Reportes Diarios, Inspecciones, Reuniones de Seguridad, Planes de Peligros, Cajas de Zanja, Incidentes, Pre-Op.",
      "Baje a las listas maestras: Trabajos, Empleados, Proveedores, Equipo, Partes. Cada una tiene edición en línea, importación masiva, exportación XLSX y pestaña de Archivo.",
      "Barra superior: bandera ALL OK (salud del sistema), botón Portal de Gestión, Guía, Company Info, Cerrar Sesión.",
      "Los controles de respaldo / restauración / force-reseed / recuperación NO APARECEN en el Portal de Gestión. Si necesita uno, pida al Admin.",
    ],
    tips_es: [
      "Su token PM dura hasta que cierre sesión o limpie el almacenamiento del navegador.",
      "Admin puede ver todo lo que usted ve (y más). Los Gerentes no pueden ver lo que ve el Admin (y no deberían necesitar).",
    ],
    cheatSheet_es: [
      "Registros y Formularios arriba → listas maestras abajo.",
      "Sin respaldo/restauración en PM. Eso es solo Admin.",
    ],
  },
  "pm-02-master-lists": {
    title_es: "Lección 2 — Listas Maestras (Trabajos / Empleados / Proveedores / Equipo / Partes)",
    why_es: "Estas 5 listas alimentan cada menú del app de campo. Si un trabajo no está aquí, no está en el selector. Si un empleado no está aquí, la cuadrilla no puede etiquetarlo en un Reporte Diario. Mantener estas listas limpias = toda la app se mantiene limpia.",
    steps_es: [
      "Elija una lista (ej. Trabajos). Haga clic en 'Agregar Nuevo' para escribir una fila en línea. Haga clic en cualquier celda para editar. Los cambios se guardan al salir.",
      "Reemplazo Masivo: la forma más rápida de sembrar una lista. Clic en 'Reemplazo Masivo' → pegue una hoja de cálculo → la lista completa se borra y se reconstruye desde su pegado. Los datos existentes se borran con blando (undo de 14 días).",
      "Eliminación individual: clic en el 🗑️ rojo en cualquier fila → confirmación → la fila se mueve a la pestaña Archivo (NO borrada permanentemente).",
      "Pestaña Archivo (arriba de cada panel): vea cada fila borrada con su marca 'borrado hace 3 días'. Clic en 'Restaurar' para traerla de vuelta. Después de 14 días, las filas se purgan permanentemente.",
      "Botón Exportar (verde): descarga la lista actual como un libro XLSX. Hace round-trip limpio al Reemplazo Masivo.",
    ],
    tips_es: [
      "El borrado suave de 14 días es su red de seguridad para errores — borre libremente, restaure desde Archivo si se arrepiente.",
      "Si hace un reemplazo masivo por error, cada fila vieja está en la pestaña Archivo. Restaure individualmente o simplemente pegue los datos VIEJOS de vuelta en otro Reemplazo Masivo.",
    ],
    cheatSheet_es: [
      "Agregar Nuevo → escribir en línea. Clic en celda → editar en línea.",
      "🗑️ = borrado suave. Pestaña Archivo = undo 14 días.",
      "Reemplazo Masivo = borrar + sembrar. Exportar = XLSX.",
    ],
  },
  "pm-03-import-export": {
    title_es: "Lección 3 — Round-Trips de Importar / Exportar",
    why_es: "Sus listas maestras pueden convertirse en la copia más limpia de estos datos que tiene la compañía. Exporte regularmente para que finanzas, seguros y auditores puedan obtener datos frescos cuando sea.",
    steps_es: [
      "En cualquier lista maestra, clic en 'Exportar' (botón verde). Descarga un XLSX con marca de tiempo (ej. MASCI_employees_2026-05-01.xlsx).",
      "Ábralo en Excel/Google Sheets. Cada columna coincide con lo que Reemplazo Masivo espera al regresar.",
      "Haga ediciones fuera de línea (actualizaciones y adiciones masivas). Guarde el libro.",
      "De vuelta en el portal, clic en 'Reemplazo Masivo' → arrastre el libro. La lista se reconstruye.",
      "Para verificar: después de un reemplazo masivo, exporte de nuevo y compare contra el archivo que importó. Debe coincidir byte por byte (excepto marcas de tiempo).",
    ],
    tips_es: [
      "Pruebe importaciones grandes trabajando en una copia del export primero. Pruebe el archivo contra una lista (ej. 5 filas) antes de reemplazar los 137 empleados.",
      "Después de un reemplazo masivo, eche un vistazo a la pestaña Archivo — cada fila reemplazada está ahí por 14 días si necesita comparar.",
    ],
    cheatSheet_es: [
      "Exportar → editar fuera de línea → Reemplazo Masivo de vuelta.",
      "Round-trip coincide byte por byte.",
    ],
  },
  "pm-04-archive": {
    title_es: "Lección 4 — Archivo y Undo de 14 Días",
    why_es: "Cada borrado a través de las 5 listas maestras es un borrado suave. Las filas no se van — se sientan en la pestaña Archivo por 14 días, luego se purgan. Esta es la red que lo salva de un mal clic de viernes por la tarde.",
    steps_es: [
      "En cualquier panel de lista maestra (Trabajos, Empleados, Proveedores, Equipo, Partes), clic en la pestaña 'Archivo' arriba.",
      "Verá cada fila borrada con: qué era, quién la borró (si se registró), cuándo se borró y cuántos días hasta la purga.",
      "Clic en 'Restaurar' para regresarla a la lista en vivo al instante.",
      "Filas mayores a 14 días son auto-purgadas por un trabajo en segundo plano. Una vez purgadas, solo una restauración de respaldo completo puede recuperarlas.",
      "Solo Admin: existe un botón 'Purgar Ahora' para barridas de cumplimiento — nuca toda la pestaña Archivo. Los Gerentes no ven este botón.",
    ],
    tips_es: [
      "Si ve una fila que no reconoce en el Archivo, no la restaure — consulte con Admin primero. Puede haber sido archivada deliberadamente.",
      "La ventana de 14 días es un límite DURO. Ponga un recordatorio en calendario si necesita algo más largo.",
    ],
    cheatSheet_es: [
      "Pestaña Archivo = filas con borrado suave.",
      "Restaurar → de vuelta en la lista en vivo.",
      "Purgado después de 14 días. Luego solo un respaldo puede salvarlo.",
    ],
  },
  "pm-05-email-routing": {
    title_es: "Lección 5 — Ruteo de Correos (Gerente y Seguridad)",
    why_es: "Cada formulario enviado desde el campo se envía por correo automáticamente al Gerente relevante (basado en el trabajo elegido) y con copia a la lista de distribución de la oficina. Admin ahora puede cambiar QUIÉN recibe qué correo directamente desde /admin → Email Routing — sin redespliegue, sin editar variables env. Esta lección cubre lo que controla como Gerente y lo que solo Admin puede cambiar.",
    steps_es: [
      "Portal de Gestión → lista de Gerentes de Proyecto. Cada fila: nombre, correo, teléfono, interruptor activo, última actividad.",
      "Abra el maestro de Trabajos → cada trabajo tiene un campo 'Gerente de Proyecto', un campo 'Correo del Gerente', y hasta 4 co-Gerentes. Cuando se envía un Reporte Diario para ese trabajo, la app busca el Correo del Gerente Y cada correo de co-Gerente y los copia automáticamente.",
      "Para cambiar quién está en un trabajo: edite la fila → elija un nuevo Gerente → el correo se autocompleta → guarde. Agregue co-Gerentes en la misma fila.",
      "Formularios de cumplimiento (Inspección de Sitio, Junta de Seguridad, JHA, Incidente, QA/QC) TAMBIÉN reciben la lista always-CC de la oficina (jaymn.judd + safety@ por defecto). Reportes Diarios + Pre-Ops NO — van solo al Gerente y co-Gerentes, manteniendo la bandeja de la oficina tranquila.",
      "Correos de FALLA de Pre-Op adicionalmente se envían a cada mecánico activo del panel de Shop Users.",
      "Admin puede sobrescribir cada lista (always-CC de cumplimiento, destinatarios de safety forms, CC de leadership, extras de incidentes severos, fallback del taller, destino del respaldo diario) en /admin → Email Routing — vea la lección 8 de Admin.",
    ],
    tips_es: [
      "AUTO_EMAIL_REPORTS es un interruptor a nivel env. Producción lo tiene ON. Preview lo tiene OFF para que las pruebas no quemen el cupo diario.",
      "Si un Gerente no recibe correos, revise: (1) interruptor activo, (2) asignación del Gerente al Trabajo, (3) carpeta de spam, (4) /admin → Email Routing → 'Send test email' a esa dirección.",
      "Cuando agrega un co-Gerente, automáticamente recibe cada correo de los registros de ese trabajo — sin necesidad de editar el ruteo aparte.",
    ],
    cheatSheet_es: [
      "Trabajo → Gerente Primario + Co-Gerentes → correo + CCs automático.",
      "Tipos de cumplimiento = CC de oficina. Operacionales = solo Gerente.",
      "Admin → Email Routing para cada override (sin redespliegue).",
    ],
  },
  "pm-06-posters-jha": {
    title_es: "Lección 6 — Carteles del Sitio + Planes JHP",
    why_es: "Los Carteles del Sitio son folletos imprimibles que pegan dentro de los tráileres — con código QR para que las cuadrillas escaneen desde cualquier teléfono. Los Planes JHP son PDFs por trabajo que la oficina sube para que los capataces lean el Plan de Peligros antes de comenzar.",
    steps_es: [
      "Panel de Carteles del Sitio (Portal de Gestión → Carteles). Tres carteles: Hoja de Referencia, Cartel de Cajas de Zanja, Cartel de Planes JHP.",
      "Vista previa de cualquier cartel en nueva pestaña. Imprímalo. Péguelo dentro de cada tráiler de trabajo activo.",
      "Admin de Planes JHP: suba un PDF por trabajo activo — arrastre o clic para elegir. Máximo 10 MB por PDF.",
      "Las cuadrillas van a Seguridad → Planes de Peligros → eligen su trabajo → leen el PDF. Sin inicio de sesión.",
      "Descarga para uso sin conexión: las cuadrillas tocan el PDF en su teléfono → menú compartir → guardar en Archivos/Descargas. Funciona en zonas muertas.",
    ],
    tips_es: [
      "Reimprima los carteles en cada actualización trimestral de seguridad — los QRs no cambian pero el papel se desgasta.",
      "Si el Plan JHP de un trabajo no está subido, los capataces no pueden verlo. Ponga recordatorio en calendario: suba antes del Día 1 de cada nuevo trabajo.",
    ],
    cheatSheet_es: [
      "Carteles → imprimir → pegar en tráiler.",
      "PDF JHP → subido por trabajo → legible sin conexión en teléfonos.",
    ],
  },

  // ============================================================
  // ADMIN
  // ============================================================
  "admin-01-platform-overview": {
    title_es: "Lección 1 — Panorama de la Plataforma",
    why_es: "Usted tiene la contraseña de admin. Eso significa todo lo que puede hacer un Gerente, más los controles que mantienen la plataforma segura — respaldos, restauraciones, force-reseed, auditorías de integridad. Esta lección es un mapa de lo que hay bajo el capó.",
    steps_es: [
      "La plataforma es React (frontend) + FastAPI (backend) + MongoDB (base de datos), desplegada en mascidocs.com. Preview en safety-audit-mobile-1.preview.emergentagent.com.",
      "Tres niveles de acceso: Admin ve todo. Gerente (PM) ve lo diario pero NO respaldo/restauración. Taller solo ve equipo + firmas Pre-Op. Cada nivel tiene su propia contraseña — emitida por el liderazgo del Departamento de Seguridad, nunca compartida por escrito.",
      "Tarjeta Admin en el área inferior del Hub. /admin/login con la contraseña de Admin (pregunte al liderazgo del Departamento de Seguridad). Después del login aterriza en Registros y Formularios (idéntico a la vista PM) + la sección Recuperación del Sistema abajo.",
      "Paneles principales bajo Admin: Tableros (cumplimiento), Listas Maestras (Trabajos/Empleados/Proveedores/Equipo/Partes), Formularios (Ver y Correo), Ruteo de Correos, Carteles, Admin JHP, Admin Cajas de Zanja, Gerentes de Proyecto, Recuperación del Sistema.",
      "Sección Recuperación del Sistema (admin-estricto, los Gerentes no la pueden ver): Respaldo y Restauración de Todo, Verificación de Integridad, lista de Respaldos en Servidor, Recuperación de Cuadrilla, Force-Reseed.",
      "Los respaldos programados corren dos veces al día: 02:00 UTC y 18:00 UTC. 14 días de retención. Podados automáticamente. Admin no hace nada.",
    ],
    tips_es: [
      "Nunca comparta la contraseña de Admin. Si sospecha que se filtró, rótela vía ADMIN_PASSWORD en las variables env del despliegue de producción.",
      "Todo lo que puede hacer un Gerente también está en Admin — no hay razón para 'ser un Gerente' siendo admin. Inicie sesión como admin y vaya.",
    ],
    cheatSheet_es: [
      "Admin = Gerente + Recuperación del Sistema (respaldos, restauración, force-reseed).",
      "3 niveles de contraseña: Admin > Gerente > Taller.",
      "Respaldos corren 02:00 + 18:00 UTC. 14 días de retención. Automático.",
    ],
  },
  "admin-02-backups-how": {
    title_es: "Lección 2 — Cómo Funcionan los Respaldos (Automático + Manual)",
    why_es: "Si la base de datos de mascidocs.com desapareciera ahora mismo, los respaldos son lo único que traería los registros de MASCI de vuelta. Necesita saber EXACTAMENTE cómo corren, dónde viven y cómo sacar uno rápido si el app de producción está en llamas.",
    steps_es: [
      "DOS ventanas programadas diarias: 02:00 UTC (~10pm hora Este, nocturno) y 18:00 UTC (~2pm hora Este, medio día). Configurado en el backend vía variable env BACKUP_HOURS_UTC. Valores seguros por defecto.",
      "Contenido del respaldo: UN zip por corrida, nombrado MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip. Contiene cada colección de MongoDB como JSON crudo + un manifiesto de índice + todos los archivos subidos (PDFs, firmas, fotos).",
      "Ubicación de almacenamiento: /app/backend/backups/ en el disco del servidor. Listado vía el panel Admin → Respaldos en Servidor.",
      "Retención: 14 días. Archivos mayores a 14 días son podados automáticamente en cada corrida (pre-flight).",
      "Respaldo manual: Admin → Recuperación del Sistema → Panel Hero de Respaldo → clic en 'Respaldo + correo + descargar AHORA'. En ~30 segundos obtiene: (1) un .zip descargado a su máquina, (2) el mismo .zip enviado por correo a BACKUP_EMAIL_TO vía Resend.",
      "Qué hay EN el .zip: es un archivo normal. Descomprímalo en el Explorador de Windows o Finder de Mac. Cada colección tiene un archivo .json. Cada registro de seguridad tiene un .pdf imprimible. Fotos/firmas están embebidas como base64 dentro del JSON. Nada está encriptado — guárdelo en un lugar seguro.",
      "Verificación de Integridad: Admin → Recuperación del Sistema → 'Verificación de Integridad'. Compara las colecciones en vivo vs el manifiesto del respaldo más reciente. Si alguna colección en vivo no está en el respaldo, la marca. Corra después de cambios grandes o antes de un despliegue.",
      "Si el respaldo programado falla: revise los logs de /app/backend (grep 'scheduled-backup'). La causa común es espacio en disco — la verificación pre-flight aborta si el disco está >95% lleno después de podar.",
    ],
    tips_es: [
      "Antes de cualquier redespliegue, corra el respaldo manual. Toma 30 segundos. Lo salva si el despliegue cambia una variable env oculta.",
      "BACKUP_EMAIL_TO se configura en el env de despliegue. Si está mal, los respaldos aún se guardan al disco — pero no recibirá una copia en su bandeja.",
      "NO borre archivos .zip de la UI a menos que tenga otra copia. La app no puede resucitarlos.",
    ],
    cheatSheet_es: [
      "Auto: 02:00 + 18:00 UTC. 14 días de retención.",
      "Manual: Admin → Respaldo + correo + descargar AHORA.",
      "Verificación de Integridad antes de cada despliegue.",
      "BACKUP_EMAIL_TO debe estar configurado en env de prod.",
    ],
  },
  "admin-03-restore": {
    title_es: "Lección 3 — Cómo Restaurar desde un Respaldo",
    why_es: "Tiene un .zip. Algo salió mal. Necesita los datos de vuelta. Este es el flujo exacto.",
    steps_es: [
      "Confirme qué salió mal. Si una sola fila fue borrada suavemente, use la pestaña Archivo en la lista maestra — más rápido y seguro que una restauración completa.",
      "Obtenga un .zip. Ya sea descargue el más reciente de Admin → Respaldos en Servidor, o use el .zip de su correo (BACKUP_EMAIL_TO se lo envió a su bandeja).",
      "Admin → Recuperación del Sistema → Panel Hero de Respaldo → 'Restaurar Desde Archivo' → elija el .zip de su computadora. Máximo 500 MB.",
      "La restauración FUSIONA registros: filas existentes que coinciden con una fila del respaldo se sobrescriben con la copia del respaldo. Filas nuevas en el respaldo se agregan. Filas en la DB en vivo que NO están en el respaldo se DEJAN INTACTAS (no se borran). Seguro de correr.",
      "Modal de confirmación: 'Cada registro dentro de este .zip se fusionará al sistema en vivo…'. Clic en 'Sí, restaurar'.",
      "Vea el progreso. Al final verá 'Restaurados X registros en Y colecciones'.",
      "Abra un par de tableros para revisar los datos restaurados.",
    ],
    tips_es: [
      "Las restauraciones NUNCA borran. Si está intentando revertir un cambio malo, TAMBIÉN necesita borrar las filas nuevas malas después de restaurar — el respaldo viejo no sabe de ellas.",
      "Si el .zip es más viejo que sus datos en vivo actuales, SOBRESCRIBIRÁ datos en vivo con datos desactualizados. Piense antes de clic en Sí.",
      "Recuperación completa del sistema (borrar todo, restaurar desde respaldo): contacte a su desarrollador / soporte del proveedor — no es un botón de UI a propósito.",
    ],
    cheatSheet_es: [
      "Restaurar = fusionar. Nunca borra. Filas viejas restauradas + filas nuevas AGREGADAS.",
      "Si quiere un verdadero rollback: restaurar + borrar manualmente las filas nuevas malas.",
      "La pestaña de borrado suave es más rápida para errores de una sola fila.",
    ],
  },
  "admin-04-integrity-check": {
    title_es: "Lección 4 — Verificación de Integridad y Bitácora de Auditoría",
    why_es: "Confíe pero verifique. La Verificación de Integridad prueba que cada colección actualmente en su DB en vivo está capturada en el respaldo más reciente — atrapa colecciones nuevas que un feature futuro agregue sin actualizar la rutina de respaldo.",
    steps_es: [
      "Admin → Recuperación del Sistema → Verificación de Integridad (o /api/admin/backups/integrity-check directamente).",
      "Salida: last_backup_filename, last_backup_at, live_collections (cada colección Mongo ahora mismo), captured_collections (qué contenía el último respaldo), missing_from_backup (⚠ cualquier discrepancia), ok (true/false).",
      "Si ok === false: una colección existe en vivo pero no fue respaldada. Acción: corra un respaldo manual inmediatamente, luego verifique que la próxima corrida programada la capture. Si sigue faltando, el código de respaldo necesita un parche.",
      "Corra esta verificación: (1) después de cualquier lanzamiento de feature que agregue una colección, (2) antes de cualquier despliegue de prod, (3) como barrida mensual de sanidad.",
    ],
    tips_es: [
      "Desde la última auditoría, las 23 colecciones están capturadas: activity_log, daily_reports, docs, employees, equipment_inspections, equipment_master, equipment_parts, equipment_units, events, hill_scopes, incidents, inspections, jhas, job_hazard_files, jobs_master, meetings, message_comments, messages, notifications, project_managers, project_members, projects, suppliers.",
      "La verificación de integridad es barata (<1 seg). No hay razón para no correrla frecuentemente.",
    ],
    cheatSheet_es: [
      "Verificación de Integridad = ¿coinciden las colecciones en vivo con el manifiesto del último respaldo?",
      "ok=true → todo bien. ok=false → corra respaldo manual ahora.",
    ],
  },
  "admin-05-crew-recovery": {
    title_es: "Lección 5 — Herramientas de Recuperación de Cuadrilla (Force-Reseed, Reinicio de Contraseña)",
    why_es: "Herramientas de uso raro para cuando los datos sembrados (trabajos, lista) se corrompen o el app desplegado pierde su semilla en un redespliegue. Solo Admin. NUNCA usadas por Gerentes. La mayoría de admins nunca las tocan — pero cuando las necesita, las necesita de verdad.",
    steps_es: [
      "Estado de Recuperación de Cuadrilla: /api/admin/crew-recovery/status (o vía el panel UI). Muestra cuántos trabajos, empleados, proveedores están en la DB en vivo vs qué insertaría la semilla.",
      "Reiniciar Contraseña: /api/admin/crew-recovery/reset-password. Raramente necesario. Úselo si un usuario del taller olvidó y no puede actualizarlo vía el panel de usuarios.",
      "Force-Reseed: /api/admin/crew-recovery/force-reseed. BORRA Y RECONSTRUYE las colecciones sembradas (jobs_master, employees, suppliers) desde el JOB_LIBRARY hard-codeado. Todas las ediciones manuales a esas tablas se PIERDEN.",
      "Antes de force-reseed: corra un respaldo manual. Confirme que quiere perder cada edición desde la última semilla. Luego clic.",
      "Scrap-Crew-Hub: /api/admin/crew-recovery/scrap-crew-hub. Nuca la bandera del feature viejo clon de Basecamp y las colecciones asociadas. Ya corrido históricamente. No lo vuelva a correr a menos que reactive Crew Hub.",
    ],
    tips_es: [
      "Si un Gerente Reemplazó Masivamente por error los 137 empleados con 2 filas de prueba, NO force-reseed — restaure desde Archivo (borrado suave de 14 días) en lugar. Force-reseed es para corrupción más profunda.",
      "Cada ruta de recuperación es require_admin_strict. Tokens PM regresan 401. Tokens Taller regresan 401.",
    ],
    cheatSheet_es: [
      "Force-reseed = borrar + sembrar desde JOB_LIBRARY. Último recurso.",
      "Siempre respaldo manual PRIMERO.",
      "Prefiera restauración de Archivo para errores de una sola fila.",
    ],
  },
  "admin-06-deploy-redeploy": {
    title_es: "Lección 6 — Flujo de Despliegue / Redespliegue Seguro",
    why_es: "Cada redespliegue es una oportunidad de romper algo. La rutina abajo ha enviado más de 20 despliegues sin pérdida de datos. Sígala.",
    steps_es: [
      "Paso 1 — RESPALDO. Admin → Recuperación del Sistema → 'Respaldo + correo + descargar AHORA'. Espere la palomita verde.",
      "Paso 2 — Verificación de Integridad. Admin → 'Verificación de Integridad'. Confirme ok: true.",
      "Paso 3 — Save-to-GitHub (en el input de chat del despliegue). Captura el frontend+backend actual como un commit — punto de rollback.",
      "Paso 4 — Verifique las variables env del despliegue de producción: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD, ADMIN_HMAC_SECRET, CORS_ORIGINS, MONGO_URL, DB_NAME, BACKUP_EMAIL_TO, RESEND_API_KEY, AUTO_EMAIL_REPORTS=true, RATE_LIMITING=on.",
      "Paso 5 — Clic en Desplegar en el tablero de despliegue. Espere la compilación.",
      "Paso 6 — Prueba post-despliegue: curl /api/health → 200. Inicie sesión como Admin, Gerente, Taller. Revise un tablero. Revise que el panel de Respaldo carga.",
      "Paso 7 — Corra Verificación de Integridad de nuevo en el sitio en vivo. Confirme que el respaldo post-despliegue captura todas las colecciones.",
      "Si algo se ve mal: use la opción Rollback en el tablero de despliegue para regresar al punto antes del despliegue. Si los datos cambiaron entre el despliegue y el rollback, restaure desde el respaldo del Paso 1.",
    ],
    tips_es: [
      "Rollback es gratis y rápido. No dude si algo se ve mal — rollback primero, debugee después.",
      "Siempre guarde el respaldo pre-despliegue por al menos una semana después del despliegue — ese es su seguro si un bug sutil solo aparece al día 3.",
    ],
    cheatSheet_es: [
      "Respaldo → Verificación de Integridad → GitHub → Desplegar → Prueba → Verificación de Integridad.",
      "Rollback si algo no está bien. Debugee después.",
    ],
  },
  "admin-07-security-passwords": {
    title_es: "Lección 7 — Contraseñas, Acceso y Seguridad",
    why_es: "El eslabón más débil de cualquier sistema es la contraseña. Aquí está cómo funciona el modelo de token de MASCI y qué hacer cuando una contraseña se filtra o un Gerente/Taller se va.",
    steps_es: [
      "Las contraseñas viven en variables env: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD. Todas configuradas en el env de despliegue de producción.",
      "Flujo frontend: POST /api/{admin|pm|shop}/login con la contraseña → backend regresa un token HMAC de 64 caracteres → frontend lo guarda en localStorage y lo envía como header X-{Admin|PM|Shop}-Token en cada solicitud.",
      "El token no tiene expiración — se invalida rotando la contraseña (todos los tokens viejos dejan de funcionar inmediatamente).",
      "Rotar Admin: configure ADMIN_PASSWORD a un nuevo valor en env de despliegue de producción → redespliegue. Cada sesión admin es expulsada. Igual para PM_PASSWORD / SHOP_PASSWORD.",
      "Limitación de tasa: LOGIN_MAX_FAILS=10 (por defecto) y LOGIN_LOCKOUT_SECONDS=900 (15 min) — bloquea ataques de pulverización de contraseña por IP.",
      "CORS: solo mascidocs.com y su origen www pueden pegar la API de prod. URLs de preview se permiten vía CORS_ORIGIN_REGEX.",
      "Cuando un Gerente se va: rote PM_PASSWORD. Informe a los Gerentes restantes de la nueva contraseña fuera de banda (Signal, teléfono, en persona — NO correo).",
    ],
    tips_es: [
      "Si una contraseña de admin SE FILTRA: rote inmediatamente. Audite la colección activity_log por cosas raras en las últimas 72 horas.",
      "ADMIN_HMAC_SECRET es la llave HMAC que firma los tokens. Si ESO se filtra, rótelo también — lo cual invalida cada sesión admin en todo el sistema.",
    ],
    cheatSheet_es: [
      "Contraseñas = variables env. Rotar = redesplegar = todos los tokens viejos invalidados.",
      "Límite de tasa: 10 fallos → bloqueo de IP por 15 min.",
      "Cuando alguien se va → rote la contraseña de su nivel.",
    ],
  },
  "field-08-doc-ids": {
    title_es: "Lección 8 — Doc IDs (número de seguimiento de cada formulario)",
    why_es: "Cada formulario, reporte, inspección y check-in que llena ahora lleva un Doc ID único — como DR-2026-00042 para un Reporte Diario. El número se imprime en el PDF, aparece en pantalla, y va en el asunto del correo. Cuando la oficina llame por 'ese reporte del martes pasado', le darán el Doc ID. Léalo de vuelta, búsquelo, listo — sin escarbar entre 50 reportes.",
    steps_es: [
      "Después de enviar cualquier formulario, la pantalla de Gracias muestra el Doc ID arriba en rojo grande. Tome captura si su supervisor lo pide.",
      "El PDF que se envía por correo lleva el Doc ID impreso arriba a la derecha en rojo en cada página.",
      "Formato del Doc ID = <TIPO>-<AÑO>-<5 dígitos>. El tipo dice qué es: DR=Reporte Diario, PRE=Pre-Op, INSP=Inspección de Sitio, MTG=Junta de Seguridad, JHA=Plan de Peligros, INC=Incidente, QC=QA/QC, EQC=Checkout de Equipo, EQR=Devolución de Equipo, SEI=Entrega de PPE, SET=Capacitación de Seguridad.",
      "Los números reinician cada 1 de enero. Así que DR-2026-00001 fue el primer Reporte Diario de 2026.",
      "Cuando llame a la oficina por un registro, deles el Doc ID — pueden meterlo en la barra de búsqueda de Admin y aterrizan instantáneo.",
    ],
    tips_es: [
      "Si ve dos Doc IDs en la misma pantalla, eso es un formulario de Devolución que referencia su Checkout padre — ambos números quedan ligados.",
      "Los Doc IDs nunca cambian. Una vez sellados, ese número pertenece a ese registro para siempre — aunque editen detalles después.",
      "Los PDFs en español llevan los mismos Doc IDs (el formato es universal — sin traducción necesaria).",
    ],
    cheatSheet_es: [
      "Doc ID = <TIPO>-<AÑO>-<5 dígitos>. Arriba a la derecha de cada PDF.",
      "DR=Diario, PRE=Pre-Op, INC=Incidente, EQC=Checkout, EQR=Devolución.",
      "Oficina llama por un registro → deles el Doc ID → lo encuentran instantáneo.",
    ],
  },
  "shop-04-account-and-password": {
    title_es: "Lección 4 — Su Cuenta, Inicio de Sesión y Contraseña",
    why_es: "Cada mecánico tiene su propia cuenta MASCI para que cada firma de Pre-Op, cada orden de partes, y cada edición de flota sea trazable a la persona que la hizo. Las contraseñas compartidas se acabaron. Esta lección es todo lo que necesita para manejar su propio inicio de sesión.",
    steps_es: [
      "Admin emite su cuenta desde /admin → panel de Shop Users. Dos opciones de entrega: (1) Mostrar en Pantalla — admin le lee la contraseña temporal, o (2) Enviar por Correo — Resend le manda un correo de bienvenida con la contraseña incluida.",
      "Primer inicio de sesión: vaya a /shop/login → correo + contraseña temporal → será redirigido a /shop/change-password. Elija una nueva contraseña de 6+ caracteres. Confirme. Está adentro.",
      "Cambie su contraseña en cualquier momento: en el Hub del Taller, toque el botón ámbar 'CHANGE PASSWORD' al lado de Sign Out. Ingrese vieja, nueva, confirme. Envíe.",
      "Olvidó su contraseña: en /shop/login toque 'Forgot password?' → ingrese su correo de trabajo → revise bandeja (Gmail, Outlook, lo que use) → toque el enlace de restablecimiento dentro de 30 minutos → elija nueva contraseña → cae directo en la Consola del Taller.",
      "Si un compañero se va de la compañía: Admin desactiva su cuenta desde /admin → Shop Users → ícono de candado. Su token deja de funcionar inmediatamente — sin necesidad de rotar contraseñas.",
    ],
    tips_es: [
      "Los enlaces de restablecimiento son válidos solo por 30 minutos. Si el suyo expiró, solicite otro — sin daño.",
      "No comparta su contraseña. Cada firma lleva su nombre automáticamente; si alguien más usa su login, esa es SU firma en la pista de auditoría.",
      "Si no puede entrar a su bandeja en este momento, pídale a Admin que use 'Mostrar en Pantalla' — contraseña temporal nueva en 5 segundos.",
    ],
    cheatSheet_es: [
      "Correo + contraseña. Enlace 'Forgot password' envía restablecimiento de 30 min.",
      "Botón Change Password en el Hub en cualquier momento.",
      "No comparta login = su nombre permanece en sus firmas.",
    ],
  },
  "pm-07-field-leadership": {
    title_es: "Lección 7 — Hub de Field Leadership (perspectiva del PM)",
    why_es: "Field Leadership es el kit de herramientas del supervisor (10 formularios — write-ups, coaching, checkout/devolución de equipo, evaluaciones, notas del supervisor). Como PM, usted es el destino de ruteo para cada registro de leadership en sus trabajos. Esta lección es cómo encontrarlos, revisarlos, y actuar sobre ellos.",
    steps_es: [
      "Cada registro de Field Leadership envía correo automático al PM asignado (usted), jaymn.judd@mascigc.com, y safety@mascigc.com. PDF adjunto a cada correo.",
      "Para navegar en pantalla: /pm → registros de Field Leadership (o directo /leadership/records). Filtre por tipo (10 tipos), fecha, empleado, proyecto. Los PMs ven SOLO registros en sus trabajos asignados — admin ve todo.",
      "Toque cualquier registro → página de detalle → badge de Doc ID en el encabezado (ej. EQR-2026-00012), datos completos del formulario, firmas, fotos.",
      "Registros de Equipment Checkout: fotos por artículo renderizadas en la página Y en el PDF. CADA artículo tiene Marca / Nombre / Modelo / Serie / cantidad / valor de reemplazo / 2+ fotos.",
      "Registros de Equipment Return: comparación lado-a-lado 'Original al Checkout' (esmeralda, izquierda) vs. 'Condición de Devolución' (ámbar/rojo, derecha). El badge de Damage Owed en el encabezado se pone rojo cuando hay artículos Dañados/Perdidos.",
      "Si un Write-Up necesita seguimiento, el PDF incluye la fecha de seguimiento — ponga recordatorio en su calendario.",
      "Exportar registros: botón 'CSV' arriba a la derecha en la página de registros. Descarga la lista filtrada con todos los metadatos.",
    ],
    tips_es: [
      "Las Notas del Supervisor son admin-estricto: los PMs pueden leer notas archivadas para sus propios trabajos pero el formulario es solo-admin para presentar (los Capataces no tienen acceso).",
      "Equipment Return usa el Doc ID del Checkout original para jalar la comparación lado-a-lado. Si un registro de devolución se archivó pre-iter52, la comparación todavía funciona vía búsqueda de respaldo — la columna esmeralda muestra 'Checkout coincidente'.",
      "Use la barra de búsqueda de Doc ID en /admin para saltar directo a un registro de leadership por su Doc ID (EQR-2026-00012, FLN-2026-00007, etc.).",
    ],
    cheatSheet_es: [
      "PM auto-CC en cada registro de Field Leadership en sus trabajos.",
      "/leadership/records → filtrar, buscar, abrir, exportar.",
      "Equipment Return muestra comparación lado-a-lado + badge Damage Owed.",
    ],
  },
  "pm-08-job-photos": {
    title_es: "Lección 8 — Biblioteca de Fotos del Trabajo",
    why_es: "Cada foto que las cuadrillas envían en Reportes Diarios, Inspecciones de Sitio, e Inspecciones QA/QC se replica a una galería buscable única — organizada por Trabajo → Semana. Selección múltiple para descargar un ZIP o enviar un paquete por correo a un GC, ajustador de seguros, o abogado.",
    steps_es: [
      "Portal del PM → Job Photos (o /pm/photos). Las fotos están limitadas a trabajos asignados (admin ve todo).",
      "Acordeón de carpetas: cada Trabajo (con Doc ID donde aplique) → expandir → Semanas. Cada semana muestra fotos con badge de fuente (Reporte Diario = rojo, Inspección de Sitio = ámbar, QA/QC = verde) y fecha.",
      "Barra de búsqueda: escriba un número de proyecto, nombre de empleado, o parte del nombre del trabajo. El filtro de fuente reduce a un tipo.",
      "Toque cualquier foto para abrir la lightbox (resolución completa). Presione Esc para cerrar.",
      "Selección múltiple: toque la casilla en la esquina arriba-derecha de cualquier mosaico. La barra de acciones sube desde abajo: cuenta seleccionada + botón Email + botón Download ZIP.",
      "Download ZIP: organiza fotos en <Trabajo>/<Semana>/<fuente>__<fecha>__N.<ext>. Tope 1000 fotos por zip.",
      "Email packet: escriba destinatario(s), asunto, nota opcional. Adjunta el ZIP. Tope 200 fotos / 25 MB por correo.",
      "Las fotos HEIC del iPhone se renderizan correctamente (el backend convierte HEIC → WebP/AVIF/JPEG automáticamente). Las fotos de Pre-Op intencionalmente NO están en esta biblioteca — son de diagnóstico, no de documentación de progreso.",
    ],
    tips_es: [
      "Las fotos NO se duplican — la biblioteca lee del registro original. Borre una foto en un Reporte Diario y la entrada de la biblioteca también desaparece.",
      "El Email packet es la forma más rápida de enviar documentación de seguro/legal — no tiene que descargar y luego adjuntar.",
      "Las galerías cargan instantáneo la segunda vez porque el backend pre-renderiza miniaturas en un caché de 7 días. La primera visita a las fotos de un Reporte Diario nuevo puede tomar ~10 segundos (el background warm-up maneja envíos nuevos automáticamente dentro de 10 minutos).",
    ],
    cheatSheet_es: [
      "Portal del PM → Job Photos. Carpetas por Trabajo → Semana.",
      "Selección múltiple → Download ZIP o Email packet.",
      "Topes: 1000 fotos/ZIP, 200 fotos / 25 MB por correo.",
    ],
  },
  "admin-08-email-routing": {
    title_es: "Lección 8 — Consola de Email Routing (overrides sin redespliegue)",
    why_es: "Seis listas de correo ruteables (always-CC de cumplimiento, To de Safety Forms, CC de Field Leadership, extras de Severe Incident, fallback del Shop Manager, destino de Daily Backup) antes requerían cambio de variable env + redespliegue para actualizar. Ahora las edita directo en /admin → Email Routing. Los cambios están vivos dentro de 60 segundos.",
    steps_es: [
      "Hub de Admin → panel de Email Routing (entre la PM Routing Table y Site Posters).",
      "Cada fila muestra: una etiqueta, el valor en vivo, el default de env, badge OVERRIDE si la personalizó, y botones Default + Save por fila.",
      "Edite cualquier lista: escriba direcciones separadas por comas, punto-y-coma, o saltos de línea. Save. El toast confirma 'Saved · <Nombre de ruta>'.",
      "Reset a default: toque el botón Default → carga el valor de env en el textarea → toque Save para persistir (o aléjese para descartar).",
      "Lista vacía = silenciar la ruta. Por ejemplo, ponga Severe Incident extra-CC en vacío si quiere cero destinatarios extra en incidentes severos (solo el PM estándar + always-CC).",
      "Send test email: parte de abajo del panel. Escriba cualquier dirección → toque Send test → el destinatario recibe un mensaje 'Email Routing test' estilizado vía Resend en 3 segundos. Use esto para verificar el correo de un GC nuevo o su dirección personal antes de agregar a una lista de ruteo.",
      "El badge arriba a la derecha muestra la fuente: 'Defaults (env)' (borde ámbar) significa que todo usa env vars; 'Custom (DB)' (fondo ámbar) significa que al menos una lista está sobrescrita.",
      "Línea de auditoría de última actualización abajo: timestamp ISO + quién lo cambió (siempre 'admin' por ahora ya que solo admins pueden pegarle a los endpoints).",
    ],
    tips_es: [
      "Los cambios se propagan en 60 segundos (caché por proceso), pero el botón Save fuerza una invalidación inmediata del caché — para cuando se va el toast, el siguiente correo ya usa la nueva lista.",
      "Las variables env quedan como respaldos — si alguna vez borra un override de DB, la ruta vuelve al default de env automáticamente. Cinturón + tirantes.",
      "Use el botón de test email ANTES de agregar el correo de un nuevo GC a una lista de ruteo. Bouncebacks gastan cupo de Resend y podría perderlos en los logs.",
    ],
    cheatSheet_es: [
      "Admin → Email Routing. 6 listas + 1 correo único + Send test.",
      "Lista vacía = silenciar. Badge OVERRIDE = personalizada.",
      "Efecto en 60 segundos. Sin redespliegue.",
    ],
  },
  "admin-09-doc-id-search": {
    title_es: "Lección 9 — Barra de Búsqueda Global de Doc ID",
    why_es: "Cada formulario, reporte e inspección en el sistema lleva un Doc ID único (DR-2026-00042, EQR-2026-00012, etc.). La barra de búsqueda ámbar arriba de /admin le permite meter cualquier Doc ID y aterrizar en la página de detalle del registro coincidente con una pulsación. Reemplaza el problema de 'darle clic a 8 páginas de lista para encontrar ese registro' por completo.",
    steps_es: [
      "Hub de Admin → arriba de la página → barra de búsqueda con borde ámbar e ícono de lupa.",
      "El placeholder muestra el formato: PRE-2026-00042, DR-2026-00007, EQR-2026-00012, JHA-2026-00001…",
      "Escriba el Doc ID (no importa mayúsculas — auto-mayúsculas) → presione Enter o toque Find.",
      "Coincidencia encontrada → la app lo rutea directo a la página de detalle (ej. /admin/daily/<id> o /admin/leadership/records/<id>) con el badge del Doc ID resaltado.",
      "Sin coincidencia → mensaje rojo 'NO RECORD FOUND FOR \"<id>\"' inline. Sin toast, sin error — limpio.",
      "Doc ID se busca a través de las 10 colecciones fuente en un round-trip (~50ms total).",
    ],
    tips_es: [
      "La búsqueda es insensible a mayúsculas pero coincidencia exacta. 'DR-2026-42' no coincide con DR-2026-00042 (el padding de 5 dígitos importa).",
      "Cuando los admins navegan DESDE la barra de búsqueda, el token admin se preserva a través del ruteo — aunque el destino sea un path /pm/* o /shop/*. Sin sign-out accidental.",
      "Búsqueda de texto libre (ej. 'encuentra cada reporte que mencione Topcon') NO está aquí — use los inputs de búsqueda por lista en Records & Forms.",
    ],
    cheatSheet_es: [
      "Arriba de /admin. Escriba Doc ID → Enter → aterriza en el registro.",
      "10 colecciones buscadas en un round-trip.",
      "Insensible a mayúsculas pero exacto (el padding cero importa).",
    ],
  },
  "admin-10-job-photos-perf": {
    title_es: "Lección 10 — Rendimiento de Job Photos (HEIC, warm-cache, Re-index)",
    why_es: "Las fotos del iPhone son HEIC por defecto — sin conversión del lado del servidor renderizan como miniaturas rotas para cada vista de galería. La plataforma ahora decodifica HEIC, cachea miniaturas WebP/AVIF/JPEG en MongoDB por 7 días, y auto-calienta envíos nuevos en background. Esta lección es lo que pasa bajo el capó y los dos botones de admin que existen para emergencias.",
    steps_es: [
      "Pipeline: foto enviada → indexer replica metadatos a colección job_photos → galería frontend pide /api/job-photos/{id}/thumb-signed?t=<token> → backend revisa caché de Mongo → si miss, decodifica vía Pillow (con pillow-heif registrado para HEIC del iPhone) → encodea a WebP/AVIF/JPEG en una pasada → guarda los 3 en caché → sirve el formato correcto basado en el header Accept del navegador.",
      "La concurrencia de render está topada en 2 decodificaciones de Pillow en vuelo por worker (env: JOB_PHOTO_RENDER_CONCURRENCY). Esto acota la memoria; una galería de 30 fotos no le hace OOM al worker. Hits de caché saltan el lock por completo.",
      "Tope del frontend: máximo 6 peticiones de miniatura en vuelo en cualquier momento, gateadas por IntersectionObserver (300px rootMargin). Los mosaicos solo cargan cuando se scrollean cerca. La carga lazy nativa del navegador sola disparaba muy temprano cuando los acordeones se expandían.",
      "Scheduler de auto-warm: cada 10 minutos, un loop en background pre-renderiza cualquier foto indexada que no tenga entrada de caché JPEG. Hasta 200 fotos por tick. Honra el mismo tope de concurrencia. Efecto: un Reporte Diario enviado a mediodía está calentado completo dentro de 10 minutos — primer espectador a las 12:15 ve miniaturas instantáneas.",
      "Re-index MANUAL: Admin → página de Job Photos → botón Re-index (arriba-derecha). Limpia el índice de metadatos Y el caché de miniaturas, luego reconstruye desde la fuente. Use después de un despliegue o cuando una foto conocida no aparece.",
      "Warm-cache MANUAL: POST /api/job-photos/admin/warm-cache (token admin requerido). Pre-renderiza cada foto en el índice. Devuelve {warmed, skipped, failed, elapsed_seconds}. Solo útil justo después de un Re-index cuando no quiere esperar 10 minutos al loop de auto-warm.",
      "TTL del caché: 7 días. Fotos frías (sin peticiones en 7 días) caen automático — el plan Atlas se mantiene acotado. Re-renderizadas en la siguiente petición.",
    ],
    tips_es: [
      "Después de cada despliegue de producción: entre a /admin → Job Photos → clic en Re-index. Limpia el caché para que cualquier foto del iPhone que estaba rota antes de instalar pillow-heif se re-renderice fresca.",
      "Si un usuario reporta miniaturas rotas: revise pestaña Network → vea la petición /thumb-signed → estado 5xx = problema del backend (worker crasheó, revise logs). 404 = registro fuente faltante o foto borrada. 200 con tamaño <1KB = payload corrupto en caché, clic en Re-index.",
      "Tormentas de Cloudflare 520 (cada foto fallando en paralelo) son una firma del worker siendo OOM-killed. El semáforo + pipeline de render-once-cache-thrice agregado en iter59 lo previene — si las ve otra vez, revise env JOB_PHOTO_RENDER_CONCURRENCY (default 2) y revise memoria del contenedor.",
    ],
    cheatSheet_es: [
      "Auto-warm cada 10 min. TTL caché 7 días. HEIC soportado.",
      "Después del despliegue → clic en Re-index una vez. Listo.",
      "Concurrencia de render topada en 2 (semáforo). Frontend topado en 6 mosaicos en vuelo.",
    ],
  },

  // ============================================================
  // ADMIN (new lessons 11-14)
  // ============================================================
  "admin-11-hr-users": {
    title_es: "Lección 11 — Usuarios y Accesos de RRHH",
    why_es: "Admin gestiona el roster de RRHH. Agrega/quita personal, emite contraseñas temporales, deshabilita cuentas. Los usuarios de RRHH solo ven datos con alcance HR — sin superficies PM ni financieras.",
    steps_es: [
      "Consola Admin → 'Usuarios y Accesos de RRHH' (icono morado, entre Usuarios de Taller y Auto-Ruteo de Correo).",
      "Agregar Usuario: nombre + email + teléfono + rol. Clic en Agregar — un correo de bienvenida sale por Resend con contraseña temporal.",
      "Emitir / Resetear contraseña: clic en el icono de llave. Dos opciones: 'Email al Usuario' o 'Mostrar en pantalla'. Campo opcional de contraseña personalizada.",
      "Deshabilitar / habilitar: clic en la insignia activo/deshabilitado para alternar.",
      "Editar y borrar: iconos lápiz y basurero. Borrar requiere confirmación.",
    ],
    tips_es: [
      "Al resetear contraseña el token anterior queda inválido automáticamente.",
      "Si RESEND_API_KEY no está configurado, el correo de bienvenida se registra en logs en vez de enviarse.",
    ],
    cheatSheet_es: [
      "Agregar · Resetear contraseña · Deshabilitar · Borrar.",
      "Rotación de contraseña invalida tokens viejos.",
    ],
  },
  "admin-12-terminations": {
    title_es: "Lección 12 — Tablero de Terminaciones de Empleados",
    why_es: "Reemplaza el viejo registro de Notas del Supervisor. Tablero HR dedicado con filtros de elegibilidad de recontratación, estado de equipo pendiente, banderas de policía y trazabilidad de rechazo/no-presente.",
    steps_es: [
      "Consola Admin → mosaico Terminaciones (caja roja) — o directamente en /admin/terminations.",
      "Tira de 5 estadísticas: Total · Recontratar Sí · Recontratar No · Equipo Pendiente · Policía.",
      "Búsqueda + 4 chips de filtro de recontratación: Todas / Sí / No / Condicional.",
      "Columnas: Fecha · Empleado · Supervisor · Trabajo · Tipo · Recontratar · Banderas · Ver.",
      "Acción Ver → cajón completo de Liderazgo de Campo + descarga PDF.",
    ],
    tips_es: [
      "El tablero es solo-admin por diseño — HR ve las terminaciones en su lista de registros de Liderazgo de Campo.",
      "El conteo de equipo pendiente se actualiza en vivo al filar un Retorno de Equipo.",
    ],
    cheatSheet_es: [
      "/admin/terminations — tablero HR dedicado.",
      "Filtros: chips de recontratación. Banderas: pendiente · policía · rechazó · ausente.",
    ],
  },
  "admin-13-hub-banners": {
    title_es: "Lección 13 — Sistema de Banners del Hub",
    why_es: "Alertas a nivel sitio con 9 plantillas precargadas, 4 niveles de severidad, reconocimiento obligatorio opcional, auto-traducción al español, trazabilidad, exportación PDF/CSV, clonar/rebroadcast y archivo.",
    steps_es: [
      "Consola Admin → panel 'Mensajes de Banner del Hub'. Chips de plantilla arriba + formulario abajo.",
      "Elija plantilla → autocompleta título + cuerpo + severidad. O escriba desde cero.",
      "Severidad: INFO (azul) · AVISO (ámbar) · ADVERTENCIA (naranja) · CRÍTICO (rojo). Críticos bloquean la página hasta reconocer.",
      "Expiración opcional. Reconocimiento Obligatorio: modal de pantalla completa hasta tocar 'Reconozco'.",
      "Auto-Español: 'Vista previa en español' antes de publicar. Traduce con Claude Haiku 4.5.",
      "Después de publicar: 4 iconos. Reloj = trazabilidad · Copiar = clonar · Lápiz = editar · Basurero = borrar.",
    ],
    tips_es: [
      "Visitas OSHA / paros de seguridad — use Reconocimiento Obligatorio. Saque el PDF de trazabilidad como respaldo legal.",
      "Los banners se actualizan cada 60 seg — un banner publicado a las 10:00 aparece en cada teléfono para las 10:01 sin recargar.",
    ],
    cheatSheet_es: [
      "9 plantillas · 4 severidades · auto-español.",
      "Reconocimiento Obligatorio = modal hasta tocar.",
      "Reloj = trazabilidad · PDF/CSV · Clonar rebroadcast.",
    ],
  },
  "admin-14-cloud-archives": {
    title_es: "Lección 14 — Archivos en la Nube (Cloudflare R2)",
    why_es: "Archivos completos del sistema suben a Cloudflare R2 cada noche a las 03:00 UTC. Incluye cada registro + fotos. Un solo zip autónomo — restaura todo el Hub aún si R2 fuera inalcanzable.",
    steps_es: [
      "Consola Admin → panel 'Archivos en la Nube · Cloudflare R2' (debajo de Respaldos Almacenados).",
      "Botón 'Construir archivo completo ahora' → dispara la construcción. Polling cada 4 seg. Termina en ~40 seg típico.",
      "Tira de horario nocturno muestra la próxima hora (default 03:00 UTC) y la última fecha exitosa.",
      "Lista de archivos: más nuevos primero, anchors clic-para-descargar con URLs presignadas Cloudflare a 7 días.",
      "Correos de heartbeat embeben el último link R2 — su correo diario llega con descarga de un clic.",
    ],
    tips_es: [
      "Costo R2: ~$0.015/GB-mes × 0.6 GB ≈ <$0.01/mes. Egress dentro de Cloudflare es gratis.",
      "Opciones de pull para IT: vía /api/admin/backups-list-r2 + URL presignada, o token R2 read-only directo al bucket.",
    ],
    cheatSheet_es: [
      "Construir archivo ahora → zip R2 listo en ~40 seg.",
      "Nocturno 03:00 UTC. Correo heartbeat embebe el último link.",
      "URLs presignadas 7 días · seguro para compartir con IT.",
    ],
  },

  // ============================================================
  // HR (8 lessons) — concise EN→ES mirror
  // ============================================================
  "hr-01-portal-intro": {
    title_es: "Lección 1 — Resumen del Portal de RRHH",
    why_es: "El Portal de RRHH es un alcance aislado y de solo lectura. RRHH ve registros de empleado y datos de nómina — nunca superficies PM/financieras. Tokens admin NO funcionan en rutas HR; los usuarios HR ingresan con su propio correo + contraseña.",
    steps_es: [
      "Abra https://mascidocs.com/hr/login (o haga clic en la tarjeta de Portal de RRHH del Hub público).",
      "Ingrese con correo + contraseña. Cuentas nuevas son redirigidas a Cambiar Contraseña.",
      "El Hub RRHH muestra 5 mosaicos: Registros de Liderazgo · Responsabilidad del Empleado · Verificación de Tiempo · Variación de Nómina · Registros de Capacitación.",
      "Use el botón Salir (arriba derecha) en cualquier momento. Las sesiones se limpian al navegar fuera de /hr.",
      "Use el botón EN/ES en el encabezado para cambiar idioma.",
    ],
    tips_es: [
      "¿Olvidó la contraseña? Clic en 'Olvidó contraseña?' — un correo de reseteo llega en segundos.",
      "Su token HR se borra el momento que sale de /hr/* — esto es intencional. Vuelva a ingresar para regresar.",
    ],
    cheatSheet_es: [
      "Ingrese en /hr/login · 5 mosaicos.",
      "RRHH es solo lectura · sin PM / financieras.",
      "Sesiones se borran al salir de /hr/*.",
    ],
  },
  "hr-02-field-leadership-records": {
    title_es: "Lección 2 — Registros de Liderazgo de Campo (Solo Lectura)",
    why_es: "Cada amonestación, coaching, reconocimiento, evaluación, terminación y entrega de equipo presentada por supervisores es visible aquí. Usado para limpieza de salida, resolución de disputas e investigación histórica.",
    steps_es: [
      "Hub RRHH → Registros de Liderazgo de Campo.",
      "Búsqueda: tipo empleado, supervisor, número de proyecto, o nombre del proyecto. Apply.",
      "Dropdown Tipo de Formulario filtra a un tipo (Amonestación, Terminación, Entrega de Equipo, etc.).",
      "Icono ojo → cajón de detalle con cada campo del registro original.",
      "Icono PDF → descarga del PDF oficial MASCI.",
    ],
    tips_es: [
      "Las terminaciones tienen su propio tablero Admin con filtros de recontratación.",
      "Las fotos se transmiten desde el archivo R2 — no se guardan en su dispositivo.",
    ],
    cheatSheet_es: [
      "Buscar por nombre/supervisor/proyecto · filtrar por tipo.",
      "Ojo = detalle · PDF = descargar.",
    ],
  },
  "hr-03-employee-accountability": {
    title_es: "Lección 3 — Responsabilidad del Empleado (Limpieza de Salida)",
    why_es: "Antes de aprobar una salida debe saber qué equipo sigue en posesión del empleado, sus amonestaciones activas, y su historial de capacitación. Esta página da la respuesta consolidada en una búsqueda.",
    steps_es: [
      "Hub RRHH → Responsabilidad del Empleado.",
      "Escriba ≥2 caracteres del nombre → Buscar.",
      "Tira de estadísticas: registros LC · amonestaciones activas · equipo pendiente · capacitaciones.",
      "Si aparece la insignia 'TERMINATED' — ya hay terminación en archivo.",
      "Tabla Equipo Pendiente (encabezado rojo) — cada línea sin devolver. DEBE recuperarse antes de la limpieza de salida.",
      "Tabla Registros LC — cada registro para el empleado, más nuevos primero.",
      "Tabla Capacitación — tracks completados.",
    ],
    tips_es: [
      "Use la tira de chips por-tipo para triaje rápido.",
      "Equipo Pendiente se calcula en vivo — un Retorno presentado lo limpia automáticamente.",
    ],
    cheatSheet_es: [
      "Buscar nombre → conteos + 3 tablas.",
      "Tabla ROJA de equipo = recuperar antes de salida.",
      "Insignia TERMINATED = revisar terminación existente primero.",
    ],
  },
  "hr-04-time-verification": {
    title_es: "Lección 4 — Verificación de Tiempo",
    why_es: "Supervisores envían Reportes Diarios con horas de cuadrilla MASCI cada turno. Esta vista las consolida por empleado y por semana para que RRHH pueda cruzar con la nómina Exact sin abrir 60 reportes individuales.",
    steps_es: [
      "Hub RRHH → Verificación de Tiempo.",
      "Fin de Semana default hoy (ventana Lun–Dom).",
      "Filtros: Empleado, Proyecto #, Supervisor. Apply.",
      "Tira: Total Empleados · Horas Totales · Regular · Sobretiempo. OT > 0 se vuelve ámbar.",
      "Alterne 'Consolidado Semanal' vs. 'Detalle por Día'.",
      "Bandera roja 'Sin Almuerzo' = día ≥6 hrs sin almuerzo registrado.",
      "Icono descarga junto a Apply → CSV listo para revisión de nómina.",
    ],
    tips_es: [
      "División Regular vs. OT es estándar Florida (>8 hr/día = OT).",
      "Notas, fotos, materiales del Reporte Diario se omiten — solo campos de nómina.",
    ],
    cheatSheet_es: [
      "Fin de semana = Domingo. Lun–Dom se consolida.",
      "Semanal vs. Por-Día. CSV listo para pegar en Exact.",
      "Bandera Sin-Almuerzo = 6+ hr sin descanso.",
    ],
  },
  "hr-05-payroll-variance": {
    title_es: "Lección 5 — Variación de Nómina (Diff CSV Exact)",
    why_es: "Cierra la brecha entre Verificación de Tiempo y el sistema de nómina Exact. Pegue el export de Exact, la plataforma empareja cada fila con las horas reportadas por el supervisor y marca cada variación ≥ 15 minutos.",
    steps_es: [
      "Hub RRHH → Variación de Nómina.",
      "Fije Fin de Semana. Opcionalmente ajuste el Umbral (minutos) — 15 default.",
      "Pegue su CSV Exact en el área de texto. Columnas: Nombre Empleado (requerido), Horas Regulares O Horas Totales (requerido), Sobretiempo, ID Empleado, Fin Semana.",
      "Clic 'Ejecutar Variación'. Crea un lote.",
      "Tabla: Empleado · Exact Reg/OT/Total · MASCI Total · Diff · Bandera · Decisión.",
      "Colores: VERDE = match (≤1 min) · ÁMBAR = menor · ROJO = marcado · ROSA = falta en nómina.",
      "Botones Aprobar / Disputar persisten al instante.",
      "Botón CSV (arriba) descarga la variación completa con decisiones.",
    ],
    tips_es: [
      "Emparejamiento usa 'apellido:inicial-nombre'. Si difiere entre Exact y campo aparece como No-Emparejado.",
      "Filas ROSA = empleado en campo pero no en Exact. ID faltante o nuevo no onboardeado.",
      "Correo semanal cada domingo 18:00 UTC al distro HR con CSV adjunto.",
    ],
    cheatSheet_es: [
      "Pegar CSV → Ejecutar → Aprobar/Disputar.",
      "Umbral 15 min default. VERDE/ÁMBAR/ROJO/ROSA.",
      "Auto-correo domingo 18:00 UTC.",
    ],
  },
  "hr-06-training-records": {
    title_es: "Lección 6 — Registros de Capacitación",
    why_es: "Sigue las lecciones del Hub de Capacitación completadas por empleado. Requerido para OSHA y para probar competencia antes de asignar equipo nuevo. Solo lectura — completaciones se registran automáticamente.",
    steps_es: [
      "Hub RRHH → Registros de Capacitación.",
      "Filtre por Empleado. Apply.",
      "Columnas: Empleado · Track · Completado · Puntaje.",
      "Si está vacío (preview/instalación nueva) muestra estado amable — se llena automáticamente.",
    ],
    tips_es: [
      "Si un empleado muestra cero pero sabe completó, pida a Admin revisar el grabador del Hub.",
    ],
    cheatSheet_es: [
      "Roster solo-lectura. Filtre por empleado.",
      "Completaciones = automático desde Hub.",
    ],
  },
  "hr-07-offboarding-workflow": {
    title_es: "Lección 7 — Flujo End-to-End de Limpieza de Salida",
    why_es: "Camina la secuencia exacta que RRHH sigue cuando un empleado se va — desde que el supervisor presenta la terminación hasta el corte final de nómina.",
    steps_es: [
      "Paso 1 — Supervisor presenta Terminación → Admin recibe correo Y aparece en /admin/terminations. RRHH también la ve en Hub → Registros LC.",
      "Paso 2 — Hub RRHH → Responsabilidad → buscar el nombre. Revise conteos y tabla de Equipo Pendiente.",
      "Paso 3 — Si hay Equipo Pendiente: pida al supervisor presentar un Retorno de Equipo por cada item. Equipo Dañado/Faltante/Perdido se marca automáticamente contra el valor de reemplazo. Repita la búsqueda hasta que la tabla esté limpia.",
      "Paso 4 — Hub RRHH → Verificación de Tiempo → estrechar a la última semana. Confirme horas finales del supervisor.",
      "Paso 5 — Hub RRHH → Variación de Nómina → suba el CSV Exact. Apruebe/dispute. Flujo de último cheque defendible end-to-end.",
      "Paso 6 — Archive el PDF de Terminación (Hub → Liderazgo → icono PDF) en el archivo del empleado.",
    ],
    tips_es: [
      "Nunca omita Paso 3. Equipo pendiente es la fuente #1 de disputas post-salida.",
      "Si el empleado rehúsa firmar, el supervisor usó 'Rehusó Firmar' o 'No Presente' — válidas legalmente por los campos de testigo.",
    ],
    cheatSheet_es: [
      "1. Terminación → 2. Responsabilidad → 3. Cerrar equipo → 4. Verificar horas → 5. Variación → 6. Archivar PDF.",
    ],
  },
  "hr-08-your-account": {
    title_es: "Lección 8 — Su Cuenta y Contraseña de RRHH",
    why_es: "Cómo funciona su cuenta HR, cómo cambiar la contraseña, cómo recuperarla, y qué hace Admin por usted si es necesario.",
    steps_es: [
      "Su cuenta es creada por Admin. Recibe correo de bienvenida con contraseña temporal.",
      "Primer ingreso lo redirige a Cambiar Contraseña — elija 8+ caracteres.",
      "Cambie manualmente en cualquier momento: /hr/change-password.",
      "¿Olvidó? Clic 'Olvidó contraseña?' → email → link de reseteo a 30 min.",
      "¿Bloqueado? Contacte Admin — puede re-habilitar o emitir nueva contraseña temporal.",
    ],
    tips_es: [
      "Tokens se invalidan al cambiar contraseña — todo otro dispositivo cierra sesión.",
      "Use una frase memorable larga, no 'Password1!'.",
    ],
    cheatSheet_es: [
      "Correo bienvenida → Cambiar Contraseña → adentro.",
      "¿Olvidó? Reseteo self-service, 30 min TTL.",
      "¿Bloqueado? Admin re-habilita.",
    ],
  },
};
