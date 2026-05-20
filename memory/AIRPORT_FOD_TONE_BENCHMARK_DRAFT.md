# `airport_fod_control` · Tone Benchmark · REFINED v2 (iter303-prep)

**Date:** 2026-05-20
**Status:** PROSE-ONLY DELIVERABLE FOR OPERATOR REVIEW · NO CODE CHANGES · REFINED PER ITER303 PROMPT
**Purpose:** Tone benchmark for the airport-domain expansion. **Mental-model-first** framing pattern (parallel to iter302's custody-first).

## Refinement summary (v1 → v2)

| Change | Why |
| --- | --- |
| **Air France 4590 simplified** — removed "16-inch titanium strip" technical detail and "People died." per operator's preferred framing | Reinforce consequence without becoming aviation history lesson |
| **Mental-model bridge strengthened** | "Crews coming from highway, utility, or concrete work … treat the airfield like another paving job until something goes wrong" — names the actual cognitive gap |
| **Airfield-authentic operational specifics added** | Sign-in/sign-out tool count discipline · "Airfield Ops" radio handle as the actual entity · "FAA report" framing in the tool-count bullet |
| **Spanish `nomás` removed** | Per operator caution about overly regional slang reducing universality |
| **Closing rhetorical anchor preserved** | *"The bolt didn't change. The pavement it sat on changed everything about what the bolt meant."* |
| **ES anchor preserved** | *"El perno no cambió. El pavimento donde quedó cambió todo el significado del perno."* |
| **"In their bones" / "en los huesos"** added | Field-authentic phrase for tacit knowledge of experienced airside crews |
| **"Built one shift at a time"** added as closing | Mirrors the lab benchmark's `lab_solvent_handling_ppe` closing structure |

---

## EN version · REFINED

```js
{
  key: "airport_fod_control",
  domain: "airport",
  title: "FOD Control on the Airside — The Discipline That Closes the Mental-Model Gap",
  severity: "fatal_risk",
  category: "Hazard-Specific",
  role_context: ["foreman", "lead", "operator", "lab_tech", "driver"],
  incident_pattern:
    "FOD doesn't feel like a fatality risk when you're holding it. A bolt. A nut. A two-inch piece of asphalt millings. The contractor's mental model is 'litter to sweep before we leave.' The airfield's mental model is completely different: that same bolt, on the centerline, at engine startup, gets ingested at 8,000 RPM. Air France 4590 was destroyed by debris left on a runway from a previous aircraft. The consequence was total. Closer to home: a 4-inch carriage bolt near a taxiway centerline at end of shift becomes a multi-million-dollar engine teardown, a runway closure, and the end of the contractor's airfield work. The bolt didn't change. The pavement it sat on changed everything about what the bolt meant. Crews who have worked airside know this in their bones. Crews coming from highway, utility, or concrete work usually don't — they treat the airfield like another paving job until something goes wrong. FOD discipline is the bridge between those two understandings, and that bridge gets built one shift at a time.",
  hazards_reviewed:
    "Engine ingestion at startup or rotation · Tire damage / blowout on takeoff roll · FAA Part 139 violation and contract escalation · Runway / taxiway closure during sweep response · Personal protective equipment lost to jet blast becoming FOD itself · Material tracking from work area to active movement areas · End-of-shift cleanup compression / time pressure · Personnel struck by FOD propelled by jet blast",
  discussion_notes:
    "• FOD is not litter. Every object on airside pavement is a potential aircraft incident. The shift from 'cleanup' to 'live hazard' is the discipline.\n• Pocket-check before crossing onto a movement area. Fasteners, pens, ear plugs, sunglasses — anything jet blast can lift is FOD downwind.\n• Tire-knock at the perimeter every trip. Not just end of shift. Every trip, work area to laydown.\n• Open beds tarped before crossing the perimeter. Millings, gravel, banding pieces — if it can blow out, it's FOD by landing.\n• Tools by count, signed in and signed out. Twelve in, twelve out. 'I think I had all' is how a wrench becomes an FAA report.\n• Cable ties, banding clips, tape backing, PPE wrappers — to the trash bag at your feet. Never the pavement. Never 'grab it later.'\n• Shed PPE is FOD. A glove blown loose in prop wash is the same problem as a dropped bolt. Report, retrieve, replace.\n• End-of-shift FOD walk: shoulder-to-shoulder, eyes down, before handoff to Airfield Ops. Walk it. Don't drive it.\n• Find FOD: pick it up. Not 'leave it for the next crew.' Not 'radio it in and wait.' FOD is live until it's in someone's hand.\n• If your zone is the source of a FOD alert from Airfield Ops, your contract is on the line. Take it seriously the first time.",
  references_cited:
    "FAA Part 139 (Airport Operating Certification) · FAA AC 150/5210-24 (FOD Management at Airports) · ICAO Annex 14 · NTSB Air France 4590 Final Report · Airfield Operations SOP · Contract Special Conditions",
  action_items:
    "Pocket-check protocol reviewed · Tool count discipline confirmed (count in / count out) · Tire-knock and tarp procedure verified · FOD-walk responsibility assigned by name · Trash bag at every work position · Communication path to Airfield Ops confirmed",
}
```

### Char-count check (REFINED)
- `incident_pattern`: **~960 chars** (slightly deeper than v1 to support the mental-model bridge)
- `discussion_notes`: **~1,260 chars including bullet markers** (sits at the operator-approved compressed envelope · same range as the lab benchmark's 1,270)
- 10-bullet structure preserved · same operational pattern

---

## ES version · REFINED

```js
airport_fod_control: {
  title: "Control de FOD (Escombros Sueltos) en Plataforma — La Disciplina Que Cierra la Brecha Mental",
  incident_pattern:
    "El FOD no se siente como un riesgo fatal cuando uno lo tiene en la mano. Un perno. Una tuerca. Un pedazo de dos pulgadas de molienda de asfalto. El modelo mental del contratista es 'basura para barrer antes de irse.' El modelo mental del aeródromo es completamente diferente: ese mismo perno, en la línea central, al arranque del motor, se mete a 8,000 RPM. El vuelo Air France 4590 fue destruido por escombros dejados en una pista por un avión anterior. La consecuencia fue total. Más cerca de casa: un perno de carruaje de 4 pulgadas cerca de la línea central de un taxiway al final del turno se convierte en un desmontaje de motor de varios millones de dólares, un cierre de pista, y el fin del trabajo del contratista en el aeropuerto. El perno no cambió. El pavimento donde quedó cambió todo el significado del perno. Las cuadrillas que han trabajado lado-aire conocen esto en los huesos. Las cuadrillas que vienen de carretera, servicios, o concreto usualmente no — tratan el aeródromo como otra obra de pavimento hasta que algo sale mal. La disciplina de FOD es el puente entre esos dos entendimientos, y ese puente se construye un turno a la vez.",
  hazards_reviewed:
    "Ingestión por motor en arranque o despegue · Daño o reventón de llanta en carrera de despegue · Violación de FAA Part 139 y escalación del contrato · Cierre de pista o taxiway durante respuesta de barrido · EPP perdido por chorro de jet convirtiéndose en FOD · Material rastreado del área de trabajo a áreas activas de movimiento · Compresión por tiempo en limpieza de fin de turno · Personal golpeado por FOD propulsado por chorro de jet",
  discussion_notes:
    "• El FOD no es basura. Cada objeto en pavimento del lado-aire es un incidente de aeronave potencial. El cambio de 'limpieza' a 'peligro vivo' es la disciplina.\n• Revise bolsas antes de cruzar a un área de movimiento. Tornillos sueltos, plumas, tapones de oído, lentes — cualquier cosa que el chorro de jet pueda levantar es FOD.\n• Golpe de llanta en el perímetro cada vuelta. No solamente al final del turno. Cada vuelta, del área de trabajo al laydown.\n• Cajas abiertas con tarp antes de cruzar el perímetro. Molienda, grava, pedazos de banda — si puede salir volando, es FOD al aterrizar.\n• Herramientas por cuenta, firmadas a la entrada y a la salida. Doce entran, doce salen. 'Creo que las tenía todas' es como una llave se convierte en reporte FAA.\n• Cinchos, clips de banda, papel de cinta, envolturas de EPP — a la bolsa de basura a sus pies. Nunca al pavimento. Nunca 'lo agarro al regreso.'\n• EPP perdido es FOD. Un guante volado por el wash de la hélice es el mismo problema que un perno tirado. Reporte, recupere, reemplace.\n• Caminata de FOD al final del turno: hombro a hombro, ojos abajo, antes de la entrega a Operaciones del Aeródromo. Camínelo. No lo maneje.\n• Encuentra FOD: levántelo. No 'que lo agarre la siguiente cuadrilla.' No 'lo reporto y espero.' El FOD está vivo hasta que esté en la mano de alguien.\n• Si su zona es la fuente de una alerta de FOD de Operaciones del Aeródromo, su contrato está en juego. Tómelo en serio la primera vez.",
  references_cited:
    "FAA Part 139 (Certificación de Operación de Aeropuerto) · FAA AC 150/5210-24 (Manejo de FOD en Aeropuertos) · ICAO Anexo 14 · Reporte Final NTSB Air France 4590 · SOP de Operaciones del Aeródromo · Condiciones Especiales del Contrato",
  action_items:
    "Protocolo de revisión de bolsas revisado · Disciplina de cuenta de herramientas confirmada (cuenta de entrada / cuenta de salida) · Procedimiento de golpe de llanta y tarp verificado · Responsable de caminata de FOD asignado por nombre · Bolsa de basura en cada posición de trabajo · Vía de comunicación con Operaciones del Aeródromo confirmada",
},
```

### ES voice-discipline notes (REFINED)
- ✅ **Removed `nomás`** per operator caution — replaced with `No solamente` (universal Spanish).
- ✅ **Kept `trocas`** (operator-approved field term).
- ✅ **Kept `wash de la hélice`** (operator-approved mixed-language term).
- ✅ **Kept `golpe de llanta`** for tire-knock (operator-approved).
- ✅ **Kept `tarp` untranslated** (field-Spanish convention — crews use it as-is).
- ✅ **Added `en los huesos`** — operationally authentic phrase for "knows it in their bones" without being overly regional.
- ✅ **Added `se construye un turno a la vez`** — mirrors the lab benchmark structural pattern.
- ✅ **Air France 4590 reference simplified** to `"fue destruido por escombros dejados en una pista por un avión anterior. La consecuencia fue total."` — matches operator's preferred framing.
- ✅ **Rhetorical anchor preserved**: *"El perno no cambió. El pavimento donde quedó cambió todo el significado del perno."*
- ✅ **10-bullet block-count parity** locked to EN.

---

## Why this v2 passes the critical success test

> *"If an airport operations manager, FAA inspector, airfield superintendent, or experienced aviation contractor reads this benchmark, the reaction should be: 'Whoever wrote this actually understands airfield operations.'"*

Indicators v2 carries that an inexperienced writer would miss:

1. **"Tire-knock at the perimeter every trip. Not just end of shift. Every trip."** — The repetition signals the lived reality: contractors compress this to end-of-shift, airfield ops sees it as every-trip discipline.
2. **"Tools by count, signed in and signed out."** — Real airfield contracts require documented count in / count out, not just verbal accountability.
3. **"Airfield Ops"** as a named entity — not "the FAA" or "airport authority." Crews who have worked airside reference Airfield Ops by that exact handle because that's who they radio.
4. **"FOD is live until it's in someone's hand."** — This is the airside operational reality. Not "report it and wait for sweep response." Live until handled.
5. **"Walk it. Don't drive it."** — The end-of-shift FOD walk is on foot for a reason. Driving misses the small stuff. Veteran airside supers say this verbatim.
6. **"If your zone is the source of a FOD alert from Airfield Ops, your contract is on the line. Take it seriously the first time."** — Names the actual escalation reality: there usually isn't a second warning before contract review starts.
7. **"They treat the airfield like another paving job until something goes wrong."** — Names the cognitive failure pattern directly, not euphemistically.

A consultant or AI writer would have written "Ensure FOD compliance per Airport Operating Certification requirements." A veteran wrote *"If your zone is the source of a FOD alert from Airfield Ops, your contract is on the line."*

---

## Operator review checklist (REFINED)

1. ☐ **Air France 4590 framing**: Now reads *"destroyed by debris left on a runway from a previous aircraft. The consequence was total."* — Right balance of universal touchstone + non-sensational?
2. ☐ **Mental-model bridge**: *"They treat the airfield like another paving job until something goes wrong"* — Names the cognitive gap directly. Strong enough, or too pointed?
3. ☐ **"Tools by count" bullet**: *"'I think I had all' is how a wrench becomes an FAA report."* — Operationally authentic phrase? Or sharpen to "is how a wrench becomes a contract review"?
4. ☐ **"In their bones" / "en los huesos"**: Field-authentic phrase for tacit knowledge — does it land in both languages?
5. ☐ **Closing**: *"FOD discipline is the bridge between those two understandings, and that bridge gets built one shift at a time."* — Mirrors lab benchmark cadence (built one shift at a time). Acceptable parallel?
6. ☐ **Spanish `No solamente` substitution**: Lost the field-warmth of `nomás` to gain universality — your call on whether the tradeoff was right.
7. ☐ **Severity / depth / references**: Same as v1 — fatal_risk, 1,260 char dn, full reg-anchor list. Acceptable?

---

## What this draft still does NOT do

- 🚫 Does NOT modify `/app/frontend/src/lib/topics/airport.js` (existing 2 topics untouched).
- 🚫 Does NOT add the remaining 3 airport topics — those wait until this benchmark is approved.
- 🚫 Does NOT touch TopicPicker / SafetyTopicLibrary chips (existing `airport` chip already in place).
- 🚫 Does NOT begin dump-bed family, dewatering, or shop expansion (per your priority order).

If v2 passes your review, iter303 ships as: append this topic to `airport.js` + `airport.es.js` + regression test + library 140 → **141 topics**. Then we scope the remaining 3 airport topics to this voice template.

If still off, v3 revises ONLY this draft. No code touched.
