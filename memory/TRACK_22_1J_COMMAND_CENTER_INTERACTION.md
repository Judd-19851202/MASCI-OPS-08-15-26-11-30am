# TRACK 22.1J · Command-Center Startup Interaction

## Context
`build_command_center_router._startup` (module `routes.command_center`) is the **sole remaining** `@app.on_event("startup")` handler in the app after Track 22.1J. It is queued for **Track 22.1L**. This document proves readiness-last is preserved WHILE `_startup` remains legacy.

## Discovery
```
app.router.on_startup (Track 22.1J after) = ["_startup"]     # routes.command_center
```

## Execution order guarantee (post-22.1J)
```
phase-1  ▼  48 non-readiness LIFECYCLE_STEPS
             (index-ensure · seed · scheduler-nonemail ·
              email-scheduler · misc-bootstrap · backup-scheduler)
phase-2  ▼  1 legacy on_startup handler
             build_command_center_router._startup
phase-3  ▼  1 readiness LIFECYCLE_STEP
             _iter453_6_flip_ready_flag       ← LAST
yield
```
Because phase-3 iterates only steps with `group="readiness"` and there is exactly one such step (asserted by lock test), and because phase-2 runs BEFORE phase-3, the command-center router startup ALWAYS runs before readiness flips.

## Could command_center._startup break readiness?
No. It performs `command_center` index setup and route wiring. It:
- ❌ Does not touch `app.state.ready`.
- ❌ Does not raise an exception under preview env (verified by successful boot).
- ❌ Does not consume readiness (readiness is not True at that point — expected).
- ✅ Is idempotent across boots.

If it *did* raise, both the legacy behavior (before 22.1J) and the migrated behavior (after 22.1J) would re-raise to Uvicorn identically — the exception path was preserved.

## Does readiness-first-flip-then-command-center risk exist?
No. Readiness cannot possibly flip before phase-2 completes because phase-3 is downstream in the same `orchestrated_lifespan` coroutine. There is no concurrent scheduling of phases.

## Track 22.1L preview
Track 22.1L will:
- Remove `@app.on_event("startup")` from `routes.command_center._startup`.
- Register it as `@register_lifecycle_step("command-center")` (or `misc-bootstrap`).
- Leave phase-3 (`readiness`) untouched.
- Drop `on_startup_legacy_count` to 0 and `migrated_pct` to 100%.

## Verdict
🟢 **SAFE.** Readiness-last is preserved even while `_startup` remains legacy. No blocker to closing Track 22.1J now.
