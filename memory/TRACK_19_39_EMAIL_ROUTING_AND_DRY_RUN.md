# TRACK 19.39 · EMAIL ROUTING AND DRY-RUN

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_39_MORNING_SAFETY_DIGEST.md`

## Email provider
Uses **existing** `backend/lib/fsi_email_sender.py::fsi_send_email(to, subject, html, *, reply_to=None, db=None)`. Track 19.39 introduces **no new email provider** and **no new email routing table**.

## Dry-run mode
`send_digest(db, dry_run=True, ...)` (default) composes the digest, resolves active recipients, renders HTML, and writes an audit row with `send_status="dry_run"` — but **never invokes** `fsi_send_email`. Enforced by the Track 19.39 lock test which patches `lib.fsi_email_sender.fsi_send_email` and asserts `called == False` after a dry-run.

## Live send
`dry_run=False` iterates active recipients, awaits `fsi_send_email` once per recipient, records each delivery attempt with `ok` + `provider_id` / `error`, and sets `send_status="sent"` when all succeed or `"partial"` otherwise.

## Audit trail
Every send (dry-run or live) writes one row to the additive `morning_digest_audit` collection:
```
{
  id, dry_run, generated_at, generated_by,
  digest_window_days, subject, top_case_count,
  recipient_count, recipients: [{email, role_label}],
  send_status: "dry_run" | "sent" | "partial",
  delivery: [{email, ok, provider_id | error}]
}
```
This is append-only. No delete surface.

## Duplicate-send discipline
This track does not gate on prior audit rows before sending — that would risk hiding a needed re-send. Duplicate protection is delegated to the caller (an eventual scheduler / cron / operator) and can be added in a future track with a `dedupe_key = f"{digest_type}:{iso_week}"` check.

## Scheduler hook (Phase 2 · out of scope for 19.39)
The `send_digest` function is callable from any scheduler. To add a weekly Monday-morning cron:
1. Add a new APScheduler job in `server.py` guarded by `SCHEDULER_ENABLED` (existing pattern).
2. Call `await send_digest(db, dry_run=False, digest_window_days=7, top_n=5, generated_by="scheduler")`.
3. Optionally add the dedupe-key check described above.

This track ships the callable primitive; the scheduler wiring is deferred deliberately so the operator can run manual sends and reviews the audit trail before enabling automation.

## Testing safety
- Lock test uses `unittest.mock.patch("lib.fsi_email_sender.fsi_send_email", new_callable=AsyncMock)`.
- No live emails are dispatched by any test in this track.
- The runtime smoke used `dry_run=True` and verified `mock.called == False`.
