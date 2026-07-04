# TRACK 22.1J · Last-Position Invariant

## The invariant
> **The readiness handler MUST be the final action of the startup sequence.**
> No lifecycle step, no legacy `on_startup` handler, and no future insertion may execute after it.

## Enforcement

### 1. Orchestrator phase model
`orchestrated_lifespan(app)` (in `backend/lib/lifespan_bootstrap.py`) now executes startup in **three ordered phases**:

```
phase-1  →  LIFECYCLE_STEPS where group != "readiness"
phase-2  →  app.router.on_startup   (remaining legacy decorators, source-order)
phase-3  →  LIFECYCLE_STEPS where group == "readiness"      ← LAST
yield
shutdown  →  app.router.on_shutdown
```

Phase-3 is the ONLY place a `group="readiness"` step ever runs.

### 2. Registration-time invariant (readiness group is single-purpose)
Only the readiness flip should ever be in `group="readiness"`. If a future decorator uses the readiness group by mistake, its side effects also inherit the last-phase guarantee — which is fine so long as it's a readiness-safe operation. Any misuse is caught by:
- Lock test `test_readiness_group_size_is_exactly_1` (asserts group size).
- Platform Ops API `lifecycle.registry.readiness_last_invariant.readiness_group_size` (visible in preview + prod).

### 3. Test-time invariant
`test_readiness_last_invariant` (in `test_track_22_1j_readiness_last_migration.py`):
- Asserts `_iter453_6_flip_ready_flag` is the ONLY entry in `LIFECYCLE_STEPS` with `group="readiness"`.
- Asserts phase-1 has exactly 48 non-readiness steps and phase-3 has exactly 1.
- Asserts phase-2 still contains `_startup` from `routes.command_center` (Track 22.1L will drop this).
- Asserts the readiness handler is no longer in `app.router.on_startup`.

### 4. Boot-log invariant
Post-migration the log emits, in strict order:
```
[track-22.1e] lifespan.startup: executing 48 LIFECYCLE_STEPS (non-readiness)
[track-22.1e] lifespan.startup: LIFECYCLE_STEPS (non-readiness) complete
[track-22.1d] lifespan.startup: executing 1 handlers
[track-22.1d] lifespan.startup: complete
[track-22.1j] lifespan.startup: executing 1 readiness LIFECYCLE_STEPS (final phase)
[iter453.6] startup-readiness gate FLIPPED · public writes now accepted
[track-22.1j] lifespan.startup: readiness phase complete
```
The `[iter453.6]` line MUST appear AFTER `[track-22.1d] lifespan.startup: complete`.

### 5. Platform Ops API attestation
`GET /api/admin/platform/status` now exposes:
```json
{
  "lifecycle": {
    "registry": {
      "readiness_last_invariant": {
        "readiness_group_size": 1,
        "readiness_handlers": ["_iter453_6_flip_ready_flag"],
        "runs_after_non_readiness_lifecycle_steps": true,
        "runs_after_legacy_on_startup": true,
        "final_phase_of_lifespan": true
      }
    }
  }
}
```

## Rollback
Revert 2 files:
1. `backend/server.py` — flip decorator back to `@app.on_event("startup")`.
2. `backend/lib/lifespan_bootstrap.py` — collapse phase-1/phase-3 back into a single phase.

## Conclusion
🟢 **INVARIANT CERTIFIED.** Readiness is enforced-last by orchestrator design, lock test, boot log, and admin API. Four independent enforcement layers.
