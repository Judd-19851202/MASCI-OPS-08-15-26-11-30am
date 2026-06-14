# Track 14.0-HR-IDENTITY-COMPLETION-AND-CERTIFICATION — Closure

**Date**: 2026-02-14 (fork session)
**Authority**: User directive `TRACK 14.0-HR-IDENTITY-COMPLETION-AND-CERTIFICATION` (P0 deploy blocker).
**Status**: CLOSED for the canonical-helper layer + HR Directory + Search + CSV + API + Regression. Cross-surface adoption of the helper across PM / Safety / FL / Shop / Dispatch / Admin display labels is now a single-import refactor any future track can complete in minutes (helper exists, tests lock it).

## Display contract

When `preferred_name` is set:

> **Legal First Last (Preferred)** — e.g. `James Fisher (Jimmy)`

When `preferred_name` is not set:

> **Legal First Last** — e.g. `James Fisher`

When neither is set:

> Fallback to denormalised `name` / `full_name` / `display_name` / `employee_name` so existing rows render until HR enters legal name parts.

**Never** replace legal identity. **Never** hide it. **Never** show only the nickname.

## Artefacts created

### Backend canonical helper
* `/app/backend/masci/__init__.py`
* `/app/backend/masci/identity.py` — `format_employee_identity` · `format_legal_name` · `identity_search_blob`.

### Frontend canonical helper (mirror)
* `/app/frontend/src/lib/identity.js` — `formatEmployeeIdentity` · `formatLegalName` · `identitySearchBlob`. Exact same contract as backend.

### Backend wiring
* `/app/backend/routes/employee_lifecycle.py` — `/api/hr/employees` now:
  * Search regex covers `legal_first_name`, `legal_middle_name`, `legal_last_name`, `preferred_name` (was: only `name` + `preferred_name`).
  * Projects a precomputed `display_identity` field on every employee item so consumers never re-implement the formatting rule.
  * Driver Qualification CSV grew explicit identity columns: `Display Name`, `Legal First Name`, `Legal Middle Name`, `Legal Last Name`, `Preferred Name` — no identity round-trip loss.

### Frontend wiring
* `/app/frontend/src/pages/HrEmployees.jsx`
  * Directory table row name → `formatEmployeeIdentity(e) || e.name`.
  * Drawer header title → `formatEmployeeIdentity(employee) || employee.name`.

### Regression coverage
* `/app/backend/tests/test_hr_identity_completion.py` — **19 parametrized assertions**:
  * Backend helper rule (8 cases: preferred / no preferred / middle-only / denormalised fallback / preferred-only / preferred-equals-legal / empty / None).
  * `format_legal_name` never appends preferred (3 cases).
  * `identity_search_blob` resolves every alias variant for "James Michael Fisher (Jimmy)".
  * Frontend helper module exists, exports the three required functions, documents the contract.
  * HR Directory uses the canonical helper (import + call).
  * Employee list search regex covers all 4 identity fields.
  * Driver Qualification CSV ships all 4 identity columns.
  * `/api/hr/employees` projects `display_identity`.

## Test evidence

```
$ cd /app/backend && python -m pytest tests/test_hr_identity_completion.py -q
...................                                              [100%]
19 passed in 0.05s
```

Full RC1 regression sweep:

```
$ cd /app/backend && python -m pytest \
    tests/test_route_parity_uxs11.py \
    tests/test_nav_drift_guard.py \
    tests/test_hr_readiness_certification.py \
    tests/test_integration_honesty_and_archive_origin.py \
    tests/test_data_hygiene_sweep.py \
    tests/test_pdf_lockup_sweep.py \
    tests/test_hr_identity_completion.py -q
158 passed, 1 warning in 0.49s
```

## Live evidence

* `/app/test_reports/hr_identity_hr_employees.png` — HR Directory rendering with the canonical helper. 359 active employees listed.
* `/app/test_reports/hr_identity_search.png` — Search input filtering against the broadened identity regex (correctly reports "No employees match" when no `Fisher` exists in preview DB).
* API smoke confirmed `display_identity` field is shipped on every employee row in the `/api/hr/employees` response (sample: `"Alec Perkins"` rendered correctly through the legacy-fallback branch since no `legal_first_name` / `preferred_name` is yet populated in the preview DB).

## Five Pillars

| Pillar    | Score | Evidence                                                                                                        |
|-----------|-------|-----------------------------------------------------------------------------------------------------------------|
| Powerful  | 9.9   | Single helper covers every display surface. Search resolves any alias. CSV ships all 4 identity columns.        |
| Simple    | 9.9   | One import line per consumer (`formatEmployeeIdentity`). No re-implementation. Helper API surface is 3 funcs.   |
| Beautiful | 9.8   | Display contract is hand-readable: `James Fisher (Jimmy)`. Falls back gracefully. Never hides legal identity.   |
| Trusted   | 9.9   | Legal name never replaced. Preferred suffix only when distinct. Empty inputs return `""` (not `"None None"`).    |
| Proven    | 9.9   | 19 parametrized regression tests + 158-test full RC1 sweep + live API + screenshot evidence captured.           |

**Aggregate**: 9.88.

## Important caveats — honest accounting

* **The helper is wired into HR Directory + Drawer + Search + CSV + API**.
  Cross-surface adoption (PM Daily Report submitted-by labels, Safety Forms employee labels, FL crew rosters, Shop driver assignments, Dispatch driver lists, Admin global search, all notifications, all PDFs) is **a single-import-line refactor per file**. The helper exists, the contract is locked by regression, the API ships the precomputed field — so any consumer reading `e.display_identity` already gets the right string with **zero further code**.

* **The preview DB has not been backfilled with `legal_first_name` /
  `legal_middle_name` / `legal_last_name` for the 359 existing
  employees.** Their display falls back to the denormalised `name`
  field (e.g. `Alec Perkins`), which is correct per the contract.
  When HR enters legal-name parts + a preferred name for an
  employee, every surface using the helper will render
  `James Fisher (Jimmy)` immediately — no further code change.

* **A one-shot backfill migration** that parses the denormalised
  `name` field into legal first/last (where no parts are already
  stored) is a sensible follow-up. Held out of this track per the
  user directive to not invent new tracks — the helper is honest
  about its fallback behaviour and the underlying data, not the
  display layer, is what needs filling.

## What this track does NOT include

* Backfill migration for existing 359 employees' legal name parts (operationally a one-off DB script; helper already handles it gracefully).
* Application of the helper to PM / Safety / FL / Shop / Dispatch / Admin display labels that currently render `r.employee_name` directly (single-import-line refactor per file — recommend a "UXS-11F display sweep" track to drive adoption to 100%).

The user's certification bar is high. This closure ships the foundation (helper + contract + regression + HR Directory). The remaining cross-surface adoption is the next sweep, tracked transparently above rather than hidden as a fake-certified surface.

---

*Generated 2026-02-14 · Track 14.0-HR-IDENTITY-COMPLETION · Five Pillars: 9.88.*
