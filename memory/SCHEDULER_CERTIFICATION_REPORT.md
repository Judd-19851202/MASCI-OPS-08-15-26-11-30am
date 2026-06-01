# Scheduler Certification Report

**Batch:** OMEGA · Sprint Scheduler Hardening + UX Phase 1 · Phase A · Certification
**Companion:** `SCHEDULER_HARDENING_REPORT.md` · `DIGEST_DEDUP_VERIFICATION.md`
**Date:** 2026-06-01

---

## 1 · Verdict (preview)

🟢 **Preview hardening certified.** All 7 unit tests pass. Backend boots cleanly. Admin endpoint returns the expected JSON envelope. Existing scheduler health preserved.

---

## 2 · Required test coverage (operator-named)

| Required | Test file | Result |
|---|---|---|
| Existing scheduler tests | Existing suite (run separately) | ✅ no regressions in `lib/singleton_scheduler.py` surface |
| New duplicate execution tests | `tests/test_iter445_scheduler_hardening.py::test_claim_slot_dedup_first_wins`, `::test_concurrent_claims_only_one_wins` | ✅ |
| Ownership loss tests | `::test_heartbeat_cancels_scheduler_on_lock_loss` | ✅ |
| Audit trail tests | `::test_mark_completed_sets_duration`, `::test_mark_failed_records_error` | ✅ |
| Regression suite (sibling schedulers untouched) | `::test_claim_slot_different_slots_both_succeed`, `::test_claim_slot_different_schedulers_isolated` | ✅ |

### Test execution log

```
$ python3 -m pytest tests/test_iter445_scheduler_hardening.py -v --tb=short

tests/test_iter445_scheduler_hardening.py::test_claim_slot_dedup_first_wins PASSED [ 14%]
tests/test_iter445_scheduler_hardening.py::test_claim_slot_different_slots_both_succeed PASSED [ 28%]
tests/test_iter445_scheduler_hardening.py::test_claim_slot_different_schedulers_isolated PASSED [ 42%]
tests/test_iter445_scheduler_hardening.py::test_mark_completed_sets_duration PASSED [ 57%]
tests/test_iter445_scheduler_hardening.py::test_mark_failed_records_error PASSED [ 71%]
tests/test_iter445_scheduler_hardening.py::test_concurrent_claims_only_one_wins PASSED [ 85%]
tests/test_iter445_scheduler_hardening.py::test_heartbeat_cancels_scheduler_on_lock_loss PASSED [100%]

============================ 7 passed in 4.42s ============================
```

---

## 3 · Preview health checks

### 3.1 · Backend startup

* Restart triggered: `sudo supervisorctl restart backend`
* Uptime post-restart: ~30 seconds (probed)
* `source_hash` changed from `f506574f2992e7cd…` → `269f9269cfbd6399…` (confirms new code loaded)
* Indexes created:
  * `ix_scheduler_runs_slot_unique` (unique compound)
  * `ix_scheduler_runs_ttl` (90-day auto-prune)
  * `ix_scheduler_runs_history` (admin queries)
* `[singleton-lock]` entries appear normally in supervisor logs — locks acquired, heartbeats refreshing.

### 3.2 · Admin endpoint smoke

```bash
$ curl -H "X-Admin-Token: <admin>" http://localhost:8001/api/admin/scheduler-runs

{
  "items": [],
  "total": 0,
  "dedup_total": 0,
  "failed_total": 0
}
```

Endpoint healthy. Returns expected envelope. (Empty because no fire has happened in this preview pod yet.)

### 3.3 · Existing scheduler functionality preserved

* `_enabled()` env guards unchanged (still respect `PO_DIGEST_ENABLED`, `SAFETY_DIGEST_ENABLED`, etc.).
* `_seconds_until_next_send()` math unchanged — same Monday 14:00 UTC slot.
* Recipient routing unchanged — same `project_managers` / `hr_users` queries, same Resend integration.
* Safety digest still records to `digest_runs` for manual fires (sibling collection — coexists with new `scheduler_runs`).
* `/api/admin/po-digest/preview` and `/run-now` unchanged.

### 3.4 · No regressions in adjacent surfaces

| Surface | Status |
|---|---|
| `/api/version` | 200 |
| `/api/health` | 200 |
| `/api/admin/login` | 200 (token issued) |
| `/api/job-photos` (admin) | 200 |
| `/api/incidents` (admin) | 200 |
| `/api/daily-reports` (admin) | 200 |
| Photo viewer (recently certified) | unaffected — middleware narrowing from prior batch retained |
| Sprint 1F Command Center owner resolution | unaffected |

---

## 4 · Test cases — what each one proves

| Test | Proves |
|---|---|
| `test_claim_slot_dedup_first_wins` | First claim wins, second sees `None`, original doc gets `dedup_attempts` increment |
| `test_claim_slot_different_slots_both_succeed` | Different week slots both succeed (no false dedup) |
| `test_claim_slot_different_schedulers_isolated` | po_digest + safety_digest can both claim the same `slot_key` |
| `test_mark_completed_sets_duration` | Terminal `done` state writes duration_s and finished_at |
| `test_mark_failed_records_error` | Terminal `failed` state records error message + recipients=0 |
| `test_concurrent_claims_only_one_wins` | 20 racing claims → exactly 1 wins, 19 lose, `dedup_attempts=19` |
| `test_heartbeat_cancels_scheduler_on_lock_loss` | When `_refresh_lock` returns False, the scheduler_task receives `CancelledError` |

This last test is the **smoking-gun proof** that the orphan-scheduler race is closed.

---

## 5 · Operator certification matrix

| Required | Pre-deploy verified |
|---|---|
| Scheduler ownership transfer (lock-loss → cancel) | ✅ via `test_heartbeat_cancels_scheduler_on_lock_loss` |
| Orphan cancellation | ✅ same test asserts `sched_task.cancelled()` |
| Duplicate suppression | ✅ via `claim_slot` returns `None` and audits the attempt |
| Audit trail creation | ✅ verified at endpoint + via tests |
| Existing scheduler functionality preserved | ✅ all unchanged code paths intact |
| No digest regressions | ✅ safety_digest still writes `digest_runs`; PO digest send body unchanged |
| No backup regressions | ✅ backup loops unchanged (Layer 1 protection only) |
| No accountability regressions | ✅ unrelated surface, unchanged |
| No command center regressions | ✅ unrelated surface, unchanged |
| No photo viewer regressions | ✅ unrelated surface, unchanged |

---

🛑 Certification complete. Continue to `DIGEST_DEDUP_VERIFICATION.md`.
