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
    why_es: "La consola del taller es donde los mecánicos ven cada Pre-Op enviado por el campo, qué unidades están marcadas y qué requiere atención. Un solo lugar para mantener la flota funcionando.",
    steps_es: [
      "Vaya a /shop/login → ingrese la contraseña del taller → aterriza en la Consola del Taller.",
      "La barra superior muestra 4 estadísticas: Inspecciones registradas, Unidades marcadas FALLA, Firmas del taller, Equipo en la flota.",
      "Panel izquierdo: cola de Artículos Abiertos (cada FALLA sin firmar). Panel derecho: Tendencias (tasa de aprobados por unidad/categoría).",
      "Más abajo: Inspecciones Pre-Op Recientes (lista completa), Lista de Equipo (flota buscable), Catálogo de Partes.",
      "Cierre sesión arriba a la derecha cuando termine en una computadora compartida.",
    ],
    tips_es: [
      "Admin también ve todo lo que ve el taller. Los Gerentes ven tendencias pero no pueden firmar artículos.",
      "La bandera 'Todo en orden.' en Artículos Abiertos es la meta — cero fallas sin firmar.",
    ],
    cheatSheet_es: [
      "4 estadísticas arriba. Cola de Artículos Abiertos es la prioridad.",
      "Cada FALLA debe firmarse o la unidad sigue FDS.",
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
      "Vaya a /pm/login → ingrese la contraseña PM (Happy123!). Aterriza en Registros y Formularios.",
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
    why_es: "Cada formulario enviado desde el campo se envía por correo automáticamente al Gerente relevante (basado en el trabajo elegido) y siempre con copia al Gerente de Seguridad. Si el Gerente de un trabajo cambia, actualizar la tabla de ruteo actualiza cada correo futuro — sin configuración manual por formulario.",
    steps_es: [
      "Portal de Gestión → panel de Ruteo de Correos (en la lista de Gerentes / maestro de Trabajos).",
      "Cada fila de Gerente: nombre, correo, teléfono, interruptor activo.",
      "Abra el maestro de Trabajos → cada trabajo tiene un campo 'Gerente de Proyecto' y un campo 'Correo del Gerente'. Cuando se envía un Reporte Diario para ese trabajo, la app busca el Correo del Gerente y le copia automáticamente.",
      "Para cambiar quién está en un trabajo: edite la fila del trabajo → elija un nuevo Gerente del menú → el correo se actualiza automáticamente → guarde.",
      "Pruébelo: envíe un formulario de prueba desde el campo, revise la bandeja del Gerente en 60 segundos.",
    ],
    tips_es: [
      "AUTO_EMAIL_REPORTS es un interruptor a nivel env. Producción lo tiene ON. Preview lo tiene OFF para que las pruebas no quemen el cupo diario.",
      "Si un Gerente no recibe correos, revise: (1) interruptor activo, (2) asignación del Gerente al Trabajo, (3) carpeta de spam, (4) variable env en el servidor desplegado.",
    ],
    cheatSheet_es: [
      "Trabajo → Gerente → Correo → Reporte Diario copia al Gerente automático.",
      "Cambiar Gerente en un trabajo = todos los correos futuros re-ruteados.",
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
      "Tres niveles de contraseña: Admin (MASCI1982!) ve todo. Gerente (Happy123!) ve lo diario pero NO respaldo/restauración. Taller (Nothappy123!) solo ve equipo + firmas Pre-Op.",
      "Tarjeta Admin en el área inferior del Hub. /admin/login con MASCI1982!. Después del login aterriza en Registros y Formularios (idéntico a la vista PM) + la sección Recuperación del Sistema abajo.",
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
};
