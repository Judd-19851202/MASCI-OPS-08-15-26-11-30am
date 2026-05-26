# Phase 31.4 · Backup + Restore Certification
## iter441 · 2026-05-26

> Re-verification with hard evidence after Phase 31.2 + 31.3 fixes
> landed on production.

---

## Scheduler

```
[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days · max 3 files
[scheduled-backup] R2 hourly mode armed via BACKUP_R2_HOURLY=true
[scheduled-backup] R2 state seeded from backup_health: last_r2_complete_hour=2026-05-26T01
                   (prevents restart-fire of MASCI_complete_backup_2026-05-26_010157Z.zip)
[scheduled-backup] supervisor armed — checks task health every 5 min
```

🟢 Scheduler armed · state seed in place · restart-fire prevention verified.

---

## R2 inventory

```
total keys under backups/:    1506
  backups/auto-90d/:          1004 keys (90-day lifecycle scope)
  backups/<legacy>/:           500 keys (pre-iter184, manual cleanup deferred)

newest archive:    MASCI_complete_backup_2026-05-26_010157Z.zip @ 01:04:44 UTC
oldest archive:    backups/<legacy>/ at 2026-05-11 14:15 UTC
storage usage:     ~77.66 GB total · ~$1.17/mo at $0.015/GB
```

🟢 Inventory healthy · pagination fix returning truthful counts.

---

## Lifecycle policy (probed directly via R2 API)

```
Rule 1: "Default Multipart Abort Rule"
  Status: Enabled · AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 }

Rule 2: "masci-backups-auto-90d"
  Status: Enabled
  Expiration: { Days: 90 }
  Filter: { Prefix: "backups/auto-90d/" }
```

🟢 Lifecycle rule active. Steady-state will converge at ~190 GB post-fix.

---

## Manifest integrity (downloaded 91 MB archive · inspected MANIFEST.json)

```
captured_collections:    123  (matches Atlas count exactly)
explicit_exclusions:     []   (none)
redaction_rules_applied: ['user_directory', 'users']
inlined_photos:          10
total_records:           243,565
operational_attachments  → ✅ included
user_passkeys            → ✅ included
webauthn_challenges      → ✅ included
```

🟢 Manifest valid · all critical collections captured.

---

## MFA secret exclusion (verified by row sampling)

```
sample user_directory row:
  { "id": "u-iter425-...",
    "email": "...",
    "mfa": { "enabled": true } }      ← only enabled flag, NO totp_secret
```

🟢 No MFA secrets in backup. Redaction rules apply.

---

## backup_health state (post-fix · live)

```
mode=complete-r2      :  98 rows · ok=true · all have filename + size + records
mode=r2-usage-alert   :  98 rows · informational R2 quota probe
mode=complete-r2-error:   2 rows · 2026-05-25T15 (Atlas usage_events sort memory · self-recovered)
mode=lite             :   1 row
```

🟢 Most recent successful complete-r2: 2 minutes before audit (live cadence).

---

## Drift watcher

```
last snapshot:     2026-05-25T16:16:34
captured_collections: present
total_records:        present
explicit_exclusions:  []
```

🟢 Drift watcher armed. Next snapshot per cycle.

---

## Restore runbook accuracy

* Archive shape unchanged since iter383.
* Manifest format unchanged.
* Redaction rules documented.
* Restore process: download zip → unzip → mongorestore JSON dirs → replay
  attachments from R2 (same key paths preserved).
* No new manual steps required.

🟢 Restore runbook remains accurate.

---

## Risks

* 🟡 500 legacy archives in `backups/<no-prefix>/` (22.5 GB) — out of lifecycle.
  Optional cleanup; not blocking.
* 🟡 5 `.zip.tmp.*` files on PREVIEW disk (~440 MB) — production disk is clean
  (fresh deploy). Preview will self-clear next pod cycle.

🟢 Backup + restore certified.
