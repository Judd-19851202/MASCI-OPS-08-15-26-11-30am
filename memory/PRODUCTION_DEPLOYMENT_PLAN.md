# PRODUCTION_DEPLOYMENT_PLAN

**Phase:** OMEGA Production Remediation · Phase 3 (Deployment Plan)
**Date:** 2026-05-30 (UTC)
**Mandate:** Plan only. Operator-controlled execution. NO agent-initiated deploy or migration.
**Scope:** Bring production into alignment with preview for Batch H + Batch K + Batch L + Wave 1 substrates + the photo migration.
**Pre-reqs satisfied:** `PRODUCTION_ALIGNMENT_REPORT.md` (delta enumerated) · `PHOTO_MIGRATION_VALIDATION.md` (script certified safe) · `PRODUCTION_RECOVERABILITY_REPORT.md` (scheduler + backups healthy).

---

## 🎯 OBJECTIVE

Move production from source_hash `8e8ec6da…` to `550118…` (preview parity), and convert all 86 production daily_reports from inline base64 to `photo://` refs, in a single operator-supervised window with three independent rollback paths armed.

Estimated total window: **~75 minutes** (60 min deploy + verification + 15 min migration).
Estimated user-visible disruption: **0 seconds** (the deploy is a rolling Emergent platform deploy; the migration is out-of-process).

---

## 1 · Exact deployment order

### Step 0 · Operator gate (T-30 min)

| Action | Owner | Required output |
|---|---|---|
| Authorize the deploy + migration window in chat | Operator | Written authorization timestamp |
| Verify operator has tail access to backend logs and DB | Operator | `tail -f /var/log/supervisor/backend.err.log` reachable |
| Confirm `/api/version` on prod = `8e8ec6da31cf225cae2db172573f49a0` | Agent (read-only) | `curl https://mascidocs.com/api/version` |
| Confirm `/api/version` on preview = `550118913c503ae6d206223be384372f` | Agent (read-only) | `curl https://backup-forensics.preview.emergentagent.com/api/version` |

### Step 1 · Cut a pre-deploy safety backup (T-25 min)

| Action | Mechanism | Verification |
|---|---|---|
| Trigger a complete-R2 backup archive on prod | Wait for next scheduler tick (cadence ~3 hr) **OR** trigger on-demand via the backup verification endpoint if operator has the X-Admin-Token | `recent_health` in backup scheduler readiness shows new `MASCI_complete_backup_<ts>.zip` with `ok=true` |
| Record the archive filename | Operator notes the exact filename | Filename appended to `OBSERVATION_LEDGER.json` |
| Verify archive size and record count | Probe `/api/admin/backup-verification/recent-health?limit=2` | `size_bytes ≥ previous archive` AND `records ≥ previous archive` |

### Step 2 · Deploy preview code to production (T-20 min → T+0)

| Action | Owner | Mechanism |
|---|---|---|
| Initiate Emergent platform deploy (preview → prod) | Operator | Standard "Deploy to Production" button in Emergent platform |
| Wait for build + push completion | Emergent platform | ~10–15 min build, ~5 min cutover |
| Confirm new SHA is live | Agent | `curl https://mascidocs.com/api/version` returns source_hash `550118913c503ae6d206223be384372f` |
| Confirm `app_env=production` and `db_name=masci_safety` post-deploy | Agent | Same `/api/version` response |
| Confirm `/api/health` 200 | Agent | `curl https://mascidocs.com/api/health` |

### Step 3 · Smoke probe — confirm new code paths are live (T+0 → T+10 min)

| Probe | Expected post-deploy behavior |
|---|---|
| `GET /api/health` | 🟢 200 |
| `GET /api/version` | source_hash matches preview |
| `GET /api/admin/backup-verification/recent-health` | scheduler still alive, ticking |
| Submit a single canary DR with 1 inline base64 photo via the official POST `/api/daily-reports` (operator-issued test payload) | DR is accepted, photos field stored as `photo://` ref (Batch H sanitizer fired) |
| Submit a canary Fleet DVIR with `monitor` severity (operator-issued test payload) | 1 task created with `source_module=fleet.dvir`, `assignee_role=shop`, priority=Medium; 1 notification `dvir.defect`; 1 auto `task.assigned` |
| Submit a canary Fleet DVIR with `oos` severity | 1 task Critical; 2 `dvir.defect.oos` notifications (shop + dispatch); 1 auto `task.assigned` |
| Submit a canary Safety Meeting | 1 task `source_module=safety.meeting` to safety; 1 notification `meeting.submitted` |
| `GET /api/tasks?limit=10` shows new task rows | confirms fan-out is wired |

If ALL probes pass → proceed to Step 4. Otherwise → execute Rollback Path A (Step 7.1).

### Step 4 · Cleanup canary test data (T+10 → T+12 min)

| Action | Mechanism |
|---|---|
| Delete canary DR, canary DVIRs, canary meeting from prod via authenticated DELETE / direct DB cleanup | Operator-supervised (script: `scripts/cleanup_canary_smoke.py` — pattern used in Batches K + L preview cleanups) |
| Verify task and notification counts return to baseline + zero new test rows | DB count probe |

### Step 5 · Run photo migration in dry-run mode (T+12 → T+15 min)

```bash
python3 /app/scripts/migrate_dr_photos.py \
  --target-db masci_safety \
  --i-know-this-is-prod \
  --backup-dir /app/memory/dr_migration_backups
```

(Note: `--apply` is NOT passed → dry-run only.)

Expected output: ~86 DRs to be migrated, ~270 MB total inline payload to compress to ~50 KB total refs. Summary table at the bottom should match `PHOTO_MIGRATION_STATUS_REPORT.md §4` projection.

### Step 6 · Run photo migration with `--limit 1` (T+15 → T+16 min)

```bash
python3 /app/scripts/migrate_dr_photos.py \
  --target-db masci_safety \
  --i-know-this-is-prod \
  --apply \
  --limit 1 \
  --backup-dir /app/memory/dr_migration_backups
```

Verify the single migrated DR:
- The DR's `photos[]` array now contains `photo://masci-hub/photos/2026/05/dr_<id>/0.jpg` style refs (no more `data:image/...`)
- The R2 object is reachable via `photo_storage.read_photo_bytes(ref)` (curl the rendered DR PDF)
- The `dr_migration_backups/<dr_id>.json` file exists on local disk and contains the pre-migration inline data
- `coll.find_one({"id": dr_id})._legacy_b64_migrated` is NOT set (that marker is from the LEGACY_BASE64_MIGRATION_PLAN.md design; the actual script does not set it — verify by absence; this is acceptable because the photo:// ref itself is the marker)

If verification passes → Step 7. Otherwise → Rollback Path A on the single DR.

### Step 7 · Run photo migration on full prod set (T+16 → T+30 min)

```bash
python3 /app/scripts/migrate_dr_photos.py \
  --target-db masci_safety \
  --i-know-this-is-prod \
  --apply \
  --backup-dir /app/memory/dr_migration_backups
```

Expected runtime: ~5–15 minutes for 86 DRs (~3–8 sec/DR including R2 PUTs).

### Step 8 · Post-migration verification (T+30 → T+35 min)

| Verification | Expected |
|---|---|
| Re-run dry-run | `Photos to migrate: 0` — confirms 100% migrated |
| Sample 5 random DRs via curl | All photos render via R2 (PDF export works) |
| Check `daily_reports` collection size | dropped from ~260 MB → ~2–3 MB |
| Check next backup archive | should drop from 464 MB → ~115 MB |
| Check `/api/version` | still `550118…`, uptime > 30 min |
| Check `/api/health` | 🟢 200 |
| Check scheduler `last_tick_ts` | continued advancing throughout the window |

---

## 2 · Exact rollback order

### Path A — Per-DR JSON rollback (FASTEST · ~5 min · used for partial-migration failures)

```bash
# Operator runs only on explicit decision
for f in /app/memory/dr_migration_backups/*.json; do
  python3 -c "
import json, os
from pymongo import MongoClient
mc = MongoClient(os.environ['MONGO_URL'])
doc = json.load(open('$f'))
mc['masci_safety'].daily_reports.replace_one({'id': doc['id']}, doc)
print('Restored', doc['id'])
"
done
```

Trigger when: a small number of DRs failed migration or the migration's behavior on prod differs from preview/staging.

### Path B — Full archive restore (SLOWEST · ~15 min · used for catastrophic data loss)

```bash
# Operator runs only on explicit decision
python3 /app/scripts/restore_drill.py \
  --archive MASCI_complete_backup_<ts>.zip \
  --target-db masci_safety \
  --collections daily_reports \
  --restore-photos
```

Trigger when: the `daily_reports` collection is irrecoverably mutated AND Path A is unavailable (no backup-dir, or backup-dir corrupted).

### Path C — Deploy rollback (~5 min · used if the deploy itself causes a regression)

| Action | Mechanism |
|---|---|
| Roll back the Emergent platform deploy to the previous SHA | Emergent platform "Rollback to previous deploy" button |
| Verify `/api/version` returns `8e8ec6da…` | curl |
| Verify `/api/health` is 200 | curl |
| Verify no `daily_reports` rows were mutated between deploy and rollback | Optional Path A if rows were mutated (unlikely since migration is a separate command) |

Trigger when: any of the Step-3 smoke probes fail OR an unexpected 5xx storm appears in the first 5 minutes post-deploy.

### Rollback decision tree

```
                        Failure detected
                              |
                              v
         Was it during the deploy/smoke? ── yes ──> Path C (deploy rollback)
                              |
                              no
                              |
                              v
         Were any DRs mutated by the migration? ── no ──> No rollback needed
                              |
                              yes
                              |
                              v
         Is the backup-dir intact? ── yes ──> Path A (per-DR JSON restore)
                              |
                              no
                              |
                              v
                       Path B (full archive restore)
```

---

## 3 · Expected downtime

| Component | Window | Notes |
|---|---|---|
| `/api/health` 5xx | **0 seconds** | Emergent platform deploy is rolling; old worker drains while new worker takes over |
| `/api/daily-reports` POST | **0 seconds** | Endpoint is always reachable. POST behavior changes from "inline base64 saved as-is" to "inline base64 → photo:// ref" — invisible to the user |
| `/api/tasks` and `/api/notifications` GET | **0 seconds** | Pre-existing endpoints, unchanged contract |
| Backup scheduler | **0 seconds** | Singleton scheduler in worker; survives rolling deploy |
| PM Project Detail page | **0 seconds** | Wave 1 sidecar is additive (new component, new mount point — no replacement) |

**Net expected downtime: 0 seconds.** This is a true zero-downtime deploy.

---

## 4 · Recovery path

If the platform becomes unrecoverable mid-window:

| Severity | Action | Owner | RTO |
|---|---|---|---|
| 🟡 Single-DR migration failure | Path A on that DR | Operator | ~30 sec |
| 🟡 Batch of DRs failed migration | Path A on all backed-up DRs | Operator | < 5 min |
| 🟠 Deploy regression (5xx storm) | Path C (Emergent rollback button) | Operator | ~5 min |
| 🔴 Full `daily_reports` corruption | Path B (`restore_drill.py` against pre-deploy archive) | Operator | ~15 min |
| 🔴 Mongo cluster failure (unrelated) | Standard Atlas-class failover + `restore_drill.py` | Atlas + Operator | < 30 min |
| 🔴 R2 unreachable mid-migration | Script soft-fails per DR (counts as `drs_failed`) · operator retries when R2 returns | Operator | minutes to hours depending on R2 |

The backup scheduler ALREADY runs every ~3 hr cutting archive snapshots. RTO documented in `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md` is < 30 min for any Mongo-only scenario.

---

## 5 · Verification steps

### 5.1 · Immediate post-deploy (T+5 min)

```bash
curl https://mascidocs.com/api/health
curl https://mascidocs.com/api/version | grep -E "source_hash|app_env|db_name|uptime_s"
curl https://mascidocs.com/api/admin/backup-verification/recent-health?limit=2 -H "X-Admin-Token: $ADMIN_TOKEN"
```

Pass criteria:
- `health.ok == true`
- `version.source_hash == "550118913c503ae6d206223be384372f"`
- `version.app_env == "production"`
- `version.db_name == "masci_safety"`
- `version.uptime_s > 30`
- `recent_health[0].ok == true`

### 5.2 · Canary fan-out probes (T+10 min)

Submit one canary record per workflow (operator-supervised) and confirm tasks/notifications appear with the expected `source_module`. List in `PRODUCTION_ALIGNMENT_REPORT.md §6` table.

### 5.3 · Photo migration verification (T+35 min)

```bash
# Re-run dry-run — must show 0 to migrate
python3 /app/scripts/migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod
```

Pass criteria:
- `Photos to migrate: 0`
- `DRs already clean: 86`
- `DRs failed: 0`

### 5.4 · Recoverability re-verification (T+45 min)

```bash
# Confirm scheduler is still healthy
curl https://mascidocs.com/api/admin/backup-verification/recent-health?limit=4 -H "X-Admin-Token: $ADMIN_TOKEN"
```

Pass criteria:
- `scheduler.alive == true`
- `last_tick_ts` advanced beyond start-of-window
- No new rows in `failed_attempts`

### 5.5 · Long-tail observation (T+24 hr)

| Check | Expected |
|---|---|
| Next complete-R2 archive size | drops from 464 MB → ~115 MB |
| R2 storage total | drops from 80 GB → ~20 GB (after lifecycle ages out old inline-bloated archives) |
| `recent_health` last 24 hr | all `ok=true` |
| Any user complaints about PDF export | none expected |
| Any 5xx spike on `/api/daily-reports/{id}` | none expected |

---

## 6 · Success criteria

ALL of the following MUST hold at T+35 min for the deploy + migration to be declared SUCCESSFUL:

| # | Criterion | Verifier |
|---|---|---|
| 1 | `/api/version.source_hash == 550118…` on prod | curl |
| 2 | `/api/health == 200 ok=true` on prod | curl |
| 3 | Canary DR fan-out emitted tasks + notifications with correct `source_module` | `/api/tasks` enumeration |
| 4 | Canary Fleet DVIR (monitor) emitted Shop task Medium + dvir.defect notification | `/api/tasks` + `/api/notifications` enumeration |
| 5 | Canary Fleet DVIR (OOS) emitted Shop task Critical + dual dvir.defect.oos notifications (shop + dispatch) | enumeration |
| 6 | Canary records cleaned up · tasks/notifications counts returned to pre-canary baseline | DB count |
| 7 | Photo migration dry-run-after-apply shows 0 to migrate | script summary |
| 8 | DRs already clean == 86, DRs failed == 0 | script summary |
| 9 | `/api/daily-reports/{any old DR}` PDF export renders all photos correctly | manual or curl-driven render |
| 10 | Backup scheduler `last_tick_ts` continued advancing throughout window | recent-health probe |
| 11 | No 5xx storm observed on `/api/daily-reports` POST or GET | log tail |
| 12 | `OBSERVATION_LEDGER.json` updated with deploy timestamp + migration counter | manual append |

## 7 · Stop-condition compliance

- ✅ Plan only · execution remains operator-controlled
- ✅ Three independent rollback paths armed before execution
- ✅ Zero-downtime architecture
- ✅ Per-DR atomic migration with backup-dir
- ✅ All canary probes documented before any cleanup
- ✅ No new features · no new endpoints introduced beyond what is already in preview
- ✅ Phase 1 + Phase 2 evidence packages produced before this plan was authored

---

_End of PRODUCTION_DEPLOYMENT_PLAN.md._
