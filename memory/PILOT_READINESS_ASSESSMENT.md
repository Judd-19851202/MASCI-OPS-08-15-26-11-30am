# Pilot Readiness Assessment

_Phase V.2 · Wave-1C · 2026-05-29 · operator decision gate for first crew pilot._

> **This assessment is the official gating document between
> Wave-1C closure and pilot authorization.** Until every gating
> criterion in §5 is explicitly satisfied, no pilot crew is
> onboarded.

---

## 1 · TL;DR

| Status | Position |
|---|---|
| 🟢 Architecture · backend · audit · UI surface | Ready |
| 🟡 Automated offline test coverage | Partial (1 of 7 acceptance criteria covered) |
| 🟡 Field-truth probe | Not yet exercised under real weak-signal conditions |
| 🛑 Pilot authorization | **NOT GRANTED** until §5 criteria are explicitly verified |

We are **architecturally ready** but **not yet field-ready**. The
gap is field-truth verification + 5 automated tests that simulate
the real low-signal field conditions a pilot crew will encounter.
Estimate to close: **~2.25 dev-days**.

## 2 · What IS ready

| Layer | Evidence |
|---|---|
| Backend write path | `POST /api/daily-reports` restored · idempotent · 410 DELETE preserved |
| Backend structured data | `production[]` + `constraints[]` shipped · 7-unit and 11-type closed enums |
| Advisory derivation | server-side · deterministic · operator-defined heuristic locked |
| Audit envelope | SHA256 stamped at insert · footer endpoint live |
| PDF audit footer | renders on every page of every DR PDF (Wave-1C) |
| Frontend UI | production card + constraint chip selector inside existing form |
| PM exposure tile | drop-in component + aggregator endpoint live |
| Test surface | 89 / 89 pytest passing · 0 governance probe failures |
| Doctrine inheritance | Lock #1 + Lock #2 preserved · 9-step contract locked |
| Historical preservation | M1 freeze invariant intact (count never decreases via DELETE) |

## 3 · What is NOT YET ready (the gap to pilot)

| # | Item | Type | Effort | Pilot blocker? |
|---|---|---|---|---|
| 1 | Service-worker POST queue formalization | infra | ~0.5 dev-day | YES |
| 2 | Visible "X drafts queued · will sync" banner | UI | ~0.25 dev-day | YES (operator visibility) |
| 3 | Recovery telemetry events (`draft_resumed`, `offline_submit_queued`, `photo_retry_settled`) | telemetry | ~0.25 dev-day | YES (acceptance criteria) |
| 4 | Automated kill-mid-typing Playwright harness | test | ~0.5 dev-day | YES (acceptance criteria) |
| 5 | Automated throttled-network Playwright harness (50 kbps) | test | ~0.5 dev-day | YES (acceptance criteria) |
| 6 | 24 h photo retry lifecycle test | test | ~0.25 dev-day | YES (acceptance criteria) |
| 7 | First-foreman preview submit on real weak signal | field validation | n/a (operator coordinates) | YES |

**Total: ~2.25 dev-days of automated work + 1 field session.**

## 4 · Risk surface · what could go wrong in pilot

| Risk | Severity | Mitigation |
|---|---|---|
| Foreman taps Submit on weak signal · spinner hangs · they retry | HIGH | Idempotency-Key prevents double submit (locked) |
| Browser tab killed mid-typing · 30 min of work lost | HIGH | localStorage auto-save (2 s debounce) recovers; field-truth verification needed |
| 5 photos enqueued offline · only 2 sync | HIGH | Photo retry queue exists; 24 h lifecycle test needs to run |
| Foreman sees a destructive error on submit failure | MEDIUM | UI surfaces "queued" banner (item 2 · deferred) |
| PM doesn't know that signals are signals (interprets as alerts) | LOW | Tile copy explicit: "Signal only · no actions taken" |
| External auditor questions PDF integrity | LOW | Audit footer + endpoint provide one-call verification |
| Historical data corrupted | LOW | M1 DELETE freeze · `test_legacy_row_count_only_grows_via_post` 🟢 |

## 5 · Gating criteria for pilot authorization

Pilot may NOT begin until all 7 of these are explicitly satisfied
and acknowledged by the operator.

| # | Criterion | Status |
|---|---|---|
| 1 | Kill-browser test: 5 mid-step kills · all recover the draft | ⏳ |
| 2 | Throttle test: submit at 50 kbps · queue holds 10 min · settles on reconnect | ⏳ |
| 3 | Photo retry test: 5 photos enqueued offline · all settle within 24 h | ⏳ |
| 4 | Idempotency test: double-tap submit during weak signal · only 1 row created | ✅ `test_idempotent_post` 🟢 |
| 5 | Telemetry: `draft_resumed` event observable within 24 h | ⏳ |
| 6 | Telemetry: `offline_submit_queued` event observable within 24 h | ⏳ |
| 7 | Field test: ≥ 1 foreman submits successfully on weak/no signal during preview | ⏳ |

**Status: 1 of 7 met.**

## 6 · Recommended next-wave scope

The smallest possible move that gets us pilot-ready:

| Wave | Items | Effort |
|---|---|---|
| **Wave-1D (pilot-prep)** | items 1–6 from §3 | ~2.25 dev-days |
| **Wave-1E (pilot)** | item 7 + first crew live · operator coordinates · monitored for 1 week | n/a |

Total dev work to pilot-ready: **~2.25 days** + 1 coordinated
field session.

## 7 · Out-of-scope for pilot (locked behind separate authorization)

| Capability | Status |
|---|---|
| RFI module | locked behind RFI authorization |
| Schedule module | locked behind schedule authorization |
| P6 integration | locked behind P6 authorization |
| Production deploy beyond preview | locked behind deploy authorization |
| Cross-portal consistency probe graduating from advisory to enforced | optional · operator decision |

## 8 · Operator-facing one-liner

> **Architecturally we are pilot-ready. Field-truth we are not.**
> The gap is ~2 dev-days of automated tests + telemetry + a small
> service-worker formalization, plus one real foreman trying it on a
> real construction site under real weak-signal conditions. Once
> those 7 criteria turn green, pilot can begin.

---

_End of PILOT_READINESS_ASSESSMENT.md._
