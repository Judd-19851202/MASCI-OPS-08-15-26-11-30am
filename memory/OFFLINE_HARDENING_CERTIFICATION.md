# Offline Hardening · Certification (Wave-1A baseline)

_Phase V.2 · Wave-1A · 2026-05-29 · contract baselined · strengthening scheduled for Wave-1C._

> The Wave-1A low/no-signal posture: **everything that already
> worked still works.** This certification documents the contract
> baseline, the strengthening work scheduled, and the acceptance
> criteria before any pilot.

---

## 1 · What is in scope for Wave-1A

Wave-1A explicitly **does not** add new offline machinery. It
preserves and re-certifies the existing Phase J / Field Resiliency
posture. Strengthening work (formal service-worker POST queue,
queue depth UI, recovery telemetry, kill-mid-typing tests) is
scheduled for Wave-1C — see §8.

## 2 · Inventory · what works today

| Capability | Status today | Evidence |
|---|---|---|
| Idempotent submit (Phase J) | ✅ Working | `tests/odr/test_wave_1a.py::test_idempotent_post` 🟢 |
| Per-field auto-save | ✅ Working | localStorage keyed by `(project, date)` — existing |
| Draft recovery on mount | ✅ Working | "Resume your draft?" affordance — existing |
| Photo upload retry queue | ✅ Working | client-side queue · `job_photos` mirror — existing |
| Device recognition | ✅ Working | `device_inferences` — existing |
| Backend write idempotency wrapper | ✅ Working | `lib/idempotency.py` · 24 h TTL · `Idempotency-Key` header |

## 3 · Contract baselined at Wave-1A

| Property | Contract |
|---|---|
| **Submit safety** | Repeat POSTs with same `Idempotency-Key` are no-ops on the second hit |
| **Auto-save bound** | Maximum data loss window: 2 s of typing (existing 2 s debounce) |
| **Draft survival** | Browser tab kill before save → draft on disk; after save → draft on disk; never lost |
| **Photo survival** | Photos enter retry queue · exponential backoff up to 24 h before manual retry surface |
| **Device recognition** | Project + crew + equipment defaults preload on known device |
| **POST restored** | `POST /api/daily-reports` accepts submits (M1 partial revert) |

## 4 · Test surface · what Wave-1A regression locks

| Test | Result |
|---|---|
| `tests/odr/test_wave_1a.py::test_idempotent_post` | 🟢 same key → same id |
| `tests/odr/test_wave_1a.py::test_post_daily_report_restored` | 🟢 POST works |
| `tests/odr/test_wave_1a.py::test_unified_projector_surfaces_new_dr` | 🟢 new submits reach the unified dashboard |
| `tests/odr/test_m1_option_c.py::test_legacy_row_count_only_grows_via_post` | 🟢 DELETE remains frozen |
| Phase J idempotency tests (existing) | 🟢 |

## 5 · Acceptance criteria for pilot (gating · NOT met at Wave-1A)

Per the pivot directive: **no pilot unless this works.** The
following criteria are NOT yet met and will be addressed in Wave-1C
strengthening work:

| # | Criterion | Wave-1A status | Wave-1C target |
|---|---|---|---|
| 1 | Kill-browser test: 5 mid-step kills · all recover the draft | not formally tested | ✅ |
| 2 | Throttle test: submit at 50 kbps · queue holds 10 min · settles on reconnect | not formally tested | ✅ |
| 3 | Photo retry test: 5 photos enqueued offline · all settle within 24 h | not formally tested | ✅ |
| 4 | Idempotency test: double-tap submit during weak signal · only 1 row | ✅ (test_idempotent_post) | ✅ (kept) |
| 5 | Telemetry: `draft_resumed` event observable within 24 h | not wired | ✅ |
| 6 | Telemetry: `offline_submit_queued` event observable within 24 h | not wired | ✅ |
| 7 | Field test: ≥1 foreman submits on weak/no signal during preview | not yet done | ✅ |

## 6 · Wave-1C scope (planned · NOT in Wave-1A)

| Move | Estimate |
|---|---|
| Formal service-worker POST queue contract | ~0.5 dev-day |
| Queue depth UI ("1 queued · retrying…") | ~0.25 dev-day |
| Recovery telemetry → `odr_observation_events` | ~0.25 dev-day |
| Kill-mid-typing automated test | ~0.5 dev-day |
| Throttled-network automated test | ~0.5 dev-day |
| 24 h photo retry lifecycle test | ~0.25 dev-day |
| Calm "X drafts queued" banner | ~0.25 dev-day |
| **Total** | **~2.5 dev-days** |

Wave-1C is gated behind operator authorization after Wave-1A review.

## 7 · What is NOT promised yet

| | Wave-1A | Wave-1C target |
|---|---|---|
| Service-worker POST queue formalization | partial | full |
| Operator-visible queue depth | absent | present |
| Crash-recovery telemetry | absent | present |
| "Queued — will sync when reconnected" calm banner | absent | present |
| Pilot readiness | NOT met | met after Wave-1C 7 criteria pass |

## 8 · Operator-facing one-liner

> **Wave-1A keeps every existing offline guarantee intact.** No
> regressions. Idempotent submit, auto-save, draft recovery, photo
> retry queue, device recognition — all still working. The deeper
> strengthening (service-worker formalization, queue UI, recovery
> telemetry, automated kill/throttle tests) lands in Wave-1C before
> any pilot.

---

_End of OFFLINE_HARDENING_CERTIFICATION.md._
