# Operational Adoption Protection Plan

**Date:** 2026-05-24
**Purpose:** Define the **guardrails** that prevent Phase 5C compression
from accidentally breaking governance, accountability, lifecycle continuity,
or compliance.
**Audience:** the future implementer of any compression item from
`PHASE5C_WORKFLOW_COMPRESSION_PLAN.md`.

---

## The non-negotiable: 100% data fidelity

Every field that exists in the schema today must still be **submittable**
after compression. Compression hides fields visually; it never deletes them.

**Test before any compression PR merges:**
1. Build the form in current state. Submit. Capture the resulting record from `db.daily_reports` / `db.incidents`.
2. Build the form in compressed state. Submit with the same data (using "Show all fields" if Tier 3 fields are populated). Capture the resulting record.
3. **Diff the two records.** Difference set must be empty.

If the diff is non-empty, the compression is broken. Do not merge.

---

## Governance preservation checklist

For Daily Report compression:

- [ ] `db.daily_reports` collection accepts identical payload shape pre/post
- [ ] Required fields enforced server-side (project_number, location, prepared_by, photos≥6) still gate submission
- [ ] Distribution list email fan-out still fires
- [ ] PDF generation includes all 35 + 7 fields
- [ ] PM hub `/api/daily-reports` returns identical projection
- [ ] HR portal `/api/hr/daily-reports` returns identical projection
- [ ] Phase 5 P1 W3 surfaces (`/api/safety/daily-reports`, `/api/dispatch/daily-reports`, `/api/field-leadership/portal/daily-reports`) return identical projections (these are the most recently added — any drift here regresses Phase 5 P1)
- [ ] Auto-email routing fires for safety_incidents_today=Yes
- [ ] Lifecycle status updates fire (e.g., "submitted" → fans out notifications)

For Incident compression:

- [ ] `db.incidents` collection accepts both Tier 1 and Tier 2 payloads (test PATCH path)
- [ ] Required fields enforced server-side per severity tier
- [ ] OSHA recordable detection still works (severity ≥ medical OR osha_recordable=Yes triggers OSHA flag)
- [ ] CAPA creation hook still fires from incident → corrective_action linkage
- [ ] Safety / PM / GC / Owner notification fan-out still fires on Tier 1 submit
- [ ] Incident detail page (existing route) supports Tier 2 PATCH update
- [ ] Audit trail records both Tier 1 create and Tier 2 update events
- [ ] Reverse-linkage to employee_master_id preserved (governance + accountability timeline)
- [ ] Distribution list emails fire on initial Tier 1 submit
- [ ] PDF generation includes Tier 1 + Tier 2 fields when both present
- [ ] Phase 5 P1 W8 `/api/incidents.csv` export still includes all incidents

---

## Backend invariants (do NOT change in Phase 5C)

| Invariant | Why it matters |
|---|---|
| `POST /api/daily-reports` validation logic | Compression is UX-only; backend rules unchanged |
| `POST /api/incidents` schema | Same |
| `PATCH /api/incidents/{id}` schema | Tier 2 uses this — must work as-is |
| `routes/safety.py` fan-out triggers | Notification + auto-email logic unchanged |
| `routes/daily_reports.py` projections | All consumer portals see same data |
| Pydantic model field requirements | If a field is required server-side, it remains required (the compressed UI must still ensure it's submitted, even if hidden) |
| Lifecycle status transitions | Tier 1 → Tier 2 must use existing `status` field semantics, not introduce new ones |

**If you find yourself wanting to change a backend route during Phase 5C compression: STOP. Re-read this document. The change is out of scope.**

---

## Conditional disclosure rules — must be enforced

For Daily Report:

```
Tier 3 ("More fields") collapse state must NOT bypass any required-field validation.

Example: if `subcontractors[]` requires a `company` per row, and the user
populates a sub row then collapses Tier 3, the submit must STILL fail
validation if `company` is empty.

Implementation: validate the form state, not the visible state.
```

For Incident:

```
Tier 1 → Tier 2 transition must NOT lose any data the user entered.

Example: if a user enters person_name in Tier 1, submits, then opens
Tier 2 to add witnesses, the person_name must already be populated in
the Tier 2 view. Do not refetch a partial record.

Implementation: Tier 2 loads the full record from `/api/incidents/{id}`.
```

---

## Severity auto-escalation rules

This is the **single most important guardrail** in incident compression. The rule that prevents under-classification:

```
On change of `severity` field, evaluate:

  IF severity IN {medical, restricted, lost_time, fatality}:
    SHOW Tier 2 block in current page
    MAKE Tier 2 fields required-for-submit
    DISABLE Tier 1-only submit path

  IF severity == fatality:
    AUTO-SET osha_recordable = "Yes" (read-only)
    DISPLAY "OSHA notification required within 8 hours" banner
    DISABLE submit until medical_facility populated
```

This rule must be implemented identically in the UI and backed by server-side validation. **Do not rely on UI alone**.

---

## Notification + accountability preservation

The platform's strongest feature is invisible-but-reliable fan-out. Compression cannot break this. Specifically:

1. **Tier 1 incident submit MUST fire the same fan-out as a current full submit:**
   - Auto-email to safety_contacts
   - Notification to Safety role
   - Notification to PM (via project_number routing)
   - Task creation if severity ≥ medical
2. **Tier 2 update MUST NOT re-fire the fan-out** (avoid notification spam).
3. **Auto-escalation on severity change MUST update the audit log** with the severity change event (not silent).
4. **CAPA linkage:** if severity ≥ medical, the existing CAPA-creation prompt must still surface in Tier 2 follow-up (see `routes/safety.py` for the existing trigger).

---

## "Show all fields" escape hatch (mandatory)

Every compressed form MUST include a "Show all fields" toggle.

**Rationale:** power users (Safety managers, senior PMs) sometimes need the full form expanded. Forcing them through progressive disclosure adds friction for the most engaged users. The escape hatch:

- Is a single button/checkbox at the top of the form: `[ ] Show all fields`
- Remembers state per-user via localStorage (`masci.form.dr.showAll`)
- Does not affect the Tier 1 / Tier 2 model for incidents (tiered submission is structural, not visual)

For Daily Report, "Show all fields" expands the Tier 3 disclosure.
For Incident, "Show all fields" expands Tier 2 in-page (still a Tier 1 submission unless severity auto-escalates).

---

## Coaching alignment (`LifecycleGuide`)

Existing LifecycleGuide instances on both forms must be **updated**, not removed:

**Daily Report LifecycleGuide updates:**
- Add: "Fast path: 12 fields cover most days. Use 'More fields' for subs, equipment, materials."
- Keep: existing accountability + downstream visibility text

**Incident LifecycleGuide updates:**
- Add: "Near Miss: submit in 8 fields, Safety is notified immediately. Add follow-up details within 24 hours from the incident detail page."
- Keep: existing severity + OSHA explainer

LifecycleGuide must remain **short**. If the bullet list grows past 4 items, trim.

---

## Rollback plan per compression item

| Item | Rollback |
|---|---|
| Daily Report Tier 3 collapse | Set `showMoreDefault = true` constant; restores current behavior |
| Daily Report Tier 1 reorder | Revert single JSX block |
| Incident Tier 1 fast entry | Set `tierDefault = 2` constant; restores current 54-field form |
| Incident Tier 2 follow-up flow | Frontend-only; backend already supports PATCH |
| Severity auto-escalation | Disable the side-effect handler; severity becomes display-only |
| "Show all fields" toggle | Remove the toggle button + the localStorage key |

All rollbacks are **localized** — no migration, no data rewrite, no backend touch.

---

## What success looks like (end of Phase 5C if implementation is authorized)

| Indicator | Target |
|---|---|
| Daily Report clean-day completion time | ≤ 90s on phone (currently ~5min) |
| Daily Report tap count | ≤ 10 (currently ~22) |
| Daily Report Tier 3 use rate | < 30% of submissions (most days don't need subs/visitors/materials) |
| Incident Near Miss submit time | ≤ 60s on phone (currently ~5min) |
| Incident Tier 2 follow-up completion rate within 24h | ≥ 80% |
| Severity auto-escalation never bypassed | 100% (UI + server) |
| Zero data-fidelity loss (pre vs post compression) | 0 fields missing on submit-diff |
| Backend route changes | 0 |
| New API surfaces created | 0 |

---

## Closing principle

Compression that drops data quality is **worse than no compression at all**. The whole point of the platform is the data it captures and propagates. Anything that erodes data fidelity in the name of speed is a regression.

**Speed up the supervisor, never the data.**
