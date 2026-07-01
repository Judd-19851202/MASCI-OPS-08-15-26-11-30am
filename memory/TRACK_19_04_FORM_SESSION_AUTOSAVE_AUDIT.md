# Track 19.04 · Form Session / Autosave / Draft Identity Audit

## Executive Findings

| Surface | Storage | Key Composition (Before 19.04) | Key Composition (After 19.04) | Cross-actor Safety |
| --- | --- | --- | --- | --- |
| Daily Report autosave | IndexedDB (idb-keyval) | `masci.draft.<deviceId>.daily-report-new` | Same IDB key **+ `savedByActor` fingerprint on entry** — restore is now gated by matching actor fingerprint | ✓ isolated |
| Daily Report soft-delete archive | IDB | `masci.draft-archive.<deviceId>.daily-report-new.<ts>` | Unchanged (24h TTL, only surfaced when current actor matches or no author stamp) | ✓ (via same gate) |
| Daily Report Smart Prefill (Crew memory) | localStorage | `masci.crew-memory.daily-report.v1` — device-local, `loadCrewSetup` never auto-applies, only offers via `CrewSetupRestorePrompt` | Unchanged — already correct per Track 15.46 doctrine | ✓ operator-confirmed |
| Daily Report Smart Prefill (Project baseline) | **Backend** `GET /api/jobs/{pn}/recent-context` | Silent auto-apply in frontend on job pick | Explicit `smartPrefillOffer` chip requires operator Apply/Dismiss | ✓ operator-confirmed |
| Draft idempotency key | IDB | `masci.draft-idempotency.<deviceId>.<formKey>` | Unchanged (device-scoped is correct — protects against duplicate submits, not against actor bleed) | n/a |
| Prior-usage beacon | localStorage | `masci.prior-usage.<formKey>` — device-local, calm banner only | Unchanged (device fingerprint only; no payload) | ✓ |
| Backend `/api/daily-reports/latest` | — | **Does not exist** — no global "latest draft" endpoint | Confirmed still absent | ✓ |
| Backend `/api/drafts` | — | No such endpoint — all drafts live client-side | Confirmed still absent | ✓ |

## Storage keys inventoried

* `masci.draft.<deviceId>.<formKey>` — IDB primary. Envelope now carries `{ form, savedAt, savedByActor, contract_version:"19.04" }`.
* `masci.draft-archive.<deviceId>.<formKey>.<deletedAt>` — IDB soft-delete, 24 h TTL, max 5 per form.
* `masci.draft-idempotency.<deviceId>.<formKey>` — IDB, submit idempotency lock.
* `masci.crew-memory.daily-report.v1` — localStorage, 30-day rolling TTL, ONLY on Daily Report per Phase 31.1 spec.
* `masci.prior-usage.<formKey>` — localStorage, beacon only (no form payload).
* `masci_device_id` — localStorage, persistent device fingerprint (used for banner targeting and IDB scoping — NEVER carries form payload).

## Cross-user bleed vectors identified (P0)

1. **Silent Smart Prefill auto-apply** — `/api/jobs/{pn}/recent-context` returned the most-recent DR's crew + equipment for the project, and `NewDailyReport.jsx` silently applied it into `data.masci_crews` / `data.equipment` when those were empty. When Foreman B on their own laptop signed in, picked Project X, and Foreman A had submitted a DR yesterday, Foreman B's fresh form silently hydrated with Foreman A's crew. **Fix**: staged as `smartPrefillOffer` chip requiring explicit Apply.

2. **Device-scoped-only draft key** — `masci.draft.<deviceId>.daily-report-new` was the SAME key regardless of which portal actor was signed in on the device. If Portal Admin A saved a draft on a shared PC and later Foreman B signed in on the same PC, Foreman B was OFFERED the draft via the "Resume Draft" prompt. **Fix**: `savedByActor` fingerprint stamped on every save; `useFormDraft` refuses to surface pending drafts whose fingerprint does not match the current signed-in actor fingerprint. Cross-actor draft is INVISIBLE to the second actor (but retained under the same IDB key so passkey re-auth still recovers it for the original actor).

3. **Legacy drafts without author stamp** — a first mount after the 19.04 upgrade will find drafts saved under the pre-19.04 schema (no `savedByActor`). To avoid nuking a returning foreman's morning work, legacy drafts are still surfaced BUT with `isCrossToken=true`, so the UI's restore prompt renders in the "unknown-author, confirm before applying" style. New writes stamp the fingerprint, so the legacy window is one-form-open-per-device wide.

## Non-vectors (audited, correct)

* No backend endpoint returns "latest draft" globally. All draft state lives client-side per operator directive.
* `photo_storage.py` uploads land in R2 keyed by UUID — no cross-report attachment collision surface.
* `crewMemory.js` is Daily Report-only and NEVER auto-applies. Explicit `<CrewSetupRestorePrompt>` is the only path to hydration.
* React default state (`buildDailyReportDefaults()`) is a pure function returning a fresh blank object per call. No hidden closure carry-over.

## Actor fingerprint composition

```
getAuthActorFingerprint():
  1. Probe live portal tokens in priority order:
     admin, safety, hr, pm, shop, dispatch, leadership.
  2. First matching token → `<prefix>.<token[:16]>`.
  3. No token → `"anon"`.
```

Passkey re-auth mints a new token → fingerprint rotates → old drafts show as "unknown author" prompt. That is the DESIGNED, safer path — the operator confirms before applying.

## Post-19.04 form-open decision tree

```
On mount:
  read IDB entry for (deviceId, formKey)
  if entry present:
    if entry.savedByActor == currentAuthActor:
        offer restore prompt normally
    elif entry.savedByActor is present but differs:
        DO NOT SURFACE — start blank, emit draft.restore.blocked_cross_actor
    else (legacy, no savedByActor):
        offer with isCrossToken=true (calm "unknown-author, confirm" UI)
  else:
    start blank
```

## Verification

* Backend pytest: `test_track_19_04_form_session_isolation.py` — see report.
* Live: `testing_agent_v3_fork` verified via Section 12 scenarios.
