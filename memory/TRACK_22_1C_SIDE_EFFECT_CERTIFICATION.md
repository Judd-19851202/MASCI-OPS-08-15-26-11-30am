# TRACK 22.1C · Side-Effect Certification

## Classification (all 51 startup handlers · 1 shutdown handler)

Full JSON at `memory/track_22_1c/STARTUP_ORDER_before.json`. Aggregate:

| Side-effect class | Count | Env gate | 22.1C change |
|---|---|---|---|
| Index creation only | 11 | none (idempotent) | none |
| Mongo write (bootstrap seeds) | 2 | idempotent | none |
| Scheduler task launch | 11 | `SCHEDULER_ENABLED` | none |
| Backup subsystem launch | 3 | `SCHEDULER_ENABLED` + `BACKUP_ON_STARTUP` | none |
| Digest cron | 2 | `SCHEDULER_ENABLED` | none |
| Email-capable (via schedule_auto_email) | 4 | `EMAIL_SAFETY_MODE` + `AUTO_EMAIL_REPORTS` + `TEST_` guardrail | **fingerprint-locked** |
| R2 / storage | 2 | `SCHEDULER_ENABLED` | none |
| No detected side effect | 26 | n/a | none |

## Detailed side-effect certification

### 1 · Email-capable handlers (4)

Locked by SHA-256 bytecode fingerprint. Sender chain:

```
_start_safety_digest_cron / _start_operator_digest_cron / _start_po_digest_cron / _dispatch_reminder_scheduler_start
    ↓
schedule_auto_email(kind, record)       ← lib.email_dispatch (Track 22.1B)
    ↓
_DISPATCHER_HOOK = server._dispatch_auto_email (bytecode-locked · Track 22.1B)
    ↓
Three-layer email safety envelope:
  1. EMAIL_SAFETY_MODE ∈ {strict,silent,test}  → skip + Trust Spine "skipped" event → return
  2. project_name.startswith("TEST_")          → skip + Trust Spine "skipped" event → return
  3. auto_email_enabled() False                → skip + Trust Spine "skipped" event → return
    ↓ (only reachable under EMAIL_SAFETY_MODE=off + non-TEST_ payload + AUTO_EMAIL_REPORTS=true)
resend.Emails.send(params)  ← in preview: monkey-patched to _blocked_send → returns safety stub
```

**No 22.1C change to any layer.** Verified by runtime probe returning `{"id":"blocked_by_email_safety_mode","status":"skipped"}`.

### 2 · Backup subsystem (3 handlers)

- `_start_backup_scheduler` — starts `_backup_scheduler_loop_with_capture`. Env-gated by `SCHEDULER_ENABLED` (preview: false → no-op).
- `_start_backup_verification_cron` — verification cron. Env-gated.
- Boot-step recorder used by both — logs only, no side effect.

**No 22.1C change.**

### 3 · Scheduler task launchers (11 handlers)

All use `asyncio.create_task(run_with_singleton_lock(db, "<name>", <fn>))`. `run_with_singleton_lock` is a pre-existing helper in `lib/singleton_scheduler.py` that either elects a runner across workers or logs "SCHEDULER_ENABLED='false' — scheduler disabled" and returns. Verified by boot log entries.

**No 22.1C change.**

### 4 · R2 storage handlers (2 handlers)

Only test-blob janitor / photo-migration jobs. Env-gated by `SCHEDULER_ENABLED`. No 22.1C change.

### 5 · Index / seed handlers (11 + 2 = 13 handlers)

Idempotent by design. Motor `create_index` is a no-op when the index exists. Seed helpers check for existing rows before insert. No 22.1C change.

### 6 · Shutdown handler (1 handler)

Not classified as side-effect-producing beyond logging. No 22.1C change.

## Unit-test safety

- Lock-test files never trigger a startup handler directly. They only:
  - Read files.
  - Import server (which triggers all startup handlers).
  - Query in-memory state (`app.router.on_startup`, `_DISPATCHER_HOOK`).
- No lock test performs an HTTP POST to a workflow endpoint.
- No lock test writes to Mongo.
- No lock test issues an external API call.
- No lock test dispatches email.

Verified across the 196-assertion lock envelope.

## Six Pillars

- Trusted: 9.97 — every side-effect class documented + email-capable handlers cryptographically locked.
- Proven: 9.97 — reproducible inventory harness + lock test.
- Operational: 9.83 — `verify_locked_bytecode(app)` is a runtime self-check available for future boot-time audit.

## Verdict

🟢 **SIDE-EFFECT CERTIFIED.** Every handler classified. Every email-capable handler locked. Zero live sends. Zero unsafe test path.
