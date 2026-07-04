# TRACK 22.1D · Deprecation Cleanup Report

## Status: DEFERRED (with explicit reasoning per mandate Phase 10)

Mandate Phase 10: *"If old decorators remain as compatibility shims, document why and target a follow-up."*

## Current state

- 51 `@app.on_event("startup")` decorators — **all retained.**
- 1 `@app.on_event("shutdown")` decorator — **retained.**
- FastAPI emits `DeprecationWarning: on_event is deprecated, use lifespan event handlers instead` — 117 warning records per test run.

## Why deferred

Rewriting 51 individual handlers into an explicit `LIFECYCLE_STEPS` registry within Track 22.1D would be a **51-way behavior-change risk**. Each handler closes over server.py module-locals (`db`, `app`, and various flags); moving each requires:

1. Either lazy back-imports (creating import cycles).
2. Or wide dependency-injection factories that alter the closure mechanism.

Both approaches add non-trivial risk without user-facing benefit. The correct staging is:

- **Track 22.1D (this track):** Deliver the lifespan orchestration foundation. Zero behavior change.
- **Track 22.1e/f/g/...:** Migrate individual handlers one-by-one, with per-migration bytecode-fingerprint proof.

Each future migration is a bounded, testable, rollback-safe change. This is the "elite execution" the mandate requires.

## Follow-up track queue

| Track | Migration scope | Estimated handlers |
|---|---|---|
| 22.1e · Idempotent index-ensure migration | `_ensure_*_indexes`, `_arm_*_indexes` | ~11 |
| 22.1f · Seed migration | `_seed_shop_users`, `_seed_hr_users`, `_seed_field_leadership_*`, `_seed_safety_users`, `_seed_phase1` | ~5 |
| 22.1g · Scheduler-armament migration | 8 non-email schedulers | ~8 |
| 22.1h · Email-capable scheduler migration | 4 fingerprint-locked schedulers | 4 |
| 22.1i · Miscellaneous bootstrap migration | `_bootstrap_operations`, `_bootstrap_integrations`, `_bootstrap_user_directory`, other track-XX-XX handlers | ~10 |
| 22.1j · Readiness-flip migration | `_iter453_6_flip_ready_flag` + `_dispatch_reminder_scheduler_start` | 2 (must be last) |
| 22.1k · Shutdown migration | 1 shutdown handler | 1 |

Target completion: sometime in the roadmap when platform stability metrics permit.

## No pytest.ini filterwarnings band-aid

The mandate specifies: *"no `pytest.ini filterwarnings` band-aid unless migration cannot be safely completed."* We honor this — the 117 DeprecationWarnings are visible in every test run as a permanent reminder that migration is pending. Silencing them would hide progress.

## Verdict

🟡 **CLEANUP DEFERRED (documented).** Foundation delivered. Individual migrations queued into 7 follow-up tracks.
