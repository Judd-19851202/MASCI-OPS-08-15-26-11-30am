# RFI List · Visual Doctrine
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> The most-used PM surface in the new subsystem. Calm density.
> Scanable. Field-readable. Doctrine-locked.

---

## 1 · Desktop Wireframe (≥ 1024px)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Home  ←  Back            [M]   [Search ⌘K]  [🔔42] [EN|ES]  [Company] [Pwd] [Sign out] │
│ ────────── caution stripe ──────────                                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
┌────────────┬───────────────────────────────────────────────────────────────────────────┐
│            │                                                                           │
│  PM        │  ← Project Manager                                                         │
│  V2        │                                                                           │
│  SIDEBAR   │  PROJECT MANAGER · CHRIS WRIGHT  ·  GOVERNANCE STABLE  ░ ◄ chip            │
│  …         │                                                                           │
│  ▌ OPS     │  RFI Center                                                               │
│  RECORDS   │  Draft, review, submit. PM-owned. Field-first.                            │
│  ──────    │                                                                           │
│   RFI ◄    │  ┌─────────────────────────────────────────────────────────────────────┐  │
│  ▣ CENTER  │  │ FILTERS                                                             │  │
│            │  │ Project [ All ▾ ]   Status [ Open ▾ ]   Priority [ All ▾ ]          │  │
│  Constr… │  │ Discipline [ All ▾ ]   Aging [ Any ▾ ]   Search [ ⌕ ............... ] │  │
│            │  └─────────────────────────────────────────────────────────────────────┘  │
│  Schedule  │                                                                           │
│            │  RFI #     PROJECT        DISCIPLINE   STATION    STATUS    IMPACT   AGE  │
│  Lookahead │  ─────────────────────────────────────────────────────────────────────────│
│            │  ⬤ 0042   T5860 SR 9     Utilities   145+50 RT   ⬛ Submitted  ⛬◌  3d   │
│  Op Impact │  ◯ 0041   T5860 SR 9     Roadway     088+10 LT   ⬛ Submitted  ◌   8d   │
│            │  ⬤ 0040   CC5744 OXFORD   Drainage    220+40      ⬛ CEI Review ⛬◌  1d   │
│  Open P6 ↗ │  ◯ 0039   NSB CORBIN     Roadway     145+90 LT   ⬛ Closed     ─   12d  │
│            │  ⬤ 0038   T5860 SR 9     MOT          010+00      ⬛ Submitted  ⛬◌  5d   │
│            │  ⬜ 0037   I-95 RESURFACE Utilities    342+00 RT   ⬛ Draft       ─   1h   │
│            │  ◯ 0036   NSB CORBIN     Drainage    078+50      ⬛ Closed     ─   18d  │
│            │  ◯ 0035   CC5744 OXFORD   Roadway     200+10      ⬛ Closed     ─   22d  │
│            │  ⬤ 0034   I-95 PHASE 2   FAA Closure 412+10      ⬛ Submitted  ⛬◌  2d   │
│            │  ⬤ 0033   T5860 SR 9     Survey      098+20      ⬛ CEI Review  ◌   4d   │
│            │  ─────────────────────────────────────────────────────────────────────────│
│            │                                                                           │
│            │  Showing 1–10 of 27        [< Prev]  Page 1  [Next >]    Export CSV ↓     │
│            │                                                                           │
└────────────┴───────────────────────────────────────────────────────────────────────────┘
```

### Legend (single-character glyph dictionary · standardized once · reused everywhere)

| Glyph | Meaning |
|---|---|
| `⬤` (filled) | Critical-path impact OR safety/compliance exposure (red-700) |
| `◯` (open circle) | Action required (amber-600) |
| `⬜` (light square) | Routine (slate-500) |
| `⛬` | Has a linked constraint |
| `◌` | Has a linked schedule activity |
| `─` | None of the above |

Every glyph is single-character, monochrome by default, **only** the
left-most severity glyph carries color. This preserves the loudness
budget.

---

## 2 · Row Density

- **Height per row:** 44px (touch-friendly on tablet · still dense
  enough that 10 rows fit above the fold on a 1080px monitor).
- **Hover** brightens the row to `bg-slate-50`.
- **Click** opens the RFI detail panel in a side drawer (desktop) or
  navigates to the detail route (mobile).
- **Columns auto-truncate** with ellipsis · tooltip on hover.

---

## 3 · Required Columns

| Column | Source | Width |
|---|---|---|
| Severity glyph | computed (priority + exposure) | 32px |
| RFI # | `rfi.number` (zero-padded · "0042") | 80px |
| Project | `rfi.project_label` (short name) | 18% |
| Discipline | `rfi.discipline` (from template) | 14% |
| Station | `rfi.station_offset` | 12% |
| Status | `rfi.status` enum label (slate pill) | 14% |
| Impact | constraint glyph + activity glyph | 10% |
| Aging | computed from `submitted_at` / `response_due` | 10% |

That's 8 fixed columns. No "view picker" lets users add more.
Doctrine: one canonical operational view, not a configurable mess.

---

## 4 · Filter Strip

```
┌─────────────────────────────────────────────────────────────────────┐
│ Project [ All ▾ ]  Status [ Open ▾ ]  Priority [ All ▾ ]            │
│ Discipline [ All ▾ ]  Aging [ Any ▾ ]  Search [ ⌕ ................. ] │
└─────────────────────────────────────────────────────────────────────┘
```

- Status default · **Open** (everything not closed / converted / voided).
- Priority default · All.
- Project default · All (within PM scope).
- Filter chip shows under the strip when any filter is active:
  `Showing: Open · T5860 SR 9 · Last 7 days   [Clear all]`

---

## 5 · Empty States

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       No RFIs match the filter.                 │
│                       Adjust filters or clear all.              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

When the project has **zero RFIs ever**:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       No RFIs on this project yet.              │
│                       Draft the first one.   [ New RFI ]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

One CTA · neutral slate-800 button.

---

## 6 · Bulk Operations · Forbidden

There is **no** multi-select checkbox column. Operations on multiple
RFIs at once create silent failure modes and audit gaps. Each RFI is
acted on individually.

---

## 7 · Sort Discipline

Default sort: **Aging (descending)**. The oldest open RFI sits at the
top. Operators can re-sort by clicking column headers. Sort state is
**ephemeral** (per session, not persisted) — there is no "user view
preferences" feature. Doctrine: one canonical view.

---

## 8 · Mobile (≤ 1023px)

```
┌──────────────────────────────────────┐
│  RFI Center                          │
│  Draft, review, submit.              │
│  ──────────                          │
│  [ ⌕ Search ]   [ Filter (3) ▾ ]    │
│  ─────                                │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ ⬤ 0042 · T5860 SR 9            │  │
│  │ Utilities · STA 145+50 RT      │  │
│  │ Submitted · 3 days · ⛬◌         │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ ⬤ 0040 · CC5744 OXFORD          │  │
│  │ Drainage · STA 220+40          │  │
│  │ CEI Review · 1 day · ⛬◌         │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ ⬜ 0037 · I-95 RESURFACE        │  │
│  │ Utilities · STA 342+00 RT      │  │
│  │ Draft · 1 hour · ─              │  │
│  └────────────────────────────────┘  │
│  …                                   │
│                                      │
│  [        + New RFI         ]        │
└──────────────────────────────────────┘
```

Card-style stack. Severity glyph + RFI # on first line, location on
second, status + aging on third. Single floating CTA at the bottom.

---

## 9 · Loudness Probe Targets for `/pm/rfi`

| Metric | Target |
|---|---|
| Hue families on page | ≤ 4 |
| Badge density (per 100 elements) | ≤ 15 |
| Escalation noise (red + amber) | ≤ 8 elements |
| Calmness score | ≥ 72 |
| Direction (after 5 records) | stable |

Same budget as PM Hub V2. The list must not visibly elevate loudness.

---

## 10 · Operator Sign-off Items

- [ ] Default 8-column layout is sufficient for daily PM work.
- [ ] Severity glyph dictionary is intuitive on first glance.
- [ ] Sort/filter discipline (ephemeral, no user views) is acceptable.
- [ ] Mobile card stack reads cleanly under field conditions.
- [ ] No "AI suggestions" or marketing chrome present.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Locked for V.1 list implementation.
