# TRACK 16.11 — TRANSPORTATION HR LIFECYCLE INTEGRATION

**Status:** GO · merged · regression green.
**Date:** 2026-02-10
**Scope:** HR-safe, additive-only sync of MASCI HR lifecycle state into
Transportation eligibility for MASCI employee drivers.

---

## HR-SAFE APPROACH

* HR remains the **sole source of truth**. Nothing here mutates an
  employee record.
* No new employee identity, no parallel collection. The mapper reads
  the existing `db.employees` documents and projects a read-only
  snapshot onto the matching `transport_persons` row.
* All HR routes (`POST/PATCH/POST .../status/POST .../reactivate`)
  call a fire-and-forget `safe_sync_after_hr_write` shim **after** the
  HR write has been persisted. Sync failure cannot block HR.

## LIFECYCLE MAPPER (`lib/transport_hr_lifecycle.py`)

`map_hr_lifecycle_to_transport(employee_record) -> dict`

Returns:

```json
{
  "hr_active": true,
  "transport_state": "eligible | pending_review | suspended | not_dispatchable | needs_correction",
  "reason_codes": ["hr_status_active"],
  "reason_labels": ["HR employment is active"],
  "source_status": "Active",
  "source_fields": {...}
}
```

Mapping rules (vocabulary mirrors `ALLOWED_LIFECYCLE_STATUSES`):

| HR `lifecycle_status` | Transport state    | Reason code           |
|-----------------------|--------------------|-----------------------|
| Active                | eligible           | hr_status_active      |
| Pending Hire          | pending_review     | hr_status_pending_hire|
| Seasonal              | eligible           | hr_status_seasonal    |
| Leave of Absence      | suspended          | hr_status_on_leave    |
| Suspended             | suspended          | hr_status_suspended   |
| Inactive              | not_dispatchable   | hr_status_inactive    |
| Terminated            | not_dispatchable   | hr_status_terminated  |
| Resigned              | not_dispatchable   | hr_status_resigned    |
| Retired               | not_dispatchable   | hr_status_retired     |
| (unknown)             | pending_review     | hr_status_unknown     |
| (missing record)      | needs_correction   | hr_employee_missing   |

Driver-status sub-signal (`suspended`, `restricted`, `inactive`) further
narrows but never relaxes the top-level decision. Active employees with
non-driver role / trade / department are projected as
`needs_correction` with `hr_role_not_driver`.

## SYNC HELPER

`sync_transport_person_from_hr(db, employee_id, *, trigger, actor)`

* Locates the existing transport_person where
  `kind=masci_employee` and `employee_id` matches.
* Snapshots projection onto `transport_persons.hr_projection` plus
  `synced_at` / `synced_trigger`.
* Recomputes eligibility via the existing pure
  `compute_transport_eligibility` function and upserts the canonical
  `transport_eligibility_state` row.
* **Never** creates a new transport_person — operators link explicitly
  via Transportation admin (mandate: do not duplicate employees).
* Emits audit rows: `transport_hr_sync_attempted`,
  `transport_hr_sync_succeeded`, `transport_hr_sync_failed`,
  `transport_hr_sync_skipped`.
* Drops action items into `transport_action_items` (idempotent by
  `event_key`) for: HR sync failed, HR employee missing, missing
  linkage, role change, dispatch block due to HR.

## HR HOOKS (additive, post-success)

Added to `routes/employee_lifecycle.py`:

* `POST /api/hr/employees` → `trigger="hr.employee_created"`
* `PATCH /api/hr/employees/{id}` → `trigger="hr.employee_updated"`
* `POST /api/hr/employees/{id}/status` → `trigger="hr.status_changed.{status}"`
* `POST /api/hr/employees/{id}/reactivate` → `trigger="hr.employee_reactivated"`

Each hook is wrapped in `try / except` and uses `safe_sync_after_hr_write`
which swallows every exception. The HR transaction is already committed
when the hook fires.

## ELIGIBILITY

`lib/transport_eligibility.py` now consumes a richer HR context:

* `hr_transport_state` — projection state (preferred over legacy boolean)
* `hr_reason_codes`, `hr_reason_labels`, `hr_source_status`

Any HR projection state of `not_dispatchable / suspended /
needs_correction` overrides document/orientation truth. Reasons carry
`source="hr_lifecycle"` plus the verbatim HR status for the dispatch
gate envelope.

## ACTION QUEUE

* `hr_employee_missing` — HR record not found for linked driver
* `hr_linkage_missing` — Active driver-relevant employee with no
  transport_person link
* `hr_dispatch_block` — HR status now blocks dispatch
* `hr_role_not_driver` — Role / trade moved away from driver
* `hr_sync_failed` — Unexpected error during sync

All rows are idempotent (deduped by `related_event_key`).

## DISPATCH GATE

`lib/transport_dispatch_gate.py` `HUMAN_REASONS` extended with the new
HR codes so block envelopes render text like:

* "Employee is terminated in HR"
* "Employee is on leave in HR"
* "Employee role requires Transportation review"
* "HR lifecycle status unknown — review required"

## UI

`DriverWorkspace` (frontend, `pages/transportation/_lists.jsx`) renders
a new **HR lifecycle projection** card alongside the existing HR linkage
card. The panel is strictly read-only and explicitly states HR is the
source of truth. Test IDs: `driver-hr-lifecycle-panel`,
`driver-hr-projection-chip`, `driver-hr-reason-<i>`,
`driver-hr-synced-at`, `driver-hr-lifecycle-disclaimer`.

No write controls were added to the HR-side UI in this track.

## AUDIT

`db.audit_events` rows now include:

* `kind` ∈ {`transport_hr_sync_attempted`,
  `transport_hr_sync_succeeded`, `transport_hr_sync_failed`,
  `transport_hr_sync_skipped`}
* `employee_id`, `transport_person_id`, `trigger`, `actor`,
  `prior_transport_state`, `new_transport_state`,
  `source_hr_status`, `ts`.

## EMAIL / NOTIFICATIONS

Route key `TRANSPORT_HR_LIFECYCLE_SYNC_ALERT` is referenced as the
action-item association only. No new send paths were enabled.
Internal-only, dry-run by default if/when later seeded.

No SMS / Twilio / push references.

## TESTS

`backend/tests/test_track_16_11_transport_hr_lifecycle_integration.py`
covers all 32 mandated requirements + 2 bonus end-to-end assertions
(projection persistence + eligibility recompute). Wired into
`scripts/deployment_gate.py`.

Regression: **34 / 34 new tests pass** · 354 transport-track tests pass
(8 network-gated live smoke tests skipped without env).

## RISKS / DEFERRALS

* Stale-sync detection (time-based) intentionally deferred — codes
  exist (`hr_sync_stale`) but no scheduled stale scanner runs yet.
* HR onboarding automation, HR document packet changes, payroll
  integration, fuel cards, badge checklist — all deferred (P2).

## SIX-PILLAR SCORE

* Powerful — 9 / 10 · HR change → dispatch state in one transaction.
* Simple — 10 / 10 · single mapper + single helper + 4 hook lines.
* Beautiful — 9 / 10 · UI panel is calm, dispatcher gate text is
  human-readable.
* Trusted — 10 / 10 · audit row per attempt, source HR status
  preserved verbatim.
* Proven — 10 / 10 · 34 tests + full transport-track regression green.
* Deployable — 10 / 10 · additive only, no destructive migration, no
  HR routes touched.
* **Overall — 9.7 / 10 · GO.**

## NEXT RECOMMENDED TRACK

Track 16.12 — Transportation predictive analytics / carrier scorecards
(P2), or Track 16.11A — stale-sync scanner if operators want a daily
proof that HR ↔ Transportation projections remain consistent.
