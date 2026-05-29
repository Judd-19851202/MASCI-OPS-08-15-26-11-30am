# ODR UI WIREFRAMES

_Phase V.1 · Operational Daily Record · Architecture Artifact 2 of 5 · 2026-05-29_

Text wireframes describing the foreman-facing entry experience.
**Doctrine: foremen never stare at blank forms.** Every section
opens pre-populated; the foreman's job is to **verify · adjust ·
add evidence**, not to type from zero.

Mobile-first (iPhone-portrait baseline). iPad and desktop are
progressive enhancements — same content, more breathing room.

---

## 0 · Global shell

```
┌─────────────────────────────────────────────┐
│ ⟵  ODR · {project_number}                   │  ← back to project list
│      Day 47 · Wed May 28 · 06:14 ET         │  ← auto Section 1 strip
├─────────────────────────────────────────────┤
│  ▮▮▮▮▯▯▯▯▯▯▯▯▯▯▯▯  4 / 16 sections          │  ← passive progress
│  3 coaching prompts · 0 hard stops          │  ← from § 15 engine
├─────────────────────────────────────────────┤
│  [Section pill bar — horizontally scrolls]  │
│  PROJECT  CREW  MANPOWER  EQUIP  …          │
├─────────────────────────────────────────────┤
│                                             │
│            (active section body)            │
│                                             │
├─────────────────────────────────────────────┤
│  Save Draft       Review & Submit          │  ← sticky bottom bar
└─────────────────────────────────────────────┘
```

- Always visible: project header strip, progress, sticky action bar.
- No red pills. No celebratory toasts. **Single-red doctrine.**
- The progress bar is passive; numbers and pills are calm-coloured.
- Mic icon (🎙) appears next to any free-text field — voice-to-text.

---

## 1 · Section 1 · Project Snapshot

```
┌─────────────────────────────────────────────┐
│  Project Snapshot                       ⓘ   │
├─────────────────────────────────────────────┤
│  Project   ▸ I-95 / SR-9 Widening · #43-217 │  read-only
│  Contract  ▸ E1S22                          │  read-only
│  Date      ▸ Wed · 2026-05-28               │  read-only
│  Day #     ▸ 47                             │  read-only
│  Location  ▸ 27.96198, -82.12041   ±3.2m    │  read-only · pull-to-refresh
│  Created   ▸ 06:14 ET (10:14 UTC)           │  read-only
│  Foreman   ▸ Carlos Reyes                   │  read-only (you)
│  Super     ▸ J. Murphy            change ▾  │  selectable
│  PM        ▸ M. Ortiz             change ▾  │  selectable
│ ───────────────────────────────────────────  │
│  Weather   ▸ Partly cloudy · 78°F · 6 mph W │  auto NOAA
│  Sun       ▸ 06:39 — 20:14                  │  auto
│  Rain      ▸ 0.00″ today / 0.08″ overnight  │  auto
└─────────────────────────────────────────────┘
```

Nothing here for the foreman to do unless the auto-pull failed
(then the section turns into a single-tap "refresh weather" button).

---

## 2 · Section 2 · Crew Profile

```
┌─────────────────────────────────────────────┐
│  Crew Profile                    *required  │
├─────────────────────────────────────────────┤
│  Crew Type ▾  ┌──────────────┐              │
│               │ Pipe         │  (last used) │
│               │ Utility      │              │
│               │ Grading      │              │
│               │ … 13 more    │              │
│               └──────────────┘              │
│                                             │
│  Primary Operation ▾                         │
│  (filtered list driven by crew_type)        │
│  · Install storm pipe                       │
│  · Install structures                       │
│  · Backfill / compact                       │
│  · Pressure test                            │
│  · Other                                    │
│                                             │
│  Secondary (multi-select)                   │
└─────────────────────────────────────────────┘
```

- Both fields default to the crew's **last 7-day mode** (most common
  recent value). Foreman taps to confirm — usually one tap.
- Choosing `crew_type` **switches the Section 6 template** before
  the foreman gets there.

---

## 3 · Section 3 · Manpower

```
┌─────────────────────────────────────────────┐
│  Manpower · 8 expected · 7 confirmed        │
├─────────────────────────────────────────────┤
│  ⚠ 1 missing: Diego Cruz   [absent ▾]       │  coaching, not alert
├─────────────────────────────────────────────┤
│  Carlos Reyes · Foreman      10.0 h  ✓      │
│  J. Murphy · Operator         9.5 h  ✓      │
│  T. Webb · Laborer           10.0 h  ✓      │
│  K. Vance · Op                8.0 h ✏       │  tap to edit hours
│  …                                          │
├─────────────────────────────────────────────┤
│  + Add walk-on                              │  rare path
└─────────────────────────────────────────────┘
```

- Roster pre-populated from yesterday's ODR + dispatch board.
- Default `hours = scheduled hours`. Foreman taps any row to adjust.
- Missing personnel surfaces a one-tap reason picker (sick / leave /
  no-show / reassigned).

---

## 4 · Section 4 · Equipment

```
┌─────────────────────────────────────────────┐
│  Equipment · 5 assigned                     │
├─────────────────────────────────────────────┤
│  Cat 320 Excavator · #E-114                 │
│    Hours  ▸ 8.5    Idle 1.5    Down 0.0    │
│    [+ Maintenance issue]                    │
│                                             │
│  John Deere 850K Dozer · #E-088   ⚠         │
│    Hours  ▸ 7.0    Idle 2.0    Down 1.0    │
│    Issue ▸ Hydraulic leak (rear)            │
│    Photos ▸ [+]                             │
│    → Auto Shop visibility on submit         │
│                                             │
│  …                                          │
└─────────────────────────────────────────────┘
```

- Asset roster pulled from `equipment` master via the day's dispatch.
- Hours field accepts swipe-to-increment in 0.5 h increments.
- Maintenance issue automatically creates a Shop ticket on submit —
  **the foreman never re-enters this in another portal.**

---

## 5 · Section 5 · Subcontractors / Vendors

```
┌─────────────────────────────────────────────┐
│  Subcontractors / Vendors                   │
├─────────────────────────────────────────────┤
│  Coastal Striping     Present ◉ ◯           │
│    Work ▸ [voice icon] "striped lanes 1–3"  │
│                                             │
│  Vulcan Materials     Delivery only         │
│    21 loads · #57 stone · 11:20 first       │
│                                             │
│  [+ Add sub] [+ Add delivery]               │
└─────────────────────────────────────────────┘
```

- Pre-loaded from the project's standing subcontractor list and from
  the day's dispatch deliveries.

---

## 6 · Section 6 · Production (DYNAMIC TEMPLATE)

### 6.A · `crew_type = pipe` (example)

```
┌─────────────────────────────────────────────┐
│  Production · Pipe                          │
├─────────────────────────────────────────────┤
│  Run 1                                      │
│    Pipe size ▾ 24"                          │
│    Material  ▾ RCP                          │
│    LF installed     ▸ 220                   │
│    From structure   ▸ S-14                  │
│    To structure     ▸ S-16                  │
│    Backfill type    ▾ #57 stone             │
│    Compaction %     ▸ 98                    │
│    Testing          ▸ [+ add test record]   │
│                                             │
│  [+ Add run]                                │
│                                             │
│  ── Structures set ──                        │
│    S-15  · 24" tee · 11:40                  │
│    [+ Add structure]                        │
│                                             │
│  Total today ▸ 220 LF · 1 structure         │
└─────────────────────────────────────────────┘
```

### 6.B · `crew_type = paving` (template switch)

```
┌─────────────────────────────────────────────┐
│  Production · Paving                        │
├─────────────────────────────────────────────┤
│  Lift     ▾ Type SP-12.5 · 1.5"             │
│  Tons     ▸ 412                             │
│  Station limits  ▸ 122+50 — 132+00          │
│  Mix temp at lay-down ▸ 305°F               │
│  Compaction          ▸ 93% / 92%            │
│                                             │
│  [+ Add lift]                               │
└─────────────────────────────────────────────┘
```

### 6.C · `crew_type = mot` (template switch)

```
┌─────────────────────────────────────────────┐
│  Production · MOT                           │
├─────────────────────────────────────────────┤
│  Lane closure type ▾ Single-lane south      │
│  Hours active   ▸ 7.5                       │
│  Changes today  ▸ 2 (06:00 set / 13:30 lift)│
│  Detour active  ▸ No                        │
│                                             │
│  [+ Add closure event]                      │
└─────────────────────────────────────────────┘
```

The template comes from `crew_type` + `primary_operation`. Closed-set
dropdowns ensure analytics on Day 2.

---

## 7 · Section 7 · Delays

```
┌─────────────────────────────────────────────┐
│  Any delays today?      ◯ No   ◉ Yes        │ ← mandatory
├─────────────────────────────────────────────┤
│  Delay 1                                    │
│    Type   ▾ Utility                         │
│    Hours  ▸ 2.5                             │
│    Notes  🎙 "FPL crew didn't arrive…"      │
│    Photos [+]                               │
│                                             │
│  [+ Add delay]                              │
└─────────────────────────────────────────────┘
```

If `No` is selected the section collapses to a single line and the
progress pill advances. The "Yes" branch never asks the foreman to
type a type — it's a closed-set dropdown.

---

## 8 · Section 8 · Extra Work

```
┌─────────────────────────────────────────────┐
│  Any extra work?        ◯ No   ◉ Yes        │
├─────────────────────────────────────────────┤
│  Extra 1                                    │
│    Requested by      ▸ M. Lopez (CEI)       │
│    Description       🎙 …                    │
│    Cost impact       ▸ $4,200 (est)         │
│    Schedule impact   ▸ 0.5 day              │
│    Photos            [+]                    │
└─────────────────────────────────────────────┘
```

---

## 9 · Section 9 · Constraints

```
┌─────────────────────────────────────────────┐
│  Constraints                                │
├─────────────────────────────────────────────┤
│  Today's obstacles? (tap all that apply)    │
│  □ Utility   □ Survey   □ Design            │
│  □ Access    □ Staffing □ Material          │
│  □ Equipment □ Other                        │
│                                             │
│  Selected — Utility                          │
│    Description 🎙 …                          │
│    Recurs?  ◯ Yes (links to Memory)         │
└─────────────────────────────────────────────┘
```

Selected items become `operational_constraints` rows automatically
(V-Prelude Wave 1 substrate). Foreman never visits a separate
"Constraints" portal.

---

## 10 · Section 10 · Safety Compliance · HARD-STOP

```
┌─────────────────────────────────────────────┐
│  Safety today                               │
├─────────────────────────────────────────────┤
│  Accident?                ◯ Yes  ◉ No       │
│  Incident?                ◯ Yes  ◉ No       │
│  Near miss?               ◯ Yes  ◉ No       │
│  Property damage?         ◯ Yes  ◉ No       │
│  Environmental release?   ◯ Yes  ◉ No       │
│  Injury?                  ◯ Yes  ◉ No       │
└─────────────────────────────────────────────┘
```

When **any** flag flips to Yes:

```
┌─────────────────────────────────────────────┐
│  ⛔  Safety event detected — required:       │
│                                             │
│  Notified Safety?    ◯ Yes  ◉ No            │
│   ↳ Contact name    ▸ ____                  │
│   ↳ Contact time    ▸ ____                  │
│                                             │
│  Incident report complete?  ◯ Yes  ◯ No     │
│   ↳ [Open incident report] →                │
│                                             │
│  Submission blocked until both = Yes.       │
└─────────────────────────────────────────────┘
```

**Hard stop.** The Review & Submit button is disabled until both
Safety-notified and Incident-report-complete are true. The "Open
incident report" link launches the existing Safety incident form
deep-linked to this ODR — **single entry, no duplicate workflow.**

---

## 11 · Section 11 · Weather Impact

```
┌─────────────────────────────────────────────┐
│  Weather today: 78°F · partly cloudy        │  auto
│  Did weather impact work?    ◯ Yes  ◉ No    │
│   ↳ Hours lost   ▸ ____                     │  only if Yes
│   ↳ Notes        🎙 ____                     │
└─────────────────────────────────────────────┘
```

Foreman never types a temperature or wind speed — those came from § 1.

---

## 12 · Section 12 · Photos

```
┌─────────────────────────────────────────────┐
│  Photos · 9 today                           │
├─────────────────────────────────────────────┤
│  Drag to re-tag · long-press for caption    │
│                                             │
│  ┌────┐ Prod │ ┌────┐ Delay│ ┌────┐ Equip   │
│  │ 1  │ S-15│ │ 2  │ FPL  │ │ 3  │ leak    │
│  └────┘     │ └────┘      │ └────┘          │
│  ┌────┐ Prod│ ┌────┐ QC   │ ┌────┐ MOT      │
│  │ 4  │     │ │ 5  │ comp│ │ 6  │           │
│  └────┘     │ └────┘     │ └────┘           │
│                                             │
│  [+ Take photo]  [+ From album]             │
└─────────────────────────────────────────────┘
```

- Photos tagged via the long-press chip; default tag inferred from
  the section the foreman was in when the camera was opened.
- Voice caption icon on every thumbnail (🎙); transcript shows once
  Whisper returns (offline → fallback "tap to type").

---

## 13 · Section 13 · Tomorrow Plan

```
┌─────────────────────────────────────────────┐
│  Tomorrow                                   │
├─────────────────────────────────────────────┤
│  Planned work       🎙 "finish S-16 to S-18"│
│  Resources needed   □ #57 stone  □ pump     │
│                     □ flagger    □ vactor   │
│  Concerns           □ rain risk  □ utility  │
└─────────────────────────────────────────────┘
```

Checkbox lists are pre-populated from yesterday's plan + the project's
weekly Look-Ahead. Foreman edits in place.

---

## 14 · Section 14 · Plan vs Actual

```
┌─────────────────────────────────────────────┐
│  Did the crew complete today's plan?        │
│           ◉ Yes      ◯ No                   │
├─────────────────────────────────────────────┤
│  (Only if No)                               │
│  Reason  ▾ Material delivery short          │
│  Schedule impact ▸ 0.5 day                  │
└─────────────────────────────────────────────┘
```

---

## 15 · Section 15 · Readiness Check

Rendered as a calm checklist **inline** at the top of the Review &
Submit screen — never as a separate page.

```
┌─────────────────────────────────────────────┐
│  Ready to submit?                           │
├─────────────────────────────────────────────┤
│  ⛔ Hard stops · 0                            │
│  ⚠ Coaching · 3                             │
│     · Add 1 photo to "Delay 1" for          │
│        claims protection.                   │
│     · Compaction missing on Run 2.          │
│     · Tomorrow's resources list is empty.   │
│                                             │
│  [Save Draft]    [Submit ODR]   ← enabled   │
└─────────────────────────────────────────────┘
```

Coaching is **opt-in** — the foreman can submit through it. Only the
Safety hard-stop in § 10 actually blocks the button.

---

## 16 · Section 16 · PM Review (Phase 2 surface)

At launch the field carries the value but the UI surface is the
existing project page (a single status pill). Reviewer queue lands in
V.1.1.

```
ODR  ·  Submitted        ⏎ awaiting PM review
ODR  ·  Returned         ⏎ "fix compaction"
ODR  ·  Approved         ⏎ M. Ortiz · 18:11
```

---

## 17 · Cross-cutting interaction rules

| Rule | Where it applies |
|---|---|
| Voice-to-text on every free-text field | § 5, 7, 8, 9, 11, 12, 13, 14 |
| Dropdowns before free-text | § 2, 6, 7, 9 (constraint type), 8 (requested-by org) |
| Auto-fill from yesterday / dispatch / weather / master | § 1, 2, 3, 4, 5, 13 |
| Single entry → multi-consumer | maintenance → Shop · safety → Safety · constraint → Memory |
| No celebratory toasts · no badges · single-red doctrine | global |
| TRUST-TIME-1 timestamps (Z UTC + render local) | every dated surface |
| Photo governance Wave 1 contract inherited | § 12 |

---

## 18 · Open UI questions for operator review

1. Should the section pill bar collapse on mobile portrait when the
   foreman is mid-section? (Default: yes — saves 56 px of vertical.)
2. Should the readiness coaching list be visible during entry, or
   only on the Review screen? (Default: only on Review — keeps the
   entry pane uncluttered.)
3. Should voice captions be transcribed inline as the foreman
   speaks, or after a long-press release? (Default: stream live with
   final settling on release.)
4. Should the foreman be able to assign multiple `secondary_operations`
   in Section 2? (Default: yes — up to 3.)
5. Should the PM Review pill appear inside the ODR itself, or only
   on the PM project detail page? (Default: both — calm pill on the
   ODR + queue on PM project page.)

Awaiting operator decisions before implementation.

---

_Artifact 2 of 5 · proceed to ODR_ECOSYSTEM_INTEGRATION_MAP.md_

---

# Delta Integration Addendum (D1–D8) · 2026-05-29

This addendum revises the UI to absorb D1–D8 + O1–O10 without
breaking the simplicity doctrine. Wireframes here **supersede** the
sections they touch.

## U1 · Global shell · EN/ES toggle + Sync pill (D4 + D6)

```
┌─────────────────────────────────────────────┐
│ ⟵  ODR · #43-217   ◉ Sync clean   EN | ES   │  ← top bar
│      Day 47 · Wed May 28 · 06:14 ET         │
├─────────────────────────────────────────────┤
│  ▮▮▮▮▮▯▯▯▯▯▯▯▯▯▯▯▯▯  5 / 18 sections        │  passive
│  3 coaching · 0 hard stops                   │
├─────────────────────────────────────────────┤
│  [Section pill bar — scrolls horizontally]   │
│  PROJECT  CREW  AREAS  MANPOWER  EQUIP …    │
└─────────────────────────────────────────────┘
```

- **EN / ES toggle** lives in the top bar. When toggled to ES, every
  label / hint / dropdown enum / coaching message renders in Spanish
  via existing `frontend/src/lib/i18n` string tables.
- **Sync pill** shows `Sync clean · Pending · Conflict · Error` from
  `reliability.sync_state`. Tap to see queue detail.
- 18 sections now (16 original + 2.5 Work Areas + 5.5 Materials).

## U2 · Section 2.5 · Work Areas (NEW · D2)

Sits between Crew Profile and Manpower. Pre-populated from
yesterday's ODR + Memory pattern matching for the project.

```
┌─────────────────────────────────────────────┐
│  Work areas today                            │
├─────────────────────────────────────────────┤
│  ◉ MP 12.4 SB         (yesterday's area)    │
│  ◉ MP 13.1 SB         (suggested · Memory)  │
│  ◯ Taxiway B          (rarely used here)    │
│                                              │
│  [+ Add area]                                │
│                                              │
│  Selected — MP 12.4 SB                       │
│   Station    ▸ 122+50 — 132+00               │
│   Notes      🎙 …                            │
└─────────────────────────────────────────────┘
```

Foreman taps to confirm or add. **Zero typing on a typical day.**
Each work area becomes a chip that can be attached to any later
event (delay · extra work · production segment · material · photo).

## U3 · Section 5.5 · Materials (NEW · D3)

Sits between Subcontractors and Production. Defaults to empty on
no-material days — adds **0 seconds** when nothing happened.

```
┌─────────────────────────────────────────────┐
│  Materials today                             │
├─────────────────────────────────────────────┤
│  ┌─ #57 Stone · Vulcan ─────────────────┐   │
│  │  Kind ▾ Delivered   Qty 21 · ton      │   │
│  │  Area ▾ MP 12.4 SB                     │   │
│  │  Tickets · 21 (autofilled from dispatch)│   │
│  │  Issue · none                          │   │
│  └────────────────────────────────────────┘   │
│  [+ Add material]                            │
└─────────────────────────────────────────────┘
```

Auto-pre-fill from today's dispatch deliveries. Foreman confirms
quantity if it differs from what arrived.

## U4 · Section 6 · Production Segments (REVISED · D1)

The polymorphic template per `crew_type` from the original spec now
runs **per segment**. Add-row pattern: foreman taps `[+ Add segment]`
to start a new operation (e.g., paving after pipe).

```
┌─────────────────────────────────────────────┐
│  Production · Segment 1 / 2                 │
│  Crew type ▾ Pipe   Area ▾ MP 12.4 SB       │
├─────────────────────────────────────────────┤
│  Run 1 · 24" RCP · 220 LF · S-14 → S-16     │
│  Run 2 · …                                   │
│  [+ Add run]                                 │
│                                              │
│  ←  Segment 1   ●●   Segment 2  →            │  swipe between
├─────────────────────────────────────────────┤
│  [+ Add segment]                             │
└─────────────────────────────────────────────┘
```

- **Single-segment days look identical to the original spec.** The
  "+ Add segment" affordance is a soft secondary action.
- Each segment can target a different `work_area_id`.
- Cap: 6 segments per ODR (operator-configurable).

## U5 · Section 10 · Safety per-event branch (REVISED · D7)

```
┌─────────────────────────────────────────────┐
│  Safety today                                │
├─────────────────────────────────────────────┤
│  Accident?                ◯ Yes  ◉ No        │
│  Incident?                ◉ Yes  ◯ No   ⛔   │
│  Near miss?               ◯ Yes  ◉ No        │
│  Property damage?         ◯ Yes  ◉ No        │
│  Environmental release?   ◯ Yes  ◉ No        │
│  Injury?                  ◯ Yes  ◉ No        │
└─────────────────────────────────────────────┘
        ↓ when any Yes:
┌─────────────────────────────────────────────┐
│  ⛔  Safety event(s) — required:              │
│                                              │
│   Event 1 · Incident                        │
│     Notified Safety?    ◉ Yes  ◯ No          │
│      ↳ Contact name    ▸ J. Vincent           │
│      ↳ Contact time    ▸ 14:12 ET             │
│     Incident report complete?  ◯ Yes  ◯ No   │
│      ↳ [Open incident report] →               │
│                                              │
│   [+ Add another safety event]               │
│                                              │
│  Submission blocked until each event = Yes.  │
└─────────────────────────────────────────────┘
```

Multiple events in one ODR (e.g., one incident **and** one property-
damage) each carry their own contact / time / linked-report lineage.

## U6 · Reliability surfaces (D4)

Three small additions to existing surfaces. **No new section.**

- **Top-bar sync pill** (see U1) — replaces nothing; new tag.
- **Auto-save indicator** appears beneath the sticky bottom bar:
  `Saved 06:21 ET` (text-only, single-line). Updates every ≤ 5 s.
- **Offline mode banner** (single calm text line · NOT red): "You are
  offline — saving locally. Will sync when connected."
- **Conflict resolver** (rare path · drawer) opens only when
  `sync_conflicts` is non-empty. Side-by-side server/client view; one-
  tap resolve.

## U7 · Bilingual interaction rules (D6)

| Field | EN entry | ES entry | Storage |
|---|---|---|---|
| Free-text (all 10 fields) | typed or voice-EN | typed or voice-ES | `LocalizedString.original` preserves ES; `text` carries EN canonical (auto-translated on save) |
| Dropdowns | EN labels | ES labels (i18n table) | enum value (language-independent) |
| Section titles · hints · coaching | EN | ES | i18n table |
| Hard-stop messages (§ 10) | EN | ES | i18n table |
| Photo voice captions | EN audio | ES audio | both audio + transcript + EN translation |

Toggle is single-tap, persists per-foreman in localStorage. No
foreman ever has to "re-enter in English" — the platform does the
translation, the foreman can re-edit the canonical text if they want.

## U8 · Updated per-section completion-time receipt (after D1–D8)

(Verbatim from `ODR_SPEC_LOCK_READINESS_REVIEW.md § 2.)

- Typical-day total: **4 m 15 s – 7 m 45 s**
- Complex-day total: **8 m – 13 m**

D1–D3 add 15–90 seconds on a typical day. Doctrine O3 (< 5 min) is
achievable when Memory pre-fills work areas + materials defaults to
empty + production stays single-segment (~85% of crew-days).

## U9 · Cross-cutting interaction rules — REVISED

Adds to original § 17:

| Rule | Where it applies |
|---|---|
| EN/ES toggle in global shell | global |
| LocalizedString fields wrap voice + text | 10 free-text fields |
| Add-row / add-segment pattern | Work Areas · Materials · Production Segments · Safety Events |
| Work-area chip selector on every event-bearing form | Delays · Extra Work · Constraints · Equipment · Materials · Photos · Segments |
| Sync pill visibility | global |
| Auto-save indicator | global |
| Offline mode banner | global (when offline) |

## U10 · Doctrine anchors (O1–O10 in UI)

| Doctrine | Where visible |
|---|---|
| O1 complexity ≠ burden | add-row pattern + auto-pre-fill from yesterday/Memory |
| O2 many of everything | every multi-row section + new § 2.5 + § 5.5 + per-event safety |
| O3 < 5 min typical day | passive progress bar + auto-fill density |
| O4 voice/dropdown/auto-fill | mic icon on every free-text · closed-set dropdowns · last-7-day defaults |
| O5 platform > foreman | Memory suggestions in § 2.5, § 9 · dispatch pre-fill in § 5.5 |
| O6 single-entry | Safety incident "Open incident report" inline · no duplicate form |
| O7 bilingual native | EN/ES toggle from day 1 |
| O8 reliability | sync pill + auto-save indicator + offline banner |
| O9 safety hard-stop · production coach | § 10 disables submit; § 15 coaching never blocks |
| O10 PDF executive | PDF_LAYOUT artifact |

_End of Delta Integration Addendum (D1–D8) · UI_WIREFRAMES._

---

# Public-Link Device Continuity Addendum · 2026-05-29

This addendum revises the foreman entry flow to honour the Public
Link Device Continuity Doctrine (O11–O20). Wireframes here describe
the four new flows triggered by the continuity gate.

## C1 · Open public link · continuity decision moment

When the foreman opens `https://mascidocs.com/odr/<link_id>/today`,
the continuity engine evaluates the seven signals **before** any
prior-day data is shipped to the device. The decision moment lasts
≤ 300 ms and is invisible to the foreman in the success path.

## C2 · Flow A · continuity PASSES (verified device)

```
┌─────────────────────────────────────────────┐
│  ODR · #43-217 · Reyes Crew                  │
│  Welcome back. Today is Thursday, May 29.   │
│                                              │
│  We've pre-filled today's report with your   │
│  crew, equipment, subs, and work areas       │
│  from yesterday.                             │
│                                              │
│   [Start today's report]                     │
│   [Start blank instead]                      │
└─────────────────────────────────────────────┘
```

- Single calm header sentence — no badge, no chrome, no banner.
- Pre-filled data: crew roster · equipment list · subs/vendors ·
  work areas · production-segment shells (crew_type +
  primary_operation only — never values). See `ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md § 4`.
- Always show a "Start blank instead" affordance so the foreman is
  never forced into yesterday's context.

## C3 · Flow B · continuity FAILS (denied preload · calm fallback)

```
┌─────────────────────────────────────────────┐
│  ODR · #43-217                               │
│                                              │
│  We could not verify this is the same       │
│  device that created yesterday's report.    │
│  Start a blank report for today.            │
│                                              │
│  [Start blank report]                       │
│  [Get help from your PM]                    │
└─────────────────────────────────────────────┘
```

- One sentence. Single primary action.
- Neutral chrome — no red, no warning glyph, no "security",
  "denied", "unauthorized", or "error" copy. (Per doctrine O20.)
- The "Get help from your PM" link opens a `mailto:` / phone link
  configured per project; it does **not** trigger an in-app override.
- The form opens blank if the foreman taps "Start blank report".
  Project / date / weather still auto-fill (those are public, not
  prior-ODR data).

## C4 · Flow C · authenticated PM/Admin override (inside portal · not public link)

This flow lives in `/pm/projects/:projectNumber/odr/...` (PM
portal) and `/admin/odr/...` (Admin portal). It is **not**
reachable from the public link surface.

```
┌─────────────────────────────────────────────┐
│  PM · Project #43-217 · ODR · 2026-05-28     │
├─────────────────────────────────────────────┤
│  Reyes Crew · submitted 18:11 ET             │
│  Trusted devices (3):                        │
│    · iPhone 15 · iOS 17.4 · last seen 18:11 │
│    · iPhone 13 · iOS 17.3 · last seen May 26│
│    · iPad Air · iPadOS 17.4 · last seen Apr │
│                                              │
│  Recent preload attempts (5):                │
│    · 06:14 ET today · denied_device_mismatch │
│    · 06:11 ET today · denied_device_mismatch │
│    …                                         │
│                                              │
│  Trust a new device                          │
│    Device fingerprint: ___ (paste from foreman's screen)│
│    Reason: _________________________________ │
│   [Trust this device for preload]            │
└─────────────────────────────────────────────┘
```

- Override action requires PM-token or Admin-token authentication;
  the route enforces token type.
- Action writes one row to `odr_preload_attempts` with
  `outcome="override_used"` + `override_actor_uid` + `override_portal`
  + `notes`.
- Action appends a `DeviceToken` to `public_access.device_tokens[]`
  with `issued_via="pm_override"` or `"admin_override"` and an
  `expires_at_utc` per the operator-configurable TTL.
- Foreman reloads the public link → continuity now passes → Flow A.

## C5 · Flow D · first-time device (no prior preload context)

When the link has no prior ODR yet (first day of project, or new
crew), the foreman is **not** subject to a continuity decision —
there is nothing to preload. Section 1 auto-fills from project
metadata; everything else opens blank. On submission, the foreman's
device fingerprint + a freshly-minted `DeviceToken` are stamped
into the new ODR's `public_access.device_tokens[]` with
`issued_via="foreman_first_use"`. Subsequent days will treat this
device as trusted (signal 1 + 2 pass).

## C6 · Global shell · continuity status pill (passive)

A small, calm pill appears in the top bar (next to the existing
`Sync clean` + `EN | ES` pills):

```
┌────────────────────────────────────────────────┐
│ ⟵ ODR · #43-217  ◉ Sync clean  EN|ES  ◉ Trusted │
└────────────────────────────────────────────────┘
```

- `Trusted` — this device passed continuity OR is the link's
  first-use device.
- `Not trusted` — appears only on Flow B; same calm tone.
- `New device` — appears on Flow D first-use.

No tooltip mentions security. Tone is operational, not adversarial.

## C7 · Bilingual coverage (D6 inheritance)

Flow B and Flow D messages have i18n string entries in:

- `frontend/src/lib/i18n/en/odr.public_link.json` (planned)
- `frontend/src/lib/i18n/es/odr.public_link.json` (planned)

The `odr_bilingual_probe.py` (D8) extends to assert these entries
exist in both languages — the failure UX must be readable to a
Spanish-speaking foreman without code-switching.

## C8 · Doctrine anchors (O11–O20 in UI)

| Doctrine | Flow / surface |
|---|---|
| O11 public-link scope | none of these flows expose other crews or other projects |
| O12–O14 continuity-gated preload | Flow A vs Flow B branching at moment-of-open |
| O15 no leak | Flow B opens blank · zero prior data on screen |
| O16 manual blank always allowed | "Start blank instead" on Flow A · primary action on Flow B |
| O17 override authenticated only | Flow C lives only in PM / Admin portals · not in any public route |
| O18 audit logged | every flow writes one `odr_preload_attempts` row |
| O20 asymmetric default | Flow B copy is calm; the system prefers blank over leak |

_End of Public-Link Device Continuity Addendum · UI_WIREFRAMES._

---

# Final Governance Addendum · 2026-05-29

This addendum adds the Field Leadership ODR Center, the ODR Inbox,
the foreman / superintendent / PM views, the signature affordance,
and the attachment add affordance. **No implementation.**

## G1 · Field Leadership ODR Center · top-level

Location: `/field-leadership/portal/odr` (authenticated · X-FL-Token).
Three left-rail destinations:

```
┌──────────────────────────────────────────────────────┐
│  Field Leadership                                     │
│  · ODR · Inbox                                        │
│  · ODR · Mine (foreman own-only · all roles see)      │
│  · ODR · Search / Export (Super+)                     │
├──────────────────────────────────────────────────────┤
│  (selected view body)                                 │
└──────────────────────────────────────────────────────┘
```

## G2 · Inbox wireframe (Superintendent · scope: project)

```
┌──────────────────────────────────────────────────────┐
│  ODR Inbox · Project #43-217 · Reyes/Davis crews     │
├──────────────────────────────────────────────────────┤
│  ┌Missing 2┐┌Draft 1┐┌Submitted 4┐┌Returned 1┐┌Approved 187┐│
│                                                       │
│  Missing                                              │
│    · Reyes Pipe     2026-05-28      [Open record]    │
│    · Davis Paving   2026-05-28      [Open record]    │
│                                                       │
│  Submitted                                            │
│    · Davis Paving   2026-05-28   18:11 ET  ▸          │
│       readiness ◉◉◉◉○  (4 coaching)                  │
│    · Reyes Pipe     2026-05-27   17:54 ET  ▸          │
│    · …                                                │
│                                                       │
│  Returned                                             │
│    · Reyes Pipe     2026-05-26  "fix compaction"      │
└──────────────────────────────────────────────────────┘
```

- Five tabs at top; counts auto-update.
- Each row carries the calm readiness dots (filled = sections
  complete) — visible coaching, no scoring.
- "Open record" launches the review surface (G3).

## G3 · Superintendent review surface (Submitted → Approved)

```
┌──────────────────────────────────────────────────────┐
│  ⟵ Inbox      Davis Paving · 2026-05-28 · ODR-…-00427 │
├──────────────────────────────────────────────────────┤
│  [ Today at a glance card · same shape as PDF p.1 ]   │
│                                                       │
│  Sections (collapsed by default)                      │
│    ▸ Project · Crew · Work Areas · Manpower …         │
│                                                       │
│  Readiness                                            │
│    · 4 coaching items — open ▾                       │
│                                                       │
│  Actions:                                             │
│    [ Amend a field ]  [ Return for revision ]  [ Approve ] │
│                                                       │
│  Amendment log (chronological)                        │
│    · J. Murphy · 2026-05-28 19:02 · production_       │
│       segments[0].body.pipe.runs[0].compaction_pct    │
│       96 → 98 · "field re-measure" ▸                  │
└──────────────────────────────────────────────────────┘
```

- Amend surface opens a per-field editor with required `reason`.
- Return surface requires a reason; transitions `submitted → returned`.
- Approve transitions `submitted | returned → approved` · validates
  quality (does NOT change the official record status).

## G4 · Foreman "Mine" view (own ODRs · all FL foremen)

```
┌──────────────────────────────────────────────────────┐
│  My ODRs · Carlos Reyes                              │
├──────────────────────────────────────────────────────┤
│  Drafts (1)                                          │
│   · 2026-05-29 11:24 ET · pipe · Reyes crew  [Open]  │
│  Submitted (last 30d)                                │
│   · 2026-05-28 18:11 ET · edit window: 16h 22m left  │
│       [View] [Edit]                                  │
│   · 2026-05-27 17:54 ET · edit window: closed        │
│       [View only]                                    │
│  Returned (1)                                        │
│   · 2026-05-26 · "fix compaction" · [Re-open]        │
│  Approved (most recent 5)                            │
│   · 2026-05-25 · 2026-05-24 · …                      │
└──────────────────────────────────────────────────────┘
```

- 24h edit window shown as a live countdown next to "Submitted" rows.
- After 24h, "[Edit]" is replaced by "[View only]" with the calm
  text "Window closed. Ask your Superintendent for an amendment."

## G5 · PM Portal · ODR consumption surface (READ-ONLY)

PM stays in their existing portal (`/pm/projects/:projectNumber`).
A read-only ODR panel is added beneath the existing Project Detail
content:

```
┌──────────────────────────────────────────────────────┐
│  ODR · #43-217 · last 7 days                          │
├──────────────────────────────────────────────────────┤
│  ◉◉◉◉◉◉◉ 7/7 days reported                            │
│  · Davis Paving  · 2026-05-28 · Approved              │
│  · Reyes Pipe    · 2026-05-28 · Approved              │
│  · …                                                  │
│                                                       │
│  [ Search ODRs ]   [ Export selection ]               │
│  [ Quality dashboard ]   [ Completion dashboard ]     │
└──────────────────────────────────────────────────────┘
```

- **PM cannot edit, return, approve, or amend.** Action buttons are
  absent — not greyed out — to enforce O22.
- Quality dashboard shows aggregated coaching counts; never per-
  foreman scoring.

## G6 · Foreman signature at submit (O31)

Added to the bottom of the Review & Submit screen (UI § 15 of the
original spec):

```
┌──────────────────────────────────────────────────────┐
│  I certify the information on this report is true    │
│  and complete to the best of my knowledge.           │
│  ☐  I acknowledge                                     │
│                                                       │
│  [Submit ODR]   (disabled until check + readiness OK) │
└──────────────────────────────────────────────────────┘
```

- Single checkbox · single sentence.
- Renders in both EN and ES via existing i18n table.
- On submit, the check is stamped into `signature.foreman_ack` with
  fingerprint + timestamp + UID.

## G7 · Attachment add affordance (O32)

Added to the Photos section (UI § 12) AND to relevant per-event
forms (Materials, ExtraWork, Safety):

```
┌──────────────────────────────────────────────────────┐
│  Evidence                                             │
├──────────────────────────────────────────────────────┤
│  Photos  9                                            │
│  Attachments  2                                       │
│    · Delivery ticket · Vulcan · #21338 · 1.4 MB · PDF │
│    · CEI directive   · M. Lopez · 2026-05-28 · PDF   │
│                                                       │
│  [+ Photo]  [+ Attachment]                            │
└──────────────────────────────────────────────────────┘
```

- "[+ Attachment]" opens a kind selector (Delivery / Haul / Density
  / Asphalt / Concrete / CEI / FAA / FDOT / RFI / Other).
- Architecture supports all 11 attachment kinds today; UI exposure
  is staged per `ODR_FINAL_GOVERNANCE_ADDENDUM.md § 8` (V.1 exposes
  delivery ticket numbers via materials; richer attachment surfaces
  arrive M1+).

## G8 · Doctrine anchors (O21–O35 in UI)

| Doctrine | Anchor |
|---|---|
| O21 FL governance | § G1 ODR Center root |
| O22 PM read-only | § G5 (action buttons absent) |
| O23–O24 public ODR simple | original public-link flows unchanged · no Inbox / dashboard on public surface |
| O25 FL ODR Center | § G1 |
| O26 5-category Inbox | § G2 |
| O27 coaching not punish | § G2 readiness dots · § G5 quality dashboard (no per-foreman scoring) |
| O28 24h edit window | § G4 countdown |
| O29 amendment preserves | § G3 amendment log visible |
| O31 foreman signature | § G6 |
| O32 attachments | § G7 |

_End of Final Governance Addendum · UI_WIREFRAMES._

---

# Coaching / Guidance Addendum · 2026-05-29

UI deltas for the coaching doctrine (O36–O50). Read alongside
`ODR_COACHING_GUIDANCE_ADDENDUM.md`.

## C1 · Four guidance touchpoints per section

Every guidance-eligible ODR section (12 sections per addendum § 3)
gains four small affordances next to the section header. None block
entry; all are dismissible.

```
┌──────────────────────────────────────────────────────┐
│  Production · Segment 1                       ⓘ      │  ⓘ = Learn More
│  Crew type ▾ Pipe   Area ▾ MP 12.4 SB                │
│  Tips for pipe crews                                  │  ← pill (Crew Tips)
│  Show example ✎                                       │  ← link (Examples)
│  Best practices ▸                                     │  ← footer link
│  …section body…                                       │
└──────────────────────────────────────────────────────┘
```

- `ⓘ` Learn More — small icon · slide-in drawer · 1 paragraph
- "Tips for X crews" — calm pill at top · opens drawer with 4–6 bullets
- "Show example ✎" — link beneath header · drawer with 2–4 worked examples
- "Best practices ▸" — footer link · deep-links to OGC entry in same drawer

## C2 · Inline guidance drawer (shared shape)

Slides in from the right (desktop) or bottom (mobile). Workflow
context preserved — the underlying form remains visible behind the
drawer. Closing returns the foreman exactly where they were.

```
┌──────────────────────────────────────────────────────┐
│  ✕  Tips for pipe crews                              │
├──────────────────────────────────────────────────────┤
│  · Record bedding type per run                        │
│  · Separate runs by station break                     │
│  · Capture compaction percent + test method           │
│  · Note testing time for claims                       │
│  · Add photo of structure with stationing visible     │
│                                                       │
│  See the Operational Guidance Center for the full     │
│  pipe-crew best practices ▸                           │
└──────────────────────────────────────────────────────┘
```

Bilingual: drawer reads from i18n strings keyed by `prompt_key` ·
EN/ES parity enforced by `odr_bilingual_probe.py` (D8 + this pass).

## C3 · First-time onboarding flow (≤ 2 minutes)

Shown on first open per `(device_fingerprint, project_id)`. Renders
inside the ODR shell as a 4-card slide-show — not a full-screen
takeover. Foreman can dismiss any time.

```
┌──────────────────────────────────────────────────────┐
│  ●○○○  Welcome — this is your daily report.          │
│                                                       │
│  The form fills itself in where it can. You confirm. │
│                                                       │
│  [Got it]   [Skip for now]                           │
└──────────────────────────────────────────────────────┘
```

Cards 2–4: "Sections fill themselves" · "Tap ⓘ for tips on any
section" · "Submit when ready — you have 24h to edit after". Card 4
ends with "Got it". State stored in localStorage keyed to
`(fingerprint, project_id)`. Re-launchable from the help menu →
"Quick start".

## C4 · Top-right help menu

```
┌──────────────────────────────────────────────────────┐
│                                          (?) Help    │
└──────────────────────────────────────────────────────┘
         ▼
┌──────────────────────────────────────────────────────┐
│  · Quick start (4 cards · ≤ 2 min)                   │
│  · Search guidance ▸ (opens OGC search)               │
│  · Contact your superintendent ▸ (mailto/phone)       │
└──────────────────────────────────────────────────────┘
```

Single calm menu. No marketing copy. No surveys. No upsells.

## C5 · Field Leadership Training Center

Lives at `/field-leadership/portal/training` (X-FL-Token Super+).
Read-only. Four panels:

```
┌──────────────────────────────────────────────────────┐
│  ODR Training · Project #43-217                       │
├──── Best Practices ─────────────────────────────────┤
│   · Pipe crew · Pavement crew · MOT crew · …          │
├──── Examples ───────────────────────────────────────┤
│   · Anonymized real-day examples · drag to compare    │
├──── Quality Guidance ───────────────────────────────┤
│   · What makes an ODR claims-defensible               │
├──── Coaching Metrics (aggregate) ───────────────────┤
│   · 87% submitted with all production photos          │
│   · 71% submitted with tomorrow plan                  │
│   · Most coached section: Production · Pipe           │
│   · Most coached prompt: "Add compaction value"       │
└──────────────────────────────────────────────────────┘
```

**No per-foreman names · no per-foreman counts · no rankings.**
Drawing on `CoachingMetricsRollup` from the data-model addendum.

## C6 · PM coaching consumption surface

Added to the existing read-only PM ODR panel
(`ODR_FINAL_GOVERNANCE_ADDENDUM.md § G5` · `UI § G5`):

```
┌──────────────────────────────────────────────────────┐
│  ODR · #43-217 · coaching                             │
├──────────────────────────────────────────────────────┤
│  Completion trend (last 30 days)                      │
│   ▮▮▮▮▮▮▮▯▯▯  79%   (last week 81%)                  │
│  Coaching opportunities (top 3)                       │
│   · 18 reports missing tomorrow plan                  │
│   · 12 reports missing compaction value               │
│   · 8 reports missing delay description               │
│  Common missing information                           │
│   · production.pipe.compaction_pct                    │
│   · tomorrow.planned_work                             │
│   · delays.entries[].description                      │
└──────────────────────────────────────────────────────┘
```

**Aggregate-only.** No per-foreman dimension. No "Request a
performance review" affordance — purely a training-opportunity
identifier.

## C7 · Doctrine anchors (O36–O50 in UI)

| Doctrine | Anchor |
|---|---|
| O37 teach while working | § C1 + § C2 inline drawers |
| O39 multiple guidance modes | § C1 four touchpoints |
| O41 OGC integration | § C2 + § C4 + § C5 + § C6 all read from OGC |
| O42 context-preserving | § C2 inline drawer (no destructive nav) |
| O45 readiness coaches | calm pills · "Suggest" / "Tip" never "Error" |
| O46 first-time onboarding | § C3 |
| O47 FL Training Center | § C5 |
| O48 PM coaching consumption | § C6 |
| O50 never performance-review | § C5 + § C6 aggregate-only |

_End of Coaching / Guidance Addendum · UI_WIREFRAMES._
