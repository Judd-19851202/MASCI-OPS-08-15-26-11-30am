# COMPLETE_BACKUP_VERIFICATION_REPORT

**Date:** 2026-02-01 · Batch A · Step 6
**Authorized action:** Execute `POST /api/admin/backups/run-now?lite=false` against production once.

**Trigger time (UTC):** 2026-05-30T03:14:33Z
**Auth method:** `X-Admin-Token` header
**Raw response:** `/app/memory/batch_a_evidence/runnow_response.json`
**Post-trigger state (T+20s):** `/app/memory/batch_a_evidence/scheduler_state_after_20s.json`

---

## Trigger response

```json
{
  "accepted": true,
  "lite_mode": false,             ← the REQUEST was lite=false
  "poll": "/api/admin/backups-scheduler-state",
  "started_at": "2026-05-30T03:14:33.281898+00:00"
}
```

## Post-trigger state (T+20s)

```json
"manual_run": {
  "started_at": "2026-05-30T03:14:33.281898+00:00",
  "finished_at": "2026-05-30T03:14:39.182699+00:00",
  "outcome": "ok · MASCI_lite_backup_2026-05-30_031433Z.zip · 206 KB · emailed_to=jaymn.judd@mascigc.com",
  "lite_mode": false              ← the request flag is preserved
}
```

New `recent_health` row:
```json
{
  "id": "a918059bf33446deb78d5553efa89256",
  "ts": "2026-05-30T03:14:39.059548+00:00",
  "ok": true,
  "mode": "lite",                 ← actual mode WAS LITE despite lite=false request
  "filename": "MASCI_lite_backup_2026-05-30_031433Z.zip",
  "size_bytes": 211805,
  "records": 141,
  "emailed_to": "jaymn.judd@mascigc.com",
  "error": null
}
```

---

## Critical finding

**The `lite=false` query parameter is overridden by the `BACKUP_LITE_MODE_ONLY=true` env flag in production.**

Code path that overrides:
- `server.py:6723 use_lite = _lite_mode_default() if lite is None else bool(lite)` — but inside `_run_scheduled_backup(db, lite_mode=False)`, the helper consults `_lite_mode_default()` AGAIN when the lite flag falls through certain code paths.
- Conclusively: the filename `MASCI_lite_backup_*.zip` (lite prefix) + `mode: "lite"` in `backup_health` + 141 records (full-mode would have 200,000+) prove the run produced a lite backup.

**Implication:** `POST /api/admin/backups/run-now?lite=false` **cannot produce a complete-r2 backup in production** until either:
1. The `BACKUP_LITE_MODE_ONLY` env flag is cleared on the production worker, OR
2. The operator uses a different endpoint — most likely `POST /api/admin/backups/run-complete-now` (this is the explicit complete-archive code path; see `server.py:4889` docstring).

---

## What was actually verified

✅ **Manual lite backup pipeline still works** in production:
- Completion time: 5.90 seconds
- Output file: `MASCI_lite_backup_2026-05-30_031433Z.zip` (206 KB · 211 805 bytes)
- Record count: 141 (metadata-snapshot only — NOT the full dataset)
- Email delivered to `jaymn.judd@mascigc.com`
- `backup_health` row inserted successfully
- No errors, no exceptions, no hung process

❌ **Complete-r2 backup pipeline NOT verified** — the `lite=false` request was silently downgraded to lite mode by the env flag.

---

## Last verified complete-r2 backup remains: 2026-05-26 11:06 UTC

The production `backup_health` collection does not contain a `complete-r2` row in the most recent 10 entries (all 10 are `mode: "lite"`). The last `complete-r2` backup verified was on 2026-05-26 at 11:06 UTC per the prior `BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md` (and the `latest_r2_seed_query` confirmed during the 2026-05-29 diagnostic).

**Drift since last complete-r2 backup: 4 days (as of 2026-05-30 03:14 UTC).**

---

## Recommendations (operator decision required)

1. **For an actual complete-r2 backup verification**, the correct endpoint is `POST /api/admin/backups/run-complete-now`. This is the explicit Phase 2c complete-archive code path. Operator authorization required before calling.
2. **Alternative**: Temporarily clear `BACKUP_LITE_MODE_ONLY` on the production worker (requires env-var update + worker restart) to allow `run-now?lite=false` to actually run complete mode. Higher operational risk.
3. **Strategic**: Resolve the scheduler dead-state via the Phase 1 + Phase 2 hardening that was just deployed; once the scheduler is alive and ticking, scheduled backups will fire and operator may not need to manually trigger.

---

## Stop-condition compliance

- ✅ Single one-time write request to production
- ✅ Endpoint matches operator authorization (`POST /api/admin/backups/run-now?lite=false`)
- ✅ No scheduler code modification during this step
- ✅ No env-var changes
- ✅ Raw response + post-trigger state persisted under `/app/memory/batch_a_evidence/`
