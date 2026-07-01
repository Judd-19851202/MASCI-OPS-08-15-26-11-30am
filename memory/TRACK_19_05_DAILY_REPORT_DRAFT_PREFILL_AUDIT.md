# Track 19.05 · Daily Report Draft / Autosave / Smart Prefill Audit

Post-Track-19.04 finalized behavior. Sources: `/app/frontend/src/lib/resiliency/*`, `/app/frontend/src/lib/crewMemory.js`, `/app/frontend/src/pages/NewDailyReport.jsx`.

## Storage keys

| Storage | Key shape | Purpose |
| --- | --- | --- |
| IndexedDB | `masci.draft.<deviceId>.daily-report-new` | Primary autosave · envelope `{form, savedAt, savedByActor, contract_version:"19.04"}` |
| IndexedDB | `masci.draft-archive.<deviceId>.daily-report-new.<deletedAt>` | 24 h soft-delete window |
| IndexedDB | `masci.draft-idempotency.<deviceId>.daily-report-new` | Submit idempotency key |
| localStorage | `masci.crew-memory.daily-report.v1` | Device-local Phase 31.1 crew setup snapshot |
| localStorage | `masci.prior-usage.daily-report-new` | Beacon (no payload) |
| localStorage | `masci_device_id` | Persistent device fingerprint |

## Identities

| Identity | Source | Used for |
| --- | --- | --- |
| Device ID | `getDeviceId()` (persistent local) | IDB key scoping, banner targeting, telemetry |
| Auth actor fingerprint | `getAuthActorFingerprint()` — 7 portal token probes, first-match, `<prefix>.<token[:16]>` or `"anon"` | Track 19.04 restore gate |
| Legacy actor id | `getLegacyActorIds()` | One-shot IDB migration to device-scoped key |

## Draft lifecycle

1. **Save** — 800 ms debounce + 10 s force-flush + iOS `visibilitychange`/`pagehide`/`beforeunload` synchronous flushes. Each write stamps `savedByActor` + `contract_version:"19.04"`.
2. **Restore offer** — on mount, `useFormDraft` reads the entry. Surfaces `pendingDraft` ONLY when `entry.savedByActor === currentAuthActor` (or legacy stamp missing → surface with `isCrossToken=true`). Cross-actor drafts silently blocked; emits `draft.restore.blocked_cross_actor`.
3. **Discard** — moves entry to `-archive.` prefix; 24 h TTL; max 5 per form.
4. **Commit (on submit)** — `discardDraft` + `clearIdempotencyKey`.
5. **Prior-usage beacon** — records the fact this device has saved this form before (no payload).

## Smart Prefill sources (allowed baselines)

Ordered by precedence:
1. Current active draft (via explicit Restore prompt).
2. `/api/jobs/{pn}/recent-context?foreman=…&superintendent=…` — Track 19.04 v19.04 contract. Filters to actor's own most-recent baseline when `foreman`/`superintendent` params match. Falls back to project-most-recent when no self-report.
3. Device-local Phase 31.1 snapshot (`crewMemory.js`) — restore prompt only, never silent.
4. Blank.

## Fields Smart Prefill MAY populate

* `superintendent` (auto-fill when foreman hasn't typed one and job-master lacks it).
* `masci_crews[]` (name, employee_id, trade, hours) — via v19.04 offer chip.
* `equipment[]` (description, hours_used) — via v19.04 offer chip.
* Phase 31.1 setup fields (prepared_by, project_name, project_number, superintendent, `masci_crews` name+trade, `subcontractors` company+trade+foreman, `equipment` description) — via CrewSetupRestorePrompt.

## Fields Smart Prefill MUST NOT populate (per doctrine)

Times (start/lunch/stop, time_delivered/removed), production quantities, notes/work_performed, weather, incidents, signatures, photos, materials rows, visitor rows, ticket numbers.

## Cross-user protections (Track 19.04 verified)

| Protection | Mechanism |
| --- | --- |
| Cross-actor draft leak | `savedByActor` gate in `useFormDraft` |
| Cross-project prefill | Project number scopes `/recent-context`; different project → no baseline returned |
| Cross-session silent apply | Smart Prefill is now an OFFER (Apply / Dismiss); never silent |
| Cross-device residue | IDB is device-local; no server sync |
| Global "latest draft" lookup | Verified absent by pytest `test_no_global_latest_draft_endpoint` |

## Contract lock tests (Track 19.04)

* `test_save_draft_stamps_saved_by_actor`
* `test_useformdraft_gates_restore_by_actor`
* `test_actorid_exposes_auth_fingerprint`
* `test_smart_prefill_is_explicit_offer_not_auto_apply`
* `test_default_data_is_pure_and_carries_attachments_field`

## Redesign risk

* HIGH — any redesign that removes the explicit Apply chip re-opens the Track 19.04 P0.
* HIGH — must preserve `useFormDraft(formKey, data, actorId)` signature; all 8 long-form editors depend on it.
* MEDIUM — `crewMemory.js` snapshot fields are hardcoded; redesign renaming crew/equipment schema requires coordinated update.
