# TRACK 19.43 · Legacy `safety_digest.py` · Operator Cutover Gate

**Status:** 🟢 SHIPPED. Single-env-flag cutover.

## The gate

`/app/backend/safety_digest.py::_enabled()` now short-circuits when the operator sets:

```
OI_ENGINE_SAFETY_MORNING_LIVE=true
```

When this flag is set:
- The legacy safety_digest cron loop `safety_digest_scheduler_loop` still starts.
- `_enabled()` returns `False` → each loop iteration sleeps and skips send.
- No email fires from the legacy path.
- The Track 19.39 Morning Safety Intelligence product becomes the authoritative sender.

When the flag is unset (or `false`):
- Legacy behaviour preserved verbatim — `SAFETY_DIGEST_ENABLED` controls the cron.

## Cutover sequence (recommended)

1. **Operator preparation** — add current `SAFETY_DIGEST_TO_EMAIL` recipients into `morning_digest_recipients` (`digest_type=safety_morning_digest`) via the Track 19.39 admin endpoints.
2. **Operator dry-run** — POST `/api/incident-intelligence/morning-digest/send?dry_run=true` and verify preview.
3. **Set the gate** — production env: `OI_ENGINE_SAFETY_MORNING_LIVE=true`.
4. **Trigger the Track 19.39 send** manually the first Monday (or wait for the next weekly cadence when the OI scheduler ships).
5. **Verify no send** from the legacy path via `scheduler_runs` audit (no rows for `safety_digest` after the gate is live).
6. **After 2 weeks of clean operation**, remove the legacy code path in Track 19.44 (still shipped for rollback).

## Rollback

Set `OI_ENGINE_SAFETY_MORNING_LIVE=false` (or delete the env var). Legacy cron immediately resumes on next iteration. HIGH confidence.

## Zero-drift proof

- Module `safety_digest.py` unchanged except for a single `_enabled()` short-circuit.
- `safety_digest_scheduler_loop` unchanged.
- `server.py` wiring unchanged.
- `singleton_scheduler` unchanged.
- No new email path introduced.

## Test coverage

- `test_cutover_gate_disables_legacy_safety_digest` — asserts `_enabled()` returns False when the flag is set, True when unset.
- `test_legacy_safety_digest_module_still_present` — module preserved for rollback.
