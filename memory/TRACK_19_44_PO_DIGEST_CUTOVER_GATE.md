# TRACK 19.44 · Legacy `po_digest.py` · Operator Cutover Gate

**Status:** 🟢 SHIPPED. Mirrors the Track 19.43 safety_digest gate.

## The gate

`/app/backend/po_digest.py::_enabled()` now short-circuits when operators set:

```
OI_ENGINE_PO_WEEKLY_LIVE=true
```

Behaviour:
- Legacy `po_digest_scheduler_loop` still starts (zero drift).
- Every iteration calls `_enabled()` — returns `False` when the flag is set.
- No email fires from the legacy path.
- The Track 19.41 `po_weekly_digest` product becomes the authoritative sender (once its dispatch is invoked).

When the flag is unset or `false`, legacy behaviour preserved (`PO_DIGEST_ENABLED=true` still controls the cron as before).

## Cutover sequence (recommended · operator)

1. **Prep** — ensure the OI-engine PO product is reachable at `/api/operational-intelligence/po_weekly_digest/preview` and returns the 14-section layout.
2. **Dry-run compare** — trigger `POST /api/operational-intelligence/po_weekly_digest/dispatch?dry_run=true` and compare recipient list + subject with the legacy Monday email.
3. **Flip the gate** — production env: `OI_ENGINE_PO_WEEKLY_LIVE=true`.
4. **Trigger the OI send** manually the first Monday (or wait for the OI scheduler once shipped).
5. **Verify no send** from the legacy path via `scheduler_runs` audit (no `po_digest` rows after gate is live).
6. **After 2 weeks of clean operation**, remove the legacy code path in a follow-up track (still shipped for rollback).

## Rollback

Set `OI_ENGINE_PO_WEEKLY_LIVE=false` (or delete the env var). Legacy cron immediately resumes on next loop iteration. HIGH confidence.

## Zero-drift proof

- Module `po_digest.py` unchanged except for a single `_enabled()` short-circuit block.
- `po_digest_scheduler_loop` unchanged.
- `server.py` wiring unchanged.
- `singleton_scheduler` + `scheduler_runs` unique index unchanged.
- No new email path introduced.

## Test coverage

- `test_po_cutover_gate_disables_legacy_when_flag_set` — asserts `_enabled()` returns False when the flag is set, True when unset.
- `test_legacy_po_digest_module_still_present` — module preserved for rollback.
