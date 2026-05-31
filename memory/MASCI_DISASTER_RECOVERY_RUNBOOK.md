# MASCI Disaster Recovery Runbook

**Audience:** Any competent platform operator. Assumes NO prior knowledge of MASCI.
**Goal:** Restore the platform to working order in ≤ 15 minutes without help from the original builder.
**Last verified:** 2026-05-31 (UTC) — by drill `f74aeea3df2f`, 4.937 min wall time, all 10 axes green.
**Print this. Keep a copy offline.**

---

## 0 · TL;DR (5 lines)

1. Find the most recent archive: R2 bucket `masci-hub`, prefix `backups/auto-90d/`, filename `MASCI_complete_backup_<UTC>.zip`.
2. Run `python3 /app/scripts/restore_drill.py --backup <archive_key> --target-db masci_recovery --restore-photos --seed-user-passwords`.
3. Point the production API at the new DB (`MONGO_URL` + `DB_NAME=masci_recovery`).
4. Restart the API worker (supervisor or Emergent deploy).
5. Verify `/api/health` + admin login + one Daily Report submit.

If all 5 succeed in ≤ 15 min, recovery is complete.

---

## 1 · System architecture (one page)

```
   ┌──────────────┐         ┌───────────────────┐         ┌──────────────────┐
   │  Browser/UI  │──HTTPS─▶│  Cloudflare proxy │──HTTPS─▶│  API worker pod  │
   └──────────────┘         └───────────────────┘         │  (FastAPI/uvicorn)│
                                                          └──────┬───────────┘
                                                                 │
                                       ┌─────────────────────────┼─────────────────────────┐
                                       │                         │                         │
                                       ▼                         ▼                         ▼
                            ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
                            │  MongoDB Atlas     │    │  Cloudflare R2     │    │  Resend (email)    │
                            │  cluster:masci-prod│    │  bucket: masci-hub │    │  outbound only     │
                            │  db: masci_safety  │    │  photos/* + backups│    └────────────────────┘
                            └────────────────────┘    │  /auto-90d/*       │
                                                      └────────────────────┘
```

| Component | Holds | Loss of this means |
|---|---|---|
| MongoDB Atlas (`masci_safety`) | All business records | Restore from R2 archive (this runbook §5) |
| R2 bucket `masci-hub` `photos/*` | All operational photos | Re-upload from archive's `photos/*` |
| R2 bucket `masci-hub` `backups/auto-90d/*` | 90 days of complete archives | Recovery becomes harder · use any out-of-band copy you have |
| API worker pod | In-flight requests | Just restarts; no data lost |
| Resend | Email transport only | Email fails silently · no business data lost |
| Cloudflare proxy | TLS termination + caching | Bypass with origin IP if needed; not a data risk |

---

## 2 · The 4 disaster scenarios

### 2.1 · API worker crash / pod restart

**Symptom:** `/api/health` returns 502/503 or times out. Browser shows error.
**Lost:** in-flight requests, sessions; in-process idempotency cache; per-process counters.
**Recovery:** wait for Kubernetes/Emergent restart (~30 s) OR `sudo supervisorctl restart backend`.
**RTO:** 30-60 s. **RPO:** 0.
**Verification:** `curl https://mascidocs.com/api/health` → `{"ok":true}`.

### 2.2 · Mongo failure (Atlas region down / cluster lost)

**Symptom:** `/api/health` may still respond but `/api/version` and all routes return 500.
**Lost:** every Mongo write since the last archive timestamp.
**Recovery (this runbook §5):** restore from latest R2 archive into a NEW Atlas DB; flip `MONGO_URL`/`DB_NAME`; restart API.
**RTO:** ≤ 15 min. **RPO:** ≤ 60 min (hourly cadence) or ≤ 24 h (daily cadence). Check `/admin/recovery` for current state.
**Verification:** §7 below.

### 2.3 · R2 failure (Cloudflare R2 region down)

**Symptom:** Mongo + API still alive. Photos fail to load (broken image icons). Backups stop succeeding.
**Lost:** Photo SERVING (until R2 recovers). Mongo business records: ZERO loss (Mongo is system of record).
**Recovery:**
- If R2 returns within hours: do nothing; service resumes when R2 does.
- If R2 is dead permanently: provision a new R2 (or S3-compatible) bucket; re-upload the most recent archive's `photos/*` prefix; update `S3_ENDPOINT_URL` / `S3_BUCKET` env vars; restart API. (NOTE: `photo://` refs in Mongo encode the bucket — schema change may be needed.)
**RTO:** 30-60 min for full photo re-population. **RPO:** 0 for Mongo data.

### 2.4 · Both Mongo AND R2 lost (worst case)

**Lost:** Everything not in your offline archive copy.
**Recovery:** restore from any saved archive (operator off-platform backups). The archive is self-contained: it carries every business record + every photo as inline binary. Single zip = whole platform.
**RTO:** ≤ 15 min once you have the archive in hand.
**Mitigation tip:** download the latest archive once a week (manual click in `/admin/system` "Run Complete Backup Now" → save the presigned-URL ZIP to your laptop). 7-day-old copy = bounded worst-case loss.

---

## 3 · Required credentials & access (pre-disaster collection)

A future operator needs these BEFORE a disaster strikes. Store them in a secrets vault, NOT in this runbook:

| Credential | Used for |
|---|---|
| MongoDB Atlas org credentials | Create new cluster / new DB |
| Cloudflare account login | R2 console access |
| Emergent platform login | Redeploy API with new env |
| `ADMIN_PASSWORD` (current: see `/app/memory/test_credentials.md`) | Post-restore admin login |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | R2 boto3 access (see `/app/backend/.env`) |
| Resend API key | Restore email-sending (optional) |

Stop reading this runbook now and verify you can find each of the above. If you can't find one, fix that today, not during a disaster.

---

## 4 · Pre-flight checks (run anytime · not during a disaster)

```bash
# 1. Latest archive exists in R2
python3 /app/scripts/automated_drill.py --auto

# 2. Recovery dashboard is GREEN
curl -H "X-Admin-Token: <hmac>" https://mascidocs.com/api/admin/recovery/snapshot \
  | python3 -m json.tool | grep -E '"pill"|"backup_age_minutes"'

# 3. Last drill outcome is "ok"
# (read `last_drill` field from the snapshot above)
```

If any of these fail in steady state, you have a problem BEFORE a disaster.

---

## 5 · Recovery procedure (Mongo-loss path)

### 5.1 · Inventory

```bash
# What's the latest healthy archive?
python3 -c "
import os, boto3
from botocore.config import Config
for line in open('/app/backend/.env'):
    if '=' in line and not line.strip().startswith('#'):
        k,_,v=line.strip().partition('=')
        os.environ.setdefault(k,v.strip('\"').strip(\"'\"))
s3 = boto3.client('s3',
    endpoint_url=os.environ['S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    region_name='auto',
    config=Config(signature_version='s3v4', s3={'addressing_style':'path'}))
out = []
for page in s3.get_paginator('list_objects_v2').paginate(
        Bucket=os.environ['S3_BUCKET'], Prefix='backups/auto-90d/'):
    for o in page.get('Contents') or []:
        if o['Key'].endswith('.zip'):
            out.append((o['LastModified'], o['Size']/1e6, o['Key']))
out.sort(reverse=True)
for t,s,k in out[:5]: print(f'{t}  {s:.1f} MB  {k}')
"
```

### 5.2 · Restore

```bash
# Replace KEY with the most recent archive
KEY="backups/auto-90d/MASCI_complete_backup_<UTC>.zip"

# Choose a NEW target DB name (NEVER reuse a live DB name)
TARGET="masci_recovery_$(date -u +%Y%m%d_%H%M%S)"

# Run restore with photo rehydration and user-password seeding
python3 /app/scripts/restore_drill.py \
    --backup "$KEY" \
    --target-db "$TARGET" \
    --restore-photos \
    --seed-user-passwords
```

Expected wall time: **3-5 minutes** for a typical 300-400 MB archive (proven multiple times).

### 5.3 · Cut over

Update the production env:

```
MONGO_URL=mongodb+srv://...   # may be unchanged; same cluster, different DB
DB_NAME=masci_recovery_<ts>   # the new target DB from step 5.2
```

Restart the API worker:

```bash
# Emergent platform: trigger redeploy with new env
# OR if you have shell access: sudo supervisorctl restart backend
```

### 5.4 · Verify

Run §7 verification checklist.

### 5.5 · Cleanup

After 24 h of stable operation:

```bash
# Promote the recovery DB to the canonical name
# (Atlas: create alias, or via mongodump/mongorestore one-shot rename)
# Or just keep DB_NAME=masci_recovery_<ts> as the new permanent name.

# Drop any old corrupted DB after evidence is preserved.
```

---

## 6 · Recovery procedure (R2-loss path)

### 6.1 · Provision replacement bucket

Cloudflare R2 console → new bucket (or any S3-compatible storage). Note the endpoint + credentials.

### 6.2 · Repopulate photos from latest archive

```bash
# Download latest archive (use §5.1 inventory)
KEY="backups/auto-90d/MASCI_complete_backup_<UTC>.zip"

# Extract photos to local tmp
python3 -c "
import boto3, zipfile, os
from botocore.config import Config
for line in open('/app/backend/.env'):
    if '=' in line and not line.strip().startswith('#'):
        k,_,v=line.strip().partition('=')
        os.environ.setdefault(k,v.strip('\"').strip(\"'\"))
# download into /tmp/recovery.zip
... # see scripts/restore_drill.py for full extraction pattern
"

# Re-upload photos/* to new bucket using boto3 (~30-60 min for ~300 MB)
```

### 6.3 · Update env

```
S3_ENDPOINT_URL=<new-bucket-endpoint>
S3_BUCKET=<new-bucket-name>
S3_ACCESS_KEY=<new-key>
S3_SECRET_KEY=<new-secret>
```

Restart API. `photo://` refs in Mongo encode the bucket — if you renamed the bucket, you may need a one-time Mongo `$set` over all collections to rewrite `photo://oldbucket/...` → `photo://newbucket/...`. See §7 verification.

---

## 7 · Verification checklist (every recovery cycle)

Tick each off in order:

| # | Check | Expected | If fail |
|---|---|---|---|
| 1 | `curl https://mascidocs.com/api/health` | `{"ok":true,...}` | API worker not started · check supervisor / Emergent deploy |
| 2 | `curl https://mascidocs.com/api/version` | `db_name = <new target>` | env var not picked up · restart |
| 3 | Admin login at `/admin/login` | Success | `ADMIN_PASSWORD` env mismatch · re-set |
| 4 | `/admin/recovery` dashboard | `pill=GREEN` after one fresh backup | Trigger manual backup via `/admin/system` |
| 5 | Submit one Daily Report via UI | Saves successfully · email triggers · bell appears | Write path broken · check Mongo connection |
| 6 | Open a recently-restored Daily Report | Photos render | `photo://` refs broken · re-run §6 photo migration if needed |
| 7 | Run `python3 /app/scripts/automated_drill.py --auto` against the latest archive | All 10 axes GREEN | Drift found · investigate the failed axis |

**Sign off:** Operator signs the checklist with name + timestamp once all 7 pass.

---

## 8 · Expected recovery times

| Scenario | Detection | Restore | Cut-over | Verification | **Total** |
|---|---:|---:|---:|---:|---:|
| API worker crash | <1 min (auto-monitor) | n/a | n/a | 1 min | **2 min** |
| Mongo loss | 1-5 min | 3-5 min | 2-5 min | 3-5 min | **≤ 15 min** |
| R2 loss (transient) | 1-5 min | 0 (wait) | 0 | 0 | **R2-dependent** |
| R2 loss (permanent) | 5-15 min | 30-60 min | 5 min | 5 min | **~75 min** (photos) + 0 (data) |
| Both lost | 10-30 min | 5 min + 30-60 min | 5 min | 5 min | **~75-105 min** |

---

## 9 · Escalation contacts

| Tier | Role | Where to find |
|---|---|---|
| Tier 1 | Platform operator (you) | this runbook |
| Tier 2 | Emergent Support | https://emergent.sh support channels |
| Tier 3 | MongoDB Atlas Support | Atlas console → Support |
| Tier 4 | Cloudflare R2 Support | Cloudflare console → Support |

Original builder (Jaymn): cite this runbook before pinging. The runbook should answer the question without needing the original builder.

---

## 10 · Final sign-off process

After a recovery event, fill in the post-incident sign-off:

```
RECOVERY EVENT REPORT — <date>
==============================
Detected by    : <name>          at <ts>
Scenario       : [API/Mongo/R2/Both]
Archive used   : MASCI_complete_backup_<utc>.zip
Target DB used : masci_recovery_<ts>
RTO actual     : <minutes>       (target: 15)
RPO actual     : <minutes>       (target: 60 hourly · 1440 daily)
Verification   : §7 checklist 1-7 all passed
Anomalies      : <free text · or "none">
Sign-off       : <operator name + ts>

Filed to       : /app/memory/INCIDENT_<utc>.md
```

Commit the report to memory. The next operator should be able to learn from your incident.

---

## 11 · Steady-state confidence tests (do these monthly, not during a disaster)

| Test | How |
|---|---|
| **A** Trigger one manual backup | `/admin/system` → "Run Complete Backup Now" |
| **B** Run one automated drill | `bash /app/scripts/weekly_drill.sh` |
| **C** Verify dashboard goes GREEN | `/admin/recovery` |
| **D** Download latest archive to your laptop | as offline copy (out-of-band) |

Doing **A-D once a month** keeps the recovery muscle warm. The first time you need this runbook should not be a discovery exercise.

---

_End of MASCI_DISASTER_RECOVERY_RUNBOOK.md._
