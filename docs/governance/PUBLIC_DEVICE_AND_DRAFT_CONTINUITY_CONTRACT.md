# PRE-C10 Public Device & Draft Continuity Contract

Date: 2026-08-09  
Status: **IN PROGRESS — shared root cause repaired for the current public-form denominator; full lane remains open until all audited public workflows and cross-device protections are fully evidenced.**

## Constitutional distinction

- Anonymous device continuity **is not authentication**.
- Device identity exists only to support:
  - autosave,
  - draft recovery,
  - interruption recovery,
  - same-device continuation,
  - draft/submitted separation.
- Device continuity must **never** become:
  - employee identity,
  - portal authorization,
  - protected-data access,
  - proof of signature,
  - proof of attendance,
  - proof of submission ownership.

## Root cause found in the current PRE-C10 lane

Public forms had two shared continuity drifts:

1. **Token-scoped actor IDs leaked into public draft identity**  
   Shared `useFormDraft()` consumers were defaulting to `getActorId()`, which can resolve to a portal-token-prefixed identity when a protected portal had been visited earlier. That meant a public draft created under stale auth context did not have a stable anonymous same-device identity.

2. **Several public forms had no explicit anonymous draft-session contract**  
   The form could autosave, but there was no formalized public session scope / recovery boundary proving that the saved work belonged to an anonymous device session rather than a signed-in portal identity.

## Shared owner/components

- `frontend/src/lib/resiliency/publicDraftScope.js`
- `frontend/src/lib/resiliency/useFormDraft.js`
- Public form pages using the shared draft hook
- Public lookup components that sit inside those forms

## Shared repair now in place

- Added `publicDraftScope.js` with:
  - `getActivePublicDraftSession()`
  - `ensureActivePublicDraftSession()`
  - `clearActivePublicDraftSession()`
  - `buildPublicDraftSessionScope()`
  - `buildPublicDraftScopedFormKey()`
  - `hasMeaningfulPublicDraft()`
- Wired anonymous device draft continuity into these public workflows:
  - `/daily/submit`
  - `/trench-safety/excavation/new`
  - `/safety/inspections/new`
  - `/meetings/submit`
  - `/incidents/report` shared incident entry layer
  - `/safety/forms/equipment-issuance/new`
  - `/safety/forms/equipment-training/new`
  - `/equipment/submit`
  - `/fleet/dvir/new`
- Public forms now use:
  - `getDeviceScopedActorId()`
  - `publicAnonymous: true`
  - explicit restore/discard UX via `DraftRestorePrompt`
  - visible draft-state indicator via `DraftStatusPill`
  - `Idempotency-Key` on canonical submit paths so reconnect/retry stays one record instead of duplicate truth
- Daily Report keeps a stricter same-device contract where supported:
  - `getActiveDailyReportDraftSession()` / `ensureActiveDailyReportDraftSession()` / `clearActiveDailyReportDraftSession()`
  - same-device session scope when a draft has already started
  - explicit `Restore` / `Discard` choice on reload instead of silent auto-restore
  - fallback recovery for recent/day-before drafts on the same device
  - persisted `Idempotency-Key` so reconnect/retry stays a single canonical submit
- Successful submission now clears the active anonymous draft session so the completed draft does not resurface as unfinished work.

## Permanent regression tripwires added

- `frontend/src/lib/resiliency/__tests__/publicDraftScope.test.js`
- `frontend/src/lib/resiliency/__tests__/publicDeviceDraftContract.test.js`
- `frontend/src/lib/resiliency/__tests__/dailyReportScope.test.js`
- `frontend/src/lib/resiliency/__tests__/dailyReportDraftContinuityContract.test.js`
- `frontend/src/lib/__tests__/publicExcavationContract.test.js`

These fail future builds if the shared anonymous draft session primitives disappear or if audited public forms stop using the anonymous-device draft contract.

## Direct evidence captured so far

- Focused frontend tests PASS:
  - `publicDraftScope.test.js`
  - `publicDeviceDraftContract.test.js`
  - existing `c2_session_reset` and `Hub.session-home` regressions still PASS
- Clean signed-out browser recovery smoke PASS:
  - `/daily/submit` now shows an explicit restore/discard prompt on reload, preserves same-device session scope, supports recent/day-before fallback recovery where applicable, and clears the active session after canonical submit/queue settle
  - `/trench-safety/excavation/new` now shows draft status, restore/discard prompt, public-safe roster fallback, and idempotent canonical submit/reinspection request behavior signed-out
  - `/equipment/submit` autosave → reload → restore prompt → restore value
  - `/safety/forms/equipment-issuance/new` autosave → reload → restore prompt → restore value
  - `/fleet/dvir/new` autosave → reload → restore prompt → restore value

## Remaining denominator still open

- Same-device recovery proof still needs to be extended across every audited public workflow, not only the currently repaired subset.
- Cross-device leakage proof still needs explicit runtime evidence.
- Multiple-draft selection on shared devices still needs broader denominator review to prove every applicable workflow either:
  - correctly separates multiple recoverable drafts, or
  - is factually constrained to one active draft per workflow with no ambiguity.
- Attachment/photo/signature continuity still requires route-by-route evidence before any claim that it is recoverable.
- Final KPI/truth contamination proof for drafts vs submitted records remains part of the broader PRE-C10 denominator.

## Frozen behavior contract for audited public forms

For the repaired public workflows, the current contract is:

`Signed-out device` → `anonymous device session` → `autosaved draft` → `restore/discard choice` → `same-device continuation` → `single canonical submit` → `draft session cleared`

Not allowed:

- `device session` → `portal auth`
- `device session` → `employee identity`
- `draft` → `submitted KPI/history`
- `stale portal token` → `public draft ownership`
- `submitted record` → `draft prompt resurfacing`