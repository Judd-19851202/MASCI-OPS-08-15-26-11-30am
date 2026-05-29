# Field Reliability Test Matrix

_Phase V.3 · Wave-2 · 2026-05-29 · Daily Report._

> This matrix exists to verify "Nothing lost" across the 15 reliability scenarios mandated in the Wave-2 directive. **A green row is acceptance criteria for that scenario; a red row blocks pilot.**

## 1 · How to run

Each scenario has two tiers:

| Tier | What it is | Where it runs |
|---|---|---|
| **A · Playwright probe** | Headless browser automation that exercises the autosave / queue / restore code paths in a deterministic environment | `tests/pw_suite/test_dr_field_reliability.py` (TO BE AUTHORED · scaffolding in §3 below) |
| **B · iPad walk** | Operator running the scenario on a real iPad against the preview URL with a realistic project | Manual · checklist below |

Both tiers MUST pass before the operator authorizes pilot scoping.

## 2 · The 15 scenarios

| # | Scenario | Tier A (automated probe) | Tier B (iPad walk) | Acceptance |
|---|---|---|---|---|
| 1 | Browser refresh mid-report | `page.reload()` after filling form → `DraftRestorePrompt` appears → Restore → all fields including `production[]` + `constraints[]` round-trip | Fill 3 production rows + 1 weather delay → tap browser refresh → confirm "Draft restored" → confirm all fields present | 100 % restore · 0 lost rows |
| 2 | Browser close mid-report | dispatch `pagehide` then re-`page.goto()` → confirm IDB envelope contains last typed value | Type the prepared-by field → close Safari → reopen → confirm restore prompt appears | Restore prompt offered · all fields intact |
| 3 | Browser crash simulation | force-kill the page via `page.crash()` → re-`page.goto()` → confirm IDB still has the envelope from the last 10 s forced flush | n/a (cannot reliably crash Safari on demand) | Worst-case data loss bounded to ≤ 10 s |
| 4 | iPad sleep | `visibilitychange → hidden` → wait → `visible` → confirm autosave fired on hidden transition | Lock the iPad mid-form for 5 min → wake → confirm fields intact | 100 % round-trip · `draft.lifecycle` telemetry shows `visibilitychange` trigger |
| 5 | Offline report creation | `context.set_offline(True)` → fill form → confirm autosave still writes to IDB (no network needed) | Toggle airplane mode → fill production + delays → confirm draft pill shows "Saved" | All fields persisted offline |
| 6 | Offline photo capture | offline + `PhotoUpload` action → confirm photo dataURL lands in `data.photos[]` → confirm autosave includes it | Airplane mode · take 6 photos · confirm previews render | Photos in IDB envelope |
| 7 | Offline submit | offline + submit button → `enqueueUpload` fails first attempt → entry persists to `masci.resiliency.queue.v1` → toast "Saved · will upload when reconnected" | Airplane mode · tap Submit · confirm toast appears | Queue entry present in IDB |
| 8 | Weak network throttling | `route.continue({ delay: 3000 })` on `/daily-reports` → submit → first attempt times out → enters retry queue → backoff fires | Throttle to "Slow 3G" in Chrome DevTools · submit · confirm backoff visible | At most 5 retries · then `failed` status if no 2xx |
| 9 | Multi-photo upload interruption | n/a (DR path A — photos are inline, not a separate upload) | Add 20 photos · toggle offline mid-compress · confirm no half-state | All compressed photos persist · in-progress photo retried client-side |
| 10 | Reconnect after outage | offline submit (queued) → `context.set_offline(False)` → `online` event fires → queue auto-drains → 2xx received → `commit()` called | Airplane mode · submit · re-enable wifi · confirm "Daily report filed" toast within 30 s | 2xx within 30 s of reconnect · IDB draft cleared |
| 11 | Recovery after restart | `page.close()` mid-queue → re-open `page` → `enqueueUpload` queue loads from IDB on mount of `resiliencyQueue` → drain fires on `focus` | Submit offline · close Safari · reopen · confirm queue drains | Drain on next focus · 2xx received |
| 12 | Recovery after refresh | covered by scenario 1 | covered by scenario 1 | covered by scenario 1 |
| 13 | Recovery after browser relaunch | covered by scenario 2 + 11 | covered by scenario 2 + 11 | covered by scenario 2 + 11 |
| 14 | Duplicate submit prevention | submit twice in rapid succession with same `idempotencyKeyRef.current` → backend honors `Idempotency-Key` → only one DR created | Tap Submit · before navigation completes, tap Submit again · confirm only one DR appears in the list | DR count increments by exactly 1 |
| 15 | Duplicate photo prevention | n/a (DR path A — photos are an array inside the envelope; idempotency key on the envelope ensures at most one envelope is created) | submit with 6 photos · refresh during drain · re-submit · confirm DR has 6 (not 12) photos | photo count = 6 |

## 3 · Tier-A scaffolding (Playwright probe — TO BE AUTHORED on operator authorization)

A standalone Playwright probe file `tests/pw_suite/test_dr_field_reliability.py` is the recommended next implementation step **but is deferred** — the iter440 engine has zero schema coupling so this matrix can be exercised today via the existing Playwright smoke I already used to verify Wave-2 (see `OFFLINE_HARDENING_IMPLEMENTATION_REPORT.md §4`). The scaffolding below documents the recipe for the future authoring pass:

```python
async def test_S1_refresh_round_trip(page, base_url):
    # Open /daily/new
    # Fill project_name + prepared_by + 3 production rows + 1 constraint row
    # Force visibilitychange flush
    # Assert IDB has the envelope (production_count == 3, constraints_count == 1)
    # page.reload()
    # Wait for DraftRestorePrompt
    # Click Restore
    # Assert form state matches what was typed

async def test_S7_offline_submit_queues(context, page, base_url):
    # Fill form
    # await context.set_offline(True)
    # Click Submit
    # Assert toast "Saved · will upload when reconnected"
    # Assert IDB[masci.resiliency.queue.v1] has 1 entry with idempotencyKey

async def test_S10_reconnect_drains(context, page, base_url):
    # Pre-state: 1 queued entry from S7
    # await context.set_offline(False)
    # Wait for online event drain
    # Assert toast "Daily report filed"
    # Assert IDB queue empty

async def test_S14_duplicate_submit_prevention(page, base_url, idempotency_dedup_check):
    # Fill form
    # Click Submit twice in 200 ms
    # Backend should see two POSTs with the same Idempotency-Key
    # idempotency_dedup_check fixture asserts DR count incremented by 1
```

## 4 · Tier-B operator checklist (iPad walk)

> Print or screen-pin this list on the iPad before the field session.

```
☐ S1  Refresh mid-report                 → "Draft restored" → all fields present
☐ S2  Close Safari mid-report             → reopen → "Draft restored" → fields intact
☐ S3  Force-kill Safari                   → reopen → restore offered (loss bounded ≤10s)
☐ S4  iPad sleep / lock mid-report        → wake → all fields intact
☐ S5  Airplane mode · fill form           → "Saved" pill on every section
☐ S6  Airplane mode · take 6 photos       → all 6 previews render
☐ S7  Airplane mode · tap Submit          → "Saved · will upload when reconnected"
☐ S8  Slow-3G · submit                    → backoff visible · eventually succeeds
☐ S9  Add 20 photos · toggle offline mid  → all compressed photos kept · no half-state
☐ S10 Re-enable wifi after S7             → "Daily report filed" within 30 s
☐ S11 Close Safari mid-queue              → reopen → drain on focus → 2xx
☐ S12 covered by S1
☐ S13 covered by S2 + S11
☐ S14 Submit twice in rapid succession    → exactly one DR appears
☐ S15 Submit with 6 photos · refresh ·    → DR has 6 photos, not 12
       resubmit during drain
```

Each checkbox must be observed and ticked. Any unchecked or amber row blocks pilot.

## 5 · Acceptance criteria

| Criterion | Value |
|---|---|
| Scenarios 1–15 all green | required |
| Lost photos | 0 |
| Lost reports | 0 |
| Duplicate reports | 0 |
| Duplicate photos | 0 |
| Worst-case data loss bound | ≤ 10 s (driven by `MAX_INTERVAL_MS`) |

## 6 · Stop condition

🛑 The 15-row matrix is the authoritative gate before pilot. Until every row is green on a real iPad in a realistic project, pilot scoping does not begin.

---

_End of FIELD_RELIABILITY_TEST_MATRIX.md._
