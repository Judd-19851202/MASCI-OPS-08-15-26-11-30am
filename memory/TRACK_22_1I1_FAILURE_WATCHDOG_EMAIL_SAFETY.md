# TRACK 22.1I.1 · Failure Watchdog / Email Safety Audit

## Scope
Prove that migrating `_start_backup_scheduler` cannot dispatch a live email at any point — startup or during the test envelope.

## Static analysis (handler body)
Grep of the ~140-line handler body for `resend.Emails.send`, `import resend`, `send_email`, `_dispatch_auto_email`, `fsi_send_email`:
- ❌ No match. The handler body invokes only `logging`, `asyncio.create_task`, disk helpers, and the singleton-locked loop launcher.

## Email path indirection
1. Failure alerts (missing backup) are dispatched by **`_start_backup_verification_cron`** — a separate handler in the `email-scheduler` group, migrated and fingerprint-locked in Track 22.1H (SHA-256 `36bf2f8f...`). Not touched by this track.
2. `_start_backup_verification_cron` goes through `_safety_send_email` → `_dispatch_auto_email` → Resend SDK. All three respect `EMAIL_SAFETY_MODE=strict`.

## Runtime safety envelope (three layers, all intact)
1. **SDK monkey-patch** — `resend.Emails.send` replaced with `_blocked_send` stub at server module import. Verified by:
   ```
   platform_status.email_safety = {mode: "strict", resend_sdk_patched: True, live_emails_possible: False}
   ```
2. **`auto_email_enabled()`** — returns `False` when `EMAIL_SAFETY_MODE` is `strict|silent|test`.
3. **`_dispatch_auto_email`** — short-circuits with `status="skipped"` + `failure_reason="email_safety_mode:strict"` on Trust Spine.

## Fingerprint lock chain
| Handler | SHA-256 | Track | Status |
|---|---|---|---|
| `_dispatch_auto_email` | `ebf5259d...` | 22.1B | 🟢 Match |
| `_start_safety_digest_cron` | `9aabbd4f...` | 22.1H | 🟢 Match |
| `_start_operator_digest_cron` | `8f28a846...` | 22.1H | 🟢 Match |
| `_start_po_digest_cron` | `5158200a...` | 22.1H | 🟢 Match |
| `_dispatch_reminder_scheduler_start` | `5a6e3986...` | 22.1H | 🟢 Match |
| **`_start_backup_scheduler`** | **`c7d29e00...`** | **22.1I.1** | 🟢 **Match (new)** |

## Runtime probe (post-migration)
```
platform_status.bytecode_fingerprints = {
  "checked": 6,
  "ok_count": 6,
  "drift_count": 0,
  "missing_count": 0,
  "clean": true
}
platform_status.email_safety = {
  "mode": "strict",
  "resend_sdk_patched": true,
  "live_emails_possible": false
}
```

## Verdict
🟢 **GO** — Failure watchdog / email dispatch surface unchanged. Zero live emails.
