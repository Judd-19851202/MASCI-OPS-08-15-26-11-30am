# TRACK 15.86 CONTINUOUS BROWSER SMOKE REGRESSION GATE

Date: 2026-08-11
Status: ACTIVE PRE-SAVE GATE

## Purpose

- Preserve the continuous browser smoke gate shape for certified routes.
- Keep high-signal landings covered: Public Safety, Admin, and Operations Map.
- Keep the extended route family inventory aligned with Track 15.85 portal certification.

## Current gate posture

- Runner file remains at `backend/tests/browser_smoke/run_browser_smoke.py`.
- Gate and extended route lists remain mounted in the app routing shell.
- Required breakpoints remain 390x844, 768x1024, and 1024x768, with extended laptop and desktop coverage.
- Forbidden-string, overflow, blank-page, hydration-warning, console-error, and page-error assertions remain mandatory.

## Routes covered

- Gate routes: Public Safety, Admin, Operations Map.
- Extended routes: dispatch portal, dispatch map, operations map, shop, PM, leadership, HR, safety portal, trench safety, public forms, admin deep links, and notifications.

## Breakpoints

- Gate: 390x844, 768x1024, 1024x768.
- Extended: includes laptop and desktop coverage in addition to the gate breakpoints.

## Assertions

- No 404.
- No blank page.
- No horizontal overflow.
- No hydration warnings.
- No console errors.
- No uncaught page errors.
- No forbidden scaffold / placeholder strings.

## Deployment gate

- The browser smoke meta-gate is wired into the deployment gate as a required regression lock.

## How to run

- Meta-tests: `python3 -m pytest -q backend/tests/test_track_15_86_browser_smoke_gate.py`
- Runner: `python3 backend/tests/browser_smoke/run_browser_smoke.py --gate --base-url <preview-url> --json`

## Pre-save note

- This ledger documents the governed regression gate only.
- Fresh pre-save Product Quality and browser QA must still complete against the stabilized preview workspace before owner Save.