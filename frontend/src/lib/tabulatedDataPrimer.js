/**
 * tabulatedDataPrimer.js — Full text of the United Rentals "What is
 * Tabulated Data?" explainer, translated to Spanish alongside the
 * English original. Used by:
 *   - /trench-boxes → "¿Qué son los Datos Tabulados?" panel (public crew-facing)
 *   - /admin/trench-boxes → same primer (admin view)
 *
 * Source: United Rentals presentation © 2020 (included as the first file
 * in /app/frontend/src/assets — crew should read the PDF AND this
 * summary). Structure mirrors the original slide-by-slide order so a
 * crew member in the field can follow along.
 *
 * IMPORTANT: Translated professionally for construction safety context —
 * key OSHA terms (shield, spreader, surcharge, competent person, P.E.)
 * use industry-standard Spanish (escudo, separador, sobrecarga, persona
 * competente, Ingeniero Profesional — I.P.).
 */

export const TABULATED_DATA_PRIMER = {
  intro: {
    en: {
      title: "What is Tabulated Data?",
      subtitle: "And why it matters in the field",
      hook: "Every trench shield on a MASCI job has an engineer-approved data sheet that tells you exactly how deep you can dig, in what kind of soil, with what spreaders, and under what conditions. Read it before you enter the box. Every time.",
    },
    es: {
      title: "¿Qué son los Datos Tabulados?",
      subtitle: "Y por qué son importantes en el campo",
      hook: "Cada escudo de zanja en un trabajo de MASCI tiene una hoja de datos aprobada por un ingeniero que le dice exactamente qué tan profundo puede excavar, en qué tipo de suelo, con qué separadores y bajo qué condiciones. Léala antes de entrar al escudo. Siempre.",
    },
  },

  sections: [
    // -------------------------------------------------------------
    {
      id: "osha-definition",
      en: {
        heading: "OSHA's Definition",
        body: [
          "Tabulated Data means tables and charts approved by a registered professional engineer and used to design and construct a protective system.",
          "The document must be in written form on the jobsite during construction of the protective system.",
          "'Construct' means to place, position, or reposition — NOT just assemble.",
        ],
      },
      es: {
        heading: "Definición de OSHA",
        body: [
          "Los Datos Tabulados son tablas y gráficos aprobados por un ingeniero profesional registrado y utilizados para diseñar y construir un sistema de protección.",
          "El documento debe estar por escrito en el sitio de trabajo durante la construcción del sistema de protección.",
          "'Construir' significa colocar, posicionar o reposicionar — NO solo ensamblar.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "protective-systems",
      en: {
        heading: "Protective System Options",
        body: [
          "OSHA Charts — Sloping and Benching, Timber Shoring, Aluminum Hydraulic Shoring.",
          "Designs by a Registered P.E. — Manufactured Trench Shields, Site-Specific Designs.",
          "All options were produced by professional engineers. All data is presented as tables (rows and columns) — learn to read them.",
        ],
      },
      es: {
        heading: "Opciones de Sistemas de Protección",
        body: [
          "Cuadros OSHA — Taludes y Bancos, Entibación de Madera, Entibación Hidráulica de Aluminio.",
          "Diseños por un I.P. Registrado — Escudos de Zanja Fabricados, Diseños Específicos del Sitio.",
          "Todas las opciones fueron creadas por ingenieros profesionales. Todos los datos se presentan como tablas (filas y columnas) — aprenda a leerlos.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "osha-subpart-p",
      en: {
        heading: "OSHA Subpart P — The Rule",
        body: [
          "Shield (Shield system) means a structure that is able to withstand the forces imposed on it by a cave-in and thereby protect employees within the structure.",
          "Protective systems will have the capacity to resist — without failure — all loads that are intended or could be reasonably expected to be applied or transmitted to the system.",
          "Shield systems shall NOT be subjected to loads exceeding those which the system was designed to withstand.",
        ],
      },
      es: {
        heading: "Subparte P de OSHA — La Regla",
        body: [
          "Escudo (Sistema de escudo) significa una estructura capaz de resistir las fuerzas impuestas por un derrumbe y proteger así a los empleados dentro de la estructura.",
          "Los sistemas de protección tendrán la capacidad de resistir — sin fallar — todas las cargas que se pretendan o que razonablemente se espere que sean aplicadas o transmitidas al sistema.",
          "Los sistemas de escudo NO deben someterse a cargas que excedan aquellas para las que el sistema fue diseñado.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "data-components",
      en: {
        heading: "What's in a Tabulated Data Sheet",
        body: [
          "Identity and contact info of the manufacturer.",
          "Soil classification (OSHA Type A / B / C with lateral-earth-pressure values 25 / 35 / 45 / 60 / 80 psf).",
          "Maximum working depths for each soil type.",
          "Capacity of the shield and allowable loads.",
          "Assembly and inspection instructions.",
          "Safety recommendations and limits.",
          "Spreader size, length, and placement requirements.",
          "A P.E.'s stamp and signature — if it's missing, the data is not valid.",
        ],
      },
      es: {
        heading: "Qué hay en una Hoja de Datos Tabulados",
        body: [
          "Identidad e información de contacto del fabricante.",
          "Clasificación del suelo (OSHA Tipo A / B / C con valores de presión lateral de tierra 25 / 35 / 45 / 60 / 80 psf).",
          "Profundidades máximas de trabajo para cada tipo de suelo.",
          "Capacidad del escudo y cargas permitidas.",
          "Instrucciones de ensamblaje e inspección.",
          "Recomendaciones y límites de seguridad.",
          "Tamaño, longitud y requisitos de colocación del separador.",
          "Sello y firma de un I.P. — si falta, los datos no son válidos.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "competent-person",
      en: {
        heading: "The Competent Person — Who Is That?",
        body: [
          "Someone knowledgeable and capable of complying with all federal regulations, state and local laws, and ordinances.",
          "Trained and experienced in the proper use of trench shields, safe excavation practices, and soil classification methods.",
          "MUST direct and control the use of every trench shield on the job.",
          "Classifies the soil IN ACCORDANCE with OSHA guidelines — no guessing.",
        ],
      },
      es: {
        heading: "La Persona Competente — ¿Quién es?",
        body: [
          "Alguien con conocimiento y capacidad para cumplir con todas las regulaciones federales, leyes estatales y locales, y ordenanzas.",
          "Capacitado y con experiencia en el uso adecuado de escudos de zanja, prácticas seguras de excavación y métodos de clasificación de suelos.",
          "DEBE dirigir y controlar el uso de cada escudo de zanja en el trabajo.",
          "Clasifica el suelo DE ACUERDO con las pautas de OSHA — sin adivinar.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "soil-ends",
      en: {
        heading: "Managing Soil at the End of a Shield",
        body: [
          "Shields are designed for LINEAR trench application.",
          "The ends of shields were intended to be OPEN, with no vertical wall of soil pressing against them.",
          "Soils at the end should be no more steep than 1½ : 1 (that's a 1½-foot horizontal run for every 1 foot of depth).",
          "If you must cap the ends with steel plate, follow the manufacturer's end-load technical data sheet — it has its own depth limits.",
        ],
      },
      es: {
        heading: "Manejo del Suelo al Final de un Escudo",
        body: [
          "Los escudos están diseñados para aplicación LINEAL en zanjas.",
          "Los extremos de los escudos deben estar ABIERTOS, sin ninguna pared vertical de suelo presionándolos.",
          "Los suelos al final no deben tener una pendiente más pronunciada que 1½ : 1 (eso es 1½ pie de distancia horizontal por cada 1 pie de profundidad).",
          "Si debe cubrir los extremos con placa de acero, siga la hoja técnica de carga final del fabricante — tiene sus propios límites de profundidad.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "common-mistakes",
      en: {
        heading: "Common Practices That CONFLICT With Tabulated Data",
        body: [
          "End loading (soil pressing against the open ends).",
          "Side loading (uneven soil pressure across the panels).",
          "Inappropriate spreader usage or placement.",
          "Failure to comply with surcharge limits.",
          "Active vehicular traffic loads on top of the shield.",
          "Lack of groundwater extraction (water adds pressure).",
          "Using manufactured goods that have NO tabulated data at all.",
          "Incorrect box positioning or movement in the trench.",
          "ANY deviation from the manufacturer's data requires WRITTEN P.E. approval before work continues.",
        ],
      },
      es: {
        heading: "Prácticas Comunes que ENTRAN EN CONFLICTO con los Datos Tabulados",
        body: [
          "Carga en los extremos (suelo presionando contra los extremos abiertos).",
          "Carga lateral (presión de suelo desigual en los paneles).",
          "Uso o colocación inadecuada de los separadores.",
          "No cumplir con los límites de sobrecarga.",
          "Cargas de tráfico vehicular activo sobre el escudo.",
          "Falta de extracción de agua subterránea (el agua añade presión).",
          "Usar bienes fabricados que NO tienen datos tabulados en absoluto.",
          "Posicionamiento o movimiento incorrecto del escudo en la zanja.",
          "CUALQUIER desviación de los datos del fabricante requiere aprobación ESCRITA del I.P. antes de continuar el trabajo.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "surcharge",
      en: {
        heading: "Surcharge Loads — 72 psf Maximum",
        body: [
          "Surcharge = extra load from stuff near the trench (heavy equipment, spoil piles, traffic, vibrations, adjacent buildings).",
          "'Adjacent' means within a horizontal distance from the edge of the trench equal to the depth of the trench. A 10-ft deep trench has a 10-ft adjacent zone.",
          "Tabulated data depth ratings typically account for a MAX 72 psf lateral surcharge. Above that, the shield is NOT rated.",
          "The competent person MUST verify this limit is not exceeded — if it is, call a P.E. for written direction.",
          "Surcharge can reduce your allowable working depth dramatically. Don't skip this step.",
        ],
      },
      es: {
        heading: "Cargas de Sobrecarga — 72 psf Máximo",
        body: [
          "Sobrecarga = carga adicional de cosas cerca de la zanja (equipo pesado, pilas de material, tráfico, vibraciones, edificios adyacentes).",
          "'Adyacente' significa dentro de una distancia horizontal desde el borde de la zanja igual a la profundidad de la zanja. Una zanja de 10 pies de profundidad tiene una zona adyacente de 10 pies.",
          "Los datos tabulados de profundidad típicamente consideran una sobrecarga lateral MÁXIMA de 72 psf. Por encima de eso, el escudo NO está calificado.",
          "La persona competente DEBE verificar que este límite no se exceda — si lo hace, llame a un I.P. para dirección escrita.",
          "La sobrecarga puede reducir dramáticamente su profundidad de trabajo permitida. No omita este paso.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "spreaders",
      en: {
        heading: "Radial Load on Spreaders",
        body: [
          "Typical steel trench shields use 8-inch Schedule 80 pipe spreaders.",
          "The spreader's STRENGTH is along its axis (axial load).",
          "Axial loads COMBINED with radial (sideways) loads were NOT part of the design calculation for working depth.",
          "The LOWERMOST spreader — the one under compression — is the most susceptible to failure if you add radial load.",
          "Never hang material on a spreader. Never climb on one. Never use one to lift/move the box.",
        ],
      },
      es: {
        heading: "Carga Radial en los Separadores",
        body: [
          "Los escudos típicos de zanja de acero usan separadores de tubería Cédula 80 de 8 pulgadas.",
          "La RESISTENCIA del separador está a lo largo de su eje (carga axial).",
          "Las cargas axiales COMBINADAS con cargas radiales (laterales) NO fueron parte del cálculo de diseño para la profundidad de trabajo.",
          "El separador MÁS BAJO — el que está bajo compresión — es el más susceptible a fallar si añade carga radial.",
          "Nunca cuelgue material de un separador. Nunca trepe uno. Nunca use uno para levantar/mover el escudo.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "deviation",
      en: {
        heading: "When Deviation Is Required",
        body: [
          "A registered P.E. engineer MUST approve any deviation.",
          "The approval MUST be in written form BEFORE changes are made.",
          "The approval document is treated the same as tabulated data — keep it on the jobsite.",
          "Can be a Technical Data Sheet, an Approval Letter, or a Site-Specific Plan.",
          "Limits of the deviation must be specific (which box, what depth, what soil type, what conditions).",
          "If you're not 100% sure what you're doing counts as a deviation — stop, call the office, ask.",
        ],
      },
      es: {
        heading: "Cuándo se Requiere una Desviación",
        body: [
          "Un ingeniero I.P. registrado DEBE aprobar cualquier desviación.",
          "La aprobación DEBE estar por escrito ANTES de hacer cambios.",
          "El documento de aprobación se trata igual que los datos tabulados — manténgalo en el sitio de trabajo.",
          "Puede ser una Hoja de Datos Técnicos, una Carta de Aprobación o un Plan Específico del Sitio.",
          "Los límites de la desviación deben ser específicos (qué escudo, qué profundidad, qué tipo de suelo, qué condiciones).",
          "Si no está 100% seguro de que lo que está haciendo cuenta como desviación — deténgase, llame a la oficina, pregunte.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "assembly",
      en: {
        heading: "Assembly & Disassembly — Every Time",
        body: [
          "Inspect shields before AND after assembly. A competent person does the inspection.",
          "All damage must be evaluated and repairs made under the direction of a registered P.E. Replace missing or damaged parts with OEM parts only.",
          "Rigging: evaluate rated capacity, inspect for damage, use only the designated lifting points on a shield.",
          "Tag lines keep crew members away from pinch points and overhead loads.",
          "All spreaders, pins, and keepers installed PER the manufacturer's tabulated data — exactly the right spec, quantity, and position.",
          "Lay the box flat on firm, level ground before dismantling. Never dismantle on a slope or dunnage.",
          "Never enter a box while an excavator is moving it. Never climb spreaders. Never exit a box into an unsupported area.",
          "Watch for unbalanced loads during lift — a crane and rigging plan may be required for long arch-spreader extensions.",
        ],
      },
      es: {
        heading: "Ensamblaje y Desensamblaje — Cada Vez",
        body: [
          "Inspeccione los escudos ANTES Y DESPUÉS del ensamblaje. Una persona competente realiza la inspección.",
          "Todo daño debe ser evaluado y las reparaciones hechas bajo la dirección de un I.P. registrado. Reemplace partes faltantes o dañadas solo con partes del fabricante original (OEM).",
          "Aparejos: evalúe la capacidad nominal, inspeccione por daños, use solo los puntos de elevación designados en un escudo.",
          "Las líneas guía mantienen a los miembros del equipo alejados de puntos de pellizco y cargas elevadas.",
          "Todos los separadores, pasadores y retenedores instalados SEGÚN los datos tabulados del fabricante — exactamente la especificación, cantidad y posición correctas.",
          "Coloque el escudo plano sobre suelo firme y nivelado antes de desmontar. Nunca desmonte en una pendiente o sobre soportes.",
          "Nunca entre a un escudo mientras una excavadora lo está moviendo. Nunca trepe separadores. Nunca salga de un escudo a un área sin soporte.",
          "Vigile cargas desequilibradas durante la elevación — un plan de grúa y aparejos puede ser requerido para extensiones largas de separador de arco.",
        ],
      },
    },

    // -------------------------------------------------------------
    {
      id: "bottom-line",
      en: {
        heading: "The Bottom Line",
        body: [
          "Tabulated data is SPECIFIC to each make and model of trench shield. Different manufacturers = different data.",
          "Soil type is CRITICAL — classification is non-negotiable and done by a competent person.",
          "Surcharge loads reduce your allowable depth. Account for them.",
          "Any deviation = written P.E. approval BEFORE work.",
          "Proper assembly and handling are just as critical as the design — shields can fail even when correctly rated if installed wrong.",
          "Read the data sheet BEFORE you get in the box. Every job. Every time.",
        ],
      },
      es: {
        heading: "El Resultado Final",
        body: [
          "Los datos tabulados son ESPECÍFICOS para cada marca y modelo de escudo de zanja. Diferentes fabricantes = diferentes datos.",
          "El tipo de suelo es CRÍTICO — la clasificación es innegociable y la hace una persona competente.",
          "Las cargas de sobrecarga reducen su profundidad permitida. Téngalas en cuenta.",
          "Cualquier desviación = aprobación ESCRITA del I.P. ANTES del trabajo.",
          "El ensamblaje y manejo adecuados son tan críticos como el diseño — los escudos pueden fallar incluso cuando están correctamente calificados si se instalan mal.",
          "Lea la hoja de datos ANTES de entrar al escudo. Cada trabajo. Siempre.",
        ],
      },
    },
  ],

  footer: {
    en: {
      cta: "Questions? Ask your competent person on site, call the office, or contact United Rentals directly — they're a phone call away.",
      attribution:
        "Adapted from the United Rentals Tabulated Data training presentation, © 2020 United Rentals, Inc. Original PDF available in the Tabulated Data Library below.",
    },
    es: {
      cta: "¿Preguntas? Pregunte a su persona competente en el sitio, llame a la oficina o contacte directamente a United Rentals — están a una llamada telefónica de distancia.",
      attribution:
        "Adaptado de la presentación de capacitación sobre Datos Tabulados de United Rentals, © 2020 United Rentals, Inc. El PDF original está disponible en la Biblioteca de Datos Tabulados a continuación.",
    },
  },
};
