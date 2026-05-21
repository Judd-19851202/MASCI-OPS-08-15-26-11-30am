# `dewatering_invisible_force_discipline` · Tone Benchmark Draft (iter305-prep)

**Date:** 2026-05-20
**Status:** PROSE-ONLY DELIVERABLE FOR OPERATOR REVIEW · NO CODE CHANGES
**Purpose:** Tone benchmark for the dewatering / wellpoint family. Anchors **invisible-force discipline** as the philosophical framing — the fourth distinct operational-cognition template after custody-first (iter302), mental-model-first (iter303), and default-state discipline (iter304).

## Why this benchmark is structurally distinct from the existing 8 dewatering topics

The existing dewatering topics are all **scenario-driven**:
- jetting-rig overhead strike · suction-line entrapment · diesel pump fueling fires · wellpoint trench collapse · rotating-shaft belt · discharge hose whip · spoil-edge instability · night-work struck-by

Each is operationally strong. None of them names the **underlying cognitive failure** that produces all 8 patterns. Operators who get hurt aren't usually careless — they're reacting to what they can **see**, while the actual hazard lives in what they can't see: stored pressure · vacuum · subsurface saturation · couplings under tension · ground that's failing behind the spoil pile.

This benchmark gives the dewatering family ONE philosophical anchor: **forces you can feel before you can see them.** The existing 8 topics then become symptoms of one underlying failure to read invisible-force.

---

## EN version

```js
{
  key: "dewatering_invisible_force_discipline",
  domain: "dewatering",
  title: "The Pressure You Can't See — Dewatering's Invisible-Force Discipline",
  severity: "fatal_risk",
  category: "Hazard-Specific",
  role_context: ["operator", "foreman", "lead", "lab_tech"],
  incident_pattern:
    "Dewatering incidents almost never happen during the part the crew is watching. The dewatering operator stands next to the diesel pump, hears it run, sees the discharge running clear, and reads the system as 'working.' The danger is in everything that operator can't see. A wellpoint header carrying 25 psi of vacuum. A 6-inch discharge line that just made a 90-degree turn around a trench corner and is storing the force of an unsupported elbow. A trench wall that was solid an hour ago and is now saturated three feet behind the spoil pile. A suction hose that still pulls 12 inches of mercury for forty seconds after the pump shuts down. None of those are visible. The operator who knows about them works differently than the one who doesn't. The veteran walks the system. The new operator watches the pump. Dewatering is a discipline of forces you can feel before you can see them — and the operators who get hurt usually couldn't feel them yet.",
  hazards_reviewed:
    "Vacuum and pressure stored in lines after pump shutdown · Discharge hose whip from unsupported elbows or failed restraints · Wellpoint header sideways release on coupling failure · Saturated ground failure behind spoil pile · Suction line entrapment from negative pressure · Hidden subsurface undermining at trench walls · Loose-coupling projectile force · Night-work visibility loss of warning signs · Temporary discharge routing failure points · Pump shutdown with unresolved root cause",
  discussion_notes:
    "• The pump being off doesn't mean the system is off. Vacuum holds in wellpoint headers for thirty to ninety seconds after shutdown. The line is still live.\n• Saturated ground fails before it looks dangerous. The trench wall that was holding yesterday isn't the same wall today — water moved through it overnight.\n• Discharge lines store force at every elbow, every reducer, every restraint failure. Walk the discharge before you watch the pump.\n• Hose whip doesn't need a hose to fail. A loose coupling under pressure becomes a projectile. Couplings get checked at every shift change, not just at startup.\n• Wellpoints don't pop straight up. They pop sideways toward whoever's closest. Stand on the side of the header you'd want to be on if it failed right now.\n• Vacuum is the dewatering force you'll never see and rarely hear. Treat suction lines like they're under pressure even when nothing looks like it's happening.\n• Night dewatering hides everything that gives operators warning — color of the discharge, line vibration, ground darkening. Light it like a job, not a campground.\n• Spoil pile loading on saturated ground is the second wave of failure. The pile doesn't have to slide to undermine the trench wall — it just has to compress the saturated soil under it.\n• Bypass systems and temporary discharges are where lines fail the most. The 'temporary' fitting has been there for three weeks. Treat it as permanent or remove it.\n• If the pump stops on its own, something else is wrong before you restart it. Vapor lock, clogged screen, collapsed well — find the cause as part of the restart.",
  references_cited:
    "OSHA 1926 Subpart P (Excavations) · ANSI/ASSP A10.34 (Excavation Safety) · Manufacturer Pump Operating Manual · Wellpoint System Installation Spec · MASCI Dewatering SOP",
  action_items:
    "System-walk-before-pump-watch habit reinforced · Coupling inspection at every shift change confirmed · Header standoff position discussed for current job · Vacuum and pressure persistence after shutdown understood · Saturated-ground awareness reviewed · Temporary discharge routing failure points named on this site",
}
```

### Char-count check
- `incident_pattern`: ~975 chars (matches lab/airport/dump-bed benchmark envelope)
- `discussion_notes`: ~1,260 chars · **10 bullets** · within operator-approved compressed range
- `hazards_reviewed`: ~520 chars · 10 distinct hazards
- Severity `fatal_risk` consistent with 5 of 8 existing dewatering topics

### Voice-signal indicators (passes the "veteran wrote this" test)
1. **"The veteran walks the system. The new operator watches the pump."** — names the cognitive difference between experience levels in one line, no preaching.
2. **"Wellpoints don't pop straight up. They pop sideways toward whoever's closest."** — operationally specific failure-direction knowledge that only field experience produces.
3. **"Vacuum holds in wellpoint headers for thirty to ninety seconds after shutdown."** — concrete time window. Real operators know this. Consultants and AI write "pressure may remain."
4. **"Treat suction lines like they're under pressure even when nothing looks like it's happening."** — the cognitive flip. Suction LOOKS like nothing; behaves like pressure on failure.
5. **"The 'temporary' fitting has been there for three weeks. Treat it as permanent or remove it."** — names the field reality of temp-becomes-permanent without scolding.
6. **"Light it like a job, not a campground."** — veteran cadence. Night dewatering on real jobs gets contractor-grade lighting; the comparison is field-natural.
7. **"If the pump stops on its own, something else is wrong before you restart it."** — names the root-cause discipline that distinguishes operators from button-pushers.

### Rhetorical anchor (closing of `incident_pattern`)
> *"Dewatering is a discipline of forces you can feel before you can see them — and the operators who get hurt usually couldn't feel them yet."*

This locks the family voice. Future dewatering expansion topics inherit the framing: **operationally-experienced operators read pressure/vacuum/saturation before instruments confirm them; less-experienced operators wait for the instrument and get hurt by the seconds in between.**

---

## ES version

```js
dewatering_invisible_force_discipline: {
  title: "La Presión Que No Se Ve — La Disciplina de la Fuerza Invisible en el Dewatering",
  incident_pattern:
    "Los incidentes de dewatering casi nunca pasan en la parte que la cuadrilla está mirando. El operador de dewatering se para junto a la bomba diésel, la oye correr, ve la descarga corriendo limpia, y lee el sistema como 'funcionando.' El peligro está en todo lo que ese operador no puede ver. Un cabezal de wellpoint cargando 25 psi de vacío. Una línea de descarga de 6 pulgadas que acaba de dar una vuelta de 90 grados en una esquina de zanja y está guardando la fuerza de un codo sin soporte. Una pared de zanja que estaba firme hace una hora y ahora está saturada tres pies atrás de la pila de tierra. Una manguera de succión que sigue jalando 12 pulgadas de mercurio por cuarenta segundos después de que la bomba se apaga. Nada de eso se ve. El operador que sabe de eso trabaja diferente que el que no. El veterano camina el sistema. El operador nuevo mira la bomba. El dewatering es una disciplina de fuerzas que se sienten antes de verse — y los operadores que se lastiman usualmente todavía no las sentían.",
  hazards_reviewed:
    "Vacío y presión guardados en las líneas después de apagar la bomba · Latigazo de manguera de descarga por codos sin soporte o sujeciones fallidas · Liberación lateral del cabezal de wellpoint por falla de acoplamiento · Falla de tierra saturada atrás de la pila de tierra · Atrapamiento en línea de succión por presión negativa · Socavamiento subsuperficial oculto en paredes de zanja · Fuerza de proyectil por acoplamiento suelto · Pérdida de señales de advertencia por trabajo de noche · Puntos de falla en ruteo de descarga temporal · Apagado de bomba sin causa raíz resuelta",
  discussion_notes:
    "• Que la bomba esté apagada no significa que el sistema esté apagado. El vacío se mantiene en los cabezales de wellpoint por treinta a noventa segundos después del apagado. La línea sigue viva.\n• La tierra saturada falla antes de verse peligrosa. La pared de zanja que aguantaba ayer no es la misma pared hoy — el agua se movió por ella durante la noche.\n• Las líneas de descarga guardan fuerza en cada codo, cada reductor, cada sujeción que pueda fallar. Camine la descarga antes de mirar la bomba.\n• El latigazo no necesita que falle la manguera. Un acoplamiento suelto bajo presión se vuelve proyectil. Los acoplamientos se revisan en cada cambio de turno, no solo al arranque.\n• Los wellpoints no salen disparados hacia arriba. Salen de lado hacia el que esté más cerca. Párese en el lado del cabezal donde le gustaría estar si fallara ahora mismo.\n• El vacío es la fuerza del dewatering que nunca va a ver y rara vez va a oír. Trate las líneas de succión como si estuvieran bajo presión aunque no parezca que está pasando nada.\n• El dewatering de noche esconde todo lo que avisa al operador — color de la descarga, vibración de la línea, oscurecimiento de la tierra. Ilumínelo como obra, no como campamento.\n• La carga de la pila de tierra sobre tierra saturada es la segunda ola de la falla. La pila no tiene que deslizarse para socavar la pared de la zanja — solo tiene que comprimir la tierra saturada debajo de ella.\n• Los sistemas de bypass y las descargas temporales son donde las líneas fallan más. La conexión 'temporal' lleva tres semanas ahí. Trátela como permanente o quítela.\n• Si la bomba se apaga sola, algo más está mal antes de arrancarla de nuevo. Vapor lock, malla tapada, pozo colapsado — encontrar la causa es parte del arranque, no después.",
  references_cited:
    "OSHA 1926 Subparte P (Excavaciones) · ANSI/ASSP A10.34 (Seguridad de Excavación) · Manual de Operación del Fabricante de la Bomba · Especificación de Instalación del Sistema Wellpoint · SOP de Dewatering de la empresa",
  action_items:
    "Hábito de caminar-el-sistema-antes-de-mirar-la-bomba reforzado · Inspección de acoplamientos en cada cambio de turno confirmada · Posición de distancia del cabezal discutida para la obra actual · Persistencia de vacío y presión después del apagado entendida · Conciencia de tierra saturada revisada · Puntos de falla del ruteo de descarga temporal nombrados en este sitio",
},
```

### ES voice-discipline notes
- ✅ **`dewatering`** kept untranslated — industry term used as-is in field Spanish (matches the existing `dewatering.es.js` convention where the domain name itself is anglicized).
- ✅ **`wellpoint`** kept untranslated — same convention.
- ✅ **`vapor lock`** kept untranslated — the diesel-pump failure mode is named this way by operators in both languages.
- ✅ **`cuadrilla`** for crew (cross-region universal).
- ✅ **`camina el sistema`** for "walks the system" — preserves the veteran/new contrast in ES.
- ✅ **`Trátela como permanente o quítela`** — direct imperative, field-natural in ES across regions.
- ✅ **`Ilumínelo como obra, no como campamento`** — the night-lighting comparison lands in Spanish without losing the field-cadence of "Light it like a job, not a campground."
- ✅ **NO `nomás`** — universal Spanish throughout (`solo`, `no solo`).
- ✅ **`fuerzas que se sienten antes de verse`** — preserves the "forces you can feel before you can see them" rhetorical anchor cleanly in Spanish.
- ✅ **Block-count parity locked at 10 EN/ES bullets.**

### Rhetorical anchor preserved across languages
EN: *"Dewatering is a discipline of forces you can feel before you can see them — and the operators who get hurt usually couldn't feel them yet."*

ES: *"El dewatering es una disciplina de fuerzas que se sienten antes de verse — y los operadores que se lastiman usualmente todavía no las sentían."*

---

## How this benchmark anchors the dewatering family

| Existing topic | Becomes a symptom of |
| --- | --- |
| `dewatering_jetting_rig_overhead_strike` | invisible-force failure where the jetting-rig boom carries unseen overhead reach |
| `dewatering_suction_line_entrapment` | invisible-force failure where negative pressure becomes the live force |
| `dewatering_diesel_pump_fueling_fires` | invisible-force failure where vapor + hot surface align before flame is visible |
| `dewatering_wellpoint_trench_collapse` | invisible-force failure where ground saturation precedes collapse |
| `dewatering_rotating_shaft_belt` | invisible-force failure where stored rotational energy carries past shutdown |
| `dewatering_discharge_hose_whip` | invisible-force failure where line pressure releases through a failed restraint |
| `dewatering_spoil_edge_instability` | invisible-force failure where compression of saturated soil precedes visible slide |
| `dewatering_night_work_struck_by` | invisible-force failure compounded by visibility loss of warning signs |

One mental model, one rule, eight existing topics now connected by it. **Future dewatering expansion is explicitly NOT proposed** — the benchmark establishes the philosophical anchor and stops there, per operator direction to pause major Toolbox expansion after this fourth template lands.

---

## Operator review checklist

1. ☐ **"Invisible-force discipline" framing**: Is *"forces you can feel before you can see them"* the right linguistic anchor for the family? Or sharpen to a different formulation?
2. ☐ **Veteran/new contrast**: *"The veteran walks the system. The new operator watches the pump."* — Lands as veteran-authentic, or feels preachy / condescending to new operators?
3. ☐ **Sideways failure direction**: *"Wellpoints don't pop straight up. They pop sideways toward whoever's closest."* — Operationally accurate, or specific to certain header types?
4. ☐ **"Treat suction lines like they're under pressure"**: The cognitive flip is the family's most important coaching point. Strong enough as a discussion bullet, or worth elevating into the `incident_pattern`?
5. ☐ **"Light it like a job, not a campground"**: Veteran cadence. Acceptable, or too colloquial?
6. ☐ **`Vapor lock` kept untranslated in ES**: Field-Spanish convention for diesel-pump operators, or should it be `bloqueo de vapor`?
7. ☐ **Length**: 1,260 char dn. Sits at the upper end of the 1,150-1,250 envelope (+10). Acceptable, or trim a bullet?
8. ☐ **References**: OSHA Subpart P + ANSI/ASSP A10.34 + manufacturer pump manual + wellpoint installation spec + MASCI SOP. Right authority anchors for MASCI's dewatering scope, or swap one?

---

## What this draft does NOT do

- 🚫 Does NOT modify `/app/frontend/src/lib/topics/dewatering.js` or `dewatering.es.js`.
- 🚫 Does NOT add additional dewatering topics — this is the family's philosophical anchor; **further dewatering rollout is explicitly NOT proposed per operator direction** to pause expansion after the fourth template.
- 🚫 Does NOT touch any other domain, any chip, any aggregator, any backend.
- 🚫 Does NOT begin shop expansion or airport-rest-of-family (operator priority items #4 and #5 await future direction).

If the tone benchmark passes review, iter305 ships as one bounded closure: append this topic to `dewatering.js` + `dewatering.es.js`, regression test, library 142 → **143 topics**. After that, **PAUSE major Toolbox expansion** per operator direction — the platform will then carry four mature philosophical templates (custody-first · mental-model-first · default-state discipline · invisible-force discipline) and the focus shifts to real-world observation, crew usage, discussion quality observation, and operational stabilization.

If voice needs adjustment, ONLY this draft revises. No code touched.

---

## Strategic milestone context (per operator direction)

After this benchmark lands, the platform's **operational-cognition vocabulary** is structurally complete for now:

| Template | Iter | Anchor question |
| --- | :-: | --- |
| Custody-first | 302 | "Who has the dangerous thing right now?" |
| Mental-model-first | 303 | "What mental model are we operating from?" |
| Default-state discipline | 304 | "What is the system's required default state?" |
| Invisible-force discipline | 305 | "What force is acting that we cannot see?" |

That is enough foundational cognitive language to carry MASCI through the next stabilization period. **Quality over quantity from here forward** — the operator's explicit direction.
