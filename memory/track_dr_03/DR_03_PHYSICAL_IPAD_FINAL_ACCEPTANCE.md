# DR-03 Physical iPad / Safari Final Acceptance

Status: DOCUMENTATION ONLY — NOT EXECUTED BY BUILDER

## Objective
- Validate the canonical Daily Report flow on a real iPad using Safari.
- Confirm the governed Production Certification Lane behaves correctly on a physical field device.
- Confirm no operational pollution, no broken autosave, and no misleading timeout states.

## Required operator inputs
- Production URL
- Controlled certification credentials
  - Foreman / field identity
  - PM / Co-PM verification identities if needed
- Controlled certification project number: `ZZ-RUNTIME-CERT-2026`
- Known expected routing recipients:
  - `cert.pm@example.com`
  - `cert.copm@example.com`

## Device preparation
1. Use a physical iPad, not desktop responsive mode.
2. Use Safari.
3. Ensure battery is sufficient for a 30–45 minute run.
4. Ensure Wi-Fi is stable at start.
5. Confirm camera permission and location permission prompts can be answered.

## Acceptance sequence
### A. Entry and identity
1. Open the production app in Safari.
2. Sign in only with the controlled certification field identity.
3. Confirm the login succeeds without redirect loops.

### B. Daily Report create flow
1. Open the canonical Daily Report create route.
2. Select or enter the controlled certification project `ZZ-RUNTIME-CERT-2026`.
3. Confirm the form loads and remains responsive.
4. Type into several fields and verify autosave indicators appear truthfully.

### C. Draft telemetry proof points
1. Change several fields.
2. Wait for autosave.
3. Confirm there are no visible frontend telemetry errors.
4. Navigate away and return.
5. Confirm draft restore works.

### D. AI / timeout behavior
1. Visit HR / Shop / Safety intelligence surfaces.
2. If intelligence loads, record normal state.
3. If intelligence times out, confirm the UI shows a truthful timeout state.
4. Confirm each timeout state offers Retry.
5. Confirm the parent page remains usable.

### E. Summary / submit
1. Complete minimum valid Daily Report content.
2. Use the canonical summary path.
3. If AI/manual summary is needed, complete it through the canonical flow only.
4. Submit the report.
5. Record the returned report number.

### F. Certification lane validation
1. Confirm the submission was accepted.
2. Confirm it does not leak into operational lists/search surfaces.
3. Confirm controlled certification routing is preserved for the report.
4. Confirm the viewer route and PDF route still work for the submitted report.

### G. Offline / recovery spot check
1. Create a second draft.
2. Briefly disable network.
3. Make an edit.
4. Re-enable network.
5. Confirm the draft recovers and the page stays stable.

## Pass criteria
- Login stable on iPad Safari
- Daily Report create route usable
- Autosave and restore truthful
- No visible telemetry 422/operator failure
- Timeout widgets are truthful and retryable
- Submission succeeds on the governed certification project
- Controlled certification submission does not pollute operational surfaces
- Viewer/PDF still function

## Record for evidence
- Timestamp of run
- Device model + iPadOS version
- Safari version
- Report number(s)
- Screenshots of autosave, timeout state, submit success, viewer, and PDF
- Exact routing recipient evidence if visible

## Failure handling
- If any failure occurs, capture:
  - route/page
  - exact time
  - screenshot
  - report number if one exists
  - whether the failure was recoverable with Retry