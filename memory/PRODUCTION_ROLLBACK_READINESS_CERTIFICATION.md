# PRODUCTION ROLLBACK READINESS CERTIFICATION

**Date**: 2026-02-12

---

## ROLLBACK REFERENCE EXISTS

✅ `/app/memory/DEPLOYMENT_ROLLBACK_REFERENCE.md` written 2026-02-12.

Contents:
* **Current HEAD** (this deployment): `d00a56fb9b15f51b57990a67fd91d3b03de54047`
* **Previous stable commit**: `3fb5c3a5b9c18a7d11ea5afa4957f9bf10c6bdef` (pre-CORS-fix · pre-gitignore-fix · pre-i18n-fix)
* **Soft rollback** (one file) command documented
* **Full rollback** procedure documented (use Emergent platform Rollback feature, NOT `git reset`)

---

## DATABASE BACKUP POLICY

Observed in `/app/backend/.env`:

```
BACKUP_HOURS_UTC=2,18                  # daily backups at 02:00 and 18:00 UTC
BACKUP_R2_HOURLY=true                  # hourly R2 backups in addition
SCHEDULER_ENABLED=false                # PREVIEW value — preview pod does not run schedulers
```

Per `server.py` boot log (verified during deployment):

```
[scheduled-backup] supervisor armed — checks task health every 5 min
[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days · max 3 files · disk-watermark 75% · dir=/app/backend/backups
[scheduled-backup] scheduler disabled on this worker (preview / non-prod)
```

Backup mechanism is wired and active when `SCHEDULER_ENABLED=true`. **Operator must verify `SCHEDULER_ENABLED=true` in production env** before cutover.

### Backup verification command (operator runs on production pod)

```bash
ls -la /app/backend/backups/      # most recent N backup files; expect daily files dated within last 24h
```

Expected after first 24h of production: 1–3 `.archive` or `.dump` files dated within the last 24 hours.

---

## R2 BACKUP / INVENTORY POLICY

`BACKUP_R2_HOURLY=true` — backups are also pushed to R2.

* Bucket: `masci-hub` (shared in current config; see `R2_STORAGE_SEPARATION_CERTIFICATION.md` for production separation requirement)
* Path: under `backups/` prefix (per backup helper)
* Retention: 14 days local + indefinite in R2 unless lifecycle rule applied

**Operator action**: confirm R2 lifecycle rule (recommend 30 days for hot tier, archive thereafter).

---

## ROLLBACK PROCEDURE — OPERATOR PLAYBOOK

### Scenario A · Code rollback only (UI/translation/CORS/.gitignore fixes need to be undone)

1. Open Emergent platform dashboard → Deployments → Checkpoint list.
2. Select checkpoint corresponding to commit `3fb5c3a` (pre-this-deployment).
3. Click **Rollback** (free of charge per Emergent platform support guidance).
4. Verify Preview URL serves the prior code state.
5. No DB action required — schema unchanged.

### Scenario B · Code rollback + DB restore (something corrupted writes)

1. Identify the time-of-corruption from `audit_events` or application logs.
2. From `/app/backend/backups/`, pick the most recent backup file dated BEFORE the corruption time.
3. Operator coordinates with MongoDB Atlas point-in-time-restore via Atlas dashboard (separate from Emergent platform).
4. Confirm restore by spot-checking key collections (`users`, `trench_safety_assets`, `trench_excavations`) for correct counts.

### Scenario C · Production secret rotation rollback

If a rotated secret breaks production:
1. Restore previous secret value from your secret vault.
2. Update Emergent prod env in dashboard.
3. Restart backend (Emergent platform auto-restarts on env change).
4. Verify login flow works.

---

## OPERATOR-FACING ROLLBACK COMMANDS (one-pager · for cutover binder)

```bash
# Health check (any environment):
curl -s -o /dev/null -w "%{http_code}\n" $REACT_APP_BACKEND_URL/api/trench-safety/excavations/public/asset-roster?limit=1

# DB ping (production pod):
python3 -c "from pymongo import MongoClient; import os; print(MongoClient(os.environ['MONGO_URL']).admin.command('ping'))"

# Latest backup verification (production pod):
ls -lt /app/backend/backups/ | head -5

# Emergency code rollback (Emergent dashboard):
#   Deployments → Checkpoints → select previous green checkpoint → Rollback
```

---

## VERDICT

| Item | Status |
|---|---|
| Rollback reference exists | ✅ `DEPLOYMENT_ROLLBACK_REFERENCE.md` |
| Previous stable commit documented | ✅ `3fb5c3a` |
| Current commit documented | ✅ `d00a56f` |
| DB backup mechanism active in production | ⚠️ requires operator to flip `SCHEDULER_ENABLED=true` (currently `false` per preview) |
| R2 inventory / backup policy documented | ✅ this file |
| Operator rollback path documented | ✅ Emergent platform Rollback feature · Atlas PIT restore for DB |
| One-page cutover binder commands | ✅ this file |

# **PASS** (with operator action item: confirm `SCHEDULER_ENABLED=true` in production env before cutover)

Operator signature line:

```
SCHEDULER_ENABLED in production : [ ] true
First daily backup created      : __________ (date/time)
Atlas PIT restore tested        : [ ] yes / [ ] no

Operator signature : __________________________
Date               : __________________________
```
