# TRACK 22.1L · Boot Order Report

## Certified boot order (post-22.1L)
```
▼ lifespan.startup begins
[track-22.1e] lifespan.startup: executing 49 LIFECYCLE_STEPS (non-readiness)
    ├─ 11 × index-ensure     (Mongo indexes)
    ├─  7 × seed             (default rows / role templates / etc)
    ├─  4 × scheduler-nonemail
    ├─  4 × email-scheduler  (digests · reminders — 4 of 5)
    ├─ 20 × misc-bootstrap
    ├─  1 × backup-scheduler  · [scheduled-backup] scheduler started …
    ├─  1 × command-center    · (silent seed of thresholds/calendar)
    └─  1 × email-scheduler  (5th, registered LAST due to source position — `_dispatch_reminder_scheduler_start`)
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS (non-readiness) complete

[track-22.1d] lifespan.startup: executing 0 handlers      ← EMPTY
[track-22.1d] lifespan.startup: complete

[track-22.1j] lifespan.startup: executing 1 readiness LIFECYCLE_STEPS (final phase)
[iter453.6] startup-readiness gate FLIPPED · public writes now accepted
[track-22.1j] lifespan.startup: readiness phase complete

Application startup complete.
```

## Invariants proven by the boot log
1. 🟢 **All indexes exist** before any seed / scheduler / bootstrap runs.
2. 🟢 **Seeds run** after indexes.
3. 🟢 **Schedulers armed** after seeds.
4. 🟢 **Backup scheduler starts** as part of the `backup-scheduler` group (isolated in its own group for auditability).
5. 🟢 **Command-center thresholds/calendar** seeded eagerly (not lazily on first request).
6. 🟢 **Legacy `on_startup`** window (phase-2) is now empty. FastAPI has no residual startup work.
7. 🟢 **Readiness flip** is the LAST action of startup — nothing runs after `[iter453.6] gate FLIPPED`.

## Zero-drift proof
- Boot log line count: identical to pre-22.1L modulo:
  - New `[track-22.1j] lifespan.startup: readiness phase complete` line (added in 22.1J, unchanged in 22.1L).
  - Legacy phase-2 header says `executing 0 handlers` instead of `executing 1 handlers`.
- All application-level log lines (index-ensure, seed, scheduler start banners) are byte-identical to pre-22.1L.

## Absolute rule: nothing after readiness
Post-22.1L, phase-3 (readiness) is the terminal phase before `yield`. The orchestrator itself enforces this — no code path can queue work "after readiness" without adding a NEW phase, which would require a new group order rule and a lock-test update.
