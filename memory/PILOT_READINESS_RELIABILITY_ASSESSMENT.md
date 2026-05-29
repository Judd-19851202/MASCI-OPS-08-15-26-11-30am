# Pilot Readiness · Reliability Assessment

_Phase V.3 · Wave-2 · 2026-05-29 · Daily Report._

> This document supersedes `PILOT_READINESS_ASSESSMENT.md` (Wave-1B/1C) for the **reliability axis only**. The original assessment covered Daily Report content / UX gates; this one covers offline / recovery / sync. Both must land green before pilot scoping begins.

## 1 · Reliability axis status

| Surface | Wave-2 status |
|---|---|
| Autosave (`useFormDraft`) | 🟢 iter440 engine · zero schema-bump gaps |
| Restore prompt (`DraftRestorePrompt`) | 🟢 verified live with `production[]` + `constraints[]` round-trip |
| Photo resiliency (Path A — inline) | 🟢 photos ride the envelope · single atomic submit |
| Offline submit queue (`resiliencyQueue`) | 🟢 MAX_TRIES=5 · exponential backoff · `online` + `focus` auto-drain |
| Idempotency keys | 🟢 client mint + IDB persistence + 24 h backend TTL |
| Recovery telemetry | 🟢 `/api/draft-telemetry` · 7-event taxonomy mapped to operator's 5 mandated signals |
| Sync reconciliation | 🟢 single-author / single-device / append-only doctrine eliminates merge surface |
| Quota awareness | 🟢 80 % warning chip · QuotaExceededError surfaces truthfully |
| Cross-token migration | 🟢 device-scoped actor id · one-time idempotent re-key |
| Field Reliability Test Matrix | 🟡 15-scenario matrix published · awaiting iPad walk and Playwright probe authoring |

🟢 = engine confirmed · 🟡 = awaiting field validation.

## 2 · Open risks (before pilot authorization)

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | Tier-B iPad walk of all 15 scenarios NOT YET PERFORMED in a realistic project on real cellular signal. | MEDIUM | Operator-led iPad session using the checklist in `FIELD_RELIABILITY_TEST_MATRIX.md §4`. |
| R2 | Tier-A Playwright probe file `tests/pw_suite/test_dr_field_reliability.py` is scaffolded but not authored. | LOW | One-day engineering follow-up. Existing Wave-2 smoke probe (in `OFFLINE_HARDENING_IMPLEMENTATION_REPORT.md §4`) already exercises the round-trip path. |
| R3 | iOS Safari edge cases (extension upgrade mid-session · private-browsing IDB quota differences) NOT YET CHARACTERIZED. | LOW-MEDIUM | Tier-B walk on the actual iPad fleet will surface this. |
| R4 | Backend `Idempotency-Key` 24 h TTL is correct for the offline queue's 31 s max retry window, but should be doctrine-locked in writing. | LOW | Documented in `OFFLINE_SUBMISSION_QUEUE_CERTIFICATION.md §3 + §6`. |
| R5 | Cross-foreman draft-restore on a shared iPad — current behavior shows a cross-token warning banner, but the prompt copy may be improved. | LOW | UX wording can be revised after the iPad walk surfaces real foreman feedback. |
| R6 | No service-worker uplift means a fully-closed iPad with no foreground tab cannot retry a queued submit until the foreman reopens the app. | KNOWN-AND-ACCEPTED | Operator authorized this scope: _"Do not introduce Service Worker / Background Sync in this wave."_ The drain fires on `focus` of the app's next open. |

🟢 No HIGH severity items.

## 3 · Acceptance criteria for pilot scoping authorization

Pilot scoping **may begin** when ALL of the following are simultaneously true:

| Gate | State today |
|---|---|
| Wave-1B/1C closure accepted by operator | ✅ |
| Section 03 cleanup accepted by operator | ✅ |
| Weather Impact cleanup accepted by operator | ✅ |
| Auto-Expand Guidance accepted by operator | ✅ |
| FL Role Standardization mappings confirmed by operator | 🟡 (4 uncertain rows in `LEGACY_ROLE_MAPPING_REVIEW.md`) |
| Internal Superintendent Validation Review walked on real iPad | 🟡 (3 scenarios documented · not yet walked) |
| Wave-2 Audit-and-Certify accepted by operator | 🟡 (this document) |
| Field Reliability Test Matrix Tier-B walk: 15/15 green | 🟡 (matrix published · not yet walked) |
| Operator explicit authorization | 🛑 not granted |

## 4 · What pilot scoping looks like once authorized

(Not in scope today · documented here so the operator can see the runway.)

1. Cohort selection — 1 project · 1 superintendent · 2-3 foremen.
2. Success scorecard — 15-scenario reliability + 9-step contract preservation + zero data loss claim.
3. Rollback plan — feature-flag-style switch to revert auto-expand + role pickers + structured production/constraints in a single click.
4. Daily check-in — operator sees `/api/draft-telemetry` reliability metrics for the cohort.
5. Pilot exit criteria — operator-defined.

## 5 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Reliability before expansion | ✅ this wave does only reliability |
| No new features | ✅ |
| No pilot · no RFI · no Schedule · no P6 | ✅ |
| Protect the data | ✅ engine certified |
| Protect the photos | ✅ engine certified |
| Make MASCI Ops field-proof | 🟡 awaiting Tier-B iPad walk |

## 6 · Stop condition

🛑 **HALTED at end of Wave-2 Audit-and-Certify pass as directed.**

- ❌ NO Pilot · NO RFI · NO Schedule · NO P6
- ❌ NO PM Hub wiring · NO approval/rejection workflow
- ❌ NO Service Worker uplift in this wave
- ✅ Awaiting operator review of the 8 deliverables and the 15-scenario test matrix.

---

_End of PILOT_READINESS_RELIABILITY_ASSESSMENT.md._
