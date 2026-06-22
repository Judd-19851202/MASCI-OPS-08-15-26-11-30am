# TRACK 15.61 — Human Usability Audit (Phase 11)

**Method:** read the live `NewDailyReport.jsx` source against the production data and assess whether a competent superintendent can produce a correct, complete Daily Report on the first attempt.

## Can a superintendent complete it correctly the first time?

**Sometimes.** The form is long (multi-section), uses several pickers (job, employee, equipment, material, supplier), and asks for ≥ 4 photos as a hard gate. A trained user CAN complete it; the corpus shows several reports scoring 6/8 from the same operators repeatedly. But the form does not coach a NEW operator into the "right answer". The evidence:

| Observation | Evidence |
|---|---|
| 18.8 % of reports leave `superintendent` blank | Phase 1 inventory |
| `prepared_by` field receives "Superintendent" 11 times (a role label, not a name) | Phase 1 inventory |
| The same operator's name appears in 2-3 different casings | Phase 1 inventory |
| 46.8 % of reports have ZERO narrative anywhere | Phase 9 |
| 2.6 % of reports record outbound material — despite active hauling | Phase 5 |

## Can a PM get meaningful production intelligence?

**Partially.** The PM Project Detail page surfaces incoming + outgoing material rows correctly for a chosen day. The PM Command Center, however, shows zeros across `loads_today`, `materials_out_today`, `active_hauls`, `equipment_assigned`, and `drivers_assigned`. A PM glancing at the Command Center cannot tell that 11 loads of dirt moved on a project the previous afternoon.

## Can an executive understand job status?

**No.** No dedicated executive endpoint exists. The exec must drill into individual PDFs or per-project drill-downs. The cross-job "what happened this week" question is not answered by the platform.

## Confusing workflows / missing prompts identified

### 1. Two narrative surfaces with no clear hierarchy

`activities[]` and `general_notes` are two parallel narrative surfaces. The form does not tell the operator which one to use, and the platform's downstream consumers prefer different ones (PDF reads both; PM dashboards read neither in roll-up). Operators in production resolve this by typing into `general_notes` (40.3 % vs. 26.0 %).

**Fix candidate:** unify into a single "What happened today?" prompt with a story-template scaffold and a structured-row mode for those who want it.

### 2. The Activities table assumes a table-shaped mental model

A foreman ending a day at 5:30 PM does not think in `{activity, % done, notes}` columns. They think "we did X, finished Y, ran into Z". The current row-add UI forces a tabular composition.

**Fix candidate:** allow paragraph-first entry; chunk into rows asynchronously via lightweight server-side parsing OR keep the table for those who like it and add a sibling paragraph field that scores equally for downstream aggregation.

### 3. Material picker has no canonical material vocabulary

Both incoming and outgoing material fields are free-text. The 60-day corpus shows literally one material word in outbound ("Dirt"). With a canonical vocabulary (Dirt · Rock · Asphalt millings · Concrete demo · Etc.) the data would be aggregable.

### 4. Hauler picker has no integration with the truck roster

The hauler field is free-text. "Masci" / "MASCI" appears in two casings — same problem as the `prepared_by` field. There is no dropdown bound to the asset master (which DOES contain Motive-linked trucks). The operator types whatever they remember.

### 5. The dead fields are still rendered

`schedule_delays_notes`, `weather_impact_notes`, and `linked_excavation_ids` are still shown to the operator even though no one fills them in. Their continued presence:
- Lengthens the form unnecessarily.
- Trains operators to skip-and-scroll, lowering the chance of filling other fields.
- Creates the impression that "this form doesn't really matter" because operators see fields that are never used.

### 6. No real-time feedback on report quality

The form does not tell the operator "your report is missing a narrative" or "you haven't said anything about hauling today even though equipment shows trucks were assigned". A simple completion-quality bar would meaningfully push the median score upward.

### 7. The PM dashboard does not return what the operator entered

The biggest UX failure is asymmetric: operators take time to enter Activity-Log content, but the PM Command Center does not show that content back to anyone. **The form is teaching: "Your work disappears."** Operators who see this stop typing.

## Conclusion

The Daily Report is functionally complete but operationally hollow. The form captures data, the PDF prints data, the project-detail page surfaces some data — but the round-trip from "operator types narrative" → "PM/exec sees narrative as part of a meaningful roll-up" is broken. The UX is not pulling the operator into the right behaviour and the dashboard is not rewarding the behaviour when it happens.

See `TRACK_15_61_RECOMMENDATIONS.md` for ranked fixes.
