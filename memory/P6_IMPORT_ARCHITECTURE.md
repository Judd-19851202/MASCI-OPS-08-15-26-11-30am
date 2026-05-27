# P6 Import Architecture
## Phase V.0 · Architecture & Governance · 2026-05-27

> Read-only `.xer` import flow for MASCI Ops. No live Oracle API. No
> two-way sync. Doctrine-locked.

---

## 1 · Format Roadmap

| Format | Phase | Notes |
|---|---|---|
| `.xer` (Primavera export) | **V.4 MVP** | Tab-delimited, well-documented format. Single source for initial import. |
| Primavera XML | V.5 | Richer fidelity (constraints, calendars). Same flow. |
| MSP XML | V.6 | Microsoft Project users. Lower priority. |
| Oracle Primavera Cloud API | **never** | Out of scope. Operator-confirmed. |
| Two-way sync | **never** | Out of scope. Operator-confirmed. |

---

## 2 · Upload Pipeline

```
PM uploads .xer
        │
        ▼
Frontend chunked upload  ────►  Backend receives file
                                       │
                                       ▼
                            Persist raw file to R2
                            (immutable · key includes sha256)
                                       │
                                       ▼
                            Parse with vendored parser
                            (xerparser / custom · LIVE in V.4)
                                       │
                                       ▼
                            Validation pipeline
                            (see § 4)
                                       │
                              ┌────────┴────────┐
                              │                 │
                          OK passes        Validation fails
                              │                 │
                              ▼                 ▼
                  Generate IMPORT PREVIEW   Audit failure
                  (diff vs current active)  Notify PM
                              │
                              ▼
                  PM reviews preview
                              │
                  ┌───────────┴───────────┐
                  │                       │
              Accept                  Reject
                  │                       │
                  ▼                       ▼
       New active revision         Preserve upload
       Old revision archived       (no activation)
       Audit trail entry           Audit trail entry
```

---

## 3 · Storage Layout

### 3.1 — R2 keys

```
schedules/
  {project_number}/
    raw/
      {sha256}.xer                 # original file · immutable
    revisions/
      rev-001/
        original_filename.xer     # symlink-like reference (metadata)
        diff_against_prior.json   # human-readable diff snapshot
      rev-002/
        ...
    pdfs/
      lookahead_<rev>_<ts>.pdf
      critical_path_<rev>_<ts>.pdf
```

### 3.2 — Mongo collections (NEW for Schedule)

| Collection | Purpose |
|---|---|
| `schedule_imports` | One row per upload (raw upload tracking · always created) |
| `schedules` | One row per **active** project schedule (current view) |
| `schedule_revisions` | One row per accepted revision (immutable) |
| `schedule_activities` | One row per activity per revision |
| `schedule_relationships` | One row per logical relationship |
| `schedule_milestones` | One row per milestone |
| `schedule_calendars` | One row per calendar |
| `schedule_constraints_native` | P6-native date/logic constraints (NOT operational constraints) |
| `schedule_audit` | Append-only audit trail |

---

## 4 · Validation Pipeline

The validator runs before activation. It MUST flag:

| Check | Severity | Behavior |
|---|---|---|
| File parses as `.xer` | hard fail | reject upload |
| File contains at least one `PROJECT` row | hard fail | reject upload |
| Project ID matches an active MASCI project (mapped) | warn | PM can override with explicit mapping |
| Data date present and parseable | hard fail | reject upload |
| Data date newer than current active's data date | warn | "schedule moves backward in time — confirm" |
| Activity count delta > 25% vs prior | warn | "large activity-count change · confirm" |
| Critical-path length delta > 20% vs prior | warn | "critical-path shifted significantly · confirm" |
| Any activity references a missing calendar | warn | "missing calendar reference · activity will use default" |
| Encoding is UTF-8 or Windows-1252 | hard fail if neither | reject upload |
| File size > 100 MB | warn | "large file · upload will be chunked" |
| File size > 500 MB | hard fail | reject upload |

Validation results go into `schedule_imports.validation_report` and
are surfaced in the preview UI.

---

## 5 · Diff Engine

When generating the import preview, the system computes:

```json
{
  "activity_count": { "before": 1342, "after": 1356, "delta": +14 },
  "milestone_count": { "before": 27, "after": 27, "delta": 0 },
  "critical_path_count": { "before": 89, "after": 96, "delta": +7 },
  "data_date": { "before": "2026-04-15", "after": "2026-05-15", "delta_days": 30 },
  "new_activities": [{ "id": "...", "name": "..." }, ...],
  "removed_activities": [{ "id": "...", "name": "..." }, ...],
  "schedule_shift": { "earliest_finish_delta_days": +3 },
  "warnings": [...]
}
```

The PM sees this as a calm three-section panel:
1. Summary (counts, deltas)
2. Top changes (newly critical activities, removed activities)
3. Warnings (if any)

No giant Gantt diff. No flashing. Operationally legible.

---

## 6 · Active Revision Doctrine

Only **one** revision is active per project at a time. Activation is:

1. Atomic: a single Mongo transaction sets the prior `active=false`
   and the new `active=true`.
2. Audited: `schedule_audit` records `actor`, `prior_revision_id`,
   `new_revision_id`, `timestamp`, `ip`, `notes`.
3. Reversible: PM can re-activate a prior revision (with the same
   audit discipline) if a bad import slipped through.
4. Linked: existing RFI ↔ activity links **rebind** to the new
   revision via stable activity IDs (P6 `task_id`). When a referenced
   activity is removed in the new revision, the RFI link surfaces as
   "activity removed in revision N — reattach" in the operational
   impact view.

---

## 7 · Parser Strategy

V.4 will use **a vendored Python parser** (likely `xerparser` from PyPI
or an equivalent) wrapped behind a thin internal interface
`backend/services/schedule_parser.py`. The interface:

```python
class ScheduleParser:
    def parse(file_bytes: bytes) -> ParsedSchedule
    def diff(prior: ParsedSchedule, new: ParsedSchedule) -> ScheduleDiff
    def validate(parsed: ParsedSchedule, project_meta: dict) -> ValidationReport
```

Rationale: wrapping the parser behind our own interface lets us swap
implementations (XML, MSP XML, custom) without disturbing the upload /
preview / activation flow.

---

## 8 · Permission Doctrine for Imports

| Operation | Allowed |
|---|---|
| Upload `.xer` | PM (in-scope project) · Admin |
| Preview import | PM (in-scope) · Admin |
| Accept activation | PM (in-scope) · Admin |
| Reject import | PM (in-scope) · Admin |
| Re-activate prior revision | PM (in-scope) · Admin |
| Delete raw upload | **never** (preserved for audit) |
| External party (CEI / Owner) | view active schedule via tokenized link (V.6+) only · no upload |

---

## 9 · Field-Side Effects (none)

Importing a schedule **does not** notify the field automatically.
Schedule changes are a PM-driven operational event. Crews learn about
schedule shifts through the existing daily-report / Basecamp / phone
discipline. The Schedule Intelligence dashboard surfaces the shift the
next time a PM or Superintendent opens it.

Why: notification hell is doctrine-forbidden. Importing a schedule
update should not produce 60 push notifications.

---

## 10 · Performance Envelope

- Parse: ≤ 30 seconds for a 50 MB `.xer` on the existing pod size.
- Validation: ≤ 5 seconds.
- Diff: ≤ 10 seconds.
- Active activation: ≤ 2 seconds (Mongo transaction).
- UI render of active activity list: ≤ 1.5 seconds for 5k activities
  (paginated).

If we cannot hit these envelopes in V.4 prototype, parser is
backgrounded with a status polling pattern.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Parser lands in V.4. Upload UI lands in V.3.
