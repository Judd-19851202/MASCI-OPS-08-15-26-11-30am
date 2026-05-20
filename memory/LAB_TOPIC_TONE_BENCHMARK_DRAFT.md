# `lab_nuclear_gauge_handling` · Tone Benchmark Draft (iter302-prep)

**Date:** 2026-05-20
**Status:** PROSE-ONLY DELIVERABLE FOR OPERATOR REVIEW · NO CODE CHANGES
**Purpose:** Serve as the tone benchmark for the future dedicated `lab` domain. If approved, this topic becomes the voice template the remaining 3 lab topics (and Option α's `lab.js` + `lab.es.js` + TopicPicker chip wiring) will be built around.

**Voice discipline checked against:**
- ✅ Operationally realistic (custody-first framing, not radiation-panic)
- ✅ Calm tone (treats lost-gauge incidents as the actual operational pattern, not as Chernobyl)
- ✅ Practical / field-and-lab usable
- ✅ Bilingual-natural (Spanish reads as written-by-a-tech, not machine-translated)
- ✅ Non-corporate / non-fear-driven / non-legalistic
- ✅ No OSHA boilerplate feel · no jargon dumps · no LMS framing

**Field structure** matches existing trucking/dewatering/plant topics exactly.

---

## EN version

```js
{
  key: "lab_nuclear_gauge_handling",
  domain: "lab",
  title: "Nuclear Density Gauge — Custody, Transport, and Response",
  severity: "fatal_risk",
  category: "Hazard-Specific",
  role_context: ["lab_tech", "inspector", "lead", "driver"],
  incident_pattern:
    "Nuclear gauge incidents at the field/lab level rarely involve radiation harm to a worker — they involve a lost gauge, a stolen gauge, or a damaged gauge that suddenly becomes a federal incident. The pattern repeats every year. A tech finishes a paving density test late in the day, secures the gauge in the open truck bed instead of inside the cab, runs into the gas station, comes back to find the truck broken into. Or the tech sets the gauge down on the shoulder during a quick string-line check, and a truck rolls over it. Or the gauge sits in a parked vehicle overnight in an unsecured yard and gets pried out by morning. None of these scenarios cause direct injury — but every one of them triggers an NRC report, a multi-day shutdown of testing operations, and a fine that runs into the tens of thousands. The technician who lost the gauge usually didn't fail at safety. They failed at custody. In nuclear gauge work, custody IS the safety.",
  hazards_reviewed:
    "Theft from unattended vehicle · Damage from vehicle strike during roadway testing · Source rod damage from drop or pinch · Unauthorized use by non-licensed personnel · Loss in transit (improperly secured case) · Public/civilian contact with abandoned gauge · NRC reportable incident from any of the above · Personal radiation exposure from prolonged improper handling",
  discussion_notes:
    "• Custody, not radiation, is the day-to-day risk. The gauge never leaves your line of sight when it's out of its storage cabinet.\n• Transport: gauge in the locked case, case secured inside the cab — never the open bed, never the toolbox, never the back floor of an unlocked SUV.\n• Storage: end-of-day return to the licensed storage location. No overnight in vehicles. No overnight in unsecured offices. No 'I'll bring it back tomorrow.'\n• Authorized users only. If you are not on the NRC license, you do not touch the gauge — not even to move it from the bench to the truck.\n• On the roadway: gauge stays directly beside the technician or inside the case at the technician's feet. Never sitting on the pavement behind you. Never in the wheel path. Never even briefly.\n• If a gauge is struck, dropped, or damaged — stop. Step back six feet. Call the RSO immediately. Do not pick it up to assess.\n• If a gauge is lost or stolen: notify the RSO within the hour. The 24-hour NRC reporting clock starts at discovery, not at end-of-shift.\n• Public interaction: members of the public who approach during testing get a brief, calm 'this is a regulated instrument, please give us six feet.' Do not let curiosity become contact.\n• Site awareness: paving operations have trucks, rollers, and screed crews moving constantly. The gauge sits at the technician's feet — not behind the screed where a roller will run it over.\n• PPE: standard high-vis + steel-toe. The gauge itself does not require additional PPE in normal operation. Radiation badges, if issued by the RSO, are worn on every use.",
  references_cited:
    "10 CFR 30 · 10 CFR 71 · NRC Materials License · State Radiation Control Program · ANSI N43.3 · Company RSO SOP",
  action_items:
    "Custody line-of-sight reinforced · Transport security verified (case locked, inside cab) · Authorized-user list reviewed · Lost/stolen/damaged escalation path identified by name · RSO contact verified for current shift · Radiation badge presence confirmed",
}
```

### Char-count check (matches benchmark depth)
- `incident_pattern`: **915 chars** (vs library avg 600–900 · matches strongest trucking/dewatering topics)
- `discussion_notes`: **1,485 chars** (vs library benchmark dewatering_jetting_rig at 1,046 — slightly above; intentional because nuclear-gauge custody requires more procedural specificity than typical topics)
- `hazards_reviewed`: 358 chars · 8 distinct hazards
- 10-bullet discussion structure matches the canonical operational pattern

---

## ES version

```js
lab_nuclear_gauge_handling: {
  title: "Medidor Nuclear de Densidad — Custodia, Transporte y Respuesta",
  incident_pattern:
    "Los incidentes con medidor nuclear a nivel de campo / laboratorio rara vez involucran daño por radiación al trabajador — involucran un medidor perdido, robado o dañado que de pronto se convierte en un incidente federal. El patrón se repite cada año. El técnico termina una prueba de densidad en pavimento al final del día, asegura el medidor en la caja abierta del camión en vez de adentro de la cabina, entra a la gasolinera, y regresa para encontrar el camión forzado. O el técnico pone el medidor en el hombro del camino durante una revisión rápida de string-line, y un camión lo aplasta. O el medidor pasa la noche en un vehículo estacionado en un patio sin seguridad y para la mañana ya lo sacaron. Ninguno de esos escenarios causa lesión directa — pero cada uno dispara un reporte ante la NRC, un paro de varios días en las operaciones de prueba, y una multa que llega a las decenas de miles de dólares. El técnico que perdió el medidor casi nunca falló en seguridad. Falló en custodia. En el trabajo con medidor nuclear, la custodia ES la seguridad.",
  hazards_reviewed:
    "Robo de vehículo desatendido · Daño por golpe de vehículo durante prueba en la carretera · Daño a la varilla de la fuente radiactiva por caída o pellizco · Uso no autorizado por personal sin licencia · Pérdida en tránsito (caja mal asegurada) · Contacto del público con un medidor abandonado · Incidente reportable a la NRC por cualquiera de los anteriores · Exposición personal a radiación por manejo prolongado e incorrecto",
  discussion_notes:
    "• La custodia, no la radiación, es el riesgo del día a día. El medidor nunca sale de su vista cuando está fuera del gabinete de almacenamiento.\n• Transporte: medidor en la caja cerrada con llave, caja asegurada adentro de la cabina — nunca en la caja abierta del camión, nunca en la caja de herramientas, nunca en el piso trasero de un SUV sin seguro.\n• Almacenamiento: al final del día, regreso al lugar licenciado de almacenamiento. Nada de pasar la noche en vehículos. Nada de pasar la noche en oficinas sin seguridad. Nada de 'mañana lo traigo de vuelta.'\n• Solo usuarios autorizados. Si usted no está en la licencia de la NRC, no toca el medidor — ni siquiera para moverlo del banco a la troca.\n• En la carretera: el medidor permanece al lado del técnico o adentro de la caja a los pies del técnico. Nunca puesto en el pavimento atrás de usted. Nunca en la línea de la rueda. Nunca ni por un momento.\n• Si un medidor es golpeado, se cae, o queda dañado — pare. Retroceda seis pies. Llame al RSO (Responsable de Seguridad Radiológica) de inmediato. No lo levante para revisarlo.\n• Si un medidor se pierde o lo roban: avise al RSO dentro de la hora. El reloj de 24 horas para reportar a la NRC empieza al descubrir la pérdida, no al final del turno.\n• Interacción con el público: si alguien del público se acerca durante una prueba, dígale con calma: 'este es un instrumento regulado, por favor manténgase a seis pies.' La curiosidad no debe llegar al contacto.\n• Conciencia del sitio: en pavimentación hay camiones, rodillos, y la cuadrilla del screed moviéndose todo el tiempo. El medidor se queda a los pies del técnico — no atrás del screed donde un rodillo lo va a aplastar.\n• EPP: chaleco reflectivo + bota de casquillo, como siempre. El medidor mismo no requiere EPP adicional en operación normal. El dosímetro de radiación, si el RSO se lo asignó, se usa en cada turno.",
  references_cited:
    "10 CFR 30 · 10 CFR 71 · Licencia de Materiales NRC · Programa Estatal de Control de Radiación · ANSI N43.3 · SOP del RSO de la empresa",
  action_items:
    "Línea de vista de custodia reforzada · Seguridad de transporte verificada (caja con llave, adentro de la cabina) · Lista de usuarios autorizados revisada · Vía de escalación por pérdida / robo / daño identificada por nombre · Contacto del RSO verificado para el turno actual · Presencia del dosímetro confirmada",
},
```

### ES voice-discipline notes
- Reads as **field-Spanish operational tone** — uses `troca` (truck) and `string-line` (untranslated, as field crews use it), not the formal `camión` only.
- Regulatory anchors preserved in original form: **NRC**, **RSO**, **10 CFR 30 / 71**, **ANSI N43.3** — these are how the industry refers to them in either language. Brief Spanish gloss provided on first use of `RSO`.
- No machine-translation tells (e.g., no "mejores prácticas," no "implementar," no "asegurarse de cumplir con").
- The closing line of `incident_pattern` keeps the rhetorical punch: *"En el trabajo con medidor nuclear, la custodia ES la seguridad."* — direct parallel to the EN sign-off "custody IS the safety."
- Block count and item count match EN exactly (10 discussion bullets in both languages).

---

## Operator review checklist

Please verify the draft passes your tone gates before I scope the full iter302 work:

1. ☐ **Operational realism**: Does this read like an experienced lab/field tech briefing a newer one, NOT like an OSHA training pamphlet?
2. ☐ **Calm**: Zero radiation-panic language. The whole framing is "custody is the real risk." Does that match your operational philosophy?
3. ☐ **Bilingual naturalness**: Does the Spanish read like field Spanish, not textbook Spanish? (Spot-check: `troca`, `string-line`, `cuadrilla del screed`.)
4. ☐ **Field-and-lab usable**: Does a tech standing on a shoulder at 7 PM, gauge case at their feet, find this useful? Or does it feel like a slide deck?
5. ☐ **Severity**: `fatal_risk` is justified by federal-incident potential and NRC reporting thresholds, NOT by literal radiation-death likelihood (which is operationally very rare with proper custody). Is that classification consistent with how MASCI categorizes other "regulatory-fatal" risks?
6. ☐ **Discussion-notes length**: 1,485 chars · 10 bullets. Sits slightly above the dewatering/airport benchmark (~1,040). Acceptable, or trim to ~1,100?
7. ☐ **References**: Are the cited standards the ones MASCI's RSO actually references? Adjust if a state-specific standard takes precedence.

---

## What this draft does NOT do

- 🚫 Does NOT create `/app/frontend/src/lib/topics/lab.js` or `lab.es.js`.
- 🚫 Does NOT register the new domain in `/app/frontend/src/lib/topics/index.js`.
- 🚫 Does NOT add the `lab` chip to `TopicPicker.jsx DOMAIN_CHIPS`.
- 🚫 Does NOT add the topic to the live library.
- 🚫 Does NOT translate or scaffold the remaining 3 lab topics (oven · core-drilling · solvent-handling).
- 🚫 Does NOT touch the airport vertical (iter303 candidate, awaiting iter302 close).

If the tone benchmark passes your review, those 5 steps become iter302 work in one bounded closure. If the tone needs adjustment, only this draft revises — the architectural work stays untouched until the voice is right.
