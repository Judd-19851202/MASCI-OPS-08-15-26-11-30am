# TRACK 22.1D · Startup Parity Report

## Method

- **`memory/track_22_1d/STARTUP_ORDER_before.json`** — inventory captured with server.py at its Track 22.1C close (16,028 lines, decorator-based lifecycle).
- **`memory/track_22_1d/STARTUP_ORDER_after.json`** — inventory captured after adding `lifespan=create_lifespan()` to `FastAPI(...)` (16,039 lines).

Both files list all 51 startup handlers by registration index, with per-handler `qualname`, `name`, `module`, `sourcefile`, `lineno`, `is_coroutine`, `arg_count`, `bytecode_sha256`, `side_effects` classification, and `docstring_first_line`.

## Results

| Field | Before | After | Delta |
|---|---|---|---|
| Startup handler count | 51 | 51 | **0** |
| Handler `qualname` list | (full list) | (full list) | **byte-equal** |
| Handler `name` list | (full list) | (full list) | **byte-equal** |
| Handler `module` list | (all `server`) | (all `server`) | **byte-equal** |
| Handler `bytecode_sha256` list | (51 hashes) | (51 hashes) | **byte-equal** — every function body is unchanged |
| Handler `is_coroutine` flags | (all True) | (all True) | **byte-equal** |
| Handler `arg_count` list | (all 0) | (all 0) | **byte-equal** |
| Handler `side_effects` classifications | (per-handler) | (per-handler) | **byte-equal** |
| Handler `lineno` list | (51 values) | (51 values shifted by +11) | **cosmetic** — the FastAPI(lifespan=...) argument added 11 lines above the handlers |

## Locked handler fingerprint re-verification

Post-lifespan boot, `verify_locked_bytecode(server.app)` returns:

```
{
  "checked": 5,
  "ok": ["_dispatch_auto_email",
         "_start_safety_digest_cron",
         "_start_operator_digest_cron",
         "_start_po_digest_cron",
         "_dispatch_reminder_scheduler_start"],
  "drift": [],
  "missing": []
}
```

**Zero drift.** Every safety-critical function body has the exact same compiled bytecode as pre-22.1D.

## Runtime boot evidence

Boot log excerpt from the post-22.1D restart:

```
[track-16-10] automation scheduler armed
[track-16-10a] command-digest scheduler armed
[singleton-lock:transport_automation] SCHEDULER_ENABLED='false' — scheduler disabled...
...
[safety-indexes] ensured
[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days...
[system-bootstrap] OK · version=1 · steps=history_indexes,email_routes
[iter453.6] startup-readiness gate FLIPPED · public writes now accepted
[dispatch-reminders] background task scheduled
[track-22.1d] lifespan.startup: complete
[dispatch-reminders] SCHEDULER_ENABLED is off — loop is a no-op.
INFO:     Application startup complete.
```

The same handlers fire in the same order — including the readiness-gate flip (handler #49) BEFORE the final `_dispatch_reminder_scheduler_start` (handler #50). The lifespan wrapper's `complete` marker prints after all 51.

## Verdict

🟢 **STARTUP PARITY CERTIFIED.** Every one of the 51 handlers registers at the same index, has the same qualname, and produces the same compiled bytecode. Only cosmetic line-number shifts from the FastAPI constructor's new kwarg.
