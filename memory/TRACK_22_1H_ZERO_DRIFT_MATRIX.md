# TRACK 22.1H · Zero-Drift Matrix

## What changed

| Change | File(s) | Kind |
|---|---|---|
| 5 email-capable scheduler decorator swaps (`@app.on_event("startup")` → `@register_lifecycle_step("email-scheduler")`) | `backend/server.py` (5 single-line diffs) | Runtime code — decorator swap only, function bodies byte-identical (bytecode SHA-256 preserved for all 5) |
| Pre-existing double-registration closure for `_start_safety_digest_cron` | `backend/server.py` (1 leftover `@app.on_event("startup")` line removed) | **Defect fix** — see § "Defect closure detail" |
| Platform Ops API: `email-scheduler.closed=True`, `22.1H` in `recent_track_closures`, recommendation queue promoted to 22.1I | `backend/lib/platform_status.py` (additive-only ~6 lines) | Additive field update within `attestation_version=22.1F` contract |
| Runtime snapshots (before, after) | `memory/track_22_1h/RUNTIME_ENUMERATION_*.json` | Evidence |
| Lock test | `backend/tests/test_track_22_1h_email_scheduler_migration.py` (16 assertions) | Test infrastructure |
| 12 memory MDs | `memory/TRACK_22_1H_*.md` | Documentation |
| Ledgers | PRD · CHANGELOG · Debt Register · Platform Manifest | Documentation |

**Runtime code files touched:** 2 — `backend/server.py` (5 decorator swaps + 1 defect-fix line removal) + `backend/lib/platform_status.py` (additive updates).

## What did NOT change

- **1,441 routes** — same set, same methods, same `endpoint_qualname`, same `dependency_chain`. Zero drift.
- **1,264 OpenAPI paths.**
- **7 middleware entries** — byte-equal chain.
- **1 shutdown handler** — same qualname, same bytecode.
- **3 exception handlers.**
- **5 locked bytecode fingerprints** — all match live post-22.1H:
  - `_dispatch_auto_email`: `ebf525...`
  - `_start_safety_digest_cron`: `9aabbd...`
  - `_start_operator_digest_cron`: `8f28a8...`
  - `_start_po_digest_cron`: `5158200...`
  - `_dispatch_reminder_scheduler_start`: `5a6e39...`
- **`_start_backup_verification_cron`** bytecode SHA-256 (newly recorded at `36bf2f8f...`) — stable; will be the reference for future drift audits.
- **5 migrated scheduler bodies** — byte-identical.
- **Email safety envelope** — 3 layers intact. SDK patch position preserved. `lib/lifespan_bootstrap.py` + `lib/platform_status.py` still AST-verified no `import resend` at module scope.
- **CORS explicit allow-lists** — preserved.
- **`EMAIL_SAFETY_MODE=strict`** — preserved.
- **Singleton-lock keys / cadences / env gates / recipient paths.** Zero changes.
- **Every Mongo collection, schema, field, index definition, TTL, unique/sparse option.**
- **Every auth gate.**
- **Frontend** — untouched.
- **All 17 prior-track lock tests** — still committed.
- **Every handler still fires at least once per boot.** 27 via `LIFECYCLE_STEPS`, 23 via `app.router.on_startup`. Unique lifecycle callables: **50** (was 51 with dupe).

## Defect closure detail

**Finding:** In the pre-22.1H source, `_start_safety_digest_cron` had TWO `@app.on_event("startup")` decorators (a stray copy-paste in some earlier iteration). FastAPI processes each decorator independently and registers the same coroutine into `app.router.on_startup` twice.

**Effect pre-22.1H:**
- `asyncio.create_task(...)` invoked TWICE per boot.
- The `run_with_singleton_lock(db, "safety_digest", ...)` inside the loop body ensured only ONE cluster-wide instance actually ran, so no duplicate emails were dispatched.
- Visible artifact: one wasted asyncio task per boot; one extra "task launched" log line; one item too many in `on_startup` list length; one extra deprecation warning per pytest run.

**Fix in Track 22.1H:** During the standard 5-way decorator swap, my initial search_replace matched only the FIRST `@app.on_event("startup")` (immediately above the def), leaving the SECOND (one line up) stacked with the new `@register_lifecycle_step("email-scheduler")`. Runtime snapshot showed the double-registration; the main agent removed the leftover `@app.on_event("startup")` line and re-verified the enumeration.

**Post-22.1H:**
- Exactly ONE decorator on `_start_safety_digest_cron`: `@register_lifecycle_step("email-scheduler")`.
- Fires exactly ONCE per boot.
- Bytecode SHA-256 unchanged (`9aabbd...`).
- All fingerprint locks pass.

**Classification:** Class C (pre-existing engineering debt) → **CLOSED** as part of Track 22.1H per constitutional mandate ("If anything is found broken, own it and fix it if safe").

## Production impact

**Zero on existing surfaces + one silent improvement.** The 5 email-capable schedulers now schedule their asyncio tasks marginally earlier during boot (during `LIFECYCLE_STEPS` phase). The tasks' cadences are unchanged (Monday 14:00 UTC weekly, etc.). The pre-existing double-fire of the safety digest scheduler is retired — one wasted asyncio task per boot recovered.

`/api/admin/platform/status.lifecycle.migration_progress.migrated_pct` climbs from 43.14% → **54.00%**.

Boot log deltas:

```
[track-22.1e] lifespan.startup: executing 27 LIFECYCLE_STEPS   (was 22)
[track-22.1d] lifespan.startup: executing 23 handlers          (was 29)
```

## Rollback path

1. In `backend/server.py`, replace the 5 `@register_lifecycle_step("email-scheduler")` decorators with `@app.on_event("startup")` (single-line revert per handler).
2. Re-insert the leftover `@app.on_event("startup")` line above `_start_safety_digest_cron` if you want the pre-existing double-registration bug restored (**NOT RECOMMENDED**).
3. In `backend/lib/platform_status.py`, revert `email-scheduler.closed` to `False`, remove `22.1H` from `recent_track_closures`, revert recommendation queue.
4. Delete `backend/tests/test_track_22_1h_email_scheduler_migration.py`.
5. Delete `memory/track_22_1h/` snapshots and 12 memory MDs.
6. Revert the four ledger blocks (PRD · CHANGELOG · Debt Register · Platform Manifest).

FastAPI reverts to Track 22.1G state.

## Zero-drift verdict

🟢 **CERTIFIED.** Zero route drift. Zero OpenAPI drift. Zero handler bytecode drift. Zero email dispatch path change. Zero recipient path change. Zero live-email risk. Only 5 single-line decorator swaps + 1 defect-fix line removal + 1 additive Platform Ops API update.
