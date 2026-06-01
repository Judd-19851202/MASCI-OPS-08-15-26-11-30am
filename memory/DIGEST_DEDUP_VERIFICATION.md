# Digest Dedup Verification

**Batch:** OMEGA · Sprint Scheduler Hardening + UX Phase 1 · Phase A · Verification
**Companion:** `SCHEDULER_HARDENING_REPORT.md` · `SCHEDULER_CERTIFICATION_REPORT.md`
**Date:** 2026-06-01

---

## 1 · Purpose

This document is the operator's audit-trail of **what was tested and proven** for the two-layer dedup defense added to the singleton-scheduler family. It answers a single question: *"If this batch goes to production, will any Monday ever again deliver 22 PO digest emails instead of 11?"*

**Answer:** 🟢 **No.** Two independent layers must both fail simultaneously for a duplicate to occur. Each layer was verified in isolation; both were verified together via a concurrent-claim stress test.

---

## 2 · Defense layers

| Layer | Mechanism | File | Verified by |
|---|---|---|---|
| **L1 · Orphan cancel** | When `_refresh_lock` fails, the heartbeat now calls `scheduler_task.cancel()`. The orphaned scheduler coroutine immediately raises `CancelledError` inside its `asyncio.sleep(days)` — it can no longer fire. | `lib/singleton_scheduler.py` | `test_heartbeat_cancels_scheduler_on_lock_loss` |
| **L2 · Per-slot dedup** | Before sending, the scheduler calls `claim_slot(scheduler, slot_key)`. The `(scheduler, slot_key)` unique index on `scheduler_runs` enforces atomicity at MongoDB. Second claim returns `None`; the send is skipped and the attempt is logged. | `lib/scheduler_runs.py` + `po_digest.py` + `safety_digest.py` + `lib/operator_digest.py` | `test_claim_slot_dedup_first_wins` · `test_concurrent_claims_only_one_wins` |
| **L3 · Audit trail** | `claim_slot` writes `started_at`/`owner_id`/`host`/`pid`; `mark_completed` writes `recipients`/`duration_s`/`finished_at`; `mark_failed` writes `error`. TTL prunes at 90 days. | `lib/scheduler_runs.py` | `test_mark_completed_sets_duration` · `test_mark_failed_records_error` |

---

## 3 · Per-scheduler coverage

| Scheduler | Slot key | L1 | L2 | L3 | Status |
|---|---|---|---|---|---|
| `po_digest` | next-Monday 14:00 UTC | ✅ | ✅ | ✅ | 🟢 fully hardened |
| `safety_digest` | next-Monday 14:00 UTC | ✅ | ✅ | ✅ | 🟢 fully hardened |
| `operator_digest` | next-Monday 14:00 UTC | ✅ | ✅ | ✅ | 🟢 fully hardened |
| `backup_scheduler` | hourly fuzzy | ✅ | n/a — fuzzy slot | already `backup_runs` | 🟡 L1 only (sufficient) |
| `backup_verification` | hourly fuzzy | ✅ | n/a — fuzzy slot | already `r2_degraded_events` | 🟡 L1 only (sufficient) |

Backup schedulers use a 5-minute polling tick + hour-transition observer. They do not have a discrete fire slot to claim; per-slot dedup would require restructuring. L1 alone closes the duplicate-fire race for these — and they already write their own audit collections. **No regression to existing behavior.**

---

## 4 · Test execution log (verbatim)

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

## 5 · Concurrent-claim stress test detail

The most important behavioral guarantee — that two workers cannot both deliver a digest in the same slot — is asserted by `test_concurrent_claims_only_one_wins`:

* 20 concurrent `asyncio.create_task(claim_slot("po_digest", same_slot_key, …))` calls.
* Exactly **1** task receives a truthy owner_id; the other **19** receive `None`.
* The winning document's `dedup_attempts` counter reaches **19**.
* `dedup_attempt_log` records the host/pid of each losing claim — enough for forensic attribution after the fact.

This proves L2 is atomic at the Mongo level, not racy at the application level.

---

## 6 · Orphan-cancel proof

`test_heartbeat_cancels_scheduler_on_lock_loss`:

1. Builds a fake scheduler coroutine that sleeps forever.
2. Wires it into `run_with_singleton_lock` with a heartbeat that immediately fails (mock returns `False`).
3. Asserts `scheduler_task.cancelled() is True` within one heartbeat interval.

Before this batch, the equivalent test would have failed — the orphan would still be in `await asyncio.sleep(days)`, alive and unreachable, scheduled to fire next Monday in parallel with the new lock-owner.

---

## 7 · Manual admin-endpoint check (preview)

```bash
$ curl -H "X-Admin-Token: <admin>" \
       http://localhost:8001/api/admin/scheduler-runs

{
  "items": [],
  "total": 0,
  "dedup_total": 0,
  "failed_total": 0
}
```

Endpoint healthy. Empty because no fire has occurred in this preview pod (the next slot is Monday 2026-06-08T14:00:00Z). After the first real fire, the row schema is:

```json
{
  "scheduler": "po_digest",
  "slot_key": "2026-06-08T14:00:00+00:00",
  "host": "safety-audit-mobile-1-…",
  "pid": 24,
  "owner_id": "host:pid:…",
  "started_at": "2026-06-08T14:00:00.123Z",
  "finished_at": "2026-06-08T14:00:12.456Z",
  "duration_s": 12.3,
  "recipients": 11,
  "status": "done",
  "dedup_attempts": 0
}
```

If the L1 orphan-cancel ever regressed, `dedup_attempts` would be `>=1` and the operator would see the attempt log inline. The send count still equals one.

---

## 8 · What this verification does NOT cover

| Out of scope | Reason |
|---|---|
| Real Monday-14:00-UTC fire in production | Cannot be tested in preview. Will be observed on first post-deploy Monday. |
| Resend deliverability | Resend remains synchronous · no retry · unchanged from prior batches. |
| Pod-restart timing | The exact wall-clock between pod restart and lock takeover is environment-dependent (60-90 s expected). |
| Backup scheduler L2 dedup | Intentionally excluded — fuzzy slot. L1 alone closes the race. |
| Recipient routing change | None. Same `project_managers` / `hr_users` queries, same `_po_digest_send_email`. |

---

## 9 · Verification status

| Item | Status |
|---|---|
| Unit tests written | 🟢 7/7 |
| Unit tests passing | 🟢 7/7 |
| Backend boots with new code | 🟢 verified · source_hash changed |
| Indexes created on startup | 🟢 3 indexes (unique compound · TTL · history) |
| Admin endpoint healthy | 🟢 `/api/admin/scheduler-runs` returns expected envelope |
| Frontend admin tile renders | 🟢 verified via smoke screenshot |
| Existing scheduler behavior preserved | 🟢 env guards · slot math · recipient lists all unchanged |

🛑 Dedup verification complete. Continue to `UX_PHASE1_IMPLEMENTATION_REPORT.md`.
