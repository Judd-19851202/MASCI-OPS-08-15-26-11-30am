# Field Language Cleanup — Certification

_Phase V.2 · Daily Report Field-Logic Refinement · Fix 4 of 4 · 2026-05-29._

## 1 · Goal

Bring the user-facing Daily Report copy into alignment with
construction vocabulary, without renaming backend models /
enums / APIs.

> **Operator directive (verbatim):** _"UI language must be
> field-friendly. Backend terminology may remain ConstraintRow /
> ConstraintType."_

## 2 · Strings changed (all in `NewDailyReport.jsx`)

| # | Surface | Before | After |
|---|---|---|---|
| 1 | Section 03 YES/NO label | "Schedule Delays Today?" | **"Delays / Extra Work Today?"** |
| 2 | Delays card title | "Issues / Delays · Structured" | **"Delays / Extra Work"** (set in the prior closure pass · re-affirmed here) |
| 3 | Empty-state pill | "No issues today" | **"No delays today"** (set prior · re-affirmed) |
| 4 | Required-state pill (new) | _(none — no required state existed)_ | **"Add at least one delay (required)"** (amber) |
| 5 | Helper line above chips | "Tap a chip to log a constraint…" | **"Tap a delay cause to document impacts to today's work. Signal only — never creates an RFI or schedule entry."** (set prior · re-affirmed) |
| 6 | Row label inside repeat block | "Constraint N" | **"Delay N"** (set prior · re-affirmed) |
| 7 | Add-row button | "ADD CONSTRAINT" | **"ADD DELAY"** (set prior · re-affirmed) |
| 8 | Delay row "hours" field label | "Hours Impact" | **"Lost Hours"** |
| 9 | Submit error toast | _(none)_ | **"Add at least one Delay / Extra Work row (Type + Notes) before submitting"** |
| 10 | Subcontractor foreman label | "Foreman / Lead" | **"Subcontractor Foreman / Lead"** |

## 3 · Strings preserved (internal terminology)

| Surface | Preserved value | Rationale |
|---|---|---|
| Pydantic model | `ConstraintRow` | platform-internal · referenced across analytics / heuristics / probes |
| Pydantic enum | `ConstraintType` | platform-internal · advisory derivation engine |
| API field | `data.constraints[]` (POST + GET) | wire-format stability · historical reports |
| API field | `data.schedule_delays` (Yes/No) | wire-format stability · advisory aggregator key |
| API field | `data.schedule_delays_notes` | narrative · used by legacy reports + audit footer |
| Advisory flags | `may_require_rfi`, `may_affect_schedule` | server-derived intelligence · unchanged |
| `data-testid="constraint-chip-*"` | unchanged | telemetry · drift probes · pw_suite stability |
| `data-testid="dr-constraints*"` | unchanged | telemetry · drift probes |
| `data-testid="constraint-row-*"` | unchanged | telemetry · drift probes |
| New endpoint name | `GET /api/field-leadership-roster` | mirrors existing `/api/employees` convention (no separate "picker" namespace) |

## 4 · Chip labels — held as-is per operator directive

| Label kept | Notes |
|---|---|
| Weather | _"Weather"_ |
| Utility | _"Utility"_ |
| Survey | _"Survey"_ |
| Material | _"Material"_ |
| Equipment | _"Equipment"_ |
| Trucking | _"Trucking"_ |
| MOT | _"MOT"_ |
| CEI / Inspection | _"CEI / Inspection"_ |
| Owner / Engineer | _"Owner / Engineer"_ |
| Safety | _"Safety"_ |
| Other | _"Other"_ |

Operator directive (verbatim): _"Chip labels: Leave chip labels
as-is for now."_ Any future rename surfaces in
`SUPERINTENDENT_VALIDATION_REPORT.md §4 ("What terminology
confused users")`.

## 5 · Anti-pattern audit (forbidden strings)

The following phrases must NOT appear on user-facing surfaces of
the Daily Report:

| Forbidden | Rationale |
|---|---|
| "Constraint" (UI) | Backend-only terminology |
| "Structured Issues" | Software jargon |
| "Schedule Delays" (label) | Software jargon — backend field name `schedule_delays` is permitted |
| "Constraint analytics" / "Constraint heuristics" | Backend-only |

Today's verification confirms none of the four phrases appear on
the `/daily/new` rendered DOM.

## 6 · Verification

| Probe | Result |
|---|---|
| DOM scan for forbidden UI strings | 🟢 0 hits |
| DOM scan for new strings (§2) | 🟢 all present at expected surfaces |
| Backend regression (89/89) | 🟢 |
| ESLint on `NewDailyReport.jsx`, `FlUserCombo.jsx` | 🟢 |
| `data-testid` selectors unchanged | 🟢 |

## 7 · Stop condition

🛑 No further user-facing copy changes. Chip-label rewrites,
help-tip rewrites, and PM-facing copy refinements deferred until
the Superintendent Validation Review surfaces real-world
terminology confusion items.

---

_End of FIELD_LANGUAGE_CLEANUP_CERTIFICATION.md._
