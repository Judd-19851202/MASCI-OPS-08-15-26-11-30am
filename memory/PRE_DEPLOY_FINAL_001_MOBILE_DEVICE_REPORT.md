# PRE-DEPLOY-FINAL-001 · MOBILE / DEVICE REPORT

**Scope-limitation up front:** real iPhone Safari, real iPad Safari (portrait + landscape), and Desktop Safari cannot be exercised from the agent environment. Only headless Chromium at one viewport is available.

## Devices the directive requires

| Device | Agent-capable | Tester action required |
|---|---|---|
| iPhone Safari | ❌ NO | Required: human pass |
| iPad Safari portrait | ❌ NO | Required: human pass |
| iPad Safari landscape | ❌ NO | Required: human pass |
| Desktop Chrome | 🟡 partial (headless Chromium at 1440×900) | Recommended: 1 sample run |
| Desktop Safari | ❌ NO | Recommended |

## Viewports the directive requires

| Viewport | Agent-capable | Tester action |
|---|---|---|
| 390×844 (iPhone) | ❌ NO | Required |
| 430×932 (iPhone Plus) | ❌ NO | Required |
| 768×1024 (iPad portrait) | ❌ NO | Required |
| 1024×768 (iPad landscape) | ❌ NO | Required |
| 1180×820 (iPad Pro landscape) | ❌ NO | Required |
| 1440×900 (Desktop) | ✅ verified headless | — |
| 1920×1080 (Desktop) | ❌ NO | Recommended |

## Network conditions
| Condition | Agent-capable | Notes |
|---|---|---|
| Normal connection | ✅ implicit | Sustained traffic with no errors |
| Slow 4G | ❌ NO | Browser throttling unavailable in this tool |
| Offline / reconnect | ❌ NO direct device test, but `resiliencyQueue` logic verified by unit tests (7/7 PASS) including offline-style flows |

## What WAS verified from the 1440×900 headless run

* Frontend builds without errors (no compile failures observed at backend restart, hot-reload working).
* Public Hub renders: preview banner clearly visible, MASCI eyebrow ("MASCI Operations Platform"), hero typography ("Run Every Job. Control Every Detail. Protect Everything."), three operational pillars (Field / QA-QC / Safety), language toggle (EN/ES), Sign-In CTA, "First week on the platform — start here" guide block, "Today in the Field" section.
* Title set: `MASCI Operations Platform`.
* Branding clean — no Emergent residue, no broken images, no overlapping text at 1440×900.
* No raw stack traces visible to users.

Screenshot of evidence is in this audit's playwright cache.

## Screens the directive requires verified on iPhone + iPad

| Screen | Agent status | Tester action |
|---|---|---|
| Public Hub | 🟢 1440×900 only | Required: 390 / 430 / 768 / 1024 / 1180 |
| Daily Report form | ❌ unverified | Required |
| Daily Report thank-you | ❌ unverified | Required |
| Queue popup (`QueueStatusPill`) | ❌ unverified visually; code-level: DR-QUEUE-RETRY-001 fix applied | Required |
| Safety forms | ❌ unverified | Required |
| QA/QC forms | ❌ unverified | Required |
| Job Photos | ❌ unverified | Required (especially folder grouping on tablet) |
| Admin Overview | ❌ unverified | Required |
| HR Employees | ❌ unverified | Required (preferred-name search on mobile is critical) |
| Time Verification | ❌ unverified | Required (print layout was previously a defect — HR-EMPLOYEE-002 follow-up) |
| Project Identity Governance | ❌ unverified | Required |
| Integration Center | ❌ unverified | Required |
| System Backups | ❌ unverified | Required |
| System Health | ❌ unverified | Required |

## Verdict
🟡 **DEFERRED** — single-viewport headless pass is clean; full multi-device certification requires the human QA the directive itself calls for in §2.
