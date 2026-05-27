# RFI ↔ Schedule Linkage Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> How RFIs connect to schedule activities and constraints, and how the
> two subsystems surface operational risk. Doctrine-locked.

---

## 1 · Why the Linkage Matters

Most of the dispute value in DOT / FAA contracts comes from
**proving** that a delay was caused by an unresolved clarification —
i.e., the RFI was outstanding while a critical-path activity was
waiting. Without the linkage, claims rest on memory and reconstructed
timelines. With the linkage, the claim is a query.

This is **the MASCI advantage**: native operational lineage from RFI →
constraint → activity → impact → resolution.

---

## 2 · The Three-Object Triangle

```
                 ┌──────────────┐
                 │     RFI      │
                 │ (field-first,│
                 │  PM-owned)   │
                 └──────┬───────┘
                        │   one-to-one (optional) or
                        │   one-to-many in revisions
                        ▼
                 ┌──────────────┐         many-to-many
                 │  Constraint  │◄──────────────────────┐
                 │ (operational │                       │
                 │  bridge)     │                       │
                 └──────┬───────┘                       │
                        │ many-to-many                  │
                        ▼                               │
                 ┌──────────────┐                       │
                 │   Activity   │───────────────────────┘
                 │ (P6 task_id) │
                 └──────────────┘
```

- An RFI **may** create one or more constraints (when PM marks "impacts schedule").
- A constraint **may** link to one or more activities.
- A constraint **may** exist without an RFI (e.g., utility conflict, weather hold).
- An RFI **may** exist without a constraint (routine clarification).

The triangle is the **only** linkage model. No direct `rfi → activity`
edges. Activities and RFIs never reference each other directly. The
constraint is always in the middle. This keeps the data model honest
and the query surface predictable.

---

## 3 · Cardinality Doctrine

| Edge | Cardinality | Required? |
|---|---|---|
| RFI → Constraint | 0..N (PM-driven) | optional |
| Constraint → RFI | 0..1 (a constraint may originate from one RFI) | optional |
| Constraint → Activity | 1..N (every constraint touches at least one activity) | required |
| Activity → Constraint | 0..N | implicit (reverse lookup) |
| RFI → Daily Report | 0..N (evidence) | optional |
| RFI → Photo | 0..N (evidence) | optional |
| Constraint → Daily Report | 0..N (evidence) | optional |
| Constraint → Photo | 0..N (evidence) | optional |

Required cardinality is enforced at write time. Optional links are
validated at read time and surface as "missing evidence" hints in the
PM dashboard.

---

## 4 · "Impacts Schedule" Toggle

On the RFI draft / review form, the PM sees a single toggle:

> **Schedule impact** — *(if yes, links a constraint to one or more activities below.)*

When ON:
1. Activity picker becomes required (at least one).
2. Constraint type defaults to `rfi_pending` (override-able to other types).
3. Needed-by date prefills to the RFI's `response_due_date` (override-able).
4. Submitting the RFI also activates the proposed constraint.

When OFF:
1. No constraint is created.
2. RFI submits normally.
3. PM can flip it ON later via a revision (audited).

This toggle is the **single decision point** between routine RFIs and
schedule-impacting RFIs. It is the operational hinge of the entire
subsystem.

---

## 5 · Activity Picker UX

The activity picker must:

- Default to the current active schedule revision.
- Allow filtering by: WBS · discipline · station range · critical
  flag · this-week / next-2-weeks lookahead.
- Show: activity id · short name · start · finish · float · CP flag.
- Preserve selection through draft saves.
- Multi-select with a chip-style summary.

On submission, the snapshot stores the resolved `task_id` values. If a
later schedule revision removes one of those activities, the link
surfaces as orphaned (see `SCHEDULE_CONSTRAINT_MODEL §5`).

---

## 6 · Reverse Lookup: "What blocks this activity?"

The schedule activity detail panel shows:

- All constraints linked to the activity (current revision).
- For each constraint: type · status · needed-by · linked RFI (if any) ·
  responsible party.
- The total **exposure days** computed from the constraint set
  (sum of overdue days across all active constraints linked to the
  activity, capped at activity float).

This reverse view answers: *"Why is this activity blocked, who owes
the resolution, when do we need it?"* — in one tap.

---

## 7 · Critical-Path Exposure Calculation

For each project, the system computes nightly (and on-demand):

```
critical_path_exposure_days =
    sum over all (active_constraints linked to CP activities) of
        max(0, days_overdue_against_needed_by)
    capped at the smallest float of any linked CP activity
```

This single number is the **headline exposure metric**. It surfaces
on:

- PM dashboard
- Governance Health Chip (when the project carries CP exposure)
- Executive read-only view
- The schedule subsystem's Critical-Path Risk View

No flashy "exposure score" with arbitrary weighting. Just days
overdue against CP activities. Operationally legible.

---

## 8 · Schedule Snapshot Discipline on RFI Submission

When an RFI with `schedule impact = yes` is submitted:

- A **snapshot** of the linked activities (id, name, start, finish,
  float, CP flag) is written into the RFI's submitted revision body.
- This snapshot **never updates**. It is the "what the schedule looked
  like when this RFI was raised" record.
- The live linkage continues to follow active-revision rebinding.
- Both views are available in the RFI detail panel: "as submitted"
  and "current".

This is doctrine because claims hinge on the schedule state at the
moment the RFI was raised — not on the current state.

---

## 9 · Visual Linkage Doctrine

- RFI row in any list shows a small slate icon when it has a linked
  constraint.
- Constraint row shows a small RFI icon when it has a linked RFI.
- Activity row shows a small slate dot when it has active linked
  constraints; the dot turns into a **red** dot (the ONE allowed red
  signal in this subsystem) when the activity is on the critical path
  AND has an overdue constraint.

No badges. No counters in the row. The icon/dot is the entire
vocabulary. Detail comes from the panel.

---

## 10 · Backend Surface (V.5 implementation note)

Endpoints expected for V.5:

```
GET /api/rfi/{id}/constraints                  → constraints linked to an RFI
GET /api/rfi/{id}/activities                   → activities linked through constraints
GET /api/constraints/{id}                      → constraint detail (with embedded links)
GET /api/schedule/{project}/activity/{id}/constraints
                                               → constraints linked to an activity
GET /api/schedule/{project}/critical-path-exposure
                                               → headline number + breakdown
```

All read endpoints follow the cross-portal read pattern (any portal
token in scope). Writes are PM/Admin only.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Linkage lands in V.5 after both RFI MVP (V.1) and Schedule shell (V.3) are operator-blessed.
