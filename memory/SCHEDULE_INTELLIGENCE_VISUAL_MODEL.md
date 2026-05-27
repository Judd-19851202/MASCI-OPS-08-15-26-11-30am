# Schedule Intelligence · Visual Model
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> Operational intelligence layer above P6. Field-readable. Calm.
> NOT a Primavera replacement. Doctrine-locked.

---

## 1 · Five Views (no more, no less)

| View | Purpose | Default? |
|---|---|---|
| Activity List | The flat operational truth | yes (desktop) |
| Lookahead | Next 14 days, field-readable | yes (mobile) |
| Critical-Path Risk | Where exposure lives now | on tap |
| Operational Impact | RFI × Constraint × Activity | on tap |
| Schedule History | Revision activations + diffs | on tap |

That's all. There is no Gantt view as the default. A Gantt view may
arrive in V.6+ only after operator demand justifies the cognitive
cost. Until then: tables and panels.

---

## 2 · Schedule Hub Landing

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Schedule                                                                     │
│ P6 imports. Active revisions. Read-only intelligence.                       │
│                                                                              │
│ Project [ T5860 SR 9 ▾ ]                                                     │
│ ────────────────────────────────────────────────────────────────────────     │
│                                                                              │
│  ACTIVE REVISION                                                             │
│  ────────                                                                    │
│  Rev 14 · activated 2026-05-22 by Chris Wright                               │
│  Data date 2026-05-15 · 1,342 activities · 96 on critical path               │
│                                                                              │
│  [  Upload .xer  ]   [ Open Primavera P6 ↗ ]                                 │
│                                                                              │
│  ──────────────────                                                          │
│                                                                              │
│  VIEWS                                                                       │
│  ──────                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Activity List              All activities · sortable · scanable      →│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Lookahead                  Next 14 days · field-readable rhythm      →│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Critical-Path Risk         3 CP activities with active constraints   →│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Operational Impact         RFI × Constraint × Activity               →│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Schedule History           14 revisions · diff between any two       →│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Five entries · five neutral CTAs · zero badges · zero charts. The
intelligence is one tap away.

---

## 3 · Activity List View

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Activity List                                                                       │
│ All activities · current revision · scanable.                                       │
│                                                                                     │
│ WBS [ All ▾ ]   Status [ All ▾ ]   CP only [ ☐ ]   Search [ ⌕ ............... ]    │
│ ─────────────────────────────────────────────────────────────────────────────────── │
│                                                                                     │
│ ACT ID    NAME                              START      FINISH     FLOAT  CP   IMP   │
│ ────────  ────────────────────────────────  ─────────  ─────────  ─────  ──   ───   │
│ A0801     MOT Phase 1 · East Lane           2026-05-12  2026-06-02  4d    ⚠         │
│ A0814     Survey Control · STA 098          2026-05-18  2026-05-25  0d    ⚠   ⛬    │
│ A0815     Survey Re-check · STA 098         2026-05-26  2026-05-28  0d    ⚠   ⛬    │
│ A0912     Utility Relocation · STA 145      2026-05-22  2026-06-08  0d    ⚠   ⛬⬤   │
│ A1318     Storm Pipe · STA 220 (mainline)   2026-05-25  2026-06-12  2d    ⚠   ⛬    │
│ A1320     Storm Phase 3 · STA 220+40        2026-05-28  2026-06-18  0d    ⚠   ⛬⬤   │
│ A2310     Friction Course · STA 410-450     2026-06-14  2026-06-21  8d    ─         │
│ A2412     Striping Phase 2                  2026-06-22  2026-06-28  3d    ─         │
│ …                                                                                   │
│ ─────────────────────────────────────────────────────────────────────────────────── │
│ Showing 1–8 of 1,342         [< Prev]  Page 1 of 168  [Next >]    Export CSV ↓     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Column dictionary

| Column | Source | Width |
|---|---|---|
| Activity ID | `task_id` | 80px |
| Name | `task_name` | 32% |
| Start | early_start | 12% |
| Finish | early_finish | 12% |
| Float | `total_float_days` | 8% |
| CP | `is_critical` · `⚠` glyph | 5% |
| IMP | constraint glyph (⛬) · severity dot (⬤ red CP-overdue · ◯ amber overdue · blank otherwise) | 6% |

### Visual discipline

- The red dot in IMP column appears **only** when CP=true AND a linked
  constraint is overdue. That is the only red in the entire activity list.
- The `⚠` in the CP column is **monochrome** slate-500 (not red — being
  on the critical path is informational, not an alarm).
- Hover row → `bg-slate-50`. Click row → opens activity detail drawer
  (see §6).

---

## 4 · Lookahead View

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Lookahead                                                                       │
│ Next 14 days · current revision.                                               │
│                                                                                 │
│ Window  ◉ 14 days   ◯ 7 days   ◯ 21 days     Discipline [ All ▾ ]              │
│ ───────────────────────────────────────────────────────────────────────────     │
│                                                                                 │
│ THIS WEEK · 2026-05-27 → 2026-06-02                                            │
│ ─────────────                                                                  │
│  A0912 · Utility Relocation · STA 145             ⚠ CP · 0d float · ⛬⬤        │
│         Starts Mon 5/22 · Finishes Sun 6/8                                     │
│  A1320 · Storm Phase 3 · STA 220+40               ⚠ CP · 0d float · ⛬⬤        │
│         Starts Thu 5/28 · Finishes Wed 6/18                                    │
│  A0801 · MOT Phase 1 · East Lane                  4d float                     │
│         Starts Mon 5/12 · Finishes Tue 6/2                                     │
│                                                                                 │
│ NEXT WEEK · 2026-06-03 → 2026-06-09                                            │
│ ─────────────                                                                  │
│  A0912 · Utility Relocation · STA 145             ⚠ CP (continues)             │
│  A1318 · Storm Pipe · STA 220 (mainline)          2d float · ⛬                 │
│  A1320 · Storm Phase 3 · STA 220+40               ⚠ CP (continues)             │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

- Mobile-first by default. The lookahead is what a superintendent
  pulls up in the truck.
- Activities group by week.
- Each row carries the same glyph dictionary as the activity list.
- One CP activity with one overdue constraint anywhere on the lookahead
  surfaces a single `⬤` red dot. Nothing else.
- No bar chart. No timeline graphic. Operational rhythm in text form.

---

## 5 · Critical-Path Risk View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Critical-Path Risk                                                          │
│ Where exposure lives now.                                                   │
│                                                                             │
│ Project [ T5860 SR 9 ▾ ]                                                    │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  EXPOSURE TODAY                                                             │
│  ──────                                                                     │
│  Critical-path activities with active constraints · 3                       │
│  Overdue against needed-by · 1 (Storm Phase 3)                              │
│  Days of exposure · 1                                                       │
│                                                                             │
│  ──────                                                                     │
│                                                                             │
│  ⬤  A1320 · Storm Phase 3 · STA 220+40                                      │
│      Float 0d · 0% complete · finish 2026-06-18                             │
│      Constraint: RFI #0040 · CEI · Needed 2026-05-29 · OVERDUE 1 day        │
│                                                                             │
│  ⚠   A0912 · Utility Relocation · STA 145+50 RT                             │
│      Float 0d · 5% complete · finish 2026-06-08                             │
│      Constraint: RFI #0042 · Engineer of Record · Needed 2026-05-30         │
│                                                                             │
│  ⚠   A0815 · Survey Re-check · STA 098+20                                   │
│      Float 0d · not started · finish 2026-05-28                             │
│      Constraint: CEI Hold · Needed 2026-05-31                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Only CP activities with at least one active constraint appear here.
- The single `⬤` red dot appears for the one row that is overdue.
- "Days of exposure" is the single headline number — the formula from
  `RFI_SCHEDULE_LINKAGE_MODEL §7`. No weighted scores. No charts.
- An empty state reads: *"No critical-path exposure right now."*

---

## 6 · Operational Impact View

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Operational Impact                                                           │
│ RFI × Constraint × Activity.                                                 │
│                                                                              │
│ Project [ All in scope ▾ ]   Linked to [ Active constraint ▾ ]               │
│ ──────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ⬤  RFI #0040 · CC5744 OXFORD · Drainage · STA 220+40                        │
│      ↳ Constraint · RFI Pending · OVERDUE · CEI                              │
│        ↳ Activity · A1320 · Storm Phase 3 · CRITICAL · 0d float              │
│      Submitted 2026-05-22 · Response due 2026-05-29                          │
│                                                                              │
│  ⚠   RFI #0042 · T5860 SR 9 · Utilities · STA 145+50 RT                      │
│      ↳ Constraint · RFI Pending · Active · Engineer of Record                │
│        ↳ Activity · A0912 · Utility Relocation · CRITICAL · 0d float         │
│      Submitted 2026-05-23 · Response due 2026-05-30                          │
│                                                                              │
│  ⚠   RFI #0038 · T5860 SR 9 · MOT · STA 010+00                               │
│      ↳ Constraint · MOT Restriction · Active · DOT                           │
│        ↳ Activity · A0801 · MOT Phase 1 · 4d float                           │
│      Submitted 2026-05-20 · Response due 2026-05-30                          │
│                                                                              │
│ ──────────────────────────────────────────────────────────────────────────── │
│ 3 active impacts · 1 overdue (CP)                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

- Tree view: RFI → Constraint → Activity. Three levels max.
- Indentation tells the eye the linkage direction without arrows.
- Sortable by overdue first, then by float ascending, then by
  submitted date.

---

## 7 · Activity Detail Drawer

```
┌──────────────────────────────────────────────────┐
│  ACTIVITY                            [ ✕ Close ] │
│  ─────────                                       │
│                                                  │
│  ⚠  A1320 · Storm Phase 3                        │
│  CC5744 OXFORD                                   │
│                                                  │
│  WBS               1.3.20 · Storm Phase          │
│  EARLY START       2026-05-28                    │
│  EARLY FINISH      2026-06-18                    │
│  REMAINING DUR     22 days                       │
│  TOTAL FLOAT       0d  (CRITICAL)                │
│  STATUS            Not started · 0%              │
│                                                  │
│  RELATIONSHIPS                                   │
│   Pred: A1318 (FS)                               │
│   Succ: A1322 (FS)                               │
│                                                  │
│  LINKED CONSTRAINTS  (1)                         │
│   ⬤ RFI #0040 · OVERDUE 1 day · CEI         →    │
│                                                  │
│  LINKED RFIs  (1)                                │
│   ⬤ #0040 · Submitted 2026-05-22            →    │
│                                                  │
│  RECENT REVISION ACTIVITY                        │
│   Rev 14 (2026-05-22) · finish moved +3 days     │
│   Rev 13 (2026-05-08) · added · CP entry         │
│                                                  │
└──────────────────────────────────────────────────┘
```

No editing here. The drawer is read-only. P6 owns the math.

---

## 8 · What's Intentionally NOT Here

- ❌ Default Gantt view — never as the landing
- ❌ Resource histograms — out of scope for V.x
- ❌ Cost loading / earned value — out of scope
- ❌ User-defined column sets — one canonical view per surface
- ❌ Editable activity rows — P6 is the source of truth
- ❌ "Predict the slip" AI suggestions — never
- ❌ Inline activity comments — comments live on the linked RFI/constraint

---

## 9 · Loudness Probe Targets per Schedule Surface

| Surface | Hue families | Badge density | Calmness | Direction |
|---|---|---|---|---|
| Schedule Hub | 2 | ≤ 5 | ≥ 74 | stable |
| Activity List | 3 | ≤ 15 | ≥ 72 | stable |
| Lookahead | 2 | ≤ 8 | ≥ 74 | stable |
| Critical-Path Risk | 3 | ≤ 10 | ≥ 72 | stable |
| Operational Impact | 3 | ≤ 12 | ≥ 72 | stable |

The whole subsystem stays within the existing platform calmness band.

---

## 10 · Operator Sign-off Items

- [ ] Five views (no Gantt default) is the right scope.
- [ ] "Days of exposure" as the single headline number is sufficient.
- [ ] Tree view on Operational Impact reads cleanly.
- [ ] Activity detail drawer is read-only as expected.
- [ ] Schedule hub feels like a calm entry, not a dashboard.
- [ ] No data visualization (charts, histograms, Gantts) is missed.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Locked for V.3 (shell), V.4 (import), V.5 (linkage), V.6 (impact).
