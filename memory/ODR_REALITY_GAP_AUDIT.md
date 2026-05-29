# M0.35 · ODR Reality Gap Audit

_Phase V.1 · 2026-05-29 · evidence-based · pre-M1._

This audit captures the **real friction** observed driving 4 MASCI-
style workflows through ODR. We document only what surfaced; we do
not invent work.

Each gap is rated:

- 🔴 **must-fix-before-pilot**
- 🟡 **fix-during-pilot** (acceptable to ship and learn)
- 🟢 **future improvement** (not a pilot blocker)

## Gap inventory (8 real items)

### G1 · Foreman entry: photo capture is referenced but not yet wired

**Surfaced in**: All 4 scenarios.

**Observation**: Every coaching catalog bullet says "photograph
this" / "attach the ticket". The `photos[]` array exists on the
substrate, but the M0.3 frontend does not yet expose a photo
capture / upload widget on each section.

**Severity**: 🟡 fix-during-pilot.

**Fix**: M0.4 — wire `<input type="file" accept="image/*"
capture="environment" multiple>` per section · POST to
`/api/photos` (existing photo governance substrate) · attach photo
ids to ODR PATCH. Voice captions next.

---

### G2 · Airfield: FOD walk + NOTAM timestamps have no structured slot

**Surfaced in**: Scenario 1.

**Observation**: Foremen want to record FOD walk start/end times
and NOTAM activation windows as discrete events, not buried in
notes. The substrate has no airfield-specific block.

**Severity**: 🟢 future improvement.

**Fix**: M0.4 — add an optional `airfield_block` to ODR carrying
`fod_walks: [{started_at_utc, ended_at_utc, items_found}]` and
`notam_events: [{kind, started_at_utc, ended_at_utc, notam_id}]`.
For the pilot, free-text entry is acceptable — DOT/FAA reviewers
read the description anyway.

---

### G3 · Utility: locate-variance distance has no numeric field

**Surfaced in**: Scenario 2.

**Observation**: "ATT fiber found 8 ft south of called location"
sits in description text. There's no `locate_variance_ft` numeric
field for trend analysis.

**Severity**: 🟢 future improvement.

**Fix**: M1+ — add an optional sub-block to `ConstraintEntry` for
`locate_variance: {feet, direction, utility_owner}`. Free-text in
description remains the primary capture for the pilot.

---

### G4 · Paving: density core test results are descriptive, not structured

**Surfaced in**: Scenario 3.

**Observation**: `PipeRun` has `testing: List[TestRecord]` already.
The paving sub-shape (`GenericProduction`) does not. So density
cores live in production notes.

**Severity**: 🟡 fix-during-pilot.

**Fix**: M0.4 — extend `GenericProduction` to optionally carry
`testing: List[TestRecord]` for the audiences that need it
(paving, milling, concrete). One Pydantic edit. Backwards
compatible (additive).

---

### G5 · Concrete: cylinder cast schedule has no structured slot

**Surfaced in**: Scenario 4.

**Observation**: "cylinders cast at trucks 1, 4, 7 (7-day, 28-day,
56-day)" sits in production notes. QC pulls these manually.

**Severity**: 🟡 fix-during-pilot.

**Fix**: M0.4 — extend the concrete sub-shape with
`cylinder_sets: [{set_id, truck_no, age_days, lab_destination}]`.
Backwards compatible.

---

### G6 · Foreman + Superintendent PDFs render the same envelope today

**Surfaced in**: All 4 scenarios — `X-ODR-SHA256` is identical
between `audience=foreman` and `audience=superintendent`.

**Observation**: The `_project_for_audience` function gives both
audiences the same field set. The doctrine says "Super tier sees
amendment trail + safety events + photo count" — those ARE
included, but the same fields go to foreman too. So the SHA matches.

**Severity**: 🟢 future improvement.

**Fix**: M0.4 — differentiate the layout (Super gets the amendment
chain at end; Foreman gets the readiness summary at top). The
**data** projection is correct; only the rendered layout needs to
diverge. Not a redaction concern.

---

### G7 · External PDF lacks attached photo thumbnails

**Surfaced in**: All 4 scenarios.

**Observation**: External audience receives bullet-list facts. No
embedded photo evidence. The current renderer does not pull
images.

**Severity**: 🔴 must-fix-before-pilot (for DOT/FAA acceptance).

**Fix**: M0.4 — extend `pdf.py` to embed up to N photo thumbnails
(External strips voice captions, keeps text caption + tag). Asset
pipeline already exists in `routes/photo_governance.py`.

---

### G8 · Bilingual original text not surfaced in PDFs

**Surfaced in**: Scenarios entered by Spanish-speaking foremen
would store `LocalizedString.original` + `original_lang="es"`. The
current PDF projection only reads `.text` (canonical EN).

**Severity**: 🟡 fix-during-pilot (English-only foremen submitted
all 4 scenarios; this surfaces the moment the first ES foreman
runs through).

**Fix**: M0.4 — when `original_lang` is set on a `LocalizedString`,
render `<canonical EN> · (original ES: <original>)` in the PDF.
Catalog already supports it; renderer needs the wiring.

---

## Friction NOT captured (intentional)

We did NOT log gaps that:

- The directive explicitly says to defer (RFI, Schedule, P6).
- Are hypothetical ("a foreman might want…") rather than observed
  in the 4 scenarios.
- Are platform-level design choices the operator already locked
  in M0.3 (tone, redaction, trust banner copy).

## Gap density by category

| Category | Count |
|---|---|
| Frontend wiring (photos) | 1 (G1) |
| Discipline-specific structured fields | 4 (G2, G3, G4, G5) |
| PDF / public-record polish | 2 (G6, G7) |
| Bilingual surfacing | 1 (G8) |
| **Pilot blockers** | **1** (G7 only) |

## Verdict

🟢 **8 real gaps · 1 pilot blocker · 0 architecture rework needed.**

G7 (photo embedding in External PDFs) is the only must-fix item
before pilot. Everything else is pilot-tolerable and can be fixed
during M1.

_End of ODR_REALITY_GAP_AUDIT.md._
