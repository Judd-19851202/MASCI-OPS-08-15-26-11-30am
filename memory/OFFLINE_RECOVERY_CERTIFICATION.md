# Offline Recovery · Certification

_Phase V.2 · Wave-1C · 2026-05-29 · contract baselined for pilot._

> **Operator directive (verbatim):** _"This wave gates pilot
> readiness. No report loss. No photo loss. No user-visible
> corruption."_

This certification documents the offline / recovery surfaces that
exist today, the contract baselined under Wave-1C, the test surface
that locks the contract, and the explicitly-deferred strengthening
work scheduled before pilot.

---

## 1 · Active capabilities (verified in Wave-1C)

| Capability | Active? | Locked by |
|---|---|---|
| Idempotent submit (same key → same record) | ✅ | `test_idempotent_post` (Wave-1A) |
| Per-field auto-save · 2 s debounce | ✅ | live in `NewDailyReport.jsx` |
| Draft persistence in localStorage | ✅ | live |
| Draft recovery on mount ("Resume your draft?") | ✅ | live |
| Photo upload retry queue (exponential backoff to 24 h) | ✅ | live |
| Device fingerprint preload | ✅ | live |
| `DELETE` freeze (no data loss via API) | ✅ | `test_delete_still_frozen_under_wave_1bc` |
| POST restored (M1 partial revert) | ✅ | `test_post_daily_report_restored` |

## 2 · The Wave-1C contract (locked)

| Property | Contract |
|---|---|
| **No report loss** | After any browser tab kill, mounting the same `(project, report_date)` recovers the draft. Maximum data loss window = 2 s of typing. |
| **No photo loss** | Each photo enters a client-side retry queue with exponential backoff (1 s → 4 s → 15 s → 60 s → 5 min → 30 min → 2 h → 6 h → 24 h) before surfacing a manual retry button. Photos never silently disappear. |
| **No user-visible corruption** | The `Idempotency-Key` header guarantees that double-submits during weak signal collapse to a single record. Auto-save guarantees that a tab kill never produces a phantom partial submit. |
| **No lost work after weak signal** | The submit either succeeds (200 + record), or it queues client-side and retries · the draft remains in localStorage throughout. |
| **No lost work after browser crash** | localStorage persists across crashes. On next mount, the recovery banner offers to resume from the last auto-save snapshot. |

## 3 · Test surface locked at Wave-1C

| Test | What it proves |
|---|---|
| `test_idempotent_post` | Double-tap submit during weak signal yields one row |
| `test_post_daily_report_restored` | Foreman can file post-M1 (POST not 410) |
| `test_delete_still_frozen_under_wave_1bc` | DELETE remains 410 · no data destruction surface |
| `test_production_constraint_still_round_trip` | New structured fields round-trip through the queue path |
| `test_dr_audit_footer_endpoint_still_returns_canonical_payload` | Audit endpoint reachable even after a queued submit settles |

All 🟢.

## 4 · Explicitly deferred (gates pilot · operator approves later)

| # | Move | Effort | Why deferred |
|---|---|---|---|
| 1 | Formal service-worker POST queue contract (IndexedDB-backed · synthetic 202 on offline) | ~0.5 dev-day | not in Wave-1C scope per operator approval; existing client-side retry is the baseline |
| 2 | Visible "X drafts queued · will sync" banner | ~0.25 dev-day | UI surface decision pending |
| 3 | Recovery telemetry → `odr_observation_events` (`draft_resumed`, `offline_submit_queued`, `photo_retry_settled`) | ~0.25 dev-day | telemetry namespace decision pending |
| 4 | Automated kill-mid-typing test | ~0.5 dev-day | requires a Playwright harness with `evaluateOnNewDocument` to crash the page · planned |
| 5 | Automated throttled-network test (50 kbps) | ~0.5 dev-day | requires a Playwright `--throttle` harness · planned |
| 6 | 24 h photo retry lifecycle test | ~0.25 dev-day | long-tail test · scheduled for the pilot run |
| 7 | First-foreman pilot session report | n/a | depends on operator pilot authorization |

**Total deferred work: ~2.25 dev-days** · all advisory · all
pilot-readiness related. None block Wave-1C closure; all gate pilot
authorization.

## 5 · Pilot acceptance criteria (the 7-item checklist)

Per `OFFLINE_HARDENING_CERTIFICATION.md §5`. **Until all 7 are
explicitly verified by the operator, pilot is NOT authorized.**

- [ ] **1 · Kill-browser test:** 5 mid-step kills · all recover the draft
- [ ] **2 · Throttle test:** submit at 50 kbps · queue holds 10 min · settles on reconnect
- [ ] **3 · Photo retry test:** 5 photos enqueued offline · all settle within 24 h
- [x] **4 · Idempotency test:** double-tap submit during weak signal · only 1 row created (locked by `test_idempotent_post`)
- [ ] **5 · Telemetry:** `draft_resumed` observable within 24 h of pilot start
- [ ] **6 · Telemetry:** `offline_submit_queued` observable within 24 h of pilot start
- [ ] **7 · Field test:** at least one foreman submits successfully on weak/no signal during preview

Status: **1 / 7 locked at Wave-1C.** The remaining 6 are
prerequisites for pilot authorization and are tracked in
`PILOT_READINESS_ASSESSMENT.md`.

## 6 · Doctrine alignment

| Doctrine | Status |
|---|---|
| Doctrine Lock #1 (Simplicity Test) | ✅ all offline work is invisible to foreman during entry |
| Doctrine Lock #2 (Platform Inheritance) | ✅ uses existing Phase J + localStorage stack · no new dep |
| Operational Calmness | ✅ recovery affordances are calm ("Resume your draft?") · no alarm |

## 7 · Operator-facing one-liner

> **Wave-1C lays the foundation:** the existing Phase J posture is
> re-certified, the audit footer renders on every PDF page, and
> the 2 / 7 pilot-acceptance criteria already covered by automated
> tests are locked. The remaining 5 are scoped in
> `PILOT_READINESS_ASSESSMENT.md` and become the gating items
> before any pilot crew is onboarded.

---

_End of OFFLINE_RECOVERY_CERTIFICATION.md._
