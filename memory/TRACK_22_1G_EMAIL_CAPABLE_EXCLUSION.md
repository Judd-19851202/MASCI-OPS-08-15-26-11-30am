# TRACK 22.1G · Email-Capable Scheduler Exclusion

Track 22.1G MUST NOT migrate any scheduler handler that can emit a live email. These 5 handlers are explicitly EXCLUDED from this track and remain in `app.router.on_startup` until Track 22.1H.

## The 5 excluded handlers

| Handler | Why excluded | Fingerprint status (Track 22.1C lock) | Target track | Email-safety risk if migrated in 22.1G | Required parity gate for 22.1H |
|---|---|---|---|---|---|
| `_start_safety_digest_cron` | Long-running weekly cron sending safety digest emails. Body imports `resend` at handler time and calls `resend.Emails.send(...)` through the dispatcher. | LOCKED · `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` | **22.1H** | **HIGH** — reordering could race a fresh scheduler tick against the SDK-patch install if run in a non-strict env. | Preserve SHA-256 fingerprint; verify SDK patch is active before task creation; `EMAIL_SAFETY_MODE=strict` in test env. |
| `_start_operator_digest_cron` | Weekly operator digest email cron. | LOCKED · `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` | **22.1H** | **HIGH** — same class as safety digest. | Same as above. |
| `_start_po_digest_cron` | Weekly PO Request digest email (iter246 F3). | LOCKED · `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` | **22.1H** | **HIGH** — same class. | Same as above. |
| `_dispatch_reminder_scheduler_start` | Starts the dispatch-reminder scheduler which invokes `_dispatch_auto_email` on schedule. | LOCKED · `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` | **22.1H** | **CRITICAL** — this handler is one hop away from `_dispatch_auto_email`; any reorder must be proven parity-safe. | Preserve SHA-256 fingerprint; `_dispatch_auto_email` fingerprint (`ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b`) must remain clean; assert `auto_email_enabled()` returns False in test env. |
| `_start_backup_verification_cron` | Long-running weekly cron sending backup verification email. | not fingerprint-locked at Track 22.1C close, but its body contains a Resend call path via the backup watchdog. | **22.1H** | **HIGH** — email side effect on schedule tick. | Add SHA-256 fingerprint before migration; preserve backup-verification cadence; `EMAIL_SAFETY_MODE=strict` in test env. |

## Post-22.1G quarantine assertion

The Track 22.1G lock test (`test_email_capable_schedulers_still_in_on_startup`) asserts all 5 remain in `app.router.on_startup` (i.e., they were NOT accidentally moved). This assertion runs on every lock envelope pass and will fail LOUDLY if a future track violates the quarantine before 22.1H closes it properly.

## Fingerprint verification post-22.1G

```
verify_locked_bytecode(server.app) →
    checked=5 · ok=5 · drift=0 · missing=0
```

The 5 locked fingerprints (`_dispatch_auto_email` + 4 email-capable scheduler handlers) all match live bytecode — proven that Track 22.1G did not accidentally rewrite any email-sensitive path.

## Verdict

🟢 **EXCLUSION CERTIFIED.** All 5 email-capable handlers untouched. Fingerprints locked. Track 22.1H has a clean scope + owner.
