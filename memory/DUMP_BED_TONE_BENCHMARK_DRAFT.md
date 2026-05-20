# `dump_bed_transition_discipline` · Tone Benchmark Draft (iter304-prep)

**Date:** 2026-05-20
**Status:** PROSE-ONLY DELIVERABLE FOR OPERATOR REVIEW · NO CODE CHANGES
**Purpose:** Tone benchmark for the dump-bed family expansion. Anchors **default-state discipline** as the philosophical framing — parallels iter302's custody-first and iter303's mental-model-first patterns.

## Why this benchmark is structurally distinct from the existing 5 dump-bed topics

The existing dump-bed topics are **scenario-driven** (overhead strike · traveling raised · PTO habits · soft-ground tipover · wind raised). Each is a distinct incident pattern.

This benchmark is **cognitive-pattern-driven** — it names the SINGLE failure mode that produces all 5 scenarios:

> **The driver's mind transitions from "dumping" to "traveling" before the truck physically transitions from raised-bed to travel-ready.**

Per operator framing: *"The dangerous moment is often AFTER dumping, not during dumping."* The benchmark names that AFTER-moment as the **seam** between two operational modes, and treats bed-down as the **travel prerequisite** that closes the seam.

This anchor topic gives the family a unifying mental model. The existing 5 topics then become **symptoms** of the one underlying transition-discipline failure — which is how veteran drivers actually frame it.

---

## EN version

```js
{
  key: "dump_bed_transition_discipline",
  domain: "trucking",
  title: "Bed Down Before Travel — The Default-State Discipline",
  severity: "fatal_risk",
  category: "Hazard-Specific",
  role_context: ["driver", "operator", "foreman", "lead"],
  incident_pattern:
    "The dangerous moment with a dump bed almost never happens during the dump. The driver is focused, the bed is up because it's supposed to be up, and the operation is going as planned. The dangerous moment is the next thirty seconds. The driver shifts mentally from 'dumping a load' to 'going to the next one' before the truck shifts physically from raised-bed to travel-ready. The bed-up alarm is buzzing — the driver tunes it out. The truck rolls forward six feet to clear the windrow, then twenty feet, then enough that a power line catches the side rail. Or the bed slumps to the right on soft ground that was solid when the truck was empty. Or the next thing the driver remembers is the cab tilting. None of those drivers were reckless. None of them said 'I'll travel with the bed up.' They said 'I thought the bed was down.' The bed didn't get hurt during dumping or during driving. It got hurt in the seam between the two — when the driver's mind had already left the dump and the truck hadn't.",
  hazards_reviewed:
    "Overhead strike from raised bed during transition · Power-line contact during short-distance moves · Bridge or structure clearance violation · Tipover on soft ground with partially-raised bed · Conveyor or plant fixed-asset strike · Wind catching raised bed during transition · Tuned-out bed-up alarm · Mirror-skip on repetitive task · Cab-tilt incident from soft-ground transition · Driver mental-mode shift before physical-mode shift",
  discussion_notes:
    "• Bed-down isn't the last step of dumping. It's the first step of traveling. The mental order is what fails — the rule is what survives.\n• Mirror-confirm BEFORE motion. The side mirror shows body angle. If the body isn't fully down, the truck doesn't move yet.\n• PTO out before motion. PTO disengage is the physical handshake that says 'travel mode is real now.'\n• The bed-up alarm exists because drivers tune it out. If you hear it after rolling, you stop. Not 'check at the next stop.'\n• 'Just moving a few feet' is the scenario every overhead-strike investigation finds. Six feet finds power lines. Twenty feet finds bridges.\n• Soft ground that held an empty truck doesn't hold a partially-raised one. The center of gravity moves up; the wheelbase doesn't.\n• Night and rain make body angle invisible from the cab. The mirror check is harder, not optional. Get out if you have to.\n• Repetitive-task complacency is real. The driver who has done this 4,000 times skips the mirror check first. Crew leads watch for it.\n• If the bed-up alarm fails, the truck doesn't move. Report it. A silent alarm is the worst possible default state.\n• Bed-down-before-travel is the rule, not a checklist item. The crews that prevent the most incidents put it on the dash in front of the driver.",
  references_cited:
    "FMCSA 49 CFR 393 (Vehicle Equipment) · DOT Pre-Trip / Post-Trip Inspection · OSHA 1926.602 (Material Handling Equipment) · Manufacturer Body-Up Alarm Specification · Company Dump-Truck SOP",
  action_items:
    "Mirror-confirm-before-motion practice reinforced · PTO disengage discipline confirmed · Bed-up alarm function verified on every dump-truck unit on site · Soft-ground awareness reviewed for current job · Repetitive-task complacency named as the actual failure pattern · 'Bed Down Before Travel' rule posted in cab",
}
```

### Char-count check
- `incident_pattern`: ~995 chars (slightly deeper than lab/airport benchmarks because the seam-framing requires the contrast structure)
- `discussion_notes`: ~1,275 chars · **10 bullets** · sits in the operator-approved compressed envelope
- `hazards_reviewed`: ~415 chars · 10 distinct hazards
- Matches the existing trucking-domain voice depth (avg dn 902 per iter301 audit)

### Voice-signal indicators (passes the "veteran wrote this" test)
1. **"The dangerous moment is the next thirty seconds"** — names the specific time window, not vague "after dumping."
2. **"PTO disengage is the physical handshake that says 'travel mode is real now.'"** — names the physical-mental linkage directly. Not "complete PTO disengagement procedure."
3. **"The bed-up alarm exists because drivers tune it out."** — names the design intent and the human failure mode in one line.
4. **"A silent alarm is the worst possible default state."** — operator-grade philosophical framing tied to the rule's reverse case.
5. **"The crews that prevent the most incidents put it on the dash in front of the driver."** — names the actual operational practice veterans use, not a corporate suggestion.
6. **"They said 'I thought the bed was down.'"** — verbatim driver quote, the canonical post-incident statement.
7. **"The driver's mind had already left the dump and the truck hadn't."** — closing rhetorical anchor naming the cognitive vs physical desynchronization.

---

## ES version

```js
dump_bed_transition_discipline: {
  title: "Caja Abajo Antes del Modo Viaje — La Disciplina del Estado por Defecto",
  incident_pattern:
    "El momento peligroso con la caja casi nunca pasa durante el volteo. El chofer está enfocado, la caja está arriba porque tiene que estar arriba, y la operación va según lo planeado. El momento peligroso son los siguientes treinta segundos. El chofer cambia mentalmente de 'volteando una carga' a 'voy a la siguiente' antes que la troca cambie físicamente de caja-arriba a listo-para-viajar. La alarma de caja arriba está sonando — el chofer la ignora. La troca rueda seis pies para limpiar el cordón, después veinte pies, después suficiente para que una línea eléctrica agarre el riel lateral. O la caja se inclina a la derecha sobre tierra blanda que estaba firme cuando la troca iba vacía. O lo siguiente que el chofer recuerda es la cabina inclinándose. Ninguno de esos choferes fue imprudente. Ninguno dijo 'voy a viajar con la caja arriba.' Dijeron 'pensé que la caja estaba abajo.' La caja no se daña durante el volteo ni durante el manejo. Se daña en la costura entre los dos — cuando la mente del chofer ya se fue del volteo y la troca no.",
  hazards_reviewed:
    "Golpe por arriba con caja levantada durante la transición · Contacto con línea eléctrica durante movimientos de poca distancia · Violación de despeje de puente o estructura · Volcadura en tierra blanda con caja parcialmente arriba · Golpe contra transportador o instalación fija de planta · Viento agarrando caja arriba durante la transición · Alarma de caja arriba ignorada · Espejo no revisado en tarea repetida · Inclinación de cabina por transición en tierra blanda · Cambio mental del chofer antes del cambio físico de la troca",
  discussion_notes:
    "• Caja abajo no es el último paso del volteo. Es el primer paso del viaje. El orden mental es lo que falla — la regla es lo que sobrevive.\n• Confirmar por espejo ANTES de moverse. El espejo lateral muestra el ángulo de la caja. Si la caja no está completamente abajo, la troca no se mueve todavía.\n• PTO desconectada antes de moverse. La desconexión del PTO es el apretón de manos físico que dice 'el modo viaje ya es real.'\n• La alarma de caja arriba existe porque los choferes la ignoran. Si la oye después de empezar a rodar, se detiene. Nada de 'lo reviso en la siguiente parada.'\n• 'Nada más moviéndome unos pies' es el escenario que toda investigación de golpe contra puente encuentra. Seis pies alcanzan para una línea eléctrica. Veinte pies alcanzan para un puente.\n• La tierra blanda que aguantó una troca vacía no aguanta una con caja parcialmente arriba. El centro de gravedad sube; la base de las ruedas no.\n• La noche y la lluvia hacen el ángulo de la caja invisible desde la cabina. La revisión por espejo es más difícil, no opcional. Bájese si tiene que.\n• La complacencia por tarea repetida es real. El chofer que ha hecho esto 4,000 veces es el primero que se salta la revisión por espejo. Los líderes de cuadrilla lo cuidan.\n• Si la alarma de caja arriba falla, la troca no se mueve. Repórtela. Una alarma silenciosa es el peor estado por defecto posible.\n• Caja-abajo-antes-de-viajar es la regla, no un punto de la lista. Las cuadrillas que previenen más incidentes lo ponen en el tablero frente al chofer.",
  references_cited:
    "FMCSA 49 CFR 393 (Equipo del Vehículo) · Inspección Pre-Viaje / Post-Viaje DOT · OSHA 1926.602 (Equipo de Manejo de Material) · Especificación del Fabricante de la Alarma de Caja Arriba · SOP de Camión de Volteo de la empresa",
  action_items:
    "Práctica de confirmar-por-espejo-antes-de-moverse reforzada · Disciplina de desconexión de PTO confirmada · Función de alarma de caja arriba verificada en cada unidad en el sitio · Conciencia de tierra blanda revisada para la obra actual · Complacencia por tarea repetida nombrada como el patrón de falla real · Regla 'Caja Abajo Antes del Viaje' puesta en la cabina",
},
```

### ES voice-discipline notes
- ✅ **`trocas`** used throughout (operator-approved field-Spanish)
- ✅ **`Bájese si tiene que`** — universal Spanish imperative, field-natural across regions
- ✅ **`Nada más`** instead of `nomás` (operator caution about regional slang honored — `Nada más` is universal Spanish equivalent of "just" in the driver-quote)
- ✅ **`tierra blanda`** instead of regional alternatives
- ✅ **`tablero`** for dashboard (universal)
- ✅ **`costura`** for "seam" — preserves the conceptual lock; same metaphor lands in Spanish
- ✅ **`apretón de manos físico`** for "physical handshake" — same conceptual punch
- ✅ **`estado por defecto`** for "default state" — preserves the operator's "default-state discipline" framing in the title

### Rhetorical anchor preserved across languages
EN: *"The bed didn't get hurt during dumping or during driving. It got hurt in the seam between the two — when the driver's mind had already left the dump and the truck hadn't."*

ES: *"La caja no se daña durante el volteo ni durante el manejo. Se daña en la costura entre los dos — cuando la mente del chofer ya se fue del volteo y la troca no."*

The **seam** metaphor lands cleanly in both languages without translation awkwardness.

---

## How this benchmark anchors the future dump-bed family

The existing 5 dump-bed topics already exist in `trucking.js`. After this benchmark lands:

| Existing topic | Becomes a symptom of the transition-discipline benchmark |
| --- | --- |
| `dump_bed_overhead_strike` | The seam failure that finds a power line / bridge / sign |
| `dump_bed_traveling_raised` | The seam failure caught in motion |
| `dump_bed_pto_habits` | The seam failure where the physical handshake is skipped |
| `dump_bed_soft_ground_tipover` | The seam failure on uneven ground |
| `dump_bed_wind_raised` | The seam failure where wind compounds the raised state |

The benchmark gives crews ONE mental model to understand WHY all 5 patterns happen, and one operational rule (*bed-down-before-travel*) that prevents all 5.

**Future expansion (NOT proposed yet)**: post-dump distraction · windrow-clearing complacency · plant-exit body-angle discipline. Each would inherit this benchmark's voice template the way airport topics will inherit iter303's mental-model-first template.

---

## Operator review checklist

1. ☐ **The seam framing**: *"The bed didn't get hurt during dumping or during driving. It got hurt in the seam between the two."* — Strong enough as the conceptual lock? Or sharpen?
2. ☐ **"The dangerous moment is the next thirty seconds"**: Right specificity for the time window, or too precise / too vague?
3. ☐ **"PTO disengage is the physical handshake"**: Field-authentic operational metaphor? Or feels overly metaphorical for a driver-audience topic?
4. ☐ **"A silent alarm is the worst possible default state"**: Captures the default-state-discipline philosophy. Strong enough as a secondary anchor?
5. ☐ **"They said 'I thought the bed was down.'"**: Verbatim driver-quote framing — operationally true to how post-incident statements actually read?
6. ☐ **"The crews that prevent the most incidents put it on the dash in front of the driver."**: Names the real operational practice. Acceptable, or does it imply too much "this should be a sticker we sell"?
7. ☐ **Compressed envelope**: 995 char ip + 1,275 char dn + 10 bullets. Matches lab/airport benchmarks. Acceptable depth?
8. ☐ **ES `Nada más` substitution for `nomás`**: Continues the iter303 universality discipline. Loses a tiny bit of warmth but gains regional reach. Right tradeoff?

---

## What this draft does NOT do

- 🚫 Does NOT modify `trucking.js` or `trucking.es.js` (existing 12 trucking topics untouched).
- 🚫 Does NOT add additional dump-bed topics (post-dump distraction · windrow complacency · etc. wait for benchmark approval).
- 🚫 Does NOT touch any other domain, any chip, any aggregator, any backend.
- 🚫 Does NOT begin dewatering or shop expansion (per operator priority order).

If the tone benchmark passes review, iter304 ships as one bounded closure: append this topic to `trucking.js` + `trucking.es.js`, regression test, library 141 → **142 topics**. Future dump-bed expansion topics then inherit this voice template.

If voice needs adjustment, ONLY this draft revises. No code touched.
