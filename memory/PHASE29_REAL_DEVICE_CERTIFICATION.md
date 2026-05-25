# PHASE 29 · Real-Device Certification Matrix
## iter431 · 2026-05-25 · OPERATOR-OWNED

This matrix is the formal real-world device certification list for
the MASCI Operations Platform. The coding agent CANNOT execute
WebAuthn ceremonies on physical hardware — every row below is
operator-driven and must be ticked manually against shipping devices.

Refer to `PHASE28_2_REAL_DEVICE_VALIDATION.md` for the per-row
"how to verify" runbook. Phase 29 adds:
  - explicit OS coverage (Windows / macOS / iPadOS / Android)
  - rugged-Android-tablet column (if available)
  - the new Operational Moments Rail row

## Mobile

| Workflow                                  | iPhone Safari | iPhone Chrome | iPad Safari | Android Chrome | Samsung Internet | Rugged Android |
|-------------------------------------------|---------------|---------------|-------------|----------------|------------------|----------------|
| Password login                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Passkey login                             | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Passkey enroll (admin/profile)            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Passkey remove                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| MFA challenge flow                        | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Logout / login persistence                | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Assignment issue (dispatch)               | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Reassignment                              | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Lifecycle change buttons                  | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Breakdown flow                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Attachment upload (camera)                | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Operational Moments Rail renders          | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Driver QR flow                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Driver shift start                        | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Driver lifecycle transitions              | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Offline queue replay                      | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Breakdown photo upload                    | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Shop · `waiting_on_parts`                 | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Shop · `operational_test`                 | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Shop · `returned_to_service`              | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| PM · haul awareness                       | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| EN ↔ ES toggle                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Touch targets ≥ 44 px                     | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Keyboard overlap                          | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Sticky headers                            | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Viewport scaling (no horizontal scroll)   | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| Camera permission grant                   | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |
| R2-backed image fetch                     | ☐             | ☐             | ☐           | ☐              | ☐                | ☐              |

## Desktop

| Workflow                                  | Chrome Win | Edge Win | Safari Mac | Firefox Win | Firefox Mac |
|-------------------------------------------|------------|----------|------------|-------------|-------------|
| Password login                            | ☐          | ☐        | ☐          | ☐           | ☐           |
| Passkey login (Hello / Touch ID)          | ☐          | ☐        | ☐          | ☐ N/A       | ☐ N/A       |
| Passkey enroll                            | ☐          | ☐        | ☐          | ☐ N/A       | ☐ N/A       |
| Passkey remove                            | ☐          | ☐        | ☐          | ☐           | ☐           |
| Dispatch assignment issue / reassign      | ☐          | ☐        | ☐          | ☐           | ☐           |
| Operational Moments Rail renders          | ☐          | ☐        | ☐          | ☐           | ☐           |
| Attachment upload (file picker)           | ☐          | ☐        | ☐          | ☐           | ☐           |
| R2-backed image fetch                     | ☐          | ☐        | ☐          | ☐           | ☐           |
| Admin · persistence-health curl           | ☐          | ☐        | ☐          | ☐           | ☐           |
| Admin · storage-summary curl              | ☐          | ☐        | ☐          | ☐           | ☐           |
| Admin · weekly-digest GET                 | ☐          | ☐        | ☐          | ☐           | ☐           |
| Admin · stability sweep dry-run           | ☐          | ☐        | ☐          | ☐           | ☐           |
| EN ↔ ES toggle                            | ☐          | ☐        | ☐          | ☐           | ☐           |

## Operating systems

Cross-row matrix · same workflows above re-verified on each OS:

| OS          | Mark `✅` once an explicit pass-sweep has been done |
|-------------|-----------------------------------------------------|
| Windows 10  | ☐                                                   |
| Windows 11  | ☐                                                   |
| macOS 14+   | ☐                                                   |
| iPadOS 17+  | ☐                                                   |
| iOS 17+     | ☐                                                   |
| Android 13+ | ☐                                                   |
| Android 14+ | ☐                                                   |

## Operational findings (filled in by operator)

| Date | Device / OS | Workflow | Finding | Resolved? |
|------|-------------|----------|---------|-----------|
|      |             |          |         |           |

## Doctrine notes
- Any single row failure blocks production confidence for that
  device. File the failure as the next operational moment.
- Sweep-all-green gates wider production rollout (more drivers,
  more PMs, more shops).
- Sentry should auto-attach `portal/role/route/device/browser/
  language/tenant` tags to any errors surfaced during testing — if
  a tag is missing, file it as a Phase 30 observability bug.
