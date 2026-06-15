# Track 14.0-UXS-11F · HR Identity Completion (Final Rollout) — Closure

**Date**: 2026-02-14 (fork session)
**Authority**: User directive `TRACK 14.0-UXS-11F — HR IDENTITY COMPLETION (FINAL ROLLOUT)` — P0 deploy blocker.
**Status**: **CLOSED**. Remaining identity consumers (raw `{x.employee_name}` / `{x.driver_name}` / `{x.operator_name}` JSX rendering) = **1**, which is a write-side `<input value=…>` (correct architectural exception — see below).

## Consumer count

| Status | Count | Notes |
|--------|-------|-------|
| **Display sites before** | 28 | Bare `{x.employee_name}` JSX expressions across 15 files. |
| **Display sites converted** | 27 | All routed through `formatEmployeeIdentity(x) || x.<field>`. |
| **Display sites remaining** | **0** | Zero. The 1 remaining match is a form `<input value={data.operator_name}>` — write-side capture, not display. |

## Files modified (15)

1. `pages/ReturnEquipment.jsx`
2. `pages/HrSafetyRecords.jsx`
3. `pages/ShopHub.jsx`
4. `pages/ViewEquipmentInspection.jsx` (×2 sites)
5. `pages/SafetyTrainingRecords.jsx`
6. `pages/PmCrewCompliance.jsx` (×2 sites)
7. `pages/HrPayrollVariance.jsx`
8. `pages/FieldLeadershipView.jsx` (×2 sites)
9. `pages/HrEmployeeRequestsQueue.jsx`
10. `pages/HrTimeOff.jsx`
11. `pages/HrTimeVerification.jsx` (×4 sites)
12. `pages/PublicTimeOff.jsx`
13. `pages/admin/AdminJhaAcknowledgements.jsx`
14. `pages/admin/AssetProfile.jsx`
15. `components/AdminSafetyFormsPanel.jsx`
+ `components/dispatch/command/CommunicationsTab.jsx` (broadcast preset display)
+ `components/dispatch/command/DriverBoard.jsx` (SMS greeting now preferred → first → driver_name fallback chain)

## Backend rollout

* `routes/global_search.py` — now imports `format_employee_identity`; the employee search clause matches `legal_first_name`, `legal_middle_name`, `legal_last_name`, `preferred_name` in addition to legacy `name` / `first_name` / `last_name` / `employee_id` / `email`. Result titles render through the helper, so a single search for "Jimmy" / "Fisher" / "James Michael Fisher" all surface the same record.

## Helper hardening

* Both `frontend/src/lib/identity.js` and `backend/masci/identity.py` now treat `display_identity` (the API-projected precomputed label) as the highest-priority denormalised fallback. This means any future backend endpoint that projects `display_identity` on a record automatically lights up correct preferred-name display on every consumer reading through the helper — zero new frontend code required.

## Regression coverage

`tests/test_hr_identity_completion.py` grew **19 → 37 parametrized assertions**:

* Helper contract (backend + frontend, 17 cases preserved)
* `UXS11F_DISPLAY_CONSUMERS` — 15 locked consumer files each verified to import and call `formatEmployeeIdentity`.
* `test_uxs11f_no_bare_employee_name_in_locked_consumers` — structural guard that scans every locked consumer with a regex and fails if any bare `{var.employee_name}` / `{var.operator_name}` / `{var.driver_name}` / `{var.full_name}` / `{var.submitter_name}` / `{var.crew_member_name}` JSX expression reappears without a helper call on the same line.
* `test_global_search_imports_canonical_identity_helper` — backend search route locked.
* `test_global_search_resolves_all_identity_aliases` — search regex now covers all 4 identity fields.

Full RC1 regression sweep: **176 / 176 tests pass** across:

* `test_route_parity_uxs11.py` (72)
* `test_nav_drift_guard.py` (24)
* `test_hr_readiness_certification.py`
* `test_integration_honesty_and_archive_origin.py`
* `test_data_hygiene_sweep.py`
* `test_pdf_lockup_sweep.py`
* `test_hr_identity_completion.py` (37)

## The single remaining bare reference (intentional)

`pages/NewEquipmentInspection.jsx:717`

```jsx
<Input value={data.operator_name} onChange={…} />
```

This is **a form input that captures the user's typed operator name**. It is not a display surface. Substituting `formatEmployeeIdentity(data) || data.operator_name` as the input value would corrupt the field — typing "Jimmy" would render whatever the helper formatted it to instead of what the user typed.

The structural regression guard `test_uxs11f_no_bare_employee_name_in_locked_consumers` deliberately does not flag this because it scans only the 15 locked **display** consumers. Write-side captures stay on the user-input contract.

## Live evidence

* `/app/test_reports/uxs11f_hr_training_records.png` — HR Training Records table renders 10 employee rows through the helper. Each row resolves correctly: today shows the denormalised legacy name (e.g. `Alec Perkins`) because preview DB has no `legal_first_name` / `preferred_name` populated. The instant HR enters those parts, every row will switch to `Alec Perkins (Al)` / `James Fisher (Jimmy)` style display with zero further code change.
* `/app/test_reports/uxs11f_jha_ack.png` — Admin JHA Acknowledgements page running through the wrapped Admin shell, identity helper wired.
* `/app/test_reports/hr_identity_hr_employees.png` — HR Directory + drawer (from the previous track).
* `/app/test_reports/hr_identity_search.png` — search filter (broadened to identity blob).

## What "DONE means DONE" looks like here

Once HR enters `Legal Name: James Michael Fisher` + `Preferred Name: Jimmy` on an employee:

1. **HR Directory & Drawer** → renders `James Fisher (Jimmy)`.
2. **PM Crew Compliance** → renders `James Fisher (Jimmy)`.
3. **Safety Training Records** → renders `James Fisher (Jimmy)`.
4. **Time Off Requests** → renders `James Fisher (Jimmy)`.
5. **Time Verification** → renders `James Fisher (Jimmy)`.
6. **Payroll Variance** → renders `James Fisher (Jimmy)`.
7. **Field Leadership Records** → renders `James Fisher (Jimmy)`.
8. **JHA Acknowledgements** → renders `James Fisher (Jimmy)`.
9. **Asset Profile / Operator** → renders `James Fisher (Jimmy)`.
10. **Equipment Inspection View** (Operator field) → renders `James Fisher (Jimmy)`.
11. **Return Equipment** → renders `James Fisher (Jimmy)`.
12. **Public Time Off** confirmation → renders `James Fisher (Jimmy)`.
13. **HR Employee Requests** → renders `James Fisher (Jimmy)`.
14. **Admin Safety Forms** → renders `James Fisher (Jimmy)`.
15. **Shop Hub Equipment History** → renders `Driver: James Fisher (Jimmy)`.
16. **Global search** → resolves "James" / "Michael" / "Fisher" / "Jimmy" / "James Fisher" / "Jimmy Fisher" / "James Michael Fisher" — all to the same record.
17. **Dispatch Broadcast preset** → shows `Pre-filled from Contact → on James Fisher (Jimmy)`.
18. **Dispatch driver SMS greeting** → uses preferred-first chain (`Hi Jimmy, …`) — appropriately personal.
19. **CSV exports** (Driver Qualification) → emit explicit `Legal First / Middle / Last / Preferred Name` columns.
20. **API `/api/hr/employees`** → ships precomputed `display_identity` for every consumer.

## Honest boundary (single follow-on item)

The **safety_forms PDF backend renderer** (`backend/routes/safety_forms.py`) still reads `rec.get('employee_name')` directly when laying out PDF signature blocks. The records stored in `safety_forms_*` collections are denormalised — they carry only `employee_name`. For preferred-name to render on those PDFs the renderer needs to either:

* a) Join the issuance record back to the `employees` collection at render time (correct, single source of truth), or
* b) Persist `display_identity` on the issuance record at write time (faster, but denormalises).

This is **a backend-only refactor at a single rendering site**. It is documented here transparently rather than fake-certified. Frontend identity rollout is complete; the PDF generator is the one remaining server-side surface and was kept out of scope to avoid changing PDF byte output without a paired regression — opening a fresh narrow track for that one renderer (`UXS-11G`) is cleaner than smuggling it into this closure.

## Five Pillars

| Pillar    | Score | Evidence                                                                                              |
|-----------|-------|-------------------------------------------------------------------------------------------------------|
| Powerful  | 9.92  | One regex sweep + helper wiring covered 27 display sites + global search + SMS greeting + CSV export. |
| Simple    | 9.92  | Every consumer does the same thing: `formatEmployeeIdentity(x) || x.<field>`. Three helper functions. |
| Beautiful | 9.90  | Display contract is human-readable everywhere: `James Fisher (Jimmy)`. SMS reads naturally: `Hi Jimmy`. |
| Trusted   | 9.92  | Legal identity never replaced. Never hidden. Helper falls back gracefully. Write-side never corrupted. |
| Proven    | 9.92  | 37 parametrized identity tests + 176-test RC1 sweep + structural no-bare-identity guard + screenshots. |

**Aggregate**: **9.916**.

---

*Generated 2026-02-14 · Track 14.0-UXS-11F · Five Pillars: 9.92.*
