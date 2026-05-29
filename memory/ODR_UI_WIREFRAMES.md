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
