# Deployment Risk Report

**Batch:** OMEGA · Sprint Scheduler Hardening + UX Phase 1 · Pre-Deploy Risk Assessment
**Companion:** `GO_NO_GO_DECISION.md`
**Date:** 2026-06-01

---

## 1 · Headline

🟢 **Overall risk: LOW.** All changes are additive, surgically scoped, and individually rollback-safe. The most novel change (singleton-scheduler heartbeat now cancels its scheduler task on lock-loss) is covered by a dedicated regression test (`test_heartbeat_cancels_scheduler_on_lock_loss`) and is defense-in-depth — even if it regressed, the L2 `claim_slot` dedup at MongoDB level catches duplicates.

---

## 2 · Change inventory

| Domain | Surface | Risk class | Rollback path |
|---|---|---|---|
| Backend | `lib/singleton_scheduler.py` heartbeat cancels scheduler task on lock-loss | 🟡 Medium-Low (novel control-flow change) | Redeploy previous backend commit · scheduler_locks unchanged · no data migration |
| Backend | `lib/scheduler_runs.py` (new module) | 🟢 Low (additive) | New collection — drop or TTL-prune; new module unreferenced after rollback |
| Backend | `po_digest.py` / `safety_digest.py` / `lib/operator_digest.py` — wire `claim_slot` + `mark_completed` | 🟡 Medium-Low (changes the digest send path) | Rollback restores previous send path (no claim_slot call) |
| Backend | `routes/scheduler_runs_admin.py` (new admin route) | 🟢 Low (read-only · admin-gated) | Disappears with backend rollback |
| Backend | `server.py` startup hook adds `ensure_scheduler_runs_indexes` | 🟢 Low (idempotent) | Indexes can be left in place after rollback |
| Frontend | `HrPayrollVariance.jsx` per-row deep-link | 🟢 Low (additive cell content · target=_blank) | Re-deploy previous frontend bundle |
| Frontend | `HrTimeVerification.jsx` query-string acceptance | 🟢 Low (graceful degradation: no QS → defaults) | Same |
| Frontend | `HrHub.jsx` tile copy edit | 🟢 Low (string only) | Same |
| Frontend | `FieldLeadershipHub.jsx` + 2 tiles + new group | 🟢 Low (additive group · existing tiles unchanged) | Same |
| Frontend | `AdminSchedulerRuns.jsx` (new page) | 🟢 Low (admin-gated read-only) | Page disappears with rollback; if backend kept but frontend rolled back, no harm |
| Frontend | `AdminHub.jsx` new tile | 🟢 Low (additive) | Same |
| Frontend | `App.js` new route | 🟢 Low (additive) | Same |

---

## 3 · Risk-by-failure-mode

### 3.1 · The heartbeat cancel introduces a new cancellation point in the scheduler control flow

**Failure mode:** Cancel propagates further than expected → all scheduler tasks die on first heartbeat hiccup → no Monday digest fires at all.

**Mitigations:**
* The cancellation only fires when `_refresh_lock` returns False **and** the heartbeat detects ownership has been transferred. The poll loop will pick up the released lock within 60 s and start a fresh scheduler.
* `test_heartbeat_cancels_scheduler_on_lock_loss` asserts the scheduler is cancelled exactly when the lock is lost — not in the steady-state path.
* Existing `_seconds_until_next_send` slot math is untouched. The fresh scheduler computes the same target slot.
* `[singleton-lock]` logs make any cancel/restart event visible in supervisor logs.

**Residual risk:** 🟡 Medium-Low. Mitigated by the L2 dedup (worst case: orphan keeps firing → claim_slot returns None → no duplicate send).

### 3.2 · The `scheduler_runs` unique compound index could collide with operator-fired manual digests

**Failure mode:** A manual `/run-now` fire with the same slot_key as a scheduled fire could DuplicateKeyError out.

**Mitigations:**
* Manual fire paths (`/api/admin/po-digest/run-now`, `/api/admin/safety-digest/send-now`) do NOT call `claim_slot`. They are unaffected by the new collection. They continue to log to their existing `digest_runs` collection.
* `claim_slot` is invoked **only** from the scheduler loop, after `_seconds_until_next_send` math returns 0.

**Residual risk:** 🟢 Low. Verified by reading the diff.

### 3.3 · Frontend deep-link could pass user-supplied data into URL params

**Failure mode:** Employee name with special chars / quotes / `<script>` content → XSS or routing break.

**Mitigations:**
* `encodeURIComponent(r.employee_name)` is applied at the link source.
* Receiving page reads via `URLSearchParams.get()`, which percent-decodes safely.
* The value is bound to a React `useState` and rendered via React's default JSX escaping — no `dangerouslySetInnerHTML`.

**Residual risk:** 🟢 Low.

### 3.4 · Backup schedulers retain L1-only protection

**Failure mode:** A backup scheduler heartbeat-loss event could still produce a duplicate hourly backup run if L1 ever regresses.

**Mitigations:**
* `backup_runs` collection already exists and audits every backup. A duplicate would be visible.
* Each duplicate is at most cosmetic (an extra R2 archive at the same timestamp · ~few MB · safe to delete).
* `r2_degraded_events` are write-once-per-event; a duplicate would be a single redundant test row.

**Residual risk:** 🟢 Low (storage waste, not correctness).

### 3.5 · `scheduler_runs` TTL behavior in MongoDB

**Failure mode:** TTL index doesn't fire as expected → collection grows unbounded.

**Mitigations:**
* `ttl_at` is set explicitly to `started_at + 90 days` at write time.
* TTL index is `{ttl_at: 1}, expireAfterSeconds: 0`.
* Even without TTL eviction, ~5 fires/week × 90d = ~65 rows. Nominal storage impact.

**Residual risk:** 🟢 Low.

### 3.6 · Admin endpoint exposed without rate limit

**Failure mode:** A misconfigured client polls `/api/admin/scheduler-runs` aggressively → load on Mongo.

**Mitigations:**
* The endpoint is admin-gated (`X-Admin-Token` required).
* Mongo query is indexed on `(scheduler, started_at)`.
* The collection holds ≤200 rows under normal operation.

**Residual risk:** 🟢 Low.

---

## 4 · Pre-existing risks NOT addressed by this batch

| Carry-forward | Severity | Why deferred |
|---|---|---|
| Orphan `job_photos` documents (404 noise in batch validation) | 🟡 Medium | Out of scope · separate data-hygiene batch |
| R2 bucket at 92.38 GB (above 50 GB ALERT threshold) | 🟡 Medium | Out of scope · `R2_STORAGE_GOVERNANCE_REPORT.md` |
| RTO drill_runs activation on production dashboard | 🟢 Low | Operator-side step · `DR_DRILL_REPORT.md` §7 |
| accountability_projection.py PO-request resolver field pattern | 🟢 Low | Same defect class as Sprint 1F · deferred |
| Two parallel training-records surfaces (HR + Safety) | 🟢 Low | Medium-friction · UX Phase 2 |
| `/admin/dispatch` vs. dispatcher portal | 🟢 Low | Medium-friction · UX Phase 2 |

None of these are exacerbated by this batch.

---

## 5 · Operator deploy plan

| Step | Action | Verification |
|---|---|---|
| 1 | Standard backend redeploy (current code in `main`) | `/api/version` `source_hash` changes |
| 2 | Frontend redeploy (current bundle) | `/admin/scheduler-runs` 200 |
| 3 | Visit AdminHub | New amber "Scheduler Runs · Digest History" tile visible |
| 4 | Visit `/admin/scheduler-runs` | Empty state hint visible · `total: 0` |
| 5 | Wait for Monday 2026-06-08 14:00 UTC | First row appears post-fire |
| 6 | Confirm `recipients` count matches inbox | Single email per recipient · no duplicate |
| 7 | Confirm `dedup_attempts == 0` | No race triggered |

No new env vars. No new secrets. No schema migration. The `scheduler_runs` collection is created on first write; indexes ensured at backend startup.

---

## 6 · Rollback runbook

| Layer | Steps | RTO |
|---|---|---|
| Backend | Redeploy previous backend commit | < 5 min |
| Frontend | Redeploy previous frontend bundle | < 5 min |
| `scheduler_runs` collection | Safe to leave (TTL prunes in 90d). Optional `db.scheduler_runs.drop()`. | < 1 min |
| Locks (`scheduler_locks`) | Unchanged. No action needed. | n/a |
| Existing `digest_runs` | Unchanged. No action needed. | n/a |

Estimated full rollback wall-clock: **< 10 min**.

---

## 7 · Risk matrix

| Risk | Likelihood | Impact | Mitigation | Residual |
|---|---|---|---|---|
| Heartbeat cancel breaks scheduler steady state | Low | Medium (no digest) | Unit test + L2 backstop + visible logs | 🟢 Low |
| `claim_slot` blocks a legitimate first-send | Very Low | High | Tests prove first send always wins | 🟢 Very Low |
| `scheduler_runs` collection growth | Very Low | Low | TTL + nominal volume | 🟢 Very Low |
| Frontend deep-link XSS | Very Low | High | encodeURIComponent + React escaping | 🟢 Very Low |
| Backup duplicate (cosmetic) | Low | Very Low | `backup_runs` audits | 🟢 Very Low |
| AdminSchedulerRuns route conflict | Very Low | Low | Distinct path under `/admin/` | 🟢 Very Low |
| Bilingual string rendering bug | Very Low | Low | Existing `useT` pattern reused | 🟢 Very Low |
| Per-Day Detail link breaks Time Verification default flow | Very Low | Low | No-QS path falls back to defaults | 🟢 Very Low |

---

## 8 · Deploy windows

| Window | Suitability |
|---|---|
| Any weekday between 09:00–17:00 ET | 🟢 Preferred (operator on-call) |
| Friday afternoon | 🟡 Acceptable (no Monday-impacting risk; first Monday fire is still 3 days out) |
| Within 24h of Monday 14:00 UTC | 🔴 Avoid (the first Monday fire post-deploy is the highest-value observation moment; cushion of ≥48h preferred) |

**Recommended:** Tue–Wed daytime ET.

---

## 9 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Risk inventory enumerated | ✅ |
| Rollback runbook documented | ✅ |
| Pre-existing risks distinguished from batch-introduced risks | ✅ |
| Production unchanged | ✅ — preview only |
| Operator owns final deploy decision | ✅ — see `GO_NO_GO_DECISION.md` |

🛑 Risk report complete. Continue to `GO_NO_GO_DECISION.md` for the final operator-facing one-pager.
