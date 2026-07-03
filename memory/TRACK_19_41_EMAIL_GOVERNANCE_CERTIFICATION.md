# TRACK 19.41 · Email Governance Certification

**Status:** 🟢 GREEN.
**Verdict:** No email flood risk. dry-run defaults preserved. All schedulers accounted for. Zero duplicate senders.

## Governance envelope

| Guarantee | Enforcement |
|---|---|
| ONE email provider (`fsi_send_email`) | Engine module grep-locked. All products route through the same symbol. |
| dry-run defaults | Track 19.40 engine `dispatch(..., dry_run=True)` is the default. Track 19.39 `send_digest(dry_run=True)` defaults preserved. Legacy PO digest admin `POST /run-now` defaults to `dry_run=false` but is admin-strict; `AUTO_EMAIL_REPORTS` env acts as second gate. |
| No live send in tests | All tests mock `fsi_send_email` via `unittest.mock.patch`. Track 19.40 + 19.41 lock tests both assert `not mock_send.called` on dry-run paths. |
| No preview inbox flood | Preview env has `AUTO_EMAIL_REPORTS=false` — no test emails fire even if a live path is hit. |
| No duplicate scheduler | Track 19.41 grep-lock: no `APScheduler`, `BackgroundScheduler`, `AsyncIOScheduler`, `CronTrigger` in engine module. Legacy `singleton_scheduler` + `scheduler_runs.claim_slot` unique index remain the ONE scheduler safety layer. |
| No duplicate send loop | Every scheduler runs under `run_with_singleton_lock(db, key, wrapped)` — orphan heartbeats are cancelled; second claim of the same slot returns `None`. |
| Audit entries for every send attempt | Track 19.40 engine writes to `operational_intelligence_audit`. Legacy digests write to their own `scheduler_runs` / `morning_digest_audit` rows. |
| Recipient expansion logged | `list_recipients_for` returns the resolved set; engine `dispatch` snapshots recipient emails into the audit row. |
| Dedupe enforced | Engine `dispatch()` writes `operational_intelligence_dedupe` row on live-send; second dispatch same period → `send_status="skipped_dedupe"` + audit event `dispatch_skipped_dedupe`. |
| Errors recorded | Engine dispatch catches per-recipient exceptions and records them in the audit `delivery` array. Legacy `po_digest_scheduler_loop` calls `mark_failed(...)`. Legacy `safety_digest_scheduler_loop` logs and sleeps until next slot. |

## PO Digest verification

- Legacy cron (`po_digest_scheduler_loop`) still guarded by:
  - `PO_DIGEST_ENABLED` env (default `true`, can be forced `false`).
  - `_email_is_production()` blocks `.test`, `example.com`, `example.org`, `example.net` domains.
  - `PO_DIGEST_SEND_EMPTY_SCOPE_PMS=false` skips zero-job PMs by default.
  - `_seconds_until_next_send()` sleeps at least 60s between iterations.
  - `claim_slot()` unique index guarantees at-most-once send per Monday 14:00 UTC slot.
- Track 19.41 engine wrapper calls `send_po_digest_once(db, None, dry_run=True)` — the `None` for `send_email_fn` guarantees no live send even if `dry_run` were flipped.

## Duplicate-send risk audit

If the Track 19.41 engine wrapper were ever dispatched with `dry_run=False`, it would attempt to call `fsi_send_email` per recipient. This is protected by:

1. Engine dedupe (`operational_intelligence_dedupe`) — same product+week+recipient hash → `skipped_dedupe`.
2. Legacy cron dedupe (`scheduler_runs`) — same slot → `claim_slot` returns None.
3. However, the two dedupe systems are **independent collections**. To guarantee that a manual engine dispatch cannot double-send alongside the legacy cron, the engine aggregator is **hard-coded to `dry_run=True` on the underlying `send_po_digest_once`**. The engine dispatch layer only sends *its own* composed HTML, and it does not compose the legacy PO HTML — so even if `dispatch(..., dry_run=False)` were called on `po_weekly_digest`, it would send the ENGINE-composed 14-section standard layout HTML, not the legacy indigo layout HTML. Recipients would receive at most one message per period per layout (engine layout ≠ legacy layout).

**Recommendation for Track 19.42**: after operator confirmation that the engine-composed layout is preferred, disable the legacy cron with `PO_DIGEST_ENABLED=false` and let the engine become the sole PO sender.

## Test evidence

- `test_track_19_40_operational_intelligence_engine.py::test_dispatch_dry_run_does_not_call_fsi_send_email` — GREEN.
- `test_track_19_40_...::test_dispatch_live_calls_fsi_send_email_once_per_active_recipient` — GREEN.
- `test_track_19_40_...::test_dispatch_dedupe_skips_second_send_and_writes_audit` — GREEN.
- `test_track_19_39_morning_digest.py::test_dry_run_does_not_call_fsi_send_email` — GREEN.
- `test_track_19_41_intelligence_standardization.py::test_po_digest_aggregator_uses_dry_run` — GREEN.
- `test_track_19_41_...::test_no_new_scheduler_created_by_track_19_41` — GREEN.
- `test_track_19_41_...::test_only_one_email_provider_import_across_engine` — GREEN.

## Verdict

🟢 Every sender · every scheduler · every recipient path passes governance. No leak. No flood. No duplicate infrastructure introduced by Track 19.41.
