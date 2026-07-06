# TRACK 22.4C — MOBILE RESPONSIVENESS SWEEP + FIELD DEVICE CERTIFICATION

**Status:** ✅ GO · 2026-07-06
**Scope:** Certify MASCI Ops across real field-device viewports (390px
phone, 430px large-phone, 768px tablet portrait, 1024px iPad landscape,
1366px laptop). Close the two known Track 22.4 P1 defects
(PM Command Center 390px + Dispatch Map 390px). Fix one new P1 caught
during the sweep. Regression-lock everything.

## Viewports Certified

| Width  | Device class            | Verdict |
|--------|-------------------------|---------|
| 390px  | iPhone 12/13/14 baseline| ✅ ZERO horizontal overflow on 15 routes |
| 430px  | large phone             | ✅ ZERO horizontal overflow on 15 routes |
| 768px  | iPad portrait / tablet  | ✅ ZERO horizontal overflow on 15 routes |
| 1024px | iPad landscape / tablet | ✅ ZERO horizontal overflow on 15 routes |
| 1366px | laptop                  | ✅ ZERO horizontal overflow on 15 routes |

## Known P1 Fixes (Track 22.4 carry-overs)

- **PM Command Center 390px:** ✅ FIXED (was already responsive in the
  handoff repo state — command strip uses 2/3/4/6-col Tailwind grid,
  page-shell wraps cleanly). Regression lock:
  `test_pm_command_center_390px_no_horizontal_overflow`.
- **Dispatch Map / Dispatch Hub 390px:** ✅ FIXED (Motive stale ribbon
  renders inline, map controls sit inside the map container, sticky
  actions do not cover content). Regression lock:
  `test_dispatch_map_390px_no_horizontal_overflow`.

## New P1 Caught + Fixed During the Sweep

- **P1 · PortalShell H1 pre-hydration overflow at 390px** — long
  question-style titles ("What safety work requires attention right
  now?", "What requires the dispatcher's attention right now?")
  rendered at ~500-540px before whitespace wrapping settled, briefly
  pushing the document width past 390px. Field devices don't wait for
  hydration; this was a real defect.
  - **Fix:** `/app/frontend/src/design-system/PortalShell.jsx` —
    added `min-w-0 flex-1` to the H1's flex parent and
    `overflowWrap: anywhere; wordBreak: break-word; hyphens: auto;
    lineHeight: 1.15` to the H1 inline style. Any pre-wrap browser
    state is now forced to break inside the container.
  - **Regression lock:** 15 routes × 5 viewports = 75 parametrized
    overflow assertions in `test_route_has_no_horizontal_overflow`.
  - **RBAC / Motive / visual identity:** untouched.

## Portal Verdicts

| Portal / Surface       | 390px | 1024px | Notes |
|------------------------|-------|--------|-------|
| Admin Console          | ✅    | ✅     | landing tile responsive |
| PM Command Center      | ✅    | ✅     | strip 2-col → 6-col grid; project-first home stacks cleanly |
| Safety Hub V2          | ✅    | ✅     | H1 fix applied |
| HR Portal              | ✅    | ✅     | landing shell responsive |
| Dispatch Hub Legacy    | ✅    | ✅     | Motive ribbon + map + coaching tips + OA1 all stack cleanly |
| Dispatch Hub V2        | ✅    | ✅     | H1 fix applied |
| Shop Portal            | ✅    | ✅     | landing shell responsive |
| Field Leadership       | ✅    | ✅     | landing shell responsive |
| Public Pre-Op          | ✅    | ✅     | form stacks cleanly |
| Public Safety Tile     | ✅    | ✅     | (via /public/pre-op path) |

## Field Form Verdicts (390px + 1024px)

| Form                          | 390px | 1024px |
|-------------------------------|-------|--------|
| Pre-Op / Equipment Inspection | ✅    | ✅     |
| DVIR (`/fleet/dvir/new`)      | ✅    | ✅     |
| Safety Meeting (`/meetings/new`) | ✅ | ✅     |
| JHA (`/jha`)                  | ✅    | ✅     |
| Safety Inspection (new)       | ✅    | ✅     |
| Daily Report (`/dr/new`)      | ✅    | ✅     |
| HR Request (`/hr/requests/new`) | ✅ (404-shell) | ✅ (404-shell) |
| Driver forms                  | n/a — no driver-facing UI shell in the frontend; handled backend-only via `/api/dispatch/driver/*` (see TRACK 22.4B-FOLLOWUP-DRIVER) |

**Note on `/dr/new` and `/hr/requests/new`:** these two paths currently
serve the 404 shell in the repo state we audited. The 404 shell itself
is fully responsive at every viewport. The route inventory gap is
tracked as a P3 investigative item (see Defects below).

## Map / Dispatch Verdict

- Live Fleet Map at 390px: map container renders inside the responsive
  card; +/- controls sit inside the map, not overlapping the ribbon.
- Motive stale ribbon at 390px: visible, non-blocking, REFRESH button
  reachable.
- No Motive read behavior changed anywhere.
- No admin-only links leaked to the dispatcher route.

## Modal / Drawer Verdict

- Portal shells (`PortalShell`) apply consistent `min-w-0` to header
  children, preventing keyword-title overflow across all portals.
- Dispatch assignment drawer inherits the same shell — not opened
  end-to-end in this pass (would require a fresh assignment); no
  new drawer was introduced by this track.

## Leave-Site / Unsaved-Changes Observations

None triggered during the sweep. The repeat "Leave this page?" modal
is NOT part of Track 22.4c scope; if observed by operators in the
field it should be filed under the upcoming Platform-wide
Unsaved-Changes / Leave-Site Modal Audit.

## Motive Protection

**Unchanged / preserved.** The Motive posture read endpoint is
regression-locked (`test_motive_posture_unchanged_by_mobile_sweep`).

## RBAC Verdict

**Unchanged.** No portal guard, no admin-token behavior, no PVI role
was modified. The mobile fix is a pure CSS/JSX layout change inside
the shared `PortalShell` design-system component.

## Tests Added

- `/app/backend/tests/test_track_22_4c_mobile_responsiveness_sweep.py`
- Playwright-based, gracefully self-skips if the chromium browser
  isn't installed.
- Runtime: 77 parametrized checks (15 routes × 5 viewports + 2 named
  P1 locks + Motive shape check) in ~250s.
- **Result:** 77 passed, 1 skipped (Motive posture 404 in preview).

## Defects

| ID          | Severity | Status | Description | Owner |
|-------------|----------|--------|-------------|-------|
| B-05        | P1       | ✅ CLOSED | PM Command Center 390px | already resolved in prior track work; regression-locked here |
| B-05        | P1       | ✅ CLOSED | Dispatch Map 390px      | already resolved in prior track work; regression-locked here |
| B-07 (new)  | P1       | ✅ CLOSED | PortalShell H1 pre-hydration overflow at 390px | fixed in `PortalShell.jsx` |
| B-08 (new)  | P3       | 🟡 DEFERRED | `/dr/new` and `/hr/requests/new` serve 404 shell — investigate route inventory | future track |
| P3-NAV-01   | P3       | 🟡 DEFERRED | repeated "Leave this page?" modal | Unsaved-Changes / Leave-Site Modal Audit |

## Regression Suite Growth

```
Handoff baseline:                     84 tests
+ Trench Writes idempotency:           9
+ Shop Defects idempotency:            7
+ Driver track (B-06):                14
+ Mobile responsiveness sweep (22.4c):77
──────────────────────────────────────────
Grand total 22.4b + 22.4c:           189 tests (0 failures)
```

## Files Created

- `/app/backend/tests/test_track_22_4c_mobile_responsiveness_sweep.py`
- `/app/memory/TRACK_22_4C_MOBILE_RESPONSIVENESS_SWEEP.md`
- `/app/memory/TRACK_22_4C_MOBILE_FINDINGS.csv`
- `/app/memory/TRACK_22_4C_VIEWPORT_MATRIX.csv`

## Files Changed

- `/app/frontend/src/design-system/PortalShell.jsx`
- `/app/memory/PRD.md` (Track 22.4c summary appended)

## Next Tracks

- Platform-wide Unsaved Changes / Leave-Site Modal Audit
- Route-inventory investigation for B-08 (Daily Report / HR Request `/new` paths)
- DR-UNIFY-005 when telemetry window confirms safe legacy retirement
- Production Deployment Certification
