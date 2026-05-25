# PHASE 31 · Mobile Recovery Validation Matrix

_iter435 · 2026-05-25 · Pass B + operator-owned_

## Purpose
Operator-executed walking validation that the work recovery primitives
hold up on real devices under real conditions. This doc is the
canonical checklist for the next field certification sweep.

## Pre-flight
- Build is at iter435 or later (verify by checking `/admin/system` →
  build identity card)
- A test field-form draft already exists on the device (file a small
  Incident report draft on the device but do NOT submit)
- A staged photo exists for an active assignment (attempt an upload
  while in airplane mode to seed `photoStaging`)
- A queued lifecycle transition exists on a driver session (tap a
  lifecycle button while offline to seed `offlineQueue`)

## Device matrix

| Device | OS | Browser | Tests | Owner | Result |
|--------|----|---------|-------|-------|--------|
| iPhone 13+ | iOS 17 / 18 | Safari | T1–T9 | Operator | ☐ |
| iPhone (older) | iOS 16 | Safari | T1–T9 | Operator | ☐ |
| iPad | iPadOS 17 | Safari | T1–T9 | Operator | ☐ |
| Pixel 7+ | Android 14 | Chrome | T1–T9 | Operator | ☐ |
| Samsung Galaxy | Android 13 | Chrome | T1–T9 | Operator | ☐ |
| Rugged tablet | Android 11+ | Chrome | T1–T9 | Operator | ☐ |
| Desktop | macOS | Safari | T1–T6, T8 | Operator | ☐ |
| Desktop | Windows | Edge | T1–T6, T8 | Operator | ☐ |
| Desktop | Windows / macOS | Firefox | T1–T6, T8 | Operator | ☐ |

## Tests

### T1 · Refresh recovery (text draft)
1. Open `/incidents/submit`
2. Type a few words in any field
3. Wait 2 seconds (autosave debounce)
4. Hit the browser refresh button
5. **EXPECT** the calm amber prompt appears: _"You have unsaved work
   from earlier."_ with **Restore** and **Discard** buttons
6. Click **Restore** → typed text reappears
7. Refresh again → no prompt (draft consumed)

### T2 · Browser close recovery
1. Type into `/daily/submit`
2. Close the browser tab (or app)
3. Re-open the URL
4. **EXPECT** the calm restore prompt
5. Click **Discard** → form resets, no prompt on next reload

### T3 · No auto-overwrite
1. Type into `/incidents/submit`, wait for autosave
2. Refresh
3. **EXPECT** form fields visible on the page remain EMPTY until the
   user clicks Restore. The doctrine forbids auto-apply.

### T4 · Per-actor isolation (shared device)
1. Sign in as User A · type into `/incidents/submit` · refresh
2. **EXPECT** prompt appears for User A
3. Sign out · sign in as User B (different portal token)
4. Navigate to `/incidents/submit`
5. **EXPECT** NO prompt for User B (different `actorId` namespace)

### T5 · Draft expiration
- Manually backdate a draft entry's `savedAt` to > 14 days ago via
  `idb-keyval` DevTools
- Reload the form
- **EXPECT** the stale draft is purged · no prompt

### T6 · Submitted draft cleanup
1. Type into `/incidents/submit`
2. Submit successfully
3. **EXPECT** the IDB key `masci.draft.<actor>.incident-new` is GONE
4. Re-visit the page → no prompt

### T7 · Photo staging (offline upload)
1. On `/dispatch-portal/board` open an assignment drawer
2. Enable airplane mode
3. Tap **Capture / Upload** in the AttachmentStrip · pick a photo
4. **EXPECT** the calm message _"Photo saved on this device · will
   send when online."_ and the **N waiting to send** pill appears
5. Disable airplane mode (regain signal)
6. Wait a few seconds (or trigger window `focus`)
7. **EXPECT** the staged photo uploads · pill disappears · the
   attachment appears in the list

### T8 · Offline lifecycle transitions (driver)
1. Sign in as a driver via magic link
2. Enable airplane mode
3. Tap a lifecycle state button (e.g. ENROUTE_TO_LOAD)
4. **EXPECT** the calm pending-sync indicator appears · no red error
5. Disable airplane mode
6. **EXPECT** the queued transition replays automatically · the
   state card updates to the new state · pending count returns to 0

### T9 · Battery death / app force quit
1. Type a long incident description on `/incidents/submit`
2. Hold power + volume to force-quit the app (or kill the tab)
3. Re-open
4. **EXPECT** the restore prompt with the typed text intact

## Pass / fail rules
- ANY device that fails T1, T2, or T3 is a **P0 escalation** — the
  Phase 31 doctrine fails for that device.
- T7, T8, T9 failures are **P1** — staging / queue still work but
  with friction.
- T4, T5, T6 failures are **P2** — hygiene boundary, not data loss.

## Reporting
- Capture screenshots of EACH prompt appearance on each device.
- File results back to operator via `/admin/system` or push the
  results into a follow-up `PHASE31_MOBILE_RECOVERY_RESULTS_YYYY-MM-DD.md`
  in `/app/memory/`.

## Anti-scope
- NO test for backup dashboards, KPI screens, or admin draft
  browsers — those do not exist by doctrine.
- NO test for Service Worker behaviour — Phase 31 is foreground-only.
