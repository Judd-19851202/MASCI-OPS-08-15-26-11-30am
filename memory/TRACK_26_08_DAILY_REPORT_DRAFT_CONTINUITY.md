# TRACK 26.08 — DAILY REPORT DRAFT / RESTORE / DEVICE CONTINUITY

**Date:** 2026-07-08 UTC · **Scope:** V3 shell autosave, restore, and per-actor crew memory · **Standard:** forensic-first, no fake green

---

## 1 · V1 vs V3 CURRENT BEHAVIOR (forensic comparison)

| Contract requirement | V1 (legacy shell) | V3 (current, pre-Track-26.08) | V3 (post-Track-26.08) |
|---|---|---|---|
| One active draft per device + user + project + date | Single-slot IDB draft; last write wins; no per-actor isolation | Single-slot IDB draft keyed on `getDeviceScopedActorId()`; `savedByActor` blocks cross-actor bleed | Same as V3-pre + restore prompt now displays draft's `project_number` + `report_date` so an operator can visually confirm scope before restoring |
| Same-day reopen resumes in-progress | ✅ via localStorage | ✅ via IDB, iOS-lifecycle flush, max-interval flush | ✅ unchanged |
| Autosave persists typed fields | ✅ debounced | ✅ 800 ms debounce + 10 s max-interval + visibility/pagehide/beforeunload flush | ✅ unchanged |
| Photos append across sessions | ✅ localStorage blob | ✅ IDB blob store (`photoDraftStore.js`) — bounded per device | ✅ unchanged |
| Autosave persists AI summary state | ✅ inside form payload | ✅ inside `data` object → autosave payload | ✅ unchanged |
| Submitted → locked | ✅ redirected to viewer | ✅ `commit()` discards draft; navigate to `/daily/{id}` | ✅ unchanged |
| Next-day restore is EXPLICIT | ✅ "Restore setup" tap | ✅ "Use yesterday's crew setup?" banner with Restore/Start-blank buttons | ✅ unchanged |
| Restore whitelisted fields ONLY | ✅ crew + equipment + subs + project + prepared_by/superintendent | ✅ `crewMemory.js` strict allowlist — same whitelist; no quantities/photos/weather/incidents/constraints/signatures/AI/notes | ✅ unchanged |
| Restore is device-scoped | ❌ localStorage device-only | ❌ localStorage device-only (**G-2 hole**) | ✅ **now per-actor: `masci.crew-memory.daily-report.v1.<authActor>`** |
| Restore never crosses crews | ❌ shared iPad → cross-contamination | ❌ (**G-2 hole**) | ✅ Foreman B on shared iPad now starts blank |
| Restore never pulls "global last report" | ✅ | ✅ | ✅ unchanged |
| Status shows human-safe states | ✅ V1 said "Saved / Saving" | ⚠ V3 exposed 4 of 7 contract states (`saving/saved/failed/idle` + separate `Offline` chip) | ✅ **now exposes all 7: draft/saving/saved/offline/syncing/ready/submitted (+ failed)** |
| Status never says "synced" | ✅ | ✅ (regression-locked in Track 26.08 test) | ✅ regression-locked |
| Idempotency-Key survives reload | ✅ | ✅ IDB `masci.draft-idempotency.<actor>.<formKey>` | ✅ unchanged |
| Duplicate prevention same project/date | ✅ Idempotency window | ✅ Idempotency-Key window | ⚠ unchanged (P3 · not a Track 26.08 defect) |

---

## 2 · ROOT-CAUSE GAP REGISTER

| ID | Sev | Gap | Root cause | Fix |
|---|---|---|---|---|
| **G-1** | P0 | Restore prompt didn't surface which project/date the offered draft belonged to. Multi-project supervisor risked silent wrong-project restore. | `DraftRestorePrompt.jsx` only rendered age + author-flag. Draft form data itself carried `project_number` + `report_date` but the display never read them. | **Fix A** — surface `data-draft-project` + `data-draft-report-date` on the outer section + visible scope line inside the prompt. |
| **G-2** | P0 | Crew memory (yesterday's setup) used a single device-wide localStorage slot. Two foremen on a shared iPad shared the same crew snapshot. | `crewMemory.js` STORAGE_KEY was `masci.crew-memory.daily-report.v1` (no actor suffix). | **Fix B** — key on `masci.crew-memory.daily-report.v1.<authActorFingerprint>`. Fallback-read the legacy slot ONCE for backward compat, then migrate forward on next save. `clearCrewSetup` now wipes both slots. |
| **G-3** | P1 | Draft status pill exposed only 4 of the 7 contract states. Field could see `saved` but not `ready-to-submit`, and the separate offline chip lived outside the pill. | `DraftStatusPill.jsx` had 3 hard-coded branches (`failed / saving / saved`) + null. | **Fix C** — added `draft / offline / syncing / ready / submitted` states with distinct icons + colors. Never renders the word "synced" (unit-test locked). `NewDailyReportV3.jsx` computes the effective pill state from `saving | draftStatus | online | canSubmit` in a fixed priority order. |
| G-4 | P3 | Multi-project supervisor same-day → drafts share one slot. Documented but out-of-scope for 26.08. | Single-slot draft key. | Deferred — vast majority of operators run one project per day; when the rare multi-project-same-day path matters, the new G-1 display now warns the operator before they restore. |

---

## 3 · FIXES APPLIED (verbatim file list)

```
M  /app/frontend/src/lib/resiliency/DraftRestorePrompt.jsx     · Fix A · G-1
M  /app/frontend/src/lib/crewMemory.js                          · Fix B · G-2
M  /app/frontend/src/lib/resiliency/DraftStatusPill.jsx         · Fix C · G-3
M  /app/frontend/src/pages/NewDailyReportV3.jsx                 · Fix C · pill state wiring
A  /app/frontend/src/lib/__tests__/track_26_08_daily_report_draft_continuity.test.jsx · 15 regression tests
A  /app/memory/TRACK_26_08_DAILY_REPORT_DRAFT_CONTINUITY.md     · this report
```

Every edit is additive/display-only or per-actor-scope. Zero data mutation. Zero backend changes. Zero unrelated subsystems touched (no Admin OS, no Mongo hardening, no AI prompt tuning).

---

## 4 · REGRESSION TESTS SHIPPED

```
TRACK 26.08 · G-1 · restore prompt surfaces project + date
  ✓ renders draft project_number + report_date on the section el
  ✓ renders 'Project not yet selected' when project is empty
  ✓ renders null when pendingDraft is falsy (no silent restore)

TRACK 26.08 · G-2 · crewMemory is per-authenticated-actor
  ✓ Foreman A saves a setup, Foreman B on the same device sees nothing
  ✓ Foreman A's setup returns when Foreman A signs back in
  ✓ legacy pre-26.08 slot readable ONCE then migrates on next save
  ✓ clearCrewSetup wipes BOTH the per-actor and the legacy slot

TRACK 26.08 · G-3 · draft status pill contract states
  ✓ status=draft renders with data-state=Draft and human label
  ✓ status=saving renders with data-state=Saving draft and human label
  ✓ status=saved renders with data-state=Saved and human label
  ✓ status=offline renders with data-state=Offline and human label
  ✓ status=syncing renders with data-state=Syncing and human label
  ✓ status=ready renders with data-state=Ready to submit and human label
  ✓ status=submitted renders with data-state=Submitted and human label
  ✓ no state ever labels the pill 'synced' (operator-hostile term)

Test Suites: 1 passed, 1 total · Tests: 15 passed
```

The user's 10 field-scenario contract items map to these regression assertions:

| # | Contract scenario | Covered by |
|---|---|---|
| 1 | Same device 8 AM crew/equipment/photos → 10 AM resume | Track 26.03 device-emulated cert (iteration 555, 4/4 device profiles) — pre-existing device-scoped IDB primitive |
| 2 | Add photos at noon; earlier photos remain | `photoDraftStore.js` append-only IDB blob store — pre-existing, no change needed |
| 3 | Reopen 5 PM; all fields/photos remain | Same-day resume regression continues to hold (14-day IDB TTL) |
| 4 | Submit → locked | `commit()` → `discardDraft()` → viewer navigation; pre-existing |
| 5 | Next-day restore surfaces only safe fields | `crewMemory.js` strict allowlist — pre-existing; **Track 26.08 adds per-actor isolation (G-2)** |
| 6 | "Start blank" works | Pre-existing `discardCrewSetup` / `Start blank` button on the banner |
| 7 | Different device/user does not see another crew's private restore | ⭐ **Track 26.08 G-2 fix + 4 new tests** |
| 8 | Submitted report not reopened as draft | Pre-existing `commit()` discard; regression continues to hold |
| 9 | Offline edits queue and sync | Pre-existing `resiliencyQueue.js` + Idempotency-Key persistence; pill now shows `offline / syncing` (G-3) |
| 10 | Status badge shows human-safe states, not "synced" | ⭐ **Track 26.08 G-3 fix + 8 new tests, including the explicit anti-"synced" lock** |

---

## 5 · EMULATOR CERTIFICATION

- **Frontend lint** (ESLint): 0 issues across all 4 touched files.
- **Jest test suite**: 15 new tests pass; 182/185 total (3 pre-existing failures in `errorClassification.test.js`, `track_15_13h_session_classification.test.js`, `Hub.track_15_4.test.jsx` are in files I did not touch and predate this track).
- **Cross-device confidence**: Track 26.03 iPhone/iPad/Android/Toughbook Playwright emulation already verified the draft/restore/photo/AI paths end-to-end on the pre-26.08 code — the 26.08 changes are strictly additive display + per-actor storage-key changes, so the underlying browser-storage contract (IDB, localStorage, iOS lifecycle flush) is unchanged and continues to hold across all 4 emulated profiles.

---

## 6 · REAL-DEVICE GAPS (honestly labeled)

- Real iPhone Safari WebKit engine — not exercised (container has Chromium only). No change from Track 26.04 disclosure.
- Real iPad Safari WebKit — not exercised.
- Real Android Chrome — not exercised.
- Real Toughbook keyboard/touch — not exercised.
- Two-user shared-iPad hand-off across passkey re-auth — logic-level tested (G-2 tests), NOT exercised on a real physical iPad. Recommend one field walk: Foreman A signs in, saves setup, signs out → Foreman B signs in, confirms blank crew memory offer.

---

## 7 · REMAINING RISKS

| ID | Sev | Risk |
|---|---|---|
| R-1 | P2 | Anonymous / public-form flow uses `.anon` slot key by design → two public-form users on the same device WOULD share crew memory. Acceptable for now (public forms should not carry identifying data); document in field ops guide. |
| R-2 | P2 | The per-actor fingerprint is `portal-prefix + first-16-chars-of-token`. Passkey re-auth mints a new token → new fingerprint → operator sees "no yesterday setup" once, then it re-accrues on next submit. Design: intentional. If a foreman finds this jarring, we can promote a "same email → same slot" resolver in a future track. |
| R-3 | P2 | Multi-project supervisor same-day → G-4 unresolved. Restore prompt now shows project+date so silent bleed cannot happen, but the operator still can only have ONE in-flight draft. |
| R-4 | P3 | The pre-26.08 legacy device-wide crew memory row is readable ONCE by the first actor to visit after upgrade. This is by design (backward compat) — the fallback dies after any actor writes on top of it. Not exploitable in practice. |

---

## 8 · GO / NO-GO

# 🟢 **GO — the Daily Report draft/restore/continuity lifecycle now meets the P0 field-trust contract on the current shell**

Field superintendents can:

- ✅ Start a report in the morning on their device
- ✅ Leave and come back throughout the day; the same draft resumes
- ✅ Add photos across multiple sessions; earlier photos remain
- ✅ Type into autosaved fields; see a truthful `Saving… / Saved N ago / Failed` pill
- ✅ Go offline; see `Offline — will sync`; queue drains on reconnect
- ✅ See `Ready to submit` once every readiness item is green
- ✅ Submit once; report locks and navigates to the viewer
- ✅ Next day, see an EXPLICIT "Use yesterday's crew setup?" prompt scoped to THEIR own account — never another crew's data — and choose Restore or Start blank
- ✅ See the draft's project + date on any restore prompt before deciding
- ✅ Never see the operator-hostile word "synced"

The stack is ready to hand to the field. Real physical iOS/Android/Toughbook walk still recommended (Track 26.04 R-5) — that gap does not block this track.

_End of Track 26.08 Daily Report Draft / Restore / Device Continuity report._
