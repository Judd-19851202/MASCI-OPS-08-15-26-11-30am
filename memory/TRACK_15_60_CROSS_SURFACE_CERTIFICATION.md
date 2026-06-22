# TRACK 15.60 — Cross-Surface Request-to-Add Certification (Phase 8)

The cross-surface guarantee in 15.60 is that **every place a real field user can hit an unknown person must offer a reliable Request-to-Add affordance, and a failure there must NOT destroy the parent form's state.**

All five primary safety / field surfaces share the SAME `EmployeeCombo` component. The Track 15.60 fix to `EmployeeCombo.addToRoster` therefore lands in every surface simultaneously.

## Per-surface certification grid

| # | Surface | URL | Button visible? | Form opens & submits to `/api/employee-requests`? | HR notified? | Parent form survives failure? | Offline queue active? |
|---|---|---|---|---|---|---|---|
| 1 | **Safety Meeting** (attendees) | `/meetings/new` | ✅ orange "Request HR add" button under EmployeeCombo | ✅ via `enqueueUpload` | ✅ bell + `/hr/employee-requests` | ✅ proven by stress test C (40 rows survived forced network failure) | ✅ — `enqueueUpload` retries on backoff |
| 2 | **Daily Report** (crew) | `/daily/new` | ✅ same component | ✅ | ✅ | ✅ — `NewDailyReport` has its own draft autosave (iter440) | ✅ |
| 3 | **Incident — Involved Person** | `/incidents/new` | ✅ same component | ✅ | ✅ | ✅ — `NewIncident` has `useFormDraft` (iter440) | ✅ |
| 4 | **Incident — Witnesses** | `/incidents/new` (witness rows) | ✅ same component | ✅ | ✅ | ✅ — same autosave applies | ✅ |
| 5 | **Site Inspection** | `/inspect/new` | ✅ same component | ✅ | ✅ | ✅ — `NewInspection` has `useFormDraft` | ✅ |
| 6 | **Fleet DVIR** (driver) | `/fleet/dvir/new` | ✅ same component | ✅ | ✅ | ✅ — failure is toast-only, no parent mutation | ⚠️ DVIR does not yet wear `useFormDraft` — backlog item; not in 15.60 scope (no failure reported) |
| 7 | **HR review surface** | `/hr/employee-requests` | n/a — read+approve, no new request entry | ✅ all requests visible | ✅ this IS the HR surface | n/a | n/a |

## Confidence per surface

- **Safety Meeting (1)** — the surface that triggered the field report. Directly stress-tested in 6 scenarios; all pass. Highest confidence.
- **Daily Report / Incident / Inspection (2, 3, 4, 5)** — same `EmployeeCombo.addToRoster` code path, exercised by their own iter440-era regression suites. The 15.60 fix is purely additive to the failure path; the success path is unchanged.
- **Fleet DVIR (6)** — Request-to-Add now offline-queues correctly. Form-loss protection is the DVIR's responsibility; not addressed in 15.60 because the DVIR is short (1 page) and no field-loss report exists for it.
- **HR review surface (7)** — already certified by `test_employee_governance_alpha.py` and `test_hr_readiness_certification.py`.

## Surfaces explicitly NOT in scope for 15.60

| Surface | Why deferred |
|---|---|
| **Equipment Issuance form** | Uses a specialised picker, not `EmployeeCombo`. No field-loss report. Backlog item. |
| **Equipment Training form** | Same. |
| **Field Leadership forms** | Uses `FlUserCombo` scoped to FL accounts only. Not a "stranger entered the meeting" surface. |
| **PM Assignment drawer** | Assigns to PMs, not arbitrary persons. |
| **HR Employees page** | This is the destination of approved requests, not a request submission surface. |

## Six Pillars on cross-surface coverage

- **Powerful** — every safety-critical form picks up the resiliency improvement at once.
- **Simple** — operators see the same Request HR add button everywhere; same toast vocabulary.
- **Beautiful** — calm "Request saved · will send when reconnected" replaces the panic-inducing "no signal".
- **Trusted** — no parent-form state can be touched by a Request-to-Add failure anywhere in the platform.
- **Proven** — 6/6 stress-test scenarios pass on the actual failure surface; failure semantics identical across the other 4 EmployeeCombo surfaces by construction.
- **Deployable** — single-component change. No new endpoint, no schema, no migration.
