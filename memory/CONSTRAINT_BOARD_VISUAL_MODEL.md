# Constraint Board · Visual Model
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> Operational blocker board. Not a legal document index. Not a
> ticketing dashboard. Doctrine-locked.

---

## 1 · What This Surface IS

An at-a-glance answer to: **"What is blocking forward progress on
this project right now, and who owes the resolution?"**

It is **not**: a Kanban board for tasks · a generic issue tracker · a
risk register with weighting · a Gantt overlay.

---

## 2 · Desktop Wireframe

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ PROJECT MANAGER · CHRIS WRIGHT  ·  GOVERNANCE STABLE  ░                        │
│                                                                                │
│ Constraints                                                                    │
│ Operational blockers. Linked to RFIs and activities.                          │
│                                                                                │
│ Project [ T5860 SR 9 ▾ ]   Status [ Active ▾ ]   Type [ All ▾ ]                │
│ ────────────────────────────────────────────────────────────────────────────── │
│                                                                                │
│  RESPONSIBLE · CEI                                                             │
│  ─────────────                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  ⬤ RFI Pending · 0040 · CC5744 OXFORD                                    │ │
│  │  Drainage · STA 220+40 · CP impact                                       │ │
│  │  Needed by 2026-05-29 · OVERDUE 1 day                                    │ │
│  │  Linked activity: A1320 · Storm Phase 3 (CRITICAL)                       │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  ◯ CEI Hold · 0033 · T5860 SR 9                                          │ │
│  │  Survey · STA 098+20                                                     │ │
│  │  Needed by 2026-05-31                                                    │ │
│  │  Linked activities: A0814, A0815                                         │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  RESPONSIBLE · ENGINEER OF RECORD                                              │
│  ─────────────                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  ⬤ RFI Pending · 0042 · T5860 SR 9                                       │ │
│  │  Utilities · STA 145+50 RT · CP impact                                   │ │
│  │  Needed by 2026-05-30                                                    │ │
│  │  Linked activity: A0912 · Utility Relocation Phase 2 (CRITICAL)          │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  RESPONSIBLE · UTILITY (FPL)                                                   │
│  ─────────────                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  ◯ Utility Conflict · CC5744 OXFORD                                      │ │
│  │  Drainage · STA 220+10                                                   │ │
│  │  Needed by 2026-06-04                                                    │ │
│  │  Linked activity: A1318                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  RESPONSIBLE · INTERNAL                                                        │
│  ─────────────                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  ⬜ Material Lead · I-95 RESURFACE                                       │ │
│  │  MOT · Friction course mix                                               │ │
│  │  Needed by 2026-06-14                                                    │ │
│  │  Linked activity: A2310                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│ ────────────────────────────────────────────────────────────────────────────── │
│ 5 active · 1 overdue (CP) · 0 voided                                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3 · Grouping Doctrine

The board groups by **responsible party**, not by type, not by
severity, not by date. Why:

- The operational question is *"who owes the resolution"*.
- Grouping by responsible party gives the PM a direct call list.
- Severity is encoded in the single glyph per card.
- Date is encoded in the line under the title.

Grouping options (single dropdown, no multi-axis chaos):

- **Responsible party** (default)
- Constraint type
- Linked project (when scope = all PM projects)

That's it. Three views. Not seventeen.

---

## 4 · Card Anatomy

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ⬤  RFI Pending · 0040 · CC5744 OXFORD                                   │
│  Drainage · STA 220+40 · CP impact                                       │
│  Needed by 2026-05-29 · OVERDUE 1 day                                    │
│  Linked activity: A1320 · Storm Phase 3 (CRITICAL)                       │
└──────────────────────────────────────────────────────────────────────────┘
```

| Line | Meaning |
|---|---|
| Title row | Severity glyph · constraint type · linked RFI # (when present) · project label |
| Context row | Discipline · station · impact summary |
| Time row | Needed-by date · aging status (red text only when overdue) |
| Linkage row | Linked activity ID + name + CP flag (when CP) |

Clicking the card opens the constraint detail panel in a right
drawer. No new full-page navigation needed for routine ops.

---

## 5 · Severity Glyph (reused from RFI list)

| Glyph | Meaning |
|---|---|
| `⬤` (red-700) | Critical-path impact OR safety / compliance / stoppage |
| `◯` (amber-600) | Overdue, not CP — OR — active, not yet overdue, near-critical (float < 5d) |
| `⬜` (slate-500) | Routine active |

One glyph. One color. Per card. No badges, no extra pills.

---

## 6 · Filters

Three filters only:

```
Project [ T5860 SR 9 ▾ ]   Status [ Active ▾ ]   Type [ All ▾ ]
```

Status options:

- **Active** (default · proposed + active)
- Resolved
- Voided
- All

Type options follow the 14-type enum from `SCHEDULE_CONSTRAINT_MODEL §2`.

No date range filter, no search. The board exists to be skimmed in
≤ 10 seconds, not searched.

---

## 7 · The Footer Tally

```
5 active · 1 overdue (CP) · 0 voided
```

- One line.
- Plain text · slate-500 small caps.
- The "1 overdue (CP)" segment renders red-700 only when count > 0.
- When all three counts are zero, the line reads: *"No active
  constraints."*

---

## 8 · Constraint Detail Drawer (right side · desktop)

When a card is tapped:

```
┌──────────────────────────────────────────────────┐
│  CONSTRAINT                          [ ✕ Close ] │
│  ─────────                                       │
│                                                  │
│  ⬤  RFI Pending                                  │
│  0040 · CC5744 OXFORD                            │
│                                                  │
│  TYPE              RFI Pending                   │
│  STATUS            Active · Overdue 1 day        │
│  RESPONSIBLE       CEI (Sue Patton)              │
│  NEEDED BY         2026-05-29                    │
│  CREATED           2026-05-22 by Chris Wright    │
│                                                  │
│  LINKED RFI        #0040 (open)            →     │
│  LINKED ACTIVITY   A1320 · Storm Phase 3   →     │
│                     Critical-path · 6 days float │
│                                                  │
│  EVIDENCE                                        │
│   2 photos · 1 daily report · 0 inspections      │
│                                                  │
│  IMPACT ASSESSMENT                               │
│   Sub waiting on conduit-routing answer.         │
│   Crew demobilized 2026-05-23. Re-mob requires   │
│   48h notice.                                    │
│                                                  │
│  AUDIT TRAIL (last 3)                            │
│   2026-05-29 PM noted overdue · phone call to CEI│
│   2026-05-22 PM confirmed active · linked A1320  │
│   2026-05-22 SI raised · attached photos         │
│                                                  │
│  [   Resolve   ]   [   Void with reason   ]      │
└──────────────────────────────────────────────────┘
```

- Drawer takes 38% of the viewport width on desktop · 100% on mobile.
- Two primary actions: **Resolve** and **Void with reason**.
- Both require PM confirmation. Void requires Admin co-sign (dual control).

---

## 9 · Mobile (≤ 1023px)

```
┌──────────────────────────────────────┐
│  Constraints                         │
│  Operational blockers.               │
│  ──────                              │
│  [ T5860 SR 9 ▾ ]  [ Active ▾ ]      │
│                                      │
│  CEI                                 │
│  ──────                              │
│  ┌────────────────────────────────┐  │
│  │ ⬤ RFI Pending · 0040           │  │
│  │ CC5744 OXFORD · STA 220+40     │  │
│  │ OVERDUE 1 day                   │  │
│  │ A1320 · Storm Phase 3 (CRIT)   │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ ◯ CEI Hold · 0033              │  │
│  │ T5860 SR 9 · STA 098+20        │  │
│  │ Due 2026-05-31                  │  │
│  │ A0814, A0815                    │  │
│  └────────────────────────────────┘  │
│                                      │
│  ENGINEER OF RECORD                  │
│  ──────                              │
│  ┌────────────────────────────────┐  │
│  │ ⬤ RFI Pending · 0042           │  │
│  │ T5860 SR 9 · STA 145+50 RT      │  │
│  │ Due 2026-05-30                  │  │
│  │ A0912 · Utility Reloc (CRIT)    │  │
│  └────────────────────────────────┘  │
│                                      │
│  …                                   │
└──────────────────────────────────────┘
```

Same group-by-responsible-party hierarchy. Each card collapses to 4
lines on mobile.

---

## 10 · Loudness Probe Targets

| Metric | Target |
|---|---|
| Hue families | ≤ 3 (slate + amber + red · functional only) |
| Badge density | ≤ 12 |
| Escalation noise | ≤ 6 elements |
| Calmness score | ≥ 72 |

The board is information-dense but visually quiet. Doctrine intact.

---

## 11 · What's Intentionally NOT Here

- ❌ Kanban columns by status — we group by responsible party
- ❌ Drag-to-reorder — operational order is computed, not user-defined
- ❌ Priority weighting (low/medium/high color matrix) — single glyph only
- ❌ Aging charts / trend lines — the board is a skim, not a dashboard
- ❌ Bulk operations — every constraint resolves individually
- ❌ Notifications — the daily PM digest summarizes; the board is on-demand

---

## 12 · Operator Sign-off Items

- [ ] Grouping by responsible party reads correctly to a PM.
- [ ] Single-glyph severity vocabulary is sufficient.
- [ ] Card density (4 lines desktop · 4 lines mobile) is operational, not cramped.
- [ ] No third axis (priority weighting) is missed.
- [ ] Detail drawer is the right level of depth.
- [ ] Dual-control void is workable from this surface.

---

## 13 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Locked for V.5 (RFI ↔ Schedule linkage phase).
