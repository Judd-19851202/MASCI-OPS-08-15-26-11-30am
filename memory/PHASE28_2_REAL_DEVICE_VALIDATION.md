# PHASE 28.2 · Real-Device Validation Matrix
## iter430 · 2026-05-25 · OPERATOR-OWNED

> I (the coding agent) cannot drive physical iPhones / iPads / etc.
> This document is the runbook you (or any operator) execute against
> live preview / production on real devices.

## Matrix

| Surface           | iPhone Safari | iPad Safari | Android Chrome | Chrome Win | Edge Win | Mac Safari (Touch ID) | Firefox |
|-------------------|---------------|-------------|----------------|------------|----------|------------------------|---------|
| Passkey enroll    | ☐             | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐ N/A   |
| Passkey sign-in   | ☐             | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐ N/A   |
| Passkey remove (admin/profile) | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Attachment upload (camera) | ☐    | ☐           | ☐              | ☐ N/A      | ☐ N/A    | ☐ N/A                  | ☐ N/A   |
| Attachment fetch (image)   | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Recovery state update      | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Continuity event creation  | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Offline queue replay       | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| EN ↔ ES language switch    | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Coaching tooltips visible  | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Touch-target size (44 px+) | ☐    | ☐           | ☐              | N/A        | N/A      | N/A                    | N/A     |
| Sticky header behaviour    | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Keyboard overlap (input)   | ☐    | ☐           | ☐              | N/A        | N/A      | N/A                    | N/A     |
| R2 attachment fetch        | ☐    | ☐           | ☐              | ☐          | ☐        | ☐                      | ☐       |
| Backup trigger (admin)     | n/a  | n/a         | n/a            | ☐          | ☐        | ☐                      | ☐       |
| persistence-health (admin) | n/a  | n/a         | n/a            | ☐          | ☐        | ☐                      | ☐       |
| Storage-summary (admin)    | n/a  | n/a         | n/a            | ☐          | ☐        | ☐                      | ☐       |

Mark `☐` → tick `✅` or `❌` per device.

## How to verify (per row)

### Passkey ceremony
- Sign in with password once · accept the calm enrollment prompt
  ("Enable faster sign-in on this device?").
- Sign out · sign back in with passkey · confirm landed on correct
  portal.
- Navigate to `/admin/profile` (admin) · device must appear in
  "Your devices" list with a sensible label + last-used timestamp.
- Tap "Remove" · refresh · device must disappear · password sign-in
  must still work.

### Attachment camera path
- Open Dispatch / Field Leadership / Shop on iPhone.
- Tap an attachment upload affordance · take a photo with the live
  camera · confirm it appears in the assignment's attachment strip
  within ~3 s.
- Sample the new attachment on a desktop browser ·
  `inline_b64`-style or R2-backed both render via the same fetch
  endpoint.

### Offline queue replay
- Put device on airplane mode · perform a recovery-state update
  on Shop · take it off airplane mode within 60 s · confirm the
  state lands on Atlas (visible via Dispatch).

### Bilingual continuity
- Toggle EN ↔ ES from any hub header · confirm every operational
  string switches · no English fallback strings on ES side · no
  Spanish leak on EN side.

### persistence-health spot-check
- On a desktop, while signed in as admin: open browser console →
  `await fetch('/api/admin-strict/diag/persistence-health', { headers: { 'X-Admin-Token': localStorage.getItem('admin_token') } }).then(r=>r.json())`
- Expect `atlas_connected: true`, `mongo_version` present, recent
  `last_backup_time`.

## Pass / fail rule
- Any single row marked ❌ blocks production confidence for that
  device. File the failure mode as the next operational moment;
  surgical fix in the next phase.
- Sweeping "all green" gates the operator's confidence to widen
  production rollout (more drivers, more PMs, more shops).
