# Schedule System Doctrine
## Phase V.0 · Architecture & Governance · 2026-05-27

> Authoritative doctrine for the MASCI Ops Schedule Intelligence layer.
> P6 stays canonical. MASCI is the operational intelligence layer on
> top. No CPM rebuild. Doctrine-locked.

---

## 1 · Position Statement

| | Primavera P6 | MASCI Ops Schedule Intelligence |
|---|---|---|
| What it is | The official CPM scheduling tool. The contract baseline. The math engine. | The operational visibility, exposure tracking, and field-readable view of the P6 schedule. |
| Owns CPM math | ✅ | ❌ |
| Edits logic / relationships / durations | ✅ | ❌ |
| Maintains baseline | ✅ | ❌ (read-only reference) |
| Imports from `.xer` / XML | — (source) | ✅ |
| Field-readable activity / constraint surfaces | ❌ (not optimized) | ✅ |
| Links to RFIs, daily reports, photos, constraints | ❌ | ✅ |
| Surfaces operational risk dashboards | ❌ | ✅ |
| Two-way sync with Oracle | — | ❌ (never · scope-locked) |

**P6 is canonical. MASCI Ops is operational intelligence.** Any feature
that would blur this line is rejected by doctrine.

---

## 2 · Why This Split

- DOT, FAA, and Owner contracts already specify P6 as the scheduling
  tool. Re-implementing CPM math is wasted engineering and an
  unbounded validation problem.
- P6's math is reliable; the user experience is not field-friendly.
  Field operators cannot consume the P6 native view at 6:15am on a
  phone in the dirt.
- The MASCI advantage is **operational intelligence**: tying the
  schedule to RFIs, daily reports, constraints, photos, and exposure.
  That linkage is where claim defensibility and operational decisions live.

---

## 3 · Scope (Phase V · architecture only)

In scope for V.3 → V.6:

- `.xer` upload + parse + validate + activate workflow.
- XML / MSP-XML import (after `.xer` MVP).
- Activity list view, lookahead view, constraint view, critical-path
  risk view, operational-impact view.
- Constraint model (this doc + `SCHEDULE_CONSTRAINT_MODEL.md`).
- RFI ↔ schedule linkage (`RFI_SCHEDULE_LINKAGE_MODEL.md`).
- Field-readable PDF lookahead.
- Schedule revision history.

Out of scope (and explicitly forbidden in V.0):

- CPM engine implementation.
- Live Oracle Primavera Cloud API integration.
- Two-way sync with P6 (push back schedule edits).
- Resource leveling.
- Cost loading / earned value (deferred to future phase).
- Gantt chart "killer feature" UI (V.5+ if at all, never as a v.1
  hero).

---

## 4 · Configurable P6 Link Doctrine

Every PM portal page in scope carries a configurable **"Open Primavera P6"**
link styled identically to the existing Basecamp / OnStation links.
Rules:

- Link URL is per-project, configurable in project meta.
- Default is blank (no link) until PM sets it.
- Falls back gracefully when blank: link is not rendered, no error.
- Never hardcoded.

This honours the existing pattern (Basecamp is per-org, OnStation is
per-project, neither is hardcoded).

---

## 5 · Field-First Schedule Discipline

The schedule UI must remain field-readable. That means:

- Mobile-first by default. Desktop is a denser view, not the default.
- Activity rows show: ID · short name · start · finish · float ·
  critical flag. Anything else opens a detail sheet.
- Lookahead defaults to the **next 14 days**. Operators rarely need
  the entire schedule on a phone.
- Filters favor operational questions: "what's critical this week",
  "what's blocked by an RFI", "what's overdue".
- No infinite-scroll giant Gantt. The Gantt view (when it lands)
  paginates by 4-week windows.

---

## 6 · Doctrine Inheritance

The Schedule subsystem inherits **the same governance contracts** as
RFI:

- Operational Calmness Doctrine
- Coaching / Subline Standard (≤ 14 words)
- Visual Loudness Doctrine
- Escalation Hierarchy (critical-path stripe is the ONE red signal)
- Mobile Doctrine
- Cross-Portal Continuity
- Governance Health instrumentation (chip surfaces schedule drift too)
- Doctrine Trendline participation
- Auto-deploy checkpoint participation

Every new schedule screen registers in the visual doctrine baseline.

---

## 7 · Storage Doctrine (preview of `SCHEDULE_BACKUP_RETENTION_MODEL.md`)

- Mongo: parsed schedule data, revision metadata, constraint links,
  audit trail.
- R2: original `.xer` / XML files (immutable), generated PDFs.

Schedule data is read-heavy. Indexes optimize for:
- `project_number + active=true` (current schedule lookup)
- `activity_id + project_number` (joins from RFIs and constraints)
- `critical = true + project_number` (CP risk view)
- `late_start_date` (lookahead)

---

## 8 · Revision Discipline

A new `.xer` upload **does not** automatically replace the active
schedule. The flow is:

1. PM uploads `.xer`.
2. System parses it, computes a diff against the current active
   schedule (activity-count, milestone-count, critical-path-length,
   data-date change, new activities, removed activities).
3. Diff is presented to the PM.
4. PM accepts → new revision becomes active. Prior revision archived
   (still queryable).
5. PM rejects → upload is preserved in R2 but not activated. Audited.

No silent schedule changes. Schedule swaps are operationally
significant — they get explicit approval.

---

## 9 · Schedule Exposure Doctrine

The Schedule Intelligence layer surfaces three kinds of exposure:

1. **Critical-path exposure** — activity is on the CP and has an
   active RFI or constraint that could delay it.
2. **Float-erosion exposure** — total float drops below a threshold
   (default 10 days, project-configurable) and there is an active
   constraint or RFI.
3. **Aging exposure** — an RFI tied to an in-window activity has been
   pending external response longer than the response window.

Exposures surface in the operational-impact view, the chip, the PM
dashboard. No flashing, no red unless the exposure is real.

---

## 10 · External Schedule Access (deferred)

Owners and CEI sometimes want read access to the lookahead. This is
**deferred to V.6**:

- Initially the lookahead is internal-only.
- External access lands via the same tokenized pattern as RFI external
  access — but with stricter permissions (`view_lookahead` only · no
  download of `.xer`).

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** P6 import lands in V.4 only after the V.3 shell + external P6 link ship cleanly.
