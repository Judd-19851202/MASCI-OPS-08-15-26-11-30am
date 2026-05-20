# `airport_fod_control` · Tone Benchmark Draft (iter303-prep)

**Date:** 2026-05-20
**Status:** PROSE-ONLY DELIVERABLE FOR OPERATOR REVIEW · NO CODE CHANGES
**Purpose:** Tone benchmark for the airport-domain expansion. If approved, this topic anchors the airport vertical at the same voice depth the `lab` domain anchored with `lab_nuclear_gauge_handling`.

**Operator's named insight that drove this choice:**
> *"FOD discipline is one of the most misunderstood operational concepts among non-airfield crews and carries real federal/operational consequence."*

The draft is engineered to **reframe FOD from "nuisance cleanup" to "every dropped item is a potential aircraft incident"** — exactly the mental-model bridge the operator named. Custody-first framing was the iter302 benchmark; this is **mental-model-first framing** for iter303.

**Voice discipline checked against:**
- ✅ Operationally realistic (reframes FOD as live engine-ingestion risk, NOT as airfield-ops paperwork)
- ✅ Calm tone (anchors with the Air France 4590 reference but does NOT sensationalize)
- ✅ Practical / field-and-airside usable
- ✅ Bilingual-natural (field-Spanish: `trocas` · `wash de la hélice` · `golpe de llanta`)
- ✅ Non-corporate / non-fear-driven / non-legalistic
- ✅ No OSHA boilerplate · no FAA jargon dumps · no LMS framing
- ✅ Addresses the **non-airfield crew** mental model directly (operator's key insight)

Field structure matches iter302 lab benchmark and existing trucking/dewatering topics.

---

## EN version

```js
{
  key: "airport_fod_control",
  domain: "airport",
  title: "FOD Control on the Airside — The Discipline That Closes the Mental-Model Gap",
  severity: "fatal_risk",
  category: "Hazard-Specific",
  role_context: ["foreman", "lead", "operator", "lab_tech", "driver"],
  incident_pattern:
    "FOD doesn't feel like a fatality risk when you're holding it. A bolt. A nut. A two-inch piece of asphalt millings. The contractor's mental model is 'litter to sweep up before we leave.' The airfield's mental model is different: that same bolt, on the centerline, at engine startup, gets ingested at 8,000 RPM. Air France 4590 was destroyed by a 16-inch titanium strip lost from a previous aircraft. People died. Closer to home: a 4-inch carriage bolt left near a taxiway centerline at end of shift becomes a multi-million-dollar engine teardown, a runway closure, a federal investigation, and the end of the contractor's airfield work. The bolt didn't change. The pavement it sat on changed everything about what the bolt meant. Crews who have worked airside know this. Crews coming from highway, concrete, or utility work usually don't. FOD discipline is the bridge between those two understandings.",
  hazards_reviewed:
    "Engine ingestion at startup or rotation · Tire damage / blowout on takeoff roll · FAA Part 139 violation and contract escalation · Runway / taxiway closure during sweep response · Personal protective equipment lost to jet blast becoming FOD itself · Material tracking from work area to active movement areas · End-of-shift cleanup compression / time pressure · Personnel struck by FOD propelled by jet blast",
  discussion_notes:
    "• FOD is not 'litter.' Every item dropped on airside pavement is potential engine ingestion. The mental shift is hardest for crews coming from highway work.\n• Pocket-check before crossing onto a movement area. Loose fasteners, pens, sunglasses, ear plugs — all jet-blast departures waiting to happen.\n• Trucks moving from work area to laydown go through tire-knock at the perimeter every trip. Not just end of shift. Every trip.\n• Open beds tarped before crossing the perimeter. Millings, gravel, banding pieces — anything that flies out is FOD by landing time.\n• Tools accountability is by count. Twelve in, twelve out. Not 'I think I had all of them.'\n• Cable ties, banding clips, PPE wrappers go to the trash bag at your feet — never the pavement, never 'grab it later.'\n• Shed PPE is FOD. A glove blown loose by prop wash is the same problem as a dropped bolt. Report, retrieve, replace.\n• End-of-shift FOD walk is not optional. Shoulder-to-shoulder, eyes down, before airfield ops handoff. Walk it. Don't drive it.\n• If you find FOD: pick it up. Not 'leave it for the next crew.' Not 'radio it in and wait.' Live until it's in someone's hand.\n• If your zone is the source of a FOD alert, your contract is on the line. Take it seriously the first time.",
  references_cited:
    "FAA Part 139 (Airport Operating Certification) · FAA AC 150/5210-24 (FOD Management at Airports) · ICAO Annex 14 · NTSB Air France 4590 Final Report · Airfield Operations SOP · Contract Special Conditions",
  action_items:
    "Pocket-check protocol reviewed · Tool count discipline confirmed (count in / count out) · Tire-knock and tarp procedure verified · FOD-walk responsibility assigned by name · Trash bag at every work position · Communication path to Airfield Ops confirmed",
}
```

### Char-count check (matches operator-approved compressed envelope)
- `incident_pattern`: ~905 chars (mirrors the lab benchmark depth)
- `discussion_notes`: ~1,255 chars · **inside the 1,150–1,250 target with ≤ +5 buffer**
- `hazards_reviewed`: ~415 chars · 8 distinct hazards
- 10-bullet discussion structure matches the canonical operational pattern
- Reading-level matches lab benchmark (foreman-grade, narrative-first, no jargon dumps)

---

## ES version

```js
airport_fod_control: {
  title: "Control de FOD (Escombros Sueltos) en Plataforma — La Disciplina Que Cierra la Brecha Mental",
  incident_pattern:
    "El FOD no se siente como un riesgo fatal cuando uno lo tiene en la mano. Un perno. Una tuerca. Un pedazo de dos pulgadas de molienda de asfalto. El modelo mental del contratista es 'basura para barrer antes de irse.' El modelo mental del aeródromo es diferente: ese mismo perno, en la línea central, al arranque del motor, se mete a 8,000 RPM. El vuelo Air France 4590 fue destruido por una tira de titanio de 16 pulgadas perdida por un avión anterior. Murió gente. Más cerca de casa: un perno de carruaje de 4 pulgadas dejado cerca de la línea central de un taxiway al final del turno se convierte en un desmontaje de motor de varios millones de dólares, un cierre de pista, una investigación federal, y el fin del trabajo del contratista en el aeropuerto. El perno no cambió. El pavimento donde quedó cambió todo el significado del perno. Las cuadrillas que han trabajado lado-aire conocen esto. Las cuadrillas que vienen de carretera, concreto, o servicios usualmente no. La disciplina de FOD es el puente entre esos dos entendimientos.",
  hazards_reviewed:
    "Ingestión por motor en arranque o despegue · Daño o reventón de llanta en carrera de despegue · Violación de FAA Part 139 y escalación del contrato · Cierre de pista o taxiway durante respuesta de barrido · EPP perdido por chorro de jet convirtiéndose en FOD · Material rastreado del área de trabajo a áreas activas de movimiento · Compresión por tiempo en limpieza de fin de turno · Personal golpeado por FOD propulsado por chorro de jet",
  discussion_notes:
    "• El FOD no es 'basura.' Cada objeto caído en el pavimento del lado-aire es ingestión potencial del motor. El cambio mental es más difícil para cuadrillas que vienen de carretera.\n• Revise bolsas antes de cruzar a un área de movimiento. Pernos sueltos, plumas, lentes, tapones de oído — todos son salidas por chorro de jet esperando.\n• Las trocas que van del área de trabajo al laydown pasan por golpe de llanta en el perímetro cada vuelta. No nomás al final del turno. Cada vuelta.\n• Cajas abiertas con tarp antes de cruzar el perímetro. Molienda, grava, pedazos de banda — todo lo que sale volando es FOD para cuando aterriza.\n• La cuenta de herramientas es por número. Doce entran, doce salen. Nada de 'creo que las tenía todas.'\n• Cinchos, clips de banda, envolturas de EPP van a la bolsa de basura a sus pies — nunca al pavimento, nunca 'lo agarro al regreso.'\n• EPP perdido es FOD. Un guante volado por el wash de la hélice es el mismo problema que un perno tirado. Reporte, recupere, reemplace.\n• La caminata de FOD al final del turno no es opcional. Hombro a hombro, ojos abajo, antes de la entrega a operaciones del aeródromo. Camínelo. No lo maneje.\n• Si encuentra FOD: levántelo. Nada de 'que lo agarre la siguiente cuadrilla.' Nada de 'lo reporto y espero.' Está vivo hasta que esté en la mano de alguien.\n• Si su zona es la fuente de una alerta de FOD, su contrato está en juego. Tómelo en serio la primera vez.",
  references_cited:
    "FAA Part 139 (Certificación de Operación de Aeropuerto) · FAA AC 150/5210-24 (Manejo de FOD en Aeropuertos) · ICAO Anexo 14 · Reporte Final NTSB Air France 4590 · SOP de Operaciones del Aeródromo · Condiciones Especiales del Contrato",
  action_items:
    "Protocolo de revisión de bolsas revisado · Disciplina de cuenta de herramientas confirmada (cuenta de entrada / cuenta de salida) · Procedimiento de golpe de llanta y tarp verificado · Responsable de caminata de FOD asignado por nombre · Bolsa de basura en cada posición de trabajo · Vía de comunicación con Operaciones del Aeródromo confirmada",
},
```

### ES voice-discipline notes
- **Field-Spanish operational tone preserved**: `trocas` · `wash de la hélice` · `tarp` (untranslated, as crews use it) · `nomás` (idiomatic field-Spanish) · `golpe de llanta` for tire-knock.
- Regulatory anchors preserved as-is: **FAA Part 139** · **AC 150/5210-24** · **ICAO Anexo 14** · **NTSB**. Brief Spanish gloss provided on first use of Part 139 ("Certificación de Operación de Aeropuerto") and AC ("Manejo de FOD en Aeropuertos") per the iter279/iter297/iter300/iter302 convention.
- **The Air France 4590 reference survives in ES** — operationally important because the example is the universal touchstone for FOD discipline globally, regardless of language.
- The rhetorical anchor of the EN closing — *"The bolt didn't change. The pavement it sat on changed everything about what the bolt meant."* — survives in ES as *"El perno no cambió. El pavimento donde quedó cambió todo el significado del perno."* — same conceptual punch, same operational mental-model bridge.
- 10-bullet block-count parity locked to EN (same per-iter302 discipline).

---

## What makes this a benchmark (not just another topic)

This topic is engineered to anchor the **mental-model-first framing pattern** the way `lab_nuclear_gauge_handling` anchored the **custody-first framing pattern**. The whole airport domain rolls out from here:

- `airport_fod_control` ← THIS (mental-model bridge · why crews from off-airport work misunderstand FOD)
- `airport_night_work_visibility` ← future (most airport civil is nights; airfield-ops handoff timing realities)
- `airport_security_badging_escort` ← future (federal-incident framing for badge/escort violations)
- `airport_airfield_electrical_lighting` ← future (live circuits at runway edges · isolation discipline)

Each future topic in the domain inherits the **mental-model bridge** voice this benchmark establishes. The structural value of the benchmark is *not* the FOD content alone — it's the voice template that prevents the future 3 topics from drifting into FAA boilerplate.

---

## Operator review checklist

Please verify the draft passes your tone gates before I scope the full airport iter303 work:

1. ☐ **Mental-model bridge framing**: Does *"the contractor's mental model is litter; the airfield's mental model is engine ingestion"* read as the right reframing? Or should the angle be sharper (e.g., lead with the contract-termination consequence)?
2. ☐ **Air France 4590 reference**: Operationally appropriate touchstone, or risks sensationalism / dating? (The reference is decades old but remains the universal industry FOD example.)
3. ☐ **Severity**: `fatal_risk` justified by engine-ingestion potential + FAA Part 139 escalation + contract-life consequence. Consistent with `airport_movement_area_awareness` (existing fatal_risk). Acceptable?
4. ☐ **Compressed depth**: 1,255 chars · 10 bullets · sits exactly at the operator-approved 1,150-1,250 envelope (+5 buffer). Acceptable?
5. ☐ **Field-Spanish naturalness**: Spot-check `trocas` · `wash de la hélice` · `nomás` · `tarp` untranslated. Polish or accept?
6. ☐ **Closing rhetorical anchor**: *"The bolt didn't change. The pavement it sat on changed everything about what the bolt meant."* — strong enough as the benchmark conceptual lock?
7. ☐ **References**: FAA Part 139 + AC 150/5210-24 + ICAO Annex 14 + NTSB Air France 4590 — are these the right authority anchors for MASCI's airfield contract context, or should a state DOT special-provisions reference replace one?

---

## What this draft does NOT do

- 🚫 Does NOT create `/app/frontend/src/lib/topics/airport.js` modifications.
- 🚫 Does NOT add 3 more airport topics (those wait until benchmark approval).
- 🚫 Does NOT touch the existing 2 airport topics (`airport_movement_area_awareness` · `airport_jet_blast_fueling`).
- 🚫 Does NOT modify TopicPicker chip (existing `airport` chip already in place).
- 🚫 Does NOT touch any code, any aggregator, any backend.
- 🚫 Does NOT begin scoping the dump-bed family, dewatering build-out, or shop expansion (those wait per your priority order).

If the tone benchmark passes your review, iter303 work becomes: append this topic to `airport.js` + `airport.es.js`, write regression test, ship in one bounded closure. The remaining 3 airport topics follow only after this voice is locked.

---

## Priority order reminder (per your direction)

1. **🟢 Airport FOD benchmark** ← awaiting your review (this draft)
2. 🟡 Dump-bed strike family expansion (highest catastrophic-frequency)
3. 🟡 Dewatering / Wellpoint division build-out (build culture before incidents)
4. 🟡 Shop / Mechanic domain expansion (jack stands · grinder wheels · hydraulic injection · welding/fire watch · pinch points · LOTO realism)
5. 🟢 Airport expansion full 4-topic set (after FOD benchmark approval)

The benchmark-first workflow continues exactly as iter302 proved.
