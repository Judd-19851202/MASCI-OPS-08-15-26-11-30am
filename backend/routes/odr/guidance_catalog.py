"""
routes/odr/guidance_catalog.py — OGC catalog seed for ODR coaching prompts.

Doctrine:
  /app/memory/ODR_COACHING_GUIDANCE_ADDENDUM.md (O36–O50)

The catalog is the **canonical store** for prompt_key → bilingual
bullets. The substrate carries only `prompt_key` references on
`ReadinessSnapshot`; this module resolves them at surface render
time. The catalog is deterministic — never AI-generated at runtime.

Structure:
  CATALOG: Dict[prompt_key, PromptEntry]
  PromptEntry:
    en: List[str]                # ≥ 4 bullets
    es: List[str]                # ≥ 4 bullets
    severity: nudge|suggest|strong_suggest
    section: ODR section anchor
    crew_overrides: Dict[crew_type, {en, es}]  # crew-specific overlays

Resolution order:
  1. crew_overrides[crew_type]    if present
  2. base entry                   fallback

API helpers:
  resolve_prompt(prompt_key, crew_type, lang) → List[str]
  list_prompt_keys() → List[str]
  catalog_health() → Dict (coverage stats · for the bilingual probe)

Crew types (14):
  pipe · drainage (aliased to utility) · utility · paving (asphalt) ·
  milling · mot · concrete · structures · airfield · striping ·
  survey · demo · electrical · earthwork (aliased to grading) ·
  + legacy: grading · fine_grade · stabilization · curb · sidewalk · other
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── Crew type universe ───────────────────────────────────────────────
# Combines current enums.CrewType + directive-listed labels.
CATALOG_CREW_TYPES = [
    "pipe", "utility", "grading", "fine_grade", "stabilization",
    "concrete", "structures", "curb", "sidewalk", "milling", "paving",
    "mot", "survey", "airfield", "electrical",
    # Directive-listed (mapped from existing enum where possible)
    "drainage",     # alias for utility-pipe in field nomenclature
    "asphalt",      # alias for paving in field nomenclature
    "striping",     # MOT sub-discipline · separate in field nomenclature
    "demo",         # demolition · maps to "other" in current enum
    "earthwork",    # alias for grading
    "other",
]


# ── Base catalog (section × prompt_key) ──────────────────────────────
# Convention: prompt_key = "<section>.<verb>" or "<section>.<focus>"
# Severity: nudge (informational) · suggest (recommended) · strong_suggest (impactful)

CATALOG: Dict[str, Dict[str, Any]] = {

    # ── Project Snapshot (Section 1) ─────────────────────────────────
    "project.weather.verify_capture": {
        "section": "project",
        "severity": "nudge",
        "en": [
            "Confirm today's weather pulled from NOAA matches what you observed at the project.",
            "If conditions changed mid-shift, note the actual weather window in the daily summary.",
            "Take a quick photo of the sky and any standing water before crews start work.",
            "Mismatched weather is a top reason claims get rejected later — verify before signing.",
        ],
        "es": [
            "Confirme que el clima cargado de NOAA coincide con lo observado en el proyecto.",
            "Si las condiciones cambiaron durante el turno, anote la ventana real en el resumen del día.",
            "Tome una foto rápida del cielo y de cualquier acumulación de agua antes de comenzar.",
            "El clima incorrecto es una de las razones principales por las que se rechazan reclamos — verifíquelo antes de firmar.",
        ],
    },

    # ── Manpower (Section 3) ─────────────────────────────────────────
    "manpower.hours.complete_all_rows": {
        "section": "manpower",
        "severity": "strong_suggest",
        "en": [
            "Every person on the crew today should have hours recorded — including operators and ground men.",
            "If a worker only showed up part of the day, note the actual hours, not a standard shift.",
            "Overtime hours go in the overtime column — do not combine with straight time.",
            "Missing hours create payroll disputes and slow down weekly approvals.",
        ],
        "es": [
            "Cada persona del equipo hoy debe tener horas registradas — incluyendo operadores y obreros.",
            "Si un trabajador estuvo solo parte del día, anote las horas reales, no un turno estándar.",
            "Las horas extra van en la columna de tiempo extra — no las combine con tiempo regular.",
            "Las horas faltantes crean disputas de nómina y demoran las aprobaciones semanales.",
        ],
    },

    # ── Equipment (Section 4) ────────────────────────────────────────
    "equipment.utilization.record_idle_down": {
        "section": "equipment",
        "severity": "suggest",
        "en": [
            "Record idle hours separately when a machine was on site but not actively working.",
            "Down hours capture breakdowns — note severity if the machine needs Shop attention.",
            "Photos of any equipment damage or fluid leaks should be attached to the equipment row.",
            "Accurate idle vs. down hours drive the Shop's repair priority and your fleet utilization reports.",
        ],
        "es": [
            "Registre las horas de ralentí por separado cuando una máquina estuvo en sitio pero sin trabajar.",
            "Las horas de avería capturan paros — anote la severidad si necesita atención del Taller.",
            "Fotos de cualquier daño al equipo o fugas de fluido deben adjuntarse al renglón del equipo.",
            "Las horas correctas de ralentí vs. avería determinan la prioridad de reparación del Taller y los reportes de utilización.",
        ],
    },

    # ── Materials (Section 5.5) ──────────────────────────────────────
    "materials.tickets.attach_all": {
        "section": "materials",
        "severity": "strong_suggest",
        "en": [
            "Every delivery ticket should be photographed and attached to the materials row that day.",
            "Note rejected or short loads with the supplier name and the ticket number for follow-up.",
            "Wasted material (over-pour, spillage, contamination) should be quantified separately.",
            "Material tickets are the backbone of cost recovery for change orders — capture them all.",
        ],
        "es": [
            "Cada ticket de entrega debe fotografiarse y adjuntarse al renglón de materiales del día.",
            "Anote cargas rechazadas o cortas con el nombre del proveedor y el número de ticket para seguimiento.",
            "El material desperdiciado (sobre-vertido, derrames, contaminación) debe cuantificarse por separado.",
            "Los tickets de materiales son la base de la recuperación de costos para órdenes de cambio — capture todos.",
        ],
    },

    # ── Production (Section 6) ───────────────────────────────────────
    "production.add_first_segment": {
        "section": "production_segments",
        "severity": "strong_suggest",
        "en": [
            "Every ODR needs at least one production segment describing today's primary operation.",
            "Pick the crew type that matches what you actually did most of the day.",
            "If the crew split between two operations, add a segment for each.",
            "Empty production sections trigger PM follow-up — fill them out before submitting.",
        ],
        "es": [
            "Cada ODR necesita al menos un segmento de producción describiendo la operación principal del día.",
            "Elija el tipo de cuadrilla que coincida con lo que realmente hizo la mayor parte del día.",
            "Si la cuadrilla se dividió entre dos operaciones, agregue un segmento para cada una.",
            "Las secciones de producción vacías generan seguimiento del PM — llénelas antes de enviar.",
        ],
        # Crew-specific overlays
        "crew_overrides": {
            "pipe": {
                "en": [
                    "Record total LF installed by pipe size and material — RCP, HDPE, PVC, etc.",
                    "Capture from-structure and to-structure for every run so QC can verify alignment.",
                    "Note backfill type and compaction percentage for each segment laid today.",
                    "Photograph every joint inspection before backfill — that's your evidence chain.",
                ],
                "es": [
                    "Registre el total de pies lineales instalados por tamaño y material — RCP, HDPE, PVC, etc.",
                    "Capture la estructura de inicio y final de cada tramo para que QC verifique la alineación.",
                    "Anote el tipo de relleno y porcentaje de compactación para cada tramo colocado hoy.",
                    "Fotografíe cada inspección de junta antes del relleno — esa es su cadena de evidencia.",
                ],
            },
            "paving": {
                "en": [
                    "Record tonnage placed by mix design, lift number, and station limits.",
                    "Note mat temperature and density readings at the regulator and at the paver.",
                    "If you ran short and had to wait on a truck, capture the wait time in delays.",
                    "Test reports (cores, density) get attached as attachments — not buried in notes.",
                ],
                "es": [
                    "Registre el tonelaje colocado por diseño de mezcla, número de capa y estaciones límite.",
                    "Anote la temperatura de la mezcla y las lecturas de densidad en el regulador y en la pavimentadora.",
                    "Si quedó corto y tuvo que esperar un camión, capture el tiempo de espera en demoras.",
                    "Los reportes de prueba (núcleos, densidad) se adjuntan como anexos — no se entierran en notas.",
                ],
            },
            "milling": {
                "en": [
                    "Record SY milled by depth, station limits, and existing surface condition encountered.",
                    "If you hit unmarked utilities or unexpected base, photograph and flag for the surveyor.",
                    "Capture truck cycle times if hauling away — delay analysis depends on it.",
                    "Note any drum drum wear or pick changes — Shop schedules around the wear pattern.",
                ],
                "es": [
                    "Registre las yardas cuadradas fresadas por profundidad, estaciones y condición de la superficie encontrada.",
                    "Si encontró utilidades no marcadas o base inesperada, fotografíe y marque para el topógrafo.",
                    "Capture los tiempos de ciclo de camiones si está acarreando — el análisis de demoras depende de eso.",
                    "Anote el desgaste del tambor o cambios de picas — el Taller programa según el patrón.",
                ],
            },
            "mot": {
                "en": [
                    "Document every MOT setup change with a photo — the inspection sequence runs on this.",
                    "Cone count, sign list, and arrow board positions go in the production segment notes.",
                    "If FDOT or CEI flagged anything during the shift, log it as an extra-work item with their name.",
                    "Night-work setups need their own segment — separate from day setups for billing clarity.",
                ],
                "es": [
                    "Documente cada cambio de configuración MOT con una foto — la secuencia de inspección depende de esto.",
                    "Conteo de conos, lista de señales y posiciones de tablero de flechas van en las notas del segmento.",
                    "Si FDOT o CEI marcó algo durante el turno, regístrelo como trabajo extra con el nombre.",
                    "Las configuraciones nocturnas necesitan su propio segmento — separadas de las diurnas para claridad de facturación.",
                ],
            },
            "concrete": {
                "en": [
                    "Record CY placed by mix design, slump, and air content readings.",
                    "Capture truck delivery times — concrete is time-sensitive and the audit trail matters.",
                    "Note any cylinders cast for compressive strength testing — they tie to your QC log.",
                    "Cold joints, finish quality issues, or rejected loads must be photographed and described.",
                ],
                "es": [
                    "Registre las yardas cúbicas colocadas por diseño de mezcla, revenimiento y contenido de aire.",
                    "Capture los tiempos de entrega de camiones — el concreto es sensible al tiempo y la auditoría importa.",
                    "Anote cilindros tomados para prueba de resistencia — se vinculan con su bitácora QC.",
                    "Las juntas frías, problemas de acabado o cargas rechazadas deben fotografiarse y describirse.",
                ],
            },
            "structures": {
                "en": [
                    "Record each structure set with location, type, invert elevations, and rim elevation.",
                    "Photograph the bedding prep before each structure drops — that's the QC anchor.",
                    "Note grade adjustments needed and who approved them (CEI, owner, designer).",
                    "Any precast damage or warranty rejection requires photos and the manufacturer ticket.",
                ],
                "es": [
                    "Registre cada estructura colocada con ubicación, tipo, elevaciones de invertido y elevación de la tapa.",
                    "Fotografíe la preparación de la cama antes de colocar cada estructura — es el anclaje QC.",
                    "Anote los ajustes de rasante necesarios y quién los aprobó (CEI, propietario, diseñador).",
                    "Cualquier daño en prefabricado o rechazo de garantía requiere fotos y el ticket del fabricante.",
                ],
            },
            "airfield": {
                "en": [
                    "Record every escort window and the time the runway was returned to airport operations.",
                    "FOD walks should be logged with start time, end time, and items found — even zero counts matter.",
                    "Note any FAA NOTAM activations or deactivations that bracketed today's work.",
                    "If a runway incursion or radio loss occurred, that becomes a safety event — not a delay.",
                ],
                "es": [
                    "Registre cada ventana de escolta y la hora en que la pista fue devuelta a operaciones del aeropuerto.",
                    "Las inspecciones FOD deben registrarse con hora de inicio, fin y artículos encontrados — incluso cero importa.",
                    "Anote cualquier activación o desactivación de NOTAM de FAA que enmarcó el trabajo de hoy.",
                    "Si ocurrió una incursión en pista o pérdida de radio, eso es un evento de seguridad — no una demora.",
                ],
            },
            "electrical": {
                "en": [
                    "Record each circuit pulled, terminated, or tested with LF and conductor size.",
                    "Megger and continuity test results need ticket photos in the attachments section.",
                    "Note any energization events with the time, witness name, and authority approving.",
                    "Trenching for conduit shares discipline with utility crews — pull in their constraints too.",
                ],
                "es": [
                    "Registre cada circuito tirado, conectado o probado con pies lineales y calibre.",
                    "Resultados de pruebas megger y continuidad necesitan fotos de ticket en la sección de anexos.",
                    "Anote cualquier evento de energización con la hora, nombre del testigo y autoridad que aprobó.",
                    "El trincheo para conducto comparte disciplina con utilidades — incluya también esas restricciones.",
                ],
            },
            "survey": {
                "en": [
                    "Record stationing surveyed today, control points set, and any benchmark checks performed.",
                    "Note discrepancies between plan and field — those become RFIs, not silent corrections.",
                    "Photographs of monumentation, layout stakes, and any disturbed control go on this segment.",
                    "If you supported another crew today, name the crew and what they were laying out.",
                ],
                "es": [
                    "Registre las estaciones topografiadas hoy, puntos de control colocados y revisiones de banco.",
                    "Anote discrepancias entre plano y campo — esas se vuelven RFI, no correcciones silenciosas.",
                    "Fotos de monumentación, estacas de trazo y cualquier control alterado van en este segmento.",
                    "Si apoyó a otra cuadrilla hoy, nombre la cuadrilla y lo que estaban trazando.",
                ],
            },
        },
    },

    # ── Delays (Section 7) ───────────────────────────────────────────
    "delays.classify_with_type": {
        "section": "delays",
        "severity": "strong_suggest",
        "en": [
            "Every delay needs a category (weather, utility, CEI, owner, etc.) — generic 'other' triggers PM follow-up.",
            "Note hours lost as accurately as you can; a 'half day lost' is 4 hours, not 8.",
            "If the delay was caused by someone outside MASCI, capture their name and organization.",
            "Photos of the conditions causing the delay protect the project on claims and time extensions.",
        ],
        "es": [
            "Cada demora necesita una categoría (clima, servicio, CEI, propietario, etc.) — 'otro' genérico provoca seguimiento del PM.",
            "Registre las horas perdidas con la mayor precisión posible; 'medio día perdido' son 4 horas, no 8.",
            "Si la demora fue causada por alguien fuera de MASCI, capture su nombre y organización.",
            "Fotos de las condiciones que causan la demora protegen el proyecto en reclamos y extensiones de tiempo.",
        ],
    },

    # ── Extra Work (Section 8) ───────────────────────────────────────
    "extra_work.capture_directive_source": {
        "section": "extra_work",
        "severity": "strong_suggest",
        "en": [
            "Every extra-work item needs a named requestor — 'CEI told us' is not enough; capture the person's name.",
            "Quote the directive or change request word-for-word in the description.",
            "Photograph the as-found conditions before performing any extra work.",
            "Cost and schedule impact estimates protect the contractual lens later — fill them in if known.",
        ],
        "es": [
            "Cada artículo de trabajo extra necesita un solicitante con nombre — 'CEI nos dijo' no basta; capture el nombre de la persona.",
            "Cite la directriz o solicitud de cambio palabra por palabra en la descripción.",
            "Fotografíe las condiciones tal-como-encontradas antes de realizar trabajo extra.",
            "Estimaciones de impacto en costo y cronograma protegen el lente contractual — complételas si las sabe.",
        ],
    },

    # ── Constraints (Section 9) ──────────────────────────────────────
    "constraints.link_to_substrate": {
        "section": "constraints",
        "severity": "suggest",
        "en": [
            "If today's work hit a real blocker, log it as a constraint — not just as a delay.",
            "Constraint type (utility, design, access, etc.) helps the platform pattern-match to recurring issues.",
            "If this is a constraint from an earlier day, reference it instead of creating a new one.",
            "Constraints power the Operational Memory layer — recurring patterns drive project-level fixes.",
        ],
        "es": [
            "Si el trabajo hoy chocó con un bloqueador real, regístrelo como restricción — no solo como demora.",
            "El tipo de restricción (servicio, diseño, acceso, etc.) ayuda a la plataforma a detectar patrones recurrentes.",
            "Si es una restricción de un día anterior, refiérala en vez de crear una nueva.",
            "Las restricciones alimentan la Memoria Operacional — patrones recurrentes impulsan correcciones a nivel proyecto.",
        ],
    },

    # ── Safety (Section 10) ──────────────────────────────────────────
    "safety.report_every_event": {
        "section": "safety",
        "severity": "strong_suggest",
        "en": [
            "Every safety event — even near miss — gets logged with who, what, when, and the safety contact notified.",
            "Notify Safety BEFORE you submit the ODR — calling Safety is the hard stop, not the report.",
            "Take photos at the scene before anyone moves equipment or workers.",
            "Incident report attaches as a separate document; the ODR safety section is the gateway, not the file.",
        ],
        "es": [
            "Cada evento de seguridad — incluso casi-accidente — se registra con quién, qué, cuándo y el contacto de Seguridad notificado.",
            "Notifique a Seguridad ANTES de enviar el ODR — llamar a Seguridad es la parada obligatoria, no el reporte.",
            "Tome fotos en la escena antes de que alguien mueva equipo o trabajadores.",
            "El reporte de incidente se adjunta como documento separado; la sección de seguridad del ODR es la puerta, no el archivo.",
        ],
    },

    # ── Weather Impact (Section 11) ──────────────────────────────────
    "weather_impact.detail_when_impacted": {
        "section": "weather_impact",
        "severity": "suggest",
        "en": [
            "When you toggle 'weather impacted work', describe the actual impact — not just the weather.",
            "Hours lost should reflect productive work stopped, not the total time on site.",
            "If rain delayed paving but pipe kept going, only mark the paving crew's impact.",
            "Weather-impact details support extension requests and claims defense.",
        ],
        "es": [
            "Cuando active 'clima afectó el trabajo', describa el impacto real — no solo el clima.",
            "Horas perdidas deben reflejar trabajo productivo detenido, no el tiempo total en sitio.",
            "Si la lluvia demoró pavimentación pero tubería continuó, marque solo el impacto de pavimentación.",
            "Detalles del impacto climático apoyan solicitudes de extensión y defensa de reclamos.",
        ],
    },

    # ── Photos (Section 12) ──────────────────────────────────────────
    "photos.tag_and_caption": {
        "section": "photos",
        "severity": "nudge",
        "en": [
            "Tag each photo with what it shows: production, delay, safety, equipment, MOT.",
            "Voice captions are the fastest way to add context — they get transcribed automatically.",
            "Photos taken before backfill, before pour, before cover-up have the highest evidence value.",
            "Pictures without context become noise — a 5-second caption saves hours of rework later.",
        ],
        "es": [
            "Etiquete cada foto con lo que muestra: producción, demora, seguridad, equipo, MOT.",
            "Subtítulos de voz son la forma más rápida de agregar contexto — se transcriben automáticamente.",
            "Fotos tomadas antes del relleno, antes del vaciado, antes del cubrimiento tienen el mayor valor de evidencia.",
            "Fotos sin contexto se vuelven ruido — un subtítulo de 5 segundos ahorra horas de rehacer trabajo.",
        ],
    },

    # ── Tomorrow Plan (Section 13) ───────────────────────────────────
    "tomorrow.planned_work.add_summary": {
        "section": "tomorrow",
        "severity": "suggest",
        "en": [
            "Tomorrow's plan helps Dispatch and Shop pre-stage equipment and materials.",
            "Name the specific operations: 'pipe MH-12 to MH-14', not 'continue pipe'.",
            "List what you need that you don't have yet — material, equipment, manpower.",
            "Concerns capture the 'this could go wrong' instinct — share it before it becomes a real problem.",
        ],
        "es": [
            "El plan de mañana ayuda a Despacho y Taller a preparar equipo y materiales con anticipación.",
            "Nombre las operaciones específicas: 'tubería MH-12 a MH-14', no 'continuar tubería'.",
            "Liste lo que necesita y aún no tiene — material, equipo, mano de obra.",
            "Las preocupaciones capturan el instinto de 'esto podría salir mal' — compártalo antes de que sea un problema real.",
        ],
    },

    # ── Plan vs Actual (Section 14) ──────────────────────────────────
    "plan_vs_actual.explain_variance": {
        "section": "plan_vs_actual",
        "severity": "strong_suggest",
        "en": [
            "If you didn't complete yesterday's planned work, explain why with one or two specific reasons.",
            "Schedule impact in days helps the PM forecast — even an honest 'half day behind' counts.",
            "Variance isn't a confession — it's the data the platform uses to learn what causes slips.",
            "Patterns in variance reasons drive operational fixes — be precise.",
        ],
        "es": [
            "Si no completó el trabajo planeado de ayer, explique por qué con una o dos razones específicas.",
            "El impacto en cronograma en días ayuda al PM a pronosticar — incluso un honesto 'medio día atrasado' cuenta.",
            "La variación no es una confesión — es el dato que la plataforma usa para aprender qué causa retrasos.",
            "Patrones en razones de variación impulsan correcciones operativas — sea preciso.",
        ],
    },

    # ── Signature (Section governance) ───────────────────────────────
    "signature.foreman_acknowledgement.required": {
        "section": "signature",
        "severity": "strong_suggest",
        "en": [
            "Acknowledging the report means: 'this is what I observed today, to the best of my knowledge.'",
            "If you can't acknowledge — STOP. Talk to your superintendent before submitting.",
            "Your acknowledgement is the official record signature — it carries legal weight.",
            "You have 24 hours after submit to amend without authority — use it if memory clarifies.",
        ],
        "es": [
            "Reconocer el reporte significa: 'esto es lo que observé hoy, a mi mejor saber.'",
            "Si no puede reconocer — PARE. Hable con su superintendente antes de enviar.",
            "Su reconocimiento es la firma oficial del registro — tiene peso legal.",
            "Tiene 24 horas después de enviar para corregir sin autoridad — úselo si la memoria aclara.",
        ],
    },
}


def list_prompt_keys() -> List[str]:
    return sorted(CATALOG.keys())


def resolve_prompt(
    prompt_key: str,
    crew_type: Optional[str] = None,
    lang: str = "en",
) -> List[str]:
    """Return the bullets for (prompt_key, crew_type, lang).

    Crew-specific overlay takes precedence over the base entry.
    """
    entry = CATALOG.get(prompt_key)
    if not entry:
        return []
    if lang not in ("en", "es"):
        lang = "en"
    if crew_type:
        overlay = (entry.get("crew_overrides") or {}).get(crew_type) or {}
        bullets = overlay.get(lang)
        if bullets:
            return list(bullets)
    return list(entry.get(lang) or [])


def catalog_health() -> Dict[str, Any]:
    """Coverage stats for the bilingual probe."""
    total = len(CATALOG)
    en_min4 = sum(1 for v in CATALOG.values() if len(v.get("en") or []) >= 4)
    es_min4 = sum(1 for v in CATALOG.values() if len(v.get("es") or []) >= 4)
    sections = sorted({v.get("section", "") for v in CATALOG.values()})
    crews_covered = sorted({
        crew
        for v in CATALOG.values()
        for crew in (v.get("crew_overrides") or {}).keys()
    })
    return {
        "prompt_keys": total,
        "en_keys_meeting_floor": en_min4,
        "es_keys_meeting_floor": es_min4,
        "en_keys_below_floor": [k for k, v in CATALOG.items() if len(v.get("en") or []) < 4],
        "es_keys_below_floor": [k for k, v in CATALOG.items() if len(v.get("es") or []) < 4],
        "sections_covered": sections,
        "crews_with_overrides": crews_covered,
        "crews_universe": CATALOG_CREW_TYPES,
    }


__all__ = [
    "CATALOG", "CATALOG_CREW_TYPES",
    "list_prompt_keys", "resolve_prompt", "catalog_health",
]
