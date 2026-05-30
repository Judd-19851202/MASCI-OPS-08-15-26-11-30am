# PRODUCTION_SCHEDULER_INSTRUMENTATION_DEPLOY_REPORT

**Date:** 2026-02-01 · Batch B · Step 1
**Authorized action:** Deploy Phase 1 + Phase 2 scheduler hardening from preview to production.

---

## Deploy mechanism

Emergent platform Deploy button (operator-driven via chat header). Agent has no platform-side deploy CLI/API. Operator clicked Deploy and confirmed live at 2026-05-30 ~04:00 UTC.

## Code shipped to production

`/app/backend/server.py` changes (from Batch A · Steps 7a + 7b):

| Code site | Change |
|-----------|--------|
| `_BACKUP_SCHEDULER_STATE` dict | 3 new keys: `boot_step`, `boot_step_ts`, `boot_exception` |
| `_record_boot_step(step, *, exc=None)` | New helper writes module state + structured log line |
| `_backup_scheduler_loop` body | 7 instrumentation call sites threaded through boot path |
| `_backup_scheduler_loop_with_capture(db)` | New wrapper coroutine — wraps `run_with_singleton_lock` in try/except so unhandled exceptions are captured before task terminates |
| Initial spawn site (~line 11299) | Routes through the wrapper |
| Supervisor resurrection site (~line 11357) | Routes through the wrapper |

**No scheduler logic was changed.** All edits are observability + defensive wrapping per Batch A authorization.

---

## Deploy verification

### Endpoint shape check
`GET https://mascidocs.com/api/admin/backups-scheduler-state` (post-deploy) returns the 3 new fields:

```
boot_step          : None         ← new key present
boot_step_ts       : None         ← new key present
boot_exception     : None         ← new key present
```

The presence of these keys in the production response **proves the deploy is live**.

### Production pod identity confirmed via `/api/version`
```
service:     masci-hub
source_hash: 8e8ec6da31cf225cae2db172573f49a0
started_at:  2026-05-30T04:00:09.687871+00:00
uptime_s:    257 (at probe time)
```

Pod started 257 seconds before the first probe — confirming a fresh deploy.

---

## Behavior verification on production

| Field | Expected for healthy scheduler | Expected for dead-state | Observed in production |
|-------|--------------------------------|-------------------------|------------------------|
| `boot_step` | `entering_main_tick_loop` (steady-state) | last stage reached before death | **`None`** |
| `boot_step_ts` | recent timestamp | recent timestamp | **`None`** |
| `boot_exception` | `None` (healthy) | exception class + repr | **`None`** |
| `alive` | `true` | `false` | **`false`** |
| `armed_at` | recent ISO timestamp | `null` (never reached) | **`null`** |
| `task_alive` | `true` | `false` | **`false`** |

The observed state means: **the scheduler task is dying BEFORE `_record_boot_step("entered_loop_body")` is even called.** Combined with `boot_exception: None`, this indicates a clean return inside `run_with_singleton_lock(...)` — i.e., the lock-acquirer returned without calling `scheduler_fn`. This is the smoking gun for the root cause investigation.

(Full analysis in `POST_DEPLOY_SCHEDULER_PROBE_REPORT.md`.)

---

## Stop-condition compliance

- ✅ Deploy was instrumentation + defensive wrapper only
- ✅ No new scheduler logic
- ✅ No env-var changes
- ✅ No retries, no emails, no Phase 3/4 hardening
- ✅ Operator-authorized deploy via Emergent Deploy button
- ✅ Post-deploy endpoint shape verified
