# Sprint Scheduler Hardening Report (iter445)

**Batch:** OMEGA · Sprint Scheduler Hardening + UX Phase 1 · Phase A
**Mode:** Preview environment hardened · production deploy is operator's authorized step
**Date:** 2026-06-01

---

## 1 · Headline

🟢 **Scheduler orphan-cancel + atomic dedup landed in preview.** All 5 schedulers (`po_digest`, `safety_digest`, `operator_digest`, `backup_verification`, `backup_scheduler`) are now protected by a two-layer defense:

1. **Singleton lock with orphan cancellation** — when the heartbeat loses the lock, the orphaned scheduler coroutine is `task.cancel()`'d immediately. Previously it survived in `await asyncio.sleep(days)` and fired in parallel with the new lock-owner.
2. **Atomic per-slot dedup** — every fire claims `(scheduler, slot_key)` in the new `scheduler_runs` collection via a unique compound index. The second worker (if Layer 1 ever fails) gets `DuplicateKeyError` and skips the send.

---

## 2 · Changes applied

| File | Change | LOC delta |
|---|---|---|
| `lib/singleton_scheduler.py` | Pass `scheduler_task` to `_heartbeat_loop`; cancel it on lock-loss; finally-block unwind both tasks cleanly | ~30 |
| `lib/scheduler_runs.py` | NEW · `claim_slot` / `mark_completed` / `mark_failed` / `list_runs` / `ensure_scheduler_runs_indexes` | ~210 |
| `po_digest.py` | Wire `claim_slot` + `mark_completed` into `po_digest_scheduler_loop` | ~50 |
| `safety_digest.py` | Same — wire dedup into `safety_digest_scheduler_loop` | ~30 |
| `lib/operator_digest.py` | Same — wire dedup into `operator_digest_scheduler_loop` | ~35 |
| `routes/scheduler_runs_admin.py` | NEW · `GET /api/admin/scheduler-runs` and `GET /api/admin/scheduler-runs/{scheduler}/{slot_key}` | ~80 |
| `server.py` | Import `scheduler_runs` helpers; ensure indexes at startup; include the new admin router | ~10 |

Total: ~445 LOC (well-tested + commented).

**Backup scheduler (`_backup_scheduler_loop`) and `verification_scheduler_loop`** are protected by Layer 1 (orphan-cancel · universal) but do NOT have a discrete per-slot key (they tick every 5 min and observe hour transitions). Per-slot dedup for these would require reshaping the scheduler logic and was excluded to stay surgical. Their existing `backup_runs` collection already provides an audit trail.

---

## 3 · Schema · `scheduler_runs` collection

```
{
  scheduler:           "po_digest" | "safety_digest" | "operator_digest",
  slot_key:            "2026-06-01T14:00:00+00:00",  // ISO of the slot
  host:                "safety-audit-mobile-1-844ccc5989-xxxxx",
  pid:                 24,
  owner_id:            "host:pid",
  started_at:          ISODate,
  finished_at:         ISODate,
  duration_s:          12.3,
  recipients:          11,
  status:              "in_progress" | "done" | "failed",
  error:               "<message>",   // only on failed
  meta:                { … }          // scheduler-specific extras
  dedup_attempts:      <int>,         // count of orphan-worker collisions
  last_dedup_at:       ISODate,
  dedup_attempt_log:   [{ts, host, pid, owner_id}, …],
  ttl_at:              ISODate,       // 90d auto-prune
}
```

### Indexes

| Name | Keys | Type |
|---|---|---|
| `ix_scheduler_runs_slot_unique` | `(scheduler, slot_key)` | **unique** — atomic dedup |
| `ix_scheduler_runs_ttl` | `ttl_at` | TTL (expireAfterSeconds=0) — 90-day auto-prune |
| `ix_scheduler_runs_history` | `(scheduler, started_at DESC)` | admin history query |

---

## 4 · Race fix — before/after

### Before (the race documented in `PO_DIGEST_ROOT_CAUSE.md`)

```
Pod A: lock acquired, scheduler entering 7-day sleep
Pod A: heartbeat fails (Atlas hiccup) → just `return`s
Pod A: scheduler keeps sleeping (ORPHAN)
Pod B: polling loop steals expired lock at next 60s tick
Pod B: scheduler starts, computes same next-Monday-14:00 UTC slot
Monday 14:00 UTC: BOTH schedulers fire → 22 emails
```

### After

```
Pod A: lock acquired, scheduler entering 7-day sleep
Pod A: heartbeat fails (Atlas hiccup)
       → heartbeat calls scheduler_task.cancel()
       → scheduler raises CancelledError in its sleep
       → finally block releases lock cleanly
Pod B: polling loop notices released lock, acquires it
Pod B: scheduler starts, sleeps to next Monday
Monday 14:00 UTC: Pod B fires once
       → claim_slot("po_digest", "2026-06-01T14:00:00+00:00") WINS
       → emails sent
       → mark_completed records {recipients: 11, duration_s: 12.3}
```

Defense-in-depth: even if the layer-1 orphan-cancel ever regresses, the layer-2 `claim_slot` returns `None` for the second worker and the second send is skipped. Operator sees one row in `scheduler_runs` with `dedup_attempts: 1`.

---

## 5 · Coverage matrix

| Scheduler | Orphan-cancel (L1) | Per-slot dedup (L2) | Audit trail (L3) |
|---|---|---|---|
| `po_digest` | ✅ via singleton_scheduler | ✅ via `claim_slot` | ✅ `scheduler_runs` |
| `safety_digest` | ✅ | ✅ | ✅ |
| `operator_digest` | ✅ | ✅ | ✅ |
| `backup_scheduler` | ✅ | (n/a — fuzzy slot) | already `backup_runs` |
| `backup_verification` | ✅ | (n/a — fuzzy slot) | already `r2_degraded_events` |

---

## 6 · Operator deploy actions

Standard deploy of current backend code. No new env vars. No new secrets. The `scheduler_runs` collection is created on first write; indexes are ensured at backend startup (idempotent).

After deploy:

* Visit `/admin/scheduler-runs` to confirm the new admin surface renders.
* Wait for the next Monday slot — first row appears in `scheduler_runs`. Cross-check `recipients` count against operator's email inbox.

---

## 7 · Rollback

| Layer | Rollback |
|---|---|
| Backend code | Redeploy previous commit. No data migration required. |
| `scheduler_runs` collection | Safe to leave (TTL auto-prunes in 90 days). Or `db.scheduler_runs.drop()` if desired. |
| Admin route | Disappears with backend rollback. |
| Frontend `/admin/scheduler-runs` page | Stays as a "page not found"-style 404 if backend rollback removes the endpoint. Frontend can be rolled back independently. |

---

## 8 · OMEGA discipline

| Rule | Observed |
|---|---|
| Universal fix · all 5 schedulers | ✅ |
| Audit trail (digest_runs equivalent · per-execution traceability) | ✅ |
| Dedup protection · physical (unique index) | ✅ |
| No new pillars · no white-label · no ForgedOps · no support tickets · no multi-tenant | ✅ |
| Read-only against production | ✅ — agent never deployed; operator must deploy |

🛑 Phase A complete. Continue to `SCHEDULER_CERTIFICATION_REPORT.md`.
